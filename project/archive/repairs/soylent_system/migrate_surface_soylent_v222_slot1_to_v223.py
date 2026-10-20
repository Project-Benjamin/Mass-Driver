#!/usr/bin/env python3
"""Migrate the exact V222 Intake Slot 1 state to V223 safely.

V223 keeps the finished V222 examination-door geometry and changes only the
far-edge V coordinate used by model 20's two textured threshold quads.  The
loaded field is already resident in this saved state, so this tool applies the
four 0x95 -> 0x8D model bytes and the corresponding four UV bytes in each of
the six live double-buffered packet arenas.

The migration pins the exact source state, both finished media images, field
621's component/model identities, resident model and packet identities, and
the deterministic output.  Its decompressed payload whitelist contains only
those 28 RAM bytes.  In particular, it preserves the loaded field header,
scripts, actors, collision, player, camera, and resident archive table, and it
never writes live DuckStation Slot 1.
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
import tools.migrate_surface_soylent_v220_slot1_to_v221 as model_migration  # noqa: E402
import tools.migrate_surface_soylent_v221_slot1_to_v222 as v222_migration  # noqa: E402
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

SOURCE_STATE_SIZE = 1_677_622
SOURCE_STATE_SHA256 = "a714c8e830ee539157288d9407a22fc38ff670149a276acf9c02c3c69acba9e8"
SOURCE_COMPRESSED_SIZE = 1_623_849
SOURCE_COMPRESSED_SHA256 = "3f6abb87f33dfc53c482c289a6f5e19032fb7a5be69b212cdc7f062d351837eb"
SOURCE_PREFIX_SIZE = 53_773
SOURCE_PREFIX_SHA256 = "818b2a53acb159900d61bd6304754b90e4e6f61b78260b681942425ceddb288c"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "600458b4766982a2e7970f9709e1cacc1d9c12e123efb075a784544bf0afcc68"
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
SOURCE_RAM_SHA256 = "734f94fb5aecfae2b205694d403181c871d7cadef4fc9c1b66c3baf50863e9ac"

OUTPUT_STATE_SIZE = 1_519_504
OUTPUT_STATE_SHA256 = "075b239d04e3781464f0a3e739ea8e65f8ba5086492eab0b9cdd87f71c797872"
OUTPUT_COMPRESSED_SIZE = 1_465_731
OUTPUT_COMPRESSED_SHA256 = "27b1d1398ac84c9d0aae5c1e97059c558f2807cf410f08e046705151a2c5413b"
OUTPUT_PREFIX_SHA256 = "7ddb53e3b7d8b28566042642f5b9eada03a4abd0aebf8d3a09cf65a79cbca98a"
OUTPUT_PAYLOAD_SHA256 = "7012e08113286a05bd613a3b789b583d70c17343a28bbb302aa89ed7c9da6c3e"
OUTPUT_RAM_SHA256 = "065b299d971001cafbbedfa2ba172a76e9769a94f68e3b2557973a23ed23d893"

OLD_DISC_SIZE = NEW_DISC_SIZE = 698_642_784
OLD_DISC_SHA256 = v222_migration.NEW_DISC_SHA256
NEW_DISC_SHA256 = "4cd47686c8a7cc2b5be331f03b73f3e58bfd5e5e23b850ad7547abac917dc7e8"
OLD_CUE_NAME = v222_migration.NEW_CUE_NAME
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v223.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = v222_migration.NEW_CUE_SHA256
NEW_CUE_SHA256 = "bbc6dce43108fe5afc233d91acf6e0e11107833824c2216560abcc663c0e2e4a"

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = "f0a26fa145622264a69cbd25a59213bc1f47920aca22f9d2f00d24fde4342290"
NEW_ARCHIVE_TABLE_SHA256 = "7699ef7067eba7fd54a33ab9a6957097328d14b5f55aaa1c789a12fa8fdedca4"
MEDIA_ARCHIVE_TABLE_DIFFS = ((0x3268, 0xE8, 0xE4),)
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
EXPECTED_ARCHIVE_TABLE_VOLATILE_BYTES = 1
EXPECTED_VOLATILE_TABLE_VALUE = 0xE0
RESIDENT_ARCHIVE_TABLE_SHA256 = "3eacc1ac53db105f07c987a3eeb20cfbbca9df9fefe21a8c7a4c4750e14dfba0"

FIELD621_FAT_INDEX = 1843
FIELD621_CANONICAL_DISC2_INDEX = 1848
FIELD621_MODEL_COMPONENT_INDEX = 2
FIELD621_MODEL20_INDEX = 20
FIELD621_MODEL_COUNT = 21
OLD_FIELD621_BUNDLE_SIZE = 135_656
OLD_FIELD621_BUNDLE_SHA256 = "acf5c09f99d67ee157c4049c31fe1f48026819e6a39e041284bd1912e6e4a039"
NEW_FIELD621_BUNDLE_SIZE = 135_652
NEW_FIELD621_BUNDLE_SHA256 = "d96a1dad2085ab1b0099c62ab7180ece7e52c93862faaa199b6ae7f3119a4c3f"
FIELD_HEADER_SIZE = 1_408
OLD_DISK_HEADER_SHA256 = "a673a4079dddfd4d908f63f8fedee227e9c23f033c6652b8aace86de08900887"
NEW_DISK_HEADER_SHA256 = "bc016d4404b7cd5f31a4eb7aac91315b594152ca17ea640104bc6f8fdc4790df"
FIELD_HEADER_DIFF_TRIPLETS = (
    (0x13C, 0x40, 0x3C),
    (0x140, 0x3C, 0x38),
    (0x144, 0xF4, 0xF0),
    (0x148, 0x60, 0x5C),
    (0x14C, 0x34, 0x30),
    (0x150, 0xE4, 0xE0),
)
FIELD621_MODEL_ARCHIVE_SIZE = 39_292
OLD_FIELD621_MODEL_ARCHIVE_SHA256 = "9fec53653008970b00bc06b4e151f5c093c08e9e49d2620600600f75042e2d7a"
NEW_FIELD621_MODEL_ARCHIVE_SHA256 = "abd08ad9f355179df8281ecd7c297c4e34b45982aa3bcf39f604374c116688d4"
MODEL_ARCHIVE_DIFF_TRIPLETS = (
    (0x9937, 0x95, 0x8D),
    (0x993B, 0x95, 0x8D),
    (0x9943, 0x95, 0x8D),
    (0x9947, 0x95, 0x8D),
)
RESIDENT_SCRIPT_SIZE = 10_895
DISK_SCRIPT_SHA256 = "a362a56e04f91240e4209cb93cdb36a63c31d57bdf2e03c25fca52f202845ea7"

RUNTIME_MODEL20_OFFSET = model_migration.RUNTIME_MODEL20_OFFSET
RUNTIME_MODEL20_SIZE = model_migration.RUNTIME_MODEL20_SIZE
RUNTIME_MODEL20_ARENA_SIZE = model_migration.RUNTIME_MODEL20_ARENA_SIZE
RUNTIME_MODEL20_GUEST_BLOCK_POINTER = model_migration.RUNTIME_MODEL20_GUEST_BLOCK_POINTER
MODEL20_INSTANCE_LAYOUT = model_migration.MODEL20_INSTANCE_LAYOUT
MODEL20_DISK_COUNTS = model_migration.NEW_MODEL20_DISK_COUNTS
MODEL20_RUNTIME_COUNTS = model_migration.NEW_MODEL20_RUNTIME_COUNTS
MODEL20_OFFSETS = model_migration.NEW_MODEL20_OFFSETS
MODEL20_INVENTORY = model_migration.NEW_MODEL20_INVENTORY
OLD_DISK_MODEL20_SHA256 = model_migration.NEW_DISK_MODEL20_SHA256
NEW_DISK_MODEL20_SHA256 = "524f3d90eb72bb674cba3428a7d55b40f580e4064aaf3270b54d8f331320c98a"
SOURCE_RUNTIME_MODEL20_SHA256 = model_migration.OUTPUT_RUNTIME_MODEL20_SHA256
TARGET_RUNTIME_MODEL20_SHA256 = "6f477079b5f55bedfbd2b438883b4a15026bdee4924b28aca242c5daedf5e9fa"
MODEL20_UV_DIFF_TRIPLETS = (
    (0x147, 0x95, 0x8D),
    (0x14B, 0x95, 0x8D),
    (0x153, 0x95, 0x8D),
    (0x157, 0x95, 0x8D),
)
PACKET_ARENA_UV_DIFF_TRIPLETS = (
    (0x15, 0x95, 0x8D),
    (0x25, 0x95, 0x8D),
    (0x3D, 0x95, 0x8D),
    (0x4D, 0x95, 0x8D),
)
SOURCE_PACKET_ARENA_SHA256 = (
    "15faeabc3063eda5291c7244600fe62b050341bdc21872fa8b3bd8f3024cef77",
    "134a185cc87323ac7ffde74667fb5b740594793790668fd3096dc1449407dc8e",
    "322f7ddc103008603cff4f38e46d0c758fea599e8904d6001cc9c5644c6284b6",
    "99e191cbdcb7ec6ef38f6fe6c548e5ca3ef9abe1bba5d06e7fb8734929e313fc",
    "5d6fa03a2200be4b28b40a95d7440f89b7ec31b2c7f1c51e80ff12ed480f42a9",
    "66a4f39d3a13c379b7a834ac0d0e9832b99d2ba2cdb634440721b4619a0b26ca",
)
TARGET_PACKET_ARENA_SHA256 = (
    "47f2a6f90c49ed9b6520fa8947da25fc926c13a8ac0126b3a064b74aaadb64d9",
    "fabb2d54cb5a45fbed5cc8e8f9e4eff08d5908608d90c2662b186b7106a584bd",
    "fbfa9faabe33d7862da2f5ce7565f6cbe2c3a23a5dfae652a28c34e9f27aeac4",
    "1ba3287cafd3103092be7b8c8af52fc57b93f9967fe580dc59c1198f2dcf4c0c",
    "9e933caf321913a3e22a049ca207167522e13292bc41ae87d7a9c37ca37a255c",
    "b85b495b5a7b2134447d3bc93d0217ae6a20322a27f07853b96ed9e982e9cee6",
)
SOURCE_PACKET_ARENAS_SHA256 = "71c37ff13e04f11e8fcab3bfcdabfdb9acbf576fc43108596e6ec83ef2c69387"
TARGET_PACKET_ARENAS_SHA256 = "92e6cec844d9f5a318e4dd9210efd5ae5db2d54386aec27329db7a20dcfa3ec1"

RUNTIME_MODEL2_OFFSET = model_migration.RUNTIME_MODEL2_OFFSET
RUNTIME_MODEL2_SIZE = model_migration.RUNTIME_MODEL2_SIZE
RUNTIME_MODEL2_SHA256 = "749800fc048b59c2e89028b558846f375f9009ff01e0c2a0cc2bcf2b07857ba8"
EXPECTED_FIELD_ACTOR_COUNT = 63
EXPECTED_FIELD_ACTORS = 0x11B0D4
ACTOR_ARRAY_SIZE = EXPECTED_FIELD_ACTOR_COUNT * FIELD_ACTOR_STRIDE
ACTOR_DATA_SIZE = 0x138
SOURCE_ACTOR_ARRAY_SHA256 = "3887f105ee86d1bbd15d2769fdc505585dcf3dd5019af2ea90c2823e67581162"
SOURCE_ACTOR_DATA_SHA256 = "3075767839030f6d4a1a1e7fee46667d059b5e549642a4cb7476e924641da191"
LOADED_HEADER_OFFSET = v222_migration.LOADED_HEADER_OFFSET
LOADED_HEADER_SHA256 = v222_migration.TARGET_LOADED_HEADER_SHA256
RESIDENT_SCRIPT_OFFSET = v222_migration.RESIDENT_SCRIPT_OFFSET
RESIDENT_SCRIPT_SHA256 = v222_migration.NEW_SCRIPT_SHA256
RESIDENT_DIALOGUE_OFFSET = v222_migration.RESIDENT_DIALOGUE_OFFSET
RESIDENT_DIALOGUE_SIZE = v222_migration.RESIDENT_DIALOGUE_SIZE
RESIDENT_DIALOGUE_SHA256 = v222_migration.RESIDENT_DIALOGUE_SHA256
RESIDENT_WALKMESH_OFFSET = v222_migration.RESIDENT_WALKMESH_OFFSET
RESIDENT_WALKMESH_SIZE = v222_migration.RESIDENT_WALKMESH_SIZE
RESIDENT_WALKMESH_SHA256 = v222_migration.RESIDENT_WALKMESH_SHA256
SOURCE_GAMESTATE_SHA256 = "7a3116028dd3fb9c0fd7d8224909f5cd334f9f4cf19a096ec2b903840dcb3d88"
SOURCE_CAMERA_SHA256 = "19ab060bf443462c8bea3e9f6337ee4934aafb56d40116f7092097548a0182b2"

EXPECTED_MODEL20_BYTES_CHANGED = 4
EXPECTED_PACKET_ARENA_COUNT = 6
EXPECTED_PACKET_ARENA_BYTES_CHANGED_EACH = 4
EXPECTED_PACKET_ARENA_BYTES_CHANGED = 24
EXPECTED_RAM_BYTES_CHANGED = 28
EXPECTED_PAYLOAD_BYTES_CHANGED = 28
EXPECTED_PREFIX_BYTES_CHANGED = 4


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output whenever the pinned V222/V223 contract drifts."""


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
        return v222_migration._unpack_state(state, zstd)
    except v222_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc


