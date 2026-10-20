from __future__ import annotations

from dataclasses import replace
import unittest

from modules.soylent_system import base, build as campaign
from modules.soylent_system.tests.disc_fixtures import source_disc_path
from modules.soylent_system.tests.test_build_surface_soylent_campaign import _run_appointment_vm
from modules.soylent_system.tools import surface_soylent_finale_closure as closure
from modules.soylent_system.tools import surface_soylent_story_finish as story
from shared.tools.xgdialog import DialogueBlockSpec, encode_dialogue, parse_dialogue
from shared.tools.xgscript import AtelScript


class FinaleClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = source_disc_path("mass_driver_base")
        if not source.is_file():
            raise unittest.SkipTest("Configured Soylent donor is unavailable")
        sources = base.load_source_fields(source)
        item = base.prepare_native_interactions(base.prepare_playable_field(base.FINAL_GENERATION_SCENE, *sources[622]))
        item = campaign._prepare_generation(item)
        item = campaign._prepare_campaign_dialogue_layout_field(campaign._prepare_door_clearance(item))
        cls.before = story.prepare_story_finish(item)
        cls.after = closure.prepare_finale_closure(cls.before)
        cls.old = AtelScript(cls.before.components[5])
        cls.editor = AtelScript(cls.after.components[5])
        cls.blocks = parse_dialogue(cls.after.components[7]).blocks

    def execute(self, entity, state, stops=(), choice=1):
        return _run_appointment_vm(
            self.editor.bytecode, start_pc=self.editor.get_script_pointer(entity, 2),
            variables={campaign.STATE_OPERAND: state}, stop_pcs=stops, menu_choices={43: choice},
        )

    def test_all_survivors_keep_native_dialogue_until_the_epilogue_finishes(self):
        for entity in closure.AFTERMATH:
            native_pc = self.old.get_script_pointer(entity, 2)
            for state in (0x008F, 0x448F):
                result = self.execute(entity, state, stops=(native_pc,))
                self.assertEqual(result["reason"], "target")
                self.assertEqual(result["dialogue_ids"], ())
                self.assertEqual(result["variables"][campaign.STATE_OPERAND], state)

    def test_secured_survivors_have_repeatable_read_only_aftermath(self):
        for entity, text in closure.AFTERMATH.items():
            for state in (0x808F, 0xC48F):
                result = self.execute(entity, state)
                self.assertEqual(self.blocks[result["dialogue_ids"][0]].text, text)
                self.assertEqual(result["variables"][campaign.STATE_OPERAND], state)
                self.assertEqual(result["bit_writes"], ())
                self.assertEqual(result["bit_clears"], ())
                self.assertEqual(result["battle_ids"], ())
                self.assertEqual(result["control_suspends"], 1)
                self.assertEqual(result["control_restores"], 1)

    def test_completion_receipt_is_reachable_only_after_native_victory(self):
        denied = self.execute(29, 0x408F, choice=2)
        self.assertNotIn(40, denied["dialogue_ids"])
        self.assertEqual(denied["battle_ids"], ())
        completed = self.execute(29, 0x408F)
        self.assertEqual(completed["battle_ids"], (9,))
        self.assertEqual(completed["battle_syncs"], 1)
        self.assertEqual(completed["dialogue_ids"], (43, 39, 40))
        self.assertEqual(completed["variables"][campaign.STATE_OPERAND], 0xC08F)
        self.assertIn("SOYLENT SYSTEM COMPLETE", self.blocks[40].text)
        self.assertIn("Other Surface systems remain.", self.blocks[40].text)
        wait_pc = self.editor.bytecode.index(b"\xF5\x28\x00\x01\x9C", 0x1000) + 4
        waiting = self.execute(29, 0x408F, stops=(wait_pc,))
        self.assertEqual(waiting["variables"][campaign.STATE_OPERAND], 0x448F)
        self.assertEqual(waiting["control_restores"], 0)

    def test_interrupted_epilogue_and_completed_repeat_remain_recoverable(self):
        recovered = self.execute(29, 0x448F)
        self.assertEqual(recovered["dialogue_ids"], (40,))
        self.assertEqual(recovered["battle_ids"], ())
        self.assertEqual(recovered["variables"][campaign.STATE_OPERAND], 0xC08F)
        for state in (0xC08F, 0xC48F):
            repeated = self.execute(29, state)
            self.assertEqual(repeated["dialogue_ids"], (41,))
            self.assertEqual(repeated["battle_ids"], ())
            self.assertEqual(repeated["variables"][campaign.STATE_OPERAND], 0xC08F)
            self.assertIn("SOYLENT SYSTEM COMPLETE", self.blocks[41].text)

    def test_native_battle_save_doors_and_assets_remain_exact(self):
        self.assertEqual(self.old.bytecode, self.editor.bytecode[:self.old.bytecode_size])
        self.assertEqual(self.before.header[0x18C:], self.after.header[0x18C:])
        self.assertEqual(self.before.graphics, self.after.graphics)
        for index, component in enumerate(self.before.components):
            if index not in (5, 7):
                self.assertEqual(component, self.after.components[index])
        for entity in range(self.old.entity_count):
            for slot in range(32):
                if (entity in closure.AFTERMATH and slot == 2):
                    continue
                self.assertEqual(self.old.get_script_pointer(entity, slot), self.editor.get_script_pointer(entity, slot))
        for block in parse_dialogue(self.before.components[7]).blocks:
            if block.block_id not in (40, 41):
                self.assertEqual(block.payload, self.blocks[block.block_id].payload)
        self.assertEqual(story.story_metadata(self.after)["added_dialogue_ids"], [43, 44])

    def test_final_text_fits_native_windows_and_source_drift_is_rejected(self):
        for block in self.blocks:
            if block.block_id not in (40, 41) and block.block_id < 45:
                continue
            measured = parse_dialogue(encode_dialogue((DialogueBlockSpec(0, block.width, block.height, block.text),))).blocks[0]
            with self.subTest(dialogue=block.block_id):
                self.assertEqual(campaign._campaign_dialogue_layout_issues(measured), ())
        with self.assertRaises(campaign.SurfaceCampaignBuildError):
            closure.prepare_finale_closure(self.after)
        components = list(self.before.components)
        components[7] = components[7][:-1]
        with self.assertRaises(campaign.SurfaceCampaignBuildError):
            closure.prepare_finale_closure(replace(self.before, components=tuple(components)))


if __name__ == "__main__":
    unittest.main()
