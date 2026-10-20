#!/usr/bin/env python3
"""Build native-textured doors for the defense archive.

Field 394 has no movable door object.  Its west and north walls instead contain
ordinary textured quads.  The dungeon builder removes one audited quad at each
exit and installs a pair of deliberately simple moving field models plus a
recessed reveal:

* the west bulkhead reconstructs model 8's ``88 x 132`` wall panel;
* the north lift reconstructs model 13's ``88 x 85`` lower wall panel.

The moving leaves are one-primitive models, like retail Zeboim sliding doors.
When closed, their UVs reconstruct the source polygons exactly.  The stationary
frames contain only dark jamb, lintel, and sill returns behind the original wall
planes.  No authored trim sits over neighbouring background art.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct


# Filled from deterministic builds below.  These are release contracts, not
# merely documentation: every public builder verifies both size and digest.
BULKHEAD_LEFT_MODEL_SHA256 = (
    "e6dee685c9856adc626d9785749fc37155362c76253d36e60b8850f7dc3beebc"
)
BULKHEAD_RIGHT_MODEL_SHA256 = (
    "7a869fff26c681a2164f2cdc197fa8396f5f7cf3b366b387dd2eee55d85a51d6"
)
BULKHEAD_FRAME_MODEL_SHA256 = (
    "3352ec9ab42d8a0741db97a8c2763887ef96f45ab280fcf273d3d17ff93f97b0"
)
NORTH_LIFT_LEFT_MODEL_SHA256 = (
    "f68dbae6a908826a625f1c4537a9317e575e4950b544fae235ebff2e4e9e6677"
)
NORTH_LIFT_RIGHT_MODEL_SHA256 = (
    "9fb6ae79e2f864b2f79f10f06ddabd0d7526d788dd8278e2f094a77731f0fc45"
)
NORTH_LIFT_FRAME_MODEL_SHA256 = (
    "00faa0d0d3bf6b6e6fd4e393b7cec160ef05b75779431032ecb99dfd753c78ee"
)

BULKHEAD_LEFT_MODEL_SIZE = 136
BULKHEAD_RIGHT_MODEL_SIZE = 136
BULKHEAD_FRAME_MODEL_SIZE = 396
NORTH_LIFT_LEFT_MODEL_SIZE = 136
NORTH_LIFT_RIGHT_MODEL_SIZE = 136
NORTH_LIFT_FRAME_MODEL_SIZE = 396

_F3_MESH_TYPE = 0x04
_FT4_MESH_TYPE = 0x0D
_MESH_UNKNOWN = 119
_F3_GPU_COMMAND = 0x20
_FT4_GPU_COMMAND = 0x2D

# These are the exact state commands active at field 394 model 8's removed
# west-wall primitive: TPAGE 0x0087 and CLUT 0x7800.
_TEXTURE_STATE = bytes.fromhex("87 00 00 C4 00 78 00 C8")

_WEST_WALL_X = -573
_WEST_REVEAL_BACK_X = -580
_WEST_REVEAL_FRONT_X = -574
_WEST_DOOR_TOP = -132
_WEST_DOOR_BOTTOM = 0
_WEST_DOOR_LOW_Z = -44
_WEST_DOOR_CENTRE_Z = 0
_WEST_DOOR_HIGH_Z = 44

_NORTH_WALL_Z = 308
_NORTH_REVEAL_FRONT_Z = 309
_NORTH_REVEAL_BACK_Z = 315
_NORTH_DOOR_TOP = -85
_NORTH_DOOR_BOTTOM = 0
_NORTH_DOOR_LOW_X = -44
_NORTH_DOOR_CENTRE_X = 0
_NORTH_DOOR_HIGH_X = 44

_REVEAL = (30, 36, 35)


@dataclass(frozen=True)
class _Triangle:
    indices: tuple[int, int, int, int]
    colour: tuple[int, int, int]


@dataclass(frozen=True)
class _Rectangle:
    corners: tuple[
        tuple[int, int, int],
        tuple[int, int, int],
        tuple[int, int, int],
        tuple[int, int, int],
    ]
    colour: tuple[int, int, int]


@dataclass(frozen=True)
class _TexturedQuad:
    corners: tuple[
        tuple[int, int, int],
        tuple[int, int, int],
        tuple[int, int, int],
        tuple[int, int, int],
    ]
    uv: tuple[int, int, int, int, int, int, int, int]


def _front_rectangle(
    x: int,
    y_bottom: int,
    y_top: int,
    z_low: int,
    z_high: int,
    colour: tuple[int, int, int],
) -> _Rectangle:
    """Return a wall-facing rectangle in the source quad's winding order."""

    return _Rectangle(
        (
            (x, y_bottom, z_high),
            (x, y_bottom, z_low),
            (x, y_top, z_high),
            (x, y_top, z_low),
        ),
        colour,
    )


