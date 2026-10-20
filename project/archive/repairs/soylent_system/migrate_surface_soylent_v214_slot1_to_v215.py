#!/usr/bin/env python3
"""Build the allocator-safe V215 candidate for the audited V214 Slot 1.

The captured state is paused on field 593's Quarantine-card description.  Its
resident ATEL allocation has only sixteen spare bytes, while the normal V215
field file is twenty-nine bytes larger.  Copying that file into RAM would
overwrite a live heap header and allocation.  This migration therefore keeps
the resident file and every live PC at their V214 sizes/addresses, jumps from
the card action into a retired field-352 entity-14 cavity, and stores the new
choice in retired dialogue slot 52.  The normal V215 files remain on disc and
will be used after the field is loaded again.

The active window's start/current pointers are deliberately left untouched.
Dialogue 53 is rewritten at its old address and padded with Close opcodes, so
both pointers remain valid while subsequent interactions get the shorter text.
The helper is fail-closed, writes only a separate candidate, and never writes
the live Slot 1.
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
from tools.xgdialog import parse_dialogue  # noqa: E402
from tools.xgscript import AtelScript  # noqa: E402
from work.read_duckstation_runtime import (  # noqa: E402
    CAMERA_VECTORS,
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

SOURCE_STATE_SIZE = 1_845_036
SOURCE_STATE_SHA256 = "dcd01f7a32a44c831d152c0ba97e562dbd8043a1f2fa09ad160aa9da118050a2"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "800c49934d39d46e58e6d259190908568a9a9a14115f688b8fdb370709d1547e"
EXPECTED_FRAME_START = 0x8BF4
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62

OLD_DISC_SIZE = 698_642_784
OLD_DISC_SHA256 = "b3bdc04631d89e44353e5f6d02f672a8237111189015675a4efcaab41f54ace8"
NEW_DISC_SIZE = 698_642_784
NEW_DISC_SHA256 = "2ebd33059188333895db4ec2a2fbe80568d9707cfb7a464ebe49c4fa8d6af1c3"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v214.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v215.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = "b6a0d53c65e5205a9e8f3505091e8f6c2e91d3a0330642a15031e5293cdf7f2c"
NEW_CUE_SHA256 = "fbce922f0018ae7ac6698e6c49b5d0e782659f4f2b9bcb87b23b99622157c275"

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = "10121240c6e8f4c6d724959518744178fad6987a72339a7f7b03b66c1417f454"
NEW_ARCHIVE_TABLE_SHA256 = "6c97368f1892d1f0dcf24d739fb5ce13f6e255f8310a5bb9cf8971c1ff50e541"
ARCHIVE_TABLE_DIFFS = ((0x30E0, 0x60, 0x88), (0x3268, 0x44, 0xC8))
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
EXPECTED_VOLATILE_TABLE_VALUE = 0xE0

OLD_SCRIPT_SIZE = 3_392
NEW_SCRIPT_SIZE = 3_421
OLD_SCRIPT_SHA256 = "38110231ca7a3670f72a1d078b0968e16b55e22f0db920f696dbf4147669bb1d"
NEW_SCRIPT_SHA256 = "99b1323786e554f3bdaff39ba08bfcf8b27d2c7640558ff5984de8fe1cd8daad"
RESIDENT_SCRIPT_SIZE = OLD_SCRIPT_SIZE
RESIDENT_SCRIPT_SHA256 = "62ade3971f6caa319652757a3138e1509f5abff9239bc0fb597d0c4cc82badff"
EXPECTED_SCRIPT_PAYLOAD_OFFSET = 0x10CD56
EXPECTED_SCRIPT_GUEST_POINTER = 0x8010B2F4
EXPECTED_VM_SCRIPT_GUEST_POINTER = 0x8010B8B8
SCRIPT_BYTECODE_OFFSET = 0x05C4
SCRIPT_ALLOCATED_CAPACITY = 0x0D50
SCRIPT_NEXT_HEADER_GUEST = 0x10C044
SCRIPT_GAP_SIZE = 48
SCRIPT_GAP_SHA256 = "3edf0e090fcbc4fa185663d9af64830047f1408d1e7d3fa8db1eb5bc50674e41"

OLD_DIALOGUE_SIZE = 5_474
NEW_DIALOGUE_SIZE = 5_488
OLD_DIALOGUE_SHA256 = "a0052a30fc6969a3152fa9d270355be85ad1fc122bdba06a5feb8ce933114f1e"
NEW_DIALOGUE_SHA256 = "afad9f8c0e8b9b3418ad501a6260e666537a6a5d305d449925ec26e3712f5770"
RESIDENT_DIALOGUE_SIZE = OLD_DIALOGUE_SIZE
RESIDENT_DIALOGUE_SHA256 = "a8d562582b5a6d8768cce8b7b7678a8b7a38ad087ab47e988a581b1a4051c3f9"
EXPECTED_DIALOGUE_PAYLOAD_OFFSET = 0x10DAC6
EXPECTED_DIALOGUE_GUEST_POINTER = 0x8010C064
DIALOGUE_ALLOCATED_CAPACITY = 5_492
EXPECTED_WALKMESH_PAYLOAD_OFFSET = 0x10F042
DIALOGUE_GAP_SIZE = 26
DIALOGUE_GAP_SHA256 = "7ba2053e722728bc8ac47e00ab36580454e6264cad00c524d149649e9c279c46"

# V214's terminal action is live at WAIT_DIALOG 0x0708.  Its next award path
# starts at 0x0717; a three-byte absolute jump reaches a wholly retired e14
# routine range.  All 32 e14 slots point to shared STOP 0x068C.
TERMINAL_ENTITY = 19
SCHEDULER_ENTITY = 20
TERMINAL_ACTION_PC = 0x06E0
TERMINAL_ACTIVE_PC = 0x0708
TERMINAL_FINISH_PC = 0x0725
SHARED_STOP_PC = 0x0728
ACTION_JUMP_PC = 0x0717
ACTION_JUMP_OLD = bytes.fromhex("74 37 80")
ACTION_JUMP_NEW = bytes.fromhex("01 E3 03")
RETIRED_ENTITY = 14
RETIRED_ENTITY_STOP_PC = 0x068C
RETIRED_CAVITY_PC = 0x03E3
RETIRED_CAVITY_OLD = bytes.fromhex(
    "0B 02 80 84 98 80 18 04 02 E0 00 0A 00 42 F8 03 "
    "29 0E 01 15 04 02 EA 00 04 00 46 0C 04 19 78 00 "
    "CE FF C0 69 06 80 01 15 04 19 00 00 92 00"
)
RETIRED_CAVITY_BODY = bytes.fromhex(
    "D2 34 00 00 A9 12 9C 02 14 00 01 00 40 25 07 "
    "31 20 00 FD 03 26 01 80 01 F2 03 26 01 80 "
    "74 37 80 F5 36 00 01 9C 3A 1A 02 08 00 40 "
    "01 25 07"
)

# Retired ID52 is large enough for the 61-byte choice without moving any
# dialogue address.  IDs53/55 are rewritten at their V214 starts and padded
# with 0x00 (Close), preserving the active window pointers.
CHOICE_DIALOGUE_ID = 52
INSERTED_DIALOGUE_ID = 53
ACQUIRED_DIALOGUE_ID = 54
EMPTY_DIALOGUE_ID = 55
NEW_CHOICE_DIALOGUE_ID = 56
RESIDENT_DIALOGUE_SPANS = {
    52: (0x13EA, 91, 56),
    53: (0x1445, 109, 53),
    55: (0x14FC, 102, 55),
}
CHOICE_GRID = (58, 4)

EXPECTED_FIELD = 593
EXPECTED_ACTOR_COUNT = 35
EXPECTED_ACTOR_ARRAY_GUEST_POINTER = 0x80112DB0
EXPECTED_TERMINAL_ACTOR_DATA = 0x115B78
EXPECTED_SCHEDULER_ACTOR_DATA = 0x115D30
ACTOR_SCRIPT_SLOT_OFFSET = 0x8C
ACTOR_CURRENT_PC_OFFSET = 0xCC
EXPECTED_TERMINAL_SLOT0 = bytes.fromhex("08 07 00 02 FF FF 0C 00")
EXPECTED_SCHEDULER_SLOT0 = bytes.fromhex("28 07 00 FF FF FF 3C 00")
EXPECTED_SCHEDULER_CURRENT = bytes.fromhex("28 07 00 00")
EXPECTED_VM_ACTOR_GUEST_POINTER = 0x80115D30

FIELD_CUR_DIALOGUE_FILE = 0x0ADBF0
FIELD_SMALL_COMPONENT = 0x0ADBF4
EXPECTED_SMALL_COMPONENT_POINTER = 0x8010C04C
GAME_SCENE_MAP = 0x04F34C

DIALOG_WINDOWS = 0x0C2698
DIALOG_WINDOWS_SIZE = 4 * 0x498
ACTIVE_WINDOW_START_POINTER_OFFSET = DIALOG_WINDOWS + 0xA8
ACTIVE_WINDOW_CURRENT_POINTER_OFFSET = DIALOG_WINDOWS + 0x34
EXPECTED_ACTIVE_WINDOW_START_POINTER = 0x8010D4A9
EXPECTED_ACTIVE_WINDOW_CURRENT_POINTER = 0x8010D515
EXPECTED_DIALOG_WINDOWS_SHA256 = "ea5eee648dc90242d4af0f3019d002cf21b2793b9f00393e3a544bc7e999b448"

EXPECTED_GAMESTATE_SHA256 = "aa0ca37198c51a4009611123b8349f458be3b5fce3c3dcb794a9a646676fa375"
EXPECTED_CAMERA_SHA256 = "bd12f57e1570114ca5619678f7d2d5e85ca58c8086848808f61781104cbe4f60"
PARTY_RECORD_SHA256 = (
    "94ae9b6d64e1b0e7123d181815600ceefd386ff6380befcc29ca9ca715366b3f",
    "aa101a6ff6fc0bdc7db549abcc0eed7d7400552cd63637b99bf3b0102e0af48d",
    "faf5b005295483df7afc958fa168275d8669846321fae706fb4fb2bad21ab87c",
)
PARTY_ACTOR_DATA_POINTERS = (0x113A4C, 0x113C04, 0x113DBC)
PARTY_ACTOR_DATA_SHA256 = (
    "a0dd538fd1b13c04c8782043409f2de5baeaa310332c35a2064b201b77e211ed",
    "203f60e45af19a4d90b97ff37c9b09bf8e11fc8682995bd30c4d476513ceb18d",
    "ba08eb75211e7e2c785e764cb28db9a626fd85085599455a5057a2e6f4fc3f94",
)

EXPECTED_SCRIPT_BYTES_CHANGED = 49
EXPECTED_DIALOGUE_BYTES_CHANGED = 270
EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED = 2
EXPECTED_PAYLOAD_BYTES_CHANGED = 321
EXPECTED_OUTPUT_SIZE = 1_674_270
EXPECTED_OUTPUT_SHA256 = "509b97a21526b1fb86ed0e19ac2be5743462a669d404a6dac01740d06871d195"
EXPECTED_OUTPUT_PAYLOAD_SHA256 = "630a27ae3811d38483a2897d261471ba7d643ba5646143ead22152f42de17748"


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output whenever a pinned V214/V215 contract drifts."""


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


