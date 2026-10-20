#!/usr/bin/env python3
"""Build the code-native texture atlas used by the Nuke terminal game.

The atlas is deliberately small and self-contained.  It occupies the free
64x64 direct-colour rectangle at VRAM (640,384), using the deliberately empty
third party-sprite slot in this fixed Elly/Emeralda-only route and ending
immediately before the portrait column at x=704.  Glyph and tile rectangles
are public so field-model builders can use the same coordinates without
duplicating layout knowledge.
"""

from __future__ import annotations

from collections.abc import Mapping
import struct
from types import MappingProxyType

from PIL import Image


Rect = tuple[int, int, int, int]
Rgb = tuple[int, int, int]

NUKE_ATLAS_VRAM_X = 640
NUKE_ATLAS_VRAM_Y = 384
NUKE_ATLAS_WIDTH = 64
NUKE_ATLAS_HEIGHT = 64
NUKE_ATLAS_PIXEL_BYTES = NUKE_ATLAS_WIDTH * NUKE_ATLAS_HEIGHT * 2
NUKE_ATLAS_IMAGE_BLOCK_SIZE = 12 + NUKE_ATLAS_PIXEL_BYTES
NUKE_ATLAS_TOTAL_SIZE = 8 + NUKE_ATLAS_IMAGE_BLOCK_SIZE

# TIM magic, 16-bpp direct-colour flags, image-block byte length, and the
# destination rectangle in 16-bit VRAM pixels.
NUKE_ATLAS_TIM_HEADER = struct.pack(
    "<IIIHHHH",
    0x10,
    0x02,
    NUKE_ATLAS_IMAGE_BLOCK_SIZE,
    NUKE_ATLAS_VRAM_X,
    NUKE_ATLAS_VRAM_Y,
    NUKE_ATLAS_WIDTH,
    NUKE_ATLAS_HEIGHT,
)

NUKE_BLACK: Rgb = (0, 0, 0)
NUKE_PHOSPHOR_GREEN: Rgb = (24, 248, 112)
NUKE_DIM_GREEN: Rgb = (0, 96, 56)
NUKE_AMBER: Rgb = (248, 152, 0)
NUKE_YELLOW: Rgb = (248, 240, 48)
NUKE_WHITE: Rgb = (248, 248, 248)
NUKE_RED: Rgb = (248, 40, 24)
# These four RGB555-exact shades approximate the converted console CRT.  The
# 168x96 playfield in ``nuke_game.png`` averages RGB (44.79,47.29,45.04)
# after the retail 320x224 conversion; the board tile below averages
# (44,48,44).  Repeating that tile gives game code a deterministic erase
# source without preserving a second framebuffer page.
NUKE_CRT_BASE: Rgb = (40, 48, 40)
NUKE_CRT_NEUTRAL: Rgb = (48, 48, 48)
NUKE_CRT_DARK: Rgb = (32, 40, 32)
NUKE_CRT_HIGHLIGHT: Rgb = (56, 56, 56)

NUKE_PALETTE: Mapping[str, Rgb] = MappingProxyType(
    {
        "black": NUKE_BLACK,
        "phosphor_green": NUKE_PHOSPHOR_GREEN,
        "dim_green": NUKE_DIM_GREEN,
        "amber": NUKE_AMBER,
        "yellow": NUKE_YELLOW,
        "white": NUKE_WHITE,
        "red": NUKE_RED,
        "crt_base": NUKE_CRT_BASE,
        "crt_neutral": NUKE_CRT_NEUTRAL,
        "crt_dark": NUKE_CRT_DARK,
        "crt_highlight": NUKE_CRT_HIGHLIGHT,
    }
)

FONT_GLYPH_WIDTH = 4
FONT_GLYPH_HEIGHT = 6
FONT_CELL_WIDTH = 5
FONT_CELL_HEIGHT = 7
ALPHABET_COLUMNS = 12
ALPHABET_ORIGIN = (1, 1)
DIGIT_ORIGIN = (1, 22)

# Prefixed aliases keep the public naming consistent with the other atlas
# constants, while the shorter names above are convenient in field builders.
NUKE_GLYPH_WIDTH = FONT_GLYPH_WIDTH
NUKE_GLYPH_HEIGHT = FONT_GLYPH_HEIGHT
NUKE_FONT_CELL_WIDTH = FONT_CELL_WIDTH
NUKE_FONT_CELL_HEIGHT = FONT_CELL_HEIGHT
NUKE_ALPHABET_COLUMNS = ALPHABET_COLUMNS
NUKE_ALPHABET_ORIGIN = ALPHABET_ORIGIN
NUKE_DIGIT_ORIGIN = DIGIT_ORIGIN

