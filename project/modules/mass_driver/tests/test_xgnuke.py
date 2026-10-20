from __future__ import annotations

import hashlib
import struct
import unittest

from PIL import Image

from tools.xgnuke import (
    ALPHABET_COLUMNS,
    ALPHABET_ORIGIN,
    DIGIT_ORIGIN,
    FONT_CELL_HEIGHT,
    FONT_CELL_WIDTH,
    NUKE_ATLAS_HEIGHT,
    NUKE_ATLAS_IMAGE_BLOCK_SIZE,
    NUKE_ATLAS_TIM_HEADER,
    NUKE_ATLAS_TOTAL_SIZE,
    NUKE_ATLAS_VRAM_X,
    NUKE_ATLAS_VRAM_Y,
    NUKE_ATLAS_WIDTH,
    NUKE_AMBER,
    NUKE_BOARD_BACKGROUND_RECT,
    NUKE_BOARD_BACKGROUND_TILE_NAME,
    NUKE_BOARD_BACKGROUND_VRAM_RECT,
    NUKE_BLACK,
    NUKE_CRT_BASE,
    NUKE_CRT_DARK,
    NUKE_CRT_HIGHLIGHT,
    NUKE_CRT_NEUTRAL,
    NUKE_DIM_GREEN,
    NUKE_PANEL_BACKGROUND_RECT,
    NUKE_PANEL_BACKGROUND_TILE_NAME,
    NUKE_PANEL_BACKGROUND_VRAM_RECT,
    NUKE_PHOSPHOR_GREEN,
    NUKE_PUNCTUATION,
    NUKE_GLYPH_HEIGHT,
    NUKE_GLYPH_RECTS,
    NUKE_GLYPH_WIDTH,
    NUKE_TILE_ORDER,
    NUKE_TILE_RECTS,
    NUKE_TILE_SIZE,
    build_nuke_atlas_image,
    build_nuke_atlas_tim,
    validate_nuke_atlas_image,
    validate_nuke_atlas_tim,
)


def _overlap(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
) -> bool:
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


