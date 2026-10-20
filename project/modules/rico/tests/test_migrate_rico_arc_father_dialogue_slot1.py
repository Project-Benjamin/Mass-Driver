from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

from pathlib import Path
import struct
import unittest

from tools.migrate_duckstation_disc_state import (
    DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
    DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    _Zstd,
)
from tools.migrate_rico_arc_father_dialogue_slot1 import (
    ACTIVE_DIALOGUE_ID,
    ACTIVE_DIALOGUE_OFFSET,
    ARCHIVE_TABLE_DIFFS,
    ARCHIVE_TABLE_PAYLOAD_OFFSET,
    ARCHIVE_TABLE_SIZE,
    BRIDGE_DIALOGUE_CAPACITY,
    BRIDGE_DIALOGUE_ID,
    BRIDGE_DIALOGUE_OFFSET,
    DEFAULT_NEW_DISC,
    DEFAULT_ZSTD,
    DIALOG_WINDOWS,
    DIALOG_WINDOW_COUNT,
    DIALOG_WINDOW_STRIDE,
    DOORWAY_SECOND_DIALOGUE_PC,
    EXPECTED_CONTINUATION_DIALOGUE,
    EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT,
    EXPECTED_FIRST_DIALOGUE,
    EXPECTED_OUTPUT_PAYLOAD_SHA256,
    EXPECTED_OUTPUT_SHA256,
    EXPECTED_OUTPUT_SIZE,
    EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT,
    EXPECTED_RESIDENT_DIALOGUE_SHA256,
    EXPECTED_RESIDENT_SCRIPT_SHA256,
    EXPECTED_SCRIPT_CHANGED_BYTE_COUNT,
    FIELD_SCRIPT_MEMORY,
    FIELD_VARIABLE_BANK_SIZE,
    FIRST_DIALOGUE_CAPACITY,
    FIRST_DIALOGUE_ID,
    FIRST_DIALOGUE_OFFSET,
    GAMESTATE_SIZE,
    GAME_STATE,
    LIVE_SLOT_ONE,
    NEXT_ALLOCATOR_HEADER,
    OBSOLETE_DIALOGUE_ID,
    RESIDENT_DIALOGUE_ALIGNMENT,
    RESIDENT_DIALOGUE_ALLOCATED_SIZE,
    RESIDENT_DIALOGUE_PAYLOAD_OFFSET,
    RESIDENT_DIALOGUE_UNUSED_TAIL,
    RESIDENT_DOORWAY_SECOND_DIALOGUE,
    RESIDENT_SCRIPT_PAYLOAD_OFFSET,
    RESIDENT_SCRIPT_SIZE,
    RicoFatherDialogueMigrationError,
    SCRIPT_BYTECODE_OFFSET,
    SCRIPT_DIALOGUE_GAP_SIZE,
    SOURCE_DIALOGUE_SIZE,
    SOURCE_DOORWAY_SECOND_DIALOGUE,
    SOURCE_FRAME_OFFSET,
    SOURCE_PAYLOAD_SHA256,
    SOURCE_STATE_SHA256,
    TARGET_CONTINUATION_DIALOGUE_SIZE,
    TARGET_CONTINUATION_DIMENSIONS,
    TARGET_DIALOGUE_SIZE,
    TARGET_FIRST_DIALOGUE_SIZE,
    TARGET_FIRST_DIMENSIONS,
    _choice_command,
    _dialogue_command,
    _differences,
    _raw_dialogue_blocks,
    _sha256,
    _validated_target_resources,
    main,
    migrate_state,
)
from tools.xgdialog import decode_text


ROOT = REPOSITORY_ROOT
SOURCE_STATE = ROOT / "work" / "rico_arc_before_father_doorway_rewrite_slot1.sav"


class RicoFatherDialogueSlotOneMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (SOURCE_STATE, DEFAULT_NEW_DISC, DEFAULT_ZSTD)
        if any(not path.is_file() for path in required):
            raise unittest.SkipTest(
                "Audited Rico Slot 1, father-dialogue stage, or zstd is unavailable"
            )
        cls.source_state = SOURCE_STATE.read_bytes()
        if _sha256(cls.source_state) != SOURCE_STATE_SHA256:
            raise unittest.SkipTest(
                "Archived pre-father-dialogue Slot 1 is no longer exact"
            )
        cls.zstd = _Zstd(DEFAULT_ZSTD)
        try:
            cls.result, cls.report = migrate_state(
                cls.source_state,
                zstd=cls.zstd,
                new_disc=DEFAULT_NEW_DISC,
            )
        except RicoFatherDialogueMigrationError as exc:
            raise unittest.SkipTest(
                "Slot 1 or staged media is no longer the audited source: "
                + str(exc)
            ) from exc

        source_frame = struct.unpack_from(
            "<I",
            cls.source_state,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET + 12,
        )[0]
        result_frame = struct.unpack_from(
            "<I",
            cls.result,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET + 12,
        )[0]
        cls.source_payload = cls.zstd.decompress(
            cls.source_state[source_frame:]
        )
        cls.result_payload = cls.zstd.decompress(cls.result[result_frame:])
        (
            cls.target_script,
            cls.target_dialogue,
            cls.target_table,
        ) = _validated_target_resources(DEFAULT_NEW_DISC)
        cls.source_script = cls.source_payload[
            RESIDENT_SCRIPT_PAYLOAD_OFFSET :
            RESIDENT_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE
        ]
        cls.result_script = cls.result_payload[
            RESIDENT_SCRIPT_PAYLOAD_OFFSET :
            RESIDENT_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE
        ]
        cls.source_dialogue = cls.source_payload[
            RESIDENT_DIALOGUE_PAYLOAD_OFFSET :
            RESIDENT_DIALOGUE_PAYLOAD_OFFSET + SOURCE_DIALOGUE_SIZE
        ]
        cls.result_dialogue = cls.result_payload[
            RESIDENT_DIALOGUE_PAYLOAD_OFFSET :
            RESIDENT_DIALOGUE_PAYLOAD_OFFSET + SOURCE_DIALOGUE_SIZE
        ]
        cls.source_blocks = _raw_dialogue_blocks(cls.source_dialogue)
        cls.result_blocks = _raw_dialogue_blocks(cls.result_dialogue)
        cls.target_blocks = _raw_dialogue_blocks(cls.target_dialogue)

    def test_exact_candidate_identity_and_report(self) -> None:
        self.assertEqual(len(self.result), EXPECTED_OUTPUT_SIZE)
        self.assertEqual(_sha256(self.result), EXPECTED_OUTPUT_SHA256)
        self.assertEqual(
            _sha256(self.result_payload),
            EXPECTED_OUTPUT_PAYLOAD_SHA256,
        )
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
        self.assertEqual(self.report["resident_fat_changed_byte_count"], 1)
        self.assertTrue(self.report["dialogue_offsets_preserved"])
        self.assertTrue(self.report["allocator_header_preserved"])
        self.assertFalse(self.report["script_allocation_relocated"])
        self.assertFalse(self.report["dialogue_allocation_relocated"])

    def test_only_future_script_dialogue_spans_and_one_fat_byte_change(self) -> None:
        script_diffs = _differences(self.source_script, self.result_script)
        self.assertEqual(
            script_diffs,
            (
                (
                    SCRIPT_BYTECODE_OFFSET + DOORWAY_SECOND_DIALOGUE_PC + 1,
                    OBSOLETE_DIALOGUE_ID,
                    BRIDGE_DIALOGUE_ID,
                ),
            ),
        )
        self.assertEqual(
            RESIDENT_SCRIPT_PAYLOAD_OFFSET + script_diffs[0][0],
            0x10DC6B,
        )

        dialogue_diffs = _differences(
            self.source_dialogue,
            self.result_dialogue,
        )
        allowed_dialogue_offsets = {
            # ID57's two dimension bytes and its fixed payload span.
            4 + len(self.source_blocks) * 2 + BRIDGE_DIALOGUE_ID * 2,
            4 + len(self.source_blocks) * 2 + BRIDGE_DIALOGUE_ID * 2 + 1,
            *range(
                BRIDGE_DIALOGUE_OFFSET,
                BRIDGE_DIALOGUE_OFFSET + BRIDGE_DIALOGUE_CAPACITY,
            ),
            *range(
                FIRST_DIALOGUE_OFFSET,
                FIRST_DIALOGUE_OFFSET + FIRST_DIALOGUE_CAPACITY,
            ),
        }
        self.assertEqual(len(dialogue_diffs), EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT)
        self.assertTrue(
            {offset for offset, _old, _new in dialogue_diffs}
            <= allowed_dialogue_offsets
        )

        expected = tuple(
            sorted(
                (
                    *(
                        (
                            RESIDENT_SCRIPT_PAYLOAD_OFFSET + offset,
                            old,
                            new,
                        )
                        for offset, old, new in script_diffs
                    ),
                    *(
                        (
                            RESIDENT_DIALOGUE_PAYLOAD_OFFSET + offset,
                            old,
                            new,
                        )
                        for offset, old, new in dialogue_diffs
                    ),
                    *(
                        (
                            ARCHIVE_TABLE_PAYLOAD_OFFSET + offset,
                            old,
                            new,
                        )
                        for offset, old, new in ARCHIVE_TABLE_DIFFS
                    ),
                )
            )
        )
        self.assertEqual(
            _differences(self.source_payload, self.result_payload),
            expected,
        )

    def test_rebuilt_media_has_the_normal_exact_two_block_exchange(self) -> None:
        self.assertEqual(self.target_script, self.source_script)
        self.assertEqual(len(self.target_dialogue), TARGET_DIALOGUE_SIZE)
        self.assertEqual(
            TARGET_DIALOGUE_SIZE - SOURCE_DIALOGUE_SIZE,
            129,
        )
        first = self.target_blocks[FIRST_DIALOGUE_ID]
        continuation = self.target_blocks[OBSOLETE_DIALOGUE_ID]
        self.assertEqual(
            (len(first.payload), first.width, first.height),
            (TARGET_FIRST_DIALOGUE_SIZE, *TARGET_FIRST_DIMENSIONS),
        )
        self.assertEqual(decode_text(first.payload), EXPECTED_FIRST_DIALOGUE)
        self.assertEqual(
            (
                len(continuation.payload),
                continuation.width,
                continuation.height,
            ),
            (
                TARGET_CONTINUATION_DIALOGUE_SIZE,
                *TARGET_CONTINUATION_DIMENSIONS,
            ),
        )
        self.assertEqual(
            decode_text(continuation.payload),
            EXPECTED_CONTINUATION_DIALOGUE,
        )
        self.assertEqual(
            self.target_script.count(_dialogue_command(OBSOLETE_DIALOGUE_ID)),
            1,
        )
        self.assertEqual(
            self.target_script.count(_dialogue_command(BRIDGE_DIALOGUE_ID)),
            0,
        )

    def test_resident_bridge_preserves_every_dialogue_offset(self) -> None:
        self.assertEqual(
            tuple(block.offset for block in self.result_blocks),
            tuple(block.offset for block in self.source_blocks),
        )
        self.assertEqual(
            _sha256(self.result_dialogue),
            EXPECTED_RESIDENT_DIALOGUE_SHA256,
        )
        self.assertEqual(
            _sha256(self.result_script),
            EXPECTED_RESIDENT_SCRIPT_SHA256,
        )

        target_first = self.target_blocks[FIRST_DIALOGUE_ID]
        target_continuation = self.target_blocks[OBSOLETE_DIALOGUE_ID]
        resident_first = self.result_blocks[FIRST_DIALOGUE_ID]
        resident_continuation = self.result_blocks[BRIDGE_DIALOGUE_ID]
        self.assertEqual(
            resident_first.payload,
            target_first.payload
            + bytes(FIRST_DIALOGUE_CAPACITY - len(target_first.payload)),
        )
        self.assertEqual(
            resident_continuation.payload,
            target_continuation.payload
            + bytes(
                BRIDGE_DIALOGUE_CAPACITY - len(target_continuation.payload)
            ),
        )
        self.assertEqual(
            (resident_continuation.width, resident_continuation.height),
            TARGET_CONTINUATION_DIMENSIONS,
        )
        self.assertEqual(
            decode_text(resident_first.payload),
            EXPECTED_FIRST_DIALOGUE
            + "<Close>" * (FIRST_DIALOGUE_CAPACITY - len(target_first.payload)),
        )
        self.assertEqual(
            decode_text(resident_continuation.payload),
            EXPECTED_CONTINUATION_DIALOGUE
            + "<Close>"
            * (BRIDGE_DIALOGUE_CAPACITY - len(target_continuation.payload)),
        )

        # The old answer remains byte-exact but cannot be reached: the only
        # F5-128 operand became F5-57.  This minimizes state mutation.
        self.assertEqual(
            self.result_blocks[OBSOLETE_DIALOGUE_ID],
            self.source_blocks[OBSOLETE_DIALOGUE_ID],
        )
        self.assertEqual(
            self.result_script.count(_dialogue_command(BRIDGE_DIALOGUE_ID)),
            1,
        )
        self.assertEqual(
            self.result_script.count(_choice_command(BRIDGE_DIALOGUE_ID)),
            0,
        )
        self.assertEqual(
            self.result_script.count(_dialogue_command(OBSOLETE_DIALOGUE_ID)),
            0,
        )

    def test_active_id39_window_and_progress_are_byte_exact(self) -> None:
        source_active = self.source_blocks[ACTIVE_DIALOGUE_ID]
        result_active = self.result_blocks[ACTIVE_DIALOGUE_ID]
        self.assertEqual(source_active, result_active)
        self.assertEqual(source_active.offset, ACTIVE_DIALOGUE_OFFSET)

        # All these addresses are relative to RAM; RAM begins at payload 0x1A62.
        ram = 0x1A62
        preserved = (
            (GAME_STATE, GAMESTATE_SIZE),
            (FIELD_SCRIPT_MEMORY, FIELD_VARIABLE_BANK_SIZE),
            (DIALOG_WINDOWS, DIALOG_WINDOW_STRIDE * DIALOG_WINDOW_COUNT),
        )
        for start, size in preserved:
            with self.subTest(start=hex(start)):
                self.assertEqual(
                    self.result_payload[ram + start : ram + start + size],
                    self.source_payload[ram + start : ram + start + size],
                )
        self.assertTrue(self.report["active_dialogue_window_preserved"])
        self.assertTrue(
            self.report["gamestate_field_variables_windows_preserved"]
        )

    def test_component_allocations_and_heap_neighbors_are_untouched(self) -> None:
        dialogue_start = RESIDENT_DIALOGUE_PAYLOAD_OFFSET
        dialogue_end = dialogue_start + SOURCE_DIALOGUE_SIZE
        allocated_end = dialogue_start + RESIDENT_DIALOGUE_ALLOCATED_SIZE
        aligned_end = allocated_end + len(RESIDENT_DIALOGUE_ALIGNMENT)
        header_end = aligned_end + len(NEXT_ALLOCATOR_HEADER)
        self.assertEqual(
            self.result_payload[dialogue_end:allocated_end],
            RESIDENT_DIALOGUE_UNUSED_TAIL,
        )
        self.assertEqual(
            self.result_payload[allocated_end:aligned_end],
            RESIDENT_DIALOGUE_ALIGNMENT,
        )
        self.assertEqual(
            self.result_payload[aligned_end:header_end],
            NEXT_ALLOCATOR_HEADER,
        )
        self.assertEqual(
            self.result_payload[dialogue_end:header_end],
            self.source_payload[dialogue_end:header_end],
        )
        script_end = RESIDENT_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE
        self.assertEqual(
            self.result_payload[
                script_end : script_end + SCRIPT_DIALOGUE_GAP_SIZE
            ],
            self.source_payload[
                script_end : script_end + SCRIPT_DIALOGUE_GAP_SIZE
            ],
        )
        # A naive copy would run 120 bytes into live heap ownership.
        self.assertEqual(
            TARGET_DIALOGUE_SIZE - RESIDENT_DIALOGUE_ALLOCATED_SIZE,
            120,
        )

    def test_resident_fat_matches_stage_except_volatile_tail(self) -> None:
        start = ARCHIVE_TABLE_PAYLOAD_OFFSET
        end = start + ARCHIVE_TABLE_SIZE
        source = self.source_payload[start:end]
        result = self.result_payload[start:end]
        self.assertEqual(result[:-1], self.target_table[:-1])
        self.assertEqual(result[-1], source[-1])
        self.assertEqual(
            _differences(source[:-1] + self.target_table[-1:], self.target_table),
            ARCHIVE_TABLE_DIFFS,
        )
        self.assertTrue(self.report["resident_fat_migrated"])
        self.assertTrue(
            self.report["cold_reload_uses_normal_two_block_dialogue"]
        )

    def test_prefix_and_payload_shape_are_preserved(self) -> None:
        self.assertEqual(_sha256(self.source_payload), SOURCE_PAYLOAD_SHA256)
        self.assertEqual(len(self.result_payload), len(self.source_payload))
        source_prefix = bytearray(self.source_state[:SOURCE_FRAME_OFFSET])
        result_prefix = bytearray(self.result[:SOURCE_FRAME_OFFSET])
        result_prefix[
            DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET :
            DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET + 4
        ] = source_prefix[
            DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET :
            DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET + 4
        ]
        self.assertEqual(result_prefix, source_prefix)

    def test_mutated_source_and_wrong_disc_are_rejected(self) -> None:
        changed = bytearray(self.source_state)
        changed[-1] ^= 1
        with self.assertRaisesRegex(
            RicoFatherDialogueMigrationError,
            "Source Slot 1 identity changed",
        ):
            migrate_state(
                bytes(changed),
                zstd=self.zstd,
                new_disc=DEFAULT_NEW_DISC,
            )
        with self.assertRaisesRegex(
            RicoFatherDialogueMigrationError,
            "Disc 1 identity changed",
        ):
            migrate_state(
                self.source_state,
                zstd=self.zstd,
                new_disc=LIVE_SLOT_ONE,
            )

    def test_cli_refuses_live_slot_output(self) -> None:
        with self.assertRaisesRegex(SystemExit, "live Slot 1"):
            main(
                (
                    str(LIVE_SLOT_ONE),
                    str(LIVE_SLOT_ONE),
                    "--new-disc",
                    str(DEFAULT_NEW_DISC),
                    "--zstd",
                    str(DEFAULT_ZSTD),
                )
            )


if __name__ == "__main__":
    unittest.main()
