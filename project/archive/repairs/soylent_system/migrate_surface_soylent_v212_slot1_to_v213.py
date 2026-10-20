#!/usr/bin/env python3
"""Create a validated V213 candidate from the audited V212 Slot 1.

The captured state is already resident in field 550.  This fail-closed helper
updates the mounted CUE, resident archive table, equal-length ATEL/dialogue
components, and queues retired entity 4's new hidden terminal initializer for
the normal field scheduler.  It never writes the live Slot 1 path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
from typing import Protocol, Sequence


if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import tools.migrate_duckstation_disc_state as media_migration  # noqa: E402
from tools.xgdeathblows import GAMESTATE_SIZE  # noqa: E402
from tools.xgscript import AtelScript  # noqa: E402
from work.read_duckstation_runtime import (  # noqa: E402
    FIELD_ACTORS,
    FIELD_ACTOR_DATA_POINTER,
    FIELD_ACTOR_STRIDE,
    FIELD_CUR_SCRIPT_FILE,
    FIELD_NUM_ACTORS,
    FIELD_SCRIPT_VM_CUR_SCRIPT_DATA,
    GAME_STATE,
    RAM_SIZE,
    _psx_ram_offset,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIVE_SLOT1 = (PROJECT_ROOT / "emulator_data" / "SLUS-00669_1.sav").resolve()

SOURCE_STATE_SHA256 = (
    "3493bff36abf088a0d80f7e71087854f7fe99262b5f25ed647ddfd9ed0257b49"
)
SOURCE_PAYLOAD_SHA256 = (
    "ae964f054bead2183b6a85c96b26bc450eb65fe45dbbf0516f61589796f739a6"
)
OLD_DISC_SHA256 = (
    "d98297809775b908ab8b4f6012ebdb102f18e7bdfd11157fcb69ab138a890d0d"
)
NEW_DISC_SHA256 = (
    "9a2d781630e265af0f51ca01a801372d2766018f79a0bb5637818298c2b7e684"
)
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v212.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v213.cue"

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = (
    "a42d81a5486a91ed0b6053f945fcf3575b98044f5df7158148b0284c84897ece"
)
NEW_ARCHIVE_TABLE_SHA256 = (
    "fae7429ff90b782c6beab4b43056012487af6b611db17fcb2be1b43a7111095f"
)
ARCHIVE_TABLE_DIFFS = (
    (0x2E86, 0x38, 0xB4),
    (0x2E87, 0x31, 0x30),
)

SCRIPT_SIZE = 5_414
OLD_SCRIPT_SHA256 = (
    "fa81dbe4ef893818c0fa46d2bb3580ffe56b38edc8825146c69a598a06e02302"
)
NEW_SCRIPT_SHA256 = (
    "13da59f3ed7a31e67e411bc695d2e6b991f68cfcf482f002478be0505b3765b5"
)
DIALOGUE_SIZE = 6_056
OLD_DIALOGUE_SHA256 = (
    "7cfd5d8e7ea0db798791b420890cc120c8f9a8593064623407bde8b4abdbdd97"
)
NEW_DIALOGUE_SHA256 = (
    "3c1f8cc6906384c6a9a0bb23ee5710bde6a524f656baa4b6ac8c49659d51bc4e"
)

EXPECTED_FRAME_START = 0xD7EB
EXPECTED_PAYLOAD_SIZE = 3_819_109
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
EXPECTED_SCRIPT_PAYLOAD_OFFSET = 0x10CD56
EXPECTED_DIALOGUE_PAYLOAD_OFFSET = 0x10E2AE
EXPECTED_SCRIPT_RAM_OFFSET = 0x10B2F4
EXPECTED_SCRIPT_GUEST_POINTER = 0x8010B2F4
EXPECTED_VM_SCRIPT_GUEST_POINTER = 0x8010B978

GAME_SCENE_MAP = 0x04F34C
EXPECTED_FIELD = 550
EXPECTED_ACTOR_COUNT = 38
SCRIPT_ENTITY_COUNT = 24
EXPECTED_ACTOR_ARRAY_GUEST_POINTER = 0x80113B24
TERMINAL_ENTITY = 4
EXPECTED_TERMINAL_ACTOR_DATA = 0x114FB4
ACTOR_RECORD_STATUS_OFFSET = 0x58
ACTOR_DATA_FLAGS_OFFSET = 0x04
ACTOR_SCRIPT_SLOT_OFFSET = 0x8C
ACTOR_SCRIPT_SLOT_SIZE = 8
ACTOR_SCRIPT_SLOT_COUNT = 8
ACTOR_CURRENT_PC_OFFSET = 0xCC
TERMINAL_INIT_PC = 0x054B
TERMINAL_INIT_STOP_PC = 0x0567
TERMINAL_ACTION_PC = 0x0568
TERMINAL_CAVITY_END_PC = 0x0649
OLD_TERMINAL_RECORD_STATUS = bytes.fromhex("E0 01")
NEW_TERMINAL_RECORD_STATUS = bytes.fromhex("60 02")
OLD_TERMINAL_ACTOR_FLAGS = bytes.fromhex("00 08 00 04")
NEW_TERMINAL_ACTOR_FLAGS = bytes.fromhex("00 08 00 00")
OLD_TERMINAL_SLOT0 = bytes.fromhex("8C 06 00 FF FF FF 3C 00")
NEW_TERMINAL_SLOT0 = bytes.fromhex("4B 05 00 00 FF FF 1C 00")
EXPECTED_GAMESTATE_SHA256 = (
    "542228b209c4f86b5b4bb48ea720ca916864f81e1138a6a16b035227d59b1222"
)

EXPECTED_OUTPUT_SIZE = 1_453_925
EXPECTED_OUTPUT_SHA256 = (
    "86b337dd0b63b321e12c31949247ccbcce719d58c80cd40137c595c7c270b7b6"
)


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output whenever a pinned V212/V213 contract drifts."""


