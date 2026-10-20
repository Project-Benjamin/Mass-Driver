from __future__ import annotations

from dataclasses import replace
import unittest

from modules.soylent_system import base, build as campaign
from modules.soylent_system.tests.disc_fixtures import source_disc_path
from modules.soylent_system.tests.test_build_surface_soylent_campaign import _run_appointment_vm
from modules.soylent_system.tools import surface_soylent_campaign_exam_rooms as exam
from modules.soylent_system.tools import surface_soylent_keycard_room as keycard
from shared.tools.xgfield import parse_field
from shared.tools.xgscript import AtelScript


class EmptyKeycardRoomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source, donor = source_disc_path("mass_driver_base"), source_disc_path("pw_disc1")
        if not source.is_file() or not donor.is_file():
            raise unittest.SkipTest("checked Soylent source and clinic donor are unavailable")
        cls.rooms = {
            item.identity.scene: campaign._prepare_campaign_dialogue_layout_donor(
                campaign._prepare_donor_door_clearance(item)
            )
            for item in exam.prepare_exam_rooms_from_discs(source, donor)
        }
        cls.original = cls.rooms[593]
        cls.prepared = keycard.prepare_keycard_room(cls.original)
        cls.old_script = AtelScript(cls.original.components[base.SCRIPT_INDEX])
        cls.script = AtelScript(cls.prepared.components[base.SCRIPT_INDEX])

    def test_both_npcs_have_no_active_init_update_talk_or_called_slots(self):
        for entity in (13, 16):
            for slot in range(32):
                with self.subTest(entity=entity, slot=slot):
                    pc = self.script.get_script_pointer(entity, slot)
                    self.assertEqual(pc, 0x068C)
                    result = _run_appointment_vm(self.script.bytecode, start_pc=pc, variables={})
                    self.assertEqual(result["reason"], "stop")
                    self.assertEqual(result["dialogue_ids"], ())
                    self.assertEqual(result["bit_writes"], ())
        # The other two retired retail humanoids must remain retired too.
        for entity in (14, 15):
            self.assertEqual({self.script.get_script_pointer(entity, slot) for slot in range(32)}, {0x068C})

    def test_party_terminal_doors_and_every_other_entity_are_unchanged(self):
        self.assertEqual(self.script.entity_count, self.old_script.entity_count)
        self.assertEqual(self.script.bytecode, self.old_script.bytecode)
        for entity in range(self.script.entity_count):
            if entity in (13, 16):
                continue
            for slot in range(32):
                with self.subTest(entity=entity, slot=slot):
                    self.assertEqual(self.script.get_script_pointer(entity, slot), self.old_script.get_script_pointer(entity, slot))
        for entity in (4, 5, 19):
            self.assertEqual(self.script.get_script_pointer(entity, 2), 0x06E0)
        self.assertNotEqual(self.script.get_script_pointer(17, 2), 0x068C)
        self.assertNotEqual(self.script.get_script_pointer(18, 4), 0x068C)

    def test_models_assets_dialogue_walkmesh_and_actor_order_are_preserved(self):
        for index, component in enumerate(self.original.components):
            if index != base.SCRIPT_INDEX:
                self.assertEqual(self.prepared.components[index], component)
        self.assertEqual(self.prepared.graphics, self.original.graphics)
        self.assertEqual(self.prepared.source_bundle, self.original.source_bundle)
        self.assertEqual(self.prepared.header[0x18C:], self.original.header[0x18C:])
        decoded = parse_field(self.prepared.bundle)
        self.assertEqual(tuple(part.data for part in decoded.parts), self.prepared.components)
        self.assertIn("NPC-empty", self.prepared.role)
        self.assertNotIn("solid talkable physician", self.prepared.role)

    def run_terminal(self, selection: int, state: int = 1):
        return _run_appointment_vm(
            self.script.bytecode, start_pc=self.script.get_script_pointer(19, 2),
            variables={0x021A: state}, menu_choices={56: selection},
        )

    def test_keycard_accept_still_awards_once_and_repeat_reads_the_record(self):
        accepted = self.run_terminal(1)
        self.assertEqual(accepted["dialogue_ids"], (53, 56, 54))
        self.assertEqual(accepted["sound_ids"], (0x37,))
        self.assertEqual(accepted["variables"][0x021A], 0x0101)
        self.assertEqual(tuple((word, bit) for _, word, bit in accepted["bit_writes"]), ((0x021A, 8),))
        repeated = self.run_terminal(1, accepted["variables"][0x021A])
        self.assertEqual(repeated["dialogue_ids"], (55,))
        self.assertEqual(repeated["sound_ids"], ())
        self.assertEqual(repeated["bit_writes"], ())
        self.assertEqual(repeated["variables"][0x021A], 0x0101)

    def test_leaving_or_cancelling_the_terminal_remains_state_neutral(self):
        for selection in (0, 2, 255):
            with self.subTest(selection=selection):
                result = self.run_terminal(selection)
                self.assertEqual(result["dialogue_ids"], (53, 56))
                self.assertEqual(result["sound_ids"], ())
                self.assertEqual(result["bit_writes"], ())
                self.assertEqual(result["variables"][0x021A], 1)
                self.assertEqual(result["control_restores"], 1)

    def test_other_exam_rooms_are_exact_no_ops(self):
        for scene in (591, 592, 594):
            with self.subTest(scene=scene):
                original = self.rooms[scene]
                self.assertIs(keycard.prepare_keycard_room(original), original)
                script = AtelScript(original.components[base.SCRIPT_INDEX])
                for entity in (13, 16):
                    self.assertNotEqual(script.get_script_pointer(entity, 0), 0x068C)
                    self.assertNotEqual(script.get_script_pointer(entity, 2), 0x068C)

    def test_drift_and_duplicate_application_are_rejected(self):
        components = list(self.original.components)
        editor = AtelScript(components[base.SCRIPT_INDEX])
        editor.set_script_pointer(19, 2, 0x068C)
        components[base.SCRIPT_INDEX] = editor.to_bytes()
        variants = {
            "terminal_pointer": replace(self.original, components=tuple(components)),
            "header": replace(self.original, header=self.original.header[:-1]),
            "bundle": replace(self.original, bundle=self.original.bundle[:-1]),
        }
        for label, changed in variants.items():
            with self.subTest(drift=label), self.assertRaises(keycard.KeycardRoomError):
                keycard.prepare_keycard_room(changed)
        with self.assertRaises(keycard.KeycardRoomError):
            keycard.prepare_keycard_room(self.prepared)


if __name__ == "__main__":
    unittest.main()
