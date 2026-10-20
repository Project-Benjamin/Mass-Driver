"""Prepare an explicitly private, noncommercial local game/runtime/firmware payload.

No publishing or redistribution clearance is implied. Inputs remain unchanged.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from shared.tools.xgdisc import Mode2Image

DUCK_COMMIT = "c66b2694da65cece8886ed3d4a069098831f8358"
DUCK_SHA = "ade6b3cd7a8329a658a402f065c81136e19511962a1f5e0c1a4c30a50392cdca"
BIOS_SHA = "71af94d1e47a68c11e8fdb9f8368040601514a42a5a399cda48c7d3bff1e99d3"

def require(condition, message):
    if not condition: raise RuntimeError(message)

def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while data := stream.read(8 << 20): value.update(data)
    return value.hexdigest()

def pinned(path, size, digest):
    require(path.is_file() and not path.is_symlink() and not path.is_junction(), f"Invalid regular input: {path}")
    require(path.stat().st_size == size and sha(path) == digest, f"Input identity differs: {path}")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-dir", type=Path, required=True)
    parser.add_argument("--runtime-inventory", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--bios", type=Path, required=True)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--crt-inventory", type=Path, required=True,
                        help="Independently verified private app-local Microsoft VC runtime file inventory")
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    release, runtime, bios, output = (p.resolve() for p in (args.release_dir, args.runtime_root, args.bios, args.output_root))
    require(not output.exists(), "Choose a fresh private output directory")
    inventory = json.loads(args.runtime_inventory.read_text(encoding="utf-8-sig"))
    require(inventory["format"] == "mass-driver-local-runtime-inventory-v1" and
            Path(inventory["runtime_root"]).resolve() == runtime, "Unexpected runtime inventory")
    receipt = json.loads((release / "project-build.json").read_text(encoding="utf-8"))
    require(receipt["status"] == "built" and receipt["plan"]["profile"] == "mass_driver" and
            receipt["content_versions"]["mass_driver"] == "V174", "Need the built V174 Mass Driver receipt")
    images = [value for value in receipt["outputs"] if value["path"].lower().endswith(".bin")]
    require(len(images) == 1, "Expected one final game image")
    image_spec = images[0]; image = (release / image_spec["path"]).resolve()
    require(image.parent == release, "Game image escaped release directory")
    pinned(image, image_spec["size"], image_spec["sha256"])
    Mode2Image(image).read_index()
    pinned(bios, 524288, BIOS_SHA)
    selected, exclusions = [], []
    for spec in inventory["runtime_files"]:
        name = spec["path"]
        require(".." not in name and "\\" not in name and not Path(name).is_absolute(), "Unsafe runtime inventory path")
        path = runtime / name
        pinned(path, spec["size"], spec["sha256"])
        if name in {"updater.exe", "uninstaller.exe"}:
            exclusions.append({**spec, "reason": "Standalone private package uses its own installation; no updater/uninstaller bundled"})
            continue
        if "/" in name:
            require(name.split("/", 1)[0] in {"QtPlugins", "resources", "translations"}, f"Unexpected runtime data directory: {name}")
        else:
            require(Path(name).suffix.lower() == ".dll" or name in
                    {"duckstation-qt-x64-ReleaseLTCG.exe", "LICENSE.txt", "qt.conf"}, f"Unexpected runtime root file: {name}")
        selected.append(spec)
    require(len(selected) == 247 and len(exclusions) == 2, "Runtime inventory/exclusions changed")
    require(next(item for item in selected if item["path"] == "duckstation-qt-x64-ReleaseLTCG.exe")["sha256"] == DUCK_SHA,
            "Installed DuckStation executable identity changed")
    require(any(item["path"] == "resources/thirdparty.html" for item in selected), "Missing third-party runtime notices")
    crt_files=[]
    crt_record=None
    if args.crt_inventory:
        crt_record=json.loads(args.crt_inventory.read_text(encoding="utf-8-sig"))
        require(crt_record["format"]=="mass-driver-private-crt-inventory-v1", "Unexpected private CRT inventory")
        names=set()
        for spec in crt_record["files"]:
            source=Path(spec["path"]).resolve();name=spec["name"]
            require(source.name.lower()==name.lower() and Path(name).name==name and name.lower().endswith(".dll") and
                    name.lower().startswith(("msvcp140","vcruntime140","concrt140","vcomp140")), "CRT inventory contains an unapproved component")
            require(name.lower() not in names and spec["signature_status"]=="Valid", "CRT name/signature verification changed")
            require("Microsoft" in spec["signer_subject"], "Private CRT signer is not Microsoft")
            require(spec["pe_machine"]=="AMD64 (0x8664)", "Private CRT architecture is not AMD64")
            names.add(name.lower());pinned(source,spec["size"],spec["sha256"]);crt_files.append(spec)
        require(names=={"msvcp140.dll","msvcp140_1.dll","msvcp140_2.dll","msvcp140_atomic_wait.dll",
                        "vcruntime140.dll","vcruntime140_1.dll"}, "Expected reviewed Microsoft VC dependency closure")
    output.mkdir(parents=True)
    payload = output / "payload"; payload.mkdir()
    for spec in selected:
        source = runtime / spec["path"]; target = payload / "runtime" / spec["path"]
        target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
        pinned(target, spec["size"], spec["sha256"])
    (payload / "runtime/portable.txt").write_bytes(b"")
    for spec in crt_files:
        target=payload/"runtime"/spec["name"]
        if not target.exists():shutil.copyfile(spec["path"],target)
        pinned(target,spec["size"],spec["sha256"])
    (payload / "game").mkdir()
    shutil.copyfile(image, payload / "game/Xenogears_Mass_Driver.bin")
    pinned(payload / "game/Xenogears_Mass_Driver.bin", image_spec["size"], image_spec["sha256"])
    shutil.copyfile(HERE / "game.cue.template", payload / "game/Xenogears_Mass_Driver.cue")
    (payload / "bios").mkdir(); shutil.copyfile(bios, payload / "bios/ps-22a.bin")
    (payload / "defaults").mkdir(); shutil.copyfile(HERE / "settings.ini.template", payload / "defaults/settings.ini.template")
    shutil.copyfile(HERE / "README_PRIVATE.md", payload / "README_PRIVATE.md")
    notices = payload / "licenses"; notices.mkdir()
    for name in ("LICENSE.TXT",): shutil.copyfile(args.compiler / name, notices / "llvm-mingw-LICENSE.txt")
    compiler_notices = args.compiler / "x86_64-w64-mingw32/share/mingw32"
    for path in compiler_notices.glob("COPYING*"):
        shutil.copyfile(path, notices / ("mingw-w64-" + path.name + (".txt" if path.name == "COPYING" else "")))
    shutil.copyfile(HERE / "licenses/Perfect_Works_0.10.2_GPL-3.0.txt",
                    notices / "Perfect_Works_GPL-3.0.txt")
    provenance = {
        "scope": "Private noncommercial local package only; not published or cleared for public redistribution",
        "duckstation_commit": DUCK_COMMIT,
        "duckstation_readme": f"https://github.com/stenzek/duckstation/blob/{DUCK_COMMIT}/README.md",
        "duckstation_license": f"https://github.com/stenzek/duckstation/blob/{DUCK_COMMIT}/LICENSE",
        "perfect_works": "https://github.com/PWBuild-Team/Perfect_Works_Build/tree/0.10.2",
        "game_release": release.name, "game_size": image_spec["size"], "game_sha256": image_spec["sha256"],
        "bios_size": 524288, "bios_sha256": BIOS_SHA,
        "app_local_microsoft_vc_runtime_files":len(crt_files),
    }
    (notices / "PRIVATE_PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n")
    if crt_record is not None:
        # Exact local signed-file identities are private provenance, not public redistribution clearance.
        (notices/"PRIVATE_MICROSOFT_RUNTIME_PROVENANCE.json").write_text(json.dumps(crt_record,indent=2)+"\n",encoding="utf-8")
    report = {**provenance, "status": "prepared", "runtime_files": selected, "excluded_runtime_files": exclusions,
              "payload_files": [{"path": p.relative_to(payload).as_posix(), "size": p.stat().st_size, "sha256": sha(p)}
                                for p in sorted(payload.rglob("*")) if p.is_file()],
              "runtime_source_inventory_sha256": sha(args.runtime_inventory), "receipt_sha256": sha(release / "project-build.json"),
              "original_inputs_unchanged": True}
    for spec in inventory["runtime_files"]: pinned(runtime / spec["path"], spec["size"], spec["sha256"])
    for spec in crt_files:pinned(Path(spec["path"]),spec["size"],spec["sha256"])
    pinned(image, image_spec["size"], image_spec["sha256"]); pinned(bios, 524288, BIOS_SHA)
    (output / "payload-preparation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key not in {"runtime_files", "payload_files"}}, indent=2))

if __name__ == "__main__": main()
