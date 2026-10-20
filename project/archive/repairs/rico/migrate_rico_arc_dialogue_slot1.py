#!/usr/bin/env python3
"""Migrate the audited Rico Chapter 1 Slot 1 to the revised Anne dialogue.

The installed Slot 1 keeps field 721's dialogue component resident while the
main menu is open.  Merely mounting the rebuilt disc would therefore leave the
old bedside exchange active until a full field reload.  This guarded migration
replaces that one resident component in place and refreshes the one changed
Disc-1 FAT size byte.  The replacement dialogue has the exact same allocation
length as the source, so no allocator header, pointer, script, or neighboring
field component moves.

The tool accepts only the exact audited state and exact staged Disc 1.  It
always writes a separate candidate and refuses DuckStation's live Slot 1 path.
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
from tools.xgdisc import Mode2Image
from tools.xgfield import parse_field
from work.read_duckstation_runtime import RAM_SIZE, _psx_ram_offset


ROOT: Final = Path(__file__).resolve().parents[3]
LIVE_SLOT_ONE: Final = ROOT / "emulator_data" / "SLUS-00664_1.sav"
DEFAULT_ZSTD: Final = ROOT / "work" / "duckstation" / "zstd.dll"
DEFAULT_NEW_DISC: Final = (
    ROOT
    / "work"
    / "rico_arc_dialogue_stage"
    / "Xenogears_Rico_Arc_Disc_1.bin"
)

SOURCE_STATE_SIZE: Final = 1_366_014
SOURCE_STATE_SHA256: Final = (
    "34382f875ebe8522283ef4611a8e56f06e6413986b42f660f653479b831dd40e"
)
SOURCE_FRAME_OFFSET: Final = 0x6DD0
SOURCE_COMPRESSED_SIZE: Final = 1_337_902
SOURCE_PAYLOAD_SIZE: Final = 3_817_429
SOURCE_PAYLOAD_SHA256: Final = (
    "7858f787e44a25050f48186ad533be88dfb33a6fadc455c1ba6e9de18fae58b7"
)
SOURCE_RAM_OFFSET: Final = 0x1A62

SOURCE_MEDIA_PATH: Final = (
    rb"C:\Users\Chad\Xenogears_Reimagined\output\rico_arc\Xenogears_Rico_Arc.m3u"
)

# Field 721 / canonical 2048 is already resident.  Component 7 starts at this
# exact decompressed-state offset.  The source allocation ends at 0x110BB9;
# seven zero alignment bytes and an 18-byte allocator header follow it.  The
# revised component deliberately remains 11,803 bytes, preserving all of that
# runtime-owned memory byte-for-byte.
DIALOGUE_COMPONENT_INDEX: Final = 7
RESIDENT_DIALOGUE_PAYLOAD_OFFSET: Final = 0x10DD9E
RESIDENT_DIALOGUE_SIZE: Final = 11_803
SOURCE_DIALOGUE_SHA256: Final = (
    "a3d2421208494501a036dde7305197f7b2784e00a2e601afc329e45bdfe8f811"
)
TARGET_DIALOGUE_SHA256: Final = (
    "e7eb57eb7a996801048a5dd05205038b798120f1a6ade28be5fa81d9f7ba2873"
)
RESIDENT_DIALOGUE_PADDING: Final = bytes(7)
NEXT_ALLOCATOR_HEADER: Final = bytes.fromhex(
    "60 1D 00 02 2D E4 4B 12 6B 51 90 FC 10 80 5E C4 01 81"
)

TARGET_FIELD_CANONICAL_ID: Final = 2048
TARGET_FIELD_SECTOR: Final = 230_237
TARGET_FIELD_SIZE: Final = 37_728
TARGET_FIELD_SHA256: Final = (
    "fc586e6a5ffb9ce9db9cf4b4db647b2f0fd3130e7f6133abee6e762050c83081"
)
UNCHANGED_SCRIPT_SIZE: Final = 5_426
UNCHANGED_SCRIPT_SHA256: Final = (
    "85e334efff6a70674d84615fde31be4fd5be8f60bd1eebdb46e7ebc2b9d20386"
)

TARGET_DISC_SIZE: Final = 719_175_744
TARGET_DISC_SHA256: Final = (
    "f755cc84bd217bc4fd3fc7b546c20c22c764b4861f7ef75f4cabfd87c3404a75"
)
ARCHIVE_TABLE_SIZE: Final = 0x8000
ARCHIVE_TABLE_PAYLOAD_OFFSET: Final = 0x11A66
SOURCE_ARCHIVE_TABLE_SHA256: Final = (
    "c59fdb110087bd153f5e7118263ab4c003e770d8d9752883ead147166cb5f583"
)
SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "4f5824fb94369a465fd121c138c65f074a06043c13f1c7197efa5f8082852ddd"
)
SOURCE_VOLATILE_ARCHIVE_BYTE: Final = 0xC4
TARGET_ARCHIVE_TABLE_SHA256: Final = (
    "e5cd07aef6c4445852af5292a23f07656fc3af7443b29718fba9855fd7b1296f"
)
TARGET_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "edbfcc8f1f4eb685165271b515f8bb001d4710474f031c2a201141f6a08c8f83"
)
ARCHIVE_TABLE_DIFFS: Final = (
    (0x3803, 0x7C, 0x60),  # FAT 2048 size: 37,756 -> 37,728
)

EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT: Final = 633
EXPECTED_REPAIRED_PAYLOAD_SHA256: Final = (
    "afa5a6a39c848c414a1fba4985ae97d03c37bb920b2704c3b2107ee6f58af2e3"
)
EXPECTED_REPAIRED_STATE_SIZE: Final = 1_366_010
EXPECTED_REPAIRED_STATE_SHA256: Final = (
    "b74ea08c4bdfd235b94dc3be3da4da2ff84a2ecda0fe21dbc9274c41713b2f56"
)


class RicoChapterOneDialogueMigrationError(RuntimeError):
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
        raise RicoChapterOneDialogueMigrationError(
            f"Compared payload sizes differ: {len(before)} != {len(after)}"
        )
    return tuple(
        (offset, old, new)
        for offset, (old, new) in enumerate(zip(before, after, strict=True))
        if old != new
    )


def _validated_target_dialogue(new_disc: Path) -> tuple[bytes, bytes]:
    """Validate final staged media and return its dialogue and archive table."""

    if (
        not new_disc.is_file()
        or new_disc.stat().st_size != TARGET_DISC_SIZE
        or _file_sha256(new_disc) != TARGET_DISC_SHA256
    ):
        raise RicoChapterOneDialogueMigrationError(
            "Final staged Rico Disc 1 identity changed"
        )

    image = Mode2Image(new_disc)
    entries = image.read_index()
    if TARGET_FIELD_CANONICAL_ID >= len(entries):
        raise RicoChapterOneDialogueMigrationError(
            "Final staged Disc 1 is missing canonical 2048"
        )
    entry = entries[TARGET_FIELD_CANONICAL_ID]
    if (
        entry.kind != "file"
        or entry.sector != TARGET_FIELD_SECTOR
        or entry.size != TARGET_FIELD_SIZE
    ):
        raise RicoChapterOneDialogueMigrationError(
            "Final staged canonical-2048 FAT allocation changed"
        )
    field = image.extract_entry(entry)
    if len(field) != TARGET_FIELD_SIZE or _sha256(field) != TARGET_FIELD_SHA256:
        raise RicoChapterOneDialogueMigrationError(
            "Final staged canonical-2048 field identity changed"
        )
    parsed = parse_field(field)
    if len(parsed.parts) != 9:
        raise RicoChapterOneDialogueMigrationError(
            "Final staged canonical-2048 component count changed"
        )
    script = parsed.parts[5].data
    if (
        len(script) != UNCHANGED_SCRIPT_SIZE
        or _sha256(script) != UNCHANGED_SCRIPT_SHA256
    ):
        raise RicoChapterOneDialogueMigrationError(
            "Chapter 1 script changed with the dialogue-only rebuild"
        )
    dialogue = parsed.parts[DIALOGUE_COMPONENT_INDEX].data
    if (
        len(dialogue) != RESIDENT_DIALOGUE_SIZE
        or _sha256(dialogue) != TARGET_DIALOGUE_SHA256
    ):
        raise RicoChapterOneDialogueMigrationError(
            "Final staged Chapter 1 dialogue identity changed"
        )

    table = _archive_table(new_disc)
    if (
        len(table) != ARCHIVE_TABLE_SIZE
        or _sha256(table) != TARGET_ARCHIVE_TABLE_SHA256
    ):
        raise RicoChapterOneDialogueMigrationError(
            "Final staged Disc-1 archive table identity changed"
        )
    return dialogue, table


def migrate_state(
    state: bytes,
    *,
    zstd: _Zstd,
    new_disc: Path,
) -> tuple[bytes, dict[str, object]]:
    """Return the exact revised-dialogue candidate and its audit report."""

    state_hash = _sha256(state)
    if len(state) != SOURCE_STATE_SIZE or state_hash != SOURCE_STATE_SHA256:
        raise RicoChapterOneDialogueMigrationError(
            "Source Slot 1 identity changed: "
            f"{len(state)} bytes / {state_hash}; expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    if (
        len(state) < DUCKSTATION_STATE_HEADER_SIZE
        or state[:4] != DUCKSTATION_STATE_MAGIC
    ):
        raise RicoChapterOneDialogueMigrationError(
            "Source is not a supported DuckStation state"
        )
    if state.count(SOURCE_MEDIA_PATH) != 1:
        raise RicoChapterOneDialogueMigrationError(
            "Source state no longer mounts the stable Rico M3U path"
        )

    target_dialogue, target_archive_table = _validated_target_dialogue(
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
        raise RicoChapterOneDialogueMigrationError(
            "State payload is not Zstandard-compressed"
        )
    if (
        compressed_size != SOURCE_COMPRESSED_SIZE
        or payload_size != SOURCE_PAYLOAD_SIZE
        or frame_offset != SOURCE_FRAME_OFFSET
        or frame_offset + compressed_size != len(state)
    ):
        raise RicoChapterOneDialogueMigrationError(
            "Source DuckStation frame layout changed"
        )
    frame = state[frame_offset:]
    if not frame.startswith(ZSTD_MAGIC) or zstd.frame_size(frame) != compressed_size:
        raise RicoChapterOneDialogueMigrationError(
            "Source compressed frame identity is invalid"
        )

    source_payload = zstd.decompress(frame)
    if (
        len(source_payload) != SOURCE_PAYLOAD_SIZE
        or _sha256(source_payload) != SOURCE_PAYLOAD_SHA256
    ):
        raise RicoChapterOneDialogueMigrationError(
            "Source decompressed payload identity changed"
        )
    ram_offset = _psx_ram_offset(source_payload)
    if ram_offset != SOURCE_RAM_OFFSET or ram_offset + RAM_SIZE > len(source_payload):
        raise RicoChapterOneDialogueMigrationError(
            "Source PSX RAM layout changed"
        )

    dialogue_start = RESIDENT_DIALOGUE_PAYLOAD_OFFSET
    dialogue_end = dialogue_start + RESIDENT_DIALOGUE_SIZE
    source_dialogue = source_payload[dialogue_start:dialogue_end]
    if _sha256(source_dialogue) != SOURCE_DIALOGUE_SHA256:
        raise RicoChapterOneDialogueMigrationError(
            "Resident Chapter 1 dialogue identity changed"
        )
    padding_end = dialogue_end + len(RESIDENT_DIALOGUE_PADDING)
    header_end = padding_end + len(NEXT_ALLOCATOR_HEADER)
    if (
        source_payload[dialogue_end:padding_end] != RESIDENT_DIALOGUE_PADDING
        or source_payload[padding_end:header_end] != NEXT_ALLOCATOR_HEADER
    ):
        raise RicoChapterOneDialogueMigrationError(
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
        raise RicoChapterOneDialogueMigrationError(
            "Source resident Disc-1 archive table changed"
        )
    normalized_source_table = (
        source_resident_table[:-1] + target_archive_table[-1:]
    )
    if _sha256(normalized_source_table) != SOURCE_ARCHIVE_TABLE_SHA256:
        raise RicoChapterOneDialogueMigrationError(
            "Source normalized Disc-1 archive table changed"
        )
    archive_differences = _differences(
        normalized_source_table,
        target_archive_table,
    )
    if archive_differences != ARCHIVE_TABLE_DIFFS:
        raise RicoChapterOneDialogueMigrationError(
            "Source/final Disc-1 archive-table delta changed"
        )

    payload = bytearray(source_payload)
    payload[dialogue_start:dialogue_end] = target_dialogue
    for relative_offset, old, new in ARCHIVE_TABLE_DIFFS:
        offset = table_start + relative_offset
        if payload[offset] != old:
            raise RicoChapterOneDialogueMigrationError(
                f"Resident FAT byte changed at payload 0x{offset:X}"
            )
        payload[offset] = new

    repaired_payload = bytes(payload)
    if (
        repaired_payload[dialogue_end:padding_end] != RESIDENT_DIALOGUE_PADDING
        or repaired_payload[padding_end:header_end] != NEXT_ALLOCATOR_HEADER
    ):
        raise RicoChapterOneDialogueMigrationError(
            "Migration changed dialogue padding or its next allocator header"
        )
    target_resident_table = repaired_payload[table_start:table_end]
    if (
        _sha256(target_resident_table)
        != TARGET_RESIDENT_ARCHIVE_TABLE_SHA256
        or target_resident_table[:-1] != target_archive_table[:-1]
        or target_resident_table[-1] != SOURCE_VOLATILE_ARCHIVE_BYTE
    ):
        raise RicoChapterOneDialogueMigrationError(
            "Migrated resident Disc-1 archive table is not exact"
        )

    dialogue_differences = _differences(source_dialogue, target_dialogue)
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
        raise RicoChapterOneDialogueMigrationError(
            "Migration changed unexpected decompressed payload bytes"
        )
    repaired_payload_hash = _sha256(repaired_payload)
    if repaired_payload_hash != EXPECTED_REPAIRED_PAYLOAD_SHA256:
        raise RicoChapterOneDialogueMigrationError(
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
        raise RicoChapterOneDialogueMigrationError(
            "Repaired state failed its Zstandard round trip"
        )
    if (
        len(result) != EXPECTED_REPAIRED_STATE_SIZE
        or _sha256(result) != EXPECTED_REPAIRED_STATE_SHA256
    ):
        raise RicoChapterOneDialogueMigrationError(
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
        "dialogue_component_size": len(target_dialogue),
        "dialogue_changed_byte_count": len(dialogue_differences),
        "resident_archive_table_payload_offset": table_start,
        "resident_archive_table_changed_byte_count": len(ARCHIVE_TABLE_DIFFS),
        "target_field_canonical_id": TARGET_FIELD_CANONICAL_ID,
        "target_field_sector": TARGET_FIELD_SECTOR,
        "target_field_size": TARGET_FIELD_SIZE,
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
    except RicoChapterOneDialogueMigrationError as exc:
        raise SystemExit(str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)
    print(f"Wrote revised-dialogue savestate candidate: {output}")
    for key, value in report.items():
        if isinstance(value, int) and "offset" in key:
            value = f"0x{value:X}"
        print(f"{key}: {value}")
    print("The source and DuckStation's live Slot 1 were not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
