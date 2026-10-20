#!/usr/bin/env python3
"""Native one-choice title menu and menu portraits for the Rico anthology.

The retail title menu is not dialogue.  Its three choices are font records in
canonical resource 2593, and the title field uploads the texture pages used by
those records from canonical resource 1587.  This module follows the proven
Mass-Driver/Surface-Soylent route: it renders ``Rico's Arc`` from Xenogears'
built-in menu font at its natural width, places that raster in checked spare
title-field VRAM, and repoints the retail New Game record to it.  Continue and
Sound remain ordinary safe polygons but sample checked transparent atlas
space, so they are genuinely absent rather than replaced with fake options.

Canonical overlay 2599 is patched last, after the Rico weight overlay.  The
input patch is accepted in its checked Disc 1 or Disc 2 form, so the title's
physical-disc gate and the weight-clamp hook are both retained while Up/Down
are made unavailable.  Confirm therefore has exactly one reachable route.
"""

from __future__ import annotations

import hashlib
import struct
from typing import Final

from shared.tools.xgfield import compress_lzss, decompress_lzss


class RicoNativeTitleError(RuntimeError):
    """A canonical title resource no longer matches its audited contract."""


def _sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Canonical identities and native layout


TITLE_GRAPHICS_CANONICAL_ID: Final = 1587
TITLE_MENU_CANONICAL_ID: Final = 2593
TITLE_OVERLAY_CANONICAL_ID: Final = 2599

TITLE_MENU_SOURCE_SIZE: Final = 0xFF80
TITLE_MENU_SOURCE_SHA256: Final = (
    "4aec6a89bcf155d19a11b76df7d4f73139b840bf1e04482a4328ae80b3428c2b"
)
TITLE_MENU_RESULT_SIZE: Final = 65_392
TITLE_MENU_RESULT_SHA256: Final = (
    "614d0b1495502aa48f1ace6d4949cb295f18be4ffafc611badd25a1dc20a0477"
)
TITLE_MENU_SECTOR_BUDGET: Final = 0x10000

TITLE_GRAPHICS_SIZE: Final = 182_272
TITLE_GRAPHICS_SOURCE_SHA256: Final = (
    "c451da6b1f1ea04eb6e654dfe60d251fbcbca3818b8e412c9d07d5505c2754e1"
)
TITLE_GRAPHICS_RESULT_SHA256: Final = (
    "53dc60b3c06788196daa50370dd0edb86f38ec2cadcbdde11776b9091c456068"
)
TITLE_GRAPHICS_LAST_CHUNK_HEIGHT_OFFSET: Final = 0x26032
TITLE_GRAPHICS_LAST_CHUNK_SOURCE_HEIGHT: Final = 4
TITLE_GRAPHICS_LAST_CHUNK_RESULT_HEIGHT: Final = 13
TITLE_GRAPHICS_ATLAS_OFFSET: Final = 0x2C200
TITLE_GRAPHICS_ATLAS_SOURCE_SHA256: Final = (
    "4cf9816ed1062189ff0c8d427fba5e912cc68fc9af76cf7f08fd255977de3b33"
)

TITLE_OVERLAY_SIZE: Final = 153_864
TITLE_OVERLAY_RETAIL_SHA256: Final = (
    "82f84a24ac1fd1979754e1cc9c861405fb59ce95dd78db00a76f00c8f1bd177d"
)
TITLE_OVERLAY_DISC2_GATE_SHA256: Final = (
    "546c59dbe8b43a7b3b8799d205ae14a0053137787132a64fa623d0739e078b15"
)
TITLE_OVERLAY_BALANCED_SHA256: Final = (
    "960e852c3830e7c721901aa4373448a8bfc49681fcf3e34b11feed69af56a484"
)
TITLE_OVERLAY_DISC2_BALANCED_SHA256: Final = (
    "a054649dc96943719562462c90474441ff9eeff7cae41b3a9eb9909bf9214701"
)

ARCHIVE_ENTRY_COUNT: Final = 8
ARCHIVE_SOURCE_OFFSETS: Final = (
    0x0028,
    0x00EC,
    0x7160,
    0x85A8,
    0x8CC8,
    0xF9F8,
    0xFA7C,
    0xFCF4,
)
TITLE_IMAGE_ENTRY: Final = 1
TITLE_FONT_ENTRY: Final = 2
TITLE_IMAGES_SIZE: Final = 0xA2FC
TITLE_IMAGES_SHA256: Final = (
    "69dd2d2f7af2beec83fd00cd9fccd63c6395e48d62f15a1d1f5ee09c48f695d0"
)
TITLE_FONT_SIZE: Final = 0x5C47
TITLE_FONT_SHA256: Final = (
    "2707fb2fcfc4660436328d3bdc930a32a70751a7dbf72d005a718ed189732898"
)
TITLE_FONT_RESULT_SHA256: Final = (
    "729405bc4c3160763cc0dc1f893ef580604151bf3f676545c1d0b330fde7cd2f"
)
TITLE_FONT_PACKED_RESULT_SIZE: Final = 5_176
TITLE_FONT_PACKED_RESULT_SHA256: Final = (
    "6eb274aaefda123269d10c9f9b3305729eded8f82184e6f6c620c401a9e1933e"
)

