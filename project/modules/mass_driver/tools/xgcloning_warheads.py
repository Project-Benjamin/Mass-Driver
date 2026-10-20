#!/usr/bin/env python3
"""Replace field 673's six cloning vats with grounded low-poly warheads.

Field 673 is the retail Karellen/Karen cloning-chamber flashback. Its six vats occupy 24 static
header nodes and use model entries 0..7. This transform parks those glass-vat
nodes below the floor, appends one self-contained warhead as model 20, and
reuses six of the now-free opaque static nodes as its placements. The original
20 model entries, room geometry, textures, walkmesh, and lighting remain
byte-identical.

The replacement uses ordinary untextured POLY_F3 primitives, so it consumes
no texture page, CLUT, or VRAM space. Its silhouette and palette follow
``assets/mass_driver/cloning-chamber-warhead-concept-v1.png`` while remaining
deliberately coarser than that concept sheet for authentic PS1 field scale.
Each shell now seats in a floor-flush plinth with four visible buttress feet;
raised seams, access panels, and stepped armour break up the broad surfaces
without introducing texture or transparency artifacts.

The active archive-reader transform operates only on that checked
warhead-patched result. It transplants field 373's authentic model-7 Zeboim
station into retired model slot 0, lowers the original hanging installation to
the floor beside the east-side interaction point, and turns its screen toward
the player approach. Its used 8-bpp texture islands are losslessly repacked
into field 673's native fourth upload while retaining the donor's full
256-colour palette in row 488. Those slots belonged only to cloning-vat models
whose nodes are parked below the floor. Keeping the fourth upload's original
header, rectangle, chunk table, padding, and total byte count makes those
pixels survive the live field/actor VRAM allocator. Retired slot 1 is compacted
with a harmless model copy so the playable room remains below the field-loader
ceiling; model entries 2 onward and all active field-673 scenery remain
byte-identical.

The older native three-piece service-pedestal helper remains below solely for
historical release verification and backwards-compatible tests.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import struct

from modules.mass_driver.tools.xgmissiles import _model_spans


RETAIL_FIELD_673_MODELS_SHA256 = (
    "bf8ad4d546485459761b3db1a934716d391216665a1ed982ccf2d7095db5e668"
)
RETAIL_FIELD_673_HEADER_SHA256 = (
    "c3e085b9c1b0c165bda0b71953380d63c7cda54fa5ebca70e848bff8599bb62d"
)

PATCHED_FIELD_673_MODELS_SHA256 = (
    "26a636bdab842d2eb08deb04514f86c630b0131be855235e3eb9f973d1c088c3"
)
PATCHED_FIELD_673_HEADER_SHA256 = (
    "5c00edf43c3673ebf86cdaa782dd8d4d801797ae03d7394db26e11d1953155f3"
)

ARCHIVE_PEDESTAL_FIELD_673_MODELS_SHA256 = (
    "640a17fb3ec761baad7ef03f624c74d6ceb95e626d5bc7e6024c18211acad61c"
)
ARCHIVE_PEDESTAL_FIELD_673_MODELS_SIZE = 62780
ARCHIVE_PEDESTAL_FIELD_673_HEADER_SHA256 = (
    "501643326421898886e22bee10ff3d714964b3c76c03e4647c80f74722acb06b"
)
ARCHIVE_PEDESTAL_FIELD_673_GRAPHICS_SHA256 = (
    "e58a4c0f5aacffbf500c31879e0795238af402d3bfb8d83dfca46df454dca2ed"
)
ARCHIVE_PEDESTAL_FIELD_673_GRAPHICS_SIZE = 102400
RETAIL_FIELD_673_GRAPHICS_SHA256 = (
    "e58a4c0f5aacffbf500c31879e0795238af402d3bfb8d83dfca46df454dca2ed"
)
RETAIL_FIELD_673_GRAPHICS_SIZE = 102400

F3_MESH_TYPE = 0x04
F3_MESH_UNKNOWN = 119
F3_GPU_COMMAND = 0x20
FACET_COUNT = 8

WARHEAD_MODEL_INDEX = 20
WARHEAD_FLOOR_Y = 0
WARHEAD_FOOTPRINT_RADIUS = 72
WARHEAD_NODE_INDICES: tuple[int, ...] = (34, 35, 36, 37, 38, 39)
WARHEAD_PLACEMENTS: tuple[tuple[int, int, int], ...] = (
    (661, 0, -396),
    (661, 0, 396),
    (0, 0, -396),
    (-661, 0, -396),
    (-661, 0, 396),
    (0, 0, 396),
)
PARKED_VAT_NODE_INDICES: tuple[int, ...] = (
    *range(22, 34),
    *range(40, 46),
)
PARKED_VAT_Y = 2048

CLONING_ARCHIVE_PEDESTAL_MODEL_INDICES = (2, 4, 6)
CLONING_ARCHIVE_PEDESTAL_MODEL_SHA256S = (
    "f7babe13aedd2b6ce2bb947645b02e346bf57972f7b4c3f6b78c481e116cc426",
    "2496f1d24739250392224268d62523d16f948dd2cd2eb74887116887d9d3f0ba",
    "5915e5db95fa06d806076d73b76acb1844e4f05c08fe30a2f84e52bc31d89f83",
)
CLONING_ARCHIVE_PEDESTAL_NODE_INDICES = (22, 23, 24)
CLONING_ARCHIVE_PEDESTAL_SOURCE_NODE_MODELS = (0, 1, 2)
CLONING_ARCHIVE_PEDESTAL_NODE_FLAGS = (0x0000, 0x0010, 0x8000)
CLONING_ARCHIVE_PEDESTAL_PLACEMENT = (1161, 0, 396)
CLONING_ARCHIVE_PEDESTAL_VISUAL_CENTER = (500, 0, 0)
CLONING_ARCHIVE_PEDESTAL_WORLD_BOUNDS = (466, 534, -197, 44, -36, 35)
CLONING_ARCHIVE_PEDESTAL_Y_ROTATION = 0
CLONING_ARCHIVE_PEDESTAL_RETIRED_MODEL_INDICES = (0, 1)
CLONING_ARCHIVE_PEDESTAL_COMPACTION_MODEL_INDEX = 6
CLONING_ARCHIVE_PEDESTAL_COMPACTION_MODEL_SHA256 = (
    "5915e5db95fa06d806076d73b76acb1844e4f05c08fe30a2f84e52bc31d89f83"
)
ARCHIVE_TERMINAL_SCREEN_NORMAL = (-1, 0, 0)

# The selected replacement for the reserve-magazine archive reader is the
# authentic green-lit Zeboim station from retail field 373, static node 44 /
# model 7. Its model uses only the lower 64 rows of one 8-bit texture page.
# Field 673's fourth native graphics upload and CLUT row 488 serve only parked
# cloning-vat models 2/3 after the warhead conversion, so reuse that registered
# runtime allocation for a lossless atlas of the station's used texture islands
# and the full retail palette. The fourth upload's complete structure remains
# byte-identical to retail field 673; only its row payload changes. Appending or resizing MIM
# rectangles is deliberately forbidden: DuckStation's live VRAM showed that
# unregistered allocations do not survive the field/actor allocator even
# though an offline replay of the MIM stream appears correct.
ZEBOIM_STATION_DONOR_HEADER_SIZE = 1376
ZEBOIM_STATION_DONOR_HEADER_SHA256 = (
    "1f1f84faed6efe45e8eb83d0c7b0980d9cfe7e2473155ef11c2f276b3320693b"
)
ZEBOIM_STATION_DONOR_MODELS_SIZE = 19068
ZEBOIM_STATION_DONOR_MODELS_SHA256 = (
    "0aa722c57d0ee704124055b4f2ed4edca349de7d245c302be3041c99d306089c"
)
ZEBOIM_STATION_DONOR_GRAPHICS_SIZE = 180224
ZEBOIM_STATION_DONOR_GRAPHICS_SHA256 = (
    "4d411b597b06d9901789c73ffdb1e7dcaca4fb526b41d806fd01d5abf88a8d28"
)
ZEBOIM_STATION_SOURCE_NODE_INDEX = 44
ZEBOIM_STATION_SOURCE_MODEL_INDEX = 7
ZEBOIM_STATION_SOURCE_MODEL_SIZE = 2524
ZEBOIM_STATION_SOURCE_MODEL_SHA256 = (
    "c7791afbe919aece2096c863e0cdff9677b091872e147d10bdbbdc37799d6c1c"
)
ZEBOIM_STATION_RELOCATED_MODEL_SHA256 = (
    "793603ccbe854180cc28a69810696bf3713a394168f06454a83c20693846a015"
)
ZEBOIM_STATION_TARGET_MODEL_INDEX = 0
ZEBOIM_STATION_TARGET_NODE_INDEX = 22
ZEBOIM_STATION_NODE_FLAGS = 0x0010
ZEBOIM_STATION_PLACEMENT = (486, 106, -41)
ZEBOIM_STATION_Y_ROTATION = 0x0600
ZEBOIM_STATION_VISUAL_CENTER = (500, -76, 0)
ZEBOIM_STATION_WORLD_BOUNDS = (461, 539, -152, 0, -40, 39)
ZEBOIM_STATION_SCREEN_NORMAL = (-1, 0, 0)
ZEBOIM_STATION_SOURCE_TPAGES = (0x0087, 0x00A7)
ZEBOIM_STATION_RELOCATED_TPAGES = (0x0088, 0x00A8)
ZEBOIM_STATION_SOURCE_CLUT = 0x7980
ZEBOIM_STATION_RELOCATED_CLUT = 0x7A00
ZEBOIM_STATION_SOURCE_TEXTURE_RECT = (448, 192, 65, 64)
ZEBOIM_STATION_SOURCE_TEXTURE_PIXEL_WIDTH = 130
ZEBOIM_STATION_TARGET_TEXTURE_PIXEL_WIDTH = 80
ZEBOIM_STATION_TARGET_TEXTURE_RECT = (512, 192, 40, 64)
# Each source entry is (u, v, width, height); its paired target entry is
# (u, v-relative-to-192). The 21 conservative UV islands occupy 4,288 texels,
# fit within 78x62 of the native 80x64 slot, and preserve every texel that any
# station primitive can sample.
ZEBOIM_STATION_TEXTURE_ATLAS = (
    ((16, 205, 18, 50), (0, 0)),
    ((43, 237, 24, 16), (51, 29)),
    ((35, 205, 7, 50), (28, 0)),
    ((72, 199, 58, 6), (0, 50)),
    ((43, 220, 16, 16), (35, 28)),
    ((60, 220, 12, 16), (35, 0)),
    ((11, 192, 16, 12), (35, 16)),
    ((32, 192, 18, 10), (54, 0)),
    ((5, 205, 10, 17), (51, 12)),
    ((102, 192, 28, 6), (0, 56)),
    ((72, 192, 29, 6), (28, 56)),
    ((51, 192, 20, 10), (58, 50)),
    ((43, 203, 10, 16), (18, 25)),
    ((62, 203, 7, 16), (18, 9)),
    ((54, 203, 7, 16), (61, 12)),
    ((5, 246, 10, 9), (18, 0)),
    ((103, 219, 16, 5), (35, 44)),
    ((5, 234, 9, 8), (68, 12)),
    ((5, 192, 5, 12), (72, 0)),
    ((0, 243, 4, 13), (47, 0)),
    ((28, 192, 3, 12), (51, 0)),
)
ZEBOIM_STATION_SOURCE_CLUT_RECT = (0, 486, 256, 1)
ZEBOIM_STATION_TARGET_CLUT_RECT = (0, 488, 256, 1)
ZEBOIM_STATION_RETIRED_TEXTURE_RECT = ZEBOIM_STATION_TARGET_TEXTURE_RECT
ZEBOIM_STATION_RETIRED_CLUT_FILE_OFFSET = 0x1800
ZEBOIM_STATION_RETIRED_GRAPHICS_BLOCK_OFFSET = 0x17000
ZEBOIM_STATION_RETIRED_GRAPHICS_BLOCK_SHA256 = (
    "c3dc592bbe6b96648053a3afdc970651355d897684934f4f1bb70680ea342c1a"
)
ZEBOIM_STATION_RETIRED_CLUT_ROWS_SHA256 = (
    "0edb29e1f1283c3d27a8e93aaa63ebd1540c0800d31b146a44fa2cfe08cae6ab"
)
ZEBOIM_STATION_TEXTURE_ROWS_SHA256 = (
    "43fc5607fa79b876453a8e100ed322c0cec4aa705d7edb66d3d0ab0020489df6"
)
ZEBOIM_STATION_ATLAS_TEXTURE_ROWS_SHA256 = (
    "a6ee4c693587c5f68d8777ef60007ca178a744cad66b9d92ea5a85dfe424f129"
)
ZEBOIM_STATION_CLUT_ROWS_SHA256 = (
    "7754aac52c72639ecd632cbac7a46c73b0a2873ca1091dcb67325ba2508c1065"
)
ZEBOIM_STATION_TEXTURE_UPLOAD_SHA256 = (
    "5dd2f0bd4cf84a1cfd51c699bdaded58c6cebbda597e3c7e4852edbfcd25a124"
)
ZEBOIM_STATION_FIELD_673_HEADER_SHA256 = (
    "634cf058c2cc989b4dda828884b824ce0b14a35bdba9d1dcde1b1b19c14e146e"
)
ZEBOIM_STATION_FIELD_673_MODELS_SIZE = 64860
ZEBOIM_STATION_FIELD_673_MODELS_SHA256 = (
    "daa9d7d7f759c2c04bcbc2da7d2319d1ade0fd70f85afb68f00cf9be2cbf4207"
)
ZEBOIM_STATION_FIELD_673_GRAPHICS_SIZE = 102400
ZEBOIM_STATION_FIELD_673_GRAPHICS_SHA256 = (
    "395e3907406464ec1746cba8097008a19eebf05babf9e19a34bdef71d9832f50"
)

COLLAR = (46, 51, 48)
SHOULDER = (72, 74, 62)
BODY = (72, 82, 84)
BAND_EDGE = (43, 48, 45)
WARNING_BAND = (126, 70, 38)
NOSE = (88, 87, 70)
MOUNT = (42, 47, 43)
FOOT = (34, 39, 37)
ACCESS_PANEL = (31, 37, 38)
SEAM = (28, 33, 31)
FACET_LIGHT = (-6, 1, 5, -1, -7, -2, 4, 0)

ARCHIVE_TERMINAL_BASE = (33, 39, 36)
ARCHIVE_TERMINAL_BODY = (55, 62, 54)
ARCHIVE_TERMINAL_EDGE = (26, 32, 29)
ARCHIVE_TERMINAL_PANEL = (44, 51, 45)
ARCHIVE_TERMINAL_SCREEN_COLOUR = (28, 102, 91)
ARCHIVE_TERMINAL_SCREEN_DARK = (18, 48, 44)
ARCHIVE_TERMINAL_STATUS = (132, 83, 35)
ARCHIVE_TERMINAL_MODEL_SIZE = 1604
ARCHIVE_TERMINAL_MODEL_SHA256 = (
    "ea8ba6b044f48b2d5e8c5f23cce0dd3fe7fab7c9082d292fe3296bd74635cf6c"
)


class CloningWarheadModelError(RuntimeError):
    """Raised when the cloning-chamber donor no longer matches its audit."""


@dataclass(frozen=True)
class Triangle:
    indices: tuple[int, int, int, int]
    colour: tuple[int, int, int]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _shade(
    colour: tuple[int, int, int],
    facet: int,
) -> tuple[int, int, int]:
    delta = FACET_LIGHT[facet % len(FACET_LIGHT)]
    return tuple(max(0, min(255, channel + delta)) for channel in colour)


def _ring(
    center_x: int,
    center_z: int,
    y: int,
    radius: int,
) -> tuple[tuple[int, int, int, int], ...]:
    return tuple(
        (
            center_x
            + int(round(math.cos(2.0 * math.pi * index / FACET_COUNT) * radius)),
            y,
            center_z
            + int(round(math.sin(2.0 * math.pi * index / FACET_COUNT) * radius)),
            0,
        )
        for index in range(FACET_COUNT)
    )


def _append_ring_span(
    triangles: list[Triangle],
    lower_start: int,
    upper_start: int,
    colour: tuple[int, int, int],
) -> None:
    for facet in range(FACET_COUNT):
        following = (facet + 1) % FACET_COUNT
        a = lower_start + facet
        b = lower_start + following
        c = upper_start + facet
        d = upper_start + following
        shaded = _shade(colour, facet)
        triangles.append(Triangle((a, c, b, 0), shaded))
        triangles.append(Triangle((b, c, d, 0), shaded))


def _append_geometry(
    vertices: list[tuple[int, int, int, int]],
    triangles: list[Triangle],
    added_vertices: tuple[tuple[int, int, int, int], ...],
    added_triangles: tuple[Triangle, ...],
) -> None:
    base = len(vertices)
    vertices.extend(added_vertices)
    triangles.extend(
        Triangle(
            (
                triangle.indices[0] + base,
                triangle.indices[1] + base,
                triangle.indices[2] + base,
                triangle.indices[3],
            ),
            triangle.colour,
        )
        for triangle in added_triangles
    )


def _radial_strip(
    center_x: int,
    center_z: int,
    *,
    angle_degrees: float,
    radius: float,
    half_width: float,
    bottom_y: int,
    top_y: int,
    colour: tuple[int, int, int],
    shade_index: int,
) -> tuple[tuple[tuple[int, int, int, int], ...], tuple[Triangle, ...]]:
    angle = math.radians(angle_degrees)
    radial_x = math.cos(angle)
    radial_z = math.sin(angle)
    tangent_x = -radial_z
    tangent_z = radial_x

    def point(y: int, tangent_distance: float) -> tuple[int, int, int, int]:
        return (
            center_x
            + int(
                round(
                    radial_x * radius + tangent_x * tangent_distance
                )
            ),
            y,
            center_z
            + int(
                round(
                    radial_z * radius + tangent_z * tangent_distance
                )
            ),
            0,
        )

    vertices = (
        point(bottom_y, -half_width),
        point(bottom_y, half_width),
        point(top_y, -half_width),
        point(top_y, half_width),
    )
    shaded = _shade(colour, shade_index)
    triangles = (
        Triangle((0, 2, 1, 0), shaded),
        Triangle((1, 2, 3, 0), shaded),
    )
    return vertices, triangles


def _warhead_geometry(
    center_x: int,
    center_z: int,
) -> tuple[tuple[tuple[int, int, int, int], ...], tuple[Triangle, ...]]:
    rings: tuple[tuple[int, int], ...] = (
        (-96, 48),
        (-116, 52),
        (-330, 52),
        (-350, 54),
        (-378, 54),
        (-394, 52),
        (-430, 52),
        (-452, 56),
        (-478, 48),
        (-535, 36),
        (-600, 20),
        (-642, 8),
    )
    span_colours = (
        COLLAR,
        BODY,
        BAND_EDGE,
        WARNING_BAND,
        BAND_EDGE,
        BODY,
        SHOULDER,
        NOSE,
        NOSE,
        NOSE,
        NOSE,
    )
    vertices: list[tuple[int, int, int, int]] = []
    for y, radius in rings:
        vertices.extend(_ring(center_x, center_z, y, radius))
    apex = len(vertices)
    vertices.append((center_x, -660, center_z, 0))

    triangles: list[Triangle] = []
    for ring_index, colour in enumerate(span_colours):
        _append_ring_span(
            triangles,
            ring_index * FACET_COUNT,
            (ring_index + 1) * FACET_COUNT,
            colour,
        )
    final_ring = (len(rings) - 1) * FACET_COUNT
    for facet in range(FACET_COUNT):
        following = (facet + 1) % FACET_COUNT
        triangles.append(
            Triangle(
                (final_ring + facet, apex, final_ring + following, 0),
                _shade(NOSE, facet),
            )
        )

    # The dark maintenance plates and narrow seam strips sit one model unit
    # proud of alternating octagonal faces. At field scale they read as
    # recessed panels and armour joins without requiring a texture page.
    for side in range(4):
        panel_vertices, panel_triangles = _radial_strip(
            center_x,
            center_z,
            angle_degrees=22.5 + side * 90.0,
            radius=49.0,
            half_width=12.0,
            bottom_y=-184,
            top_y=-292,
            colour=ACCESS_PANEL,
            shade_index=side * 2,
        )
        _append_geometry(
            vertices,
            triangles,
            panel_vertices,
            panel_triangles,
        )
        seam_vertices, seam_triangles = _radial_strip(
            center_x,
            center_z,
            angle_degrees=67.5 + side * 90.0,
            radius=49.0,
            half_width=2.0,
            bottom_y=-124,
            top_y=-324,
            colour=SEAM,
            shade_index=side * 2 + 1,
        )
        _append_geometry(
            vertices,
            triangles,
            seam_vertices,
            seam_triangles,
        )
    return tuple(vertices), tuple(triangles)


def _mount_geometry(
    center_x: int,
    center_z: int,
) -> tuple[tuple[tuple[int, int, int, int], ...], tuple[Triangle, ...]]:
    rings: tuple[tuple[int, int], ...] = (
        (WARHEAD_FLOOR_Y, 64),
        (-18, 64),
        (-34, 58),
        (-96, 48),
    )
    vertices: list[tuple[int, int, int, int]] = []
    for y, radius in rings:
        vertices.extend(_ring(center_x, center_z, y, radius))
    triangles: list[Triangle] = []
    _append_ring_span(triangles, 0, FACET_COUNT, MOUNT)
    _append_ring_span(triangles, FACET_COUNT, FACET_COUNT * 2, MOUNT)
    _append_ring_span(
        triangles,
        FACET_COUNT * 2,
        FACET_COUNT * 3,
        COLLAR,
    )

    # Four low triangular-prism buttresses make the floor contact explicit.
    # Their roots disappear into the plinth while their outer soles terminate
    # exactly at y=0, so no part of the model appears to hover or sink.
    for side, (radial_x, radial_z) in enumerate(
        ((1, 0), (0, 1), (-1, 0), (0, -1))
    ):
        tangent_x = -radial_z
        tangent_z = radial_x

        def foot_point(
            radial_distance: int,
            tangent_distance: int,
            y: int,
        ) -> tuple[int, int, int, int]:
            return (
                center_x
                + radial_x * radial_distance
                + tangent_x * tangent_distance,
                y,
                center_z
                + radial_z * radial_distance
                + tangent_z * tangent_distance,
                0,
            )

        foot_vertices = (
            foot_point(44, -12, -72),
            foot_point(44, 12, -72),
            foot_point(70, -16, -18),
            foot_point(70, 16, -18),
            foot_point(70, -16, WARHEAD_FLOOR_Y),
            foot_point(70, 16, WARHEAD_FLOOR_Y),
        )
        mount_colour = _shade(MOUNT, side * 2)
        foot_colour = _shade(FOOT, side * 2)
        foot_triangles = (
            Triangle((0, 2, 1, 0), mount_colour),
            Triangle((1, 2, 3, 0), mount_colour),
            Triangle((2, 4, 3, 0), foot_colour),
            Triangle((3, 4, 5, 0), foot_colour),
            Triangle((4, 0, 5, 0), foot_colour),
            Triangle((5, 0, 1, 0), foot_colour),
            Triangle((0, 4, 2, 0), foot_colour),
            Triangle((1, 3, 5, 0), foot_colour),
        )
        _append_geometry(
            vertices,
            triangles,
            foot_vertices,
            foot_triangles,
        )
    return tuple(vertices), tuple(triangles)


def _cuboid_geometry(
    minimum_x: int,
    maximum_x: int,
    minimum_y: int,
    maximum_y: int,
    minimum_z: int,
    maximum_z: int,
    colour: tuple[int, int, int],
) -> tuple[tuple[tuple[int, int, int, int], ...], tuple[Triangle, ...]]:
    """Return one closed, shared-vertex cuboid with subtly shaded faces."""

    if not (
        minimum_x < maximum_x
        and minimum_y < maximum_y
        and minimum_z < maximum_z
    ):
        raise CloningWarheadModelError("Flat cuboid bounds are degenerate")
    vertices = (
        (minimum_x, minimum_y, minimum_z, 0),
        (maximum_x, minimum_y, minimum_z, 0),
        (minimum_x, maximum_y, minimum_z, 0),
        (maximum_x, maximum_y, minimum_z, 0),
        (minimum_x, minimum_y, maximum_z, 0),
        (maximum_x, minimum_y, maximum_z, 0),
        (minimum_x, maximum_y, maximum_z, 0),
        (maximum_x, maximum_y, maximum_z, 0),
    )
    faces = (
        ((0, 2, 4, 0), (4, 2, 6, 0)),
        ((1, 5, 3, 0), (5, 7, 3, 0)),
        ((0, 4, 1, 0), (1, 4, 5, 0)),
        ((2, 3, 6, 0), (3, 7, 6, 0)),
        ((0, 1, 2, 0), (1, 3, 2, 0)),
        ((4, 6, 5, 0), (5, 6, 7, 0)),
    )
    triangles = tuple(
        Triangle(indices, _shade(colour, face_index))
        for face_index, face in enumerate(faces)
        for indices in face
    )
    return vertices, triangles


def _archive_terminal_geometry(
) -> tuple[tuple[tuple[int, int, int, int], ...], tuple[Triangle, ...]]:
    """Build a floor-standing archive console whose screen faces negative X."""

    vertices: list[tuple[int, int, int, int]] = []
    triangles: list[Triangle] = []

    for bounds, colour in (
        ((-48, 48, -12, 0, -52, 52), ARCHIVE_TERMINAL_BASE),
        ((-27, 30, -104, -12, -39, 39), ARCHIVE_TERMINAL_BODY),
        ((-58, -27, -112, -102, -48, 48), ARCHIVE_TERMINAL_PANEL),
    ):
        cuboid_vertices, cuboid_triangles = _cuboid_geometry(*bounds, colour)
        _append_geometry(
            vertices,
            triangles,
            cuboid_vertices,
            cuboid_triangles,
        )

    # A tapered equipment hood places its sloped operator face toward -X.
    # Its screen and frame sit two model units proud of that face to avoid
    # z-fighting without requiring a texture page or transparency primitive.
    hood_vertices = (
        (-58, -202, -52, 0),
        (35, -202, -52, 0),
        (-34, -102, -52, 0),
        (35, -102, -52, 0),
        (-58, -202, 52, 0),
        (35, -202, 52, 0),
        (-34, -102, 52, 0),
        (35, -102, 52, 0),
    )
    hood_faces = (
        ((0, 2, 4, 0), (4, 2, 6, 0)),
        ((1, 5, 3, 0), (5, 7, 3, 0)),
        ((0, 4, 1, 0), (1, 4, 5, 0)),
        ((2, 3, 6, 0), (3, 7, 6, 0)),
        ((0, 1, 2, 0), (1, 3, 2, 0)),
        ((4, 6, 5, 0), (5, 6, 7, 0)),
    )
    hood_triangles = tuple(
        Triangle(
            indices,
            _shade(ARCHIVE_TERMINAL_BODY, face_index),
        )
        for face_index, face in enumerate(hood_faces)
        for indices in face
    )
    _append_geometry(
        vertices,
        triangles,
        hood_vertices,
        hood_triangles,
    )

    def append_front_quad(
        bottom_x: int,
        bottom_y: int,
        top_x: int,
        top_y: int,
        minimum_z: int,
        maximum_z: int,
        colour: tuple[int, int, int],
    ) -> None:
        base = len(vertices)
        vertices.extend(
            (
                (bottom_x, bottom_y, minimum_z, 0),
                (top_x, top_y, minimum_z, 0),
                (bottom_x, bottom_y, maximum_z, 0),
                (top_x, top_y, maximum_z, 0),
            )
        )
        # Both triangles have a negative-X normal. This is the console's
        # authored front, independently verifiable from the model stream.
        triangles.extend(
            (
                Triangle((base, base + 1, base + 2, 0), colour),
                Triangle((base + 2, base + 1, base + 3, 0), colour),
            )
        )

    append_front_quad(
        -40,
        -118,
        -59,
        -188,
        -43,
        43,
        ARCHIVE_TERMINAL_EDGE,
    )
    append_front_quad(
        -43,
        -129,
        -56,
        -177,
        -34,
        34,
        ARCHIVE_TERMINAL_SCREEN_COLOUR,
    )
    append_front_quad(
        -42,
        -121,
        -44,
        -128,
        -34,
        20,
        ARCHIVE_TERMINAL_SCREEN_DARK,
    )
    append_front_quad(
        -47,
        -139,
        -49,
        -147,
        38,
        43,
        ARCHIVE_TERMINAL_STATUS,
    )
    append_front_quad(
        -50,
        -151,
        -52,
        -159,
        38,
        43,
        ARCHIVE_TERMINAL_STATUS,
    )

    # Two narrow vertical ribs tie the hood visually into the pedestal and
    # keep the silhouette legible against the dark magazine floor.
    for minimum_z, maximum_z in ((-53, -47), (47, 53)):
        rib_vertices, rib_triangles = _cuboid_geometry(
            -38,
            -28,
            -115,
            -20,
            minimum_z,
            maximum_z,
            ARCHIVE_TERMINAL_EDGE,
        )
        _append_geometry(
            vertices,
            triangles,
            rib_vertices,
            rib_triangles,
        )

    return tuple(vertices), tuple(triangles)


def build_archive_terminal_model() -> bytes:
    """Return the self-contained texture-free Zeboim archive console model."""

    vertices, triangles = _archive_terminal_geometry()
    model = _build_f3_model(vertices, triangles)
    if (
        len(model) != ARCHIVE_TERMINAL_MODEL_SIZE
        or _sha256(model) != ARCHIVE_TERMINAL_MODEL_SHA256
    ):
        raise CloningWarheadModelError(
            "Archive-terminal model is not deterministic"
        )
    return model


def _build_f3_model(
    vertices: tuple[tuple[int, int, int, int], ...],
    triangles: tuple[Triangle, ...],
) -> bytes:
    if not vertices or not triangles:
        raise CloningWarheadModelError("Flat model geometry cannot be empty")
    if len(vertices) > 0xFFFF or len(triangles) > 0xFFFF:
        raise CloningWarheadModelError("Flat model exceeds a 16-bit count")
    if any(
        not -0x8000 <= coordinate <= 0x7FFF
        for vertex in vertices
        for coordinate in vertex[:3]
    ):
        raise CloningWarheadModelError("Flat model vertex exceeds signed 16-bit")
    if any(
        index >= len(vertices)
        for triangle in triangles
        for index in triangle.indices[:3]
    ):
        raise CloningWarheadModelError("Flat model triangle index is invalid")

    vertex_offset = 0x48
    vertex_data = b"".join(struct.pack("<hhhh", *vertex) for vertex in vertices)
    mesh_offset = vertex_offset + len(vertex_data)
    index_data = b"".join(
        struct.pack("<HHHH", *triangle.indices) for triangle in triangles
    )
    mesh_data = (
        struct.pack(
            "<BBH",
            F3_MESH_TYPE,
            F3_MESH_UNKNOWN,
            len(triangles),
        )
        + index_data
    )
    display_offset = mesh_offset + len(mesh_data)
    display_data = b"".join(
        bytes((*triangle.colour, F3_GPU_COMMAND)) for triangle in triangles
    )

    output = bytearray(vertex_offset)
    struct.pack_into("<I", output, 0, 1)
    block = 0x10
    struct.pack_into("<H", output, block + 2, len(vertices))
    struct.pack_into("<H", output, block + 4, len(triangles))
    struct.pack_into("<H", output, block + 6, 1)
    struct.pack_into("<I", output, block + 8, vertex_offset)
    struct.pack_into("<I", output, block + 0x0C, vertex_offset)
    struct.pack_into("<I", output, block + 0x10, mesh_offset)
    struct.pack_into("<I", output, block + 0x14, display_offset)
    struct.pack_into("<I", output, block + 0x18, 0)
    struct.pack_into("<I", output, block + 0x1C, 0)
    for axis, minimum_offset, maximum_offset in (
        (0, block + 0x20, block + 0x28),
        (1, block + 0x22, block + 0x2A),
        (2, block + 0x24, block + 0x2C),
    ):
        struct.pack_into("<h", output, minimum_offset, min(v[axis] for v in vertices))
        struct.pack_into("<h", output, maximum_offset, max(v[axis] for v in vertices))
    struct.pack_into("<I", output, block + 0x34, len(triangles) * 0x14)
    output.extend(vertex_data)
    output.extend(mesh_data)
    output.extend(display_data)
    return bytes(output)


def _rebuild_model_archive(source: bytes, entries: list[bytes]) -> bytes:
    original_count = struct.unpack_from("<I", source)[0]
    if len(entries) != original_count + 1:
        raise CloningWarheadModelError("Exactly one model must be appended")
    original_table_end = 4 + original_count * 4
    new_table_end = 4 + len(entries) * 4
    original_first = struct.unpack_from("<I", source, 4)[0]
    prefix_padding = source[original_table_end:original_first]
    output = bytearray(new_table_end)
    struct.pack_into("<I", output, 0, len(entries))
    output.extend(prefix_padding)
    for index, entry in enumerate(entries):
        if not entry:
            raise CloningWarheadModelError("Model archive entry cannot be empty")
        while len(output) % 4:
            output.append(0)
        struct.pack_into("<I", output, 4 + index * 4, len(output))
        output.extend(entry)
    return bytes(output)


def _rebuild_same_count_model_archive(
    source: bytes,
    entries: list[bytes],
) -> bytes:
    """Rebuild an archive after replacing entries without changing its count."""

    if len(source) < 8:
        raise CloningWarheadModelError("Model archive is shorter than its header")
    original_count = struct.unpack_from("<I", source)[0]
    if len(entries) != original_count:
        raise CloningWarheadModelError(
            "Replacement model inventory changed the archive count"
        )
    table_end = 4 + original_count * 4
    original_first = struct.unpack_from("<I", source, 4)[0]
    if not table_end <= original_first <= len(source):
        raise CloningWarheadModelError(
            "Replacement model archive has an invalid first offset"
        )
    output = bytearray(table_end)
    struct.pack_into("<I", output, 0, original_count)
    output.extend(source[table_end:original_first])
    for index, entry in enumerate(entries):
        if not entry:
            raise CloningWarheadModelError("Model archive entry cannot be empty")
        while len(output) % 4:
            output.append(0)
        struct.pack_into("<I", output, 4 + index * 4, len(output))
        output.extend(entry)
    return bytes(output)


def _patch_warhead_nodes(header: bytes) -> bytes:
    if _sha256(header) != RETAIL_FIELD_673_HEADER_SHA256:
        raise CloningWarheadModelError(
            "Cloning-chamber warheads require the audited field 673 header"
        )
    if (
        len(header) != 0x5F0
        or struct.unpack_from("<H", header, 0x18C)[0] != 70
    ):
        raise CloningWarheadModelError(
            "Field 673 static-node inventory changed"
        )
    output = bytearray(header)
    for node_index in PARKED_VAT_NODE_INDICES:
        record = 0x190 + node_index * 16
        struct.pack_into("<h", output, record + 10, PARKED_VAT_Y)
    for node_index, (x, y, z) in zip(
        WARHEAD_NODE_INDICES,
        WARHEAD_PLACEMENTS,
        strict=True,
    ):
        record = 0x190 + node_index * 16
        output[record : record + 16] = struct.pack(
            "<HhhhhhhH",
            0x0010,
            0,
            0,
            0,
            x,
            y,
            z,
            WARHEAD_MODEL_INDEX,
        )
    digest = _sha256(output)
    if digest != PATCHED_FIELD_673_HEADER_SHA256:
        raise CloningWarheadModelError(
            f"Patched cloning-chamber header is not deterministic: {digest}"
        )
    return bytes(output)


def patch_cloning_chamber_warheads(
    header: bytes,
    models: bytes,
) -> tuple[bytes, bytes]:
    """Return field 673 with all six glass vats replaced by warheads."""

    digest = _sha256(models)
    if digest != RETAIL_FIELD_673_MODELS_SHA256:
        raise CloningWarheadModelError(
            "Cloning-chamber warheads require audited field 673 models; "
            f"found SHA-256 {digest}"
        )
    spans = _model_spans(models)
    if len(spans) != 20:
        raise CloningWarheadModelError(
            f"Expected 20 cloning-chamber models, found {len(spans)}"
        )
    entries = [models[start:end] for start, end in spans]
    body_vertices, body_triangles = _warhead_geometry(0, 0)
    mount_vertices, mount_triangles = _mount_geometry(0, 0)
    mount_base = len(body_vertices)
    combined_triangles = (
        *body_triangles,
        *(
            Triangle(
                (
                    triangle.indices[0] + mount_base,
                    triangle.indices[1] + mount_base,
                    triangle.indices[2] + mount_base,
                    triangle.indices[3],
                ),
                triangle.colour,
            )
            for triangle in mount_triangles
        ),
    )
    entries.append(
        _build_f3_model(
            (*body_vertices, *mount_vertices),
            combined_triangles,
        )
    )
    output = _rebuild_model_archive(models, entries)

    rebuilt_spans = _model_spans(output)
    rebuilt_entries = [
        output[start:end] for start, end in rebuilt_spans
    ]
    if rebuilt_entries[:-1] != entries[:-1]:
        raise CloningWarheadModelError(
            "A retail cloning-chamber model changed"
        )
    output_digest = _sha256(output)
    if output_digest != PATCHED_FIELD_673_MODELS_SHA256:
        raise CloningWarheadModelError(
            "Patched cloning-chamber model archive is not deterministic: "
            f"{output_digest}"
        )
    return _patch_warhead_nodes(header), output




def patch_cloning_chamber_archive_pedestal(
    header: bytes,
    models: bytes,
    graphics: bytes,
) -> tuple[bytes, bytes, bytes]:
    """Reassemble field 673's native lower service pedestal beside the aisle."""

    header_digest = _sha256(header)
    if header_digest != PATCHED_FIELD_673_HEADER_SHA256:
        raise CloningWarheadModelError(
            "Archive pedestal requires the audited warhead-patched field 673 "
            f"header; found SHA-256 {header_digest}"
        )
    models_digest = _sha256(models)
    if models_digest != PATCHED_FIELD_673_MODELS_SHA256:
        raise CloningWarheadModelError(
            "Archive pedestal requires the audited warhead-patched field 673 "
            f"models; found SHA-256 {models_digest}"
        )
    if (
        len(graphics) != RETAIL_FIELD_673_GRAPHICS_SIZE
        or _sha256(graphics) != RETAIL_FIELD_673_GRAPHICS_SHA256
    ):
        raise CloningWarheadModelError(
            "Archive pedestal requires audited retail field 673 graphics"
        )
    if (
        len(header) != 0x5F0
        or struct.unpack_from("<H", header, 0x18C)[0] != 70
    ):
        raise CloningWarheadModelError(
            "Archive-pedestal field 673 header inventory changed"
        )

    spans = _model_spans(models)
    if len(spans) != 21:
        raise CloningWarheadModelError(
            f"Expected 21 warhead-patched models, found {len(spans)}"
        )
    entries = [models[start:end] for start, end in spans]
    if tuple(
        _sha256(entries[index])
        for index in CLONING_ARCHIVE_PEDESTAL_MODEL_INDICES
    ) != CLONING_ARCHIVE_PEDESTAL_MODEL_SHA256S:
        raise CloningWarheadModelError(
            "Archive pedestal's native field 673 model set failed its audit"
        )

    # The two large upper-vat bodies are never rendered after the six vats are
    # removed. Replace only those retired payloads with valid copies of the
    # tiny native service cap; this recovers enough packed-field space for the
    # playable scripts without introducing a synthetic or cross-field model.
    preserved_entries = tuple(entries[2:])
    compact_model = entries[CLONING_ARCHIVE_PEDESTAL_COMPACTION_MODEL_INDEX]
    if _sha256(compact_model) != CLONING_ARCHIVE_PEDESTAL_COMPACTION_MODEL_SHA256:
        raise CloningWarheadModelError(
            "Archive pedestal's native compaction model failed its audit"
        )
    for index in CLONING_ARCHIVE_PEDESTAL_RETIRED_MODEL_INDICES:
        entries[index] = compact_model
    output_models = _rebuild_same_count_model_archive(models, entries)
    rebuilt_spans = _model_spans(output_models)
    rebuilt_entries = [output_models[start:end] for start, end in rebuilt_spans]
    if (
        len(output_models) != ARCHIVE_PEDESTAL_FIELD_673_MODELS_SIZE
        or _sha256(output_models) != ARCHIVE_PEDESTAL_FIELD_673_MODELS_SHA256
        or len(rebuilt_entries) != 21
        or tuple(rebuilt_entries[2:]) != preserved_entries
        or any(
            rebuilt_entries[index] != compact_model
            for index in CLONING_ARCHIVE_PEDESTAL_RETIRED_MODEL_INDICES
        )
    ):
        raise CloningWarheadModelError(
            "Archive pedestal model compaction is not deterministic"
        )

    output_header = bytearray(header)
    x, y, z = CLONING_ARCHIVE_PEDESTAL_PLACEMENT
    for node_index, source_model, model_index, flags in zip(
        CLONING_ARCHIVE_PEDESTAL_NODE_INDICES,
        CLONING_ARCHIVE_PEDESTAL_SOURCE_NODE_MODELS,
        CLONING_ARCHIVE_PEDESTAL_MODEL_INDICES,
        CLONING_ARCHIVE_PEDESTAL_NODE_FLAGS,
        strict=True,
    ):
        record = 0x190 + node_index * 16
        expected_parked_record = struct.pack(
            "<HhhhhhhH",
            0,
            0,
            0,
            0,
            1322,
            PARKED_VAT_Y,
            0,
            source_model,
        )
        if output_header[record : record + 16] != expected_parked_record:
            raise CloningWarheadModelError(
                "Archive-pedestal node is not the audited parked vat"
            )
        output_header[record : record + 16] = struct.pack(
            "<HhhhhhhH",
            flags,
            0,
            CLONING_ARCHIVE_PEDESTAL_Y_ROTATION,
            0,
            x,
            y,
            z,
            model_index,
        )

    output_header_digest = _sha256(output_header)
    if output_header_digest != ARCHIVE_PEDESTAL_FIELD_673_HEADER_SHA256:
        raise CloningWarheadModelError(
            "Archive-pedestal header is not deterministic: "
            f"{output_header_digest}"
        )
    if (
        len(graphics) != ARCHIVE_PEDESTAL_FIELD_673_GRAPHICS_SIZE
        or _sha256(graphics) != ARCHIVE_PEDESTAL_FIELD_673_GRAPHICS_SHA256
    ):
        raise CloningWarheadModelError(
            "Archive pedestal changed field 673's native graphics"
        )
    return bytes(output_header), output_models, graphics


