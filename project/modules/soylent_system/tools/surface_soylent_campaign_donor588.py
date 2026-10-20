#!/usr/bin/env python3
"""Transplant Disc 1 field 550 into logical field 588.

The donor is the bright Etrenank diagnostic scanner room.  Its baked scanner,
party actors, and native model-backed south door survive.  Retail scanner,
item, NPC/story progression, and random encounters do not.  The campaign
layer later installs the Quarantine-keycard action on scanner carrier e4.
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


SCENE = 588
SOURCE_SCENE = 550
TARGET_BUNDLE_ID = 1782
TARGET_GRAPHICS_ID = 1783
# Disc 1 has five more leading canonical resources than Disc 2.  The checked
# reference files are named 1706/1707; their Disc-1 canonical IDs are below.
SOURCE_BUNDLE_ID = 1711
SOURCE_GRAPHICS_ID = 1712

SOURCE_NATURAL_IDENTITY = surface.DONOR_BY_SCENE[SOURCE_SCENE]
DONOR588_IDENTITY = surface.SourceIdentity(
    SCENE,
    TARGET_BUNDLE_ID,
    TARGET_GRAPHICS_ID,
    SOURCE_NATURAL_IDENTITY.bundle_size,
    SOURCE_NATURAL_IDENTITY.bundle_sha256,
    SOURCE_NATURAL_IDENTITY.graphics_size,
    SOURCE_NATURAL_IDENTITY.graphics_sha256,
    SOURCE_NATURAL_IDENTITY.script_size,
    SOURCE_NATURAL_IDENTITY.script_sha256,
    SOURCE_NATURAL_IDENTITY.header_size,
    SOURCE_NATURAL_IDENTITY.header_sha256,
)
DONOR588_TARGET_IDS = (TARGET_BUNDLE_ID, TARGET_GRAPHICS_ID)
DONOR588_SOURCE_IDS = (SOURCE_BUNDLE_ID, SOURCE_GRAPHICS_ID)

SOURCE_COMPONENT_IDENTITIES = (
    (4, "df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119"),
    (2864, "bd0bc67697da4c5fcaefb5a0477d7bc58d6a26cb22b34db959a3c5b6a03cccc8"),
    (11932, "14568cfc1681e203c7fd70ffa842829c360124c1d5e7e20ed46bb875c549a099"),
    (6724, "d886f360c112ac59247f3439c6dc2a800840cd153bbeed2e296b1f2db39da004"),
    (11684, "0762607a4654cf1c8c373d21be79a48656cd203001891ee988a65568311464e0"),
    (4572, "7fa1515799718f45bfad14bd206285cc122940d467dc0b4c5f5d442b6f05ed7c"),
    (528, "54325752ea0b7e2c679501792acf113e86495454e3a238acdaf63eaa7db06e16"),
    (355, "2d11390dc5fcdfe0520d948618474e1b174dc7c852a68a4bdb4ad71630defaae"),
    (0, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
)
SOURCE_ENTITY_COUNT = 29
SOURCE_HEADER_ACTOR_COUNT = 35
SOURCE_BYTECODE_SIZE = 0x0A18

ENTRY_PARAMETER = 0
ENTRY_POSITION = (-85, -230)
ENTRY_WALKMESH = 0
ENTRY_CAMERA_DIRECTION = 7
ENTRY_ACTOR_DIRECTION = 7
ENTRY_TRIANGLE = 14
ENTRY_SOURCE = struct.pack("<hhBBB", -85, -230, 0, 0xFF, 0xFF)
ENTRY_PLAYABLE = struct.pack(
    "<hhBBB",
    *ENTRY_POSITION,
    ENTRY_WALKMESH,
    ENTRY_CAMERA_DIRECTION,
    ENTRY_ACTOR_DIRECTION,
)
PARTY_INIT_PCS = (0x01CE, 0x01F3, 0x01FE)
PARTY_SOURCE_OPERANDS = (0x003E, 0x0040, 0x0042)

# e4 is the model-less X carrier at the visible scanner frontage.
CONSOLE_ENTITY = 4
CONSOLE_POSITION = (190, 190)
CONSOLE_TRIANGLE = 34
CONSOLE_INTERACTION_HALF_WIDTH = 0x1E
CONSOLE_INTERACTION_HALF_DEPTH = 0x1E
CONSOLE_NATIVE_INIT_PC = 0x0209
CONSOLE_NATIVE_INIT_STOP_PC = 0x0236
CONSOLE_NATIVE_ACTION_PC = 0x0237
CONSOLE_NATIVE_ACTION_STOP_PC = 0x0453
CONSOLE_NATIVE_INIT = bytes.fromhex(
    "BC 19 BE 00 BE 00 C0 F8 00 00 20 F8 03 04 00 18 1E 1E 1E 00 "
    "36 00 04 36 02 04 36 04 04 37 06 04 36 08 04 36 0A 04 "
    "37 0C 04 36 0E 04 00"
)
CONSOLE_HEADER_RECORD = (480, 0, 0, 0, 0, 0, 0, 0)

# Exact baked white scanner shell records.  These are static nodes rather
# than scripted actors, so retiring retail scripts cannot remove them.
VISIBLE_SCANNER_STATIC_NODES = (29, 30, 31, 32, 33, 34)
VISIBLE_COMPUTER_STATIC_NODES = VISIBLE_SCANNER_STATIC_NODES
# Campaign door clearance extends the 29-entity ATEL table with its seal at
# header index 29, shifting every baked source node by exactly one.
CAMPAIGN_VISIBLE_SCANNER_STATIC_NODES = (30, 31, 32, 33, 34, 35)
CAMPAIGN_VISIBLE_COMPUTER_STATIC_NODES = CAMPAIGN_VISIBLE_SCANNER_STATIC_NODES
STATIC_NODE_RANGE = VISIBLE_SCANNER_STATIC_NODES
STATIC_NODE_MODELS = (0, 3, 4, 5, 6, 7)
VISIBLE_SCANNER_STATIC_RECORDS = (
    (16, 0, 3584, 0, 0, 0, 0, 0),
    (16, 0, 3584, 0, 0, 0, 0, 3),
    (16, 0, 3584, 0, 0, 0, 0, 4),
    (0, 0, 3584, 0, 0, 0, 0, 5),
    (16, 0, 3584, 0, 0, 0, 0, 6),
    (16, 0, 3584, 0, 0, 0, 0, 7),
)
VISIBLE_COMPUTER_STATIC_RECORDS = VISIBLE_SCANNER_STATIC_RECORDS

# e5..e16 are initially hidden scanner indicators/apparatus.  Their harmless
# hide/disable init is preserved; all later behaviors are parked.
SCANNER_INDICATOR_ENTITIES = tuple(range(5, 13))
SCANNER_APPARATUS_ENTITIES = (13, 14, 15, 16)
SCANNER_FIXTURE_ENTITIES = SCANNER_INDICATOR_ENTITIES + SCANNER_APPARATUS_ENTITIES
SCANNER_FIXTURE_INIT_PCS = (
    0x0454, 0x045A, 0x0460, 0x0466, 0x046C, 0x0472,
    0x0478, 0x047E, 0x0484, 0x050E, 0x0598, 0x0622,
)
SCANNER_FIXTURE_INIT_BODY = bytes.fromhex("BC 23 2A 00")

# Native south door and its model-backed e18 leaf.
RETURN_CONTROLLER = 17
RETURN_CONTROLLER_INIT_PC = 0x0628
RETURN_CONTROLLER_INIT_COMMAND_END_PC = 0x063C
RETURN_CONTROLLER_INIT_STOP_PC = 0x063C
RETURN_CONTROLLER_SECOND_STOP_PC = 0x063D
RETURN_CONTROLLER_ACTION_PC = 0x063E
RETURN_ACTION_STOP_PC = 0x064F
RETURN_HELPER = 18
RETURN_HELPER_SCRIPT_INDEX = 4
RETURN_HELPER_PC = 0x0656
RETURN_HELPER_BODY = bytes.fromhex("05 C2 00 00")
RETURN_HELPER_HEADER_RECORD = (656, 0, 3584, 0, 0, 0, 0, 1)
RETURN_PLAYER_ENTITY = 1
RETURN_PLAYER_SCRIPT_INDEX = 4
RETURN_PLAYER_PC = 0x01D9
RETURN_PLAYER_BODY = bytes.fromhex("1F 10 4A F9 FF CF FE C0 00")
RETURN_TRANSITION_PC = 0x0649
RETURN_SOURCE_FIELD = 551
RETURN_SOURCE_PARAMETER = 1
RETURN_FIELD = 621
RETURN_PARAMETER = 5
RETURN_SOURCE_ACTION = (
    bytes.fromhex("FE 54 09 12 24 07 01 24 26 0A 80")
    + surface._change_field(RETURN_SOURCE_FIELD, RETURN_SOURCE_PARAMETER)
    + b"\x5B"
)
RETURN_ACTION = (
    bytes.fromhex("FE 54 09 12 24 07 01 24 26 0A 80")
    + surface._change_field(RETURN_FIELD, RETURN_PARAMETER)
    + b"\x5B"
)
RETURN_CONTROLLER_NATIVE_INIT = bytes.fromhex(
    "BC 19 D3 FF F6 FE C0 F8 00 00 20 F8 03 04 00 18 0A 0A 1E 00"
)
RETURN_CONTROLLER_HEADER_RECORD = CONSOLE_HEADER_RECORD
RETURN_CONTROLLER_POSITION = (-45, -266)
RETURN_CONTROLLER_TRIANGLE = 28
RETURN_INTERACTION_HALF_WIDTH = 0x0A
RETURN_INTERACTION_HALF_DEPTH = 0x0A
# The native 0x0A shell already reaches the first 44-unit round-seal contact
# on this diagonal, while a wider shell would overlap p0 and invite an
# immediate bounce.  Campaign ghosting removes the native facing requirement.
RETURN_ACTION_HALF_WIDTH = RETURN_INTERACTION_HALF_WIDTH
RETURN_ACTION_HALF_DEPTH = RETURN_INTERACTION_HALF_DEPTH
RETURN_ACTION_REQUIRES_FACING = False
RETURN_CUT_TRIANGLES = (14, 0, 1, 28, 29)
RETURN_CLOSED_SIDE_PROBE = ENTRY_POSITION
RETURN_OPEN_SIDE_PROBE = (-7, -305)
RETURN_CROSSING_WAYPOINT = RETURN_OPEN_SIDE_PROBE
RETURN_CROSSING_TRIANGLE = 29
IMMOVABLE_OPCODE = bytes.fromhex("F8 00 10 00")
IMMOVABLE_PRECEDES_STOP = True
HARDENED_INIT_PC = SOURCE_BYTECODE_SIZE
HARDENED_INIT = RETURN_CONTROLLER_NATIVE_INIT + IMMOVABLE_OPCODE + b"\x00"

SHARED_STOP_PC = 0x01BE
RETIRED_STORY_ENTITIES = tuple(range(19, 29))
RETIRED_ENTITIES = RETIRED_STORY_ENTITIES
RETIRED_ENTITY_SLOTS_ALL_STOP = RETIRED_STORY_ENTITIES
PRESERVED_SCRIPT_SLOTS = frozenset(
    {
        (0, 0), (0, 1),
        (1, 0), (1, 1), (1, RETURN_PLAYER_SCRIPT_INDEX),
        (2, 0), (2, 1),
        (3, 0), (3, 1),
        (CONSOLE_ENTITY, 0),
        (RETURN_CONTROLLER, 0), (RETURN_CONTROLLER, 2),
        (RETURN_HELPER, 0), (RETURN_HELPER, RETURN_HELPER_SCRIPT_INDEX),
    }
    | {(entity, 0) for entity in SCANNER_FIXTURE_ENTITIES}
)
RETIRED_SCRIPT_SLOTS = tuple(
    (entity, slot)
    for entity in range(SOURCE_ENTITY_COUNT)
    for slot in range(32)
    if (entity, slot) not in PRESERVED_SCRIPT_SLOTS
)

SOURCE_ENCOUNTER_WEIGHTS = (0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
FINAL_ENCOUNTER_WEIGHTS = (0,) * 16

FINAL_SCRIPT_IDENTITY = (
    4597,
    "bc808299bf6b2156b826edfe76a4fc59f908aa820cc69bc5ebba9c3074e98b15",
)
FINAL_ENCOUNTER_IDENTITY = (
    528,
    "616c9c6b55c6ccbbb0163a34345508c3142f44b60b3bfa926d720bf547d6fd7e",
)
FINAL_BUNDLE_IDENTITY = (
    24192,
    "b4422032e7dd9b34d43fd94e90ac93189510546f55c72d74c676e5ad08ffa96a",
)
FINAL_HEADER_IDENTITY = (
    960,
    "a27e4ff0384f88268ff0018c77843915de747f559dc571e0cef68539aed189c4",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _identity(data: bytes) -> tuple[int, str]:
    return len(data), _sha256(data)


def _assert_source_identity(bundle: bytes, graphics: bytes) -> None:
    identity = DONOR588_IDENTITY
    if _identity(bundle) != (identity.bundle_size, identity.bundle_sha256):
        raise surface.SurfaceSoylentBuildError("Disc 1 donor field 550 bundle changed")
    if _identity(graphics) != (identity.graphics_size, identity.graphics_sha256):
        raise surface.SurfaceSoylentBuildError("Disc 1 donor field 550 graphics changed")
    parsed = parse_field(bundle)
    if tuple(_identity(part.data) for part in parsed.parts) != SOURCE_COMPONENT_IDENTITIES:
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 donor field 550 component identities changed"
        )
    if _identity(parsed.header) != (identity.header_size, identity.header_sha256):
        raise surface.SurfaceSoylentBuildError("Disc 1 donor field 550 header changed")
    editor = ScriptEditor(parsed.parts[surface.SCRIPT_INDEX].data)
    actor_count = struct.unpack_from("<H", parsed.header, 0x18C)[0]
    if (
        editor.entity_count != SOURCE_ENTITY_COUNT
        or actor_count != SOURCE_HEADER_ACTOR_COUNT
        or editor.bytecode_size != SOURCE_BYTECODE_SIZE
    ):
        raise surface.SurfaceSoylentBuildError("Disc 1 donor field 550 entity layout changed")


def load_donor588_source(donor_disc: Path | str) -> tuple[bytes, bytes]:
    """Extract and verify the natural physical field-550 pair from Disc 1."""
    image = Mode2Image(donor_disc)
    entries = image.read_index()
    first = image.read_directories()[FIELD_DIRECTORY].first_file
    local = FIRST_FIELD_LOCAL_FILE + 2 * SOURCE_SCENE
    bundle_index = directory_file_fat_index(first, local)
    graphics_index = directory_file_fat_index(first, local + 1)
    actual_ids = (bundle_index + 5, graphics_index + 5)
    if actual_ids != DONOR588_SOURCE_IDS:
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 field 550 resolved to canonical resources "
            f"{actual_ids}, expected {DONOR588_SOURCE_IDS}"
        )
    bundle = image.extract_entry(entries[bundle_index])
    graphics = image.extract_entry(entries[graphics_index])
    _assert_source_identity(bundle, graphics)
    return bundle, graphics


def verify_donor588_targets_are_dummy(source_disc: Path | str) -> None:
    """Refuse to overwrite logical field 588 unless both targets are dummies."""
    expected = {
        canonical_id: (len(surface.DONOR_DUMMY), surface.DONOR_DUMMY_SHA256)
        for canonical_id in DONOR588_TARGET_IDS
    }
    resources = surface._load_canonical_resources(source_disc, expected)
    if set(resources) != set(DONOR588_TARGET_IDS) or any(
        resources[canonical_id] != surface.DONOR_DUMMY
        for canonical_id in DONOR588_TARGET_IDS
    ):
        raise surface.SurfaceSoylentBuildError(
            "Disc 2 field-588 donor target is not the checked CDMAKE dummy"
        )


def _audit_scanner_header(header: bytes) -> None:
    if struct.unpack_from("<H", header, 0x18C)[0] != SOURCE_HEADER_ACTOR_COUNT:
        raise surface.SurfaceSoylentBuildError("Field 550 diagnostic-room actor count changed")
    records = tuple(
        struct.unpack_from("<8H", header, 0x190 + node * 16)
        for node in VISIBLE_SCANNER_STATIC_NODES
    )
    if records != VISIBLE_SCANNER_STATIC_RECORDS:
        raise surface.SurfaceSoylentBuildError(
            "Field 550 baked diagnostic scanner models changed"
        )
    if (
        struct.unpack_from("<8H", header, 0x190 + CONSOLE_ENTITY * 16)
        != CONSOLE_HEADER_RECORD
        or struct.unpack_from(
            "<8H", header, 0x190 + RETURN_CONTROLLER * 16
        ) != RETURN_CONTROLLER_HEADER_RECORD
        or struct.unpack_from("<8H", header, 0x190 + RETURN_HELPER * 16)
        != RETURN_HELPER_HEADER_RECORD
    ):
        raise surface.SurfaceSoylentBuildError(
            "Field 550 scanner carrier or model-backed return leaf changed"
        )


def _audit_native_scripts(editor: ScriptEditor) -> None:
    if (
        editor.get_script_pointer(CONSOLE_ENTITY, 0) != CONSOLE_NATIVE_INIT_PC
        or editor.bytecode[CONSOLE_NATIVE_INIT_PC:CONSOLE_NATIVE_INIT_STOP_PC]
        != CONSOLE_NATIVE_INIT
        or editor.bytecode[CONSOLE_NATIVE_INIT_STOP_PC] != 0
        or editor.get_script_pointer(CONSOLE_ENTITY, 2) != CONSOLE_NATIVE_ACTION_PC
        or editor.bytecode[CONSOLE_NATIVE_ACTION_STOP_PC] != 0
    ):
        raise surface.SurfaceSoylentBuildError("Field 550 native scanner carrier changed")
    for entity, pc in zip(SCANNER_FIXTURE_ENTITIES, SCANNER_FIXTURE_INIT_PCS, strict=True):
        if (
            editor.get_script_pointer(entity, 0) != pc
            or editor.bytecode[pc:pc + len(SCANNER_FIXTURE_INIT_BODY)]
            != SCANNER_FIXTURE_INIT_BODY
        ):
            raise surface.SurfaceSoylentBuildError(
                f"Field 550 scanner fixture e{entity} init changed"
            )
    if (
        editor.get_script_pointer(RETURN_CONTROLLER, 0) != RETURN_CONTROLLER_INIT_PC
        or editor.bytecode[
            RETURN_CONTROLLER_INIT_PC:RETURN_CONTROLLER_INIT_COMMAND_END_PC
        ] != RETURN_CONTROLLER_NATIVE_INIT
        or editor.bytecode[RETURN_CONTROLLER_INIT_STOP_PC] != 0
        or editor.bytecode[RETURN_CONTROLLER_SECOND_STOP_PC] != 0
        or editor.get_script_pointer(RETURN_CONTROLLER, 2) != RETURN_CONTROLLER_ACTION_PC
        or editor.bytecode[
            RETURN_CONTROLLER_ACTION_PC:RETURN_CONTROLLER_ACTION_PC + len(RETURN_ACTION)
        ] != RETURN_ACTION
        or editor.bytecode[RETURN_ACTION_STOP_PC] != 0
        or editor.get_script_pointer(RETURN_HELPER, RETURN_HELPER_SCRIPT_INDEX)
        != RETURN_HELPER_PC
        or editor.bytecode[RETURN_HELPER_PC:RETURN_HELPER_PC + len(RETURN_HELPER_BODY)]
        != RETURN_HELPER_BODY
        or editor.get_script_pointer(RETURN_PLAYER_ENTITY, RETURN_PLAYER_SCRIPT_INDEX)
        != RETURN_PLAYER_PC
        or editor.bytecode[RETURN_PLAYER_PC:RETURN_PLAYER_PC + len(RETURN_PLAYER_BODY)]
        != RETURN_PLAYER_BODY
    ):
        raise surface.SurfaceSoylentBuildError("Field 550 native animated return door changed")


def _prepare_script(source: bytes) -> bytes:
    script = surface._patch_bytecode(
        source, 1 + 7 * ENTRY_PARAMETER, ENTRY_SOURCE, ENTRY_PLAYABLE
    )
    script = surface._patch_donor_party(script, PARTY_INIT_PCS, PARTY_SOURCE_OPERANDS)
    script = surface._patch_bytecode(
        script, 0x015E, bytes.fromhex("66 01"), bytes.fromhex("60 01")
    )
    script = surface._patch_bytecode(
        script, 0x016C, bytes.fromhex("74 01"), bytes.fromhex("6E 01")
    )
    script = surface._patch_bytecode(
        script,
        RETURN_TRANSITION_PC,
        surface._change_field(RETURN_SOURCE_FIELD, RETURN_SOURCE_PARAMETER),
        surface._change_field(RETURN_FIELD, RETURN_PARAMETER),
    )
    editor = ScriptEditor(script)
    if (
        editor.entity_count != SOURCE_ENTITY_COUNT
        or editor.bytecode_size != SOURCE_BYTECODE_SIZE
        or editor.bytecode[SHARED_STOP_PC] != 0
    ):
        raise surface.SurfaceSoylentBuildError("Field 550 ATEL foundation changed")
    _audit_native_scripts(editor)
    for entity, slot in RETIRED_SCRIPT_SLOTS:
        editor.set_script_pointer(entity, slot, SHARED_STOP_PC)
    if editor.append_and_repoint(RETURN_CONTROLLER, 0, HARDENED_INIT) != HARDENED_INIT_PC:
        raise surface.SurfaceSoylentBuildError(
            "Field 588 hardened return-door initializer moved"
        )
    for entity in RETIRED_ENTITY_SLOTS_ALL_STOP:
        if any(editor.get_script_pointer(entity, slot) != SHARED_STOP_PC for slot in range(32)):
            raise surface.SurfaceSoylentBuildError(
                f"Field 588 retail story e{entity} became reachable"
            )
    if editor.get_script_pointer(CONSOLE_ENTITY, 2) != SHARED_STOP_PC:
        raise surface.SurfaceSoylentBuildError(
            "Field 588 retail scanner progression became reachable"
        )
    for entity in SCANNER_FIXTURE_ENTITIES:
        if any(
            editor.get_script_pointer(entity, slot) != SHARED_STOP_PC
            for slot in range(1, 32)
        ):
            raise surface.SurfaceSoylentBuildError(
                f"Field 588 scanner fixture e{entity} behavior became reachable"
            )
    return editor.to_bytes()


def _disable_encounters(source: bytes) -> bytes:
    table = EncounterTable(source)
    if table.weights != SOURCE_ENCOUNTER_WEIGHTS:
        raise surface.SurfaceSoylentBuildError("Field 550 source encounter weights changed")
    for index in range(16):
        table.set_weight(index, 0)
    result = table.to_bytes()
    if EncounterTable(result).weights != FINAL_ENCOUNTER_WEIGHTS:
        raise surface.SurfaceSoylentBuildError("Field 588 random encounters remained enabled")
    return result


def _assert_final_identity(
    label: str, data: bytes, expected: tuple[int, str] | None
) -> None:
    if expected is not None and _identity(data) != expected:
        raise surface.SurfaceSoylentBuildError(
            f"Field 588 final {label} identity changed: {_identity(data)}"
        )


def prepare_donor588(
    source_bundle: bytes, graphics: bytes
) -> surface.PreparedDonorField:
    """Build the deterministic bright diagnostic credential-room transplant."""
    _assert_source_identity(source_bundle, graphics)
    parsed = parse_field(source_bundle)
    _audit_scanner_header(parsed.header)
    components = [part.data for part in parsed.parts]
    triangles = surface._walkmesh_layer(components[1], ENTRY_WALKMESH)
    for position, triangle, label in (
        (ENTRY_POSITION, ENTRY_TRIANGLE, "arrival"),
        (CONSOLE_POSITION, CONSOLE_TRIANGLE, "scanner frontage"),
        (RETURN_CONTROLLER_POSITION, RETURN_CONTROLLER_TRIANGLE, "return door"),
        (RETURN_CROSSING_WAYPOINT, RETURN_CROSSING_TRIANGLE, "door crossing"),
    ):
        hits = tuple(
            index
            for index, candidate in enumerate(triangles)
            if surface._point_inside_triangle(position, candidate)
        )
        if hits != (triangle,):
            raise surface.SurfaceSoylentBuildError(
                f"Field 588 {label} left audited triangle {triangle}: {hits}"
            )
    script = _prepare_script(components[surface.SCRIPT_INDEX])
    encounters = _disable_encounters(components[6])
    _assert_final_identity("ATEL", script, FINAL_SCRIPT_IDENTITY)
    _assert_final_identity("encounters", encounters, FINAL_ENCOUNTER_IDENTITY)
    components[surface.SCRIPT_INDEX] = script
    components[6] = encounters
    bundle = build_field_preserving(
        source_bundle,
        components,
        (surface.SCRIPT_INDEX, 6),
        compact_changed=True,
    )
    _assert_final_identity("packed bundle", bundle, FINAL_BUNDLE_IDENTITY)
    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise surface.SurfaceSoylentBuildError(
            "Field 588 packed output failed decoded-stream round trip"
        )
    _assert_final_identity("packed header", reparsed.header, FINAL_HEADER_IDENTITY)
    return surface.PreparedDonorField(
        DONOR588_IDENTITY,
        (
            "bright Etrenank diagnostic scanner credential room; baked scanner "
            "n29-n34 preserved; retail scanner/item/story progression retired; "
            "native model-backed return door retargeted to field 621/p5; "
            "random encounters disabled"
        ),
        source_bundle,
        graphics,
        reparsed.header,
        tuple(components),
        bundle,
        ((ENTRY_PARAMETER, ENTRY_TRIANGLE),),
    )


def prepare_donor588_from_discs(
    source_disc: Path | str, donor_disc: Path | str
) -> surface.PreparedDonorField:
    """Verify targets, extract Disc 1 field 550, and prepare it."""
    verify_donor588_targets_are_dummy(source_disc)
    return prepare_donor588(*load_donor588_source(donor_disc))


__all__ = [name for name in globals() if name.isupper()] + [
    "load_donor588_source",
    "prepare_donor588",
    "prepare_donor588_from_discs",
    "verify_donor588_targets_are_dummy",
]