def _pack_state(prefix: bytes, payload: bytes, zstd: _ZstdLike) -> bytes:
    try:
        return v222_migration._pack_state(prefix, payload, zstd)
    except v222_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc


def _ram_from_payload(payload: bytes) -> tuple[int, bytes]:
    try:
        offset, ram = v222_migration._ram_from_payload(payload)
    except v222_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc
    if offset != EXPECTED_RAM_PAYLOAD_OFFSET:
        raise SurfaceSlotMigrationError("Serialized PSX RAM payload offset drifted")
    return offset, ram


def _expected_prefix(source_prefix: bytes, *, compressed_size: int) -> bytes:
    old_name = OLD_CUE_NAME.encode("ascii")
    new_name = NEW_CUE_NAME.encode("ascii")
    if len(old_name) != len(new_name) or source_prefix.count(old_name) != 1:
        raise SurfaceSlotMigrationError("Pinned V222 media path changed")
    if new_name in source_prefix:
        raise SurfaceSlotMigrationError("Source state already names the V223 media")
    expected = bytearray(source_prefix.replace(old_name, new_name))
    struct.pack_into(
        "<I",
        expected,
        media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        compressed_size,
    )
    return bytes(expected)


def _indexed_entries(data: bytes) -> tuple[bytes, ...]:
    if len(data) < 8:
        raise SurfaceSlotMigrationError("Field-621 model archive is truncated")
    count = struct.unpack_from("<I", data)[0]
    table_end = 4 + 4 * count
    if count == 0 or table_end > len(data):
        raise SurfaceSlotMigrationError("Field-621 model offset table is invalid")
    offsets = struct.unpack_from(f"<{count}I", data, 4)
    if (
        offsets[0] < table_end
        or offsets[-1] >= len(data)
        or any(left >= right for left, right in zip(offsets, offsets[1:]))
    ):
        raise SurfaceSlotMigrationError("Field-621 model offsets are invalid")
    return tuple(
        data[start:end]
        for start, end in zip(offsets, (*offsets[1:], len(data)), strict=True)
    )