NUKE_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
NUKE_DIGITS = "0123456789"
NUKE_PUNCTUATION = ":-./!?+"
NUKE_GLYPH_ORDER = NUKE_ALPHABET + NUKE_DIGITS + NUKE_PUNCTUATION
_PUNCTUATION_ORIGIN = (1, 29)


def _make_glyph_rects() -> dict[str, Rect]:
    rectangles = {
        glyph: (
            ALPHABET_ORIGIN[0] + (index % ALPHABET_COLUMNS) * FONT_CELL_WIDTH,
            ALPHABET_ORIGIN[1] + (index // ALPHABET_COLUMNS) * FONT_CELL_HEIGHT,
            FONT_GLYPH_WIDTH,
            FONT_GLYPH_HEIGHT,
        )
        for index, glyph in enumerate(NUKE_ALPHABET)
    }
    rectangles.update(
        {
            glyph: (
                DIGIT_ORIGIN[0] + index * FONT_CELL_WIDTH,
                DIGIT_ORIGIN[1],
                FONT_GLYPH_WIDTH,
                FONT_GLYPH_HEIGHT,
            )
            for index, glyph in enumerate(NUKE_DIGITS)
        }
    )
    rectangles.update(
        {
            glyph: (
                _PUNCTUATION_ORIGIN[0] + index * FONT_CELL_WIDTH,
                _PUNCTUATION_ORIGIN[1],
                FONT_GLYPH_WIDTH,
                FONT_GLYPH_HEIGHT,
            )
            for index, glyph in enumerate(NUKE_PUNCTUATION)
        }
    )
    return rectangles


NUKE_GLYPH_RECTS: Mapping[str, Rect] = MappingProxyType(_make_glyph_rects())

# Each row uses ``#`` for a phosphor-green pixel and ``.`` for black.  These
# hand-authored 4x6 forms stay readable at native PS1 resolution while leaving
# enough room in the atlas for all game sprites.
_FONT_BITMAPS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "A": (".##.", "#..#", "####", "#..#", "#..#", "#..#"),
        "B": ("###.", "#..#", "###.", "#..#", "#..#", "###."),
        "C": (".###", "#...", "#...", "#...", "#...", ".###"),
        "D": ("###.", "#..#", "#..#", "#..#", "#..#", "###."),
        "E": ("####", "#...", "###.", "#...", "#...", "####"),
        "F": ("####", "#...", "###.", "#...", "#...", "#..."),
        "G": (".###", "#...", "#...", "#.##", "#..#", ".###"),
        "H": ("#..#", "#..#", "####", "#..#", "#..#", "#..#"),
        "I": ("####", ".##.", ".##.", ".##.", ".##.", "####"),
        "J": ("..##", "...#", "...#", "...#", "#..#", ".##."),
        "K": ("#..#", "#.#.", "##..", "#.#.", "#..#", "#..#"),
        "L": ("#...", "#...", "#...", "#...", "#...", "####"),
        "M": ("#..#", "####", "####", "#..#", "#..#", "#..#"),
        "N": ("#..#", "##.#", "##.#", "#.##", "#.##", "#..#"),
        "O": (".##.", "#..#", "#..#", "#..#", "#..#", ".##."),
        "P": ("###.", "#..#", "#..#", "###.", "#...", "#..."),
        "Q": (".##.", "#..#", "#..#", "#..#", "#.##", ".###"),
        "R": ("###.", "#..#", "#..#", "###.", "#.#.", "#..#"),
        "S": (".###", "#...", ".##.", "...#", "...#", "###."),
        "T": ("####", ".##.", ".##.", ".##.", ".##.", ".##."),
        "U": ("#..#", "#..#", "#..#", "#..#", "#..#", ".##."),
        "V": ("#..#", "#..#", "#..#", "#..#", ".##.", ".##."),
        "W": ("#..#", "#..#", "#..#", "####", "####", ".##."),
        "X": ("#..#", "#..#", ".##.", ".##.", "#..#", "#..#"),
        "Y": ("#..#", "#..#", ".##.", ".##.", ".##.", ".##."),
        "Z": ("####", "...#", "..#.", ".#..", "#...", "####"),
        "0": (".##.", "#..#", "#.##", "##.#", "#..#", ".##."),
        "1": (".##.", "###.", ".##.", ".##.", ".##.", "####"),
        "2": (".##.", "#..#", "...#", ".##.", "#...", "####"),
        "3": ("###.", "...#", ".##.", "...#", "#..#", ".##."),
        "4": ("#..#", "#..#", "####", "...#", "...#", "...#"),
        "5": ("####", "#...", "###.", "...#", "#..#", ".##."),
        "6": (".##.", "#...", "###.", "#..#", "#..#", ".##."),
        "7": ("####", "...#", "..#.", ".#..", ".#..", ".#.."),
        "8": (".##.", "#..#", ".##.", "#..#", "#..#", ".##."),
        "9": (".##.", "#..#", "#..#", ".###", "...#", ".##."),
        ":": ("....", ".##.", ".##.", "....", ".##.", ".##."),
        "-": ("....", "....", "####", "....", "....", "...."),
        ".": ("....", "....", "....", "....", "....", ".##."),
        "/": ("...#", "..#.", "..#.", ".#..", ".#..", "#..."),
        "!": (".##.", ".##.", ".##.", ".##.", "....", ".##."),
        "?": (".##.", "#..#", "...#", "..#.", "....", "..#."),
        "+": ("....", ".#..", "###.", ".#..", "....", "...."),
    }
)

