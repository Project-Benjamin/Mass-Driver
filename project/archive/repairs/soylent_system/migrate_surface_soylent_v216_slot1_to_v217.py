#!/usr/bin/env python3
"""Build the exact V217 door-clearance candidate from the audited V216 Slot 1.

The source is paused in field 593 with Fei immediately south-east of the
doctor-office doorway.  The old circular collision seal touches him before he
can cross the retail walkmesh's narrow aperture.  V217 keeps the walkmesh and
native Cross action exact, installs a 41-byte leader-position poll in a
verified retired 87-byte cavity, and changes only entity 20's seal to the
aperture-aligned rectangle used by the new on-disc field.

The helper is fail-closed, does not grow the resident ATEL allocation, writes
only a new candidate, and never writes the live DuckStation Slot 1.
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

SOURCE_STATE_SIZE = 1_853_093
SOURCE_STATE_SHA256 = "1114bf36b351a450a606c693b807a3116bccf6613b59b068552d52cdce2fa73e"
SOURCE_COMPRESSED_SIZE = 1_813_726
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "6b18f6d7ccbce66369d1e9075fb40ab1a4579e200b53110ef15a5cc92a060823"
EXPECTED_FRAME_START = 0x99C7
EXPECTED_SOURCE_PREFIX_SHA256 = "fce255d29f75f387b9a6465e8145a03f283c91cf3677b17db1942072407c9eca"
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
SOURCE_RAM_SHA256 = "10db98a3aa829e392574c8215f1422a56c26985a5cd02c84c5f3d3290ced1af2"
OUTPUT_RAM_SHA256 = "861e70e901d5d3bac60c0d2d3ab5ee180224efc7e32927ae3b1305196ff19b02"

OLD_DISC_SIZE = NEW_DISC_SIZE = 698_642_784
OLD_DISC_SHA256 = "3764d6584fce3f590298cdc4e752432f4da1ec7770aa3416141296e6a79b4498"
NEW_DISC_SHA256 = "b672e95c592efe2978cd46a10ee3cde3b86d6af89a1db69a02646fbb0789184a"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v216.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v217.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = "5019b53f2c2ffa5e7b3a52cd194da14b2f36ba8207b5dd2c9210d7d77afce722"
NEW_CUE_SHA256 = "2f921abda6c2b87ed5ab71896e1148965e59f464be0657b42bcbf9107d09d297"

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = "573f7d4f8dfb68f9ff408124a321a238bc07565d22c26a1355594f0fbffc15ab"
NEW_ARCHIVE_TABLE_SHA256 = "f8a18fbbe9fd1c211d4d3cf4f9cb3fe2d9a7e7384ec2128a5f641fa005f33d9e"
ARCHIVE_TABLE_DIFFS = (
    (0x30C4, 0xBC, 0xCC),
    (0x30D2, 0xD4, 0xE4),
    (0x30E0, 0x94, 0xA0),
)
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
EXPECTED_VOLATILE_TABLE_VALUE = 0xE0
SOURCE_RESIDENT_TABLE_SHA256 = "734c6f92419c1aa5917567a9f774cca2429287f07697551a470fd347d0da7ac6"
OUTPUT_RESIDENT_TABLE_SHA256 = "4ea43d37f2b380ea1e9eb519ca702d1c74fc5d3645ca9ff2752d5f403f8532e1"

OLD_HEADER_SIZE = NEW_HEADER_SIZE = 960
OLD_HEADER_SHA256 = "f40da1a82556d51f663cdafec037e68cbbb3c23e01b9c9bde53b2a79e1ec5f3d"
NEW_HEADER_SHA256 = "09da55f31308e32612bdc10de60fa3724c4f3b18d4d3735dad04ded314797b44"
HEADER_DIFFS = (
    (0x0148, 0x58, 0x64),
    (0x014C, 0xF4, 0x00),
    (0x014D, 0x3B, 0x3C),
    (0x0150, 0x90, 0x9C),
    (0x02DC, 0xFA, 0x0A),
    (0x02DD, 0x00, 0x01),
)
HEADER_ACTOR_TABLE_OFFSET = 0x190
HEADER_E20_Z_OFFSET = 0x2DC

OLD_SCRIPT_SIZE = NEW_SCRIPT_SIZE = 3_421
OLD_SCRIPT_SHA256 = "99b1323786e554f3bdaff39ba08bfcf8b27d2c7640558ff5984de8fe1cd8daad"
NEW_SCRIPT_SHA256 = "d7f51dae2c8d7aa2520050c59576a4562f0c91c05708486d4ef3369095d754c4"
NORMAL_BYTECODE_OFFSET = 0x5C4
NORMAL_BYTECODE_SIZE = 0x799
NORMAL_SEAL_INIT_PC = 0x0762
NORMAL_NATIVE_ACTION_PC = 0x0781

RESIDENT_SCRIPT_SIZE = 3_392
SOURCE_RESIDENT_SCRIPT_SHA256 = "62ade3971f6caa319652757a3138e1509f5abff9239bc0fb597d0c4cc82badff"
OUTPUT_RESIDENT_SCRIPT_SHA256 = "b521b39029c29c34ae4476ed089cbbb590692574b07352eff577906f2f45e8c5"
EXPECTED_SCRIPT_PAYLOAD_OFFSET = 0x10CD56
EXPECTED_SCRIPT_GUEST_POINTER = 0x8010B2F4
EXPECTED_VM_SCRIPT_GUEST_POINTER = 0x8010B8B8
SCRIPT_ALLOCATED_CAPACITY = 0x0D50
SCRIPT_GAP_SIZE = 48
SCRIPT_GAP_SHA256 = "3edf0e090fcbc4fa185663d9af64830047f1408d1e7d3fa8db1eb5bc50674e41"
RESIDENT_BYTECODE_OFFSET = 0x5C4
RESIDENT_BYTECODE_SIZE = 0x77C
SHARED_STOP_PC = 0x068C
COMPACT_SEAL_STOP_PC = 0x0728
COMPACT_SEAL_RELEASE_PC = 0x0729
COMPACT_SEAL_INIT_PC = 0x0745
COMPACT_NATIVE_ACTION_PC = 0x0764

FORWARD_POLL_PC = 0x044E
FORWARD_POLL_CAVITY_END_PC = 0x04A5
FORWARD_POLL_CAVITY_ENTITY = 14
FORWARD_POLL_CAVITY_SCRIPT = 5
FORWARD_POLL = bytes.fromhex(
    "2D FF F8 07 FA 07 FC 07 02 F8 07 C0 FF 44 71 04 "
    "02 F8 07 41 00 43 71 04 02 FA 07 E6 00 44 71 04 "
    "09 11 22 26 00 80 01 4E 04"
)
FORWARD_POLL_SOURCE_CAVITY = bytes.fromhex(
    "21 30 81 4A 5A 00 3E 00 C0 4A 5A 00 C8 FF C0 69 06 80 "
    "26 0A 80 2C 04 FE 0D 01 80 D2 24 00 00 9C 09 FF C5 26 "
    "0A 80 2C 00 D2 25 00 00 9C 09 FE C6 26 0A 80 69 00 80 "
    "26 05 80 D2 26 00 00 9C 09 FF C7 FE 24 26 04 80 FE AA "
    "FF 35 E0 00 00 00 40 FE 53 2C 00 69 06 80 00"
)
OLD_SEAL_INIT = bytes.fromhex(
    "0B 00 80 19 00 00 FA 00 C0 1A 00 F8 04 00 20 F8 "
    "07 04 00 18 00 00 64 0E F8 00 10 00 2A 23 00"
)
NEW_SEAL_INIT = bytes.fromhex(
    "0B 00 80 19 00 00 0A 01 C0 1A 00 F8 00 00 20 F8 "
    "07 04 00 18 18 08 64 08 F8 00 10 00 2A 23 00"
)
NATIVE_ACTION = bytes.fromhex(
    "FE 54 74 77 80 09 12 C4 09 14 24 98 6D 82 09 80 "
    "00 BC 75 3D 80 01 10 00"
)

SOURCE_RESIDENT_DIALOGUE_SIZE = OUTPUT_RESIDENT_DIALOGUE_SIZE = 5_474
SOURCE_RESIDENT_DIALOGUE_SHA256 = OUTPUT_RESIDENT_DIALOGUE_SHA256 = (
    "3e7c7efacf25102e43ac08d3bc64f2bf9d90cb04eb18470c1fd6c2f51a5dbdda"
)
OLD_DIALOGUE_SIZE = NEW_DIALOGUE_SIZE = 5_488
OLD_DIALOGUE_SHA256 = NEW_DIALOGUE_SHA256 = (
    "f875da417daab6b7d8f76e4d318efe99d90f4e813debbcdf5c1324a155e67636"
)
EXPECTED_DIALOGUE_PAYLOAD_OFFSET = 0x10DAC6
EXPECTED_DIALOGUE_GUEST_POINTER = 0x8010C064
DIALOGUE_ALLOCATED_CAPACITY = 5_492
EXPECTED_WALKMESH_PAYLOAD_OFFSET = 0x10F042
DIALOGUE_GAP_SIZE = 26
DIALOGUE_GAP_SHA256 = "7ba2053e722728bc8ac47e00ab36580454e6264cad00c524d149649e9c279c46"
WALKMESH_SIZE = 1_948
WALKMESH_SHA256 = "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d8cca4238393571df"

EXPECTED_FIELD = 593
EXPECTED_ACTOR_COUNT = 35
SCRIPT_ENTITY_COUNT = 21
EXPECTED_ACTOR_ARRAY_GUEST_POINTER = 0x80112DB0
FIELD_CUR_DIALOGUE_FILE = 0x0ADBF0
FIELD_SMALL_COMPONENT = 0x0ADBF4
EXPECTED_SMALL_COMPONENT_POINTER = 0x8010C04C
GAME_SCENE_MAP = 0x04F34C
EXPECTED_VM_ACTOR_GUEST_POINTER = 0x80115D30

ACTOR_RECORD_SIZE = FIELD_ACTOR_STRIDE
ACTOR_DATA_SIZE = 0x138
ACTOR_DATA_FLAGS_OFFSET = 0x00
ACTOR_DATA_SECONDARY_FLAGS_OFFSET = 0x04
ACTOR_DATA_SURFACES_OFFSET = 0x08
ACTOR_DATA_BOUNDS_OFFSET = 0x18
ACTOR_DATA_POSITION_OFFSET = 0x20
ACTOR_DATA_OLD_POSITION_OFFSET = 0x68
ACTOR_SCRIPT_SLOT_OFFSET = 0x8C
ACTOR_CURRENT_PC_OFFSET = 0xCC
ACTOR_FACING_OFFSET = 0x106

CONTROLLER_ENTITY = 0
FEI_ENTITY = 1
CROSS_CARRIER_ENTITY = 17
DOOR_LEAF_ENTITY = 18
SEAL_ENTITY = 20
EXPECTED_ACTOR_DATA_POINTERS = {
    0: 0x113A4C,
    1: 0x113C04,
    2: 0x113DBC,
    3: 0x113F74,
    17: 0x115784,
    18: 0x1159C0,
    19: 0x115B78,
    20: 0x115D30,
}
EXPECTED_ACTOR_RECORD_SHA256 = {
    0: "94ae9b6d64e1b0e7123d181815600ceefd386ff6380befcc29ca9ca715366b3f",
    1: "c468785f281274b4febddca743af14ab3346e46f738b56674cc338eef4510420",
    2: "cfe7e98f06cb175c7e623d751f4e7889e403e155fae35e0d18b6743740cb0d73",
    3: "5ffea214d519265df0eb021dfd01ba48077c9d5a62b307a527b84ec887cc2415",
    17: "5a55c16924449d96fd1998ffad6d1855a5a85d97a9eb66a124369c7743daa6a4",
    18: "7a0273a4c5f9760e093dbb73a8e460e63e4fcaf8f5148236242074b6dddb178c",
    19: "749764abe38d39ea23b27657b070422d12707f243feb7e6a56475f1f6a50a82f",
    20: "6b37b3803fcc00fd3af21b9721c00b87e1a5ec92c3a7462045bfd5cee99decab",
}
EXPECTED_ACTOR_DATA_SHA256 = {
    0: "a0dd538fd1b13c04c8782043409f2de5baeaa310332c35a2064b201b77e211ed",
    1: "afe42791af623ae4b0d7662deb7f03421ea2b4f223ed0932698309f0559b73a2",
    2: "01f8b8f6b47165c2d93367e17b39b019ed6874f5ff112e4110a070c9955f09e3",
    3: "67e0a8a9733d0dd27c3116e3cc4813c93be34754cd5521296b5deb91fe587e15",
    17: "52e08318460873939b66b4944b85058164f7709d44428b331343b163727b7c2c",
    18: "10616488fe5c0817d866f0fc06694f8cefa2e436756d24986ea09cc06a8d44de",
    19: "0af39220de187ef10a6bef5a674c8b8ebf7a404f965662429ceb3483ad954ac3",
    20: "7079d9d74b5c1814c0f12b4775e2df254f5152922898001c78c72a6d09ee379b",
}
OUTPUT_E20_RECORD_SHA256 = "82b03765d7e9a268d5666cf7250e3b3901fb0ece245e3bbaeda50578612c3e50"
OUTPUT_E20_ACTOR_DATA_SHA256 = "1f7f4e2375f7bc32ef9ac9e7218fa332259661b3c6dfb15a7f3e0bbd2a6903ca"

EXPECTED_FEI_POSITION = (2_624_381, 0, 14_973_253)
EXPECTED_FEI_TRIANGLES = (15, 0, 0, 0)
EXPECTED_FEI_FACING = 0x0800
EXPECTED_FEI_CURRENT = bytes.fromhex("5F 01 00 00")
EXPECTED_CONTROLLER_SLOT0 = bytes.fromhex("8C 06 00 FF FF FF 3C 00")
EXPECTED_CONTROLLER_CURRENT = bytes.fromhex("8C 06 00 00")
EXPECTED_LEAF_SLOT4 = bytes.fromhex("FF FF 00 FF FF FF 3C 00")
EXPECTED_LEAF_CURRENT = bytes.fromhex("8C 06 00 00")
EXPECTED_SEAL_SLOT0 = bytes.fromhex("28 07 00 FF FF FF 3C 00")
EXPECTED_SEAL_CURRENT = bytes.fromhex("28 07 00 00")

OLD_E20_FLAGS = bytes.fromhex("30 01 02 00")
NEW_E20_FLAGS = bytes.fromhex("30 21 02 00")
OLD_E20_BOUNDS = bytes.fromhex("10 00 C8 00 10 00 1C 00")
NEW_E20_BOUNDS = bytes.fromhex("30 00 C8 00 10 00 10 00")
OLD_E20_CURRENT_POSITION = bytes.fromhex("00 00 00 00 00 00 00 00 00 00 FA 00")
NEW_E20_CURRENT_POSITION = bytes.fromhex("00 00 00 00 00 00 00 00 00 00 0A 01")
OLD_E20_OLD_POSITION = bytes.fromhex("00 00 00 00 FA 00 00 00")
NEW_E20_OLD_POSITION = bytes.fromhex("00 00 00 00 0A 01 00 00")
OLD_E20_RECORD_Z = bytes.fromhex("FA 00 00 00")
NEW_E20_RECORD_Z = bytes.fromhex("0A 01 00 00")

# Each offset below is relative to the serialized 2 MiB PSX RAM block.
E20_RECORD_RAM_OFFSET = 0x1134E0
E20_ACTOR_DATA_RAM_OFFSET = 0x115D30
RUNTIME_PATCHES = (
    (E20_RECORD_RAM_OFFSET + 0x28, OLD_E20_RECORD_Z, NEW_E20_RECORD_Z, "e20 matrix 0 Z"),
    (E20_RECORD_RAM_OFFSET + 0x48, OLD_E20_RECORD_Z, NEW_E20_RECORD_Z, "e20 matrix 1 Z"),
    (E20_ACTOR_DATA_RAM_OFFSET, OLD_E20_FLAGS, NEW_E20_FLAGS, "e20 rectangle flag"),
    (
        E20_ACTOR_DATA_RAM_OFFSET + ACTOR_DATA_BOUNDS_OFFSET,
        OLD_E20_BOUNDS,
        NEW_E20_BOUNDS,
        "e20 rectangular bounds",
    ),
    (
        E20_ACTOR_DATA_RAM_OFFSET + ACTOR_DATA_POSITION_OFFSET,
        OLD_E20_CURRENT_POSITION,
        NEW_E20_CURRENT_POSITION,
        "e20 current position",
    ),
    (
        E20_ACTOR_DATA_RAM_OFFSET + ACTOR_DATA_OLD_POSITION_OFFSET,
        OLD_E20_OLD_POSITION,
        NEW_E20_OLD_POSITION,
        "e20 old position",
    ),
)

CLOSED_LEAF_MATRIX = bytes.fromhex(
    "00 00 00 00 00 10 00 00 00 10 00 00 00 F0 00 00 00 00"
)
CLOSED_LEAF_HELPER_OPERAND = 0x040E
EXPECTED_CLOSED_LEAF_HELPER = 0

DIALOG_WINDOWS = 0x0C2698
DIALOG_WINDOW_STRIDE = 0x498
DIALOG_WINDOWS_SIZE = 4 * DIALOG_WINDOW_STRIDE
DIALOG_WINDOW_STATUS_OFFSET = 0x40E
EXPECTED_DIALOG_WINDOWS_SHA256 = "5774957457b6de63f3e7cb1c2971c5ea4ec1623a13d6a72cac7bd2670482706c"
WINDOW0_START_POINTER_OFFSET = DIALOG_WINDOWS + 0xA8
WINDOW0_CURRENT_POINTER_OFFSET = DIALOG_WINDOWS + 0x34
EXPECTED_WINDOW0_START_POINTER = 0x8010D560
EXPECTED_WINDOW0_CURRENT_POINTER = 0x8010D5B9

FIELD_VARIABLE_BACKUP_OFFSET = 0x1930
FIELD_VARIABLE_BANK_SIZE = 0x400
QUARANTINE_CARD_OPERAND = 0x021A
QUARANTINE_CARD_BIT = 8
EXPECTED_QUARANTINE_WORD = 0x01FD
EXPECTED_FIELD_VARIABLE_BANK_SHA256 = "ce57d9877ed1971befd68330a9cad53ebdddc2f4d7a4e540793b8fe35ffc6a50"
EXPECTED_GAMESTATE_SHA256 = "57bdd982ddb553f5bf36058698bdcb6dfa2ad822812914c9ecc186ff6497e027"
EXPECTED_CAMERA_SHA256 = "8501aaca89ed61d5968ee3ea39c648a7f8fc29cfb398215a3463517fcccf470b"

# The loaded field-header allocation is retained for provenance but is not
# consulted by the running actor scheduler.  It must remain byte-exact; the
# live FieldActor and ActorData structures above receive the V217 z position.
LOADED_HEADER_RAM_OFFSET = 0x1D6D3C
LOADED_HEADER_SIZE = 960
EXPECTED_LOADED_HEADER_SHA256 = "34380af758547922f0a0abe2bf9dc88479847cd2a60acc71cf472d305d26efa4"

EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED = 3
EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED = 46
EXPECTED_RUNTIME_BYTES_CHANGED = 11
EXPECTED_PAYLOAD_BYTES_CHANGED = 60
EXPECTED_OUTPUT_PAYLOAD_SHA256 = "d13d5b3db1cea6aea600dfed8d5864ab0d5895758c2f9f514976bb7b83d2b411"
EXPECTED_OUTPUT_SIZE = 1_679_396
EXPECTED_OUTPUT_COMPRESSED_SIZE = 1_640_029
EXPECTED_OUTPUT_SHA256 = "577668ae2ffd55b3132b68f5fa7d19a9f813e6f5769b8427f4362e47b63d8596"
EXPECTED_OUTPUT_PREFIX_SHA256 = "368b1666fffb50031f9e381fe4e23db7282c6427d1663ee7db02a2521f4159a5"


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output whenever a pinned V216/V217 contract drifts."""


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


