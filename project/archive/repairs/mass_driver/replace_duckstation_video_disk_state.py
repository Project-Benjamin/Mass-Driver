#!/usr/bin/env python3
"""Prepare the disposable save used to test the video-disk reach repair.

The user's captured state has field 376 resident from the previous VTA media.
Mounting the rebuilt VDA disc alone would therefore retain entity 26's old
initializer results and resident script.  This helper is deliberately pinned
to the one media-migrated QA state.  It replaces the equal-length field script
and updates only entity 26's live Z coordinate and X/Z interaction extents.
The user's source slot is never overwritten.
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


# This is the deterministic result of migrating the pinned user source state
# to the equal-length disk_bounds profile while the VTA and VDA FAT tables are
# byte-identical.  The helper will refuse the state if the final VDA build
# changes that table or any other migration input.
MIGRATED_STATE_SHA256 = (
    "dcc2afc487305774c0cc776c559c7a45c0f65bfa52b3d1809bf2ccbb7aa85382"
)
OLD_SCRIPT_SHA256 = (
    "b1699971a6529c597e145bd8d3a019c4df8adea42ac77c903a66400f92348f2c"
)
NEW_SCRIPT_SHA256 = (
    "6490ad77c3a0a9f731ff5498df5b6e12936c29d932082f2c8f66d074afd2fd9b"
)
SCRIPT_SIZE = 48_946
SCRIPT_DIFFS = {
    0xBE82: (0x5E, 0x6C),
    0xBE8E: (0x04, 0x0C),
    0xBE8F: (0x04, 0x0C),
}

EXPECTED_FRAME_START = 0x13F19
EXPECTED_PAYLOAD_SIZE = 3_687_980
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

GAME_SCENE_MAP = 0x04F34C
FIELD_CUR_SCRIPT_FILE = 0x0ADBF8
FIELD_SCRIPT_VM_CUR_SCRIPT_DATA = 0x0ADC00
FIELD_NUM_ACTORS = 0x0AFB0C
FIELD_ACTORS = 0x0AFB10
FIELD_PLAYER_ACTOR_INDEX = 0x0B226C

FIELD_ACTOR_ARRAY = 0x126040
FIELD_ACTOR_ARRAY_POINTER = 0x80126040
FIELD_ACTOR_SIZE = 0x5C
FIELD_ACTOR_SCRIPT_ENTITY_POINTER_OFFSET = 0x4C

PLAYER_ENTITY = 2
PLAYER_FIELD_ACTOR = FIELD_ACTOR_ARRAY + PLAYER_ENTITY * FIELD_ACTOR_SIZE
PLAYER_ACTOR_DATA = 0x127388
PLAYER_ACTOR_DATA_POINTER = 0x80127388

VIDEO_DISK_ENTITY = 26
VIDEO_DISK_FIELD_ACTOR = (
    FIELD_ACTOR_ARRAY + VIDEO_DISK_ENTITY * FIELD_ACTOR_SIZE
)
VIDEO_DISK_ACTOR_DATA = 0x129ED8
VIDEO_DISK_ACTOR_DATA_POINTER = 0x80129ED8

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
CURRENT_SCRIPT_SLOT_OFFSET = 0xCE
CURRENT_EVENT_SLOT_OFFSET = 0xCF
ROTATION_Y_OFFSET = 0x106

EXPECTED_FIELD = 376
EXPECTED_ACTOR_COUNT = 44
EXPECTED_PLAYER_INDEX = PLAYER_ENTITY
EXPECTED_PLAYER_TRIANGLE = 157
EXPECTED_PLAYER_POSITION = (-5_450_370, 0, -10_795_482)
EXPECTED_PLAYER_YAW = 0x0C00

EXPECTED_FLAGS0 = 0x00402180
EXPECTED_FLAGS4 = 0x00040800
EXPECTED_TRIANGLE = 157
EXPECTED_OLD_POSITION = (-75 << 16, 0, -162 << 16)
EXPECTED_NEW_POSITION = (-75 << 16, 0, -148 << 16)
EXPECTED_OLD_BOUNDS = (8, 200, 8, 16)
EXPECTED_NEW_BOUNDS = (24, 200, 24, 16)
EXPECTED_TOUCHED_ACTOR = -1
EXPECTED_IDLE_PC = 0x082F
EXPECTED_CURRENT_SCRIPT_SLOT = 0
EXPECTED_CURRENT_EVENT_SLOT = 0

OLD_CUE_PATH = str(
    (
        PROJECT
        / "work"
        / "term_bounds_runtime_qa_20260815"
        / "Xenogears_Mass_Driver_no_cam.cue"
    ).resolve()
).encode("ascii")
NEW_CUE_PATH = str(
    (
        PROJECT
        / "work"
        / "disk_bounds_runtime_qa_20260815"
        / "Xenogears_Mass_Driver_no_cam.cue"
    ).resolve()
).encode("ascii")


class VideoDiskStateError(RuntimeError):
    """Raised before output when an audited state contract has drifted."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _psx_ram_offset(payload: bytes) -> int:
    cursor = 0
    while True:
        marker = payload.find(BUS_MARKER, cursor)
        if marker < 0:
            raise VideoDiskStateError(
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
        raise VideoDiskStateError("state is shorter than its header")
    if state[:4] != DUCKSTATION_STATE_MAGIC:
        raise VideoDiskStateError("input is not a DuckStation state")
    compression, compressed_size, payload_size, frame_start = struct.unpack_from(
        "<IIII", state, DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET
    )
    if compression != DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise VideoDiskStateError(
            "DuckStation payload is not Zstandard-compressed"
        )
    if frame_start != EXPECTED_FRAME_START:
        raise VideoDiskStateError(
            f"state frame starts at 0x{frame_start:X}, expected "
            f"0x{EXPECTED_FRAME_START:X}"
        )
    if frame_start + compressed_size != len(state):
        raise VideoDiskStateError(
            "state compressed-data span does not end at EOF"
        )
    frame = state[frame_start:]
    if zstd.frame_size(frame) != compressed_size:
        raise VideoDiskStateError(
            "state header compressed size does not match its zstd frame"
        )
    payload = zstd.decompress(frame)
    if len(payload) != payload_size or payload_size != EXPECTED_PAYLOAD_SIZE:
        raise VideoDiskStateError(
            f"state payload size is {len(payload)}, expected "
            f"{EXPECTED_PAYLOAD_SIZE}"
        )
    return payload, frame_start


def _script_delta(
    old_script: bytes,
    new_script: bytes,
) -> dict[int, tuple[int, int]]:
    return {
        offset: (old_byte, new_byte)
        for offset, (old_byte, new_byte) in enumerate(
            zip(old_script, new_script, strict=True)
        )
        if old_byte != new_byte
    }


def _read_actor_contract(ram: bytes) -> dict[str, object]:
    base = VIDEO_DISK_ACTOR_DATA
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
        "current_script_slot": ram[base + CURRENT_SCRIPT_SLOT_OFFSET],
        "current_event_slot": ram[base + CURRENT_EVENT_SLOT_OFFSET],
    }


