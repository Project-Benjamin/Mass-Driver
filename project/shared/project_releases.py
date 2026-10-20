"""Explicit release selection and checked launch plans for every build profile.

An image being the newest build does not make it the active or accepted build.
Only activate_release changes the selection; this module never starts an emulator.
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path, PureWindowsPath
import re
import tempfile
from typing import Any

from shared import project_registry as project


CURRENT_FORMAT = "xenogears-current-releases-v1"
STATUS_FORMAT = "xenogears-release-status-v1"


def _profile(registry: dict[str, Any], profile: str) -> None:
    project._validate_name(profile)
    if profile not in registry["profiles"]:
        raise project.ProjectError(f"Unknown build profile: {profile}")


def _build_root(root: Path, registry: dict[str, Any]) -> Path:
    return project._project_path(root.resolve(), registry["build_root"])


def _relative_file(base: Path, value: Any) -> Path:
    if (not isinstance(value, str) or not value or "\x00" in value
            or Path(value).is_absolute() or PureWindowsPath(value).drive
            or PureWindowsPath(value).is_absolute()
            or ".." in PureWindowsPath(value).parts):
        raise project.ProjectError(f"Invalid release-relative file: {value!r}")
    return project.contained_path(base, value.replace("\\", "/"))


def _identity(value: Any, label: str) -> dict[str, Any]:
    if (not isinstance(value, dict) or type(value.get("size")) is not int
            or value["size"] < 0 or not isinstance(value.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", value["sha256"])):
        raise project.ProjectError(f"Invalid recorded file identity: {label}")
    return {"size": value["size"], "sha256": value["sha256"]}


def _read_current(root: Path, registry: dict[str, Any]) -> dict[str, Any]:
    path = project.contained_path(_build_root(root, registry), "current.json")
    if not path.exists():
        return {"format": CURRENT_FORMAT, "profiles": {}}
    value = project._json(path)
    if value.get("format") != CURRENT_FORMAT or not isinstance(value.get("profiles"), dict):
        raise project.ProjectError(f"Invalid active release registry: {path}")
    for profile, record in value["profiles"].items():
        _profile(registry, profile)
        if not isinstance(record, dict) or set(record) - {"release", "label", "runtime_status"}:
            raise project.ProjectError(f"Invalid active release record: {profile}")
        project._validate_name(record.get("release"), release=True)
        for key in ("label", "runtime_status"):
            if key in record and not isinstance(record[key], str):
                raise project.ProjectError(f"Active {profile} {key} must be text")
    return value


class _Checks:
    """Hash each shared source/input once during a multi-profile status call."""

    def __init__(self, root: Path, registry: dict[str, Any]):
        self.root = root.resolve()
        self.registry = registry
        self.hashes: dict[Path, dict[str, Any]] = {}
        self.snapshots: dict[str, dict[str, Any]] = {}
        self.toolchain: dict[str, Any] | None = None

    def fingerprint(self, path: Path) -> dict[str, Any]:
        path = path.resolve()
        if path not in self.hashes:
            self.hashes[path] = project.fingerprint_file(path)
        return self.hashes[path]

    def freshness(self, receipt: dict[str, Any], profile: str) -> list[str]:
        changes: list[str] = []
        if profile not in self.snapshots:
            self.snapshots[profile] = project.source_snapshot(self.root, self.registry, profile)
        current = self.snapshots[profile]
        recorded = receipt.get("source_snapshot", {})
        if not isinstance(recorded, dict):
            recorded = {}
        if current.get("sha256") != recorded.get("sha256"):
            old_shared = recorded.get("shared", {})
            if not isinstance(old_shared, dict) or current["shared"]["sha256"] != old_shared.get("sha256"):
                changes.append("shared tools or project configuration changed")
            old_modules = recorded.get("modules", {})
            if not isinstance(old_modules, dict):
                old_modules = {}
            for slug, module in current["modules"].items():
                old = old_modules.get(slug, {})
                if not isinstance(old, dict) or old.get("sha256") != module["sha256"]:
                    changes.append(f"module {slug} changed")
            if not changes:
                changes.append("module selection or build dependencies changed")

        native = receipt.get("native_tools", {})
        native = native if isinstance(native, dict) else {}
        try:
            path = project.configured_path(self.root, self.registry["tools"].get("xenoiso"), "tools.xenoiso")
            old = native.get("xenoiso", {})
            old = old if isinstance(old, dict) else {}
            if (Path(old.get("path", "")).resolve() != path
                    or _identity(old, "Xenoiso") != self.fingerprint(path)):
                changes.append("configured Xenoiso changed")
        except (OSError, project.ProjectError, TypeError) as exc:
            changes.append(f"Xenoiso unavailable or unrecorded: {exc}")

        sources = receipt.get("sources", {})
        sources = sources if isinstance(sources, dict) else {}
        source_ids = self.registry["profiles"][profile]["source_ids"]
        if set(sources) != set(source_ids):
            changes.append("source-disc selection changed")
        for source_id in source_ids:
            try:
                source = self.registry["sources"][source_id]
                path = project.configured_path(self.root, source.get("path"), f"sources.{source_id}.path")
                old = sources.get(source_id, {})
                old = old if isinstance(old, dict) else {}
                actual = self.fingerprint(path)
                if (Path(old.get("path", "")).resolve() != path
                        or _identity(old, source_id) != actual
                        or (source.get("sha256") and source["sha256"].lower() != actual["sha256"])):
                    changes.append(f"source disc {source_id} changed")
            except (OSError, project.ProjectError, TypeError) as exc:
                changes.append(f"source disc {source_id} unavailable or unrecorded: {exc}")

        try:
            consumed = receipt.get("consumed_extracted_inputs")
            if (not isinstance(consumed, dict)
                    or consumed.get("format") != "xenogears-consumed-inputs-v1"
                    or consumed.get("error") is not None
                    or not isinstance(consumed.get("files"), list)
                    or consumed.get("sha256") != project._digest(consumed["files"])):
                raise project.ProjectError("missing or invalid consumed-input receipt")
            input_root = project.configured_path(self.root, self.registry["tools"].get("input_root"), "tools.input_root")
            if Path(consumed.get("input_root", "")).resolve() != input_root:
                changes.append("extracted input directory changed")
            seen = set()
            for item in consumed["files"]:
                if not isinstance(item, dict):
                    raise project.ProjectError("invalid consumed-input file record")
                path = _relative_file(input_root, item.get("path"))
                if path in seen:
                    raise project.ProjectError(f"duplicate consumed input: {path}")
                seen.add(path)
                if _identity(item, str(path)) != self.fingerprint(path):
                    changes.append(f"extracted input changed: {item['path']}")
        except (OSError, project.ProjectError, TypeError) as exc:
            changes.append(f"extracted input verification failed: {exc}")

        try:
            from shared.toolchain import toolchain_snapshot

            if self.toolchain is None:
                self.toolchain = toolchain_snapshot(self.root, self.registry)
            old = receipt.get("toolchain", {})
            if not isinstance(old, dict) or old.get("sha256") != self.toolchain.get("sha256"):
                changes.append("shared toolchain changed or was not recorded")
        except (ImportError, OSError, project.ProjectError) as exc:
            changes.append(f"shared toolchain verification unavailable: {exc}")
        return changes


def _receipt(root: Path, registry: dict[str, Any], profile: str, release: str,
             *, require_built: bool = True) -> tuple[Path, dict[str, Any]]:
    _profile(registry, profile)
    project._validate_name(release, release=True)
    directory = project.contained_path(_build_root(root, registry), f"{profile}/{release}")
    path = project.contained_path(directory, "project-build.json")
    value = project._json(path)
    plan = value.get("plan", {})
    if (value.get("format") != project.MANIFEST_FORMAT or not isinstance(plan, dict)
            or plan.get("profile") != profile or plan.get("release") != release):
        raise project.ProjectError(f"Build receipt identity disagrees with selected release: {path}")
    if value.get("status") not in ("building", "prepared", "built", "failed"):
        raise project.ProjectError(f"Build receipt has missing or invalid status: {path}")
    if require_built and (value.get("status") != "built" or plan.get("prepare_only")):
        raise project.ProjectError(f"Release is not a completed disc build ({value.get('status')}): {path}")
    if not isinstance(plan.get("output"), str) or Path(plan["output"]).resolve() != directory:
        raise project.ProjectError(f"Build receipt output directory disagrees with selected release: {path}")
    return directory, value


def _media(directory: Path, receipt: dict[str, Any], profile: str, checks: _Checks,
           *, verify: bool) -> Path:
    records = receipt.get("outputs")
    if not isinstance(records, list) or not records:
        raise project.ProjectError("Build has no recorded outputs")
    outputs: dict[Path, dict[str, Any]] = {}
    for item in records:
        if not isinstance(item, dict):
            raise project.ProjectError("Invalid build output record")
        path = _relative_file(directory, item.get("path"))
        identity = _identity(item, str(path))
        if path in outputs:
            raise project.ProjectError(f"Duplicate build output: {path}")
        if not path.is_file() or path.stat().st_size != identity["size"]:
            raise project.ProjectError(f"Build output missing or wrong size: {path}")
        # Quick status still authenticates launch descriptors; large BIN hashes
        # are required for activation/play and for explicitly verified status.
        if (verify or path.suffix.lower() in {".cue", ".m3u"}) and checks.fingerprint(path) != identity:
            raise project.ProjectError(f"Build output SHA-256 mismatch: {path}")
        outputs[path] = item

    def reference(owner: Path, name: str, allowed: set[str]) -> Path:
        path = _relative_file(owner.parent, name)
        if not path.is_relative_to(directory) or path not in outputs or path.suffix.lower() not in allowed:
            raise project.ProjectError(f"Unrecorded or unsupported media reference in {owner.name}: {name}")
        return path

    playlist_references: dict[Path, list[Path]] = {}
    for path in outputs:
        suffix = path.suffix.lower()
        if suffix not in {".cue", ".m3u"}:
            continue
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except (OSError, UnicodeError) as exc:
            raise project.ProjectError(f"Cannot read launch descriptor {path}: {exc}") from exc
        count = 0
        if suffix == ".m3u":
            playlist_references[path] = []
        for line in lines:
            line = line.strip()
            if suffix == ".m3u":
                if not line or line.startswith("#"):
                    continue
                playlist_references[path].append(reference(path, line, {".cue"}))
                count += 1
            elif re.match(r"FILE\b", line, re.I):
                match = re.fullmatch(r'FILE\s+(?:"([^"]+)"|(\S+))\s+BINARY', line, re.I)
                if not match:
                    raise project.ProjectError(f"Malformed CUE FILE reference: {path}")
                reference(path, match.group(1) or match.group(2), {".bin"})
                count += 1
        if not count:
            raise project.ProjectError(f"Launch descriptor has no media references: {path}")

    playlists = [path for path in outputs if path.parent == directory and path.suffix.lower() == ".m3u"]
    cues = [path for path in outputs if path.parent == directory and path.suffix.lower() == ".cue"]
    if checks.registry["profiles"][profile]["adapter"] in ("rico", "definitive"):
        if len(playlists) != 1:
            raise project.ProjectError("Two-disc build must have one unambiguous root playlist")
        members = playlist_references[playlists[0]]
        if len(cues) != 2 or len(members) != 2 or set(members) != set(cues):
            raise project.ProjectError("Two-disc playlist must include exactly two distinct recorded root CUEs, once each")
        return playlists[0]
    if len(cues) != 1:
        raise project.ProjectError("Build must have one unambiguous root CUE or Rico playlist")
    return cues[0]


def play_plan(root: Path, registry: dict[str, Any], profile: str, release: str | None = None,
              *, allow_stale: bool = False) -> dict[str, Any]:
    """Return verified media for an explicit release or the explicitly active one."""
    _profile(registry, profile)
    current = _read_current(root, registry)
    active = current["profiles"].get(profile, {})
    if release is None:
        release = active.get("release")
        if release is None:
            raise project.ProjectError(f"No active {profile} release. Activate a reviewed build first.")
    directory, receipt = _receipt(root, registry, profile, release)
    checks = _Checks(root, registry)
    media = _media(directory, receipt, profile, checks, verify=True)
    changes = checks.freshness(receipt, profile)
    if changes and not allow_stale:
        raise project.ProjectError(f"Release {profile}/{release} is stale: {'; '.join(changes)}. Rebuild before activating or playing it.")
    metadata = active if active.get("release") == release else {}
    return {
        "profile": profile, "release": release, "media": str(media),
        "receipt": str(directory / "project-build.json"), "fresh": not changes,
        "freshness_changes": changes, "runtime_status": metadata.get("runtime_status", "untested"),
        "label": metadata.get("label", release), "active": active.get("release") == release,
        "media_verified": True,
    }


def activate_release(root: Path, registry: dict[str, Any], profile: str, release: str,
                     *, runtime_status: str | None = None, label: str | None = None) -> dict[str, Any]:
    """Validate first, then atomically select one build without accepting gameplay."""
    for key, value in (("runtime_status", runtime_status), ("label", label)):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise project.ProjectError(f"{key} must be nonempty text")
    plan = play_plan(root, registry, profile, release)
    current = _read_current(root, registry)
    old = current["profiles"].get(profile, {})
    record = dict(old) if old.get("release") == release else {"release": release}
    record["runtime_status"] = runtime_status if runtime_status is not None else record.get("runtime_status", "untested")
    if label is not None:
        record["label"] = label
    current["profiles"][profile] = record
    path = project.contained_path(_build_root(root, registry), "current.json")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         prefix=".current-", suffix=".json.tmp",
                                         dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(current, ensure_ascii=False, indent=2) + "\n")
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return {**plan, **record, "active": True, "active_registry": str(path)}


def release_status(root: Path, registry: dict[str, Any], profile: str | None = None,
                   *, verify: bool = False) -> dict[str, Any]:
    """Inventory builds; distinguish active selection, recency, and verification."""
    root = root.resolve()
    if profile is not None:
        _profile(registry, profile)
    current = _read_current(root, registry)
    checks = _Checks(root, registry)
    report: dict[str, Any] = {"format": STATUS_FORMAT, "active_registry": str(_build_root(root, registry) / "current.json"), "profiles": {}}
    for name in ([profile] if profile is not None else registry["profiles"]):
        folder = project.contained_path(_build_root(root, registry), name)
        active = current["profiles"].get(name)
        names = {path.parent.name for path in folder.glob("*/project-build.json")} if folder.exists() else set()
        if active:
            names.add(active["release"])
        entries = []
        for release in sorted(names):
            item: dict[str, Any] = {"profile": name, "release": release, "status": "invalid", "fresh": False,
                                    "freshness_changes": [], "errors": [], "media_verified": False,
                                    "runtime_status": "untested", "active": bool(active and active["release"] == release)}
            if item["active"]:
                item.update(active)
            try:
                directory, receipt = _receipt(root, registry, name, release, require_built=False)
                item.update(status=receipt["status"], receipt=str(directory / "project-build.json"),
                            finished_utc=receipt.get("finished_utc"))
                if receipt.get("status") != "built" or receipt["plan"].get("prepare_only"):
                    raise project.ProjectError(f"Release is not a completed disc build ({receipt.get('status')})")
                item["freshness_changes"] = checks.freshness(receipt, name)
                item["fresh"] = not item["freshness_changes"]
                item["media"] = str(_media(directory, receipt, name, checks, verify=verify))
                item["media_verified"] = verify
            except (OSError, project.ProjectError) as exc:
                item["fresh"] = False
                item["media_verified"] = False
                item["errors"].append(str(exc))
            entries.append(item)

        def finish(item: dict[str, Any]) -> float:
            try:
                return datetime.fromisoformat(item.get("finished_utc", "")).timestamp()
            except (TypeError, ValueError, OverflowError):
                return float("-inf")

        built = [item for item in entries if item["status"] == "built"]
        report["profiles"][name] = {
            "active": next((item for item in entries if item["active"]), None),
            "latest_built": max(built, key=finish) if built else None,
            "releases": entries,
        }
    return report
