#!/usr/bin/env python3
"""Replace the exact resident field-376 script in the west-camera QA state.

This helper is deliberately pinned to the August 15, 2026 camera-removal
candidate.  It operates on a migrated, disposable DuckStation state, never on
the user's source slot.  The replacement is allowed only when the old script
occurs once inside serialized PSX RAM, nowhere else in the payload, the new
script is the same size, and their audited delta is exactly 46 bytes.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct
import sys

if __package__ in {None, ""}:
    PROJECT = Path(__file__).resolve().parents[3]
    if str(PROJECT) not in sys.path:
        sys.path.insert(0, str(PROJECT))
else:
    PROJECT = Path(__file__).resolve().parents[3]

from tools.migrate_duckstation_disc_state import (  # noqa: E402
    DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
    DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    DUCKSTATION_DATA_OFFSET_OFFSET,
    DUCKSTATION_DATA_UNCOMPRESSED_SIZE_OFFSET,
    DUCKSTATION_STATE_HEADER_SIZE,
    DUCKSTATION_STATE_MAGIC,
    DUCKSTATION_ZSTD_COMPRESSION_TYPE,
    StateMigrationError,
    _Zstd,
)
MIGRATED_STATE_SHA256 = (
    "646aab3e3d904fa477fafadc6e11aa922e30bd856a66ea3a54244302751a5518"
)
OLD_SCRIPT_SHA256 = (
    "bdbcfacf464841df93ba2a415aea03559273f715298e6ad98a189c29cfb3bcbc"
)
NEW_SCRIPT_SHA256 = (
    "cd714499c8ef9392f4dcb22e9e9b0c7de5d48148e7403e3d296d839c4292d845"
)
SCRIPT_SIZE = 48_930
SCRIPT_CHANGED_BYTES = 46
SCRIPT_DIFF_RANGES = ((0xBDAD, 0xBDCF), (0xBDE5, 0xBDEF))

EXPECTED_FRAME_START = 0x9E9C
EXPECTED_PAYLOAD_SIZE = 3_819_109
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
EXPECTED_SCRIPT_RAM_OFFSET = 0x1147E8
EXPECTED_SCRIPT_PAYLOAD_OFFSET = (
    EXPECTED_RAM_PAYLOAD_OFFSET + EXPECTED_SCRIPT_RAM_OFFSET
)
EXPECTED_SCRIPT_GUEST_POINTER = 0x801147E8
EXPECTED_VM_SCRIPT_GUEST_POINTER = 0x80114F6C

RAM_SIZE = 2 * 1024 * 1024
BUS_MARKER = struct.pack("<I", 3) + b"Bus"
BUS_TIMING_ARRAY_SIZE = 5 * 3 * 4
FIELD_CUR_SCRIPT_FILE = 0x0ADBF8
FIELD_SCRIPT_VM_CUR_SCRIPT_DATA = 0x0ADC00

NEW_CUE_PATH = str(
    (
        PROJECT
        / "work"
        / "west_camera_runtime_qa_20260815"
        / "Xenogears_Mass_Driver_no_cam.cue"
    ).resolve()
).encode("ascii")


class ResidentScriptReplacementError(RuntimeError):
    """Raised before writing when a QA state or script pin has drifted."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _diff_ranges(before: bytes, after: bytes) -> tuple[tuple[int, int], ...]:
    changed = [
        offset
        for offset, (old_byte, new_byte) in enumerate(zip(before, after))
        if old_byte != new_byte
    ]
    ranges: list[list[int]] = []
    for offset in changed:
        if not ranges or offset != ranges[-1][1] + 1:
            ranges.append([offset, offset])
        else:
            ranges[-1][1] = offset
    return tuple((start, end) for start, end in ranges)


def _psx_ram_offset(payload: bytes) -> int:
    """Return the 2 MiB RAM block's offset in a decompressed DuckStation state."""
    cursor = 0
    while True:
        marker = payload.find(BUS_MARKER, cursor)
        if marker < 0:
            raise ResidentScriptReplacementError(
                "could not locate DuckStation's serialized Bus state"
            )
        ram_size_offset = marker + len(BUS_MARKER)
        ram_size = struct.unpack_from("<I", payload, ram_size_offset)[0]
        ram_offset = ram_size_offset + 4 + BUS_TIMING_ARRAY_SIZE
        if ram_size == RAM_SIZE and ram_offset + ram_size <= len(payload):
            return ram_offset
        cursor = marker + 1


