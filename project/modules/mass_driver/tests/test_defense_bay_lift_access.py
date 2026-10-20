"""Regression for the native straight-approach stop before the north lift."""
from __future__ import annotations

import struct
import unittest

from shared.paths import PROJECT_ROOT
from shared.tools.xgscript import AtelScript
from modules.mass_driver import build as dungeon


def _dispatch_at_position(body, base, authorized, position):
    """Interpret the poll's native comparison instructions and 16.16 position.

    This executes emitted bytecode. It does not duplicate the threshold test
    using builder constants, which would miss a wrongly encoded operand.
    """
    variables = {dungeon.INTERLOCK_VARIABLE: dungeon.LAUNCH_AUTHORIZATION_MASK if authorized else 0}
    pc = base
    for _ in range(12):
        offset = pc - base
        opcode = body[offset]
        if opcode == 0x02:
            variable, immediate, control, target = struct.unpack_from("<HHBH", body, offset + 1)
            value = variables[variable]
            if control == 0x46:
                passed = bool(value & immediate)
            elif control == 0x44:
                signed = immediate if immediate < 0x8000 else immediate - 0x10000
                passed = value >= signed
            elif control == 0x43:
                passed = value < immediate
            else:
                raise AssertionError(f"Unexpected comparison {control:02X}")
            pc = pc + 8 if passed else target
        elif opcode == 0x2D:
            assert body[offset + 1] == 0xFF
            x_variable, z_variable, y_variable = struct.unpack_from("<HHH", body, offset + 2)
            x, y, z = (int(value * 65536) >> 16 for value in position)
            variables.update({x_variable: x, z_variable: z, y_variable: y})
            pc += 8
        elif opcode == 0x09:
            return body[offset + 1], body[offset + 2]
        elif opcode == 0x26:
            return None  # Native yield/retry, without dispatching the lift.
        else:
            raise AssertionError(f"Unexpected poll opcode {opcode:02X}")
    raise AssertionError("Lift poll did not dispatch or yield")


class DefenseBayLiftAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = next(spec for spec in dungeon.CLONES if spec.target_field == 376)
        cls.prepared = dungeon._prepare_clone(cls.spec, PROJECT_ROOT / "work", PROJECT_ROOT / "modules/mass_driver/content")
        cls.script = AtelScript(cls.prepared.components[dungeon.SCRIPT_INDEX])
        cls.lift = cls.spec.defense_bay_lift_exit
        cls.poll_pc = cls.script.get_script_pointer(0, 1)
        cls.poll = dungeon._defense_bay_lift_proximity_poll(cls.poll_pc, cls.lift)

    def test_actual_native_straight_stop_truncates_to_271_and_enters_when_authorized(self):
        captured = (3.045166, 0, 271.910645)
        self.assertEqual(int(captured[2] * 65536) >> 16, 271)
        self.assertEqual(_dispatch_at_position(self.poll, self.poll_pc, True, captured), (17, 0x22))
        self.assertIsNone(_dispatch_at_position(self.poll, self.poll_pc, False, captured))
        # The previous boundary is reproduced with its actual encoded operand;
        # it must reject the exact same captured approach.
        old = bytearray(self.poll)
        struct.pack_into("<H", old, 35, 274)
        self.assertIsNone(_dispatch_at_position(bytes(old), self.poll_pc, True, captured))

    def test_return_spawn_and_other_passages_do_not_autoactivate(self):
        cases = (
            ((0, 0, 245), False), ((0, 0, 269.99), False), ((0, 0, 270), True),
            ((-44, 0, 271), True), ((44, 0, 271), True),
            ((-45, 0, 271), False), ((45, 0, 271), False),
            ((694.87, 31, 279), False), ((-30, 0, 141), False),
        )
        for position, expected in cases:
            with self.subTest(position=position):
                self.assertEqual(_dispatch_at_position(self.poll, self.poll_pc, True, position) is not None, expected)

    def test_native_fallback_reaches_actual_stop_and_excludes_return_spawn(self):
        init = self.script.get_script_pointer(17, 0)
        self.assertEqual(init, 0x0775)
        bounding = self.script.bytecode[0x0784:0x0789]
        self.assertEqual(bounding, bytes.fromhex("18 0B 0B 64 00"))
        x_extent, z_extent = bounding[1] * 2 + 16, bounding[2] * 2 + 16
        self.assertEqual((x_extent, z_extent), (38, 38))
        self.assertLessEqual(abs(3 - 0), x_extent)
        self.assertLessEqual(abs(271 - 308), z_extent)
        self.assertGreater(abs(269 - 308), z_extent)
        self.assertGreater(abs(245 - 308), z_extent)

    def test_only_three_lift_bytes_and_reviewed_missile_fix_change_from_v173(self):
        frozen = PROJECT_ROOT / "builds/mass_driver/mass-driver-v173-release-candidate-20261019/stage/clones/field_376"
        previous = (frozen / "05_scripts.bin").read_bytes()
        old_script = AtelScript(previous)
        expected = bytearray(previous)
        for pc, before, after in ((0x0785, 0x09, 0x0B), (0x0786, 0x09, 0x0B), (0x080B, 0x12, 0x0E)):
            offset = old_script.bytecode_offset + pc
            self.assertEqual(expected[offset], before)
            expected[offset] = after
        # V176's separately tested physical-Triangle repair changes four
        # Missile input operands. Preserve this test's original V173 baseline
        # and include only those reviewed additions beside the three lift bytes.
        for pc, old, new in ((0x9D64, 0x30, 0xA0), (0x9D73, 0x10, 0x80),
                             (0x9DB5, 0x10, 0x80), (0xB2A7, 0x10, 0x80)):
            offset = old_script.bytecode_offset + pc
            self.assertEqual(expected[offset], old)
            expected[offset] = new
        self.assertEqual(self.prepared.components[dungeon.SCRIPT_INDEX], bytes(expected))
        self.assertEqual(self.prepared.header, (frozen / "header.bin").read_bytes())
        for index, name in enumerate(("images", "walkmesh", "models", "actors", "sprites", "scripts", "encounters", "dialogue", "triggers")):
            if index != dungeon.SCRIPT_INDEX:
                self.assertEqual(self.prepared.components[index], (frozen / f"{index:02}_{name}.bin").read_bytes())


if __name__ == "__main__":
    unittest.main()
