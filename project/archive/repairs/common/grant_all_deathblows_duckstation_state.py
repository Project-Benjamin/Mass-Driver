#!/usr/bin/env python3
"""Grant all native on-foot deathblows in a separate DuckStation state.

The input is never overwritten.  This tool validates DuckStation's type-2
Zstandard envelope, patches only the resident Xenogears GameState ability
halfwords, updates the compressed-size header, and verifies a full round trip
before writing the requested output.  It does not change mounted media or the
resident disc archive table; use ``migrate_duckstation_disc_state.py`` first
when carrying an older state onto a rebuilt disc.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
from typing import Protocol, Sequence

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from tools.migrate_duckstation_disc_state import (  # noqa: E402
    DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
    DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    DUCKSTATION_STATE_HEADER_SIZE,
    DUCKSTATION_STATE_MAGIC,
    DUCKSTATION_ZSTD_COMPRESSION_TYPE,
    StateMigrationError,
    ZSTD_MAGIC,
    _Zstd,
)
from tools.xgdeathblows import (  # noqa: E402
    DEATHBLOW_PROFILES,
    GAMESTATE_SIZE,
    grant_all_on_foot_deathblows,
    learned_mask,
)


GAMESTATE_PAYLOAD_OFFSET = 0x6F096
GAMESTATE_FIELD_OFFSET = 0x231A


class StateDeathblowError(RuntimeError):
    """Raised before output when the state fails a byte-level safety check."""


class _ZstdLike(Protocol):
    def frame_size(self, frame: bytes) -> int: ...

    def decompress(self, frame: bytes) -> bytes: ...

    def compress(self, payload: bytes) -> bytes: ...


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _unpack_state(
    state: bytes,
    zstd: _ZstdLike,
) -> tuple[bytes, int, bytes]:
    if (
        len(state) < DUCKSTATION_STATE_HEADER_SIZE
        or state[:4] != DUCKSTATION_STATE_MAGIC
    ):
        raise StateDeathblowError("Input is not a supported DuckStation save state")
    compression, compressed_size, payload_size, frame_start = struct.unpack_from(
        "<IIII", state, DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET
    )
    if compression != DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise StateDeathblowError(
            "DuckStation state payload is not Zstandard-compressed"
        )
    if not DUCKSTATION_STATE_HEADER_SIZE <= frame_start < len(state):
        raise StateDeathblowError("DuckStation state data offset is outside the file")
    frame_end = frame_start + compressed_size
    if frame_end != len(state):
        raise StateDeathblowError(
            "DuckStation state has an inconsistent frame span or trailing data"
        )
    frame = state[frame_start:frame_end]
    if not frame.startswith(ZSTD_MAGIC):
        raise StateDeathblowError("DuckStation state data is not a Zstandard frame")
    if zstd.frame_size(frame) != compressed_size:
        raise StateDeathblowError(
            "DuckStation state compressed-size header does not match its frame"
        )
    payload = zstd.decompress(frame)
    if len(payload) != payload_size:
        raise StateDeathblowError(
            "DuckStation state uncompressed-size header does not match its payload"
        )
    return payload, frame_start, state[:frame_start]


def grant_deathblows_to_state(
    state: bytes,
    *,
    zstd: _ZstdLike,
    expected_source_sha256: str | None = None,
    expected_field: int | None = None,
) -> tuple[bytes, dict[str, object]]:
    """Return a validated state with only resident GameState masks changed."""

    if expected_source_sha256 is None or expected_field is None:
        raise StateDeathblowError(
            "Both the exact source SHA-256 and expected field are required"
        )
    normalized_expected_sha256 = expected_source_sha256.lower()
    if (
        len(normalized_expected_sha256) != 64
        or any(character not in "0123456789abcdef" for character in normalized_expected_sha256)
    ):
        raise StateDeathblowError("Expected source SHA-256 must be 64 hexadecimal digits")
    if not 0 <= expected_field <= 0xFFFF:
        raise StateDeathblowError("Expected field is outside the 16-bit field-ID range")

    source_sha256 = _sha256(state)
    if source_sha256 != normalized_expected_sha256:
        raise StateDeathblowError(
            f"Source state SHA-256 is {source_sha256}, expected "
            f"{normalized_expected_sha256}"
        )
    payload, frame_start, prefix = _unpack_state(state, zstd)
    state_end = GAMESTATE_PAYLOAD_OFFSET + GAMESTATE_SIZE
    if state_end > len(payload):
        raise StateDeathblowError(
            "DuckStation payload is too short for the resident Xenogears GameState"
        )
    source_gamestate = payload[GAMESTATE_PAYLOAD_OFFSET:state_end]
    field = struct.unpack_from("<H", source_gamestate, GAMESTATE_FIELD_OFFSET)[0]
    if field != expected_field:
        raise StateDeathblowError(
            f"Resident GameState is field {field}, expected field {expected_field}"
        )

    patched_gamestate = grant_all_on_foot_deathblows(source_gamestate)
    allowed_offsets = {
        profile.word_offset + byte
        for profile in DEATHBLOW_PROFILES
        if profile.full_mask
        for byte in (0, 1)
    }
    changed_gamestate_offsets = {
        offset
        for offset, (before, after) in enumerate(
            zip(source_gamestate, patched_gamestate, strict=True)
        )
        if before != after
    }
    if not changed_gamestate_offsets <= allowed_offsets:
        raise StateDeathblowError(
            "Deathblow migration changed bytes outside the learned-command words"
        )

    patched_payload = (
        payload[:GAMESTATE_PAYLOAD_OFFSET]
        + patched_gamestate
        + payload[state_end:]
    )
    if (
        patched_payload[:GAMESTATE_PAYLOAD_OFFSET]
        != payload[:GAMESTATE_PAYLOAD_OFFSET]
        or patched_payload[state_end:] != payload[state_end:]
    ):
        raise StateDeathblowError("Payload changed outside the resident GameState")

    compressed = zstd.compress(patched_payload)
    if len(compressed) > 0xFFFFFFFF:
        raise StateDeathblowError("Recompressed state exceeds its 32-bit size field")
    patched_prefix = bytearray(prefix)
    struct.pack_into(
        "<I",
        patched_prefix,
        DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        len(compressed),
    )
    result = bytes(patched_prefix) + compressed
    verified_payload, verified_frame_start, _verified_prefix = _unpack_state(
        result, zstd
    )
    if verified_frame_start != frame_start or verified_payload != patched_payload:
        raise StateDeathblowError("Recompressed deathblow state failed round trip")

    grants = []
    for profile in DEATHBLOW_PROFILES:
        before = learned_mask(source_gamestate, profile.character_id)
        after = learned_mask(patched_gamestate, profile.character_id)
        grants.append(
            {
                "character_id": profile.character_id,
                "character": profile.character,
                "native_deathblows": len(profile.command_names),
                "before_mask": f"0x{before:04X}",
                "after_mask": f"0x{after:04X}",
            }
        )
    report: dict[str, object] = {
        "source_sha256": source_sha256,
        "output_sha256": _sha256(result),
        "source_size": len(state),
        "output_size": len(result),
        "payload_size": len(payload),
        "payload_frame_offset": frame_start,
        "gamestate_payload_offset": GAMESTATE_PAYLOAD_OFFSET,
        "gamestate_field": field,
        "gamestate_source_sha256": _sha256(source_gamestate),
        "gamestate_output_sha256": _sha256(patched_gamestate),
        "changed_gamestate_bytes": len(changed_gamestate_offsets),
        "changed_payload_bytes": sum(
            before != after
            for before, after in zip(payload, patched_payload, strict=True)
        ),
        "levels_changed": False,
        "stats_changed": False,
        "grants": grants,
    }
    return result, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--zstd",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "work" / "duckstation" / "zstd.dll",
    )
    parser.add_argument("--expected-source-sha256", required=True)
    parser.add_argument("--expected-field", type=int, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        source = args.state.resolve()
        output = args.output.resolve()
        if source == output:
            raise StateDeathblowError("Output must differ from the input state")
        if not source.is_file():
            raise StateDeathblowError(f"Input state does not exist: {source}")
        if output.exists():
            raise StateDeathblowError(f"Output already exists: {output}")
        if not output.parent.is_dir():
            raise StateDeathblowError(
                f"Output directory does not exist: {output.parent}"
            )
        result, report = grant_deathblows_to_state(
            source.read_bytes(),
            zstd=_Zstd(args.zstd.resolve()),
            expected_source_sha256=args.expected_source_sha256,
            expected_field=args.expected_field,
        )
        output.write_bytes(result)
        print(json.dumps(report, indent=2, sort_keys=True))
        print(f"Wrote {output}")
    except (OSError, ValueError, StateDeathblowError, StateMigrationError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
