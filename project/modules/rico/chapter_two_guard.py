"""Install the checked Kislev guard in the opening infirmary's unused bank.

Field 213 mixes external graphics banks with a compact local sprite list.
The local list currently belongs to bank 6, not bank 0. Turning bank 0 into
a local upload therefore requires inserting its atlas before the old list.
The separate field graphics also upload the old bank-0 cell. Install the
matching graphics replacement as well, so either loader order draws the guard.
"""
from __future__ import annotations

import hashlib
import struct

from modules.mass_driver import build as native
from modules.rico.chapter_two_resources import DONOR_RESOURCE_IDENTITIES, ChapterTwoResourceError
from shared.tools.xgfield import parse_field, build_field_preserving

GUARD_ENTITY = 10
GUARD_BANK = 0
GUARD_DONOR_FIELD = 230
GUARD_SOURCE_IDENTITY = (63620, "87707b40154d04bea8733038ac0130331697d3155ed13f3a431bf1ce0c079318")
GUARD_ACTOR_IDENTITY = (3236, "30ee150e0d148c8d0ea8fecd79320e578f0b19f96d60709649d4c5e53b21fc1f")
GUARD_SPRITE_IDENTITY = (22796, "ff4f4340596a85683d83aa83c201f446ee132ac723637de83b93408cce1b1a41")
GUARD_VRAM_RECT = (832, 0, 64, 178)
GUARD_ORIGINAL_GRAPHICS_RECT = (832, 0, 64, 134)
GUARD_GRAPHICS_BLOCK_START = 217088
GUARD_GRAPHICS_BLOCK_END = 237568


def _identity(data: bytes) -> tuple[int, str]:
    return len(data), hashlib.sha256(data).hexdigest()


def install_intake_guard(intake: bytes, donor: bytes) -> bytes:
    if _identity(intake) != DONOR_RESOURCE_IDENTITIES[1032]:
        raise ChapterTwoResourceError("Guard transplant requires retail infirmary 213")
    if _identity(donor) != GUARD_SOURCE_IDENTITY:
        raise ChapterTwoResourceError("Kislev guard donor 230 changed")
    target, source = parse_field(intake), parse_field(donor)
    if struct.unpack_from("<4H", target.header) != (832, 0, 0, 1):
        raise ChapterTwoResourceError("Infirmary bank 0 external mapping changed")
    if struct.unpack_from("<4H", source.header) != (832, 0, 0, 0):
        raise ChapterTwoResourceError("Guard local VRAM cell changed")
    parts = [part.data for part in target.parts]
    actors = list(native._indexed_bundle_entries(parts[3]))
    sprites = list(native._indexed_bundle_entries(parts[4]))
    guard_actor = native._indexed_bundle_entries(source.parts[3].data)[0]
    guard_sprite = native._indexed_bundle_entries(source.parts[4].data)[0]
    if _identity(guard_actor) != GUARD_ACTOR_IDENTITY or _identity(guard_sprite) != GUARD_SPRITE_IDENTITY:
        raise ChapterTwoResourceError("Guard actor or atlas changed")
    sheets = native._indexed_bundle_entries(guard_sprite)
    if len(sheets) != 1 or struct.unpack_from("<2H", sheets[0]) != (64, 178):
        raise ChapterTwoResourceError("Guard atlas exceeds its checked VRAM cell")
    local_banks = [i for i in range(len(actors))
                   if struct.unpack_from("<H", target.header, i * 8 + 6)[0] == 0]
    if local_banks != [6] or len(sprites) != 1:
        raise ChapterTwoResourceError("Infirmary compact local sprite layout changed")
    actors[0] = guard_actor
    parts[3] = native._rebuild_indexed_bundle(parts[3], actors)
    parts[4] = native._rebuild_indexed_bundle(parts[4], [guard_sprite, *sprites])
    header = bytearray(target.header)
    struct.pack_into("<H", header, 6, 0)
    result = build_field_preserving(intake, parts, (3, 4), compact_changed=True,
                                    replacement_header=bytes(header))
    checked = parse_field(result)
    if [part.data for part in checked.parts] != parts or checked.header[6:8] != b"\0\0":
        raise ChapterTwoResourceError("Guard transplant failed packed readback")
    return result


