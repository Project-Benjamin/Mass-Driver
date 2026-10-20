#!/usr/bin/env python3
"""Build one Disc 2 containing every Xenogears Reimagined content module.

The output keeps Xenogears' native New Game / Continue / Sound title screen.
New Game enters a dedicated full-screen selector with Mass Driver, Surface
Soylent, a visibly disabled Mahanon card, and Rico's Arc.  Rico enters its
chapter-select hub; the authentic memory cube there can save or return to the
selector without restarting the emulator.

All source images are read-only.  Mass Driver, Surface Soylent, and Rico are
prepared independently and then composed by canonical file ID in one guarded
Xenoiso pass.  Shared system resources are merged record-by-record so neither
project silently overwrites another.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.mass_driver import build as mass_driver
from modules.rico import build as rico
from modules.rico.chapter_two_resources import WORLD_FIELDS, REDRUM_RESOURCE_IDENTITIES
from modules.rico.chapter_two_scenes import CINEMATIC_RESOURCE_IDENTITIES
from modules.soylent_system import build as surface
from shared.tools import xenoiso_build
from shared.tools import xgcontent_menu_field as content_menu
from shared.tools.xgdisc import Mode2Image
from shared.tools.xgmode2 import verify_retail_title_boot
from modules.rico.tools.xgrico_balance import (
    decode_lzss_complete_groups,
    patch_weight_mutation_overlay,
)
from shared.tools.xgunified_resources import (
    merge_initial_gamestate,
    merge_menu_archive_with_young_rico,
    merge_system_data,
    merge_system_names,
)


OUTPUT_FORMAT = "xenogears-reimagined-unified-disc2-v1"
CONTENT_MENU_FIELD = 63
CONTENT_MENU_BUNDLE_ID = 732
CONTENT_MENU_GRAPHICS_ID = 733
MASS_DRIVER_FIELD = 728
SURFACE_SOYLENT_FIELD = 623
RICO_HUB_FIELD = 229
MAHANON_STATUS = "coming soon; visible but never focusable"

SHARED_SYSTEM_NAMES_ID = 29
SHARED_BATTLE_OVERLAY_ID = 38
SHARED_TITLE_FIELD_ID = 1586
SHARED_TITLE_GRAPHICS_ID = 1587
SHARED_MENU_ID = 2593
SHARED_SYSTEM_DATA_ID = 2594
SHARED_GAMESTATE_ID = 2595
WEIGHT_OVERLAY_IDS = (2597, 2599, 2603)

# Rico's Disc 1 battle arena dependencies 47/2614 conflict with the complete
# Disc 2 normal-combat set installed by Mass Driver.  The unified image keeps
# the latter so Guardian, random, and Gear encounters retain their checked
# Disc 2 runtime.  Rico's field/battle records and non-conflicting dependency
# 2623 remain installed; this policy is surfaced in the manifest and tests.
MASS_OWNED_RICO_CONFLICT_IDS = frozenset((47, 2614))
RICO_SHARED_IDS = frozenset(
    (
        SHARED_SYSTEM_NAMES_ID,
        SHARED_BATTLE_OVERLAY_ID,
        *MASS_OWNED_RICO_CONFLICT_IDS,
        SHARED_TITLE_FIELD_ID,
        SHARED_TITLE_GRAPHICS_ID,
        SHARED_MENU_ID,
        SHARED_SYSTEM_DATA_ID,
        SHARED_GAMESTATE_ID,
        *WEIGHT_OVERLAY_IDS,
    )
)
MASS_COMPOSED_IDS = frozenset(
    (
        SHARED_SYSTEM_NAMES_ID,
        SHARED_TITLE_FIELD_ID,
        SHARED_TITLE_GRAPHICS_ID,
        SHARED_MENU_ID,
        SHARED_SYSTEM_DATA_ID,
        SHARED_GAMESTATE_ID,
        2599,
    )
)

DUMMY_PAYLOAD = b"It's CDMAKE Dummy !\r\n\r\n "
DUMMY_SHA256 = "aafefb97ceb8e4667c719b99c4250b286e03087315b61848d196300140a95a2c"
RESERVED_DUMMY_IDS = tuple(range(732, 766))
IDENTICAL_RICO_DEPENDENCIES = frozenset((2622, *REDRUM_RESOURCE_IDENTITIES, *CINEMATIC_RESOURCE_IDENTITIES))


class UnifiedBuildError(RuntimeError):
    """A module or shared-resource composition contract was violated."""


@dataclass(frozen=True)
class UnifiedReplacement:
    canonical_id: int
    role: str
    owner: str
    data: bytes

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()


def _slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return result[:72] or "resource"


def _add(
    replacements: dict[int, UnifiedReplacement],
    replacement: UnifiedReplacement,
    *,
    allow_identical: bool = False,
) -> None:
    current = replacements.get(replacement.canonical_id)
    if current is None:
        replacements[replacement.canonical_id] = replacement
        return
    if allow_identical and current.data == replacement.data:
        replacements[replacement.canonical_id] = UnifiedReplacement(
            current.canonical_id,
            f"{current.role}; {replacement.role}",
            f"{current.owner}+{replacement.owner}",
            current.data,
        )
        return
    raise UnifiedBuildError(
        f"Canonical {replacement.canonical_id} is owned by both "
        f"{current.owner} and {replacement.owner} with different data"
    )


def _mass_replacements(
    prepared: Sequence[mass_driver.PreparedReplacement],
) -> dict[int, UnifiedReplacement]:
    result: dict[int, UnifiedReplacement] = {}
    for item in prepared:
        if item.bundle_id not in MASS_COMPOSED_IDS:
            _add(
                result,
                UnifiedReplacement(item.bundle_id, item.label, "mass_driver", item.bundle),
            )
        if item.graphics_id is not None and item.graphics is not None:
            if item.graphics_id not in MASS_COMPOSED_IDS:
                _add(
                    result,
                    UnifiedReplacement(
                        item.graphics_id,
                        f"{item.label} graphics",
                        "mass_driver",
                        item.graphics,
                    ),
                )
    return result


def _mass_resource(
    prepared: Sequence[mass_driver.PreparedReplacement],
    canonical_id: int,
) -> bytes:
    matches = [item.bundle for item in prepared if item.bundle_id == canonical_id]
    if len(matches) != 1:
        raise UnifiedBuildError(
            f"Mass Driver prepared {len(matches)} resources for canonical {canonical_id}"
        )
    return matches[0]


def _mass_field(
    prepared: Sequence[mass_driver.PreparedReplacement],
    field: int,
) -> mass_driver.PreparedReplacement:
    matches = [item for item in prepared if item.target_field == field]
    if len(matches) != 1 or matches[0].graphics is None:
        raise UnifiedBuildError(f"Mass Driver prepared field {field} incorrectly")
    return matches[0]


def _add_surface(
    replacements: dict[int, UnifiedReplacement],
    fields: Sequence[Any],
    donors: Sequence[Any],
) -> None:
    for item in fields:
        _add(
            replacements,
            UnifiedReplacement(
                item.spec.identity.bundle_id,
                f"Surface Soylent field {item.spec.identity.scene}",
                "surface_soylent",
                item.bundle,
            ),
        )
    for item in donors:
        _add(
            replacements,
            UnifiedReplacement(
                item.identity.bundle_id,
                f"Surface Soylent donor field {item.identity.scene}",
                "surface_soylent",
                item.bundle,
            ),
        )
        _add(
            replacements,
            UnifiedReplacement(
                item.identity.graphics_id,
                f"Surface Soylent donor field {item.identity.scene} graphics",
                "surface_soylent",
                item.graphics,
            ),
        )


def _add_rico(
    replacements: dict[int, UnifiedReplacement],
    rico_items: Sequence[rico.Replacement],
) -> None:
    for item in rico_items:
        if item.canonical_id in RICO_SHARED_IDS:
            continue
        _add(
            replacements,
            UnifiedReplacement(
                item.canonical_id,
                item.role,
                "rico_arc",
                item.data,
            ),
            # Keep shared boss/scene assets only after exact byte equality.
            allow_identical=item.canonical_id in IDENTICAL_RICO_DEPENDENCIES,
        )


def _rico_resource(
    rico_items: Sequence[rico.Replacement],
    canonical_id: int,
) -> bytes:
    matches = [item.data for item in rico_items if item.canonical_id == canonical_id]
    if len(matches) != 1:
        raise UnifiedBuildError(
            f"Rico prepared {len(matches)} resources for canonical {canonical_id}"
        )
    return matches[0]


def _verify_rico_battle_compatibility(
    replacements: dict[int, UnifiedReplacement],
    rico_items: Sequence[rico.Replacement],
) -> None:
    """Prove Mass-owned battle resources retain Rico's required runtime data."""

    try:
        mass_arena = decode_lzss_complete_groups(
            replacements[47].data + bytes(16)
        )[0]
        rico_arena = decode_lzss_complete_groups(
            _rico_resource(rico_items, 47) + bytes(16)
        )[0]
        mass_arena_header = struct.unpack_from("<4I", mass_arena)
        rico_arena_header = struct.unpack_from("<4I", rico_arena)
        runtime_start, runtime_end = mass_arena_header[2:4]
        if (
            mass_arena_header != rico_arena_header
            or not 0 <= runtime_start <= runtime_end <= len(mass_arena)
            or runtime_end > len(rico_arena)
            or mass_arena[runtime_start:runtime_end]
            != rico_arena[runtime_start:runtime_end]
        ):
            raise UnifiedBuildError(
                "Mass-owned battle arena 47 is incompatible with Rico's runtime"
            )

        mass_stats = mass_driver._indexed_bundle_entries(replacements[2614].data)
        rico_stats = mass_driver._indexed_bundle_entries(
            _rico_resource(rico_items, 2614)
        )
        if len(mass_stats) != 38 or len(rico_stats) != 38:
            raise UnifiedBuildError(
                "Mass/Rico battle-stat archive 2614 lost its 38-entry layout"
            )
        # Redrum's local boss record dispatches enemy attacks through entry 3.
        # Preserve the normalized retail table; raw PW Disc 2 differs here.
        if decode_lzss_complete_groups(mass_stats[3] + bytes(16))[0] != decode_lzss_complete_groups(rico_stats[3] + bytes(16))[0]:
            raise UnifiedBuildError("Mass-owned battle stats 2614 changed Redrum attack entry 3")
        attack_region = 41 * mass_driver.EL_REGULUS_ATTACK_RECORD_SIZE
        # These are the live archive entries for Weltall, Brigandier, and
        # Stier, the player Gears used by Rico's authored battle contracts.
        for entry_id in (27, 31, 33):
            mass_table = decode_lzss_complete_groups(
                mass_stats[entry_id] + bytes(16)
            )[0]
            rico_table = decode_lzss_complete_groups(
                rico_stats[entry_id] + bytes(16)
            )[0]
            if (
                len(mass_table) < attack_region
                or len(rico_table) < attack_region
                or mass_table[:attack_region] != rico_table[:attack_region]
            ):
                raise UnifiedBuildError(
                    "Mass-owned battle stats 2614 are incompatible with "
                    f"Rico Gear archive entry {entry_id}"
                )
    except KeyError as exc:
        raise UnifiedBuildError(
            f"Mass-owned Rico battle dependency {exc.args[0]} was not retained"
        ) from exc
    except (ValueError, struct.error, mass_driver.DungeonBuildError) as exc:
        raise UnifiedBuildError(
            f"Mass/Rico battle compatibility data is malformed: {exc}"
        ) from exc


