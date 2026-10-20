#!/usr/bin/env python3
"""Migrate the exact live V224 field-550 Slot 1 state to V225 safely.

The saved party is standing at the north door of the doctor's office.  V224
keeps field 352's disconnected exterior walkmesh edge and gives the door a
round collision seal, while its automatic door poll is still the retired
entity-14 cavity.  V225 installs a 63-byte leader poll in the prefix of that
same 87-byte allocation and uses a thin z-normal rectangular seal for every
field-352 medical-room variant.

This helper is deliberately fail-closed.  It accepts one exact V224 state,
pins both media images and the staged field-550 header/script pair, changes
only six resident archive-table bytes, 68 resident ATEL bytes, the two-byte
loaded-header e19 Z coordinate, and eleven live e19 collision bytes.  It never
writes DuckStation's live Slot 1; the CLI emits only a separate candidate and
JSON report.
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
SOURCE_BACKUP = (
    PROJECT_ROOT
    / "work"
    / "save_backups"
    / "SLUS-00669_1_v224_field550_door_clip_6df7129d.sav"
).resolve()

SOURCE_STATE_SIZE = 1_851_504
SOURCE_STATE_SHA256 = "6df7129d144f7b9efe785f24749ca68512f10dda04ca8d4022cadf757c9b5dae"
SOURCE_PREFIX_SIZE = 0xABD1
SOURCE_PREFIX_SHA256 = "43576719b7f831cc4fa4f62ef3d6794bc2c5627da9fbf87c6843bbec015a7fcc"
SOURCE_COMPRESSED_SIZE = 1_807_519
SOURCE_COMPRESSED_SHA256 = "a362bfe2f71d9e03846524346d949b847f54e16bf540c97d79e742fadf577491"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "2a17720d0054133cc2fbc8b60e484d895614a47569b91ebacbbd3dcdad803003"
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
SOURCE_RAM_SHA256 = "31d6a9e086e3870a41e94755d9a9bd090113254c02f76562ea1b4031788271b8"

OUTPUT_STATE_SIZE = 1_672_710
OUTPUT_STATE_SHA256 = "b8638edcf76e2c19a829711b57cc7c0beded7a89c60871e2cc8aaac60616f9eb"
OUTPUT_PREFIX_SHA256 = "8dab824cc93a2150a7d766e798afdec70a6172d0316b69317dcdd6cb23bfec3d"
OUTPUT_COMPRESSED_SIZE = 1_628_725
OUTPUT_COMPRESSED_SHA256 = "a1d542be06f0b474b5c2c4d9703b92aec62b7cbed79221d990e3522f36a1c9fd"
OUTPUT_PAYLOAD_SHA256 = "f27cebfc3eb00498cbb76d339d78ee98779c2b2c8868559254f474969f0243ed"
OUTPUT_RAM_SHA256 = "60d52d04106554e57b1f444a53f3a6e5a77fbc88a5092429f5c441c4edaea2e1"

OLD_DISC_SIZE = NEW_DISC_SIZE = 698_642_784
OLD_DISC_SHA256 = "6d0854e878f677eee7e8c57fd5084d0f28b9cc776b758934925ef353da30022d"
NEW_DISC_SHA256 = "539e2e33266d71337666c84d9d3a153dfd7555d8db933efadc49376483e6e1ff"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v224.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v225.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = "4cd7c8be1096148c00d619f776754e6e15cf55dffcc9a3cc97b8887af333944d"
NEW_CUE_SHA256 = "6a289550cec7003e9742d75f862db41d37214afe499d0dcddab1892839f6b8fd"

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = "9ece390ff3c1d88d8604892f3355ec1f70687d3931a3a8f06b60fc5d27ce362c"
NEW_ARCHIVE_TABLE_SHA256 = "e89e07218cfd6843357d7480d427bd9c4cc27b53792ed83ddebbb485de2fc875"
ARCHIVE_TABLE_DIFFS = (
    (0x2E86, 0xC0, 0xC8),
    (0x2F74, 0x38, 0x40),
    (0x30C4, 0xCC, 0xC0),
    (0x30D2, 0xE4, 0xD8),
    (0x30E0, 0xA0, 0x98),
)
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
SOURCE_RESIDENT_TABLE_SHA256 = "3eacc1ac53db105f07c987a3eeb20cfbbca9df9fefe21a8c7a4c4750e14dfba0"
OUTPUT_RESIDENT_TABLE_SHA256 = "337607d4873dcc0f5c2eee5cd69f7d61f130badb074b3441e09a60cd0e801eb9"
RESIDENT_VS_OLD_MEDIA_DIFFS = (
    (0x3268, 0xE8, 0xE0),
    (0x7FFF, 0xE0, 0x00),
)
# 0x3268 is field 621's nonvolatile FAT entry and must catch up before the
# saved party returns there.  Only the table's final runtime byte is volatile.
RESIDENT_ARCHIVE_TABLE_PATCHES = (
    *ARCHIVE_TABLE_DIFFS,
    (0x3268, 0xE8, 0xE0),
)
RESIDENT_VS_NEW_MEDIA_DIFFS = ((0x7FFF, 0xE0, 0x00),)

OLD_HEADER_SIZE = NEW_HEADER_SIZE = 1_008
OLD_HEADER_SHA256 = "65855edb709abbbe945d32ea77fc63b058d24f8a26316bfdec5b6adbbd8cbbc6"
NEW_HEADER_SHA256 = "438e5449e97b1de003fde24bf40ecf8b68f9a14a612e6fb58a53b4f9dbfa1db6"
HEADER_DIFFS = (
    (0x0148, 0xAC, 0xB4),
    (0x014C, 0x48, 0x50),
    (0x0150, 0xBC, 0xC4),
    (0x02CC, 0xFA, 0x0A),
    (0x02CD, 0x00, 0x01),
)
HEADER_ACTOR_TABLE_OFFSET = 0x190
HEADER_E19_Z_OFFSET = 0x2CC
EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET = 0x1D9E3E
EXPECTED_LOADED_HEADER_RAM_OFFSET = 0x1D83DC
SOURCE_LOADED_HEADER_SHA256 = OLD_HEADER_SHA256
OUTPUT_LOADED_HEADER_SHA256 = "a061c2a01a90675b62add0f4f36021cba9101bdf6dbf7835a770c89193e0c347"

OLD_SCRIPT_SIZE = NEW_SCRIPT_SIZE = 5_414
OLD_SCRIPT_SHA256 = "544e77f06e8e3e3a0f14e48399a2d105c0fa4227ffeed3ae864407302e832e86"
NEW_SCRIPT_SHA256 = "3e8b9942cc6c75eacec771df36d8f322ae9b831f4fd2017b1b5266d47087e134"
EXPECTED_SCRIPT_PAYLOAD_OFFSET = 0x10CD56
EXPECTED_SCRIPT_GUEST_POINTER = 0x8010B2F4
EXPECTED_VM_SCRIPT_GUEST_POINTER = 0x8010B978
SCRIPT_ALLOCATED_CAPACITY = 5_464
SCRIPT_GAP_SIZE = 50
SCRIPT_GAP_SHA256 = "30a3d4b44016487a842d979786dc58fe9f1afb129a82b4e106e9fd78a2162618"
NORMAL_BYTECODE_OFFSET = 0x684
NORMAL_BYTECODE_SIZE = 0xEA2
SHARED_STOP_PC = 0x068C
FORWARD_POLL_PC = 0x044E
FORWARD_POLL_CAVITY_END_PC = 0x04A5
FORWARD_POLL_CAVITY_ENTITY = 14
SEAL_STOP_PC = 0x0A56
SEAL_RELEASE_PC = 0x0A57
SEAL_INIT_PC = 0x0A73
NATIVE_EXIT_GATE_PC = 0x0DDB
NATIVE_EXIT_GATE_SHA256 = "92603ab6ce845f78fefbfc138bfbc91183d41a7993ca7ace6c21a68e031a85e3"
FORWARD_POLL_SOURCE_CAVITY = bytes.fromhex(
    "21 30 81 4A 5A 00 3E 00 C0 4A 5A 00 C8 FF C0 69 06 80 "
    "26 0A 80 2C 04 FE 0D 01 80 D2 24 00 00 9C 09 FF C5 26 "
    "0A 80 2C 00 D2 25 00 00 9C 09 FE C6 26 0A 80 69 00 80 "
    "26 05 80 D2 26 00 00 9C 09 FF C7 FE 24 26 04 80 FE AA "
    "FF 35 E0 00 00 00 40 FE 53 2C 00 69 06 80 00"
)
FORWARD_POLL = bytes.fromhex(
    "2D FF F8 07 FA 07 FC 07 "
    "02 F8 07 C0 FF 44 87 04 "
    "02 F8 07 41 00 43 87 04 "
    "02 FA 07 E4 00 44 87 04 "
    "09 11 22 "
    "2D FF F8 07 FA 07 FC 07 "
    "02 FA 07 E4 00 44 4E 04 "
    "26 00 80 01 71 04 "
    "26 00 80 01 4E 04"
)
OLD_SEAL_INIT = bytes.fromhex(
    "0B 00 80 19 00 00 FA 00 C0 1A 00 F8 04 00 20 F8 "
    "07 04 00 18 00 00 64 0E F8 00 10 00 2A 23 00"
)
NEW_SEAL_INIT = bytes.fromhex(
    "0B 00 80 19 00 00 0A 01 C0 1A 00 F8 00 00 20 F8 "
    "07 04 00 18 18 08 64 08 F8 00 10 00 2A 23 00"
)

EXPECTED_DIALOGUE_PAYLOAD_OFFSET = 0x10E2AE
EXPECTED_DIALOGUE_GUEST_POINTER = 0x8010C84C
EXPECTED_SMALL_COMPONENT_POINTER = 0x8010C834
DIALOGUE_SIZE = 6_056
DIALOGUE_SHA256 = "3c1f8cc6906384c6a9a0bb23ee5710bde6a524f656baa4b6ac8c49659d51bc4e"
DIALOGUE_GAP_SIZE = 24
DIALOGUE_GAP_SHA256 = "11cf0557c6dcdbab1489c5684701a967854bf42dcef9b65ba1b73cad135399c9"
EXPECTED_WALKMESH_PAYLOAD_OFFSET = 0x10FA6E
WALKMESH_SIZE = 1_948
WALKMESH_SHA256 = "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d8cca4238393571df"

FIELD_CUR_DIALOGUE_FILE = 0x0ADBF0
FIELD_SMALL_COMPONENT = 0x0ADBF4
GAME_SCENE_MAP = 0x04F34C
EXPECTED_FIELD = 550
EXPECTED_ACTOR_COUNT = 38
SCRIPT_ENTITY_COUNT = 24
EXPECTED_ACTOR_ARRAY_GUEST_POINTER = 0x80113B24
EXPECTED_VM_ACTOR_GUEST_POINTER = 0x801170E0
ACTOR_ARRAY_SIZE = EXPECTED_ACTOR_COUNT * FIELD_ACTOR_STRIDE
ACTOR_DATA_SIZE = 0x138
SOURCE_ACTOR_ARRAY_SHA256 = "505975a87711ccfe4985209bba16956b20e961b9f9cf5aebba7a2333f94edf20"
OUTPUT_ACTOR_ARRAY_SHA256 = "024c81e8ee0ed46a280b25c1ed057f2c04b371044f18915a546c63173ddb706e"
SOURCE_ACTOR_DATA_SHA256 = "4e9061fc0111bc6da39cafa96ab2410fc1d765dea71b792296e7f2df710b21a0"
OUTPUT_ACTOR_DATA_SHA256 = "346a68cf39da35236349a2875279be69b57e267592f206347f0af927354b159e"

ACTOR_DATA_FLAGS_OFFSET = 0x00
ACTOR_DATA_SURFACES_OFFSET = 0x08
ACTOR_DATA_BOUNDS_OFFSET = 0x18
ACTOR_DATA_POSITION_OFFSET = 0x20
ACTOR_DATA_OLD_POSITION_OFFSET = 0x68
ACTOR_SCRIPT_SLOT_OFFSET = 0x8C
ACTOR_CURRENT_PC_OFFSET = 0xCC
ACTOR_FACING_OFFSET = 0x106
CONTROLLER_ENTITY = 0
FEI_ENTITY = 1
DOCTOR_ENTITY = 16
CROSS_CARRIER_ENTITY = 17
DOOR_LEAF_ENTITY = 18
SEAL_ENTITY = 19
SECURITY_ENTITIES = (20, 21, 22, 23)
EXPECTED_FEI_POSITION = (2_841_247, 0, 14_988_804)
EXPECTED_FEI_TRIANGLES = (15, 0, 0, 0)
EXPECTED_FEI_FACING = 0x0800
EXPECTED_FEI_CURRENT = bytes.fromhex("5F 01 00 00")
EXPECTED_CONTROLLER_CURRENT = bytes.fromhex("8C 06 00 00")
EXPECTED_LEAF_CURRENT = bytes.fromhex("8C 06 00 00")
EXPECTED_SEAL_CURRENT = bytes.fromhex("56 0A 00 00")
CLOSED_LEAF_MATRIX = bytes.fromhex(
    "00 00 00 00 00 10 00 00 00 10 00 00 00 F0 00 00 00 00"
)

E19_RECORD_RAM_OFFSET = 0x1141F8
E19_ACTOR_DATA_RAM_OFFSET = 0x116A00
SOURCE_E19_RECORD_SHA256 = "c58e57fe256194031d172d741e219908325f9ca679064eea7e3ea0f2c75b78df"
SOURCE_E19_ACTOR_DATA_SHA256 = "16b18f71bf427fcbbbcf2f5a988379648499be4e2a6e2e2e545d50cc60802f28"
OUTPUT_E19_RECORD_SHA256 = "31879064a785cc76cfd54f7b975be4c5ae960f9ef5b943ce98dfaf6c8aaade3e"
OUTPUT_E19_ACTOR_DATA_SHA256 = "fce631b1a4921d0481eb868c83d0a30a5c8de77780b61e9fce6d7473667d487f"
OLD_E19_RECORD_Z = bytes.fromhex("FA 00 00 00")
NEW_E19_RECORD_Z = bytes.fromhex("0A 01 00 00")
OLD_E19_FLAGS = bytes.fromhex("30 01 02 00")
NEW_E19_FLAGS = bytes.fromhex("30 21 02 00")
OLD_E19_BOUNDS = bytes.fromhex("10 00 C8 00 10 00 1C 00")
NEW_E19_BOUNDS = bytes.fromhex("30 00 C8 00 10 00 10 00")
OLD_E19_CURRENT_POSITION = bytes.fromhex("00 00 00 00 00 00 00 00 00 00 FA 00")
NEW_E19_CURRENT_POSITION = bytes.fromhex("00 00 00 00 00 00 00 00 00 00 0A 01")
OLD_E19_OLD_POSITION = bytes.fromhex("00 00 00 00 FA 00 00 00")
NEW_E19_OLD_POSITION = bytes.fromhex("00 00 00 00 0A 01 00 00")
RUNTIME_PATCHES = (
    (E19_RECORD_RAM_OFFSET + 0x28, OLD_E19_RECORD_Z, NEW_E19_RECORD_Z, "e19 matrix 0 Z"),
    (E19_RECORD_RAM_OFFSET + 0x48, OLD_E19_RECORD_Z, NEW_E19_RECORD_Z, "e19 matrix 1 Z"),
    (E19_ACTOR_DATA_RAM_OFFSET, OLD_E19_FLAGS, NEW_E19_FLAGS, "e19 rectangle flag"),
    (
        E19_ACTOR_DATA_RAM_OFFSET + ACTOR_DATA_BOUNDS_OFFSET,
        OLD_E19_BOUNDS,
        NEW_E19_BOUNDS,
        "e19 rectangular bounds",
    ),
    (
        E19_ACTOR_DATA_RAM_OFFSET + ACTOR_DATA_POSITION_OFFSET,
        OLD_E19_CURRENT_POSITION,
        NEW_E19_CURRENT_POSITION,
        "e19 current position",
    ),
    (
        E19_ACTOR_DATA_RAM_OFFSET + ACTOR_DATA_OLD_POSITION_OFFSET,
        OLD_E19_OLD_POSITION,
        NEW_E19_OLD_POSITION,
        "e19 old position",
    ),
)

FIELD_VARIABLE_BACKUP_OFFSET = 0x1930
FIELD_VARIABLE_BANK_SIZE = 0x400
APPOINTMENT_OPERAND = 0x03EE
STATE_OPERAND = 0x03FA
EXPECTED_APPOINTMENT_WORD = 0x4005
EXPECTED_STATE_WORD = 0x00F0
DIALOG_WINDOWS = 0x0C2698
DIALOG_WINDOW_STRIDE = 0x498
DIALOG_WINDOWS_SIZE = 4 * DIALOG_WINDOW_STRIDE
DIALOG_WINDOW_STATUS_OFFSET = 0x40E
EXPECTED_GAMESTATE_SHA256 = "7243501f0e2af4d31fc266412f95796456f596795bafc3c240f69e6db231500f"
EXPECTED_FIELD_VARIABLE_BANK_SHA256 = "7d02d2247ba01e056e1e370176a2d63f0e78982284b99be7c1cdf360f9653e35"
EXPECTED_CAMERA_SHA256 = "028b46cc93d8bac97d40ed83b15ba45602a729df7b4786f7f7ad091b384df468"
EXPECTED_DIALOG_WINDOWS_SHA256 = "8b8d2743404ca97d8690ccdd1bcd59d997da9fd3f9a00a6800a465274d3e3eef"

EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED = 6
EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED = 68
EXPECTED_LOADED_HEADER_BYTES_CHANGED = 2
EXPECTED_RUNTIME_BYTES_CHANGED = 11
EXPECTED_PAYLOAD_BYTES_CHANGED = 87
EXPECTED_PREFIX_BYTES_CHANGED = 4


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output whenever the pinned V224/V225 contract drifts."""


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


