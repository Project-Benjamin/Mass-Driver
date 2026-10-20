from pathlib import Path
from importlib.util import find_spec
import json
import struct
import unittest

from modules.definitive.build import RetailDisc
from modules.definitive.item_spell_audit import (
    AuditError, archive_members, decode_member, indexed_strings, inventory,
    native_food_validation, record_rows,
)
from modules.definitive.description_fixes import build_description_replacements

ROOT = Path(__file__).resolve().parents[3]


class StructureTests(unittest.TestCase):
    def test_archive_rejects_overlapping_and_out_of_bounds_members(self):
        for data in (b"", struct.pack("<III", 2, 12, 12),
                     struct.pack("<III", 2, 8, 100) + bytes(20)):
            with self.assertRaises(AuditError):
                archive_members(data)

    def test_record_start_is_zero_not_price_offset(self):
        rows = record_rows(bytes(range(32)) + bytes(3), 16, 2)
        self.assertEqual(rows, (bytes(range(16)), bytes(range(16, 32))))
        for size in (31, 40):
            with self.assertRaises(AuditError):
                record_rows(bytes(size), 16, 2)

    def test_strings_keep_unknown_codes_and_allocation_metadata(self):
        raw = struct.pack("<IHBB", 0, 8, 6, 1) + bytes([0x77, 0, 0])
        row = indexed_strings(raw)[0]
        self.assertEqual(row["text"], "<Byte:77>")
        self.assertTrue(row["has_untranslated_or_unknown_codes"])
        self.assertEqual((row["width"], row["height"], row["raw_hex"]), (6, 1, "770000"))

    def test_strings_reject_no_terminal_close(self):
        with self.assertRaises(AuditError):
            indexed_strings(struct.pack("<IHBB", 0, 8, 2, 1) + b"\x20")

    def test_zero_control_argument_is_not_a_terminal_close(self):
        raw = struct.pack("<IHBB", 0, 8, 6, 1) + bytes([0xFE, 0, 0x20, 0])
        self.assertEqual(indexed_strings(raw)[0]["text"], "<Extra1:00>A")


class RetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        local = ROOT / "project.local.json"
        if not local.exists():
            raise unittest.SkipTest("Local retail discs are not configured")
        sources = json.loads(local.read_text(encoding="utf-8")).get("sources", {})
        if not all(sources.get(f"retail_disc{disc}", {}).get("path") for disc in (1, 2)):
            raise unittest.SkipTest("Both local retail discs are required")
        paths = [Path(sources[f"retail_disc{disc}"]["path"]) for disc in (1, 2)]
        paths = [p if p.is_absolute() else ROOT / p for p in paths]
        if not all(path.exists() for path in paths):
            raise unittest.SkipTest("Both local retail discs are required")
        cls.discs = [RetailDisc(path, disc) for disc, path in enumerate(paths, 1)]

    def test_full_native_inventory_and_menu_battle_duplicates(self):
        reports = [inventory(disc.read) for disc in self.discs]
        self.assertEqual(reports[0], reports[1])
        report = reports[0]
        self.assertEqual(report["coverage"]["native_item_equipment_rows"], 1180)
        self.assertEqual(len(report["tables"]["character_abilities"]["rows"]), 176)
        differing = [row for row in report["duplicate_tables"] if not row["identical_meaningful_rows"]]
        # Retail already has a different Gear 16 menu copy. Inventory that gap;
        # never erase it by falsely asserting every action copy is identical.
        self.assertEqual([(r["kind"], r["actor"]) for r in differing], [("gear_actions", 16)])
        self.assertEqual(len(differing[0]["differences"]), 11)
        self.assertEqual([(x["item_id"], x["claimed_hp"], x["native_menu_hp_before_cap"])
                          for x in report["findings"]], [(58, 150, 100), (59, 500, 150)])
        self.assertFalse(report["coverage"]["whole_game_semantics_verified"])

    @unittest.skipUnless(find_spec("unicorn"), "optional native CPU audit requires requirements-audit.txt")
    def test_native_food_recovery_and_battle_exclusion_on_both_discs(self):
        for disc in self.discs:
            with self.subTest(disc=disc.disc):
                report = native_food_validation(disc.read)
                self.assertEqual(len(report["hp_recovery_cases"]), 36)
                self.assertEqual(len(report["battle_item_filter_cases"]), 150)
                self.assertTrue(all(x["passed"] for x in report["hp_recovery_cases"]))
                self.assertFalse(report["battle_item_filter_cases"][58]["available"])
                self.assertFalse(report["battle_item_filter_cases"][59]["available"])

    def test_description_fix_changes_only_four_fixed_length_strings(self):
        for disc in self.discs:
            replacements, receipt = build_description_replacements(disc.read)
            self.assertEqual(set(replacements), {2594})
            self.assertFalse(receipt["effects_changed"])
            before = archive_members(disc.read(2594), 56)
            after = archive_members(replacements[2594], 56)
            for member in range(56):
                if member not in (14, 41):
                    self.assertEqual(before[member], after[member])
                    continue
                old, new = decode_member(before[member]), decode_member(after[member])
                old_rows, new_rows = indexed_strings(old), indexed_strings(new)
                self.assertEqual(new_rows[58]["text"], "Restores HP (100) Non-battle")
                self.assertEqual(new_rows[59]["text"], "Restores HP (150) Non-battle")
                allowed = set()
                for i in (58, 59):
                    off = old_rows[i]["decoded_offset"] + len("Restores HP (")
                    allowed.update(range(off, off + 3))
                    self.assertEqual(old_rows[i]["width"], new_rows[i]["width"])
                    self.assertEqual(old_rows[i]["decoded_offset"], new_rows[i]["decoded_offset"])
                self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(old, new))))
                self.assertLessEqual(len(new) - len(old), 7)
            patched_inventory = inventory(lambda cid: replacements.get(cid) or disc.read(cid))
            self.assertEqual(patched_inventory["findings"], [])

    def test_description_fix_rejects_repeated_unknown_or_changed_code(self):
        disc = self.discs[0]
        replacements, _ = build_description_replacements(disc.read)
        with self.assertRaises(AuditError):
            build_description_replacements(lambda cid: replacements.get(cid) or disc.read(cid))
        for cid, offset in ((2594, 100), (2599, 0x1E234), (2615, 0xD80)):
            changed = bytearray(disc.read(cid))
            changed[offset] ^= 1
            with self.subTest(cid=cid), self.assertRaises(AuditError):
                build_description_replacements(lambda request: bytes(changed) if request == cid else disc.read(request))


if __name__ == "__main__":
    unittest.main()
