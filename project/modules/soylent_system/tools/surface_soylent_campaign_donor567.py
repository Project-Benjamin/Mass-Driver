#!/usr/bin/env python3
"""Prepare field 567 as the Surface Soylent stabilization ward.

Retail field 567 is the compact Krelian Lab Wels surgery room on Disc 1.
Its same-number Disc 2 resource slots are checked CDMAKE dummies, which makes
the room a natural, asset-complete bridge between the Surface intake lobby and
the Krelian Lab service corridor.  This module keeps that transplant isolated
from the campaign builder: it verifies both discs, makes the two reciprocal
entries playable, converts the party actors to runtime selectors, retires the
retail surgery scene, and preserves the room's three paired model doors.

The campaign layer may subsequently split each hardened door carrier into a
ghost interaction actor and a round physical seal.  ``ACTIVE_DOORS`` and the
other exported constants deliberately freeze every PC and helper needed for
that integration.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import struct
from typing import Sequence

import modules.soylent_system.base as surface
from shared.tools.xgdialog import DialogueBlockSpec, encode_dialogue, parse_dialogue
from shared.tools.xgdisc import (
    FIELD_DIRECTORY,
    FIRST_FIELD_LOCAL_FILE,
    Mode2Image,
    directory_file_fat_index,
)
from shared.tools.xgfield import build_field_preserving, parse_field
from shared.tools.xgscript import AtelScript as ScriptEditor


SCENE = 567
TARGET_BUNDLE_ID = 1740
TARGET_GRAPHICS_ID = 1741
SOURCE_BUNDLE_ID = 1745
SOURCE_GRAPHICS_ID = 1746

DONOR567_IDENTITY = surface.SourceIdentity(
    SCENE,
    TARGET_BUNDLE_ID,
    TARGET_GRAPHICS_ID,
    84_648,
    "c9648040ebd58d16218f2a1c75651cf2c34bda83fd8b9aa68b93115e3848b75d",
    165_888,
    "29462f01559383a600dd55ff25f67530e64cd2c2b1e15f831ad8868b6fafe4d1",
    4_496,
    "887a46dcf43b749ae1fd4698193a4a2ae2aab12a6f88927cc287feeabba26975",
    896,
    "a6913dafa91709c9a2f81144abcb72528b1712752804ae99933540c645d6762b",
)

DONOR567_TARGET_IDS = (TARGET_BUNDLE_ID, TARGET_GRAPHICS_ID)
DONOR567_SOURCE_IDS = (SOURCE_BUNDLE_ID, SOURCE_GRAPHICS_ID)

SOURCE_DIALOGUE_IDENTITY = (
    51,
    "37a4b87f4393f9ce6ffc87b8a63cc0d300dcfb907096d46938d810e407406eb1",
)
SOURCE_ENTITY_COUNT = 22
SOURCE_HEADER_ACTOR_COUNT = 31
SOURCE_BYTECODE_SIZE = 0x0B8C

# The native entry points are already comfortably inside the room.  Concrete
# camera/actor directions replace retail's 0xFF inheritance: p0 faces away
# from the southwest door into the ward, and p1 faces away from the northeast
# service door.  Each point has exactly one audited layer-0 triangle.
ENTRY_PARAMETERS = (0, 1)
ENTRY_POSITIONS = {
    0: (140, 350),
    1: (860, -360),
}
ENTRY_WALKMESH = 0
ENTRY_DIRECTIONS = {
    0: (1, 1),
    1: (5, 5),
}
ENTRY_TRIANGLES = {
    0: 88,
    1: 51,
}
ENTRY_SOURCE = {
    0: struct.pack("<hhBBB", 140, 350, 0, 0xFF, 0xFF),
    1: struct.pack("<hhBBB", 860, -360, 0, 0xFF, 0xFF),
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

PARTY_INIT_PCS = (0x006E, 0x0094, 0x009F)
PARTY_SOURCE_OPERANDS = (0x8000, 0x8001, 0x8002)

# Controller source locations and geometry.  Their native init bodies end in
# STOP; the prepared versions move IMMOBILE immediately before that STOP so a
# later campaign collision split can recognize and safely replace them.
LOBBY_CONTROLLER = 4
LOBBY_NATIVE_INIT_PC = 0x00AA
LOBBY_NATIVE_INIT_STOP_PC = 0x00BE
LOBBY_NATIVE_ACTION_PC = 0x00CA
LOBBY_ASYNC_HELPER = 7
LOBBY_BLOCKING_HELPER = 8
LOBBY_PLAYER_SCRIPT = 4
LOBBY_DESTINATION_FIELD = 621
LOBBY_DESTINATION_PARAMETER = 4

SERVICE_CONTROLLER = 5
SERVICE_NATIVE_INIT_PC = 0x00E0
SERVICE_NATIVE_INIT_STOP_PC = 0x00F4
SERVICE_NATIVE_ACTION_PC = 0x00F6
SERVICE_ASYNC_HELPER = 11
SERVICE_BLOCKING_HELPER = 12
SERVICE_PLAYER_SCRIPT = 5
SERVICE_DESTINATION_FIELD = 565
SERVICE_DESTINATION_PARAMETER = 2

RESTRICTED_CONTROLLER = 6
RESTRICTED_NATIVE_INIT_PC = 0x010C
RESTRICTED_NATIVE_INIT_STOP_PC = 0x0120
RESTRICTED_NATIVE_ACTION_PC = 0x0122
RESTRICTED_ASYNC_HELPER = 9
RESTRICTED_BLOCKING_HELPER = 10
RESTRICTED_PLAYER_SCRIPT = 6

CONTROLLER_NATIVE_INITS = {
    LOBBY_CONTROLLER: (LOBBY_NATIVE_INIT_PC, LOBBY_NATIVE_INIT_STOP_PC),
    SERVICE_CONTROLLER: (SERVICE_NATIVE_INIT_PC, SERVICE_NATIVE_INIT_STOP_PC),
    RESTRICTED_CONTROLLER: (
        RESTRICTED_NATIVE_INIT_PC,
        RESTRICTED_NATIVE_INIT_STOP_PC,
    ),
}
CONTROLLER_POSITIONS = {
    LOBBY_CONTROLLER: (65, 435),
    SERVICE_CONTROLLER: (935, -440),
    RESTRICTED_CONTROLLER: (1000, -125),
}
CONTROLLER_TRIANGLES = {
    LOBBY_CONTROLLER: 89,
    SERVICE_CONTROLLER: 45,
    RESTRICTED_CONTROLLER: 48,
}
CONTROLLER_INTERACTION_HALF_EXTENTS = (0x1E, 0x1E)
IMMOVABLE_OPCODE = bytes.fromhex("F8 00 10 00")
IMMOVABLE_PRECEDES_STOP = True

# All six native door leaves share CALL 0x0A7A; STOP in script four.  Keep
# both the asynchronous and blocking leaves: dropping the first helper makes
# half of the visible door remain shut.
DOOR_HELPER_SCRIPT_INDEX = 4
DOOR_HELPER_BODY = bytes.fromhex("05 7A 0A 00")
DOOR_HELPER_PCS = {
    LOBBY_ASYNC_HELPER: 0x013D,
    LOBBY_BLOCKING_HELPER: 0x0146,
    RESTRICTED_ASYNC_HELPER: 0x014F,
    RESTRICTED_BLOCKING_HELPER: 0x0158,
    SERVICE_ASYNC_HELPER: 0x0161,
    SERVICE_BLOCKING_HELPER: 0x016A,
}

# Native outbound destinations are frozen independently of the campaign
# topology so a mismatched retail source cannot be silently retargeted.
NATIVE_DOOR_DESTINATIONS = {
    LOBBY_CONTROLLER: (562, 1),
    SERVICE_CONTROLLER: (563, 0),
    RESTRICTED_CONTROLLER: (568, 0),
}

# The append layout is intentionally public.  The campaign consumes the two
# active action PCs, validates ``paired_door_action``, then adds fresh-Cross
# drain and seal release without guessing where this donor placed anything.
NEUTRAL_STORY_ENTITIES = tuple(range(13, 22))
NEUTRAL_STORY_INIT_BODY = bytes.fromhex("2A 23 20 01 80 00")
NEUTRAL_STORY_INIT_PC = 0x0B8C
NEUTRAL_STORY_STOP_PC = 0x0B91
HARDENED_CONTROLLER_INIT_PCS = {
    LOBBY_CONTROLLER: 0x0B92,
    SERVICE_CONTROLLER: 0x0BAB,
    RESTRICTED_CONTROLLER: 0x0BC4,
}
LOBBY_ACTION_PC = 0x0BDD
SERVICE_ACTION_PC = 0x0BF1
SEALED_ACTION_PC = 0x0C05

# (controller, prepared action PC, async helper, blocking helper,
#  player script, destination field, destination parameter)
ACTIVE_DOORS = (
    (
        LOBBY_CONTROLLER,
        LOBBY_ACTION_PC,
        LOBBY_ASYNC_HELPER,
        LOBBY_BLOCKING_HELPER,
        LOBBY_PLAYER_SCRIPT,
        LOBBY_DESTINATION_FIELD,
        LOBBY_DESTINATION_PARAMETER,
    ),
    (
        SERVICE_CONTROLLER,
        SERVICE_ACTION_PC,
        SERVICE_ASYNC_HELPER,
        SERVICE_BLOCKING_HELPER,
        SERVICE_PLAYER_SCRIPT,
        SERVICE_DESTINATION_FIELD,
        SERVICE_DESTINATION_PARAMETER,
    ),
)

SEALED_DIALOGUE_ID = 2
SEALED_DIALOGUE_TEXT = (
    "STABILIZATION WARD // PROCEDURE SUITE\n"
    "Sealed pending physician authorization.<Close>"
)

FINAL_SCRIPT_IDENTITY = (
    4_642,
    "00c1e177a6467fe76f70df7ca0597800daa7e1e86194051153fe5e511a645f18",
)
FINAL_DIALOGUE_IDENTITY = (
    133,
    "f24c1fc70cd7f66d4edb630154faef6ee276d60220c73234112cc1b045bb1374",
)
FINAL_BUNDLE_IDENTITY = (
    84_724,
    "b1ca6fbe63f7afa345a78669e125853447252d99ffb6bfcbda1e3dd817b31630",
)
FINAL_HEADER_IDENTITY = (
    896,
    "6f6d0ac4953b10f0618735ee06a6b312218a4f49259777a1810fb5030f21bed2",
)

# Retail field 567 independently uses the same Krelian Lab cue as field 565
# and disables random encounters in its entity-zero initializer.
MUSIC_PC = 0x0017
MUSIC_OPCODE = bytes.fromhex("75 3D 80")
NO_RANDOM_ENCOUNTERS_PC = 0x001A
NO_RANDOM_ENCOUNTERS = bytes.fromhex("F7 2C 81 00 80")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _u16(value: int) -> bytes:
    if not isinstance(value, int) or not 0 <= value <= 0xFFFF:
        raise surface.SurfaceSoylentBuildError(
            f"Field 567 u16 value is outside 0..65535: {value}"
        )
    return struct.pack("<H", value)


def paired_door_action(
    async_helper: int,
    blocking_helper: int,
    player_script: int,
    destination_field: int,
    destination_parameter: int,
) -> bytes:
    """Encode field 567's authentic two-leaf/player field transition."""

    if not 0 <= async_helper <= 0xFF or not 0 <= blocking_helper <= 0xFF:
        raise surface.SurfaceSoylentBuildError(
            "Field 567 door helper entity is outside 0..255"
        )
    if not 0 <= player_script <= 0x1F:
        raise surface.SurfaceSoylentBuildError(
            "Field 567 player doorway script is outside 0..31"
        )
    return (
        b"\xFE\x54"
        + b"\x07" + bytes((async_helper, 0x24))
        + b"\x09" + bytes((blocking_helper, 0x24))
        + b"\x07\x01" + bytes((0x20 | player_script,))
        + b"\x26\x0A\x80"
        + surface._change_field(destination_field, destination_parameter)
        + b"\x5B"
    )