def _reconstruct_graphics_vram(
    graphics: bytes,
    *,
    label: str,
) -> tuple[bytearray, tuple[tuple[int, int, int, int], ...]]:
    """Replay one field MIM upload stream into word-addressed PSX VRAM."""

    sector = 0x800
    vram_width = 1024
    vram_height = 512
    vram = bytearray(vram_width * vram_height * 2)
    rectangles: list[tuple[int, int, int, int]] = []
    cursor = 0
    block_index = 0
    while cursor < len(graphics):
        if cursor + 0x1C > len(graphics):
            raise CloningWarheadModelError(
                f"{label} graphics end inside upload {block_index} header"
            )
        upload_type = struct.unpack_from("<H", graphics, cursor)[0]
        (
            page_x,
            page_y,
            move_x,
            move_y,
            width,
            nominal_height,
            unknown,
            chunk_count,
        ) = struct.unpack_from("<8H", graphics, cursor + 4)
        if (
            upload_type not in (0x1200, 0x1201)
            or unknown != 1
            or width == 0
            or nominal_height == 0
            or chunk_count == 0
        ):
            raise CloningWarheadModelError(
                f"{label} graphics upload {block_index} has an invalid header"
            )
        height_table_end = cursor + 0x1C + chunk_count * 2
        if height_table_end > len(graphics):
            raise CloningWarheadModelError(
                f"{label} graphics upload {block_index} height table is truncated"
            )
        chunk_heights = struct.unpack_from(
            f"<{chunk_count}H",
            graphics,
            cursor + 0x1C,
        )
        if any(
            height == 0 or height > nominal_height
            for height in chunk_heights
        ):
            raise CloningWarheadModelError(
                f"{label} graphics upload {block_index} has an invalid chunk"
            )
        header_size = (
            (0x1C + chunk_count * 2 + sector - 1) // sector
        ) * sector
        cursor += header_size
        destination_x = page_x + move_x
        destination_y = page_y + move_y
        total_height = sum(chunk_heights)
        if (
            destination_x + width > vram_width
            or destination_y + total_height > vram_height
        ):
            raise CloningWarheadModelError(
                f"{label} graphics upload {block_index} exceeds PSX VRAM"
            )
        rectangles.append(
            (destination_x, destination_y, width, total_height)
        )
        for chunk_height in chunk_heights:
            data_size = width * chunk_height * 2
            padded_size = ((data_size + sector - 1) // sector) * sector
            if cursor + padded_size > len(graphics):
                raise CloningWarheadModelError(
                    f"{label} graphics upload {block_index} data is truncated"
                )
            for row in range(chunk_height):
                source_start = cursor + row * width * 2
                target_start = (
                    (destination_y + row) * vram_width + destination_x
                ) * 2
                vram[target_start : target_start + width * 2] = graphics[
                    source_start : source_start + width * 2
                ]
            destination_y += chunk_height
            cursor += padded_size
        block_index += 1
    if cursor != len(graphics):
        raise CloningWarheadModelError(
            f"{label} graphics do not end on an upload boundary"
        )
    return vram, tuple(rectangles)


def _graphics_rows(
    vram: bytes,
    rectangle: tuple[int, int, int, int],
) -> bytes:
    x, y, width, height = rectangle
    if (
        x < 0
        or y < 0
        or width <= 0
        or height <= 0
        or x + width > 1024
        or y + height > 512
    ):
        raise CloningWarheadModelError("Graphics rectangle lies outside PSX VRAM")
    return b"".join(
        vram[
            ((y + row) * 1024 + x) * 2 :
            ((y + row) * 1024 + x + width) * 2
        ]
        for row in range(height)
    )


def _build_graphics_upload(
    rows: bytes,
    destination: tuple[int, int, int, int],
    *,
    maximum_chunk_height: int,
    upload_type: int = 0x1200,
) -> bytes:
    """Build one deterministic sector-aligned field graphics upload."""

    x, y, width, height = destination
    if maximum_chunk_height <= 0:
        raise CloningWarheadModelError("Graphics chunk height must be positive")
    if upload_type not in (0x1200, 0x1201):
        raise CloningWarheadModelError("Graphics upload type is invalid")
    if len(rows) != width * height * 2:
        raise CloningWarheadModelError(
            "Graphics rows do not match their destination rectangle"
        )
    chunk_heights: list[int] = []
    remaining = height
    while remaining:
        take = min(maximum_chunk_height, remaining)
        chunk_heights.append(take)
        remaining -= take

    header = bytearray(0x800)
    struct.pack_into("<H", header, 0, upload_type)
    struct.pack_into(
        "<8H",
        header,
        4,
        x,
        0,
        0,
        y,
        width,
        max(chunk_heights),
        1,
        len(chunk_heights),
    )
    struct.pack_into(
        f"<{len(chunk_heights)}H",
        header,
        0x1C,
        *chunk_heights,
    )
    output = bytearray(header)
    cursor = 0
    for chunk_height in chunk_heights:
        size = width * chunk_height * 2
        chunk = rows[cursor : cursor + size]
        output.extend(chunk)
        output.extend(bytes((-len(chunk)) % 0x800))
        cursor += size
    if cursor != len(rows):
        raise CloningWarheadModelError(
            "Graphics upload did not consume its normalized rows"
        )
    return bytes(output)


def _rectangles_overlap(
    left: tuple[int, int, int, int],
    right: tuple[int, int, int, int],
) -> bool:
    lx, ly, lw, lh = left
    rx, ry, rw, rh = right
    return (
        lx < rx + rw
        and rx < lx + lw
        and ly < ry + rh
        and ry < ly + lh
    )


def _relocate_zeboim_station_model(model: bytes) -> bytes:
    """Point field 373 model 7 at field 673's compact native texture slot."""

    if (
        len(model) != ZEBOIM_STATION_SOURCE_MODEL_SIZE
        or _sha256(model) != ZEBOIM_STATION_SOURCE_MODEL_SHA256
    ):
        raise CloningWarheadModelError(
            "Zeboim station donor model 7 failed its retail audit"
        )

    output = bytearray(model)
    part_count = struct.unpack_from("<I", output, 0)[0]
    status_count = 0
    clut_count = 0
    textured_triangles = 0
    textured_quads = 0
    used_atlas_islands: set[int] = set()
    status_mapping = dict(
        zip(
            ZEBOIM_STATION_SOURCE_TPAGES,
            ZEBOIM_STATION_RELOCATED_TPAGES,
            strict=True,
        )
    )

    def relocate_uvs(offsets: tuple[int, ...]) -> None:
        source_uvs = tuple((output[offset], output[offset + 1]) for offset in offsets)
        matches: list[tuple[int, int, int, int, int]] = []
        for island_index, (source, target) in enumerate(
            ZEBOIM_STATION_TEXTURE_ATLAS
        ):
            source_u, source_v, width, height = source
            if all(
                source_u <= u < source_u + width
                and source_v <= v < source_v + height
                for u, v in source_uvs
            ):
                matches.append(
                    (
                        island_index,
                        source_u,
                        source_v,
                        target[0],
                        target[1],
                    )
                )
        if len(matches) != 1:
            raise CloningWarheadModelError(
                "Zeboim station polygon does not belong to one audited atlas island"
            )
        island_index, source_u, source_v, target_u, target_v = matches[0]
        used_atlas_islands.add(island_index)
        for offset, (old_u, old_v) in zip(offsets, source_uvs, strict=True):
            new_u = target_u + old_u - source_u
            new_v = 192 + target_v + old_v - source_v
            if not (0 <= new_u < 80 and 192 <= new_v < 256):
                raise CloningWarheadModelError(
                    "Zeboim station atlas relocation exceeds its native slot"
                )
            output[offset] = new_u
            output[offset + 1] = new_v

    for part_index in range(part_count):
        part_offset = struct.unpack_from("<I", output, 4 + part_index * 4)[0]
        block_count = struct.unpack_from("<I", output, part_offset)[0]
        for block_index in range(block_count):
            block_offset = part_offset + 0x10 + block_index * 0x38
            mesh_block_count = struct.unpack_from(
                "<H", output, block_offset + 6
            )[0]
            mesh_offset = struct.unpack_from(
                "<I", output, block_offset + 0x10
            )[0]
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
                    command = struct.unpack_from(
                        "<I", output, command_offset
                    )[0]
                    operator = (command >> 24) & 0xFF
                    polygon_operator = operator & ~(0x10 | 0x02 | 0x01)
                    display_offset += 4
                    if operator == 0xC4:
                        old_status = command & 0xFFFF
                        if old_status not in status_mapping:
                            raise CloningWarheadModelError(
                                "Zeboim station uses an unaudited texture page"
                            )
                        struct.pack_into(
                            "<H",
                            output,
                            command_offset,
                            status_mapping[old_status],
                        )
                        status_count += 1
                    elif operator == 0xC8:
                        if command & 0xFFFF != ZEBOIM_STATION_SOURCE_CLUT:
                            raise CloningWarheadModelError(
                                "Zeboim station uses an unaudited CLUT"
                            )
                        struct.pack_into(
                            "<H",
                            output,
                            command_offset,
                            ZEBOIM_STATION_RELOCATED_CLUT,
                        )
                        clut_count += 1
                    elif polygon_operator == 0x24:
                        # The triangle's third UV coordinate is stored in the
                        # command word; the first two follow it as UV pairs.
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
                        textured_triangles += 1
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
                        textured_quads += 1
                    elif polygon_operator in (0x20, 0x28):
                        raise CloningWarheadModelError(
                            "Zeboim station gained an unaudited flat-shaded polygon"
                        )
                    else:
                        raise CloningWarheadModelError(
                            "Zeboim station display list contains an unknown command"
                        )

    if (
        status_count != 2
        or clut_count != 1
        or textured_triangles != 5
        or textured_quads != 80
        or used_atlas_islands != set(range(len(ZEBOIM_STATION_TEXTURE_ATLAS)))
        or len(output) != ZEBOIM_STATION_SOURCE_MODEL_SIZE
        or _sha256(output) != ZEBOIM_STATION_RELOCATED_MODEL_SHA256
    ):
        raise CloningWarheadModelError(
            "Relocated Zeboim station model is not deterministic"
        )
    return bytes(output)


def patch_cloning_chamber_zeboim_station(
    header: bytes,
    models: bytes,
    graphics: bytes,
    donor_header: bytes,
    donor_models: bytes,
    donor_graphics: bytes,
) -> tuple[bytes, bytes, bytes]:
    """Install retail field 373 model 7 as the reserve-magazine terminal."""

    if _sha256(header) != PATCHED_FIELD_673_HEADER_SHA256:
        raise CloningWarheadModelError(
            "Zeboim station requires the audited warhead-patched field 673 header"
        )
    if _sha256(models) != PATCHED_FIELD_673_MODELS_SHA256:
        raise CloningWarheadModelError(
            "Zeboim station requires the audited warhead-patched field 673 models"
        )
    if (
        len(graphics) != RETAIL_FIELD_673_GRAPHICS_SIZE
        or _sha256(graphics) != RETAIL_FIELD_673_GRAPHICS_SHA256
    ):
        raise CloningWarheadModelError(
            "Zeboim station requires audited retail field 673 graphics"
        )
    if (
        len(donor_header) != ZEBOIM_STATION_DONOR_HEADER_SIZE
        or _sha256(donor_header) != ZEBOIM_STATION_DONOR_HEADER_SHA256
        or len(donor_models) != ZEBOIM_STATION_DONOR_MODELS_SIZE
        or _sha256(donor_models) != ZEBOIM_STATION_DONOR_MODELS_SHA256
        or len(donor_graphics) != ZEBOIM_STATION_DONOR_GRAPHICS_SIZE
        or _sha256(donor_graphics) != ZEBOIM_STATION_DONOR_GRAPHICS_SHA256
    ):
        raise CloningWarheadModelError(
            "Zeboim station requires the audited retail field 373 donor assets"
        )

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
        raise CloningWarheadModelError(
            "Zeboim station source node 44 changed from its retail audit"
        )

    donor_spans = _model_spans(donor_models)
    if len(donor_spans) != 15:
        raise CloningWarheadModelError(
            f"Expected 15 field-373 models, found {len(donor_spans)}"
        )
    donor_start, donor_end = donor_spans[ZEBOIM_STATION_SOURCE_MODEL_INDEX]
    relocated_station = _relocate_zeboim_station_model(
        donor_models[donor_start:donor_end]
    )

    target_spans = _model_spans(models)
    if len(target_spans) != 21:
        raise CloningWarheadModelError(
            f"Expected 21 warhead-patched models, found {len(target_spans)}"
        )
    entries = [models[start:end] for start, end in target_spans]
    preserved_entries = tuple(entries[2:])
    compact_model = entries[CLONING_ARCHIVE_PEDESTAL_COMPACTION_MODEL_INDEX]
    if _sha256(compact_model) != CLONING_ARCHIVE_PEDESTAL_COMPACTION_MODEL_SHA256:
        raise CloningWarheadModelError(
            "Zeboim station compaction model failed its field-673 audit"
        )
    entries[ZEBOIM_STATION_TARGET_MODEL_INDEX] = relocated_station
    entries[1] = compact_model
    output_models = _rebuild_same_count_model_archive(models, entries)
    rebuilt_spans = _model_spans(output_models)
    rebuilt_entries = [
        output_models[start:end] for start, end in rebuilt_spans
    ]
    if (
        len(output_models) != ZEBOIM_STATION_FIELD_673_MODELS_SIZE
        or _sha256(output_models) != ZEBOIM_STATION_FIELD_673_MODELS_SHA256
        or rebuilt_entries[ZEBOIM_STATION_TARGET_MODEL_INDEX]
        != relocated_station
        or rebuilt_entries[1] != compact_model
        or tuple(rebuilt_entries[2:]) != preserved_entries
    ):
        raise CloningWarheadModelError(
            "Zeboim station model transplant is not deterministic"
        )

    output_header = bytearray(header)
    target_record = 0x190 + ZEBOIM_STATION_TARGET_NODE_INDEX * 16
    expected_parked_record = struct.pack(
        "<HhhhhhhH",
        0,
        0,
        0,
        0,
        1322,
        PARKED_VAT_Y,
        0,
        ZEBOIM_STATION_TARGET_MODEL_INDEX,
    )
    if output_header[target_record : target_record + 16] != expected_parked_record:
        raise CloningWarheadModelError(
            "Zeboim station target node is not the audited parked vat"
        )
    x, y, z = ZEBOIM_STATION_PLACEMENT
    output_header[target_record : target_record + 16] = struct.pack(
        "<HhhhhhhH",
        ZEBOIM_STATION_NODE_FLAGS,
        0,
        ZEBOIM_STATION_Y_ROTATION,
        0,
        x,
        y,
        z,
        ZEBOIM_STATION_TARGET_MODEL_INDEX,
    )
    if _sha256(output_header) != ZEBOIM_STATION_FIELD_673_HEADER_SHA256:
        raise CloningWarheadModelError(
            "Zeboim station header placement is not deterministic"
        )

    donor_vram, donor_rectangles = _reconstruct_graphics_vram(
        donor_graphics,
        label="Retail field 373",
    )
    target_vram, target_rectangles = _reconstruct_graphics_vram(
        graphics,
        label="Retail field 673",
    )
    if donor_rectangles != (
        (0, 480, 256, 7),
        (320, 0, 288, 192),
        (320, 192, 248, 64),
        (576, 192, 24, 64),
    ) or target_rectangles != (
        (0, 480, 256, 9),
        (320, 0, 128, 256),
        (448, 0, 64, 128),
        (512, 192, 40, 64),
    ):
        raise CloningWarheadModelError(
            "Zeboim station donor or target VRAM layout changed from its audit"
        )

    retired_block = graphics[ZEBOIM_STATION_RETIRED_GRAPHICS_BLOCK_OFFSET :]
    retired_clut_start = ZEBOIM_STATION_RETIRED_CLUT_FILE_OFFSET
    retired_clut_end = retired_clut_start + 256 * 2
    if (
        len(retired_block) != 0x2000
        or _sha256(retired_block)
        != ZEBOIM_STATION_RETIRED_GRAPHICS_BLOCK_SHA256
        or _sha256(graphics[retired_clut_start:retired_clut_end])
        != ZEBOIM_STATION_RETIRED_CLUT_ROWS_SHA256
        or _graphics_rows(target_vram, ZEBOIM_STATION_TARGET_CLUT_RECT)
        != graphics[retired_clut_start:retired_clut_end]
    ):
        raise CloningWarheadModelError(
            "Zeboim station's retired field-673 graphics allocation changed"
        )

    clut_rows = _graphics_rows(
        donor_vram,
        ZEBOIM_STATION_SOURCE_CLUT_RECT,
    )
    texture_rows = _graphics_rows(
        donor_vram,
        ZEBOIM_STATION_SOURCE_TEXTURE_RECT,
    )
    if (
        _sha256(clut_rows) != ZEBOIM_STATION_CLUT_ROWS_SHA256
        or _sha256(texture_rows) != ZEBOIM_STATION_TEXTURE_ROWS_SHA256
    ):
        raise CloningWarheadModelError(
            "Zeboim station retail palette or texels failed their audit"
        )
    source_width = ZEBOIM_STATION_SOURCE_TEXTURE_PIXEL_WIDTH
    target_width = ZEBOIM_STATION_TARGET_TEXTURE_PIXEL_WIDTH
    atlas_texture_rows = bytearray(
        _graphics_rows(target_vram, ZEBOIM_STATION_TARGET_TEXTURE_RECT)
    )
    occupied_target_texels: set[tuple[int, int]] = set()
    for source, target in ZEBOIM_STATION_TEXTURE_ATLAS:
        source_u, source_v, width, height = source
        target_u, target_v = target
        if (
            source_u < 0
            or source_v < ZEBOIM_STATION_SOURCE_TEXTURE_RECT[1]
            or source_u + width > source_width
            or source_v + height
            > ZEBOIM_STATION_SOURCE_TEXTURE_RECT[1]
            + ZEBOIM_STATION_SOURCE_TEXTURE_RECT[3]
            or target_u < 0
            or target_v < 0
            or target_u + width > target_width
            or target_v + height > ZEBOIM_STATION_TARGET_TEXTURE_RECT[3]
        ):
            raise CloningWarheadModelError(
                "Zeboim station atlas contains an out-of-bounds island"
            )
        island_texels = {
            (target_u + x, target_v + y)
            for y in range(height)
            for x in range(width)
        }
        if occupied_target_texels & island_texels:
            raise CloningWarheadModelError(
                "Zeboim station atlas islands overlap in the native slot"
            )
        occupied_target_texels.update(island_texels)
        for row in range(height):
            source_start = (
                source_v
                - ZEBOIM_STATION_SOURCE_TEXTURE_RECT[1]
                + row
            ) * source_width + source_u
            target_start = (target_v + row) * target_width + target_u
            atlas_texture_rows[target_start : target_start + width] = (
                texture_rows[source_start : source_start + width]
            )
    atlas_texture_rows = bytes(atlas_texture_rows)
    if (
        len(occupied_target_texels) != 4_288
        or max(x for x, _y in occupied_target_texels) != 77
        or max(y for _x, y in occupied_target_texels) != 61
        or len(atlas_texture_rows) != target_width * 64
        or _sha256(atlas_texture_rows)
        != ZEBOIM_STATION_ATLAS_TEXTURE_ROWS_SHA256
    ):
        raise CloningWarheadModelError(
            "Zeboim station lossless texture atlas is not deterministic"
        )

    # Preserve the complete retail fourth-upload structure. In particular its
    # page/move coordinates are not equivalent to rebuilding a header with the
    # same apparent destination: the live field allocator retains the former
    # and discarded the latter. Only the row bytes inside its 25/25/14 chunks
    # are replaced; headers, padding, offsets, and the 0x2000-byte span remain.
    texture_upload = bytearray(retired_block)
    source_offset = 0
    chunk_offset = 0x800
    for chunk_height in (25, 25, 14):
        chunk_size = ZEBOIM_STATION_TARGET_TEXTURE_RECT[2] * chunk_height * 2
        texture_upload[chunk_offset : chunk_offset + chunk_size] = (
            atlas_texture_rows[source_offset : source_offset + chunk_size]
        )
        source_offset += chunk_size
        chunk_offset += 0x800
    if (
        source_offset != len(atlas_texture_rows)
        or chunk_offset != len(texture_upload)
        or len(texture_upload) != 0x2000
        or texture_upload[:0x800] != retired_block[:0x800]
        or _sha256(bytes(texture_upload))
        != ZEBOIM_STATION_TEXTURE_UPLOAD_SHA256
    ):
        raise CloningWarheadModelError(
            "Zeboim station replacement graphics upload is not deterministic"
        )

    # Preserve the native four-upload inventory. The engine/runtime allocator
    # does not retain the two formerly appended rectangles even though an
    # offline MIM replay can see them. Row 488 and upload four belonged only to
    # parked models 2/3, so replace those exact registered payloads instead.
    output_graphics = bytearray(graphics)
    output_graphics[retired_clut_start:retired_clut_end] = clut_rows
    output_graphics[ZEBOIM_STATION_RETIRED_GRAPHICS_BLOCK_OFFSET :] = (
        texture_upload
    )
    output_vram, output_rectangles = _reconstruct_graphics_vram(
        bytes(output_graphics),
        label="Field 673 with Zeboim station",
    )
    if (
        len(output_graphics) != ZEBOIM_STATION_FIELD_673_GRAPHICS_SIZE
        or _sha256(output_graphics) != ZEBOIM_STATION_FIELD_673_GRAPHICS_SHA256
        or output_rectangles != target_rectangles
        or output_graphics[:retired_clut_start]
        != graphics[:retired_clut_start]
        or output_graphics[
            retired_clut_end:ZEBOIM_STATION_RETIRED_GRAPHICS_BLOCK_OFFSET
        ]
        != graphics[
            retired_clut_end:ZEBOIM_STATION_RETIRED_GRAPHICS_BLOCK_OFFSET
        ]
        or _graphics_rows(output_vram, ZEBOIM_STATION_TARGET_CLUT_RECT)
        != clut_rows
        or _graphics_rows(output_vram, ZEBOIM_STATION_TARGET_TEXTURE_RECT)
        != atlas_texture_rows
    ):
        raise CloningWarheadModelError(
            "Zeboim station graphics transplant is not deterministic"
        )

    # Outside the retired palette/texture allocation, the complete 1024x512
    # word-addressed VRAM image is unchanged.
    masked_output = bytearray(output_vram)
    for rectangle in (
        ZEBOIM_STATION_TARGET_CLUT_RECT,
        ZEBOIM_STATION_RETIRED_TEXTURE_RECT,
    ):
        x, y, width, height = rectangle
        for row in range(height):
            start = ((y + row) * 1024 + x) * 2
            end = start + width * 2
            masked_output[start:end] = target_vram[start:end]
    if masked_output != target_vram:
        raise CloningWarheadModelError(
            "Zeboim station changed active field-673 VRAM outside retired slots"
        )
    return bytes(output_header), output_models, bytes(output_graphics)


__all__ = [
    "ARCHIVE_PEDESTAL_FIELD_673_GRAPHICS_SHA256",
    "ARCHIVE_PEDESTAL_FIELD_673_GRAPHICS_SIZE",
    "ARCHIVE_PEDESTAL_FIELD_673_HEADER_SHA256",
    "ARCHIVE_PEDESTAL_FIELD_673_MODELS_SHA256",
    "ARCHIVE_PEDESTAL_FIELD_673_MODELS_SIZE",
    "ARCHIVE_TERMINAL_MODEL_SHA256",
    "ARCHIVE_TERMINAL_MODEL_SIZE",
    "ARCHIVE_TERMINAL_SCREEN_COLOUR",
    "ARCHIVE_TERMINAL_SCREEN_NORMAL",
    "CLONING_ARCHIVE_PEDESTAL_COMPACTION_MODEL_INDEX",
    "CLONING_ARCHIVE_PEDESTAL_COMPACTION_MODEL_SHA256",
    "CLONING_ARCHIVE_PEDESTAL_MODEL_INDICES",
    "CLONING_ARCHIVE_PEDESTAL_MODEL_SHA256S",
    "CLONING_ARCHIVE_PEDESTAL_NODE_FLAGS",
    "CLONING_ARCHIVE_PEDESTAL_NODE_INDICES",
    "CLONING_ARCHIVE_PEDESTAL_PLACEMENT",
    "CLONING_ARCHIVE_PEDESTAL_RETIRED_MODEL_INDICES",
    "CLONING_ARCHIVE_PEDESTAL_SOURCE_NODE_MODELS",
    "CLONING_ARCHIVE_PEDESTAL_VISUAL_CENTER",
    "CLONING_ARCHIVE_PEDESTAL_WORLD_BOUNDS",
    "CLONING_ARCHIVE_PEDESTAL_Y_ROTATION",
    "PATCHED_FIELD_673_MODELS_SHA256",
    "PATCHED_FIELD_673_HEADER_SHA256",
    "RETAIL_FIELD_673_GRAPHICS_SHA256",
    "RETAIL_FIELD_673_GRAPHICS_SIZE",
    "RETAIL_FIELD_673_MODELS_SHA256",
    "RETAIL_FIELD_673_HEADER_SHA256",
    "WARHEAD_FLOOR_Y",
    "WARHEAD_FOOTPRINT_RADIUS",
    "ZEBOIM_STATION_ATLAS_TEXTURE_ROWS_SHA256",
    "ZEBOIM_STATION_CLUT_ROWS_SHA256",
    "ZEBOIM_STATION_DONOR_GRAPHICS_SHA256",
    "ZEBOIM_STATION_DONOR_GRAPHICS_SIZE",
    "ZEBOIM_STATION_DONOR_HEADER_SHA256",
    "ZEBOIM_STATION_DONOR_HEADER_SIZE",
    "ZEBOIM_STATION_DONOR_MODELS_SHA256",
    "ZEBOIM_STATION_DONOR_MODELS_SIZE",
    "ZEBOIM_STATION_FIELD_673_GRAPHICS_SHA256",
    "ZEBOIM_STATION_FIELD_673_GRAPHICS_SIZE",
    "ZEBOIM_STATION_FIELD_673_HEADER_SHA256",
    "ZEBOIM_STATION_FIELD_673_MODELS_SHA256",
    "ZEBOIM_STATION_FIELD_673_MODELS_SIZE",
    "ZEBOIM_STATION_NODE_FLAGS",
    "ZEBOIM_STATION_PLACEMENT",
    "ZEBOIM_STATION_RELOCATED_CLUT",
    "ZEBOIM_STATION_RELOCATED_MODEL_SHA256",
    "ZEBOIM_STATION_RELOCATED_TPAGES",
    "ZEBOIM_STATION_SCREEN_NORMAL",
    "ZEBOIM_STATION_SOURCE_CLUT",
    "ZEBOIM_STATION_SOURCE_CLUT_RECT",
    "ZEBOIM_STATION_SOURCE_MODEL_INDEX",
    "ZEBOIM_STATION_SOURCE_MODEL_SHA256",
    "ZEBOIM_STATION_SOURCE_MODEL_SIZE",
    "ZEBOIM_STATION_SOURCE_NODE_INDEX",
    "ZEBOIM_STATION_SOURCE_TEXTURE_RECT",
    "ZEBOIM_STATION_SOURCE_TEXTURE_PIXEL_WIDTH",
    "ZEBOIM_STATION_SOURCE_TPAGES",
    "ZEBOIM_STATION_TARGET_CLUT_RECT",
    "ZEBOIM_STATION_TARGET_MODEL_INDEX",
    "ZEBOIM_STATION_TARGET_NODE_INDEX",
    "ZEBOIM_STATION_TARGET_TEXTURE_RECT",
    "ZEBOIM_STATION_TARGET_TEXTURE_PIXEL_WIDTH",
    "ZEBOIM_STATION_TEXTURE_ATLAS",
    "ZEBOIM_STATION_TEXTURE_ROWS_SHA256",
    "ZEBOIM_STATION_VISUAL_CENTER",
    "ZEBOIM_STATION_WORLD_BOUNDS",
    "ZEBOIM_STATION_Y_ROTATION",
    "CloningWarheadModelError",
    "build_archive_terminal_model",
    "patch_cloning_chamber_archive_pedestal",
    "patch_cloning_chamber_zeboim_station",
    "patch_cloning_chamber_warheads",
]
