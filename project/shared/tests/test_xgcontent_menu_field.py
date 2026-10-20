from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import unittest

from tools import build_mass_driver_dungeon as mass_driver
from tools import build_surface_soylent_dungeon as surface
from tools import xgcontent_menu
from tools import xgcontent_menu_field as menu
from tools.xgfield import parse_field
from tools.xgscript import AtelScript, SCRIPTS_PER_ENTITY


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MASS_FIELD_376_BUNDLE = (
    PROJECT_ROOT
    / "work"
    / "mass_driver_v167_stage"
    / "replacements"
    / "1358_field_376.bin"
)
MASS_FIELD_376_GRAPHICS = (
    PROJECT_ROOT
    / "work"
    / "mass_driver_v167_stage"
    / "replacements"
    / "1359_field_376_graphics.bin"
)
RETAIL_TITLE_FIELD = PROJECT_ROOT / "work" / "rico_arc_audit" / "disc1" / "1586.bin"


class ContentMenuFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_bundle = MASS_FIELD_376_BUNDLE.read_bytes()
        cls.source_graphics = MASS_FIELD_376_GRAPHICS.read_bytes()
        (
            cls.menu_bundle,
            cls.menu_graphics,
            cls.menu_atlas,
        ) = menu.build_content_menu_field(
            cls.source_bundle,
            cls.source_graphics,
        )
        cls.source_field = parse_field(cls.source_bundle)
        cls.menu_field = parse_field(cls.menu_bundle)
        cls.menu_editor = AtelScript(
            cls.menu_field.parts[mass_driver.SCRIPT_INDEX].data
        )

    def test_disc2_slot_and_four_card_selection_contract_are_explicit(self) -> None:
        self.assertEqual(menu.CONTENT_MENU_FIELD, 63)
        self.assertEqual(menu.CONTENT_MENU_BUNDLE_CANONICAL_ID, 732)
        self.assertEqual(menu.CONTENT_MENU_GRAPHICS_CANONICAL_ID, 733)
        self.assertEqual(menu.CONTENT_MENU_SELECTION_RING, (0, 1, 3))
        self.assertEqual(
            [(card.selection, card.label, card.enabled) for card in menu.CONTENT_MENU_CARDS],
            [
                (0, "MASS DRIVER", True),
                (1, "SURFACE SOYLENT", True),
                (2, "MAHANON - COMING SOON", False),
                (3, "RICO'S ARC", True),
            ],
        )
        for index, card in enumerate(menu.CONTENT_MENU_CARDS):
            x, y, width, height = card.rect
            self.assertGreater(width, 0)
            self.assertGreater(height, 0)
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(x + width, 320)
            self.assertLessEqual(y + height, 224)
            for other in menu.CONTENT_MENU_CARDS[index + 1 :]:
                self.assertFalse(menu._rectangles_overlap(card.rect, other.rect))

    def test_builder_is_deterministic_and_preserves_non_script_components(self) -> None:
        rebuilt = menu.build_content_menu_field(
            self.source_bundle,
            self.source_graphics,
        )
        self.assertEqual(
            rebuilt,
            (self.menu_bundle, self.menu_graphics, self.menu_atlas),
        )
        self.assertLess(len(self.menu_bundle), 0x40000)
        self.assertEqual(len(self.menu_field.header), len(self.source_field.header))
        self.assertEqual(
            self.menu_field.header[0x18C:],
            self.source_field.header[0x18C:],
        )
        for index, (before, after) in enumerate(
            zip(self.source_field.parts, self.menu_field.parts, strict=True)
        ):
            if index == mass_driver.SCRIPT_INDEX:
                self.assertNotEqual(before.data, after.data)
            else:
                self.assertEqual(before.data, after.data)
        self.assertEqual(
            hashlib.sha256(self.menu_bundle).hexdigest(),
            "3120a6993d827ec141a5612f75a02c07eaafab9fdf9b13b79448fdbee5980acc",
        )

    def test_atlas_is_embedded_in_graphics_733_not_global_file_2477(self) -> None:
        self.assertEqual(
            self.menu_atlas,
            xgcontent_menu.build_content_menu_atlas_tim(),
        )
        self.assertEqual(len(self.menu_atlas), 8_212)
        self.assertEqual(
            hashlib.sha256(self.menu_atlas).hexdigest(),
            "e4bf77e4587e6661390976e8da0743e53e0117211d81b1a9258dbf1715684dac",
        )
        self.assertTrue(self.menu_graphics.startswith(self.source_graphics))
        appended = self.menu_graphics[len(self.source_graphics) :]
        self.assertEqual(len(appended), 10_240)
        self.assertEqual(struct.unpack_from("<H", appended, 0)[0], 0x1200)
        self.assertEqual(
            struct.unpack_from("<8H", appended, 4),
            (640, 0, 0, 384, 64, 16, 1, 4),
        )
        self.assertEqual(
            struct.unpack_from("<4H", appended, 0x1C),
            (16, 16, 16, 16),
        )
        _vram, rectangles = mass_driver._reconstruct_field_graphics_vram(
            self.menu_graphics,
            label="test field 63",
        )
        self.assertEqual(rectangles[-1], (640, 384, 64, 64))
        # FE77 selector 12 would alias live canonical 2477.  The atlas is
        # present before ATEL starts, so field 63 never invokes LOAD_TIM.
        self.assertNotIn(b"\xFE\x77", self.menu_editor.bytecode)
        self.assertEqual(
            hashlib.sha256(self.menu_graphics).hexdigest(),
            "4fc7dd41040546c2d922e9be2919a570123f7c4750d3335160e5c8142dcdbaf9",
        )

    def test_retail_archive_scripts_are_removed_and_only_menu_actors_run(self) -> None:
        editor = self.menu_editor
        self.assertEqual(editor.entity_count, 28)
        self.assertLess(editor.bytecode_size, 0x2000)
        for entity in range(editor.entity_count):
            pointers = [
                editor.get_script_pointer(entity, script_index)
                for script_index in range(SCRIPTS_PER_ENTITY)
            ]
            if entity == 0:
                self.assertNotEqual(pointers[0], 0)
                self.assertNotEqual(pointers[1], 0)
                self.assertEqual(pointers[2:], [0] * 30)
            elif entity == menu.CONTENT_MENU_SCREEN_ENTITY:
                self.assertNotEqual(pointers[0], 0)
                self.assertEqual(pointers[1:], [0] * 31)
            else:
                self.assertEqual(pointers, [0] * 32)
        screen_pc = editor.get_script_pointer(menu.CONTENT_MENU_SCREEN_ENTITY, 0)
        screen_init = mass_driver._facility_video_screen_init_body()
        self.assertEqual(
            editor.bytecode[screen_pc : screen_pc + len(screen_init)],
            screen_init,
        )
        self.assertNotIn(mass_driver._change_field(377, 0), editor.bytecode)
        self.assertNotIn(mass_driver._change_field(384, 0), editor.bytecode)

    def test_menu_input_skips_mahanon_and_dispatches_only_three_routes(self) -> None:
        bytecode = self.menu_editor.bytecode
        self.assertEqual(bytecode.count(b"\xFE\xE0\x01"), 1)
        self.assertEqual(bytecode.count(b"\xFE\xE0\x00"), 3)
        self.assertEqual(
            bytecode.count(
                mass_driver._set_variable_s16(
                    menu.CONTENT_MENU_SELECTION_VARIABLE,
                    menu.MAHANON_SELECTION,
                )
            ),
            0,
        )
        for selection in menu.CONTENT_MENU_SELECTION_RING:
            self.assertIn(
                mass_driver._set_variable_s16(
                    menu.CONTENT_MENU_SELECTION_VARIABLE,
                    selection,
                ),
                bytecode,
            )
        self.assertIn(
            b"\x74" + mass_driver._immediate(mass_driver.TITLE_MENU_DISABLED_SOUND_ID),
            bytecode,
        )
        expected_routes = (
            mass_driver._change_field(mass_driver.BOOTSTRAP_FIELD, 0),
            mass_driver._change_field(
                surface.SURFACE_ENTRY_FIELD,
                surface.SURFACE_ENTRY_PARAMETER,
            ),
            mass_driver._change_field(menu.RICO_ARC_HUB_FIELD, 0),
        )
        for route in expected_routes:
            self.assertEqual(bytecode.count(route), 1)
        self.assertNotIn(mass_driver._change_field(menu.MAHANON_SELECTION, 0), bytecode)

    def test_route_launches_reset_state_party_and_vierge_exactly(self) -> None:
        bytecode = self.menu_editor.bytecode
        for variable in (
            mass_driver.ANNEX_TREASURE_VARIABLE,
            mass_driver.LIFT_STATE_VARIABLE,
            mass_driver.INTERLOCK_VARIABLE,
        ):
            self.assertIn(mass_driver._set_variable_s16(variable, 0), bytecode)
        self.assertIn(menu._party_setup(menu.MASS_DRIVER_PARTY), bytecode)
        self.assertIn(menu._party_setup(menu.SURFACE_SOYLENT_PARTY), bytecode)
        self.assertIn(menu._party_setup(menu.RICO_ARC_PARTY), bytecode)
        self.assertIn(
            bytes.fromhex("FE 42 00 80 FE 42 01 80"),
            bytecode,
        )
        self.assertIn(
            bytes.fromhex("FE A1 01 80 02 80 FE A1 06 80 09 80"),
            bytecode,
        )
        surface_handoff = mass_driver._change_field(
            surface.SURFACE_ENTRY_FIELD,
            surface.SURFACE_ENTRY_PARAMETER,
        )
        self.assertIn(
            surface.SURFACE_STATE_RESET_ROUTINE[: -len(surface_handoff)],
            bytecode,
        )

    def test_content_launch_prefix_falls_through_into_each_route(self) -> None:
        # Decode instruction boundaries: zero is a valid pause operand, but
        # at an instruction boundary it is STOP. FE53 consumes no operand.
        # The route must therefore follow FE53 in the same running script.
        prefix = menu._launch_prefix()
        bytecode = self.menu_editor.bytecode
        for route in (
            menu._mass_driver_route_body(),
            menu._surface_soylent_route_body(),
            menu._rico_arc_route_body(),
        ):
            launch = prefix + route
            self.assertEqual(bytecode.count(launch), 1)
            pc = 0
            while pc < len(prefix):
                opcode = launch[pc]
                self.assertNotEqual(opcode, 0, "STOP makes content route unreachable")
                if opcode == 0xFE:
                    extended = launch[pc + 1]
                    self.assertIn(extended, (0xE0, 0x53))
                    pc += 3 if extended == 0xE0 else 2
                else:
                    self.assertIn(opcode, (0x74, 0xB4, 0x26, 0x25))
                    pc += 2 if opcode == 0x25 else 3
            self.assertEqual(pc, len(prefix))
            self.assertEqual(launch[pc:], route)


class ContentMenuTitlePatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = RETAIL_TITLE_FIELD.read_bytes()
        cls.result = menu.patch_title_field_for_content_menu(cls.source)
        cls.source_field = parse_field(cls.source)
        cls.result_field = parse_field(cls.result)
        cls.source_editor = AtelScript(
            cls.source_field.parts[mass_driver.SCRIPT_INDEX].data
        )
        cls.result_editor = AtelScript(
            cls.result_field.parts[mass_driver.SCRIPT_INDEX].data
        )

    def test_only_new_game_fallthrough_routes_to_field_63(self) -> None:
        before = self.source_editor.bytecode
        after = self.result_editor.bytecode
        branch_pc = mass_driver.TITLE_MENU_FIELD_RESULT_BRANCH_PC
        fallthrough_pc = mass_driver.TITLE_MENU_FIELD_MASS_DRIVER_FALLTHROUGH_PC
        self.assertEqual(
            after[
                branch_pc : branch_pc + len(mass_driver.TITLE_MENU_FIELD_RESULT_BRANCH)
            ],
            mass_driver.TITLE_MENU_FIELD_RESULT_BRANCH,
        )
        self.assertEqual(after[:fallthrough_pc], before[:fallthrough_pc])
        self.assertEqual(after[fallthrough_pc + 8 : len(before)], before[fallthrough_pc + 8 :])
        self.assertEqual(after[fallthrough_pc], 0x01)
        route_pc = struct.unpack_from("<H", after, fallthrough_pc + 1)[0]
        route = mass_driver._change_field(menu.CONTENT_MENU_FIELD, 0) + b"\x5B"
        self.assertEqual(after[route_pc : route_pc + len(route)], route)
        self.assertEqual(after[fallthrough_pc + 3 : fallthrough_pc + 8], bytes(5))

    def test_title_patch_preserves_every_non_script_component(self) -> None:
        self.assertEqual(len(self.result), 4_348)
        self.assertEqual(
            hashlib.sha256(self.result).hexdigest(),
            "4a8d6afb7c175a5118dcdf5cbc2549d2a94a5f4084dd64954ee9c54c5cd71f77",
        )
        self.assertEqual(
            self.result_field.header[0x18C:],
            self.source_field.header[0x18C:],
        )
        for index, (before, after) in enumerate(
            zip(self.source_field.parts, self.result_field.parts, strict=True)
        ):
            if index == mass_driver.SCRIPT_INDEX:
                self.assertNotEqual(before.data, after.data)
            else:
                self.assertEqual(before.data, after.data)

    def test_title_patch_rejects_an_already_modified_source(self) -> None:
        with self.assertRaises(menu.ContentMenuFieldError):
            menu.patch_title_field_for_content_menu(self.result)


if __name__ == "__main__":
    unittest.main()
