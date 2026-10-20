#!/usr/bin/env python3
"""Render authentic Xenogears field-model parts to labelled PNG sheets.

The renderer deliberately reuses the geometry, texture, palette, and node
decoders in the checked-in ``xenogears-map-viewer`` source.  It loads only
those pure decoding functions through ``ast`` so the inventory does not need
the viewer's optional pygame/PyOpenGL runtime.  NumPy and Pillow provide a
small orthographic software rasterizer suitable for visual asset audits.
"""

from __future__ import annotations

import argparse
import array
import ast
from dataclasses import dataclass
import math
from pathlib import Path
import struct
import sys
from typing import Iterable, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared.tools.xgdisc import (  # noqa: E402
    FIELD_DIRECTORY,
    FIRST_FIELD_LOCAL_FILE,
    Mode2Image,
    directory_file_fat_index,
)
from shared.tools.xgfield import parse_field  # noqa: E402


@dataclass(frozen=True)
class DiscField:
    scene: int
    disc: int
    fat_index: int
    model: dict[str, object]
    nodes: list[tuple[int, int, tuple[int, int, int], tuple[int, int, int]]]


@dataclass(frozen=True)
class PartAudit:
    scene: int
    disc: int
    fat_index: int
    part: int
    primitive_count: int
    span: tuple[int, int, int]
    node_ids: tuple[int, ...]


def _viewer_decoders() -> dict[str, object]:
    source_path = (
        PROJECT_ROOT / "work" / "xenogears-map-viewer" / "xgl.py"
    )
    source = source_path.read_text(encoding="utf-8")
    module = ast.parse(source)
    wanted = {
        "ShaderBuilder",
        "loadModel",
        "getColour",
        "loadTextures",
        "getNodes",
    }
    body = [
        node
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        and node.name in wanted
    ]
    namespace: dict[str, object] = {
        "array": array,
        "struct": struct,
        "abe_alpha": [128, 0, 0, 64],
    }
    exec(compile(ast.Module(body=body, type_ignores=[]), source_path, "exec"), namespace)
    return namespace


class RetailFields:
    def __init__(self, disc1: Path, disc2: Path) -> None:
        self._decoder = _viewer_decoders()
        self._discs = []
        for number, path in ((1, disc1), (2, disc2)):
            image = Mode2Image(path)
            self._discs.append(
                (
                    number,
                    image,
                    image.read_index(),
                    image.read_directories()[FIELD_DIRECTORY].first_file,
                )
            )
        self._cache: dict[int, DiscField] = {}

    def load(self, scene: int) -> DiscField:
        cached = self._cache.get(scene)
        if cached is not None:
            return cached

        live = []
        for disc, image, entries, first_file in self._discs:
            bundle_index = directory_file_fat_index(
                first_file, FIRST_FIELD_LOCAL_FILE + 2 * scene
            )
            bundle_entry = entries[bundle_index]
            graphics_entry = entries[bundle_index + 1]
            if bundle_entry.size > 24 and graphics_entry.size > 24:
                live.append(
                    (
                        disc,
                        image,
                        bundle_entry,
                        graphics_entry,
                        bundle_index,
                    )
                )
        if not live:
            raise ValueError(f"field {scene} has no live retail pair")

        preferred_disc = 1 if scene < 612 else 2
        selected = next((item for item in live if item[0] == preferred_disc), live[0])
        disc, image, bundle_entry, graphics_entry, bundle_index = selected
        bundle = image.extract_entry(bundle_entry)
        graphics = image.extract_entry(graphics_entry)
        parsed = parse_field(bundle)
        model = self._decoder["loadModel"](parsed.parts[2].data)
        model["textures"] = self._decoder["loadTextures"](
            graphics, model["shaders"]
        )
        result = DiscField(
            scene=scene,
            disc=disc,
            fat_index=bundle_index,
            model=model,
            nodes=self._decoder["getNodes"](bundle),
        )
        self._cache[scene] = result
        return result


