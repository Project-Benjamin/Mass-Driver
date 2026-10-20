#!/usr/bin/env python3
"""Build the provenance-checked ``Rico's Arc`` retail title-menu label.

The USA discs store the three title choices as 4-bpp raster labels inside
canonical menu resource 2593, not as dialogue text.  This transform changes
only the 44-by-9-pixel ``New Game`` rectangle.  ``Continue``, ``Sound``, the
menu-font records, palettes, title field, title graphics, and menu executable
remain byte-for-byte untouched.
"""

from __future__ import annotations

import hashlib
import struct

from shared.tools.xgfield import compress_lzss, decompress_lzss


TITLE_MENU_CANONICAL_ID = 2593
TITLE_MENU_SOURCE_SIZE = 0xFF80
TITLE_MENU_SOURCE_SHA256 = (
    "4aec6a89bcf155d19a11b76df7d4f73139b840bf1e04482a4328ae80b3428c2b"
)
TITLE_MENU_RESULT_SIZE = 0xFEF4
TITLE_MENU_RESULT_SHA256 = (
    "26b7d6103cda568cb9f4493b6c6e54b3afa0bcc529e45696fcc691b620d5e938"
)
TITLE_MENU_SECTOR_BUDGET = 0x10000

ARCHIVE_ENTRY_COUNT = 8
ARCHIVE_SOURCE_OFFSETS = (
    0x0028,
    0x00EC,
    0x7160,
    0x85A8,
    0x8CC8,
    0xF9F8,
    0xFA7C,
    0xFCF4,
)
ARCHIVE_RESULT_OFFSETS = (
    0x0028,
    0x00EC,
    0x70D4,
    0x851C,
    0x8C3C,
    0xF96C,
    0xF9F0,
    0xFC68,
)
TITLE_IMAGE_ENTRY = 1
TITLE_FONT_ENTRY = 2

TITLE_IMAGES_SIZE = 0xA2FC
TITLE_IMAGES_SHA256 = (
    "69dd2d2f7af2beec83fd00cd9fccd63c6395e48d62f15a1d1f5ee09c48f695d0"
)
RICO_TITLE_IMAGES_SHA256 = (
    "628d7bd785463f2b77d8415b3e49db1029102eca203934a6d5d268c51c0d74b4"
)
TITLE_IMAGES_PACKED_RESULT_SIZE = 0x6FE8
TITLE_IMAGES_PACKED_RESULT_SHA256 = (
    "ab29f2e297035ecb971d8f918dcbe7cb3dd556caaed0ca761d56be58431c085a"
)
TITLE_FONT_SIZE = 0x5C47
TITLE_FONT_SHA256 = (
    "2707fb2fcfc4660436328d3bdc930a32a70751a7dbf72d005a718ed189732898"
)

IMAGE_BUNDLE_COUNT = 33
STANDARD_FONT_TIM_INDEX = 9
STANDARD_FONT_TIM_POINTER = 0x2FD0
STANDARD_FONT_CLUT = (304, 509)
STANDARD_FONT_IMAGE = (479, 120, 32, 112)

TITLE_LABEL_TIM_INDEX = 16
TITLE_LABEL_TIM_POINTER = 0x5498
TITLE_LABEL_TIM_END = 0x6180
TITLE_LABEL_CLUT_OFFSET = 0x54A0
TITLE_LABEL_CLUT_SHA256 = (
    "49c32cb719213c76f61e673d6d99a39cb591bb8eb2e2f0c22fa4248c763f451c"
)
TITLE_LABEL_IMAGE_HEADER_OFFSET = 0x54CC
TITLE_LABEL_PIXELS_OFFSET = 0x54D8
TITLE_LABEL_IMAGE = (448, 148, 30, 54)
TITLE_LABEL_ROW_BYTES = 60
NEW_GAME_X = 0
NEW_GAME_Y = 18
NEW_GAME_WIDTH = 44
NEW_GAME_HEIGHT = 9
NEW_GAME_SOURCE_PIXELS_SHA256 = (
    "8d20fd484f2243a60a4a3cf6db8008d9d6f74acf3bbbbc25cc6ec31b433e5783"
)
RICO_TITLE_PIXELS_SHA256 = (
    "acc0448b77d4f54c910771edce4488aedc2decedcb3571f00fa46e4bc278729e"
)

