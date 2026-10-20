"""Prepare a fresh portable patch kit from a built, receipt-verified release.

Never edits a source disc, build receipt, historical manifest or existing kit.
The resulting kit contains the patch and package inputs, not either game BIN.
Preparation proves a clean retail Disc 2 -> exact release BIN round trip. It
does not establish gameplay acceptance or publish the package.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from shared.tools.xgdisc import Mode2Image

RETAIL_SIZE = 688_700_880
RETAIL_SHA256 = "5eab85c683d4d7087d345b587472db9c44df29b35ce66553c2626d26018b947e"
DECODER_COMMIT = "7508fd2a823443b1f0173ca361620f21d62a7d37"


def require(condition: bool, message: str):
    if not condition:
        raise RuntimeError(message)


def digest(path: Path):
    value = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(8 * 1024 * 1024):
            value.update(block)
    return value.hexdigest()


def pinned(path: Path, size: int, sha256: str, label: str):
    require(path.is_file(), f"{label} is missing: {path}")
    require(not path.is_symlink(), f"{label} must be a regular file: {path}")
    require(path.stat().st_size == size, f"{label} has the wrong size")
    require(digest(path) == sha256, f"{label} SHA-256 mismatch")


def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def run(arguments: list[str], log: Path | None = None):
    result = subprocess.run(arguments, text=True, encoding="utf-8", errors="replace",
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if log is not None:
        log.write_text(result.stdout, encoding="utf-8")
    require(result.returncode == 0, f"Tool failed ({result.returncode}): {result.stdout[-2000:]}")
    return result.stdout


def prepare(args):
    source = args.source_bin.resolve()
    release = args.release_dir.resolve()
    output = args.output_dir.resolve()
    encoder = args.xdelta.resolve()
    decoder_source = args.xdelta_source.resolve()
    license_path = args.perfect_works_license.resolve()
    require(not output.exists(), f"Output already exists; choose a new directory: {output}")
    pinned(source, RETAIL_SIZE, RETAIL_SHA256, "Clean USA Disc 2 source")
    source_stat = source.stat()
    receipt_path = release / "project-build.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    require(receipt.get("format") == "xenogears-project-build-v1" and receipt.get("status") == "built",
            "Release receipt does not describe a completed build")
    require(receipt["plan"]["profile"] == "mass_driver", "Receipt belongs to a different profile")
    require(receipt["plan"]["release"] == release.name, "Release directory and receipt disagree")
    require(receipt["content_versions"]["mass_driver"] == args.content_version,
            "Receipt content version differs from requested release version")
    bins = [item for item in receipt["outputs"] if item["path"].lower().endswith(".bin")]
    require(len(bins) == 1, "Receipt must contain exactly one final BIN")
    spec = bins[0]
    target = (release / spec["path"]).resolve()
    require(target.parent == release, "Final BIN must be a direct child of its release")
    pinned(target, spec["size"], spec["sha256"], "Built release BIN")
    require(source != target, "Source and target BIN paths must differ")
    require(encoder.is_file() and license_path.is_file(), "Encoder or Perfect Works license is missing")
    require(run(["git", "-C", str(decoder_source), "rev-parse", "HEAD"]).strip() == DECODER_COMMIT,
            "Decoder checkout is not at the pinned Apache source commit")
    require(not run(["git", "-C", str(decoder_source), "status", "--porcelain=v1", "--untracked-files=all"]).strip(),
            "Pinned decoder checkout is not clean")
    require((decoder_source / "xdelta3/LICENSE").is_file(), "Pinned xdelta license is missing")
    Mode2Image(source).read_index()
    Mode2Image(target).read_index()

    manifest = json.loads((HERE / "build_manifest.json").read_text(encoding="utf-8"))
    manifest["source"].update(size=RETAIL_SIZE, sha256=RETAIL_SHA256)
    require(manifest["decoder"]["source_commit"] == DECODER_COMMIT, "Template decoder pin changed")
    compiler_license = None
    if args.mingw_directory is not None:
        compiler_license = args.mingw_directory.resolve() / "LICENSE.TXT"
        require(compiler_license.is_file(), "Portable compiler license is missing")
        manifest["compiler_runtime_license"] = {
            "relative_path": "MassDriverData/licenses/llvm-mingw-LICENSE.txt",
            "size": compiler_license.stat().st_size, "sha256": digest(compiler_license),
        }
        runtime_notices = args.mingw_directory.resolve() / "x86_64-w64-mingw32/share/mingw32"
        manifest["compiler_runtime_notices"] = []
        for name in ("COPYING", "COPYING.MinGW-w64.txt", "COPYING.MinGW-w64-runtime.txt",
                     "COPYING.winpthreads.txt", "COPYING.winstorecompat.txt"):
            notice = runtime_notices / name
            require(notice.is_file(), f"Portable runtime notice is missing: {name}")
            destination = f"mingw-w64-{name}" + (".txt" if name == "COPYING" else "")
            manifest["compiler_runtime_notices"].append({
                "relative_path": f"MassDriverData/licenses/{destination}",
                "source_name": name, "size": notice.stat().st_size, "sha256": digest(notice),
            })

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".prepare-mass-driver-", dir=output.parent) as temporary:
        stage = Path(temporary).resolve()
        require(stage.parent == output.parent, "Preparation staging escaped its destination parent")
        kit = stage / "kit"
        kit.mkdir()
        patch = kit / "Mass_Driver.xdelta"
        # No secondary compressor or application-header filename is embedded.
        run([str(encoder), "-e", "-D", "-S", "none", "-A", "-s", str(source), str(target), str(patch)],
            kit / "encode.log")
        with patch.open("rb") as stream:
            require(stream.read(5) == bytes.fromhex("d6c3c40000"),
                    "Encoder did not produce plain VCDIFF without secondary/application headers")
        scratch_parent = args.scratch_directory.resolve() if args.scratch_directory else stage
        scratch_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".mass-driver-roundtrip-", dir=scratch_parent) as scratch:
            scratch_path = Path(scratch).resolve()
            require(scratch_path.parent == scratch_parent, "Roundtrip scratch escaped its parent")
            roundtrip = scratch_path / "roundtrip.bin"
            run([str(encoder), "-d", "-D", "-R", "-s", str(source), str(patch), str(roundtrip)],
                kit / "roundtrip.log")
            pinned(roundtrip, spec["size"], spec["sha256"], "Retail-source reconstructed BIN")
        require(source.stat().st_size == source_stat.st_size and
                source.stat().st_mtime_ns == source_stat.st_mtime_ns and digest(source) == RETAIL_SHA256,
                "Original retail source changed during preparation")
        require(digest(target) == spec["sha256"], "Built target changed during preparation")
        cue = kit / "Mass_Driver.cue.template"
        shutil.copyfile(HERE / "game.cue.template", cue)
        manifest["patch"].update(size=patch.stat().st_size, sha256=digest(patch))
        manifest["cue_template"].update(size=cue.stat().st_size, sha256=digest(cue))
        manifest["output"].update(bin_size=spec["size"], bin_sha256=spec["sha256"],
                                   cue_size=cue.stat().st_size, cue_sha256=digest(cue))
        write_json(kit / "portable-build-manifest.json", manifest)
        licenses = kit / "licenses"
        licenses.mkdir()
        shutil.copyfile(license_path, licenses / "Perfect_Works_GPL-3.0.txt")
        shutil.copyfile(decoder_source / "xdelta3/LICENSE", licenses / "xdelta-Apache-2.0.txt")
        if compiler_license is not None:
            shutil.copyfile(compiler_license, licenses / "llvm-mingw-LICENSE.txt")
            for notice in manifest["compiler_runtime_notices"]:
                shutil.copyfile(runtime_notices / notice["source_name"],
                                licenses / Path(notice["relative_path"]).name)
        evidence = {
            "format": "mass-driver-portable-preparation-v1", "status": "passed",
            "prepared_utc": datetime.now(timezone.utc).isoformat(),
            "release": release.name, "content_version": args.content_version,
            "receipt_sha256": digest(receipt_path), "source_sha256": RETAIL_SHA256,
            "target_size": spec["size"], "target_sha256": spec["sha256"],
            "patch_size": patch.stat().st_size, "patch_sha256": digest(patch),
            "encoder_sha256": digest(encoder), "pinned_decoder_commit": DECODER_COMMIT,
            "clean_retail_roundtrip_exact": True, "source_unchanged": True,
            "runtime_acceptance": "Not established by package preparation",
            "publication": "Not published; this is a release-specific package input kit",
        }
        write_json(kit / "preparation-report.json", evidence)
        require(not output.exists(), "Output appeared during preparation; refusing replacement")
        os.rename(kit, output)
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-bin", type=Path, required=True)
    parser.add_argument("--release-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--xdelta", type=Path, required=True)
    parser.add_argument("--xdelta-source", type=Path, required=True)
    parser.add_argument("--perfect-works-license", type=Path, required=True)
    parser.add_argument("--mingw-directory", type=Path)
    parser.add_argument("--scratch-directory", type=Path,
                        help="Optional parent for the temporary reconstructed BIN (may be another drive)")
    parser.add_argument("--content-version", default="V176")
    args = parser.parse_args()
    try:
        evidence = prepare(args)
    except (OSError, KeyError, ValueError, RuntimeError) as exc:
        print(f"Preparation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(evidence, indent=2))
    print(f"Release input kit: {args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
