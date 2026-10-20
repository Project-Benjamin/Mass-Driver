"""Apply Rico's native portraits and opt-in speaker color at release assembly.

Semantic chapter preparation remains independently inspectable. This final
layer is shared by the two-disc anthology and combined Disc 2 composition.
Only Rico-owned field bundles are passed to the portrait compiler.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Mapping

from modules.rico.dialogue_portraits import present_field
from modules.rico.portrait_assets import (
    CUSTOM_PORTRAIT_IDS, NATIVE_PORTRAIT_IDS, prepare_portrait_assets,
)


def speaker_portraits(*, young_rico: bool = False) -> dict[str, int]:
    portraits = dict(NATIVE_PORTRAIT_IDS)
    portraits.update({slug.replace("_", " ").title(): portrait
                     for slug, portrait in CUSTOM_PORTRAIT_IDS.items()
                     if slug != "young_rico"})
    portraits["Announcer"] = CUSTOM_PORTRAIT_IDS["arena_official"]
    portraits["Demi-Human Worker"] = CUSTOM_PORTRAIT_IDS["demi_human_worker"]
    if young_rico:
        portraits["Rico"] = CUSTOM_PORTRAIT_IDS["young_rico"]
    return portraits


def apply_release_presentation(
    donor_reader,
    replacements: Mapping[int, list],
    *,
    executable_sources: Mapping[int, bytes],
    combined: bool = False,
):
    from modules.rico import build as core
    from modules.rico.chapter_two_resources import WORLD_FIELDS
    from modules.rico.chapter_two_interludes import ACTIVE_ROOMS
    from modules.rico.dialogue_name_color import patch_executable

    if set(replacements) != set(executable_sources):
        raise ValueError("Every presented disc needs its own source executable")
    assets = prepare_portrait_assets(donor_reader.canonical)
    output = {}
    report = {"format": "rico-native-dialogue-presentation-v1", "discs": {}}
    for disc, items in replacements.items():
        ancillary = (core.UNIFIED_DISC2_CHAPTER_ONE_ANCILLARY_FIELDS
                     if combined and disc == 2 else core.DEFAULT_CHAPTER_ONE_ANCILLARY_FIELDS)
        child_fields = {core.CHAPTER_FIELDS[disc][1], ancillary.firewood,
                        ancillary.aftermath, ancillary.funeral}
        bedroom = (core.UNIFIED_DISC2_CHAPTER_TWO_BEDROOM_FIELD
                   if combined and disc == 2 else core.CHAPTER_TWO_BEDROOM_FIELD)
        owned_fields = (set(core.CHAPTER_FIELDS[disc].values()) | child_fields
                        | {bedroom} | set(WORLD_FIELDS.values()))
        field_ids = {606 + 2 * field: field for field in owned_fields}
        fields = []
        presented = []
        seen = set()
        for item in items:
            if item.canonical_id in seen:
                raise ValueError(f"Duplicate Rico resource {item.canonical_id}")
            seen.add(item.canonical_id)
            if item.canonical_id in field_ids:
                field = field_ids[item.canonical_id]
                result = present_field(
                    item.data,
                    speaker_portraits(young_rico=field in child_fields),
                    colorize=lambda text: "<Opcode:0B:FE>" + text,
                )
                presented.append(replace(item, data=result.bundle))
                fields.append({"field": field, "canonical_id": item.canonical_id,
                               "windows": result.windows, "calls": result.calls,
                               "speakers": list(result.speakers),
                               "maximum_original_call_depth": result.maximum_original_call_depth})
            else:
                presented.append(item)
        # Historical expansion fields can still be inspected when supplied.
        # Current releases include only the five gap-story locations.
        retired = {606 + 2 * field for room, field in WORLD_FIELDS.items()
                   if room not in ACTIVE_ROOMS}
        absent = set(field_ids) - seen - retired
        if absent:
            raise ValueError(f"Missing Rico presentation fields: {sorted(absent)}")
        additions = [core.Replacement(asset.canonical_id,
                      f"Rico dialogue portrait: {asset.slug}", asset.data) for asset in assets]
        additions.append(core.Replacement(22, "Opt-in yellow dialogue speaker names",
                                          patch_executable(executable_sources[disc])))
        if seen.intersection(item.canonical_id for item in additions):
            raise ValueError("Dialogue presentation overlaps an existing replacement")
        output[disc] = presented + additions
        report["discs"][str(disc)] = {"fields": fields,
            "custom_portraits": [{"canonical_id": asset.canonical_id,
                                  "portrait_id": asset.portrait_id, "slug": asset.slug,
                                  "sha256": asset.sha256, "png_sha256": asset.png_sha256}
                                 for asset in assets]}
    return output, report
