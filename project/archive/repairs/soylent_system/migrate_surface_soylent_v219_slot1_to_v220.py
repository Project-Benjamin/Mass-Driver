#!/usr/bin/env python3
"""Migrate the exact V219 Intake camera-glitch state to V220 safely.

The authoritative source is paused in field 621 after the custom examination
doors were installed.  V219 still retains model 2's native solid-black camera
occluders, whose four F3 corner caps and 134 F4 fascia faces can cross the
party at the user's Door-A and Door-B camera angles.  V220 makes those two
mesh groups non-rendering in place and keeps the already-inert model-20 rear
plate allocation unchanged.

This migration retargets the mounted CUE, updates the two exact resident
archive-table bytes changed by V220, and zeroes only the pinned runtime index
ranges.  Model sizes, primitive counts, display packets, actor allocations,
scripts, walkmesh/collision, GameState, camera vectors, and player state remain
byte-identical.  The tool never overwrites live DuckStation Slot 1.
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
from work.read_duckstation_runtime import (  # noqa: E402
    CAMERA_VECTORS,
    FIELD_ACTORS,
    FIELD_ACTOR_DATA_POINTER,
    FIELD_ACTOR_STRIDE,
    FIELD_NUM_ACTORS,
    GAME_STATE,
    RAM_SIZE,
    _psx_ram_offset,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIVE_SLOT1 = (PROJECT_ROOT / "emulator_data" / "SLUS-00669_1.sav").resolve()

SOURCE_STATE_SIZE = 1_657_093
SOURCE_STATE_SHA256 = "3081ee5db0b0a5bf4a73a11970cb6341bebc1dca8d14415f0925d0fc0dc88053"
SOURCE_COMPRESSED_SIZE = 1_610_750
SOURCE_PREFIX_SIZE = 46_343
SOURCE_PREFIX_SHA256 = "26f038d43e16fae5e19f79f98818e7740cee804c56e4082d9353e631636feaf4"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "99b509fc0e092c1c867b8218b2dc75764d63131511d0038a22addb157b2a19eb"
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
SOURCE_RAM_SHA256 = "7870182df0028ebdc5862174e8f9d1bdacd9d088c679f368c5269c965fd98c39"

OUTPUT_STATE_SIZE = 1_506_786
OUTPUT_STATE_SHA256 = "d5acab444832d1e773a2bc66c58c0074cf2a54f901ebd689549acac34b3a017b"
OUTPUT_COMPRESSED_SIZE = 1_460_443
OUTPUT_PREFIX_SHA256 = "46e90e746ae1dd9f9558662b5a23a05d1d7654427dee9c19907dc334e6d89131"
OUTPUT_PAYLOAD_SHA256 = "b7cc59ab5f8a683e37e336e4ec4978dbb8b44437d8c1eea80d93f60bd4b5548c"
OUTPUT_RAM_SHA256 = "fee47c44603462700784fa314a4bc8be8e9c0fd741c191aa41adce86ac102cc2"

OLD_DISC_SIZE = NEW_DISC_SIZE = 698_642_784
OLD_DISC_SHA256 = "6d00d1c9246aa5b61a23949d4f52b55a7ab87a787244143740980cd1e31d837f"
NEW_DISC_SHA256 = "b4f91cad8d7c819e4908d0e1c8369ff3fe3c432405a39ff4cb8d7bd9e961c63d"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v219.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v220.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = "8403365f8a5010224604956d9b521594be603ae7408b426da4145c378b5aa7d6"
NEW_CUE_SHA256 = "4a07ef2954e665340ed6f00912777a1cac162b4d8bb3206c41e5a8e653d85ab7"

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = "55c8301a640bb118b6705fa553a3d3f7dd80a6edaeb8f80433c56923fc719d15"
NEW_ARCHIVE_TABLE_SHA256 = "7699ef7067eba7fd54a33ab9a6957097328d14b5f55aaa1c789a12fa8fdedca4"
ARCHIVE_TABLE_DIFFS = (
    (0x3268, 0xAC, 0xE4),
    (0x3269, 0x14, 0x11),
)
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
EXPECTED_VOLATILE_TABLE_VALUE = 0xE0
SOURCE_RESIDENT_TABLE_SHA256 = "4396cda395cb53af17a1d184c0d23c3411a127359548fed4f0cc55eeae24d649"
OUTPUT_RESIDENT_TABLE_SHA256 = "81d563907cda74748d869ad3a2e2956f6758bf00424a3fd78a2379ac787a64c1"

# Resident model 2 is referenced by static field actor e51.  Its four mesh
# groups remain allocated.  Only the untextured flat-black F3 group 0 and F4
# group 2 index records are made zero-area; textured groups 1 and 3 remain.
RUNTIME_MODEL2_OFFSET = 0x10B370
RUNTIME_MODEL2_SIZE = 4_836
SOURCE_RUNTIME_MODEL2_SHA256 = "6b8d8947a4b37dbdb464e970d51fe0918a4dc178a79683cfd9969be62863e6e7"
OUTPUT_RUNTIME_MODEL2_SHA256 = "749800fc048b59c2e89028b558846f375f9009ff01e0c2a0cc2bcf2b07857ba8"
MODEL2_ZERO_RANGES = (
    (0x6F4, 0x714),  # group 0: four F3 records
    (0x74C, 0xB7C),  # group 2: 134 F4 records
)
MODEL2_EXPECTED_LAYOUT = (
    (0x04, 0x77, 4),
    (0x05, 0x77, 6),
    (0x0C, 0x77, 134),
    (0x0D, 0x77, 64),
)

# Model 20 was already hot-patched to its final inert form before the source
# state was captured.  Rewriting its index range to zero is intentionally
# idempotent, and its full hash is pinned on both sides of the migration.
RUNTIME_MODEL20_OFFSET = 0x110A18
RUNTIME_MODEL20_SIZE = 396
SOURCE_RUNTIME_MODEL20_SHA256 = "fa98fafb54e8c85d1f67701bb8c20f62a2838fc5c25a11d572b044415c93aa91"
OUTPUT_RUNTIME_MODEL20_SHA256 = SOURCE_RUNTIME_MODEL20_SHA256
MODEL20_ZERO_RANGES = ((0x0CC, 0x14C),)
MODEL20_EXPECTED_LAYOUT = ((0x04, 0x77, 16),)

EXPECTED_MODEL2_BYTES_CHANGED = 546
EXPECTED_MODEL20_BYTES_CHANGED = 0
EXPECTED_GEOMETRY_BYTES_CHANGED = 546
EXPECTED_ARCHIVE_BYTES_CHANGED = 2
EXPECTED_PAYLOAD_BYTES_CHANGED = 548

EXPECTED_FIELD_ACTOR_COUNT = 63
EXPECTED_FIELD_ACTORS = 0x11B0D4
ACTOR_DATA_SIZE = 0x138
SOURCE_ACTOR_ARRAY_SHA256 = "22cc85d5813452a58bcf6abcd24987e4b6bdc6b238a5b93778d8587b15d8293a"
SOURCE_ACTOR_DATA_SHA256 = "8ae2b4b3b8fa9a5b4856a6b3f24f5ebebc1b3acad1c5dd927c00e789339833e6"

# Exact loaded field resources and gameplay state that must not change.
LOADED_HEADER_OFFSET = 0x1C9FD4
LOADED_HEADER_SIZE = 1_408
LOADED_HEADER_SHA256 = "07a06f1fd4db8494dd18b0fe75db2d8d1212aae429ce176b79e6dd1d12565bbf"
RESIDENT_SCRIPT_OFFSET = 0x110BBC
RESIDENT_SCRIPT_SIZE = 10_895
RESIDENT_SCRIPT_SHA256 = "78399e8caa38656e936aaf5a72bc1bb6db70b998c33ab028c522ced107cc392e"
RESIDENT_DIALOGUE_OFFSET = 0x11367C
RESIDENT_DIALOGUE_SIZE = 2_135
RESIDENT_DIALOGUE_SHA256 = "2affc3b9e7ad27ae0e9be2b4e8f0d1362f3b37ef7218001aa995994cf6e5bb40"
RESIDENT_WALKMESH_OFFSET = 0x113EEC
RESIDENT_WALKMESH_SIZE = 5_156
RESIDENT_WALKMESH_SHA256 = "6d36a3fc267029bc2e65ee9ae7435208be0a7934c9aa86af3fa1fd580548b932"
SOURCE_GAMESTATE_SHA256 = "dbe1b595455cd51142dd45effbdaa86cb10b3e9500021c1ee055259c6940063e"
SOURCE_CAMERA_SHA256 = "2bb59a4ef707423774b34c620cc37c522368f306072eebfa3ab5abf0e13432c9"


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output whenever the pinned V219/V220 contract drifts."""


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
    if len(compressed) > 0xFFFFFFFF:
        raise SurfaceSlotMigrationError("Recompressed payload exceeds its 32-bit header field")
    result_prefix = bytearray(prefix)
    struct.pack_into(
        "<I",
        result_prefix,
        media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        len(compressed),
    )
    return bytes(result_prefix) + compressed


