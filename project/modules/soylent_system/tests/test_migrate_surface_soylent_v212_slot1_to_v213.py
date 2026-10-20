from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

import hashlib
from pathlib import Path
import struct
import unittest

import tools.migrate_duckstation_disc_state as media_migration
import tools.migrate_surface_soylent_v212_slot1_to_v213 as migration
from tools.xgdeathblows import GAMESTATE_SIZE
from tools.xgdialog import parse_dialogue
from work.read_duckstation_runtime import GAME_STATE


PROJECT_ROOT = REPOSITORY_ROOT
SOURCE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_backups"
    / "SLUS-00669_1_v212_3493bff3.sav"
)
OLD_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v212.bin"
)
NEW_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v213.bin"
)
OLD_FIELD = (
    PROJECT_ROOT
    / "work"
    / "surface_soylent_campaign_v212_stage"
    / "clones"
    / "field_550_disc1_donor"
)
NEW_FIELD = (
    PROJECT_ROOT
    / "work"
    / "surface_soylent_campaign_v213_stage"
    / "clones"
    / "field_550_disc1_donor"
)
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SurfaceSoylentV212Slot1MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (
            SOURCE_STATE,
            OLD_DISC,
            NEW_DISC,
            OLD_FIELD / "05_scripts.bin",
            NEW_FIELD / "05_scripts.bin",
            OLD_FIELD / "07_dialogue.bin",
            NEW_FIELD / "07_dialogue.bin",
            ZSTD,
        )
        if not all(path.is_file() for path in required):
            raise unittest.SkipTest("Pinned V212/V213 migration fixtures unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.old_script = (OLD_FIELD / "05_scripts.bin").read_bytes()
        cls.new_script = (NEW_FIELD / "05_scripts.bin").read_bytes()
        cls.old_dialogue = (OLD_FIELD / "07_dialogue.bin").read_bytes()
        cls.new_dialogue = (NEW_FIELD / "07_dialogue.bin").read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v212_slot1_to_v213(
            cls.source,
            old_disc=OLD_DISC,
            new_disc=NEW_DISC,
            old_script=cls.old_script,
            new_script=cls.new_script,
            old_dialogue=cls.old_dialogue,
            new_dialogue=cls.new_dialogue,
            zstd=cls.zstd,
        )
        cls.source_payload, cls.frame_start, cls.source_prefix = (
            migration._unpack_state(cls.source, cls.zstd)
        )
        cls.result_payload, cls.result_frame_start, cls.result_prefix = (
            migration._unpack_state(cls.result, cls.zstd)
        )

    def test_candidate_identity_and_round_trip_are_frozen(self) -> None:
        self.assertEqual(len(self.result), migration.EXPECTED_OUTPUT_SIZE)
        self.assertEqual(_sha256(self.result), migration.EXPECTED_OUTPUT_SHA256)
        self.assertEqual(self.result_frame_start, self.frame_start)
        self.assertEqual(
            self.result_prefix,
            migration._expected_prefix(
                self.source_prefix,
                compressed_size=len(self.result) - self.frame_start,
            ),
        )
        self.assertEqual(
            self.result.count(migration.OLD_CUE_NAME.encode("ascii")), 0
        )
        self.assertEqual(
            self.result.count(migration.NEW_CUE_NAME.encode("ascii")), 1
        )
        self.assertTrue(self.report["round_trip_verified"])

    def test_equal_size_resident_components_are_replaced_exactly(self) -> None:
        self.assertEqual(len(self.old_script), len(self.new_script))
        self.assertEqual(len(self.old_dialogue), len(self.new_dialogue))
        self.assertEqual(self.report["script_bytes_changed"], 235)
        self.assertEqual(self.report["dialogue_bytes_changed"], 4_623)
        self.assertEqual(
            self.result_payload[
                migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET :
                migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + migration.SCRIPT_SIZE
            ],
            self.new_script,
        )
        self.assertEqual(
            self.result_payload[
                migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET :
                migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET
                + migration.DIALOGUE_SIZE
            ],
            self.new_dialogue,
        )
        self.assertEqual(self.result_payload.count(self.old_script), 0)
        self.assertEqual(self.result_payload.count(self.old_dialogue), 0)
        old_blocks = parse_dialogue(self.old_dialogue).blocks
        new_blocks = parse_dialogue(self.new_dialogue).blocks
        for dialogue_id in range(53, 61):
            with self.subTest(active_clinic_dialogue=dialogue_id):
                self.assertEqual(
                    (new_blocks[dialogue_id].offset, new_blocks[dialogue_id].payload),
                    (old_blocks[dialogue_id].offset, old_blocks[dialogue_id].payload),
                )

    def test_only_whitelisted_payload_bytes_change(self) -> None:
        self.assertEqual(self.report["payload_bytes_changed"], 4_867)
        self.assertEqual(self.report["terminal_runtime_bytes_changed"], 7)
        offsets = migration._diff_offsets(self.source_payload, self.result_payload)
        self.assertEqual(len(offsets), 4_867)
        new_table = media_migration._archive_table(NEW_DISC)
        self.assertEqual(
            self.result_payload[
                migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
                migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
                + migration.ARCHIVE_TABLE_SIZE
            ],
            new_table,
        )

    def test_gamestate_is_preserved_and_terminal_initializer_is_queued(self) -> None:
        _source_ram_offset, source_ram = migration._ram_from_payload(
            self.source_payload
        )
        _result_ram_offset, result_ram = migration._ram_from_payload(
            self.result_payload
        )
        self.assertEqual(
            source_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
            result_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
        )
        actor_array = migration.EXPECTED_ACTOR_ARRAY_GUEST_POINTER & 0x1FFFFFFF
        record = (
            actor_array
            + migration.TERMINAL_ENTITY * migration.FIELD_ACTOR_STRIDE
        )
        actor_data = migration.EXPECTED_TERMINAL_ACTOR_DATA
        self.assertEqual(
            result_ram[
                record + migration.ACTOR_RECORD_STATUS_OFFSET :
                record + migration.ACTOR_RECORD_STATUS_OFFSET + 2
            ],
            migration.NEW_TERMINAL_RECORD_STATUS,
        )
        self.assertEqual(
            result_ram[
                actor_data + migration.ACTOR_DATA_FLAGS_OFFSET :
                actor_data + migration.ACTOR_DATA_FLAGS_OFFSET + 4
            ],
            migration.NEW_TERMINAL_ACTOR_FLAGS,
        )
        self.assertEqual(
            result_ram[
                actor_data + migration.ACTOR_SCRIPT_SLOT_OFFSET :
                actor_data + migration.ACTOR_SCRIPT_SLOT_OFFSET + 8
            ],
            migration.NEW_TERMINAL_SLOT0,
        )
        self.assertEqual(
            struct.unpack_from(
                "<H", result_ram, actor_data + migration.ACTOR_CURRENT_PC_OFFSET
            )[0],
            0x068C,
        )
        self.assertTrue(self.report["terminal_initializer_queued"])

    def test_source_and_wrong_inputs_are_fail_closed(self) -> None:
        self.assertEqual(_sha256(self.source), migration.SOURCE_STATE_SHA256)
        self.assertEqual(SOURCE_STATE.read_bytes(), self.source)
        wrong_state = bytearray(self.source)
        wrong_state[0x100] ^= 1
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError,
            "Source Slot 1 SHA-256",
        ):
            migration.migrate_v212_slot1_to_v213(
                bytes(wrong_state),
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_script=self.old_script,
                new_script=self.new_script,
                old_dialogue=self.old_dialogue,
                new_dialogue=self.new_dialogue,
                zstd=self.zstd,
            )
        wrong_dialogue = bytearray(self.new_dialogue)
        wrong_dialogue[-1] ^= 1
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError,
            "V213 dialogue identity drifted",
        ):
            migration.migrate_v212_slot1_to_v213(
                self.source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_script=self.old_script,
                new_script=self.new_script,
                old_dialogue=self.old_dialogue,
                new_dialogue=bytes(wrong_dialogue),
                zstd=self.zstd,
            )


if __name__ == "__main__":
    unittest.main()
