"""Compile Rico's custom speaker portraits into checked native TIM resources.

Dialogue portraits are separate from the 48x48 main-menu portrait sheet.
FE 0D selects a native portrait ID; the engine maps that ID to a standalone
64x64, 8-bpp TIM and loads it on demand into one of three cached VRAM slots.
The reserved IDs below are unused by current Mass Driver/Soylent portrait
instructions and avoid retained Rico donor portrait IDs. They replace native
alternate portraits in the anthology image; they are not additional engine
table entries. See content/assets/dialogue_portraits/manifest.json.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct
from typing import Callable, Mapping

from PIL import Image, ImageChops, ImageDraw, ImageOps


ASSET_ROOT = Path(__file__).resolve().parent / "content" / "assets" / "dialogue_portraits"
MANIFEST_PATH = ASSET_ROOT / "manifest.json"
PORTRAIT_SIZE = (64, 64)
PORTRAIT_TIM_SIZE = 4640
PORTRAIT_PALETTE_OFFSET = 20
PORTRAIT_IMAGE_OFFSET = 544
PORTRAIT_CLUT_HEADER = bytes.fromhex("10 00 00 00 09 00 00 00 0C 02 00 00 00 00 E0 01 00 01 01 00")
PORTRAIT_IMAGE_HEADER = bytes.fromhex("0C 10 00 00 00 00 00 00 20 00 40 00")

# These are portrait selectors, not the unrelated 0F 05 name-insertion IDs.
NATIVE_PORTRAIT_IDS: Mapping[str, int] = {
    "Fei": 0,
    "Elly": 1,
    "Citan": 2,
    "Bart": 3,
    "Billy": 4,
    "Rico": 5,
    "Emeralda": 6,
    "Hammer": 46,
    "Sigmund": 76,
}

CUSTOM_PORTRAIT_IDS: Mapping[str, int] = {
    "young_rico": 32,
    "anne": 33,
    "ethos_priest": 34,
    "suzarn": 37,
    "rue": 38,
    "leonardo": 40,
    "gramps": 41,
    "guard": 42,
    "infirmary_attendant": 43,
    "worker": 45,
    "prisoner": 47,
    "battler": 48,
    "arena_official": 50,
    "clerk": 51,
    "adjutant": 52,
    "archivist": 53,
    "security_captain": 54,
    "demi_human_worker": 55,
    "old_prisoner": 56,
    "latina": 59,
}


class PortraitAssetError(ValueError):
    """An asset, reserved slot, or native source failed its contract."""


@dataclass(frozen=True)
class PortraitAssetReplacement:
    canonical_id: int
    portrait_id: int
    slug: str
    source_sha256: str
    png_sha256: str
    data: bytes

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()


def validate_portrait_tim(data: bytes, *, require_native_coordinates: bool = True) -> None:
    """Accept exactly the native 64x64 indexed portrait container."""

    if len(data) != PORTRAIT_TIM_SIZE:
        raise PortraitAssetError(f"Portrait TIM must be {PORTRAIT_TIM_SIZE} bytes")
    if data[:12] != PORTRAIT_CLUT_HEADER[:12] or data[16:20] != PORTRAIT_CLUT_HEADER[16:20]:
        raise PortraitAssetError("Portrait TIM lost its native CLUT header")
    if data[532:536] != PORTRAIT_IMAGE_HEADER[:4] or data[540:544] != PORTRAIT_IMAGE_HEADER[8:]:
        raise PortraitAssetError("Portrait TIM lost its native 64x64 image header")
    if require_native_coordinates and (
        data[12:16] != PORTRAIT_CLUT_HEADER[12:16]
        or data[536:540] != PORTRAIT_IMAGE_HEADER[4:8]
    ):
        raise PortraitAssetError("Portrait TIM upload coordinates changed")


def _remove_border_black_matte(image: Image.Image, threshold: int) -> Image.Image:
    """Key only near-black pixels connected to the source image's border.

    Generated sources use a black matte. Flooding its connected exterior,
    before resampling, avoids a rectangular backdrop and leaves enclosed
    black eyes, hair details, and linework opaque. Existing alpha survives.
    """

    if isinstance(threshold, bool) or not isinstance(threshold, int) or not 0 <= threshold <= 31:
        raise PortraitAssetError("Black matte threshold must be an integer from 0 to 31")
    red, green, blue, alpha = image.split()
    brightest = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    eligible = brightest.point(lambda value: 255 if value <= threshold else 0)
    # One eligible padding pixel joins all four exterior edges, so a single
    # flood covers separate matte regions without touching enclosed blacks.
    connected = ImageOps.expand(eligible, border=1, fill=255)
    ImageDraw.floodfill(connected, (0, 0), 128)
    connected = connected.crop((1, 1, image.width + 1, image.height + 1))
    keep = connected.point(lambda value: 0 if value == 128 else 255)
    image = image.copy()
    image.putalpha(ImageChops.multiply(alpha, keep))
    return image


def image_to_portrait_tim(
    image: Image.Image, *, border_connected_black_matte_max_channel: int | None = None,
) -> bytes:
    """Resize and quantize generated art without changing native TIM layout.

    Index 255 is reserved for transparent pixels. Other indices encode PS1
    BGR555; opaque black uses 0x8000 so it cannot become transparent word zero.
    Portrait primitives are opaque, making that word an opaque black pixel.
    """

    source = ImageOps.exif_transpose(image).convert("RGBA")
    if border_connected_black_matte_max_channel is not None:
        source = _remove_border_black_matte(source, border_connected_black_matte_max_channel)
    rgba = ImageOps.fit(
        source,
        PORTRAIT_SIZE,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    alpha = rgba.getchannel("A").tobytes()
    quantized = rgba.convert("RGB").quantize(
        colors=255,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    palette = quantized.getpalette()
    if palette is None:
        raise PortraitAssetError("Quantized portrait has no palette")
    palette = palette + [0] * max(0, 255 * 3 - len(palette))
    encoded_palette = bytearray(512)
    for index in range(255):
        red, green, blue = palette[index * 3 : index * 3 + 3]
        word = (red >> 3) | ((green >> 3) << 5) | ((blue >> 3) << 10)
        struct.pack_into("<H", encoded_palette, index * 2, word or 0x8000)
    pixels = bytes(
        color if opacity >= 128 else 255
        for color, opacity in zip(quantized.tobytes(), alpha, strict=True)
    )
    result = PORTRAIT_CLUT_HEADER + bytes(encoded_palette) + PORTRAIT_IMAGE_HEADER + pixels
    validate_portrait_tim(result)
    return result


def portrait_tim_to_image(data: bytes) -> Image.Image:
    """Decode a checked portrait for asset review and quantization checks."""

    validate_portrait_tim(data)
    palette = struct.unpack_from("<256H", data, PORTRAIT_PALETTE_OFFSET)
    colors = [
        ((word & 31) * 255 // 31,
         ((word >> 5) & 31) * 255 // 31,
         ((word >> 10) & 31) * 255 // 31,
         0 if word == 0 else 255)
        for word in palette
    ]
    result = Image.new("RGBA", PORTRAIT_SIZE)
    result.putdata([colors[index] for index in data[PORTRAIT_IMAGE_OFFSET:]])
    return result


def load_portrait_manifest(path: Path = MANIFEST_PATH) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("format") != "rico-dialogue-portraits-v1":
        raise PortraitAssetError("Unrecognized Rico portrait manifest")
    assets = document.get("assets", [])
    expected = dict(CUSTOM_PORTRAIT_IDS)
    actual = {entry["slug"]: entry["portrait_id"] for entry in assets}
    if actual != expected or len(assets) != len(expected):
        raise PortraitAssetError("Reserved custom portrait inventory changed")
    canonical_ids = [entry["canonical_id"] for entry in assets]
    if len(set(canonical_ids)) != len(canonical_ids):
        raise PortraitAssetError("Custom portrait assets share a canonical resource")
    for entry in assets:
        if entry["canonical_id"] != 492 + entry["native_asset_index"]:
            raise PortraitAssetError("Portrait canonical/native asset mapping changed")
        if entry["portrait_id"] in NATIVE_PORTRAIT_IDS.values():
            raise PortraitAssetError("Custom portrait overlaps an active named portrait")
    return document


def prepare_portrait_assets(
    canonical_reader: Callable[[int], bytes],
    *,
    asset_root: Path = ASSET_ROOT,
) -> tuple[PortraitAssetReplacement, ...]:
    """Return nineteen verified replacements; the caller owns disc emission.

    Rico canonical IDs map directly to Disc 1 FAT indices. For Disc 2 the
    existing cd2fix/DiscReader contract subtracts five from that same ID.
    This function never mutates the source disc or writes generated assets.
    """

    document = load_portrait_manifest(asset_root / "manifest.json")
    result = []
    for entry in document["assets"]:
        source = canonical_reader(entry["canonical_id"])
        # The native loader supplies its own destination. Two checked Perfect
        # Works sources carry different TIM coordinates; their full hashes in
        # the manifest remain mandatory even though those coordinates differ.
        validate_portrait_tim(source, require_native_coordinates=False)
        source_hash = hashlib.sha256(source).hexdigest()
        if source_hash not in entry["accepted_source_sha256"]:
            raise PortraitAssetError(f"Unchecked native portrait source for {entry['slug']}")
        source_path = asset_root / "sources" / f"{entry['slug']}.png"
        if not source_path.is_file():
            raise PortraitAssetError(f"Missing generated portrait: {source_path}")
        source_png = source_path.read_bytes()
        with Image.open(source_path) as image:
            if image.format != "PNG":
                raise PortraitAssetError(f"Portrait source is not PNG: {source_path}")
            data = image_to_portrait_tim(
                image,
                border_connected_black_matte_max_channel=document.get("image_encoding", {}).get(
                    "border_connected_black_matte_max_channel"
                ),
            )
        result.append(PortraitAssetReplacement(
            canonical_id=entry["canonical_id"],
            portrait_id=entry["portrait_id"],
            slug=entry["slug"],
            source_sha256=source_hash,
            png_sha256=hashlib.sha256(source_png).hexdigest(),
            data=data,
        ))
    return tuple(result)
