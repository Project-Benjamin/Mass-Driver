"""Build planning and provenance checks without invoking game-data builders."""

from copy import deepcopy
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from shared import project_registry as registry


PROJECT = Path(__file__).resolve().parent.parent


class ProjectRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="xgregistry_")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.document = json.loads((PROJECT / "project.json").read_text(encoding="utf-8"))
        (self.root / "shared" / "tools").mkdir(parents=True)
        (self.root / "shared" / "resources.json").write_text('{"format":"test-ledger"}')
        (self.root / "shared" / "tools" / "xgdialog.py").write_text("TOKEN = 1\n")
        (self.root / "shared" / "tools" / "build_combined.py").write_text("def main(argv): return 0\n")
        (self.root / "project.py").write_text("# fixture entrypoint\n")
        (self.root / "work").mkdir()
        (self.root / "Xenoiso.exe").write_bytes(b"fixture-tool")
        self.document["tools"] = {"input_root": "work", "xenoiso": "Xenoiso.exe"}
        for source_id, source in self.document["sources"].items():
            filename = f"{source_id}.bin"
            payload = source_id.encode("ascii")
            (self.root / filename).write_bytes(payload)
            source.update(path=filename, sha256=hashlib.sha256(payload).hexdigest())
        for module in self.document["modules"].values():
            directory = self.root / module["path"]
            (directory / "content").mkdir(parents=True)
            (directory / "content" / "manifest.json").write_text('{"fixture":true}\n')
            (directory / "build.py").write_text("def main(argv): return 0\n")
        self.save()

    def save(self):
        (self.root / "project.json").write_text(json.dumps(self.document), encoding="utf-8")

    def test_plans_use_canonical_current_builders_and_correct_donor_sources(self):
        document = registry.load_registry(self.root)
        mass = registry.build_plan(self.root, document, "mass_driver", prepare_only=True)
        combined = registry.build_plan(self.root, document, "combined", release="v200")
        soylent = registry.build_plan(self.root, document, "soylent_system", prepare_only=True)
        rico = registry.build_plan(self.root, document, "rico", prepare_only=True)
        self.assertEqual(mass["command"][1:3], ["-m", "modules.mass_driver.build"])
        self.assertEqual(combined["modules"], ["mass_driver", "soylent_system", "rico"])
        self.assertEqual(combined["command"][2], "shared.tools.build_combined")
        self.assertEqual(combined["output"], str(self.root / "builds/combined/v200"))
        self.assertEqual(combined["stage"], str(self.root / "builds/combined/v200/stage"))
        self.assertIn(str(self.root / "modules/mass_driver/content"), combined["command"])
        self.assertIn("--disc2-source", combined["command"])
        self.assertIn("--rico-disc1", combined["command"])
        source_index = soylent["command"].index("--source-disc") + 1
        self.assertEqual(soylent["command"][source_index], str(self.root / "mass_driver_base.bin"))
        self.assertIn("--prepare-only", rico["command"])
        stage_index = rico["command"].index("--stage-directory") + 1
        self.assertEqual(rico["command"][stage_index], "stage")
        self.assertFalse((self.root / "builds").exists())

    def test_local_overrides_legacy_and_source_hashes_are_checked(self):
        (self.root / "config.local.json").write_text(json.dumps({"disc2_source": "wrong.bin"}))
        (self.root / "project.local.json").write_text(json.dumps({
            "sources": {"pw_disc2": {"path": "pw_disc2.bin"}}
        }))
        document = registry.load_registry(self.root)
        sources, warnings = registry.inspect_sources(self.root, document, ["pw_disc2", "mass_driver_base"])
        self.assertEqual(warnings, [])
        self.assertEqual(sources["pw_disc2"]["path"], str(self.root / "pw_disc2.bin"))
        self.assertEqual(sources["mass_driver_base"]["provenance"]["module"], "mass_driver")
        (self.root / "pw_disc2.bin").write_bytes(b"changed-source")
        with self.assertRaisesRegex(registry.ProjectError, "SHA-256 mismatch"):
            registry.inspect_sources(self.root, document, ["pw_disc2"])
        report = registry.doctor(self.root, document)
        self.assertFalse(report["ok"])
        self.assertEqual(len(report["errors"]), 1)

    def test_definitive_plan_uses_retail_pair_and_pinned_options_only(self):
        document = registry.load_registry(self.root)
        selection = self.root / 'modules/definitive/content/chosen.json'
        selection.write_text('{}')
        plan = registry.build_plan(self.root, document, 'definitive',
                                   patch_options='modules/definitive/content/chosen.json')
        self.assertEqual(plan['modules'], ['definitive'])
        self.assertEqual(plan['build_dependency_modules'], [])
        self.assertEqual(plan['source_ids'], ['retail_disc1', 'retail_disc2'])
        self.assertIsNone(plan['disc_output'])
        command = plan['command']
        self.assertEqual(command[command.index('--options') + 1], str(selection))
        self.assertNotIn('--story-manifest', command)
        with self.assertRaisesRegex(registry.ProjectError, 'only'):
            registry.build_plan(self.root, document, 'rico', patch_options='modules/definitive/content/chosen.json')
        with self.assertRaises(registry.ProjectError):
            registry.build_plan(self.root, document, 'definitive', patch_options='modules/rico/content/manifest.json')

    def test_registry_rejects_unknown_sources_disabled_modules_and_bad_hashes(self):
        for change, message in (
            (lambda d: d["profiles"]["combined"]["source_ids"].append("typo"), "unknown source IDs"),
            (lambda d: d["modules"]["rico"].update(enabled=False), "disabled module"),
            (lambda d: d["sources"]["pw_disc1"].update(sha256="abc"), "64 hexadecimal"),
            (lambda d: d["modules"]["rico"].update(status="scaffold"), "Only active"),
            (lambda d: d["profiles"]["combined"].update(modules=["mass_driver"]), "disagrees"),
        ):
            with self.subTest(message=message):
                document = deepcopy(self.document)
                change(document)
                with self.assertRaisesRegex(registry.ProjectError, message):
                    registry.validate_registry(self.root, document)

    def test_traversal_reserved_names_existing_output_and_junction_escape_are_rejected(self):
        document = registry.load_registry(self.root)
        for release in ("../outside", "..", "C:/outside", "a/b", "a\\b", "CON", "bad."):
            with self.subTest(release=release), self.assertRaises(registry.ProjectError):
                registry.build_plan(self.root, document, "mass_driver", release=release, prepare_only=True)
        destination = self.root / "builds/mass_driver/current"
        destination.mkdir(parents=True)
        with self.assertRaisesRegex(registry.ProjectError, "already exists"):
            registry.build_plan(self.root, document, "mass_driver", prepare_only=True)
        registry.build_plan(self.root, document, "mass_driver", prepare_only=True, force=True)
        document["build_root"] = "../outside"
        with self.assertRaises(registry.ProjectError):
            registry.validate_registry(self.root, document)
        outside = self.root / "outside"
        outside.mkdir()
        link = self.root / "builds/combined"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            return  # Some Windows test runners cannot create symlinks.
        with self.assertRaisesRegex(registry.ProjectError, "escapes"):
            registry.build_plan(self.root, self.document, "combined", prepare_only=True)

    def test_whitespace_paths_survive_planning_for_staging_and_disc_builds(self):
        document = deepcopy(self.document)
        document["sources"]["pw_disc2"]["path"] = "source with spaces.bin"
        document["tools"]["xenoiso"] = "tools with spaces/Xenoiso.exe"
        document["build_root"] = "builds with spaces"
        for prepare_only in (True, False):
            plan = registry.build_plan(self.root, document, "combined", prepare_only=prepare_only)
            self.assertIn(str(self.root / "source with spaces.bin"), plan["command"])
            self.assertEqual(plan["output"], str(self.root / "builds with spaces/combined/current"))
            if not prepare_only:
                self.assertIn(str(self.root / "tools with spaces/Xenoiso.exe"), plan["command"])
        document["sources"]["retail_disc1"]["path"] = "retail source with spaces.bin"
        rico = registry.build_plan(self.root, document, "rico")
        self.assertIn(str(self.root / "retail source with spaces.bin"), rico["command"])

    def test_snapshot_changes_when_module_or_shared_inputs_change_and_ignores_cache(self):
        first = registry.source_snapshot(self.root, self.document, "combined")
        (self.root / "modules/rico/content/manifest.json").write_text('{"fixture":false}\n')
        second = registry.source_snapshot(self.root, self.document, "combined")
        self.assertNotEqual(first["modules"]["rico"]["sha256"], second["modules"]["rico"]["sha256"])
        self.assertEqual(first["modules"]["mass_driver"], second["modules"]["mass_driver"])
        (self.root / "shared/tools/xgdialog.py").write_text("TOKEN = 2\n")
        third = registry.source_snapshot(self.root, self.document, "combined")
        self.assertNotEqual(second["shared"]["sha256"], third["shared"]["sha256"])
        cache = self.root / "shared/__pycache__"
        cache.mkdir()
        (cache / "generated.pyc").write_bytes(b"cache")
        self.assertEqual(third, registry.source_snapshot(self.root, self.document, "combined"))

    def test_scaffold_is_disabled_and_cannot_enter_existing_build_profiles(self):
        original_profiles = deepcopy(self.document["profiles"])
        directory = registry.scaffold_module(self.root, "future_chapter", "Future chapter")
        document = registry.load_registry(self.root)
        self.assertEqual(document["profiles"], original_profiles)
        module = document["modules"]["future_chapter"]
        self.assertFalse(module["enabled"])
        self.assertEqual(module["status"], "scaffold")
        for name in ("content", "assets", "docs", "tests", "build.py", "module.json", "README.md"):
            self.assertTrue((directory / name).exists())
        with self.assertRaisesRegex(registry.ProjectError, "Unknown build profile"):
            registry.build_plan(self.root, document, "future_chapter", prepare_only=True)
        with self.assertRaisesRegex(registry.ProjectError, "already registered"):
            registry.scaffold_module(self.root, "future_chapter", "Again")
        self.assertNotIn("future_chapter", registry.source_snapshot(self.root, document, "combined")["modules"])

    def test_implementation_dependencies_are_transitive_and_change_snapshot_without_selecting_content(self):
        # Rico can reach Mass Driver implementation through Soylent's base
        # even without listing Mass Driver as a direct dependency.
        self.document["modules"]["rico"]["build_dependencies"] = ["soylent_system"]
        first = registry.source_snapshot(self.root, self.document, "rico")
        self.assertEqual(first["selected_modules"], ["rico"])
        self.assertEqual(first["build_dependency_modules"], ["soylent_system", "mass_driver"])
        self.assertEqual(first["modules"]["mass_driver"]["role"], "build_dependency")
        self.assertEqual(first["modules"]["rico"]["role"], "selected_module")
        (self.root / "modules/mass_driver/build.py").write_text("# changed shared implementation\n")
        second = registry.source_snapshot(self.root, self.document, "rico")
        self.assertEqual(first["modules"]["rico"]["sha256"], second["modules"]["rico"]["sha256"])
        self.assertNotEqual(first["sha256"], second["sha256"])
        self.assertNotEqual(first["modules"]["mass_driver"]["sha256"],
                            second["modules"]["mass_driver"]["sha256"])
        self.document["modules"]["mass_driver"]["build_dependencies"] = ["rico"]
        with self.assertRaisesRegex(registry.ProjectError, "dependency cycle"):
            registry.validate_registry(self.root, self.document)

    def fake_completed_builder(self, command, cwd, check):
        # Produce the receipt expected from the isolated audit wrapper.
        receipt = Path(command[6])
        receipt.write_text(json.dumps({
            "format": "xenogears-consumed-inputs-v1",
            "input_root": str(self.root / "work"), "files": [], "sha256": registry._digest([]),
            "error": None,
        }))
        (receipt.parent / "stage").mkdir()
        (receipt.parent / "stage/manifest.json").write_text('{"prepared":true}\n')
        return subprocess.CompletedProcess(command, 0)

    def test_build_records_provenance_and_force_preserves_previous_release(self):
        plan = registry.build_plan(self.root, self.document, "combined", prepare_only=True)
        with patch.object(registry.subprocess, "run", side_effect=self.fake_completed_builder):
            self.assertEqual(registry.execute_build(self.root, self.document, plan), 0)
        manifest_path = Path(plan["output"]) / "project-build.json"
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["status"], "prepared")
        self.assertNotIn("native_tools", manifest)
        self.assertEqual(set(manifest["source_snapshot"]["modules"]), {"mass_driver", "soylent_system", "rico"})
        self.assertEqual(set(manifest["sources"]), {"pw_disc1", "pw_disc2", "retail_disc1"})
        old_manifest = manifest_path.read_bytes()
        forced = registry.build_plan(self.root, self.document, "combined", prepare_only=True, force=True)
        with patch.object(registry.subprocess, "run", side_effect=self.fake_completed_builder):
            registry.execute_build(self.root, self.document, forced)
        replaced = list((self.root / "builds/combined").glob("current.replaced-*"))
        self.assertEqual(len(replaced), 1)
        self.assertEqual((replaced[0] / "project-build.json").read_bytes(), old_manifest)

    def test_full_build_records_native_tool_and_rejects_changes_during_execution(self):
        executable = self.root / "Xenoiso.exe"
        identity = {"path": str(executable), "size": len(b"fixture-tool"),
                    "sha256": hashlib.sha256(b"fixture-tool").hexdigest()}
        plan = registry.build_plan(self.root, self.document, "combined", release="stable")
        with patch.object(registry.subprocess, "run", side_effect=self.fake_completed_builder):
            registry.execute_build(self.root, self.document, plan)
        manifest = json.loads((Path(plan["output"]) / "project-build.json").read_text())
        self.assertEqual(manifest["status"], "built")
        self.assertEqual(manifest["native_tools"], {"xenoiso": identity})

        plan = registry.build_plan(self.root, self.document, "combined", release="changed")
        def changing_builder(*args, **kwargs):
            result = self.fake_completed_builder(*args, **kwargs)
            executable.write_bytes(b"changed-native-disc-writer")
            return result
        with patch.object(registry.subprocess, "run", side_effect=changing_builder):
            with self.assertRaisesRegex(registry.ProjectError, "Native tool xenoiso changed"):
                registry.execute_build(self.root, self.document, plan)
        manifest = json.loads((Path(plan["output"]) / "project-build.json").read_text())
        self.assertEqual(manifest["status"], "failed")
        self.assertEqual(manifest["native_tools"], {"xenoiso": identity})

    def test_source_change_during_builder_execution_marks_output_failed(self):
        plan = registry.build_plan(self.root, self.document, "combined", prepare_only=True)
        def changing_builder(*args, **kwargs):
            result = self.fake_completed_builder(*args, **kwargs)
            (self.root / "modules/mass_driver/build.py").write_text("# changed during build\n")
            return result
        with patch.object(registry.subprocess, "run", side_effect=changing_builder):
            with self.assertRaisesRegex(registry.ProjectError, "changed during the build"):
                registry.execute_build(self.root, self.document, plan)
        manifest = json.loads((Path(plan["output"]) / "project-build.json").read_text())
        self.assertEqual(manifest["status"], "failed")

    def test_read_audit_records_only_consumed_original_extracted_files(self):
        donor = self.root / "work/donor.bin"
        donor.write_bytes(b"original-donor")
        builder = self.root / "audit_fixture_builder.py"
        builder.write_text(
            "from pathlib import Path\n"
            "def main(argv):\n"
            "    p = Path(argv[0])\n"
            "    (p / 'donor.bin').read_bytes()\n"
            "    (p / 'new-cache.bin').write_bytes(b'cache')\n"
            "    (p / 'new-cache.bin').read_bytes()\n"
            "    return 0\n"
        )
        receipt = self.root / "receipt.json"
        env = dict(os.environ, PYTHONPATH=str(self.root))
        completed = subprocess.run([
            sys.executable, str(Path(registry.__file__).resolve()), "_run-builder",
            "audit_fixture_builder", str(self.root / "work"), str(receipt), str(self.root / "work")
        ], cwd=self.root, env=env, capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        recorded = json.loads(receipt.read_text())
        self.assertEqual(recorded["error"], None)
        self.assertEqual([item["path"] for item in recorded["files"]], ["donor.bin"])
        self.assertEqual(recorded["files"][0]["sha256"], hashlib.sha256(b"original-donor").hexdigest())

    def test_test_plan_includes_shared_and_transitive_dependencies_once(self):
        for directory, filename in (
            ("shared/tests", "test_shared.py"),
            ("modules/mass_driver/tests", "test_mass.py"),
            ("modules/soylent_system/tests", "test_soylent.py"),
            ("modules/rico/tests", "test_rico.py"),
            ("tests", "test_project_registry.py"),
        ):
            path = self.root / directory / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# fixture test\n")
        command = registry.test_plan(self.root, self.document, "rico")
        self.assertEqual(command[:3], [sys.executable, "-m", "unittest"])
        self.assertEqual(set(command[3:]), {
            "shared.tests.test_shared", "modules.mass_driver.tests.test_mass",
            "modules.soylent_system.tests.test_soylent", "modules.rico.tests.test_rico",
            "tests.test_project_registry",
        })
        self.assertEqual(len(command[3:]), len(set(command[3:])))
        mass = registry.test_plan(self.root, self.document, "mass_driver")
        self.assertNotIn("modules.rico.tests.test_rico", mass)
        self.assertNotIn("modules.soylent_system.tests.test_soylent", mass)

    def test_launch_check_uses_configured_emulator_and_never_opens_it(self):
        executable = self.root / "Emulator With Spaces.exe"
        executable.write_bytes(b"fixture-emulator")
        self.document["tools"]["duckstation"] = str(executable)
        media = self.root / "builds/rico/latest/paired.m3u"
        launch = {"profile":"rico", "release":"latest", "media":str(media), "runtime_status":"untested"}
        with patch("shared.project_releases.play_plan", return_value=launch) as check, \
                patch.object(registry.subprocess, "Popen") as spawn, redirect_stdout(io.StringIO()):
            plan = registry.play_release(self.root, self.document, "rico", check_only=True)
            spawn.assert_not_called()
            check.assert_called_once_with(self.root, self.document, "rico", None, allow_stale=False)
        self.assertEqual(plan["command"], [str(executable), "-batch", "-fastboot", "--", str(media)])

    def test_cli_rejects_stale_default_launch_and_prepared_activation(self):
        with redirect_stderr(io.StringIO()), patch.object(registry.subprocess, "Popen") as spawn:
            self.assertEqual(registry.main(["play", "rico", "--allow-stale"], root=self.root), 2)
            self.assertEqual(registry.main(["build", "rico", "--prepare-only", "--activate"], root=self.root), 2)
            spawn.assert_not_called()
        self.assertFalse((self.root / "builds").exists())

    def test_failed_build_does_not_activate(self):
        from shared import project_releases
        with patch.object(registry, "execute_build", return_value=1), \
                patch.object(project_releases, "activate_release") as activate:
            self.assertEqual(registry.main(["build", "rico", "--activate"], root=self.root), 1)
            activate.assert_not_called()

    def test_new_build_receipt_records_shared_toolchain_and_content_versions(self):
        plan = registry.build_plan(self.root, self.document, "combined", prepare_only=True)
        with patch.object(registry.subprocess, "run", side_effect=self.fake_completed_builder), redirect_stdout(io.StringIO()):
            registry.execute_build(self.root, self.document, plan)
        receipt = json.loads((Path(plan["output"]) / "project-build.json").read_text())
        self.assertEqual(receipt["content_versions"], {
            name: self.document["modules"][name]["content_version"] for name in plan["modules"]
        })
        self.assertEqual(receipt["toolchain"]["python"]["executable"], sys.executable)
        self.assertIn("Pillow", receipt["toolchain"]["packages"])

    def test_force_cannot_replace_active_release_even_after_planning(self):
        from shared.project_releases import CURRENT_FORMAT
        directory = self.root / "builds/rico/stable"
        directory.mkdir(parents=True)
        media = directory / "disc.bin"
        media.write_bytes(b"active build must survive")
        plan = registry.build_plan(self.root, self.document, "rico", release="stable", force=True)
        pointer = self.root / "builds/current.json"
        pointer.write_text(json.dumps({"format":CURRENT_FORMAT, "profiles":{"rico":{"release":"stable"}}}))
        original = pointer.read_bytes()
        with self.assertRaisesRegex(registry.ProjectError, "Cannot replace active release"):
            registry.build_plan(self.root, self.document, "rico", release="stable", force=True)
        with patch.object(registry.subprocess, "run") as builder:
            with self.assertRaisesRegex(registry.ProjectError, "Cannot replace active release"):
                registry.execute_build(self.root, self.document, plan)
            builder.assert_not_called()
        self.assertEqual(media.read_bytes(), b"active build must survive")
        self.assertEqual(pointer.read_bytes(), original)
        self.assertEqual(list(directory.parent.glob("stable.replaced-*")), [])


if __name__ == "__main__":
    unittest.main()
