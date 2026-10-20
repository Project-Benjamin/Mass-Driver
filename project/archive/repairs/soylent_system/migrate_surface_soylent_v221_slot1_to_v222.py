#!/usr/bin/env python3
"""Migrate the exact V221 Intake Slot 1 state to V222 safely.

V222 restores the three authored examination-room doors in field 621 to the
same planes and outward threshold topology as the native doors.  The loaded
field is already resident in the saved state, so changing only the mounted
disc would leave V221's inset leaves, reversed threshold transforms, and
absolute slide-script coordinates active until the field was reloaded.

This migrator applies the finished V222 field header and ATEL deltas to the
resident field, then updates every serialized runtime mirror of those
transforms: both actor matrices/translations, ActorData current/old positions,
and the dynamic leaves' sprite-core positions.  It pins the exact source,
media, component, runtime, and output identities; enforces a 204-byte payload
whitelist; preserves the unchanged archive table and volatile byte; and never
writes live DuckStation Slot 1.
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
import tools.migrate_surface_soylent_v220_slot1_to_v221 as v221_migration  # noqa: E402
from tools.xgdeathblows import GAMESTATE_SIZE  # noqa: E402
from tools.xgdisc import DiscFormatError, Mode2Image  # noqa: E402
from tools.xgfield import FieldFormatError, ParsedField, parse_field  # noqa: E402
from work.read_duckstation_runtime import (  # noqa: E402
    CAMERA_VECTORS,
    FIELD_ACTORS,
    FIELD_ACTOR_DATA_POINTER,
    FIELD_ACTOR_STRIDE,
    FIELD_NUM_ACTORS,
    GAME_STATE,
    RAM_SIZE,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIVE_SLOT1 = (PROJECT_ROOT / "emulator_data" / "SLUS-00669_1.sav").resolve()

SOURCE_STATE_SIZE = 1_521_337
SOURCE_STATE_SHA256 = "27710b20903e4eb6be1c818b3e3aaf8bf4050c7cc709575a73f5c2fb7f9d3581"
SOURCE_COMPRESSED_SIZE = 1_465_263
SOURCE_PREFIX_SIZE = 56_074
SOURCE_PREFIX_SHA256 = "462c1f421c4e0ad1ff48a94956baf2a83589c666074343c9f089edb192c7a5c4"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "88525715b23bc3c13c1c39b1e25d9d06cb7772cd02560a9234d0ca722e97a816"
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
SOURCE_RAM_SHA256 = "f9f8af4c8481a0d56591de232c3b0f7c094f3fe36454e05a02f89d8fe9367d03"

OUTPUT_STATE_SIZE = 1_521_338
OUTPUT_STATE_SHA256 = "66bbf32915c4181aefc7518b8d73c57979a132b24d3c5b6098d0951a6c104427"
OUTPUT_COMPRESSED_SIZE = 1_465_264
OUTPUT_PREFIX_SHA256 = "016c702f07a3ef1d3d9bf17d7f860a5ebb5d7a89f1b197f688d4c18d52f8e4ba"
OUTPUT_PAYLOAD_SHA256 = "0ca8b7f1883445fced3de07e6fc8f827562b5d582c878e9b143cf6846021d95a"
OUTPUT_RAM_SHA256 = "75ee178b9723b04c533bb3b1c7ffad580f55ee715731ea419667dbe15857dadb"

OLD_DISC_SIZE = NEW_DISC_SIZE = 698_642_784
OLD_DISC_SHA256 = "577519db3fb4228c17f0555466866b271c265587a5fdc01515d9ff3f78f6827a"
NEW_DISC_SHA256 = "4d386649f85a873003235ec8fc3082eb3e036aa5dbbc306c8cabdf84c8c80d03"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v221.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v222.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = "a4134fcf3f5bee22530aa90aed6cd691a29983483eb8438828af5caa30ba1163"
NEW_CUE_SHA256 = "a2ab49791fbd65b34964361d8603e85e6cea5fb79430e852440af6e582f3220e"

ARCHIVE_TABLE_SIZE = 0x8000
ARCHIVE_TABLE_SHA256 = "f0a26fa145622264a69cbd25a59213bc1f47920aca22f9d2f00d24fde4342290"
ARCHIVE_TABLE_DIFFS: tuple[tuple[int, int, int], ...] = ()
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
EXPECTED_VOLATILE_TABLE_VALUE = 0xE0
RESIDENT_ARCHIVE_TABLE_SHA256 = "3eacc1ac53db105f07c987a3eeb20cfbbca9df9fefe21a8c7a4c4750e14dfba0"

FIELD621_FAT_INDEX = 1843
OLD_FIELD621_BUNDLE_SIZE = NEW_FIELD621_BUNDLE_SIZE = 135_656
OLD_FIELD621_BUNDLE_SHA256 = "693c507955696d8a3c75b07acb1be7ad13c50ed4791b95a48b558661c279aae4"
NEW_FIELD621_BUNDLE_SHA256 = "acf5c09f99d67ee157c4049c31fe1f48026819e6a39e041284bd1912e6e4a039"
FIELD_HEADER_SIZE = 1_408
OLD_DISK_HEADER_SHA256 = "3c4e07cd1cc92ad2983f5214c677e1614d5d9e5c048ecf0181b018156f8ccbce"
NEW_DISK_HEADER_SHA256 = "a673a4079dddfd4d908f63f8fedee227e9c23f033c6652b8aace86de08900887"
FIELD_HEADER_DIFF_TRIPLETS = (
    (0x478, 0x0E, 0x10),
    (0x47C, 0xB5, 0xB7),
    (0x488, 0xC3, 0xC5),
    (0x498, 0xC3, 0xC5),
    (0x555, 0x0A, 0x02),
    (0x558, 0xAA, 0x6D),
    (0x55C, 0xDC, 0x1B),
    (0x55D, 0x04, 0x05),
    (0x565, 0x0C, 0x04),
    (0x568, 0x1C, 0x1D),
    (0x56C, 0x19, 0x72),
    (0x575, 0x0C, 0x04),
    (0x578, 0x1C, 0x1D),
    (0x57C, 0x60, 0xB9),
)

RESIDENT_SCRIPT_OFFSET = 0x110BBC
RESIDENT_SCRIPT_SIZE = 10_895
OLD_SCRIPT_SHA256 = "78399e8caa38656e936aaf5a72bc1bb6db70b998c33ab028c522ced107cc392e"
NEW_SCRIPT_SHA256 = "a362a56e04f91240e4209cb93cdb36a63c31d57bdf2e03c25fca52f202845ea7"
SCRIPT_ROUTINES = (
    (46, 0x25DD, 289,
     "9e582bcc39766bd02a2412bbef32612007292e2d3675b7855d379146bee7ef0c",
     "2b7b51b78cd8cf01ea1805c06d59536e84a233793c00a6f91eb1f92fadf0315e"),
    (47, 0x2776, 289,
     "5fce707b6b501ba645e58d71d424affc0dfb5bd50c93f33ae8852e5a5c2641a7",
     "19468fb6368aae5b4590a7da4893e3293f0007e96c362dc74354fbe0d2413476"),
    (48, 0x290F, 289,
     "5fce707b6b501ba645e58d71d424affc0dfb5bd50c93f33ae8852e5a5c2641a7",
     "19468fb6368aae5b4590a7da4893e3293f0007e96c362dc74354fbe0d2413476"),
)

LOADED_HEADER_OFFSET = 0x1C9FD4
SOURCE_LOADED_HEADER_SHA256 = "07a06f1fd4db8494dd18b0fe75db2d8d1212aae429ce176b79e6dd1d12565bbf"
TARGET_LOADED_HEADER_SHA256 = "f8a3ec611b9f521ff3c3f3bcd02fc892b8a4381ce6dd5861ceea3621c18a79ec"
HEADER_RECORD_OFFSET = 0x190
HEADER_RECORD_SIZE = 0x10
HEADER_RECORDS = {
    46: (
        bytes.fromhex("90 02 00 00 00 0A 00 00 0E 0C 00 00 B5 05 03 00"),
        bytes.fromhex("90 02 00 00 00 0A 00 00 10 0C 00 00 B7 05 03 00"),
    ),
    47: (
        bytes.fromhex("90 02 00 00 00 00 00 00 C3 06 00 00 00 00 06 00"),
        bytes.fromhex("90 02 00 00 00 00 00 00 C5 06 00 00 00 00 06 00"),
    ),
    48: (
        bytes.fromhex("90 02 00 00 00 00 00 00 C3 06 00 00 00 00 07 00"),
        bytes.fromhex("90 02 00 00 00 00 00 00 C5 06 00 00 00 00 07 00"),
    ),
    60: (
        bytes.fromhex("10 00 00 00 00 0A 00 00 AA 06 00 00 DC 04 14 00"),
        bytes.fromhex("10 00 00 00 00 02 00 00 6D 06 00 00 1B 05 14 00"),
    ),
    61: (
        bytes.fromhex("10 00 00 00 00 0C 00 00 1C 07 00 00 19 03 14 00"),
        bytes.fromhex("10 00 00 00 00 04 00 00 1D 07 00 00 72 03 14 00"),
    ),
    62: (
        bytes.fromhex("10 00 00 00 00 0C 00 00 1C 07 00 00 60 01 14 00"),
        bytes.fromhex("10 00 00 00 00 04 00 00 1D 07 00 00 B9 01 14 00"),
    ),
}

EXPECTED_FIELD_ACTOR_COUNT = 63
EXPECTED_FIELD_ACTORS = 0x11B0D4
ACTOR_ARRAY_SIZE = EXPECTED_FIELD_ACTOR_COUNT * FIELD_ACTOR_STRIDE
SOURCE_ACTOR_ARRAY_SHA256 = "a74b3977801d58976b596c0b966d9c8edb958813af643bbe303d1232d302f37f"
TARGET_ACTOR_ARRAY_SHA256 = "575bdb66cc1a137854e707b5001e5a1405b432a03a518573522dbd6e96c0b6c8"
ACTOR_RECORD_SHA256 = {
    46: ("99e1bd8c20b446c1623dc7a7c25176b5847cfa838be05a0f24ce37843af32ae4",
         "22b76c97fdaeb6379f1a57b098101992cff97b469d5a522de803e30b1cfe2282"),
    47: ("4049cac6efc55909ef6ce62eee383c25024a8bab3fd250bfc841c7384462c1e0",
         "f58917db9c277dbf586a55f85c4921bc686fc03fa963e2a027b357fb24a72d23"),
    48: ("485d8a1f672c9a5edee1e743665e7d951d8451a6685e5a73766aedc1e7a053f7",
         "ec56816609dde72d20bb34362fbd4ef7b50db37dc5f85cdfed82a13c8a015762"),
    60: ("9ae74db20c6c1c157e0e307d43a8181de605ebee8642b93eef9c23fd1dbab579",
         "e72bf1e2359505d1ecc6a8de987c2a55192b33de356180390f507757aabc331d"),
    61: ("40672c14d561432400e78629cb55a8ccb475b4b8eac10da6592a403a86923498",
         "d825046c0c26359dbb3656f6a638e215bdc9adce1cccaccd565872ce2f3304f4"),
    62: ("ea2ce036519f1aec56b49f86583ec4305eb20b045c8d436a7ecdade7e38c67d9",
         "1244fcfae2879d32a800b59c5463d9e594bf0219a575f435d834edf8d4c52bae"),
}

# e46-e48 are dynamic single-leaf helpers.  e60-e62 are static floor aprons.
DYNAMIC_PLACEMENTS = {
    46: (3_088, 0, 1_463),
    47: (1_733, 0, 0),
    48: (1_733, 0, 0),
}
STATIC_PLACEMENTS = {
    60: ((2_896, 0, 2_896, 0, 4_096, 0, -2_896, 0, 2_896),
         (1_645, 0, 1_307), 0x0200),
    61: ((0, 0, 4_096, 0, 4_096, 0, -4_096, 0, 0),
         (1_821, 0, 882), 0x0400),
    62: ((0, 0, 4_096, 0, 4_096, 0, -4_096, 0, 0),
         (1_821, 0, 441), 0x0400),
}

ACTOR_DATA_SIZE = 0x138
ACTOR_DATA_POSITION_OFFSET = 0x20
ACTOR_DATA_OLD_POSITION_OFFSET = 0x68
ACTOR_DATA_LAYOUT = {
    46: (0x1225E8, 0x148AA8),
    47: (0x122874, 0x148C4C),
    48: (0x122B00, 0x148DF0),
}
SOURCE_ACTOR_DATA_SHA256 = "c4e53e2063213b18b8222383239abff397c49b8ec1a9bcec01ce798a9a07acfb"
TARGET_ACTOR_DATA_SHA256 = "c890f8302c38f84da9a2ca00eab345a4289f9381b2653ddc71d79ca5e2613392"
ACTOR_DATA_SHA256 = {
    46: ("dbd3f5d24e6fa2c97aee032ca163b27994603d1faa5234e73252c633cede6af2",
         "df65fab87dcd625cf2e2378366c05ef8080bf591dd3bcc8695a5f77eb9aeb887"),
    47: ("e5b2c6f12fa947046258c8e2e788942f4f6e521faa429bd6fa4ba91ce6ad17eb",
         "a84c84bb2023529f48c32967a6b25b9ce2666e295ff149c33fc502b3096fce0c"),
    48: ("6c7e8620d1ff66bac5181017f51c7b63bed4cf1148ed0b1c3518f0f63f68fdc9",
         "1af2c6479aebb5ed90275b566e005a13e37365009675d9ef976ac1c341cdb3f8"),
}
SPRITE_CORE_POSITION_SIZE = 12
SPRITE_CORE_SHA256 = {
    46: ("903ce9e7453f778a8f7f56b1572f1ed8bc60d7bc2531c8f264bf3c9dbff24022",
         "723a0ee01d7d4a7b84b7cfeb0e856d3a0d95b8126c4b6a69e65715a82cc8e354"),
    47: ("1d2e7f6ee30fe2241439da8506849b4495a5650607c0feef0a965fbdbb562114",
         "10961d1b16e2804e09e7687b035d57467e4dba2e1830aae3e1217f2f71f4752a"),
    48: ("1d2e7f6ee30fe2241439da8506849b4495a5650607c0feef0a965fbdbb562114",
         "10961d1b16e2804e09e7687b035d57467e4dba2e1830aae3e1217f2f71f4752a"),
}

RESIDENT_DIALOGUE_OFFSET = 0x11367C
RESIDENT_DIALOGUE_SIZE = 2_135
RESIDENT_DIALOGUE_SHA256 = "2affc3b9e7ad27ae0e9be2b4e8f0d1362f3b37ef7218001aa995994cf6e5bb40"
RESIDENT_WALKMESH_OFFSET = 0x113EEC
RESIDENT_WALKMESH_SIZE = 5_156
RESIDENT_WALKMESH_SHA256 = "6d36a3fc267029bc2e65ee9ae7435208be0a7934c9aa86af3fa1fd580548b932"
SOURCE_GAMESTATE_SHA256 = "b7d95bfc1c03b11793a49c12410e028549a570f0cf8a4ef46415e61ac878d5b1"
SOURCE_CAMERA_SHA256 = "7e5575ebac9b9571b04a93382e48cd47088649cab7f2ff70ced72de9506b0548"
RUNTIME_MODEL2_OFFSET = v221_migration.RUNTIME_MODEL2_OFFSET
RUNTIME_MODEL2_SIZE = v221_migration.RUNTIME_MODEL2_SIZE
RUNTIME_MODEL2_SHA256 = v221_migration.RUNTIME_MODEL2_SHA256
RUNTIME_MODEL20_OFFSET = v221_migration.RUNTIME_MODEL20_OFFSET
RUNTIME_MODEL20_SIZE = v221_migration.RUNTIME_MODEL20_SIZE
RUNTIME_MODEL20_SHA256 = v221_migration.OUTPUT_RUNTIME_MODEL20_SHA256
MODEL20_INSTANCE_LAYOUT = v221_migration.MODEL20_INSTANCE_LAYOUT
RUNTIME_MODEL20_ARENA_SIZE = v221_migration.RUNTIME_MODEL20_ARENA_SIZE
PACKET_ARENAS_SHA256 = v221_migration.TARGET_PACKET_ARENAS_SHA256

EXPECTED_HEADER_BYTES_CHANGED = 14
EXPECTED_SCRIPT_BYTES_CHANGED = 129
EXPECTED_ACTOR_BYTES_CHANGED = 49
EXPECTED_ACTOR_DATA_BYTES_CHANGED = 8
EXPECTED_SPRITE_BYTES_CHANGED = 4
EXPECTED_RAM_BYTES_CHANGED = 204
EXPECTED_PAYLOAD_BYTES_CHANGED = 204


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output whenever the pinned V221/V222 contract drifts."""


