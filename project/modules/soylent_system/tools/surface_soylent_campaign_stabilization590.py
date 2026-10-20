#!/usr/bin/env python3
"""Recover the reserved Krelian Lab stabilization ward as logical field 590.

V194 briefly installed Disc 1 field 567 between Intake and the service
manifold.  V195 correctly returned logical field 567 to the user's requested
empty examination room, while preserving the complete ward donor for later
use.  This module consumes that frozen donor preparation, installs it into the
checked dummy Disc 2 field-590 pair, and enables the donor's native parameter-2
arrival beside its third paired door.

The campaign layer owns the final three reciprocal destinations and the
production gate.  This module changes no geometry, models, graphics, encounter
data, door helpers, or neutralized story actors.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
import struct

import modules.soylent_system.base as surface
import modules.soylent_system.tools.surface_soylent_campaign_donor567 as donor567
from shared.tools.xgfield import build_field_preserving, parse_field
from shared.tools.xgscript import AtelScript as ScriptEditor


SCENE = 590
TARGET_BUNDLE_ID = 1786
TARGET_GRAPHICS_ID = 1787
TARGET_IDS = (TARGET_BUNDLE_ID, TARGET_GRAPHICS_ID)
SOURCE_SCENE = donor567.SCENE
SOURCE_IDS = donor567.DONOR567_SOURCE_IDS

# The recovered room keeps the donor's three native door locations, but all
# arrivals are moved farther into their audited room-side triangles.  Its
# rectangular ghost targets can therefore be widened from 0x1E to 0x24 while
# a held Cross press remains unable to bounce the party back through a door.
ACTION_HALF_EXTENT = 0x24
ENTRY_PARAMETERS = (0, 1, 2)
ENTRY_POSITIONS = {
    0: (140, 300),
    1: (830, -360),
    2: (890, -125),
}
ENTRY_WALKMESH = 0
ENTRY_DIRECTIONS = {
    0: (1, 1),
    1: (5, 5),
    2: (7, 7),
}
ENTRY_TRIANGLES = {
    0: 88,
    1: 51,
    2: 52,
}
ENTRY_SOURCE = {
    0: struct.pack("<hhBBB", 140, 350, 0, 1, 1),
    1: struct.pack("<hhBBB", 860, -360, 0, 5, 5),
    2: struct.pack("<hhBBB", 915, -200, 0, 0xFF, 0xFF),
}
ENTRY_PLAYABLE = {
    parameter: struct.pack(
        "<hhBBB",
        *ENTRY_POSITIONS[parameter],
        ENTRY_WALKMESH,
        *ENTRY_DIRECTIONS[parameter],
    )
    for parameter in ENTRY_PARAMETERS
}

# Compatibility names make the production-side third entry explicit to the
# campaign builder and its focused route tests.
PRODUCTION_ENTRY_PARAMETER = 2
PRODUCTION_ENTRY_POSITION = ENTRY_POSITIONS[PRODUCTION_ENTRY_PARAMETER]
PRODUCTION_ENTRY_WALKMESH = ENTRY_WALKMESH
PRODUCTION_ENTRY_DIRECTIONS = ENTRY_DIRECTIONS[PRODUCTION_ENTRY_PARAMETER]
PRODUCTION_ENTRY_TRIANGLE = ENTRY_TRIANGLES[PRODUCTION_ENTRY_PARAMETER]
PRODUCTION_ENTRY_SOURCE = ENTRY_SOURCE[PRODUCTION_ENTRY_PARAMETER]
PRODUCTION_ENTRY_PLAYABLE = ENTRY_PLAYABLE[PRODUCTION_ENTRY_PARAMETER]

MANIFOLD_BULKHEAD_DESTINATION = (565, 1)
MANIFOLD_STAFF_DESTINATION = (565, 2)
SORTING_DESTINATION = (624, 0)
PRODUCTION_DENIAL_DIALOGUE_ID = donor567.SEALED_DIALOGUE_ID
PRODUCTION_DENIAL_DIALOGUE = (
    "PRODUCTION ACCESS SEALED\n"
    "Required: security keycard, quarantine consensus,\n"
    "resonance authorization, and bio-interface cutoff.<Close>"
)


class Stabilization590Error(surface.SurfaceSoylentBuildError):
    """Raised when the recovered ward or its dummy target changes."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_targets_are_dummy(source_disc: Path | str) -> None:
    """Refuse to overwrite field 590 unless both Disc 2 slots are dummies."""

    expected = {
        canonical_id: (len(surface.DONOR_DUMMY), surface.DONOR_DUMMY_SHA256)
        for canonical_id in TARGET_IDS
    }
    resources = surface._load_canonical_resources(source_disc, expected)
    if set(resources) != set(TARGET_IDS) or any(
        resources[canonical_id] != surface.DONOR_DUMMY
        for canonical_id in TARGET_IDS
    ):
        raise Stabilization590Error(
            "Disc 2 field-590 recovered-ward target is not the checked "
            "CDMAKE dummy"
        )


