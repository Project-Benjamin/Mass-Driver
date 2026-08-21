#!/usr/bin/env python3
"""Build a safe Disc 2 output image with legacy Xenoiso 0.95.

Xenoiso's command-list parser requires the final replacement line to end at
EOF (not with a newline), and it returns success even for several failures.
This wrapper handles both quirks and creates a matching MODE2/2352 CUE.
"""

from __future__ import annotations

import argparse
from pathlib import Path
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
    source: Path, output: Path, replacements: Sequence[tuple[int, Path]]
) -> bytes:
    lines = ["cd2fix", str(source), str(output)]
    lines.extend(f"{number},{path}" for number, path in replacements)
    return "\r\n".join(lines).encode("ascii")


def _checked_path(path: Path, description: str, must_exist: bool) -> Path:
    resolved = path.resolve()
    if any(character.isspace() for character in str(resolved)):
        raise BuildError(
            f"Legacy Xenoiso cannot parse whitespace in {description} path: {resolved}"
        )
    if must_exist and not resolved.is_file():
        raise BuildError(f"{description} does not exist: {resolved}")
    return resolved


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
    if source == output:
        raise BuildError("Output image must not be the source image")
    if output.exists():
        if not args.force:
            raise BuildError(f"Refusing to overwrite {output}; pass --force")
        output.unlink()

    output.parent.mkdir(parents=True, exist_ok=True)
    command_data = command_list_bytes(source, output, replacements)
    list_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".txt", prefix="xenoiso_", dir=output.parent, delete=False
        ) as command_file:
            command_file.write(command_data)
            list_path = Path(command_file.name)

        result = subprocess.run(
            [str(executable), str(list_path)],
            cwd=output.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    finally:
        if list_path is not None:
            list_path.unlink(missing_ok=True)

    transcript = result.stdout.decode("cp1252", errors="replace")
    tail = transcript.replace("\r", "").splitlines()[-20:]
    if tail:
        print("\n".join(tail))

    lowered = transcript.lower()
    if "error opening file" in lowered or "errore" in lowered:
        raise BuildError("Xenoiso reported an error")
    if not output.is_file() or output.stat().st_size == 0:
        raise BuildError("Xenoiso did not create a non-empty output image")

    cue = output.with_suffix(".cue")
    cue.write_text(
        f'FILE "{output.name}" BINARY\n'
        "  TRACK 01 MODE2/2352\n"
        "    INDEX 01 00:00:00\n",
        encoding="ascii",
        newline="\n",
    )
    print(f"Built {output} ({output.stat().st_size} bytes)")
    print(f"Wrote {cue}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xenoiso", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
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
