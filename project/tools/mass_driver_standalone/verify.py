"""Private installer headless QA. Never starts a GUI or the game runtime.

All mutations are confined to a fresh explicitly supplied QA directory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

def require(condition,message):
    if not condition:raise RuntimeError(message)

def sha(path):
    value=hashlib.sha256()
    with path.open("rb") as stream:
        while data:=stream.read(8<<20):value.update(data)
    return value.hexdigest()

def state(path):return path.stat().st_size,path.stat().st_mtime_ns,sha(path)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installer",type=Path,required=True)
    parser.add_argument("--build-report",type=Path,required=True)
    parser.add_argument("--payload-root",type=Path,required=True)
    parser.add_argument("--qa-root",type=Path,required=True)
    args=parser.parse_args()
    installer=args.installer.resolve();payload=args.payload_root.resolve();qa=args.qa_root.resolve()
    require(not qa.exists(),"Choose a fresh QA root; existing user installations are never used")
    contract=json.loads(args.build_report.read_text(encoding="utf-8"))
    require(installer.stat().st_size==contract["installer"]["size"] and sha(installer)==contract["installer"]["sha256"],"Installer differs from build record")
    require(qa!=installer.parent and qa not in installer.parents and payload not in qa.parents,"Unsafe QA destination")
    before=state(installer);inputs={item["path"]:state(payload/item["path"]) for item in contract["payload_files"]}
    qa.mkdir(parents=True);transcript=[]
    def run(exe,arguments,expected):
        result=subprocess.run([str(exe),"--headless",*map(str,arguments)],capture_output=True,text=True,encoding="utf-8",errors="replace")
        transcript.append({"exe":str(exe),"arguments":list(map(str,arguments)),"exit_code":result.returncode,"stdout":result.stdout,"stderr":result.stderr})
        require(result.returncode==expected,f"Expected exit{expected}, got{result.returncode}: {result.stderr}")
        return result
    run(installer,["--inspect"],0)
    for flag in ("--cancel-before","--cancel-during"):
        target=qa/flag[2:]
        run(installer,["--install","--root",target,flag],61)
        require(not list(target.glob(".install-*")) and not (target/"installation.txt").exists(),"Cancelled installation committed data/staging")
        require(not list((target/"v").iterdir()),"Cancelled installation committed a version")
    root=qa/"installed"
    run(installer,["--install","--root",root],0)
    identity=(root/"installation.txt").read_text().strip()
    require(len(identity)==64 and set(identity)<=set("0123456789abcdef"),"Invalid version identity")
    version=root/"v"/identity[:16]
    for item in contract["payload_files"]:
        target=version/item["path"]
        require(target.stat().st_size==item["size"] and sha(target)==item["sha256"],f"Extracted bytes differ: {item['path']}")
    play=root/"Play Mass Driver.exe"
    require(play.stat().st_size==contract["play_launcher"]["size"] and sha(play)==contract["play_launcher"]["sha256"],"Installed small Play launcher differs")
    require(not (version/"runtime/updater.exe").exists() and not (version/"runtime/uninstaller.exe").exists(),"Excluded runtime tools were installed")
    settings=root/"UserData/settings.ini"
    initial=settings.read_text(encoding="utf-8")
    require(str(root/"UserData/memcards").replace("\\","/") in initial,"Memory-card path is not stable private UserData")
    require(str(version/"bios").replace("\\","/") in initial and "PathNTSCU = ps-22a.bin" in initial,"Bundled BIOS path is not explicit")
    require("@DATA_DIRECTORY@" not in initial and "@BIOS_DIRECTORY@" not in initial,"Unexpanded settings token")
    require("Macro" not in initial and "TogglePause = Keyboard/Space" in initial,"Test macros or invalid default pause binding")
    settings.write_text(initial+"\n; Preserve this private user preference through repair\n[QAUserPreference]\nValue = keep\n",encoding="utf-8")
    card=root/"UserData/memcards/preserve-qa-card.mcd";card.write_bytes(b"private user save sentinel")
    user_before={settings:state(settings),card:state(card)}
    run(installer,["--install","--root",root],0)
    require(user_before=={path:state(path) for path in user_before},"Reinstall changed private settings/cards")
    run(play,["--check-installed"],0)
    dry=run(play,["--launch-check"],0)
    require("RUNTIME_LAUNCHED=false" in dry.stdout and str(version/"runtime/duckstation-qt-x64-ReleaseLTCG.exe").replace("\\","/") in dry.stdout and
            "-batch -nogui -fullscreen -fastboot --" in dry.stdout,"Dry launch plan differs")
    require(user_before=={path:state(path) for path in user_before},"Dry launch changed canonical settings/cards")
    # Damage only this owned QA game's extracted bytes, then repair all immutable content.
    game=version/"game/Xenogears_Mass_Driver.bin"
    with game.open("r+b") as stream:
        original=stream.read(1);stream.seek(0);stream.write(bytes([original[0]^1]))
    run(play,["--check-installed"],20)
    run(installer,["--install","--root",root],0)
    run(play,["--check-installed"],0)
    require(user_before=={path:state(path) for path in user_before},"Repair changed private settings/cards")
    require(list((root/"v").glob(identity[:16]+".preserved-*")),"Repair discarded the previous private version instead of preserving it")
    for item in contract["payload_files"]:
        require(sha(version/item["path"])==item["sha256"],"Repaired payload differs")
    changed=qa/"changed-installer.exe";shutil.copyfile(installer,changed)
    with changed.open("r+b") as stream:stream.seek(-1,2);byte=stream.read(1);stream.seek(-1,2);stream.write(bytes([byte[0]^1]))
    run(changed,["--inspect"],10)
    long_root=qa/("long-"+"x"*110)
    rejected=run(installer,["--install","--root",long_root],20)
    require("too long" in rejected.stderr and not long_root.exists(),"Unsafe long runtime location was not rejected before installation")
    require(before==state(installer) and inputs=={name:state(payload/name) for name in inputs},"Original installer/payload changed")
    report={"format":"mass-driver-private-installer-headless-qa-v1","status":"passed","installer_sha256":before[2],
            "payload_files":len(contract["payload_files"]),"payload_bytes":sum(item["size"] for item in contract["payload_files"]),
            "exact_extraction_verified":True,"pre_and_mid_extraction_cancellation_cleanup":True,
            "reinstall_and_repair_preserve_private_cards_and_settings":True,"damaged_payload_detected_and_repaired":True,
            "changed_installer_rejected":True,"installed_small_launcher_verified":True,"bundled_runtime_command_verified":True,
            "long_runtime_location_rejected_without_writes":True,"compact_version_path":True,
            "source_inputs_unchanged":True,"gui_or_game_runtime_launched":False,"public_redistribution_cleared":False,
            "qa_install_root":str(root),"transcript":transcript}
    (qa/"qa-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:value for key,value in report.items() if key!="transcript"},indent=2))

if __name__=="__main__":main()
