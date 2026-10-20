from __future__ import annotations

import hashlib
import struct
import unittest
from unittest import mock

import tools.build_surface_soylent_dungeon as surface
import tools.surface_soylent_campaign_empty_clinic567 as clinic567
from modules.soylent_system.tests.disc_fixtures import source_disc_path
from tools.xgencounter import EncounterTable
from tools.xgfield import parse_field
from tools.xgscript import AtelScript as ScriptEditor


DISC1 = source_disc_path("pw_disc1")
DISC2 = source_disc_path("pw_disc2")


def _identity(data: bytes) -> tuple[int, str]:
    return len(data), hashlib.sha256(data).hexdigest()


class EmptyClinic567MetadataTests(unittest.TestCase):
    def test_disc_one_source_and_disc_two_target_ids_are_frozen(self) -> None:
        identity = clinic567.EMPTY_CLINIC567_IDENTITY
        self.assertEqual(identity.scene, 567)
        self.assertEqual(
            (identity.bundle_id, identity.graphics_id),
            clinic567.EMPTY_CLINIC567_TARGET_IDS,
        )
        self.assertEqual(clinic567.EMPTY_CLINIC567_TARGET_IDS, (1740, 1741))
        self.assertEqual(clinic567.EMPTY_CLINIC567_SOURCE_IDS, (1315, 1316))
        self.assertEqual(
            (identity.bundle_size, identity.bundle_sha256),
            clinic567.SOURCE_BUNDLE_IDENTITY,
        )
        self.assertEqual(
            (identity.graphics_size, identity.graphics_sha256),
            clinic567.SOURCE_GRAPHICS_IDENTITY,
        )

    def test_one_door_integration_contract_matches_the_clinic_geometry(self) -> None:
        self.assertEqual(
            clinic567.RETURN_ROUTE,
            (17, 0x06A7, 18, 4, 621, 4),
        )
        self.assertEqual(clinic567.RETURN_CONTROLLER_POSITION, (0, 250))
        self.assertEqual(clinic567.RETURN_CONTROLLER_TRIANGLE, 34)
        self.assertEqual(clinic567.RETURN_CONTROLLER_TRIANGLES, (16, 34, 35))
        self.assertEqual(clinic567.DOOR_CLOSED_SIDE_PROBE, (0, 200))
        self.assertEqual(clinic567.DOOR_OPEN_SIDE_PROBE, (0, 300))
        self.assertEqual(clinic567.DOOR_SEAL_RADIUS, 0x0E)
        self.assertEqual(
            (
                clinic567.DOOR_INTERACTION_HALF_WIDTH,
                clinic567.DOOR_INTERACTION_HALF_DEPTH,
                clinic567.DOOR_ACTION_HALF_DEPTH,
            ),
            (0x18, 0x08, 0x10),
        )
        self.assertFalse(clinic567.IMMOVABLE_PRECEDES_STOP)
        self.assertEqual(
            clinic567.DOOR_ENDPOINT_ID,
            "intake_medical_examination.examination",
        )

    def test_examination_bed_contract_is_explicit(self) -> None:
        self.assertEqual(clinic567.BED_MODEL_INDEX, 2)
        self.assertEqual(clinic567.BED_HEADER_NODE, 21)
        self.assertEqual(
            clinic567.BED_MODEL_IDENTITY,
            (
                2_408,
                "dde8e7dda4546b058ea5e5f39b9be8c769d18f87546a32f80f68f476454731a4",
            ),
        )
        self.assertEqual(
            clinic567.BED_HEADER_RECORD,
            bytes.fromhex(
                "10 00 00 00 00 04 00 00 00 00 00 00 00 00 02 00"
            ),
        )

    def test_dummy_target_guard_checks_both_exact_payloads(self) -> None:
        exact = {
            canonical_id: surface.DONOR_DUMMY
            for canonical_id in clinic567.EMPTY_CLINIC567_TARGET_IDS
        }
        with mock.patch.object(
            clinic567.surface,
            "_load_canonical_resources",
            return_value=exact,
        ) as loader:
            clinic567.verify_empty_clinic567_targets_are_dummy("disc2.bin")
        self.assertEqual(
            set(loader.call_args.args[1]),
            set(clinic567.EMPTY_CLINIC567_TARGET_IDS),
        )

        wrong = dict(exact)
        wrong[clinic567.TARGET_GRAPHICS_ID] = b"not the checked dummy"
        with mock.patch.object(
            clinic567.surface,
            "_load_canonical_resources",
            return_value=wrong,
        ):
            with self.assertRaisesRegex(
                surface.SurfaceSoylentBuildError,
                "not the checked CDMAKE dummy",
            ):
                clinic567.verify_empty_clinic567_targets_are_dummy("disc2.bin")


