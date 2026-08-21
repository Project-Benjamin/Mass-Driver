#!/usr/bin/env python3
"""Read Xenogears' custom file table from a raw MODE2/2352 BIN image.

This tool is intentionally read-only.  It never writes to the source image;
the extract command only creates ordinary files in a separate directory.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys
from typing import BinaryIO, Iterable, Sequence


RAW_SECTOR_SIZE = 2352
USER_DATA_OFFSET = 24
USER_DATA_SIZE = 2048
INDEX_SECTOR = 24
INDEX_SECTORS = 16
INDEX_ENTRY_SIZE = 7
INDEX_TERMINATOR = 0xFFFFFF
DIRECTORY_SECTOR = 40
DIRECTORY_TABLE_SIZE = 0x7A
FIELD_DIRECTORY = 4
FIRST_FIELD_LOCAL_FILE = 0xB8


class DiscFormatError(RuntimeError):
    """Raised when an image does not match the expected Xenogears layout."""


@dataclass(frozen=True)
class IndexEntry:
    index: int
    sector: int
    size: int
    kind: str

    @property
    def canonical_disc2_index(self) -> int:
        """Return the SadNES/global file number used by ``cd2fix`` lists."""

        return self.index + 5


@dataclass(frozen=True)
class DirectoryEntry:
    index: int
    first_file: int


def classify_entry(sector: int, size: int) -> str:
    """Match Xenoiso 0.95's custom-FAT entry classification."""

    if sector != 0 and 0 < size < 0xFF000000:
        return "file"
    if sector == 0 and size == 0:
        return "empty"
    return "metadata"


class Mode2Image:
    """Read user data and Xenogears FAT entries from a raw BIN image."""

    def __init__(self, path: Path | str):
        self.path = Path(path).resolve()
        if not self.path.is_file():
            raise DiscFormatError(f"Image does not exist: {self.path}")

        image_size = self.path.stat().st_size
        if image_size % RAW_SECTOR_SIZE != 0:
            raise DiscFormatError(
                f"Expected a MODE2/2352 BIN; size is not divisible by "
                f"{RAW_SECTOR_SIZE}: {image_size} bytes"
            )
        self.sector_count = image_size // RAW_SECTOR_SIZE
        if self.sector_count < INDEX_SECTOR + INDEX_SECTORS:
            raise DiscFormatError("Image is too small to contain the Xenogears FAT")

    def _read_user_data_from(
        self, handle: BinaryIO, sector: int, byte_count: int
    ) -> bytes:
        if sector < 0 or byte_count < 0:
            raise ValueError("sector and byte_count must be non-negative")

        sectors_needed = (byte_count + USER_DATA_SIZE - 1) // USER_DATA_SIZE
        if sector + sectors_needed > self.sector_count:
            raise DiscFormatError(
                f"Read extends beyond image: sector {sector}, {byte_count} bytes"
            )

        result = bytearray()
        remaining = byte_count
        current_sector = sector
        while remaining:
            take = min(USER_DATA_SIZE, remaining)
            handle.seek(current_sector * RAW_SECTOR_SIZE + USER_DATA_OFFSET)
            chunk = handle.read(take)
            if len(chunk) != take:
                raise DiscFormatError(
                    f"Short read at sector {current_sector}: "
                    f"wanted {take} bytes, got {len(chunk)}"
                )
            result.extend(chunk)
            remaining -= take
            current_sector += 1
        return bytes(result)

    def read_user_data(self, sector: int, byte_count: int) -> bytes:
        with self.path.open("rb") as handle:
            return self._read_user_data_from(handle, sector, byte_count)

    def read_index(self) -> list[IndexEntry]:
        index_data = self.read_user_data(
            INDEX_SECTOR, INDEX_SECTORS * USER_DATA_SIZE
        )
        entries: list[IndexEntry] = []

        for offset in range(0, len(index_data) - INDEX_ENTRY_SIZE + 1, 7):
            sector = int.from_bytes(index_data[offset : offset + 3], "little")
            size = int.from_bytes(index_data[offset + 3 : offset + 7], "little")
            entry = IndexEntry(
                index=len(entries),
                sector=sector,
                size=size,
                kind=classify_entry(sector, size),
            )
            entries.append(entry)
            if sector == INDEX_TERMINATOR:
                return entries

        raise DiscFormatError(
            f"No aligned 0xFFFFFF FAT terminator in the {len(index_data)}-byte index"
        )

    def read_directories(self) -> list[DirectoryEntry]:
        directory_data = self.read_user_data(DIRECTORY_SECTOR, DIRECTORY_TABLE_SIZE)
        return [
            DirectoryEntry(
                index=offset // 2,
                first_file=int.from_bytes(
                    directory_data[offset : offset + 2], "little", signed=True
                ),
            )
            for offset in range(0, len(directory_data), 2)
        ]

    def extract_entry(self, entry: IndexEntry) -> bytes:
        if entry.kind != "file":
            raise DiscFormatError(
                f"FAT entry {entry.index} is {entry.kind}, not an extractable file"
            )
        return self.read_user_data(entry.sector, entry.size)


