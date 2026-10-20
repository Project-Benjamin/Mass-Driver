"""Correct two proven non-battle food descriptions without changing their effects."""
from __future__ import annotations

import struct

from shared.tools.xgdialog import PLAIN_ENCODE
from shared.tools.xgfield import compress_lzss_retail
from modules.definitive.item_spell_audit import (
    AuditError, archive_members, decode_member, indexed_strings, sha256,
)

SYSTEM_DATA_SHA256 = "c3bd13cfc3579339a072377dbca30319535aa9ef2aa5f93d464c5ae12c13f4fa"
CORRECTIONS = {58: ("150", "100"), 59: ("500", "150")}


def build_description_replacements(read):
    source = read(2594)
    if len(source) != 40336 or sha256(source) != SYSTEM_DATA_SHA256:
        raise AuditError("Food description fixes require exact clean USA system data 2594")
    # These code guards establish that the text describes the audited native
    # menu effect and that food IDs cannot appear in the ordinary battle list.
    menu = read(2599)
    loader = read(2615)
    if sha256(menu[0x1E1C0:0x1E2F0]) != "cb385173545f0c399e7cc7b28265d14955b56b4019f9e35c9c235e40d78640f2":
        raise AuditError("HP recovery instructions changed")
    if sha256(loader[0xCD0:0xDD4]) != "a99d7d760d7b4d5d2f4b75bf4f9865790e9afbb31eaf4e90c967e8946da64eda":
        raise AuditError("Battle item availability instructions changed")
    members = list(archive_members(source, 56))
    changes = []
    for member in (14, 41):
        original = decode_member(members[member])
        strings = indexed_strings(original)
        result = bytearray(original)
        allowed = set()
        for item, (before_number, after_number) in CORRECTIONS.items():
            before = f"Restores HP ({before_number}) Non-battle"
            after = f"Restores HP ({after_number}) Non-battle"
            if strings[item]["text"] != before:
                raise AuditError(f"Food description {member}:{item} changed")
            offset = strings[item]["decoded_offset"]
            expected = bytes(PLAIN_ENCODE[c] for c in before) + b"\0"
            replacement = bytes(PLAIN_ENCODE[c] for c in after) + b"\0"
            if original[offset:offset + len(expected)] != expected:
                raise AuditError("Food description encoded content changed")
            if len(expected) != len(replacement):
                raise AuditError("Food fix must retain exact string allocation")
            result[offset:offset + len(replacement)] = replacement
            allowed.update(range(offset, offset + len(replacement)))
            changes.append({"member": member, "item_id": item, "before": before,
                            "after": after, "decoded_offset": offset})
        if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(original, result))):
            raise AuditError("Unrelated description bytes changed")
        packed = compress_lzss_retail(bytes(result))
        decoded = decode_member(packed)
        if decoded[:len(result)] != result or not 0 <= len(decoded) - len(result) <= 7 or any(decoded[len(result):]):
            raise AuditError("Food descriptions failed native compression round trip")
        members[member] = packed
    # Keep the original count, header cushion, and every unselected compressed
    # member exactly; only archive start offsets follow new compressed sizes.
    first_offset = struct.unpack_from("<I", source, 4)[0]
    rebuilt = bytearray(source[:first_offset])
    offsets = []
    for member in members:
        offsets.append(len(rebuilt))
        rebuilt.extend(member)
        rebuilt.extend(bytes((-len(rebuilt)) % 4))
    struct.pack_into("<56I", rebuilt, 4, *offsets)
    verified = archive_members(bytes(rebuilt), 56)
    originals = archive_members(source, 56)
    for member in range(56):
        if member not in (14, 41) and verified[member] != originals[member]:
            raise AuditError(f"Unselected system member {member} changed")
    return {2594: bytes(rebuilt)}, {
        "id": "food_hp_descriptions", "source_sha256": sha256(source),
        "patched_sha256": sha256(bytes(rebuilt)), "changes": changes,
        "behavior": "Hob-Meat says 100 HP; Hob-Steak says 150 HP, matching unchanged menu recovery.",
        "battle_context": "Native battle loader only admits item IDs 1..48; food IDs 58/59 are excluded.",
        "effects_changed": False, "runtime_status": "untested",
    }
