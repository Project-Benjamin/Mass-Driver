#!/usr/bin/env python3
"""Migrate the exact rejected V218 Intake-door view to corrected V219.

The user's source state is paused in field 621 at examination-room Door A,
where V218's double-sided opaque rear plate can render as a black wall from an
exterior camera angle.  V219 keeps the same resident model allocation and
changes only sixteen low bytes in its triangle indices, replacing each reverse
primitive with a duplicate of the matching hallway-facing primitive.

The rebuilt field is 28 bytes smaller, so the resident disc archive index also
needs its one exact size byte updated.  The table's volatile final byte is
preserved.  Everything else in the payload--including the field header,
scripts, walkmesh/collision, actor records and ActorData, GameState, and camera
vectors--must remain byte-identical.  The equal-length mounted CUE name is
retargeted in the DuckStation prefix and its compressed-size field is updated
after deterministic recompression.  This tool never overwrites live Slot 1.
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

SOURCE_STATE_SIZE = 1_615_002
SOURCE_STATE_SHA256 = "f2c0841846b81a09f8c7fdf7052a570daaa9a5f2071e356ffe1a70e9e7602644"
SOURCE_COMPRESSED_SIZE = 1_583_473
SOURCE_PREFIX_SIZE = 31_529
SOURCE_PREFIX_SHA256 = "1375351fe041226e236684281626d67eb62f725fea3371248e2346c6c8f7a379"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "9b16dbadfef45f6ae9262ef73622412945579ef7d1c2e31eacfabd9b8718a0ae"
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
SOURCE_RAM_SHA256 = "4586695ca819297724728a05dbf7e9d4137acf0712b444583f2ca6d7989ac258"

OUTPUT_STATE_SIZE = 1_478_919
OUTPUT_STATE_SHA256 = "52d3c05178ea43a8af46e46a6c9b565fcafb25bc93a1b40a86f29e29010b4c3b"
OUTPUT_COMPRESSED_SIZE = 1_447_390
OUTPUT_PREFIX_SHA256 = "7d6977c3d7e16c7e86bd6b5e29cb4e9d5504add42e591a3895d2a7c696005e2b"
OUTPUT_PAYLOAD_SHA256 = "c8e9ade8d032b845cdf6cc5307499b6ac0706b567dc5d8c76bdf4b7931d54361"
OUTPUT_RAM_SHA256 = "039adee7b8f1b339f4dcaeb07977c91a88341878424c9cb28a415aa8a14224b2"

OLD_DISC_SIZE = NEW_DISC_SIZE = 698_642_784
OLD_DISC_SHA256 = "1660e1a4ff0a90f416a428428e92fadfb05410cbb17d5be6c0b132ec39bc248a"
NEW_DISC_SHA256 = "6d00d1c9246aa5b61a23949d4f52b55a7ab87a787244143740980cd1e31d837f"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v218.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v219.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = "ae8410db00d89f864f42cb0bc880c708f59e36972f8da95da944e7aebfd31524"
NEW_CUE_SHA256 = "8403365f8a5010224604956d9b521594be603ae7408b426da4145c378b5aa7d6"

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = "f8a18fbbe9fd1c211d4d3cf4f9cb3fe2d9a7e7384ec2128a5f641fa005f33d9e"
NEW_ARCHIVE_TABLE_SHA256 = "55c8301a640bb118b6705fa553a3d3f7dd80a6edaeb8f80433c56923fc719d15"
ARCHIVE_TABLE_DIFFS = ((0x3268, 0xC8, 0xAC),)
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
EXPECTED_VOLATILE_TABLE_VALUE = 0xE0
SOURCE_RESIDENT_TABLE_SHA256 = "4ea43d37f2b380ea1e9eb519ca702d1c74fc5d3645ca9ff2752d5f403f8532e1"
OUTPUT_RESIDENT_TABLE_SHA256 = "4396cda395cb53af17a1d184c0d23c3411a127359548fed4f0cc55eeae24d649"

EXPECTED_FIELD_ACTOR_COUNT = 63
EXPECTED_FIELD_ACTORS = 0x11B0D4
ACTOR_DATA_SIZE = 0x138
SOURCE_ACTOR_ARRAY_SHA256 = "0facd09ac19c2b1036fec77cbfa11fd79b71691d04194436509a2b1e0b9f3907"
SOURCE_ACTOR_DATA_SHA256 = "221252e9e71c468436ae2006eeaf9f0cd6762433b201153f2d9c3d4550383e05"

RUNTIME_MODEL_OFFSET = 0x110A18
RUNTIME_MODEL_SIZE = 396
SOURCE_RUNTIME_MODEL_SHA256 = "353fa7bcd71e1f6d898203e33ce70f6c77f5e307d1412049157ed15a8d51604a"
OUTPUT_RUNTIME_MODEL_SHA256 = "9e82d1e128b565a267d832b260f6122e488807bd83b51586b6a76504d31eec2b"
GEOMETRY_BYTE_EDITS = (
    (0x0DC, 0x02, 0x00),
    (0x0E0, 0x00, 0x02),
    (0x0E4, 0x02, 0x01),
    (0x0E8, 0x01, 0x02),
    (0x0FC, 0x06, 0x04),
    (0x100, 0x04, 0x06),
    (0x104, 0x06, 0x05),
    (0x108, 0x05, 0x06),
    (0x11C, 0x0A, 0x08),
    (0x120, 0x08, 0x0A),
    (0x124, 0x0A, 0x09),
    (0x128, 0x09, 0x0A),
    (0x13C, 0x0E, 0x0C),
    (0x140, 0x0C, 0x0E),
    (0x144, 0x0E, 0x0D),
    (0x148, 0x0D, 0x0E),
)

# Exact loaded field resources whose contents must remain unchanged.
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
SOURCE_GAMESTATE_SHA256 = "47d6137f08d7b80a0c16126a9b7e0b65bde721c9fb77c126d64948596fd551ce"
SOURCE_CAMERA_SHA256 = "3d8f25e3db4aae40dc803631ddc31a5a469046aa854f392ff100f85f3918aeb2"

EXPECTED_ARCHIVE_BYTES_CHANGED = 1
EXPECTED_GEOMETRY_BYTES_CHANGED = 16
EXPECTED_PAYLOAD_BYTES_CHANGED = 17


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output whenever the pinned V218/V219 contract drifts."""


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
        raise SurfaceSlotMigrationError("Pinned V218 media path changed")
    if new_name in source_prefix:
        raise SurfaceSlotMigrationError("Source state already names the V219 media")
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
        raise SurfaceSlotMigrationError("V219 actor layout was not preserved")

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