# The main menu indexes this decoded portrait sheet by live character ID.  The
# standalone anthology reserves slot 10 for Chapter 1's young Rico, leaving
# adult Rico's slot 5 byte-for-byte intact for every later chapter.
MENU_PORTRAIT_ENTRY: Final = 4
MENU_PORTRAIT_SOURCE_SIZE: Final = 0x6D30
MENU_PORTRAIT_SOURCE_SHA256: Final = (
    "871063f46ee9ddaf333d19f6a5991038e5949963923fffe5b2777ac7544b0e02"
)
MENU_PORTRAIT_DECODED_SIZE: Final = 0x7A66
MENU_PORTRAIT_DECODED_SHA256: Final = (
    "cc2e9b78cc484b49175b4c1fb1f85dfa8b733a1d688d99607f155632d7fb9ec6"
)
MENU_PORTRAIT_TIM_SIZE: Final = 0xB20
MENU_PORTRAIT_COUNT: Final = 11
YOUNG_RICO_PORTRAIT_SLOT: Final = 10
YOUNG_RICO_PORTRAIT_OFFSET: Final = (
    YOUNG_RICO_PORTRAIT_SLOT * MENU_PORTRAIT_TIM_SIZE
)
YOUNG_RICO_PORTRAIT_SOURCE_SHA256: Final = (
    "bd6a0d2b1988febdd4885bda119af81f2da6b068b411094541b51b09efaf3e1a"
)
YOUNG_RICO_PORTRAIT_TIM_SHA256: Final = (
    "b57e22ae1c5c4858bede38fd45e950a05662dc2cdd855cc2bc2c43d1b5559542"
)
MENU_PORTRAIT_PATCHED_SHA256: Final = (
    "36a8cddf7289aeaf7fff2aed520fd003e8b392bb05d105e9594cee5785f04742"
)
MENU_PORTRAIT_PATCHED_DECODED_SHA256: Final = (
    "a2c9dcd957efbb6c6ccd86d3e9cc1e5a631fa43bb50ecf6a1040557257b84628"
)
MENU_PORTRAIT_TAIL_SIZE: Final = 6

IMAGE_BUNDLE_COUNT: Final = 33
STANDARD_FONT_TIM_INDEX: Final = 9
STANDARD_FONT_TIM_POINTER: Final = 0x2FD0
STANDARD_FONT_CLUT: Final = (304, 509)
STANDARD_FONT_IMAGE: Final = (479, 120, 32, 112)
FONT_GLYPH_COUNT: Final = 385
APOSTROPHE_GLYPH: Final = 0x93

RICO_TITLE_TEXT: Final = "Rico's Arc"
RICO_TITLE_WIDTH: Final = 57
TITLE_LABEL_HEIGHT: Final = 9
TITLE_LABEL_GLYPHS: Final = (0x123, 0x124, 0x125)
TITLE_LABEL_TEXTURE_U: Final = (0, 64, 112)
TITLE_LABEL_WIDTHS: Final = (RICO_TITLE_WIDTH, 41, 27)
TITLE_LABEL_SCREEN_Y: Final = (10, 29, 49)
# Center the sole 57-pixel label in Mass Driver's proven 68-pixel first-row
# footprint instead of stranding it at the left edge of a three-row layout.
TITLE_LABEL_SCREEN_X: Final = -69
TITLE_LABEL_TEXTURE_WIDTH: Final = 256
TITLE_LABEL_TEXTURE_HEIGHT: Final = 9
TITLE_LABEL_TEXTURE_VRAM: Final = (960, 180)
TITLE_LABEL_ATLAS_SHA256: Final = (
    "dd5b997dc569e624d6b3245b4ffd0422a43ef3e26f086f361af4aca0dd3cf1bd"
)

# Retail label records are pinned so the transform cannot silently target a
# different regional or modified font table.
TITLE_LABEL_SOURCE_RECORDS: Final = {
    0x123: bytes.fromhex(
        "01 00 00 00 00 00 A6 00 2C 00 09 00 A5 FF 0A 00 "
        "04 00 00 00 00 00 10 01 FD 01 C0 01 94 00 00 00"
    ),
    0x124: bytes.fromhex(
        "01 00 00 00 2C 00 A6 00 29 00 09 00 AA FF 1D 00 "
        "04 00 00 00 00 00 10 01 FD 01 C0 01 94 00 00 00"
    ),
    0x125: bytes.fromhex(
        "01 00 00 00 00 00 C1 00 1B 00 09 00 AB FF 31 00 "
        "04 00 00 00 00 00 10 01 FD 01 C0 01 94 00 00 00"
    ),
}
APOSTROPHE_SOURCE_RECORD: Final = bytes.fromhex(
    "01 00 00 00 DC 00 B0 00 08 00 08 00 00 00 00 00 "
    "04 00 00 00 00 00 30 01 FD 01 DF 01 78 00 00 00"
)


# ---------------------------------------------------------------------------
# Checked menu archive and retail-complete compression