FONT_GLYPH_COUNT = 385
NEW_GAME_GLYPH = 0x123
CONTINUE_GLYPH = 0x124
SOUND_GLYPH = 0x125
APOSTROPHE_GLYPH = 0x93
TITLE_LABEL_RECORDS = {
    NEW_GAME_GLYPH: bytes.fromhex(
        "01 00 00 00 00 00 A6 00 2C 00 09 00 A5 FF 0A 00 "
        "04 00 00 00 00 00 10 01 FD 01 C0 01 94 00 00 00"
    ),
    CONTINUE_GLYPH: bytes.fromhex(
        "01 00 00 00 2C 00 A6 00 29 00 09 00 AA FF 1D 00 "
        "04 00 00 00 00 00 10 01 FD 01 C0 01 94 00 00 00"
    ),
    SOUND_GLYPH: bytes.fromhex(
        "01 00 00 00 00 00 C1 00 1B 00 09 00 AB FF 31 00 "
        "04 00 00 00 00 00 10 01 FD 01 C0 01 94 00 00 00"
    ),
}
APOSTROPHE_RECORD = bytes.fromhex(
    "01 00 00 00 DC 00 B0 00 08 00 08 00 00 00 00 00 "
    "04 00 00 00 00 00 30 01 FD 01 DF 01 78 00 00 00"
)

RICO_TITLE_TEXT = "Rico's Arc"
RICO_TITLE_SOURCE_WIDTH = 57


class RicoTitleError(RuntimeError):
    """Raised when the retail menu source or deterministic output drifts."""


def _sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


def _archive_entries(data: bytes) -> tuple[tuple[int, ...], tuple[bytes, ...]]:
    if len(data) < 4 + ARCHIVE_ENTRY_COUNT * 4:
        raise RicoTitleError("Title-menu archive is shorter than its header")
    count = struct.unpack_from("<I", data, 0)[0]
    if count != ARCHIVE_ENTRY_COUNT:
        raise RicoTitleError(f"Title-menu archive has {count} entries")
    offsets = struct.unpack_from(f"<{count}I", data, 4)
    if offsets != ARCHIVE_SOURCE_OFFSETS:
        raise RicoTitleError("Title-menu archive offsets changed")
    if offsets[0] < 4 + count * 4 or any(offset % 4 for offset in offsets):
        raise RicoTitleError("Title-menu archive offsets are invalid")
    if any(left >= right for left, right in zip(offsets, offsets[1:])):
        raise RicoTitleError("Title-menu archive offsets are not ordered")
    if offsets[-1] >= len(data):
        raise RicoTitleError("Title-menu archive ends outside its source")
    entries = tuple(
        data[start : offsets[index + 1] if index + 1 < count else len(data)]
        for index, start in enumerate(offsets)
    )
    return offsets, entries


def _decode_entry(
    entry: bytes,
    *,
    expected_size: int,
    expected_sha256: str,
    label: str,
) -> bytes:
    if len(entry) < 4:
        raise RicoTitleError(f"{label} is shorter than its LZSS header")
    declared_size = struct.unpack_from("<I", entry, 0)[0]
    if declared_size != expected_size:
        raise RicoTitleError(
            f"{label} declares {declared_size} bytes, expected {expected_size}"
        )
    decoded = decompress_lzss(entry + bytes(16), expected_size).data
    actual_sha256 = _sha256(decoded)
    if actual_sha256 != expected_sha256:
        raise RicoTitleError(f"{label} decoded hash changed: {actual_sha256}")
    return decoded


