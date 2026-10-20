#!/usr/bin/env python3
"""Install field 373's authentic Zeboim station inside the subway train.

Target field 721 already reserves local sprite bank 1 for the now-retired H-10
archive relay.  Its first image at ``x768,y0`` is also the field-dialogue glyph
scratch page: dialogue and shop teardown overwrite it without restoring a
hidden carrier.  The bank's second registered image at ``x832,y0`` is disjoint
from that scratch page and survives menu return.  This transform repacks the
station and model-14 texels into that exact 64-word-by-49-row image instead of
appending an allocator-unsafe MIM rectangle.

The station needs the complete 256-colour field-373 palette.  Field 721's
row-488 CLUT is used only by four model-14 quads.  Their exact 32-by-40 texture
and 28 colours are moved to unused indices in row 489, then row 488 is replaced
with the station palette.  Every other field texture, palette entry, upload
header, chunk table, and padding byte remains unchanged.
"""

from __future__ import annotations

import hashlib
import struct
from typing import Sequence

from modules.mass_driver.tools.xgcloning_warheads import (
    RETAIL_FIELD_673_GRAPHICS_SHA256,
    RETAIL_FIELD_673_GRAPHICS_SIZE,
    ZEBOIM_STATION_ATLAS_TEXTURE_ROWS_SHA256,
    ZEBOIM_STATION_DONOR_GRAPHICS_SHA256,
    ZEBOIM_STATION_DONOR_GRAPHICS_SIZE,
    ZEBOIM_STATION_DONOR_HEADER_SHA256,
    ZEBOIM_STATION_DONOR_HEADER_SIZE,
    ZEBOIM_STATION_DONOR_MODELS_SHA256,
    ZEBOIM_STATION_DONOR_MODELS_SIZE,
    ZEBOIM_STATION_SOURCE_CLUT,
    ZEBOIM_STATION_SOURCE_CLUT_RECT,
    ZEBOIM_STATION_SOURCE_MODEL_INDEX,
    ZEBOIM_STATION_SOURCE_MODEL_SHA256,
    ZEBOIM_STATION_SOURCE_MODEL_SIZE,
    ZEBOIM_STATION_SOURCE_NODE_INDEX,
    ZEBOIM_STATION_SOURCE_TEXTURE_PIXEL_WIDTH,
    ZEBOIM_STATION_SOURCE_TEXTURE_RECT,
    ZEBOIM_STATION_SOURCE_TPAGES,
    ZEBOIM_STATION_TARGET_TEXTURE_PIXEL_WIDTH,
    ZEBOIM_STATION_TARGET_TEXTURE_RECT,
    ZEBOIM_STATION_TEXTURE_ATLAS,
    _graphics_rows,
    _reconstruct_graphics_vram,
)


class SubwayStationError(RuntimeError):
    """Raised when a subway-station source or target fails its audit."""


def _sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


# Input is target 721 immediately after the v94 H-10 transplant.  The actor
# archive remains present but no longer has a visible initializer; only its
# registered sprite-bank allocation is reused.
SUBWAY_STATION_INPUT_HEADER_SIZE = 880
SUBWAY_STATION_INPUT_HEADER_SHA256 = (
    "262b4e4e422cf3eafd44ede619fa6b9fbc4a0d071af030f5b3e777af4f4a375e"
)
SUBWAY_STATION_INPUT_MODELS_SIZE = 49_436
SUBWAY_STATION_INPUT_MODELS_SHA256 = (
    "51193f0e147e06ee137b6678e5b4128cee57d07e0aaa9277ac673b43b5eb4b64"
)
SUBWAY_STATION_INPUT_SPRITES_SIZE = 102_196
SUBWAY_STATION_INPUT_SPRITES_SHA256 = (
    "78ed026e119e44f549899965882a289d7e1553f1e251018abf368c58a4649ef7"
)
SUBWAY_STATION_INPUT_GRAPHICS_SIZE = 319_488
SUBWAY_STATION_INPUT_GRAPHICS_SHA256 = (
    "8fc521c8500270878422a012a074559a822437bcae682e08681b85d2178ed02a"
)

SUBWAY_STATION_SOURCE_MODEL14_SHA256 = (
    "a556eca1a532639646fbcad077ee7da8987059c9492245adaa0ebd77dc0e67e0"
)
SUBWAY_STATION_SOURCE_SPRITE_BANK_SHA256 = (
    "31c608dfc84beae944e0d35713a929702233f6e6adecb91d95593d35a7a66a84"
)
SUBWAY_STATION_SOURCE_SPRITE_IMAGE_SHA256S = (
    "5d9a96545ee731f01e2dff67065dffa68b3a8d7f5ea6180208fedd159f7145e3",
    "24191d2e3fc3a5f6fa1e1cd412132582f94694e52932103a4a838e5afc32ca26",
)

SUBWAY_STATION_TARGET_MODEL_INDEX = 15
SUBWAY_STATION_TARGET_NODE_INDEX = 30
SUBWAY_STATION_NODE_FLAGS = 0x0010
# Align the authentic model's visual centre with the retired H-10 actor and
# entity 14's established interaction point.  Its bottom lands at the train
# floor (y=-88), and its controls face +X toward the party.
SUBWAY_STATION_PLACEMENT = (-1011, 18, 225)
SUBWAY_STATION_Y_ROTATION = 0x0E00
SUBWAY_STATION_VISUAL_CENTER = (-1025, -164, 185)
SUBWAY_STATION_WORLD_BOUNDS = (-1065, -986, -240, -88, 146, 224)
SUBWAY_STATION_CONTROLLER_POSITION = (-1025, 185)

