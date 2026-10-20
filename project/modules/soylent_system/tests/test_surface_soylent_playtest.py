from __future__ import annotations

import hashlib
import struct
import unittest
from unittest.mock import patch

import modules.soylent_system.build as campaign
from modules.soylent_system.tests.disc_fixtures import source_disc_path
from modules.soylent_system.tools import surface_soylent_playtest as playtest
from shared.tools.xgdisc import Mode2Image
from shared.tools.xgencounter import EncounterTable
from shared.tools.xgfield import parse_field


class OneHitResourceGuardTests(unittest.TestCase):
    def test_missing_canonical_entry_is_rejected_without_output(self):
        with patch.object(playtest, "Mode2Image") as image:
            image.return_value.read_index.return_value = []
            with self.assertRaisesRegex(playtest.PlaytestResourceError, "outside the disc index"):
                playtest.prepare_one_hit_resources("unused.bin")
            image.return_value.extract_entry.assert_not_called()


class OneHitNativeResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = source_disc_path("mass_driver_base")
        if not cls.source.is_file():
            raise unittest.SkipTest("pinned Soylent source disc is unavailable")
        image = Mode2Image(cls.source)
        entries = image.read_index()
        cls.original = {
            rid: image.extract_entry(entries[rid - 5]) for rid in (2684, 2706)
        }
        boss = parse_field(image.extract_entry(entries[1850 - 5]))
        cls.formations = (
            campaign.CLINIC_SECURITY_FORMATION,
            EncounterTable(boss.parts[6].data).formation(9),
        )
        cls.prepared, cls.metadata = playtest.prepare_one_hit_resources(cls.source)
        cls.patched = {item.canonical_id: item.data for item in cls.prepared}

    def test_every_native_formation_member_uses_one_hp_in_its_active_pool(self):
        # Interpret the native encounter selectors independently of the patch
        # manifest: bit 7 selects Gear HP, low 7 bits select the enemy record.
        # This catches omitting adds or writing character HP for the Gear boss.
        encountered = []
        for formation in self.formations:
            resource_id = 2618 + 2 * formation[0]
            count = 0
            for selector in formation[8:16]:
                record = selector & 0x7F
                if record == 0x7F:
                    continue
                count += 1
                offset = 0x32 + record * 0x170
                if selector & 0x80:
                    normal = struct.unpack_from("<II", self.original[resource_id], offset + 0x104)
                    hp, maximum = struct.unpack_from("<II", self.patched[resource_id], offset + 0x104)
                else:
                    normal = struct.unpack_from("<HH", self.original[resource_id], offset + 0x4C)
                    hp, maximum = struct.unpack_from("<HH", self.patched[resource_id], offset + 0x4C)
                with self.subTest(resource=resource_id, selector=selector):
                    self.assertGreater(normal[0], 1)
                    self.assertEqual((hp, maximum), (1, 1))
                encountered.append((resource_id, record, bool(selector & 0x80)))
            self.assertEqual(count, 4 if resource_id == 2684 else 5)
        self.assertEqual(set(encountered), {
            (2684, 1, False), (2684, 2, False),
            (2706, 3, False), (2706, 4, True),
        })

    def test_only_active_hp_bytes_change_ai_rewards_and_other_records_are_exact(self):
        # Explicit audited byte windows are independent of the helper's spec.
        windows = {2684: ((0x1EE, 4), (0x35E, 4)),
                   2706: ((0x4CE, 4), (0x6F6, 8))}
        for resource_id, spans in windows.items():
            normal = self.original[resource_id]
            modified = self.patched[resource_id]
            allowed = {index for start, size in spans for index in range(start, start + size)}
            self.assertEqual(len(normal), len(modified))
            self.assertTrue(any(a != b for a, b in zip(normal, modified)))
            self.assertEqual(
                bytes(value for index, value in enumerate(normal) if index not in allowed),
                bytes(value for index, value in enumerate(modified) if index not in allowed),
            )
            # Scripts begin immediately after the eight stat records; names
            # follow them. Both must remain exactly native.
            self.assertEqual(normal[0xBB2:], modified[0xBB2:])
        self.assertEqual(struct.unpack_from("<HH", self.patched[2706], 0x63E), (6000, 6000))
        for offset in (0x2A6, 0x416):
            self.assertEqual(struct.unpack_from("<II", self.patched[2684], offset), (0, 0))

    def test_manifest_reports_exact_source_and_output_and_only_two_enemy_resources(self):
        self.assertTrue(self.metadata["one_hit_kills"])
        self.assertEqual(self.metadata["scope"], "standalone_soylent_encounters")
        self.assertEqual(tuple(item.canonical_id for item in self.prepared), (2684, 2706))
        self.assertEqual({item["canonical_id"] for item in self.metadata["resources"]}, {2684, 2706})
        for item, report in zip(self.prepared, self.metadata["resources"]):
            self.assertEqual(report["source_sha256"], hashlib.sha256(self.original[item.canonical_id]).hexdigest())
            self.assertEqual(report["patched_sha256"], hashlib.sha256(item.data).hexdigest())
            self.assertEqual(report["size"], len(item.data))
            self.assertEqual(item.source_sha256, report["source_sha256"])
            for record in report["records"]:
                fmt = "<I" if record["form"] == "gear" else "<H"
                for pool in ("current", "max"):
                    offset = record[f"{pool}_hp_offset"]
                    self.assertEqual(struct.unpack_from(fmt, self.original[item.canonical_id], offset)[0], record[f"original_{pool}_hp"])
                    self.assertEqual(struct.unpack_from(fmt, item.data, offset)[0], record[f"{pool}_hp"])

    def test_source_is_unchanged_and_repeated_preparation_is_deterministic(self):
        again, report = playtest.prepare_one_hit_resources(self.source)
        self.assertEqual(again, self.prepared)
        self.assertEqual(report, self.metadata)
        image = Mode2Image(self.source)
        entries = image.read_index()
        for resource_id, original in self.original.items():
            self.assertEqual(image.extract_entry(entries[resource_id - 5]), original)

    def test_modified_truncated_and_already_one_hit_donors_fail_closed(self):
        corrupt_ai = bytearray(self.original[2684])
        corrupt_ai[0xBB2] ^= 1
        variants = (bytes(corrupt_ai), self.original[2684][:-1], self.patched[2684])
        for variant in variants:
            with self.subTest(size=len(variant)), patch.object(playtest, "Mode2Image") as image:
                image.return_value.read_index.return_value = list(range(3000))
                image.return_value.extract_entry.side_effect = lambda index: (
                    variant if index == 2684 - 5 else self.original[index + 5]
                )
                with self.assertRaisesRegex(playtest.PlaytestResourceError, "checked normalized normal-combat donor"):
                    playtest.prepare_one_hit_resources("unused.bin")


if __name__ == "__main__":
    unittest.main()