def _expected_prefix(source_prefix: bytes, *, compressed_size: int) -> bytes:
    old_name = OLD_CUE_NAME.encode("ascii")
    new_name = NEW_CUE_NAME.encode("ascii")
    if len(old_name) != len(new_name) or source_prefix.count(old_name) != 1:
        raise SurfaceSlotMigrationError("Pinned V219 media path changed")
    if new_name in source_prefix:
        raise SurfaceSlotMigrationError("Source state already names the V220 media")
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
        raise SurfaceSlotMigrationError("Serialized PSX RAM payload offset drifted")
    ram = payload[offset : offset + RAM_SIZE]
    if len(ram) != RAM_SIZE:
        raise SurfaceSlotMigrationError("Serialized PSX RAM span is truncated")
    return offset, ram


def _camera_snapshot(ram: bytes) -> bytes:
    return b"".join(ram[address : address + 16] for address in CAMERA_VECTORS.values())


def _actor_data_snapshot(ram: bytes, actor_base: int, actor_count: int) -> bytes:
    chunks: list[bytes] = []
    for entity in range(actor_count):
        record = actor_base + entity * FIELD_ACTOR_STRIDE
        pointer = struct.unpack_from("<I", ram, record + FIELD_ACTOR_DATA_POINTER)[0]
        offset = pointer & 0x1FFFFFFF
        if offset == 0:
            continue
        if offset > RAM_SIZE - ACTOR_DATA_SIZE:
            raise SurfaceSlotMigrationError(f"e{entity} ActorData pointer is outside PSX RAM")
        chunks.append(ram[offset : offset + ACTOR_DATA_SIZE])
    return b"".join(chunks)


