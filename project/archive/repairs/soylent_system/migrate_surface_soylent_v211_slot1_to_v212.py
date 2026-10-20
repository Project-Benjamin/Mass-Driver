#!/usr/bin/env python3
"""Create a validated V212 candidate from the audited V211 Slot 1.

The captured state is resident in field 550, so mounting the rebuilt disc alone
would leave the old time-sliced exit gate in RAM.  This one-state migrator
updates the mounted CUE, resident archive table, and equal-length field-550 ATEL
script while preserving all gameplay state.  It refuses the live Slot 1 path;
installation remains a separate operation after DuckStation is fully closed.
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
    FIELD_SCRIPT_VM_CUR_ACTOR,
    FIELD_SCRIPT_VM_CUR_SCRIPT_DATA,
    GAME_STATE,
    RAM_SIZE,
    _psx_ram_offset,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIVE_SLOT1 = (PROJECT_ROOT / "emulator_data" / "SLUS-00669_1.sav").resolve()

SOURCE_STATE_SHA256 = (
    "a2bd6b8bff5d88be81549f876db5b40bb6da5217d84ea4e162f7f16c8028ff2f"
)
SOURCE_PAYLOAD_SHA256 = (
    "9e9fe09b5974595fd09304496c5b172410dc7bf7fdfb58e0b7740071daafe693"
)
OLD_DISC_SHA256 = (
    "0b23ae64ccc0aececbd3cbb84b8c5486b8878884e048d341d4ab36662d0f5369"
)
NEW_DISC_SHA256 = (
    "d98297809775b908ab8b4f6012ebdb102f18e7bdfd11157fcb69ab138a890d0d"
)
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v211.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v212.cue"

OLD_ARCHIVE_TABLE_SHA256 = (
    "1ad4bf0a0e0994db9313040dd737d964c48065da7d405df9f55aca3b2ff67734"
)
NEW_ARCHIVE_TABLE_SHA256 = (
    "a42d81a5486a91ed0b6053f945fcf3575b98044f5df7158148b0284c84897ece"
)
SOURCE_RESIDENT_TABLE_SHA256 = (
    "be995dfb6e59f3d7d9626d939d7ab38b3bcacd0cae1db4a7a417ea324ebfa94c"
)
ARCHIVE_TABLE_SIZE = 0x8000
DISC_TABLE_DIFFS = ((0x2E86, 0x20, 0x38),)
SOURCE_TABLE_TO_NEW_DIFFS = (
    (0x2E86, 0x20, 0x38),
    (0x7FFF, 0xE0, 0x00),
)

OLD_SCRIPT_SHA256 = (
    "8943d013711b30b4bd4cb68fd302ca7393be926337bca761b82a6461753e87c2"
)
NEW_SCRIPT_SHA256 = (
    "fa81dbe4ef893818c0fa46d2bb3580ffe56b38edc8825146c69a598a06e02302"
)
SCRIPT_SIZE = 5_414
SCRIPT_ENTITY_COUNT = 24
SCRIPT_ENTRY_TABLE_OFFSET = 0x84
SCRIPT_ENTRY_SIZE = 0x40
SCRIPT_BYTECODE_OFFSET = 0x684
SCRIPT_BYTECODE_SIZE = 0xEA2
EXIT_ENTITY = 17
EXIT_ACTION_SLOT = 2
EXIT_GATE_PC = 0x0DDB
EXIT_GATE_END_PC = 0x0EA2
OLD_SCRATCH_WORD = bytes.fromhex("C6 07")
NEW_SCRATCH_WORD = bytes.fromhex("D0 07")
SCRIPT_DIFF_OFFSETS = (
    0x1460,
    0x1466,
    0x146C,
    0x147C,
    0x1482,
    0x1488,
    0x1490,
    0x1498,
    0x14A0,
    0x14A8,
    0x14AE,
    0x14B4,
    0x14BC,
)
SCRIPT_DIFFS = tuple((offset, 0xC6, 0xD0) for offset in SCRIPT_DIFF_OFFSETS)

EXPECTED_FRAME_START = 0xAFAE
EXPECTED_PAYLOAD_SIZE = 3_819_109
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
EXPECTED_SCRIPT_RAM_OFFSET = 0x10B2F4
EXPECTED_SCRIPT_PAYLOAD_OFFSET = 0x10CD56
EXPECTED_SCRIPT_GUEST_POINTER = 0x8010B2F4
EXPECTED_VM_SCRIPT_GUEST_POINTER = 0x8010B978

GAME_SCENE_MAP = 0x04F34C
EXPECTED_FIELD = 550
EXPECTED_ACTOR_COUNT = 38
EXPECTED_ACTOR_ARRAY_GUEST_POINTER = 0x80113B24
ACTOR_CURRENT_PC_OFFSET = 0xCC
ACTOR_CURRENT_SLOT_OFFSET = 0xCE
ACTOR_POSITION_OFFSET = 0x20
ACTOR_TRIANGLE_OFFSET = 0x08
ACTOR_COLLISION_RADIUS_OFFSET = 0x1E
EXPECTED_CURRENT_VM_ACTOR = 0x801170E0
EXPECTED_ACTORS = {
    1: (0x114A8C, 0x015F, 0, 16),
    16: (0x116454, 0x0A55, 0, 8),
    17: (0x11660C, 0x068C, 0, 34),
    19: (0x116A00, 0x0A56, 0, 34),
    23: (0x1170E0, 0x068C, 0, 34),
}
EXPECTED_PLAYER_POSITION = (0, 0, 13_434_800)
EXPECTED_SEAL_POSITION = (0, 0, 16_384_000)
EXPECTED_SEAL_COLLISION_RADIUS = 28
EXPECTED_GAMESTATE_SHA256 = (
    "a3d0f5ac43c8ff8eb466eabfa4abbdce5c6dd0babd0d445f424f9d60a1849add"
)

EXPECTED_OUTPUT_SIZE = 1_435_487
EXPECTED_OUTPUT_SHA256 = (
    "e0e5dc547be87ef615a3b7a78ba7df16f5743cb18030c110609b29feeeb01d4e"
)


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output when any pinned V211/V212 contract drifts."""


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
        raise SurfaceSlotMigrationError(
            f"Compared byte strings have different lengths: {len(before)} != {len(after)}"
        )
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
        raise SurfaceSlotMigrationError(
            "Input is not a supported DuckStation save state"
        )
    compression, compressed_size, payload_size, frame_start = struct.unpack_from(
        "<IIII",
        state,
        media_migration.DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    )
    if compression != media_migration.DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise SurfaceSlotMigrationError(
            "DuckStation state payload is not Zstandard-compressed"
        )
    frame_end = frame_start + compressed_size
    if (
        not media_migration.DUCKSTATION_STATE_HEADER_SIZE <= frame_start < len(state)
        or frame_end != len(state)
    ):
        raise SurfaceSlotMigrationError("DuckStation state frame span is invalid")
    frame = state[frame_start:frame_end]
    if not frame.startswith(media_migration.ZSTD_MAGIC):
        raise SurfaceSlotMigrationError(
            "DuckStation declared payload is not a Zstandard frame"
        )
    if zstd.frame_size(frame) != compressed_size:
        raise SurfaceSlotMigrationError(
            "DuckStation compressed-size header does not match its frame"
        )
    payload = zstd.decompress(frame)
    if len(payload) != payload_size:
        raise SurfaceSlotMigrationError(
            "DuckStation uncompressed-size header does not match its payload"
        )
    return payload, frame_start, state[:frame_start]


