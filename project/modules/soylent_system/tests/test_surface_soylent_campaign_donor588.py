from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

from collections import deque
import hashlib
import math
import struct
import unittest
from unittest import mock

import tools.build_surface_soylent_dungeon as surface
import tools.surface_soylent_campaign_donor588 as donor588
from modules.soylent_system.tests.disc_fixtures import source_disc_path
from tools.xgatel import AtelScript as ParsedAtelScript, scan_raw_transitions
from tools.xgencounter import EncounterTable
from tools.xgfield import parse_field
from tools.xgscript import AtelScript as ScriptEditor


PROJECT_ROOT = REPOSITORY_ROOT
REFERENCE_ROOT = (
    PROJECT_ROOT / "work" / "reference_fields" /
    "surface_soylent_donors_cd1_fields"
)
DISC1 = source_disc_path("pw_disc1")
DISC2 = source_disc_path("pw_disc2")


def _identity(data: bytes) -> tuple[int, str]:
    return len(data), hashlib.sha256(data).hexdigest()


def _sampled_cut_is_reachable(
    triangles: tuple[tuple[tuple[int, int, int], ...], ...],
    triangle_ids: tuple[int, ...],
    center: tuple[int, int],
    radius: int,
    start: tuple[int, int],
    goal: tuple[int, int],
) -> bool:
    selected = tuple(triangles[index] for index in triangle_ids)
    step = 2
    xs = [vertex[0] for triangle in selected for vertex in triangle]
    zs = [vertex[2] for triangle in selected for vertex in triangle]
    points = {
        (x, z)
        for x in range(min(xs) // step * step, max(xs) + 1, step)
        for z in range(min(zs) // step * step, max(zs) + 1, step)
        if (
            (x - center[0]) ** 2 + (z - center[1]) ** 2 >= radius ** 2
            and any(
                surface._point_inside_triangle((x, z), triangle)
                for triangle in selected
            )
        )
    }
    nearest = lambda point: min(  # noqa: E731
        points,
        key=lambda sample: (
            (sample[0] - point[0]) ** 2 + (sample[1] - point[1]) ** 2
        ),
    )
    sampled_start = nearest(start)
    sampled_goal = nearest(goal)
    reached = {sampled_start}
    pending = deque((sampled_start,))
    while pending:
        x, z = pending.popleft()
        for dx in (-step, 0, step):
            for dz in (-step, 0, step):
                candidate = x + dx, z + dz
                if candidate in points and candidate not in reached:
                    reached.add(candidate)
                    pending.append(candidate)
    return sampled_goal in reached


class SurfaceSoylentDonor588Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_bundle = (REFERENCE_ROOT / "1706.bin").read_bytes()
        cls.graphics = (REFERENCE_ROOT / "1707.bin").read_bytes()
        cls.source = parse_field(cls.source_bundle)
        cls.prepared = donor588.prepare_donor588(
            cls.source_bundle,
            cls.graphics,
        )

    def test_exact_natural_field550_source_and_logical588_targets(self) -> None:
        identity = donor588.DONOR588_IDENTITY
        self.assertEqual(donor588.SOURCE_SCENE, 550)
        self.assertEqual(donor588.SOURCE_NATURAL_IDENTITY, surface.DONOR_BY_SCENE[550])
        self.assertEqual(donor588.DONOR588_SOURCE_IDS, (1711, 1712))
        self.assertEqual(donor588.DONOR588_TARGET_IDS, (1782, 1783))
        self.assertEqual(identity.scene, 588)
        self.assertEqual((identity.bundle_id, identity.graphics_id), (1782, 1783))
        self.assertEqual(
            _identity(self.source_bundle),
            (identity.bundle_size, identity.bundle_sha256),
        )
        self.assertEqual(
            _identity(self.graphics),
            (identity.graphics_size, identity.graphics_sha256),
        )
        self.assertEqual(
            tuple(_identity(part.data) for part in self.source.parts),
            donor588.SOURCE_COMPONENT_IDENTITIES,
        )

    def test_prepared_output_is_frozen_and_only_script_encounters_change(self) -> None:
        again = donor588.prepare_donor588(self.source_bundle, self.graphics)
        self.assertEqual(self.prepared, again)
        self.assertEqual(
            _identity(self.prepared.components[surface.SCRIPT_INDEX]),
            donor588.FINAL_SCRIPT_IDENTITY,
        )
        self.assertEqual(
            _identity(self.prepared.components[6]),
            donor588.FINAL_ENCOUNTER_IDENTITY,
        )
        self.assertEqual(_identity(self.prepared.bundle), donor588.FINAL_BUNDLE_IDENTITY)
        self.assertEqual(_identity(self.prepared.header), donor588.FINAL_HEADER_IDENTITY)
        self.assertEqual(self.prepared.graphics, self.graphics)
        after = parse_field(self.prepared.bundle)
        changed = {
            index
            for index, (before, prepared) in enumerate(
                zip(self.source.parts, after.parts, strict=True)
            )
            if before.data != prepared.data
        }
        self.assertEqual(changed, {surface.SCRIPT_INDEX, 6})

    def test_bright_baked_scanner_shell_is_preserved_exactly(self) -> None:
        self.assertEqual(donor588.SOURCE_HEADER_ACTOR_COUNT, 35)
        self.assertEqual(
            struct.unpack_from("<H", self.source.header, 0x18C)[0],
            donor588.SOURCE_HEADER_ACTOR_COUNT,
        )
        self.assertEqual(donor588.VISIBLE_SCANNER_STATIC_NODES, tuple(range(29, 35)))
        records = tuple(
            struct.unpack_from("<8H", self.prepared.header, 0x190 + node * 16)
            for node in donor588.VISIBLE_SCANNER_STATIC_NODES
        )
        self.assertEqual(records, donor588.VISIBLE_SCANNER_STATIC_RECORDS)
        self.assertEqual(tuple(record[-1] for record in records), (0, 3, 4, 5, 6, 7))
        for node in donor588.VISIBLE_SCANNER_STATIC_NODES:
            start = 0x190 + node * 16
            self.assertEqual(
                self.prepared.header[start:start + 16],
                self.source.header[start:start + 16],
            )
        self.assertEqual(
            donor588.CAMPAIGN_VISIBLE_SCANNER_STATIC_NODES,
            tuple(node + 1 for node in donor588.VISIBLE_SCANNER_STATIC_NODES),
        )
        self.assertEqual(
            struct.unpack_from(
                "<8H", self.prepared.header,
                0x190 + donor588.CONSOLE_ENTITY * 16,
            ),
            donor588.CONSOLE_HEADER_RECORD,
        )
        self.assertEqual(
            struct.unpack_from(
                "<8H", self.prepared.header,
                0x190 + donor588.RETURN_HELPER * 16,
            ),
            donor588.RETURN_HELPER_HEADER_RECORD,
        )
        self.assertEqual(donor588.RETURN_HELPER_HEADER_RECORD[-1], 1)

    def test_entry_console_return_and_crossing_are_unique_walkmesh_points(self) -> None:
        editor = ScriptEditor(self.prepared.components[surface.SCRIPT_INDEX])
        self.assertEqual(editor.bytecode[1:8], donor588.ENTRY_PLAYABLE)
        self.assertEqual(self.prepared.entry_triangles, ((0, 14),))
        triangles = surface._walkmesh_layer(self.prepared.components[1], 0)
        for position, expected in (
            (donor588.ENTRY_POSITION, donor588.ENTRY_TRIANGLE),
            (donor588.CONSOLE_POSITION, donor588.CONSOLE_TRIANGLE),
            (donor588.RETURN_CONTROLLER_POSITION, donor588.RETURN_CONTROLLER_TRIANGLE),
            (donor588.RETURN_CROSSING_WAYPOINT, donor588.RETURN_CROSSING_TRIANGLE),
        ):
            hits = tuple(
                index
                for index, triangle in enumerate(triangles)
                if surface._point_inside_triangle(position, triangle)
            )
            self.assertEqual(hits, (expected,))
        self.assertEqual((donor588.CONSOLE_ENTITY, donor588.CONSOLE_POSITION), (4, (190, 190)))

    def test_entry_is_clear_and_round_seal_disconnects_door_choke(self) -> None:
        effective_radius = 2 * 0x0E + 0x10
        for probe in (
            donor588.RETURN_CLOSED_SIDE_PROBE,
            donor588.RETURN_OPEN_SIDE_PROBE,
        ):
            self.assertGreater(
                math.dist(probe, donor588.RETURN_CONTROLLER_POSITION),
                effective_radius,
            )
        triangles = surface._walkmesh_layer(self.prepared.components[1], 0)
        self.assertFalse(
            _sampled_cut_is_reachable(
                triangles,
                donor588.RETURN_CUT_TRIANGLES,
                donor588.RETURN_CONTROLLER_POSITION,
                effective_radius,
                donor588.RETURN_CLOSED_SIDE_PROBE,
                donor588.RETURN_OPEN_SIDE_PROBE,
            )
        )
        dx = abs(
            donor588.RETURN_CLOSED_SIDE_PROBE[0]
            - donor588.RETURN_CONTROLLER_POSITION[0]
        )
        dz = abs(
            donor588.RETURN_CLOSED_SIDE_PROBE[1]
            - donor588.RETURN_CONTROLLER_POSITION[1]
        )
        action_x_reach = 2 * donor588.RETURN_ACTION_HALF_WIDTH + 0x10
        action_z_reach = 2 * donor588.RETURN_ACTION_HALF_DEPTH + 0x10
        self.assertTrue(dx > action_x_reach or dz > action_z_reach)
        approach_distance = math.hypot(dx, dz)
        self.assertLessEqual(dx * effective_radius / approach_distance, action_x_reach)
        self.assertLessEqual(dz * effective_radius / approach_distance, action_z_reach)
        self.assertFalse(donor588.RETURN_ACTION_REQUIRES_FACING)

    def test_all_three_party_slots_use_runtime_selectors(self) -> None:
        editor = ScriptEditor(self.prepared.components[surface.SCRIPT_INDEX])
        for pc, selector in zip(
            donor588.PARTY_INIT_PCS,
            surface.PARTY_SELECTORS,
            strict=True,
        ):
            immediate = surface._immediate(selector)
            self.assertEqual(
                editor.bytecode[pc:pc + 7],
                b"\x16" + immediate + b"\xFE\x0D" + immediate,
            )

    def test_native_model_door_is_retargeted_and_correctly_hardened(self) -> None:
        editor = ScriptEditor(self.prepared.components[surface.SCRIPT_INDEX])
        self.assertEqual(
            editor.get_script_pointer(donor588.RETURN_CONTROLLER, 0),
            donor588.HARDENED_INIT_PC,
        )
        self.assertEqual(
            editor.bytecode[
                donor588.HARDENED_INIT_PC:
                donor588.HARDENED_INIT_PC + len(donor588.HARDENED_INIT)
            ],
            donor588.HARDENED_INIT,
        )
        self.assertTrue(donor588.IMMOVABLE_PRECEDES_STOP)
        self.assertEqual(
            donor588.HARDENED_INIT[-len(donor588.IMMOVABLE_OPCODE) - 1:],
            donor588.IMMOVABLE_OPCODE + b"\x00",
        )
        self.assertEqual(
            donor588.HARDENED_INIT,
            donor588.RETURN_CONTROLLER_NATIVE_INIT
            + donor588.IMMOVABLE_OPCODE
            + b"\x00",
        )
        self.assertEqual(
            editor.get_script_pointer(donor588.RETURN_CONTROLLER, 2),
            donor588.RETURN_CONTROLLER_ACTION_PC,
        )
        self.assertEqual(
            editor.bytecode[
                donor588.RETURN_CONTROLLER_ACTION_PC:
                donor588.RETURN_CONTROLLER_ACTION_PC + len(donor588.RETURN_ACTION)
            ],
            donor588.RETURN_ACTION,
        )
        self.assertEqual(
            editor.bytecode[
                donor588.RETURN_TRANSITION_PC:donor588.RETURN_TRANSITION_PC + 5
            ],
            surface._change_field(621, 5),
        )
        self.assertEqual(
            editor.get_script_pointer(
                donor588.RETURN_HELPER,
                donor588.RETURN_HELPER_SCRIPT_INDEX,
            ),
            donor588.RETURN_HELPER_PC,
        )
        self.assertEqual(
            editor.bytecode[
                donor588.RETURN_HELPER_PC:
                donor588.RETURN_HELPER_PC + len(donor588.RETURN_HELPER_BODY)
            ],
            donor588.RETURN_HELPER_BODY,
        )
        self.assertEqual(
            editor.bytecode[
                donor588.RETURN_PLAYER_PC:
                donor588.RETURN_PLAYER_PC + len(donor588.RETURN_PLAYER_BODY)
            ],
            donor588.RETURN_PLAYER_BODY,
        )

    def test_only_return_transition_survives_and_points_to_621_p5(self) -> None:
        source_transitions = scan_raw_transitions(
            ParsedAtelScript(self.source.parts[surface.SCRIPT_INDEX].data)
        )
        final_transitions = scan_raw_transitions(
            ParsedAtelScript(self.prepared.components[surface.SCRIPT_INDEX])
        )
        self.assertEqual(
            tuple((item.pc, item.field, item.parameter) for item in source_transitions),
            ((0x0649, 551, 1),),
        )
        self.assertEqual(
            tuple((item.pc, item.field, item.parameter) for item in final_transitions),
            ((0x0649, 621, 5),),
        )

    def test_retail_scanner_item_story_and_indicator_actions_are_unreachable(self) -> None:
        editor = ScriptEditor(self.prepared.components[surface.SCRIPT_INDEX])
        self.assertEqual(editor.bytecode[donor588.SHARED_STOP_PC], 0)
        self.assertEqual(editor.get_script_pointer(donor588.CONSOLE_ENTITY, 2), donor588.SHARED_STOP_PC)
        self.assertNotIn(
            donor588.CONSOLE_NATIVE_ACTION_PC,
            {
                editor.get_script_pointer(entity, slot)
                for entity in range(editor.entity_count)
                for slot in range(32)
            },
        )
        for entity, pc in zip(
            donor588.SCANNER_FIXTURE_ENTITIES,
            donor588.SCANNER_FIXTURE_INIT_PCS,
            strict=True,
        ):
            self.assertEqual(editor.get_script_pointer(entity, 0), pc)
            self.assertEqual(
                editor.bytecode[pc:pc + len(donor588.SCANNER_FIXTURE_INIT_BODY)],
                donor588.SCANNER_FIXTURE_INIT_BODY,
            )
            self.assertEqual(
                tuple(editor.get_script_pointer(entity, slot) for slot in range(1, 32)),
                (donor588.SHARED_STOP_PC,) * 31,
            )
        self.assertEqual(donor588.RETIRED_STORY_ENTITIES, tuple(range(19, 29)))
        for entity in donor588.RETIRED_ENTITY_SLOTS_ALL_STOP:
            self.assertEqual(
                tuple(editor.get_script_pointer(entity, slot) for slot in range(32)),
                (donor588.SHARED_STOP_PC,) * 32,
            )
        self.assertIn("item/story progression retired", self.prepared.role)

    def test_random_encounters_are_disabled_in_the_real_encounter_table(self) -> None:
        self.assertEqual(
            EncounterTable(self.source.parts[6].data).weights,
            donor588.SOURCE_ENCOUNTER_WEIGHTS,
        )
        self.assertEqual(
            EncounterTable(self.prepared.components[6]).weights,
            donor588.FINAL_ENCOUNTER_WEIGHTS,
        )

    def test_source_drift_is_rejected_before_packing(self) -> None:
        bad_bundle = bytearray(self.source_bundle)
        bad_bundle[-1] ^= 1
        with self.assertRaisesRegex(surface.SurfaceSoylentBuildError, "bundle changed"):
            donor588.prepare_donor588(bytes(bad_bundle), self.graphics)
        bad_graphics = bytearray(self.graphics)
        bad_graphics[-1] ^= 1
        with self.assertRaisesRegex(surface.SurfaceSoylentBuildError, "graphics changed"):
            donor588.prepare_donor588(self.source_bundle, bytes(bad_graphics))

    def test_dummy_target_guard_checks_both_exact_payloads(self) -> None:
        exact = {
            canonical_id: surface.DONOR_DUMMY
            for canonical_id in donor588.DONOR588_TARGET_IDS
        }
        with mock.patch.object(
            donor588.surface,
            "_load_canonical_resources",
            return_value=exact,
        ) as loader:
            donor588.verify_donor588_targets_are_dummy("disc2.bin")
        self.assertEqual(set(loader.call_args.args[1]), set(exact))
        wrong = dict(exact)
        wrong[donor588.TARGET_GRAPHICS_ID] = b"wrong"
        with mock.patch.object(
            donor588.surface,
            "_load_canonical_resources",
            return_value=wrong,
        ):
            with self.assertRaisesRegex(
                surface.SurfaceSoylentBuildError,
                "not the checked CDMAKE dummy",
            ):
                donor588.verify_donor588_targets_are_dummy("disc2.bin")

    @unittest.skipUnless(DISC1.is_file(), "Perfect Works Disc 1 is unavailable")
    def test_disc_loader_extracts_the_frozen_reference_pair(self) -> None:
        self.assertEqual(
            donor588.load_donor588_source(DISC1),
            (self.source_bundle, self.graphics),
        )

    @unittest.skipUnless(DISC2.is_file(), "Perfect Works Disc 2 is unavailable")
    def test_real_disc_two_targets_are_checked_dummies(self) -> None:
        donor588.verify_donor588_targets_are_dummy(DISC2)


if __name__ == "__main__":
    unittest.main()