@unittest.skipUnless(DISC1.is_file(), "Perfect Works Disc 1 is unavailable")
class EmptyClinic567BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_bundle, cls.graphics = (
            clinic567.load_empty_clinic567_source(DISC1)
        )
        cls.source = parse_field(cls.source_bundle)
        cls.prepared = clinic567.prepare_empty_clinic567(
            cls.source_bundle,
            cls.graphics,
        )

    def test_source_field352_pair_and_components_match_frozen_identities(self) -> None:
        self.assertEqual(
            _identity(self.source_bundle),
            clinic567.SOURCE_BUNDLE_IDENTITY,
        )
        self.assertEqual(
            _identity(self.graphics),
            clinic567.SOURCE_GRAPHICS_IDENTITY,
        )
        self.assertEqual(
            _identity(self.source.header),
            clinic567.SOURCE_HEADER_IDENTITY,
        )
        self.assertEqual(
            tuple(_identity(part.data) for part in self.source.parts),
            clinic567.SOURCE_COMPONENT_IDENTITIES,
        )

    def test_prepared_output_is_frozen_and_changes_only_atel_weights(self) -> None:
        again = clinic567.prepare_empty_clinic567(
            self.source_bundle,
            self.graphics,
        )
        self.assertEqual(self.prepared, again)
        self.assertEqual(
            _identity(self.prepared.components[surface.SCRIPT_INDEX]),
            clinic567.FINAL_SCRIPT_IDENTITY,
        )
        self.assertEqual(
            _identity(self.prepared.components[6]),
            clinic567.FINAL_ENCOUNTER_IDENTITY,
        )
        self.assertEqual(
            _identity(self.prepared.components[7]),
            clinic567.FINAL_DIALOGUE_IDENTITY,
        )
        self.assertEqual(
            _identity(self.prepared.bundle),
            clinic567.FINAL_BUNDLE_IDENTITY,
        )
        self.assertEqual(
            _identity(self.prepared.header),
            clinic567.FINAL_HEADER_IDENTITY,
        )
        self.assertEqual(self.prepared.graphics, self.graphics)

        prepared = parse_field(self.prepared.bundle)
        for index, (source_part, prepared_part) in enumerate(
            zip(self.source.parts, prepared.parts, strict=True)
        ):
            if index in (surface.SCRIPT_INDEX, 6):
                self.assertNotEqual(source_part.data, prepared_part.data)
            else:
                self.assertEqual(source_part.data, prepared_part.data)
        self.assertEqual(
            self.prepared.header[0x190:],
            self.source.header[0x190:],
        )
        self.assertEqual(
            struct.unpack_from("<H", self.prepared.header, 0x18C)[0],
            clinic567.SOURCE_HEADER_ACTOR_COUNT,
        )

    def test_examination_bed_and_environment_are_byte_identical(self) -> None:
        source_models = surface.mass_driver._indexed_bundle_entries(
            self.source.parts[surface.mass_driver.MODEL_INDEX].data
        )
        prepared_models = surface.mass_driver._indexed_bundle_entries(
            self.prepared.components[surface.mass_driver.MODEL_INDEX]
        )
        self.assertEqual(prepared_models, source_models)
        self.assertEqual(
            _identity(prepared_models[clinic567.BED_MODEL_INDEX]),
            clinic567.BED_MODEL_IDENTITY,
        )
        offset = 0x190 + clinic567.BED_HEADER_NODE * 16
        self.assertEqual(
            self.prepared.header[offset:offset + 16],
            clinic567.BED_HEADER_RECORD,
        )
        self.assertGreaterEqual(
            clinic567.BED_HEADER_NODE,
            clinic567.SOURCE_ENTITY_COUNT,
        )
        for index in (0, 1, 2, 3, 4, 7, 8):
            with self.subTest(preserved_component=index):
                self.assertEqual(
                    self.prepared.components[index],
                    self.source.parts[index].data,
                )

    def test_parameter_zero_is_concrete_unique_and_clear_of_the_door(self) -> None:
        editor = ScriptEditor(
            self.prepared.components[surface.SCRIPT_INDEX]
        )
        self.assertEqual(editor.bytecode[1:8], clinic567.ENTRY_PLAYABLE)
        self.assertEqual(self.prepared.entry_triangles, ((0, 16),))
        triangles = surface._walkmesh_layer(self.prepared.components[1], 0)
        hits = tuple(
            index
            for index, triangle in enumerate(triangles)
            if surface._point_inside_triangle(
                clinic567.ENTRY_POSITION,
                triangle,
            )
        )
        self.assertEqual(hits, (clinic567.ENTRY_TRIANGLE,))
        dx = clinic567.ENTRY_POSITION[0] - clinic567.RETURN_CONTROLLER_POSITION[0]
        dz = clinic567.ENTRY_POSITION[1] - clinic567.RETURN_CONTROLLER_POSITION[1]
        effective_radius = 2 * clinic567.DOOR_SEAL_RADIUS + 0x10
        self.assertGreater(dx * dx + dz * dz, effective_radius * effective_radius)

    def test_all_three_party_slots_use_runtime_selectors(self) -> None:
        editor = ScriptEditor(
            self.prepared.components[surface.SCRIPT_INDEX]
        )
        for pc, selector in zip(
            clinic567.PARTY_INIT_PCS,
            surface.PARTY_SELECTORS,
            strict=True,
        ):
            immediate = surface._immediate(selector)
            self.assertEqual(
                editor.bytecode[pc:pc + 7],
                b"\x16" + immediate + b"\xFE\x0D" + immediate,
            )
        for entity, pc in zip(
            clinic567.PARTY_ENTITIES,
            clinic567.PARTY_UPDATE_PCS,
            strict=True,
        ):
            self.assertEqual(editor.get_script_pointer(entity, 1), pc)
            self.assertEqual(editor.bytecode[pc], 0x0C)

    def test_only_safe_room_routines_are_reachable(self) -> None:
        editor = ScriptEditor(
            self.prepared.components[surface.SCRIPT_INDEX]
        )
        self.assertEqual(editor.entity_count, clinic567.SOURCE_ENTITY_COUNT)
        self.assertEqual(editor.bytecode[clinic567.SHARED_STOP_PC], 0)
        for entity in range(editor.entity_count):
            for script_index in range(32):
                pointer = editor.get_script_pointer(entity, script_index)
                if (entity, script_index) in clinic567.FINAL_ACTIVE_SLOTS:
                    with self.subTest(active=(entity, script_index)):
                        self.assertNotEqual(pointer, clinic567.SHARED_STOP_PC)
                else:
                    with self.subTest(retired=(entity, script_index)):
                        self.assertEqual(pointer, clinic567.SHARED_STOP_PC)

        self.assertEqual(editor.get_script_pointer(0, 0), clinic567.GLOBAL_INIT_PC)
        self.assertEqual(editor.get_script_pointer(0, 1), clinic567.SHARED_STOP_PC)
        for entity in clinic567.RETIRED_NPC_ENTITIES:
            for script_index in range(32):
                self.assertEqual(
                    editor.get_script_pointer(entity, script_index),
                    clinic567.SHARED_STOP_PC,
                )
        for script_index in range(32):
            self.assertEqual(
                editor.get_script_pointer(
                    clinic567.DOCTOR_ENTITY,
                    script_index,
                ),
                clinic567.SHARED_STOP_PC,
            )

    def test_sole_door_retains_native_leaf_and_returns_to_intake_p4(self) -> None:
        source_editor = ScriptEditor(
            self.source.parts[surface.SCRIPT_INDEX].data
        )
        editor = ScriptEditor(
            self.prepared.components[surface.SCRIPT_INDEX]
        )
        self.assertEqual(
            editor.get_script_pointer(clinic567.RETURN_CONTROLLER, 0),
            clinic567.RETURN_CONTROLLER_INIT_PC,
        )
        self.assertEqual(
            editor.bytecode[
                clinic567.RETURN_CONTROLLER_INIT_PC:
                clinic567.RETURN_CONTROLLER_INIT_PC
                + len(clinic567.RETURN_CONTROLLER_INIT_BODY)
            ],
            clinic567.RETURN_CONTROLLER_INIT_BODY,
        )
        self.assertEqual(
            editor.get_script_pointer(clinic567.RETURN_CONTROLLER, 2),
            clinic567.RETURN_CONTROLLER_ACTION_PC,
        )
        self.assertEqual(
            editor.bytecode[
                clinic567.RETURN_CONTROLLER_ACTION_PC:
                clinic567.RETURN_CONTROLLER_ACTION_PC
                + len(clinic567.RETURN_ACTION)
            ],
            clinic567.RETURN_ACTION,
        )
        self.assertIn(
            surface._change_field(621, 4),
            clinic567.RETURN_ACTION,
        )
        self.assertNotIn(b"\xD2", clinic567.RETURN_ACTION)
        self.assertNotIn(b"\xF5", clinic567.RETURN_ACTION)
        self.assertNotIn(b"\xFE\x84", clinic567.RETURN_ACTION)

        self.assertEqual(
            source_editor.get_script_pointer(
                clinic567.RETURN_HELPER,
                clinic567.RETURN_HELPER_SCRIPT_INDEX,
            ),
            clinic567.RETURN_HELPER_PC,
        )
        self.assertEqual(
            editor.get_script_pointer(
                clinic567.RETURN_HELPER,
                clinic567.RETURN_HELPER_SCRIPT_INDEX,
            ),
            clinic567.RETURN_HELPER_PC,
        )
        self.assertEqual(
            editor.bytecode[
                clinic567.RETURN_HELPER_PC:
                clinic567.RETURN_HELPER_PC
                + len(clinic567.RETURN_HELPER_BODY)
            ],
            clinic567.RETURN_HELPER_BODY,
        )

    def test_no_random_or_scripted_battle_and_no_reachable_dialogue(self) -> None:
        source_encounters = self.source.parts[6].data
        prepared_encounters = self.prepared.components[6]
        self.assertEqual(prepared_encounters[:-16], source_encounters[:-16])
        self.assertEqual(
            EncounterTable(source_encounters).weights,
            clinic567.SOURCE_ENCOUNTER_WEIGHTS,
        )
        self.assertEqual(
            EncounterTable(prepared_encounters).weights,
            (0,) * 16,
        )
        self.assertEqual(self.prepared.components[7], self.source.parts[7].data)

        editor = ScriptEditor(
            self.prepared.components[surface.SCRIPT_INDEX]
        )
        active_bodies = (
            editor.bytecode[
                clinic567.GLOBAL_INIT_PC:
                clinic567.GLOBAL_INIT_PC + len(clinic567.GLOBAL_INIT_BODY)
            ],
            clinic567.RETURN_CONTROLLER_INIT_BODY,
            clinic567.RETURN_ACTION,
            clinic567.RETURN_HELPER_BODY,
        )
        for body in active_bodies:
            self.assertNotIn(b"\xD2", body)
            self.assertNotIn(b"\xF5", body)
            self.assertNotIn(b"\xFE\x84", body)

    def test_source_drift_is_rejected_before_packing(self) -> None:
        bad_bundle = bytearray(self.source_bundle)
        bad_bundle[-1] ^= 1
        with self.assertRaisesRegex(
            surface.SurfaceSoylentBuildError,
            "bundle changed",
        ):
            clinic567.prepare_empty_clinic567(
                bytes(bad_bundle),
                self.graphics,
            )

        bad_graphics = bytearray(self.graphics)
        bad_graphics[-1] ^= 1
        with self.assertRaisesRegex(
            surface.SurfaceSoylentBuildError,
            "graphics changed",
        ):
            clinic567.prepare_empty_clinic567(
                self.source_bundle,
                bytes(bad_graphics),
            )

    def test_disc_loader_extracts_the_frozen_field352_pair(self) -> None:
        self.assertEqual(
            clinic567.load_empty_clinic567_source(DISC1),
            (self.source_bundle, self.graphics),
        )

    @unittest.skipUnless(DISC2.is_file(), "Perfect Works Disc 2 is unavailable")
    def test_real_disc_two_targets_are_checked_dummies(self) -> None:
        clinic567.verify_empty_clinic567_targets_are_dummy(DISC2)


if __name__ == "__main__":
    unittest.main()
