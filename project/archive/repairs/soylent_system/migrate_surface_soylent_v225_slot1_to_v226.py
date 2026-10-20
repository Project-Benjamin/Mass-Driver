#!/usr/bin/env python3
"""Migrate the exact V225 field-592 Slot 1 state to V226 safely.

The pinned V225 state was saved while field 592's controller e0 was executing
the retired automatic forward-door poll at PC 0x048A.  V226 removes that poll:
e0:s1 points back to the shared STOP at 0x068C, the complete 0x044E..0x04A5
retail cavity is restored, and only the native e17:s2 X action opens the door.

This helper is deliberately fail-closed.  It accepts one exact source state,
pins the V225/V226 media, V226 stage manifest, and both field-592 header/script
pairs, and changes only four resident archive-table bytes, 62 equal-size ATEL
bytes, and the two-byte PC in each of e0's active-slot/current-PC fields.  The
loaded header, walkmesh, all actor records, e1..e20 ActorData (including Fei and
the e17/e18/e20 carrier/leaf/rectangle), GameState, party, field variables,
camera, and windows are preserved byte-for-byte.  The CLI never writes the
live DuckStation Slot 1; it emits only a separate candidate and JSON report.
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
    / "SLUS-00669_1_v225_auto_open_408a5dc9.sav"
).resolve()

SOURCE_STATE_SIZE = 1_855_939
SOURCE_STATE_SHA256 = "408a5dc96f5a2633079f8a41b09eefe669400b71a455bd5312fa9e0fc6cb22b9"
SOURCE_PREFIX_SIZE = 0xB098
SOURCE_PREFIX_SHA256 = "638bf31efaec950191950802931422eaa18bd87ffef83fa742e4bf02e5e59486"
SOURCE_COMPRESSED_SIZE = 1_810_731
SOURCE_COMPRESSED_SHA256 = "c212a89fd64d2e4c438be400e8d096408c88f24b3abfe9bd9534911810dbd0e0"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "f27cb51ea6b06b4de410c702f3285e2ceba295f6384158a1aed5d4093522264a"
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
SOURCE_RAM_SHA256 = "66c41c1cde25e0c0e0868f9a0851a634128f7263da89e4d2aef795d63209fd66"

OUTPUT_STATE_SIZE = 1_680_239
OUTPUT_STATE_SHA256 = "a3aa3752e1b4b035b1f05f7cc0495bc4d4acd61f988923401e3ee8e30876e7bb"
OUTPUT_PREFIX_SHA256 = "a05e58a25444e27d2afb101b53f359d7a7ff3b07049d8a344d4e598b9c36098f"
OUTPUT_COMPRESSED_SIZE = 1_635_031
OUTPUT_COMPRESSED_SHA256 = "d8e3cadf0ac9bbb80026c306c41212b8151147b4773127862ed5e8769000ef6f"
OUTPUT_PAYLOAD_SHA256 = "3a256a7d4632d79fedd13488d1e7b95fecb038490f1cd1496e7db4abe25602cb"
OUTPUT_RAM_SHA256 = "4a52a6df97f29cb9eb7a4aadbb48c86962bb08d0600853b9f81186f2fbf903bf"

OLD_DISC_SIZE = NEW_DISC_SIZE = 698_642_784
OLD_DISC_SHA256 = "539e2e33266d71337666c84d9d3a153dfd7555d8db933efadc49376483e6e1ff"
NEW_DISC_SHA256 = "8a916111d1557c98c904ed95431d973a0d460aa71b52fc3eba56093e9127dda6"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v225.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v226.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = "6a289550cec7003e9742d75f862db41d37214afe499d0dcddab1892839f6b8fd"
NEW_CUE_SHA256 = "ee95f0b73bf490e5718b6b3023366f03e385008a46f681c19b7f142ad4cbbcee"

V226_STAGE_MANIFEST_SIZE = 119_802
V226_STAGE_MANIFEST_SHA256 = "8c223274a187197e74b06f94edccd74ce7e33b287c3afbed87a6ce471f621f74"
V226_FIELD_BUNDLE_CANONICAL_ID = 1790
V226_FIELD_BUNDLE_SIZE = 83_668
V226_FIELD_BUNDLE_SHA256 = "6d3fcc81be8d99f806e56e1d2c33902c8eef0ea05ea9cf431217b8ff64ae41cd"

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = "e89e07218cfd6843357d7480d427bd9c4cc27b53792ed83ddebbb485de2fc875"
NEW_ARCHIVE_TABLE_SHA256 = "a6505ea96cd9c20b16bfb45e67f34a5b932795f569ec04b7f44d4bf815c2937c"
ARCHIVE_TABLE_DIFFS = (
    (0x2F74, 0x40, 0x38),
    (0x30C4, 0xC0, 0xBC),
    (0x30D2, 0xD8, 0xD4),
    (0x30E0, 0x98, 0x94),
)
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
SOURCE_RESIDENT_TABLE_SHA256 = "337607d4873dcc0f5c2eee5cd69f7d61f130badb074b3441e09a60cd0e801eb9"
OUTPUT_RESIDENT_TABLE_SHA256 = "3ee67d330d7a2c4b2bbdd8188dfa38a4a0152bea3950be3276d40a6ce8862a47"
RESIDENT_VS_MEDIA_DIFFS = ((0x7FFF, 0xE0, 0x00),)

OLD_HEADER_SIZE = NEW_HEADER_SIZE = 960
OLD_HEADER_SHA256 = "09e170c43a7285fbbc84a907cde6a0d7cbacc1ab59cabee3441901e3ae46e1a4"
NEW_HEADER_SHA256 = "b022a0fa84bf4d0911a43cd29131227b706adb0ce7c77395df82241426659648"
HEADER_DIFFS = (
    (0x0148, 0x14, 0x10),
    (0x014C, 0xB0, 0xAC),
    (0x0150, 0xD4, 0xD0),
)
EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET = 0x1D8826

OLD_SCRIPT_SIZE = NEW_SCRIPT_SIZE = 3_345
OLD_SCRIPT_SHA256 = "a7c256ca386a1dddb0a6e26fa65e59bef268b20d0a938ab69f870ca974c88896"
NEW_SCRIPT_SHA256 = "6aa5e7fd9d2e212cb0c14a3c9a3872f4ab1367f7c4983b63f82751e1a731b2f8"
EXPECTED_SCRIPT_PAYLOAD_OFFSET = 0x10CD56
EXPECTED_SCRIPT_GUEST_POINTER = 0x8010B2F4
EXPECTED_VM_SCRIPT_GUEST_POINTER = 0x8010B8B8
SCRIPT_ALLOCATED_CAPACITY = 3_396
SCRIPT_GAP_SIZE = 51
SCRIPT_GAP_SHA256 = "291eb5f88551f6ed544e74d8bf278890de6138fb9bcdecc8b234d81d09eb6d76"
NORMAL_BYTECODE_OFFSET = 0x5C4
NORMAL_BYTECODE_SIZE = 0x74D
AUTO_POLL_PC = 0x044E
AUTO_POLL_CURRENT_PC = 0x048A
AUTO_POLL_CAVITY_END_PC = 0x04A5
SHARED_STOP_PC = 0x068C
NATIVE_X_ACTION_PC = 0x0735
AUTO_POLL_CAVITY = bytes.fromhex(
    "2D FF F8 07 FA 07 FC 07 02 F8 07 C0 FF 44 87 04 02 F8 07 41 00 43 87 04 "
    "02 FA 07 E4 00 44 87 04 09 11 22 2D FF F8 07 FA 07 FC 07 02 FA 07 E4 "
    "00 44 4E 04 26 00 80 01 71 04 26 00 80 01 4E 04 FF C7 FE 24 26 04 80 "
    "FE AA FF 35 E0 00 00 00 40 FE 53 2C 00 69 06 80 00"
)
X_ONLY_CAVITY = bytes.fromhex(
    "21 30 81 4A 5A 00 3E 00 C0 4A 5A 00 C8 FF C0 69 06 80 26 0A 80 2C 04 FE "
    "0D 01 80 D2 24 00 00 9C 09 FF C5 26 0A 80 2C 00 D2 25 00 00 9C 09 FE "
    "C6 26 0A 80 69 00 80 26 05 80 D2 26 00 00 9C 09 FF C7 FE 24 26 04 80 "
    "FE AA FF 35 E0 00 00 00 40 FE 53 2C 00 69 06 80 00"
)

EXPECTED_DIALOGUE_PAYLOAD_OFFSET = 0x10DA9A
EXPECTED_DIALOGUE_GUEST_POINTER = 0x8010C038
EXPECTED_SMALL_COMPONENT_POINTER = 0x8010C020
DIALOGUE_SIZE = 5_291
DIALOGUE_SHA256 = "dbe8426e776cd719c61c9630e59e587e65c4f76ca51326c9069925421a2a8c70"
DIALOGUE_GAP_SIZE = 25
DIALOGUE_GAP_SHA256 = "1f0a239888c8222f300e43c531f481992de3a11cb39a19d171c8384477760f7a"
EXPECTED_WALKMESH_PAYLOAD_OFFSET = 0x10EF5E
WALKMESH_SIZE = 1_948
WALKMESH_SHA256 = "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d8cca4238393571df"

FIELD_CUR_DIALOGUE_FILE = 0x0ADBF0
FIELD_SMALL_COMPONENT = 0x0ADBF4
GAME_SCENE_MAP = 0x04F34C
EXPECTED_FIELD = 592
EXPECTED_ACTOR_COUNT = 35
SCRIPT_ENTITY_COUNT = 21
EXPECTED_ACTOR_ARRAY_GUEST_POINTER = 0x80112CCC
EXPECTED_VM_ACTOR_GUEST_POINTER = 0x80115C4C
ACTOR_ARRAY_SIZE = EXPECTED_ACTOR_COUNT * FIELD_ACTOR_STRIDE
ACTOR_DATA_SIZE = 0x138
EXPECTED_ACTOR_DATA_OFFSETS = (
    0x113968, 0x113B20, 0x113CD8, 0x113E90, 0x114048, 0x114200, 0x1143B8,
    0x114570, 0x114728, 0x1148E0, 0x114A98, 0x114C50, 0x114E08, 0x114FC0,
    0x115178, 0x115330, 0x1154E8, 0x1156A0, 0x1158DC, 0x115A94, 0x115C4C,
)
SOURCE_ACTOR_ARRAY_SHA256 = "110d1a22e71fe37d0fc286d6a8221ae1f302a1c5414c0340c0f1fa250c24901d"
SOURCE_ACTOR_DATA_SHA256 = "a8c26a422f8c517e0424b9d231fa69a94701ec0b95167b13c15e936139664697"
OUTPUT_ACTOR_DATA_SHA256 = "ddf6783c4b8adc6eab5830ad53e6a524e4e1afebaf156a55b55dc6b51054c8d2"

ACTOR_DATA_FLAGS_OFFSET = 0x00
ACTOR_DATA_SURFACES_OFFSET = 0x08
ACTOR_DATA_BOUNDS_OFFSET = 0x18
ACTOR_DATA_POSITION_OFFSET = 0x20
ACTOR_SCRIPT_SLOT_OFFSET = 0x8C
ACTOR_CURRENT_PC_OFFSET = 0xCC
ACTOR_FACING_OFFSET = 0x106
CONTROLLER_ENTITY = 0
FEI_ENTITY = 1
CROSS_CARRIER_ENTITY = 17
DOOR_LEAF_ENTITY = 18
TERMINAL_ENTITY = 19
RECTANGLE_ENTITY = 20
EXPECTED_FEI_POSITION = (0, 0, 14_745_200)
EXPECTED_FEI_SURFACES = (16, 0, 0, 0)
EXPECTED_FEI_FACING = 0x0C00
EXPECTED_FEI_CURRENT = bytes.fromhex("5F 01 00 00")
CLOSED_LEAF_MATRIX = bytes.fromhex(
    "00 00 00 00 00 10 00 00 00 10 00 00 00 F0 00 00 00 00"
)
SOURCE_E0_RECORD_SHA256 = "bec05cc830aee7f5af972250dd52323985ab8948a1d3cfd88a625c1a28839046"
SOURCE_E0_DATA_SHA256 = "fbc9e7c91a991817d0ecb87d6be3135577a88eba91215a346e0df8e1b47cf19c"
OUTPUT_E0_DATA_SHA256 = "93406788e6f4ddcd293ea54538b35bc2c967d78dfd3ab879e2f928d2272fdd94"
SOURCE_E17_RECORD_SHA256 = "229bd099c821adf063bbefbe9b41656c260a024be6ceb457536c1ef7a777558b"
SOURCE_E17_DATA_SHA256 = "37dababcd029d7a8e4ad3d23d76271cd05e495f868af06853e7aea2e30f97659"
SOURCE_E18_RECORD_SHA256 = "c579e2a6d00cf23464a0e2c3283f543cacf749f1384cd482a1df18d842309da1"
SOURCE_E18_DATA_SHA256 = "e87291e1da474db45af87451d6a9f33fa4603b836b37e7f6181acabf6c06e753"
SOURCE_E20_RECORD_SHA256 = "5731b2ce57d5c892d532d7f8591580d42607fb65ce2a5c062de52530f468c0d6"
SOURCE_E20_DATA_SHA256 = "70c251c41ef5933ba0c3f506bbeaee9723e7cf58aaafba55921b3e71bac64fc0"

RUNTIME_PATCHES = (
    (
        EXPECTED_ACTOR_DATA_OFFSETS[0] + ACTOR_SCRIPT_SLOT_OFFSET,
        bytes.fromhex("8A 04"),
        bytes.fromhex("8C 06"),
        "e0 active-slot IP",
    ),
    (
        EXPECTED_ACTOR_DATA_OFFSETS[0] + ACTOR_CURRENT_PC_OFFSET,
        bytes.fromhex("8A 04"),
        bytes.fromhex("8C 06"),
        "e0 current PC",
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
EXPECTED_GAMESTATE_SHA256 = "189d5bb39b22ab317e94ee16f45530b944ae856a86161dc08a9cffaba1c673ec"
EXPECTED_FIELD_VARIABLE_BANK_SHA256 = "8958eb8c2be0b7a20d497cb91a32c1118d86a35ba38f3674b7fca1cbd403f4f4"
EXPECTED_CAMERA_SHA256 = "00e40052201e0961516b2cba27d4f729aae6ddf6e5b75491fe10041d7e3df2c8"
EXPECTED_DIALOG_WINDOWS_SHA256 = "8b8d2743404ca97d8690ccdd1bcd59d997da9fd3f9a00a6800a465274d3e3eef"

EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED = 4
EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED = 62
EXPECTED_RUNTIME_E0_BYTES_CHANGED = 4
EXPECTED_PAYLOAD_BYTES_CHANGED = 70
EXPECTED_PREFIX_BYTES_CHANGED = 4


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output whenever the pinned V225/V226 contract drifts."""


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
    expected = bytearray(source_prefix.replace(OLD_CUE_NAME.encode("ascii"), NEW_CUE_NAME.encode("ascii")))
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


