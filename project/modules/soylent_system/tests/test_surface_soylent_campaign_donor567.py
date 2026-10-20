from __future__ import annotations

import hashlib
import unittest
from unittest import mock

import tools.build_surface_soylent_dungeon as surface
import tools.surface_soylent_campaign_donor567 as donor567
from modules.soylent_system.tests.disc_fixtures import source_disc_path
from tools.xgdialog import parse_dialogue
from tools.xgfield import parse_field
from tools.xgscript import AtelScript as ScriptEditor


DISC1 = source_disc_path("pw_disc1")
DISC2 = source_disc_path("pw_disc2")


class SurfaceSoylentDonor567MetadataTests(unittest.TestCase):
    def test_disc_one_source_and_disc_two_target_ids_are_distinct(self) -> None:
        identity = donor567.DONOR567_IDENTITY
        self.assertEqual(identity.scene, 567)
        self.assertEqual(
            (identity.bundle_id, identity.graphics_id),
            donor567.DONOR567_TARGET_IDS,
        )
        self.assertEqual(donor567.DONOR567_TARGET_IDS, (1740, 1741))
        self.assertEqual(donor567.DONOR567_SOURCE_IDS, (1745, 1746))

    def test_active_door_contract_exposes_both_native_leaves(self) -> None:
        self.assertEqual(
            donor567.ACTIVE_DOORS,
            (
                (4, 0x0BDD, 7, 8, 4, 621, 4),
                (5, 0x0BF1, 11, 12, 5, 565, 2),
            ),
        )
        for active in donor567.ACTIVE_DOORS:
            (
                _controller,
                _pc,
                async_helper,
                blocking_helper,
                player_script,
                destination_field,
                destination_parameter,
            ) = active
            action = donor567.paired_door_action(
                async_helper,
                blocking_helper,
                player_script,
                destination_field,
                destination_parameter,
            )
            self.assertEqual(
                action,
                b"\xFE\x54"
                + b"\x07" + bytes((async_helper, 0x24))
                + b"\x09" + bytes((blocking_helper, 0x24))
                + b"\x07\x01" + bytes((0x20 | player_script,))
                + b"\x26\x0A\x80"
                + surface._change_field(
                    destination_field,
                    destination_parameter,
                )
                + b"\x5B",
            )

    def test_collision_integration_constants_are_explicit(self) -> None:
        self.assertTrue(donor567.IMMOVABLE_PRECEDES_STOP)
        self.assertEqual(
            donor567.HARDENED_CONTROLLER_INIT_PCS,
            {4: 0x0B92, 5: 0x0BAB, 6: 0x0BC4},
        )
        self.assertEqual(
            donor567.CONTROLLER_POSITIONS,
            {4: (65, 435), 5: (935, -440), 6: (1000, -125)},
        )
        self.assertEqual(
            donor567.CONTROLLER_TRIANGLES,
            {4: 89, 5: 45, 6: 48},
        )
        self.assertEqual(donor567.CONTROLLER_INTERACTION_HALF_EXTENTS, (30, 30))

    def test_dummy_target_guard_checks_both_exact_payloads(self) -> None:
        exact = {
            canonical_id: surface.DONOR_DUMMY
            for canonical_id in donor567.DONOR567_TARGET_IDS
        }
        with mock.patch.object(
            donor567.surface,
            "_load_canonical_resources",
            return_value=exact,
        ) as loader:
            donor567.verify_donor567_targets_are_dummy("disc2.bin")
        self.assertEqual(
            set(loader.call_args.args[1]),
            set(donor567.DONOR567_TARGET_IDS),
        )

        wrong = dict(exact)
        wrong[donor567.TARGET_GRAPHICS_ID] = b"not the checked dummy"
        with mock.patch.object(
            donor567.surface,
            "_load_canonical_resources",
            return_value=wrong,
        ):
            with self.assertRaisesRegex(
                surface.SurfaceSoylentBuildError,
                "not the checked CDMAKE dummy",
            ):
                donor567.verify_donor567_targets_are_dummy("disc2.bin")