def _diff_offsets(before: bytes, after: bytes) -> tuple[int, ...]:
    if len(before) != len(after):
        raise SurfaceSlotMigrationError("Compared byte strings have different lengths")
    return tuple(i for i, (old, new) in enumerate(zip(before, after, strict=True)) if old != new)


def _unpack_state(state: bytes, zstd: _ZstdLike) -> tuple[bytes, int, bytes]:
    if len(state) < media_migration.DUCKSTATION_STATE_HEADER_SIZE or state[:4] != media_migration.DUCKSTATION_STATE_MAGIC:
        raise SurfaceSlotMigrationError("Input is not a supported DuckStation state")
    compression, compressed_size, payload_size, frame_start = struct.unpack_from(
        "<IIII", state, media_migration.DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET
    )
    if compression != media_migration.DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise SurfaceSlotMigrationError("DuckStation payload is not Zstandard-compressed")
    frame = state[frame_start : frame_start + compressed_size]
    if frame_start + compressed_size != len(state) or zstd.frame_size(frame) != compressed_size:
        raise SurfaceSlotMigrationError("DuckStation compressed frame span drifted")
    payload = zstd.decompress(frame)
    if len(payload) != payload_size:
        raise SurfaceSlotMigrationError("DuckStation payload-size header drifted")
    return payload, frame_start, state[:frame_start]


