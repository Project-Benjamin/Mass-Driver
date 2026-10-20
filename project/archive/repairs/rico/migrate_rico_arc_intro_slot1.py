#!/usr/bin/env python3
"""Migrate the audited Rico Slot 1 to the revised Chapter 1 introduction.

The revised Chapter 1 selection exposition lives only in the Path of Sephirot
hub resource; it is not resident in the captured field-721/main-menu state.
The rebuilt hub remains at the same sector but grows within its existing
22-sector allocation.  This migration therefore changes only the two bytes of
its size in the resident Disc-1 FAT.  All PSX RAM, including Chapter 1's
dialogue, allocator metadata, inventory, and repaired menu overlay, remains
byte-for-byte unchanged.

Only the exact audited state and exact staged Disc 1 are accepted.  The tool
always writes a separate candidate and refuses DuckStation's live Slot 1.
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
    RESIDENT_DIALOGUE_PAYLOAD_OFFSET,
    RESIDENT_DIALOGUE_SIZE,
    SOURCE_MEDIA_PATH,
)
from tools.migrate_rico_arc_eulogy_slot1 import (
    HOUSE_FIELD_CANONICAL_ID,
    HOUSE_FIELD_SECTOR,
    HOUSE_FIELD_SHA256,
    HOUSE_FIELD_SIZE,
    TARGET_ALLOCATED_DIALOGUE_SHA256,
)
from tools.xgdisc import Mode2Image
from tools.xgfield import parse_field
from work.read_duckstation_runtime import RAM_SIZE, _psx_ram_offset


ROOT: Final = Path(__file__).resolve().parents[3]
DEFAULT_ZSTD: Final = ROOT / "work" / "duckstation" / "zstd.dll"
DEFAULT_NEW_DISC: Final = (
    ROOT / "work" / "rico_intro_stage" / "Xenogears_Rico_Arc_Disc_1.bin"
)

SOURCE_STATE_SIZE: Final = 1_366_013
SOURCE_STATE_SHA256: Final = (
    "962e4989dc08e437e62bd9efc2efed31731e64bed115de20f4cdbfe5f56ff0c6"
)
SOURCE_FRAME_OFFSET: Final = 0x6DD0
SOURCE_COMPRESSED_SIZE: Final = 1_337_901
SOURCE_PAYLOAD_SIZE: Final = 3_817_429
SOURCE_PAYLOAD_SHA256: Final = (
    "a375b33afe38dd1a2fabcaa455efd489d6277995395c7e7caaaff81f8cd55a24"
)
SOURCE_RAM_OFFSET: Final = 0x1A62

HUB_FIELD_CANONICAL_ID: Final = 2046
HUB_FIELD_SECTOR: Final = 230_160
HUB_FIELD_SIZE: Final = 43_800
HUB_FIELD_SHA256: Final = (
    "efc0a80534e7b9a893e27af1586c2360c641208baf9f2bc8f612348b95293757"
)
HUB_SCRIPT_SIZE: Final = 6_566
HUB_SCRIPT_SHA256: Final = (
    "b22ad2b97be1f8cf745d43bd69a97a169292105cce727c9c4c319e13c104df5c"
)
HUB_DIALOGUE_SIZE: Final = 2_471
HUB_DIALOGUE_SHA256: Final = (
    "860fcddc6596a2ef9b49262cbaa71fe3ff77d85d194cf19d83a052b2280e5970"
)

TARGET_DISC_SIZE: Final = 719_175_744
TARGET_DISC_SHA256: Final = (
    "f5d8daec0c2d670052c0bbd473783ff13805c7e8a76d79cd80e5daf9ae03cd78"
)
SOURCE_ARCHIVE_TABLE_SHA256: Final = (
    "534f0afd1f7e9d9a9c0d33f96ff0409477a0a0f203470300f71ab9a469f16116"
)
SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "0caff8fc7a75ae16747fb8b8bb250a17bd25fa3fda5b031a212f7c3194041094"
)
SOURCE_VOLATILE_ARCHIVE_BYTE: Final = 0xC4
TARGET_ARCHIVE_TABLE_SHA256: Final = (
    "db423876ee5f975cdf053d10101abfc97030d459914931b38dad40da43821edc"
)
TARGET_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "7cd56307bfbcbd45f316810c253356b68f491a051a67a707bdfdec7a77373eda"
)
ARCHIVE_TABLE_DIFFS: Final = (
    (0x37F5, 0xFC, 0x18),  # FAT 2046 size low:  43,772 -> 43,800
    (0x37F6, 0xAA, 0xAB),  # FAT 2046 size high: 43,772 -> 43,800
)

EXPECTED_REPAIRED_PAYLOAD_SHA256: Final = (
    "3f9ce043263d6cddee81867cfcacf4cbe3b958f297bb1d8c9b772d2bd2992b2b"
)
EXPECTED_REPAIRED_STATE_SIZE: Final = 1_366_013
EXPECTED_REPAIRED_STATE_SHA256: Final = (
    "ddf81b82182f0ce664ffe3d190d2fcc61ff75a065ab8fcd02de21eceed6e40d8"
)


class RicoChapterOneIntroMigrationError(RuntimeError):
    """Raised before output when the pinned FAT-only contract drifts."""


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
        raise RicoChapterOneIntroMigrationError(
            f"Compared payload sizes differ: {len(before)} != {len(after)}"
        )
    return tuple(
        (offset, old, new)
        for offset, (old, new) in enumerate(zip(before, after, strict=True))
        if old != new
    )


def _validated_target_hub(new_disc: Path) -> tuple[bytes, bytes]:
    """Validate final staged media and return its hub dialogue and FAT."""

    if (
        not new_disc.is_file()
        or new_disc.stat().st_size != TARGET_DISC_SIZE
        or _file_sha256(new_disc) != TARGET_DISC_SHA256
    ):
        raise RicoChapterOneIntroMigrationError(
            "Final staged Rico Disc 1 identity changed"
        )
    image = Mode2Image(new_disc)
    entries = image.read_index()
    if max(HUB_FIELD_CANONICAL_ID, HOUSE_FIELD_CANONICAL_ID) >= len(entries):
        raise RicoChapterOneIntroMigrationError(
            "Final staged Disc 1 is missing a required field"
        )

    hub_entry = entries[HUB_FIELD_CANONICAL_ID]
    if (
        hub_entry.kind != "file"
        or hub_entry.sector != HUB_FIELD_SECTOR
        or hub_entry.size != HUB_FIELD_SIZE
    ):
        raise RicoChapterOneIntroMigrationError(
            "Final staged chapter-hub FAT allocation changed"
        )
    hub = image.extract_entry(hub_entry)
    if len(hub) != HUB_FIELD_SIZE or _sha256(hub) != HUB_FIELD_SHA256:
        raise RicoChapterOneIntroMigrationError(
            "Final staged chapter-hub identity changed"
        )
    parsed = parse_field(hub)
    if len(parsed.parts) != 9:
        raise RicoChapterOneIntroMigrationError(
            "Final staged chapter-hub component count changed"
        )
    script = parsed.parts[5].data
    dialogue = parsed.parts[7].data
    if len(script) != HUB_SCRIPT_SIZE or _sha256(script) != HUB_SCRIPT_SHA256:
        raise RicoChapterOneIntroMigrationError(
            "Chapter-hub script changed in an exposition-only build"
        )
    if (
        len(dialogue) != HUB_DIALOGUE_SIZE
        or _sha256(dialogue) != HUB_DIALOGUE_SHA256
    ):
        raise RicoChapterOneIntroMigrationError(
            "Final staged chapter-hub dialogue identity changed"
        )

    # The currently resident house is intentionally unchanged by this build.
    house_entry = entries[HOUSE_FIELD_CANONICAL_ID]
    if (
        house_entry.kind != "file"
        or house_entry.sector != HOUSE_FIELD_SECTOR
        or house_entry.size != HOUSE_FIELD_SIZE
    ):
        raise RicoChapterOneIntroMigrationError(
            "Final staged Chapter 1 house allocation changed"
        )
    house = image.extract_entry(house_entry)
    if len(house) != HOUSE_FIELD_SIZE or _sha256(house) != HOUSE_FIELD_SHA256:
        raise RicoChapterOneIntroMigrationError(
            "Final staged Chapter 1 house changed"
        )

    table = _archive_table(new_disc)
    if (
        len(table) != ARCHIVE_TABLE_SIZE
        or _sha256(table) != TARGET_ARCHIVE_TABLE_SHA256
    ):
        raise RicoChapterOneIntroMigrationError(
            "Final staged Disc-1 archive table identity changed"
        )
    return dialogue, table


def migrate_state(
    state: bytes,
    *,
    zstd: _Zstd,
    new_disc: Path,
) -> tuple[bytes, dict[str, object]]:
    """Return the exact revised-introduction candidate and audit report."""

    state_hash = _sha256(state)
    if len(state) != SOURCE_STATE_SIZE or state_hash != SOURCE_STATE_SHA256:
        raise RicoChapterOneIntroMigrationError(
            "Source Slot 1 identity changed: "
            f"{len(state)} bytes / {state_hash}; expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    if (
        len(state) < DUCKSTATION_STATE_HEADER_SIZE
        or state[:4] != DUCKSTATION_STATE_MAGIC
    ):
        raise RicoChapterOneIntroMigrationError(
            "Source is not a supported DuckStation state"
        )
    if state.count(SOURCE_MEDIA_PATH) != 1:
        raise RicoChapterOneIntroMigrationError(
            "Source state no longer mounts the stable Rico M3U path"
        )
    _hub_dialogue, target_archive_table = _validated_target_hub(
        new_disc.resolve()
    )

    compression_type, compressed_size, payload_size, frame_offset = (
        struct.unpack_from(
            "<IIII",
            state,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
        )
    )
    if compression_type != DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise RicoChapterOneIntroMigrationError(
            "State payload is not Zstandard-compressed"
        )
    if (
        compressed_size != SOURCE_COMPRESSED_SIZE
        or payload_size != SOURCE_PAYLOAD_SIZE
        or frame_offset != SOURCE_FRAME_OFFSET
        or frame_offset + compressed_size != len(state)
    ):
        raise RicoChapterOneIntroMigrationError(
            "Source DuckStation frame layout changed"
        )
    frame = state[frame_offset:]
    if not frame.startswith(ZSTD_MAGIC) or zstd.frame_size(frame) != compressed_size:
        raise RicoChapterOneIntroMigrationError(
            "Source compressed frame identity is invalid"
        )
    source_payload = zstd.decompress(frame)
    if (
        len(source_payload) != SOURCE_PAYLOAD_SIZE
        or _sha256(source_payload) != SOURCE_PAYLOAD_SHA256
    ):
        raise RicoChapterOneIntroMigrationError(
            "Source decompressed payload identity changed"
        )
    ram_offset = _psx_ram_offset(source_payload)
    if ram_offset != SOURCE_RAM_OFFSET or ram_offset + RAM_SIZE > len(source_payload):
        raise RicoChapterOneIntroMigrationError("Source PSX RAM layout changed")

    dialogue_start = RESIDENT_DIALOGUE_PAYLOAD_OFFSET
    dialogue_end = dialogue_start + RESIDENT_DIALOGUE_SIZE
    resident_dialogue = source_payload[dialogue_start:dialogue_end]
    if _sha256(resident_dialogue) != TARGET_ALLOCATED_DIALOGUE_SHA256:
        raise RicoChapterOneIntroMigrationError(
            "Previously migrated resident Chapter 1 dialogue changed"
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
        raise RicoChapterOneIntroMigrationError(
            "Source resident Disc-1 archive table changed"
        )
    normalized_source_table = (
        source_resident_table[:-1] + target_archive_table[-1:]
    )
    if _sha256(normalized_source_table) != SOURCE_ARCHIVE_TABLE_SHA256:
        raise RicoChapterOneIntroMigrationError(
            "Source normalized Disc-1 archive table changed"
        )
    archive_differences = _differences(
        normalized_source_table,
        target_archive_table,
    )
    if archive_differences != ARCHIVE_TABLE_DIFFS:
        raise RicoChapterOneIntroMigrationError(
            "Source/final Disc-1 archive-table delta changed"
        )

    payload = bytearray(source_payload)
    for relative_offset, old, new in ARCHIVE_TABLE_DIFFS:
        offset = table_start + relative_offset
        if payload[offset] != old:
            raise RicoChapterOneIntroMigrationError(
                f"Resident FAT byte changed at payload 0x{offset:X}"
            )
        payload[offset] = new
    repaired_payload = bytes(payload)

    if repaired_payload[dialogue_start:dialogue_end] != resident_dialogue:
        raise RicoChapterOneIntroMigrationError(
            "FAT-only migration changed resident Chapter 1 dialogue"
        )
    target_resident_table = repaired_payload[table_start:table_end]
    if (
        _sha256(target_resident_table)
        != TARGET_RESIDENT_ARCHIVE_TABLE_SHA256
        or target_resident_table[:-1] != target_archive_table[:-1]
        or target_resident_table[-1] != SOURCE_VOLATILE_ARCHIVE_BYTE
    ):
        raise RicoChapterOneIntroMigrationError(
            "Migrated resident Disc-1 archive table is not exact"
        )
    expected_changes = tuple(
        (
            table_start + offset,
            old,
            new,
        )
        for offset, old, new in ARCHIVE_TABLE_DIFFS
    )
    actual_changes = _differences(source_payload, repaired_payload)
    if actual_changes != expected_changes:
        raise RicoChapterOneIntroMigrationError(
            "FAT-only migration changed unexpected payload bytes"
        )
    repaired_payload_hash = _sha256(repaired_payload)
    if repaired_payload_hash != EXPECTED_REPAIRED_PAYLOAD_SHA256:
        raise RicoChapterOneIntroMigrationError(
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
        raise RicoChapterOneIntroMigrationError(
            "Repaired state failed its Zstandard round trip"
        )
    if (
        len(result) != EXPECTED_REPAIRED_STATE_SIZE
        or _sha256(result) != EXPECTED_REPAIRED_STATE_SHA256
    ):
        raise RicoChapterOneIntroMigrationError(
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
        "resident_archive_table_payload_offset": table_start,
        "resident_archive_table_changed_byte_count": len(ARCHIVE_TABLE_DIFFS),
        "hub_field_sector": HUB_FIELD_SECTOR,
        "hub_field_size": HUB_FIELD_SIZE,
        "resident_dialogue_changed_byte_count": 0,
        "gamestate_changed_byte_count": 0,
        "allocator_changed_byte_count": 0,
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
    except RicoChapterOneIntroMigrationError as exc:
        raise SystemExit(str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)
    print(f"Wrote revised-introduction savestate candidate: {output}")
    for key, value in report.items():
        if isinstance(value, int) and "offset" in key:
            value = f"0x{value:X}"
        print(f"{key}: {value}")
    print("The source and DuckStation's live Slot 1 were not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
