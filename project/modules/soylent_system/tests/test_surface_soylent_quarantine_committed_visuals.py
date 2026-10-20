from __future__ import annotations

from dataclasses import replace
import hashlib
import struct
import unittest

from modules.soylent_system import base, build as campaign
from modules.soylent_system.tests.disc_fixtures import source_disc_path
from modules.soylent_system.tools import surface_soylent_quarantine_feedback as feedback
from modules.soylent_system.tools import surface_soylent_quarantine_committed_visuals as visuals
from shared.tools.xgfield import SIZE_TABLE_OFFSET, STREAM_TABLE_OFFSET
from shared.tools.xgscript import AtelScript


def _render_scale(bytecode: bytes, pc: int, variables: dict[int, int]):
    """Evaluate only the read-only scale tail after checked native creation.

    The actor's native default scale is 0x1000. Refuse any instruction capable
    of changing variables, actor controls, or field state in the appended tail.
    """
    initial = dict(variables)
    scale = (0x1000,) * 3
    for _ in range(12):
        opcode = bytecode[pc]
        if opcode == 0:
            return scale, initial
        if opcode == 1:
            pc = struct.unpack_from("<H", bytecode, pc + 1)[0]
        elif opcode == 2:
            operand, mask, mode, target = struct.unpack_from("<HHBH", bytecode, pc + 1)
            if mode != 0x46:
                raise AssertionError(f"Unexpected conditional mode {mode}")
            pc = pc + 8 if variables.get(operand, 0) & mask else target
        elif bytecode[pc:pc + 2] == b"\xFE\x08":
            raw = struct.unpack_from("<HHH", bytecode, pc + 2)
            if not all(value & 0x8000 for value in raw):
                raise AssertionError("Ring scale must use literal values")
            scale = tuple(value & 0x7FFF for value in raw)
            pc += 8
        else:
            raise AssertionError(f"Unexpected ring-tail opcode {opcode:02X} at {pc:04X}")
    raise AssertionError("Ring initializer did not stop")


class QuarantineCommittedVisualsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = source_disc_path("mass_driver_base")
        if not source.is_file():
            raise unittest.SkipTest("Configured Soylent source is unavailable")
        sources = base.load_source_fields(source)
        spec = next(spec for spec in base.PLAYABLE_SCENES if spec.identity.scene == 620)
        item = base.prepare_native_interactions(base.prepare_quarantine_puzzle(
            base.prepare_playable_field(spec, *sources[620])))
        item = campaign._prepare_quarantine_lore(item)
        item = campaign._prepare_quarantine_completion(campaign._prepare_door_clearance(item))
        item = campaign._prepare_campaign_dialogue_layout_field(item)
        cls.before = feedback.prepare_quarantine_feedback(item)
        cls.after = visuals.prepare_committed_visuals(cls.before)
        cls.old = AtelScript(cls.before.components[campaign.SCRIPT_INDEX])
        cls.new = AtelScript(cls.after.components[campaign.SCRIPT_INDEX])

    def render(self, entity, state, selection):
        pc = self.new.get_script_pointer(entity, 0)
        values = {campaign.STATE_OPERAND: state, campaign.LOCAL_PUZZLE_OPERAND: selection}
        result, unchanged = _render_scale(self.new.bytecode, pc + visuals.NATIVE_SETUP_SIZE, values)
        self.assertEqual(unchanged, values)
        return result

    def test_unsolved_initializers_preserve_all_sixteen_native_selections(self):
        for selection in range(16):
            for entity, bit, *_ in feedback.RELAYS:
                with self.subTest(selection=selection, entity=entity):
                    local = selection << 4
                    expected = (0x1400 if local & (1 << bit) else 0x1000,) * 3
                    self.assertEqual(self.render(entity, 0x028F, local), expected)
                    native_pc = self.old.get_script_pointer(entity, 0)
                    original, _ = _render_scale(self.old.bytecode, native_pc + visuals.NATIVE_SETUP_SIZE,
                                               {campaign.LOCAL_PUZZLE_OPERAND: local})
                    self.assertEqual(self.render(entity, 0x028F, local), original)

    def test_accepted_solution_survives_local_reset_and_ignores_stale_local_values(self):
        for selection in range(16):
            for entity, *_ in feedback.RELAYS:
                with self.subTest(selection=selection, entity=entity):
                    expected = (0x1000 if entity == 20 else 0x1400,) * 3
                    self.assertEqual(self.render(entity, 0x038F, selection << 4), expected)
                    self.assertEqual(self.render(entity, 0x838F, selection << 4), expected)

    def test_native_creation_and_every_other_entry_and_resource_are_unchanged(self):
        self.assertEqual(self.old.bytecode, self.new.bytecode[:self.old.bytecode_size])
        self.assertEqual(self.old.entity_count, self.new.entity_count)
        changed = {(entity, 0) for entity, *_ in feedback.RELAYS}
        for entity in range(self.old.entity_count):
            for slot in range(32):
                old_pc, new_pc = self.old.get_script_pointer(entity, slot), self.new.get_script_pointer(entity, slot)
                if (entity, slot) in changed:
                    self.assertNotEqual(old_pc, new_pc)
                    self.assertEqual(self.old.bytecode[old_pc:old_pc + visuals.NATIVE_SETUP_SIZE],
                                     self.new.bytecode[new_pc:new_pc + visuals.NATIVE_SETUP_SIZE])
                    self.assertEqual(self.new.bytecode[new_pc], 0xBC)
                else:
                    self.assertEqual(old_pc, new_pc)
        # Repacking updates the script length and following stream offsets;
        # all actor records and other header data must remain byte-identical.
        header = bytearray(self.after.header)
        script_size_offset = SIZE_TABLE_OFFSET + 4 * campaign.SCRIPT_INDEX
        header[script_size_offset:script_size_offset + 4] = self.before.header[script_size_offset:script_size_offset + 4]
        for index in range(campaign.SCRIPT_INDEX + 1, len(self.before.components)):
            offset = STREAM_TABLE_OFFSET + 4 * index
            header[offset:offset + 4] = self.before.header[offset:offset + 4]
        self.assertEqual(self.before.header, header)
        self.assertEqual(self.before.graphics, self.after.graphics)
        for index, component in enumerate(self.before.components):
            if index != campaign.SCRIPT_INDEX:
                self.assertEqual(component, self.after.components[index])

    def test_exact_foundation_and_single_application_are_required(self):
        script = self.before.components[campaign.SCRIPT_INDEX]
        self.assertEqual((len(script), hashlib.sha256(script).hexdigest()), visuals.INPUT_SCRIPT_IDENTITY)
        with self.assertRaises(campaign.SurfaceCampaignBuildError):
            visuals.prepare_committed_visuals(self.after)
        changed = list(self.before.components)
        changed[campaign.SCRIPT_INDEX] = script[:-1]
        with self.assertRaises(campaign.SurfaceCampaignBuildError):
            visuals.prepare_committed_visuals(replace(self.before, components=tuple(changed)))
        other = replace(self.before, spec=replace(self.before.spec,
                        identity=replace(self.before.spec.identity, scene=623)))
        self.assertIs(visuals.prepare_committed_visuals(other), other)


if __name__ == "__main__":
    unittest.main()