NUKE_TILE_SIZE = 6
NUKE_TILE_ORDER = (
    "head_right",
    "head_down",
    "head_left",
    "head_up",
    "trail_hot",
    "trail_bright",
    "trail_dim",
    "target",
    "warhead",
    "cursor",
    "pause",
    "explosion",
    "hazard",
    "level_up",
    "board_background",
    "panel_background",
    "frame",
    "enemy_trail",
    "interceptor",
    "city",
    "city_ruin",
    "battery",
    "battery_empty",
)
_TILE_ORIGIN_X = 1
_TILE_ORIGIN_Y = 37
_TILE_PITCH_X = 8
_TILE_PITCH_Y = 8
_TILE_COLUMNS = 8


def _make_tile_rects() -> dict[str, Rect]:
    return {
        name: (
            _TILE_ORIGIN_X + (index % _TILE_COLUMNS) * _TILE_PITCH_X,
            _TILE_ORIGIN_Y + (index // _TILE_COLUMNS) * _TILE_PITCH_Y,
            NUKE_TILE_SIZE,
            NUKE_TILE_SIZE,
        )
        for index, name in enumerate(NUKE_TILE_ORDER)
    }


NUKE_TILE_RECTS: Mapping[str, Rect] = MappingProxyType(_make_tile_rects())
NUKE_BOARD_BACKGROUND_TILE_NAME = "board_background"
NUKE_BOARD_BACKGROUND_RECT = NUKE_TILE_RECTS[NUKE_BOARD_BACKGROUND_TILE_NAME]
NUKE_BOARD_BACKGROUND_VRAM_RECT = (
    NUKE_ATLAS_VRAM_X + NUKE_BOARD_BACKGROUND_RECT[0],
    NUKE_ATLAS_VRAM_Y + NUKE_BOARD_BACKGROUND_RECT[1],
    NUKE_BOARD_BACKGROUND_RECT[2],
    NUKE_BOARD_BACKGROUND_RECT[3],
)
NUKE_PANEL_BACKGROUND_TILE_NAME = "panel_background"
NUKE_PANEL_BACKGROUND_RECT = NUKE_TILE_RECTS[NUKE_PANEL_BACKGROUND_TILE_NAME]
NUKE_PANEL_BACKGROUND_VRAM_RECT = (
    NUKE_ATLAS_VRAM_X + NUKE_PANEL_BACKGROUND_RECT[0],
    NUKE_ATLAS_VRAM_Y + NUKE_PANEL_BACKGROUND_RECT[1],
    NUKE_PANEL_BACKGROUND_RECT[2],
    NUKE_PANEL_BACKGROUND_RECT[3],
)


def _rotate_clockwise(bitmap: tuple[str, ...]) -> tuple[str, ...]:
    """Rotate one square symbol bitmap clockwise without interpolation."""

    return tuple(
        "".join(bitmap[NUKE_TILE_SIZE - 1 - x][y] for x in range(NUKE_TILE_SIZE))
        for y in range(NUKE_TILE_SIZE)
    )


_HEAD_RIGHT = (
    "..W...",
    "AWWW..",
    "RWWGWR",
    "AWWW..",
    "..W...",
    "......",
)
_HEAD_DOWN = _rotate_clockwise(_HEAD_RIGHT)
_HEAD_LEFT = _rotate_clockwise(_HEAD_DOWN)
_HEAD_UP = _rotate_clockwise(_HEAD_LEFT)

_BOARD_BACKGROUND_BITMAP = (
    "bnbbnd",
    "nblnbn",
    "bbnnlb",
    "ndbbnn",
    "blnndb",
    "nbbnld",
)

_TILE_BITMAPS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "head_right": _HEAD_RIGHT,
        "head_down": _HEAD_DOWN,
        "head_left": _HEAD_LEFT,
        "head_up": _HEAD_UP,
        "trail_hot": (
            "..W...",
            ".YYY..",
            "AYWYA.",
            ".YYY..",
            "..A...",
            "......",
        ),
        "trail_bright": (
            "......",
            "..Y...",
            ".AYYA.",
            "..YY..",
            "..A...",
            "......",
        ),
        "trail_dim": (
            "......",
            "..D...",
            ".DGD..",
            "..DD..",
            "..D...",
            "......",
        ),
        "target": (
            "..R...",
            "..R...",
            "RRWRRR",
            "..R...",
            "..R...",
            "......",
        ),
        "warhead": (
            "..R...",
            ".WWW..",
            "WWGWW.",
            ".WWW..",
            "..A...",
            "..A...",
        ),
        "cursor": (
            "AAAAA.",
            "A...A.",
            "A...A.",
            "A...A.",
            "AAAAA.",
            "......",
        ),
        "pause": (
            "......",
            ".WW.W.",
            ".WW.W.",
            ".WW.W.",
            ".WW.W.",
            "......",
        ),
        "explosion": (
            "R..R..",
            ".AYA..",
            "RYWYR.",
            ".AYA..",
            "R..R..",
            "......",
        ),
        "hazard": (
            ".RRR..",
            "R...R.",
            "R.W.R.",
            "R...R.",
            ".RRR..",
            "..R...",
        ),
        "level_up": (
            "..G...",
            ".GGG..",
            "G.G.G.",
            "..G...",
            "..G...",
            "..G...",
        ),
        # Subtle, aperiodic-looking RGB555 grain whose mean closely matches
        # the converted CRT playfield.  The game tiles the full board with
        # this cell once, then uses the same source rectangle for erasure.
        "board_background": _BOARD_BACKGROUND_BITMAP,
        # A separate zero-valued source for clearing HUD and message panels.
        # ``k`` is intentionally opaque black rather than an unused marker.
        "panel_background": (
            "kkkkkk",
            "kkkkkk",
            "kkkkkk",
            "kkkkkk",
            "kkkkkk",
            "kkkkkk",
        ),
        # Solid dim phosphor used for the board and modal-panel rules.  The
        # fill helper may seed only the first one or two rows/columns, so one
        # opaque tile supports crisp native-resolution frames of any size.
        "frame": (
            "DDDDDD",
            "DDDDDD",
            "DDDDDD",
            "DDDDDD",
            "DDDDDD",
            "DDDDDD",
        ),
        "enemy_trail": (
            "......",
            "..R...",
            "..R...",
            "...R..",
            "...R..",
            "......",
        ),
        "interceptor": (
            "..W...",
            ".WGW..",
            "..G...",
            "..G...",
            "..A...",
            "......",
        ),
        "city": (
            "......",
            ".G.G..",
            ".GGG..",
            "GGGGG.",
            "GAGAG.",
            "GGGGG.",
        ),
        "city_ruin": (
            "......",
            "R...R.",
            ".R.R..",
            "..R...",
            ".D.D..",
            "DDDDD.",
        ),
        "battery": (
            "..W...",
            "..W...",
            ".GGG..",
            "GGWGG.",
            "GGGGG.",
            "AAAAA.",
        ),
        "battery_empty": (
            "......",
            "..D...",
            ".DDD..",
            "DDDDD.",
            "DDDDD.",
            "AAAAA.",
        ),
    }
)