def _unpack_state(state: bytes, zstd: _ZstdLike) -> tuple[bytes, int, bytes]:
    if (
        len(state) < media_migration.DUCKSTATION_STATE_HEADER_SIZE
        or state[:4] != media_migration.DUCKSTATION_STATE_MAGIC
    ):
        raise SurfaceSlotMigrationError("Input is not a supported DuckStation state")
    compression, compressed_size, payload_size, frame_start = struct.unpack_from(
        "<IIII", state, media_migration.DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET
    )
    if compression != media_migration.DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise SurfaceSlotMigrationError("DuckStation payload is not Zstandard-compressed")
    frame = state[frame_start : frame_start + compressed_size]
    if (
        frame_start + compressed_size != len(state)
        or zstd.frame_size(frame) != compressed_size
    ):
        raise SurfaceSlotMigrationError("DuckStation compressed frame span drifted")
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
    old_name, new_name = OLD_CUE_NAME.encode("ascii"), NEW_CUE_NAME.encode("ascii")
    expected = bytearray(source_prefix.replace(old_name, new_name))
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
        raise SurfaceSlotMigrationError("Serialized RAM span is truncated")
    return offset, ram


def _camera_snapshot(ram: bytes) -> bytes:
    return b"".join(ram[address : address + 16] for address in CAMERA_VECTORS.values())


