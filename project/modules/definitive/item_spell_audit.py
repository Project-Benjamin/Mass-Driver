"""Read native USA item/ability tables without pretending raw flags are proven effects.

All offsets are zero-based archive indices and decoded member offsets. This is
an inventory/consistency audit; it does not simulate the whole battle engine.
"""
from __future__ import annotations

import argparse
from collections.abc import Callable
import hashlib
import json
from pathlib import Path
import re
import struct

from shared.tools.xgdialog import decode_text
from shared.tools.xgfield import decompress_lzss


class AuditError(ValueError):
    """A native table cannot be read without guessing."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def archive_members(data: bytes, expected_count: int | None = None) -> tuple[bytes, ...]:
    if len(data) < 8:
        raise AuditError("Truncated native archive")
    count = int.from_bytes(data[:4], "little")
    if not 1 <= count <= 512 or 4 + count * 4 > len(data):
        raise AuditError("Invalid archive pointer count")
    if expected_count is not None and count != expected_count:
        raise AuditError(f"Archive has {count} members, expected {expected_count}")
    offsets = struct.unpack_from(f"<{count}I", data, 4)
    if offsets[0] < 4 + count * 4 or offsets[-1] >= len(data):
        raise AuditError("Archive pointer outside payload")
    if any(a >= b for a, b in zip(offsets, offsets[1:])):
        raise AuditError("Archive pointers must increase strictly")
    return tuple(data[a:b] for a, b in zip(offsets, (*offsets[1:], len(data))))


def decode_member(data: bytes) -> bytes:
    if len(data) < 4:
        raise AuditError("Truncated LZSS size")
    size = int.from_bytes(data[:4], "little")
    if not 0 <= size <= 2_000_000:
        raise AuditError("Unexpected LZSS member size")
    # Retail completes its final group into the decoder's allocation cushion.
    # The exact declared size is kept here; record_rows checks any row padding.
    return decompress_lzss(data + bytes(16), size).data


def record_rows(data: bytes, stride: int, count: int) -> tuple[bytes, ...]:
    if stride <= 0 or count <= 0 or not count * stride <= len(data) <= count * stride + 7:
        raise AuditError("Record table length does not match fixed native layout")
    return tuple(data[i * stride:(i + 1) * stride] for i in range(count))


def indexed_strings(data: bytes) -> list[dict]:
    if len(data) < 8:
        raise AuditError("Truncated string table")
    count = int.from_bytes(data[:4], "little") + 1
    end = 4 + count * 4
    if not 1 <= count <= 4096 or end >= len(data):
        raise AuditError("Invalid indexed string count")
    offsets = struct.unpack_from(f"<{count}H", data, 4)
    if offsets[0] != end or offsets[-1] >= len(data):
        raise AuditError("Invalid indexed string boundaries")
    if any(a >= b for a, b in zip(offsets, offsets[1:])):
        raise AuditError("Indexed string boundaries must increase strictly")
    rows = []
    for i, (a, b) in enumerate(zip(offsets, (*offsets[1:], len(data)))):
        payload = data[a:b]
        # Terminal padding is retained in raw_hex rather than called text.
        terminal = 0
        while terminal < len(payload) and payload[terminal] != 0:
            token = payload[terminal]
            terminal += 3 if token == 0x0F else 2 if token in (0xFE, 0xFF) else 1
        if terminal >= len(payload):
            raise AuditError(f"String {i} has no terminal Close")
        text = decode_text(payload[:terminal + 1]).removesuffix("<Close>").strip()
        rows.append({"id": i, "text": text, "raw_hex": payload.hex(),
                     "width": data[4 + count * 2 + i * 2],
                     "height": data[5 + count * 2 + i * 2],
                     "decoded_offset": a,
                     "has_untranslated_or_unknown_codes": "<" in text})
    return rows


def _text(table: list[dict], index: int) -> str | None:
    return table[index]["text"] if index < len(table) else None


def _row_info(row: bytes, index: int) -> dict:
    return {"id": index, "decoded_offset": index * len(row), "raw_hex": row.hex(),
            "semantics_status": "not_verified", "runtime_status": "untested"}


def inventory(read: Callable[[int], bytes]) -> dict:
    resources = {cid: read(cid) for cid in (29, 2594, 2614)}
    names = archive_members(decode_member(resources[29]), 53)
    menu = tuple(decode_member(x) for x in archive_members(resources[2594], 56))
    battle = tuple(decode_member(x) for x in archive_members(resources[2614], 38))
    text_tables = {}
    for cid, blocks, ids in [(29, names, (17, 20, 22, 23, 48, 50, 51, 52)),
                             (2594, menu, (14, 15, 20, 21, 39, 40, 41, 44, 45, 46,
                                            47, 48, 49, 50, 51, 52, 53, 54, 55)),
                             (2614, battle, (15,))]:
        for i in ids:
            text_tables[f"{cid}:{i}"] = indexed_strings(blocks[i])
    # Physical rows start at offset zero. The price field at +2 is not a header.
    specs = (
        ("items", 0, 16, 150, "29:22", "2594:14"),
        ("weapons", 1, 16, 100, "29:23", "2594:39"),
        ("accessories", 2, 16, 200, "29:17", "2594:40"),
        ("gear_frames", 16, 24, 180, "2594:45", "2594:48"),
        ("gear_armor", 17, 20, 150, "2594:44", "2594:47"),
        ("gear_engines", 18, 16, 150, "2594:46", "2594:49"),
        ("gear_accessories", 19, 28, 150, "29:50", "2594:51"),
        ("gear_weapons", 42, 20, 100, "29:51", "2594:50"),
    )
    tables = {}
    for label, member, stride, count, nt, dt in specs:
        rows = []
        for i, row in enumerate(record_rows(menu[member], stride, count)):
            out = _row_info(row, i)
            out.update({"name": _text(text_tables[nt], i),
                        "description": _text(text_tables[dt], i)})
            if label == "items":
                out.update({"price": int.from_bytes(row[2:4], "little"),
                            "availability_flags_raw": row[6], "potency_raw": row[8],
                            "effect_flags_raw": int.from_bytes(row[10:12], "little"),
                            "effect_argument_raw": int.from_bytes(row[12:14], "little"),
                            "shop_description": _text(text_tables["2594:41"], i),
                            "battle_description": _text(text_tables["2614:15"], i)})
            elif label == "accessories":
                out.update({"price": int.from_bytes(row[2:4], "little"),
                            "equip_flags_raw": int.from_bytes(row[:2], "little"),
                            "status_group_raw": row[9],
                            "status_bits_raw": int.from_bytes(row[10:12], "little"),
                            "stat_flags_raw": int.from_bytes(row[12:14], "little")})
            elif label == "gear_accessories":
                out.update({"equipment_weight": int.from_bytes(row[6:8], "little"),
                            "defense_raw": int.from_bytes(row[8:10], "little"),
                            "ether_defense_raw": int.from_bytes(row[10:12], "little")})
            rows.append(out)
        tables[label] = {"canonical": 2594, "member": member, "stride": stride,
                         "rows": rows, "name_table": nt, "description_table": dt,
                         "declared_decoded_length": len(menu[member]),
                         "allocation_tail_hex": menu[member][count * stride:].hex()}
    character_rows = []
    copies = []
    for char in range(11):
        battle_rows = record_rows(battle[4 + char], 40, 38)
        menu_rows = record_rows(menu[3 + char], 40, 38)
        copies.append({"kind": "character_actions", "actor": char,
                       "menu_member": 3 + char, "battle_member": 4 + char,
                       "identical_meaningful_rows": menu_rows == battle_rows})
        for slot in range(16):
            row = battle_rows[22 + slot]
            i = char * 16 + slot
            out = _row_info(row, i)
            out.update({"character": char, "ability_slot": slot,
                        "battle_row": 22 + slot, "battle_member": 4 + char,
                        "menu_member": 3 + char, "decoded_offset": (22 + slot) * 40,
                        "name": _text(text_tables["29:20"], i),
                        "description_lines": [text_tables["2594:15"][i * 2 + j]["text"] for j in range(2)],
                        "base_ep_cost": row[0x13],
                        "target_flags_raw": int.from_bytes(row[:2], "little"),
                        "effect_flags_raw": int.from_bytes(row[10:12], "little")})
            character_rows.append(out)
    tables["character_abilities"] = {"rows": character_rows,
        "note": "11 actor records x 16 slots, including blanks and alternate forms. EP cost is the raw base before equipment/status changes."}
    gear_actions = []
    for gear in range(19):
        rows = record_rows(battle[16 + gear], 40, 41)
        if gear < 17:
            menu_rows = record_rows(menu[22 + gear], 40, 41)
            copies.append({"kind": "gear_actions", "actor": gear,
                           "menu_member": 22 + gear, "battle_member": 16 + gear,
                           "identical_meaningful_rows": menu_rows == rows,
                           "differences": [{"row": r, "byte": byte, "menu": a, "battle": b}
                               for r, (x, y) in enumerate(zip(menu_rows, rows))
                               for byte, (a, b) in enumerate(zip(x, y)) if a != b]})
        for slot, row in enumerate(rows):
            out = _row_info(row, slot)
            out.update({"gear": gear, "battle_member": 16 + gear,
                        "base_cost_raw": row[0x13],
                        "target_flags_raw": int.from_bytes(row[:2], "little"),
                        "effect_flags_raw": int.from_bytes(row[10:12], "little")})
            gear_actions.append(out)
    tables["gear_actions"] = {"rows": gear_actions,
        "note": "19 x 41 native action rows. Gear Ether/special names and descriptions are inventoried separately; their action joins remain unverified."}
    copies.append({"kind": "item_rows", "menu_member": 0, "battle_member": 2,
                   "identical_meaningful_rows": record_rows(menu[0], 16, 150) == record_rows(battle[2], 16, 150)})
    findings = []
    for row in tables["items"]["rows"]:
        text = row["description"] or ""
        m = re.search(r"Restores HP \((\d+)\).*Non-battle", text)
        if m and row["effect_flags_raw"] & 0x8000:
            actual = row["potency_raw"] * 50
            if int(m[1]) != actual:
                findings.append({"id": f"food_hp_{row['id']}", "kind": "description_mismatch",
                    "name": row["name"], "item_id": row["id"],
                    "claimed_hp": int(m[1]), "native_menu_hp_before_cap": actual,
                    "evidence": "Menu 2599 +0x1E234 loads 50, +0x1E240 reads row+8, +0x1E248 multiplies; +0x1E2A8..0x1E2C8 caps to max HP.",
                    "runtime_status": "untested"})
    return {"format": "xenogears-item-spell-audit-v1",
            "resources": {str(k): {"size": len(v), "sha256": sha256(v)} for k, v in resources.items()},
            "tables": tables, "text_tables": text_tables, "duplicate_tables": copies,
            "findings": findings,
            "coverage": {"native_item_equipment_rows": sum(spec[3] for spec in specs),
                         "character_ability_slots": len(character_rows),
                         "gear_action_rows": len(gear_actions),
                         "whole_game_semantics_verified": False,
                         "text_inventory_is_not_behavior_verification": True}}


def audit_pair(retail_path: Path, build_path: Path, disc: int) -> dict:
    from modules.definitive.build import RetailDisc, digest
    retail = RetailDisc(retail_path, disc)
    built = RetailDisc(build_path, disc)
    retail_inventory = inventory(retail.read)
    result = inventory(built.read)
    result["identity"] = {"disc": disc, "retail_path": str(retail_path.resolve()),
                          "build_path": str(build_path.resolve()),
                          "retail_disc_sha256": digest(retail_path),
                          "build_disc_sha256": digest(build_path)}
    result["retail_comparison"] = {str(cid): {"identical_bytes": retail.read(cid) == built.read(cid)}
                                    for cid in (29, 2594, 2614)}
    result["retail_findings"] = retail_inventory["findings"]
    result["native_food_validation"] = native_food_validation(built.read)
    return result


def native_food_validation(read: Callable[[int], bytes]) -> dict:
    """Execute native HP recovery and battle-inventory exclusion in isolated RAM."""
    from modules.definitive.cpu_audit import Machine
    menu_code, loader = read(2599), read(2615)
    if sha256(menu_code[0x1E1C0:0x1E2F0]) != "cb385173545f0c399e7cc7b28265d14955b56b4019f9e35c9c235e40d78640f2":
        raise AuditError("Native HP recovery block changed; re-audit its behavior")
    if sha256(loader[0xCD0:0xDD4]) != "a99d7d760d7b4d5d2f4b75bf4f9865790e9afbb31eaf4e90c967e8946da64eda":
        raise AuditError("Native battle inventory filter changed; re-audit availability")
    items = record_rows(decode_member(archive_members(read(2594), 56)[0]), 16, 150)
    machine = Machine(menu_code, 0x801C5000)
    machine.write(0x8010001C, struct.pack("<I", 0x80101000))
    machine.write(0x80101000, b"".join(items))
    hp_cases = []
    for item in (57, 58, 59):
        for maximum in (100, 499, 999):
            for current in (0, 1, maximum - 1, maximum):
                machine.reg("sp", 0x801FF000)
                machine.reg("a0", 0x80100000)
                machine.reg("a1", 0)
                machine.reg("a2", item)
                machine.write(0x8006D8A0, bytes(164))
                machine.write(0x8006D8EC, struct.pack("<HHHH", current, maximum, 0, 99))
                machine.run(0x801E31C0, 0x801E32F0)
                actual = struct.unpack("<H", machine.read(0x8006D8EC, 2))[0]
                expected = min(maximum, current + items[item][8] * 50)
                if actual != expected:
                    raise AuditError(f"Native menu HP case failed for item {item}")
                hp_cases.append({"item_id": item, "hp_before": current, "max_hp": maximum,
                                 "hp_after": actual, "expected": expected, "passed": True})
    machine = Machine(loader, 0x801E4000)
    battle_cases = []
    for item in range(150):
        # One item with a positive quantity; all other inventory slots empty.
        machine.write(0x8006F5C4, b"\x01" + bytes(149))
        machine.write(0x8006F65A, bytes([item]) + bytes(149))
        machine.run(0x801E4CD0, 0x801E4DD4, max_instructions=6000)
        selected = list(machine.read(0x800D2CE0, 48))
        expected = [item if 0 < item < 49 else 0] + [0] * 47
        if selected != expected:
            raise AuditError(f"Native battle item filter failed for item {item}")
        battle_cases.append({"item_id": item, "available": bool(selected[0]), "passed": True})
    return {"hp_recovery_cases": hp_cases, "battle_item_filter_cases": battle_cases,
            "menu_resource_sha256": sha256(menu_code), "loader_resource_sha256": sha256(loader),
            "evidence_level": "Executed native MIPS blocks in isolated RAM; no scene, save, menu rendering or full-battle playthrough"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retail", type=Path, required=True)
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--disc", type=int, choices=(1, 2), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit_pair(args.retail, args.build, args.disc)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"coverage": result["coverage"], "findings": result["findings"],
                      "retail_comparison": result["retail_comparison"]}, indent=2))


if __name__ == "__main__":
    main()
