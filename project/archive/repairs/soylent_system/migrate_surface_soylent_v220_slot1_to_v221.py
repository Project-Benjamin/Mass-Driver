#!/usr/bin/env python3
"""Migrate the exact V220 Intake reference state to V221 safely.

V221 replaces field 621's inert model 20 with the two-quad, textured floor
apron used by the three custom examination-room doors.  The serialized field
already owns a 396-byte resident model slot and two 0x140-byte GPU packet
arenas for each of static nodes e60-e62, so the migration can rebuild those
objects in place without moving an actor, allocation, script, walkmesh, camera,
or player byte.

Changing model topology also changes the packet interpretation.  A raw-model
patch alone would make the renderer consume V220's sixteen POLY_F3 templates
as two POLY_FT4 plus twelve POLY_F3 templates.  This tool therefore recreates
all six fixed-size packet arenas exactly as a fresh field load would.  It
refuses every unpinned source, disc, CUE, archive-table, model, pointer, arena,
or output identity and never writes live DuckStation Slot 1.
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
import tools.migrate_surface_soylent_v219_slot1_to_v220 as v220_migration  # noqa: E402
from tools.xgdeathblows import GAMESTATE_SIZE  # noqa: E402
from tools.xgdisc import DiscFormatError, Mode2Image  # noqa: E402
from tools.xgfield import FieldFormatError, parse_field  # noqa: E402
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

SOURCE_STATE_SIZE = 1_679_306
SOURCE_STATE_SHA256 = "e4aea385a822c19b74040bb442c1766ad122be1a95009a24d9bec51429198c54"
SOURCE_COMPRESSED_SIZE = 1_623_232
SOURCE_PREFIX_SIZE = 56_074
SOURCE_PREFIX_SHA256 = "890082d9fa516f687813dc025952486bef224c04d69d95cecdb1c5d8a137a1c7"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "079d52cfb5d50a3dc0bcb3ee512da99c0d8d9b50c2f541fa1a2e53ef1e73b554"
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
SOURCE_RAM_SHA256 = "917ec65b323ec13bad7a91966cef101174f1ff08a6b6d71df1638bea211f832d"

OUTPUT_STATE_SIZE = 1_521_337
OUTPUT_STATE_SHA256 = "27710b20903e4eb6be1c818b3e3aaf8bf4050c7cc709575a73f5c2fb7f9d3581"
OUTPUT_COMPRESSED_SIZE = 1_465_263
OUTPUT_PREFIX_SHA256 = "462c1f421c4e0ad1ff48a94956baf2a83589c666074343c9f089edb192c7a5c4"
OUTPUT_PAYLOAD_SHA256 = "88525715b23bc3c13c1c39b1e25d9d06cb7772cd02560a9234d0ca722e97a816"
OUTPUT_RAM_SHA256 = "f9f8af4c8481a0d56591de232c3b0f7c094f3fe36454e05a02f89d8fe9367d03"

OLD_DISC_SIZE = NEW_DISC_SIZE = 698_642_784
OLD_DISC_SHA256 = "b4f91cad8d7c819e4908d0e1c8369ff3fe3c432405a39ff4cb8d7bd9e961c63d"
NEW_DISC_SHA256 = "577519db3fb4228c17f0555466866b271c265587a5fdc01515d9ff3f78f6827a"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v220.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v221.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = "4a07ef2954e665340ed6f00912777a1cac162b4d8bb3206c41e5a8e653d85ab7"
NEW_CUE_SHA256 = "a4134fcf3f5bee22530aa90aed6cd691a29983483eb8438828af5caa30ba1163"

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = "7699ef7067eba7fd54a33ab9a6957097328d14b5f55aaa1c789a12fa8fdedca4"
NEW_ARCHIVE_TABLE_SHA256 = "f0a26fa145622264a69cbd25a59213bc1f47920aca22f9d2f00d24fde4342290"
ARCHIVE_TABLE_DIFFS = ((0x3268, 0xE4, 0xE8),)
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
EXPECTED_VOLATILE_TABLE_VALUE = 0xE0
SOURCE_RESIDENT_TABLE_SHA256 = "81d563907cda74748d869ad3a2e2956f6758bf00424a3fd78a2379ac787a64c1"
OUTPUT_RESIDENT_TABLE_SHA256 = "3eacc1ac53db105f07c987a3eeb20cfbbca9df9fefe21a8c7a4c4750e14dfba0"

# Canonical Disc-2 file 1848 is FAT index 1843.  Read model 20 back from both
# finished images so the resident reconstruction is tied to shipped media.
FIELD621_FAT_INDEX = 1843
FIELD621_MODEL_COMPONENT_INDEX = 2
FIELD621_MODEL20_INDEX = 20
OLD_FIELD621_BUNDLE_SIZE = 135_652
OLD_FIELD621_BUNDLE_SHA256 = "aa95c7a60046b3c6cf08456b609af80867b491a4720588f2823b2f70e819d124"
NEW_FIELD621_BUNDLE_SIZE = 135_656
NEW_FIELD621_BUNDLE_SHA256 = "693c507955696d8a3c75b07acb1be7ad13c50ed4791b95a48b558661c279aae4"
FIELD621_MODEL_ARCHIVE_SIZE = 39_292
OLD_FIELD621_MODEL_ARCHIVE_SHA256 = "df7a58c4f4f30cdc3e22c3838065750ab4e6c5f3f79cd4fa973b70d559795996"
NEW_FIELD621_MODEL_ARCHIVE_SHA256 = "9fec53653008970b00bc06b4e151f5c093c08e9e49d2620600600f75042e2d7a"
FIELD621_MODEL_COUNT = 21

RUNTIME_MODEL20_OFFSET = 0x110A18
RUNTIME_MODEL20_GUEST_BLOCK_POINTER = 0x80110A28
RUNTIME_MODEL20_SIZE = 396
RUNTIME_MODEL20_ARENA_SIZE = 0x140
OLD_DISK_MODEL20_SHA256 = "501971ffbbfa09a28c8f3be10f546630cb9ab6cf52b31c3b28882679388cbb39"
NEW_DISK_MODEL20_SHA256 = "0ce78d9edc020706c22ac4b4027149c53ac28be99ef4b71bedb80a25bbf7744f"
SOURCE_RUNTIME_MODEL20_SHA256 = "fa98fafb54e8c85d1f67701bb8c20f62a2838fc5c25a11d572b044415c93aa91"
OUTPUT_RUNTIME_MODEL20_SHA256 = "81b45178684dbd87fcaf71c4cba3f43bccb2932106aa2245fa2048303f0cb8bb"
OLD_MODEL20_DISK_COUNTS = (16, 16, 1)
OLD_MODEL20_RUNTIME_COUNTS = (16, 18, 1)
OLD_MODEL20_OFFSETS = (0x48, 0x48, 0xC8, 0x14C)
OLD_MODEL20_INVENTORY = ((0x04, 0x77, 16),)
NEW_MODEL20_DISK_COUNTS = (15, 14, 2)
NEW_MODEL20_RUNTIME_COUNTS = (15, 16, 2)
MODEL20_RUNTIME_PRIMITIVE_OVERHEAD = 2
NEW_MODEL20_OFFSETS = (0x48, 0x48, 0xC0, 0x138)
NEW_MODEL20_INVENTORY = ((0x0D, 0x77, 2), (0x04, 0x77, 12))
NEW_RUNTIME_MODEL20_WITHOUT_OVERHEAD_SHA256 = (
    "f6ad9e1861e3b400971aad7f9316163119bd8aafe11232937cf1648434876b93"
)
NEW_MODEL20_DISPLAY_BYTES = bytes.fromhex(
    "A8 00 00 C4 00 79 00 C8 "
    "00 00 00 2D 97 89 97 95 A6 89 A6 95 "
    "00 00 00 2D A6 89 A6 95 B6 89 B6 95"
) + bytes.fromhex("00 00 00 20") * 12

# Static nodes e60-e62 share model 20.  Each instance owns a double-buffered
# packet arena whose size remains 0x140 in V221.
MODEL20_INSTANCE_LAYOUT = (
    (60, 0x13B1D4, (0x13B200, 0x13B340)),
    (61, 0x13B488, (0x13B4B4, 0x13B5F4)),
    (62, 0x13B73C, (0x13B768, 0x13B8A8)),
)
SOURCE_PACKET_ARENA_SHA256 = (
    "7293f55f613cf67ce8d9a4aff9a0fcbb2af9ca6ccec642f7e2f3859529f18809",
    "ef3da6634cb76c48520a0a3f182f9d100f449893cd092cc432882bd3ad3259e6",
    "ae0b593e2fe94c81c529749fc39866e2a4ac4c7ca03359948f5c7856c3dda2c1",
    "933fc7f31c40aa6cbdca7185b1f35697e255220980895421f98a1054de26a219",
    "c703a825e5741c17a6507d17d96560a2e57fa5ecc40a079f4f284e9e4ba320c9",
    "c94a6e3ebb6afc272cf239ac5a62237ed6ab47acde8857bd6faeedd8566b9095",
)
SOURCE_PACKET_ARENAS_SHA256 = "0b2a1de8b223d960da14a7873602b3b0145cdf7e8cd8a8183aa94447d8e2ea35"
TARGET_PACKET_ARENA_SHA256 = "dfa8e31262d760c4ccca0669d42bc7e302c7bb06ea470b9b8bd158f72dcda298"
TARGET_PACKET_ARENAS_SHA256 = "8225f199051718510efad5f75e8a69ecc58a8a283f043eafa16b2c3235553d7e"

# Model 2 is already V220's final camera-safe version and is immutable here.
RUNTIME_MODEL2_OFFSET = v220_migration.RUNTIME_MODEL2_OFFSET
RUNTIME_MODEL2_SIZE = v220_migration.RUNTIME_MODEL2_SIZE
RUNTIME_MODEL2_SHA256 = v220_migration.OUTPUT_RUNTIME_MODEL2_SHA256

EXPECTED_FIELD_ACTOR_COUNT = 63
EXPECTED_FIELD_ACTORS = 0x11B0D4
ACTOR_DATA_SIZE = 0x138
SOURCE_ACTOR_ARRAY_SHA256 = "a74b3977801d58976b596c0b966d9c8edb958813af643bbe303d1232d302f37f"
SOURCE_ACTOR_DATA_SHA256 = "c4e53e2063213b18b8222383239abff397c49b8ec1a9bcec01ce798a9a07acfb"
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
SOURCE_GAMESTATE_SHA256 = "b7d95bfc1c03b11793a49c12410e028549a570f0cf8a4ef46415e61ac878d5b1"
SOURCE_CAMERA_SHA256 = "7e5575ebac9b9571b04a93382e48cd47088649cab7f2ff70ced72de9506b0548"

EXPECTED_MODEL20_BYTES_CHANGED = 113
EXPECTED_PACKET_ARENA_BYTES_CHANGED = 911
EXPECTED_RESIDENT_RENDER_BYTES_CHANGED = 1_024
EXPECTED_ARCHIVE_BYTES_CHANGED = 1
EXPECTED_PAYLOAD_BYTES_CHANGED = 1_025


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output whenever the pinned V220/V221 contract drifts."""


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
        return v220_migration._unpack_state(state, zstd)
    except v220_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc


def _pack_state(prefix: bytes, payload: bytes, zstd: _ZstdLike) -> bytes:
    try:
        return v220_migration._pack_state(prefix, payload, zstd)
    except v220_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc


def _ram_from_payload(payload: bytes) -> tuple[int, bytes]:
    try:
        offset, ram = v220_migration._ram_from_payload(payload)
    except v220_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc
    if offset != EXPECTED_RAM_PAYLOAD_OFFSET:
        raise SurfaceSlotMigrationError("Serialized PSX RAM payload offset drifted")
    return offset, ram


def _expected_prefix(source_prefix: bytes, *, compressed_size: int) -> bytes:
    old_name = OLD_CUE_NAME.encode("ascii")
    new_name = NEW_CUE_NAME.encode("ascii")
    if len(old_name) != len(new_name) or source_prefix.count(old_name) != 1:
        raise SurfaceSlotMigrationError("Pinned V220 media path changed")
    if new_name in source_prefix:
        raise SurfaceSlotMigrationError("Source state already names the V221 media")
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


def _disc_model20(
    disc: Path,
    *,
    bundle_identity: tuple[int, str],
    archive_sha256: str,
    model_sha256: str,
) -> bytes:
    try:
        image = Mode2Image(disc)
        entries = image.read_index()
        if FIELD621_FAT_INDEX >= len(entries):
            raise SurfaceSlotMigrationError("Field-621 FAT index is absent")
        entry = entries[FIELD621_FAT_INDEX]
        if entry.canonical_disc2_index != 1848:
            raise SurfaceSlotMigrationError("Field-621 canonical file mapping drifted")
        bundle = image.extract_entry(entry)
        if (len(bundle), _sha256(bundle)) != bundle_identity:
            raise SurfaceSlotMigrationError("Field-621 disc bundle identity changed")
        parsed = parse_field(bundle)
        models = parsed.parts[FIELD621_MODEL_COMPONENT_INDEX].data
    except (DiscFormatError, FieldFormatError) as exc:
        raise SurfaceSlotMigrationError(f"Cannot decode field 621 from disc: {exc}") from exc
    if (len(models), _sha256(models)) != (FIELD621_MODEL_ARCHIVE_SIZE, archive_sha256):
        raise SurfaceSlotMigrationError("Field-621 model archive identity changed")
    model_entries = _indexed_entries(models)
    if len(model_entries) != FIELD621_MODEL_COUNT:
        raise SurfaceSlotMigrationError("Field-621 model count changed")
    model = model_entries[FIELD621_MODEL20_INDEX]
    if (len(model), _sha256(model)) != (RUNTIME_MODEL20_SIZE, model_sha256):
        raise SurfaceSlotMigrationError("Field-621 disc model 20 identity changed")
    return model


