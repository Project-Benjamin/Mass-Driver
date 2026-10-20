#!/usr/bin/env python3
"""Migrate the audited Rico Slot 1 to the no-name Chapter 1 eulogy.

The current state has Chapter 1 field 721 resident behind the open main menu.
That field carries the complete authored Chapter 1 dialogue table, including
the later funeral text.  This guarded migration installs the rebuilt resident
dialogue, clears the nine bytes no longer used by its smaller allocation, and
refreshes the exact two Disc-1 FAT size bytes needed by the rebuilt house and
funeral fields.

No script, pointer, allocator header, menu hook, inventory byte, gameplay
state, or media path moves.  Only the exact audited state and exact staged
Disc 1 are accepted, and the tool refuses to write DuckStation's live Slot 1.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct
import sys
from typing import Final, Sequence

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from tools.migrate_duckstation_disc_state import (
    DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
    DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    DUCKSTATION_STATE_HEADER_SIZE,
    DUCKSTATION_STATE_MAGIC,
    DUCKSTATION_ZSTD_COMPRESSION_TYPE,
    ZSTD_MAGIC,
    _Zstd,
    _archive_table,
)
from tools.migrate_rico_arc_dialogue_slot1 import (
    ARCHIVE_TABLE_PAYLOAD_OFFSET,
    ARCHIVE_TABLE_SIZE,
    LIVE_SLOT_ONE,
    NEXT_ALLOCATOR_HEADER,
    RESIDENT_DIALOGUE_PADDING,
    RESIDENT_DIALOGUE_PAYLOAD_OFFSET,
    RESIDENT_DIALOGUE_SIZE,
    SOURCE_MEDIA_PATH,
)
from tools.xgdisc import Mode2Image
from tools.xgfield import parse_field
from work.read_duckstation_runtime import RAM_SIZE, _psx_ram_offset


ROOT: Final = Path(__file__).resolve().parents[3]
DEFAULT_ZSTD: Final = ROOT / "work" / "duckstation" / "zstd.dll"
DEFAULT_NEW_DISC: Final = (
    ROOT / "work" / "rico_sig_stage" / "Xenogears_Rico_Arc_Disc_1.bin"
)

SOURCE_STATE_SIZE: Final = 1_366_010
SOURCE_STATE_SHA256: Final = (
    "b74ea08c4bdfd235b94dc3be3da4da2ff84a2ecda0fe21dbc9274c41713b2f56"
)
SOURCE_FRAME_OFFSET: Final = 0x6DD0
SOURCE_COMPRESSED_SIZE: Final = 1_337_898
SOURCE_PAYLOAD_SIZE: Final = 3_817_429
SOURCE_PAYLOAD_SHA256: Final = (
    "afa5a6a39c848c414a1fba4985ae97d03c37bb920b2704c3b2107ee6f58af2e3"
)
SOURCE_RAM_OFFSET: Final = 0x1A62

SOURCE_DIALOGUE_SHA256: Final = (
    "e7eb57eb7a996801048a5dd05205038b798120f1a6ade28be5fa81d9f7ba2873"
)
TARGET_DIALOGUE_SIZE: Final = 11_794
TARGET_DIALOGUE_SHA256: Final = (
    "e96b1a4bc2d525150511cce3dd9d01206814da050c7a400400b32f2e5451f0ed"
)
OBSOLETE_DIALOGUE_TAIL_SIZE: Final = RESIDENT_DIALOGUE_SIZE - TARGET_DIALOGUE_SIZE
TARGET_ALLOCATED_DIALOGUE_SHA256: Final = (
    "7e1d2c5084c3a4f850fc9f2790293867149926c4faca398cb370e2e83a322692"
)

HOUSE_FIELD_CANONICAL_ID: Final = 2048
HOUSE_FIELD_SECTOR: Final = 230_237
HOUSE_FIELD_SIZE: Final = 37_708
HOUSE_FIELD_SHA256: Final = (
    "962ef5fe5562265e96750a6d77c530ea192162bebcdbb18b0792685e1e78cef3"
)
HOUSE_SCRIPT_SIZE: Final = 5_426
HOUSE_SCRIPT_SHA256: Final = (
    "85e334efff6a70674d84615fde31be4fd5be8f60bd1eebdb46e7ebc2b9d20386"
)

FUNERAL_FIELD_CANONICAL_ID: Final = 1362
FUNERAL_FIELD_SECTOR: Final = 179_821
FUNERAL_FIELD_SIZE: Final = 134_476
FUNERAL_FIELD_SHA256: Final = (
    "9fbc4231c90d12a7824ec1cb8034aebc893245b35e4f2348be732096fa290ead"
)
FUNERAL_SCRIPT_SIZE: Final = 16_464
FUNERAL_SCRIPT_SHA256: Final = (
    "943d77f9528377dcd97ae94ac89dce39d89016c776557fca2ab012ff531d5faf"
)
FUNERAL_DIALOGUE_SIZE: Final = 1_117
FUNERAL_DIALOGUE_SHA256: Final = (
    "a2fc110366013c76d018578b6c64c51b7275fe18ad5c9cafd6b0392cd89b3fc3"
)

TARGET_DISC_SIZE: Final = 719_175_744
TARGET_DISC_SHA256: Final = (
    "776a254d3a3c832d9e90f9ed4353b3aeea846ad7ada0c6bcfc274ba403c69b42"
)
SOURCE_ARCHIVE_TABLE_SHA256: Final = (
    "e5cd07aef6c4445852af5292a23f07656fc3af7443b29718fba9855fd7b1296f"
)
SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "edbfcc8f1f4eb685165271b515f8bb001d4710474f031c2a201141f6a08c8f83"
)
SOURCE_VOLATILE_ARCHIVE_BYTE: Final = 0xC4
TARGET_ARCHIVE_TABLE_SHA256: Final = (
    "534f0afd1f7e9d9a9c0d33f96ff0409477a0a0f203470300f71ab9a469f16116"
)
TARGET_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "0caff8fc7a75ae16747fb8b8bb250a17bd25fa3fda5b031a212f7c3194041094"
)
ARCHIVE_TABLE_DIFFS: Final = (
    (0x2541, 0x58, 0x4C),  # FAT 1362 size: 134,488 -> 134,476
    (0x3803, 0x60, 0x4C),  # FAT 2048 size:  37,728 ->  37,708
)

EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT: Final = 4_943
EXPECTED_REPAIRED_PAYLOAD_SHA256: Final = (
    "a375b33afe38dd1a2fabcaa455efd489d6277995395c7e7caaaff81f8cd55a24"
)
EXPECTED_REPAIRED_STATE_SIZE: Final = 1_366_013
EXPECTED_REPAIRED_STATE_SHA256: Final = (
    "962e4989dc08e437e62bd9efc2efed31731e64bed115de20f4cdbfe5f56ff0c6"
)


class RicoChapterOneEulogyMigrationError(RuntimeError):
    """Raised before output when the pinned migration contract drifts."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _differences(
    before: bytes,
    after: bytes,
) -> tuple[tuple[int, int, int], ...]:
    if len(before) != len(after):
        raise RicoChapterOneEulogyMigrationError(
            f"Compared payload sizes differ: {len(before)} != {len(after)}"
        )
    return tuple(
        (offset, old, new)
        for offset, (old, new) in enumerate(zip(before, after, strict=True))
        if old != new
    )


