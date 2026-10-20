#!/usr/bin/env python3
"""Migrate the exact V226 intake-door Slot 1 state to V227 safely.

V227 reroutes field 621's examination-room door from field 565 / parameter 3
to the new Treatment Preparation Room at field 594 / parameter 0.  The saved
field is already resident, so changing only the mounted image is insufficient:
the matching five-byte CHANGE_FIELD instruction must also be updated in the
serialized resident ATEL.  Its size and every script address remain unchanged.

This helper is deliberately fail-closed.  It pins the source state, both media
sets, the V227 stage manifest, both field-621 bundles/header/script pairs, the
3,031-byte archive-table delta, and the complete live field layout.  It changes
only the archive-table delta and the two operands that differ in the resident
CHANGE_FIELD instruction.  ActorData (including Fei, e26, and e34), GameState,
field variables, camera, dialogue windows, and every neighboring field
component are preserved byte-for-byte.  The CLI never writes DuckStation's live
Slot 1; it emits a separate candidate and JSON report.
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
SOURCE_BACKUP = (
    PROJECT_ROOT
    / "work"
    / "save_backups"
    / "SLUS-00669_1_v226_intake_door_room_change_9436ef84.sav"
).resolve()

SOURCE_STATE_SIZE = 1_910_685
SOURCE_STATE_SHA256 = "9436ef847164e1c850828da3c6f90a28ba1ea931763a3b691c6117e376333c82"
SOURCE_PREFIX_SIZE = 0xA0D1
SOURCE_PREFIX_SHA256 = "a5b0038292e953635040e54e0310fe6b10b05382b96dbd882dea9515da24ebc9"
SOURCE_COMPRESSED_SIZE = 1_869_516
SOURCE_COMPRESSED_SHA256 = "52f0b304d97449eb82ee686825b914889018094dc928022e372f8e4ed4a5f22f"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "7dea010fc6d894530902fefa33d9fe4ddd7cf8894a4d0445b253628208d4a676"
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
SOURCE_RAM_SHA256 = "c7d247c83eb7dc12f974b918db94e77b56f7bbc893a6f445fec50956e80d7c1e"

OUTPUT_STATE_SIZE = 1_735_278
OUTPUT_STATE_SHA256 = "23221b3468b77096fb9a8e07a11a32203fbd51e4c92d0b7fd203b036e30c1950"
OUTPUT_PREFIX_SHA256 = "c7c7fb043efdc45f00fc37ae628d1dbd907e2928de1f5b0d9a63eb076628d373"
OUTPUT_COMPRESSED_SIZE = 1_694_109
OUTPUT_COMPRESSED_SHA256 = "799caec8ddb776d60bd03ecbccabfdd5974f5435d90de9719470291ad0c93796"
OUTPUT_PAYLOAD_SHA256 = "378c7d8a3fe297927ba5823fcdb77eb7c362c4840eb27f1c1f806d604a3858a4"
OUTPUT_RAM_SHA256 = "3aa5febe630f91612e4905ffe6d8f198e46a30cfaa03a78c40285e1235ab4591"

OLD_DISC_SIZE = 698_642_784
NEW_DISC_SIZE = 698_885_040
OLD_DISC_SHA256 = "8a916111d1557c98c904ed95431d973a0d460aa71b52fc3eba56093e9127dda6"
NEW_DISC_SHA256 = "108c753b964831ae6be61ca05fb8cbcd47240d27c0d4f376135828b4945596ed"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v226.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v227.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = "ee95f0b73bf490e5718b6b3023366f03e385008a46f681c19b7f142ad4cbbcee"
NEW_CUE_SHA256 = "df061663cd9053e195513221997f4042d37c8d23fba9268e9d10bdafa577c134"

V227_STAGE_MANIFEST_SIZE = 122_987
V227_STAGE_MANIFEST_SHA256 = "3a56b3ac97ce837c9356207df6a14d488a26cc0a63524472ba903bbae557fb67"
MANIFEST_RESOURCES = {
    1794: (83_664, "3ba1ba695be88e8000ab09edb5dc50911edfd7e4c6dd00ca2f57b4150af7b700"),
    1795: (131_072, "d151035c6523091d22255ebf587e463748a74d1db521cce852a8d85f6e197d41"),
    1848: (135_644, "168fb1fb14a0c4745725396aae8d5831d931cd30d0d1c67eb6e8d654708eb2bd"),
}

FIELD621_CANONICAL_ID = 1848
FIELD621_FAT_INDEX = FIELD621_CANONICAL_ID - 5
OLD_FIELD621_BUNDLE_SIZE = 135_648
OLD_FIELD621_BUNDLE_SHA256 = "011be9593a2c565e6c3bb5f325ef64ac47811592794945ce529fcb3b6eb36677"
NEW_FIELD621_BUNDLE_SIZE, NEW_FIELD621_BUNDLE_SHA256 = MANIFEST_RESOURCES[1848]
OLD_DUMMY_SIZE = 24
OLD_DUMMY_SHA256 = "aafefb97ceb8e4667c719b99c4250b286e03087315b61848d196300140a95a2c"

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = "a6505ea96cd9c20b16bfb45e67f34a5b932795f569ec04b7f44d4bf815c2937c"
NEW_ARCHIVE_TABLE_SHA256 = "165b10eb5a7a7c31f9188ae62d70dc0ce82810a4bb8b8671910e881cb4379e8f"
ARCHIVE_TABLE_DIFF_COUNT = 3_031
ARCHIVE_TABLE_DIFF_FIRST = 0x2F58
ARCHIVE_TABLE_DIFF_LAST = 0x7157
ARCHIVE_TABLE_DIFF_SHA256 = "bbc6601824b2f9a8eaad355ca88c66c982c3e2c16f77ae95f80a82ac76f783b4"
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
SOURCE_RESIDENT_TABLE_SHA256 = "3ee67d330d7a2c4b2bbdd8188dfa38a4a0152bea3950be3276d40a6ce8862a47"
OUTPUT_RESIDENT_TABLE_SHA256 = "bdf07517cbcfb3ad6676aa1deda27086707aa75f7e67c54cf002afac9ef45ada"
RESIDENT_VS_MEDIA_DIFFS = ((0x7FFF, 0xE0, 0x00),)

OLD_HEADER_SIZE = NEW_HEADER_SIZE = 1_408
OLD_HEADER_SHA256 = "bd8be9feef57bff074c81c885d66b329ed20456e42d3a11c6b8e03b18550598f"
NEW_HEADER_SHA256 = "2d05178f666806c9eaed864d63c44ec41822adeb1164d13e69e50e9cde55432d"
HEADER_DIFFS = ((0x0148, 0x58, 0x54), (0x014C, 0x2C, 0x28), (0x0150, 0xDC, 0xD8))
HEADER_DIFF_SHA256 = "0d8eb6effdef221548817e853160c40557524c454f74556719717ebafb5a8dc0"
EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET = 0x1CBD1E

OLD_SCRIPT_SIZE = NEW_SCRIPT_SIZE = 10_895
OLD_SCRIPT_SHA256 = "a362a56e04f91240e4209cb93cdb36a63c31d57bdf2e03c25fca52f202845ea7"
NEW_SCRIPT_SHA256 = "a7c52258a56f10a1bea9e8ee7cdc9c7730b78bd1c21f524a12a108302a2172f2"
EXPECTED_SCRIPT_PAYLOAD_OFFSET = 0x11261E
EXPECTED_SCRIPT_GUEST_POINTER = 0x80110BBC
EXPECTED_VM_SCRIPT_GUEST_POINTER = 0x80111880
SCRIPT_ENTITY_COUNT = 49
SCRIPT_BYTECODE_OFFSET = 0x0CC4
SCRIPT_BYTECODE_SIZE = 0x1DCB
DOOR_ENTITY = 26
DOOR_HELPER_ENTITY = 34
DOOR_NATIVE_ACTION_PC = 0x0D38
DOOR_CHANGE_FIELD_PC = 0x0D4C
DOOR_SCRIPT2_PC = 0x1617
SCRIPT_PATCH_OFFSET = SCRIPT_BYTECODE_OFFSET + DOOR_CHANGE_FIELD_PC
OLD_CHANGE_FIELD = bytes.fromhex("98 35 82 03 80")
NEW_CHANGE_FIELD = bytes.fromhex("98 52 82 00 80")
SCRIPT_DIFFS = ((0x1A11, 0x35, 0x52), (0x1A13, 0x03, 0x00))
SCRIPT_DIFF_SHA256 = "24feb5ae89cb6d0d44a3e2fb2c9778a6827d7340342d13a31e57b9e9530b6923"
OLD_DESTINATION_FIELD = 565
OLD_DESTINATION_PARAMETER = 3
NEW_DESTINATION_FIELD = 594
NEW_DESTINATION_PARAMETER = 0

COMPONENT_IDENTITIES = (
    (1, 5_156, "6d36a3fc267029bc2e65ee9ae7435208be0a7934c9aa86af3fa1fd580548b932", "walkmesh"),
    (2, 39_292, "b06e38c58fcd5e1ce5033e1135f0ae7c7d745b9ef37575f44b0cba4c936c52aa", "models"),
    (3, 23_956, "d1f14379b3179d1baec2ebc239cea70309144d3f7b3c366044aa18dd09c27770", "actors"),
    (4, 143_108, "f5b083c238c90ec8cca8b554a15e8f3b1b94bede0c4b4f0322a7808c89453a23", "sprites"),
    (6, 528, "54325752ea0b7e2c679501792acf113e86495454e3a238acdaf63eaa7db06e16", "encounters"),
    (7, 2_135, "2affc3b9e7ad27ae0e9be2b4e8f0d1362f3b37ef7218001aa995994cf6e5bb40", "dialogue"),
)
EXPECTED_DIALOGUE_PAYLOAD_OFFSET = 0x1150DE
DIALOGUE_SIZE = 2_135
DIALOGUE_SHA256 = COMPONENT_IDENTITIES[-1][2]
EXPECTED_WALKMESH_PAYLOAD_OFFSET = 0x11594E
WALKMESH_SIZE = 5_156
WALKMESH_SHA256 = COMPONENT_IDENTITIES[0][2]
SCRIPT_GAP_SIZE = 49
SCRIPT_GAP_SHA256 = "ac980b58ab900dfd9aee8ed5440cc2f2d395fd4b24a58a647df9128ef388e562"
DIALOGUE_GAP_SIZE = 25
DIALOGUE_GAP_SHA256 = "114e33f61a7e85e1dd3211f91826fe4cd3609d327de71c8f250e32a30ee4fcf2"

FIELD_CUR_DIALOGUE_FILE = 0x0ADBF0
FIELD_SMALL_COMPONENT = 0x0ADBF4
GAME_SCENE_MAP = 0x04F34C
EXPECTED_FIELD = 621
EXPECTED_ACTOR_COUNT = 63
EXPECTED_ACTOR_ARRAY_GUEST_POINTER = 0x8011B0D4
EXPECTED_VM_ACTOR_GUEST_POINTER = 0x80122B00
EXPECTED_DIALOGUE_GUEST_POINTER = 0x8011367C
EXPECTED_SMALL_COMPONENT_POINTER = 0x80113664
ACTOR_ARRAY_SIZE = EXPECTED_ACTOR_COUNT * FIELD_ACTOR_STRIDE
ACTOR_DATA_SIZE = 0x138
ACTOR_SCRIPT_SLOT_OFFSET = 0x8C
ACTOR_CURRENT_PC_OFFSET = 0xCC
ACTOR_DATA_POSITION_OFFSET = 0x20
ACTOR_DATA_SURFACES_OFFSET = 0x08
ACTOR_FACING_OFFSET = 0x106
FEI_ENTITY = 3
EXPECTED_FEI_ACTOR_DATA = 0x11CD7C
EXPECTED_DOOR_ACTOR_DATA = 0x11FAD4
EXPECTED_HELPER_ACTOR_DATA = 0x120FD4
EXPECTED_FEI_PC = 0x0201
EXPECTED_DOOR_PC = 0x024E
EXPECTED_HELPER_PC = 0x038F
EXPECTED_FEI_POSITION = (108_940_603, 0, 26_196_522)
EXPECTED_FEI_SURFACES = (85, 0, 0, 0)
EXPECTED_FEI_FACING = 0x0800
SOURCE_ACTOR_ARRAY_SHA256 = "e83938ae155bc3cf37a3a93b7853f9d93196e9f160d90200d5c6bb1ce0bca7ee"
SOURCE_ACTOR_DATA_SHA256 = "e402d65eedcf2f6ec52f04289f9453493215d6fa2fce189f1407706ba97ff228"
SOURCE_FEI_RECORD_SHA256 = "7274462841aefe4dea43db1ba0021349ff9dcb1de87a2ba2670335bbbd187f2b"
SOURCE_FEI_DATA_SHA256 = "48775db3f996843b2688de1f746db814201e0704956992fe77988cb40a606353"
SOURCE_DOOR_RECORD_SHA256 = "b1f24430239ad1ee96584369e2e155a80e95c2d4af671b5794f6857a29b0a7f6"
SOURCE_DOOR_DATA_SHA256 = "39998b57c96f6b66899f08ba6915ce14ca5f64a96b1e2660fca717ae22a238f8"
SOURCE_HELPER_RECORD_SHA256 = "61c9fc4f5df96b808870774c382e1502a7c37efcf412c412d4cd2d85d373aaf5"
SOURCE_HELPER_DATA_SHA256 = "8d2bfa7d7f4764bfb4a45a045569e6014fc78d9637d3865da96b250445849416"

FIELD_VARIABLE_BACKUP_OFFSET = 0x1930
FIELD_VARIABLE_BANK_SIZE = 0x400
KEYCARD_OPERAND = 0x021A
APPOINTMENT_OPERAND = 0x03EE
STATE_OPERAND = 0x03FA
EXPECTED_KEYCARD_WORD = 0x00FD
EXPECTED_APPOINTMENT_WORD = 0x4005
EXPECTED_STATE_WORD = 0x00F0
DIALOG_WINDOWS = 0x0C2698
DIALOG_WINDOW_STRIDE = 0x498
DIALOG_WINDOWS_SIZE = 4 * DIALOG_WINDOW_STRIDE
DIALOG_WINDOW_STATUS_OFFSET = 0x40E
EXPECTED_GAMESTATE_SHA256 = "8e27d49b1a9e7bb8a553f1985fc37b900cdecad6a55a9fe3a20a4f9a0e5e1916"
EXPECTED_FIELD_VARIABLE_BANK_SHA256 = "625d0d0ee64a6d5f3f55e5717f10c6bcda19a958e75c8ec4466492ab568027b9"
EXPECTED_CAMERA_SHA256 = "505f0da08fb00d222953a1e5797c2f8237dd2720b2eacdad34dedb9ef88e1ffb"
EXPECTED_DIALOG_WINDOWS_SHA256 = "8b8d2743404ca97d8690ccdd1bcd59d997da9fd3f9a00a6800a465274d3e3eef"

EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED = 3_031
EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED = 2
EXPECTED_RUNTIME_PC_BYTES_CHANGED = 0
EXPECTED_PAYLOAD_BYTES_CHANGED = 3_033
EXPECTED_PREFIX_BYTES_CHANGED = 4


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output whenever the pinned V226/V227 contract drifts."""


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


