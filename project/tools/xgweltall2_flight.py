#!/usr/bin/env python3
"""Checked Disc-1 world-map patch for the standalone flying Weltall-2 mod.

The patch deliberately keeps Xenogears' native Yggdrasil flight task.  It
changes only the input routing and presentation around that task: Jump enters
flight from the player Gear, Cross supplies forward thrust, and either Jump or
Triangle requests the retail landing check.  The invisible Yggdrasil entity
continues to own collision, altitude, camera, and landing validation while the
player's Gear sprite is kept visible at its position.  Takeoff also selects
Weltall-2's native deployed-wing animation and starts two private, Gear-bound
white engine glows; native touchdown removes them and restores the ground
animation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct

from tools.xgworldmap import (
    _retail_safe_lzss_edit,
    decompress_worldmap,
)


DISC1_RETAIL_PACKED_SIZE = 92_180
DISC1_RETAIL_PACKED_SHA256 = (
    "0f7e7a283fc5ef25d4a82960e16b119d09e1ba5594cc02069cf3dd2113f48803"
)
DISC1_RETAIL_DECODED_SIZE = 180_422
DISC1_RETAIL_DECODED_SHA256 = (
    "4c15fd32b3a03d7cd5ea4403dcaabc70abaf99b6aaca65d63d6866803edaac70"
)
DISC1_PATCHED_PACKED_SIZE = 111_572
DISC1_PATCHED_PACKED_SHA256 = (
    "58e97284e5adc228cf86ce539922ab6db34a7e9282b96ee2afcb000f8d3721e5"
)
DISC1_PATCHED_DECODED_SHA256 = (
    "cc86b8f58f53bde64527aec049bcb414c680c56490b90b9dee28cb8b919202a8"
)


class Weltall2FlightPatchError(RuntimeError):
    """Raised when the input overlay is not the audited USA Disc-1 build."""


@dataclass(frozen=True)
class FlightPatchResult:
    packed: bytes
    decoded: bytes
    changed_offsets: tuple[int, ...]


@dataclass(frozen=True)
class _CheckedPatch:
    offset: int
    before: bytes
    after: bytes
    purpose: str

    def __post_init__(self) -> None:
        if not self.before or len(self.before) != len(self.after):
            raise ValueError("Checked MIPS patches must be non-empty and size-neutral")


def _hex(value: str) -> bytes:
    return bytes.fromhex(value)


_REGISTERS = {
    "zero": 0,
    "v0": 2,
    "v1": 3,
    "a0": 4,
    "a1": 5,
    "a2": 6,
    "t0": 8,
    "t1": 9,
    "t2": 10,
    "t3": 11,
    "s1": 17,
}


def _reg(value: str | int) -> int:
    return _REGISTERS[value] if isinstance(value, str) else value


def _i(opcode: int, rs: str | int, rt: str | int, immediate: int) -> int:
    return (
        (opcode << 26)
        | (_reg(rs) << 21)
        | (_reg(rt) << 16)
        | (immediate & 0xFFFF)
    )


def _r(
    rs: str | int,
    rt: str | int,
    rd: str | int,
    shift: int,
    function: int,
) -> int:
    return (
        (_reg(rs) << 21)
        | (_reg(rt) << 16)
        | (_reg(rd) << 11)
        | ((shift & 0x1F) << 6)
        | function
    )


def _j(opcode: int, address: int) -> int:
    return (opcode << 26) | ((address >> 2) & 0x03FFFFFF)


def _words(*values: int) -> bytes:
    return struct.pack(f"<{len(values)}I", *values)


def _lui(rt: str | int, immediate: int) -> int:
    return _i(0x0F, "zero", rt, immediate)


def _lw(rt: str | int, immediate: int, rs: str | int) -> int:
    return _i(0x23, rs, rt, immediate)


def _lhu(rt: str | int, immediate: int, rs: str | int) -> int:
    return _i(0x25, rs, rt, immediate)


def _lbu(rt: str | int, immediate: int, rs: str | int) -> int:
    return _i(0x24, rs, rt, immediate)


def _sh(rt: str | int, immediate: int, rs: str | int) -> int:
    return _i(0x29, rs, rt, immediate)


def _sw(rt: str | int, immediate: int, rs: str | int) -> int:
    return _i(0x2B, rs, rt, immediate)


def _addiu(rt: str | int, rs: str | int, immediate: int) -> int:
    return _i(0x09, rs, rt, immediate)


def _ori(rt: str | int, rs: str | int, immediate: int) -> int:
    return _i(0x0D, rs, rt, immediate)


def _addu(rd: str | int, rs: str | int, rt: str | int) -> int:
    return _r(rs, rt, rd, 0, 0x21)


def _sra(rd: str | int, rt: str | int, shift: int) -> int:
    return _r("zero", rt, rd, shift, 0x03)


def _bne(rs: str | int, rt: str | int, relative_words: int) -> int:
    return _i(0x05, rs, rt, relative_words)


_OVERLAY_RUNTIME_BASE = 0x8006FAF0
_COMMON_PLAYER_GEAR_RETURN = 0x8008D34C
_FLAME_UPDATE_OFFSET = 0x1D214
_FLAME_UPDATE_RUNTIME = _OVERLAY_RUNTIME_BASE + _FLAME_UPDATE_OFFSET
_FLAME_INIT_RUNTIME = _FLAME_UPDATE_RUNTIME + 29 * 4
_FLAME_CLEAR_OFFSET = 0x1D300
_FLAME_CLEAR_RUNTIME = _OVERLAY_RUNTIME_BASE + _FLAME_CLEAR_OFFSET
_FLAME_GUARD_OFFSET = 0x1D39C
_FLAME_GUARD_RUNTIME = _OVERLAY_RUNTIME_BASE + _FLAME_GUARD_OFFSET
_SPAWN_WORLDMAP_PARTICLES = 0x80089160
_CLEAR_WORLDMAP_PARTICLES = 0x800894C8
_SPRITE_SET_ANIMATION = 0x800245D8
_TOUCHDOWN_SECOND_CLEAR = 0x8008F840

# World-map effects 0x32..0x3B have no callers in the Disc-1 overlay.  On
# takeoff, effect 0x32 receives two copies of retail effect 0x08's first
# single-particle white engine light.  Their local origins are then pinned to
# the left and right Weltall-2 wing engines.  This avoids the large, expanding
# fire plume produced by effect 0x0B and keeps the visual as two compact wing
# lights.  A private channel avoids stealing any Yggdrasil wake, terrain, or
# scripted world-map effect.
_FLAME_EFFECT = 0x32
_FLAME_SOURCE_EFFECT = 0x08
_PARTICLE_EFFECT_SIZE = 0x2A0
_PARTICLE_RECORD_SIZE = 0x54
_FLAME_RECORDS_SIZE = 2 * _PARTICLE_RECORD_SIZE

_FLAME_UPDATE_WORDS = (
    _lui("t0", 0x1F80),
    _lw("v0", 0x28, "s1"),
    0,  # PSX load delay
    _sra("v0", "v0", 12),
    _sh("v0", 0x00A8, "t0"),
    _lw("v0", 0x2C, "s1"),
    0,
    _sra("v0", "v0", 12),
    _sh("v0", 0x00AA, "t0"),
    _lw("v0", 0x30, "s1"),
    0,
    _sra("v0", "v0", 12),
    _sh("v0", 0x00AC, "t0"),
    _sh("zero", 0x00AE, "t0"),
    _sh("zero", 0x00A0, "t0"),
    _lhu("v0", 0x48, "s1"),
    0,
    _sh("v0", 0x00A2, "t0"),
    _lui("v1", 0x800A),
    _lhu("v1", -0x42C4, "v1"),  # worldmapRotation.vz
    0,
    _sh("v1", 0x00A4, "t0"),
    _sh("zero", 0x00A6, "t0"),
    _addiu("a0", "zero", _FLAME_EFFECT),
    _ori("a1", "t0", 0x00A8),
    _j(0x03, _SPAWN_WORLDMAP_PARTICLES),
    _ori("a2", "t0", 0x00A0),
    _j(0x02, _COMMON_PLAYER_GEAR_RETURN),
    0,
)

_flame_source_offset = _FLAME_SOURCE_EFFECT * _PARTICLE_EFFECT_SIZE
_flame_target_offset = _FLAME_EFFECT * _PARTICLE_EFFECT_SIZE
_FLAME_INIT_WORDS = (
    _lui("v0", 0x800A),
    _lw("v0", -0x4340, "v0"),  # current world-map particle table
    0,
    _addiu("t0", "v0", _flame_source_offset),
    _ori("t1", "zero", _flame_target_offset),
    _addu("t1", "v0", "t1"),
    # Duplicate one compact native light record into the private channel's
    # first two slots so both wings use precisely the same visual.
    _addiu("t2", "zero", _PARTICLE_RECORD_SIZE // 4),
    _lw("t3", 0, "t0"),
    _addiu("t0", "t0", 4),
    _sw("t3", 0, "t1"),
    _sw("t3", _PARTICLE_RECORD_SIZE, "t1"),
    _addiu("t1", "t1", 4),
    _addiu("t2", "t2", -1),
    _bne("t2", "zero", -7),
    0,
    # t1 now points at the second private record.  Give both copies identical
    # start/end origins and zero the preset's tiny Z drift.  With one particle
    # per record, this produces fixed white wing lights rather than a trail.
    _lui("v1", 0xFFD1),
    _addiu("v1", "v1", -24),       # x=-24, y=-48
    _sw("v1", -0x30, "t1"),
    _sw("v1", -0x28, "t1"),
    _sh("zero", -0x24, "t1"),
    _lui("v1", 0xFFD0),
    _ori("v1", "v1", 24),          # x=+24, y=-48
    _sw("v1", 0x24, "t1"),
    _sw("v1", 0x2C, "t1"),
    _sh("zero", 0x30, "t1"),
    0,  # preserve the checked helper/cave boundary
    _j(0x03, _CLEAR_WORLDMAP_PARTICLES),
    _addiu("a0", "zero", _FLAME_EFFECT),
    _j(0x02, _COMMON_PLAYER_GEAR_RETURN),
    0,
)

_FLAME_HELPERS = _words(*_FLAME_UPDATE_WORDS, *_FLAME_INIT_WORDS)
assert len(_FLAME_UPDATE_WORDS) == 29
assert _FLAME_INIT_RUNTIME == 0x8008CD78
assert len(_FLAME_HELPERS) == 236

# The retail touchdown sequence clears particle channels 0 and 1.  Redirect
# its first call through this wrapper so channel 0 is still cleared, then clear
# the private wing-light channel and rejoin the untouched native channel-1 call.
# The wrapper occupies the now-unreachable tail of the old multi-party boarding
# state 9, immediately after the flame initializer.
_FLAME_CLEAR_WORDS = (
    _j(0x03, _CLEAR_WORLDMAP_PARTICLES),
    0,  # a0 remains the retail value 0 from the entry jump's delay slot
    _j(0x03, _CLEAR_WORLDMAP_PARTICLES),
    _addiu("a0", "zero", _FLAME_EFFECT),
    _j(0x02, _TOUCHDOWN_SECOND_CLEAR),
    0,
    0,
    0,
)
_FLAME_CLEAR_HELPER = _words(*_FLAME_CLEAR_WORDS)
assert len(_FLAME_CLEAR_HELPER) == 32
assert _FLAME_CLEAR_OFFSET == _FLAME_UPDATE_OFFSET + len(_FLAME_HELPERS)

# An in-game world-map save can be made while flying.  Loading that save
# reconstructs player state 2, but retail sprite creation selects animation 0
# and the newly loaded particle table has no private light template.  Check
# both pieces once per state-2 update: ordinary flight takes the fast path,
# while a resumed flight restores animation 1 and runs the existing template
# initializer before the next update spawns the glows.
_FLAME_GUARD_WORDS = (
    _lw("a0", 0x4C, "s1"),
    0,
    _lbu("v0", 0xAF, "a0"),
    0,
    _addiu("v1", "zero", 1),
    _bne("v0", "v1", 10),         # -> initialize at 0x8008CECC
    0,
    _lui("t0", 0x800A),
    _lw("t0", -0x4340, "t0"),     # current world-map particle table
    0,
    _ori("v0", "zero", _flame_target_offset + 0x0C),
    _addu("t0", "t0", "v0"),
    _lhu("v0", 0, "t0"),          # first private emitter's count
    0,
    _bne("v0", "zero", -113),     # -> regular updater at 0x8008CD04
    0,
    _j(0x03, _SPRITE_SET_ANIMATION),
    _addiu("a1", "zero", 1),
    _j(0x02, _FLAME_INIT_RUNTIME),
    0,
)
_FLAME_GUARD_HELPER = _words(*_FLAME_GUARD_WORDS)
assert len(_FLAME_GUARD_HELPER) == 80
assert _FLAME_GUARD_RUNTIME == 0x8008CE8C


# Decoded offsets are used here because the retail-safe LZSS editor preserves
# all untouched command groups.  The overlay's runtime code base is 0x8006FAF0.
_PATCHES = (
    _CheckedPatch(
        0x14E44,
        _hex("21 A0 00 00"),                  # move s4,zero
        _hex("04 00 14 24"),                  # addiu s4,zero,4
        "start model rendering at index four (hide Yggdrasil models 0..3)",
    ),
    _CheckedPatch(
        0x14EB8,
        _hex("21 90 00 00"),                  # move s2,zero
        _hex("50 01 12 24"),                  # addiu s2,zero,0x150
        "start the model pointer at four 0x54-byte records",
    ),
    _CheckedPatch(
        0x1CEDC,
        _hex("08 00 02 24"),                  # addiu v0,zero,8
        _hex("0A 00 02 24"),                  # addiu v0,zero,0xA
        "skip multi-member boarding and enter the repurposed launch state",
    ),
    _CheckedPatch(
        0x1D1E4,
        _hex(
            "0A 80 03 3C 24 BE 63 8C 00 00 00 00 A8 03 62 8C "
            "00 00 00 00 28 00 22 AE B0 03 62 8C 00 00 00 00 "
            "30 00 22 AE C8 03 62 94 D3 34 02 08 48 00 22 A6"
        ),
        _hex(
            "0A 80 03 3C 24 BE 63 8C 24 00 20 A6 A8 03 62 8C "
            "AC 03 64 8C 28 00 22 AE B0 03 62 8C 2C 00 24 AE "
            "C8 03 64 94 30 00 22 AE A3 33 02 08 48 00 24 A6"
        ),
        "show/synchronize the player Gear, then guard/update its flight visuals",
    ),
    _CheckedPatch(
        _FLAME_UPDATE_OFFSET,
        _hex(
            "07 80 03 3C 69 F3 63 90 FF 00 02 24 19 01 62 10 "
            "01 00 02 24 07 80 03 3C E6 F8 63 90 00 00 00 00 "
            "0D 00 62 14 02 00 04 24 05 00 04 24 DC 5D 02 0C "
            "01 00 05 24 84 01 40 10 00 00 00 00 20 00 22 96 "
            "0A 80 03 3C 60 BD 63 90 01 00 42 24 86 00 23 A6 "
            "D3 34 02 08 20 00 22 A6 DC 5D 02 0C 01 00 05 24 "
            "05 00 04 24 0A 80 03 3C 24 BE 63 8C 0A 80 02 3C "
            "60 BD 42 90 08 00 05 24 DC 5D 02 0C 06 01 62 A4 "
            "5E 34 02 08 00 00 00 00 07 80 03 3C 6A F3 63 90 "
            "FF 00 02 24 F7 00 62 10 01 00 02 24 07 80 03 3C "
            "E7 F8 63 90 00 00 00 00 0D 00 62 14 03 00 04 24 "
            "06 00 04 24 DC 5D 02 0C 01 00 05 24 62 01 40 10 "
            "00 00 00 00 20 00 22 96 0A 80 03 3C 60 BD 63 90 "
            "01 00 42 24 06 01 23 A6 D3 34 02 08 20 00 22 A6 "
            "DC 5D 02 0C 01 00 05 24 06 00 04 24"
        ),
        _FLAME_HELPERS,
        "replace unreachable multi-party boarding states with private wing-light helpers",
    ),
    _CheckedPatch(
        _FLAME_CLEAR_OFFSET,
        _hex(
            "0A 80 03 3C 24 BE 63 8C 0A 80 02 3C 60 BD 42 90 "
            "08 00 05 24 DC 5D 02 0C 86 01 62 A4 5E 34 02 08"
        ),
        _FLAME_CLEAR_HELPER,
        "preserve native touchdown cleanup while also clearing the wing lights",
    ),
    _CheckedPatch(
        0x1D324,
        _hex(
            "28 00 24 26 38 00 26 26 48 00 27 26 0A 80 02 3C "
            "60 BD 42 90 0A 80 05 3C 24 BE A5 8C C0 11 02 00 "
            "21 28 A2 00 71 50 02 0C 28 00 A5 24 0A 80 03 3C "
            "60 BD 63 90 0A 80 02 3C 24 BE 42 8C C0 19 03 00 "
            "21 18 62 00 28 00 62 8C 01 00 05 24 03 13 02 00 "
            "50 00 22 AE 30 00 62 8C 4C 00 24 8E 03 13 02 00 "
            "76 91 00 0C 54 00 22 AE 20 00 22 96 00 00 00 00 "
            "01 00 42 24 20 00 22 A6"
        ),
        _hex(
            "0A 80 03 3C 24 BE 63 8C 00 00 00 00 28 00 22 8E "
            "2C 00 24 8E A8 03 62 AC 30 00 22 8E AC 03 64 AC "
            "34 00 24 8E B0 03 62 AC 48 00 22 96 B4 03 64 AC "
            "C8 03 62 A4 0C 00 02 24 20 00 22 A6 4C 00 24 8E "
            "76 91 00 0C 01 00 05 24 5E 33 02 08 00 00 00 00 "
            "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
            "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
            "00 00 00 00 00 00 00 00"
        ),
        "move entity seven to Weltall-2, deploy its wings, and initialize lights",
    ),
    _CheckedPatch(
        _FLAME_GUARD_OFFSET,
        _hex(
            "B2 2F 02 0C 21 20 20 02 03 00 03 24 05 00 43 14 "
            "00 00 00 00 20 00 22 96 00 00 00 00 01 00 42 24 "
            "20 00 22 A6 0A 80 05 3C 5C D5 A5 24 28 00 22 8E "
            "2C 00 23 8E 30 00 24 8E 00 00 A2 AC 04 00 A3 AC "
            "08 00 A4 AC 34 00 22 8E 00 00 00 00 0C 00 A2 AC"
        ),
        _FLAME_GUARD_HELPER,
        "restore deployed wings and the light template after an airborne save load",
    ),
    _CheckedPatch(
        0x1F064,
        _hex("F5 2F 02 0C"),                  # jal addWorldmapDynamicCollisions
        _hex("00 00 00 00"),                  # nop
        "remove the hidden parked Yggdrasil's ground collision",
    ),
    _CheckedPatch(
        0x1FD48,
        _hex("32 25 02 0C"),                  # jal clearWorldmapParticles
        _words(_j(0x02, _FLAME_CLEAR_RUNTIME)),
        "route touchdown through additive channel 0/0x32 cleanup",
    ),
    _CheckedPatch(
        0x21288,
        _hex("20 00 42 30"),                  # andi v0,v0,0x20
        _hex("80 00 42 30"),                  # andi v0,v0,0x80
        "use the Gear Jump action to request takeoff",
    ),
    _CheckedPatch(
        0x21294,
        _hex(
            "0A 80 02 3C 38 D7 42 90 00 00 00 00 1B 00 40 14 "
            "03 00 02 24"
        ),
        _hex(
            "0A 80 02 3C 07 00 03 24 60 BD 43 A0 80 43 02 08 "
            "03 00 02 24"
        ),
        "select hidden vehicle entity seven and return the board/takeoff result",
    ),
    _CheckedPatch(
        0x2177C,
        _hex("80 00 62 30"),                  # andi v0,v1,0x80
        _hex("20 00 62 30"),                  # andi v0,v1,0x20
        "map held Cross to native forward/reverse thrust",
    ),
    _CheckedPatch(
        0x217B8,
        _hex("80 00 42 30"),                  # andi v0,v0,0x80
        _hex("20 00 42 30"),                  # andi v0,v0,0x20
        "retain native thrust clamping while Cross is held",
    ),
    _CheckedPatch(
        0x21880,
        _hex("20 00 42 30"),                  # andi v0,v0,0x20
        _hex("00 00 42 30"),                  # andi v0,v0,0
        "prevent Cross thrust from entering a world-map location",
    ),
    _CheckedPatch(
        0x218AC,
        _hex("40 00 42 30"),                  # andi v0,v0,0x40
        _hex("90 00 42 30"),                  # andi v0,v0,0x90
        "request native landing on a new Jump or Triangle press",
    ),
    _CheckedPatch(
        0x218E4,
        _hex("10 00 42 30"),                  # andi v0,v0,0x10
        _hex("00 00 42 30"),                  # andi v0,v0,0
        "disable the Yggdrasil-deck transition so Triangle only means land",
    ),
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_decoded_flight_patches(decoded: bytes) -> bytes:
    """Apply all size-neutral checked edits to an audited decoded overlay."""

    if len(decoded) != DISC1_RETAIL_DECODED_SIZE:
        raise Weltall2FlightPatchError(
            f"Decoded world-map overlay is {len(decoded)} bytes; expected "
            f"{DISC1_RETAIL_DECODED_SIZE}"
        )
    actual_hash = _sha256(decoded)
    if actual_hash != DISC1_RETAIL_DECODED_SHA256:
        raise Weltall2FlightPatchError(
            "Decoded world-map overlay hash mismatch: "
            f"{actual_hash}; expected {DISC1_RETAIL_DECODED_SHA256}"
        )

    edited = bytearray(decoded)
    previous_end = 0
    for patch in sorted(_PATCHES, key=lambda value: value.offset):
        if patch.offset < previous_end:
            raise Weltall2FlightPatchError("Internal flight patches overlap")
        end = patch.offset + len(patch.before)
        if end > len(edited):
            raise Weltall2FlightPatchError(
                f"{patch.purpose} is outside the decoded overlay"
            )
        found = bytes(edited[patch.offset:end])
        if found != patch.before:
            raise Weltall2FlightPatchError(
                f"Checked context changed at 0x{patch.offset:X} for "
                f"{patch.purpose}: {found.hex(' ')}"
            )
        edited[patch.offset:end] = patch.after
        previous_end = end

    result = bytes(edited)
    patched_hash = _sha256(result)
    if patched_hash != DISC1_PATCHED_DECODED_SHA256:
        raise Weltall2FlightPatchError(
            f"Patched decoded overlay hash mismatch: {patched_hash}"
        )
    return result


def patch_disc1_worldmap_overlay(packed: bytes) -> FlightPatchResult:
    """Patch checked USA Disc-1 canonical file 37 and preserve retail LZSS."""

    if len(packed) != DISC1_RETAIL_PACKED_SIZE:
        raise Weltall2FlightPatchError(
            f"Packed world-map overlay is {len(packed)} bytes; expected "
            f"{DISC1_RETAIL_PACKED_SIZE}"
        )
    actual_hash = _sha256(packed)
    if actual_hash != DISC1_RETAIL_PACKED_SHA256:
        raise Weltall2FlightPatchError(
            f"Packed world-map overlay hash mismatch: {actual_hash}"
        )

    decoded = decompress_worldmap(packed)
    edited = apply_decoded_flight_patches(decoded)
    repacked = _retail_safe_lzss_edit(packed, decoded, edited)
    if decompress_worldmap(repacked) != edited:
        raise Weltall2FlightPatchError("Patched world-map overlay failed round trip")
    packed_hash = _sha256(repacked)
    if (
        len(repacked) != DISC1_PATCHED_PACKED_SIZE
        or packed_hash != DISC1_PATCHED_PACKED_SHA256
    ):
        raise Weltall2FlightPatchError(
            "Patched packed overlay identity changed: "
            f"{len(repacked)} bytes, SHA-256 {packed_hash}"
        )
    return FlightPatchResult(
        packed=repacked,
        decoded=edited,
        changed_offsets=tuple(patch.offset for patch in _PATCHES),
    )


__all__ = [
    "DISC1_PATCHED_DECODED_SHA256",
    "DISC1_PATCHED_PACKED_SHA256",
    "DISC1_RETAIL_DECODED_SHA256",
    "DISC1_RETAIL_PACKED_SHA256",
    "FlightPatchResult",
    "Weltall2FlightPatchError",
    "apply_decoded_flight_patches",
    "patch_disc1_worldmap_overlay",
]