def _model_layout(
    model: bytes,
    *,
    guest_base: int,
    expected_counts: tuple[int, int, int],
    expected_offsets: tuple[int, int, int, int],
) -> tuple[tuple[int, int, int], ...]:
    try:
        return v220_migration._model_layout(
            model,
            guest_base=guest_base,
            expected_size=RUNTIME_MODEL20_SIZE,
            expected_counts=expected_counts,
            expected_offsets=expected_offsets,
        )
    except v220_migration.SurfaceSlotMigrationError as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc


def _runtime_model20(disk_model: bytes) -> bytes:
    """Apply the field loader's pinned in-place model relocation."""

    if len(disk_model) != RUNTIME_MODEL20_SIZE or struct.unpack_from("<I", disk_model)[0] != 1:
        raise SurfaceSlotMigrationError("Disc model 20 container changed")
    result = bytearray(disk_model)
    if struct.unpack_from("<I", result, 4)[0] != 0:
        raise SurfaceSlotMigrationError("Disc model 20 is unexpectedly pre-relocated")
    struct.pack_into("<I", result, 4, 1)

    # Preserve model 20's exact loader accounting.  The finished V220 disc has
    # 16 mesh primitives while this untouched loaded slot has 18; relocating
    # that disc model and applying this +2 is byte-for-byte identical to the
    # source resident model.  V221 likewise carries 14 mesh primitives and
    # therefore requires a runtime total of 16.  Omitting this one u16 edit
    # produces the independently audited-but-wrong f6ad9e... reconstruction.
    primitive_count = struct.unpack_from("<H", result, 0x14)[0]
    struct.pack_into(
        "<H",
        result,
        0x14,
        primitive_count + MODEL20_RUNTIME_PRIMITIVE_OVERHEAD,
    )
    for pointer_offset in (0x18, 0x1C, 0x20, 0x24):
        relative = struct.unpack_from("<I", result, pointer_offset)[0]
        if relative >= len(result):
            raise SurfaceSlotMigrationError("Disc model 20 pointer leaves its allocation")
        struct.pack_into(
            "<I",
            result,
            pointer_offset,
            0x80000000 | (RUNTIME_MODEL20_OFFSET + relative),
        )
    return bytes(result)


