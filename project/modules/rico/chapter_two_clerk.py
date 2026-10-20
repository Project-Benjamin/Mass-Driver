"""Replace the commons' Hammer clone with the native arena receptionist.

Only existing commons bank2 and its external VRAM cell are changed. Retail
field221 entity7 loads bank4/palette0 and speaks the Receptionist dialogue.
The main-room and preparation-bay Hammer banks are separate resources.
"""
from __future__ import annotations

import hashlib
import struct

from modules.mass_driver import build as native
from modules.rico.chapter_two_resources import DONOR_RESOURCE_IDENTITIES, ChapterTwoResourceError
from shared.tools.xgfield import parse_field, build_field_preserving


CLERK_ENTITY = 10
CLERK_BANK = 2
CLERK_PALETTE = 0
RECEPTIONIST_DONOR_FIELD = 221
RECEPTIONIST_SOURCE_IDENTITY = (76428, "41ad0497f17db2851c0a812ad7e41e9a485e950e21edfd3bf9257fce32ca47ea")
RECEPTIONIST_GRAPHICS_IDENTITY = (260096, "c4069f8803284a2ca114f71fc92bbce81a117613a80bb31f98deeb8a3c6af20f")
RECEPTIONIST_ACTOR_IDENTITY = (4704, "d66b59ae6e5deba9065651c59a0a5cdb999a37d49745cf68d8dfd3ba7d9f73a6")
ORIGINAL_ACTOR_IDENTITY = (5788, "8efce6f4757622e7b060bffc5f5d1a241f457ab527f580f51c8e7f6b19fee910")
RECEPTIONIST_PIXELS_IDENTITY = (21888, "f0538ced1bb3d4c56f9b7ef308ed8b28edb366a1e1347c8731ed047400196b09")
RECEPTIONIST_VRAM_RECT = (384, 256, 64, 171)
CLERK_VRAM_RECT = (960, 0, 64, 228)
CLERK_GRAPHICS_BLOCK_START = 0x1B000
CLERK_GRAPHICS_BLOCK_END = 0x23000


def _identity(data: bytes) -> tuple[int, str]:
    return len(data), hashlib.sha256(data).hexdigest()


def install_commons_clerk(commons: bytes, receptionist_donor: bytes) -> bytes:
    """Install the checked actor in the bank used only by the authored clerk."""
    if _identity(commons) != DONOR_RESOURCE_IDENTITIES[1028]:
        raise ChapterTwoResourceError("Clerk transplant requires retail commons211")
    if _identity(receptionist_donor) != RECEPTIONIST_SOURCE_IDENTITY:
        raise ChapterTwoResourceError("Arena receptionist donor221 changed")
    target, donor = parse_field(commons), parse_field(receptionist_donor)
    if struct.unpack_from("<4H", target.header, CLERK_BANK * 8) != (960, 0, 0, 1):
        raise ChapterTwoResourceError("Commons clerk external VRAM mapping changed")
    if struct.unpack_from("<4H", donor.header, 4 * 8) != (384, 256, 0, 1):
        raise ChapterTwoResourceError("Receptionist donor VRAM mapping changed")
    parts = [part.data for part in target.parts]
    actors = list(native._indexed_bundle_entries(parts[3]))
    actor = native._indexed_bundle_entries(donor.parts[3].data)[4]
    if len(actors) != 5 or _identity(actors[CLERK_BANK]) != ORIGINAL_ACTOR_IDENTITY:
        raise ChapterTwoResourceError("Commons original bank2 identity changed")
    if _identity(actor) != RECEPTIONIST_ACTOR_IDENTITY:
        raise ChapterTwoResourceError("Receptionist actor identity changed")
    actors[CLERK_BANK] = actor
    parts[3] = native._rebuild_indexed_bundle(parts[3], actors)
    result = build_field_preserving(commons, parts, (3,), compact_changed=True)
    checked = parse_field(result)
    if [part.data for part in checked.parts] != parts:
        raise ChapterTwoResourceError("Clerk transplant failed packed readback")
    return result


def install_commons_clerk_graphics(graphics: bytes, receptionist_graphics: bytes) -> bytes:
    """Replace only pixels in the old external bank2 cell; keep its geometry.

    The smaller receptionist sheet occupies171 of228 rows. Zero-fill the
    unused rows, retaining every upload header, sector padding, palette,
    other texture and file length. No local sprite producer is introduced.
    """
    if _identity(graphics) != DONOR_RESOURCE_IDENTITIES[1029]:
        raise ChapterTwoResourceError("Clerk graphics require retail commons211")
    if _identity(receptionist_graphics) != RECEPTIONIST_GRAPHICS_IDENTITY:
        raise ChapterTwoResourceError("Receptionist graphics donor221 changed")
    source_vram, _ = native._reconstruct_field_graphics_vram(
        receptionist_graphics, label="Retail arena receptionist221")
    x, y, width, height = RECEPTIONIST_VRAM_RECT
    pixels = b"".join(source_vram[((y + row) * 1024 + x) * 2:
                                 ((y + row) * 1024 + x + width) * 2]
                      for row in range(height))
    if _identity(pixels) != RECEPTIONIST_PIXELS_IDENTITY:
        raise ChapterTwoResourceError("Receptionist source atlas pixels changed")
    _, rectangles = native._reconstruct_field_graphics_vram(graphics, label="Retail commons211")
    x, y, width, height = CLERK_VRAM_RECT
    overlaps = [r for r in rectangles if r[0] < x + width and x < r[0] + r[2]
                and r[1] < y + height and y < r[1] + r[3]]
    if overlaps != [CLERK_VRAM_RECT]:
        raise ChapterTwoResourceError("Clerk cell overlaps another graphics upload")
    start, end = CLERK_GRAPHICS_BLOCK_START, CLERK_GRAPHICS_BLOCK_END
    if graphics[start:start + 0x1C] != bytes.fromhex(
            "0012000040010000800200004000100001000f00360000000f000000"):
        raise ChapterTwoResourceError("Commons clerk upload header changed")
    heights = struct.unpack_from("<15H", graphics, start + 0x1C)
    if heights != (16,) * 14 + (4,):
        raise ChapterTwoResourceError("Commons clerk upload chunks changed")
    pixels += bytes(width * (height - RECEPTIONIST_VRAM_RECT[3]) * 2)
    result = bytearray(graphics)
    cursor, consumed = start + 0x800, 0
    for chunk_height in heights:
        size = width * chunk_height * 2
        result[cursor:cursor + size] = pixels[consumed:consumed + size]
        consumed += size
        cursor += (size + 0x7FF) & ~0x7FF
    if cursor != end or consumed != len(pixels):
        raise ChapterTwoResourceError("Clerk upload extent changed")
    vram, installed_rectangles = native._reconstruct_field_graphics_vram(
        bytes(result), label="Commons with authentic receptionist")
    installed_pixels = b"".join(vram[((y + row) * 1024 + x) * 2:
                                    ((y + row) * 1024 + x + width) * 2]
                               for row in range(height))
    if installed_rectangles != rectangles or installed_pixels != pixels:
        raise ChapterTwoResourceError("Clerk external upload failed readback")
    return bytes(result)
