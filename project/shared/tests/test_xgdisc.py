from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.xgdisc import (
    DIRECTORY_SECTOR,
    INDEX_ENTRY_SIZE,
    INDEX_SECTOR,
    Mode2Image,
    RAW_SECTOR_SIZE,
    USER_DATA_OFFSET,
    directory_file_fat_index,
)


def _entry(sector: int, size: int) -> bytes:
    return sector.to_bytes(3, "little") + size.to_bytes(4, "little")


def _put_user_data(image: bytearray, sector: int, data: bytes) -> None:
    remaining = memoryview(data)
    current_sector = sector
    while remaining:
        chunk = remaining[:2048]
        offset = current_sector * RAW_SECTOR_SIZE + USER_DATA_OFFSET
        image[offset : offset + len(chunk)] = chunk
        remaining = remaining[len(chunk) :]
        current_sector += 1


class Mode2ImageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.image_path = Path(self.temporary_directory.name) / "synthetic.bin"

        image = bytearray(64 * RAW_SECTOR_SIZE)
        index = b"".join(
            (
                _entry(50, 5),
                _entry(0, 0),
                _entry(0, 0xFF000000),
                _entry(0xFFFFFF, 0),
            )
        )
        self.assertEqual(len(index), 4 * INDEX_ENTRY_SIZE)
        _put_user_data(image, INDEX_SECTOR, index)
        directory_table = bytearray(b"\xff\xff" * 61)
        directory_table[8:10] = (419).to_bytes(2, "little", signed=True)
        _put_user_data(image, DIRECTORY_SECTOR, directory_table)
        _put_user_data(image, 50, b"hello")
        self.image_path.write_bytes(image)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_reads_and_classifies_index(self) -> None:
        entries = Mode2Image(self.image_path).read_index()

        self.assertEqual(len(entries), 4)
        self.assertEqual(entries[0].kind, "file")
        self.assertEqual(entries[1].kind, "empty")
        self.assertEqual(entries[2].kind, "metadata")
        self.assertEqual(entries[3].sector, 0xFFFFFF)

    def test_extracts_only_declared_file_bytes(self) -> None:
        image = Mode2Image(self.image_path)

        self.assertEqual(image.extract_entry(image.read_index()[0]), b"hello")

    def test_reads_directory_table(self) -> None:
        directories = Mode2Image(self.image_path).read_directories()

        self.assertEqual(len(directories), 61)
        self.assertEqual(directories[4].first_file, 419)
        self.assertEqual(directories[5].first_file, -1)

    def test_resolves_mass_driver_field_file(self) -> None:
        self.assertEqual(directory_file_fat_index(419, 0xB8 + 2 * 617), 1835)


if __name__ == "__main__":
    unittest.main()
