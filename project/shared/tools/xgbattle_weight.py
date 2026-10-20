#!/usr/bin/env python3
"""Restore character body weight as a battle stat in overlay 38.

Xenogears already persists body weight in each 0xA4-byte character record.
The exact conversion used here is:

``weight_hundredths_lb = 22 * (10 * (record[0x77] + record[0x78]) + record[0x79])``

The retail battle loader copies all three bytes, but neither physical damage
nor ATB timing consumes them.  This module patches those two missing reads in
the decoded battle overlay.  Gear combat and enemy combat retain their retail
paths.
"""

from __future__ import annotations

import hashlib
import struct
from typing import Final


class BattleWeightPatchError(ValueError):
    """The supplied battle overlay does not match the audited retail image."""


CHARACTER_RECORD_SIZE: Final = 0xA4
WEIGHT_FIXED_OFFSET: Final = 0x77
WEIGHT_MUTABLE_OFFSET: Final = 0x78
WEIGHT_TENTHS_OFFSET: Final = 0x79

# Fei's new-game 167.20 lb weight is the neutral point.  Physical Attack moves
# by 5/22 percent (about 0.2273%) per pound, while ATB readiness moves by one
# tick per 4.40 lb.  These curves make every retail weight item meaningful
# without letting weight erase the much larger role of Attack and Agility.
POUNDS_HUNDREDTHS_PER_NATIVE_TENTH: Final = 22
POUNDS_HUNDREDTHS_PER_NATIVE_WHOLE: Final = 220
NEUTRAL_WEIGHT_HUNDREDTHS_LB: Final = 16_720
PHYSICAL_SCALE_DENOMINATOR_LB100: Final = 44_000
PHYSICAL_SCALE_BIAS_LB100: Final = 27_280
ATB_HUNDREDTHS_LB_PER_TICK: Final = 440

# The injected MIPS reduces the pound formulas by their exact conversion
# factors so the two helpers fit the audited 184-byte cave.
_NATIVE_PHYSICAL_SCALE_DENOMINATOR: Final = (
    PHYSICAL_SCALE_DENOMINATOR_LB100 // POUNDS_HUNDREDTHS_PER_NATIVE_TENTH
)
_NATIVE_PHYSICAL_SCALE_BIAS: Final = (
    PHYSICAL_SCALE_BIAS_LB100 // POUNDS_HUNDREDTHS_PER_NATIVE_TENTH
)
_NATIVE_NEUTRAL_WEIGHT_WHOLE: Final = (
    NEUTRAL_WEIGHT_HUNDREDTHS_LB // POUNDS_HUNDREDTHS_PER_NATIVE_WHOLE
)
_NATIVE_WHOLE_STEPS_PER_ATB_TICK: Final = (
    ATB_HUNDREDTHS_LB_PER_TICK // POUNDS_HUNDREDTHS_PER_NATIVE_WHOLE
)
# Retail subtracts a subsequent random term in [-4, +3].  Four is therefore
# the smallest safe pre-jitter value: the final countdown remains at least 1.
MIN_PRE_JITTER_ATB_TICKS: Final = 4

# The anthology is built from the untouched USA retail discs.  The older
# Mass Driver worktree uses a 12-byte-larger Perfect Works overlay variant;
# both contain the same audited damage and ATB hook instructions.  Keep the
# legacy identity stable while also accepting the clean retail payload.
BATTLE_OVERLAY_CLEAN_DECODED_SIZE: Final = 343_936
BATTLE_OVERLAY_CLEAN_DECODED_RETAIL_SHA256: Final = (
    "1830b4ef1fe37129972fc310dfad534f8161d6c0b123e74254c3711334a3e291"
)
BATTLE_OVERLAY_CLEAN_DECODED_PATCHED_SHA256: Final = (
    "9b20572d47065423147a5fa329b4f0c0780dd314a3b332ecca0813d95ea995ad"
)