def _fresh_packet_arena(runtime_model: bytes) -> bytes:
    display_offset = (
        struct.unpack_from("<I", runtime_model, 0x24)[0] & 0x1FFFFFFF
    ) - RUNTIME_MODEL20_OFFSET
    display = runtime_model[display_offset : display_offset + len(NEW_MODEL20_DISPLAY_BYTES)]
    if display != NEW_MODEL20_DISPLAY_BYTES:
        raise SurfaceSlotMigrationError("V221 model 20 display list changed")
    if struct.unpack_from("<I", runtime_model, 0x44)[0] != RUNTIME_MODEL20_ARENA_SIZE:
        raise SurfaceSlotMigrationError("V221 model 20 packet allocation changed")

    state = display[:8]
    if state != bytes.fromhex("A8 00 00 C4 00 79 00 C8"):
        raise SurfaceSlotMigrationError("V221 apron texture state changed")
    tpage = 0x00A8
    clut = 0x7900

    def ft4(record: bytes) -> bytes:
        if len(record) != 12 or record[:4] != bytes.fromhex("00 00 00 2D"):
            raise SurfaceSlotMigrationError("V221 apron POLY_FT4 record changed")
        packet = bytearray(0x28)
        packet[3] = 9
        packet[4:8] = record[:4]
        packet[12:14] = record[4:6]
        struct.pack_into("<H", packet, 14, clut)
        packet[20:22] = record[6:8]
        struct.pack_into("<H", packet, 22, tpage)
        packet[28:30] = record[8:10]
        packet[36:38] = record[10:12]
        return bytes(packet)

    def f3(record: bytes) -> bytes:
        if record != bytes.fromhex("00 00 00 20"):
            raise SurfaceSlotMigrationError("V221 inert POLY_F3 record changed")
        packet = bytearray(0x14)
        packet[3] = 4
        packet[4:8] = record
        return bytes(packet)

    cursor = 8
    packets = bytearray()
    for _ in range(2):
        packets.extend(ft4(display[cursor : cursor + 12]))
        cursor += 12
    for _ in range(12):
        packets.extend(f3(display[cursor : cursor + 4]))
        cursor += 4
    arena = bytes(packets)
    if (
        cursor != len(display)
        or len(arena) != RUNTIME_MODEL20_ARENA_SIZE
        or _sha256(arena) != TARGET_PACKET_ARENA_SHA256
    ):
        raise SurfaceSlotMigrationError("V221 packet-arena reconstruction changed")
    return arena