def _part_primitives(field: DiscField, parts: Iterable[int]):
    for part_index in parts:
        part = field.model["parts"][part_index]
        for block in part["blocks"]:
            for kind, vertex_count in (
                ("tri_tex", 3),
                ("quad_tex", 4),
                ("tri_mono", 3),
                ("quad_mono", 4),
            ):
                textured = kind.endswith("tex")
                for shader, polygon in block[kind]:
                    triangles = ((0, 1, 2),) if vertex_count == 3 else (
                        (0, 1, 2),
                        (0, 2, 3),
                    )
                    for indices in triangles:
                        yield (
                            np.array(
                                [polygon[index][0] for index in indices],
                                dtype=np.float64,
                            ),
                            np.array(
                                [polygon[index][2] for index in indices],
                                dtype=np.float64,
                            ),
                            textured,
                            shader,
                        )


def audit_part(field: DiscField, part: int) -> PartAudit | None:
    primitives = list(_part_primitives(field, (part,)))
    if not primitives:
        return None
    vertices = np.concatenate([primitive[0] for primitive in primitives], axis=0)
    span_array = vertices.max(axis=0) - vertices.min(axis=0)
    return PartAudit(
        scene=field.scene,
        disc=field.disc,
        fat_index=field.fat_index,
        part=part,
        primitive_count=len(primitives),
        span=tuple(int(value) for value in span_array),
        node_ids=tuple(
            index for index, node in enumerate(field.nodes) if node[1] == part
        ),
    )


def render_parts(
    field: DiscField,
    parts: Sequence[int],
    *,
    size: int = 300,
    yaw_degrees: float = 35.0,
    pitch_degrees: float = 22.0,
) -> Image.Image:
    primitives = list(_part_primitives(field, parts))
    if not primitives:
        raise ValueError("selected model parts contain no primitives")

    all_vertices = np.concatenate([primitive[0] for primitive in primitives], axis=0)
    center = (all_vertices.min(axis=0) + all_vertices.max(axis=0)) / 2
    yaw = math.radians(yaw_degrees)
    pitch = math.radians(pitch_degrees)

    def project(vertices: np.ndarray) -> np.ndarray:
        points = vertices - center
        x = points[:, 0]
        y = -points[:, 1]
        z = points[:, 2]
        screen_x = x * math.cos(yaw) - z * math.sin(yaw)
        depth = x * math.sin(yaw) + z * math.cos(yaw)
        screen_y = y * math.cos(pitch) - depth * math.sin(pitch)
        final_depth = y * math.sin(pitch) + depth * math.cos(pitch)
        return np.stack((screen_x, screen_y, final_depth), axis=1)

    projected = project(all_vertices)
    minimum = projected[:, :2].min(axis=0)
    maximum = projected[:, :2].max(axis=0)
    span = np.maximum(maximum - minimum, 1)
    margin = 22
    scale = min((size - 2 * margin) / span[0], (size - 2 * margin) / span[1])
    midpoint = (minimum + maximum) / 2

    canvas = np.zeros((size, size, 4), dtype=np.uint8)
    canvas[:, :, :3] = 20
    canvas[:, :, 3] = 255
    depth_buffer = np.full((size, size), -np.inf, dtype=np.float64)

    for vertices, attributes, textured, shader in primitives:
        points = project(vertices)
        xy = (points[:, :2] - midpoint) * scale + size / 2
        xy[:, 1] = size - xy[:, 1]
        x_min = max(0, int(math.floor(xy[:, 0].min())))
        x_max = min(size - 1, int(math.ceil(xy[:, 0].max())))
        y_min = max(0, int(math.floor(xy[:, 1].min())))
        y_max = min(size - 1, int(math.ceil(xy[:, 1].max())))
        if x_max < x_min or y_max < y_min:
            continue

        x0, y0 = xy[0]
        x1, y1 = xy[1]
        x2, y2 = xy[2]
        denominator = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(denominator) < 1e-8:
            continue
        yy, xx = np.mgrid[y_min : y_max + 1, x_min : x_max + 1]
        weight0 = (
            (y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)
        ) / denominator
        weight1 = (
            (y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)
        ) / denominator
        weight2 = 1 - weight0 - weight1
        mask = (weight0 >= -1e-6) & (weight1 >= -1e-6) & (weight2 >= -1e-6)
        depth = (
            weight0 * points[0, 2]
            + weight1 * points[1, 2]
            + weight2 * points[2, 2]
        )
        depth_region = depth_buffer[y_min : y_max + 1, x_min : x_max + 1]
        mask &= depth >= depth_region - 1e-7
        if not mask.any():
            continue

        if textured:
            texture_data = field.model["textures"][shader]
            if texture_data is None:
                continue
            # getColour stores RRGGBBAA in an integer.  Its native little-endian
            # byte representation is ABGR, so reverse it for Pillow-style RGBA.
            texture = np.frombuffer(texture_data, dtype=np.uint8).reshape(
                256, 256, 4
            )[:, :, [3, 2, 1, 0]]
            uv = (
                weight0[..., None] * attributes[0]
                + weight1[..., None] * attributes[1]
                + weight2[..., None] * attributes[2]
            )
            u = np.clip(np.floor(uv[..., 0]).astype(int), 0, 255)
            v = np.clip(np.floor(uv[..., 1]).astype(int), 0, 255)
            colour = texture[v, u]
        else:
            colour = np.clip(
                weight0[..., None] * attributes[0]
                + weight1[..., None] * attributes[1]
                + weight2[..., None] * attributes[2],
                0,
                255,
            ).astype(np.uint8)

        mask &= colour[..., 3] > 0
        if not mask.any():
            continue
        region = canvas[y_min : y_max + 1, x_min : x_max + 1]
        alpha = colour[..., 3:4].astype(np.float32) / 255
        blended = (
            colour[..., :3] * alpha + region[..., :3] * (1 - alpha)
        ).astype(np.uint8)
        region[mask, :3] = blended[mask]
        region[mask, 3] = 255
        depth_region[mask] = depth[mask]

    return Image.fromarray(canvas, "RGBA")


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = Path(r"C:\Windows\Fonts\arial.ttf")
    return ImageFont.truetype(path, size) if path.is_file() else ImageFont.load_default()


