#!/usr/bin/env python3
"""Prepare the exact disposable save used to test the video-terminal reach fix.

The user's save already contains field 376 in RAM, so mounting the corrected
disc is not enough: entity 21's initializer has already installed its old
pivot and collision bounds.  This helper is deliberately pinned to that one
migrated QA state.  It replaces the equal-length resident script and updates
only the live entity-21 Z coordinate and its X/Z interaction extents.  The
user's source slot is never overwritten.
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
    DUCKSTATION_STATE_HEADER_SIZE,
    DUCKSTATION_STATE_MAGIC,
    DUCKSTATION_ZSTD_COMPRESSION_TYPE,
    StateMigrationError,
    _Zstd,
)


MIGRATED_STATE_SHA256 = (
    "dbf2ded45cf1768271cf7ebdcf84d9f80ec284040f9f110d1ee68f98b981bdfb"
)
OLD_SCRIPT_SHA256 = (
    "7c6de99d76cc74527665146b33952a3ac8b00458c384b7bc5eaf7a3cff0e4e0d"
)
NEW_SCRIPT_SHA256 = (
    "b1699971a6529c597e145bd8d3a019c4df8adea42ac77c903a66400f92348f2c"
)
SCRIPT_SIZE = 48_946
SCRIPT_DIFFS = {
    0x7490: (0x5B, 0x6C),
    0x749C: (0x04, 0x0C),
    0x749D: (0x04, 0x0C),
}

EXPECTED_FRAME_START = 0x139B8
EXPECTED_PAYLOAD_SIZE = 3_819_074
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

FIELD_ACTOR_ARRAY = 0x126040
FIELD_ACTOR_SIZE = 0x5C
VIDEO_TERMINAL_ENTITY = 21
VIDEO_TERMINAL_FIELD_ACTOR = (
    FIELD_ACTOR_ARRAY + VIDEO_TERMINAL_ENTITY * FIELD_ACTOR_SIZE
)
FIELD_ACTOR_SCRIPT_ENTITY_POINTER_OFFSET = 0x4C
VIDEO_TERMINAL_ACTOR_DATA = 0x129640
VIDEO_TERMINAL_ACTOR_DATA_POINTER = 0x80129640

FLAGS0_OFFSET = 0x00
FLAGS4_OFFSET = 0x04
TRIANGLE_OFFSET = 0x08
BOUND_X_OFFSET = 0x18
BOUND_Y_OFFSET = 0x1A
BOUND_Z_OFFSET = 0x1C
COLLISION_RADIUS_OFFSET = 0x1E
POSITION_X_OFFSET = 0x20
POSITION_Y_OFFSET = 0x24
POSITION_Z_OFFSET = 0x28
TOUCHED_ACTOR_OFFSET = 0x74
CURRENT_SCRIPT_PC_OFFSET = 0xCC

EXPECTED_FLAGS0 = 0x00402180
EXPECTED_FLAGS4 = 0x00040800
EXPECTED_TRIANGLE = 146
EXPECTED_OLD_POSITION = (264 << 16, 0, -165 << 16)
EXPECTED_NEW_POSITION = (264 << 16, 0, -148 << 16)
EXPECTED_OLD_BOUNDS = (8, 200, 8, 16)
EXPECTED_NEW_BOUNDS = (24, 200, 24, 16)
EXPECTED_TOUCHED_ACTOR = -1
EXPECTED_IDLE_PC = 0x082F

NEW_CUE_PATH = str(
    (
        PROJECT
        / "work"
        / "term_bounds_runtime_qa_20260815"
        / "Xenogears_Mass_Driver_no_cam.cue"
    ).resolve()
).encode("ascii")


class VideoTerminalStateError(RuntimeError):
    """Raised before output when an audited state contract has drifted."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _psx_ram_offset(payload: bytes) -> int:
    cursor = 0
    while True:
        marker = payload.find(BUS_MARKER, cursor)
        if marker < 0:
            raise VideoTerminalStateError(
                "could not locate DuckStation's serialized Bus state"
            )
        size_offset = marker + len(BUS_MARKER)
        ram_size = struct.unpack_from("<I", payload, size_offset)[0]
        ram_offset = size_offset + 4 + BUS_TIMING_ARRAY_SIZE
        if ram_size == RAM_SIZE and ram_offset + ram_size <= len(payload):
            return ram_offset
        cursor = marker + 1