def _packet_arena_offsets(ram: bytes, *, require_source_hashes: bool) -> tuple[int, ...]:
    offsets: list[int] = []
    for entity, instance, expected_buffers in MODEL20_INSTANCE_LAYOUT:
        if not 0 <= instance <= RAM_SIZE - 0x10:
            raise SurfaceSlotMigrationError(f"e{entity} model instance leaves PSX RAM")
        model_pointer, buffer0, buffer1 = struct.unpack_from("<III", ram, instance + 4)
        actual_buffers = (buffer0 & 0x1FFFFFFF, buffer1 & 0x1FFFFFFF)
        if model_pointer != RUNTIME_MODEL20_GUEST_BLOCK_POINTER:
            raise SurfaceSlotMigrationError(f"e{entity} no longer references model 20")
        if actual_buffers != expected_buffers:
            raise SurfaceSlotMigrationError(f"e{entity} packet-arena pointers changed")
        offsets.extend(actual_buffers)
    if len(set(offsets)) != 6 or any(
        offset < 0 or offset + RUNTIME_MODEL20_ARENA_SIZE > RAM_SIZE
        for offset in offsets
    ):
        raise SurfaceSlotMigrationError("Model-20 packet arenas overlap or leave PSX RAM")
    ordered = sorted(offsets)
    if any(
        left + RUNTIME_MODEL20_ARENA_SIZE > right
        for left, right in zip(ordered, ordered[1:])
    ):
        raise SurfaceSlotMigrationError("Model-20 packet arenas overlap")
    if require_source_hashes:
        arenas = tuple(
            ram[offset : offset + RUNTIME_MODEL20_ARENA_SIZE] for offset in offsets
        )
        if tuple(_sha256(arena) for arena in arenas) != SOURCE_PACKET_ARENA_SHA256:
            raise SurfaceSlotMigrationError("Pinned V220 packet-arena identity changed")
        if _sha256(b"".join(arenas)) != SOURCE_PACKET_ARENAS_SHA256:
            raise SurfaceSlotMigrationError("Pinned V220 packet-arena set changed")
    return tuple(offsets)


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