def _model_layout(
    model: bytes,
    *,
    guest_base: int,
    expected_size: int,
    expected_counts: tuple[int, int, int],
    expected_offsets: tuple[int, int, int, int],
) -> tuple[tuple[int, int, int], ...]:
    if len(model) != expected_size or struct.unpack_from("<I", model)[0] != 1:
        raise SurfaceSlotMigrationError("Resident model container layout changed")
    if struct.unpack_from("<HHH", model, 0x12) != expected_counts:
        raise SurfaceSlotMigrationError("Resident model header counts changed")
    pointers = struct.unpack_from("<4I", model, 0x18)
    relative = tuple((pointer & 0x1FFFFFFF) - guest_base for pointer in pointers)
    if relative != expected_offsets:
        raise SurfaceSlotMigrationError("Resident model relocated offsets changed")
    mesh_offset = relative[2]
    display_offset = relative[3]
    inventory: list[tuple[int, int, int]] = []
    cursor = mesh_offset
    for _ in range(expected_counts[2]):
        primitive_type, unknown, count = struct.unpack_from("<BBH", model, cursor)
        inventory.append((primitive_type, unknown, count))
        cursor += 4 + count * 8
    if cursor != display_offset:
        raise SurfaceSlotMigrationError("Resident model mesh span changed")
    return tuple(inventory)