def _unpack_state(state: bytes, zstd: _Zstd) -> tuple[bytes, int]:
    if len(state) < DUCKSTATION_STATE_HEADER_SIZE:
        raise ResidentScriptReplacementError("state is shorter than its header")
    if state[:4] != DUCKSTATION_STATE_MAGIC:
        raise ResidentScriptReplacementError("input is not a DuckStation state")
    compression, compressed_size, payload_size, frame_start = struct.unpack_from(
        "<IIII", state, DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET
    )
    if compression != DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise ResidentScriptReplacementError(
            "DuckStation payload is not Zstandard-compressed"
        )
    if frame_start != EXPECTED_FRAME_START:
        raise ResidentScriptReplacementError(
            f"state frame starts at 0x{frame_start:X}, expected "
            f"0x{EXPECTED_FRAME_START:X}"
        )
    if frame_start + compressed_size != len(state):
        raise ResidentScriptReplacementError(
            "state compressed-data span does not end at EOF"
        )
    frame = state[frame_start:]
    if zstd.frame_size(frame) != compressed_size:
        raise ResidentScriptReplacementError(
            "state header compressed size does not match its zstd frame"
        )
    payload = zstd.decompress(frame)
    if len(payload) != payload_size or payload_size != EXPECTED_PAYLOAD_SIZE:
        raise ResidentScriptReplacementError(
            f"state payload size is {len(payload)}, expected "
            f"{EXPECTED_PAYLOAD_SIZE}"
        )
    return payload, frame_start


