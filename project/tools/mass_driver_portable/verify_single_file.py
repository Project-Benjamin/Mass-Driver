"""Verify a data-embedded patcher without opening a GUI or launching an emulator."""
from __future__ import annotations
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while data := stream.read(8 << 20):
            value.update(data)
    return value.hexdigest()


def resource(path):
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.LoadLibraryExW.argtypes = [wintypes.LPCWSTR, wintypes.HANDLE, wintypes.DWORD]
    api.LoadLibraryExW.restype = wintypes.HMODULE
    api.FindResourceW.argtypes = [wintypes.HMODULE, ctypes.c_void_p, ctypes.c_void_p]
    api.FindResourceW.restype = ctypes.c_void_p
    api.LoadResource.argtypes = [wintypes.HMODULE, ctypes.c_void_p]
    api.LoadResource.restype = ctypes.c_void_p
    api.SizeofResource.argtypes = [wintypes.HMODULE, ctypes.c_void_p]
    api.SizeofResource.restype = wintypes.DWORD
    api.LockResource.argtypes = [ctypes.c_void_p]
    api.LockResource.restype = ctypes.c_void_p
    api.FreeLibrary.argtypes = [wintypes.HMODULE]
    module = api.LoadLibraryExW(str(path), None, 0x22)  # data/image resource only; no code is run
    require(module, "Cannot open EXE resources")
    try:
        found = api.FindResourceW(module, ctypes.c_void_p(400), ctypes.c_void_p(10))
        require(found, "Embedded data resource is missing")
        size = api.SizeofResource(module, found)
        memory = api.LockResource(api.LoadResource(module, found))
        require(size and memory, "Embedded data resource is unreadable")
        return ctypes.string_at(memory, size)
    finally:
        api.FreeLibrary(module)


