"""Toolchain provenance and production import boundaries, without running builders."""

import ast
import hashlib
from importlib import metadata
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from shared import toolchain


PROJECT = Path(__file__).resolve().parents[1]


class ToolchainTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="xgtoolchain_")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.registry = {"tools": {"xenoiso": "bin/xenoiso.exe", "duckstation": None}}
        self.write("shared/tools/xgfield.py", "def parse_field(data): return data\n")
        self.write("modules/story/build.py", "from shared.tools import xgfield\n")
        executable = self.root / "bin/xenoiso.exe"
        executable.parent.mkdir()
        executable.write_bytes(b"local xenoiso fixture")
        self.versions = {"Pillow": "12.1.0", "numpy": "2.4.0", "xxhash": "4.0.1"}
        package_versions = patch.object(toolchain.metadata, "version", side_effect=self.version)
        package_versions.start()
        self.addCleanup(package_versions.stop)

    def version(self, name):
        if name not in self.versions:
            raise metadata.PackageNotFoundError(name)
        return self.versions[name]

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def snapshot(self):
        return toolchain.toolchain_snapshot(self.root, self.registry)

    def test_identity_is_deterministic_and_hashes_canonical_identity(self):
        first = self.snapshot()
        second = self.snapshot()
        self.assertEqual(first, second)
        identity = {key: value for key, value in first.items() if key != "sha256"}
        encoded = json.dumps(identity, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":")).encode("utf-8")
        self.assertEqual(first["sha256"], hashlib.sha256(encoded).hexdigest())
        self.assertEqual(first["shared_tools"]["path"], "shared/tools")
        self.assertEqual(first["shared_tools"]["file_count"], 1)
        self.assertEqual(first["packages"], self.versions)
        self.assertTrue(first["python"]["executable"])
        self.assertTrue(first["python"]["version"])
        self.assertTrue(first["python"]["implementation"])

    def test_installed_package_version_change_invalidates_fingerprint(self):
        before = self.snapshot()
        self.versions["Pillow"] = "12.2.0"
        after = self.snapshot()
        self.assertNotEqual(before["sha256"], after["sha256"])
        self.assertEqual(before["shared_tools"], after["shared_tools"])
        self.assertEqual(after["packages"]["Pillow"], "12.2.0")

    def test_missing_packages_and_optional_emulator_are_explicit(self):
        self.versions.clear()
        result = self.snapshot()
        self.assertEqual(result["packages"], {"Pillow": None, "numpy": None, "xxhash": None})
        self.assertEqual(result["duckstation"], {
            "path": None, "resolved_path": None, "exists": False, "sha256": None,
        })
        self.registry["tools"]["duckstation"] = "missing/duckstation.exe"
        configured = self.snapshot()["duckstation"]
        self.assertFalse(configured["exists"])
        self.assertIsNone(configured["sha256"])
        self.assertEqual(configured["resolved_path"], str(self.root / "missing/duckstation.exe"))

    def test_native_tool_replacement_changes_identity_without_executing_tool(self):
        before = self.snapshot()
        self.assertEqual(before["xenoiso"]["sha256"], hashlib.sha256(b"local xenoiso fixture").hexdigest())
        (self.root / "bin/xenoiso.exe").write_bytes(b"new local xenoiso fixture")
        after = self.snapshot()
        self.assertNotEqual(before["sha256"], after["sha256"])
        self.registry["tools"]["duckstation"] = "bin/duckstation.exe"
        (self.root / "bin/duckstation.exe").write_bytes(b"emulator fixture")
        emulator = self.snapshot()
        self.assertTrue(emulator["duckstation"]["exists"])
        self.assertEqual(emulator["duckstation"]["sha256"], hashlib.sha256(b"emulator fixture").hexdigest())
        self.assertNotEqual(after["sha256"], emulator["sha256"])

    def test_source_edits_change_identity_but_generated_outputs_and_selection_do_not(self):
        before = self.snapshot()
        self.write("shared/tools/tests/test_example.py", "import tools.xgfield\n")
        self.write("shared/tools/__pycache__/cached.py", "old = True\n")
        self.write("work/research.py", "old = True\n")
        self.write("builds/combined/new/stage/build.py", "generated = True\n")
        self.registry["active_release"] = "new"
        self.assertEqual(before, self.snapshot())
        self.write("shared/tools/xgfield.py", "def parse_field(data): return bytes(data)\n")
        after = self.snapshot()
        self.assertNotEqual(before["shared_tools"]["sha256"], after["shared_tools"]["sha256"])
        self.assertNotEqual(before["sha256"], after["sha256"])

    def test_audit_rejects_each_retired_absolute_import_root_with_locations(self):
        self.write("modules/story/build.py", (
            "import tools.xgfield\n"
            "from work import donor\n"
            "from archive.repair import patch\n"
            "import xenogears_modding_starter.tools.reader\n"
        ))
        errors = toolchain.audit_imports(self.root)
        self.assertEqual(len(errors), 4)
        for line in range(1, 5):
            self.assertTrue(any(error.startswith(f"modules/story/build.py:{line}:") for error in errors))

    def test_audit_checks_literal_dynamic_imports_and_aliases(self):
        self.write("shared/tools/dynamic.py", (
            "import importlib as loader\n"
            "from importlib import import_module as load\n"
            "loader.import_module('work.donor')\n"
            "load('archive.repair')\n"
            "__import__('tools.xgfield')\n"
            "load('.xgfield', package='tools')\n"
        ))
        errors = toolchain.audit_imports(self.root)
        self.assertEqual(len(errors), 4)
        for line in range(3, 7):
            self.assertTrue(any(error.startswith(f"shared/tools/dynamic.py:{line}:") for error in errors))

    def test_audit_allows_canonical_relative_imports_and_does_not_guess_strings(self):
        self.write("modules/story/tools/build.py", (
            "from shared.tools import xgfield\n"
            "from .. import build\n"
            "from . import helpers\n"
            "from ...mass_driver import build as mass\n"
            "import archive_utils\n"
            "import importlib\n"
            "description = 'import tools.xgfield'\n"
            "# from work import donor\n"
            "importlib.import_module(description)\n"
            "importlib.import_module('.xgfield', 'shared.tools')\n"
        ))
        self.assertEqual(toolchain.audit_imports(self.root), [])

    def test_audit_excludes_tests_wrappers_archived_and_scaffold_modules(self):
        for path in (
            "tests/test_compatibility.py", "tools/compatibility.py",
            "shared/tests/test_compatibility.py", "modules/story/tests/test_old.py",
            "modules/story/tools/test_old.py", "modules/retired/build.py",
            "modules/future/build.py", "work/research.py", "archive/repair.py",
        ):
            self.write(path, "import tools.xgfield\n")
        self.write("project.json", json.dumps({"modules": {
            "story": {"status": "active"}, "retired": {"status": "archived"},
            "future": {"status": "scaffold"},
        }}))
        self.assertEqual(toolchain.audit_imports(self.root), [])
        self.write("modules/unregistered/build.py", "import tools.xgfield\n")
        self.assertEqual(len(toolchain.audit_imports(self.root)), 1)

    def test_audit_reports_syntax_errors_instead_of_skipping_source(self):
        self.write("modules/story/broken.py", "def broken(:\n")
        errors = toolchain.audit_imports(self.root)
        self.assertEqual(len(errors), 1)
        self.assertIn("modules/story/broken.py:1: cannot parse production Python", errors[0])

    def test_report_references_existing_source_symbols_without_loading_builders(self):
        report = toolchain.toolchain_report(PROJECT, {"tools": {}})
        self.assertEqual(report["format"], toolchain.REPORT_FORMAT)
        self.assertEqual({item["id"] for item in report["capabilities"]}, {
            "disc", "fields", "dialogue", "atel", "graphics", "battles",
        })
        sources = [source for item in report["capabilities"] for source in item["sources"]]
        sources.extend(report["module_helpers"])
        for source in sources:
            self.assertTrue(source["exists"], source["path"])
            tree = ast.parse((PROJECT / source["path"]).read_text(encoding="utf-8-sig"))
            definitions = {node.name for node in tree.body
                           if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
            self.assertTrue(set(source["symbols"]).issubset(definitions), source)
            self.assertTrue(source["import"].startswith(("shared.tools.", "modules.")))


if __name__ == "__main__":
    unittest.main()
