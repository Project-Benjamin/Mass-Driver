from __future__ import annotations

from dataclasses import replace
import unittest

from modules.soylent_system import base, build as campaign
from modules.soylent_system.tests.disc_fixtures import source_disc_path
from modules.soylent_system.tests.test_build_surface_soylent_campaign import _run_appointment_vm
from modules.soylent_system.tools import surface_soylent_final_guidance as guidance
from shared.tools.xgdialog import parse_dialogue
from shared.tools.xgfield import parse_field
from shared.tools.xgscript import AtelScript


class FinalGuidanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        donor = source_disc_path("pw_disc1")
        if not donor.is_file():
            raise unittest.SkipTest("checked Soylent clinic donor is unavailable")
        cls.original = {}
        for item in base.prepare_donors(donor):
            scene = item.identity.scene
            if scene not in (565, 589):
                cls.unrelated = item
                continue
            transform = {565: campaign._prepare_service_manifold,
                         589: campaign._prepare_resonance_annex}[scene]
            cls.original[scene] = campaign._prepare_campaign_dialogue_layout_donor(
                campaign._prepare_donor_door_clearance(transform(base.prepare_donor_interactions(item)))
            )
        cls.prepared = {scene: guidance.prepare_final_guidance(item)
                        for scene, item in cls.original.items()}

    def test_only_selected_dialogue_payload_changes(self) -> None:
        for scene, original in self.original.items():
            with self.subTest(scene=scene):
                prepared = self.prepared[scene]
                self.assertEqual(prepared.source_bundle, original.source_bundle)
                self.assertEqual(prepared.graphics, original.graphics)
                self.assertEqual(prepared.header[0x18C:], original.header[0x18C:])
                self.assertEqual(prepared.entry_triangles, original.entry_triangles)
                for index, component in enumerate(original.components):
                    if index != 7:
                        self.assertEqual(prepared.components[index], component)
                before = parse_dialogue(original.components[7]).blocks
                after = parse_dialogue(prepared.components[7]).blocks
                self.assertEqual(len(after), len(before))
                for old, new in zip(before, after, strict=True):
                    self.assertEqual((old.width, old.height), (new.width, new.height))
                    if old.block_id != guidance.DIALOGUE_IDS[scene]:
                        self.assertEqual(old.payload, new.payload)
                self.assertEqual(tuple(part.data for part in parse_field(prepared.bundle).parts),
                                 prepared.components)

    def test_messages_are_explicit_and_fit_the_manual_grid(self) -> None:
        for scene, prepared in self.prepared.items():
            block_id = guidance.DIALOGUE_IDS[scene]
            block = parse_dialogue(prepared.components[7]).blocks[block_id]
            with self.subTest(scene=scene):
                self.assertEqual(block.text, guidance.TEXT[scene])
                self.assertEqual((block.width, block.height), (58, 4))
                base.mass_driver._validate_authored_manual_wrap(
                    {"manual_wrap": True, "width": block.width, "height": block.height,
                     "text": block.text}, block_id,
                )
                self.assertEqual(campaign._campaign_dialogue_layout_issues(block), ())
        self.assertIn("permanently sealed", guidance.TEXT[565])
        self.assertNotIn("currently authorized", guidance.TEXT[565])
        self.assertEqual(guidance.TEXT[589].splitlines()[1], "Up, Down, Up, Left, Right.")
        self.assertIn("Service Manifold input panel", guidance.TEXT[589])

    def test_sealed_shaft_stays_state_neutral_before_and_after_shutdown(self) -> None:
        editor = AtelScript(self.prepared[565].components[base.SCRIPT_INDEX])
        for state in (0, 0xFFFF):
            with self.subTest(state=state):
                variables = {0x03FA: state, 0x021A: state, 0x021E: state}
                result = _run_appointment_vm(
                    editor.bytecode, start_pc=editor.get_script_pointer(7, 2), variables=variables,
                )
                self.assertEqual(result["dialogue_ids"], (16,))
                self.assertEqual(result["variables"], variables)
                self.assertEqual(result["bit_writes"], ())
                self.assertEqual(result["bit_clears"], ())
                self.assertIsNone(result["field_change"])
                self.assertEqual(result["sound_ids"], ())
                self.assertEqual(result["control_restores"], 1)

    def test_readable_pattern_retains_native_audio_and_clue_only_award(self) -> None:
        editor = AtelScript(self.prepared[589].components[base.SCRIPT_INDEX])
        self.assertEqual(editor.get_script_pointer(9, 2), campaign.RESONANCE_CLUE_ACTION_PC)
        native = editor.bytecode[campaign.RESONANCE_CLUE_ACTION_PC:campaign.RESONANCE_CLUE_TAIL_PC]
        cursor = 0
        for sound_id in (0x91, 0x92, 0x91, 0x94, 0x93):
            offset = native.index(bytes((0x74, sound_id, 0x81)), cursor)
            cursor = offset + 3
        self.assertIn(campaign._set_bit(0x021E, 8), native)
        self.assertNotIn(campaign._set_bit(0x021E, 9), editor.bytecode)
        self.assertEqual(editor.bytecode[campaign.RESONANCE_CLUE_TAIL_PC:
                                        campaign.RESONANCE_CLUE_TAIL_PC + 3],
                         campaign._jump(campaign.RESONANCE_CLUE_RECEIPT_ACTION_PC))
        self.assertIn(b"\xF5\x05\x00\x01\x9C",
                      editor.bytecode[campaign.RESONANCE_CLUE_RECEIPT_ACTION_PC:])

    def test_music_pass_keeps_native_scripts_and_wrapper_exact(self) -> None:
        for scene, original in self.original.items():
            with self.subTest(scene=scene):
                normal = campaign._prepare_campaign_music_donor(original)
                final = campaign._prepare_campaign_music_donor(self.prepared[scene])
                self.assertEqual(final.components[base.SCRIPT_INDEX], normal.components[base.SCRIPT_INDEX])
                self.assertEqual(final.components[7], self.prepared[scene].components[7])
                growth = len(final.components[base.SCRIPT_INDEX]) - len(original.components[base.SCRIPT_INDEX])
                self.assertEqual(growth, 0 if scene == 565 else 7)

    def test_drift_and_duplicate_application_fail_closed(self) -> None:
        for scene, original in self.original.items():
            for index, name in ((base.SCRIPT_INDEX, "script"), (7, "dialogue")):
                components = list(original.components)
                components[index] = components[index][:-1]
                with self.subTest(scene=scene, component=name), self.assertRaisesRegex(
                    guidance.FinalGuidanceError, f"input {name} changed"
                ):
                    guidance.prepare_final_guidance(replace(original, components=tuple(components)))
            with self.subTest(scene=scene, duplicate=True), self.assertRaises(guidance.FinalGuidanceError):
                guidance.prepare_final_guidance(self.prepared[scene])

    def test_unrelated_rooms_are_exact_no_ops_and_metadata_names_native_lock(self) -> None:
        self.assertIs(guidance.prepare_final_guidance(self.unrelated), self.unrelated)
        metadata = guidance.final_guidance_metadata()
        self.assertFalse(metadata["script_changes"])
        self.assertFalse(metadata["progression_changes"])
        self.assertEqual(metadata["resonance_clue"]["native_pattern"],
                         ["Up", "Down", "Up", "Left", "Right"])
        self.assertEqual(metadata["resonance_clue"]["authorization_source"],
                         "native field-565 input panel only")


if __name__ == "__main__":
    unittest.main()
