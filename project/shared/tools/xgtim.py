#!/usr/bin/env python3
"""Convert still images to Xenogears-compatible full-screen 16-bit TIM files.

The Zeboim video player uses ordinary PlayStation direct-colour TIM images:
320x224 pixels, five bits per colour channel, and the STP bit clear.  This
module deliberately emits the same fixed image-block header used by the
retail full-screen frames.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import struct
from typing import Sequence

from PIL import Image, ImageOps


TIM_WIDTH = 320
TIM_HEIGHT = 224
TIM_PIXEL_BYTES = TIM_WIDTH * TIM_HEIGHT * 2
TIM_IMAGE_BLOCK_SIZE = 12 + TIM_PIXEL_BYTES
TIM_TOTAL_SIZE = 8 + TIM_IMAGE_BLOCK_SIZE

# TIM magic, 16-bit direct-colour flags, then the retail full-screen image
# block: byte length, VRAM x/y, and width/height in 16-bit pixels.
TIM_HEADER = bytes.fromhex(
    "10 00 00 00 02 00 00 00 0C 30 02 00 80 02 00 00 40 01 E0 00"
)


def _opaque_rgb(image: Image.Image) -> Image.Image:
    """Apply orientation and flatten any transparency onto opaque black."""

    oriented = ImageOps.exif_transpose(image)
    if oriented.mode == "RGB":
        return oriented.copy()
    if "A" in oriented.getbands() or "transparency" in oriented.info:
        foreground = oriented.convert("RGBA")
        background = Image.new("RGBA", foreground.size, (0, 0, 0, 255))
        return Image.alpha_composite(background, foreground).convert("RGB")
    return oriented.convert("RGB")


def center_crop_resize(
    image: Image.Image,
    size: tuple[int, int] = (TIM_WIDTH, TIM_HEIGHT),
) -> Image.Image:
    """Return an undistorted, centred crop resized with Lanczos filtering."""

    width, height = size
    if width <= 0 or height <= 0:
        raise ValueError(f"output dimensions must be positive, got {size!r}")
    rgb = _opaque_rgb(image)
    return ImageOps.fit(
        rgb,
        (width, height),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def encode_rgb555(image: Image.Image) -> bytes:
    """Encode one exact-size RGB image as little-endian PS1 BGR555 pixels.

    PlayStation direct-colour words put red in bits 0..4, green in 5..9,
    blue in 10..14, and STP in bit 15.  Xenogears' retail full-screen stills
    keep STP clear, so the generated images do the same.
    """

    expected = (TIM_WIDTH, TIM_HEIGHT)
    if image.size != expected:
        raise ValueError(f"RGB555 image must be {expected[0]}x{expected[1]}, got {image.size}")
    if image.mode != "RGB":
        raise ValueError(f"RGB555 image must use RGB mode, got {image.mode!r}")

    source = image.tobytes()
    encoded = bytearray(TIM_PIXEL_BYTES)
    destination = 0
    for source_offset in range(0, len(source), 3):
        red = source[source_offset] >> 3
        green = source[source_offset + 1] >> 3
        blue = source[source_offset + 2] >> 3
        word = red | (green << 5) | (blue << 10)
        struct.pack_into("<H", encoded, destination, word)
        destination += 2
    return bytes(encoded)


def validate_tim(data: bytes | bytearray | memoryview) -> None:
    """Raise ``ValueError`` unless *data* is the required full-screen TIM."""

    payload = bytes(data)
    if len(payload) != TIM_TOTAL_SIZE:
        raise ValueError(f"TIM must be {TIM_TOTAL_SIZE} bytes, got {len(payload)}")
    if payload[: len(TIM_HEADER)] != TIM_HEADER:
        raise ValueError("TIM does not have the retail 320x224 direct-colour header")

    magic, flags = struct.unpack_from("<II", payload, 0)
    block_size, vram_x, vram_y, width, height = struct.unpack_from("<IHHHH", payload, 8)
    if magic != 0x10 or flags != 0x02:
        raise ValueError(f"unexpected TIM magic/flags: {magic:#x}/{flags:#x}")
    if block_size != TIM_IMAGE_BLOCK_SIZE:
        raise ValueError(
            f"TIM image block must be {TIM_IMAGE_BLOCK_SIZE} bytes, got {block_size}"
        )
    if (vram_x, vram_y, width, height) != (640, 0, TIM_WIDTH, TIM_HEIGHT):
        raise ValueError(
            "TIM image rectangle must be VRAM (640,0) with dimensions "
            f"{TIM_WIDTH}x{TIM_HEIGHT}"
        )


def image_to_tim(image: Image.Image) -> bytes:
    """Centre-crop and encode a Pillow image as a retail-compatible TIM."""

    prepared = center_crop_resize(image)
    result = TIM_HEADER + encode_rgb555(prepared)
    validate_tim(result)
    return result


def convert_png_to_bytes(source: Path | str) -> bytes:
    """Read one PNG and return its deterministic full-screen TIM payload."""

    source_path = Path(source)
    with Image.open(source_path) as image:
        if image.format != "PNG":
            raise ValueError(f"input is not a PNG image: {source_path}")
        return image_to_tim(image)


def convert_png(source: Path | str, destination: Path | str) -> Path:
    """Convert one PNG and return the written TIM path."""

    source_path = Path(source)
    destination_path = Path(destination)
    result = convert_png_to_bytes(source_path)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_bytes(result)
    return destination_path


def convert_pngs(
    sources: Sequence[Path | str],
    output_directory: Path | str,
) -> tuple[Path, ...]:
    """Convert PNGs in caller-supplied order, retaining each source stem."""

    if not sources:
        raise ValueError("at least one input PNG is required")
    output_root = Path(output_directory)
    destinations = tuple(output_root / f"{Path(source).stem}.tim" for source in sources)
    folded_names = [path.name.casefold() for path in destinations]
    if len(set(folded_names)) != len(folded_names):
        raise ValueError("input PNG names would overwrite the same output TIM")
    return tuple(
        convert_png(source, destination)
        for source, destination in zip(sources, destinations, strict=True)
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert ordered PNG stills to Xenogears 320x224 direct-colour TIM files."
        )
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="PNG files in playback order")
    parser.add_argument(
        "-o",
        "--output-directory",
        required=True,
        type=Path,
        help="directory receiving same-stem .tim files",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    for path in convert_pngs(args.inputs, args.output_directory):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
