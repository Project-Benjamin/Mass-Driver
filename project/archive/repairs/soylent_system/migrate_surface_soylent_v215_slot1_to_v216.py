#!/usr/bin/env python3
"""Build the exact V216 candidate from the audited post-keycard V215 Slot 1.

The source is paused in field 593 after the Quarantine keycard was accepted
and after the terminal's old EMPTY readback was closed.  The resident ATEL
script is the allocator-safe compact V215 script and must not move or change.
Only resident dialogue ID 55 is replaced, in its existing 102-byte cavity,
with V216's 90-byte medical-diagnostics payload followed by twelve Close
bytes.  The archive table and CUE identity are migrated to the V216 disc.

The helper is fail-closed, writes only a new candidate, and never writes the
live DuckStation Slot 1.
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
    FIELD_SCRIPT_MEMORY,
    FIELD_SCRIPT_VM_CUR_ACTOR,
    FIELD_SCRIPT_VM_CUR_SCRIPT_DATA,
    GAME_STATE,
    RAM_SIZE,
    _psx_ram_offset,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIVE_SLOT1 = (PROJECT_ROOT / "emulator_data" / "SLUS-00669_1.sav").resolve()

SOURCE_STATE_SIZE = 1_863_440
SOURCE_STATE_SHA256 = "ca850361c46ae503dce3b3d7cc0f456dc5cb1d271a07b26adfa7831de2e5810e"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "98de74c2f9646c3669b7941f20adb0e30494757b510961fe80ed76a84fca2b5b"
EXPECTED_FRAME_START = 0xA6FA
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
SOURCE_RAM_SHA256 = "a68a5beca858cc7f38eebb44f4111af5ebf76ce71cf6045781112ad2c92fb32d"
OUTPUT_RAM_SHA256 = "1401adc62b06ef09505e5871671d47447cf943cc68e4cecb996ce7b6da0c679c"

OLD_DISC_SIZE = NEW_DISC_SIZE = 698_642_784
OLD_DISC_SHA256 = "2ebd33059188333895db4ec2a2fbe80568d9707cfb7a464ebe49c4fa8d6af1c3"
NEW_DISC_SHA256 = "3764d6584fce3f590298cdc4e752432f4da1ec7770aa3416141296e6a79b4498"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v215.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v216.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = "fbce922f0018ae7ac6698e6c49b5d0e782659f4f2b9bcb87b23b99622157c275"
NEW_CUE_SHA256 = "5019b53f2c2ffa5e7b3a52cd194da14b2f36ba8207b5dd2c9210d7d77afce722"

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = "6c97368f1892d1f0dcf24d739fb5ce13f6e255f8310a5bb9cf8971c1ff50e541"
NEW_ARCHIVE_TABLE_SHA256 = "573f7d4f8dfb68f9ff408124a321a238bc07565d22c26a1355594f0fbffc15ab"
ARCHIVE_TABLE_DIFFS = ((0x30E0, 0x88, 0x94),)
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
EXPECTED_VOLATILE_TABLE_VALUE = 0xE0
SOURCE_RESIDENT_TABLE_SHA256 = "2ab5e29313023b7eba2fd4a3d089293e3edb0b96fc78429bbe5c570abb0e65e6"
OUTPUT_RESIDENT_TABLE_SHA256 = "734c6f92419c1aa5917567a9f774cca2429287f07697551a470fd347d0da7ac6"

OLD_SCRIPT_SIZE = NEW_SCRIPT_SIZE = 3_421
OLD_SCRIPT_SHA256 = NEW_SCRIPT_SHA256 = "99b1323786e554f3bdaff39ba08bfcf8b27d2c7640558ff5984de8fe1cd8daad"
RESIDENT_SCRIPT_SIZE = 3_392
RESIDENT_SCRIPT_SHA256 = "62ade3971f6caa319652757a3138e1509f5abff9239bc0fb597d0c4cc82badff"
EXPECTED_SCRIPT_PAYLOAD_OFFSET = 0x10CD56
EXPECTED_SCRIPT_GUEST_POINTER = 0x8010B2F4
EXPECTED_VM_SCRIPT_GUEST_POINTER = 0x8010B8B8
SCRIPT_ALLOCATED_CAPACITY = 0x0D50
SCRIPT_GAP_SIZE = 48
SCRIPT_GAP_SHA256 = "3edf0e090fcbc4fa185663d9af64830047f1408d1e7d3fa8db1eb5bc50674e41"

OLD_DIALOGUE_SIZE = NEW_DIALOGUE_SIZE = 5_488
OLD_DIALOGUE_SHA256 = "afad9f8c0e8b9b3418ad501a6260e666537a6a5d305d449925ec26e3712f5770"
NEW_DIALOGUE_SHA256 = "f875da417daab6b7d8f76e4d318efe99d90f4e813debbcdf5c1324a155e67636"
SOURCE_RESIDENT_DIALOGUE_SIZE = OUTPUT_RESIDENT_DIALOGUE_SIZE = 5_474
SOURCE_RESIDENT_DIALOGUE_SHA256 = "a8d562582b5a6d8768cce8b7b7678a8b7a38ad087ab47e988a581b1a4051c3f9"
OUTPUT_RESIDENT_DIALOGUE_SHA256 = "3e7c7efacf25102e43ac08d3bc64f2bf9d90cb04eb18470c1fd6c2f51a5dbdda"
EXPECTED_DIALOGUE_PAYLOAD_OFFSET = 0x10DAC6
EXPECTED_DIALOGUE_GUEST_POINTER = 0x8010C064
DIALOGUE_ALLOCATED_CAPACITY = 5_492
EXPECTED_WALKMESH_PAYLOAD_OFFSET = 0x10F042
DIALOGUE_GAP_SIZE = 26
DIALOGUE_GAP_SHA256 = "7ba2053e722728bc8ac47e00ab36580454e6264cad00c524d149649e9c279c46"

DIAGNOSTIC_DIALOGUE_ID = 55
RESIDENT_ID55_OFFSET = 0x14FC
RESIDENT_ID55_CAPACITY = 102
V215_ID55_PAYLOAD_SIZE = V216_ID55_PAYLOAD_SIZE = 90
V215_ID55_PAYLOAD_SHA256 = "759b45be90d3dc0ba0ade0b6b6578de58f95f39b0e38b437b922c3d0f0592319"
V216_ID55_PAYLOAD_SHA256 = "05552f996c37467bbc945672d3cabf80a1103d6963a69f741e5ce1f242ca6cf3"
DIAGNOSTIC_GRID = (58, 4)
DIAGNOSTIC_TEXT = (
    "MEDICAL DIAGNOSTICS\n"
    "Pulse 64 / BP 118/72\n"
    "Temp 36.8 C / Resp 14\n"
    "Neural activity: ELEVATED.<Close>"
)

EXPECTED_FIELD = 593
EXPECTED_ACTOR_COUNT = 35
EXPECTED_ACTOR_ARRAY_GUEST_POINTER = 0x80112DB0
TERMINAL_ENTITY = 19
SCHEDULER_ENTITY = 20
EXPECTED_TERMINAL_ACTOR_DATA = 0x115B78
EXPECTED_SCHEDULER_ACTOR_DATA = 0x115D30
ACTOR_SCRIPT_SLOT_OFFSET = 0x8C
ACTOR_CURRENT_PC_OFFSET = 0xCC
EXPECTED_TERMINAL_SLOT0 = bytes.fromhex("8C 06 00 03 FF FF 10 00")
EXPECTED_TERMINAL_CURRENT = bytes.fromhex("8C 06 00 00")
EXPECTED_SCHEDULER_SLOT0 = bytes.fromhex("28 07 00 FF FF FF 3C 00")
EXPECTED_SCHEDULER_CURRENT = bytes.fromhex("28 07 00 00")
EXPECTED_VM_ACTOR_GUEST_POINTER = 0x80115D30

FIELD_CUR_DIALOGUE_FILE = 0x0ADBF0
FIELD_SMALL_COMPONENT = 0x0ADBF4
EXPECTED_SMALL_COMPONENT_POINTER = 0x8010C04C
GAME_SCENE_MAP = 0x04F34C

DIALOG_WINDOWS = 0x0C2698
DIALOG_WINDOW_STRIDE = 0x498
DIALOG_WINDOWS_SIZE = 4 * DIALOG_WINDOW_STRIDE
DIALOG_WINDOW_STATUS_OFFSET = 0x40E
WINDOW0_START_POINTER_OFFSET = DIALOG_WINDOWS + 0xA8
WINDOW0_CURRENT_POINTER_OFFSET = DIALOG_WINDOWS + 0x34
EXPECTED_WINDOW0_START_POINTER = 0x8010D560
EXPECTED_WINDOW0_CURRENT_POINTER = 0x8010D5B9
EXPECTED_DIALOG_WINDOWS_SHA256 = "92d8f3207023b5d328ef6c68a079b772738a51d23a6ce69c2056303c45e54522"

FIELD_VARIABLE_BACKUP_OFFSET = 0x1930
FIELD_VARIABLE_BANK_SIZE = 0x400
QUARANTINE_CARD_OPERAND = 0x021A
QUARANTINE_CARD_BIT = 8
EXPECTED_QUARANTINE_WORD = 0x01FD
EXPECTED_FIELD_VARIABLE_BANK_SHA256 = "230acd24cc4105714643d631b5a3e8a0b38ea21bedb8d06349229bf28e7c5d22"
EXPECTED_GAMESTATE_SHA256 = "ec86e0f146eda0183cacfe60acd9391345a30704f6ff57658c9ab074b254bac2"
EXPECTED_CAMERA_SHA256 = "891b36be144d188e6afef23424e7e6e4447fe976485ba1983700f60f39f83c6f"
PARTY_RECORD_SHA256 = (
    "94ae9b6d64e1b0e7123d181815600ceefd386ff6380befcc29ca9ca715366b3f",
    "aa101a6ff6fc0bdc7db549abcc0eed7d7400552cd63637b99bf3b0102e0af48d",
    "817c639368e4cf4bf564af9f21943c69d739c436f1d7576d46bbff316631987e",
)
PARTY_ACTOR_DATA_POINTERS = (0x113A4C, 0x113C04, 0x113DBC)
PARTY_ACTOR_DATA_SHA256 = (
    "a0dd538fd1b13c04c8782043409f2de5baeaa310332c35a2064b201b77e211ed",
    "203f60e45af19a4d90b97ff37c9b09bf8e11fc8682995bd30c4d476513ceb18d",
    "07e6ce2fb1eda0ff1239334c48c3c09efba208a6b79fb004d3427148811d99aa",
)

EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED = 1
EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED = 0
EXPECTED_RESIDENT_DIALOGUE_BYTES_CHANGED = 84
EXPECTED_PAYLOAD_BYTES_CHANGED = 85
EXPECTED_OUTPUT_PAYLOAD_SHA256 = "8011a177acd0eae5e09a9e462604424e094e5bea0e94ad3b99855eea0a06b782"
EXPECTED_OUTPUT_SIZE = 1_685_638
EXPECTED_OUTPUT_SHA256 = "544c4c32c84412e52ddbfa8b85bfe4d79be2ae8eae9da44137584fbdfd562b40"


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output whenever a pinned V215/V216 contract drifts."""


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
    ram = payload[offset : offset + RAM_SIZE]
    if len(ram) != RAM_SIZE:
        raise SurfaceSlotMigrationError("Serialized RAM span is truncated")
    return offset, ram


