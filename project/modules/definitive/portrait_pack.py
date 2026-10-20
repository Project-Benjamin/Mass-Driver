"""Export the supplied HD portraits as an uninstalled DuckStation candidate.

Every native bank is pinned to an original image independently compared with
both retail discs. The export only converts decoded RGBA from WEBP to PNG;
it does not resample, retouch, or replace any native disc resource.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from typing import Callable

from PIL import Image
import xxhash

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACK = ROOT / "assets" / "definitive" / "portraits"
SOURCES = Path(__file__).resolve().parent / "content" / "portrait_sources.json"
SERIALS = ("SLUS-00664", "SLUS-00669")


class PortraitPackError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def texture_name(native: bytes) -> str:
    """Name one full native P8 upload for DuckStation 0.1.11515.

    Palette words are little endian, 256 entries at offset 20; indices are
    64x64 bytes at offset 544. The VRAM upload width is 32 sixteen-bit words.
    Full palettes avoid assumptions about reduced-palette configuration.
    """
    if (len(native) != 4640 or native[:8] != bytes.fromhex("10 00 00 00 09 00 00 00")
            or native[16:20] != bytes.fromhex("00 01 01 00")
            or native[540:544] != bytes.fromhex("20 00 40 00")):
        raise PortraitPackError("Expected a native 64x64 P8 TIM portrait")
    pixels = xxhash.xxh3_64_hexdigest(native[544:]).upper()
    palette = xxhash.xxh3_64_hexdigest(native[20:532]).upper()
    return f"texupload-P8-{pixels}-{palette}-32x64-0-0-64x64-P0-255"


def _lossless_png(path: Path) -> tuple[bytes, dict]:
    encoded_source = path.read_bytes()
    with Image.open(io.BytesIO(encoded_source)) as image:
        rgba = image.convert("RGBA")
        source = rgba.tobytes()
        buffer = io.BytesIO()
        rgba.save(buffer, format="PNG")
        encoded = buffer.getvalue()
        with Image.open(io.BytesIO(encoded)) as check:
            if check.size != rgba.size or check.convert("RGBA").tobytes() != source:
                raise PortraitPackError(f"PNG conversion changed decoded pixels: {path.name}")
        return encoded, {"width": rgba.width, "height": rgba.height,
                         "source_sha256": sha256(encoded_source),
                         "rgba_sha256": sha256(source),
                         "fully_transparent": rgba.getchannel("A").getextrema()[1] == 0}


def export_pack(path: Path | str, output: Path | str,
                read_disc: Callable[[int], bytes]) -> dict:
    """Validate all 91 mappings, then create both serial folders and a manifest.

    ``read_disc`` takes canonical resource IDs (492..582) from one checked
    retail disc. ``output`` is a new standalone texture-pack directory, never
    the user's emulator data directory. The result remains runtime-untested.
    """
    pack = Path(path).resolve()
    destination = Path(output).resolve()
    if destination == pack or destination.is_relative_to(pack) or pack.is_relative_to(destination):
        raise PortraitPackError("Texture output must be separate from the source pack")
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise PortraitPackError(f"Texture output already contains files: {destination}")
    metadata_path = pack / "metadata.json"
    metadata_bytes = metadata_path.read_bytes()
    metadata = json.loads(metadata_bytes)
    sources_bytes = SOURCES.read_bytes()
    sources = json.loads(sources_bytes)
    assets = metadata.get("assets", [])
    ids = [asset.get("id") for asset in assets]
    if len(ids) != 91 or set(ids) != {f"portrait-{index}" for index in range(91)}:
        raise PortraitPackError("Expected exactly portrait-0 through portrait-90")
    if metadata.get("scale") != 4:
        raise PortraitPackError("Expected the supplied 4x portrait pack")
    assets_by_id = {asset["id"]: asset for asset in assets}
    native_sources = sources.get("assets", [])
    if len(native_sources) != 91 or [entry["index"] for entry in native_sources] != list(range(91)):
        raise PortraitPackError("Original portrait mapping registry changed")
    prepared = []
    aliases = {}
    alias_pixels = {}
    # Complete validation and conversion before creating the export directory.
    for original in native_sources:
        asset = assets_by_id[original["id"]]
        files = asset.get("files", [])
        if len(files) != 1:
            raise PortraitPackError(f"Expected one image for {asset['id']}")
        filename = files[0].get("filename")
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise PortraitPackError("Portrait filename must be a direct child of the pack")
        source_path = (pack / filename).resolve()
        if not source_path.is_relative_to(pack):
            raise PortraitPackError("Portrait filename escapes source pack")
        native = read_disc(original["canonical_id"])
        if sha256(native) != original["tim_sha256"]:
            raise PortraitPackError(f"Native portrait {original['index']} differs from audited retail")
        name = texture_name(native)
        pixels, dimensions = _lossless_png(source_path)
        blank = original["index"] == 90
        if blank:
            if not dimensions["fully_transparent"]:
                raise PortraitPackError("Blank portrait 90 must remain transparent")
        elif (dimensions["width"], dimensions["height"]) != (256, 256):
            raise PortraitPackError(f"Expected 256x256 HD source: {filename}")
        png_name = f"{original['id']}.png"
        if not blank:
            if name in alias_pixels and alias_pixels[name] != dimensions["rgba_sha256"]:
                raise PortraitPackError(f"Conflicting HD images for identical native texture {asset['id']}")
            aliases.setdefault(name, png_name)
            alias_pixels[name] = dimensions["rgba_sha256"]
        record = {"id": original["id"], "name": asset.get("name", original["name"]),
                  "canonical_id": original["canonical_id"], "selectors": original["selectors"],
                  "native_tim_sha256": original["tim_sha256"],
                  "original_url": original["original_url"],
                  "original_rgba_sha256": original["original_rgba_sha256"],
                  "source_file": filename,
                  "png_file": png_name, "png_sha256": sha256(pixels), **dimensions,
                  "texture_alias": None if blank else name,
                  "status": "blank_preserved_unmapped" if blank else "candidate"}
        prepared.append((record, pixels))
    files = []
    destination.mkdir(parents=True, exist_ok=True)

    def write(relative: str, data: bytes):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
        files.append({"path": relative, "size": len(data), "sha256": sha256(data)})

    config = ("# Generated candidate for DuckStation 0.1.11515; not runtime-verified.\n"
              "# Merge aliases only after validating in an isolated emulator profile.\n"
              "Aliases:\n" + "".join(f"  {name}: {filename}\n" for name, filename in sorted(aliases.items())))
    for serial in SERIALS:
        for record, data in prepared:
            write(f"{serial}/replacements/{record['png_file']}", data)
        write(f"{serial}/config.yaml", config.encode("utf-8"))
    readme = ("Xenogears HD portrait texture-pack candidate\n\n"
              "This standalone sidecar contains the supplied portraits at their original HD dimensions. "
              "PNG conversion preserves decoded RGBA pixels exactly. No disc or emulator setting was changed.\n\n"
              "The SLUS-00664 and SLUS-00669 folders contain candidate DuckStation texture aliases for "
              "the verified retail portrait banks. These have not been validated in the emulator. "
              "Do not overwrite an existing texture config. Validate aliases in an isolated profile, "
              "then merge with any existing replacements. Enable Texture Cache and Texture Replacements "
              "for that profile as described in DuckStation's Texture Replacement wiki.\n\n"
              "Native bank identities are verified for all 91 assets; runtime upload splitting, cropping, "
              "palette changes, mirrored portraits, Disc 2 transitions, and other texture packs still "
              "need visual checks. This pack covers dialogue portraits; menu and battle portraits "
              "use separate resources. The transparent portrait 90 is preserved but not installed as an alias.\n")
    write("README.txt", readme.encode("utf-8"))
    manifest = {"format": "xenogears-definitive-hd-portrait-pack-v1", "source_pack": str(pack),
                "source_metadata_sha256": sha256(metadata_bytes),
                "mapping_registry_sha256": sha256(sources_bytes),
                "duckstation_version": sources["duckstation_version"],
                "duckstation_source": sources["duckstation_source"],
                "xxhash_version": xxhash.VERSION,
                "runtime_status": "unverified_candidate", "installed": False,
                "native_assets_verified": 91, "alias_count_per_serial": len(aliases),
                "serials": list(SERIALS), "assets": [record for record, _ in prepared],
                "files": files}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
