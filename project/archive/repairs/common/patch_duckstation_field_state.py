#!/usr/bin/env python3
"""Set one field-variable bit in a disposable DuckStation save state.

Xenogears keeps a 0x400-byte field-variable bank both in GameState and in the
active field runtime.  This helper requires those two copies to be identical,
patches the requested bit in both, and recompresses the state without touching
the source.  It is intended for controlled transition/testing states, not for
normal player saves.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import struct
import sys

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from tools.migrate_duckstation_disc_state import (  # noqa: E402
    DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
    DUCKSTATION_DATA_OFFSET_OFFSET,
    DUCKSTATION_STATE_MAGIC,
    _Zstd,
)
from work.read_duckstation_runtime import (  # noqa: E402
    GAME_STATE,
    RAM_SIZE,
    _psx_ram_offset,
)


FIELD_VARIABLE_BACKUP_OFFSET = 0x1930
FIELD_VARIABLE_BANK_SIZE = 0x400


def _parse_int(value: str) -> int:
    return int(value, 0)


def _all_offsets(haystack: bytes, needle: bytes) -> tuple[int, ...]:
    offsets: list[int] = []
    cursor = 0
    while True:
        offset = haystack.find(needle, cursor)
        if offset < 0:
            return tuple(offsets)
        offsets.append(offset)
        cursor = offset + 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--variable", type=_parse_int, required=True)
    parser.add_argument("--bit", type=_parse_int, required=True)
    parser.add_argument("--zstd", type=Path, required=True)
    args = parser.parse_args()

    if args.variable & 1 or not 0 <= args.variable <= 0x3FE:
        raise SystemExit("--variable must be an even field offset in 0..0x3FE")
    if not 0 <= args.bit <= 15:
        raise SystemExit("--bit must be in 0..15")
    if args.source.resolve() == args.output.resolve():
        raise SystemExit("source and output must be different paths")

    state = args.source.read_bytes()
    if state[:4] != DUCKSTATION_STATE_MAGIC:
        raise SystemExit("source is not a DuckStation state")
    frame_start = struct.unpack_from(
        "<I", state, DUCKSTATION_DATA_OFFSET_OFFSET
    )[0]
    frame_size = struct.unpack_from(
        "<I", state, DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET
    )[0]
    if frame_start + frame_size != len(state):
        raise SystemExit("state compressed-data span does not end at EOF")

    zstd = _Zstd(args.zstd)
    payload = bytearray(zstd.decompress(state[frame_start:]))
    ram_offset = _psx_ram_offset(payload)
    ram = memoryview(payload)[ram_offset : ram_offset + RAM_SIZE]
    backup = GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET
    bank = bytes(ram[backup : backup + FIELD_VARIABLE_BANK_SIZE])
    bank_offsets = _all_offsets(bytes(ram), bank)
    if len(bank_offsets) != 2 or backup not in bank_offsets:
        raise SystemExit(
            "field-variable bank did not have exactly one GameState and one "
            f"active copy: {tuple(hex(value) for value in bank_offsets)}"
        )
    active = next(offset for offset in bank_offsets if offset != backup)

    mask = 1 << args.bit
    old_values: list[int] = []
    for bank_base in (backup, active):
        word_offset = bank_base + args.variable
        old_value = struct.unpack_from("<H", ram, word_offset)[0]
        old_values.append(old_value)
        struct.pack_into("<H", ram, word_offset, old_value | mask)
    if old_values[0] != old_values[1]:
        raise SystemExit(
            "GameState and active field-variable words differed before patch"
        )

    compressed = zstd.compress(bytes(payload))
    prefix = bytearray(state[:frame_start])
    struct.pack_into(
        "<I",
        prefix,
        DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        len(compressed),
    )
    args.output.write_bytes(prefix + compressed)
    print(
        f"Wrote {args.output.resolve()}\n"
        f"GameState bank: 0x{backup:X}\n"
        f"Active bank: 0x{active:X}\n"
        f"Variable: 0x{args.variable:04X}, bit {args.bit}, "
        f"0x{old_values[0]:04X}->0x{old_values[0] | mask:04X}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