def _validate_runtime_models(source_ram: bytes, output_ram: bytes) -> None:
    source_model2 = source_ram[
        RUNTIME_MODEL2_OFFSET : RUNTIME_MODEL2_OFFSET + RUNTIME_MODEL2_SIZE
    ]
    output_model2 = output_ram[
        RUNTIME_MODEL2_OFFSET : RUNTIME_MODEL2_OFFSET + RUNTIME_MODEL2_SIZE
    ]
    if _sha256(source_model2) != SOURCE_RUNTIME_MODEL2_SHA256:
        raise SurfaceSlotMigrationError("Pinned resident V219 model 2 changed")
    if _sha256(output_model2) != OUTPUT_RUNTIME_MODEL2_SHA256:
        raise SurfaceSlotMigrationError("Resident V220 model 2 reconstruction changed")
    for model in (source_model2, output_model2):
        if (
            _model_layout(
                model,
                guest_base=RUNTIME_MODEL2_OFFSET,
                expected_size=RUNTIME_MODEL2_SIZE,
                expected_counts=(213, 210, 4),
                expected_offsets=(0x48, 0x48, 0x6F0, 0xD80),
            )
            != MODEL2_EXPECTED_LAYOUT
        ):
            raise SurfaceSlotMigrationError("Resident model 2 mesh inventory changed")
    for start, end in MODEL2_ZERO_RANGES:
        if output_model2[start:end] != bytes(end - start):
            raise SurfaceSlotMigrationError("Resident V220 model 2 is not inert")

    source_model20 = source_ram[
        RUNTIME_MODEL20_OFFSET : RUNTIME_MODEL20_OFFSET + RUNTIME_MODEL20_SIZE
    ]
    output_model20 = output_ram[
        RUNTIME_MODEL20_OFFSET : RUNTIME_MODEL20_OFFSET + RUNTIME_MODEL20_SIZE
    ]
    if _sha256(source_model20) != SOURCE_RUNTIME_MODEL20_SHA256:
        raise SurfaceSlotMigrationError("Pinned resident V219 model 20 changed")
    if _sha256(output_model20) != OUTPUT_RUNTIME_MODEL20_SHA256:
        raise SurfaceSlotMigrationError("Resident V220 model 20 reconstruction changed")
    for model in (source_model20, output_model20):
        if (
            _model_layout(
                model,
                guest_base=RUNTIME_MODEL20_OFFSET,
                expected_size=RUNTIME_MODEL20_SIZE,
                expected_counts=(16, 18, 1),
                expected_offsets=(0x48, 0x48, 0xC8, 0x14C),
            )
            != MODEL20_EXPECTED_LAYOUT
        ):
            raise SurfaceSlotMigrationError("Resident model 20 mesh inventory changed")
    for start, end in MODEL20_ZERO_RANGES:
        if source_model20[start:end] != bytes(end - start):
            raise SurfaceSlotMigrationError("Pinned V219 model 20 is not already inert")
        if output_model20[start:end] != bytes(end - start):
            raise SurfaceSlotMigrationError("Resident V220 model 20 is not inert")


