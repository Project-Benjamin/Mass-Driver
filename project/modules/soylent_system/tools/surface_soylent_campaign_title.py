#!/usr/bin/env python3
"""Add the comprehensive Surface Soylent bootstrap to the v173 title field.

The v173 builder already owns the two-choice title menu and the independent
Mass-Driver path.  This deliberately small transform operates on the checked,
complete Surface title field and initial GameState.  The existing Surface
reset routine still clears its original puzzle state, then hands off to a new
tail which clears the campaign bits, installs the story-correct party, and
enters field 623.  The initial state grants every native on-foot deathblow to
all character forms; levels and every other stat remain untouched.  The
Mass-Driver dispatch and every other title resource remain unchanged.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib
import struct
from typing import Sequence

import modules.soylent_system.base as soylent
import shared.tools.xgdeathblows as deathblows
from shared.tools.xgfield import build_field_preserving, parse_field
from shared.tools.xgscript import AtelScript as ScriptEditor


TITLE_FIELD_CANONICAL_ID = 1586
INITIAL_GAMESTATE_CANONICAL_ID = 2595

BASE_TITLE_BUNDLE_SIZE = soylent.COMPLETE_TITLE_FIELD_BUNDLE_SIZE
BASE_TITLE_BUNDLE_SHA256 = soylent.COMPLETE_TITLE_FIELD_BUNDLE_SHA256
BASE_TITLE_SCRIPT_SIZE = soylent.COMPLETE_TITLE_FIELD_SCRIPT_SIZE
BASE_TITLE_SCRIPT_SHA256 = soylent.COMPLETE_TITLE_FIELD_SCRIPT_SHA256

BASE_INITIAL_GAMESTATE_SIZE = soylent.TITLE_BASE_IDENTITIES[
    INITIAL_GAMESTATE_CANONICAL_ID
][0]
BASE_INITIAL_GAMESTATE_SHA256 = soylent.TITLE_BASE_IDENTITIES[
    INITIAL_GAMESTATE_CANONICAL_ID
][1]
CAMPAIGN_INITIAL_GAMESTATE_SIZE = deathblows.GAMESTATE_SIZE
CAMPAIGN_INITIAL_GAMESTATE_SHA256 = (
    "5880e33ef21edfd370ffa87b199d595c8f6df92d94b7c3bb96abe7a9aa056bcc"
)

CAMPAIGN_STATE_OPERAND = 0x03FA
CAMPAIGN_STATE_BIT_INDICES = (7, 11, 12, 13, 14, 15)
APPOINTMENT_STATE_OPERAND = 0x03EE
APPOINTMENT_STATE_CLEAR = (
    b"\x35"
    + struct.pack("<H", APPOINTMENT_STATE_OPERAND)
    + struct.pack("<H", 0)
    + b"\x40"
)

FEI_CHARACTER = 0
ELLY_CHARACTER = 1
CITAN_CHARACTER = 2
EMERALDA_CHARACTER = 6

# FE19 removes a character from the current party.  FE18 followed by FE1A
# adds and finalizes one in the next free slot.  Removing both characters in
# the v173 bootstrap first makes the final ordering deterministic even when
# this transform is exercised repeatedly during development.
CAMPAIGN_PARTY_BOOTSTRAP = bytes.fromhex(
    "FE 19 06 "
    "FE 19 01 "
    "FE 18 00 FE 1A "
    "FE 18 01 FE 1A "
    "FE 18 02 FE 1A"
)

CAMPAIGN_RESET_PC = 0x01DB
CAMPAIGN_RESET_ROUTINE = (
    APPOINTMENT_STATE_CLEAR
    + b"".join(
        b"\x3B"
        + struct.pack("<H", CAMPAIGN_STATE_OPERAND)
        + struct.pack("<H", bit_index)
        + b"\x40"
        for bit_index in CAMPAIGN_STATE_BIT_INDICES
    )
    + CAMPAIGN_PARTY_BOOTSTRAP
    + soylent._change_field(
        soylent.SURFACE_ENTRY_FIELD,
        soylent.SURFACE_ENTRY_PARAMETER,
    )
)

# The former direct CHANGE_FIELD is replaced by an unconditional jump.  The
# two STOP bytes are unreachable padding which keep the original five-byte
# extent stable and make accidental fallthrough conspicuous in tests.
CAMPAIGN_HANDOFF = b"\x01" + struct.pack("<H", CAMPAIGN_RESET_PC) + b"\x5B\x5B"

CAMPAIGN_TITLE_SCRIPT_SIZE = 739
CAMPAIGN_TITLE_SCRIPT_SHA256 = (
    "b5241c54e1afb253a3ee0478b1cfe1faf8f60aaceee7161bae03ee2bb116c964"
)
CAMPAIGN_TITLE_BUNDLE_SIZE = 4476
CAMPAIGN_TITLE_BUNDLE_SHA256 = (
    "7663ad79bff2c8d177a0473aaedabdde7016b35cccf5902f65760c2d9f3090ea"
)


class CampaignTitleError(soylent.SurfaceSoylentBuildError):
    """Raised when the campaign title source or authored bootstrap drifts."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def transform_title_bundle(source_bundle: bytes) -> bytes:
    """Transform the exact v173 complete title bundle into the campaign one."""

    if (
        len(source_bundle) != BASE_TITLE_BUNDLE_SIZE
        or _sha256(source_bundle) != BASE_TITLE_BUNDLE_SHA256
    ):
        raise CampaignTitleError("Campaign title requires the checked v173 title field")

    parsed = parse_field(source_bundle)
    components = [part.data for part in parsed.parts]
    script = components[soylent.SCRIPT_INDEX]
    if (
        len(script) != BASE_TITLE_SCRIPT_SIZE
        or _sha256(script) != BASE_TITLE_SCRIPT_SHA256
    ):
        raise CampaignTitleError("Campaign title source ATEL changed")

    editor = ScriptEditor(script)
    if editor.bytecode_size != CAMPAIGN_RESET_PC:
        raise CampaignTitleError("Campaign title append point moved")
    if editor.bytecode[0x0171:0x0176] != soylent._change_field(
        soylent.MASS_DRIVER_ENTRY_FIELD,
        0,
    ):
        raise CampaignTitleError("Mass-Driver title route changed")
    if editor.bytecode[0x00BE:0x00C0] != struct.pack(
        "<H", soylent.SURFACE_STATE_RESET_PC
    ):
        raise CampaignTitleError("Surface title dispatch changed")

    reset_start = soylent.SURFACE_STATE_RESET_PC
    reset_end = reset_start + len(soylent.SURFACE_STATE_RESET_ROUTINE)
    if editor.bytecode[reset_start:reset_end] != soylent.SURFACE_STATE_RESET_ROUTINE:
        raise CampaignTitleError("v173 Surface reset routine changed")

    terminal_pc = reset_end - 5
    patched_script = bytearray(script)
    terminal_offset = editor.bytecode_offset + terminal_pc
    patched_script[terminal_offset : terminal_offset + 5] = CAMPAIGN_HANDOFF

    editor = ScriptEditor(bytes(patched_script))
    appended_pc = editor.append_raw_routine(CAMPAIGN_RESET_ROUTINE)
    if appended_pc != CAMPAIGN_RESET_PC:
        raise CampaignTitleError("Campaign title reset tail moved")
    script = editor.to_bytes()
    script_identity = (len(script), _sha256(script))
    if script_identity != (
        CAMPAIGN_TITLE_SCRIPT_SIZE,
        CAMPAIGN_TITLE_SCRIPT_SHA256,
    ):
        raise CampaignTitleError(
            f"Campaign title ATEL output changed: {script_identity}"
        )

    components[soylent.SCRIPT_INDEX] = script
    bundle = build_field_preserving(
        source_bundle,
        components,
        (soylent.SCRIPT_INDEX,),
        compact_changed=True,
    )
    bundle_identity = (len(bundle), _sha256(bundle))
    if bundle_identity != (
        CAMPAIGN_TITLE_BUNDLE_SIZE,
        CAMPAIGN_TITLE_BUNDLE_SHA256,
    ):
        raise CampaignTitleError(
            f"Campaign title field output changed: {bundle_identity}"
        )
    if tuple(part.data for part in parse_field(bundle).parts) != tuple(components):
        raise CampaignTitleError("Campaign title field failed round trip")
    return bundle


