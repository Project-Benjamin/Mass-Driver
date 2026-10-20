"""Audit native weight code by executing bounded MIPS blocks from game media.

This does not patch the game, launch DuckStation or access a memory card.
Body weight and Gear accessory load are different systems. CPU-block evidence
does not establish an original body-weight damage formula or a game playthrough.
"""
from __future__ import annotations

import hashlib
import struct

from modules.definitive.cpu_audit import Machine
from modules.definitive.item_spell_audit import archive_members, decode_member, record_rows
from shared.tools.xgfield import decompress_lzss

MENU_BASE = 0x801C5000
BATTLE_BASE = 0x8006FAF0
CHARACTER_BASE = 0x8006D8A0
GEAR_BASE = 0x8006DFAC
RECORD_SIZE = 0xA4

# These spans were independently read from the pinned USA retail media.
SPANS = (
    (2599, 0x1E484, 0x1E510, "body_item", "49cdc88184b86320a49cae940681c02ec349f1471a0f56b3065fc2517b0913ee"),
    (2599, 0x128EC, 0x1293C, "body_display", "a95a1a2a46c7c53727c300cf16425bd1613dd1fbdcbf2b0ef65ff84bffa7ec07"),
    (2599, 0x1FA28, 0x1FAB4, "body_save_copy", "b9737f6d1427ecf5ef67d0a3b37e850de1b17943a2308cb6354f692d3d75f080"),
    (2599, 0x1FD10, 0x1FDBC, "body_load_copy", "49f282c1ca1ba1207325c5f402718c43e36ddd26abe7751c07aab43e03b6acf5"),
    (2602, 0x1190C, 0x1197C, "gear_penalty", "3b9d16dbf519831e62b986577f59e4b0b0474e62c9e98cc7d5192745cda4c719"),
    (38, 0x287C0, 0x287E4, "gear_battle_agility", "2f665c6b0e89854f12e79028e5787b830c7ee571d9d0cc22a17a44e54b856ba3"),
    (38, 0x29008, 0x2917C, "battle_atb", "5ebb37bc38bf501c619fb46173513b551b7527b3bf42b4e72803247dba76257d"),
    (36, 0x1AB84, 0x1ABC0, "field_weight_set", "835e0ca96bf098c0eb82c351c1085d6d100997ca1137c212aedf8951a9bcbc3f"),
)


class WeightAuditError(ValueError):
    pass


def decoded_resource(reader, canonical):
    source = reader(canonical)
    if canonical in (36, 38, 39):
        decoded = decompress_lzss(source + bytes(16), int.from_bytes(source[:4], "little")).data
        if canonical == 39:
            # Recompression may declare up to seven zero allocation bytes.
            if not 153864 <= len(decoded) <= 153871 or any(decoded[153864:]):
                raise WeightAuditError("Menu 39 has unexpected decoded allocation padding")
            return decoded[:153864]
        return decoded
    return source


def check_spans(resources):
    result = []
    for canonical, start, end, name, expected in SPANS:
        actual = hashlib.sha256(resources[canonical][start:end]).hexdigest()
        fixed_item = name == "body_item" and actual == "5ef0e1fed275b51ca693a7ebe689c398cfc3ee35f2727fc7049651b144853c2b"
        if actual != expected and not fixed_item:
            raise WeightAuditError(f"Native {name} code changed in resource {canonical}")
        result.append({"routine": name, "canonical_id": canonical,
                       "start": hex(start), "end_exclusive": hex(end), "sha256": actual,
                       "variant": "gain_cap_corrected" if fixed_item else "retail"})
    return result


def body_item_cases(menu, item_rows):
    machine = Machine(menu, MENU_BASE)
    record_address, item_address = 0x80100000, 0x80101000
    results = []
    for item_id, amount in ((72, -2), (73, -4), (74, 2), (75, 4)):
        row = item_rows[item_id]
        expected_effect = abs(amount) | (0x8000 if amount > 0 else 0)
        if struct.unpack_from("<HH", row, 0xA) != (2, expected_effect):
            raise WeightAuditError(f"Weight item {item_id} changed its native effect")
        failures = []
        for mutable in range(201):
            record = bytearray([0x55] * RECORD_SIZE)
            record[0x77:0x7A] = bytes((26, mutable, mutable % 10))
            machine.write(record_address, record)
            machine.write(item_address, row)
            machine.reg("a0", record_address)
            machine.reg("s0", item_address)
            machine.run(MENU_BASE + 0x1E484, MENU_BASE + 0x1E510)
            record[0x78] = min(200, max(0, mutable + amount))
            if machine.read(record_address, RECORD_SIZE) != record:
                failures.append(mutable)
        results.append({"item_id": item_id, "native_whole_change": amount,
                        "pound_change": amount * 2.2, "cases": 201,
                        "mutable_range": [0, 200], "failed_inputs": failures})
    return results


