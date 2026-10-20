#!/usr/bin/env python3
"""Migrate the audited Rico Chapter 1 Slot 1 to the menu/equipment build.

The captured state predates Chapter 1's weapon/accessory inventory gate.  This
guarded migration models the retail ``8D`` removal result in its fixed
GameState arrays, replaces only the stable 20-byte resident main-menu hook,
and refreshes the exact two changed bytes in the resident Disc-1 FAT.

It intentionally does *not* write a helper into the menu overlay's nominal
tail: that area already contains allocator data in the captured state.  The
next main-menu load must therefore come from rebuilt media, which installs the
new hook and its helper together.  The source is never overwritten.
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

from tools import xgrico_balance as balance
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
from work.read_duckstation_runtime import GAME_STATE, RAM_SIZE, _psx_ram_offset


ROOT: Final = Path(__file__).resolve().parents[3]
DEFAULT_ZSTD: Final = ROOT / "work" / "duckstation" / "zstd.dll"
DEFAULT_NEW_DISC: Final = (
    ROOT / "output" / "rico_arc" / "Xenogears_Rico_Arc_Disc_1.bin"
)

SOURCE_STATE_SIZE: Final = 1_604_167
SOURCE_STATE_SHA256: Final = (
    "996988257079171b8cc32796f81d26f31c3c856959c30c23b8ab5d04b0f3c4ec"
)
SOURCE_FRAME_OFFSET: Final = 0x6DD0
SOURCE_COMPRESSED_SIZE: Final = 1_576_055
SOURCE_PAYLOAD_SIZE: Final = 3_817_429
SOURCE_PAYLOAD_SHA256: Final = (
    "5ee473c6b9720da5de242237032d430b5260b90f028b422989bbcc8fc09722d1"
)
SOURCE_RAM_OFFSET: Final = 0x1A62

# GameState inventory arrays.  Each family stores quantities first and item IDs
# in a parallel array.  Retail opcode 8D leaves the vacated quantity at zero
# and the corresponding ID at FF.
WEAPON_QUANTITY_OFFSET: Final = 0x1D38
WEAPON_ID_OFFSET: Final = 0x1D9C
ACCESSORY_QUANTITY_OFFSET: Final = 0x1E00
ACCESSORY_ID_OFFSET: Final = 0x1EC8
SOURCE_WEAPON_STACKS: Final = (
    (0, 0x32, 1),
    (1, 0x10, 1),
    (2, 0x39, 1),
    (3, 0x33, 1),
    (4, 0x01, 1),
    (6, 0x3A, 1),
    (7, 0x1F, 1),
)
SOURCE_ACCESSORY_STACKS: Final = (
    (5, 0x6A, 1),
    (6, 0x62, 3),
)

MENU_OVERLAY_RAM_OFFSET: Final = 0x1C5000
RESIDENT_GEAR_HOOK_RAM_OFFSET: Final = (
    MENU_OVERLAY_RAM_OFFSET + balance.GEAR_MENU_DRAW_HOOK_OFFSET
)
SOURCE_RESIDENT_GEAR_HOOK: Final = bytes.fromhex(
    "C8 A9 07 0C 00 00 00 00 "
    "06 80 04 3C A0 25 84 8C 00 00 00 00"
)
TARGET_RESIDENT_GEAR_HOOK: Final = bytes.fromhex(
    "06 80 10 3C A0 25 10 8E 2E A9 07 0C "
    "21 20 00 02 21 20 00 02"
)

# Both spans contain nonzero runtime data in the source and must remain exact.
TARGET_HELPER_RAM_SPAN: Final = (
    MENU_OVERLAY_RAM_OFFSET + balance.GEAR_MENU_GRAY_HELPER_OFFSET,
    MENU_OVERLAY_RAM_OFFSET + balance.GEAR_MENU_GRAY_HELPER_END,
)
HISTORICAL_HELPER_RAM_SPAN: Final = (
    MENU_OVERLAY_RAM_OFFSET + 0x25720,
    MENU_OVERLAY_RAM_OFFSET + 0x25720 + 0x40,
)

EXPECTED_REPAIRED_STATE_SIZE: Final = 1_366_014
EXPECTED_REPAIRED_STATE_SHA256: Final = (
    "34382f875ebe8522283ef4611a8e56f06e6413986b42f660f653479b831dd40e"
)
EXPECTED_REPAIRED_PAYLOAD_SHA256: Final = (
    "7858f787e44a25050f48186ad533be88dfb33a6fadc455c1ba6e9de18fae58b7"
)

# The save points at the stable Rico M3U path and currently has Disc 1
# mounted.  The final rebuild keeps that path and every relevant LBA fixed,
# but two resources grow: the item/equipment text table (physical FAT 1362)
# and the Chapter-1 hub (physical FAT 2046).  Xenogears keeps the 0x8000-byte
# archive table resident, so those two size bytes must catch up in the state.
SOURCE_MEDIA_PATH: Final = (
    rb"C:\Users\Chad\Xenogears_Reimagined\output\rico_arc\Xenogears_Rico_Arc.m3u"
)
ARCHIVE_TABLE_SIZE: Final = 0x8000
ARCHIVE_TABLE_PAYLOAD_OFFSET: Final = 0x11A66
SOURCE_ARCHIVE_TABLE_SHA256: Final = (
    "0b6b4c57041623a886c69fad8ac50a0a63079aef27d8b3f0f8a39792a47d445e"
)
SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "299a7bfe38b508a269a1a667a47c57800e48387eb8159ddb133ab6892a88b8cf"
)
SOURCE_VOLATILE_ARCHIVE_BYTE: Final = 0xC4
TARGET_DISC_SIZE: Final = 719_175_744
TARGET_DISC_SHA256: Final = (
    "f79ad6187686c1749c2e329b053f7b787207be8f93088665b8faa7ba331ede24"
)
TARGET_ARCHIVE_TABLE_SHA256: Final = (
    "c59fdb110087bd153f5e7118263ab4c003e770d8d9752883ead147166cb5f583"
)
TARGET_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "4f5824fb94369a465fd121c138c65f074a06043c13f1c7197efa5f8082852ddd"
)
ARCHIVE_TABLE_DIFFS: Final = (
    (0x2541, 0x30, 0x58),  # FAT 1362 size: 134448 -> 134488
    (0x37F5, 0xE4, 0xFC),  # FAT 2046 size:  43748 ->  43772
)
TARGET_FAT_ENTRIES: Final = {
    1362: (179_821, 134_488),
    2046: (230_160, 43_772),
    # The pending main-menu reload remains at the same exact allocation.
    2597: (239_671, 153_864),
}


class RicoChapterOneStateMigrationError(RuntimeError):
    """Raised before producing bytes when the pinned migration path drifts."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _differences(before: bytes, after: bytes) -> tuple[tuple[int, int, int], ...]:
    if len(before) != len(after):
        raise RicoChapterOneStateMigrationError(
            f"Compared payload sizes differ: {len(before)} != {len(after)}"
        )
    return tuple(
        (offset, old, new)
        for offset, (old, new) in enumerate(zip(before, after, strict=True))
        if old != new
    )


