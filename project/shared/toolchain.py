"""Inventory the current workspace toolchain without loading builders or upgrading tools.

Build receipts can compare ``toolchain_snapshot(...)["sha256"]``. Generated
outputs, release selection, timestamps, and the extracted ``work`` inputs do
not participate in this identity; the project registry records build inputs
and module source identities separately.
"""

from __future__ import annotations

import ast
import hashlib
from importlib import metadata
from importlib.util import resolve_name
import json
from pathlib import Path
import platform
import sys
from typing import Any, Mapping


SNAPSHOT_FORMAT = "xenogears-toolchain-v1"
REPORT_FORMAT = "xenogears-toolchain-report-v1"
IGNORED_DIRECTORIES = {
    "__pycache__", ".git", ".pytest_cache", ".venv", "venv",
    "tests", "test", "work", "archive", "builds", "output",
}
RETIRED_IMPORT_ROOTS = {"tools", "work", "archive", "xenogears_modding_starter"}


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _production_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        (path for path in directory.rglob("*.py")
         if path.is_file()
         and not any(part in IGNORED_DIRECTORIES
                     for part in path.relative_to(directory).parts[:-1])
         and not path.name.startswith("test_")
         and not path.name.endswith("_test.py")),
        key=lambda path: path.relative_to(directory).as_posix(),
    )


