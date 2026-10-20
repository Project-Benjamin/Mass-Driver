"""Temporary one-hit enemy HP for standalone Soylent playtesting.

Only the HP pools selected by the clinic-security and native Sufal formations
change. The normalized donor remains the source of truth; callers opt in after
normal campaign preparation and emit these two replacements separately from
title resources. No party data, AI, rewards, encounter selection, or field
progression changes here.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import struct

import modules.soylent_system.base as base
from shared.tools.xgdisc import Mode2Image


class PlaytestResourceError(base.SurfaceSoylentBuildError):
    """Raised when the checked normal-combat source no longer matches."""


# Native battleLoader.cpp loads eight 0x170-byte enemy definitions at 0x32.
# Each embeds sGameStateA4 followed by its Gear data at +0xA4. The formation
# selector's high bit chooses which pool applyChangeToHpOrMp actually damages:
# character current/max +0x4C/+0x4E (u16), Gear +0x104/+0x108 (u32).
# This is also the Gear HP layout audited by Mass Driver's normal-combat helper.
ENEMY_RECORD_START = 0x32
ENEMY_RECORD_SIZE = 0x170


@dataclass(frozen=True)
class EnemyHp:
    record: int
    form: str
    original_hp: int

    @property
    def offset(self) -> int:
        relative = 0x104 if self.form == "gear" else 0x4C
        return ENEMY_RECORD_START + self.record * ENEMY_RECORD_SIZE + relative

    @property
    def value_size(self) -> int:
        return 4 if self.form == "gear" else 2

    @property
    def format(self) -> str:
        return "<II" if self.form == "gear" else "<HH"


@dataclass(frozen=True)
class EnemyResource:
    canonical_id: int
    resource_set: int
    encounter: str
    size: int
    sha256: str
    enemies: tuple[EnemyHp, ...]


RESOURCE_SPECS = (
    EnemyResource(
        2684, 0x21, "clinic_security", 4533,
        "c7c46e83cf2383de1809f9d6d6faa90617906f0fa56acfea687d6adae248a862",
        (EnemyHp(1, "on_foot", 200), EnemyHp(2, "on_foot", 180)),
    ),
    EnemyResource(
        2706, 0x2C, "sufal_native_configuration_9", 4581,
        "a8260d2351cb681150a7dfbb43068699c717e8ec443783ab7ebb38525f1b50ff",
        (EnemyHp(3, "on_foot", 1300), EnemyHp(4, "gear", 4800)),
    ),
)


def prepare_one_hit_resources(
    source_disc: Path | str,
) -> tuple[tuple[base.PreparedTitleResource, ...], dict[str, object]]:
    """Prepare two checked enemy-stat overrides without modifying the source.

    Current and maximum HP become one so native healing cannot refill enemies
    beyond one. Misses, immunities, AI and victory/defeat processing stay native:
    the first successful damaging hit defeats each target. The return type is
    the existing generic resource payload shape, not a request for title jobs.
    """

    image = Mode2Image(source_disc)
    entries = image.read_index()
    sources: dict[int, bytes] = {}
    for spec in RESOURCE_SPECS:
        fat_index = spec.canonical_id - 5
        if not 0 <= fat_index < len(entries):
            raise PlaytestResourceError(
                f"One-hit resource {spec.canonical_id} lies outside the disc index"
            )
        data = image.extract_entry(entries[fat_index])
        if len(data) != spec.size or hashlib.sha256(data).hexdigest() != spec.sha256:
            raise PlaytestResourceError(
                f"One-hit resource {spec.canonical_id} is not the checked "
                "normalized normal-combat donor"
            )
        for enemy in spec.enemies:
            if struct.unpack_from(enemy.format, data, enemy.offset) != (
                enemy.original_hp, enemy.original_hp,
            ):
                raise PlaytestResourceError(
                    f"One-hit resource {spec.canonical_id} enemy {enemy.record} "
                    "current/max HP differs from the audited normal values"
                )
        sources[spec.canonical_id] = data

    prepared = []
    resource_metadata = []
    for spec in RESOURCE_SPECS:
        data = bytearray(sources[spec.canonical_id])
        record_metadata = []
        for enemy in spec.enemies:
            struct.pack_into(enemy.format, data, enemy.offset, 1, 1)
            record_metadata.append({
                "enemy_record": enemy.record,
                "form": enemy.form,
                "current_hp_offset": enemy.offset,
                "max_hp_offset": enemy.offset + enemy.value_size,
                "original_current_hp": enemy.original_hp,
                "original_max_hp": enemy.original_hp,
                "current_hp": 1,
                "max_hp": 1,
            })
        result = bytes(data)
        prepared.append(base.PreparedTitleResource(
            canonical_id=spec.canonical_id,
            name=f"soylent_playtest_{spec.encounter}_one_hit",
            filename=f"{spec.canonical_id}_soylent_playtest_one_hit.bin",
            source_sha256=spec.sha256,
            data=result,
        ))
        resource_metadata.append({
            "canonical_id": spec.canonical_id,
            "resource_set": spec.resource_set,
            "encounter": spec.encounter,
            "source_sha256": spec.sha256,
            "patched_sha256": hashlib.sha256(result).hexdigest(),
            "size": len(result),
            "records": record_metadata,
        })
    return tuple(prepared), {
        "one_hit_kills": True,
        "mode": "one_hit_kills",
        "scope": "standalone_soylent_encounters",
        "behavior": "Each enemy falls to the first successful damaging hit.",
        "resources": resource_metadata,
    }