def _triplet_digest(diffs: Sequence[tuple[int, int, int]]) -> str:
    return _sha256(b"".join(struct.pack("<HBB", offset, old, new) for offset, old, new in diffs))


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
    old_name, new_name = OLD_CUE_NAME.encode("ascii"), NEW_CUE_NAME.encode("ascii")
    if len(old_name) != len(new_name) or source_prefix.count(old_name) != 1 or source_prefix.count(new_name):
        raise SurfaceSlotMigrationError("Pinned V226 media path changed")
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


def _validate_file(path: Path, size: int, sha256: str, label: str) -> None:
    if not path.is_file() or path.stat().st_size != size or _file_sha256(path) != sha256:
        raise SurfaceSlotMigrationError(f"{label} identity drifted")


def _disc_resource(image: Mode2Image, canonical_id: int, size: int, sha256: str, label: str) -> bytes:
    entries = image.read_index()
    index = canonical_id - 5
    if index >= len(entries) or entries[index].canonical_disc2_index != canonical_id:
        raise SurfaceSlotMigrationError(f"{label} FAT mapping drifted")
    data = image.extract_entry(entries[index])
    if (len(data), _sha256(data)) != (size, sha256):
        raise SurfaceSlotMigrationError(f"{label} identity drifted")
    return data


