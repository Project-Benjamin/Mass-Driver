#!/usr/bin/env python3
"""Install field 727's authentic Zeboim station in target field 363.

The visible prop is retail field 373 static node 44 / model 7, using the
same lossless 80-by-64 atlas and colours already installed in target field
727.  Field 363 has no local image or sprite archive, and its only bank-zero
carrier owner is repurposed as the station's invisible solid body.  The
station atlas replaces rows 0..63 inside that already-registered x832 block;
no upload is added, resized, or moved.

All nine native palette rows are occupied.  Native model 3 is the only user
of row 485 and samples 28 indices, leaving 228 entries free.  The station uses
192 indices, so its atlas and exact 16-bit colours are losslessly remapped into
those free entries.  Native row 488, its two door models, and the complete
native door texture remain byte-for-byte unchanged; this also preserves any
transition-aperture rendering path that reads the retail door palette without
going through a static-model display list.
"""

from __future__ import annotations

import hashlib
import struct

from modules.mass_driver.tools.xgcloning_warheads import (
    ZEBOIM_STATION_DONOR_GRAPHICS_SHA256,
    ZEBOIM_STATION_DONOR_GRAPHICS_SIZE,
    ZEBOIM_STATION_DONOR_HEADER_SHA256,
    ZEBOIM_STATION_DONOR_HEADER_SIZE,
    ZEBOIM_STATION_DONOR_MODELS_SHA256,
    ZEBOIM_STATION_DONOR_MODELS_SIZE,
    ZEBOIM_STATION_SOURCE_MODEL_INDEX,
    ZEBOIM_STATION_SOURCE_NODE_INDEX,
    _graphics_rows,
    _reconstruct_graphics_vram,
)
from modules.mass_driver.tools.xginner_access_station import (
    INNER_ACCESS_STATION_ATLAS_HEIGHT,
    INNER_ACCESS_STATION_ATLAS_WIDTH,
    INNER_ACCESS_STATION_RELOCATED_MODEL_SHA256,
    INNER_ACCESS_STATION_TARGET_CLUT,
    _relocate_station_model,
)
from modules.mass_driver.tools.xgsubway_station import (
    _build_legacy_station_atlas,
    _indexed_entries,
    _rebuild_indexed,
)


class ServiceJunctionStationError(RuntimeError):
    """Raised when a service-junction station asset fails its exact audit."""


def _sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


SERVICE_JUNCTION_STATION_INPUT_HEADER_SIZE = 800
SERVICE_JUNCTION_STATION_INPUT_HEADER_SHA256 = (
    "9c676de1bb64ea8d316da217723729e87674ab126c45597d28cc94b571b9cef0"
)
SERVICE_JUNCTION_STATION_INPUT_MODELS_SIZE = 7_376
SERVICE_JUNCTION_STATION_INPUT_MODELS_SHA256 = (
    "524e552435be6fd08f4dd7a40dce6b3d24f93cd0bafef08480807b5610101ecc"
)
SERVICE_JUNCTION_STATION_INPUT_GRAPHICS_SIZE = 106_496
SERVICE_JUNCTION_STATION_INPUT_GRAPHICS_SHA256 = (
    "0d561e4850c1ca2205d3e68e7886849412af053816be7c71c76d7f1a6ffc1965"
)

# The authentic station's local control surface faces diagonally.  Yaw 0x0A00
# turns it toward +Z, into the room.  This integral placement grounds its base
# at y=-1 and rounds the visual centre to Elly's captured (0,-189) marker.  Its
# rear seven units embed behind the inert z=-220 wall panel, hiding the former
# doorway without creating a room or transition.
SERVICE_JUNCTION_STATION_PLACEMENT = (-41, 105, -175)
SERVICE_JUNCTION_STATION_Y_ROTATION = 0x0A00
SERVICE_JUNCTION_STATION_SCREEN_NORMAL = (0, 0, 1)
SERVICE_JUNCTION_STATION_VISUAL_CENTER = (0, -189)
SERVICE_JUNCTION_STATION_WORLD_BOUNDS = (
    -39.58578643762691,
    38.903066274079876,
    -153.0,
    -1.0,
    -227.32590180780451,
    -150.25126265847084,
)

