"""Import the Xenoverse Fan edition and audit its relationship to retail text.

This is deliberately not a blind transcript-to-ROM converter. Website passage
IDs describe a transcript, not field dialogue addresses. Candidate matches are
review evidence only; neither fuzzy matches nor source-only passages authorize
replacement of a game script, control byte, or dialogue block.

Run as ``python -m modules.definitive.translation fetch`` or ``audit-disc``.
The downloaded corpus lives in ignored output/, with a small checked-in report.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import struct
from typing import Any, Callable, Mapping, Sequence
import urllib.error
import urllib.request

from shared.tools import xgdialog, xgdisc, xgfield


SOURCE_URL = "https://xenoverse.world/#/xenogears/script"
SOURCE_ORIGIN = "https://xenoverse.world"
FAN_METHOD = "Faithful fan localization; Japanese-checked"
CORPUS_FORMAT = "xenogears-definitive-fan-corpus-v1"
MAPPING_FORMAT = "xenogears-definitive-reviewed-translation-v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE = ROOT / "output/definitive/translation"
DEFAULT_REPORT = Path(__file__).parent / "content/translation/source-audit.json"
SHA_PATTERN = re.compile(r"[0-9a-fA-F]{64}\Z")
STORY_PATTERN = re.compile(r"story\d{2}\Z")


class TranslationError(ValueError):
    """A source or proposed mapping is inconsistent with its evidence."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    # The website signs JSON.stringify(units); retain object order and Unicode.
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _valid_sha(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA_PATTERN.fullmatch(value))


def validate_alignment(document: Any, chapter_id: str) -> dict[str, Any]:
    """Validate the website's chapter schema without assigning ROM addresses."""
    if (not isinstance(document, dict) or document.get("schemaVersion") != 1
            or document.get("id") != chapter_id):
        raise TranslationError(f"Invalid alignment for chapter {chapter_id}")
    sources = document.get("sources", {}).get("japanese")
    if not isinstance(sources, list) or not sources:
        raise TranslationError(f"Chapter {chapter_id} has no Japanese source metadata")
    for source in sources:
        if (not isinstance(source, dict)
                or not STORY_PATTERN.fullmatch(str(source.get("storyId", "")))
                or not _valid_sha(source.get("sha256"))):
            raise TranslationError(f"Invalid source metadata in chapter {chapter_id}")
    identifiers: dict[str, set[str]] = {}
    for side in ("japanese", "official"):
        units = document.get("units", {}).get(side)
        if not isinstance(units, list):
            raise TranslationError(f"Chapter {chapter_id} lacks {side} units")
        identifiers[side] = set()
        for unit in units:
            if (not isinstance(unit, dict) or not isinstance(unit.get("id"), str)
                    or not unit["id"] or unit["id"] in identifiers[side]
                    or not isinstance(unit.get("text"), str)):
                raise TranslationError(f"Invalid/duplicate {side} passage in {chapter_id}")
            identifiers[side].add(unit["id"])
    rows = document.get("rows")
    if not isinstance(rows, list):
        raise TranslationError(f"Chapter {chapter_id} has no alignment rows")
    row_ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or row["id"] in row_ids:
            raise TranslationError(f"Invalid/duplicate row in chapter {chapter_id}")
        row_ids.add(row["id"])
        for side in identifiers:
            values = row.get(side)
            if not isinstance(values, list) or any(not isinstance(value, str) or value not in identifiers[side] for value in values):
                raise TranslationError(f"Foreign {side} passage in chapter {chapter_id}")
    return document


def validate_fan(document: Any, source: Mapping[str, Any]) -> dict[str, Any]:
    """Require the user's Fan edition, matching Japanese revision and text hash."""
    story_id = source["storyId"]
    if (not isinstance(document, dict) or document.get("schemaVersion") != 1
            or document.get("storyId") != story_id
            or document.get("sourceSha256") != source["sha256"]
            or document.get("translationMethod") != FAN_METHOD
            or document.get("provenance", {}).get("edition") != "fan"
            or not _valid_sha(document.get("provenance", {}).get("unitsSha256"))
            or not isinstance(document.get("units"), list) or not document["units"]):
        raise TranslationError(f"Fan edition/source integrity failed for {story_id}")
    seen: set[str] = set()
    for unit in document["units"]:
        if (not isinstance(unit, dict) or not isinstance(unit.get("id"), str)
                or not unit["id"].startswith(story_id + "-") or unit["id"] in seen
                or not isinstance(unit.get("text"), str)
                or not unit["text"].replace("▽", "").replace("▼", "").strip()):
            raise TranslationError(f"Invalid or repeated fan passage in {story_id}")
        seen.add(unit["id"])
    if sha256(_json_bytes(document["units"])) != document["provenance"]["unitsSha256"]:
        raise TranslationError(f"Fan text-integrity checksum failed for {story_id}")
    return document


