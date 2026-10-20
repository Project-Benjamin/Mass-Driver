#!/usr/bin/env python3
"""Build the reproducible Mass-Driver graybox replacement files.

The tracked recipe describes every field clone and every size-preserving ATEL
redirect.  Inputs are unpacked field directories produced by ``xgfield.py``
plus their paired graphics files.  This tool only writes to ``--output`` (and,
when explicitly requested, a separate ``--disc-output``); it never writes to
the recipe inputs or source disc.

The default recipe's foot-only route is:

    retail 633 -> scene 724 (entry)
    retail 634 -> scene 721 (hub)
    retail 631 -> scene 726 (control/return)

Use ``--build-disc`` only after reviewing the replacement manifest.  Without
that flag the tool creates replacement files but does not invoke Xenoiso.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Mapping, Sequence

# ``python tools/build_mass_driver_graybox.py`` puts only ``tools`` on the
# import path.  Add the project root so both direct CLI use and module imports
# resolve the existing ``tools.*`` modules identically.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from shared.tools.xgatel import AtelFormatError, AtelScript, patch_transition
from shared.tools.xgfield import (
    FieldFormatError,
    STREAM_NAMES,
    build_field,
    parse_field,
)
from shared.tools.xgdialog import DialogueFormatError, rebuild_dialogue


RECIPE_FORMAT = "xenogears-mass-driver-graybox-v1"
OUTPUT_FORMAT = "xenogears-mass-driver-graybox-output-v1"
SCRIPT_COMPONENT = "05_scripts.bin"


class GrayboxBuildError(RuntimeError):
    """Raised when a recipe or build request is unsafe or inconsistent."""


@dataclass(frozen=True)
class TransitionPatch:
    pc: int
    expected_field: int
    expected_parameter: int
    new_field: int
    new_parameter: int
    note: str = ""


@dataclass(frozen=True)
class BytePatch:
    pc: int
    expected: bytes
    replacement: bytes
    note: str = ""


@dataclass(frozen=True)
class HookSpec:
    source_field: int
    canonical_bundle_id: int
    bundle_directory: Path
    script_sha256: str
    patches: tuple[TransitionPatch, ...]
    byte_patches: tuple[BytePatch, ...]


@dataclass(frozen=True)
class CloneSpec:
    role: str
    source_field: int
    target_field: int
    source_bundle_id: int
    source_graphics_id: int
    target_bundle_id: int
    target_graphics_id: int
    bundle_directory: Path
    graphics_file: Path
    script_sha256: str
    graphics_sha256: str
    dialogue_spec: Path | None
    patches: tuple[TransitionPatch, ...]
    byte_patches: tuple[BytePatch, ...]


@dataclass(frozen=True)
class GrayboxRecipe:
    name: str
    notes: tuple[str, ...]
    hook: HookSpec
    clones: tuple[CloneSpec, ...]


@dataclass(frozen=True)
class PreparedBundle:
    label: str
    source_directory: Path
    clone_directory_name: str
    patched_script: bytes
    packed_bundle: bytes
    bundle_id: int
    bundle_filename: str
    patches: tuple[TransitionPatch, ...]
    byte_patches: tuple[BytePatch, ...]
    patched_dialogue: bytes | None = None
    dialogue_spec: Path | None = None
    graphics_source: Path | None = None
    graphics_data: bytes | None = None
    graphics_id: int | None = None
    graphics_filename: str | None = None


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _integer(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise GrayboxBuildError(f"{context} must be an integer")
    if value < 0 or value > 0x7FFF:
        raise GrayboxBuildError(f"{context} is outside 0..32767: {value}")
    return value


def _text(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GrayboxBuildError(f"{context} must be a non-empty string")
    return value


def _sha256_text(value: Any, context: str) -> str:
    result = _text(value, context).lower()
    if len(result) != 64 or any(character not in "0123456789abcdef" for character in result):
        raise GrayboxBuildError(f"{context} must be a 64-digit SHA-256 hash")
    return result


def _mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise GrayboxBuildError(f"{context} must be an object")
    return value


def _sequence(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise GrayboxBuildError(f"{context} must be an array")
    return value


def _relative_path(value: Any, context: str) -> Path:
    result = Path(_text(value, context))
    if result.is_absolute() or ".." in result.parts:
        raise GrayboxBuildError(f"{context} must stay relative to --input-root")
    return result


def _parse_patch(value: Any, context: str) -> TransitionPatch:
    item = _mapping(value, context)
    return TransitionPatch(
        pc=_integer(item.get("pc"), f"{context}.pc"),
        expected_field=_integer(
            item.get("expected_field"), f"{context}.expected_field"
        ),
        expected_parameter=_integer(
            item.get("expected_parameter"), f"{context}.expected_parameter"
        ),
        new_field=_integer(item.get("new_field"), f"{context}.new_field"),
        new_parameter=_integer(
            item.get("new_parameter"), f"{context}.new_parameter"
        ),
        note=str(item.get("note", "")),
    )


def _parse_patches(value: Any, context: str) -> tuple[TransitionPatch, ...]:
    patches = tuple(
        _parse_patch(item, f"{context}[{index}]")
        for index, item in enumerate(_sequence(value, context))
    )
    if not patches:
        raise GrayboxBuildError(f"{context} must contain at least one patch")
    pcs = [patch.pc for patch in patches]
    if len(pcs) != len(set(pcs)):
        raise GrayboxBuildError(f"{context} contains a duplicate PC")
    return patches


def _hex_bytes(value: Any, context: str) -> bytes:
    source = _text(value, context).replace(" ", "")
    if len(source) % 2:
        raise GrayboxBuildError(f"{context} must contain complete hexadecimal bytes")
    try:
        result = bytes.fromhex(source)
    except ValueError as exc:
        raise GrayboxBuildError(f"{context} is not valid hexadecimal") from exc
    if not result:
        raise GrayboxBuildError(f"{context} must not be empty")
    return result


def _parse_byte_patch(value: Any, context: str) -> BytePatch:
    item = _mapping(value, context)
    expected = _hex_bytes(item.get("expected"), f"{context}.expected")
    replacement = _hex_bytes(item.get("replacement"), f"{context}.replacement")
    if len(expected) != len(replacement):
        raise GrayboxBuildError(
            f"{context} expected and replacement byte strings must have equal length"
        )
    return BytePatch(
        pc=_integer(item.get("pc"), f"{context}.pc"),
        expected=expected,
        replacement=replacement,
        note=str(item.get("note", "")),
    )


def _parse_byte_patches(value: Any, context: str) -> tuple[BytePatch, ...]:
    patches = tuple(
        _parse_byte_patch(item, f"{context}[{index}]")
        for index, item in enumerate(_sequence(value, context))
    )
    pcs = [patch.pc for patch in patches]
    if len(pcs) != len(set(pcs)):
        raise GrayboxBuildError(f"{context} contains a duplicate PC")
    return patches


def load_recipe(path: Path | str) -> GrayboxRecipe:
    recipe_path = Path(path)
    try:
        source = json.loads(recipe_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise GrayboxBuildError(f"Invalid recipe JSON: {exc}") from exc
    root = _mapping(source, "recipe")
    if root.get("format") != RECIPE_FORMAT:
        raise GrayboxBuildError(
            f"Unsupported recipe format: {root.get('format')!r}; expected {RECIPE_FORMAT}"
        )

    raw_notes = _sequence(root.get("notes", []), "recipe.notes")
    notes = tuple(_text(note, f"recipe.notes[{index}]") for index, note in enumerate(raw_notes))

    raw_hook = _mapping(root.get("hook"), "recipe.hook")
    hook = HookSpec(
        source_field=_integer(raw_hook.get("source_field"), "recipe.hook.source_field"),
        canonical_bundle_id=_integer(
            raw_hook.get("canonical_bundle_id"), "recipe.hook.canonical_bundle_id"
        ),
        bundle_directory=_relative_path(
            raw_hook.get("bundle_directory"), "recipe.hook.bundle_directory"
        ),
        script_sha256=_sha256_text(
            raw_hook.get("script_sha256"), "recipe.hook.script_sha256"
        ),
        patches=_parse_patches(raw_hook.get("patches"), "recipe.hook.patches"),
        byte_patches=_parse_byte_patches(
            raw_hook.get("byte_patches", []), "recipe.hook.byte_patches"
        ),
    )

    clones = []
    for index, raw_value in enumerate(_sequence(root.get("clones"), "recipe.clones")):
        context = f"recipe.clones[{index}]"
        raw = _mapping(raw_value, context)
        raw_dialogue_spec = raw.get("dialogue_spec")
        dialogue_spec = None
        if raw_dialogue_spec is not None:
            relative_dialogue_spec = _relative_path(
                raw_dialogue_spec, f"{context}.dialogue_spec"
            )
            dialogue_spec = (recipe_path.parent / relative_dialogue_spec).resolve()
            if not _inside(dialogue_spec, recipe_path.parent.resolve()):
                raise GrayboxBuildError(
                    f"{context}.dialogue_spec escapes the recipe directory"
                )
        clones.append(
            CloneSpec(
                role=_text(raw.get("role"), f"{context}.role"),
                source_field=_integer(raw.get("source_field"), f"{context}.source_field"),
                target_field=_integer(raw.get("target_field"), f"{context}.target_field"),
                source_bundle_id=_integer(
                    raw.get("source_bundle_id"), f"{context}.source_bundle_id"
                ),
                source_graphics_id=_integer(
                    raw.get("source_graphics_id"), f"{context}.source_graphics_id"
                ),
                target_bundle_id=_integer(
                    raw.get("target_bundle_id"), f"{context}.target_bundle_id"
                ),
                target_graphics_id=_integer(
                    raw.get("target_graphics_id"), f"{context}.target_graphics_id"
                ),
                bundle_directory=_relative_path(
                    raw.get("bundle_directory"), f"{context}.bundle_directory"
                ),
                graphics_file=_relative_path(
                    raw.get("graphics_file"), f"{context}.graphics_file"
                ),
                script_sha256=_sha256_text(
                    raw.get("script_sha256"), f"{context}.script_sha256"
                ),
                graphics_sha256=_sha256_text(
                    raw.get("graphics_sha256"), f"{context}.graphics_sha256"
                ),
                dialogue_spec=dialogue_spec,
                patches=_parse_patches(raw.get("patches"), f"{context}.patches"),
                byte_patches=_parse_byte_patches(
                    raw.get("byte_patches", []), f"{context}.byte_patches"
                ),
            )
        )
    if not clones:
        raise GrayboxBuildError("recipe.clones must contain at least one clone")

    target_fields = [clone.target_field for clone in clones]
    if len(target_fields) != len(set(target_fields)):
        raise GrayboxBuildError("recipe.clones contains a duplicate target field")
    replacement_ids = [hook.canonical_bundle_id]
    for clone in clones:
        replacement_ids.extend((clone.target_bundle_id, clone.target_graphics_id))
    if len(replacement_ids) != len(set(replacement_ids)):
        raise GrayboxBuildError("recipe contains a duplicate replacement canonical ID")

    return GrayboxRecipe(
        name=_text(root.get("name"), "recipe.name"),
        notes=notes,
        hook=hook,
        clones=tuple(clones),
    )


def apply_transition_patches(
    data: bytes, patches: Sequence[TransitionPatch]
) -> bytes:
    """Apply checked ATEL edits and assert that their byte length never changes."""

    result = data
    original_size = len(data)
    for item in patches:
        result = patch_transition(
            result,
            item.pc,
            item.expected_field,
            item.expected_parameter,
            item.new_field,
            item.new_parameter,
        )
        if len(result) != original_size:
            raise GrayboxBuildError(
                f"ATEL patch at PC 0x{item.pc:04X} changed script size"
            )
    return result


def apply_byte_patches(data: bytes, patches: Sequence[BytePatch]) -> bytes:
    """Apply validated, size-preserving byte edits at ATEL bytecode PCs."""

    result = bytearray(data)
    bytecode_offset = AtelScript(data).bytecode_offset
    for item in patches:
        absolute = bytecode_offset + item.pc
        end = absolute + len(item.expected)
        if item.pc < 0 or end > len(result):
            raise GrayboxBuildError(
                f"Byte patch at PC 0x{item.pc:04X} is outside the ATEL bytecode"
            )
        actual = bytes(result[absolute:end])
        if actual != item.expected:
            raise GrayboxBuildError(
                f"Byte patch at PC 0x{item.pc:04X} found {actual.hex(' ')}, "
                f"expected {item.expected.hex(' ')}"
            )
        result[absolute:end] = item.replacement
    if len(result) != len(data):
        raise GrayboxBuildError("A raw ATEL patch changed script size")
    return bytes(result)


def _component_path(directory: Path, index: int, name: str) -> Path:
    return directory / f"{index:02d}_{name}.bin"


def _read_and_pack(
    source_directory: Path,
    expected_script_sha256: str,
    patches: tuple[TransitionPatch, ...],
    byte_patches: tuple[BytePatch, ...],
    dialogue_spec: Path | None = None,
) -> tuple[bytes, bytes | None, bytes]:
    if not source_directory.is_dir():
        raise GrayboxBuildError(
            f"Unpacked field directory does not exist: {source_directory}"
        )
    header_path = source_directory / "header.bin"
    component_paths = [
        _component_path(source_directory, index, name)
        for index, name in enumerate(STREAM_NAMES)
    ]
    for path in (header_path, *component_paths):
        if not path.is_file():
            raise GrayboxBuildError(f"Required unpacked field file is missing: {path}")

    header = header_path.read_bytes()
    components = [path.read_bytes() for path in component_paths]
    script = components[5]
    actual_hash = _sha256(script)
    if actual_hash != expected_script_sha256:
        raise GrayboxBuildError(
            f"Script hash mismatch for {source_directory}: {actual_hash}; "
            f"expected {expected_script_sha256}"
        )
    patched_script = apply_transition_patches(script, patches)
    patched_script = apply_byte_patches(patched_script, byte_patches)
    components[5] = patched_script
    patched_dialogue = None
    if dialogue_spec is not None:
        if not dialogue_spec.is_file():
            raise GrayboxBuildError(
                f"Dialogue replacement spec does not exist: {dialogue_spec}"
            )
        try:
            dialogue_document = json.loads(dialogue_spec.read_text(encoding="utf-8"))
            patched_dialogue = rebuild_dialogue(components[7], dialogue_document)
        except (json.JSONDecodeError, DialogueFormatError) as exc:
            raise GrayboxBuildError(
                f"Invalid dialogue replacement for {source_directory}: {exc}"
            ) from exc
        components[7] = patched_dialogue
    packed = build_field(header, components)

    # Treat a parse-and-compare round trip as part of compilation, not an
    # optional verification step.
    reparsed = parse_field(packed)
    for expected, actual in zip(components, reparsed.parts, strict=True):
        if expected != actual.data:
            raise GrayboxBuildError(
                f"Packed component verification failed for {actual.name}"
            )
    return patched_script, patched_dialogue, packed


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _resolve_input(input_root: Path, relative: Path, context: str) -> Path:
    result = (input_root / relative).resolve()
    if not _inside(result, input_root):
        raise GrayboxBuildError(f"{context} escapes --input-root: {relative}")
    return result


def prepare_bundles(
    recipe: GrayboxRecipe, input_root: Path | str, output_root: Path | str
) -> tuple[PreparedBundle, ...]:
    """Validate all sources and compile every bundle without writing files."""

    input_path = Path(input_root).resolve()
    output_path = Path(output_root).resolve()

    hook_source = _resolve_input(
        input_path, recipe.hook.bundle_directory, "Hook bundle directory"
    )
    source_directories = [hook_source]
    clone_inputs: list[tuple[CloneSpec, Path, Path]] = []
    for clone in recipe.clones:
        source_directory = _resolve_input(
            input_path,
            clone.bundle_directory,
            f"Field {clone.source_field} bundle directory",
        )
        graphics_source = _resolve_input(
            input_path,
            clone.graphics_file,
            f"Field {clone.source_field} graphics file",
        )
        source_directories.append(source_directory)
        clone_inputs.append((clone, source_directory, graphics_source))

    for source in source_directories:
        if _inside(output_path, source) or _inside(source, output_path):
            raise GrayboxBuildError(
                f"Output directory overlaps a source directory: {source}"
            )

    hook_script, hook_dialogue, hook_bundle = _read_and_pack(
        hook_source,
        recipe.hook.script_sha256,
        recipe.hook.patches,
        recipe.hook.byte_patches,
    )
    prepared = [
        PreparedBundle(
            label=f"field {recipe.hook.source_field} hook",
            source_directory=hook_source,
            clone_directory_name=f"field_{recipe.hook.source_field}_hook",
            patched_script=hook_script,
            packed_bundle=hook_bundle,
            bundle_id=recipe.hook.canonical_bundle_id,
            bundle_filename=(
                f"{recipe.hook.canonical_bundle_id}_field_"
                f"{recipe.hook.source_field}_hook.bin"
            ),
            patches=recipe.hook.patches,
            byte_patches=recipe.hook.byte_patches,
            patched_dialogue=hook_dialogue,
        )
    ]

    for clone, source_directory, graphics_source in clone_inputs:
        if not graphics_source.is_file():
            raise GrayboxBuildError(
                f"Graphics source does not exist: {graphics_source}"
            )
        graphics_data = graphics_source.read_bytes()
        actual_graphics_hash = _sha256(graphics_data)
        if actual_graphics_hash != clone.graphics_sha256:
            raise GrayboxBuildError(
                f"Graphics hash mismatch for {graphics_source}: "
                f"{actual_graphics_hash}; expected {clone.graphics_sha256}"
            )
        script, patched_dialogue, bundle = _read_and_pack(
            source_directory,
            clone.script_sha256,
            clone.patches,
            clone.byte_patches,
            clone.dialogue_spec,
        )
        prepared.append(
            PreparedBundle(
                label=(
                    f"{clone.role}: field {clone.source_field} -> "
                    f"scene {clone.target_field}"
                ),
                source_directory=source_directory,
                clone_directory_name=f"field_{clone.target_field}",
                patched_script=script,
                packed_bundle=bundle,
                bundle_id=clone.target_bundle_id,
                bundle_filename=(
                    f"{clone.target_bundle_id}_field_{clone.target_field}.bin"
                ),
                patches=clone.patches,
                byte_patches=clone.byte_patches,
                patched_dialogue=patched_dialogue,
                dialogue_spec=clone.dialogue_spec,
                graphics_source=graphics_source,
                graphics_data=graphics_data,
                graphics_id=clone.target_graphics_id,
                graphics_filename=(
                    f"{clone.target_graphics_id}_field_"
                    f"{clone.target_field}_graphics.bin"
                ),
            )
        )
    return tuple(prepared)


def _patch_record(item: TransitionPatch) -> dict[str, Any]:
    return {
        "pc": item.pc,
        "pc_hex": f"0x{item.pc:04X}",
        "expected": [item.expected_field, item.expected_parameter],
        "new": [item.new_field, item.new_parameter],
        "note": item.note,
    }


def _byte_patch_record(item: BytePatch) -> dict[str, Any]:
    return {
        "pc": item.pc,
        "pc_hex": f"0x{item.pc:04X}",
        "expected": item.expected.hex(" "),
        "replacement": item.replacement.hex(" "),
        "note": item.note,
    }


def _ensure_output_available(output: Path, force: bool) -> None:
    if output.exists() and not output.is_dir():
        raise GrayboxBuildError(f"Output path is not a directory: {output}")
    if output.is_dir() and any(output.iterdir()) and not force:
        raise GrayboxBuildError(
            f"Refusing to overwrite non-empty output directory {output}; pass --force"
        )


def materialize_bundles(
    recipe: GrayboxRecipe,
    recipe_path: Path,
    prepared: Sequence[PreparedBundle],
    output_root: Path | str,
    force: bool = False,
) -> tuple[tuple[int, Path], ...]:
    """Copy validated clones and emit packed replacement files."""

    output = Path(output_root).resolve()
    _ensure_output_available(output, force)
    clones_directory = output / "clones"
    replacements_directory = output / "replacements"
    clones_directory.mkdir(parents=True, exist_ok=True)
    replacements_directory.mkdir(parents=True, exist_ok=True)

    replacements: list[tuple[int, Path]] = []
    manifest_jobs = []
    for job in prepared:
        clone_destination = clones_directory / job.clone_directory_name
        shutil.copytree(
            job.source_directory,
            clone_destination,
            dirs_exist_ok=force,
        )
        (clone_destination / SCRIPT_COMPONENT).write_bytes(job.patched_script)
        if job.patched_dialogue is not None:
            _component_path(clone_destination, 7, STREAM_NAMES[7]).write_bytes(
                job.patched_dialogue
            )
        dialogue_record = None
        if job.dialogue_spec is not None and job.patched_dialogue is not None:
            dialogue_record = {
                "spec": str(job.dialogue_spec),
                "spec_sha256": _sha256(job.dialogue_spec.read_bytes()),
                "patched_sha256": _sha256(job.patched_dialogue),
                "patched_size": len(job.patched_dialogue),
            }
        patch_manifest = {
            "format": OUTPUT_FORMAT,
            "label": job.label,
            "source_directory": str(job.source_directory),
            "patched_script_sha256": _sha256(job.patched_script),
            "patches": [_patch_record(item) for item in job.patches],
            "byte_patches": [
                _byte_patch_record(item) for item in job.byte_patches
            ],
            "dialogue": dialogue_record,
        }
        (clone_destination / "graybox-patches.json").write_text(
            json.dumps(patch_manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )

        bundle_path = replacements_directory / job.bundle_filename
        bundle_path.write_bytes(job.packed_bundle)
        replacements.append((job.bundle_id, bundle_path))
        job_replacements = [
            {
                "canonical_id": job.bundle_id,
                "file": str(bundle_path.relative_to(output)),
                "size": len(job.packed_bundle),
                "sha256": _sha256(job.packed_bundle),
            }
        ]

        if job.graphics_data is not None:
            if job.graphics_id is None or job.graphics_filename is None:
                raise GrayboxBuildError(
                    f"Internal graphics metadata is incomplete for {job.label}"
                )
            graphics_path = replacements_directory / job.graphics_filename
            graphics_path.write_bytes(job.graphics_data)
            replacements.append((job.graphics_id, graphics_path))
            job_replacements.append(
                {
                    "canonical_id": job.graphics_id,
                    "file": str(graphics_path.relative_to(output)),
                    "size": len(job.graphics_data),
                    "sha256": _sha256(job.graphics_data),
                }
            )
        manifest_jobs.append(
            {
                "label": job.label,
                "clone_directory": str(clone_destination.relative_to(output)),
                "patches": [_patch_record(item) for item in job.patches],
                "byte_patches": [
                    _byte_patch_record(item) for item in job.byte_patches
                ],
                "dialogue": dialogue_record,
                "replacements": job_replacements,
            }
        )

    manifest = {
        "format": OUTPUT_FORMAT,
        "name": recipe.name,
        "recipe_file": recipe_path.name,
        "recipe_sha256": _sha256(recipe_path.read_bytes()),
        "notes": list(recipe.notes),
        "jobs": manifest_jobs,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return tuple(replacements)


def xenoiso_wrapper_command(
    xenoiso: Path | str,
    source_disc: Path | str,
    disc_output: Path | str,
    replacements: Sequence[tuple[int, Path]],
    force: bool = False,
) -> list[str]:
    source = Path(source_disc).resolve()
    destination = Path(disc_output).resolve()
    if source == destination:
        raise GrayboxBuildError("Disc output must not overwrite the source disc")
    wrapper = (Path(__file__).resolve().parents[3] / "shared/tools/xenoiso_build.py")
    command = [
        sys.executable,
        str(wrapper),
        "--xenoiso",
        str(Path(xenoiso).resolve()),
        "--source",
        str(source),
        "--output",
        str(destination),
    ]
    for canonical_id, path in replacements:
        command.extend(("--replacement", f"{canonical_id}={path.resolve()}"))
    if force:
        command.append("--force")
    return command


def build_graybox(
    recipe_path: Path | str,
    input_root: Path | str,
    output_root: Path | str,
    force: bool = False,
) -> tuple[GrayboxRecipe, tuple[tuple[int, Path], ...]]:
    """Compile and write a recipe without invoking Xenoiso."""

    recipe_file = Path(recipe_path).resolve()
    recipe = load_recipe(recipe_file)
    output = Path(output_root).resolve()
    _ensure_output_available(output, force)
    prepared = prepare_bundles(recipe, input_root, output)
    replacements = materialize_bundles(
        recipe, recipe_file, prepared, output, force=force
    )
    return recipe, replacements


def build_parser() -> argparse.ArgumentParser:
    project_root = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recipe",
        type=Path,
        default=project_root / "recipes" / "mass_driver_graybox.json",
    )
    parser.add_argument(
        "--input-root",
        type=Path,
        required=True,
        help="root containing the recipe's unpacked bundle and graphics paths",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--build-disc",
        action="store_true",
        help="after creating replacements, invoke the existing Xenoiso wrapper",
    )
    parser.add_argument("--xenoiso", type=Path)
    parser.add_argument("--source-disc", type=Path)
    parser.add_argument("--disc-output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.build_disc and not all(
        (args.xenoiso, args.source_disc, args.disc_output)
    ):
        parser.error(
            "--build-disc requires --xenoiso, --source-disc, and --disc-output"
        )
    if not args.build_disc and any(
        (args.xenoiso, args.source_disc, args.disc_output)
    ):
        parser.error(
            "--xenoiso/--source-disc/--disc-output require --build-disc"
        )

    try:
        recipe, replacements = build_graybox(
            args.recipe, args.input_root, args.output, force=args.force
        )
        print(f"Prepared {recipe.name}")
        for canonical_id, path in replacements:
            print(f"  canonical {canonical_id}: {path}")
        print(f"Wrote {Path(args.output).resolve() / 'manifest.json'}")

        if args.build_disc:
            command = xenoiso_wrapper_command(
                args.xenoiso,
                args.source_disc,
                args.disc_output,
                replacements,
                force=args.force,
            )
            result = subprocess.run(command, check=False)
            if result.returncode != 0:
                raise GrayboxBuildError(
                    f"Xenoiso wrapper exited with code {result.returncode}"
                )
        else:
            print("Disc build skipped (use --build-disc after reviewing the manifest).")
        return 0
    except (GrayboxBuildError, AtelFormatError, FieldFormatError, OSError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
