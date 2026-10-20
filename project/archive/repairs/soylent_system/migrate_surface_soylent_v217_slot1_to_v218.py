#!/usr/bin/env python3
"""Migrate the exact saved Intake-door view from V217 to V218.

The user's source state is paused in field 621 at examination-room Door A.  Its
resident field still contains V217's shallow black jamb/lintel/sill model, so a
media-path migration alone would retain the reported floating outline until a
room reload.  This migration keeps the state allocation and all gameplay data
fixed and applies V218's same-size rear-plate geometry to the resident raw
model.  The instantiated actor pointers stay byte-identical: clearing them can
leave DuckStation with invalid live renderer references when emulation resumes.

The live Slot 1 is never overwritten by this tool.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
from typing import Sequence


if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import tools.migrate_duckstation_disc_state as media_migration  # noqa: E402
from work.read_duckstation_runtime import (  # noqa: E402
    FIELD_ACTORS,
    FIELD_ACTOR_STRIDE,
    FIELD_NUM_ACTORS,
    RAM_SIZE,
    _psx_ram_offset,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIVE_SLOT1 = (PROJECT_ROOT / "emulator_data" / "SLUS-00669_1.sav").resolve()

SOURCE_STATE_SIZE = 1_604_372
SOURCE_STATE_SHA256 = "e8bcc43145f206185e1eaa6e90a204fdf7ca0219a4a986eadd540fccffdeeb09"
SOURCE_PREFIX_SIZE = 31_594
SOURCE_PREFIX_SHA256 = "62fffce70293f686ec1fde5f8942223349395b1485032ffde3d259eafa91fdad"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "5a489ed4c52e7ee56ea8fde2f1592a4691c4fc2f902dc2f875c144652cce8158"
SOURCE_RAM_SHA256 = "fdb68f49fcd853cda49b668fa80a48b0da92b16269767f5bd377b88a74b6d6dd"
OUTPUT_STATE_SIZE = 1_468_317
OUTPUT_STATE_SHA256 = "ebffa2fb49f4486f6f57feec0ec67935c87ae19f6672091622a67cdc54db777d"
OUTPUT_PAYLOAD_SHA256 = "50d4d551e928bf4b3d5c840d989100e8fa96febc8b7d036031def8f20f44e01b"
EXPECTED_PAYLOAD_BYTES_CHANGED = 42

OLD_DISC_SIZE = NEW_DISC_SIZE = 698_642_784
OLD_DISC_SHA256 = "b672e95c592efe2978cd46a10ee3cde3b86d6af89a1db69a02646fbb0789184a"
NEW_DISC_SHA256 = "1660e1a4ff0a90f416a428428e92fadfb05410cbb17d5be6c0b132ec39bc248a"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v217.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v218.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = "2f921abda6c2b87ed5ab71896e1148965e59f464be0657b42bcbf9107d09d297"
NEW_CUE_SHA256 = "ae8410db00d89f864f42cb0bc880c708f59e36972f8da95da944e7aebfd31524"

EXPECTED_FIELD_ACTOR_COUNT = 63
EXPECTED_FIELD_ACTORS = 0x11B0D4
RUNTIME_MODEL_OFFSET = 0x110A18
RUNTIME_MODEL_SIZE = 396
SOURCE_RUNTIME_MODEL_SHA256 = "d6765513e21dc61b27531ca2e38a33b2022680c3d81c41ff630f160fb96b5835"
OUTPUT_RUNTIME_MODEL_SHA256 = "353fa7bcd71e1f6d898203e33ce70f6c77f5e307d1412049157ed15a8d51604a"

STATIC_BACKER_ENTITIES = (60, 61, 62)
STATIC_BACKER_MODEL_POINTERS = (0x8013B1D4, 0x8013B488, 0x8013B73C)
STATIC_BACKER_RECORD_SHA256S = (
    "9ae74db20c6c1c157e0e307d43a8181de605ebee8642b93eef9c23fd1dbab579",
    "40672c14d561432400e78629cb55a8ccb475b4b8eac10da6592a403a86923498",
    "ea2ce036519f1aec56b49f86583ec4305eb20b045c8d436a7ecdade7e38c67d9",
)
GEOMETRY_BYTE_EDITS = (
    (0x034, 0xF8, 0xE0),
    (0x03C, 0xFE, 0xE0),
    (0x04C, 0xFE, 0xE0),
    (0x050, 0x00, 0x2C),
    (0x054, 0xF8, 0xE0),
    (0x05A, 0x8C, 0xC6),
    (0x05C, 0xFE, 0xE0),
    (0x060, 0x00, 0x2C),
    (0x062, 0x8C, 0xC6),
    (0x064, 0xF8, 0xE0),
    (0x068, 0x59, 0x2C),
    (0x06C, 0xF8, 0xE0),
    (0x074, 0xFE, 0xE0),
    (0x078, 0x59, 0x2C),
    (0x07A, 0x8C, 0xC6),
    (0x07C, 0xF8, 0xE0),
    (0x082, 0x8C, 0xC6),
    (0x084, 0xFE, 0xE0),
    (0x08A, 0x8C, 0xC6),
    (0x08C, 0xF8, 0xE0),
    (0x090, 0x59, 0x2C),
    (0x092, 0x8C, 0xC6),
    (0x094, 0xF8, 0xE0),
    (0x09C, 0xFE, 0xE0),
    (0x0A0, 0x59, 0x2C),
    (0x0A4, 0xFE, 0xE0),
    (0x0A8, 0x59, 0x2C),
    (0x0AA, 0x00, 0xC6),
    (0x0AB, 0x00, 0xFF),
    (0x0AC, 0xF8, 0xE0),
    (0x0B0, 0x00, 0x59),
    (0x0B2, 0x00, 0xC6),
    (0x0B3, 0x00, 0xFF),
    (0x0B4, 0xF8, 0xE0),
    (0x0B8, 0x59, 0x2C),
    (0x0BA, 0x00, 0x8C),
    (0x0BB, 0x00, 0xFF),
    (0x0BC, 0xFE, 0xE0),
    (0x0C0, 0x00, 0x59),
    (0x0C2, 0x00, 0x8C),
    (0x0C3, 0x00, 0xFF),
    (0x0C4, 0xFE, 0xE0),
)


class SurfaceSlotMigrationError(RuntimeError):
    """Raised before output whenever the pinned V217 state contract drifts."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_file(path: Path, size: int, sha256: str, label: str) -> None:
    if not path.is_file():
        raise SurfaceSlotMigrationError(f"{label} does not exist: {path}")
    actual_size = path.stat().st_size
    actual_sha256 = _file_sha256(path)
    if (actual_size, actual_sha256) != (size, sha256):
        raise SurfaceSlotMigrationError(
            f"{label} identity changed: {actual_size} bytes, SHA-256 {actual_sha256}"
        )