def replace_resident_script(
    state: bytes,
    *,
    old_script: bytes,
    new_script: bytes,
    zstd: _Zstd,
) -> tuple[bytes, dict[str, object]]:
    if _sha256(state) != MIGRATED_STATE_SHA256:
        raise ResidentScriptReplacementError("migrated QA state hash drifted")
    if state.count(NEW_CUE_PATH) != 1:
        raise ResidentScriptReplacementError(
            "migrated QA state does not contain its exact isolated CUE path once"
        )
    if (len(old_script), _sha256(old_script)) != (
        SCRIPT_SIZE,
        OLD_SCRIPT_SHA256,
    ):
        raise ResidentScriptReplacementError("old field-376 script pin drifted")
    if (len(new_script), _sha256(new_script)) != (
        SCRIPT_SIZE,
        NEW_SCRIPT_SHA256,
    ):
        raise ResidentScriptReplacementError("new field-376 script pin drifted")
    if len(old_script) != len(new_script):
        raise ResidentScriptReplacementError("resident scripts are not the same size")
    changed = sum(a != b for a, b in zip(old_script, new_script))
    diff_ranges = _diff_ranges(old_script, new_script)
    if changed != SCRIPT_CHANGED_BYTES or diff_ranges != SCRIPT_DIFF_RANGES:
        raise ResidentScriptReplacementError(
            f"script delta is {changed} bytes in {diff_ranges}, expected "
            f"{SCRIPT_CHANGED_BYTES} bytes in {SCRIPT_DIFF_RANGES}"
        )

    payload, frame_start = _unpack_state(state, zstd)
    ram_payload_offset = _psx_ram_offset(payload)
    if ram_payload_offset != EXPECTED_RAM_PAYLOAD_OFFSET:
        raise ResidentScriptReplacementError(
            f"serialized RAM starts at payload 0x{ram_payload_offset:X}, expected "
            f"0x{EXPECTED_RAM_PAYLOAD_OFFSET:X}"
        )
    ram = payload[ram_payload_offset : ram_payload_offset + RAM_SIZE]
    if len(ram) != RAM_SIZE:
        raise ResidentScriptReplacementError("serialized PSX RAM is incomplete")
    if payload.count(old_script) != 1 or ram.count(old_script) != 1:
        raise ResidentScriptReplacementError(
            "old script must occur exactly once inside PSX RAM and nowhere else"
        )
    if payload.count(new_script) != 0:
        raise ResidentScriptReplacementError(
            "new script already occurs in the migrated state"
        )
    script_ram_offset = ram.find(old_script)
    script_payload_offset = payload.find(old_script)
    if (
        script_ram_offset != EXPECTED_SCRIPT_RAM_OFFSET
        or script_payload_offset != EXPECTED_SCRIPT_PAYLOAD_OFFSET
    ):
        raise ResidentScriptReplacementError(
            "resident field-376 script is not at its audited RAM location"
        )
    current_script = struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0]
    vm_script = struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA)[0]
    if (
        current_script != EXPECTED_SCRIPT_GUEST_POINTER
        or vm_script != EXPECTED_VM_SCRIPT_GUEST_POINTER
    ):
        raise ResidentScriptReplacementError(
            "field-script runtime pointers do not match the audited settled state"
        )

    patched_payload = bytearray(payload)
    patched_payload[
        script_payload_offset : script_payload_offset + SCRIPT_SIZE
    ] = new_script
    if (
        patched_payload[:script_payload_offset] != payload[:script_payload_offset]
        or patched_payload[script_payload_offset + SCRIPT_SIZE :]
        != payload[script_payload_offset + SCRIPT_SIZE :]
    ):
        raise ResidentScriptReplacementError(
            "payload changed outside the resident field-376 script"
        )
    if (
        bytes(patched_payload).count(old_script) != 0
        or bytes(patched_payload).count(new_script) != 1
    ):
        raise ResidentScriptReplacementError(
            "resident script replacement did not produce one exact new copy"
        )
    payload_changed = sum(
        old_byte != new_byte
        for old_byte, new_byte in zip(payload, patched_payload)
    )
    if payload_changed != SCRIPT_CHANGED_BYTES:
        raise ResidentScriptReplacementError(
            f"payload changed by {payload_changed} bytes, expected "
            f"{SCRIPT_CHANGED_BYTES}"
        )

    compressed = zstd.compress(bytes(patched_payload))
    prefix = bytearray(state[:frame_start])
    struct.pack_into(
        "<I", prefix, DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET, len(compressed)
    )
    result = bytes(prefix) + compressed
    verified_payload, verified_frame_start = _unpack_state(result, zstd)
    if verified_frame_start != frame_start or verified_payload != patched_payload:
        raise ResidentScriptReplacementError(
            "recompressed resident-script state did not round-trip exactly"
        )
    if result.count(NEW_CUE_PATH) != 1:
        raise ResidentScriptReplacementError(
            "resident-script replacement changed the isolated CUE path"
        )

    return result, {
        "source_sha256": _sha256(state),
        "output_sha256": _sha256(result),
        "source_size": len(state),
        "output_size": len(result),
        "payload_size": len(payload),
        "payload_sha256": _sha256(verified_payload),
        "ram_payload_offset": f"0x{ram_payload_offset:X}",
        "script_ram_offset": f"0x{script_ram_offset:X}",
        "script_payload_offset": f"0x{script_payload_offset:X}",
        "old_script_sha256": OLD_SCRIPT_SHA256,
        "new_script_sha256": NEW_SCRIPT_SHA256,
        "script_size": SCRIPT_SIZE,
        "script_bytes_changed": payload_changed,
        "script_diff_ranges": ", ".join(
            f"0x{start:X}-0x{end:X}" for start, end in diff_ranges
        ),
        "payload_bytes_changed_outside_script": 0,
        "round_trip_verified": True,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--old-script",
        type=Path,
        default=(
            PROJECT
            / "work"
            / "mass_driver_title_branding_removed_stage_a"
            / "clones"
            / "field_376"
            / "05_scripts.bin"
        ),
    )
    parser.add_argument(
        "--new-script",
        type=Path,
        default=(
            PROJECT
            / "work"
            / "wca_stage"
            / "clones"
            / "field_376"
            / "05_scripts.bin"
        ),
    )
    parser.add_argument(
        "--zstd",
        type=Path,
        default=PROJECT / "work" / "duckstation" / "zstd.dll",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        source = args.source.resolve()
        output = args.output.resolve()
        if source == output:
            raise ResidentScriptReplacementError(
                "source and output state paths must differ"
            )
        for path, label in (
            (source, "source state"),
            (args.old_script.resolve(), "old script"),
            (args.new_script.resolve(), "new script"),
            (args.zstd.resolve(), "zstd library"),
        ):
            if not path.is_file():
                raise ResidentScriptReplacementError(f"{label} is missing: {path}")
        if output.exists():
            raise ResidentScriptReplacementError(
                f"refusing to overwrite existing output: {output}"
            )

        result, report = replace_resident_script(
            source.read_bytes(),
            old_script=args.old_script.resolve().read_bytes(),
            new_script=args.new_script.resolve().read_bytes(),
            zstd=_Zstd(args.zstd.resolve()),
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        print(f"Wrote {output} ({len(result)} bytes)")
        for key, value in report.items():
            print(f"{key}: {value}")
        return 0
    except (OSError, StateMigrationError, ResidentScriptReplacementError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