def _patch_reconstruction(
    source: bytes,
    patches: Sequence[tuple[int, bytes, bytes]],
) -> bytes:
    result = bytearray(source)
    for offset, old, new in patches:
        if len(old) != len(new) or result[offset : offset + len(old)] != old:
            raise SurfaceSlotMigrationError(f"Patch source drifted at 0x{offset:X}")
        result[offset : offset + len(new)] = new
    return bytes(result)


def _script_patches() -> tuple[tuple[int, bytes, bytes], ...]:
    return (
        (0x0086, struct.pack("<H", SHARED_STOP_PC), struct.pack("<H", FORWARD_POLL_PC)),
        (
            NORMAL_BYTECODE_OFFSET + FORWARD_POLL_PC,
            FORWARD_POLL_SOURCE_CAVITY[: len(FORWARD_POLL)],
            FORWARD_POLL,
        ),
        (NORMAL_BYTECODE_OFFSET + SEAL_INIT_PC, OLD_SEAL_INIT, NEW_SEAL_INIT),
    )


def _validate_file(path: Path, size: int, sha256: str, label: str) -> None:
    if not path.is_file() or path.stat().st_size != size or _file_sha256(path) != sha256:
        raise SurfaceSlotMigrationError(f"{label} identity drifted")


def _validate_resources(
    old_disc: Path,
    new_disc: Path,
    old_header: bytes,
    new_header: bytes,
    old_script: bytes,
    new_script: bytes,
) -> tuple[bytes, bytes]:
    identities = (
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V224 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V225 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V224 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V225 CUE"),
    )
    for path, size, sha256, label in identities:
        _validate_file(path, size, sha256, label)
    blobs = (
        (old_header, OLD_HEADER_SIZE, OLD_HEADER_SHA256, "V224 field-550 header"),
        (new_header, NEW_HEADER_SIZE, NEW_HEADER_SHA256, "V225 field-550 header"),
        (old_script, OLD_SCRIPT_SIZE, OLD_SCRIPT_SHA256, "V224 field-550 script"),
        (new_script, NEW_SCRIPT_SIZE, NEW_SCRIPT_SHA256, "V225 field-550 script"),
    )
    for blob, size, sha256, label in blobs:
        if (len(blob), _sha256(blob)) != (size, sha256):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    if _diff_triplets(old_header, new_header) != HEADER_DIFFS:
        raise SurfaceSlotMigrationError("V224/V225 field-550 header delta drifted")
    if (
        struct.unpack_from("<h", old_header, HEADER_E19_Z_OFFSET)[0] != 250
        or struct.unpack_from("<h", new_header, HEADER_E19_Z_OFFSET)[0] != 266
    ):
        raise SurfaceSlotMigrationError("V225 field-header e19 position drifted")

    expected_script = _patch_reconstruction(old_script, _script_patches())
    if (
        expected_script != new_script
        or len(_diff_offsets(old_script, new_script))
        != EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED
    ):
        raise SurfaceSlotMigrationError("V224/V225 normal script delta drifted")
    old_editor, new_editor = AtelScript(old_script), AtelScript(new_script)
    pointer_diffs = tuple(
        (entity, script)
        for entity in range(old_editor.entity_count)
        for script in range(32)
        if old_editor.get_script_pointer(entity, script)
        != new_editor.get_script_pointer(entity, script)
    )
    cavity_entries = tuple(
        (entity, script)
        for entity in range(new_editor.entity_count)
        for script in range(32)
        if FORWARD_POLL_PC
        <= new_editor.get_script_pointer(entity, script)
        < FORWARD_POLL_CAVITY_END_PC
    )
    if (
        old_editor.entity_count != SCRIPT_ENTITY_COUNT
        or new_editor.entity_count != SCRIPT_ENTITY_COUNT
        or old_editor.bytecode_offset != NORMAL_BYTECODE_OFFSET
        or new_editor.bytecode_offset != NORMAL_BYTECODE_OFFSET
        or old_editor.bytecode_size != NORMAL_BYTECODE_SIZE
        or new_editor.bytecode_size != NORMAL_BYTECODE_SIZE
        or old_editor.get_script_pointer(0, 1) != SHARED_STOP_PC
        or new_editor.get_script_pointer(0, 1) != FORWARD_POLL_PC
        or pointer_diffs != ((0, 1),)
        or cavity_entries != ((0, 1),)
        or any(
            old_editor.get_script_pointer(FORWARD_POLL_CAVITY_ENTITY, script)
            != SHARED_STOP_PC
            for script in range(32)
        )
        or old_editor.bytecode[FORWARD_POLL_PC:FORWARD_POLL_CAVITY_END_PC]
        != FORWARD_POLL_SOURCE_CAVITY
        or new_editor.bytecode[FORWARD_POLL_PC : FORWARD_POLL_PC + len(FORWARD_POLL)]
        != FORWARD_POLL
        or new_editor.bytecode[
            FORWARD_POLL_PC + len(FORWARD_POLL) : FORWARD_POLL_CAVITY_END_PC
        ]
        != FORWARD_POLL_SOURCE_CAVITY[len(FORWARD_POLL) :]
        or old_editor.get_script_pointer(SEAL_ENTITY, 0) != SEAL_INIT_PC
        or new_editor.get_script_pointer(SEAL_ENTITY, 0) != SEAL_INIT_PC
        or old_editor.get_script_pointer(SEAL_ENTITY, 4) != SEAL_RELEASE_PC
        or new_editor.get_script_pointer(SEAL_ENTITY, 4) != SEAL_RELEASE_PC
        or old_editor.get_script_pointer(CROSS_CARRIER_ENTITY, 2) != NATIVE_EXIT_GATE_PC
        or new_editor.get_script_pointer(CROSS_CARRIER_ENTITY, 2) != NATIVE_EXIT_GATE_PC
        or old_editor.bytecode[SEAL_INIT_PC : SEAL_INIT_PC + len(OLD_SEAL_INIT)]
        != OLD_SEAL_INIT
        or new_editor.bytecode[SEAL_INIT_PC : SEAL_INIT_PC + len(NEW_SEAL_INIT)]
        != NEW_SEAL_INIT
        or old_editor.bytecode[NATIVE_EXIT_GATE_PC:] != new_editor.bytecode[NATIVE_EXIT_GATE_PC:]
        or _sha256(old_editor.bytecode[NATIVE_EXIT_GATE_PC:])
        != NATIVE_EXIT_GATE_SHA256
    ):
        raise SurfaceSlotMigrationError("V224/V225 field-550 ATEL topology drifted")

    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    if (
        len(old_table) != ARCHIVE_TABLE_SIZE
        or _sha256(old_table) != OLD_ARCHIVE_TABLE_SHA256
        or _sha256(new_table) != NEW_ARCHIVE_TABLE_SHA256
        or _diff_triplets(old_table, new_table) != ARCHIVE_TABLE_DIFFS
    ):
        raise SurfaceSlotMigrationError("V224/V225 archive-table delta drifted")
    return old_table, new_table