def _disc_field621(
    disc: Path,
    *,
    bundle_size: int,
    bundle_sha256: str,
    header_sha256: str,
    model_archive_sha256: str,
    model20_sha256: str,
) -> tuple[ParsedField, bytes, bytes]:
    try:
        image = Mode2Image(disc)
        entries = image.read_index()
        if FIELD621_FAT_INDEX >= len(entries):
            raise SurfaceSlotMigrationError("Field-621 FAT index is absent")
        entry = entries[FIELD621_FAT_INDEX]
        if entry.canonical_disc2_index != FIELD621_CANONICAL_DISC2_INDEX:
            raise SurfaceSlotMigrationError("Field-621 canonical file mapping drifted")
        bundle = image.extract_entry(entry)
        if (len(bundle), _sha256(bundle)) != (bundle_size, bundle_sha256):
            raise SurfaceSlotMigrationError("Field-621 disc bundle identity changed")
        parsed = parse_field(bundle)
    except (DiscFormatError, FieldFormatError) as exc:
        raise SurfaceSlotMigrationError(f"Cannot decode field 621 from disc: {exc}") from exc

    if (
        len(parsed.header) != FIELD_HEADER_SIZE
        or _sha256(parsed.header) != header_sha256
        or len(parsed.parts) != 9
    ):
        raise SurfaceSlotMigrationError("Field-621 header or component layout changed")
    models = parsed.parts[FIELD621_MODEL_COMPONENT_INDEX].data
    if (len(models), _sha256(models)) != (
        FIELD621_MODEL_ARCHIVE_SIZE,
        model_archive_sha256,
    ):
        raise SurfaceSlotMigrationError("Field-621 model archive identity changed")
    entries = _indexed_entries(models)
    if len(entries) != FIELD621_MODEL_COUNT:
        raise SurfaceSlotMigrationError("Field-621 model count changed")
    model20 = entries[FIELD621_MODEL20_INDEX]
    if (len(model20), _sha256(model20)) != (RUNTIME_MODEL20_SIZE, model20_sha256):
        raise SurfaceSlotMigrationError("Field-621 model 20 identity changed")
    return parsed, models, model20