def _parse_int(value: str) -> int:
    try:
        return int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not an integer: {value}") from exc


def directory_file_fat_index(first_file: int, local_file: int) -> int:
    """Resolve the game's one-based-ish directory lookup to a physical FAT index."""

    if first_file < 0:
        raise DiscFormatError("Directory is absent on this disc")
    if local_file < 1:
        raise DiscFormatError("Directory-local file index must be at least 1")
    # Matches setCurrentDirectory() and getFileStartSector() in the game:
    #   start = first_file - 1
    #   FAT index = local_file + start - 1
    return first_file + local_file - 2


def _selected_entries(
    entries: Sequence[IndexEntry], start: int | None, end: int | None
) -> Iterable[IndexEntry]:
    first = 0 if start is None else start
    last = len(entries) - 1 if end is None else end
    if first < 0 or last < first:
        raise DiscFormatError(f"Invalid inclusive range: {first}..{last}")
    if last >= len(entries):
        raise DiscFormatError(
            f"Range ends at {last}, but the last FAT entry is {len(entries) - 1}"
        )
    return entries[first : last + 1]


def command_list(args: argparse.Namespace) -> int:
    image = Mode2Image(args.image)
    entries = image.read_index()
    selected = list(_selected_entries(entries, args.start, args.end))

    if args.json:
        payload = {
            "image": str(image.path),
            "raw_sectors": image.sector_count,
            "entry_count": len(entries),
            "entries": [
                {**asdict(entry), "canonical_disc2_index": entry.index + 5}
                for entry in selected
            ],
        }
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Image: {image.path}")
    print(f"Raw sectors: {image.sector_count}")
    print(f"FAT entries (including terminator): {len(entries)}")
    print(" index  cd2fix     sector        size  kind")
    for entry in selected:
        print(
            f"{entry.index:6d}  {entry.canonical_disc2_index:6d}  "
            f"{entry.sector:9d}  {entry.size:10d}  {entry.kind}"
        )
    return 0


def command_directories(args: argparse.Namespace) -> int:
    image = Mode2Image(args.image)
    directories = image.read_directories()
    if args.json:
        print(
            json.dumps(
                {
                    "image": str(image.path),
                    "directories": [asdict(entry) for entry in directories],
                },
                indent=2,
            )
        )
        return 0

    print(f"Image: {image.path}")
    print("directory  first FAT entry")
    for entry in directories:
        print(f"{entry.index:9d}  {entry.first_file:15d}")
    return 0


