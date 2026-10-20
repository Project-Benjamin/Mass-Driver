"""Prepare the public player from a pinned GPL emulator and verified patch kit.

No game image, BIOS, Microsoft DLL or user data is copied into this payload.
The matching emulator/dependency source companion is distributed separately.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
RUNTIME_COMMIT = "b2577ef8bdaae99840874b6dae8146f0316357b4"
RUNTIME_TAG = "v0.1-7371"
RUNTIME_ZIP_SHA = "b1036ea9dbf91609cef77daf03bdf2efce19b03ed3d6b4ea7c5c3396f5fc3b96"
RUNTIME_EXE_SHA = "10d0d2db84e93b7c1700e2e9a20f1a34a3511f735952565c26714334825967c6"
SOURCE_ZIP_SHA = "38a4fa18425a175b66cbe29b29bbd92336715fa0a6fbf08a99ac9d636cf1f489"
PATCHER_SHA = "0068ab00d64d6911b1a135ff53bd35f9c6c7c0245d331b2881b3a33c5e15f823"
VC_PATTERN = re.compile(r"^(?:msvcp140|vcruntime140|concrt140|vcomp140).*\.dll$", re.I)
QT_SOURCE_HASHES = {
    "qtbase": "488119aad60719a085a1e45c31641ac2406ef86fc088a3c99885c18e9d6b4bb9",
    "qtimageformats": "8e736b02db7dd67dbe834d56503b242344ce85d3532da692f1812b30ccf80997",
    "qtsvg": "85a22142270a92be0dd0ab5d27cc53617b2a2f1a45fc0a3890024164032f8475",
    "qttools": "9e15f1fdbd83e4123e733bff20aff1b45921c09056c3790fa42eb71d0a5cd01f",
    "qttranslations": "d1f25e0f68a1282feffdd5fe795a027ee5f16ad19e3b1fa2e04a51cea19110ec",
}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while data := stream.read(8 << 20):
            value.update(data)
    return value.hexdigest()


def inventory(root):
    return [{"path": p.relative_to(root).as_posix(), "size": p.stat().st_size, "sha256": sha(p)}
            for p in sorted(root.rglob("*")) if p.is_file()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-archive", type=Path, required=True)
    parser.add_argument("--emulator-source-archive", type=Path, required=True)
    parser.add_argument("--dependency-source-dir", type=Path, required=True,
                        help="Pinned Qt 6.7.2 source archives for verbatim installed notices")
    parser.add_argument("--patcher-package", type=Path, required=True)
    parser.add_argument("--build-manifest", type=Path, required=True)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--content-version", default="V176")
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_root.resolve()
    require(not output.exists(), "Choose a fresh public payload output")
    require(sha(args.runtime_archive) == RUNTIME_ZIP_SHA, "GPL runtime archive changed")
    require(sha(args.emulator_source_archive) == SOURCE_ZIP_SHA, "Matching emulator source archive changed")
    manifest = json.loads(args.build_manifest.read_text(encoding="utf-8"))
    require(manifest["format"] == "xenogears-mass-driver-build-v1", "Wrong patch build manifest")
    require(manifest["source"]["sha256"] == "5eab85c683d4d7087d345b587472db9c44df29b35ce66553c2626d26018b947e", "Unsupported retail source")
    package = args.patcher_package.resolve()
    expected_package = {"Xenogears_Mass_Driver.exe", "MassDriverData/SHA256SUMS.txt", "MassDriverData/patch_manifest.txt",
                        "MassDriverData/docs/README_FIRST.md", "MassDriverData/docs/CREDITS_AND_LICENSES.md",
                        "MassDriverData/licenses/Perfect_Works_GPL-3.0.txt", "MassDriverData/licenses/xdelta-Apache-2.0.txt",
                        manifest["patch"]["relative_path"], manifest["cue_template"]["relative_path"]}
    for spec in (manifest.get("compiler_runtime_license"), *manifest.get("compiler_runtime_notices", [])):
        if spec:
            expected_package.add(spec["relative_path"])
            path = package / spec["relative_path"]
            require(path.stat().st_size == spec["size"] and sha(path) == spec["sha256"], "Patcher dependency notice changed")
    require(not any(p.is_symlink() or p.is_junction() for p in package.rglob("*")), "Linked patcher input")
    require({p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file()} == expected_package,
            "Patcher package has missing or extra files; refusing possible private data")
    require(sha(package / "Xenogears_Mass_Driver.exe") == PATCHER_SHA, "Unreviewed plain patcher")
    for item in (manifest["patch"], manifest["cue_template"]):
        path = package / item["relative_path"]
        require(path.stat().st_size == item["size"] and sha(path) == item["sha256"], "Patch package differs from manifest")
    # Derive supported original NTSC-U PS1 identities from this exact runtime's
    # BIOS table. The UI deliberately accepts 512 KiB PS1 dumps, not PS2 files.
    prefix = "duckstation-" + RUNTIME_COMMIT + "/"
    with zipfile.ZipFile(args.emulator_source_archive) as source:
        bios_source = source.read(prefix + "src/core/bios.cpp").decode("utf-8")
        bios_md5s = re.findall(r'^\s*\{"(?!PS2)[^"\n]+", ConsoleRegion::NTSC_U, MakeHashFromString\("([0-9a-f]{32})"\)', bios_source, re.M)
    require(len(bios_md5s) == 7, "Pinned NTSC-U PlayStation BIOS table changed")
    output.mkdir(parents=True)
    payload = output / "payload"
    (payload / "runtime").mkdir(parents=True)
    exclusions = []
    with zipfile.ZipFile(args.runtime_archive) as archive:
        for item in archive.infolist():
            name = PurePosixPath(item.filename)
            require(not name.is_absolute() and all(p not in ("..", ".") for p in name.parts), "Unsafe runtime archive name")
            require(not item.filename.endswith("/") or item.is_dir(), "Invalid runtime archive directory")
            if item.is_dir():
                continue
            if item.filename == "updater.exe":
                exclusions.append({"path": item.filename, "reason": "This player pins its runtime and has no upstream updater"})
                continue
            require(not VC_PATTERN.match(name.name), "Public runtime must not contain Microsoft DLLs")
            target = payload / "runtime" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(item))
    require(exclusions == [{"path": "updater.exe", "reason": "This player pins its runtime and has no upstream updater"}], "Runtime exclusions changed")
    require(sha(payload / "runtime/duckstation-qt-x64-ReleaseLTCG.exe") == RUNTIME_EXE_SHA, "Runtime executable changed")
    (payload / "runtime/portable.txt").write_bytes(b"")
    shutil.copytree(package, payload / "patcher")
    require(not any(p.is_symlink() or p.is_junction() for p in (payload / "patcher").rglob("*")), "Linked patcher package")
    # The old GPL frontend resets every setting without its schema marker.
    defaults = (HERE / "settings.ini.template").read_text(encoding="utf-8")
    defaults = defaults.replace("[Main]\n", "[Main]\nSettingsVersion = 3\n", 1)
    defaults = defaults.replace("PathNTSCU = ps-22a.bin", "PathNTSCU = user-bios.bin")
    (payload / "defaults").mkdir()
    (payload / "defaults/settings.ini.template").write_text(defaults, encoding="utf-8")
    shutil.copyfile(HERE / "README_PLAYER.md", payload / "README_PLAYER.md")
    # Inspect all native runtime imports, including Qt plugins, to pin the VC
    # names checked on the player's PC. Microsoft code is never packaged.
    imports = []
    required_vc = set()
    reader = args.compiler / "bin/llvm-readobj.exe"
    for path in sorted((payload / "runtime").rglob("*")):
        if path.suffix.lower() not in (".exe", ".dll"):
            continue
        text = subprocess.check_output([str(reader), "--coff-imports", str(path)], text=True, encoding="utf-8")
        names = sorted(set(re.findall(r"^  Name: (.+)$", text, re.M)), key=str.lower)
        required_vc.update(name.lower() for name in names if VC_PATTERN.fullmatch(name))
        imports.append({"path": path.relative_to(payload).as_posix(), "imports": names})
    require(required_vc and len(required_vc) <= 8, "Unexpected Microsoft runtime dependency closure")
    release = {
        "format": "mass-driver-public-player-release-v1",
        "content_version": args.content_version,
        "source": manifest["source"], "game": manifest["output"],
        "runtime": {"tag": RUNTIME_TAG, "commit": RUNTIME_COMMIT,
                    "archive_sha256": RUNTIME_ZIP_SHA, "exe_sha256": RUNTIME_EXE_SHA,
                    "license": "GPL-3.0", "source_archive_sha256": SOURCE_ZIP_SHA},
        "bios": {"size": 524288, "ntsc_u_md5s": bios_md5s,
                 "source": f"https://github.com/stenzek/duckstation/blob/{RUNTIME_COMMIT}/src/core/bios.cpp"},
        "required_system_vc_dlls": sorted(required_vc),
        "microsoft_runtime_download": "https://aka.ms/vs/17/release/vc_redist.x64.exe",
        "microsoft_binaries_included": False,
    }
    (payload / "player-release.json").write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")
    notices = payload / "licenses"
    notices.mkdir()
    qt_notices = []
    for module, expected_hash in QT_SOURCE_HASHES.items():
        path = args.dependency_source_dir / f"{module}-everywhere-src-6.7.2.zip"
        require(sha(path) == expected_hash, "Qt source identity changed: " + module)
        with zipfile.ZipFile(path) as qt:
            for item in qt.infolist():
                name = PurePosixPath(item.filename)
                relative = PurePosixPath(*name.parts[1:])
                if item.is_dir() or not relative.parts:
                    continue
                # Keep full license texts and copyright notices, including Qt's
                # vendored libraries. No Qt implementation/source code is added
                # to the player payload; its complete sources ship separately.
                base = relative.name.upper()
                if any(p in ("tests", "examples") for p in relative.parts) or base.endswith(".JSON") or base == "LICENSEREF-QT-COMMERCIAL.TXT":
                    continue
                if relative.parts[0] != "LICENSES" and not base.startswith(("LICENSE", "COPYING", "NOTICE", "COPYRIGHT")):
                    continue
                require(not name.is_absolute() and ".." not in name.parts and item.file_size <= 2 * 1024 * 1024,
                        "Unsafe Qt notice path")
                target = notices / "Qt-6.7.2" / module / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(qt.read(item))
                qt_notices.append(target.relative_to(payload).as_posix())
    (notices / "Qt-6.7.2/README_NOTICES.txt").write_text(
        "Qt 6.7.2: Copyright The Qt Company Ltd. and other contributors.\n"
        "Unmodified dynamically linked Qt libraries/plugins accompany the GPL emulator.\n"
        "These are verbatim Qt and bundled-library license/copyright notices from the\n"
        "five exact source modules used by the pinned upstream dependency build script.\n"
        "Complete matching Qt source, upstream build scripts and notices are in the\n"
        "Emulator_Source companion next to this download. See GPL/LGPL texts here.\n"
        "To use modified libraries, replace files in a prepared payload and rebuild\n"
        "the player from its source, or run the upstream emulator directly.\n"
        "No signing key is required; component license rights are preserved.\n",
        encoding="utf-8")
    (notices / "EMULATOR_SOURCE.txt").write_text(
        f"DuckStation {RUNTIME_TAG}, commit {RUNTIME_COMMIT}, GPL version 3.\n"
        "Unmodified runtime binaries; separate Mass Driver launcher and generated settings.\n"
        "Matching source and dependency sources/build scripts are in the Emulator_Source companion\n"
        "next to the player download. They can be modified and redistributed under their licenses.\n"
        f"Upstream source: https://github.com/stenzek/duckstation/tree/{RUNTIME_COMMIT}\n"
        "Copyright (c) DuckStation contributors. No warranty; see runtime/LICENSE.txt and\n"
        "runtime/resources/thirdparty.html. The emulator developers do not endorse this dungeon.\n",
        encoding="utf-8")
    for name in ("LICENSE.TXT",):
        shutil.copyfile(args.compiler / name, notices / "llvm-mingw-LICENSE.txt")
    for path in (args.compiler / "x86_64-w64-mingw32/share/mingw32").glob("COPYING*"):
        shutil.copyfile(path, notices / ("mingw-w64-" + path.name + (".txt" if path.name == "COPYING" else "")))
    require(not (payload / "game").exists() and not (payload / "bios").exists(), "Private game/BIOS entered public payload")
    require(not any(VC_PATTERN.match(p.name) for p in payload.rglob("*")), "Microsoft binaries entered public payload")
    report = {"format": "mass-driver-public-player-payload-v1", "status": "prepared",
              "release": release, "runtime_exclusions": exclusions, "runtime_imports": imports,
              "qt_verbatim_license_notices": qt_notices,
              "payload_files": inventory(payload), "game_or_bios_bundled": False,
              "microsoft_binaries_bundled": False, "runtime_acceptance": "Not established by preparing a payload"}
    (output / "public-payload-preparation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("payload_files", "runtime_imports", "qt_verbatim_license_notices")}, indent=2))


if __name__ == "__main__":
    main()
