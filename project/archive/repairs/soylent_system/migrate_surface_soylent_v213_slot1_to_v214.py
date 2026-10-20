#!/usr/bin/env python3
"""Create a validated V214 candidate from the audited live V213 Slot 1.

The source is resident in field 550 with entity 4 paused on WAIT_DIALOG inside
its patient-record action.  V214 moves that live carrier to the real terminal
and adds retired entities 5 and 6 as two more frontage carriers.  This helper
therefore patches entity 4 in place, queues the new entity-5/entity-6
initializers for the normal field scheduler, and replaces the equal-length
resident ATEL component.  It deliberately leaves entity 4's active action,
dialogue state, GameState, sprites, and volatile resident archive-table tail
untouched.  It never writes Slot 1.
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

SOURCE_STATE_SIZE = 1_567_694
SOURCE_STATE_SHA256 = (
    "3c2e76d52ec7bfffa613766e98ce2ce6a84f8991722bd9b2c65839926723197e"
)
SOURCE_PAYLOAD_SHA256 = (
    "0ec7618c371d6464d6d70e797f5c1a108702df78703090d79da95b3887557f4e"
)
OLD_DISC_SIZE = 698_642_784
OLD_DISC_SHA256 = (
    "9a2d781630e265af0f51ca01a801372d2766018f79a0bb5637818298c2b7e684"
)
NEW_DISC_SIZE = 698_642_784
NEW_DISC_SHA256 = (
    "b3bdc04631d89e44353e5f6d02f672a8237111189015675a4efcaab41f54ace8"
)
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v213.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v214.cue"
OLD_CUE_SIZE = 112
OLD_CUE_SHA256 = (
    "03c0ec7f3647ba91801dec48841ff9b1685cf23be2e5ca833f83a454e849dd71"
)
NEW_CUE_SIZE = 112
NEW_CUE_SHA256 = (
    "b6a0d53c65e5205a9e8f3505091e8f6c2e91d3a0330642a15031e5293cdf7f2c"
)

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = (
    "fae7429ff90b782c6beab4b43056012487af6b611db17fcb2be1b43a7111095f"
)
NEW_ARCHIVE_TABLE_SHA256 = (
    "10121240c6e8f4c6d724959518744178fad6987a72339a7f7b03b66c1417f454"
)
ARCHIVE_TABLE_DIFFS = ((0x2E86, 0xB4, 0xC0),)
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
EXPECTED_ARCHIVE_TABLE_CHANGED_PAYLOAD_OFFSET = 0x148EC
EXPECTED_VOLATILE_TABLE_PAYLOAD_OFFSET = 0x19A65
EXPECTED_VOLATILE_TABLE_VALUE = 0xE0

SCRIPT_SIZE = 5_414
OLD_SCRIPT_SHA256 = (
    "13da59f3ed7a31e67e411bc695d2e6b991f68cfcf482f002478be0505b3765b5"
)
NEW_SCRIPT_SHA256 = (
    "544e77f06e8e3e3a0f14e48399a2d105c0fa4227ffeed3ae864407302e832e86"
)
SCRIPT_DIFFS = (
    (0x01C4, 0x8C, 0xF1),
    (0x01C5, 0x06, 0x05),
    (0x01C8, 0x8C, 0x68),
    (0x01C9, 0x06, 0x05),
    (0x0204, 0x8C, 0x0E),
    (0x0208, 0x8C, 0x68),
    (0x0209, 0x06, 0x05),
    (0x0BD3, 0x46, 0x50),
    (0x0BD5, 0x71, 0x59),
    (0x0BDF, 0x07, 0x03),
    (0x0BE3, 0x18, 0x01),
    (0x0BE6, 0x0F, 0x01),
    (0x0C75, 0x00, 0x0B),
    (0x0C77, 0x00, 0x80),
    (0x0C78, 0x00, 0x19),
    (0x0C79, 0x00, 0x74),
    (0x0C7B, 0x00, 0x59),
    (0x0C7C, 0x00, 0xFF),
    (0x0C7D, 0x00, 0xC0),
    (0x0C7E, 0x00, 0x1A),
    (0x0C80, 0x00, 0xF8),
    (0x0C83, 0x00, 0x20),
    (0x0C84, 0x00, 0xF8),
    (0x0C85, 0x00, 0x03),
    (0x0C86, 0x00, 0x04),
    (0x0C88, 0x00, 0x18),
    (0x0C89, 0x00, 0x01),
    (0x0C8A, 0x00, 0x0F),
    (0x0C8B, 0x00, 0x64),
    (0x0C8C, 0x00, 0x01),
    (0x0C8D, 0x00, 0x20),
    (0x0C8E, 0x00, 0x01),
    (0x0C8F, 0x00, 0x80),
    (0x0C90, 0x00, 0x23),
    (0x0C92, 0x00, 0x0B),
    (0x0C94, 0x00, 0x80),
    (0x0C95, 0x00, 0x19),
    (0x0C96, 0x00, 0x98),
    (0x0C98, 0x00, 0x59),
    (0x0C99, 0x00, 0xFF),
    (0x0C9A, 0x00, 0xC0),
    (0x0C9B, 0x00, 0x1A),
    (0x0C9D, 0x00, 0xF8),
    (0x0CA0, 0x00, 0x20),
    (0x0CA1, 0x00, 0xF8),
    (0x0CA2, 0x00, 0x03),
    (0x0CA3, 0x00, 0x04),
    (0x0CA5, 0x00, 0x18),
    (0x0CA6, 0x00, 0x01),
    (0x0CA7, 0x00, 0x0F),
    (0x0CA8, 0x00, 0x64),
    (0x0CA9, 0x00, 0x01),
    (0x0CAA, 0x00, 0x20),
    (0x0CAB, 0x00, 0x01),
    (0x0CAC, 0x00, 0x80),
    (0x0CAD, 0x00, 0x23),
)
DIALOGUE_SIZE = 6_056
DIALOGUE_SHA256 = (
    "3c1f8cc6906384c6a9a0bb23ee5710bde6a524f656baa4b6ac8c49659d51bc4e"
)

EXPECTED_FRAME_START = 0x9D05
EXPECTED_PAYLOAD_SIZE = 3_819_109
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
EXPECTED_SCRIPT_PAYLOAD_OFFSET = 0x10CD56
EXPECTED_DIALOGUE_PAYLOAD_OFFSET = 0x10E2AE
EXPECTED_SCRIPT_GUEST_POINTER = 0x8010B2F4
EXPECTED_VM_SCRIPT_GUEST_POINTER = 0x8010B978
EXPECTED_VM_ACTOR_GUEST_POINTER = 0x801170E0

GAME_SCENE_MAP = 0x04F34C
EXPECTED_FIELD = 550
EXPECTED_ACTOR_COUNT = 38
EXPECTED_ACTOR_ARRAY_GUEST_POINTER = 0x80113B24
TERMINAL_ENTITY = 4
TERMINAL_ENTITIES = (4, 5, 6)
EXPECTED_TERMINAL_RECORD = 0x113C94
EXPECTED_TERMINAL_ACTOR_DATA = 0x114FB4
EXPECTED_TERMINAL_RECORDS = (0x113C94, 0x113CF0, 0x113D4C)
EXPECTED_TERMINAL_ACTOR_DATA_OFFSETS = (0x114FB4, 0x11516C, 0x115324)
EXPECTED_TERMINAL_SPRITE_POINTERS = (0x80129BA0, 0x80129DEC, 0x8012A038)
EXPECTED_TERMINAL_SPRITE_SHA256 = (
    "1bad6dcfd963229f92ca77c56c90738f04a25e841e7b497f994618a296a58342",
    "ea1592eaaf2b45c68bdd34bc828ce0deb45827124d6d238bca6580c4f0ee3944",
    "e55bf95950ef433fa3bff51a454a210d08300461d3e3b047f68718b9efb82622",
)
TERMINAL_SPRITE_RUNTIME_SIZE = 0x24C

ACTOR_RECORD_STATUS_OFFSET = 0x58
ACTOR_DATA_FLAGS_OFFSET = 0x04
ACTOR_DATA_SURFACES_OFFSET = 0x08
ACTOR_DATA_BOUNDS_OFFSET = 0x18
ACTOR_DATA_POSITION_OFFSET = 0x20
ACTOR_DATA_OLD_POSITION_OFFSET = 0x68
ACTOR_SCRIPT_SLOT_OFFSET = 0x8C
ACTOR_CURRENT_PC_OFFSET = 0xCC
TERMINAL_INIT_PC = 0x054B
TERMINAL_INIT_PCS = (0x054B, 0x05F1, 0x060E)
TERMINAL_ACTION_PC = 0x0568
TERMINAL_ACTION_END_PC = 0x05F1
TERMINAL_PAYLOAD_END_PC = 0x062B
TERMINAL_CAVITY_END_PC = 0x0649
TERMINAL_SHARED_STOP_PC = 0x068C
TERMINAL_ACTIVE_PC = 0x05CF
TERMINAL_ACTIVE_DIALOGUE_BODY = bytes.fromhex("D2 02 00 00 9C")
NEW_AUX_TERMINAL_INIT_BODIES = (
    bytes.fromhex(
        "0B 00 80 19 74 00 59 FF C0 1A 00 F8 00 00 20 "
        "F8 03 04 00 18 01 0F 64 01 20 01 80 23 00"
    ),
    bytes.fromhex(
        "0B 00 80 19 98 00 59 FF C0 1A 00 F8 00 00 20 "
        "F8 03 04 00 18 01 0F 64 01 20 01 80 23 00"
    ),
)
OLD_AUX_TERMINAL_RECORD_STATUS = bytes.fromhex("E0 01")
NEW_AUX_TERMINAL_RECORD_STATUS = bytes.fromhex("60 02")
OLD_AUX_TERMINAL_FLAGS = bytes.fromhex("00 08 00 04")
NEW_AUX_TERMINAL_FLAGS = bytes.fromhex("00 08 00 00")
OLD_AUX_TERMINAL_SLOT0 = bytes.fromhex("8C 06 00 FF FF FF 3C 00")
NEW_AUX_TERMINAL_SLOT0 = (
    bytes.fromhex("F1 05 00 00 FF FF 1C 00"),
    bytes.fromhex("0E 06 00 00 FF FF 1C 00"),
)

EXPECTED_GAMESTATE_SHA256 = (
    "72d598eb11f6d9ca9e79042fd1276737dc86b3e79de9f611355c5994508e0aa8"
)

# Absolute offsets in the decompressed DuckStation payload.  Each tuple is
# (offset, exact V213 bytes, exact V214 bytes, description).  Entity 4 is
# patched directly because its action is live.  Entities 5 and 6 are queued at
# their new initializer PCs, matching the scheduler-safe V212->V213 handoff.
# Multi-byte fields are written as units even where only one byte changes.
RUNTIME_PATCHES = (
    (0x115716, bytes.fromhex("46 00 00 00"), bytes.fromhex("50 00 00 00"), "record matrix 0 X"),
    (0x11571E, bytes.fromhex("71 FF FF FF"), bytes.fromhex("59 FF FF FF"), "record matrix 0 Z"),
    (0x115736, bytes.fromhex("46 00 00 00"), bytes.fromhex("50 00 00 00"), "record matrix 1 X"),
    (0x11573E, bytes.fromhex("71 FF FF FF"), bytes.fromhex("59 FF FF FF"), "record matrix 1 Z"),
    (
        0x116A1A,
        bytes.fromhex("00 00 00 00"),
        bytes.fromhex("00 00 04 00"),
        "ActorData m4 facing flag",
    ),
    (0x116A2E, bytes.fromhex("30 00"), bytes.fromhex("02 00"), "ActorData X diameter"),
    (0x116A34, bytes.fromhex("1E 00"), bytes.fromhex("02 00"), "ActorData minimum diameter"),
    (0x116A36, bytes.fromhex("00 00 46 00"), bytes.fromhex("00 00 50 00"), "ActorData current X"),
    (0x116A3E, bytes.fromhex("00 00 71 FF"), bytes.fromhex("00 00 59 FF"), "ActorData current Z"),
    (0x116A7E, bytes.fromhex("46 00"), bytes.fromhex("50 00"), "ActorData old X"),
    (0x116A82, bytes.fromhex("71 FF"), bytes.fromhex("59 FF"), "ActorData old Z"),
    (0x1157AA, OLD_AUX_TERMINAL_RECORD_STATUS, NEW_AUX_TERMINAL_RECORD_STATUS, "e5 record status"),
    (0x116BD2, OLD_AUX_TERMINAL_FLAGS, NEW_AUX_TERMINAL_FLAGS, "e5 ActorData flags"),
    (0x116C5A, OLD_AUX_TERMINAL_SLOT0, NEW_AUX_TERMINAL_SLOT0[0], "e5 queued initializer"),
    (0x115806, OLD_AUX_TERMINAL_RECORD_STATUS, NEW_AUX_TERMINAL_RECORD_STATUS, "e6 record status"),
    (0x116D8A, OLD_AUX_TERMINAL_FLAGS, NEW_AUX_TERMINAL_FLAGS, "e6 ActorData flags"),
    (0x116E12, OLD_AUX_TERMINAL_SLOT0, NEW_AUX_TERMINAL_SLOT0[1], "e6 queued initializer"),
)
EXPECTED_SCRIPT_BYTES_CHANGED = 56
EXPECTED_RUNTIME_BYTES_CHANGED = 24
EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED = 1
EXPECTED_PAYLOAD_BYTES_CHANGED = 81

EXPECTED_OUTPUT_SIZE = 1_433_243
EXPECTED_OUTPUT_SHA256 = (
    "d4617725cfb7c46c71f0555805632827c056f48aa4935e88d96c2092cad2a047"
)


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output whenever a pinned V213/V214 contract drifts."""


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
        for offset, (old, new) in enumerate(zip(before, after, strict=True))
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
    if (
        old_disc.stat().st_size != OLD_DISC_SIZE
        or _file_sha256(old_disc) != OLD_DISC_SHA256
    ):
        raise SurfaceSlotMigrationError("V213 disc identity drifted")
    if (
        new_disc.stat().st_size != NEW_DISC_SIZE
        or _file_sha256(new_disc) != NEW_DISC_SHA256
    ):
        raise SurfaceSlotMigrationError("V214 disc identity drifted")
    cue_resources = (
        (
            old_disc.with_name(OLD_CUE_NAME),
            OLD_CUE_SIZE,
            OLD_CUE_SHA256,
            "V213 CUE",
        ),
        (
            new_disc.with_name(NEW_CUE_NAME),
            NEW_CUE_SIZE,
            NEW_CUE_SHA256,
            "V214 CUE",
        ),
    )
    for path, size, sha256, label in cue_resources:
        if (
            not path.is_file()
            or path.stat().st_size != size
            or _file_sha256(path) != sha256
        ):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    expected = (
        (old_script, SCRIPT_SIZE, OLD_SCRIPT_SHA256, "V213 script"),
        (new_script, SCRIPT_SIZE, NEW_SCRIPT_SHA256, "V214 script"),
        (old_dialogue, DIALOGUE_SIZE, DIALOGUE_SHA256, "V213 dialogue"),
        (new_dialogue, DIALOGUE_SIZE, DIALOGUE_SHA256, "V214 dialogue"),
    )
    for data, size, sha256, label in expected:
        if (len(data), _sha256(data)) != (size, sha256):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    if old_dialogue != new_dialogue:
        raise SurfaceSlotMigrationError("V214 dialogue is not byte-identical to V213")
    if _diff_triplets(old_script, new_script) != SCRIPT_DIFFS:
        raise SurfaceSlotMigrationError(
            "V214 script is not the exact three-carrier init delta"
        )

    old_editor = AtelScript(old_script)
    new_editor = AtelScript(new_script)
    if (
        old_editor.entity_count != 24
        or new_editor.entity_count != old_editor.entity_count
        or new_editor.bytecode_size != old_editor.bytecode_size
        or tuple(
            old_editor.get_script_pointer(entity, 0)
            for entity in TERMINAL_ENTITIES
        )
        != (TERMINAL_INIT_PC, TERMINAL_SHARED_STOP_PC, TERMINAL_SHARED_STOP_PC)
        or tuple(
            new_editor.get_script_pointer(entity, 0)
            for entity in TERMINAL_ENTITIES
        )
        != TERMINAL_INIT_PCS
        or tuple(
            old_editor.get_script_pointer(entity, 2)
            for entity in TERMINAL_ENTITIES
        )
        != (TERMINAL_ACTION_PC, TERMINAL_SHARED_STOP_PC, TERMINAL_SHARED_STOP_PC)
        or tuple(
            new_editor.get_script_pointer(entity, 2)
            for entity in TERMINAL_ENTITIES
        )
        != (TERMINAL_ACTION_PC,) * len(TERMINAL_ENTITIES)
        or old_editor.bytecode[TERMINAL_ACTION_PC:TERMINAL_ACTION_END_PC]
        != new_editor.bytecode[TERMINAL_ACTION_PC:TERMINAL_ACTION_END_PC]
        or old_editor.bytecode[TERMINAL_ACTION_END_PC:TERMINAL_PAYLOAD_END_PC]
        != b"\x00" * (TERMINAL_PAYLOAD_END_PC - TERMINAL_ACTION_END_PC)
        or tuple(
            new_editor.bytecode[pc : pc + len(body)]
            for pc, body in zip(
                TERMINAL_INIT_PCS[1:],
                NEW_AUX_TERMINAL_INIT_BODIES,
                strict=True,
            )
        )
        != NEW_AUX_TERMINAL_INIT_BODIES
        or old_editor.bytecode[TERMINAL_PAYLOAD_END_PC:TERMINAL_CAVITY_END_PC]
        != new_editor.bytecode[TERMINAL_PAYLOAD_END_PC:TERMINAL_CAVITY_END_PC]
        or old_editor.bytecode[TERMINAL_ACTIVE_PC] != 0x9C
        or new_editor.bytecode[TERMINAL_ACTIVE_PC] != 0x9C
        or old_editor.bytecode[0x05CB:0x05D0] != TERMINAL_ACTIVE_DIALOGUE_BODY
        or new_editor.bytecode[0x05CB:0x05D0] != TERMINAL_ACTIVE_DIALOGUE_BODY
    ):
        raise SurfaceSlotMigrationError("Field-550 active terminal topology drifted")

    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    if (
        len(old_table) != ARCHIVE_TABLE_SIZE
        or len(new_table) != ARCHIVE_TABLE_SIZE
        or _sha256(old_table) != OLD_ARCHIVE_TABLE_SHA256
        or _sha256(new_table) != NEW_ARCHIVE_TABLE_SHA256
        or _diff_triplets(old_table, new_table) != ARCHIVE_TABLE_DIFFS
    ):
        raise SurfaceSlotMigrationError(
            "V213/V214 archive-table delta is not the exact one-byte change"
        )
    return old_table, new_table