class _ZstdLike(Protocol):
    def frame_size(self, frame: bytes) -> int: ...
    def decompress(self, frame: bytes) -> bytes: ...
    def compress(self, payload: bytes) -> bytes: ...


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _diff_offsets(before: bytes, after: bytes) -> tuple[int, ...]:
    if len(before) != len(after):
        raise SurfaceSlotMigrationError("Compared byte strings have different lengths")
    return tuple(
        index
        for index, (old, new) in enumerate(zip(before, after, strict=True))
        if old != new
    )


def _diff_triplets(before: bytes, after: bytes) -> tuple[tuple[int, int, int], ...]:
    return tuple((index, before[index], after[index]) for index in _diff_offsets(before, after))


def _validate_file(path: Path, size: int, sha256: str, label: str) -> None:
    if not path.is_file():
        raise SurfaceSlotMigrationError(f"{label} does not exist: {path}")
    actual = (path.stat().st_size, _file_sha256(path))
    if actual != (size, sha256):
        raise SurfaceSlotMigrationError(
            f"{label} identity changed: {actual[0]} bytes, SHA-256 {actual[1]}"
        )


def _unpack_state(state: bytes, zstd: _ZstdLike) -> tuple[bytes, int, bytes]:
    try:
        return v221_migration._unpack_state(state, zstd)
    except v221_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc


def _pack_state(prefix: bytes, payload: bytes, zstd: _ZstdLike) -> bytes:
    try:
        return v221_migration._pack_state(prefix, payload, zstd)
    except v221_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc


def _ram_from_payload(payload: bytes) -> tuple[int, bytes]:
    try:
        offset, ram = v221_migration._ram_from_payload(payload)
    except v221_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc
    if offset != EXPECTED_RAM_PAYLOAD_OFFSET:
        raise SurfaceSlotMigrationError("Serialized PSX RAM payload offset drifted")
    return offset, ram


def _expected_prefix(source_prefix: bytes, *, compressed_size: int) -> bytes:
    old_name = OLD_CUE_NAME.encode("ascii")
    new_name = NEW_CUE_NAME.encode("ascii")
    if len(old_name) != len(new_name) or source_prefix.count(old_name) != 1:
        raise SurfaceSlotMigrationError("Pinned V221 media path changed")
    if new_name in source_prefix:
        raise SurfaceSlotMigrationError("Source state already names the V222 media")
    expected = bytearray(source_prefix.replace(old_name, new_name))
    struct.pack_into(
        "<I",
        expected,
        media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        compressed_size,
    )
    return bytes(expected)


def _disc_field621(
    disc: Path, *, bundle_size: int, bundle_sha256: str
) -> ParsedField:
    try:
        image = Mode2Image(disc)
        entries = image.read_index()
        if FIELD621_FAT_INDEX >= len(entries):
            raise SurfaceSlotMigrationError("Field-621 FAT index is absent")
        entry = entries[FIELD621_FAT_INDEX]
        if entry.canonical_disc2_index != 1848:
            raise SurfaceSlotMigrationError("Field-621 canonical file mapping drifted")
        bundle = image.extract_entry(entry)
        if (len(bundle), _sha256(bundle)) != (bundle_size, bundle_sha256):
            raise SurfaceSlotMigrationError("Field-621 disc bundle identity changed")
        parsed = parse_field(bundle)
    except (DiscFormatError, FieldFormatError) as exc:
        raise SurfaceSlotMigrationError(f"Cannot decode field 621 from disc: {exc}") from exc
    if len(parsed.header) != FIELD_HEADER_SIZE or len(parsed.parts) != 9:
        raise SurfaceSlotMigrationError("Field-621 component layout changed")
    return parsed