def _decode_complete_groups(stream: bytes) -> tuple[bytes, int]:
    """Model the retail decoder, which always executes all eight commands."""

    if len(stream) < 4:
        raise RicoTitleError("LZSS stream is shorter than its size header")
    declared_size = struct.unpack_from("<I", stream, 0)[0]
    position = 4
    output = bytearray()
    while len(output) < declared_size:
        if position >= len(stream):
            raise RicoTitleError("LZSS stream ends before a control group")
        control = stream[position]
        position += 1
        for bit in range(8):
            if control & (1 << bit):
                if position + 2 > len(stream):
                    raise RicoTitleError("LZSS stream ends inside a backreference")
                low = stream[position]
                high = stream[position + 1]
                position += 2
                distance = low | ((high & 0x0F) << 8)
                length = (high >> 4) + 3
                if not 1 <= distance <= len(output):
                    raise RicoTitleError("LZSS stream has an invalid distance")
                for _ in range(length):
                    output.append(output[-distance])
            else:
                if position >= len(stream):
                    raise RicoTitleError("LZSS stream ends inside a literal")
                output.append(stream[position])
                position += 1
        if len(output) > declared_size:
            raise RicoTitleError("LZSS command group overruns its output")
    return bytes(output), position


def _compress_exact_complete_groups(data: bytes) -> bytes:
    """Compact exact-size data and finish on an eight-command boundary."""

    if not data:
        return bytes(4)
    packed = compress_lzss(data)
    position = 4
    output_size = 0
    commands: list[tuple[bool, bytes, int]] = []
    while output_size < len(data):
        if position >= len(packed):
            raise RicoTitleError("Compact LZSS stream lost a control group")
        control = packed[position]
        position += 1
        for bit in range(8):
            if output_size >= len(data):
                break
            if control & (1 << bit):
                if position + 2 > len(packed):
                    raise RicoTitleError("Compact LZSS backreference is truncated")
                payload = packed[position : position + 2]
                position += 2
                command_size = (payload[1] >> 4) + 3
                commands.append((True, payload, command_size))
            else:
                if position >= len(packed):
                    raise RicoTitleError("Compact LZSS literal is truncated")
                payload = packed[position : position + 1]
                position += 1
                command_size = 1
                commands.append((False, payload, command_size))
            output_size += command_size
            if output_size > len(data):
                raise RicoTitleError("Compact LZSS command exceeds its source")

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
        distance_low = payload[0]
        distance_high = payload[1] & 0x0F
        lengths = [3] * split_count + [command_size - 3 * split_count]
        replacements = [
            (
                True,
                bytes((distance_low, distance_high | ((length - 3) << 4))),
                length,
            )
            for length in lengths
        ]
        commands[command_index : command_index + 1] = replacements
        missing_commands -= split_count
        command_index += len(replacements)
    if missing_commands or len(commands) % 8:
        raise RicoTitleError(
            "Compact LZSS stream cannot end without decoded padding"
        )

    result = bytearray(struct.pack("<I", len(data)))
    for group_start in range(0, len(commands), 8):
        group = commands[group_start : group_start + 8]
        result.append(
            sum(
                (1 << bit) if is_reference else 0
                for bit, (is_reference, _, _) in enumerate(group)
            )
        )
        for _, payload, _ in group:
            result.extend(payload)
    result.extend(bytes((-len(result)) % 4))
    packed_result = bytes(result)
    decoded, consumed = _decode_complete_groups(packed_result)
    if decoded != data or consumed > len(packed_result):
        raise RicoTitleError("Exact LZSS stream failed retail decoding")
    return packed_result


def _font_records(font: bytes) -> tuple[bytes, ...]:
    if len(font) < 4:
        raise RicoTitleError("Title font is shorter than its header")
    count = struct.unpack_from("<I", font, 0)[0]
    if count != FONT_GLYPH_COUNT or 4 + count * 2 > len(font):
        raise RicoTitleError(f"Title font has an invalid glyph count {count}")
    offsets = struct.unpack_from(f"<{count}H", font, 4)
    if offsets[0] != 4 + count * 2 or any(
        left >= right for left, right in zip(offsets, offsets[1:])
    ):
        raise RicoTitleError("Title-font offsets are invalid")
    if offsets[-1] >= len(font):
        raise RicoTitleError("Title font ends before its final glyph")
    records = tuple(
        font[start : offsets[index + 1] if index + 1 < count else len(font)]
        for index, start in enumerate(offsets)
    )
    for glyph, expected in TITLE_LABEL_RECORDS.items():
        if records[glyph] != expected:
            raise RicoTitleError(f"Retail title-label record 0x{glyph:X} changed")
    if records[APOSTROPHE_GLYPH] != APOSTROPHE_RECORD:
        raise RicoTitleError("Retail apostrophe glyph changed")
    return records


