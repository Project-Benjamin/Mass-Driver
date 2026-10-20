"""Behavioral checks for completed visits and the west bulkhead's record menu.

These run the emitted field routines with controlled state and input. They do
not emulate rendering, asynchronous door animation, or a physical controller.
"""
from __future__ import annotations

from collections import deque
from dataclasses import replace
import hashlib
import struct
import unittest

from shared.paths import PROJECT_ROOT
from shared.tools.xgscript import AtelScript
from modules.mass_driver import build


class _RoutineProbe:
    """Strict interpreter for the small reviewed field-control instruction set."""

    def __init__(self, code, start, variables, choices=(), held=0):
        self.code = code
        self.pc = start
        self.variables = dict(variables)
        self.choices = deque(choices)
        self.held = held
        self.dialogues = []
        self.helper_calls = []
        self.sounds = []
        self.writes = []
        self.control_enabled = True
        self.waits = 0
        self.stopped = False

    def step(self):
        code, pc = self.code, self.pc
        opcode = code[pc]
        if opcode in (0x00, 0x5B):
            self.stopped = True
        elif opcode == 0x01:
            self.pc = struct.unpack_from("<H", code, pc + 1)[0]
        elif opcode == 0x02:
            variable, operand, condition, target = struct.unpack_from("<HHBH", code, pc + 1)
            value = self.variables.get(variable, 0)
            if condition == 0x40:
                take = value != operand
            elif condition == 0x41:
                take = value == operand
            elif condition == 0x46:
                take = not (value & operand)
            else:
                raise AssertionError(f"Unreviewed branch condition {condition:#x} at {pc:#x}")
            self.pc = target if take else pc + 8
        elif opcode == 0x31:
            mask, released_target = struct.unpack_from("<HH", code, pc + 1)
            self.pc = pc + 5 if self.held & mask else released_target
        elif opcode == 0x26:
            frames = struct.unpack_from("<H", code, pc + 1)[0]
            if not frames & 0x8000:
                raise AssertionError("Probe requires an immediate frame wait")
            self.waits += (frames & 0x7FFF) + 1
            self.pc += 3
        elif opcode == 0x33:
            # Clearing accumulated input does not release physically held input.
            self.pc += 1
        elif opcode == 0xF4:
            if code[pc + 1] != 1:
                raise AssertionError("Unexpected dialogue geometry operation")
            self.pc += 2
        elif opcode == 0xFE:
            operation = code[pc + 1]
            if operation in (0x53, 0x54):
                self.control_enabled = operation == 0x53
                self.pc += 2
            elif code[pc:pc + 4] == b"\xFE\x0D\xFC\x80":
                self.pc += 4
            else:
                raise AssertionError(f"Unreviewed extended operation {operation:#x} at {pc:#x}")
        elif opcode in (0xD2, 0xF5):
            self.dialogues.append(struct.unpack_from("<H", code, pc + 1)[0])
            self.pc += 4
        elif opcode == 0xA9:
            if code[pc + 1] != 0x13:
                raise AssertionError("Expected a three-choice native menu")
            if not self.choices:
                raise AssertionError("Unexpected extra menu request")
            self.variables[0x0014] = self.choices.popleft()
            self.pc += 2
        elif opcode == 0x9C:
            self.pc += 1
        elif opcode == 0x74:
            operand = struct.unpack_from("<H", code, pc + 1)[0]
            if not operand & 0x8000:
                raise AssertionError("Probe requires an immediate sound ID")
            self.sounds.append(operand & 0x7FFF)
            self.pc += 3
        elif opcode == 0x07:
            self.helper_calls.append((code[pc + 1], code[pc + 2] & 0x1F))
            self.pc += 3
        elif opcode == 0x3A:
            variable, bit = struct.unpack_from("<HH", code, pc + 1)
            if code[pc + 5] != 0x40:
                raise AssertionError("Unexpected persistent-write mode")
            self.variables[variable] = self.variables.get(variable, 0) | (1 << bit)
            self.writes.append((variable, bit))
            self.pc += 6
        else:
            # This also rejects accidental movement, field changes, battles,
            # camera work, inventory updates, or extra story-state mutations.
            raise AssertionError(f"Unreviewed operation {opcode:#x} at {pc:#x}")

    def advance(self, steps=1000):
        for _ in range(steps):
            if self.stopped:
                break
            self.step()
        return self

    def finish(self):
        self.advance()
        if not self.stopped:
            raise AssertionError("Field routine did not terminate")
        return self