def _diff_triplets(before: bytes, after: bytes) -> tuple[tuple[int, int, int], ...]:
    return tuple((i, before[i], after[i]) for i in _diff_offsets(before, after))


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


def _actor_data_offset(ram: bytes, actor_base: int, entity: int) -> int:
    pointer = struct.unpack_from(
        "<I", ram, actor_base + entity * FIELD_ACTOR_STRIDE + FIELD_ACTOR_DATA_POINTER
    )[0]
    offset = pointer & 0x1FFFFFFF
    if not 0 < offset <= RAM_SIZE - ACTOR_DATA_SIZE:
        raise SurfaceSlotMigrationError(f"e{entity} ActorData pointer is outside PSX RAM")
    return offset


def _patch_reconstruction(source: bytes, patches: Sequence[tuple[int, bytes, bytes]]) -> bytes:
    result = bytearray(source)
    for offset, old, new in patches:
        if len(old) != len(new) or result[offset : offset + len(old)] != old:
            raise SurfaceSlotMigrationError(f"Patch source drifted at 0x{offset:X}")
        result[offset : offset + len(new)] = new
    return bytes(result)


def _normal_script_patches() -> tuple[tuple[int, bytes, bytes], ...]:
    return (
        (0x0086, struct.pack("<H", SHARED_STOP_PC), struct.pack("<H", FORWARD_POLL_PC)),
        (
            NORMAL_BYTECODE_OFFSET + FORWARD_POLL_PC,
            FORWARD_POLL_SOURCE_CAVITY[: len(FORWARD_POLL)],
            FORWARD_POLL,
        ),
        (NORMAL_BYTECODE_OFFSET + NORMAL_SEAL_INIT_PC, OLD_SEAL_INIT, NEW_SEAL_INIT),
    )