def _tim4_pixels(
    image_bundle: bytes,
    *,
    pointer: int,
    expected_clut: tuple[int, int],
    expected_image: tuple[int, int, int, int],
) -> tuple[int, int, int, int, bytes]:
    if pointer + 8 > len(image_bundle):
        raise RicoTitleError("Title TIM header lies outside its image bundle")
    if struct.unpack_from("<II", image_bundle, pointer) != (0x10, 0x08):
        raise RicoTitleError("Title TIM is not a checked 4-bpp CLUT image")
    cursor = pointer + 8
    if cursor + 12 > len(image_bundle):
        raise RicoTitleError("Title TIM CLUT header is truncated")
    clut_size, clut_x, clut_y, clut_width, clut_height = struct.unpack_from(
        "<I4H", image_bundle, cursor
    )
    if (
        clut_size != 44
        or (clut_x, clut_y) != expected_clut
        or (clut_width, clut_height) != (16, 1)
        or cursor + clut_size > len(image_bundle)
    ):
        raise RicoTitleError("Title TIM CLUT changed")
    cursor += clut_size
    if cursor + 12 > len(image_bundle):
        raise RicoTitleError("Title TIM image header is truncated")
    block_size, image_x, image_y, width_words, height = struct.unpack_from(
        "<I4H", image_bundle, cursor
    )
    pixel_size = width_words * height * 2
    if (
        (image_x, image_y, width_words, height) != expected_image
        or block_size != 12 + pixel_size
        or cursor + block_size > len(image_bundle)
    ):
        raise RicoTitleError("Title TIM image layout changed")
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
    raise RicoTitleError(f"Rico title contains unsupported character {character!r}")


