#!/usr/bin/env python3
"""Add horizontal Zeboim missile racks to the retail field-385 model archive.

The Mass Driver reconstruction uses field 385's long magnetic-conduit hall as
an authentic Zeboim-era donor.  This transform adds eight low-poly missiles in
four overhead wall-rack rows while leaving the walkmesh, field entities,
scripts, textures, and graphics bundle untouched.

Only model 11 is changed.  It is the hall's checked static environment model
and already owns a flat-triangle (POLY_F3) mesh group, so the new primitives
need no actor, texture page, CLUT, or VRAM allocation.  Both the complete
retail model archive and model 11 are SHA-256 locked before any edit.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
from typing import Iterable

from modules.mass_driver.tools.xgmissiles import (
    MissileGeometry,
    MissileModelError,
    PLATFORM_FLOOR_Y,
    Triangle,
    _model_spans,
    _one_missile,
)


RETAIL_FIELD_385_MODELS_SHA256 = (
    "558f17333a467d274b28fde9c2a20f29e241a08317a1c2f0f170c5b642319823"
)
RETAIL_FIELD_385_MODEL_11_SHA256 = (
    "464176add2befce8caae6b3167420924be918dc578e126dc5971dfb9293ddd03"
)

# Keeping the deterministic checked output hash public lets the dungeon builder
# and release manifest assert the exact model component they are about to pack.
PATCHED_FIELD_385_MODELS_SHA256 = (
    "3f0a8b4b3f9994073818d8243cdc9c572acc21cf5efb76037fe6a1e742153397"
)

TARGET_MODEL_INDEX = 11
F3_MESH_TYPE = 0x04
F3_GPU_COMMAND = 0x20

# The donor hall is approximately x=-176..176 and y=-235..22.  These racks
# remain inside x=-175..175 and y=-172..-87.  The two deeper right-hand racks
# jog inward with the retail hall's narrower northern section.
MISSILE_CENTER_Y = -135


@dataclass(frozen=True)
class RackPlacement:
    center_x: int
    center_z: int
    wall_x: int


RACK_PLACEMENTS: tuple[RackPlacement, ...] = (
    RackPlacement(-138, -150, -175),
    RackPlacement(138, -150, 175),
    RackPlacement(-138, -400, -175),
    RackPlacement(138, -400, 175),
    RackPlacement(-138, -700, -175),
    RackPlacement(43, -700, 80),
    RackPlacement(-138, -950, -175),
    RackPlacement(43, -950, 80),
)

# The original prop is 390 units long with 82-unit fin tips.  Field 385's
# ceiling is much lower than field 632's missile-gallery donor, so the prop is
# laid horizontally and reduced to roughly 238 x 74 x 74 units.
LONGITUDINAL_SCALE = (3, 5)
RADIAL_SCALE = (9, 20)
RACK_COLOUR = (34, 40, 39)


@dataclass(frozen=True)
class Model11Audit:
    vertex_count: int
    primitive_count: int
    mesh_count: int
    mesh_groups: tuple[tuple[int, int, int], ...]
    vertex_offset: int
    mesh_offset: int
    display_list_offset: int
    instance_buffer_size: int
    model_size: int
    minimum: tuple[int, int, int]
    maximum: tuple[int, int, int]

    @property
    def f3_count(self) -> int:
        return self.mesh_groups[0][2]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _scale_signed(value: int, numerator: int, denominator: int) -> int:
    """Scale one signed integer with deterministic half-away-from-zero rounding."""

    if denominator <= 0 or numerator < 0:
        raise ValueError("Scale must have a non-negative numerator and positive denominator")
    magnitude = (abs(value) * numerator + denominator // 2) // denominator
    return -magnitude if value < 0 else magnitude


def _append_two_sided_triangle(
    triangles: list[Triangle],
    a: int,
    b: int,
    c: int,
    colour: tuple[int, int, int],
) -> None:
    triangles.append(Triangle((a, b, c, 0), colour))
    triangles.append(Triangle((c, b, a, 0), colour))


def build_zeboim_missile_rack_geometry(
    placements: Iterable[RackPlacement] = RACK_PLACEMENTS,
) -> MissileGeometry:
    """Return eight horizontal missiles and their native flat-shaded brackets."""

    source = _one_missile(0, 0)
    longitudinal_numerator, longitudinal_denominator = LONGITUDINAL_SCALE
    radial_numerator, radial_denominator = RADIAL_SCALE
    longitudinal_extent = _scale_signed(
        390,
        longitudinal_numerator,
        longitudinal_denominator,
    )
    half_length = longitudinal_extent // 2

    vertices: list[tuple[int, int, int, int]] = []
    triangles: list[Triangle] = []
    checked_placements = tuple(placements)
    if not checked_placements:
        raise MissileModelError("Zeboim missile rack needs at least one placement")

    for placement in checked_placements:
        side = -1 if placement.wall_x < placement.center_x else 1
        if side < 0 and placement.wall_x >= placement.center_x:
            raise MissileModelError("Left rack wall must be outside its missile")
        if side > 0 and placement.wall_x <= placement.center_x:
            raise MissileModelError("Right rack wall must be outside its missile")

        missile_base = len(vertices)
        for source_x, source_y, source_z, _unused in source.vertices:
            axial = PLATFORM_FLOOR_Y - source_y
            x = placement.center_x + _scale_signed(
                source_x,
                radial_numerator,
                radial_denominator,
            )
            y = MISSILE_CENTER_Y + _scale_signed(
                source_z,
                radial_numerator,
                radial_denominator,
            )
            z = (
                placement.center_z
                + half_length
                - _scale_signed(
                    axial,
                    longitudinal_numerator,
                    longitudinal_denominator,
                )
            )
            if any(not -0x8000 <= value <= 0x7FFF for value in (x, y, z)):
                raise MissileModelError("Transformed missile vertex overflows s16")
            vertices.append((x, y, z, 0))

        triangles.extend(
            Triangle(
                (
                    triangle.indices[0] + missile_base,
                    triangle.indices[1] + missile_base,
                    triangle.indices[2] + missile_base,
                    0,
                ),
                triangle.colour,
            )
            for triangle in source.triangles
        )

        # Two double-sided wall brackets cradle each missile outside its
        # central-aisle silhouette.  They use the same F3 primitive class and
        # therefore add no texture or graphics dependency.
        seat_x = placement.center_x + side * 18
        for bracket_z in (placement.center_z - 70, placement.center_z + 70):
            bracket_base = len(vertices)
            vertices.extend(
                (
                    (placement.wall_x, MISSILE_CENTER_Y + 48, bracket_z, 0),
                    (seat_x, MISSILE_CENTER_Y + 30, bracket_z, 0),
                    (seat_x, MISSILE_CENTER_Y + 3, bracket_z, 0),
                )
            )
            _append_two_sided_triangle(
                triangles,
                bracket_base,
                bracket_base + 1,
                bracket_base + 2,
                RACK_COLOUR,
            )

    return MissileGeometry(tuple(vertices), tuple(triangles))


def _audit_model11(model: bytes) -> Model11Audit:
    if len(model) < 0x48 or struct.unpack_from("<I", model)[0] != 1:
        raise MissileModelError("Field 385 model 11 is not one checked block")

    block = 0x10
    vertex_count = struct.unpack_from("<H", model, block + 2)[0]
    primitive_count = struct.unpack_from("<H", model, block + 4)[0]
    mesh_count = struct.unpack_from("<H", model, block + 6)[0]
    vertex_offset = struct.unpack_from("<I", model, block + 8)[0]
    normal_offset = struct.unpack_from("<I", model, block + 0x0C)[0]
    mesh_offset = struct.unpack_from("<I", model, block + 0x10)[0]
    display_offset = struct.unpack_from("<I", model, block + 0x14)[0]
    dynamic_offset = struct.unpack_from("<I", model, block + 0x18)[0]
    instance_size = struct.unpack_from("<I", model, block + 0x34)[0]

    if (
        vertex_offset != 0x48
        or normal_offset != vertex_offset
        or dynamic_offset != 0
        or mesh_count != 4
    ):
        raise MissileModelError("Field 385 model 11 block layout changed")
    if vertex_offset + vertex_count * 8 != mesh_offset:
        raise MissileModelError("Model 11 vertex table does not end at its mesh")
    if not mesh_offset < display_offset <= len(model):
        raise MissileModelError("Model 11 mesh/display offsets are invalid")

    cursor = mesh_offset
    groups: list[tuple[int, int, int]] = []
    for _ in range(mesh_count):
        if cursor + 4 > display_offset:
            raise MissileModelError("Model 11 mesh header overlaps its display list")
        primitive_type, unknown, count = struct.unpack_from("<BBH", model, cursor)
        cursor += 4
        groups.append((primitive_type, unknown, count))
        cursor += count * 8
    if cursor != display_offset:
        raise MissileModelError("Model 11 mesh groups do not end at the display list")
    if tuple((kind, unknown) for kind, unknown, _count in groups) != (
        (0x04, 119),
        (0x05, 119),
        (0x0C, 119),
        (0x0D, 119),
    ):
        raise MissileModelError(f"Unexpected model 11 mesh inventory: {groups!r}")
    if sum(count for _kind, _unknown, count in groups) != primitive_count:
        raise MissileModelError("Model 11 primitive count disagrees with its groups")
    if len(model) < display_offset + groups[0][2] * 4:
        raise MissileModelError("Model 11 flat-triangle display records are truncated")

    minimum = struct.unpack_from("<hhh", model, block + 0x20)
    maximum = struct.unpack_from("<hhh", model, block + 0x28)
    return Model11Audit(
        vertex_count,
        primitive_count,
        mesh_count,
        tuple(groups),
        vertex_offset,
        mesh_offset,
        display_offset,
        instance_size,
        len(model),
        minimum,
        maximum,
    )


def _rebuild_model_archive(source: bytes, entries: list[bytes]) -> bytes:
    original_count = struct.unpack_from("<I", source)[0]
    if original_count != len(entries):
        raise MissileModelError("Model archive entry count changed unexpectedly")
    original_table_end = 4 + original_count * 4
    original_first = struct.unpack_from("<I", source, 4)[0]
    prefix_padding = source[original_table_end:original_first]

    output = bytearray(4 + len(entries) * 4)
    struct.pack_into("<I", output, 0, len(entries))
    output.extend(prefix_padding)
    for index, entry in enumerate(entries):
        if not entry:
            raise MissileModelError("Model archive cannot contain an empty entry")
        struct.pack_into("<I", output, 4 + index * 4, len(output))
        output.extend(entry)
    return bytes(output)


def patch_zeboim_missile_racks(models: bytes) -> bytes:
    """Return field 385's model archive with eight overhead missile racks."""

    digest = _sha256(models)
    if digest != RETAIL_FIELD_385_MODELS_SHA256:
        raise MissileModelError(
            "Zeboim missile racks require the audited retail field 385 model "
            f"archive; found SHA-256 {digest}"
        )

    spans = _model_spans(models)
    if len(spans) != 13:
        raise MissileModelError(f"Expected 13 field-385 models, found {len(spans)}")
    entries = [models[start:end] for start, end in spans]
    source_model = entries[TARGET_MODEL_INDEX]
    if _sha256(source_model) != RETAIL_FIELD_385_MODEL_11_SHA256:
        raise MissileModelError("Field 385 model 11 hash does not match the audit")

    before = _audit_model11(source_model)
    if (
        before.vertex_count,
        before.primitive_count,
        before.f3_count,
        before.mesh_offset,
        before.display_list_offset,
        before.instance_buffer_size,
        before.model_size,
    ) != (235, 198, 2, 1952, 3552, 7672, 5892):
        raise MissileModelError(f"Unexpected retail model 11 audit: {before!r}")

    geometry = build_zeboim_missile_rack_geometry()
    added_vertex_bytes = b"".join(
        struct.pack("<hhhh", *vertex) for vertex in geometry.vertices
    )
    added_index_bytes = b"".join(
        struct.pack("<HHHH", *triangle.indices) for triangle in geometry.triangles
    )
    added_commands = b"".join(
        bytes((*triangle.colour, F3_GPU_COMMAND))
        for triangle in geometry.triangles
    )

    added_vertices = len(geometry.vertices)
    added_triangles = len(geometry.triangles)
    new_vertex_count = before.vertex_count + added_vertices
    new_primitive_count = before.primitive_count + added_triangles
    new_f3_count = before.f3_count + added_triangles
    if any(
        value > 0xFFFF
        for value in (new_vertex_count, new_primitive_count, new_f3_count)
    ):
        raise MissileModelError("Patched model count exceeds a 16-bit field")

    relocated_indices = bytearray()
    for offset in range(0, len(added_index_bytes), 8):
        a, b, c, unused = struct.unpack_from("<HHHH", added_index_bytes, offset)
        relocated_indices.extend(
            struct.pack(
                "<HHHH",
                a + before.vertex_count,
                b + before.vertex_count,
                c + before.vertex_count,
                unused,
            )
        )

    old_vertices = source_model[before.vertex_offset : before.mesh_offset]
    first_group_type, first_group_unknown, old_f3_count = struct.unpack_from(
        "<BBH",
        source_model,
        before.mesh_offset,
    )
    if (
        first_group_type != F3_MESH_TYPE
        or first_group_unknown != 119
        or old_f3_count != before.f3_count
    ):
        raise MissileModelError("Model 11 first mesh group is not the audited F3 group")
    old_f3_indices_start = before.mesh_offset + 4
    old_f3_indices_end = old_f3_indices_start + old_f3_count * 8
    mesh_tail = source_model[old_f3_indices_end : before.display_list_offset]
    mesh = (
        struct.pack("<BBH", first_group_type, first_group_unknown, new_f3_count)
        + source_model[old_f3_indices_start:old_f3_indices_end]
        + bytes(relocated_indices)
        + mesh_tail
    )

    old_f3_display_end = before.display_list_offset + old_f3_count * 4
    display = (
        source_model[before.display_list_offset:old_f3_display_end]
        + added_commands
        + source_model[old_f3_display_end:]
    )

    new_model = bytearray(source_model[: before.vertex_offset])
    new_model.extend(old_vertices)
    new_model.extend(added_vertex_bytes)
    new_mesh_offset = len(new_model)
    new_model.extend(mesh)
    new_display_offset = len(new_model)
    new_model.extend(display)

    block = 0x10
    struct.pack_into("<H", new_model, block + 2, new_vertex_count)
    struct.pack_into("<H", new_model, block + 4, new_primitive_count)
    struct.pack_into("<I", new_model, block + 0x10, new_mesh_offset)
    struct.pack_into("<I", new_model, block + 0x14, new_display_offset)
    struct.pack_into(
        "<I",
        new_model,
        block + 0x34,
        before.instance_buffer_size + added_triangles * 0x14,
    )

    all_vertices = [
        struct.unpack_from("<hhhh", new_model, before.vertex_offset + index * 8)
        for index in range(new_vertex_count)
    ]
    for axis, minimum_offset, maximum_offset in (
        (0, block + 0x20, block + 0x28),
        (1, block + 0x22, block + 0x2A),
        (2, block + 0x24, block + 0x2C),
    ):
        struct.pack_into(
            "<h",
            new_model,
            minimum_offset,
            min(vertex[axis] for vertex in all_vertices),
        )
        struct.pack_into(
            "<h",
            new_model,
            maximum_offset,
            max(vertex[axis] for vertex in all_vertices),
        )

    entries[TARGET_MODEL_INDEX] = bytes(new_model)
    output = _rebuild_model_archive(models, entries)

    patched_spans = _model_spans(output)
    patched_entries = [output[start:end] for start, end in patched_spans]
    if any(
        patched_entries[index] != entries[index]
        for index in range(len(entries))
        if index != TARGET_MODEL_INDEX
    ):
        raise MissileModelError("A non-target field-385 model changed")

    after = _audit_model11(patched_entries[TARGET_MODEL_INDEX])
    expected_groups = (
        (0x04, 119, new_f3_count),
        *before.mesh_groups[1:],
    )
    if after != Model11Audit(
        new_vertex_count,
        new_primitive_count,
        before.mesh_count,
        expected_groups,
        before.vertex_offset,
        new_mesh_offset,
        new_display_offset,
        before.instance_buffer_size + added_triangles * 0x14,
        before.model_size
        + len(added_vertex_bytes)
        + len(relocated_indices)
        + len(added_commands),
        before.minimum,
        before.maximum,
    ):
        raise MissileModelError(f"Patched model 11 audit mismatch: {after!r}")

    output_digest = _sha256(output)
    if output_digest != PATCHED_FIELD_385_MODELS_SHA256:
        raise MissileModelError(
            "Patched field-385 model archive is not deterministic: "
            f"{output_digest}"
        )
    return output


__all__ = [
    "MISSILE_CENTER_Y",
    "PATCHED_FIELD_385_MODELS_SHA256",
    "RACK_PLACEMENTS",
    "RETAIL_FIELD_385_MODELS_SHA256",
    "RackPlacement",
    "build_zeboim_missile_rack_geometry",
    "patch_zeboim_missile_racks",
]
