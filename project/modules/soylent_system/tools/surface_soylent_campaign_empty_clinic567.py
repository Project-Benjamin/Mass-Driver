#!/usr/bin/env python3
"""Prepare logical field 567 as an empty Ethos medical room.

The visual source is Disc 1 field 352, the compact Ethos infirmary already
used elsewhere by the Surface campaign.  This isolated preparation keeps the
room shell, examination bed, props, walkmesh, actor/sprite archives, dialogue,
and external graphics byte-identical.  Retail story execution is removed:
only the safe field initializer, runtime party actors, and the native animated
exit leaf remain reachable.  A single controller returns to field 621/p4 and
all random-encounter weights are zero.

The module deliberately does not edit the campaign builder or topology.  It
exports the frozen entry, door, collision, component, and output contracts
needed for that later integration.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import struct

import modules.soylent_system.base as surface
from shared.tools.xgdisc import (
    FIELD_DIRECTORY,
    FIRST_FIELD_LOCAL_FILE,
    Mode2Image,
    directory_file_fat_index,
)
from shared.tools.xgencounter import EncounterTable
from shared.tools.xgfield import build_field_preserving, parse_field
from shared.tools.xgscript import AtelScript as ScriptEditor


SCENE = 567
SOURCE_SCENE = 352
TARGET_BUNDLE_ID = 1740
TARGET_GRAPHICS_ID = 1741
SOURCE_BUNDLE_ID = 1315
SOURCE_GRAPHICS_ID = 1316

SOURCE_BUNDLE_IDENTITY = (
    83_720,
    "99fe2c065c60176f5199ac672f7cf513f1f0a81df4af5dfe31020e0610112074",
)
SOURCE_GRAPHICS_IDENTITY = (
    131_072,
    "d151035c6523091d22255ebf587e463748a74d1db521cce852a8d85f6e197d41",
)
SOURCE_SCRIPT_IDENTITY = (
    3_024,
    "37fdf199d4839fd0b9d6ca23067b4b4fccabf9b173fcfa367761f369075520e6",
)
SOURCE_HEADER_IDENTITY = (
    928,
    "01337fb6045d01fc6072e776dee6e65ef38bb110ccd2af9ae90cc39a45c8cb8b",
)
SOURCE_DIALOGUE_IDENTITY = (
    5_177,
    "6d9ae403fabe60061966a43a50c5d970317a2f0997bf5554e0dab588866ce518",
)
SOURCE_COMPONENT_IDENTITIES = (
    (4, "df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119"),
    (1_948, "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d8cca4238393571df"),
    (16_564, "23fee92e7341e7d55a9e208352629a86e9c33e685b3fa25e89fa3bb71be6feb1"),
    (20_484, "080399f5e7a2c6a129f46ca7dd21c40ad6beb5ed3c14840c0cdca6a4b749514a"),
    (88_132, "891c7eba778f1dba2c01e3a7b6895200f7901103a02e8e6e1f029229e61973f9"),
    SOURCE_SCRIPT_IDENTITY,
    (528, "551596bcaf880334be106c719d5f4fedf4ffd90430d1f9b16b93e6638e87ea87"),
    SOURCE_DIALOGUE_IDENTITY,
    (0, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
)

EMPTY_CLINIC567_IDENTITY = surface.SourceIdentity(
    SCENE,
    TARGET_BUNDLE_ID,
    TARGET_GRAPHICS_ID,
    *SOURCE_BUNDLE_IDENTITY,
    *SOURCE_GRAPHICS_IDENTITY,
    *SOURCE_SCRIPT_IDENTITY,
    *SOURCE_HEADER_IDENTITY,
)
DONOR567_IDENTITY = EMPTY_CLINIC567_IDENTITY
EMPTY_CLINIC567_TARGET_IDS = (TARGET_BUNDLE_ID, TARGET_GRAPHICS_ID)
EMPTY_CLINIC567_SOURCE_IDS = (SOURCE_BUNDLE_ID, SOURCE_GRAPHICS_ID)

SOURCE_ENTITY_COUNT = 19
SOURCE_HEADER_ACTOR_COUNT = 33
SOURCE_BYTECODE_SIZE = 0x068C

# The sole entry is fifty world units inside the closed door plane.  The
# campaign's ordinary 0x0E seal plus Fei's 0x10 radius reaches 44 units, so a
# fresh held-Cross arrival remains clear of an immediate reciprocal retrigger.
ENTRY_PARAMETER = 0
ENTRY_POSITION = (0, 200)
ENTRY_WALKMESH = 0
ENTRY_CAMERA_DIRECTION = 4
ENTRY_ACTOR_DIRECTION = 4
ENTRY_TRIANGLE = 16
ENTRY_SOURCE = bytes.fromhex("00 00 C8 00 00 FF FF")
ENTRY_PLAYABLE = bytes.fromhex("00 00 C8 00 00 04 04")

GLOBAL_ENTITY = 0
GLOBAL_INIT_PC = 0x000F
GLOBAL_INIT_BODY = bytes.fromhex(
    "BC 2A A0 FF 80 1E 80 00 83 00"
)
PARTY_ENTITIES = (1, 2, 3)
PARTY_INIT_PCS = (0x0157, 0x016A, 0x0191)
PARTY_UPDATE_PCS = (0x015F, 0x0172, 0x0199)
PARTY_SOURCE_OPERANDS = (0x8000, 0x8001, 0x8002)

# Model 2 is the complete examination bed and node 21 instantiates it after
# the nineteen-row ATEL boundary.  Retiring every story entity therefore
# cannot remove or reinterpret the bed.
BED_MODEL_INDEX = 2
BED_HEADER_NODE = 21
BED_MODEL_IDENTITY = (
    2_408,
    "dde8e7dda4546b058ea5e5f39b9be8c769d18f87546a32f80f68f476454731a4",
)
BED_HEADER_RECORD = bytes.fromhex(
    "10 00 00 00 00 04 00 00 00 00 00 00 00 00 02 00"
)

# Source e17 is the room's only physical threshold.  E18 owns its exact
# model-backed leaf animation.  The appended foundation intentionally matches
# the already-audited field-550 carrier layout so the campaign's later
# ghost-target/round-seal split can consume the same collision contract.
RETURN_CONTROLLER = 17
RETURN_CONTROLLER_POSITION = (0, 250)
RETURN_CONTROLLER_TRIANGLE = 34
RETURN_CONTROLLER_TRIANGLES = (16, 34, 35)
RETURN_CONTROLLER_SOURCE_INIT_PC = 0x0649
RETURN_CONTROLLER_SOURCE_ACTION_PC = 0x065C
RETURN_CONTROLLER_SOURCE_DESTINATION = (353, 1)
RETURN_CONTROLLER_SOURCE_ACTION = bytes.fromhex(
    "FE 54 74 77 80 09 12 C4 98 61 81 01 80 00"
)
RETURN_HELPER = 18
RETURN_HELPER_INIT_PC = 0x066A
RETURN_HELPER_SCRIPT_INDEX = 4
RETURN_HELPER_PC = 0x066E
RETURN_HELPER_BODY = bytes.fromhex(
    "35 0E 04 00 00 40 02 0E 04 1E 00 43 8B 06 FE 1B "
    "FF FF 00 00 26 00 80 3C 0E 04 01 74 06 00"
)
RETURN_PLAYER_SCRIPT = 4
RETURN_FIELD = 621
RETURN_PARAMETER = 4

DOOR_ENDPOINT_ID = "intake_medical_examination.examination"
DOOR_SEAL_RADIUS = 0x0E
DOOR_INTERACTION_HALF_WIDTH = 0x18
DOOR_INTERACTION_HALF_DEPTH = 0x08
DOOR_ACTION_HALF_DEPTH = 0x10
DOOR_CLOSED_SIDE_PROBE = ENTRY_POSITION
DOOR_OPEN_SIDE_PROBE = (0, 300)
IMMOVABLE_OPCODE = bytes.fromhex("F8 00 10 00")
IMMOVABLE_PRECEDES_STOP = False

SHARED_STOP_PC = 0x068C
RETURN_CONTROLLER_INIT_PC = 0x068D
RETURN_CONTROLLER_ACTION_PC = 0x06A7
RETURN_CONTROLLER_INIT_BODY = bytes.fromhex(
    "BC 19 00 00 FA 00 C0 F8 00 00 20 F8 03 04 00 "
    "18 18 08 1E 00 00 F8 00 10 00 00"
)
RETURN_ACTION = (
    b"\xFE\x54\x74\x77\x80"
    + b"\x09" + bytes((RETURN_HELPER, 0xC4))
    + surface._change_field(RETURN_FIELD, RETURN_PARAMETER)
    + b"\x00"
)
RETURN_ROUTE = (
    RETURN_CONTROLLER,
    RETURN_CONTROLLER_ACTION_PC,
    RETURN_HELPER,
    RETURN_PLAYER_SCRIPT,
    RETURN_FIELD,
    RETURN_PARAMETER,
)

# These are the only source routines retained before the fresh return
# controller is installed.  All other retail NPC, doctor, dialogue, automatic,
# story-transition, and progression slots point to one appended STOP.
RETAINED_SOURCE_SLOTS = frozenset(
    {
        (GLOBAL_ENTITY, 0),
        *((entity, slot) for entity in PARTY_ENTITIES for slot in (0, 1)),
        (RETURN_HELPER, 0),
        (RETURN_HELPER, RETURN_HELPER_SCRIPT_INDEX),
    }
)
FINAL_ACTIVE_SLOTS = frozenset(
    {
        *RETAINED_SOURCE_SLOTS,
        (RETURN_CONTROLLER, 0),
        (RETURN_CONTROLLER, 2),
    }
)
RETIRED_NPC_ENTITIES = (13, 14, 15, 16)
DOCTOR_ENTITY = 16

SOURCE_ENCOUNTER_WEIGHTS = (1, 1, 1, 1, 1, 1) + (0,) * 10
FINAL_ENCOUNTER_IDENTITY = (
    528,
    "48018da2ff103e2890c170b83d4fbb677011e085587dfe1bc4fbcea3f246ce12",
)
FINAL_SCRIPT_IDENTITY = (
    3_065,
    "ae019801478e5acbc2eeae43d4131a9fdea60003304b0b2add50999caf886a0c",
)
FINAL_DIALOGUE_IDENTITY = SOURCE_DIALOGUE_IDENTITY
FINAL_BUNDLE_IDENTITY = (
    83_428,
    "bd594bdef941a479283b76f212294e05007e0af8e3b9248a7a5eb3edb5fcecbc",
)
FINAL_HEADER_IDENTITY = (
    928,
    "1d4a041a762ad8cfe1bf28cdf3fcdc8825b068756f632e3f95e611072640ee7e",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _identity(data: bytes) -> tuple[int, str]:
    return len(data), _sha256(data)


def _assert_source_identity(bundle: bytes, graphics: bytes) -> None:
    if _identity(bundle) != SOURCE_BUNDLE_IDENTITY:
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 empty-clinic source field 352 bundle changed"
        )
    if _identity(graphics) != SOURCE_GRAPHICS_IDENTITY:
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 empty-clinic source field 352 graphics changed"
        )

    parsed = parse_field(bundle)
    component_identities = tuple(_identity(part.data) for part in parsed.parts)
    if component_identities != SOURCE_COMPONENT_IDENTITIES:
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 empty-clinic source components changed"
        )
    if _identity(parsed.header) != SOURCE_HEADER_IDENTITY:
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 empty-clinic source header changed"
        )

    editor = ScriptEditor(parsed.parts[surface.SCRIPT_INDEX].data)
    actor_count = struct.unpack_from("<H", parsed.header, 0x18C)[0]
    if (
        editor.entity_count != SOURCE_ENTITY_COUNT
        or editor.bytecode_size != SOURCE_BYTECODE_SIZE
        or actor_count != SOURCE_HEADER_ACTOR_COUNT
        or len(parsed.header) != 0x190 + actor_count * 16
    ):
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 empty-clinic entity/header boundary changed"
        )

    model_entries = surface.mass_driver._indexed_bundle_entries(
        parsed.parts[surface.mass_driver.MODEL_INDEX].data
    )
    bed_offset = 0x190 + BED_HEADER_NODE * 16
    if (
        len(model_entries) != 15
        or _identity(model_entries[BED_MODEL_INDEX]) != BED_MODEL_IDENTITY
        or parsed.header[bed_offset:bed_offset + 16] != BED_HEADER_RECORD
        or BED_HEADER_NODE < SOURCE_ENTITY_COUNT
    ):
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 field-352 examination bed identity changed"
        )


def _verify_source_script_foundation(script: bytes) -> None:
    editor = ScriptEditor(script)
    if (
        editor.entity_count != SOURCE_ENTITY_COUNT
        or editor.bytecode_size != SOURCE_BYTECODE_SIZE
        or editor.get_script_pointer(GLOBAL_ENTITY, 0) != GLOBAL_INIT_PC
        or editor.bytecode[
            GLOBAL_INIT_PC:GLOBAL_INIT_PC + len(GLOBAL_INIT_BODY)
        ] != GLOBAL_INIT_BODY
        or tuple(
            editor.get_script_pointer(entity, 0) for entity in PARTY_ENTITIES
        ) != PARTY_INIT_PCS
        or tuple(
            editor.get_script_pointer(entity, 1) for entity in PARTY_ENTITIES
        ) != PARTY_UPDATE_PCS
        or editor.get_script_pointer(RETURN_CONTROLLER, 0)
        != RETURN_CONTROLLER_SOURCE_INIT_PC
        or editor.get_script_pointer(RETURN_CONTROLLER, 2)
        != RETURN_CONTROLLER_SOURCE_ACTION_PC
        or editor.bytecode[
            RETURN_CONTROLLER_SOURCE_ACTION_PC:
            RETURN_CONTROLLER_SOURCE_ACTION_PC
            + len(RETURN_CONTROLLER_SOURCE_ACTION)
        ] != RETURN_CONTROLLER_SOURCE_ACTION
        or editor.get_script_pointer(RETURN_HELPER, 0) != RETURN_HELPER_INIT_PC
        or editor.get_script_pointer(
            RETURN_HELPER,
            RETURN_HELPER_SCRIPT_INDEX,
        ) != RETURN_HELPER_PC
        or editor.bytecode[
            RETURN_HELPER_PC:RETURN_HELPER_PC + len(RETURN_HELPER_BODY)
        ] != RETURN_HELPER_BODY
    ):
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 field-352 safe initializer/party/door foundation changed"
        )


def load_empty_clinic567_source(
    donor_disc: Path | str,
) -> tuple[bytes, bytes]:
    """Extract and verify the Disc 1 field-352 infirmary pair."""

    image = Mode2Image(donor_disc)
    entries = image.read_index()
    first = image.read_directories()[FIELD_DIRECTORY].first_file
    local = FIRST_FIELD_LOCAL_FILE + 2 * SOURCE_SCENE
    bundle_index = directory_file_fat_index(first, local)
    graphics_index = directory_file_fat_index(first, local + 1)
    actual_ids = (bundle_index + 5, graphics_index + 5)
    if actual_ids != EMPTY_CLINIC567_SOURCE_IDS:
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 field 352 resolved to canonical resources "
            f"{actual_ids}, expected {EMPTY_CLINIC567_SOURCE_IDS}"
        )
    bundle = image.extract_entry(entries[bundle_index])
    graphics = image.extract_entry(entries[graphics_index])
    _assert_source_identity(bundle, graphics)
    return bundle, graphics


def verify_empty_clinic567_targets_are_dummy(source_disc: Path | str) -> None:
    """Refuse to replace logical field 567 unless both Disc 2 slots are dummies."""

    expected = {
        canonical_id: (len(surface.DONOR_DUMMY), surface.DONOR_DUMMY_SHA256)
        for canonical_id in EMPTY_CLINIC567_TARGET_IDS
    }
    resources = surface._load_canonical_resources(source_disc, expected)
    if set(resources) != set(EMPTY_CLINIC567_TARGET_IDS) or any(
        resources[canonical_id] != surface.DONOR_DUMMY
        for canonical_id in EMPTY_CLINIC567_TARGET_IDS
    ):
        raise surface.SurfaceSoylentBuildError(
            "Disc 2 field-567 empty-clinic target is not the checked CDMAKE dummy"
        )


def _patch_entry_and_party(script: bytes) -> bytes:
    script = surface._patch_bytecode(
        script,
        1 + 7 * ENTRY_PARAMETER,
        ENTRY_SOURCE,
        ENTRY_PLAYABLE,
    )
    return surface._patch_donor_party(
        script,
        PARTY_INIT_PCS,
        PARTY_SOURCE_OPERANDS,
    )


def _install_empty_room_scripts(script: bytes) -> bytes:
    """Retire every retail event and install the sole reciprocal door."""

    editor = ScriptEditor(script)
    stop_pc = editor.append_raw_routine(b"\x00")
    if stop_pc != SHARED_STOP_PC:
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-clinic shared STOP moved"
        )

    for entity in range(editor.entity_count):
        for script_index in range(32):
            if (entity, script_index) not in RETAINED_SOURCE_SLOTS:
                editor.set_script_pointer(entity, script_index, stop_pc)

    init_pc = editor.append_and_repoint(
        RETURN_CONTROLLER,
        0,
        RETURN_CONTROLLER_INIT_BODY,
    )
    action_pc = editor.append_and_repoint(
        RETURN_CONTROLLER,
        2,
        RETURN_ACTION,
    )
    if (init_pc, action_pc) != (
        RETURN_CONTROLLER_INIT_PC,
        RETURN_CONTROLLER_ACTION_PC,
    ):
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-clinic return-door routines moved"
        )

    for entity in range(editor.entity_count):
        for script_index in range(32):
            if (entity, script_index) not in FINAL_ACTIVE_SLOTS and (
                editor.get_script_pointer(entity, script_index) != stop_pc
            ):
                raise surface.SurfaceSoylentBuildError(
                    f"Field 567 empty-clinic e{entity}:s{script_index} "
                    "escaped retirement"
                )
    return editor.to_bytes()


def _disable_random_encounters(encounters: bytes) -> bytes:
    table = EncounterTable(encounters)
    if table.weights != SOURCE_ENCOUNTER_WEIGHTS:
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 field-352 random-encounter weights changed"
        )
    formations = encounters[:-16]
    for formation in range(16):
        table.set_weight(formation, 0)
    disabled = table.to_bytes()
    if (
        disabled[:-16] != formations
        or table.weights != (0,) * 16
        or _identity(disabled) != FINAL_ENCOUNTER_IDENTITY
    ):
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-clinic encounter suppression changed a formation"
        )
    return disabled


def prepare_empty_clinic567(
    source_bundle: bytes,
    graphics: bytes,
) -> surface.PreparedDonorField:
    """Build the deterministic exploration-only field-352 clone for field 567."""

    _assert_source_identity(source_bundle, graphics)
    parsed = parse_field(source_bundle)
    components = [part.data for part in parsed.parts]
    source_script = components[surface.SCRIPT_INDEX]
    _verify_source_script_foundation(source_script)

    triangles = surface._walkmesh_layer(components[1], ENTRY_WALKMESH)
    entry_hits = tuple(
        index
        for index, triangle in enumerate(triangles)
        if surface._point_inside_triangle(ENTRY_POSITION, triangle)
    )
    if entry_hits != (ENTRY_TRIANGLE,):
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-clinic entry left audited triangle 16: "
            f"{entry_hits}"
        )
    if (
        RETURN_CONTROLLER_TRIANGLE >= len(triangles)
        or not surface._point_inside_triangle(
            RETURN_CONTROLLER_POSITION,
            triangles[RETURN_CONTROLLER_TRIANGLE],
        )
    ):
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-clinic door left audited triangle 34"
        )

    script = _patch_entry_and_party(source_script)
    script = _install_empty_room_scripts(script)
    encounters = _disable_random_encounters(components[6])
    if _identity(script) != FINAL_SCRIPT_IDENTITY:
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-clinic final ATEL identity changed"
        )

    components[surface.SCRIPT_INDEX] = script
    components[6] = encounters
    bundle = build_field_preserving(
        source_bundle,
        components,
        (surface.SCRIPT_INDEX, 6),
        compact_changed=True,
    )
    if _identity(bundle) != FINAL_BUNDLE_IDENTITY:
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-clinic packed bundle identity changed"
        )

    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-clinic packed output failed decoded-stream round trip"
        )
    if _identity(reparsed.header) != FINAL_HEADER_IDENTITY:
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-clinic packed header identity changed"
        )
    if _identity(components[7]) != FINAL_DIALOGUE_IDENTITY:
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-clinic dormant dialogue inventory changed"
        )

    return surface.PreparedDonorField(
        EMPTY_CLINIC567_IDENTITY,
        (
            "empty Ethos medical room; examination bed and environment "
            "preserved; one animated reciprocal return to field 621/p4; "
            "all retail NPC, dialogue, automatic, battle, and progression "
            "events unreachable; random encounters disabled"
        ),
        source_bundle,
        graphics,
        reparsed.header,
        tuple(components),
        bundle,
        ((ENTRY_PARAMETER, ENTRY_TRIANGLE),),
    )


def prepare_empty_clinic567_from_discs(
    source_disc: Path | str,
    donor_disc: Path | str,
) -> surface.PreparedDonorField:
    """Verify Disc 2 targets, then prepare the Disc 1 field-352 clone."""

    verify_empty_clinic567_targets_are_dummy(source_disc)
    return prepare_empty_clinic567(
        *load_empty_clinic567_source(donor_disc)
    )


__all__ = [
    "BED_HEADER_NODE",
    "BED_HEADER_RECORD",
    "BED_MODEL_IDENTITY",
    "BED_MODEL_INDEX",
    "DONOR567_IDENTITY",
    "DOCTOR_ENTITY",
    "DOOR_ACTION_HALF_DEPTH",
    "DOOR_CLOSED_SIDE_PROBE",
    "DOOR_ENDPOINT_ID",
    "DOOR_INTERACTION_HALF_DEPTH",
    "DOOR_INTERACTION_HALF_WIDTH",
    "DOOR_OPEN_SIDE_PROBE",
    "DOOR_SEAL_RADIUS",
    "EMPTY_CLINIC567_IDENTITY",
    "EMPTY_CLINIC567_SOURCE_IDS",
    "EMPTY_CLINIC567_TARGET_IDS",
    "ENTRY_ACTOR_DIRECTION",
    "ENTRY_CAMERA_DIRECTION",
    "ENTRY_PARAMETER",
    "ENTRY_PLAYABLE",
    "ENTRY_POSITION",
    "ENTRY_SOURCE",
    "ENTRY_TRIANGLE",
    "ENTRY_WALKMESH",
    "FINAL_ACTIVE_SLOTS",
    "FINAL_BUNDLE_IDENTITY",
    "FINAL_DIALOGUE_IDENTITY",
    "FINAL_ENCOUNTER_IDENTITY",
    "FINAL_HEADER_IDENTITY",
    "FINAL_SCRIPT_IDENTITY",
    "IMMOVABLE_OPCODE",
    "IMMOVABLE_PRECEDES_STOP",
    "GLOBAL_INIT_BODY",
    "GLOBAL_INIT_PC",
    "PARTY_ENTITIES",
    "PARTY_INIT_PCS",
    "PARTY_UPDATE_PCS",
    "RETAINED_SOURCE_SLOTS",
    "RETIRED_NPC_ENTITIES",
    "RETURN_ACTION",
    "RETURN_CONTROLLER",
    "RETURN_CONTROLLER_ACTION_PC",
    "RETURN_CONTROLLER_INIT_BODY",
    "RETURN_CONTROLLER_INIT_PC",
    "RETURN_CONTROLLER_POSITION",
    "RETURN_CONTROLLER_SOURCE_ACTION",
    "RETURN_CONTROLLER_SOURCE_ACTION_PC",
    "RETURN_CONTROLLER_SOURCE_DESTINATION",
    "RETURN_CONTROLLER_SOURCE_INIT_PC",
    "RETURN_CONTROLLER_TRIANGLE",
    "RETURN_CONTROLLER_TRIANGLES",
    "RETURN_FIELD",
    "RETURN_HELPER",
    "RETURN_HELPER_BODY",
    "RETURN_HELPER_INIT_PC",
    "RETURN_HELPER_PC",
    "RETURN_HELPER_SCRIPT_INDEX",
    "RETURN_PARAMETER",
    "RETURN_PLAYER_SCRIPT",
    "RETURN_ROUTE",
    "SHARED_STOP_PC",
    "SOURCE_BUNDLE_ID",
    "SOURCE_BUNDLE_IDENTITY",
    "SOURCE_BYTECODE_SIZE",
    "SOURCE_COMPONENT_IDENTITIES",
    "SOURCE_DIALOGUE_IDENTITY",
    "SOURCE_ENTITY_COUNT",
    "SOURCE_ENCOUNTER_WEIGHTS",
    "SOURCE_GRAPHICS_ID",
    "SOURCE_GRAPHICS_IDENTITY",
    "SOURCE_HEADER_ACTOR_COUNT",
    "SOURCE_HEADER_IDENTITY",
    "SOURCE_SCENE",
    "SOURCE_SCRIPT_IDENTITY",
    "TARGET_BUNDLE_ID",
    "TARGET_GRAPHICS_ID",
    "load_empty_clinic567_source",
    "prepare_empty_clinic567",
    "prepare_empty_clinic567_from_discs",
    "verify_empty_clinic567_targets_are_dummy",
]