def _pack_state(prefix: bytes, payload: bytes, zstd: _ZstdLike) -> bytes:
    compressed = zstd.compress(payload)
    result_prefix = bytearray(prefix)
    struct.pack_into("<I", result_prefix, media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET, len(compressed))
    return bytes(result_prefix) + compressed


def _expected_prefix(source_prefix: bytes, *, compressed_size: int) -> bytes:
    old_name, new_name = OLD_CUE_NAME.encode(), NEW_CUE_NAME.encode()
    expected = bytearray(source_prefix.replace(old_name, new_name))
    struct.pack_into("<I", expected, media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET, compressed_size)
    return bytes(expected)


def _ram_from_payload(payload: bytes) -> tuple[int, bytes]:
    try:
        offset = _psx_ram_offset(payload)
    except SystemExit as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc
    if offset != EXPECTED_RAM_PAYLOAD_OFFSET:
        raise SurfaceSlotMigrationError("Serialized RAM payload offset drifted")
    return offset, payload[offset : offset + RAM_SIZE]


def _build_resident_script(old_script: bytes) -> bytes:
    editor = AtelScript(old_script)
    if editor.bytecode_offset != SCRIPT_BYTECODE_OFFSET:
        raise SurfaceSlotMigrationError("V214 bytecode offset drifted")
    bytecode = editor.bytecode
    if bytecode[ACTION_JUMP_PC : ACTION_JUMP_PC + 3] != ACTION_JUMP_OLD:
        raise SurfaceSlotMigrationError("V214 award entry drifted")
    if bytecode[RETIRED_CAVITY_PC : RETIRED_CAVITY_PC + len(RETIRED_CAVITY_OLD)] != RETIRED_CAVITY_OLD:
        raise SurfaceSlotMigrationError("Retired e14 cavity provenance drifted")
    if any(editor.get_script_pointer(RETIRED_ENTITY, slot) != RETIRED_ENTITY_STOP_PC for slot in range(32)):
        raise SurfaceSlotMigrationError("Retired e14 cavity became reachable")
    result = bytearray(old_script)
    result[SCRIPT_BYTECODE_OFFSET + ACTION_JUMP_PC : SCRIPT_BYTECODE_OFFSET + ACTION_JUMP_PC + 3] = ACTION_JUMP_NEW
    result[SCRIPT_BYTECODE_OFFSET + RETIRED_CAVITY_PC : SCRIPT_BYTECODE_OFFSET + RETIRED_CAVITY_PC + len(RETIRED_CAVITY_BODY)] = RETIRED_CAVITY_BODY
    resident = bytes(result)
    if (len(resident), _sha256(resident)) != (RESIDENT_SCRIPT_SIZE, RESIDENT_SCRIPT_SHA256):
        raise SurfaceSlotMigrationError("Allocator-safe resident script identity drifted")
    return resident


