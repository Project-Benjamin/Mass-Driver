"""Verify the HD sidecar's identities, pixel preservation, and isolation."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from modules.definitive import portrait_pack as p


def native_tim():
    data = bytearray(4640)
    data[:20] = bytes.fromhex("10 00 00 00 09 00 00 00 0C 02 00 00 00 00 E0 01 00 01 01 00")
    data[532:544] = bytes.fromhex("0C 10 00 00 00 00 00 00 20 00 40 00")
    data[20:532] = bytes(range(256)) * 2
    data[544:] = bytes(range(256)) * 16
    return bytes(data)


class PortraitPackTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.pack = self.root / "source"
        self.pack.mkdir()
        image = Image.new("RGBA", (256, 256), (123, 54, 90, 127))
        image.save(self.pack / "portrait.webp", lossless=True)
        Image.new("RGBA", (1, 1)).save(self.pack / "blank.png")
        self.native = native_tim()
        assets = [{"id": f"portrait-{index}", "name": f"Test {index}",
                   "files": [{"filename": "blank.png" if index == 90 else "portrait.webp"}]}
                  for index in range(91)]
        self.metadata = {"scale": 4, "assets": assets}
        self.save_metadata()
        self.registry = self.root / "mapping.json"
        self.registry.write_text(json.dumps({"duckstation_version": "0.1.11515",
            "duckstation_source": "https://example.invalid/test-fixture",
            "assets": [{"id": f"portrait-{index}", "index": index, "name": "Test",
                        "canonical_id": 492 + index, "selectors": [index],
                        "tim_sha256": p.sha256(self.native), "original_url": "fixture",
                        "original_rgba_sha256": "fixture"} for index in range(91)]}))
        patcher = patch.object(p, "SOURCES", self.registry)
        patcher.start()
        self.addCleanup(patcher.stop)

    def save_metadata(self):
        (self.pack / "metadata.json").write_text(json.dumps(self.metadata))

    def export(self, name="candidate", read=None):
        return p.export_pack(self.pack, self.root / name, read or (lambda canonical: self.native))

    def test_export_preserves_pixels_and_maps_both_serials_without_installing(self):
        manifest = self.export()
        self.assertEqual(manifest["native_assets_verified"], 91)
        self.assertFalse(manifest["installed"])
        self.assertEqual(manifest["runtime_status"], "unverified_candidate")
        self.assertEqual(manifest["alias_count_per_serial"], 1, "Identical native banks should share aliases")
        original = Image.open(self.pack / "portrait.webp").convert("RGBA")
        for serial in p.SERIALS:
            base = self.root / "candidate" / serial
            converted = Image.open(base / "replacements/portrait-0.png").convert("RGBA")
            self.assertEqual(original.tobytes(), converted.tobytes())
            self.assertEqual(original.size, converted.size)
            config = (base / "config.yaml").read_text()
            self.assertIn(p.texture_name(self.native) + ": portrait-0.png", config)
            self.assertNotIn("portrait-90.png", config)
        self.assertEqual(len(manifest["files"]), 185)
        for entry in manifest["files"]:
            self.assertEqual(p.sha256((self.root / "candidate" / entry["path"]).read_bytes()), entry["sha256"])

    def test_full_upload_hash_does_not_include_tim_header_or_coordinates(self):
        name = p.texture_name(self.native)
        self.assertRegex(name, r"^texupload-P8-[0-9A-F]{16}-[0-9A-F]{16}-32x64-0-0-64x64-P0-255$")
        changed = bytearray(self.native)
        changed[12] ^= 1
        changed[536] ^= 1
        self.assertEqual(name, p.texture_name(bytes(changed)))
        changed[544] ^= 1
        self.assertNotEqual(name, p.texture_name(bytes(changed)))
        changed = bytearray(self.native)
        changed[20] ^= 1
        self.assertNotEqual(name, p.texture_name(bytes(changed)))

    def test_native_hash_mismatch_stops_before_writing(self):
        with self.assertRaisesRegex(p.PortraitPackError, "differs from audited retail"):
            self.export(read=lambda canonical: b"wrong donor")
        self.assertFalse((self.root / "candidate").exists())

    def test_pack_ids_paths_and_scale_are_validated(self):
        for change in (lambda: self.metadata["assets"].pop(),
                       lambda: self.metadata["assets"][0]["files"][0].update(filename="../outside.png"),
                       lambda: self.metadata.update(scale=2)):
            old = json.loads(json.dumps(self.metadata))
            change()
            self.save_metadata()
            with self.assertRaises(p.PortraitPackError):
                self.export()
            self.assertFalse((self.root / "candidate").exists())
            self.metadata = old

    def test_output_cannot_overlap_or_overwrite_the_source_or_existing_files(self):
        for destination in (self.pack, self.pack / "new", self.root):
            with self.assertRaises(p.PortraitPackError):
                p.export_pack(self.pack, destination, lambda canonical: self.native)
        self.export()
        before = (self.root / "candidate/manifest.json").read_bytes()
        with self.assertRaisesRegex(p.PortraitPackError, "already contains"):
            self.export()
        self.assertEqual((self.root / "candidate/manifest.json").read_bytes(), before)

    def test_wrong_dimensions_and_nontransparent_blank_are_rejected(self):
        Image.new("RGBA", (64, 64)).save(self.pack / "portrait.webp", lossless=True)
        with self.assertRaisesRegex(p.PortraitPackError, "256x256"):
            self.export()
        Image.new("RGBA", (256, 256)).save(self.pack / "portrait.webp", lossless=True)
        Image.new("RGBA", (1, 1), (1, 1, 1, 255)).save(self.pack / "blank.png")
        with self.assertRaisesRegex(p.PortraitPackError, "must remain transparent"):
            self.export()

    def test_identical_native_texture_with_conflicting_hd_images_is_rejected(self):
        Image.new("RGBA", (256, 256), (255, 10, 20, 255)).save(self.pack / "other.png")
        self.metadata["assets"][1]["files"][0]["filename"] = "other.png"
        self.save_metadata()
        with self.assertRaisesRegex(p.PortraitPackError, "Conflicting HD"):
            self.export()
        self.assertFalse((self.root / "candidate").exists())


if __name__ == "__main__":
    unittest.main()
