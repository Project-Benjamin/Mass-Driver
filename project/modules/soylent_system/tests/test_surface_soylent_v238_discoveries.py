from __future__ import annotations

from dataclasses import replace
import unittest

from modules.soylent_system import base, build as campaign
from modules.soylent_system.tests.disc_fixtures import source_disc_path
from modules.soylent_system.tests.test_build_surface_soylent_campaign import _run_appointment_vm
from modules.soylent_system.tools import surface_soylent_campaign_exam_rooms as exam
from modules.soylent_system.tools import surface_soylent_clinical_discoveries as clinical
from modules.soylent_system.tools import surface_soylent_quarantine_feedback as quarantine
from shared.tools.xgdialog import DialogueBlockSpec, encode_dialogue, parse_dialogue
from shared.tools.xgscript import AtelScript


class V238DiscoveriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source, donor = source_disc_path("mass_driver_base"), source_disc_path("pw_disc1")
        if not source.is_file() or not donor.is_file():
            raise unittest.SkipTest("Configured Soylent donors are unavailable")
        sources = base.load_source_fields(source)
        spec = next(spec for spec in base.PLAYABLE_SCENES if spec.identity.scene == 620)
        item = base.prepare_native_interactions(base.prepare_quarantine_puzzle(base.prepare_playable_field(spec, *sources[620])))
        item = campaign._prepare_quarantine_lore(item)
        item = campaign._prepare_quarantine_completion(campaign._prepare_door_clearance(item))
        cls.q_before = campaign._prepare_campaign_dialogue_layout_field(item)
        cls.q_after = quarantine.prepare_quarantine_feedback(cls.q_before)
        cls.before = {item.identity.scene: campaign._prepare_campaign_dialogue_layout_donor(
            campaign._prepare_donor_door_clearance(item))
            for item in exam.prepare_exam_rooms_from_discs(source, donor)}
        cls.after = {scene: clinical.prepare_clinical_discoveries(item) for scene, item in cls.before.items()}

    def execute(self, prepared, entity, values, choices=None, stops=()):
        editor = AtelScript(prepared.components[5])
        return _run_appointment_vm(editor.bytecode, start_pc=editor.get_script_pointer(entity, 2),
                                   variables=values, menu_choices=choices or {}, stop_pcs=stops)

    def test_every_relay_reports_the_resulting_state_and_preserves_other_bits(self):
        blocks = parse_dialogue(self.q_after.components[7]).blocks
        for entity, bit, title, _ in quarantine.RELAYS:
            for selection in range(16):
                local = selection << 4
                result = self.execute(self.q_after, entity, {0x07D0: local, 0x03FA: 0x028F})
                expected = local ^ (1 << bit)
                self.assertEqual(result["variables"][0x07D0], expected)
                self.assertEqual(result["variables"][0x03FA], 0x028F)
                text = blocks[result["dialogue_ids"][-1]].text
                self.assertIn(title, text)
                self.assertIn("Reading: " + ("INCLUDED" if expected & (1 << bit) else "EXCLUDED"), text)
                self.assertEqual(result["control_suspends"], result["control_restores"])
                self.assertIsNone(result["field_change"])

    def test_hint_explains_selection_and_reset_and_is_only_shown_once(self):
        result = self.execute(self.q_after, 17, {0x07D0: 0, 0x03FA: 0x008F})
        blocks = parse_dialogue(self.q_after.components[7]).blocks
        self.assertEqual(blocks[result["dialogue_ids"][0]].text, quarantine.INSTRUCTIONS)
        self.assertEqual(result["variables"][0x03FA], 0x028F)
        second = self.execute(self.q_after, 18, result["variables"])
        self.assertEqual(len(second["dialogue_ids"]), 1)
        self.assertEqual(second["variables"][0x07D0], 0x30)

    def test_only_biological_readings_open_door_and_completed_relays_are_read_only(self):
        for selection in range(16):
            result = self.execute(self.q_after, 24, {0x07D0: selection << 4, 0x03FA: 0x028F})
            if selection == 7:
                self.assertEqual(result["field_change"], (565, 6))
                self.assertEqual(result["variables"][0x03FA], 0x038F)
            else:
                self.assertIsNone(result["field_change"])
                self.assertEqual(result["variables"][0x03FA], 0x028F)
        blocks = parse_dialogue(self.q_after.components[7]).blocks
        for entity, bit, _, _ in quarantine.RELAYS:
            result = self.execute(self.q_after, entity, {0x07D0: 0, 0x03FA: 0x038F})
            self.assertEqual(result["variables"][0x07D0], 0)
            self.assertEqual(result["bit_writes"], ())
            self.assertEqual(result["bit_clears"], ())
            self.assertIn("Accepted reading: " + ("EXCLUDED" if bit == 7 else "INCLUDED"), blocks[result["dialogue_ids"][0]].text)

    def test_optional_records_memoranda_and_cancel_never_write_progression(self):
        for scene in clinical.INPUT_IDENTITIES:
            item = self.after[scene]
            blocks = parse_dialogue(item.components[7]).blocks
            menu_id = clinical.discovery_metadata(item)["menu_dialogue_id"]
            for entity in exam.TERMINAL_ENTITIES:
                for selection in (0, 1, 2, 3, 4, 255):
                    result = self.execute(item, entity, {0x03FA: 0x028F, 0x021A: 1}, {menu_id: selection})
                    self.assertEqual(result["variables"][0x03FA], 0x028F)
                    self.assertEqual(result["variables"][0x021A], 1)
                    self.assertEqual(result["bit_writes"], ())
                    self.assertEqual(result["bit_clears"], ())
                    self.assertIsNone(result["field_change"])
                    self.assertEqual(result["control_restores"], 1)
                    if selection == 1:
                        self.assertEqual(result["dialogue_ids"][-1], exam.PATIENT_RECORD_DIALOGUE_IDS_BY_SCENE[scene])
                    elif selection == 2:
                        self.assertEqual(blocks[result["dialogue_ids"][-1]].text, clinical.MEMORANDA[scene])
                    elif selection == 4:
                        self.assertEqual(blocks[result["dialogue_ids"][-1]].text, clinical.ACTIVE_REPORT)
                    else:
                        self.assertEqual(result["dialogue_ids"], (menu_id,))

    def test_memoranda_remain_available_and_status_changes_only_after_secured(self):
        for scene in clinical.INPUT_IDENTITIES:
            item = self.after[scene]
            blocks = parse_dialogue(item.components[7]).blocks
            metadata = clinical.discovery_metadata(item)
            menu_id = metadata["menu_dialogue_id"]
            self.assertEqual(blocks[menu_id].height, 5)
            self.assertEqual(metadata["choices"], ["Patient record", "Staff memorandum", "Leave", "Current status"])
            editor = AtelScript(item.components[5])
            pc = editor.get_script_pointer(exam.TERMINAL_ENTITY, 2)
            expected_action = clinical.expected_terminal_action(scene)
            self.assertEqual(editor.bytecode[pc:pc + len(expected_action)], expected_action)
            for state in (0x0000, 0x4000, 0x4400, 0x8000, 0xC48F):
                for entity in exam.TERMINAL_ENTITIES:
                    for selection in (1, 2, 3, 4, 255):
                        with self.subTest(scene=scene, state=state, entity=entity, selection=selection):
                            result = self.execute(item, entity, {0x03FA: state, 0x021A: 0x0101}, {menu_id: selection})
                            self.assertEqual(result["variables"][0x03FA], state)
                            self.assertEqual(result["variables"][0x021A], 0x0101)
                            self.assertEqual(result["bit_writes"], ())
                            self.assertEqual(result["bit_clears"], ())
                            self.assertIsNone(result["field_change"])
                            self.assertEqual(result["control_suspends"], result["control_restores"])
                            if selection == 1:
                                self.assertEqual(result["dialogue_ids"][-1], exam.PATIENT_RECORD_DIALOGUE_IDS_BY_SCENE[scene])
                            elif selection == 2:
                                self.assertEqual(blocks[result["dialogue_ids"][-1]].text, clinical.MEMORANDA[scene])
                            elif selection == 4:
                                expected = clinical.HALTED_REPORT if state & campaign.SECURED_BIT_MASK else clinical.ACTIVE_REPORT
                                self.assertEqual(blocks[result["dialogue_ids"][-1]].text, expected)
                            else:
                                self.assertEqual(result["dialogue_ids"], (menu_id,))

    def test_native_menu_exposes_all_four_rows_with_matching_dialogue_height(self):
        for scene in clinical.INPUT_IDENTITIES:
            item = self.after[scene]
            metadata = clinical.discovery_metadata(item)
            menu_id = metadata["menu_dialogue_id"]
            block = parse_dialogue(item.components[7]).blocks[menu_id]
            self.assertEqual(block.height, 5)
            self.assertEqual(block.text.splitlines(), [
                "PATIENT WORKSTATION",
                "<Opcode:01:FF>    Patient record",
                "    Staff memorandum",
                "    Leave",
                "    Current status<Close>",
            ])
            editor = AtelScript(item.components[5])
            for entity in exam.TERMINAL_ENTITIES:
                pc = editor.get_script_pointer(entity, 2)
                action = clinical.expected_terminal_action(scene)
                installed = editor.bytecode[pc:pc + len(action)]
                self.assertEqual(installed, action)
                self.assertIn(base.mass_driver._choice_dialog(menu_id) + b"\xA9\x14\x9C", installed)
                self.assertNotIn(b"\xA9\x13\x9C", installed)

    def test_care_handoff_is_an_optional_post_completion_physician_conversation(self):
        item = self.after[591]
        blocks = parse_dialogue(item.components[7]).blocks
        handoff_id = next(block.block_id for block in blocks if block.text == clinical.CARE_HANDOFF)
        self.assertEqual(clinical.CARE_HANDOFF.count("<New>"), 2)
        self.assertIn("Citan\n", clinical.CARE_HANDOFF)
        self.assertIn("Check their breathing", clinical.CARE_HANDOFF)
        self.assertIn("record any changes", clinical.CARE_HANDOFF)
        for state in (0x4000, 0x4400, 0x8000, 0xC400):
            result = self.execute(item, exam.DOCTOR_ENTITY, {0x03FA: state})
            self.assertEqual(handoff_id in result["dialogue_ids"], bool(state & campaign.SECURED_BIT_MASK))
            self.assertEqual(result["variables"][0x03FA], state)
            self.assertEqual(result["bit_writes"], ())
            self.assertEqual(result["bit_clears"], ())
            self.assertIsNone(result["field_change"])
        for scene in (592, 594):
            self.assertNotIn(clinical.CARE_HANDOFF, [block.text for block in parse_dialogue(self.after[scene].components[7]).blocks])

    def test_npcs_keep_hopeful_early_dialogue_then_react_to_revelation_and_shutdown(self):
        for scene in clinical.INPUT_IDENTITIES:
            item = self.after[scene]
            old = AtelScript(self.before[scene].components[5])
            blocks = parse_dialogue(item.components[7]).blocks
            for entity, offset in ((13, 0), (16, 1)):
                original = old.get_script_pointer(entity, 2)
                early = self.execute(item, entity, {0x03FA: 0x0200}, stops=(original,))
                self.assertEqual(early["reason"], "target")
                self.assertEqual(early["dialogue_ids"], ())
                for state, index in ((0x4000, offset), (0x8000, offset + 2), (0xC000, offset + 2)):
                    result = self.execute(item, entity, {0x03FA: state})
                    self.assertEqual(blocks[result["dialogue_ids"][0]].text, clinical.RESPONSES[scene][index])
                    self.assertEqual(result["variables"][0x03FA], state)
                    self.assertEqual(result["bit_writes"], ())
                    self.assertEqual(result["bit_clears"], ())

    def test_only_intended_actions_change_and_keycard_room_is_exact_no_op(self):
        self.assertIs(self.after[593], self.before[593])
        cases = [(self.q_before, self.q_after, {(entity, 2) for entity, *_ in quarantine.RELAYS})]
        cases += [(self.before[scene], self.after[scene], {(entity, 2) for entity in (*exam.TERMINAL_ENTITIES, 13, 16)})
                  for scene in clinical.INPUT_IDENTITIES]
        for before, after, allowed in cases:
            self.assertEqual(before.graphics, after.graphics)
            for index, component in enumerate(before.components):
                if index not in (5, 7):
                    self.assertEqual(component, after.components[index])
            old, new = AtelScript(before.components[5]), AtelScript(after.components[5])
            self.assertEqual(old.bytecode, new.bytecode[:old.bytecode_size])
            self.assertEqual(old.entity_count, new.entity_count)
            for entity in range(old.entity_count):
                for slot in range(32):
                    if (entity, slot) not in allowed:
                        self.assertEqual(old.get_script_pointer(entity, slot), new.get_script_pointer(entity, slot))

    def test_all_new_dialogue_fits_and_foundation_drift_is_rejected(self):
        for before, after, transform in [(self.q_before, self.q_after, quarantine.prepare_quarantine_feedback)] + [
            (self.before[scene], self.after[scene], clinical.prepare_clinical_discoveries) for scene in clinical.INPUT_IDENTITIES
        ]:
            count = len(parse_dialogue(before.components[7]).blocks)
            for block in parse_dialogue(after.components[7]).blocks[count:]:
                measured = parse_dialogue(encode_dialogue((DialogueBlockSpec(0, block.width, block.height, block.text.replace("<Opcode:01:FF>", "")),))).blocks[0]
                with self.subTest(text=block.text):
                    self.assertEqual(campaign._campaign_dialogue_layout_issues(measured), ())
            with self.assertRaises(campaign.SurfaceCampaignBuildError):
                transform(after)
            changed = list(before.components)
            changed[5] = changed[5][:-1]
            with self.assertRaises(campaign.SurfaceCampaignBuildError):
                transform(replace(before, components=tuple(changed)))


if __name__ == "__main__":
    unittest.main()