def _actor_data_snapshot(ram: bytes, actor_base: int, actor_count: int) -> bytes:
    chunks: list[bytes] = []
    for entity in range(actor_count):
        record = actor_base + entity * FIELD_ACTOR_STRIDE
        pointer = struct.unpack_from("<I", ram, record + FIELD_ACTOR_DATA_POINTER)[0]
        offset = pointer & 0x1FFFFFFF
        if offset == 0:
            continue
        if offset > RAM_SIZE - ACTOR_DATA_SIZE:
            raise SurfaceSlotMigrationError(f"e{entity} ActorData leaves PSX RAM")
        chunks.append(ram[offset : offset + ACTOR_DATA_SIZE])
    return b"".join(chunks)


def _camera_snapshot(ram: bytes) -> bytes:
    return b"".join(ram[address : address + 16] for address in CAMERA_VECTORS.values())


def _packet_arenas(ram: bytes) -> bytes:
    chunks: list[bytes] = []
    for entity, instance, expected_buffers in MODEL20_INSTANCE_LAYOUT:
        model_pointer, buffer0, buffer1 = struct.unpack_from("<III", ram, instance + 4)
        buffers = (buffer0 & 0x1FFFFFFF, buffer1 & 0x1FFFFFFF)
        if model_pointer != v221_migration.RUNTIME_MODEL20_GUEST_BLOCK_POINTER:
            raise SurfaceSlotMigrationError(f"e{entity} no longer references model 20")
        if buffers != expected_buffers:
            raise SurfaceSlotMigrationError(f"e{entity} model-20 arenas moved")
        for offset in buffers:
            chunks.append(ram[offset : offset + RUNTIME_MODEL20_ARENA_SIZE])
    return b"".join(chunks)


