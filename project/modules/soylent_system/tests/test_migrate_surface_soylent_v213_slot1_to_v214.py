from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

from contextlib import redirect_stderr
import hashlib
import io
from pathlib import Path
import struct
import unittest

import tools.migrate_duckstation_disc_state as media_migration
import tools.migrate_surface_soylent_v213_slot1_to_v214 as migration
from tools.xgdeathblows import GAMESTATE_SIZE
from tools.xgscript import AtelScript
from work.read_duckstation_runtime import GAME_STATE


PROJECT_ROOT = REPOSITORY_ROOT
SOURCE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_backups"
    / "SLUS-00669_1_v213_3c2e76d5.sav"
)
OLD_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v213.bin"
)
NEW_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v214.bin"
)
OLD_CUE = OLD_DISC.with_suffix(".cue")
NEW_CUE = NEW_DISC.with_suffix(".cue")
OLD_FIELD = (
    PROJECT_ROOT
    / "work"
    / "surface_soylent_campaign_v213_stage"
    / "clones"
    / "field_550_disc1_donor"
)
NEW_FIELD = (
    PROJECT_ROOT
    / "work"
    / "surface_soylent_campaign_v214_stage"
    / "clones"
    / "field_550_disc1_donor"
)
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SurfaceSoylentV213Slot1MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (
            SOURCE_STATE,
            OLD_DISC,
            NEW_DISC,
            OLD_CUE,
            NEW_CUE,
            OLD_FIELD / "05_scripts.bin",
            NEW_FIELD / "05_scripts.bin",
            OLD_FIELD / "07_dialogue.bin",
            NEW_FIELD / "07_dialogue.bin",
            ZSTD,
        )
        if not all(path.is_file() for path in required):
            raise unittest.SkipTest("Pinned V213/V214 migration fixtures unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.old_script = (OLD_FIELD / "05_scripts.bin").read_bytes()
        cls.new_script = (NEW_FIELD / "05_scripts.bin").read_bytes()
        cls.old_dialogue = (OLD_FIELD / "07_dialogue.bin").read_bytes()
        cls.new_dialogue = (NEW_FIELD / "07_dialogue.bin").read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v213_slot1_to_v214(
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
        self.assertEqual(self.frame_start, migration.EXPECTED_FRAME_START)
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

    def test_resources_have_exact_carrier_and_archive_table_deltas(self) -> None:
        self.assertEqual(len(self.old_script), len(self.new_script))
        self.assertEqual(
            migration._diff_triplets(self.old_script, self.new_script),
            migration.SCRIPT_DIFFS,
        )
        old_editor = AtelScript(self.old_script)
        new_editor = AtelScript(self.new_script)
        self.assertEqual(
            old_editor.bytecode[
                migration.TERMINAL_ACTION_PC : migration.TERMINAL_ACTION_END_PC
            ],
            new_editor.bytecode[
                migration.TERMINAL_ACTION_PC : migration.TERMINAL_ACTION_END_PC
            ],
        )
        self.assertEqual(
            tuple(
                old_editor.get_script_pointer(entity, 0)
                for entity in migration.TERMINAL_ENTITIES
            ),
            (
                migration.TERMINAL_INIT_PC,
                migration.TERMINAL_SHARED_STOP_PC,
                migration.TERMINAL_SHARED_STOP_PC,
            ),
        )
        self.assertEqual(
            tuple(
                new_editor.get_script_pointer(entity, 0)
                for entity in migration.TERMINAL_ENTITIES
            ),
            migration.TERMINAL_INIT_PCS,
        )
        self.assertEqual(
            tuple(
                new_editor.get_script_pointer(entity, 2)
                for entity in migration.TERMINAL_ENTITIES
            ),
            (migration.TERMINAL_ACTION_PC,) * 3,
        )
        self.assertEqual(
            tuple(
                new_editor.bytecode[pc : pc + len(body)]
                for pc, body in zip(
                    migration.TERMINAL_INIT_PCS[1:],
                    migration.NEW_AUX_TERMINAL_INIT_BODIES,
                    strict=True,
                )
            ),
            migration.NEW_AUX_TERMINAL_INIT_BODIES,
        )
        self.assertEqual(self.old_dialogue, self.new_dialogue)
        self.assertEqual(
            migration._diff_triplets(
                media_migration._archive_table(OLD_DISC),
                media_migration._archive_table(NEW_DISC),
            ),
            migration.ARCHIVE_TABLE_DIFFS,
        )
        self.assertEqual(
            (OLD_CUE.stat().st_size, _sha256(OLD_CUE.read_bytes())),
            (migration.OLD_CUE_SIZE, migration.OLD_CUE_SHA256),
        )
        self.assertEqual(
            (NEW_CUE.stat().st_size, _sha256(NEW_CUE.read_bytes())),
            (migration.NEW_CUE_SIZE, migration.NEW_CUE_SHA256),
        )

    def test_only_56_script_and_24_runtime_bytes_change(self) -> None:
        offsets = migration._diff_offsets(self.source_payload, self.result_payload)
        expected = {
            *(
                migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + offset
                for offset, _old, _new in migration.ARCHIVE_TABLE_DIFFS
            ),
            *(
                migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + offset
                for offset, _old, _new in migration.SCRIPT_DIFFS
            ),
        }
        for offset, old, new, _label in migration.RUNTIME_PATCHES:
            expected.update(
                offset + relative
                for relative, (before, after) in enumerate(
                    zip(old, new, strict=True)
                )
                if before != after
            )
        self.assertEqual(offsets, tuple(sorted(expected)))
        self.assertEqual(len(offsets), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        self.assertEqual(
            self.report["payload_bytes_changed"],
            migration.EXPECTED_PAYLOAD_BYTES_CHANGED,
        )
        self.assertEqual(
            self.report["script_bytes_changed"],
            migration.EXPECTED_SCRIPT_BYTES_CHANGED,
        )
        self.assertEqual(
            self.report["terminal_runtime_bytes_changed"],
            migration.EXPECTED_RUNTIME_BYTES_CHANGED,
        )
        self.assertEqual(
            self.report["archive_table_payload_bytes_changed"],
            migration.EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED,
        )

    def test_volatile_archive_tail_and_dialogue_are_byte_identical(self) -> None:
        table_start = migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        table_end = table_start + migration.ARCHIVE_TABLE_SIZE
        self.assertEqual(
            migration._diff_triplets(
                self.source_payload[table_start:table_end],
                self.result_payload[table_start:table_end],
            ),
            migration.ARCHIVE_TABLE_DIFFS,
        )
        expected_table = bytearray(media_migration._archive_table(NEW_DISC))
        expected_table[-1] = migration.EXPECTED_VOLATILE_TABLE_VALUE
        self.assertEqual(
            self.result_payload[table_start:table_end],
            bytes(expected_table),
        )
        self.assertEqual(
            self.result_payload[migration.EXPECTED_VOLATILE_TABLE_PAYLOAD_OFFSET],
            migration.EXPECTED_VOLATILE_TABLE_VALUE,
        )
        dialogue_start = migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        dialogue_end = dialogue_start + migration.DIALOGUE_SIZE
        self.assertEqual(
            self.source_payload[dialogue_start:dialogue_end],
            self.result_payload[dialogue_start:dialogue_end],
        )
        self.assertEqual(
            self.result_payload[dialogue_start:dialogue_end], self.old_dialogue
        )
        self.assertTrue(self.report["volatile_table_tail_preserved"])
        self.assertTrue(self.report["active_dialogue_preserved"])

    def test_runtime_carriers_move_or_queue_without_disturbing_active_e4(self) -> None:
        _source_ram_offset, source_ram = migration._ram_from_payload(
            self.source_payload
        )
        _result_ram_offset, result_ram = migration._ram_from_payload(
            self.result_payload
        )
        record = migration.EXPECTED_TERMINAL_RECORD
        actor_data = migration.EXPECTED_TERMINAL_ACTOR_DATA
        self.assertEqual(
            struct.unpack_from("<3i", result_ram, record + 0x20),
            (80, 0, -167),
        )
        self.assertEqual(
            struct.unpack_from("<3i", result_ram, record + 0x40),
            (80, 0, -167),
        )
        self.assertEqual(
            struct.unpack_from("<I", result_ram, actor_data + 0x04)[0],
            0x00040000,
        )
        self.assertEqual(
            struct.unpack_from("<4H", result_ram, actor_data + 0x08),
            (31, 0, 0, 0),
        )
        self.assertEqual(
            struct.unpack_from("<4H", result_ram, actor_data + 0x18),
            (2, 200, 30, 2),
        )
        self.assertEqual(
            struct.unpack_from("<3i", result_ram, actor_data + 0x20),
            (80 << 16, 0, (-167) << 16),
        )
        self.assertEqual(
            struct.unpack_from("<4h", result_ram, actor_data + 0x68),
            (80, 0, -167, 0),
        )
        self.assertEqual(
            source_ram[actor_data + 0x80 : actor_data + 0xD0],
            result_ram[actor_data + 0x80 : actor_data + 0xD0],
        )
        self.assertEqual(
            struct.unpack_from("<H", result_ram, actor_data + 0xCC)[0],
            migration.TERMINAL_ACTIVE_PC,
        )
        self.assertEqual(
            result_ram[actor_data + 0x8C : actor_data + 0x94],
            bytes.fromhex("CF 05 00 02 FF FF 0C 00"),
        )

        for entity, auxiliary_record, auxiliary_data, sprite_pointer, slot0 in zip(
            migration.TERMINAL_ENTITIES[1:],
            migration.EXPECTED_TERMINAL_RECORDS[1:],
            migration.EXPECTED_TERMINAL_ACTOR_DATA_OFFSETS[1:],
            migration.EXPECTED_TERMINAL_SPRITE_POINTERS[1:],
            migration.NEW_AUX_TERMINAL_SLOT0,
            strict=True,
        ):
            self.assertEqual(
                struct.unpack_from("<II", result_ram, auxiliary_record),
                (0, sprite_pointer),
            )
            self.assertEqual(
                result_ram[
                    auxiliary_record + migration.ACTOR_RECORD_STATUS_OFFSET :
                    auxiliary_record + migration.ACTOR_RECORD_STATUS_OFFSET + 2
                ],
                migration.NEW_AUX_TERMINAL_RECORD_STATUS,
            )
            self.assertEqual(
                result_ram[
                    auxiliary_data + migration.ACTOR_DATA_FLAGS_OFFSET :
                    auxiliary_data + migration.ACTOR_DATA_FLAGS_OFFSET + 4
                ],
                migration.NEW_AUX_TERMINAL_FLAGS,
            )
            self.assertEqual(
                source_ram[
                    auxiliary_data + migration.ACTOR_DATA_SURFACES_OFFSET :
                    auxiliary_data + migration.ACTOR_SCRIPT_SLOT_OFFSET
                ],
                result_ram[
                    auxiliary_data + migration.ACTOR_DATA_SURFACES_OFFSET :
                    auxiliary_data + migration.ACTOR_SCRIPT_SLOT_OFFSET
                ],
            )
            self.assertEqual(
                source_ram[
                    auxiliary_data + migration.ACTOR_SCRIPT_SLOT_OFFSET :
                    auxiliary_data + migration.ACTOR_SCRIPT_SLOT_OFFSET + 8
                ],
                migration.OLD_AUX_TERMINAL_SLOT0,
            )
            self.assertEqual(
                result_ram[
                    auxiliary_data + migration.ACTOR_SCRIPT_SLOT_OFFSET :
                    auxiliary_data + migration.ACTOR_SCRIPT_SLOT_OFFSET + 8
                ],
                slot0,
            )
            self.assertEqual(
                source_ram[
                    auxiliary_data + migration.ACTOR_SCRIPT_SLOT_OFFSET + 8 :
                    auxiliary_data + 0xD0
                ],
                result_ram[
                    auxiliary_data + migration.ACTOR_SCRIPT_SLOT_OFFSET + 8 :
                    auxiliary_data + 0xD0
                ],
            )
            self.assertEqual(
                struct.unpack_from(
                    "<H",
                    result_ram,
                    auxiliary_data + migration.ACTOR_CURRENT_PC_OFFSET,
                )[0],
                migration.TERMINAL_SHARED_STOP_PC,
                f"e{entity} current PC must stay parked until the queue runs",
            )

        for entity, sprite_pointer, sprite_sha256 in zip(
            migration.TERMINAL_ENTITIES,
            migration.EXPECTED_TERMINAL_SPRITE_POINTERS,
            migration.EXPECTED_TERMINAL_SPRITE_SHA256,
            strict=True,
        ):
            sprite = sprite_pointer & 0x1FFFFFFF
            source_sprite = source_ram[
                sprite : sprite + migration.TERMINAL_SPRITE_RUNTIME_SIZE
            ]
            result_sprite = result_ram[
                sprite : sprite + migration.TERMINAL_SPRITE_RUNTIME_SIZE
            ]
            self.assertEqual(_sha256(source_sprite), sprite_sha256, f"e{entity}")
            self.assertEqual(result_sprite, source_sprite, f"e{entity}")
        self.assertEqual(
            self.report["queued_terminal_initializers"],
            {"e5": "0x05F1", "e6": "0x060E"},
        )
        self.assertTrue(self.report["terminal_sprites_preserved"])

    def test_gamestate_and_active_wait_dialog_are_preserved(self) -> None:
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
        self.assertEqual(
            _sha256(result_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE]),
            migration.EXPECTED_GAMESTATE_SHA256,
        )
        active_byte = (
            migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET
            + AtelScript(self.old_script).bytecode_offset
            + migration.TERMINAL_ACTIVE_PC
        )
        self.assertEqual(
            (self.source_payload[active_byte], self.result_payload[active_byte]),
            (0x9C, 0x9C),
        )
        self.assertEqual(
            self.result_payload[
                migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET :
                migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + migration.SCRIPT_SIZE
            ],
            self.new_script,
        )
        self.assertTrue(self.report["gamestate_preserved"])

    def test_wrong_source_components_and_dialogue_fail_closed(self) -> None:
        self.assertEqual(len(self.source), migration.SOURCE_STATE_SIZE)
        self.assertEqual(_sha256(self.source), migration.SOURCE_STATE_SHA256)
        wrong_state = bytearray(self.source)
        wrong_state[0x100] ^= 1
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError,
            "Source Slot 1 identity",
        ):
            migration.migrate_v213_slot1_to_v214(
                bytes(wrong_state),
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_script=self.old_script,
                new_script=self.new_script,
                old_dialogue=self.old_dialogue,
                new_dialogue=self.new_dialogue,
                zstd=self.zstd,
            )

        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError,
            "V214 disc identity drifted",
        ):
            migration.migrate_v213_slot1_to_v214(
                self.source,
                old_disc=OLD_DISC,
                new_disc=OLD_DISC,
                old_script=self.old_script,
                new_script=self.new_script,
                old_dialogue=self.old_dialogue,
                new_dialogue=self.new_dialogue,
                zstd=self.zstd,
            )

        wrong_script = bytearray(self.new_script)
        wrong_script[-1] ^= 1
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError,
            "V214 script identity drifted",
        ):
            migration.migrate_v213_slot1_to_v214(
                self.source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_script=self.old_script,
                new_script=bytes(wrong_script),
                old_dialogue=self.old_dialogue,
                new_dialogue=self.new_dialogue,
                zstd=self.zstd,
            )

        wrong_dialogue = bytearray(self.new_dialogue)
        wrong_dialogue[-1] ^= 1
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError,
            "V214 dialogue identity drifted",
        ):
            migration.migrate_v213_slot1_to_v214(
                self.source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_script=self.old_script,
                new_script=self.new_script,
                old_dialogue=self.old_dialogue,
                new_dialogue=bytes(wrong_dialogue),
                zstd=self.zstd,
            )

    def test_cli_refuses_to_overwrite_live_slot1(self) -> None:
        before = migration.LIVE_SLOT1.read_bytes()
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = migration.main(
                (
                    str(SOURCE_STATE),
                    str(migration.LIVE_SLOT1),
                    "--old-disc",
                    str(OLD_DISC),
                    "--new-disc",
                    str(NEW_DISC),
                    "--old-script",
                    str(OLD_FIELD / "05_scripts.bin"),
                    "--new-script",
                    str(NEW_FIELD / "05_scripts.bin"),
                    "--old-dialogue",
                    str(OLD_FIELD / "07_dialogue.bin"),
                    "--new-dialogue",
                    str(NEW_FIELD / "07_dialogue.bin"),
                    "--zstd",
                    str(ZSTD),
                )
            )
        self.assertEqual(result, 1)
        self.assertIn("may not be the live Slot 1", stderr.getvalue())
        self.assertEqual(migration.LIVE_SLOT1.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