def sealed_door_action(dialogue_id: int, routine_pc: int) -> bytes:
    """Drain Cross and show the repeatable restricted-suite response."""

    release_pc = routine_pc + 3
    return (
        b"\x33\xFE\x54"
        + surface.mass_driver._wait_for_pad_release(
            surface.mass_driver.PAD_MASK_CROSS,
            release_pc,
        )
        + b"\x26\x01\x80"
        + b"\xF5" + _u16(dialogue_id)
        + b"\x01\x9C\xFE\x53\x00"
    )


def _assert_source_identity(bundle: bytes, graphics: bytes) -> None:
    identity = DONOR567_IDENTITY
    if (len(bundle), _sha256(bundle)) != (
        identity.bundle_size,
        identity.bundle_sha256,
    ):
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 donor field 567 bundle changed"
        )
    if (len(graphics), _sha256(graphics)) != (
        identity.graphics_size,
        identity.graphics_sha256,
    ):
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 donor field 567 graphics changed"
        )

    parsed = parse_field(bundle)
    script = parsed.parts[surface.SCRIPT_INDEX].data
    if (len(script), _sha256(script)) != (
        identity.script_size,
        identity.script_sha256,
    ):
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 donor field 567 ATEL script changed"
        )
    if (len(parsed.header), _sha256(parsed.header)) != (
        identity.header_size,
        identity.header_sha256,
    ):
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 donor field 567 header changed"
        )
    if (
        len(parsed.parts[7].data),
        _sha256(parsed.parts[7].data),
    ) != SOURCE_DIALOGUE_IDENTITY:
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 donor field 567 dialogue changed"
        )

    editor = ScriptEditor(script)
    actor_count = struct.unpack_from("<H", parsed.header, 0x18C)[0]
    if (
        editor.entity_count != SOURCE_ENTITY_COUNT
        or actor_count != SOURCE_HEADER_ACTOR_COUNT
        or editor.bytecode_size != SOURCE_BYTECODE_SIZE
    ):
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 donor field 567 entity layout changed"
        )


