#!/usr/bin/env python3
"""Build a safe Xenogears output image with legacy Xenoiso 0.95.

Xenoiso's command-list parser requires short, unquoted ASCII filenames and
the final replacement line to end at EOF. It returns success for several
failures. This wrapper stages short aliases, checks the process and result,
and publishes a matching MODE2/2352 CUE only after a successful build.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Sequence


class BuildError(RuntimeError):
    """Raised when inputs are unsafe or Xenoiso reports a failed build."""


def parse_replacement(value: str) -> tuple[int, Path]:
    number, separator, filename = value.partition("=")
    if not separator:
        raise argparse.ArgumentTypeError("replacement must be CANONICAL_ID=FILE")
    try:
        canonical_id = int(number, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid canonical ID: {number}") from exc
    return canonical_id, Path(filename)


def command_list_bytes(
    source: Path,
    output: Path,
    replacements: Sequence[tuple[int, Path]],
    *,
    disc: int = 2,
) -> bytes:
    """Encode one legacy command list in the shared canonical namespace.

    Disc 1's FAT already uses the canonical file numbers, while ``cd2fix``
    translates those same numbers to Disc 2's five-entry-shorter physical FAT.
    Keeping callers in one namespace is important for resources shared by the
    two anthology discs (title field 1586 and initial GameState 2595).
    """

    if disc not in (1, 2):
        raise BuildError(f"Disc must be 1 or 2, got {disc}")
    lines = ["cd1" if disc == 1 else "cd2fix", str(source), str(output)]
    lines.extend(f"{number},{path}" for number, path in replacements)
    return "\r\n".join(lines).encode("ascii")


def _checked_path(path: Path, description: str, must_exist: bool) -> Path:
    resolved = path.resolve()
    if must_exist and not resolved.is_file():
        raise BuildError(f"{description} does not exist: {resolved}")
    return resolved


def _stage_input(source: Path, destination: Path) -> None:
    """Give the read-only legacy input a short name without editing its bytes."""
    try:
        os.link(source, destination)
    except OSError:
        # Different volumes and some filesystems do not support hard links.
        shutil.copyfile(source, destination)


def _publish_file(staged: Path, destination: Path, *, force: bool) -> None:
    if force:
        os.replace(staged, destination)
        return
    # Hard-link creation is exclusive, unlike rename on some platforms. It
    # cannot overwrite an output that another process created during the build.
    try:
        os.link(staged, destination)
    except FileExistsError as exc:
        raise BuildError(f"Refusing to overwrite {destination}; pass --force") from exc
    except OSError:
        with destination.open("xb") as output:
            with staged.open("rb") as source:
                shutil.copyfileobj(source, output, length=8 * 1024 * 1024)


def command_build(args: argparse.Namespace) -> int:
    executable = _checked_path(args.xenoiso, "Xenoiso executable", True)
    source = _checked_path(args.source, "source image", True)
    output = _checked_path(args.output, "output image", False)
    replacements = [
        (number, _checked_path(path, f"replacement {number}", True))
        for number, path in args.replacement
    ]
    if not replacements:
        raise BuildError("At least one replacement is required")
    cue = output.with_suffix(".cue")
    inputs = {executable, source, *(path for _number, path in replacements)}
    if output in inputs or cue in inputs:
        raise BuildError("Output image/CUE must not overwrite a source, replacement, or executable")
    if output == cue:
        raise BuildError("Output image filename must not use the .cue extension")
    for destination in (output, cue):
        if destination.exists() and not args.force:
            raise BuildError(f"Refusing to overwrite {destination}; pass --force")
        if destination.exists() and not destination.is_file():
            raise BuildError(f"Output destination is not a file: {destination}")
    ids = [number for number, _path in replacements]
    if any(isinstance(number, bool) or not isinstance(number, int) or number < 0 for number in ids):
        raise BuildError("Canonical replacement IDs must be nonnegative integers")
    if len(set(ids)) != len(ids):
        raise BuildError("Canonical replacement IDs must be unique")
    if args.disc not in (1, 2):
        raise BuildError(f"Disc must be 1 or 2, got {args.disc}")

    output.parent.mkdir(parents=True, exist_ok=True)
    # Legacy Xenoiso stores command-list filenames in fixed-size buffers.
    # Pass only short aliases; neither deep output trees nor source-path
    # whitespace reaches that parser. The working directory stays on the
    # destination volume so publishing a completed image is inexpensive.
    with tempfile.TemporaryDirectory(prefix="xgi_", dir=output.parent) as temporary:
        workspace = Path(temporary).resolve()
        if workspace.parent != output.parent.resolve():
            raise BuildError("Xenoiso staging directory escaped its output directory")
        _stage_input(source, workspace / "source.bin")
        aliases = []
        for index, (number, path) in enumerate(replacements):
            alias = Path(f"r{index:05d}.bin")
            _stage_input(path, workspace / alias)
            aliases.append((number, alias))
        staged_output = workspace / "output.bin"
        (workspace / "build.txt").write_bytes(command_list_bytes(
            Path("source.bin"), Path("output.bin"), aliases, disc=args.disc,
        ))
        result = subprocess.run(
            [str(executable), "build.txt"],
            cwd=workspace,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        transcript = result.stdout.decode("cp1252", errors="replace")
        tail = transcript.replace("\r", "").splitlines()[-20:]
        if tail:
            print("\n".join(tail))
        if result.returncode:
            raise BuildError(
                f"Xenoiso exited with status {result.returncode} "
                f"(0x{result.returncode & 0xFFFFFFFF:08X})"
            )
        lowered = transcript.lower()
        if "error opening file" in lowered or "errore" in lowered:
            raise BuildError("Xenoiso reported an error")
        if not staged_output.is_file() or staged_output.stat().st_size == 0:
            raise BuildError("Xenoiso did not create a non-empty output image")
        staged_cue = workspace / "output.cue"
        staged_cue.write_text(
            f'FILE "{output.name}" BINARY\n'
            "  TRACK 01 MODE2/2352\n"
            "    INDEX 01 00:00:00\n",
            encoding="utf-8",
            newline="\n",
        )
        # Existing outputs survive every staging/process/validation failure.
        _publish_file(staged_output, output, force=args.force)
        _publish_file(staged_cue, cue, force=args.force)
    print(f"Built {output} ({output.stat().st_size} bytes)")
    print(f"Wrote {cue}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xenoiso", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--disc",
        type=int,
        choices=(1, 2),
        default=2,
        help=(
            "source disc number; defaults to 2 for compatibility with the "
            "original Disc-2-only wrapper"
        ),
    )
    parser.add_argument(
        "--replacement",
        action="append",
        type=parse_replacement,
        default=[],
        metavar="CANONICAL_ID=FILE",
    )
    parser.add_argument("--force", action="store_true")
    parser.set_defaults(handler=command_build)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (BuildError, OSError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