def _camera_snapshot(ram: bytes) -> bytes:
    return b"".join(ram[address : address + 16] for address in CAMERA_VECTORS.values())


def _build_resident_dialogue(resident_source: bytes, old_dialogue: bytes, new_dialogue: bytes) -> bytes:
    source = parse_dialogue(resident_source)
    old = parse_dialogue(old_dialogue)
    new = parse_dialogue(new_dialogue)
    if len(source.blocks) != 56 or len(old.blocks) != 57 or len(new.blocks) != 57:
        raise SurfaceSlotMigrationError("V215/V216 dialogue count drifted")
    old_block = old.blocks[DIAGNOSTIC_DIALOGUE_ID]
    new_block = new.blocks[DIAGNOSTIC_DIALOGUE_ID]
    resident_block = source.blocks[DIAGNOSTIC_DIALOGUE_ID]
    if (
        (old_block.offset, len(old_block.payload), old_block.width, old_block.height) != (0x14D9, V215_ID55_PAYLOAD_SIZE, *DIAGNOSTIC_GRID)
        or (new_block.offset, len(new_block.payload), new_block.width, new_block.height) != (0x14D9, V216_ID55_PAYLOAD_SIZE, *DIAGNOSTIC_GRID)
        or _sha256(old_block.payload) != V215_ID55_PAYLOAD_SHA256
        or _sha256(new_block.payload) != V216_ID55_PAYLOAD_SHA256
        or (resident_block.offset, len(resident_block.payload), resident_block.width, resident_block.height)
        != (RESIDENT_ID55_OFFSET, RESIDENT_ID55_CAPACITY, *DIAGNOSTIC_GRID)
        or not resident_block.text.startswith("SOLARIS AUTHORIZATION\nAccess slot: EMPTY")
        or new_block.text != DIAGNOSTIC_TEXT
    ):
        raise SurfaceSlotMigrationError("Dialogue ID55 topology/content drifted")
    full_diffs = _diff_offsets(old_dialogue, new_dialogue)
    if len(full_diffs) != EXPECTED_RESIDENT_DIALOGUE_BYTES_CHANGED or any(
        not old_block.offset <= offset < old_block.offset + len(old_block.payload) for offset in full_diffs
    ):
        raise SurfaceSlotMigrationError("V215/V216 full dialogue changed outside ID55")
    result = bytearray(resident_source)
    result[RESIDENT_ID55_OFFSET : RESIDENT_ID55_OFFSET + RESIDENT_ID55_CAPACITY] = (
        new_block.payload + b"\x00" * (RESIDENT_ID55_CAPACITY - len(new_block.payload))
    )
    resident = bytes(result)
    parsed = parse_dialogue(resident)
    resident_diffs = _diff_offsets(resident_source, resident)
    if (
        (len(resident), _sha256(resident))
        != (OUTPUT_RESIDENT_DIALOGUE_SIZE, OUTPUT_RESIDENT_DIALOGUE_SHA256)
        or len(resident_diffs) != EXPECTED_RESIDENT_DIALOGUE_BYTES_CHANGED
        or any(not RESIDENT_ID55_OFFSET <= offset < RESIDENT_ID55_OFFSET + RESIDENT_ID55_CAPACITY for offset in resident_diffs)
        or parsed.blocks[DIAGNOSTIC_DIALOGUE_ID].text != DIAGNOSTIC_TEXT + "<Close>" * 12
    ):
        raise SurfaceSlotMigrationError("Compact V216 resident dialogue identity drifted")
    return resident