def _archive_entries(data: bytes) -> tuple[bytes, tuple[bytes, ...]]:
    if len(data) != TITLE_MENU_SOURCE_SIZE or _sha256(data) != TITLE_MENU_SOURCE_SHA256:
        raise RicoNativeTitleError(
            "Rico native title requires clean USA canonical resource 2593"
        )
    count = struct.unpack_from("<I", data, 0)[0]
    if count != ARCHIVE_ENTRY_COUNT:
        raise RicoNativeTitleError(f"Title-menu archive has {count} entries")
    offsets = struct.unpack_from(f"<{count}I", data, 4)
    if offsets != ARCHIVE_SOURCE_OFFSETS:
        raise RicoNativeTitleError("Title-menu archive offsets changed")
    entries = tuple(
        data[start : offsets[index + 1] if index + 1 < count else len(data)]
        for index, start in enumerate(offsets)
    )
    return data[: offsets[0]], entries


def _decode_entry(
    entry: bytes,
    *,
    expected_size: int,
    expected_sha256: str,
    label: str,
) -> bytes:
    if len(entry) < 4 or struct.unpack_from("<I", entry, 0)[0] != expected_size:
        raise RicoNativeTitleError(f"{label} has an unexpected decoded size")
    decoded = decompress_lzss(entry + bytes(16), expected_size).data
    if _sha256(decoded) != expected_sha256:
        raise RicoNativeTitleError(f"{label} decoded hash changed")
    return decoded


def _decode_complete_groups(stream: bytes) -> tuple[bytes, int]:
    """Model the retail decoder, which executes all eight commands per group."""

    if len(stream) < 4:
        raise RicoNativeTitleError("LZSS stream is shorter than its header")
    declared_size = struct.unpack_from("<I", stream, 0)[0]
    position = 4
    output = bytearray()
    while len(output) < declared_size:
        if position >= len(stream):
            raise RicoNativeTitleError("LZSS stream ends before a control group")
        control = stream[position]
        position += 1
        for bit in range(8):
            if control & (1 << bit):
                if position + 2 > len(stream):
                    raise RicoNativeTitleError("LZSS backreference is truncated")
                low, high = stream[position : position + 2]
                position += 2
                distance = low | ((high & 0x0F) << 8)
                length = (high >> 4) + 3
                if not 1 <= distance <= len(output):
                    raise RicoNativeTitleError("LZSS backreference is invalid")
                for _ in range(length):
                    output.append(output[-distance])
            else:
                if position >= len(stream):
                    raise RicoNativeTitleError("LZSS literal is truncated")
                output.append(stream[position])
                position += 1
        if len(output) > declared_size:
            raise RicoNativeTitleError("LZSS group overruns its allocation")
    return bytes(output), position