def _patch_reconstruction(source: bytes, patches: Sequence[tuple[int, bytes, bytes]]) -> bytes:
    result = bytearray(source)
    for offset, old, new in patches:
        if len(old) != len(new) or result[offset : offset + len(old)] != old:
            raise SurfaceSlotMigrationError(f"Patch source drifted at 0x{offset:X}")
        result[offset : offset + len(new)] = new
    return bytes(result)


def _script_patches() -> tuple[tuple[int, bytes, bytes], ...]:
    return (
        (0x0086, struct.pack("<H", AUTO_POLL_PC), struct.pack("<H", SHARED_STOP_PC)),
        (NORMAL_BYTECODE_OFFSET + AUTO_POLL_PC, AUTO_POLL_CAVITY, X_ONLY_CAVITY),
    )


def _validate_file(path: Path, size: int, sha256: str, label: str) -> None:
    if not path.is_file() or path.stat().st_size != size or _file_sha256(path) != sha256:
        raise SurfaceSlotMigrationError(f"{label} identity drifted")


def _validate_resources(
    old_disc: Path,
    new_disc: Path,
    stage_manifest: bytes,
    old_header: bytes,
    new_header: bytes,
    old_script: bytes,
    new_script: bytes,
) -> tuple[bytes, bytes]:
    for path, size, sha256, label in (
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V225 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V226 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V225 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V226 CUE"),
    ):
        _validate_file(path, size, sha256, label)
    if (len(stage_manifest), _sha256(stage_manifest)) != (V226_STAGE_MANIFEST_SIZE, V226_STAGE_MANIFEST_SHA256):
        raise SurfaceSlotMigrationError("V226 stage manifest identity drifted")
    try:
        inventory = json.loads(stage_manifest)["replacement_inventory"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise SurfaceSlotMigrationError("V226 stage manifest structure drifted") from exc
    field_bundle = next((item for item in inventory if item.get("canonical_id") == V226_FIELD_BUNDLE_CANONICAL_ID), None)
    if field_bundle is None or (field_bundle.get("size"), field_bundle.get("sha256")) != (V226_FIELD_BUNDLE_SIZE, V226_FIELD_BUNDLE_SHA256):
        raise SurfaceSlotMigrationError("V226 field-592 bundle manifest identity drifted")
    for blob, size, sha256, label in (
        (old_header, OLD_HEADER_SIZE, OLD_HEADER_SHA256, "V225 field-592 header"),
        (new_header, NEW_HEADER_SIZE, NEW_HEADER_SHA256, "V226 field-592 header"),
        (old_script, OLD_SCRIPT_SIZE, OLD_SCRIPT_SHA256, "V225 field-592 script"),
        (new_script, NEW_SCRIPT_SIZE, NEW_SCRIPT_SHA256, "V226 field-592 script"),
    ):
        if (len(blob), _sha256(blob)) != (size, sha256):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    if _diff_triplets(old_header, new_header) != HEADER_DIFFS:
        raise SurfaceSlotMigrationError("V225/V226 field-592 header delta drifted")
    if _patch_reconstruction(old_script, _script_patches()) != new_script or len(_diff_offsets(old_script, new_script)) != EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED:
        raise SurfaceSlotMigrationError("V225/V226 field-592 script delta drifted")
    old_atel, new_atel = AtelScript(old_script), AtelScript(new_script)
    pointer_diffs = tuple(
        (entity, script)
        for entity in range(old_atel.entity_count)
        for script in range(32)
        if old_atel.get_script_pointer(entity, script) != new_atel.get_script_pointer(entity, script)
    )
    new_cavity_entries = tuple(
        (entity, script)
        for entity in range(new_atel.entity_count)
        for script in range(32)
        if AUTO_POLL_PC <= new_atel.get_script_pointer(entity, script) < AUTO_POLL_CAVITY_END_PC
    )
    if (
        old_atel.entity_count != SCRIPT_ENTITY_COUNT
        or new_atel.entity_count != SCRIPT_ENTITY_COUNT
        or (old_atel.bytecode_offset, old_atel.bytecode_size) != (NORMAL_BYTECODE_OFFSET, NORMAL_BYTECODE_SIZE)
        or (new_atel.bytecode_offset, new_atel.bytecode_size) != (NORMAL_BYTECODE_OFFSET, NORMAL_BYTECODE_SIZE)
        or old_atel.get_script_pointer(0, 1) != AUTO_POLL_PC
        or new_atel.get_script_pointer(0, 1) != SHARED_STOP_PC
        or pointer_diffs != ((0, 1),)
        or new_cavity_entries
        or old_atel.bytecode[AUTO_POLL_PC:AUTO_POLL_CAVITY_END_PC] != AUTO_POLL_CAVITY
        or new_atel.bytecode[AUTO_POLL_PC:AUTO_POLL_CAVITY_END_PC] != X_ONLY_CAVITY
        or old_atel.get_script_pointer(CROSS_CARRIER_ENTITY, 2) != NATIVE_X_ACTION_PC
        or new_atel.get_script_pointer(CROSS_CARRIER_ENTITY, 2) != NATIVE_X_ACTION_PC
    ):
        raise SurfaceSlotMigrationError("V225/V226 field-592 X-only ATEL topology drifted")
    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    if (
        len(old_table) != ARCHIVE_TABLE_SIZE
        or _sha256(old_table) != OLD_ARCHIVE_TABLE_SHA256
        or _sha256(new_table) != NEW_ARCHIVE_TABLE_SHA256
        or _diff_triplets(old_table, new_table) != ARCHIVE_TABLE_DIFFS
    ):
        raise SurfaceSlotMigrationError("V225/V226 archive-table delta drifted")
    return old_table, new_table


def _actor_data_offset(ram: bytes, actor_base: int, entity: int) -> int:
    pointer = struct.unpack_from("<I", ram, actor_base + entity * FIELD_ACTOR_STRIDE + FIELD_ACTOR_DATA_POINTER)[0]
    offset = pointer & 0x1FFFFFFF
    if not 0 < offset <= RAM_SIZE - ACTOR_DATA_SIZE:
        raise SurfaceSlotMigrationError(f"e{entity} ActorData pointer is outside PSX RAM")
    return offset


def _validate_source(payload: bytes, old_table: bytes, old_header: bytes, old_script: bytes) -> dict[str, object]:
    if (len(payload), _sha256(payload)) != (SOURCE_PAYLOAD_SIZE, SOURCE_PAYLOAD_SHA256):
        raise SurfaceSlotMigrationError("V225 decompressed payload identity drifted")
    ram_offset, ram = _ram_from_payload(payload)
    if _sha256(ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("V225 serialized RAM identity drifted")
    resident_table = payload[EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET : EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE]
    script = payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + OLD_SCRIPT_SIZE]
    dialogue = payload[EXPECTED_DIALOGUE_PAYLOAD_OFFSET : EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE]
    walkmesh = payload[EXPECTED_WALKMESH_PAYLOAD_OFFSET : EXPECTED_WALKMESH_PAYLOAD_OFFSET + WALKMESH_SIZE]
    loaded_header = payload[EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET : EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET + OLD_HEADER_SIZE]
    if (
        _sha256(resident_table) != SOURCE_RESIDENT_TABLE_SHA256
        or _diff_triplets(resident_table, old_table) != RESIDENT_VS_MEDIA_DIFFS
        or script != old_script or payload.count(script) != 1 or payload.find(script) != EXPECTED_SCRIPT_PAYLOAD_OFFSET
        or (len(dialogue), _sha256(dialogue)) != (DIALOGUE_SIZE, DIALOGUE_SHA256)
        or payload.count(dialogue) != 1 or payload.find(dialogue) != EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        or (len(walkmesh), _sha256(walkmesh)) != (WALKMESH_SIZE, WALKMESH_SHA256)
        or payload.count(walkmesh) != 1 or payload.find(walkmesh) != EXPECTED_WALKMESH_PAYLOAD_OFFSET
        or loaded_header != old_header or payload.count(loaded_header) != 1 or payload.find(loaded_header) != EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET
        or len(payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET + OLD_SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET]) != SCRIPT_GAP_SIZE
        or _sha256(payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET + OLD_SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET]) != SCRIPT_GAP_SHA256
        or len(payload[EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET]) != DIALOGUE_GAP_SIZE
        or _sha256(payload[EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET]) != DIALOGUE_GAP_SHA256
    ):
        raise SurfaceSlotMigrationError("Resident field-592 component/table/gap identity drifted")
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
        raise SurfaceSlotMigrationError("Live field-592 pointer topology drifted")
    actor_base = actor_array_pointer & 0x1FFFFFFF
    actor_array = bytes(ram[actor_base : actor_base + ACTOR_ARRAY_SIZE])
    records = tuple(bytes(ram[actor_base + e * FIELD_ACTOR_STRIDE : actor_base + (e + 1) * FIELD_ACTOR_STRIDE]) for e in range(SCRIPT_ENTITY_COUNT))
    offsets = tuple(_actor_data_offset(ram, actor_base, e) for e in range(SCRIPT_ENTITY_COUNT))
    data = tuple(bytes(ram[offset : offset + ACTOR_DATA_SIZE]) for offset in offsets)
    if (
        offsets != EXPECTED_ACTOR_DATA_OFFSETS
        or _sha256(actor_array) != SOURCE_ACTOR_ARRAY_SHA256
        or _sha256(b"".join(data)) != SOURCE_ACTOR_DATA_SHA256
        or _sha256(records[0]) != SOURCE_E0_RECORD_SHA256
        or _sha256(data[0]) != SOURCE_E0_DATA_SHA256
        or (_sha256(records[17]), _sha256(data[17])) != (SOURCE_E17_RECORD_SHA256, SOURCE_E17_DATA_SHA256)
        or (_sha256(records[18]), _sha256(data[18])) != (SOURCE_E18_RECORD_SHA256, SOURCE_E18_DATA_SHA256)
        or (_sha256(records[20]), _sha256(data[20])) != (SOURCE_E20_RECORD_SHA256, SOURCE_E20_DATA_SHA256)
    ):
        raise SurfaceSlotMigrationError("Live field-592 actor allocation identity drifted")
    fei, carrier, leaf, rectangle = (offsets[e] for e in (FEI_ENTITY, CROSS_CARRIER_ENTITY, DOOR_LEAF_ENTITY, RECTANGLE_ENTITY))
    leaf_record = actor_base + DOOR_LEAF_ENTITY * FIELD_ACTOR_STRIDE
    if (
        struct.unpack_from("<3i", ram, fei + ACTOR_DATA_POSITION_OFFSET) != EXPECTED_FEI_POSITION
        or struct.unpack_from("<4H", ram, fei + ACTOR_DATA_SURFACES_OFFSET) != EXPECTED_FEI_SURFACES
        or (struct.unpack_from("<H", ram, fei + ACTOR_FACING_OFFSET)[0] & 0xFFF) != EXPECTED_FEI_FACING
        or ram[fei + ACTOR_CURRENT_PC_OFFSET : fei + ACTOR_CURRENT_PC_OFFSET + 4] != EXPECTED_FEI_CURRENT
        or struct.unpack_from("<3i", ram, carrier + ACTOR_DATA_POSITION_OFFSET) != (0, 0, 250 << 16)
        or struct.unpack_from("<4H", ram, carrier + ACTOR_DATA_BOUNDS_OFFSET) != (48, 60, 32, 16)
        or not (struct.unpack_from("<I", ram, carrier + ACTOR_DATA_FLAGS_OFFSET)[0] & 0x80)
        or ram[leaf_record + 0x0C : leaf_record + 0x1E] != CLOSED_LEAF_MATRIX
        or ram[leaf_record + 0x2C : leaf_record + 0x3E] != CLOSED_LEAF_MATRIX
        or struct.unpack_from("<3i", ram, rectangle + ACTOR_DATA_POSITION_OFFSET) != (0, 0, 266 << 16)
        or struct.unpack_from("<4H", ram, rectangle + ACTOR_DATA_BOUNDS_OFFSET) != (48, 200, 16, 16)
        or not (struct.unpack_from("<I", ram, rectangle + ACTOR_DATA_FLAGS_OFFSET)[0] & 0x2000)
    ):
        raise SurfaceSlotMigrationError("Fei/e17/e18/e20 saved doorway state drifted")
    controller = offsets[CONTROLLER_ENTITY]
    if (
        ram[controller + ACTOR_SCRIPT_SLOT_OFFSET : controller + ACTOR_SCRIPT_SLOT_OFFSET + 4] != bytes.fromhex("8A 04 00 FF")
        or ram[controller + ACTOR_CURRENT_PC_OFFSET : controller + ACTOR_CURRENT_PC_OFFSET + 4] != bytes.fromhex("8A 04 00 00")
    ):
        raise SurfaceSlotMigrationError("e0 is not at the pinned automatic-poll PC")
    gamestate = bytes(ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE])
    field_bank = bytes(ram[FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE])
    backup_bank = bytes(ram[GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET : GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET + FIELD_VARIABLE_BANK_SIZE])
    camera = _camera_snapshot(ram)
    windows = bytes(ram[DIALOG_WINDOWS : DIALOG_WINDOWS + DIALOG_WINDOWS_SIZE])
    if (
        _sha256(gamestate) != EXPECTED_GAMESTATE_SHA256
        or field_bank != backup_bank
        or _sha256(field_bank) != EXPECTED_FIELD_VARIABLE_BANK_SHA256
        or struct.unpack_from("<H", field_bank, APPOINTMENT_OPERAND)[0] != EXPECTED_APPOINTMENT_WORD
        or struct.unpack_from("<H", field_bank, STATE_OPERAND)[0] != EXPECTED_STATE_WORD
        or _sha256(camera) != EXPECTED_CAMERA_SHA256
        or _sha256(windows) != EXPECTED_DIALOG_WINDOWS_SHA256
        or any(struct.unpack_from("<h", windows, i * DIALOG_WINDOW_STRIDE + DIALOG_WINDOW_STATUS_OFFSET)[0] != -1 for i in range(4))
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
        "records": records,
        "data": data,
        "offsets": offsets,
        "gamestate": gamestate,
        "field_bank": field_bank,
        "camera": camera,
        "windows": windows,
    }