def _validate_field_contract(ram: bytes) -> None:
    field_id = struct.unpack_from("<I", ram, GAME_SCENE_MAP)[0] & 0x0FFF
    if field_id != EXPECTED_FIELD:
        raise VideoDiskStateError("captured state is not resident field 376")
    if struct.unpack_from("<I", ram, FIELD_NUM_ACTORS)[0] != EXPECTED_ACTOR_COUNT:
        raise VideoDiskStateError("field actor count drifted")
    if struct.unpack_from("<I", ram, FIELD_ACTORS)[0] != FIELD_ACTOR_ARRAY_POINTER:
        raise VideoDiskStateError("field actor-array pointer drifted")
    if (
        struct.unpack_from("<I", ram, FIELD_PLAYER_ACTOR_INDEX)[0]
        != EXPECTED_PLAYER_INDEX
    ):
        raise VideoDiskStateError("player entity index drifted")

    player_pointer = struct.unpack_from(
        "<I",
        ram,
        PLAYER_FIELD_ACTOR + FIELD_ACTOR_SCRIPT_ENTITY_POINTER_OFFSET,
    )[0]
    if player_pointer != PLAYER_ACTOR_DATA_POINTER:
        raise VideoDiskStateError("player ActorData pointer drifted")
    player_position = struct.unpack_from(
        "<3i", ram, PLAYER_ACTOR_DATA + POSITION_X_OFFSET
    )
    player_triangle = struct.unpack_from(
        "<h", ram, PLAYER_ACTOR_DATA + TRIANGLE_OFFSET
    )[0]
    player_yaw = (
        struct.unpack_from("<H", ram, PLAYER_ACTOR_DATA + ROTATION_Y_OFFSET)[0]
        & 0x0FFF
    )
    if (
        player_position != EXPECTED_PLAYER_POSITION
        or player_triangle != EXPECTED_PLAYER_TRIANGLE
        or player_yaw != EXPECTED_PLAYER_YAW
    ):
        raise VideoDiskStateError(
            "player no longer matches the captured video-disk dead-zone stance"
        )

    disk_pointer = struct.unpack_from(
        "<I",
        ram,
        VIDEO_DISK_FIELD_ACTOR + FIELD_ACTOR_SCRIPT_ENTITY_POINTER_OFFSET,
    )[0]
    if disk_pointer != VIDEO_DISK_ACTOR_DATA_POINTER:
        raise VideoDiskStateError("entity-26 ActorData pointer drifted")