def _download(url: str) -> bytes:
    if not url.startswith(SOURCE_ORIGIN + "/"):
        raise TranslationError(f"Unexpected source origin: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json,text/plain,*/*"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def discover_chapters(download: Callable[[str], bytes] = _download) -> tuple[list[str], dict[str, str]]:
    """Read the public application chapter catalogue; never execute website code."""
    landing = download(SOURCE_ORIGIN + "/")
    match = re.search(rb'<script[^>]+src="(/assets/index-[^"]+\.js)"', landing)
    if not match:
        raise TranslationError("Website entry bundle changed; chapter discovery needs review")
    entry_url = SOURCE_ORIGIN + match[1].decode("ascii")
    entry = download(entry_url)
    match = re.search(rb'assets/(ArchivePage-[A-Za-z0-9_-]+\.js)', entry)
    if not match:
        raise TranslationError("Website archive bundle changed; chapter discovery needs review")
    archive_url = SOURCE_ORIGIN + "/assets/" + match[1].decode("ascii")
    archive = download(archive_url)
    # The exported catalogue begins with the Opening Movie constructor. Locate
    # its name instead of relying on a particular minifier's variable spelling.
    match = re.search(rb'\[(\w+)\(-1,`Opening Movie`.*?\];', archive, re.DOTALL)
    if not match:
        raise TranslationError("Website chapter catalogue changed; review required")
    numbers = [int(number) for number in re.findall(rb'\b' + re.escape(match[1]) + rb'\((-?\d+),', match[0])]
    if not numbers or len(numbers) != len(set(numbers)) or any(number < -1 or number > 99 for number in numbers):
        raise TranslationError("Invalid website chapter catalogue")
    chapters = ["opening" if number == -1 else f"{number:02d}" for number in numbers]
    return chapters, {"entry_url": entry_url, "entry_sha256": sha256(entry), "catalogue_url": archive_url, "catalogue_sha256": sha256(archive)}


def corpus_audit(alignments: Sequence[Mapping[str, Any]], fans: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    translated = {unit["id"]: unit["text"] for fan in fans.values() for unit in fan["units"]}
    selected: set[str] = set()
    chapters = []
    for alignment in alignments:
        expected = {unit["id"] for unit in alignment["units"]["japanese"]}
        selected.update(expected)
        missing = sorted(expected.difference(translated))
        rows = alignment["rows"]
        chapters.append({"id": alignment["id"], "title": alignment.get("title"),
            "japanese_units": len(expected), "official_units": len(alignment["units"]["official"]),
            "fan_units_available": len(expected) - len(missing), "missing_fan_units": missing,
            "paired_rows": sum(bool(row["japanese"] and row["official"]) for row in rows),
            "japanese_only_rows": sum(bool(row["japanese"] and not row["official"]) for row in rows),
            "official_only_rows": sum(bool(row["official"] and not row["japanese"]) for row in rows),
            "review_needed_rows": sum(row.get("status") == "review-needed" for row in rows)})
    unusual = Counter(character for text in translated.values() for character in text if character not in xgdialog.PLAIN_ENCODE and character not in "\n\r▽▼")
    return {"source_url": SOURCE_URL, "edition": "fan", "translation_method": FAN_METHOD,
        "chapters": chapters, "chapter_count": len(chapters), "fan_story_count": len(fans),
        "fan_passage_count": len(translated), "selected_japanese_passage_count": len(selected),
        "selected_fan_passage_count": len(selected.intersection(translated)),
        "missing_selected_fan_passages": sorted(selected.difference(translated)),
        "fan_passages_outside_chapter_selections": len(set(translated).difference(selected)),
        "characters_requiring_explicit_game_encoding": dict(sorted(unusual.items())),
        "verified_rom_replacements": 0, "runtime_verified": False,
        "limitations": ["Transcript units are not ROM field/block addresses.",
            "Website coverage does not prove coverage of optional NPCs, menus, items, battle text, or FMV subtitles.",
            "Original script control bytes, name tokens, choices, pacing, width/height and page layout need per-block verification.",
            "No ROM text is changed by importing or auditing this corpus."]}


def fetch_corpus(cache_dir: Path = DEFAULT_CACHE, *, workers: int = 4,
                 download: Callable[[str], bytes] = _download) -> dict[str, Any]:
    """Fetch all catalogue alignments and available Fan assets with checksums."""
    cache_dir = Path(cache_dir)
    chapters, discovery = discover_chapters(download)
    assets: dict[str, dict[str, Any]] = {}

    def get_alignment(chapter: str) -> tuple[str, bytes, dict[str, Any]]:
        relative = f"aligned/{chapter}.json"
        raw = download(SOURCE_ORIGIN + "/assets/scripts/xenogears/" + relative)
        return relative, raw, validate_alignment(json.loads(raw), chapter)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        alignment_results = list(pool.map(get_alignment, chapters))
    alignments = [document for _, _, document in alignment_results]
    sources: dict[str, Mapping[str, Any]] = {}
    for alignment in alignments:
        for source in alignment["sources"]["japanese"]:
            old = sources.get(source["storyId"])
            if old and old["sha256"] != source["sha256"]:
                raise TranslationError(f"Conflicting Japanese source revisions for {source['storyId']}")
            sources[source["storyId"]] = source

    def get_fan(source: Mapping[str, Any]) -> tuple[str, bytes, dict[str, Any]] | None:
        relative = f"fan-retranslation/{source['storyId']}.json"
        try:
            raw = download(SOURCE_ORIGIN + "/assets/scripts/xenogears/" + relative)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            raise
        # A missing static asset can return the SPA HTML with status 200.
        if raw.lstrip().startswith((b"<!doctype", b"<!DOCTYPE", b"<html")):
            return None
        return relative, raw, validate_fan(json.loads(raw), source)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        fan_results = [result for result in pool.map(get_fan, sources.values()) if result is not None]
    for relative, raw, _ in alignment_results + fan_results:
        destination = cache_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        assets[relative] = {"url": SOURCE_ORIGIN + "/assets/scripts/xenogears/" + relative, "sha256": sha256(raw), "bytes": len(raw)}
    fans = {document["storyId"]: document for _, _, document in fan_results}
    audit = corpus_audit(alignments, fans)
    manifest = {"format": CORPUS_FORMAT, "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": SOURCE_URL, "discovery": discovery, "chapters": chapters, "assets": assets,
        "missing_fan_stories": sorted(set(sources).difference(fans))}
    _write_json(cache_dir / "manifest.json", manifest)
    audit.update({"fetched_at_utc": manifest["fetched_at_utc"], "corpus_manifest_sha256": sha256((cache_dir / "manifest.json").read_bytes()),
        "source_asset_count": len(assets), "source_bytes": sum(asset["bytes"] for asset in assets.values()),
        "missing_fan_stories": manifest["missing_fan_stories"], "source_assets": assets})
    _write_json(cache_dir / "audit.json", audit)
    return audit


def load_corpus(cache_dir: Path = DEFAULT_CACHE) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Load the pinned local import and reject modified or substituted assets."""
    cache_dir = Path(cache_dir).resolve()
    manifest = json.loads((cache_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != CORPUS_FORMAT:
        raise TranslationError("Unrecognized corpus manifest")
    documents = {}
    for relative, asset in manifest["assets"].items():
        path = (cache_dir / relative).resolve()
        if not path.is_relative_to(cache_dir):
            raise TranslationError("Corpus asset path leaves its cache directory")
        raw = path.read_bytes()
        if sha256(raw) != asset["sha256"]:
            raise TranslationError(f"Local corpus checksum mismatch: {relative}")
        documents[relative] = json.loads(raw)
    alignments = [validate_alignment(documents[f"aligned/{chapter}.json"], chapter) for chapter in manifest["chapters"]]
    fans = {}
    for alignment in alignments:
        for source in alignment["sources"]["japanese"]:
            relative = f"fan-retranslation/{source['storyId']}.json"
            if relative in documents:
                fans[source["storyId"]] = validate_fan(documents[relative], source)
    return alignments, fans


def normalized_dialogue(text: str, *, game_tokens: bool = False) -> str:
    """Conservative case-sensitive whitespace matching for review candidates."""
    if game_tokens:
        text = re.sub(r"<([^>]+)>", lambda match: match[1] if match[1] in xgdialog.CHARACTER_IDS else " ", text)
    else:
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        text = html.unescape(text)
    return " ".join(text.replace("▽", " ").replace("▼", " ").split())


def candidate_index(alignments: Sequence[Mapping[str, Any]], fans: Mapping[str, Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Index aligned official units with Fan IDs. Every result needs review."""
    translated_ids = {unit["id"] for fan in fans.values() for unit in fan["units"]}
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for alignment in alignments:
        official = {unit["id"]: unit for unit in alignment["units"]["official"]}
        for row in alignment["rows"]:
            if not row["official"] or not row["japanese"] or not set(row["japanese"]).issubset(translated_ids):
                continue
            # A complete row can map several transcript units to one game block.
            text = "\n".join(official[identifier]["text"] for identifier in row["official"])
            key = normalized_dialogue(text)
            if not key:
                continue
            index[key].append({"chapter_id": alignment["id"], "row_id": row["id"],
                "official_unit_ids": row["official"], "fan_unit_ids": row["japanese"],
                "alignment_status": row.get("status"), "verified": False})
    return dict(index)


def translation_content_key(text: str, *, game_tokens: bool = False) -> str:
    """Compare wording while allowing line wrapping and font punctuation forms.

    Straight/curly dialogue quotation marks are presentation, since the Fan
    transcript often omits closing quotes. All words and their order remain
    exact; editorial annotations are not silently removed.
    """
    text = text.translate(str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'",
        "…": "...", "—": "-", "–": "-", "‐": "-"}))
    if game_tokens:
        text = re.sub(r"<([^>]+)>", lambda match: match[1] if match[1] in xgdialog.CHARACTER_IDS else "\n" if match[1] in {"New", "Close"} else "", text)
    return " ".join(text.replace('"', "").replace("▽", " ").replace("▼", " ").split())