def _disc_field621(disc: Path, *, size: int, sha256: str, label: str) -> tuple[bytes, ParsedField]:
    try:
        bundle = _disc_resource(Mode2Image(disc), FIELD621_CANONICAL_ID, size, sha256, label)
        parsed = parse_field(bundle)
    except (DiscFormatError, FieldFormatError) as exc:
        raise SurfaceSlotMigrationError(f"Cannot decode {label}: {exc}") from exc
    if len(parsed.parts) != 9:
        raise SurfaceSlotMigrationError(f"{label} component layout drifted")
    return bundle, parsed


def _patch_reconstruction(source: bytes, offset: int, old: bytes, new: bytes) -> bytes:
    if len(old) != len(new) or source[offset : offset + len(old)] != old:
        raise SurfaceSlotMigrationError(f"Patch source drifted at 0x{offset:X}")
    result = bytearray(source)
    result[offset : offset + len(new)] = new
    return bytes(result)


def _validate_resources(
    old_disc: Path,
    new_disc: Path,
    stage_manifest: bytes,
    old_header: bytes,
    new_header: bytes,
    old_script: bytes,
    new_script: bytes,
) -> tuple[bytes, bytes]:
    if (len(stage_manifest), _sha256(stage_manifest)) != (V227_STAGE_MANIFEST_SIZE, V227_STAGE_MANIFEST_SHA256):
        raise SurfaceSlotMigrationError("V227 stage manifest identity drifted")
    try:
        inventory = {item["canonical_id"]: item for item in json.loads(stage_manifest)["replacement_inventory"]}
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise SurfaceSlotMigrationError("V227 stage manifest structure drifted") from exc
    for canonical_id, expected in MANIFEST_RESOURCES.items():
        item = inventory.get(canonical_id)
        if item is None or (item.get("size"), item.get("sha256")) != expected:
            raise SurfaceSlotMigrationError(f"V227 manifest resource {canonical_id} drifted")
    for blob, size, sha256, label in (
        (old_header, OLD_HEADER_SIZE, OLD_HEADER_SHA256, "V226 field-621 header"),
        (new_header, NEW_HEADER_SIZE, NEW_HEADER_SHA256, "V227 field-621 header"),
        (old_script, OLD_SCRIPT_SIZE, OLD_SCRIPT_SHA256, "V226 field-621 script"),
        (new_script, NEW_SCRIPT_SIZE, NEW_SCRIPT_SHA256, "V227 field-621 script"),
    ):
        if (len(blob), _sha256(blob)) != (size, sha256):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    header_diffs = _diff_triplets(old_header, new_header)
    script_diffs = _diff_triplets(old_script, new_script)
    if header_diffs != HEADER_DIFFS or _triplet_digest(header_diffs) != HEADER_DIFF_SHA256:
        raise SurfaceSlotMigrationError("V226/V227 field-621 header delta drifted")
    if (
        script_diffs != SCRIPT_DIFFS
        or _triplet_digest(script_diffs) != SCRIPT_DIFF_SHA256
        or _patch_reconstruction(old_script, SCRIPT_PATCH_OFFSET, OLD_CHANGE_FIELD, NEW_CHANGE_FIELD) != new_script
    ):
        raise SurfaceSlotMigrationError("V226/V227 field-621 route delta drifted")
    old_atel, new_atel = AtelScript(old_script), AtelScript(new_script)
    old_pointers = tuple(old_atel.get_script_pointer(e, s) for e in range(SCRIPT_ENTITY_COUNT) for s in range(32))
    new_pointers = tuple(new_atel.get_script_pointer(e, s) for e in range(SCRIPT_ENTITY_COUNT) for s in range(32))
    if (
        old_atel.entity_count != SCRIPT_ENTITY_COUNT
        or new_atel.entity_count != SCRIPT_ENTITY_COUNT
        or (old_atel.bytecode_offset, old_atel.bytecode_size) != (SCRIPT_BYTECODE_OFFSET, SCRIPT_BYTECODE_SIZE)
        or (new_atel.bytecode_offset, new_atel.bytecode_size) != (SCRIPT_BYTECODE_OFFSET, SCRIPT_BYTECODE_SIZE)
        or old_pointers != new_pointers
        or old_atel.get_script_pointer(DOOR_ENTITY, 2) != DOOR_SCRIPT2_PC
        or old_atel.bytecode[DOOR_CHANGE_FIELD_PC : DOOR_CHANGE_FIELD_PC + 5] != OLD_CHANGE_FIELD
        or new_atel.bytecode[DOOR_CHANGE_FIELD_PC : DOOR_CHANGE_FIELD_PC + 5] != NEW_CHANGE_FIELD
        or old_atel.bytecode[DOOR_NATIVE_ACTION_PC : DOOR_CHANGE_FIELD_PC] != new_atel.bytecode[DOOR_NATIVE_ACTION_PC : DOOR_CHANGE_FIELD_PC]
    ):
        raise SurfaceSlotMigrationError("V226/V227 field-621 ATEL topology drifted")
    for path, size, sha256, label in (
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V226 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V227 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V226 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V227 CUE"),
    ):
        _validate_file(path, size, sha256, label)
    try:
        _old_bundle, old_field = _disc_field621(
            old_disc, size=OLD_FIELD621_BUNDLE_SIZE, sha256=OLD_FIELD621_BUNDLE_SHA256, label="V226 field-621 bundle"
        )
        _new_bundle, new_field = _disc_field621(
            new_disc, size=NEW_FIELD621_BUNDLE_SIZE, sha256=NEW_FIELD621_BUNDLE_SHA256, label="V227 field-621 bundle"
        )
        old_image, new_image = Mode2Image(old_disc), Mode2Image(new_disc)
        for canonical_id in (1794, 1795):
            _disc_resource(old_image, canonical_id, OLD_DUMMY_SIZE, OLD_DUMMY_SHA256, f"V226 resource {canonical_id}")
            size, sha256 = MANIFEST_RESOURCES[canonical_id]
            _disc_resource(new_image, canonical_id, size, sha256, f"V227 resource {canonical_id}")
    except DiscFormatError as exc:
        raise SurfaceSlotMigrationError(f"Cannot validate V226/V227 disc resources: {exc}") from exc
    if old_field.header != old_header or new_field.header != new_header:
        raise SurfaceSlotMigrationError("Field-621 disc/header clone identity drifted")
    old_parts = tuple(part.data for part in old_field.parts)
    new_parts = tuple(part.data for part in new_field.parts)
    if old_parts[5] != old_script or new_parts[5] != new_script:
        raise SurfaceSlotMigrationError("Field-621 disc/script clone identity drifted")
    for index, size, sha256, label in COMPONENT_IDENTITIES:
        if (
            (len(old_parts[index]), _sha256(old_parts[index])) != (size, sha256)
            or old_parts[index] != new_parts[index]
        ):
            raise SurfaceSlotMigrationError(f"Field-621 {label} preservation drifted")
    if any(old_parts[index] != new_parts[index] for index in range(9) if index != 5):
        raise SurfaceSlotMigrationError("A non-script field-621 component changed")
    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    table_diffs = _diff_triplets(old_table, new_table)
    if (
        len(old_table) != ARCHIVE_TABLE_SIZE
        or _sha256(old_table) != OLD_ARCHIVE_TABLE_SHA256
        or _sha256(new_table) != NEW_ARCHIVE_TABLE_SHA256
        or len(table_diffs) != ARCHIVE_TABLE_DIFF_COUNT
        or table_diffs[0][0] != ARCHIVE_TABLE_DIFF_FIRST
        or table_diffs[-1][0] != ARCHIVE_TABLE_DIFF_LAST
        or _triplet_digest(table_diffs) != ARCHIVE_TABLE_DIFF_SHA256
        or any(offset == 0x7FFF for offset, _old, _new in table_diffs)
    ):
        raise SurfaceSlotMigrationError("V226/V227 archive-table delta drifted")
    return old_table, new_table