def prepare_state(
    state: bytes,
    *,
    old_script: bytes,
    new_script: bytes,
    zstd: _Zstd,
) -> tuple[bytes, dict[str, object]]:
    if _sha256(state) != MIGRATED_STATE_SHA256:
        raise VideoDiskStateError("migrated QA state hash drifted")
    if len(OLD_CUE_PATH) != len(NEW_CUE_PATH):
        raise VideoDiskStateError("isolated profile CUE paths are not equal length")
    if state.count(NEW_CUE_PATH) != 1 or state.count(OLD_CUE_PATH) != 0:
        raise VideoDiskStateError(
            "migrated QA state does not contain only its exact isolated CUE path"
        )
    if (len(old_script), _sha256(old_script)) != (
        SCRIPT_SIZE,
        OLD_SCRIPT_SHA256,
    ):
        raise VideoDiskStateError("old field-376 script pin drifted")
    if (len(new_script), _sha256(new_script)) != (
        SCRIPT_SIZE,
        NEW_SCRIPT_SHA256,
    ):
        raise VideoDiskStateError("new field-376 script pin drifted")
    if _script_delta(old_script, new_script) != SCRIPT_DIFFS:
        raise VideoDiskStateError("field-376 script delta is not exact")

    payload, frame_start = _unpack_state(state, zstd)
    ram_payload_offset = _psx_ram_offset(payload)
    if ram_payload_offset != EXPECTED_RAM_PAYLOAD_OFFSET:
        raise VideoDiskStateError(
            f"serialized RAM starts at 0x{ram_payload_offset:X}, expected "
            f"0x{EXPECTED_RAM_PAYLOAD_OFFSET:X}"
        )
    ram = payload[ram_payload_offset : ram_payload_offset + RAM_SIZE]
    if len(ram) != RAM_SIZE:
        raise VideoDiskStateError("serialized PSX RAM is incomplete")
    if payload.count(old_script) != 1 or ram.count(old_script) != 1:
        raise VideoDiskStateError(
            "old field-376 script must occur once inside serialized RAM"
        )
    if payload.count(new_script) != 0:
        raise VideoDiskStateError("new field-376 script is already resident")
    if (
        ram.find(old_script) != EXPECTED_SCRIPT_RAM_OFFSET
        or payload.find(old_script) != EXPECTED_SCRIPT_PAYLOAD_OFFSET
    ):
        raise VideoDiskStateError(
            "resident field-376 script is not at its audited address"
        )
    if (
        struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0]
        != EXPECTED_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA)[0]
        != EXPECTED_VM_SCRIPT_GUEST_POINTER
    ):
        raise VideoDiskStateError("live field-script pointers drifted")

    _validate_field_contract(ram)
    before_actor = _read_actor_contract(ram)
    expected_before_actor = {
        "flags0": EXPECTED_FLAGS0,
        "flags4": EXPECTED_FLAGS4,
        "triangle": EXPECTED_TRIANGLE,
        "bounds": EXPECTED_OLD_BOUNDS,
        "position": EXPECTED_OLD_POSITION,
        "touched_actor": EXPECTED_TOUCHED_ACTOR,
        "current_script_pc": EXPECTED_IDLE_PC,
        "current_script_slot": EXPECTED_CURRENT_SCRIPT_SLOT,
        "current_event_slot": EXPECTED_CURRENT_EVENT_SLOT,
    }
    if before_actor != expected_before_actor:
        raise VideoDiskStateError(
            f"entity-26 live initializer state drifted: {before_actor}"
        )

    patched_payload = bytearray(payload)
    patched_payload[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET :
        EXPECTED_SCRIPT_PAYLOAD_OFFSET + SCRIPT_SIZE
    ] = new_script
    actor_payload = ram_payload_offset + VIDEO_DISK_ACTOR_DATA
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
    _validate_field_contract(verified_ram)
    after_actor = _read_actor_contract(verified_ram)
    expected_after_actor = {
        **expected_before_actor,
        "bounds": EXPECTED_NEW_BOUNDS,
        "position": EXPECTED_NEW_POSITION,
    }
    if after_actor != expected_after_actor:
        raise VideoDiskStateError(
            f"entity-26 live patched state is wrong: {after_actor}"
        )
    if (
        bytes(patched_payload).count(old_script) != 0
        or bytes(patched_payload).count(new_script) != 1
    ):
        raise VideoDiskStateError(
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
        raise VideoDiskStateError(
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
        raise VideoDiskStateError(
            "recompressed video-disk state did not round-trip exactly"
        )
    if result.count(NEW_CUE_PATH) != 1 or result.count(OLD_CUE_PATH) != 0:
        raise VideoDiskStateError("video-disk patch changed the isolated CUE path")

    return result, {
        "source_sha256": _sha256(state),
        "output_sha256": _sha256(result),
        "source_size": len(state),
        "output_size": len(result),
        "payload_size": len(payload),
        "payload_sha256": _sha256(round_trip_payload),
        "ram_payload_offset": f"0x{ram_payload_offset:X}",
        "script_ram_offset": f"0x{EXPECTED_SCRIPT_RAM_OFFSET:X}",
        "script_payload_offset": f"0x{EXPECTED_SCRIPT_PAYLOAD_OFFSET:X}",
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
            / "vta_stage"
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
            / "vda_stage"
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
            / "disk_bounds_runtime_qa_20260815"
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
            raise VideoDiskStateError("source and output paths must differ")
        for path, label in (
            (source, "source state"),
            (args.old_script.resolve(), "old script"),
            (args.new_script.resolve(), "new script"),
            (args.zstd.resolve(), "zstd library"),
        ):
            if not path.is_file():
                raise VideoDiskStateError(f"{label} is missing: {path}")
        if output.exists():
            raise VideoDiskStateError(
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
    except (OSError, StateMigrationError, VideoDiskStateError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
