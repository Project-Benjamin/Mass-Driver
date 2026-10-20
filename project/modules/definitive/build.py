"""Build original-campaign candidates from checked USA retail discs."""
from __future__ import annotations
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil

from shared.tools.xgdisc import Mode2Image, streamed_movie_entries, XA_STORED_SECTOR_SIZE
from shared.tools.xenoiso_build import command_build
from shared.tools.xgdialog_name_color import patch_executable, verify_executable_image
from modules.definitive.options import Options
from modules.definitive.dialogue import patch_disc_dialogue
from modules.definitive.restoration import build_restoration_replacements
from modules.definitive.qol import patch_rewards
from modules.definitive.encounters import build_encounter_replacements

ROOT = Path(__file__).resolve().parents[2]
RETAIL_SHA256 = {
    1: "39c547a9afc6da15d847ef81a2c6cea1a6516bdfa562cf13b0999b04e8598bda",
    2: "5eab85c683d4d7087d345b587472db9c44df29b35ce66553c2626d26018b947e",
}
PLAYLIST = "Xenogears_Definitive.m3u"


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class RetailDisc:
    def __init__(self, path, disc):
        if disc not in (1, 2):
            raise ValueError("Expected disc 1 or 2")
        self.disc = disc
        self.image = Mode2Image(path)
        self.entries = self.image.read_index()

    def read(self, canonical):
        physical = canonical - (5 if self.disc == 2 else 0)
        if not 0 <= physical < len(self.entries):
            raise ValueError(f"Resource {canonical} is outside disc {self.disc}")
        return self.image.extract_entry(self.entries[physical])


def prepare_disc(source: RetailDisc, options: Options):
    options.validate()
    replacements, audit = {}, {}
    if options.bug_fixes:
        replacements, audit["bug_fixes"] = build_restoration_replacements(source.read)
    if options.double_xp:
        replacements, audit["double_xp"] = patch_rewards(source.read, replacements)
    if options.encounters != "normal":
        encounter_patches, audit["encounters"] = build_encounter_replacements(source.read, mode=options.encounters)
        if replacements.keys() & encounter_patches.keys():
            raise ValueError("Encounter and mechanics patches overlap; explicit composition is required")
        replacements.update(encounter_patches)
    replacements, audit["dialogue"] = patch_disc_dialogue(
        source.image.path, source.disc, yellow_names=options.yellow_names,
        replacements=replacements)
    if options.yellow_names:
        replacements[22] = patch_executable(source.read(22))
    return replacements, audit


def verify_resources(source: RetailDisc, output: Path, replacements: dict[int, bytes]):
    actual = RetailDisc(output, source.disc)
    if len(actual.entries) != len(source.entries):
        raise ValueError("Rebuilt FAT entry count differs from retail")
    if actual.image.read_directories() != source.image.read_directories():
        raise ValueError("Rebuilt native directory lookup table differs from retail")
    movies = {entry.index: entry for entry in streamed_movie_entries(source.entries)}
    if {entry.index for entry in streamed_movie_entries(actual.entries)} != movies.keys():
        raise ValueError("Rebuilt streamed movie group changed")
    checked = 0
    movies_checked = 0
    for entry in source.entries:
        canonical = entry.index + (5 if source.disc == 2 else 0)
        if actual.entries[entry.index].kind != entry.kind:
            raise ValueError(f"FAT record kind changed for {canonical}")
        if entry.kind != "file":
            following = entry.index + 1
            expected_sector = entry.sector
            if (following < len(source.entries) and source.entries[following].kind == "file"
                    and source.entries[following].sector == entry.sector):
                expected_sector = actual.entries[following].sector
            rebuilt = actual.entries[entry.index]
            if rebuilt.size != entry.size or rebuilt.sector != expected_sector:
                raise ValueError(f"Nonfile FAT metadata changed for {canonical}")
            continue
        if entry.index in movies:
            rebuilt = actual.entries[entry.index]
            if canonical in replacements or rebuilt.size != entry.size or rebuilt.sector != entry.sector:
                raise ValueError("Unselected movie extent was modified")
            sectors = entry.size // XA_STORED_SECTOR_SIZE
            if (actual.image.raw_sector_sha256(rebuilt.sector, sectors)
                    != source.image.raw_sector_sha256(entry.sector, sectors)):
                raise ValueError(f"Raw XA movie sectors changed for {canonical}")
            movies_checked += 1
            continue
        if canonical == 22:
            continue
        expected = replacements.get(canonical)
        if expected is None:
            expected = source.image.extract_entry(entry)
        if actual.read(canonical) != expected:
            raise ValueError(f"Rebuilt resource {canonical} differs from expected bytes")
        checked += 1
    boot = verify_executable_image(output, source.disc, replacements.get(22, source.read(22)))
    return {"resource_files_verified": checked, "raw_xa_movies_verified": movies_checked, "boot": boot,
            "runtime_status": "untested", "note": "Byte verification is not an emulator playthrough."}