def _model_layout(
    model: bytes,
    *,
    guest_base: int,
    expected_counts: tuple[int, int, int],
) -> tuple[tuple[int, int, int], ...]:
    try:
        return model_migration._model_layout(
            model,
            guest_base=guest_base,
            expected_counts=expected_counts,
            expected_offsets=MODEL20_OFFSETS,
        )
    except model_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc


def _runtime_model20(disk_model: bytes) -> bytes:
    try:
        return model_migration._runtime_model20(disk_model)
    except model_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc


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


def _packet_arena_offsets(
    ram: bytes,
    *,
    expected_hashes: tuple[str, ...] | None,
) -> tuple[int, ...]:
    offsets: list[int] = []
    for entity, instance, expected_buffers in MODEL20_INSTANCE_LAYOUT:
        if not 0 <= instance <= RAM_SIZE - 0x10:
            raise SurfaceSlotMigrationError(f"e{entity} model instance leaves PSX RAM")
        model_pointer, buffer0, buffer1 = struct.unpack_from("<III", ram, instance + 4)
        buffers = (buffer0 & 0x1FFFFFFF, buffer1 & 0x1FFFFFFF)
        if model_pointer != RUNTIME_MODEL20_GUEST_BLOCK_POINTER:
            raise SurfaceSlotMigrationError(f"e{entity} no longer references model 20")
        if buffers != expected_buffers:
            raise SurfaceSlotMigrationError(f"e{entity} packet-arena pointers changed")
        offsets.extend(buffers)

    if len(offsets) != EXPECTED_PACKET_ARENA_COUNT or len(set(offsets)) != len(offsets):
        raise SurfaceSlotMigrationError("Model-20 packet-arena count or ownership changed")
    ordered = sorted(offsets)
    if any(
        offset < 0 or offset + RUNTIME_MODEL20_ARENA_SIZE > RAM_SIZE
        for offset in offsets
    ) or any(
        left + RUNTIME_MODEL20_ARENA_SIZE > right
        for left, right in zip(ordered, ordered[1:])
    ):
        raise SurfaceSlotMigrationError("Model-20 packet arenas overlap or leave PSX RAM")

    arenas = tuple(
        ram[offset : offset + RUNTIME_MODEL20_ARENA_SIZE] for offset in offsets
    )
    if expected_hashes is not None and tuple(_sha256(arena) for arena in arenas) != expected_hashes:
        raise SurfaceSlotMigrationError("Pinned model-20 packet-arena identities changed")
    return tuple(offsets)