def _actor_data_offset(ram: bytes, actor_base: int, entity: int) -> int:
    pointer = struct.unpack_from(
        "<I",
        ram,
        actor_base + entity * FIELD_ACTOR_STRIDE + FIELD_ACTOR_DATA_POINTER,
    )[0]
    offset = pointer & 0x1FFFFFFF
    if not 0 < offset <= RAM_SIZE - ACTOR_DATA_SIZE:
        raise SurfaceSlotMigrationError(f"e{entity} ActorData pointer is outside PSX RAM")
    return offset


def _validate_walkmesh(walkmesh: bytes) -> None:
    if (len(walkmesh), _sha256(walkmesh)) != (WALKMESH_SIZE, WALKMESH_SHA256):
        raise SurfaceSlotMigrationError("Resident field-550 walkmesh identity drifted")
    triangle_offset, vertex_offset = struct.unpack_from("<II", walkmesh, 0x18)

    def triangle(index: int) -> tuple[tuple[tuple[int, int, int], ...], tuple[int, int, int]]:
        record = triangle_offset + index * 14
        indices = struct.unpack_from("<3H", walkmesh, record)
        neighbors = struct.unpack_from("<3h", walkmesh, record + 6)
        vertices = tuple(
            struct.unpack_from("<hhhh", walkmesh, vertex_offset + vertex * 8)[:3]
            for vertex in indices
        )
        return vertices, neighbors

    if (
        struct.unpack_from("<II", walkmesh, 0) != (2, 560)
        or (triangle_offset, vertex_offset) != (0x28, 0x258)
        or triangle(15)
        != (((160, 0, 234), (69, 0, 66), (23, 0, 234)), (9, 16, -1))
        or triangle(3)
        != (((23, 0, 234), (-25, 0, 234), (0, 0, 243)), (16, 35, 34))
        or triangle(34)
        != (((0, 0, 306), (23, 0, 234), (0, 0, 243)), (-1, 3, 35))
        or triangle(35)
        != (((0, 0, 243), (-25, 0, 234), (0, 0, 306)), (3, -1, 34))
    ):
        raise SurfaceSlotMigrationError("Field-550 doorway walkmesh topology drifted")