def _verify_rico_field_pairs(
    replacements: dict[int, UnifiedReplacement],
) -> None:
    """Require active Rico field pairs without requiring retired reenactments."""

    from modules.rico.chapter_two_interludes import ACTIVE_ROOMS

    expected_fields = {
        *range(229, 237),
        64,
        65,
        66,
        rico.UNIFIED_DISC2_CHAPTER_TWO_BEDROOM_FIELD,
        *(field for room, field in WORLD_FIELDS.items() if room in ACTIVE_ROOMS),
    }
    expected_resources = {
        resource_id
        for field in expected_fields
        for resource_id in (
            rico._field_bundle_id(field),
            rico._field_bundle_id(field) + 1,
        )
    }
    missing = sorted(expected_resources - replacements.keys())
    if missing:
        raise UnifiedBuildError(
            f"Unified Rico field/graphics set is missing canonical IDs {missing}"
        )


def _verify_reserved_dummies(disc2: rico.DiscReader) -> None:
    for canonical_id in RESERVED_DUMMY_IDS:
        data = disc2.canonical(canonical_id)
        if data != DUMMY_PAYLOAD or hashlib.sha256(data).hexdigest() != DUMMY_SHA256:
            raise UnifiedBuildError(
                f"Reserved Disc 2 canonical {canonical_id} is no longer CDMAKE dummy"
            )


