"""Isolated, fail-closed fixes for the USA retail battle executable.

This module does not install the Perfect Works battle overlay.  Each correction
changes one existing MIPS instruction in the user's verified retail resource.
Binary verification is not an emulator playthrough; the receipt says so.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import hashlib

from shared.tools.xgfield import compress_lzss_retail, decompress_lzss


class MechanicsPatchError(ValueError):
    """A selected patch or its retail preimage is not supported."""


BATTLE_CANONICAL_ID = 38
BATTLE_PACKED_SIZE = 166_564
BATTLE_PACKED_SHA256 = "b9c3a15bf5f3eb06bcb3824ef62793b9a500fe1dcb3717fe8963e23e9f27628b"
BATTLE_DECODED_SIZE = 343_936
BATTLE_DECODED_SHA256 = "1830b4ef1fe37129972fc310dfad534f8161d6c0b123e74254c3711334a3e291"


@dataclass(frozen=True)
class BattleFix:
    id: str
    title: str
    offset: int
    before: bytes
    after: bytes
    source: str
    behavior: str


BATTLE_FIXES = (
    BattleFix(
        "gear_charge_multiplier",
        "Gear Charger multiplier",
        0x2A894,
        bytes.fromhex("00 00 A3 94"),  # lhu v1, 0(a1)
        bytes.fromhex("0A 00 03 34"),  # ori v1, zero, 10
        "https://github.com/PWBuild-Team/Perfect_Works_Build/commit/c81044cce6ee9a9876073a4d87d261124ba114fc",
        "Charger fuel recovery uses its encoded value times ten instead of "
        "reading the first halfword of the battle damage table as a multiplier. "
        "The no-Charger baseline and attack-level bonuses retain their retail code.",
    ),
    BattleFix(
        "defense_up_status",
        "Def Up status check",
        0x27C28,
        bytes.fromhex("00 01 42 30"),  # andi v0, v0, 0x0100
        bytes.fromhex("00 40 42 30"),  # andi v0, v0, 0x4000
        "https://github.com/PWBuild-Team/Perfect_Works_Build/commit/6a6dac9164bf12eadef34dcf6b73e5aeab22ba00",
        "The existing on-foot defense adjustment checks the Def Up flag "
        "0x4000 instead of 0x0100. Upstream reports this also increases blocking; "
        "runtime defense and blocking coverage is still required.",
    ),
)
BATTLE_FIX_IDS = tuple(fix.id for fix in BATTLE_FIXES)
GEAR_SHOP_FIX_ID = "gear_shop_ether_amp"
SUPPORTED_FIX_IDS = BATTLE_FIX_IDS + (GEAR_SHOP_FIX_ID,)
GEAR_SHOP_CANONICAL_ID = 2602
GEAR_SHOP_SIZE = 82_080
GEAR_SHOP_SHA256 = "5a08a22f2c5cc1d131b33a944d3167a2ac460c5f9f17f2dcf94dd8860158a25c"
GEAR_SHOP_PATCHED_SHA256 = "18ea2428cad59024e1facb509bdb0d29b9873fe68df79666d52df8a65fe8f7a2"
GEAR_SHOP_FIX = BattleFix(
    GEAR_SHOP_FIX_ID,
    "Gear shop preserves equipment Ether amp",
    0x11428,
    bytes.fromhex("54 00 00 A2"),  # sb zero, 0x54(s0)
    bytes(4),
    "https://github.com/PWBuild-Team/Perfect_Works_Build/commit/9355acf5cc507edc12bb72f3d63100c7edca5054",
    "Opening the Gear shop Parts menu no longer clears the equipment Ether "
    "amplifier byte in the persistent Gear record.",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _selected(fixes: Iterable[str]) -> tuple[BattleFix, ...]:
    requested = tuple(fixes)
    if len(requested) != len(set(requested)):
        raise MechanicsPatchError("duplicate mechanics fix selection")
    unknown = set(requested) - set(BATTLE_FIX_IDS)
    if unknown:
        raise MechanicsPatchError(f"unsupported mechanics fix: {sorted(unknown)}")
    return tuple(fix for fix in BATTLE_FIXES if fix.id in requested)


def patch_decoded_battle_overlay(
    decoded: bytes, fixes: Iterable[str] = BATTLE_FIX_IDS
) -> bytes:
    """Change selected retail instructions; reject modified/foreign overlays."""
    selected = _selected(fixes)
    digest = _sha256(decoded)
    if len(decoded) != BATTLE_DECODED_SIZE or digest != BATTLE_DECODED_SHA256:
        raise MechanicsPatchError(
            f"clean USA retail battle overlay required: {len(decoded)} bytes, {digest}"
        )
    for fix in selected:
        if decoded[fix.offset:fix.offset + len(fix.before)] != fix.before:
            raise MechanicsPatchError(f"{fix.id}: retail instruction changed")
    result = bytearray(decoded)
    for fix in selected:
        result[fix.offset:fix.offset + len(fix.after)] = fix.after
    return bytes(result)


def patch_battle_resource(
    source: bytes, fixes: Iterable[str] = BATTLE_FIX_IDS
) -> tuple[bytes, dict]:
    """Return canonical resource 38 and an honest, serializable audit receipt."""
    selected = _selected(fixes)
    digest = _sha256(source)
    if len(source) != BATTLE_PACKED_SIZE or digest != BATTLE_PACKED_SHA256:
        raise MechanicsPatchError(
            f"clean USA retail resource 38 required: {len(source)} bytes, {digest}"
        )
    decoded = decompress_lzss(source, BATTLE_DECODED_SIZE).data
    patched = patch_decoded_battle_overlay(decoded, (fix.id for fix in selected))
    packed = compress_lzss_retail(patched) if selected else source
    declared = int.from_bytes(packed[:4], "little")
    roundtrip = decompress_lzss(packed, declared)
    padding = declared - len(patched)
    if not 0 <= padding <= 7 or roundtrip.data != patched + bytes(padding):
        raise MechanicsPatchError("battle resource failed retail LZSS round-trip")
    receipt = {
        "canonical_id": BATTLE_CANONICAL_ID,
        "source_sha256": digest,
        "source_decoded_sha256": _sha256(decoded),
        "patched_sha256": _sha256(packed),
        "patched_decoded_sha256": _sha256(patched),
        "decoded_bytes": len(patched),
        "allocation_padding_bytes": padding,
        "binary_validation": "exact retail preimage; isolated instruction changes; LZSS round-trip passed",
        "runtime_validation": "not tested in emulator",
        "fixes": [
            {
                "id": fix.id,
                "title": fix.title,
                "offset": f"0x{fix.offset:05X}",
                "before": fix.before.hex(),
                "after": fix.after.hex(),
                "source": fix.source,
                "behavior": fix.behavior,
            }
            for fix in selected
        ],
        "body_weight": "unchanged; original intended combat formula not established",
        "coverage": "two isolated battle fixes; not an all-bugs certification",
    }
    return packed, receipt


def patch_gear_shop_resource(source: bytes) -> tuple[bytes, dict]:
    """Remove the one proven Ether-amplifier clearing store from retail 2602."""
    digest = _sha256(source)
    if len(source) != GEAR_SHOP_SIZE or digest != GEAR_SHOP_SHA256:
        raise MechanicsPatchError(
            f"clean USA retail resource 2602 required: {len(source)} bytes, {digest}"
        )
    fix = GEAR_SHOP_FIX
    if source[fix.offset:fix.offset + 4] != fix.before:
        raise MechanicsPatchError("Gear shop clearing store context changed")
    patched = bytearray(source)
    patched[fix.offset:fix.offset + 4] = fix.after
    result = bytes(patched)
    if _sha256(result) != GEAR_SHOP_PATCHED_SHA256:
        raise MechanicsPatchError("Gear shop patched identity mismatch")
    return result, {
        "canonical_id": GEAR_SHOP_CANONICAL_ID,
        "source_sha256": digest,
        "patched_sha256": _sha256(result),
        "binary_validation": "exact retail preimage; one isolated store replaced by NOP",
        "runtime_validation": "not tested in emulator",
        "fixes": [{
            "id": fix.id, "title": fix.title, "offset": f"0x{fix.offset:05X}",
            "before": fix.before.hex(), "after": fix.after.hex(),
            "source": fix.source, "behavior": fix.behavior,
        }],
    }


def build_mechanics_replacements(
    read_canonical: Callable[[int], bytes], fixes: Iterable[str] = SUPPORTED_FIX_IDS
) -> tuple[dict[int, bytes], dict]:
    """Build canonical replacements from the builder's tracked retail reader."""
    selected = tuple(fixes)
    if len(selected) != len(set(selected)):
        raise MechanicsPatchError("duplicate mechanics fix selection")
    unknown = set(selected) - set(SUPPORTED_FIX_IDS)
    if unknown:
        raise MechanicsPatchError(f"unsupported mechanics fix: {sorted(unknown)}")
    if not selected:
        return {}, {"fixes": [], "runtime_validation": "not tested in emulator"}
    replacements = {}
    receipts = []
    battle_fixes = tuple(fix for fix in selected if fix in BATTLE_FIX_IDS)
    if battle_fixes:
        packed, receipt = patch_battle_resource(read_canonical(BATTLE_CANONICAL_ID), battle_fixes)
        replacements[BATTLE_CANONICAL_ID] = packed
        receipts.append(receipt)
    if GEAR_SHOP_FIX_ID in selected:
        packed, receipt = patch_gear_shop_resource(read_canonical(GEAR_SHOP_CANONICAL_ID))
        replacements[GEAR_SHOP_CANONICAL_ID] = packed
        receipts.append(receipt)
    return replacements, {
        "fixes": [fix for receipt in receipts for fix in receipt["fixes"]],
        "resources": receipts,
        "runtime_validation": "not tested in emulator",
        "body_weight": "unchanged; original intended combat formula not established",
        "coverage": "three isolated fixes; not an all-bugs certification",
    }