def _compact_script_patches() -> tuple[tuple[int, bytes, bytes], ...]:
    return (
        (0x0086, struct.pack("<H", SHARED_STOP_PC), struct.pack("<H", FORWARD_POLL_PC)),
        (
            RESIDENT_BYTECODE_OFFSET + FORWARD_POLL_PC,
            FORWARD_POLL_SOURCE_CAVITY[: len(FORWARD_POLL)],
            FORWARD_POLL,
        ),
        (RESIDENT_BYTECODE_OFFSET + COMPACT_SEAL_INIT_PC, OLD_SEAL_INIT, NEW_SEAL_INIT),
    )


def _validate_resources(
    old_disc: Path,
    new_disc: Path,
    old_header: bytes,
    new_header: bytes,
    old_script: bytes,
    new_script: bytes,
    old_dialogue: bytes,
    new_dialogue: bytes,
) -> tuple[bytes, bytes]:
    identities = (
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V216 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V217 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V216 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V217 CUE"),
    )
    for path, size, sha, label in identities:
        if not path.is_file() or path.stat().st_size != size or _file_sha256(path) != sha:
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    blobs = (
        (old_header, OLD_HEADER_SIZE, OLD_HEADER_SHA256, "V216 header"),
        (new_header, NEW_HEADER_SIZE, NEW_HEADER_SHA256, "V217 header"),
        (old_script, OLD_SCRIPT_SIZE, OLD_SCRIPT_SHA256, "V216 script"),
        (new_script, NEW_SCRIPT_SIZE, NEW_SCRIPT_SHA256, "V217 script"),
        (old_dialogue, OLD_DIALOGUE_SIZE, OLD_DIALOGUE_SHA256, "V216 dialogue"),
        (new_dialogue, NEW_DIALOGUE_SIZE, NEW_DIALOGUE_SHA256, "V217 dialogue"),
    )
    for blob, size, sha, label in blobs:
        if (len(blob), _sha256(blob)) != (size, sha):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    if old_dialogue != new_dialogue:
        raise SurfaceSlotMigrationError("V217 unexpectedly changes field-593 dialogue")
    if _diff_triplets(old_header, new_header) != HEADER_DIFFS:
        raise SurfaceSlotMigrationError("V216/V217 field-header delta drifted")
    if struct.unpack_from("<h", old_header, HEADER_E20_Z_OFFSET)[0] != 250 or struct.unpack_from(
        "<h", new_header, HEADER_E20_Z_OFFSET
    )[0] != 266:
        raise SurfaceSlotMigrationError("V217 field-header e20 position drifted")

    expected_script = _patch_reconstruction(old_script, _normal_script_patches())
    if expected_script != new_script or len(_diff_offsets(old_script, new_script)) != EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED:
        raise SurfaceSlotMigrationError("V216/V217 normal script delta drifted")
    old_editor, new_editor = AtelScript(old_script), AtelScript(new_script)
    if (
        old_editor.entity_count != SCRIPT_ENTITY_COUNT
        or new_editor.entity_count != SCRIPT_ENTITY_COUNT
        or old_editor.bytecode_offset != NORMAL_BYTECODE_OFFSET
        or new_editor.bytecode_offset != NORMAL_BYTECODE_OFFSET
        or old_editor.bytecode_size != NORMAL_BYTECODE_SIZE
        or new_editor.bytecode_size != NORMAL_BYTECODE_SIZE
        or old_editor.get_script_pointer(0, 1) != SHARED_STOP_PC
        or new_editor.get_script_pointer(0, 1) != FORWARD_POLL_PC
        or old_editor.get_script_pointer(SEAL_ENTITY, 0) != NORMAL_SEAL_INIT_PC
        or new_editor.get_script_pointer(SEAL_ENTITY, 0) != NORMAL_SEAL_INIT_PC
        or old_editor.get_script_pointer(CROSS_CARRIER_ENTITY, 2) != NORMAL_NATIVE_ACTION_PC
        or new_editor.get_script_pointer(CROSS_CARRIER_ENTITY, 2) != NORMAL_NATIVE_ACTION_PC
        or old_editor.bytecode[FORWARD_POLL_PC:FORWARD_POLL_CAVITY_END_PC] != FORWARD_POLL_SOURCE_CAVITY
        or new_editor.bytecode[FORWARD_POLL_PC : FORWARD_POLL_PC + len(FORWARD_POLL)] != FORWARD_POLL
        or new_editor.bytecode[FORWARD_POLL_PC + len(FORWARD_POLL) : FORWARD_POLL_CAVITY_END_PC]
        != FORWARD_POLL_SOURCE_CAVITY[len(FORWARD_POLL) :]
        or old_editor.bytecode[NORMAL_SEAL_INIT_PC : NORMAL_SEAL_INIT_PC + len(OLD_SEAL_INIT)] != OLD_SEAL_INIT
        or new_editor.bytecode[NORMAL_SEAL_INIT_PC : NORMAL_SEAL_INIT_PC + len(NEW_SEAL_INIT)] != NEW_SEAL_INIT
        or old_editor.bytecode[NORMAL_NATIVE_ACTION_PC:] != NATIVE_ACTION
        or new_editor.bytecode[NORMAL_NATIVE_ACTION_PC:] != NATIVE_ACTION
    ):
        raise SurfaceSlotMigrationError("V216/V217 normal ATEL topology drifted")

    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    if (
        _sha256(old_table) != OLD_ARCHIVE_TABLE_SHA256
        or _sha256(new_table) != NEW_ARCHIVE_TABLE_SHA256
        or _diff_triplets(old_table, new_table) != ARCHIVE_TABLE_DIFFS
    ):
        raise SurfaceSlotMigrationError("V216/V217 archive-table delta drifted")
    return old_table, new_table