class NukeAtlasTests(unittest.TestCase):
    def test_tim_header_size_destination_and_hash_are_stable(self) -> None:
        payload = build_nuke_atlas_tim()
        self.assertEqual(NUKE_ATLAS_WIDTH, 64)
        self.assertEqual(NUKE_ATLAS_HEIGHT, 64)
        self.assertEqual(NUKE_ATLAS_VRAM_X + NUKE_ATLAS_WIDTH, 704)
        self.assertEqual(NUKE_ATLAS_VRAM_Y + NUKE_ATLAS_HEIGHT, 448)
        self.assertEqual(NUKE_ATLAS_IMAGE_BLOCK_SIZE, 8_204)
        self.assertEqual(NUKE_ATLAS_TOTAL_SIZE, 8_212)
        self.assertEqual(len(payload), NUKE_ATLAS_TOTAL_SIZE)
        self.assertEqual(payload[:20], NUKE_ATLAS_TIM_HEADER)
        self.assertEqual(
            struct.unpack_from("<IIIHHHH", payload),
            (
                0x10,
                0x02,
                NUKE_ATLAS_IMAGE_BLOCK_SIZE,
                640,
                384,
                64,
                64,
            ),
        )
        self.assertEqual(
            hashlib.sha256(payload).hexdigest(),
            "3ddd11f3639c01cff6fdf12c95bfaca86893bdc2652ac449791faf4ef529471d",
        )
        atlas_rect = (
            NUKE_ATLAS_VRAM_X,
            NUKE_ATLAS_VRAM_Y,
            NUKE_ATLAS_WIDTH,
            NUKE_ATLAS_HEIGHT,
        )
        for name, reserved_rect in (
            ("party_slot_0", (640, 256, 64, 64)),
            ("party_slot_1", (640, 320, 64, 64)),
            ("compass", (640, 448, 64, 64)),
        ):
            with self.subTest(runtime_vram_neighbor=name):
                self.assertFalse(_overlap(atlas_rect, reserved_rect))
        validate_nuke_atlas_tim(payload)

    def test_image_is_fresh_exact_rgb_pixel_art(self) -> None:
        first = build_nuke_atlas_image()
        second = build_nuke_atlas_image()
        self.assertIsNot(first, second)
        self.assertEqual(first.mode, "RGB")
        self.assertEqual(first.size, (64, 64))
        self.assertEqual(first.tobytes(), second.tobytes())
        validate_nuke_atlas_image(first)

    def test_all_required_glyphs_are_covered_nonblank_and_disjoint(self) -> None:
        image = build_nuke_atlas_image()
        required = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        self.assertTrue(required <= set(NUKE_GLYPH_RECTS))
        self.assertTrue(
            all(
                rect[2:] == (NUKE_GLYPH_WIDTH, NUKE_GLYPH_HEIGHT)
                for rect in NUKE_GLYPH_RECTS.values()
            )
        )

        for index, glyph in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            self.assertEqual(
                NUKE_GLYPH_RECTS[glyph][:2],
                (
                    ALPHABET_ORIGIN[0] + index % ALPHABET_COLUMNS * FONT_CELL_WIDTH,
                    ALPHABET_ORIGIN[1] + index // ALPHABET_COLUMNS * FONT_CELL_HEIGHT,
                ),
            )
        for index, glyph in enumerate("0123456789"):
            self.assertEqual(
                NUKE_GLYPH_RECTS[glyph][:2],
                (DIGIT_ORIGIN[0] + index * FONT_CELL_WIDTH, DIGIT_ORIGIN[1]),
            )
        self.assertEqual(ALPHABET_COLUMNS, 12)
        self.assertEqual(ALPHABET_ORIGIN, (1, 1))
        self.assertEqual(DIGIT_ORIGIN, (1, 22))
        self.assertEqual(NUKE_PUNCTUATION, ":-./!?+")
        for index, glyph in enumerate(NUKE_PUNCTUATION):
            self.assertEqual(
                NUKE_GLYPH_RECTS[glyph][:2],
                (1 + index * FONT_CELL_WIDTH, 29),
            )

        entries = list(NUKE_GLYPH_RECTS.items())
        for index, (glyph, rect) in enumerate(entries):
            self.assertIsNotNone(image.crop((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3])).getbbox(), glyph)
            for other_glyph, other_rect in entries[index + 1 :]:
                self.assertFalse(_overlap(rect, other_rect), f"{glyph!r}/{other_glyph!r}")

    def test_game_tiles_are_nonblank_disjoint_and_directional(self) -> None:
        image = build_nuke_atlas_image()
        self.assertEqual(len(NUKE_TILE_ORDER), 23)
        self.assertEqual(
            tuple(NUKE_TILE_RECTS[name] for name in NUKE_TILE_ORDER),
            tuple(
                (1 + index % 8 * 8, 37 + index // 8 * 8, 6, 6)
                for index in range(23)
            ),
        )
        self.assertEqual(
            {"head_right", "head_down", "head_left", "head_up"} <= set(NUKE_TILE_RECTS),
            True,
        )
        entries = list(NUKE_TILE_RECTS.items())
        tile_payloads: dict[str, bytes] = {}
        for index, (name, rect) in enumerate(entries):
            self.assertEqual(rect[2:], (NUKE_TILE_SIZE, NUKE_TILE_SIZE))
            tile = image.crop((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]))
            tile_payloads[name] = tile.tobytes()
            if name == NUKE_PANEL_BACKGROUND_TILE_NAME:
                self.assertFalse(any(tile_payloads[name]), name)
            else:
                self.assertTrue(any(tile_payloads[name]), name)
            for other_name, other_rect in entries[index + 1 :]:
                self.assertFalse(_overlap(rect, other_rect), f"{name}/{other_name}")
            for glyph, glyph_rect in NUKE_GLYPH_RECTS.items():
                self.assertFalse(_overlap(rect, glyph_rect), f"{name}/{glyph!r}")
        self.assertEqual(
            len({tile_payloads[f"head_{direction}"] for direction in ("right", "down", "left", "up")}),
            4,
        )

    def test_ui_values_cursor_and_frames_have_distinct_accent_colours(self) -> None:
        image = build_nuke_atlas_image()

        for glyph in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            x, y, width, height = NUKE_GLYPH_RECTS[glyph]
            pixels = set(
                image.crop((x, y, x + width, y + height)).get_flattened_data()
            )
            self.assertEqual(pixels - {NUKE_BLACK}, {NUKE_PHOSPHOR_GREEN})
        for glyph in "0123456789":
            x, y, width, height = NUKE_GLYPH_RECTS[glyph]
            pixels = set(
                image.crop((x, y, x + width, y + height)).get_flattened_data()
            )
            self.assertEqual(pixels - {NUKE_BLACK}, {NUKE_AMBER})

        cursor_x, cursor_y, width, height = NUKE_TILE_RECTS["cursor"]
        cursor_pixels = set(
            image.crop(
                (cursor_x, cursor_y, cursor_x + width, cursor_y + height)
            ).get_flattened_data()
        )
        self.assertIn(NUKE_AMBER, cursor_pixels)

        self.assertEqual(NUKE_TILE_RECTS["frame"], (1, 53, 6, 6))
        frame_x, frame_y, width, height = NUKE_TILE_RECTS["frame"]
        self.assertEqual(
            set(
                image.crop(
                    (frame_x, frame_y, frame_x + width, frame_y + height)
                ).get_flattened_data()
            ),
            {NUKE_DIM_GREEN},
        )

    def test_exhaust_trail_has_distinct_hot_bright_and_fading_stages(self) -> None:
        image = build_nuke_atlas_image()
        required = {
            "head_right",
            "head_down",
            "head_left",
            "head_up",
            "trail_hot",
            "trail_bright",
            "trail_dim",
            "target",
            "cursor",
            "explosion",
        }
        self.assertTrue(required <= set(NUKE_TILE_RECTS))

        energy: list[int] = []
        payloads: list[bytes] = []
        for name in ("trail_hot", "trail_bright", "trail_dim"):
            x, y, width, height = NUKE_TILE_RECTS[name]
            tile = image.crop((x, y, x + width, y + height))
            pixels = tuple(tile.get_flattened_data())
            energy.append(sum(sum(pixel) for pixel in pixels))
            payloads.append(tile.tobytes())
        self.assertEqual(len(set(payloads)), 3)
        self.assertGreater(energy[0], energy[1])
        self.assertGreater(energy[1], energy[2])

    def test_board_background_tile_matches_converted_crt_and_is_erase_ready(self) -> None:
        self.assertEqual(NUKE_BOARD_BACKGROUND_TILE_NAME, "board_background")
        self.assertEqual(NUKE_BOARD_BACKGROUND_RECT, (49, 45, 6, 6))
        self.assertEqual(NUKE_BOARD_BACKGROUND_VRAM_RECT, (689, 429, 6, 6))
        image = build_nuke_atlas_image()
        x, y, width, height = NUKE_BOARD_BACKGROUND_RECT
        pixels = list(
            image.crop((x, y, x + width, y + height)).get_flattened_data()
        )
        self.assertEqual(
            set(pixels),
            {NUKE_CRT_BASE, NUKE_CRT_NEUTRAL, NUKE_CRT_DARK, NUKE_CRT_HIGHLIGHT},
        )
        self.assertEqual(
            tuple(sum(pixel[channel] for pixel in pixels) // len(pixels) for channel in range(3)),
            (44, 48, 44),
        )

        # Opaque sprite copies use the identical cell-relative stipple for
        # unused pixels, avoiding black boxes around moving game objects.
        background_bytes = image.crop((x, y, x + width, y + height)).tobytes()
        head_x, head_y, _, _ = NUKE_TILE_RECTS["head_right"]
        head = image.crop(
            (head_x, head_y, head_x + NUKE_TILE_SIZE, head_y + NUKE_TILE_SIZE)
        )
        self.assertNotIn(NUKE_BLACK, set(head.get_flattened_data()))
        head_bytes = head.tobytes()
        for pixel_index in (0, 1, 5, 30, 35):
            offset = pixel_index * 3
            self.assertEqual(
                head_bytes[offset : offset + 3],
                background_bytes[offset : offset + 3],
            )

    def test_panel_background_is_solid_black_and_precedes_frame_slot(self) -> None:
        self.assertEqual(NUKE_PANEL_BACKGROUND_TILE_NAME, "panel_background")
        self.assertEqual(NUKE_PANEL_BACKGROUND_RECT, (57, 45, 6, 6))
        self.assertEqual(NUKE_PANEL_BACKGROUND_VRAM_RECT, (697, 429, 6, 6))
        self.assertEqual(
            NUKE_PANEL_BACKGROUND_RECT[0] + NUKE_PANEL_BACKGROUND_RECT[2],
            63,
        )
        self.assertEqual(
            NUKE_TILE_ORDER[15:17],
            (NUKE_PANEL_BACKGROUND_TILE_NAME, "frame"),
        )
        image = build_nuke_atlas_image()
        x, y, width, height = NUKE_PANEL_BACKGROUND_RECT
        panel = image.crop((x, y, x + width, y + height))
        self.assertEqual(set(panel.get_flattened_data()), {NUKE_BLACK})

    def test_strict_image_validation_rejects_shape_mode_and_pixel_changes(self) -> None:
        with self.assertRaisesRegex(ValueError, "64x64"):
            validate_nuke_atlas_image(Image.new("RGB", (63, 64)))
        with self.assertRaisesRegex(ValueError, "RGB mode"):
            validate_nuke_atlas_image(Image.new("RGBA", (64, 64)))
        changed = build_nuke_atlas_image()
        changed.putpixel((0, 0), (8, 0, 0))
        with self.assertRaisesRegex(ValueError, "canonical atlas"):
            validate_nuke_atlas_image(changed)

    def test_strict_tim_validation_rejects_structure_stp_and_pixel_changes(self) -> None:
        payload = bytearray(build_nuke_atlas_tim())
        with self.assertRaisesRegex(ValueError, "8212 bytes"):
            validate_nuke_atlas_tim(payload[:-1])

        wrong_destination = payload.copy()
        struct.pack_into("<H", wrong_destination, 12, 639)
        with self.assertRaisesRegex(ValueError, "target VRAM"):
            validate_nuke_atlas_tim(wrong_destination)

        stp_set = payload.copy()
        word = struct.unpack_from("<H", stp_set, 20)[0]
        struct.pack_into("<H", stp_set, 20, word | 0x8000)
        with self.assertRaisesRegex(ValueError, "STP bit clear"):
            validate_nuke_atlas_tim(stp_set)

        changed_pixel = payload.copy()
        changed_pixel[20] ^= 1
        with self.assertRaisesRegex(ValueError, "canonical atlas"):
            validate_nuke_atlas_tim(changed_pixel)


if __name__ == "__main__":
    unittest.main()
