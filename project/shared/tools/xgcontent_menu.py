#!/usr/bin/env python3
"""Build the tiny direct-colour atlas for the unified content selector.

The selector is rendered by field bytecode with the PlayStation ``MoveImage``
primitive.  Keeping the artwork as a deterministic 64x64 TIM means the menu
does not depend on an emulator overlay or on pre-rendered screenshots: it is
ordinary Xenogears field content and therefore also works on real hardware.

Four copies of the deliberately small glyph set are stored with backgrounds
that match the four UI surfaces.  ``MoveImage`` copies zero-valued pixels too,
so baking the matching background into every glyph avoids black boxes when a
label is drawn on a highlighted or disabled card.
"""

from __future__ import annotations

from collections.abc import Mapping
import struct
from types import MappingProxyType

from PIL import Image

import modules.mass_driver.tools.xgnuke as xgnuke
Rect = tuple[int, int, int, int]
Rgb = tuple[int, int, int]

MENU_ATLAS_VRAM_X = 640
MENU_ATLAS_VRAM_Y = 384
MENU_ATLAS_WIDTH = 64
MENU_ATLAS_HEIGHT = 64
MENU_ATLAS_PIXEL_BYTES = MENU_ATLAS_WIDTH * MENU_ATLAS_HEIGHT * 2
MENU_ATLAS_IMAGE_BLOCK_SIZE = 12 + MENU_ATLAS_PIXEL_BYTES
MENU_ATLAS_TOTAL_SIZE = 8 + MENU_ATLAS_IMAGE_BLOCK_SIZE
MENU_ATLAS_TIM_HEADER = struct.pack(
    "<IIIHHHH",
    0x10,
    0x02,
    MENU_ATLAS_IMAGE_BLOCK_SIZE,
    MENU_ATLAS_VRAM_X,
    MENU_ATLAS_VRAM_Y,
    MENU_ATLAS_WIDTH,
    MENU_ATLAS_HEIGHT,
)

MENU_FONT_GLYPH_WIDTH = 4
MENU_FONT_GLYPH_HEIGHT = 6
MENU_FONT_CELL_WIDTH = 5
MENU_FONT_CELL_HEIGHT = 7
MENU_FONT_COLUMNS = 12

# This is the complete character inventory used by the selector.  Twenty-four
# cells fit exactly in two 12-column rows, allowing four background-aware
# variants plus a final strip of solid fill pixels in one 64x64 texture.
MENU_GLYPH_ORDER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".replace("J", "").replace(
    "K", ""
).replace("Q", "").replace("W", "") + "'-"
if len(MENU_GLYPH_ORDER) != 24:  # pragma: no cover - import-time invariant
    raise RuntimeError("Unified-menu glyph inventory no longer has 24 cells")

MENU_STYLE_BASE = "base"
MENU_STYLE_ACTIVE = "active"
MENU_STYLE_INACTIVE = "inactive"
MENU_STYLE_DISABLED = "disabled"
MENU_STYLES = (
    MENU_STYLE_BASE,
    MENU_STYLE_ACTIVE,
    MENU_STYLE_INACTIVE,
    MENU_STYLE_DISABLED,
)
MENU_STYLE_ORIGINS = MappingProxyType(
    {
        MENU_STYLE_BASE: (1, 0),
        MENU_STYLE_ACTIVE: (1, 14),
        MENU_STYLE_INACTIVE: (1, 28),
        MENU_STYLE_DISABLED: (1, 42),
    }
)

MENU_BACKGROUND: Rgb = (8, 16, 32)
MENU_PANEL: Rgb = (24, 36, 56)
MENU_HIGHLIGHT: Rgb = (24, 80, 112)
MENU_DISABLED: Rgb = (14, 20, 31)
MENU_ACCENT: Rgb = (80, 208, 240)
MENU_WHITE: Rgb = (248, 248, 248)
MENU_GRAY: Rgb = (136, 152, 168)
MENU_DIM: Rgb = (64, 76, 88)

MENU_STYLE_COLORS: Mapping[str, tuple[Rgb, Rgb]] = MappingProxyType(
    {
        MENU_STYLE_BASE: (MENU_ACCENT, MENU_BACKGROUND),
        MENU_STYLE_ACTIVE: (MENU_WHITE, MENU_HIGHLIGHT),
        MENU_STYLE_INACTIVE: (MENU_GRAY, MENU_PANEL),
        MENU_STYLE_DISABLED: (MENU_DIM, MENU_DISABLED),
    }
)

MENU_TILE_Y = 58
MENU_TILE_RECTS: Mapping[str, Rect] = MappingProxyType(
    {
        "background": (1, MENU_TILE_Y, 1, 1),
        "panel": (2, MENU_TILE_Y, 1, 1),
        "highlight": (3, MENU_TILE_Y, 1, 1),
        "disabled": (4, MENU_TILE_Y, 1, 1),
        "accent": (5, MENU_TILE_Y, 1, 1),
    }
)
MENU_TILE_COLORS: Mapping[str, Rgb] = MappingProxyType(
    {
        "background": MENU_BACKGROUND,
        "panel": MENU_PANEL,
        "highlight": MENU_HIGHLIGHT,
        "disabled": MENU_DISABLED,
        "accent": MENU_ACCENT,
    }
)


