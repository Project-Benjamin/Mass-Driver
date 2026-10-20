"""Geometry/resource boundaries for the connected Chapter 2 expansion."""
from __future__ import annotations

import json
from pathlib import Path
import unittest
from unittest.mock import patch

from shared.paths import PROJECT_ROOT
from modules.rico import chapter_two_resources as resources
from modules.rico.build import DiscReader


class ChapterTwoResourceContractTests(unittest.TestCase):
    def test_intake_cast_has_bedside_attendant_and_guard_before_hammers_entrance(self):
        intake = resources.ROOM_SPECS["intake"]
        self.assertEqual(intake["npcs"], {"doctor": {"entity": 8, "bank": 2, "palette": 1},
                                         "guard": {"entity": 10, "bank": 0}})
        self.assertEqual(intake["landmarks"]["guard"], resources.ARRIVAL_GUARD)
        self.assertNotIn("hammer", intake["landmarks"])
        self.assertEqual(intake["cast"]["fei"], resources.ARRIVAL_PATIENT[:2])

    def test_all_profiles_reserve_the_same_twelve_isolated_fields(self):
        self.assertEqual(set(resources.WORLD_FIELDS.values()), set(range(68, 80)))
        self.assertEqual(resources.fields_for(1), resources.fields_for(2, combined=True))
        self.assertEqual(set(resources.WORLD_FIELDS), set(resources.ROOM_SPECS))
        with self.assertRaises(resources.ChapterTwoResourceError):
            resources.fields_for(1, combined=True)
        copied = resources.fields_for(1)
        copied["intake"] = 0
        self.assertEqual(resources.WORLD_FIELDS["intake"], 68)

    def test_formation_install_changes_only_requested_slot_and_random_weights(self):
        original = bytes((index * 7 + 1) % 256 for index in range(528))
        result = resources.install_redrum_formation(original, slot=7)
        self.assertEqual(result[:224], original[:224])
        self.assertEqual(result[224:256], resources.REDRUM_FORMATION)
        self.assertEqual(result[256:512], original[256:512])
        self.assertEqual(result[512:], bytes(16))
        for data, slot in ((bytes(512), 15), (original, -1), (original, 16), (original, True)):
            with self.subTest(length=len(data), slot=slot), self.assertRaises(resources.ChapterTwoResourceError):
                resources.install_redrum_formation(data, slot=slot)

    def test_walkable_room_entries_start_outside_all_active_action_carriers(self):
        from modules.rico.chapter_two import actions_for
        for role, spec in resources.ROOM_SPECS.items():
            x, z, _ = spec["entry"]
            for action in actions_for(role):
                if action.landmark in spec.get("native_actions", {}):
                    continue  # Native doors have no authored proximity carrier.
                ax, az, _ = spec["landmarks"][action.landmark]
                with self.subTest(room=role, action=action.name):
                    # OP18 doubles18 to36, then adds Rico's16-unit extent.
                    # Seventy provides clearance beyond that52-unit box.
                    self.assertGreaterEqual(max(abs(x - ax), abs(z - az)), 70)


class ChapterTwoRetailResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = PROJECT_ROOT / "project.local.json"
        if not path.is_file():
            raise unittest.SkipTest("Local source-disc registry is absent")
        local = json.loads(path.read_text(encoding="utf-8"))
        cls.sources = local.get("sources", {})
        source = Path(cls.sources.get("retail_disc1", {}).get("path", "missing-retail-disc1.bin"))
        if not source.is_file():
            raise unittest.SkipTest("Original retail Disc 1 is unavailable")
        cls.disc1 = DiscReader(source, 1)

    def test_all_pinned_donors_allocations_and_landmarks_match_retail(self):
        report = resources.validate_allocations(self.disc1)
        self.assertEqual(len(report["rooms"]), 12)
        self.assertEqual(report["rooms"]["sewer_key"]["connected"], 185)
        self.assertEqual(len(resources.DONOR_RESOURCE_IDENTITIES), 24)
        self.assertEqual(len(resources.DISC_ONE_DISPOSABLE_IDENTITIES), 24)

    def test_geometry_guard_rejects_valid_floor_in_an_unreachable_component(self):
        role = "sewer_key"
        source = self.disc1.canonical(606 + 2 * resources.ROOM_SPECS[role]["donor"])
        parsed = resources.parse_field(source)
        triangles, neighbours = resources._layer_zero_geometry(parsed.parts[1].data)
        connected, pending = {46}, [46]
        while pending:
            for neighbour in neighbours[pending.pop()]:
                if neighbour not in connected:
                    connected.add(neighbour)
                    pending.append(neighbour)
        unreachable = next(index for index in range(len(triangles)) if index not in connected)
        x, _, z = triangles[unreachable][0]
        spec = dict(resources.ROOM_SPECS[role])
        spec["landmarks"] = {"unreachable": (x, z, unreachable)}
        with patch.dict(resources.ROOM_SPECS, {role: spec}):
            with self.assertRaisesRegex(resources.ChapterTwoResourceError, "reachable"):
                resources.validate_room_geometry(role, source)

    def test_donor_and_target_pins_both_reject_changed_source_bytes(self):
        for resource in (next(iter(resources.DONOR_RESOURCE_IDENTITIES)),
                         next(iter(resources.DISC_ONE_DISPOSABLE_IDENTITIES))):
            reader = self.disc1.canonical

            class ChangedReader:
                disc = 1

                def canonical(self, resource_id):
                    value = reader(resource_id)
                    return value[:-1] + bytes([value[-1] ^ 1]) if resource_id == resource else value

            with self.subTest(resource=resource), self.assertRaisesRegex(resources.ChapterTwoResourceError, str(resource)):
                resources.validate_allocations(ChangedReader())

    def test_redrum_formation_matches_native_slot_fifteen(self):
        field = resources.parse_field(self.disc1.canonical(606 + 2 * 239))
        self.assertEqual(field.parts[6].data[15 * 32:16 * 32], resources.REDRUM_FORMATION)

    def test_visible_model_allowlist_excludes_actor_attached_baptism_props(self):
        from shared.tools.xgatel import AtelScript
        self.assertEqual(resources.SAFE_STATIC_MODELS["central"], tuple(range(12, 37)))
        self.assertEqual(resources.SAFE_STATIC_MODELS["baptism"], ())
        for role, spec in resources.ROOM_SPECS.items():
            parsed = resources.parse_field(self.disc1.canonical(606 + 2 * spec["donor"]))
            script = AtelScript(parsed.parts[5].data)
            pointers = {(entity, slot): pc for entity, slot, pc in script.entry_points()}
            for entity in spec["safe_static_models"]:
                with self.subTest(room=role, model_entity=entity):
                    start = pointers[entity, 0]
                    self.assertIn(script.bytecode[start], (0xBC, 0x46))
                    # Native F9 attachment needs its director transforms and
                    # must never enter the header-only model allowlist.
                    self.assertNotEqual(script.bytecode[start:start + 2], b"\xBC\xF9")

    def test_boss_copies_are_local_and_identical_merges_are_safe(self):
        result = resources.battle_resources(self.disc1)
        self.assertEqual(set(result), {2752, 2753, 2793, 2794})
        self.assertEqual(resources.prepare_redrum_resources(self.disc1.canonical, existing=result), {})
        conflicting = dict(result)
        conflicting[2752] += b"changed"
        with self.assertRaisesRegex(resources.ChapterTwoResourceError, "Conflicting Redrum resource 2752"):
            resources.prepare_redrum_resources(self.disc1.canonical, existing=conflicting)
        with self.assertRaisesRegex(resources.ChapterTwoResourceError, "Redrum resource 2752 changed"):
            resources.prepare_redrum_resources(lambda resource: conflicting[resource])

    def test_disc_two_retail_and_pw_slots_are_all_exact_dummies(self):
        checked = 0
        for source_id in ("retail_disc2", "pw_disc2"):
            path = Path(self.sources.get(source_id, {}).get("path", "missing-disc2.bin"))
            if not path.is_file():
                continue
            with self.subTest(source=source_id):
                reader = DiscReader(path, 2)
                resources.validate_disc_two_allocations(reader.canonical)
                with self.assertRaisesRegex(resources.ChapterTwoResourceError, "not the audited dummy"):
                    resources.validate_disc_two_allocations(lambda resource: b"occupied")
                checked += 1
        if not checked:
            self.skipTest("No local Disc 2 source")

    def test_prep_hammer_transplant_preserves_every_unrelated_component_and_bank(self):
        from modules.mass_driver import build as native
        source = self.disc1.canonical(606 + 2 * 223)
        hammer = self.disc1.canonical(606 + 2 * 218)
        before = resources.parse_field(source)
        after = resources.parse_field(resources.install_prep_hammer(source, hammer))
        donor = resources.parse_field(hammer)
        for index in range(9):
            if index in (3, 4):
                original = native._indexed_bundle_entries(before.parts[index].data)
                installed = native._indexed_bundle_entries(after.parts[index].data)
                hammer_banks = native._indexed_bundle_entries(donor.parts[index].data)
                self.assertEqual(installed[0], hammer_banks[4])
                self.assertEqual(installed[1:], original[1:])
            else:
                self.assertEqual(after.parts[index].data, before.parts[index].data)
        self.assertEqual(after.header[:0x100], before.header[:0x100])
        self.assertEqual(after.header[0x18C:], before.header[0x18C:])
        for prep, supplier in ((source + b"changed", hammer), (source, hammer + b"changed")):
            with self.assertRaises(resources.ChapterTwoResourceError):
                resources.install_prep_hammer(prep, supplier)


if __name__ == "__main__":
    unittest.main()