def _packet_arenas(ram: bytes) -> bytes:
    offsets = _packet_arena_offsets(ram, expected_hashes=None)
    return b"".join(
        ram[offset : offset + RUNTIME_MODEL20_ARENA_SIZE] for offset in offsets
    )


def _validate_preserved_state(source_ram: bytes, output_ram: bytes) -> None:
    actor_count = struct.unpack_from("<I", source_ram, FIELD_NUM_ACTORS)[0]
    actor_base = struct.unpack_from("<I", source_ram, FIELD_ACTORS)[0] & 0x1FFFFFFF
    if (actor_count, actor_base) != (EXPECTED_FIELD_ACTOR_COUNT, EXPECTED_FIELD_ACTORS):
        raise SurfaceSlotMigrationError("Loaded field-621 actor layout changed")
    if (
        struct.unpack_from("<I", output_ram, FIELD_NUM_ACTORS)[0] != actor_count
        or (struct.unpack_from("<I", output_ram, FIELD_ACTORS)[0] & 0x1FFFFFFF)
        != actor_base
    ):
        raise SurfaceSlotMigrationError("Actor layout was not preserved")

    source_actors = source_ram[actor_base : actor_base + ACTOR_ARRAY_SIZE]
    source_actor_data = _actor_data_snapshot(source_ram, actor_base, actor_count)
    if (
        _sha256(source_actors) != SOURCE_ACTOR_ARRAY_SHA256
        or _sha256(source_actor_data) != SOURCE_ACTOR_DATA_SHA256
    ):
        raise SurfaceSlotMigrationError("Pinned actor or collision state changed")
    if (
        output_ram[actor_base : actor_base + ACTOR_ARRAY_SIZE] != source_actors
        or _actor_data_snapshot(output_ram, actor_base, actor_count) != source_actor_data
    ):
        raise SurfaceSlotMigrationError("Actor or collision state was not preserved")

    preserved_ranges = (
        (GAME_STATE, GAMESTATE_SIZE, SOURCE_GAMESTATE_SHA256, "GameState"),
        (LOADED_HEADER_OFFSET, FIELD_HEADER_SIZE, LOADED_HEADER_SHA256, "loaded field header"),
        (RESIDENT_SCRIPT_OFFSET, RESIDENT_SCRIPT_SIZE, RESIDENT_SCRIPT_SHA256, "field script"),
        (
            RESIDENT_DIALOGUE_OFFSET,
            RESIDENT_DIALOGUE_SIZE,
            RESIDENT_DIALOGUE_SHA256,
            "field dialogue",
        ),
        (
            RESIDENT_WALKMESH_OFFSET,
            RESIDENT_WALKMESH_SIZE,
            RESIDENT_WALKMESH_SHA256,
            "walkmesh/collision",
        ),
        (RUNTIME_MODEL2_OFFSET, RUNTIME_MODEL2_SIZE, RUNTIME_MODEL2_SHA256, "model 2"),
    )
    for offset, size, expected_hash, label in preserved_ranges:
        source = source_ram[offset : offset + size]
        if _sha256(source) != expected_hash:
            raise SurfaceSlotMigrationError(f"Pinned {label} identity changed")
        if output_ram[offset : offset + size] != source:
            raise SurfaceSlotMigrationError(f"{label} was not preserved")

    source_camera = _camera_snapshot(source_ram)
    if _sha256(source_camera) != SOURCE_CAMERA_SHA256:
        raise SurfaceSlotMigrationError("Pinned camera identity changed")
    if _camera_snapshot(output_ram) != source_camera:
        raise SurfaceSlotMigrationError("Camera state was not preserved")