def _validate_source_runtime(
    payload: bytes,
    *,
    old_script: bytes,
    new_script: bytes,
    dialogue: bytes,
    archive_table: bytes,
) -> dict[str, object]:
    if (
        len(payload) != EXPECTED_PAYLOAD_SIZE
        or _sha256(payload) != SOURCE_PAYLOAD_SHA256
    ):
        raise SurfaceSlotMigrationError("V213 decompressed payload identity drifted")
    ram_payload_offset, ram = _ram_from_payload(payload)
    if (
        payload.count(old_script) != 1
        or payload.find(old_script) != EXPECTED_SCRIPT_PAYLOAD_OFFSET
        or payload.count(new_script) != 0
        or payload.count(dialogue) != 1
        or payload.find(dialogue) != EXPECTED_DIALOGUE_PAYLOAD_OFFSET
    ):
        raise SurfaceSlotMigrationError("Resident field-550 component identity drifted")
    if (
        struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0]
        != EXPECTED_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA)[0]
        != EXPECTED_VM_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_ACTOR)[0]
        != EXPECTED_VM_ACTOR_GUEST_POINTER
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
    terminal_records = tuple(
        actor_array + entity * FIELD_ACTOR_STRIDE for entity in TERMINAL_ENTITIES
    )
    terminal_actor_data_offsets = tuple(
        _guest_ram_offset(
            struct.unpack_from(
                "<I", ram, record + FIELD_ACTOR_DATA_POINTER
            )[0],
            f"terminal e{entity} ActorData",
        )
        for entity, record in zip(
            TERMINAL_ENTITIES,
            terminal_records,
            strict=True,
        )
    )
    terminal_sprite_pointers = tuple(
        struct.unpack_from("<I", ram, record + 0x04)[0]
        for record in terminal_records
    )
    if (
        terminal_records != EXPECTED_TERMINAL_RECORDS
        or terminal_actor_data_offsets != EXPECTED_TERMINAL_ACTOR_DATA_OFFSETS
        or terminal_sprite_pointers != EXPECTED_TERMINAL_SPRITE_POINTERS
        or any(struct.unpack_from("<I", ram, record)[0] != 0 for record in terminal_records)
    ):
        raise SurfaceSlotMigrationError(
            "Terminal records, ActorData, or sprite pointers drifted"
        )
    terminal_sprite_bytes = tuple(
        bytes(
            ram[
                _guest_ram_offset(pointer, f"terminal e{entity} sprite") :
                _guest_ram_offset(pointer, f"terminal e{entity} sprite")
                + TERMINAL_SPRITE_RUNTIME_SIZE
            ]
        )
        for entity, pointer in zip(
            TERMINAL_ENTITIES,
            terminal_sprite_pointers,
            strict=True,
        )
    )
    if tuple(_sha256(sprite) for sprite in terminal_sprite_bytes) != (
        EXPECTED_TERMINAL_SPRITE_SHA256
    ):
        raise SurfaceSlotMigrationError("Terminal runtime sprites drifted")

    terminal_record = terminal_records[0]
    terminal_actor_data = terminal_actor_data_offsets[0]

    checks = (
        (
            terminal_record + ACTOR_RECORD_STATUS_OFFSET,
            bytes.fromhex("60 02"),
            "terminal record status",
        ),
        (
            terminal_actor_data + ACTOR_DATA_FLAGS_OFFSET,
            bytes.fromhex("00 00 00 00"),
            "terminal secondary flags",
        ),
        (
            terminal_actor_data + ACTOR_DATA_SURFACES_OFFSET,
            bytes.fromhex("1F 00 00 00 00 00 00 00"),
            "terminal surface triangles",
        ),
        (
            terminal_actor_data + ACTOR_DATA_BOUNDS_OFFSET,
            bytes.fromhex("30 00 C8 00 1E 00 1E 00"),
            "terminal action bounds",
        ),
        (
            terminal_actor_data + ACTOR_DATA_POSITION_OFFSET,
            bytes.fromhex("00 00 46 00 00 00 00 00 00 00 71 FF"),
            "terminal current position",
        ),
        (
            terminal_actor_data + ACTOR_DATA_OLD_POSITION_OFFSET,
            bytes.fromhex("46 00 00 00 71 FF 00 00"),
            "terminal old position",
        ),
        (
            terminal_actor_data + ACTOR_SCRIPT_SLOT_OFFSET,
            bytes.fromhex("CF 05 00 02 FF FF 0C 00"),
            "terminal active script slot",
        ),
        (
            terminal_actor_data + ACTOR_CURRENT_PC_OFFSET,
            bytes.fromhex("CF 05 00 00"),
            "terminal current WAIT_DIALOG PC",
        ),
    )
    for offset, expected, label in checks:
        if ram[offset : offset + len(expected)] != expected:
            raise SurfaceSlotMigrationError(f"V213 {label} drifted")

    for entity, record, actor_data in zip(
        TERMINAL_ENTITIES[1:],
        terminal_records[1:],
        terminal_actor_data_offsets[1:],
        strict=True,
    ):
        auxiliary_checks = (
            (
                record + ACTOR_RECORD_STATUS_OFFSET,
                OLD_AUX_TERMINAL_RECORD_STATUS,
                "record status",
            ),
            (
                actor_data + ACTOR_DATA_FLAGS_OFFSET,
                OLD_AUX_TERMINAL_FLAGS,
                "ActorData flags",
            ),
            (
                actor_data + ACTOR_DATA_SURFACES_OFFSET,
                bytes.fromhex("26 00 00 00 00 00 00 00"),
                "surface triangles",
            ),
            (
                actor_data + ACTOR_DATA_BOUNDS_OFFSET,
                bytes.fromhex("10 00 5A 00 10 00 10 00"),
                "action bounds",
            ),
            (
                actor_data + ACTOR_DATA_POSITION_OFFSET,
                b"\x00" * 12,
                "current position",
            ),
            (
                actor_data + ACTOR_DATA_OLD_POSITION_OFFSET,
                b"\x00" * 8,
                "old position",
            ),
            (
                actor_data + ACTOR_SCRIPT_SLOT_OFFSET,
                OLD_AUX_TERMINAL_SLOT0,
                "script slot 0",
            ),
            (
                actor_data + ACTOR_CURRENT_PC_OFFSET,
                bytes.fromhex("8C 06 00 00"),
                "current STOP PC",
            ),
        )
        for offset, expected, label in auxiliary_checks:
            if ram[offset : offset + len(expected)] != expected:
                raise SurfaceSlotMigrationError(
                    f"V213 terminal e{entity} {label} drifted"
                )

    table_offset, volatile = media_migration._find_resident_archive_table(
        payload, archive_table
    )
    if (
        table_offset != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or volatile != 1
        or payload[EXPECTED_VOLATILE_TABLE_PAYLOAD_OFFSET]
        != EXPECTED_VOLATILE_TABLE_VALUE
        or archive_table[-1] != 0
    ):
        raise SurfaceSlotMigrationError("Resident V213 archive-table tail drifted")
    resident_table = bytes(payload[table_offset : table_offset + ARCHIVE_TABLE_SIZE])
    if resident_table != archive_table[:-1] + bytes(
        (EXPECTED_VOLATILE_TABLE_VALUE,)
    ):
        raise SurfaceSlotMigrationError(
            "Resident V213 archive table differs outside its volatile tail"
        )

    gamestate = bytes(ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE])
    if _sha256(gamestate) != EXPECTED_GAMESTATE_SHA256:
        raise SurfaceSlotMigrationError("V213 GameState identity drifted")
    return {
        "ram_payload_offset": ram_payload_offset,
        "terminal_record": terminal_record,
        "terminal_actor_data": terminal_actor_data,
        "terminal_records": terminal_records,
        "terminal_actor_data_offsets": terminal_actor_data_offsets,
        "terminal_sprite_pointers": terminal_sprite_pointers,
        "terminal_sprite_bytes": terminal_sprite_bytes,
        "gamestate": gamestate,
        "resident_table": resident_table,
    }


