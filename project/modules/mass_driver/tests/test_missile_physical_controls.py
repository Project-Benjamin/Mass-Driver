"""Regress the actual physical face-button words observed in native play.

The V175 script used Square's configured word for actions labeled Triangle.
These execute the emitted control branches with independently observed words,
and retain the old script as a failing behavioral and byte-preservation check.
"""
from __future__ import annotations

import struct
import unittest

from shared.paths import PROJECT_ROOT
from shared.tools.xgscript import AtelScript
from modules.mass_driver import build as dungeon


def _control_path(code, pc, held, stops):
    """Execute only the checked native pad/jump/write/yield branch fragment."""
    writes = {}
    visited = []
    for _ in range(80):
        if pc in stops:
            return pc, writes, visited
        visited.append(pc)
        opcode = code[pc]
        if opcode == 0x31:
            mask, target = struct.unpack_from("<HH", code, pc + 1)
            pc = pc + 5 if held & mask else target
        elif opcode == 0x01:
            pc = struct.unpack_from("<H", code, pc + 1)[0]
        elif opcode == 0x35:
            variable, value, control = struct.unpack_from("<HHB", code, pc + 1)
            assert control == 0x40
            writes[variable] = value
            pc += 6
        elif opcode == 0x26:
            assert code[pc + 2] == 0x80
            pc += 3
        elif opcode == 0xC6:
            pc += 1
        else:
            raise AssertionError(f"Unexpected control instruction {opcode:02X} at {pc:04X}")
    raise AssertionError("Control fragment did not reach its checked boundary")


class MissilePhysicalControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = next(s for s in dungeon.CLONES if s.target_field == 376)
        cls.prepared = dungeon._prepare_clone(
            spec, PROJECT_ROOT / "work", PROJECT_ROOT / "modules/mass_driver/content"
        )
        cls.data = cls.prepared.components[dungeon.SCRIPT_INDEX]
        cls.script = AtelScript(cls.data)
        cls.frozen = PROJECT_ROOT / "builds/mass_driver/mass-driver-v175-release-candidate-20261019/stage/clones/field_376"
        cls.previous_data = (cls.frozen / "05_scripts.bin").read_bytes()
        cls.previous = AtelScript(cls.previous_data)

    def test_physical_triangle_exits_title_while_square_does_not(self):
        # Independent Sony-firmware native captures: callback Triangle9 -> 80;
        # callback Square1 -> 10. Hardware Triangle was simultaneously EFFF.
        stops = {0xB30E, 0x9D7A}
        self.assertEqual(_control_path(self.script.bytecode, 0x9D72, 0x80, stops)[0], 0xB30E)
        self.assertEqual(_control_path(self.script.bytecode, 0x9D72, 0x10, stops)[0], 0x9D7A)
        self.assertEqual(_control_path(self.previous.bytecode, 0x9D72, 0x80, stops)[0], 0x9D7A)
        self.assertEqual(_control_path(self.previous.bytecode, 0x9D72, 0x10, stops)[0], 0xB30E)

    def test_physical_triangle_requests_pause_without_firing_or_stopping_workers(self):
        stops = {0xB034, 0x9DCB}
        pc, writes, _ = _control_path(self.script.bytecode, 0x9DB4, 0x80, stops)
        self.assertEqual((pc, writes), (0xB034, {dungeon.MISSILE_MODE_REQUEST_VARIABLE: 1}))
        pc, writes, _ = _control_path(self.script.bytecode, 0x9DB4, 0x10, stops)
        self.assertEqual((pc, writes), (0x9DCB, {}))
        self.assertEqual(_control_path(self.previous.bytecode, 0x9DB4, 0x80, stops)[0], 0x9DCB)

    def test_triangle_release_gate_covers_both_title_and_pause(self):
        for start, wait, released in ((0x9D63, 0x9D68, 0x9D6E), (0xB2A6, 0xB2AB, 0xB2B1)):
            with self.subTest(start=hex(start)):
                stops = {wait, released}
                self.assertEqual(_control_path(self.script.bytecode, start, 0x80, stops)[0], wait)
                self.assertEqual(_control_path(self.script.bytecode, start, 0x10, stops)[0], released)
                self.assertEqual(_control_path(self.script.bytecode, start, 0, stops)[0], released)
        # The title also waits for the unchanged physical Cross confirmation.
        self.assertEqual(_control_path(self.script.bytecode, 0x9D63, 0x20, {0x9D68, 0x9D6E})[0], 0x9D68)

    def test_paused_cross_resume_and_circle_exit_branches_are_preserved(self):
        stops = {0xB2F9, 0xB2C8, 0xB2B1}
        self.assertEqual(_control_path(self.script.bytecode, 0xB2B5, 0x40, stops)[:2],
                         (0xB2F9, {dungeon.MISSILE_MODE_REQUEST_VARIABLE: 0}))
        self.assertEqual(_control_path(self.script.bytecode, 0xB2B5, 0x20, stops)[:2], (0xB2C8, {}))
        self.assertEqual(_control_path(self.script.bytecode, 0xB2B5, 0, stops)[:2], (0xB2B1, {}))
        self.assertEqual(self.script.bytecode[0xB2B1:0xB30E], self.previous.bytecode[0xB2B1:0xB30E])

    def test_only_four_pad_operand_bytes_change_from_v175(self):
        expected = bytearray(self.previous_data)
        for pc, old, new in ((0x9D64, 0x30, 0xA0), (0x9D73, 0x10, 0x80),
                             (0x9DB5, 0x10, 0x80), (0xB2A7, 0x10, 0x80)):
            offset = self.previous.bytecode_offset + pc
            self.assertEqual(expected[offset], old)
            expected[offset] = new
        self.assertEqual(self.data, bytes(expected))
        self.assertEqual(self.prepared.header, (self.frozen / "header.bin").read_bytes())
        for index, name in enumerate(("images", "walkmesh", "models", "actors", "sprites", "scripts", "encounters", "dialogue", "triggers")):
            if index != dungeon.SCRIPT_INDEX:
                self.assertEqual(self.prepared.components[index], (self.frozen / f"{index:02}_{name}.bin").read_bytes())


if __name__ == "__main__":
    unittest.main()