def _build_target_ram(
    source_ram: bytes,
    *,
    old_runtime_model: bytes,
    target_runtime_model: bytes,
) -> tuple[bytes, dict[str, frozenset[int]]]:
    if len(source_ram) != RAM_SIZE:
        raise SurfaceSlotMigrationError("Serialized PSX RAM size changed")
    resident_model = source_ram[
        RUNTIME_MODEL20_OFFSET : RUNTIME_MODEL20_OFFSET + RUNTIME_MODEL20_SIZE
    ]
    if (
        resident_model != old_runtime_model
        or _sha256(resident_model) != SOURCE_RUNTIME_MODEL20_SHA256
    ):
        raise SurfaceSlotMigrationError("Pinned resident V222 model 20 changed")
    if _sha256(target_runtime_model) != TARGET_RUNTIME_MODEL20_SHA256:
        raise SurfaceSlotMigrationError("Resident V223 model-20 reconstruction changed")
    if _diff_triplets(old_runtime_model, target_runtime_model) != MODEL20_UV_DIFF_TRIPLETS:
        raise SurfaceSlotMigrationError("V222/V223 resident model-20 delta changed")

    arena_offsets = _packet_arena_offsets(
        source_ram, expected_hashes=SOURCE_PACKET_ARENA_SHA256
    )
    source_arenas = b"".join(
        source_ram[offset : offset + RUNTIME_MODEL20_ARENA_SIZE]
        for offset in arena_offsets
    )
    if _sha256(source_arenas) != SOURCE_PACKET_ARENAS_SHA256:
        raise SurfaceSlotMigrationError("Pinned model-20 packet-arena set changed")

    target = bytearray(source_ram)
    model_offsets: set[int] = set()
    for relative, old, new in MODEL20_UV_DIFF_TRIPLETS:
        offset = RUNTIME_MODEL20_OFFSET + relative
        if target[offset] != old:
            raise SurfaceSlotMigrationError(
                f"Resident model 20 drifted at relative offset 0x{relative:03X}"
            )
        target[offset] = new
        model_offsets.add(offset)

    packet_offsets: set[int] = set()
    for arena_offset in arena_offsets:
        for relative, old, new in PACKET_ARENA_UV_DIFF_TRIPLETS:
            offset = arena_offset + relative
            if target[offset] != old:
                raise SurfaceSlotMigrationError(
                    f"Packet arena 0x{arena_offset:06X} drifted at +0x{relative:02X}"
                )
            target[offset] = new
            packet_offsets.add(offset)

    result = bytes(target)
    categories = {
        "model20_uv": frozenset(model_offsets),
        "packet_arena_uv": frozenset(packet_offsets),
    }
    if (
        len(model_offsets) != EXPECTED_MODEL20_BYTES_CHANGED
        or len(packet_offsets) != EXPECTED_PACKET_ARENA_BYTES_CHANGED
        or len(model_offsets | packet_offsets) != EXPECTED_RAM_BYTES_CHANGED
        or frozenset(_diff_offsets(source_ram, result))
        != frozenset(model_offsets | packet_offsets)
    ):
        raise SurfaceSlotMigrationError("V223 RAM changed outside the exact UV whitelist")

    if result[
        RUNTIME_MODEL20_OFFSET : RUNTIME_MODEL20_OFFSET + RUNTIME_MODEL20_SIZE
    ] != target_runtime_model:
        raise SurfaceSlotMigrationError("Resident V223 model 20 was not installed")
    output_arena_offsets = _packet_arena_offsets(
        result, expected_hashes=TARGET_PACKET_ARENA_SHA256
    )
    if output_arena_offsets != arena_offsets or _sha256(_packet_arenas(result)) != TARGET_PACKET_ARENAS_SHA256:
        raise SurfaceSlotMigrationError("Resident V223 packet arenas were not patched exactly")
    _validate_preserved_state(source_ram, result)
    return result, categories