def _actor_data_offset(ram: bytes, actor_base: int, entity: int) -> int:
    pointer = struct.unpack_from("<I", ram, actor_base + entity * FIELD_ACTOR_STRIDE + FIELD_ACTOR_DATA_POINTER)[0]
    offset = pointer & 0x1FFFFFFF
    if not 0 < offset <= RAM_SIZE - ACTOR_DATA_SIZE:
        raise SurfaceSlotMigrationError(f"e{entity} ActorData pointer is outside PSX RAM")
    return offset


def _validate_source(payload: bytes, old_table: bytes, old_header: bytes, old_script: bytes) -> dict[str, object]:
    if (len(payload), _sha256(payload)) != (SOURCE_PAYLOAD_SIZE, SOURCE_PAYLOAD_SHA256):
        raise SurfaceSlotMigrationError("V226 decompressed payload identity drifted")
    ram_offset, ram = _ram_from_payload(payload)
    if _sha256(ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("V226 serialized RAM identity drifted")
    resident_table = payload[EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET : EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE]
    script = payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + OLD_SCRIPT_SIZE]
    dialogue = payload[EXPECTED_DIALOGUE_PAYLOAD_OFFSET : EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE]
    walkmesh = payload[EXPECTED_WALKMESH_PAYLOAD_OFFSET : EXPECTED_WALKMESH_PAYLOAD_OFFSET + WALKMESH_SIZE]
    loaded_header = payload[EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET : EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET + OLD_HEADER_SIZE]
    script_gap = payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET + OLD_SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET]
    dialogue_gap = payload[EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET]
    if (
        _sha256(resident_table) != SOURCE_RESIDENT_TABLE_SHA256
        or _diff_triplets(resident_table, old_table) != RESIDENT_VS_MEDIA_DIFFS
        or script != old_script
        or payload.count(old_script) != 1
        or payload.find(old_script) != EXPECTED_SCRIPT_PAYLOAD_OFFSET
        or (len(dialogue), _sha256(dialogue)) != (DIALOGUE_SIZE, DIALOGUE_SHA256)
        or payload.count(dialogue) != 1
        or payload.find(dialogue) != EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        or (len(walkmesh), _sha256(walkmesh)) != (WALKMESH_SIZE, WALKMESH_SHA256)
        or payload.count(walkmesh) != 1
        or payload.find(walkmesh) != EXPECTED_WALKMESH_PAYLOAD_OFFSET
        or loaded_header != old_header
        or payload.count(old_header) != 1
        or payload.find(old_header) != EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET
        or (len(script_gap), _sha256(script_gap)) != (SCRIPT_GAP_SIZE, SCRIPT_GAP_SHA256)
        or (len(dialogue_gap), _sha256(dialogue_gap)) != (DIALOGUE_GAP_SIZE, DIALOGUE_GAP_SHA256)
    ):
        raise SurfaceSlotMigrationError("Resident field-621 component/table/gap identity drifted")
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
        raise SurfaceSlotMigrationError("Live field-621 pointer topology drifted")
    actor_base = actor_array_pointer & 0x1FFFFFFF
    actor_array = bytes(ram[actor_base : actor_base + ACTOR_ARRAY_SIZE])
    records = tuple(
        bytes(ram[actor_base + entity * FIELD_ACTOR_STRIDE : actor_base + (entity + 1) * FIELD_ACTOR_STRIDE])
        for entity in range(EXPECTED_ACTOR_COUNT)
    )
    offsets = tuple(_actor_data_offset(ram, actor_base, entity) for entity in range(SCRIPT_ENTITY_COUNT))
    data = tuple(bytes(ram[offset : offset + ACTOR_DATA_SIZE]) for offset in offsets)
    key_entities = (
        (FEI_ENTITY, EXPECTED_FEI_ACTOR_DATA, SOURCE_FEI_RECORD_SHA256, SOURCE_FEI_DATA_SHA256),
        (DOOR_ENTITY, EXPECTED_DOOR_ACTOR_DATA, SOURCE_DOOR_RECORD_SHA256, SOURCE_DOOR_DATA_SHA256),
        (DOOR_HELPER_ENTITY, EXPECTED_HELPER_ACTOR_DATA, SOURCE_HELPER_RECORD_SHA256, SOURCE_HELPER_DATA_SHA256),
    )
    if _sha256(actor_array) != SOURCE_ACTOR_ARRAY_SHA256 or _sha256(b"".join(data)) != SOURCE_ACTOR_DATA_SHA256:
        raise SurfaceSlotMigrationError("Live field-621 actor allocation identity drifted")
    for entity, expected_offset, record_sha, data_sha in key_entities:
        if offsets[entity] != expected_offset or _sha256(records[entity]) != record_sha or _sha256(data[entity]) != data_sha:
            raise SurfaceSlotMigrationError(f"Live field-621 e{entity} identity drifted")
    old_atel = AtelScript(old_script)
    idle = ((FEI_ENTITY, EXPECTED_FEI_PC), (DOOR_ENTITY, EXPECTED_DOOR_PC), (DOOR_HELPER_ENTITY, EXPECTED_HELPER_PC))
    for entity, expected_pc in idle:
        slot_pc = struct.unpack_from("<H", data[entity], ACTOR_SCRIPT_SLOT_OFFSET)[0]
        current_pc = struct.unpack_from("<H", data[entity], ACTOR_CURRENT_PC_OFFSET)[0]
        if slot_pc != expected_pc or current_pc != expected_pc or old_atel.bytecode[current_pc] != 0x00:
            raise SurfaceSlotMigrationError(f"e{entity} is not idle at the pinned STOP")
    current_pcs = tuple(struct.unpack_from("<H", actor, ACTOR_CURRENT_PC_OFFSET)[0] for actor in data)
    if any(DOOR_CHANGE_FIELD_PC <= pc < DOOR_CHANGE_FIELD_PC + len(OLD_CHANGE_FIELD) for pc in current_pcs):
        raise SurfaceSlotMigrationError("An ActorData PC points into the changed route instruction")
    fei = data[FEI_ENTITY]
    if (
        struct.unpack_from("<3i", fei, ACTOR_DATA_POSITION_OFFSET) != EXPECTED_FEI_POSITION
        or struct.unpack_from("<4H", fei, ACTOR_DATA_SURFACES_OFFSET) != EXPECTED_FEI_SURFACES
        or (struct.unpack_from("<H", fei, ACTOR_FACING_OFFSET)[0] & 0xFFF) != EXPECTED_FEI_FACING
    ):
        raise SurfaceSlotMigrationError("Fei's saved doorway pose drifted")
    gamestate = bytes(ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE])
    field_bank = bytes(ram[FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE])
    backup_bank = bytes(ram[GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET : GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET + FIELD_VARIABLE_BANK_SIZE])
    camera = _camera_snapshot(ram)
    windows = bytes(ram[DIALOG_WINDOWS : DIALOG_WINDOWS + DIALOG_WINDOWS_SIZE])
    if (
        _sha256(gamestate) != EXPECTED_GAMESTATE_SHA256
        or field_bank != backup_bank
        or _sha256(field_bank) != EXPECTED_FIELD_VARIABLE_BANK_SHA256
        or struct.unpack_from("<H", field_bank, KEYCARD_OPERAND)[0] != EXPECTED_KEYCARD_WORD
        or struct.unpack_from("<H", field_bank, APPOINTMENT_OPERAND)[0] != EXPECTED_APPOINTMENT_WORD
        or struct.unpack_from("<H", field_bank, STATE_OPERAND)[0] != EXPECTED_STATE_WORD
        or _sha256(camera) != EXPECTED_CAMERA_SHA256
        or _sha256(windows) != EXPECTED_DIALOG_WINDOWS_SHA256
        or any(
            struct.unpack_from("<h", windows, i * DIALOG_WINDOW_STRIDE + DIALOG_WINDOW_STATUS_OFFSET)[0] != -1
            for i in range(4)
        )
    ):
        raise SurfaceSlotMigrationError("GameState/field/camera/window identity drifted")
    return {
        "ram_offset": ram_offset,
        "ram": ram,
        "resident_table": resident_table,
        "script": script,
        "dialogue": dialogue,
        "walkmesh": walkmesh,
        "loaded_header": loaded_header,
        "script_gap": script_gap,
        "dialogue_gap": dialogue_gap,
        "actor_base": actor_base,
        "actor_array": actor_array,
        "records": records,
        "offsets": offsets,
        "data": data,
        "gamestate": gamestate,
        "field_bank": field_bank,
        "camera": camera,
        "windows": windows,
    }