def compile_verified_field(source: bytes, mapping: Mapping[str, Any],
                           fans: Mapping[str, Mapping[str, Any]]) -> tuple[bytes, dict[str, Any]]:
    """Compile a statically reviewed field mapping with original-byte guards.

    This entry point requires explicit per-block layout and exact Fan wording.
    It preserves the complete sequence of retail control/name tokens, every
    untouched payload, all script IDs, and every non-dialogue field component.
    Runtime verification remains a separate requirement, never inferred here.
    """
    if (mapping.get("format") != MAPPING_FORMAT or mapping.get("review_status") != "static-reviewed"
            or not isinstance(mapping.get("review_evidence"), str) or not mapping["review_evidence"].strip()
            or mapping.get("source_field_sha256") != sha256(source)):
        raise TranslationError("Field mapping lacks matching source bytes and explicit static review")
    parsed = xgfield.parse_field(source)
    original = parsed.parts[7].data
    if mapping.get("source_dialogue_sha256") != sha256(original):
        raise TranslationError("Reviewed dialogue hash does not match source")
    blocks = xgdialog.parse_dialogue(original).blocks
    fan_units = {unit["id"]: unit for fan in fans.values() for unit in fan["units"]}
    records = mapping.get("blocks")
    if not isinstance(records, list) or not records:
        raise TranslationError("Reviewed mapping has no blocks")
    changes = {}
    for record in records:
        block_id = record.get("block_id")
        if type(block_id) is not int or block_id < 0 or block_id >= len(blocks) or block_id in changes:
            raise TranslationError("Invalid or duplicated reviewed block ID")
        before = blocks[block_id]
        if record.get("source_payload_sha256") != sha256(before.payload):
            raise TranslationError(f"Retail block {block_id} does not match reviewed payload")
        identifiers = record.get("fan_unit_ids")
        if (not isinstance(identifiers, list) or not identifiers
                or any(not isinstance(identifier, str) or identifier not in fan_units for identifier in identifiers)
                or len(set(identifiers)) != len(identifiers)):
            raise TranslationError(f"Missing or invalid Fan passage for block {block_id}")
        selected = [fan_units[identifier] for identifier in identifiers]
        if record.get("fan_units_sha256") != sha256(_json_bytes(selected)):
            raise TranslationError(f"Fan wording changed since block {block_id} was reviewed")
        replacement = record.get("text")
        if not isinstance(replacement, str):
            raise TranslationError(f"Missing reviewed token text for block {block_id}")
        if translation_content_key(replacement, game_tokens=True) != translation_content_key("\n".join(unit["text"] for unit in selected)):
            raise TranslationError(f"Block {block_id} changes the reviewed Fan wording")
        controls = lambda text: re.findall(r"<[^<>]+>", text)
        if controls(before.text) != controls(replacement):
            raise TranslationError(f"Block {block_id} changes retail control/name token sequence")
        width, height = record.get("width", before.width), record.get("height", before.height)
        if type(width) is not int or type(height) is not int or not 1 <= width <= 64 or not 1 <= height <= 4:
            raise TranslationError(f"Block {block_id} exceeds the reviewed field-window limits")
        for page in replacement.split("<New>"):
            # Dynamic names reserve their supported nine-character maximum.
            visible = re.sub(r"<([^>]+)>", lambda match: "X" * 9 if match[1] in xgdialog.CHARACTER_IDS else "", page)
            rows = visible.split("\n")
            if len(rows) > height or any(2 * len(row) > (width | 1) for row in rows):
                raise TranslationError(f"Block {block_id} does not fit its reviewed window")
        payload = xgdialog.encode_text(replacement)
        changes[block_id] = (width, height, payload)
    # Rebuild only the native offset/dimension directory and changed payloads.
    result = bytearray(original[:4 + 4 * len(blocks)])
    for before in blocks:
        width, height, payload = changes.get(before.block_id, (before.width, before.height, before.payload))
        if len(result) + len(payload) > xgdialog.MAX_DIALOGUE_SIZE:
            raise TranslationError("Reviewed translation exceeds the u16 dialogue limit")
        struct.pack_into("<H", result, 4 + 2 * before.block_id, len(result))
        dimension_offset = 4 + len(blocks) * 2 + before.block_id * 2
        result[dimension_offset:dimension_offset + 2] = bytes((width, height))
        result.extend(payload)
    component = bytes(result)
    rebuilt_blocks = xgdialog.parse_dialogue(component).blocks
    for before, after in zip(blocks, rebuilt_blocks):
        if before.block_id not in changes and (before.payload, before.width, before.height) != (after.payload, after.width, after.height):
            raise TranslationError("An unselected retail block changed during rebuild")
    parts = [part.data for part in parsed.parts]
    parts[7] = component
    rebuilt = xgfield.build_field_preserving(source, parts, {7}, compact_changed=True)
    reparsed = xgfield.parse_field(rebuilt)
    if any(before.data != after.data for index, (before, after) in enumerate(zip(parsed.parts, reparsed.parts)) if index != 7):
        raise TranslationError("Non-dialogue field content changed during translation")
    return rebuilt, {"changed_block_ids": sorted(changes), "source_field_sha256": sha256(source),
        "result_field_sha256": sha256(rebuilt), "source_dialogue_sha256": sha256(original),
        "result_dialogue_sha256": sha256(component), "untouched_blocks_preserved": True,
        "other_field_components_preserved": True, "retail_control_sequences_preserved": True,
        "runtime_status": "not_playtested"}