def _textured_front_rectangle(
    x: int,
    y_bottom: int,
    y_top: int,
    z_low: int,
    z_high: int,
    uv: tuple[int, int, int, int, int, int, int, int],
) -> _TexturedQuad:
    return _TexturedQuad(
        (
            (x, y_bottom, z_high),
            (x, y_bottom, z_low),
            (x, y_top, z_high),
            (x, y_top, z_low),
        ),
        uv,
    )


def _textured_north_rectangle(
    z: int,
    y_bottom: int,
    y_top: int,
    x_low: int,
    x_high: int,
    uv: tuple[int, int, int, int, int, int, int, int],
) -> _TexturedQuad:
    """Return a north-wall quad in model 13 primitive 19's winding order."""

    return _TexturedQuad(
        (
            (x_high, y_bottom, z),
            (x_low, y_bottom, z),
            (x_high, y_top, z),
            (x_low, y_top, z),
        ),
        uv,
    )


def _rectangle_geometry(
    rectangles: tuple[_Rectangle, ...],
    *,
    vertex_base: int,
) -> tuple[
    tuple[tuple[int, int, int, int], ...],
    tuple[_Triangle, ...],
]:
    """Expand rectangles into checked two-sided F3 triangles."""

    vertices: list[tuple[int, int, int, int]] = []
    triangles: list[_Triangle] = []
    for rectangle in rectangles:
        base = vertex_base + len(vertices)
        vertices.extend((*corner, 0) for corner in rectangle.corners)
        for indices in (
            (base, base + 1, base + 2, 0),
            (base + 1, base + 3, base + 2, 0),
            (base + 2, base + 1, base, 0),
            (base + 2, base + 3, base + 1, 0),
        ):
            triangles.append(_Triangle(indices, rectangle.colour))
    return tuple(vertices), tuple(triangles)


def _set_model_bounds(
    output: bytearray,
    vertices: tuple[tuple[int, int, int, int], ...],
) -> None:
    block = 0x10
    for axis, minimum_offset, maximum_offset in (
        (0, block + 0x20, block + 0x28),
        (1, block + 0x22, block + 0x2A),
        (2, block + 0x24, block + 0x2C),
    ):
        struct.pack_into(
            "<h",
            output,
            minimum_offset,
            min(vertex[axis] for vertex in vertices),
        )
        struct.pack_into(
            "<h",
            output,
            maximum_offset,
            max(vertex[axis] for vertex in vertices),
        )


