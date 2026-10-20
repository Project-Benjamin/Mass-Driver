#!/usr/bin/env python3
"""Materialize the dormant El-Regulus resource set outside active builds.

The Mass Driver chapter correctly keeps Elly in Vierge.  This utility preserves
the completed Gear 10 work as a reproducible, hash-checked archive without
placing any of those replacements in ``prepare_all`` or a playable image.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

try:
    from .build_mass_driver_dungeon import (
        ARCHIVED_EL_REGULUS_CANONICAL_IDS,
        prepare_archived_el_regulus_resources,
    )
except ImportError:  # Direct ``python tools/build_el_regulus_archive.py`` use.
    from build_mass_driver_dungeon import (
        ARCHIVED_EL_REGULUS_CANONICAL_IDS,
        prepare_archived_el_regulus_resources,
    )


ARCHIVE_FORMAT = "xenogears-el-regulus-future-resource-archive-v1"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _slug(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def materialize_archive(
    input_root: Path | str,
    output_root: Path | str,
    *,
    force: bool = False,
) -> Path:
    """Write the checked future resources and return their manifest path."""

    source = Path(input_root).resolve()
    output = Path(output_root).resolve()
    prepared = prepare_archived_el_regulus_resources(source)
    ids = tuple(item.bundle_id for item in prepared)
    if ids != ARCHIVED_EL_REGULUS_CANONICAL_IDS:
        raise RuntimeError(f"El-Regulus archive inventory drifted: {ids}")

    output.mkdir(parents=True, exist_ok=True)
    targets = tuple(
        output / f"{item.bundle_id:05d}_{_slug(item.label)}.bin"
        for item in prepared
    )
    manifest_path = output / "manifest.json"
    existing = [path for path in (*targets, manifest_path) if path.exists()]
    if existing and not force:
        rendered = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            f"Archive output already exists ({rendered}); pass --force to replace it"
        )

    resources: list[dict[str, object]] = []
    for item, target in zip(prepared, targets, strict=True):
        target.write_bytes(item.bundle)
        resources.append(
            {
                "canonical_id": item.bundle_id,
                "filename": target.name,
                "label": item.label,
                "size": len(item.bundle),
                "sha256": _sha256(item.bundle),
                "notes": list(item.notes),
            }
        )

    manifest = {
        "format": ARCHIVE_FORMAT,
        "name": "El-Regulus future chapter resource archive",
        "status": "dormant",
        "active_mass_driver_emitted": False,
        "gear_id": 10,
        "source_input_root": str(source),
        "resources": resources,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-root",
        default="work",
        help="Extracted/audited Mass Driver source-resource root (default: work)",
    )
    parser.add_argument(
        "--output",
        default="work/el_regulus_future_archive",
        help="Ignored local archive destination",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an archive previously generated at the destination",
    )
    args = parser.parse_args()
    manifest = materialize_archive(
        args.input_root,
        args.output,
        force=args.force,
    )
    print(f"Wrote dormant El-Regulus archive: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
