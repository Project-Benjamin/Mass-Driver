from __future__ import annotations

from pathlib import Path
import struct
import unittest

from tools import build_rico_arc as rico
from tools.migrate_duckstation_disc_state import (
    DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    _Zstd,
)
from tools.migrate_rico_arc_dialogue_slot1 import (
    LIVE_SLOT_ONE,
    NEXT_ALLOCATOR_HEADER,
    RESIDENT_DIALOGUE_PADDING,
    RESIDENT_DIALOGUE_PAYLOAD_OFFSET,
    RESIDENT_DIALOGUE_SIZE,
)
from tools.migrate_rico_arc_eulogy_slot1 import (
    ARCHIVE_TABLE_DIFFS,
    ARCHIVE_TABLE_PAYLOAD_OFFSET,
    ARCHIVE_TABLE_SIZE,
    DEFAULT_NEW_DISC,
    DEFAULT_ZSTD,
    EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT,
    EXPECTED_REPAIRED_PAYLOAD_SHA256,
    EXPECTED_REPAIRED_STATE_SHA256,
    EXPECTED_REPAIRED_STATE_SIZE,
    FUNERAL_DIALOGUE_SHA256,
    OBSOLETE_DIALOGUE_TAIL_SIZE,
    RicoChapterOneEulogyMigrationError,
    SOURCE_FRAME_OFFSET,
    SOURCE_PAYLOAD_SHA256,
    SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256,
    TARGET_ALLOCATED_DIALOGUE_SHA256,
    TARGET_DIALOGUE_SHA256,
    TARGET_DIALOGUE_SIZE,
    TARGET_RESIDENT_ARCHIVE_TABLE_SHA256,
    _differences,
    _sha256,
    _validated_target_resources,
    main,
    migrate_state,
)
from tools.xgdialog import decode_text, encode_text


class RicoChapterOneEulogySlotOneMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (LIVE_SLOT_ONE, DEFAULT_NEW_DISC, DEFAULT_ZSTD)
        if any(not path.is_file() for path in required):
            raise unittest.SkipTest(
                "Audited Rico Slot 1, no-name stage, or zstd is unavailable"
            )
        cls.source_state = LIVE_SLOT_ONE.read_bytes()
        cls.zstd = _Zstd(DEFAULT_ZSTD)
        try:
            cls.result, cls.report = migrate_state(
                cls.source_state,
                zstd=cls.zstd,
                new_disc=DEFAULT_NEW_DISC,
            )
        except RicoChapterOneEulogyMigrationError as exc:
            raise unittest.SkipTest(
                "Slot 1 or staged media is no longer the audited source: "
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
        cls.result_payload = cls.zstd.decompress(cls.result[result_frame_offset:])
        (
            cls.target_dialogue,
            cls.funeral_dialogue,
            cls.target_archive_table,
        ) = _validated_target_resources(DEFAULT_NEW_DISC)

    @staticmethod
    def _decoded_block(component: bytes, block_id: int) -> str:
        count = struct.unpack_from("<I", component, 0)[0] + 1
        if not 0 <= block_id < count:
            raise AssertionError(f"Dialogue block {block_id} outside {count}")
        offsets = tuple(
            struct.unpack_from("<H", component, 4 + index * 2)[0]
            for index in range(count)
        )
        start = offsets[block_id]
        end = offsets[block_id + 1] if block_id + 1 < count else len(component)
        return decode_text(component[start:end])

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
            self.report["obsolete_dialogue_tail_zeroed"],
            OBSOLETE_DIALOGUE_TAIL_SIZE,
        )
        self.assertEqual(
            self.report["resident_archive_table_changed_byte_count"],
            2,
        )
        self.assertTrue(self.report["allocator_header_preserved"])
        self.assertFalse(self.report["dialogue_allocation_relocated"])
        self.assertTrue(self.report["resident_fat_migrated"])

    def test_only_allocated_dialogue_and_two_fat_bytes_change(self) -> None:
        start = RESIDENT_DIALOGUE_PAYLOAD_OFFSET
        end = start + RESIDENT_DIALOGUE_SIZE
        target_allocation = self.target_dialogue + bytes(
            OBSOLETE_DIALOGUE_TAIL_SIZE
        )
        dialogue_changes = _differences(
            self.source_payload[start:end],
            target_allocation,
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
        self.assertEqual(len(dialogue_changes), 4_943)
        self.assertEqual(_sha256(target_allocation), TARGET_ALLOCATED_DIALOGUE_SHA256)

    def test_shorter_dialogue_clears_tail_and_preserves_allocator(self) -> None:
        start = RESIDENT_DIALOGUE_PAYLOAD_OFFSET
        target_end = start + TARGET_DIALOGUE_SIZE
        allocation_end = start + RESIDENT_DIALOGUE_SIZE
        padding_end = allocation_end + len(RESIDENT_DIALOGUE_PADDING)
        header_end = padding_end + len(NEXT_ALLOCATOR_HEADER)

        self.assertEqual(
            self.result_payload[start:target_end],
            self.target_dialogue,
        )
        self.assertEqual(
            self.result_payload[target_end:allocation_end],
            bytes(OBSOLETE_DIALOGUE_TAIL_SIZE),
        )
        self.assertEqual(
            self.result_payload[allocation_end:padding_end],
            RESIDENT_DIALOGUE_PADDING,
        )
        self.assertEqual(
            self.result_payload[padding_end:header_end],
            NEXT_ALLOCATOR_HEADER,
        )
        self.assertEqual(
            self.result_payload[allocation_end:header_end],
            self.source_payload[allocation_end:header_end],
        )

    def test_eulogy_omits_sigmund_in_house_and_funeral_copies(self) -> None:
        chapter = rico.load_chapters()[0]
        eulogy = rico._reflow_dialogue_text(
            chapter.blocks[42],
            sentence_safe_pages=True,
        )
        visible_eulogy = " ".join(
            eulogy.replace("<New>", " ").replace("<Close>", "").split()
        )
        self.assertIn("her husband, who is still fighting", visible_eulogy)
        self.assertNotIn("Sigmund", eulogy)

        # Donor field 229 contributes 27 IDs, so authored block 42 is ID 69.
        self.assertEqual(self._decoded_block(self.target_dialogue, 69), eulogy)
        encoded = encode_text(eulogy)
        self.assertEqual(self.target_dialogue.count(encoded), 1)
        self.assertEqual(self.funeral_dialogue.count(encoded), 1)
        self.assertEqual(_sha256(self.target_dialogue), TARGET_DIALOGUE_SHA256)
        self.assertEqual(_sha256(self.funeral_dialogue), FUNERAL_DIALOGUE_SHA256)

    def test_prior_bedside_dialogue_remains_exact(self) -> None:
        chapter = rico.load_chapters()[0]
        for authored_index in range(12, 19):
            expected = rico._reflow_dialogue_text(
                chapter.blocks[authored_index],
                sentence_safe_pages=True,
            )
            self.assertEqual(
                self._decoded_block(self.target_dialogue, 27 + authored_index),
                expected,
            )
        joined = "\n".join(chapter.blocks[12:19])
        self.assertIn("This sickness will take me soon", joined)
        self.assertIn("I can't just let you die", joined)
        self.assertIn("Do not make others suffer", joined)
        self.assertIn("I will. I promise", joined)

    def test_resident_fat_matches_new_disc_except_volatile_byte(self) -> None:
        start = ARCHIVE_TABLE_PAYLOAD_OFFSET
        end = start + ARCHIVE_TABLE_SIZE
        source = self.source_payload[start:end]
        target = self.result_payload[start:end]
        self.assertEqual(_sha256(source), SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256)
        self.assertEqual(_sha256(target), TARGET_RESIDENT_ARCHIVE_TABLE_SHA256)
        self.assertEqual(target[:-1], self.target_archive_table[:-1])
        self.assertEqual(target[-1], source[-1])

    def test_state_prefix_shape_and_all_unrelated_payload_are_preserved(self) -> None:
        self.assertEqual(_sha256(self.source_payload), SOURCE_PAYLOAD_SHA256)
        source_prefix = bytearray(self.source_state[:SOURCE_FRAME_OFFSET])
        result_prefix = bytearray(self.result[:SOURCE_FRAME_OFFSET])
        compressed_size = DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET + 4
        result_prefix[compressed_size : compressed_size + 4] = source_prefix[
            compressed_size : compressed_size + 4
        ]
        self.assertEqual(result_prefix, source_prefix)
        self.assertEqual(len(self.result_payload), len(self.source_payload))

    def test_mutated_source_and_wrong_disc_are_rejected(self) -> None:
        changed = bytearray(self.source_state)
        changed[-1] ^= 1
        with self.assertRaisesRegex(
            RicoChapterOneEulogyMigrationError,
            "Source Slot 1 identity changed",
        ):
            migrate_state(
                bytes(changed),
                zstd=self.zstd,
                new_disc=DEFAULT_NEW_DISC,
            )
        with self.assertRaisesRegex(
            RicoChapterOneEulogyMigrationError,
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