def load_donor567_source(donor_disc: Path | str) -> tuple[bytes, bytes]:
    """Extract and verify the natural field-567 pair from Disc 1."""

    image = Mode2Image(donor_disc)
    entries = image.read_index()
    first = image.read_directories()[FIELD_DIRECTORY].first_file
    local = FIRST_FIELD_LOCAL_FILE + 2 * SCENE
    bundle_index = directory_file_fat_index(first, local)
    graphics_index = directory_file_fat_index(first, local + 1)
    actual_ids = (bundle_index + 5, graphics_index + 5)
    if actual_ids != DONOR567_SOURCE_IDS:
        raise surface.SurfaceSoylentBuildError(
            "Disc 1 field 567 resolved to canonical resources "
            f"{actual_ids}, expected {DONOR567_SOURCE_IDS}"
        )
    bundle = image.extract_entry(entries[bundle_index])
    graphics = image.extract_entry(entries[graphics_index])
    _assert_source_identity(bundle, graphics)
    return bundle, graphics


def verify_donor567_targets_are_dummy(source_disc: Path | str) -> None:
    """Refuse to overwrite field 567's Disc 2 slots unless both are dummies."""

    expected = {
        canonical_id: (len(surface.DONOR_DUMMY), surface.DONOR_DUMMY_SHA256)
        for canonical_id in DONOR567_TARGET_IDS
    }
    resources = surface._load_canonical_resources(source_disc, expected)
    if set(resources) != set(DONOR567_TARGET_IDS) or any(
        resources[canonical_id] != surface.DONOR_DUMMY
        for canonical_id in DONOR567_TARGET_IDS
    ):
        raise surface.SurfaceSoylentBuildError(
            "Disc 2 field-567 donor target is not the checked CDMAKE dummy"
        )


