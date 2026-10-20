"""Release selection guards exercised with small, real on-disk media fixtures."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

from shared import project_registry as project
from shared import project_releases as releases


ROOT = Path(__file__).resolve().parents[1]


class ProjectReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="xgreleases_")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = json.loads((ROOT / "project.json").read_text(encoding="utf-8"))
        (self.root / "shared" / "tools").mkdir(parents=True)
        (self.root / "shared" / "tools" / "codec.py").write_text("VALUE = 1\n")
        (self.root / "shared" / "resources.json").write_text("{}")
        (self.root / "project.py").write_text("# fixture\n")
        for module in self.registry["modules"].values():
            directory = self.root / module["path"]
            (directory / "content").mkdir(parents=True)
            (directory / "build.py").write_text("# fixture module\n")
        (self.root / "work").mkdir()
        (self.root / "work" / "donor.bin").write_bytes(b"small extracted donor")
        (self.root / "xenoiso.exe").write_bytes(b"fixture native tool")
        self.registry["tools"].update(input_root="work", xenoiso="xenoiso.exe")
        for source_id, source in self.registry["sources"].items():
            path = self.root / f"{source_id}.bin"
            path.write_bytes(source_id.encode("ascii"))
            source.update(path=str(path), sha256=project.fingerprint_file(path)["sha256"])
        (self.root / "project.json").write_text(json.dumps(self.registry))
        self.toolchain = {"sha256": "a" * 64}
        tool_module = ModuleType("shared.toolchain")
        tool_module.toolchain_snapshot = lambda root, registry: self.toolchain
        mock = patch.dict(sys.modules, {"shared.toolchain": tool_module})
        mock.start()
        self.addCleanup(mock.stop)

    def build(self, profile="combined", release="reviewed", *, status="built", finished="2026-09-05T12:00:00+00:00"):
        directory = self.root / "builds" / profile / release
        directory.mkdir(parents=True)
        names = ["disc1", "disc2"] if profile == "rico" else ["disc"]
        for name in names:
            (directory / f"{name}.bin").write_bytes(f"{profile} {release} {name}".encode())
            (directory / f"{name}.cue").write_text(f'FILE "{name}.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n')
        if profile == "rico":
            (directory / "game.m3u").write_text("# paired discs\ndisc1.cue\ndisc2.cue\n")
        spec = self.registry["profiles"][profile]
        sources, _ = project.inspect_sources(self.root, self.registry, spec["source_ids"])
        donor = self.root / "work" / "donor.bin"
        inputs = [{"path": "donor.bin", **project.fingerprint_file(donor)}]
        receipt = {
            "format": project.MANIFEST_FORMAT, "status": status, "finished_utc": finished,
            "plan": {"profile": profile, "release": release, "output": str(directory),
                     "prepare_only": status == "prepared", "source_ids": spec["source_ids"],
                     "modules": spec["modules"]},
            "source_snapshot": project.source_snapshot(self.root, self.registry, profile),
            "native_tools": {"xenoiso": {"path": str(self.root / "xenoiso.exe"), **project.fingerprint_file(self.root / "xenoiso.exe")}},
            "sources": sources,
            "consumed_extracted_inputs": {"format": "xenogears-consumed-inputs-v1", "input_root": str(self.root / "work"),
                                          "files": inputs, "sha256": project._digest(inputs), "error": None},
            "toolchain": deepcopy(self.toolchain),
            "outputs": [{"path": p.name, **project.fingerprint_file(p)} for p in sorted(directory.iterdir())],
        }
        self.write_receipt(directory, receipt)
        return directory, receipt

    @staticmethod
    def write_receipt(directory, receipt):
        (directory / "project-build.json").write_text(json.dumps(receipt), encoding="utf-8")

    def update_output(self, directory, receipt, name, text):
        path = directory / name
        path.write_text(text)
        for item in receipt["outputs"]:
            if item["path"] == name:
                item.update(project.fingerprint_file(path))
        self.write_receipt(directory, receipt)

    def test_latest_probe_never_replaces_explicit_active_release(self):
        self.build()
        activated = releases.activate_release(self.root, self.registry, "combined", "reviewed",
                                             runtime_status="selector issue under investigation", label="Current candidate")
        self.assertTrue(activated["media_verified"])
        self.build(release="probe", finished="2026-09-05T15:00:00+00:00")
        plan = releases.play_plan(self.root, self.registry, "combined")
        self.assertEqual(plan["release"], "reviewed")
        self.assertEqual(plan["runtime_status"], "selector issue under investigation")
        report = releases.release_status(self.root, self.registry, "combined")["profiles"]["combined"]
        self.assertEqual(report["active"]["release"], "reviewed")
        self.assertEqual(report["latest_built"]["release"], "probe")
        self.assertFalse(report["active"]["media_verified"])

    def test_no_active_selection_never_falls_back_to_newest(self):
        self.build(release="probe")
        with self.assertRaisesRegex(project.ProjectError, "No active"):
            releases.play_plan(self.root, self.registry, "combined")
        self.assertFalse((self.root / "builds/current.json").exists())

    def test_shared_changes_block_play_and_activation_without_mutating_selection(self):
        self.build()
        releases.activate_release(self.root, self.registry, "combined", "reviewed")
        original = (self.root / "builds/current.json").read_bytes()
        (self.root / "shared/tools/codec.py").write_text("VALUE = 2\n")
        for action in (
            lambda: releases.play_plan(self.root, self.registry, "combined"),
            lambda: releases.activate_release(self.root, self.registry, "combined", "reviewed"),
        ):
            with self.assertRaisesRegex(project.ProjectError, "shared tools"):
                action()
        self.assertEqual((self.root / "builds/current.json").read_bytes(), original)
        plan = releases.play_plan(self.root, self.registry, "combined", allow_stale=True)
        self.assertFalse(plan["fresh"])

    def test_rico_dependency_change_blocks_standalone_launch(self):
        self.build(profile="rico")
        (self.root / "modules/mass_driver/build.py").write_text("# changed reused helper\n")
        with self.assertRaisesRegex(project.ProjectError, "module mass_driver changed"):
            releases.play_plan(self.root, self.registry, "rico", "reviewed")

    def test_failed_and_prepared_builds_cannot_be_activated(self):
        for status in ("failed", "prepared", "building"):
            self.build(release=status, status=status)
            with self.subTest(status=status), self.assertRaisesRegex(project.ProjectError, "not a completed disc build"):
                releases.activate_release(self.root, self.registry, "combined", status)
        self.assertFalse((self.root / "builds/current.json").exists())
        status = releases.release_status(self.root, self.registry, "combined")["profiles"]["combined"]
        self.assertIsNone(status["latest_built"])
        self.assertEqual({item["status"] for item in status["releases"]}, {"failed", "prepared", "building"})

    def test_rico_uses_verified_paired_playlist(self):
        directory, _ = self.build(profile="rico")
        plan = releases.play_plan(self.root, self.registry, "rico", "reviewed")
        self.assertEqual(plan["media"], str(directory / "game.m3u"))
        self.assertEqual(plan["runtime_status"], "untested")

    def test_rico_playlist_requires_each_recorded_disc_exactly_once(self):
        directory, receipt = self.build(profile="rico")
        for content in ("disc1.cue\ndisc1.cue\n", "disc1.cue\n", "disc1.cue\ndisc2.cue\ndisc1.cue\n"):
            self.update_output(directory, receipt, "game.m3u", content)
            with self.subTest(content=content), self.assertRaisesRegex(project.ProjectError, "two distinct"):
                releases.play_plan(self.root, self.registry, "rico", "reviewed")
            report = releases.release_status(self.root, self.registry, "rico")["profiles"]["rico"]["latest_built"]
            self.assertFalse(report["fresh"])
            self.assertTrue(report["errors"])

    def test_rico_cannot_fall_back_to_a_single_cue_without_playlist(self):
        directory, receipt = self.build(profile="rico")
        receipt["outputs"] = [item for item in receipt["outputs"] if item["path"] in ("disc1.bin", "disc1.cue")]
        self.write_receipt(directory, receipt)
        with self.assertRaisesRegex(project.ProjectError, "root playlist"):
            releases.play_plan(self.root, self.registry, "rico", "reviewed")

    def test_same_size_bin_tampering_blocks_play_even_allow_stale(self):
        directory, _ = self.build()
        media = directory / "disc.bin"
        media.write_bytes(b"X" * media.stat().st_size)
        with self.assertRaisesRegex(project.ProjectError, "SHA-256 mismatch"):
            releases.play_plan(self.root, self.registry, "combined", "reviewed", allow_stale=True)
        report = releases.release_status(self.root, self.registry, "combined", verify=True)
        self.assertIn("SHA-256 mismatch", report["profiles"]["combined"]["latest_built"]["errors"][0])
        self.assertFalse(report["profiles"]["combined"]["latest_built"]["fresh"])

    def test_unrecorded_cue_reference_is_rejected_even_with_updated_cue_hash(self):
        directory, receipt = self.build()
        (directory / "other.bin").write_bytes(b"unrecorded")
        self.update_output(directory, receipt, "disc.cue", 'FILE "other.bin" BINARY\n')
        with self.assertRaisesRegex(project.ProjectError, "Unrecorded"):
            releases.activate_release(self.root, self.registry, "combined", "reviewed")
        status = releases.release_status(self.root, self.registry, "combined")["profiles"]["combined"]["latest_built"]
        self.assertFalse(status["fresh"])
        self.assertTrue(status["errors"])

    def test_cue_path_escape_and_malformed_references_are_rejected(self):
        directory, receipt = self.build()
        for line in ('FILE "../outside.bin" BINARY\n', 'FILE "C:\\outside.bin" BINARY\n', 'FILE "disc.bin"\n'):
            self.update_output(directory, receipt, "disc.cue", line)
            with self.subTest(line=line), self.assertRaises(project.ProjectError):
                releases.play_plan(self.root, self.registry, "combined", "reviewed")

    def test_m3u_cannot_escape_or_reference_an_unrecorded_cue(self):
        directory, receipt = self.build(profile="rico")
        for line in ("../foreign.cue\n", "absent.cue\n", "disc1.bin\n"):
            self.update_output(directory, receipt, "game.m3u", line)
            with self.subTest(line=line), self.assertRaises(project.ProjectError):
                releases.play_plan(self.root, self.registry, "rico", "reviewed")

    def test_receipt_profile_and_recorded_output_path_are_checked(self):
        directory, receipt = self.build()
        receipt["plan"]["profile"] = "rico"
        self.write_receipt(directory, receipt)
        with self.assertRaisesRegex(project.ProjectError, "identity disagrees"):
            releases.play_plan(self.root, self.registry, "combined", "reviewed")
        receipt["plan"]["profile"] = "combined"
        receipt["outputs"][0]["path"] = "../foreign.bin"
        self.write_receipt(directory, receipt)
        with self.assertRaisesRegex(project.ProjectError, "release-relative"):
            releases.play_plan(self.root, self.registry, "combined", "reviewed")

    def test_missing_or_invalid_receipt_status_is_reported_without_crashing(self):
        directory, receipt = self.build()
        for invalid in (None, "unknown", {"status": "built"}):
            if invalid is None:
                receipt.pop("status", None)
            else:
                receipt["status"] = invalid
            self.write_receipt(directory, receipt)
            with self.subTest(status=invalid), self.assertRaisesRegex(project.ProjectError, "invalid status"):
                releases.play_plan(self.root, self.registry, "combined", "reviewed")
            status = releases.release_status(self.root, self.registry, "combined")["profiles"]["combined"]
            self.assertIsNone(status["latest_built"])
            self.assertEqual(status["releases"][0]["status"], "invalid")
            self.assertTrue(status["releases"][0]["errors"])

    def test_source_native_input_and_toolchain_changes_each_block_strict_play(self):
        directory, receipt = self.build()
        cases = [
            (self.root / "pw_disc2.bin", "source disc pw_disc2 changed"),
            (self.root / "xenoiso.exe", "Xenoiso changed"),
            (self.root / "work/donor.bin", "extracted input changed"),
        ]
        for path, expected in cases:
            original = path.read_bytes()
            path.write_bytes(original + b" changed")
            with self.subTest(path=path), self.assertRaisesRegex(project.ProjectError, expected):
                releases.play_plan(self.root, self.registry, "combined", "reviewed")
            path.write_bytes(original)
        self.toolchain = {"sha256": "b" * 64}
        with self.assertRaisesRegex(project.ProjectError, "shared toolchain changed"):
            releases.play_plan(self.root, self.registry, "combined", "reviewed")
        self.toolchain = receipt.pop("toolchain")
        self.write_receipt(directory, receipt)
        with self.assertRaisesRegex(project.ProjectError, "was not recorded"):
            releases.play_plan(self.root, self.registry, "combined", "reviewed")

    def test_invalid_active_registry_and_missing_active_build_are_not_silent(self):
        directory, _ = self.build()
        pointer = self.root / "builds/current.json"
        pointer.write_text(json.dumps({"format": releases.CURRENT_FORMAT, "profiles": {"combined": {"release": "missing"}}}))
        report = releases.release_status(self.root, self.registry, "combined")["profiles"]["combined"]
        self.assertEqual(report["active"]["release"], "missing")
        self.assertTrue(report["active"]["errors"])
        with self.assertRaises(project.ProjectError):
            releases.play_plan(self.root, self.registry, "combined")
        pointer.write_text('{"format":"wrong","profiles":{}}')
        with self.assertRaisesRegex(project.ProjectError, "Invalid active"):
            releases.play_plan(self.root, self.registry, "combined", "reviewed")

    def test_malformed_nested_provenance_is_reported_as_unverifiable(self):
        directory, receipt = self.build()
        receipt["source_snapshot"] = {"shared": None, "modules": []}
        receipt["native_tools"] = {"xenoiso": None}
        receipt["sources"]["pw_disc2"] = None
        self.write_receipt(directory, receipt)
        with self.assertRaisesRegex(project.ProjectError, "stale"):
            releases.play_plan(self.root, self.registry, "combined", "reviewed")
        status = releases.release_status(self.root, self.registry, "combined")["profiles"]["combined"]
        self.assertFalse(status["latest_built"]["fresh"])

    def test_symlinked_media_cannot_escape_release(self):
        directory, receipt = self.build()
        outside = self.root / "foreign.bin"
        outside.write_bytes(b"outside media")
        media = directory / "disc.bin"
        media.unlink()
        try:
            media.symlink_to(outside)
        except OSError:
            self.skipTest("symlink creation unavailable")
        for item in receipt["outputs"]:
            if item["path"] == "disc.bin":
                item.update(project.fingerprint_file(outside))
        self.write_receipt(directory, receipt)
        with self.assertRaisesRegex(project.ProjectError, "escapes"):
            releases.play_plan(self.root, self.registry, "combined", "reviewed")


if __name__ == "__main__":
    unittest.main()
