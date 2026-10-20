from __future__ import annotations

import unittest

from modules.definitive import bug_audit, mechanics
from modules.definitive.tests.test_mechanics import _retail_sources
from shared.tools.xgdisc import Mode2Image
from shared.tools.xgfield import compress_lzss_retail


@unittest.skipUnless(_retail_sources(), "local user retail discs are not configured")
class KnownBugAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discs = []
        for disc, path in _retail_sources():
            image = Mode2Image(path)
            entries = image.read_index()
            data = {n: image.extract_entry(entries[n - (5 if disc == 2 else 0)])
                    for n in (38, 2602, 2746)}
            cls.discs.append((disc, data))

    def test_both_retail_discs_have_deus_and_billy_preimages(self):
        for disc, retail in self.discs:
            with self.subTest(disc=disc):
                result = bug_audit.audit_resources(retail.__getitem__, retail.__getitem__)
                self.assertEqual([x["status"] for x in result["known_issues"]],
                                 ["inspected_correction_absent"] * 2)
                self.assertFalse(result["all_bugs_fixed_verified"])
                self.assertFalse(any(x["correction_bytes_present"] for x in result["implemented_corrections"]))
                self.assertEqual(retail[2746][0xC22:0xC26], bytes.fromhex("01 00 01 00"))

    def test_three_existing_fixes_do_not_pass_remaining_bug_checks(self):
        retail = self.discs[0][1]
        replacements, _ = mechanics.build_mechanics_replacements(retail.__getitem__)
        current = retail | replacements
        result = bug_audit.audit_resources(retail.__getitem__, current.__getitem__)
        self.assertTrue(all(x["correction_bytes_present"] for x in result["implemented_corrections"]))
        self.assertEqual([x["status"] for x in result["known_issues"]],
                         ["inspected_correction_absent"] * 2)
        self.assertTrue(all(x["retail_bytes_retained"] for x in result["status_effect_investigation"]["probes"]))
        self.assertFalse(result["all_bugs_fixed_verified"])

    def test_changing_a_known_bug_site_does_not_certify_a_fix(self):
        retail = self.discs[0][1]
        decoded = bytearray(bug_audit._battle(retail[38]))
        decoded[0x248A0] ^= 1
        current = retail | {38: compress_lzss_retail(bytes(decoded))}
        result = bug_audit.audit_resources(retail.__getitem__, current.__getitem__)
        self.assertEqual(result["known_issues"][1]["status"], "modified_requires_validation")
        self.assertFalse(result["all_bugs_fixed_verified"])

    def test_enemy_flag_alone_does_not_certify_camera_fix(self):
        retail = self.discs[0][1]
        enemy = bytearray(retail[2746])
        enemy[0xC25] = 1
        result = bug_audit.audit_resources(retail.__getitem__, (retail | {2746: bytes(enemy)}).__getitem__)
        self.assertEqual(result["known_issues"][0]["status"], "modified_requires_validation")
        self.assertTrue(all(x["retail_bytes_retained"] for x in result["known_issues"][0]["probes"][:3]))
        self.assertFalse(result["all_bugs_fixed_verified"])

    def test_foreign_retail_and_truncated_current_images_fail_closed(self):
        retail = self.discs[0][1]
        for n in retail:
            changed = retail | {n: retail[n][:-1]}
            with self.subTest(resource=n), self.assertRaises(ValueError):
                bug_audit.audit_resources(changed.__getitem__, retail.__getitem__)
        with self.assertRaises(ValueError):
            bug_audit.audit_resources(retail.__getitem__, (retail | {38: b"short"}).__getitem__)
        with self.assertRaises(ValueError):
            bug_audit.audit_resources(retail.__getitem__, (retail | {2746: bytes(4)}).__getitem__)


if __name__ == "__main__":
    unittest.main()
