"""Headless compact-layout upgrade QA against an explicitly supplied prior QA install.

Only an installation named by a successful prior headless QA report is accepted.
No GUI or game runtime is started. Existing private data and old content are hashed
before and after the new installer runs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while data := stream.read(8 << 20):
            value.update(data)
    return value.hexdigest()


def inventory(root):
    require(root.is_dir() and not root.is_symlink(), "Missing or linked QA directory")
    result = {}
    for item in sorted(root.rglob("*")):
        require(not item.is_symlink() and not item.is_junction(), "Linked QA data")
        if item.is_file():
            result[item.relative_to(root).as_posix()] = {
                "size": item.stat().st_size,
                "mtime_ns": item.stat().st_mtime_ns,
                "sha256": sha(item),
            }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous-qa-report", type=Path, required=True)
    parser.add_argument("--installer", type=Path, required=True)
    parser.add_argument("--build-report", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    previous_path = args.previous_qa_report.resolve()
    previous = json.loads(previous_path.read_text(encoding="utf-8"))
    require(previous.get("status") == "passed" and previous.get("gui_or_game_runtime_launched") is False,
            "Prior report must describe a successful headless QA installation")
    root = Path(previous["qa_install_root"]).resolve()
    require(root == previous_path.parent / "installed", "Prior QA report root differs from owned QA directory")
    require(not args.report.exists(), "Choose a new report path")
    old_versions = root / "versions"
    require(old_versions.is_dir() and not (root / "v").exists(), "Expected an unmodified old-layout QA installation")
    installer = args.installer.resolve()
    contract = json.loads(args.build_report.read_text(encoding="utf-8"))
    require(sha(installer) == contract["installer"]["sha256"] and installer.stat().st_size == contract["installer"]["size"],
            "Installer differs from build record")
    user_before = inventory(root / "UserData")
    old_before = inventory(old_versions)
    require("settings.ini" in user_before and "memcards/preserve-qa-card.mcd" in user_before,
            "Prior QA settings/card preservation sentinels missing")
    transcript = []

    def run(exe, arguments):
        result = subprocess.run([str(exe), "--headless", *map(str, arguments)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        transcript.append({"exe": str(exe), "arguments": list(map(str, arguments)),
                           "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        require(result.returncode == 0, f"Headless operation failed: {result.stderr}")
        return result

    run(installer, ["--install", "--root", root])
    identity = (root / "installation.txt").read_text().strip()
    version = root / "v" / identity[:16]
    for item in contract["payload_files"]:
        target = version / item["path"]
        require(target.stat().st_size == item["size"] and sha(target) == item["sha256"],
                f"New installed content differs: {item['path']}")
    launcher = root / "Play Mass Driver.exe"
    require(sha(launcher) == contract["play_launcher"]["sha256"], "Updated launcher differs")
    run(launcher, ["--check-installed"])
    dry = run(launcher, ["--launch-check"])
    require("RUNTIME_LAUNCHED=false" in dry.stdout, "Dry-launch diagnostic missing")
    require(user_before == inventory(root / "UserData"), "Upgrade changed private UserData")
    require(old_before == inventory(old_versions), "Upgrade changed old version files")
    report = {"format": "mass-driver-private-layout-upgrade-qa-v1", "status": "passed",
              "installer_sha256": contract["installer"]["sha256"], "prior_qa_report": str(previous_path),
              "qa_install_root": str(root), "new_compact_version": str(version),
              "canonical_settings_and_card_sentinel_preserved": True, "all_userdata_files_unchanged": True,
              "old_versions_files_unchanged": True, "old_version_files": len(old_before),
              "new_payload_files_verified": len(contract["payload_files"]),
              "gui_or_game_runtime_launched": False, "transcript": transcript}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "transcript"}, indent=2))


if __name__ == "__main__":
    main()