BATTLE_OVERLAY_DECODED_SIZE: Final = 343_948
BATTLE_OVERLAY_DECODED_RETAIL_SHA256: Final = (
    "ad4586923095715288377caea89f2cd15d70a2f80ef53394e2faec22b2e0b825"
)
BATTLE_OVERLAY_DECODED_PATCHED_SHA256: Final = (
    "0b1b6a530abc4f7faacd0743a9d31214d4c81f4f1d464caeece7b35ab9bed580"
)

# Overlay 38 is loaded at this address.  Its first export confirms the base:
# decoded +0x4B40 is the function at 0x80074630.
BATTLE_OVERLAY_LOAD_BASE: Final = 0x8006FAF0

DAMAGE_HOOK_OFFSET: Final = 0x275D8
ATB_HOOK_OFFSET: Final = 0x29134
CODE_CAVE_OFFSET: Final = 0x2B8B8
CODE_CAVE_SIZE: Final = 0xB8

# Clean retail has no naturally empty 176-byte code cave.  This straight-line
# initialization routine needlessly reloads the same 0x8007 high half before
# every store.  Removing those 65 redundant LUI instructions is semantics-
# preserving (there are no jump or branch targets inside the span) and opens a
# 260-byte cave without moving the following function.
CLEAN_COMPACTION_START: Final = 0x2B750
CLEAN_COMPACTION_END: Final = 0x2B97C
CLEAN_REDUNDANT_LUI: Final = struct.pack("<I", 0x3C018007)
CLEAN_CODE_CAVE_OFFSET: Final = 0x2B878
CLEAN_CODE_CAVE_SIZE: Final = CLEAN_COMPACTION_END - CLEAN_CODE_CAVE_OFFSET

DAMAGE_HOOK_RETAIL: Final = bytes.fromhex(
    "00 00 00 00 "  # nop
    "58 00 47 90"  # lbu a3, 0x58(v0), retained as the JAL delay slot
)
ATB_HOOK_RETAIL: Final = bytes.fromhex(
    "8E FE 00 0C "  # jal 0x8003FA38 (xenoRand)
    "23 80 50 00"  # subu s0, v0, s0, retained as the JAL delay slot
)
XENO_RAND_ADDRESS: Final = 0x8003FA38


def weight_hundredths_lb(record: bytes | bytearray | memoryview) -> int:
    """Return body weight in hundredths of a pound."""

    if len(record) < WEIGHT_TENTHS_OFFSET + 1:
        raise ValueError(
            "character record is too short for weight bytes: "
            f"{len(record)} < {WEIGHT_TENTHS_OFFSET + 1}"
        )
    tenths_digit = record[WEIGHT_TENTHS_OFFSET]
    if tenths_digit > 9:
        raise ValueError(
            f"character weight tenths digit is not decimal: {tenths_digit}"
        )
    native_weight = 10 * (
        record[WEIGHT_FIXED_OFFSET] + record[WEIGHT_MUTABLE_OFFSET]
    ) + tenths_digit
    return POUNDS_HUNDREDTHS_PER_NATIVE_TENTH * native_weight


def scale_physical_attack(attack: int, weight_hundredths_lb: int) -> int:
    """Scale the physical Attack component by the restored weight curve.

    A 167.20 lb character is unchanged.  Each pound above or below that point
    changes the component by 5/22 percent (about 0.2273%); integer division
    matches the reduced MIPS implementation.
    """

    if not 0 <= attack <= 0xFF:
        raise ValueError(f"physical Attack must be an unsigned byte: {attack}")
    if weight_hundredths_lb < 0:
        raise ValueError(f"weight cannot be negative: {weight_hundredths_lb}")
    return attack * (
        weight_hundredths_lb + PHYSICAL_SCALE_BIAS_LB100
    ) // (
        PHYSICAL_SCALE_DENOMINATOR_LB100
    )


