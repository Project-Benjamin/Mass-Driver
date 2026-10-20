from pathlib import Path
import hashlib
import struct
import unittest

from modules.rico import build as core
from modules.rico import chapter_two_guard as guard


class IntakeGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = core.ROOT / "Xenogears (Disc 1).bin"
        if not path.is_file():
            raise unittest.SkipTest("Retail Disc 1 required")
        reader = core.DiscReader(path, 1)
        cls.original = reader.canonical(1032)
        cls.original_graphics = reader.canonical(1033)
        cls.donor = reader.canonical(1066)
        cls.result = guard.install_intake_guard(cls.original, cls.donor)
        cls.graphics = guard.install_intake_guard_graphics(cls.original_graphics, cls.donor)

    def test_guard_upload_preserves_the_existing_local_bank_and_other_resources(self):
        before, after = core.parse_field(self.original), core.parse_field(self.result)
        actor_before = core.mass_driver._indexed_bundle_entries(before.parts[3].data)
        actor_after = core.mass_driver._indexed_bundle_entries(after.parts[3].data)
        self.assertEqual(actor_before[1:], actor_after[1:])
        self.assertEqual((len(actor_after[0]), hashlib.sha256(actor_after[0]).hexdigest()), guard.GUARD_ACTOR_IDENTITY)
        local_before = core.mass_driver._indexed_bundle_entries(before.parts[4].data)
        local_after = core.mass_driver._indexed_bundle_entries(after.parts[4].data)
        self.assertEqual(local_after[1:], local_before)
        self.assertEqual((len(local_after[0]), hashlib.sha256(local_after[0]).hexdigest()), guard.GUARD_SPRITE_IDENTITY)
        for index in range(len(before.parts)):
            if index not in (3, 4):
                self.assertEqual(before.parts[index].data, after.parts[index].data)
        self.assertEqual(struct.unpack_from("<4H", after.header), (832, 0, 0, 0))
        self.assertEqual(before.header[8:0x10C], after.header[8:0x10C])

    def test_changed_or_wrong_donors_are_rejected(self):
        with self.assertRaises(ValueError):
            guard.install_intake_guard(self.result, self.donor)
        with self.assertRaises(ValueError):
            guard.install_intake_guard(self.original, self.original)

    def test_external_upload_preserves_every_other_block_and_full_guard_pixels(self):
        before, rects_before = core.mass_driver._reconstruct_field_graphics_vram(
            self.original_graphics, label="original intake")
        after, rects_after = core.mass_driver._reconstruct_field_graphics_vram(
            self.graphics, label="guard intake")
        self.assertEqual(len(self.graphics) - len(self.original_graphics), 3 * 0x800)
        start, end = guard.GUARD_GRAPHICS_BLOCK_START, guard.GUARD_GRAPHICS_BLOCK_END
        self.assertEqual(self.graphics[:start], self.original_graphics[:start])
        self.assertEqual(self.graphics[end + 3 * 0x800:], self.original_graphics[end:])
        self.assertEqual(rects_after, tuple(guard.GUARD_VRAM_RECT
                         if rect == guard.GUARD_ORIGINAL_GRAPHICS_RECT else rect for rect in rects_before))
        # A replay of the external stream must supply all178 rows, including
        # the44 rows beyond the old134-row Suzarn cell.
        field = core.parse_field(self.result)
        bank = core.mass_driver._indexed_bundle_entries(field.parts[4].data)[0]
        local_pixels = core.mass_driver._indexed_bundle_entries(bank)[0][4:]
        x, y, width, height = guard.GUARD_VRAM_RECT
        external_pixels = b"".join(after[((y + row) * 1024 + x) * 2:
                                        ((y + row) * 1024 + x + width) * 2]
                                    for row in range(height))
        self.assertEqual(external_pixels, local_pixels)
        # Palette/model textures outside the guard cell remain byte exact.
        for row in range(512):
            if y <= row < y + height:
                left, right = (row * 1024 + x) * 2, (row * 1024 + x + width) * 2
                after[left:right] = before[left:right]
        self.assertEqual(after, before)

    def test_external_upload_rejects_changed_graphics_or_guard_source(self):
        for graphics, donor in ((self.graphics, self.donor),
                                (self.original_graphics[:-1] + bytes([self.original_graphics[-1] ^ 1]), self.donor),
                                (self.original_graphics, self.original)):
            with self.subTest(graphics_size=len(graphics), donor_size=len(donor)), self.assertRaises(ValueError):
                guard.install_intake_guard_graphics(graphics, donor)


if __name__ == "__main__":
    unittest.main()
