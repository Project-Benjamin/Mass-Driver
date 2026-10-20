from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import unittest

from tools.xgcloning_warheads import (
    ARCHIVE_PEDESTAL_FIELD_673_GRAPHICS_SHA256,
    ARCHIVE_PEDESTAL_FIELD_673_GRAPHICS_SIZE,
    ARCHIVE_PEDESTAL_FIELD_673_HEADER_SHA256,
    ARCHIVE_PEDESTAL_FIELD_673_MODELS_SHA256,
    ARCHIVE_PEDESTAL_FIELD_673_MODELS_SIZE,
    CLONING_ARCHIVE_PEDESTAL_COMPACTION_MODEL_INDEX,
    CLONING_ARCHIVE_PEDESTAL_COMPACTION_MODEL_SHA256,
    CLONING_ARCHIVE_PEDESTAL_MODEL_INDICES,
    CLONING_ARCHIVE_PEDESTAL_MODEL_SHA256S,
    CLONING_ARCHIVE_PEDESTAL_NODE_FLAGS,
    CLONING_ARCHIVE_PEDESTAL_NODE_INDICES,
    CLONING_ARCHIVE_PEDESTAL_PLACEMENT,
    CLONING_ARCHIVE_PEDESTAL_RETIRED_MODEL_INDICES,
    CLONING_ARCHIVE_PEDESTAL_SOURCE_NODE_MODELS,
    CLONING_ARCHIVE_PEDESTAL_VISUAL_CENTER,
    CLONING_ARCHIVE_PEDESTAL_WORLD_BOUNDS,
    CLONING_ARCHIVE_PEDESTAL_Y_ROTATION,
    PARKED_VAT_NODE_INDICES,
    PARKED_VAT_Y,
    PATCHED_FIELD_673_HEADER_SHA256,
    PATCHED_FIELD_673_MODELS_SHA256,
    RETAIL_FIELD_673_GRAPHICS_SHA256,
    RETAIL_FIELD_673_GRAPHICS_SIZE,
    WARHEAD_FLOOR_Y,
    WARHEAD_FOOTPRINT_RADIUS,
    WARHEAD_MODEL_INDEX,
    WARHEAD_NODE_INDICES,
    WARHEAD_PLACEMENTS,
    ZEBOIM_STATION_ATLAS_TEXTURE_ROWS_SHA256,
    ZEBOIM_STATION_CLUT_ROWS_SHA256,
    ZEBOIM_STATION_DONOR_GRAPHICS_SHA256,
    ZEBOIM_STATION_DONOR_GRAPHICS_SIZE,
    ZEBOIM_STATION_DONOR_HEADER_SHA256,
    ZEBOIM_STATION_DONOR_HEADER_SIZE,
    ZEBOIM_STATION_DONOR_MODELS_SHA256,
    ZEBOIM_STATION_DONOR_MODELS_SIZE,
    ZEBOIM_STATION_FIELD_673_GRAPHICS_SHA256,
    ZEBOIM_STATION_FIELD_673_GRAPHICS_SIZE,
    ZEBOIM_STATION_FIELD_673_HEADER_SHA256,
    ZEBOIM_STATION_FIELD_673_MODELS_SHA256,
    ZEBOIM_STATION_FIELD_673_MODELS_SIZE,
    ZEBOIM_STATION_NODE_FLAGS,
    ZEBOIM_STATION_PLACEMENT,
    ZEBOIM_STATION_RELOCATED_CLUT,
    ZEBOIM_STATION_RELOCATED_MODEL_SHA256,
    ZEBOIM_STATION_RELOCATED_TPAGES,
    ZEBOIM_STATION_RETIRED_CLUT_FILE_OFFSET,
    ZEBOIM_STATION_RETIRED_GRAPHICS_BLOCK_OFFSET,
    ZEBOIM_STATION_RETIRED_TEXTURE_RECT,
    ZEBOIM_STATION_SOURCE_CLUT,
    ZEBOIM_STATION_SOURCE_CLUT_RECT,
    ZEBOIM_STATION_SOURCE_MODEL_INDEX,
    ZEBOIM_STATION_SOURCE_MODEL_SHA256,
    ZEBOIM_STATION_SOURCE_MODEL_SIZE,
    ZEBOIM_STATION_SOURCE_NODE_INDEX,
    ZEBOIM_STATION_SOURCE_TEXTURE_RECT,
    ZEBOIM_STATION_SOURCE_TEXTURE_PIXEL_WIDTH,
    ZEBOIM_STATION_SOURCE_TPAGES,
    ZEBOIM_STATION_TARGET_CLUT_RECT,
    ZEBOIM_STATION_TARGET_MODEL_INDEX,
    ZEBOIM_STATION_TARGET_NODE_INDEX,
    ZEBOIM_STATION_TARGET_TEXTURE_RECT,
    ZEBOIM_STATION_TARGET_TEXTURE_PIXEL_WIDTH,
    ZEBOIM_STATION_TEXTURE_ATLAS,
    ZEBOIM_STATION_TEXTURE_UPLOAD_SHA256,
    ZEBOIM_STATION_TEXTURE_ROWS_SHA256,
    ZEBOIM_STATION_VISUAL_CENTER,
    ZEBOIM_STATION_WORLD_BOUNDS,
    ZEBOIM_STATION_Y_ROTATION,
    CloningWarheadModelError,
    _graphics_rows,
    _reconstruct_graphics_vram,
    patch_cloning_chamber_archive_pedestal,
    patch_cloning_chamber_zeboim_station,
    patch_cloning_chamber_warheads,
)
from tools.xgfield import STREAM_NAMES, build_field, parse_field
from tools.xgmissiles import _model_spans


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DONOR = PROJECT_ROOT / "work" / "reference_fields" / "field_673"
FIELD_673_GRAPHICS = (
    PROJECT_ROOT
    / "work"
    / "reference_fields"
    / "cd1_cloning"
    / "1953.bin"
)
PEDESTAL_FIXTURES_PRESENT = DONOR.is_dir() and FIELD_673_GRAPHICS.is_file()
STATION_DONOR = PROJECT_ROOT / "work" / "audit_zeboim_cd1" / "field_373"
STATION_DONOR_GRAPHICS = (
    PROJECT_ROOT / "work" / "audit_zeboim_cd1" / "1353.bin"
)
STATION_FIXTURES_PRESENT = (
    PEDESTAL_FIXTURES_PRESENT
    and STATION_DONOR.is_dir()
    and STATION_DONOR_GRAPHICS.is_file()
)
CONCEPT = (
    PROJECT_ROOT
    / "assets"
    / "mass_driver"
    / "cloning-chamber-warhead-concept-v1.png"
)