def _validated_source_layout(ram: bytes) -> tuple[int, int]:
    actor_count = struct.unpack_from("<I", ram, FIELD_NUM_ACTORS)[0]
    actor_base = struct.unpack_from("<I", ram, FIELD_ACTORS)[0] & 0x1FFFFFFF
    if (actor_count, actor_base) != (EXPECTED_FIELD_ACTOR_COUNT, EXPECTED_FIELD_ACTORS):
        raise SurfaceSlotMigrationError("Loaded field-621 actor layout changed")
    actors = ram[actor_base : actor_base + ACTOR_ARRAY_SIZE]
    actor_data = _actor_data_snapshot(ram, actor_base, actor_count)
    if _sha256(actors) != SOURCE_ACTOR_ARRAY_SHA256:
        raise SurfaceSlotMigrationError("Pinned V221 actor array changed")
    if _sha256(actor_data) != SOURCE_ACTOR_DATA_SHA256:
        raise SurfaceSlotMigrationError("Pinned V221 ActorData set changed")

    for entity, (actor_data_offset, sprite_offset) in ACTOR_DATA_LAYOUT.items():
        record = actor_base + entity * FIELD_ACTOR_STRIDE
        actual_actor_data = (
            struct.unpack_from("<I", ram, record + FIELD_ACTOR_DATA_POINTER)[0]
            & 0x1FFFFFFF
        )
        actual_sprite = struct.unpack_from("<I", ram, record + 4)[0] & 0x1FFFFFFF
        if (actual_actor_data, actual_sprite) != (actor_data_offset, sprite_offset):
            raise SurfaceSlotMigrationError(f"e{entity} runtime pointer layout changed")
        if _sha256(ram[record : record + FIELD_ACTOR_STRIDE]) != ACTOR_RECORD_SHA256[entity][0]:
            raise SurfaceSlotMigrationError(f"e{entity} source actor record changed")
        if _sha256(ram[actor_data_offset : actor_data_offset + ACTOR_DATA_SIZE]) != ACTOR_DATA_SHA256[entity][0]:
            raise SurfaceSlotMigrationError(f"e{entity} source ActorData changed")
        if _sha256(ram[sprite_offset : sprite_offset + SPRITE_CORE_POSITION_SIZE]) != SPRITE_CORE_SHA256[entity][0]:
            raise SurfaceSlotMigrationError(f"e{entity} source sprite position changed")
    for entity in STATIC_PLACEMENTS:
        record = actor_base + entity * FIELD_ACTOR_STRIDE
        if _sha256(ram[record : record + FIELD_ACTOR_STRIDE]) != ACTOR_RECORD_SHA256[entity][0]:
            raise SurfaceSlotMigrationError(f"e{entity} source actor record changed")
    return actor_count, actor_base