# 8-bpp station atlas in local sprite bank 1's second image (VRAM x832, y0).
# U is measured in pixels, while the image width is 64 words = 128 indexed
# pixels. The 49-row height ends immediately before the post-menu bytes seen
# changing in live VRAM.
SUBWAY_STATION_CARRIER_IMAGE_INDEX = 1
SUBWAY_STATION_CARRIER_VRAM_RECT = (832, 0, 64, 49)
SUBWAY_STATION_DIALOGUE_SCRATCH_VRAM_RECT = (768, 0, 64, 256)
SUBWAY_STATION_TARGET_TPAGES = (0x008D, 0x00AD)
SUBWAY_STATION_TARGET_CLUT = 0x7A00
SUBWAY_STATION_ATLAS_WIDTH = 128
SUBWAY_STATION_ATLAS_HEIGHT = 49

# The shared 80-by-64 atlas used by the cloning-room transplant is too tall
# for bank 1's menu-safe second image. Only its two 50-row islands need to be
# split: no station primitive crosses the five audited horizontal seams. The
# resulting 29 conservative islands retain every sampled retail texel and fit
# beside model 14 inside the exact 128-by-49 indexed-pixel page.
SUBWAY_STATION_TEXTURE_ATLAS = (
    ((16, 205, 18, 17), (32, 16)),
    ((16, 221, 18, 14), (56, 0)),
    ((16, 234, 18, 8), (87, 18)),
    ((16, 241, 18, 6), (32, 33)),
    ((16, 246, 18, 9), (106, 17)),
    ((43, 237, 24, 16), (32, 0)),
    ((35, 205, 7, 17), (78, 18)),
    ((35, 221, 7, 14), (99, 26)),
    ((35, 234, 7, 8), (50, 32)),
    ((35, 241, 7, 6), (78, 35)),
    ((35, 246, 7, 9), (109, 39)),
    ((72, 199, 58, 6), (0, 40)),
    ((43, 220, 16, 16), (50, 16)),
    ((60, 220, 12, 16), (66, 14)),
    ((11, 192, 16, 12), (74, 0)),
    ((32, 192, 18, 10), (90, 0)),
    ((5, 205, 10, 17), (108, 0)),
    ((102, 192, 28, 6), (78, 12)),
    ((72, 192, 29, 6), (58, 42)),
    ((51, 192, 20, 10), (58, 32)),
    ((43, 203, 10, 16), (118, 0)),
    ((62, 203, 7, 16), (85, 26)),
    ((54, 203, 7, 16), (92, 26)),
    ((5, 246, 10, 9), (99, 40)),
    ((103, 219, 16, 5), (109, 26)),
    ((5, 234, 9, 8), (106, 31)),
    ((5, 192, 5, 12), (116, 31)),
    ((0, 243, 4, 13), (121, 31)),
    ((28, 192, 3, 12), (125, 16)),
)
SUBWAY_STATION_ATLAS_OCCUPIED_TEXELS = 4_388
SUBWAY_STATION_ATLAS_TEXTURE_ROWS_SHA256 = (
    "f7ea5f20e563ae4e733cb0897958e0f7aca3c526bb0bc91691df68bb233e2428"
)

# Model 14 alone used row 488 and its 32x40 indexed texture.  These row-489
# entries are unused by every active target-721 static model.  Relocating its
# 28 colours here frees the complete row-488 CLUT without changing appearance.
SUBWAY_STATION_MODEL14_SOURCE_TEXTURE_RECT = (704, 128, 16, 40)
SUBWAY_STATION_MODEL14_SOURCE_UV_ORIGIN = (0, 128)
SUBWAY_STATION_MODEL14_TARGET_UV_ORIGIN = (0, 0)
SUBWAY_STATION_MODEL14_SOURCE_CLUT = 0x7A00
SUBWAY_STATION_MODEL14_TARGET_CLUT = 0x7A40
SUBWAY_STATION_MODEL14_SOURCE_TPAGE = 0x008B
SUBWAY_STATION_MODEL14_TARGET_TPAGE = 0x008D
SUBWAY_STATION_MODEL14_PALETTE_REMAP = (
    17,
    27,
    28,
    29,
    30,
    31,
    45,
    46,
    47,
    58,
    59,
    60,
    61,
    62,
    63,
    95,
    98,
    107,
    108,
    109,
    110,
    111,
    167,
    192,
    195,
    196,
    197,
    198,
)
SUBWAY_STATION_MODEL14_TEXTURE_SHA256 = (
    "3ef67781b3facb3c60b18334efe7ce9b9bd2d9d7c110b1d143c47cc5d84a90fc"
)
SUBWAY_STATION_MODEL14_RELOCATED_TEXTURE_SHA256 = (
    "1da4a300c865c708cbb405da3dd8dd1d149a748cdf2c434c38d7b5cbe991d3d3"
)
SUBWAY_STATION_ROW488_SHA256 = (
    "2e73624e48cd4bd3a219097e920176c6ac9fb55a4f3355b03f228d92675f2e58"
)
SUBWAY_STATION_ROW489_SHA256 = (
    "ab783eafcddfacbb84cca6c6cb813e672ee054b0e72ecd5851644cd5504adf75"
)
SUBWAY_STATION_RELOCATED_ROW489_SHA256 = (
    "41f3319a7a8a6759db38b86ad39856ba0a360a837f8e68dfb26316e19027af1a"
)

