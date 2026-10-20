#!/usr/bin/env python3
"""Migrate the exact V228 field-549 Slot 1 state to V229 safely.

V229 narrows field 549's archive-return collision seal from script radius
``0x0E`` (28 world units) to ``0x08`` (16 world units).  The user's saved
state is already resident in that field, so mounting V229 media alone would
leave both the old ATEL operand and e16's initialized radius in RAM.

This helper is deliberately fail-closed.  It pins the exact source state,
both media sets and manifests, the sole changed field resource, the complete
resident field layout, and the exact two payload bytes that may differ.  It
reconstructs the resident archive table from the V229 media table while
preserving Xenogears' known volatile final padding byte, changes the resident
ATEL byte at payload ``0x10C74D``, and changes e16's runtime collision word at
payload ``0x11217C`` from ``1C 00`` to ``10 00``.  Fei, party/GameState,
camera, field variables, dialogue windows, and every other actor byte remain
unchanged.  The CLI never writes DuckStation's live Slot 1; it emits only a
separate candidate and JSON report.
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
import tools.migrate_surface_soylent_v227_slot1_to_v228 as previous  # noqa: E402
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
    / "SLUS-00669_1_v228_source_cd84f8b5_field549.sav"
).resolve()

SOURCE_STATE_SIZE = 1_632_883
SOURCE_STATE_SHA256 = "cd84f8b59d80398f81dc10f153633f4105be152f2c4f79b2fa73a33174debfa8"
SOURCE_PREFIX_SIZE = 0xB7D8
SOURCE_PREFIX_SHA256 = "84a9b099d3fcae320564a6d24292480e7db33d3fd00c5c885c63867b691c421d"
SOURCE_COMPRESSED_SIZE = 1_585_819
SOURCE_COMPRESSED_SHA256 = "fc5b366862ceab0b135035af9c502b278a0312424486b69ffb5fd606724c1600"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "29484159df82905db3df4d3a9d86804dec1acfcbf78d743ad63ef3b0d99dc56b"
SOURCE_RAM_SHA256 = "0855417ca928ca169a59e582b16ae106b95254d1d2c5c8a830ba2ef99f1a8abd"

OUTPUT_STATE_SIZE = 1_485_222
OUTPUT_STATE_SHA256 = "13ae2d667d8edd24ef60c1465f3e1771363823bcc4fd78c09064564a90eba21c"
OUTPUT_PREFIX_SHA256 = "309ea9dc1a8ec6e2c1d2dfbe47a244e7abb534ccc2c96051e5f4290f7021bb79"
OUTPUT_COMPRESSED_SIZE = 1_438_158
OUTPUT_COMPRESSED_SHA256 = "0f3a002be787eafc2595fd5599cac9a0e7ccf1cd75c709c0d6b7d3ed16ca051f"
OUTPUT_PAYLOAD_SHA256 = "6c05487dfbf434f01ecf2c7a11fa6a9784c4d74df0be6e1947365788e06c698e"
OUTPUT_RAM_SHA256 = "b9a8b4e8aed436bf6b0bf2ce00b499afda537db715073f4424c08f730aa48a5d"

OLD_DISC_SIZE = NEW_DISC_SIZE = 698_814_480
OLD_DISC_SHA256 = "7bdb5fd17970abb15fc36f32a0907aafd132f80eae818e79ba21473380621deb"
NEW_DISC_SHA256 = "436ecb3a053df1c6860aaedc356fa6db55d2749a27f51b4812166b117500ddc4"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v228.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v229.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = "0c3e3672f69969a0e1ced0e04d8dfc2f2298e706acf42b1c58292b4689c714fb"
NEW_CUE_SHA256 = "73812b56b1cb84b57cd8a8b1f9ecd5f67c1b983c475777dabee9d3f042c1083d"

V228_STAGE_MANIFEST_SIZE = 128_038
V228_STAGE_MANIFEST_SHA256 = "39e5b82647ecece73fb61784eae7b3cdcf490e411887765b72a58ea8ed592244"
V229_STAGE_MANIFEST_SIZE = 129_207
V229_STAGE_MANIFEST_SHA256 = "2dfba5b96913771b7cf97827d11d08c67336db190c9ebf208609dccf2d7749bf"

FIELD549_CANONICAL_ID = 1704
FIELD549_GRAPHICS_CANONICAL_ID = 1705
OLD_FIELD_BUNDLE_SIZE = NEW_FIELD_BUNDLE_SIZE = 23_336
OLD_FIELD_BUNDLE_SHA256 = "f9e1d07a20d5d602a458f9dfab2f9b746d3969000270151e869f4a1d29c88547"
NEW_FIELD_BUNDLE_SHA256 = "4ac69db0dc2abb254135a548ae882ea97334ba72f99ee62ec4d9176afc8d8a6f"
FIELD549_GRAPHICS_SIZE = 161_792
FIELD549_GRAPHICS_SHA256 = "6c4ae880e1520c174d88716008bf7c881a797e8eafb2e6b0c12b59cd050b3249"
OLD_MANIFEST_RESOURCES = {
    FIELD549_CANONICAL_ID: (OLD_FIELD_BUNDLE_SIZE, OLD_FIELD_BUNDLE_SHA256),
    FIELD549_GRAPHICS_CANONICAL_ID: (FIELD549_GRAPHICS_SIZE, FIELD549_GRAPHICS_SHA256),
}
NEW_MANIFEST_RESOURCES = {
    FIELD549_CANONICAL_ID: (NEW_FIELD_BUNDLE_SIZE, NEW_FIELD_BUNDLE_SHA256),
    FIELD549_GRAPHICS_CANONICAL_ID: (FIELD549_GRAPHICS_SIZE, FIELD549_GRAPHICS_SHA256),
}
CHANGED_RESOURCE_IDS = (FIELD549_CANONICAL_ID,)
PINNED_RESOURCE_IDS = tuple(OLD_MANIFEST_RESOURCES)

FIELD_HEADER_SIZE = 752
FIELD_HEADER_SHA256 = "a044f9447f902c2b5379f864495e974bb34157860e08d20591018cc70a8e4b2b"
COMPONENT_IDENTITIES = (
    (4, "df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119"),
    (1_648, "c110f3bb190614aad8740af9d5505126562ed68d935426aa8f78ccac5d13f321"),
    (11_328, "87d88dba39eb0b8d8fa62c00f4818986d326ed3d88537cb739c72ac45c2e9c90"),
    (6_724, "d886f360c112ac59247f3439c6dc2a800840cd153bbeed2e296b1f2db39da004"),
    (11_684, "0762607a4654cf1c8c373d21be79a48656cd203001891ee988a65568311464e0"),
    # Component five is version-specific and validated separately below.
    (3_841, ""),
    (528, "54325752ea0b7e2c679501792acf113e86495454e3a238acdaf63eaa7db06e16"),
    (2_125, "57ed56cde500d327df72112d7d47823b0e66ba25c969b90ce5d9c259a5c7401b"),
    (0, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
)

SCRIPT_SIZE = 3_841
OLD_SCRIPT_SHA256 = "8ce8194defe2125e48fd71d8c5862d8dd4fede62c52049e8d71735b3a9a9d30a"
NEW_SCRIPT_SHA256 = "04512b30bb15c4188cbe33ed714682c7d579260c5a4b42cc8ff71f9136c0a185"
SCRIPT_PATCH_OFFSET = 0xE6B
SCRIPT_DIFFS = ((SCRIPT_PATCH_OFFSET, 0x0E, 0x08),)
SCRIPT_DIFF_SHA256 = "cd8be8974ae0d90631449c1a3e977b95e5b852d7e2bb8a6f8e7b18abcf35052e"
BUNDLE_DIFFS = ((0x5531, 0x0E, 0x08),)
BUNDLE_DIFF_SHA256 = "5d5f366817e1a748e8b887c821beb14975b79200d1407d23cf8ca7b3d564494d"
SCRIPT_ENTITY_COUNT = 17
SCRIPT_BYTECODE_OFFSET = 0x4C4
SCRIPT_BYTECODE_SIZE = 0xA3D
SEAL_ENTITY = 16
SEAL_INIT_SLOT = 0
SEAL_INIT_PC = 0x0990
SEAL_VOLUME_PC = 0x09A3
SEAL_RADIUS_PC = 0x09A7
OLD_SEAL_VOLUME = bytes.fromhex("18 00 00 64 0E")
NEW_SEAL_VOLUME = bytes.fromhex("18 00 00 64 08")

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = NEW_ARCHIVE_TABLE_SHA256 = (
    "72d321cee32b79b344bd7292beea419b633d7d96244408e166cb4d4b5c2eb6b3"
)
ARCHIVE_TABLE_DIFFS: tuple[tuple[int, int, int], ...] = ()
ARCHIVE_TABLE_DIFF_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
SOURCE_RESIDENT_TABLE_SHA256 = OUTPUT_RESIDENT_TABLE_SHA256 = (
    "13d23b9b2f983cba4b0883e58cd2b083126642284957fe752ae821e9b0c5a727"
)
RESIDENT_VS_MEDIA_DIFFS = ((0x7FFF, 0xE0, 0x00),)

EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
EXPECTED_FIELD = 549
GAME_SCENE_MAP = 0x04F34C
EXPECTED_GAME_SCENE_MAP = 0x0225
EXPECTED_ACTOR_COUNT = 22
SCRIPT_ACTOR_COUNT = SCRIPT_ENTITY_COUNT
EXPECTED_ACTOR_ARRAY_GUEST_POINTER = 0x8010D700
EXPECTED_SCRIPT_GUEST_POINTER = 0x80109E80
EXPECTED_VM_SCRIPT_GUEST_POINTER = 0x8010A344
EXPECTED_VM_ACTOR_GUEST_POINTER = 0x801106FC

EXPECTED_SCRIPT_PAYLOAD_OFFSET = 0x10B8E2
EXPECTED_SCRIPT_PATCH_PAYLOAD_OFFSET = 0x10C74D
EXPECTED_DIALOGUE_PAYLOAD_OFFSET = 0x10C816
EXPECTED_WALKMESH_PAYLOAD_OFFSET = 0x10D07E
EXPECTED_CACHED_HEADER_PAYLOAD_OFFSET = 0x1EF3DE
DIALOGUE_SIZE = 2_125
DIALOGUE_SHA256 = COMPONENT_IDENTITIES[7][1]
WALKMESH_SIZE = 1_648
WALKMESH_SHA256 = COMPONENT_IDENTITIES[1][1]
SCRIPT_GAP_SIZE = 51
SCRIPT_GAP_SHA256 = "04dd92d7fe3b65592060bef6eecac3b9f9f7ff7d3df66fa8a91b716229d9ed20"
DIALOGUE_GAP_SIZE = 27
DIALOGUE_GAP_SHA256 = "eb403630c0bbc65993106b029a22375e50fb21ba4b9f689aa318339383849903"

ACTOR_ARRAY_SIZE = EXPECTED_ACTOR_COUNT * FIELD_ACTOR_STRIDE
ACTOR_DATA_SIZE = 0x138
ACTOR_CURRENT_PC_OFFSET = 0xCC
ACTOR_CURRENT_SLOT_OFFSET = 0xCE
ACTOR_POSITION_OFFSET = 0x20
ACTOR_COLLISION_VOLUME_OFFSET = 0x18
ACTOR_COLLISION_RADIUS_OFFSET = 0x1E
FEI_ENTITY = 1
EXPECTED_FEI_DATA_OFFSET = 0x10E0A8
EXPECTED_FEI_POSITION = (-12_702_524, 0, 16_007_409)
SOURCE_FEI_DATA_SHA256 = "517bdcedbd0748333d00a74c81b4104f73b6b1840f07cb9d03cc4300250bdb43"
EXPECTED_SEAL_DATA_OFFSET = 0x1106FC
EXPECTED_SEAL_POSITION = (-15_728_640, 0, 15_728_640)
EXPECTED_RUNTIME_RADIUS_RAM_OFFSET = 0x11071A
EXPECTED_RUNTIME_RADIUS_PAYLOAD_OFFSET = 0x11217C
OLD_RUNTIME_RADIUS = bytes.fromhex("1C 00")
NEW_RUNTIME_RADIUS = bytes.fromhex("10 00")
OLD_RUNTIME_COLLISION_VOLUME = bytes.fromhex("10 00 C8 00 10 00 1C 00")
NEW_RUNTIME_COLLISION_VOLUME = bytes.fromhex("10 00 C8 00 10 00 10 00")
SOURCE_SEAL_DATA_SHA256 = "fd40267114c0f5b6556390556b126792101f203aad09477a6e428cfd3da95095"
OUTPUT_SEAL_DATA_SHA256 = "017e3a25acfc41e687ad0bc97c24c2347191dc952b0d826d4bfb9bb4ec14efe7"
SOURCE_ACTOR_ARRAY_SHA256 = "45db0b886a51feada82e14178fde9bbf4dc84a587beb384d71d7bd4000a7be50"
SOURCE_ACTOR_DATA_SHA256 = "a9c0b79504987f68fe2a821b6af7a3898cf91d30282f41a275ff51eecde4085c"
OUTPUT_ACTOR_DATA_SHA256 = "9ad62814c7e24f058116161270748f29b43d9d752f1b8e7275923800bf78ca6c"
EXPECTED_ACTOR_DATA_OFFSETS = (
    0x10DEF0,
    0x10E0A8,
    0x10E260,
    0x10E418,
    0x10E5D0,
    0x10E788,
    0x10E940,
    0x10EC6C,
    0x10EF98,
    0x10F484,
    0x10F7B0,
    0x10FC1C,
    0x10FF48,
    0x1101D4,
    0x11038C,
    0x110544,
    0x1106FC,
)
EXPECTED_CURRENT_PCS = (
    0x006F,
    0x0088,
    0x00B9,
    0x00C4,
    0x00D7,
    0x0190,
    0x01B3,
    0x01CA,
    0x01D4,
    0x0258,
    0x02DC,
    0x0360,
    0x03E4,
    0x0468,
    0x04F5,
    0x059B,
    0x0973,
)

FIELD_VARIABLE_BANK_SIZE = 0x400
FIELD_VARIABLE_BACKUP_OFFSET = 0x48
DIALOG_WINDOWS = 0x0C2698
DIALOG_WINDOW_STRIDE = 0xB0
DIALOG_WINDOWS_SIZE = 4 * DIALOG_WINDOW_STRIDE
EXPECTED_GAMESTATE_SHA256 = "edb14890ed45143196cf5e433e47d9ac169b4d2fca90c45c6e13215884a8d971"
EXPECTED_FIELD_VARIABLE_BANK_SHA256 = "1b9dfda85260b3f4df8b22ffc12e22b283226bd27fd9eca5b65b246cbefe17d4"
EXPECTED_BACKUP_VARIABLE_BANK_SHA256 = "daf360be2171a62a2a3e564fadfc08c699216dd65fe53b7044afb873107ead1e"
EXPECTED_DIALOG_WINDOWS_SHA256 = "72ebc6eba54d8be461afa74fe720550044a844dc83ee96baab224eeae9578e08"
EXPECTED_CAMERA_SHA256 = "316b871f775bce1e71d9723b56f86a5e36df2c757e94fd7b694c6b322fea4d7b"

EXPECTED_PAYLOAD_CHANGED_OFFSETS = (
    EXPECTED_SCRIPT_PATCH_PAYLOAD_OFFSET,
    EXPECTED_RUNTIME_RADIUS_PAYLOAD_OFFSET,
)
EXPECTED_PAYLOAD_BYTES_CHANGED = len(EXPECTED_PAYLOAD_CHANGED_OFFSETS)
EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED = 0
EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED = 1
EXPECTED_RUNTIME_RADIUS_BYTES_CHANGED = 1
EXPECTED_PREFIX_BYTES_CHANGED = 4


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
    return previous._triplet_digest(diffs)


def _unpack_state(state: bytes, zstd: _ZstdLike) -> tuple[bytes, int, bytes]:
    return previous._unpack_state(state, zstd)


def _pack_state(prefix: bytes, payload: bytes, zstd: _ZstdLike) -> bytes:
    return previous._pack_state(prefix, payload, zstd)


def _patch_reconstruction(source: bytes, offset: int, old: bytes, new: bytes) -> bytes:
    if len(old) != len(new) or source[offset : offset + len(old)] != old:
        raise SurfaceSlotMigrationError(f"Patch source drifted at 0x{offset:X}")
    result = bytearray(source)
    result[offset : offset + len(new)] = new
    return bytes(result)


def _expected_prefix(source_prefix: bytes, *, compressed_size: int) -> bytes:
    old_name, new_name = OLD_CUE_NAME.encode("ascii"), NEW_CUE_NAME.encode("ascii")
    if (
        len(old_name) != len(new_name)
        or source_prefix.count(old_name) != 1
        or source_prefix.count(new_name)
    ):
        raise SurfaceSlotMigrationError("Pinned V228 media path changed")
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
        raise SurfaceSlotMigrationError("Serialized PSX RAM is incomplete")
    return offset, ram


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


def _disc_field549(
    disc: Path,
    *,
    size: int,
    sha256: str,
    label: str,
) -> tuple[bytes, ParsedField]:
    try:
        bundle = _disc_resource(
            Mode2Image(disc), FIELD549_CANONICAL_ID, size, sha256, label
        )
        parsed = parse_field(bundle)
    except (DiscFormatError, FieldFormatError) as exc:
        raise SurfaceSlotMigrationError(f"Cannot decode {label}: {exc}") from exc
    if len(parsed.parts) != 9:
        raise SurfaceSlotMigrationError(f"{label} component layout drifted")
    return bundle, parsed


def _validate_atel_contract(old_script: bytes, new_script: bytes) -> None:
    for blob, sha256, label in (
        (old_script, OLD_SCRIPT_SHA256, "V228 field-549 script"),
        (new_script, NEW_SCRIPT_SHA256, "V229 field-549 script"),
    ):
        if (len(blob), _sha256(blob)) != (SCRIPT_SIZE, sha256):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    script_diffs = _diff_triplets(old_script, new_script)
    if (
        script_diffs != SCRIPT_DIFFS
        or _triplet_digest(script_diffs) != SCRIPT_DIFF_SHA256
        or _patch_reconstruction(
            old_script,
            SCRIPT_PATCH_OFFSET,
            bytes((SCRIPT_DIFFS[0][1],)),
            bytes((SCRIPT_DIFFS[0][2],)),
        )
        != new_script
    ):
        raise SurfaceSlotMigrationError("V228/V229 field-549 script delta drifted")

    old_atel, new_atel = AtelScript(old_script), AtelScript(new_script)
    old_pointers = tuple(
        old_atel.get_script_pointer(entity, slot)
        for entity in range(SCRIPT_ENTITY_COUNT)
        for slot in range(32)
    )
    new_pointers = tuple(
        new_atel.get_script_pointer(entity, slot)
        for entity in range(SCRIPT_ENTITY_COUNT)
        for slot in range(32)
    )
    if (
        old_atel.entity_count != SCRIPT_ENTITY_COUNT
        or new_atel.entity_count != SCRIPT_ENTITY_COUNT
        or (old_atel.bytecode_offset, old_atel.bytecode_size)
        != (SCRIPT_BYTECODE_OFFSET, SCRIPT_BYTECODE_SIZE)
        or (new_atel.bytecode_offset, new_atel.bytecode_size)
        != (SCRIPT_BYTECODE_OFFSET, SCRIPT_BYTECODE_SIZE)
        or old_pointers != new_pointers
        or old_atel.get_script_pointer(SEAL_ENTITY, SEAL_INIT_SLOT) != SEAL_INIT_PC
        or new_atel.get_script_pointer(SEAL_ENTITY, SEAL_INIT_SLOT) != SEAL_INIT_PC
        or old_atel.bytecode[SEAL_VOLUME_PC : SEAL_VOLUME_PC + len(OLD_SEAL_VOLUME)]
        != OLD_SEAL_VOLUME
        or new_atel.bytecode[SEAL_VOLUME_PC : SEAL_VOLUME_PC + len(NEW_SEAL_VOLUME)]
        != NEW_SEAL_VOLUME
        or SCRIPT_BYTECODE_OFFSET + SEAL_RADIUS_PC != SCRIPT_PATCH_OFFSET
    ):
        raise SurfaceSlotMigrationError("V228/V229 field-549 ATEL topology drifted")


def _validate_media(
    old_disc: Path,
    new_disc: Path,
    old_manifest: bytes,
    new_manifest: bytes,
    old_header: bytes,
    new_header: bytes,
    old_script: bytes,
    new_script: bytes,
) -> tuple[bytes, bytes]:
    for path, size, sha256, label in (
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V228 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V229 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V228 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V229 CUE"),
    ):
        _validate_file(path, size, sha256, label)

    old_inventory = _manifest_inventory(
        old_manifest,
        size=V228_STAGE_MANIFEST_SIZE,
        sha256=V228_STAGE_MANIFEST_SHA256,
        label="V228 stage manifest",
    )
    new_inventory = _manifest_inventory(
        new_manifest,
        size=V229_STAGE_MANIFEST_SIZE,
        sha256=V229_STAGE_MANIFEST_SHA256,
        label="V229 stage manifest",
    )
    for canonical_id in PINNED_RESOURCE_IDS:
        if old_inventory.get(canonical_id) != OLD_MANIFEST_RESOURCES[canonical_id]:
            raise SurfaceSlotMigrationError(f"V228 manifest resource {canonical_id} drifted")
        if new_inventory.get(canonical_id) != NEW_MANIFEST_RESOURCES[canonical_id]:
            raise SurfaceSlotMigrationError(f"V229 manifest resource {canonical_id} drifted")
    changed = tuple(
        sorted(
            canonical_id
            for canonical_id in old_inventory.keys() | new_inventory.keys()
            if old_inventory.get(canonical_id) != new_inventory.get(canonical_id)
        )
    )
    if changed != CHANGED_RESOURCE_IDS:
        raise SurfaceSlotMigrationError("V228/V229 replacement-inventory change set drifted")

    for blob, label in (
        (old_header, "V228 field-549 header clone"),
        (new_header, "V229 field-549 header clone"),
    ):
        if (len(blob), _sha256(blob)) != (FIELD_HEADER_SIZE, FIELD_HEADER_SHA256):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    if old_header != new_header:
        raise SurfaceSlotMigrationError("V229 changed the field-549 header")
    _validate_atel_contract(old_script, new_script)

    try:
        old_image, new_image = Mode2Image(old_disc), Mode2Image(new_disc)
        for canonical_id in PINNED_RESOURCE_IDS:
            _disc_resource(
                old_image,
                canonical_id,
                *OLD_MANIFEST_RESOURCES[canonical_id],
                f"V228 resource {canonical_id}",
            )
            _disc_resource(
                new_image,
                canonical_id,
                *NEW_MANIFEST_RESOURCES[canonical_id],
                f"V229 resource {canonical_id}",
            )
        old_bundle, old_field = _disc_field549(
            old_disc,
            size=OLD_FIELD_BUNDLE_SIZE,
            sha256=OLD_FIELD_BUNDLE_SHA256,
            label="V228 field-549 bundle",
        )
        new_bundle, new_field = _disc_field549(
            new_disc,
            size=NEW_FIELD_BUNDLE_SIZE,
            sha256=NEW_FIELD_BUNDLE_SHA256,
            label="V229 field-549 bundle",
        )
    except DiscFormatError as exc:
        raise SurfaceSlotMigrationError(f"Cannot validate V228/V229 resources: {exc}") from exc

    bundle_diffs = _diff_triplets(old_bundle, new_bundle)
    if bundle_diffs != BUNDLE_DIFFS or _triplet_digest(bundle_diffs) != BUNDLE_DIFF_SHA256:
        raise SurfaceSlotMigrationError("V228/V229 packed field-549 delta drifted")
    if old_field.header != old_header or new_field.header != new_header:
        raise SurfaceSlotMigrationError("Field-549 disc/header clone identity drifted")
    for index, (old_part, new_part) in enumerate(zip(old_field.parts, new_field.parts, strict=True)):
        if index == 5:
            if old_part.data != old_script or new_part.data != new_script:
                raise SurfaceSlotMigrationError("Field-549 decoded script clone drifted")
            continue
        expected_size, expected_sha = COMPONENT_IDENTITIES[index]
        if (
            old_part.data != new_part.data
            or (len(old_part.data), _sha256(old_part.data)) != (expected_size, expected_sha)
        ):
            raise SurfaceSlotMigrationError(f"Field-549 component {index} changed")

    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    table_diffs = _diff_triplets(old_table, new_table)
    if (
        len(old_table) != ARCHIVE_TABLE_SIZE
        or _sha256(old_table) != OLD_ARCHIVE_TABLE_SHA256
        or _sha256(new_table) != NEW_ARCHIVE_TABLE_SHA256
        or table_diffs != ARCHIVE_TABLE_DIFFS
        or _triplet_digest(table_diffs) != ARCHIVE_TABLE_DIFF_SHA256
        or old_table != new_table
    ):
        raise SurfaceSlotMigrationError("V228/V229 archive-table identity drifted")
    return old_table, new_table


def _actor_data_offset(ram: bytes, actor_base: int, entity: int) -> int:
    pointer = struct.unpack_from(
        "<I",
        ram,
        actor_base + entity * FIELD_ACTOR_STRIDE + FIELD_ACTOR_DATA_POINTER,
    )[0]
    offset = pointer & 0x1FFFFFFF
    if not 0 < offset <= RAM_SIZE - ACTOR_DATA_SIZE:
        raise SurfaceSlotMigrationError(f"e{entity} ActorData pointer drifted")
    return offset


def _validate_source(
    payload: bytes,
    *,
    old_table: bytes,
    old_script: bytes,
) -> dict[str, object]:
    if (len(payload), _sha256(payload)) != (SOURCE_PAYLOAD_SIZE, SOURCE_PAYLOAD_SHA256):
        raise SurfaceSlotMigrationError("V228 decompressed payload identity drifted")
    ram_offset, ram = _ram_from_payload(payload)
    if _sha256(ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("V228 serialized RAM identity drifted")

    table = payload[
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
    ]
    script = payload[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + SCRIPT_SIZE
    ]
    dialogue = payload[
        EXPECTED_DIALOGUE_PAYLOAD_OFFSET : EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE
    ]
    walkmesh = payload[
        EXPECTED_WALKMESH_PAYLOAD_OFFSET : EXPECTED_WALKMESH_PAYLOAD_OFFSET + WALKMESH_SIZE
    ]
    cached_header = payload[
        EXPECTED_CACHED_HEADER_PAYLOAD_OFFSET :
        EXPECTED_CACHED_HEADER_PAYLOAD_OFFSET + FIELD_HEADER_SIZE
    ]
    script_gap = payload[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET + SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET
    ]
    dialogue_gap = payload[
        EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET
    ]
    if (
        _sha256(table) != SOURCE_RESIDENT_TABLE_SHA256
        or _diff_triplets(table, old_table) != RESIDENT_VS_MEDIA_DIFFS
        or script != old_script
        or payload.count(old_script) != 1
        or script[SCRIPT_PATCH_OFFSET] != 0x0E
        or (len(dialogue), _sha256(dialogue)) != (DIALOGUE_SIZE, DIALOGUE_SHA256)
        or (len(walkmesh), _sha256(walkmesh)) != (WALKMESH_SIZE, WALKMESH_SHA256)
        or (len(cached_header), _sha256(cached_header)) != (FIELD_HEADER_SIZE, FIELD_HEADER_SHA256)
        or (len(script_gap), _sha256(script_gap)) != (SCRIPT_GAP_SIZE, SCRIPT_GAP_SHA256)
        or (len(dialogue_gap), _sha256(dialogue_gap)) != (DIALOGUE_GAP_SIZE, DIALOGUE_GAP_SHA256)
        or EXPECTED_SCRIPT_PAYLOAD_OFFSET + SCRIPT_PATCH_OFFSET
        != EXPECTED_SCRIPT_PATCH_PAYLOAD_OFFSET
    ):
        raise SurfaceSlotMigrationError("Resident V228 field-549 identity drifted")

    actor_pointer = struct.unpack_from("<I", ram, FIELD_ACTORS)[0]
    if (
        struct.unpack_from("<I", ram, GAME_SCENE_MAP)[0] != EXPECTED_GAME_SCENE_MAP
        or (EXPECTED_GAME_SCENE_MAP & 0xFFF) != EXPECTED_FIELD
        or struct.unpack_from("<I", ram, FIELD_NUM_ACTORS)[0] != EXPECTED_ACTOR_COUNT
        or actor_pointer != EXPECTED_ACTOR_ARRAY_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0]
        != EXPECTED_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA)[0]
        != EXPECTED_VM_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_ACTOR)[0]
        != EXPECTED_VM_ACTOR_GUEST_POINTER
    ):
        raise SurfaceSlotMigrationError("Live field-549 pointer topology drifted")

    actor_base = actor_pointer & 0x1FFFFFFF
    actor_array = bytes(ram[actor_base : actor_base + ACTOR_ARRAY_SIZE])
    records = tuple(
        bytes(
            ram[
                actor_base + entity * FIELD_ACTOR_STRIDE :
                actor_base + (entity + 1) * FIELD_ACTOR_STRIDE
            ]
        )
        for entity in range(EXPECTED_ACTOR_COUNT)
    )
    offsets = tuple(
        _actor_data_offset(ram, actor_base, entity)
        for entity in range(SCRIPT_ACTOR_COUNT)
    )
    data = tuple(bytes(ram[offset : offset + ACTOR_DATA_SIZE]) for offset in offsets)
    if (
        offsets != EXPECTED_ACTOR_DATA_OFFSETS
        or _sha256(actor_array) != SOURCE_ACTOR_ARRAY_SHA256
        or _sha256(b"".join(data)) != SOURCE_ACTOR_DATA_SHA256
    ):
        raise SurfaceSlotMigrationError("Live field-549 actor allocation identity drifted")
    atel = AtelScript(script)
    for entity, (actor, expected_pc) in enumerate(zip(data, EXPECTED_CURRENT_PCS, strict=True)):
        pc = struct.unpack_from("<H", actor, ACTOR_CURRENT_PC_OFFSET)[0]
        slot = actor[ACTOR_CURRENT_SLOT_OFFSET]
        if pc != expected_pc or slot != 0 or atel.bytecode[pc] != 0x00:
            raise SurfaceSlotMigrationError(f"e{entity} is not idle at the pinned STOP")

    fei, seal = data[FEI_ENTITY], data[SEAL_ENTITY]
    if (
        offsets[FEI_ENTITY] != EXPECTED_FEI_DATA_OFFSET
        or _sha256(fei) != SOURCE_FEI_DATA_SHA256
        or struct.unpack_from("<3i", fei, ACTOR_POSITION_OFFSET) != EXPECTED_FEI_POSITION
        or offsets[SEAL_ENTITY] != EXPECTED_SEAL_DATA_OFFSET
        or _sha256(seal) != SOURCE_SEAL_DATA_SHA256
        or struct.unpack_from("<3i", seal, ACTOR_POSITION_OFFSET) != EXPECTED_SEAL_POSITION
        or seal[
            ACTOR_COLLISION_VOLUME_OFFSET :
            ACTOR_COLLISION_VOLUME_OFFSET + len(OLD_RUNTIME_COLLISION_VOLUME)
        ]
        != OLD_RUNTIME_COLLISION_VOLUME
        or ram[
            EXPECTED_RUNTIME_RADIUS_RAM_OFFSET : EXPECTED_RUNTIME_RADIUS_RAM_OFFSET + 2
        ]
        != OLD_RUNTIME_RADIUS
        or ram_offset + EXPECTED_RUNTIME_RADIUS_RAM_OFFSET
        != EXPECTED_RUNTIME_RADIUS_PAYLOAD_OFFSET
    ):
        raise SurfaceSlotMigrationError("Live e16 collision or Fei stance drifted")

    gamestate = bytes(ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE])
    field_bank = bytes(ram[FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE])
    backup_bank = bytes(
        ram[
            GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET :
            GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET + FIELD_VARIABLE_BANK_SIZE
        ]
    )
    windows = bytes(ram[DIALOG_WINDOWS : DIALOG_WINDOWS + DIALOG_WINDOWS_SIZE])
    camera = _camera_snapshot(ram)
    if (
        _sha256(gamestate) != EXPECTED_GAMESTATE_SHA256
        or _sha256(field_bank) != EXPECTED_FIELD_VARIABLE_BANK_SHA256
        or _sha256(backup_bank) != EXPECTED_BACKUP_VARIABLE_BANK_SHA256
        or _sha256(windows) != EXPECTED_DIALOG_WINDOWS_SHA256
        or _sha256(camera) != EXPECTED_CAMERA_SHA256
    ):
        raise SurfaceSlotMigrationError("GameState/field/camera/window identity drifted")
    return {
        "ram_offset": ram_offset,
        "ram": ram,
        "table": table,
        "script": script,
        "dialogue": dialogue,
        "walkmesh": walkmesh,
        "cached_header": cached_header,
        "script_gap": script_gap,
        "dialogue_gap": dialogue_gap,
        "actor_base": actor_base,
        "actor_array": actor_array,
        "records": records,
        "offsets": offsets,
        "data": data,
        "gamestate": gamestate,
        "field_bank": field_bank,
        "backup_bank": backup_bank,
        "windows": windows,
        "camera": camera,
    }


def _rebuild_resident_table(source_table: bytes, new_media_table: bytes) -> bytes:
    """Return the V229 media table with the known volatile tail restored."""

    if (
        len(source_table) != ARCHIVE_TABLE_SIZE
        or len(new_media_table) != ARCHIVE_TABLE_SIZE
        or _diff_triplets(source_table, new_media_table) != RESIDENT_VS_MEDIA_DIFFS
    ):
        raise SurfaceSlotMigrationError("Resident archive-table source drifted")
    rebuilt = bytearray(new_media_table)
    for offset, resident, media in RESIDENT_VS_MEDIA_DIFFS:
        if source_table[offset] != resident or new_media_table[offset] != media:
            raise SurfaceSlotMigrationError("Resident archive volatile-byte contract drifted")
        rebuilt[offset] = resident
    result = bytes(rebuilt)
    if (
        _sha256(result) != OUTPUT_RESIDENT_TABLE_SHA256
        or _diff_triplets(result, new_media_table) != RESIDENT_VS_MEDIA_DIFFS
    ):
        raise SurfaceSlotMigrationError("V229 resident archive-table reconstruction drifted")
    return result


def migrate_v228_slot1_to_v229(
    state: bytes,
    *,
    old_disc: Path,
    new_disc: Path,
    old_manifest: bytes,
    new_manifest: bytes,
    old_header: bytes,
    new_header: bytes,
    old_script: bytes,
    new_script: bytes,
    zstd: _ZstdLike,
) -> tuple[bytes, dict[str, object]]:
    """Return the exact separately writable V229 state candidate and report."""

    source_sha = _sha256(state)
    if (len(state), source_sha) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise SurfaceSlotMigrationError(
            f"Source Slot 1 identity is {len(state)} / {source_sha}, expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    old_name, new_name = OLD_CUE_NAME.encode("ascii"), NEW_CUE_NAME.encode("ascii")
    if (
        len(old_name) != len(new_name)
        or state.count(old_name) != 1
        or state.count(new_name)
    ):
        raise SurfaceSlotMigrationError("Source CUE identity drifted")

    old_table, new_table = _validate_media(
        old_disc,
        new_disc,
        old_manifest,
        new_manifest,
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
    snapshots = _validate_source(source_payload, old_table=old_table, old_script=old_script)

    final = bytearray(source_payload)
    rebuilt_table = _rebuild_resident_table(snapshots["table"], new_table)
    final[
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
    ] = rebuilt_table
    if final[EXPECTED_SCRIPT_PATCH_PAYLOAD_OFFSET] != 0x0E:
        raise SurfaceSlotMigrationError("Resident ATEL radius source byte drifted")
    final[EXPECTED_SCRIPT_PATCH_PAYLOAD_OFFSET] = 0x08
    if (
        final[
            EXPECTED_RUNTIME_RADIUS_PAYLOAD_OFFSET :
            EXPECTED_RUNTIME_RADIUS_PAYLOAD_OFFSET + 2
        ]
        != OLD_RUNTIME_RADIUS
    ):
        raise SurfaceSlotMigrationError("Runtime e16 radius source word drifted")
    final[
        EXPECTED_RUNTIME_RADIUS_PAYLOAD_OFFSET :
        EXPECTED_RUNTIME_RADIUS_PAYLOAD_OFFSET + 2
    ] = NEW_RUNTIME_RADIUS
    final_payload = bytes(final)
    actual_offsets = _diff_offsets(source_payload, final_payload)
    if (
        actual_offsets != EXPECTED_PAYLOAD_CHANGED_OFFSETS
        or len(actual_offsets) != EXPECTED_PAYLOAD_BYTES_CHANGED
        or _sha256(final_payload) != OUTPUT_PAYLOAD_SHA256
    ):
        raise SurfaceSlotMigrationError("Migration escaped the exact ATEL/runtime whitelist")

    output_table = final_payload[
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
    ]
    output_script = final_payload[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + SCRIPT_SIZE
    ]
    if (
        output_table != rebuilt_table
        or _sha256(output_table) != OUTPUT_RESIDENT_TABLE_SHA256
        or _diff_triplets(output_table, new_table) != RESIDENT_VS_MEDIA_DIFFS
        or output_script != new_script
        or final_payload.count(old_script) != 0
        or final_payload.count(new_script) != 1
    ):
        raise SurfaceSlotMigrationError("Final resident field-549 media state drifted")
    for offset, expected, label in (
        (EXPECTED_DIALOGUE_PAYLOAD_OFFSET, snapshots["dialogue"], "dialogue"),
        (EXPECTED_WALKMESH_PAYLOAD_OFFSET, snapshots["walkmesh"], "walkmesh"),
        (EXPECTED_CACHED_HEADER_PAYLOAD_OFFSET, snapshots["cached_header"], "cached header"),
    ):
        if final_payload[offset : offset + len(expected)] != expected:
            raise SurfaceSlotMigrationError(f"Resident field-549 {label} changed")

    ram_offset, result_ram = _ram_from_payload(final_payload)
    if ram_offset != snapshots["ram_offset"] or _sha256(result_ram) != OUTPUT_RAM_SHA256:
        raise SurfaceSlotMigrationError("Final V229 serialized RAM identity drifted")
    source_ram = snapshots["ram"]
    expected_ram_offsets = tuple(
        offset - ram_offset for offset in EXPECTED_PAYLOAD_CHANGED_OFFSETS
    )
    if _diff_offsets(source_ram, result_ram) != expected_ram_offsets:
        raise SurfaceSlotMigrationError("A payload edit escaped the serialized PSX RAM span")

    actor_base = snapshots["actor_base"]
    if result_ram[actor_base : actor_base + ACTOR_ARRAY_SIZE] != snapshots["actor_array"]:
        raise SurfaceSlotMigrationError("Field-549 actor array changed")
    result_data = []
    for entity in range(SCRIPT_ACTOR_COUNT):
        record = result_ram[
            actor_base + entity * FIELD_ACTOR_STRIDE :
            actor_base + (entity + 1) * FIELD_ACTOR_STRIDE
        ]
        data_offset = snapshots["offsets"][entity]
        actor = bytes(result_ram[data_offset : data_offset + ACTOR_DATA_SIZE])
        if record != snapshots["records"][entity]:
            raise SurfaceSlotMigrationError(f"Field actor record e{entity} changed")
        if entity == SEAL_ENTITY:
            if (
                _diff_offsets(snapshots["data"][entity], actor)
                != (ACTOR_COLLISION_RADIUS_OFFSET,)
                or _sha256(actor) != OUTPUT_SEAL_DATA_SHA256
                or actor[
                    ACTOR_COLLISION_VOLUME_OFFSET :
                    ACTOR_COLLISION_VOLUME_OFFSET + len(NEW_RUNTIME_COLLISION_VOLUME)
                ]
                != NEW_RUNTIME_COLLISION_VOLUME
            ):
                raise SurfaceSlotMigrationError("Runtime e16 collision repair drifted")
        elif actor != snapshots["data"][entity]:
            raise SurfaceSlotMigrationError(f"Unrelated field runtime e{entity} changed")
        result_data.append(actor)
    if _sha256(b"".join(result_data)) != OUTPUT_ACTOR_DATA_SHA256:
        raise SurfaceSlotMigrationError("Final ActorData identity drifted")

    for start, size, expected, label in (
        (GAME_STATE, GAMESTATE_SIZE, snapshots["gamestate"], "GameState/party"),
        (FIELD_SCRIPT_MEMORY, FIELD_VARIABLE_BANK_SIZE, snapshots["field_bank"], "field variables"),
        (
            GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET,
            FIELD_VARIABLE_BANK_SIZE,
            snapshots["backup_bank"],
            "backup field variables",
        ),
        (DIALOG_WINDOWS, DIALOG_WINDOWS_SIZE, snapshots["windows"], "dialogue windows"),
    ):
        if result_ram[start : start + size] != expected:
            raise SurfaceSlotMigrationError(f"{label} changed")
    if _camera_snapshot(result_ram) != snapshots["camera"]:
        raise SurfaceSlotMigrationError("Camera changed")
    if result_data[FEI_ENTITY] != snapshots["data"][FEI_ENTITY]:
        raise SurfaceSlotMigrationError("Fei runtime state changed")

    provisional_prefix = _expected_prefix(
        source_prefix,
        compressed_size=OUTPUT_COMPRESSED_SIZE,
    )
    if (
        len(_diff_offsets(source_prefix, provisional_prefix)) != EXPECTED_PREFIX_BYTES_CHANGED
        or _sha256(provisional_prefix) != OUTPUT_PREFIX_SHA256
    ):
        raise SurfaceSlotMigrationError("V229 media-prefix reconstruction drifted")
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
        raise SurfaceSlotMigrationError("Final V229 state identity or round trip drifted")

    report: dict[str, object] = {
        "source_sha256": SOURCE_STATE_SHA256,
        "output_sha256": OUTPUT_STATE_SHA256,
        "source_size": len(state),
        "output_size": len(result),
        "field": EXPECTED_FIELD,
        "payload_size": len(final_payload),
        "payload_sha256": OUTPUT_PAYLOAD_SHA256,
        "ram_sha256": OUTPUT_RAM_SHA256,
        "compressed_payload_size": OUTPUT_COMPRESSED_SIZE,
        "compressed_payload_sha256": OUTPUT_COMPRESSED_SHA256,
        "payload_bytes_changed": len(actual_offsets),
        "payload_changed_offsets": [f"0x{offset:X}" for offset in actual_offsets],
        "archive_table_bytes_changed": EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED,
        "resident_script_bytes_changed": EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED,
        "runtime_e16_radius_bytes_changed": EXPECTED_RUNTIME_RADIUS_BYTES_CHANGED,
        "runtime_e16_radius_before": 28,
        "runtime_e16_radius_after": 16,
        "effective_closed_radius_before": 44,
        "effective_closed_radius_after": 32,
        "changed_resource_ids": list(CHANGED_RESOURCE_IDS),
        "resident_archive_table_sha256": OUTPUT_RESIDENT_TABLE_SHA256,
        "v228_v229_media_archive_tables_identical": True,
        "resident_archive_table_rebuilt_for_v229": True,
        "resident_archive_volatile_tail_preserved": True,
        "resident_field549_script_matches_v229": True,
        "fei_party_gamestate_field_camera_windows_preserved": True,
        "all_unrelated_actor_runtime_preserved": True,
        "allocator_safe": True,
        "round_trip_verified": True,
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "v228_stage_manifest_sha256": V228_STAGE_MANIFEST_SHA256,
        "v229_stage_manifest_sha256": V229_STAGE_MANIFEST_SHA256,
        "v228_disc_sha256": OLD_DISC_SHA256,
        "v229_disc_sha256": NEW_DISC_SHA256,
    }
    return result, report


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
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v228_stage" / "manifest.json",
    )
    parser.add_argument(
        "--new-manifest",
        type=Path,
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v229_stage" / "manifest.json",
    )
    parser.add_argument(
        "--old-header",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "surface_soylent_campaign_v228_stage"
            / "clones"
            / "field_549_disc1_donor"
            / "header.bin"
        ),
    )
    parser.add_argument(
        "--new-header",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "surface_soylent_campaign_v229_stage"
            / "clones"
            / "field_549_disc1_donor"
            / "header.bin"
        ),
    )
    parser.add_argument(
        "--old-script",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "surface_soylent_campaign_v228_stage"
            / "clones"
            / "field_549_disc1_donor"
            / "05_scripts.bin"
        ),
    )
    parser.add_argument(
        "--new-script",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "surface_soylent_campaign_v229_stage"
            / "clones"
            / "field_549_disc1_donor"
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
            / "SLUS-00669_1_v229_from_cd84f8b5_field549_seal.sav"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "save_candidates"
            / "SLUS-00669_1_v229_from_cd84f8b5_field549_seal.json"
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
        result, report = migrate_v228_slot1_to_v229(
            source_path.read_bytes(),
            old_disc=args.old_disc,
            new_disc=args.new_disc,
            old_manifest=args.old_manifest.read_bytes(),
            new_manifest=args.new_manifest.read_bytes(),
            old_header=args.old_header.read_bytes(),
            new_header=args.new_header.read_bytes(),
            old_script=args.old_script.read_bytes(),
            new_script=args.new_script.read_bytes(),
            zstd=media_migration._Zstd(args.zstd),
        )
        if output.exists() and output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Refusing to overwrite a different V229 candidate")
        if report_path.exists():
            try:
                existing_report = json.loads(report_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                raise SurfaceSlotMigrationError("Refusing to overwrite an unreadable report") from exc
            if existing_report != report:
                raise SurfaceSlotMigrationError("Refusing to overwrite a different V229 report")
        output.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if output.read_bytes() != result or json.loads(report_path.read_text(encoding="utf-8")) != report:
            raise SurfaceSlotMigrationError("Written V229 candidate/report failed verification")
    except (OSError, ValueError, SurfaceSlotMigrationError, media_migration.StateMigrationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote V229 candidate: {output}")
    print(f"Wrote migration report: {report_path}")
    print(f"SHA-256: {report['output_sha256']}")
    print("The live Slot 1 was not modified. Install only after DuckStation is fully closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
