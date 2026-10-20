from __future__ import annotations

from contextlib import redirect_stdout
import io
from pathlib import Path
import struct
import tempfile
import unittest

from PIL import Image

from tools.xgtim import (
    TIM_HEADER,
    TIM_HEIGHT,
    TIM_IMAGE_BLOCK_SIZE,
    TIM_TOTAL_SIZE,
    TIM_WIDTH,
    center_crop_resize,
    convert_png,
    encode_rgb555,
    image_to_tim,
    main,
    validate_tim,
)


class XenogearsTimTests(unittest.TestCase):
    def test_retail_header_and_dimensions_are_exact(self) -> None:
        self.assertEqual(
            TIM_HEADER,
            bytes.fromhex(
                "10 00 00 00 02 00 00 00 0C 30 02 00 "
                "80 02 00 00 40 01 E0 00"
            ),
        )
        self.assertEqual(TIM_IMAGE_BLOCK_SIZE, 143_372)
        self.assertEqual(TIM_TOTAL_SIZE, 143_380)
        image = Image.new("RGB", (TIM_WIDTH, TIM_HEIGHT), (17, 34, 51))
        data = image_to_tim(image)
        self.assertEqual(len(data), 143_380)
        self.assertEqual(data[:20], TIM_HEADER)
        validate_tim(data)

    def test_rgb555_channel_order_is_little_endian_and_stp_clear(self) -> None:
        image = Image.new("RGB", (TIM_WIDTH, TIM_HEIGHT), (0, 0, 0))
        image.putpixel((0, 0), (255, 0, 0))
        image.putpixel((1, 0), (0, 255, 0))
        image.putpixel((2, 0), (0, 0, 255))
        image.putpixel((3, 0), (255, 255, 255))
        encoded = encode_rgb555(image)
        self.assertEqual(struct.unpack_from("<4H", encoded), (0x001F, 0x03E0, 0x7C00, 0x7FFF))
        words = struct.unpack(f"<{TIM_WIDTH * TIM_HEIGHT}H", encoded)
        self.assertTrue(all(word & 0x8000 == 0 for word in words))

    def test_center_crop_preserves_aspect_without_stretching(self) -> None:
        image = Image.new("RGB", (400, TIM_HEIGHT), (0, 255, 0))
        for x in range(40):
            for y in range(TIM_HEIGHT):
                image.putpixel((x, y), (255, 0, 0))
                image.putpixel((399 - x, y), (0, 0, 255))
        result = center_crop_resize(image)
        self.assertEqual(result.size, (TIM_WIDTH, TIM_HEIGHT))
        self.assertEqual(result.getbbox(), (0, 0, TIM_WIDTH, TIM_HEIGHT))
        self.assertEqual(result.tobytes(), bytes((0, 255, 0)) * (TIM_WIDTH * TIM_HEIGHT))

    def test_alpha_is_flattened_to_an_opaque_black_background(self) -> None:
        image = Image.new("RGBA", (TIM_WIDTH, TIM_HEIGHT), (255, 0, 0, 0))
        image.putpixel((TIM_WIDTH // 2, TIM_HEIGHT // 2), (255, 0, 0, 255))
        result = center_crop_resize(image)
        self.assertEqual(result.mode, "RGB")
        self.assertEqual(result.getpixel((0, 0)), (0, 0, 0))
        self.assertEqual(result.getpixel((TIM_WIDTH // 2, TIM_HEIGHT // 2)), (255, 0, 0))

    def test_encoder_rejects_wrong_dimensions_or_mode(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be 320x224"):
            encode_rgb555(Image.new("RGB", (319, TIM_HEIGHT)))
        with self.assertRaisesRegex(ValueError, "must use RGB mode"):
            encode_rgb555(Image.new("RGBA", (TIM_WIDTH, TIM_HEIGHT)))

    def test_validation_rejects_size_and_header_changes(self) -> None:
        data = bytearray(image_to_tim(Image.new("RGB", (TIM_WIDTH, TIM_HEIGHT))))
        with self.assertRaisesRegex(ValueError, "must be 143380 bytes"):
            validate_tim(data[:-1])
        data[12] ^= 1
        with self.assertRaisesRegex(ValueError, "retail 320x224"):
            validate_tim(data)

    def test_png_conversion_and_cli_preserve_input_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "1.png"
            second = root / "2.png"
            Image.new("RGB", (640, 448), (248, 0, 0)).save(first)
            Image.new("RGB", (640, 448), (0, 248, 0)).save(second)
            output = root / "tim"

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main([str(second), str(first), "-o", str(output)])
            self.assertEqual(result, 0)
            self.assertEqual(
                stdout.getvalue().splitlines(),
                [str(output / "2.tim"), str(output / "1.tim")],
            )
            second_data = (output / "2.tim").read_bytes()
            first_data = (output / "1.tim").read_bytes()
            validate_tim(second_data)
            validate_tim(first_data)
            self.assertEqual(struct.unpack_from("<H", second_data, 20)[0], 0x03E0)
            self.assertEqual(struct.unpack_from("<H", first_data, 20)[0], 0x001F)

    def test_non_png_input_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "renamed.png"
            Image.new("RGB", (TIM_WIDTH, TIM_HEIGHT)).save(source, format="BMP")
            with self.assertRaisesRegex(ValueError, "not a PNG"):
                convert_png(source, root / "result.tim")


if __name__ == "__main__":
    unittest.main()