# Upload zero is (0,481,256,12), split into three exact four-row chunks.
# Row 488 is the fourth row of chunk two; row 489 starts chunk three.
SUBWAY_STATION_GRAPHICS_ROW488_OFFSET = 0x1600
SUBWAY_STATION_GRAPHICS_ROW489_OFFSET = 0x1800

SUBWAY_STATION_RELOCATED_MODEL_SHA256 = (
    "fdd32a5e2fdd4366fa27e68128ca0efe8ad2e8ec533c11c03fcd2cb9fed4a1d7"
)
SUBWAY_STATION_PATCHED_MODEL14_SHA256 = (
    "28d84618d3cb159cb417a89be93ab3b4d555992aa34071d55415960be6ccb730"
)
SUBWAY_STATION_CARRIER_IMAGE_SHA256 = (
    "cc4b3df24b36d3a4c44857a2c6d0126b473f3ee9c026b9dfd2af2337cf622413"
)
SUBWAY_STATION_CARRIER_BANK_SHA256 = (
    "c8e221cd04d098a069e0bc5b7f03d7513c41c5c8b2082bc13f5b854870656afc"
)
SUBWAY_STATION_OUTPUT_HEADER_SHA256 = (
    "5d0d23a4cc22c5f1142ce972f1b6a24417f56db7b897167395c08ad7b90652e2"
)
SUBWAY_STATION_OUTPUT_MODELS_SHA256 = (
    "7a3809a4ed6ff8815b64b8e7a69356585b455f845b72c1de9b76aa15f310d7fd"
)
SUBWAY_STATION_OUTPUT_SPRITES_SHA256 = (
    "692c6b9b6e596b1ef84a192ee5bf2f3c8a23b7a39ade106c5f02f4b2a9b7b4cc"
)
SUBWAY_STATION_OUTPUT_GRAPHICS_SHA256 = (
    "d4cf59e33b30df0c03c0c2cd584d942fc6997b7cec2bd79b3d4cbe4fee512aa3"
)


def _indexed_entries(data: bytes, *, label: str) -> tuple[bytes, ...]:
    if len(data) < 8:
        raise SubwayStationError(f"{label} is shorter than its index header")
    count = struct.unpack_from("<I", data)[0]
    table_end = 4 + count * 4
    if count == 0 or table_end > len(data):
        raise SubwayStationError(f"{label} has an invalid entry count")
    offsets = struct.unpack_from(f"<{count}I", data, 4)
    if offsets[0] < table_end or any(
        left >= right for left, right in zip(offsets, offsets[1:])
    ):
        raise SubwayStationError(f"{label} has invalid absolute offsets")
    if offsets[-1] >= len(data):
        raise SubwayStationError(f"{label} has an empty final entry")
    ends = (*offsets[1:], len(data))
    return tuple(data[start:end] for start, end in zip(offsets, ends, strict=True))


def _rebuild_indexed(data: bytes, entries: Sequence[bytes], *, label: str) -> bytes:
    old_count = struct.unpack_from("<I", data)[0]
    old_table_end = 4 + old_count * 4
    old_first = struct.unpack_from("<I", data, 4)[0]
    prefix = data[old_table_end:old_first]
    table_end = 4 + len(entries) * 4
    offsets: list[int] = []
    cursor = table_end + len(prefix)
    for entry in entries:
        if not entry:
            raise SubwayStationError(f"{label} contains an empty entry")
        offsets.append(cursor)
        cursor += len(entry)
    return (
        struct.pack("<I", len(entries))
        + struct.pack(f"<{len(entries)}I", *offsets)
        + prefix
        + b"".join(entries)
    )