def _camera_snapshot(ram: bytes) -> bytes:
    return b"".join(ram[address : address + 16] for address in CAMERA_VECTORS.values())


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
        raise SurfaceSlotMigrationError("V221 actor layout was not preserved")
    actor_array_size = actor_count * FIELD_ACTOR_STRIDE
    source_actors = source_ram[actor_base : actor_base + actor_array_size]
    source_actor_data = _actor_data_snapshot(source_ram, actor_base, actor_count)
    if (
        _sha256(source_actors) != SOURCE_ACTOR_ARRAY_SHA256
        or _sha256(source_actor_data) != SOURCE_ACTOR_DATA_SHA256
    ):
        raise SurfaceSlotMigrationError("Pinned actor or collision state changed")
    if (
        output_ram[actor_base : actor_base + actor_array_size] != source_actors
        or _actor_data_snapshot(output_ram, actor_base, actor_count) != source_actor_data
    ):
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
        if _sha256(source) != expected_hash:
            raise SurfaceSlotMigrationError(f"Pinned {label} identity changed")
        if output_ram[offset : offset + size] != source:
            raise SurfaceSlotMigrationError(f"{label} was not preserved")
    source_camera = _camera_snapshot(source_ram)
    if _sha256(source_camera) != SOURCE_CAMERA_SHA256:
        raise SurfaceSlotMigrationError("Pinned camera identity changed")
    if _camera_snapshot(output_ram) != source_camera:
        raise SurfaceSlotMigrationError("Camera state was not preserved")

    source_model2 = source_ram[
        RUNTIME_MODEL2_OFFSET : RUNTIME_MODEL2_OFFSET + RUNTIME_MODEL2_SIZE
    ]
    output_model2 = output_ram[
        RUNTIME_MODEL2_OFFSET : RUNTIME_MODEL2_OFFSET + RUNTIME_MODEL2_SIZE
    ]
    if _sha256(source_model2) != RUNTIME_MODEL2_SHA256 or output_model2 != source_model2:
        raise SurfaceSlotMigrationError("Resident model 2 was not preserved")


