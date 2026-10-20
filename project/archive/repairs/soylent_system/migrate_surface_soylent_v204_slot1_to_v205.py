#!/usr/bin/env python3
"""Create a validated V205 candidate from the audited Surface Soylent V204 Slot 1.

The saved field is already resident in PlayStation RAM.  Retargeting only the
mounted CUE and archive table would therefore leave field 621 running its V204
door bytecode until the field was reloaded.  This helper performs the complete
three-part migration in memory:

* replace the exact V204 CUE basename in the DuckStation header;
* replace the exact resident V204 disc archive table with V205's table; and
* replace the exact, equal-length resident field-621 ATEL script with V205's.

This is intentionally a one-state, one-release migration.  Every source asset,
runtime address, script delta, and payload delta is pinned.  The input and
output paths are mandatory and must differ; existing outputs and the live Slot
1 path are refused.  Installing the validated candidate remains a separate
operation to perform only while DuckStation is closed.
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
    "20a7487b773adc6739cd1c1bf0924fcf0310142cb62ea05e85b8c21960985cea"
)
EXPECTED_MEDIA_STATE_SHA256 = (
    "4ebebcbcb73afac76d16c802e01f42edf56244ae7c76a0fcbd12773e734af4de"
)
OLD_DISC_SHA256 = (
    "79b59e10776da09b1175691d717a51f9642b5016056e91c316d964c7c9631255"
)
NEW_DISC_SHA256 = (
    "d3a2ccd661eae4cd987393cecefe1232f9e76f003152e1dd1dfab1521cd3017f"
)
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v204.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v205.cue"

OLD_ARCHIVE_TABLE_SHA256 = (
    "72c3ca5d369b014ade2ce70ee95a88243bd6361452e070aa15c8f7a1e7f9457f"
)
NEW_ARCHIVE_TABLE_SHA256 = (
    "e928168f5b972bb6d88571d0a1bc9519a13e41cf9a11c1899715449dc0ca36fb"
)
ARCHIVE_TABLE_SIZE = 0x8000
ARCHIVE_TABLE_DIFFS = ((0x2F58, 0x44, 0x50),)

OLD_SCRIPT_SHA256 = (
    "0323d26b39b3252ad7c6d2b4d95ff9a33da9e62a44ba80d2ccfa753d8d59f66f"
)
NEW_SCRIPT_SHA256 = (
    "f8ee07c43382d9a14ffc97d286b1521f4f1a6cf3765a1a8ff6cd10ef17efda67"
)
SCRIPT_SIZE = 9_091
SCRIPT_ENTITY_COUNT = 43
SCRIPT_ENTRY_TABLE_OFFSET = 0x84
SCRIPT_ENTRY_SIZE = 0x40
SCRIPT_BYTECODE_OFFSET = 0xB44
SCRIPT_BYTECODE_SIZE = 0x183F
FREIGHT_ENTITY = 26
FREIGHT_ACTION_SLOT = 2
FREIGHT_GATE_PC = 0x1617
FREIGHT_CHANGE_PC = 0x0D4C
OLD_FREIGHT_CHANGE = bytes.fromhex("98 35 82 03 80")
NEW_FREIGHT_CHANGE = bytes.fromhex("98 4C 82 00 80")
SCRIPT_DIFFS = ((0x1891, 0x35, 0x4C), (0x1893, 0x03, 0x00))

EXPECTED_FRAME_START = 0x8765
EXPECTED_PAYLOAD_SIZE = 3_819_109
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
EXPECTED_SCRIPT_RAM_OFFSET = 0x110A38
EXPECTED_SCRIPT_PAYLOAD_OFFSET = 0x11249A
EXPECTED_SCRIPT_GUEST_POINTER = 0x80110A38
EXPECTED_VM_SCRIPT_GUEST_POINTER = 0x8011157C

EXPECTED_FIELD = 621
GAMESTATE_FIELD_OFFSET = 0x231A
EXPECTED_ACTOR_COUNT = 54
EXPECTED_ACTOR_ARRAY_GUEST_POINTER = 0x8011A804
PLAYER_ENTITY = 3
EXPECTED_PLAYER_ACTOR_DATA = 0x11C170
EXPECTED_PLAYER_IDLE_PC = 0x0201
FREIGHT_ACTOR_DATA = 0x11EEC8
EXPECTED_FREIGHT_IDLE_PC = 0x024E
ACTOR_CURRENT_PC_OFFSET = 0xCC
ACTOR_CURRENT_SLOT_OFFSET = 0xCE


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output when any pinned V204/V205 contract drifts."""


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
    if not media_migration.DUCKSTATION_STATE_HEADER_SIZE <= frame_start < len(state):
        raise SurfaceSlotMigrationError(
            "DuckStation state data offset is outside the file"
        )
    frame_end = frame_start + compressed_size
    if frame_end != len(state):
        raise SurfaceSlotMigrationError(
            "DuckStation state has an inconsistent frame span or trailing data"
        )
    frame = state[frame_start:frame_end]
    if not frame.startswith(media_migration.ZSTD_MAGIC):
        raise SurfaceSlotMigrationError(
            "DuckStation state data is not a Zstandard frame"
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


def _guest_ram_offset(pointer: int, label: str) -> int:
    address = pointer & 0x1FFFFFFF
    if address >= RAM_SIZE:
        raise SurfaceSlotMigrationError(
            f"{label} pointer 0x{pointer:08X} is outside PSX RAM"
        )
    return address


def _validate_script_contract(old_script: bytes, new_script: bytes) -> None:
    if (len(old_script), _sha256(old_script)) != (
        SCRIPT_SIZE,
        OLD_SCRIPT_SHA256,
    ):
        raise SurfaceSlotMigrationError("V204 field-621 script identity drifted")
    if (len(new_script), _sha256(new_script)) != (
        SCRIPT_SIZE,
        NEW_SCRIPT_SHA256,
    ):
        raise SurfaceSlotMigrationError("V205 field-621 script identity drifted")
    if _diff_triplets(old_script, new_script) != SCRIPT_DIFFS:
        raise SurfaceSlotMigrationError(
            "Field-621 script delta is not the exact audited V205 freight retarget"
        )

    for label, script, change in (
        ("V204", old_script, OLD_FREIGHT_CHANGE),
        ("V205", new_script, NEW_FREIGHT_CHANGE),
    ):
        entity_count = struct.unpack_from("<I", script, 0x80)[0]
        bytecode_offset = SCRIPT_ENTRY_TABLE_OFFSET + entity_count * SCRIPT_ENTRY_SIZE
        if (
            entity_count != SCRIPT_ENTITY_COUNT
            or bytecode_offset != SCRIPT_BYTECODE_OFFSET
            or len(script) - bytecode_offset != SCRIPT_BYTECODE_SIZE
        ):
            raise SurfaceSlotMigrationError(
                f"{label} field-621 ATEL topology drifted"
            )
        pointer_offset = (
            SCRIPT_ENTRY_TABLE_OFFSET
            + FREIGHT_ENTITY * SCRIPT_ENTRY_SIZE
            + FREIGHT_ACTION_SLOT * 2
        )
        if struct.unpack_from("<H", script, pointer_offset)[0] != FREIGHT_GATE_PC:
            raise SurfaceSlotMigrationError(
                f"{label} field-621 e26 gate pointer drifted"
            )
        raw_change = bytecode_offset + FREIGHT_CHANGE_PC
        if script[raw_change : raw_change + len(change)] != change:
            raise SurfaceSlotMigrationError(
                f"{label} field-621 e26 destination instruction drifted"
            )


def _validate_disc_contract(
    old_disc: Path,
    new_disc: Path,
) -> tuple[bytes, bytes]:
    old_disc_hash = _file_sha256(old_disc)
    new_disc_hash = _file_sha256(new_disc)
    if old_disc_hash != OLD_DISC_SHA256:
        raise SurfaceSlotMigrationError(
            f"V204 disc SHA-256 is {old_disc_hash}, expected {OLD_DISC_SHA256}"
        )
    if new_disc_hash != NEW_DISC_SHA256:
        raise SurfaceSlotMigrationError(
            f"V205 disc SHA-256 is {new_disc_hash}, expected {NEW_DISC_SHA256}"
        )

    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    if (len(old_table), _sha256(old_table)) != (
        ARCHIVE_TABLE_SIZE,
        OLD_ARCHIVE_TABLE_SHA256,
    ):
        raise SurfaceSlotMigrationError("V204 resident archive-table identity drifted")
    if (len(new_table), _sha256(new_table)) != (
        ARCHIVE_TABLE_SIZE,
        NEW_ARCHIVE_TABLE_SHA256,
    ):
        raise SurfaceSlotMigrationError("V205 resident archive-table identity drifted")
    if _diff_triplets(old_table, new_table) != ARCHIVE_TABLE_DIFFS:
        raise SurfaceSlotMigrationError(
            "V204/V205 archive-table delta is not the exact audited release delta"
        )
    return old_table, new_table


def _ram_from_payload(payload: bytes) -> tuple[int, bytes]:
    try:
        ram_payload_offset = _psx_ram_offset(payload)
    except SystemExit as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc
    if ram_payload_offset != EXPECTED_RAM_PAYLOAD_OFFSET:
        raise SurfaceSlotMigrationError(
            f"Serialized RAM begins at payload 0x{ram_payload_offset:X}, expected "
            f"0x{EXPECTED_RAM_PAYLOAD_OFFSET:X}"
        )
    ram = payload[ram_payload_offset : ram_payload_offset + RAM_SIZE]
    if len(ram) != RAM_SIZE:
        raise SurfaceSlotMigrationError("Serialized PSX RAM is incomplete")
    return ram_payload_offset, ram


def _actor_data_pointer(ram: bytes, actor_array: int, entity: int) -> int:
    actor = actor_array + entity * FIELD_ACTOR_STRIDE
    pointer = struct.unpack_from(
        "<I", ram, actor + FIELD_ACTOR_DATA_POINTER
    )[0]
    return _guest_ram_offset(pointer, f"field actor e{entity} ActorData")


def _validate_runtime_contract(
    payload: bytes,
    *,
    resident_script: bytes,
    absent_script: bytes,
    label: str,
) -> dict[str, object]:
    if len(payload) != EXPECTED_PAYLOAD_SIZE:
        raise SurfaceSlotMigrationError(
            f"{label} payload size is {len(payload)}, expected {EXPECTED_PAYLOAD_SIZE}"
        )
    ram_payload_offset, ram = _ram_from_payload(payload)
    if payload.count(resident_script) != 1 or ram.count(resident_script) != 1:
        raise SurfaceSlotMigrationError(
            f"{label} resident field-621 script is not unique in serialized RAM"
        )
    if payload.find(resident_script) != EXPECTED_SCRIPT_PAYLOAD_OFFSET:
        raise SurfaceSlotMigrationError(
            f"{label} resident field-621 script moved in the state payload"
        )
    if ram.find(resident_script) != EXPECTED_SCRIPT_RAM_OFFSET:
        raise SurfaceSlotMigrationError(
            f"{label} resident field-621 script moved in PSX RAM"
        )
    if payload.count(absent_script) != 0:
        raise SurfaceSlotMigrationError(
            f"{label} unexpectedly contains the opposite field-621 script"
        )

    current_script = struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0]
    vm_script = struct.unpack_from(
        "<I", ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA
    )[0]
    if (
        current_script != EXPECTED_SCRIPT_GUEST_POINTER
        or vm_script != EXPECTED_VM_SCRIPT_GUEST_POINTER
    ):
        raise SurfaceSlotMigrationError(
            f"{label} field-script runtime pointers do not match Slot 1"
        )
    field = struct.unpack_from(
        "<H", ram, GAME_STATE + GAMESTATE_FIELD_OFFSET
    )[0]
    if field != EXPECTED_FIELD:
        raise SurfaceSlotMigrationError(
            f"{label} GameState field is {field}, expected {EXPECTED_FIELD}"
        )

    actor_count = struct.unpack_from("<I", ram, FIELD_NUM_ACTORS)[0]
    actor_array_pointer = struct.unpack_from("<I", ram, FIELD_ACTORS)[0]
    if (
        actor_count != EXPECTED_ACTOR_COUNT
        or actor_array_pointer != EXPECTED_ACTOR_ARRAY_GUEST_POINTER
    ):
        raise SurfaceSlotMigrationError(f"{label} field-621 actor topology drifted")
    actor_array = _guest_ram_offset(actor_array_pointer, "field actor array")
    player_actor_data = _actor_data_pointer(ram, actor_array, PLAYER_ENTITY)
    freight_actor_data = _actor_data_pointer(ram, actor_array, FREIGHT_ENTITY)
    if (
        player_actor_data != EXPECTED_PLAYER_ACTOR_DATA
        or freight_actor_data != FREIGHT_ACTOR_DATA
    ):
        raise SurfaceSlotMigrationError(f"{label} player/e26 ActorData moved")
    player_pc = struct.unpack_from(
        "<H", ram, player_actor_data + ACTOR_CURRENT_PC_OFFSET
    )[0]
    freight_pc = struct.unpack_from(
        "<H", ram, freight_actor_data + ACTOR_CURRENT_PC_OFFSET
    )[0]
    player_slot = ram[player_actor_data + ACTOR_CURRENT_SLOT_OFFSET]
    freight_slot = ram[freight_actor_data + ACTOR_CURRENT_SLOT_OFFSET]
    if (
        (player_pc, player_slot) != (EXPECTED_PLAYER_IDLE_PC, 0)
        or (freight_pc, freight_slot) != (EXPECTED_FREIGHT_IDLE_PC, 0)
    ):
        raise SurfaceSlotMigrationError(
            f"{label} player/e26 is not in the audited idle state"
        )
    if FREIGHT_CHANGE_PC <= player_pc < FREIGHT_CHANGE_PC + 5 or (
        FREIGHT_CHANGE_PC <= freight_pc < FREIGHT_CHANGE_PC + 5
    ):
        raise SurfaceSlotMigrationError(
            f"{label} has a live actor executing the changed e26 instruction"
        )

    return {
        "ram_payload_offset": ram_payload_offset,
        "gamestate": bytes(ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE]),
        "actor_array_pointer": actor_array_pointer,
        "player_actor_data": player_actor_data,
        "freight_actor_data": freight_actor_data,
        "player_pc": player_pc,
        "freight_pc": freight_pc,
    }


