#!/usr/bin/env python3
"""Retarget one DuckStation state to a rebuilt Xenogears disc safely.

DuckStation stores the mounted media path in its uncompressed header and the
game's resident 0x8000-byte archive table inside its final zstd payload. A
media-path-only edit is unsafe whenever rebuilt files change FAT sizes or
sectors. This tool validates and replaces both pieces, then updates the
header's compressed-data size after recompression, while leaving gameplay
state, RAM outside the table, thumbnail data, and the source file untouched.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
from pathlib import Path
import struct
import sys
from typing import Sequence

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from tools.xgdisc import INDEX_SECTOR, INDEX_SECTORS, USER_DATA_SIZE, Mode2Image


ZSTD_MAGIC = bytes.fromhex("28 B5 2F FD")
ZSTD_CONTENTSIZE_ERROR = 0xFFFFFFFFFFFFFFFF
ZSTD_CONTENTSIZE_UNKNOWN = 0xFFFFFFFFFFFFFFFE

DUCKSTATION_STATE_MAGIC = b"DUCC"
DUCKSTATION_STATE_HEADER_SIZE = 0xD8
DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET = 0xC8
DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET = 0xCC
DUCKSTATION_DATA_UNCOMPRESSED_SIZE_OFFSET = 0xD0
DUCKSTATION_DATA_OFFSET_OFFSET = 0xD4
DUCKSTATION_ZSTD_COMPRESSION_TYPE = 2


class StateMigrationError(RuntimeError):
    """Raised before writing when a state or disc does not match the contract."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class _Zstd:
    def __init__(self, library: Path):
        if not library.is_file():
            raise StateMigrationError(f"zstd library does not exist: {library}")
        try:
            loader = ctypes.WinDLL if sys.platform == "win32" else ctypes.CDLL
            self.library = loader(str(library.resolve()))
        except OSError as exc:
            raise StateMigrationError(
                f"Cannot load zstd library {library}: {exc}"
            ) from exc

        self.library.ZSTD_getFrameContentSize.argtypes = [
            ctypes.c_void_p,
            ctypes.c_size_t,
        ]
        self.library.ZSTD_getFrameContentSize.restype = ctypes.c_ulonglong
        self.library.ZSTD_findFrameCompressedSize.argtypes = [
            ctypes.c_void_p,
            ctypes.c_size_t,
        ]
        self.library.ZSTD_findFrameCompressedSize.restype = ctypes.c_size_t
        self.library.ZSTD_decompress.argtypes = [
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_void_p,
            ctypes.c_size_t,
        ]
        self.library.ZSTD_decompress.restype = ctypes.c_size_t
        self.library.ZSTD_compressBound.argtypes = [ctypes.c_size_t]
        self.library.ZSTD_compressBound.restype = ctypes.c_size_t
        self.library.ZSTD_compress.argtypes = [
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_int,
        ]
        self.library.ZSTD_compress.restype = ctypes.c_size_t
        self.library.ZSTD_isError.argtypes = [ctypes.c_size_t]
        self.library.ZSTD_isError.restype = ctypes.c_uint
        self.library.ZSTD_getErrorName.argtypes = [ctypes.c_size_t]
        self.library.ZSTD_getErrorName.restype = ctypes.c_char_p

    def _checked_size(self, result: int, operation: str) -> int:
        if self.library.ZSTD_isError(result):
            name = self.library.ZSTD_getErrorName(result).decode(
                "ascii", errors="replace"
            )
            raise StateMigrationError(f"zstd {operation} failed: {name}")
        return result

    def frame_size(self, frame_and_tail: bytes) -> int:
        source = ctypes.create_string_buffer(frame_and_tail)
        return self._checked_size(
            self.library.ZSTD_findFrameCompressedSize(
                source,
                len(frame_and_tail),
            ),
            "frame-size query",
        )

    def decompress(self, frame: bytes) -> bytes:
        source = ctypes.create_string_buffer(frame)
        size = self.library.ZSTD_getFrameContentSize(source, len(frame))
        if size in (ZSTD_CONTENTSIZE_ERROR, ZSTD_CONTENTSIZE_UNKNOWN):
            raise StateMigrationError(
                "DuckStation zstd frame has no declared content size"
            )
        destination = ctypes.create_string_buffer(size)
        written = self._checked_size(
            self.library.ZSTD_decompress(
                destination,
                size,
                source,
                len(frame),
            ),
            "decompression",
        )
        if written != size:
            raise StateMigrationError(
                f"zstd decompressed {written} bytes, expected {size}"
            )
        return destination.raw[:written]

    def compress(self, payload: bytes, level: int = 3) -> bytes:
        source = ctypes.create_string_buffer(payload)
        capacity = self.library.ZSTD_compressBound(len(payload))
        destination = ctypes.create_string_buffer(capacity)
        written = self._checked_size(
            self.library.ZSTD_compress(
                destination,
                capacity,
                source,
                len(payload),
                level,
            ),
            "compression",
        )
        result = destination.raw[:written]
        if self.decompress(result) != payload:
            raise StateMigrationError("Recompressed zstd payload did not round-trip")
        return result