def _inventory_patches(
    *,
    ram_offset: int,
) -> tuple[tuple[int, int, int], ...]:
    patches: list[tuple[int, int, int]] = []
    families = (
        (WEAPON_QUANTITY_OFFSET, WEAPON_ID_OFFSET, SOURCE_WEAPON_STACKS),
        (
            ACCESSORY_QUANTITY_OFFSET,
            ACCESSORY_ID_OFFSET,
            SOURCE_ACCESSORY_STACKS,
        ),
    )
    for quantity_base, id_base, stacks in families:
        for slot, item_id, quantity in stacks:
            patches.append(
                (ram_offset + GAME_STATE + quantity_base + slot, quantity, 0)
            )
            patches.append(
                (ram_offset + GAME_STATE + id_base + slot, item_id, 0xFF)
            )
    return tuple(sorted(patches))


def _validated_target_archive_table(new_disc: Path) -> bytes:
    """Return the exact final Disc-1 table after validating media/layout."""

    if (
        not new_disc.is_file()
        or new_disc.stat().st_size != TARGET_DISC_SIZE
        or _file_sha256(new_disc) != TARGET_DISC_SHA256
    ):
        raise RicoChapterOneStateMigrationError(
            "Final Rico Disc 1 identity changed"
        )
    table = _archive_table(new_disc)
    if (
        len(table) != ARCHIVE_TABLE_SIZE
        or _sha256(table) != TARGET_ARCHIVE_TABLE_SHA256
    ):
        raise RicoChapterOneStateMigrationError(
            "Final Rico Disc-1 archive table identity changed"
        )

    entries = Mode2Image(new_disc).read_index()
    for index, expected in TARGET_FAT_ENTRIES.items():
        if index >= len(entries):
            raise RicoChapterOneStateMigrationError(
                f"Final Rico Disc 1 is missing FAT entry {index}"
            )
        entry = entries[index]
        actual = (entry.sector, entry.size)
        if entry.kind != "file" or actual != expected:
            raise RicoChapterOneStateMigrationError(
                f"Final Rico Disc-1 FAT {index} changed: {actual} != {expected}"
            )
    return table


