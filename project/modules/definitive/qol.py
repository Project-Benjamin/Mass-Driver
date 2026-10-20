"""Optional reward changes to existing enemy records, without balance edits.

The fixed eight 0x170-byte records start at 0x32. The four-byte XP reward
is at record+0x14C. This agrees with the retail data and PW's monsterEditor
source; do not copy that editor's variable-length loop or wchar_t reads.
"""
import struct

ENEMY_FILES = tuple(range(2618, 2769, 2))
RECORD_START = 0x32
RECORD_SIZE = 0x170
RECORD_COUNT = 8
XP_OFFSET = 0x14C
RECORD_END = RECORD_START + RECORD_SIZE * RECORD_COUNT


def double_enemy_xp(source: bytes) -> tuple[bytes, list[dict]]:
    if len(source) < RECORD_END:
        raise ValueError("Enemy file is shorter than its eight stat records")
    # The first script pointer marks the end of the stat table in retail.
    if struct.unpack_from("<H", source)[0] != RECORD_END:
        raise ValueError("Enemy script/stat table boundary differs from retail")
    result = bytearray(source)
    changes = []
    for slot in range(RECORD_COUNT):
        offset = RECORD_START + slot * RECORD_SIZE + XP_OFFSET
        before = struct.unpack_from("<I", source, offset)[0]
        if before > 0x3FFFFFFF:
            raise ValueError(f"Doubling enemy {slot} XP would overflow signed reward arithmetic")
        after = before * 2
        struct.pack_into("<I", result, offset, after)
        if before != after:
            changes.append({"slot": slot, "offset": offset, "before": before, "after": after})
    return bytes(result), changes


def patch_rewards(read_resource, replacements=None):
    result = dict(replacements or {})
    audit = []
    for canonical in ENEMY_FILES:
        source = result[canonical] if canonical in result else read_resource(canonical)
        patched, changes = double_enemy_xp(source)
        if changes:
            result[canonical] = patched
        audit.append({"canonical_id": canonical, "changes": changes})
    return result, {"files_examined": len(audit), "files": audit,
                    "scope": "Enemy XP rewards, including bosses; no gold or deathblow-learning edits",
                    "runtime_status": "untested"}