def _validate_preserved_field_state(source_ram: bytes, output_ram: bytes) -> None:
    actor_count = struct.unpack_from("<I", source_ram, FIELD_NUM_ACTORS)[0]
    actor_base = struct.unpack_from("<I", source_ram, FIELD_ACTORS)[0] & 0x1FFFFFFF
    if (actor_count, actor_base) != (EXPECTED_FIELD_ACTOR_COUNT, EXPECTED_FIELD_ACTORS):
        raise SurfaceSlotMigrationError("Loaded field-621 actor layout changed")
    if (
        struct.unpack_from("<I", output_ram, FIELD_NUM_ACTORS)[0] != actor_count
        or (struct.unpack_from("<I", output_ram, FIELD_ACTORS)[0] & 0x1FFFFFFF)
        != actor_base
    ):
        raise SurfaceSlotMigrationError("V220 actor layout was not preserved")

    actor_array_size = actor_count * FIELD_ACTOR_STRIDE
    source_actors = source_ram[actor_base : actor_base + actor_array_size]
    output_actors = output_ram[actor_base : actor_base + actor_array_size]
    source_actor_data = _actor_data_snapshot(source_ram, actor_base, actor_count)
    output_actor_data = _actor_data_snapshot(output_ram, actor_base, actor_count)
    if (
        _sha256(source_actors) != SOURCE_ACTOR_ARRAY_SHA256
        or _sha256(source_actor_data) != SOURCE_ACTOR_DATA_SHA256
    ):
        raise SurfaceSlotMigrationError("Pinned actor or collision state changed")
    if output_actors != source_actors or output_actor_data != source_actor_data:
        raise SurfaceSlotMigrationError("Actor or collision state was not preserved")

    preserved_ranges = (
        (GAME_STATE, GAMESTATE_SIZE, SOURCE_GAMESTATE_SHA256, "GameState"),
        (LOADED_HEADER_OFFSET, LOADED_HEADER_SIZE, LOADED_HEADER_SHA256, "field header"),
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
    )
    for offset, size, expected_hash, label in preserved_ranges:
        source = source_ram[offset : offset + size]
        output = output_ram[offset : offset + size]
        if _sha256(source) != expected_hash:
            raise SurfaceSlotMigrationError(f"Pinned {label} identity changed")
        if output != source:
            raise SurfaceSlotMigrationError(f"{label} was not preserved")
    source_camera = _camera_snapshot(source_ram)
    if _sha256(source_camera) != SOURCE_CAMERA_SHA256:
        raise SurfaceSlotMigrationError("Pinned camera identity changed")
    if _camera_snapshot(output_ram) != source_camera:
        raise SurfaceSlotMigrationError("Camera state was not preserved")


def _geometry_changed_payload_offsets(source_ram: bytes, ram_offset: int) -> set[int]:
    changed: set[int] = set()
    for model_offset, ranges in (
        (RUNTIME_MODEL2_OFFSET, MODEL2_ZERO_RANGES),
        (RUNTIME_MODEL20_OFFSET, MODEL20_ZERO_RANGES),
    ):
        for start, end in ranges:
            for relative, value in enumerate(source_ram[model_offset + start : model_offset + end], start):
                if value:
                    changed.add(ram_offset + model_offset + relative)
    return changed