def prepare_unified_replacements(
    *,
    disc2_source: Path | str,
    disc1_donor: Path | str,
    rico_disc1: Path | str,
    input_root: Path | str = ROOT / "work",
    dialogue_root: Path | str = ROOT / "modules" / "mass_driver" / "content",
) -> tuple[UnifiedReplacement, ...]:
    """Prepare and compose the complete unified canonical replacement map."""

    disc2_path = Path(disc2_source).resolve()
    disc1_path = Path(disc1_donor).resolve()
    rico_disc1_path = Path(rico_disc1).resolve()
    disc2 = rico.DiscReader(disc2_path, 2)
    _verify_reserved_dummies(disc2)
    rico.validate_disc(rico_disc1_path, 1)

    mass_prepared = mass_driver.prepare_all(input_root, dialogue_root)
    mass_driver.verify_route_transitions(mass_prepared)
    mass_driver.verify_visible_door_contracts(mass_prepared)
    mass_driver.verify_save_point_visual_contracts(mass_prepared)
    mass_driver.verify_control_and_archive_terminal_roles(mass_prepared)
    mass_driver.verify_scene_continuity(mass_prepared)
    replacements = _mass_replacements(mass_prepared)
    clinic_resource_overrides = {
        item.bundle_id: item.bundle
        for item in mass_prepared
        if item.bundle_id in surface.CLINIC_SECURITY_NORMALIZED_CD2_RESOURCES
    }

    surface_fields, surface_donors, surface_titles = surface.prepare_campaign(
        disc2_path,
        disc1_path,
        include_title=False,
        clinic_resource_overrides=clinic_resource_overrides,
    )
    if surface_titles:
        raise UnifiedBuildError("Content-only Surface preparation emitted title resources")
    _add_surface(replacements, surface_fields, surface_donors)

    chapters = rico.load_chapters()
    rico_reader = rico.DiscReader(rico_disc1_path, 1)
    rico_by_disc = rico.prepare_replacements(
        rico_reader,
        chapters,
        content_menu_field=CONTENT_MENU_FIELD,
        disc2_ancillary_fields=rico.UNIFIED_DISC2_CHAPTER_ONE_ANCILLARY_FIELDS,
        disc2_chapter_two_bedroom_field=(
            rico.UNIFIED_DISC2_CHAPTER_TWO_BEDROOM_FIELD
        ),
    )
    from modules.rico.release_presentation import apply_release_presentation
    presented_rico, _presentation = apply_release_presentation(
        rico_reader, {2: rico_by_disc[2]},
        executable_sources={2: disc2.canonical(22)}, combined=True,
    )
    rico_by_disc[2] = presented_rico[2]
    _verify_rico_battle_compatibility(replacements, rico_by_disc[2])
    _add_rico(replacements, rico_by_disc[2])

    defense_archive = _mass_field(mass_prepared, 376)
    menu_bundle, menu_graphics, _menu_atlas = content_menu.build_content_menu_field(
        defense_archive.bundle,
        defense_archive.graphics,
    )
    _add(
        replacements,
        UnifiedReplacement(
            CONTENT_MENU_BUNDLE_ID,
            "full-screen four-card content selector",
            "unified_menu",
            menu_bundle,
        ),
    )
    _add(
        replacements,
        UnifiedReplacement(
            CONTENT_MENU_GRAPHICS_ID,
            "content selector screen plane and embedded atlas",
            "unified_menu",
            menu_graphics,
        ),
    )

    title_field = content_menu.patch_title_field_for_content_menu(
        disc2.canonical(SHARED_TITLE_FIELD_ID),
        menu_field=CONTENT_MENU_FIELD,
    )
    _add(
        replacements,
        UnifiedReplacement(
            SHARED_TITLE_FIELD_ID,
            "native New Game handoff to unified content selector",
            "unified_shared",
            title_field,
        ),
    )

    young_rico_portrait = rico.YOUNG_RICO_PORTRAIT_TIM.read_bytes()
    _add(
        replacements,
        UnifiedReplacement(
            SHARED_MENU_ID,
            "native title labels, Repair Bot shops, and young-Rico portrait",
            "unified_shared",
            merge_menu_archive_with_young_rico(
                disc2.canonical(SHARED_MENU_ID),
                _mass_resource(mass_prepared, SHARED_MENU_ID),
                young_rico_portrait,
            ),
        ),
    )
    _add(
        replacements,
        UnifiedReplacement(
            SHARED_SYSTEM_NAMES_ID,
            "Video Disk and young-Rico keepsake names",
            "unified_shared",
            merge_system_names(
                _mass_resource(mass_prepared, SHARED_SYSTEM_NAMES_ID)
            ),
        ),
    )
    _add(
        replacements,
        UnifiedReplacement(
            SHARED_SYSTEM_DATA_ID,
            "Video Disk, Memento balance, and keepsake descriptions",
            "unified_shared",
            merge_system_data(
                _mass_resource(mass_prepared, SHARED_SYSTEM_DATA_ID)
            ),
        ),
    )
    _add(
        replacements,
        UnifiedReplacement(
            SHARED_GAMESTATE_ID,
            "Vierge foundation, all deathblows, and Rico profiles",
            "unified_shared",
            merge_initial_gamestate(
                _mass_resource(mass_prepared, SHARED_GAMESTATE_ID)
            ),
        ),
    )

    for canonical_id in (2597, 2603):
        _add(
            replacements,
            UnifiedReplacement(
                canonical_id,
                "per-character weight-range enforcement",
                "unified_shared",
                patch_weight_mutation_overlay(disc2.canonical(canonical_id)),
            ),
        )
    disc2_title_overlay = rico._build_disc2_title_overlay(
        disc2.canonical(2599)
    )
    _add(
        replacements,
        UnifiedReplacement(
            2599,
            "native title/Continue with Disc 2 gate and weight ranges",
            "unified_shared",
            patch_weight_mutation_overlay(disc2_title_overlay),
        ),
    )

    if SHARED_BATTLE_OVERLAY_ID not in replacements:
        raise UnifiedBuildError("Mass Driver battle overlay was not retained")
    for canonical_id in MASS_OWNED_RICO_CONFLICT_IDS:
        if canonical_id not in replacements:
            raise UnifiedBuildError(
                f"Mass normal-combat dependency {canonical_id} was not retained"
            )
    if SHARED_TITLE_GRAPHICS_ID in replacements:
        raise UnifiedBuildError("Unified selector must leave retail title graphics intact")
    _verify_rico_field_pairs(replacements)
    return tuple(replacements[key] for key in sorted(replacements))