def _build_resident_script(source: bytes, old_script: bytes, new_script: bytes) -> bytes:
    if (len(source), _sha256(source)) != (RESIDENT_SCRIPT_SIZE, SOURCE_RESIDENT_SCRIPT_SHA256):
        raise SurfaceSlotMigrationError("Compact V216 resident script identity drifted")
    editor = AtelScript(source)
    old_editor, new_editor = AtelScript(old_script), AtelScript(new_script)
    if (
        editor.entity_count != SCRIPT_ENTITY_COUNT
        or editor.bytecode_offset != RESIDENT_BYTECODE_OFFSET
        or editor.bytecode_size != RESIDENT_BYTECODE_SIZE
        or editor.get_script_pointer(0, 1) != SHARED_STOP_PC
        or editor.get_script_pointer(SEAL_ENTITY, 0) != COMPACT_SEAL_INIT_PC
        or editor.get_script_pointer(CROSS_CARRIER_ENTITY, 2) != COMPACT_NATIVE_ACTION_PC
        or any(editor.get_script_pointer(FORWARD_POLL_CAVITY_ENTITY, script) != SHARED_STOP_PC for script in range(32))
        or editor.bytecode[FORWARD_POLL_PC:FORWARD_POLL_CAVITY_END_PC] != FORWARD_POLL_SOURCE_CAVITY
        or editor.bytecode[COMPACT_SEAL_INIT_PC : COMPACT_SEAL_INIT_PC + len(OLD_SEAL_INIT)] != OLD_SEAL_INIT
        or editor.bytecode[COMPACT_NATIVE_ACTION_PC:] != NATIVE_ACTION
        or editor.bytecode[COMPACT_SEAL_INIT_PC:] != old_editor.bytecode[NORMAL_SEAL_INIT_PC:]
    ):
        raise SurfaceSlotMigrationError("Compact V216 resident ATEL topology drifted")
    for entity in range(editor.entity_count):
        for script in range(32):
            pointer = editor.get_script_pointer(entity, script)
            if FORWARD_POLL_PC <= pointer < FORWARD_POLL_CAVITY_END_PC:
                raise SurfaceSlotMigrationError("Retired forward-poll cavity acquired an entry point")

    result = _patch_reconstruction(source, _compact_script_patches())
    installed = AtelScript(result)
    cavity_entries = tuple(
        (entity, script)
        for entity in range(installed.entity_count)
        for script in range(32)
        if FORWARD_POLL_PC <= installed.get_script_pointer(entity, script) < FORWARD_POLL_CAVITY_END_PC
    )
    pointer_diffs = tuple(
        (entity, script)
        for entity in range(editor.entity_count)
        for script in range(32)
        if editor.get_script_pointer(entity, script) != installed.get_script_pointer(entity, script)
    )
    if (
        (len(result), _sha256(result)) != (RESIDENT_SCRIPT_SIZE, OUTPUT_RESIDENT_SCRIPT_SHA256)
        or len(result) > SCRIPT_ALLOCATED_CAPACITY
        or len(_diff_offsets(source, result)) != EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED
        or pointer_diffs != ((0, 1),)
        or cavity_entries != ((0, 1),)
        or installed.get_script_pointer(0, 1) != FORWARD_POLL_PC
        or installed.bytecode[FORWARD_POLL_PC : FORWARD_POLL_PC + len(FORWARD_POLL)] != FORWARD_POLL
        or installed.bytecode[FORWARD_POLL_PC + len(FORWARD_POLL) : FORWARD_POLL_CAVITY_END_PC]
        != FORWARD_POLL_SOURCE_CAVITY[len(FORWARD_POLL) :]
        or installed.bytecode[COMPACT_SEAL_INIT_PC : COMPACT_SEAL_INIT_PC + len(NEW_SEAL_INIT)] != NEW_SEAL_INIT
        or installed.bytecode[COMPACT_SEAL_INIT_PC:] != new_editor.bytecode[NORMAL_SEAL_INIT_PC:]
        or installed.bytecode[COMPACT_NATIVE_ACTION_PC:] != NATIVE_ACTION
    ):
        raise SurfaceSlotMigrationError("Compact V217 resident ATEL construction drifted")
    return result