def _build_target_ram(
    source_ram: bytes, *, old_field: ParsedField, new_field: ParsedField
) -> tuple[bytes, dict[str, frozenset[int]]]:
    actor_count, actor_base = _validated_source_layout(source_ram)
    old_header, new_header = old_field.header, new_field.header
    old_script = old_field.parts[5].data
    new_script = new_field.parts[5].data
    if (
        _sha256(old_header) != OLD_DISK_HEADER_SHA256
        or _sha256(new_header) != NEW_DISK_HEADER_SHA256
        or _diff_triplets(old_header, new_header) != FIELD_HEADER_DIFF_TRIPLETS
    ):
        raise SurfaceSlotMigrationError("Finished field-621 header delta changed")
    if (
        (len(old_script), _sha256(old_script)) != (RESIDENT_SCRIPT_SIZE, OLD_SCRIPT_SHA256)
        or (len(new_script), _sha256(new_script)) != (RESIDENT_SCRIPT_SIZE, NEW_SCRIPT_SHA256)
        or len(_diff_offsets(old_script, new_script)) != EXPECTED_SCRIPT_BYTES_CHANGED
    ):
        raise SurfaceSlotMigrationError("Finished field-621 ATEL delta changed")
    if source_ram[RESIDENT_SCRIPT_OFFSET : RESIDENT_SCRIPT_OFFSET + RESIDENT_SCRIPT_SIZE] != old_script:
        raise SurfaceSlotMigrationError("Resident V221 field-621 ATEL changed")

    source_loaded_header = source_ram[
        LOADED_HEADER_OFFSET : LOADED_HEADER_OFFSET + FIELD_HEADER_SIZE
    ]
    if _sha256(source_loaded_header) != SOURCE_LOADED_HEADER_SHA256:
        raise SurfaceSlotMigrationError("Resident V221 field header changed")
    for entity, (source_record, _target_record) in HEADER_RECORDS.items():
        start = HEADER_RECORD_OFFSET + entity * HEADER_RECORD_SIZE
        if source_loaded_header[start : start + HEADER_RECORD_SIZE] != source_record:
            raise SurfaceSlotMigrationError(f"e{entity} source header record changed")

    for entity, relative, size, source_hash, target_hash in SCRIPT_ROUTINES:
        before = old_script[relative : relative + size]
        after = new_script[relative : relative + size]
        if (_sha256(before), _sha256(after)) != (source_hash, target_hash):
            raise SurfaceSlotMigrationError(f"e{entity} slide routine changed")

    target = bytearray(source_ram)
    for relative, old, new in FIELD_HEADER_DIFF_TRIPLETS:
        absolute = LOADED_HEADER_OFFSET + relative
        if target[absolute] != old:
            raise SurfaceSlotMigrationError(
                f"Resident header drifted at relative offset 0x{relative:X}"
            )
        target[absolute] = new
    target[
        RESIDENT_SCRIPT_OFFSET : RESIDENT_SCRIPT_OFFSET + RESIDENT_SCRIPT_SIZE
    ] = new_script

    for entity, position in DYNAMIC_PLACEMENTS.items():
        actor = actor_base + entity * FIELD_ACTOR_STRIDE
        for translation in (0x20, 0x40):
            struct.pack_into("<3i", target, actor + translation, *position)

    for entity, (matrix, position, yaw) in STATIC_PLACEMENTS.items():
        actor = actor_base + entity * FIELD_ACTOR_STRIDE
        for matrix_offset, translation_offset in ((0x0C, 0x20), (0x2C, 0x40)):
            struct.pack_into("<9h", target, actor + matrix_offset, *matrix)
            struct.pack_into("<3i", target, actor + translation_offset, *position)
        struct.pack_into("<h", target, actor + 0x52, yaw)

    for entity, position in DYNAMIC_PLACEMENTS.items():
        actor_data, sprite = ACTOR_DATA_LAYOUT[entity]
        fixed_position = tuple(coordinate << 16 for coordinate in position)
        struct.pack_into("<3i", target, actor_data + ACTOR_DATA_POSITION_OFFSET, *fixed_position)
        struct.pack_into("<3h", target, actor_data + ACTOR_DATA_OLD_POSITION_OFFSET, *position)
        struct.pack_into("<3i", target, sprite, *fixed_position)

    target_ram = bytes(target)
    target_loaded_header = target_ram[
        LOADED_HEADER_OFFSET : LOADED_HEADER_OFFSET + FIELD_HEADER_SIZE
    ]
    if _sha256(target_loaded_header) != TARGET_LOADED_HEADER_SHA256:
        raise SurfaceSlotMigrationError("Target loaded field header reconstruction changed")
    for entity, (_source_record, target_record) in HEADER_RECORDS.items():
        start = HEADER_RECORD_OFFSET + entity * HEADER_RECORD_SIZE
        if target_loaded_header[start : start + HEADER_RECORD_SIZE] != target_record:
            raise SurfaceSlotMigrationError(f"e{entity} target header record changed")
    if target_ram[RESIDENT_SCRIPT_OFFSET : RESIDENT_SCRIPT_OFFSET + RESIDENT_SCRIPT_SIZE] != new_script:
        raise SurfaceSlotMigrationError("Target V222 field-621 ATEL was not installed")

    target_actors = target_ram[actor_base : actor_base + ACTOR_ARRAY_SIZE]
    if _sha256(target_actors) != TARGET_ACTOR_ARRAY_SHA256:
        raise SurfaceSlotMigrationError("Target actor-array reconstruction changed")
    if _sha256(_actor_data_snapshot(target_ram, actor_base, actor_count)) != TARGET_ACTOR_DATA_SHA256:
        raise SurfaceSlotMigrationError("Target ActorData reconstruction changed")
    for entity, (actor_data, sprite) in ACTOR_DATA_LAYOUT.items():
        record = actor_base + entity * FIELD_ACTOR_STRIDE
        if _sha256(target_ram[record : record + FIELD_ACTOR_STRIDE]) != ACTOR_RECORD_SHA256[entity][1]:
            raise SurfaceSlotMigrationError(f"e{entity} target actor record changed")
        if _sha256(target_ram[actor_data : actor_data + ACTOR_DATA_SIZE]) != ACTOR_DATA_SHA256[entity][1]:
            raise SurfaceSlotMigrationError(f"e{entity} target ActorData changed")
        if _sha256(target_ram[sprite : sprite + SPRITE_CORE_POSITION_SIZE]) != SPRITE_CORE_SHA256[entity][1]:
            raise SurfaceSlotMigrationError(f"e{entity} target sprite position changed")
    for entity in STATIC_PLACEMENTS:
        record = actor_base + entity * FIELD_ACTOR_STRIDE
        if _sha256(target_ram[record : record + FIELD_ACTOR_STRIDE]) != ACTOR_RECORD_SHA256[entity][1]:
            raise SurfaceSlotMigrationError(f"e{entity} target actor record changed")

    categories = {
        "header": frozenset(
            LOADED_HEADER_OFFSET + relative
            for relative, _old, _new in FIELD_HEADER_DIFF_TRIPLETS
        ),
        "script": frozenset(
            RESIDENT_SCRIPT_OFFSET + relative
            for relative in _diff_offsets(old_script, new_script)
        ),
        "actors": frozenset(
            actor_base + relative
            for relative in _diff_offsets(
                source_ram[actor_base : actor_base + ACTOR_ARRAY_SIZE], target_actors
            )
        ),
        "actor_data": frozenset(
            actor_data + relative
            for entity, (actor_data, _sprite) in ACTOR_DATA_LAYOUT.items()
            for relative in _diff_offsets(
                source_ram[actor_data : actor_data + ACTOR_DATA_SIZE],
                target_ram[actor_data : actor_data + ACTOR_DATA_SIZE],
            )
        ),
        "sprites": frozenset(
            sprite + relative
            for entity, (_actor_data, sprite) in ACTOR_DATA_LAYOUT.items()
            for relative in _diff_offsets(
                source_ram[sprite : sprite + SPRITE_CORE_POSITION_SIZE],
                target_ram[sprite : sprite + SPRITE_CORE_POSITION_SIZE],
            )
        ),
    }
    expected_counts = {
        "header": EXPECTED_HEADER_BYTES_CHANGED,
        "script": EXPECTED_SCRIPT_BYTES_CHANGED,
        "actors": EXPECTED_ACTOR_BYTES_CHANGED,
        "actor_data": EXPECTED_ACTOR_DATA_BYTES_CHANGED,
        "sprites": EXPECTED_SPRITE_BYTES_CHANGED,
    }
    if {name: len(offsets) for name, offsets in categories.items()} != expected_counts:
        raise SurfaceSlotMigrationError("Runtime transform byte counts changed")
    expected = frozenset().union(*categories.values())
    if sum(map(len, categories.values())) != len(expected):
        raise SurfaceSlotMigrationError("Runtime transform patch ranges overlap")
    if (
        len(expected) != EXPECTED_RAM_BYTES_CHANGED
        or frozenset(_diff_offsets(source_ram, target_ram)) != expected
        or _sha256(target_ram) != OUTPUT_RAM_SHA256
    ):
        raise SurfaceSlotMigrationError("RAM changed outside the exact V222 whitelist")
    return target_ram, categories