def migrate_v220_slot1_to_v221(
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
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V220 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V221 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V220 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V221 CUE"),
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
        raise SurfaceSlotMigrationError("V220/V221 archive-table delta changed")

    old_disk_model = _disc_model20(
        old_disc,
        bundle_identity=(OLD_FIELD621_BUNDLE_SIZE, OLD_FIELD621_BUNDLE_SHA256),
        archive_sha256=OLD_FIELD621_MODEL_ARCHIVE_SHA256,
        model_sha256=OLD_DISK_MODEL20_SHA256,
    )
    new_disk_model = _disc_model20(
        new_disc,
        bundle_identity=(NEW_FIELD621_BUNDLE_SIZE, NEW_FIELD621_BUNDLE_SHA256),
        archive_sha256=NEW_FIELD621_MODEL_ARCHIVE_SHA256,
        model_sha256=NEW_DISK_MODEL20_SHA256,
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
        raise SurfaceSlotMigrationError("Disc model-20 inventory changed")

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
        raise SurfaceSlotMigrationError("Pinned resident V220 archive table changed")

    ram_offset, source_ram = _ram_from_payload(source_payload)
    if _sha256(source_ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("Pinned V220 RAM identity changed")
    source_model = source_ram[
        RUNTIME_MODEL20_OFFSET : RUNTIME_MODEL20_OFFSET + RUNTIME_MODEL20_SIZE
    ]
    if (
        _sha256(source_model) != SOURCE_RUNTIME_MODEL20_SHA256
        or _runtime_model20(old_disk_model) != source_model
        or _model_layout(
            source_model,
            guest_base=RUNTIME_MODEL20_OFFSET,
            expected_counts=OLD_MODEL20_RUNTIME_COUNTS,
            expected_offsets=OLD_MODEL20_OFFSETS,
        )
        != OLD_MODEL20_INVENTORY
    ):
        raise SurfaceSlotMigrationError("Pinned resident V220 model 20 changed")
    source_arena_offsets = _packet_arena_offsets(source_ram, require_source_hashes=True)

    target_model = _runtime_model20(new_disk_model)
    if (
        _sha256(target_model) != OUTPUT_RUNTIME_MODEL20_SHA256
        or _model_layout(
            target_model,
            guest_base=RUNTIME_MODEL20_OFFSET,
            expected_counts=NEW_MODEL20_RUNTIME_COUNTS,
            expected_offsets=NEW_MODEL20_OFFSETS,
        )
        != NEW_MODEL20_INVENTORY
    ):
        raise SurfaceSlotMigrationError("Resident V221 model-20 reconstruction changed")
    target_arena = _fresh_packet_arena(target_model)

    expected_model_offsets = {
        ram_offset + RUNTIME_MODEL20_OFFSET + relative
        for relative in _diff_offsets(source_model, target_model)
    }
    expected_arena_offsets = {
        ram_offset + arena_offset + relative
        for arena_offset in source_arena_offsets
        for relative in _diff_offsets(
            source_ram[
                arena_offset : arena_offset + RUNTIME_MODEL20_ARENA_SIZE
            ],
            target_arena,
        )
    }
    if (
        len(expected_model_offsets) != EXPECTED_MODEL20_BYTES_CHANGED
        or len(expected_arena_offsets) != EXPECTED_PACKET_ARENA_BYTES_CHANGED
        or len(expected_model_offsets | expected_arena_offsets)
        != EXPECTED_RESIDENT_RENDER_BYTES_CHANGED
    ):
        raise SurfaceSlotMigrationError("Pinned resident render byte counts changed")

    output_payload = bytearray(source_payload)
    for relative, old, new in ARCHIVE_TABLE_DIFFS:
        offset = table_offset + relative
        if output_payload[offset] != old:
            raise SurfaceSlotMigrationError(
                f"Resident archive table drifted at relative offset 0x{relative:04X}"
            )
        output_payload[offset] = new
    output_payload[
        ram_offset + RUNTIME_MODEL20_OFFSET :
        ram_offset + RUNTIME_MODEL20_OFFSET + RUNTIME_MODEL20_SIZE
    ] = target_model
    for arena_offset in source_arena_offsets:
        absolute = ram_offset + arena_offset
        output_payload[absolute : absolute + RUNTIME_MODEL20_ARENA_SIZE] = target_arena

    output_payload_bytes = bytes(output_payload)
    if (
        output_payload_bytes[table_offset : table_offset + ARCHIVE_TABLE_SIZE - 1]
        != new_table[:-1]
        or output_payload_bytes[table_offset + ARCHIVE_TABLE_SIZE - 1]
        != EXPECTED_VOLATILE_TABLE_VALUE
        or _sha256(
            output_payload_bytes[table_offset : table_offset + ARCHIVE_TABLE_SIZE]
        )
        != OUTPUT_RESIDENT_TABLE_SHA256
    ):
        raise SurfaceSlotMigrationError("Resident V221 archive table reconstruction changed")

    output_ram_offset, output_ram = _ram_from_payload(output_payload_bytes)
    if output_ram_offset != ram_offset:
        raise SurfaceSlotMigrationError("Serialized PSX RAM moved")
    output_model = output_ram[
        RUNTIME_MODEL20_OFFSET : RUNTIME_MODEL20_OFFSET + RUNTIME_MODEL20_SIZE
    ]
    if output_model != target_model:
        raise SurfaceSlotMigrationError("Resident V221 model 20 was not installed")
    output_arena_offsets = _packet_arena_offsets(output_ram, require_source_hashes=False)
    if output_arena_offsets != source_arena_offsets:
        raise SurfaceSlotMigrationError("Model-20 packet allocation moved")
    output_arenas = tuple(
        output_ram[offset : offset + RUNTIME_MODEL20_ARENA_SIZE]
        for offset in output_arena_offsets
    )
    if (
        any(arena != target_arena for arena in output_arenas)
        or _sha256(b"".join(output_arenas)) != TARGET_PACKET_ARENAS_SHA256
    ):
        raise SurfaceSlotMigrationError("Resident V221 packet arenas were not rebuilt")
    _validate_preserved_state(source_ram, output_ram)

    expected_payload_offsets = {
        *(table_offset + relative for relative, _old, _new in ARCHIVE_TABLE_DIFFS),
        *expected_model_offsets,
        *expected_arena_offsets,
    }
    changed_offsets = _diff_offsets(source_payload, output_payload_bytes)
    if (
        set(changed_offsets) != expected_payload_offsets
        or len(changed_offsets) != EXPECTED_PAYLOAD_BYTES_CHANGED
        or _sha256(output_payload_bytes) != OUTPUT_PAYLOAD_SHA256
        or _sha256(output_ram) != OUTPUT_RAM_SHA256
    ):
        raise SurfaceSlotMigrationError("V221 payload changed outside the exact byte whitelist")

    provisional_prefix = _expected_prefix(source_prefix, compressed_size=OUTPUT_COMPRESSED_SIZE)
    result = _pack_state(provisional_prefix, output_payload_bytes, zstd)
    output_payload_check, output_frame_start, output_prefix = _unpack_state(result, zstd)
    if (
        output_frame_start != SOURCE_PREFIX_SIZE
        or len(result) - output_frame_start != OUTPUT_COMPRESSED_SIZE
        or output_payload_check != output_payload_bytes
        or output_prefix != _expected_prefix(
            source_prefix, compressed_size=OUTPUT_COMPRESSED_SIZE
        )
        or _sha256(output_prefix) != OUTPUT_PREFIX_SHA256
        or (len(result), _sha256(result)) != (OUTPUT_STATE_SIZE, OUTPUT_STATE_SHA256)
    ):
        raise SurfaceSlotMigrationError("Final V221 state identity or round trip changed")

    report: dict[str, object] = {
        "source_sha256": SOURCE_STATE_SHA256,
        "output_sha256": OUTPUT_STATE_SHA256,
        "source_size": len(state),
        "output_size": len(result),
        "payload_size": len(output_payload_bytes),
        "payload_sha256": OUTPUT_PAYLOAD_SHA256,
        "payload_bytes_changed": len(changed_offsets),
        "archive_table_bytes_changed": len(ARCHIVE_TABLE_DIFFS),
        "model20_bytes_changed": len(expected_model_offsets),
        "packet_arena_bytes_changed": len(expected_arena_offsets),
        "resident_render_bytes_changed": len(expected_model_offsets | expected_arena_offsets),
        "packet_arena_count": len(output_arena_offsets),
        "resident_archive_table_sha256": OUTPUT_RESIDENT_TABLE_SHA256,
        "resident_model2_sha256": RUNTIME_MODEL2_SHA256,
        "resident_model20_sha256": OUTPUT_RUNTIME_MODEL20_SHA256,
        "disk_model20_primitive_count": NEW_MODEL20_DISK_COUNTS[1],
        "runtime_model20_primitive_count": NEW_MODEL20_RUNTIME_COUNTS[1],
        "model20_runtime_primitive_overhead": MODEL20_RUNTIME_PRIMITIVE_OVERHEAD,
        "packet_arena_sha256": TARGET_PACKET_ARENA_SHA256,
        "packet_arenas_sha256": TARGET_PACKET_ARENAS_SHA256,
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "actor_header_game_camera_script_collision_preserved": True,
        "model2_preserved": True,
        "model20_allocation_preserved": True,
        "packet_arena_allocations_preserved": True,
        "packet_arenas_reinitialized_for_topology": True,
        "volatile_archive_table_byte_preserved": True,
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
            / "SLUS-00669_1_v220_original_door_path_reference_e4aea385.sav"
        ),
    )
    parser.add_argument(
        "--old-disc",
        type=Path,
        default=(
            PROJECT_ROOT
            / "output"
            / "Xenogears_PW_CD2_mass_driver_surface_soylent_v220.bin"
        ),
    )
    parser.add_argument(
        "--new-disc",
        type=Path,
        default=(
            PROJECT_ROOT
            / "output"
            / "Xenogears_PW_CD2_mass_driver_surface_soylent_v221.bin"
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
            / "SLUS-00669_1_v221_from_e4aea385_native_threshold_aprons.sav"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "save_candidates"
            / "SLUS-00669_1_v221_from_e4aea385_native_threshold_aprons.json"
        ),
    )
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        source = args.state.resolve()
        output = args.output.resolve()
        report_path = args.report.resolve() if args.report else None
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
        if report_path is not None and report_path.exists() and not args.force:
            raise SurfaceSlotMigrationError(f"Report already exists: {report_path}")
        zstd = media_migration._Zstd(args.zstd.resolve())
        result, report = migrate_v220_slot1_to_v221(
            source.read_bytes(),
            old_disc=args.old_disc.resolve(),
            new_disc=args.new_disc.resolve(),
            zstd=zstd,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        if output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Written V221 candidate changed on disk")
        if report_path is not None:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote validated V221 candidate: {output}")
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, media_migration.StateMigrationError, SurfaceSlotMigrationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