def _pack_state(prefix: bytes, payload: bytes, zstd: _ZstdLike) -> bytes:
    compressed = zstd.compress(payload)
    if len(compressed) > 0xFFFFFFFF:
        raise SurfaceSlotMigrationError("Recompressed payload exceeds 32 bits")
    result_prefix = bytearray(prefix)
    struct.pack_into(
        "<I",
        result_prefix,
        media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        len(compressed),
    )
    return bytes(result_prefix) + compressed


def _expected_prefix(source_prefix: bytes, *, compressed_size: int) -> bytes:
    old_name = OLD_CUE_NAME.encode("ascii")
    new_name = NEW_CUE_NAME.encode("ascii")
    if len(old_name) != len(new_name) or source_prefix.count(old_name) != 1:
        raise SurfaceSlotMigrationError("Source prefix CUE-name contract drifted")
    expected = bytearray(source_prefix.replace(old_name, new_name))
    struct.pack_into(
        "<I",
        expected,
        media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        compressed_size,
    )
    return bytes(expected)


def _guest_ram_offset(pointer: int, label: str) -> int:
    address = pointer & 0x1FFFFFFF
    if address >= RAM_SIZE:
        raise SurfaceSlotMigrationError(
            f"{label} pointer 0x{pointer:08X} is outside PSX RAM"
        )
    return address


