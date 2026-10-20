#!/usr/bin/env python3
"""Create a repaired copy of the audited Rico Chapter 1 stove savestate.

The 2026-09-02 Slot 1 captures Rico at a valid central-cooktop stance, but its
resident field script still rejects that stance with the old diagonal contact
minimum.  This migration replaces the exact equal-length resident ATEL script
with the rebuilt one.  It is deliberately tied to that one audited state and
never permits the source path to be overwritten.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct
import sys
from typing import Sequence

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from tools.build_rico_arc import SCRIPT_INDEX
from tools.migrate_duckstation_disc_state import (
    DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
    DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    DUCKSTATION_DATA_OFFSET_OFFSET,
    DUCKSTATION_DATA_UNCOMPRESSED_SIZE_OFFSET,
    DUCKSTATION_STATE_HEADER_SIZE,
    DUCKSTATION_STATE_MAGIC,
    DUCKSTATION_ZSTD_COMPRESSION_TYPE,
    _Zstd,
)
from tools.xgfield import parse_field
from work.read_duckstation_runtime import (
    FIELD_CUR_SCRIPT_FILE,
    RAM_SIZE,
    _psx_ram_offset,
)


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BUNDLE = ROOT / "output" / "rico_arc" / "prepared" / "disc1" / "2048.bin"
DEFAULT_ZSTD = ROOT / "work" / "duckstation" / "zstd.dll"

SOURCE_STATE_SIZE = 1_673_608
SOURCE_STATE_SHA256 = (
    "d8b1a6ef162a115ac5445f72926daf5b9aa17360c944a344ea45567eb06344a8"
)
SOURCE_PAYLOAD_SIZE = 3_817_429
SOURCE_PAYLOAD_SHA256 = (
    "e3ab6fbee048320c263299bc742bc355ee9910356fc06b02d33dc01578e938d5"
)
SOURCE_FRAME_OFFSET = 0xACAA
SOURCE_RAM_OFFSET = 0x1A62
RESIDENT_SCRIPT_RAM_OFFSET = 0x10ADC0
RESIDENT_SCRIPT_SIZE = 5_393
SOURCE_SCRIPT_SHA256 = (
    "64e9bb9d2415baceb4f764d616c1c6bb349fb93244c06648546e2563be6b8c29"
)
REPAIRED_SCRIPT_SHA256 = (
    "1d2480f9636f9964fce105cbb7f2a5cd7f7c52a88cf133f172a72b2ba726ced1"
)
GATE_LITERAL_SCRIPT_OFFSET = 0x11CD
SOURCE_GATE_LITERAL = 0x40
REPAIRED_GATE_LITERAL = 0x3C
EXPECTED_SCRIPT_DIFF = (
    GATE_LITERAL_SCRIPT_OFFSET,
    SOURCE_GATE_LITERAL,
    REPAIRED_GATE_LITERAL,
)


class RicoStoveStateMigrationError(RuntimeError):
    """Raised before writing when an input leaves the audited migration path."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _differences(before: bytes, after: bytes) -> tuple[tuple[int, int, int], ...]:
    if len(before) != len(after):
        raise RicoStoveStateMigrationError(
            f"Compared byte strings differ in size: {len(before)} != {len(after)}"
        )
    return tuple(
        (offset, old, new)
        for offset, (old, new) in enumerate(zip(before, after))
        if old != new
    )


