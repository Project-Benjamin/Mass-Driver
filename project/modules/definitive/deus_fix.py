"""Isolated Mahanon Deus HP-halving camera guard for verified USA retail.

This changes the affected camera command, not damage, enemy stats, or fights.
The transient flag occupies the unused alignment word following the final
battle-overlay function. No saved state, field allocation or chapter is used.
"""
from __future__ import annotations

from collections.abc import Callable
import hashlib
import struct

from modules.definitive import mechanics
from modules.definitive.qol import ENEMY_FILES
from shared.tools.xgfield import compress_lzss_retail, decompress_lzss

SOURCE = "https://github.com/PWBuild-Team/Perfect_Works_Build/commit/c054f82f8e8dab8c6ad5106ed270d301d586aa54"
ENEMY_ID = 2746
ENEMY_SHA256 = "338b41b89491c4d53185e89b4efbacf974848f6561151573bd8406f5410d300a"
PATCHED_ENEMY_SHA256 = "86c439808a674c7a3a507fa675ee9ea8fb92631ec18ed3b0ea8513798d17ddc7"
PATCHED_BATTLE_SHA256 = "e315f4397bc784775ce942939012d3398e4bdd9395690a371c0c1e1092b1b8a6"
SCRATCH_ADDRESS = 0x800C2048
SCRATCH_OFFSET = 0x52558

# Complete instruction blocks, isolated against the source commit and retail.
BLOCKS = (
    (0xAD64,
     bytes.fromhex("0000000001004290000000000200401400000000"),
     bytes.fromhex("0300c990010042900c800a3c02004014482049a1")),
    (0x3D0E0,
     bytes.fromhex("00000000afb7020800000000"),
     bytes.fromhex("0c80153cafb702084820a0a2")),
    (0x3E104,
     bytes.fromhex("3001a48f0d80113c5c3331860d80033c543363840d80103c603310860d80023c58334284238823023dc0020c23800202a9f2020c000000002120200201000f34ff0018340c80013cf83d2fa00c80013c843b38a0cb2c010c21280002ff0f42300c80013c903b22a40c80013ca03b22a40c80013c943b20a40c80013c983b20a40c80013c9c3b20a40c80013c8c3b20a00c80013ca83b20a40c80013ca43b20a4"),
     bytes.fromhex("0c800f3c4820ee91000000000300c0114820e0a1afb70208000000003001a48f0d80113c5c3331860d80033c543363840d80103c603310860d80023c58334284238823023dc0020c23800202a9f2020c000000002120200201000f34ff0018340c80013cf83d2fa00c80013c843b38a0cb2c010c21280002ff0f42300c80013c903b22a4a03b22a4943b20a4983b20a49c3b20a48c3b20a0a83b20a4a43b20a4")),
)


class DeusPatchError(ValueError):
    pass


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _decode(source: bytes) -> bytes:
    if len(source) < 4:
        raise DeusPatchError("Truncated battle resource")
    declared = int.from_bytes(source[:4], "little")
    size = mechanics.BATTLE_DECODED_SIZE
    if not size <= declared <= size + 7:
        raise DeusPatchError("Unexpected battle allocation")
    decoded = decompress_lzss(source, declared).data
    if decoded[size:] != bytes(declared - size):
        raise DeusPatchError("Nonzero battle allocation padding")
    return decoded[:size]


def patch_decoded_battle(decoded: bytes) -> bytes:
    """Allow only retail plus the two separately audited mechanics words."""
    normalized = bytearray(decoded)
    for fix in mechanics.BATTLE_FIXES:
        word = decoded[fix.offset:fix.offset + 4]
        if word not in (fix.before, fix.after):
            raise DeusPatchError(f"Unsupported battle modification at {fix.id}")
        normalized[fix.offset:fix.offset + 4] = fix.before
    if len(decoded) != mechanics.BATTLE_DECODED_SIZE or _sha(normalized) != mechanics.BATTLE_DECODED_SHA256:
        raise DeusPatchError("Retail battle plus only the known mechanics fixes is required")
    if decoded[SCRATCH_OFFSET - 8:SCRATCH_OFFSET + 4] != bytes.fromhex("0800e0030000000000000000"):
        raise DeusPatchError("Battle end-of-code padding is no longer available")
    patched = bytearray(decoded)
    for offset, before, after in BLOCKS:
        if len(before) != len(after) or decoded[offset:offset + len(before)] != before:
            raise DeusPatchError("Deus camera preimage changed")
        patched[offset:offset + len(after)] = after
        normalized[offset:offset + len(after)] = after
    if _sha(normalized) != PATCHED_BATTLE_SHA256:
        raise DeusPatchError("Isolated source-commit identity mismatch")
    return bytes(patched)


