from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

import hashlib
from pathlib import Path
import struct
import unittest

from tools.xgfield import decompress_lzss
from tools import xgrico_title as title


PROJECT_ROOT = REPOSITORY_ROOT
RETAIL_MENU = (
    PROJECT_ROOT
    / "work"
    / "title_menu_audit_20260813"
    / "retail"
    / "2593.bin"
)
RETAIL_OVERLAY = (
    PROJECT_ROOT
    / "work"
    / "title_menu_audit_20260813"
    / "retail"
    / "2599.bin"
)


def _sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


def _archive_entries(data: bytes) -> tuple[tuple[int, ...], tuple[bytes, ...]]:
    count = struct.unpack_from("<I", data, 0)[0]
    offsets = struct.unpack_from(f"<{count}I", data, 4)
    entries = tuple(
        data[start : offsets[index + 1] if index + 1 < count else len(data)]
        for index, start in enumerate(offsets)
    )
    return offsets, entries


def _decode(entry: bytes) -> bytes:
    size = struct.unpack_from("<I", entry, 0)[0]
    return decompress_lzss(entry + bytes(16), size).data


def _font_records(font: bytes) -> tuple[bytes, ...]:
    count = struct.unpack_from("<I", font, 0)[0]
    offsets = struct.unpack_from(f"<{count}H", font, 4)
    return tuple(
        font[start : offsets[index + 1] if index + 1 < count else len(font)]
        for index, start in enumerate(offsets)
    )


def _label_rectangle(images: bytes) -> bytes:
    row_size = title.NEW_GAME_WIDTH // 2
    return b"".join(
        images[
            title.TITLE_LABEL_PIXELS_OFFSET
            + (title.NEW_GAME_Y + y) * title.TITLE_LABEL_ROW_BYTES :
            title.TITLE_LABEL_PIXELS_OFFSET
            + (title.NEW_GAME_Y + y) * title.TITLE_LABEL_ROW_BYTES
            + row_size
        ]
        for y in range(title.NEW_GAME_HEIGHT)
    )


class RicoTitleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not RETAIL_MENU.is_file():
            raise AssertionError(f"Missing checked retail menu resource: {RETAIL_MENU}")
        cls.source = RETAIL_MENU.read_bytes()
        cls.result = title.patch_rico_title_menu(cls.source)
        cls.source_offsets, cls.source_entries = _archive_entries(cls.source)
        cls.result_offsets, cls.result_entries = _archive_entries(cls.result)
        cls.source_images = _decode(cls.source_entries[title.TITLE_IMAGE_ENTRY])
        cls.result_images = _decode(cls.result_entries[title.TITLE_IMAGE_ENTRY])

    def test_output_is_frozen_deterministic_and_source_locked(self) -> None:
        self.assertEqual(
            (len(self.source), _sha256(self.source)),
            (title.TITLE_MENU_SOURCE_SIZE, title.TITLE_MENU_SOURCE_SHA256),
        )
        self.assertEqual(
            (len(self.result), _sha256(self.result)),
            (title.TITLE_MENU_RESULT_SIZE, title.TITLE_MENU_RESULT_SHA256),
        )
        self.assertEqual(title.patch_rico_title_menu(self.source), self.result)

        tampered = bytearray(self.source)
        tampered[-1] ^= 1
        with self.assertRaisesRegex(
            title.RicoTitleError, "clean USA canonical menu resource 2593"
        ):
            title.patch_rico_title_menu(bytes(tampered))
        with self.assertRaises(title.RicoTitleError):
            title.patch_rico_title_menu(self.result)

    def test_only_image_entry_and_new_game_rectangle_change(self) -> None:
        self.assertEqual(self.source_offsets, title.ARCHIVE_SOURCE_OFFSETS)
        self.assertEqual(self.result_offsets, title.ARCHIVE_RESULT_OFFSETS)
        for index, (before, after) in enumerate(
            zip(self.source_entries, self.result_entries, strict=True)
        ):
            with self.subTest(archive_entry=index):
                if index == title.TITLE_IMAGE_ENTRY:
                    self.assertNotEqual(after, before)
                else:
                    self.assertEqual(after, before)

        allowed = {
            title.TITLE_LABEL_PIXELS_OFFSET
            + (title.NEW_GAME_Y + y) * title.TITLE_LABEL_ROW_BYTES
            + x
            for y in range(title.NEW_GAME_HEIGHT)
            for x in range(title.NEW_GAME_WIDTH // 2)
        }
        changed = {
            index
            for index, (before, after) in enumerate(
                zip(self.source_images, self.result_images, strict=True)
            )
            if before != after
        }
        self.assertEqual(len(changed), 173)
        self.assertTrue(changed <= allowed)
        self.assertEqual(
            _sha256(_label_rectangle(self.source_images)),
            title.NEW_GAME_SOURCE_PIXELS_SHA256,
        )
        self.assertEqual(
            _sha256(_label_rectangle(self.result_images)),
            title.RICO_TITLE_PIXELS_SHA256,
        )
        self.assertEqual(
            _sha256(self.result_images), title.RICO_TITLE_IMAGES_SHA256
        )

    def test_font_records_continue_sound_and_clut_are_unchanged(self) -> None:
        source_font = _decode(self.source_entries[title.TITLE_FONT_ENTRY])
        result_font = _decode(self.result_entries[title.TITLE_FONT_ENTRY])
        self.assertEqual(result_font, source_font)
        self.assertEqual(_sha256(result_font), title.TITLE_FONT_SHA256)
        records = _font_records(result_font)
        for glyph, expected in title.TITLE_LABEL_RECORDS.items():
            with self.subTest(glyph=hex(glyph)):
                self.assertEqual(records[glyph], expected)
        self.assertEqual(
            records[title.APOSTROPHE_GLYPH], title.APOSTROPHE_RECORD
        )
        self.assertEqual(
            self.result_images[
                title.TITLE_LABEL_CLUT_OFFSET :
                title.TITLE_LABEL_IMAGE_HEADER_OFFSET
            ],
            self.source_images[
                title.TITLE_LABEL_CLUT_OFFSET :
                title.TITLE_LABEL_IMAGE_HEADER_OFFSET
            ],
        )

    def test_repacked_image_uses_exact_complete_groups_and_same_sector_budget(
        self,
    ) -> None:
        packed = self.result_entries[title.TITLE_IMAGE_ENTRY]
        self.assertEqual(
            (len(packed), _sha256(packed)),
            (
                title.TITLE_IMAGES_PACKED_RESULT_SIZE,
                title.TITLE_IMAGES_PACKED_RESULT_SHA256,
            ),
        )
        decoded, consumed = title._decode_complete_groups(packed)
        self.assertEqual(decoded, self.result_images)
        self.assertLessEqual(consumed, len(packed))
        self.assertEqual(struct.unpack_from("<I", packed, 0)[0], len(decoded))
        self.assertLessEqual(len(self.result), title.TITLE_MENU_SECTOR_BUDGET)
        self.assertEqual(
            (len(self.source) + 0x7FF) & ~0x7FF,
            (len(self.result) + 0x7FF) & ~0x7FF,
        )

    def test_retail_selection_table_uses_one_label_in_both_cursor_states(self) -> None:
        if not RETAIL_OVERLAY.is_file():
            raise AssertionError(
                f"Missing checked retail title overlay: {RETAIL_OVERLAY}"
            )
        overlay = RETAIL_OVERLAY.read_bytes()
        self.assertEqual(
            (len(overlay), _sha256(overlay)),
            (
                153_864,
                "82f84a24ac1fd1979754e1cc9c861405fb59ce95dd78db00a76f00c8f1bd177d",
            ),
        )
        self.assertEqual(
            struct.unpack_from("<6I", overlay, 0x251D4),
            (
                0x109,
                title.SOUND_GLYPH,
                0x10A,
                title.CONTINUE_GLYPH,
                0x10B,
                title.NEW_GAME_GLYPH,
            ),
        )
        # Runtime selection changes only cursor 0x109..0x10B to cursor+0x0D;
        # all states continue to draw the same second-column label record.
        self.assertNotIn(title.NEW_GAME_GLYPH + 0x0D, (0x109, 0x10A, 0x10B))


if __name__ == "__main__":
    unittest.main()
