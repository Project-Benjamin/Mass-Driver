import struct
import unittest

from modules.rico import build as core
from modules.rico import chapter_two_clerk as clerk


class CommonsClerkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = core.ROOT / "Xenogears (Disc 1).bin"
        if not path.is_file():
            raise unittest.SkipTest("Retail Disc1 required")
        reader = core.DiscReader(path, 1)
        cls.original = reader.canonical(1028)
        cls.original_graphics = reader.canonical(1029)
        cls.donor = reader.canonical(1048)
        cls.donor_graphics = reader.canonical(1049)
        cls.result = clerk.install_commons_clerk(cls.original, cls.donor)
        cls.graphics = clerk.install_commons_clerk_graphics(cls.original_graphics, cls.donor_graphics)

    def test_only_the_commons_clerk_actor_bank_changes(self):
        before, after = core.parse_field(self.original), core.parse_field(self.result)
        old = core.mass_driver._indexed_bundle_entries(before.parts[3].data)
        new = core.mass_driver._indexed_bundle_entries(after.parts[3].data)
        donor = core.mass_driver._indexed_bundle_entries(core.parse_field(self.donor).parts[3].data)[4]
        self.assertEqual(new[2], donor)
        for bank in (0, 1, 3, 4):
            self.assertEqual(new[bank], old[bank])
        for index in range(len(before.parts)):
            if index != 3:
                self.assertEqual(before.parts[index].data, after.parts[index].data)
        self.assertEqual(before.header[:0x10C], after.header[:0x10C])
        self.assertEqual(before.header[0x18C:], after.header[0x18C:])
        self.assertEqual(struct.unpack_from("<4H", after.header, 2 * 8), (960, 0, 0, 1))
        # No local sprite upload competes with the existing external producer.
        self.assertEqual(after.parts[4].data, before.parts[4].data)

    def test_exact_native_receptionist_pixels_and_clear_unused_rows(self):
        native = core.mass_driver
        before, old_rects = native._reconstruct_field_graphics_vram(self.original_graphics, label="before")
        after, new_rects = native._reconstruct_field_graphics_vram(self.graphics, label="after")
        source, _ = native._reconstruct_field_graphics_vram(self.donor_graphics, label="source")
        self.assertEqual(old_rects, new_rects)
        self.assertEqual(len(self.graphics), len(self.original_graphics))
        for row in range(228):
            start = (row * 1024 + 960) * 2
            expected = (source[((256 + row) * 1024 + 384) * 2:
                               ((256 + row) * 1024 + 448) * 2] if row < 171 else bytes(128))
            self.assertEqual(after[start:start + 128], expected)
            after[start:start + 128] = before[start:start + 128]
        self.assertEqual(after, before, "All VRAM outside the existing bank2 cell must survive")

    def test_upload_headers_sector_padding_and_other_bytes_are_identical(self):
        start, end = clerk.CLERK_GRAPHICS_BLOCK_START, clerk.CLERK_GRAPHICS_BLOCK_END
        self.assertEqual(self.graphics[:start + 0x800], self.original_graphics[:start + 0x800])
        self.assertEqual(self.graphics[end:], self.original_graphics[end:])
        # Final sector contains only4 rows; retain its1536 padding bytes.
        self.assertEqual(self.graphics[end - 0x600:end], self.original_graphics[end - 0x600:end])

    def test_wrong_or_modified_donors_are_rejected(self):
        for original, donor in ((self.result, self.donor), (self.original, self.original)):
            with self.assertRaises(ValueError):
                clerk.install_commons_clerk(original, donor)
        for graphics, donor in ((self.graphics, self.donor_graphics),
                                (self.original_graphics, self.original_graphics)):
            with self.assertRaises(ValueError):
                clerk.install_commons_clerk_graphics(graphics, donor)


if __name__ == "__main__":
    unittest.main()