_TILE_COLOURS: Mapping[str, Rgb] = MappingProxyType(
    {
        ".": NUKE_BLACK,
        "G": NUKE_PHOSPHOR_GREEN,
        "D": NUKE_DIM_GREEN,
        "A": NUKE_AMBER,
        "Y": NUKE_YELLOW,
        "W": NUKE_WHITE,
        "R": NUKE_RED,
        "b": NUKE_CRT_BASE,
        "n": NUKE_CRT_NEUTRAL,
        "d": NUKE_CRT_DARK,
        "l": NUKE_CRT_HIGHLIGHT,
        "k": NUKE_BLACK,
    }
)


def _rectangles_overlap(first: Rect, second: Rect) -> bool:
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def _validate_layout() -> None:
    if len(set(NUKE_GLYPH_ORDER)) != len(NUKE_GLYPH_ORDER):
        raise ValueError("Nuke glyph order contains duplicate characters")
    if set(_FONT_BITMAPS) != set(NUKE_GLYPH_ORDER):
        raise ValueError("Nuke font bitmap coverage does not match glyph order")
    if set(_TILE_BITMAPS) != set(NUKE_TILE_ORDER):
        raise ValueError("Nuke tile bitmap coverage does not match tile order")

    rectangles = [
        *(('glyph ' + repr(name), rect) for name, rect in NUKE_GLYPH_RECTS.items()),
        *(("tile " + name, rect) for name, rect in NUKE_TILE_RECTS.items()),
    ]
    for name, (x, y, width, height) in rectangles:
        if width <= 0 or height <= 0:
            raise ValueError(f"{name} has a non-positive rectangle")
        if x < 0 or y < 0 or x + width > NUKE_ATLAS_WIDTH or y + height > NUKE_ATLAS_HEIGHT:
            raise ValueError(f"{name} lies outside the Nuke atlas")
    for index, (name, rect) in enumerate(rectangles):
        for other_name, other_rect in rectangles[index + 1 :]:
            if _rectangles_overlap(rect, other_rect):
                raise ValueError(f"{name} overlaps {other_name}")

    for glyph, bitmap in _FONT_BITMAPS.items():
        if len(bitmap) != NUKE_GLYPH_HEIGHT or any(
            len(row) != NUKE_GLYPH_WIDTH or set(row) - {".", "#"} for row in bitmap
        ):
            raise ValueError(f"glyph {glyph!r} is not a valid 4x6 bitmap")
        if not any("#" in row for row in bitmap):
            raise ValueError(f"glyph {glyph!r} is blank")
    for name, bitmap in _TILE_BITMAPS.items():
        if len(bitmap) != NUKE_TILE_SIZE or any(
            len(row) != NUKE_TILE_SIZE or set(row) - set(_TILE_COLOURS) for row in bitmap
        ):
            raise ValueError(f"tile {name!r} is not a valid 6x6 bitmap")
        if not any(symbol != "." for row in bitmap for symbol in row):
            raise ValueError(f"tile {name!r} is blank")