def _validated_field(
    image: Mode2Image,
    entries: Sequence[object],
    *,
    canonical_id: int,
    sector: int,
    size: int,
    digest: str,
    script_size: int,
    script_digest: str,
) -> tuple[bytes, bytes]:
    if canonical_id >= len(entries):
        raise RicoChapterOneEulogyMigrationError(
            f"Final staged Disc 1 is missing canonical {canonical_id}"
        )
    entry = entries[canonical_id]
    if (
        getattr(entry, "kind", None) != "file"
        or getattr(entry, "sector", None) != sector
        or getattr(entry, "size", None) != size
    ):
        raise RicoChapterOneEulogyMigrationError(
            f"Final staged canonical-{canonical_id} FAT allocation changed"
        )
    field = image.extract_entry(entry)
    if len(field) != size or _sha256(field) != digest:
        raise RicoChapterOneEulogyMigrationError(
            f"Final staged canonical-{canonical_id} field identity changed"
        )
    parsed = parse_field(field)
    if len(parsed.parts) != 9:
        raise RicoChapterOneEulogyMigrationError(
            f"Final staged canonical-{canonical_id} component count changed"
        )
    script = parsed.parts[5].data
    if len(script) != script_size or _sha256(script) != script_digest:
        raise RicoChapterOneEulogyMigrationError(
            f"Canonical-{canonical_id} script changed in a dialogue-only build"
        )
    return field, parsed.parts[7].data