class _ZstdLike(Protocol):
    def frame_size(self, frame: bytes) -> int: ...

    def decompress(self, frame: bytes) -> bytes: ...

    def compress(self, payload: bytes) -> bytes: ...


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _diff_triplets(before: bytes, after: bytes) -> tuple[tuple[int, int, int], ...]:
    if len(before) != len(after):
        raise SurfaceSlotMigrationError("Compared byte strings have different lengths")
    return tuple(
        (offset, old, new)
        for offset, (old, new) in enumerate(zip(before, after))
        if old != new
    )


def _diff_offsets(before: bytes, after: bytes) -> tuple[int, ...]:
    return tuple(offset for offset, _old, _new in _diff_triplets(before, after))


def _unpack_state(
    state: bytes,
    zstd: _ZstdLike,
) -> tuple[bytes, int, bytes]:
    if (
        len(state) < media_migration.DUCKSTATION_STATE_HEADER_SIZE
        or state[:4] != media_migration.DUCKSTATION_STATE_MAGIC
    ):
        raise SurfaceSlotMigrationError("Input is not a supported DuckStation state")
    compression, compressed_size, payload_size, frame_start = struct.unpack_from(
        "<IIII",
        state,
        media_migration.DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    )
    if compression != media_migration.DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise SurfaceSlotMigrationError("DuckStation payload is not Zstandard-compressed")
    frame = state[frame_start : frame_start + compressed_size]
    if frame_start + compressed_size != len(state):
        raise SurfaceSlotMigrationError("DuckStation compressed frame span is invalid")
    if zstd.frame_size(frame) != compressed_size:
        raise SurfaceSlotMigrationError("DuckStation compressed frame size drifted")
    payload = zstd.decompress(frame)
    if len(payload) != payload_size:
        raise SurfaceSlotMigrationError("DuckStation payload-size header drifted")
    return payload, frame_start, state[:frame_start]


