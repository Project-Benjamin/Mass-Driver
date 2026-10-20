#!/usr/bin/env python3
"""Install an authentic Zeboim time-clock station in field 377/target 727.

The three-door operations junction has one registered local sprite allocation
at VRAM x832.  Its native door image occupies only rows 0..76 of a 64-word
wide bank.  The game registers the complete image dimensions when the field
loads, so this transform extends that same bank to row 191 and uses rows
128..191 as a carrier for field 373's exact 8-bpp station atlas.  No untracked
MIM upload is appended.

The room's static models use three 256-colour palettes in rows 480..482.
Models 0/1/2/4 sample 107 row-482 indices, while model 3's row-481 polygons
sample only indices 1..89.  The former set is losslessly remapped into unused
row-481 indices 90..196, freeing the complete registered row 482 for the
station's retail palette.  Existing geometry, colours, walkmesh, and every
unrelated VRAM byte remain unchanged.
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
    ZEBOIM_STATION_SOURCE_CLUT,
    ZEBOIM_STATION_SOURCE_MODEL_INDEX,
    ZEBOIM_STATION_SOURCE_MODEL_SHA256,
    ZEBOIM_STATION_SOURCE_MODEL_SIZE,
    ZEBOIM_STATION_SOURCE_NODE_INDEX,
    ZEBOIM_STATION_SOURCE_TPAGES,
    ZEBOIM_STATION_TEXTURE_ATLAS,
    _graphics_rows,
    _reconstruct_graphics_vram,
)
from modules.mass_driver.tools.xgsubway_station import (
    _build_legacy_station_atlas,
    _indexed_entries,
    _rebuild_indexed,
)


class InnerAccessStationError(RuntimeError):
    """Raised when a source or target asset fails its exact audit."""


def _sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


INNER_ACCESS_STATION_INPUT_HEADER_SIZE = 720
INNER_ACCESS_STATION_INPUT_HEADER_SHA256 = (
    "f46e59eb359cca3d27da02b1c1919a2c4c1e846ed3562b38ebcbb803b8757f09"
)
INNER_ACCESS_STATION_INPUT_MODELS_SIZE = 2_868
INNER_ACCESS_STATION_INPUT_MODELS_SHA256 = (
    "c4435de49086ccfd68df20488c7e69204c2bbde27305d26af798c0512cb1d2b4"
)
INNER_ACCESS_STATION_INPUT_SPRITES_SIZE = 9_876
INNER_ACCESS_STATION_INPUT_SPRITES_SHA256 = (
    "96902a4a530809dee1c9fb6eb01ec046205ff6a04ff81e445acac3ab3a4052e2"
)
INNER_ACCESS_STATION_INPUT_GRAPHICS_SIZE = 116_736
INNER_ACCESS_STATION_INPUT_GRAPHICS_SHA256 = (
    "db54a274c151c4a2602e10b24e7781e99aed220916b64429b6d1d9bb476b8259"
)

INNER_ACCESS_STATION_SOURCE_SPRITE_BANK_SHA256 = (
    "35dbb84be4dd88b772ceb356dc9da65e5b9cc2d74477790e2f4020a044ce9093"
)
INNER_ACCESS_STATION_SOURCE_SPRITE_IMAGE_SHA256 = (
    "1d9b37811680dda76f98c947530d1537a1de0d6a33e78889a105be4a430df3e1"
)

# The station's visual centre is the live position at which the player stood
# while requesting the addition.  Entity 18 is centred on the static model and
# initialized as a solid NPC actor; its 0x1C bounds expand to 56 units at
# runtime, covering the model's complete horizontal footprint.  Entity 19 is
# a separate, non-solid reader at the east-facing control surface.  Its tight
# facing-gated frontage contains the user's captured stance (-88.55,-42.18)
# without allowing either side of the station to dispatch the notice.
INNER_ACCESS_STATION_VISUAL_CENTER = (-147, -42)
INNER_ACCESS_STATION_PLACEMENT = (-133, 102, -1)
INNER_ACCESS_STATION_Y_ROTATION = 0x0E00
INNER_ACCESS_STATION_WORLD_BOUNDS = (
    -185.326,
    -108.251,
    -156.0,
    -4.0,
    -80.903,
    -2.414,
)
INNER_ACCESS_STATION_COLLIDER_ENTITY = 18
INNER_ACCESS_STATION_COLLIDER_POSITION = INNER_ACCESS_STATION_VISUAL_CENTER
INNER_ACCESS_STATION_COLLIDER_TRIANGLE = 8
INNER_ACCESS_STATION_COLLISION_OPERAND = 0x1C
INNER_ACCESS_STATION_CONTROLLER_ENTITY = 19
INNER_ACCESS_STATION_CONTROLLER_POSITION = (-108, -42)
INNER_ACCESS_STATION_APPROACH_POSITION = (-89, -42)
INNER_ACCESS_STATION_CONTROLLER_TRIANGLE = 7
INNER_ACCESS_STATION_INTERACTION_HALF_WIDTH = 0x04

INNER_ACCESS_STATION_TARGET_MODEL_INDEX = 5
INNER_ACCESS_STATION_TARGET_NODE_INDEX = 22
INNER_ACCESS_STATION_NODE_FLAGS = 0x0010
INNER_ACCESS_STATION_TARGET_TPAGES = (0x008D, 0x00AD)
INNER_ACCESS_STATION_TARGET_CLUT = 0x7880
INNER_ACCESS_STATION_ATLAS_V = 128
INNER_ACCESS_STATION_ATLAS_WIDTH = 80
INNER_ACCESS_STATION_ATLAS_HEIGHT = 64
INNER_ACCESS_STATION_CARRIER_IMAGE_DIMENSIONS = (64, 192)

INNER_ACCESS_NATIVE_OLD_CLUT = 0x7880
INNER_ACCESS_NATIVE_RELOCATED_CLUT = 0x7840
INNER_ACCESS_NATIVE_RELOCATED_MODELS = (0, 1, 2, 4)
INNER_ACCESS_NATIVE_USED_INDICES = (
    *range(1, 23),
    *range(24, 74),
    *range(76, 106),
    *range(107, 111),
    112,
)
INNER_ACCESS_NATIVE_TEXTURE_RECTS = (
    (0, 0, 32, 50),
    (0, 50, 51, 31),
    (104, 50, 24, 30),
)
INNER_ACCESS_NATIVE_TEXTURE_FILE_OFFSET = 0x1800
INNER_ACCESS_NATIVE_TEXTURE_ROW_STRIDE = 512
INNER_ACCESS_NATIVE_TEXTURE_U_OFFSET = 384
INNER_ACCESS_GRAPHICS_ROW481_OFFSET = 0x0A00
INNER_ACCESS_GRAPHICS_ROW482_OFFSET = 0x0C00

INNER_ACCESS_STATION_RELOCATED_MODEL_SHA256 = (
    "df5637e5078f9ee853ff776294c717e734457d9727689b0eb9cf364cc0708f19"
)
INNER_ACCESS_STATION_OUTPUT_HEADER_SHA256 = (
    "1154bd7a0d3941bf9f2240e889ce5ed94b463f2d2888684df3b3e6d9135a81a0"
)
INNER_ACCESS_STATION_OUTPUT_MODELS_SHA256 = (
    "da4da224f7b1cd0da539afcf56679e1c4216a9f69c3eaea2616e8bc2b8ce1abe"
)
INNER_ACCESS_STATION_OUTPUT_SPRITES_SHA256 = (
    "a36fc4945b2f43dc21b02d2ff08302fc69dae4a8a6ec0b9bb34dedf59513af00"
)
INNER_ACCESS_STATION_OUTPUT_GRAPHICS_SHA256 = (
    "c64a25229e4916e814e299b9e5b9dbcffc24c016186037ca932600feb7c9fa59"
)
INNER_ACCESS_STATION_OUTPUT_NATIVE_MODEL_SHA256S = (
    "8ce9d14f415b5ef8e55422de1e7e8e70b37a0695e8c976bbe12f3f124bc47033",
    "85bf71ce10fadab178297aeb256efb7e47a72da817e81959dac122a110826925",
    "727e072b16eaf584add062c2163b60d16bee27e4655c48250de698091170ab24",
    "05e8502f3652dca3a0b181aa58a89af13b405c113f8c751047238118ace55ead",
    "7d6f7bde88b633125d6d412a3292e5e5f9197be75542e0399b920fbefdfbbe02",
)
INNER_ACCESS_STATION_OUTPUT_ROW481_SHA256 = (
    "0b555fdba1059256b8ff58be89765266a16c7cb10957ff8fa5ae4b2233bc2cd4"
)


def _relocate_station_model(model: bytes) -> bytes:
    """Point field 373's exact model at x832, rows 128..191."""

    if (
        len(model) != ZEBOIM_STATION_SOURCE_MODEL_SIZE
        or _sha256(model) != ZEBOIM_STATION_SOURCE_MODEL_SHA256
    ):
        raise InnerAccessStationError("Zeboim station donor model failed its audit")

    output = bytearray(model)
    status_mapping = dict(
        zip(
            ZEBOIM_STATION_SOURCE_TPAGES,
            INNER_ACCESS_STATION_TARGET_TPAGES,
            strict=True,
        )
    )
    part_count = struct.unpack_from("<I", output)[0]
    status_count = 0
    clut_count = 0
    triangles = 0
    quads = 0
    used_islands: set[int] = set()

    def relocate_uvs(offsets: tuple[int, ...]) -> None:
        old_uvs = tuple((output[offset], output[offset + 1]) for offset in offsets)
        matches: list[tuple[int, int, int, int, int]] = []
        for island_index, (source, target) in enumerate(
            ZEBOIM_STATION_TEXTURE_ATLAS
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
            raise InnerAccessStationError(
                "Station polygon does not belong to one audited atlas island"
            )
        island_index, source_u, source_v, target_u, target_v = matches[0]
        used_islands.add(island_index)
        for offset, (old_u, old_v) in zip(offsets, old_uvs, strict=True):
            new_u = target_u + old_u - source_u
            new_v = (
                INNER_ACCESS_STATION_ATLAS_V
                + target_v
                + old_v
                - source_v
            )
            if not (
                0 <= new_u < INNER_ACCESS_STATION_ATLAS_WIDTH
                and INNER_ACCESS_STATION_ATLAS_V
                <= new_v
                < INNER_ACCESS_STATION_ATLAS_V
                + INNER_ACCESS_STATION_ATLAS_HEIGHT
            ):
                raise InnerAccessStationError(
                    "Station UV exceeds the registered carrier atlas"
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
                        old_status = command & 0xFFFF
                        if old_status not in status_mapping:
                            raise InnerAccessStationError(
                                "Station uses an unaudited texture page"
                            )
                        struct.pack_into(
                            "<H", output, command_offset, status_mapping[old_status]
                        )
                        status_count += 1
                    elif operator == 0xC8:
                        if command & 0xFFFF != ZEBOIM_STATION_SOURCE_CLUT:
                            raise InnerAccessStationError(
                                "Station uses an unaudited CLUT"
                            )
                        struct.pack_into(
                            "<H",
                            output,
                            command_offset,
                            INNER_ACCESS_STATION_TARGET_CLUT,
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
                        raise InnerAccessStationError(
                            "Station display list contains an unknown command"
                        )

    relocated = bytes(output)
    if (
        status_count != 2
        or clut_count != 1
        or triangles != 5
        or quads != 80
        or used_islands != set(range(len(ZEBOIM_STATION_TEXTURE_ATLAS)))
        or len(relocated) != ZEBOIM_STATION_SOURCE_MODEL_SIZE
    ):
        raise InnerAccessStationError("Station model relocation is incomplete")
    if (
        INNER_ACCESS_STATION_RELOCATED_MODEL_SHA256
        and _sha256(relocated) != INNER_ACCESS_STATION_RELOCATED_MODEL_SHA256
    ):
        raise InnerAccessStationError("Relocated station model is not deterministic")
    return relocated


def _patch_native_model_clut(model: bytes) -> bytes:
    """Point one audited 8-bpp native model at remapped row 481."""

    output = bytearray(model)
    changed = 0
    for offset in range(0, len(output) - 3, 4):
        command = struct.unpack_from("<I", output, offset)[0]
        if command >> 24 == 0xC8 and command & 0xFFFF == INNER_ACCESS_NATIVE_OLD_CLUT:
            struct.pack_into("<H", output, offset, INNER_ACCESS_NATIVE_RELOCATED_CLUT)
            changed += 1
    if changed != 1:
        raise InnerAccessStationError(
            "Native field-377 model did not contain one audited row-482 CLUT"
        )
    return bytes(output)


def _patch_sprite_carrier(sprites: bytes, station_atlas: bytes) -> bytes:
    banks = list(_indexed_entries(sprites, label="field-377 sprite archive"))
    if (
        len(banks) != 1
        or _sha256(banks[0]) != INNER_ACCESS_STATION_SOURCE_SPRITE_BANK_SHA256
    ):
        raise InnerAccessStationError("Field-377 sprite carrier changed")
    images = list(_indexed_entries(banks[0], label="field-377 sprite bank 0"))
    if (
        len(images) != 1
        or struct.unpack_from("<HH", images[0]) != (64, 77)
        or _sha256(images[0]) != INNER_ACCESS_STATION_SOURCE_SPRITE_IMAGE_SHA256
    ):
        raise InnerAccessStationError("Field-377 sprite image changed")
    if len(station_atlas) != (
        INNER_ACCESS_STATION_ATLAS_WIDTH * INNER_ACCESS_STATION_ATLAS_HEIGHT
    ):
        raise InnerAccessStationError("Station atlas has an unexpected size")

    width_words, height = INNER_ACCESS_STATION_CARRIER_IMAGE_DIMENSIONS
    row_stride = width_words * 2
    image = bytearray(4 + row_stride * height)
    image[: len(images[0])] = images[0]
    struct.pack_into("<HH", image, 0, width_words, height)
    for row in range(INNER_ACCESS_STATION_ATLAS_HEIGHT):
        source_start = row * INNER_ACCESS_STATION_ATLAS_WIDTH
        target_start = (
            4 + (INNER_ACCESS_STATION_ATLAS_V + row) * row_stride
        )
        image[
            target_start : target_start + INNER_ACCESS_STATION_ATLAS_WIDTH
        ] = station_atlas[
            source_start : source_start + INNER_ACCESS_STATION_ATLAS_WIDTH
        ]
    images[0] = bytes(image)
    banks[0] = _rebuild_indexed(
        banks[0], images, label="field-377 expanded sprite carrier"
    )
    return _rebuild_indexed(
        sprites, banks, label="field-377 station sprite archive"
    )


def _patch_graphics_palette(graphics: bytes, station_palette: bytes) -> bytes:
    vram, rectangles = _reconstruct_graphics_vram(
        graphics, label="Retail field 377"
    )
    if rectangles != (
        (0, 480, 256, 3),
        (320, 0, 256, 128),
        (320, 128, 128, 128),
        (448, 128, 64, 64),
    ):
        raise InnerAccessStationError("Field-377 graphics inventory changed")
    row481 = _graphics_rows(vram, (0, 481, 256, 1))
    row482 = _graphics_rows(vram, (0, 482, 256, 1))
    if len(station_palette) != 512:
        raise InnerAccessStationError("Station palette has an unexpected size")

    # Models 0/1/2/4 share TPAGE 0x0088 and the three disjoint texture
    # rectangles below.  Their 107 sampled indices are moved into row 481's
    # proven-free 90..196 range.  Model 3 keeps row 481 indices 1..89, so the
    # native colours remain disjoint and exact.
    used_indices = tuple(INNER_ACCESS_NATIVE_USED_INDICES)
    if len(used_indices) != 107 or len(set(used_indices)) != 107:
        raise InnerAccessStationError("Native palette-index audit changed")
    palette_mapping = {
        source: 90 + index for index, source in enumerate(used_indices)
    }
    output_row481 = bytearray(row481)
    for source, target in palette_mapping.items():
        output_row481[target * 2 : target * 2 + 2] = row482[
            source * 2 : source * 2 + 2
        ]

    output = bytearray(graphics)
    if (
        output[
            INNER_ACCESS_GRAPHICS_ROW481_OFFSET :
            INNER_ACCESS_GRAPHICS_ROW481_OFFSET + 512
        ]
        != row481
        or output[
            INNER_ACCESS_GRAPHICS_ROW482_OFFSET :
            INNER_ACCESS_GRAPHICS_ROW482_OFFSET + 512
        ]
        != row482
    ):
        raise InnerAccessStationError("Field-377 palette file offsets changed")

    sampled_indices: set[int] = set()
    patched_texels: set[int] = set()
    for u, v, width, height in INNER_ACCESS_NATIVE_TEXTURE_RECTS:
        for row in range(height):
            for column in range(width):
                source_u = u + column
                source_v = v + row
                vram_offset = ((source_v * 1024 + 512) * 2) + source_u
                source_index = vram[vram_offset]
                sampled_indices.add(source_index)
                if source_index not in palette_mapping:
                    raise InnerAccessStationError(
                        "Native TPAGE 0x0088 gained an unaudited palette index"
                    )
                file_offset = (
                    INNER_ACCESS_NATIVE_TEXTURE_FILE_OFFSET
                    + source_v * INNER_ACCESS_NATIVE_TEXTURE_ROW_STRIDE
                    + INNER_ACCESS_NATIVE_TEXTURE_U_OFFSET
                    + source_u
                )
                if output[file_offset] != source_index:
                    raise InnerAccessStationError(
                        "Native TPAGE 0x0088 file mapping changed"
                    )
                output[file_offset] = palette_mapping[source_index]
                patched_texels.add(file_offset)
    if (
        tuple(sorted(sampled_indices)) != used_indices
        or len(patched_texels) != 3_901
    ):
        raise InnerAccessStationError(
            "Native TPAGE 0x0088 sampled-index audit changed"
        )

    output[
        INNER_ACCESS_GRAPHICS_ROW481_OFFSET :
        INNER_ACCESS_GRAPHICS_ROW481_OFFSET + 512
    ] = output_row481
    output[
        INNER_ACCESS_GRAPHICS_ROW482_OFFSET :
        INNER_ACCESS_GRAPHICS_ROW482_OFFSET + 512
    ] = station_palette
    output_vram, output_rectangles = _reconstruct_graphics_vram(
        bytes(output), label="Target-727 station graphics"
    )
    if (
        output_rectangles != rectangles
        or _sha256(_graphics_rows(output_vram, (0, 481, 256, 1)))
        != INNER_ACCESS_STATION_OUTPUT_ROW481_SHA256
        or _graphics_rows(output_vram, (0, 482, 256, 1))
        != station_palette
    ):
        raise InnerAccessStationError(
            "Inner-access palette relocation is not deterministic"
        )
    return bytes(output)


def patch_inner_access_zeboim_station(
    header: bytes,
    models: bytes,
    sprites: bytes,
    graphics: bytes,
    donor_header: bytes,
    donor_models: bytes,
    donor_graphics: bytes,
    atlas_backing_graphics: bytes,
) -> tuple[bytes, bytes, bytes, bytes]:
    """Add field 373's station at the live target-727 request point."""

    if (
        len(header) != INNER_ACCESS_STATION_INPUT_HEADER_SIZE
        or _sha256(header) != INNER_ACCESS_STATION_INPUT_HEADER_SHA256
        or len(models) != INNER_ACCESS_STATION_INPUT_MODELS_SIZE
        or _sha256(models) != INNER_ACCESS_STATION_INPUT_MODELS_SHA256
        or len(sprites) != INNER_ACCESS_STATION_INPUT_SPRITES_SIZE
        or _sha256(sprites) != INNER_ACCESS_STATION_INPUT_SPRITES_SHA256
        or len(graphics) != INNER_ACCESS_STATION_INPUT_GRAPHICS_SIZE
        or _sha256(graphics) != INNER_ACCESS_STATION_INPUT_GRAPHICS_SHA256
    ):
        raise InnerAccessStationError("Inner-access station target failed its audit")
    if (
        len(donor_header) != ZEBOIM_STATION_DONOR_HEADER_SIZE
        or _sha256(donor_header) != ZEBOIM_STATION_DONOR_HEADER_SHA256
        or len(donor_models) != ZEBOIM_STATION_DONOR_MODELS_SIZE
        or _sha256(donor_models) != ZEBOIM_STATION_DONOR_MODELS_SHA256
        or len(donor_graphics) != ZEBOIM_STATION_DONOR_GRAPHICS_SIZE
        or _sha256(donor_graphics) != ZEBOIM_STATION_DONOR_GRAPHICS_SHA256
    ):
        raise InnerAccessStationError("Zeboim station donor failed its audit")

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
        raise InnerAccessStationError("Station source node changed from retail")

    donor_entries = _indexed_entries(donor_models, label="field-373 models")
    if len(donor_entries) != 15:
        raise InnerAccessStationError("Field-373 model inventory changed")
    station_model = _relocate_station_model(
        donor_entries[ZEBOIM_STATION_SOURCE_MODEL_INDEX]
    )
    station_atlas, station_palette = _build_legacy_station_atlas(
        donor_graphics, atlas_backing_graphics
    )

    model_entries = list(_indexed_entries(models, label="field-377 models"))
    if len(model_entries) != INNER_ACCESS_STATION_TARGET_MODEL_INDEX:
        raise InnerAccessStationError("Field-377 model inventory changed")
    for model_index in INNER_ACCESS_NATIVE_RELOCATED_MODELS:
        model_entries[model_index] = _patch_native_model_clut(
            model_entries[model_index]
        )
    if tuple(_sha256(model) for model in model_entries) != (
        INNER_ACCESS_STATION_OUTPUT_NATIVE_MODEL_SHA256S
    ):
        raise InnerAccessStationError(
            "Native field-377 palette relocation changed"
        )
    model_entries.append(station_model)
    output_models = _rebuild_indexed(
        models, model_entries, label="field-377 station models"
    )
    output_sprites = _patch_sprite_carrier(sprites, station_atlas)
    output_graphics = _patch_graphics_palette(graphics, station_palette)

    if struct.unpack_from("<H", header, 0x18C)[0] != 20:
        raise InnerAccessStationError("Field-377 static-node count changed")
    records = [
        header[0x190 + index * 16 : 0x190 + (index + 1) * 16]
        for index in range(20)
    ]
    collider_x, collider_z = INNER_ACCESS_STATION_COLLIDER_POSITION
    collider_record = struct.pack(
        "<HhhhhhhH",
        0x01E0,
        0,
        0,
        0,
        collider_x,
        0,
        collider_z,
        0,
    )
    if collider_record.hex() != "e0010000000000006dff0000d6ff0000":
        raise InnerAccessStationError("Station collider record changed")
    controller_x, controller_z = INNER_ACCESS_STATION_CONTROLLER_POSITION
    controller_record = struct.pack(
        "<HhhhhhhH",
        0x01E0,
        0,
        0,
        0,
        controller_x,
        0,
        controller_z,
        0,
    )
    if controller_record.hex() != "e00100000000000094ff0000d6ff0000":
        raise InnerAccessStationError("Station frontage record changed")
    records.insert(INNER_ACCESS_STATION_COLLIDER_ENTITY, collider_record)
    records.insert(INNER_ACCESS_STATION_CONTROLLER_ENTITY, controller_record)
    station_record = (
        struct.pack(
            "<HhhhhhhH",
            INNER_ACCESS_STATION_NODE_FLAGS,
            0,
            INNER_ACCESS_STATION_Y_ROTATION,
            0,
            *INNER_ACCESS_STATION_PLACEMENT,
            INNER_ACCESS_STATION_TARGET_MODEL_INDEX,
        )
    )
    if station_record.hex() != "10000000000e00007bff6600ffff0500":
        raise InnerAccessStationError("Station static-node record changed")
    records.append(station_record)
    output_header = bytearray(header[:0x190] + b"".join(records))
    struct.pack_into("<H", output_header, 0x18C, len(records))
    if len(records) != 23 or len(output_header) != 768:
        raise InnerAccessStationError("Station header insertion changed")

    checks = (
        (bytes(output_header), INNER_ACCESS_STATION_OUTPUT_HEADER_SHA256),
        (output_models, INNER_ACCESS_STATION_OUTPUT_MODELS_SHA256),
        (output_sprites, INNER_ACCESS_STATION_OUTPUT_SPRITES_SHA256),
        (output_graphics, INNER_ACCESS_STATION_OUTPUT_GRAPHICS_SHA256),
    )
    for payload, expected in checks:
        if expected and _sha256(payload) != expected:
            raise InnerAccessStationError(
                "Inner-access station output is not deterministic"
            )
    return bytes(output_header), output_models, output_sprites, output_graphics


__all__ = [
    "INNER_ACCESS_STATION_ATLAS_HEIGHT",
    "INNER_ACCESS_STATION_ATLAS_V",
    "INNER_ACCESS_STATION_ATLAS_WIDTH",
    "INNER_ACCESS_STATION_APPROACH_POSITION",
    "INNER_ACCESS_STATION_COLLIDER_ENTITY",
    "INNER_ACCESS_STATION_COLLIDER_POSITION",
    "INNER_ACCESS_STATION_COLLIDER_TRIANGLE",
    "INNER_ACCESS_STATION_COLLISION_OPERAND",
    "INNER_ACCESS_STATION_CONTROLLER_ENTITY",
    "INNER_ACCESS_STATION_CONTROLLER_POSITION",
    "INNER_ACCESS_STATION_CONTROLLER_TRIANGLE",
    "INNER_ACCESS_STATION_INTERACTION_HALF_WIDTH",
    "INNER_ACCESS_STATION_NODE_FLAGS",
    "INNER_ACCESS_STATION_PLACEMENT",
    "INNER_ACCESS_STATION_TARGET_CLUT",
    "INNER_ACCESS_STATION_TARGET_MODEL_INDEX",
    "INNER_ACCESS_STATION_TARGET_NODE_INDEX",
    "INNER_ACCESS_STATION_TARGET_TPAGES",
    "INNER_ACCESS_STATION_VISUAL_CENTER",
    "INNER_ACCESS_STATION_WORLD_BOUNDS",
    "INNER_ACCESS_STATION_Y_ROTATION",
    "InnerAccessStationError",
    "patch_inner_access_zeboim_station",
]