def migrate_v213_slot1_to_v214(
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
    """Return a separately writable, fully validated V214 state candidate."""

    source_sha256 = _sha256(state)
    if len(state) != SOURCE_STATE_SIZE or source_sha256 != SOURCE_STATE_SHA256:
        raise SurfaceSlotMigrationError(
            "Source Slot 1 identity is "
            f"{len(state)} bytes / {source_sha256}, expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    old_name = OLD_CUE_NAME.encode("ascii")
    new_name = NEW_CUE_NAME.encode("ascii")
    if (
        len(old_name) != len(new_name)
        or state.count(old_name) != 1
        or state.count(new_name) != 0
    ):
        raise SurfaceSlotMigrationError("Source CUE identity drifted")

    old_archive_table, new_archive_table = _validate_resources(
        old_disc=old_disc,
        new_disc=new_disc,
        old_script=old_script,
        new_script=new_script,
        old_dialogue=old_dialogue,
        new_dialogue=new_dialogue,
    )
    source_payload, frame_start, source_prefix = _unpack_state(state, zstd)
    if frame_start != EXPECTED_FRAME_START:
        raise SurfaceSlotMigrationError("Source frame offset drifted")
    runtime = _validate_source_runtime(
        source_payload,
        old_script=old_script,
        new_script=new_script,
        dialogue=old_dialogue,
        archive_table=old_archive_table,
    )

    final_payload = bytearray(source_payload)
    for relative, old, new in ARCHIVE_TABLE_DIFFS:
        offset = EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + relative
        if (
            offset != EXPECTED_ARCHIVE_TABLE_CHANGED_PAYLOAD_OFFSET
            or final_payload[offset] != old
        ):
            raise SurfaceSlotMigrationError(
                "Resident archive-table patch source drifted"
            )
        final_payload[offset] = new
    final_payload[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + SCRIPT_SIZE
    ] = new_script
    for offset, old, new, label in RUNTIME_PATCHES:
        if final_payload[offset : offset + len(old)] != old:
            raise SurfaceSlotMigrationError(f"Runtime patch source drifted: {label}")
        final_payload[offset : offset + len(new)] = new
    final_payload_bytes = bytes(final_payload)

    expected_offsets = {
        *(
            EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + offset
            for offset, _old, _new in ARCHIVE_TABLE_DIFFS
        ),
        *(EXPECTED_SCRIPT_PAYLOAD_OFFSET + offset for offset, _old, _new in SCRIPT_DIFFS),
    }
    for offset, old, new, _label in RUNTIME_PATCHES:
        expected_offsets.update(
            offset + relative
            for relative, (before, after) in enumerate(zip(old, new, strict=True))
            if before != after
        )
    runtime_bytes_changed = sum(
        before != after
        for _offset, old, new, _label in RUNTIME_PATCHES
        for before, after in zip(old, new, strict=True)
    )
    actual_offsets = _diff_offsets(source_payload, final_payload_bytes)
    if (
        len(ARCHIVE_TABLE_DIFFS) != EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED
        or len(SCRIPT_DIFFS) != EXPECTED_SCRIPT_BYTES_CHANGED
        or runtime_bytes_changed != EXPECTED_RUNTIME_BYTES_CHANGED
        or actual_offsets != tuple(sorted(expected_offsets))
        or len(actual_offsets) != EXPECTED_PAYLOAD_BYTES_CHANGED
    ):
        raise SurfaceSlotMigrationError(
            "Migration changed bytes outside the exact 81-byte whitelist"
        )
    expected_resident_table = new_archive_table[:-1] + bytes(
        (EXPECTED_VOLATILE_TABLE_VALUE,)
    )
    if (
        final_payload_bytes[
            EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
            EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
        ]
        != expected_resident_table
        or final_payload_bytes[EXPECTED_VOLATILE_TABLE_PAYLOAD_OFFSET]
        != EXPECTED_VOLATILE_TABLE_VALUE
        or final_payload_bytes[
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET :
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE
        ]
        != old_dialogue
    ):
        raise SurfaceSlotMigrationError("Archive table or active dialogue changed")

    cue_prefix = source_prefix.replace(old_name, new_name)
    if len(cue_prefix) != len(source_prefix) or cue_prefix.count(new_name) != 1:
        raise SurfaceSlotMigrationError("V214 CUE prefix replacement drifted")
    result = _pack_state(cue_prefix, final_payload_bytes, zstd)
    verified_payload, verified_frame_start, verified_prefix = _unpack_state(result, zstd)
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
        raise SurfaceSlotMigrationError("Final V214 state failed exact round trip")

    result_ram_offset, result_ram = _ram_from_payload(verified_payload)
    terminal_actor_data = int(runtime["terminal_actor_data"])
    terminal_records = tuple(runtime["terminal_records"])
    terminal_actor_data_offsets = tuple(runtime["terminal_actor_data_offsets"])
    terminal_sprite_pointers = tuple(runtime["terminal_sprite_pointers"])
    terminal_sprite_bytes = tuple(runtime["terminal_sprite_bytes"])
    if (
        result_ram_offset != runtime["ram_payload_offset"]
        or bytes(result_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE])
        != runtime["gamestate"]
        or verified_payload.count(old_script) != 0
        or verified_payload.count(new_script) != 1
        or verified_payload.count(old_dialogue) != 1
        or struct.unpack_from(
            "<H", result_ram, terminal_actor_data + ACTOR_CURRENT_PC_OFFSET
        )[0]
        != TERMINAL_ACTIVE_PC
        or result_ram[
            terminal_actor_data + ACTOR_SCRIPT_SLOT_OFFSET :
            terminal_actor_data + ACTOR_SCRIPT_SLOT_OFFSET + 8
        ]
        != bytes.fromhex("CF 05 00 02 FF FF 0C 00")
    ):
        raise SurfaceSlotMigrationError("V214 gameplay/action preservation failed")

    for entity, record, actor_data, slot0 in zip(
        TERMINAL_ENTITIES[1:],
        terminal_records[1:],
        terminal_actor_data_offsets[1:],
        NEW_AUX_TERMINAL_SLOT0,
        strict=True,
    ):
        if (
            result_ram[
                record + ACTOR_RECORD_STATUS_OFFSET :
                record + ACTOR_RECORD_STATUS_OFFSET + 2
            ]
            != NEW_AUX_TERMINAL_RECORD_STATUS
            or result_ram[
                actor_data + ACTOR_DATA_FLAGS_OFFSET :
                actor_data + ACTOR_DATA_FLAGS_OFFSET + 4
            ]
            != NEW_AUX_TERMINAL_FLAGS
            or result_ram[
                actor_data + ACTOR_SCRIPT_SLOT_OFFSET :
                actor_data + ACTOR_SCRIPT_SLOT_OFFSET + 8
            ]
            != slot0
            or result_ram[
                actor_data + ACTOR_CURRENT_PC_OFFSET :
                actor_data + ACTOR_CURRENT_PC_OFFSET + 4
            ]
            != bytes.fromhex("8C 06 00 00")
        ):
            raise SurfaceSlotMigrationError(
                f"V214 terminal e{entity} initializer queue failed"
            )
    for entity, pointer, expected_sprite in zip(
        TERMINAL_ENTITIES,
        terminal_sprite_pointers,
        terminal_sprite_bytes,
        strict=True,
    ):
        sprite = _guest_ram_offset(pointer, f"terminal e{entity} sprite")
        if (
            result_ram[sprite : sprite + TERMINAL_SPRITE_RUNTIME_SIZE]
            != expected_sprite
        ):
            raise SurfaceSlotMigrationError(
                f"V214 terminal e{entity} sprite changed before its scheduler tick"
            )

    output_sha256 = _sha256(result)
    if EXPECTED_OUTPUT_SIZE is not None and len(result) != EXPECTED_OUTPUT_SIZE:
        raise SurfaceSlotMigrationError("V214 candidate size drifted")
    if EXPECTED_OUTPUT_SHA256 is not None and output_sha256 != EXPECTED_OUTPUT_SHA256:
        raise SurfaceSlotMigrationError("V214 candidate identity drifted")
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
        "archive_table_payload_offset": f"0x{EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET:X}",
        "archive_table_payload_bytes_changed": len(ARCHIVE_TABLE_DIFFS),
        "volatile_table_tail_preserved": True,
        "script_payload_offset": f"0x{EXPECTED_SCRIPT_PAYLOAD_OFFSET:X}",
        "dialogue_payload_offset": f"0x{EXPECTED_DIALOGUE_PAYLOAD_OFFSET:X}",
        "payload_bytes_changed": len(actual_offsets),
        "script_bytes_changed": len(SCRIPT_DIFFS),
        "terminal_runtime_bytes_changed": runtime_bytes_changed,
        "queued_terminal_initializers": {
            "e5": f"0x{TERMINAL_INIT_PCS[1]:04X}",
            "e6": f"0x{TERMINAL_INIT_PCS[2]:04X}",
        },
        "terminal_sprites_preserved": True,
        "active_terminal_pc": f"0x{TERMINAL_ACTIVE_PC:04X}",
        "active_dialogue_preserved": True,
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
        result, report = migrate_v213_slot1_to_v214(
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
            raise SurfaceSlotMigrationError("Written V214 candidate changed on disk")
        print(f"Wrote validated V214 candidate: {output}")
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