def _actor_data_pointer(ram: bytes, actor_array: int, entity: int) -> int:
    actor = actor_array + entity * FIELD_ACTOR_STRIDE
    pointer = struct.unpack_from(
        "<I", ram, actor + FIELD_ACTOR_DATA_POINTER
    )[0]
    return _guest_ram_offset(pointer, f"field actor e{entity} ActorData")


def _validate_script_contract(old_script: bytes, new_script: bytes) -> None:
    if (len(old_script), _sha256(old_script)) != (
        SCRIPT_SIZE,
        OLD_SCRIPT_SHA256,
    ):
        raise SurfaceSlotMigrationError("V211 field-550 script identity drifted")
    if (len(new_script), _sha256(new_script)) != (
        SCRIPT_SIZE,
        NEW_SCRIPT_SHA256,
    ):
        raise SurfaceSlotMigrationError("V212 field-550 script identity drifted")
    if _diff_triplets(old_script, new_script) != SCRIPT_DIFFS:
        raise SurfaceSlotMigrationError(
            "Field-550 script delta is not the exact private-scratch repair"
        )
    for label, script in (("V211", old_script), ("V212", new_script)):
        editor = AtelScript(script)
        bytecode_offset = SCRIPT_ENTRY_TABLE_OFFSET + editor.entity_count * SCRIPT_ENTRY_SIZE
        if (
            editor.entity_count != SCRIPT_ENTITY_COUNT
            or bytecode_offset != SCRIPT_BYTECODE_OFFSET
            or len(editor.bytecode) != SCRIPT_BYTECODE_SIZE
            or editor.get_script_pointer(EXIT_ENTITY, EXIT_ACTION_SLOT)
            != EXIT_GATE_PC
        ):
            raise SurfaceSlotMigrationError(f"{label} field-550 ATEL topology drifted")
    if old_script.count(OLD_SCRATCH_WORD) != 77:
        raise SurfaceSlotMigrationError("V211 scratch-word inventory drifted")
    if new_script.count(OLD_SCRATCH_WORD) != 64:
        raise SurfaceSlotMigrationError("V212 retained scratch inventory drifted")
    if old_script.count(NEW_SCRATCH_WORD) != 0:
        raise SurfaceSlotMigrationError("V211 unexpectedly contains the new scratch")
    if new_script.count(NEW_SCRATCH_WORD) != 13:
        raise SurfaceSlotMigrationError("V212 private-scratch inventory drifted")
    gate_start = SCRIPT_BYTECODE_OFFSET + EXIT_GATE_PC
    gate_end = SCRIPT_BYTECODE_OFFSET + EXIT_GATE_END_PC
    if new_script[:gate_start].count(NEW_SCRATCH_WORD) or new_script[
        gate_end:
    ].count(NEW_SCRATCH_WORD):
        raise SurfaceSlotMigrationError("V212 private scratch escaped the exit gate")


def _validate_disc_contract(old_disc: Path, new_disc: Path) -> tuple[bytes, bytes]:
    if _file_sha256(old_disc) != OLD_DISC_SHA256:
        raise SurfaceSlotMigrationError("V211 disc identity drifted")
    if _file_sha256(new_disc) != NEW_DISC_SHA256:
        raise SurfaceSlotMigrationError("V212 disc identity drifted")
    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    if (len(old_table), _sha256(old_table)) != (
        ARCHIVE_TABLE_SIZE,
        OLD_ARCHIVE_TABLE_SHA256,
    ):
        raise SurfaceSlotMigrationError("V211 archive-table identity drifted")
    if (len(new_table), _sha256(new_table)) != (
        ARCHIVE_TABLE_SIZE,
        NEW_ARCHIVE_TABLE_SHA256,
    ):
        raise SurfaceSlotMigrationError("V212 archive-table identity drifted")
    if _diff_triplets(old_table, new_table) != DISC_TABLE_DIFFS:
        raise SurfaceSlotMigrationError("V211/V212 archive-table delta drifted")
    return old_table, new_table