def build(args):
    options = Options.load(args.options)
    output = args.output.resolve()
    paths = {1: args.disc1.resolve(), 2: args.disc2.resolve()}
    if paths[1] == paths[2]:
        raise ValueError("Disc 1 and Disc 2 must be different files")
    sources = {}
    for disc, path in paths.items():
        if path == output or path.is_relative_to(output):
            raise ValueError("Source discs must be outside the build destination")
        identity = digest(path)
        if identity != RETAIL_SHA256[disc]:
            raise ValueError(f"Disc {disc} does not match the audited USA retail image: {identity}")
        sources[str(disc)] = {"path": str(path), "sha256": identity, "size": path.stat().st_size}
    if not args.prepare_only and (not args.xenoiso or not args.xenoiso.is_file()):
        raise ValueError("A configured Xenoiso executable is required")
    output.mkdir(parents=True, exist_ok=True)
    stage = output / "stage"
    stage.mkdir(exist_ok=False)
    manifest = {"format": "xenogears-definitive-build-v1", "options": asdict(options),
                "sources": sources, "discs": {}, "runtime_status": "untested",
                "scope": "Original retail campaign; no expansion content or persistent story/save-state allocations. Bug fixes use one declared transient battle-camera byte.",
                "completion": "Development candidate; full retranslation and whole-game bug audit incomplete"}
    cues = []
    for disc in (1, 2):
        print(f"Auditing Disc {disc} and preparing selected changes...", flush=True)
        source = RetailDisc(paths[disc], disc)
        replacements, audit = prepare_disc(source, options)
        directory = stage / f"disc{disc}"
        directory.mkdir()
        files, records = [], []
        for canonical, data in sorted(replacements.items()):
            path = directory / f"{canonical:04}.bin"
            path.write_bytes(data)
            files.append((canonical, path))
            records.append({"canonical_id": canonical, "size": len(data),
                            "sha256": hashlib.sha256(data).hexdigest()})
        (directory / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
        record = {"replacements": records, "audit": f"stage/disc{disc}/audit.json"}
        manifest["discs"][str(disc)] = record
        if args.prepare_only:
            continue
        destination = output / f"Xenogears_Definitive_CD{disc}.bin"
        cue = destination.with_suffix(".cue")
        if destination.exists() or cue.exists():
            raise ValueError("Refusing to overwrite existing build media")
        if files:
            command_build(argparse.Namespace(xenoiso=args.xenoiso, source=paths[disc],
                          output=destination, replacement=files, disc=disc, force=False))
        else:
            with paths[disc].open("rb") as src, destination.open("xb") as dst:
                shutil.copyfileobj(src, dst, 8 * 1024 * 1024)
            cue.write_text(f'FILE "{destination.name}" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n', encoding="utf-8")
        print(f"Verifying every Disc {disc} resource and native boot executable...", flush=True)
        record["verification"] = verify_resources(source, destination, replacements)
        cues.append(cue.name)
    if not args.prepare_only:
        (output / PLAYLIST).write_text("\n".join(cues) + "\n", encoding="utf-8")
    path = output / "definitive-build-manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded candidate manifest: {path}", flush=True)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disc1", type=Path, required=True)
    parser.add_argument("--disc2", type=Path, required=True)
    parser.add_argument("--options", type=Path, default=ROOT / "modules/definitive/content/options.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--xenoiso", type=Path)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--force", action="store_true", help="Registry compatibility; existing stage/media are never overwritten")
    args = parser.parse_args(argv)
    try:
        build(args)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