def _pack_state(prefix: bytes, payload: bytes, zstd: _ZstdLike) -> bytes:
    compressed = zstd.compress(payload)
    result_prefix = bytearray(prefix)
    struct.pack_into(
        "<I",
        result_prefix,
        media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        len(compressed),
    )
    return bytes(result_prefix) + compressed


def _expected_prefix(source_prefix: bytes, *, compressed_size: int) -> bytes:
    old = OLD_CUE_NAME.encode("ascii")
    new = NEW_CUE_NAME.encode("ascii")
    if len(old) != len(new) or source_prefix.count(old) != 1:
        raise SurfaceSlotMigrationError("Source prefix CUE-name contract drifted")
    expected = bytearray(source_prefix.replace(old, new))
    struct.pack_into(
        "<I",
        expected,
        media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        compressed_size,
    )
    return bytes(expected)


def _ram_from_payload(payload: bytes) -> tuple[int, bytes]:
    try:
        offset = _psx_ram_offset(payload)
    except SystemExit as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc
    if offset != EXPECTED_RAM_PAYLOAD_OFFSET:
        raise SurfaceSlotMigrationError("Serialized RAM payload offset drifted")
    ram = payload[offset : offset + RAM_SIZE]
    if len(ram) != RAM_SIZE:
        raise SurfaceSlotMigrationError("Serialized PSX RAM is incomplete")
    return offset, ram


def _guest_ram_offset(pointer: int, label: str) -> int:
    offset = pointer & 0x1FFFFFFF
    if offset >= RAM_SIZE:
        raise SurfaceSlotMigrationError(f"{label} pointer is outside PSX RAM")
    return offset


def _validate_resources(
    *,
    old_disc: Path,
    new_disc: Path,
    old_script: bytes,
    new_script: bytes,
    old_dialogue: bytes,
    new_dialogue: bytes,
) -> tuple[bytes, bytes]:
    if _file_sha256(old_disc) != OLD_DISC_SHA256:
        raise SurfaceSlotMigrationError("V212 disc identity drifted")
    if _file_sha256(new_disc) != NEW_DISC_SHA256:
        raise SurfaceSlotMigrationError("V213 disc identity drifted")
    expected = (
        (old_script, SCRIPT_SIZE, OLD_SCRIPT_SHA256, "V212 script"),
        (new_script, SCRIPT_SIZE, NEW_SCRIPT_SHA256, "V213 script"),
        (old_dialogue, DIALOGUE_SIZE, OLD_DIALOGUE_SHA256, "V212 dialogue"),
        (new_dialogue, DIALOGUE_SIZE, NEW_DIALOGUE_SHA256, "V213 dialogue"),
    )
    for data, size, sha256, label in expected:
        if (len(data), _sha256(data)) != (size, sha256):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")

    old_editor = AtelScript(old_script)
    new_editor = AtelScript(new_script)
    if (
        old_editor.entity_count != 24
        or new_editor.entity_count != old_editor.entity_count
        or new_editor.bytecode_size != old_editor.bytecode_size
        or old_editor.get_script_pointer(TERMINAL_ENTITY, 0) != 0x068C
        or old_editor.get_script_pointer(TERMINAL_ENTITY, 2) != 0x068C
        or new_editor.get_script_pointer(TERMINAL_ENTITY, 0) != TERMINAL_INIT_PC
        or new_editor.get_script_pointer(TERMINAL_ENTITY, 2) != TERMINAL_ACTION_PC
        or new_editor.bytecode[TERMINAL_INIT_STOP_PC] != 0
    ):
        raise SurfaceSlotMigrationError("Field-550 terminal ATEL topology drifted")
    changed_script_offsets = _diff_offsets(old_script, new_script)
    allowed_pointer_offsets = {0x184, 0x185, 0x188, 0x189}
    cavity_start = new_editor.bytecode_offset + TERMINAL_INIT_PC
    cavity_end = new_editor.bytecode_offset + TERMINAL_CAVITY_END_PC
    if any(
        offset not in allowed_pointer_offsets
        and not cavity_start <= offset < cavity_end
        for offset in changed_script_offsets
    ):
        raise SurfaceSlotMigrationError("V213 script changed outside e4's retired cavity")

    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    if (
        (len(old_table), _sha256(old_table))
        != (ARCHIVE_TABLE_SIZE, OLD_ARCHIVE_TABLE_SHA256)
        or (len(new_table), _sha256(new_table))
        != (ARCHIVE_TABLE_SIZE, NEW_ARCHIVE_TABLE_SHA256)
        or _diff_triplets(old_table, new_table) != ARCHIVE_TABLE_DIFFS
    ):
        raise SurfaceSlotMigrationError("V212/V213 archive-table contract drifted")
    return old_table, new_table


