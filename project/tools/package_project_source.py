"""Inventory or package the canonical project source without private game data.

The default command writes a reviewable file manifest only. Pass --archive to
also create and verify a deterministic ZIP. Portable patcher sources have their
own companion script and retain their tools/mass_driver_portable path.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = frozenset((
    ".py", ".json", ".md", ".txt", ".ps1", ".cmd", ".html", ".css",
    ".js", ".toml", ".yaml", ".yml", ".template",
))
FORBIDDEN_SUFFIXES = frozenset((
    ".bin", ".cue", ".iso", ".img", ".chd", ".ecm", ".exe", ".dll",
    ".bios", ".mcd", ".srm", ".sav", ".state", ".ducksav", ".pyc",
    ".pyo", ".7z", ".zip", ".xdelta", ".xd3", ".flac", ".webp",
))
EXCLUDED_DIRECTORIES = frozenset((
    "__pycache__", "node_modules", ".git", ".venv", ".pytest_cache",
))
PUBLIC_ROOT_FILES = (
    ".gitignore", "AGENTS.md", "README.md", "readme.html", "project.py",
    "project.json", "project.local.example.json", "config.example.json",
    "PLAY_MASS_DRIVER.cmd", "PLAY_SOYLENT_SYSTEM.cmd", "PLAY_RICO.cmd",
    "PLAY_XENOGEARS_REIMAGINED.cmd", "PLAY_DEFINITIVE.cmd",
    "PATCH_XENOGEARS_DEFINITIVE.cmd", "WRITE_CENTRAL_CONTROL_DIALOGUE.cmd",
)
SOURCE_TREES = ("modules", "shared", "tools", "tests", "docs", "archive/repairs")
TREE_EXCLUSIONS = (
    "shared/assets", "tools/mass_driver_installer", "tools/mass_driver_portable",
    "tools/mass_driver_standalone",
)
RICO_ASSET_ROOT = "modules/rico/content/assets"
CUSTOM_TIM = f"{RICO_ASSET_ROOT}/young_rico_menu_portrait.tim"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def relative_name(value: str) -> str:
    """Reject absolute, drive-qualified and traversal names before archive use."""
    name = value.replace("\\", "/")
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or any(p in (".", "..") or ":" in p for p in path.parts):
        raise ValueError(f"Unsafe relative source path: {value!r}")
    return path.as_posix()


def is_under(name: str, directory: str) -> bool:
    return name == directory or name.startswith(directory + "/")


def authored_mass_driver_images() -> tuple[str, ...]:
    """Read only literal asset declarations; importing the builder is unnecessary."""
    tree = ast.parse((ROOT / "modules/mass_driver/build.py").read_text(encoding="utf-8"))
    values = {}
    targets = {"FACILITY_VIDEO_SOURCE_RELATIVE_PATHS", "NUKE_SOURCE_RELATIVE_PATH"}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in targets:
                    literal = node.value
                    if isinstance(literal, ast.Call) and isinstance(literal.func, ast.Name) and literal.func.id == "Path" and len(literal.args) == 1 and not literal.keywords:
                        literal = literal.args[0]
                    values[target.id] = ast.literal_eval(literal)
    if set(values) != targets:
        raise ValueError("The builder's authored-image declarations changed; review the source scope.")
    paths = (*values["FACILITY_VIDEO_SOURCE_RELATIVE_PATHS"], values["NUKE_SOURCE_RELATIVE_PATH"])
    names = tuple(relative_name(str(path)) for path in paths)
    if len(names) != 8 or len(set(names)) != 8 or any(not n.startswith("assets/mass_driver/") or not n.endswith(".png") for n in names):
        raise ValueError("Unexpected Mass Driver authored-image allowlist; review before packaging.")
    return names


def source_files() -> dict[str, bytes]:
    selected: set[str] = set(PUBLIC_ROOT_FILES)
    selected.update(authored_mass_driver_images())
    selected.add("archive/__init__.py")
    selected.update(p.relative_to(ROOT).as_posix() for p in (ROOT / "archive").glob("README*.md"))
    for directory in SOURCE_TREES:
        for path in sorted((ROOT / directory).rglob("*")):
            name = path.relative_to(ROOT).as_posix()
            if any(part in EXCLUDED_DIRECTORIES or part.startswith(".") for part in path.relative_to(ROOT).parts):
                continue
            if any(is_under(name, excluded) for excluded in TREE_EXCLUSIONS):
                continue
            if path.is_symlink():
                raise ValueError(f"Source companion refuses linked input: {name}")
            if not path.is_file():
                continue
            if path.suffix.lower() in TEXT_SUFFIXES:
                selected.add(name)
            elif is_under(name, RICO_ASSET_ROOT) and (path.suffix.lower() == ".png" or name == CUSTOM_TIM):
                selected.add(name)
            else:
                raise ValueError(f"Unreviewed file in a source tree: {name}")
    result = {}
    for name in sorted(selected):
        name = relative_name(name)
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Missing or linked source input: {name}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES or name in ("project.local.json", "config.local.json"):
            raise ValueError(f"Forbidden source input: {name}")
        if path.suffix.lower() in TEXT_SUFFIXES:
            path.read_text(encoding="utf-8-sig")
        result[name] = path.read_bytes()
    return result


def external_inputs(receipt: dict) -> dict:
    source = receipt["consumed_extracted_inputs"]
    if source.get("error"):
        raise ValueError("Build receipt has an incomplete consumed-input inventory")
    files = []
    for item in source["files"]:
        files.append({"path_below_input_root": relative_name(item["path"]), "size": item["size"], "sha256": item["sha256"]})
    native_tools = {
        name: {"filename": Path(value["path"]).name, "size": value["size"], "sha256": value["sha256"]}
        for name, value in receipt.get("native_tools", {}).items()
    }
    return {
        "format": "xenogears-external-source-inputs-v1",
        "profile": receipt["plan"]["profile"],
        "release": receipt["plan"]["release"],
        "payloads_included": False,
        "input_root": "Configure tools.input_root locally; relative paths below are the builder's audited donor contract.",
        "source_discs": {name: {"size": value["size"], "sha256": value["sha256"]} for name, value in receipt["sources"].items()},
        "native_tools": native_tools,
        "important_requirements": [
            "Obtain the documented retail/PW disc variants separately; no disc or patch payload is included.",
            "Restore or independently reproduce each extracted donor below at its recorded size and hash.",
            "standalone_bootstrap/2595.bin is a captured game-state fixture; it is not generated solely by the disc extraction step.",
            "Historical regression checks also require excluded historical output images, captures and prepared fixtures.",
            "Other profiles declare additional source IDs and donors in project.json and their module guides.",
        ],
        "files": sorted(files, key=lambda item: item["path_below_input_root"]),
    }


def validate_receipt_sources(receipt: dict) -> int:
    """Do not attach a completed build's identity to changed implementation."""
    snapshot = receipt["source_snapshot"]
    records = list(snapshot["shared"]["files"])
    for module in snapshot["modules"].values():
        records.extend(module["files"])
    for item in records:
        name = relative_name(item["path"])
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Recorded build source is missing or linked: {name}")
        data = path.read_bytes()
        if len(data) != item["size"] or sha(data) != item["sha256"]:
            raise ValueError(f"Recorded build source has changed: {name}; use a matching new build receipt.")
    return len(records)