def _patch_entries_and_party(script: bytes) -> bytes:
    for parameter in ENTRY_PARAMETERS:
        script = surface._patch_bytecode(
            script,
            1 + 7 * parameter,
            ENTRY_SOURCE[parameter],
            ENTRY_PLAYABLE[parameter],
        )
    return surface._patch_donor_party(
        script,
        PARTY_INIT_PCS,
        PARTY_SOURCE_OPERANDS,
    )


def _append_dialogue_blocks(
    source: bytes,
    texts: Sequence[str],
    *,
    width: int,
    height: int,
) -> bytes:
    parsed = parse_dialogue(source)
    specs = [
        DialogueBlockSpec(block.block_id, block.width, block.height, block.text)
        for block in parsed.blocks
    ]
    for text in texts:
        specs.append(DialogueBlockSpec(len(specs), width, height, text))
    rebuilt = encode_dialogue(specs)
    reparsed = parse_dialogue(rebuilt)
    for before, after in zip(parsed.blocks, reparsed.blocks, strict=False):
        if (before.width, before.height, before.payload) != (
            after.width,
            after.height,
            after.payload,
        ):
            raise surface.SurfaceSoylentBuildError(
                "Field 567 existing dialogue changed while appending"
            )
    return rebuilt


def _verify_native_doors(editor: ScriptEditor) -> None:
    for controller, (init_pc, stop_pc) in CONTROLLER_NATIVE_INITS.items():
        position = CONTROLLER_POSITIONS[controller]
        expected_body = (
            b"\xBC\x19"
            + struct.pack("<hh", *position)
            + b"\xC0"
            + b"\xF8\x00\x00\x20"
            + b"\xF8\x03\x04\x00"
            + b"\x18\x1E\x1E\x1E\x00"
        )
        if (
            editor.get_script_pointer(controller, 0) != init_pc
            or editor.bytecode[init_pc:stop_pc] != expected_body
            or editor.bytecode[stop_pc] != 0
        ):
            raise surface.SurfaceSoylentBuildError(
                f"Field 567 native door e{controller} init moved"
            )

    native_actions = (
        (
            LOBBY_CONTROLLER,
            LOBBY_NATIVE_ACTION_PC,
            LOBBY_ASYNC_HELPER,
            LOBBY_BLOCKING_HELPER,
            LOBBY_PLAYER_SCRIPT,
        ),
        (
            SERVICE_CONTROLLER,
            SERVICE_NATIVE_ACTION_PC,
            SERVICE_ASYNC_HELPER,
            SERVICE_BLOCKING_HELPER,
            SERVICE_PLAYER_SCRIPT,
        ),
        (
            RESTRICTED_CONTROLLER,
            RESTRICTED_NATIVE_ACTION_PC,
            RESTRICTED_ASYNC_HELPER,
            RESTRICTED_BLOCKING_HELPER,
            RESTRICTED_PLAYER_SCRIPT,
        ),
    )
    for controller, pc, async_helper, blocking_helper, player_script in native_actions:
        destination_field, destination_parameter = NATIVE_DOOR_DESTINATIONS[controller]
        expected = paired_door_action(
            async_helper,
            blocking_helper,
            player_script,
            destination_field,
            destination_parameter,
        )
        if (
            editor.get_script_pointer(controller, 2) != pc
            or editor.bytecode[pc:pc + len(expected)] != expected
        ):
            raise surface.SurfaceSoylentBuildError(
                f"Field 567 native door e{controller} action moved"
            )

    for helper, pc in DOOR_HELPER_PCS.items():
        if (
            editor.get_script_pointer(helper, DOOR_HELPER_SCRIPT_INDEX) != pc
            or editor.bytecode[pc:pc + len(DOOR_HELPER_BODY)] != DOOR_HELPER_BODY
        ):
            raise surface.SurfaceSoylentBuildError(
                f"Field 567 paired-door helper e{helper}:s4 moved"
            )