SERVICE_JUNCTION_STATION_COLLIDER_ENTITY = 12
SERVICE_JUNCTION_STATION_COLLIDER_POSITION = (
    SERVICE_JUNCTION_STATION_VISUAL_CENTER
)
SERVICE_JUNCTION_STATION_READER_ENTITY = 17
SERVICE_JUNCTION_STATION_READER_POSITION = (0, -150)
SERVICE_JUNCTION_STATION_APPROACH_POSITION = (0, -130)
SERVICE_JUNCTION_STATION_COLLIDER_TRIANGLE = 27
SERVICE_JUNCTION_STATION_READER_TRIANGLE = 19
SERVICE_JUNCTION_STATION_APPROACH_TRIANGLE = 18
SERVICE_JUNCTION_STATION_COLLISION_OPERAND = 0x14
SERVICE_JUNCTION_STATION_READER_HALF_WIDTH = 0x04

SERVICE_JUNCTION_STATION_TARGET_MODEL_INDEX = 10
SERVICE_JUNCTION_STATION_TARGET_NODE_INDEX = 26
SERVICE_JUNCTION_STATION_NODE_FLAGS = 0x0010
SERVICE_JUNCTION_STATION_TARGET_TPAGES = (0x008D, 0x00AD)
SERVICE_JUNCTION_STATION_TARGET_CLUT = 0x7940
SERVICE_JUNCTION_STATION_ATLAS_V = 0
SERVICE_JUNCTION_STATION_TEXTURE_RECT = (832, 0, 40, 64)
SERVICE_JUNCTION_STATION_TARGET_PALETTE_RECT = (0, 485, 256, 1)
SERVICE_JUNCTION_NATIVE_ROW488_RECT = (0, 488, 256, 1)

SERVICE_JUNCTION_STATION_ATLAS_SHA256 = (
    "a6ee4c693587c5f68d8777ef60007ca178a744cad66b9d92ea5a85dfe424f129"
)
SERVICE_JUNCTION_STATION_PALETTE_SHA256 = (
    "7754aac52c72639ecd632cbac7a46c73b0a2873ca1091dcb67325ba2508c1065"
)
SERVICE_JUNCTION_STATION_REMAPPED_ATLAS_SHA256 = (
    "46d09777e7725d9cd1ee78a7dab9b264a1e6c56dda91f0d0a7e8813971a6f84e"
)
SERVICE_JUNCTION_STATION_MODEL_SHA256 = (
    "2466949bd495d1b8c4b150d4cff288e103111c33e63cd90779278482fdcc2041"
)

SERVICE_JUNCTION_NATIVE_ROW485_USED_INDICES = (
    0,
    2,
    3,
    4,
    6,
    7,
    8,
    9,
    11,
    12,
    13,
    14,
    16,
    18,
    19,
    20,
    21,
    25,
    26,
    27,
    29,
    32,
    33,
    34,
    35,
    36,
    37,
    38,
)
SERVICE_JUNCTION_STATION_USED_INDEX_COUNT = 192
SERVICE_JUNCTION_GRAPHICS_ROW485_OFFSET = 0x1200
SERVICE_JUNCTION_GRAPHICS_ROW488_OFFSET = 0x1800

SERVICE_JUNCTION_STATION_OUTPUT_HEADER_SHA256 = (
    "c5dd92f8b149eee4e8287b622d0cd70c730c82eb796115dc0642464d2df6a182"
)
SERVICE_JUNCTION_STATION_OUTPUT_MODELS_SHA256 = (
    "b756da8c20274bf8a6c3c136eafe63c73a830566b0c9aaefb56c5bf7db4f9d20"
)
SERVICE_JUNCTION_STATION_OUTPUT_GRAPHICS_SHA256 = (
    "0f90479813717a6aa250691ec85f02b2c3fb009aed9adbab003212a80bda2561"
)

SERVICE_JUNCTION_GRAPHICS_RECTANGLES = (
    (0, 480, 256, 9),
    (336, 0, 72, 222),
    (832, 0, 64, 144),
    (408, 0, 27, 239),
    (320, 0, 8, 254),
    (328, 0, 8, 250),
    (440, 0, 10, 148),
    (435, 0, 5, 196),
    (450, 94, 5, 54),
)