def migrate_v226_slot1_to_v227(
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
    old_table, new_table = _validate_resources(
        old_disc, new_disc, stage_manifest, old_header, new_header, old_script, new_script
    )
    table_diffs = _diff_triplets(old_table, new_table)
    source_payload, frame_start, source_prefix = _unpack_state(state, zstd)
    if (
        frame_start != SOURCE_PREFIX_SIZE
        or len(state) - frame_start != SOURCE_COMPRESSED_SIZE
        or _sha256(state[frame_start:]) != SOURCE_COMPRESSED_SHA256
        or _sha256(source_prefix) != SOURCE_PREFIX_SHA256
    ):
        raise SurfaceSlotMigrationError("Source frame/prefix identity drifted")
    snapshots = _validate_source(source_payload, old_table, old_header, old_script)
    resident_script = _patch_reconstruction(snapshots["script"], SCRIPT_PATCH_OFFSET, OLD_CHANGE_FIELD, NEW_CHANGE_FIELD)
    if resident_script != new_script:
        raise SurfaceSlotMigrationError("Resident V227 field-621 script reconstruction drifted")

    final = bytearray(source_payload)
    categories: dict[str, set[int]] = {"archive_table": set(), "resident_script": set(), "runtime_pc": set()}

    def install(offset: int, old: bytes, new: bytes, category: str, label: str) -> None:
        if len(old) != len(new) or final[offset : offset + len(old)] != old:
            raise SurfaceSlotMigrationError(f"Patch source drifted: {label}")
        categories[category].update(offset + i for i, (before, after) in enumerate(zip(old, new, strict=True)) if before != after)
        final[offset : offset + len(new)] = new

    for relative, old, new in table_diffs:
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
        "resident field-621 ATEL",
    )
    final_payload = bytes(final)
    expected_counts = {
        "archive_table": EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED,
        "resident_script": EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED,
        "runtime_pc": EXPECTED_RUNTIME_PC_BYTES_CHANGED,
    }
    expected_offsets = frozenset().union(*categories.values())
    actual_offsets = frozenset(_diff_offsets(source_payload, final_payload))
    if (
        {key: len(value) for key, value in categories.items()} != expected_counts
        or actual_offsets != expected_offsets
        or len(actual_offsets) != EXPECTED_PAYLOAD_BYTES_CHANGED
        or _sha256(final_payload) != OUTPUT_PAYLOAD_SHA256
    ):
        raise SurfaceSlotMigrationError("Migration changed bytes outside the exact 3,033-byte whitelist")
    output_table = final_payload[EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET : EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE]
    if _sha256(output_table) != OUTPUT_RESIDENT_TABLE_SHA256 or _diff_triplets(output_table, new_table) != RESIDENT_VS_MEDIA_DIFFS:
        raise SurfaceSlotMigrationError("V227 resident archive-table reconstruction drifted")
    if final_payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + NEW_SCRIPT_SIZE] != new_script:
        raise SurfaceSlotMigrationError("V227 resident field-621 script was not installed")

    ram_offset, result_ram = _ram_from_payload(final_payload)
    source_ram = snapshots["ram"]
    if ram_offset != snapshots["ram_offset"] or _sha256(result_ram) != OUTPUT_RAM_SHA256:
        raise SurfaceSlotMigrationError("Final V227 serialized RAM identity drifted")
    ram_diffs = _diff_offsets(source_ram, result_ram)
    if tuple(ram_offset + offset for offset in ram_diffs) != tuple(sorted(actual_offsets)):
        raise SurfaceSlotMigrationError("A payload edit escaped the serialized PSX RAM span")
    actor_base = snapshots["actor_base"]
    offsets = snapshots["offsets"]
    if result_ram[actor_base : actor_base + ACTOR_ARRAY_SIZE] != snapshots["actor_array"]:
        raise SurfaceSlotMigrationError("Field-621 actor array changed")
    for entity in range(SCRIPT_ENTITY_COUNT):
        record = result_ram[actor_base + entity * FIELD_ACTOR_STRIDE : actor_base + (entity + 1) * FIELD_ACTOR_STRIDE]
        data = result_ram[offsets[entity] : offsets[entity] + ACTOR_DATA_SIZE]
        if record != snapshots["records"][entity] or data != snapshots["data"][entity]:
            raise SurfaceSlotMigrationError(f"Field runtime e{entity} changed")
    for start, size, expected, label in (
        (GAME_STATE, GAMESTATE_SIZE, snapshots["gamestate"], "GameState/party"),
        (FIELD_SCRIPT_MEMORY, FIELD_VARIABLE_BANK_SIZE, snapshots["field_bank"], "active field variables"),
        (DIALOG_WINDOWS, DIALOG_WINDOWS_SIZE, snapshots["windows"], "dialogue windows"),
    ):
        if result_ram[start : start + size] != expected:
            raise SurfaceSlotMigrationError(f"{label} was not preserved")
    if _camera_snapshot(result_ram) != snapshots["camera"]:
        raise SurfaceSlotMigrationError("Camera was not preserved")
    for offset, size, expected, label in (
        (EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET, OLD_HEADER_SIZE, snapshots["loaded_header"], "loaded header"),
        (EXPECTED_DIALOGUE_PAYLOAD_OFFSET, DIALOGUE_SIZE, snapshots["dialogue"], "dialogue"),
        (EXPECTED_WALKMESH_PAYLOAD_OFFSET, WALKMESH_SIZE, snapshots["walkmesh"], "walkmesh"),
    ):
        if final_payload[offset : offset + size] != expected:
            raise SurfaceSlotMigrationError(f"Field-621 {label} was not preserved")
    if (
        final_payload[EXPECTED_SCRIPT_PAYLOAD_OFFSET + NEW_SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET]
        != snapshots["script_gap"]
        or final_payload[EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET]
        != snapshots["dialogue_gap"]
    ):
        raise SurfaceSlotMigrationError("Allocator/component neighbors changed")

    provisional_prefix = _expected_prefix(source_prefix, compressed_size=OUTPUT_COMPRESSED_SIZE)
    if len(_diff_offsets(source_prefix, provisional_prefix)) != EXPECTED_PREFIX_BYTES_CHANGED or _sha256(provisional_prefix) != OUTPUT_PREFIX_SHA256:
        raise SurfaceSlotMigrationError("V227 media-prefix reconstruction drifted")
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
        raise SurfaceSlotMigrationError("Final V227 state identity or round trip drifted")
    report: dict[str, object] = {
        "source_sha256": SOURCE_STATE_SHA256,
        "output_sha256": OUTPUT_STATE_SHA256,
        "source_size": len(state),
        "output_size": len(result),
        "field": EXPECTED_FIELD,
        "door_entity": DOOR_ENTITY,
        "door_helper_entity": DOOR_HELPER_ENTITY,
        "old_destination": {"field": OLD_DESTINATION_FIELD, "parameter": OLD_DESTINATION_PARAMETER},
        "new_destination": {"field": NEW_DESTINATION_FIELD, "parameter": NEW_DESTINATION_PARAMETER},
        "endpoint": "intake_treatment_preparation.treatment",
        "payload_size": len(final_payload),
        "payload_sha256": OUTPUT_PAYLOAD_SHA256,
        "payload_bytes_changed": len(actual_offsets),
        "archive_table_bytes_changed": len(categories["archive_table"]),
        "resident_script_bytes_changed": len(categories["resident_script"]),
        "runtime_actor_pc_bytes_changed": len(categories["runtime_pc"]),
        "resident_route_payload_offset": "0x11402E",
        "resident_route_script_offset": "0x1A10",
        "resident_route_pc": "0x0D4C",
        "old_change_field_bytes": OLD_CHANGE_FIELD.hex(" ").upper(),
        "new_change_field_bytes": NEW_CHANGE_FIELD.hex(" ").upper(),
        "resident_archive_table_sha256": OUTPUT_RESIDENT_TABLE_SHA256,
        "resident_archive_volatile_tail_preserved": True,
        "loaded_header_preserved": True,
        "dialogue_walkmesh_neighbors_preserved": True,
        "field_variables_preserved": True,
        "fei_e26_e34_idle_and_preserved": True,
        "all_actor_runtime_preserved": True,
        "gamestate_party_camera_windows_preserved": True,
        "allocator_safe": True,
        "round_trip_verified": True,
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "v227_stage_manifest_sha256": V227_STAGE_MANIFEST_SHA256,
        "v227_disc_sha256": NEW_DISC_SHA256,
    }
    return result, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=SOURCE_BACKUP)
    parser.add_argument("--old-disc", type=Path, default=PROJECT_ROOT / "output" / OLD_CUE_NAME.replace(".cue", ".bin"))
    parser.add_argument("--new-disc", type=Path, default=PROJECT_ROOT / "output" / NEW_CUE_NAME.replace(".cue", ".bin"))
    parser.add_argument("--stage-manifest", type=Path, default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v227_stage" / "manifest.json")
    parser.add_argument("--old-header", type=Path, default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v226_stage" / "clones" / "field_621" / "header.bin")
    parser.add_argument("--new-header", type=Path, default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v227_stage" / "clones" / "field_621" / "header.bin")
    parser.add_argument("--old-script", type=Path, default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v226_stage" / "clones" / "field_621" / "05_scripts.bin")
    parser.add_argument("--new-script", type=Path, default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v227_stage" / "clones" / "field_621" / "05_scripts.bin")
    parser.add_argument("--zstd", type=Path, default=PROJECT_ROOT / "work" / "duckstation" / "zstd.dll")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "work" / "save_candidates" / "SLUS-00669_1_v227_from_9436ef84_treatment_preparation.sav")
    parser.add_argument("--report", type=Path, default=PROJECT_ROOT / "work" / "save_candidates" / "SLUS-00669_1_v227_from_9436ef84_treatment_preparation.json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        source_path, output, report_path = args.source.resolve(), args.output.resolve(), args.report.resolve()
        if output == LIVE_SLOT1 or report_path == LIVE_SLOT1:
            raise SurfaceSlotMigrationError("Output/report may not be the live Slot 1")
        if output == source_path or report_path == source_path:
            raise SurfaceSlotMigrationError("Output/report may not replace the source state")
        if output == report_path:
            raise SurfaceSlotMigrationError("Output and report paths must be distinct")
        result, report = migrate_v226_slot1_to_v227(
            args.source.read_bytes(),
            old_disc=args.old_disc,
            new_disc=args.new_disc,
            stage_manifest=args.stage_manifest.read_bytes(),
            old_header=args.old_header.read_bytes(),
            new_header=args.new_header.read_bytes(),
            old_script=args.old_script.read_bytes(),
            new_script=args.new_script.read_bytes(),
            zstd=media_migration._Zstd(args.zstd),
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if output.read_bytes() != result or json.loads(report_path.read_text(encoding="utf-8")) != report:
            raise SurfaceSlotMigrationError("Written V227 candidate/report failed verification")
    except (OSError, ValueError, SurfaceSlotMigrationError, media_migration.StateMigrationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote V227 candidate: {output}")
    print(f"Wrote migration report: {report_path}")
    print(f"SHA-256: {report['output_sha256']}")
    print("The live Slot 1 was not modified. Install only after DuckStation is fully closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