def _validated_target_resources(
    new_disc: Path,
) -> tuple[bytes, bytes, bytes]:
    """Validate staged media and return house/funeral dialogue plus its FAT."""

    if (
        not new_disc.is_file()
        or new_disc.stat().st_size != TARGET_DISC_SIZE
        or _file_sha256(new_disc) != TARGET_DISC_SHA256
    ):
        raise RicoChapterOneEulogyMigrationError(
            "Final staged Rico Disc 1 identity changed"
        )
    image = Mode2Image(new_disc)
    entries = image.read_index()
    _house, house_dialogue = _validated_field(
        image,
        entries,
        canonical_id=HOUSE_FIELD_CANONICAL_ID,
        sector=HOUSE_FIELD_SECTOR,
        size=HOUSE_FIELD_SIZE,
        digest=HOUSE_FIELD_SHA256,
        script_size=HOUSE_SCRIPT_SIZE,
        script_digest=HOUSE_SCRIPT_SHA256,
    )
    if (
        len(house_dialogue) != TARGET_DIALOGUE_SIZE
        or _sha256(house_dialogue) != TARGET_DIALOGUE_SHA256
    ):
        raise RicoChapterOneEulogyMigrationError(
            "Final staged house dialogue identity changed"
        )
    _funeral, funeral_dialogue = _validated_field(
        image,
        entries,
        canonical_id=FUNERAL_FIELD_CANONICAL_ID,
        sector=FUNERAL_FIELD_SECTOR,
        size=FUNERAL_FIELD_SIZE,
        digest=FUNERAL_FIELD_SHA256,
        script_size=FUNERAL_SCRIPT_SIZE,
        script_digest=FUNERAL_SCRIPT_SHA256,
    )
    if (
        len(funeral_dialogue) != FUNERAL_DIALOGUE_SIZE
        or _sha256(funeral_dialogue) != FUNERAL_DIALOGUE_SHA256
    ):
        raise RicoChapterOneEulogyMigrationError(
            "Final staged funeral dialogue identity changed"
        )

    table = _archive_table(new_disc)
    if (
        len(table) != ARCHIVE_TABLE_SIZE
        or _sha256(table) != TARGET_ARCHIVE_TABLE_SHA256
    ):
        raise RicoChapterOneEulogyMigrationError(
            "Final staged Disc-1 archive table identity changed"
        )
    return house_dialogue, funeral_dialogue, table