def _relocate_station_model(model: bytes) -> bytes:
    """Relocate the exact field-373 model to bank 1's menu-safe image."""

    if (
        len(model) != ZEBOIM_STATION_SOURCE_MODEL_SIZE
        or _sha256(model) != ZEBOIM_STATION_SOURCE_MODEL_SHA256
    ):
        raise SubwayStationError("Zeboim station donor model failed its audit")

    output = bytearray(model)
    part_count = struct.unpack_from("<I", output)[0]
    status_mapping = dict(
        zip(
            ZEBOIM_STATION_SOURCE_TPAGES,
            SUBWAY_STATION_TARGET_TPAGES,
            strict=True,
        )
    )
    status_count = 0
    clut_count = 0
    triangles = 0
    quads = 0
    used_islands: set[int] = set()

    def relocate_uvs(offsets: tuple[int, ...]) -> None:
        old_uvs = tuple((output[offset], output[offset + 1]) for offset in offsets)
        matches: list[tuple[int, int, int, int, int]] = []
        for island_index, (source, target) in enumerate(
            SUBWAY_STATION_TEXTURE_ATLAS
        ):
            source_u, source_v, width, height = source
            if all(
                source_u <= u < source_u + width
                and source_v <= v < source_v + height
                for u, v in old_uvs
            ):
                matches.append(
                    (island_index, source_u, source_v, target[0], target[1])
                )
        if len(matches) != 1:
            raise SubwayStationError(
                "Station polygon does not belong to one audited atlas island"
            )
        island_index, source_u, source_v, target_u, target_v = matches[0]
        used_islands.add(island_index)
        for offset, (old_u, old_v) in zip(offsets, old_uvs, strict=True):
            new_u = target_u + old_u - source_u
            new_v = target_v + old_v - source_v
            if not (
                0 <= new_u < SUBWAY_STATION_ATLAS_WIDTH
                and 0 <= new_v < SUBWAY_STATION_ATLAS_HEIGHT
            ):
                raise SubwayStationError(
                    "Station UV exceeds its menu-safe bank-1 atlas"
                )
            output[offset] = new_u
            output[offset + 1] = new_v

    for part_index in range(part_count):
        part_offset = struct.unpack_from("<I", output, 4 + part_index * 4)[0]
        block_count = struct.unpack_from("<I", output, part_offset)[0]
        for block_index in range(block_count):
            block_offset = part_offset + 0x10 + block_index * 0x38
            mesh_block_count = struct.unpack_from("<H", output, block_offset + 6)[0]
            mesh_offset = struct.unpack_from("<I", output, block_offset + 0x10)[0]
            display_offset = struct.unpack_from("<I", output, block_offset + 0x14)[0]
            for _ in range(mesh_block_count):
                polygon_count = struct.unpack_from(
                    "<H", output, part_offset + mesh_offset + 2
                )[0]
                mesh_offset += 4
                while polygon_count:
                    command_offset = part_offset + display_offset
                    command = struct.unpack_from("<I", output, command_offset)[0]
                    operator = command >> 24
                    polygon_operator = operator & ~(0x10 | 0x02 | 0x01)
                    display_offset += 4
                    if operator == 0xC4:
                        old_status = command & 0xFFFF
                        if old_status not in status_mapping:
                            raise SubwayStationError("Station uses an unaudited tpage")
                        struct.pack_into(
                            "<H", output, command_offset, status_mapping[old_status]
                        )
                        status_count += 1
                    elif operator == 0xC8:
                        if command & 0xFFFF != ZEBOIM_STATION_SOURCE_CLUT:
                            raise SubwayStationError("Station uses an unaudited CLUT")
                        struct.pack_into(
                            "<H", output, command_offset, SUBWAY_STATION_TARGET_CLUT
                        )
                        clut_count += 1
                    elif polygon_operator == 0x24:
                        relocate_uvs(
                            (
                                command_offset,
                                part_offset + display_offset,
                                part_offset + display_offset + 2,
                            )
                        )
                        display_offset += 4
                        mesh_offset += 8
                        polygon_count -= 1
                        triangles += 1
                    elif polygon_operator == 0x2C:
                        relocate_uvs(
                            tuple(
                                part_offset + display_offset + delta
                                for delta in (0, 2, 4, 6)
                            )
                        )
                        display_offset += 8
                        mesh_offset += 8
                        polygon_count -= 1
                        quads += 1
                    else:
                        raise SubwayStationError(
                            "Station display list contains an unknown command"
                        )

    if (
        status_count != 2
        or clut_count != 1
        or triangles != 5
        or quads != 80
        or used_islands != set(range(len(SUBWAY_STATION_TEXTURE_ATLAS)))
        or len(output) != ZEBOIM_STATION_SOURCE_MODEL_SIZE
        or _sha256(output) != SUBWAY_STATION_RELOCATED_MODEL_SHA256
    ):
        raise SubwayStationError(
            "Station model relocation is incomplete: "
            f"hash={_sha256(output)}, statuses={status_count}, "
            f"cluts={clut_count}, triangles={triangles}, quads={quads}, "
            f"islands={sorted(used_islands)}"
        )
    return bytes(output)