def _unpack_state(state: bytes, zstd: _Zstd) -> tuple[bytes, int]:
    if len(state) < DUCKSTATION_STATE_HEADER_SIZE:
        raise VideoTerminalStateError("state is shorter than its header")
    if state[:4] != DUCKSTATION_STATE_MAGIC:
        raise VideoTerminalStateError("input is not a DuckStation state")
    compression, compressed_size, payload_size, frame_start = struct.unpack_from(
        "<IIII", state, DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET
    )
    if compression != DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise VideoTerminalStateError(
            "DuckStation payload is not Zstandard-compressed"
        )
    if frame_start != EXPECTED_FRAME_START:
        raise VideoTerminalStateError(
            f"state frame starts at 0x{frame_start:X}, expected "
            f"0x{EXPECTED_FRAME_START:X}"
        )
    if frame_start + compressed_size != len(state):
        raise VideoTerminalStateError(
            "state compressed-data span does not end at EOF"
        )
    frame = state[frame_start:]
    if zstd.frame_size(frame) != compressed_size:
        raise VideoTerminalStateError(
            "state header compressed size does not match its zstd frame"
        )
    payload = zstd.decompress(frame)
    if len(payload) != payload_size or payload_size != EXPECTED_PAYLOAD_SIZE:
        raise VideoTerminalStateError(
            f"state payload size is {len(payload)}, expected "
            f"{EXPECTED_PAYLOAD_SIZE}"
        )
    return payload, frame_start


def _script_delta(old_script: bytes, new_script: bytes) -> dict[int, tuple[int, int]]:
    return {
        offset: (old_byte, new_byte)
        for offset, (old_byte, new_byte) in enumerate(
            zip(old_script, new_script, strict=True)
        )
        if old_byte != new_byte
    }


def _read_actor_contract(ram: bytes) -> dict[str, object]:
    base = VIDEO_TERMINAL_ACTOR_DATA
    return {
        "flags0": struct.unpack_from("<I", ram, base + FLAGS0_OFFSET)[0],
        "flags4": struct.unpack_from("<I", ram, base + FLAGS4_OFFSET)[0],
        "triangle": struct.unpack_from("<h", ram, base + TRIANGLE_OFFSET)[0],
        "bounds": tuple(
            struct.unpack_from("<h", ram, base + offset)[0]
            for offset in (
                BOUND_X_OFFSET,
                BOUND_Y_OFFSET,
                BOUND_Z_OFFSET,
                COLLISION_RADIUS_OFFSET,
            )
        ),
        "position": tuple(
            struct.unpack_from("<i", ram, base + offset)[0]
            for offset in (
                POSITION_X_OFFSET,
                POSITION_Y_OFFSET,
                POSITION_Z_OFFSET,
            )
        ),
        "touched_actor": struct.unpack_from(
            "<b", ram, base + TOUCHED_ACTOR_OFFSET
        )[0],
        "current_script_pc": struct.unpack_from(
            "<H", ram, base + CURRENT_SCRIPT_PC_OFFSET
        )[0],
    }