def transform_title_resource(
    resource: soylent.PreparedTitleResource,
) -> soylent.PreparedTitleResource:
    """Return a PreparedTitleResource compatible with the campaign wrapper."""

    if resource.canonical_id != TITLE_FIELD_CANONICAL_ID:
        raise CampaignTitleError(
            f"Expected canonical title field {TITLE_FIELD_CANONICAL_ID}, "
            f"got {resource.canonical_id}"
        )
    expected_source_sha256 = soylent.TITLE_BASE_IDENTITIES[
        TITLE_FIELD_CANONICAL_ID
    ][1]
    if resource.source_sha256 != expected_source_sha256:
        raise CampaignTitleError("Prepared title field provenance changed")
    return replace(
        resource,
        name="Title field: Mass-Driver and comprehensive Surface routes",
        filename="1586_title_screen_campaign_surface_route.bin",
        data=transform_title_bundle(resource.data),
    )


def transform_initial_gamestate(source: bytes) -> bytes:
    """Grant every native on-foot deathblow in the checked initial state."""

    if (
        len(source) != BASE_INITIAL_GAMESTATE_SIZE
        or _sha256(source) != BASE_INITIAL_GAMESTATE_SHA256
    ):
        raise CampaignTitleError(
            "Campaign deathblows require the checked Mass-Driver initial GameState"
        )
    result = deathblows.grant_all_on_foot_deathblows(source)
    identity = (len(result), _sha256(result))
    if identity != (
        CAMPAIGN_INITIAL_GAMESTATE_SIZE,
        CAMPAIGN_INITIAL_GAMESTATE_SHA256,
    ):
        raise CampaignTitleError(
            f"Campaign initial GameState output changed: {identity}"
        )
    return result