def _build_resident_dialogue(old_dialogue: bytes, new_dialogue: bytes) -> bytes:
    old, new = parse_dialogue(old_dialogue), parse_dialogue(new_dialogue)
    if len(old.blocks) != 56 or len(new.blocks) != 57:
        raise SurfaceSlotMigrationError("V214/V215 dialogue count drifted")
    result = bytearray(old_dialogue)
    dimensions = 4 + 2 * len(old.blocks)
    result[dimensions + CHOICE_DIALOGUE_ID * 2 : dimensions + CHOICE_DIALOGUE_ID * 2 + 2] = bytes(CHOICE_GRID)
    for destination, (start, capacity, source) in RESIDENT_DIALOGUE_SPANS.items():
        old_block = old.blocks[destination]
        payload = new.blocks[source].payload
        if old_block.offset != start or len(old_block.payload) != capacity or len(payload) > capacity:
            raise SurfaceSlotMigrationError(f"Dialogue cavity {destination} drifted")
        result[start : start + capacity] = payload + b"\x00" * (capacity - len(payload))
    resident = bytes(result)
    parsed = parse_dialogue(resident)
    if (
        (len(resident), _sha256(resident)) != (RESIDENT_DIALOGUE_SIZE, RESIDENT_DIALOGUE_SHA256)
        or (parsed.blocks[52].width, parsed.blocks[52].height) != CHOICE_GRID
        or not parsed.blocks[52].text.startswith("<Opcode:01:FF>Take the Quarantine keycard?")
        or not parsed.blocks[53].text.startswith("QUARANTINE KEYCARD\nA keycard is seated")
        or not parsed.blocks[55].text.startswith("SOLARIS AUTHORIZATION\nAccess slot: EMPTY")
    ):
        raise SurfaceSlotMigrationError("Allocator-safe resident dialogue identity drifted")
    return resident


