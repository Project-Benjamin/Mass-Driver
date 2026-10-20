#!/usr/bin/env python3
"""Append a streaming, pinned private payload to a native installer stub.

Windows only. Uses cabinet.dll XPRESS_HUFF in independent <=4 MiB buffer-mode
chunks, storing a chunk raw when compression would not reduce it. No game-specific
discovery occurs here: every ordinary file under --payload-root is inventoried.
An archive checksum detects corruption; it is not a publisher signature.

Wire format (little endian): 48-byte header, sorted 64-byte entry headers + ASCII
paths, chunk stream, 104-byte footer. Each chunk has four uint32 values
(raw length, stored length, codec [0 raw, 1 XPRESS_HUFF], reserved zero).
Entry offsets are relative to the archive start; directories are implicit.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import sys
import tempfile

MAGIC = b"MDARCHIVEv1\0\0\0\0\0"
FOOT_MAGIC = b"MDFOOTERv1\0\0\0\0\0\0"
HEADER = struct.Struct("<16sIIIIQQ")
ENTRY = struct.Struct("<HHIQQQ32s")
FOOTER = struct.Struct("<16sQQQ32s32s")
CHUNK = struct.Struct("<IIII")
CHUNK_SIZE = 4 * 1024 * 1024
MAX_TOTAL = 2 * 1024 * 1024 * 1024
MAX_FILES = 8192
MAX_PATH = 240
MAX_MANIFEST = 4 * 1024 * 1024
MAX_STUB = 64 * 1024 * 1024


def validate_path(path: str) -> bytes:
    try:
        encoded = path.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"Payload paths must be ASCII: {path!r}") from exc
    if not encoded or len(encoded) > MAX_PATH:
        raise ValueError(f"Invalid payload path length: {path!r}")
    for part in path.split("/"):
        if not part or part in (".", "..") or part[-1] in " .":
            raise ValueError(f"Unsafe payload path: {path!r}")
        if any(ord(c) < 32 or ord(c) > 126 or c in '<>:"\\|?*' for c in part):
            raise ValueError(f"Unsafe payload path: {path!r}")
        stem = part.split(".", 1)[0].upper()
        if stem in {"CON", "PRN", "AUX", "NUL"} or (
            len(stem) == 4 and stem[:3] in ("COM", "LPT") and stem[3] in "123456789"
        ):
            raise ValueError(f"Windows device path forbidden: {path!r}")
    return encoded


def plain_stat(path: Path, directory: bool = False):
    info = path.lstat()
    if info.st_file_attributes & 0x400 or stat.S_ISLNK(info.st_mode):
        raise ValueError(f"Reparse points and links are forbidden: {path}")
    expected = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
    if not expected:
        raise ValueError(f"Expected an ordinary {'directory' if directory else 'file'}: {path}")
    return info


def plain_ancestors(path: Path):
    for parent in path.parents:
        plain_stat(parent, True)


def inventory(root: Path):
    # Check ancestors before resolve() can hide an input junction.
    for parent in (root, *root.parents):
        plain_stat(parent, True)
    found = []
    for base, dirs, files in os.walk(root, followlinks=False):
        base_path = Path(base)
        for directory in dirs:
            child = base_path / directory
            plain_stat(child, True)
            validate_path(child.relative_to(root).as_posix())
        for name in files:
            path = base_path / name
            info = plain_stat(path)
            rel = path.relative_to(root).as_posix()
            validate_path(rel)
            found.append((rel, path, info))
    found.sort(key=lambda row: row[0])
    if not found or len(found) > MAX_FILES:
        raise ValueError(f"Payload must contain 1..{MAX_FILES} files")
    keys = {row[0].lower() for row in found}
    if len(keys) != len(found):
        raise ValueError("Payload contains case-insensitive path aliases")
    for key in keys:
        parts = key.split("/")
        if any("/".join(parts[:i]) in keys for i in range(1, len(parts))):
            raise ValueError("A payload file is also a directory prefix")
    if sum(row[2].st_size for row in found) > MAX_TOTAL:
        raise ValueError("Payload exceeds the 2 GiB limit")
    return found


def validate_stub(stub: Path, size: int):
    with stub.open("rb") as stream:
        dos = stream.read(64)
        if len(dos) != 64 or dos[:2] != b"MZ":
            raise ValueError("Stub is not a Windows PE executable")
        pe = struct.unpack_from("<I", dos, 60)[0]
        if not 64 <= pe <= 1024 * 1024 or pe + 24 > size:
            raise ValueError("Stub PE header offset is invalid")
        stream.seek(pe)
        coff = stream.read(24)
        if coff[:4] != b"PE\0\0":
            raise ValueError("Stub PE signature is invalid")
        optional_size = struct.unpack_from("<H", coff, 20)[0]
        if not 2 <= optional_size <= 4096 or pe + 24 + optional_size > size:
            raise ValueError("Stub PE optional header is invalid")
        optional = stream.read(optional_size)
        magic = struct.unpack_from("<H", optional)[0]
        directories = 112 if magic == 0x20B else 96 if magic == 0x10B else 0
        if not directories or len(optional) < directories:
            raise ValueError("Stub PE optional header type is unsupported")
        if struct.unpack_from("<I", optional, directories - 4)[0] > 4:
            if len(optional) < directories + 40:
                raise ValueError("Stub PE security directory is truncated")
            if any(struct.unpack_from("<II", optional, directories + 32)):
                raise ValueError("Stub must be unsigned; sign the completed installer after packing")
        if size >= FOOTER.size:
            stream.seek(-FOOTER.size, os.SEEK_END)
            if stream.read(16) == FOOT_MAGIC:
                raise ValueError("Stub already contains an appended archive")


class Compressor:
    def __init__(self):
        self.dll = ctypes.WinDLL("cabinet.dll", use_last_error=True)
        self.dll.CreateCompressor.argtypes = [wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
        self.dll.CreateCompressor.restype = wintypes.BOOL
        self.dll.Compress.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
                                     ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        self.dll.Compress.restype = wintypes.BOOL
        self.dll.CloseCompressor.argtypes = [ctypes.c_void_p]
        self.dll.CloseCompressor.restype = wintypes.BOOL
        self.handle = ctypes.c_void_p()
        if not self.dll.CreateCompressor(4, None, ctypes.byref(self.handle)):
            raise ctypes.WinError(ctypes.get_last_error())

    def compress(self, raw: bytes) -> bytes:
        src = ctypes.create_string_buffer(raw)
        needed = ctypes.c_size_t()
        ok = self.dll.Compress(self.handle, src, len(raw), None, 0, ctypes.byref(needed))
        if not ok and ctypes.get_last_error() != 122:  # ERROR_INSUFFICIENT_BUFFER
            raise ctypes.WinError(ctypes.get_last_error())
        # The sizing query may return a conservative upper bound rather than
        # the final compressed length. Always compress before choosing raw.
        if not needed.value or needed.value > 2 * CHUNK_SIZE:
            raise ValueError("Compression API returned an invalid buffer size")
        dst = ctypes.create_string_buffer(needed.value)
        actual = ctypes.c_size_t()
        if not self.dll.Compress(self.handle, src, len(raw), dst, len(dst), ctypes.byref(actual)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not actual.value or actual.value > len(dst):
            raise ValueError("Compression API returned an invalid chunk size")
        return dst.raw[:actual.value] if actual.value < len(raw) else raw

    def close(self):
        if self.handle:
            self.dll.CloseCompressor(self.handle)
            self.handle = ctypes.c_void_p()


def stat_key(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def digest_file(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def pack(args):
    if os.name != "nt":
        raise ValueError("This packer requires Windows cabinet.dll")
    root = Path(os.path.abspath(args.payload_root))
    stub = Path(os.path.abspath(args.stub))
    output = Path(os.path.abspath(args.output))
    report_path = Path(os.path.abspath(args.report))
    if output == report_path or output.exists() or report_path.exists():
        raise ValueError("Output and report must be distinct new files")
    if output.is_relative_to(root) or report_path.is_relative_to(root):
        raise ValueError("Output and report must be outside the payload root")
    if not output.parent.is_dir() or not report_path.parent.is_dir():
        raise ValueError("Output and report parent directories must already exist")
    stub_info = plain_stat(stub)
    plain_ancestors(stub)
    if not 64 <= stub_info.st_size <= MAX_STUB:
        raise ValueError("Stub must be 64 bytes..64 MiB")
    validate_stub(stub, stub_info.st_size)
    files = inventory(root)
    compressor = Compressor()
    records = []
    raw_count = compressed_count = 0
    output_created = report_created = False
    try:
        with tempfile.TemporaryFile(dir=output.parent) as data:
            for rel, path, before in files:
                start = data.tell()
                digest = hashlib.sha256()
                size = chunks = 0
                with path.open("rb") as source:
                    while raw := source.read(CHUNK_SIZE):
                        digest.update(raw)
                        size += len(raw)
                        if size > before.st_size:
                            raise ValueError(f"Payload file changed while reading: {rel}")
                        encoded = compressor.compress(raw)
                        codec = int(len(encoded) < len(raw))
                        data.write(CHUNK.pack(len(raw), len(encoded), codec, 0))
                        data.write(encoded)
                        chunks += 1
                        compressed_count += codec
                        raw_count += 1 - codec
                if size != before.st_size or stat_key(plain_stat(path)) != stat_key(before):
                    raise ValueError(f"Payload file changed while reading: {rel}")
                records.append(dict(path=rel, size=size, sha256=digest.hexdigest(),
                                    chunks=chunks, offset=start, length=data.tell()-start))
            again = inventory(root)
            if [(r, stat_key(s)) for r, _, s in files] != [(r, stat_key(s)) for r, _, s in again]:
                raise ValueError("Payload inventory changed while packing")
            manifest_length = HEADER.size + sum(ENTRY.size + len(r["path"]) for r in records)
            if manifest_length > MAX_MANIFEST:
                raise ValueError("Manifest exceeds limit")
            total = sum(r["size"] for r in records)
            manifest = bytearray(HEADER.pack(MAGIC, 1, CHUNK_SIZE, len(records), 0, total, manifest_length))
            for rec in records:
                name = rec["path"].encode("ascii")
                manifest += ENTRY.pack(len(name), 0, rec["chunks"], rec["size"],
                                       manifest_length + rec["offset"], rec["length"], bytes.fromhex(rec["sha256"]))
                manifest += name
            archive_digest = hashlib.sha256(manifest)
            full_digest = hashlib.sha256()
            stub_digest = hashlib.sha256()
            archive_length = manifest_length + data.tell()
            with output.open("xb") as target:
                output_created = True
                with stub.open("rb") as source:
                    while chunk := source.read(CHUNK_SIZE):
                        target.write(chunk)
                        full_digest.update(chunk)
                        stub_digest.update(chunk)
                if stat_key(plain_stat(stub)) != stat_key(stub_info):
                    raise ValueError("Stub changed while packing")
                target.write(manifest)
                full_digest.update(manifest)
                data.seek(0)
                while chunk := data.read(CHUNK_SIZE):
                    target.write(chunk)
                    full_digest.update(chunk)
                    archive_digest.update(chunk)
                footer = FOOTER.pack(FOOT_MAGIC, stub_info.st_size, archive_length, manifest_length,
                                     archive_digest.digest(), hashlib.sha256(manifest).digest())
                target.write(footer)
                full_digest.update(footer)
                target.flush()
                os.fsync(target.fileno())
            report = dict(format="mass-driver-private-archive-v1", output=str(output),
                          output_size=output.stat().st_size, output_sha256=full_digest.hexdigest(),
                          stub_sha256=stub_digest.hexdigest(), archive_sha256=archive_digest.hexdigest(),
                          manifest_sha256=hashlib.sha256(manifest).hexdigest(), archive_offset=stub_info.st_size,
                          archive_length=archive_length, manifest_length=manifest_length,
                          total_uncompressed_size=total, file_count=len(records), chunk_size=CHUNK_SIZE,
                          compressed_chunks=compressed_count, raw_chunks=raw_count,
                          checksum_is_publisher_signature=False, files=records)
            # Re-read the finished installer before recording success.
            if digest_file(output) != report["output_sha256"]:
                raise ValueError("Finished installer hash verification failed")
            with report_path.open("x", encoding="utf-8", newline="\n") as stream:
                report_created = True
                json.dump(report, stream, indent=2)
                stream.write("\n")
            return report
    except BaseException:
        # Only files created by this invocation can be removed here.
        if output_created:
            output.unlink(missing_ok=True)
        if report_created:
            report_path.unlink(missing_ok=True)
        raise
    finally:
        compressor.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stub", required=True)
    parser.add_argument("--payload-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    try:
        report = pack(args)
    except (OSError, ValueError) as exc:
        print(f"Packing failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({key: report[key] for key in ("output", "output_sha256", "archive_sha256", "file_count", "total_uncompressed_size")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