def migrate_v219_slot1_to_v220(
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
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V219 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V220 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V219 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V220 CUE"),
    )
    for path, size, sha256, label in identities:
        _validate_file(path, size, sha256, label)

    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    if (
        len(old_table) != ARCHIVE_TABLE_SIZE
        or _sha256(old_table) != OLD_ARCHIVE_TABLE_SHA256
        or _sha256(new_table) != NEW_ARCHIVE_TABLE_SHA256
        or _diff_triplets(old_table, new_table) != ARCHIVE_TABLE_DIFFS
    ):
        raise SurfaceSlotMigrationError("V219/V220 archive-table delta changed")

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
    source_resident_table = source_payload[table_offset : table_offset + ARCHIVE_TABLE_SIZE]
    if (
        table_offset != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or volatile_bytes != 1
        or source_resident_table[-1] != EXPECTED_VOLATILE_TABLE_VALUE
        or _sha256(source_resident_table) != SOURCE_RESIDENT_TABLE_SHA256
    ):
        raise SurfaceSlotMigrationError("Pinned resident V219 archive table changed")

    ram_offset, source_ram = _ram_from_payload(source_payload)
    if _sha256(source_ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("Pinned V219 RAM identity changed")
    # Validate both source model identities and all relocated mesh pointers
    # before mutating the payload.  Passing source as output deliberately fails
    # only model 2's target hash, so validate source layouts directly here.
    source_model2 = source_ram[
        RUNTIME_MODEL2_OFFSET : RUNTIME_MODEL2_OFFSET + RUNTIME_MODEL2_SIZE
    ]
    source_model20 = source_ram[
        RUNTIME_MODEL20_OFFSET : RUNTIME_MODEL20_OFFSET + RUNTIME_MODEL20_SIZE
    ]
    if (
        _sha256(source_model2) != SOURCE_RUNTIME_MODEL2_SHA256
        or _sha256(source_model20) != SOURCE_RUNTIME_MODEL20_SHA256
    ):
        raise SurfaceSlotMigrationError("Pinned resident V219 geometry changed")
    if (
        _model_layout(
            source_model2,
            guest_base=RUNTIME_MODEL2_OFFSET,
            expected_size=RUNTIME_MODEL2_SIZE,
            expected_counts=(213, 210, 4),
            expected_offsets=(0x48, 0x48, 0x6F0, 0xD80),
        )
        != MODEL2_EXPECTED_LAYOUT
        or _model_layout(
            source_model20,
            guest_base=RUNTIME_MODEL20_OFFSET,
            expected_size=RUNTIME_MODEL20_SIZE,
            expected_counts=(16, 18, 1),
            expected_offsets=(0x48, 0x48, 0xC8, 0x14C),
        )
        != MODEL20_EXPECTED_LAYOUT
    ):
        raise SurfaceSlotMigrationError("Pinned resident V219 model inventory changed")
    for start, end in MODEL20_ZERO_RANGES:
        if source_model20[start:end] != bytes(end - start):
            raise SurfaceSlotMigrationError("Pinned V219 model 20 is not already inert")

    expected_geometry_offsets = _geometry_changed_payload_offsets(source_ram, ram_offset)
    if len(expected_geometry_offsets) != EXPECTED_GEOMETRY_BYTES_CHANGED:
        raise SurfaceSlotMigrationError("Pinned geometry byte-change count drifted")

    output_payload = bytearray(source_payload)
    for relative, old, new in ARCHIVE_TABLE_DIFFS:
        offset = table_offset + relative
        if output_payload[offset] != old:
            raise SurfaceSlotMigrationError(
                f"Resident archive table drifted at relative offset 0x{relative:04X}"
            )
        output_payload[offset] = new
    if output_payload[table_offset + ARCHIVE_TABLE_SIZE - 1] != EXPECTED_VOLATILE_TABLE_VALUE:
        raise SurfaceSlotMigrationError("Resident archive table's volatile byte was not preserved")
    if (
        _sha256(output_payload[table_offset : table_offset + ARCHIVE_TABLE_SIZE])
        != OUTPUT_RESIDENT_TABLE_SHA256
    ):
        raise SurfaceSlotMigrationError("Resident V220 archive table reconstruction changed")

    for model_offset, ranges in (
        (RUNTIME_MODEL2_OFFSET, MODEL2_ZERO_RANGES),
        (RUNTIME_MODEL20_OFFSET, MODEL20_ZERO_RANGES),
    ):
        for start, end in ranges:
            absolute = ram_offset + model_offset + start
            output_payload[absolute : absolute + end - start] = bytes(end - start)

    output_payload_bytes = bytes(output_payload)
    _output_ram_offset, output_ram = _ram_from_payload(output_payload_bytes)
    _validate_runtime_models(source_ram, output_ram)
    _validate_preserved_field_state(source_ram, output_ram)

    expected_payload_offsets = {
        *(table_offset + relative for relative, _old, _new in ARCHIVE_TABLE_DIFFS),
        *expected_geometry_offsets,
    }
    changed_offsets = _diff_offsets(source_payload, output_payload_bytes)
    if (
        set(changed_offsets) != expected_payload_offsets
        or len(changed_offsets) != EXPECTED_PAYLOAD_BYTES_CHANGED
        or _sha256(output_payload_bytes) != OUTPUT_PAYLOAD_SHA256
        or _sha256(output_ram) != OUTPUT_RAM_SHA256
    ):
        raise SurfaceSlotMigrationError("V220 payload changed outside the exact byte whitelist")

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
        raise SurfaceSlotMigrationError("Final V220 state identity or round trip changed")

    model2_changed = len(
        _diff_offsets(
            source_ram[
                RUNTIME_MODEL2_OFFSET : RUNTIME_MODEL2_OFFSET + RUNTIME_MODEL2_SIZE
            ],
            output_ram[
                RUNTIME_MODEL2_OFFSET : RUNTIME_MODEL2_OFFSET + RUNTIME_MODEL2_SIZE
            ],
        )
    )
    model20_changed = len(
        _diff_offsets(
            source_ram[
                RUNTIME_MODEL20_OFFSET : RUNTIME_MODEL20_OFFSET + RUNTIME_MODEL20_SIZE
            ],
            output_ram[
                RUNTIME_MODEL20_OFFSET : RUNTIME_MODEL20_OFFSET + RUNTIME_MODEL20_SIZE
            ],
        )
    )
    if (
        model2_changed != EXPECTED_MODEL2_BYTES_CHANGED
        or model20_changed != EXPECTED_MODEL20_BYTES_CHANGED
    ):
        raise SurfaceSlotMigrationError("Resident geometry change counts drifted")

    report: dict[str, object] = {
        "source_sha256": SOURCE_STATE_SHA256,
        "output_sha256": OUTPUT_STATE_SHA256,
        "source_size": len(state),
        "output_size": len(result),
        "payload_size": len(output_payload_bytes),
        "payload_sha256": OUTPUT_PAYLOAD_SHA256,
        "payload_bytes_changed": len(changed_offsets),
        "archive_table_bytes_changed": len(ARCHIVE_TABLE_DIFFS),
        "model2_bytes_changed": model2_changed,
        "model20_bytes_changed": model20_changed,
        "geometry_bytes_changed": model2_changed + model20_changed,
        "resident_archive_table_sha256": OUTPUT_RESIDENT_TABLE_SHA256,
        "resident_model2_sha256": OUTPUT_RUNTIME_MODEL2_SHA256,
        "resident_model20_sha256": OUTPUT_RUNTIME_MODEL20_SHA256,
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "actor_header_game_camera_script_collision_preserved": True,
        "volatile_archive_table_byte_preserved": True,
        "model20_already_inert_and_preserved": True,
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
            / "SLUS-00669_1_v219_latest_camera_glitch_3081ee5d.sav"
        ),
    )
    parser.add_argument(
        "--old-disc",
        type=Path,
        default=(
            PROJECT_ROOT
            / "output"
            / "Xenogears_PW_CD2_mass_driver_surface_soylent_v219.bin"
        ),
    )
    parser.add_argument(
        "--new-disc",
        type=Path,
        default=(
            PROJECT_ROOT
            / "output"
            / "Xenogears_PW_CD2_mass_driver_surface_soylent_v220.bin"
        ),
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
            / "SLUS-00669_1_v220_from_3081ee5d_camera_occluder_fix.sav"
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
        if source == output:
            raise SurfaceSlotMigrationError("Output must not overwrite the source state")
        if output == LIVE_SLOT1:
            raise SurfaceSlotMigrationError("The migration tool never writes live Slot 1")
        if output.exists() and not args.force:
            raise SurfaceSlotMigrationError(f"Output already exists: {output}")
        zstd = media_migration._Zstd(args.zstd.resolve())
        result, report = migrate_v219_slot1_to_v220(
            source.read_bytes(),
            old_disc=args.old_disc.resolve(),
            new_disc=args.new_disc.resolve(),
            zstd=zstd,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        if output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Written V220 candidate changed on disk")
        if args.report:
            report_path = args.report.resolve()
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote validated V220 candidate: {output}")
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, media_migration.StateMigrationError, SurfaceSlotMigrationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