def _ram_from_payload(payload: bytes) -> tuple[int, bytes]:
    try:
        ram_payload_offset = _psx_ram_offset(payload)
    except SystemExit as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc
    if ram_payload_offset != EXPECTED_RAM_PAYLOAD_OFFSET:
        raise SurfaceSlotMigrationError("Serialized RAM payload offset drifted")
    ram = payload[ram_payload_offset : ram_payload_offset + RAM_SIZE]
    if len(ram) != RAM_SIZE:
        raise SurfaceSlotMigrationError("Serialized PSX RAM is incomplete")
    return ram_payload_offset, ram


def _validate_runtime_contract(
    payload: bytes,
    *,
    resident_script: bytes,
    absent_script: bytes,
    label: str,
) -> dict[str, object]:
    if len(payload) != EXPECTED_PAYLOAD_SIZE:
        raise SurfaceSlotMigrationError(f"{label} payload size drifted")
    ram_payload_offset, ram = _ram_from_payload(payload)
    if (
        payload.count(resident_script) != 1
        or ram.count(resident_script) != 1
        or payload.find(resident_script) != EXPECTED_SCRIPT_PAYLOAD_OFFSET
        or ram.find(resident_script) != EXPECTED_SCRIPT_RAM_OFFSET
        or payload.count(absent_script) != 0
    ):
        raise SurfaceSlotMigrationError(f"{label} resident field-550 script drifted")
    current_script = struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0]
    vm_script = struct.unpack_from(
        "<I", ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA
    )[0]
    vm_actor = struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_ACTOR)[0]
    if (
        current_script != EXPECTED_SCRIPT_GUEST_POINTER
        or vm_script != EXPECTED_VM_SCRIPT_GUEST_POINTER
        or vm_actor != EXPECTED_CURRENT_VM_ACTOR
    ):
        raise SurfaceSlotMigrationError(f"{label} script VM pointers drifted")
    field = struct.unpack_from("<I", ram, GAME_SCENE_MAP)[0] & 0x0FFF
    if field != EXPECTED_FIELD:
        raise SurfaceSlotMigrationError(f"{label} is not resident field 550")
    actor_count = struct.unpack_from("<I", ram, FIELD_NUM_ACTORS)[0]
    actor_array_pointer = struct.unpack_from("<I", ram, FIELD_ACTORS)[0]
    if (
        actor_count != EXPECTED_ACTOR_COUNT
        or actor_array_pointer != EXPECTED_ACTOR_ARRAY_GUEST_POINTER
    ):
        raise SurfaceSlotMigrationError(f"{label} actor topology drifted")
    actor_array = _guest_ram_offset(actor_array_pointer, "field actor array")
    actor_contract: dict[int, tuple[int, int, int, int]] = {}
    for entity, expected in EXPECTED_ACTORS.items():
        actor_data = _actor_data_pointer(ram, actor_array, entity)
        pc = struct.unpack_from(
            "<H", ram, actor_data + ACTOR_CURRENT_PC_OFFSET
        )[0]
        slot = ram[actor_data + ACTOR_CURRENT_SLOT_OFFSET]
        triangle = struct.unpack_from(
            "<H", ram, actor_data + ACTOR_TRIANGLE_OFFSET
        )[0]
        actual = (actor_data, pc, slot, triangle)
        if actual != expected:
            raise SurfaceSlotMigrationError(
                f"{label} field actor e{entity} contract drifted: {actual}"
            )
        actor_contract[entity] = actual
    for entity in range(actor_count):
        actor_data = _actor_data_pointer(ram, actor_array, entity)
        pc = struct.unpack_from(
            "<H", ram, actor_data + ACTOR_CURRENT_PC_OFFSET
        )[0]
        if EXIT_GATE_PC <= pc < EXIT_GATE_END_PC:
            raise SurfaceSlotMigrationError(
                f"{label} actor e{entity} is executing the changed exit gate"
            )
    player_data = EXPECTED_ACTORS[1][0]
    seal_data = EXPECTED_ACTORS[19][0]
    if struct.unpack_from("<3i", ram, player_data + ACTOR_POSITION_OFFSET) != (
        EXPECTED_PLAYER_POSITION
    ):
        raise SurfaceSlotMigrationError(f"{label} player position drifted")
    if struct.unpack_from("<3i", ram, seal_data + ACTOR_POSITION_OFFSET) != (
        EXPECTED_SEAL_POSITION
    ):
        raise SurfaceSlotMigrationError(f"{label} exit-seal position drifted")
    if struct.unpack_from(
        "<H", ram, seal_data + ACTOR_COLLISION_RADIUS_OFFSET
    )[0] != EXPECTED_SEAL_COLLISION_RADIUS:
        raise SurfaceSlotMigrationError(f"{label} exit-seal radius drifted")
    gamestate = bytes(ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE])
    if _sha256(gamestate) != EXPECTED_GAMESTATE_SHA256:
        raise SurfaceSlotMigrationError(f"{label} GameState identity drifted")
    return {
        "ram_payload_offset": ram_payload_offset,
        "gamestate": gamestate,
        "actor_array_pointer": actor_array_pointer,
        "actor_contract": actor_contract,
        "seal_radius": EXPECTED_SEAL_COLLISION_RADIUS,
    }


