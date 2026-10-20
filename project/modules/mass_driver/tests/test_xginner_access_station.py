from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT
from shared.tools.xgdialog import parse_dialogue

import hashlib
from pathlib import Path
import struct
import unittest

from tools.build_mass_driver_dungeon import (
    CLONES,
    MODEL_INDEX,
    SCRIPT_INDEX,
    SPRITE_INDEX,
    _automatic_dialogue_body,
    _prepare_clone,
    _solid_station_controller_init,
    _static_door_controller_init,
)
from tools.xgcloning_warheads import _graphics_rows, _reconstruct_graphics_vram
from tools.xginner_access_station import (
    INNER_ACCESS_NATIVE_RELOCATED_CLUT,
    INNER_ACCESS_NATIVE_TEXTURE_RECTS,
    INNER_ACCESS_NATIVE_USED_INDICES,
    INNER_ACCESS_STATION_ATLAS_HEIGHT,
    INNER_ACCESS_STATION_ATLAS_V,
    INNER_ACCESS_STATION_ATLAS_WIDTH,
    INNER_ACCESS_STATION_APPROACH_POSITION,
    INNER_ACCESS_STATION_COLLIDER_ENTITY,
    INNER_ACCESS_STATION_COLLIDER_POSITION,
    INNER_ACCESS_STATION_COLLISION_OPERAND,
    INNER_ACCESS_STATION_CONTROLLER_ENTITY,
    INNER_ACCESS_STATION_CONTROLLER_POSITION,
    INNER_ACCESS_STATION_CONTROLLER_TRIANGLE,
    INNER_ACCESS_STATION_INTERACTION_HALF_WIDTH,
    INNER_ACCESS_STATION_NODE_FLAGS,
    INNER_ACCESS_STATION_OUTPUT_GRAPHICS_SHA256,
    INNER_ACCESS_STATION_OUTPUT_HEADER_SHA256,
    INNER_ACCESS_STATION_OUTPUT_MODELS_SHA256,
    INNER_ACCESS_STATION_OUTPUT_SPRITES_SHA256,
    INNER_ACCESS_STATION_PLACEMENT,
    INNER_ACCESS_STATION_TARGET_CLUT,
    INNER_ACCESS_STATION_TARGET_MODEL_INDEX,
    INNER_ACCESS_STATION_TARGET_TPAGES,
    INNER_ACCESS_STATION_WORLD_BOUNDS,
    INNER_ACCESS_STATION_Y_ROTATION,
    patch_inner_access_zeboim_station,
)
from tools.xgscript import AtelScript
from tools.xgsubway_station import _indexed_entries


def _sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


class InnerAccessZeboimStationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project = REPOSITORY_ROOT
        cls.input_root = cls.project / "work"
        cls.dialogue_root = cls.project / "modules" / "mass_driver" / "content"
        cls.spec = next(spec for spec in CLONES if spec.target_field == 727)
        source = cls.input_root / "reference_fields" / "field_377"
        donor = cls.input_root / "audit_zeboim_cd1" / "field_373"
        cls.original = (
            (source / "header.bin").read_bytes(),
            (source / "02_models.bin").read_bytes(),
            (source / "04_sprites.bin").read_bytes(),
            (
                cls.input_root
                / "reference_fields"
                / "cd1_zeboim"
                / "1361.bin"
            ).read_bytes(),
        )
        cls.output = patch_inner_access_zeboim_station(
            *cls.original,
            (donor / "header.bin").read_bytes(),
            (donor / "02_models.bin").read_bytes(),
            (cls.input_root / "audit_zeboim_cd1" / "1353.bin").read_bytes(),
            (
                cls.input_root
                / "reference_fields"
                / "cd1_cloning"
                / "1953.bin"
            ).read_bytes(),
        )

    def test_header_inserts_collider_and_frontage_before_station(self) -> None:
        old_header = self.original[0]
        header = self.output[0]
        self.assertEqual((len(header), _sha256(header)), (768, INNER_ACCESS_STATION_OUTPUT_HEADER_SHA256))
        self.assertEqual(struct.unpack_from("<H", header, 0x18C)[0], 23)
        old_records = [
            old_header[0x190 + index * 16 : 0x190 + (index + 1) * 16]
            for index in range(20)
        ]
        new_records = [
            header[0x190 + index * 16 : 0x190 + (index + 1) * 16]
            for index in range(23)
        ]
        self.assertEqual(new_records[:18], old_records[:18])
        self.assertEqual(new_records[20:22], old_records[18:20])
        self.assertEqual(
            new_records[18],
            bytes.fromhex("e0010000000000006dff0000d6ff0000"),
        )
        self.assertEqual(
            new_records[19],
            bytes.fromhex("e00100000000000094ff0000d6ff0000"),
        )
        self.assertEqual(
            struct.unpack("<HhhhhhhH", new_records[22]),
            (
                INNER_ACCESS_STATION_NODE_FLAGS,
                0,
                INNER_ACCESS_STATION_Y_ROTATION,
                0,
                *INNER_ACCESS_STATION_PLACEMENT,
                INNER_ACCESS_STATION_TARGET_MODEL_INDEX,
            ),
        )
        self.assertEqual(INNER_ACCESS_STATION_WORLD_BOUNDS[3], -4.0)

    def test_station_model_and_registered_sprite_carrier_are_exact(self) -> None:
        old_models = _indexed_entries(self.original[1], label="old field-377 models")
        models = _indexed_entries(self.output[1], label="station field-377 models")
        self.assertEqual((len(self.output[1]), _sha256(self.output[1])), (5_396, INNER_ACCESS_STATION_OUTPUT_MODELS_SHA256))
        self.assertEqual(len(models), 6)
        self.assertEqual(models[3], old_models[3])
        station = models[INNER_ACCESS_STATION_TARGET_MODEL_INDEX]
        for value in INNER_ACCESS_STATION_TARGET_TPAGES:
            self.assertIn(struct.pack("<H", value), station)
        self.assertIn(struct.pack("<H", INNER_ACCESS_STATION_TARGET_CLUT), station)
        for index in (0, 1, 2, 4):
            self.assertIn(
                struct.pack("<H", INNER_ACCESS_NATIVE_RELOCATED_CLUT),
                models[index],
            )

        old_bank = _indexed_entries(self.original[2], label="old sprites")[0]
        new_bank = _indexed_entries(self.output[2], label="new sprites")[0]
        old_image = _indexed_entries(old_bank, label="old bank")[0]
        new_image = _indexed_entries(new_bank, label="new bank")[0]
        self.assertEqual((len(self.output[2]), _sha256(self.output[2])), (24_596, INNER_ACCESS_STATION_OUTPUT_SPRITES_SHA256))
        self.assertEqual(struct.unpack_from("<HH", new_image), (64, 192))
        self.assertEqual(new_image[4 : 4 + 128 * 77], old_image[4:])
        self.assertEqual(new_image[4 + 128 * 77 : 4 + 128 * 128], bytes(128 * 51))
        atlas = b"".join(
            new_image[
                4 + (INNER_ACCESS_STATION_ATLAS_V + row) * 128 :
                4
                + (INNER_ACCESS_STATION_ATLAS_V + row) * 128
                + INNER_ACCESS_STATION_ATLAS_WIDTH
            ]
            for row in range(INNER_ACCESS_STATION_ATLAS_HEIGHT)
        )
        self.assertEqual(
            (
                INNER_ACCESS_STATION_ATLAS_WIDTH,
                INNER_ACCESS_STATION_ATLAS_HEIGHT,
            ),
            (80, 64),
        )
        self.assertEqual(
            _sha256(atlas),
            "a6ee4c693587c5f68d8777ef60007ca178a744cad66b9d92ea5a85dfe424f129",
        )

    def test_native_8bpp_colours_survive_sparse_palette_remap(self) -> None:
        old_vram, old_rectangles = _reconstruct_graphics_vram(
            self.original[3], label="old field 377"
        )
        new_vram, new_rectangles = _reconstruct_graphics_vram(
            self.output[3], label="station field 377"
        )
        self.assertEqual(old_rectangles, new_rectangles)
        self.assertEqual((len(self.output[3]), _sha256(self.output[3])), (116_736, INNER_ACCESS_STATION_OUTPUT_GRAPHICS_SHA256))
        old_palette = _graphics_rows(old_vram, (0, 482, 256, 1))
        new_native_palette = _graphics_rows(new_vram, (0, 481, 256, 1))
        mapping = {
            source: 90 + index
            for index, source in enumerate(INNER_ACCESS_NATIVE_USED_INDICES)
        }
        sampled = set()
        for u, v, width, height in INNER_ACCESS_NATIVE_TEXTURE_RECTS:
            for row in range(height):
                for column in range(width):
                    old_offset = ((v + row) * 1024 + 512) * 2 + u + column
                    old_index = old_vram[old_offset]
                    new_index = new_vram[old_offset]
                    sampled.add(old_index)
                    self.assertEqual(new_index, mapping[old_index])
                    self.assertEqual(
                        old_palette[old_index * 2 : old_index * 2 + 2],
                        new_native_palette[new_index * 2 : new_index * 2 + 2],
                    )
        self.assertEqual(tuple(sorted(sampled)), tuple(INNER_ACCESS_NATIVE_USED_INDICES))
        self.assertEqual(
            _sha256(_graphics_rows(new_vram, (0, 482, 256, 1))),
            "7754aac52c72639ecd632cbac7a46c73b0a2873ca1091dcb67325ba2508c1065",
        )

    def test_prepared_target_has_local_repeatable_notice(self) -> None:
        prepared = _prepare_clone(self.spec, self.input_root, self.dialogue_root)
        self.assertEqual(
            (len(prepared.bundle), _sha256(prepared.bundle)),
            (
                44_052,
                "e7fc02e7c4b1f061729bebb4aa439b1717acc05f8e7e9fa5d11b2d01f86bf124",
            ),
        )
        editor = AtelScript(prepared.components[SCRIPT_INDEX])
        self.assertEqual(editor.entity_count, 20)

        collider_x, collider_z = INNER_ACCESS_STATION_COLLIDER_POSITION
        expected_collider = _solid_station_controller_init(
            collider_x,
            collider_z,
            requires_facing=False,
            collision_operand=INNER_ACCESS_STATION_COLLISION_OPERAND,
            interaction_enabled=False,
        )
        collider_init = editor.get_script_pointer(
            INNER_ACCESS_STATION_COLLIDER_ENTITY, 0
        )
        self.assertEqual(
            editor.bytecode[
                collider_init : collider_init + len(expected_collider)
            ],
            expected_collider,
        )
        self.assertEqual(expected_collider[0], 0x0B)
        self.assertIn(bytes.fromhex("F8 00 10 00 23 2A 00"), expected_collider)
        self.assertEqual(
            editor.get_script_pointer(INNER_ACCESS_STATION_COLLIDER_ENTITY, 2),
            editor.get_script_pointer(INNER_ACCESS_STATION_COLLIDER_ENTITY, 3),
        )

        controller_x, controller_z = INNER_ACCESS_STATION_CONTROLLER_POSITION
        expected_controller = _static_door_controller_init(
            controller_x,
            controller_z,
            requires_facing=True,
            interaction_half_width=INNER_ACCESS_STATION_INTERACTION_HALF_WIDTH,
        )
        controller_init = editor.get_script_pointer(
            INNER_ACCESS_STATION_CONTROLLER_ENTITY, 0
        )
        self.assertEqual(
            editor.bytecode[
                controller_init : controller_init + len(expected_controller)
            ],
            expected_controller,
        )
        self.assertIn(bytes.fromhex("F8 03 04 00"), expected_controller)
        action = editor.get_script_pointer(
            INNER_ACCESS_STATION_CONTROLLER_ENTITY, 2
        )
        expected_action = _automatic_dialogue_body((4,), routine_pc=action) + b"\x00"
        self.assertEqual(editor.bytecode[action : action + len(expected_action)], expected_action)
        self.assertNotIn(bytes.fromhex("A3"), expected_action)
        approach_x, approach_z = INNER_ACCESS_STATION_APPROACH_POSITION
        effective_reach = INNER_ACCESS_STATION_INTERACTION_HALF_WIDTH * 2 + 16
        self.assertLessEqual(abs(approach_x - controller_x), effective_reach)
        self.assertLessEqual(abs(approach_z - controller_z), effective_reach)
        for side_or_rear_position in (
            (-147, -97),
            (-147, 14),
            (-205, -42),
        ):
            with self.subTest(outside_frontage=side_or_rear_position):
                side_x, side_z = side_or_rear_position
                self.assertTrue(
                    abs(side_x - controller_x) > effective_reach
                    or abs(side_z - controller_z) > effective_reach
                )

        notice = " ".join(
            parse_dialogue(prepared.components[7]).blocks[4].text
            .replace("<New>", " ").split()
        )
        for phrase in (
            "PERSONNEL DESK",
            "STORED SHIFT NOTICE",
            "Clock in before reporting to your section.",
            "Record your departure at the end of the shift.",
            "contact the shift supervisor.",
            "Do not leave an operating control station unattended.",
            "Do not lend access badges.",
        ):
            self.assertIn(phrase, notice)


if __name__ == "__main__":
    unittest.main()
