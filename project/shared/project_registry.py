"""Project registry and build orchestration; imports no game builder on discovery."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Sequence


FORMAT = "xenogears-project-v1"
MANIFEST_FORMAT = "xenogears-project-build-v1"
MODULE_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")
RELEASE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)
}
ADAPTER_SOURCES = {
    "definitive": {"retail_disc1", "retail_disc2"},
    "mass_driver": {"pw_disc2"},
    "soylent_system": {"pw_disc1", "mass_driver_base"},
    "rico": {"retail_disc1", "retail_disc2"},
    "combined": {"pw_disc1", "pw_disc2", "retail_disc1"},
}
IGNORED_DIRECTORIES = {"__pycache__", ".git", ".pytest_cache", ".venv"}


class ProjectError(ValueError):
    """A configuration, provenance, or build-safety check failed."""


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProjectError(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProjectError(f"Expected a JSON object: {path}")
    return value


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _validate_name(value: str, *, release: bool = False) -> str:
    pattern = RELEASE_PATTERN if release else MODULE_PATTERN
    if not isinstance(value, str) or not pattern.fullmatch(value):
        label = "Release" if release else "Module/profile"
        raise ProjectError(f"{label} name must be a simple name, without path separators: {value!r}")
    if value.endswith(".") or value.split(".", 1)[0].upper() in RESERVED_NAMES:
        raise ProjectError(f"Name is reserved or ambiguous on Windows: {value!r}")
    return value


def contained_path(parent: Path, value: str | Path, *, allow_parent: bool = False) -> Path:
    """Resolve junctions/symlinks and require a strict descendant of parent."""
    parent = parent.resolve()
    value = Path(value)
    resolved = (value if value.is_absolute() else parent / value).resolve()
    if not resolved.is_relative_to(parent) or (resolved == parent and not allow_parent):
        raise ProjectError(f"Path escapes its allowed directory {parent}: {resolved}")
    return resolved


def _project_path(root: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ProjectError(f"Registry paths must be nonempty project-relative paths: {value!r}")
    # Reject traversal even when normalization would happen to land in root.
    if ".." in Path(value).parts or "\\" in value:
        raise ProjectError(f"Use a project-relative path without traversal: {value!r}")
    return contained_path(root, value)


def configured_path(root: Path, value: Any, description: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ProjectError(f"Configure {description} in project.local.json")
    path = Path(value).expanduser()
    return (path if path.is_absolute() else root / path).resolve()


def validate_registry(root: Path, registry: dict[str, Any], *, check_files: bool = True) -> None:
    root = root.resolve()
    if registry.get("format") != FORMAT:
        raise ProjectError(f"project.json must declare format {FORMAT!r}")
    sources = registry.get("sources")
    modules = registry.get("modules")
    profiles = registry.get("profiles")
    if not all(isinstance(value, dict) and value for value in (sources, modules, profiles)):
        raise ProjectError("Registry sources, modules, and profiles must be nonempty objects")
    _project_path(root, registry.get("build_root"))
    ledger = _project_path(root, registry.get("resource_ledger"))
    if check_files:
        _json(ledger)
    for source_id, source in sources.items():
        _validate_name(source_id)
        if not isinstance(source, dict) or source.get("kind") != "disc":
            raise ProjectError(f"Source {source_id} must be a disc object")
        if source.get("path") is not None and not isinstance(source["path"], str):
            raise ProjectError(f"Source {source_id} path must be a string or null")
        expected = source.get("sha256")
        if expected is not None and (
            not isinstance(expected, str) or re.fullmatch(r"[0-9a-fA-F]{64}", expected) is None
        ):
            raise ProjectError(f"Source {source_id} SHA-256 must contain exactly 64 hexadecimal digits")
    if not isinstance(registry.get("tools"), dict):
        raise ProjectError("Registry tools must be an object")
    for slug, module in modules.items():
        _validate_name(slug)
        if not isinstance(module, dict) or not isinstance(module.get("enabled"), bool):
            raise ProjectError(f"Module {slug} must declare enabled: true or false")
        if module.get("status") not in ("active", "scaffold", "archived"):
            raise ProjectError(f"Module {slug} has an unsupported status")
        if module["enabled"] and module["status"] != "active":
            raise ProjectError(f"Only active modules may be enabled: {slug}")
        directory = _project_path(root, module.get("path"))
        expected_directory = contained_path(root, f"modules/{slug}")
        if directory != expected_directory:
            raise ProjectError(f"Module {slug} must live in modules/{slug}")
        builder = _project_path(root, module.get("builder"))
        content = _project_path(root, module.get("content"))
        if not builder.is_relative_to(directory) or not content.is_relative_to(directory):
            raise ProjectError(f"Module {slug} builder/content must stay inside its module directory")
        _validate_source_ids(module.get("source_ids"), sources, f"module {slug}", allow_empty=True)
        dependencies = module.get("build_dependencies", [])
        if (not isinstance(dependencies, list)
                or any(not isinstance(item, str) for item in dependencies)
                or len(set(dependencies)) != len(dependencies)):
            raise ProjectError(f"Module {slug} build_dependencies must be distinct module IDs")
        if any(item not in modules for item in dependencies):
            raise ProjectError(f"Module {slug} has an unknown build dependency")
        if check_files and (not directory.is_dir() or not builder.is_file() or not content.is_dir()):
            raise ProjectError(f"Module {slug} is missing its directory, builder, or content: {directory}")
    module_dependency_closure(registry, list(modules))
    for profile_name, profile in profiles.items():
        _validate_name(profile_name)
        if not isinstance(profile, dict) or profile.get("adapter") not in ADAPTER_SOURCES:
            raise ProjectError(f"Profile {profile_name} has no supported build adapter")
        selected = profile.get("modules")
        if (not isinstance(selected, list) or not selected
                or any(not isinstance(item, str) for item in selected)
                or len(selected) != len(set(selected))):
            raise ProjectError(f"Profile {profile_name} must select distinct modules")
        for slug in selected:
            if slug not in modules or not modules[slug]["enabled"]:
                raise ProjectError(f"Profile {profile_name} includes an unknown or disabled module: {slug}")
        _validate_source_ids(profile.get("source_ids"), sources, f"profile {profile_name}")
        required = ADAPTER_SOURCES[profile["adapter"]]
        if not required.issubset(profile["source_ids"]):
            raise ProjectError(f"Profile {profile_name} omits adapter sources: {sorted(required)}")
        expected_modules = (
            {"mass_driver", "soylent_system", "rico"}
            if profile["adapter"] == "combined" else {profile["adapter"]}
        )
        if set(selected) != expected_modules:
            raise ProjectError(f"Profile {profile_name} module list disagrees with its builder adapter")
        builder = _project_path(root, profile.get("builder"))
        if check_files and not builder.is_file():
            raise ProjectError(f"Profile {profile_name} builder is missing: {builder}")


def _validate_source_ids(value: Any, sources: dict[str, Any], label: str,
                         *, allow_empty: bool = False) -> None:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ProjectError(f"{label} requires a source_ids list")
    if any(not isinstance(item, str) for item in value) or len(set(value)) != len(value):
        raise ProjectError(f"{label} source IDs must be distinct strings")
    unknown = set(value) - sources.keys()
    if unknown:
        raise ProjectError(f"{label} contains unknown source IDs: {sorted(unknown)}")


def module_dependency_closure(registry: dict[str, Any], selected: Sequence[str]) -> list[str]:
    """Include implementation dependencies without selecting their playable content."""
    result: list[str] = []
    completed: set[str] = set()

    def visit(slug: str, stack: tuple[str, ...]) -> None:
        if slug in stack:
            raise ProjectError(f"Module build dependency cycle: {' -> '.join((*stack, slug))}")
        if slug in completed:
            return
        if slug not in registry["modules"]:
            raise ProjectError(f"Unknown module build dependency: {slug}")
        result.append(slug)
        for dependency in registry["modules"][slug].get("build_dependencies", []):
            visit(dependency, (*stack, slug))
        completed.add(slug)

    for slug in selected:
        visit(slug, ())
    return result


def load_registry(root: Path, *, check_files: bool = True) -> dict[str, Any]:
    root = root.resolve()
    registry = deepcopy(_json(root / "project.json"))
    legacy_path = root / "config.local.json"
    if legacy_path.is_file():
        legacy = _json(legacy_path)
        for source_id, old_key in (("pw_disc1", "disc1_source"), ("pw_disc2", "disc2_source")):
            if old_key in legacy and source_id in registry.get("sources", {}):
                registry["sources"][source_id]["path"] = legacy[old_key]
        for key in ("xenoiso", "input_root"):
            if key in legacy:
                registry.setdefault("tools", {})[key] = legacy[key]
    local_path = root / "project.local.json"
    if local_path.is_file():
        local = _json(local_path)
        if set(local) - {"sources", "tools"}:
            raise ProjectError("project.local.json accepts only sources and tools")
        for section in ("sources", "tools"):
            overrides = local.get(section, {})
            if not isinstance(overrides, dict):
                raise ProjectError(f"Local {section} must be an object")
            for key, value in overrides.items():
                if key not in registry.get(section, {}):
                    raise ProjectError(f"Unknown local {section} key: {key}")
                if section == "sources":
                    if isinstance(value, str):
                        value = {"path": value}
                    if not isinstance(value, dict) or set(value) - {"path", "sha256"}:
                        raise ProjectError(f"Local source {key} accepts path and sha256 only")
                    registry[section][key].update(value)
                else:
                    registry[section][key] = value
    validate_registry(root, registry, check_files=check_files)
    return registry


def fingerprint_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ProjectError(f"Required file is missing: {path}")
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ProjectError(f"File changed while hashing: {path}")
    return {"size": before.st_size, "sha256": digest.hexdigest()}


def inspect_sources(root: Path, registry: dict[str, Any], source_ids: Sequence[str]) -> tuple[dict[str, Any], list[str]]:
    result: dict[str, Any] = {}
    warnings = []
    for source_id in source_ids:
        source = registry["sources"][source_id]
        path = configured_path(root, source.get("path"), f"sources.{source_id}.path")
        actual = fingerprint_file(path)
        expected = source.get("sha256")
        if expected and actual["sha256"] != expected.lower():
            raise ProjectError(
                f"Source {source_id} SHA-256 mismatch: expected {expected.lower()}, "
                f"got {actual['sha256']} ({path})"
            )
        if not expected:
            warnings.append(f"{source_id} has no pinned SHA-256; the observed identity is recorded.")
        result[source_id] = {"path": str(path), **actual, "expected_sha256": expected}
        if source.get("provenance") is not None:
            result[source_id]["provenance"] = deepcopy(source["provenance"])
    return result, warnings


def build_plan(root: Path, registry: dict[str, Any], profile_name: str,
               *, release: str = "current", prepare_only: bool = False,
               force: bool = False, patch_options: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    _validate_name(profile_name)
    _validate_name(release, release=True)
    if profile_name not in registry["profiles"]:
        raise ProjectError(f"Unknown build profile {profile_name!r}; run python project.py list")
    profile = registry["profiles"][profile_name]
    build_root = _project_path(root, registry["build_root"])
    destination = contained_path(build_root, f"{profile_name}/{release}")
    if force:
        _protect_active_release(root, registry, profile_name, release)
    if destination.exists() and not force:
        raise ProjectError(f"Build already exists: {destination}. Choose another --release or pass --force.")
    stage = contained_path(build_root, destination / "stage")
    source_paths = {
        source_id: configured_path(root, registry["sources"][source_id].get("path"),
                                   f"sources.{source_id}.path")
        for source_id in profile["source_ids"]
    }
    for source_id, path in source_paths.items():
        if path == destination or path.is_relative_to(destination):
            raise ProjectError(f"Source {source_id} is inside the build destination: {path}")
    adapter = profile["adapter"]
    if patch_options is not None and adapter != "definitive":
        raise ProjectError("--patch-options is supported only by the definitive profile")
    builder = _project_path(root, profile["builder"])
    entrypoint = ".".join(builder.relative_to(root).with_suffix("").parts)
    command = [sys.executable, "-m", entrypoint]
    disc_output = destination / f"Xenogears_Reimagined_{profile_name}_{release}_CD2.bin"
    module = registry["modules"]
    if adapter in ("mass_driver", "combined"):
        input_root = configured_path(root, registry["tools"].get("input_root"), "tools.input_root")
        if input_root == destination or input_root.is_relative_to(destination):
            raise ProjectError("Extracted input_root must not be inside the build destination")
        command += ["--input-root", str(input_root), "--dialogue-root",
                    str(_project_path(root, module["mass_driver"]["content"]))]
    if adapter == "mass_driver":
        command += ["--output", str(stage)]
        if not prepare_only:
            command += ["--source-disc", str(source_paths["pw_disc2"])]
    elif adapter == "soylent_system":
        command += ["--source-disc", str(source_paths["mass_driver_base"]),
                    "--donor-disc", str(source_paths["pw_disc1"]), "--output", str(stage)]
    elif adapter == "combined":
        command += ["--disc2-source", str(source_paths["pw_disc2"]),
                    "--disc1-donor", str(source_paths["pw_disc1"]),
                    "--rico-disc1", str(source_paths["retail_disc1"]), "--output", str(stage)]
    elif adapter == "definitive":
        options_path = _project_path(root, module["definitive"]["content"]) / "options.json"
        if patch_options is not None:
            options_path = _project_path(root, patch_options)
            content_root = _project_path(root, module["definitive"]["content"])
            if not options_path.is_relative_to(content_root) or not options_path.is_file():
                raise ProjectError("Patch options must be an existing file inside definitive/content")
        command += ["--disc1", str(source_paths["retail_disc1"]),
                    "--disc2", str(source_paths["retail_disc2"]),
                    "--options", str(options_path),
                    "--output", str(destination)]
        if prepare_only:
            command.append("--prepare-only")
    else:
        command += ["--disc1", str(source_paths["retail_disc1"]),
                    "--disc2", str(source_paths["retail_disc2"]),
                    "--story-manifest", str(_project_path(root, module["rico"]["content"]) / "manifest.json"),
                    "--output", str(destination), "--stage-directory", "stage"]
        if prepare_only:
            command.append("--prepare-only")
    if not prepare_only:
        xenoiso = configured_path(root, registry["tools"].get("xenoiso"), "tools.xenoiso")
        # The shared wrapper supplies short ASCII aliases to legacy Xenoiso;
        # real project/source/tool paths remain correctly quoted argv entries.
        command += ["--xenoiso", str(xenoiso)]
        if adapter not in ("rico", "definitive"):
            command += ["--build-disc", "--disc-output", str(disc_output)]
    if force:
        command.append("--force")
    return {
        "profile": profile_name, "release": release, "prepare_only": prepare_only,
        "force": force, "modules": profile["modules"], "source_ids": profile["source_ids"],
        "build_dependency_modules": [
            slug for slug in module_dependency_closure(registry, profile["modules"])
            if slug not in profile["modules"]
        ],
        "build_root": str(build_root), "output": str(destination), "stage": str(stage),
        "disc_output": None if adapter in ("rico", "definitive") or prepare_only else str(disc_output),
        "builder": profile["builder"], "command": command,
    }


def _protect_active_release(root: Path, registry: dict[str, Any], profile: str, release: str) -> None:
    """A selected path must keep identifying the same bytes during rebuilds."""
    from shared.project_releases import _read_current
    active = _read_current(root, registry)["profiles"].get(profile, {})
    if active.get("release") == release:
        raise ProjectError(
            f"Cannot replace active release {profile}/{release}. "
            "Build with a new --release name, then use --activate after it succeeds."
        )


def source_snapshot(root: Path, registry: dict[str, Any], profile_name: str) -> dict[str, Any]:
    """Fingerprint current module code/content plus shared implementation and ledgers."""
    root = root.resolve()
    profile = registry["profiles"][profile_name]

    def tree_files(directory: Path) -> list[dict[str, Any]]:
        files = []
        for path in sorted(directory.rglob("*")):
            relative = path.relative_to(root)
            if any(part in IGNORED_DIRECTORIES for part in relative.parts):
                continue
            if path.is_file():
                resolved = contained_path(root, path)
                files.append({"path": relative.as_posix(), **fingerprint_file(resolved)})
        return files

    modules = {}
    dependency_modules = module_dependency_closure(registry, profile["modules"])
    for slug in dependency_modules:
        spec = registry["modules"][slug]
        files = tree_files(_project_path(root, spec["path"]))
        modules[slug] = {
            "path": spec["path"], "files": files, "sha256": _digest(files),
            "role": "selected_module" if slug in profile["modules"] else "build_dependency",
            "build_dependencies": list(spec.get("build_dependencies", [])),
            "declared_donor_source_ids": list(spec["source_ids"]),
            "donor_source_ids": [source_id for source_id in spec["source_ids"]
                                 if source_id in profile["source_ids"]],
        }
    shared = tree_files(root / "shared")
    for name in ("project.py", "project.json"):
        shared.append({"path": name, **fingerprint_file(root / name)})
    shared.sort(key=lambda item: item["path"])
    snapshot = {
        "selected_modules": list(profile["modules"]),
        "build_dependency_modules": [slug for slug in dependency_modules if slug not in profile["modules"]],
        "modules": modules, "shared": {"files": shared, "sha256": _digest(shared)},
    }
    return {**snapshot, "sha256": _digest(snapshot)}


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")


def _run_builder_with_receipt(arguments: Sequence[str]) -> int:
    """Private subprocess entry: inventory the extracted input files actually read."""
    if len(arguments) < 3:
        raise ProjectError("Internal builder runner requires entrypoint, input root, and receipt path")
    entrypoint, input_directory, receipt_file, *builder_arguments = arguments
    input_root = Path(input_directory).resolve()
    receipt = Path(receipt_file).resolve()
    reads: dict[Path, tuple[int, int]] = {}
    written: set[Path] = set()
    active = True

    def audit(event: str, args: tuple[Any, ...]) -> None:
        if not active or event != "open" or not args or not isinstance(args[0], (str, bytes)):
            return
        mode = args[1] if len(args) > 1 else None
        flags = args[2] if len(args) > 2 else 0
        path = Path(os.fsdecode(args[0])).resolve()
        if not path.is_relative_to(input_root):
            return
        if any(part in IGNORED_DIRECTORIES for part in path.relative_to(input_root).parts):
            return
        is_write = (
            isinstance(mode, str) and any(character in mode for character in ("w", "a", "+"))
        ) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR))
        if is_write:
            written.add(path)
            return
        if path not in written and path.is_file() and path not in reads:
            stat = path.stat()
            reads[path] = (stat.st_size, stat.st_mtime_ns)

    sys.addaudithook(audit)
    result = 1
    error = None
    try:
        builder = importlib.import_module(entrypoint)
        result = int(builder.main(builder_arguments) or 0)
    except SystemExit as exc:
        result = exc.code if isinstance(exc.code, int) else 1
        error = str(exc)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        print(error, file=sys.stderr)
    finally:
        active = False
        files = []
        for path, initial_stat in sorted(reads.items()):
            try:
                stat = path.stat()
                if (stat.st_size, stat.st_mtime_ns) != initial_stat:
                    raise ProjectError(f"Extracted input changed during build: {path}")
                files.append({"path": path.relative_to(input_root).as_posix(),
                              **fingerprint_file(path)})
            except (OSError, ProjectError) as exc:
                result = 1
                error = str(exc)
        _write_json(receipt, {
            "format": "xenogears-consumed-inputs-v1", "input_root": str(input_root),
            "files": files, "sha256": _digest(files), "error": error,
        })
    return result


def execute_build(root: Path, registry: dict[str, Any], plan: dict[str, Any]) -> int:
    """Validate inputs, record provenance, and invoke one canonical builder."""
    root = root.resolve()
    if plan["force"]:
        _protect_active_release(root, registry, plan["profile"], plan["release"])
    sources, warnings = inspect_sources(root, registry, plan["source_ids"])
    for warning in warnings:
        print(f"Note: {warning}", flush=True)
    if registry["profiles"][plan["profile"]]["adapter"] in ("mass_driver", "combined"):
        input_root = configured_path(root, registry["tools"].get("input_root"), "tools.input_root")
        if not input_root.is_dir():
            raise ProjectError(f"Extracted input directory is missing: {input_root}")
    native_tools = {}
    native_tool_stats = {}
    if not plan["prepare_only"]:
        xenoiso = configured_path(root, registry["tools"].get("xenoiso"), "tools.xenoiso")
        if not xenoiso.is_file():
            raise ProjectError(f"Xenoiso executable is missing: {xenoiso}")
        native_tool_stats["xenoiso"] = xenoiso.stat()
        native_tools["xenoiso"] = {"path": str(xenoiso), **fingerprint_file(xenoiso)}
    snapshot = source_snapshot(root, registry, plan["profile"])
    from shared.toolchain import audit_imports, toolchain_snapshot
    import_errors = audit_imports(root)
    if import_errors:
        raise ProjectError("Active code imports retired tools:\n" + "\n".join(import_errors))
    toolchain = toolchain_snapshot(root, registry)
    source_stats = {key: Path(item["path"]).stat() for key, item in sources.items()}
    build_root = _project_path(root, registry["build_root"])
    destination = contained_path(build_root, plan["output"])
    previous = None
    if destination.exists():
        if not plan["force"]:
            raise ProjectError(f"Build output appeared after planning: {destination}")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        previous = contained_path(build_root, destination.with_name(f"{destination.name}.replaced-{stamp}"))
        if previous.exists():
            raise ProjectError(f"Previous-build destination already exists: {previous}")
        destination.rename(previous)
    destination.mkdir(parents=True, exist_ok=False)
    manifest_path = destination / "project-build.json"
    manifest = {
        "format": MANIFEST_FORMAT, "status": "building",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "plan": plan, "sources": sources, "source_snapshot": snapshot,
        "toolchain": toolchain,
        "content_versions": {
            slug: registry["modules"][slug].get("content_version", "unversioned")
            for slug in plan["modules"]
        },
        "previous_build": str(previous) if previous else None,
        "input_root": registry["tools"].get("input_root"),
        "source_snapshot_policy": "Current module and shared files; no frozen chapter stage is selected by this CLI.",
    }
    if native_tools:
        manifest["native_tools"] = native_tools
    _write_json(manifest_path, manifest)
    try:
        input_directory = configured_path(root, registry["tools"].get("input_root"), "tools.input_root")
        receipt_path = destination / "consumed-inputs.json"
        # Keep the exact canonical command in the public plan; the isolated
        # wrapper adds only a read audit and invokes that module's main(argv).
        command = [
            sys.executable, "-m", "shared.project_registry", "_run-builder",
            plan["command"][2], str(input_directory), str(receipt_path), *plan["command"][3:],
        ]
        completed = subprocess.run(command, cwd=root, check=False)
        if receipt_path.is_file():
            manifest["consumed_extracted_inputs"] = _json(receipt_path)
        else:
            raise ProjectError(f"Builder did not produce its extracted-input receipt: {receipt_path}")
        if completed.returncode:
            raise ProjectError(f"Builder exited with status {completed.returncode}; see {manifest_path}")
        if source_snapshot(root, registry, plan["profile"]) != snapshot:
            raise ProjectError("Module/shared sources changed during the build; this output is not a verified snapshot")
        for key, before in source_stats.items():
            after = Path(sources[key]["path"]).stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ProjectError(f"Source disc {key} changed during the build")
        for key, before in native_tool_stats.items():
            after = Path(native_tools[key]["path"]).stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ProjectError(f"Native tool {key} changed during the build")
        if toolchain_snapshot(root, registry) != toolchain:
            raise ProjectError("Shared toolchain changed during the build")
        manifest["status"] = "prepared" if plan["prepare_only"] else "built"
        manifest["finished_utc"] = datetime.now(timezone.utc).isoformat()
        outputs = []
        for path in sorted(destination.rglob("*")):
            if path.is_file() and path != manifest_path and (
                path.suffix.lower() in (".bin", ".cue", ".m3u") or path.name.endswith("manifest.json")
            ):
                if path.suffix.lower() == ".bin" and path.parent != destination:
                    continue
                outputs.append({"path": path.relative_to(destination).as_posix(), **fingerprint_file(path)})
        manifest["outputs"] = outputs
    except (OSError, ProjectError, KeyboardInterrupt) as exc:
        manifest["status"] = "failed"
        manifest["error"] = str(exc)
        _write_json(manifest_path, manifest)
        raise
    _write_json(manifest_path, manifest)
    print(f"Recorded exact module/source identities: {manifest_path}")
    return 0


def scaffold_module(root: Path, slug: str, title: str) -> Path:
    """Create a disabled module without adding any build or content-menu profile."""
    root = root.resolve()
    _validate_name(slug)
    if not isinstance(title, str) or not title.strip() or "\n" in title or "\r" in title:
        raise ProjectError("Module title must be a nonempty single line")
    registry_path = root / "project.json"
    original_bytes = registry_path.read_bytes()
    document = _json(registry_path)
    validate_registry(root, document, check_files=False)
    if slug in document["modules"]:
        raise ProjectError(f"Module is already registered: {slug}")
    directory = contained_path(root, f"modules/{slug}")
    if directory.exists():
        raise ProjectError(f"Module directory already exists: {directory}")
    directory.mkdir(parents=True, exist_ok=False)
    for child in ("content", "assets", "docs", "tests", "tools"):
        (directory / child).mkdir()
    (directory / "__init__.py").write_text('"""Unpublished module scaffold."""\n', encoding="utf-8")
    (directory / "build.py").write_text(
        '"""Builder scaffold. Implement and validate before registering a build profile."""\n\n'
        'def main(argv=None):\n'
        '    raise SystemExit("This module is a scaffold; no game resources are emitted.")\n\n'
        'if __name__ == "__main__":\n'
        '    main()\n', encoding="utf-8")
    manifest = {
        "format": "xenogears-module-v1", "id": slug, "title": title.strip(),
        "status": "scaffold", "enabled": False, "source_ids": [],
        "build_dependencies": [],
        "resource_claims": [], "state_claims": [],
    }
    _write_json(directory / "module.json", manifest)
    (directory / "README.md").write_text(
        f"# {title.strip()}\n\n"
        "This module is an unpublished scaffold. It is disabled and excluded from every build profile.\n\n"
        "- Put authored records in content/ and supporting assets in assets/.\n"
        "- Define donor sources, resource IDs, and state allocations in shared/resources.json.\n"
        "- Implement build.py and add meaningful checks in tests/.\n"
        "- Import current codecs and ATEL helpers from shared.tools; do not copy the starter toolkit.\n"
        "- Declare any reused module helpers as build_dependencies in project.json.\n"
        "- Use python project.py tools and the root development guide for the shared workflow.\n"
        "- Review resource conflicts and completion behavior before enabling a build profile.\n\n"
        "The registry does not automatically add modules to the in-game content menu.\n",
        encoding="utf-8")
    document["modules"][slug] = {
        "title": title.strip(), "path": f"modules/{slug}", "builder": f"modules/{slug}/build.py",
        "content": f"modules/{slug}/content", "enabled": False, "status": "scaffold",
        "source_ids": [], "build_dependencies": [],
    }
    if registry_path.read_bytes() != original_bytes:
        raise ProjectError(f"Registry changed concurrently. Scaffold is at {directory}; register it after review.")
    temporary = root / ".project.json.tmp"
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(registry_path)
    return directory


def doctor(root: Path, registry: dict[str, Any]) -> dict[str, Any]:
    """Check every registered source path/hash without searching the machine."""
    report: dict[str, Any] = {"ok": True, "sources": {}, "errors": [], "warnings": []}
    for source_id in registry["sources"]:
        try:
            sources, warnings = inspect_sources(root, registry, [source_id])
            report["sources"].update(sources)
            report["warnings"].extend(warnings)
        except (OSError, ProjectError) as exc:
            report["errors"].append(str(exc))
    for key in ("input_root", "xenoiso"):
        try:
            path = configured_path(root, registry["tools"].get(key), f"tools.{key}")
            if not (path.is_dir() if key == "input_root" else path.is_file()):
                raise ProjectError(f"Configured {key} does not exist: {path}")
        except (OSError, ProjectError) as exc:
            report["errors"].append(str(exc))
    from shared.toolchain import toolchain_report
    report["toolchain"] = toolchain_report(root, registry)
    report["errors"].extend(report["toolchain"]["import_audit"])
    report["ok"] = not report["errors"]
    return report


def test_plan(root: Path, registry: dict[str, Any], profile_name: str) -> list[str]:
    """Run shared checks and the complete implementation dependency closure."""
    if profile_name == "all":
        selected = [name for name, module in registry["modules"].items() if module["enabled"]]
    elif profile_name in registry["profiles"]:
        selected = registry["profiles"][profile_name]["modules"]
    else:
        raise ProjectError(f"Unknown test profile: {profile_name}")
    directories = [root / "shared" / "tests"] + [
        _project_path(root, registry["modules"][slug]["path"]) / "tests"
        for slug in module_dependency_closure(registry, selected)
    ]
    tests = {path for directory in directories for path in directory.glob("test_*.py")}
    tests.update(path for path in (root / "tests").glob("test_project_*.py"))
    if (root / "tests" / "test_toolchain.py").is_file():
        tests.add(root / "tests" / "test_toolchain.py")
    names = [".".join(path.relative_to(root).with_suffix("").parts) for path in sorted(tests)]
    if not names:
        raise ProjectError(f"No tests found for {profile_name}")
    return [sys.executable, "-m", "unittest", *names]


def play_release(root: Path, registry: dict[str, Any], profile: str, *,
                 release: str | None = None, check_only: bool = False,
                 allow_stale: bool = False) -> dict[str, Any]:
    from shared.project_releases import play_plan
    plan = play_plan(root, registry, profile, release, allow_stale=allow_stale)
    emulator = configured_path(root, registry["tools"].get("duckstation"), "tools.duckstation")
    if not emulator.is_file():
        raise ProjectError(f"Configured DuckStation is missing: {emulator}")
    plan["command"] = [str(emulator), "-batch", "-fastboot", "--", str(plan["media"])]
    print(f"{profile} / {plan['release']}: {plan.get('label') or 'development candidate'}", flush=True)
    print(f"Disc: {plan['media']}", flush=True)
    print(f"Gameplay status: {plan.get('runtime_status', 'untested')}", flush=True)
    if allow_stale and not plan.get("fresh", True):
        print("Historical build explicitly selected; it does not match current working files.", flush=True)
    if check_only:
        print("Launch identity verified; emulator not opened.", flush=True)
    else:
        subprocess.Popen(plan["command"], cwd=root)
    return plan


def main(argv: Sequence[str] | None = None, *, root: Path | None = None) -> int:
    root = (root or Path(__file__).resolve().parent.parent).resolve()
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] == "_run-builder":
        return _run_builder_with_receipt(arguments[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("list", help="List build profiles and registered modules")
    diagnostics = commands.add_parser("doctor", help="Validate registry, configured files, and source hashes")
    diagnostics.add_argument("--json", action="store_true")
    commands.add_parser("tools", help="Show the shared tools and recorded local toolchain")
    status = commands.add_parser("status", help="Show active builds, newest receipts, and stale source/tool changes")
    status.add_argument("profile", nargs="?")
    status.add_argument("--verify", action="store_true", help="Also hash finished launch media")
    status.add_argument("--json", action="store_true")
    activate = commands.add_parser("activate", help="Select an explicitly verified build for a profile's normal launcher")
    activate.add_argument("profile")
    activate.add_argument("--release", required=True)
    activate.add_argument("--label")
    activate.add_argument("--runtime-status", choices=("untested", "known-issue", "passed"))
    play = commands.add_parser("play", help="Verify exact build identity and launch with the configured emulator")
    play.add_argument("profile", nargs="?", default="combined")
    play.add_argument("--release", help="Explicit historical/test release instead of the active build")
    play.add_argument("--check-only", action="store_true")
    play.add_argument("--allow-stale", action="store_true", help="Explicitly allow old source/tool versions; media hashes must still match")
    test = commands.add_parser("test", help="Run shared tests plus a profile's module and dependency tests")
    test.add_argument("profile", nargs="?", default="all")
    test.add_argument("--dry-run", action="store_true")
    build = commands.add_parser("build", help="Build current sources into an isolated release directory")
    build.add_argument("profile")
    build.add_argument("--release", default="current")
    build.add_argument("--prepare-only", action="store_true")
    build.add_argument("--patch-options", help="Definitive only: project-relative options file inside its content directory")
    build.add_argument("--dry-run", action="store_true", help="Print the exact command and paths without writing outputs")
    build.add_argument("--force", action="store_true", help="Preserve any previous release under a dated name, then rebuild")
    build.add_argument("--activate", action="store_true", help="After a full successful build, verify and select it for normal launch")
    build.add_argument("--label")
    build.add_argument("--runtime-status", choices=("untested", "known-issue", "passed"))
    new = commands.add_parser("new-module", help="Create and register a disabled module scaffold")
    new.add_argument("slug")
    new.add_argument("--title", required=True)
    args = parser.parse_args(arguments)
    try:
        if args.action == "new-module":
            print(f"Created disabled scaffold: {scaffold_module(root, args.slug, args.title)}")
            return 0
        registry = load_registry(root)
        if args.action == "tools":
            from shared.toolchain import toolchain_report
            print(json.dumps(toolchain_report(root, registry), indent=2))
            return 0
        if args.action == "status":
            from shared.project_releases import release_status
            report = release_status(root, registry, args.profile, verify=args.verify)
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                for name, item in report["profiles"].items():
                    active = item["active"]
                    if active:
                        state = ("INVALID / cannot launch" if active.get("errors") else
                                 "current" if active.get("fresh") else "STALE / needs rebuild")
                        print(f"{name}: {active['release']} [{state}; gameplay: {active.get('runtime_status', 'untested')}]")
                        print(f"  {active.get('media') or active.get('receipt')}")
                        for change in active.get("freshness_changes", [])[:8]:
                            print(f"  Changed: {change}")
                        for error in active.get("errors", []):
                            print(f"  Error: {error}")
                    else:
                        print(f"{name}: no active build; choose one explicitly with activate")
                    latest = item["latest_built"]
                    if latest and (not active or latest["release"] != active["release"]):
                        print(f"  Newest built receipt: {latest['release']} (not automatically activated)")
            return 0
        if args.action == "activate":
            from shared.project_releases import activate_release
            print(json.dumps(activate_release(root, registry, args.profile, args.release,
                                             label=args.label, runtime_status=args.runtime_status), indent=2))
            return 0
        if args.action == "play":
            if args.allow_stale and not args.release:
                raise ProjectError("--allow-stale requires an explicit --release; normal launch must use current tools")
            play_release(root, registry, args.profile, release=args.release,
                         check_only=args.check_only, allow_stale=args.allow_stale)
            return 0
        if args.action == "test":
            command = test_plan(root, registry, args.profile)
            if args.dry_run:
                print(json.dumps(command, indent=2))
                return 0
            return subprocess.run(command, cwd=root, check=False).returncode
        if args.action == "list":
            for name, profile in registry["profiles"].items():
                print(f"{name}: {', '.join(profile['modules'])}")
            print("\nModules:")
            for slug, module in registry["modules"].items():
                state = "enabled" if module["enabled"] else module["status"]
                print(f"  {slug}: {module['title']} [{state}]")
            return 0
        if args.action == "doctor":
            report = doctor(root, registry)
            if args.json:
                print(json.dumps(report, indent=2))
            else:
                for name, source in report["sources"].items():
                    print(f"OK {name}: {source['sha256']} ({source['size']} bytes)")
                for warning in report["warnings"]:
                    print(f"Note: {warning}")
                for error in report["errors"]:
                    print(f"ERROR: {error}", file=sys.stderr)
                print("Project checks passed." if report["ok"] else "Project checks failed.")
            return 0 if report["ok"] else 1
        if args.activate and args.prepare_only:
            raise ProjectError("--activate requires a full build; prepared replacements cannot be launched")
        plan = build_plan(root, registry, args.profile, release=args.release,
                          prepare_only=args.prepare_only, force=args.force, patch_options=args.patch_options)
        if args.dry_run:
            print(json.dumps(plan, indent=2))
            return 0
        result = execute_build(root, registry, plan)
        if not result and args.activate:
            from shared.project_releases import activate_release
            activate_release(root, registry, args.profile, args.release,
                             label=args.label, runtime_status=args.runtime_status)
            print(f"Active {args.profile} release: {args.release}")
        return result
    except (OSError, ProjectError) as exc:
        print(f"Project error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