def _render_rico_title(image_bundle: bytes, records: tuple[bytes, ...]) -> bytes:
    image_x, image_y, width_words, image_height, pixels = _tim4_pixels(
        image_bundle,
        pointer=STANDARD_FONT_TIM_POINTER,
        expected_clut=STANDARD_FONT_CLUT,
        expected_image=STANDARD_FONT_IMAGE,
    )

    def source_pixel(x: int, y: int) -> int:
        if not (0 <= x < width_words * 4 and 0 <= y < image_height):
            raise RicoTitleError("Title glyph lies outside its standard-font TIM")
        pixel_index = y * width_words * 4 + x
        packed = pixels[pixel_index // 2]
        return (packed >> 4) & 0x0F if pixel_index & 1 else packed & 0x0F

    def glyph_canvas(character: str) -> list[list[int]]:
        if character == " ":
            return [[0] * 3 for _ in range(NEW_GAME_HEIGHT)]
        glyph_index = _source_glyph_index(character)
        record = records[glyph_index]
        if len(record) != 32 or struct.unpack_from("<HH", record, 0) != (1, 0):
            raise RicoTitleError(
                f"Title source glyph {character!r} is not one polygon"
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
            or offset_y + height > NEW_GAME_HEIGHT
        ):
            raise RicoTitleError(f"Title source glyph {character!r} changed")
        page_x = (tpage_x // 64) * 256
        page_y = (tpage_y // 256) * 256
        local_x = page_x + texture_u - image_x * 4
        local_y = page_y + texture_v - image_y
        canvas = [
            [0] * max(1, offset_x + width) for _ in range(NEW_GAME_HEIGHT)
        ]
        for y in range(height):
            for x in range(width):
                canvas[offset_y + y][offset_x + x] = source_pixel(
                    local_x + x, local_y + y
                )
        occupied_x = [
            x for row in canvas for x, value in enumerate(row) if value != 0
        ]
        if not occupied_x:
            raise RicoTitleError(f"Title source glyph {character!r} is empty")
        left, right = min(occupied_x), max(occupied_x)
        return [row[left : right + 1] for row in canvas]

    glyphs = [glyph_canvas(character) for character in RICO_TITLE_TEXT]
    source_width = sum(len(glyph[0]) for glyph in glyphs) + len(glyphs) - 1
    if source_width != RICO_TITLE_SOURCE_WIDTH:
        raise RicoTitleError(f"Rico title rendered at unexpected width {source_width}")
    source = [[0] * source_width for _ in range(NEW_GAME_HEIGHT)]
    cursor = 0
    for glyph in glyphs:
        for y, row in enumerate(glyph):
            source[y][cursor : cursor + len(row)] = row
        cursor += len(glyph[0]) + 1
    scaled = [
        [row[x * source_width // NEW_GAME_WIDTH] for x in range(NEW_GAME_WIDTH)]
        for row in source
    ]
    packed = bytes(
        value
        for row in scaled
        for x in range(0, NEW_GAME_WIDTH, 2)
        for value in (row[x] | (row[x + 1] << 4),)
    )
    if _sha256(packed) != RICO_TITLE_PIXELS_SHA256:
        raise RicoTitleError("Rendered Rico title pixels changed")
    return packed


def _label_rectangle(image_bundle: bytes | bytearray) -> bytes:
    row_size = NEW_GAME_WIDTH // 2
    return b"".join(
        image_bundle[
            TITLE_LABEL_PIXELS_OFFSET
            + (NEW_GAME_Y + y) * TITLE_LABEL_ROW_BYTES
            + NEW_GAME_X // 2 :
            TITLE_LABEL_PIXELS_OFFSET
            + (NEW_GAME_Y + y) * TITLE_LABEL_ROW_BYTES
            + NEW_GAME_X // 2
            + row_size
        ]
        for y in range(NEW_GAME_HEIGHT)
    )


def _install_label(image_bundle: bytes, packed_label: bytes) -> bytes:
    count = struct.unpack_from("<I", image_bundle, 0)[0]
    if count != IMAGE_BUNDLE_COUNT or 4 + count * 4 > len(image_bundle):
        raise RicoTitleError("Title image bundle has an invalid image count")
    pointers = struct.unpack_from(f"<{count}I", image_bundle, 4)
    if (
        pointers[STANDARD_FONT_TIM_INDEX] != STANDARD_FONT_TIM_POINTER
        or pointers[TITLE_LABEL_TIM_INDEX] != TITLE_LABEL_TIM_POINTER
        or pointers[TITLE_LABEL_TIM_INDEX + 1] != TITLE_LABEL_TIM_END
    ):
        raise RicoTitleError("Title image pointers changed")
    _tim4_pixels(
        image_bundle,
        pointer=TITLE_LABEL_TIM_POINTER,
        expected_clut=(272, 509),
        expected_image=TITLE_LABEL_IMAGE,
    )
    if _sha256(
        image_bundle[TITLE_LABEL_CLUT_OFFSET:TITLE_LABEL_IMAGE_HEADER_OFFSET]
    ) != TITLE_LABEL_CLUT_SHA256:
        raise RicoTitleError("Retail title-label CLUT changed")
    if _sha256(_label_rectangle(image_bundle)) != NEW_GAME_SOURCE_PIXELS_SHA256:
        raise RicoTitleError("Retail New Game pixels changed")
    expected_label_size = NEW_GAME_WIDTH * NEW_GAME_HEIGHT // 2
    if len(packed_label) != expected_label_size:
        raise RicoTitleError("Rendered Rico title has the wrong packed size")

    patched = bytearray(image_bundle)
    row_size = NEW_GAME_WIDTH // 2
    for y in range(NEW_GAME_HEIGHT):
        destination = (
            TITLE_LABEL_PIXELS_OFFSET
            + (NEW_GAME_Y + y) * TITLE_LABEL_ROW_BYTES
            + NEW_GAME_X // 2
        )
        source = y * row_size
        patched[destination : destination + row_size] = packed_label[
            source : source + row_size
        ]
    if _sha256(_label_rectangle(patched)) != RICO_TITLE_PIXELS_SHA256:
        raise RicoTitleError("Installed Rico title pixels changed")
    allowed = {
        TITLE_LABEL_PIXELS_OFFSET
        + (NEW_GAME_Y + y) * TITLE_LABEL_ROW_BYTES
        + x
        for y in range(NEW_GAME_HEIGHT)
        for x in range(row_size)
    }
    if any(
        before != after and index not in allowed
        for index, (before, after) in enumerate(zip(image_bundle, patched, strict=True))
    ):
        raise RicoTitleError("Title image changed outside the New Game rectangle")
    result = bytes(patched)
    if _sha256(result) != RICO_TITLE_IMAGES_SHA256:
        raise RicoTitleError("Patched title-image bundle changed")
    return result


def _rebuild_archive(
    source: bytes,
    entries: tuple[bytes, ...],
) -> bytes:
    result = bytearray(source[: ARCHIVE_SOURCE_OFFSETS[0]])
    rebuilt_offsets: list[int] = []
    for entry in entries:
        result.extend(bytes((-len(result)) % 4))
        rebuilt_offsets.append(len(result))
        result.extend(entry)
    if tuple(rebuilt_offsets) != ARCHIVE_RESULT_OFFSETS:
        raise RicoTitleError(
            f"Rebuilt title archive offsets changed: {tuple(rebuilt_offsets)}"
        )
    struct.pack_into(
        f"<{len(rebuilt_offsets)}I", result, 4, *rebuilt_offsets
    )
    return bytes(result)


def patch_rico_title_menu(source: bytes) -> bytes:
    """Change only retail ``New Game`` to ``Rico's Arc`` in canonical 2593."""

    if (
        len(source) != TITLE_MENU_SOURCE_SIZE
        or _sha256(source) != TITLE_MENU_SOURCE_SHA256
    ):
        raise RicoTitleError(
            "Rico title requires clean USA canonical menu resource 2593"
        )
    _offsets, original_entries = _archive_entries(source)
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
    records = _font_records(font)
    packed_label = _render_rico_title(images, records)
    patched_images = _install_label(images, packed_label)
    packed_images = _compress_exact_complete_groups(patched_images)
    if (
        len(packed_images) != TITLE_IMAGES_PACKED_RESULT_SIZE
        or _sha256(packed_images) != TITLE_IMAGES_PACKED_RESULT_SHA256
    ):
        raise RicoTitleError("Repacked title-image entry changed")

    entries = list(original_entries)
    entries[TITLE_IMAGE_ENTRY] = packed_images
    for index, (before, after) in enumerate(
        zip(original_entries, entries, strict=True)
    ):
        if index != TITLE_IMAGE_ENTRY and before != after:
            raise RicoTitleError(f"Unrelated title archive entry {index} changed")
    result = _rebuild_archive(source, tuple(entries))
    if len(result) > TITLE_MENU_SECTOR_BUDGET:
        raise RicoTitleError("Rico title exceeds canonical 2593's sector budget")
    if (
        len(result) != TITLE_MENU_RESULT_SIZE
        or _sha256(result) != TITLE_MENU_RESULT_SHA256
    ):
        raise RicoTitleError(
            f"Rico title output changed: {len(result)} bytes, SHA-256 {_sha256(result)}"
        )
    return result


__all__ = [
    "RICO_TITLE_TEXT",
    "RicoTitleError",
    "TITLE_MENU_CANONICAL_ID",
    "TITLE_MENU_RESULT_SHA256",
    "TITLE_MENU_RESULT_SIZE",
    "TITLE_MENU_SOURCE_SHA256",
    "TITLE_MENU_SOURCE_SIZE",
    "patch_rico_title_menu",
]