def patch_enemy(source: bytes) -> bytes:
    if _sha(source) != ENEMY_SHA256 or len(source) != 4498:
        raise DeusPatchError("Clean USA retail Deus enemy resource is required")
    if source[0xC16:0xC2A] != bytes.fromhex("01011100010221000103000001000100fdffffff"):
        raise DeusPatchError("Deus move command context changed")
    result = bytearray(source)
    result[0xC25] = 1
    if _sha(result) != PATCHED_ENEMY_SHA256:
        raise DeusPatchError("Deus script identity mismatch")
    return bytes(result)


def verify_unused_script_flags(read: Callable[[int], bytes]) -> dict:
    """Conservatively scan all aligned script records, including headers.

    Native command 01 ignores byte 3. Reject any existing nonzero value, so
    only the one explicitly patched Deus command can request suppression.
    """
    checked = 0
    files = []
    for canonical in ENEMY_FILES:
        data = read(canonical)
        if len(data) < 0xBB2:
            raise DeusPatchError(f"Truncated enemy resource {canonical}")
        start, end = struct.unpack_from("<H", data)[0], struct.unpack_from("<H", data, 0x30)[0]
        if start != 0xBB2 or not start <= end <= len(data) or (end - start) % 4:
            raise DeusPatchError(f"Unexpected script extent in enemy resource {canonical}")
        commands = 0
        for offset in range(start, end, 4):
            if data[offset] == 1:
                commands += 1
                if data[offset + 3] != 0:
                    raise DeusPatchError(f"Existing camera flag in enemy {canonical} at 0x{offset + 3:X}")
        checked += commands
        files.append({"canonical_id": canonical, "sha256": _sha(data), "command_01_records": commands})
    return {"files": files, "file_count": len(files), "command_01_records": checked,
            "nonzero_reserved_bytes": 0}


def build_deus_replacements(read: Callable[[int], bytes], replacements=None) -> tuple[dict[int, bytes], dict]:
    """Compose after mechanics and before XP; reject unrecognized input edits."""
    original_battle = read(38)
    if _sha(original_battle) != mechanics.BATTLE_PACKED_SHA256:
        raise DeusPatchError("Clean USA retail battle source is required")
    original_enemy = read(ENEMY_ID)
    result = dict(replacements or {})
    if ENEMY_ID in result and result[ENEMY_ID] != original_enemy:
        raise DeusPatchError("Deus fix must precede enemy reward or script edits")
    flags = verify_unused_script_flags(read)
    packed_input = result.get(38, original_battle)
    before = _decode(packed_input)
    after = patch_decoded_battle(before)
    packed = compress_lzss_retail(after)
    if _decode(packed) != after:
        raise DeusPatchError("Deus battle recompression failed verification")
    result[38], result[ENEMY_ID] = packed, patch_enemy(original_enemy)
    return result, {
        "id": "deus_mahanon_hp_halving_camera",
        "source": SOURCE,
        "battle_decoded_changed_bytes": sum(a != b for a, b in zip(before, after)),
        "battle_sha256": _sha(packed), "battle_decoded_sha256": _sha(after),
        "enemy_canonical_id": ENEMY_ID, "enemy_offset": "0xC25",
        "enemy_before": "00", "enemy_after": "01", "enemy_sha256": _sha(result[ENEMY_ID]),
        "transient_state": {"address": "0x800C2048", "bytes": 1,
                            "lifetime": "Battle overlay alignment padding; command capture, consume and reset; never saved"},
        "reserved_script_byte_audit": flags,
        "runtime_status": "not tested in emulator",
        "scope": "First Deus fight only: mark its HP-halving command to bypass the problematic camera sequence. Damage and enemy stats unchanged.",
    }
