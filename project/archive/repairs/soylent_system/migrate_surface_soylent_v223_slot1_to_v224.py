#!/usr/bin/env python3
"""Migrate the exact V223 Intake Slot 1 state to V224 safely.

V224 replaces model 20's two half-width threshold quads with one retail-style
full-width quad.  Its 396-byte resident allocation and all six 0x140-byte GPU
packet allocations remain fixed, but the topology changes from two POLY_FT4
plus twelve inert POLY_F3 records to one POLY_FT4 plus fourteen inert POLY_F3
records.  The serialized packet arenas must therefore be rebuilt in place;
mounting the new disc alone would reinterpret V223 packet data incorrectly.

This tool accepts only the preserved V223 bottom-left-clipping state.  It pins
both media images, field 621, the old and new model layouts, every source and
target runtime arena, and the deterministic output.  Its payload whitelist is
limited to resident model 20 and those six arenas.  The player, camera,
gameplay, loaded header, scripts, actors, collision, archive table, allocation
pointers, and every unrelated byte are preserved.  Live DuckStation Slot 1 is
never written.
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
import tools.migrate_surface_soylent_v222_slot1_to_v223 as v223_migration  # noqa: E402
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

SOURCE_STATE_SIZE = 1_672_493
SOURCE_STATE_SHA256 = "b962464676e5c2b9a59918a5b9247d5d747276ab6ec0fc4a36c1f5f48ae96d24"
SOURCE_COMPRESSED_SIZE = 1_618_732
SOURCE_COMPRESSED_SHA256 = "af318e188979fa264998c98bd88600e825d325b9c40d6bed6fdbfc29b2ebaa5a"
SOURCE_PREFIX_SIZE = 53_761
SOURCE_PREFIX_SHA256 = "f7bee459c6cacbda746c7fe132417bba31f682318a30b1e03a4651e0114241a7"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "c637a743bf702efbc2bec2f599d0531c3c1517f9c846d5280cb3f94162f55e54"
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
SOURCE_RAM_SHA256 = "24734bc3ae6d7b47d14447806d88a173e0fc3e59b30f5c65782e5b68366cea37"

OUTPUT_STATE_SIZE = 1_513_683
OUTPUT_STATE_SHA256 = "fab19182ff32d0ec0e25f8ef334f1e3604ee407dea29fcf180c3cd2dd14156bb"
OUTPUT_COMPRESSED_SIZE = 1_459_922
OUTPUT_COMPRESSED_SHA256 = "cdaeda46d895c67ff00b9feaabd3ed08033db9924f588b7faaddeb9db48236eb"
OUTPUT_PREFIX_SHA256 = "a506bbe7ca174c7da769b79ee5841e2c4698ce2058ea1b75b24d577a8e672c11"
OUTPUT_PAYLOAD_SHA256 = "b74fea8bf8be9d12394afe99afb9ed0c21f6451b273c8c6d94cdff4a412971b3"
OUTPUT_RAM_SHA256 = "b2a4cd510c004f7b6ed4b9934f2f8098d56f58bc87768ef179854e9793662a53"

OLD_DISC_SIZE = NEW_DISC_SIZE = 698_642_784
OLD_DISC_SHA256 = v223_migration.NEW_DISC_SHA256
NEW_DISC_SHA256 = "6d0854e878f677eee7e8c57fd5084d0f28b9cc776b758934925ef353da30022d"
OLD_CUE_NAME = v223_migration.NEW_CUE_NAME
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v224.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = v223_migration.NEW_CUE_SHA256
NEW_CUE_SHA256 = "4cd7c8be1096148c00d619f776754e6e15cf55dffcc9a3cc97b8887af333944d"

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = v223_migration.NEW_ARCHIVE_TABLE_SHA256
NEW_ARCHIVE_TABLE_SHA256 = "9ece390ff3c1d88d8604892f3355ec1f70687d3931a3a8f06b60fc5d27ce362c"
MEDIA_ARCHIVE_TABLE_DIFFS = ((0x3268, 0xE4, 0xE0),)
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
EXPECTED_VOLATILE_TABLE_VALUE = 0xE0
RESIDENT_ARCHIVE_TABLE_SHA256 = v223_migration.RESIDENT_ARCHIVE_TABLE_SHA256
RESIDENT_VS_OLD_MEDIA_DIFFS = (
    (0x3268, 0xE8, 0xE4),
    (0x7FFF, 0xE0, 0x00),
)

FIELD621_FAT_INDEX = 1843
FIELD621_CANONICAL_DISC2_INDEX = 1848
FIELD621_MODEL_COMPONENT_INDEX = 2
FIELD621_MODEL20_INDEX = 20
FIELD621_MODEL_COUNT = 21
OLD_FIELD621_BUNDLE_SIZE = v223_migration.NEW_FIELD621_BUNDLE_SIZE
OLD_FIELD621_BUNDLE_SHA256 = v223_migration.NEW_FIELD621_BUNDLE_SHA256
NEW_FIELD621_BUNDLE_SIZE = 135_648
NEW_FIELD621_BUNDLE_SHA256 = "011be9593a2c565e6c3bb5f325ef64ac47811592794945ce529fcb3b6eb36677"
FIELD_HEADER_SIZE = 1_408
OLD_DISK_HEADER_SHA256 = v223_migration.NEW_DISK_HEADER_SHA256
NEW_DISK_HEADER_SHA256 = "bd8be9feef57bff074c81c885d66b329ed20456e42d3a11c6b8e03b18550598f"
FIELD_HEADER_DIFF_TRIPLETS = (
    (0x13C, 0x3C, 0x38),
    (0x140, 0x38, 0x34),
    (0x144, 0xF0, 0xEC),
    (0x148, 0x5C, 0x58),
    (0x14C, 0x30, 0x2C),
    (0x150, 0xE0, 0xDC),
)
FIELD621_MODEL_ARCHIVE_SIZE = 39_292
OLD_FIELD621_MODEL_ARCHIVE_SHA256 = v223_migration.NEW_FIELD621_MODEL_ARCHIVE_SHA256
NEW_FIELD621_MODEL_ARCHIVE_SHA256 = "b06e38c58fcd5e1ce5033e1135f0ae7c7d745b9ef37575f44b0cba4c936c52aa"
RESIDENT_SCRIPT_SIZE = 10_895
DISK_SCRIPT_SHA256 = v223_migration.DISK_SCRIPT_SHA256

RUNTIME_MODEL20_OFFSET = model_migration.RUNTIME_MODEL20_OFFSET
RUNTIME_MODEL20_SIZE = model_migration.RUNTIME_MODEL20_SIZE
RUNTIME_MODEL20_ARENA_SIZE = model_migration.RUNTIME_MODEL20_ARENA_SIZE
RUNTIME_MODEL20_GUEST_BLOCK_POINTER = model_migration.RUNTIME_MODEL20_GUEST_BLOCK_POINTER
MODEL20_INSTANCE_LAYOUT = model_migration.MODEL20_INSTANCE_LAYOUT
MODEL20_RUNTIME_PRIMITIVE_OVERHEAD = model_migration.MODEL20_RUNTIME_PRIMITIVE_OVERHEAD
OLD_DISK_MODEL20_SHA256 = v223_migration.NEW_DISK_MODEL20_SHA256
NEW_DISK_MODEL20_SHA256 = "8ef50d3f377c7b8caf2fdcfa0fcaecebe3d25ce5a51a90dfa0f14a734fdf3b52"
SOURCE_RUNTIME_MODEL20_SHA256 = v223_migration.TARGET_RUNTIME_MODEL20_SHA256
TARGET_RUNTIME_MODEL20_SHA256 = "af389e6da468c4a5875d2bd4271574654a34fcd2ca6f62e235771fddfc03c03d"
OLD_MODEL20_DISK_COUNTS = (15, 14, 2)
OLD_MODEL20_RUNTIME_COUNTS = (15, 16, 2)
OLD_MODEL20_OFFSETS = (0x48, 0x48, 0xC0, 0x138)
OLD_MODEL20_INVENTORY = ((0x0D, 0x77, 2), (0x04, 0x77, 12))
NEW_MODEL20_DISK_COUNTS = (15, 15, 2)
NEW_MODEL20_RUNTIME_COUNTS = (15, 17, 2)
NEW_MODEL20_OFFSETS = (0x48, 0x48, 0xC0, 0x140)
NEW_MODEL20_INVENTORY = ((0x0D, 0x77, 1), (0x04, 0x77, 14))

DISK_MODEL20_DIFF_TRIPLETS = (
    (0x014, 0x0E, 0x0F),
    (0x024, 0x38, 0x40),
    (0x0C2, 0x02, 0x01),
    (0x0C8, 0x02, 0x04),
    (0x0CA, 0x03, 0x05),
    (0x0CC, 0x02, 0x04),
    (0x0CD, 0x00, 0x77),
    (0x0CE, 0x03, 0x0E),
    (0x0D0, 0x04, 0x00),
    (0x0D2, 0x05, 0x00),
    (0x0D4, 0x04, 0x00),
    (0x0D5, 0x77, 0x00),
    (0x0D6, 0x0C, 0x00),
    (0x138, 0xA8, 0x00),
    (0x13B, 0xC4, 0x00),
    (0x13D, 0x79, 0x00),
    (0x13F, 0xC8, 0x00),
    (0x140, 0x00, 0xA8),
    (0x143, 0x2D, 0xC4),
    (0x144, 0x97, 0x00),
    (0x145, 0x89, 0x79),
    (0x146, 0x97, 0x00),
    (0x147, 0x8D, 0xC8),
    (0x148, 0xA6, 0x00),
    (0x149, 0x89, 0x00),
    (0x14A, 0xA6, 0x00),
    (0x14B, 0x8D, 0x2D),
    (0x14C, 0x00, 0x97),
    (0x14D, 0x00, 0x89),
    (0x14E, 0x00, 0x97),
    (0x14F, 0x2D, 0x8D),
    (0x150, 0xA6, 0xB6),
    (0x152, 0xA6, 0xB6),
    (0x154, 0xB6, 0x00),
    (0x155, 0x89, 0x00),
    (0x156, 0xB6, 0x00),
    (0x157, 0x8D, 0x20),
    (0x18B, 0x00, 0x20),
)
RUNTIME_MODEL20_DIFF_TRIPLETS = (
    (0x014, 0x10, 0x11),
    (0x024, 0x50, 0x58),
    *DISK_MODEL20_DIFF_TRIPLETS[2:],
)
MODEL20_ARCHIVE_ENTRY_OFFSET = 0x97F0
MODEL_ARCHIVE_DIFF_TRIPLETS = tuple(
    (MODEL20_ARCHIVE_ENTRY_OFFSET + offset, old, new)
    for offset, old, new in DISK_MODEL20_DIFF_TRIPLETS
)

NEW_MODEL20_DISPLAY_BYTES = bytes.fromhex(
    "A8 00 00 C4 00 79 00 C8 "
    "00 00 00 2D 97 89 97 8D B6 89 B6 8D"
) + bytes.fromhex("00 00 00 20") * 14
TARGET_PACKET_ARENA_SHA256 = "3c03f04c72c2424d4a5faa272ef4d8e855dd647360b00e210bcbe02f6e0bd508"
TARGET_PACKET_ARENAS_SHA256 = "5574ecb24ef25954a3ecb136ea9def40b82e94d4de4927f9c1e552d2bab13680"
SOURCE_PACKET_ARENA_SHA256 = (
    "4de6d5520185585921b3d0ca4a38f61b70175d9ec691a113a7c01d2d9d7e5247",
    "6cde72becccb61c524a6a54b592bba8030aa7a7752c96dff55413bbb59688366",
    "fbfa9faabe33d7862da2f5ce7565f6cbe2c3a23a5dfae652a28c34e9f27aeac4",
    "1ba3287cafd3103092be7b8c8af52fc57b93f9967fe580dc59c1198f2dcf4c0c",
    "9e933caf321913a3e22a049ca207167522e13292bc41ae87d7a9c37ca37a255c",
    "b85b495b5a7b2134447d3bc93d0217ae6a20322a27f07853b96ed9e982e9cee6",
)
SOURCE_PACKET_ARENAS_SHA256 = "28233bf041a5c88d0389127d04229c83aea618d538b4d55a9ac272bb6005c0c2"
EXPECTED_PACKET_ARENA_DIFF_COUNTS = (67, 65, 62, 62, 62, 62)

RUNTIME_MODEL2_OFFSET = v223_migration.RUNTIME_MODEL2_OFFSET
RUNTIME_MODEL2_SIZE = v223_migration.RUNTIME_MODEL2_SIZE
RUNTIME_MODEL2_SHA256 = v223_migration.RUNTIME_MODEL2_SHA256
EXPECTED_FIELD_ACTOR_COUNT = 63
EXPECTED_FIELD_ACTORS = 0x11B0D4
ACTOR_ARRAY_SIZE = EXPECTED_FIELD_ACTOR_COUNT * FIELD_ACTOR_STRIDE
ACTOR_DATA_SIZE = 0x138
SOURCE_ACTOR_ARRAY_SHA256 = "36197cf70643da8abf6fb8a23eb85fcfd37cf32fd2ca30659a96b7ef342bad58"
SOURCE_ACTOR_DATA_SHA256 = "42c00c31ca713b9b84786cd4098bf0280febbcbb54b63ccfa2acc4e9d75f46de"
LOADED_HEADER_OFFSET = v223_migration.LOADED_HEADER_OFFSET
LOADED_HEADER_SHA256 = v223_migration.LOADED_HEADER_SHA256
RESIDENT_SCRIPT_OFFSET = v223_migration.RESIDENT_SCRIPT_OFFSET
RESIDENT_SCRIPT_SHA256 = v223_migration.RESIDENT_SCRIPT_SHA256
RESIDENT_DIALOGUE_OFFSET = v223_migration.RESIDENT_DIALOGUE_OFFSET
RESIDENT_DIALOGUE_SIZE = v223_migration.RESIDENT_DIALOGUE_SIZE
RESIDENT_DIALOGUE_SHA256 = v223_migration.RESIDENT_DIALOGUE_SHA256
RESIDENT_WALKMESH_OFFSET = v223_migration.RESIDENT_WALKMESH_OFFSET
RESIDENT_WALKMESH_SIZE = v223_migration.RESIDENT_WALKMESH_SIZE
RESIDENT_WALKMESH_SHA256 = v223_migration.RESIDENT_WALKMESH_SHA256
SOURCE_GAMESTATE_SHA256 = "ad50b4d22babe8089b8be08e8898ee5a2e979574af03ab70a0cdd0a4ff8c4f43"
SOURCE_CAMERA_SHA256 = "fcc1f8df2e47fc46623664baa0563f88b56856a97c86b2bdba7015366cc3a333"

EXPECTED_MODEL20_BYTES_CHANGED = 38
EXPECTED_PACKET_ARENA_COUNT = 6
EXPECTED_PACKET_ARENA_BYTES_CHANGED = 380
EXPECTED_RESIDENT_RENDER_BYTES_CHANGED = 418
EXPECTED_RAM_BYTES_CHANGED = 418
EXPECTED_PAYLOAD_BYTES_CHANGED = 418
EXPECTED_PREFIX_BYTES_CHANGED = 4


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output whenever the pinned V223/V224 contract drifts."""


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
        return v223_migration._unpack_state(state, zstd)
    except v223_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc


def _pack_state(prefix: bytes, payload: bytes, zstd: _ZstdLike) -> bytes:
    try:
        return v223_migration._pack_state(prefix, payload, zstd)
    except v223_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc


def _ram_from_payload(payload: bytes) -> tuple[int, bytes]:
    try:
        offset, ram = v223_migration._ram_from_payload(payload)
    except v223_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc
    if offset != EXPECTED_RAM_PAYLOAD_OFFSET:
        raise SurfaceSlotMigrationError("Serialized PSX RAM payload offset drifted")
    return offset, ram


def _expected_prefix(source_prefix: bytes, *, compressed_size: int) -> bytes:
    old_name = OLD_CUE_NAME.encode("ascii")
    new_name = NEW_CUE_NAME.encode("ascii")
    if len(old_name) != len(new_name) or source_prefix.count(old_name) != 1:
        raise SurfaceSlotMigrationError("Pinned V223 media path changed")
    if new_name in source_prefix:
        raise SurfaceSlotMigrationError("Source state already names the V224 media")
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
    expected_offsets: tuple[int, int, int, int],
) -> tuple[tuple[int, int, int], ...]:
    try:
        return model_migration._model_layout(
            model,
            guest_base=guest_base,
            expected_counts=expected_counts,
            expected_offsets=expected_offsets,
        )
    except model_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc


def _runtime_model20(disk_model: bytes) -> bytes:
    try:
        return model_migration._runtime_model20(disk_model)
    except model_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc


def _fresh_packet_arena(runtime_model: bytes) -> bytes:
    display_offset = (
        struct.unpack_from("<I", runtime_model, 0x24)[0] & 0x1FFFFFFF
    ) - RUNTIME_MODEL20_OFFSET
    display = runtime_model[display_offset:]
    if display != NEW_MODEL20_DISPLAY_BYTES:
        raise SurfaceSlotMigrationError("V224 model-20 display list changed")
    if struct.unpack_from("<I", runtime_model, 0x44)[0] != RUNTIME_MODEL20_ARENA_SIZE:
        raise SurfaceSlotMigrationError("V224 model-20 packet allocation changed")

    state = display[:8]
    if state != bytes.fromhex("A8 00 00 C4 00 79 00 C8"):
        raise SurfaceSlotMigrationError("V224 threshold texture state changed")
    tpage = 0x00A8
    clut = 0x7900

    record = display[8:20]
    if record != bytes.fromhex("00 00 00 2D 97 89 97 8D B6 89 B6 8D"):
        raise SurfaceSlotMigrationError("V224 full-width POLY_FT4 record changed")
    ft4 = bytearray(0x28)
    ft4[3] = 9
    ft4[4:8] = record[:4]
    ft4[12:14] = record[4:6]
    struct.pack_into("<H", ft4, 14, clut)
    ft4[20:22] = record[6:8]
    struct.pack_into("<H", ft4, 22, tpage)
    ft4[28:30] = record[8:10]
    ft4[36:38] = record[10:12]

    cursor = 20
    packets = bytearray(ft4)
    for _ in range(14):
        inert = display[cursor : cursor + 4]
        if inert != bytes.fromhex("00 00 00 20"):
            raise SurfaceSlotMigrationError("V224 inert POLY_F3 record changed")
        packet = bytearray(0x14)
        packet[3] = 4
        packet[4:8] = inert
        packets.extend(packet)
        cursor += 4
    arena = bytes(packets)
    if (
        cursor != len(display)
        or len(arena) != RUNTIME_MODEL20_ARENA_SIZE
        or _sha256(arena) != TARGET_PACKET_ARENA_SHA256
    ):
        raise SurfaceSlotMigrationError("V224 packet-arena reconstruction changed")
    return arena


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
    source_model = source_ram[
        RUNTIME_MODEL20_OFFSET : RUNTIME_MODEL20_OFFSET + RUNTIME_MODEL20_SIZE
    ]
    if (
        source_model != old_runtime_model
        or _sha256(source_model) != SOURCE_RUNTIME_MODEL20_SHA256
        or _diff_triplets(source_model, target_runtime_model)
        != RUNTIME_MODEL20_DIFF_TRIPLETS
    ):
        raise SurfaceSlotMigrationError("Pinned V223 resident model-20 identity or delta changed")
    if _sha256(target_runtime_model) != TARGET_RUNTIME_MODEL20_SHA256:
        raise SurfaceSlotMigrationError("Resident V224 model-20 reconstruction changed")

    source_arena_offsets = _packet_arena_offsets(
        source_ram, expected_hashes=SOURCE_PACKET_ARENA_SHA256
    )
    if _sha256(_packet_arenas(source_ram)) != SOURCE_PACKET_ARENAS_SHA256:
        raise SurfaceSlotMigrationError("Pinned V223 packet-arena set changed")
    target_arena = _fresh_packet_arena(target_runtime_model)

    model_offsets = frozenset(
        RUNTIME_MODEL20_OFFSET + relative
        for relative in _diff_offsets(source_model, target_runtime_model)
    )
    arena_diff_sets = tuple(
        frozenset(
            arena_offset + relative
            for relative in _diff_offsets(
                source_ram[
                    arena_offset : arena_offset + RUNTIME_MODEL20_ARENA_SIZE
                ],
                target_arena,
            )
        )
        for arena_offset in source_arena_offsets
    )
    packet_offsets = frozenset().union(*arena_diff_sets)
    if (
        len(model_offsets) != EXPECTED_MODEL20_BYTES_CHANGED
        or tuple(len(offsets) for offsets in arena_diff_sets)
        != EXPECTED_PACKET_ARENA_DIFF_COUNTS
        or len(packet_offsets) != EXPECTED_PACKET_ARENA_BYTES_CHANGED
        or len(model_offsets | packet_offsets) != EXPECTED_RESIDENT_RENDER_BYTES_CHANGED
    ):
        raise SurfaceSlotMigrationError("Pinned resident render byte counts changed")

    target = bytearray(source_ram)
    target[
        RUNTIME_MODEL20_OFFSET : RUNTIME_MODEL20_OFFSET + RUNTIME_MODEL20_SIZE
    ] = target_runtime_model
    for arena_offset in source_arena_offsets:
        target[
            arena_offset : arena_offset + RUNTIME_MODEL20_ARENA_SIZE
        ] = target_arena
    result = bytes(target)
    categories = {
        "model20": model_offsets,
        "packet_arenas": packet_offsets,
    }
    if frozenset(_diff_offsets(source_ram, result)) != frozenset(
        model_offsets | packet_offsets
    ):
        raise SurfaceSlotMigrationError("V224 RAM changed outside the render whitelist")
    if result[
        RUNTIME_MODEL20_OFFSET : RUNTIME_MODEL20_OFFSET + RUNTIME_MODEL20_SIZE
    ] != target_runtime_model:
        raise SurfaceSlotMigrationError("Resident V224 model 20 was not installed")
    output_arena_offsets = _packet_arena_offsets(result, expected_hashes=None)
    if output_arena_offsets != source_arena_offsets:
        raise SurfaceSlotMigrationError("Model-20 packet allocation moved")
    output_arenas = tuple(
        result[offset : offset + RUNTIME_MODEL20_ARENA_SIZE]
        for offset in output_arena_offsets
    )
    if (
        any(arena != target_arena for arena in output_arenas)
        or _sha256(b"".join(output_arenas)) != TARGET_PACKET_ARENAS_SHA256
    ):
        raise SurfaceSlotMigrationError("Resident V224 packet arenas were not rebuilt")
    _validate_preserved_state(source_ram, result)
    return result, categories


