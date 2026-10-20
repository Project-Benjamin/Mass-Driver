#!/usr/bin/env python3
"""Build an isolated Mass Driver Guardian enemy resource set.

The retail mechanical ``Pedestal`` enemy is a suitable visual and behavioral
base for the Mass Driver security boss, but its normal resource set ``0x41``
is also used by Disc 2 world-map encounters.  Replacing that set directly
would rename and strengthen every retail Pedestal.

Disc 2 does not reference enemy set ``0x10`` from any field or world-map
formation.  This module therefore clones the checked Pedestal stats/AI and
model resources into set ``0x10`` (canonicals 2650/2651), then changes only
enemy record 0's name and current/maximum Gear HP.  Both sources and both
outputs are SHA-256 locked so the dungeon builder cannot silently transform
an incompatible translation or model revision.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct


PEDESTAL_STATS_CANONICAL_ID = 2748
PEDESTAL_MODEL_CANONICAL_ID = 2749
GUARDIAN_STATS_CANONICAL_ID = 2650
GUARDIAN_MODEL_CANONICAL_ID = 2651
GUARDIAN_RESOURCE_SET_ID = 0x10

PEDESTAL_STATS_SIZE = 4367
PEDESTAL_MODEL_SIZE = 197900
PEDESTAL_STATS_SHA256 = (
    "88f1d4c08bdbdc0355013fb818e375c1fb4c4c632b04bbaac2b968d1be0136d4"
)
PEDESTAL_MODEL_SHA256 = (
    "64dcb01ee940438a8b31657d4805f7679e61da3000b937502646cc743069f1d6"
)

GUARDIAN_STATS_SHA256 = (
    "c53522461bec68e376b0290a90e91835a19d2d7e749665c18a4302a44c616bbd"
)
# The model/animation payload is an exact clone; only its destination changes.
GUARDIAN_MODEL_SHA256 = PEDESTAL_MODEL_SHA256

PEDESTAL_HP = 12000
GUARDIAN_HP = 36000
GEAR_CURRENT_HP_OFFSET = 0x136
GEAR_MAXIMUM_HP_OFFSET = 0x13A
ENEMY_NAME_OFFSET = 0x10A2

# Xenogears' single-byte dialogue glyph encoding, without a terminator.
PEDESTAL_NAME = bytes((0x2F, 0x41, 0x40, 0x41, 0x4F, 0x50, 0x3D, 0x48))
GUARDIAN_NAME = bytes((0x26, 0x51, 0x3D, 0x4E, 0x40, 0x45, 0x3D, 0x4A))


class GuardianResourceError(ValueError):
    """Raised when a Guardian source or deterministic output is not audited."""


@dataclass(frozen=True)
class CanonicalResourcePayload:
    """One checked byte payload and the canonical Disc 2 ID it must replace."""

    canonical_id: int
    source_canonical_id: int
    data: bytes
    sha256: str


@dataclass(frozen=True)
class IsolatedGuardianResources:
    """The stats/model pair for isolated enemy resource set ``0x10``."""

    stats: CanonicalResourcePayload
    model: CanonicalResourcePayload

    def canonical_payloads(self) -> tuple[tuple[int, bytes], ...]:
        """Return replacement-friendly ``(canonical_id, data)`` pairs."""

        return (
            (self.stats.canonical_id, self.stats.data),
            (self.model.canonical_id, self.model.data),
        )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _check_source(
    data: bytes,
    *,
    label: str,
    expected_size: int,
    expected_sha256: str,
) -> None:
    if len(data) != expected_size:
        raise GuardianResourceError(
            f"{label} is {len(data)} bytes; expected {expected_size}"
        )
    actual_sha256 = _sha256(data)
    if actual_sha256 != expected_sha256:
        raise GuardianResourceError(
            f"{label} SHA-256 is {actual_sha256}; expected {expected_sha256}"
        )


def _check_region(
    data: bytes,
    offset: int,
    expected: bytes,
    label: str,
) -> None:
    actual = data[offset : offset + len(expected)]
    if actual != expected:
        raise GuardianResourceError(
            f"{label} at 0x{offset:X} is {actual.hex(' ')}; "
            f"expected {expected.hex(' ')}"
        )


def patch_guardian_stats(pedestal_stats: bytes) -> bytes:
    """Return the checked Pedestal stats/AI payload renamed and set to 36k HP."""

    source = bytes(pedestal_stats)
    _check_source(
        source,
        label=f"Pedestal stats canonical {PEDESTAL_STATS_CANONICAL_ID}",
        expected_size=PEDESTAL_STATS_SIZE,
        expected_sha256=PEDESTAL_STATS_SHA256,
    )

    native_hp = struct.pack("<I", PEDESTAL_HP)
    _check_region(source, GEAR_CURRENT_HP_OFFSET, native_hp, "current Gear HP")
    _check_region(source, GEAR_MAXIMUM_HP_OFFSET, native_hp, "maximum Gear HP")
    _check_region(source, ENEMY_NAME_OFFSET, PEDESTAL_NAME, "enemy name")

    result = bytearray(source)
    guardian_hp = struct.pack("<I", GUARDIAN_HP)
    result[
        GEAR_CURRENT_HP_OFFSET : GEAR_CURRENT_HP_OFFSET + len(guardian_hp)
    ] = guardian_hp
    result[
        GEAR_MAXIMUM_HP_OFFSET : GEAR_MAXIMUM_HP_OFFSET + len(guardian_hp)
    ] = guardian_hp
    result[ENEMY_NAME_OFFSET : ENEMY_NAME_OFFSET + len(GUARDIAN_NAME)] = (
        GUARDIAN_NAME
    )
    output = bytes(result)

    mutable_offsets = frozenset(
        range(GEAR_CURRENT_HP_OFFSET, GEAR_CURRENT_HP_OFFSET + 4)
    ) | frozenset(range(GEAR_MAXIMUM_HP_OFFSET, GEAR_MAXIMUM_HP_OFFSET + 4))
    mutable_offsets |= frozenset(
        range(ENEMY_NAME_OFFSET, ENEMY_NAME_OFFSET + len(GUARDIAN_NAME))
    )
    if any(
        source[index] != output[index] and index not in mutable_offsets
        for index in range(len(source))
    ):
        raise GuardianResourceError(
            "Guardian stats changed data outside the audited name/HP regions"
        )

    output_sha256 = _sha256(output)
    if output_sha256 != GUARDIAN_STATS_SHA256:
        raise GuardianResourceError(
            f"Guardian stats SHA-256 is {output_sha256}; "
            f"expected {GUARDIAN_STATS_SHA256}"
        )
    return output


def build_isolated_guardian_resources(
    pedestal_stats: bytes,
    pedestal_model: bytes,
) -> IsolatedGuardianResources:
    """Return the hash-locked Guardian payloads for canonicals 2650 and 2651."""

    model = bytes(pedestal_model)
    _check_source(
        model,
        label=f"Pedestal model canonical {PEDESTAL_MODEL_CANONICAL_ID}",
        expected_size=PEDESTAL_MODEL_SIZE,
        expected_sha256=PEDESTAL_MODEL_SHA256,
    )
    stats = patch_guardian_stats(pedestal_stats)

    if _sha256(model) != GUARDIAN_MODEL_SHA256:
        raise GuardianResourceError("Cloned Guardian model failed its output hash")

    return IsolatedGuardianResources(
        stats=CanonicalResourcePayload(
            canonical_id=GUARDIAN_STATS_CANONICAL_ID,
            source_canonical_id=PEDESTAL_STATS_CANONICAL_ID,
            data=stats,
            sha256=GUARDIAN_STATS_SHA256,
        ),
        model=CanonicalResourcePayload(
            canonical_id=GUARDIAN_MODEL_CANONICAL_ID,
            source_canonical_id=PEDESTAL_MODEL_CANONICAL_ID,
            data=model,
            sha256=GUARDIAN_MODEL_SHA256,
        ),
    )


__all__ = [
    "CanonicalResourcePayload",
    "ENEMY_NAME_OFFSET",
    "GEAR_CURRENT_HP_OFFSET",
    "GEAR_MAXIMUM_HP_OFFSET",
    "GUARDIAN_HP",
    "GUARDIAN_MODEL_CANONICAL_ID",
    "GUARDIAN_MODEL_SHA256",
    "GUARDIAN_NAME",
    "GUARDIAN_RESOURCE_SET_ID",
    "GUARDIAN_STATS_CANONICAL_ID",
    "GUARDIAN_STATS_SHA256",
    "GuardianResourceError",
    "IsolatedGuardianResources",
    "PEDESTAL_HP",
    "PEDESTAL_MODEL_CANONICAL_ID",
    "PEDESTAL_MODEL_SHA256",
    "PEDESTAL_NAME",
    "PEDESTAL_STATS_CANONICAL_ID",
    "PEDESTAL_STATS_SHA256",
    "build_isolated_guardian_resources",
    "patch_guardian_stats",
]