def _package_version(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def _executable_identity(root: Path, value: Any) -> dict[str, Any]:
    """Hash a configured local executable; never launch or search for one."""
    identity: dict[str, Any] = {
        "path": value, "resolved_path": None, "exists": False, "sha256": None,
    }
    if value is None:
        return identity
    if not isinstance(value, str) or not value.strip():
        identity["error"] = "Expected a nonempty path string or null"
        return identity
    path = Path(value).expanduser()
    path = (path if path.is_absolute() else root / path).resolve()
    identity["resolved_path"] = str(path)
    identity["exists"] = path.is_file()
    if identity["exists"]:
        identity["sha256"] = _file_digest(path)
    return identity


def toolchain_snapshot(root: Path | str, registry: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic identity of installed tools and shared Python sources.

    Missing optional DuckStation and unavailable Python distributions are
    explicit values, not automatic installation requests. Whether a profile
    requires a dependency is the caller's decision.
    """
    root = Path(root).resolve()
    shared_tools = root / "shared" / "tools"
    sources = [
        {"path": path.relative_to(shared_tools).as_posix(),
         "sha256": _file_digest(path)}
        for path in _production_files(shared_tools)
    ]
    configured = registry.get("tools", {})
    identity: dict[str, Any] = {
        "format": SNAPSHOT_FORMAT,
        "python": {
            "executable": str(Path(sys.executable).resolve()) if sys.executable else None,
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "build": sys.version,
        },
        "packages": {name: _package_version(name) for name in ("Pillow", "numpy", "xxhash")},
        "shared_tools": {
            "path": "shared/tools", "exists": shared_tools.is_dir(),
            "file_count": len(sources), "sha256": _digest(sources),
        },
        "xenoiso": _executable_identity(root, configured.get("xenoiso")),
        "duckstation": _executable_identity(root, configured.get("duckstation")),
    }
    return {**identity, "sha256": _digest(identity)}


def _active_module_directories(root: Path) -> list[Path]:
    """Respect registered archived/scaffold modules; audit unregistered modules too."""
    modules = root / "modules"
    if not modules.is_dir():
        return []
    registry_path = root / "project.json"
    registered: dict[str, Any] = {}
    if registry_path.is_file():
        # Registry validation belongs to the project loader. A malformed
        # registry must not silently hide source files from this audit.
        try:
            value = json.loads(registry_path.read_text(encoding="utf-8-sig"))
            if isinstance(value, dict) and isinstance(value.get("modules"), dict):
                registered = value["modules"]
        except (OSError, UnicodeError, json.JSONDecodeError):
            pass
    result = []
    for directory in sorted(modules.iterdir(), key=lambda path: path.name):
        if not directory.is_dir() or directory.name in IGNORED_DIRECTORIES:
            continue
        module = registered.get(directory.name, {})
        if isinstance(module, dict) and module.get("status") in {"archived", "scaffold"}:
            continue
        result.append(directory)
    return result


def _relative_import(package: str, level: int, name: str) -> str | None:
    try:
        return resolve_name("." * level + name, package)
    except (ImportError, ValueError):
        return None


def _import_targets(tree: ast.AST, package: str):
    """Yield static imports and literal dynamic imports; do not evaluate Python."""
    importlib_aliases = set()
    import_module_aliases = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield node.lineno, alias.name
                if alias.name == "importlib":
                    importlib_aliases.add(alias.asname or "importlib")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level:
                module = _relative_import(package, node.level, module)
            if module:
                yield node.lineno, module
                for alias in node.names:
                    if alias.name != "*":
                        yield node.lineno, f"{module}.{alias.name}"
            if node.level == 0 and node.module == "importlib":
                for alias in node.names:
                    if alias.name == "import_module":
                        import_module_aliases.add(alias.asname or alias.name)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        function = node.func
        direct = isinstance(function, ast.Name) and (
            function.id == "__import__" or function.id in import_module_aliases
        )
        qualified = (isinstance(function, ast.Attribute)
                     and isinstance(function.value, ast.Name)
                     and function.value.id in importlib_aliases
                     and function.attr == "import_module")
        if not (direct or qualified):
            continue
        argument = node.args[0]
        if not isinstance(argument, ast.Constant) or not isinstance(argument.value, str):
            continue
        name = argument.value
        if name.startswith("."):
            package_argument = node.args[1] if len(node.args) > 1 else next(
                (keyword.value for keyword in node.keywords if keyword.arg == "package"),
                None,
            )
            if not isinstance(package_argument, ast.Constant) or not isinstance(package_argument.value, str):
                continue
            try:
                name = resolve_name(name, package_argument.value)
            except (ImportError, ValueError):
                continue
        yield node.lineno, name


def audit_imports(root: Path | str) -> list[str]:
    """Report production imports of retired source trees as ``path:line`` errors.

    Test suites and compatibility wrappers outside ``shared``/``modules`` are
    intentionally outside this check. Imports built from runtime values cannot
    be resolved statically and are not guessed. Syntax/read errors are reported.
    """
    root = Path(root).resolve()
    directories = [root / "shared", *_active_module_directories(root)]
    errors: set[str] = set()
    for directory in directories:
        for path in _production_files(directory):
            relative = path.relative_to(root)
            label = relative.as_posix()
            package = ".".join(relative.parent.parts)
            try:
                tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=label)
            except (OSError, UnicodeError, SyntaxError) as exc:
                line = getattr(exc, "lineno", None) or 1
                errors.add(f"{label}:{line}: cannot parse production Python: {exc}")
                continue
            reported: set[tuple[int, str]] = set()
            for line, target in _import_targets(tree, package):
                retired = target.split(".", 1)[0]
                if retired not in RETIRED_IMPORT_ROOTS or (line, retired) in reported:
                    continue
                reported.add((line, retired))
                errors.add(f"{label}:{line}: retired import {target!r}; use shared.tools or the owning modules package")
    return sorted(errors)


_CAPABILITIES = (
    ("disc", "Read canonical disc resources, build images, and verify Mode 2 boot sectors", (
        ("shared/tools/xgdisc.py", ("Mode2Image",)),
        ("shared/tools/xenoiso_build.py", ("command_build", "command_list_bytes")),
        ("shared/tools/xgmode2.py", ("verify_retail_title_boot", "regenerate_mode2_form1")),
    )),
    ("fields", "Parse and repack field bundles while preserving unchanged components", (
        ("shared/tools/xgfield.py", ("parse_field", "build_field_preserving")),
    )),
    ("dialogue", "Encode, inspect, and replace native dialogue blocks", (
        ("shared/tools/xgdialog.py", ("parse_dialogue", "encode_dialogue", "replace_dialogue")),
        ("shared/tools/xgdialog_name_color.py", ("patch_executable", "verify_executable_image")),
    )),
    ("atel", "Edit script entry points, decode bytecode, and encode checked variable operations", (
        ("shared/tools/xgscript.py", ("AtelScript",)),
        ("shared/tools/xgatel.py", ("decode_instruction", "reachable_instructions")),
        ("shared/tools/atel_primitives.py", ("set_var_bit", "copy_variable", "variable_math")),
    )),
    ("graphics", "Convert TIM images and inspect field props and thumbnail atlases", (
        ("shared/tools/xgtim.py", ("convert_png_to_bytes", "validate_tim")),
        ("shared/tools/render_xg_field_props.py", ("render_parts",)),
        ("shared/tools/build_field_thumbnail_atlas.py", ("make_page",)),
    )),
    ("battles", "Edit encounter tables, weight mechanics, and learned deathblows", (
        ("shared/tools/xgencounter.py", ("EncounterTable",)),
        ("shared/tools/xgbattle_weight.py", ("patch_decoded_battle_overlay",)),
        ("shared/tools/xgdeathblows.py", ("grant_all_on_foot_deathblows",)),
    )),
)

_MODULE_HELPERS = (
    ("mass_driver", "modules/mass_driver/build.py",
     "Scene routines, camera and dialogue staging, and fixed battles",
     ("_RoutineBuilder", "_change_field", "_fixed_battle", "_dialogue_sequence")),
    ("soylent_system", "modules/soylent_system/base.py",
     "Donor-party adaptation and walkmesh geometry",
     ("_patch_donor_party", "_point_inside_triangle", "_walkmesh_layer")),
    ("rico", "modules/rico/build.py",
     "Chapter loading and canonical replacements for both discs",
     ("DiscReader", "load_chapters", "prepare_replacements")),
    ("rico", "modules/rico/chapter_two.py",
     "Chapter 2 state graph and room construction",
     ("validate_graph", "build_room")),
)


def toolchain_report(root: Path | str, registry: Mapping[str, Any]) -> dict[str, Any]:
    """Describe installed provenance and existing capabilities for doctor/help UIs."""
    root = Path(root).resolve()

    def source(path: str, symbols: tuple[str, ...]) -> dict[str, Any]:
        return {"path": path, "import": path.removesuffix(".py").replace("/", "."),
                "symbols": list(symbols), "exists": (root / path).is_file()}

    return {
        "format": REPORT_FORMAT,
        "snapshot": toolchain_snapshot(root, registry),
        "capabilities": [
            {"id": name, "description": description,
             "sources": [source(path, symbols) for path, symbols in sources]}
            for name, description, sources in _CAPABILITIES
        ],
        "module_helpers": [
            {"module": module, "description": description, **source(path, symbols)}
            for module, path, description, symbols in _MODULE_HELPERS
        ],
        "import_audit": audit_imports(root),
        "notes": [
            "Use the current workspace sources; this report does not check for or install external upgrades.",
            "Module-owned helpers retain their owning module path; declare build_dependencies when reusing them.",
            "DuckStation is optional for building; its configured executable is recorded without launching it.",
            "Bytecode decoding and field rendering may require the donor metadata/assets requested by those tools.",
        ],
    }
