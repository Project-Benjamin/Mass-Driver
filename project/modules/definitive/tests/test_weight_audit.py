from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import struct
import unittest

from modules.definitive.build import RetailDisc
from modules.definitive import weight_audit as audit, weight_fix as fix
from modules.definitive.cpu_audit import Machine
from modules.definitive.item_spell_audit import archive_members, decode_member, record_rows
from shared.tools.xgfield import decompress_lzss

ROOT = Path(__file__).resolve().parents[3]


class NativeWeightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = ROOT / "project.local.json"
        if not config.is_file():
            raise unittest.SkipTest("Configured USA retail disc required")
        data = json.loads(config.read_text(encoding="utf-8"))
        cls.readers = []
        for disc in (1, 2):
            raw = data.get("sources", {}).get(f"retail_disc{disc}", {}).get("path")
            if raw and Path(raw).is_file():
                cls.readers.append(RetailDisc(Path(raw), disc))
        if not cls.readers:
            raise unittest.SkipTest("Configured USA retail disc required")
        cls.reader = cls.readers[0]
        cls.menu = cls.reader.read(2599)
        members = archive_members(cls.reader.read(2594), expected_count=56)
        cls.item_rows = record_rows(decode_member(members[0]), stride=16, count=150)
        cls.accessories = record_rows(decode_member(members[19]), stride=28, count=150)

    def require_cpu(self):
        if importlib.util.find_spec("unicorn") is None:
            self.skipTest("Install requirements-audit.txt to execute native MIPS")

    def test_fix_rejects_modified_or_already_patched_menu(self):
        for source in (b"", self.menu[:-1], bytes([self.menu[0] ^ 1]) + self.menu[1:], fix.patch_menu(self.menu)):
            with self.assertRaises(fix.WeightFixError):
                fix.patch_menu(source)

    def test_all_four_menu_variants_and_both_retail_discs(self):
        for reader in self.readers:
            with self.subTest(disc=reader.disc):
                replacements, report = fix.build_weight_replacements(reader.read)
                self.assertEqual(set(replacements), {39, 2597, 2599, 2603})
                self.assertEqual(len(report["resources"]), 4)
                expected = fix.patch_menu(reader.read(2599))
                self.assertEqual(expected[:fix.GAIN_START], self.menu[:fix.GAIN_START])
                self.assertEqual(expected[fix.GAIN_END:], self.menu[fix.GAIN_END:])
                for canonical, result in replacements.items():
                    if canonical == 39:
                        self.assertEqual(audit.decoded_resource(replacements.__getitem__, 39), expected)
                        result = decompress_lzss(result, fix.MENU_SIZE).data
                    self.assertEqual(result, expected)

    def test_gain_fix_all_byte_weights_and_loss_path_unchanged(self):
        self.require_cpu()
        machine = Machine(fix.patch_menu(self.menu), audit.MENU_BASE)
        for item_id, delta in ((72, -2), (73, -4), (74, 2), (75, 4)):
            for mutable in range(256):
                record = bytearray((i * 37) & 255 for i in range(0xA4))
                record[0x77:0x7A] = bytes((26, mutable, mutable % 10))
                machine.write(0x80100000, record)
                machine.write(0x80101000, self.item_rows[item_id])
                machine.reg("a0", 0x80100000)
                machine.reg("s0", 0x80101000)
                machine.run(audit.MENU_BASE + 0x1E484, audit.MENU_BASE + 0x1E510)
                expected = (mutable if mutable >= 200 else min(200, mutable + delta)) if delta > 0 else max(0, mutable + delta)
                record[0x78] = expected
                with self.subTest(item=item_id, mutable=mutable):
                    self.assertEqual(machine.read(0x80100000, 0xA4), record)

    def test_native_regression_reproduced_then_corrected(self):
        self.require_cpu()
        before = audit.body_gain_above_cap_cases(self.menu, self.item_rows)
        after = audit.body_gain_above_cap_cases(fix.patch_menu(self.menu), self.item_rows)
        self.assertTrue(before["remaining_bug"])
        self.assertFalse(after["remaining_bug"])
        self.assertEqual(before["rows"][2]["mutable_before"], 229)
        self.assertEqual(before["rows"][2]["mutable_after"], 200)
        self.assertEqual(after["rows"][2]["mutable_after"], 229)

    def test_native_display_and_save_buffer_round_trip(self):
        self.require_cpu()
        result = audit.body_display_cases(self.menu, self.reader.read(2595))
        self.assertEqual(result["cases"], 550)
        self.assertEqual(result["failed_inputs"], [])
        saved = audit.body_save_copy_case(self.menu)
        self.assertTrue(saved["passed"])
        self.assertEqual(saved["bytes_roundtripped"], 1804)

    def test_native_gear_weight_penalty_and_battle_consumer(self):
        self.require_cpu()
        penalty = audit.gear_penalty_cases(self.reader.read(2602), self.accessories, self.reader.read(2595))
        self.assertEqual(penalty["max_three_slot_weight"], 1800)
        self.assertEqual(penalty["failed_inputs"], [])
        battle = audit.decoded_resource(self.reader.read, 38)
        self.assertEqual(audit.gear_battle_cases(battle)["failures"], 0)
        readiness = audit.atb_cases(battle)
        self.assertTrue(all(row["passed"] for row in readiness["rows"]))

    def test_native_field_setter_preserves_lower_floor_but_has_no_upper_clamp(self):
        self.require_cpu()
        result = audit.field_weight_boundary_cases(audit.decoded_resource(self.reader.read, 36))
        self.assertTrue(all(row["mutable_result"] == row["native_expected"] for row in result["rows"]))
        self.assertEqual(result["rows"][-1]["mutable_result"], 0)

    def test_audit_rejects_changed_native_weight_consumer(self):
        resources = {n: audit.decoded_resource(self.reader.read, n) for n in (36, 38, 2599, 2602)}
        audit.check_spans(resources)
        changed = bytearray(resources[38])
        changed[0x287D0] ^= 1
        resources[38] = bytes(changed)
        with self.assertRaises(audit.WeightAuditError):
            audit.check_spans(resources)


if __name__ == "__main__":
    unittest.main()
