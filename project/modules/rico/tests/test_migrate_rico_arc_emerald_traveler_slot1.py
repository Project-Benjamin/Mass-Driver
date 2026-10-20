from __future__ import annotations

from pathlib import Path
import struct
import tempfile
import unittest

from tools import build_rico_arc as rico
from tools.migrate_duckstation_disc_state import (
    DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
    _Zstd,
)
from tools.migrate_rico_arc_emerald_traveler_slot1 import (
    ARCHIVE_TABLE_DIFFS,
    ARCHIVE_TABLE_PAYLOAD_OFFSET,
    ARCHIVE_TABLE_SIZE,
    DEFAULT_NEW_DISC,
    DEFAULT_OUTPUT,
    DEFAULT_SOURCE,
    DEFAULT_TARGET_BUNDLE,
    DEFAULT_ZSTD,
    DIALOGUE_ALIGNMENT,
    DIALOG_WINDOWS,
    DIALOG_WINDOW_COUNT,
    DIALOG_WINDOW_STRIDE,
    EXPECTED_COMPRESSED_SHA256,
    EXPECTED_COMPRESSED_SIZE,
    EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT,
    EXPECTED_FAT_CHANGED_BYTE_COUNT,
    EXPECTED_OUTPUT_PAYLOAD_SHA256,
    EXPECTED_OUTPUT_RAM_SHA256,
    EXPECTED_OUTPUT_SHA256,
    EXPECTED_OUTPUT_SIZE,
    EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT,
    EXPECTED_PROGRESS_CHANGED_BYTE_COUNT,
    EXPECTED_SCRIPT_CHANGED_BYTE_COUNT,
    EXPECTED_TARGET_READING_FIRST_TEXT,
    EXPECTED_TARGET_READING_REPEAT_TEXT,
    EXPECTED_TARGET_WINDOW_TEXT,
    FIELD_VARIABLE_BANK_SIZE,
    GAMESTATE_SIZE,
    LIVE_SLOT_ONE,
    NEXT_ALLOCATOR_HEADER,
    NEXT_CONTROLLER_ENTITY,
    NEXT_CONTROLLER_INIT_PC,
    NEXT_CONTROLLER_UPDATE_PC,
    OBSOLETE_DIALOGUE_TAIL_SIZE,
    PLAYABLE_STATE_PAYLOAD_OFFSET,
    PLAYABLE_STATE_RAM_OFFSET,
    READING_ACTION_PC,
    READING_ACTION_SCRIPT,
    READING_ACTION_SIZE,
    READING_ACTION_TRAILING_STOP_BYTES,
    READING_CONTROLLER_ENTITY,
    RESIDENT_DIALOGUE_PAYLOAD_OFFSET,
    RESIDENT_SCRIPT_PAYLOAD_OFFSET,
    RESIDENT_SCRIPT_SIZE,
    RicoEmeraldTravelerMigrationError,
    SOURCE_DIALOGUE_BLOCK_COUNT,
    SOURCE_FRAME_OFFSET,
    SOURCE_MEDIA_PATH,
    SOURCE_PAYLOAD_SHA256,
    SOURCE_PLAYABLE_STATE,
    SOURCE_RAM_OFFSET,
    SOURCE_READING_FIRST_DIALOGUE_IDS,
    SOURCE_RESIDENT_DIALOGUE_SIZE,
    SOURCE_STATE_SHA256,
    TARGET_ARCHIVE_TABLE_SHA256,
    TARGET_DIALOGUE_BLOCK_COUNT,
    TARGET_DIALOGUE_SIZE,
    TARGET_PLAYABLE_STATE,
    TARGET_READING_FIRST_DIALOGUE_ID,
    TARGET_READING_REPEAT_DIALOGUE_ID,
    TARGET_RESIDENT_ARCHIVE_TABLE_SHA256,
    TARGET_RESIDENT_DIALOGUE_SPAN_SHA256,
    TARGET_RESIDENT_SCRIPT_SHA256,
    _differences,
    _raw_dialogue_blocks,
    _sha256,
    _validated_target_resources,
    main,
    migrate_state,
)
from tools.xgdialog import decode_text
from tools.xgscript import AtelScript
from work.read_duckstation_runtime import (
    FIELD_ACTORS,
    FIELD_ACTOR_DATA_POINTER,
    FIELD_ACTOR_STRIDE,
    FIELD_SCRIPT_MEMORY,
    GAME_STATE,
    RAM_SIZE,
)


class RicoEmeraldTravelerSlotOneMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (
            DEFAULT_SOURCE,
            DEFAULT_NEW_DISC,
            DEFAULT_TARGET_BUNDLE,
            DEFAULT_ZSTD,
        )
        if any(not path.is_file() for path in required):
            raise unittest.SkipTest(
                "Audited Emerald Traveler migration inputs are unavailable"
            )
        cls.source_state = DEFAULT_SOURCE.read_bytes()
        if _sha256(cls.source_state) != SOURCE_STATE_SHA256:
            raise unittest.SkipTest("Archived Slot 1 source is no longer exact")
        cls.zstd = _Zstd(DEFAULT_ZSTD)
        cls.result, cls.report = migrate_state(
            cls.source_state,
            zstd=cls.zstd,
            new_disc=DEFAULT_NEW_DISC,
            target_bundle=DEFAULT_TARGET_BUNDLE,
        )
        cls.source_payload = cls.zstd.decompress(
            cls.source_state[SOURCE_FRAME_OFFSET:]
        )
        cls.result_payload = cls.zstd.decompress(cls.result[SOURCE_FRAME_OFFSET:])
        cls.source_ram = cls.source_payload[
            SOURCE_RAM_OFFSET : SOURCE_RAM_OFFSET + RAM_SIZE
        ]
        cls.result_ram = cls.result_payload[
            SOURCE_RAM_OFFSET : SOURCE_RAM_OFFSET + RAM_SIZE
        ]
        (
            cls.target_script,
            cls.target_dialogue,
            cls.target_table,
        ) = _validated_target_resources(
            DEFAULT_NEW_DISC,
            DEFAULT_TARGET_BUNDLE,
        )
        cls.source_script = cls.source_payload[
            RESIDENT_SCRIPT_PAYLOAD_OFFSET :
            RESIDENT_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE
        ]
        cls.source_dialogue = cls.source_payload[
            RESIDENT_DIALOGUE_PAYLOAD_OFFSET :
            RESIDENT_DIALOGUE_PAYLOAD_OFFSET + SOURCE_RESIDENT_DIALOGUE_SIZE
        ]

    def test_exact_candidate_identity_and_report(self) -> None:
        self.assertEqual(len(self.result), EXPECTED_OUTPUT_SIZE)
        self.assertEqual(_sha256(self.result), EXPECTED_OUTPUT_SHA256)
        self.assertEqual(_sha256(self.source_payload), SOURCE_PAYLOAD_SHA256)
        self.assertEqual(
            _sha256(self.result_payload),
            EXPECTED_OUTPUT_PAYLOAD_SHA256,
        )
        self.assertEqual(_sha256(self.result_ram), EXPECTED_OUTPUT_RAM_SHA256)
        compressed = self.result[SOURCE_FRAME_OFFSET:]
        self.assertEqual(len(compressed), EXPECTED_COMPRESSED_SIZE)
        self.assertEqual(_sha256(compressed), EXPECTED_COMPRESSED_SHA256)
        self.assertEqual(
            self.report["payload_changed_byte_count"],
            EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT,
        )
        self.assertEqual(
            self.report["resident_script_changed_byte_count"],
            EXPECTED_SCRIPT_CHANGED_BYTE_COUNT,
        )
        self.assertEqual(
            self.report["resident_dialogue_changed_byte_count"],
            EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT,
        )
        self.assertEqual(
            self.report["dialogue_zeroed_tail_size"],
            OBSOLETE_DIALOGUE_TAIL_SIZE,
        )
        self.assertEqual(
            self.report["resident_fat_changed_byte_count"],
            EXPECTED_FAT_CHANGED_BYTE_COUNT,
        )
        self.assertEqual(
            self.report["progress_changed_byte_count"],
            EXPECTED_PROGRESS_CHANGED_BYTE_COUNT,
        )
        for key in (
            "reading_complete_bit_cleared",
            "first_use_narration_ready",
            "closed_dialogue_windows_preserved",
            "actor_vm_state_preserved",
            "game_state_preserved",
            "allocator_alignment_preserved",
            "allocator_header_preserved",
            "resident_fat_migrated",
        ):
            self.assertTrue(self.report[key], key)
        self.assertFalse(self.report["dialogue_allocation_relocated"])
        self.assertFalse(self.report["media_path_rewrite_required"])

        expected_prefix = bytearray(self.source_state[:SOURCE_FRAME_OFFSET])
        struct.pack_into(
            "<I",
            expected_prefix,
            DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
            EXPECTED_COMPRESSED_SIZE,
        )
        self.assertEqual(self.result[:SOURCE_FRAME_OFFSET], bytes(expected_prefix))
        self.assertEqual(self.result.count(SOURCE_MEDIA_PATH), 1)

    def test_payload_changes_are_the_exact_four_allowed_groups(self) -> None:
        result_script = self.result_payload[
            RESIDENT_SCRIPT_PAYLOAD_OFFSET :
            RESIDENT_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE
        ]
        target_dialogue_span = self.target_dialogue + bytes(
            OBSOLETE_DIALOGUE_TAIL_SIZE
        )
        script_differences = _differences(self.source_script, result_script)
        dialogue_differences = _differences(
            self.source_dialogue,
            target_dialogue_span,
        )
        progress_differences = _differences(
            self.source_payload[
                PLAYABLE_STATE_PAYLOAD_OFFSET : PLAYABLE_STATE_PAYLOAD_OFFSET + 2
            ],
            self.result_payload[
                PLAYABLE_STATE_PAYLOAD_OFFSET : PLAYABLE_STATE_PAYLOAD_OFFSET + 2
            ],
        )
        expected = tuple(
            sorted(
                (
                    *(
                        (RESIDENT_SCRIPT_PAYLOAD_OFFSET + offset, old, new)
                        for offset, old, new in script_differences
                    ),
                    *(
                        (RESIDENT_DIALOGUE_PAYLOAD_OFFSET + offset, old, new)
                        for offset, old, new in dialogue_differences
                    ),
                    *(
                        (ARCHIVE_TABLE_PAYLOAD_OFFSET + offset, old, new)
                        for offset, old, new in ARCHIVE_TABLE_DIFFS
                    ),
                    *(
                        (PLAYABLE_STATE_PAYLOAD_OFFSET + offset, old, new)
                        for offset, old, new in progress_differences
                    ),
                )
            )
        )
        self.assertEqual(len(script_differences), EXPECTED_SCRIPT_CHANGED_BYTE_COUNT)
        self.assertEqual(
            len(dialogue_differences),
            EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT,
        )
        self.assertEqual(progress_differences, ((1, 1, 0),))
        self.assertEqual(len(expected), EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT)
        self.assertEqual(
            _differences(self.source_payload, self.result_payload),
            expected,
        )

    def test_shorter_dialogue_stays_inside_the_resident_allocation(self) -> None:
        target_end = RESIDENT_DIALOGUE_PAYLOAD_OFFSET + TARGET_DIALOGUE_SIZE
        source_end = (
            RESIDENT_DIALOGUE_PAYLOAD_OFFSET + SOURCE_RESIDENT_DIALOGUE_SIZE
        )
        alignment_end = source_end + len(DIALOGUE_ALIGNMENT)
        header_end = alignment_end + len(NEXT_ALLOCATOR_HEADER)
        self.assertEqual(
            self.result_payload[
                RESIDENT_DIALOGUE_PAYLOAD_OFFSET:target_end
            ],
            self.target_dialogue,
        )
        self.assertEqual(
            self.result_payload[target_end:source_end],
            bytes(OBSOLETE_DIALOGUE_TAIL_SIZE),
        )
        self.assertEqual(
            _sha256(
                self.result_payload[
                    RESIDENT_DIALOGUE_PAYLOAD_OFFSET:source_end
                ]
            ),
            TARGET_RESIDENT_DIALOGUE_SPAN_SHA256,
        )
        self.assertEqual(
            self.result_payload[source_end:alignment_end],
            DIALOGUE_ALIGNMENT,
        )
        self.assertEqual(
            self.result_payload[alignment_end:header_end],
            NEXT_ALLOCATOR_HEADER,
        )
        self.assertEqual(
            self.result_payload[source_end:header_end],
            self.source_payload[source_end:header_end],
        )

    def test_first_use_bit_is_cleared_without_changing_other_gameplay_state(self) -> None:
        self.assertEqual(
            struct.unpack_from(
                "<H",
                self.source_ram,
                PLAYABLE_STATE_RAM_OFFSET,
            )[0],
            SOURCE_PLAYABLE_STATE,
        )
        self.assertEqual(
            struct.unpack_from(
                "<H",
                self.result_ram,
                PLAYABLE_STATE_RAM_OFFSET,
            )[0],
            TARGET_PLAYABLE_STATE,
        )
        source_bank = self.source_ram[
            FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE
        ]
        result_bank = self.result_ram[
            FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE
        ]
        self.assertEqual(
            _differences(source_bank, result_bank),
            ((rico.PLAYABLE_STATE_VARIABLE + 1, 1, 0),),
        )
        self.assertEqual(
            self.result_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
            self.source_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
        )
        window_slice = slice(
            DIALOG_WINDOWS,
            DIALOG_WINDOWS + DIALOG_WINDOW_STRIDE * DIALOG_WINDOW_COUNT,
        )
        self.assertEqual(
            self.result_ram[window_slice],
            self.source_ram[window_slice],
        )

    def test_padded_script_preserves_live_actor_program_counters(self) -> None:
        result_script = self.result_payload[
            RESIDENT_SCRIPT_PAYLOAD_OFFSET :
            RESIDENT_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE
        ]
        self.assertEqual(result_script, self.target_script)
        self.assertEqual(_sha256(result_script), TARGET_RESIDENT_SCRIPT_SHA256)
        editor = AtelScript(result_script)
        reading_pc = editor.get_script_pointer(
            READING_CONTROLLER_ENTITY,
            READING_ACTION_SCRIPT,
        )
        next_pc = editor.get_script_pointer(NEXT_CONTROLLER_ENTITY, 0)
        self.assertEqual(reading_pc, READING_ACTION_PC)
        self.assertEqual(next_pc, NEXT_CONTROLLER_INIT_PC)
        self.assertEqual(
            editor.get_script_pointer(NEXT_CONTROLLER_ENTITY, 1),
            NEXT_CONTROLLER_UPDATE_PC,
        )
        reading_action = editor.bytecode[reading_pc:next_pc]
        self.assertEqual(len(reading_action), READING_ACTION_SIZE)
        self.assertEqual(
            reading_action[-READING_ACTION_TRAILING_STOP_BYTES:],
            bytes(READING_ACTION_TRAILING_STOP_BYTES),
        )

        actor_array = struct.unpack_from("<I", self.source_ram, FIELD_ACTORS)[0]
        actor_array &= 0x1FFFFFFF
        controller_record = actor_array + NEXT_CONTROLLER_ENTITY * FIELD_ACTOR_STRIDE
        actor_data = struct.unpack_from(
            "<I",
            self.source_ram,
            controller_record + FIELD_ACTOR_DATA_POINTER,
        )[0]
        actor_data &= 0x1FFFFFFF
        for pc_offset in (0x8C, 0xCC):
            self.assertEqual(
                struct.unpack_from("<H", self.source_ram, actor_data + pc_offset)[0],
                0x0AB6,
            )
            self.assertEqual(
                self.result_ram[actor_data + pc_offset : actor_data + pc_offset + 2],
                self.source_ram[actor_data + pc_offset : actor_data + pc_offset + 2],
            )

    def test_target_dialogue_is_the_requested_window_and_book_narration(self) -> None:
        source_blocks = _raw_dialogue_blocks(self.source_dialogue)
        target_blocks = _raw_dialogue_blocks(self.target_dialogue)
        self.assertEqual(len(source_blocks), SOURCE_DIALOGUE_BLOCK_COUNT)
        self.assertEqual(len(target_blocks), TARGET_DIALOGUE_BLOCK_COUNT)
        self.assertEqual(
            decode_text(target_blocks[81].payload),
            EXPECTED_TARGET_WINDOW_TEXT,
        )
        self.assertNotIn("slat", decode_text(target_blocks[81].payload).casefold())
        self.assertEqual(
            decode_text(target_blocks[TARGET_READING_REPEAT_DIALOGUE_ID].payload),
            EXPECTED_TARGET_READING_REPEAT_TEXT,
        )
        self.assertEqual(
            decode_text(target_blocks[TARGET_READING_FIRST_DIALOGUE_ID].payload),
            EXPECTED_TARGET_READING_FIRST_TEXT,
        )
        editor = AtelScript(self.target_script)
        action = editor.bytecode[
            READING_ACTION_PC:NEXT_CONTROLLER_INIT_PC
        ]
        for block_id in SOURCE_READING_FIRST_DIALOGUE_IDS[1:]:
            self.assertNotIn(
                b"\xF5" + struct.pack("<H", block_id),
                action,
            )

    def test_resident_fat_matches_target_while_preserving_volatile_byte(self) -> None:
        resident = self.result_payload[
            ARCHIVE_TABLE_PAYLOAD_OFFSET :
            ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
        ]
        self.assertEqual(_sha256(self.target_table), TARGET_ARCHIVE_TABLE_SHA256)
        self.assertEqual(_sha256(resident), TARGET_RESIDENT_ARCHIVE_TABLE_SHA256)
        self.assertEqual(resident[:-1], self.target_table[:-1])
        self.assertEqual(resident[-1], 0xC4)
        self.assertEqual(self.target_table[-1], 0)

    def test_source_target_and_cli_output_guards(self) -> None:
        changed = bytearray(self.source_state)
        changed[-1] ^= 1
        with self.assertRaisesRegex(
            RicoEmeraldTravelerMigrationError,
            "Source Slot 1 identity changed",
        ):
            migrate_state(
                bytes(changed),
                zstd=self.zstd,
                new_disc=DEFAULT_NEW_DISC,
                target_bundle=DEFAULT_TARGET_BUNDLE,
            )
        with self.assertRaisesRegex(
            RicoEmeraldTravelerMigrationError,
            "Disc 1 identity changed",
        ):
            migrate_state(
                self.source_state,
                zstd=self.zstd,
                new_disc=LIVE_SLOT_ONE,
                target_bundle=DEFAULT_TARGET_BUNDLE,
            )
        with self.assertRaisesRegex(
            RicoEmeraldTravelerMigrationError,
            "bundle identity changed",
        ):
            migrate_state(
                self.source_state,
                zstd=self.zstd,
                new_disc=DEFAULT_NEW_DISC,
                target_bundle=LIVE_SLOT_ONE,
            )
        with self.assertRaisesRegex(SystemExit, "live Slot 1"):
            main((str(DEFAULT_SOURCE), str(LIVE_SLOT_ONE)))
        with tempfile.TemporaryDirectory() as directory:
            source_copy = Path(directory) / "source.sav"
            source_copy.write_bytes(self.source_state)
            with self.assertRaisesRegex(SystemExit, "source state"):
                main((str(source_copy), str(source_copy)))
        self.assertEqual(DEFAULT_OUTPUT.parent.name, "save_candidates")

    def test_cli_writes_only_a_separate_candidate(self) -> None:
        source_hash = _sha256(DEFAULT_SOURCE.read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "emerald_traveler.sav"
            self.assertEqual(
                main(
                    (
                        str(DEFAULT_SOURCE),
                        str(output),
                        "--new-disc",
                        str(DEFAULT_NEW_DISC),
                        "--target-bundle",
                        str(DEFAULT_TARGET_BUNDLE),
                        "--zstd",
                        str(DEFAULT_ZSTD),
                    )
                ),
                0,
            )
            self.assertEqual(output.read_bytes(), self.result)
        self.assertEqual(_sha256(DEFAULT_SOURCE.read_bytes()), source_hash)


if __name__ == "__main__":
    unittest.main()