def _validate_resources(
    old_disc: Path,
    new_disc: Path,
    old_script: bytes,
    new_script: bytes,
    old_dialogue: bytes,
    new_dialogue: bytes,
) -> tuple[bytes, bytes]:
    identities = (
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V215 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V216 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V215 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V216 CUE"),
    )
    for path, size, sha, label in identities:
        if not path.is_file() or path.stat().st_size != size or _file_sha256(path) != sha:
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    blobs = (
        (old_script, OLD_SCRIPT_SIZE, OLD_SCRIPT_SHA256, "V215 script"),
        (new_script, NEW_SCRIPT_SIZE, NEW_SCRIPT_SHA256, "V216 script"),
        (old_dialogue, OLD_DIALOGUE_SIZE, OLD_DIALOGUE_SHA256, "V215 dialogue"),
        (new_dialogue, NEW_DIALOGUE_SIZE, NEW_DIALOGUE_SHA256, "V216 dialogue"),
    )
    for blob, size, sha, label in blobs:
        if (len(blob), _sha256(blob)) != (size, sha):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    if old_script != new_script:
        raise SurfaceSlotMigrationError("V216 unexpectedly changes field-593 script")
    old_editor, new_editor = AtelScript(old_script), AtelScript(new_script)
    if old_editor.entity_count != 21 or new_editor.entity_count != 21:
        raise SurfaceSlotMigrationError("Field-593 script topology drifted")
    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    diffs = tuple((i, a, b) for i, (a, b) in enumerate(zip(old_table, new_table, strict=True)) if a != b)
    if (
        _sha256(old_table) != OLD_ARCHIVE_TABLE_SHA256
        or _sha256(new_table) != NEW_ARCHIVE_TABLE_SHA256
        or diffs != ARCHIVE_TABLE_DIFFS
    ):
        raise SurfaceSlotMigrationError("V215/V216 archive-table delta drifted")
    return old_table, new_table


