"""Native title regression: Continue must never enter the New Game bootstrap."""
from __future__ import annotations

import hashlib
import struct
import unittest

from shared.paths import PROJECT_ROOT
from shared.tools.xgfield import parse_field
from shared.tools.xgscript import AtelScript
from modules.mass_driver import build as dungeon


def _title_return_path(bytecode: bytes, result: int, saved_field: int):
    """Execute the small, checked retail title-return branch, not a mock menu.

    OP02 falls through when its comparison is true; otherwise it takes its
    encoded target. Only the instructions reached by New Game and Continue
    are supported. Unexpected instructions make the regression fail.
    """
    variables = {0x46: result, 4: saved_field, 0x7D0: 0xBEEF}
    visited = []
    pc = dungeon.TITLE_MENU_FIELD_RESULT_BRANCH_PC
    for _ in range(20):
        visited.append(pc)
        op = bytecode[pc]
        if op == 0x02:
            variable, value, control, target = struct.unpack_from("<HHBH", bytecode, pc + 1)
            assert control in (0x40, 0x43)
            passed = variables[variable] == value if control == 0x40 else variables[variable] < value
            pc = pc + 8 if passed else target
        elif op == 0x01:
            pc = struct.unpack_from("<H", bytecode, pc + 1)[0]
        elif op in (0x35, 0x3E):
            variable, value, control = struct.unpack_from("<HHB", bytecode, pc + 1)
            if op == 0x35:
                assert control == 0
                variables[variable] = variables[value]
            else:
                assert control == 0x40
                variables[variable] &= value
            pc += 6
        elif bytecode[pc:pc + 2] == b"\xFE\x83":
            mode = struct.unpack_from("<H", bytecode, pc + 2)[0]
            assert mode & 0x8000
            return "saved_boot_mode", mode & 0x7FFF, variables, visited
        elif op == 0x98:
            field, parameter = struct.unpack_from("<HH", bytecode, pc + 1)
            assert field & 0x8000 and parameter & 0x8000
            return "new_game_field", field & 0x7FFF, variables, visited
        else:
            raise AssertionError(f"Unexpected title-return opcode {op:02X} at {pc:04X}")
    raise AssertionError("Title return did not reach a field handoff")


class NativeTitleContinueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = PROJECT_ROOT / "work"
        cls.overlay_source = (cls.inputs / "shop_menu_data/2599.bin").read_bytes()
        cls.menu_source = (cls.inputs / "shop_menu_data/2593.bin").read_bytes()
        cls.overlay = dungeon._prepare_title_menu_overlay(cls.inputs)
        cls.menu = dungeon._prepare_menu_shop_catalogs(cls.inputs)
        cls.field = dungeon._prepare_title_menu_field(cls.inputs)

    def test_active_overlay_changes_only_new_game_physical_disc_gate(self):
        expected = bytearray(self.overlay_source)
        expected[0x13B8:0x13BC] = bytes.fromhex("01 00 04 34")
        self.assertEqual(self.overlay.bundle, bytes(expected))
        self.assertEqual(hashlib.sha256(self.overlay.bundle).hexdigest(),
                         dungeon.NATIVE_TITLE_MENU_OVERLAY_SHA256)
        # Preserve original selection initialization, both navigation branches,
        # and native movement/confirm sound dispatch, including delay slots.
        for start, end in ((0x1AFC, 0x1B00), (0x0950, 0x0A50),
                           (0x2E2C, 0x2E34), (0x2E6C, 0x2E74)):
            with self.subTest(region=hex(start)):
                self.assertEqual(self.overlay.bundle[start:end], self.overlay_source[start:end])
        self.assertEqual(self.overlay.bundle[0x1AFC:0x1B00], bytes.fromhex("01 00 02 34"))

    def test_active_menu_retains_native_labels_and_all_non_shop_streams(self):
        _offsets, original = dungeon._menu_archive_entries(self.menu_source)
        active = dungeon._indexed_bundle_entries(self.menu.bundle)
        legacy = dungeon._indexed_bundle_entries(dungeon._patch_menu_shop_catalogs(self.menu_source))
        for index, source in enumerate(original):
            with self.subTest(entry=index):
                if index in (dungeon.ITEM_SHOP_ARCHIVE_ENTRY, dungeon.GEAR_SHOP_ARCHIVE_ENTRY):
                    self.assertEqual(active[index], legacy[index])
                else:
                    self.assertEqual(active[index], source)
        # Original font polygons and their image texture remain paired exactly.
        self.assertEqual(active[dungeon.TITLE_MENU_FONT_ARCHIVE_ENTRY], original[dungeon.TITLE_MENU_FONT_ARCHIVE_ENTRY])
        self.assertEqual(active[dungeon.TITLE_MENU_IMAGE_ARCHIVE_ENTRY], original[dungeon.TITLE_MENU_IMAGE_ARCHIVE_ENTRY])
        self.assertEqual(len(self.menu.bundle), dungeon.NATIVE_TITLE_MENU_SHARED_SIZE)
        self.assertLessEqual(len(self.menu.bundle), (len(self.menu_source) + 0x7FF) & ~0x7FF)

    def test_legacy_default_outputs_remain_compatible_with_other_profiles(self):
        self.assertEqual(hashlib.sha256(dungeon._patch_title_menu_overlay(self.overlay_source)).hexdigest(),
                         dungeon.TITLE_MENU_OVERLAY_PATCHED_SHA256)
        self.assertEqual(hashlib.sha256(dungeon._patch_menu_shop_catalogs(self.menu_source)).hexdigest(),
                         dungeon.MENU_SHOP_CATALOG_PATCHED_SHA256)

    def test_continue_return_preserves_entire_retail_saved_field_branch(self):
        donor = parse_field((self.inputs / "title_menu_audit_20260813/pwe/1586.bin").read_bytes())
        source = AtelScript(donor.parts[dungeon.SCRIPT_INDEX].data).bytecode
        active = AtelScript(self.field.components[dungeon.SCRIPT_INDEX]).bytecode
        self.assertEqual(active[0xB0:0xB8], source[0xB0:0xB8])
        self.assertEqual(active[0xE7:0x16C], source[0xE7:0x16C])
        for index, part in enumerate(donor.parts):
            if index != dungeon.SCRIPT_INDEX:
                self.assertEqual(self.field.components[index], part.data)

    def test_native_continue_uses_saved_field_and_never_bootstraps(self):
        active = AtelScript(self.field.components[dungeon.SCRIPT_INDEX]).bytecode
        for saved_field, mode in ((725, 1), (728, 1), (0x400, 3), (0x8400, 3)):
            with self.subTest(saved_field=hex(saved_field)):
                kind, actual_mode, variables, visited = _title_return_path(active, 2, saved_field)
                self.assertEqual((kind, actual_mode), ("saved_boot_mode", mode))
                self.assertEqual(variables[0x406], saved_field & 0x3FFF)
                self.assertEqual(variables[4], saved_field)
                self.assertEqual(variables[0x7D0], 0xBEEF)
                self.assertNotIn(0xB8, visited)
                self.assertNotIn(0x16C, visited)

    def test_only_new_game_return_enters_mass_driver_gateway(self):
        active = AtelScript(self.field.components[dungeon.SCRIPT_INDEX]).bytecode
        kind, destination, _variables, visited = _title_return_path(active, 0, 725)
        self.assertEqual((kind, destination), ("new_game_field", dungeon.BOOTSTRAP_FIELD))
        self.assertIn(0xB8, visited)
        self.assertIn(0x16C, visited)
        self.assertNotIn(0xE7, visited)

    def test_native_mode_still_rejects_wrong_overlay_and_menu_sources(self):
        for function, source in ((dungeon._patch_title_menu_overlay, self.overlay_source),
                                 (dungeon._patch_menu_shop_catalogs, self.menu_source)):
            changed = bytearray(source)
            changed[0x0960] ^= 1
            with self.subTest(transform=function.__name__), self.assertRaises(dungeon.DungeonBuildError):
                function(bytes(changed), native_title=True)


if __name__ == "__main__":
    unittest.main()