def migrate_state(
    state: bytes,
    *,
    zstd: _Zstd,
    new_disc: Path,
) -> tuple[bytes, dict[str, object]]:
    """Return the exact no-name-eulogy candidate and its audit report."""

    state_hash = _sha256(state)
    if len(state) != SOURCE_STATE_SIZE or state_hash != SOURCE_STATE_SHA256:
        raise RicoChapterOneEulogyMigrationError(
            "Source Slot 1 identity changed: "
            f"{len(state)} bytes / {state_hash}; expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    if (
        len(state) < DUCKSTATION_STATE_HEADER_SIZE
        or state[:4] != DUCKSTATION_STATE_MAGIC
    ):
        raise RicoChapterOneEulogyMigrationError(
            "Source is not a supported DuckStation state"
        )
    if state.count(SOURCE_MEDIA_PATH) != 1:
        raise RicoChapterOneEulogyMigrationError(
            "Source state no longer mounts the stable Rico M3U path"
        )

    target_dialogue, _funeral_dialogue, target_archive_table = (
        _validated_target_resources(new_disc.resolve())
    )
    target_allocation = target_dialogue + bytes(OBSOLETE_DIALOGUE_TAIL_SIZE)
    if (
        len(target_allocation) != RESIDENT_DIALOGUE_SIZE
        or _sha256(target_allocation) != TARGET_ALLOCATED_DIALOGUE_SHA256
    ):
        raise RicoChapterOneEulogyMigrationError(
            "Target resident dialogue allocation changed"
        )

    compression_type, compressed_size, payload_size, frame_offset = (
        struct.unpack_from(
            "<IIII",
            state,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
        )
    )
    if compression_type != DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise RicoChapterOneEulogyMigrationError(
            "State payload is not Zstandard-compressed"
        )
    if (
        compressed_size != SOURCE_COMPRESSED_SIZE
        or payload_size != SOURCE_PAYLOAD_SIZE
        or frame_offset != SOURCE_FRAME_OFFSET
        or frame_offset + compressed_size != len(state)
    ):
        raise RicoChapterOneEulogyMigrationError(
            "Source DuckStation frame layout changed"
        )
    frame = state[frame_offset:]
    if not frame.startswith(ZSTD_MAGIC) or zstd.frame_size(frame) != compressed_size:
        raise RicoChapterOneEulogyMigrationError(
            "Source compressed frame identity is invalid"
        )
    source_payload = zstd.decompress(frame)
    if (
        len(source_payload) != SOURCE_PAYLOAD_SIZE
        or _sha256(source_payload) != SOURCE_PAYLOAD_SHA256
    ):
        raise RicoChapterOneEulogyMigrationError(
            "Source decompressed payload identity changed"
        )
    ram_offset = _psx_ram_offset(source_payload)
    if ram_offset != SOURCE_RAM_OFFSET or ram_offset + RAM_SIZE > len(source_payload):
        raise RicoChapterOneEulogyMigrationError("Source PSX RAM layout changed")

    dialogue_start = RESIDENT_DIALOGUE_PAYLOAD_OFFSET
    dialogue_end = dialogue_start + RESIDENT_DIALOGUE_SIZE
    source_dialogue = source_payload[dialogue_start:dialogue_end]
    if _sha256(source_dialogue) != SOURCE_DIALOGUE_SHA256:
        raise RicoChapterOneEulogyMigrationError(
            "Resident Chapter 1 dialogue identity changed"
        )
    padding_end = dialogue_end + len(RESIDENT_DIALOGUE_PADDING)
    header_end = padding_end + len(NEXT_ALLOCATOR_HEADER)
    if (
        source_payload[dialogue_end:padding_end] != RESIDENT_DIALOGUE_PADDING
        or source_payload[padding_end:header_end] != NEXT_ALLOCATOR_HEADER
    ):
        raise RicoChapterOneEulogyMigrationError(
            "Resident dialogue allocation boundary changed"
        )

    table_start = ARCHIVE_TABLE_PAYLOAD_OFFSET
    table_end = table_start + ARCHIVE_TABLE_SIZE
    source_resident_table = source_payload[table_start:table_end]
    if (
        len(source_resident_table) != ARCHIVE_TABLE_SIZE
        or _sha256(source_resident_table)
        != SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256
        or source_resident_table[-1] != SOURCE_VOLATILE_ARCHIVE_BYTE
    ):
        raise RicoChapterOneEulogyMigrationError(
            "Source resident Disc-1 archive table changed"
        )
    normalized_source_table = (
        source_resident_table[:-1] + target_archive_table[-1:]
    )
    if _sha256(normalized_source_table) != SOURCE_ARCHIVE_TABLE_SHA256:
        raise RicoChapterOneEulogyMigrationError(
            "Source normalized Disc-1 archive table changed"
        )
    archive_differences = _differences(
        normalized_source_table,
        target_archive_table,
    )
    if archive_differences != ARCHIVE_TABLE_DIFFS:
        raise RicoChapterOneEulogyMigrationError(
            "Source/final Disc-1 archive-table delta changed"
        )

    payload = bytearray(source_payload)
    payload[dialogue_start:dialogue_end] = target_allocation
    for relative_offset, old, new in ARCHIVE_TABLE_DIFFS:
        offset = table_start + relative_offset
        if payload[offset] != old:
            raise RicoChapterOneEulogyMigrationError(
                f"Resident FAT byte changed at payload 0x{offset:X}"
            )
        payload[offset] = new

    repaired_payload = bytes(payload)
    target_end = dialogue_start + TARGET_DIALOGUE_SIZE
    if repaired_payload[target_end:dialogue_end] != bytes(
        OBSOLETE_DIALOGUE_TAIL_SIZE
    ):
        raise RicoChapterOneEulogyMigrationError(
            "Obsolete resident dialogue tail was not cleared"
        )
    if (
        repaired_payload[dialogue_end:padding_end] != RESIDENT_DIALOGUE_PADDING
        or repaired_payload[padding_end:header_end] != NEXT_ALLOCATOR_HEADER
    ):
        raise RicoChapterOneEulogyMigrationError(
            "Migration changed dialogue padding or its next allocator header"
        )
    target_resident_table = repaired_payload[table_start:table_end]
    if (
        _sha256(target_resident_table)
        != TARGET_RESIDENT_ARCHIVE_TABLE_SHA256
        or target_resident_table[:-1] != target_archive_table[:-1]
        or target_resident_table[-1] != SOURCE_VOLATILE_ARCHIVE_BYTE
    ):
        raise RicoChapterOneEulogyMigrationError(
            "Migrated resident Disc-1 archive table is not exact"
        )

    dialogue_differences = _differences(source_dialogue, target_allocation)
    expected_changes = tuple(
        sorted(
            (
                *(
                    (dialogue_start + offset, old, new)
                    for offset, old, new in dialogue_differences
                ),
                *(
                    (table_start + offset, old, new)
                    for offset, old, new in ARCHIVE_TABLE_DIFFS
                ),
            )
        )
    )
    actual_changes = _differences(source_payload, repaired_payload)
    if (
        len(dialogue_differences) != EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT
        or actual_changes != expected_changes
    ):
        raise RicoChapterOneEulogyMigrationError(
            "Migration changed unexpected decompressed payload bytes"
        )
    repaired_payload_hash = _sha256(repaired_payload)
    if repaired_payload_hash != EXPECTED_REPAIRED_PAYLOAD_SHA256:
        raise RicoChapterOneEulogyMigrationError(
            "Repaired payload identity changed: " + repaired_payload_hash
        )

    compressed = zstd.compress(repaired_payload)
    prefix = bytearray(state[:frame_offset])
    struct.pack_into(
        "<I",
        prefix,
        DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        len(compressed),
    )
    result = bytes(prefix) + compressed
    if zstd.decompress(result[frame_offset:]) != repaired_payload:
        raise RicoChapterOneEulogyMigrationError(
            "Repaired state failed its Zstandard round trip"
        )
    if (
        len(result) != EXPECTED_REPAIRED_STATE_SIZE
        or _sha256(result) != EXPECTED_REPAIRED_STATE_SHA256
    ):
        raise RicoChapterOneEulogyMigrationError(
            "Repaired state identity changed: "
            f"{len(result)} bytes / {_sha256(result)}"
        )

    report: dict[str, object] = {
        "source_state_sha256": state_hash,
        "repaired_state_sha256": _sha256(result),
        "source_state_size": len(state),
        "repaired_state_size": len(result),
        "source_payload_sha256": SOURCE_PAYLOAD_SHA256,
        "repaired_payload_sha256": repaired_payload_hash,
        "dialogue_payload_offset": dialogue_start,
        "source_dialogue_allocation_size": RESIDENT_DIALOGUE_SIZE,
        "target_dialogue_size": TARGET_DIALOGUE_SIZE,
        "obsolete_dialogue_tail_zeroed": OBSOLETE_DIALOGUE_TAIL_SIZE,
        "dialogue_changed_byte_count": len(dialogue_differences),
        "resident_archive_table_payload_offset": table_start,
        "resident_archive_table_changed_byte_count": len(ARCHIVE_TABLE_DIFFS),
        "house_field_size": HOUSE_FIELD_SIZE,
        "funeral_field_size": FUNERAL_FIELD_SIZE,
        "allocator_header_preserved": True,
        "dialogue_allocation_relocated": False,
        "resident_fat_migrated": True,
        "media_path_rewrite_required": False,
    }
    return result, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--zstd", type=Path, default=DEFAULT_ZSTD)
    parser.add_argument("--new-disc", type=Path, default=DEFAULT_NEW_DISC)
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = args.source.resolve()
    output = args.output.resolve()
    zstd_path = args.zstd.resolve()
    new_disc = args.new_disc.resolve()
    if source == output or output == LIVE_SLOT_ONE.resolve():
        raise SystemExit(
            "Output must be separate and may not be DuckStation's live Slot 1"
        )
    for path, label in (
        (source, "source state"),
        (zstd_path, "zstd library"),
        (new_disc, "final staged Rico Disc 1"),
    ):
        if not path.is_file():
            raise SystemExit(f"{label} does not exist: {path}")
    if output.exists() and not args.force:
        raise SystemExit(f"Output already exists (use --force): {output}")

    try:
        result, report = migrate_state(
            source.read_bytes(),
            zstd=_Zstd(zstd_path),
            new_disc=new_disc,
        )
    except RicoChapterOneEulogyMigrationError as exc:
        raise SystemExit(str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)
    print(f"Wrote no-name-eulogy savestate candidate: {output}")
    for key, value in report.items():
        if isinstance(value, int) and "offset" in key:
            value = f"0x{value:X}"
        print(f"{key}: {value}")
    print("The source and DuckStation's live Slot 1 were not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
