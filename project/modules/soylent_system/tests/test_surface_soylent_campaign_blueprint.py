from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from modules.soylent_system.tools import surface_soylent_campaign_blueprint as blueprint
from modules.soylent_system.tools import surface_soylent_campaign_exam_rooms as exam_rooms


class SurfaceSoylentCampaignBlueprintTests(unittest.TestCase):
    def test_exact_eighteen_room_identity_and_lore_registry(self) -> None:
        self.assertEqual(
            tuple(room.field for room in blueprint.ROOMS),
            (
                623,
                621,
                549,
                550,
                620,
                565,
                567,
                591,
                592,
                593,
                594,
                589,
                588,
                590,
                624,
                626,
                625,
                622,
            ),
        )
        self.assertEqual(len(blueprint.ROOM_BY_FIELD), 18)
        self.assertIn("not the entire crisis", blueprint.FACILITY_IDENTITY["scope"])
        medical = blueprint.ROOM_BY_FIELD[567]
        self.assertEqual(
            (
                medical.slug,
                medical.name,
                medical.origin,
                medical.function,
                medical.lore_beat,
            ),
            (
                "unassigned_medical_examination_room",
                "Unassigned Medical Examination Room",
                blueprint.RoomOrigin.DONOR_ETHOS,
                "Optional empty medical annex with one bed and a read-only workstation",
                (
                    "An unassigned Ethos examination room retains one clinical bed and "
                    "reports that no patient is loaded. It has no NPC, combat, gate, or "
                    "progression logic."
                ),
            ),
        )
        ward = blueprint.ROOM_BY_FIELD[590]
        self.assertEqual(
            (
                ward.slug,
                ward.name,
                ward.origin,
                ward.function,
            ),
            (
                "clinical_stabilization_ward",
                "Clinical Stabilization Ward",
                blueprint.RoomOrigin.DONOR_SOLARIS,
                (
                    "Recovered three-door clinical bridge between service "
                    "circulation and production"
                ),
            ),
        )
        exam_rooms = tuple(blueprint.ROOM_BY_FIELD[field] for field in (591, 592, 593))
        self.assertEqual(
            tuple(room.slug for room in exam_rooms),
            (
                "intake_examination_room_a",
                "intake_examination_room_b",
                "intake_examination_room_c",
            ),
        )
        self.assertTrue(
            all(room.origin is blueprint.RoomOrigin.DONOR_ETHOS for room in exam_rooms)
        )
        self.assertTrue(all("Bright examination room" in room.function for room in exam_rooms))
        self.assertIn("Quarantine keycard", exam_rooms[-1].function)

        treatment = blueprint.ROOM_BY_FIELD[594]
        self.assertEqual(
            (
                treatment.slug,
                treatment.name,
                treatment.origin,
                treatment.function,
            ),
            (
                "treatment_preparation_room",
                "Treatment Preparation Room",
                blueprint.RoomOrigin.DONOR_ETHOS,
                (
                    "Bright self-contained preoperative treatment room with a "
                    "read-only Solaris terminal"
                ),
            ),
        )
        self.assertIn("metabolic conditioning and injections", treatment.lore_beat)
        self.assertIn("without awarding a credential", treatment.lore_beat)

        scanner = blueprint.ROOM_BY_FIELD[588]
        self.assertEqual(
            (scanner.slug, scanner.name, scanner.origin),
            (
                "clinical_interface_scanner_annex",
                "Clinical Interface Scanner Annex",
                blueprint.RoomOrigin.DONOR_SOLARIS,
            ),
        )
        self.assertIn("arms the interface cutoff", scanner.function)
        self.assertIn("field-550 clinical shell", scanner.lore_beat)
        self.assertIn("neither stores nor issues a keycard", scanner.lore_beat)
        for room in blueprint.ROOMS:
            with self.subTest(field=room.field):
                self.assertTrue(room.name)
                self.assertTrue(room.function)
                self.assertGreater(len(room.lore_beat), 40)

    def test_active_twenty_pairs_are_forty_reciprocal_x_endpoints(self) -> None:
        self.assertEqual(
            blueprint.ACTIVE_TOPOLOGY_SCOPE,
            "active_current_release",
        )
        self.assertEqual(len(blueprint.DOOR_PAIRS), 20)
        self.assertEqual(len(blueprint.ENDPOINTS), 40)
        self.assertEqual(len(blueprint.ENDPOINT_BY_ID), 40)
        self.assertEqual(
            Counter(pair.classification for pair in blueprint.DOOR_PAIRS),
            {
                blueprint.DoorClass.MAIN: 7,
                blueprint.DoorClass.ANNEX: 9,
                blueprint.DoorClass.INTERNAL: 3,
                blueprint.DoorClass.SHORTCUT: 1,
            },
        )
        for pair in blueprint.DOOR_PAIRS:
            with self.subTest(pair=pair.id):
                a, b = pair.endpoints
                self.assertEqual(a.destination_field, b.field)
                self.assertEqual(a.destination_entry_parameter, b.local_entry_parameter)
                self.assertEqual(b.destination_field, a.field)
                self.assertEqual(b.destination_entry_parameter, a.local_entry_parameter)
                self.assertEqual(a.interaction, "x")
                self.assertEqual(b.interaction, "x")

    def test_v232_boundary_is_preserved_only_as_historical_evidence(
        self,
    ) -> None:
        self.assertEqual(blueprint.CURRENT_RELEASE_VERSION, 240)
        self.assertEqual(blueprint.ACTIVE_CONTENT_BOUNDARIES, ())
        boundary = blueprint.CURRENT_CONTENT_BOUNDARY
        self.assertEqual(blueprint.HISTORICAL_CONTENT_BOUNDARIES, (boundary,))
        self.assertEqual(
            boundary,
            blueprint.CurrentContentBoundary(
                version=232,
                endpoint_id="quarantine_service.quarantine",
                field=620,
                controller_entity=24,
                action_script_index=2,
                action_pc=0x0C42,
                side="east continuation threshold",
                dialogue_id=24,
                dialogue=(
                    "This is the end for now.\n"
                    "The rest is coming soon...<Close>"
                ),
                dialogue_width=58,
                dialogue_height=4,
                repeatable=True,
                cross_release_drains=2,
                plays_sound=False,
                animates_leaf=False,
                opens=False,
                transitions=False,
                writes_state=False,
                planned_destination=(565, 6),
                preserved_return_endpoint_id="intake_quarantine.quarantine",
                preserved_return_controller_entity=23,
                preserved_return_destination=(621, 2),
            ),
        )

        planned = blueprint.ENDPOINT_BY_ID[boundary.endpoint_id]
        self.assertEqual(
            (
                planned.field,
                planned.destination_field,
                planned.destination_entry_parameter,
            ),
            (620, 565, 6),
        )
        preserved_return = blueprint.ENDPOINT_BY_ID[
            boundary.preserved_return_endpoint_id
        ]
        self.assertEqual(
            (
                preserved_return.field,
                preserved_return.destination_field,
                preserved_return.destination_entry_parameter,
            ),
            (620, 621, 2),
        )
        self.assertFalse(
            any(
                (
                    boundary.plays_sound,
                    boundary.animates_leaf,
                    boundary.opens,
                    boundary.transitions,
                    boundary.writes_state,
                )
            )
        )
        blueprint.validate_blueprint()

    def test_active_links_include_exam_and_treatment_rooms(self) -> None:
        expected = {
            (623, 621, 6), (621, 623, 1),
            (621, 620, 0), (620, 621, 2),
            (621, 549, 0), (549, 621, 0),
            (621, 550, 0), (550, 621, 3),
            (621, 565, 0), (565, 621, 1),
            (621, 567, 0), (567, 621, 4),
            (621, 594, 0), (594, 621, 5),
            (621, 591, 0), (591, 621, 7),
            (621, 592, 0), (592, 621, 8),
            (621, 593, 0), (593, 621, 9),
            (620, 565, 6), (565, 620, 1),
            (565, 589, 0), (589, 565, 4),
            (565, 588, 0), (588, 565, 5),
            (565, 590, 0), (590, 565, 1),
            (565, 590, 1), (590, 565, 2),
            (590, 624, 0), (624, 590, 2),
            (624, 626, 0), (626, 624, 1),
            (626, 625, 0), (625, 626, 1),
            (625, 622, 0), (622, 625, 1),
            (622, 623, 0), (623, 622, 1),
        }
        self.assertEqual(blueprint.physical_links(), expected)

    def test_v195_medical_room_stays_isolated_from_recovered_ward_routes(self) -> None:
        pair = blueprint.DOOR_PAIR_BY_ID["intake_medical_examination"]
        self.assertEqual(pair.classification, blueprint.DoorClass.ANNEX)
        self.assertEqual(
            (
                pair.a.id,
                pair.a.field,
                pair.a.local_entry_parameter,
                pair.a.destination_field,
                pair.a.destination_entry_parameter,
            ),
            ("intake_medical_examination.intake", 621, 4, 567, 0),
        )
        self.assertEqual(
            (
                pair.b.id,
                pair.b.field,
                pair.b.local_entry_parameter,
                pair.b.destination_field,
                pair.b.destination_entry_parameter,
            ),
            ("intake_medical_examination.examination", 567, 0, 621, 4),
        )
        self.assertEqual(
            [candidate.id for candidate in blueprint.DOOR_PAIRS if 567 in candidate.fields],
            ["intake_medical_examination"],
        )
        staff = blueprint.DOOR_PAIR_BY_ID["service_stabilization_staff"]
        self.assertEqual(
            (
                staff.a.field,
                staff.a.local_entry_parameter,
                staff.a.destination_field,
                staff.a.destination_entry_parameter,
                staff.b.field,
                staff.b.local_entry_parameter,
                staff.b.destination_field,
                staff.b.destination_entry_parameter,
            ),
            (565, 2, 590, 1, 590, 1, 565, 2),
        )
        self.assertNotIn(567, staff.fields)

    def test_intake_treatment_room_replaces_the_freight_lab_handoff(self) -> None:
        treatment = blueprint.DOOR_PAIR_BY_ID["intake_treatment_preparation"]
        self.assertEqual(treatment.classification, blueprint.DoorClass.ANNEX)
        self.assertEqual(treatment.gate, "security_keycard_access")
        self.assertEqual(
            (
                treatment.a.id,
                treatment.a.field,
                treatment.a.local_entry_parameter,
                treatment.a.destination_field,
                treatment.a.destination_entry_parameter,
                treatment.b.id,
                treatment.b.field,
                treatment.b.local_entry_parameter,
                treatment.b.destination_field,
                treatment.b.destination_entry_parameter,
            ),
            (
                "intake_treatment_preparation.intake",
                621,
                5,
                594,
                0,
                "intake_treatment_preparation.treatment",
                594,
                0,
                621,
                5,
            ),
        )
        self.assertNotIn(
            (565, 3),
            {
                (endpoint.field, endpoint.local_entry_parameter)
                for endpoint in blueprint.ENDPOINTS
            },
        )

        scanner = blueprint.DOOR_PAIR_BY_ID["service_interface_annex"]
        self.assertEqual(scanner.classification, blueprint.DoorClass.ANNEX)
        self.assertIsNone(scanner.gate)
        self.assertEqual(
            (
                scanner.a.id,
                scanner.a.field,
                scanner.a.local_entry_parameter,
                scanner.a.destination_field,
                scanner.a.destination_entry_parameter,
                scanner.b.id,
                scanner.b.field,
                scanner.b.local_entry_parameter,
                scanner.b.destination_field,
                scanner.b.destination_entry_parameter,
            ),
            (
                "service_interface_annex.service",
                565,
                5,
                588,
                0,
                "service_interface_annex.interface",
                588,
                0,
                565,
                5,
            ),
        )
        self.assertEqual(
            [candidate.id for candidate in blueprint.DOOR_PAIRS if 588 in candidate.fields],
            ["service_interface_annex"],
        )

    def test_three_security_gated_exam_rooms_use_intake_entries_seven_to_nine(self) -> None:
        expected = {
            "intake_exam_a": (7, 591),
            "intake_exam_b": (8, 592),
            "intake_exam_c": (9, 593),
        }
        for pair_id, (intake_entry, room_field) in expected.items():
            with self.subTest(pair=pair_id):
                pair = blueprint.DOOR_PAIR_BY_ID[pair_id]
                self.assertEqual(pair.classification, blueprint.DoorClass.ANNEX)
                self.assertEqual(pair.gate, "security_keycard_access")
                self.assertEqual(
                    (
                        pair.a.id,
                        pair.a.field,
                        pair.a.local_entry_parameter,
                        pair.a.destination_field,
                        pair.a.destination_entry_parameter,
                        pair.b.id,
                        pair.b.field,
                        pair.b.local_entry_parameter,
                        pair.b.destination_field,
                        pair.b.destination_entry_parameter,
                    ),
                    (
                        f"{pair_id}.intake",
                        621,
                        intake_entry,
                        room_field,
                        0,
                        f"{pair_id}.examination",
                        room_field,
                        0,
                        621,
                        intake_entry,
                    ),
                )

    def test_recovered_ward_owns_two_manifold_routes_and_the_production_gate(self) -> None:
        route_specs = {
            pair_id: (
                pair.a.field,
                pair.a.local_entry_parameter,
                pair.a.destination_field,
                pair.a.destination_entry_parameter,
                pair.b.field,
                pair.b.local_entry_parameter,
                pair.b.destination_field,
                pair.b.destination_entry_parameter,
                pair.gate,
            )
            for pair_id in (
                "service_stabilization_production",
                "service_stabilization_staff",
                "stabilization_sorting",
            )
            for pair in (blueprint.DOOR_PAIR_BY_ID[pair_id],)
        }
        self.assertEqual(
            route_specs,
            {
                "service_stabilization_production": (
                    565,
                    1,
                    590,
                    0,
                    590,
                    0,
                    565,
                    1,
                    None,
                ),
                "service_stabilization_staff": (
                    565,
                    2,
                    590,
                    1,
                    590,
                    1,
                    565,
                    2,
                    None,
                ),
                "stabilization_sorting": (
                    590,
                    2,
                    624,
                    0,
                    624,
                    0,
                    590,
                    2,
                    "production_clearance",
                ),
            },
        )
        self.assertNotIn("service_sorting", blueprint.DOOR_PAIR_BY_ID)

    def test_v182_intake_room_swap_owns_exact_reciprocal_entries(self) -> None:
        endpoints = {
            endpoint.id: (
                endpoint.field,
                endpoint.local_entry_parameter,
                endpoint.destination_field,
                endpoint.destination_entry_parameter,
            )
            for endpoint in blueprint.ENDPOINTS
        }
        self.assertEqual(
            {
                endpoint_id: endpoints[endpoint_id]
                for endpoint_id in (
                    "intake_quarantine.intake",
                    "intake_quarantine.quarantine",
                    "intake_archive.intake",
                    "intake_archive.archive",
                    "intake_service_patient.intake",
                    "intake_service_patient.service",
                )
            },
            {
                "intake_quarantine.intake": (621, 2, 620, 0),
                "intake_quarantine.quarantine": (620, 0, 621, 2),
                "intake_archive.intake": (621, 0, 549, 0),
                "intake_archive.archive": (549, 0, 621, 0),
                "intake_service_patient.intake": (621, 1, 565, 0),
                "intake_service_patient.service": (565, 0, 621, 1),
            },
        )

    def test_active_progression_has_reachable_writers_and_reaches_every_room(
        self,
    ) -> None:
        self.assertEqual(
            blueprint.ACTIVE_PROGRESSION_SCOPE,
            "active_campaign_progression",
        )
        snapshots = blueprint.simulate_progression()
        self.assertEqual(
            snapshots[0].reachable_rooms,
            frozenset((549, 567, 621, 623)),
        )
        self.assertEqual(
            snapshots[0].newly_unlocked_doors,
            frozenset(
                (
                    "transfer_intake",
                    "intake_archive",
                    "intake_medical_examination",
                    "service_resonance",
                    "service_interface_annex",
                    "service_stabilization_production",
                    "service_stabilization_staff",
                )
            ),
        )
        self.assertEqual(snapshots[1].stage, "checkin")
        self.assertIn("intake_checkin_complete", snapshots[1].flags)
        self.assertEqual(snapshots[1].newly_reachable_rooms, frozenset((550,)))
        self.assertEqual(
            snapshots[1].newly_unlocked_doors,
            frozenset(("intake_scanner",)),
        )
        self.assertEqual(snapshots[2].stage, "security_keycard")
        self.assertIn("security_keycard", snapshots[2].flags)
        self.assertEqual(
            snapshots[2].newly_reachable_rooms,
            frozenset((565, 588, 589, 590, 591, 592, 593, 594)),
        )
        self.assertEqual(
            snapshots[2].newly_unlocked_doors,
            frozenset(
                (
                    "intake_service_patient",
                    "intake_treatment_preparation",
                    "intake_exam_a",
                    "intake_exam_b",
                    "intake_exam_c",
                )
            ),
        )
        self.assertEqual(snapshots[3].stage, "quarantine_keycard")
        self.assertEqual(
            set(snapshots[3].flags) - set(snapshots[2].flags),
            {"quarantine_keycard"},
        )
        self.assertEqual(snapshots[3].newly_reachable_rooms, frozenset((620,)))
        self.assertEqual(
            snapshots[3].newly_unlocked_doors,
            frozenset(("intake_quarantine", "quarantine_service")),
        )
        self.assertEqual(snapshots[4].stage, "resonance")
        self.assertIn("tone_authorized", snapshots[4].flags)
        self.assertEqual(snapshots[4].newly_reachable_rooms, frozenset())
        self.assertEqual(snapshots[4].newly_unlocked_doors, frozenset())
        self.assertEqual(snapshots[5].stage, "interface_cutoff")
        self.assertEqual(
            set(snapshots[5].flags) - set(snapshots[4].flags),
            {"interface_cutoff_armed"},
        )
        self.assertEqual(snapshots[5].newly_reachable_rooms, frozenset())
        self.assertEqual(snapshots[5].newly_unlocked_doors, frozenset())
        self.assertEqual(snapshots[6].stage, "quarantine")
        self.assertEqual(snapshots[6].newly_reachable_rooms, frozenset((624,)))
        self.assertEqual(
            snapshots[6].newly_unlocked_doors,
            frozenset(("stabilization_sorting",)),
        )
        self.assertEqual(snapshots[7].newly_reachable_rooms, frozenset((626,)))
        self.assertEqual(snapshots[8].newly_reachable_rooms, frozenset((625,)))
        self.assertEqual(snapshots[9].newly_reachable_rooms, frozenset((622,)))
        self.assertEqual(snapshots[-1].reachable_rooms, frozenset(blueprint.ROOM_BY_FIELD))
        self.assertEqual(
            snapshots[-1].newly_unlocked_doors,
            frozenset(("generation_transfer_shortcut",)),
        )

    def test_active_bulkhead_requires_all_four_early_systems(self) -> None:
        gate = blueprint.GATE_BY_KEY["production_clearance"]
        requirements = set(gate.requirements)
        self.assertEqual(
            requirements,
            {
                "security_keycard",
                "tone_authorized",
                "quarantine_complete",
                "interface_cutoff_armed",
            },
        )
        for missing in requirements:
            with self.subTest(missing=missing):
                self.assertFalse(blueprint.gate_is_open(gate, requirements - {missing}))
        self.assertTrue(blueprint.gate_is_open(gate, requirements))

    def test_awards_cannot_be_injected_from_an_unrelated_reachable_room(self) -> None:
        stages = list(blueprint.PROGRESSION_STAGES)
        stages[1] = replace(stages[1], interaction_field=621)
        with self.assertRaisesRegex(blueprint.BlueprintError, "reachable writer in field 549"):
            blueprint.simulate_progression(stages)

    def test_a_missing_live_writer_blocks_progression(self) -> None:
        writers = dict(blueprint.AWARD_WRITER_BY_FLAG)
        del writers["quarantine_complete"]
        with patch.object(blueprint, "AWARD_WRITER_BY_FLAG", writers):
            with self.assertRaisesRegex(blueprint.BlueprintError, "no active writer.*quarantine_complete"):
                blueprint.simulate_progression()

    def test_writer_prerequisites_are_required_before_an_award(self) -> None:
        # A future accidental circulation unlock must not bypass registration.
        with patch.object(blueprint, "reachable_rooms", return_value=frozenset(blueprint.ROOM_BY_FIELD)):
            with self.assertRaisesRegex(blueprint.BlueprintError, "lacks prerequisites.*intake_checkin_complete"):
                blueprint.simulate_progression((blueprint.PROGRESSION_STAGES[2],))

    def test_reactivating_the_old_boundary_prevents_quarantine_completion(self) -> None:
        with patch.object(
            blueprint, "ACTIVE_CONTENT_BOUNDARIES", blueprint.HISTORICAL_CONTENT_BOUNDARIES
        ):
            # The patient-service alternative still reaches every early room;
            # writer validation must catch the lost award, not just the edge.
            with self.assertRaisesRegex(blueprint.BlueprintError, "boundary disables writer.*quarantine_complete"):
                blueprint.simulate_progression()

    def test_registration_and_scanner_are_required_and_caste_is_excluded(self) -> None:
        self.assertIn("Mandatory intake registration", blueprint.ROOM_BY_FIELD[549].function)
        self.assertIn("optional classification records", blueprint.ROOM_BY_FIELD[549].function)
        self.assertIn("Required", blueprint.ROOM_BY_FIELD[588].function)
        self.assertEqual(blueprint.QUARANTINE_REQUIRED_RELAYS, ("Genome", "Limiter", "Nanomachines"))
        self.assertEqual(blueprint.QUARANTINE_EXCLUDED_RELAY, "Caste")
        self.assertEqual(blueprint.QUARANTINE_VALID_SELECTION, 0x70)
        self.assertEqual(blueprint.QUARANTINE_SELECTION_MASK, 0xF0)
        writer = blueprint.AWARD_WRITER_BY_FLAG["quarantine_complete"]
        self.assertEqual((writer.field, writer.entities, writer.script_index), (620, (24,), 2))
        self.assertEqual(writer.endpoint_id, "quarantine_service.quarantine")
        self.assertIn("leave Caste off", writer.condition)
        self.assertIn("Caste is off", blueprint.FLAG_BY_KEY["quarantine_complete"].meaning)

    def test_security_victory_unlocks_service_treatment_and_three_exam_rooms(self) -> None:
        keycard = blueprint.FLAG_BY_KEY["security_keycard"]
        self.assertEqual(
            (
                keycard.operand,
                keycard.mask,
                keycard.bit_index,
                keycard.awarded_in_field,
                keycard.allocation,
            ),
            (0x021A, 0x0001, 0, 550, "retail_reused"),
        )
        self.assertNotIn("scanner_approved", blueprint.FLAG_BY_KEY)

        gate = blueprint.GATE_BY_KEY["security_keycard_access"]
        self.assertEqual(gate.requirements, ("security_keycard",))
        gated_routes = {
            "intake_service_patient",
            "intake_treatment_preparation",
            "intake_exam_a",
            "intake_exam_b",
            "intake_exam_c",
        }
        for pair_id in gated_routes:
            with self.subTest(pair=pair_id):
                route = blueprint.DOOR_PAIR_BY_ID[pair_id]
                self.assertEqual(route.gate, "security_keycard_access")
                self.assertFalse(blueprint.gate_is_open(route.gate, ()))
                self.assertTrue(
                    blueprint.gate_is_open(route.gate, ("security_keycard",))
                )
        self.assertLessEqual(
            gated_routes,
            blueprint.unlocked_door_pairs(("security_keycard",)),
        )
        self.assertEqual(
            blueprint.reachable_rooms(("security_keycard",))
            - blueprint.reachable_rooms(),
            frozenset((565, 588, 589, 590, 591, 592, 593, 594)),
        )

    def test_exam_c_is_sole_writer_and_planned_service_gate_uses_keycard(self) -> None:
        tone = blueprint.FLAG_BY_KEY["tone_authorized"]
        self.assertEqual(
            (
                tone.operand,
                tone.mask,
                tone.bit_index,
                tone.awarded_in_field,
            ),
            (0x021E, 0x0200, 9, 565),
        )
        keycard = blueprint.FLAG_BY_KEY["quarantine_keycard"]
        self.assertEqual(
            (
                keycard.operand,
                keycard.mask,
                keycard.bit_index,
                keycard.awarded_in_field,
                keycard.allocation,
            ),
            (0x021A, 0x0100, 8, 593, "retail_reused"),
        )
        self.assertIn("Solaris terminal", keycard.meaning)
        self.assertIn("no other terminal or scanner", keycard.meaning)
        cutoff = blueprint.FLAG_BY_KEY["interface_cutoff_armed"]
        self.assertEqual(cutoff.awarded_in_field, 588)
        self.assertIn("arms only", cutoff.meaning)
        self.assertIn("never stores or issues", cutoff.meaning)
        self.assertEqual(
            [
                stage.interaction_field
                for stage in blueprint.PROGRESSION_STAGES
                if "quarantine_keycard" in stage.awards
            ],
            [593],
        )

        gate = blueprint.GATE_BY_KEY["quarantine_keycard_access"]
        self.assertEqual(gate.requirements, ("quarantine_keycard",))
        route = blueprint.DOOR_PAIR_BY_ID["quarantine_service"]
        self.assertEqual(route.gate, "quarantine_keycard_access")
        self.assertFalse(blueprint.gate_is_open(route.gate, ("security_keycard",)))
        self.assertTrue(
            blueprint.gate_is_open(route.gate, ("quarantine_keycard",))
        )
        self.assertNotIn(
            "quarantine_service",
            blueprint.unlocked_door_pairs(("security_keycard",)),
        )
        self.assertIn(
            "quarantine_service",
            blueprint.unlocked_door_pairs(("quarantine_keycard",)),
        )
        self.assertEqual(
            blueprint.reachable_rooms(
                (
                    "security_keycard",
                    "tone_authorized",
                    "interface_cutoff_armed",
                    "quarantine_keycard",
                )
            )
            - blueprint.reachable_rooms(("security_keycard", "tone_authorized")),
            frozenset((620,)),
        )

    def test_active_quarantine_gate_and_production_clearance(self) -> None:
        intake = blueprint.DOOR_PAIR_BY_ID["intake_quarantine"]
        service = blueprint.DOOR_PAIR_BY_ID["quarantine_service"]
        self.assertEqual(intake.gate, "quarantine_keycard_access")
        self.assertEqual(service.gate, "quarantine_keycard_access")
        self.assertNotIn("intake_quarantine", blueprint.unlocked_door_pairs(()))
        self.assertNotIn(
            "intake_quarantine",
            blueprint.unlocked_door_pairs(("security_keycard",)),
        )
        self.assertIn(
            "intake_quarantine",
            blueprint.unlocked_door_pairs(("quarantine_keycard",)),
        )
        early_clearances = {
            "security_keycard",
            "tone_authorized",
            "interface_cutoff_armed",
        }
        self.assertNotIn(
            "stabilization_sorting",
            blueprint.unlocked_door_pairs(early_clearances),
        )
        self.assertIn(
            "stabilization_sorting",
            blueprint.unlocked_door_pairs(
                early_clearances | {"quarantine_complete"}
            ),
        )

    def test_bit_10_is_transient_epilogue_state_not_a_progression_award(self) -> None:
        epilogue = blueprint.FLAG_BY_KEY["finale_epilogue_pending"]
        self.assertEqual(
            (
                epilogue.operand,
                epilogue.mask,
                epilogue.bit_index,
                epilogue.awarded_in_field,
                epilogue.active,
            ),
            (0x03FA, 0x0400, 10, None, False),
        )
        self.assertNotIn(epilogue.key, blueprint.ACTIVE_FLAG_KEYS)
        self.assertFalse(
            any(
                epilogue.key in stage.awards
                for stage in blueprint.PROGRESSION_STAGES
            )
        )

    def test_checkin_uses_bit_7_and_progression_keeps_bits_11_through_15(self) -> None:
        checkin = blueprint.FLAG_BY_KEY["intake_checkin_complete"]
        self.assertEqual(
            (checkin.operand, checkin.mask, checkin.bit_index, checkin.awarded_in_field),
            (0x03FA, 0x0080, 7, 549),
        )
        self.assertEqual(blueprint.NEW_CAMPAIGN_BIT_INDICES, (11, 12, 13, 14, 15))
        self.assertEqual(
            [
                (blueprint.FLAG_BY_KEY[key].operand, blueprint.FLAG_BY_KEY[key].mask)
                for key in blueprint.NEW_CAMPAIGN_FLAG_KEYS
            ],
            [
                (0x03FA, 0x0800),
                (0x03FA, 0x1000),
                (0x03FA, 0x2000),
                (0x03FA, 0x4000),
                (0x03FA, 0x8000),
            ],
        )
        self.assertEqual(
            blueprint.reset_masks_by_operand(),
            {0x021A: 0x0101, 0x021E: 0x0200, 0x03FA: 0xFD80},
        )

    def test_manifest_exports_active_topology_and_historical_boundary(self) -> None:
        manifest = blueprint.to_manifest()
        encoded = json.dumps(manifest, sort_keys=True)
        self.assertIn("Ignas Surface Soylent System", encoded)
        self.assertEqual(
            manifest["topology_scope"],
            {
                "door_graph": "active_current_release",
                "progression": "active_campaign_progression",
                "current_release_version": 240,
                "policy": (
                    "the complete route is active; each progression award requires "
                    "a reachable registered writer and its prerequisites; static "
                    "contracts require independent compiled-script and runtime verification"
                ),
            },
        )
        self.assertEqual(len(manifest["rooms"]), 18)
        self.assertEqual(len(manifest["doors"]), 20)
        self.assertEqual(
            sum(len(pair["endpoints"]) for pair in manifest["doors"]),
            40,
        )
        self.assertIsNone(manifest["current_content_boundary"])
        self.assertEqual(manifest["active_content_boundaries"], [])
        self.assertEqual(len(manifest["historical_content_boundaries"]), 1)
        self.assertEqual(
            manifest["historical_content_boundaries"][0],
            {
                "version": 232,
                "endpoint_id": "quarantine_service.quarantine",
                "field": 620,
                "entity": 24,
                "action_script_index": 2,
                "action_pc": 0x0C42,
                "side": "east continuation threshold",
                "dialogue_id": 24,
                "dialogue": (
                    "This is the end for now.\n"
                    "The rest is coming soon..."
                ),
                "window": [58, 4],
                "underlying_future_destination": [565, 6],
                "historical_behavior": {
                    "repeatable": True,
                    "cross_release_drains": 2,
                    "plays_sound": False,
                    "animates_leaf": False,
                    "opens": False,
                    "transitions": False,
                    "writes_state": False,
                },
                "preserved_return": {
                    "endpoint_id": "intake_quarantine.quarantine",
                    "entity": 23,
                    "destination": [621, 2],
                },
            },
        )
        self.assertEqual(
            manifest["quarantine_solution"],
            {
                "enabled_relays": ["Genome", "Limiter", "Nanomachines"],
                "disabled_relay": "Caste",
                "selection_mask": 0xF0,
                "valid_selection": 0x70,
                "completion_endpoint": "quarantine_service.quarantine",
                "commit": "after the east-door success receipt closes",
            },
        )
        self.assertEqual(
            {writer["flag"] for writer in manifest["award_writers"]},
            blueprint.ACTIVE_FLAG_KEYS,
        )

    def test_v233_plan_records_empty_and_occupied_side_bank_terminals(self) -> None:
        plan_path = (
            REPOSITORY_ROOT
            / "modules" / "soylent_system" / "content"
            / "dungeon_plan.json"
        )
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertIn("V233", plan["status"])
        self.assertIn("actual side computer bank", plan["status"])
        self.assertIn("saved aisle position", plan["status"])
        self.assertIn("distinct two-page patient records", plan["status"])
        self.assertIn("fields 591-594", plan["status"])
        self.assertIn("Three narrow, facing-gated X carriers", plan["status"])
        self.assertIn("no patient is loaded", plan["status"])
        self.assertIn("NPC-empty field-567", plan["status"])
        self.assertIn("V230 Classification Archive correction", plan["status"])
        self.assertIn("100% PERFECT FIT", plan["status"])
        self.assertIn("field-620 end notice", plan["status"])
        expected_v225 = {
                "version": 225,
                "bin": {
                    "path": (
                        "output/"
                        "Xenogears_PW_CD2_mass_driver_surface_soylent_v225.bin"
                    ),
                    "size": 698642784,
                    "sha256": (
                        "539e2e33266d71337666c84d9d3a153dfd7555d8db933efa"
                        "dc49376483e6e1ff"
                    ),
                },
                "cue": {
                    "path": (
                        "output/"
                        "Xenogears_PW_CD2_mass_driver_surface_soylent_v225.cue"
                    ),
                    "size": 112,
                    "sha256": (
                        "6a289550cec7003e9742d75f862db41d37214afe499d0dcdda"
                        "b1892839f6b8fd"
                    ),
                },
                "repeat_manifest": {
                    "path": "work/v225r_stage/manifest.json",
                    "size": 119944,
                    "sha256": (
                        "2f6d433e9c257455e70fbc028a07335ec5b84790c646d7ff"
                        "397f544a8ca1bb99"
                    ),
                },
                "field_550": {
                    "bundle": {
                        "size": 78024,
                        "sha256": (
                            "da2db7cac3f81a400ae01115ea0c57aff6c5ff558703ab52"
                            "fddb07336f9e2564"
                        ),
                    },
                    "script": {
                        "size": 5414,
                        "sha256": (
                            "3e8b9942cc6c75eacec771df36d8f322ae9b831f4fd2017b"
                            "1b5266d47087e134"
                        ),
                    },
                    "header": {
                        "size": 1008,
                        "sha256": (
                            "438e5449e97b1de003fde24bf40ecf8b68f9a14a612e6fb5"
                            "8a53b4f9dbfa1db6"
                        ),
                    },
                    "dialogue": {
                        "size": 6056,
                        "sha256": (
                            "3c1f8cc6906384c6a9a0bb23ee5710bde6a524f656baa4b6"
                            "ac8c49659d51bc4e"
                        ),
                    },
                    "walkmesh": {
                        "size": 1948,
                        "sha256": (
                            "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d"
                            "8cca4238393571df"
                        ),
                    },
                },
                "field_352_family": {
                    "scenes": [550, 567, 591, 592, 593],
                    "forward_poll_minimum_z": 228,
                    "forward_poll_size": 63,
                    "seal_center": [0, 266],
                    "seal_half_extents_script_units": [24, 8],
                    "walkmesh_size": 1948,
                    "walkmesh_sha256": (
                        "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d"
                        "8cca4238393571df"
                    ),
                },
                "retained_field_621": {
                    "bundle": {
                        "size": 135648,
                        "sha256": (
                            "011be9593a2c565e6c3bb5f325ef64ac47811592794945ce5"
                            "29fcb3b6eb36677"
                        ),
                    },
                    "script": {
                        "size": 10895,
                        "sha256": (
                            "a362a56e04f91240e4209cb93cdb36a63c31d57bdf2e03c2"
                            "5fca52f202845ea7"
                        ),
                    },
                    "header": {
                        "size": 1408,
                        "sha256": (
                            "bd8be9feef57bff074c81c885d66b329ed20456e42d3a11c"
                            "6b8e03b18550598f"
                        ),
                    },
                },
                "migration": {
                    "source": {
                        "path": (
                            "work/save_backups/SLUS-00669_1_v224_field550_"
                            "door_clip_6df7129d.sav"
                        ),
                        "size": 1851504,
                        "sha256": (
                            "6df7129d144f7b9efe785f24749ca68512f10dda04ca8d402"
                            "2cadf757c9b5dae"
                        ),
                    },
                    "candidate": {
                        "path": (
                            "work/save_candidates/SLUS-00669_1_v225_from_"
                            "6df7129d_field550_clearance.sav"
                        ),
                        "size": 1672710,
                        "sha256": (
                            "b8638edcf76e2c19a829711b57cc7c0beded7a89c60871e2"
                            "cc8aaac60616f9eb"
                        ),
                    },
                    "report": {
                        "path": (
                            "work/save_candidates/SLUS-00669_1_v225_from_"
                            "6df7129d_field550_clearance.json"
                        ),
                        "size": 1810,
                        "sha256": (
                            "4d5c253f890f2840d2ad343c8740ab86362f9999c82998ac"
                            "4836d310df142bcb"
                        ),
                    },
                    "decompressed_payload": {
                        "size": 3819109,
                        "sha256": (
                            "f27cebfc3eb00498cbb76d339d78ee98779c2b2c886855925"
                            "4f474969f0243ed"
                        ),
                        "bytes_changed": 87,
                        "breakdown": {
                            "archive_table": 6,
                            "resident_script": 68,
                            "loaded_header": 2,
                            "runtime_e19": 11,
                        },
                    },
                    "compressed_payload": {
                        "size": 1628725,
                        "sha256": (
                            "a1d542be06f0b474b5c2c4d9703b92aec62b7cbed79221d9"
                            "90e3522f36a1c9fd"
                        ),
                    },
                    "resident_hashes": {
                        "ram": (
                            "60d52d04106554e57b1f444a53f3a6e5a77fbc88a509242"
                            "9f5c441c4edaea2e1"
                        ),
                        "archive_table": (
                            "337607d4873dcc0f5c2eee5cd69f7d61f130badb074b3441"
                            "e09a60cd0e801eb9"
                        ),
                        "loaded_header": (
                            "a061c2a01a90675b62add0f4f36021cba9101bdf6dbf7835"
                            "a770c89193e0c347"
                        ),
                    },
                    "preservation": {
                        "field_variables": True,
                        "gamestate_party": True,
                        "doctor_security_runtime": True,
                        "controller_runtime": True,
                        "closed_leaf": True,
                        "camera": True,
                        "dialogue_windows": True,
                        "dialogue": True,
                        "walkmesh": True,
                        "native_cross_action": True,
                        "allocator_safe": True,
                        "round_trip_verified": True,
                    },
                    "policy": (
                        "apply only to the exact V224 field-550 doorway-"
                        "clipping Slot 1 identity; normalize field 621's "
                        "nonvolatile resident FAT size byte and preserve only "
                        "the volatile table tail; every other state must "
                        "cold-load the affected room from V225 media"
                    ),
                },
        }
        self.assertEqual(plan["historical_releases"]["v225"], expected_v225)
        expected_v226 = {
                "version": 226,
                "bin": {
                    "path": (
                        "output/"
                        "Xenogears_PW_CD2_mass_driver_surface_soylent_v226.bin"
                    ),
                    "size": 698642784,
                    "sha256": (
                        "8a916111d1557c98c904ed95431d973a0d460aa71b52fc3e"
                        "ba56093e9127dda6"
                    ),
                },
                "cue": {
                    "path": (
                        "output/"
                        "Xenogears_PW_CD2_mass_driver_surface_soylent_v226.cue"
                    ),
                    "size": 112,
                    "sha256": (
                        "ee95f0b73bf490e5718b6b3023366f03e385008a46f681c1"
                        "9b7f142ad4cbbcee"
                    ),
                },
                "repeat_manifest": {
                    "path": "work/v226r_stage/manifest.json",
                    "size": 119802,
                    "sha256": (
                        "8c223274a187197e74b06f94edccd74ce7e33b287c3afbed8"
                        "7a6ce471f621f74"
                    ),
                },
                "field_550": {
                    "bundle": {
                        "size": 78024,
                        "sha256": (
                            "b75339d2fdefc2291f2e130329adddafc29a3ca42941c5a2"
                            "4487b3ea6ab9a698"
                        ),
                    },
                    "script": {
                        "size": 5414,
                        "sha256": (
                            "83329cf20bf5bd16e217e7fb445d399ccb2301b612e54c491"
                            "0a3f19ec91d9a85"
                        ),
                    },
                    "header": {
                        "size": 1008,
                        "sha256": (
                            "438e5449e97b1de003fde24bf40ecf8b68f9a14a612e6fb5"
                            "8a53b4f9dbfa1db6"
                        ),
                    },
                    "dialogue": {
                        "size": 6056,
                        "sha256": (
                            "3c1f8cc6906384c6a9a0bb23ee5710bde6a524f656baa4b6"
                            "ac8c49659d51bc4e"
                        ),
                    },
                    "walkmesh": {
                        "size": 1948,
                        "sha256": (
                            "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d"
                            "8cca4238393571df"
                        ),
                    },
                },
                "field_352_family": {
                    "scenes": [550, 567, 591, 592, 593],
                    "automatic_forward_poll": False,
                    "x_button_required": True,
                    "global_update": {
                        "entity": 0,
                        "script": 1,
                        "opcode": "STOP",
                        "pc": "0x068C",
                    },
                    "retired_automatic_cavity": {
                        "span": ["0x044E", "0x04A5"],
                        "size": 87,
                        "sha256": (
                            "85581a31b32134e75912714f1e71cbe0957721e289f114f9"
                            "54a98ed7c4ca8824"
                        ),
                        "active_entry_points": 0,
                    },
                    "seal_center": [0, 266],
                    "seal_half_extents_script_units": [24, 8],
                    "walkmesh_size": 1948,
                    "walkmesh_sha256": (
                        "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d"
                        "8cca4238393571df"
                    ),
                },
                "retained_field_621": {
                    "bundle": {
                        "size": 135648,
                        "sha256": (
                            "011be9593a2c565e6c3bb5f325ef64ac47811592794945ce5"
                            "29fcb3b6eb36677"
                        ),
                    },
                    "script": {
                        "size": 10895,
                        "sha256": (
                            "a362a56e04f91240e4209cb93cdb36a63c31d57bdf2e03c2"
                            "5fca52f202845ea7"
                        ),
                    },
                    "header": {
                        "size": 1408,
                        "sha256": (
                            "bd8be9feef57bff074c81c885d66b329ed20456e42d3a11c"
                            "6b8e03b18550598f"
                        ),
                    },
                },
                "migration": {
                    "source": {
                        "path": (
                            "work/save_backups/"
                            "SLUS-00669_1_v225_auto_open_408a5dc9.sav"
                        ),
                        "size": 1855939,
                        "sha256": (
                            "408a5dc96f5a2633079f8a41b09eefe669400b71a455bd531"
                            "2fa9e0fc6cb22b9"
                        ),
                    },
                    "candidate": {
                        "path": (
                            "work/save_candidates/"
                            "SLUS-00669_1_v226_from_408a5dc9_field592_x_only.sav"
                        ),
                        "size": 1680239,
                        "sha256": (
                            "a3aa3752e1b4b035b1f05f7cc0495bc4d4acd61f98892340"
                            "1e3ee8e30876e7bb"
                        ),
                    },
                    "report": {
                        "path": (
                            "work/save_candidates/"
                            "SLUS-00669_1_v226_from_408a5dc9_field592_x_only.json"
                        ),
                        "size": 1629,
                        "sha256": (
                            "bde8fc1e9c71a7036372ee26223914d549b4c0ffc811501b"
                            "7849d279b5552b45"
                        ),
                    },
                    "decompressed_payload": {
                        "size": 3819109,
                        "sha256": (
                            "3a256a7d4632d79fedd13488d1e7b95fecb038490f1cd149"
                            "6e7db4abe25602cb"
                        ),
                        "bytes_changed": 70,
                        "breakdown": {
                            "archive_table": 4,
                            "resident_script": 62,
                            "runtime_e0": 4,
                        },
                    },
                    "compressed_payload": {
                        "size": 1635031,
                        "sha256": (
                            "d8e3cadf0ac9bbb80026c306c41212b8151147b477312786"
                            "2ed5e8769000ef6f"
                        ),
                    },
                    "resident_hashes": {
                        "ram": (
                            "4a52a6df97f29cb9eb7a4aadbb48c86962bb08d0600853b9"
                            "f81186f2fbf903bf"
                        ),
                        "archive_table": (
                            "3ee67d330d7a2c4b2bbdd8188dfa38a4a0152bea3950be32"
                            "76d40a6ce8862a47"
                        ),
                    },
                    "preservation": {
                        "field_variables": True,
                        "gamestate_party_camera_windows": True,
                        "all_noncontroller_actor_runtime": True,
                        "fei": True,
                        "e17_carrier": True,
                        "e18_closed_leaf": True,
                        "e20_rectangle": True,
                        "loaded_header": True,
                        "walkmesh": True,
                        "native_x_action": True,
                        "resident_archive_volatile_tail": True,
                        "allocator_safe": True,
                        "round_trip_verified": True,
                    },
                    "policy": (
                        "apply only to the exact V225 field-592 automatic-entry "
                        "Slot 1 identity; restore the full retired 87-byte "
                        "automatic-poll cavity and reset both e0:s1 runtime PCs "
                        "to shared STOP 0x068C while preserving the native X "
                        "action; every other state must cold-load the affected "
                        "room from V226 media"
                    ),
                },
            }
        self.assertEqual(plan["historical_releases"]["v226"], expected_v226)
        expected_v227 = {
            **expected_v226,
            "version": 227,
            "bin": {
                "path": (
                    "output/"
                    "Xenogears_PW_CD2_mass_driver_surface_soylent_v227.bin"
                ),
                "size": 698885040,
                "sha256": (
                    "108c753b964831ae6be61ca05fb8cbcd47240d27c0d4f376"
                    "135828b4945596ed"
                ),
            },
            "cue": {
                "path": (
                    "output/"
                    "Xenogears_PW_CD2_mass_driver_surface_soylent_v227.cue"
                ),
                "size": 112,
                "sha256": (
                    "df061663cd9053e195513221997f4042d37c8d23fba9268e9"
                    "d10bdafa577c134"
                ),
            },
            "repeat_manifest": {
                "path": "work/v227r_stage/manifest.json",
                "size": 122987,
                "sha256": (
                    "3a56b3ac97ce837c9356207df6a14d488a26cc0a63524472"
                    "ba903bbae557fb67"
                ),
            },
            "field_352_family": {
                **expected_v226["field_352_family"],
                "scenes": [550, 567, 591, 592, 593, 594],
            },
            "retained_field_621": {
                "bundle": {
                    "size": 135644,
                    "sha256": (
                        "168fb1fb14a0c4745725396aae8d5831d931cd30d0d1c67eb"
                        "6e8d654708eb2bd"
                    ),
                },
                "script": {
                    "size": 10895,
                    "sha256": (
                        "a7c52258a56f10a1bea9e8ee7cdc9c7730b78bd1c21f524a"
                        "12a108302a2172f2"
                    ),
                },
                "header": {
                    "size": 1408,
                    "sha256": (
                        "2d05178f666806c9eaed864d63c44ec41822adeb1164d13e6"
                        "9e50e9cde55432d"
                    ),
                },
            },
            "migration": {
                "source": {
                    "path": (
                        "work/save_backups/"
                        "SLUS-00669_1_v226_intake_door_room_change_9436ef84.sav"
                    ),
                    "size": 1910685,
                    "sha256": (
                        "9436ef847164e1c850828da3c6f90a28ba1ea931763a3b691"
                        "c6117e376333c82"
                    ),
                },
                "candidate": {
                    "path": (
                        "work/save_candidates/"
                        "SLUS-00669_1_v227_from_9436ef84_"
                        "treatment_preparation.sav"
                    ),
                    "size": 1735278,
                    "sha256": (
                        "23221b3468b77096fb9a8e07a11a32203fbd51e4c92d0b7"
                        "fd203b036e30c1950"
                    ),
                },
                "report": {
                    "path": (
                        "work/save_candidates/"
                        "SLUS-00669_1_v227_from_9436ef84_"
                        "treatment_preparation.json"
                    ),
                    "size": 1809,
                    "sha256": (
                        "ee5e4952da80a7eef27af2e39f88b824675c80a5ff1571b"
                        "9816d7f44fcf003e4"
                    ),
                },
                "decompressed_payload": {
                    "size": 3819109,
                    "sha256": (
                        "378c7d8a3fe297927ba5823fcdb77eb7c362c4840eb27f1c"
                        "1f806d604a3858a4"
                    ),
                    "bytes_changed": 3033,
                    "breakdown": {
                        "archive_table": 3031,
                        "resident_script": 2,
                        "runtime_actor_pc": 0,
                    },
                },
                "compressed_payload": {
                    "size": 1694109,
                    "sha256": (
                        "799caec8ddb776d60bd03ecbccabfdd5974f5435d90de971"
                        "9470291ad0c93796"
                    ),
                },
                "resident_hashes": {
                    "ram": (
                        "3aa5febe630f91612e4905ffe6d8f198e46a30cfaa03a78c"
                        "40285e1235ab4591"
                    ),
                    "archive_table": (
                        "bdf07517cbcfb3ad6676aa1deda27086707aa75f7e67c54c"
                        "f002afac9ef45ada"
                    ),
                },
                "preservation": {
                    "field_variables": True,
                    "gamestate_party_camera_windows": True,
                    "all_actor_runtime": True,
                    "fei_e26_e34_idle": True,
                    "loaded_header": True,
                    "dialogue_walkmesh_neighbors": True,
                    "resident_archive_volatile_tail": True,
                    "allocator_safe": True,
                    "round_trip_verified": True,
                },
                "policy": (
                    "apply only to the exact V226 field-621 Intake e26 Slot 1 "
                    "identity; reconstruct the resident archive table for V227 "
                    "media and patch only the retained e26 CHANGE_FIELD operand "
                    "from field 565/p3 to field 594/p0 without changing any "
                    "runtime actor PC; every other state must cold-load field "
                    "621 from V227 media"
                ),
            },
        }
        self.assertEqual(plan["historical_releases"]["v227"], expected_v227)
        expected_v228 = {
            **expected_v227,
            "version": 228,
            "bin": {
                "path": (
                    "output/"
                    "Xenogears_PW_CD2_mass_driver_surface_soylent_v228.bin"
                ),
                "size": 698814480,
                "sha256": (
                    "7bdb5fd17970abb15fc36f32a0907aafd132f80eae818e79b"
                    "a21473380621deb"
                ),
            },
            "cue": {
                "path": (
                    "output/"
                    "Xenogears_PW_CD2_mass_driver_surface_soylent_v228.cue"
                ),
                "size": 112,
                "sha256": (
                    "0c3e3672f69969a0e1ced0e04d8dfc2f2298e706acf42b1c"
                    "58292b4689c714fb"
                ),
            },
            "repeat_manifest": {
                "path": "work/v228r_stage/manifest.json",
                "size": 128038,
                "sha256": (
                    "39e5b82647ecece73fb61784eae7b3cdcf490e411887765b7"
                    "2a58ea8ed592244"
                ),
            },
            "migration": {
                "source": {
                    "path": (
                        "work/save_backups/"
                        "SLUS-00669_1_v227_private_clinic_source_23221b34.sav"
                    ),
                    "size": 1735278,
                    "sha256": (
                        "23221b3468b77096fb9a8e07a11a32203fbd51e4c92d0b7"
                        "fd203b036e30c1950"
                    ),
                },
                "candidate": {
                    "path": (
                        "work/save_candidates/"
                        "SLUS-00669_1_v228_from_23221b34_clinic_aid.sav"
                    ),
                    "size": 1735287,
                    "sha256": (
                        "a991c4f8779bf0ce877fd6ef90806c757e08cde97abc2b2d"
                        "05c692972164df64"
                    ),
                },
                "report": {
                    "path": (
                        "work/save_candidates/"
                        "SLUS-00669_1_v228_from_23221b34_clinic_aid.json"
                    ),
                    "size": 1804,
                    "sha256": (
                        "05d28f4752bc365e54539dc50a9a762f01a724d5787ae891"
                        "0f8a5c172fc5c8b0"
                    ),
                },
                "decompressed_payload": {
                    "size": 3819109,
                    "sha256": (
                        "79c55c9400f47672f60010cc59bb961875107882e358d0510"
                        "d7ad3f4268ae83c"
                    ),
                    "bytes_changed": 2464,
                    "breakdown": {
                        "archive_table": 2464,
                        "resident_script": 0,
                        "loaded_header": 0,
                        "runtime_actor_pc": 0,
                    },
                },
                "compressed_payload": {
                    "size": 1694118,
                    "sha256": (
                        "4dea5b870cafd121c655eda68bc68bfe7cf1fc1fe2d79dd30"
                        "1e6820ba5917960"
                    ),
                },
                "resident_hashes": {
                    "ram": (
                        "9f1c0865fe38aed3b63328fee4a9e278e49a17181c77ad10"
                        "aa47f63670cccbac"
                    ),
                    "archive_table": (
                        "13d23b9b2f983cba4b0883e58cd2b083126642284957fe75"
                        "2ae821e9b0c5a727"
                    ),
                },
                "preservation": {
                    "field_variables": True,
                    "gamestate_party_camera_windows": True,
                    "all_actor_runtime": True,
                    "resident_script": True,
                    "loaded_header": True,
                    "resident_route": True,
                    "resident_archive_volatile_tail": True,
                    "allocator_safe": True,
                    "round_trip_verified": True,
                },
                "policy": (
                    "apply only to the exact V227 field-621 Intake Slot 1 "
                    "identity; rebuild only the serialized archive-table entries "
                    "for off-resident field bundles 591-594 from V228 media while "
                    "preserving the resident field-621 route, script, hybrid V226 "
                    "header, actor runtime, camera, variables, and volatile archive "
                    "tail; every other state must cold-load the affected rooms from "
                    "V228 media"
                ),
            },
        }
        self.assertEqual(plan["historical_releases"]["v228"], expected_v228)
        expected_v229 = {
            **expected_v228,
            "version": 229,
            "bin": {
                "path": (
                    "output/"
                    "Xenogears_PW_CD2_mass_driver_surface_soylent_v229.bin"
                ),
                "size": 698814480,
                "sha256": (
                    "436ecb3a053df1c6860aaedc356fa6db55d2749a27f51b48"
                    "12166b117500ddc4"
                ),
            },
            "cue": {
                "path": (
                    "output/"
                    "Xenogears_PW_CD2_mass_driver_surface_soylent_v229.cue"
                ),
                "size": 112,
                "sha256": (
                    "73812b56b1cb84b57cd8a8b1f9ecd5f67c1b983c475777d"
                    "abee9d3f042c1083d"
                ),
            },
            "repeat_manifest": {
                "path": "work/v229r_stage/manifest.json",
                "size": 129207,
                "sha256": (
                    "2dfba5b96913771b7cf97827d11d08c67336db190c9ebf20"
                    "8609dccf2d7749bf"
                ),
            },
            "field_549": {
                "bundle": {
                    "size": 23336,
                    "sha256": (
                        "4ac69db0dc2abb254135a548ae882ea97334ba72f99ee62e"
                        "c4d9176afc8d8a6f"
                    ),
                },
                "script": {
                    "size": 3841,
                    "sha256": (
                        "04512b30bb15c4188cbe33ed714682c7d579260c5a4b42cc"
                        "8ff71f9136c0a185"
                    ),
                },
                "dialogue": {
                    "size": 2125,
                    "sha256": (
                        "57ed56cde500d327df72112d7d47823b0e66ba25c969b90c"
                        "e5d9c259a5c7401b"
                    ),
                },
                "archive_return_seal": {
                    "entity": 16,
                    "radius_script_units": 8,
                    "effective_player_contact_radius": 32,
                },
                "archive_return_x": {
                    "entity": 6,
                    "script": 2,
                    "effective_half_extents_world_units": [36, 40],
                    "automatic_proximity_action": False,
                },
            },
            "migration": {
                "source": {
                    "path": (
                        "work/save_candidates/"
                        "SLUS-00669_1_v228_source_cd84f8b5_field549.sav"
                    ),
                    "size": 1632883,
                    "sha256": (
                        "cd84f8b59d80398f81dc10f153633f4105be152f2c4f79b2"
                        "fa73a33174debfa8"
                    ),
                },
                "candidate": {
                    "path": (
                        "work/save_candidates/"
                        "SLUS-00669_1_v229_from_cd84f8b5_field549_seal.sav"
                    ),
                    "size": 1485222,
                    "sha256": (
                        "13ae2d667d8edd24ef60c1465f3e1771363823bcc4fd78c09"
                        "064564a90eba21c"
                    ),
                },
                "report": {
                    "path": (
                        "work/save_candidates/"
                        "SLUS-00669_1_v229_from_cd84f8b5_field549_seal.json"
                    ),
                    "size": 2030,
                    "sha256": (
                        "8927c34eb57f296b4804953d65a88c22920f2fd5865ff6e3"
                        "34ddf6807a6ba181"
                    ),
                },
                "decompressed_payload": {
                    "size": 3819109,
                    "sha256": (
                        "6c05487dfbf434f01ecf2c7a11fa6a9784c4d74df0be6e19"
                        "47365788e06c698e"
                    ),
                    "bytes_changed": 2,
                    "changed_offsets": ["0x10C74D", "0x11217C"],
                    "breakdown": {
                        "archive_table": 0,
                        "resident_script": 1,
                        "runtime_e16_radius": 1,
                    },
                },
                "compressed_payload": {
                    "size": 1438158,
                    "sha256": (
                        "0f3a002be787eafc2595fd5599cac9a0e7ccf1cd75c709c0"
                        "d6b7d3ed16ca051f"
                    ),
                },
                "resident_hashes": {
                    "ram": (
                        "b9a8b4e8aed436bf6b0bf2ce00b499afda537db715073f44"
                        "24c08f730aa48a5d"
                    ),
                    "archive_table": (
                        "13d23b9b2f983cba4b0883e58cd2b083126642284957fe75"
                        "2ae821e9b0c5a727"
                    ),
                    "field_549_script": (
                        "04512b30bb15c4188cbe33ed714682c7d579260c5a4b42cc"
                        "8ff71f9136c0a185"
                    ),
                    "e16_actor_data": (
                        "017e3a25acfc41e687ad0bc97c24c2347191dc952b0d826d"
                        "4bfb9bb4ec14efe7"
                    ),
                },
                "preservation": {
                    "field_variables": True,
                    "fei_party_gamestate_camera_windows": True,
                    "all_unrelated_actor_runtime": True,
                    "resident_archive_table_rebuilt_for_v229": True,
                    "v228_v229_media_archive_tables_identical": True,
                    "resident_archive_volatile_tail": True,
                    "allocator_safe": True,
                    "round_trip_verified": True,
                },
                "policy": (
                    "apply only to the exact V228 field-549 Classification "
                    "Archive Slot 1 identity; validate the byte-identical V229 "
                    "media archive table while preserving its volatile resident "
                    "tail, patch only the resident field-549 entity-16 seal "
                    "operand from 0x0E to 0x08 and its loaded runtime radius low "
                    "byte from 0x1C to 0x10, and preserve Fei, party, GameState, "
                    "field variables, camera, windows, and every unrelated actor "
                    "byte; every other state must cold-load field 549 from V229 media"
                ),
            },
        }
        self.assertEqual(plan["historical_releases"]["v229"], expected_v229)
        expected_v230 = {
            **expected_v229,
            "version": 230,
            "bin": {
                "path": (
                    "output/"
                    "Xenogears_PW_CD2_mass_driver_surface_soylent_v230.bin"
                ),
                "size": 698814480,
                "sha256": (
                    "140921144d691e81ed1d7f7340bef3c45a1753d18f5be9c81"
                    "db5f8b0c7e1c79e"
                ),
            },
            "cue": {
                "path": (
                    "output/"
                    "Xenogears_PW_CD2_mass_driver_surface_soylent_v230.cue"
                ),
                "size": 112,
                "sha256": (
                    "c3dc7220ce01a0f55457d8e2652f7c54a235adfa5baafdd1"
                    "0a18503a2bcfbf3a"
                ),
            },
            "repeat_manifest": {
                "path": "work/v230r_stage/manifest.json",
                "size": 129959,
                "sha256": (
                    "9a8be0713439ad4c140ac0a8ab43f950555305e897fc087f"
                    "f4aea204c16d9d07"
                ),
            },
            "field_549": {
                "bundle": {
                    "size": 23332,
                    "sha256": (
                        "8bdb39fab5c1e7dbd201c0f0d53368c3a754d36bf698fa71"
                        "7558202852bdeefe"
                    ),
                },
                "script": {
                    "size": 3841,
                    "sha256": (
                        "2dd2804d33004a52b66e676adb3ba9d978532ad21c80ca6d"
                        "a4d84f9ba1e3c999"
                    ),
                },
                "dialogue": expected_v229["field_549"]["dialogue"],
                "archive_return_seal": {
                    "entity": 16,
                    "center": [-244, 248],
                    "radius_script_units": 8,
                    "effective_player_contact_radius": 32,
                    "southwest_ray_clearance_world_units": 5.639441995778888,
                    "closed_cut_triangles": [6, 10, 11, 12, 13],
                },
                "archive_return_x": {
                    "entity": 6,
                    "script": 2,
                    "center": [-240, 240],
                    "effective_half_extents_world_units": [36, 40],
                    "automatic_proximity_action": False,
                },
            },
            "migration": {
                "source": {
                    "path": (
                        "work/save_candidates/"
                        "SLUS-00669_1_v229_roundtrip_stuck_09d68876.sav"
                    ),
                    "size": 1615526,
                    "sha256": (
                        "09d68876b0c2ebf50f2b130d97f26bc6b8bd242aa84c154e"
                        "96f8ef9e7ae17e5c"
                    ),
                },
                "candidate": {
                    "path": (
                        "work/save_candidates/"
                        "SLUS-00669_1_v230_from_09d68876_field549_shifted_seal.sav"
                    ),
                    "size": 1466492,
                    "sha256": (
                        "36e5bbaf509f9cdeb4c86a3555175c5dd880002d9964eb73"
                        "cf7cf69f4bfc070e"
                    ),
                },
                "report": {
                    "path": (
                        "work/save_candidates/"
                        "SLUS-00669_1_v230_from_09d68876_field549_shifted_seal.json"
                    ),
                    "size": 2496,
                    "sha256": (
                        "ca74e80180a9c7dfcebbe45b8105d95b40cd59e3b0d70442"
                        "bec023e094520504"
                    ),
                },
                "decompressed_payload": {
                    "size": 3819109,
                    "sha256": (
                        "7cd05bcf4fc79c7d204812a9c6c42c6371da5cdf5f17033b"
                        "dfae824318a1dc6c"
                    ),
                    "bytes_changed": 7,
                    "changed_offsets": [
                        "0x148DE",
                        "0x10C73A",
                        "0x10C73C",
                        "0x112180",
                        "0x112188",
                        "0x1EF676",
                        "0x1EF67A",
                    ],
                    "breakdown": {
                        "archive_table": 1,
                        "resident_script_position": 2,
                        "runtime_e16_position": 2,
                        "cached_header_position": 2,
                    },
                },
                "compressed_payload": {
                    "size": 1419163,
                    "sha256": (
                        "e3e765712039941a0e484c40f90590bb7b8be91c7355d7af"
                        "625591e90a789ca8"
                    ),
                },
                "resident_hashes": {
                    "ram": (
                        "f092899a0be6915cc83ababb133daf1c527c8f92ef6a1f27"
                        "552452130e1541b9"
                    ),
                    "archive_table": (
                        "ad54b3917aaa84e84eabb8751a56df8a3311b708fc2da1fd"
                        "690b4011068206c4"
                    ),
                    "field_549_script": (
                        "2dd2804d33004a52b66e676adb3ba9d978532ad21c80ca6d"
                        "a4d84f9ba1e3c999"
                    ),
                    "cached_header": (
                        "f842bd2febf7f2c21d5ea63cefeafe065a19e063ae8665fa"
                        "400ef907cac84698"
                    ),
                    "prepared_media_header": (
                        "27432b47d36a1d08438aa843146bfeccbae0efbd0370167c"
                        "cbf00871a9914a21"
                    ),
                    "e16_actor_data": (
                        "89b3816fce60b16c13e220c55b92ad4f35c209dd0a5c535"
                        "942ccff8ca3f6a159"
                    ),
                },
                "preservation": {
                    "field_variables": True,
                    "fei_party_gamestate_camera_windows": True,
                    "all_unrelated_actor_runtime": True,
                    "resident_archive_table_rebuilt_for_v230": True,
                    "v229_v230_media_archive_table_bytes_changed": 1,
                    "resident_archive_volatile_tail": True,
                    "resident_cached_header_keeps_v229_component_offsets": True,
                    "runtime_e16_collision_volume": True,
                    "allocator_safe": True,
                    "round_trip_verified": True,
                },
                "policy": (
                    "apply only to the exact V229 field-549 returning Slot 1 "
                    "identity; rebuild the resident archive table from V230 "
                    "while preserving its volatile tail, patch only e16's two "
                    "resident ATEL coordinate bytes, two live ActorData "
                    "coordinate bytes, and two cached-header coordinate bytes, "
                    "retain the cached V229 component offsets rather than "
                    "copying V230 media offsets into the allocated heap, and "
                    "preserve Fei, party, GameState, field variables, camera, "
                    "windows, collision volume, and every unrelated actor byte; "
                    "every other state must cold-load field 549 from V230 media"
                ),
            },
        }
        self.assertEqual(plan["historical_releases"]["v230"], expected_v230)

        v232_campaign_patient_identities = {
            591: {
                "bundle": (
                    63_640,
                    "bb852caeac217e5ab0d5c26fbd9ebbfb6caf21f6c21a6479"
                    "8022a6cee5e89297",
                ),
                "script": (
                    3_455,
                    "c7f7fbc7bd5a82b006e6e351121dde668f15ec167f66d47b"
                    "6ac4c31df1dc71a1",
                ),
            },
            592: {
                "bundle": (
                    64_184,
                    "9398ec12f0164f543321c14e40dbcd9c156403b33c245bd7"
                    "07b1d22442ff65df",
                ),
                "script": (
                    3_455,
                    "429ad93c0fd8becd2b9fa456507d1f5fd586c323badf4061"
                    "1bf2f3d07a4df2d4",
                ),
            },
            593: {
                "bundle": (
                    69_676,
                    "e60e85c8f0bc6225adb78b4c25fabf9411520f32610bf6fe"
                    "926e85f7253e50e1",
                ),
                "script": (
                    3_515,
                    "8669b5754be76c7928026bfc40e8e84e4ae0a1797dfef802"
                    "f06a2b0756c43785",
                ),
            },
            594: {
                "bundle": (
                    72_116,
                    "194613b51b0e7b30140f7181d8a3779f612c6cfb4c7a8b4b"
                    "d38699ea5226669b",
                ),
                "script": (
                    3_453,
                    "637b1c0d04691b2dd3e693607d5e007cec4b259e59434bff"
                    "09ad278e2f3771d1",
                ),
            },
        }
        expected_occupied_patient_records = {
            "policy": (
                "each occupied field-352 treatment room has one repeatable, "
                "read-only two-page diagnostic record for the demihuman patient "
                "beside its bed; field 593's one-time Quarantine-keycard prompt "
                "remains before its post-acquisition record"
            ),
            "terminal_interaction": {
                "static_model_index": 3,
                "source_header_node": 22,
                "authored_header_node": 23,
                "model_size": 1_436,
                "model_sha256": (
                    "bc7ed77986a3133bed3e6f3de6d4b7c59ca4f92c4ef45f6"
                    "9130bef34946baa28"
                ),
                "carrier_entities": [19, 4, 5],
                "positions": [[80, -167], [116, -167], [152, -167]],
                "triangles": [31, 6, 6],
                "half_extents_script_units": [1, 15],
                "effective_half_reach_world_units": [18, 46],
                "requires_facing": True,
                "init_facing_opcode": "F8 03 04 00",
                "saved_slot_1_rejected": {
                    "field": 593,
                    "position": [75.00785827636719, -77.75068664550781],
                    "triangle": 8,
                    "yaw": "0x0400",
                },
                "frontage_proof": {
                    "reachable_points": 1_201,
                    "workstation_yaw": "0x0400",
                    "bed_yaw": "0x0800",
                    "bed_yaw_accepted_points": 0,
                },
            },
            **{
                str(scene): {
                    "dialogue_id": (
                        exam_rooms.PATIENT_RECORD_DIALOGUE_IDS_BY_SCENE[scene]
                    ),
                    "patient_id": (
                        exam_rooms.PATIENT_RECORD_DIALOGUES_BY_SCENE[scene]
                        .splitlines()[0]
                        .removeprefix("PATIENT RECORD: ")
                    ),
                    "type": (
                        exam_rooms.PATIENT_RECORD_DIALOGUES_BY_SCENE[scene]
                        .splitlines()[1]
                        .removeprefix("Type: ")
                    ),
                    "bundle": {
                        "size": v232_campaign_patient_identities[scene][
                            "bundle"
                        ][0],
                        "sha256": v232_campaign_patient_identities[scene][
                            "bundle"
                        ][1],
                    },
                    "script": {
                        "size": v232_campaign_patient_identities[scene][
                            "script"
                        ][0],
                        "sha256": v232_campaign_patient_identities[scene][
                            "script"
                        ][1],
                    },
                    "dialogue": {
                        "size": exam_rooms.FINAL_DIALOGUE_IDENTITIES[scene][0],
                        "sha256": exam_rooms.FINAL_DIALOGUE_IDENTITIES[scene][1],
                    },
                }
                for scene in exam_rooms.SCENES
            },
        }
        expected_v232 = {
            **expected_v230,
            "version": 232,
            "bin": {
                "path": (
                    "output/"
                    "Xenogears_PW_CD2_mass_driver_surface_soylent_v232.bin"
                ),
                "size": 698_816_832,
                "sha256": (
                    "8e9020e85760e64555040ea26b73876f0add72a788a32210"
                    "70e4d57823520394"
                ),
            },
            "cue": {
                "path": (
                    "output/"
                    "Xenogears_PW_CD2_mass_driver_surface_soylent_v232.cue"
                ),
                "size": 112,
                "sha256": (
                    "dacbd8033a8ae9ac9c98c9e3918d3de7deb59a5ddb320dcd"
                    "7264438ad59d7647"
                ),
            },
            "repeat_manifest": {
                "path": "work/v232r_stage/manifest.json",
                "size": 135_113,
                "sha256": (
                    "007ef9b6e1863d6ec01b4512303e8b52129da5cf8c454d53"
                    "704fc48a0f6786ea"
                ),
            },
            "field_352_family": {
                "scenes": [550, 567, 591, 592, 593, 594],
                "automatic_forward_poll": False,
                "x_button_required": True,
                "global_update": {
                    "entity": 0,
                    "script": 1,
                    "opcode": "STOP",
                    "pc": "0x068C",
                },
                "retired_automatic_cavity": {
                    "span": ["0x044E", "0x04A5"],
                    "size": 87,
                    "sha256": (
                        "85581a31b32134e75912714f1e71cbe0957721e289f114f9"
                        "54a98ed7c4ca8824"
                    ),
                    "byte_identical_scenes": [550, 567],
                    "side_terminal_carrier_scenes": [591, 592, 593, 594],
                    "side_terminal_init_entry_points": [
                        {"entity": 4, "script": 0, "pc": "0x044E"},
                        {"entity": 5, "script": 0, "pc": "0x046B"},
                    ],
                    "other_active_entry_points": 0,
                },
                "seal_center": [0, 266],
                "seal_half_extents_script_units": [24, 8],
                "walkmesh_size": 1948,
                "walkmesh_sha256": (
                    "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d"
                    "8cca4238393571df"
                ),
            },
            "occupied_patient_records": expected_occupied_patient_records,
            "migration": {
                "source": {
                    "path": (
                        "work/save_candidates/"
                        "SLUS-00669_1_v231_field593_terminal_proximity_6adde32f.sav"
                    ),
                    "size": 1_839_559,
                    "sha256": (
                        "6adde32f8351a7e6201bb6d40dafc7b11d00910bf13f3306"
                        "6a905549047fbe48"
                    ),
                },
                "candidate": {
                    "path": (
                        "work/save_candidates/"
                        "SLUS-00669_1_v232_from_6adde32f_"
                        "field593_terminal_proximity.sav"
                    ),
                    "size": 1_661_998,
                    "sha256": (
                        "eae5680680e2a197d2333524ce254483cd921b8f12bfab4b"
                        "325ac2b9269be45f"
                    ),
                },
                "report": {
                    "path": (
                        "work/save_candidates/"
                        "SLUS-00669_1_v232_from_6adde32f_"
                        "field593_terminal_proximity.json"
                    ),
                    "size": 3_913,
                    "sha256": (
                        "bdaa558f721cbd720ee5682f37adc8db28a2bd0d84931790"
                        "92e25af62a178858"
                    ),
                },
                "decompressed_payload": {
                    "size": 3_819_109,
                    "sha256": (
                        "87e80394311c328302d8ec21f6526129f3c42cb5f1a3902d"
                        "1b7a0be2aa7d17b1"
                    ),
                    "bytes_changed": 112,
                    "triplet_sha256": (
                        "7abe4ec67aa7cb8a61365df698ab1c35c4d8282f952668a6"
                        "f407793c3fce47d1"
                    ),
                    "breakdown": {
                        "archive_table": 4,
                        "resident_script": 84,
                        "resident_cached_header": 1,
                        "terminal_runtime": 23,
                    },
                },
                "compressed_payload": {
                    "size": 1_620_309,
                    "sha256": (
                        "7632b5c01a7165092b70195573938288448ab441939b98270"
                        "aff4eb9c6adc701"
                    ),
                },
                "resident_hashes": {
                    "ram": (
                        "a11ad580783f9940f467d7992eeed01bc34c309277d970cb"
                        "cbf0f8b58ddea00c"
                    ),
                    "archive_table": (
                        "194ecb959cc2af747bc3286f28dc1a54b07c33beb714183e"
                        "ea4938764a1ec2c6"
                    ),
                    "field_593_script": (
                        "8669b5754be76c7928026bfc40e8e84e4ae0a1797dfef802"
                        "f06a2b0756c43785"
                    ),
                    "field_593_header_hybrid": (
                        "fda02b034ab1c11419710906c4ee3e114c95c62a0ee84582"
                        "be135848e51feba6"
                    ),
                    "prepared_media_header": (
                        "eb74bc65af5847bca1b039064a61c7398e2b1013c5c739d9"
                        "13d7edb024308108"
                    ),
                    "dialogue": (
                        "92d7f6d9ab86a53e8cabd300bc7bb84d8bbb04142f9aa9c4"
                        "f91a9bd5578b828e"
                    ),
                    "walkmesh": (
                        "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d"
                        "8cca4238393571df"
                    ),
                },
                "resident_terminal_projection": {
                    "entities": [19, 4, 5],
                    "positions": [[80, -167], [116, -167], [152, -167]],
                    "triangles": [31, 6, 6],
                    "half_extents_script_units": [1, 15],
                    "requires_facing": True,
                    "shared_action_pc": "0x06E0",
                    "queued_initializers": {"e4": "0x044E", "e5": "0x046B"},
                    "primary_runtime_bytes_changed": 9,
                    "auxiliary_runtime_bytes_changed": 14,
                    "old_aisle_carrier_disabled": True,
                },
                "preservation": {
                    "field_variables": True,
                    "fei_party_gamestate_camera": True,
                    "patient_doctor_and_unrelated_actor_state": True,
                    "dialogue_and_windows": True,
                    "security_and_quarantine_keycards": True,
                    "resident_component_sizes": True,
                    "resident_v231_packed_stream_offsets": True,
                    "resident_archive_volatile_tail": True,
                    "allocator_safe": True,
                    "round_trip_verified": True,
                },
                "policy": (
                    "apply only to the exact V231 field-593 Save 1 identity; "
                    "rebuild the resident archive table for V232 while preserving "
                    "its volatile tail, install V232's equal-size resident ATEL, "
                    "preserve the live V231 packed-stream offsets and patch only "
                    "e19's cached-header Z coordinate, directly normalize the "
                    "stopped e19 carrier, queue dormant e4/e5 through their new "
                    "initializers, and preserve Fei's exact saved aisle stance, "
                    "party, GameState, field variables, camera, keycards, dialogue, "
                    "windows, patient, doctor, every unrelated actor, component "
                    "boundaries, and heap neighbors; a cold field reload uses the "
                    "ordinary V232 header and scripts"
                ),
            },
        }
        current = plan["current_release"]
        self.assertEqual(current["version"], 233)
        self.assertEqual(
            current["bin"],
            {
                "path": (
                    "output/"
                    "Xenogears_PW_CD2_mass_driver_surface_soylent_v233.bin"
                ),
                "size": 698_816_832,
                "sha256": (
                    "f50fa064e8d466bde46e0946a4c1ea7dc556a6a94d85f463"
                    "2de201934318a72b"
                ),
            },
        )
        self.assertEqual(
            current["cue"],
            {
                "path": (
                    "output/"
                    "Xenogears_PW_CD2_mass_driver_surface_soylent_v233.cue"
                ),
                "size": 112,
                "sha256": (
                    "106149772cdd6b12a460be98858e59d268fb1e01008d12b81"
                    "f3eda80dd04ca28"
                ),
            },
        )
        self.assertEqual(
            current["repeat_manifest"],
            {
                "path": "work/v233r_stage/manifest.json",
                "size": 136_361,
                "sha256": (
                    "b79d7a866ba29ad9a5f488bf6e004310f5a5a2c32ed73aaf"
                    "676eee3154ac4d1a"
                ),
            },
        )
        for retained_key in (
            "field_549",
            "field_550",
            "retained_field_621",
            "occupied_patient_records",
            "migration",
        ):
            with self.subTest(retained_v232_contract=retained_key):
                self.assertEqual(current[retained_key], expected_v232[retained_key])
        self.assertEqual(
            current["field_567"],
            {
                "bundle": {
                    "size": 83_548,
                    "sha256": (
                        "6f4be9fa9932c77094b2ff09875ee5a035e145662efd83ba"
                        "50b1b879d5c36999"
                    ),
                },
                "script": {
                    "size": 3_281,
                    "sha256": (
                        "24eb53d1aaa10678f2815cf5fe89e80455c592319d6d6971"
                        "2932f4941793790d"
                    ),
                },
                "header": {
                    "size": 944,
                    "sha256": (
                        "daa0e99244adbe653367a2257024add96d21d40af973c879"
                        "e2c18a2bebb925b9"
                    ),
                },
                "dialogue": {
                    "size": 5_232,
                    "sha256": (
                        "2f15ffdeda92ec407a983737cd0acf550856725718b4fb6a"
                        "05df046e47f2d8fd"
                    ),
                },
                "walkmesh": {
                    "size": 1_948,
                    "sha256": (
                        "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8"
                        "d8cca4238393571df"
                    ),
                },
                "terminal": {
                    "carrier_entities": [4, 5, 6],
                    "init_pcs": [0x044E, 0x046B, 0x06B5],
                    "action_pc": 0x06D2,
                    "dialogue_id": 53,
                    "positions": [[80, -167], [116, -167], [152, -167]],
                    "triangles": [31, 6, 6],
                    "half_extents_script_units": [1, 15],
                    "effective_half_reach_world_units": [18, 46],
                    "requires_facing": True,
                    "repeatable": True,
                    "read_only": True,
                    "writes_state": False,
                    "doctor": None,
                    "patient": None,
                    "text": (
                        "PATIENT RECORD\nNo patient is loaded\n"
                        "for this room.<Close>"
                    ),
                },
            },
        )
        migration_v233 = current["v232_to_v233_migration"]
        self.assertEqual(
            migration_v233["source"],
            {
                "path": (
                    "work/save_backups/"
                    "SLUS-00669_1_v232_field567_empty_terminal_3f09a8ce.sav"
                ),
                "size": 1_607_991,
                "sha256": (
                    "3f09a8cea70ce09c87b2bc0892ad8e427cc90d7fcf1759b8"
                    "677413927c20b022"
                ),
            },
        )
        self.assertEqual(
            migration_v233["candidate"],
            {
                "path": (
                    "work/save_candidates/"
                    "SLUS-00669_1_v233_from_3f09a8ce_"
                    "field567_empty_terminal_native_init.sav"
                ),
                "size": 1_457_268,
                "sha256": (
                    "b9b41cbc756300f6567a7c1cdc6b304e44bc57e025f1a4a5"
                    "1ff74aae84742acf"
                ),
            },
        )
        self.assertEqual(
            migration_v233["decompressed_payload"]["breakdown"],
            {
                "archive_table": 1,
                "resident_script": 127,
                "relocated_dialogue": 307,
                "terminal_scheduler": 21,
            },
        )
        self.assertEqual(
            migration_v233["resident_terminal_projection"]["entities"],
            [4, 5, 6],
        )
        self.assertTrue(
            migration_v233["resident_terminal_projection"][
                "saved_stance_is_within_terminal_reach"
            ]
        )
        self.assertTrue(migration_v233["preservation"]["allocator_safe"])
        self.assertTrue(migration_v233["preservation"]["round_trip_verified"])
        family = current["field_352_family"]
        self.assertEqual(family["scenes"], [550, 567, 591, 592, 593, 594])
        self.assertEqual(
            family["retired_automatic_cavity"],
            {
                "span": ["0x044E", "0x04A5"],
                "size": 87,
                "source_sha256": (
                    "85581a31b32134e75912714f1e71cbe0957721e289f114f9"
                    "54a98ed7c4ca8824"
                ),
                "empty_room_sha256": (
                    "dd87cc07ee6313fe77431e34af52c9158d41a59498f9abf"
                    "056013feac490a400"
                ),
                "byte_identical_scenes": [550],
                "side_terminal_carrier_scenes": [567, 591, 592, 593, 594],
                "side_terminal_init_entry_points": [
                    {"entity": 4, "script": 0, "pc": "0x044E"},
                    {"entity": 5, "script": 0, "pc": "0x046B"},
                ],
                "field567_third_carrier": {
                    "entity": 6,
                    "script": 0,
                    "pc": "0x06B5",
                },
                "other_active_entry_points": 0,
            },
        )
        self.assertEqual(
            plan["historical_releases"]["v224"],
            {
                "version": 224,
                "bin": {
                    "path": (
                        "output/"
                        "Xenogears_PW_CD2_mass_driver_surface_soylent_v224.bin"
                    ),
                    "size": 698642784,
                    "sha256": (
                        "6d0854e878f677eee7e8c57fd5084d0f28b9cc776b758934"
                        "925ef353da30022d"
                    ),
                },
                "cue": {
                    "path": (
                        "output/"
                        "Xenogears_PW_CD2_mass_driver_surface_soylent_v224.cue"
                    ),
                    "size": 112,
                    "sha256": (
                        "4cd7c8be1096148c00d619f776754e6e15cf55dffcc9a3cc"
                        "97b8887af333944d"
                    ),
                },
                "repeat_manifest": {
                    "path": "work/v224r_stage/manifest.json",
                    "size": 119788,
                    "sha256": (
                        "9296f347064f271df10370feb5c433baa49093b717c58fa37"
                        "4a0bca1cb2fae91"
                    ),
                },
                "field_621": {
                    "bundle": {
                        "size": 135648,
                        "sha256": (
                            "011be9593a2c565e6c3bb5f325ef64ac47811592794945ce5"
                            "29fcb3b6eb36677"
                        ),
                    },
                    "script": {
                        "size": 10895,
                        "sha256": (
                            "a362a56e04f91240e4209cb93cdb36a63c31d57bdf2e03c2"
                            "5fca52f202845ea7"
                        ),
                    },
                    "header": {
                        "size": 1408,
                        "sha256": (
                            "bd8be9feef57bff074c81c885d66b329ed20456e42d3a11c"
                            "6b8e03b18550598f"
                        ),
                    },
                },
                "migration": {
                    "source": {
                        "path": (
                            "work/save_backups/"
                            "SLUS-00669_1_v223_persistent_bottom_left_clip_"
                            "b9624646.sav"
                        ),
                        "size": 1672493,
                        "sha256": (
                            "b962464676e5c2b9a59918a5b9247d5d747276ab6ec0fc4a"
                            "36c1f5f48ae96d24"
                        ),
                    },
                    "candidate": {
                        "path": (
                            "work/save_candidates/"
                            "SLUS-00669_1_v224_from_b9624646_single_"
                            "threshold_quad.sav"
                        ),
                        "size": 1513683,
                        "sha256": (
                            "fab19182ff32d0ec0e25f8ef334f1e3604ee407dea29fcf18"
                            "0c3cd2dd14156bb"
                        ),
                    },
                    "report": {
                        "path": (
                            "work/save_candidates/"
                            "SLUS-00669_1_v224_from_b9624646_single_"
                            "threshold_quad.json"
                        ),
                        "size": 1655,
                        "sha256": (
                            "06d409e29b2f2dd6aba2b761b0c39e721a1eb16bbe82e007"
                            "b9d674e1eb858317"
                        ),
                    },
                    "decompressed_payload": {
                        "size": 3819109,
                        "sha256": (
                            "b74fea8bf8be9d12394afe99afb9ed0c21f6451b273c8c6d"
                            "94cdff4a412971b3"
                        ),
                        "bytes_changed": 418,
                        "breakdown": {
                            "model20_topology": 38,
                            "six_packet_arenas": 380,
                            "packet_arena_diff_counts": [67, 65, 62, 62, 62, 62],
                            "resident_archive_table": 0,
                        },
                    },
                    "resident_hashes": {
                        "ram": (
                            "b2a4cd510c004f7b6ed4b9934f2f8098d56f58bc87768ef1"
                            "79854e9793662a53"
                        ),
                        "model20": (
                            "af389e6da468c4a5875d2bd4271574654a34fcd2ca6f62e23"
                            "5771fddfc03c03d"
                        ),
                        "packet_arena": (
                            "3c03f04c72c2424d4a5faa272ef4d8e855dd647360b00e21"
                            "0bcbe02f6e0bd508"
                        ),
                        "packet_arenas": (
                            "5574ecb24ef25954a3ecb136ea9def40b82e94d4de4927f9c"
                            "1e552d2bab13680"
                        ),
                        "archive_table": (
                            "3eacc1ac53db105f07c987a3eeb20cfbbca9df9fefe21a8c7"
                            "a4c4750e14dfba0"
                        ),
                    },
                    "preservation": {
                        "model20_allocation": True,
                        "packet_arena_allocations": True,
                        "packet_arenas_reinitialized_for_topology": True,
                        "field_header": True,
                        "scripts": True,
                        "actors": True,
                        "collision": True,
                        "player": True,
                        "camera": True,
                        "game_state": True,
                        "dialogue": True,
                        "walkmesh": True,
                        "resident_archive_table": True,
                        "round_trip_verified": True,
                    },
                    "policy": (
                        "apply only to the exact V223 persistent-bottom-left-"
                        "clipping Slot 1 identity; every other state must "
                        "cold-load field 621 from V224 media"
                    ),
                },
            },
        )
        self.assertEqual(
            plan["historical_releases"]["v221"],
            {
                "version": 221,
                "bin": {
                    "path": (
                        "output/"
                        "Xenogears_PW_CD2_mass_driver_surface_soylent_v221.bin"
                    ),
                    "size": 698642784,
                    "sha256": (
                        "577519db3fb4228c17f0555466866b271c265587a5fdc015"
                        "15d9ff3f78f6827a"
                    ),
                },
                "cue": {
                    "path": (
                        "output/"
                        "Xenogears_PW_CD2_mass_driver_surface_soylent_v221.cue"
                    ),
                    "size": 112,
                    "sha256": (
                        "a4134fcf3f5bee22530aa90aed6cd691a29983483eb843882"
                        "8af5caa30ba1163"
                    ),
                },
                "repeat_manifest": {
                    "path": "work/v221r_stage/manifest.json",
                    "size": 119665,
                    "sha256": (
                        "ff8acf4b520034bc401dd8c88d7d051a5c90f4169b38d206"
                        "48e0efea780e25b1"
                    ),
                },
                "migration": {
                    "source": {
                        "size": 1679306,
                        "sha256": (
                            "e4aea385a822c19b74040bb442c1766ad122be1a95009a24"
                            "d9bec51429198c54"
                        ),
                    },
                    "candidate": {
                        "path": (
                            "work/save_candidates/"
                            "SLUS-00669_1_v221_from_e4aea385_"
                            "native_threshold_aprons.sav"
                        ),
                        "size": 1521337,
                        "sha256": (
                            "27710b20903e4eb6be1c818b3e3aaf8bf4050c7cc709575a"
                            "73f5c2fb7f9d3581"
                        ),
                    },
                    "decompressed_payload": {
                        "size": 3819109,
                        "sha256": (
                            "88525715b23bc3c13c1c39b1e25d9d06cb7772cd02560a92"
                            "34d0ca722e97a816"
                        ),
                        "bytes_changed": 1025,
                        "breakdown": {
                            "archive_table": 1,
                            "model20": 113,
                            "six_packet_arenas": 911,
                        },
                    },
                    "resident_hashes": {
                        "archive_table": (
                            "3eacc1ac53db105f07c987a3eeb20cfbbca9df9fefe21a8c"
                            "7a4c4750e14dfba0"
                        ),
                        "model2": (
                            "749800fc048b59c2e89028b558846f375f9009ff01e0c2a0"
                            "cc2bcf2b07857ba8"
                        ),
                        "model20": (
                            "81b45178684dbd87fcaf71c4cba3f43bccb2932106aa2245"
                            "fa2048303f0cb8bb"
                        ),
                        "packet_arenas": (
                            "8225f199051718510efad5f75e8a69ecc58a8a283f043eaf"
                            "a16b2c3235553d7e"
                        ),
                    },
                    "preservation": {
                        "actor_header_game_camera_script_collision": True,
                        "model2": True,
                        "model20_allocation": True,
                        "packet_arena_allocations": True,
                        "volatile_archive_table_byte": True,
                        "packet_arenas_reinitialized_for_topology": True,
                        "round_trip_verified": True,
                    },
                    "policy": (
                        "apply only to the exact source identity; every other "
                        "state must cold-load field 621 from V221 media"
                    ),
                },
            },
        )
        self.assertEqual(
            plan["implementation_invariants"]["field352_exam_room_doorways"],
            {
                "version": 226,
                "fields": [550, 567, 591, 592, 593, 594],
                "collision": "aperture-aligned thin rectangular seal",
                "automatic_entry": False,
                "interaction": (
                    "one fresh deliberate X press on the unchanged broad carrier "
                    "is required to invoke the native door action"
                ),
                "controller_update": (
                    "entity 0 script 1 resolves to the shared STOP and the "
                    "retired field-352 cavity has no active entry point"
                ),
                "walkmesh": "the retail field-352 walkmesh remains byte-identical",
                "policy": (
                    "the seal blocks only the physical doorway aperture instead "
                    "of clipping Fei against an oversized radial volume; Forward "
                    "alone cannot open a leaf or display doctor-office dialogue, "
                    "while a fresh X press reaches the unchanged native animated-"
                    "door action"
                ),
            },
        )
        doors = {pair["id"]: pair for pair in plan["door_pairs"]}
        self.assertEqual(
            {
                pair_id: doors[pair_id]["gate"]
                for pair_id in (
                    "intake_service_patient",
                    "intake_treatment_preparation",
                    "intake_exam_a",
                    "intake_exam_b",
                    "intake_exam_c",
                )
            },
            {
                "intake_service_patient": "security_keycard",
                "intake_treatment_preparation": "security_keycard",
                "intake_exam_a": "security_keycard",
                "intake_exam_b": "security_keycard",
                "intake_exam_c": "security_keycard",
            },
        )
        self.assertEqual(
            (
                doors["intake_treatment_preparation"]["a"],
                doors["intake_treatment_preparation"]["b"],
            ),
            ("621/p5", "594/p0"),
        )
        self.assertNotIn(
            "565/p3",
            {
                endpoint
                for pair in plan["door_pairs"]
                for endpoint in (pair["a"], pair["b"])
            },
        )
        self.assertEqual(
            plan["implementation_invariants"]["intake_treatment_preparation"],
            {
                "version": 232,
                "field": 621,
                "entity": 26,
                "slot_1_marker": {"position": [1645, 396], "facing": "west"},
                "route": {
                    "pair": "intake_treatment_preparation",
                    "local_entry": 5,
                    "destination": [594, 0],
                },
                "dialogue": "The door is locked. A security keycard is required.",
                "unlock_trigger": (
                    "security_keycard at operand 0x021A bit 0, awarded only after "
                    "victory over the field-550 security team"
                ),
                "room": {
                    "field": 594,
                    "source_field": 352,
                    "source_resources": [1315, 1316],
                    "target_resources": [1794, 1795],
                    "entry_parameter": 0,
                    "role": "bright Solaris treatment-preparation room",
                    "return": {
                        "entity": 17,
                        "helper": 18,
                        "destination": [621, 5],
                    },
                    "terminal": {
                        "entities": [19, 4, 5],
                        "model_index": 3,
                        "positions": [[80, -167], [116, -167], [152, -167]],
                        "triangles": [31, 6, 6],
                        "half_extents_script_units": [1, 15],
                        "effective_half_reach_world_units": [18, 46],
                        "requires_facing": True,
                        "interaction": "repeatable read-only X interaction",
                        "cross_release_drains": 2,
                        "dialogue": (
                            exam_rooms.PATIENT_RECORD_DIALOGUES_BY_SCENE[594]
                        ),
                        "writes_progression": False,
                    },
                    "encounters": "disabled",
                },
                "retired_handoff": {
                    "field": 565,
                    "entity": 7,
                    "local_entry": 3,
                    "state": "sealed and dormant",
                    "destination": None,
                    "role": "reserved future laboratory handoff",
                },
                "policy": (
                    "before the keycard, deny access without playing the door sound "
                    "or opening the leaf; after the keycard, run the preserved sound "
                    "and leaf-helper call, then enter the self-contained field-594 "
                    "treatment room; its native entity-17 exit returns only to field "
                    "621/p5, and this Intake door never exposes field 565 or Krelian's Lab"
                ),
            },
        )
        self.assertEqual(
            (
                doors["service_interface_annex"]["a"],
                doors["service_interface_annex"]["b"],
            ),
            ("565/p5", "588/p0"),
        )
        self.assertEqual(
            {
                pair_id: (doors[pair_id]["a"], doors[pair_id]["b"])
                for pair_id in ("intake_exam_a", "intake_exam_b", "intake_exam_c")
            },
            {
                "intake_exam_a": ("621/p7", "591/p0"),
                "intake_exam_b": ("621/p8", "592/p0"),
                "intake_exam_c": ("621/p9", "593/p0"),
            },
        )
        office_terminal = plan["intake_checkin"]["appointment"][
            "office_terminal"
        ]
        self.assertEqual(
            {
                "version": office_terminal["version"],
                "static": (
                    office_terminal["static_node"],
                    office_terminal["static_model"],
                ),
                "carriers": office_terminal["carrier_entities"],
                "positions": office_terminal["operator_positions"],
                "operator_triangles": office_terminal["operator_triangles"],
                "runtime_carrier_triangles": office_terminal[
                    "runtime_carrier_triangles"
                ],
                "requires_facing": office_terminal["requires_facing"],
                "compatibility": office_terminal["biological_compatibility"],
            },
            {
                "version": 214,
                "static": (27, 3),
                "carriers": [4, 5, 6],
                "positions": [[80, -167], [116, -167], [152, -167]],
                "operator_triangles": [31, 30, 6, 7],
                "runtime_carrier_triangles": [0, 0, 0],
                "requires_facing": True,
                "compatibility": {
                    "index_percent": 100,
                    "classification": "PERFECT FIT",
                    "lore_role": "Sufal Mass integration suitability",
                },
            },
        )
        invariants = plan["implementation_invariants"]
        self.assertEqual(
            invariants["current_content_boundary"]["version"],
            blueprint.CURRENT_CONTENT_BOUNDARY.version,
        )
        self.assertEqual(
            invariants["classification_archive_return_collision"],
            {
                "version": 230,
                "field": 549,
                "controller_entity": 6,
                "physical_seal_entity": 16,
                "center": [-244, 248],
                "action_center": [-240, 240],
                "shape": "rotation-invariant circle",
                "radius_script_units": 8,
                "radius_world_units": 16,
                "effective_player_contact_radius": 32,
                "saved_approach": {
                    "position_fixed": [-12702524, 0, 16007409],
                    "position_world": [
                        -193.82513427734375,
                        0.0,
                        244.25367736816406,
                    ],
                    "triangle": 10,
                },
                "round_trip_saved_approach": {
                    "position_fixed": [-13485612, 0, 15269605],
                    "position_world": [
                        -205.77410888671875,
                        0.0,
                        232.9956817626953,
                    ],
                    "triangle": 10,
                    "yaw": "0x0600",
                    "travel_direction": "southwest (-X,-Z)",
                    "ray_clearance_world_units": 5.639441995778888,
                },
                "closed_cut_triangles": [6, 10, 11, 12, 13],
                "diagonal_seam_intersection_margins_world_units": [
                    12.48625560742041,
                    15.741379398790173,
                ],
                "deliberate_x": {
                    "carrier_entity": 6,
                    "script": 2,
                    "action_half_extents_script_units": [10, 12],
                    "effective_cross_half_extents_world_units": [36, 40],
                    "automatic_proximity_action": False,
                    "required": True,
                },
                "policy": (
                    "keep the shifted circle entirely within deliberate-X reach, "
                    "clear the exact southwest corridor ray, intersect both "
                    "diagonal aperture seams across triangles 6, 10, 11, 12, "
                    "and 13 while closed, and never open from Forward alone"
                ),
            },
        )
        population = invariants["private_treatment_population"]
        self.assertEqual(population["version"], 237)
        self.assertEqual(population["empty_bed_rooms"], [567, 593])
        self.assertEqual(population["occupied_rooms"], [591, 592, 594])
        self.assertEqual(population["entities"], {"patient": 13, "doctor": 16})
        self.assertIn("active NPC assets", population["patient_assets_scope"])
        self.assertEqual(
            [entry["source"] for entry in population["patient_assets"]],
            [[620, 2], [620, 3], [621, 3]],
        )
        self.assertTrue(population["solid_talkable"])
        self.assertTrue(population["mutual_bedside_facing"])
        self.assertIn("unique private-area", population["policy"])
        self.assertIn("hopeful", population["policy"])
        self.assertEqual(invariants["intake_examination_rooms"]["version"], 232)
        self.assertEqual(
            invariants["intake_examination_rooms"]["patient_records"],
            {
                str(scene): {
                    "dialogue_id": (
                        exam_rooms.PATIENT_RECORD_DIALOGUE_IDS_BY_SCENE[scene]
                    ),
                    "text": exam_rooms.PATIENT_RECORD_DIALOGUES_BY_SCENE[scene],
                }
                for scene in (591, 592, 593)
            },
        )
        self.assertEqual(
            invariants["intake_examination_rooms"]["terminal_interaction"],
            {
                "static_model_index": 3,
                "source_header_node": 22,
                "authored_header_node": 23,
                "model_size": 1_436,
                "model_sha256": (
                    "bc7ed77986a3133bed3e6f3de6d4b7c59ca4f92c4ef45f6"
                    "9130bef34946baa28"
                ),
                "carrier_entities": [19, 4, 5],
                "positions": [[80, -167], [116, -167], [152, -167]],
                "triangles": [31, 6, 6],
                "half_extents_script_units": [1, 15],
                "effective_half_reach_world_units": [18, 46],
                "requires_facing": True,
                "saved_slot_1_rejected": {
                    "field": 593,
                    "position": [75.00785827636719, -77.75068664550781],
                    "triangle": 8,
                    "yaw": "0x0400",
                },
                "frontage_proof": {
                    "reachable_points": 1_201,
                    "workstation_yaw": "0x0400",
                    "bed_yaw": "0x0800",
                    "bed_yaw_accepted_points": 0,
                },
            },
        )
        self.assertEqual(
            invariants["intake_examination_rooms"]["doors"],
            [
                {"entity": 43, "helper": 46, "threshold_header_node": 60, "local_entry": 7, "destination": [591, 0], "door_model": 3, "controller": [1650, 1246], "return": [1598, 1194], "model_origin": [3088, 0, 1463], "threshold_placement": [512, 1645, 0, 1307]},
                {"entity": 44, "helper": 47, "threshold_header_node": 61, "local_entry": 8, "destination": [592, 0], "door_model": 6, "controller": [1774, 840], "return": [1720, 840], "model_origin": [1733, 0, 0], "threshold_placement": [1024, 1821, 0, 882]},
                {"entity": 45, "helper": 48, "threshold_header_node": 62, "local_entry": 9, "destination": [593, 0], "door_model": 7, "controller": [1774, 396], "return": [1720, 396], "model_origin": [1733, 0, 0], "threshold_placement": [1024, 1821, 0, 441]},
            ],
        )
        self.assertEqual(
            invariants["intake_examination_rooms"]["native_threshold_source"],
            {
                "field": 621,
                "door_entity": 24,
                "door_model_index": 4,
                "door_model_size": 172,
                "door_model_sha256": (
                    "1c585299d3b1e67826303f5b668ed7cc04eede7f02b65174"
                    "a4134c4ba0ae6e25"
                ),
                "door_plane": {"x": 1645, "z": [793, 882]},
                "apron_model_index": 19,
                "apron_header_node": 59,
                "apron_model_size": 560,
                "apron_model_sha256": (
                    "7d2aab285a01c5561182f1a3db7f6f5eaefc1e806c22ecec"
                    "256413315109a502"
                ),
                "model_counts": {
                    "vertices": 34,
                    "POLY_FT4": 10,
                    "mesh_groups": 1,
                },
                "model_offsets": {
                    "vertices": "0x48",
                    "normals": "0x48",
                    "meshes": "0x158",
                    "display": "0x1AC",
                },
                "gpu_packet_arena": "0x190",
                "primitive": {
                    "type": "POLY_FT4",
                    "ordinal": 4,
                    "dimensions": [89, 44],
                    "vertices": [
                        [1601, 0, 793],
                        [1601, 0, 882],
                        [1645, 0, 882],
                        [1645, 0, 793],
                    ],
                    "indices": [1, 2, 0, 3],
                    "texture_state": ["A8 00 00 C4", "00 79 00 C8"],
                    "packet": "00 00 00 2D B6 95 B6 89 97 95 97 89",
                },
                "proof": (
                    "retail entity 24/model 4 is only the leaf; the short "
                    "visible pathway beyond it is model 19 FT4 ordinal 4, "
                    "retained at shifted header node 59"
                ),
            },
        )
        self.assertEqual(
            invariants["intake_examination_rooms"]["threshold_model"],
            {
                "model_index": 20,
                "size": 396,
                "sha256": (
                    "8ef50d3f377c7b8caf2fdcfa0fcaecebe3d25ce5a51a90df"
                    "a0f14a734fdf3b52"
                ),
                "source": (
                    "one retail model-19 entity-24 apron normalized as one "
                    "whole-width FT4"
                ),
                "counts": {
                    "vertices": 15,
                    "primitives": 15,
                    "mesh_groups": 2,
                },
                "offsets": {
                    "vertices": "0x48",
                    "normals": "0x48",
                    "meshes": "0xC0",
                    "display": "0x140",
                },
                "gpu_packet_arena": "0x140",
                "visible_primitives": {
                    "type": "POLY_FT4",
                    "count": 1,
                    "packets": [
                        "00 00 00 2D 97 89 97 8D B6 89 B6 8D",
                    ],
                },
                "disabled_primitives": {
                    "type": "POLY_F3",
                    "count": 14,
                    "method": "degenerate vertex-index records",
                },
                "local_bounds": {"x": [0, 89], "y": [0, 0], "z": [0, 44]},
                "rendering": (
                    "far-side top-facing floor only; local negative-Z is the "
                    "accessible hall and remains empty, so model 20 shares only "
                    "the aperture edge with model 1's hall floor and has no "
                    "positive-area overlap or vertical near-plane ribbon; the "
                    "retail one-FT4 topology keeps the whole apron behind a "
                    "closed leaf in the PS1 ordering table; the far-depth V "
                    "endpoint remains capped at cyan-shadow row 0x8D before "
                    "the source texture's near-black tail"
                ),
            },
        )
        self.assertEqual(
            invariants["intake_examination_rooms"][
                "historical_v220_inert_reveal_model"
            ],
            {
                "model_index": 20,
                "size": 396,
                "sha256": (
                    "501971ffbbfa09a28c8f3be10f546630cb9ab6cf52b31c3b"
                    "28882679388cbb39"
                ),
                "disabled_primitives": {
                    "type": "POLY_F3",
                    "count": 16,
                    "method": "degenerate vertex-index records",
                },
                "rendering": (
                    "V220 allocation-preserving inert compatibility model "
                    "retained header nodes, placements, model size, counts, "
                    "display layout, and pointers but rendered no finite rear "
                    "surface"
                ),
            },
        )
        self.assertEqual(
            invariants["intake_examination_rooms"]["model_archive"],
            {
                "size": 39292,
                "sha256": (
                    "b06e38c58fcd5e1ce5033e1135f0ae7c7d745b9ef37575f4"
                    "4b0cba4c936c52aa"
                ),
            },
        )
        self.assertEqual(
            invariants["intake_examination_rooms"]["field_bundle"],
            {
                "size": 135648,
                "sha256": (
                    "011be9593a2c565e6c3bb5f325ef64ac47811592794945ce5"
                    "29fcb3b6eb36677"
                ),
            },
        )
        self.assertEqual(
            invariants["intake_examination_rooms"]["script"],
            {
                "size": 10895,
                "sha256": (
                    "a362a56e04f91240e4209cb93cdb36a63c31d57bdf2e03c2"
                    "5fca52f202845ea7"
                ),
            },
        )
        self.assertEqual(
            invariants["intake_examination_rooms"]["header"],
            {
                "size": 1408,
                "sha256": (
                    "bc016d4404b7cd5f31a4eb7aac91315b594152ca17ea64010"
                    "4bc6f8fdc4790df"
                ),
            },
        )
        self.assertEqual(
            invariants["intake_examination_rooms"]["camera_occluder_model"],
            {
                "model_index": 2,
                "size": 4836,
                "native_sha256": "b093460d49974a083f191442a2aaafb75983da7ed5ad78201b3d46f5b4b2bdd3",
                "sha256": "2d0b40fb67720162fe93bb3fa522d33c3cf3db8333865f3f8d7c897688fad5d3",
                "disabled_groups": [0, 2],
                "disabled_primitives": {"POLY_F3": 4, "POLY_F4": 134},
                "preserved_groups": [1, 3],
                "rendering": (
                    "native flat-black corner-cap and ceiling-fascia index "
                    "records are degenerate; textured shell groups, packets, "
                    "counts, offsets, pointers, allocation, and collision remain"
                ),
            },
        )
        self.assertEqual(
            invariants["quarantine_keycard_terminal"]["field"], 593
        )
        self.assertEqual(
            invariants["quarantine_keycard_terminal"]["entities"], [19, 4, 5]
        )
        self.assertEqual(
            invariants["quarantine_keycard_terminal"]["positions"],
            [[80, -167], [116, -167], [152, -167]],
        )
        self.assertEqual(
            invariants["interface_cutoff_scanner"]["awards"],
            ["bio-interface cutoff armed at operand 0x03FA bit 11"],
        )
        self.assertEqual(
            doors["intake_quarantine"]["gate"],
            "quarantine_keycard",
        )
        self.assertIn(
            "finale_epilogue_pending",
            plan["persistent_state"]["03FA_bit10"],
        )
        physician = plan["implementation_invariants"]["physician_collision"]
        self.assertEqual(
            {
                "version": physician["version"],
                "lobby": (physician["lobby"]["field"], physician["lobby"]["entity"]),
                "office": (physician["office"]["field"], physician["office"]["entity"]),
                "runtime_half_extents": physician["runtime_half_extents"],
                "transit_flags_opcode": physician["transit_flags_opcode"],
                "stationary_flags_opcode": physician["stationary_flags_opcode"],
            },
            {
                "version": 199,
                "lobby": (621, 35),
                "office": (550, 16),
                "runtime_half_extents": [32, 32],
                "transit_flags_opcode": "20 01 80",
                "stationary_flags_opcode": "20 0C 80",
            },
        )
        traversal = plan["implementation_invariants"][
            "clinic_doorway_traversal"
        ]
        self.assertEqual(
            traversal,
            {
                "version": 200,
                "field": 550,
                "walkmesh_size": 1_948,
                "walkmesh_sha256": (
                    "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d8cca4238393571df"
                ),
                "exterior_triangles": [34, 35],
                "exterior_material": 0,
                "exterior_material_flags": "0x00800000",
                "actor_local_override": "0x0038",
                "override_set_opcode": "F8 02 38 00",
                "override_clear_opcode": "F8 06 38 00",
                "security_clear_position": [0, 200],
                "security_waypoint_max_steps": 16,
                "doctor_threshold_max_steps": 16,
                "policy": (
                    "the leaf opens before actor-local permission is set; "
                    "security crosses from exterior triangle 34 to deep "
                    "interior floor before clearing it; the doctor crosses "
                    "outside, remains visible for the blocking close, hides, "
                    "then clears it; Fei's solid seal and the global walkmesh "
                    "never change"
                ),
            },
        )

    def test_module_level_validation_passes(self) -> None:
        blueprint.validate_blueprint()


if __name__ == "__main__":
    unittest.main()