def migrate_state(
    state: bytes,
    *,
    repaired_field_bundle: bytes,
    zstd: _Zstd,
) -> tuple[bytes, dict[str, object]]:
    """Return one validated repaired copy and an audit report."""

    state_hash = _sha256(state)
    if len(state) != SOURCE_STATE_SIZE or state_hash != SOURCE_STATE_SHA256:
        raise RicoStoveStateMigrationError(
            "Source Slot 1 identity changed: "
            f"{len(state)} bytes / {state_hash}; expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    if (
        len(state) < DUCKSTATION_STATE_HEADER_SIZE
        or state[:4] != DUCKSTATION_STATE_MAGIC
    ):
        raise RicoStoveStateMigrationError("Source is not a DuckStation state")

    compression_type, compressed_size, payload_size, frame_offset = (
        struct.unpack_from(
            "<IIII",
            state,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
        )
    )
    if compression_type != DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise RicoStoveStateMigrationError("State payload is not Zstandard-compressed")
    if frame_offset != SOURCE_FRAME_OFFSET:
        raise RicoStoveStateMigrationError(
            f"State frame moved: 0x{frame_offset:X} != 0x{SOURCE_FRAME_OFFSET:X}"
        )
    if frame_offset + compressed_size != len(state):
        raise RicoStoveStateMigrationError("Compressed state span does not end at EOF")
    if zstd.frame_size(state[frame_offset:]) != compressed_size:
        raise RicoStoveStateMigrationError("Declared compressed size is incorrect")

    payload = bytearray(zstd.decompress(state[frame_offset:]))
    if payload_size != SOURCE_PAYLOAD_SIZE or len(payload) != SOURCE_PAYLOAD_SIZE:
        raise RicoStoveStateMigrationError("Decompressed payload size changed")
    payload_hash = _sha256(payload)
    if payload_hash != SOURCE_PAYLOAD_SHA256:
        raise RicoStoveStateMigrationError(
            f"Decompressed payload identity changed: {payload_hash}"
        )
    ram_offset = _psx_ram_offset(payload)
    if ram_offset != SOURCE_RAM_OFFSET:
        raise RicoStoveStateMigrationError(
            f"PSX RAM moved: 0x{ram_offset:X} != 0x{SOURCE_RAM_OFFSET:X}"
        )
    ram = memoryview(payload)[ram_offset : ram_offset + RAM_SIZE]
    resident_pointer = (
        struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0] & 0x1FFFFFFF
    )
    if resident_pointer != RESIDENT_SCRIPT_RAM_OFFSET:
        raise RicoStoveStateMigrationError(
            "Resident field script moved: "
            f"0x{resident_pointer:X} != 0x{RESIDENT_SCRIPT_RAM_OFFSET:X}"
        )

    parsed = parse_field(repaired_field_bundle)
    repaired_script = parsed.parts[SCRIPT_INDEX].data
    if (
        len(repaired_script) != RESIDENT_SCRIPT_SIZE
        or _sha256(repaired_script) != REPAIRED_SCRIPT_SHA256
    ):
        raise RicoStoveStateMigrationError(
            "Rebuilt Chapter 1 script is not the audited stove repair"
        )
    resident_end = resident_pointer + RESIDENT_SCRIPT_SIZE
    source_script = bytes(ram[resident_pointer:resident_end])
    if _sha256(source_script) != SOURCE_SCRIPT_SHA256:
        raise RicoStoveStateMigrationError(
            "Resident Chapter 1 script is not the audited pre-fix script"
        )
    script_differences = _differences(source_script, repaired_script)
    if script_differences != (EXPECTED_SCRIPT_DIFF,):
        raise RicoStoveStateMigrationError(
            f"Unexpected resident script changes: {script_differences}"
        )

    source_payload = bytes(payload)
    ram[resident_pointer:resident_end] = repaired_script
    repaired_payload = bytes(payload)
    payload_differences = _differences(source_payload, repaired_payload)
    expected_payload_offset = (
        ram_offset + resident_pointer + GATE_LITERAL_SCRIPT_OFFSET
    )
    expected_payload_diff = (
        expected_payload_offset,
        SOURCE_GATE_LITERAL,
        REPAIRED_GATE_LITERAL,
    )
    if payload_differences != (expected_payload_diff,):
        raise RicoStoveStateMigrationError(
            f"Migration changed unexpected payload bytes: {payload_differences}"
        )

    compressed = zstd.compress(repaired_payload)
    prefix = bytearray(state[:frame_offset])
    struct.pack_into(
        "<I",
        prefix,
        DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        len(compressed),
    )
    result = bytes(prefix) + compressed
    if zstd.decompress(result[frame_offset:]) != repaired_payload:
        raise RicoStoveStateMigrationError("Repaired state failed its zstd round trip")

    report: dict[str, object] = {
        "source_state_sha256": state_hash,
        "repaired_state_sha256": _sha256(result),
        "source_state_size": len(state),
        "repaired_state_size": len(result),
        "payload_sha256": _sha256(repaired_payload),
        "resident_script_ram_offset": resident_pointer,
        "resident_script_sha256": _sha256(repaired_script),
        "changed_payload_offset": expected_payload_offset,
        "old_gate_minimum": 320,
        "new_gate_minimum": 316,
    }
    return result, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--zstd", type=Path, default=DEFAULT_ZSTD)
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = args.source.resolve()
    output = args.output.resolve()
    bundle = args.bundle.resolve()
    if source == output:
        raise SystemExit("Output must be separate and may not be live Slot 1")
    for path, label in (
        (source, "source state"),
        (bundle, "repaired Chapter 1 bundle"),
        (args.zstd.resolve(), "zstd library"),
    ):
        if not path.is_file():
            raise SystemExit(f"{label} does not exist: {path}")
    if output.exists() and not args.force:
        raise SystemExit(f"Output already exists (use --force): {output}")

    try:
        result, report = migrate_state(
            source.read_bytes(),
            repaired_field_bundle=bundle.read_bytes(),
            zstd=_Zstd(args.zstd.resolve()),
        )
    except RicoStoveStateMigrationError as exc:
        raise SystemExit(str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)
    print(f"Wrote repaired savestate candidate: {output}")
    for key, value in report.items():
        if isinstance(value, int) and "offset" in key:
            value = f"0x{value:X}"
        print(f"{key}: {value}")
    print("The source Slot 1 was not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
