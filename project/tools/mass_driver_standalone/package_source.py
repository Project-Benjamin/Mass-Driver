"""Create and verify a deterministic source-only companion; no private payload inputs."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
PREFIX = "tools/mass_driver_standalone/"
NAMES = {
    "app.manifest", "archive.cpp", "archive.h", "build.py", "main.cpp",
    "pack_payload.py", "prepare_payload.py", "README_PRIVATE.md", "README.md",
    "settings.ini.template", "verify.py", "verify_upgrade.py", "package_source.py",
    "game.cue.template", "licenses/Perfect_Works_0.10.2_GPL-3.0.txt",
    "public_player.h", "prepare_public_payload.py", "verify_public.py", "README_PLAYER.md",
    "licenses/DuckStation_7371_GPL-3.0.txt",
}
PUBLIC_GUIDE = """Mass Driver public player V176 - Windows x64 source companion

This archive contains the shared native installer/Play launcher source, public
and historical private build modes, preparation/QA scripts and license notices.
No game image, BIOS, emulator binary, Microsoft binary, patch payload, user data
or compiler is included. The public mode asks each player for their own Disc 2
and BIOS and constructs a separate local game. It never modifies source inputs.

Read tools/mass_driver_standalone/README.md. The public entry points are
prepare_public_payload.py, build.py --public and verify_public.py. The runtime
is official GPL DuckStation v0.1-7371, exact source commit:
b2577ef8bdaae99840874b6dae8146f0316357b4.
Its matching full source/dependency archive is a separate Emulator_Source
companion supplied next to the player download. Runtime notices and the GPL
license are retained in the installed program. No endorsement is implied.

The portable patcher's own source companion and matching complete Mass Driver
project-source companion are separate. Reconstructing a game patch requires
their external original-disc and extracted-data inputs. This source archive
does not contain copyrighted retail game/firmware bytes.

To use a modified GPL emulator or Qt library, replace the appropriate files in
an independently prepared payload, update its descriptive player-release.json,
then run build.py --public. The builder pins the bytes of YOUR payload; no
signing key or password is needed. You may also run the upstream emulator
directly, independently of the Mass Driver integrity-checking launcher.
Preserve the component licenses/notices when making changes. This archive
does not restrict the rights granted by those licenses.

Official compiler: llvm-mingw 20261006 UCRT x86_64 portable distribution:
https://github.com/mstorsjo/llvm-mingw/releases/download/20261006/llvm-mingw-20261006-ucrt-x86_64.zip
SHA256: 317492c456aa27ee607a5919f1d2d38dcdc1112516a24d0bf4b00d078f52d17a
The compiler and prepared payload remain external build-time inputs.

Fixed ZIP metadata and source-manifest.json make this companion reproducible.
Hashes identify bytes, not a publisher signature or full gameplay acceptance.
"""
GUIDE = """Mass Driver private standalone V174 â€” Windows x64 source companion

This archive contains installer/launcher source only. It contains no game image,
BIOS, runtime executables, Microsoft DLLs, user configuration, saves, or compiler.
The CUE text template and original Perfect Works GPL notice are included.
It does not establish public redistribution clearance for any private input.

Extract into the matching project source root, preserving tools/ paths. Read
tools/mass_driver_standalone/README.md for preparation, build and headless QA.
prepare_payload.py needs the matching canonical shared.tools.xgdisc module from
the separate project source companion. build.py and pack_payload.py operate on
an independently prepared, verified private payload directory.

Actual compiler: official llvm-mingw 20261006 UCRT x86_64 portable distribution:
https://github.com/mstorsjo/llvm-mingw/releases/download/20261006/llvm-mingw-20261006-ucrt-x86_64.zip
Archive SHA256: 317492c456aa27ee607a5919f1d2d38dcdc1112516a24d0bf4b00d078f52d17a
The game release receipt, reviewed runtime and Microsoft CRT inventories, local
BIOS, runtime/compiler license notices and verified input bytes remain external inputs.
The preparation report pins their identities; they are deliberately not included.

All installer, launcher and source ZIP hashes describe identity, not a code
signature. No signing certificate is supplied. A headless packaging audit does
not establish native game boot, complete gameplay, or clean-machine acceptance.

source-manifest.json records every source entry's exact size and SHA256. Fixed ZIP
metadata makes this source archive reproducible from the same source bytes.
"""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--public", dest="public_source", action="store_true")
    parser.add_argument("--player-release", type=Path,
                        help="Actual public player-release.json; includes identities only, no payload data")
    args = parser.parse_args()
    output = args.output_root.resolve()
    if output.exists():
        raise RuntimeError("Choose a fresh source-companion destination")
    payload = {PREFIX + name: (HERE / name).read_bytes() for name in sorted(NAMES)}
    payload["README_SOURCE.txt"] = (PUBLIC_GUIDE if args.public_source else GUIDE).encode("utf-8")
    if args.player_release:
        document = json.loads(args.player_release.read_text(encoding="utf-8"))
        if document.get("format") != "mass-driver-public-player-release-v1":
            raise RuntimeError("Unrecognized public release identity")
        payload["release/player-release.json"] = args.player_release.read_bytes()
    files = [{"path": name, "size": len(data), "sha256": digest(data)}
             for name, data in sorted(payload.items())]
    manifest = {"format": "mass-driver-public-player-source-v1" if args.public_source else "mass-driver-private-standalone-source-v1", "files": files,
                "game_bios_runtime_or_user_data_included": False}
    payload["source-manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    output.mkdir(parents=True)
    archive = output / ("Mass_Driver_Player_Source_V176.zip" if args.public_source else "Mass_Driver_Private_V174_Installer_Source.zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as target:
        for name, data in sorted(payload.items()):
            entry = zipfile.ZipInfo(name, date_time=(2026, 10, 19, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            target.writestr(entry, data, compresslevel=9)
    with zipfile.ZipFile(archive) as check:
        assert check.namelist() == sorted(payload)
        for name, data in payload.items():
            assert check.read(name) == data
    report = {"format": manifest["format"], "status": "passed", "archive": archive.name,
              "size": archive.stat().st_size, "sha256": digest(archive.read_bytes()),
              "source_entries": len(files), "zip_entries": len(payload),
              "all_archived_bytes_verified": True, "deterministic_metadata": True,
              "game_bios_runtime_or_user_data_included": False, "files": files}
    (output / "source-package-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "files"}, indent=2))


if __name__ == "__main__":
    main()