def _validate_walkmesh(walkmesh: bytes) -> None:
    if (len(walkmesh), _sha256(walkmesh)) != (WALKMESH_SIZE, WALKMESH_SHA256):
        raise SurfaceSlotMigrationError("Resident field-593 walkmesh identity drifted")
    layer_count = struct.unpack_from("<I", walkmesh, 0)[0]
    triangle_bytes = struct.unpack_from("<I", walkmesh, 4)[0]
    triangle_offset, vertex_offset = struct.unpack_from("<II", walkmesh, 0x18)
    if (layer_count, triangle_bytes, triangle_offset, vertex_offset) != (2, 560, 0x28, 0x258):
        raise SurfaceSlotMigrationError("Field-593 walkmesh layout drifted")

    def triangle(index: int) -> tuple[tuple[tuple[int, int, int], ...], tuple[int, int, int]]:
        record = triangle_offset + index * 14
        indices = struct.unpack_from("<3H", walkmesh, record)
        neighbors = struct.unpack_from("<3h", walkmesh, record + 6)
        vertices = tuple(struct.unpack_from("<hhhh", walkmesh, vertex_offset + vertex * 8)[:3] for vertex in indices)
        return vertices, neighbors

    if (
        triangle(15) != (((160, 0, 234), (69, 0, 66), (23, 0, 234)), (9, 16, -1))
        or triangle(3) != (((23, 0, 234), (-25, 0, 234), (0, 0, 243)), (16, 35, 34))
        or triangle(34) != (((0, 0, 306), (23, 0, 234), (0, 0, 243)), (-1, 3, 35))
        or triangle(35) != (((0, 0, 243), (-25, 0, 234), (0, 0, 306)), (3, -1, 34))
    ):
        raise SurfaceSlotMigrationError("Field-593 doorway walkmesh topology drifted")


