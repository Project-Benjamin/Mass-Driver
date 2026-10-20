"""Compiled interaction/state regression, not an emulator playthrough.

The VM models released Cross, successful battle returns and completed actor
movement. Native resonance input is supplied through its five input-buffer
words; its comparison branch and award instructions execute unchanged. The
audited camera command between them is checked and skipped explicitly.
"""

from __future__ import annotations

import struct
import unittest

from modules.soylent_system import base, build as campaign
from modules.soylent_system.tests.disc_fixtures import source_disc_path
from modules.soylent_system.tests.test_build_surface_soylent_campaign import (
    _clock_variables,
    _run_appointment_vm,
    _simulate_archive_checkin_action,
)
from modules.soylent_system.tools import surface_soylent_campaign_blueprint as blueprint
from modules.soylent_system.tools import surface_soylent_campaign_exam_rooms as exam_rooms
from modules.soylent_system.tools import surface_soylent_completion as completion
from shared.tools.xgdialog import parse_dialogue
from shared.tools.xgscript import AtelScript


class SurfaceSoylentCompletionRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        source = source_disc_path("mass_driver_base")
        donor = source_disc_path("pw_disc1")
        if not source.is_file() or not donor.is_file():
            raise unittest.SkipTest("Configured Surface campaign discs are unavailable")
        fields, donors, _ = campaign.prepare_campaign(source, donor, include_title=False)
        cls.rooms = {item.spec.identity.scene: item for item in fields}
        cls.rooms.update({item.identity.scene: item for item in donors})
        cls.editors = {
            field: AtelScript(item.components[campaign.SCRIPT_INDEX])
            for field, item in cls.rooms.items()
        }

    def setUp(self) -> None:
        self.values = {operand: 0 for operand in blueprint.reset_masks_by_operand()}
        self.values[campaign.APPOINTMENT_OPERAND] = 0
        self.executed_writers: set[str] = set()

    def flags(self) -> set[str]:
        return {
            flag.key for flag in blueprint.FLAGS if flag.active
            and self.values.get(flag.operand, 0) & flag.mask
        }

    def run_action(self, field: int, entity: int, slot: int = 2, **options):
        self.assertIn(field, blueprint.reachable_rooms(self.flags()))
        editor = self.editors[field]
        before = self.flags()
        result = _run_appointment_vm(
            editor.bytecode, start_pc=editor.get_script_pointer(entity, slot),
            variables=self.values, **options,
        )
        self.values = result["variables"]
        for key in self.flags() - before:
            writer = blueprint.AWARD_WRITER_BY_FLAG[key]
            self.assertEqual((writer.field, writer.script_index), (field, slot))
            self.assertIn(entity, writer.entities)
            self.assertLessEqual(set(writer.prerequisites), before)
            self.executed_writers.add(key)
        if result["field_change"] is not None:
            # Engine field-local words do not survive a transition.
            self.values = {address: value for address, value in self.values.items() if address < 0x07C0}
        return result

    def assert_transition(self, result, destination):
        self.assertEqual(result["field_change"], destination)

    def native_resonance(self) -> None:
        """Exercise the native comparison/award without injecting its flag."""
        self.assertIn(565, blueprint.reachable_rooms(self.flags()))
        self.assertIn("security_keycard", self.flags())
        editor = self.editors[565]
        self.assertEqual(editor.get_script_pointer(12, 2), base.FIELD565_TONE_GATE_ACTION_PC)
        compare = editor.bytecode.index(bytes.fromhex("02 0C 04 01 00 40"), 0x03AC)
        award = editor.bytecode.index(campaign._set_bit(campaign.TONE_OPERAND, campaign.TONE_BIT_INDEX), compare)
        failure = struct.unpack_from("<H", editor.bytecode, compare + 6)[0]
        # The five comparisons lead through the genuine success dialogue and
        # door helper to this non-state camera command before the real award.
        camera = award - 5
        self.assertEqual(editor.bytecode[camera:award], bytes.fromhex("80 99 00 00 80"))
        inputs = dict(zip((0x040C, 0x040E, 0x0410, 0x0412, 0x0414), (1, 2, 1, 4, 3)))
        bad = _run_appointment_vm(
            editor.bytecode, start_pc=compare,
            variables=self.values | inputs | {0x0414: 4}, stop_pcs=(camera, failure),
        )
        self.assertEqual(bad["pc"], failure)
        self.assertFalse(bad["variables"].get(campaign.TONE_OPERAND, 0) & campaign.TONE_MASK)
        accepted = _run_appointment_vm(
            editor.bytecode, start_pc=compare, variables=self.values | inputs,
            stop_pcs=(camera, failure),
        )
        self.assertEqual(accepted["pc"], camera)
        awarded = _run_appointment_vm(
            editor.bytecode, start_pc=award, variables=accepted["variables"],
            stop_pcs=(award + 18,),
        )
        self.values = awarded["variables"]
        self.assertIn("tone_authorized", self.flags())
        self.assertEqual(
            tuple((operand, bit) for _, operand, bit in awarded["bit_writes"]),
            ((campaign.TONE_OPERAND, 9), (campaign.TONE_OPERAND, 8), (campaign.TONE_OPERAND, 10)),
        )
        self.executed_writers.add("tone_authorized")

    def solve_production_room(self, field: int, destination) -> None:
        puzzle = completion.PUZZLES[field]
        metadata = completion.puzzle_metadata(self.rooms[field])
        self.assertEqual(metadata["solution"], {624: 0x39, 626: 0x25}[field])
        denied = self.run_action(field, 1)
        self.assertIsNone(denied["field_change"])
        self.assertEqual(denied["bit_writes"], ())
        blocks = parse_dialogue(self.rooms[field].components[7]).blocks
        for index, entity in enumerate(metadata["console_entities"]):
            text = puzzle.names[index] + "\n" + "\n".join(puzzle.choices + ("Leave", "Review instructions")) + "<Close>"
            normalize = lambda value: "".join(value.replace("<Opcode:01:FF>", "").split())
            menu_ids = [block.block_id for block in blocks if normalize(block.text) == normalize(text)]
            self.assertEqual(len(menu_ids), 1)
            self.run_action(field, entity, menu_choices={menu_ids[0]: puzzle.correct[index]})
        self.assertEqual(self.values[campaign.LOCAL_PUZZLE_OPERAND], puzzle.solution)
        self.assertFalse(self.values[campaign.STATE_OPERAND] & (1 << puzzle.progress_bit))
        self.assert_transition(self.run_action(field, 1), destination)
        self.assertTrue(self.values[campaign.STATE_OPERAND] & (1 << puzzle.progress_bit))

    def test_earned_state_reaches_sufal_and_opens_both_emergency_returns(self) -> None:
        self.assertEqual(self.flags(), set())
        self.assertEqual(blueprint.ACTIVE_CONTENT_BOUNDARIES, ())
        # Production and the finale shortcut must refuse the reset state.
        for field, entity in ((590, 6), (623, 38)):
            editor = self.editors[field]
            denied = _run_appointment_vm(
                editor.bytecode, start_pc=editor.get_script_pointer(entity, 2),
                variables=self.values, menu_choices={3: 1},
            )
            self.assertIsNone(denied["field_change"])
            self.assertEqual(denied["bit_writes"], ())

        registration = _simulate_archive_checkin_action(
            self.editors[549], initial_state=0, initial_appointment=0,
            menu_choices={12: 1}, character_weights={0: 150, 1: 100, 2: 160},
        )
        self.values.update(registration["variables"])
        self.assertEqual(self.flags(), {"intake_checkin_complete"})
        self.executed_writers.add("intake_checkin_complete")
        self.values.update(_clock_variables(0))
        self.assert_transition(self.run_action(549, 6), (621, 0))
        waiting = self.run_action(621, campaign.INTAKE_DOCTOR_ENTITY, 1, stop_on_zero_wait=True)
        self.assertEqual(waiting["reason"], "yield")
        self.values.update(_clock_variables(campaign.APPOINTMENT_DELAY_SECONDS))
        self.run_action(621, campaign.INTAKE_DOCTOR_ENTITY, 1)
        self.run_action(621, campaign.INTAKE_DOCTOR_ENTITY)
        self.assert_transition(self.run_action(621, campaign.INTAKE_CLINIC_DOOR_ENTITY), (550, 0))
        self.run_action(550, campaign.CLINIC_DOCTOR_ENTITY, 1)
        self.run_action(550, campaign.CLINIC_DOCTOR_ENTITY)
        self.run_action(550, campaign.CLINIC_DOCTOR_ENTITY)
        security = self.run_action(550, campaign.CLINIC_DOCTOR_ENTITY, 1)
        self.assertEqual(security["battle_ids"], (campaign.CLINIC_SECURITY_CONFIGURATION,))
        self.assertEqual(security["battle_syncs"], 1)
        self.assertIn("security_keycard", self.flags())
        self.assert_transition(self.run_action(550, campaign.CLINIC_EXIT_ENTITY), (621, 3))

        choice_id = exam_rooms.TERMINAL_DIALOGUE_IDS_BY_SCENE[593][-1]
        self.run_action(593, exam_rooms.TERMINAL_ENTITY, menu_choices={choice_id: 1})
        self.assertIn("quarantine_keycard", self.flags())
        self.assert_transition(self.run_action(621, campaign.INTAKE_PATIENT_DOOR_ENTITY), (565, 0))
        self.native_resonance()
        self.run_action(588, 4)
        self.assertIn("interface_cutoff_armed", self.flags())
        # Fresh field load: earn the actual 0x70 selection via the three relay
        # actions; the fourth, administrative Caste relay stays disabled.
        self.values[campaign.LOCAL_PUZZLE_OPERAND] = 0
        for entity in (17, 18, 19):
            self.run_action(620, entity)
        self.assertEqual(self.values[campaign.LOCAL_PUZZLE_OPERAND], 0x70)
        self.run_action(620, 20)
        self.assertEqual(self.values[campaign.LOCAL_PUZZLE_OPERAND], 0xF0)
        caste_denied = self.run_action(620, 24)
        self.assertIsNone(caste_denied["field_change"])
        self.assertEqual(caste_denied["bit_writes"], ())
        self.assertNotIn("quarantine_complete", self.flags())
        self.run_action(620, 20)
        self.assert_transition(self.run_action(620, 24), (565, 6))
        self.assertIn("quarantine_complete", self.flags())

        # Each production credential remains necessary in the actual compiled
        # gate. Negative probes clear one earned flag in an isolated VM copy.
        ward = self.editors[590]
        for missing in blueprint.GATE_BY_KEY["production_clearance"].requirements:
            flag = blueprint.FLAG_BY_KEY[missing]
            probe = dict(self.values)
            probe[flag.operand] &= ~flag.mask
            with self.subTest(missing_production_clearance=missing):
                denied = _run_appointment_vm(
                    ward.bytecode, start_pc=ward.get_script_pointer(6, 2),
                    variables=probe, menu_choices={3: 1},
                )
                self.assertIsNone(denied["field_change"])
                self.assertEqual(denied["bit_writes"], ())
        self.assert_transition(self.run_action(590, 6, menu_choices={3: 1}), (624, 0))
        self.solve_production_room(624, (626, 0))
        self.solve_production_room(626, (625, 0))
        self.run_action(625, 33)
        self.assert_transition(self.run_action(625, 6), (622, 0))
        boss_menu = next(
            block.block_id for block in parse_dialogue(self.rooms[622].components[7]).blocks
            if "Confront the Sufal Mass" in block.text
        )
        boss = self.run_action(622, 29, menu_choices={boss_menu: 1})
        self.assertEqual(boss["battle_ids"], (9,))
        self.assertEqual(boss["battle_syncs"], 1)
        self.assertIn("facility_secured", self.flags())
        self.assertFalse(self.values[campaign.STATE_OPERAND] & campaign.FINALE_EPILOGUE_PENDING_BIT_MASK)
        self.assert_transition(self.run_action(622, 26), (623, 0))
        self.assert_transition(self.run_action(623, 38), (622, 1))
        self.assertEqual(self.run_action(622, 29)["battle_ids"], ())
        self.assertEqual(self.executed_writers, blueprint.ACTIVE_FLAG_KEYS)


if __name__ == "__main__":
    unittest.main()