def _validate_resources(old_disc: Path, new_disc: Path, old_script: bytes, new_script: bytes, old_dialogue: bytes, new_dialogue: bytes) -> tuple[bytes, bytes, bytes, bytes]:
    identities = (
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V214 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V215 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V214 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V215 CUE"),
    )
    for path, size, sha, label in identities:
        if not path.is_file() or path.stat().st_size != size or _file_sha256(path) != sha:
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    blobs = (
        (old_script, OLD_SCRIPT_SIZE, OLD_SCRIPT_SHA256, "V214 script"),
        (new_script, NEW_SCRIPT_SIZE, NEW_SCRIPT_SHA256, "V215 script"),
        (old_dialogue, OLD_DIALOGUE_SIZE, OLD_DIALOGUE_SHA256, "V214 dialogue"),
        (new_dialogue, NEW_DIALOGUE_SIZE, NEW_DIALOGUE_SHA256, "V215 dialogue"),
    )
    for blob, size, sha, label in blobs:
        if (len(blob), _sha256(blob)) != (size, sha):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    old_editor, new_editor = AtelScript(old_script), AtelScript(new_script)
    if (
        old_editor.entity_count != 21
        or new_editor.entity_count != 21
        or old_editor.get_script_pointer(TERMINAL_ENTITY, 2) != TERMINAL_ACTION_PC
        or new_editor.get_script_pointer(TERMINAL_ENTITY, 2) != TERMINAL_ACTION_PC
        or old_editor.bytecode[TERMINAL_ACTIVE_PC] != 0x9C
        or new_editor.bytecode[TERMINAL_ACTIVE_PC] != 0x9C
        or old_editor.get_script_pointer(SCHEDULER_ENTITY, 1) != SHARED_STOP_PC
        or new_editor.get_script_pointer(SCHEDULER_ENTITY, 1) != 0x0745
    ):
        raise SurfaceSlotMigrationError("Field-593 V214/V215 script topology drifted")
    old_table, new_table = media_migration._archive_table(old_disc), media_migration._archive_table(new_disc)
    diffs = tuple((i, a, b) for i, (a, b) in enumerate(zip(old_table, new_table, strict=True)) if a != b)
    if (
        _sha256(old_table) != OLD_ARCHIVE_TABLE_SHA256
        or _sha256(new_table) != NEW_ARCHIVE_TABLE_SHA256
        or diffs != ARCHIVE_TABLE_DIFFS
    ):
        raise SurfaceSlotMigrationError("V214/V215 archive-table delta drifted")
    return old_table, new_table, _build_resident_script(old_script), _build_resident_dialogue(old_dialogue, new_dialogue)


def _camera_snapshot(ram: bytes) -> bytes:
    return b"".join(ram[address : address + 16] for address in CAMERA_VECTORS.values())


