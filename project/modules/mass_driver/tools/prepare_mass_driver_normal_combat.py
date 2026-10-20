#!/usr/bin/env python3
"""Prepare normal Perfect Works combat resources for the standalone dungeon.

The original v24 source image was built with Perfect Works Story Mode, whose
files zero enemy durability and attack power for one-hit, no-threat battles.
This helper selects the matching non-Story-Mode resources from a legal Perfect
Works 0.10.2 package: the retranslated ``script2`` version when present,
otherwise the untouched ``og_monsters`` version.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
from typing import Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from modules.mass_driver.build import (
    NORMAL_COMBAT_CANONICAL_IDS,
    NORMAL_COMBAT_RESOURCE_AGGREGATE_SHA256,
    NORMAL_COMBAT_RESOURCE_COUNT,
    NORMAL_COMBAT_RESOURCE_TOTAL_SIZE,
    NORMAL_ENEMY_CANONICAL_IDS,
    _enemy_resource_aggregate,
)


class NormalCombatPreparationError(RuntimeError):
    """Raised when the Perfect Works normal combat set is incomplete."""


def prepare_normal_combat(
    gamefiles_root: Path | str,
    output_root: Path | str,
    *,
    force: bool = False,
) -> tuple[Path, ...]:
    gamefiles = Path(gamefiles_root).resolve()
    output = Path(output_root).resolve()
    script = gamefiles / "script2"
    original = gamefiles / "og_monsters"
    if not script.is_dir() or not original.is_dir():
        raise NormalCombatPreparationError(
            "Expected Perfect Works gamefiles/script2 and "
            "gamefiles/og_monsters directories"
        )
    if output.exists() and not output.is_dir():
        raise NormalCombatPreparationError(
            f"Output is not a directory: {output}"
        )
    if output.is_dir() and any(output.iterdir()) and not force:
        raise NormalCombatPreparationError(
            f"Output is not empty: {output}; pass --force"
        )

    selected: list[tuple[int, Path, bytes, str]] = []
    for canonical_id in NORMAL_COMBAT_CANONICAL_IDS:
        translated = script / (
            f"{canonical_id:04d}" if canonical_id < 1000 else str(canonical_id)
        )
        retail = original / str(canonical_id)
        source = translated if translated.is_file() else retail
        provenance = "script2" if source == translated else "og_monsters"
        if not source.is_file():
            raise NormalCombatPreparationError(
                f"Normal combat resource {canonical_id} is missing from "
                "both script2 and og_monsters"
            )
        selected.append(
            (canonical_id, source, source.read_bytes(), provenance)
        )

    resources = [(canonical_id, data) for canonical_id, _, data, _ in selected]
    total_size = sum(len(data) for _, data in resources)
    aggregate = _enemy_resource_aggregate(resources)
    if len(resources) != NORMAL_COMBAT_RESOURCE_COUNT:
        raise NormalCombatPreparationError(
            f"Selected {len(resources)} combat resources, expected "
            f"{NORMAL_COMBAT_RESOURCE_COUNT}"
        )
    if total_size != NORMAL_COMBAT_RESOURCE_TOTAL_SIZE:
        raise NormalCombatPreparationError(
            f"Selected combat resources total {total_size} bytes, expected "
            f"{NORMAL_COMBAT_RESOURCE_TOTAL_SIZE}"
        )
    if aggregate != NORMAL_COMBAT_RESOURCE_AGGREGATE_SHA256:
        raise NormalCombatPreparationError(
            f"Normal combat resource aggregate hash mismatch: {aggregate}"
        )

    output.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    manifest_resources: list[dict[str, object]] = []
    for canonical_id, source, data, provenance in selected:
        destination = output / f"{canonical_id}.bin"
        shutil.copyfile(source, destination)
        written.append(destination)
        manifest_resources.append(
            {
                "canonical_id": canonical_id,
                "provenance": provenance,
                "size": len(data),
            }
        )
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "format": "xenogears-normal-combat-resources-v1",
                "source": "Perfect Works 0.10.2 without Story Mode",
                "resource_count": len(resources),
                "enemy_resource_count": len(NORMAL_ENEMY_CANONICAL_IDS),
                "total_size": total_size,
                "aggregate_sha256": aggregate,
                "resources": manifest_resources,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return tuple(written)


def build_parser() -> argparse.ArgumentParser:
    project = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--perfect-works-gamefiles",
        type=Path,
        required=True,
        help="Path to the Perfect Works 0.10.2 gamefiles directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=project / "work" / "normal_combat_resources",
    )
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        written = prepare_normal_combat(
            args.perfect_works_gamefiles,
            args.output,
            force=args.force,
        )
        print(
            f"Wrote {len(written)} normal combat resources to "
            f"{Path(args.output).resolve()}"
        )
        print(
            "Aggregate SHA-256 "
            f"{NORMAL_COMBAT_RESOURCE_AGGREGATE_SHA256}"
        )
        return 0
    except (NormalCombatPreparationError, OSError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