def migrate_state(
    state: bytes,
    *,
    zstd: _Zstd,
    new_disc: Path,
) -> tuple[bytes, dict[str, object]]:
    """Return the guarded final-media candidate and its audit report."""

    state_hash = _sha256(state)
    if len(state) != SOURCE_STATE_SIZE or state_hash != SOURCE_STATE_SHA256:
        raise RicoChapterOneStateMigrationError(
            "Source Slot 1 identity changed: "
            f"{len(state)} bytes / {state_hash}; expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    if (
        len(state) < DUCKSTATION_STATE_HEADER_SIZE
        or state[:4] != DUCKSTATION_STATE_MAGIC
    ):
        raise RicoChapterOneStateMigrationError(
            "Source is not a supported DuckStation state"
        )
    if state.count(SOURCE_MEDIA_PATH) != 1:
        raise RicoChapterOneStateMigrationError(
            "Source state no longer mounts the stable Rico M3U path"
        )

    target_archive_table = _validated_target_archive_table(new_disc.resolve())

    compression_type, compressed_size, payload_size, frame_offset = (
        struct.unpack_from(
            "<IIII",
            state,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
        )
    )
    if compression_type != DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise RicoChapterOneStateMigrationError(
            "State payload is not Zstandard-compressed"
        )
    if (
        compressed_size != SOURCE_COMPRESSED_SIZE
        or payload_size != SOURCE_PAYLOAD_SIZE
        or frame_offset != SOURCE_FRAME_OFFSET
        or frame_offset + compressed_size != len(state)
    ):
        raise RicoChapterOneStateMigrationError(
            "Source DuckStation frame layout changed"
        )
    frame = state[frame_offset:]
    if not frame.startswith(ZSTD_MAGIC) or zstd.frame_size(frame) != compressed_size:
        raise RicoChapterOneStateMigrationError(
            "Source compressed frame identity is invalid"
        )

    source_payload = zstd.decompress(frame)
    if (
        len(source_payload) != SOURCE_PAYLOAD_SIZE
        or _sha256(source_payload) != SOURCE_PAYLOAD_SHA256
    ):
        raise RicoChapterOneStateMigrationError(
            "Source decompressed payload identity changed"
        )
    ram_offset = _psx_ram_offset(source_payload)
    if ram_offset != SOURCE_RAM_OFFSET:
        raise RicoChapterOneStateMigrationError(
            f"PSX RAM moved: 0x{ram_offset:X} != 0x{SOURCE_RAM_OFFSET:X}"
        )
    if ram_offset + RAM_SIZE > len(source_payload):
        raise RicoChapterOneStateMigrationError("PSX RAM span is truncated")

    table_start = ARCHIVE_TABLE_PAYLOAD_OFFSET
    table_end = table_start + ARCHIVE_TABLE_SIZE
    source_resident_table = source_payload[table_start:table_end]
    if (
        len(source_resident_table) != ARCHIVE_TABLE_SIZE
        or _sha256(source_resident_table)
        != SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256
        or source_resident_table[-1] != SOURCE_VOLATILE_ARCHIVE_BYTE
    ):
        raise RicoChapterOneStateMigrationError(
            "Source resident Disc-1 archive table changed"
        )
    normalized_source_table = source_resident_table[:-1] + target_archive_table[-1:]
    if (
        _sha256(normalized_source_table) != SOURCE_ARCHIVE_TABLE_SHA256
        or _differences(normalized_source_table, target_archive_table)
        != ARCHIVE_TABLE_DIFFS
    ):
        raise RicoChapterOneStateMigrationError(
            "Source/final Disc-1 archive-table delta changed"
        )

    if (
        TARGET_RESIDENT_GEAR_HOOK != balance.GEAR_MENU_DRAW_HOOK_PATCHED
        or RESIDENT_GEAR_HOOK_RAM_OFFSET
        != MENU_OVERLAY_RAM_OFFSET + balance.GEAR_MENU_DRAW_HOOK_OFFSET
    ):
        raise RicoChapterOneStateMigrationError(
            "Target Gear-menu hook no longer matches the rebuilt overlay"
        )

    payload = bytearray(source_payload)
    expected_changes: list[tuple[int, int, int]] = []
    for offset, expected, replacement in _inventory_patches(ram_offset=ram_offset):
        if payload[offset] != expected:
            raise RicoChapterOneStateMigrationError(
                f"Inventory source byte changed at payload 0x{offset:X}: "
                f"0x{payload[offset]:02X} != 0x{expected:02X}"
            )
        payload[offset] = replacement
        expected_changes.append((offset, expected, replacement))

    hook_offset = ram_offset + RESIDENT_GEAR_HOOK_RAM_OFFSET
    hook_end = hook_offset + len(SOURCE_RESIDENT_GEAR_HOOK)
    if bytes(payload[hook_offset:hook_end]) != SOURCE_RESIDENT_GEAR_HOOK:
        raise RicoChapterOneStateMigrationError(
            "Resident Gear-menu hook context changed"
        )
    payload[hook_offset:hook_end] = TARGET_RESIDENT_GEAR_HOOK
    expected_changes.extend(
        (hook_offset + index, old, new)
        for index, (old, new) in enumerate(
            zip(
                SOURCE_RESIDENT_GEAR_HOOK,
                TARGET_RESIDENT_GEAR_HOOK,
                strict=True,
            )
        )
        if old != new
    )

    for relative_offset, old, new in ARCHIVE_TABLE_DIFFS:
        offset = table_start + relative_offset
        if payload[offset] != old:
            raise RicoChapterOneStateMigrationError(
                f"Resident FAT source byte changed at payload 0x{offset:X}: "
                f"0x{payload[offset]:02X} != 0x{old:02X}"
            )
        payload[offset] = new
        expected_changes.append((offset, old, new))

    target_resident_table = bytes(payload[table_start:table_end])
    if (
        _sha256(target_resident_table)
        != TARGET_RESIDENT_ARCHIVE_TABLE_SHA256
        or target_resident_table[:-1] != target_archive_table[:-1]
        or target_resident_table[-1] != SOURCE_VOLATILE_ARCHIVE_BYTE
    ):
        raise RicoChapterOneStateMigrationError(
            "Migrated resident Disc-1 archive table is not exact"
        )

    repaired_payload = bytes(payload)
    actual_changes = _differences(source_payload, repaired_payload)
    if actual_changes != tuple(sorted(expected_changes)):
        raise RicoChapterOneStateMigrationError(
            f"Migration changed unexpected payload bytes: {actual_changes}"
        )
    repaired_payload_hash = _sha256(repaired_payload)
    if repaired_payload_hash != EXPECTED_REPAIRED_PAYLOAD_SHA256:
        raise RicoChapterOneStateMigrationError(
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
        raise RicoChapterOneStateMigrationError(
            "Repaired state failed its Zstandard round trip"
        )
    if (
        len(result) != EXPECTED_REPAIRED_STATE_SIZE
        or _sha256(result) != EXPECTED_REPAIRED_STATE_SHA256
    ):
        raise RicoChapterOneStateMigrationError(
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
        "changed_payload_byte_count": len(actual_changes),
        "inventory_changed_byte_count": len(_inventory_patches(ram_offset=ram_offset)),
        "gear_hook_changed_byte_count": sum(
            old != new
            for old, new in zip(
                SOURCE_RESIDENT_GEAR_HOOK,
                TARGET_RESIDENT_GEAR_HOOK,
                strict=True,
            )
        ),
        "gear_hook_payload_offset": hook_offset,
        "resident_archive_table_payload_offset": table_start,
        "resident_archive_table_changed_byte_count": len(ARCHIVE_TABLE_DIFFS),
        "source_archive_table_sha256": SOURCE_ARCHIVE_TABLE_SHA256,
        "target_archive_table_sha256": TARGET_ARCHIVE_TABLE_SHA256,
        "target_resident_archive_table_sha256": (
            TARGET_RESIDENT_ARCHIVE_TABLE_SHA256
        ),
        "volatile_archive_byte_preserved": True,
        "canonical_2597_sector": TARGET_FAT_ENTRIES[2597][0],
        "canonical_2597_size": TARGET_FAT_ENTRIES[2597][1],
        "resident_helper_patched": False,
        "menu_reload_from_rebuilt_media_required": True,
        "resident_fat_migrated": True,
        "media_path_rewrite_required_if_output_path_is_unchanged": False,
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
    if source == output:
        raise SystemExit("Output must be separate and may not be live Slot 1")
    for path, label in (
        (source, "source state"),
        (zstd_path, "zstd library"),
        (new_disc, "final Rico Disc 1"),
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
    except RicoChapterOneStateMigrationError as exc:
        raise SystemExit(str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)
    print(f"Wrote final-media savestate candidate: {output}")
    for key, value in report.items():
        if isinstance(value, int) and "offset" in key:
            value = f"0x{value:X}"
        print(f"{key}: {value}")
    print("The source Slot 1 was not modified.")
    print("Resident FAT now matches the validated final rebuilt Disc 1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