def prepare_state(
    state: bytes,
    *,
    old_script: bytes,
    new_script: bytes,
    zstd: _Zstd,
) -> tuple[bytes, dict[str, object]]:
    if _sha256(state) != MIGRATED_STATE_SHA256:
        raise VideoTerminalStateError("migrated QA state hash drifted")
    if state.count(NEW_CUE_PATH) != 1:
        raise VideoTerminalStateError(
            "migrated QA state does not contain its isolated CUE path once"
        )
    if (len(old_script), _sha256(old_script)) != (
        SCRIPT_SIZE,
        OLD_SCRIPT_SHA256,
    ):
        raise VideoTerminalStateError("old field-376 script pin drifted")
    if (len(new_script), _sha256(new_script)) != (
        SCRIPT_SIZE,
        NEW_SCRIPT_SHA256,
    ):
        raise VideoTerminalStateError("new field-376 script pin drifted")
    if _script_delta(old_script, new_script) != SCRIPT_DIFFS:
        raise VideoTerminalStateError("field-376 script delta is not exact")

    payload, frame_start = _unpack_state(state, zstd)
    ram_payload_offset = _psx_ram_offset(payload)
    if ram_payload_offset != EXPECTED_RAM_PAYLOAD_OFFSET:
        raise VideoTerminalStateError(
            f"serialized RAM starts at 0x{ram_payload_offset:X}, expected "
            f"0x{EXPECTED_RAM_PAYLOAD_OFFSET:X}"
        )
    ram = payload[ram_payload_offset : ram_payload_offset + RAM_SIZE]
    if len(ram) != RAM_SIZE:
        raise VideoTerminalStateError("serialized PSX RAM is incomplete")
    if payload.count(old_script) != 1 or ram.count(old_script) != 1:
        raise VideoTerminalStateError(
            "old field-376 script must occur once inside serialized RAM"
        )
    if payload.count(new_script) != 0:
        raise VideoTerminalStateError("new field-376 script is already resident")
    if (
        ram.find(old_script) != EXPECTED_SCRIPT_RAM_OFFSET
        or payload.find(old_script) != EXPECTED_SCRIPT_PAYLOAD_OFFSET
    ):
        raise VideoTerminalStateError(
            "resident field-376 script is not at its audited address"
        )
    if (
        struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0]
        != EXPECTED_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA)[0]
        != EXPECTED_VM_SCRIPT_GUEST_POINTER
    ):
        raise VideoTerminalStateError("live field-script pointers drifted")
    actor_pointer = struct.unpack_from(
        "<I",
        ram,
        VIDEO_TERMINAL_FIELD_ACTOR
        + FIELD_ACTOR_SCRIPT_ENTITY_POINTER_OFFSET,
    )[0]
    if actor_pointer != VIDEO_TERMINAL_ACTOR_DATA_POINTER:
        raise VideoTerminalStateError("entity-21 ActorData pointer drifted")

    before_actor = _read_actor_contract(ram)
    expected_before_actor = {
        "flags0": EXPECTED_FLAGS0,
        "flags4": EXPECTED_FLAGS4,
        "triangle": EXPECTED_TRIANGLE,
        "bounds": EXPECTED_OLD_BOUNDS,
        "position": EXPECTED_OLD_POSITION,
        "touched_actor": EXPECTED_TOUCHED_ACTOR,
        "current_script_pc": EXPECTED_IDLE_PC,
    }
    if before_actor != expected_before_actor:
        raise VideoTerminalStateError(
            f"entity-21 live initializer state drifted: {before_actor}"
        )

    patched_payload = bytearray(payload)
    patched_payload[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET :
        EXPECTED_SCRIPT_PAYLOAD_OFFSET + SCRIPT_SIZE
    ] = new_script
    actor_payload = ram_payload_offset + VIDEO_TERMINAL_ACTOR_DATA
    struct.pack_into(
        "<h",
        patched_payload,
        actor_payload + BOUND_X_OFFSET,
        EXPECTED_NEW_BOUNDS[0],
    )
    struct.pack_into(
        "<h",
        patched_payload,
        actor_payload + BOUND_Z_OFFSET,
        EXPECTED_NEW_BOUNDS[2],
    )
    struct.pack_into(
        "<i",
        patched_payload,
        actor_payload + POSITION_Z_OFFSET,
        EXPECTED_NEW_POSITION[2],
    )

    verified_ram = bytes(
        patched_payload[ram_payload_offset : ram_payload_offset + RAM_SIZE]
    )
    after_actor = _read_actor_contract(verified_ram)
    expected_after_actor = {
        **expected_before_actor,
        "bounds": EXPECTED_NEW_BOUNDS,
        "position": EXPECTED_NEW_POSITION,
    }
    if after_actor != expected_after_actor:
        raise VideoTerminalStateError(
            f"entity-21 live patched state is wrong: {after_actor}"
        )
    if (
        bytes(patched_payload).count(old_script) != 0
        or bytes(patched_payload).count(new_script) != 1
    ):
        raise VideoTerminalStateError(
            "resident script replacement did not produce one new copy"
        )

    changed_offsets = [
        offset
        for offset, (before, after) in enumerate(
            zip(payload, patched_payload, strict=True)
        )
        if before != after
    ]
    expected_changed_offsets = sorted(
        [
            EXPECTED_SCRIPT_PAYLOAD_OFFSET + offset
            for offset in SCRIPT_DIFFS
        ]
        + [
            actor_payload + BOUND_X_OFFSET,
            actor_payload + BOUND_Z_OFFSET,
            actor_payload + POSITION_Z_OFFSET + 2,
        ]
    )
    if changed_offsets != expected_changed_offsets:
        raise VideoTerminalStateError(
            "payload changed outside the exact script/controller bytes: "
            f"{[hex(offset) for offset in changed_offsets]}"
        )

    compressed = zstd.compress(bytes(patched_payload))
    prefix = bytearray(state[:frame_start])
    struct.pack_into(
        "<I", prefix, DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET, len(compressed)
    )
    result = bytes(prefix) + compressed
    round_trip_payload, round_trip_frame_start = _unpack_state(result, zstd)
    if (
        round_trip_frame_start != frame_start
        or round_trip_payload != bytes(patched_payload)
    ):
        raise VideoTerminalStateError(
            "recompressed video-terminal state did not round-trip exactly"
        )
    if result.count(NEW_CUE_PATH) != 1:
        raise VideoTerminalStateError(
            "video-terminal patch changed the isolated CUE path"
        )

    return result, {
        "source_sha256": _sha256(state),
        "output_sha256": _sha256(result),
        "source_size": len(state),
        "output_size": len(result),
        "payload_size": len(payload),
        "payload_sha256": _sha256(round_trip_payload),
        "ram_payload_offset": f"0x{ram_payload_offset:X}",
        "script_ram_offset": f"0x{EXPECTED_SCRIPT_RAM_OFFSET:X}",
        "old_script_sha256": OLD_SCRIPT_SHA256,
        "new_script_sha256": NEW_SCRIPT_SHA256,
        "script_size": SCRIPT_SIZE,
        "payload_bytes_changed": len(changed_offsets),
        "payload_changed_offsets": ", ".join(
            f"0x{offset:X}" for offset in changed_offsets
        ),
        "actor_before": before_actor,
        "actor_after": after_actor,
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
            / "wcr_a_stage"
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
            / "vta_stage"
            / "clones"
            / "field_376"
            / "05_scripts.bin"
        ),
    )
    parser.add_argument(
        "--zstd",
        type=Path,
        default=(
            PROJECT
            / "work"
            / "term_bounds_runtime_qa_20260815"
            / "zstd.dll"
        ),
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        source = args.source.resolve()
        output = args.output.resolve()
        if source == output:
            raise VideoTerminalStateError("source and output paths must differ")
        for path, label in (
            (source, "source state"),
            (args.old_script.resolve(), "old script"),
            (args.new_script.resolve(), "new script"),
            (args.zstd.resolve(), "zstd library"),
        ):
            if not path.is_file():
                raise VideoTerminalStateError(f"{label} is missing: {path}")
        if output.exists():
            raise VideoTerminalStateError(
                f"refusing to overwrite existing output: {output}"
            )
        result, report = prepare_state(
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
    except (OSError, StateMigrationError, VideoTerminalStateError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
