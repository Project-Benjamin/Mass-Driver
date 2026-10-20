"""Native field music for Rico's rooms and D Block.

Retail field 218/canonical 1042 begins director INIT with BC 75 2F80:
track 47, The Champ. Field 230/canonical 1066 begins BC 75 4780:
track 71, normal Nortune music. Fields 196 and 217 also select 71 in
their ordinary town branches; field 211's commons inherits that music.
The separate 61 branches belong to later story conditions.

Use the same selection on field entry and after a fixed battle. OP75's
native same-track behavior preserves continuity between connected rooms;
it does not need a stop/restart or a volume change on every visit.
"""

from typing import Final


CHAMP_MUSIC_ID: Final = 0x2F
NORTUNE_MUSIC_ID: Final = 0x47
SEWER_MUSIC_ID: Final = 0x0D


def room_music(room: str, fallback: int = CHAMP_MUSIC_ID) -> int:
    """Choose the requested room themes while retaining other chapter cues."""
    if room in ("main", "bedroom"):
        return CHAMP_MUSIC_ID
    if room in ("commons", "intake", "bar", "street"):
        return NORTUNE_MUSIC_ID
    if room.startswith("sewer_"):
        return SEWER_MUSIC_ID
    return fallback
