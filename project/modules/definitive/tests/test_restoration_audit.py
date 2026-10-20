from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from modules.definitive import restoration, restoration_audit as audit
from modules.definitive.options import Options


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _rows(resources):
    return [{"canonical_id": n, "size": len(data), "sha256": _hash(data)}
            for n, data in resources.items()]


class ExactResourceTests(unittest.TestCase):
    def test_installed_corruption_is_rejected_even_when_manifest_is_correct(self):
        expected = {38: b"guarded battle", 2746: b"guarded enemy"}
        current = expected | {38: b"guarded battlf"}
        with self.assertRaisesRegex(audit.RestorationAuditError, "Installed resource 38 differs"):
            audit.verify_expected_resources(current.__getitem__, expected, _rows(expected))

    def test_claimed_hash_cannot_replace_regeneration(self):
        expected = {38: b"guarded battle"}
        different = {38: b"unrelated code"}
        with self.assertRaisesRegex(audit.RestorationAuditError, "differs from current restoration"):
            audit.verify_expected_resources(different.__getitem__, expected, _rows(different))
        with self.assertRaisesRegex(audit.RestorationAuditError, "Duplicate"):
            audit.verify_expected_resources(expected.__getitem__, expected, _rows(expected) * 2)


class ReleaseAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / "release"
        self.folder.mkdir()
        self.expected = {38: b"battle repair", 2746: b"Deus flag"}
        self.retail_hashes = {}
        self.manifest = {"format": "xenogears-definitive-build-v1", "options": asdict(Options()),
                         "sources": {}, "discs": {}}
        self.receipt = {"format": "xenogears-project-build-v1", "status": "built",
                        "plan": {"profile": "definitive", "release": "fixture", "prepare_only": False},
                        "sources": {}}
        for disc in (1, 2):
            source_path = Path(self.temp.name) / f"retail{disc}.bin"
            self.write_media(source_path, {38: f"retail battle{disc}".encode(), 2746: b"retail enemy"})
            self.retail_hashes[disc] = audit.digest(source_path)
            record = {"path": str(source_path), "size": source_path.stat().st_size,
                      "sha256": self.retail_hashes[disc]}
            self.receipt["sources"][f"retail_disc{disc}"] = record
            self.manifest["sources"][str(disc)] = dict(record)
            self.manifest["discs"][str(disc)] = {"replacements": _rows(self.expected)}
            self.write_media(self.folder / f"Xenogears_Definitive_CD{disc}.bin", self.expected)
        self.seal_manifest()
        self.seal_receipt()
        self.helper_patch = patch.object(restoration, "build_restoration_replacements", return_value=(self.expected, {"repairs": ["fixture"]}))
        self.helper = self.helper_patch.start()
        self.addCleanup(self.helper_patch.stop)

        class FixtureDisc:
            def __init__(self, path, disc):
                self.data = {int(n): bytes.fromhex(data) for n, data in json.loads(Path(path).read_text()).items()}
            def read(self, canonical):
                return self.data[canonical]
        disc_patch = patch.object(audit, "RetailDisc", FixtureDisc)
        disc_patch.start()
        self.addCleanup(disc_patch.stop)
        hash_patch = patch.object(audit, "RETAIL_SHA256", self.retail_hashes)
        hash_patch.start()
        self.addCleanup(hash_patch.stop)

    def write_media(self, path, resources):
        path.write_text(json.dumps({n: data.hex() for n, data in resources.items()}), encoding="utf-8")

    def seal_manifest(self):
        (self.folder / "definitive-build-manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def seal_receipt(self):
        self.receipt["outputs"] = []
        for name in ("definitive-build-manifest.json", "Xenogears_Definitive_CD1.bin", "Xenogears_Definitive_CD2.bin"):
            path = self.folder / name
            self.receipt["outputs"].append({"path": name, "size": path.stat().st_size, "sha256": audit.digest(path)})
        self.write_receipt()

    def write_receipt(self):
        (self.folder / "project-build.json").write_text(json.dumps(self.receipt), encoding="utf-8")

    def test_completed_pair_is_verified_and_never_certified_as_gameplay(self):
        report = audit.audit_release(self.folder)
        self.assertEqual(set(report["discs"]), {"1", "2"})
        self.assertEqual(self.helper.call_count, 2)
        self.assertTrue(report["exact_selected_bytes_verified"])
        self.assertFalse(report["all_bugs_fixed_verified"])
        self.assertEqual(report["gameplay_status"], "untested")
        self.assertEqual([d["resources_checked"] for d in report["discs"].values()], [2, 2])

    def test_manifest_selected_xp_composes_after_restoration(self):
        xp_expected = self.expected | {2618: b"double XP"}
        self.manifest["options"]["double_xp"] = True
        for disc in (1, 2):
            self.manifest["discs"][str(disc)]["replacements"] = _rows(xp_expected)
            self.write_media(self.folder / f"Xenogears_Definitive_CD{disc}.bin", xp_expected)
        self.seal_manifest()
        self.seal_receipt()
        with patch.object(audit, "patch_rewards", return_value=(xp_expected, {})) as rewards:
            report = audit.audit_release(self.folder)
        self.assertEqual(rewards.call_count, 2)
        for call in rewards.call_args_list:
            self.assertEqual(call.args[1], self.expected)
        self.assertEqual([d["resources_checked"] for d in report["discs"].values()], [3, 3])

    def test_resealed_corrupt_disc_still_fails_regenerated_byte_check(self):
        self.write_media(self.folder / "Xenogears_Definitive_CD2.bin", self.expected | {38: b"bad battle"})
        self.seal_receipt()  # matching file hash cannot bless incorrect installed bytes
        with self.assertRaisesRegex(audit.RestorationAuditError, "Installed resource 38 differs"):
            audit.audit_release(self.folder)

    def test_manifest_and_source_identity_changes_are_rejected(self):
        manifest_path = self.folder / "definitive-build-manifest.json"
        manifest_path.write_text(manifest_path.read_text() + " ")
        with self.assertRaisesRegex(audit.RestorationAuditError, "Output identity differs"):
            audit.audit_release(self.folder)
        self.seal_manifest()
        self.seal_receipt()
        source = Path(self.receipt["sources"]["retail_disc1"]["path"])
        source.write_text("foreign disc")
        with self.assertRaisesRegex(audit.RestorationAuditError, "source identity differs"):
            audit.audit_release(self.folder)

    def test_incomplete_receipts_duplicate_records_and_path_escape_rejected(self):
        self.receipt["status"] = "prepared"
        self.write_receipt()
        with self.assertRaisesRegex(audit.RestorationAuditError, "completed"):
            audit.audit_release(self.folder)
        self.receipt["status"] = "built"
        self.receipt["outputs"].append(dict(self.receipt["outputs"][0]))
        self.write_receipt()
        with self.assertRaisesRegex(audit.RestorationAuditError, "Duplicate"):
            audit.audit_release(self.folder)
        self.seal_receipt()
        self.receipt["outputs"].append({"path": "../outside.bin", "size": 0, "sha256": "unused"})
        self.write_receipt()
        with self.assertRaisesRegex(audit.RestorationAuditError, "escapes"):
            audit.audit_release(self.folder)


if __name__ == "__main__":
    unittest.main()
