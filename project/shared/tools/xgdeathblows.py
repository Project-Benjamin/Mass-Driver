#!/usr/bin/env python3
"""Grant every native on-foot deathblow in a Xenogears GameState.

The persistent GameState contains eleven 0x20-byte ability records.  Their
first little-endian halfword is a reverse-ordered learned-command bitfield:
bit 15 is command zero, bit 14 is command one, and so on.  Chu-Chu and Maria
have no native on-foot deathblow table; the final two records are Citan's
sword form and adult Emeralda.

This module deliberately changes only those learned-command halfwords.  Gear
commands live in later words in the same records and must not be conflated
with the on-foot masks.  Character levels, experience, HP, and all other
stats are preserved.  The checked Perfect Works foundation already removes
the level requirements from these commands, so no level edit is required.
"""

from __future__ import annotations

from dataclasses import dataclass
import struct
from typing import Final


GAMESTATE_SIZE: Final = 0x2358
ABILITY_RECORD_BASE: Final = 0x16C0
ABILITY_RECORD_SIZE: Final = 0x20
ON_FOOT_DEATHBLOW_WORD_OFFSET: Final = 0


@dataclass(frozen=True)
class DeathblowProfile:
    """One native GameState ability record and its complete command mask."""

    character_id: int
    character: str
    command_names: tuple[str, ...]

    @property
    def full_mask(self) -> int:
        count = len(self.command_names)
        return ((1 << count) - 1) << (16 - count) if count else 0

    @property
    def word_offset(self) -> int:
        return (
            ABILITY_RECORD_BASE
            + self.character_id * ABILITY_RECORD_SIZE
            + ON_FOOT_DEATHBLOW_WORD_OFFSET
        )


DEATHBLOW_PROFILES: Final = (
    DeathblowProfile(
        0,
        "Fei",
        (
            "Raijin",
            "Senretsu",
            "Hagan",
            "Hoten",
            "Tenbu",
            "Ryujin",
            "Koho",
            "Fukei",
            "Chikei",
            "Kakei",
            "Suikei",
            "Kokei",
            "Yamikei",
        ),
    ),
    DeathblowProfile(
        1,
        "Elly",
        (
            "Screamer",
            "Cyclone Kick",
            "Breakthrough",
            "Double Shock",
            "Sky Attack",
            "Bright Spark",
            "Sting Kick",
            "Anemo Zap",
            "Terra Charge",
            "Thermo Thump",
            "Aqua Frost",
        ),
    ),
    DeathblowProfile(
        2,
        "Citan",
        (
            "Ukigumo",
            "Mufu",
            "Jinrai",
            "Shinrai",
            "Renken",
            "Hakai",
            "Ougi",
            "Willow Wind",
            "Rare Earth",
            "Hell Fire",
            "Tsunami Ice",
        ),
    ),
    DeathblowProfile(
        3,
        "Bart",
        (
            "Head Hunter",
            "Twin Sonic",
            "Rhythm Shock",
            "Dynamic",
            "Astral",
            "Bracer",
            "Justice",
            "Angel",
            "Land Break",
            "Prominence",
            "Tornado",
        ),
    ),
    DeathblowProfile(
        4,
        "Billy",
        (
            "Adams Apple",
            "Gunholic",
            "Hell Blast",
            "Nut Crack",
            "Sky Walker",
            "Devil Blast",
            "Banfrau",
            "True Dream",
            "Holy Gate",
            "Dear Friend",
        ),
    ),
    DeathblowProfile(
        5,
        "Rico",
        (
            "Rico Rocket",
            "Death Drive",
            "Banderas",
            "Dragon Fist",
            "Fire Bomb",
            "Pile Crusher",
            "Spin Strike",
            "Death Roll",
            "Flame Lariat",
            "Hell Splash",
        ),
    ),
    DeathblowProfile(
        6,
        "Emeralda (child)",
        (
            "Leg Cutter",
            "Wave Cutter",
            "Leg Spin",
            "Hammerhead",
            "Grand Arm",
            "Divider",
            "Flying Arm",
            "Tornado Hand",
            "Reycount",
            "Dark Beast",
        ),
    ),
    DeathblowProfile(7, "Chu-Chu", ()),
    DeathblowProfile(8, "Maria", ()),
    DeathblowProfile(
        9,
        "Citan (sword)",
        (
            "Amaoto",
            "Engetsu",
            "Amagumo",
            "Himatsu",
            "Yako",
            "Zanretsu",
            "Myogetsu",
            "Festive Wind",
            "Rumble Earth",
            "Haze of Fire",
            "CrystalWater",
        ),
    ),
    DeathblowProfile(
        10,
        "Emeralda (adult)",
        (
            "Leg Cutter",
            "Wave Cutter",
            "Leg Spin",
            "Hammerhead",
            "Grand Arm",
            "Divider",
            "Flying Arm",
            "Tornado Hand",
            "Reycount",
            "Dark Beast",
        ),
    ),
)

FULL_MASKS: Final = tuple(profile.full_mask for profile in DEATHBLOW_PROFILES)
EXPECTED_FULL_MASKS: Final = (
    0xFFF8,
    0xFFE0,
    0xFFE0,
    0xFFE0,
    0xFFC0,
    0xFFC0,
    0xFFC0,
    0x0000,
    0x0000,
    0xFFE0,
    0xFFC0,
)
if FULL_MASKS != EXPECTED_FULL_MASKS:
    raise AssertionError("Native deathblow profile masks changed")


def learned_mask(gamestate: bytes | bytearray, character_id: int) -> int:
    """Read one character form's learned on-foot deathblow mask."""

    if len(gamestate) != GAMESTATE_SIZE:
        raise ValueError(
            f"GameState is {len(gamestate)} bytes, expected {GAMESTATE_SIZE}"
        )
    if not 0 <= character_id < len(DEATHBLOW_PROFILES):
        raise ValueError(f"Character ID is outside the GameState roster: {character_id}")
    return struct.unpack_from(
        "<H", gamestate, DEATHBLOW_PROFILES[character_id].word_offset
    )[0]


def grant_all_on_foot_deathblows(gamestate: bytes) -> bytes:
    """Return a GameState with every native on-foot deathblow learned.

    Existing bits outside each character's natural command range are retained.
    This is both safer for future engine discoveries and makes the operation
    idempotent on already-upgraded saves.
    """

    if len(gamestate) != GAMESTATE_SIZE:
        raise ValueError(
            f"GameState is {len(gamestate)} bytes, expected {GAMESTATE_SIZE}"
        )
    result = bytearray(gamestate)
    for profile in DEATHBLOW_PROFILES:
        if not profile.full_mask:
            continue
        before = struct.unpack_from("<H", result, profile.word_offset)[0]
        struct.pack_into("<H", result, profile.word_offset, before | profile.full_mask)
    return bytes(result)


__all__ = [
    "ABILITY_RECORD_BASE",
    "ABILITY_RECORD_SIZE",
    "DEATHBLOW_PROFILES",
    "EXPECTED_FULL_MASKS",
    "FULL_MASKS",
    "GAMESTATE_SIZE",
    "ON_FOOT_DEATHBLOW_WORD_OFFSET",
    "DeathblowProfile",
    "grant_all_on_foot_deathblows",
    "learned_mask",
]