def _validate_preserved_state(source_ram: bytes, target_ram: bytes) -> None:
    preserved = (
        (GAME_STATE, GAMESTATE_SIZE, SOURCE_GAMESTATE_SHA256, "GameState"),
        (RESIDENT_DIALOGUE_OFFSET, RESIDENT_DIALOGUE_SIZE, RESIDENT_DIALOGUE_SHA256, "dialogue"),
        (RESIDENT_WALKMESH_OFFSET, RESIDENT_WALKMESH_SIZE, RESIDENT_WALKMESH_SHA256, "walkmesh"),
        (RUNTIME_MODEL2_OFFSET, RUNTIME_MODEL2_SIZE, RUNTIME_MODEL2_SHA256, "model 2"),
        (RUNTIME_MODEL20_OFFSET, RUNTIME_MODEL20_SIZE, RUNTIME_MODEL20_SHA256, "model 20"),
    )
    for offset, size, expected_hash, label in preserved:
        source = source_ram[offset : offset + size]
        if _sha256(source) != expected_hash:
            raise SurfaceSlotMigrationError(f"Pinned {label} identity changed")
        if target_ram[offset : offset + size] != source:
            raise SurfaceSlotMigrationError(f"{label} was not preserved")
    source_camera = _camera_snapshot(source_ram)
    if _sha256(source_camera) != SOURCE_CAMERA_SHA256:
        raise SurfaceSlotMigrationError("Pinned camera identity changed")
    if _camera_snapshot(target_ram) != source_camera:
        raise SurfaceSlotMigrationError("Camera state was not preserved")
    source_arenas = _packet_arenas(source_ram)
    if _sha256(source_arenas) != PACKET_ARENAS_SHA256:
        raise SurfaceSlotMigrationError("Pinned model-20 packet arenas changed")
    if _packet_arenas(target_ram) != source_arenas:
        raise SurfaceSlotMigrationError("Model-20 packet arenas were not preserved")


