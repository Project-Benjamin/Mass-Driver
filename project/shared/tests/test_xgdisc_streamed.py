"""XA movie extents and full-sector integrity must not use 2048-byte reads."""

from dataclasses import replace
import hashlib
from pathlib import Path
import tempfile
import unittest

from shared.tools.xgdisc import (
    DiscFormatError, IndexEntry, Mode2Image, RAW_SECTOR_SIZE,
    XA_STORED_SECTOR_SIZE, streamed_movie_entries,
)


def movie_group(count=2):
    entries = [IndexEntry(0, 41, (1 << 32) - count, "metadata")]
    cursor = 41
    for index in range(1, count + 1):
        sectors = index + 1
        entries.append(IndexEntry(index, cursor, sectors * XA_STORED_SECTOR_SIZE, "file"))
        cursor += sectors
    entries.append(IndexEntry(count + 1, cursor, 0, "metadata"))
    entries.append(IndexEntry(count + 2, cursor, 10, "file"))
    return entries


class StreamedMovieGroupTests(unittest.TestCase):
    def test_counted_groups_identify_both_retail_disc_lengths(self):
        for count in (17, 12):
            with self.subTest(count=count):
                entries = movie_group(count)
                result = streamed_movie_entries(entries)
                self.assertEqual(result, tuple(entries[1:count + 1]))
                self.assertEqual(sum(entry.size // XA_STORED_SECTOR_SIZE for entry in result),
                                 entries[count + 1].sector - entries[0].sector)

    def test_regular_file_fixtures_are_not_misclassified_as_movies(self):
        for entries in ([], [IndexEntry(0, 41, 2048, "file")],
                        [IndexEntry(0, 41, 0, "metadata")]):
            with self.subTest(entries=entries):
                self.assertEqual(streamed_movie_entries(entries), ())

    def test_fractional_xa_sizes_and_bad_member_kinds_are_rejected(self):
        for mutation in (lambda entry: replace(entry, size=entry.size + 1),
                         lambda entry: replace(entry, kind="metadata")):
            entries = movie_group()
            entries[1] = mutation(entries[1])
            with self.assertRaisesRegex(DiscFormatError, "2336"):
                streamed_movie_entries(entries)

    def test_group_start_gaps_overlaps_and_wrong_ending_boundary_are_rejected(self):
        mutations = [
            lambda entries: entries.__setitem__(0, replace(entries[0], sector=40)),
            lambda entries: entries.__setitem__(2, replace(entries[2], sector=entries[2].sector + 1)),
            lambda entries: entries.__setitem__(2, replace(entries[2], sector=entries[2].sector - 1)),
            lambda entries: entries.__setitem__(3, replace(entries[3], kind="file")),
        ]
        for mutation in mutations:
            entries = movie_group()
            mutation(entries)
            with self.subTest(entries=entries), self.assertRaises(DiscFormatError):
                streamed_movie_entries(entries)

    def test_count_overflow_and_truncated_group_are_rejected(self):
        entries = movie_group()
        entries[0] = replace(entries[0], size=0xFF000000)
        with self.assertRaisesRegex(DiscFormatError, "count"):
            streamed_movie_entries(entries)
        with self.assertRaisesRegex(DiscFormatError, "count"):
            streamed_movie_entries(movie_group()[:3])


class RawSectorHashTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="xgxa_")
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "mixed-mode2.bin"
        data = bytearray(64 * RAW_SECTOR_SIZE)
        # Form1 video followed by Form2 audio. Full raw bytes include headers,
        # both subheader copies, payload, and ECC/EDC beyond byte 24 + 2048.
        for sector, submode in ((44, 0x42), (45, 0x64)):
            start = sector * RAW_SECTOR_SIZE
            data[start:start + RAW_SECTOR_SIZE] = bytes((index + sector) % 256 for index in range(RAW_SECTOR_SIZE))
            data[start + 15] = 2
            data[start + 16:start + 24] = bytes((1, 1, submode, 0x80)) * 2
        self.data = bytes(data)
        self.path.write_bytes(data)
        self.image = Mode2Image(self.path)

    def test_hash_includes_full_mixed_form_sectors_and_exact_extent_only(self):
        begin, end = 44 * RAW_SECTOR_SIZE, 46 * RAW_SECTOR_SIZE
        expected = hashlib.sha256(self.data[begin:end]).hexdigest()
        self.assertEqual(self.image.raw_sector_sha256(44, 2), expected)
        changed = bytearray(self.data)
        changed[end + 10] ^= 0xFF  # A following ordinary file is outside movie.
        self.path.write_bytes(changed)
        self.assertEqual(self.image.raw_sector_sha256(44, 2), expected)
        for offset in (begin + 3, begin + 18, begin + 24 + 2200):
            with self.subTest(offset=offset):
                changed = bytearray(self.data)
                changed[offset] ^= 0xFF
                self.path.write_bytes(changed)
                self.assertNotEqual(self.image.raw_sector_sha256(44, 2), expected)

    def test_invalid_types_and_out_of_range_extents_are_rejected(self):
        for sector, count in [(-1, 1), (0, 0), (0, -1), (64, 1), (63, 2), (True, 1), (0, True), (0.0, 1)]:
            with self.subTest(sector=sector, count=count), self.assertRaises(DiscFormatError):
                self.image.raw_sector_sha256(sector, count)

    def test_truncation_after_open_is_rejected_instead_of_hashing_short_data(self):
        self.path.write_bytes(self.data[:-1])
        with self.assertRaisesRegex(DiscFormatError, "Short read"):
            self.image.raw_sector_sha256(63, 1)


if __name__ == "__main__":
    unittest.main()