def _validate_source(payload: bytes, old_table: bytes) -> dict[str, object]:
    if len(payload) != SOURCE_PAYLOAD_SIZE or _sha256(payload) != SOURCE_PAYLOAD_SHA256:
        raise SurfaceSlotMigrationError("V215 decompressed payload identity drifted")
    ram_offset, ram = _ram_from_payload(payload)
    if _sha256(ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("V215 serialized RAM identity drifted")
    table_offset, volatile = media_migration._find_resident_archive_table(payload, old_table)
    resident_table = payload[table_offset : table_offset + ARCHIVE_TABLE_SIZE]
    script = payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE]
    dialogue = payload[EXPECTED_DIALOGUE_PAYLOAD_OFFSET : EXPECTED_DIALOGUE_PAYLOAD_OFFSET + SOURCE_RESIDENT_DIALOGUE_SIZE]
    if (
        table_offset != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or volatile != 1
        or _sha256(resident_table) != SOURCE_RESIDENT_TABLE_SHA256
        or resident_table != old_table[:-1] + bytes((EXPECTED_VOLATILE_TABLE_VALUE,))
        or (len(script), _sha256(script)) != (RESIDENT_SCRIPT_SIZE, RESIDENT_SCRIPT_SHA256)
        or payload.count(script) != 1
        or payload.find(script) != EXPECTED_SCRIPT_PAYLOAD_OFFSET
        or (len(dialogue), _sha256(dialogue))
        != (SOURCE_RESIDENT_DIALOGUE_SIZE, SOURCE_RESIDENT_DIALOGUE_SHA256)
        or payload.count(dialogue) != 1
        or payload.find(dialogue) != EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        or _sha256(payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET])
        != SCRIPT_GAP_SHA256
        or _sha256(payload[EXPECTED_DIALOGUE_PAYLOAD_OFFSET + SOURCE_RESIDENT_DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET])
        != DIALOGUE_GAP_SHA256
    ):
        raise SurfaceSlotMigrationError("Resident field-593 component/table/gap identity drifted")
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
        or ram[terminal + ACTOR_CURRENT_PC_OFFSET : terminal + ACTOR_CURRENT_PC_OFFSET + 4] != EXPECTED_TERMINAL_CURRENT
        or ram[scheduler + ACTOR_SCRIPT_SLOT_OFFSET : scheduler + ACTOR_SCRIPT_SLOT_OFFSET + 8] != EXPECTED_SCHEDULER_SLOT0
        or ram[scheduler + ACTOR_CURRENT_PC_OFFSET : scheduler + ACTOR_CURRENT_PC_OFFSET + 4] != EXPECTED_SCHEDULER_CURRENT
    ):
        raise SurfaceSlotMigrationError("e19/e20 runtime state drifted")
    windows = ram[DIALOG_WINDOWS : DIALOG_WINDOWS + DIALOG_WINDOWS_SIZE]
    if (
        _sha256(windows) != EXPECTED_DIALOG_WINDOWS_SHA256
        or any(struct.unpack_from("<h", ram, DIALOG_WINDOWS + i * DIALOG_WINDOW_STRIDE + DIALOG_WINDOW_STATUS_OFFSET)[0] != -1 for i in range(4))
        or struct.unpack_from("<I", ram, WINDOW0_START_POINTER_OFFSET)[0] != EXPECTED_WINDOW0_START_POINTER
        or struct.unpack_from("<I", ram, WINDOW0_CURRENT_POINTER_OFFSET)[0] != EXPECTED_WINDOW0_CURRENT_POINTER
    ):
        raise SurfaceSlotMigrationError("Closed dialogue-window state drifted")
    gamestate = ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE]
    field_bank = ram[FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE]
    backup_bank = ram[
        GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET : GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET + FIELD_VARIABLE_BANK_SIZE
    ]
    if (
        _sha256(gamestate) != EXPECTED_GAMESTATE_SHA256
        or field_bank != backup_bank
        or _sha256(field_bank) != EXPECTED_FIELD_VARIABLE_BANK_SHA256
        or struct.unpack_from("<H", field_bank, QUARANTINE_CARD_OPERAND)[0] != EXPECTED_QUARANTINE_WORD
        or not (struct.unpack_from("<H", field_bank, QUARANTINE_CARD_OPERAND)[0] & (1 << QUARANTINE_CARD_BIT))
        or _sha256(_camera_snapshot(ram)) != EXPECTED_CAMERA_SHA256
    ):
        raise SurfaceSlotMigrationError("GameState/card/camera identity drifted")
    actor_base = actor_array & 0x1FFFFFFF
    for entity, (record_sha, actor_data, data_sha) in enumerate(
        zip(PARTY_RECORD_SHA256, PARTY_ACTOR_DATA_POINTERS, PARTY_ACTOR_DATA_SHA256, strict=True)
    ):
        record = actor_base + entity * FIELD_ACTOR_STRIDE
        if (
            _sha256(ram[record : record + FIELD_ACTOR_STRIDE]) != record_sha
            or (struct.unpack_from("<I", ram, record + FIELD_ACTOR_DATA_POINTER)[0] & 0x1FFFFFFF) != actor_data
            or _sha256(ram[actor_data : actor_data + 0x138]) != data_sha
        ):
            raise SurfaceSlotMigrationError(f"Party runtime e{entity} drifted")
    return {
        "ram_offset": ram_offset,
        "ram": ram,
        "script": script,
        "dialogue": dialogue,
        "gamestate": gamestate,
        "field_bank": field_bank,
        "camera": _camera_snapshot(ram),
        "windows": windows,
    }


