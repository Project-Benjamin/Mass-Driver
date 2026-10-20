from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

from contextlib import redirect_stderr
import hashlib
import io
from pathlib import Path
import struct
import unittest

import tools.migrate_duckstation_disc_state as media_migration
import tools.migrate_surface_soylent_v215_slot1_to_v216 as migration
from tools.xgdeathblows import GAMESTATE_SIZE
from tools.xgdialog import parse_dialogue
from work.read_duckstation_runtime import (
    CAMERA_VECTORS,
    FIELD_ACTORS,
    FIELD_ACTOR_DATA_POINTER,
    FIELD_ACTOR_STRIDE,
    FIELD_SCRIPT_MEMORY,
    GAME_STATE,
)


PROJECT_ROOT = REPOSITORY_ROOT
SOURCE_STATE = PROJECT_ROOT / "work" / "save_backups" / "SLUS-00669_1_v215_post_keycard_ca850361.sav"
CANDIDATE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v216_from_ca850361_terminal_diagnostics.sav"
)
OLD_DISC = PROJECT_ROOT / "output" / "Xenogears_PW_CD2_mass_driver_surface_soylent_v215.bin"
NEW_DISC = PROJECT_ROOT / "output" / "Xenogears_PW_CD2_mass_driver_surface_soylent_v216.bin"
OLD_FIELD = PROJECT_ROOT / "work" / "surface_soylent_campaign_v215_stage" / "clones" / "field_593_disc1_donor"
NEW_FIELD = PROJECT_ROOT / "work" / "surface_soylent_campaign_v216_stage" / "clones" / "field_593_disc1_donor"
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SurfaceSoylentV215Slot1MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (
            SOURCE_STATE,
            OLD_DISC,
            NEW_DISC,
            OLD_DISC.with_suffix(".cue"),
            NEW_DISC.with_suffix(".cue"),
            OLD_FIELD / "05_scripts.bin",
            NEW_FIELD / "05_scripts.bin",
            OLD_FIELD / "07_dialogue.bin",
            NEW_FIELD / "07_dialogue.bin",
            ZSTD,
        )
        if not all(path.is_file() for path in required):
            raise unittest.SkipTest("Pinned V215/V216 migration fixtures unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.old_script = (OLD_FIELD / "05_scripts.bin").read_bytes()
        cls.new_script = (NEW_FIELD / "05_scripts.bin").read_bytes()
        cls.old_dialogue = (OLD_FIELD / "07_dialogue.bin").read_bytes()
        cls.new_dialogue = (NEW_FIELD / "07_dialogue.bin").read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v215_slot1_to_v216(
            cls.source,
            old_disc=OLD_DISC,
            new_disc=NEW_DISC,
            old_script=cls.old_script,
            new_script=cls.new_script,
            old_dialogue=cls.old_dialogue,
            new_dialogue=cls.new_dialogue,
            zstd=cls.zstd,
        )
        cls.source_payload, cls.frame_start, cls.source_prefix = migration._unpack_state(cls.source, cls.zstd)
        cls.result_payload, cls.result_frame_start, cls.result_prefix = migration._unpack_state(cls.result, cls.zstd)
        cls.source_resident_dialogue = cls.source_payload[
            migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET :
            migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET + migration.SOURCE_RESIDENT_DIALOGUE_SIZE
        ]
        cls.result_resident_dialogue = cls.result_payload[
            migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET :
            migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET + migration.OUTPUT_RESIDENT_DIALOGUE_SIZE
        ]

    def test_candidate_identity_round_trip_and_formal_file_are_frozen(self) -> None:
        self.assertEqual(
            (len(self.result), _sha256(self.result)),
            (migration.EXPECTED_OUTPUT_SIZE, migration.EXPECTED_OUTPUT_SHA256),
        )
        self.assertEqual(_sha256(self.result_payload), migration.EXPECTED_OUTPUT_PAYLOAD_SHA256)
        self.assertEqual(self.frame_start, migration.EXPECTED_FRAME_START)
        self.assertEqual(self.result_frame_start, self.frame_start)
        self.assertEqual(
            self.result_prefix,
            migration._expected_prefix(
                self.source_prefix,
                compressed_size=len(self.result) - self.frame_start,
            ),
        )
        self.assertEqual(self.result.count(migration.OLD_CUE_NAME.encode()), 0)
        self.assertEqual(self.result.count(migration.NEW_CUE_NAME.encode()), 1)
        self.assertTrue(self.report["round_trip_verified"])
        self.assertTrue(self.report["allocator_safe"])
        if CANDIDATE_STATE.is_file():
            self.assertEqual(CANDIDATE_STATE.read_bytes(), self.result)

    def test_disc_cue_archive_table_and_full_field_resources_are_exact(self) -> None:
        self.assertEqual(self.old_script, self.new_script)
        self.assertEqual(_sha256(self.old_script), migration.OLD_SCRIPT_SHA256)
        self.assertEqual(_sha256(self.old_dialogue), migration.OLD_DIALOGUE_SHA256)
        self.assertEqual(_sha256(self.new_dialogue), migration.NEW_DIALOGUE_SHA256)
        old_table = media_migration._archive_table(OLD_DISC)
        new_table = media_migration._archive_table(NEW_DISC)
        diffs = tuple((i, a, b) for i, (a, b) in enumerate(zip(old_table, new_table, strict=True)) if a != b)
        self.assertEqual(diffs, migration.ARCHIVE_TABLE_DIFFS)
        table = migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        expected = new_table[:-1] + bytes((migration.EXPECTED_VOLATILE_TABLE_VALUE,))
        actual = self.result_payload[table : table + migration.ARCHIVE_TABLE_SIZE]
        self.assertEqual(actual, expected)
        self.assertEqual(_sha256(actual), migration.OUTPUT_RESIDENT_TABLE_SHA256)
        self.assertEqual(actual[-1], 0xE0)

    def test_exact_source_is_post_keycard_field593_with_closed_id55_window(self) -> None:
        self.assertEqual(
            (len(self.source), _sha256(self.source)),
            (migration.SOURCE_STATE_SIZE, migration.SOURCE_STATE_SHA256),
        )
        self.assertEqual(
            (len(self.source_payload), _sha256(self.source_payload)),
            (migration.SOURCE_PAYLOAD_SIZE, migration.SOURCE_PAYLOAD_SHA256),
        )
        _offset, ram = migration._ram_from_payload(self.source_payload)
        self.assertEqual(_sha256(ram), migration.SOURCE_RAM_SHA256)
        self.assertEqual(
            struct.unpack_from("<I", ram, migration.GAME_SCENE_MAP)[0] & 0xFFF,
            migration.EXPECTED_FIELD,
        )
        active_bank = ram[
            FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + migration.FIELD_VARIABLE_BANK_SIZE
        ]
        backup_bank = ram[
            GAME_STATE + migration.FIELD_VARIABLE_BACKUP_OFFSET :
            GAME_STATE + migration.FIELD_VARIABLE_BACKUP_OFFSET + migration.FIELD_VARIABLE_BANK_SIZE
        ]
        self.assertEqual(active_bank, backup_bank)
        self.assertEqual(_sha256(active_bank), migration.EXPECTED_FIELD_VARIABLE_BANK_SHA256)
        self.assertEqual(
            struct.unpack_from("<H", active_bank, migration.QUARANTINE_CARD_OPERAND)[0],
            migration.EXPECTED_QUARANTINE_WORD,
        )
        self.assertTrue(
            struct.unpack_from("<H", active_bank, migration.QUARANTINE_CARD_OPERAND)[0]
            & (1 << migration.QUARANTINE_CARD_BIT)
        )
        for i in range(4):
            status = struct.unpack_from(
                "<h",
                ram,
                migration.DIALOG_WINDOWS
                + i * migration.DIALOG_WINDOW_STRIDE
                + migration.DIALOG_WINDOW_STATUS_OFFSET,
            )[0]
            self.assertEqual(status, -1)
        self.assertEqual(
            struct.unpack_from("<I", ram, migration.WINDOW0_START_POINTER_OFFSET)[0],
            migration.EXPECTED_WINDOW0_START_POINTER,
        )
        self.assertEqual(
            struct.unpack_from("<I", ram, migration.WINDOW0_CURRENT_POINTER_OFFSET)[0],
            migration.EXPECTED_WINDOW0_CURRENT_POINTER,
        )

    def test_compact_id55_only_becomes_four_line_medical_diagnostics(self) -> None:
        source = parse_dialogue(self.source_resident_dialogue)
        result = parse_dialogue(self.result_resident_dialogue)
        self.assertEqual(len(source.blocks), 56)
        self.assertEqual(len(result.blocks), 56)
        self.assertEqual(
            (len(self.source_resident_dialogue), _sha256(self.source_resident_dialogue)),
            (
                migration.SOURCE_RESIDENT_DIALOGUE_SIZE,
                migration.SOURCE_RESIDENT_DIALOGUE_SHA256,
            ),
        )
        self.assertEqual(
            (len(self.result_resident_dialogue), _sha256(self.result_resident_dialogue)),
            (
                migration.OUTPUT_RESIDENT_DIALOGUE_SIZE,
                migration.OUTPUT_RESIDENT_DIALOGUE_SHA256,
            ),
        )
        for dialogue_id in range(55):
            self.assertEqual(source.blocks[dialogue_id], result.blocks[dialogue_id])
        block = result.blocks[migration.DIAGNOSTIC_DIALOGUE_ID]
        self.assertEqual(
            (block.offset, len(block.payload), block.width, block.height),
            (
                migration.RESIDENT_ID55_OFFSET,
                migration.RESIDENT_ID55_CAPACITY,
                *migration.DIAGNOSTIC_GRID,
            ),
        )
        self.assertEqual(
            block.text,
            migration.DIAGNOSTIC_TEXT + "<Close>" * 12,
        )
        self.assertEqual(
            block.text.split("<Close>", 1)[0].split("\n"),
            [
                "MEDICAL DIAGNOSTICS",
                "Pulse 64 / BP 118/72",
                "Temp 36.8 C / Resp 14",
                "Neural activity: ELEVATED.",
            ],
        )
        self.assertEqual(
            self.result_resident_dialogue[
                migration.RESIDENT_ID55_OFFSET + migration.V216_ID55_PAYLOAD_SIZE :
                migration.RESIDENT_ID55_OFFSET + migration.RESIDENT_ID55_CAPACITY
            ],
            b"\x00" * 12,
        )

    def test_payload_diff_is_exactly_one_table_byte_and_84_id55_bytes(self) -> None:
        actual = migration._diff_offsets(self.source_payload, self.result_payload)
        dialogue_diffs = migration._diff_offsets(
            self.source_resident_dialogue,
            self.result_resident_dialogue,
        )
        expected = {
            migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + 0x30E0,
            *(
                migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET + offset
                for offset in dialogue_diffs
            ),
        }
        self.assertEqual(actual, tuple(sorted(expected)))
        self.assertEqual(len(actual), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        self.assertEqual(len(dialogue_diffs), migration.EXPECTED_RESIDENT_DIALOGUE_BYTES_CHANGED)
        table_change = migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + 0x30E0
        dialogue_actual = tuple(offset for offset in actual if offset != table_change)
        self.assertEqual(
            min(dialogue_actual),
            migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET + migration.RESIDENT_ID55_OFFSET,
        )
        self.assertEqual(
            max(dialogue_actual),
            migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET
            + migration.RESIDENT_ID55_OFFSET
            + migration.V216_ID55_PAYLOAD_SIZE
            - 3,
        )
        self.assertEqual(self.report["archive_table_bytes_changed"], 1)
        self.assertEqual(self.report["resident_script_bytes_changed"], 0)
        self.assertEqual(self.report["resident_dialogue_bytes_changed"], 84)
        self.assertEqual(self.report["payload_bytes_changed"], 85)

    def test_allocator_headers_script_and_component_neighbors_are_unchanged(self) -> None:
        script = migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET
        dialogue = migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        walkmesh = migration.EXPECTED_WALKMESH_PAYLOAD_OFFSET
        self.assertEqual(
            self.source_payload[script : script + migration.RESIDENT_SCRIPT_SIZE],
            self.result_payload[script : script + migration.RESIDENT_SCRIPT_SIZE],
        )
        self.assertEqual(
            _sha256(self.result_payload[script : script + migration.RESIDENT_SCRIPT_SIZE]),
            migration.RESIDENT_SCRIPT_SHA256,
        )
        self.assertEqual(
            self.source_payload[script + migration.RESIDENT_SCRIPT_SIZE : dialogue],
            self.result_payload[script + migration.RESIDENT_SCRIPT_SIZE : dialogue],
        )
        self.assertEqual(
            _sha256(self.result_payload[script + migration.RESIDENT_SCRIPT_SIZE : dialogue]),
            migration.SCRIPT_GAP_SHA256,
        )
        self.assertEqual(
            self.source_payload[
                dialogue + migration.SOURCE_RESIDENT_DIALOGUE_SIZE : walkmesh
            ],
            self.result_payload[
                dialogue + migration.OUTPUT_RESIDENT_DIALOGUE_SIZE : walkmesh
            ],
        )
        self.assertEqual(
            _sha256(
                self.result_payload[
                    dialogue + migration.OUTPUT_RESIDENT_DIALOGUE_SIZE : walkmesh
                ]
            ),
            migration.DIALOGUE_GAP_SHA256,
        )
        _, source_ram = migration._ram_from_payload(self.source_payload)
        _, result_ram = migration._ram_from_payload(self.result_payload)
        # Script's adjacent g_pFieldTriggerZones header/payload and the
        # dialogue's following heap header remain exact.
        self.assertEqual(source_ram[0x10C044:0x10C064], result_ram[0x10C044:0x10C064])
        self.assertEqual(source_ram[0x10D5C6:0x10D5E0], result_ram[0x10D5C6:0x10D5E0])
        self.assertLessEqual(
            migration.OUTPUT_RESIDENT_DIALOGUE_SIZE,
            migration.DIALOGUE_ALLOCATED_CAPACITY,
        )

    def test_runtime_pointers_e19_e20_gamestate_party_and_camera_are_identical(self) -> None:
        _, source_ram = migration._ram_from_payload(self.source_payload)
        _, result_ram = migration._ram_from_payload(self.result_payload)
        preserved = (
            (GAME_STATE, GAMESTATE_SIZE),
            (FIELD_SCRIPT_MEMORY, migration.FIELD_VARIABLE_BANK_SIZE),
            (migration.DIALOG_WINDOWS, migration.DIALOG_WINDOWS_SIZE),
            (migration.EXPECTED_TERMINAL_ACTOR_DATA, 0x138),
            (migration.EXPECTED_SCHEDULER_ACTOR_DATA, 0x138),
        )
        for start, size in preserved:
            self.assertEqual(source_ram[start : start + size], result_ram[start : start + size])
        self.assertEqual(
            result_ram[
                migration.EXPECTED_TERMINAL_ACTOR_DATA + migration.ACTOR_SCRIPT_SLOT_OFFSET :
                migration.EXPECTED_TERMINAL_ACTOR_DATA + migration.ACTOR_SCRIPT_SLOT_OFFSET + 8
            ],
            migration.EXPECTED_TERMINAL_SLOT0,
        )
        self.assertEqual(
            result_ram[
                migration.EXPECTED_TERMINAL_ACTOR_DATA + migration.ACTOR_CURRENT_PC_OFFSET :
                migration.EXPECTED_TERMINAL_ACTOR_DATA + migration.ACTOR_CURRENT_PC_OFFSET + 4
            ],
            migration.EXPECTED_TERMINAL_CURRENT,
        )
        self.assertEqual(
            result_ram[
                migration.EXPECTED_SCHEDULER_ACTOR_DATA + migration.ACTOR_SCRIPT_SLOT_OFFSET :
                migration.EXPECTED_SCHEDULER_ACTOR_DATA + migration.ACTOR_SCRIPT_SLOT_OFFSET + 8
            ],
            migration.EXPECTED_SCHEDULER_SLOT0,
        )
        self.assertEqual(
            result_ram[
                migration.EXPECTED_SCHEDULER_ACTOR_DATA + migration.ACTOR_CURRENT_PC_OFFSET :
                migration.EXPECTED_SCHEDULER_ACTOR_DATA + migration.ACTOR_CURRENT_PC_OFFSET + 4
            ],
            migration.EXPECTED_SCHEDULER_CURRENT,
        )
        for address in CAMERA_VECTORS.values():
            self.assertEqual(source_ram[address : address + 16], result_ram[address : address + 16])
        actor_base = struct.unpack_from("<I", source_ram, FIELD_ACTORS)[0] & 0x1FFFFFFF
        for entity in range(3):
            record = actor_base + entity * FIELD_ACTOR_STRIDE
            actor_data = struct.unpack_from(
                "<I", source_ram, record + FIELD_ACTOR_DATA_POINTER
            )[0] & 0x1FFFFFFF
            self.assertEqual(
                source_ram[record : record + FIELD_ACTOR_STRIDE],
                result_ram[record : record + FIELD_ACTOR_STRIDE],
            )
            self.assertEqual(
                source_ram[actor_data : actor_data + 0x138],
                result_ram[actor_data : actor_data + 0x138],
            )
        self.assertTrue(self.report["closed_window_pointers_preserved"])
        self.assertTrue(self.report["gamestate_party_camera_preserved"])

    def test_closed_window_stale_pointers_remain_valid_in_new_id55(self) -> None:
        base = migration.EXPECTED_DIALOGUE_GUEST_POINTER & 0x1FFFFFFF
        start = (migration.EXPECTED_WINDOW0_START_POINTER & 0x1FFFFFFF) - base
        current = (migration.EXPECTED_WINDOW0_CURRENT_POINTER & 0x1FFFFFFF) - base
        self.assertEqual(start, migration.RESIDENT_ID55_OFFSET)
        self.assertEqual(
            current,
            migration.RESIDENT_ID55_OFFSET + migration.V216_ID55_PAYLOAD_SIZE - 1,
        )
        self.assertEqual(self.result_resident_dialogue[current], 0)
        expected_payload = parse_dialogue(self.new_dialogue).blocks[55].payload
        self.assertEqual(
            self.result_resident_dialogue[
                start : start + migration.V216_ID55_PAYLOAD_SIZE
            ],
            expected_payload,
        )

    def test_wrong_source_or_resource_fails_closed(self) -> None:
        wrong_state = bytearray(self.source)
        wrong_state[0x100] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "Source Slot 1 identity"):
            migration.migrate_v215_slot1_to_v216(
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
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "V216 dialogue identity"):
            migration.migrate_v215_slot1_to_v216(
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
        before_size = migration.LIVE_SLOT1.stat().st_size
        before_sha = migration._file_sha256(migration.LIVE_SLOT1)
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
        self.assertEqual(migration.LIVE_SLOT1.stat().st_size, before_size)
        self.assertEqual(migration._file_sha256(migration.LIVE_SLOT1), before_sha)


if __name__ == "__main__":
    unittest.main()
