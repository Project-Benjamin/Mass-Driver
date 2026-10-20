from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

from pathlib import Path
import struct
import unittest

from tools.migrate_duckstation_disc_state import (
    DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    _Zstd,
)
from tools.migrate_rico_arc_flower_dialogue_slot1 import (
    ACTIVE_DIALOGUE_ID,
    ARCHIVE_TABLE_DIFFS,
    ARCHIVE_TABLE_PAYLOAD_OFFSET,
    DEFAULT_NEW_DISC,
    DEFAULT_ZSTD,
    EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT,
    EXPECTED_OUTPUT_PAYLOAD_SHA256,
    EXPECTED_OUTPUT_SHA256,
    EXPECTED_OUTPUT_SIZE,
    EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT,
    EXPECTED_RESIDENT_DIALOGUE_SHA256,
    EXPECTED_RESIDENT_SCRIPT_SHA256,
    FLOWER_LESSON_OPERAND_OFFSET,
    LIVE_SLOT_ONE,
    RESIDENT_DIALOGUE_BLOCK_COUNT,
    RESIDENT_DIALOGUE_PAYLOAD_OFFSET,
    RESIDENT_DIALOGUE_SIZE,
    RESIDENT_LESSON_CAPACITY,
    RESIDENT_LESSON_DIALOGUE_ID,
    RESIDENT_LESSON_OFFSET,
    RESIDENT_QUESTION_CAPACITY,
    RESIDENT_QUESTION_DIALOGUE_ID,
    RESIDENT_QUESTION_OFFSET,
    RESIDENT_SCRIPT_PAYLOAD_OFFSET,
    RESIDENT_SCRIPT_SIZE,
    RicoFlowerDialogueMigrationError,
    SOURCE_PAYLOAD_SHA256,
    SOURCE_STATE_SHA256,
    TARGET_LESSON_DIALOGUE_ID,
    TARGET_LESSON_TEXT,
    TARGET_QUESTION_DIALOGUE_ID,
    TARGET_QUESTION_TEXT,
    _dialogue_dimensions_offset,
    _differences,
    _raw_dialogue_blocks,
    _sha256,
    _validated_target_resources,
    main,
    migrate_state,
)
from tools.xgdialog import decode_text


ROOT = REPOSITORY_ROOT
SOURCE_STATE = ROOT / "work" / "rico_arc_before_flower_dialogue_slot1.sav"


class RicoFlowerDialogueSlotOneMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (SOURCE_STATE, DEFAULT_NEW_DISC, DEFAULT_ZSTD)
        if any(not path.is_file() for path in required):
            raise unittest.SkipTest(
                "Audited flower-dialogue inputs are unavailable"
            )
        cls.source_state = SOURCE_STATE.read_bytes()
        if _sha256(cls.source_state) != SOURCE_STATE_SHA256:
            raise unittest.SkipTest("Archived source Slot 1 is no longer exact")
        cls.zstd = _Zstd(DEFAULT_ZSTD)
        cls.result, cls.report = migrate_state(
            cls.source_state,
            zstd=cls.zstd,
            new_disc=DEFAULT_NEW_DISC,
        )
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
        cls.source_payload = cls.zstd.decompress(cls.source_state[source_frame:])
        cls.result_payload = cls.zstd.decompress(cls.result[result_frame:])
        cls.target_script, cls.target_dialogue, cls.target_table = (
            _validated_target_resources(DEFAULT_NEW_DISC)
        )
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
            RESIDENT_DIALOGUE_PAYLOAD_OFFSET + RESIDENT_DIALOGUE_SIZE
        ]
        cls.result_dialogue = cls.result_payload[
            RESIDENT_DIALOGUE_PAYLOAD_OFFSET :
            RESIDENT_DIALOGUE_PAYLOAD_OFFSET + RESIDENT_DIALOGUE_SIZE
        ]
        cls.source_blocks = _raw_dialogue_blocks(cls.source_dialogue)
        cls.result_blocks = _raw_dialogue_blocks(cls.result_dialogue)
        cls.target_blocks = _raw_dialogue_blocks(cls.target_dialogue)

    def test_exact_candidate_identity_and_report(self) -> None:
        self.assertEqual(len(self.result), EXPECTED_OUTPUT_SIZE)
        self.assertEqual(_sha256(self.result), EXPECTED_OUTPUT_SHA256)
        self.assertEqual(_sha256(self.result_payload), EXPECTED_OUTPUT_PAYLOAD_SHA256)
        self.assertEqual(
            self.report["payload_changed_byte_count"],
            EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT,
        )
        self.assertEqual(self.report["resident_script_changed_byte_count"], 1)
        self.assertEqual(
            self.report["resident_dialogue_changed_byte_count"],
            EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT,
        )
        self.assertEqual(self.report["resident_fat_changed_byte_count"], 2)
        self.assertEqual(self.report["lesson_call_redirect"], "52->69")
        self.assertTrue(self.report["dialogue_offsets_preserved"])
        self.assertTrue(self.report["active_dialogue_window_preserved"])
        self.assertTrue(self.report["father_dialogue_bridge_preserved"])
        self.assertTrue(self.report["allocator_header_preserved"])

    def test_only_script_operand_fixed_dialogue_spans_and_fat_change(self) -> None:
        self.assertEqual(
            _differences(self.source_script, self.result_script),
            ((FLOWER_LESSON_OPERAND_OFFSET, 0x34, 0x45),),
        )
        dialogue_diffs = _differences(self.source_dialogue, self.result_dialogue)
        allowed = set()
        for block_id, offset, capacity in (
            (
                RESIDENT_QUESTION_DIALOGUE_ID,
                RESIDENT_QUESTION_OFFSET,
                RESIDENT_QUESTION_CAPACITY,
            ),
            (
                RESIDENT_LESSON_DIALOGUE_ID,
                RESIDENT_LESSON_OFFSET,
                RESIDENT_LESSON_CAPACITY,
            ),
        ):
            dimension = _dialogue_dimensions_offset(
                RESIDENT_DIALOGUE_BLOCK_COUNT,
                block_id,
            )
            allowed.update((dimension, dimension + 1))
            allowed.update(range(offset, offset + capacity))
        self.assertEqual(len(dialogue_diffs), EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT)
        self.assertTrue({offset for offset, _old, _new in dialogue_diffs} <= allowed)
        expected = tuple(
            sorted(
                (
                    *(
                        (RESIDENT_SCRIPT_PAYLOAD_OFFSET + o, a, b)
                        for o, a, b in _differences(
                            self.source_script,
                            self.result_script,
                        )
                    ),
                    *(
                        (RESIDENT_DIALOGUE_PAYLOAD_OFFSET + o, a, b)
                        for o, a, b in dialogue_diffs
                    ),
                    *(
                        (ARCHIVE_TABLE_PAYLOAD_OFFSET + o, a, b)
                        for o, a, b in ARCHIVE_TABLE_DIFFS
                    ),
                )
            )
        )
        self.assertEqual(_differences(self.source_payload, self.result_payload), expected)

    def test_target_and_resident_bridge_have_exact_new_conversation(self) -> None:
        target_question = self.target_blocks[TARGET_QUESTION_DIALOGUE_ID]
        target_lesson = self.target_blocks[TARGET_LESSON_DIALOGUE_ID]
        self.assertEqual(decode_text(target_question.payload), TARGET_QUESTION_TEXT)
        self.assertEqual(decode_text(target_lesson.payload), TARGET_LESSON_TEXT)
        resident_question = self.result_blocks[RESIDENT_QUESTION_DIALOGUE_ID]
        resident_lesson = self.result_blocks[RESIDENT_LESSON_DIALOGUE_ID]
        self.assertEqual(
            resident_question.payload,
            target_question.payload
            + bytes(RESIDENT_QUESTION_CAPACITY - len(target_question.payload)),
        )
        self.assertEqual(
            resident_lesson.payload,
            target_lesson.payload
            + bytes(RESIDENT_LESSON_CAPACITY - len(target_lesson.payload)),
        )
        self.assertEqual(_sha256(self.result_script), EXPECTED_RESIDENT_SCRIPT_SHA256)
        self.assertEqual(_sha256(self.result_dialogue), EXPECTED_RESIDENT_DIALOGUE_SHA256)

    def test_offsets_active_dialogue_and_father_bridge_are_preserved(self) -> None:
        self.assertEqual(
            tuple(block.offset for block in self.result_blocks),
            tuple(block.offset for block in self.source_blocks),
        )
        for block_id in range(RESIDENT_DIALOGUE_BLOCK_COUNT):
            if block_id not in {
                RESIDENT_QUESTION_DIALOGUE_ID,
                RESIDENT_LESSON_DIALOGUE_ID,
            }:
                with self.subTest(block_id=block_id):
                    self.assertEqual(
                        self.result_blocks[block_id],
                        self.source_blocks[block_id],
                    )
        self.assertEqual(
            self.result_blocks[ACTIVE_DIALOGUE_ID],
            self.source_blocks[ACTIVE_DIALOGUE_ID],
        )

    def test_source_identity_and_mutations_are_guarded(self) -> None:
        self.assertEqual(_sha256(self.source_payload), SOURCE_PAYLOAD_SHA256)
        changed = bytearray(self.source_state)
        changed[-1] ^= 1
        with self.assertRaisesRegex(
            RicoFlowerDialogueMigrationError,
            "Source Slot 1 identity changed",
        ):
            migrate_state(bytes(changed), zstd=self.zstd, new_disc=DEFAULT_NEW_DISC)
        with self.assertRaisesRegex(
            RicoFlowerDialogueMigrationError,
            "Disc 1 identity changed",
        ):
            migrate_state(self.source_state, zstd=self.zstd, new_disc=LIVE_SLOT_ONE)

    def test_cli_refuses_live_slot_output(self) -> None:
        with self.assertRaisesRegex(SystemExit, "live Slot 1"):
            main(
                (
                    str(SOURCE_STATE),
                    str(LIVE_SLOT_ONE),
                    "--new-disc",
                    str(DEFAULT_NEW_DISC),
                    "--zstd",
                    str(DEFAULT_ZSTD),
                )
            )


if __name__ == "__main__":
    unittest.main()