def write_sheets(
    fields: RetailFields,
    scenes: Sequence[int],
    output: Path,
    *,
    max_span: int,
    minimum_primitives: int,
) -> list[Path]:
    candidates: list[tuple[DiscField, PartAudit]] = []
    for scene in scenes:
        field = fields.load(scene)
        referenced = sorted({node[1] for node in field.nodes if node[0] != 480})
        for part in referenced:
            audit = audit_part(field, part)
            if audit is None:
                continue
            if audit.primitive_count < minimum_primitives:
                continue
            if max(audit.span) > max_span:
                continue
            candidates.append((field, audit))

    output.mkdir(parents=True, exist_ok=True)
    columns = 4
    rows = 5
    tile_width = 360
    tile_height = 390
    per_page = columns * rows
    title_font = _font(16)
    detail_font = _font(13)
    written = []
    for page_index in range(math.ceil(len(candidates) / per_page)):
        page = candidates[page_index * per_page : (page_index + 1) * per_page]
        sheet = Image.new(
            "RGB", (columns * tile_width, rows * tile_height), (10, 12, 15)
        )
        draw = ImageDraw.Draw(sheet)
        for index, (field, audit) in enumerate(page):
            image = render_parts(field, (audit.part,), size=320).convert("RGB")
            x = (index % columns) * tile_width + 20
            y = (index // columns) * tile_height + 8
            sheet.paste(image, (x, y))
            draw.text(
                (x, y + 324),
                f"Field {audit.scene} · model {audit.part} · retail CD{audit.disc}",
                font=title_font,
                fill=(225, 235, 245),
            )
            draw.text(
                (x, y + 348),
                f"nodes {','.join(map(str, audit.node_ids)) or '-'} · "
                f"span {audit.span} · {audit.primitive_count} triangles",
                font=detail_font,
                fill=(120, 205, 255),
            )
            draw.text(
                (x, y + 368),
                f"physical FAT {audit.fat_index}/{audit.fat_index + 1}",
                font=detail_font,
                fill=(150, 155, 165),
            )
        path = output / f"field_props_{page_index + 1:02d}.png"
        sheet.save(path, optimize=True)
        written.append(path)
    return written


def _parse_int(value: str) -> int:
    return int(value, 0)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disc1", type=Path, required=True)
    parser.add_argument("--disc2", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fields", type=_parse_int, nargs="+", required=True)
    parser.add_argument("--max-span", type=int, default=800)
    parser.add_argument("--minimum-primitives", type=int, default=4)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    fields = RetailFields(args.disc1, args.disc2)
    paths = write_sheets(
        fields,
        args.fields,
        args.output,
        max_span=args.max_span,
        minimum_primitives=args.minimum_primitives,
    )
    for path in paths:
        print(path.resolve())
    print(f"Rendered {len(paths)} labelled contact-sheet page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