def migrate_v225_slot1_to_v226(
    state: bytes,
    *,
    old_disc: Path,
    new_disc: Path,
    stage_manifest: bytes,
    old_header: bytes,
    new_header: bytes,
    old_script: bytes,
    new_script: bytes,
    zstd: _ZstdLike,
) -> tuple[bytes, dict[str, object]]:
    source_sha = _sha256(state)
    if (len(state), source_sha) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise SurfaceSlotMigrationError(
            f"Source Slot 1 identity is {len(state)} / {source_sha}, expected {SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    old_name, new_name = OLD_CUE_NAME.encode("ascii"), NEW_CUE_NAME.encode("ascii")
    if len(old_name) != len(new_name) or state.count(old_name) != 1 or state.count(new_name):
        raise SurfaceSlotMigrationError("Source CUE identity drifted")
    old_table, new_table = _validate_resources(old_disc, new_disc, stage_manifest, old_header, new_header, old_script, new_script)
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
        raise SurfaceSlotMigrationError("Resident V226 script reconstruction drifted")

    final = bytearray(source_payload)
    categories: dict[str, set[int]] = {"archive_table": set(), "resident_script": set(), "runtime_e0": set()}

    def install(offset: int, old: bytes, new: bytes, category: str, label: str) -> None:
        if len(old) != len(new) or final[offset : offset + len(old)] != old:
            raise SurfaceSlotMigrationError(f"Patch source drifted: {label}")
        categories[category].update(offset + i for i, (before, after) in enumerate(zip(old, new, strict=True)) if before != after)
        final[offset : offset + len(new)] = new

    for relative, old, new in ARCHIVE_TABLE_DIFFS:
        install(EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + relative, bytes((old,)), bytes((new,)), "archive_table", f"archive table 0x{relative:04X}")
    install(EXPECTED_SCRIPT_PAYLOAD_OFFSET, snapshots["script"], resident_script, "resident_script", "resident field-592 ATEL")
    ram_offset = int(snapshots["ram_offset"])
    for relative, old, new, label in RUNTIME_PATCHES:
        install(ram_offset + relative, old, new, "runtime_e0", label)
    final_payload = bytes(final)
    expected_counts = {
        "archive_table": EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED,
        "resident_script": EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED,
        "runtime_e0": EXPECTED_RUNTIME_E0_BYTES_CHANGED,
    }
    expected_offsets = frozenset().union(*categories.values())
    actual_offsets = frozenset(_diff_offsets(source_payload, final_payload))
    if (
        {key: len(value) for key, value in categories.items()} != expected_counts
        or actual_offsets != expected_offsets
        or len(actual_offsets) != EXPECTED_PAYLOAD_BYTES_CHANGED
        or _sha256(final_payload) != OUTPUT_PAYLOAD_SHA256
    ):
        raise SurfaceSlotMigrationError("Migration changed bytes outside the exact 70-byte whitelist")
    output_table = final_payload[EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET : EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE]
    if _sha256(output_table) != OUTPUT_RESIDENT_TABLE_SHA256 or _diff_triplets(output_table, new_table) != RESIDENT_VS_MEDIA_DIFFS:
        raise SurfaceSlotMigrationError("V226 resident archive-table reconstruction drifted")
    if final_payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + NEW_SCRIPT_SIZE] != new_script:
        raise SurfaceSlotMigrationError("V226 resident field-592 script was not installed")

    result_ram_offset, result_ram = _ram_from_payload(final_payload)
    source_ram = snapshots["ram"]
    if result_ram_offset != ram_offset or _sha256(result_ram) != OUTPUT_RAM_SHA256:
        raise SurfaceSlotMigrationError("Final V226 serialized RAM identity drifted")
    actor_base = int(snapshots["actor_base"])
    offsets = tuple(snapshots["offsets"])
    records = tuple(snapshots["records"])
    source_data = tuple(snapshots["data"])
    if (
        result_ram[actor_base : actor_base + ACTOR_ARRAY_SIZE] != snapshots["actor_array"]
        or _sha256(b"".join(result_ram[o : o + ACTOR_DATA_SIZE] for o in offsets)) != OUTPUT_ACTOR_DATA_SHA256
        or _sha256(result_ram[offsets[0] : offsets[0] + ACTOR_DATA_SIZE]) != OUTPUT_E0_DATA_SHA256
        or result_ram[offsets[0] + ACTOR_SCRIPT_SLOT_OFFSET : offsets[0] + ACTOR_SCRIPT_SLOT_OFFSET + 4] != bytes.fromhex("8C 06 00 FF")
        or result_ram[offsets[0] + ACTOR_CURRENT_PC_OFFSET : offsets[0] + ACTOR_CURRENT_PC_OFFSET + 4] != bytes.fromhex("8C 06 00 00")
    ):
        raise SurfaceSlotMigrationError("Final field-592 e0 runtime identity drifted")
    for entity in range(SCRIPT_ENTITY_COUNT):
        record = result_ram[actor_base + entity * FIELD_ACTOR_STRIDE : actor_base + (entity + 1) * FIELD_ACTOR_STRIDE]
        data = result_ram[offsets[entity] : offsets[entity] + ACTOR_DATA_SIZE]
        if record != records[entity] or (entity and data != source_data[entity]):
            raise SurfaceSlotMigrationError(f"Unrelated field runtime e{entity} changed")
    for start, size, label in (
        (GAME_STATE, GAMESTATE_SIZE, "GameState/party"),
        (FIELD_SCRIPT_MEMORY, FIELD_VARIABLE_BANK_SIZE, "active field variables"),
        (DIALOG_WINDOWS, DIALOG_WINDOWS_SIZE, "dialogue windows"),
    ):
        if result_ram[start : start + size] != source_ram[start : start + size]:
            raise SurfaceSlotMigrationError(f"{label} was not preserved")
    if _camera_snapshot(result_ram) != snapshots["camera"]:
        raise SurfaceSlotMigrationError("Camera was not preserved")
    for offset, size, source_blob, label in (
        (EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET, OLD_HEADER_SIZE, snapshots["loaded_header"], "loaded header"),
        (EXPECTED_DIALOGUE_PAYLOAD_OFFSET, DIALOGUE_SIZE, snapshots["dialogue"], "dialogue"),
        (EXPECTED_WALKMESH_PAYLOAD_OFFSET, WALKMESH_SIZE, snapshots["walkmesh"], "walkmesh"),
    ):
        if final_payload[offset : offset + size] != source_blob:
            raise SurfaceSlotMigrationError(f"Field-592 {label} was not preserved")
    if (
        final_payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET + NEW_SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET]
        != source_payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET + OLD_SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET]
        or final_payload[EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET]
        != source_payload[EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET]
    ):
        raise SurfaceSlotMigrationError("Allocator/component neighbors changed")

    provisional_prefix = _expected_prefix(source_prefix, compressed_size=OUTPUT_COMPRESSED_SIZE)
    if len(_diff_offsets(source_prefix, provisional_prefix)) != EXPECTED_PREFIX_BYTES_CHANGED or _sha256(provisional_prefix) != OUTPUT_PREFIX_SHA256:
        raise SurfaceSlotMigrationError("V226 media-prefix reconstruction drifted")
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
        raise SurfaceSlotMigrationError("Final V226 state identity or round trip drifted")
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
        "runtime_e0_bytes_changed": len(categories["runtime_e0"]),
        "resident_script_size": len(resident_script),
        "resident_script_capacity": SCRIPT_ALLOCATED_CAPACITY,
        "retired_auto_poll_pc": f"0x{AUTO_POLL_CURRENT_PC:04X}",
        "shared_stop_pc": f"0x{SHARED_STOP_PC:04X}",
        "native_x_action_pc": f"0x{NATIVE_X_ACTION_PC:04X}",
        "full_poll_cavity_restored": True,
        "resident_archive_table_sha256": OUTPUT_RESIDENT_TABLE_SHA256,
        "resident_archive_volatile_tail_preserved": True,
        "loaded_header_preserved": True,
        "walkmesh_preserved": True,
        "field_variables_preserved": True,
        "fei_preserved": True,
        "e17_carrier_preserved": True,
        "e18_closed_leaf_preserved": True,
        "e20_rectangle_preserved": True,
        "all_noncontroller_actor_runtime_preserved": True,
        "gamestate_party_camera_windows_preserved": True,
        "allocator_safe": True,
        "round_trip_verified": True,
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "v226_stage_manifest_sha256": V226_STAGE_MANIFEST_SHA256,
        "v226_disc_sha256": NEW_DISC_SHA256,
    }
    return result, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=SOURCE_BACKUP)
    parser.add_argument("--old-disc", type=Path, default=PROJECT_ROOT / "output" / OLD_CUE_NAME.replace(".cue", ".bin"))
    parser.add_argument("--new-disc", type=Path, default=PROJECT_ROOT / "output" / NEW_CUE_NAME.replace(".cue", ".bin"))
    parser.add_argument("--stage-manifest", type=Path, default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v226_stage" / "manifest.json")
    parser.add_argument("--old-header", type=Path, default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v225_stage" / "clones" / "field_592_disc1_donor" / "header.bin")
    parser.add_argument("--new-header", type=Path, default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v226_stage" / "clones" / "field_592_disc1_donor" / "header.bin")
    parser.add_argument("--old-script", type=Path, default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v225_stage" / "clones" / "field_592_disc1_donor" / "05_scripts.bin")
    parser.add_argument("--new-script", type=Path, default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v226_stage" / "clones" / "field_592_disc1_donor" / "05_scripts.bin")
    parser.add_argument("--zstd", type=Path, default=PROJECT_ROOT / "work" / "duckstation" / "zstd.dll")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "work" / "save_candidates" / "SLUS-00669_1_v226_from_408a5dc9_field592_x_only.sav")
    parser.add_argument("--report", type=Path, default=PROJECT_ROOT / "work" / "save_candidates" / "SLUS-00669_1_v226_from_408a5dc9_field592_x_only.json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output, report_path = args.output.resolve(), args.report.resolve()
        source_path = args.source.resolve()
        if output == LIVE_SLOT1 or report_path == LIVE_SLOT1:
            raise SurfaceSlotMigrationError("Output/report may not be the live Slot 1")
        if output == source_path or report_path == source_path:
            raise SurfaceSlotMigrationError("Output/report may not replace the source state")
        if output == report_path:
            raise SurfaceSlotMigrationError("Output and report paths must be distinct")
        zstd = media_migration._Zstd(args.zstd)
        result, report = migrate_v225_slot1_to_v226(
            args.source.read_bytes(),
            old_disc=args.old_disc,
            new_disc=args.new_disc,
            stage_manifest=args.stage_manifest.read_bytes(),
            old_header=args.old_header.read_bytes(),
            new_header=args.new_header.read_bytes(),
            old_script=args.old_script.read_bytes(),
            new_script=args.new_script.read_bytes(),
            zstd=zstd,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, SurfaceSlotMigrationError, media_migration.StateMigrationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote V226 candidate: {output}")
    print(f"Wrote migration report: {report_path}")
    print(f"SHA-256: {report['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
