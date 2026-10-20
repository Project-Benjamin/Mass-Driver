#!/usr/bin/env python3
"""Migrate the exact V231 field-593 terminal-proximity state to V232.

The source was saved beside field 593's old aisle-wide interaction carrier.
V232 moves that carrier onto the real Solaris side bank, makes it narrow and
facing-gated, and reuses retired entities 4 and 5 for the rest of the bank.

This migration replaces the equal-length resident ATEL and cached header,
patches entity 19 directly, and queues the entity-4/entity-5 initializers for
the normal field scheduler.  The archive table is rebuilt for V232 while its
known volatile final byte is retained.  A cold reload therefore uses ordinary
V232 media, while the already-loaded field has a scheduler-safe compatibility
layout.  The helper is fail-closed, writes only a separate candidate/report,
and never writes DuckStation's live Slot 1.
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
import tools.migrate_surface_soylent_v230_slot1_to_v231 as previous  # noqa: E402
from tools.xgdeathblows import GAMESTATE_SIZE  # noqa: E402
from tools.xgdisc import DiscFormatError, Mode2Image  # noqa: E402
from tools.xgfield import FieldFormatError, ParsedField, parse_field  # noqa: E402
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
SOURCE_FIXTURE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v231_field593_terminal_proximity_6adde32f.sav"
).resolve()

SOURCE_STATE_SIZE = 1_839_559
SOURCE_STATE_SHA256 = "6adde32f8351a7e6201bb6d40dafc7b11d00910bf13f33066a905549047fbe48"
SOURCE_PREFIX_SIZE = 41_689
SOURCE_PREFIX_SHA256 = "95df2d48cf7ad7faf64514185c24d2a46711dc78e1d8cb8709917836d531ba9b"
SOURCE_COMPRESSED_SIZE = 1_797_870
SOURCE_COMPRESSED_SHA256 = "671119aa4ed30cc20b451c559b5eddd157afe678d068b2e70e739e25c8e106f7"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "ca5c4a03f7f43053c66fe1ba0a7411ede3e792b028d871df9e096e77c894ca8f"
SOURCE_RAM_SHA256 = "3a090b73547d66c2d53676bcf32a64e480b03e52ca84b8c9812689fb1f1c4eb3"

# Filled with the deterministic zstd result after the whitelist is complete.
# These values are deliberately checked by both the migration and its tests.
OUTPUT_STATE_SIZE = 1_661_998
OUTPUT_STATE_SHA256 = "eae5680680e2a197d2333524ce254483cd921b8f12bfab4b325ac2b9269be45f"
OUTPUT_PREFIX_SHA256 = "e301decbfd5004b6fc01de5ad8cacb3fed77faf84abacb41448b8f3577364119"
OUTPUT_COMPRESSED_SIZE = 1_620_309
OUTPUT_COMPRESSED_SHA256 = "7632b5c01a7165092b70195573938288448ab441939b98270aff4eb9c6adc701"
OUTPUT_PAYLOAD_SHA256 = "87e80394311c328302d8ec21f6526129f3c42cb5f1a3902d1b7a0be2aa7d17b1"
OUTPUT_RAM_SHA256 = "a11ad580783f9940f467d7992eeed01bc34c309277d970cbcbf0f8b58ddea00c"
OUTPUT_REPORT_SIZE = 3_913
OUTPUT_REPORT_SHA256 = "bdaa558f721cbd720ee5682f37adc8db28a2bd0d8493179092e25af62a178858"

OLD_DISC_SIZE = NEW_DISC_SIZE = 698_816_832
OLD_DISC_SHA256 = "1f01094862fdb859787295f8babec12ad8d8a3122649b30a8ac01d84f84be3d2"
NEW_DISC_SHA256 = "8e9020e85760e64555040ea26b73876f0add72a788a3221070e4d57823520394"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v231.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v232.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = "3f7037d31b91d0e05360ed94d48d5a93c93839c9ac8ffa4bd0516533871e4f9b"
NEW_CUE_SHA256 = "dacbd8033a8ae9ac9c98c9e3918d3de7deb59a5ddb320dcd7264438ad59d7647"

OLD_MANIFEST_SIZE = 131_663
OLD_MANIFEST_SHA256 = "3158359afe3ff059e3882de85a8e4aa3ebbc057bfc788affe120693934b17717"
NEW_MANIFEST_SIZE = 135_113
NEW_MANIFEST_SHA256 = "007ef9b6e1863d6ec01b4512303e8b52129da5cf8c454d53704fc48a0f6786ea"
CHANGED_RESOURCE_IDS = (1788, 1790, 1792, 1794)
CHANGED_RESOURCE_IDENTITIES = {
    1788: (
        (63_680, "52ca81a59f421127a1352cace807aecc40177b1d36f7bbf367fb434e36b33b58"),
        (63_640, "bb852caeac217e5ab0d5c26fbd9ebbfb6caf21f6c21a64798022a6cee5e89297"),
    ),
    1790: (
        (64_224, "e0c6785f2c1a3799ac96e66b4b8a713d3fe4ae1165506ed3adff15e89a609a5d"),
        (64_184, "9398ec12f0164f543321c14e40dbcd9c156403b33c245bd707b1d22442ff65df"),
    ),
    1792: (
        (69_716, "abbc49722ab4817f49012c37136b2ea3cafc52f98b1c33ccac09804202bf65ca"),
        (69_676, "e60e85c8f0bc6225adb78b4c25fabf9411520f32610bf6fe926e85f7253e50e1"),
    ),
    1794: (
        (72_156, "e6deba398bb2394a695af0f04dcc7401eb4f70b3aa7d4427165dfd419122ea31"),
        (72_116, "194613b51b0e7b30140f7181d8a3779f612c6cfb4c7a8b4bd38699ea5226669b"),
    ),
}

FIELD593_CANONICAL_ID = 1792
OLD_FIELD_BUNDLE_SIZE, OLD_FIELD_BUNDLE_SHA256 = CHANGED_RESOURCE_IDENTITIES[
    FIELD593_CANONICAL_ID
][0]
NEW_FIELD_BUNDLE_SIZE, NEW_FIELD_BUNDLE_SHA256 = CHANGED_RESOURCE_IDENTITIES[
    FIELD593_CANONICAL_ID
][1]

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = "4238e60078de7c6442228ccfdc35b5d410d4eff6f496ddfba71a316c6d2ea1bf"
NEW_ARCHIVE_TABLE_SHA256 = "bb4741fed2677df0519c00bb7d105ec7aec027061269e6657bdec60c10717a51"
ARCHIVE_TABLE_DIFFS = (
    (0x30C4, 0xC0, 0x98),
    (0x30D2, 0xE0, 0xB8),
    (0x30E0, 0x54, 0x2C),
    (0x30EE, 0xDC, 0xB4),
)
ARCHIVE_TABLE_DIFF_SHA256 = "16350e42bd680cceebac7339b53c9d8c5f4f1e31aac95f6d19992c95b0312784"
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
EXPECTED_VOLATILE_TABLE_PAYLOAD_OFFSET = 0x19A65
EXPECTED_VOLATILE_TABLE_VALUE = 0xE0
SOURCE_RESIDENT_TABLE_SHA256 = "bc09aa66f53ab89dab9f747132b324677dab93ff9c6c633a369b51733176f555"
OUTPUT_RESIDENT_TABLE_SHA256 = "194ecb959cc2af747bc3286f28dc1a54b07c33beb714183eea4938764a1ec2c6"

SCRIPT_SIZE = 3_515
OLD_SCRIPT_SHA256 = "1c242fe3321f9d6fefeed96487bf3dbffe446c4f75039a56568b68b6c86e4680"
NEW_SCRIPT_SHA256 = "8669b5754be76c7928026bfc40e8e84e4ae0a1797dfef802f06a2b0756c43785"
SCRIPT_DIFF_COUNT = 84
SCRIPT_DIFF_FIRST = 0x0184
SCRIPT_DIFF_LAST = 0x0C9E
SCRIPT_DIFF_SHA256 = "0ca789cf858c29bbf3e1d541511bce417a8f430fb7c6f0ff0eecc95867578fcf"
SCRIPT_BYTECODE_OFFSET = 0x05C4
SCRIPT_BYTECODE_SIZE = 0x07F7
SCRIPT_ENTITY_COUNT = 21
SHARED_STOP_PC = 0x068C
TERMINAL_ENTITIES = (19, 4, 5)
TERMINAL_INIT_PCS = (0x06C3, 0x044E, 0x046B)
TERMINAL_ACTION_PC = 0x06E0
TERMINAL_ACTION_SIZE = 101
TERMINAL_ACTION_SHA256 = "178e0251af24d952cb69071f49c15842f0f7d0963b0e8558db2c8760f1c944de"
TERMINAL_POSITIONS = ((80, -167), (116, -167), (152, -167))
TERMINAL_TRIANGLES = (31, 6, 6)
TERMINAL_INIT_BODIES = (
    bytes.fromhex(
        "0B 00 80 19 50 00 59 FF C0 1A 00 F8 00 00 20 "
        "F8 03 04 00 18 01 0F 64 01 20 01 80 23 00"
    ),
    bytes.fromhex(
        "0B 00 80 19 74 00 59 FF C0 1A 00 F8 00 00 20 "
        "F8 03 04 00 18 01 0F 64 01 20 01 80 23 00"
    ),
    bytes.fromhex(
        "0B 00 80 19 98 00 59 FF C0 1A 00 F8 00 00 20 "
        "F8 03 04 00 18 01 0F 64 01 20 01 80 23 00"
    ),
)

HEADER_SIZE = 960
OLD_HEADER_SHA256 = "4d9e0d7d181a156cd0c2289ee460c6b32de91e1b082e3634d3cc019dbaa0d3a6"
NEW_HEADER_SHA256 = "eb74bc65af5847bca1b039064a61c7398e2b1013c5c739d913d7edb024308108"
HEADER_DIFFS = (
    (0x0148, 0x54, 0x2C),
    (0x014C, 0xF0, 0xC8),
    (0x0150, 0x50, 0x28),
    (0x02CC, 0xB0, 0x59),
)
HEADER_DIFF_SHA256 = "972bf13154ccf472c152cf6a769837b987c9b58e9cecba1f7373bb3927eb8ffc"
RESIDENT_HEADER_DIFFS = ((0x02CC, 0xB0, 0x59),)
RESIDENT_HEADER_SHA256 = "fda02b034ab1c11419710906c4ee3e114c95c62a0ee84582be135848e51feba6"

DIALOGUE_SIZE = 5_766
DIALOGUE_SHA256 = "92d7f6d9ab86a53e8cabd300bc7bb84d8bbb04142f9aa9c4f91a9bd5578b828e"
WALKMESH_SIZE = 1_948
WALKMESH_SHA256 = "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d8cca4238393571df"

EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
EXPECTED_SCRIPT_PAYLOAD_OFFSET = 0x10CD56
EXPECTED_DIALOGUE_PAYLOAD_OFFSET = 0x10DB42
EXPECTED_WALKMESH_PAYLOAD_OFFSET = 0x10F1E2
EXPECTED_HEADER_PAYLOAD_OFFSET = 0x1DBEAA
EXPECTED_SCRIPT_GUEST_POINTER = 0x8010B2F4
EXPECTED_VM_SCRIPT_GUEST_POINTER = 0x8010B8B8
EXPECTED_VM_ACTOR_GUEST_POINTER = 0x80113CD0

GAME_SCENE_MAP = 0x04F34C
EXPECTED_GAME_SCENE_MAP = 0x0251
EXPECTED_FIELD = 593
EXPECTED_ACTOR_COUNT = 35
EXPECTED_ACTOR_ARRAY_GUEST_POINTER = 0x80110D50
EXPECTED_ACTOR_ARRAY_SHA256 = "777a0a9c1e620b50da103a888cf9d0d62b9197331136f7c96da6a03781b7f69c"
EXPECTED_ACTOR_DATA_POINTERS = {
    4: 0x001120CC,
    5: 0x00112284,
    13: 0x00113044,
    16: 0x0011356C,
    19: 0x00113B18,
    20: 0x00113CD0,
}

ACTOR_DATA_SIZE = 0x138
ACTOR_RECORD_STATUS_OFFSET = 0x58
ACTOR_DATA_FLAGS_OFFSET = 0x04
ACTOR_DATA_SURFACES_OFFSET = 0x08
ACTOR_DATA_BOUNDS_OFFSET = 0x18
ACTOR_DATA_POSITION_OFFSET = 0x20
ACTOR_DATA_OLD_POSITION_OFFSET = 0x68
ACTOR_SCRIPT_SLOT_OFFSET = 0x8C
ACTOR_CURRENT_PC_OFFSET = 0xCC

FIELD_VARIABLE_BANK_SIZE = 0x400
FIELD_VARIABLE_BACKUP_OFFSET = 0x1930
EXPECTED_GAMESTATE_SHA256 = "406eb1000c641615df4d549a45ef5c5eedfb91c03a50cf3064183c265378e3d8"
EXPECTED_FIELD_VARIABLE_BANK_SHA256 = "4c0ce1b23c332475c645fc5548f999db67cc021f9bd3df5fd76769cc654cfb4f"
EXPECTED_CAMERA_SHA256 = "f926db5daae3e11d1b68acc825e06d2f57f1be9dc1742dd94384b56a0edb6099"
EXPECTED_PARTY_RECORDS_SHA256 = "6e7bdfd5aa14858e31fc8cf04e9afb775a8428b374bcbc7a7f302f74c0a177c5"
EXPECTED_PARTY_ACTOR_DATA_SHA256 = "e4637f99b47811e213107cde5fdfc23bd206a707826bfa10c0f8d30bd4a37b86"
EXPECTED_PATIENT_DOCTOR_RECORDS_SHA256 = "b6aca00bae44d579e58e338dd98e66fe6cf63720ed0ca5d8f9c84cec1ce06a57"
EXPECTED_PATIENT_DOCTOR_ACTOR_DATA_SHA256 = "53d3e6d75171d76be8f182359582d96912b68ec1554c7b042fb312b5b718bdad"
QUARANTINE_KEYCARD_OPERAND = 0x021A
EXPECTED_KEYCARD_WORD = 0x01FD
DIALOG_WINDOWS = 0x0C2698
DIALOG_WINDOW_STRIDE = 0x498
DIALOG_WINDOWS_SIZE = 4 * DIALOG_WINDOW_STRIDE
DIALOG_WINDOW_STATUS_OFFSET = 0x40E
EXPECTED_DIALOG_WINDOWS_SHA256 = "24fa071f273d6e43baadf49775cbb87fc5c86384fefb7be614c9096713250290"
EXPECTED_UNRELATED_RUNTIME_SHA256 = "d51587844f2630f0ab12df816db1452b3d26afa842efad5edb57860df26a4654"

OUTPUT_ACTOR_ARRAY_SHA256 = "667705621b089755ef9ca539133ee86a8f4f7f509f88b745a41ead4fa5091af2"
OUTPUT_ALL_SCRIPT_ACTOR_DATA_SHA256 = "f15051fdc2c32d24769ab662ce8ee54fbd896d2c2b439d1a46c97176cfce2f3f"
OUTPUT_TERMINAL_RUNTIME_SHA256 = {
    4: (
        "52d21dfea8fddd182a3f27d082de5ec28d4c3ad762649c23c41a6ce2ccac0d7c",
        "a2c30ceba3da55ff894a2fe7cb7a7c164df340cd4f16e5f69d1639231fcd53d6",
    ),
    5: (
        "3b95d53fa5646e1aa81cc258580f2619eaa6cb87a712b15dfaefafc4633cd58d",
        "e56ee55b9fc260e6fabf3a767f13d6c22d88f073607a5c999dc28585a5186c53",
    ),
    19: (
        "3c8e2cf096028e3ee28dcc8d022c60fc6dedc3afdf1a3caa42bc9d02a0b9261e",
        "8a381f6e39814334cf1a2b4b6474c6c86ef4ce05e570735a36e0398b4cf0a007",
    ),
}

SAVED_FEI_XZ = (75.00785827636719, -77.75068664550781)
SAVED_FEI_YAW = 0x0400
TERMINAL_EFFECTIVE_HALF_REACH = (18, 46)

OLD_AUX_RECORD_STATUS = bytes.fromhex("E0 01")
NEW_AUX_RECORD_STATUS = bytes.fromhex("60 02")
OLD_AUX_FLAGS = bytes.fromhex("00 08 00 04")
NEW_AUX_FLAGS = bytes.fromhex("00 08 00 00")
OLD_AUX_SLOT0 = bytes.fromhex("8C 06 00 FF FF FF 3C 00")
NEW_AUX_SLOT0 = (
    bytes.fromhex("4E 04 00 00 FF FF 1C 00"),
    bytes.fromhex("6B 04 00 00 FF FF 1C 00"),
)

# RAM-relative patches.  The source and replacement are multi-byte units so
# their meaning stays auditable even when only one byte differs.
RUNTIME_PATCHES = (
    (0x11144C, bytes.fromhex("B0 FF FF FF"), bytes.fromhex("59 FF FF FF"), "e19 current record Z"),
    (0x11146C, bytes.fromhex("B0 FF FF FF"), bytes.fromhex("59 FF FF FF"), "e19 previous record Z"),
    (0x113B1C, bytes.fromhex("00 00 00 00"), bytes.fromhex("00 00 04 00"), "e19 facing flag"),
    (0x113B20, bytes.fromhex("08 00 00 00 00 00 00 00"), bytes.fromhex("1F 00 00 00 00 00 00 00"), "e19 side-bank surface"),
    (0x113B30, bytes.fromhex("30 00 C8 00 30 00 30 00"), bytes.fromhex("02 00 C8 00 1E 00 02 00"), "e19 narrow bounds"),
    (0x113B38, bytes.fromhex("00 00 50 00 00 00 00 00 00 00 B0 FF"), bytes.fromhex("00 00 50 00 00 00 00 00 00 00 59 FF"), "e19 current position"),
    (0x113B80, bytes.fromhex("50 00 00 00 B0 FF 00 00"), bytes.fromhex("50 00 00 00 59 FF 00 00"), "e19 previous position"),
    (0x110F18, OLD_AUX_RECORD_STATUS, NEW_AUX_RECORD_STATUS, "e4 record status"),
    (0x1120D0, OLD_AUX_FLAGS, NEW_AUX_FLAGS, "e4 ActorData flags"),
    (0x112158, OLD_AUX_SLOT0, NEW_AUX_SLOT0[0], "e4 queued initializer"),
    (0x110F74, OLD_AUX_RECORD_STATUS, NEW_AUX_RECORD_STATUS, "e5 record status"),
    (0x112288, OLD_AUX_FLAGS, NEW_AUX_FLAGS, "e5 ActorData flags"),
    (0x112310, OLD_AUX_SLOT0, NEW_AUX_SLOT0[1], "e5 queued initializer"),
)
EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED = 4
EXPECTED_SCRIPT_BYTES_CHANGED = 84
EXPECTED_HEADER_BYTES_CHANGED = 1
EXPECTED_PRIMARY_RUNTIME_BYTES_CHANGED = 9
EXPECTED_AUX_RUNTIME_BYTES_CHANGED = 14
EXPECTED_RUNTIME_BYTES_CHANGED = 23
EXPECTED_PAYLOAD_BYTES_CHANGED = 112
RUNTIME_DIFF_SHA256 = "9de1c19a66d26bc6bf25e8f332f9a9c6b4ba43383d16150762924020e2eb1ed4"
PAYLOAD_DIFF_SHA256 = "7abe4ec67aa7cb8a61365df698ab1c35c4d8282f952668a6f407793c3fce47d1"
EXPECTED_PREFIX_BYTES_CHANGED = 4

ZSTD_SIZE = 657_408
ZSTD_SHA256 = "51172dce5d1ffef10d90789d97b94b5ffbcaf1404bcd34c1f80e9c3072361c5e"


class _ZstdLike(Protocol):
    def frame_size(self, frame: bytes) -> int: ...
    def decompress(self, frame: bytes) -> bytes: ...
    def compress(self, payload: bytes) -> bytes: ...


SurfaceSlotMigrationError = previous.SurfaceSlotMigrationError


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _diff_offsets(before: bytes, after: bytes) -> tuple[int, ...]:
    return previous._diff_offsets(before, after)


def _diff_triplets(before: bytes, after: bytes) -> tuple[tuple[int, int, int], ...]:
    return previous._diff_triplets(before, after)


def _triplet_digest(diffs: Sequence[tuple[int, int, int]]) -> str:
    return _sha256(
        b"".join(struct.pack("<IBB", offset, old, new) for offset, old, new in diffs)
    )


def _unpack_state(state: bytes, zstd: _ZstdLike) -> tuple[bytes, int, bytes]:
    return previous._unpack_state(state, zstd)


def _pack_state(prefix: bytes, payload: bytes, zstd: _ZstdLike) -> bytes:
    return previous._pack_state(prefix, payload, zstd)


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


def _camera_snapshot(ram: bytes) -> bytes:
    return b"".join(ram[address : address + 16] for address in CAMERA_VECTORS.values())


def _validate_file(path: Path, size: int, sha256: str, label: str) -> None:
    if not path.is_file() or path.stat().st_size != size or _file_sha256(path) != sha256:
        raise SurfaceSlotMigrationError(f"{label} identity drifted")


def _manifest_inventory(
    blob: bytes,
    *,
    size: int,
    sha256: str,
    label: str,
) -> dict[int, tuple[int, str]]:
    if (len(blob), _sha256(blob)) != (size, sha256):
        raise SurfaceSlotMigrationError(f"{label} identity drifted")
    try:
        return {
            int(item["canonical_id"]): (int(item["size"]), str(item["sha256"]))
            for item in json.loads(blob)["replacement_inventory"]
        }
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise SurfaceSlotMigrationError(f"{label} structure drifted") from exc


def _disc_resource(
    image: Mode2Image,
    canonical_id: int,
    size: int,
    sha256: str,
    label: str,
) -> bytes:
    entries = image.read_index()
    index = canonical_id - 5
    if index >= len(entries) or entries[index].canonical_disc2_index != canonical_id:
        raise SurfaceSlotMigrationError(f"{label} FAT mapping drifted")
    data = image.extract_entry(entries[index])
    if (len(data), _sha256(data)) != (size, sha256):
        raise SurfaceSlotMigrationError(f"{label} identity drifted")
    return data


def _disc_field593(
    disc: Path,
    *,
    size: int,
    sha256: str,
    label: str,
) -> ParsedField:
    try:
        parsed = parse_field(
            _disc_resource(Mode2Image(disc), FIELD593_CANONICAL_ID, size, sha256, label)
        )
    except (DiscFormatError, FieldFormatError) as exc:
        raise SurfaceSlotMigrationError(f"Cannot decode {label}: {exc}") from exc
    if len(parsed.parts) != 9:
        raise SurfaceSlotMigrationError(f"{label} component layout drifted")
    return parsed


def _validate_atel(old_script: bytes, new_script: bytes) -> None:
    for blob, sha256, label in (
        (old_script, OLD_SCRIPT_SHA256, "V231 field-593 ATEL"),
        (new_script, NEW_SCRIPT_SHA256, "V232 field-593 ATEL"),
    ):
        if (len(blob), _sha256(blob)) != (SCRIPT_SIZE, sha256):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    diffs = _diff_triplets(old_script, new_script)
    if (
        len(diffs) != SCRIPT_DIFF_COUNT
        or diffs[0][0] != SCRIPT_DIFF_FIRST
        or diffs[-1][0] != SCRIPT_DIFF_LAST
        or _triplet_digest(diffs) != SCRIPT_DIFF_SHA256
    ):
        raise SurfaceSlotMigrationError("V231/V232 ATEL delta drifted")

    old = AtelScript(old_script)
    new = AtelScript(new_script)
    if (
        old.entity_count != SCRIPT_ENTITY_COUNT
        or new.entity_count != SCRIPT_ENTITY_COUNT
        or (old.bytecode_offset, old.bytecode_size)
        != (SCRIPT_BYTECODE_OFFSET, SCRIPT_BYTECODE_SIZE)
        or (new.bytecode_offset, new.bytecode_size)
        != (SCRIPT_BYTECODE_OFFSET, SCRIPT_BYTECODE_SIZE)
        or tuple(old.get_script_pointer(entity, 0) for entity in TERMINAL_ENTITIES)
        != (TERMINAL_INIT_PCS[0], SHARED_STOP_PC, SHARED_STOP_PC)
        or tuple(old.get_script_pointer(entity, 2) for entity in TERMINAL_ENTITIES)
        != (TERMINAL_ACTION_PC, SHARED_STOP_PC, SHARED_STOP_PC)
        or tuple(new.get_script_pointer(entity, 0) for entity in TERMINAL_ENTITIES)
        != TERMINAL_INIT_PCS
        or tuple(new.get_script_pointer(entity, 2) for entity in TERMINAL_ENTITIES)
        != (TERMINAL_ACTION_PC,) * 3
        or tuple(
            new.bytecode[pc : pc + len(body)]
            for pc, body in zip(TERMINAL_INIT_PCS, TERMINAL_INIT_BODIES, strict=True)
        )
        != TERMINAL_INIT_BODIES
        or old.bytecode[
            TERMINAL_ACTION_PC : TERMINAL_ACTION_PC + TERMINAL_ACTION_SIZE
        ]
        != new.bytecode[
            TERMINAL_ACTION_PC : TERMINAL_ACTION_PC + TERMINAL_ACTION_SIZE
        ]
        or _sha256(
            new.bytecode[
                TERMINAL_ACTION_PC : TERMINAL_ACTION_PC + TERMINAL_ACTION_SIZE
            ]
        )
        != TERMINAL_ACTION_SHA256
    ):
        raise SurfaceSlotMigrationError("Field-593 three-carrier ATEL topology drifted")


def _validate_media(
    *,
    old_disc: Path,
    new_disc: Path,
    old_manifest: bytes,
    new_manifest: bytes,
    old_script: bytes,
    new_script: bytes,
    old_header: bytes,
    new_header: bytes,
    old_dialogue: bytes,
    new_dialogue: bytes,
) -> tuple[bytes, bytes]:
    for path, size, sha256, label in (
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V231 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V232 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V231 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V232 CUE"),
    ):
        _validate_file(path, size, sha256, label)

    old_inventory = _manifest_inventory(
        old_manifest,
        size=OLD_MANIFEST_SIZE,
        sha256=OLD_MANIFEST_SHA256,
        label="V231 stage manifest",
    )
    new_inventory = _manifest_inventory(
        new_manifest,
        size=NEW_MANIFEST_SIZE,
        sha256=NEW_MANIFEST_SHA256,
        label="V232 stage manifest",
    )
    changed = tuple(
        resource_id
        for resource_id in sorted(set(old_inventory) | set(new_inventory))
        if old_inventory.get(resource_id) != new_inventory.get(resource_id)
    )
    if (
        set(old_inventory) != set(new_inventory)
        or changed != CHANGED_RESOURCE_IDS
        or any(
            (old_inventory[resource_id], new_inventory[resource_id])
            != CHANGED_RESOURCE_IDENTITIES[resource_id]
            for resource_id in CHANGED_RESOURCE_IDS
        )
    ):
        raise SurfaceSlotMigrationError("V231/V232 replacement inventory drifted")

    _validate_atel(old_script, new_script)
    if (
        (len(old_header), _sha256(old_header)) != (HEADER_SIZE, OLD_HEADER_SHA256)
        or (len(new_header), _sha256(new_header)) != (HEADER_SIZE, NEW_HEADER_SHA256)
        or _diff_triplets(old_header, new_header) != HEADER_DIFFS
        or _triplet_digest(HEADER_DIFFS) != HEADER_DIFF_SHA256
        or (len(old_dialogue), _sha256(old_dialogue))
        != (DIALOGUE_SIZE, DIALOGUE_SHA256)
        or new_dialogue != old_dialogue
    ):
        raise SurfaceSlotMigrationError("V231/V232 field-593 component delta drifted")

    old_field = _disc_field593(
        old_disc,
        size=OLD_FIELD_BUNDLE_SIZE,
        sha256=OLD_FIELD_BUNDLE_SHA256,
        label="V231 field-593 bundle",
    )
    new_field = _disc_field593(
        new_disc,
        size=NEW_FIELD_BUNDLE_SIZE,
        sha256=NEW_FIELD_BUNDLE_SHA256,
        label="V232 field-593 bundle",
    )
    if (
        old_field.header != old_header
        or new_field.header != new_header
        or old_field.parts[5].data != old_script
        or new_field.parts[5].data != new_script
        or old_field.parts[7].data != old_dialogue
        or new_field.parts[7].data != new_dialogue
        or any(
            old_field.parts[index].data != new_field.parts[index].data
            for index in range(9)
            if index != 5
        )
        or (len(old_field.parts[1].data), _sha256(old_field.parts[1].data))
        != (WALKMESH_SIZE, WALKMESH_SHA256)
    ):
        raise SurfaceSlotMigrationError("V231/V232 field-593 media contract drifted")

    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    if (
        len(old_table) != ARCHIVE_TABLE_SIZE
        or len(new_table) != ARCHIVE_TABLE_SIZE
        or _sha256(old_table) != OLD_ARCHIVE_TABLE_SHA256
        or _sha256(new_table) != NEW_ARCHIVE_TABLE_SHA256
        or _diff_triplets(old_table, new_table) != ARCHIVE_TABLE_DIFFS
        or _triplet_digest(ARCHIVE_TABLE_DIFFS) != ARCHIVE_TABLE_DIFF_SHA256
    ):
        raise SurfaceSlotMigrationError("V231/V232 archive-table delta drifted")
    return old_table, new_table


def _entity_records(ram: bytes, actor_array: int, entities: Sequence[int]) -> bytes:
    return b"".join(
        ram[
            actor_array + entity * FIELD_ACTOR_STRIDE :
            actor_array + (entity + 1) * FIELD_ACTOR_STRIDE
        ]
        for entity in entities
    )


def _entity_actor_data(ram: bytes, actor_array: int, entities: Sequence[int]) -> bytes:
    result = bytearray()
    for entity in entities:
        record = actor_array + entity * FIELD_ACTOR_STRIDE
        actor_data = _guest_ram_offset(
            struct.unpack_from("<I", ram, record + FIELD_ACTOR_DATA_POINTER)[0],
            f"e{entity} ActorData",
        )
        result.extend(ram[actor_data : actor_data + ACTOR_DATA_SIZE])
    return bytes(result)


def _entity_runtime_interleaved(
    ram: bytes,
    actor_array: int,
    entities: Sequence[int],
) -> bytes:
    result = bytearray()
    for entity in entities:
        record = actor_array + entity * FIELD_ACTOR_STRIDE
        actor_data = _guest_ram_offset(
            struct.unpack_from("<I", ram, record + FIELD_ACTOR_DATA_POINTER)[0],
            f"e{entity} ActorData",
        )
        result.extend(ram[record : record + FIELD_ACTOR_STRIDE])
        result.extend(ram[actor_data : actor_data + ACTOR_DATA_SIZE])
    return bytes(result)


def _validate_source_runtime(
    payload: bytes,
    *,
    old_table: bytes,
    old_script: bytes,
    new_script: bytes,
    old_header: bytes,
    new_header: bytes,
    dialogue: bytes,
) -> dict[str, object]:
    if (
        len(payload) != SOURCE_PAYLOAD_SIZE
        or _sha256(payload) != SOURCE_PAYLOAD_SHA256
    ):
        raise SurfaceSlotMigrationError("V231 decompressed payload identity drifted")
    ram_offset, ram = _ram_from_payload(payload)
    if _sha256(ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("V231 serialized RAM identity drifted")
    component_contracts = (
        (old_script, EXPECTED_SCRIPT_PAYLOAD_OFFSET, "resident V231 ATEL"),
        (old_header, EXPECTED_HEADER_PAYLOAD_OFFSET, "cached V231 header"),
        (dialogue, EXPECTED_DIALOGUE_PAYLOAD_OFFSET, "resident dialogue"),
    )
    for component, expected_offset, label in component_contracts:
        if payload.count(component) != 1 or payload.find(component) != expected_offset:
            raise SurfaceSlotMigrationError(f"{label} identity/offset drifted")
    if payload.count(new_script) or payload.count(new_header):
        raise SurfaceSlotMigrationError("Source already contains a V232 resident component")
    walkmesh = payload[
        EXPECTED_WALKMESH_PAYLOAD_OFFSET :
        EXPECTED_WALKMESH_PAYLOAD_OFFSET + WALKMESH_SIZE
    ]
    if _sha256(walkmesh) != WALKMESH_SHA256:
        raise SurfaceSlotMigrationError("Resident walkmesh identity drifted")

    if (
        struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0]
        != EXPECTED_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA)[0]
        != EXPECTED_VM_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_ACTOR)[0]
        != EXPECTED_VM_ACTOR_GUEST_POINTER
        or struct.unpack_from("<I", ram, GAME_SCENE_MAP)[0]
        != EXPECTED_GAME_SCENE_MAP
        or struct.unpack_from("<I", ram, FIELD_NUM_ACTORS)[0]
        != EXPECTED_ACTOR_COUNT
        or struct.unpack_from("<I", ram, FIELD_ACTORS)[0]
        != EXPECTED_ACTOR_ARRAY_GUEST_POINTER
    ):
        raise SurfaceSlotMigrationError("Resident field-593 runtime topology drifted")
    actor_array = _guest_ram_offset(
        EXPECTED_ACTOR_ARRAY_GUEST_POINTER, "field actor array"
    )
    actor_array_bytes = bytes(
        ram[actor_array : actor_array + EXPECTED_ACTOR_COUNT * FIELD_ACTOR_STRIDE]
    )
    if _sha256(actor_array_bytes) != EXPECTED_ACTOR_ARRAY_SHA256:
        raise SurfaceSlotMigrationError("Field-593 actor array identity drifted")
    for entity, expected in EXPECTED_ACTOR_DATA_POINTERS.items():
        record = actor_array + entity * FIELD_ACTOR_STRIDE
        actual = _guest_ram_offset(
            struct.unpack_from("<I", ram, record + FIELD_ACTOR_DATA_POINTER)[0],
            f"e{entity} ActorData",
        )
        if actual != expected:
            raise SurfaceSlotMigrationError(f"e{entity} ActorData pointer drifted")

    primary_record = actor_array + 19 * FIELD_ACTOR_STRIDE
    primary_data = EXPECTED_ACTOR_DATA_POINTERS[19]
    primary_checks = (
        (primary_record + ACTOR_RECORD_STATUS_OFFSET, bytes.fromhex("60 02"), "record status"),
        (primary_data + ACTOR_DATA_FLAGS_OFFSET, bytes.fromhex("00 00 00 00"), "flags"),
        (primary_data + ACTOR_DATA_SURFACES_OFFSET, bytes.fromhex("08 00 00 00 00 00 00 00"), "surface"),
        (primary_data + ACTOR_DATA_BOUNDS_OFFSET, bytes.fromhex("30 00 C8 00 30 00 30 00"), "bounds"),
        (primary_data + ACTOR_DATA_POSITION_OFFSET, bytes.fromhex("00 00 50 00 00 00 00 00 00 00 B0 FF"), "position"),
        (primary_data + ACTOR_DATA_OLD_POSITION_OFFSET, bytes.fromhex("50 00 00 00 B0 FF 00 00"), "old position"),
        (primary_data + ACTOR_SCRIPT_SLOT_OFFSET, bytes.fromhex("8C 06 00 03 FF FF 10 00"), "slot 0"),
        (primary_data + ACTOR_CURRENT_PC_OFFSET, bytes.fromhex("8C 06 00 00"), "current PC"),
    )
    for offset, expected, label in primary_checks:
        if ram[offset : offset + len(expected)] != expected:
            raise SurfaceSlotMigrationError(f"V231 e19 {label} drifted")

    for entity, slot0 in zip((4, 5), (OLD_AUX_SLOT0,) * 2, strict=True):
        record = actor_array + entity * FIELD_ACTOR_STRIDE
        actor_data = EXPECTED_ACTOR_DATA_POINTERS[entity]
        checks = (
            (record + ACTOR_RECORD_STATUS_OFFSET, OLD_AUX_RECORD_STATUS, "record status"),
            (actor_data + ACTOR_DATA_FLAGS_OFFSET, OLD_AUX_FLAGS, "flags"),
            (actor_data + ACTOR_DATA_SURFACES_OFFSET, bytes.fromhex("26 00 00 00 00 00 00 00"), "surface"),
            (actor_data + ACTOR_DATA_BOUNDS_OFFSET, bytes.fromhex("10 00 58 00 10 00 10 00"), "bounds"),
            (actor_data + ACTOR_DATA_POSITION_OFFSET, b"\x00" * 12, "position"),
            (actor_data + ACTOR_DATA_OLD_POSITION_OFFSET, b"\x00" * 8, "old position"),
            (actor_data + ACTOR_SCRIPT_SLOT_OFFSET, slot0, "slot 0"),
            (actor_data + ACTOR_CURRENT_PC_OFFSET, bytes.fromhex("8C 06 00 00"), "current PC"),
        )
        for offset, expected, label in checks:
            if ram[offset : offset + len(expected)] != expected:
                raise SurfaceSlotMigrationError(f"V231 e{entity} {label} drifted")

    table_offset, volatile = media_migration._find_resident_archive_table(payload, old_table)
    resident_table = bytes(payload[table_offset : table_offset + ARCHIVE_TABLE_SIZE])
    if (
        table_offset != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or volatile != 1
        or payload[EXPECTED_VOLATILE_TABLE_PAYLOAD_OFFSET]
        != EXPECTED_VOLATILE_TABLE_VALUE
        or _sha256(resident_table) != SOURCE_RESIDENT_TABLE_SHA256
        or resident_table != old_table[:-1] + bytes((EXPECTED_VOLATILE_TABLE_VALUE,))
    ):
        raise SurfaceSlotMigrationError("Resident V231 archive table drifted")

    gamestate = bytes(ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE])
    field_bank = bytes(
        ram[FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE]
    )
    backup_bank = bytes(
        ram[
            GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET :
            GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET + FIELD_VARIABLE_BANK_SIZE
        ]
    )
    camera = _camera_snapshot(ram)
    party_records = _entity_records(ram, actor_array, (1, 2, 3))
    party_data = _entity_actor_data(ram, actor_array, (1, 2, 3))
    patient_doctor_records = _entity_records(ram, actor_array, (13, 16))
    patient_doctor_data = _entity_actor_data(ram, actor_array, (13, 16))
    dialog_windows = bytes(ram[DIALOG_WINDOWS : DIALOG_WINDOWS + DIALOG_WINDOWS_SIZE])
    unrelated_entities = tuple(
        entity
        for entity in range(SCRIPT_ENTITY_COUNT)
        if entity not in TERMINAL_ENTITIES
    )
    unrelated_runtime = _entity_runtime_interleaved(
        ram,
        actor_array,
        unrelated_entities,
    )
    if (
        _sha256(gamestate) != EXPECTED_GAMESTATE_SHA256
        or _sha256(field_bank) != EXPECTED_FIELD_VARIABLE_BANK_SHA256
        or backup_bank != field_bank
        or struct.unpack_from("<H", field_bank, QUARANTINE_KEYCARD_OPERAND)[0]
        != EXPECTED_KEYCARD_WORD
        or struct.unpack_from("<H", backup_bank, QUARANTINE_KEYCARD_OPERAND)[0]
        != EXPECTED_KEYCARD_WORD
        or _sha256(camera) != EXPECTED_CAMERA_SHA256
        or _sha256(party_records) != EXPECTED_PARTY_RECORDS_SHA256
        or _sha256(party_data) != EXPECTED_PARTY_ACTOR_DATA_SHA256
        or _sha256(patient_doctor_records) != EXPECTED_PATIENT_DOCTOR_RECORDS_SHA256
        or _sha256(patient_doctor_data) != EXPECTED_PATIENT_DOCTOR_ACTOR_DATA_SHA256
        or _sha256(dialog_windows) != EXPECTED_DIALOG_WINDOWS_SHA256
        or any(
            struct.unpack_from(
                "<h",
                dialog_windows,
                index * DIALOG_WINDOW_STRIDE + DIALOG_WINDOW_STATUS_OFFSET,
            )[0]
            != -1
            for index in range(4)
        )
        or _sha256(unrelated_runtime) != EXPECTED_UNRELATED_RUNTIME_SHA256
    ):
        raise SurfaceSlotMigrationError("Gameplay/patient/doctor preservation source drifted")
    return {
        "ram_offset": ram_offset,
        "ram": ram,
        "actor_array": actor_array,
        "actor_array_bytes": actor_array_bytes,
        "resident_table": resident_table,
        "walkmesh": walkmesh,
        "gamestate": gamestate,
        "field_bank": field_bank,
        "backup_bank": backup_bank,
        "camera": camera,
        "party_records": party_records,
        "party_data": party_data,
        "patient_doctor_records": patient_doctor_records,
        "patient_doctor_data": patient_doctor_data,
        "dialog_windows": dialog_windows,
        "unrelated_runtime": unrelated_runtime,
    }


def _expected_prefix(source_prefix: bytes, *, compressed_size: int) -> bytes:
    old_name = OLD_CUE_NAME.encode("ascii")
    new_name = NEW_CUE_NAME.encode("ascii")
    if (
        len(old_name) != len(new_name)
        or source_prefix.count(old_name) != 1
        or source_prefix.count(new_name)
    ):
        raise SurfaceSlotMigrationError("Pinned V231 media path changed")
    expected = bytearray(source_prefix.replace(old_name, new_name))
    struct.pack_into(
        "<I",
        expected,
        media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        compressed_size,
    )
    return bytes(expected)


def _runtime_changed_count(patches: Sequence[tuple[int, bytes, bytes, str]]) -> int:
    return sum(
        before != after
        for _offset, old, new, _label in patches
        for before, after in zip(old, new, strict=True)
    )


def migrate_v231_slot1_to_v232(
    state: bytes,
    *,
    old_disc: Path,
    new_disc: Path,
    old_manifest: bytes,
    new_manifest: bytes,
    old_script: bytes,
    new_script: bytes,
    old_header: bytes,
    new_header: bytes,
    old_dialogue: bytes,
    new_dialogue: bytes,
    zstd: _ZstdLike,
) -> tuple[bytes, dict[str, object]]:
    """Return the exact separately writable V232 candidate and report."""

    source_sha256 = _sha256(state)
    if (len(state), source_sha256) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise SurfaceSlotMigrationError(
            f"Source state is {len(state)} / {source_sha256}, expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    old_name = OLD_CUE_NAME.encode("ascii")
    new_name = NEW_CUE_NAME.encode("ascii")
    if (
        len(old_name) != len(new_name)
        or state.count(old_name) != 1
        or state.count(new_name)
    ):
        raise SurfaceSlotMigrationError("Source CUE identity drifted")

    old_table, new_table = _validate_media(
        old_disc=old_disc,
        new_disc=new_disc,
        old_manifest=old_manifest,
        new_manifest=new_manifest,
        old_script=old_script,
        new_script=new_script,
        old_header=old_header,
        new_header=new_header,
        old_dialogue=old_dialogue,
        new_dialogue=new_dialogue,
    )
    source_payload, frame_start, source_prefix = _unpack_state(state, zstd)
    if (
        frame_start != SOURCE_PREFIX_SIZE
        or len(state) - frame_start != SOURCE_COMPRESSED_SIZE
        or _sha256(state[frame_start:]) != SOURCE_COMPRESSED_SHA256
        or _sha256(source_prefix) != SOURCE_PREFIX_SHA256
    ):
        raise SurfaceSlotMigrationError("Source frame/prefix identity drifted")
    snapshots = _validate_source_runtime(
        source_payload,
        old_table=old_table,
        old_script=old_script,
        new_script=new_script,
        old_header=old_header,
        new_header=new_header,
        dialogue=old_dialogue,
    )

    rebuilt_table = new_table[:-1] + bytes((EXPECTED_VOLATILE_TABLE_VALUE,))
    if (
        _sha256(rebuilt_table) != OUTPUT_RESIDENT_TABLE_SHA256
        or _diff_triplets(rebuilt_table, new_table)
        != ((ARCHIVE_TABLE_SIZE - 1, EXPECTED_VOLATILE_TABLE_VALUE, 0),)
    ):
        raise SurfaceSlotMigrationError("V232 resident archive reconstruction drifted")

    # V232's first three header changes are packed-stream offsets from the
    # newly compressed media bundle.  The already-loaded field retains its
    # V231 allocations, so importing those offsets would be allocator-unsafe.
    # Adopt only e19's authored Z coordinate; a cold reload gets the complete
    # ordinary V232 header from media.
    resident_header_data = bytearray(old_header)
    for offset, old, new in RESIDENT_HEADER_DIFFS:
        if resident_header_data[offset] != old:
            raise SurfaceSlotMigrationError("Cached-header e19 coordinate drifted")
        resident_header_data[offset] = new
    resident_header = bytes(resident_header_data)
    if (
        _diff_triplets(old_header, resident_header) != RESIDENT_HEADER_DIFFS
        or _sha256(resident_header) != RESIDENT_HEADER_SHA256
        or any(
            resident_header[offset] != old
            for offset, old, _new in HEADER_DIFFS[:-1]
        )
        or resident_header[HEADER_DIFFS[-1][0]] != new_header[HEADER_DIFFS[-1][0]]
    ):
        raise SurfaceSlotMigrationError("Allocator-safe cached V232 header drifted")

    final = bytearray(source_payload)
    final[
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
    ] = rebuilt_table
    final[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + SCRIPT_SIZE
    ] = new_script
    final[
        EXPECTED_HEADER_PAYLOAD_OFFSET : EXPECTED_HEADER_PAYLOAD_OFFSET + HEADER_SIZE
    ] = resident_header
    ram_offset = int(snapshots["ram_offset"])
    for offset, old, new, label in RUNTIME_PATCHES:
        payload_offset = ram_offset + offset
        if final[payload_offset : payload_offset + len(old)] != old:
            raise SurfaceSlotMigrationError(f"Runtime patch source drifted: {label}")
        final[payload_offset : payload_offset + len(new)] = new
    final_payload = bytes(final)

    table_diffs = _diff_offsets(bytes(snapshots["resident_table"]), rebuilt_table)
    script_diffs = _diff_offsets(old_script, new_script)
    header_diffs = _diff_offsets(old_header, resident_header)
    runtime_offsets: set[int] = set()
    for offset, old, new, _label in RUNTIME_PATCHES:
        runtime_offsets.update(
            ram_offset + offset + relative
            for relative, (before, after) in enumerate(zip(old, new, strict=True))
            if before != after
        )
    expected_offsets = {
        *(EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + offset for offset in table_diffs),
        *(EXPECTED_SCRIPT_PAYLOAD_OFFSET + offset for offset in script_diffs),
        *(EXPECTED_HEADER_PAYLOAD_OFFSET + offset for offset in header_diffs),
        *runtime_offsets,
    }
    actual_diffs = _diff_triplets(source_payload, final_payload)
    actual_offsets = tuple(offset for offset, _old, _new in actual_diffs)
    runtime_diffs = tuple(
        sorted(
            (
                ram_offset + offset + relative,
                before,
                after,
            )
            for offset, old, new, _label in RUNTIME_PATCHES
            for relative, (before, after) in enumerate(zip(old, new, strict=True))
            if before != after
        )
    )
    runtime_changed = _runtime_changed_count(RUNTIME_PATCHES)
    primary_runtime_changed = _runtime_changed_count(RUNTIME_PATCHES[:7])
    auxiliary_runtime_changed = _runtime_changed_count(RUNTIME_PATCHES[7:])
    if (
        len(table_diffs) != EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED
        or len(script_diffs) != EXPECTED_SCRIPT_BYTES_CHANGED
        or len(header_diffs) != EXPECTED_HEADER_BYTES_CHANGED
        or primary_runtime_changed != EXPECTED_PRIMARY_RUNTIME_BYTES_CHANGED
        or auxiliary_runtime_changed != EXPECTED_AUX_RUNTIME_BYTES_CHANGED
        or runtime_changed != EXPECTED_RUNTIME_BYTES_CHANGED
        or actual_offsets != tuple(sorted(expected_offsets))
        or len(actual_offsets) != EXPECTED_PAYLOAD_BYTES_CHANGED
        or _triplet_digest(runtime_diffs) != RUNTIME_DIFF_SHA256
        or _triplet_digest(actual_diffs) != PAYLOAD_DIFF_SHA256
        or (
            OUTPUT_PAYLOAD_SHA256 is not None
            and _sha256(final_payload) != OUTPUT_PAYLOAD_SHA256
        )
    ):
        raise SurfaceSlotMigrationError(
            "Migration escaped the exact archive/ATEL/header/runtime whitelist"
        )

    if (
        final_payload[
            EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
            EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
        ]
        != rebuilt_table
        or final_payload[
            EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + SCRIPT_SIZE
        ]
        != new_script
        or final_payload[
            EXPECTED_HEADER_PAYLOAD_OFFSET : EXPECTED_HEADER_PAYLOAD_OFFSET + HEADER_SIZE
        ]
        != resident_header
        or final_payload[
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET :
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE
        ]
        != old_dialogue
        or final_payload[
            EXPECTED_WALKMESH_PAYLOAD_OFFSET :
            EXPECTED_WALKMESH_PAYLOAD_OFFSET + WALKMESH_SIZE
        ]
        != snapshots["walkmesh"]
    ):
        raise SurfaceSlotMigrationError("Resident component boundary/preservation drifted")

    result_ram_offset, result_ram = _ram_from_payload(final_payload)
    source_ram = bytes(snapshots["ram"])
    actor_array = int(snapshots["actor_array"])
    if (
        result_ram_offset != ram_offset
        or (
            OUTPUT_RAM_SHA256 is not None
            and _sha256(result_ram) != OUTPUT_RAM_SHA256
        )
        or result_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE]
        != snapshots["gamestate"]
        or result_ram[
            FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE
        ]
        != snapshots["field_bank"]
        or result_ram[
            GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET :
            GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET + FIELD_VARIABLE_BANK_SIZE
        ]
        != snapshots["backup_bank"]
        or _camera_snapshot(result_ram) != snapshots["camera"]
        or _entity_records(result_ram, actor_array, (1, 2, 3))
        != snapshots["party_records"]
        or _entity_actor_data(result_ram, actor_array, (1, 2, 3))
        != snapshots["party_data"]
        or _entity_records(result_ram, actor_array, (13, 16))
        != snapshots["patient_doctor_records"]
        or _entity_actor_data(result_ram, actor_array, (13, 16))
        != snapshots["patient_doctor_data"]
        or result_ram[DIALOG_WINDOWS : DIALOG_WINDOWS + DIALOG_WINDOWS_SIZE]
        != snapshots["dialog_windows"]
        or _entity_runtime_interleaved(
            result_ram,
            actor_array,
            tuple(
                entity
                for entity in range(SCRIPT_ENTITY_COUNT)
                if entity not in TERMINAL_ENTITIES
            ),
        )
        != snapshots["unrelated_runtime"]
        or struct.unpack_from(
            "<H",
            result_ram,
            FIELD_SCRIPT_MEMORY + QUARANTINE_KEYCARD_OPERAND,
        )[0]
        != EXPECTED_KEYCARD_WORD
        or struct.unpack_from(
            "<H",
            result_ram,
            GAME_STATE
            + FIELD_VARIABLE_BACKUP_OFFSET
            + QUARANTINE_KEYCARD_OPERAND,
        )[0]
        != EXPECTED_KEYCARD_WORD
    ):
        raise SurfaceSlotMigrationError("Fei/party/GameState/camera/patient/doctor changed")

    # Every field actor except the three terminal carriers remains exact.
    for entity in range(SCRIPT_ENTITY_COUNT):
        if entity in TERMINAL_ENTITIES:
            continue
        record = actor_array + entity * FIELD_ACTOR_STRIDE
        actor_data = _guest_ram_offset(
            struct.unpack_from("<I", source_ram, record + FIELD_ACTOR_DATA_POINTER)[0],
            f"e{entity} ActorData",
        )
        if (
            result_ram[record : record + FIELD_ACTOR_STRIDE]
            != source_ram[record : record + FIELD_ACTOR_STRIDE]
            or result_ram[actor_data : actor_data + ACTOR_DATA_SIZE]
            != source_ram[actor_data : actor_data + ACTOR_DATA_SIZE]
        ):
            raise SurfaceSlotMigrationError(f"Unrelated e{entity} runtime changed")

    primary_record = actor_array + 19 * FIELD_ACTOR_STRIDE
    primary_data = EXPECTED_ACTOR_DATA_POINTERS[19]
    primary_result_checks = (
        (primary_record + 0x28, bytes.fromhex("59 FF FF FF"), "record current Z"),
        (primary_record + 0x48, bytes.fromhex("59 FF FF FF"), "record previous Z"),
        (primary_data + ACTOR_DATA_FLAGS_OFFSET, bytes.fromhex("00 00 04 00"), "facing flag"),
        (primary_data + ACTOR_DATA_SURFACES_OFFSET, bytes.fromhex("1F 00 00 00 00 00 00 00"), "surface"),
        (primary_data + ACTOR_DATA_BOUNDS_OFFSET, bytes.fromhex("02 00 C8 00 1E 00 02 00"), "bounds"),
        (primary_data + ACTOR_DATA_POSITION_OFFSET, bytes.fromhex("00 00 50 00 00 00 00 00 00 00 59 FF"), "position"),
        (primary_data + ACTOR_DATA_OLD_POSITION_OFFSET, bytes.fromhex("50 00 00 00 59 FF 00 00"), "old position"),
        (primary_data + ACTOR_SCRIPT_SLOT_OFFSET, bytes.fromhex("8C 06 00 03 FF FF 10 00"), "stopped init slot"),
        (primary_data + ACTOR_CURRENT_PC_OFFSET, bytes.fromhex("8C 06 00 00"), "current STOP PC"),
    )
    for offset, expected, label in primary_result_checks:
        if result_ram[offset : offset + len(expected)] != expected:
            raise SurfaceSlotMigrationError(f"V232 e19 {label} drifted")

    for entity, slot0 in zip((4, 5), NEW_AUX_SLOT0, strict=True):
        record = actor_array + entity * FIELD_ACTOR_STRIDE
        actor_data = EXPECTED_ACTOR_DATA_POINTERS[entity]
        if (
            result_ram[
                record + ACTOR_RECORD_STATUS_OFFSET :
                record + ACTOR_RECORD_STATUS_OFFSET + 2
            ]
            != NEW_AUX_RECORD_STATUS
            or result_ram[
                actor_data + ACTOR_DATA_FLAGS_OFFSET :
                actor_data + ACTOR_DATA_FLAGS_OFFSET + 4
            ]
            != NEW_AUX_FLAGS
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
            raise SurfaceSlotMigrationError(f"V232 e{entity} initializer queue failed")

    output_actor_array = bytes(
        result_ram[
            actor_array : actor_array + EXPECTED_ACTOR_COUNT * FIELD_ACTOR_STRIDE
        ]
    )
    output_all_actor_data = _entity_actor_data(
        result_ram,
        actor_array,
        tuple(range(SCRIPT_ENTITY_COUNT)),
    )
    if (
        _sha256(output_actor_array) != OUTPUT_ACTOR_ARRAY_SHA256
        or _sha256(output_all_actor_data) != OUTPUT_ALL_SCRIPT_ACTOR_DATA_SHA256
    ):
        raise SurfaceSlotMigrationError("Final field actor runtime identity drifted")
    for entity, (record_sha256, actor_data_sha256) in OUTPUT_TERMINAL_RUNTIME_SHA256.items():
        record = actor_array + entity * FIELD_ACTOR_STRIDE
        actor_data = EXPECTED_ACTOR_DATA_POINTERS[entity]
        if (
            _sha256(result_ram[record : record + FIELD_ACTOR_STRIDE])
            != record_sha256
            or _sha256(result_ram[actor_data : actor_data + ACTOR_DATA_SIZE])
            != actor_data_sha256
        ):
            raise SurfaceSlotMigrationError(f"Final e{entity} runtime identity drifted")

    if any(
        abs(SAVED_FEI_XZ[0] - x) <= TERMINAL_EFFECTIVE_HALF_REACH[0]
        and abs(SAVED_FEI_XZ[1] - z) <= TERMINAL_EFFECTIVE_HALF_REACH[1]
        for x, z in TERMINAL_POSITIONS
    ):
        raise SurfaceSlotMigrationError("Saved aisle stance still reaches a terminal carrier")

    cue_prefix = source_prefix.replace(old_name, new_name)
    result = _pack_state(cue_prefix, final_payload, zstd)
    verified_payload, verified_frame, verified_prefix = _unpack_state(result, zstd)
    expected_prefix = _expected_prefix(
        source_prefix,
        compressed_size=len(result) - frame_start,
    )
    prefix_changed = len(_diff_offsets(source_prefix, expected_prefix))
    if (
        verified_payload != final_payload
        or verified_frame != SOURCE_PREFIX_SIZE
        or verified_prefix != expected_prefix
        or result.count(old_name)
        or result.count(new_name) != 1
        or (
            EXPECTED_PREFIX_BYTES_CHANGED is not None
            and prefix_changed != EXPECTED_PREFIX_BYTES_CHANGED
        )
        or (
            OUTPUT_PREFIX_SHA256 is not None
            and _sha256(verified_prefix) != OUTPUT_PREFIX_SHA256
        )
        or (
            OUTPUT_COMPRESSED_SIZE is not None
            and len(result) - verified_frame != OUTPUT_COMPRESSED_SIZE
        )
        or (
            OUTPUT_COMPRESSED_SHA256 is not None
            and _sha256(result[verified_frame:]) != OUTPUT_COMPRESSED_SHA256
        )
        or (OUTPUT_STATE_SIZE is not None and len(result) != OUTPUT_STATE_SIZE)
        or (
            OUTPUT_STATE_SHA256 is not None
            and _sha256(result) != OUTPUT_STATE_SHA256
        )
    ):
        raise SurfaceSlotMigrationError("Final V232 identity/round trip drifted")

    report: dict[str, object] = {
        "source_sha256": SOURCE_STATE_SHA256,
        "output_sha256": _sha256(result),
        "source_size": len(state),
        "output_size": len(result),
        "field": EXPECTED_FIELD,
        "payload_size": len(final_payload),
        "payload_sha256": _sha256(final_payload),
        "ram_sha256": _sha256(result_ram),
        "compressed_payload_size": len(result) - verified_frame,
        "compressed_payload_sha256": _sha256(result[verified_frame:]),
        "prefix_size": len(verified_prefix),
        "prefix_sha256": _sha256(verified_prefix),
        "prefix_bytes_changed": prefix_changed,
        "payload_bytes_changed": len(actual_offsets),
        "payload_diff_triplet_sha256": PAYLOAD_DIFF_SHA256,
        "archive_table_bytes_changed": len(table_diffs),
        "resident_script_bytes_changed": len(script_diffs),
        "resident_header_bytes_changed": len(header_diffs),
        "terminal_runtime_bytes_changed": runtime_changed,
        "terminal_runtime_diff_triplet_sha256": RUNTIME_DIFF_SHA256,
        "primary_terminal_runtime_bytes_changed": primary_runtime_changed,
        "auxiliary_terminal_runtime_bytes_changed": auxiliary_runtime_changed,
        "resident_archive_table_sha256": OUTPUT_RESIDENT_TABLE_SHA256,
        "resident_script_sha256": NEW_SCRIPT_SHA256,
        "resident_header_sha256": RESIDENT_HEADER_SHA256,
        "prepared_media_header_sha256": NEW_HEADER_SHA256,
        "resident_dialogue_sha256": DIALOGUE_SHA256,
        "resident_walkmesh_sha256": WALKMESH_SHA256,
        "terminal_entities": list(TERMINAL_ENTITIES),
        "terminal_positions": [list(position) for position in TERMINAL_POSITIONS],
        "terminal_triangles": list(TERMINAL_TRIANGLES),
        "terminal_bounds_half_width_depth": [1, 15],
        "terminal_requires_facing": True,
        "shared_terminal_action_pc": f"0x{TERMINAL_ACTION_PC:04X}",
        "queued_terminal_initializers": {
            "e4": f"0x{TERMINAL_INIT_PCS[1]:04X}",
            "e5": f"0x{TERMINAL_INIT_PCS[2]:04X}",
        },
        "old_aisle_carrier_disabled": True,
        "saved_stance": [SAVED_FEI_XZ[0], SAVED_FEI_XZ[1], SAVED_FEI_YAW],
        "saved_stance_is_outside_all_terminal_reach": True,
        "resident_compatibility_layout": True,
        "resident_v231_packed_stream_offsets_preserved": True,
        "cold_reload_uses_normal_v232": True,
        "fei_party_gamestate_field_variables_camera_preserved": True,
        "patient_doctor_state_preserved": True,
        "security_and_quarantine_keycard_state_preserved": True,
        "keycard_operand_word": f"0x{EXPECTED_KEYCARD_WORD:04X}",
        "dialog_windows_sha256": EXPECTED_DIALOG_WINDOWS_SHA256,
        "output_actor_array_sha256": OUTPUT_ACTOR_ARRAY_SHA256,
        "output_all_script_actor_data_sha256": OUTPUT_ALL_SCRIPT_ACTOR_DATA_SHA256,
        "resident_dialogue_walkmesh_preserved": True,
        "resident_archive_volatile_tail_preserved": True,
        "allocator_safe": True,
        "round_trip_verified": True,
        "safe_to_mount_after_duckstation_is_fully_closed": True,
        "live_slot1_modified": False,
        "changed_resource_ids": list(CHANGED_RESOURCE_IDS),
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "v231_manifest_sha256": OLD_MANIFEST_SHA256,
        "v232_manifest_sha256": NEW_MANIFEST_SHA256,
        "v231_disc_sha256": OLD_DISC_SHA256,
        "v232_disc_sha256": NEW_DISC_SHA256,
    }
    return result, report


def _report_blob(report: dict[str, object]) -> bytes:
    return (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=SOURCE_FIXTURE)
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
        "--old-manifest",
        type=Path,
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v231_stage" / "manifest.json",
    )
    parser.add_argument(
        "--new-manifest",
        type=Path,
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v232_stage" / "manifest.json",
    )
    for version in (231, 232):
        stage = PROJECT_ROOT / "work" / f"surface_soylent_campaign_v{version}_stage" / "clones" / "field_593_disc1_donor"
        parser.add_argument(
            f"--{'old' if version == 231 else 'new'}-script",
            type=Path,
            default=stage / "05_scripts.bin",
        )
        parser.add_argument(
            f"--{'old' if version == 231 else 'new'}-header",
            type=Path,
            default=stage / "header.bin",
        )
        parser.add_argument(
            f"--{'old' if version == 231 else 'new'}-dialogue",
            type=Path,
            default=stage / "07_dialogue.bin",
        )
    parser.add_argument(
        "--zstd",
        type=Path,
        default=PROJECT_ROOT / "work" / "duckstation" / "zstd.dll",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "save_candidates"
            / "SLUS-00669_1_v232_from_6adde32f_field593_terminal_proximity.sav"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "save_candidates"
            / "SLUS-00669_1_v232_from_6adde32f_field593_terminal_proximity.json"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        source_path = args.source.resolve()
        output = args.output.resolve()
        report_path = args.report.resolve()
        if output == LIVE_SLOT1 or report_path == LIVE_SLOT1:
            raise SurfaceSlotMigrationError("Output/report may not be the live Slot 1")
        if output == source_path or report_path == source_path:
            raise SurfaceSlotMigrationError("Output/report may not replace the source state")
        if output == report_path:
            raise SurfaceSlotMigrationError("Output and report paths must be distinct")
        _validate_file(args.zstd, ZSTD_SIZE, ZSTD_SHA256, "zstd codec")
        result, report = migrate_v231_slot1_to_v232(
            source_path.read_bytes(),
            old_disc=args.old_disc,
            new_disc=args.new_disc,
            old_manifest=args.old_manifest.read_bytes(),
            new_manifest=args.new_manifest.read_bytes(),
            old_script=args.old_script.read_bytes(),
            new_script=args.new_script.read_bytes(),
            old_header=args.old_header.read_bytes(),
            new_header=args.new_header.read_bytes(),
            old_dialogue=args.old_dialogue.read_bytes(),
            new_dialogue=args.new_dialogue.read_bytes(),
            zstd=media_migration._Zstd(args.zstd),
        )
        report_blob = _report_blob(report)
        if (
            OUTPUT_REPORT_SIZE is not None
            and len(report_blob) != OUTPUT_REPORT_SIZE
        ) or (
            OUTPUT_REPORT_SHA256 is not None
            and _sha256(report_blob) != OUTPUT_REPORT_SHA256
        ):
            raise SurfaceSlotMigrationError("V232 report identity drifted")
        if output.exists() and output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Refusing to overwrite a different V232 candidate")
        if report_path.exists() and report_path.read_bytes() != report_blob:
            raise SurfaceSlotMigrationError("Refusing to overwrite a different V232 report")
        output.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        report_path.write_bytes(report_blob)
        if output.read_bytes() != result or report_path.read_bytes() != report_blob:
            raise SurfaceSlotMigrationError("Written V232 candidate/report failed verification")
    except (
        OSError,
        ValueError,
        SurfaceSlotMigrationError,
        media_migration.StateMigrationError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote V232 candidate: {output}")
    print(f"Wrote migration report: {report_path}")
    print(f"SHA-256: {report['output_sha256']}")
    print("The live Slot 1 was not modified. Install only after DuckStation is fully closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