def _expected_prefix(
    source_prefix: bytes,
    *,
    compressed_size: int,
) -> bytes:
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


def _pack_state(prefix: bytes, payload: bytes, zstd: _ZstdLike) -> bytes:
    compressed = zstd.compress(payload)
    if len(compressed) > 0xFFFFFFFF:
        raise SurfaceSlotMigrationError(
            "Recompressed DuckStation payload exceeds its 32-bit header field"
        )
    updated = bytearray(prefix)
    struct.pack_into(
        "<I",
        updated,
        media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        len(compressed),
    )
    return bytes(updated) + compressed


def migrate_v204_slot1_to_v205(
    state: bytes,
    *,
    old_disc: Path,
    new_disc: Path,
    old_script: bytes,
    new_script: bytes,
    zstd: _ZstdLike,
) -> tuple[bytes, dict[str, object]]:
    """Return a separately writable, fully validated V205 state candidate."""

    source_sha256 = _sha256(state)
    if source_sha256 != SOURCE_STATE_SHA256:
        raise SurfaceSlotMigrationError(
            f"Source Slot 1 SHA-256 is {source_sha256}, expected "
            f"{SOURCE_STATE_SHA256}"
        )
    if state.count(OLD_CUE_NAME.encode("ascii")) != 1:
        raise SurfaceSlotMigrationError("Source does not contain one exact V204 CUE name")
    if state.count(NEW_CUE_NAME.encode("ascii")) != 0:
        raise SurfaceSlotMigrationError("Source already contains the V205 CUE name")

    _validate_script_contract(old_script, new_script)
    old_table, new_table = _validate_disc_contract(old_disc, new_disc)
    source_payload, frame_start, source_prefix = _unpack_state(state, zstd)
    if frame_start != EXPECTED_FRAME_START:
        raise SurfaceSlotMigrationError(
            f"Source zstd frame begins at 0x{frame_start:X}, expected "
            f"0x{EXPECTED_FRAME_START:X}"
        )
    source_runtime = _validate_runtime_contract(
        source_payload,
        resident_script=old_script,
        absent_script=new_script,
        label="V204 source",
    )
    table_offset, volatile_bytes = media_migration._find_resident_archive_table(
        source_payload, old_table
    )
    if (
        table_offset != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or volatile_bytes != 0
    ):
        raise SurfaceSlotMigrationError(
            "V204 resident archive table is not the exact audited Slot 1 copy"
        )

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
        raise SurfaceSlotMigrationError(
            f"V204-to-V205 media migration failed: {exc}"
        ) from exc

    if (
        _sha256(media_state) != EXPECTED_MEDIA_STATE_SHA256
        or media_report["resident_table_offset"]
        != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or media_report["volatile_source_table_bytes"] != 0
        or media_report["old_table_sha256"] != OLD_ARCHIVE_TABLE_SHA256
        or media_report["new_table_sha256"] != NEW_ARCHIVE_TABLE_SHA256
        or media_report["bytes_changed_in_payload"] != len(ARCHIVE_TABLE_DIFFS)
    ):
        raise SurfaceSlotMigrationError("Media migration report drifted from V205")

    media_payload, media_frame_start, media_prefix = _unpack_state(media_state, zstd)
    if media_frame_start != frame_start:
        raise SurfaceSlotMigrationError("Media migration moved the zstd frame")
    expected_table_offsets = tuple(
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + offset
        for offset, _old, _new in ARCHIVE_TABLE_DIFFS
    )
    if _diff_offsets(source_payload, media_payload) != expected_table_offsets:
        raise SurfaceSlotMigrationError(
            "Media migration changed payload bytes outside the exact V205 FAT delta"
        )
    if (
        media_payload.count(new_table) != 1
        or media_payload.find(new_table) != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or media_payload.count(old_table) != 0
    ):
        raise SurfaceSlotMigrationError("Media migration did not install one V205 FAT")
    if media_payload[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + SCRIPT_SIZE
    ] != old_script:
        raise SurfaceSlotMigrationError("Media migration changed resident field 621")
    expected_media_prefix = _expected_prefix(
        source_prefix,
        compressed_size=len(media_state) - frame_start,
    )
    if media_prefix != expected_media_prefix:
        raise SurfaceSlotMigrationError(
            "Media migration changed header bytes outside the CUE and size fields"
        )

    final_payload = bytearray(media_payload)
    final_payload[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + SCRIPT_SIZE
    ] = new_script
    final_payload_bytes = bytes(final_payload)
    expected_payload_offsets = tuple(
        sorted(
            expected_table_offsets
            + tuple(
                EXPECTED_SCRIPT_PAYLOAD_OFFSET + offset
                for offset, _old, _new in SCRIPT_DIFFS
            )
        )
    )
    if _diff_offsets(source_payload, final_payload_bytes) != expected_payload_offsets:
        raise SurfaceSlotMigrationError(
            "Combined migration changed bytes outside the exact FAT/script delta"
        )
    if (
        final_payload_bytes.count(old_script) != 0
        or final_payload_bytes.count(new_script) != 1
    ):
        raise SurfaceSlotMigrationError(
            "Resident field-621 replacement did not produce one exact V205 copy"
        )

    result = _pack_state(media_prefix, final_payload_bytes, zstd)
    verified_payload, verified_frame_start, verified_prefix = _unpack_state(
        result, zstd
    )
    if verified_frame_start != frame_start or verified_payload != final_payload_bytes:
        raise SurfaceSlotMigrationError(
            "Final V205 candidate did not round-trip through Zstandard exactly"
        )
    expected_final_prefix = _expected_prefix(
        source_prefix,
        compressed_size=len(result) - frame_start,
    )
    if verified_prefix != expected_final_prefix:
        raise SurfaceSlotMigrationError(
            "Final V205 header changed outside the CUE and compressed-size fields"
        )
    if (
        result.count(OLD_CUE_NAME.encode("ascii")) != 0
        or result.count(NEW_CUE_NAME.encode("ascii")) != 1
    ):
        raise SurfaceSlotMigrationError("Final V205 CUE identity is not unique")
    final_runtime = _validate_runtime_contract(
        verified_payload,
        resident_script=new_script,
        absent_script=old_script,
        label="V205 output",
    )
    if final_runtime["gamestate"] != source_runtime["gamestate"]:
        raise SurfaceSlotMigrationError("Resident Xenogears GameState changed")
    for key in (
        "ram_payload_offset",
        "actor_array_pointer",
        "player_actor_data",
        "freight_actor_data",
        "player_pc",
        "freight_pc",
    ):
        if final_runtime[key] != source_runtime[key]:
            raise SurfaceSlotMigrationError(
                f"Runtime contract value {key} changed during migration"
            )

    return result, {
        "source_sha256": source_sha256,
        "media_state_sha256": EXPECTED_MEDIA_STATE_SHA256,
        "output_sha256": _sha256(result),
        "source_size": len(state),
        "output_size": len(result),
        "field": EXPECTED_FIELD,
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "payload_size": len(verified_payload),
        "frame_offset": f"0x{frame_start:X}",
        "ram_payload_offset": f"0x{EXPECTED_RAM_PAYLOAD_OFFSET:X}",
        "archive_table_payload_offset": (
            f"0x{EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET:X}"
        ),
        "script_ram_offset": f"0x{EXPECTED_SCRIPT_RAM_OFFSET:X}",
        "script_payload_offset": f"0x{EXPECTED_SCRIPT_PAYLOAD_OFFSET:X}",
        "old_script_sha256": OLD_SCRIPT_SHA256,
        "new_script_sha256": NEW_SCRIPT_SHA256,
        "payload_bytes_changed": len(expected_payload_offsets),
        "payload_changed_offsets": tuple(
            f"0x{offset:X}" for offset in expected_payload_offsets
        ),
        "gamestate_preserved": True,
        "runtime_contract_preserved": True,
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
            (old_disc, "V204 disc"),
            (new_disc, "V205 disc"),
            (old_script_path, "V204 field-621 script"),
            (new_script_path, "V205 field-621 script"),
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

        result, report = migrate_v204_slot1_to_v205(
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
            raise SurfaceSlotMigrationError(
                "Written V205 candidate does not match the validated result"
            )
        print(f"Wrote validated V205 candidate: {output}")
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