def _install_ward_scripts(script: bytes) -> bytes:
    editor = ScriptEditor(script)
    _verify_native_doors(editor)

    if editor.append_raw_routine(NEUTRAL_STORY_INIT_BODY) != NEUTRAL_STORY_INIT_PC:
        raise surface.SurfaceSoylentBuildError(
            "Field 567 neutral story initializer moved"
        )
    for entity in NEUTRAL_STORY_ENTITIES:
        editor.set_script_pointer(entity, 0, NEUTRAL_STORY_INIT_PC)
        for script_index in range(1, 32):
            editor.set_script_pointer(entity, script_index, NEUTRAL_STORY_STOP_PC)

    for controller in (
        LOBBY_CONTROLLER,
        SERVICE_CONTROLLER,
        RESTRICTED_CONTROLLER,
    ):
        init_pc, stop_pc = CONTROLLER_NATIVE_INITS[controller]
        native_body = editor.bytecode[init_pc:stop_pc]
        hardened = native_body + IMMOVABLE_OPCODE + b"\x00"
        appended_pc = editor.append_and_repoint(controller, 0, hardened)
        if appended_pc != HARDENED_CONTROLLER_INIT_PCS[controller]:
            raise surface.SurfaceSoylentBuildError(
                f"Field 567 hardened door e{controller} init moved"
            )

    for active in ACTIVE_DOORS:
        (
            controller,
            expected_pc,
            async_helper,
            blocking_helper,
            player_script,
            destination_field,
            destination_parameter,
        ) = active
        action = paired_door_action(
            async_helper,
            blocking_helper,
            player_script,
            destination_field,
            destination_parameter,
        )
        if editor.append_and_repoint(controller, 2, action) != expected_pc:
            raise surface.SurfaceSoylentBuildError(
                f"Field 567 active door e{controller} action moved"
            )

    sealed = sealed_door_action(SEALED_DIALOGUE_ID, SEALED_ACTION_PC)
    if (
        editor.append_and_repoint(RESTRICTED_CONTROLLER, 2, sealed)
        != SEALED_ACTION_PC
    ):
        raise surface.SurfaceSoylentBuildError(
            "Field 567 restricted-suite response moved"
        )

    # The helper scripts themselves and the complete native bytecode prefix
    # remain untouched; only checked entry/party operands and pointer slots
    # above have changed.
    for helper, pc in DOOR_HELPER_PCS.items():
        if (
            editor.get_script_pointer(helper, DOOR_HELPER_SCRIPT_INDEX) != pc
            or editor.bytecode[pc:pc + len(DOOR_HELPER_BODY)] != DOOR_HELPER_BODY
        ):
            raise surface.SurfaceSoylentBuildError(
                f"Field 567 helper e{helper}:s4 changed during ward install"
            )
    return editor.to_bytes()


