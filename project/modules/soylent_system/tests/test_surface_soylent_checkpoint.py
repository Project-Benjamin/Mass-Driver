from __future__ import annotations

from dataclasses import replace
import unittest

from modules.soylent_system import base, build as campaign
from modules.soylent_system.tests.disc_fixtures import source_disc_path
from modules.soylent_system.tests import test_build_surface_soylent_campaign as vm
from modules.soylent_system.tools import surface_soylent_campaign_stabilization590 as ward
from modules.soylent_system.tools import surface_soylent_checkpoint as checkpoint
from shared.tools.xgdialog import parse_dialogue
from shared.tools.xgfield import parse_field
from shared.tools.xgscript import AtelScript


class StabilizationCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Prepare only the independent ward foundation, before checkpoint/music.
        cls.source = campaign._prepare_campaign_dialogue_layout_donor(
            campaign._prepare_donor_door_clearance(
                campaign._prepare_recovered_stabilization(
                    ward.prepare_stabilization590_from_discs(
                        source_disc_path("mass_driver_base"),
                        source_disc_path("pw_disc1"),
                    )
                )
            )
        )
        cls.prepared = checkpoint.prepare_checkpoint(cls.source)
        cls.editor = AtelScript(cls.prepared.components[base.SCRIPT_INDEX])
        cls.action_pc = cls.editor.get_script_pointer(6, 2)

    def run_choice(self, choice: int) -> dict[str, object]:
        return vm._run_appointment_vm(
            self.editor.bytecode,
            start_pc=self.action_pc,
            variables={0x03FA: 0xABCD, 0x03EE: 0xC123, 0x021A: 0x5151},
            menu_choices={checkpoint.MENU_DIALOGUE_ID: choice},
            stop_pcs=(checkpoint.PRODUCTION_GATE_PC,),
        )

    def assert_progression_untouched(self, result: dict[str, object]) -> None:
        for operand, value in ((0x03FA, 0xABCD), (0x03EE, 0xC123), (0x021A, 0x5151)):
            self.assertEqual(result["variables"][operand], value)
        self.assertEqual(result["bit_writes"], ())
        self.assertEqual(result["bit_clears"], ())
        self.assertIsNone(result["field_change"])
        self.assertEqual(result["battle_ids"], ())
        self.assertEqual(result["blocking_calls"], ())
        self.assertEqual(result["control_suspends"], 1)
        self.assertEqual(result["control_restores"], 1)

    def test_enter_reaches_only_the_unchanged_production_gate(self) -> None:
        result = self.run_choice(1)
        self.assertEqual(result["reason"], "target")
        self.assertEqual(result["pc"], checkpoint.PRODUCTION_GATE_PC)
        self.assertEqual(result["dialogue_ids"], (checkpoint.MENU_DIALOGUE_ID,))
        self.assertEqual((result["hp_restores"], result["mp_restores"]), (0, 0))
        self.assertEqual((result["save_menus"], result["save_returns"]), (0, 0))
        self.assertEqual(result["save_modes"], ())
        self.assert_progression_untouched(result)

    def test_restore_is_repeatable_and_exclusive_to_the_restore_choice(self) -> None:
        for invocation in range(2):
            with self.subTest(invocation=invocation):
                result = self.run_choice(2)
                self.assertEqual(result["reason"], "stop")
                self.assertEqual(result["dialogue_ids"], (
                    checkpoint.MENU_DIALOGUE_ID, checkpoint.RESTORED_DIALOGUE_ID,
                ))
                self.assertEqual((result["hp_restores"], result["mp_restores"]), (1, 1))
                self.assertEqual((result["save_menus"], result["save_returns"]), (0, 0))
                self.assertEqual(result["save_modes"], ())
                self.assert_progression_untouched(result)

    def test_native_save_and_cancel_return_without_healing_or_clearance(self) -> None:
        # Native FE87 only observes menu closure, including cancellation.
        result = self.run_choice(3)
        self.assertEqual(result["reason"], "stop")
        self.assertEqual(result["dialogue_ids"], (checkpoint.MENU_DIALOGUE_ID,))
        self.assertEqual((result["hp_restores"], result["mp_restores"]), (0, 0))
        self.assertEqual((result["save_menus"], result["save_returns"]), (1, 1))
        self.assertEqual(result["save_modes"], (0,))
        self.assert_progression_untouched(result)

    def test_leave_cancel_and_unexpected_selections_have_no_side_effects(self) -> None:
        for choice in (0, 4, 5, 0xFFFF):
            with self.subTest(choice=choice):
                result = self.run_choice(choice)
                self.assertEqual(result["reason"], "stop")
                self.assertEqual(result["dialogue_ids"], (checkpoint.MENU_DIALOGUE_ID,))
                self.assertEqual((result["hp_restores"], result["mp_restores"]), (0, 0))
                self.assertEqual((result["save_menus"], result["save_returns"]), (0, 0))
                self.assertEqual(result["save_modes"], ())
                self.assert_progression_untouched(result)

    def test_menu_uses_native_line_numbers_and_release_loops(self) -> None:
        action = self.editor.bytecode[self.action_pc:]
        self.assertIn(b"\xA9\x14\x9C", action)
        # Each held-X branch yields then returns to the same pad test; its
        # released branch advances past the loop. Cover opening, selection,
        # and native-save/healing-receipt closing presses.
        positions = [i for i in range(len(action)) if action[i:i + 3] == b"\x31\x20\x00"]
        self.assertEqual(len(positions), 3)
        for offset in positions:
            pc = self.action_pc + offset
            self.assertEqual(
                action[offset:offset + 11],
                b"\x31\x20\x00" + (pc + 11).to_bytes(2, "little")
                + b"\x26\x01\x80\x01" + pc.to_bytes(2, "little"),
            )
        blocks = parse_dialogue(self.prepared.components[7]).blocks
        menu = blocks[checkpoint.MENU_DIALOGUE_ID]
        self.assertEqual((menu.width, menu.height), (58, 5))
        self.assertEqual(menu.text, checkpoint.MENU_TEXT)
        self.assertEqual(menu.text.splitlines()[1:], [
            "<Opcode:01:FF>    Enter production", "    Restore HP and EP",
            "    Save progress", "    Leave<Close>",
        ])

    def test_transform_preserves_original_gate_every_other_script_and_room_assets(self) -> None:
        before = AtelScript(self.source.components[base.SCRIPT_INDEX])
        self.assertEqual(self.editor.entity_count, before.entity_count)
        self.assertEqual(self.action_pc, before.bytecode_size)
        self.assertEqual(self.editor.bytecode[:before.bytecode_size], before.bytecode)
        for entity in range(before.entity_count):
            for slot in range(32):
                if (entity, slot) != (6, 2):
                    self.assertEqual(self.editor.get_script_pointer(entity, slot),
                                     before.get_script_pointer(entity, slot))
        self.assertEqual(
            self.editor.bytecode[checkpoint.PRODUCTION_GATE_PC:self.action_pc],
            checkpoint.PRODUCTION_GATE_BYTES,
        )
        self.assertEqual(self.prepared.graphics, self.source.graphics)
        self.assertEqual(self.prepared.entry_triangles, self.source.entry_triangles)
        # Packed component offsets may move; actor/static-model records do not.
        self.assertEqual(self.prepared.header[0x18C:], self.source.header[0x18C:])
        for index, component in enumerate(self.source.components):
            if index not in (base.SCRIPT_INDEX, 7):
                self.assertEqual(self.prepared.components[index], component)
        before_dialogue = parse_dialogue(self.source.components[7]).blocks
        after_dialogue = parse_dialogue(self.prepared.components[7]).blocks
        for old, new in zip(before_dialogue, after_dialogue):
            self.assertEqual((old.width, old.height, old.payload),
                             (new.width, new.height, new.payload))
        reparsed = parse_field(self.prepared.bundle)
        self.assertEqual(tuple(part.data for part in reparsed.parts), self.prepared.components)
        self.assertEqual(checkpoint.prepare_checkpoint(self.source).bundle, self.prepared.bundle)

    def test_wrong_room_drift_and_double_application_fail_closed(self) -> None:
        candidates = [
            replace(self.source, identity=replace(self.source.identity, scene=567)),
            replace(self.source, header=self.source.header[:-1] + b"\x01"),
            replace(self.source, bundle=self.source.bundle + b"\x00"),
            self.prepared,
        ]
        for index in (base.SCRIPT_INDEX, 7):
            components = list(self.source.components)
            components[index] += b"\x00"
            candidates.append(replace(self.source, components=tuple(components)))
        redirected = AtelScript(self.source.components[base.SCRIPT_INDEX])
        redirected.set_script_pointer(6, 2, 0)
        components = list(self.source.components)
        components[base.SCRIPT_INDEX] = redirected.to_bytes()
        candidates.append(replace(self.source, components=tuple(components)))
        for index, candidate in enumerate(candidates):
            with self.subTest(candidate=index), self.assertRaises(checkpoint.CheckpointError):
                checkpoint.prepare_checkpoint(candidate)


if __name__ == "__main__":
    unittest.main()
