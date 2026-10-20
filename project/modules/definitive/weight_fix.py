"""Prevent Bulimy gain items from reducing food-raised body weight.

Only the native inventory gain path changes. The existing 200 mutable-unit
cap remains for characters below it; characters already at/above it stay at
their current weight. Field food, weight loss, display, saves and combat keep
their native code. All four identical menu overlay copies must be patched.
"""
from __future__ import annotations

import hashlib
import struct

from shared.tools.xgfield import compress_lzss_retail, decompress_lzss

MENU_IDS = (39, 2597, 2599, 2603)
MENU_SIZE = 153864
MENU_SHA256 = "82f84a24ac1fd1979754e1cc9c861405fb59ce95dd78db00a76f00c8f1bd177d"
PACKED_MENU_SHA256 = "f3b8d9516c519ee7b1580716c653c54804f205f43eaef3567355700e45d13261"
GAIN_START, GAIN_END = 0x1E4B0, 0x1E4E0
GAIN_BEFORE = bytes.fromhex(
    "78008290 0c000392 00000000 21104300 780082a0 78008290 "
    "00000000 c900422c 0f004014 c8000234 448d0708 780082a0"
)
# lbu v0,78(a0); lbu v1,C(s0); sltiu at,v0,200;
# beq at,zero,end; nop; addu v0,v0,v1; sltiu at,v0,201;
# bne at,zero,jump; nop; ori v0,zero,200; j end; sb v0,78(a0).
# The two LBU results are used only after their R3000A load-delay slots.
# Branches and the final jump retain explicit, safe delay slots.
GAIN_AFTER = struct.pack("<12I",
    0x90820078, 0x9203000C, 0x2C4100C8, 0x10200014,
    0, 0x00431021, 0x2C4100C9, 0x14200002,
    0, 0x340200C8, 0x08078D44, 0xA0820078)


class WeightFixError(ValueError):
    pass


def patch_menu(source: bytes) -> bytes:
    if len(source) != MENU_SIZE or hashlib.sha256(source).hexdigest() != MENU_SHA256:
        raise WeightFixError("Clean USA retail menu overlay required for the weight-gain fix")
    if source[GAIN_START:GAIN_END] != GAIN_BEFORE:
        raise WeightFixError("Native body-weight gain instructions changed")
    return source[:GAIN_START] + GAIN_AFTER + source[GAIN_END:]


def build_weight_replacements(read_canonical):
    replacements, rows = {}, []
    for canonical in MENU_IDS:
        original = read_canonical(canonical)
        if canonical == 39:
            if hashlib.sha256(original).hexdigest() != PACKED_MENU_SHA256:
                raise WeightFixError("Clean USA retail packed menu 39 required")
            decoded = decompress_lzss(original, MENU_SIZE).data
        else:
            decoded = original
        patched = patch_menu(decoded)
        output = compress_lzss_retail(patched) if canonical == 39 else patched
        if canonical == 39:
            declared = int.from_bytes(output[:4], "little")
            if (not 0 <= declared - MENU_SIZE <= 7
                    or decompress_lzss(output, declared).data != patched + bytes(declared - MENU_SIZE)):
                raise WeightFixError("Weight menu failed LZSS round-trip")
        replacements[canonical] = output
        rows.append({"canonical_id": canonical,
                     "source_sha256": hashlib.sha256(original).hexdigest(),
                     "output_sha256": hashlib.sha256(output).hexdigest(),
                     "decoded_output_sha256": hashlib.sha256(patched).hexdigest()})
    return replacements, {
        "id": "body_weight_gain_monotonic",
        "title": "Bulimy weight-gain cap correction",
        "behavior": "Gain items preserve already-at/above-cap weight and cannot wrap a byte",
        "native_mutable_cap": 200,
        "changed_decoded_span": [hex(GAIN_START), hex(GAIN_END)],
        "before": GAIN_BEFORE.hex(), "after": GAIN_AFTER.hex(),
        "resources": rows,
        "unchanged": ["field food", "weight loss", "fixed and fractional weight bytes",
                      "body display", "save format", "Gear weight", "combat formulas"],
        "gameplay_status": "untested",
        "evidence": "Native CPU regression: original gain items reduce mutable229 to200; corrected preserves229",
    }
