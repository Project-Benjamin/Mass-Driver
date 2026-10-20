from __future__ import annotations

from collections import Counter
from dataclasses import replace
import struct
import unittest

from modules.soylent_system import build as campaign
from modules.soylent_system.tests.test_build_surface_soylent_campaign import _run_appointment_vm
from modules.soylent_system.tests import test_surface_soylent_completion as completion_tests
from modules.soylent_system.tools import surface_soylent_production_shutdown_visuals as visuals
from shared.tools.xgscript import AtelScript


class ProductionShutdownVisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        completion_tests.ProductionFieldIntegrationTests.setUpClass()
        cls.before = completion_tests.ProductionFieldIntegrationTests.finished[624]
        cls.after = visuals.prepare_shutdown_visuals(cls.before)
        cls.old = AtelScript(cls.before.components[campaign.SCRIPT_INDEX])
        cls.new = AtelScript(cls.after.components[campaign.SCRIPT_INDEX])

    def run_update(self, entity, persistent, local):
        """Use the campaign VM for branches, modeling only native FE1C placement."""
        pc = self.new.get_script_pointer(entity, 1)
        native_pc = self.old.get_script_pointer(entity, 1)
        position = struct.unpack_from("<3h", self.after.header, 0x190 + 16 * entity + 8)
        has_placement = self.old.bytecode[native_pc:native_pc + 2] == b"\xFE\x1C"
        targets = (native_pc, pc + 8) if has_placement else (native_pc,)
        result = _run_appointment_vm(
            self.new.bytecode, start_pc=pc, stop_pcs=targets,
            variables={campaign.STATE_OPERAND: persistent, campaign.LOCAL_PUZZLE_OPERAND: local},
        )
        if result["pc"] == pc + 8 and has_placement:
            setup = self.new.bytecode[pc + 8:pc + 17]
            self.assertEqual(setup, self.old.bytecode[native_pc:native_pc + 9])
            self.assertEqual(setup[:2], b"\xFE\x1C")
            self.assertEqual(setup[-1], 0xE0)  # all three coordinates immediate
            x, z, y = struct.unpack_from("<3h", setup, 2)
            position = x, y, z
            result = _run_appointment_vm(
                self.new.bytecode, start_pc=pc + 17, stop_pcs=(native_pc,),
                variables=result["variables"],
            )
        result["position"] = position
        return result

    def test_uncommitted_updates_resume_exact_native_motion_without_writes(self):
        for entity in visuals.ENTITIES:
            native_pc = self.old.get_script_pointer(entity, 1)
            for persistent in (0, 0x0FFF, 0x8000, 0xEFFF):
                with self.subTest(entity=entity, persistent=persistent):
                    result = self.run_update(entity, persistent, 0x39)
                    self.assertEqual(result["reason"], "target")
                    self.assertEqual(result["pc"], native_pc)
                    self.assertEqual(result["variables"][campaign.STATE_OPERAND], persistent)
                    self.assertEqual(result["variables"][campaign.LOCAL_PUZZLE_OPERAND], 0x39)
                    self.assertFalse(result["bit_writes"])
                    self.assertFalse(result["dialogue_ids"])

    def test_committed_and_secured_reentry_stop_motion_after_local_reset(self):
        for entity in visuals.ENTITIES:
            for persistent in (0x1000, 0x3000, 0x9000, 0xFFFF):
                for local in (0, 0x39, 0x3F):
                    with self.subTest(entity=entity, persistent=persistent, local=local):
                        result = self.run_update(entity, persistent, local)
                        self.assertEqual(result["reason"], "stop")
                        self.assertEqual(result["variables"][campaign.STATE_OPERAND], persistent)
                        self.assertEqual(result["variables"][campaign.LOCAL_PUZZLE_OPERAND], local)
                        self.assertFalse(result["bit_writes"])
                        self.assertFalse(result["dialogue_ids"])

    def test_only_checked_movement_updates_change_every_original_byte_is_preserved(self):
        self.assertEqual(self.new.entity_count, self.old.entity_count)
        self.assertEqual(self.new.bytecode[:self.old.bytecode_size], self.old.bytecode)
        self.assertEqual(self.new.bytecode_size - self.old.bytecode_size, 72 * 12 + 4 * 9)
        for entity in range(self.old.entity_count):
            for slot in range(32):
                old_pc = self.old.get_script_pointer(entity, slot)
                new_pc = self.new.get_script_pointer(entity, slot)
                if entity in visuals.ENTITIES and slot == 1:
                    self.assertGreaterEqual(new_pc, self.old.bytecode_size)
                    expected = visuals.shutdown_update(new_pc, old_pc)
                    self.assertEqual(self.new.bytecode[new_pc:new_pc + len(expected)], expected)
                else:
                    self.assertEqual(new_pc, old_pc, (entity, slot))

    def test_target_actors_are_visible_material_models_and_assets_stay_exact(self):
        records = [struct.unpack_from("<HhhhhhhH", self.after.header, 0x190 + 16 * entity)
                   for entity in visuals.ENTITIES]
        self.assertEqual(Counter((record[0], record[-1]) for record in records),
                         Counter({(0x0290, model): 18 for model in (8, 9, 10, 11)}))
        self.assertEqual(self.before.header[0x18C:], self.after.header[0x18C:])
        self.assertEqual(self.before.graphics, self.after.graphics)
        self.assertEqual(self.before.spec.edges, self.after.spec.edges)
        for index, component in enumerate(self.before.components):
            if index != campaign.SCRIPT_INDEX:
                self.assertEqual(self.after.components[index], component)

    def test_core_containment_is_a_noop(self):
        core = completion_tests.ProductionFieldIntegrationTests.finished[626]
        self.assertIs(visuals.prepare_shutdown_visuals(core), core)

    def test_native_placements_are_nonzero_distinct_and_keep_four_setup_overrides(self):
        expected_overrides = {
            10: (0, 0, -1675), 27: (1719, 0, -749),
            50: (1543, 0, -926), 54: (-308, 0, 926),
        }
        positions = []
        for entity in visuals.ENTITIES:
            header_position = struct.unpack_from("<3h", self.after.header, 0x190 + 16 * entity + 8)
            self.assertNotEqual(header_position, (0, 0, 0))
            result = self.run_update(entity, 0x9000, 0)
            expected = expected_overrides.get(entity, header_position)
            self.assertEqual(result["position"], expected)
            positions.append(result["position"])
        self.assertEqual(len(set(positions)), 72)

    def test_native_motion_and_actor_mapping_guards_reject_drift(self):
        components = list(self.before.components)
        script = bytearray(components[campaign.SCRIPT_INDEX])
        script[self.old.bytecode_offset + visuals.NATIVE_REGION[0]] ^= 1
        components[campaign.SCRIPT_INDEX] = bytes(script)
        with self.assertRaisesRegex(campaign.SurfaceCampaignBuildError, "native conveyor"):
            visuals.prepare_shutdown_visuals(replace(self.before, components=tuple(components)))
        header = bytearray(self.before.header)
        header[0x190 + 5 * 16 + 14] ^= 1
        with self.assertRaisesRegex(campaign.SurfaceCampaignBuildError, "actor/model"):
            visuals.prepare_shutdown_visuals(replace(self.before, header=bytes(header)))
        editor = AtelScript(self.before.components[campaign.SCRIPT_INDEX])
        editor.set_script_pointer(5, 1, editor.get_script_pointer(6, 1))
        components = list(self.before.components)
        components[campaign.SCRIPT_INDEX] = editor.to_bytes()
        with self.assertRaisesRegex(campaign.SurfaceCampaignBuildError, "entry points"):
            visuals.prepare_shutdown_visuals(replace(self.before, components=tuple(components)))
        with self.assertRaisesRegex(campaign.SurfaceCampaignBuildError, "entry points"):
            visuals.prepare_shutdown_visuals(self.after)


if __name__ == "__main__":
    unittest.main()
