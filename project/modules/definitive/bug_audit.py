"""Read-only coverage checks for a bounded set of independently sourced bugs.

An unchanged retail site is evidence that the inspected correction is absent.
A changed site is not evidence that it is fixed. Neither result is gameplay QA.
"""
from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from shared.tools.xgdisc import Mode2Image
from shared.tools.xgfield import decompress_lzss
from modules.definitive import mechanics


DEUS_ENEMY_SHA256 = "338b41b89491c4d53185e89b4efbacf974848f6561151573bd8406f5410d300a"
DEUS_SOURCE = "https://github.com/PWBuild-Team/Perfect_Works_Build/commit/c054f82f8e8dab8c6ad5106ed270d301d586aa54"
BILLY_SOURCE = "https://github.com/PWBuild-Team/Perfect_Works_Build/commit/7a9f6e74826c623e028793194a5017a71d320a8b"
STATUS_SOURCE = "https://github.com/PWBuild-Team/Perfect_Works_Build/wiki/Battle-Executable-edits"


@dataclass(frozen=True)
class Probe:
    canonical: int
    start: int
    end: int
    role: str


KNOWN_ISSUES = (
    {
        "id": "deus_hp_halving_camera_freeze",
        "title": "Deus first fight: HP-halving move at a side camera angle",
        "source": DEUS_SOURCE,
        "probes": (
            Probe(38, 0xAD64, 0xAD78, "capture camera-suppression script flag"),
            Probe(38, 0x3D0E0, 0x3D0EC, "reset camera-suppression state"),
            Probe(38, 0x3E104, 0x3E1A4, "guard the camera routine"),
            Probe(2746, 0xC25, 0xC26, "mark Deus's affected move"),
        ),
    },
    {
        "id": "billy_ether_ammo_refresh",
        "title": "Billy: changing equipped elemental Ether ammunition",
        "source": BILLY_SOURCE,
        "probes": (
            Probe(38, 0x248A0, 0x248B8, "refresh element from equipped ammunition"),
            Probe(38, 0x2B748, 0x2B970, "upstream routine and reclaimed initializer space"),
        ),
    },
)

STATUS_PROBES = (
    Probe(38, 0x25694, 0x258CC, "shared defense / Wither / Weaken handling"),
    Probe(38, 0x25E3C, 0x26258, "status dispatch and target handling"),
    Probe(38, 0x29B3C, 0x29CA4, "status duration handling"),
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _battle(packed: bytes) -> bytes:
    if len(packed) < 4:
        raise ValueError("Truncated battle resource")
    size = int.from_bytes(packed[:4], "little")
    meaningful = mechanics.BATTLE_DECODED_SIZE
    if not meaningful <= size <= meaningful + 7:
        raise ValueError("Unsupported battle allocation size")
    data = decompress_lzss(packed, size).data
    if data[meaningful:] != bytes(size - meaningful):
        raise ValueError("Nonzero unexpected battle allocation tail")
    return data[:meaningful]


def _probe(probe: Probe, retail: dict[int, bytes], current: dict[int, bytes]) -> dict:
    original, actual = retail[probe.canonical], current[probe.canonical]
    if len(original) < probe.end or len(actual) < probe.end:
        raise ValueError(f"Truncated resource {probe.canonical} at probe {probe.role}")
    before = original[probe.start:probe.end]
    after = actual[probe.start:probe.end]
    return {
        "canonical_id": probe.canonical,
        "offset": f"0x{probe.start:X}",
        "length": probe.end - probe.start,
        "role": probe.role,
        "retail_sha256": _sha(before),
        "current_sha256": _sha(after),
        "retail_bytes_retained": before == after,
        "changed_bytes": sum(a != b for a, b in zip(before, after)),
    }


def audit_resources(read_retail: Callable[[int], bytes], read_current: Callable[[int], bytes]) -> dict:
    """Inspect actual media resources without patching, execution, or assumptions."""
    packed_retail = {n: read_retail(n) for n in (38, 2602, 2746)}
    expected = {
        38: mechanics.BATTLE_PACKED_SHA256,
        2602: mechanics.GEAR_SHOP_SHA256,
        2746: DEUS_ENEMY_SHA256,
    }
    for n, digest in expected.items():
        if _sha(packed_retail[n]) != digest:
            raise ValueError(f"Canonical {n} is not the audited USA retail preimage")
    packed_current = {n: read_current(n) for n in expected}
    retail, current = dict(packed_retail), dict(packed_current)
    retail[38], current[38] = _battle(retail[38]), _battle(current[38])
    if _sha(retail[38]) != mechanics.BATTLE_DECODED_SHA256:
        raise ValueError("Retail battle decoding differs from the audited identity")
    implemented = []
    for fix in mechanics.BATTLE_FIXES + (mechanics.GEAR_SHOP_FIX,):
        canonical = 2602 if fix.id == mechanics.GEAR_SHOP_FIX_ID else 38
        actual = current[canonical][fix.offset:fix.offset + len(fix.after)]
        implemented.append({
            "id": fix.id, "canonical_id": canonical, "offset": f"0x{fix.offset:X}",
            "expected": fix.after.hex(), "actual": actual.hex(),
            "correction_bytes_present": actual == fix.after,
            "runtime_status": "not tested",
        })
    known = []
    for issue in KNOWN_ISSUES:
        probes = [_probe(p, retail, current) for p in issue["probes"]]
        unchanged = all(p["retail_bytes_retained"] for p in probes)
        known.append({
            **{k: v for k, v in issue.items() if k != "probes"},
            "status": "inspected_correction_absent" if unchanged else "modified_requires_validation",
            "probes": probes,
            "runtime_status": "not tested",
        })
    return {
        "format": "xenogears-definitive-known-bug-audit-v1",
        "all_bugs_fixed_verified": False,
        "runtime_status": "not tested",
        "scope": "Three implemented corrections and two further known issues; not an exhaustive bug catalogue.",
        "resource_hashes": [{"canonical_id": n, "retail_sha256": _sha(packed_retail[n]),
                             "current_sha256": _sha(packed_current[n])} for n in expected],
        "implemented_corrections": implemented,
        "known_issues": known,
        "status_effect_investigation": {
            "source": STATUS_SOURCE,
            "status": "behavior_not_certified",
            "probes": [_probe(p, retail, current) for p in STATUS_PROBES],
            "note": "Def Up mask correction alone does not validate every Bracer, Wither, Weaken, immunity, or duration case. Upstream changes mix repair and balance changes.",
        },
        "unresolved": ["Ether Veiler and remaining item/spell cases need individual effect, target, duration, immunity, and description checks.",
                       "Scene, audio, camera, inventory, save/load, and disc-transition bugs are outside this bounded binary audit."],
    }


def audit_disc(retail: Path, current: Path, disc: int) -> dict:
    if disc not in (1, 2):
        raise ValueError("Disc must be 1 or 2")
    def reader(path: Path):
        image = Mode2Image(path)
        entries = image.read_index()
        def read(canonical: int) -> bytes:
            return image.extract_entry(entries[canonical - (5 if disc == 2 else 0)])
        return read
    result = audit_resources(reader(retail), reader(current))
    result.update({"disc": disc, "retail": str(retail.resolve()), "current": str(current.resolve())})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retail", required=True, type=Path)
    parser.add_argument("--current", required=True, type=Path)
    parser.add_argument("--disc", required=True, type=int, choices=(1, 2))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_disc(args.retail, args.current, args.disc)
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