def prepare_stabilization590(
    source_bundle: bytes,
    graphics: bytes,
) -> surface.PreparedDonorField:
    """Prepare the reserved ward with three wide-target-safe arrivals."""

    prepared = donor567.prepare_donor567(source_bundle, graphics)
    script = prepared.components[surface.SCRIPT_INDEX]
    for parameter in ENTRY_PARAMETERS:
        script = surface._patch_bytecode(
            script,
            1 + 7 * parameter,
            ENTRY_SOURCE[parameter],
            ENTRY_PLAYABLE[parameter],
        )

    components = list(prepared.components)
    triangles = surface._walkmesh_layer(
        components[1],
        ENTRY_WALKMESH,
    )
    for parameter in ENTRY_PARAMETERS:
        hits = tuple(
            index
            for index, triangle in enumerate(triangles)
            if surface._point_inside_triangle(
                ENTRY_POSITIONS[parameter],
                triangle,
            )
        )
        if hits != (ENTRY_TRIANGLES[parameter],):
            raise Stabilization590Error(
                f"Recovered stabilization-ward parameter {parameter} left "
                f"audited triangle {ENTRY_TRIANGLES[parameter]}: {hits}"
            )

    components[surface.SCRIPT_INDEX] = script
    bundle = build_field_preserving(
        prepared.bundle,
        components,
        (surface.SCRIPT_INDEX,),
        compact_changed=True,
    )
    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise Stabilization590Error(
            "Recovered stabilization ward failed decoded-stream round trip"
        )

    identity = replace(
        prepared.identity,
        scene=SCENE,
        bundle_id=TARGET_BUNDLE_ID,
        graphics_id=TARGET_GRAPHICS_ID,
    )
    return surface.PreparedDonorField(
        identity,
        (
            "recovered Clinical Stabilization Ward; three audited entries; "
            "native paired leaves and helpers retained; retail surgery scene "
            "neutralized; final reciprocal routes owned by campaign V201"
        ),
        prepared.source_bundle,
        prepared.graphics,
        reparsed.header,
        tuple(components),
        bundle,
        tuple((parameter, ENTRY_TRIANGLES[parameter]) for parameter in ENTRY_PARAMETERS),
    )


def prepare_stabilization590_from_discs(
    source_disc: Path | str,
    donor_disc: Path | str,
) -> surface.PreparedDonorField:
    """Verify the target and prepare the reserved Disc 1 field-567 donor."""

    verify_targets_are_dummy(source_disc)
    source_bundle, graphics = donor567.load_donor567_source(donor_disc)
    return prepare_stabilization590(source_bundle, graphics)


__all__ = [
    "ACTION_HALF_EXTENT",
    "ENTRY_DIRECTIONS",
    "ENTRY_PARAMETERS",
    "ENTRY_PLAYABLE",
    "ENTRY_POSITIONS",
    "ENTRY_SOURCE",
    "ENTRY_TRIANGLES",
    "ENTRY_WALKMESH",
    "MANIFOLD_BULKHEAD_DESTINATION",
    "MANIFOLD_STAFF_DESTINATION",
    "PRODUCTION_DENIAL_DIALOGUE",
    "PRODUCTION_DENIAL_DIALOGUE_ID",
    "PRODUCTION_ENTRY_DIRECTIONS",
    "PRODUCTION_ENTRY_PARAMETER",
    "PRODUCTION_ENTRY_PLAYABLE",
    "PRODUCTION_ENTRY_POSITION",
    "PRODUCTION_ENTRY_SOURCE",
    "PRODUCTION_ENTRY_TRIANGLE",
    "SCENE",
    "SORTING_DESTINATION",
    "SOURCE_IDS",
    "SOURCE_SCENE",
    "TARGET_IDS",
    "prepare_stabilization590",
    "prepare_stabilization590_from_discs",
    "verify_targets_are_dummy",
]
