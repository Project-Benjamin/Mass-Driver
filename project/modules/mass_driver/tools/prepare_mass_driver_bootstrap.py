#!/usr/bin/env python3
"""Create the checked standalone GameState from the audited DuckStation save.

The generated 0x2358-byte file is an ignored build input.  It is normalized to
start Elly and Emeralda on foot in the one-frame gateway field; the gateway
then uses the retail field transition into world-map position 21.  The source
save and zstd library are never modified.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
from pathlib import Path
import struct
import sys
from typing import Sequence


ZSTD_MAGIC = bytes.fromhex("28 B5 2F FD")
STATE_PAYLOAD_OFFSET = 0x6F096
STATE_SIZE = 0x2358
STATE_FRAME_OFFSET = 0x10222
AUDITED_SAVESTATE_SHA256 = (
    "007cbdab3d4b9c88cfcda50d8fb0414116e5e438fe590bb945dcc1b18984e38f"
)
AUDITED_SOURCE_SHA256 = (
    "ad39b37bacc48e70367d4b93d30bafacb576b7ccdeb330c4470d6f7dd14be944"
)
NORMALIZED_SHA256 = (
    "c90f343a1cceccf9e9a8d3cb68079856ac8e63efad0d99a1f5655a4d45fa4375"
)


class BootstrapError(RuntimeError):
    """Raised when the local save does not match the audited bootstrap donor."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _frame_offsets(data: bytes) -> list[int]:
    offsets: list[int] = []
    cursor = 0
    while True:
        offset = data.find(ZSTD_MAGIC, cursor)
        if offset < 0:
            return offsets
        offsets.append(offset)
        cursor = offset + 1


class _Zstd:
    def __init__(self, library: Path):
        if not library.is_file():
            raise BootstrapError(f"zstd library does not exist: {library}")
        try:
            loader = ctypes.WinDLL if sys.platform == "win32" else ctypes.CDLL
            self.library = loader(str(library.resolve()))
        except OSError as exc:
            raise BootstrapError(f"Cannot load zstd library {library}: {exc}") from exc
        self.library.ZSTD_getFrameContentSize.argtypes = [
            ctypes.c_void_p,
            ctypes.c_size_t,
        ]
        self.library.ZSTD_getFrameContentSize.restype = ctypes.c_ulonglong
        self.library.ZSTD_decompress.argtypes = [
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_void_p,
            ctypes.c_size_t,
        ]
        self.library.ZSTD_decompress.restype = ctypes.c_size_t
        self.library.ZSTD_isError.argtypes = [ctypes.c_size_t]
        self.library.ZSTD_isError.restype = ctypes.c_uint

    def decompress(self, frame_and_tail: bytes) -> bytes:
        source = ctypes.create_string_buffer(frame_and_tail)
        size = self.library.ZSTD_getFrameContentSize(source, len(frame_and_tail))
        if size in (0xFFFFFFFFFFFFFFFF, 0xFFFFFFFFFFFFFFFE):
            raise BootstrapError("DuckStation zstd frame has no declared content size")
        destination = ctypes.create_string_buffer(size)
        written = self.library.ZSTD_decompress(
            destination, size, source, len(frame_and_tail)
        )
        if self.library.ZSTD_isError(written):
            raise BootstrapError("zstd could not decompress the DuckStation payload")
        return destination.raw[:written]


def extract_audited_state(savestate: bytes, zstd: _Zstd) -> bytes:
    save_hash = _sha256(savestate)
    if save_hash != AUDITED_SAVESTATE_SHA256:
        raise BootstrapError(
            f"DuckStation save hash mismatch: {save_hash}; expected the audited save"
        )
    minimum = STATE_PAYLOAD_OFFSET + STATE_SIZE
    if savestate[STATE_FRAME_OFFSET : STATE_FRAME_OFFSET + 4] != ZSTD_MAGIC:
        raise BootstrapError(
            f"DuckStation state frame is missing at 0x{STATE_FRAME_OFFSET:X}"
        )
    payload = zstd.decompress(savestate[STATE_FRAME_OFFSET:])
    if len(payload) < minimum:
        raise BootstrapError(
            f"DuckStation payload is {len(payload)} bytes, expected at least {minimum}"
        )
    state = payload[STATE_PAYLOAD_OFFSET:minimum]
    actual = _sha256(state)
    if actual != AUDITED_SOURCE_SHA256:
        raise BootstrapError(
            f"DuckStation GameState hash mismatch: {actual}; expected the audited save"
        )
    return state


def normalize_state(source: bytes) -> bytes:
    state = bytearray(source)
    struct.pack_into("<H", state, 0x1834, 0)  # on foot, not Yggdrasil
    struct.pack_into("<H", state, 0x1836, 0)
    struct.pack_into("<H", state, 0x1934, 0)  # no world-map-origin marker
    struct.pack_into("<H", state, 0x1D2A, 0)  # normalize annex treasure flags
    struct.pack_into("<H", state, 0x1D2C, 0)  # normalize paired lift state
    struct.pack_into("<H", state, 0x1D2E, 0)  # normalize unused persistent scratch
    state[0x1D34:0x1D37] = bytes((1, 6, 0xFF))  # Elly, Emeralda, empty
    state[0x22B1:0x22B4] = b"\x00\x00\x00"  # no party member is in a Gear
    struct.pack_into("<H", state, 0x2318, 0)
    struct.pack_into("<H", state, 0x231A, 720)
    struct.pack_into("<H", state, 0x231C, 0x400)
    struct.pack_into("<H", state, 0x231E, 21)
    struct.pack_into("<H", state, 0x2320, 0)  # source field entry record 0
    result = bytes(state)
    actual = _sha256(result)
    if actual != NORMALIZED_SHA256:
        raise BootstrapError(
            f"Normalized GameState hash mismatch: {actual}; audited layout changed"
        )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("savestate", type=Path)
    parser.add_argument("--zstd", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        savestate = args.savestate.resolve()
        if not savestate.is_file():
            raise BootstrapError(f"DuckStation save does not exist: {savestate}")
        output = args.output.resolve()
        if output.exists() and not args.force:
            raise BootstrapError(f"Refusing to overwrite {output}; pass --force")
        state = normalize_state(
            extract_audited_state(savestate.read_bytes(), _Zstd(args.zstd.resolve()))
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(state)
        print(f"Wrote {output} ({len(state)} bytes, SHA-256 {_sha256(state)})")
        return 0
    except (BootstrapError, OSError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
