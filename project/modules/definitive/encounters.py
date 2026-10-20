"""Optional suppression of native random dispatch on both retail overlays.

Two isolated instructions disable field random dispatch and world-map random
readiness. Forced battle script handlers are not patched. Runtime coverage of
story encounters remains pending; static checks are recorded separately.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import hashlib

from shared.tools.xgfield import compress_lzss_retail, decompress_lzss


class EncounterPatchError(ValueError):
    """The image or encounter mode does not match the audited retail input."""


@dataclass(frozen=True)
class EncounterPatch:
    canonical_id: int
    title: str
    packed_size: int
    packed_sha256: str
    decoded_size: int
    decoded_sha256: str
    offset: int
    before: bytes
    after: bytes
    patched_decoded_sha256: str
    behavior: str


NO_ENCOUNTER_PATCHES = (
    EncounterPatch(
        36, "Field random encounters", 125_304,
        "7735f4e2f204b7afd053d95f2812053b56eb03306c7d2de38c08b2d78ba392dd",
        260_862,
        "38a1ce829a6f094c505f67143d6ace2d328418c65425a7383991179467e1fdfc",
        0x99CC, bytes.fromhex("1C 00 A0 10"), bytes.fromhex("1C 00 00 10"),
        "129429fac491a9cdedba6660d436ab1af85fb4e00fce1b46adfdb5a8dfd9acbf",
        "The field random-check function always takes its existing no-encounter "
        "epilogue after advancing timers and selecting a weighted formation. "
        "The separate forced battle opcode handler is untouched.",
    ),
    EncounterPatch(
        37, "World-map random encounters", 92_180,
        "0f7e7a283fc5ef25d4a82960e16b119d09e1ba5594cc02069cf3dd2113f48803",
        180_422,
        "4c15fd32b3a03d7cd5ea4403dcaabc70abaf99b6aaca65d63d6866803edaac70",
        0x5940, bytes.fromhex("0C D8 22 AC"), bytes.fromhex("0C D8 20 AC"),
        "56204adae5d04f59bd64545aa81faf78cc6f9f9454ef52242e8addc43084ab89",
        "The world-map random timer writes zero to the random-readiness counter "
        "instead of its incremented value. Timer generation, movement and "
        "other transition paths retain their retail instructions.",
    ),
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_no_encounter_resource(source: bytes, canonical_id: int) -> tuple[bytes, dict]:
    """Patch exactly one audited retail resource and return a candidate receipt."""
    patch = next((item for item in NO_ENCOUNTER_PATCHES if item.canonical_id == canonical_id), None)
    if patch is None:
        raise EncounterPatchError(f"unsupported encounter resource: {canonical_id}")
    digest = _sha256(source)
    if len(source) != patch.packed_size or digest != patch.packed_sha256:
        raise EncounterPatchError(
            f"clean USA retail resource {canonical_id} required: {len(source)} bytes, {digest}"
        )
    # Retail field 36's declared stream extends into zero-filled sector tail.
    # Only the exact frozen preimage takes this path, and the full decoded
    # result must still match its independent frozen hash.
    decoded = decompress_lzss(source + bytes(16), patch.decoded_size).data
    if _sha256(decoded) != patch.decoded_sha256:
        raise EncounterPatchError(f"decoded resource {canonical_id} identity changed")
    if decoded[patch.offset:patch.offset + 4] != patch.before:
        raise EncounterPatchError(f"resource {canonical_id} instruction preimage changed")
    changed = bytearray(decoded)
    changed[patch.offset:patch.offset + 4] = patch.after
    changed = bytes(changed)
    if _sha256(changed) != patch.patched_decoded_sha256:
        raise EncounterPatchError(f"resource {canonical_id} patched identity changed")
    packed = compress_lzss_retail(changed)
    declared = int.from_bytes(packed[:4], "little")
    padding = declared - len(changed)
    roundtrip = decompress_lzss(packed, declared).data
    if not 0 <= padding <= 7 or roundtrip != changed + bytes(padding):
        raise EncounterPatchError(f"resource {canonical_id} failed LZSS round-trip")
    return packed, {
        "canonical_id": canonical_id,
        "title": patch.title,
        "source_sha256": digest,
        "source_decoded_sha256": patch.decoded_sha256,
        "patched_sha256": _sha256(packed),
        "patched_decoded_sha256": patch.patched_decoded_sha256,
        "offset": f"0x{patch.offset:05X}",
        "before": patch.before.hex(),
        "after": patch.after.hex(),
        "behavior": patch.behavior,
        "allocation_padding_bytes": padding,
        "binary_validation": "exact retail identity; one instruction changed; full LZSS round-trip",
        "runtime_validation": "not tested in emulator",
    }


def build_encounter_replacements(
    read_canonical: Callable[[int], bytes], mode: str = "normal"
) -> tuple[dict[int, bytes], dict]:
    """Build optional random-encounter suppression without editing field scripts."""
    if mode not in ("normal", "none"):
        raise EncounterPatchError(
            f"encounter mode {mode!r} is not supported here; half-rate requires a separate verified implementation"
        )
    if mode == "normal":
        return {}, {"mode": mode, "resources": []}
    replacements = {}
    receipts = []
    for patch in NO_ENCOUNTER_PATCHES:
        packed, receipt = patch_no_encounter_resource(read_canonical(patch.canonical_id), patch.canonical_id)
        replacements[patch.canonical_id] = packed
        receipts.append(receipt)
    return replacements, {
        "mode": mode,
        "status": "binary-verified candidate; emulator validation pending",
        "resources": receipts,
        "forced_encounters": "field forced-battle handler and event scripts unchanged; story runtime tests pending",
        "runtime_validation": "not tested in emulator",
    }