def install_intake_guard_graphics(graphics: bytes, guard_donor: bytes) -> bytes:
    """Replace only the old bank-0 upload with the complete native guard atlas.

    The retail texture stream contains a 64x134 upload at (832,0), even when
    the field header selects a local bank there. Replace that entire block
    with 64x178 guard pixels. Keep all other upload bytes, palettes and their
    order intact. Both the local and external producers then agree, without
    relying on the incompletely documented retail async upload order.
    """
    if _identity(graphics) != DONOR_RESOURCE_IDENTITIES[1033]:
        raise ChapterTwoResourceError("Guard graphics require retail infirmary 213 graphics")
    if _identity(guard_donor) != GUARD_SOURCE_IDENTITY:
        raise ChapterTwoResourceError("Kislev guard donor 230 changed")
    source = parse_field(guard_donor)
    sprite = native._indexed_bundle_entries(source.parts[4].data)[0]
    if _identity(sprite) != GUARD_SPRITE_IDENTITY:
        raise ChapterTwoResourceError("Guard atlas changed")
    sheets = native._indexed_bundle_entries(sprite)
    if len(sheets) != 1 or struct.unpack_from("<2H", sheets[0]) != GUARD_VRAM_RECT[2:]:
        raise ChapterTwoResourceError("Guard atlas dimensions changed")
    pixels = sheets[0][4:]
    x, y, width, height = GUARD_VRAM_RECT
    if len(pixels) != width * height * 2:
        raise ChapterTwoResourceError("Guard atlas pixel extent changed")
    _, rectangles = native._reconstruct_field_graphics_vram(graphics, label="Retail infirmary 213")
    overlapping = [r for r in rectangles
                   if r[0] < x + width and x < r[0] + r[2]
                   and r[1] < y + height and y < r[1] + r[3]]
    if overlapping != [GUARD_ORIGINAL_GRAPHICS_RECT]:
        raise ChapterTwoResourceError("Guard cell overlaps other infirmary graphics")

    start, end = GUARD_GRAPHICS_BLOCK_START, GUARD_GRAPHICS_BLOCK_END
    # Preserve this exact native header, including its duplicate sector count
    # at0x18. A width64/height16 chunk is one 2048-byte payload sector.
    header = bytearray(graphics[start:start + 0x800])
    if (struct.unpack_from("<14H", header) !=
            (0x1200, 0, 320, 0, 512, 0, 64, 16, 1, 9, 32, 0, 9, 0)
            or end - start != 10 * 0x800):
        raise ChapterTwoResourceError("Infirmary bank-0 upload block changed")
    heights = (16,) * (height // 16) + (height % 16,)
    struct.pack_into("<H", header, 0x12, len(heights))
    struct.pack_into("<H", header, 0x18, len(heights))
    header[0x1C:] = bytes(0x800 - 0x1C)
    struct.pack_into(f"<{len(heights)}H", header, 0x1C, *heights)
    upload = bytearray(header)
    consumed = 0
    for chunk_height in heights:
        size = width * chunk_height * 2
        upload.extend(pixels[consumed:consumed + size])
        upload.extend(bytes((-size) % 0x800))
        consumed += size
    result = graphics[:start] + bytes(upload) + graphics[end:]
    vram, installed_rectangles = native._reconstruct_field_graphics_vram(
        result, label="Infirmary 213 with visible guard")
    expected_rectangles = tuple(GUARD_VRAM_RECT if r == GUARD_ORIGINAL_GRAPHICS_RECT else r
                                for r in rectangles)
    installed_pixels = b"".join(vram[((y + row) * 1024 + x) * 2:
                                    ((y + row) * 1024 + x + width) * 2]
                                for row in range(height))
    if installed_rectangles != expected_rectangles or installed_pixels != pixels:
        raise ChapterTwoResourceError("Guard external graphics failed VRAM readback")
    return result