def _retarget_inner_access_station_model(model: bytes) -> bytes:
    """Move field 727's exact station atlas from V128 to V0 and row 485."""

    if (
        len(model) != 2_524
        or _sha256(model) != INNER_ACCESS_STATION_RELOCATED_MODEL_SHA256
    ):
        raise ServiceJunctionStationError(
            "Field-727 station model changed from its exact audit"
        )
    output = bytearray(model)
    part_count = struct.unpack_from("<I", output)[0]
    status_count = 0
    clut_count = 0
    triangles = 0
    quads = 0
    uv_count = 0

    def relocate_v(offsets: tuple[int, ...]) -> None:
        nonlocal uv_count
        for offset in offsets:
            old_v = output[offset + 1]
            if not 128 <= old_v < 192:
                raise ServiceJunctionStationError(
                    "Field-727 station UV left its audited atlas"
                )
            output[offset + 1] = old_v - 128
            uv_count += 1

    for part_index in range(part_count):
        part_offset = struct.unpack_from("<I", output, 4 + part_index * 4)[0]
        block_count = struct.unpack_from("<I", output, part_offset)[0]
        for block_index in range(block_count):
            block_offset = part_offset + 0x10 + block_index * 0x38
            mesh_block_count = struct.unpack_from("<H", output, block_offset + 6)[0]
            mesh_offset = struct.unpack_from("<I", output, block_offset + 0x10)[0]
            display_offset = struct.unpack_from(
                "<I", output, block_offset + 0x14
            )[0]
            for _mesh_block_index in range(mesh_block_count):
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
                        if command & 0xFFFF not in (
                            SERVICE_JUNCTION_STATION_TARGET_TPAGES
                        ):
                            raise ServiceJunctionStationError(
                                "Field-727 station TPAGE changed"
                            )
                        status_count += 1
                    elif operator == 0xC8:
                        if command & 0xFFFF != INNER_ACCESS_STATION_TARGET_CLUT:
                            raise ServiceJunctionStationError(
                                "Field-727 station CLUT changed"
                            )
                        struct.pack_into(
                            "<H",
                            output,
                            command_offset,
                            SERVICE_JUNCTION_STATION_TARGET_CLUT,
                        )
                        clut_count += 1
                    elif polygon_operator == 0x24:
                        relocate_v(
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
                        relocate_v(
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
                        raise ServiceJunctionStationError(
                            "Field-727 station display list changed"
                        )

    retargeted = bytes(output)
    if (
        status_count != 2
        or clut_count != 1
        or triangles != 5
        or quads != 80
        or uv_count != 335
        or _sha256(retargeted) != SERVICE_JUNCTION_STATION_MODEL_SHA256
    ):
        raise ServiceJunctionStationError(
            "Field-363 station model relocation is not deterministic"
        )
    return retargeted


def _rewrite_registered_vram(graphics: bytes, vram: bytes | bytearray) -> bytes:
    """Rewrite payload rows while preserving every registered MIM descriptor."""

    output = bytearray(graphics)
    cursor = 0
    sector = 0x800
    while cursor < len(output):
        (
            page_x,
            page_y,
            move_x,
            move_y,
            width,
            _nominal_height,
            _unknown,
            chunk_count,
        ) = struct.unpack_from("<8H", output, cursor + 4)
        chunk_heights = struct.unpack_from(
            f"<{chunk_count}H", output, cursor + 0x1C
        )
        cursor += (
            (0x1C + chunk_count * 2 + sector - 1) // sector
        ) * sector
        destination_x = page_x + move_x
        destination_y = page_y + move_y
        row_size = width * 2
        for chunk_height in chunk_heights:
            data_size = row_size * chunk_height
            padded_size = ((data_size + sector - 1) // sector) * sector
            for row in range(chunk_height):
                source_start = (
                    (destination_y + row) * 1024 + destination_x
                ) * 2
                output[
                    cursor + row * row_size : cursor + (row + 1) * row_size
                ] = vram[source_start : source_start + row_size]
            cursor += padded_size
            destination_y += chunk_height
    if cursor != len(output):
        raise ServiceJunctionStationError(
            "Field-363 MIM rewrite ended outside its registered inventory"
        )
    return bytes(output)


def _patch_graphics(
    graphics: bytes,
    station_atlas: bytes,
    station_palette: bytes,
) -> bytes:
    if (
        len(graphics) != SERVICE_JUNCTION_STATION_INPUT_GRAPHICS_SIZE
        or _sha256(graphics) != SERVICE_JUNCTION_STATION_INPUT_GRAPHICS_SHA256
    ):
        raise ServiceJunctionStationError(
            "Service-junction graphics failed their exact input audit"
        )
    if (
        len(station_atlas)
        != INNER_ACCESS_STATION_ATLAS_WIDTH
        * INNER_ACCESS_STATION_ATLAS_HEIGHT
        or _sha256(station_atlas) != SERVICE_JUNCTION_STATION_ATLAS_SHA256
        or len(station_palette) != 512
        or _sha256(station_palette) != SERVICE_JUNCTION_STATION_PALETTE_SHA256
    ):
        raise ServiceJunctionStationError(
            "Existing field-727 station textures changed from their audit"
        )

    old_vram, rectangles = _reconstruct_graphics_vram(
        graphics, label="Retail field 363"
    )
    if rectangles != SERVICE_JUNCTION_GRAPHICS_RECTANGLES:
        raise ServiceJunctionStationError(
            "Field-363 registered MIM inventory changed"
        )
    old_row485 = _graphics_rows(old_vram, (0, 485, 256, 1))
    old_row488 = _graphics_rows(old_vram, (0, 488, 256, 1))
    if (
        graphics[
            SERVICE_JUNCTION_GRAPHICS_ROW485_OFFSET :
            SERVICE_JUNCTION_GRAPHICS_ROW485_OFFSET + 512
        ]
        != old_row485
        or graphics[
            SERVICE_JUNCTION_GRAPHICS_ROW488_OFFSET :
            SERVICE_JUNCTION_GRAPHICS_ROW488_OFFSET + 512
        ]
        != old_row488
    ):
        raise ServiceJunctionStationError(
            "Field-363 palette file offsets changed"
        )

    station_sources = tuple(sorted(set(station_atlas)))
    if (
        len(station_sources) != SERVICE_JUNCTION_STATION_USED_INDEX_COUNT
        or station_sources[0] != 2
        or station_sources[-1] != 255
    ):
        raise ServiceJunctionStationError(
            "Existing station atlas palette-index inventory changed"
        )
    native_used = set(SERVICE_JUNCTION_NATIVE_ROW485_USED_INDICES)
    destinations = tuple(
        index for index in range(256) if index not in native_used
    )[: len(station_sources)]
    if (
        len(destinations) != len(station_sources)
        or set(destinations) & native_used
    ):
        raise ServiceJunctionStationError(
            "Field-363 row-485 palette capacity changed"
        )
    mapping = dict(zip(station_sources, destinations, strict=True))

    output_vram = bytearray(old_vram)
    output_row485 = bytearray(old_row485)
    for source, target in mapping.items():
        output_row485[target * 2 : target * 2 + 2] = station_palette[
            source * 2 : source * 2 + 2
        ]
    row485_start = 485 * 1024 * 2
    output_vram[row485_start : row485_start + 512] = output_row485
    remapped_atlas = bytes(mapping[source] for source in station_atlas)
    if _sha256(remapped_atlas) != (
        SERVICE_JUNCTION_STATION_REMAPPED_ATLAS_SHA256
    ):
        raise ServiceJunctionStationError(
            "Service-junction station atlas remap is not deterministic"
        )

    atlas_x, atlas_y, _atlas_width_words, atlas_height = (
        SERVICE_JUNCTION_STATION_TEXTURE_RECT
    )
    for row in range(atlas_height):
        source_start = row * INNER_ACCESS_STATION_ATLAS_WIDTH
        target_start = ((atlas_y + row) * 1024 + atlas_x) * 2
        output_vram[
            target_start : target_start + INNER_ACCESS_STATION_ATLAS_WIDTH
        ] = remapped_atlas[
            source_start : source_start + INNER_ACCESS_STATION_ATLAS_WIDTH
        ]

    output = _rewrite_registered_vram(graphics, output_vram)
    new_vram, new_rectangles = _reconstruct_graphics_vram(
        output, label="Target-363 authentic station graphics"
    )
    if (
        len(output) != len(graphics)
        or new_rectangles != rectangles
        or (
            SERVICE_JUNCTION_STATION_OUTPUT_GRAPHICS_SHA256
            and _sha256(output)
            != SERVICE_JUNCTION_STATION_OUTPUT_GRAPHICS_SHA256
        )
        or _graphics_rows(
            new_vram, SERVICE_JUNCTION_STATION_TEXTURE_RECT
        )
        != remapped_atlas
        or _graphics_rows(new_vram, SERVICE_JUNCTION_NATIVE_ROW488_RECT)
        != old_row488
        or _graphics_rows(new_vram, (832, 64, 64, 80))
        != _graphics_rows(old_vram, (832, 64, 64, 80))
    ):
        raise ServiceJunctionStationError(
            "Service-junction station graphics are not deterministic"
        )
    new_row485 = _graphics_rows(new_vram, (0, 485, 256, 1))
    if any(
        new_row485[index * 2 : index * 2 + 2]
        != old_row485[index * 2 : index * 2 + 2]
        for index in native_used
    ):
        raise ServiceJunctionStationError(
            "Service-junction station changed a native row-485 colour"
        )
    for source, target in mapping.items():
        if (
            new_row485[target * 2 : target * 2 + 2]
            != station_palette[source * 2 : source * 2 + 2]
        ):
            raise ServiceJunctionStationError(
                "Service-junction station colour remap is not lossless"
            )
    return output


def patch_service_junction_zeboim_station(
    header: bytes,
    models: bytes,
    graphics: bytes,
    donor_header: bytes,
    donor_models: bytes,
    donor_graphics: bytes,
    atlas_backing_graphics: bytes,
) -> tuple[bytes, bytes, bytes]:
    """Place the already-used authentic station at Elly's field-363 marker."""

    if (
        len(header) != SERVICE_JUNCTION_STATION_INPUT_HEADER_SIZE
        or _sha256(header) != SERVICE_JUNCTION_STATION_INPUT_HEADER_SHA256
        or len(models) != SERVICE_JUNCTION_STATION_INPUT_MODELS_SIZE
        or _sha256(models) != SERVICE_JUNCTION_STATION_INPUT_MODELS_SHA256
    ):
        raise ServiceJunctionStationError(
            "Service-junction station target failed its exact input audit"
        )
    if (
        len(donor_header) != ZEBOIM_STATION_DONOR_HEADER_SIZE
        or _sha256(donor_header) != ZEBOIM_STATION_DONOR_HEADER_SHA256
        or len(donor_models) != ZEBOIM_STATION_DONOR_MODELS_SIZE
        or _sha256(donor_models) != ZEBOIM_STATION_DONOR_MODELS_SHA256
        or len(donor_graphics) != ZEBOIM_STATION_DONOR_GRAPHICS_SIZE
        or _sha256(donor_graphics) != ZEBOIM_STATION_DONOR_GRAPHICS_SHA256
    ):
        raise ServiceJunctionStationError(
            "Authentic Zeboim station donor failed its exact audit"
        )
    donor_record = 0x190 + ZEBOIM_STATION_SOURCE_NODE_INDEX * 16
    if donor_header[donor_record : donor_record + 16] != struct.pack(
        "<HhhhhhhH",
        0x0010,
        0,
        0x0200,
        0,
        0,
        0,
        0,
        ZEBOIM_STATION_SOURCE_MODEL_INDEX,
    ):
        raise ServiceJunctionStationError(
            "Authentic Zeboim station source node changed"
        )

    donor_entries = _indexed_entries(donor_models, label="field-373 models")
    if len(donor_entries) != 15:
        raise ServiceJunctionStationError("Field-373 model inventory changed")
    station_model = _retarget_inner_access_station_model(
        _relocate_station_model(
            donor_entries[ZEBOIM_STATION_SOURCE_MODEL_INDEX]
        )
    )
    station_atlas, station_palette = _build_legacy_station_atlas(
        donor_graphics, atlas_backing_graphics
    )

    model_entries = list(_indexed_entries(models, label="field-363 models"))
    if len(model_entries) != SERVICE_JUNCTION_STATION_TARGET_MODEL_INDEX:
        raise ServiceJunctionStationError("Field-363 model inventory changed")
    model_entries.append(station_model)
    output_models = _rebuild_indexed(
        models, model_entries, label="field-363 authentic station models"
    )
    output_graphics = _patch_graphics(
        graphics, station_atlas, station_palette
    )

    if struct.unpack_from("<H", header, 0x18C)[0] != 25:
        raise ServiceJunctionStationError("Field-363 static-node count changed")
    records = [
        header[0x190 + index * 16 : 0x190 + (index + 1) * 16]
        for index in range(25)
    ]
    if struct.unpack("<HhhhhhhH", records[17]) != (
        0x0010,
        0,
        0,
        0,
        0,
        0,
        0,
        2,
    ):
        raise ServiceJunctionStationError(
            "Field-363 inert south wall panel changed from its audit"
        )
    reader_x, reader_z = SERVICE_JUNCTION_STATION_READER_POSITION
    reader_record = struct.pack(
        "<HhhhhhhH",
        0x01E0,
        0,
        0,
        0,
        reader_x,
        0,
        reader_z,
        0,
    )
    records.insert(SERVICE_JUNCTION_STATION_READER_ENTITY, reader_record)
    records.append(
        struct.pack(
            "<HhhhhhhH",
            SERVICE_JUNCTION_STATION_NODE_FLAGS,
            0,
            SERVICE_JUNCTION_STATION_Y_ROTATION,
            0,
            *SERVICE_JUNCTION_STATION_PLACEMENT,
            SERVICE_JUNCTION_STATION_TARGET_MODEL_INDEX,
        )
    )
    if (
        len(records) != 27
        or len(records) - 1 != SERVICE_JUNCTION_STATION_TARGET_NODE_INDEX
    ):
        raise ServiceJunctionStationError(
            "Service-junction station header alignment changed"
        )
    output_header = bytearray(header[:0x190] + b"".join(records))
    struct.pack_into("<H", output_header, 0x18C, len(records))
    if len(output_header) != 832:
        raise ServiceJunctionStationError(
            "Service-junction station header size changed"
        )

    checks = (
        (bytes(output_header), SERVICE_JUNCTION_STATION_OUTPUT_HEADER_SHA256),
        (output_models, SERVICE_JUNCTION_STATION_OUTPUT_MODELS_SHA256),
        (output_graphics, SERVICE_JUNCTION_STATION_OUTPUT_GRAPHICS_SHA256),
    )
    for payload, expected in checks:
        if expected and _sha256(payload) != expected:
            raise ServiceJunctionStationError(
                "Service-junction station output is not deterministic"
            )
    return bytes(output_header), output_models, output_graphics


__all__ = [
    "SERVICE_JUNCTION_NATIVE_ROW485_USED_INDICES",
    "SERVICE_JUNCTION_NATIVE_ROW488_RECT",
    "SERVICE_JUNCTION_STATION_APPROACH_POSITION",
    "SERVICE_JUNCTION_STATION_APPROACH_TRIANGLE",
    "SERVICE_JUNCTION_STATION_ATLAS_SHA256",
    "SERVICE_JUNCTION_STATION_ATLAS_V",
    "SERVICE_JUNCTION_STATION_COLLIDER_ENTITY",
    "SERVICE_JUNCTION_STATION_COLLIDER_POSITION",
    "SERVICE_JUNCTION_STATION_COLLIDER_TRIANGLE",
    "SERVICE_JUNCTION_STATION_COLLISION_OPERAND",
    "SERVICE_JUNCTION_STATION_NODE_FLAGS",
    "SERVICE_JUNCTION_STATION_OUTPUT_GRAPHICS_SHA256",
    "SERVICE_JUNCTION_STATION_OUTPUT_HEADER_SHA256",
    "SERVICE_JUNCTION_STATION_OUTPUT_MODELS_SHA256",
    "SERVICE_JUNCTION_STATION_PALETTE_SHA256",
    "SERVICE_JUNCTION_STATION_PLACEMENT",
    "SERVICE_JUNCTION_STATION_READER_ENTITY",
    "SERVICE_JUNCTION_STATION_READER_HALF_WIDTH",
    "SERVICE_JUNCTION_STATION_READER_POSITION",
    "SERVICE_JUNCTION_STATION_READER_TRIANGLE",
    "SERVICE_JUNCTION_STATION_SCREEN_NORMAL",
    "SERVICE_JUNCTION_STATION_TARGET_CLUT",
    "SERVICE_JUNCTION_STATION_TARGET_PALETTE_RECT",
    "SERVICE_JUNCTION_STATION_TARGET_MODEL_INDEX",
    "SERVICE_JUNCTION_STATION_TARGET_NODE_INDEX",
    "SERVICE_JUNCTION_STATION_TARGET_TPAGES",
    "SERVICE_JUNCTION_STATION_TEXTURE_RECT",
    "SERVICE_JUNCTION_STATION_REMAPPED_ATLAS_SHA256",
    "SERVICE_JUNCTION_STATION_USED_INDEX_COUNT",
    "SERVICE_JUNCTION_STATION_VISUAL_CENTER",
    "SERVICE_JUNCTION_STATION_WORLD_BOUNDS",
    "SERVICE_JUNCTION_STATION_Y_ROTATION",
    "ServiceJunctionStationError",
    "patch_service_junction_zeboim_station",
]
