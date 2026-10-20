from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

import hashlib
from pathlib import Path
import struct
import unittest

from tools import xgrico_balance as balance
from tools import xgrico_native_title as title


PROJECT_ROOT = REPOSITORY_ROOT
RETAIL_ROOT = PROJECT_ROOT / "work" / "title_menu_audit_20260813" / "retail"
YOUNG_RICO_TIM = (
    PROJECT_ROOT / "modules" / "rico" / "content" / "assets" /
    "young_rico_menu_portrait.tim"
)


def _sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


def _entries(data: bytes) -> tuple[tuple[int, ...], tuple[bytes, ...]]:
    count = struct.unpack_from("<I", data, 0)[0]
    offsets = struct.unpack_from(f"<{count}I", data, 4)
    entries = tuple(
        data[start : offsets[index + 1] if index + 1 < count else len(data)]
        for index, start in enumerate(offsets)
    )
    return offsets, entries


def _decode(entry: bytes) -> bytes:
    decoded, consumed = title._decode_complete_groups(entry)
    if consumed > len(entry):
        raise AssertionError("retail-complete decoder consumed beyond the entry")
    return decoded


def _records(font: bytes) -> tuple[bytes, ...]:
    count = struct.unpack_from("<I", font, 0)[0]
    offsets = struct.unpack_from(f"<{count}H", font, 4)
    return tuple(
        font[start : offsets[index + 1] if index + 1 < count else len(font)]
        for index, start in enumerate(offsets)
    )


def _disc2_gate(retail: bytes) -> bytes:
    result = bytearray(retail)
    offset = title.TITLE_EXPECTED_DISC_OFFSET
    if result[offset : offset + 4] != title.TITLE_EXPECT_DISC_INSTRUCTIONS[1]:
        raise AssertionError("retail expected-disc instruction changed")
    result[offset : offset + 4] = title.TITLE_EXPECT_DISC_INSTRUCTIONS[2]
    return bytes(result)


class RicoNativeTitleVisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        paths = {
            canonical_id: RETAIL_ROOT / f"{canonical_id}.bin"
            for canonical_id in (
                title.TITLE_GRAPHICS_CANONICAL_ID,
                title.TITLE_MENU_CANONICAL_ID,
                title.TITLE_OVERLAY_CANONICAL_ID,
            )
        }
        missing = [path for path in paths.values() if not path.is_file()]
        if missing:
            raise AssertionError(
                "Checked retail title extraction is incomplete: "
                + ", ".join(str(path) for path in missing)
            )
        cls.sources = {
            canonical_id: path.read_bytes()
            for canonical_id, path in paths.items()
        }
        if not YOUNG_RICO_TIM.is_file():
            raise AssertionError(f"Missing young-Rico portrait: {YOUNG_RICO_TIM}")
        cls.young_rico_tim = YOUNG_RICO_TIM.read_bytes()
        cls.atlas, cls.menu = title.build_rico_native_title_menu(
            cls.sources[title.TITLE_MENU_CANONICAL_ID],
            cls.young_rico_tim,
        )
        cls.graphics = title.patch_rico_native_title_graphics(
            cls.sources[title.TITLE_GRAPHICS_CANONICAL_ID], cls.atlas
        )

        cls.source_offsets, cls.source_entries = _entries(
            cls.sources[title.TITLE_MENU_CANONICAL_ID]
        )
        cls.result_offsets, cls.result_entries = _entries(cls.menu)
        cls.source_font = title._decode_entry(
            cls.source_entries[title.TITLE_FONT_ENTRY],
            expected_size=title.TITLE_FONT_SIZE,
            expected_sha256=title.TITLE_FONT_SHA256,
            label="test source title font",
        )
        cls.result_font = _decode(cls.result_entries[title.TITLE_FONT_ENTRY])
        cls.source_records = _records(cls.source_font)
        cls.result_records = _records(cls.result_font)

    def test_outputs_are_source_locked_frozen_and_deterministic(self) -> None:
        self.assertEqual(
            (
                len(self.sources[title.TITLE_MENU_CANONICAL_ID]),
                _sha256(self.sources[title.TITLE_MENU_CANONICAL_ID]),
            ),
            (title.TITLE_MENU_SOURCE_SIZE, title.TITLE_MENU_SOURCE_SHA256),
        )
        self.assertEqual(
            (len(self.menu), _sha256(self.menu)),
            (title.TITLE_MENU_RESULT_SIZE, title.TITLE_MENU_RESULT_SHA256),
        )
        self.assertEqual(
            _sha256(self.atlas), title.TITLE_LABEL_ATLAS_SHA256
        )
        self.assertEqual(
            _sha256(self.graphics), title.TITLE_GRAPHICS_RESULT_SHA256
        )
        self.assertEqual(
            title.build_rico_native_title_menu(
                self.sources[title.TITLE_MENU_CANONICAL_ID],
                self.young_rico_tim,
            ),
            (self.atlas, self.menu),
        )
        self.assertEqual(
            title.patch_rico_native_title_graphics(
                self.sources[title.TITLE_GRAPHICS_CANONICAL_ID], self.atlas
            ),
            self.graphics,
        )

        tampered = bytearray(self.sources[title.TITLE_MENU_CANONICAL_ID])
        tampered[-1] ^= 1
        with self.assertRaisesRegex(
            title.RicoNativeTitleError, "clean USA canonical resource 2593"
        ):
            title.build_rico_native_title_menu(bytes(tampered), self.young_rico_tim)
        tampered_tim = bytearray(self.young_rico_tim)
        tampered_tim[-1] ^= 1
        with self.assertRaisesRegex(
            title.RicoNativeTitleError, "young-Rico menu portrait asset changed"
        ):
            title.build_rico_native_title_menu(
                self.sources[title.TITLE_MENU_CANONICAL_ID], bytes(tampered_tim)
            )
        tampered = bytearray(self.sources[title.TITLE_GRAPHICS_CANONICAL_ID])
        tampered[-1] ^= 1
        with self.assertRaisesRegex(
            title.RicoNativeTitleError, "clean USA canonical resource 1587"
        ):
            title.patch_rico_native_title_graphics(bytes(tampered), self.atlas)

    def test_single_native_title_is_centered_and_other_rows_are_absent(self) -> None:
        images = title._decode_entry(
            self.source_entries[title.TITLE_IMAGE_ENTRY],
            expected_size=title.TITLE_IMAGES_SIZE,
            expected_sha256=title.TITLE_IMAGES_SHA256,
            label="test title images",
        )
        _count, source_records = title._font_records(self.source_font)
        native_label = title._render_native_label(images, source_records)
        self.assertEqual(title.RICO_TITLE_TEXT, "Rico's Arc")
        self.assertEqual(title.RICO_TITLE_WIDTH, 57)
        self.assertEqual(len(native_label), title.TITLE_LABEL_HEIGHT)
        self.assertEqual({len(row) for row in native_label}, {57})
        self.assertTrue(any(value for row in native_label for value in row))

        pixels: list[int] = []
        for packed in self.atlas:
            pixels.extend((packed & 0x0F, packed >> 4))
        self.assertEqual(title.TITLE_LABEL_TEXTURE_U, (0, 64, 112))
        self.assertEqual(title.TITLE_LABEL_WIDTHS, (57, 41, 27))
        self.assertEqual(title.TITLE_LABEL_SCREEN_Y, (10, 29, 49))
        self.assertEqual(title.TITLE_LABEL_SCREEN_X, -69)
        self.assertEqual(title.TITLE_LABEL_TEXTURE_VRAM, (960, 180))

        for glyph, u, width, y in zip(
            title.TITLE_LABEL_GLYPHS,
            title.TITLE_LABEL_TEXTURE_U,
            title.TITLE_LABEL_WIDTHS,
            title.TITLE_LABEL_SCREEN_Y,
            strict=True,
        ):
            with self.subTest(glyph=hex(glyph)):
                record = self.result_records[glyph]
                self.assertEqual(struct.unpack_from("<HH", record, 0), (1, 0))
                values = struct.unpack_from("<14h", record, 4)
                self.assertEqual(
                    values[:6],
                    (
                        u,
                        title.TITLE_LABEL_TEXTURE_VRAM[1],
                        width,
                        title.TITLE_LABEL_HEIGHT,
                        title.TITLE_LABEL_SCREEN_X,
                        y,
                    ),
                )
                self.assertEqual(
                    values[9:13],
                    (*title.STANDARD_FONT_CLUT, *title.TITLE_LABEL_TEXTURE_VRAM),
                )
                sampled = [
                    pixels[row * title.TITLE_LABEL_TEXTURE_WIDTH + column]
                    for row in range(title.TITLE_LABEL_HEIGHT)
                    for column in range(u, u + width)
                ]
                if glyph == title.TITLE_LABEL_GLYPHS[0]:
                    self.assertTrue(any(sampled))
                else:
                    self.assertEqual(set(sampled), {0})

        for row_index, row in enumerate(native_label):
            self.assertEqual(
                pixels[
                    row_index * title.TITLE_LABEL_TEXTURE_WIDTH :
                    row_index * title.TITLE_LABEL_TEXTURE_WIDTH
                    + title.RICO_TITLE_WIDTH
                ],
                row,
            )
        self.assertEqual(
            {
                pixels[row * title.TITLE_LABEL_TEXTURE_WIDTH + column]
                for row in range(title.TITLE_LABEL_HEIGHT)
                for column in range(
                    title.RICO_TITLE_WIDTH,
                    title.TITLE_LABEL_TEXTURE_WIDTH,
                )
            },
            {0},
        )

    def test_only_title_font_and_child_portrait_entries_change(self) -> None:
        self.assertEqual(self.source_offsets, title.ARCHIVE_SOURCE_OFFSETS)
        for index, (before, after) in enumerate(
            zip(self.source_entries, self.result_entries, strict=True)
        ):
            with self.subTest(archive_entry=index):
                if index in (title.TITLE_FONT_ENTRY, title.MENU_PORTRAIT_ENTRY):
                    self.assertNotEqual(after, before)
                else:
                    self.assertEqual(after, before)
        self.assertEqual(len(self.result_font), title.TITLE_FONT_SIZE)
        self.assertEqual(_sha256(self.result_font), title.TITLE_FONT_RESULT_SHA256)
        self.assertEqual(
            (len(self.result_entries[title.TITLE_FONT_ENTRY]),
             _sha256(self.result_entries[title.TITLE_FONT_ENTRY])),
            (title.TITLE_FONT_PACKED_RESULT_SIZE,
             title.TITLE_FONT_PACKED_RESULT_SHA256),
        )
        changed = {
            index
            for index, (before, after) in enumerate(
                zip(self.source_records, self.result_records, strict=True)
            )
            if before != after
        }
        self.assertEqual(changed, set(title.TITLE_LABEL_GLYPHS))
        self.assertLessEqual(len(self.menu), title.TITLE_MENU_SECTOR_BUDGET)
        self.assertEqual(
            (len(self.menu) + 0x7FF) & ~0x7FF,
            (len(self.sources[title.TITLE_MENU_CANONICAL_ID]) + 0x7FF) & ~0x7FF,
        )

    def test_portrait_slot_ten_is_child_rico_and_every_other_slot_survives(self) -> None:
        source_sheet, source_consumed = title._decode_complete_groups(
            self.source_entries[title.MENU_PORTRAIT_ENTRY] + bytes(16)
        )
        result_sheet, result_consumed = title._decode_complete_groups(
            self.result_entries[title.MENU_PORTRAIT_ENTRY]
        )
        self.assertLessEqual(
            source_consumed,
            len(self.source_entries[title.MENU_PORTRAIT_ENTRY]) + 16,
        )
        self.assertLessEqual(
            result_consumed,
            len(self.result_entries[title.MENU_PORTRAIT_ENTRY]),
        )
        self.assertEqual(
            _sha256(result_sheet),
            title.MENU_PORTRAIT_PATCHED_DECODED_SHA256,
        )
        for slot in range(title.MENU_PORTRAIT_COUNT):
            start = slot * title.MENU_PORTRAIT_TIM_SIZE
            end = start + title.MENU_PORTRAIT_TIM_SIZE
            with self.subTest(slot=slot):
                if slot == title.YOUNG_RICO_PORTRAIT_SLOT:
                    self.assertEqual(result_sheet[start:end], self.young_rico_tim)
                else:
                    self.assertEqual(result_sheet[start:end], source_sheet[start:end])
        self.assertEqual(
            result_sheet[title.MENU_PORTRAIT_COUNT * title.MENU_PORTRAIT_TIM_SIZE :],
            source_sheet[title.MENU_PORTRAIT_COUNT * title.MENU_PORTRAIT_TIM_SIZE :],
        )
        title._validate_young_rico_portrait_tim(self.young_rico_tim)

    def test_graphics_extension_uses_only_the_checked_spare_rows(self) -> None:
        source = self.sources[title.TITLE_GRAPHICS_CANONICAL_ID]
        height_offset = title.TITLE_GRAPHICS_LAST_CHUNK_HEIGHT_OFFSET
        atlas_offset = title.TITLE_GRAPHICS_ATLAS_OFFSET
        atlas_end = atlas_offset + len(self.atlas)
        self.assertEqual(
            struct.unpack_from("<H", source, height_offset)[0],
            title.TITLE_GRAPHICS_LAST_CHUNK_SOURCE_HEIGHT,
        )
        self.assertEqual(
            struct.unpack_from("<H", self.graphics, height_offset)[0],
            title.TITLE_GRAPHICS_LAST_CHUNK_RESULT_HEIGHT,
        )
        self.assertEqual(self.graphics[atlas_offset:atlas_end], self.atlas)
        allowed = {height_offset, height_offset + 1} | set(
            range(atlas_offset, atlas_end)
        )
        changed = {
            index
            for index, (before, after) in enumerate(
                zip(source, self.graphics, strict=True)
            )
            if before != after
        }
        self.assertTrue(changed <= allowed)
        self.assertEqual(atlas_offset, 0x2C000 + 64 * 4 * 2)
        self.assertEqual(atlas_end, 0x2C000 + 64 * 13 * 2)
        self.assertEqual(
            (atlas_end + 0x7FF) & ~0x7FF,
            len(self.graphics),
        )


class RicoNativeTitleOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        path = RETAIL_ROOT / f"{title.TITLE_OVERLAY_CANONICAL_ID}.bin"
        if not path.is_file():
            raise AssertionError(f"Missing checked retail title overlay: {path}")
        cls.retail = path.read_bytes()
        cls.gated = _disc2_gate(cls.retail)
        cls.balanced = balance.patch_weight_mutation_overlay(cls.retail)
        cls.gated_balanced = balance.patch_weight_mutation_overlay(cls.gated)
        cls.variants = (
            (cls.retail, 1),
            (cls.gated, 2),
            (cls.balanced, 1),
            (cls.gated_balanced, 2),
        )

    def test_all_retail_and_balanced_disc_variants_are_frozen(self) -> None:
        for source, expected_disc in self.variants:
            source_hash = _sha256(source)
            source_disc, _balanced, result_hash = title.TITLE_OVERLAY_INPUTS[
                source_hash
            ]
            with self.subTest(source=source_hash, disc=expected_disc):
                self.assertEqual(source_disc, expected_disc)
                result = title.patch_rico_native_title_overlay(
                    source, expected_disc=expected_disc
                )
                self.assertEqual(len(result), title.TITLE_OVERLAY_SIZE)
                self.assertEqual(_sha256(result), result_hash)
                self.assertEqual(
                    title.patch_rico_native_title_overlay(
                        source, expected_disc=expected_disc
                    ),
                    result,
                )

    def test_only_rico_row_is_reachable_and_native_confirm_is_retained(self) -> None:
        for source, expected_disc in self.variants:
            result = title.patch_rico_native_title_overlay(
                source, expected_disc=expected_disc
            )
            with self.subTest(disc=expected_disc, source=_sha256(source)):
                # Internal row 2 is the visual top row and dispatches retail
                # New Game.  Both direction paths return without changing it.
                self.assertEqual(result[0x1AFC:0x1B00], bytes.fromhex("02 00 02 34"))
                self.assertEqual(result[0x0960:0x0964], bytes.fromhex("38 00 62 10"))
                self.assertEqual(result[0x0970:0x0974], bytes.fromhex("34 00 71 10"))
                self.assertEqual(result[0x09EC:0x0A1C], title._DIRECTION_GATE_RESULT)
                self.assertEqual(
                    result[
                        title.TITLE_DIRECTION_SOUND_DISPATCH_OFFSET :
                        title.TITLE_DIRECTION_SOUND_DISPATCH_OFFSET + 8
                    ],
                    bytes.fromhex("7B 16 07 0C 01 00 04 34"),
                )
                self.assertEqual(
                    result[
                        title.TITLE_CONFIRM_SOUND_DISPATCH_OFFSET :
                        title.TITLE_CONFIRM_SOUND_DISPATCH_OFFSET
                        + len(title.TITLE_CONFIRM_SOUND_DISPATCH)
                    ],
                    title.TITLE_CONFIRM_SOUND_DISPATCH,
                )
                self.assertEqual(
                    result[
                        title.TITLE_SELECTION_CONFIG_OFFSET :
                        title.TITLE_SELECTION_CONFIG_OFFSET
                        + len(title.TITLE_SELECTION_CONFIG)
                    ],
                    title.TITLE_SELECTION_CONFIG,
                )

    def test_disc_gate_and_weight_patch_are_preserved_byte_for_byte(self) -> None:
        for source, expected_disc in (
            (self.balanced, 1),
            (self.gated_balanced, 2),
        ):
            result = title.patch_rico_native_title_overlay(
                source, expected_disc=expected_disc
            )
            with self.subTest(disc=expected_disc):
                offset = title.TITLE_EXPECTED_DISC_OFFSET
                self.assertEqual(
                    result[offset : offset + 4],
                    title.TITLE_EXPECT_DISC_INSTRUCTIONS[expected_disc],
                )
                self.assertEqual(
                    result[
                        balance.WEIGHT_GAIN_HOOK_OFFSET :
                        balance.WEIGHT_GAIN_HOOK_END
                    ],
                    source[
                        balance.WEIGHT_GAIN_HOOK_OFFSET :
                        balance.WEIGHT_GAIN_HOOK_END
                    ],
                )
                self.assertEqual(
                    result[
                        balance.WEIGHT_GAIN_CAP_OFFSET :
                        balance.WEIGHT_GAIN_CAP_END
                    ],
                    source[
                        balance.WEIGHT_GAIN_CAP_OFFSET :
                        balance.WEIGHT_GAIN_CAP_END
                    ],
                )
                self.assertEqual(
                    result[
                        balance.GEAR_MENU_DRAW_HOOK_OFFSET :
                        balance.GEAR_MENU_DRAW_HOOK_END
                    ],
                    source[
                        balance.GEAR_MENU_DRAW_HOOK_OFFSET :
                        balance.GEAR_MENU_DRAW_HOOK_END
                    ],
                )
                self.assertEqual(
                    result[
                        balance.WEIGHT_CLAMP_CAVE_OFFSET :
                        balance.WEIGHT_CLAMP_CAVE_END
                    ],
                    source[
                        balance.WEIGHT_CLAMP_CAVE_OFFSET :
                        balance.WEIGHT_CLAMP_CAVE_END
                    ],
                )
                self.assertEqual(
                    result[
                        balance.GEAR_MENU_GRAY_HELPER_OFFSET :
                        balance.GEAR_MENU_GRAY_HELPER_END
                    ],
                    source[
                        balance.GEAR_MENU_GRAY_HELPER_OFFSET :
                        balance.GEAR_MENU_GRAY_HELPER_END
                    ],
                )

    def test_mismatched_disc_and_unknown_inputs_fail_closed(self) -> None:
        with self.assertRaisesRegex(title.RicoNativeTitleError, "expects Disc 1"):
            title.patch_rico_native_title_overlay(self.balanced, expected_disc=2)
        with self.assertRaisesRegex(title.RicoNativeTitleError, "expects Disc 2"):
            title.patch_rico_native_title_overlay(
                self.gated_balanced, expected_disc=1
            )
        tampered = bytearray(self.balanced)
        tampered[-1] ^= 1
        with self.assertRaisesRegex(
            title.RicoNativeTitleError, "not a checked retail/balanced input"
        ):
            title.patch_rico_native_title_overlay(bytes(tampered), expected_disc=1)


if __name__ == "__main__":
    unittest.main()