def _build_station_atlas(
    donor_graphics: bytes,
) -> tuple[bytes, bytes]:
    donor_vram, donor_rectangles = _reconstruct_graphics_vram(
        donor_graphics, label="Retail field 373"
    )
    if donor_rectangles != (
        (0, 480, 256, 7),
        (320, 0, 288, 192),
        (320, 192, 248, 64),
        (576, 192, 24, 64),
    ):
        raise SubwayStationError("Field-373 graphics rectangles changed")
    palette = _graphics_rows(donor_vram, ZEBOIM_STATION_SOURCE_CLUT_RECT)
    source = _graphics_rows(donor_vram, ZEBOIM_STATION_SOURCE_TEXTURE_RECT)
    if len(palette) != 512 or len(source) != 130 * 64:
        raise SubwayStationError("Field-373 station texture extraction failed")

    atlas = bytearray(
        SUBWAY_STATION_ATLAS_WIDTH * SUBWAY_STATION_ATLAS_HEIGHT
    )
    occupied: set[tuple[int, int]] = set()
    for source_rect, target in SUBWAY_STATION_TEXTURE_ATLAS:
        source_u, source_v, width, height = source_rect
        target_u, target_v = target
        if (
            source_u < 0
            or source_v < ZEBOIM_STATION_SOURCE_TEXTURE_RECT[1]
            or source_u + width > ZEBOIM_STATION_SOURCE_TEXTURE_PIXEL_WIDTH
            or source_v + height
            > ZEBOIM_STATION_SOURCE_TEXTURE_RECT[1]
            + ZEBOIM_STATION_SOURCE_TEXTURE_RECT[3]
            or target_u < 0
            or target_v < 0
            or target_u + width > SUBWAY_STATION_ATLAS_WIDTH
            or target_v + height > SUBWAY_STATION_ATLAS_HEIGHT
        ):
            raise SubwayStationError(
                "Subway station atlas contains an out-of-bounds island"
            )
        island = {
            (target_u + x, target_v + y)
            for y in range(height)
            for x in range(width)
        }
        if occupied & island:
            raise SubwayStationError("Station atlas islands overlap")
        occupied.update(island)
        for row in range(height):
            source_start = (
                source_v - ZEBOIM_STATION_SOURCE_TEXTURE_RECT[1] + row
            ) * ZEBOIM_STATION_SOURCE_TEXTURE_PIXEL_WIDTH + source_u
            target_start = (target_v + row) * SUBWAY_STATION_ATLAS_WIDTH + target_u
            atlas[target_start : target_start + width] = source[
                source_start : source_start + width
            ]
    if (
        len(occupied) != SUBWAY_STATION_ATLAS_OCCUPIED_TEXELS
        or max(x for x, _ in occupied) != 127
        or max(y for _, y in occupied) != 48
        or _sha256(atlas) != SUBWAY_STATION_ATLAS_TEXTURE_ROWS_SHA256
    ):
        raise SubwayStationError(
            "Station atlas occupancy changed: "
            f"texels={len(occupied)}, bounds="
            f"({max(x for x, _ in occupied)},{max(y for _, y in occupied)}), "
            f"hash={_sha256(atlas)}"
        )
    return bytes(atlas), palette


def _build_legacy_station_atlas(
    donor_graphics: bytes,
    atlas_backing_graphics: bytes,
) -> tuple[bytes, bytes]:
    """Build the audited 80-by-64 atlas used outside field 721.

    Field 721 now has a separate 128-by-49, menu-safe packing.  Fields 727
    and 363 retain the original 80-by-64 layout, so keep that layout's
    dimensions and backing allocation independent from the subway carrier.
    """

    donor_vram, donor_rectangles = _reconstruct_graphics_vram(
        donor_graphics, label="Retail field 373"
    )
    if donor_rectangles != (
        (0, 480, 256, 7),
        (320, 0, 288, 192),
        (320, 192, 248, 64),
        (576, 192, 24, 64),
    ):
        raise SubwayStationError("Field-373 graphics rectangles changed")
    palette = _graphics_rows(donor_vram, ZEBOIM_STATION_SOURCE_CLUT_RECT)
    source = _graphics_rows(donor_vram, ZEBOIM_STATION_SOURCE_TEXTURE_RECT)
    if len(palette) != 512 or len(source) != 130 * 64:
        raise SubwayStationError("Field-373 station texture extraction failed")

    if (
        len(atlas_backing_graphics) != RETAIL_FIELD_673_GRAPHICS_SIZE
        or _sha256(atlas_backing_graphics) != RETAIL_FIELD_673_GRAPHICS_SHA256
    ):
        raise SubwayStationError("Station atlas backing failed its field-673 audit")
    backing_vram, backing_rectangles = _reconstruct_graphics_vram(
        atlas_backing_graphics,
        label="Retail field 673 atlas backing",
    )
    if backing_rectangles != (
        (0, 480, 256, 9),
        (320, 0, 128, 256),
        (448, 0, 64, 128),
        (512, 192, 40, 64),
    ):
        raise SubwayStationError("Field-673 atlas-backing rectangles changed")

    atlas_width = ZEBOIM_STATION_TARGET_TEXTURE_PIXEL_WIDTH
    atlas_height = ZEBOIM_STATION_TARGET_TEXTURE_RECT[3]
    atlas = bytearray(
        _graphics_rows(backing_vram, ZEBOIM_STATION_TARGET_TEXTURE_RECT)
    )
    occupied: set[tuple[int, int]] = set()
    for source_rect, target in ZEBOIM_STATION_TEXTURE_ATLAS:
        source_u, source_v, width, height = source_rect
        target_u, target_v = target
        if (
            source_u < 0
            or source_v < ZEBOIM_STATION_SOURCE_TEXTURE_RECT[1]
            or source_u + width > ZEBOIM_STATION_SOURCE_TEXTURE_PIXEL_WIDTH
            or source_v + height
            > ZEBOIM_STATION_SOURCE_TEXTURE_RECT[1]
            + ZEBOIM_STATION_SOURCE_TEXTURE_RECT[3]
            or target_u < 0
            or target_v < 0
            or target_u + width > atlas_width
            or target_v + height > atlas_height
        ):
            raise SubwayStationError(
                "Legacy station atlas contains an out-of-bounds island"
            )
        island = {
            (target_u + x, target_v + y)
            for y in range(height)
            for x in range(width)
        }
        if occupied & island:
            raise SubwayStationError("Legacy station atlas islands overlap")
        occupied.update(island)
        for row in range(height):
            source_start = (
                source_v - ZEBOIM_STATION_SOURCE_TEXTURE_RECT[1] + row
            ) * ZEBOIM_STATION_SOURCE_TEXTURE_PIXEL_WIDTH + source_u
            target_start = (target_v + row) * atlas_width + target_u
            atlas[target_start : target_start + width] = source[
                source_start : source_start + width
            ]
    if (
        len(atlas) != atlas_width * atlas_height
        or len(occupied) != 4_288
        or max(x for x, _ in occupied) != 77
        or max(y for _, y in occupied) != 61
        or _sha256(atlas) != ZEBOIM_STATION_ATLAS_TEXTURE_ROWS_SHA256
    ):
        raise SubwayStationError("Legacy station atlas occupancy changed")
    return bytes(atlas), palette