def command_field(args: argparse.Namespace) -> int:
    image = Mode2Image(args.image)
    entries = image.read_index()
    directories = image.read_directories()
    field_directory = directories[FIELD_DIRECTORY]
    results = []

    for scene in args.scenes:
        if scene < 0:
            raise DiscFormatError(f"Field scene must be non-negative: {scene}")
        bundle_local = FIRST_FIELD_LOCAL_FILE + 2 * scene
        pair = []
        for role, local_file in (
            ("bundle", bundle_local),
            ("graphics", bundle_local + 1),
        ):
            fat_index = directory_file_fat_index(
                field_directory.first_file, local_file
            )
            if fat_index >= len(entries):
                raise DiscFormatError(
                    f"Field {scene} {role} resolves to FAT {fat_index}, "
                    f"past the last entry {len(entries) - 1}"
                )
            entry = entries[fat_index]
            pair.append(
                {
                    "role": role,
                    "directory": FIELD_DIRECTORY,
                    "local_file": local_file,
                    "fat_index": fat_index,
                    "canonical_disc2_index": fat_index + 5,
                    "sector": entry.sector,
                    "size": entry.size,
                    "kind": entry.kind,
                }
            )
        results.append({"scene": scene, "files": pair})

    if args.json:
        print(
            json.dumps(
                {
                    "image": str(image.path),
                    "field_directory_first_file": field_directory.first_file,
                    "fields": results,
                },
                indent=2,
            )
        )
        return 0

    print(f"Image: {image.path}")
    print(
        f"Field directory {FIELD_DIRECTORY} begins at directory-table value "
        f"{field_directory.first_file}"
    )
    print(" scene  role      local     FAT  cd2fix     sector        size  kind")
    for result in results:
        for item in result["files"]:
            print(
                f"{result['scene']:6d}  {item['role']:8s}  "
                f"{item['local_file']:5d}  {item['fat_index']:6d}  "
                f"{item['canonical_disc2_index']:6d}  {item['sector']:9d}  "
                f"{item['size']:10d}  {item['kind']}"
            )
    return 0


def command_extract(args: argparse.Namespace) -> int:
    image = Mode2Image(args.image)
    entries = image.read_index()
    requested = args.indices
    namespace = "fat"
    if args.canonical_disc2 is not None:
        requested = [value - 5 for value in args.canonical_disc2]
        namespace = "canonical"

    output_directory = Path(args.output).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    for index in requested:
        if index < 0 or index >= len(entries):
            raise DiscFormatError(
                f"FAT index {index} is outside 0..{len(entries) - 1}"
            )
        entry = entries[index]
        display_index = index + 5 if namespace == "canonical" else index
        output_path = output_directory / f"{display_index:04d}.bin"
        if output_path.exists() and not args.force:
            raise DiscFormatError(
                f"Refusing to overwrite {output_path}; pass --force to replace it"
            )
        output_path.write_bytes(image.extract_entry(entry))
        print(
            f"Extracted FAT {index} (cd2fix {index + 5}) -> "
            f"{output_path} ({entry.size} bytes)"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect or extract Xenogears' custom FAT from a raw MODE2/2352 "
            "BIN image. The source image is never modified."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="list custom FAT entries")
    list_parser.add_argument("image", type=Path)
    list_parser.add_argument("--start", type=_parse_int)
    list_parser.add_argument("--end", type=_parse_int)
    list_parser.add_argument("--json", action="store_true")
    list_parser.set_defaults(handler=command_list)

    directories_parser = subparsers.add_parser(
        "directories", help="list the game's directory table"
    )
    directories_parser.add_argument("image", type=Path)
    directories_parser.add_argument("--json", action="store_true")
    directories_parser.set_defaults(handler=command_directories)

    field_parser = subparsers.add_parser(
        "field", help="resolve field scene IDs to Disc 2 FAT entries"
    )
    field_parser.add_argument("image", type=Path)
    field_parser.add_argument("scenes", nargs="+", type=_parse_int)
    field_parser.add_argument("--json", action="store_true")
    field_parser.set_defaults(handler=command_field)

    extract_parser = subparsers.add_parser(
        "extract", help="extract regular 2048-byte-sector files"
    )
    extract_parser.add_argument("image", type=Path)
    extract_parser.add_argument("output", type=Path)
    selection = extract_parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--indices",
        nargs="+",
        type=_parse_int,
        help="physical Disc FAT indices",
    )
    selection.add_argument(
        "--canonical-disc2",
        nargs="+",
        type=_parse_int,
        help="global filenames used by Xenoiso's cd2fix mode (physical index + 5)",
    )
    extract_parser.add_argument("--force", action="store_true")
    extract_parser.set_defaults(handler=command_extract)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (DiscFormatError, OSError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