def _build_model(
    flat_rectangles: tuple[_Rectangle, ...],
    textured_quads: tuple[_TexturedQuad, ...],
) -> bytes:
    """Build one single-block Xenogears field model."""

    textured_vertices = tuple(
        (*corner, 0)
        for quad in textured_quads
        for corner in quad.corners
    )
    flat_vertices, triangles = _rectangle_geometry(
        flat_rectangles,
        vertex_base=len(textured_vertices),
    )
    vertices = textured_vertices + flat_vertices
    if not vertices or (not triangles and not textured_quads):
        raise RuntimeError("Defense-archive model geometry is incomplete")
    if len(vertices) > 0xFFFF or len(triangles) + len(textured_quads) > 0xFFFF:
        raise RuntimeError("Defense-archive model exceeds field-model limits")

    vertex_offset = 0x48
    vertex_data = b"".join(
        struct.pack("<hhhh", *vertex) for vertex in vertices
    )
    mesh_offset = vertex_offset + len(vertex_data)
    mesh_groups: list[bytes] = []
    if triangles:
        mesh_groups.append(
            struct.pack(
                "<BBH",
                _F3_MESH_TYPE,
                _MESH_UNKNOWN,
                len(triangles),
            )
            + b"".join(
                struct.pack("<HHHH", *triangle.indices)
                for triangle in triangles
            )
        )
    if textured_quads:
        mesh_groups.append(
            struct.pack(
                "<BBH",
                _FT4_MESH_TYPE,
                _MESH_UNKNOWN,
                len(textured_quads),
            )
            + b"".join(
                struct.pack(
                    "<HHHH",
                    index * 4,
                    index * 4 + 1,
                    index * 4 + 2,
                    index * 4 + 3,
                )
                for index in range(len(textured_quads))
            )
        )
    mesh_data = b"".join(mesh_groups)
    display_offset = mesh_offset + len(mesh_data)
    display_data = b"".join(
        bytes((*triangle.colour, _F3_GPU_COMMAND))
        for triangle in triangles
    )
    if textured_quads:
        display_data += _TEXTURE_STATE + b"".join(
            bytes((0, 0, 0, _FT4_GPU_COMMAND)) + bytes(quad.uv)
            for quad in textured_quads
        )

    output = bytearray(vertex_offset)
    struct.pack_into("<I", output, 0, 1)
    block = 0x10
    struct.pack_into("<H", output, block + 2, len(vertices))
    struct.pack_into(
        "<H",
        output,
        block + 4,
        len(triangles) + len(textured_quads),
    )
    struct.pack_into("<H", output, block + 6, len(mesh_groups))
    struct.pack_into("<I", output, block + 8, vertex_offset)
    struct.pack_into("<I", output, block + 0x0C, vertex_offset)
    struct.pack_into("<I", output, block + 0x10, mesh_offset)
    struct.pack_into("<I", output, block + 0x14, display_offset)
    struct.pack_into("<I", output, block + 0x18, 0)
    struct.pack_into("<I", output, block + 0x1C, 0)
    _set_model_bounds(output, vertices)
    struct.pack_into(
        "<I",
        output,
        block + 0x34,
        len(triangles) * 0x14 + len(textured_quads) * 0x28,
    )
    output.extend(vertex_data)
    output.extend(mesh_data)
    output.extend(display_data)
    return bytes(output)


def _build_west_leaf(*, screen_left: bool) -> bytes:
    """Split model 8's removed west-wall quad without adding foreground art."""

    if screen_left:
        z_low, z_high = _WEST_DOOR_CENTRE_Z, _WEST_DOOR_HIGH_Z
        u_high, u_low = 96, 112
    else:
        z_low, z_high = _WEST_DOOR_LOW_Z, _WEST_DOOR_CENTRE_Z
        u_high, u_low = 112, 128
    textured = (
        _textured_front_rectangle(
            _WEST_WALL_X,
            _WEST_DOOR_BOTTOM,
            _WEST_DOOR_TOP,
            z_low,
            z_high,
            (
                u_high,
                115,
                u_low,
                115,
                u_high,
                66,
                u_low,
                66,
            ),
        ),
    )
    return _build_model((), textured)


