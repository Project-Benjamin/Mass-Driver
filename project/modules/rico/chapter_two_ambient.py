"""Rico-facing replies grounded in each retained resident's retail dialogue.

The separate document appends only to the bar and street dialogue tables.
Existing Chapter2 scene IDs, story conditions and progress writes are intact.
Anonymous residents deliberately have no synthetic label or portrait.
"""
from dataclasses import dataclass
import json
from pathlib import Path


CONTENT_PATH = Path(__file__).resolve().parent / "content" / "chapter_02_ambient.json"
RESIDENTS = {"bar": (7, 11, 12, 13, 14, 15, 16, 17, 18, 19),
             "street": (36, 37, 39, 51)}


@dataclass(frozen=True)
class Conversation:
    key: str
    speaker: str | None
    native_dialogue_ids: tuple[int, ...]
    blocks: tuple[str, ...]


def load_conversations(room: str) -> dict[int, Conversation]:
    if room not in RESIDENTS:
        return {}
    document = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    if document.get("format") != "xenogears-rico-chapter-two-ambient-v1":
        raise ValueError("Unknown Chapter2 ambient dialogue format")
    rows = document["rooms"][room]
    if {int(entity) for entity in rows} != set(RESIDENTS[room]):
        raise ValueError(f"{room} ambient cast differs from its audited native residents")
    result = {}
    for entity in RESIDENTS[room]:
        row = rows[str(entity)]
        blocks = tuple(row["blocks"])
        speaker = row["speaker"]
        expected_speaker = "Latina" if (room, entity) == ("bar", 7) else None
        if speaker != expected_speaker or not blocks or any(
                not isinstance(text, str) or not text.endswith("<Close>") for text in blocks):
            raise ValueError(f"Invalid ambient conversation {room}/{entity}")
        key = row["key"]
        if not isinstance(key, str) or not key.startswith(f"ambient_{room}_"):
            raise ValueError(f"Invalid ambient key for {room}/{entity}")
        result[entity] = Conversation(key, speaker, tuple(row["native_dialogue_ids"]), blocks)
    if len({row.key for row in result.values()}) != len(result):
        raise ValueError(f"Duplicate {room} ambient dialogue key")
    return result
