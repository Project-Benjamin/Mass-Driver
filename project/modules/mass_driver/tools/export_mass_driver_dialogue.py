#!/usr/bin/env python3
"""Export the active Mass Driver dialogue and its provenance as Markdown.

The exporter intentionally follows the playable ``CLONES`` sequence, checked
against ``ROUTE`` and the staged manifest, rather than every
``*.authored.json`` file in the content directory.  That makes the main
transcript an exact inventory of the selected release while retaining an
appendix for older or alternate authored files that are not compiled into it.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
from types import ModuleType
from typing import Any, Iterable


AUTHORED_FORMAT = "xenogears-field-dialogue-authored-v1"
REPLACEMENT_FORMAT = "xenogears-field-dialogue-replacements-v1"
SPEAKER_TAGS = ("Elly", "Emeralda", "Citan")
CENTRAL_LIVE_DIALOGUE_IDS = frozenset(
    (0, 1, 11, 12, 20, *range(21, 33), 35, 36)
)
CENTRAL_DORMANT_REFERENCE_IDS = frozenset(range(2, 11))
CENTRAL_NO_EMITTED_REFERENCE_IDS = frozenset((*range(13, 20), 33, 34))


class DialogueExportError(RuntimeError):
    """Raised when the release inputs do not form one exact dialogue set."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DialogueExportError(f"Could not read JSON {path}: {exc}") from exc


def _load_builder(path: Path) -> ModuleType:
    module_name = "_mass_driver_dialogue_export_builder"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise DialogueExportError(f"Could not load builder module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    tools_path = str(path.parent)
    inserted = tools_path not in sys.path
    if inserted:
        sys.path.insert(0, tools_path)
    try:
        spec.loader.exec_module(module)
    finally:
        if inserted:
            sys.path.remove(tools_path)
    return module


def _relative_link(from_directory: Path, target: Path) -> str:
    return Path(
        os.path.relpath(target.resolve(), start=from_directory.resolve())
    ).as_posix()


def _markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _page_count(blocks: Iterable[dict[str, Any]]) -> int:
    return sum(1 + str(block["text"]).count("<New>") for block in blocks)


def _render_authored_text(text: str) -> str:
    """Make authored control tags readable without discarding information."""

    rendered = text.replace("\r\n", "\n").replace("\r", "\n")
    for speaker in SPEAKER_TAGS:
        rendered = rendered.replace(f"<{speaker}>", f"\n{speaker.upper()}:\n")
    rendered = rendered.replace("<New>", "\n\n----- next page -----\n\n")
    rendered = rendered.replace("<Close>", "\n\n[window closes]")
    rendered = re.sub(r"<(Opcode:[^>]+)>", r"[\1]", rendered)
    rendered = re.sub(r"<(Delay:[^>]+)>", r"[\1]", rendered)
    rendered = re.sub(r"\n{3,}", "\n\n", rendered)
    return rendered.strip()


def _validate_authored_document(path: Path, document: Any) -> list[dict[str, Any]]:
    if not isinstance(document, dict) or document.get("format") != AUTHORED_FORMAT:
        raise DialogueExportError(
            f"{path} is not an {AUTHORED_FORMAT} document"
        )
    if document.get("reconstruction") is not True:
        raise DialogueExportError(f"{path} is not marked as authored reconstruction")
    blocks = document.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise DialogueExportError(f"{path} has no dialogue blocks")
    ids: list[int] = []
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            raise DialogueExportError(f"{path} block {index} is not an object")
        block_id = block.get("id")
        if not isinstance(block_id, int) or block_id < 0:
            raise DialogueExportError(f"{path} block {index} has an invalid id")
        if not isinstance(block.get("text"), str):
            raise DialogueExportError(f"{path} block {block_id} has no text")
        if not isinstance(block.get("width"), int) or not isinstance(
            block.get("height"), int
        ):
            raise DialogueExportError(
                f"{path} block {block_id} has invalid window dimensions"
            )
        ids.append(block_id)
    if len(ids) != len(set(ids)):
        raise DialogueExportError(f"{path} contains duplicate block ids")
    return blocks


def _validate_replacement_document(
    path: Path, document: Any
) -> list[dict[str, Any]]:
    if not isinstance(document, dict) or document.get("format") != REPLACEMENT_FORMAT:
        raise DialogueExportError(
            f"{path} is not an {REPLACEMENT_FORMAT} document"
        )
    replacements = document.get("replacements")
    if not isinstance(replacements, list) or not replacements:
        raise DialogueExportError(f"{path} has no dialogue replacements")
    if document.get("block_count") != len(replacements):
        raise DialogueExportError(
            f"{path} replacement count disagrees with block_count"
        )
    ids: list[int] = []
    for index, replacement in enumerate(replacements):
        if not isinstance(replacement, dict):
            raise DialogueExportError(
                f"{path} replacement {index} is not an object"
            )
        block_id = replacement.get("id")
        if not isinstance(block_id, int) or block_id < 0:
            raise DialogueExportError(
                f"{path} replacement {index} has an invalid id"
            )
        if not isinstance(replacement.get("text"), str):
            raise DialogueExportError(
                f"{path} replacement {block_id} has no text"
            )
        ids.append(block_id)
    if len(ids) != len(set(ids)):
        raise DialogueExportError(f"{path} contains duplicate replacement ids")
    return replacements


def _manifest_jobs_by_target(manifest: Any) -> dict[int, dict[str, Any]]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("jobs"), list):
        raise DialogueExportError("Stage manifest has no jobs array")
    jobs: dict[int, dict[str, Any]] = {}
    for job in manifest["jobs"]:
        if not isinstance(job, dict) or job.get("clone") is None:
            continue
        target = job.get("target_field")
        if not isinstance(target, int) or target in jobs:
            raise DialogueExportError(
                f"Stage manifest has an invalid or duplicate clone target {target!r}"
            )
        jobs[target] = job
    return jobs