def build_identity(receipt: dict) -> dict:
    return {
        "format": "xenogears-source-companion-release-v1",
        "profile": receipt["plan"]["profile"],
        "release": receipt["plan"]["release"],
        "receipt_status": receipt["status"],
        "content_versions": receipt["content_versions"],
        "workstation_source_snapshot_sha256": receipt["source_snapshot"]["sha256"],
        "source_snapshot_note": "Development reference screenshots are deliberately omitted. The packaged tree does not claim the workstation tree's complete source fingerprint.",
        "runtime_acceptance": "See docs/mass-driver-release-qa.md for version-attributed gameplay coverage and limits. Source packaging does not itself establish runtime acceptance.",
        "outputs": [{"path": relative_name(item["path"]), "size": item["size"], "sha256": item["sha256"]} for item in receipt["outputs"] if Path(item["path"]).suffix.lower() in (".bin", ".cue") or item["path"] == "stage/manifest.json"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True, help="Completed project-build.json for this source release")
    parser.add_argument("--output-dir", type=Path, required=True, help="A new directory; existing evidence is preserved")
    parser.add_argument("--perfect-works-license", type=Path, required=True)
    parser.add_argument("--upstream-provenance", type=Path, required=True)
    parser.add_argument("--foundation-provenance", type=Path, required=True)
    parser.add_argument("--archive", action="store_true", help="Create the ZIP after reviewing the manifest-only scope")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists():
        raise SystemExit("Choose a new output directory; source manifests and archives are not overwritten.")
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    if receipt.get("format") != "xenogears-project-build-v1" or receipt.get("status") != "built" or receipt["plan"]["profile"] != "mass_driver":
        raise SystemExit("Use a completed Mass Driver project build receipt.")
    verified_source_count = validate_receipt_sources(receipt)
    files = source_files()
    external = external_inputs(receipt)
    identity = build_identity(receipt)
    foundation = json.loads(args.foundation_provenance.read_text(encoding="utf-8"))
    foundation_keys = ("format", "date", "result", "previous_expected", "rebuilt_foundation", "official_release", "verified_retail", "official_patch", "tool_version_scope", "official_algorithm", "recipe")
    files["release/FOUNDATION_PROVENANCE.json"] = json_bytes({key: foundation[key] for key in foundation_keys})
    files["release/EXTERNAL_INPUTS.json"] = json_bytes(external)
    files["release/BUILD_IDENTITY.json"] = json_bytes(identity)
    license_text = args.perfect_works_license.read_bytes()
    upstream = json.loads(args.upstream_provenance.read_text(encoding="utf-8"))
    if len(license_text) != upstream["license_size"] or sha(license_text) != upstream["license_sha256"]:
        raise ValueError("Perfect Works license does not match its pinned upstream provenance")
    foundation_identity = foundation["rebuilt_foundation"]
    if foundation_identity["sha256"] != receipt["sources"]["pw_disc2"]["sha256"] or foundation_identity["bytes"] != receipt["sources"]["pw_disc2"]["size"]:
        raise ValueError("Foundation provenance does not identify this build's source disc")
    files["licenses/Perfect_Works_GPL-3.0.txt"] = license_text
    files["licenses/Perfect_Works_PROVENANCE.json"] = json_bytes(upstream)
    files["README_SOURCE.md"] = (
        "# Xenogears Reimagined project source companion\n\n"
        "This archive contains the canonical project entry point, modules, shared tools, "
        "tests, authored dialogue, selected authored images, public configuration templates, "
        "compatibility entry points, historical repair source and documentation for the "
        "release in release/BUILD_IDENTITY.json. Read docs/source-distribution.md first.\n\n"
        "It contains no disc images, extracted game resources, prepared game payloads, patch "
        "payloads, executables, emulator, BIOS, memory cards, saves or private configuration. "
        "release/EXTERNAL_INPUTS.json identifies the external donor contract, including a "
        "captured initial-state fixture. Historical tests require additional excluded fixtures. "
        "This source archive alone is not a turnkey build from a clean disc.\n\n"
        "The matching portable patcher and Windows player source companions are separate. "
        "Copy their tools/mass_driver_portable and tools/mass_driver_standalone directories "
        "into this project's tools directory. Their release metadata belongs alongside each "
        "companion; do not overwrite this project's release metadata. Dependency source and "
        "compiler requirements are documented in each companion. The player installer is "
        "also a separate artifact.\n\n"
        "Preserve upstream notices. The included Perfect Works license/provenance does not "
        "grant rights to the underlying Xenogears game. Development reference screenshots "
        "are excluded; the workstation's complete source-tree fingerprint is not claimed "
        "for this reduced source package. Runtime and clean-install acceptance remain "
        "separate release requirements.\n"
    ).encode("utf-8")
    files["SHA256SUMS.txt"] = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(files.items())).encode("utf-8")
    report = {
        "format": "xenogears-project-source-scope-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "verified_archive" if args.archive else "manifest_only",
        "profile": identity["profile"], "release": identity["release"],
        "scope": "Canonical project source and selected authored assets; no proprietary game-input payloads",
        "included_trees": list(SOURCE_TREES),
        "excluded_trees": ["work", "builds", "output", "emulator_data", "shared/assets", "assets except the eight active authored Mass Driver PNGs", "tools/mass_driver_installer", "tools/mass_driver_portable (separate companion)", "tools/mass_driver_standalone (separate companion)", "archive except repair source and top-level README context"],
        "excluded_sensitive_inputs": ["project.local.json", "config.local.json", ".env files", "discs", "extracted/prepared game resources", "BIOS", "cards/saves", "executables", "package caches"],
        "file_count": len(files), "uncompressed_bytes": sum(len(data) for data in files.values()),
        "external_input_count": len(external["files"]),
        "recorded_build_sources_verified": verified_source_count,
        "by_suffix": dict(sorted(Counter(Path(name).suffix or "[none]" for name in files).items())),
        "mass_driver_authored_images": list(authored_mass_driver_images()),
        "files": [{"path": name, "size": len(data), "sha256": sha(data)} for name, data in sorted(files.items())],
    }
    output.mkdir(parents=True)
    if args.archive:
        version = str(identity["content_versions"]["mass_driver"])
        prefix = f"Xenogears_Reimagined_Source_{version}"
        archive = output / f"{prefix}.zip"
        with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
            for name, data in sorted(files.items()):
                info = zipfile.ZipInfo(f"{prefix}/{relative_name(name)}", date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 0
                info.external_attr = 0
                package.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(archive) as package:
            if len(package.namelist()) != len(files) or package.testzip() is not None:
                raise RuntimeError("Source ZIP inventory or CRC verification failed")
            for name, data in files.items():
                if package.read(f"{prefix}/{name}") != data:
                    raise RuntimeError(f"Source ZIP byte comparison failed: {name}")
        report["archive"] = {"filename": archive.name, "size": archive.stat().st_size, "sha256": sha(archive.read_bytes()), "all_entries_byte_verified": True}
    (output / "project-source-manifest.json").write_bytes(json_bytes(report))
    print(json.dumps({key: value for key, value in report.items() if key != "files"}, indent=2))


if __name__ == "__main__":
    main()