def _validate_source_runtime(
    payload: bytes,
    *,
    old_script: bytes,
    new_script: bytes,
    old_dialogue: bytes,
    new_dialogue: bytes,
) -> dict[str, int | bytes]:
    if len(payload) != EXPECTED_PAYLOAD_SIZE:
        raise SurfaceSlotMigrationError("V212 payload size drifted")
    ram_payload_offset, ram = _ram_from_payload(payload)
    if (
        payload.count(old_script) != 1
        or payload.find(old_script) != EXPECTED_SCRIPT_PAYLOAD_OFFSET
        or payload.count(new_script) != 0
        or payload.count(old_dialogue) != 1
        or payload.find(old_dialogue) != EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        or payload.count(new_dialogue) != 0
    ):
        raise SurfaceSlotMigrationError("Resident field-550 component identity drifted")
    if (
        struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0]
        != EXPECTED_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA)[0]
        != EXPECTED_VM_SCRIPT_GUEST_POINTER
        or (struct.unpack_from("<I", ram, GAME_SCENE_MAP)[0] & 0x0FFF)
        != EXPECTED_FIELD
        or struct.unpack_from("<I", ram, FIELD_NUM_ACTORS)[0]
        != EXPECTED_ACTOR_COUNT
        or struct.unpack_from("<I", ram, FIELD_ACTORS)[0]
        != EXPECTED_ACTOR_ARRAY_GUEST_POINTER
    ):
        raise SurfaceSlotMigrationError("Resident field-550 runtime topology drifted")

    actor_array = _guest_ram_offset(
        EXPECTED_ACTOR_ARRAY_GUEST_POINTER, "field actor array"
    )
    terminal_record = actor_array + TERMINAL_ENTITY * FIELD_ACTOR_STRIDE
    terminal_actor_data = _guest_ram_offset(
        struct.unpack_from(
            "<I", ram, terminal_record + FIELD_ACTOR_DATA_POINTER
        )[0],
        "terminal ActorData",
    )
    if terminal_actor_data != EXPECTED_TERMINAL_ACTOR_DATA:
        raise SurfaceSlotMigrationError("Terminal ActorData pointer drifted")
    checks = (
        (
            terminal_record + ACTOR_RECORD_STATUS_OFFSET,
            OLD_TERMINAL_RECORD_STATUS,
            "terminal record status",
        ),
        (
            terminal_actor_data + ACTOR_DATA_FLAGS_OFFSET,
            OLD_TERMINAL_ACTOR_FLAGS,
            "terminal actor flags",
        ),
        (
            terminal_actor_data + ACTOR_SCRIPT_SLOT_OFFSET,
            OLD_TERMINAL_SLOT0,
            "terminal script slot 0",
        ),
    )
    for offset, expected, label in checks:
        if ram[offset : offset + len(expected)] != expected:
            raise SurfaceSlotMigrationError(f"V212 {label} drifted")

    # No actor or queued script may already be executing bytes that V213 turns
    # into the terminal initializer/action cavity.
    for entity in range(SCRIPT_ENTITY_COUNT):
        record = actor_array + entity * FIELD_ACTOR_STRIDE
        actor_data = _guest_ram_offset(
            struct.unpack_from("<I", ram, record + FIELD_ACTOR_DATA_POINTER)[0],
            f"e{entity} ActorData",
        )
        pcs = [struct.unpack_from("<H", ram, actor_data + ACTOR_CURRENT_PC_OFFSET)[0]]
        pcs.extend(
            struct.unpack_from(
                "<H",
                ram,
                actor_data + ACTOR_SCRIPT_SLOT_OFFSET + slot * ACTOR_SCRIPT_SLOT_SIZE,
            )[0]
            for slot in range(ACTOR_SCRIPT_SLOT_COUNT)
        )
        if any(TERMINAL_INIT_PC <= pc < TERMINAL_CAVITY_END_PC for pc in pcs):
            raise SurfaceSlotMigrationError(
                f"Actor e{entity} is already executing the changed terminal cavity"
            )
    gamestate = bytes(ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE])
    if _sha256(gamestate) != EXPECTED_GAMESTATE_SHA256:
        raise SurfaceSlotMigrationError("V212 GameState identity drifted")
    return {
        "ram_payload_offset": ram_payload_offset,
        "terminal_record": terminal_record,
        "terminal_actor_data": terminal_actor_data,
        "gamestate": gamestate,
    }


