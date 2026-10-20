"""A coherent adult Rico starting profile near his first playable Kislev visit.

Level 24 is an authored recruitment benchmark, not a fixed retail join level:
bench experience and player grinding change the level at which Rico joins.
The HP/EP and growing stats below are median outcomes of fourteen native
level-ups from the retail level-10 record. Agility retains its native value.

Evidence: USA Disc 1 resource 2595 (SHA256 d892fa678f66ab12e0d2cb5ccb6cd432ecbc
055b41360d8a4c4404fd38f1e20b) supplies the starting record. Resource 2607 part 0
(also 2594 part 43), SHA256 67b4996a397b207c75310b2d32f890e1348a1041734439a6a4
f161e974350c16, contains Rico's growth data at 0x608, AP thresholds at 0x61C,
Spirit thresholds at 0x640, deathblow thresholds at 0x650, and the shared XP
delta table at 0xBB0. The growth formulas were independently documented by
ForteGSOmega: https://gamefaqs.gamespot.com/ps/199365-xenogears/faqs/58934,
section 10. These are representative stats, not a reconstruction of one RNG
history or a claim that every retail level-24 Rico has identical stats.

Apply after the older level-70/full-ability anthology defaults. This helper
only changes adult Rico's progression. Equipment, body-weight settings,
Gear equipment, other characters, names, roster and story state survive.
"""

from __future__ import annotations

from dataclasses import dataclass
import struct
from typing import Final

from modules.rico.tools.xgrico_balance import (
    CHARACTER_ID_OFFSET,
    GAMESTATE_SIZE,
    PARTY_RECORD_BASE,
    PARTY_RECORD_SIZE,
    RICO_ABILITY_RECORD,
    RICO_ID,
)


class RicoRecruitmentError(ValueError):
    """The input cannot safely receive Rico's initial progression profile."""


@dataclass(frozen=True)
class RicoRecruitmentProfile:
    level: int = 24
    total_experience: int = 49_265
    next_level_experience: int = 8_051
    hp: int = 209
    mp: int = 23
    # Native order: Attack, Defense, Agility, Ether, Ether Defense,
    # reserved byte, Hit%, Evade%.
    stats: bytes = bytes.fromhex("27 23 07 0A 0C 00 0D 0C")
    learning: int = 3
    on_foot_deathblows: int = 0xF000
    spirit_commands: int = 0xC000
    stier_deathblows: int = 0x1800
    ap_per_turn: int = 6


RICO_RECRUITMENT_PROFILE: Final = RicoRecruitmentProfile()
RICO_RECRUITMENT_LEVEL: Final = RICO_RECRUITMENT_PROFILE.level
RICO_RECORD: Final = PARTY_RECORD_BASE + RICO_ID * PARTY_RECORD_SIZE

# Total on-foot/pilot XP, then remaining on-foot/pilot XP, form four u32s.
# Retail level 10 has totals 2049 and remaining 821; they must not be swapped.
XP_OFFSET: Final = 0x3C
HP_MP_OFFSET: Final = 0x4C
LEARNING_OFFSET: Final = 0x55
STATS_OFFSET: Final = 0x58
LEVELS_OFFSET: Final = 0x62
PRACTICE_OFFSET: Final = 0x90
PRACTICE_END: Final = 0xA0
ABILITY_RECORD_SIZE: Final = 0x20
AP_OFFSET: Final = 0x17


def apply_rico_recruitment_profile(source: bytes) -> bytes:
    """Initialize adult Rico at level 24 with matching XP, stats and commands.

    This is a New Game initializer, not an in-place migration for user saves.
    Four early deathblows are ready through Dragon Fist (retail level 22),
    alongside Steel Fist/Steel Body and Stier's native starting commands.
    Later commands and the donor's accumulated practice counters are cleared.
    """

    if len(source) != GAMESTATE_SIZE:
        raise RicoRecruitmentError(
            f"Initial GameState is {len(source)} bytes, expected {GAMESTATE_SIZE}"
        )
    if source[RICO_RECORD + CHARACTER_ID_OFFSET] != RICO_ID:
        raise RicoRecruitmentError("Adult Rico's record ID changed")
    result = bytearray(source)
    profile = RICO_RECRUITMENT_PROFILE
    struct.pack_into(
        "<4I", result, RICO_RECORD + XP_OFFSET,
        profile.total_experience, profile.total_experience,
        profile.next_level_experience, profile.next_level_experience,
    )
    struct.pack_into(
        "<4H", result, RICO_RECORD + HP_MP_OFFSET,
        profile.hp, profile.hp, profile.mp, profile.mp,
    )
    result[RICO_RECORD + LEARNING_OFFSET] = profile.learning
    result[RICO_RECORD + STATS_OFFSET : RICO_RECORD + STATS_OFFSET + 8] = profile.stats
    result[RICO_RECORD + LEVELS_OFFSET : RICO_RECORD + LEVELS_OFFSET + 2] = bytes((profile.level,) * 2)
    # Battle results persist the seven practice words at 0x90; the entire
    # native 0x90..0x9F starting window is zero. Do not retain late-save practice.
    result[RICO_RECORD + PRACTICE_OFFSET : RICO_RECORD + PRACTICE_END] = bytes(16)
    result[RICO_ABILITY_RECORD : RICO_ABILITY_RECORD + ABILITY_RECORD_SIZE] = bytes(ABILITY_RECORD_SIZE)
    struct.pack_into(
        "<3H", result, RICO_ABILITY_RECORD,
        profile.on_foot_deathblows, profile.spirit_commands, profile.stier_deathblows,
    )
    result[RICO_ABILITY_RECORD + AP_OFFSET] = profile.ap_per_turn
    return bytes(result)