def _validate_source(payload: bytes, old_table: bytes, old_script: bytes, old_dialogue: bytes) -> dict[str, object]:
    if len(payload) != SOURCE_PAYLOAD_SIZE or _sha256(payload) != SOURCE_PAYLOAD_SHA256:
        raise SurfaceSlotMigrationError("V214 decompressed payload identity drifted")
    ram_offset, ram = _ram_from_payload(payload)
    table_offset, volatile = media_migration._find_resident_archive_table(payload, old_table)
    script_end = EXPECTED_SCRIPT_PAYLOAD_OFFSET + len(old_script)
    dialogue_end = EXPECTED_DIALOGUE_PAYLOAD_OFFSET + len(old_dialogue)
    if (
        table_offset != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or volatile != 1
        or payload.count(old_script) != 1
        or payload.find(old_script) != EXPECTED_SCRIPT_PAYLOAD_OFFSET
        or payload.count(old_dialogue) != 1
        or payload.find(old_dialogue) != EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        or _sha256(payload[script_end:EXPECTED_DIALOGUE_PAYLOAD_OFFSET]) != SCRIPT_GAP_SHA256
        or _sha256(payload[dialogue_end:EXPECTED_WALKMESH_PAYLOAD_OFFSET]) != DIALOGUE_GAP_SHA256
    ):
        raise SurfaceSlotMigrationError("Resident field-593 component/gap identity drifted")
    actor_array = struct.unpack_from("<I", ram, FIELD_ACTORS)[0]
    if (
        (struct.unpack_from("<I", ram, GAME_SCENE_MAP)[0] & 0xFFF) != EXPECTED_FIELD
        or struct.unpack_from("<I", ram, FIELD_NUM_ACTORS)[0] != EXPECTED_ACTOR_COUNT
        or actor_array != EXPECTED_ACTOR_ARRAY_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0] != EXPECTED_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA)[0] != EXPECTED_VM_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_ACTOR)[0] != EXPECTED_VM_ACTOR_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_CUR_DIALOGUE_FILE)[0] != EXPECTED_DIALOGUE_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SMALL_COMPONENT)[0] != EXPECTED_SMALL_COMPONENT_POINTER
    ):
        raise SurfaceSlotMigrationError("Live field-593 pointer topology drifted")
    terminal = EXPECTED_TERMINAL_ACTOR_DATA
    scheduler = EXPECTED_SCHEDULER_ACTOR_DATA
    if (
        ram[terminal + ACTOR_SCRIPT_SLOT_OFFSET : terminal + ACTOR_SCRIPT_SLOT_OFFSET + 8] != EXPECTED_TERMINAL_SLOT0
        or struct.unpack_from("<H", ram, terminal + ACTOR_CURRENT_PC_OFFSET)[0] != TERMINAL_ACTIVE_PC
        or ram[scheduler + ACTOR_SCRIPT_SLOT_OFFSET : scheduler + ACTOR_SCRIPT_SLOT_OFFSET + 8] != EXPECTED_SCHEDULER_SLOT0
        or ram[scheduler + ACTOR_CURRENT_PC_OFFSET : scheduler + ACTOR_CURRENT_PC_OFFSET + 4] != EXPECTED_SCHEDULER_CURRENT
    ):
        raise SurfaceSlotMigrationError("Active e19/e20 runtime state drifted")
    window = ram[DIALOG_WINDOWS : DIALOG_WINDOWS + DIALOG_WINDOWS_SIZE]
    if (
        _sha256(window) != EXPECTED_DIALOG_WINDOWS_SHA256
        or struct.unpack_from("<I", ram, ACTIVE_WINDOW_START_POINTER_OFFSET)[0] != EXPECTED_ACTIVE_WINDOW_START_POINTER
        or struct.unpack_from("<I", ram, ACTIVE_WINDOW_CURRENT_POINTER_OFFSET)[0] != EXPECTED_ACTIVE_WINDOW_CURRENT_POINTER
    ):
        raise SurfaceSlotMigrationError("Active dialogue-window state drifted")
    gamestate = ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE]
    if _sha256(gamestate) != EXPECTED_GAMESTATE_SHA256 or _sha256(_camera_snapshot(ram)) != EXPECTED_CAMERA_SHA256:
        raise SurfaceSlotMigrationError("GameState/camera identity drifted")
    actor_base = actor_array & 0x1FFFFFFF
    for entity, (record_sha, actor_data, data_sha) in enumerate(zip(PARTY_RECORD_SHA256, PARTY_ACTOR_DATA_POINTERS, PARTY_ACTOR_DATA_SHA256, strict=True)):
        record = actor_base + entity * FIELD_ACTOR_STRIDE
        if (
            _sha256(ram[record : record + FIELD_ACTOR_STRIDE]) != record_sha
            or (struct.unpack_from("<I", ram, record + FIELD_ACTOR_DATA_POINTER)[0] & 0x1FFFFFFF) != actor_data
            or _sha256(ram[actor_data : actor_data + 0x138]) != data_sha
        ):
            raise SurfaceSlotMigrationError(f"Party runtime e{entity} drifted")
    return {"ram_offset": ram_offset, "ram": ram, "gamestate": gamestate, "camera": _camera_snapshot(ram), "window": window}


