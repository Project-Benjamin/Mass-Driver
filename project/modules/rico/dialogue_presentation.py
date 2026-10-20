"""Plan Rico's authored text as independent native dialogue windows.

This module neither allocates dialogue IDs nor installs portraits or colors.
Its caller can decorate each segment's first speaker row and select that
speaker's verified portrait.  Original strings remain suitable as dialogue-ID
keys.  Each result is one page ending in Close, so a portrait never survives
an unannounced speaker change inside the same native window.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from types import MappingProxyType

from shared.tools.xgdialog import CHARACTER_IDS, PLAIN_ENCODE


WINDOW_WIDTH = 58
NARRATOR_CAPACITY = WINDOW_WIDTH | 1
NARRATOR_ROWS = 7
PORTRAIT_CAPACITY = 41
# Native F5 adds seventeen units for the portrait. The stored width describes
# the text column, so 41 produces the same 58-unit outer width as narration.
PORTRAIT_WINDOW_WIDTH = 41
PORTRAIT_ROWS = 4
CHOICE_START = "<Opcode:01:FF>"

# This is a cast list, not the layout builder's broader all-caps-label test.
# Keep the authored spelling in text while exposing one stable cast identity.
SPEAKER_LABELS = MappingProxyType({
    **{f"<{name}>": name for name in ("Rico", "Fei", "Citan", "Bart")},
    **{name: name for name in (
        "Anne", "Sigmund", "Hammer", "Rue", "Suzarn", "Leonardo", "Gramps",
        "Guard", "Infirmary Attendant", "Worker", "Prisoner", "Battler",
        "Arena Official", "Clerk", "Latina",
    )},
    "ETHOS PRIEST": "Ethos Priest",
    "ADJUTANT": "Adjutant",
    "ARCHIVIST": "Archivist",
    "SECURITY CAPTAIN": "Security Captain",
    "WORKER": "Worker",
    "BATTLER": "Battler",
    "DEMI-HUMAN WORKER": "Demi-Human Worker",
    "OLD PRISONER": "Old Prisoner",
    "ANNOUNCER": "Announcer",
})

SYSTEM_LABELS = frozenset({
    "SYSTEM", "ARCHIVE RELAY", "ARCHIVE SEARCH", "BATTLE REPORT",
    "CITYWIDE EVACUATION GRID", "COLLAR CONTROL", "COMBAT RELAY",
    "COMMITTEE PRISONERS: HELD", "CORE REGULATOR", "DEATH REPORTS: FABRICATED",
    "EMERGENCY RELAY", "ETHOS PRENATAL PROCEDURES", "EVACUATION GRID",
    "EXECUTIVE INQUIRY OPENED", "FACILITY MAP", "FATIMA COMMAND",
    "KISLEV DISPATCH", "KISLEV RECEIVER", "LATER", "MEDICAL INDEX",
    "MONITOR", "PHYSICIAN REGISTRY", "RICO'S LETTER", "STIER LAUNCH CONTROL",
    "UPPER STATION",
    *(f"ARCHIVE RECORD {number}" for number in (1, 2, 3)),
    *(f"RELAY {number}" for number in (1, 2, 3)),
    *(f"CHAPTER {number}" for number in range(1, 8)),
    *(f"CHAPTER {number} COMPLETE" for number in range(1, 8)),
    *(f"END OF CHAPTER {number}" for number in range(1, 8)),
})
_TOKEN = re.compile(r"<([^<>]+)>")
_DELAY = re.compile(r"Delay:(\d{1,3})\Z", re.ASCII)


class DialoguePresentationError(ValueError):
    """Authored text cannot fit or cannot be interpreted without guessing."""


@dataclass(frozen=True)
class DialogueSegment:
    speaker: str | None
    text: str
    width: int
    height: int


def visible_text(text: str) -> str:
    """Expand native names and remove only understood zero-width controls."""
    result: list[str] = []
    position = 0
    while position < len(text):
        character = text[position]
        if character != "<":
            if character not in PLAIN_ENCODE and character != "\n":
                raise DialoguePresentationError(f"Unsupported glyph {character!r}")
            result.append(character)
            position += 1
            continue
        match = _TOKEN.match(text, position)
        if match is None:
            raise DialoguePresentationError("Unterminated dialogue control")
        token = match.group(1)
        delay = _DELAY.fullmatch(token)
        if token in CHARACTER_IDS:
            result.append(token)
        elif token in ("Wait", "Opcode:01:FF"):
            pass
        elif delay is not None and int(delay.group(1)) <= 255:
            pass
        else:
            raise DialoguePresentationError(f"Unsupported control <{token}>")
        position = match.end()
    return "".join(result)


def glyph_units(text: str) -> int:
    """Measure the USA renderer's four-pixel horizontal units."""
    return sum(
        2 if PLAIN_ENCODE[character] <= 0x63 else 3
        for character in visible_text(text)
        if character != "\n"
    )