def transform_initial_gamestate_resource(
    resource: soylent.PreparedTitleResource,
) -> soylent.PreparedTitleResource:
    """Return the Surface GameState replacement with all deathblows learned."""

    if resource.canonical_id != INITIAL_GAMESTATE_CANONICAL_ID:
        raise CampaignTitleError(
            f"Expected canonical initial GameState {INITIAL_GAMESTATE_CANONICAL_ID}, "
            f"got {resource.canonical_id}"
        )
    if resource.source_sha256 != BASE_INITIAL_GAMESTATE_SHA256:
        raise CampaignTitleError("Prepared initial GameState provenance changed")
    return replace(
        resource,
        name="Initial GameState: every native on-foot deathblow learned",
        filename="2595_surface_all_deathblows_gamestate.bin",
        data=transform_initial_gamestate(resource.data),
    )


def transform_title_resources(
    resources: Sequence[soylent.PreparedTitleResource],
) -> tuple[soylent.PreparedTitleResource, ...]:
    """Transform resources 1586/2595 and preserve every other title resource."""

    title_fields = [
        resource
        for resource in resources
        if resource.canonical_id == TITLE_FIELD_CANONICAL_ID
    ]
    if len(title_fields) != 1:
        raise CampaignTitleError(
            "Campaign title resources require exactly one canonical field 1586"
        )
    initial_states = [
        resource
        for resource in resources
        if resource.canonical_id == INITIAL_GAMESTATE_CANONICAL_ID
    ]
    if len(initial_states) != 1:
        raise CampaignTitleError(
            "Campaign title resources require exactly one canonical GameState 2595"
        )
    return tuple(
        transform_title_resource(resource)
        if resource.canonical_id == TITLE_FIELD_CANONICAL_ID
        else transform_initial_gamestate_resource(resource)
        if resource.canonical_id == INITIAL_GAMESTATE_CANONICAL_ID
        else resource
        for resource in resources
    )


__all__ = [
    "APPOINTMENT_STATE_CLEAR",
    "APPOINTMENT_STATE_OPERAND",
    "BASE_INITIAL_GAMESTATE_SHA256",
    "BASE_INITIAL_GAMESTATE_SIZE",
    "BASE_TITLE_BUNDLE_SHA256",
    "BASE_TITLE_BUNDLE_SIZE",
    "BASE_TITLE_SCRIPT_SHA256",
    "BASE_TITLE_SCRIPT_SIZE",
    "CAMPAIGN_HANDOFF",
    "CAMPAIGN_INITIAL_GAMESTATE_SHA256",
    "CAMPAIGN_INITIAL_GAMESTATE_SIZE",
    "CAMPAIGN_PARTY_BOOTSTRAP",
    "CAMPAIGN_RESET_PC",
    "CAMPAIGN_RESET_ROUTINE",
    "CAMPAIGN_STATE_BIT_INDICES",
    "CAMPAIGN_STATE_OPERAND",
    "CAMPAIGN_TITLE_BUNDLE_SHA256",
    "CAMPAIGN_TITLE_BUNDLE_SIZE",
    "CAMPAIGN_TITLE_SCRIPT_SHA256",
    "CAMPAIGN_TITLE_SCRIPT_SIZE",
    "CampaignTitleError",
    "INITIAL_GAMESTATE_CANONICAL_ID",
    "transform_initial_gamestate",
    "transform_initial_gamestate_resource",
    "transform_title_bundle",
    "transform_title_resource",
    "transform_title_resources",
]
