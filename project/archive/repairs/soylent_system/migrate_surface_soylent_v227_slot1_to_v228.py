#!/usr/bin/env python3
"""Migrate the exact V227 Intake-door Slot 1 state to V228 safely.

V228 changes only the four nonresident clinical-room bundles at logical fields
591 through 594.  The saved field is 621 and already contains V227's final
route to field 594, so its resident ATEL, header, actors, and runtime state must
not be edited.  Only the serialized Disc 2 archive table is reconstructed for
V228 media; DuckStation's embedded equal-length CUE name is updated when the
payload is recompressed.

The helper is deliberately fail-closed.  It pins the exact source state, both
media sets and stage manifests, every affected clinical resource, the unchanged
field-621 media bundle/header/script, the hybrid resident field-621 layout, and
the complete archive-table delta.  The CLI never writes DuckStation's live
Slot 1 and emits only a separate candidate and JSON report.
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
import tools.migrate_surface_soylent_v226_slot1_to_v227 as previous  # noqa: E402
from tools.xgdeathblows import GAMESTATE_SIZE  # noqa: E402
from tools.xgdisc import DiscFormatError, Mode2Image  # noqa: E402
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
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIVE_SLOT1 = (PROJECT_ROOT / "emulator_data" / "SLUS-00669_1.sav").resolve()
SOURCE_FIXTURE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v227_from_9436ef84_treatment_preparation.sav"
).resolve()

SOURCE_STATE_SIZE = 1_735_278
SOURCE_STATE_SHA256 = "23221b3468b77096fb9a8e07a11a32203fbd51e4c92d0b7fd203b036e30c1950"
SOURCE_PREFIX_SIZE = 0xA0D1
SOURCE_PREFIX_SHA256 = "c7c7fb043efdc45f00fc37ae628d1dbd907e2928de1f5b0d9a63eb076628d373"
SOURCE_COMPRESSED_SIZE = 1_694_109
SOURCE_COMPRESSED_SHA256 = "799caec8ddb776d60bd03ecbccabfdd5974f5435d90de9719470291ad0c93796"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "378c7d8a3fe297927ba5823fcdb77eb7c362c4840eb27f1c1f806d604a3858a4"
SOURCE_RAM_SHA256 = "3aa5febe630f91612e4905ffe6d8f198e46a30cfaa03a78c40285e1235ab4591"

OUTPUT_STATE_SIZE = 1_735_287
OUTPUT_STATE_SHA256 = "a991c4f8779bf0ce877fd6ef90806c757e08cde97abc2b2d05c692972164df64"
OUTPUT_PREFIX_SHA256 = "e30671b3be0503a4b5290e5fb7a3f303d4813da9ed1e52e92ee9be88352c2778"
OUTPUT_COMPRESSED_SIZE = 1_694_118
OUTPUT_COMPRESSED_SHA256 = "4dea5b870cafd121c655eda68bc68bfe7cf1fc1fe2d79dd301e6820ba5917960"
OUTPUT_PAYLOAD_SHA256 = "79c55c9400f47672f60010cc59bb961875107882e358d0510d7ad3f4268ae83c"
OUTPUT_RAM_SHA256 = "9f1c0865fe38aed3b63328fee4a9e278e49a17181c77ad10aa47f63670cccbac"

OLD_DISC_SIZE = 698_885_040
NEW_DISC_SIZE = 698_814_480
OLD_DISC_SHA256 = "108c753b964831ae6be61ca05fb8cbcd47240d27c0d4f376135828b4945596ed"
NEW_DISC_SHA256 = "7bdb5fd17970abb15fc36f32a0907aafd132f80eae818e79ba21473380621deb"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v227.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v228.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = "df061663cd9053e195513221997f4042d37c8d23fba9268e9d10bdafa577c134"
NEW_CUE_SHA256 = "0c3e3672f69969a0e1ced0e04d8dfc2f2298e706acf42b1c58292b4689c714fb"

V227_STAGE_MANIFEST_SIZE = 122_987
V227_STAGE_MANIFEST_SHA256 = "3a56b3ac97ce837c9356207df6a14d488a26cc0a63524472ba903bbae557fb67"
V228_STAGE_MANIFEST_SIZE = 128_038
V228_STAGE_MANIFEST_SHA256 = "39e5b82647ecece73fb61784eae7b3cdcf490e411887765b72a58ea8ed592244"

OLD_MANIFEST_RESOURCES = {
    1788: (83_652, "9ddac63dc36c23e0cb2708adfe627dfdc79a9080a2b5955bcec6fe32b570af07"),
    1789: (131_072, "d151035c6523091d22255ebf587e463748a74d1db521cce852a8d85f6e197d41"),
    1790: (83_676, "bb456fe11c9a768e937073dbaff6b9c086ead9099379632bd32f66682132880b"),
    1791: (131_072, "d151035c6523091d22255ebf587e463748a74d1db521cce852a8d85f6e197d41"),
    1792: (83_860, "15e176ff3b530d812e316005fb275c3eca35f18f533ebed7e4dd2b21f61746e6"),
    1793: (131_072, "d151035c6523091d22255ebf587e463748a74d1db521cce852a8d85f6e197d41"),
    1794: (83_664, "3ba1ba695be88e8000ab09edb5dc50911edfd7e4c6dd00ca2f57b4150af7b700"),
    1795: (131_072, "d151035c6523091d22255ebf587e463748a74d1db521cce852a8d85f6e197d41"),
    1848: (135_644, "168fb1fb14a0c4745725396aae8d5831d931cd30d0d1c67eb6e8d654708eb2bd"),
}
NEW_MANIFEST_RESOURCES = {
    1788: (63_572, "c828843c6e56ca487ede86c46dec856b3df7fe6c1acefe4eb2101753e49dd858"),
    1789: OLD_MANIFEST_RESOURCES[1789],
    1790: (64_132, "3867af0fa734544016496619ce1fea4732754412e4b413a0730d30b36cda3e63"),
    1791: OLD_MANIFEST_RESOURCES[1791],
    1792: (69_624, "82e05fe9ec3d662fd031a7749bd0a8728b54be281f3a47526a375ebd2455280a"),
    1793: OLD_MANIFEST_RESOURCES[1793],
    1794: (72_072, "d8c41033d516f9b1c0a6c965ef24302953bb5d524f523bb0e360e95202095bb7"),
    1795: OLD_MANIFEST_RESOURCES[1795],
    1848: OLD_MANIFEST_RESOURCES[1848],
}
CHANGED_RESOURCE_IDS = (1788, 1790, 1792, 1794)
PINNED_RESOURCE_IDS = tuple(OLD_MANIFEST_RESOURCES)

FIELD621_CANONICAL_ID = 1848
FIELD621_BUNDLE_SIZE, FIELD621_BUNDLE_SHA256 = OLD_MANIFEST_RESOURCES[1848]
MEDIA_HEADER_SIZE = 1_408
MEDIA_HEADER_SHA256 = "2d05178f666806c9eaed864d63c44ec41822adeb1164d13e69e50e9cde55432d"
MEDIA_SCRIPT_SIZE = 10_895
MEDIA_SCRIPT_SHA256 = "a7c52258a56f10a1bea9e8ee7cdc9c7730b78bd1c21f524a12a108302a2172f2"

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = "165b10eb5a7a7c31f9188ae62d70dc0ce82810a4bb8b8671910e881cb4379e8f"
NEW_ARCHIVE_TABLE_SHA256 = "72d321cee32b79b344bd7292beea419b633d7d96244408e166cb4d4b5c2eb6b3"
ARCHIVE_TABLE_DIFF_COUNT = 2_464
ARCHIVE_TABLE_DIFF_FIRST = 0x30C4
ARCHIVE_TABLE_DIFF_LAST = 0x7157
ARCHIVE_TABLE_DIFF_SHA256 = "fb8a42db22f6c729fa2cf69f8a40e9b9c893a928fc338da77179ccfa83ae1390"
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = previous.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
SOURCE_RESIDENT_TABLE_SHA256 = "bdf07517cbcfb3ad6676aa1deda27086707aa75f7e67c54cf002afac9ef45ada"
OUTPUT_RESIDENT_TABLE_SHA256 = "13d23b9b2f983cba4b0883e58cd2b083126642284957fe752ae821e9b0c5a727"
RESIDENT_VS_MEDIA_DIFFS = ((0x7FFF, 0xE0, 0x00),)

# The exact V227 state is a deliberate hybrid: its resident ATEL is V227, but
# its already-loaded header remains the allocator-safe V226 header.
RESIDENT_HEADER_SIZE = previous.OLD_HEADER_SIZE
RESIDENT_HEADER_SHA256 = previous.OLD_HEADER_SHA256
RESIDENT_SCRIPT_SIZE = MEDIA_SCRIPT_SIZE
RESIDENT_SCRIPT_SHA256 = MEDIA_SCRIPT_SHA256
EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET = previous.EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET
EXPECTED_SCRIPT_PAYLOAD_OFFSET = previous.EXPECTED_SCRIPT_PAYLOAD_OFFSET
EXPECTED_DIALOGUE_PAYLOAD_OFFSET = previous.EXPECTED_DIALOGUE_PAYLOAD_OFFSET
EXPECTED_WALKMESH_PAYLOAD_OFFSET = previous.EXPECTED_WALKMESH_PAYLOAD_OFFSET
DIALOGUE_SIZE = previous.DIALOGUE_SIZE
DIALOGUE_SHA256 = previous.DIALOGUE_SHA256
WALKMESH_SIZE = previous.WALKMESH_SIZE
WALKMESH_SHA256 = previous.WALKMESH_SHA256
SCRIPT_GAP_SIZE = previous.SCRIPT_GAP_SIZE
SCRIPT_GAP_SHA256 = previous.SCRIPT_GAP_SHA256
DIALOGUE_GAP_SIZE = previous.DIALOGUE_GAP_SIZE
DIALOGUE_GAP_SHA256 = previous.DIALOGUE_GAP_SHA256

EXPECTED_FIELD = previous.EXPECTED_FIELD
EXPECTED_RAM_PAYLOAD_OFFSET = previous.EXPECTED_RAM_PAYLOAD_OFFSET
EXPECTED_ACTOR_COUNT = previous.EXPECTED_ACTOR_COUNT
SCRIPT_ENTITY_COUNT = previous.SCRIPT_ENTITY_COUNT
ACTOR_ARRAY_SIZE = previous.ACTOR_ARRAY_SIZE
ACTOR_DATA_SIZE = previous.ACTOR_DATA_SIZE
ACTOR_SCRIPT_SLOT_OFFSET = previous.ACTOR_SCRIPT_SLOT_OFFSET
ACTOR_CURRENT_PC_OFFSET = previous.ACTOR_CURRENT_PC_OFFSET
FEI_ENTITY = previous.FEI_ENTITY
DOOR_ENTITY = previous.DOOR_ENTITY
DOOR_HELPER_ENTITY = previous.DOOR_HELPER_ENTITY
DOOR_CHANGE_FIELD_PC = previous.DOOR_CHANGE_FIELD_PC
CURRENT_CHANGE_FIELD = previous.NEW_CHANGE_FIELD
EXPECTED_FEI_PC = previous.EXPECTED_FEI_PC
EXPECTED_DOOR_PC = previous.EXPECTED_DOOR_PC
EXPECTED_HELPER_PC = previous.EXPECTED_HELPER_PC

EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED = ARCHIVE_TABLE_DIFF_COUNT
EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED = 0
EXPECTED_RUNTIME_PC_BYTES_CHANGED = 0
EXPECTED_PAYLOAD_BYTES_CHANGED = ARCHIVE_TABLE_DIFF_COUNT
EXPECTED_PREFIX_BYTES_CHANGED = 2


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


def _expected_prefix(source_prefix: bytes, *, compressed_size: int) -> bytes:
    old_name, new_name = OLD_CUE_NAME.encode("ascii"), NEW_CUE_NAME.encode("ascii")
    if len(old_name) != len(new_name) or source_prefix.count(old_name) != 1 or source_prefix.count(new_name):
        raise SurfaceSlotMigrationError("Pinned V227 media path changed")
    expected = bytearray(source_prefix.replace(old_name, new_name))
    struct.pack_into("<I", expected, media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET, compressed_size)
    return bytes(expected)


def _ram_from_payload(payload: bytes) -> tuple[int, bytes]:
    offset, ram = previous._ram_from_payload(payload)
    if offset != EXPECTED_RAM_PAYLOAD_OFFSET:
        raise SurfaceSlotMigrationError("Serialized RAM payload offset drifted")
    return offset, ram


def _camera_snapshot(ram: bytes) -> bytes:
    return previous._camera_snapshot(ram)


def _validate_file(path: Path, size: int, sha256: str, label: str) -> None:
    if not path.is_file() or path.stat().st_size != size or _file_sha256(path) != sha256:
        raise SurfaceSlotMigrationError(f"{label} identity drifted")


def _manifest_inventory(blob: bytes, *, size: int, sha256: str, label: str) -> dict[int, tuple[int, str]]:
    if (len(blob), _sha256(blob)) != (size, sha256):
        raise SurfaceSlotMigrationError(f"{label} identity drifted")
    try:
        inventory = {
            int(item["canonical_id"]): (int(item["size"]), str(item["sha256"]))
            for item in json.loads(blob)["replacement_inventory"]
        }
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise SurfaceSlotMigrationError(f"{label} structure drifted") from exc
    return inventory


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
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V227 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V228 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V227 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V228 CUE"),
    ):
        _validate_file(path, size, sha256, label)

    old_inventory = _manifest_inventory(
        old_manifest,
        size=V227_STAGE_MANIFEST_SIZE,
        sha256=V227_STAGE_MANIFEST_SHA256,
        label="V227 stage manifest",
    )
    new_inventory = _manifest_inventory(
        new_manifest,
        size=V228_STAGE_MANIFEST_SIZE,
        sha256=V228_STAGE_MANIFEST_SHA256,
        label="V228 stage manifest",
    )
    for canonical_id in PINNED_RESOURCE_IDS:
        if old_inventory.get(canonical_id) != OLD_MANIFEST_RESOURCES[canonical_id]:
            raise SurfaceSlotMigrationError(f"V227 manifest resource {canonical_id} drifted")
        if new_inventory.get(canonical_id) != NEW_MANIFEST_RESOURCES[canonical_id]:
            raise SurfaceSlotMigrationError(f"V228 manifest resource {canonical_id} drifted")
    changed = tuple(
        sorted(
            canonical_id
            for canonical_id in old_inventory.keys() | new_inventory.keys()
            if old_inventory.get(canonical_id) != new_inventory.get(canonical_id)
        )
    )
    if changed != CHANGED_RESOURCE_IDS:
        raise SurfaceSlotMigrationError("V227/V228 replacement-inventory change set drifted")

    for blob, label in (
        (old_header, "V227 field-621 header clone"),
        (new_header, "V228 field-621 header clone"),
    ):
        if (len(blob), _sha256(blob)) != (MEDIA_HEADER_SIZE, MEDIA_HEADER_SHA256):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    for blob, label in (
        (old_script, "V227 field-621 script clone"),
        (new_script, "V228 field-621 script clone"),
    ):
        if (len(blob), _sha256(blob)) != (MEDIA_SCRIPT_SIZE, MEDIA_SCRIPT_SHA256):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    if old_header != new_header or old_script != new_script:
        raise SurfaceSlotMigrationError("V228 changed resident field-621 media")

    try:
        old_image, new_image = Mode2Image(old_disc), Mode2Image(new_disc)
        for canonical_id in PINNED_RESOURCE_IDS:
            previous._disc_resource(
                old_image,
                canonical_id,
                *OLD_MANIFEST_RESOURCES[canonical_id],
                f"V227 resource {canonical_id}",
            )
            previous._disc_resource(
                new_image,
                canonical_id,
                *NEW_MANIFEST_RESOURCES[canonical_id],
                f"V228 resource {canonical_id}",
            )
        old_bundle, old_field = previous._disc_field621(
            old_disc,
            size=FIELD621_BUNDLE_SIZE,
            sha256=FIELD621_BUNDLE_SHA256,
            label="V227 field-621 bundle",
        )
        new_bundle, new_field = previous._disc_field621(
            new_disc,
            size=FIELD621_BUNDLE_SIZE,
            sha256=FIELD621_BUNDLE_SHA256,
            label="V228 field-621 bundle",
        )
    except DiscFormatError as exc:
        raise SurfaceSlotMigrationError(f"Cannot validate V227/V228 disc resources: {exc}") from exc
    if old_bundle != new_bundle or old_field.header != old_header or new_field.header != new_header:
        raise SurfaceSlotMigrationError("Field-621 disc/header preservation drifted")
    old_parts = tuple(part.data for part in old_field.parts)
    new_parts = tuple(part.data for part in new_field.parts)
    if old_parts != new_parts or old_parts[5] != old_script or new_parts[5] != new_script:
        raise SurfaceSlotMigrationError("Field-621 component/script preservation drifted")

    atel = AtelScript(old_script)
    if (
        atel.entity_count != SCRIPT_ENTITY_COUNT
        or atel.get_script_pointer(DOOR_ENTITY, 2) != previous.DOOR_SCRIPT2_PC
        or atel.bytecode[DOOR_CHANGE_FIELD_PC : DOOR_CHANGE_FIELD_PC + 5] != CURRENT_CHANGE_FIELD
    ):
        raise SurfaceSlotMigrationError("V227/V228 field-621 route topology drifted")

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
        raise SurfaceSlotMigrationError("V227/V228 archive-table delta drifted")
    return old_table, new_table


def _validate_source(payload: bytes, old_table: bytes) -> dict[str, object]:
    if (len(payload), _sha256(payload)) != (SOURCE_PAYLOAD_SIZE, SOURCE_PAYLOAD_SHA256):
        raise SurfaceSlotMigrationError("V227 decompressed payload identity drifted")
    ram_offset, ram = _ram_from_payload(payload)
    if _sha256(ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("V227 serialized RAM identity drifted")

    table = payload[
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET : EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
    ]
    script = payload[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE
    ]
    header = payload[
        EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET : EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET + RESIDENT_HEADER_SIZE
    ]
    dialogue = payload[EXPECTED_DIALOGUE_PAYLOAD_OFFSET : EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE]
    walkmesh = payload[EXPECTED_WALKMESH_PAYLOAD_OFFSET : EXPECTED_WALKMESH_PAYLOAD_OFFSET + WALKMESH_SIZE]
    script_gap = payload[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE : EXPECTED_DIALOGUE_PAYLOAD_OFFSET
    ]
    dialogue_gap = payload[
        EXPECTED_DIALOGUE_PAYLOAD_OFFSET + DIALOGUE_SIZE : EXPECTED_WALKMESH_PAYLOAD_OFFSET
    ]
    if (
        _sha256(table) != SOURCE_RESIDENT_TABLE_SHA256
        or _diff_triplets(table, old_table) != RESIDENT_VS_MEDIA_DIFFS
        or (len(script), _sha256(script)) != (RESIDENT_SCRIPT_SIZE, RESIDENT_SCRIPT_SHA256)
        or script[previous.SCRIPT_PATCH_OFFSET : previous.SCRIPT_PATCH_OFFSET + 5] != CURRENT_CHANGE_FIELD
        or (len(header), _sha256(header)) != (RESIDENT_HEADER_SIZE, RESIDENT_HEADER_SHA256)
        or _sha256(header) == MEDIA_HEADER_SHA256
        or (len(dialogue), _sha256(dialogue)) != (DIALOGUE_SIZE, DIALOGUE_SHA256)
        or (len(walkmesh), _sha256(walkmesh)) != (WALKMESH_SIZE, WALKMESH_SHA256)
        or (len(script_gap), _sha256(script_gap)) != (SCRIPT_GAP_SIZE, SCRIPT_GAP_SHA256)
        or (len(dialogue_gap), _sha256(dialogue_gap)) != (DIALOGUE_GAP_SIZE, DIALOGUE_GAP_SHA256)
    ):
        raise SurfaceSlotMigrationError("Hybrid resident field-621 identity drifted")

    actor_pointer = struct.unpack_from("<I", ram, FIELD_ACTORS)[0]
    if (
        (struct.unpack_from("<I", ram, previous.GAME_SCENE_MAP)[0] & 0xFFF) != EXPECTED_FIELD
        or struct.unpack_from("<I", ram, FIELD_NUM_ACTORS)[0] != EXPECTED_ACTOR_COUNT
        or actor_pointer != previous.EXPECTED_ACTOR_ARRAY_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0] != previous.EXPECTED_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA)[0]
        != previous.EXPECTED_VM_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_ACTOR)[0]
        != previous.EXPECTED_VM_ACTOR_GUEST_POINTER
    ):
        raise SurfaceSlotMigrationError("Live field-621 pointer topology drifted")
    actor_base = actor_pointer & 0x1FFFFFFF
    actor_array = bytes(ram[actor_base : actor_base + ACTOR_ARRAY_SIZE])
    records = tuple(
        bytes(ram[actor_base + entity * FIELD_ACTOR_STRIDE : actor_base + (entity + 1) * FIELD_ACTOR_STRIDE])
        for entity in range(EXPECTED_ACTOR_COUNT)
    )
    offsets = tuple(previous._actor_data_offset(ram, actor_base, entity) for entity in range(SCRIPT_ENTITY_COUNT))
    data = tuple(bytes(ram[offset : offset + ACTOR_DATA_SIZE]) for offset in offsets)
    if (
        _sha256(actor_array) != previous.SOURCE_ACTOR_ARRAY_SHA256
        or _sha256(b"".join(data)) != previous.SOURCE_ACTOR_DATA_SHA256
    ):
        raise SurfaceSlotMigrationError("Live field-621 actor allocation identity drifted")
    atel = AtelScript(script)
    for entity, expected_pc in (
        (FEI_ENTITY, EXPECTED_FEI_PC),
        (DOOR_ENTITY, EXPECTED_DOOR_PC),
        (DOOR_HELPER_ENTITY, EXPECTED_HELPER_PC),
    ):
        slot_pc = struct.unpack_from("<H", data[entity], ACTOR_SCRIPT_SLOT_OFFSET)[0]
        current_pc = struct.unpack_from("<H", data[entity], ACTOR_CURRENT_PC_OFFSET)[0]
        if slot_pc != expected_pc or current_pc != expected_pc or atel.bytecode[current_pc] != 0x00:
            raise SurfaceSlotMigrationError(f"e{entity} is not idle at the pinned STOP")

    gamestate = bytes(ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE])
    field_bank = bytes(ram[FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + previous.FIELD_VARIABLE_BANK_SIZE])
    camera = _camera_snapshot(ram)
    windows = bytes(ram[previous.DIALOG_WINDOWS : previous.DIALOG_WINDOWS + previous.DIALOG_WINDOWS_SIZE])
    if (
        _sha256(gamestate) != previous.EXPECTED_GAMESTATE_SHA256
        or _sha256(field_bank) != previous.EXPECTED_FIELD_VARIABLE_BANK_SHA256
        or _sha256(camera) != previous.EXPECTED_CAMERA_SHA256
        or _sha256(windows) != previous.EXPECTED_DIALOG_WINDOWS_SHA256
    ):
        raise SurfaceSlotMigrationError("GameState/field/camera/window identity drifted")
    return {
        "ram_offset": ram_offset,
        "ram": ram,
        "table": table,
        "script": script,
        "header": header,
        "dialogue": dialogue,
        "walkmesh": walkmesh,
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


def migrate_v227_slot1_to_v228(
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
    source_sha = _sha256(state)
    if (len(state), source_sha) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise SurfaceSlotMigrationError(
            f"Source Slot 1 identity is {len(state)} / {source_sha}, expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    old_name, new_name = OLD_CUE_NAME.encode("ascii"), NEW_CUE_NAME.encode("ascii")
    if len(old_name) != len(new_name) or state.count(old_name) != 1 or state.count(new_name):
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
    snapshots = _validate_source(source_payload, old_table)

    final = bytearray(source_payload)
    table_diffs = _diff_triplets(old_table, new_table)
    changed_offsets: set[int] = set()
    for relative, old, new in table_diffs:
        offset = EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + relative
        if final[offset] != old:
            raise SurfaceSlotMigrationError(f"Archive-table source drifted at 0x{relative:04X}")
        final[offset] = new
        changed_offsets.add(offset)
    final_payload = bytes(final)
    actual_offsets = frozenset(_diff_offsets(source_payload, final_payload))
    if (
        actual_offsets != frozenset(changed_offsets)
        or len(actual_offsets) != EXPECTED_PAYLOAD_BYTES_CHANGED
        or _sha256(final_payload) != OUTPUT_PAYLOAD_SHA256
    ):
        raise SurfaceSlotMigrationError("Migration changed bytes outside the exact archive-table whitelist")

    output_table = final_payload[
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET : EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
    ]
    if _sha256(output_table) != OUTPUT_RESIDENT_TABLE_SHA256 or _diff_triplets(output_table, new_table) != RESIDENT_VS_MEDIA_DIFFS:
        raise SurfaceSlotMigrationError("V228 resident archive-table reconstruction drifted")
    for offset, expected, label in (
        (EXPECTED_SCRIPT_PAYLOAD_OFFSET, snapshots["script"], "script"),
        (EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET, snapshots["header"], "hybrid loaded header"),
        (EXPECTED_DIALOGUE_PAYLOAD_OFFSET, snapshots["dialogue"], "dialogue"),
        (EXPECTED_WALKMESH_PAYLOAD_OFFSET, snapshots["walkmesh"], "walkmesh"),
    ):
        if final_payload[offset : offset + len(expected)] != expected:
            raise SurfaceSlotMigrationError(f"Resident field-621 {label} changed")

    ram_offset, result_ram = _ram_from_payload(final_payload)
    if ram_offset != snapshots["ram_offset"] or _sha256(result_ram) != OUTPUT_RAM_SHA256:
        raise SurfaceSlotMigrationError("Final V228 serialized RAM identity drifted")
    source_ram = snapshots["ram"]
    if tuple(ram_offset + offset for offset in _diff_offsets(source_ram, result_ram)) != tuple(sorted(actual_offsets)):
        raise SurfaceSlotMigrationError("A payload edit escaped the serialized PSX RAM span")
    actor_base = snapshots["actor_base"]
    if result_ram[actor_base : actor_base + ACTOR_ARRAY_SIZE] != snapshots["actor_array"]:
        raise SurfaceSlotMigrationError("Field-621 actor array changed")
    for entity in range(SCRIPT_ENTITY_COUNT):
        record = result_ram[actor_base + entity * FIELD_ACTOR_STRIDE : actor_base + (entity + 1) * FIELD_ACTOR_STRIDE]
        data_offset = snapshots["offsets"][entity]
        data = result_ram[data_offset : data_offset + ACTOR_DATA_SIZE]
        if record != snapshots["records"][entity] or data != snapshots["data"][entity]:
            raise SurfaceSlotMigrationError(f"Field runtime e{entity} changed")
    for start, size, expected, label in (
        (GAME_STATE, GAMESTATE_SIZE, snapshots["gamestate"], "GameState/party"),
        (FIELD_SCRIPT_MEMORY, previous.FIELD_VARIABLE_BANK_SIZE, snapshots["field_bank"], "field variables"),
        (previous.DIALOG_WINDOWS, previous.DIALOG_WINDOWS_SIZE, snapshots["windows"], "dialogue windows"),
    ):
        if result_ram[start : start + size] != expected:
            raise SurfaceSlotMigrationError(f"{label} changed")
    if _camera_snapshot(result_ram) != snapshots["camera"]:
        raise SurfaceSlotMigrationError("Camera changed")

    provisional_prefix = _expected_prefix(source_prefix, compressed_size=OUTPUT_COMPRESSED_SIZE)
    if (
        len(_diff_offsets(source_prefix, provisional_prefix)) != EXPECTED_PREFIX_BYTES_CHANGED
        or _sha256(provisional_prefix) != OUTPUT_PREFIX_SHA256
    ):
        raise SurfaceSlotMigrationError("V228 media-prefix reconstruction drifted")
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
        raise SurfaceSlotMigrationError("Final V228 state identity or round trip drifted")

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
        "archive_table_bytes_changed": len(actual_offsets),
        "resident_script_bytes_changed": 0,
        "resident_header_bytes_changed": 0,
        "runtime_actor_pc_bytes_changed": 0,
        "changed_resource_ids": list(CHANGED_RESOURCE_IDS),
        "resident_archive_table_sha256": OUTPUT_RESIDENT_TABLE_SHA256,
        "resident_archive_volatile_tail_preserved": True,
        "resident_v227_route_preserved": True,
        "hybrid_v226_loaded_header_preserved": True,
        "all_actor_runtime_preserved": True,
        "gamestate_party_field_camera_windows_preserved": True,
        "allocator_safe": True,
        "round_trip_verified": True,
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "v227_stage_manifest_sha256": V227_STAGE_MANIFEST_SHA256,
        "v228_stage_manifest_sha256": V228_STAGE_MANIFEST_SHA256,
        "v227_disc_sha256": OLD_DISC_SHA256,
        "v228_disc_sha256": NEW_DISC_SHA256,
    }
    return result, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=SOURCE_FIXTURE)
    parser.add_argument("--old-disc", type=Path, default=PROJECT_ROOT / "output" / OLD_CUE_NAME.replace(".cue", ".bin"))
    parser.add_argument("--new-disc", type=Path, default=PROJECT_ROOT / "output" / NEW_CUE_NAME.replace(".cue", ".bin"))
    parser.add_argument(
        "--old-manifest",
        type=Path,
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v227_stage" / "manifest.json",
    )
    parser.add_argument(
        "--new-manifest",
        type=Path,
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v228_stage" / "manifest.json",
    )
    parser.add_argument(
        "--old-header",
        type=Path,
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v227_stage" / "clones" / "field_621" / "header.bin",
    )
    parser.add_argument(
        "--new-header",
        type=Path,
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v228_stage" / "clones" / "field_621" / "header.bin",
    )
    parser.add_argument(
        "--old-script",
        type=Path,
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v227_stage" / "clones" / "field_621" / "05_scripts.bin",
    )
    parser.add_argument(
        "--new-script",
        type=Path,
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v228_stage" / "clones" / "field_621" / "05_scripts.bin",
    )
    parser.add_argument("--zstd", type=Path, default=PROJECT_ROOT / "work" / "duckstation" / "zstd.dll")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "work" / "save_candidates" / "SLUS-00669_1_v228_from_23221b34_clinic_aid.sav",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=PROJECT_ROOT / "work" / "save_candidates" / "SLUS-00669_1_v228_from_23221b34_clinic_aid.json",
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
        result, report = migrate_v227_slot1_to_v228(
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
        output.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if output.read_bytes() != result or json.loads(report_path.read_text(encoding="utf-8")) != report:
            raise SurfaceSlotMigrationError("Written V228 candidate/report failed verification")
    except (OSError, ValueError, SurfaceSlotMigrationError, media_migration.StateMigrationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote V228 candidate: {output}")
    print(f"Wrote migration report: {report_path}")
    print(f"SHA-256: {report['output_sha256']}")
    print("The live Slot 1 was not modified. Install only after DuckStation is fully closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
