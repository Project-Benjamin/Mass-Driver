"""Lossless retail field inventory and conservative yellow speaker rows.

This module preserves retail payloads, including unreachable padding after
Close. It never infers a name from capitalisation or rewrites prose/layout.
The shared renderer colors row zero, so only single-page, standalone speaker
rows are eligible until a separate inline/multipage renderer is verified.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import struct
from typing import Mapping

from shared.tools.xgdialog import (
    CHARACTER_NAMES, DialogueBlock, DialogueFormatError, MAX_DIALOGUE_SIZE,
    decode_text, encode_text_unchecked,
)
from shared.tools.xgdisc import (
    FIELD_DIRECTORY, FIRST_FIELD_LOCAL_FILE, DiscFormatError, Mode2Image,
    directory_file_fat_index,
)
from shared.tools.xgfield import (
    FieldFormatError, build_field_preserving, parse_field,
)
from shared.tools.xgdialog_name_color import MARKER_BYTES, MARKER_TOKEN


# Exact labels are deliberately a cast allowlist, not an all-caps heuristic.
# This list establishes identity only when the complete first row is a name.
SPEAKER_LABELS = frozenset({
    *(f"<{name}>" for index, name in CHARACTER_NAMES.items() if index < 11),
    "Fei", "Elly", "Citan", "Bart", "Billy", "Rico", "Emeralda", "Chu-Chu",
    "Maria", "Hammer", "Ramsus", "Miang", "Krelian", "Grahf", "Id", "Lacan",
    "Sophia", "Karen", "Khan", "Wiseman", "Jessie", "Sigurd", "Margie",
    "Maison", "Hammer", "Dan", "Alice", "Timothy", "Yui", "Midori", "Lee",
    "Balthasar", "Taura", "Melchior", "Gaspar", "Nikolai", "Chu-Chu",
    "Dominia", "Tolone", "Seraphita", "Kelvena", "Shakhan", "Stein", "Ziko",
    "Primera", "Franz", "Big Joe", "Doc", "Emperor", "Cain", "Hammer",
    # Explicit labels observed in the configured USA retail dialogue inventory.
    "BP-Exchanger Girl", "Captain", "Receptionist", "Informationist", "Doctor",
    "Zephyr", "Sigmund", "Hans", "Gramps", "Mysterious Woman", "Bluecrystal",
    "Associate", "Imperial City Guard", "Renk", "Ol' man Bal", "Vance", "Stone",
    "Guard", "Stratski", "Soldier", "Vanderkaum", "Subordinate", "Erich",
    "Helmholz", "Rue", "Maitreya", "Battler", "Suzarn", "Shopkeep Johnny",
    "Kim", "Roni", "Emperor Cain", "Rene", "Kanna", "Mystery Girl",
    "Shevat Emissary", "Mysterious old man", "Lance", "Bishop Stone",
    "Imperial Guard", "Shevat Agent", "Informer",
    "<Perso1>", "<Perso2>", "<Perso3>",
})
_LEADING_DELAY = re.compile(r"^(?:<Delay:\d{1,3}>)*")
_TOKEN = re.compile(r"<[^<>]*>")


@dataclass(frozen=True)
class SpeakerDecision:
    status: str
    speaker: str | None = None
    first_row: str = ""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def retail_blocks(data: bytes) -> tuple[DialogueBlock, ...]:
    """Read the native directory, preserving every byte between its offsets.

    Unlike the authored-text validator, this allows unreachable data following
    Close, which occurs on retail discs. Structural offsets remain strict.
    """
    if len(data) < 8 or len(data) > MAX_DIALOGUE_SIZE:
        raise DialogueFormatError("Retail dialogue size is outside 8..65535")
    count = struct.unpack_from("<I", data)[0] + 1
    header_size = 4 + count * 4
    if header_size >= len(data):
        raise DialogueFormatError("Retail dialogue directory exceeds component")
    offsets = struct.unpack_from(f"<{count}H", data, 4)
    if offsets[0] != header_size or list(offsets) != sorted(offsets):
        raise DialogueFormatError("Retail dialogue offsets are not a monotonic directory")
    if offsets[-1] >= len(data):
        raise DialogueFormatError("Retail dialogue offset exceeds component")
    result = []
    dimensions = 4 + count * 2
    unique_offsets = sorted(set(offsets))
    ends = dict(zip(unique_offsets, unique_offsets[1:] + [len(data)]))
    for index, start in enumerate(offsets):
        end = ends[start]
        payload = data[start:end]
        text = decode_text(payload)
        if encode_text_unchecked(text) != payload:
            raise DialogueFormatError(f"Retail block {index} does not round-trip")
        width, height = data[dimensions + index * 2:dimensions + index * 2 + 2]
        result.append(DialogueBlock(index, width, height, start, payload, text))
    return tuple(result)


def speaker_decision(block: DialogueBlock) -> SpeakerDecision:
    """Classify a row without touching names in prose, menus, or later pages."""
    if "<Close>" not in block.text:
        return SpeakerDecision("terminal_control_review", first_row=block.text.split("\n")[0])
    live = block.text.split("<Close>", 1)[0]
    marked = live.startswith(MARKER_TOKEN)
    if marked:
        live = live[len(MARKER_TOKEN):]
    prefix = _LEADING_DELAY.match(live).end()
    head, separator, _body = live[prefix:].partition("\n")
    row = head.strip()
    if "<Opcode:01:" in live or "<Byte:05>" in live:
        return SpeakerDecision("choice", first_row=row)
    if "<New>" in live:
        return SpeakerDecision("multipage_review", first_row=row)
    if "<Opcode:0B:" in live or MARKER_TOKEN in live:
        return SpeakerDecision("existing_control_review", first_row=row)
    if not separator or row not in SPEAKER_LABELS:
        return SpeakerDecision("unidentified", first_row=row)
    # A native renamed party member occupies up to nine displayed characters.
    # This matters only for detecting a wrapped label: no dimensions change.
    label = _TOKEN.sub(lambda match: "X" * 9, row)
    if 2 * (len(label) + len(head) - len(head.lstrip())) > (block.width | 1):
        return SpeakerDecision("name_width_review", row, row)
    return SpeakerDecision("already_marked" if marked else "eligible", row, row)


def mark_dialogue(data: bytes, *, enabled: bool = True) -> tuple[bytes, dict]:
    """Add markers only; preserve original dimensions, IDs and all payload bytes."""
    blocks = retail_blocks(data)
    decisions = [speaker_decision(block) for block in blocks]
    groups = {}
    for block in blocks:
        groups.setdefault(block.offset, []).append(block.block_id)
    for indices in groups.values():
        if any(decisions[index].status != "eligible" for index in indices):
            for index in indices:
                if decisions[index].status == "eligible":
                    decisions[index] = SpeakerDecision("alias_review", decisions[index].speaker,
                                                       decisions[index].first_row)
    changed = [block.block_id for block, decision in zip(blocks, decisions)
               if enabled and decision.status == "eligible"]
    audit = {"blocks": len(blocks), "status_counts": dict(Counter(
        decision.status for decision in decisions)), "marked_block_ids": changed,
        "source_sha256": sha256(data)}
    if not changed:
        audit["result_sha256"] = audit["source_sha256"]
        return data, audit
    changed_offsets = {blocks[index].offset for index in changed}
    size = len(data) + len(changed_offsets) * len(MARKER_BYTES)
    if size > MAX_DIALOGUE_SIZE:
        raise DialogueFormatError(f"Yellow names would exceed u16 dialogue size: {size}")
    count = len(blocks)
    result = bytearray(data[:4 + count * 4])
    selected = set(changed)
    relocated = {}
    for block in blocks:
        if block.offset not in relocated:
            relocated[block.offset] = len(result)
            if block.offset in changed_offsets:
                result.extend(MARKER_BYTES)
            result.extend(block.payload)
        struct.pack_into("<H", result, 4 + block.block_id * 2, relocated[block.offset])
    output = bytes(result)
    for before, after in zip(blocks, retail_blocks(output)):
        expected = (MARKER_BYTES if before.block_id in selected else b"") + before.payload
        if after.payload != expected or (before.width, before.height) != (after.width, after.height):
            raise DialogueFormatError("Yellow-name rebuild changed existing content")
    audit["result_sha256"] = sha256(output)
    return output, audit


def field_entries(image: Mode2Image):
    """Resolve all complete field pairs using the disc's own directory table."""
    entries = image.read_index()
    directories = image.read_directories()
    start = directories[FIELD_DIRECTORY].first_file
    base = directory_file_fat_index(start, FIRST_FIELD_LOCAL_FILE)
    next_directory = min((item.first_file for item in directories if item.first_file > start),
                         default=len(entries))
    stop = next_directory - 1
    if stop <= base or stop > len(entries):
        raise DiscFormatError("Invalid field-directory extent")
    # Some retail tables have a final unpaired empty pad entry before directory
    # 16. Never treat the next directory's first record as field graphics.
    if (stop - base) % 2 and entries[stop - 1].kind != "empty":
        raise DiscFormatError("Field directory has an unpaired nonempty record")
    result = []
    for scene, index in enumerate(range(base, stop - 1, 2)):
        if entries[index].kind == "metadata":
            break  # Retail scene 768 starts the next archive resource group.
        result.append((scene, entries[index]))
    return result