def _west_reveal_rectangles() -> tuple[_Rectangle, ...]:
    """Return four dark returns strictly behind the excised west-wall quad."""

    back = _WEST_REVEAL_BACK_X
    front = _WEST_REVEAL_FRONT_X
    top = _WEST_DOOR_TOP
    bottom = _WEST_DOOR_BOTTOM
    low = _WEST_DOOR_LOW_Z
    high = _WEST_DOOR_HIGH_Z
    return (
        _Rectangle(
            (
                (back, bottom, low),
                (front, bottom, low),
                (back, top, low),
                (front, top, low),
            ),
            _REVEAL,
        ),
        _Rectangle(
            (
                (front, bottom, high),
                (back, bottom, high),
                (front, top, high),
                (back, top, high),
            ),
            _REVEAL,
        ),
        _Rectangle(
            (
                (back, top, high),
                (back, top, low),
                (front, top, high),
                (front, top, low),
            ),
            _REVEAL,
        ),
        _Rectangle(
            (
                (front, bottom, high),
                (front, bottom, low),
                (back, bottom, high),
                (back, bottom, low),
            ),
            _REVEAL,
        ),
    )


def _build_west_frame() -> bytes:
    return _build_model(_west_reveal_rectangles(), ())


def _build_north_lift_leaf(*, screen_left: bool) -> bytes:
    """Split model 13 primitive 19 at U=176 without stretching its artwork."""

    if screen_left:
        x_low, x_high = _NORTH_DOOR_LOW_X, _NORTH_DOOR_CENTRE_X
        u_high, u_low = 176, 159
    else:
        x_low, x_high = _NORTH_DOOR_CENTRE_X, _NORTH_DOOR_HIGH_X
        u_high, u_low = 192, 176
    textured = (
        _textured_north_rectangle(
            _NORTH_WALL_Z,
            _NORTH_DOOR_BOTTOM,
            _NORTH_DOOR_TOP,
            x_low,
            x_high,
            (
                u_high,
                115,
                u_low,
                115,
                u_high,
                84,
                u_low,
                84,
            ),
        ),
    )
    return _build_model((), textured)


def _north_reveal_rectangles() -> tuple[_Rectangle, ...]:
    """Return lift-well returns strictly behind the removed north-wall panel."""

    front = _NORTH_REVEAL_FRONT_Z
    back = _NORTH_REVEAL_BACK_Z
    top = _NORTH_DOOR_TOP
    bottom = _NORTH_DOOR_BOTTOM
    low = _NORTH_DOOR_LOW_X
    high = _NORTH_DOOR_HIGH_X
    return (
        _Rectangle(
            (
                (low, bottom, front),
                (low, bottom, back),
                (low, top, front),
                (low, top, back),
            ),
            _REVEAL,
        ),
        _Rectangle(
            (
                (high, bottom, back),
                (high, bottom, front),
                (high, top, back),
                (high, top, front),
            ),
            _REVEAL,
        ),
        _Rectangle(
            (
                (low, top, back),
                (high, top, back),
                (low, top, front),
                (high, top, front),
            ),
            _REVEAL,
        ),
        _Rectangle(
            (
                (high, bottom, back),
                (low, bottom, back),
                (high, bottom, front),
                (low, bottom, front),
            ),
            _REVEAL,
        ),
    )


def _build_north_lift_frame() -> bytes:
    return _build_model(_north_reveal_rectangles(), ())


def _validated_model(
    result: bytes,
    *,
    label: str,
    expected_size: int,
    expected_sha256: str,
) -> bytes:
    digest = hashlib.sha256(result).hexdigest()
    if len(result) != expected_size or digest != expected_sha256:
        raise RuntimeError(
            f"{label} build is not deterministic: "
            f"{len(result)} bytes, SHA-256 {digest}"
        )
    return result


def build_defense_archive_bulkhead_left_leaf() -> bytes:
    """Return the west bulkhead's screen-left native-textured leaf."""

    return _validated_model(
        _build_west_leaf(screen_left=True),
        label="Defense-archive left bulkhead leaf",
        expected_size=BULKHEAD_LEFT_MODEL_SIZE,
        expected_sha256=BULKHEAD_LEFT_MODEL_SHA256,
    )