def entries(blob):
    require(blob[:8] == b"XGMDATA1", "Wrong embedded data format")
    count, = struct.unpack_from("<I", blob, 8)
    require(5 <= count <= 32, "Wrong embedded inventory size")
    offset, files = 12, {}
    for _ in range(count):
        length, size = struct.unpack_from("<HQ", blob, offset)
        offset += 10
        expected = blob[offset:offset + 32]
        offset += 32
        name = blob[offset:offset + length].decode("ascii")
        offset += length
        data = blob[offset:offset + size]
        offset += size
        require(len(data) == size and hashlib.sha256(data).digest() == expected, "Embedded entry hash failed")
        require(name.startswith("MassDriverData/") and ".." not in name and "\\" not in name and
                Path(name).suffix in {".md", ".txt", ".template", ".xdelta"}, "Unsafe embedded entry")
        require(name not in files, "Duplicate embedded entry")
        files[name] = data
    require(offset == len(blob), "Trailing embedded bytes")
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--build-manifest", type=Path, required=True)
    parser.add_argument("--source-bin", type=Path)
    parser.add_argument("--qa-parent", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    exe = args.exe.resolve()
    manifest = json.loads(args.build_manifest.read_text(encoding="utf-8"))
    before = (exe.stat().st_size, exe.stat().st_mtime_ns, sha(exe))
    binary = exe.read_bytes()
    for marker in (str(Path(__file__).resolve().parents[2]), str(Path.home()), "\\work\\", "\\Users\\"):
        require(marker.encode("utf-8") not in binary and marker.encode("utf-16le") not in binary,
                "Private build path is present in the EXE")
    pe, = struct.unpack_from("<I", binary, 0x3c)
    optional = pe + 24
    magic, = struct.unpack_from("<H", binary, optional)
    security = optional + (112 if magic == 0x20b else 96) + 4 * 8
    certificate_offset, certificate_size = struct.unpack_from("<II", binary, security)
    blob = resource(exe)
    files = entries(blob)
    runtime = "\n".join([
        "format=xenogears-mass-driver-patch-v1",
        f"source_size={manifest['source']['size']}", f"source_sha256={manifest['source']['sha256']}",
        f"patch_size={manifest['patch']['size']}", f"patch_sha256={manifest['patch']['sha256']}",
        f"cue_size={manifest['cue_template']['size']}", f"cue_sha256={manifest['cue_template']['sha256']}",
        f"output_size={manifest['output']['bin_size']}", f"output_sha256={manifest['output']['bin_sha256']}", "",
    ]).encode()
    require(files["MassDriverData/patch_manifest.txt"] == runtime, "Embedded runtime manifest differs")
    for spec in (manifest["patch"], manifest["cue_template"],
                 manifest.get("compiler_runtime_license"), *manifest.get("compiler_runtime_notices", [])):
        if spec:
            data = files[spec["relative_path"]]
            require(len(data) == spec["size"] and hashlib.sha256(data).hexdigest() == spec["sha256"], "Embedded pinned file differs")
    transcript = []
    def run(arguments, expected):
        result = subprocess.run([str(exe), "--headless", *map(str, arguments)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        transcript.append({"arguments": list(map(str, arguments)), "exit_code": result.returncode,
                           "stdout": result.stdout, "stderr": result.stderr})
        require(result.returncode == expected, f"Unexpected app result: {result.returncode}: {result.stderr}")
        return result
    check = run(["--check-package"], 0)
    line = next((value for value in check.stdout.splitlines() if value.startswith("EMBEDDED_DATA_ROOT=")), None)
    require(line, "Embedded cache location was not reported")
    cache = Path(line.partition("=")[2]).resolve()
    require(cache.name == hashlib.sha256(blob).hexdigest() and cache.parent.name == "PatcherData" and
            cache.parent.parent.name == "Xenogears Mass Driver", "Unexpected hash cache location")
    cached = {p.relative_to(cache).as_posix(): p for p in cache.rglob("*") if p.is_file()}
    require(set(cached) == set(files), "Cache inventory differs from embedded data")
    require(not any(p.is_symlink() or p.is_junction() for p in cache.rglob("*")), "Cache has linked entries")
    state = {name: (path.stat().st_mtime_ns, sha(path)) for name, path in cached.items()}
    for name, path in cached.items():
        require(path.read_bytes() == files[name], "Extracted resource differs")
    run(["--check-package"], 0)
    require(state == {name: (path.stat().st_mtime_ns, sha(path)) for name, path in cached.items()}, "Cache reuse rewrote data")
    # Only our exact embedded patch path is temporarily changed; its original bytes and mtime are restored.
    patch_name = manifest["patch"]["relative_path"]
    patch_path = cached[patch_name]
    saved_stat = patch_path.stat()
    try:
        changed = bytearray(files[patch_name]); changed[-1] ^= 1
        patch_path.write_bytes(changed)
        require("PACKAGE_ERROR=21:" in run(["--check-package"], 21).stderr, "Changed cache was not rejected")
    finally:
        patch_path.write_bytes(files[patch_name])
        os.utime(patch_path, ns=(saved_stat.st_atime_ns, saved_stat.st_mtime_ns))
    run(["--check-package"], 0)
    dynamic = False
    if args.source_bin:
        source = args.source_bin.resolve()
        source_state = (source.stat().st_size, source.stat().st_mtime_ns, sha(source))
        require(source_state[0] == manifest["source"]["size"] and source_state[2] == manifest["source"]["sha256"], "QA source differs from build contract")
        parent = args.qa_parent.resolve() if args.qa_parent else Path(tempfile.gettempdir())
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="MassDriverSingleQA-", dir=parent) as temporary:
            root = Path(temporary).resolve()
            require(root.parent == parent, "QA staging escaped its parent")
            output = root / "game output"
            command = ["--source", source, "--output", output]
            run([*command, "--cancel-before-decode"], 61)
            require(not output.exists() and not list(root.glob(".MassDriverBuild.*")), "Cancellation left output/staging")
            run(command, 0)
            target = output / manifest["output"]["bin_name"]
            cue = output / manifest["output"]["cue_name"]
            require(target.stat().st_size == manifest["output"]["bin_size"] and sha(target) == manifest["output"]["bin_sha256"], "Integrated reconstruction differs")
            require(cue.stat().st_size == manifest["output"]["cue_size"] and sha(cue) == manifest["output"]["cue_sha256"], "Generated CUE differs")
            target_state = (target.stat().st_mtime_ns, sha(target), cue.stat().st_mtime_ns, sha(cue))
            sentinel = output / "preserve-user-file.txt"; sentinel.write_text("preserve")
            require("already ready" in run(command, 0).stdout, "Existing exact output was not reused")
            require(target_state == (target.stat().st_mtime_ns, sha(target), cue.stat().st_mtime_ns, sha(cue)) and
                    sentinel.read_text() == "preserve", "Existing output/user file changed")
            wrong = root / "wrong.bin"; wrong.write_bytes(b"wrong")
            run(["--source", wrong, "--output", output], 11)
            with wrong.open("wb") as stream: stream.truncate(manifest["source"]["size"])
            run(["--source", wrong, "--output", output], 12)
            require(target_state == (target.stat().st_mtime_ns, sha(target), cue.stat().st_mtime_ns, sha(cue)), "Wrong source changed valid output")
            require("EMULATOR_REQUIRED" in run(["--play-check", "--game", output, "--no-emulator"], 4).stdout, "Missing emulator diagnostic differs")
        require(source_state == (source.stat().st_size, source.stat().st_mtime_ns, sha(source)), "Source BIN changed")
        dynamic = True
    require(before == (exe.stat().st_size, exe.stat().st_mtime_ns, sha(exe)), "Downloaded EXE changed")
    report = {"status": "passed", "exe_size": before[0], "exe_sha256": before[2],
              "embedded_files": len(files), "embedded_bundle_sha256": hashlib.sha256(blob).hexdigest(),
              "cache_verified": True, "cache_reuse_unchanged": True, "cache_tamper_rejected_and_restored": True,
              "no_extracted_executables": True, "dynamic_clean_source_reconstruction": dynamic,
              "native_gui_acceptance": "Not exercised", "emulator_launched": False, "transcript": transcript}
    report["pe_certificate_present"] = bool(certificate_offset or certificate_size)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "transcript"}, indent=2))


if __name__ == "__main__":
    main()