def _wrap(words: list[str], capacity: int) -> list[str]:
    rows: list[str] = []
    line = ""
    for word in words:
        if glyph_units(word) > capacity:
            raise DialoguePresentationError(
                f"Word exceeds the {capacity}-unit window capacity: {word!r}"
            )
        candidate = f"{line} {word}" if line else word
        if line and glyph_units(candidate) > capacity:
            rows.append(line)
            line = word
        else:
            line = candidate
    if line:
        rows.append(line)
    return rows


def _sentence_ends(word: str) -> bool:
    return visible_text(word).rstrip("]\"')").endswith((".", "!", "?"))


def _prose_pages(text: str, capacity: int, row_limit: int) -> list[list[str]]:
    """Prefer complete sentences; split an overlong sentence without edits."""
    words = text.split()
    if not words:
        return [[]]
    pages: list[list[str]] = []
    while words:
        count = 0
        for index in range(1, len(words) + 1):
            if len(_wrap(words[:index], capacity)) > row_limit:
                break
            count = index
        if count == 0:
            raise DialoguePresentationError("Dialogue page cannot hold its next word")
        if count < len(words):
            sentence_breaks = [
                index for index in range(1, count + 1)
                if _sentence_ends(words[index - 1])
            ]
            if sentence_breaks:
                count = sentence_breaks[-1]
        pages.append(_wrap(words[:count], capacity))
        words = words[count:]
    return pages


def _narrator_pages(page: str) -> list[list[str]]:
    rows = page.split("\n")
    visible = visible_text(page)
    all_upper = any(char.isalpha() for char in visible) and not any(
        char.islower() for char in visible
    )
    if rows[0] in SYSTEM_LABELS or all_upper:
        # Record and chapter-card rows carry meaning independently of prose.
        wrapped = [
            line for row in rows
            for line in (_wrap(row.split(), NARRATOR_CAPACITY) or [""])
        ]
        return [wrapped[start:start + NARRATOR_ROWS]
                for start in range(0, len(wrapped), NARRATOR_ROWS)]
    return _prose_pages(page, NARRATOR_CAPACITY, NARRATOR_ROWS)


def _source_atoms(text: str) -> tuple[str, ...]:
    words: list[str] = []
    for page in text[:-len("<Close>")].split("<New>"):
        head, separator, body = page.partition("\n")
        words.extend((body if separator and head in SPEAKER_LABELS else page).split())
    return tuple(words)


def plan_dialogue(text: str) -> list[DialogueSegment]:
    """Return portrait-aware pages while preserving story words and controls.

    Explicit speaker labels apply through later unlabeled New pages in this
    block.  Choices, known system labels, and bracketed stage directions reset
    that speaker.  Unmarked prose inside a speech remains speech: pronouns or
    third-person wording are not reliable narrator cues.
    """
    if not text.endswith("<Close>") or text.count("<Close>") != 1:
        raise DialoguePresentationError("Expected exactly one terminal <Close>")
    segments: list[DialogueSegment] = []
    speaker: str | None = None
    label: str | None = None
    for page in text[:-len("<Close>")].split("<New>"):
        head, separator, body = page.partition("\n")
        if page.startswith(CHOICE_START):
            speaker = label = None
            rows = page.split("\n")
            if len(rows) > NARRATOR_ROWS or any(
                glyph_units(row) > NARRATOR_CAPACITY for row in rows
            ):
                raise DialoguePresentationError("Choice must fit unchanged in one window")
            segments.append(DialogueSegment(None, page + "<Close>", WINDOW_WIDTH, len(rows)))
            continue
        if separator and head in SPEAKER_LABELS:
            speaker, label = SPEAKER_LABELS[head], head
            content = body
        else:
            if head in SYSTEM_LABELS or page.lstrip().startswith("["):
                speaker = label = None
            content = page
        if speaker is not None:
            assert label is not None
            if glyph_units(label) > PORTRAIT_CAPACITY:
                raise DialoguePresentationError(f"Speaker label does not fit: {label!r}")
            pages = _prose_pages(content, PORTRAIT_CAPACITY, PORTRAIT_ROWS - 1)
            for rows in pages:
                segments.append(DialogueSegment(
                    speaker, "\n".join([label, *rows]) + "<Close>",
                    PORTRAIT_WINDOW_WIDTH, PORTRAIT_ROWS,
                ))
        else:
            for rows in _narrator_pages(content):
                segments.append(DialogueSegment(
                    None, "\n".join(rows) + "<Close>",
                    WINDOW_WIDTH, max(1, len(rows)),
                ))
    planned_atoms = tuple(
        word for segment in segments
        for word in (
            segment.text[:-len("<Close>")].partition("\n")[2]
            if segment.speaker is not None
            else segment.text[:-len("<Close>")]
        ).split()
    )
    if planned_atoms != _source_atoms(text):
        raise DialoguePresentationError("Presentation changed story words or controls")
    return segments