def build_defense_archive_bulkhead_right_leaf() -> bytes:
    """Return the west bulkhead's screen-right native-textured leaf."""

    return _validated_model(
        _build_west_leaf(screen_left=False),
        label="Defense-archive right bulkhead leaf",
        expected_size=BULKHEAD_RIGHT_MODEL_SIZE,
        expected_sha256=BULKHEAD_RIGHT_MODEL_SHA256,
    )


def build_defense_archive_bulkhead_frame() -> bytes:
    """Return the west bulkhead's stationary behind-wall reveal."""

    return _validated_model(
        _build_west_frame(),
        label="Defense-archive bulkhead frame",
        expected_size=BULKHEAD_FRAME_MODEL_SIZE,
        expected_sha256=BULKHEAD_FRAME_MODEL_SHA256,
    )


def build_defense_archive_north_lift_left_leaf() -> bytes:
    """Return the north lift's screen-left native-textured leaf."""

    return _validated_model(
        _build_north_lift_leaf(screen_left=True),
        label="Defense-archive north-lift left leaf",
        expected_size=NORTH_LIFT_LEFT_MODEL_SIZE,
        expected_sha256=NORTH_LIFT_LEFT_MODEL_SHA256,
    )


def build_defense_archive_north_lift_right_leaf() -> bytes:
    """Return the north lift's screen-right native-textured leaf."""

    return _validated_model(
        _build_north_lift_leaf(screen_left=False),
        label="Defense-archive north-lift right leaf",
        expected_size=NORTH_LIFT_RIGHT_MODEL_SIZE,
        expected_sha256=NORTH_LIFT_RIGHT_MODEL_SHA256,
    )


def build_defense_archive_north_lift_frame() -> bytes:
    """Return the north lift's stationary behind-wall reveal."""

    return _validated_model(
        _build_north_lift_frame(),
        label="Defense-archive north-lift frame",
        expected_size=NORTH_LIFT_FRAME_MODEL_SIZE,
        expected_sha256=NORTH_LIFT_FRAME_MODEL_SHA256,
    )


# Compatibility aliases keep an older in-progress caller importable while the
# field installer migrates from one moving slab to the explicit paired leaves.
BULKHEAD_MODEL_SHA256 = BULKHEAD_LEFT_MODEL_SHA256


def build_defense_archive_bulkhead() -> bytes:
    """Compatibility alias for the explicit model-14 left-leaf builder."""

    return build_defense_archive_bulkhead_left_leaf()


__all__ = [
    "BULKHEAD_FRAME_MODEL_SHA256",
    "BULKHEAD_FRAME_MODEL_SIZE",
    "BULKHEAD_LEFT_MODEL_SHA256",
    "BULKHEAD_LEFT_MODEL_SIZE",
    "BULKHEAD_MODEL_SHA256",
    "BULKHEAD_RIGHT_MODEL_SHA256",
    "BULKHEAD_RIGHT_MODEL_SIZE",
    "NORTH_LIFT_FRAME_MODEL_SHA256",
    "NORTH_LIFT_FRAME_MODEL_SIZE",
    "NORTH_LIFT_LEFT_MODEL_SHA256",
    "NORTH_LIFT_LEFT_MODEL_SIZE",
    "NORTH_LIFT_RIGHT_MODEL_SHA256",
    "NORTH_LIFT_RIGHT_MODEL_SIZE",
    "build_defense_archive_bulkhead",
    "build_defense_archive_bulkhead_frame",
    "build_defense_archive_bulkhead_left_leaf",
    "build_defense_archive_bulkhead_right_leaf",
    "build_defense_archive_north_lift_frame",
    "build_defense_archive_north_lift_left_leaf",
    "build_defense_archive_north_lift_right_leaf",
]