@unittest.skipUnless(DISC1.is_file(), "Perfect Works Disc 1 is unavailable")
class SurfaceSoylentDonor567BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_bundle, cls.graphics = donor567.load_donor567_source(DISC1)
        cls.prepared = donor567.prepare_donor567(
            cls.source_bundle,
            cls.graphics,
        )

    def test_source_identities_match_the_frozen_disc_one_pair(self) -> None:
        identity = donor567.DONOR567_IDENTITY
        self.assertEqual(
            (
                len(self.source_bundle),
                hashlib.sha256(self.source_bundle).hexdigest(),
            ),
            (identity.bundle_size, identity.bundle_sha256),
        )
        self.assertEqual(
            (
                len(self.graphics),
                hashlib.sha256(self.graphics).hexdigest(),
            ),
            (identity.graphics_size, identity.graphics_sha256),
        )

    def test_prepared_output_is_frozen_deterministic_and_changes_two_streams(self) -> None:
        again = donor567.prepare_donor567(self.source_bundle, self.graphics)
        self.assertEqual(self.prepared, again)
        self.assertEqual(
            (
                len(self.prepared.components[surface.SCRIPT_INDEX]),
                hashlib.sha256(
                    self.prepared.components[surface.SCRIPT_INDEX]
                ).hexdigest(),
            ),
            donor567.FINAL_SCRIPT_IDENTITY,
        )
        self.assertEqual(
            (
                len(self.prepared.components[7]),
                hashlib.sha256(self.prepared.components[7]).hexdigest(),
            ),
            donor567.FINAL_DIALOGUE_IDENTITY,
        )
        self.assertEqual(
            (
                len(self.prepared.bundle),
                hashlib.sha256(self.prepared.bundle).hexdigest(),
            ),
            donor567.FINAL_BUNDLE_IDENTITY,
        )
        self.assertEqual(
            (
                len(self.prepared.header),
                hashlib.sha256(self.prepared.header).hexdigest(),
            ),
            donor567.FINAL_HEADER_IDENTITY,
        )
        self.assertEqual(self.prepared.graphics, self.graphics)

        before = parse_field(self.source_bundle)
        after = parse_field(self.prepared.bundle)
        for index, (source_part, prepared_part) in enumerate(
            zip(before.parts, after.parts, strict=True)
        ):
            if index in (surface.SCRIPT_INDEX, 7):
                self.assertNotEqual(source_part.data, prepared_part.data)
            else:
                self.assertEqual(source_part.data, prepared_part.data)

    def test_both_reciprocal_entries_are_concrete_and_on_one_real_triangle(self) -> None:
        editor = ScriptEditor(self.prepared.components[surface.SCRIPT_INDEX])
        triangles = surface._walkmesh_layer(self.prepared.components[1], 0)
        self.assertEqual(self.prepared.entry_triangles, ((0, 88), (1, 51)))
        for parameter in donor567.ENTRY_PARAMETERS:
            offset = 1 + 7 * parameter
            self.assertEqual(
                editor.bytecode[offset:offset + 7],
                donor567.ENTRY_PLAYABLE[parameter],
            )
            camera, actor = donor567.ENTRY_DIRECTIONS[parameter]
            self.assertIn(camera, range(8))
            self.assertIn(actor, range(8))
            hits = tuple(
                index
                for index, triangle in enumerate(triangles)
                if surface._point_inside_triangle(
                    donor567.ENTRY_POSITIONS[parameter],
                    triangle,
                )
            )
            self.assertEqual(hits, (donor567.ENTRY_TRIANGLES[parameter],))

            controller = 4 if parameter == 0 else 5
            position = donor567.CONTROLLER_POSITIONS[controller]
            arrival = donor567.ENTRY_POSITIONS[parameter]
            self.assertGreaterEqual(abs(arrival[0] - position[0]), 75)
            self.assertGreaterEqual(abs(arrival[1] - position[1]), 80)

    def test_all_three_party_slots_use_runtime_selectors(self) -> None:
        editor = ScriptEditor(self.prepared.components[surface.SCRIPT_INDEX])
        for pc, selector in zip(
            donor567.PARTY_INIT_PCS,
            surface.PARTY_SELECTORS,
            strict=True,
        ):
            immediate = surface._immediate(selector)
            self.assertEqual(
                editor.bytecode[pc:pc + 7],
                b"\x16" + immediate + b"\xFE\x0D" + immediate,
            )

    def test_retail_story_entities_are_hidden_ghosted_and_inert(self) -> None:
        editor = ScriptEditor(self.prepared.components[surface.SCRIPT_INDEX])
        self.assertEqual(
            editor.bytecode[
                donor567.NEUTRAL_STORY_INIT_PC:
                donor567.NEUTRAL_STORY_INIT_PC
                + len(donor567.NEUTRAL_STORY_INIT_BODY)
            ],
            donor567.NEUTRAL_STORY_INIT_BODY,
        )
        self.assertEqual(
            donor567.NEUTRAL_STORY_INIT_BODY,
            b"\x2A\x23\x20\x01\x80\x00",
        )
        for entity in donor567.NEUTRAL_STORY_ENTITIES:
            self.assertEqual(
                editor.get_script_pointer(entity, 0),
                donor567.NEUTRAL_STORY_INIT_PC,
            )
            for script_index in range(1, 32):
                self.assertEqual(
                    editor.get_script_pointer(entity, script_index),
                    donor567.NEUTRAL_STORY_STOP_PC,
                )
        self.assertEqual(editor.bytecode[donor567.NEUTRAL_STORY_STOP_PC], 0)

    def test_all_three_door_carriers_are_immovable_before_stop(self) -> None:
        source = ScriptEditor(
            parse_field(self.source_bundle).parts[surface.SCRIPT_INDEX].data
        )
        editor = ScriptEditor(self.prepared.components[surface.SCRIPT_INDEX])
        for controller, (native_pc, native_stop) in (
            donor567.CONTROLLER_NATIVE_INITS.items()
        ):
            source_body = source.bytecode[native_pc:native_stop]
            expected = source_body + donor567.IMMOVABLE_OPCODE + b"\x00"
            prepared_pc = donor567.HARDENED_CONTROLLER_INIT_PCS[controller]
            self.assertEqual(
                editor.get_script_pointer(controller, 0),
                prepared_pc,
            )
            self.assertEqual(
                editor.bytecode[prepared_pc:prepared_pc + len(expected)],
                expected,
            )
            self.assertEqual(
                editor.bytecode[
                    prepared_pc + len(source_body):
                    prepared_pc + len(source_body) + 5
                ],
                donor567.IMMOVABLE_OPCODE + b"\x00",
            )

    def test_active_routes_use_both_native_helpers_and_new_destinations(self) -> None:
        source = ScriptEditor(
            parse_field(self.source_bundle).parts[surface.SCRIPT_INDEX].data
        )
        editor = ScriptEditor(self.prepared.components[surface.SCRIPT_INDEX])
        for active in donor567.ACTIVE_DOORS:
            (
                controller,
                action_pc,
                async_helper,
                blocking_helper,
                player_script,
                destination_field,
                destination_parameter,
            ) = active
            expected = donor567.paired_door_action(
                async_helper,
                blocking_helper,
                player_script,
                destination_field,
                destination_parameter,
            )
            self.assertEqual(editor.get_script_pointer(controller, 2), action_pc)
            self.assertEqual(
                editor.bytecode[action_pc:action_pc + len(expected)],
                expected,
            )
            self.assertIn(b"\x07" + bytes((async_helper, 0x24)), expected)
            self.assertIn(b"\x09" + bytes((blocking_helper, 0x24)), expected)

        for helper, helper_pc in donor567.DOOR_HELPER_PCS.items():
            self.assertEqual(
                source.get_script_pointer(
                    helper,
                    donor567.DOOR_HELPER_SCRIPT_INDEX,
                ),
                helper_pc,
            )
            self.assertEqual(
                editor.get_script_pointer(
                    helper,
                    donor567.DOOR_HELPER_SCRIPT_INDEX,
                ),
                helper_pc,
            )
            self.assertEqual(
                source.bytecode[
                    helper_pc:helper_pc + len(donor567.DOOR_HELPER_BODY)
                ],
                donor567.DOOR_HELPER_BODY,
            )
            self.assertEqual(
                editor.bytecode[
                    helper_pc:helper_pc + len(donor567.DOOR_HELPER_BODY)
                ],
                donor567.DOOR_HELPER_BODY,
            )

    def test_restricted_procedure_door_is_repeatable_and_keeps_both_leafs_closed(self) -> None:
        editor = ScriptEditor(self.prepared.components[surface.SCRIPT_INDEX])
        expected = donor567.sealed_door_action(
            donor567.SEALED_DIALOGUE_ID,
            donor567.SEALED_ACTION_PC,
        )
        self.assertEqual(
            editor.get_script_pointer(donor567.RESTRICTED_CONTROLLER, 2),
            donor567.SEALED_ACTION_PC,
        )
        self.assertEqual(
            editor.bytecode[
                donor567.SEALED_ACTION_PC:
                donor567.SEALED_ACTION_PC + len(expected)
            ],
            expected,
        )
        self.assertTrue(expected.startswith(b"\x33\xFE\x54\x31"))
        self.assertTrue(expected.endswith(b"\x01\x9C\xFE\x53\x00"))
        self.assertNotIn(
            b"\x07" + bytes((donor567.RESTRICTED_ASYNC_HELPER, 0x24)),
            expected,
        )
        self.assertNotIn(
            b"\x09" + bytes((donor567.RESTRICTED_BLOCKING_HELPER, 0x24)),
            expected,
        )

        source_dialogue = parse_dialogue(
            parse_field(self.source_bundle).parts[7].data
        )
        prepared_dialogue = parse_dialogue(self.prepared.components[7])
        self.assertEqual(len(source_dialogue.blocks), 2)
        self.assertEqual(len(prepared_dialogue.blocks), 3)
        for before, after in zip(
            source_dialogue.blocks,
            prepared_dialogue.blocks[:2],
            strict=True,
        ):
            self.assertEqual(
                (before.width, before.height, before.payload),
                (after.width, after.height, after.payload),
            )
        sealed = prepared_dialogue.blocks[donor567.SEALED_DIALOGUE_ID]
        self.assertEqual((sealed.width, sealed.height), (58, 3))
        self.assertEqual(sealed.text, donor567.SEALED_DIALOGUE_TEXT)

    def test_native_lab_music_and_no_encounters_remain_intact(self) -> None:
        editor = ScriptEditor(self.prepared.components[surface.SCRIPT_INDEX])
        self.assertEqual(
            editor.bytecode[
                donor567.MUSIC_PC:
                donor567.MUSIC_PC + len(donor567.MUSIC_OPCODE)
            ],
            donor567.MUSIC_OPCODE,
        )
        self.assertEqual(
            editor.bytecode[
                donor567.NO_RANDOM_ENCOUNTERS_PC:
                donor567.NO_RANDOM_ENCOUNTERS_PC
                + len(donor567.NO_RANDOM_ENCOUNTERS)
            ],
            donor567.NO_RANDOM_ENCOUNTERS,
        )

    def test_source_drift_is_rejected_before_packing(self) -> None:
        bad_bundle = bytearray(self.source_bundle)
        bad_bundle[-1] ^= 1
        with self.assertRaisesRegex(
            surface.SurfaceSoylentBuildError,
            "bundle changed",
        ):
            donor567.prepare_donor567(bytes(bad_bundle), self.graphics)

        bad_graphics = bytearray(self.graphics)
        bad_graphics[-1] ^= 1
        with self.assertRaisesRegex(
            surface.SurfaceSoylentBuildError,
            "graphics changed",
        ):
            donor567.prepare_donor567(
                self.source_bundle,
                bytes(bad_graphics),
            )

    def test_disc_loader_extracts_the_frozen_reference_pair(self) -> None:
        self.assertEqual(
            donor567.load_donor567_source(DISC1),
            (self.source_bundle, self.graphics),
        )

    @unittest.skipUnless(DISC2.is_file(), "Perfect Works Disc 2 is unavailable")
    def test_real_disc_two_targets_are_checked_dummies(self) -> None:
        donor567.verify_donor567_targets_are_dummy(DISC2)


if __name__ == "__main__":
    unittest.main()
