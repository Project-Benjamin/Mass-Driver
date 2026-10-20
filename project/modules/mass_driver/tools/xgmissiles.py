#!/usr/bin/env python3
"""Add a native PS1 low-poly missile stockpile to Xenogears field 632.

The retail Anima Relic field used as the Mass Driver gallery donor has no
missile props.  This module performs a deliberately narrow model-stream edit:
it adds flat-colour POLY_F3 geometry to the already-rendered static model 0.
No texture page, field entity, walkmesh, or ATEL script is changed.

The patch is locked to the audited retail model stream so a different field
cannot be corrupted accidentally.  The output remains a normal Xenogears
model archive and can be packed by :mod:`tools.xgfield` without special engine
code.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import struct
import sys
from typing import Iterable, Sequence


RETAIL_FIELD_632_MODELS_SHA256 = (
    "22ae1aaab59da6954e68e2b740c05a1a6a8f8c35aa1cccd432ab3ec2743da8b5"
)

# Eight warheads in two ordered banks on the side platforms.  The required
# path through field 632 is the narrow central aisle around x=-84..132, so the
# props do not cover it.  The audited platform deck is Y=-180 and negative Y
# is up; anchoring at zero would bury most of each missile inside the deck.
MISSILE_POSITIONS: tuple[tuple[int, int], ...] = (
    (-790, -990),
    (-550, -990),
    (-790, -1260),
    (-550, -1260),
    (380, -1000),
    (650, -1000),
    (380, -1270),
    (650, -1270),
)
PLATFORM_FLOOR_Y = -180

# Muted colours sampled to sit beside the donor's dark metal and oxide-red
# palette.  These are native 24-bit flat primitive colours, not modern assets.
LOWER_BODY = (66, 73, 69)
WARNING_BAND = (105, 48, 37)
UPPER_BODY = (79, 86, 81)
NOSE = (55, 62, 59)
FINS = (44, 50, 48)


class MissileModelError(RuntimeError):
    """Raised when the donor model does not match the audited retail layout."""


@dataclass(frozen=True)
class Triangle:
    indices: tuple[int, int, int, int]
    colour: tuple[int, int, int]


@dataclass(frozen=True)
class MissileGeometry:
    vertices: tuple[tuple[int, int, int, int], ...]
    triangles: tuple[Triangle, ...]


@dataclass(frozen=True)
class Model0Audit:
    vertex_count: int
    primitive_count: int
    triangle_count: int
    quad_count: int
    vertex_offset: int
    mesh_offset: int
    display_list_offset: int
    instance_buffer_size: int


def _u16(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(data):
        raise MissileModelError(f"u16 outside model at 0x{offset:X}")
    return struct.unpack_from("<H", data, offset)[0]


def _u32(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise MissileModelError(f"u32 outside model at 0x{offset:X}")
    return struct.unpack_from("<I", data, offset)[0]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _model_spans(data: bytes) -> tuple[tuple[int, int], ...]:
    if len(data) < 8:
        raise MissileModelError("Model archive is shorter than its header")
    count = _u32(data, 0)
    if count == 0 or count > 256:
        raise MissileModelError(f"Implausible model count: {count}")
    table_end = 4 + count * 4
    if table_end > len(data):
        raise MissileModelError("Model offset table is truncated")
    offsets = tuple(_u32(data, 4 + index * 4) for index in range(count))
    if offsets != tuple(sorted(offsets)) or len(set(offsets)) != len(offsets):
        raise MissileModelError("Model offsets are not strictly increasing")
    if offsets[0] < table_end or any(offset % 4 for offset in offsets):
        raise MissileModelError("Model offsets overlap the header or are unaligned")
    if offsets[-1] >= len(data):
        raise MissileModelError("Last model starts outside the archive")
    ends = offsets[1:] + (len(data),)
    return tuple(zip(offsets, ends, strict=True))


def _audit_model0(model: bytes) -> Model0Audit:
    if len(model) < 72:
        raise MissileModelError("Model 0 is too short for one block")
    if _u32(model, 0) != 1:
        raise MissileModelError("Field 632 model 0 no longer has exactly one block")

    block = 0x10
    vertex_count = _u16(model, block + 2)
    primitive_count = _u16(model, block + 4)
    mesh_count = _u16(model, block + 6)
    vertex_offset = _u32(model, block + 8)
    normal_offset = _u32(model, block + 0x0C)
    mesh_offset = _u32(model, block + 0x10)
    display_offset = _u32(model, block + 0x14)
    dynamic_offset = _u32(model, block + 0x1C)
    instance_size = _u32(model, block + 0x34)

    if (
        vertex_offset != 72
        or normal_offset != vertex_offset
        or dynamic_offset != 0
        or mesh_count != 2
    ):
        raise MissileModelError("Field 632 model 0 block layout is not the audited layout")
    if vertex_offset + vertex_count * 8 != mesh_offset:
        raise MissileModelError("Vertex and mesh spans are not contiguous")

    cursor = mesh_offset
    groups: list[tuple[int, int]] = []
    for _ in range(mesh_count):
        if cursor + 4 > display_offset:
            raise MissileModelError("Mesh group header overlaps the display list")
        primitive_type, _unknown, count = struct.unpack_from("<BBH", model, cursor)
        cursor += 4
        groups.append((primitive_type, count))
        cursor += count * 8
    if cursor != display_offset:
        raise MissileModelError("Mesh groups do not end at the display list")
    if groups[0][0] != 0x04 or groups[1][0] != 0x0C:
        raise MissileModelError(f"Unexpected model 0 primitive groups: {groups!r}")
    triangle_count = groups[0][1]
    quad_count = groups[1][1]
    if triangle_count + quad_count != primitive_count:
        raise MissileModelError("Primitive header count disagrees with mesh groups")
    if display_offset + primitive_count * 4 != len(model):
        raise MissileModelError("Model 0 display list is not four bytes per flat primitive")
    if instance_size != triangle_count * 0x14 + quad_count * 0x18:
        raise MissileModelError("Model 0 instance buffer size is inconsistent")
    return Model0Audit(
        vertex_count,
        primitive_count,
        triangle_count,
        quad_count,
        vertex_offset,
        mesh_offset,
        display_offset,
        instance_size,
    )


def _triangle(
    output: list[Triangle], a: int, b: int, c: int, colour: tuple[int, int, int]
) -> None:
    output.append(Triangle((a, b, c, 0), colour))


def _one_missile(center_x: int, center_z: int) -> MissileGeometry:
    """Create one six-sided, banded Zeboim-style ballistic missile."""

    vertices: list[tuple[int, int, int, int]] = []
    triangles: list[Triangle] = []

    # Integer hexagon points with radius 42.  Repeating the ring at each level
    # permits a different primitive colour for the central warning band.
    ring_xz = ((42, 0), (21, 36), (-21, 36), (-42, 0), (-21, -36), (21, -36))
    ring_levels = tuple(
        PLATFORM_FLOOR_Y - height for height in (0, 130, 180, 270)
    )
    rings: list[tuple[int, ...]] = []
    for y in ring_levels:
        ring: list[int] = []
        for dx, dz in ring_xz:
            ring.append(len(vertices))
            vertices.append((center_x + dx, y, center_z + dz, 0))
        rings.append(tuple(ring))

    segment_colours = (LOWER_BODY, WARNING_BAND, UPPER_BODY)
    for lower, upper, colour in zip(
        rings[:-1], rings[1:], segment_colours, strict=True
    ):
        for side in range(6):
            next_side = (side + 1) % 6
            # Outward-facing winding for the coordinate system used by the
            # retail field model.
            _triangle(triangles, lower[side], lower[next_side], upper[side], colour)
            _triangle(
                triangles,
                lower[next_side],
                upper[next_side],
                upper[side],
                colour,
            )

    nose_tip = len(vertices)
    vertices.append((center_x, PLATFORM_FLOOR_Y - 390, center_z, 0))
    for side in range(6):
        _triangle(
            triangles,
            rings[-1][side],
            rings[-1][(side + 1) % 6],
            nose_tip,
            NOSE,
        )

    base_center = len(vertices)
    vertices.append((center_x, PLATFORM_FLOOR_Y, center_z, 0))
    for side in range(6):
        # Down-facing cap.  It is mostly hidden by the platform, but closes the
        # silhouette when a camera angle sees beneath a raised bank.
        _triangle(
            triangles,
            rings[0][(side + 1) % 6],
            rings[0][side],
            base_center,
            FINS,
        )

    # Four broad fins.  Each plane is emitted in both directions because a
    # zero-thickness fin must remain visible from either side of the room.
    for direction_x, direction_z, tangent_x, tangent_z in (
        (1, 0, 0, 1),
        (-1, 0, 0, -1),
        (0, 1, -1, 0),
        (0, -1, 1, 0),
    ):
        root_low = len(vertices)
        vertices.append(
            (
                center_x + direction_x * 38 + tangent_x * 10,
                PLATFORM_FLOOR_Y,
                center_z + direction_z * 38 + tangent_z * 10,
                0,
            )
        )
        root_high = len(vertices)
        vertices.append(
            (
                center_x + direction_x * 38 - tangent_x * 10,
                PLATFORM_FLOOR_Y - 105,
                center_z + direction_z * 38 - tangent_z * 10,
                0,
            )
        )
        outer = len(vertices)
        vertices.append(
            (
                center_x + direction_x * 82,
                PLATFORM_FLOOR_Y + 6,
                center_z + direction_z * 82,
                0,
            )
        )
        _triangle(triangles, root_low, root_high, outer, FINS)
        _triangle(triangles, outer, root_high, root_low, FINS)

    if len(vertices) != 38 or len(triangles) != 56:
        raise AssertionError("Internal missile geometry count changed unexpectedly")
    return MissileGeometry(tuple(vertices), tuple(triangles))


def build_stockpile_geometry(
    positions: Iterable[tuple[int, int]] = MISSILE_POSITIONS,
) -> MissileGeometry:
    vertices: list[tuple[int, int, int, int]] = []
    triangles: list[Triangle] = []
    for center_x, center_z in positions:
        missile = _one_missile(center_x, center_z)
        base = len(vertices)
        vertices.extend(missile.vertices)
        triangles.extend(
            Triangle(
                (
                    triangle.indices[0] + base,
                    triangle.indices[1] + base,
                    triangle.indices[2] + base,
                    0,
                ),
                triangle.colour,
            )
            for triangle in missile.triangles
        )
    return MissileGeometry(tuple(vertices), tuple(triangles))


def patch_mass_driver_stockpile(models: bytes) -> bytes:
    """Return field 632's model stream with eight visible missile props added."""

    digest = _sha256(models)
    if digest != RETAIL_FIELD_632_MODELS_SHA256:
        raise MissileModelError(
            "Missile patch requires the audited retail field 632 model stream; "
            f"found SHA-256 {digest}"
        )
    spans = _model_spans(models)
    if len(spans) != 5:
        raise MissileModelError(f"Expected five field 632 models, found {len(spans)}")
    model_payloads = [models[start:end] for start, end in spans]
    model0 = model_payloads[0]
    audit = _audit_model0(model0)
    if (
        audit.vertex_count,
        audit.primitive_count,
        audit.triangle_count,
        audit.quad_count,
    ) != (498, 345, 38, 307):
        raise MissileModelError(f"Unexpected retail model 0 counts: {audit!r}")

    stockpile = build_stockpile_geometry()
    added_vertex_bytes = b"".join(
        struct.pack("<hhhh", *vertex) for vertex in stockpile.vertices
    )
    added_index_bytes = b"".join(
        struct.pack("<HHHH", *triangle.indices) for triangle in stockpile.triangles
    )
    added_commands = b"".join(
        bytes((*triangle.colour, 0x20)) for triangle in stockpile.triangles
    )

    old_vertices = model0[audit.vertex_offset : audit.mesh_offset]
    cursor = audit.mesh_offset
    triangle_type, triangle_unknown, old_triangle_count = struct.unpack_from(
        "<BBH", model0, cursor
    )
    cursor += 4
    old_triangle_indices = model0[cursor : cursor + old_triangle_count * 8]
    cursor += old_triangle_count * 8
    quad_type, quad_unknown, old_quad_count = struct.unpack_from("<BBH", model0, cursor)
    old_quad_group = model0[cursor : audit.display_list_offset]

    added_vertices = len(stockpile.vertices)
    added_triangles = len(stockpile.triangles)
    vertex_count = audit.vertex_count + added_vertices
    triangle_count = audit.triangle_count + added_triangles
    primitive_count = audit.primitive_count + added_triangles
    if vertex_count > 0xFFFF or triangle_count > 0xFFFF or primitive_count > 0xFFFF:
        raise MissileModelError("Patched model count exceeds the retail 16-bit fields")

    # Indices generated above are stockpile-local; relocate them after the
    # donor's existing vertex table.
    relocated_indices = bytearray()
    for offset in range(0, len(added_index_bytes), 8):
        a, b, c, unused = struct.unpack_from("<HHHH", added_index_bytes, offset)
        relocated_indices.extend(
            struct.pack(
                "<HHHH",
                a + audit.vertex_count,
                b + audit.vertex_count,
                c + audit.vertex_count,
                unused,
            )
        )

    mesh = bytearray(struct.pack("<BBH", triangle_type, triangle_unknown, triangle_count))
    mesh.extend(old_triangle_indices)
    mesh.extend(relocated_indices)
    mesh.extend(old_quad_group)

    old_triangle_commands_end = audit.display_list_offset + audit.triangle_count * 4
    display = bytearray(
        model0[audit.display_list_offset : old_triangle_commands_end]
    )
    display.extend(added_commands)
    display.extend(model0[old_triangle_commands_end:])

    new_model0 = bytearray(model0[: audit.vertex_offset])
    new_model0.extend(old_vertices)
    new_model0.extend(added_vertex_bytes)
    new_mesh_offset = len(new_model0)
    new_model0.extend(mesh)
    new_display_offset = len(new_model0)
    new_model0.extend(display)

    block = 0x10
    struct.pack_into("<H", new_model0, block + 2, vertex_count)
    struct.pack_into("<H", new_model0, block + 4, primitive_count)
    struct.pack_into("<I", new_model0, block + 0x10, new_mesh_offset)
    struct.pack_into("<I", new_model0, block + 0x14, new_display_offset)
    struct.pack_into(
        "<I",
        new_model0,
        block + 0x34,
        audit.instance_buffer_size + added_triangles * 0x14,
    )

    all_vertices = [
        struct.unpack_from("<hhhh", new_model0, audit.vertex_offset + index * 8)
        for index in range(vertex_count)
    ]
    for axis, minimum_offset, maximum_offset in (
        (0, block + 0x20, block + 0x28),
        (1, block + 0x22, block + 0x2A),
        (2, block + 0x24, block + 0x2C),
    ):
        struct.pack_into("<h", new_model0, minimum_offset, min(v[axis] for v in all_vertices))
        struct.pack_into("<h", new_model0, maximum_offset, max(v[axis] for v in all_vertices))

    model_payloads[0] = bytes(new_model0)
    output = bytearray(4 + len(model_payloads) * 4)
    struct.pack_into("<I", output, 0, len(model_payloads))
    for index, payload in enumerate(model_payloads):
        struct.pack_into("<I", output, 4 + index * 4, len(output))
        output.extend(payload)

    # Parse the result and verify the exact changes before returning it.
    patched_spans = _model_spans(bytes(output))
    patched_payloads = [bytes(output[start:end]) for start, end in patched_spans]
    patched_audit = _audit_model0(patched_payloads[0])
    expected = Model0Audit(
        vertex_count,
        primitive_count,
        triangle_count,
        audit.quad_count,
        audit.vertex_offset,
        new_mesh_offset,
        new_display_offset,
        audit.instance_buffer_size + added_triangles * 0x14,
    )
    if patched_audit != expected:
        raise MissileModelError(
            f"Internal patched-model audit mismatch: {patched_audit!r} != {expected!r}"
        )
    if patched_payloads[1:] != model_payloads[1:]:
        raise MissileModelError("A non-target model changed during missile insertion")
    if quad_type != 0x0C or old_quad_count != audit.quad_count or quad_unknown != 119:
        raise MissileModelError("Retail quad mesh metadata changed unexpectedly")
    return bytes(output)


def command_patch(args: argparse.Namespace) -> int:
    source = Path(args.input)
    destination = Path(args.output)
    if destination.exists() and not args.force:
        raise MissileModelError(f"Refusing to overwrite {destination}; pass --force")
    patched = patch_mass_driver_stockpile(source.read_bytes())
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(patched)
    geometry = build_stockpile_geometry()
    print(
        f"Patched {source.resolve()} -> {destination.resolve()} "
        f"({len(MISSILE_POSITIONS)} missiles, {len(geometry.vertices)} vertices, "
        f"{len(geometry.triangles)} triangles, SHA-256 {_sha256(patched)})"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="retail field 632 02_models.bin")
    parser.add_argument("output", type=Path, help="patched model component")
    parser.add_argument("--force", action="store_true")
    parser.set_defaults(handler=command_patch)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (MissileModelError, OSError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