def body_display_cases(menu, initial_state):
    machine = Machine(menu, MENU_BASE)
    failures, count = [], 0
    # Execute the actual unit conversion, including native 16-bit truncation.
    for character in range(11):
        fixed = initial_state[0x26C + character * RECORD_SIZE + 0x77]
        for mutable in (0, 1, 50, 199, 200):
            for tenths in range(10):
                machine.write(CHARACTER_BASE + 0x77 + character * RECORD_SIZE,
                              bytes((fixed, mutable, tenths)))
                machine.reg("v1", character * RECORD_SIZE)
                machine.run(MENU_BASE + 0x128EC, MENU_BASE + 0x1293C)
                expected = 22 * (10 * (fixed + mutable) + tenths)
                count += 1
                if machine.reg("v1") != expected:
                    failures.append([character, mutable, tenths])
    return {"cases": count, "failed_inputs": failures,
            "formula": "hundredths_lb = 22 * (10 * (fixed + mutable) + tenths)"}


def body_gain_above_cap_cases(menu, item_rows):
    """Reproduce the mismatch between field food and inventory-item caps."""
    machine = Machine(menu, MENU_BASE)
    rows = []
    for mutable in (201, 229, 251, 252, 255):
        for item_id in (74, 75):
            machine.write(0x80100077, bytes((26, mutable, 0)))
            machine.write(0x80101000, item_rows[item_id])
            machine.reg("a0", 0x80100000)
            machine.reg("s0", 0x80101000)
            machine.run(MENU_BASE + 0x1E484, MENU_BASE + 0x1E510)
            actual = machine.read(0x80100078, 1)[0]
            rows.append({"item_id": item_id, "mutable_before": mutable,
                         "mutable_after": actual, "gain_item_reduced_weight": actual < mutable,
                         "field_total_at_fixed26": mutable + 26,
                         "within_observed_food_total_cap255": mutable + 26 <= 255})
    remaining = any(row["gain_item_reduced_weight"] for row in rows)
    return {"rows": rows, "remaining_bug": remaining,
            "finding": ("Gain items lower weight after field food raises mutable weight above 200" if remaining
                        else "Gain items preserve weight already at/above the native inventory cap")}