def _truncate_toward_zero(value: int, divisor: int) -> int:
    if value >= 0:
        return value // divisor
    return -((-value) // divisor)


def adjust_atb_ticks(base_ticks: int, weight_hundredths_lb: int) -> int:
    """Apply body weight to a character's retail ATB-ready tick count.

    Positive ticks are slower.  The retail byte layout quantizes this path to
    2.20 lb steps; signed division then truncates toward zero exactly as the
    R3000A does.
    """

    if base_ticks < 0:
        raise ValueError(f"base ATB ticks cannot be negative: {base_ticks}")
    if weight_hundredths_lb < 0:
        raise ValueError(f"weight cannot be negative: {weight_hundredths_lb}")
    quantized_weight = (
        weight_hundredths_lb
        - weight_hundredths_lb % POUNDS_HUNDREDTHS_PER_NATIVE_WHOLE
    )
    delta = _truncate_toward_zero(
        quantized_weight - NEUTRAL_WEIGHT_HUNDREDTHS_LB,
        ATB_HUNDREDTHS_LB_PER_TICK,
    )
    return max(MIN_PRE_JITTER_ATB_TICKS, base_ticks + delta)


_REGISTERS: Final = {
    "zero": 0,
    "v0": 2,
    "v1": 3,
    "a0": 4,
    "a1": 5,
    "a2": 6,
    "a3": 7,
    "t0": 8,
    "t1": 9,
    "t2": 10,
    "s0": 16,
    "ra": 31,
}


def _register(value: str | int) -> int:
    return _REGISTERS[value] if isinstance(value, str) else value


def _r_type(
    rs: str | int = 0,
    rt: str | int = 0,
    rd: str | int = 0,
    shift: int = 0,
    function: int = 0,
) -> int:
    return (
        (_register(rs) << 21)
        | (_register(rt) << 16)
        | (_register(rd) << 11)
        | (shift << 6)
        | function
    )


def _i_type(
    opcode: int,
    rs: str | int,
    rt: str | int,
    immediate: int,
) -> int:
    return (
        (opcode << 26)
        | (_register(rs) << 21)
        | (_register(rt) << 16)
        | (immediate & 0xFFFF)
    )


def _jump(opcode: int, address: int) -> int:
    return (opcode << 26) | ((address >> 2) & 0x03FFFFFF)


def _lui(rt: str | int, immediate: int) -> int:
    return _i_type(0x0F, "zero", rt, immediate)


def _lw(rt: str | int, immediate: int, rs: str | int) -> int:
    return _i_type(0x23, rs, rt, immediate)


def _lbu(rt: str | int, immediate: int, rs: str | int) -> int:
    return _i_type(0x24, rs, rt, immediate)


def _addiu(rt: str | int, rs: str | int, immediate: int) -> int:
    return _i_type(0x09, rs, rt, immediate)


def _ori(rt: str | int, rs: str | int, immediate: int) -> int:
    return _i_type(0x0D, rs, rt, immediate)


def _andi(rt: str | int, rs: str | int, immediate: int) -> int:
    return _i_type(0x0C, rs, rt, immediate)


def _sltiu(rt: str | int, rs: str | int, immediate: int) -> int:
    return _i_type(0x0B, rs, rt, immediate)


def _slti(rt: str | int, rs: str | int, immediate: int) -> int:
    return _i_type(0x0A, rs, rt, immediate)


def _branch(
    opcode: int,
    rs: str | int,
    rt: str | int,
    relative_words: int,
) -> int:
    return _i_type(opcode, rs, rt, relative_words)


def _sll(rd: str | int, rt: str | int, shift: int) -> int:
    return _r_type(rt=rt, rd=rd, shift=shift)


def _addu(rd: str | int, rs: str | int, rt: str | int) -> int:
    return _r_type(rs, rt, rd, function=0x21)


def _subu(rd: str | int, rs: str | int, rt: str | int) -> int:
    return _r_type(rs, rt, rd, function=0x23)


def _slt(rd: str | int, rs: str | int, rt: str | int) -> int:
    return _r_type(rs, rt, rd, function=0x2A)


def _multu(rs: str | int, rt: str | int) -> int:
    return _r_type(rs, rt, function=0x19)


def _div(rs: str | int, rt: str | int) -> int:
    return _r_type(rs, rt, function=0x1A)


def _divu(rs: str | int, rt: str | int) -> int:
    return _r_type(rs, rt, function=0x1B)


def _mflo(rd: str | int) -> int:
    return _r_type(rd=rd, function=0x12)


def _jr(rs: str | int) -> int:
    return _r_type(rs=rs, function=0x08)


def _pack_words(words: tuple[int, ...]) -> bytes:
    return struct.pack(f"<{len(words)}I", *words)


DAMAGE_HELPER_ADDRESS: Final = BATTLE_OVERLAY_LOAD_BASE + CODE_CAVE_OFFSET

# The hook is reached for the retail on-foot damage path.  The pointer-range
# guard narrows that path from "not a Gear" to the three player slots, leaving
# enemy Attack untouched.  Ether selects a separate component downstream, so
# the adjusted a3 is consumed only by physical actions.
DAMAGE_HELPER_WORDS: Final = (
    _lui("t0", 0x800C),
    _lw("t0", 0x34B0, "t0"),
    _lbu("t1", WEIGHT_FIXED_OFFSET, "v0"),  # LW load-delay filler
    _subu("t0", "v0", "t0"),
    _sltiu("t0", "t0", 0x450),  # 3 * sizeof(battle entity, 0x170)
    _branch(0x04, "t0", "zero", 14),
    _lbu("t0", WEIGHT_MUTABLE_OFFSET, "v0"),
    _lbu("t2", WEIGHT_TENTHS_OFFSET, "v0"),  # LBU load-delay filler
    _addu("t0", "t0", "t1"),
    _sll("t1", "t0", 1),
    _sll("t0", "t0", 3),
    _addu("t0", "t0", "t1"),
    _addu("t0", "t0", "t2"),  # full native decimal weight composite
    _addiu("t0", "t0", _NATIVE_PHYSICAL_SCALE_BIAS),
    _multu("a3", "t0"),
    _mflo("a3"),
    _ori("t0", "zero", _NATIVE_PHYSICAL_SCALE_DENOMINATOR),
    # R3000 exception recovery requires two non-HI/LO instructions between
    # MFLO and the next multiply/divide operation.  ORI is the first; this
    # delay instruction is the second.
    0,
    _divu("a3", "t0"),
    _mflo("a3"),
    _jr("ra"),
    0,
)
DAMAGE_HELPER: Final = _pack_words(DAMAGE_HELPER_WORDS)

ATB_HELPER_OFFSET: Final = CODE_CAVE_OFFSET + len(DAMAGE_HELPER)
ATB_HELPER_ADDRESS: Final = BATTLE_OVERLAY_LOAD_BASE + ATB_HELPER_OFFSET

# The original RNG call becomes a call here.  After applying weight only to an
# on-foot player record, the final jump tail-calls xenoRand, so its return
# address and the retail +/-4 tick randomization remain exactly as before.
ATB_HELPER_WORDS: Final = (
    _lui("t0", 0x800C),
    _lw("t0", 0x34B0, "t0"),
    _lbu("t1", WEIGHT_FIXED_OFFSET, "a2"),  # LW load-delay filler
    _subu("t0", "a2", "t0"),
    _sltiu("t0", "t0", 0x450),
    _branch(0x04, "t0", "zero", 14),
    _lbu("t0", 0x15A, "a2"),  # branch delay: entity flags
    _lbu("v0", WEIGHT_MUTABLE_OFFSET, "a2"),
    _andi("t0", "t0", 0x80),  # Gear flag
    _branch(0x05, "t0", "zero", 10),
    _addu("t0", "t1", "v0"),  # branch delay; v0 load is now ready
    _addiu("t0", "t0", -_NATIVE_NEUTRAL_WEIGHT_WHOLE),
    _ori("t1", "zero", _NATIVE_WHOLE_STEPS_PER_ATB_TICK),
    _div("t0", "t1"),
    _mflo("t0"),
    _addu("s0", "s0", "t0"),
    _slti("t0", "s0", MIN_PRE_JITTER_ATB_TICKS),
    _branch(0x04, "t0", "zero", 2),
    0,
    _ori("s0", "zero", MIN_PRE_JITTER_ATB_TICKS),
    _jump(0x02, XENO_RAND_ADDRESS),
    0,
)
ATB_HELPER: Final = _pack_words(ATB_HELPER_WORDS)

INJECTED_CODE: Final = DAMAGE_HELPER + ATB_HELPER
if len(INJECTED_CODE) > CODE_CAVE_SIZE:  # pragma: no cover - import invariant
    raise RuntimeError("battle-weight helpers exceed the audited code cave")

DAMAGE_HOOK_PATCHED: Final = struct.pack(
    "<I", _jump(0x03, DAMAGE_HELPER_ADDRESS)
) + DAMAGE_HOOK_RETAIL[4:]
ATB_HOOK_PATCHED: Final = struct.pack(
    "<I", _jump(0x03, ATB_HELPER_ADDRESS)
) + ATB_HOOK_RETAIL[4:]

CLEAN_DAMAGE_HELPER_ADDRESS: Final = (
    BATTLE_OVERLAY_LOAD_BASE + CLEAN_CODE_CAVE_OFFSET
)
CLEAN_ATB_HELPER_ADDRESS: Final = CLEAN_DAMAGE_HELPER_ADDRESS + len(DAMAGE_HELPER)
CLEAN_DAMAGE_HOOK_PATCHED: Final = struct.pack(
    "<I", _jump(0x03, CLEAN_DAMAGE_HELPER_ADDRESS)
) + DAMAGE_HOOK_RETAIL[4:]
CLEAN_ATB_HOOK_PATCHED: Final = struct.pack(
    "<I", _jump(0x03, CLEAN_ATB_HELPER_ADDRESS)
) + ATB_HOOK_RETAIL[4:]


def _compact_clean_retail_cave(decoded: bytes) -> bytes:
    """Compact one target-free retail initializer and return the overlay."""

    region = decoded[CLEAN_COMPACTION_START:CLEAN_COMPACTION_END]
    if len(region) != CLEAN_COMPACTION_END - CLEAN_COMPACTION_START:
        raise BattleWeightPatchError("clean retail compaction span is truncated")
    words = tuple(region[index:index + 4] for index in range(0, len(region), 4))
    if len(words) != 139 or words.count(CLEAN_REDUNDANT_LUI) != 65:
        raise BattleWeightPatchError("clean retail initializer context changed")
    compact = b"".join(word for word in words if word != CLEAN_REDUNDANT_LUI)
    if len(compact) != CLEAN_CODE_CAVE_OFFSET - CLEAN_COMPACTION_START:
        raise BattleWeightPatchError("clean retail initializer compacted incorrectly")
    if compact[-8:] != bytes.fromhex("08 00 E0 03 00 00 00 00"):
        raise BattleWeightPatchError("clean retail initializer lost its return")

    result = bytearray(decoded)
    result[CLEAN_COMPACTION_START:CLEAN_COMPACTION_END] = (
        compact + bytes(CLEAN_CODE_CAVE_SIZE)
    )
    return bytes(result)


def _patch_clean_decoded_battle_overlay(decoded: bytes) -> bytes:
    if decoded[DAMAGE_HOOK_OFFSET:DAMAGE_HOOK_OFFSET + 8] != DAMAGE_HOOK_RETAIL:
        raise BattleWeightPatchError("clean physical-damage hook context changed")
    if decoded[ATB_HOOK_OFFSET:ATB_HOOK_OFFSET + 8] != ATB_HOOK_RETAIL:
        raise BattleWeightPatchError("clean ATB hook context changed")

    prepared = _compact_clean_retail_cave(decoded)
    cave = prepared[
        CLEAN_CODE_CAVE_OFFSET:CLEAN_CODE_CAVE_OFFSET + CLEAN_CODE_CAVE_SIZE
    ]
    if cave != bytes(CLEAN_CODE_CAVE_SIZE):
        raise BattleWeightPatchError("clean retail code cave preparation failed")
    if len(INJECTED_CODE) > CLEAN_CODE_CAVE_SIZE:
        raise BattleWeightPatchError("battle-weight helpers exceed clean code cave")

    patched = bytearray(prepared)
    patched[
        DAMAGE_HOOK_OFFSET:DAMAGE_HOOK_OFFSET + len(CLEAN_DAMAGE_HOOK_PATCHED)
    ] = CLEAN_DAMAGE_HOOK_PATCHED
    patched[
        ATB_HOOK_OFFSET:ATB_HOOK_OFFSET + len(CLEAN_ATB_HOOK_PATCHED)
    ] = CLEAN_ATB_HOOK_PATCHED
    patched[
        CLEAN_CODE_CAVE_OFFSET:CLEAN_CODE_CAVE_OFFSET + len(INJECTED_CODE)
    ] = INJECTED_CODE
    result = bytes(patched)
    actual_hash = hashlib.sha256(result).hexdigest()
    if actual_hash != BATTLE_OVERLAY_CLEAN_DECODED_PATCHED_SHA256:
        raise BattleWeightPatchError(
            f"patched clean battle-overlay hash mismatch: {actual_hash}"
        )
    return result


def patch_decoded_battle_overlay(decoded: bytes) -> bytes:
    """Patch an exact clean-retail or Perfect-Works overlay-38 payload."""

    actual_hash = hashlib.sha256(decoded).hexdigest()
    if (
        len(decoded) == BATTLE_OVERLAY_CLEAN_DECODED_SIZE
        and actual_hash == BATTLE_OVERLAY_CLEAN_DECODED_RETAIL_SHA256
    ):
        return _patch_clean_decoded_battle_overlay(decoded)
    if (
        len(decoded) != BATTLE_OVERLAY_DECODED_SIZE
        or actual_hash != BATTLE_OVERLAY_DECODED_RETAIL_SHA256
    ):
        raise BattleWeightPatchError(
            "retail decoded battle overlay mismatch: "
            f"{len(decoded)} bytes, {actual_hash}"
        )

    if (
        decoded[DAMAGE_HOOK_OFFSET : DAMAGE_HOOK_OFFSET + 8]
        != DAMAGE_HOOK_RETAIL
    ):
        raise BattleWeightPatchError("physical-damage hook context changed")
    if decoded[ATB_HOOK_OFFSET : ATB_HOOK_OFFSET + 8] != ATB_HOOK_RETAIL:
        raise BattleWeightPatchError("ATB hook context changed")
    cave = decoded[CODE_CAVE_OFFSET : CODE_CAVE_OFFSET + CODE_CAVE_SIZE]
    if cave != bytes(CODE_CAVE_SIZE):
        raise BattleWeightPatchError("audited battle-overlay code cave is occupied")

    patched = bytearray(decoded)
    patched[
        DAMAGE_HOOK_OFFSET : DAMAGE_HOOK_OFFSET + len(DAMAGE_HOOK_PATCHED)
    ] = DAMAGE_HOOK_PATCHED
    patched[ATB_HOOK_OFFSET : ATB_HOOK_OFFSET + len(ATB_HOOK_PATCHED)] = (
        ATB_HOOK_PATCHED
    )
    patched[CODE_CAVE_OFFSET : CODE_CAVE_OFFSET + len(INJECTED_CODE)] = (
        INJECTED_CODE
    )
    result = bytes(patched)
    patched_hash = hashlib.sha256(result).hexdigest()
    if patched_hash != BATTLE_OVERLAY_DECODED_PATCHED_SHA256:
        raise BattleWeightPatchError(
            f"patched battle-overlay hash mismatch: {patched_hash}"
        )
    return result