def migrate_v214_slot1_to_v215(state: bytes, *, old_disc: Path, new_disc: Path, old_script: bytes, new_script: bytes, old_dialogue: bytes, new_dialogue: bytes, zstd: _ZstdLike) -> tuple[bytes, dict[str, object]]:
    source_sha = _sha256(state)
    if (len(state), source_sha) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise SurfaceSlotMigrationError(f"Source Slot 1 identity is {len(state)} / {source_sha}, expected {SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}")
    old_name, new_name = OLD_CUE_NAME.encode(), NEW_CUE_NAME.encode()
    if len(old_name) != len(new_name) or state.count(old_name) != 1 or state.count(new_name):
        raise SurfaceSlotMigrationError("Source CUE identity drifted")
    old_table, new_table, resident_script, resident_dialogue = _validate_resources(old_disc, new_disc, old_script, new_script, old_dialogue, new_dialogue)
    source_payload, frame_start, source_prefix = _unpack_state(state, zstd)
    if frame_start != EXPECTED_FRAME_START:
        raise SurfaceSlotMigrationError("Source frame offset drifted")
    snapshots = _validate_source(source_payload, old_table, old_script, old_dialogue)

    final = bytearray(source_payload)
    for relative, old, new in ARCHIVE_TABLE_DIFFS:
        absolute = EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + relative
        if final[absolute] != old:
            raise SurfaceSlotMigrationError("Resident archive-table source drifted")
        final[absolute] = new
    final[EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + len(resident_script)] = resident_script
    final[EXPECTED_DIALOGUE_PAYLOAD_OFFSET : EXPECTED_DIALOGUE_PAYLOAD_OFFSET + len(resident_dialogue)] = resident_dialogue
    final_payload = bytes(final)

    expected = {
        *(EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + relative for relative, _old, _new in ARCHIVE_TABLE_DIFFS),
        *(EXPECTED_SCRIPT_PAYLOAD_OFFSET + offset for offset in _diff_offsets(old_script, resident_script)),
        *(EXPECTED_DIALOGUE_PAYLOAD_OFFSET + offset for offset in _diff_offsets(old_dialogue, resident_dialogue)),
    }
    actual = _diff_offsets(source_payload, final_payload)
    if actual != tuple(sorted(expected)) or len(actual) != EXPECTED_PAYLOAD_BYTES_CHANGED:
        raise SurfaceSlotMigrationError("Migration changed bytes outside the exact 321-byte whitelist")
    if _sha256(final_payload) != EXPECTED_OUTPUT_PAYLOAD_SHA256:
        raise SurfaceSlotMigrationError("Final payload identity drifted")
    expected_table = new_table[:-1] + bytes((EXPECTED_VOLATILE_TABLE_VALUE,))
    if final_payload[EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET : EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE] != expected_table:
        raise SurfaceSlotMigrationError("Volatile archive-table tail was not preserved")
    # Prove both active pointers still target valid bytes after replacement.
    active_start = (EXPECTED_ACTIVE_WINDOW_START_POINTER & 0x1FFFFFFF) + EXPECTED_RAM_PAYLOAD_OFFSET
    active_current = (EXPECTED_ACTIVE_WINDOW_CURRENT_POINTER & 0x1FFFFFFF) + EXPECTED_RAM_PAYLOAD_OFFSET
    if final_payload[active_start : active_start + 4] != resident_dialogue[0x1445:0x1449] or final_payload[active_current] != 0:
        raise SurfaceSlotMigrationError("Active window pointer targets became invalid")

    result = _pack_state(source_prefix.replace(old_name, new_name), final_payload, zstd)
    verified_payload, verified_frame, verified_prefix = _unpack_state(result, zstd)
    if (
        verified_payload != final_payload
        or verified_frame != frame_start
        or verified_prefix != _expected_prefix(source_prefix, compressed_size=len(result) - frame_start)
        or result.count(old_name) != 0
        or result.count(new_name) != 1
    ):
        raise SurfaceSlotMigrationError("Final V215 state failed exact round trip")
    _result_ram_offset, result_ram = _ram_from_payload(verified_payload)
    source_ram = snapshots["ram"]
    if (
        result_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE] != snapshots["gamestate"]
        or _camera_snapshot(result_ram) != snapshots["camera"]
        or result_ram[DIALOG_WINDOWS : DIALOG_WINDOWS + DIALOG_WINDOWS_SIZE] != snapshots["window"]
        or result_ram[EXPECTED_TERMINAL_ACTOR_DATA : EXPECTED_TERMINAL_ACTOR_DATA + 0x138] != source_ram[EXPECTED_TERMINAL_ACTOR_DATA : EXPECTED_TERMINAL_ACTOR_DATA + 0x138]
        or result_ram[EXPECTED_SCHEDULER_ACTOR_DATA : EXPECTED_SCHEDULER_ACTOR_DATA + 0x138] != source_ram[EXPECTED_SCHEDULER_ACTOR_DATA : EXPECTED_SCHEDULER_ACTOR_DATA + 0x138]
    ):
        raise SurfaceSlotMigrationError("Gameplay/dialogue runtime preservation failed")
    output_sha = _sha256(result)
    if (len(result), output_sha) != (EXPECTED_OUTPUT_SIZE, EXPECTED_OUTPUT_SHA256):
        raise SurfaceSlotMigrationError("V215 candidate identity drifted")
    return result, {
        "source_sha256": source_sha,
        "output_sha256": output_sha,
        "source_size": len(state),
        "output_size": len(result),
        "field": EXPECTED_FIELD,
        "payload_bytes_changed": len(actual),
        "archive_table_bytes_changed": len(ARCHIVE_TABLE_DIFFS),
        "resident_script_bytes_changed": len(_diff_offsets(old_script, resident_script)),
        "resident_dialogue_bytes_changed": len(_diff_offsets(old_dialogue, resident_dialogue)),
        "resident_script_size": len(resident_script),
        "resident_dialogue_size": len(resident_dialogue),
        "allocator_safe": True,
        "retired_cavity": "e14:0x03E3-0x0410",
        "choice_dialogue_id": CHOICE_DIALOGUE_ID,
        "active_window_pointers_preserved": True,
        "scheduler_e20_pc_preserved": "0x0728",
        "gamestate_party_camera_preserved": True,
        "volatile_table_tail_preserved": True,
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
        source, output = args.source.resolve(), args.output.resolve()
        paths = {name: getattr(args, name.replace("-", "_")).resolve() for name in ("old_disc", "new_disc", "old_script", "new_script", "old_dialogue", "new_dialogue", "zstd")}
        if not source.is_file():
            raise SurfaceSlotMigrationError(f"Source state does not exist: {source}")
        for label, path in paths.items():
            if not path.is_file():
                raise SurfaceSlotMigrationError(f"{label} does not exist: {path}")
        if output in (source, LIVE_SLOT1):
            raise SurfaceSlotMigrationError("Output must be separate and may not be the live Slot 1")
        if output.exists():
            raise SurfaceSlotMigrationError(f"Refusing to overwrite existing output: {output}")
        result, report = migrate_v214_slot1_to_v215(
            source.read_bytes(), old_disc=paths["old_disc"], new_disc=paths["new_disc"],
            old_script=paths["old_script"].read_bytes(), new_script=paths["new_script"].read_bytes(),
            old_dialogue=paths["old_dialogue"].read_bytes(), new_dialogue=paths["new_dialogue"].read_bytes(),
            zstd=media_migration._Zstd(paths["zstd"]),
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        if output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Written V215 candidate changed on disk")
        print(f"Wrote validated V215 candidate: {output}")
        print(json.dumps(report, indent=2, sort_keys=True))
        print("The live Slot 1 was not modified. Install only after DuckStation is fully closed.")
        return 0
    except (OSError, ValueError, media_migration.StateMigrationError, SurfaceSlotMigrationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