def _assert_final_identity(
    label: str,
    data: bytes,
    identity: tuple[int, str],
) -> None:
    if (len(data), _sha256(data)) != identity:
        raise surface.SurfaceSoylentBuildError(
            f"Field 567 final {label} identity changed"
        )


def prepare_donor567(
    source_bundle: bytes,
    graphics: bytes,
) -> surface.PreparedDonorField:
    """Build the deterministic, playable stabilization-ward transplant."""

    _assert_source_identity(source_bundle, graphics)
    parsed = parse_field(source_bundle)
    components = [part.data for part in parsed.parts]
    script = _patch_entries_and_party(components[surface.SCRIPT_INDEX])

    triangles = surface._walkmesh_layer(components[1], ENTRY_WALKMESH)
    for parameter in ENTRY_PARAMETERS:
        triangle = ENTRY_TRIANGLES[parameter]
        hits = tuple(
            index
            for index, candidate in enumerate(triangles)
            if surface._point_inside_triangle(
                ENTRY_POSITIONS[parameter],
                candidate,
            )
        )
        if hits != (triangle,):
            raise surface.SurfaceSoylentBuildError(
                f"Field 567 p{parameter} left audited triangle {triangle}: {hits}"
            )

    entry_editor = ScriptEditor(script)
    if (
        entry_editor.bytecode[MUSIC_PC:MUSIC_PC + len(MUSIC_OPCODE)]
        != MUSIC_OPCODE
        or entry_editor.bytecode[
            NO_RANDOM_ENCOUNTERS_PC:
            NO_RANDOM_ENCOUNTERS_PC + len(NO_RANDOM_ENCOUNTERS)
        ] != NO_RANDOM_ENCOUNTERS
    ):
        raise surface.SurfaceSoylentBuildError(
            "Field 567 native music or encounter suppression changed"
        )

    script = _install_ward_scripts(script)
    dialogue = _append_dialogue_blocks(
        components[7],
        (SEALED_DIALOGUE_TEXT,),
        width=58,
        height=3,
    )
    _assert_final_identity("ATEL", script, FINAL_SCRIPT_IDENTITY)
    _assert_final_identity("dialogue", dialogue, FINAL_DIALOGUE_IDENTITY)

    components[surface.SCRIPT_INDEX] = script
    components[7] = dialogue
    bundle = build_field_preserving(
        source_bundle,
        components,
        (surface.SCRIPT_INDEX, 7),
        compact_changed=True,
    )
    _assert_final_identity("packed bundle", bundle, FINAL_BUNDLE_IDENTITY)

    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise surface.SurfaceSoylentBuildError(
            "Field 567 packed output failed decoded-stream round trip"
        )
    _assert_final_identity("packed header", reparsed.header, FINAL_HEADER_IDENTITY)

    return surface.PreparedDonorField(
        DONOR567_IDENTITY,
        (
            "stabilization and observation ward; playable lobby/service entries; "
            "native paired-door helpers preserved; restricted procedure suite "
            "sealed; retail surgery scene neutralized; door carriers immovable"
        ),
        source_bundle,
        graphics,
        reparsed.header,
        tuple(components),
        bundle,
        tuple(
            (parameter, ENTRY_TRIANGLES[parameter])
            for parameter in ENTRY_PARAMETERS
        ),
    )


