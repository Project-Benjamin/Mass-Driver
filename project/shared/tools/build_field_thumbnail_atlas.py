#!/usr/bin/env python3
"""Build labeled contact sheets from the map viewer's complete field thumbnails.

This is a read-only asset-audit helper.  It does not modify game data.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_THUMBNAILS = ROOT / "work" / "xenogears-map-viewer" / "Resources" / "Thumbnails"
DEFAULT_FIELD_NAMES = (
    ROOT / "work" / "noah-decomp" / "NoahLib" / "field" / "fieldDebugger" / "fieldNames.cpp"
)
DEFAULT_OUTPUT = ROOT / "work" / "terminal_asset_scan" / "field_atlas"


def load_field_names(path: Path) -> dict[int, str]:
    pattern = re.compile(r'^\s*\{(\d+),\s*"([^"]*)"\}')
    names: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(line)
        if match:
            names[int(match.group(1))] = match.group(2).strip()
    return names


def fit_label(text: str, limit: int = 24) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def make_page(
    field_ids: list[int],
    names: dict[int, str],
    thumbnails: Path,
    *,
    columns: int,
    tile_size: int,
) -> Image.Image:
    rows = (len(field_ids) + columns - 1) // columns
    label_height = 34
    margin = 16
    gap = 8
    width = margin * 2 + columns * tile_size + (columns - 1) * gap
    height = margin * 2 + rows * (tile_size + label_height) + (rows - 1) * gap
    sheet = Image.new("RGB", (width, height), (18, 21, 27))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=14)

    for index, field_id in enumerate(field_ids):
        row, column = divmod(index, columns)
        left = margin + column * (tile_size + gap)
        top = margin + row * (tile_size + label_height + gap)
        source = thumbnails / f"LevelThumbnail_{field_id}.png"
        if source.is_file():
            with Image.open(source) as thumb:
                image = thumb.convert("RGBA")
                background = Image.new("RGBA", image.size, (8, 10, 14, 255))
                background.alpha_composite(image)
                image = background.convert("RGB").resize(
                    (tile_size, tile_size), Image.Resampling.NEAREST
                )
            sheet.paste(image, (left, top))
        else:
            draw.rectangle(
                (left, top, left + tile_size - 1, top + tile_size - 1),
                fill=(35, 38, 45),
                outline=(83, 88, 99),
            )
            draw.text((left + 8, top + 8), "missing", fill=(170, 174, 184), font=font)

        draw.text(
            (left, top + tile_size + 3),
            f"{field_id:03d}  {fit_label(names.get(field_id, 'Unknown'))}",
            fill=(232, 236, 242),
            font=font,
        )
    return sheet


def parse_ids(value: str) -> list[int]:
    ids: list[int] = []
    for part in value.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start, end = int(start_text), int(end_text)
            ids.extend(range(start, end + 1))
        else:
            ids.append(int(token))
    return ids


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--thumbnails", type=Path, default=DEFAULT_THUMBNAILS)
    parser.add_argument("--field-names", type=Path, default=DEFAULT_FIELD_NAMES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--ids", help="Comma-separated IDs and ranges; default is 1-729")
    parser.add_argument("--per-page", type=int, default=81)
    parser.add_argument("--columns", type=int, default=9)
    parser.add_argument("--tile-size", type=int, default=135)
    args = parser.parse_args()

    names = load_field_names(args.field_names)
    field_ids = parse_ids(args.ids) if args.ids else list(range(1, 730))
    args.output.mkdir(parents=True, exist_ok=True)

    for page_number, start in enumerate(range(0, len(field_ids), args.per_page), start=1):
        page_ids = field_ids[start : start + args.per_page]
        sheet = make_page(
            page_ids,
            names,
            args.thumbnails,
            columns=args.columns,
            tile_size=args.tile_size,
        )
        page_path = args.output / f"field_atlas_{page_number:02d}.png"
        sheet.save(page_path)
        print(page_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
