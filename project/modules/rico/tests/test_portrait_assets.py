from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageDraw

from modules.rico import portrait_assets as portraits


class PortraitAssetsTests(unittest.TestCase):
    def test_explicit_border_matte_removal_preserves_enclosed_black_details(self):
        image = Image.new("RGBA", (64, 64), (1, 2, 1, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle((8, 8, 55, 63), fill=(100, 80, 56, 255))
        draw.rectangle((20, 20, 25, 25), fill=(0, 0, 0, 255))
        # The lower edge has visible dark clothing, beyond the matte cutoff.
        draw.rectangle((8, 60, 55, 63), fill=(16, 16, 16, 255))
        image.putpixel((30, 30), (60, 40, 20, 0))
        plain = portraits.portrait_tim_to_image(portraits.image_to_portrait_tim(image))
        keyed = portraits.portrait_tim_to_image(portraits.image_to_portrait_tim(
            image, border_connected_black_matte_max_channel=8,
        ))
        self.assertEqual(plain.getpixel((0, 0))[3], 255)
        for position in ((0, 0), (63, 0), (0, 63), (63, 63)):
            self.assertEqual(keyed.getpixel(position)[3], 0)
        self.assertEqual(keyed.getpixel((22, 22)), (0, 0, 0, 255))
        self.assertEqual(keyed.getpixel((30, 63))[3], 255)
        self.assertEqual(keyed.getpixel((30, 30))[3], 0)
        self.assertEqual(image.getpixel((0, 0)), (1, 2, 1, 255))

    def test_native_container_round_trip_preserves_transparency_and_black(self):
        image = Image.new("RGBA", (64, 64), (255, 0, 0, 255))
        image.putpixel((0, 0), (0, 0, 0, 0))
        image.putpixel((1, 0), (0, 0, 0, 255))
        image.putpixel((2, 0), (0, 255, 0, 255))
        image.putpixel((3, 0), (0, 0, 255, 255))
        data = portraits.image_to_portrait_tim(image)
        self.assertEqual(len(data), 4640)
        self.assertEqual(data, portraits.image_to_portrait_tim(image))
        decoded = portraits.portrait_tim_to_image(data)
        self.assertEqual(decoded.getpixel((0, 0))[3], 0)
        self.assertEqual(decoded.getpixel((1, 0)), (0, 0, 0, 255))
        self.assertEqual(decoded.getpixel((2, 0)), (0, 255, 0, 255))
        self.assertEqual(decoded.getpixel((3, 0)), (0, 0, 255, 255))
        self.assertEqual(decoded.getpixel((4, 0)), (255, 0, 0, 255))

    def test_manifest_slots_do_not_overlap_recorded_native_consumers(self):
        document = portraits.load_portrait_manifest()
        reserved = set(portraits.CUSTOM_PORTRAIT_IDS.values())
        self.assertEqual(len(reserved), 20)
        for profile in ("mass_driver", "soylent_system", "rico"):
            self.assertFalse(reserved & set(document["allocation_audit"][profile]["immediate_native_portrait_ids"]))
        self.assertFalse(reserved & {12, 28, 44, 89})
        for asset in document["assets"]:
            self.assertEqual(asset["disc1_fat_index"], asset["canonical_id"])
            self.assertEqual(asset["disc2_fat_index"], asset["canonical_id"] - 5)
            self.assertTrue(asset["accepted_source_sha256"])

    def test_compilation_checks_native_source_and_missing_art_before_emission(self):
        document = portraits.load_portrait_manifest()
        image = Image.new("RGBA", (64, 64), (255, 0, 0, 255))
        source = portraits.image_to_portrait_tim(image)
        source_hash = hashlib.sha256(source).hexdigest()
        for entry in document["assets"]:
            entry["accepted_source_sha256"] = [source_hash]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(portraits.PortraitAssetError, "Missing generated portrait"):
                portraits.prepare_portrait_assets(lambda _: source, asset_root=root)
            (root / "sources").mkdir()
            for slug in portraits.CUSTOM_PORTRAIT_IDS:
                image.save(root / "sources" / f"{slug}.png")
            compiled = portraits.prepare_portrait_assets(lambda _: source, asset_root=root)
            self.assertEqual(len(compiled), 20)
            self.assertEqual(len({item.canonical_id for item in compiled}), 20)
            self.assertTrue(all(item.data == source for item in compiled))
            corrupted = bytearray(source)
            corrupted[-1] ^= 1
            with self.assertRaisesRegex(portraits.PortraitAssetError, "Unchecked native portrait source"):
                portraits.prepare_portrait_assets(lambda _: bytes(corrupted), asset_root=root)


if __name__ == "__main__":
    unittest.main()
