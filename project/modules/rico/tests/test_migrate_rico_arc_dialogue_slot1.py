from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

import hashlib
from pathlib import Path
import struct
import unittest

from tools import build_rico_arc as rico
from tools.migrate_duckstation_disc_state import (
    DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    _Zstd,
)
from tools.migrate_rico_arc_dialogue_slot1 import (
    ARCHIVE_TABLE_DIFFS,
    ARCHIVE_TABLE_PAYLOAD_OFFSET,
    ARCHIVE_TABLE_SIZE,
    DEFAULT_NEW_DISC,
    DEFAULT_ZSTD,
    EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT,
    EXPECTED_REPAIRED_PAYLOAD_SHA256,
    EXPECTED_REPAIRED_STATE_SHA256,
    EXPECTED_REPAIRED_STATE_SIZE,
    LIVE_SLOT_ONE,
    NEXT_ALLOCATOR_HEADER,
    RESIDENT_DIALOGUE_PADDING,
    RESIDENT_DIALOGUE_PAYLOAD_OFFSET,
    RESIDENT_DIALOGUE_SIZE,
    RicoChapterOneDialogueMigrationError,
    SOURCE_FRAME_OFFSET,
    SOURCE_PAYLOAD_SHA256,
    SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256,
    TARGET_DIALOGUE_SHA256,
    TARGET_RESIDENT_ARCHIVE_TABLE_SHA256,
    _differences,
    _sha256,
    _validated_target_dialogue,
    main,
    migrate_state,
)
from tools.xgdialog import decode_text, encode_text


ROOT = REPOSITORY_ROOT


class RicoChapterOneDialogueSlotOneMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (LIVE_SLOT_ONE, DEFAULT_NEW_DISC, DEFAULT_ZSTD)
        if any(not path.is_file() for path in required):
            raise unittest.SkipTest(
                "Audited Rico Slot 1, staged Disc 1, or zstd is unavailable"
            )
        cls.source_state = LIVE_SLOT_ONE.read_bytes()
        cls.zstd = _Zstd(DEFAULT_ZSTD)
        try:
            cls.result, cls.report = migrate_state(
                cls.source_state,
                zstd=cls.zstd,
                new_disc=DEFAULT_NEW_DISC,
            )
        except RicoChapterOneDialogueMigrationError as exc:
            raise unittest.SkipTest(
                "Live Slot 1 or staged media is no longer the audited source: "
                + str(exc)
            ) from exc

        (
            _source_type,
            _source_compressed_size,
            _source_payload_size,
            source_frame_offset,
        ) = struct.unpack_from(
            "<IIII",
            cls.source_state,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
        )
        (
            _result_type,
            _result_compressed_size,
            _result_payload_size,
            result_frame_offset,
        ) = struct.unpack_from(
            "<IIII",
            cls.result,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
        )
        cls.source_payload = cls.zstd.decompress(
            cls.source_state[source_frame_offset:]
        )
        cls.result_payload = cls.zstd.decompress(
            cls.result[result_frame_offset:]
        )
        cls.target_dialogue, cls.target_archive_table = (
            _validated_target_dialogue(DEFAULT_NEW_DISC)
        )

    def test_exact_candidate_identity_and_report(self) -> None:
        self.assertEqual(len(self.result), EXPECTED_REPAIRED_STATE_SIZE)
        self.assertEqual(_sha256(self.result), EXPECTED_REPAIRED_STATE_SHA256)
        self.assertEqual(
            _sha256(self.result_payload),
            EXPECTED_REPAIRED_PAYLOAD_SHA256,
        )
        self.assertEqual(
            self.report["dialogue_changed_byte_count"],
            EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT,
        )
        self.assertEqual(
            self.report["resident_archive_table_changed_byte_count"],
            len(ARCHIVE_TABLE_DIFFS),
        )
        self.assertTrue(self.report["allocator_header_preserved"])
        self.assertFalse(self.report["dialogue_allocation_relocated"])
        self.assertTrue(self.report["resident_fat_migrated"])
        self.assertFalse(self.report["media_path_rewrite_required"])

    def test_only_dialogue_and_one_resident_fat_byte_change(self) -> None:
        start = RESIDENT_DIALOGUE_PAYLOAD_OFFSET
        end = start + RESIDENT_DIALOGUE_SIZE
        dialogue_changes = _differences(
            self.source_payload[start:end],
            self.target_dialogue,
        )
        expected = tuple(
            sorted(
                (
                    *(
                        (start + offset, old, new)
                        for offset, old, new in dialogue_changes
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
        self.assertEqual(len(dialogue_changes), 633)
        self.assertEqual(_sha256(self.target_dialogue), TARGET_DIALOGUE_SHA256)

    def test_dialogue_allocation_boundary_is_byte_exact(self) -> None:
        start = RESIDENT_DIALOGUE_PAYLOAD_OFFSET
        end = start + RESIDENT_DIALOGUE_SIZE
        padding_end = end + len(RESIDENT_DIALOGUE_PADDING)
        header_end = padding_end + len(NEXT_ALLOCATOR_HEADER)

        self.assertEqual(self.result_payload[start:end], self.target_dialogue)
        self.assertEqual(
            self.result_payload[end:padding_end],
            RESIDENT_DIALOGUE_PADDING,
        )
        self.assertEqual(
            self.result_payload[padding_end:header_end],
            NEXT_ALLOCATOR_HEADER,
        )
        self.assertEqual(
            self.result_payload[end:header_end],
            self.source_payload[end:header_end],
        )

    def test_authored_blocks_keep_their_ids_dimensions_and_new_text(self) -> None:
        component = self.target_dialogue
        block_count = struct.unpack_from("<I", component, 0)[0] + 1
        self.assertEqual(block_count, 129)
        offsets = tuple(
            struct.unpack_from("<H", component, 4 + index * 2)[0]
            for index in range(block_count)
        )
        dimensions_start = 4 + block_count * 2
        chapter = rico.load_chapters()[0]

        # Donor field 229 has 27 retail dialogue IDs; authored block 12 is 39.
        for authored_index in range(12, 19):
            dialogue_id = 27 + authored_index
            start = offsets[dialogue_id]
            end = offsets[dialogue_id + 1]
            actual = decode_text(component[start:end])
            expected = rico._reflow_dialogue_text(
                chapter.blocks[authored_index],
                sentence_safe_pages=True,
            )
            self.assertEqual(actual, expected)
            self.assertEqual(
                tuple(
                    component[
                        dimensions_start
                        + dialogue_id * 2 : dimensions_start
                        + dialogue_id * 2
                        + 2
                    ]
                ),
                rico._dialogue_window_dimensions(expected),
            )
            self.assertEqual(component.count(encode_text(expected)), 1)

        revised = "\n".join(chapter.blocks[12:19])
        self.assertIn("The medicine isn't helping", revised)
        self.assertIn("This sickness will take me soon", revised)
        self.assertIn("I can't just let you die", revised)
        self.assertIn("what you carry after I am gone", revised)
        self.assertIn("Mercy", revised)
        self.assertIn("I will. I promise", revised)
        for removed in (
            "Medicine takes time",
            "Pain can make the heart angry",
            "Just let people hurt us",
            "Stop the harm when you can",
        ):
            self.assertNotIn(removed, revised)

    def test_resident_archive_table_matches_new_disc_except_volatile_byte(self) -> None:
        start = ARCHIVE_TABLE_PAYLOAD_OFFSET
        end = start + ARCHIVE_TABLE_SIZE
        source = self.source_payload[start:end]
        target = self.result_payload[start:end]
        self.assertEqual(
            hashlib.sha256(source).hexdigest(),
            SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(target).hexdigest(),
            TARGET_RESIDENT_ARCHIVE_TABLE_SHA256,
        )
        self.assertEqual(target[:-1], self.target_archive_table[:-1])
        self.assertEqual(target[-1], source[-1])

    def test_state_prefix_and_payload_shape_are_preserved(self) -> None:
        self.assertEqual(_sha256(self.source_payload), SOURCE_PAYLOAD_SHA256)
        source_prefix = bytearray(self.source_state[:SOURCE_FRAME_OFFSET])
        result_prefix = bytearray(self.result[:SOURCE_FRAME_OFFSET])
        result_prefix[
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET
            + 4 : DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET
            + 8
        ] = source_prefix[
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET
            + 4 : DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET
            + 8
        ]
        self.assertEqual(result_prefix, source_prefix)
        self.assertEqual(len(self.result_payload), len(self.source_payload))

    def test_mutated_source_and_wrong_disc_are_rejected(self) -> None:
        changed = bytearray(self.source_state)
        changed[-1] ^= 1
        with self.assertRaisesRegex(
            RicoChapterOneDialogueMigrationError,
            "Source Slot 1 identity changed",
        ):
            migrate_state(
                bytes(changed),
                zstd=self.zstd,
                new_disc=DEFAULT_NEW_DISC,
            )

        with self.assertRaisesRegex(
            RicoChapterOneDialogueMigrationError,
            "Disc 1 identity changed",
        ):
            migrate_state(
                self.source_state,
                zstd=self.zstd,
                new_disc=LIVE_SLOT_ONE,
            )

    def test_cli_refuses_the_live_slot_as_output(self) -> None:
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