def migrate_v215_slot1_to_v216(
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
    source_sha = _sha256(state)
    if (len(state), source_sha) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise SurfaceSlotMigrationError(
            f"Source Slot 1 identity is {len(state)} / {source_sha}, expected {SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    old_name, new_name = OLD_CUE_NAME.encode(), NEW_CUE_NAME.encode()
    if len(old_name) != len(new_name) or state.count(old_name) != 1 or state.count(new_name):
        raise SurfaceSlotMigrationError("Source CUE identity drifted")
    old_table, new_table = _validate_resources(
        old_disc, new_disc, old_script, new_script, old_dialogue, new_dialogue
    )
    source_payload, frame_start, source_prefix = _unpack_state(state, zstd)
    if frame_start != EXPECTED_FRAME_START:
        raise SurfaceSlotMigrationError("Source frame offset drifted")
    snapshots = _validate_source(source_payload, old_table)
    resident_dialogue = _build_resident_dialogue(snapshots["dialogue"], old_dialogue, new_dialogue)

    final = bytearray(source_payload)
    for relative, old, new in ARCHIVE_TABLE_DIFFS:
        absolute = EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + relative
        if final[absolute] != old:
            raise SurfaceSlotMigrationError("Resident archive-table source drifted")
        final[absolute] = new
    final[
        EXPECTED_DIALOGUE_PAYLOAD_OFFSET : EXPECTED_DIALOGUE_PAYLOAD_OFFSET + OUTPUT_RESIDENT_DIALOGUE_SIZE
    ] = resident_dialogue
    final_payload = bytes(final)

    dialogue_diffs = _diff_offsets(snapshots["dialogue"], resident_dialogue)
    expected = {
        *(EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + relative for relative, _old, _new in ARCHIVE_TABLE_DIFFS),
        *(EXPECTED_DIALOGUE_PAYLOAD_OFFSET + offset for offset in dialogue_diffs),
    }
    actual = _diff_offsets(source_payload, final_payload)
    if actual != tuple(sorted(expected)) or len(actual) != EXPECTED_PAYLOAD_BYTES_CHANGED:
        raise SurfaceSlotMigrationError("Migration changed bytes outside the exact 85-byte whitelist")
    if _sha256(final_payload) != EXPECTED_OUTPUT_PAYLOAD_SHA256:
        raise SurfaceSlotMigrationError("Final payload identity drifted")
    expected_table = new_table[:-1] + bytes((EXPECTED_VOLATILE_TABLE_VALUE,))
    final_table = final_payload[
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET : EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
    ]
    if final_table != expected_table or _sha256(final_table) != OUTPUT_RESIDENT_TABLE_SHA256:
        raise SurfaceSlotMigrationError("Volatile V216 archive-table tail was not preserved")

    result = _pack_state(source_prefix.replace(old_name, new_name), final_payload, zstd)
    verified_payload, verified_frame, verified_prefix = _unpack_state(result, zstd)
    if (
        verified_payload != final_payload
        or verified_frame != frame_start
        or verified_prefix != _expected_prefix(source_prefix, compressed_size=len(result) - frame_start)
        or result.count(old_name) != 0
        or result.count(new_name) != 1
    ):
        raise SurfaceSlotMigrationError("Final V216 state failed exact round trip")
    _result_ram_offset, result_ram = _ram_from_payload(verified_payload)
    source_ram = snapshots["ram"]
    if _sha256(result_ram) != OUTPUT_RAM_SHA256:
        raise SurfaceSlotMigrationError("Final V216 serialized RAM identity drifted")
    preserved_spans = (
        (GAME_STATE, GAMESTATE_SIZE, "GameState"),
        (FIELD_SCRIPT_MEMORY, FIELD_VARIABLE_BANK_SIZE, "active field variables"),
        (DIALOG_WINDOWS, DIALOG_WINDOWS_SIZE, "dialogue windows"),
        (EXPECTED_TERMINAL_ACTOR_DATA, 0x138, "e19 runtime"),
        (EXPECTED_SCHEDULER_ACTOR_DATA, 0x138, "e20 runtime"),
    )
    for start, size, label in preserved_spans:
        if result_ram[start : start + size] != source_ram[start : start + size]:
            raise SurfaceSlotMigrationError(f"{label} was not preserved")
    if _camera_snapshot(result_ram) != snapshots["camera"]:
        raise SurfaceSlotMigrationError("Camera was not preserved")
    actor_base = EXPECTED_ACTOR_ARRAY_GUEST_POINTER & 0x1FFFFFFF
    for entity in range(3):
        record = actor_base + entity * FIELD_ACTOR_STRIDE
        actor_data = struct.unpack_from("<I", source_ram, record + FIELD_ACTOR_DATA_POINTER)[0] & 0x1FFFFFFF
        if (
            result_ram[record : record + FIELD_ACTOR_STRIDE] != source_ram[record : record + FIELD_ACTOR_STRIDE]
            or result_ram[actor_data : actor_data + 0x138] != source_ram[actor_data : actor_data + 0x138]
        ):
            raise SurfaceSlotMigrationError(f"Party runtime e{entity} was not preserved")
    if (
        final_payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE]
        != snapshots["script"]
        or final_payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET]
        != source_payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET]
        or final_payload[EXPECTED_DIALOGUE_PAYLOAD_OFFSET + OUTPUT_RESIDENT_DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET]
        != source_payload[EXPECTED_DIALOGUE_PAYLOAD_OFFSET + SOURCE_RESIDENT_DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET]
    ):
        raise SurfaceSlotMigrationError("Allocator/component neighbors changed")
    # Both stale pointers belong to closed window 0 and remain valid in ID55.
    start_relative = (EXPECTED_WINDOW0_START_POINTER & 0x1FFFFFFF) - (EXPECTED_DIALOGUE_GUEST_POINTER & 0x1FFFFFFF)
    current_relative = (EXPECTED_WINDOW0_CURRENT_POINTER & 0x1FFFFFFF) - (EXPECTED_DIALOGUE_GUEST_POINTER & 0x1FFFFFFF)
    if (
        start_relative != RESIDENT_ID55_OFFSET
        or current_relative != RESIDENT_ID55_OFFSET + V216_ID55_PAYLOAD_SIZE - 1
        or resident_dialogue[current_relative] != 0
    ):
        raise SurfaceSlotMigrationError("Closed window's ID55 pointers became invalid")

    output_sha = _sha256(result)
    if (len(result), output_sha) != (EXPECTED_OUTPUT_SIZE, EXPECTED_OUTPUT_SHA256):
        raise SurfaceSlotMigrationError("V216 candidate identity drifted")
    return result, {
        "source_sha256": source_sha,
        "output_sha256": output_sha,
        "source_size": len(state),
        "output_size": len(result),
        "field": EXPECTED_FIELD,
        "payload_bytes_changed": len(actual),
        "archive_table_bytes_changed": len(ARCHIVE_TABLE_DIFFS),
        "resident_script_bytes_changed": 0,
        "resident_dialogue_bytes_changed": len(dialogue_diffs),
        "resident_script_size": RESIDENT_SCRIPT_SIZE,
        "resident_dialogue_size": len(resident_dialogue),
        "diagnostic_dialogue_id": DIAGNOSTIC_DIALOGUE_ID,
        "allocator_safe": True,
        "card_word_preserved": f"0x{EXPECTED_QUARANTINE_WORD:04X}",
        "all_windows_closed": True,
        "closed_window_pointers_preserved": True,
        "terminal_e19_pc_preserved": "0x068C",
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
        paths = {
            name: getattr(args, name).resolve()
            for name in ("old_disc", "new_disc", "old_script", "new_script", "old_dialogue", "new_dialogue", "zstd")
        }
        if not source.is_file():
            raise SurfaceSlotMigrationError(f"Source state does not exist: {source}")
        for label, path in paths.items():
            if not path.is_file():
                raise SurfaceSlotMigrationError(f"{label} does not exist: {path}")
        if output in (source, LIVE_SLOT1):
            raise SurfaceSlotMigrationError("Output must be separate and may not be the live Slot 1")
        if output.exists():
            raise SurfaceSlotMigrationError(f"Refusing to overwrite existing output: {output}")
        result, report = migrate_v215_slot1_to_v216(
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
            raise SurfaceSlotMigrationError("Written V216 candidate changed on disk")
        print(f"Wrote validated V216 candidate: {output}")
        print(json.dumps(report, indent=2, sort_keys=True))
        print("The live Slot 1 was not modified. Install only after DuckStation is fully closed.")
        return 0
    except (OSError, ValueError, media_migration.StateMigrationError, SurfaceSlotMigrationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
