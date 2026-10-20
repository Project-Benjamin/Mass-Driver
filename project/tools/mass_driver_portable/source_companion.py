"""Create a deterministic source-only companion for the portable patcher.

Copies owned text sources and verbatim dependency notices. No executable,
patch payload, game image, emulator, BIOS or extracted game asset is included.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
DECODER_COMMIT = "7508fd2a823443b1f0173ca361620f21d62a7d37"
ALLOWED_SUFFIXES = {".cpp", ".h", ".ps1", ".py", ".md", ".rc", ".manifest", ".json", ".template"}
PREFIX = "Xenogears_Mass_Driver_Patcher_Source"


def sha(data: bytes):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--xdelta-source", type=Path, required=True)
    parser.add_argument("--mingw-directory", type=Path, required=True)
    parser.add_argument("--download-provenance", type=Path, required=True)
    parser.add_argument("--perfect-works-license", type=Path, required=True)
    parser.add_argument("--upstream-provenance", type=Path, required=True)
    parser.add_argument("--build-manifest", type=Path,
                        help="Optional actual release-specific manifest; never use invented payload hashes")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists():
        raise SystemExit("Choose a new source-companion output directory; existing artifacts are preserved.")
    decoder_source = args.xdelta_source.resolve()
    commit = subprocess.check_output(["git", "-C", str(decoder_source), "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output(["git", "-C", str(decoder_source), "status", "--porcelain=v1", "--untracked-files=all"], text=True)
    if commit != DECODER_COMMIT or status.strip():
        raise SystemExit("Decoder checkout must be clean at its exact pinned Apache source commit.")
    files = {}
    for path in sorted(HERE.rglob("*")):
        relative = path.relative_to(HERE)
        if any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
            continue
        if path.is_file() and path.suffix in ALLOWED_SUFFIXES:
            if path.is_symlink():
                raise SystemExit(f"Source companion refuses linked input: {relative}")
            files[f"tools/mass_driver_portable/{relative.as_posix()}"] = path.read_bytes()
    files["licenses/xdelta-Apache-2.0.txt"] = (decoder_source / "xdelta3/LICENSE").read_bytes()
    files["licenses/llvm-mingw-LICENSE.txt"] = (args.mingw_directory / "LICENSE.TXT").read_bytes()
    for name in ("COPYING", "COPYING.MinGW-w64.txt", "COPYING.MinGW-w64-runtime.txt",
                 "COPYING.winpthreads.txt", "COPYING.winstorecompat.txt"):
        destination = f"mingw-w64-{name}" + (".txt" if name == "COPYING" else "")
        files[f"licenses/{destination}"] = (args.mingw_directory / "x86_64-w64-mingw32/share/mingw32" / name).read_bytes()
    files["licenses/Perfect_Works_GPL-3.0.txt"] = args.perfect_works_license.read_bytes()
    downloads = json.loads(args.download_provenance.read_text(encoding="utf-8"))
    upstream = json.loads(args.upstream_provenance.read_text(encoding="utf-8"))
    provenance = {
        "decoder_repository": "https://github.com/jmacd/xdelta",
        "decoder_commit": DECODER_COMMIT,
        "decoder_source": f"https://github.com/jmacd/xdelta/tree/{DECODER_COMMIT}",
        "decoder_license_sha256": sha(files["licenses/xdelta-Apache-2.0.txt"]),
        "official_tool_downloads": downloads,
        "perfect_works": upstream,
    }
    files["DEPENDENCY_PROVENANCE.json"] = (json.dumps(provenance, indent=2) + "\n").encode()
    if args.build_manifest is not None:
        data = args.build_manifest.read_bytes()
        document = json.loads(data)
        if document.get("format") != "xenogears-mass-driver-build-v1":
            raise SystemExit("Unrecognized release-specific build manifest")
        files["release/portable-build-manifest.json"] = data
    files["README_SOURCE.md"] = (
        "# Mass Driver portable patcher source\n\n"
        "This archive contains the portable Windows patcher's source, build and verification scripts, "
        "release-input preparation script, and dependency notices/provenance. It contains no game data.\n\n"
        "Keep the tools/mass_driver_portable path when combining this archive with the matching full "
        "Mass Driver project-source companion. prepare_release.py imports the project's canonical "
        "shared.tools.xgdisc; that shared code and the game builder belong to the full project companion.\n\n"
        "The GUI builder can also be used on its own with explicit input paths. Follow "
        "tools/mass_driver_portable/BUILDING.md. Obtain the exact clean pinned xdelta source and the "
        "official portable compiler described in DEPENDENCY_PROVENANCE.json. No machine-wide compiler "
        "installation is needed for the llvm-mingw path.\n\n"
        "tools/mass_driver_portable/build_manifest.json is a historical V161 payload template. "
        "Its old output hashes do not describe a new release. Use a newly prepared release manifest; "
        "when supplied, the matching one is at release/portable-build-manifest.json.\n\n"
        "The player patch EXE/ZIP and matching full project source are separate companion artifacts. "
        "This archive alone does not claim to be the full corresponding source of the game mod, "
        "nor does source availability establish gameplay acceptance. Preserve dependency notices.\n"
    ).encode()
    sums = "".join(f"{sha(data)}  {name}\n" for name, data in sorted(files.items()))
    files["SHA256SUMS.txt"] = sums.encode()
    output.mkdir(parents=True)
    archive = output / "Xenogears_Mass_Driver_Patcher_Source.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(f"{PREFIX}/{name}", date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0
            package.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(archive) as package:
        if len(package.namelist()) != len(files) or package.testzip() is not None:
            raise RuntimeError("Source archive inventory/integrity failed")
        for name, data in files.items():
            if package.read(f"{PREFIX}/{name}") != data:
                raise RuntimeError(f"Source archive mismatch: {name}")
    report = {
        "status": "passed", "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Owned portable patcher source and dependency notices; no game data",
        "file_count": len(files), "zip_size": archive.stat().st_size,
        "zip_sha256": sha(archive.read_bytes()),
        "contains_release_specific_manifest": args.build_manifest is not None,
        "files": [{"path": name, "size": len(data), "sha256": sha(data)}
                  for name, data in sorted(files.items())],
    }
    (output / "source-companion-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "files"}, indent=2))
    print(f"Source companion: {archive}")


if __name__ == "__main__":
    main()
