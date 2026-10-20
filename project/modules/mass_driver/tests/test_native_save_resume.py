"""Regression for route-dependent native memory-cube resume entry selection.

These execute the emitted room-initialization prefix and the native save-entry
handoff. They do not emulate the card UI or establish an actual cold load.
"""
from __future__ import annotations

import struct
import unittest

from shared.paths import PROJECT_ROOT
from shared.tools.xgscript import AtelScript
from modules.mass_driver import build as dungeon


def _initialize_resume_context(data, variables):
    """Execute the straight-line native prefix before its music branch.

    SET_VAR_FROM_S16's 0x40 control marks an immediate operand. The remaining
    reviewed instructions initialize presentation and do not write field vars.
    Unexpected bytecode fails instead of silently approximating new behavior.
    """
    script = AtelScript(data)
    code = script.bytecode
    pc = script.get_script_pointer(0, 0)
    state = dict(variables)
    for _ in range(24):
        opcode = code[pc]
        if opcode == 0x35:
            variable, value, control = struct.unpack_from("<HHB", code, pc + 1)
            assert control == 0x40
            state[variable] = value
            pc += 6
        elif opcode in (0xBC, 0x2A, 0x14):
            pc += 1
        elif opcode == 0xA0:
            pc += 7
        elif opcode == 0x86:
            assert pc == 0x0048
            return state
        else:
            raise AssertionError(f"Unexpected room initializer opcode {opcode:02X} at {pc:04X}")
    raise AssertionError("Room initialization did not reach its native music branch")


class NativeSaveResumeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = next(spec for spec in dungeon.CLONES if spec.target_field == 725)
        cls.prepared = dungeon._prepare_clone(
            cls.spec, PROJECT_ROOT / "work", PROJECT_ROOT / "modules/mass_driver/content"
        )
        cls.data = cls.prepared.components[dungeon.SCRIPT_INDEX]
        cls.script = AtelScript(cls.data)
        cls.frozen = PROJECT_ROOT / "builds/mass_driver/mass-driver-v174-release-candidate-20261019/stage/clones/field_725"
        cls.previous = (cls.frozen / "05_scripts.bin").read_bytes()

    def test_both_actual_arrival_contexts_select_the_native_save_entry(self):
        # Native captures: from 387 had 54=3/entry=0; from 726 had 54=1/entry=1.
        for incoming_resume, arrival in ((3, 0), (1, 1)):
            with self.subTest(incoming_resume=incoming_resume, arrival=arrival):
                initial = {0x54: incoming_resume, 2: arrival, 0x7D2: 0xA55A,
                           dungeon.INTERLOCK_VARIABLE: 0x5A5A}
                initialized = _initialize_resume_context(self.data, initial)
                self.assertEqual(initialized[0x54], 2)
                self.assertEqual(initialized[2], arrival)
                self.assertEqual(initialized[0x7D2], 0xA55A)
                self.assertEqual(initialized[dungeon.INTERLOCK_VARIABLE], 0x5A5A)
                # Native Continue restores byte-var 54 as the entry parameter;
                # INIT_ENTITY_PC then indexes its seven-byte entry directly.
                entry = dungeon._read_field_entry(self.data, initialized[0x54])
                self.assertEqual((entry.x, entry.z, entry.walkmesh), (41, 50, 0))

    def test_previous_initializer_reproduces_the_observed_bad_and_accidental_entries(self):
        failed = _initialize_resume_context(self.previous, {0x54: 3})
        self.assertEqual(failed[0x54], 3)
        bad = dungeon._read_field_entry(self.previous, failed[0x54])
        self.assertEqual((bad.x, bad.z, bad.walkmesh), (-24388, -32768, 30))
        accidental = _initialize_resume_context(self.previous, {0x54: 1})
        door = dungeon._read_field_entry(self.previous, accidental[0x54])
        self.assertEqual((door.x, door.z, door.walkmesh), (120, 40, 0))

    def test_remapped_local_variable_had_no_consumers_in_this_room(self):
        previous = AtelScript(self.previous).bytecode
        # The entire compiled script had one 7D2 operand, on this lone write.
        self.assertEqual(previous.count(bytes.fromhex("D2 07")), 1)
        self.assertEqual(previous[0x0042:0x0048], bytes.fromhex("35 D2 07 02 00 40"))
        self.assertNotIn(bytes.fromhex("D2 07"), self.script.bytecode)
        self.assertEqual(self.script.bytecode[0x0042:0x0048], bytes.fromhex("35 54 00 02 00 40"))

    def test_only_the_two_native_resume_operand_bytes_change_from_v174(self):
        before = AtelScript(self.previous)
        expected = bytearray(self.previous)
        for pc, old, new in ((0x0043, 0xD2, 0x54), (0x0044, 0x07, 0x00)):
            offset = before.bytecode_offset + pc
            self.assertEqual(expected[offset], old)
            expected[offset] = new
        self.assertEqual(self.data, bytes(expected))
        self.assertEqual(self.prepared.header, (self.frozen / "header.bin").read_bytes())
        for index, name in enumerate(("images", "walkmesh", "models", "actors", "sprites", "scripts", "encounters", "dialogue", "triggers")):
            if index != dungeon.SCRIPT_INDEX:
                self.assertEqual(self.prepared.components[index],
                                 (self.frozen / f"{index:02}_{name}.bin").read_bytes())
        # All three real field-entry records and the retail Save action survive.
        self.assertEqual(self.script.bytecode[:0x16], before.bytecode[:0x16])
        action = self.script.get_script_pointer(16, 2)
        self.assertEqual(self.script.bytecode[action:action + 8], bytes.fromhex("FE 99 00 FE 55 FE 87 00"))


if __name__ == "__main__":
    unittest.main()
