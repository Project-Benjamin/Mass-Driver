"""Opt-in yellow speaker rows in the USA kernel text renderer.

The retail escape 0F 0B stores text-window byte 6D and consumes two bytes.
Only the new sentinel 0F 0B FE consumes three and marks a spoken block. Its
first displayed row uses a shaded PSX sprite with RGB (128,128,0); ordinary
rows keep the native raw-texture mode and white font palette. Each queued
block resets the marker, so narration and other campaigns stay unmodified.

There is no unused tail cave: the EXE's trailing zero bytes are live globals.
Instead, the existing 216-byte escape-04 five-table dispatcher is compacted
to 92 bytes. Its reclaimed 124 bytes contain the two small helpers; the old
escape-0B handler becomes a block-reset helper. No address or file grows.

Audited against configured USA retail and Perfect Works 0.10.2 discs 1/2.
Their renderer regions are identical; unrelated executable/file-table bytes
are preserved rather than requiring one complete-disc-specific EXE hash.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import struct

from shared.tools.xgdisc import INDEX_SECTOR, Mode2Image, USER_DATA_SIZE


class DialogueNameColorError(ValueError):
    """The executable does not match the audited USA renderer."""


CANONICAL_ID = 22
EXE_SIZE = 0x4A000
LOAD_ADDRESS = 0x80010000
LOAD_SIZE = 0x49800
MARKER_TOKEN = "<Opcode:0B:FE>"
MARKER_BYTES = bytes.fromhex("0F 0B FE")
NAME_RGB = (128, 128, 0)
# Retail/PW copies and existing Xenoiso rebuilds prove that these entries,
# including the terminator, are mirrored in the boot EXE. Do not normalize
# the surrounding padding or directory table: they are separate data.
EMBEDDED_FAT_OFFSET = 0x804
FAT_ENTRY_COUNTS = {1: 4152, 2: 4147}
BOOT_FILENAMES = {1: b"SLUS_006.64;1", 2: b"SLUS_006.69;1"}

SUBSTITUTION_ADDRESS = 0x80034188
SUBSTITUTION_END = 0x80034260
MARKER_ADDRESS = 0x800341E4
COLOR_ADDRESS = 0x8003420C
RESET_ADDRESS = 0x80034380
RESET_END = 0x8003439C
DISPATCH_ADDRESS = 0x80018A7C
RESET_HOOK_ADDRESS = 0x80034930
ROW_HOOK_ADDRESSES = (0x80034A84, 0x80034BE8)

_DISPATCH = (
    0x800340BC, 0x800340D8, 0x80034134, 0x80034158,
    SUBSTITUTION_ADDRESS, 0x80034260, 0x800342E8, 0x80034310,
    0x80034338, 0x80034360, 0x80034370, RESET_ADDRESS,
    0x8003439C, 0x800343E0, 0x80034410, 0x80034444,
)
_REGION_IDENTITIES = (
    (0x24880, 0x24DD8, "2d988158a788ba27853e14bc0696b8ac0fafdf2d864e31fd3b1050b5f28c49e4"),
    (0x25088, 0x256A8, "ccf4b85d34631e07598232722802b25d94f9924b4c088b25df28ae1440c8e8a1"),
)


def file_offset(address: int) -> int:
    return address - LOAD_ADDRESS + 0x800


def _i(op: int, source: int, target: int, immediate: int) -> int:
    return (op << 26) | (source << 21) | (target << 16) | (immediate & 0xFFFF)


def _addu(target: int, left: int, right: int) -> int:
    return (left << 21) | (right << 16) | (target << 11) | 0x21


def _j(address: int, *, link: bool = False) -> int:
    return ((3 if link else 2) << 26) | ((address >> 2) & 0x03FFFFFF)


def _pack(*words: int) -> bytes:
    return struct.pack(f"<{len(words)}I", *words)


def _compact_dispatch() -> bytes:
    # v0/v1/a0/a1 are dead or call arguments at the two native continuations.
    # s0, s3 and all other live registers retain their original behavior.
    table = SUBSTITUTION_ADDRESS + 21 * 4
    words = (
        _i(0x23, 16, 2, 0x1C),       # lw v0,current string(s0)
        _i(0x21, 16, 5, 0x80),       # lh a1,selected item (fills load delay)
        _i(9, 2, 2, 1),
        _i(0x2B, 16, 2, 0x1C),
        _i(0x0C, 5, 3, 0xFF00),
        (3 << 16) | (3 << 11) | (8 << 6) | 2,  # srl v1,v1,8
        _i(0x0B, 3, 2, 5),
        _i(4, 2, 0, 11),             # beqz v0,invalid (word 19)
        0,
        _i(0x0F, 0, 4, table >> 16),
        _addu(4, 4, 3),
        _i(0x24, 4, 3, table & 0xFFFF),
        _i(0x0F, 0, 2, 0x8006),
        _i(0x23, 2, 2, -0x6CA0),     # native message-table root
        _i(0x0C, 5, 5, 0xFF),
        _addu(2, 2, 3),
        _i(0x23, 2, 4, 0),
        _j(0x80034474),
        0,
        _j(0x800345A8),
        _i(9, 19, 19, -1),           # native invalid-case delay slot
    )
    return _pack(*words) + bytes((0x58, 0x5C, 0x44, 0xCC, 0xC8, 0, 0, 0))


def _marker_handler() -> bytes:
    return _pack(
        _i(0x23, 16, 3, 0x1C),
        0,
        _i(0x24, 3, 2, 2),
        _i(9, 3, 3, 2),              # native consumption for all other values
        _i(0x0E, 2, 4, 0xFE),
        _i(0x0B, 4, 4, 1),           # only sentinel FE consumes one extra byte
        _addu(3, 3, 4),
        _i(0x2B, 16, 3, 0x1C),
        _j(0x800345A4),
        _i(0x28, 16, 2, 0x6D),
    )


def _row_color_helper() -> bytes:
    # Both call sites are inside a function that saves RA at sp+7C and
    # restores it on exit. v1 is overwritten on both branches immediately
    # after the helper returns. No saved register or stack byte is changed.
    return _pack(
        _i(0x24, 16, 2, 0x6D),
        _i(0x0D, 0, 3, 0xFE),
        _i(5, 2, 3, 15),             # ordinary -> word 18
        0,
        _i(5, 20, 0, 13),            # only displayed row s4 == 0 is a name
        0,
        _i(0x23, 16, 3, 0x28),
        _i(0x0D, 0, 2, 128),
        _addu(3, 3, 17),             # physical row offset s1
        _addu(3, 3, 18),             # double-buffer parity offset s2
        _i(0x28, 3, 2, 4),
        _i(0x28, 3, 2, 5),
        _i(0x28, 3, 0, 6),
        _i(0x28, 3, 2, 0x18),
        _i(0x28, 3, 2, 0x19),
        _i(0x28, 3, 0, 0x1A),
        (31 << 21) | 8,              # jr ra
        _addu(2, 0, 0),              # select/shade row zero in native caller
        _i(0x24, 16, 2, 0x6E),       # original selection for ordinary rows
        (31 << 21) | 8,
        0,
    )


COMPACT_DISPATCH = _compact_dispatch()
MARKER_HANDLER = _marker_handler()
COLOR_HELPER = _row_color_helper()
INJECTED_DISPATCH = COMPACT_DISPATCH + MARKER_HANDLER + COLOR_HELPER
RESET_HELPER = _pack(
    _i(0x29, 16, 0, 0x86),           # displaced native character-delay reset
    _i(0x28, 16, 0, 0x6D),
    _j(0x80034938),
    0,
) + bytes(12)

assert len(COMPACT_DISPATCH) == MARKER_ADDRESS - SUBSTITUTION_ADDRESS
assert len(MARKER_HANDLER) == COLOR_ADDRESS - MARKER_ADDRESS
assert len(INJECTED_DISPATCH) == SUBSTITUTION_END - SUBSTITUTION_ADDRESS
assert len(RESET_HELPER) == RESET_END - RESET_ADDRESS


def patch_executable(source: bytes) -> bytes:
    """Patch only checked kernel code; preserve disc tables and other patches."""
    if (len(source) != EXE_SIZE or source[:8] != b"PS-X EXE"
            or struct.unpack_from("<II", source, 0x18) != (LOAD_ADDRESS, LOAD_SIZE)):
        raise DialogueNameColorError("Expected the audited USA PS-X executable layout")
    for start, stop, expected in _REGION_IDENTITIES:
        if hashlib.sha256(source[start:stop]).hexdigest() != expected:
            raise DialogueNameColorError(f"USA text renderer changed at file {start:#x}..{stop:#x}")
    table_offset = file_offset(DISPATCH_ADDRESS)
    if source[table_offset:table_offset + 64] != _pack(*_DISPATCH):
        raise DialogueNameColorError("USA text escape dispatch table changed")
    result = bytearray(source)
    patches = {
        SUBSTITUTION_ADDRESS: INJECTED_DISPATCH,
        RESET_ADDRESS: RESET_HELPER,
        DISPATCH_ADDRESS + 0xB * 4: _pack(MARKER_ADDRESS),
        RESET_HOOK_ADDRESS: _pack(_j(RESET_ADDRESS), _i(0x29, 16, 0, 0x88)),
        **{address: _pack(_j(COLOR_ADDRESS, link=True), 0) for address in ROW_HOOK_ADDRESSES},
    }
    for address, replacement in patches.items():
        offset = file_offset(address)
        result[offset:offset + len(replacement)] = replacement
    return bytes(result)


def _iso_extent(record: bytes) -> tuple[int, int]:
    if len(record) < 34 or record[0] != len(record) or 33 + record[32] > len(record):
        raise DialogueNameColorError("Invalid ISO9660 directory record")
    extent = struct.unpack_from("<I", record, 2)[0]
    size = struct.unpack_from("<I", record, 10)[0]
    if (extent != struct.unpack_from(">I", record, 6)[0]
            or size != struct.unpack_from(">I", record, 14)[0]):
        raise DialogueNameColorError("ISO9660 extent endian copies disagree")
    return extent, size


def verify_executable_image(
    image_path: Path | str, disc: int, expected_patched: bytes,
) -> dict[str, int | str]:
    """Verify the actual boot EXE, allowing only a correct rebuilt FAT mirror.

    Xenoiso modifies the embedded FAT after placing replacements. Comparing
    canonical 22 byte-for-byte with its staged input would reject that valid
    update; accepting the entire EXE unchecked would miss a discarded patch.
    All other bytes, including padding and the directory table, must match.
    """
    if disc not in FAT_ENTRY_COUNTS:
        raise DialogueNameColorError(f"Expected disc 1 or 2, got {disc}")
    if len(expected_patched) != EXE_SIZE or expected_patched[:8] != b"PS-X EXE":
        raise DialogueNameColorError("Expected a complete staged USA executable")
    image = Mode2Image(image_path)
    entries = image.read_index()
    if len(entries) != FAT_ENTRY_COUNTS[disc]:
        raise DialogueNameColorError("Rebuilt executable FAT entry count changed")
    physical_id = CANONICAL_ID if disc == 1 else CANONICAL_ID - 5
    entry = entries[physical_id]
    if entry.kind != "file" or entry.size != EXE_SIZE:
        raise DialogueNameColorError("Canonical 22 is not the complete boot executable")
    actual = image.extract_entry(entry)
    fat_size = len(entries) * 7
    fat_end = EMBEDDED_FAT_OFFSET + fat_size
    table = image.read_user_data(INDEX_SECTOR, fat_size)
    if actual[EMBEDDED_FAT_OFFSET:fat_end] != table:
        raise DialogueNameColorError("Boot executable's embedded FAT differs from sector 24")
    if (actual[:EMBEDDED_FAT_OFFSET] != expected_patched[:EMBEDDED_FAT_OFFSET]
            or actual[fat_end:] != expected_patched[fat_end:]):
        first = next(offset for offset, (found, expected) in enumerate(zip(actual, expected_patched))
                     if found != expected and not EMBEDDED_FAT_OFFSET <= offset < fat_end)
        raise DialogueNameColorError(f"Boot executable differs from staged patch at file {first:#x}")

    pvd = image.read_user_data(16, USER_DATA_SIZE)
    if pvd[:7] != b"\x01CD001\x01":
        raise DialogueNameColorError("Expected an ISO9660 primary volume descriptor")
    root = pvd[156:156 + pvd[156]]
    root_sector, root_size = _iso_extent(root)
    if not root[25] & 2 or not 0 < root_size <= 1024 * 1024:
        raise DialogueNameColorError("Invalid ISO9660 root directory")
    directory = image.read_user_data(root_sector, root_size)
    found: dict[bytes, tuple[int, int]] = {}
    offset = 0
    while offset < len(directory):
        length = directory[offset]
        if not length:
            offset = (offset // USER_DATA_SIZE + 1) * USER_DATA_SIZE
            continue
        if offset % USER_DATA_SIZE + length > USER_DATA_SIZE:
            raise DialogueNameColorError("ISO9660 record crosses a sector boundary")
        record = directory[offset:offset + length]
        extent = _iso_extent(record)
        name = record[33:33 + record[32]]
        if name in (BOOT_FILENAMES[disc], b"SYSTEM.CNF;1"):
            if name in found or record[25] & 2:
                raise DialogueNameColorError("Ambiguous ISO9660 boot file")
            found[name] = extent
        offset += length
    boot_name = BOOT_FILENAMES[disc]
    if found.get(boot_name) != (entry.sector, entry.size):
        raise DialogueNameColorError("ISO9660 SLUS boot extent does not match canonical 22")
    system = found.get(b"SYSTEM.CNF;1")
    if system is None or not 0 < system[1] <= USER_DATA_SIZE:
        raise DialogueNameColorError("Missing or invalid ISO9660 SYSTEM.CNF")
    config = image.read_user_data(*system)
    match = re.search(rb"(?im)^\s*BOOT\s*=\s*cdrom:\\([^\r\n]+)", config)
    if match is None or match.group(1).strip().upper() != boot_name:
        raise DialogueNameColorError("SYSTEM.CNF does not boot the expected SLUS executable")
    return {
        "canonical_id": CANONICAL_ID,
        "physical_id": physical_id,
        "boot_file": boot_name.decode("ascii"),
        "sector": entry.sector,
        "size": entry.size,
        "embedded_fat_entries": len(entries),
        "sha256": hashlib.sha256(actual).hexdigest(),
    }