def _archive_table(image_path: Path) -> bytes:
    image = Mode2Image(image_path)
    return image.read_user_data(
        INDEX_SECTOR,
        INDEX_SECTORS * USER_DATA_SIZE,
    )


def _find_resident_archive_table(payload: bytes, table: bytes) -> tuple[int, int]:
    """Locate the resident table, tolerating its volatile final padding byte.

    Xenogears occasionally reuses the final byte of the 0x8000-byte RAM buffer
    after loading the archive index.  The complete table therefore does not
    always survive in a live DuckStation state even though its first 0x7fff
    bytes still identify the mounted disc uniquely.  Only that final byte may
    differ; broader drift remains an error.
    """

    exact_count = payload.count(table)
    if exact_count == 1:
        return payload.find(table), 0
    if exact_count > 1:
        raise StateMigrationError(
            "Decompressed state contains more than one old resident archive table"
        )

    stable_prefix = table[:-1]
    prefix_count = payload.count(stable_prefix)
    if prefix_count != 1:
        raise StateMigrationError(
            "Decompressed state does not contain exactly one old resident archive table"
        )
    table_offset = payload.find(stable_prefix)
    return table_offset, int(payload[table_offset + len(table) - 1] != table[-1])


def migrate_state(
    state: bytes,
    *,
    old_disc: Path,
    new_disc: Path,
    old_cue_name: str,
    new_cue_name: str,
    zstd: _Zstd,
) -> tuple[bytes, dict[str, object]]:
    old_name = old_cue_name.encode("ascii")
    new_name = new_cue_name.encode("ascii")
    if len(old_name) != len(new_name):
        raise StateMigrationError(
            "Old and new CUE names must have identical encoded lengths"
        )
    if state.count(old_name) != 1:
        raise StateMigrationError(
            f"State contains the old CUE name {state.count(old_name)} times, expected 1"
        )
    if new_name != old_name and new_name in state:
        raise StateMigrationError("State already contains the requested new CUE name")

    if (
        len(state) < DUCKSTATION_STATE_HEADER_SIZE
        or state[:4] != DUCKSTATION_STATE_MAGIC
    ):
        raise StateMigrationError(
            "Input is not a supported DuckStation save state"
        )

    (
        compression_type,
        declared_frame_size,
        declared_payload_size,
        frame_start,
    ) = struct.unpack_from(
        "<IIII",
        state,
        DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    )
    if compression_type != DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise StateMigrationError(
            "DuckStation state payload is not Zstandard-compressed"
        )
    if not DUCKSTATION_STATE_HEADER_SIZE <= frame_start < len(state):
        raise StateMigrationError(
            "DuckStation state data offset is outside the file"
        )
    frame_end = frame_start + declared_frame_size
    if frame_end > len(state):
        raise StateMigrationError(
            "DuckStation state header declares compressed data past EOF"
        )
    if frame_end != len(state):
        raise StateMigrationError(
            "DuckStation state carries unsupported trailing data"
        )
    frame = state[frame_start:frame_end]
    if not frame.startswith(ZSTD_MAGIC):
        raise StateMigrationError(
            "DuckStation state data is not a Zstandard frame"
        )
    frame_size = zstd.frame_size(frame)
    if frame_size != declared_frame_size:
        raise StateMigrationError(
            "DuckStation state header compressed size does not match its "
            f"Zstandard frame: {declared_frame_size} != {frame_size}"
        )
    payload = zstd.decompress(frame)
    if len(payload) != declared_payload_size:
        raise StateMigrationError(
            "DuckStation state header uncompressed size does not match its "
            f"payload: {declared_payload_size} != {len(payload)}"
        )

    old_table = _archive_table(old_disc)
    new_table = _archive_table(new_disc)
    if len(old_table) != 0x8000 or len(new_table) != 0x8000:
        raise StateMigrationError("Xenogears archive table is not exactly 0x8000 bytes")
    table_offset, volatile_table_bytes = _find_resident_archive_table(
        payload,
        old_table,
    )
    patched_payload = (
        payload[:table_offset]
        + new_table
        + payload[table_offset + len(old_table) :]
    )
    if (
        patched_payload[:table_offset] != payload[:table_offset]
        or patched_payload[table_offset + len(new_table) :]
        != payload[table_offset + len(old_table) :]
    ):
        raise StateMigrationError("Payload changed outside the resident archive table")

    patched_prefix = bytearray(
        state[:frame_start].replace(old_name, new_name)
    )
    if len(patched_prefix) != frame_start:
        raise StateMigrationError("Media-path replacement changed state-header size")
    compressed = zstd.compress(patched_payload)
    if len(compressed) > 0xFFFFFFFF:
        raise StateMigrationError(
            "Recompressed DuckStation payload exceeds its 32-bit header field"
        )
    # DuckStation validates offset_to_data + data_compressed_size against EOF
    # before it attempts decompression. Recompression changes the frame size,
    # so retaining the source header value makes an otherwise valid migration
    # abort silently in batch mode.
    struct.pack_into(
        "<I",
        patched_prefix,
        DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        len(compressed),
    )
    result = bytes(patched_prefix) + compressed
    if frame_start + len(compressed) != len(result):
        raise StateMigrationError(
            "Migrated DuckStation state has an inconsistent data span"
        )
    report: dict[str, object] = {
        "source_sha256": _sha256(state),
        "output_sha256": _sha256(result),
        "source_size": len(state),
        "output_size": len(result),
        "payload_size": len(payload),
        "payload_frame_offset": frame_start,
        "source_payload_compressed_size": declared_frame_size,
        "output_payload_compressed_size": len(compressed),
        "resident_table_offset": table_offset,
        "volatile_source_table_bytes": volatile_table_bytes,
        "old_table_sha256": _sha256(old_table),
        "new_table_sha256": _sha256(new_table),
        "bytes_changed_in_payload": sum(
            before != after for before, after in zip(payload, patched_payload)
        ),
    }
    return result, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--old-disc", type=Path, required=True)
    parser.add_argument("--new-disc", type=Path, required=True)
    parser.add_argument("--old-cue-name", required=True)
    parser.add_argument("--new-cue-name", required=True)
    parser.add_argument("--zstd", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        source = args.state.resolve()
        old_disc = args.old_disc.resolve()
        new_disc = args.new_disc.resolve()
        output = args.output.resolve()
        for path, label in (
            (source, "source state"),
            (old_disc, "old disc"),
            (new_disc, "new disc"),
        ):
            if not path.is_file():
                raise StateMigrationError(f"{label} does not exist: {path}")
        if output == source:
            raise StateMigrationError("Output must not overwrite the source state")
        if output.exists() and not args.force:
            raise StateMigrationError(
                f"Refusing to overwrite {output}; pass --force"
            )

        result, report = migrate_state(
            source.read_bytes(),
            old_disc=old_disc,
            new_disc=new_disc,
            old_cue_name=args.old_cue_name,
            new_cue_name=args.new_cue_name,
            zstd=_Zstd(args.zstd.resolve()),
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        print(f"Wrote {output} ({len(result)} bytes)")
        for key, value in report.items():
            print(f"{key}: {value}")
        return 0
    except (OSError, StateMigrationError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
