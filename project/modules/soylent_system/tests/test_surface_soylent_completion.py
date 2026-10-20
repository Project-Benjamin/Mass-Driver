from __future__ import annotations

from dataclasses import replace
import itertools
from pathlib import Path
import unittest

import modules.soylent_system.base as base
import modules.soylent_system.build as campaign
from modules.soylent_system.tests.test_build_surface_soylent_campaign import _run_appointment_vm
from modules.soylent_system.tools import surface_soylent_completion as completion
from shared.paths import PROJECT_ROOT
from shared.tools.xgdialog import DialogueBlockSpec, encode_dialogue, parse_dialogue
from shared.tools.xgscript import AtelScript


class MenuSelections(dict):
    """Supply successive native menu choices to the independent ATEL VM."""

    def __getitem__(self, key):
        value = super().__getitem__(key)
        if isinstance(value, list):
            if not value:
                raise AssertionError(f"unexpected repeated menu {key}")
            return value.pop(0)
        return value


class ProductionChoiceExecutionTests(unittest.TestCase):
    """Execute emitted ATEL against the independently implemented campaign VM."""

    def run_control(self, field: int, index: int, selection: int | list[int], local: int = 0, persistent: int = 0):
        puzzle = completion.PUZZLES[field]
        body = completion.choice_action(
            puzzle=puzzle, index=index, routine_pc=0,
            instruction_id=10, status_ids=tuple(range(20, 21 + len(puzzle.choices))),
            menu_id=30, result_ids=tuple(range(40, 40 + len(puzzle.choices))), solved_id=50,
        )
        return _run_appointment_vm(
            body, start_pc=0,
            variables={completion.LOCAL_OPERAND: local, completion.STATE_OPERAND: persistent},
            menu_choices=MenuSelections({30: selection}),
        )

    def run_exit(self, field: int, local: int, persistent: int = 0):
        puzzle = completion.PUZZLES[field]
        body = campaign._gate_local_completion(
            progress_bit_index=puzzle.progress_bit, progress_bit_mask=1 << puzzle.progress_bit,
            local_value=puzzle.solution, old_action_pc=0x600,
            denial_dialogue_id=80, success_dialogue_id=81, routine_pc=0,
        )
        return _run_appointment_vm(
            body, start_pc=0, stop_pcs=(0x600,),
            variables={completion.LOCAL_OPERAND: local, completion.STATE_OPERAND: persistent},
        )

    def test_every_control_option_preserves_other_settings_and_persistent_state(self):
        for field, puzzle in completion.PUZZLES.items():
            for index in range(3):
                for selection in range(1, len(puzzle.choices) + 1):
                    for local in range(64):
                        with self.subTest(field=field, index=index, selection=selection, local=local):
                            result = self.run_control(field, index, selection, local, 0x008F)
                            expected = (local & ~(3 << (index * 2))) | (selection << (index * 2))
                            self.assertEqual(result["variables"][completion.LOCAL_OPERAND], expected)
                            self.assertEqual(result["variables"][completion.STATE_OPERAND], 0x008F)
                            self.assertEqual(result["control_suspends"], 1)
                            self.assertEqual(result["control_restores"], 1)
                            self.assertEqual(result["dialogue_ids"][-1], 39 + selection)
                            self.assertFalse(result["bit_writes"])

    def test_leave_cancel_and_unknown_selections_are_state_neutral(self):
        for field, puzzle in completion.PUZZLES.items():
            for selection in (0, len(puzzle.choices) + 1, 255):
                result = self.run_control(field, 1, selection, 0x39, 0x008F)
                self.assertEqual(result["variables"][completion.LOCAL_OPERAND], 0x39)
                self.assertEqual(result["variables"][completion.STATE_OPERAND], 0x008F)
                self.assertEqual(result["dialogue_ids"][-1], 30)
                self.assertEqual(result["control_restores"], 1)

    def test_status_reports_current_configuration_before_menu(self):
        for field, puzzle in completion.PUZZLES.items():
            for index in range(3):
                for setting in range(len(puzzle.choices) + 1):
                    result = self.run_control(field, index, len(puzzle.choices) + 1, setting << (index * 2))
                    self.assertEqual(result["dialogue_ids"], (20 + setting, 30))

    def test_review_instructions_returns_to_current_status_and_menu_without_writes(self):
        for field, puzzle in completion.PUZZLES.items():
            for index in range(3):
                for setting in range(len(puzzle.choices) + 1):
                    local = setting << (index * 2)
                    result = self.run_control(
                        field, index,
                        [len(puzzle.choices) + 2, len(puzzle.choices) + 2, len(puzzle.choices) + 1],
                        local, 0x008F,
                    )
                    self.assertEqual(result["dialogue_ids"], (
                        20 + setting, 30, 10, 20 + setting, 30, 10, 20 + setting, 30,
                    ))
                    self.assertEqual(result["variables"][completion.LOCAL_OPERAND], local)
                    self.assertEqual(result["variables"][completion.STATE_OPERAND], 0x008F)
                    self.assertFalse(result["bit_writes"])
                    self.assertEqual(result["control_suspends"], 1)
                    self.assertEqual(result["control_restores"], 1)

    def test_choice_or_cancel_after_reviewing_instructions_keeps_original_semantics(self):
        for field, puzzle in completion.PUZZLES.items():
            for selection in (0, *range(1, len(puzzle.choices) + 2), 255):
                result = self.run_control(field, 1, [len(puzzle.choices) + 2, selection], 0x35, 0x008F)
                expected = (0x35 & ~0x0C) | (selection << 2) if 1 <= selection <= len(puzzle.choices) else 0x35
                self.assertEqual(result["variables"][completion.LOCAL_OPERAND], expected)
                self.assertEqual(result["variables"][completion.STATE_OPERAND], 0x008F)
                self.assertEqual(result["dialogue_ids"][:5], (21, 30, 10, 21, 30))
                self.assertEqual(result["control_restores"], 1)

    def test_only_exact_safe_configuration_can_commit(self):
        for field, puzzle in completion.PUZZLES.items():
            for choices in itertools.product(range(4), repeat=3):
                local = sum(choice << (2 * index) for index, choice in enumerate(choices))
                with self.subTest(field=field, choices=choices):
                    result = self.run_exit(field, local, 0x008F)
                    if choices == puzzle.correct:
                        self.assertEqual(result["reason"], "target")
                        self.assertEqual(result["dialogue_ids"], (81,))
                        self.assertEqual(result["variables"][completion.STATE_OPERAND], 0x008F | (1 << puzzle.progress_bit))
                    else:
                        self.assertEqual(result["reason"], "stop")
                        self.assertEqual(result["dialogue_ids"], (80,))
                        self.assertEqual(result["variables"][completion.STATE_OPERAND], 0x008F)

    def test_wrong_choice_can_be_reversed_and_exit_retried(self):
        for field, puzzle in completion.PUZZLES.items():
            local = 0
            for index in range(3):
                result = self.run_control(field, index, len(puzzle.choices), local)
                local = result["variables"][completion.LOCAL_OPERAND]
            self.assertEqual(self.run_exit(field, local)["dialogue_ids"], (80,))
            for index, correct in enumerate(puzzle.correct):
                result = self.run_control(field, index, correct, local)
                local = result["variables"][completion.LOCAL_OPERAND]
            self.assertEqual(local, puzzle.solution)
            self.assertEqual(self.run_exit(field, local)["reason"], "target")

    def test_reentry_resets_unsolved_choices_but_solved_controls_are_read_only(self):
        for field, puzzle in completion.PUZZLES.items():
            self.assertEqual(self.run_exit(field, 0)["dialogue_ids"], (80,))
            persistent = 0x008F | (1 << puzzle.progress_bit)
            for index in range(3):
                result = self.run_control(field, index, 1, 0, persistent)
                self.assertEqual(result["dialogue_ids"], (50,))
                self.assertEqual(result["variables"][completion.LOCAL_OPERAND], 0)
                self.assertEqual(result["variables"][completion.STATE_OPERAND], persistent)
                self.assertFalse(result["bit_writes"])
            result = self.run_exit(field, 0, persistent)
            self.assertEqual(result["reason"], "target")
            self.assertFalse(result["dialogue_ids"])


class ProductionFieldIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(PROJECT_ROOT) / "output/Xenogears_PW_CD2_mass_driver_standalone_v166.bin"
        if not source.is_file():
            raise unittest.SkipTest("pinned Soylent source disc is unavailable")
        sources = base.load_source_fields(source)
        cls.foundations = {}
        cls.finished = {}
        for spec in base.NATIVE_WING_SCENES:
            scene = spec.identity.scene
            if scene not in completion.PUZZLES:
                continue
            item = base.prepare_native_interactions(base.prepare_playable_field(spec, *sources[scene]))
            item = campaign._prepare_sorting(item) if scene == 624 else campaign._prepare_core(item)
            item = campaign._prepare_campaign_dialogue_layout_field(campaign._prepare_door_clearance(item))
            cls.foundations[scene] = item
            cls.finished[scene] = completion.prepare_production_puzzle(item)

    def test_only_script_and_dialogue_change_with_same_actors_and_physical_exits(self):
        for scene, before in self.foundations.items():
            after = self.finished[scene]
            # Component sizes/offsets in the fixed header change on repacking;
            # its complete actor/static-node table must remain exact.
            self.assertEqual(before.header[0x190:], after.header[0x190:])
            self.assertEqual(before.graphics, after.graphics)
            self.assertEqual(before.spec.edges, after.spec.edges)
            for index, component in enumerate(before.components):
                if index not in (campaign.SCRIPT_INDEX, 7):
                    self.assertEqual(component, after.components[index])
            old = AtelScript(before.components[campaign.SCRIPT_INDEX])
            new = AtelScript(after.components[campaign.SCRIPT_INDEX])
            self.assertEqual(old.entity_count, new.entity_count)
            allowed = {(1, 2)} | {(entity, 2) for entity in completion.puzzle_metadata(after)["console_entities"]}
            for entity in range(old.entity_count):
                for slot in range(32):
                    if (entity, slot) not in allowed:
                        self.assertEqual(old.get_script_pointer(entity, slot), new.get_script_pointer(entity, slot))
            self.assertEqual(old.bytecode, new.bytecode[:len(old.bytecode)])

    def test_real_controls_and_exit_execute_correctly(self):
        for scene, item in self.finished.items():
            puzzle = completion.PUZZLES[scene]
            metadata = completion.puzzle_metadata(item)
            editor = AtelScript(item.components[campaign.SCRIPT_INDEX])
            variables = {completion.STATE_OPERAND: 0x008F, completion.LOCAL_OPERAND: 0}
            menu_ids = {control["menu_dialogue_id"]: puzzle.correct[index] for index, control in enumerate(metadata["controls"])}
            self.assertEqual(len(menu_ids), 3)
            for pc in metadata["console_action_pcs"]:
                result = _run_appointment_vm(editor.bytecode, start_pc=pc, variables=variables, menu_choices=menu_ids)
                variables = result["variables"]
            self.assertEqual(variables[completion.LOCAL_OPERAND], puzzle.solution)
            old = AtelScript(self.foundations[scene].components[campaign.SCRIPT_INDEX])
            old_gate = old.get_script_pointer(1, 2)
            native_target = int.from_bytes(old.bytecode[old_gate + 9:old_gate + 11], "little")
            result = _run_appointment_vm(editor.bytecode, start_pc=metadata["forward_exit_action_pc"], variables=variables, stop_pcs=(native_target,))
            self.assertEqual(result["reason"], "target")
            self.assertEqual(result["variables"][completion.STATE_OPERAND], 0x008F | (1 << puzzle.progress_bit))

    def test_real_menus_preserve_indices_and_expose_complete_optional_instructions(self):
        for scene, item in self.finished.items():
            puzzle = completion.PUZZLES[scene]
            metadata = completion.puzzle_metadata(item)
            blocks = parse_dialogue(item.components[7]).blocks
            editor = AtelScript(item.components[campaign.SCRIPT_INDEX])
            instruction_id = metadata["instructions_dialogue_id"]
            self.assertEqual(completion._normalized(blocks[instruction_id].text), completion._normalized(puzzle.instruction))
            for index, control in enumerate(metadata["controls"]):
                self.assertEqual(control["choices"], list(puzzle.choices) + ["Leave", "Review instructions"])
                self.assertEqual(control["leave_selection"], len(puzzle.choices) + 1)
                self.assertEqual(control["instructions_selection"], len(puzzle.choices) + 2)
                menu_id = control["menu_dialogue_id"]
                self.assertIn(bytes((0xA9, 0x10 | control["instructions_selection"], 0x9C)), editor.bytecode[control["action_pc"]:])
                result = _run_appointment_vm(
                    editor.bytecode, start_pc=control["action_pc"],
                    variables={completion.STATE_OPERAND: 0x008F, completion.LOCAL_OPERAND: 0x39},
                    menu_choices=MenuSelections({menu_id: [control["instructions_selection"], puzzle.correct[index]]}),
                )
                self.assertEqual(result["dialogue_ids"][1:3], (menu_id, instruction_id))
                self.assertEqual(result["dialogue_ids"][4], menu_id)
                self.assertIn("Leaving now resets it.", blocks[result["dialogue_ids"][-1]].text)
                self.assertEqual(result["variables"][completion.STATE_OPERAND], 0x008F)

    def test_all_added_dialogue_fits_native_windows(self):
        for scene, item in self.finished.items():
            old_count = len(parse_dialogue(self.foundations[scene].components[7]).blocks)
            for block in parse_dialogue(item.components[7]).blocks[old_count:]:
                # The choice cursor is a native control, not a printable glyph.
                measurable = parse_dialogue(encode_dialogue((DialogueBlockSpec(
                    0, block.width, block.height, block.text.replace("<Opcode:01:FF>", ""),
                ),))).blocks[0]
                with self.subTest(scene=scene, block=block.block_id):
                    self.assertEqual(campaign._campaign_dialogue_layout_issues(measurable), ())

    def test_modified_foundation_and_duplicate_install_fail_closed(self):
        for scene, item in self.foundations.items():
            editor = AtelScript(item.components[campaign.SCRIPT_INDEX])
            editor.append_and_repoint(1, 2, b"\x00")
            components = list(item.components)
            components[campaign.SCRIPT_INDEX] = editor.to_bytes()
            with self.assertRaises(campaign.SurfaceCampaignBuildError):
                completion.prepare_production_puzzle(replace(item, components=tuple(components)))
            with self.assertRaises(campaign.SurfaceCampaignBuildError):
                completion.prepare_production_puzzle(self.finished[scene])


if __name__ == "__main__":
    unittest.main()