def _decode_state(
    state: bytes, zstd: media_migration._Zstd
) -> tuple[bytearray, bytes, int]:
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
    if frame_start + compressed_size != len(state):
        raise SurfaceSlotMigrationError("DuckStation compressed frame span drifted")
    payload = zstd.decompress(state[frame_start:])
    if len(payload) != payload_size:
        raise SurfaceSlotMigrationError("DuckStation payload-size header drifted")
    return bytearray(state[:frame_start]), payload, frame_start


def _encode_state(
    prefix: bytearray, payload: bytes, zstd: media_migration._Zstd
) -> bytes:
    compressed = zstd.compress(payload)
    struct.pack_into(
        "<I",
        prefix,
        media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        len(compressed),
    )
    result = bytes(prefix) + compressed
    if len(result) != len(prefix) + len(compressed):
        raise SurfaceSlotMigrationError("Final DuckStation state span drifted")
    return result


def migrate_v217_slot1_to_v218(
    state: bytes,
    *,
    old_disc: Path,
    new_disc: Path,
    zstd: media_migration._Zstd,
) -> tuple[bytes, dict[str, object]]:
    if (len(state), _sha256(state)) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise SurfaceSlotMigrationError(
            f"Source Slot 1 identity changed: {len(state)} bytes, SHA-256 {_sha256(state)}"
        )
    _validate_file(old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V217 disc")
    _validate_file(new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V218 disc")
    _validate_file(old_disc.with_suffix(".cue"), OLD_CUE_SIZE, OLD_CUE_SHA256, "V217 CUE")
    _validate_file(new_disc.with_suffix(".cue"), NEW_CUE_SIZE, NEW_CUE_SHA256, "V218 CUE")
    if media_migration._archive_table(old_disc) != media_migration._archive_table(new_disc):
        raise SurfaceSlotMigrationError("V217/V218 archive tables unexpectedly differ")

    prefix, payload, frame_start = _decode_state(state, zstd)
    if (
        frame_start != SOURCE_PREFIX_SIZE
        or _sha256(payload) != SOURCE_PAYLOAD_SHA256
        or _sha256(bytes(prefix)) != SOURCE_PREFIX_SHA256
    ):
        raise SurfaceSlotMigrationError("Pinned source state decomposition changed")
    old_name = OLD_CUE_NAME.encode("ascii")
    new_name = NEW_CUE_NAME.encode("ascii")
    if len(old_name) != len(new_name) or bytes(prefix).count(old_name) != 1:
        raise SurfaceSlotMigrationError("Pinned V217 media path changed")
    if new_name in prefix:
        raise SurfaceSlotMigrationError("Source state already names the V218 media")
    prefix = bytearray(bytes(prefix).replace(old_name, new_name))
    if len(prefix) != SOURCE_PREFIX_SIZE:
        raise SurfaceSlotMigrationError("V218 media-path replacement changed prefix size")
    if _sha256(state[:SOURCE_PREFIX_SIZE]) != SOURCE_PREFIX_SHA256:
        raise SurfaceSlotMigrationError("Source state prefix identity changed")
    media_report: dict[str, object] = {
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "resident_archive_table_changed": False,
        "old_table_sha256": _sha256(media_migration._archive_table(old_disc)),
        "new_table_sha256": _sha256(media_migration._archive_table(new_disc)),
    }

    ram_offset = _psx_ram_offset(payload)
    payload = bytearray(payload)
    original_payload = bytes(payload)
    ram = bytearray(payload[ram_offset : ram_offset + RAM_SIZE])
    if len(ram) != RAM_SIZE or _sha256(ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("Pinned V217 RAM identity changed")
    actor_count = struct.unpack_from("<I", ram, FIELD_NUM_ACTORS)[0]
    actor_pointer = struct.unpack_from("<I", ram, FIELD_ACTORS)[0]
    actor_offset = actor_pointer & 0x1FFFFFFF
    if (actor_count, actor_offset) != (
        EXPECTED_FIELD_ACTOR_COUNT,
        EXPECTED_FIELD_ACTORS,
    ):
        raise SurfaceSlotMigrationError("Loaded field-621 actor layout changed")

    runtime_model = bytearray(
        ram[RUNTIME_MODEL_OFFSET : RUNTIME_MODEL_OFFSET + RUNTIME_MODEL_SIZE]
    )
    if _sha256(runtime_model) != SOURCE_RUNTIME_MODEL_SHA256:
        raise SurfaceSlotMigrationError("Resident V217 outline model identity changed")
    for offset, old, new in GEOMETRY_BYTE_EDITS:
        if runtime_model[offset] != old:
            raise SurfaceSlotMigrationError(
                f"Resident outline geometry drifted at model offset 0x{offset:03X}"
            )
        runtime_model[offset] = new
    if _sha256(runtime_model) != OUTPUT_RUNTIME_MODEL_SHA256:
        raise SurfaceSlotMigrationError("Resident V218 rear-plate geometry drifted")
    ram[RUNTIME_MODEL_OFFSET : RUNTIME_MODEL_OFFSET + RUNTIME_MODEL_SIZE] = runtime_model

    for entity, pointer, source_hash in zip(
        STATIC_BACKER_ENTITIES,
        STATIC_BACKER_MODEL_POINTERS,
        STATIC_BACKER_RECORD_SHA256S,
        strict=True,
    ):
        record_offset = actor_offset + entity * FIELD_ACTOR_STRIDE
        record = bytes(ram[record_offset : record_offset + FIELD_ACTOR_STRIDE])
        if _sha256(record) != source_hash or struct.unpack_from("<I", record)[0] != pointer:
            raise SurfaceSlotMigrationError(f"Resident outline actor e{entity} changed")

    payload[ram_offset : ram_offset + RAM_SIZE] = ram
    changed_offsets = tuple(
        index
        for index, (before, after) in enumerate(zip(original_payload, payload, strict=True))
        if before != after
    )
    expected_offsets = {
        *(ram_offset + RUNTIME_MODEL_OFFSET + offset for offset, _old, _new in GEOMETRY_BYTE_EDITS),
    }
    if set(changed_offsets) != expected_offsets:
        raise SurfaceSlotMigrationError("V218 payload changed outside the exact geometry whitelist")

    result = _encode_state(prefix, bytes(payload), zstd)
    check_prefix, check_payload, check_frame_start = _decode_state(result, zstd)
    if (
        check_frame_start != SOURCE_PREFIX_SIZE
        or check_payload != bytes(payload)
        or bytes(check_prefix).count(NEW_CUE_NAME.encode("ascii")) != 1
        or OLD_CUE_NAME.encode("ascii") in check_prefix
    ):
        raise SurfaceSlotMigrationError("Final V218 state failed exact round trip")
    if (
        len(changed_offsets) != EXPECTED_PAYLOAD_BYTES_CHANGED
        or _sha256(bytes(payload)) != OUTPUT_PAYLOAD_SHA256
        or (len(result), _sha256(result)) != (OUTPUT_STATE_SIZE, OUTPUT_STATE_SHA256)
    ):
        raise SurfaceSlotMigrationError("Final V218 candidate identity drifted")
    report: dict[str, object] = {
        "source_sha256": SOURCE_STATE_SHA256,
        "output_sha256": _sha256(result),
        "source_size": len(state),
        "output_size": len(result),
        "payload_size": len(payload),
        "payload_sha256": _sha256(bytes(payload)),
        "payload_bytes_changed": len(changed_offsets),
        "geometry_bytes_changed": len(GEOMETRY_BYTE_EDITS),
        "preserved_resident_entities": list(STATIC_BACKER_ENTITIES),
        "resident_model_sha256": OUTPUT_RUNTIME_MODEL_SHA256,
        "media": media_report,
    }
    return result, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", nargs="?", type=Path, default=LIVE_SLOT1)
    parser.add_argument(
        "--old-disc",
        type=Path,
        default=PROJECT_ROOT / "output" / "Xenogears_PW_CD2_mass_driver_surface_soylent_v217.bin",
    )
    parser.add_argument(
        "--new-disc",
        type=Path,
        default=PROJECT_ROOT / "output" / "Xenogears_PW_CD2_mass_driver_surface_soylent_v218.bin",
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
            / "SLUS-00669_1_v218_from_e8bcc431_outline_fix.sav"
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
            raise SurfaceSlotMigrationError("The migration tool never writes the live Slot 1")
        if output.exists() and not args.force:
            raise SurfaceSlotMigrationError(f"Output already exists: {output}")
        zstd = media_migration._Zstd(args.zstd.resolve())
        result, report = migrate_v217_slot1_to_v218(
            source.read_bytes(),
            old_disc=args.old_disc.resolve(),
            new_disc=args.new_disc.resolve(),
            zstd=zstd,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        if output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Written V218 candidate changed on disk")
        if args.report:
            report_path = args.report.resolve()
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote validated V218 candidate: {output}")
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, media_migration.StateMigrationError, SurfaceSlotMigrationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