def patch_disc_dialogue(
    image_path: Path | str, disc: int, *, yellow_names: bool = False,
    replacements: Mapping[int, bytes] | None = None, include_text: bool = False,
) -> tuple[dict[int, bytes], dict]:
    """Return canonical replacements and complete field audit without writing.

    Replacements supplied by a translation pass are used instead of donor
    bundles and carried forward, so optional presentation composes with text.
    The caller installs the shared executable renderer when enabling markers.
    """
    if disc not in (1, 2):
        raise ValueError("Expected disc 1 or 2")
    image = Mode2Image(image_path)
    output = dict(replacements or {})
    fields = []
    statuses = Counter()
    block_statuses = Counter()
    for scene, entry in field_entries(image):
        canonical = entry.index + (5 if disc == 2 else 0)
        record = {"field": scene, "canonical_id": canonical, "physical_id": entry.index}
        if entry.kind != "file" and canonical not in output:
            record["status"] = entry.kind
        else:
            source = output.get(canonical)
            if source is None:
                source = image.extract_entry(entry)
            record["bundle_sha256"] = sha256(source)
            try:
                if source == b"It's CDMAKE Dummy !\r\n\r\n ":
                    record["status"] = "disc_placeholder"
                    statuses.update([record["status"]])
                    fields.append(record)
                    continue
                parsed = parse_field(source)
                component = parsed.parts[7].data
                if not component or component[:4] == bytes.fromhex("ff ff 00 00"):
                    record["status"] = "no_dialogue"
                else:
                    result, details = mark_dialogue(component, enabled=yellow_names)
                    record.update(details)
                    block_statuses.update(details["status_counts"])
                    record["status"] = "changed" if result != component else "audited"
                    if include_text:
                        record["dialogue"] = [
                            {"block_id": block.block_id, "width": block.width,
                             "height": block.height, "text": block.text,
                             "payload_sha256": sha256(block.payload),
                             "speaker_status": speaker_decision(block).status}
                            for block in retail_blocks(component)]
                    if result != component:
                        parts = [part.data for part in parsed.parts]
                        parts[7] = result
                        output[canonical] = build_field_preserving(
                            source, parts, {7}, compact_changed=True)
                        record["result_bundle_sha256"] = sha256(output[canonical])
            except (FieldFormatError, DialogueFormatError) as exc:
                record["status"] = "review_required"
                record["error"] = str(exc)
        statuses.update([record["status"]])
        fields.append(record)
    audit = {"format": "xenogears-definitive-dialogue-audit-v1", "disc": disc,
             "image": str(image.path), "yellow_names": yellow_names,
             "field_slots": len(fields), "field_status_counts": dict(statuses),
             "block_status_counts": dict(block_statuses), "fields": fields,
             "coverage_note": "Field dialogue only; menus, battle text, movie subtitles, "
                              "inline speaker labels and multipage color require separate review.",
             "runtime_status": "not_playtested"}
    return output, audit


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--disc", type=int, choices=(1, 2), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-text", action="store_true")
    args = parser.parse_args(argv)
    _, audit = patch_disc_dialogue(args.image, args.disc, include_text=args.include_text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in audit.items() if key != "fields"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