def migrate_v222_slot1_to_v223(
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
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V222 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V223 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V222 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V223 CUE"),
    )
    for path, size, sha256, label in identities:
        _validate_file(path, size, sha256, label)

    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    if (
        len(old_table) != ARCHIVE_TABLE_SIZE
        or _sha256(old_table) != OLD_ARCHIVE_TABLE_SHA256
        or _sha256(new_table) != NEW_ARCHIVE_TABLE_SHA256
        or _diff_triplets(old_table, new_table) != MEDIA_ARCHIVE_TABLE_DIFFS
    ):
        raise SurfaceSlotMigrationError("V222/V223 media archive-table delta changed")

    old_field, old_models, old_disk_model = _disc_field621(
        old_disc,
        bundle_size=OLD_FIELD621_BUNDLE_SIZE,
        bundle_sha256=OLD_FIELD621_BUNDLE_SHA256,
        header_sha256=OLD_DISK_HEADER_SHA256,
        model_archive_sha256=OLD_FIELD621_MODEL_ARCHIVE_SHA256,
        model20_sha256=OLD_DISK_MODEL20_SHA256,
    )
    new_field, new_models, new_disk_model = _disc_field621(
        new_disc,
        bundle_size=NEW_FIELD621_BUNDLE_SIZE,
        bundle_sha256=NEW_FIELD621_BUNDLE_SHA256,
        header_sha256=NEW_DISK_HEADER_SHA256,
        model_archive_sha256=NEW_FIELD621_MODEL_ARCHIVE_SHA256,
        model20_sha256=NEW_DISK_MODEL20_SHA256,
    )
    if (
        _diff_triplets(old_field.header, new_field.header) != FIELD_HEADER_DIFF_TRIPLETS
        or _diff_triplets(old_models, new_models) != MODEL_ARCHIVE_DIFF_TRIPLETS
        or _diff_triplets(old_disk_model, new_disk_model) != MODEL20_UV_DIFF_TRIPLETS
    ):
        raise SurfaceSlotMigrationError("Finished field-621 UV-only media delta changed")
    if (
        len(old_field.parts[5].data) != RESIDENT_SCRIPT_SIZE
        or _sha256(old_field.parts[5].data) != DISK_SCRIPT_SHA256
        or new_field.parts[5].data != old_field.parts[5].data
    ):
        raise SurfaceSlotMigrationError("Field-621 script changed in V223")
    for index in range(len(old_field.parts)):
        if index != FIELD621_MODEL_COMPONENT_INDEX and (
            old_field.parts[index].data != new_field.parts[index].data
        ):
            raise SurfaceSlotMigrationError(
                f"Field-621 component {index} changed outside model 20"
            )

    if (
        _model_layout(
            old_disk_model,
            guest_base=0,
            expected_counts=MODEL20_DISK_COUNTS,
        )
        != MODEL20_INVENTORY
        or _model_layout(
            new_disk_model,
            guest_base=0,
            expected_counts=MODEL20_DISK_COUNTS,
        )
        != MODEL20_INVENTORY
    ):
        raise SurfaceSlotMigrationError("Disc model-20 topology changed")
    old_runtime_model = _runtime_model20(old_disk_model)
    target_runtime_model = _runtime_model20(new_disk_model)
    if (
        _sha256(old_runtime_model) != SOURCE_RUNTIME_MODEL20_SHA256
        or _sha256(target_runtime_model) != TARGET_RUNTIME_MODEL20_SHA256
        or _model_layout(
            old_runtime_model,
            guest_base=RUNTIME_MODEL20_OFFSET,
            expected_counts=MODEL20_RUNTIME_COUNTS,
        )
        != MODEL20_INVENTORY
        or _model_layout(
            target_runtime_model,
            guest_base=RUNTIME_MODEL20_OFFSET,
            expected_counts=MODEL20_RUNTIME_COUNTS,
        )
        != MODEL20_INVENTORY
    ):
        raise SurfaceSlotMigrationError("Resident model-20 reconstruction or topology changed")

    source_payload, frame_start, source_prefix = _unpack_state(state, zstd)
    if (
        frame_start != SOURCE_PREFIX_SIZE
        or len(state) - frame_start != SOURCE_COMPRESSED_SIZE
        or _sha256(state[frame_start:]) != SOURCE_COMPRESSED_SHA256
        or _sha256(source_prefix) != SOURCE_PREFIX_SHA256
        or (len(source_payload), _sha256(source_payload))
        != (SOURCE_PAYLOAD_SIZE, SOURCE_PAYLOAD_SHA256)
    ):
        raise SurfaceSlotMigrationError("Pinned source state decomposition changed")
    if (
        source_prefix.count(OLD_CUE_NAME.encode("ascii")) != 1
        or NEW_CUE_NAME.encode("ascii") in source_prefix
    ):
        raise SurfaceSlotMigrationError("Pinned source media path changed")

    try:
        table_offset, volatile_bytes = media_migration._find_resident_archive_table(
            source_payload, old_table
        )
    except media_migration.StateMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc
    source_resident_table = source_payload[table_offset : table_offset + ARCHIVE_TABLE_SIZE]
    if (
        table_offset != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or volatile_bytes != EXPECTED_ARCHIVE_TABLE_VOLATILE_BYTES
        or source_resident_table[-1] != EXPECTED_VOLATILE_TABLE_VALUE
        or _sha256(source_resident_table) != RESIDENT_ARCHIVE_TABLE_SHA256
    ):
        raise SurfaceSlotMigrationError("Pinned resident V222 archive table changed")

    ram_offset, source_ram = _ram_from_payload(source_payload)
    if _sha256(source_ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("Pinned V222 RAM identity changed")
    output_ram, categories = _build_target_ram(
        source_ram,
        old_runtime_model=old_runtime_model,
        target_runtime_model=target_runtime_model,
    )

    expected_ram_offsets = frozenset().union(*categories.values())
    output_payload = bytearray(source_payload)
    for relative in expected_ram_offsets:
        output_payload[ram_offset + relative] = output_ram[relative]
    output_payload_bytes = bytes(output_payload)
    changed_payload_offsets = frozenset(_diff_offsets(source_payload, output_payload_bytes))
    expected_payload_offsets = frozenset(
        ram_offset + relative for relative in expected_ram_offsets
    )
    if (
        changed_payload_offsets != expected_payload_offsets
        or len(changed_payload_offsets) != EXPECTED_PAYLOAD_BYTES_CHANGED
        or _sha256(output_payload_bytes) != OUTPUT_PAYLOAD_SHA256
    ):
        raise SurfaceSlotMigrationError("V223 payload changed outside the exact UV whitelist")

    output_ram_offset, output_ram_check = _ram_from_payload(output_payload_bytes)
    if (
        output_ram_offset != ram_offset
        or output_ram_check != output_ram
        or _sha256(output_ram_check) != OUTPUT_RAM_SHA256
    ):
        raise SurfaceSlotMigrationError("V223 serialized RAM identity changed")
    output_resident_table = output_payload_bytes[
        table_offset : table_offset + ARCHIVE_TABLE_SIZE
    ]
    if output_resident_table != source_resident_table:
        raise SurfaceSlotMigrationError("Resident archive table was not preserved")

    provisional_prefix = _expected_prefix(
        source_prefix, compressed_size=OUTPUT_COMPRESSED_SIZE
    )
    if (
        len(_diff_offsets(source_prefix, provisional_prefix))
        != EXPECTED_PREFIX_BYTES_CHANGED
        or _sha256(provisional_prefix) != OUTPUT_PREFIX_SHA256
    ):
        raise SurfaceSlotMigrationError("V223 media prefix reconstruction changed")
    result = _pack_state(provisional_prefix, output_payload_bytes, zstd)
    output_payload_check, output_frame_start, output_prefix = _unpack_state(result, zstd)
    if (
        output_frame_start != SOURCE_PREFIX_SIZE
        or len(result) - output_frame_start != OUTPUT_COMPRESSED_SIZE
        or _sha256(result[output_frame_start:]) != OUTPUT_COMPRESSED_SHA256
        or output_payload_check != output_payload_bytes
        or output_prefix != provisional_prefix
        or (len(result), _sha256(result)) != (OUTPUT_STATE_SIZE, OUTPUT_STATE_SHA256)
    ):
        raise SurfaceSlotMigrationError("Final V223 state identity or round trip changed")

    report: dict[str, object] = {
        "source_sha256": SOURCE_STATE_SHA256,
        "output_sha256": OUTPUT_STATE_SHA256,
        "source_size": len(state),
        "output_size": len(result),
        "payload_size": len(output_payload_bytes),
        "payload_sha256": OUTPUT_PAYLOAD_SHA256,
        "payload_bytes_changed": len(changed_payload_offsets),
        "ram_bytes_changed": len(expected_ram_offsets),
        "model20_uv_bytes_changed": len(categories["model20_uv"]),
        "packet_arena_uv_bytes_changed": len(categories["packet_arena_uv"]),
        "packet_arena_count": EXPECTED_PACKET_ARENA_COUNT,
        "packet_arena_uv_bytes_changed_each": EXPECTED_PACKET_ARENA_BYTES_CHANGED_EACH,
        "resident_model20_sha256": TARGET_RUNTIME_MODEL20_SHA256,
        "packet_arenas_sha256": TARGET_PACKET_ARENAS_SHA256,
        "media_archive_table_bytes_changed": len(MEDIA_ARCHIVE_TABLE_DIFFS),
        "resident_archive_table_bytes_changed": 0,
        "resident_archive_table_sha256": RESIDENT_ARCHIVE_TABLE_SHA256,
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "model20_topology_and_allocation_preserved": True,
        "packet_arena_allocations_preserved": True,
        "field_header_scripts_actors_collision_preserved": True,
        "player_and_camera_preserved": True,
        "resident_archive_table_preserved": True,
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
            / "save_backups"
            / "SLUS-00669_1_v222_bottom_left_clip_a714c8e8.sav"
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
            / "SLUS-00669_1_v223_from_a714c8e8_threshold_uv.sav"
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
            args.report.resolve() if args.report is not None else output.with_suffix(".json")
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
        result, report = migrate_v222_slot1_to_v223(
            source.read_bytes(),
            old_disc=args.old_disc.resolve(),
            new_disc=args.new_disc.resolve(),
            zstd=zstd,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        if output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Written V223 candidate changed on disk")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote validated V223 candidate: {output}")
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, media_migration.StateMigrationError, SurfaceSlotMigrationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