class MassDriverV170EventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scripts = {}
        cls.specs = {}
        for field in (729, 376):
            spec = next(spec for spec in build.CLONES if spec.target_field == field)
            source = (PROJECT_ROOT / "work" / spec.bundle_directory / "05_scripts.bin").read_bytes()
            transformed, _ = build._transform_clone_script(spec, source)
            cls.scripts[field] = AtelScript(transformed)
            cls.specs[field] = spec

    def test_surface_briefing_depends_on_completion_and_lift_return(self):
        script = self.scripts[729]
        scene = self.specs[729].auto_scene
        for previous in (0, 21, 364, 728):
            for completed in (False, True):
                for other_bits in (0, 0xFFFF ^ build.LAUNCH_COMPLETED_MASK):
                    with self.subTest(previous=previous, completed=completed, other_bits=other_bits):
                        state = other_bits | (build.LAUNCH_COMPLETED_MASK if completed else 0)
                        variables = {0x0004: previous, build.INTERLOCK_VARIABLE: state,
                                     build.ANNEX_TREASURE_VARIABLE: 0xA55A}
                        run = _RoutineProbe(script.bytecode, script.get_script_pointer(scene.entity, 1), variables).finish()
                        self.assertEqual(run.dialogues, [] if completed or previous == 364 else [0])
                        self.assertEqual(run.variables, variables)
                        self.assertEqual(run.writes, [])
                        self.assertEqual(run.helper_calls, [])
                        self.assertEqual(run.sounds, [])
                        self.assertTrue(run.control_enabled)

    def test_completed_surface_visit_does_not_wait_for_held_cross(self):
        script = self.scripts[729]
        start = script.get_script_pointer(self.specs[729].auto_scene.entity, 1)
        run = _RoutineProbe(script.bytecode, start, {
            0x0004: 21, build.INTERLOCK_VARIABLE: build.LAUNCH_COMPLETED_MASK,
        }, held=build.PAD_MASK_CROSS).finish()
        self.assertEqual(run.dialogues, [])
        self.assertEqual(run.waits, 0)
        self.assertTrue(run.control_enabled)

    def test_pending_surface_visit_waits_for_physical_cross_release(self):
        script = self.scripts[729]
        start = script.get_script_pointer(self.specs[729].auto_scene.entity, 1)
        run = _RoutineProbe(script.bytecode, start, {0x0004: 21}, held=build.PAD_MASK_CROSS)
        run.advance(80)
        self.assertFalse(run.stopped)
        self.assertEqual(run.dialogues, [])
        self.assertFalse(run.control_enabled)
        run.held = 0
        run.finish()
        self.assertEqual(run.dialogues, [0])
        self.assertTrue(run.control_enabled)

    def test_omitting_completion_guard_preserves_v169_surface_script(self):
        spec = self.specs[729]
        legacy_scene = replace(spec.auto_scene, skip_if_flag_set=None)
        source = (PROJECT_ROOT / "work" / spec.bundle_directory / "05_scripts.bin").read_bytes()
        actual, _ = build._transform_clone_script(replace(spec, auto_scene=legacy_scene), source)
        # Observed from the selected V169 field script before this change.
        # Keep a digest rather than a dependency on a removable build folder.
        self.assertEqual(hashlib.sha256(actual).hexdigest(),
                         "1abffd66412881264793411b4c3f9e262b817bba93bb76767f9c26dcefc1ddb1")

    def test_west_menu_preserves_every_preexisting_script_byte_and_entrypoint(self):
        script = AtelScript(self.scripts[376].to_bytes())
        west = self.specs[376].defense_archive_west_bulkhead
        self.assertEqual(script.get_script_pointer(west.panel_entity, 2), 47_034)
        # Undo only the new e23 entrypoint and ignore the appended suffix.
        # The whole remaining blob must match the observed V169 digest, which
        # includes every prior entrypoint, worker, video routine, and camera.
        script.set_script_pointer(west.panel_entity, 2, 0xB60E)
        retained = bytearray(script.to_bytes()[:script.bytecode_offset + 47_034])
        # V174 separately fixes the north lift's native straight-approach stop.
        # V176 separately corrects four Missile controls to physical Triangle.
        # Normalize only those seven reviewed operands before comparing the
        # historical V169 body; retain its original digest and every other byte.
        for pc, current, historical in ((0x0785, 0x0B, 0x09),
                                        (0x0786, 0x0B, 0x09),
                                        (0x080B, 0x0E, 0x12),
                                        (0x9D64, 0xA0, 0x30),
                                        (0x9D73, 0x80, 0x10),
                                        (0x9DB5, 0x80, 0x10),
                                        (0xB2A7, 0x80, 0x10)):
            offset = script.bytecode_offset + pc
            self.assertEqual(retained[offset], current)
            retained[offset] = historical
        self.assertEqual(hashlib.sha256(retained).hexdigest(),
                         "1a422b92553aff8b8db0f925e98aaffc20c1749ed8ea444998c4a7910001d2ef")

    def panel_probe(self, *, defeated=False, opened=False, choices=(1,), held=0):
        script = self.scripts[376]
        west = self.specs[376].defense_archive_west_bulkhead
        # Exercise persistence preservation with unrelated progress, optional
        # content, and adjacent persistent words already populated.
        variables = {west.progression_variable: (0xAFDF | (build.BOSS_DEFEATED_MASK if defeated else 0)),
                     west.opened_variable: (0x5AFB | ((1 << west.opened_bit) if opened else 0)),
                     0x03FC: 0xA55A}
        return _RoutineProbe(script.bytecode, script.get_script_pointer(west.panel_entity, 2), variables, choices, held)

    def test_operate_reports_guardian_lock_without_reading_history(self):
        run = self.panel_probe()
        before = dict(run.variables)
        run.finish()
        self.assertEqual(run.dialogues, [39, 40])
        self.assertEqual(run.writes, [])
        self.assertEqual(run.helper_calls, [])
        self.assertEqual(run.sounds, [])
        self.assertEqual({key: run.variables[key] for key in before}, before)
        self.assertTrue(run.control_enabled)

    def test_operate_opens_once_after_guardian_and_revisits_only_report_status(self):
        west = self.specs[376].defense_archive_west_bulkhead
        first = self.panel_probe(defeated=True)
        before = dict(first.variables)
        first.finish()
        self.assertEqual(first.dialogues, [39, 41])
        self.assertEqual(first.helper_calls, [(15, 4), (16, 4)])
        self.assertEqual(first.sounds, [west.sound_id])
        self.assertEqual(first.writes, [(west.opened_variable, west.opened_bit)])
        self.assertEqual(first.variables[west.opened_variable], before[west.opened_variable] | (1 << west.opened_bit))
        self.assertEqual(first.variables[west.progression_variable], before[west.progression_variable])
        self.assertEqual(first.variables[0x03FC], before[0x03FC])
        self.assertTrue(first.control_enabled)

        second = self.panel_probe(defeated=True, opened=True).finish()
        self.assertEqual(second.dialogues, [39, 41])
        self.assertEqual(second.helper_calls, [])
        self.assertEqual(second.sounds, [])
        self.assertEqual(second.writes, [])
        self.assertTrue(second.control_enabled)

    def test_read_and_leave_never_operate_door_in_any_progress_state(self):
        for defeated, opened in ((False, False), (True, False), (True, True), (False, True)):
            for choices in ((3,), (0,), (0xFFFF,), (2, 3), (2, 2, 3)):
                with self.subTest(defeated=defeated, opened=opened, choices=choices):
                    run = self.panel_probe(defeated=defeated, opened=opened, choices=choices)
                    before = dict(run.variables)
                    run.finish()
                    self.assertEqual(run.dialogues, [39] + [item for _ in choices[:-1] for item in (19, 39)])
                    self.assertEqual(run.writes, [])
                    self.assertEqual(run.helper_calls, [])
                    self.assertEqual(run.sounds, [])
                    self.assertEqual({key: run.variables[key] for key in before}, before)
                    self.assertTrue(run.control_enabled)

    def test_read_then_operate_returns_to_menu_and_respects_boss_state(self):
        for defeated in (False, True):
            with self.subTest(defeated=defeated):
                run = self.panel_probe(defeated=defeated, choices=(2, 1)).finish()
                self.assertEqual(run.dialogues, [39, 19, 39, 41 if defeated else 40])
                self.assertEqual(run.helper_calls, [(15, 4), (16, 4)] if defeated else [])
                self.assertTrue(run.control_enabled)

    def test_west_panel_drains_held_cross_before_menu_and_after_report(self):
        run = self.panel_probe(defeated=True, choices=(2, 3), held=build.PAD_MASK_CROSS)
        run.advance(80)
        self.assertFalse(run.stopped)
        self.assertEqual(run.dialogues, [])
        self.assertEqual(list(run.choices), [2, 3])
        run.held = 0
        for _ in range(1000):
            run.step()
            if run.dialogues == [39, 19] and run.code[run.pc] == 0x9C:
                break
        else:
            self.fail("Read report branch was not reached")
        run.held = build.PAD_MASK_CROSS
        run.advance(80)
        self.assertFalse(run.stopped)
        self.assertEqual(run.dialogues, [39, 19])
        self.assertEqual(list(run.choices), [3])
        self.assertEqual(run.writes, [])
        self.assertEqual(run.helper_calls, [])
        run.held = 0
        run.finish()
        self.assertEqual(run.dialogues, [39, 19, 39])
        self.assertTrue(run.control_enabled)


if __name__ == "__main__":
    unittest.main()