def _render_nuke_atlas_image() -> Image.Image:
    image = Image.new("RGB", (NUKE_ATLAS_WIDTH, NUKE_ATLAS_HEIGHT), NUKE_BLACK)
    pixels = image.load()
    if pixels is None:  # pragma: no cover - Pillow always exposes RGB pixels.
        raise RuntimeError("Pillow did not expose the Nuke atlas pixel buffer")

    for glyph, bitmap in _FONT_BITMAPS.items():
        x, y, _, _ = NUKE_GLYPH_RECTS[glyph]
        for row_index, row in enumerate(bitmap):
            for column_index, symbol in enumerate(row):
                if symbol == "#":
                    # Amber numerals establish a clear value hierarchy while
                    # labels and instructions retain the green CRT phosphor.
                    pixels[x + column_index, y + row_index] = (
                        NUKE_AMBER
                        if glyph in NUKE_DIGITS
                        else NUKE_PHOSPHOR_GREEN
                    )

    for name, bitmap in _TILE_BITMAPS.items():
        x, y, _, _ = NUKE_TILE_RECTS[name]
        for row_index, row in enumerate(bitmap):
            for column_index, symbol in enumerate(row):
                # Gameplay tiles are copied as opaque rectangles.  Key their
                # unused pixels to the board tile at the same cell-relative
                # coordinate so moving objects never reveal black boxes.
                if symbol == "." and name != NUKE_BOARD_BACKGROUND_TILE_NAME:
                    symbol = _BOARD_BACKGROUND_BITMAP[row_index][column_index]
                pixels[x + column_index, y + row_index] = _TILE_COLOURS[symbol]
    return image