def body_save_copy_case(menu):
    machine = Machine(menu, MENU_BASE)
    # Distinct bytes for every character make wrong stride/partial copies fail.
    records = bytes((i * 73 + i // RECORD_SIZE) & 255 for i in range(11 * RECORD_SIZE))
    buffer = 0x80100000
    machine.write(CHARACTER_BASE, records)
    machine.reg("a0", buffer)
    machine.reg("sp", 0x801A0000)
    machine.run(MENU_BASE + 0x1FA28, MENU_BASE + 0x1FAB4, max_instructions=4000)
    saved = machine.read(buffer + 0x290, len(records))
    machine.write(CHARACTER_BASE, bytes(len(records)))
    machine.reg("a0", buffer)
    machine.reg("a1", 0)
    machine.reg("sp", 0x801A0000)
    machine.run(MENU_BASE + 0x1FD10, MENU_BASE + 0x1FDBC, max_instructions=4000)
    restored = machine.read(CHARACTER_BASE, len(records))
    return {"characters": 11, "record_size": RECORD_SIZE,
            "save_buffer_record_offset": "0x290", "bytes_roundtripped": len(records),
            "passed": saved == records == restored,
            "limit": "Native RAM-to-save-buffer and inverse copy only; no memory-card I/O"}


def gear_penalty_cases(shop, accessory_rows, initial_state):
    machine = Machine(shop, MENU_BASE)
    max_accessory = max(struct.unpack_from("<H", row, 6)[0] for row in accessory_rows)
    # Check both sides of every division threshold within the full retail range.
    maximum_sum = max_accessory * 3
    capacities = sorted({initial_state[0x978 + i * RECORD_SIZE + 0x75] for i in range(20)})
    sums = sorted({value for boundary in range(0, maximum_sum + 121, 120)
                   for value in (boundary - 1, boundary, boundary + 1)
                   if 0 <= value <= maximum_sum})
    failures, count = [], 0
    for capacity in capacities:
        for equipment in sums:
            machine.write(GEAR_BASE + 0x44, struct.pack("<H", equipment))
            machine.write(GEAR_BASE + 0x75, bytes([capacity]))
            machine.reg("a0", 0)
            machine.reg("ra", 0x80001000)
            machine.run(MENU_BASE + 0x1190C, 0x80001000)
            expected = max(0, (equipment // 120 - capacity) // 2)
            count += 1
            if machine.reg("v0") != expected:
                failures.append([capacity, equipment])
    return {"cases": count, "failed_inputs": failures, "capacity_bytes": capacities,
            "equipment_weight_inputs": sums,
            "max_accessory_weight": max_accessory, "max_three_slot_weight": maximum_sum,
            "formula": "max(0, trunc((floor(accessory_weight / 120) - gear[0x75]) / 2))"}


def gear_battle_cases(battle):
    machine = Machine(battle, BATTLE_BASE)
    gear = 0x80100000
    machine.write(0x800D2D6C, struct.pack("<I", gear))
    rows = []
    for agility in (8, 10, 12, 16):
        for bonus in (0, 1, 2):
            for penalty in range(8):
                original = bytearray(RECORD_SIZE)
                original[0x98], original[0x4E], original[0x4A] = agility, bonus, penalty
                machine.write(gear, original)
                machine.run(BATTLE_BASE + 0x287C0, BATTLE_BASE + 0x287E4)
                original[0x98] = agility + bonus - penalty
                rows.append(machine.read(gear, RECORD_SIZE) == original)
    return {"cases": len(rows), "failures": rows.count(False),
            "behavior": "Native battle preparation subtracts stored accessory penalty from Gear agility"}


def atb_cases(battle):
    machine = Machine(battle, BATTLE_BASE)
    entity = 0x80100000
    machine.write(0x800C34B0, struct.pack("<I", entity))
    machine.reg("sp", 0x801A0000)
    rows = []
    # Stop at the random-number call. This isolates the deterministic readiness
    # input; the random-number generator, jitter and status helper stay untested.
    for gear_mode in (False, True):
        for agility in (4, 8, 10, 12, 16):
            values = []
            for body in ((26, 0, 0), (26, 50, 0), (26, 200, 9)):
                machine.write(entity, bytes(0x160))
                machine.write(entity + 0x77, bytes(body))
                machine.write(entity + 0x5A, bytes([agility]))
                machine.write(entity + 0x13C, bytes([agility]))
                machine.write(entity + 0x15A, bytes([0x80 if gear_mode else 0]))
                machine.reg("a0", 0)
                machine.run(BATTLE_BASE + 0x29008, BATTLE_BASE + 0x29134)
                values.append(machine.reg("s0"))
            rows.append({"gear_mode": gear_mode, "agility": agility,
                         "readiness_input_for_three_body_weights": values,
                         "passed": values == [agility * 9] * 3})
    return {"cases": len(rows) * 3, "rows": rows,
            "body_weight_changes_readiness": False,
            "limit": "Native deterministic pre-RNG block; not hardware timing"}


def field_weight_boundary_cases(field):
    machine = Machine(field, BATTLE_BASE)
    state = 0x80100000
    machine.write(0x8005A39C, struct.pack("<I", state))
    rows = []
    for whole in (0, 25, 26, 76, 226, 281, 282):
        machine.write(state + 0x2E3, bytes((26, 50, 7)))
        machine.reg("s0", 0)
        machine.reg("v0", whole)
        machine.run(BATTLE_BASE + 0x1AB84, BATTLE_BASE + 0x1ABC0)
        value = machine.read(state + 0x2E4, 1)[0]
        rows.append({"requested_whole_weight": whole, "mutable_result": value,
                     "native_expected": max(0, whole - 26) & 255})
    return {"rows": rows,
            "finding": "Field setter floors at the fixed part but has no upper clamp; byte overflow remains possible",
            "scope": "Injected boundary operands; no claim that a particular retail meal reaches overflow"}


def audit_weight(reader):
    resources = {n: decoded_resource(reader, n) for n in (36, 38, 39, 2599, 2602)}
    spans = check_spans(resources)
    menu = resources[2599]
    variants = {str(n): decoded_resource(reader, n) == menu for n in (39, 2597, 2603)}
    members = archive_members(reader(2594), expected_count=56)
    item_rows = record_rows(decode_member(members[0]), stride=16, count=150)
    accessory_rows = record_rows(decode_member(members[19]), stride=28, count=150)
    state = reader(2595)
    result = {"format": "xenogears-native-weight-audit-v1", "spans": spans,
              "menu_variants_identical": variants,
              "body_items": body_item_cases(menu, item_rows),
              "body_display": body_display_cases(menu, state),
              "body_gain_cap_regression": body_gain_above_cap_cases(menu, item_rows),
              "body_save_buffer": body_save_copy_case(menu),
              "gear_penalty": gear_penalty_cases(resources[2602], accessory_rows, state),
              "gear_battle": gear_battle_cases(resources[38]),
              "atb": atb_cases(resources[38]),
              "field_boundaries": field_weight_boundary_cases(resources[36]),
              "gameplay_status": "untested",
              "whole_weight_system_certified": False,
              "body_weight_combat_fix_installed": False,
              "coverage": "Native consumable, display, save-buffer, equipment-penalty and battle-consumer blocks"}
    result["tested_blocks_passed"] = (
        all(variants.values()) and all(not row["failed_inputs"] for row in result["body_items"])
        and not result["body_display"]["failed_inputs"] and result["body_save_buffer"]["passed"]
        and not result["gear_penalty"]["failed_inputs"] and not result["gear_battle"]["failures"]
        and all(row["passed"] for row in result["atb"]["rows"]))
    return result