def _build_export(args: argparse.Namespace) -> tuple[str, dict[str, int]]:
    workspace = args.workspace.resolve()
    builder_path = (workspace / args.builder).resolve()
    dialogue_root = (workspace / args.dialogue_root).resolve()
    stage_root = (workspace / args.stage_root).resolve()
    manifest_path = (workspace / args.manifest).resolve()
    metadata_path = (workspace / args.metadata).resolve()
    legacy_recipe_path = (workspace / args.legacy_recipe).resolve()
    output_path = (workspace / args.output).resolve()
    version_label = args.version.upper()

    builder = _load_builder(builder_path)
    specs = tuple(getattr(builder, "CLONES", ()))
    if not specs:
        raise DialogueExportError("Builder exposes no active CLONES")
    authored_compiler = getattr(builder, "_authored_dialogue", None)
    if not callable(authored_compiler):
        raise DialogueExportError("Builder exposes no authored-dialogue compiler")
    target_fields = [spec.target_field for spec in specs]
    if len(target_fields) != len(set(target_fields)):
        raise DialogueExportError("Builder has duplicate active target fields")
    if tuple(target_fields) != tuple(getattr(builder, "ROUTE", ())):
        raise DialogueExportError("Builder CLONES are not in playable ROUTE order")

    manifest = _load_json(manifest_path)
    jobs = _manifest_jobs_by_target(manifest)
    if set(jobs) != set(target_fields):
        raise DialogueExportError(
            "Stage manifest clone targets do not match the active builder specs"
        )
    manifest_clone_order = tuple(
        job["target_field"]
        for job in manifest["jobs"]
        if isinstance(job, dict) and job.get("clone") is not None
    )
    if manifest_clone_order != tuple(target_fields):
        raise DialogueExportError(
            "Stage manifest clone jobs are not in playable ROUTE order"
        )
    metadata = _load_json(metadata_path)
    expected_version = args.version.lower()
    releases = [
        metadata.get(key, {})
        for key in ("development_candidate", "current_release", "release")
    ]
    release_versions = [
        str(release.get("version", "")).lower()
        for release in releases
        if isinstance(release, dict) and release.get("version")
    ]
    if expected_version not in release_versions:
        raise DialogueExportError(
            f"Metadata releases are {release_versions!r}, expected {expected_version!r}"
        )
    if metadata.get("route_field_count") != len(specs):
        raise DialogueExportError(
            "Metadata route_field_count does not match the active builder specs"
        )

    active: list[dict[str, Any]] = []
    active_source_names: set[str] = set()
    total_blocks = 0
    total_pages = 0
    total_compiled_bytes = 0
    speaker_counts = {speaker: 0 for speaker in SPEAKER_TAGS}

    for route_index, spec in enumerate(specs, start=1):
        source_path = dialogue_root / spec.dialogue_file
        source_document = _load_json(source_path)
        blocks = _validate_authored_document(source_path, source_document)
        if spec.target_field == 728:
            classified_ids = (
                CENTRAL_LIVE_DIALOGUE_IDS
                | CENTRAL_DORMANT_REFERENCE_IDS
                | CENTRAL_NO_EMITTED_REFERENCE_IDS
            )
            actual_ids = {int(block["id"]) for block in blocks}
            if actual_ids != classified_ids:
                raise DialogueExportError(
                    "Central Control blocks do not match the exhaustive V158 "
                    "reference classification"
                )
        source_hash = _sha256(source_path)
        active_source_names.add(source_path.name)

        job = jobs[spec.target_field]
        job_source = Path(str(job.get("dialogue_spec", ""))).resolve()
        if job_source != source_path.resolve():
            raise DialogueExportError(
                f"Field {spec.target_field} manifest source {job_source} does not "
                f"match {source_path}"
            )
        compiled_path = stage_root / "clones" / f"field_{spec.target_field}" / "07_dialogue.bin"
        if not compiled_path.is_file():
            raise DialogueExportError(f"Missing compiled dialogue {compiled_path}")
        compiled_payload = compiled_path.read_bytes()
        try:
            rebuilt_payload = authored_compiler(source_document)
        except Exception as exc:
            raise DialogueExportError(
                f"Could not compile authored dialogue {source_path}: {exc}"
            ) from exc
        if rebuilt_payload != compiled_payload:
            raise DialogueExportError(
                f"Field {spec.target_field} authored source does not compile "
                "byte-for-byte to the staged dialogue component"
            )
        compiled_size = len(compiled_payload)
        compiled_hash = _sha256(compiled_path)
        if compiled_size != job.get("dialogue_size") or compiled_hash != job.get(
            "dialogue_sha256"
        ):
            raise DialogueExportError(
                f"Field {spec.target_field} compiled dialogue disagrees with manifest"
            )

        pages = _page_count(blocks)
        total_blocks += len(blocks)
        total_pages += pages
        total_compiled_bytes += compiled_size
        for block in blocks:
            text = str(block["text"])
            for speaker in SPEAKER_TAGS:
                speaker_counts[speaker] += text.count(f"<{speaker}>")

        active.append(
            {
                "route_index": route_index,
                "role": spec.role,
                "source_field": spec.source_field,
                "target_field": spec.target_field,
                "source_bundle_id": spec.source_bundle_id,
                "target_bundle_id": spec.target_bundle_id,
                "source_path": source_path,
                "source_hash": source_hash,
                "compiled_path": compiled_path,
                "compiled_size": compiled_size,
                "compiled_hash": compiled_hash,
                "blocks": blocks,
                "pages": pages,
            }
        )

    all_authored_paths = sorted(dialogue_root.glob("*.authored.json"))
    inactive: list[dict[str, Any]] = []
    for source_path in all_authored_paths:
        if source_path.name in active_source_names:
            continue
        source_document = _load_json(source_path)
        blocks = _validate_authored_document(source_path, source_document)
        inactive.append(
            {
                "source_path": source_path,
                "source_hash": _sha256(source_path),
                "blocks": len(blocks),
                "pages": _page_count(blocks),
            }
        )

    replacement_paths = sorted(dialogue_root.glob("*.replacements.json"))
    if legacy_recipe_path.is_file():
        replacement_paths.append(legacy_recipe_path)
    legacy_replacements: list[dict[str, Any]] = []
    for source_path in replacement_paths:
        source_document = _load_json(source_path)
        replacements = _validate_replacement_document(source_path, source_document)
        legacy_replacements.append(
            {
                "source_path": source_path,
                "source_hash": _sha256(source_path),
                "source_size": source_document.get("source_size"),
                "source_dialogue_hash": source_document.get("source_sha256"),
                "blocks": len(replacements),
                "pages": _page_count(replacements),
            }
        )

    output_directory = output_path.parent
    lines: list[str] = [
        f"# Mass Driver {version_label} dialogue and source provenance",
        "",
        "> Generated from the selected staged build. This transcript covers the "
        "Mass Driver standalone route, not the untouched retail Xenogears Disc 2 "
        "script outside that route.",
        "",
        "## Scope and provenance",
        "",
        f"- Active dialogue-bearing fields: **{len(active)}**",
        f"- Authored source files used by {version_label}: **{len(active_source_names)}**",
        f"- Tracked custom-dialogue JSON sources: **{len(active_source_names) + len(inactive) + len(legacy_replacements)}** "
        f"({len(active_source_names)} active authored, {len(inactive)} inactive authored, "
        f"{len(legacy_replacements)} legacy replacement-schema)",
        f"- Dialogue blocks: **{total_blocks}**",
        f"- Text pages (`<New>` delimited): **{total_pages}**",
        f"- Compiled dialogue bytes: **{total_compiled_bytes:,}**",
        "- Source-to-stage recompilation: **all active sources verified byte-for-byte**",
        f"- Tagged speaker cues: Elly **{speaker_counts['Elly']}**, Emeralda "
        f"**{speaker_counts['Emeralda']}**, Citan **{speaker_counts['Citan']}**",
        "",
        "Every transcript line below comes from the linked `*.authored.json` "
        "file. Each of those files is explicitly marked `reconstruction: true`. "
        "The listed retail field is the room/script donor used to construct the "
        "playable field; it is **not** a claim that the custom wording was copied "
        "from retail dialogue.",
        "",
        "Control tags are rendered as follows: `<New>` becomes `next page`, "
        "`<Close>` becomes `window closes`, speaker tags become uppercase labels, "
        "and opcode/delay tags remain visible in square brackets.",
        "A status of `compiled` means the block is present in the release dialogue "
        "component; it does not imply that every conditional branch is encountered "
        "during one playthrough. Central Control has an additional exhaustive static "
        "reference classification: `statically reachable` means an emitted VM path "
        "can reach the block under some valid flag/input state, not that a human test "
        "traversed it.",
        "",
        "### Release source ledger",
        "",
        f"- Stage manifest: `{manifest_path.relative_to(workspace).as_posix()}` - "
        f"`{_sha256(manifest_path)}`",
        f"- Reconstruction metadata: [{_markdown_cell(metadata_path.name)}]"
        f"({_relative_link(output_directory, metadata_path)}) - "
        f"`{_sha256(metadata_path)}`",
        f"- Builder mapping: [{_markdown_cell(builder_path.name)}]"
        f"({_relative_link(output_directory, builder_path)}) - "
        f"`{_sha256(builder_path)}`",
        "",
        "## Active field index",
        "",
        f"| Route | {version_label} field | Room | Retail donor | Blocks / pages | Text source | Compiled dialogue |",
        "|---:|---:|---|---:|---:|---|---|",
    ]

    for item in active:
        source_path = item["source_path"]
        compiled_path = item["compiled_path"]
        source_link = _relative_link(output_directory, source_path)
        lines.append(
            "| "
            f"{item['route_index']} | {item['target_field']} | "
            f"{_markdown_cell(item['role'])} | {item['source_field']} | "
            f"{len(item['blocks'])} / {item['pages']} | "
            f"[{source_path.name}]({source_link}) | "
            f"{item['compiled_size']:,} bytes "
            f"`{item['compiled_hash'][:12]}...` |"
        )

    lines.extend(["", "## Complete active transcript", ""])
    for item in active:
        source_path = item["source_path"]
        compiled_path = item["compiled_path"]
        lines.extend(
            [
                f"### {item['route_index']:02d}. Field {item['target_field']} - {item['role']}",
                "",
                f"- Dialogue text source: [{source_path.name}]"
                f"({_relative_link(output_directory, source_path)})",
                f"- Source SHA-256: `{item['source_hash']}`",
                f"- Retail room/script donor: field **{item['source_field']}**, "
                f"canonical bundle **{item['source_bundle_id']}**",
                f"- {version_label} destination: field **{item['target_field']}**, "
                f"canonical bundle **{item['target_bundle_id']}**",
                f"- Compiled component: "
                f"`{compiled_path.relative_to(workspace).as_posix()}`, "
                f"{item['compiled_size']:,} bytes, `{item['compiled_hash']}`",
                f"- Inventory: **{len(item['blocks'])} blocks / {item['pages']} pages**",
                "",
            ]
        )
        for block in item["blocks"]:
            block_id = block["id"]
            status = f"compiled into {version_label}"
            if item["target_field"] == 728:
                if block_id in CENTRAL_LIVE_DIALOGUE_IDS:
                    status = f"compiled; statically reachable in {version_label}"
                elif block_id in CENTRAL_DORMANT_REFERENCE_IDS:
                    status = "compiled; dormant/orphan-reference-only"
                elif block_id in CENTRAL_NO_EMITTED_REFERENCE_IDS:
                    status = "compiled; no emitted F5/D2 reference"
                else:
                    raise DialogueExportError(
                        f"Central Control block {block_id} has no reference classification"
                    )
            manual = "yes" if block.get("manual_wrap") is True else "no"
            lines.extend(
                [
                    f"#### Block {block_id}",
                    "",
                    f"- Source locator: `{source_path.relative_to(workspace).as_posix()} -> blocks[id={block_id}]`",
                    f"- Window: {block['width']} x {block['height']}; manual wrap: {manual}",
                    f"- Status: {status}",
                    "",
                    "```text",
                    _render_authored_text(str(block["text"])),
                    "```",
                    "",
                ]
            )

    inactive_blocks = sum(item["blocks"] for item in inactive)
    inactive_pages = sum(item["pages"] for item in inactive)
    lines.extend(
        [
            f"## Appendix: authored files not selected by {version_label}",
            "",
            f"These **{len(inactive)}** files ({inactive_blocks} blocks / "
            f"{inactive_pages} pages) remain in the content directory as older, "
            "alternate, or otherwise non-selected authored sources. Their text is "
            f"not part of the active {version_label} route and is therefore not duplicated in "
            "the main transcript.",
            "",
            "| Authored source | Blocks | Pages | SHA-256 |",
            "|---|---:|---:|---|",
        ]
    )
    for item in inactive:
        source_path = item["source_path"]
        lines.append(
            f"| [{source_path.name}]({_relative_link(output_directory, source_path)}) "
            f"| {item['blocks']} | {item['pages']} | `{item['source_hash']}` |"
        )

    legacy_replacement_count = sum(item["blocks"] for item in legacy_replacements)
    legacy_replacement_pages = sum(item["pages"] for item in legacy_replacements)
    lines.extend(
        [
            "",
            "## Appendix: legacy replacement-schema sources",
            "",
            f"These **{len(legacy_replacements)}** files contain "
            f"{legacy_replacement_count} replacement records / "
            f"{legacy_replacement_pages} pages. They belong to superseded Mass "
            "Driver routes or the original graybox recipe and are not consumed by "
            f"the active {version_label} builder.",
            "",
            "| Replacement source | Records | Pages | Bound retail source | File SHA-256 |",
            "|---|---:|---:|---|---|",
        ]
    )
    for item in legacy_replacements:
        source_path = item["source_path"]
        bound_source = (
            f"{item['source_size']} bytes / `{item['source_dialogue_hash']}`"
            if isinstance(item["source_size"], int)
            and isinstance(item["source_dialogue_hash"], str)
            else "unspecified"
        )
        lines.append(
            f"| [{source_path.relative_to(workspace).as_posix()}]"
            f"({_relative_link(output_directory, source_path)}) | "
            f"{item['blocks']} | {item['pages']} | {bound_source} | "
            f"`{item['source_hash']}` |"
        )

    lines.extend(
        [
            "",
            "## Reproduction",
            "",
            "From the workspace root:",
            "",
            "```powershell",
            "python tools/export_mass_driver_dialogue.py",
            "```",
            "",
            "The exporter rejects missing sources, duplicate block IDs, a release "
            "version mismatch, a builder/manifest field mismatch, authored source "
            "that does not recompile byte-for-byte, or compiled dialogue bytes that "
            "do not match the selected stage manifest.",
            "",
        ]
    )

    stats = {
        "active_fields": len(active),
        "active_sources": len(active_source_names),
        "blocks": total_blocks,
        "pages": total_pages,
        "compiled_bytes": total_compiled_bytes,
        "inactive_sources": len(inactive),
        "inactive_blocks": inactive_blocks,
        "inactive_pages": inactive_pages,
        "legacy_replacement_sources": len(legacy_replacements),
        "legacy_replacements": legacy_replacement_count,
        "legacy_replacement_pages": legacy_replacement_pages,
    }
    return "\n".join(lines), stats