def validate_nuke_atlas_image(image: Image.Image) -> None:
    """Reject any image that is not the exact canonical Nuke atlas."""

    if not isinstance(image, Image.Image):
        raise TypeError("Nuke atlas image must be a Pillow Image")
    if image.mode != "RGB":
        raise ValueError(f"Nuke atlas image must use RGB mode, got {image.mode!r}")
    if image.size != (NUKE_ATLAS_WIDTH, NUKE_ATLAS_HEIGHT):
        raise ValueError(
            "Nuke atlas image must be "
            f"{NUKE_ATLAS_WIDTH}x{NUKE_ATLAS_HEIGHT}, got {image.size}"
        )
    expected = _render_nuke_atlas_image()
    if image.tobytes() != expected.tobytes():
        raise ValueError("Nuke atlas image pixels do not match the canonical atlas")


def build_nuke_atlas_image() -> Image.Image:
    """Return a fresh RGB image containing the canonical Nuke atlas."""

    image = _render_nuke_atlas_image()
    validate_nuke_atlas_image(image)
    return image


def _encode_rgb555(image: Image.Image) -> bytes:
    source = image.tobytes()
    encoded = bytearray(NUKE_ATLAS_PIXEL_BYTES)
    destination = 0
    for source_offset in range(0, len(source), 3):
        red = source[source_offset] >> 3
        green = source[source_offset + 1] >> 3
        blue = source[source_offset + 2] >> 3
        struct.pack_into("<H", encoded, destination, red | (green << 5) | (blue << 10))
        destination += 2
    return bytes(encoded)


def _canonical_tim_payload() -> bytes:
    return NUKE_ATLAS_TIM_HEADER + _encode_rgb555(_render_nuke_atlas_image())


def validate_nuke_atlas_tim(data: bytes | bytearray | memoryview) -> None:
    """Reject any payload that is not the exact canonical Nuke atlas TIM."""

    payload = bytes(data)
    if len(payload) != NUKE_ATLAS_TOTAL_SIZE:
        raise ValueError(
            f"Nuke atlas TIM must be {NUKE_ATLAS_TOTAL_SIZE} bytes, got {len(payload)}"
        )
    magic, flags = struct.unpack_from("<II", payload, 0)
    block_size, vram_x, vram_y, width, height = struct.unpack_from("<IHHHH", payload, 8)
    if magic != 0x10 or flags != 0x02:
        raise ValueError(f"unexpected Nuke atlas TIM magic/flags: {magic:#x}/{flags:#x}")
    if block_size != NUKE_ATLAS_IMAGE_BLOCK_SIZE:
        raise ValueError(
            "Nuke atlas TIM image block must be "
            f"{NUKE_ATLAS_IMAGE_BLOCK_SIZE} bytes, got {block_size}"
        )
    expected_rectangle = (
        NUKE_ATLAS_VRAM_X,
        NUKE_ATLAS_VRAM_Y,
        NUKE_ATLAS_WIDTH,
        NUKE_ATLAS_HEIGHT,
    )
    if (vram_x, vram_y, width, height) != expected_rectangle:
        raise ValueError(
            "Nuke atlas TIM must target VRAM "
            f"({NUKE_ATLAS_VRAM_X},{NUKE_ATLAS_VRAM_Y}) at "
            f"{NUKE_ATLAS_WIDTH}x{NUKE_ATLAS_HEIGHT}"
        )
    words = struct.unpack_from(f"<{NUKE_ATLAS_WIDTH * NUKE_ATLAS_HEIGHT}H", payload, 20)
    if any(word & 0x8000 for word in words):
        raise ValueError("Nuke atlas TIM must keep every RGB555 STP bit clear")
    if payload != _canonical_tim_payload():
        raise ValueError("Nuke atlas TIM pixels do not match the canonical atlas")


def build_nuke_atlas_tim() -> bytes:
    """Return the deterministic 16-bpp TIM payload for the Nuke atlas."""

    payload = _canonical_tim_payload()
    validate_nuke_atlas_tim(payload)
    return payload


_validate_layout()