def _validate_source(payload: bytes, old_table: bytes, old_header: bytes) -> dict[str, object]:
    if (len(payload), _sha256(payload)) != (SOURCE_PAYLOAD_SIZE, SOURCE_PAYLOAD_SHA256):
        raise SurfaceSlotMigrationError("V216 decompressed payload identity drifted")
    ram_offset, ram = _ram_from_payload(payload)
    if _sha256(ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("V216 serialized RAM identity drifted")
    table_offset, volatile = media_migration._find_resident_archive_table(payload, old_table)
    resident_table = payload[table_offset : table_offset + ARCHIVE_TABLE_SIZE]
    script = payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE]
    dialogue = payload[
        EXPECTED_DIALOGUE_PAYLOAD_OFFSET : EXPECTED_DIALOGUE_PAYLOAD_OFFSET + SOURCE_RESIDENT_DIALOGUE_SIZE
    ]
    walkmesh = payload[EXPECTED_WALKMESH_PAYLOAD_OFFSET : EXPECTED_WALKMESH_PAYLOAD_OFFSET + WALKMESH_SIZE]
    if (
        table_offset != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or volatile != 1
        or resident_table != old_table[:-1] + bytes((EXPECTED_VOLATILE_TABLE_VALUE,))
        or _sha256(resident_table) != SOURCE_RESIDENT_TABLE_SHA256
        or (len(script), _sha256(script)) != (RESIDENT_SCRIPT_SIZE, SOURCE_RESIDENT_SCRIPT_SHA256)
        or payload.count(script) != 1
        or payload.find(script) != EXPECTED_SCRIPT_PAYLOAD_OFFSET
        or (len(dialogue), _sha256(dialogue))
        != (SOURCE_RESIDENT_DIALOGUE_SIZE, SOURCE_RESIDENT_DIALOGUE_SHA256)
        or payload.count(dialogue) != 1
        or payload.find(dialogue) != EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        or _sha256(payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET])
        != SCRIPT_GAP_SHA256
        or _sha256(
            payload[
                EXPECTED_DIALOGUE_PAYLOAD_OFFSET + SOURCE_RESIDENT_DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET
            ]
        )
        != DIALOGUE_GAP_SHA256
    ):
        raise SurfaceSlotMigrationError("Resident field-593 component/table/gap identity drifted")
    _validate_walkmesh(walkmesh)

    actor_array_pointer = struct.unpack_from("<I", ram, FIELD_ACTORS)[0]
    if (
        (struct.unpack_from("<I", ram, GAME_SCENE_MAP)[0] & 0xFFF) != EXPECTED_FIELD
        or struct.unpack_from("<I", ram, FIELD_NUM_ACTORS)[0] != EXPECTED_ACTOR_COUNT
        or actor_array_pointer != EXPECTED_ACTOR_ARRAY_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0] != EXPECTED_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA)[0] != EXPECTED_VM_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_ACTOR)[0] != EXPECTED_VM_ACTOR_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_CUR_DIALOGUE_FILE)[0] != EXPECTED_DIALOGUE_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SMALL_COMPONENT)[0] != EXPECTED_SMALL_COMPONENT_POINTER
    ):
        raise SurfaceSlotMigrationError("Live field-593 pointer topology drifted")
    actor_base = actor_array_pointer & 0x1FFFFFFF
    actor_records: list[bytes] = []
    actor_data: list[bytes] = []
    actor_data_offsets: list[int] = []
    for entity in range(SCRIPT_ENTITY_COUNT):
        record_offset = actor_base + entity * FIELD_ACTOR_STRIDE
        data_offset = _actor_data_offset(ram, actor_base, entity)
        actor_records.append(bytes(ram[record_offset : record_offset + ACTOR_RECORD_SIZE]))
        actor_data.append(bytes(ram[data_offset : data_offset + ACTOR_DATA_SIZE]))
        actor_data_offsets.append(data_offset)
    for entity, pointer in EXPECTED_ACTOR_DATA_POINTERS.items():
        if (
            actor_data_offsets[entity] != pointer
            or _sha256(actor_records[entity]) != EXPECTED_ACTOR_RECORD_SHA256[entity]
            or _sha256(actor_data[entity]) != EXPECTED_ACTOR_DATA_SHA256[entity]
        ):
            raise SurfaceSlotMigrationError(f"Field runtime e{entity} identity drifted")

    controller = actor_data_offsets[CONTROLLER_ENTITY]
    fei = actor_data_offsets[FEI_ENTITY]
    cross = actor_data_offsets[CROSS_CARRIER_ENTITY]
    leaf = actor_data_offsets[DOOR_LEAF_ENTITY]
    seal = actor_data_offsets[SEAL_ENTITY]
    fei_x, fei_y, fei_z = struct.unpack_from("<3i", ram, fei + ACTOR_DATA_POSITION_OFFSET)
    cross_x, _cross_y, cross_z = struct.unpack_from("<3i", ram, cross + ACTOR_DATA_POSITION_OFFSET)
    cross_bounds = struct.unpack_from("<4H", ram, cross + ACTOR_DATA_BOUNDS_OFFSET)
    if (
        (fei_x, fei_y, fei_z) != EXPECTED_FEI_POSITION
        or struct.unpack_from("<4H", ram, fei + ACTOR_DATA_SURFACES_OFFSET) != EXPECTED_FEI_TRIANGLES
        or (struct.unpack_from("<H", ram, fei + ACTOR_FACING_OFFSET)[0] & 0xFFF) != EXPECTED_FEI_FACING
        or ram[fei + ACTOR_CURRENT_PC_OFFSET : fei + ACTOR_CURRENT_PC_OFFSET + 4] != EXPECTED_FEI_CURRENT
        or ram[controller + ACTOR_SCRIPT_SLOT_OFFSET : controller + ACTOR_SCRIPT_SLOT_OFFSET + 8]
        != EXPECTED_CONTROLLER_SLOT0
        or ram[controller + ACTOR_CURRENT_PC_OFFSET : controller + ACTOR_CURRENT_PC_OFFSET + 4]
        != EXPECTED_CONTROLLER_CURRENT
    ):
        raise SurfaceSlotMigrationError("Fei/controller saved stance drifted")
    # The native ghost Cross carrier is already selectable at Fei's exact
    # stance: raw X/Z half-extents 48/32 plus Fei's radius 16.
    if (
        (cross_x, cross_z) != (0, 250 << 16)
        or cross_bounds != (48, 60, 32, 16)
        or not (struct.unpack_from("<I", ram, cross + ACTOR_DATA_FLAGS_OFFSET)[0] & 0x80)
        or not (-64 <= fei_x // 65536 <= 64 and 202 <= fei_z // 65536 <= 298)
    ):
        raise SurfaceSlotMigrationError("Native e17 Cross carrier reachability drifted")
    leaf_record = actor_base + DOOR_LEAF_ENTITY * FIELD_ACTOR_STRIDE
    if (
        ram[leaf + ACTOR_SCRIPT_SLOT_OFFSET + 4 * 8 : leaf + ACTOR_SCRIPT_SLOT_OFFSET + 5 * 8]
        != EXPECTED_LEAF_SLOT4
        or ram[leaf + ACTOR_CURRENT_PC_OFFSET : leaf + ACTOR_CURRENT_PC_OFFSET + 4] != EXPECTED_LEAF_CURRENT
        or struct.unpack_from("<H", ram, FIELD_SCRIPT_MEMORY + CLOSED_LEAF_HELPER_OPERAND)[0]
        != EXPECTED_CLOSED_LEAF_HELPER
        or ram[leaf_record + 0x0C : leaf_record + 0x1E] != CLOSED_LEAF_MATRIX
        or ram[leaf_record + 0x2C : leaf_record + 0x3E] != CLOSED_LEAF_MATRIX
        or ram[leaf_record + 0x20 : leaf_record + 0x2C] != b"\0" * 12
        or ram[leaf_record + 0x40 : leaf_record + 0x4C] != b"\0" * 12
    ):
        raise SurfaceSlotMigrationError("Native e18 door leaf is not in its closed state")
    seal_record = actor_base + SEAL_ENTITY * FIELD_ACTOR_STRIDE
    if (
        seal_record != E20_RECORD_RAM_OFFSET
        or seal != E20_ACTOR_DATA_RAM_OFFSET
        or ram[seal_record + 0x28 : seal_record + 0x2C] != OLD_E20_RECORD_Z
        or ram[seal_record + 0x48 : seal_record + 0x4C] != OLD_E20_RECORD_Z
        or ram[seal : seal + 4] != OLD_E20_FLAGS
        or ram[seal + ACTOR_DATA_SURFACES_OFFSET : seal + ACTOR_DATA_SURFACES_OFFSET + 8]
        != bytes.fromhex("22 00 00 00 00 00 00 00")
        or ram[seal + ACTOR_DATA_BOUNDS_OFFSET : seal + ACTOR_DATA_BOUNDS_OFFSET + 8] != OLD_E20_BOUNDS
        or ram[seal + ACTOR_DATA_POSITION_OFFSET : seal + ACTOR_DATA_POSITION_OFFSET + 12]
        != OLD_E20_CURRENT_POSITION
        or ram[seal + ACTOR_DATA_OLD_POSITION_OFFSET : seal + ACTOR_DATA_OLD_POSITION_OFFSET + 8]
        != OLD_E20_OLD_POSITION
        or ram[seal + ACTOR_SCRIPT_SLOT_OFFSET : seal + ACTOR_SCRIPT_SLOT_OFFSET + 8] != EXPECTED_SEAL_SLOT0
        or ram[seal + ACTOR_CURRENT_PC_OFFSET : seal + ACTOR_CURRENT_PC_OFFSET + 4] != EXPECTED_SEAL_CURRENT
        or struct.unpack_from("<I", ram, seal)[0] & 0x2000
    ):
        raise SurfaceSlotMigrationError("Active e20 circular-seal runtime drifted")

    gamestate = ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE]
    field_bank = ram[FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE]
    backup_bank = ram[
        GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET : GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET + FIELD_VARIABLE_BANK_SIZE
    ]
    windows = ram[DIALOG_WINDOWS : DIALOG_WINDOWS + DIALOG_WINDOWS_SIZE]
    loaded_header = ram[LOADED_HEADER_RAM_OFFSET : LOADED_HEADER_RAM_OFFSET + LOADED_HEADER_SIZE]
    if (
        _sha256(gamestate) != EXPECTED_GAMESTATE_SHA256
        or field_bank != backup_bank
        or _sha256(field_bank) != EXPECTED_FIELD_VARIABLE_BANK_SHA256
        or struct.unpack_from("<H", field_bank, QUARANTINE_CARD_OPERAND)[0] != EXPECTED_QUARANTINE_WORD
        or not (struct.unpack_from("<H", field_bank, QUARANTINE_CARD_OPERAND)[0] & (1 << QUARANTINE_CARD_BIT))
        or _sha256(_camera_snapshot(ram)) != EXPECTED_CAMERA_SHA256
        or _sha256(windows) != EXPECTED_DIALOG_WINDOWS_SHA256
        or any(
            struct.unpack_from("<h", ram, DIALOG_WINDOWS + i * DIALOG_WINDOW_STRIDE + DIALOG_WINDOW_STATUS_OFFSET)[0]
            != -1
            for i in range(4)
        )
        or struct.unpack_from("<I", ram, WINDOW0_START_POINTER_OFFSET)[0] != EXPECTED_WINDOW0_START_POINTER
        or struct.unpack_from("<I", ram, WINDOW0_CURRENT_POINTER_OFFSET)[0] != EXPECTED_WINDOW0_CURRENT_POINTER
        or _sha256(loaded_header) != EXPECTED_LOADED_HEADER_SHA256
        or loaded_header[HEADER_ACTOR_TABLE_OFFSET:] != old_header[HEADER_ACTOR_TABLE_OFFSET:]
    ):
        raise SurfaceSlotMigrationError("GameState/card/camera/window/header identity drifted")
    return {
        "ram_offset": ram_offset,
        "ram": ram,
        "script": script,
        "dialogue": dialogue,
        "walkmesh": walkmesh,
        "gamestate": gamestate,
        "field_bank": field_bank,
        "camera": _camera_snapshot(ram),
        "windows": windows,
        "loaded_header": loaded_header,
        "actor_base": actor_base,
        "actor_records": tuple(actor_records),
        "actor_data": tuple(actor_data),
        "actor_data_offsets": tuple(actor_data_offsets),
    }