def _validate_source(
    payload: bytes,
    old_table: bytes,
    old_header: bytes,
    old_script: bytes,
) -> dict[str, object]:
    if (len(payload), _sha256(payload)) != (SOURCE_PAYLOAD_SIZE, SOURCE_PAYLOAD_SHA256):
        raise SurfaceSlotMigrationError("V224 decompressed payload identity drifted")
    ram_offset, ram = _ram_from_payload(payload)
    if _sha256(ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("V224 serialized RAM identity drifted")

    table_offset = EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
    resident_table = payload[table_offset : table_offset + ARCHIVE_TABLE_SIZE]
    script = payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + OLD_SCRIPT_SIZE]
    dialogue = payload[
        EXPECTED_DIALOGUE_PAYLOAD_OFFSET : EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE
    ]
    walkmesh = payload[
        EXPECTED_WALKMESH_PAYLOAD_OFFSET : EXPECTED_WALKMESH_PAYLOAD_OFFSET + WALKMESH_SIZE
    ]
    loaded_header = payload[
        EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET : EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET + OLD_HEADER_SIZE
    ]
    if (
        (len(resident_table), _sha256(resident_table))
        != (ARCHIVE_TABLE_SIZE, SOURCE_RESIDENT_TABLE_SHA256)
        or _diff_triplets(resident_table, old_table) != RESIDENT_VS_OLD_MEDIA_DIFFS
        or script != old_script
        or payload.count(script) != 1
        or payload.find(script) != EXPECTED_SCRIPT_PAYLOAD_OFFSET
        or (len(dialogue), _sha256(dialogue)) != (DIALOGUE_SIZE, DIALOGUE_SHA256)
        or payload.count(dialogue) != 1
        or payload.find(dialogue) != EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        or (len(loaded_header), _sha256(loaded_header))
        != (OLD_HEADER_SIZE, SOURCE_LOADED_HEADER_SHA256)
        or loaded_header != old_header
        or payload.count(loaded_header) != 1
        or payload.find(loaded_header) != EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET
        or _sha256(
            payload[
                EXPECTED_SCRIPT_PAYLOAD_OFFSET + OLD_SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET
            ]
        )
        != SCRIPT_GAP_SHA256
        or _sha256(
            payload[
                EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET
            ]
        )
        != DIALOGUE_GAP_SHA256
    ):
        raise SurfaceSlotMigrationError("Resident field-550 component/table/gap identity drifted")
    _validate_walkmesh(walkmesh)

    actor_array_pointer = struct.unpack_from("<I", ram, FIELD_ACTORS)[0]
    if (
        (struct.unpack_from("<I", ram, GAME_SCENE_MAP)[0] & 0xFFF) != EXPECTED_FIELD
        or struct.unpack_from("<I", ram, FIELD_NUM_ACTORS)[0] != EXPECTED_ACTOR_COUNT
        or actor_array_pointer != EXPECTED_ACTOR_ARRAY_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0]
        != EXPECTED_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA)[0]
        != EXPECTED_VM_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_ACTOR)[0]
        != EXPECTED_VM_ACTOR_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_CUR_DIALOGUE_FILE)[0]
        != EXPECTED_DIALOGUE_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SMALL_COMPONENT)[0]
        != EXPECTED_SMALL_COMPONENT_POINTER
    ):
        raise SurfaceSlotMigrationError("Live field-550 pointer topology drifted")
    actor_base = actor_array_pointer & 0x1FFFFFFF
    actor_array = ram[actor_base : actor_base + ACTOR_ARRAY_SIZE]
    actor_records: list[bytes] = []
    actor_data: list[bytes] = []
    actor_data_offsets: list[int] = []
    for entity in range(SCRIPT_ENTITY_COUNT):
        record_offset = actor_base + entity * FIELD_ACTOR_STRIDE
        data_offset = _actor_data_offset(ram, actor_base, entity)
        actor_records.append(bytes(ram[record_offset : record_offset + FIELD_ACTOR_STRIDE]))
        actor_data.append(bytes(ram[data_offset : data_offset + ACTOR_DATA_SIZE]))
        actor_data_offsets.append(data_offset)
    if (
        _sha256(actor_array) != SOURCE_ACTOR_ARRAY_SHA256
        or _sha256(b"".join(actor_data)) != SOURCE_ACTOR_DATA_SHA256
        or actor_base + SEAL_ENTITY * FIELD_ACTOR_STRIDE != E19_RECORD_RAM_OFFSET
        or actor_data_offsets[SEAL_ENTITY] != E19_ACTOR_DATA_RAM_OFFSET
        or _sha256(actor_records[SEAL_ENTITY]) != SOURCE_E19_RECORD_SHA256
        or _sha256(actor_data[SEAL_ENTITY]) != SOURCE_E19_ACTOR_DATA_SHA256
    ):
        raise SurfaceSlotMigrationError("Live field-550 actor allocation identity drifted")

    controller = actor_data_offsets[CONTROLLER_ENTITY]
    fei = actor_data_offsets[FEI_ENTITY]
    cross = actor_data_offsets[CROSS_CARRIER_ENTITY]
    leaf = actor_data_offsets[DOOR_LEAF_ENTITY]
    seal = actor_data_offsets[SEAL_ENTITY]
    fei_position = struct.unpack_from("<3i", ram, fei + ACTOR_DATA_POSITION_OFFSET)
    cross_position = struct.unpack_from("<3i", ram, cross + ACTOR_DATA_POSITION_OFFSET)
    cross_bounds = struct.unpack_from("<4H", ram, cross + ACTOR_DATA_BOUNDS_OFFSET)
    if (
        fei_position != EXPECTED_FEI_POSITION
        or struct.unpack_from("<4H", ram, fei + ACTOR_DATA_SURFACES_OFFSET)
        != EXPECTED_FEI_TRIANGLES
        or (struct.unpack_from("<H", ram, fei + ACTOR_FACING_OFFSET)[0] & 0xFFF)
        != EXPECTED_FEI_FACING
        or ram[fei + ACTOR_CURRENT_PC_OFFSET : fei + ACTOR_CURRENT_PC_OFFSET + 4]
        != EXPECTED_FEI_CURRENT
        or ram[
            controller + ACTOR_CURRENT_PC_OFFSET : controller + ACTOR_CURRENT_PC_OFFSET + 4
        ]
        != EXPECTED_CONTROLLER_CURRENT
        or cross_position != (0, 0, 250 << 16)
        or cross_bounds != (48, 60, 32, 16)
        or not (struct.unpack_from("<I", ram, cross + ACTOR_DATA_FLAGS_OFFSET)[0] & 0x80)
        or not (-64 <= fei_position[0] // 65_536 <= 64)
        or fei_position[2] // 65_536 != 228
    ):
        raise SurfaceSlotMigrationError("Fei/controller/door-carrier saved stance drifted")
    leaf_record = actor_base + DOOR_LEAF_ENTITY * FIELD_ACTOR_STRIDE
    if (
        ram[leaf + ACTOR_CURRENT_PC_OFFSET : leaf + ACTOR_CURRENT_PC_OFFSET + 4]
        != EXPECTED_LEAF_CURRENT
        or ram[leaf_record + 0x0C : leaf_record + 0x1E] != CLOSED_LEAF_MATRIX
        or ram[leaf_record + 0x2C : leaf_record + 0x3E] != CLOSED_LEAF_MATRIX
    ):
        raise SurfaceSlotMigrationError("Native e18 door leaf is not closed")
    if (
        ram[E19_RECORD_RAM_OFFSET + 0x28 : E19_RECORD_RAM_OFFSET + 0x2C]
        != OLD_E19_RECORD_Z
        or ram[E19_RECORD_RAM_OFFSET + 0x48 : E19_RECORD_RAM_OFFSET + 0x4C]
        != OLD_E19_RECORD_Z
        or ram[seal : seal + 4] != OLD_E19_FLAGS
        or ram[seal + ACTOR_DATA_BOUNDS_OFFSET : seal + ACTOR_DATA_BOUNDS_OFFSET + 8]
        != OLD_E19_BOUNDS
        or ram[seal + ACTOR_DATA_POSITION_OFFSET : seal + ACTOR_DATA_POSITION_OFFSET + 12]
        != OLD_E19_CURRENT_POSITION
        or ram[seal + ACTOR_DATA_OLD_POSITION_OFFSET : seal + ACTOR_DATA_OLD_POSITION_OFFSET + 8]
        != OLD_E19_OLD_POSITION
        or ram[seal + ACTOR_CURRENT_PC_OFFSET : seal + ACTOR_CURRENT_PC_OFFSET + 4]
        != EXPECTED_SEAL_CURRENT
        or struct.unpack_from("<I", ram, seal)[0] & 0x2000
    ):
        raise SurfaceSlotMigrationError("Active e19 circular-seal runtime drifted")

    gamestate = ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE]
    field_bank = ram[FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE]
    backup_bank = ram[
        GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET :
        GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET + FIELD_VARIABLE_BANK_SIZE
    ]
    windows = ram[DIALOG_WINDOWS : DIALOG_WINDOWS + DIALOG_WINDOWS_SIZE]
    if (
        _sha256(gamestate) != EXPECTED_GAMESTATE_SHA256
        or field_bank != backup_bank
        or _sha256(field_bank) != EXPECTED_FIELD_VARIABLE_BANK_SHA256
        or struct.unpack_from("<H", field_bank, APPOINTMENT_OPERAND)[0]
        != EXPECTED_APPOINTMENT_WORD
        or struct.unpack_from("<H", field_bank, STATE_OPERAND)[0] != EXPECTED_STATE_WORD
        or _sha256(_camera_snapshot(ram)) != EXPECTED_CAMERA_SHA256
        or _sha256(windows) != EXPECTED_DIALOG_WINDOWS_SHA256
        or any(
            struct.unpack_from(
                "<h",
                ram,
                DIALOG_WINDOWS
                + index * DIALOG_WINDOW_STRIDE
                + DIALOG_WINDOW_STATUS_OFFSET,
            )[0]
            != -1
            for index in range(4)
        )
    ):
        raise SurfaceSlotMigrationError("GameState/field/camera/window identity drifted")
    return {
        "ram_offset": ram_offset,
        "ram": ram,
        "script": script,
        "dialogue": dialogue,
        "walkmesh": walkmesh,
        "loaded_header": loaded_header,
        "actor_base": actor_base,
        "actor_array": actor_array,
        "actor_records": tuple(actor_records),
        "actor_data": tuple(actor_data),
        "actor_data_offsets": tuple(actor_data_offsets),
        "gamestate": gamestate,
        "field_bank": field_bank,
        "camera": _camera_snapshot(ram),
        "windows": windows,
    }


