"""Exercise the actual public native player without UI, runtime or software install.

The optional Microsoft test downloads its official installer and checks its
signature/publisher. It never opens that installer or changes system software.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while data := stream.read(8 << 20):
            digest.update(data)
    return digest.hexdigest()


def state(path):
    return (path.stat().st_size, path.stat().st_mtime_ns, sha(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installer", type=Path, required=True)
    parser.add_argument("--build-report", type=Path, required=True)
    parser.add_argument("--payload-root", type=Path, required=True)
    parser.add_argument("--source-bin", type=Path, required=True)
    parser.add_argument("--bios", type=Path, required=True)
    parser.add_argument("--qa-root", type=Path, required=True)
    parser.add_argument("--test-microsoft-download", action="store_true")
    args = parser.parse_args()
    qa = args.qa_root.resolve()
    require(not qa.exists(), "Choose a new owned QA root")
    installer = args.installer.resolve()
    payload = args.payload_root.resolve()
    contract = json.loads(args.build_report.read_text(encoding="utf-8"))
    release = json.loads((payload / "player-release.json").read_text(encoding="utf-8"))
    require(contract["format"] == "mass-driver-public-player-build-v1", "Wrong public build contract")
    require(sha(installer) == contract["installer"]["sha256"], "Installer identity differs")
    require(not (payload / "game").exists() and not (payload / "bios").exists(), "Private inputs entered payload")
    require(not any(re.fullmatch(r"(?:msvcp140|vcruntime140|concrt140|vcomp140).*\.dll", p.name, re.I)
                    for p in payload.rglob("*")), "Microsoft binaries entered payload")
    sources = {p.resolve(): state(p.resolve()) for p in (args.source_bin, args.bios, installer)}
    qa.mkdir(parents=True)
    transcript = []

    def run(exe, arguments, expected=0):
        result = subprocess.run([str(exe), "--headless", *map(str, arguments)], capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=240)
        transcript.append({"exe": str(exe), "arguments": list(map(str, arguments)),
                           "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        (qa / "transcript-in-progress.json").write_text(json.dumps(transcript, indent=2) + "\n", encoding="utf-8")
        require(result.returncode == expected, f"Unexpected result {result.returncode}, expected {expected}: {result.stderr}")
        return result

    run(installer, ["--inspect"])
    for flag, name in (("--cancel-before", "cancel-pre"), ("--cancel-during", "cancel-mid")):
        target = qa / name
        run(installer, ["--install", "--root", target, flag], 61)
        require(not (target / "installation.txt").exists() and not list(target.glob(".install-*")), "Cancelled extraction committed or left staging")
        require(not list((target / "v").iterdir()), "Cancelled extraction committed version")
    root = qa / "installed"
    run(installer, ["--install", "--root", root])
    identity = (root / "installation.txt").read_text().strip()
    version = root / "v" / identity[:16]
    for spec in contract["payload_files"]:
        path = version / spec["path"]
        require(path.stat().st_size == spec["size"] and sha(path) == spec["sha256"], "Installed payload differs: " + spec["path"])
    play = root / "Play Mass Driver.exe"
    require(sha(play) == contract["play_launcher"]["sha256"], "Installed launcher differs")
    run(play, ["--check-installed"])
    run(play, ["--launch-check"], 41)
    settings = root / "UserData/settings.ini"
    text = settings.read_text(encoding="utf-8")
    require("SettingsVersion = 3" in text and "SetupWizardIncomplete = false" in text, "GPL frontend schema/wizard defaults differ")
    require(str(root / "UserData/bios").replace("\\", "/") in text and "PathNTSCU = user-bios.bin" in text, "User-owned BIOS routing differs")
    require("Macro" not in text and "TogglePause = Keyboard/Space" in text, "Test bindings entered defaults")
    with settings.open("a", encoding="utf-8") as target:
        target.write("\n[OwnedPublicQA]\nPreference = preserve exactly\n")
    card = root / "UserData/memcards/preserve-public-qa.mcd"
    card.write_bytes(b"owned public QA card sentinel\x00\xff")
    user_before = {settings: state(settings), card: state(card)}
    wrong = qa / "wrong.bin"
    wrong.write_bytes(b"wrong")
    run(play, ["--setup", "--source", wrong, "--bios", args.bios], 42)
    with wrong.open("wb") as stream:
        stream.truncate(release["source"]["size"])
    run(play, ["--setup", "--source", wrong, "--bios", args.bios], 42)
    run(play, ["--setup", "--source", args.source_bin], 43)
    bad_bios = qa / "wrong-bios.bin"
    bad_bios.write_bytes(b"\0" * 524288)
    run(play, ["--setup", "--source", args.source_bin, "--bios", bad_bios], 44)
    run(play, ["--setup", "--source", args.source_bin, "--bios", args.bios, "--cancel-before"], 61)
    require(not (root / "Game").exists() and not (root / "UserData/bios/user-bios.bin").exists(), "Invalid/cancelled setup copied input")
    run(play, ["--setup", "--source", args.source_bin, "--bios", args.bios, "--cancel-during"], 61)
    require(not list((root / "Game").iterdir()) and not (root / "UserData/bios/user-bios.bin").exists(), "Cancelled decoder left staging or copied BIOS")
    run(play, ["--setup", "--source", args.source_bin, "--bios", args.bios])
    game = root / "Game" / release["game"]["bin_sha256"][:16]
    generated = game / "Xenogears_Mass_Driver.bin"
    cue = game / "Xenogears_Mass_Driver.cue"
    bios = root / "UserData/bios/user-bios.bin"
    require(generated.stat().st_size == release["game"]["bin_size"] and sha(generated) == release["game"]["bin_sha256"], "Native player reconstruction differs")
    require(sha(cue) == release["game"]["cue_sha256"] and sha(bios) == sources[args.bios.resolve()][2], "CUE/BIOS copy differs")
    saved = {p: state(p) for p in (generated, cue, bios, settings, card)}
    run(play, ["--setup", "--source", args.source_bin, "--bios", args.bios])
    require(saved == {p: state(p) for p in saved}, "Repeated setup changed generated game, BIOS or private data")
    require(user_before == {p: state(p) for p in user_before}, "Setup changed canonical settings/cards")
    prerequisites = run(play, ["--check-prerequisites"])
    require("MICROSOFT_VC_RUNTIME_READY=true" in prerequisites.stdout, "This QA host lacks required Microsoft runtime")
    dry = run(play, ["--launch-check"])
    require("RUNTIME_LAUNCHED=false" in dry.stdout and str(cue).replace("\\", "/") in dry.stdout, "Dry launch plan differs")
    session = (version / "runtime/settings.ini").read_text(encoding="utf-8")
    require("SettingsVersion = 3" in session and str(root / "UserData/bios").replace("\\", "/") in session, "Session defaults/routing differ")
    run(play, ["--verify-prerequisite", "--file", installer], 46)
    download_verified = False
    if args.test_microsoft_download:
        official = qa / "official-vc-redist.exe"
        run(play, ["--download-prerequisite", "--file", official])
        run(play, ["--verify-prerequisite", "--file", official])
        before = state(official)
        run(play, ["--download-prerequisite", "--file", official], 46)
        require(before == state(official), "Download overwrote an existing file")
        download_verified = True
    # Repair only an owned damaged immutable file; inputs and generated content
    # remain outside the version. No user memory card is ever opened by a game.
    damaged = version / "README_PLAYER.md"
    with damaged.open("r+b") as stream:
        byte = stream.read(1); stream.seek(0); stream.write(bytes([byte[0] ^ 1]))
    run(play, ["--check-installed"], 20)
    run(installer, ["--install", "--root", root])
    run(play, ["--check-installed"])
    require(saved == {p: state(p) for p in saved}, "Repair changed generated game, BIOS, settings or card")
    for spec in contract["payload_files"]:
        require(sha(version / spec["path"]) == spec["sha256"], "Repaired payload differs")
    long_root = qa / ("long-" + "x" * 110)
    run(installer, ["--install", "--root", long_root], 20)
    require(not long_root.exists(), "Overlong install wrote files")
    changed = qa / "changed-installer.exe"
    shutil.copyfile(installer, changed)
    with changed.open("r+b") as stream:
        stream.seek(-1, 2); value = stream.read(1); stream.seek(-1, 2); stream.write(bytes([value[0] ^ 1]))
    run(changed, ["--inspect"], 10)
    require(sources == {p: state(p) for p in sources}, "Original input/installer changed")
    report = {"format": "mass-driver-public-player-headless-qa-v1", "status": "passed",
              "installer_sha256": contract["installer"]["sha256"],
              "payload_files_verified": len(contract["payload_files"]), "qa_install_root": str(root),
              "generated_game_sha256": sha(generated), "clean_retail_reconstruction_exact": True,
              "no_game_bios_or_microsoft_binaries_in_payload": True,
              "missing_inputs_and_wrong_disc_bios_rejected": True, "setup_cancel_retry_verified": True,
              "repeated_setup_and_repair_preserve_game_bios_cards_settings": True,
              "unsigned_prerequisite_rejected": True,
              "official_microsoft_download_signature_and_publisher_verified": download_verified,
              "microsoft_installer_executed": False, "native_gui_or_runtime_launched": False,
              "source_inputs_unchanged": True, "transcript": transcript}
    (qa / "qa-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "transcript"}, indent=2))


if __name__ == "__main__":
    main()
