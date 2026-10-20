from __future__ import annotations

import struct
import unittest

from tools import build_rico_arc as rico
from tools.migrate_duckstation_disc_state import (
    DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    _Zstd,
)
from tools.migrate_rico_arc_dialogue_slot1 import (
    ARCHIVE_TABLE_PAYLOAD_OFFSET,
    ARCHIVE_TABLE_SIZE,
    LIVE_SLOT_ONE,
    RESIDENT_DIALOGUE_PAYLOAD_OFFSET,
    RESIDENT_DIALOGUE_SIZE,
)
from tools.migrate_rico_arc_eulogy_slot1 import TARGET_ALLOCATED_DIALOGUE_SHA256
from tools.migrate_rico_arc_intro_slot1 import (
    ARCHIVE_TABLE_DIFFS,
    DEFAULT_NEW_DISC,
    DEFAULT_ZSTD,
    EXPECTED_REPAIRED_PAYLOAD_SHA256,
    EXPECTED_REPAIRED_STATE_SHA256,
    EXPECTED_REPAIRED_STATE_SIZE,
    HUB_DIALOGUE_SHA256,
    HUB_DIALOGUE_SIZE,
    HUB_FIELD_SECTOR,
    HUB_FIELD_SIZE,
    RicoChapterOneIntroMigrationError,
    SOURCE_FRAME_OFFSET,
    SOURCE_PAYLOAD_SHA256,
    SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256,
    TARGET_RESIDENT_ARCHIVE_TABLE_SHA256,
    _differences,
    _sha256,
    _validated_target_hub,
    main,
    migrate_state,
)
from tools.xgdialog import parse_dialogue
from work.read_duckstation_runtime import GAME_STATE


class RicoChapterOneIntroSlotOneMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (LIVE_SLOT_ONE, DEFAULT_NEW_DISC, DEFAULT_ZSTD)
        if any(not path.is_file() for path in required):
            raise unittest.SkipTest(
                "Audited Rico Slot 1, introduction stage, or zstd is unavailable"
            )
        cls.source_state = LIVE_SLOT_ONE.read_bytes()
        cls.zstd = _Zstd(DEFAULT_ZSTD)
        try:
            cls.result, cls.report = migrate_state(
                cls.source_state,
                zstd=cls.zstd,
                new_disc=DEFAULT_NEW_DISC,
            )
        except RicoChapterOneIntroMigrationError as exc:
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
        cls.hub_dialogue, cls.target_archive_table = _validated_target_hub(
            DEFAULT_NEW_DISC
        )

    def test_exact_candidate_identity_and_fat_only_report(self) -> None:
        self.assertEqual(len(self.result), EXPECTED_REPAIRED_STATE_SIZE)
        self.assertEqual(_sha256(self.result), EXPECTED_REPAIRED_STATE_SHA256)
        self.assertEqual(
            _sha256(self.result_payload),
            EXPECTED_REPAIRED_PAYLOAD_SHA256,
        )
        self.assertEqual(
            self.report["resident_archive_table_changed_byte_count"],
            2,
        )
        self.assertEqual(self.report["resident_dialogue_changed_byte_count"], 0)
        self.assertEqual(self.report["gamestate_changed_byte_count"], 0)
        self.assertEqual(self.report["allocator_changed_byte_count"], 0)
        self.assertTrue(self.report["resident_fat_migrated"])
        self.assertFalse(self.report["media_path_rewrite_required"])
        self.assertEqual(self.report["hub_field_sector"], HUB_FIELD_SECTOR)
        self.assertEqual(self.report["hub_field_size"], HUB_FIELD_SIZE)

    def test_exactly_two_decompressed_fat_bytes_change(self) -> None:
        expected = tuple(
            (
                ARCHIVE_TABLE_PAYLOAD_OFFSET + relative_offset,
                old,
                new,
            )
            for relative_offset, old, new in ARCHIVE_TABLE_DIFFS
        )
        self.assertEqual(
            _differences(self.source_payload, self.result_payload),
            expected,
        )
        self.assertEqual(
            tuple(offset for offset, _old, _new in expected),
            (0x1525B, 0x1525C),
        )

    def test_resident_house_dialogue_and_gamestate_are_unchanged(self) -> None:
        dialogue_start = RESIDENT_DIALOGUE_PAYLOAD_OFFSET
        dialogue_end = dialogue_start + RESIDENT_DIALOGUE_SIZE
        source_dialogue = self.source_payload[dialogue_start:dialogue_end]
        target_dialogue = self.result_payload[dialogue_start:dialogue_end]
        self.assertEqual(source_dialogue, target_dialogue)
        self.assertEqual(_sha256(target_dialogue), TARGET_ALLOCATED_DIALOGUE_SHA256)

        # GAME_STATE is a PSX-RAM offset; RAM begins at payload 0x1A62 here.
        game_state_start = 0x1A62 + GAME_STATE
        game_state_end = game_state_start + 0x2358
        self.assertEqual(
            self.result_payload[game_state_start:game_state_end],
            self.source_payload[game_state_start:game_state_end],
        )

    def test_hub_contains_the_final_sentence_safe_exposition(self) -> None:
        parsed = parse_dialogue(self.hub_dialogue)
        self.assertEqual(len(self.hub_dialogue), HUB_DIALOGUE_SIZE)
        self.assertEqual(_sha256(self.hub_dialogue), HUB_DIALOGUE_SHA256)
        chapter = rico.load_chapters()[0]
        expected = rico._reflow_dialogue_text(
            chapter.selection_exposition,
            sentence_safe_pages=True,
        )
        # Seven choice blocks precede Chapter 1's title card and exposition.
        self.assertEqual(parsed.blocks[8].text, expected)
        self.assertEqual((parsed.blocks[8].width, parsed.blocks[8].height), (58, 5))
        self.assertEqual(expected.count("<New>"), 2)
        self.assertFalse(rico._dialogue_layout_issues(expected))
        self.assertFalse(rico._dialogue_sentence_page_issues(expected))
        visible = " ".join(
            expected.replace("<New>", " ").replace("<Close>", "").split()
        )
        for phrase in (
            "Though Anne passes away",
            "Rico is only ten years old",
            "words she leaves behind remain with him",
            "shaping the man he will one day become...",
        ):
            self.assertIn(phrase, visible)
        for rejected_phrase in (
            "Fei and Elly",
            "save Kislev",
            "nation that rejected him",
            "ruler he becomes",
        ):
            self.assertNotIn(rejected_phrase, visible)

    def test_resident_archive_table_matches_stage_except_volatile_byte(self) -> None:
        start = ARCHIVE_TABLE_PAYLOAD_OFFSET
        end = start + ARCHIVE_TABLE_SIZE
        source = self.source_payload[start:end]
        target = self.result_payload[start:end]
        self.assertEqual(_sha256(source), SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256)
        self.assertEqual(_sha256(target), TARGET_RESIDENT_ARCHIVE_TABLE_SHA256)
        self.assertEqual(target[:-1], self.target_archive_table[:-1])
        self.assertEqual(target[-1], source[-1])

    def test_state_prefix_shape_and_all_other_payload_are_preserved(self) -> None:
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
            RicoChapterOneIntroMigrationError,
            "Source Slot 1 identity changed",
        ):
            migrate_state(
                bytes(changed),
                zstd=self.zstd,
                new_disc=DEFAULT_NEW_DISC,
            )
        with self.assertRaisesRegex(
            RicoChapterOneIntroMigrationError,
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