def migrate_v216_slot1_to_v217(
    state: bytes,
    *,
    old_disc: Path,
    new_disc: Path,
    old_header: bytes,
    new_header: bytes,
    old_script: bytes,
    new_script: bytes,
    old_dialogue: bytes,
    new_dialogue: bytes,
    zstd: _ZstdLike,
) -> tuple[bytes, dict[str, object]]:
    source_sha = _sha256(state)
    if (len(state), source_sha) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise SurfaceSlotMigrationError(
            f"Source Slot 1 identity is {len(state)} / {source_sha}, expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    old_name, new_name = OLD_CUE_NAME.encode(), NEW_CUE_NAME.encode()
    if len(old_name) != len(new_name) or state.count(old_name) != 1 or state.count(new_name):
        raise SurfaceSlotMigrationError("Source CUE identity drifted")
    old_table, new_table = _validate_resources(
        old_disc,
        new_disc,
        old_header,
        new_header,
        old_script,
        new_script,
        old_dialogue,
        new_dialogue,
    )
    source_payload, frame_start, source_prefix = _unpack_state(state, zstd)
    if (
        frame_start != EXPECTED_FRAME_START
        or len(state) - frame_start != SOURCE_COMPRESSED_SIZE
        or _sha256(source_prefix) != EXPECTED_SOURCE_PREFIX_SHA256
    ):
        raise SurfaceSlotMigrationError("Source frame/prefix identity drifted")
    snapshots = _validate_source(source_payload, old_table, old_header)
    resident_script = _build_resident_script(snapshots["script"], old_script, new_script)

    final = bytearray(source_payload)
    for relative, old, new in ARCHIVE_TABLE_DIFFS:
        absolute = EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + relative
        if final[absolute] != old:
            raise SurfaceSlotMigrationError("Resident archive-table source drifted")
        final[absolute] = new
    final[EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE] = resident_script
    ram_offset = int(snapshots["ram_offset"])
    for relative, old, new, label in RUNTIME_PATCHES:
        absolute = ram_offset + relative
        if final[absolute : absolute + len(old)] != old:
            raise SurfaceSlotMigrationError(f"Runtime patch source drifted: {label}")
        final[absolute : absolute + len(new)] = new
    final_payload = bytes(final)

    script_diffs = _diff_offsets(snapshots["script"], resident_script)
    expected_offsets = {
        *(EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + relative for relative, _old, _new in ARCHIVE_TABLE_DIFFS),
        *(EXPECTED_SCRIPT_PAYLOAD_OFFSET + relative for relative in script_diffs),
    }
    runtime_changed = 0
    for relative, old, new, _label in RUNTIME_PATCHES:
        runtime_changed += sum(before != after for before, after in zip(old, new, strict=True))
        expected_offsets.update(
            ram_offset + relative + index
            for index, (before, after) in enumerate(zip(old, new, strict=True))
            if before != after
        )
    actual = _diff_offsets(source_payload, final_payload)
    if (
        len(ARCHIVE_TABLE_DIFFS) != EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED
        or len(script_diffs) != EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED
        or runtime_changed != EXPECTED_RUNTIME_BYTES_CHANGED
        or actual != tuple(sorted(expected_offsets))
        or len(actual) != EXPECTED_PAYLOAD_BYTES_CHANGED
    ):
        raise SurfaceSlotMigrationError("Migration changed bytes outside the exact 60-byte whitelist")
    if _sha256(final_payload) != EXPECTED_OUTPUT_PAYLOAD_SHA256:
        raise SurfaceSlotMigrationError("Final payload identity drifted")
    expected_table = new_table[:-1] + bytes((EXPECTED_VOLATILE_TABLE_VALUE,))
    final_table = final_payload[
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET : EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
    ]
    if final_table != expected_table or _sha256(final_table) != OUTPUT_RESIDENT_TABLE_SHA256:
        raise SurfaceSlotMigrationError("Volatile V217 archive-table tail was not preserved")

    result = _pack_state(source_prefix.replace(old_name, new_name), final_payload, zstd)
    verified_payload, verified_frame, verified_prefix = _unpack_state(result, zstd)
    if (
        verified_payload != final_payload
        or verified_frame != frame_start
        or len(result) - frame_start != EXPECTED_OUTPUT_COMPRESSED_SIZE
        or verified_prefix != _expected_prefix(source_prefix, compressed_size=len(result) - frame_start)
        or _sha256(verified_prefix) != EXPECTED_OUTPUT_PREFIX_SHA256
        or result.count(old_name) != 0
        or result.count(new_name) != 1
    ):
        raise SurfaceSlotMigrationError("Final V217 state failed exact round trip")
    _result_ram_offset, result_ram = _ram_from_payload(verified_payload)
    source_ram = snapshots["ram"]
    if _sha256(result_ram) != OUTPUT_RAM_SHA256:
        raise SurfaceSlotMigrationError("Final V217 serialized RAM identity drifted")

    actor_base = int(snapshots["actor_base"])
    actor_data_offsets = tuple(snapshots["actor_data_offsets"])
    source_records = tuple(snapshots["actor_records"])
    source_actor_data = tuple(snapshots["actor_data"])
    for entity in range(SCRIPT_ENTITY_COUNT):
        record_offset = actor_base + entity * FIELD_ACTOR_STRIDE
        data_offset = actor_data_offsets[entity]
        result_record = result_ram[record_offset : record_offset + ACTOR_RECORD_SIZE]
        result_data = result_ram[data_offset : data_offset + ACTOR_DATA_SIZE]
        if entity == SEAL_ENTITY:
            expected_record = bytearray(source_records[entity])
            expected_record[0x28:0x2C] = NEW_E20_RECORD_Z
            expected_record[0x48:0x4C] = NEW_E20_RECORD_Z
            expected_data = bytearray(source_actor_data[entity])
            expected_data[:4] = NEW_E20_FLAGS
            expected_data[ACTOR_DATA_BOUNDS_OFFSET : ACTOR_DATA_BOUNDS_OFFSET + 8] = NEW_E20_BOUNDS
            expected_data[ACTOR_DATA_POSITION_OFFSET : ACTOR_DATA_POSITION_OFFSET + 12] = NEW_E20_CURRENT_POSITION
            expected_data[ACTOR_DATA_OLD_POSITION_OFFSET : ACTOR_DATA_OLD_POSITION_OFFSET + 8] = NEW_E20_OLD_POSITION
            if (
                result_record != bytes(expected_record)
                or result_data != bytes(expected_data)
                or _sha256(result_record) != OUTPUT_E20_RECORD_SHA256
                or _sha256(result_data) != OUTPUT_E20_ACTOR_DATA_SHA256
                or not (struct.unpack_from("<I", result_data, 0)[0] & 0x2000)
            ):
                raise SurfaceSlotMigrationError("V217 e20 rectangle runtime construction drifted")
        elif result_record != source_records[entity] or result_data != source_actor_data[entity]:
            raise SurfaceSlotMigrationError(f"Unrelated field runtime e{entity} changed")

    preserved_spans = (
        (GAME_STATE, GAMESTATE_SIZE, "GameState"),
        (FIELD_SCRIPT_MEMORY, FIELD_VARIABLE_BANK_SIZE, "active field variables"),
        (DIALOG_WINDOWS, DIALOG_WINDOWS_SIZE, "dialogue windows"),
        (LOADED_HEADER_RAM_OFFSET, LOADED_HEADER_SIZE, "loaded field header"),
    )
    for start, size, label in preserved_spans:
        if result_ram[start : start + size] != source_ram[start : start + size]:
            raise SurfaceSlotMigrationError(f"{label} was not preserved")
    if _camera_snapshot(result_ram) != snapshots["camera"]:
        raise SurfaceSlotMigrationError("Camera was not preserved")
    controller = actor_data_offsets[CONTROLLER_ENTITY]
    if (
        result_ram[controller : controller + ACTOR_DATA_SIZE]
        != source_ram[controller : controller + ACTOR_DATA_SIZE]
        or result_ram[controller + ACTOR_SCRIPT_SLOT_OFFSET : controller + ACTOR_SCRIPT_SLOT_OFFSET + 8]
        != EXPECTED_CONTROLLER_SLOT0
        or result_ram[controller + ACTOR_CURRENT_PC_OFFSET : controller + ACTOR_CURRENT_PC_OFFSET + 4]
        != EXPECTED_CONTROLLER_CURRENT
    ):
        raise SurfaceSlotMigrationError("e0 scheduler runtime was changed instead of its entry point")
    if (
        final_payload[EXPECTED_DIALOGUE_PAYLOAD_OFFSET : EXPECTED_DIALOGUE_PAYLOAD_OFFSET + OUTPUT_RESIDENT_DIALOGUE_SIZE]
        != snapshots["dialogue"]
        or final_payload[EXPECTED_WALKMESH_PAYLOAD_OFFSET : EXPECTED_WALKMESH_PAYLOAD_OFFSET + WALKMESH_SIZE]
        != snapshots["walkmesh"]
        or final_payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET]
        != source_payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET]
        or final_payload[
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET + OUTPUT_RESIDENT_DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET
        ]
        != source_payload[
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET + SOURCE_RESIDENT_DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET
        ]
    ):
        raise SurfaceSlotMigrationError("Allocator/component neighbors changed")

    output_sha = _sha256(result)
    if (len(result), output_sha) != (EXPECTED_OUTPUT_SIZE, EXPECTED_OUTPUT_SHA256):
        raise SurfaceSlotMigrationError("V217 candidate identity drifted")
    return result, {
        "source_sha256": source_sha,
        "output_sha256": output_sha,
        "source_size": len(state),
        "output_size": len(result),
        "field": EXPECTED_FIELD,
        "payload_bytes_changed": len(actual),
        "archive_table_bytes_changed": len(ARCHIVE_TABLE_DIFFS),
        "resident_script_bytes_changed": len(script_diffs),
        "runtime_bytes_changed": runtime_changed,
        "resident_script_size": len(resident_script),
        "resident_script_capacity": SCRIPT_ALLOCATED_CAPACITY,
        "forward_poll_pc": f"0x{FORWARD_POLL_PC:04X}",
        "native_cross_action_pc": f"0x{COMPACT_NATIVE_ACTION_PC:04X}",
        "e20_seal": "rectangle x=0 z=266 OP18=24/8 physical_half_spans=48/16",
        "walkmesh_preserved": True,
        "native_cross_action_preserved": True,
        "closed_leaf_preserved": True,
        "controller_runtime_preserved": True,
        "gamestate_party_camera_preserved": True,
        "volatile_table_tail_preserved": True,
        "allocator_safe": True,
        "round_trip_verified": True,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--old-disc", type=Path, required=True)
    parser.add_argument("--new-disc", type=Path, required=True)
    parser.add_argument("--old-header", type=Path, required=True)
    parser.add_argument("--new-header", type=Path, required=True)
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
            for name in (
                "old_disc",
                "new_disc",
                "old_header",
                "new_header",
                "old_script",
                "new_script",
                "old_dialogue",
                "new_dialogue",
                "zstd",
            )
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
        result, report = migrate_v216_slot1_to_v217(
            source.read_bytes(),
            old_disc=paths["old_disc"],
            new_disc=paths["new_disc"],
            old_header=paths["old_header"].read_bytes(),
            new_header=paths["new_header"].read_bytes(),
            old_script=paths["old_script"].read_bytes(),
            new_script=paths["new_script"].read_bytes(),
            old_dialogue=paths["old_dialogue"].read_bytes(),
            new_dialogue=paths["new_dialogue"].read_bytes(),
            zstd=media_migration._Zstd(paths["zstd"]),
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        if output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Written V217 candidate changed on disk")
        print(f"Wrote validated V217 candidate: {output}")
        print(json.dumps(report, indent=2, sort_keys=True))
        print("The live Slot 1 was not modified. Install only after DuckStation is fully closed.")
        return 0
    except (OSError, ValueError, media_migration.StateMigrationError, SurfaceSlotMigrationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