def migrate_v223_slot1_to_v224(
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
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V223 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V224 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V223 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V224 CUE"),
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
        raise SurfaceSlotMigrationError("V223/V224 media archive-table delta changed")

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
        or _diff_triplets(old_disk_model, new_disk_model) != DISK_MODEL20_DIFF_TRIPLETS
    ):
        raise SurfaceSlotMigrationError("Finished field-621 topology delta changed")
    if (
        len(old_field.parts[5].data) != RESIDENT_SCRIPT_SIZE
        or _sha256(old_field.parts[5].data) != DISK_SCRIPT_SHA256
        or new_field.parts[5].data != old_field.parts[5].data
    ):
        raise SurfaceSlotMigrationError("Field-621 script changed in V224")
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
            expected_counts=OLD_MODEL20_DISK_COUNTS,
            expected_offsets=OLD_MODEL20_OFFSETS,
        )
        != OLD_MODEL20_INVENTORY
        or _model_layout(
            new_disk_model,
            guest_base=0,
            expected_counts=NEW_MODEL20_DISK_COUNTS,
            expected_offsets=NEW_MODEL20_OFFSETS,
        )
        != NEW_MODEL20_INVENTORY
    ):
        raise SurfaceSlotMigrationError("Disc model-20 topology changed")
    old_runtime_model = _runtime_model20(old_disk_model)
    target_runtime_model = _runtime_model20(new_disk_model)
    if (
        _sha256(old_runtime_model) != SOURCE_RUNTIME_MODEL20_SHA256
        or _sha256(target_runtime_model) != TARGET_RUNTIME_MODEL20_SHA256
        or _diff_triplets(old_runtime_model, target_runtime_model)
        != RUNTIME_MODEL20_DIFF_TRIPLETS
        or _model_layout(
            old_runtime_model,
            guest_base=RUNTIME_MODEL20_OFFSET,
            expected_counts=OLD_MODEL20_RUNTIME_COUNTS,
            expected_offsets=OLD_MODEL20_OFFSETS,
        )
        != OLD_MODEL20_INVENTORY
        or _model_layout(
            target_runtime_model,
            guest_base=RUNTIME_MODEL20_OFFSET,
            expected_counts=NEW_MODEL20_RUNTIME_COUNTS,
            expected_offsets=NEW_MODEL20_OFFSETS,
        )
        != NEW_MODEL20_INVENTORY
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

    table_offset = EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
    source_resident_table = source_payload[table_offset : table_offset + ARCHIVE_TABLE_SIZE]
    if (
        len(source_resident_table) != ARCHIVE_TABLE_SIZE
        or source_resident_table[-1] != EXPECTED_VOLATILE_TABLE_VALUE
        or _sha256(source_resident_table) != RESIDENT_ARCHIVE_TABLE_SHA256
        or _diff_triplets(source_resident_table, old_table)
        != RESIDENT_VS_OLD_MEDIA_DIFFS
    ):
        raise SurfaceSlotMigrationError("Pinned resident V223 archive table changed")

    ram_offset, source_ram = _ram_from_payload(source_payload)
    if _sha256(source_ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("Pinned V223 RAM identity changed")
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
        raise SurfaceSlotMigrationError("V224 payload changed outside the render whitelist")
    output_ram_offset, output_ram_check = _ram_from_payload(output_payload_bytes)
    if (
        output_ram_offset != ram_offset
        or output_ram_check != output_ram
        or _sha256(output_ram_check) != OUTPUT_RAM_SHA256
    ):
        raise SurfaceSlotMigrationError("V224 serialized RAM identity changed")
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
        raise SurfaceSlotMigrationError("V224 media prefix reconstruction changed")
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
        raise SurfaceSlotMigrationError("Final V224 state identity or round trip changed")

    report: dict[str, object] = {
        "source_sha256": SOURCE_STATE_SHA256,
        "output_sha256": OUTPUT_STATE_SHA256,
        "source_size": len(state),
        "output_size": len(result),
        "payload_size": len(output_payload_bytes),
        "payload_sha256": OUTPUT_PAYLOAD_SHA256,
        "payload_bytes_changed": len(changed_payload_offsets),
        "model20_bytes_changed": len(categories["model20"]),
        "packet_arena_bytes_changed": len(categories["packet_arenas"]),
        "packet_arena_diff_counts": list(EXPECTED_PACKET_ARENA_DIFF_COUNTS),
        "packet_arena_count": EXPECTED_PACKET_ARENA_COUNT,
        "resident_model20_sha256": TARGET_RUNTIME_MODEL20_SHA256,
        "packet_arena_sha256": TARGET_PACKET_ARENA_SHA256,
        "packet_arenas_sha256": TARGET_PACKET_ARENAS_SHA256,
        "disk_model20_primitive_count": NEW_MODEL20_DISK_COUNTS[1],
        "runtime_model20_primitive_count": NEW_MODEL20_RUNTIME_COUNTS[1],
        "model20_runtime_primitive_overhead": MODEL20_RUNTIME_PRIMITIVE_OVERHEAD,
        "media_archive_table_bytes_changed": len(MEDIA_ARCHIVE_TABLE_DIFFS),
        "resident_archive_table_bytes_changed": 0,
        "resident_archive_table_sha256": RESIDENT_ARCHIVE_TABLE_SHA256,
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "model20_allocation_preserved": True,
        "packet_arena_allocations_preserved": True,
        "packet_arenas_reinitialized_for_topology": True,
        "field_header_scripts_actors_collision_preserved": True,
        "player_camera_gameplay_preserved": True,
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
            / "SLUS-00669_1_v223_persistent_bottom_left_clip_b9624646.sav"
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
            / "SLUS-00669_1_v224_from_b9624646_single_threshold_quad.sav"
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
        result, report = migrate_v223_slot1_to_v224(
            source.read_bytes(),
            old_disc=args.old_disc.resolve(),
            new_disc=args.new_disc.resolve(),
            zstd=zstd,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        if output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Written V224 candidate changed on disk")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote validated V224 candidate: {output}")
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, media_migration.StateMigrationError, SurfaceSlotMigrationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