def prepare_donor567_from_discs(
    source_disc: Path | str,
    donor_disc: Path | str,
) -> surface.PreparedDonorField:
    """Verify Disc 2 targets, extract Disc 1 field 567, and prepare it."""

    verify_donor567_targets_are_dummy(source_disc)
    return prepare_donor567(*load_donor567_source(donor_disc))


__all__ = [
    "ACTIVE_DOORS",
    "CONTROLLER_INTERACTION_HALF_EXTENTS",
    "CONTROLLER_POSITIONS",
    "CONTROLLER_TRIANGLES",
    "DONOR567_IDENTITY",
    "DONOR567_SOURCE_IDS",
    "DONOR567_TARGET_IDS",
    "DOOR_HELPER_BODY",
    "DOOR_HELPER_PCS",
    "DOOR_HELPER_SCRIPT_INDEX",
    "ENTRY_DIRECTIONS",
    "ENTRY_PARAMETERS",
    "ENTRY_PLAYABLE",
    "ENTRY_POSITIONS",
    "ENTRY_TRIANGLES",
    "FINAL_BUNDLE_IDENTITY",
    "FINAL_DIALOGUE_IDENTITY",
    "FINAL_HEADER_IDENTITY",
    "FINAL_SCRIPT_IDENTITY",
    "HARDENED_CONTROLLER_INIT_PCS",
    "IMMOVABLE_OPCODE",
    "IMMOVABLE_PRECEDES_STOP",
    "LOBBY_CONTROLLER",
    "NEUTRAL_STORY_ENTITIES",
    "NEUTRAL_STORY_INIT_BODY",
    "NEUTRAL_STORY_INIT_PC",
    "NEUTRAL_STORY_STOP_PC",
    "RESTRICTED_CONTROLLER",
    "SEALED_ACTION_PC",
    "SEALED_DIALOGUE_ID",
    "SEALED_DIALOGUE_TEXT",
    "SERVICE_CONTROLLER",
    "load_donor567_source",
    "paired_door_action",
    "prepare_donor567",
    "prepare_donor567_from_discs",
    "sealed_door_action",
    "verify_donor567_targets_are_dummy",
]