def _glyph_rectangles() -> dict[tuple[str, str], Rect]:
    rectangles: dict[tuple[str, str], Rect] = {}
    for style in MENU_STYLES:
        origin_x, origin_y = MENU_STYLE_ORIGINS[style]
        for index, glyph in enumerate(MENU_GLYPH_ORDER):
            rectangles[(style, glyph)] = (
                origin_x + (index % MENU_FONT_COLUMNS) * MENU_FONT_CELL_WIDTH,
                origin_y + (index // MENU_FONT_COLUMNS) * MENU_FONT_CELL_HEIGHT,
                MENU_FONT_GLYPH_WIDTH,
                MENU_FONT_GLYPH_HEIGHT,
            )
    return rectangles


MENU_GLYPH_RECTS: Mapping[tuple[str, str], Rect] = MappingProxyType(
    _glyph_rectangles()
)


def _glyph_bitmap(glyph: str) -> tuple[str, ...]:
    if glyph in xgnuke._FONT_BITMAPS:
        return xgnuke._FONT_BITMAPS[glyph]
    if glyph == "'":
        return (".##.", ".##.", ".#..", "....", "....", "....")
    raise ValueError(f"No content-menu bitmap for {glyph!r}")


def _render_menu_atlas_image() -> Image.Image:
    image = Image.new("RGB", (MENU_ATLAS_WIDTH, MENU_ATLAS_HEIGHT), (0, 0, 0))
    pixels = image.load()
    for style in MENU_STYLES:
        foreground, background = MENU_STYLE_COLORS[style]
        for glyph in MENU_GLYPH_ORDER:
            x, y, width, height = MENU_GLYPH_RECTS[(style, glyph)]
            bitmap = _glyph_bitmap(glyph)
            if len(bitmap) != height or any(len(row) != width for row in bitmap):
                raise ValueError(f"Content-menu glyph {glyph!r} has bad dimensions")
            for row_index, row in enumerate(bitmap):
                for column_index, marker in enumerate(row):
                    pixels[x + column_index, y + row_index] = (
                        foreground if marker == "#" else background
                    )
    for name, (x, y, width, height) in MENU_TILE_RECTS.items():
        color = MENU_TILE_COLORS[name]
        for row in range(y, y + height):
            for column in range(x, x + width):
                pixels[column, row] = color
    return image


def _rgb555(color: Rgb) -> int:
    red, green, blue = color
    if any(not 0 <= channel <= 255 for channel in color):
        raise ValueError(f"RGB channel is outside 0..255: {color}")
    # Every authored color is non-black and is moved directly into a live
    # framebuffer page.  The high bit is therefore unnecessary.
    return (red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10)


def _encode_rgb555(image: Image.Image) -> bytes:
    if image.size != (MENU_ATLAS_WIDTH, MENU_ATLAS_HEIGHT):
        raise ValueError(f"Content-menu atlas has unexpected size {image.size}")
    encoded = bytearray(MENU_ATLAS_PIXEL_BYTES)
    for index, color in enumerate(image.getdata()):
        struct.pack_into("<H", encoded, index * 2, _rgb555(color))
    return bytes(encoded)


def build_content_menu_atlas_image() -> Image.Image:
    """Return the deterministic RGB preview used to construct the TIM."""

    return _render_menu_atlas_image()


def build_content_menu_atlas_tim() -> bytes:
    """Return the complete 16-bpp TIM installed as field-local file 12."""

    result = MENU_ATLAS_TIM_HEADER + _encode_rgb555(_render_menu_atlas_image())
    if len(result) != MENU_ATLAS_TOTAL_SIZE:
        raise ValueError(
            f"Content-menu TIM is {len(result)} bytes, expected {MENU_ATLAS_TOTAL_SIZE}"
        )
    return result


__all__ = [
    "MENU_ATLAS_HEIGHT",
    "MENU_ATLAS_TOTAL_SIZE",
    "MENU_ATLAS_VRAM_X",
    "MENU_ATLAS_VRAM_Y",
    "MENU_ATLAS_WIDTH",
    "MENU_BACKGROUND",
    "MENU_DISABLED",
    "MENU_FONT_CELL_HEIGHT",
    "MENU_FONT_CELL_WIDTH",
    "MENU_GLYPH_ORDER",
    "MENU_GLYPH_RECTS",
    "MENU_HIGHLIGHT",
    "MENU_PANEL",
    "MENU_STYLE_ACTIVE",
    "MENU_STYLE_BASE",
    "MENU_STYLE_DISABLED",
    "MENU_STYLE_INACTIVE",
    "MENU_TILE_RECTS",
    "build_content_menu_atlas_image",
    "build_content_menu_atlas_tim",
]