def _node(data: bytes, index: int) -> tuple[int, ...]:
    return struct.unpack_from("<HhhhhhhH", data, 0x190 + index * 16)


def _models(data: bytes) -> list[bytes]:
    return [data[start:end] for start, end in _model_spans(data)]


def _station_inputs() -> tuple[bytes, bytes, bytes, bytes, bytes, bytes]:
    target_header = (DONOR / "header.bin").read_bytes()
    target_models = (DONOR / "02_models.bin").read_bytes()
    target_graphics = FIELD_673_GRAPHICS.read_bytes()
    target_header, target_models = patch_cloning_chamber_warheads(
        target_header,
        target_models,
    )
    return (
        target_header,
        target_models,
        target_graphics,
        (STATION_DONOR / "header.bin").read_bytes(),
        (STATION_DONOR / "02_models.bin").read_bytes(),
        STATION_DONOR_GRAPHICS.read_bytes(),
    )


class CloningChamberWarheadTests(unittest.TestCase):
    def test_generated_concept_asset_is_present_and_fixed(self) -> None:
        self.assertEqual(CONCEPT.stat().st_size, 1_703_353)
        self.assertEqual(
            hashlib.sha256(CONCEPT.read_bytes()).hexdigest(),
            "cbce03513cb2966827cf6ddc0985dfdf83627993463042d441972beb459b19b7",
        )

    def test_wrong_archives_are_rejected(self) -> None:
        with self.assertRaises(CloningWarheadModelError):
            patch_cloning_chamber_warheads(bytes(0x5F0), bytes(256))

    @unittest.skipUnless(
        STATION_FIXTURES_PRESENT,
        "retail field-373 station fixtures are absent",
    )
    def test_zeboim_station_rejects_target_or_donor_drift(self) -> None:
        inputs = list(_station_inputs())
        for index, expected_message in (
            (0, "warhead-patched field 673 header"),
            (1, "warhead-patched field 673 models"),
            (2, "retail field 673 graphics"),
            (3, "retail field 373 donor assets"),
            (4, "retail field 373 donor assets"),
            (5, "retail field 373 donor assets"),
        ):
            with self.subTest(drifted_input=index):
                damaged = inputs.copy()
                payload = bytearray(damaged[index])
                payload[-1] ^= 1
                damaged[index] = bytes(payload)
                with self.assertRaisesRegex(
                    CloningWarheadModelError,
                    expected_message,
                ):
                    patch_cloning_chamber_zeboim_station(*damaged)

        output = patch_cloning_chamber_zeboim_station(*inputs)
        with self.assertRaisesRegex(
            CloningWarheadModelError,
            "warhead-patched field 673 header",
        ):
            patch_cloning_chamber_zeboim_station(
                output[0],
                output[1],
                output[2],
                *inputs[3:],
            )

    @unittest.skipUnless(
        STATION_FIXTURES_PRESENT,
        "retail field-373 station fixtures are absent",
    )
    def test_zeboim_station_transplants_exact_model_palette_and_texels(self) -> None:
        inputs = _station_inputs()
        (
            target_header,
            target_models,
            target_graphics,
            donor_header,
            donor_models,
            donor_graphics,
        ) = inputs
        output_header, output_models, output_graphics = (
            patch_cloning_chamber_zeboim_station(*inputs)
        )
        self.assertEqual(
            patch_cloning_chamber_zeboim_station(*inputs),
            (output_header, output_models, output_graphics),
        )

        self.assertEqual(
            (
                len(donor_header),
                hashlib.sha256(donor_header).hexdigest(),
                len(donor_models),
                hashlib.sha256(donor_models).hexdigest(),
                len(donor_graphics),
                hashlib.sha256(donor_graphics).hexdigest(),
            ),
            (
                ZEBOIM_STATION_DONOR_HEADER_SIZE,
                ZEBOIM_STATION_DONOR_HEADER_SHA256,
                ZEBOIM_STATION_DONOR_MODELS_SIZE,
                ZEBOIM_STATION_DONOR_MODELS_SHA256,
                ZEBOIM_STATION_DONOR_GRAPHICS_SIZE,
                ZEBOIM_STATION_DONOR_GRAPHICS_SHA256,
            ),
        )
        self.assertEqual(
            _node(donor_header, ZEBOIM_STATION_SOURCE_NODE_INDEX),
            (0x0010, 0, 0x0200, 0, 0, 0, 0, ZEBOIM_STATION_SOURCE_MODEL_INDEX),
        )
        donor_entries = _models(donor_models)
        self.assertEqual(len(donor_entries), 15)
        self.assertEqual(
            (
                len(donor_entries[ZEBOIM_STATION_SOURCE_MODEL_INDEX]),
                hashlib.sha256(
                    donor_entries[ZEBOIM_STATION_SOURCE_MODEL_INDEX]
                ).hexdigest(),
            ),
            (
                ZEBOIM_STATION_SOURCE_MODEL_SIZE,
                ZEBOIM_STATION_SOURCE_MODEL_SHA256,
            ),
        )

        self.assertEqual(
            hashlib.sha256(output_header).hexdigest(),
            ZEBOIM_STATION_FIELD_673_HEADER_SHA256,
        )
        self.assertEqual(
            (
                len(output_models),
                hashlib.sha256(output_models).hexdigest(),
                len(output_graphics),
                hashlib.sha256(output_graphics).hexdigest(),
            ),
            (
                ZEBOIM_STATION_FIELD_673_MODELS_SIZE,
                ZEBOIM_STATION_FIELD_673_MODELS_SHA256,
                ZEBOIM_STATION_FIELD_673_GRAPHICS_SIZE,
                ZEBOIM_STATION_FIELD_673_GRAPHICS_SHA256,
            ),
        )
        self.assertEqual(len(target_graphics), 102_400)
        self.assertEqual(len(output_graphics), len(target_graphics))
        self.assertEqual(
            _node(output_header, ZEBOIM_STATION_TARGET_NODE_INDEX),
            (
                ZEBOIM_STATION_NODE_FLAGS,
                0,
                ZEBOIM_STATION_Y_ROTATION,
                0,
                *ZEBOIM_STATION_PLACEMENT,
                ZEBOIM_STATION_TARGET_MODEL_INDEX,
            ),
        )
        self.assertEqual(ZEBOIM_STATION_VISUAL_CENTER, (500, -76, 0))
        self.assertEqual(
            ZEBOIM_STATION_WORLD_BOUNDS,
            (461, 539, -152, 0, -40, 39),
        )
        for node_index in range(70):
            if node_index != ZEBOIM_STATION_TARGET_NODE_INDEX:
                with self.subTest(preserved_node=node_index):
                    self.assertEqual(
                        _node(output_header, node_index),
                        _node(target_header, node_index),
                    )

        target_entries = _models(target_models)
        output_entries = _models(output_models)
        self.assertEqual((len(target_entries), len(output_entries)), (21, 21))
        self.assertEqual(
            hashlib.sha256(
                output_entries[ZEBOIM_STATION_TARGET_MODEL_INDEX]
            ).hexdigest(),
            ZEBOIM_STATION_RELOCATED_MODEL_SHA256,
        )
        donor_model = donor_entries[ZEBOIM_STATION_SOURCE_MODEL_INDEX]
        station_model = output_entries[ZEBOIM_STATION_TARGET_MODEL_INDEX]
        changed_model_bytes = [
            index
            for index, (before, after) in enumerate(
                zip(donor_model, station_model, strict=True)
            )
            if before != after
        ]
        self.assertEqual(len(changed_model_bytes), 627)
        self.assertEqual(
            (ZEBOIM_STATION_SOURCE_TPAGES, ZEBOIM_STATION_RELOCATED_TPAGES),
            ((0x87, 0xA7), (0x88, 0xA8)),
        )
        self.assertEqual(
            (ZEBOIM_STATION_SOURCE_CLUT, ZEBOIM_STATION_RELOCATED_CLUT),
            (0x7980, 0x7A00),
        )
        self.assertEqual(output_entries[1], target_entries[6])
        self.assertEqual(output_entries[2:], target_entries[2:])
        self.assertEqual(
            output_entries[WARHEAD_MODEL_INDEX],
            target_entries[WARHEAD_MODEL_INDEX],
        )

        donor_vram, _donor_rectangles = _reconstruct_graphics_vram(
            donor_graphics,
            label="test field 373",
        )
        target_vram, target_rectangles = _reconstruct_graphics_vram(
            target_graphics,
            label="test field 673",
        )
        output_vram, output_rectangles = _reconstruct_graphics_vram(
            output_graphics,
            label="test transplanted field 673",
        )
        self.assertEqual(output_rectangles, target_rectangles)
        self.assertEqual(len(output_rectangles), 4)
        self.assertEqual(
            ZEBOIM_STATION_TARGET_TEXTURE_RECT,
            ZEBOIM_STATION_RETIRED_TEXTURE_RECT,
        )
        clut_start = ZEBOIM_STATION_RETIRED_CLUT_FILE_OFFSET
        clut_end = clut_start + 256 * 2
        self.assertEqual(output_graphics[:clut_start], target_graphics[:clut_start])
        self.assertEqual(
            output_graphics[
                clut_end:ZEBOIM_STATION_RETIRED_GRAPHICS_BLOCK_OFFSET
            ],
            target_graphics[
                clut_end:ZEBOIM_STATION_RETIRED_GRAPHICS_BLOCK_OFFSET
            ],
        )
        station_block = output_graphics[
            ZEBOIM_STATION_RETIRED_GRAPHICS_BLOCK_OFFSET:
        ]
        retail_block = target_graphics[
            ZEBOIM_STATION_RETIRED_GRAPHICS_BLOCK_OFFSET:
        ]
        self.assertEqual(len(station_block), 0x2000)
        self.assertEqual(station_block[:0x800], retail_block[:0x800])
        self.assertEqual(
            hashlib.sha256(station_block).hexdigest(),
            ZEBOIM_STATION_TEXTURE_UPLOAD_SHA256,
        )
        for chunk_offset, data_size in (
            (0x800, 40 * 25 * 2),
            (0x1000, 40 * 25 * 2),
            (0x1800, 40 * 14 * 2),
        ):
            with self.subTest(chunk_padding=chunk_offset):
                self.assertEqual(
                    station_block[chunk_offset + data_size : chunk_offset + 0x800],
                    retail_block[chunk_offset + data_size : chunk_offset + 0x800],
                )
        source_clut = _graphics_rows(
            donor_vram,
            ZEBOIM_STATION_SOURCE_CLUT_RECT,
        )
        source_texture = _graphics_rows(
            donor_vram,
            ZEBOIM_STATION_SOURCE_TEXTURE_RECT,
        )
        self.assertEqual(
            hashlib.sha256(source_clut).hexdigest(),
            ZEBOIM_STATION_CLUT_ROWS_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(source_texture).hexdigest(),
            ZEBOIM_STATION_TEXTURE_ROWS_SHA256,
        )
        atlas_texture = bytearray(
            _graphics_rows(target_vram, ZEBOIM_STATION_RETIRED_TEXTURE_RECT)
        )
        occupied: set[tuple[int, int]] = set()
        for source, target in ZEBOIM_STATION_TEXTURE_ATLAS:
            source_u, source_v, width, height = source
            target_u, target_v = target
            island = {
                (target_u + x, target_v + y)
                for y in range(height)
                for x in range(width)
            }
            self.assertFalse(occupied & island)
            occupied.update(island)
            for row in range(height):
                source_start = (
                    source_v
                    - ZEBOIM_STATION_SOURCE_TEXTURE_RECT[1]
                    + row
                ) * ZEBOIM_STATION_SOURCE_TEXTURE_PIXEL_WIDTH + source_u
                target_start = (
                    (target_v + row)
                    * ZEBOIM_STATION_TARGET_TEXTURE_PIXEL_WIDTH
                    + target_u
                )
                atlas_texture[target_start : target_start + width] = (
                    source_texture[source_start : source_start + width]
                )
        atlas_texture = bytes(atlas_texture)
        self.assertEqual(len(occupied), 4_288)
        self.assertEqual((max(x for x, _y in occupied), max(y for _x, y in occupied)), (77, 61))
        self.assertEqual(
            hashlib.sha256(atlas_texture).hexdigest(),
            ZEBOIM_STATION_ATLAS_TEXTURE_ROWS_SHA256,
        )
        self.assertEqual(
            _graphics_rows(output_vram, ZEBOIM_STATION_TARGET_CLUT_RECT),
            source_clut,
        )
        self.assertEqual(
            _graphics_rows(output_vram, ZEBOIM_STATION_TARGET_TEXTURE_RECT),
            atlas_texture,
        )

        # Restoring the retired palette/texture allocation must recover every
        # original VRAM word.
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
        self.assertEqual(masked_output, target_vram)

    @unittest.skipUnless(
        STATION_FIXTURES_PRESENT,
        "retail field-373 station fixtures are absent",
    )
    def test_zeboim_station_remains_within_field_673_staging_budget(self) -> None:
        (
            header,
            _models_component,
            graphics,
            donor_header,
            donor_models,
            donor_graphics,
        ) = _station_inputs()
        components = [
            (DONOR / f"{index:02d}_{name}.bin").read_bytes()
            for index, name in enumerate(STREAM_NAMES)
        ]
        _ignored_header, components[2] = patch_cloning_chamber_warheads(
            (DONOR / "header.bin").read_bytes(),
            components[2],
        )
        header, components[2], output_graphics = (
            patch_cloning_chamber_zeboim_station(
                header,
                components[2],
                graphics,
                donor_header,
                donor_models,
                donor_graphics,
            )
        )
        bundle = build_field(header, components, compact=True)
        self.assertEqual(len(bundle), 91_364)
        self.assertEqual(0x18000 - len(bundle), 6_940)
        self.assertLess(len(bundle), 0x18000)
        self.assertEqual(len(output_graphics), 102_400)
        reparsed = parse_field(bundle)
        self.assertEqual(reparsed.header[0x190:], header[0x190:])
        self.assertEqual([part.data for part in reparsed.parts], components)

    @unittest.skipUnless(
        PEDESTAL_FIXTURES_PRESENT,
        "retail field-673 pedestal fixtures are absent",
    )
    def test_archive_pedestal_rejects_unpatched_or_drifted_inputs(self) -> None:
        header = (DONOR / "header.bin").read_bytes()
        models = (DONOR / "02_models.bin").read_bytes()
        graphics = FIELD_673_GRAPHICS.read_bytes()
        with self.assertRaisesRegex(
            CloningWarheadModelError,
            "warhead-patched field 673 header",
        ):
            patch_cloning_chamber_archive_pedestal(header, models, graphics)

        patched_header, patched_models = patch_cloning_chamber_warheads(
            header,
            models,
        )
        damaged_header = bytearray(patched_header)
        damaged_header[0x190] ^= 1
        with self.assertRaisesRegex(
            CloningWarheadModelError,
            "warhead-patched field 673 header",
        ):
            patch_cloning_chamber_archive_pedestal(
                bytes(damaged_header), patched_models, graphics
            )

        damaged_models = bytearray(patched_models)
        damaged_models[-1] ^= 1
        with self.assertRaisesRegex(
            CloningWarheadModelError,
            "warhead-patched field 673 models",
        ):
            patch_cloning_chamber_archive_pedestal(
                patched_header, bytes(damaged_models), graphics
            )

        damaged_graphics = bytearray(graphics)
        damaged_graphics[-1] ^= 1
        with self.assertRaisesRegex(
            CloningWarheadModelError,
            "retail field 673 graphics",
        ):
            patch_cloning_chamber_archive_pedestal(
                patched_header, patched_models, bytes(damaged_graphics)
            )

        pedestal_header, pedestal_models, pedestal_graphics = (
            patch_cloning_chamber_archive_pedestal(
                patched_header, patched_models, graphics
            )
        )
        with self.assertRaisesRegex(
            CloningWarheadModelError,
            "warhead-patched field 673 header",
        ):
            patch_cloning_chamber_archive_pedestal(
                pedestal_header, pedestal_models, pedestal_graphics
            )

    @unittest.skipUnless(DONOR.is_dir(), "retail field-673 extraction is absent")
    def test_retail_patch_preserves_room_and_replaces_only_vat_nodes(self) -> None:
        header = (DONOR / "header.bin").read_bytes()
        models = (DONOR / "02_models.bin").read_bytes()
        patched_header, patched_models = patch_cloning_chamber_warheads(
            header,
            models,
        )

        self.assertEqual(
            hashlib.sha256(patched_header).hexdigest(),
            PATCHED_FIELD_673_HEADER_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(patched_models).hexdigest(),
            PATCHED_FIELD_673_MODELS_SHA256,
        )
        self.assertEqual(
            patch_cloning_chamber_warheads(header, models),
            (patched_header, patched_models),
        )

        source_entries = _models(models)
        patched_entries = _models(patched_models)
        self.assertEqual((len(source_entries), len(patched_entries)), (20, 21))
        self.assertEqual(patched_entries[:20], source_entries)

        warhead = patched_entries[WARHEAD_MODEL_INDEX]
        self.assertEqual(len(warhead), 4916)
        self.assertEqual(
            hashlib.sha256(warhead).hexdigest(),
            "c4395859e42c495b474db857ddb560be89ea012c60fcf71dc553268948c87c2d",
        )
        self.assertEqual(struct.unpack_from("<I", warhead)[0], 1)
        self.assertEqual(
            struct.unpack_from("<HHH", warhead, 0x12),
            (185, 280, 1),
        )
        vertex_offset = struct.unpack_from("<I", warhead, 0x18)[0]
        mesh_offset = struct.unpack_from("<I", warhead, 0x20)[0]
        display_offset = struct.unpack_from("<I", warhead, 0x24)[0]
        self.assertEqual(
            (vertex_offset, mesh_offset, display_offset),
            (0x48, 0x610, 0xED4),
        )
        self.assertEqual(
            (
                struct.unpack_from("<hhh", warhead, 0x30),
                struct.unpack_from("<hhh", warhead, 0x38),
            ),
            ((-70, -660, -70), (70, WARHEAD_FLOOR_Y, 70)),
        )
        self.assertEqual(
            struct.unpack_from("<BBH", warhead, mesh_offset),
            (0x04, 119, 280),
        )
        self.assertEqual(len(warhead) - display_offset, 280 * 4)
        self.assertTrue(
            all(
                warhead[offset + 3] == 0x20
                for offset in range(display_offset, len(warhead), 4)
            )
        )

        vertices = tuple(
            struct.unpack_from("<hhhh", warhead, vertex_offset + index * 8)
            for index in range(185)
        )
        floor_vertices = tuple(
            vertex for vertex in vertices if vertex[1] == WARHEAD_FLOOR_Y
        )
        self.assertEqual(len(floor_vertices), 16)
        self.assertEqual(max(vertex[1] for vertex in vertices), WARHEAD_FLOOR_Y)
        self.assertTrue(
            all(
                vertex[0] ** 2 + vertex[2] ** 2
                <= WARHEAD_FOOTPRINT_RADIUS**2
                for vertex in vertices
            )
        )
        self.assertTrue(
            {
                (70, WARHEAD_FLOOR_Y, -16),
                (70, WARHEAD_FLOOR_Y, 16),
                (-70, WARHEAD_FLOOR_Y, -16),
                (-70, WARHEAD_FLOOR_Y, 16),
                (-16, WARHEAD_FLOOR_Y, 70),
                (16, WARHEAD_FLOOR_Y, 70),
                (-16, WARHEAD_FLOOR_Y, -70),
                (16, WARHEAD_FLOOR_Y, -70),
            }.issubset(
                {(vertex[0], vertex[1], vertex[2]) for vertex in floor_vertices}
            )
        )

        changed_nodes = set(PARKED_VAT_NODE_INDICES) | set(WARHEAD_NODE_INDICES)
        for index in range(70):
            with self.subTest(node=index):
                if index not in changed_nodes:
                    self.assertEqual(_node(patched_header, index), _node(header, index))
        for index in PARKED_VAT_NODE_INDICES:
            original = _node(header, index)
            patched = _node(patched_header, index)
            self.assertEqual(patched[:5], original[:5])
            self.assertEqual(patched[5], PARKED_VAT_Y)
            self.assertEqual(patched[6:], original[6:])
        for index, (x, y, z) in zip(
            WARHEAD_NODE_INDICES,
            WARHEAD_PLACEMENTS,
            strict=True,
        ):
            self.assertEqual(
                _node(patched_header, index),
                (0x0010, 0, 0, 0, x, y, z, WARHEAD_MODEL_INDEX),
            )

        components = [
            (DONOR / f"{index:02d}_{name}.bin").read_bytes()
            for index, name in enumerate(STREAM_NAMES)
        ]
        components[2] = patched_models
        bundle = build_field(patched_header, components, compact=True)
        self.assertEqual(len(bundle), 97_636)
        self.assertLess(len(bundle), 0x18000)
        reparsed = parse_field(bundle)
        self.assertEqual(reparsed.header[0x190:], patched_header[0x190:])
        self.assertEqual([part.data for part in reparsed.parts], components)

    @unittest.skipUnless(
        PEDESTAL_FIXTURES_PRESENT,
        "retail field-673 pedestal fixtures are absent",
    )
    def test_archive_pedestal_reuses_only_native_models_and_nodes(self) -> None:
        source_header = (DONOR / "header.bin").read_bytes()
        source_models = (DONOR / "02_models.bin").read_bytes()
        graphics = FIELD_673_GRAPHICS.read_bytes()
        patched_header, patched_models = patch_cloning_chamber_warheads(
            source_header,
            source_models,
        )
        pedestal_header, pedestal_models, pedestal_graphics = (
            patch_cloning_chamber_archive_pedestal(
                patched_header, patched_models, graphics
            )
        )

        self.assertEqual(
            patch_cloning_chamber_archive_pedestal(
                patched_header, patched_models, graphics
            ),
            (pedestal_header, pedestal_models, pedestal_graphics),
        )
        self.assertEqual(
            hashlib.sha256(pedestal_header).hexdigest(),
            ARCHIVE_PEDESTAL_FIELD_673_HEADER_SHA256,
        )
        self.assertEqual(
            (
                len(pedestal_models),
                hashlib.sha256(pedestal_models).hexdigest(),
            ),
            (
                ARCHIVE_PEDESTAL_FIELD_673_MODELS_SIZE,
                ARCHIVE_PEDESTAL_FIELD_673_MODELS_SHA256,
            ),
        )
        self.assertEqual(
            (
                len(pedestal_graphics),
                hashlib.sha256(pedestal_graphics).hexdigest(),
            ),
            (
                ARCHIVE_PEDESTAL_FIELD_673_GRAPHICS_SIZE,
                ARCHIVE_PEDESTAL_FIELD_673_GRAPHICS_SHA256,
            ),
        )
        self.assertEqual(
            (
                ARCHIVE_PEDESTAL_FIELD_673_GRAPHICS_SIZE,
                ARCHIVE_PEDESTAL_FIELD_673_GRAPHICS_SHA256,
            ),
            (RETAIL_FIELD_673_GRAPHICS_SIZE, RETAIL_FIELD_673_GRAPHICS_SHA256),
        )
        self.assertEqual(
            (
                ARCHIVE_PEDESTAL_FIELD_673_GRAPHICS_SIZE,
                ARCHIVE_PEDESTAL_FIELD_673_GRAPHICS_SHA256,
            ),
            (
                102_400,
                "e58a4c0f5aacffbf500c31879e0795238af402d3bfb8d83dfca46df454dca2ed",
            ),
        )
        self.assertIs(pedestal_graphics, graphics)

        patched_entries = _models(patched_models)
        pedestal_entries = _models(pedestal_models)
        self.assertEqual((len(patched_entries), len(pedestal_entries)), (21, 21))
        self.assertEqual(CLONING_ARCHIVE_PEDESTAL_MODEL_INDICES, (2, 4, 6))
        self.assertEqual(pedestal_entries[2:], patched_entries[2:])
        self.assertEqual(CLONING_ARCHIVE_PEDESTAL_RETIRED_MODEL_INDICES, (0, 1))
        self.assertEqual(CLONING_ARCHIVE_PEDESTAL_COMPACTION_MODEL_INDEX, 6)
        compact_model = patched_entries[
            CLONING_ARCHIVE_PEDESTAL_COMPACTION_MODEL_INDEX
        ]
        self.assertEqual(
            hashlib.sha256(compact_model).hexdigest(),
            CLONING_ARCHIVE_PEDESTAL_COMPACTION_MODEL_SHA256,
        )
        for index in CLONING_ARCHIVE_PEDESTAL_RETIRED_MODEL_INDICES:
            with self.subTest(compacted_model=index):
                self.assertEqual(pedestal_entries[index], compact_model)
        self.assertEqual(
            tuple(
                hashlib.sha256(pedestal_entries[index]).hexdigest()
                for index in CLONING_ARCHIVE_PEDESTAL_MODEL_INDICES
            ),
            CLONING_ARCHIVE_PEDESTAL_MODEL_SHA256S,
        )
        self.assertEqual(
            pedestal_entries[WARHEAD_MODEL_INDEX],
            patched_entries[WARHEAD_MODEL_INDEX],
        )
        self.assertEqual(
            hashlib.sha256(pedestal_entries[WARHEAD_MODEL_INDEX]).hexdigest(),
            "c4395859e42c495b474db857ddb560be89ea012c60fcf71dc553268948c87c2d",
        )

        for node_index, source_model, model_index, flags in zip(
            CLONING_ARCHIVE_PEDESTAL_NODE_INDICES,
            CLONING_ARCHIVE_PEDESTAL_SOURCE_NODE_MODELS,
            CLONING_ARCHIVE_PEDESTAL_MODEL_INDICES,
            CLONING_ARCHIVE_PEDESTAL_NODE_FLAGS,
            strict=True,
        ):
            with self.subTest(pedestal_node=node_index):
                self.assertEqual(
                    _node(patched_header, node_index),
                    (0, 0, 0, 0, 1322, PARKED_VAT_Y, 0, source_model),
                )
                self.assertEqual(
                    _node(pedestal_header, node_index),
                    (
                        flags,
                        0,
                        CLONING_ARCHIVE_PEDESTAL_Y_ROTATION,
                        0,
                        *CLONING_ARCHIVE_PEDESTAL_PLACEMENT,
                        model_index,
                    ),
                )
        self.assertEqual(CLONING_ARCHIVE_PEDESTAL_NODE_INDICES, (22, 23, 24))
        self.assertEqual(CLONING_ARCHIVE_PEDESTAL_NODE_FLAGS, (0, 0x10, 0x8000))
        self.assertEqual(CLONING_ARCHIVE_PEDESTAL_PLACEMENT, (1161, 0, 396))
        for index in range(70):
            with self.subTest(preserved_pedestal_node=index):
                if index not in CLONING_ARCHIVE_PEDESTAL_NODE_INDICES:
                    self.assertEqual(
                        _node(pedestal_header, index),
                        _node(patched_header, index),
                    )
        for index, (x, y, z) in zip(
            WARHEAD_NODE_INDICES,
            WARHEAD_PLACEMENTS,
            strict=True,
        ):
            self.assertEqual(
                _node(pedestal_header, index),
                (0x0010, 0, 0, 0, x, y, z, WARHEAD_MODEL_INDEX),
            )

        placement_x, placement_y, placement_z = (
            CLONING_ARCHIVE_PEDESTAL_PLACEMENT
        )
        local_bounds = [
            (
                struct.unpack_from("<hhh", pedestal_entries[index], 0x30),
                struct.unpack_from("<hhh", pedestal_entries[index], 0x38),
            )
            for index in CLONING_ARCHIVE_PEDESTAL_MODEL_INDICES
        ]
        world_bounds = (
            placement_x + min(bounds[0][0] for bounds in local_bounds),
            placement_x + max(bounds[1][0] for bounds in local_bounds),
            placement_y + min(bounds[0][1] for bounds in local_bounds),
            placement_y + max(bounds[1][1] for bounds in local_bounds),
            placement_z + min(bounds[0][2] for bounds in local_bounds),
            placement_z + max(bounds[1][2] for bounds in local_bounds),
        )
        self.assertEqual(world_bounds, CLONING_ARCHIVE_PEDESTAL_WORLD_BOUNDS)
        self.assertEqual(world_bounds, (466, 534, -197, 44, -36, 35))
        self.assertEqual(
            (
                round((world_bounds[0] + world_bounds[1]) / 2),
                placement_y,
                round((world_bounds[4] + world_bounds[5]) / 2),
            ),
            CLONING_ARCHIVE_PEDESTAL_VISUAL_CENTER,
        )

    @unittest.skipUnless(
        PEDESTAL_FIXTURES_PRESENT,
        "retail field-673 pedestal fixtures are absent",
    )
    def test_archive_pedestal_remains_within_field_673_staging_budget(
        self,
    ) -> None:
        header = (DONOR / "header.bin").read_bytes()
        graphics = FIELD_673_GRAPHICS.read_bytes()
        components = [
            (DONOR / f"{index:02d}_{name}.bin").read_bytes()
            for index, name in enumerate(STREAM_NAMES)
        ]
        header, components[2] = patch_cloning_chamber_warheads(
            header,
            components[2],
        )
        header, components[2], output_graphics = (
            patch_cloning_chamber_archive_pedestal(
                header, components[2], graphics
            )
        )
        bundle = build_field(header, components, compact=True)

        self.assertEqual(len(bundle), 89_656)
        self.assertLess(len(bundle), 0x18000)
        self.assertEqual(0x18000 - len(bundle), 8_648)
        self.assertEqual(len(components[2]), ARCHIVE_PEDESTAL_FIELD_673_MODELS_SIZE)
        self.assertEqual(output_graphics, graphics)
        self.assertEqual(
            len(output_graphics) - RETAIL_FIELD_673_GRAPHICS_SIZE,
            0,
        )
        reparsed = parse_field(bundle)
        self.assertEqual(reparsed.header[0x190:], header[0x190:])
        self.assertEqual([part.data for part in reparsed.parts], components)


if __name__ == "__main__":
    unittest.main()