def migrate_v211_slot1_to_v212(
    state: bytes,
    *,
    old_disc: Path,
    new_disc: Path,
    old_script: bytes,
    new_script: bytes,
    zstd: _ZstdLike,
) -> tuple[bytes, dict[str, object]]:
    """Return a separately writable, fully validated V212 state candidate."""

    source_sha256 = _sha256(state)
    if source_sha256 != SOURCE_STATE_SHA256:
        raise SurfaceSlotMigrationError(
            f"Source Slot 1 SHA-256 is {source_sha256}, expected {SOURCE_STATE_SHA256}"
        )
    old_name = OLD_CUE_NAME.encode("ascii")
    new_name = NEW_CUE_NAME.encode("ascii")
    if state.count(old_name) != 1 or state.count(new_name) != 0:
        raise SurfaceSlotMigrationError("Source CUE identity drifted")
    _validate_script_contract(old_script, new_script)
    old_table, new_table = _validate_disc_contract(old_disc, new_disc)
    source_payload, frame_start, source_prefix = _unpack_state(state, zstd)
    if (
        frame_start != EXPECTED_FRAME_START
        or _sha256(source_payload) != SOURCE_PAYLOAD_SHA256
    ):
        raise SurfaceSlotMigrationError("Source payload identity drifted")
    source_runtime = _validate_runtime_contract(
        source_payload,
        resident_script=old_script,
        absent_script=new_script,
        label="V211 source",
    )
    table_offset, volatile_bytes = media_migration._find_resident_archive_table(
        source_payload, old_table
    )
    source_table = source_payload[
        table_offset : table_offset + ARCHIVE_TABLE_SIZE
    ]
    if (
        table_offset != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or volatile_bytes != 1
        or _sha256(source_table) != SOURCE_RESIDENT_TABLE_SHA256
        or _diff_triplets(source_table, new_table) != SOURCE_TABLE_TO_NEW_DIFFS
    ):
        raise SurfaceSlotMigrationError("Resident V211 archive table drifted")

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
    media_payload, media_frame_start, media_prefix = _unpack_state(
        media_state, zstd
    )
    expected_table_offsets = tuple(
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + offset
        for offset, _old, _new in SOURCE_TABLE_TO_NEW_DIFFS
    )
    if (
        media_frame_start != frame_start
        or media_report["resident_table_offset"]
        != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or media_report["volatile_source_table_bytes"] != 1
        or media_report["bytes_changed_in_payload"]
        != len(SOURCE_TABLE_TO_NEW_DIFFS)
        or _diff_offsets(source_payload, media_payload) != expected_table_offsets
        or media_payload[table_offset : table_offset + ARCHIVE_TABLE_SIZE]
        != new_table
    ):
        raise SurfaceSlotMigrationError("Media migration changed unexpected bytes")
    if media_payload[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + SCRIPT_SIZE
    ] != old_script:
        raise SurfaceSlotMigrationError("Media migration changed resident field 550")
    if media_prefix != _expected_prefix(
        source_prefix,
        compressed_size=len(media_state) - frame_start,
    ):
        raise SurfaceSlotMigrationError("Media migration changed unexpected header bytes")

    final_payload = bytearray(media_payload)
    final_payload[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + SCRIPT_SIZE
    ] = new_script
    final_payload_bytes = bytes(final_payload)
    expected_script_offsets = tuple(
        EXPECTED_SCRIPT_PAYLOAD_OFFSET + offset for offset in SCRIPT_DIFF_OFFSETS
    )
    expected_payload_offsets = tuple(
        sorted(expected_table_offsets + expected_script_offsets)
    )
    if _diff_offsets(source_payload, final_payload_bytes) != expected_payload_offsets:
        raise SurfaceSlotMigrationError(
            "Combined migration changed bytes outside the FAT and exit-gate repair"
        )
    if (
        final_payload_bytes.count(old_script) != 0
        or final_payload_bytes.count(new_script) != 1
    ):
        raise SurfaceSlotMigrationError("Resident field-550 replacement is not unique")

    result = _pack_state(media_prefix, final_payload_bytes, zstd)
    verified_payload, verified_frame_start, verified_prefix = _unpack_state(
        result, zstd
    )
    if (
        verified_frame_start != frame_start
        or verified_payload != final_payload_bytes
        or verified_prefix
        != _expected_prefix(
            source_prefix,
            compressed_size=len(result) - frame_start,
        )
        or result.count(old_name) != 0
        or result.count(new_name) != 1
    ):
        raise SurfaceSlotMigrationError("Final V212 state did not round-trip exactly")
    final_runtime = _validate_runtime_contract(
        verified_payload,
        resident_script=new_script,
        absent_script=old_script,
        label="V212 output",
    )
    if final_runtime != source_runtime:
        raise SurfaceSlotMigrationError("Gameplay runtime changed during migration")
    output_sha256 = _sha256(result)
    if (
        len(result) != EXPECTED_OUTPUT_SIZE
        or output_sha256 != EXPECTED_OUTPUT_SHA256
    ):
        raise SurfaceSlotMigrationError("V212 candidate identity drifted")
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
        "archive_table_payload_offset": (
            f"0x{EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET:X}"
        ),
        "script_payload_offset": f"0x{EXPECTED_SCRIPT_PAYLOAD_OFFSET:X}",
        "script_ram_offset": f"0x{EXPECTED_SCRIPT_RAM_OFFSET:X}",
        "old_script_sha256": OLD_SCRIPT_SHA256,
        "new_script_sha256": NEW_SCRIPT_SHA256,
        "payload_bytes_changed": len(expected_payload_offsets),
        "payload_changed_offsets": tuple(
            f"0x{offset:X}" for offset in expected_payload_offsets
        ),
        "gate_scratch_bytes_changed": len(SCRIPT_DIFF_OFFSETS),
        "gamestate_preserved": True,
        "actor_data_preserved": True,
        "seal_radius_preserved": EXPECTED_SEAL_COLLISION_RADIUS,
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
    parser.add_argument("--zstd", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        source = args.source.resolve()
        output = args.output.resolve()
        old_disc = args.old_disc.resolve()
        new_disc = args.new_disc.resolve()
        old_script_path = args.old_script.resolve()
        new_script_path = args.new_script.resolve()
        zstd_path = args.zstd.resolve()
        for path, label in (
            (source, "source state"),
            (old_disc, "V211 disc"),
            (new_disc, "V212 disc"),
            (old_script_path, "V211 field-550 script"),
            (new_script_path, "V212 field-550 script"),
            (zstd_path, "zstd library"),
        ):
            if not path.is_file():
                raise SurfaceSlotMigrationError(f"{label} does not exist: {path}")
        if output == source:
            raise SurfaceSlotMigrationError("Output must not overwrite the source state")
        if output == LIVE_SLOT1:
            raise SurfaceSlotMigrationError(
                "This tool refuses the live Slot 1 path; write a candidate and "
                "install it separately while DuckStation is closed"
            )
        if output.exists():
            raise SurfaceSlotMigrationError(
                f"Refusing to overwrite existing output: {output}"
            )
        result, report = migrate_v211_slot1_to_v212(
            source.read_bytes(),
            old_disc=old_disc,
            new_disc=new_disc,
            old_script=old_script_path.read_bytes(),
            new_script=new_script_path.read_bytes(),
            zstd=media_migration._Zstd(zstd_path),
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        if output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Written V212 candidate changed on disk")
        print(f"Wrote validated V212 candidate: {output}")
        print(json.dumps(report, indent=2, sort_keys=True))
        print(
            "The live Slot 1 was not modified. Install this candidate only "
            "after DuckStation is fully closed."
        )
        return 0
    except (
        OSError,
        SurfaceSlotMigrationError,
        media_migration.StateMigrationError,
    ) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