def _patch_model14(model: bytes) -> bytes:
    if _sha256(model) != SUBWAY_STATION_SOURCE_MODEL14_SHA256:
        raise SubwayStationError("Field-721 model 14 changed from its audit")
    output = bytearray(model)
    if (
        output[0x21E4:0x21EC]
        != bytes.fromhex("8B 00 00 C4 00 7A 00 C8")
        or any(
            output[offset : offset + 12]
            != bytes.fromhex("00 00 00 2D 1F A7 00 A7 1F 80 00 80")
            for offset in (0x21EC, 0x21F8, 0x2204, 0x2210)
        )
    ):
        raise SubwayStationError("Model-14 texture state changed from its audit")
    struct.pack_into("<H", output, 0x21E4, SUBWAY_STATION_MODEL14_TARGET_TPAGE)
    struct.pack_into("<H", output, 0x21E8, SUBWAY_STATION_MODEL14_TARGET_CLUT)
    source_u, source_v = SUBWAY_STATION_MODEL14_SOURCE_UV_ORIGIN
    target_u, target_v = SUBWAY_STATION_MODEL14_TARGET_UV_ORIGIN
    for offset in (0x21EC, 0x21F8, 0x2204, 0x2210):
        # Field FT4 records keep all four UV pairs in the eight bytes after
        # the command word; unlike FT3, the command's low halfword is unused.
        for u_offset, v_offset in ((4, 5), (6, 7), (8, 9), (10, 11)):
            output[offset + u_offset] += target_u - source_u
            output[offset + v_offset] += target_v - source_v
    patched = bytes(output)
    if _sha256(patched) != SUBWAY_STATION_PATCHED_MODEL14_SHA256:
        raise SubwayStationError(
            "Patched model 14 is not deterministic: "
            f"hash={_sha256(patched)}"
        )
    return patched


def _patch_sprite_carrier(
    sprites: bytes,
    station_atlas: bytes,
    model14_texture: bytes,
) -> bytes:
    banks = list(_indexed_entries(sprites, label="field-721 sprite archive"))
    if len(banks) != 2 or _sha256(banks[1]) != SUBWAY_STATION_SOURCE_SPRITE_BANK_SHA256:
        raise SubwayStationError("Subway bank-1 carrier changed from its audit")
    images = list(_indexed_entries(banks[1], label="subway bank-1 images"))
    if len(images) != 2:
        raise SubwayStationError("Subway bank-1 image count changed")
    for image, dimensions, digest in zip(
        images,
        ((64, 256), (64, 49)),
        SUBWAY_STATION_SOURCE_SPRITE_IMAGE_SHA256S,
        strict=True,
    ):
        if struct.unpack_from("<HH", image) != dimensions or _sha256(image) != digest:
            raise SubwayStationError("Subway bank-1 image failed its audit")

    carrier = bytearray(images[SUBWAY_STATION_CARRIER_IMAGE_INDEX])
    row_stride = 128
    if len(station_atlas) != row_stride * SUBWAY_STATION_ATLAS_HEIGHT:
        raise SubwayStationError("Subway station atlas has an unexpected size")
    carrier[4:] = station_atlas

    if len(model14_texture) != 32 * 40:
        raise SubwayStationError("Model-14 texture has an unexpected size")
    remap = SUBWAY_STATION_MODEL14_PALETTE_REMAP
    relocated_texture = bytes(remap[index] for index in model14_texture)
    target_u, target_v = SUBWAY_STATION_MODEL14_TARGET_UV_ORIGIN
    model14_rectangle = (target_u, target_v, 32, 40)
    for _source, (atlas_u, atlas_v) in SUBWAY_STATION_TEXTURE_ATLAS:
        atlas_width, atlas_height = _source[2:]
        if (
            target_u < atlas_u + atlas_width
            and atlas_u < target_u + 32
            and target_v < atlas_v + atlas_height
            and atlas_v < target_v + 40
        ):
            raise SubwayStationError(
                "Model-14 texture overlaps the subway station atlas: "
                f"{model14_rectangle}"
            )
    for row in range(40):
        source_start = row * 32
        target_start = 4 + (target_v + row) * row_stride + target_u
        carrier[target_start : target_start + 32] = relocated_texture[
            source_start : source_start + 32
        ]

    if _sha256(relocated_texture) != SUBWAY_STATION_MODEL14_RELOCATED_TEXTURE_SHA256:
        raise SubwayStationError("Model-14 sparse palette remap is not deterministic")
    images[SUBWAY_STATION_CARRIER_IMAGE_INDEX] = bytes(carrier)
    if _sha256(carrier) != SUBWAY_STATION_CARRIER_IMAGE_SHA256:
        raise SubwayStationError(
            "Subway station carrier image is not deterministic: "
            f"hash={_sha256(carrier)}"
        )
    banks[1] = _rebuild_indexed(
        banks[1], images, label="subway station carrier bank"
    )
    if _sha256(banks[1]) != SUBWAY_STATION_CARRIER_BANK_SHA256:
        raise SubwayStationError(
            "Subway station carrier bank is not deterministic: "
            f"hash={_sha256(banks[1])}"
        )
    return _rebuild_indexed(sprites, banks, label="field-721 sprite archive")