def migrate_v218_slot1_to_v219(
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
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V218 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V219 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V218 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V219 CUE"),
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
        raise SurfaceSlotMigrationError("V218/V219 archive-table delta changed")

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
    source_resident_table = source_payload[
        table_offset : table_offset + ARCHIVE_TABLE_SIZE
    ]
    if (
        table_offset != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or volatile_bytes != 1
        or source_resident_table[-1] != EXPECTED_VOLATILE_TABLE_VALUE
        or _sha256(source_resident_table) != SOURCE_RESIDENT_TABLE_SHA256
    ):
        raise SurfaceSlotMigrationError("Pinned resident V218 archive table changed")

    ram_offset, source_ram = _ram_from_payload(source_payload)
    if _sha256(source_ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("Pinned V218 RAM identity changed")
    source_model = source_ram[
        RUNTIME_MODEL_OFFSET : RUNTIME_MODEL_OFFSET + RUNTIME_MODEL_SIZE
    ]
    if _sha256(source_model) != SOURCE_RUNTIME_MODEL_SHA256:
        raise SurfaceSlotMigrationError("Resident V218 double-sided model changed")

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
        raise SurfaceSlotMigrationError("Resident V219 archive table reconstruction changed")

    for relative, old, new in GEOMETRY_BYTE_EDITS:
        offset = ram_offset + RUNTIME_MODEL_OFFSET + relative
        if output_payload[offset] != old:
            raise SurfaceSlotMigrationError(
                f"Resident rear-plate geometry drifted at model offset 0x{relative:03X}"
            )
        output_payload[offset] = new

    output_payload_bytes = bytes(output_payload)
    _output_ram_offset, output_ram = _ram_from_payload(output_payload_bytes)
    output_model = output_ram[
        RUNTIME_MODEL_OFFSET : RUNTIME_MODEL_OFFSET + RUNTIME_MODEL_SIZE
    ]
    if _sha256(output_model) != OUTPUT_RUNTIME_MODEL_SHA256:
        raise SurfaceSlotMigrationError("Resident V219 one-sided model reconstruction changed")
    _validate_preserved_field_state(source_ram, output_ram)

    expected_payload_offsets = {
        *(table_offset + relative for relative, _old, _new in ARCHIVE_TABLE_DIFFS),
        *(
            ram_offset + RUNTIME_MODEL_OFFSET + relative
            for relative, _old, _new in GEOMETRY_BYTE_EDITS
        ),
    }
    changed_offsets = _diff_offsets(source_payload, output_payload_bytes)
    if (
        set(changed_offsets) != expected_payload_offsets
        or len(changed_offsets) != EXPECTED_PAYLOAD_BYTES_CHANGED
        or _sha256(output_payload_bytes) != OUTPUT_PAYLOAD_SHA256
        or _sha256(output_ram) != OUTPUT_RAM_SHA256
    ):
        raise SurfaceSlotMigrationError("V219 payload changed outside the exact byte whitelist")

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
        raise SurfaceSlotMigrationError("Final V219 state identity or round trip changed")

    report: dict[str, object] = {
        "source_sha256": SOURCE_STATE_SHA256,
        "output_sha256": OUTPUT_STATE_SHA256,
        "source_size": len(state),
        "output_size": len(result),
        "payload_size": len(output_payload_bytes),
        "payload_sha256": OUTPUT_PAYLOAD_SHA256,
        "payload_bytes_changed": len(changed_offsets),
        "archive_table_bytes_changed": len(ARCHIVE_TABLE_DIFFS),
        "geometry_bytes_changed": len(GEOMETRY_BYTE_EDITS),
        "resident_archive_table_sha256": OUTPUT_RESIDENT_TABLE_SHA256,
        "resident_model_sha256": OUTPUT_RUNTIME_MODEL_SHA256,
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "actor_header_game_camera_script_collision_preserved": True,
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
            / "SLUS-00669_1_v218_black_wall_f2c08418.sav"
        ),
    )
    parser.add_argument(
        "--old-disc",
        type=Path,
        default=(
            PROJECT_ROOT
            / "output"
            / "Xenogears_PW_CD2_mass_driver_surface_soylent_v218.bin"
        ),
    )
    parser.add_argument(
        "--new-disc",
        type=Path,
        default=(
            PROJECT_ROOT
            / "output"
            / "Xenogears_PW_CD2_mass_driver_surface_soylent_v219.bin"
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
            / "SLUS-00669_1_v219_from_f2c08418_black_wall_fix.sav"
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
        result, report = migrate_v218_slot1_to_v219(
            source.read_bytes(),
            old_disc=args.old_disc.resolve(),
            new_disc=args.new_disc.resolve(),
            zstd=zstd,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        if output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Written V219 candidate changed on disk")
        if args.report:
            report_path = args.report.resolve()
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote validated V219 candidate: {output}")
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, media_migration.StateMigrationError, SurfaceSlotMigrationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