def materialize(
    replacements: Sequence[UnifiedReplacement],
    output_root: Path | str,
    *,
    disc2_source: Path | str,
    disc1_donor: Path | str,
    rico_disc1: Path | str,
    force: bool = False,
) -> tuple[tuple[int, Path], ...]:
    output = Path(output_root).resolve()
    if output.exists() and not output.is_dir():
        raise UnifiedBuildError(f"Output is not a directory: {output}")
    if output.is_dir() and any(output.iterdir()) and not force:
        raise UnifiedBuildError(f"Output is not empty: {output}; pass --force")
    replacement_root = output / "replacements"
    replacement_root.mkdir(parents=True, exist_ok=True)

    emitted: list[tuple[int, Path]] = []
    records: list[dict[str, Any]] = []
    ids: set[int] = set()
    for item in replacements:
        if item.canonical_id in ids:
            raise UnifiedBuildError(f"Duplicate canonical {item.canonical_id}")
        ids.add(item.canonical_id)
        path = replacement_root / (
            f"{item.canonical_id:04d}_{_slug(item.owner)}_{_slug(item.role)}.bin"
        )
        path.write_bytes(item.data)
        emitted.append((item.canonical_id, path))
        records.append(
            {
                "canonical_id": item.canonical_id,
                "owner": item.owner,
                "role": item.role,
                "file": path.relative_to(output).as_posix(),
                "size": len(item.data),
                "sha256": item.sha256,
            }
        )

    manifest = {
        "format": OUTPUT_FORMAT,
        "name": "Xenogears Reimagined - Unified Content Disc 2",
        "sources": {
            "perfect_works_disc2": Path(disc2_source).resolve().name,
            "perfect_works_disc1_donor": Path(disc1_donor).resolve().name,
            "retail_disc1_rico_donor": Path(rico_disc1).resolve().name,
        },
        "content_selector": {
            "field": CONTENT_MENU_FIELD,
            "canonical_pair": [CONTENT_MENU_BUNDLE_ID, CONTENT_MENU_GRAPHICS_ID],
            "options": [
                {"label": "Mass Driver", "enabled": True, "field": MASS_DRIVER_FIELD},
                {
                    "label": "Surface Soylent",
                    "enabled": True,
                    "field": SURFACE_SOYLENT_FIELD,
                },
                {"label": "Mahanon", "enabled": False, "status": MAHANON_STATUS},
                {"label": "Rico's Arc", "enabled": True, "field": RICO_HUB_FIELD},
            ],
            "selection_ring": [0, 1, 3],
            "mahanon_focusable": False,
        },
        "rico": {
            "chapter_select_field": RICO_HUB_FIELD,
            "chapter_fields": list(range(230, 237)),
            "chapter_one_ancillary_fields": [64, 65, 66],
            "chapter_two_bedroom_field": (
                rico.UNIFIED_DISC2_CHAPTER_TWO_BEDROOM_FIELD
            ),
            "memory_cube": {
                "save": True,
                "return_to_content_selector": CONTENT_MENU_FIELD,
                "restart_required": False,
            },
        },
        "title": {
            "native_rows": ["New Game", "Continue", "Sound"],
            "new_game_destination": CONTENT_MENU_FIELD,
            "continue_preserved": True,
            "title_graphics_1587": "source byte-identical",
        },
        "shared_resource_policy": {
            "battle_overlay_38": "Mass Disc 2 body-weight/native-yaw version",
            "battle_dependencies_47_2614": "Mass normal-combat versions",
            "system_names_29": "Video Disk plus young-Rico keepsakes",
            "system_data_2594": "Video Disk plus Memento/keepsake data",
            "menu_2593": "native title font plus Mass shops plus young-Rico portrait",
            "gamestate_2595": "Vierge plus Surface deathblows plus Rico profiles",
        },
        "replacement_count": len(records),
        "replacements": records,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return tuple(emitted)


def verify_image(
    image_path: Path | str,
    replacements: Sequence[UnifiedReplacement],
) -> None:
    image = Mode2Image(image_path)
    entries = image.read_index()
    for item in replacements:
        if item.canonical_id == 22:
            from modules.rico.dialogue_name_color import verify_executable_image
            verify_executable_image(image_path, 2, item.data)
            continue
        physical = item.canonical_id - 5
        if not 0 <= physical < len(entries):
            raise UnifiedBuildError(
                f"Canonical {item.canonical_id} is outside rebuilt Disc 2 FAT"
            )
        extracted = image.extract_entry(entries[physical])
        if extracted != item.data:
            raise UnifiedBuildError(
                f"Rebuilt canonical {item.canonical_id} differs from prepared data"
            )


def write_launcher(cue_path: Path | str) -> Path:
    from os.path import relpath

    cue = Path(cue_path).resolve()
    launcher = cue.with_name("PLAY_XENOGEARS_REIMAGINED.cmd")
    portable_executable = (
        ROOT / "work" / "duckstation" / "duckstation-qt-x64-ReleaseLTCG.exe"
    )
    try:
        portable_location = "%~dp0" + relpath(portable_executable, cue.parent)
    except ValueError:
        # An explicitly requested output on another drive has no relative
        # route to the workspace installation. Keep its exact local path.
        portable_location = str(portable_executable)
    launcher.write_text(
        "@echo off\n"
        "setlocal\n"
        "title Xenogears Reimagined - Unified Content\n"
        "set \"DISC=%~dp0" + cue.name + "\"\n"
        "set \"PORTABLE_DUCKSTATION=" + portable_location + "\"\n"
        "set \"INSTALLED_DUCKSTATION=%LOCALAPPDATA%\\Programs\\DuckStation\\duckstation-qt-x64-ReleaseLTCG.exe\"\n"
        "set \"DUCKSTATION=\"\n"
        "if exist \"%PORTABLE_DUCKSTATION%\" set \"DUCKSTATION=%PORTABLE_DUCKSTATION%\"\n"
        "if not defined DUCKSTATION if exist \"%INSTALLED_DUCKSTATION%\" set \"DUCKSTATION=%INSTALLED_DUCKSTATION%\"\n"
        "if not exist \"%DISC%\" (echo Missing %DISC% & pause & exit /b 1)\n"
        "if not defined DUCKSTATION (echo DuckStation was not found. & pause & exit /b 1)\n"
        "start \"\" \"%DUCKSTATION%\" -batch -fastboot \"%DISC%\"\n",
        encoding="utf-8",
        newline="\r\n",
    )
    return launcher


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disc2-source", type=Path, required=True)
    parser.add_argument("--disc1-donor", type=Path, required=True)
    parser.add_argument("--rico-disc1", type=Path, required=True)
    parser.add_argument("--input-root", type=Path, default=ROOT / "work")
    parser.add_argument(
        "--dialogue-root",
        type=Path,
        default=ROOT / "modules" / "mass_driver" / "content",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--build-disc", action="store_true")
    parser.add_argument("--xenoiso", type=Path)
    parser.add_argument("--disc-output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.build_disc and not all((args.xenoiso, args.disc_output)):
        parser.error("--build-disc requires --xenoiso and --disc-output")
    if not args.build_disc and any((args.xenoiso, args.disc_output)):
        parser.error("--xenoiso and --disc-output require --build-disc")
    try:
        replacements = prepare_unified_replacements(
            disc2_source=args.disc2_source,
            disc1_donor=args.disc1_donor,
            rico_disc1=args.rico_disc1,
            input_root=args.input_root,
            dialogue_root=args.dialogue_root,
        )
        emitted = materialize(
            replacements,
            args.output,
            disc2_source=args.disc2_source,
            disc1_donor=args.disc1_donor,
            rico_disc1=args.rico_disc1,
            force=args.force,
        )
        print(f"Prepared {len(replacements)} unified Disc 2 replacements")
        print(f"Wrote {Path(args.output).resolve() / 'manifest.json'}")
        if args.build_disc:
            # Invoke the wrapper in-process.  Passing hundreds of canonical
            # replacements back through its CLI exceeds Windows' command-line
            # limit even though Xenoiso's own command-list format has no such
            # restriction.
            build_result = xenoiso_build.command_build(
                argparse.Namespace(
                    xenoiso=args.xenoiso,
                    source=args.disc2_source,
                    output=args.disc_output,
                    replacement=list(emitted),
                    disc=2,
                    force=args.force,
                )
            )
            if build_result:
                raise UnifiedBuildError(
                    f"Xenoiso wrapper exited with code {build_result}"
                )
            verify_image(args.disc_output, replacements)
            boot = verify_retail_title_boot(args.disc_output)
            launcher = write_launcher(Path(args.disc_output).with_suffix(".cue"))
            print(
                f"Verified native publisher/title boot at raw LBA {boot.lba}: "
                f"{boot.sha256}"
            )
            print(f"Wrote {launcher}")
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
