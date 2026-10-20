"""Build a separate private native installer/Play launcher from a prepared payload.

The resulting EXE is for private noncommercial local use. Nothing is published.
Build-time Python and the compiler are not installed or bundled.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8 << 20): value.update(block)
    return value.hexdigest()

def run(args, log):
    result = subprocess.run(list(map(str,args)), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            encoding="utf-8", errors="replace")
    with log.open("a",encoding="utf-8") as target: target.write(result.stdout)
    if result.returncode: raise RuntimeError(f"Native build command failed: {result.stdout[-2500:]}")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload-root",type=Path,required=True)
    parser.add_argument("--compiler",type=Path,required=True)
    parser.add_argument("--output-root",type=Path,required=True)
    parser.add_argument("--public",dest="public_build",action="store_true",
                        help="Build the GPL emulator/patch player; never include a game, BIOS or Microsoft DLL")
    args=parser.parse_args()
    payload=args.payload_root.resolve();compiler=args.compiler.resolve();output=args.output_root.resolve()
    if output.exists(): raise RuntimeError("Choose a fresh private build output directory")
    files=[]
    for path in payload.rglob("*"):
        if path.is_symlink() or path.is_junction(): raise RuntimeError("Payload cannot contain linked files")
        if path.is_file(): files.append({"path":path.relative_to(payload).as_posix(),"size":path.stat().st_size,"sha256":sha(path)})
    files.sort(key=lambda item:item["path"].encode("ascii"))
    logical="XGMDCONTENT1\n"+"".join(f"{item['size']}\t{item['sha256']}\t{item['path']}\n" for item in files)
    logical_sha=hashlib.sha256(logical.encode("ascii")).hexdigest()
    required=("runtime/duckstation-qt-x64-ReleaseLTCG.exe","runtime/portable.txt","defaults/settings.ini.template")
    if args.public_build:
        required+=("player-release.json","patcher/Xenogears_Mass_Driver.exe","README_PLAYER.md")
        if (payload/"game").exists() or (payload/"bios").exists():raise RuntimeError("Public payload contains private game/BIOS")
        if any(re.fullmatch(r"(?:msvcp140|vcruntime140|concrt140|vcomp140).*\.dll",p.name,re.I) for p in payload.rglob("*")):
            raise RuntimeError("Public payload contains Microsoft runtime binaries")
        release=json.loads((payload/"player-release.json").read_text(encoding="utf-8"))
        if release["format"]!="mass-driver-public-player-release-v1" or release["runtime"]["license"]!="GPL-3.0":raise RuntimeError("Unreviewed public player release")
        for item,key in ((release["source"],"sha256"),(release["game"],"bin_sha256"),(release["game"],"cue_sha256")):
            if not re.fullmatch("[0-9a-f]{64}",item[key]):raise RuntimeError("Invalid public content identity")
        if not all(re.fullmatch("[0-9a-f]{32}",x) for x in release["bios"]["ntsc_u_md5s"]):raise RuntimeError("Invalid BIOS identity")
        if not all(re.fullmatch(r"(?:msvcp140|vcruntime140|concrt140|vcomp140)[a-z0-9_]*\.dll",x) for x in release["required_system_vc_dlls"]):raise RuntimeError("Invalid VC dependency name")
    else:
        required+=("game/Xenogears_Mass_Driver.bin","game/Xenogears_Mass_Driver.cue","bios/ps-22a.bin")
    for name in required:
        if not (payload/name).is_file():raise RuntimeError(f"Missing required payload input: {name}")
    output.mkdir(parents=True);native=output/"native-build";native.mkdir();log=output/"native-build.log"
    (native/"content_manifest.txt").write_bytes(logical.encode("ascii"))
    header=native/"private_config.h"
    header.write_text(f'#pragma once\n#define PRIVATE_CONTENT_SHA256 "{logical_sha}"\n',encoding="ascii")
    if args.public_build:
        source,game=release["source"],release["game"]
        with header.open("a",encoding="ascii") as target:
            target.write(f'#define PUBLIC_SOURCE_SIZE {int(source["size"])}ULL\n#define PUBLIC_SOURCE_SHA256 "{source["sha256"]}"\n')
            target.write(f'#define PUBLIC_GAME_SIZE {int(game["bin_size"])}ULL\n#define PUBLIC_GAME_SHA256 "{game["bin_sha256"]}"\n')
            target.write(f'#define PUBLIC_CUE_SIZE {int(game["cue_size"])}ULL\n#define PUBLIC_CUE_SHA256 "{game["cue_sha256"]}"\n')
            target.write('static constexpr const char* PUBLIC_BIOS_MD5S[] = {'+','.join('"'+x+'"' for x in release["bios"]["ntsc_u_md5s"])+'};\n')
            target.write('static constexpr const wchar_t* PUBLIC_REQUIRED_VC_DLLS[] = {'+','.join('L"'+x+'"' for x in release["required_system_vc_dlls"])+'};\n')
    shutil.copyfile(HERE/"app.manifest",native/"app.manifest")
    clang=compiler/"bin/x86_64-w64-mingw32-clang++.exe"
    windres=compiler/"bin/x86_64-w64-mingw32-windres.exe"
    flags=["-std=c++17","-O2","-g0","-DNDEBUG","-DUNICODE","-D_UNICODE","-DWIN32_LEAN_AND_MEAN","-DNOMINMAX",
           "-DWINVER=0x0A00","-D_WIN32_WINNT=0x0A00",f"-I{HERE}",f"-I{native}",
           f"-ffile-prefix-map={ROOT}=.",f"-ffile-prefix-map={output}=private-build"]
    if args.public_build:flags.append("-DPUBLIC_PLAYER=1")
    libs=["-luser32","-lgdi32","-lshell32","-lole32","-luuid","-lbcrypt","-lcabinet","-lcomctl32"]
    if args.public_build:libs.extend(["-lwinhttp","-lwintrust","-lcrypt32"])
    link=["-static","-municode","-mwindows","-Wl,--dynamicbase,--high-entropy-va,--nxcompat,--no-insert-timestamp"]
    archive_obj=native/"archive.obj";run([clang,*flags,"-c",HERE/"archive.cpp","-o",archive_obj],log)
    play=native/"Play Mass Driver.exe"
    for kind in ("play","installer"):
        resource=native/f"{kind}.rc";resource_object=native/f"{kind}.res"
        text=f'1 24 "{(native/"app.manifest").as_posix()}"\n'
        description=("Mass Driver Play" if kind=="play" else "Mass Driver setup") if args.public_build else ("Mass Driver private Play" if kind=="play" else "Mass Driver private setup")
        version="1,7,6,0" if args.public_build else "1,7,4,0"
        version_text="1.7.6.0" if args.public_build else "1.7.4.0"
        product_version="V176 release candidate" if args.public_build else "V174 private release candidate"
        text+=f'''1 VERSIONINFO
FILEVERSION {version}
PRODUCTVERSION {version}
FILEFLAGSMASK 0x3fL
FILEFLAGS 0x0L
FILEOS 0x40004L
FILETYPE 0x1L
FILESUBTYPE 0x0L
BEGIN
  BLOCK "StringFileInfo"
  BEGIN
    BLOCK "040904b0"
    BEGIN
      VALUE "FileDescription", "{description}\\0"
      VALUE "FileVersion", "{version_text}\\0"
      VALUE "ProductName", "Mass Driver\\0"
      VALUE "ProductVersion", "{product_version}\\0"
    END
  END
  BLOCK "VarFileInfo"
  BEGIN
    VALUE "Translation", 0x409, 1200
  END
END
'''
        if kind=="installer":text+=f'201 RCDATA "{play.as_posix()}"\n'
        resource.write_text(text,encoding="utf-8")
        run([windres,"-O","coff","-i",resource,"-o",resource_object],log)
        obj=native/f"{kind}.obj"
        run([clang,*flags,*( ["-DPRIVATE_PLAY_LAUNCHER=1"] if kind=="play" else []),"-c",HERE/"main.cpp","-o",obj],log)
        exe=play if kind=="play" else native/"installer-stub.exe"
        run([clang,*link,obj,archive_obj,resource_object,*libs,"-o",exe],log)
        if kind=="play":
            with header.open("a",encoding="ascii") as target:
                target.write(f'#define PRIVATE_PLAY_SIZE {play.stat().st_size}UL\n#define PRIVATE_PLAY_SHA256 "{sha(play)}"\n')
    installer=output/("Mass_Driver_Setup.exe" if args.public_build else "Mass_Driver_Private_V174_Setup.exe")
    run([sys.executable,HERE/"pack_payload.py","--stub",native/"installer-stub.exe","--payload-root",payload,
         "--output",installer,"--report",output/"archive-build.json"],log)
    report={"format":"mass-driver-public-player-build-v1" if args.public_build else "mass-driver-private-standalone-build-v1",
            "scope":"Public player candidate; no game/BIOS/Microsoft runtime included; not published" if args.public_build else "Private noncommercial local use only; not published",
            "installer":{"path":installer.name,"size":installer.stat().st_size,"sha256":sha(installer)},
            "play_launcher":{"size":play.stat().st_size,"sha256":sha(play)},
            "logical_manifest_sha256":logical_sha,"payload_files":files,"code_signed":False,
            "python_or_compiler_bundled":False,"gameplay_acceptance":"Not established by building an installer"}
    (output/("public-build.json" if args.public_build else "private-build.json")).write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:value for key,value in report.items() if key!="payload_files"},indent=2))

if __name__=="__main__":main()
