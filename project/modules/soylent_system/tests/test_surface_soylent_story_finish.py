from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import unittest

import modules.soylent_system.base as base
import modules.soylent_system.build as campaign
from modules.soylent_system.tests.test_build_surface_soylent_campaign import _run_appointment_vm
from modules.soylent_system.tools import surface_soylent_story_finish as story
from shared.paths import PROJECT_ROOT
from shared.tools.xgdialog import DialogueBlockSpec, encode_dialogue, parse_dialogue
from shared.tools.xgencounter import EncounterTable
from shared.tools.xgscript import AtelScript


class MeldAndBossExecutionTests(unittest.TestCase):
    def meld(self, state=0x008F, stop_pcs=()):
        body = story.meld_action(0, 10, 11)
        return _run_appointment_vm(body, start_pc=0, stop_pcs=stop_pcs,
                                   variables={campaign.STATE_OPERAND: state})

    def boss_script(self):
        native_pc = 0x400
        confirmation = story.boss_confirmation_action(0, native_pc, 10, 11)
        native = campaign._boss_action(pre_dialogue_id=39, post_dialogue_id=40,
                                       already_dialogue_id=41, routine_pc=native_pc)
        self.assertLess(len(confirmation), native_pc)
        return confirmation.ljust(native_pc, b"\x00") + native

    def boss(self, state=0x008F, choice=None, stop_pcs=()):
        return _run_appointment_vm(
            self.boss_script(), start_pc=0, stop_pcs=stop_pcs,
            variables={campaign.STATE_OPERAND: state},
            menu_choices=None if choice is None else {10: choice},
        )

    def test_first_meld_receipt_precedes_persistent_witness_commit(self):
        body = story.meld_action(0, 10, 11)
        reveal_wait_pc = body.index(b"\xF5\x03\x00\x01\x9C") + 4
        commit_pc = body.index(campaign._set_bit(campaign.STATE_OPERAND, campaign.MELD_BIT_INDEX))
        for stop_pc in (reveal_wait_pc, commit_pc):
            result = self.meld(stop_pcs=(stop_pc,))
            self.assertEqual(result["dialogue_ids"], (3,))
            self.assertEqual(result["variables"][campaign.STATE_OPERAND], 0x008F)
            self.assertFalse(result["bit_writes"])
            self.assertEqual(result["control_restores"], 0)
        completed = self.meld()
        self.assertEqual(completed["dialogue_ids"], (3,))
        self.assertEqual(completed["variables"][campaign.STATE_OPERAND], 0x008F | campaign.MELD_BIT_MASK)
        self.assertEqual(len(completed["bit_writes"]), 1)
        self.assertEqual(completed["control_restores"], 1)

    def test_meld_repeat_and_secured_aftermath_do_not_rewrite_progress(self):
        for extra, expected in (
            (campaign.MELD_BIT_MASK, 10),
            (campaign.SECURED_BIT_MASK, 11),
            (campaign.SECURED_BIT_MASK | campaign.MELD_BIT_MASK, 11),
        ):
            state = 0x008F | extra
            result = self.meld(state)
            self.assertEqual(result["dialogue_ids"], (expected,))
            self.assertEqual(result["variables"][campaign.STATE_OPERAND], state)
            self.assertFalse(result["bit_writes"])
            self.assertFalse(result["bit_clears"])
            self.assertEqual(result["control_restores"], 1)

    def test_boss_decline_cancel_and_unknown_choice_never_start_battle(self):
        for choice in (2, 0, 255):
            result = self.boss(choice=choice)
            self.assertEqual(result["dialogue_ids"], (10, 11))
            self.assertEqual(result["variables"][campaign.STATE_OPERAND], 0x008F)
            self.assertFalse(result["battle_ids"])
            self.assertFalse(result["sound_ids"])
            self.assertFalse(result["bit_writes"])
            self.assertFalse(result["bit_clears"])
            self.assertEqual(result["control_restores"], 1)

    def test_confirmed_boss_runs_native_battle_then_epilogue_once(self):
        result = self.boss(choice=1)
        self.assertEqual(result["dialogue_ids"], (10, 39, 40))
        self.assertEqual(result["battle_ids"], (9,))
        self.assertEqual(result["battle_syncs"], 1)
        self.assertEqual(result["variables"][campaign.STATE_OPERAND], 0x008F | campaign.SECURED_BIT_MASK)
        self.assertEqual(result["sound_ids"], (campaign.PROGRESSION_CONFIRM_SOUND_ID,))
        self.assertEqual(result["control_restores"], 1)

    def test_completion_cannot_precede_native_battle_return_and_epilogue(self):
        script = self.boss_script()
        battle_pc = script.index(bytes.fromhex("71 09 80 FE 7F"))
        sync_pc = battle_pc + 3
        epilogue_wait_pc = script.index(b"\xF5\x28\x00\x01\x9C") + 4
        for stop_pc in (battle_pc, sync_pc):
            result = self.boss(choice=1, stop_pcs=(stop_pc,))
            self.assertEqual(result["variables"][campaign.STATE_OPERAND], 0x008F)
            self.assertFalse(result["bit_writes"])
        result = self.boss(choice=1, stop_pcs=(epilogue_wait_pc,))
        self.assertEqual(result["variables"][campaign.STATE_OPERAND], 0x008F | campaign.FINALE_EPILOGUE_PENDING_BIT_MASK)
        self.assertFalse(result["variables"][campaign.STATE_OPERAND] & campaign.SECURED_BIT_MASK)

    def test_pending_victory_resumes_epilogue_without_prompt_or_battle(self):
        state = 0x008F | campaign.FINALE_EPILOGUE_PENDING_BIT_MASK
        result = self.boss(state)
        self.assertEqual(result["dialogue_ids"], (40,))
        self.assertFalse(result["battle_ids"])
        self.assertEqual(result["battle_syncs"], 0)
        self.assertEqual(result["variables"][campaign.STATE_OPERAND], 0x008F | campaign.SECURED_BIT_MASK)
        self.assertEqual(result["control_restores"], 1)

    def test_secured_and_torn_secured_pending_states_never_offer_repeat_fight(self):
        for pending in (0, campaign.FINALE_EPILOGUE_PENDING_BIT_MASK):
            state = 0x008F | campaign.SECURED_BIT_MASK | pending
            result = self.boss(state)
            self.assertEqual(result["dialogue_ids"], (41,))
            self.assertFalse(result["battle_ids"])
            self.assertFalse(result["sound_ids"])
            self.assertFalse(result["bit_writes"])
            self.assertEqual(result["variables"][campaign.STATE_OPERAND], 0x008F | campaign.SECURED_BIT_MASK)
            self.assertEqual(result["control_restores"], 1)


class StoryFinishFieldIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(PROJECT_ROOT) / "output/Xenogears_PW_CD2_mass_driver_standalone_v166.bin"
        if not source.is_file():
            raise unittest.SkipTest("pinned Soylent source disc is unavailable")
        sources = base.load_source_fields(source)
        cls.foundations = {}
        cls.finished = {}
        specs = [spec for spec in base.NATIVE_WING_SCENES if spec.identity.scene == 625]
        specs.append(base.FINAL_GENERATION_SCENE)
        for spec in specs:
            scene = spec.identity.scene
            item = base.prepare_native_interactions(base.prepare_playable_field(spec, *sources[scene]))
            item = campaign._prepare_meld(item) if scene == 625 else campaign._prepare_generation(item)
            item = campaign._prepare_campaign_dialogue_layout_field(campaign._prepare_door_clearance(item))
            cls.foundations[scene] = item
            cls.finished[scene] = story.prepare_story_finish(item)

    def test_only_expected_action_changes_preserving_native_scripts_and_assets(self):
        for scene, before in self.foundations.items():
            after = self.finished[scene]
            self.assertEqual(before.header[0x190:], after.header[0x190:])
            self.assertEqual(before.graphics, after.graphics)
            self.assertEqual(before.spec.edges, after.spec.edges)
            for index, component in enumerate(before.components):
                if index not in (campaign.SCRIPT_INDEX, 7):
                    self.assertEqual(component, after.components[index])
            old = AtelScript(before.components[campaign.SCRIPT_INDEX])
            new = AtelScript(after.components[campaign.SCRIPT_INDEX])
            self.assertEqual(old.entity_count, new.entity_count)
            self.assertEqual(old.bytecode, new.bytecode[:len(old.bytecode)])
            entity = story.MELD_ENTITY if scene == 625 else story.BOSS_ENTITY
            for candidate in range(old.entity_count):
                for slot in range(32):
                    if (candidate, slot) != (entity, 2):
                        self.assertEqual(old.get_script_pointer(candidate, slot), new.get_script_pointer(candidate, slot))

    def test_native_sufal_formation_disables_escape_and_retains_assets(self):
        # Bit 0x80 of formation byte1 is the same checked no-Escape flag used
        # by the clinic and Mass Driver fixed battle builders.
        encounters = EncounterTable(self.finished[622].components[6])
        formation = encounters.formation(9)
        self.assertEqual(formation, bytes.fromhex(
            "2c c0 34 00 00 00 00 00 84 03 03 03 03 ff ff ff "
            "00 00 00 00 00 ff ff ff 00 00 00 00 00 ff ff ff"
        ))
        self.assertTrue(formation[1] & 0x80)
        self.assertEqual(encounters.get_weight(9), 0)
        self.assertEqual(self.finished[622].components[6], self.foundations[622].components[6])

    def test_real_meld_then_boss_controls_produce_single_completion(self):
        state = {campaign.STATE_OPERAND: 0x008F}
        meld = self.finished[625]
        editor = AtelScript(meld.components[campaign.SCRIPT_INDEX])
        result = _run_appointment_vm(editor.bytecode,
            start_pc=editor.get_script_pointer(story.MELD_ENTITY, 2), variables=state)
        self.assertEqual(result["dialogue_ids"], (3,))
        state = result["variables"]
        boss = self.finished[622]
        editor = AtelScript(boss.components[campaign.SCRIPT_INDEX])
        pc = editor.get_script_pointer(story.BOSS_ENTITY, 2)
        metadata = story.story_metadata(boss)
        result = _run_appointment_vm(editor.bytecode, start_pc=pc,
            variables=state, menu_choices={metadata["added_dialogue_ids"][0]: 1})
        self.assertEqual(result["battle_ids"], (9,))
        self.assertEqual(result["variables"][campaign.STATE_OPERAND], 0x008F | campaign.MELD_BIT_MASK | campaign.SECURED_BIT_MASK)
        revisited = _run_appointment_vm(editor.bytecode, start_pc=pc, variables=result["variables"])
        self.assertEqual(revisited["dialogue_ids"], (41,))
        self.assertFalse(revisited["battle_ids"])

    def test_added_dialogue_fits_native_grid_and_two_choice_menu(self):
        for scene, item in self.finished.items():
            blocks = parse_dialogue(item.components[7]).blocks
            for block in blocks[-2:]:
                measurable = parse_dialogue(encode_dialogue((DialogueBlockSpec(
                    0, block.width, block.height, block.text.replace("<Opcode:01:FF>", ""),
                ),))).blocks[0]
                with self.subTest(scene=scene, block=block.block_id):
                    self.assertEqual(campaign._campaign_dialogue_layout_issues(measurable), ())
        block = parse_dialogue(self.finished[622].components[7]).blocks[-2]
        self.assertEqual(block.height, 3)
        self.assertEqual(block.text.splitlines(), [
            "GENERATION CHAMBER", "<Opcode:01:FF>    Confront the Sufal Mass", "    Not yet<Close>",
        ])
        editor = AtelScript(self.finished[622].components[campaign.SCRIPT_INDEX])
        pc = editor.get_script_pointer(story.BOSS_ENTITY, 2)
        menu = base.mass_driver._choice_dialog(block.block_id) + b"\xA9\x12\x9C"
        self.assertIn(menu, editor.bytecode[pc:])

    def test_changed_foundations_and_duplicate_install_fail_closed(self):
        for scene, item in self.foundations.items():
            entity = story.MELD_ENTITY if scene == 625 else story.BOSS_ENTITY
            editor = AtelScript(item.components[campaign.SCRIPT_INDEX])
            editor.append_and_repoint(entity, 2, b"\x00")
            components = list(item.components)
            components[campaign.SCRIPT_INDEX] = editor.to_bytes()
            with self.assertRaises(campaign.SurfaceCampaignBuildError):
                story.prepare_story_finish(replace(item, components=tuple(components)))
            with self.assertRaises(campaign.SurfaceCampaignBuildError):
                story.prepare_story_finish(self.finished[scene])


if __name__ == "__main__":
    unittest.main()
