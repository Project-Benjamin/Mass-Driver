from __future__ import annotations

from dataclasses import replace
import itertools
import unittest

from modules.soylent_system import base, build as campaign
from modules.soylent_system.tests.disc_fixtures import source_disc_path
from modules.soylent_system.tests import test_build_surface_soylent_campaign as vm
from modules.soylent_system.tools import surface_soylent_campaign_blueprint as blueprint
from modules.soylent_system.tools import surface_soylent_campaign_stabilization590 as ward
from modules.soylent_system.tools import surface_soylent_checkpoint as checkpoint
from modules.soylent_system.tools import surface_soylent_clearance_report as report
from shared.tools.xgdialog import parse_dialogue
from shared.tools.xgfield import parse_field
from shared.tools.xgscript import AtelScript


class StabilizationClearanceReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        foundation = campaign._prepare_campaign_dialogue_layout_donor(
            campaign._prepare_donor_door_clearance(
                campaign._prepare_recovered_stabilization(
                    ward.prepare_stabilization590_from_discs(
                        source_disc_path("mass_driver_base"),
                        source_disc_path("pw_disc1"),
                    )
                )
            )
        )
        cls.source = checkpoint.prepare_checkpoint(foundation)
        cls.prepared = report.prepare_clearance_report(cls.source)
        cls.editor = AtelScript(cls.prepared.components[base.SCRIPT_INDEX])

    def state(self, enabled: tuple[bool, ...] = (False,) * 4) -> dict[int, int]:
        # Preserve unrelated progression, appointment and local puzzle bits.
        values = {0x021A: 0xA500, 0x021E: 0xE001, 0x03FA: 0x5048,
                  0x03EE: 0xC123, 0x07D0: 0x0070}
        for requirement, active in zip(report.CLEARANCES, enabled, strict=True):
            values[requirement.operand] &= ~requirement.mask
            if active:
                values[requirement.operand] |= requirement.mask
        return values

    def run_choice(self, choice: int, values: dict[int, int]) -> dict[str, object]:
        return vm._run_appointment_vm(
            self.editor.bytecode,
            start_pc=self.editor.get_script_pointer(checkpoint.CONTROLLER_ENTITY, 2),
            variables=values,
            menu_choices={checkpoint.MENU_DIALOGUE_ID: choice},
            stop_pcs=(checkpoint.PRODUCTION_GATE_PC,),
        )

    def assert_state_untouched(self, result: dict[str, object], values: dict[int, int]) -> None:
        for operand, value in values.items():
            self.assertEqual(result["variables"][operand], value)
        self.assertEqual(result["bit_writes"], ())
        self.assertEqual(result["bit_clears"], ())
        self.assertIsNone(result["field_change"])
        self.assertEqual(result["battle_ids"], ())
        self.assertEqual(result["blocking_calls"], ())
        self.assertEqual(result["control_suspends"], 1)
        self.assertEqual(result["control_restores"], 1)

    def assert_read_only_report(self, result: dict[str, object], values: dict[int, int]) -> None:
        self.assertEqual(result["reason"], "stop")
        self.assertEqual((result["hp_restores"], result["mp_restores"]), (0, 0))
        self.assertEqual((result["save_menus"], result["save_returns"]), (0, 0))
        self.assertEqual(result["save_modes"], ())
        self.assert_state_untouched(result, values)

    def test_all_sixteen_clearance_combinations_report_exactly_the_missing_steps(self) -> None:
        for enabled in itertools.product((False, True), repeat=4):
            with self.subTest(enabled=enabled):
                values = self.state(enabled)
                result = self.run_choice(report.REPORT_CHOICE, values)
                missing = tuple(requirement.dialogue_id
                                for requirement, active in zip(report.CLEARANCES, enabled)
                                if not active)
                expected = missing or (report.READY_DIALOGUE_ID,)
                self.assertEqual(result["dialogue_ids"], (checkpoint.MENU_DIALOGUE_ID, *expected))
                self.assert_read_only_report(result, values)

    def test_secured_report_takes_priority_without_reopening_or_granting_clearance(self) -> None:
        for enabled in ((False,) * 4, (True,) * 4):
            values = self.state(enabled)
            values[report.STATE_OPERAND] |= report.SECURED_MASK
            result = self.run_choice(report.REPORT_CHOICE, values)
            self.assertEqual(result["dialogue_ids"], (
                checkpoint.MENU_DIALOGUE_ID, report.SECURED_DIALOGUE_ID,
            ))
            self.assert_read_only_report(result, values)

    def test_report_is_repeatable_without_automatically_entering_production(self) -> None:
        values = self.state((True,) * 4)
        for _ in range(2):
            result = self.run_choice(report.REPORT_CHOICE, values)
            self.assertEqual(result["dialogue_ids"], (
                checkpoint.MENU_DIALOGUE_ID, report.READY_DIALOGUE_ID,
            ))
            self.assert_read_only_report(result, values)

    def test_existing_enter_choice_reaches_only_the_original_gate(self) -> None:
        for enabled in ((False,) * 4, (True,) * 4):
            values = self.state(enabled)
            result = self.run_choice(1, values)
            self.assertEqual((result["reason"], result["pc"]),
                             ("target", checkpoint.PRODUCTION_GATE_PC))
            self.assertEqual(result["dialogue_ids"], (checkpoint.MENU_DIALOGUE_ID,))
            self.assertEqual((result["hp_restores"], result["mp_restores"]), (0, 0))
            self.assertEqual(result["save_menus"], 0)
            self.assert_state_untouched(result, values)

    def test_restore_and_native_save_keep_their_original_selection_numbers(self) -> None:
        values = self.state()
        healed = self.run_choice(2, values)
        self.assertEqual(healed["dialogue_ids"], (
            checkpoint.MENU_DIALOGUE_ID, checkpoint.RESTORED_DIALOGUE_ID,
        ))
        self.assertEqual((healed["hp_restores"], healed["mp_restores"]), (1, 1))
        self.assertEqual((healed["save_menus"], healed["save_returns"]), (0, 0))
        self.assert_state_untouched(healed, values)
        saved = self.run_choice(3, values)
        self.assertEqual(saved["dialogue_ids"], (checkpoint.MENU_DIALOGUE_ID,))
        self.assertEqual((saved["hp_restores"], saved["mp_restores"]), (0, 0))
        self.assertEqual((saved["save_menus"], saved["save_returns"]), (1, 1))
        self.assertEqual(saved["save_modes"], (0,))
        self.assert_state_untouched(saved, values)

    def test_leave_cancel_and_invalid_choices_remain_state_neutral(self) -> None:
        for choice in (0, 4, 7, 0xFFFF):
            with self.subTest(choice=choice):
                values = self.state()
                result = self.run_choice(choice, values)
                self.assertEqual(result["dialogue_ids"], (checkpoint.MENU_DIALOGUE_ID,))
                self.assert_read_only_report(result, values)

    def test_report_reads_exactly_the_original_gate_credentials(self) -> None:
        gate = checkpoint.PRODUCTION_GATE_BYTES
        actual_checks = {
            (int.from_bytes(gate[offset + 1:offset + 3], "little"),
             int.from_bytes(gate[offset + 3:offset + 5], "little"))
            for offset in range(0, 32, 8)
        }
        self.assertEqual(actual_checks, {(item.operand, item.mask) for item in report.CLEARANCES})
        self.assertEqual({item.key for item in report.CLEARANCES},
                         set(blueprint.GATE_BY_KEY["production_clearance"].requirements))
        for item in report.CLEARANCES:
            flag = blueprint.FLAG_BY_KEY[item.key]
            self.assertEqual((item.operand, item.mask), (flag.operand, flag.mask))
            self.assertIn(blueprint.AWARD_WRITER_BY_FLAG[item.key].field, item.source_fields)

    def test_menu_preserves_existing_choices_and_exposes_next_objective(self) -> None:
        menu = parse_dialogue(self.prepared.components[7]).blocks[checkpoint.MENU_DIALOGUE_ID]
        self.assertEqual((menu.width, menu.height), (58, 7))
        self.assertEqual(menu.text.splitlines(), [
            "STABILIZATION WARD", "<Opcode:01:FF>    Enter production",
            "    Restore HP and EP", "    Save progress", "    Leave",
            "    Clearance report", "    Next objective<Close>",
        ])
        self.assertEqual(self.editor.bytecode[report.MENU_RANGE_PC - 1:report.MENU_RANGE_PC + 2],
                         b"\xA9\x16\x9C")

    def test_route_guidance_names_the_actual_writers_and_distinguishes_clue_from_lock(self) -> None:
        blocks = parse_dialogue(self.prepared.components[7]).blocks
        expected = {
            5: ("physician's clinic", "Archive", "refusing bloodwork", "team to recover its keycard"),
            6: ("Quarantine", "Genome, Limiter, Nanomachines", "Caste relay OFF", "east continuation"),
            7: ("five-tone clue", "Organic Resonance Annex", "five-direction", "Service Manifold",
                "Hearing the clue alone does\nnot grant authorization"),
            8: ("Clinical Interface", "Scanner Annex", "diagnostic scanner", "interface cutoff"),
        }
        for block_id, phrases in expected.items():
            for phrase in phrases:
                self.assertIn(phrase, blocks[block_id].text)
        self.assertIn("Enter production", blocks[report.READY_DIALOGUE_ID].text)
        self.assertIn("LOCAL NODE SECURED", blocks[report.SECURED_DIALOGUE_ID].text)
        metadata = report.clearance_report_metadata()
        self.assertEqual(metadata["choices"][4:], ["Clearance report", "Next objective"])
        self.assertFalse(metadata["writes_progression_state"])

    def test_next_objective_advances_with_earned_progress_and_never_awards_it(self) -> None:
        values = {0x021A: 0x0100, 0x021E: 0x0000, 0x03FA: 0x000F,
                  0x03EE: 0xC123, 0x07D0: 0x0039}
        for index, (operand, mask, _) in enumerate(report.OBJECTIVES):
            result = self.run_choice(report.OBJECTIVE_CHOICE, values)
            self.assertEqual(result["dialogue_ids"], (checkpoint.MENU_DIALOGUE_ID,
                                                    report.OBJECTIVE_FIRST_ID + index))
            self.assert_read_only_report(result, values)
            values[operand] |= mask
        result = self.run_choice(report.OBJECTIVE_CHOICE, values)
        self.assertEqual(result["dialogue_ids"], (checkpoint.MENU_DIALOGUE_ID, report.BOSS_OBJECTIVE_ID))
        self.assert_read_only_report(result, values)
        values[report.STATE_OPERAND] |= report.SECURED_MASK
        result = self.run_choice(report.OBJECTIVE_CHOICE, values)
        self.assertEqual(result["dialogue_ids"], (checkpoint.MENU_DIALOGUE_ID, report.SECURED_DIALOGUE_ID))
        self.assert_read_only_report(result, values)

    def test_next_objective_prioritizes_first_missing_clearance_for_all_combinations(self) -> None:
        for enabled in itertools.product((False, True), repeat=4):
            values = self.state(enabled)
            values[report.STATE_OPERAND] &= ~0x7000
            first_missing = next((index for index, active in enumerate(enabled) if not active), 4)
            result = self.run_choice(report.OBJECTIVE_CHOICE, values)
            self.assertEqual(result["dialogue_ids"], (checkpoint.MENU_DIALOGUE_ID,
                                                    report.OBJECTIVE_FIRST_ID + first_missing))
            self.assert_read_only_report(result, values)

    def test_completed_objective_has_priority_even_with_incomplete_legacy_clearances(self) -> None:
        values = self.state()
        values[report.STATE_OPERAND] |= report.SECURED_MASK
        result = self.run_choice(report.OBJECTIVE_CHOICE, values)
        self.assertEqual(result["dialogue_ids"], (checkpoint.MENU_DIALOGUE_ID, report.SECURED_DIALOGUE_ID))
        self.assert_read_only_report(result, values)

    def test_only_checkpoint_menu_dispatch_and_dialogue_change_before_appended_report(self) -> None:
        before = AtelScript(self.source.components[base.SCRIPT_INDEX])
        self.assertEqual(self.editor.entity_count, before.entity_count)
        for entity in range(before.entity_count):
            for slot in range(32):
                self.assertEqual(self.editor.get_script_pointer(entity, slot),
                                 before.get_script_pointer(entity, slot))
        changed = {index for index, (old, new) in enumerate(zip(before.bytecode, self.editor.bytecode))
                   if old != new}
        self.assertEqual(changed, {report.MENU_RANGE_PC, report.REPORT_BRANCH_TARGET_PC})
        self.assertEqual(self.editor.bytecode[checkpoint.PRODUCTION_GATE_PC:report.ACTION_PC],
                         checkpoint.PRODUCTION_GATE_BYTES)
        self.assertEqual(self.prepared.graphics, self.source.graphics)
        self.assertEqual(self.prepared.entry_triangles, self.source.entry_triangles)
        self.assertEqual(self.prepared.header[0x18C:], self.source.header[0x18C:])
        for index, component in enumerate(self.source.components):
            if index not in (base.SCRIPT_INDEX, 7):
                self.assertEqual(self.prepared.components[index], component)
        before_blocks = parse_dialogue(self.source.components[7]).blocks
        after_blocks = parse_dialogue(self.prepared.components[7]).blocks
        for old, new in zip(before_blocks, after_blocks):
            if old.block_id != checkpoint.MENU_DIALOGUE_ID:
                self.assertEqual((old.width, old.height, old.payload),
                                 (new.width, new.height, new.payload))
        self.assertEqual(tuple(part.data for part in parse_field(self.prepared.bundle).parts),
                         self.prepared.components)
        self.assertEqual(report.prepare_clearance_report(self.source).bundle, self.prepared.bundle)

    def test_wrong_room_drift_and_double_application_fail_closed(self) -> None:
        candidates = [
            replace(self.source, identity=replace(self.source.identity, scene=567)),
            replace(self.source, header=self.source.header + b"\x00"),
            replace(self.source, bundle=self.source.bundle + b"\x00"),
            self.prepared,
        ]
        for index in (base.SCRIPT_INDEX, 7):
            components = list(self.source.components)
            components[index] += b"\x00"
            candidates.append(replace(self.source, components=tuple(components)))
        for index, candidate in enumerate(candidates):
            with self.subTest(candidate=index), self.assertRaises(report.ClearanceReportError):
                report.prepare_clearance_report(candidate)


if __name__ == "__main__":
    unittest.main()
