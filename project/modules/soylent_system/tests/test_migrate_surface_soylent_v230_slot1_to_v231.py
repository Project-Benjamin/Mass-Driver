from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

from contextlib import redirect_stderr
import hashlib
import io
from pathlib import Path
import struct
import unittest

import tools.migrate_duckstation_disc_state as media_migration
import tools.migrate_surface_soylent_v230_slot1_to_v231 as migration
from tools.xgdeathblows import GAMESTATE_SIZE
from tools.xgdialog import parse_dialogue
from tools.xgscript import AtelScript
from work.read_duckstation_runtime import (
    CAMERA_VECTORS,
    FIELD_ACTORS,
    FIELD_ACTOR_DATA_POINTER,
    FIELD_ACTOR_STRIDE,
    FIELD_SCRIPT_MEMORY,
    GAME_STATE,
)


PROJECT_ROOT = REPOSITORY_ROOT
SOURCE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v230_patient_terminal_1eb8b434.sav"
)
CANDIDATE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v231_from_1eb8b434_field592_patient_record.sav"
)
OLD_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v230.bin"
)
NEW_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v231.bin"
)
OLD_STAGE = PROJECT_ROOT / "work" / "surface_soylent_campaign_v230_stage"
NEW_STAGE = PROJECT_ROOT / "work" / "surface_soylent_campaign_v231_stage"
OLD_FIELD = OLD_STAGE / "clones" / "field_592_disc1_donor"
NEW_FIELD = NEW_STAGE / "clones" / "field_592_disc1_donor"
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SurfaceSoylentV230Slot1MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (
            SOURCE_STATE,
            OLD_DISC,
            NEW_DISC,
            OLD_DISC.with_suffix(".cue"),
            NEW_DISC.with_suffix(".cue"),
            OLD_STAGE / "manifest.json",
            NEW_STAGE / "manifest.json",
            OLD_FIELD / "05_scripts.bin",
            NEW_FIELD / "05_scripts.bin",
            OLD_FIELD / "07_dialogue.bin",
            NEW_FIELD / "07_dialogue.bin",
            ZSTD,
        )
        if not all(path.is_file() for path in required):
            raise unittest.SkipTest("Pinned V230/V231 migration fixtures unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.old_manifest = (OLD_STAGE / "manifest.json").read_bytes()
        cls.new_manifest = (NEW_STAGE / "manifest.json").read_bytes()
        cls.old_script = (OLD_FIELD / "05_scripts.bin").read_bytes()
        cls.new_script = (NEW_FIELD / "05_scripts.bin").read_bytes()
        cls.old_dialogue = (OLD_FIELD / "07_dialogue.bin").read_bytes()
        cls.new_dialogue = (NEW_FIELD / "07_dialogue.bin").read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v230_slot1_to_v231(
            cls.source,
            old_disc=OLD_DISC,
            new_disc=NEW_DISC,
            old_manifest=cls.old_manifest,
            new_manifest=cls.new_manifest,
            old_script=cls.old_script,
            new_script=cls.new_script,
            old_dialogue=cls.old_dialogue,
            new_dialogue=cls.new_dialogue,
            zstd=cls.zstd,
        )
        cls.source_payload, cls.frame_start, cls.source_prefix = migration._unpack_state(
            cls.source, cls.zstd
        )
        cls.result_payload, cls.result_frame_start, cls.result_prefix = migration._unpack_state(
            cls.result, cls.zstd
        )
        _, cls.source_ram = migration._ram_from_payload(cls.source_payload)
        _, cls.result_ram = migration._ram_from_payload(cls.result_payload)
        cls.source_resident_script = cls.source_payload[
            migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET :
            migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + migration.RESIDENT_SCRIPT_SIZE
        ]
        cls.result_resident_script = cls.result_payload[
            migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET :
            migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + migration.RESIDENT_SCRIPT_SIZE
        ]
        cls.source_resident_dialogue = cls.source_payload[
            migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET :
            migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET + migration.RESIDENT_DIALOGUE_SIZE
        ]
        cls.result_resident_dialogue = cls.result_payload[
            migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET :
            migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET + migration.RESIDENT_DIALOGUE_SIZE
        ]

    def test_candidate_identity_round_trip_and_formal_file_are_frozen(self) -> None:
        self.assertEqual(
            (len(self.result), _sha256(self.result)),
            (migration.OUTPUT_STATE_SIZE, migration.OUTPUT_STATE_SHA256),
        )
        self.assertEqual(_sha256(self.result_payload), migration.OUTPUT_PAYLOAD_SHA256)
        self.assertEqual(_sha256(self.result_ram), migration.OUTPUT_RAM_SHA256)
        self.assertEqual(self.result_frame_start, self.frame_start)
        self.assertEqual(
            self.result_prefix,
            migration._expected_prefix(
                self.source_prefix,
                compressed_size=migration.OUTPUT_COMPRESSED_SIZE,
            ),
        )
        self.assertEqual(self.result.count(migration.OLD_CUE_NAME.encode()), 0)
        self.assertEqual(self.result.count(migration.NEW_CUE_NAME.encode()), 1)
        self.assertTrue(self.report["round_trip_verified"])
        self.assertTrue(self.report["allocator_safe"])
        if CANDIDATE_STATE.is_file():
            self.assertEqual(CANDIDATE_STATE.read_bytes(), self.result)

    def test_media_delta_and_cold_reload_use_ordinary_v231_id53(self) -> None:
        self.assertEqual(self.old_script, self.new_script)
        self.assertEqual(_sha256(self.old_script), migration.OLD_SCRIPT_SHA256)
        self.assertEqual(_sha256(self.old_dialogue), migration.OLD_DIALOGUE_SHA256)
        self.assertEqual(_sha256(self.new_dialogue), migration.NEW_DIALOGUE_SHA256)
        old = parse_dialogue(self.old_dialogue)
        new = parse_dialogue(self.new_dialogue)
        self.assertEqual(new.blocks[53].text, migration.TARGET_TERMINAL_TEXT)
        self.assertEqual(
            (len(new.blocks[53].payload), _sha256(new.blocks[53].payload)),
            (
                migration.TARGET_TERMINAL_PAYLOAD_SIZE,
                migration.TARGET_TERMINAL_PAYLOAD_SHA256,
            ),
        )
        for dialogue_id in range(migration.DIALOGUE_COUNT):
            if dialogue_id != 53:
                self.assertEqual(
                    (
                        old.blocks[dialogue_id].width,
                        old.blocks[dialogue_id].height,
                        old.blocks[dialogue_id].payload,
                    ),
                    (
                        new.blocks[dialogue_id].width,
                        new.blocks[dialogue_id].height,
                        new.blocks[dialogue_id].payload,
                    ),
                )
        editor = AtelScript(self.new_script)
        self.assertEqual(editor.get_script_pointer(19, 2), migration.TERMINAL_ACTION_PC)
        self.assertEqual(
            editor.bytecode[
                migration.TERMINAL_DIALOGUE_PC :
                migration.TERMINAL_DIALOGUE_PC
                + len(migration.TERMINAL_DIALOGUE_INSTRUCTION)
            ],
            migration.TERMINAL_DIALOGUE_INSTRUCTION,
        )
        self.assertTrue(self.report["cold_reload_uses_v231_id53"])

    def test_exact_source_is_field592_with_active_id53_close(self) -> None:
        self.assertEqual(
            (len(self.source), _sha256(self.source)),
            (migration.SOURCE_STATE_SIZE, migration.SOURCE_STATE_SHA256),
        )
        self.assertEqual(_sha256(self.source_payload), migration.SOURCE_PAYLOAD_SHA256)
        self.assertEqual(_sha256(self.source_ram), migration.SOURCE_RAM_SHA256)
        self.assertEqual(
            struct.unpack_from("<I", self.source_ram, migration.GAME_SCENE_MAP)[0],
            migration.EXPECTED_GAME_SCENE_MAP,
        )
        self.assertEqual(
            struct.unpack_from(
                "<I", self.source_ram, migration.WINDOW0_START_POINTER_OFFSET
            )[0],
            migration.SOURCE_WINDOW0_START_POINTER,
        )
        self.assertEqual(
            struct.unpack_from(
                "<I", self.source_ram, migration.WINDOW0_CURRENT_POINTER_OFFSET
            )[0],
            migration.SOURCE_WINDOW0_CURRENT_POINTER,
        )
        self.assertEqual(
            struct.unpack_from(
                "<h",
                self.source_ram,
                migration.DIALOG_WINDOWS + migration.DIALOG_WINDOW_STATUS_OFFSET,
            )[0],
            0,
        )
        self.assertEqual(
            self.source_ram[
                migration.EXPECTED_TERMINAL_ACTOR_DATA
                + migration.ACTOR_CURRENT_PC_OFFSET :
                migration.EXPECTED_TERMINAL_ACTOR_DATA
                + migration.ACTOR_CURRENT_PC_OFFSET
                + 4
            ],
            migration.EXPECTED_TERMINAL_CURRENT,
        )

    def test_id45_is_retired_then_becomes_the_one_resident_terminal_target(self) -> None:
        old_editor = AtelScript(self.source_resident_script)
        new_editor = AtelScript(self.result_resident_script)
        migration._validate_id45_retirement(old_editor)
        pointers = tuple(
            old_editor.get_script_pointer(entity, slot)
            for entity in range(old_editor.entity_count)
            for slot in range(32)
        )
        self.assertFalse(
            any(
                migration.RETIRED_RANGE[0] <= pointer < migration.RETIRED_RANGE[1]
                for pointer in pointers
            )
        )
        self.assertEqual(
            old_editor.bytecode.find(migration.RETIRED_ID45_REFERENCE),
            migration.RETIRED_ID45_REFERENCE_PC,
        )
        self.assertEqual(
            migration._diff_offsets(
                self.source_resident_script, self.result_resident_script
            ),
            (migration.SCRIPT_DIALOGUE_OPERAND_OFFSET,),
        )
        self.assertEqual(
            new_editor.bytecode[
                migration.TERMINAL_DIALOGUE_PC :
                migration.TERMINAL_DIALOGUE_PC
                + len(migration.RELOCATED_TERMINAL_DIALOGUE_INSTRUCTION)
            ],
            migration.RELOCATED_TERMINAL_DIALOGUE_INSTRUCTION,
        )
        self.assertEqual(
            new_editor.bytecode.find(migration.RETIRED_ID45_REFERENCE),
            migration.RETIRED_ID45_REFERENCE_PC,
        )
        self.assertTrue(self.report["retired_id45_cavity_proven"])
        self.assertTrue(self.report["resident_terminal_remapped_to_id45"])

    def test_v231_record_occupies_id45_cavity_without_resizing_dialogue(self) -> None:
        source = parse_dialogue(self.source_resident_dialogue)
        result = parse_dialogue(self.result_resident_dialogue)
        target = parse_dialogue(self.new_dialogue).blocks[53]
        self.assertEqual(len(self.source_resident_dialogue), migration.RESIDENT_DIALOGUE_SIZE)
        self.assertEqual(len(self.result_resident_dialogue), migration.RESIDENT_DIALOGUE_SIZE)
        self.assertEqual(
            _sha256(self.result_resident_dialogue),
            migration.OUTPUT_RESIDENT_DIALOGUE_SHA256,
        )
        for dialogue_id in range(migration.DIALOGUE_COUNT):
            if dialogue_id != migration.RELOCATION_DIALOGUE_ID:
                self.assertEqual(source.blocks[dialogue_id], result.blocks[dialogue_id])
        cavity = result.blocks[migration.RELOCATION_DIALOGUE_ID]
        self.assertEqual(
            (cavity.offset, len(cavity.payload), cavity.width, cavity.height),
            (
                migration.RELOCATION_OFFSET,
                migration.RELOCATION_CAPACITY,
                *migration.TARGET_TERMINAL_GRID,
            ),
        )
        self.assertEqual(cavity.payload[: len(target.payload)], target.payload)
        self.assertEqual(
            cavity.payload[len(target.payload) :],
            b"\x00" * (migration.RELOCATION_CAPACITY - len(target.payload)),
        )
        self.assertEqual(result.blocks[53], source.blocks[53])

    def test_payload_diff_is_exact_archive_script_cavity_and_two_pointers(self) -> None:
        actual = migration._diff_offsets(self.source_payload, self.result_payload)
        table_before = self.source_payload[
            migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
            migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
            + migration.ARCHIVE_TABLE_SIZE
        ]
        table_after = self.result_payload[
            migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
            migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
            + migration.ARCHIVE_TABLE_SIZE
        ]
        script_diffs = migration._diff_offsets(
            self.source_resident_script, self.result_resident_script
        )
        dialogue_diffs = migration._diff_offsets(
            self.source_resident_dialogue, self.result_resident_dialogue
        )
        source_windows = self.source_ram[
            migration.DIALOG_WINDOWS :
            migration.DIALOG_WINDOWS + migration.DIALOG_WINDOWS_SIZE
        ]
        result_windows = self.result_ram[
            migration.DIALOG_WINDOWS :
            migration.DIALOG_WINDOWS + migration.DIALOG_WINDOWS_SIZE
        ]
        window_diffs = migration._diff_offsets(source_windows, result_windows)
        expected = {
            *(
                migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + offset
                for offset in migration._diff_offsets(table_before, table_after)
            ),
            *(
                migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + offset
                for offset in script_diffs
            ),
            *(
                migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET + offset
                for offset in dialogue_diffs
            ),
            *(
                migration.EXPECTED_RAM_PAYLOAD_OFFSET
                + migration.DIALOG_WINDOWS
                + offset
                for offset in window_diffs
            ),
        }
        self.assertEqual(actual, tuple(sorted(expected)))
        self.assertEqual(len(actual), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        self.assertEqual(
            len(migration._diff_offsets(table_before, table_after)),
            migration.EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED,
        )
        self.assertEqual(len(script_diffs), 1)
        self.assertEqual(len(dialogue_diffs), 299)
        self.assertEqual(len(window_diffs), 4)
        self.assertEqual(self.report["payload_bytes_changed"], 2505)

    def test_component_sizes_gaps_walkmesh_and_heap_neighbors_are_identical(self) -> None:
        script_end = migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + migration.RESIDENT_SCRIPT_SIZE
        dialogue_end = (
            migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET + migration.RESIDENT_DIALOGUE_SIZE
        )
        self.assertEqual(
            self.source_payload[script_end : migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET],
            self.result_payload[script_end : migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET],
        )
        self.assertEqual(
            self.source_payload[dialogue_end : migration.EXPECTED_WALKMESH_PAYLOAD_OFFSET],
            self.result_payload[dialogue_end : migration.EXPECTED_WALKMESH_PAYLOAD_OFFSET],
        )
        self.assertEqual(
            self.source_payload[
                migration.EXPECTED_WALKMESH_PAYLOAD_OFFSET :
                migration.EXPECTED_WALKMESH_PAYLOAD_OFFSET + migration.WALKMESH_SIZE
            ],
            self.result_payload[
                migration.EXPECTED_WALKMESH_PAYLOAD_OFFSET :
                migration.EXPECTED_WALKMESH_PAYLOAD_OFFSET + migration.WALKMESH_SIZE
            ],
        )
        self.assertTrue(self.report["resident_component_sizes_preserved"])
        self.assertTrue(self.report["heap_neighbors_preserved"])

    def test_active_window_targets_relocated_record_and_its_authored_close(self) -> None:
        self.assertEqual(
            struct.unpack_from(
                "<I", self.result_ram, migration.WINDOW0_START_POINTER_OFFSET
            )[0],
            migration.OUTPUT_WINDOW0_START_POINTER,
        )
        self.assertEqual(
            struct.unpack_from(
                "<I", self.result_ram, migration.WINDOW0_CURRENT_POINTER_OFFSET
            )[0],
            migration.OUTPUT_WINDOW0_CURRENT_POINTER,
        )
        base = migration.EXPECTED_DIALOGUE_GUEST_POINTER & 0x1FFFFFFF
        start = (migration.OUTPUT_WINDOW0_START_POINTER & 0x1FFFFFFF) - base
        current = (migration.OUTPUT_WINDOW0_CURRENT_POINTER & 0x1FFFFFFF) - base
        target = parse_dialogue(self.new_dialogue).blocks[53]
        self.assertEqual(start, migration.RELOCATION_OFFSET)
        self.assertEqual(
            current,
            migration.RELOCATION_OFFSET + len(target.payload) - 1,
        )
        self.assertEqual(
            self.result_resident_dialogue[start : start + len(target.payload)],
            target.payload,
        )
        self.assertEqual(self.result_resident_dialogue[current], 0)
        self.assertEqual(
            struct.unpack_from(
                "<h",
                self.result_ram,
                migration.DIALOG_WINDOWS + migration.DIALOG_WINDOW_STATUS_OFFSET,
            )[0],
            0,
        )

    def test_fei_party_field_camera_actors_and_window_remainder_are_preserved(self) -> None:
        for start, size in (
            (GAME_STATE, GAMESTATE_SIZE),
            (FIELD_SCRIPT_MEMORY, migration.FIELD_VARIABLE_BANK_SIZE),
            (
                GAME_STATE + migration.FIELD_VARIABLE_BACKUP_OFFSET,
                migration.FIELD_VARIABLE_BANK_SIZE,
            ),
        ):
            self.assertEqual(
                self.source_ram[start : start + size],
                self.result_ram[start : start + size],
            )
        for address in CAMERA_VECTORS.values():
            self.assertEqual(
                self.source_ram[address : address + 16],
                self.result_ram[address : address + 16],
            )
        actor_base = struct.unpack_from("<I", self.source_ram, FIELD_ACTORS)[0] & 0x1FFFFFFF
        self.assertEqual(
            self.source_ram[
                actor_base : actor_base
                + migration.EXPECTED_ACTOR_COUNT * FIELD_ACTOR_STRIDE
            ],
            self.result_ram[
                actor_base : actor_base
                + migration.EXPECTED_ACTOR_COUNT * FIELD_ACTOR_STRIDE
            ],
        )
        for entity in range(migration.SCRIPT_ENTITY_COUNT):
            record = actor_base + entity * FIELD_ACTOR_STRIDE
            data = (
                struct.unpack_from(
                    "<I", self.source_ram, record + FIELD_ACTOR_DATA_POINTER
                )[0]
                & 0x1FFFFFFF
            )
            self.assertEqual(
                self.source_ram[data : data + migration.ACTOR_DATA_SIZE],
                self.result_ram[data : data + migration.ACTOR_DATA_SIZE],
            )
        source_window = bytearray(
            self.source_ram[
                migration.DIALOG_WINDOWS :
                migration.DIALOG_WINDOWS + migration.DIALOG_WINDOWS_SIZE
            ]
        )
        result_window = bytearray(
            self.result_ram[
                migration.DIALOG_WINDOWS :
                migration.DIALOG_WINDOWS + migration.DIALOG_WINDOWS_SIZE
            ]
        )
        for offset in (0x34, 0xA8):
            source_window[offset : offset + 4] = b"\x00" * 4
            result_window[offset : offset + 4] = b"\x00" * 4
        self.assertEqual(source_window, result_window)
        self.assertTrue(self.report["fei_party_gamestate_field_camera_preserved"])
        self.assertTrue(self.report["actor_runtime_preserved"])

    def test_wrong_source_or_resource_fails_closed(self) -> None:
        wrong_state = bytearray(self.source)
        wrong_state[0x100] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "Source Slot 1 identity"):
            migration.migrate_v230_slot1_to_v231(
                bytes(wrong_state),
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_manifest=self.old_manifest,
                new_manifest=self.new_manifest,
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
            "V230/V231 field-592 media delta drifted",
        ):
            migration.migrate_v230_slot1_to_v231(
                self.source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_manifest=self.old_manifest,
                new_manifest=self.new_manifest,
                old_script=self.old_script,
                new_script=self.new_script,
                old_dialogue=self.old_dialogue,
                new_dialogue=bytes(wrong_dialogue),
                zstd=self.zstd,
            )

    def test_cli_refuses_to_overwrite_live_slot1(self) -> None:
        before_size = migration.LIVE_SLOT1.stat().st_size
        before_sha256 = migration._file_sha256(migration.LIVE_SLOT1)
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = migration.main(
                (
                    str(SOURCE_STATE),
                    "--output",
                    str(migration.LIVE_SLOT1),
                    "--old-disc",
                    str(OLD_DISC),
                    "--new-disc",
                    str(NEW_DISC),
                    "--old-manifest",
                    str(OLD_STAGE / "manifest.json"),
                    "--new-manifest",
                    str(NEW_STAGE / "manifest.json"),
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
        self.assertEqual(migration._file_sha256(migration.LIVE_SLOT1), before_sha256)


if __name__ == "__main__":
    unittest.main()