def audit_disc(image_path: Path, cache_dir: Path = DEFAULT_CACHE) -> dict[str, Any]:
    """Read all addressable field bundles and report exact normalized candidates."""
    from modules.definitive.dialogue import field_entries, retail_blocks

    alignments, fans = load_corpus(cache_dir)
    index = candidate_index(alignments, fans)
    image = xgdisc.Mode2Image(image_path)
    fields = field_entries(image)
    candidates, errors = [], []
    field_count = block_count = empty_count = 0
    placeholder_count = 0
    for field_id, entry in fields:
        fat_index = entry.index
        if entry.kind != "file":
            empty_count += 1
            continue
        try:
            source = image.extract_entry(entry)
            if source == b"It's CDMAKE Dummy !\r\n\r\n ":
                placeholder_count += 1
                continue
            field = xgfield.parse_field(source)
            component = field.parts[7].data
            field_count += 1
            if not component or component[:4] == bytes.fromhex("ff ff 00 00"):
                continue
            blocks = retail_blocks(component)
        except (xgfield.FieldFormatError, xgdialog.DialogueFormatError) as error:
            errors.append({"field_id": field_id, "fat_index": fat_index, "error": str(error)})
            continue
        block_count += len(blocks)
        for block in blocks:
            matches = index.get(normalized_dialogue(block.text.split("<Close>", 1)[0], game_tokens=True), [])
            if matches:
                candidates.append({"field_id": field_id, "fat_index": fat_index, "block_id": block.block_id,
                    "dialogue_sha256": sha256(component), "payload_sha256": sha256(block.payload),
                    "width": block.width, "height": block.height, "retail_text": block.text,
                    "matches": matches, "verified": False})
    return {"format": "xenogears-definitive-rom-translation-audit-v1", "image": str(image.path),
        "field_slots": len(fields), "parsed_fields": field_count, "empty_field_slots": empty_count,
        "placeholder_field_slots": placeholder_count, "parsed_dialogue_blocks": block_count,
        "candidate_block_count": len(candidates), "unique_candidate_block_count": sum(len(row["matches"]) == 1 for row in candidates),
        "verified_rom_replacements": 0, "runtime_verified": False, "errors": errors, "candidates": candidates,
        "limitations": ["Exact normalized transcript matching is candidate evidence, not an approved replacement.",
            "Short repeated dialogue and scene variants need field/script context review.",
            "This audit covers field component 07 only; other text stores and FMVs are outside this scan."]}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fetch = sub.add_parser("fetch", help="import all publicly listed Fan edition assets")
    fetch.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    fetch.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    fetch.add_argument("--workers", type=int, choices=range(1, 9), default=4)
    audit = sub.add_parser("audit-disc", help="read retail field text and prepare mapping candidates")
    audit.add_argument("image", type=Path)
    audit.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    audit.add_argument("--output", type=Path, required=True)
    compile_parser = sub.add_parser("compile-field", help="compile one explicitly reviewed field mapping")
    compile_parser.add_argument("image", type=Path)
    compile_parser.add_argument("mapping", type=Path)
    compile_parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    compile_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "fetch":
            report = fetch_corpus(args.cache, workers=args.workers)
            _write_json(args.report, report)
            print(json.dumps({key: value for key, value in report.items() if key not in {"source_assets", "chapters"}}, ensure_ascii=True, indent=2))
        elif args.command == "audit-disc":
            report = audit_disc(args.image, args.cache)
            _write_json(args.output, report)
            print(json.dumps({**{key: value for key, value in report.items() if key not in {"candidates", "errors"}}, "review_required_fields": len(report["errors"])}, ensure_ascii=True, indent=2))
        else:
            mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
            image = xgdisc.Mode2Image(args.image)
            field_id = mapping.get("field_id")
            if type(field_id) is not int or not 0 <= field_id < 730:
                raise TranslationError("Mapping must name a retail field ID in 0..729")
            start = image.read_directories()[xgdisc.FIELD_DIRECTORY].first_file
            fat_index = xgdisc.directory_file_fat_index(start, xgdisc.FIRST_FIELD_LOCAL_FILE + 2 * field_id)
            if mapping.get("fat_index") != fat_index:
                raise TranslationError("Mapping FAT address does not match the selected disc")
            if args.output.resolve() == image.path:
                raise TranslationError("A compiled field cannot overwrite the source disc")
            _, fans = load_corpus(args.cache)
            result, report = compile_verified_field(image.extract_entry(image.read_index()[fat_index]), mapping, fans)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(result)
            _write_json(args.output.with_suffix(".audit.json"), report)
            print(json.dumps(report, ensure_ascii=True, indent=2))
    except (TranslationError, OSError, json.JSONDecodeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