def _parser() -> argparse.ArgumentParser:
    workspace = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=workspace)
    parser.add_argument("--version", required=True, help="Release matching the staged dialogue and metadata")
    parser.add_argument("--builder", type=Path, default=Path("modules/mass_driver/build.py"))
    parser.add_argument("--dialogue-root", type=Path, default=Path("modules/mass_driver/content"))
    parser.add_argument("--stage-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("modules/mass_driver/content/reconstruction_metadata.json"),
    )
    parser.add_argument(
        "--legacy-recipe",
        type=Path,
        default=Path("recipes/mass_driver_control_dialogue.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination for this release's transcript",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    output_path = (args.workspace.resolve() / args.output).resolve()
    try:
        payload, stats = _build_export(args)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8", newline="\n")
    except DialogueExportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {output_path}")
    print(
        "Active: "
        f"{stats['active_fields']} fields, {stats['blocks']} blocks, "
        f"{stats['pages']} pages, {stats['compiled_bytes']} compiled bytes"
    )
    print(
        "Inactive appendix: "
        f"{stats['inactive_sources']} files, {stats['inactive_blocks']} blocks, "
        f"{stats['inactive_pages']} pages"
    )
    print(
        "Legacy replacement appendix: "
        f"{stats['legacy_replacement_sources']} files, "
        f"{stats['legacy_replacements']} replacements, "
        f"{stats['legacy_replacement_pages']} pages"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