def migrate_v224_slot1_to_v225(
    state: bytes,
    *,
    old_disc: Path,
    new_disc: Path,
    old_header: bytes,
    new_header: bytes,
    old_script: bytes,
    new_script: bytes,
    zstd: _ZstdLike,
) -> tuple[bytes, dict[str, object]]:
    source_sha = _sha256(state)
    if (len(state), source_sha) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise SurfaceSlotMigrationError(
            f"Source Slot 1 identity is {len(state)} / {source_sha}, expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    old_name, new_name = OLD_CUE_NAME.encode("ascii"), NEW_CUE_NAME.encode("ascii")
    if len(old_name) != len(new_name) or state.count(old_name) != 1 or state.count(new_name):
        raise SurfaceSlotMigrationError("Source CUE identity drifted")

    old_table, new_table = _validate_resources(
        old_disc,
        new_disc,
        old_header,
        new_header,
        old_script,
        new_script,
    )
    source_payload, frame_start, source_prefix = _unpack_state(state, zstd)
    if (
        frame_start != SOURCE_PREFIX_SIZE
        or len(state) - frame_start != SOURCE_COMPRESSED_SIZE
        or _sha256(state[frame_start:]) != SOURCE_COMPRESSED_SHA256
        or _sha256(source_prefix) != SOURCE_PREFIX_SHA256
    ):
        raise SurfaceSlotMigrationError("Source frame/prefix identity drifted")
    snapshots = _validate_source(source_payload, old_table, old_header, old_script)

    resident_script = _patch_reconstruction(snapshots["script"], _script_patches())
    if resident_script != new_script:
        raise SurfaceSlotMigrationError("Resident V225 script reconstruction drifted")
    loaded_header = bytearray(snapshots["loaded_header"])
    if loaded_header[HEADER_E19_Z_OFFSET : HEADER_E19_Z_OFFSET + 2] != b"\xFA\x00":
        raise SurfaceSlotMigrationError("Loaded-header e19 source position drifted")
    loaded_header[HEADER_E19_Z_OFFSET : HEADER_E19_Z_OFFSET + 2] = b"\x0A\x01"
    loaded_header_bytes = bytes(loaded_header)
    if (
        _sha256(loaded_header_bytes) != OUTPUT_LOADED_HEADER_SHA256
        or _diff_triplets(snapshots["loaded_header"], loaded_header_bytes)
        != HEADER_DIFFS[-2:]
        or _diff_triplets(loaded_header_bytes, new_header) != HEADER_DIFFS[:3]
    ):
        raise SurfaceSlotMigrationError("Loaded-header e19-only reconstruction drifted")

    final = bytearray(source_payload)
    categories: dict[str, set[int]] = {
        "archive_table": set(),
        "resident_script": set(),
        "loaded_header": set(),
        "runtime_e19": set(),
    }

    def install(
        offset: int,
        old: bytes,
        new: bytes,
        category: str,
        label: str,
    ) -> None:
        if len(old) != len(new) or final[offset : offset + len(old)] != old:
            raise SurfaceSlotMigrationError(f"Patch source drifted: {label}")
        categories[category].update(
            offset + index
            for index, (before, after) in enumerate(zip(old, new, strict=True))
            if before != after
        )
        final[offset : offset + len(new)] = new

    for relative, old, new in RESIDENT_ARCHIVE_TABLE_PATCHES:
        install(
            EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + relative,
            bytes((old,)),
            bytes((new,)),
            "archive_table",
            f"archive table 0x{relative:04X}",
        )
    install(
        EXPECTED_SCRIPT_PAYLOAD_OFFSET,
        snapshots["script"],
        resident_script,
        "resident_script",
        "resident field-550 ATEL",
    )
    install(
        EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET,
        snapshots["loaded_header"],
        loaded_header_bytes,
        "loaded_header",
        "loaded field-550 e19 header record",
    )
    ram_offset = int(snapshots["ram_offset"])
    for relative, old, new, label in RUNTIME_PATCHES:
        install(ram_offset + relative, old, new, "runtime_e19", label)
    final_payload = bytes(final)

    expected_counts = {
        "archive_table": EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED,
        "resident_script": EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED,
        "loaded_header": EXPECTED_LOADED_HEADER_BYTES_CHANGED,
        "runtime_e19": EXPECTED_RUNTIME_BYTES_CHANGED,
    }
    expected_offsets = frozenset().union(*categories.values())
    actual_offsets = frozenset(_diff_offsets(source_payload, final_payload))
    if (
        {key: len(value) for key, value in categories.items()} != expected_counts
        or actual_offsets != expected_offsets
        or len(actual_offsets) != EXPECTED_PAYLOAD_BYTES_CHANGED
        or _sha256(final_payload) != OUTPUT_PAYLOAD_SHA256
    ):
        raise SurfaceSlotMigrationError("Migration changed bytes outside the exact 87-byte whitelist")

    output_table = final_payload[
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
    ]
    if (
        _sha256(output_table) != OUTPUT_RESIDENT_TABLE_SHA256
        or _diff_triplets(output_table, new_table) != RESIDENT_VS_NEW_MEDIA_DIFFS
    ):
        raise SurfaceSlotMigrationError("V225 resident archive-table reconstruction drifted")
    if (
        final_payload[
            EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + NEW_SCRIPT_SIZE
        ]
        != new_script
        or final_payload[
            EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET :
            EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET + NEW_HEADER_SIZE
        ]
        != loaded_header_bytes
    ):
        raise SurfaceSlotMigrationError("V225 resident field-550 resources were not installed")

    result_ram_offset, result_ram = _ram_from_payload(final_payload)
    source_ram = snapshots["ram"]
    if result_ram_offset != ram_offset or _sha256(result_ram) != OUTPUT_RAM_SHA256:
        raise SurfaceSlotMigrationError("Final V225 serialized RAM identity drifted")
    actor_base = int(snapshots["actor_base"])
    actor_data_offsets = tuple(snapshots["actor_data_offsets"])
    source_records = tuple(snapshots["actor_records"])
    source_actor_data = tuple(snapshots["actor_data"])
    if (
        _sha256(result_ram[actor_base : actor_base + ACTOR_ARRAY_SIZE])
        != OUTPUT_ACTOR_ARRAY_SHA256
        or _sha256(
            b"".join(
                result_ram[offset : offset + ACTOR_DATA_SIZE]
                for offset in actor_data_offsets
            )
        )
        != OUTPUT_ACTOR_DATA_SHA256
    ):
        raise SurfaceSlotMigrationError("Final field-550 actor allocation identity drifted")
    for entity in range(SCRIPT_ENTITY_COUNT):
        record_offset = actor_base + entity * FIELD_ACTOR_STRIDE
        data_offset = actor_data_offsets[entity]
        result_record = result_ram[record_offset : record_offset + FIELD_ACTOR_STRIDE]
        result_data = result_ram[data_offset : data_offset + ACTOR_DATA_SIZE]
        if entity == SEAL_ENTITY:
            if (
                _sha256(result_record) != OUTPUT_E19_RECORD_SHA256
                or _sha256(result_data) != OUTPUT_E19_ACTOR_DATA_SHA256
                or not (struct.unpack_from("<I", result_data)[0] & 0x2000)
            ):
                raise SurfaceSlotMigrationError("V225 e19 rectangle runtime drifted")
        elif result_record != source_records[entity] or result_data != source_actor_data[entity]:
            raise SurfaceSlotMigrationError(f"Unrelated field runtime e{entity} changed")

    preserved_spans = (
        (GAME_STATE, GAMESTATE_SIZE, "GameState/party"),
        (FIELD_SCRIPT_MEMORY, FIELD_VARIABLE_BANK_SIZE, "active field variables"),
        (DIALOG_WINDOWS, DIALOG_WINDOWS_SIZE, "dialogue windows"),
    )
    for start, size, label in preserved_spans:
        if result_ram[start : start + size] != source_ram[start : start + size]:
            raise SurfaceSlotMigrationError(f"{label} was not preserved")
    if _camera_snapshot(result_ram) != snapshots["camera"]:
        raise SurfaceSlotMigrationError("Camera was not preserved")
    if (
        final_payload[
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET : EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE
        ]
        != snapshots["dialogue"]
        or final_payload[
            EXPECTED_WALKMESH_PAYLOAD_OFFSET : EXPECTED_WALKMESH_PAYLOAD_OFFSET + WALKMESH_SIZE
        ]
        != snapshots["walkmesh"]
        or final_payload[
            EXPECTED_SCRIPT_PAYLOAD_OFFSET + NEW_SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        ]
        != source_payload[
            EXPECTED_SCRIPT_PAYLOAD_OFFSET + OLD_SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        ]
        or final_payload[
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET
        ]
        != source_payload[
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET
        ]
    ):
        raise SurfaceSlotMigrationError("Allocator/component neighbors changed")

    provisional_prefix = _expected_prefix(
        source_prefix,
        compressed_size=OUTPUT_COMPRESSED_SIZE,
    )
    if (
        len(_diff_offsets(source_prefix, provisional_prefix)) != EXPECTED_PREFIX_BYTES_CHANGED
        or _sha256(provisional_prefix) != OUTPUT_PREFIX_SHA256
    ):
        raise SurfaceSlotMigrationError("V225 media-prefix reconstruction drifted")
    result = _pack_state(provisional_prefix, final_payload, zstd)
    verified_payload, verified_frame, verified_prefix = _unpack_state(result, zstd)
    if (
        verified_payload != final_payload
        or verified_frame != SOURCE_PREFIX_SIZE
        or verified_prefix != provisional_prefix
        or len(result) - verified_frame != OUTPUT_COMPRESSED_SIZE
        or _sha256(result[verified_frame:]) != OUTPUT_COMPRESSED_SHA256
        or result.count(old_name) != 0
        or result.count(new_name) != 1
        or (len(result), _sha256(result)) != (OUTPUT_STATE_SIZE, OUTPUT_STATE_SHA256)
    ):
        raise SurfaceSlotMigrationError("Final V225 state identity or round trip drifted")

    report: dict[str, object] = {
        "source_sha256": SOURCE_STATE_SHA256,
        "output_sha256": OUTPUT_STATE_SHA256,
        "source_size": len(state),
        "output_size": len(result),
        "field": EXPECTED_FIELD,
        "payload_size": len(final_payload),
        "payload_sha256": OUTPUT_PAYLOAD_SHA256,
        "payload_bytes_changed": len(actual_offsets),
        "archive_table_bytes_changed": len(categories["archive_table"]),
        "resident_script_bytes_changed": len(categories["resident_script"]),
        "loaded_header_bytes_changed": len(categories["loaded_header"]),
        "runtime_e19_bytes_changed": len(categories["runtime_e19"]),
        "resident_script_size": len(resident_script),
        "resident_script_capacity": SCRIPT_ALLOCATED_CAPACITY,
        "forward_poll_pc": f"0x{FORWARD_POLL_PC:04X}",
        "forward_poll_minimum_z": 228,
        "forward_poll_debounced": True,
        "native_cross_action_pc": f"0x{NATIVE_EXIT_GATE_PC:04X}",
        "e19_seal": "rectangle x=0 z=266 OP18=24/8 physical_half_spans=48/16",
        "resident_archive_table_sha256": OUTPUT_RESIDENT_TABLE_SHA256,
        "resident_archive_nonvolatile_field621_entry_normalized": True,
        "resident_archive_volatile_tail_preserved": True,
        "resident_archive_table_policy": (
            "apply the five V224-to-V225 media deltas, normalize field-621 "
            "FAT entry 0x3268 E8-to-E0, and preserve volatile 0x7FFF=E0"
        ),
        "loaded_header_sha256": OUTPUT_LOADED_HEADER_SHA256,
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "walkmesh_preserved": True,
        "field_variables_preserved": True,
        "native_cross_action_preserved": True,
        "closed_leaf_preserved": True,
        "controller_runtime_preserved": True,
        "doctor_security_runtime_preserved": True,
        "gamestate_party_camera_windows_preserved": True,
        "allocator_safe": True,
        "round_trip_verified": True,
    }
    return result, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=SOURCE_BACKUP,
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
        "--old-header",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "surface_soylent_campaign_v224_stage"
            / "clones"
            / "field_550_disc1_donor"
            / "header.bin"
        ),
    )
    parser.add_argument(
        "--new-header",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "surface_soylent_campaign_v225_stage"
            / "clones"
            / "field_550_disc1_donor"
            / "header.bin"
        ),
    )
    parser.add_argument(
        "--old-script",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "surface_soylent_campaign_v224_stage"
            / "clones"
            / "field_550_disc1_donor"
            / "05_scripts.bin"
        ),
    )
    parser.add_argument(
        "--new-script",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "surface_soylent_campaign_v225_stage"
            / "clones"
            / "field_550_disc1_donor"
            / "05_scripts.bin"
        ),
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
            / "SLUS-00669_1_v225_from_6df7129d_field550_clearance.sav"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "save_candidates"
            / "SLUS-00669_1_v225_from_6df7129d_field550_clearance.json"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        output = args.output.resolve()
        report_path = args.report.resolve()
        if output == LIVE_SLOT1 or report_path == LIVE_SLOT1:
            raise SurfaceSlotMigrationError("Output/report may not be the live Slot 1")
        if output == args.source.resolve():
            raise SurfaceSlotMigrationError("Output may not replace the source state")
        source = args.source.read_bytes()
        zstd = media_migration._Zstd(args.zstd)
        result, report = migrate_v224_slot1_to_v225(
            source,
            old_disc=args.old_disc,
            new_disc=args.new_disc,
            old_header=args.old_header.read_bytes(),
            new_header=args.new_header.read_bytes(),
            old_script=args.old_script.read_bytes(),
            new_script=args.new_script.read_bytes(),
            zstd=zstd,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, SurfaceSlotMigrationError, media_migration.StateMigrationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote V225 candidate: {output}")
    print(f"Wrote migration report: {report_path}")
    print(f"SHA-256: {report['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
