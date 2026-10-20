from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

import hashlib
from pathlib import Path
import struct
import unittest

import tools.migrate_duckstation_disc_state as media_migration
import tools.migrate_surface_soylent_v211_slot1_to_v212 as migration
from tools.xgdeathblows import GAMESTATE_SIZE
from tools.xgscript import AtelScript
from work.read_duckstation_runtime import GAME_STATE, RAM_SIZE


PROJECT_ROOT = REPOSITORY_ROOT
PINNED_SOURCE_BACKUP = (
    PROJECT_ROOT
    / "work"
    / "save_backups"
    / "SLUS-00669_1_v211_a2bd6b8b.sav"
)
SOURCE_STATE = (
    PINNED_SOURCE_BACKUP
    if PINNED_SOURCE_BACKUP.is_file()
    else PROJECT_ROOT / "emulator_data" / "SLUS-00669_1.sav"
)
OLD_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v211.bin"
)
NEW_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v212.bin"
)
OLD_SCRIPT = (
    PROJECT_ROOT
    / "work"
    / "surface_soylent_campaign_v211_stage"
    / "clones"
    / "field_550_disc1_donor"
    / "05_scripts.bin"
)
NEW_SCRIPT = (
    PROJECT_ROOT
    / "work"
    / "surface_soylent_campaign_v212_stage"
    / "clones"
    / "field_550_disc1_donor"
    / "05_scripts.bin"
)
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SurfaceSoylentV211Slot1MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (SOURCE_STATE, OLD_DISC, NEW_DISC, OLD_SCRIPT, NEW_SCRIPT, ZSTD)
        if not all(path.is_file() for path in required):
            raise unittest.SkipTest("Pinned V211/V212 migration fixtures unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.old_script = OLD_SCRIPT.read_bytes()
        cls.new_script = NEW_SCRIPT.read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v211_slot1_to_v212(
            cls.source,
            old_disc=OLD_DISC,
            new_disc=NEW_DISC,
            old_script=cls.old_script,
            new_script=cls.new_script,
            zstd=cls.zstd,
        )
        cls.source_payload, cls.frame_start, cls.source_prefix = (
            migration._unpack_state(cls.source, cls.zstd)
        )
        cls.result_payload, cls.result_frame_start, cls.result_prefix = (
            migration._unpack_state(cls.result, cls.zstd)
        )

    def test_equal_length_script_patch_is_exactly_thirteen_private_scratch_bytes(
        self,
    ) -> None:
        self.assertEqual(len(self.old_script), len(self.new_script))
        self.assertEqual(
            migration._diff_triplets(self.old_script, self.new_script),
            migration.SCRIPT_DIFFS,
        )
        self.assertEqual(
            tuple(offset for offset, _old, _new in migration.SCRIPT_DIFFS),
            migration.SCRIPT_DIFF_OFFSETS,
        )
        self.assertEqual(
            {old for _offset, old, _new in migration.SCRIPT_DIFFS},
            {0xC6},
        )
        self.assertEqual(
            {new for _offset, _old, new in migration.SCRIPT_DIFFS},
            {0xD0},
        )
        old_editor = AtelScript(self.old_script)
        new_editor = AtelScript(self.new_script)
        self.assertEqual(old_editor.entity_count, new_editor.entity_count)
        self.assertEqual(old_editor.bytecode_size, new_editor.bytecode_size)
        self.assertEqual(
            old_editor.get_script_pointer(
                migration.EXIT_ENTITY, migration.EXIT_ACTION_SLOT
            ),
            migration.EXIT_GATE_PC,
        )
        self.assertEqual(
            new_editor.get_script_pointer(
                migration.EXIT_ENTITY, migration.EXIT_ACTION_SLOT
            ),
            migration.EXIT_GATE_PC,
        )
        self.assertEqual(_sha256(self.new_script), migration.NEW_SCRIPT_SHA256)

    def test_candidate_identity_header_and_zstd_round_trip_are_exact(self) -> None:
        self.assertEqual(len(self.result), migration.EXPECTED_OUTPUT_SIZE)
        self.assertEqual(_sha256(self.result), migration.EXPECTED_OUTPUT_SHA256)
        self.assertEqual(self.result_payload, self.zstd.decompress(
            self.result[self.result_frame_start :]
        ))
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

    def test_payload_delta_is_only_fat_and_exit_gate(self) -> None:
        expected_table_offsets = tuple(
            migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + offset
            for offset, _old, _new in migration.SOURCE_TABLE_TO_NEW_DIFFS
        )
        expected_script_offsets = tuple(
            migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + offset
            for offset in migration.SCRIPT_DIFF_OFFSETS
        )
        expected = tuple(sorted(expected_table_offsets + expected_script_offsets))
        self.assertEqual(
            migration._diff_offsets(self.source_payload, self.result_payload),
            expected,
        )
        self.assertEqual(self.report["payload_bytes_changed"], 15)
        self.assertEqual(self.report["gate_scratch_bytes_changed"], 13)
        self.assertEqual(
            self.result_payload[
                migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET :
                migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + migration.SCRIPT_SIZE
            ],
            self.new_script,
        )
        new_table = media_migration._archive_table(NEW_DISC)
        self.assertEqual(
            self.result_payload[
                migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
                migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
                + migration.ARCHIVE_TABLE_SIZE
            ],
            new_table,
        )

    def test_gamestate_actor_data_locals_and_seal_radius_are_preserved(self) -> None:
        source_ram_offset, source_ram = migration._ram_from_payload(
            self.source_payload
        )
        result_ram_offset, result_ram = migration._ram_from_payload(
            self.result_payload
        )
        self.assertEqual(source_ram_offset, result_ram_offset)
        self.assertEqual(
            source_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
            result_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
        )
        seal = migration.EXPECTED_ACTORS[19][0]
        self.assertEqual(
            struct.unpack_from(
                "<H",
                result_ram,
                seal + migration.ACTOR_COLLISION_RADIUS_OFFSET,
            )[0],
            migration.EXPECTED_SEAL_COLLISION_RADIUS,
        )
        # These are the exact serialized field-local words in the captured
        # payload: doctor scratch 07C6=2 and new exit scratch 07D0=0.  Migration
        # must not preseed either; the repaired action initializes 07D0 itself.
        for payload_offset, expected in ((0xC5C90, 2), (0xC5C9A, 0)):
            self.assertEqual(
                struct.unpack_from("<H", self.source_payload, payload_offset)[0],
                expected,
            )
            self.assertEqual(
                self.result_payload[payload_offset : payload_offset + 2],
                self.source_payload[payload_offset : payload_offset + 2],
            )
        # The exact global payload whitelist proves every ActorData byte is
        # preserved; this explicit slice makes that guarantee easy to audit.
        actor_start = migration.EXPECTED_ACTORS[1][0]
        actor_end = migration.EXPECTED_ACTORS[23][0] + 0x1B8
        self.assertEqual(
            source_ram[actor_start:actor_end],
            result_ram[actor_start:actor_end],
        )

    def test_source_state_is_unchanged(self) -> None:
        self.assertEqual(_sha256(self.source), migration.SOURCE_STATE_SHA256)
        self.assertEqual(SOURCE_STATE.read_bytes(), self.source)

    def test_wrong_source_or_extra_script_change_is_rejected(self) -> None:
        wrong_state = bytearray(self.source)
        wrong_state[0x100] ^= 1
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError,
            "Source Slot 1 SHA-256",
        ):
            migration.migrate_v211_slot1_to_v212(
                bytes(wrong_state),
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_script=self.old_script,
                new_script=self.new_script,
                zstd=self.zstd,
            )
        wrong_script = bytearray(self.new_script)
        wrong_script[0x200] ^= 1
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError,
            "V212 field-550 script identity drifted",
        ):
            migration.migrate_v211_slot1_to_v212(
                self.source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_script=self.old_script,
                new_script=bytes(wrong_script),
                zstd=self.zstd,
            )

    def test_live_actor_inside_changed_gate_is_rejected(self) -> None:
        payload = bytearray(self.source_payload)
        ram_payload_offset = migration.EXPECTED_RAM_PAYLOAD_OFFSET
        e17 = migration.EXPECTED_ACTORS[17][0]
        struct.pack_into(
            "<H",
            payload,
            ram_payload_offset + e17 + migration.ACTOR_CURRENT_PC_OFFSET,
            migration.EXIT_GATE_PC,
        )
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError,
            "actor e17 contract drifted|executing the changed exit gate",
        ):
            migration._validate_runtime_contract(
                bytes(payload),
                resident_script=self.old_script,
                absent_script=self.new_script,
                label="mutated fixture",
            )


if __name__ == "__main__":
    unittest.main()