def _patch_graphics_palettes(
    graphics: bytes,
    station_palette: bytes,
    model14_texture: bytes,
) -> bytes:
    target_vram, rectangles = _reconstruct_graphics_vram(
        graphics, label="Retail field 721"
    )
    if len(rectangles) != 37 or rectangles[0] != (0, 481, 256, 12):
        raise SubwayStationError("Field-721 native upload inventory changed")
    row488 = _graphics_rows(target_vram, (0, 488, 256, 1))
    row489 = _graphics_rows(target_vram, (0, 489, 256, 1))
    extracted_model14 = _graphics_rows(
        target_vram, SUBWAY_STATION_MODEL14_SOURCE_TEXTURE_RECT
    )
    if (
        _sha256(row488) != SUBWAY_STATION_ROW488_SHA256
        or _sha256(row489) != SUBWAY_STATION_ROW489_SHA256
        or _sha256(extracted_model14) != SUBWAY_STATION_MODEL14_TEXTURE_SHA256
        or extracted_model14 != model14_texture
        or sorted(set(model14_texture)) != list(range(28))
    ):
        raise SubwayStationError("Field-721 retired palette/texture audit failed")

    output_row489 = bytearray(row489)
    for source_index, target_index in enumerate(
        SUBWAY_STATION_MODEL14_PALETTE_REMAP
    ):
        output_row489[target_index * 2 : target_index * 2 + 2] = row488[
            source_index * 2 : source_index * 2 + 2
        ]
    if _sha256(output_row489) != SUBWAY_STATION_RELOCATED_ROW489_SHA256:
        raise SubwayStationError("Relocated model-14 palette is not deterministic")

    output = bytearray(graphics)
    if (
        output[
            SUBWAY_STATION_GRAPHICS_ROW488_OFFSET :
            SUBWAY_STATION_GRAPHICS_ROW488_OFFSET + 512
        ]
        != row488
        or output[
            SUBWAY_STATION_GRAPHICS_ROW489_OFFSET :
            SUBWAY_STATION_GRAPHICS_ROW489_OFFSET + 512
        ]
        != row489
    ):
        raise SubwayStationError("Field-721 palette file offsets changed")
    output[
        SUBWAY_STATION_GRAPHICS_ROW488_OFFSET :
        SUBWAY_STATION_GRAPHICS_ROW488_OFFSET + 512
    ] = station_palette
    output[
        SUBWAY_STATION_GRAPHICS_ROW489_OFFSET :
        SUBWAY_STATION_GRAPHICS_ROW489_OFFSET + 512
    ] = output_row489
    return bytes(output)