def migrate_v221_slot1_to_v222(
    state: bytes,
    *,
    old_disc: Path,
    new_disc: Path,
    zstd: _ZstdLike,
) -> tuple[bytes, dict[str, object]]:
    if (len(state), _sha256(state)) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise SurfaceSlotMigrationError(
            f"Source Slot 1 identity changed: {len(state)} bytes, SHA-256 {_sha256(state)}"
        )
    identities = (
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V221 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V222 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V221 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V222 CUE"),
    )
    for path, size, sha256, label in identities:
        _validate_file(path, size, sha256, label)

    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    if (
        len(old_table) != ARCHIVE_TABLE_SIZE
        or _sha256(old_table) != ARCHIVE_TABLE_SHA256
        or new_table != old_table
        or _diff_triplets(old_table, new_table) != ARCHIVE_TABLE_DIFFS
    ):
        raise SurfaceSlotMigrationError("V221/V222 archive-table contract changed")

    old_field = _disc_field621(
        old_disc,
        bundle_size=OLD_FIELD621_BUNDLE_SIZE,
        bundle_sha256=OLD_FIELD621_BUNDLE_SHA256,
    )
    new_field = _disc_field621(
        new_disc,
        bundle_size=NEW_FIELD621_BUNDLE_SIZE,
        bundle_sha256=NEW_FIELD621_BUNDLE_SHA256,
    )
    if any(
        old_field.parts[index].data != new_field.parts[index].data
        for index in range(9)
        if index != 5
    ):
        raise SurfaceSlotMigrationError("V222 field 621 changed outside header and ATEL")

    source_payload, frame_start, source_prefix = _unpack_state(state, zstd)
    if (
        frame_start != SOURCE_PREFIX_SIZE
        or len(state) - frame_start != SOURCE_COMPRESSED_SIZE
        or _sha256(source_prefix) != SOURCE_PREFIX_SHA256
        or (len(source_payload), _sha256(source_payload))
        != (SOURCE_PAYLOAD_SIZE, SOURCE_PAYLOAD_SHA256)
    ):
        raise SurfaceSlotMigrationError("Pinned source state decomposition changed")
    try:
        table_offset, volatile_bytes = media_migration._find_resident_archive_table(
            source_payload, old_table
        )
    except media_migration.StateMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc
    resident_table = source_payload[table_offset : table_offset + ARCHIVE_TABLE_SIZE]
    if (
        table_offset != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or volatile_bytes != 1
        or resident_table[-1] != EXPECTED_VOLATILE_TABLE_VALUE
        or _sha256(resident_table) != RESIDENT_ARCHIVE_TABLE_SHA256
    ):
        raise SurfaceSlotMigrationError("Pinned resident archive table changed")

    ram_offset, source_ram = _ram_from_payload(source_payload)
    if _sha256(source_ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("Pinned V221 RAM identity changed")
    target_ram, categories = _build_target_ram(
        source_ram, old_field=old_field, new_field=new_field
    )
    _validate_preserved_state(source_ram, target_ram)

    output_payload = bytearray(source_payload)
    output_payload[ram_offset : ram_offset + RAM_SIZE] = target_ram
    output_payload_bytes = bytes(output_payload)
    expected_ram_offsets = frozenset().union(*categories.values())
    expected_payload_offsets = frozenset(
        ram_offset + offset for offset in expected_ram_offsets
    )
    changed_payload_offsets = frozenset(_diff_offsets(source_payload, output_payload_bytes))
    if (
        changed_payload_offsets != expected_payload_offsets
        or len(changed_payload_offsets) != EXPECTED_PAYLOAD_BYTES_CHANGED
        or _sha256(output_payload_bytes) != OUTPUT_PAYLOAD_SHA256
    ):
        raise SurfaceSlotMigrationError("Payload changed outside the exact V222 whitelist")
    if output_payload_bytes[
        table_offset : table_offset + ARCHIVE_TABLE_SIZE
    ] != resident_table:
        raise SurfaceSlotMigrationError("Resident archive table was not preserved")

    provisional_prefix = _expected_prefix(
        source_prefix, compressed_size=OUTPUT_COMPRESSED_SIZE
    )
    result = _pack_state(provisional_prefix, output_payload_bytes, zstd)
    output_payload_check, output_frame_start, output_prefix = _unpack_state(result, zstd)
    if (
        output_frame_start != SOURCE_PREFIX_SIZE
        or len(result) - output_frame_start != OUTPUT_COMPRESSED_SIZE
        or output_payload_check != output_payload_bytes
        or output_prefix
        != _expected_prefix(source_prefix, compressed_size=OUTPUT_COMPRESSED_SIZE)
        or _sha256(output_prefix) != OUTPUT_PREFIX_SHA256
        or (len(result), _sha256(result)) != (OUTPUT_STATE_SIZE, OUTPUT_STATE_SHA256)
    ):
        raise SurfaceSlotMigrationError("Final V222 state identity or round trip changed")

    report: dict[str, object] = {
        "source_sha256": SOURCE_STATE_SHA256,
        "output_sha256": OUTPUT_STATE_SHA256,
        "source_size": len(state),
        "output_size": len(result),
        "payload_size": len(output_payload_bytes),
        "payload_sha256": OUTPUT_PAYLOAD_SHA256,
        "ram_sha256": OUTPUT_RAM_SHA256,
        "payload_bytes_changed": len(changed_payload_offsets),
        "ram_bytes_changed": len(expected_ram_offsets),
        "header_bytes_changed": len(categories["header"]),
        "script_bytes_changed": len(categories["script"]),
        "actor_bytes_changed": len(categories["actors"]),
        "actor_data_bytes_changed": len(categories["actor_data"]),
        "sprite_core_bytes_changed": len(categories["sprites"]),
        "archive_table_bytes_changed": len(ARCHIVE_TABLE_DIFFS),
        "resident_archive_table_sha256": RESIDENT_ARCHIVE_TABLE_SHA256,
        "resident_header_sha256": TARGET_LOADED_HEADER_SHA256,
        "resident_script_sha256": NEW_SCRIPT_SHA256,
        "actor_array_sha256": TARGET_ACTOR_ARRAY_SHA256,
        "actor_data_sha256": TARGET_ACTOR_DATA_SHA256,
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "dynamic_leaf_positions": {
            f"e{entity}": list(position)
            for entity, position in DYNAMIC_PLACEMENTS.items()
        },
        "static_threshold_placements": {
            f"e{entity}": {"position": list(position), "yaw": yaw}
            for entity, (_matrix, position, yaw) in STATIC_PLACEMENTS.items()
        },
        "game_camera_dialogue_walkmesh_models_preserved": True,
        "model20_packet_arenas_preserved": True,
        "archive_table_unchanged": True,
        "volatile_archive_table_byte_preserved": True,
        "round_trip_verified": True,
    }
    return result, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "state",
        nargs="?",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "save_candidates"
            / "SLUS-00669_1_v221_from_e4aea385_native_threshold_aprons.sav"
        ),
    )
    parser.add_argument(
        "--old-disc",
        type=Path,
        default=PROJECT_ROOT / "output" / OLD_CUE_NAME.replace(".cue", ".bin"),
    )
    parser.add_argument(
        "--new-disc",
        type=Path,
        default=PROJECT_ROOT / "output" / NEW_CUE_NAME.replace(".cue", ".bin"),
    )
    parser.add_argument(
        "--zstd", type=Path, default=PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "save_candidates"
            / "SLUS-00669_1_v222_from_27710b20_flush_doors.sav"
        ),
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        source = args.state.resolve()
        output = args.output.resolve()
        report_path = (
            args.report.resolve()
            if args.report is not None
            else output.with_suffix(".json")
        )
        if source == output:
            raise SurfaceSlotMigrationError("Output must not overwrite the source state")
        if output == LIVE_SLOT1:
            raise SurfaceSlotMigrationError("The migration tool never writes live Slot 1")
        if output.exists() and not args.force:
            raise SurfaceSlotMigrationError(f"Output already exists: {output}")
        if report_path in {source, output, LIVE_SLOT1}:
            raise SurfaceSlotMigrationError(
                "Report must not overwrite source, candidate, or live Slot 1"
            )
        if report_path.exists() and not args.force:
            raise SurfaceSlotMigrationError(f"Report already exists: {report_path}")

        zstd = media_migration._Zstd(args.zstd.resolve())
        result, report = migrate_v221_slot1_to_v222(
            source.read_bytes(),
            old_disc=args.old_disc.resolve(),
            new_disc=args.new_disc.resolve(),
            zstd=zstd,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        if output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Written V222 candidate changed on disk")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote validated V222 candidate: {output}")
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, media_migration.StateMigrationError, SurfaceSlotMigrationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