def migrate_v212_slot1_to_v213(
    state: bytes,
    *,
    old_disc: Path,
    new_disc: Path,
    old_script: bytes,
    new_script: bytes,
    old_dialogue: bytes,
    new_dialogue: bytes,
    zstd: _ZstdLike,
) -> tuple[bytes, dict[str, object]]:
    """Return a separately writable, fully validated V213 state candidate."""

    source_sha256 = _sha256(state)
    if source_sha256 != SOURCE_STATE_SHA256:
        raise SurfaceSlotMigrationError(
            f"Source Slot 1 SHA-256 is {source_sha256}, expected {SOURCE_STATE_SHA256}"
        )
    old_name = OLD_CUE_NAME.encode("ascii")
    new_name = NEW_CUE_NAME.encode("ascii")
    if state.count(old_name) != 1 or state.count(new_name) != 0:
        raise SurfaceSlotMigrationError("Source CUE identity drifted")
    old_table, new_table = _validate_resources(
        old_disc=old_disc,
        new_disc=new_disc,
        old_script=old_script,
        new_script=new_script,
        old_dialogue=old_dialogue,
        new_dialogue=new_dialogue,
    )
    source_payload, frame_start, source_prefix = _unpack_state(state, zstd)
    if (
        frame_start != EXPECTED_FRAME_START
        or _sha256(source_payload) != SOURCE_PAYLOAD_SHA256
    ):
        raise SurfaceSlotMigrationError("Source payload identity drifted")
    runtime = _validate_source_runtime(
        source_payload,
        old_script=old_script,
        new_script=new_script,
        old_dialogue=old_dialogue,
        new_dialogue=new_dialogue,
    )
    table_offset, volatile = media_migration._find_resident_archive_table(
        source_payload, old_table
    )
    if table_offset != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET or volatile != 0:
        raise SurfaceSlotMigrationError("Resident V212 archive table drifted")

    try:
        media_state, media_report = media_migration.migrate_state(
            state,
            old_disc=old_disc,
            new_disc=new_disc,
            old_cue_name=OLD_CUE_NAME,
            new_cue_name=NEW_CUE_NAME,
            zstd=zstd,
        )
    except media_migration.StateMigrationError as exc:
        raise SurfaceSlotMigrationError(f"Media migration failed: {exc}") from exc
    media_payload, media_frame_start, media_prefix = _unpack_state(media_state, zstd)
    if (
        media_frame_start != frame_start
        or media_report["resident_table_offset"] != table_offset
        or media_report["bytes_changed_in_payload"] != len(ARCHIVE_TABLE_DIFFS)
        or media_payload[table_offset : table_offset + ARCHIVE_TABLE_SIZE]
        != new_table
        or media_payload[
            EXPECTED_SCRIPT_PAYLOAD_OFFSET :
            EXPECTED_SCRIPT_PAYLOAD_OFFSET + SCRIPT_SIZE
        ]
        != old_script
        or media_payload[
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET :
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE
        ]
        != old_dialogue
        or media_prefix
        != _expected_prefix(
            source_prefix,
            compressed_size=len(media_state) - frame_start,
        )
    ):
        raise SurfaceSlotMigrationError("Media migration changed unexpected state data")

    final_payload = bytearray(media_payload)
    final_payload[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET :
        EXPECTED_SCRIPT_PAYLOAD_OFFSET + SCRIPT_SIZE
    ] = new_script
    final_payload[
        EXPECTED_DIALOGUE_PAYLOAD_OFFSET :
        EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE
    ] = new_dialogue
    ram_payload_offset = int(runtime["ram_payload_offset"])
    terminal_record = int(runtime["terminal_record"])
    terminal_actor_data = int(runtime["terminal_actor_data"])
    runtime_patches = (
        (
            ram_payload_offset + terminal_record + ACTOR_RECORD_STATUS_OFFSET,
            OLD_TERMINAL_RECORD_STATUS,
            NEW_TERMINAL_RECORD_STATUS,
        ),
        (
            ram_payload_offset + terminal_actor_data + ACTOR_DATA_FLAGS_OFFSET,
            OLD_TERMINAL_ACTOR_FLAGS,
            NEW_TERMINAL_ACTOR_FLAGS,
        ),
        (
            ram_payload_offset + terminal_actor_data + ACTOR_SCRIPT_SLOT_OFFSET,
            OLD_TERMINAL_SLOT0,
            NEW_TERMINAL_SLOT0,
        ),
    )
    for offset, old, new in runtime_patches:
        if final_payload[offset : offset + len(old)] != old:
            raise SurfaceSlotMigrationError("Terminal scheduler patch source drifted")
        final_payload[offset : offset + len(new)] = new
    final_payload_bytes = bytes(final_payload)

    expected_offsets = {
        *(table_offset + offset for offset, _old, _new in ARCHIVE_TABLE_DIFFS),
        *(
            EXPECTED_SCRIPT_PAYLOAD_OFFSET + offset
            for offset in _diff_offsets(old_script, new_script)
        ),
        *(
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET + offset
            for offset in _diff_offsets(old_dialogue, new_dialogue)
        ),
    }
    for offset, old, new in runtime_patches:
        expected_offsets.update(
            offset + relative
            for relative, (before, after) in enumerate(zip(old, new))
            if before != after
        )
    actual_offsets = _diff_offsets(source_payload, final_payload_bytes)
    if actual_offsets != tuple(sorted(expected_offsets)):
        raise SurfaceSlotMigrationError("Combined migration changed non-whitelisted bytes")

    result = _pack_state(media_prefix, final_payload_bytes, zstd)
    verified_payload, verified_frame_start, verified_prefix = _unpack_state(
        result, zstd
    )
    if (
        verified_payload != final_payload_bytes
        or verified_frame_start != frame_start
        or verified_prefix
        != _expected_prefix(
            source_prefix,
            compressed_size=len(result) - frame_start,
        )
        or result.count(old_name) != 0
        or result.count(new_name) != 1
    ):
        raise SurfaceSlotMigrationError("Final V213 state failed exact round trip")
    result_ram_offset, result_ram = _ram_from_payload(verified_payload)
    if (
        result_ram_offset != ram_payload_offset
        or bytes(result_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE])
        != runtime["gamestate"]
        or verified_payload.count(old_script) != 0
        or verified_payload.count(new_script) != 1
        or verified_payload.count(old_dialogue) != 0
        or verified_payload.count(new_dialogue) != 1
    ):
        raise SurfaceSlotMigrationError("V213 gameplay/component preservation failed")

    output_sha256 = _sha256(result)
    if EXPECTED_OUTPUT_SIZE is not None and len(result) != EXPECTED_OUTPUT_SIZE:
        raise SurfaceSlotMigrationError("V213 candidate size drifted")
    if EXPECTED_OUTPUT_SHA256 is not None and output_sha256 != EXPECTED_OUTPUT_SHA256:
        raise SurfaceSlotMigrationError("V213 candidate identity drifted")
    return result, {
        "source_sha256": source_sha256,
        "output_sha256": output_sha256,
        "source_size": len(state),
        "output_size": len(result),
        "field": EXPECTED_FIELD,
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "frame_offset": f"0x{frame_start:X}",
        "payload_size": len(verified_payload),
        "archive_table_payload_offset": f"0x{table_offset:X}",
        "script_payload_offset": f"0x{EXPECTED_SCRIPT_PAYLOAD_OFFSET:X}",
        "dialogue_payload_offset": f"0x{EXPECTED_DIALOGUE_PAYLOAD_OFFSET:X}",
        "payload_bytes_changed": len(actual_offsets),
        "script_bytes_changed": len(_diff_offsets(old_script, new_script)),
        "dialogue_bytes_changed": len(_diff_offsets(old_dialogue, new_dialogue)),
        "terminal_runtime_bytes_changed": sum(
            before != after
            for _offset, old, new in runtime_patches
            for before, after in zip(old, new)
        ),
        "terminal_initializer_queued": True,
        "gamestate_preserved": True,
        "round_trip_verified": True,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--old-disc", type=Path, required=True)
    parser.add_argument("--new-disc", type=Path, required=True)
    parser.add_argument("--old-script", type=Path, required=True)
    parser.add_argument("--new-script", type=Path, required=True)
    parser.add_argument("--old-dialogue", type=Path, required=True)
    parser.add_argument("--new-dialogue", type=Path, required=True)
    parser.add_argument("--zstd", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        source = args.source.resolve()
        output = args.output.resolve()
        paths = {
            "old_disc": args.old_disc.resolve(),
            "new_disc": args.new_disc.resolve(),
            "old_script": args.old_script.resolve(),
            "new_script": args.new_script.resolve(),
            "old_dialogue": args.old_dialogue.resolve(),
            "new_dialogue": args.new_dialogue.resolve(),
            "zstd": args.zstd.resolve(),
        }
        if not source.is_file():
            raise SurfaceSlotMigrationError(f"Source state does not exist: {source}")
        for label, path in paths.items():
            if not path.is_file():
                raise SurfaceSlotMigrationError(f"{label} does not exist: {path}")
        if output in (source, LIVE_SLOT1):
            raise SurfaceSlotMigrationError(
                "Output must be separate and may not be the live Slot 1"
            )
        if output.exists():
            raise SurfaceSlotMigrationError(
                f"Refusing to overwrite existing output: {output}"
            )
        result, report = migrate_v212_slot1_to_v213(
            source.read_bytes(),
            old_disc=paths["old_disc"],
            new_disc=paths["new_disc"],
            old_script=paths["old_script"].read_bytes(),
            new_script=paths["new_script"].read_bytes(),
            old_dialogue=paths["old_dialogue"].read_bytes(),
            new_dialogue=paths["new_dialogue"].read_bytes(),
            zstd=media_migration._Zstd(paths["zstd"]),
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        if output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Written V213 candidate changed on disk")
        print(f"Wrote validated V213 candidate: {output}")
        print(json.dumps(report, indent=2, sort_keys=True))
        print(
            "The live Slot 1 was not modified. Install this candidate only "
            "after DuckStation is fully closed."
        )
        return 0
    except (
        OSError,
        ValueError,
        media_migration.StateMigrationError,
        SurfaceSlotMigrationError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