def _compress_exact_complete_groups(data: bytes) -> bytes:
    """Encode exact-size data and end on an eight-command boundary."""

    if not data:
        return bytes(4)
    packed = compress_lzss(data)
    position = 4
    output_size = 0
    commands: list[tuple[bool, bytes, int]] = []
    while output_size < len(data):
        if position >= len(packed):
            raise RicoNativeTitleError("Compact LZSS stream lost a control group")
        control = packed[position]
        position += 1
        for bit in range(8):
            if output_size >= len(data):
                break
            is_reference = bool(control & (1 << bit))
            payload_size = 2 if is_reference else 1
            if position + payload_size > len(packed):
                raise RicoNativeTitleError("Compact LZSS command is truncated")
            payload = packed[position : position + payload_size]
            position += payload_size
            command_size = (payload[1] >> 4) + 3 if is_reference else 1
            commands.append((is_reference, payload, command_size))
            output_size += command_size
            if output_size > len(data):
                raise RicoNativeTitleError("Compact LZSS command exceeds its source")

    missing_commands = (-len(commands)) % 8
    command_index = 0
    while missing_commands and command_index < len(commands):
        is_reference, payload, command_size = commands[command_index]
        if not is_reference:
            command_index += 1
            continue
        split_count = min(missing_commands, command_size // 3 - 1)
        if split_count <= 0:
            command_index += 1
            continue
        low, high = payload[0], payload[1] & 0x0F
        lengths = [3] * split_count + [command_size - 3 * split_count]
        replacements = [
            (True, bytes((low, high | ((length - 3) << 4))), length)
            for length in lengths
        ]
        commands[command_index : command_index + 1] = replacements
        missing_commands -= split_count
        command_index += len(replacements)
    if missing_commands or len(commands) % 8:
        raise RicoNativeTitleError("LZSS stream cannot end at exact decoded size")

    result = bytearray(struct.pack("<I", len(data)))
    for start in range(0, len(commands), 8):
        group = commands[start : start + 8]
        result.append(
            sum(
                (1 << bit) if is_reference else 0
                for bit, (is_reference, _payload, _size) in enumerate(group)
            )
        )
        for _is_reference, payload, _size in group:
            result.extend(payload)
    result.extend(bytes((-len(result)) % 4))
    decoded, consumed = _decode_complete_groups(bytes(result))
    if decoded != data or consumed > len(result):
        raise RicoNativeTitleError("Exact LZSS stream failed retail decoding")
    return bytes(result)


def _rebuild_archive(header: bytes, entries: tuple[bytes, ...]) -> tuple[bytes, tuple[int, ...]]:
    result = bytearray(header)
    offsets: list[int] = []
    for entry in entries:
        result.extend(bytes((-len(result)) % 4))
        offsets.append(len(result))
        result.extend(entry)
    struct.pack_into(f"<{len(offsets)}I", result, 4, *offsets)
    return bytes(result), tuple(offsets)


def _validate_young_rico_portrait_tim(tim: bytes) -> None:
    if (
        len(tim) != MENU_PORTRAIT_TIM_SIZE
        or _sha256(tim) != YOUNG_RICO_PORTRAIT_TIM_SHA256
    ):
        raise RicoNativeTitleError("young-Rico menu portrait asset changed")
    if struct.unpack_from("<II", tim, 0) != (0x10, 0x09):
        raise RicoNativeTitleError("young-Rico portrait is not an 8-bpp TIM")
    if struct.unpack_from("<I4H", tim, 8) != (0x20C, 0, 480, 256, 1):
        raise RicoNativeTitleError("young-Rico portrait CLUT layout changed")
    if struct.unpack_from("<I4H", tim, 0x214) != (0x90C, 0, 0, 24, 48):
        raise RicoNativeTitleError("young-Rico portrait image layout changed")
    palette = struct.unpack_from("<256H", tim, 0x14)
    pixels = tim[0x220:]
    used = set(pixels)
    if palette[0] != 0 or not used <= set(range(64)) or 0 not in used:
        raise RicoNativeTitleError("young-Rico portrait palette contract changed")
    if any(not palette[index] & 0x8000 for index in used - {0}):
        raise RicoNativeTitleError("young-Rico portrait opaque color lost STP")
    if any(palette[index] for index in range(64, 256)):
        raise RicoNativeTitleError("young-Rico portrait has unexpected palette data")


def _patch_young_rico_portrait(entry: bytes, tim: bytes) -> bytes:
    if (
        len(entry) != MENU_PORTRAIT_SOURCE_SIZE
        or _sha256(entry) != MENU_PORTRAIT_SOURCE_SHA256
    ):
        raise RicoNativeTitleError("menu portrait archive entry changed")
    _validate_young_rico_portrait_tim(tim)
    decoded, consumed = _decode_complete_groups(entry + bytes(16))
    if (
        consumed > len(entry) + 16
        or len(decoded) != MENU_PORTRAIT_DECODED_SIZE
        or _sha256(decoded) != MENU_PORTRAIT_DECODED_SHA256
    ):
        raise RicoNativeTitleError("menu portrait sheet identity changed")
    source_slot = decoded[
        YOUNG_RICO_PORTRAIT_OFFSET :
        YOUNG_RICO_PORTRAIT_OFFSET + MENU_PORTRAIT_TIM_SIZE
    ]
    if _sha256(source_slot) != YOUNG_RICO_PORTRAIT_SOURCE_SHA256:
        raise RicoNativeTitleError("retail portrait slot 10 changed")
    if decoded[MENU_PORTRAIT_COUNT * MENU_PORTRAIT_TIM_SIZE :] != bytes(
        MENU_PORTRAIT_TAIL_SIZE
    ):
        raise RicoNativeTitleError("menu portrait sheet tail changed")

    patched = bytearray(decoded)
    patched[
        YOUNG_RICO_PORTRAIT_OFFSET :
        YOUNG_RICO_PORTRAIT_OFFSET + MENU_PORTRAIT_TIM_SIZE
    ] = tim
    packed = _compress_exact_complete_groups(bytes(patched))
    if len(packed) > MENU_PORTRAIT_SOURCE_SIZE:
        raise RicoNativeTitleError(
            "young-Rico portrait exceeds the fixed menu archive allocation"
        )
    packed += bytes(MENU_PORTRAIT_SOURCE_SIZE - len(packed))
    round_trip, round_trip_consumed = _decode_complete_groups(packed)
    if round_trip != bytes(patched) or round_trip_consumed > len(packed):
        raise RicoNativeTitleError("young-Rico portrait failed retail round-trip")
    if (
        _sha256(packed) != MENU_PORTRAIT_PATCHED_SHA256
        or _sha256(round_trip) != MENU_PORTRAIT_PATCHED_DECODED_SHA256
    ):
        raise RicoNativeTitleError("young-Rico portrait output changed")
    return packed


# ---------------------------------------------------------------------------
# Built-in-font raster and custom records


def _font_records(font: bytes) -> tuple[int, tuple[bytes, ...]]:
    if len(font) != TITLE_FONT_SIZE:
        raise RicoNativeTitleError("Title font has an unexpected size")
    count = struct.unpack_from("<I", font, 0)[0]
    if count != FONT_GLYPH_COUNT or 4 + count * 2 > len(font):
        raise RicoNativeTitleError(f"Title font has invalid glyph count {count}")
    offsets = struct.unpack_from(f"<{count}H", font, 4)
    if offsets[0] != 4 + count * 2 or any(
        left >= right for left, right in zip(offsets, offsets[1:])
    ):
        raise RicoNativeTitleError("Title font offsets are invalid")
    records = tuple(
        font[start : offsets[index + 1] if index + 1 < count else len(font)]
        for index, start in enumerate(offsets)
    )
    for index, expected in TITLE_LABEL_SOURCE_RECORDS.items():
        if records[index] != expected:
            raise RicoNativeTitleError(f"Retail label record 0x{index:X} changed")
    if records[APOSTROPHE_GLYPH] != APOSTROPHE_SOURCE_RECORD:
        raise RicoNativeTitleError("Retail apostrophe record changed")
    return count, records


def _standard_font_pixels(image_bundle: bytes) -> tuple[int, int, int, int, bytes]:
    if len(image_bundle) != TITLE_IMAGES_SIZE:
        raise RicoNativeTitleError("Title image bundle has an unexpected size")
    count = struct.unpack_from("<I", image_bundle, 0)[0]
    if count != IMAGE_BUNDLE_COUNT:
        raise RicoNativeTitleError("Title image bundle count changed")
    pointers = struct.unpack_from(f"<{count}I", image_bundle, 4)
    if pointers[STANDARD_FONT_TIM_INDEX] != STANDARD_FONT_TIM_POINTER:
        raise RicoNativeTitleError("Standard-font TIM pointer changed")
    pointer = STANDARD_FONT_TIM_POINTER
    if struct.unpack_from("<II", image_bundle, pointer) != (0x10, 0x08):
        raise RicoNativeTitleError("Standard font is not a checked 4-bpp TIM")
    cursor = pointer + 8
    clut_size, clut_x, clut_y, clut_width, clut_height = struct.unpack_from(
        "<I4H", image_bundle, cursor
    )
    if (
        clut_size != 44
        or (clut_x, clut_y) != STANDARD_FONT_CLUT
        or (clut_width, clut_height) != (16, 1)
    ):
        raise RicoNativeTitleError("Standard-font CLUT changed")
    cursor += clut_size
    block_size, image_x, image_y, width_words, height = struct.unpack_from(
        "<I4H", image_bundle, cursor
    )
    pixel_size = width_words * height * 2
    if (
        (image_x, image_y, width_words, height) != STANDARD_FONT_IMAGE
        or block_size != 12 + pixel_size
    ):
        raise RicoNativeTitleError("Standard-font TIM layout changed")
    return (
        image_x,
        image_y,
        width_words,
        height,
        image_bundle[cursor + 12 : cursor + block_size],
    )


def _source_glyph_index(character: str) -> int:
    if "0" <= character <= "9":
        return ord(character) - ord("0")
    if "A" <= character <= "Z":
        return 0x0A + ord(character) - ord("A")
    if "a" <= character <= "z":
        return 0x24 + ord(character) - ord("a")
    if character == "'":
        return APOSTROPHE_GLYPH
    raise RicoNativeTitleError(f"Unsupported native-title character {character!r}")


def _render_native_label(
    image_bundle: bytes,
    records: tuple[bytes, ...],
) -> list[list[int]]:
    image_x, image_y, width_words, image_height, pixels = _standard_font_pixels(
        image_bundle
    )

    def source_pixel(x: int, y: int) -> int:
        if not (0 <= x < width_words * 4 and 0 <= y < image_height):
            raise RicoNativeTitleError("Native title glyph leaves its source TIM")
        pixel_index = y * width_words * 4 + x
        packed = pixels[pixel_index // 2]
        return (packed >> 4) & 0x0F if pixel_index & 1 else packed & 0x0F

    def glyph_canvas(character: str) -> list[list[int]]:
        if character == " ":
            return [[0] * 3 for _ in range(TITLE_LABEL_HEIGHT)]
        record = records[_source_glyph_index(character)]
        if len(record) != 32 or struct.unpack_from("<HH", record, 0) != (1, 0):
            raise RicoNativeTitleError(
                f"Native source glyph {character!r} is not one polygon"
            )
        values = struct.unpack_from("<14h", record, 4)
        texture_u, texture_v, width, height, offset_x, offset_y = values[:6]
        clut_x, clut_y, tpage_x, tpage_y = values[9:13]
        if (
            values[6:9] != (4, 0, 0)
            or (clut_x, clut_y) != STANDARD_FONT_CLUT
            or (tpage_x, tpage_y) != STANDARD_FONT_IMAGE[:2]
            or offset_x < 0
            or offset_y < 0
            or width <= 0
            or height <= 0
            or offset_y + height > TITLE_LABEL_HEIGHT
        ):
            raise RicoNativeTitleError(f"Native source glyph {character!r} changed")
        page_x = (tpage_x // 64) * 256
        page_y = (tpage_y // 256) * 256
        local_x = page_x + texture_u - image_x * 4
        local_y = page_y + texture_v - image_y
        canvas = [
            [0] * max(1, offset_x + width) for _ in range(TITLE_LABEL_HEIGHT)
        ]
        for y in range(height):
            for x in range(width):
                canvas[offset_y + y][offset_x + x] = source_pixel(
                    local_x + x, local_y + y
                )
        occupied = [x for row in canvas for x, value in enumerate(row) if value]
        if not occupied:
            raise RicoNativeTitleError(f"Native source glyph {character!r} is empty")
        left, right = min(occupied), max(occupied)
        return [row[left : right + 1] for row in canvas]

    glyphs = [glyph_canvas(character) for character in RICO_TITLE_TEXT]
    width = sum(len(glyph[0]) for glyph in glyphs) + len(glyphs) - 1
    if width != RICO_TITLE_WIDTH:
        raise RicoNativeTitleError(f"Rico's Arc rendered at unexpected width {width}")
    rendered = [[0] * width for _ in range(TITLE_LABEL_HEIGHT)]
    cursor = 0
    for glyph in glyphs:
        for y, row in enumerate(glyph):
            rendered[y][cursor : cursor + len(row)] = row
        cursor += len(glyph[0]) + 1
    return rendered


def _build_label_atlas(label: list[list[int]]) -> bytes:
    if len(label) != TITLE_LABEL_HEIGHT or any(
        len(row) != RICO_TITLE_WIDTH for row in label
    ):
        raise RicoNativeTitleError("Rico title raster dimensions changed")
    rows = [
        [0] * TITLE_LABEL_TEXTURE_WIDTH for _ in range(TITLE_LABEL_TEXTURE_HEIGHT)
    ]
    for y, row in enumerate(label):
        rows[y][:RICO_TITLE_WIDTH] = row
    packed = bytes(
        row[x] | (row[x + 1] << 4)
        for row in rows
        for x in range(0, TITLE_LABEL_TEXTURE_WIDTH, 2)
    )
    if TITLE_LABEL_ATLAS_SHA256 and _sha256(packed) != TITLE_LABEL_ATLAS_SHA256:
        raise RicoNativeTitleError("Rico native-title atlas changed")
    return packed


def _rebuild_font(count: int, source_records: tuple[bytes, ...]) -> bytes:
    records = list(source_records)
    vram_x, vram_y = TITLE_LABEL_TEXTURE_VRAM
    for index, (glyph, texture_u, width, screen_y) in enumerate(zip(
        TITLE_LABEL_GLYPHS,
        TITLE_LABEL_TEXTURE_U,
        TITLE_LABEL_WIDTHS,
        TITLE_LABEL_SCREEN_Y,
        strict=True,
    )):
        # Rows 1 and 2 deliberately sample checked-transparent atlas space.
        # Keeping normal 9-pixel polygons is safer than depending on undefined
        # zero-width GPU behavior while making both labels fully invisible.
        records[glyph] = struct.pack(
            "<HH14h",
            1,
            0,
            texture_u,
            vram_y,
            width,
            TITLE_LABEL_HEIGHT,
            TITLE_LABEL_SCREEN_X,
            screen_y,
            4,
            0,
            0,
            STANDARD_FONT_CLUT[0],
            STANDARD_FONT_CLUT[1],
            vram_x,
            vram_y,
            0,
        )
        if index and texture_u < RICO_TITLE_WIDTH:
            raise RicoNativeTitleError("Hidden title label overlaps Rico's Arc")

    rebuilt = bytearray(struct.pack("<I", count))
    rebuilt.extend(bytes(count * 2))
    offsets: list[int] = []
    for record in records:
        offsets.append(len(rebuilt))
        rebuilt.extend(record)
    struct.pack_into(f"<{count}H", rebuilt, 4, *offsets)
    result = bytes(rebuilt)
    if len(result) != TITLE_FONT_SIZE:
        raise RicoNativeTitleError("Rebuilt native title font changed size")
    if TITLE_FONT_RESULT_SHA256 and _sha256(result) != TITLE_FONT_RESULT_SHA256:
        raise RicoNativeTitleError("Rebuilt native title font changed")
    _count, result_records = _font_records_unchecked(result)
    for index, (before, after) in enumerate(
        zip(source_records, result_records, strict=True)
    ):
        if index not in TITLE_LABEL_GLYPHS and before != after:
            raise RicoNativeTitleError(f"Unrelated native glyph 0x{index:X} changed")
    return result


def _font_records_unchecked(font: bytes) -> tuple[int, tuple[bytes, ...]]:
    count = struct.unpack_from("<I", font, 0)[0]
    offsets = struct.unpack_from(f"<{count}H", font, 4)
    records = tuple(
        font[start : offsets[index + 1] if index + 1 < count else len(font)]
        for index, start in enumerate(offsets)
    )
    return count, records


def build_rico_native_title_menu(
    source: bytes,
    young_rico_tim: bytes,
) -> tuple[bytes, bytes]:
    """Return title atlas and menu data with a dedicated young-Rico portrait."""

    header, original_entries = _archive_entries(source)
    images = _decode_entry(
        original_entries[TITLE_IMAGE_ENTRY],
        expected_size=TITLE_IMAGES_SIZE,
        expected_sha256=TITLE_IMAGES_SHA256,
        label="title image bundle",
    )
    font = _decode_entry(
        original_entries[TITLE_FONT_ENTRY],
        expected_size=TITLE_FONT_SIZE,
        expected_sha256=TITLE_FONT_SHA256,
        label="title font",
    )
    count, records = _font_records(font)
    atlas = _build_label_atlas(_render_native_label(images, records))
    patched_font = _rebuild_font(count, records)
    packed_font = _compress_exact_complete_groups(patched_font)
    decoded, consumed = _decode_complete_groups(packed_font)
    if decoded != patched_font or consumed > len(packed_font):
        raise RicoNativeTitleError("Packed native title font failed retail decoding")
    if TITLE_FONT_PACKED_RESULT_SIZE and (
        len(packed_font) != TITLE_FONT_PACKED_RESULT_SIZE
        or _sha256(packed_font) != TITLE_FONT_PACKED_RESULT_SHA256
    ):
        raise RicoNativeTitleError("Packed native title font changed")

    entries = list(original_entries)
    entries[TITLE_FONT_ENTRY] = packed_font
    entries[MENU_PORTRAIT_ENTRY] = _patch_young_rico_portrait(
        original_entries[MENU_PORTRAIT_ENTRY],
        young_rico_tim,
    )
    result, _offsets = _rebuild_archive(header, tuple(entries))
    if len(result) > TITLE_MENU_SECTOR_BUDGET:
        raise RicoNativeTitleError("Native title menu exceeds its CD-sector budget")
    if TITLE_MENU_RESULT_SIZE and (
        len(result) != TITLE_MENU_RESULT_SIZE
        or _sha256(result) != TITLE_MENU_RESULT_SHA256
    ):
        raise RicoNativeTitleError("Native title menu output changed")
    for index, (before, after) in enumerate(
        zip(original_entries, entries, strict=True)
    ):
        if index not in (TITLE_FONT_ENTRY, MENU_PORTRAIT_ENTRY) and before != after:
            raise RicoNativeTitleError(f"Unrelated menu archive entry {index} changed")
    return atlas, result


def patch_rico_native_title_graphics(source: bytes, atlas: bytes) -> bytes:
    """Upload the checked native-label atlas through canonical 1587 padding."""

    if (
        len(source) != TITLE_GRAPHICS_SIZE
        or _sha256(source) != TITLE_GRAPHICS_SOURCE_SHA256
    ):
        raise RicoNativeTitleError(
            "Rico native title requires clean USA canonical resource 1587"
        )
    if len(atlas) != TITLE_LABEL_TEXTURE_WIDTH * TITLE_LABEL_TEXTURE_HEIGHT // 2:
        raise RicoNativeTitleError("Native title atlas has an unexpected size")
    if TITLE_LABEL_ATLAS_SHA256 and _sha256(atlas) != TITLE_LABEL_ATLAS_SHA256:
        raise RicoNativeTitleError("Native title atlas identity changed")
    height_offset = TITLE_GRAPHICS_LAST_CHUNK_HEIGHT_OFFSET
    if struct.unpack_from("<H", source, height_offset)[0] != (
        TITLE_GRAPHICS_LAST_CHUNK_SOURCE_HEIGHT
    ):
        raise RicoNativeTitleError("Title graphics final chunk changed")
    atlas_offset = TITLE_GRAPHICS_ATLAS_OFFSET
    atlas_end = atlas_offset + len(atlas)
    if _sha256(source[atlas_offset:atlas_end]) != TITLE_GRAPHICS_ATLAS_SOURCE_SHA256:
        raise RicoNativeTitleError("Title graphics spare atlas rows changed")

    result = bytearray(source)
    struct.pack_into(
        "<H", result, height_offset, TITLE_GRAPHICS_LAST_CHUNK_RESULT_HEIGHT
    )
    result[atlas_offset:atlas_end] = atlas
    patched = bytes(result)
    if TITLE_GRAPHICS_RESULT_SHA256 and _sha256(patched) != TITLE_GRAPHICS_RESULT_SHA256:
        raise RicoNativeTitleError("Native title graphics output changed")
    if (
        patched[:height_offset] != source[:height_offset]
        or patched[height_offset + 2 : atlas_offset]
        != source[height_offset + 2 : atlas_offset]
        or patched[atlas_end:] != source[atlas_end:]
    ):
        raise RicoNativeTitleError("Title graphics changed outside checked padding")
    return patched


# ---------------------------------------------------------------------------
# One reachable row, composed after the weight overlay


TITLE_EXPECTED_DISC_OFFSET: Final = 0x13B8
TITLE_EXPECT_DISC_INSTRUCTIONS: Final = {
    1: bytes.fromhex("21 20 00 00"),
    2: bytes.fromhex("01 00 04 34"),
}
TITLE_SELECTION_CONFIG_OFFSET: Final = 0x251D4
TITLE_SELECTION_CONFIG: Final = bytes.fromhex(
    "09 01 00 00 25 01 00 00 0A 01 00 00 24 01 00 00 "
    "0B 01 00 00 23 01 00 00"
)
TITLE_CONFIRM_SOUND_DISPATCH_OFFSET: Final = 0x2E2C
TITLE_CONFIRM_SOUND_DISPATCH: Final = bytes.fromhex(
    "5D 21 07 0C 02 00 04 34"
)
TITLE_DIRECTION_SOUND_DISPATCH_OFFSET: Final = 0x2E6C

_DIRECTION_GATE_SOURCE: Final = bytes.fromhex(
    "36 03 82 90 00 00 00 00 04 00 40 10 00 00 00 00 "
    "36 03 82 90 83 16 07 08 FF FF 42 24 02 00 02 34 "
    "91 16 07 08 36 03 82 A0 36 03 82 90 00 00 00 00"
)
_DIRECTION_GATE_RESULT: Final = bytes.fromhex(
    "06 80 02 3C 60 94 42 90 02 00 03 34 06 00 43 14 "
    "01 00 02 34 03 00 02 12 03 00 02 34 02 00 02 16 "
    "00 00 00 00 04 00 04 34 5D 21 07 08 00 00 00 00"
)
TITLE_OVERLAY_UI_EDITS: Final = (
    (0x1AFC, bytes.fromhex("01 00 02 34"), bytes.fromhex("02 00 02 34")),
    (0x0960, bytes.fromhex("2C 00 62 10"), bytes.fromhex("38 00 62 10")),
    (0x0970, bytes.fromhex("1E 00 71 10"), bytes.fromhex("34 00 71 10")),
    (0x09EC, _DIRECTION_GATE_SOURCE, _DIRECTION_GATE_RESULT),
    (0x2E6C, bytes.fromhex("5D 21 07 0C"), bytes.fromhex("7B 16 07 0C")),
)

# Source hash -> (physical disc, balanced, deterministic result hash).  Result
# values are frozen after the first audited build below.
TITLE_OVERLAY_INPUTS: Final = {
    TITLE_OVERLAY_RETAIL_SHA256: (
        1,
        False,
        "485c5f68d355bf2ed34072f4cc3003325af760cc7dda72be9586579b9fb2b8e5",
    ),
    TITLE_OVERLAY_DISC2_GATE_SHA256: (
        2,
        False,
        "92da8abf01921e330a7d02d6cd08b77ee65b820fc52f5ea150dc112b97e373a8",
    ),
    TITLE_OVERLAY_BALANCED_SHA256: (
        1,
        True,
        "795d7a202e3aff8e49be90177c3ffe7c42da3401b33b7a36e2a35070c6fb7bf2",
    ),
    TITLE_OVERLAY_DISC2_BALANCED_SHA256: (
        2,
        True,
        "40567343d11aead55eb3d067d688d68110f25540600a82c939357588ec4e0f1d",
    ),
}


def patch_rico_native_title_overlay(source: bytes, *, expected_disc: int) -> bytes:
    """Lock title input to ``Rico's Arc`` after optional balance patching.

    ``expected_disc`` is the physical one-based disc number.  It must match the
    source overlay's existing New Game gate; this function never guesses or
    silently changes disc identity.
    """

    actual_hash = _sha256(source)
    identity = TITLE_OVERLAY_INPUTS.get(actual_hash)
    if len(source) != TITLE_OVERLAY_SIZE or identity is None:
        raise RicoNativeTitleError(
            f"Rico title overlay is not a checked retail/balanced input: {actual_hash}"
        )
    source_disc, _balanced, expected_hash = identity
    if expected_disc not in TITLE_EXPECT_DISC_INSTRUCTIONS:
        raise RicoNativeTitleError("expected_disc must be physical disc 1 or 2")
    if source_disc != expected_disc:
        raise RicoNativeTitleError(
            f"Title overlay expects Disc {source_disc}, not Disc {expected_disc}"
        )
    disc_instruction = TITLE_EXPECT_DISC_INSTRUCTIONS[expected_disc]
    if (
        source[
            TITLE_EXPECTED_DISC_OFFSET : TITLE_EXPECTED_DISC_OFFSET + 4
        ]
        != disc_instruction
    ):
        raise RicoNativeTitleError("Title expected-disc instruction changed")
    if (
        source[
            TITLE_SELECTION_CONFIG_OFFSET :
            TITLE_SELECTION_CONFIG_OFFSET + len(TITLE_SELECTION_CONFIG)
        ]
        != TITLE_SELECTION_CONFIG
    ):
        raise RicoNativeTitleError("Title selection table changed")
    if (
        source[
            TITLE_CONFIRM_SOUND_DISPATCH_OFFSET :
            TITLE_CONFIRM_SOUND_DISPATCH_OFFSET + len(TITLE_CONFIRM_SOUND_DISPATCH)
        ]
        != TITLE_CONFIRM_SOUND_DISPATCH
    ):
        raise RicoNativeTitleError("Title confirm-sound dispatch changed")

    result = bytearray(source)
    allowed: set[int] = set()
    for offset, before, after in TITLE_OVERLAY_UI_EDITS:
        if result[offset : offset + len(before)] != before:
            raise RicoNativeTitleError(
                f"Title one-choice input check failed at 0x{offset:X}"
            )
        result[offset : offset + len(before)] = after
        allowed.update(range(offset, offset + len(before)))
    patched = bytes(result)
    if expected_hash and _sha256(patched) != expected_hash:
        raise RicoNativeTitleError("Native one-choice title overlay changed")
    if any(
        before != after and index not in allowed
        for index, (before, after) in enumerate(zip(source, patched, strict=True))
    ):
        raise RicoNativeTitleError("Title overlay changed outside one-choice input")
    if (
        patched[
            TITLE_EXPECTED_DISC_OFFSET : TITLE_EXPECTED_DISC_OFFSET + 4
        ]
        != disc_instruction
        or patched[
            TITLE_SELECTION_CONFIG_OFFSET :
            TITLE_SELECTION_CONFIG_OFFSET + len(TITLE_SELECTION_CONFIG)
        ]
        != TITLE_SELECTION_CONFIG
        or patched[
            TITLE_CONFIRM_SOUND_DISPATCH_OFFSET :
            TITLE_CONFIRM_SOUND_DISPATCH_OFFSET + len(TITLE_CONFIRM_SOUND_DISPATCH)
        ]
        != TITLE_CONFIRM_SOUND_DISPATCH
    ):
        raise RicoNativeTitleError("Native title altered disc/selection/confirm state")
    return patched


__all__ = [
    "RICO_TITLE_TEXT",
    "RicoNativeTitleError",
    "TITLE_GRAPHICS_CANONICAL_ID",
    "TITLE_MENU_CANONICAL_ID",
    "TITLE_OVERLAY_CANONICAL_ID",
    "build_rico_native_title_menu",
    "patch_rico_native_title_graphics",
    "patch_rico_native_title_overlay",
]