def patch_subway_zeboim_station(
    header: bytes,
    models: bytes,
    sprites: bytes,
    graphics: bytes,
    donor_header: bytes,
    donor_models: bytes,
    donor_graphics: bytes,
) -> tuple[bytes, bytes, bytes, bytes]:
    """Replace H-10 with the exact field-373 station and texture atlas."""

    if (
        len(header) != SUBWAY_STATION_INPUT_HEADER_SIZE
        or _sha256(header) != SUBWAY_STATION_INPUT_HEADER_SHA256
        or len(models) != SUBWAY_STATION_INPUT_MODELS_SIZE
        or _sha256(models) != SUBWAY_STATION_INPUT_MODELS_SHA256
        or len(sprites) != SUBWAY_STATION_INPUT_SPRITES_SIZE
        or _sha256(sprites) != SUBWAY_STATION_INPUT_SPRITES_SHA256
        or len(graphics) != SUBWAY_STATION_INPUT_GRAPHICS_SIZE
        or _sha256(graphics) != SUBWAY_STATION_INPUT_GRAPHICS_SHA256
    ):
        raise SubwayStationError(
            "Subway station target assets failed their audit: "
            f"header={len(header)}/{_sha256(header)}, "
            f"models={len(models)}/{_sha256(models)}, "
            f"sprites={len(sprites)}/{_sha256(sprites)}, "
            f"graphics={len(graphics)}/{_sha256(graphics)}"
        )
    if (
        len(donor_header) != ZEBOIM_STATION_DONOR_HEADER_SIZE
        or _sha256(donor_header) != ZEBOIM_STATION_DONOR_HEADER_SHA256
        or len(donor_models) != ZEBOIM_STATION_DONOR_MODELS_SIZE
        or _sha256(donor_models) != ZEBOIM_STATION_DONOR_MODELS_SHA256
        or len(donor_graphics) != ZEBOIM_STATION_DONOR_GRAPHICS_SIZE
        or _sha256(donor_graphics) != ZEBOIM_STATION_DONOR_GRAPHICS_SHA256
    ):
        raise SubwayStationError("Zeboim station donor assets failed their audit")

    donor_record = 0x190 + ZEBOIM_STATION_SOURCE_NODE_INDEX * 16
    expected_donor_record = struct.pack(
        "<HhhhhhhH",
        0x0010,
        0,
        0x0200,
        0,
        0,
        0,
        0,
        ZEBOIM_STATION_SOURCE_MODEL_INDEX,
    )
    if donor_header[donor_record : donor_record + 16] != expected_donor_record:
        raise SubwayStationError("Station source node changed from retail")

    donor_entries = _indexed_entries(donor_models, label="field-373 models")
    if len(donor_entries) != 15:
        raise SubwayStationError("Field-373 model inventory changed")
    station_model = _relocate_station_model(
        donor_entries[ZEBOIM_STATION_SOURCE_MODEL_INDEX]
    )
    station_atlas, station_palette = _build_station_atlas(donor_graphics)

    target_entries = list(_indexed_entries(models, label="field-721 models"))
    if len(target_entries) != SUBWAY_STATION_TARGET_MODEL_INDEX:
        raise SubwayStationError("Field-721 model inventory changed")
    target_entries[14] = _patch_model14(target_entries[14])
    target_entries.append(station_model)
    output_models = _rebuild_indexed(
        models, target_entries, label="field-721 station models"
    )

    target_vram, _ = _reconstruct_graphics_vram(graphics, label="Retail field 721")
    model14_texture = _graphics_rows(
        target_vram, SUBWAY_STATION_MODEL14_SOURCE_TEXTURE_RECT
    )
    output_sprites = _patch_sprite_carrier(
        sprites, station_atlas, model14_texture
    )
    output_graphics = _patch_graphics_palettes(
        graphics, station_palette, model14_texture
    )

    if struct.unpack_from("<H", header, 0x18C)[0] != 30:
        raise SubwayStationError("Field-721 static-node count changed")
    output_header = bytearray(header)
    struct.pack_into("<H", output_header, 0x18C, 31)
    output_header.extend(
        struct.pack(
            "<HhhhhhhH",
            SUBWAY_STATION_NODE_FLAGS,
            0,
            SUBWAY_STATION_Y_ROTATION,
            0,
            *SUBWAY_STATION_PLACEMENT,
            SUBWAY_STATION_TARGET_MODEL_INDEX,
        )
    )
    if len(output_header) != 896:
        raise SubwayStationError("Field-721 station node was not appended exactly")
    if (
        _sha256(output_header) != SUBWAY_STATION_OUTPUT_HEADER_SHA256
        or len(output_models) != 51_964
        or _sha256(output_models) != SUBWAY_STATION_OUTPUT_MODELS_SHA256
        or len(output_sprites) != SUBWAY_STATION_INPUT_SPRITES_SIZE
        or _sha256(output_sprites) != SUBWAY_STATION_OUTPUT_SPRITES_SHA256
        or len(output_graphics) != SUBWAY_STATION_INPUT_GRAPHICS_SIZE
        or _sha256(output_graphics) != SUBWAY_STATION_OUTPUT_GRAPHICS_SHA256
    ):
        raise SubwayStationError(
            "Subway station output is not deterministic: "
            f"header={len(output_header)}/{_sha256(output_header)}, "
            f"models={len(output_models)}/{_sha256(output_models)}, "
            f"sprites={len(output_sprites)}/{_sha256(output_sprites)}, "
            f"graphics={len(output_graphics)}/{_sha256(output_graphics)}"
        )
    return (
        bytes(output_header),
        output_models,
        output_sprites,
        output_graphics,
    )


__all__ = [
    "SUBWAY_STATION_ATLAS_HEIGHT",
    "SUBWAY_STATION_ATLAS_OCCUPIED_TEXELS",
    "SUBWAY_STATION_ATLAS_TEXTURE_ROWS_SHA256",
    "SUBWAY_STATION_ATLAS_WIDTH",
    "SUBWAY_STATION_CARRIER_IMAGE_INDEX",
    "SUBWAY_STATION_CARRIER_VRAM_RECT",
    "SUBWAY_STATION_CONTROLLER_POSITION",
    "SUBWAY_STATION_DIALOGUE_SCRATCH_VRAM_RECT",
    "SUBWAY_STATION_MODEL14_PALETTE_REMAP",
    "SUBWAY_STATION_NODE_FLAGS",
    "SUBWAY_STATION_PLACEMENT",
    "SUBWAY_STATION_TARGET_CLUT",
    "SUBWAY_STATION_TARGET_MODEL_INDEX",
    "SUBWAY_STATION_TARGET_NODE_INDEX",
    "SUBWAY_STATION_TARGET_TPAGES",
    "SUBWAY_STATION_TEXTURE_ATLAS",
    "SUBWAY_STATION_VISUAL_CENTER",
    "SUBWAY_STATION_WORLD_BOUNDS",
    "SUBWAY_STATION_Y_ROTATION",
    "SubwayStationError",
    "patch_subway_zeboim_station",
]
