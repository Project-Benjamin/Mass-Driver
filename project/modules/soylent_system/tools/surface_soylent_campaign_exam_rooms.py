#!/usr/bin/env python3
"""Build four independent, bright clinical rooms for Intake.

Logical fields 591 through 594 are unused Disc 2 slots.  Each receives the
same verified Disc 1 field-352 Ethos infirmary shell used by the campaign's
doctor office: the examination bed, illuminated medical workstation, props,
walkmesh, native animated exit, and external graphics remain intact.  Retail
story events and random encounters remain retired by the empty-clinic
foundation.

Three collision-ghosted, facing-gated X carriers make the existing side
computer bank usable without adding invisible collision or allowing an
empty-aisle interaction.  Fields 591 and 592 expose repeatable clinical status
screens.  Field 593 visibly holds the Quarantine keycard until the player
explicitly accepts it; leaving the card grants nothing and keeps the prompt
repeatable.  An accepted pickup uses the retail item sound and persistent
operand 0x021A bit 8, after which the terminal displays Fei's medical
diagnostics.  Field 594 is a separate treatment-preparation room whose terminal
reports benign metabolic conditioning status.  The rooms return to their own
Intake parameters 7, 8, 9, and 5 respectively.

This module deliberately does not edit the campaign builder or Intake.  It
exports the complete target, entry, door, terminal, and progression contracts
needed by that integration layer.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import struct
from typing import Mapping, Sequence

import modules.soylent_system.base as surface
import modules.soylent_system.tools.surface_soylent_campaign_empty_clinic567 as foundation
from shared.tools.xgdialog import DialogueBlockSpec, encode_dialogue, parse_dialogue
from shared.tools.xgdisc import (
    FIELD_DIRECTORY,
    FIRST_FIELD_LOCAL_FILE,
    Mode2Image,
    directory_file_fat_index,
)
from shared.tools.xgfield import build_field_preserving, parse_field
from shared.tools.xgscript import AtelScript as ScriptEditor


SOURCE_SCENE = foundation.SOURCE_SCENE
SOURCE_BUNDLE_ID = foundation.SOURCE_BUNDLE_ID
SOURCE_GRAPHICS_ID = foundation.SOURCE_GRAPHICS_ID
SOURCE_IDS = foundation.EMPTY_CLINIC567_SOURCE_IDS
SOURCE_BUNDLE_IDENTITY = foundation.SOURCE_BUNDLE_IDENTITY
SOURCE_GRAPHICS_IDENTITY = foundation.SOURCE_GRAPHICS_IDENTITY
SOURCE_COMPONENT_IDENTITIES = foundation.SOURCE_COMPONENT_IDENTITIES

SCENES = (591, 592, 593, 594)
TARGET_IDS_BY_SCENE = {
    591: (1788, 1789),
    592: (1790, 1791),
    593: (1792, 1793),
    594: (1794, 1795),
}
TARGET_IDS = tuple(
    canonical_id
    for scene in SCENES
    for canonical_id in TARGET_IDS_BY_SCENE[scene]
)
RETURN_PARAMETERS_BY_SCENE = {591: 7, 592: 8, 593: 9, 594: 5}

ENTRY_PARAMETER = foundation.ENTRY_PARAMETER
ENTRY_POSITION = foundation.ENTRY_POSITION
ENTRY_WALKMESH = foundation.ENTRY_WALKMESH
ENTRY_CAMERA_DIRECTION = foundation.ENTRY_CAMERA_DIRECTION
ENTRY_ACTOR_DIRECTION = foundation.ENTRY_ACTOR_DIRECTION
ENTRY_TRIANGLE = foundation.ENTRY_TRIANGLE
ENTRY_PLAYABLE = foundation.ENTRY_PLAYABLE

SOURCE_ENTITY_COUNT = foundation.SOURCE_ENTITY_COUNT
ENTITY_COUNT = SOURCE_ENTITY_COUNT + 1
SOURCE_HEADER_ACTOR_COUNT = foundation.SOURCE_HEADER_ACTOR_COUNT
HEADER_ACTOR_COUNT = SOURCE_HEADER_ACTOR_COUNT + 1
SHARED_STOP_PC = foundation.SHARED_STOP_PC

# E19 remains inserted at the old ATEL/header boundary so the campaign's later
# door-seal entity and every existing save-state actor retain their ordering.
# Retired field-352 entities 4 and 5 supply two additional carriers.  Together
# they reproduce field 550's exhaustively verified side-bank frontage: narrow
# overlapping X reaches, native facing gates, and no physical collision.  The
# anchors sit on static model 3's room-facing z=-167 plane; operator triangles
# 31, 30, 6, and 7 supply the reachable floor immediately in front of them.
TERMINAL_ENTITY = SOURCE_ENTITY_COUNT
TERMINAL_AUX_ENTITIES = (4, 5)
TERMINAL_ENTITIES = (TERMINAL_ENTITY, *TERMINAL_AUX_ENTITIES)
TERMINAL_POSITIONS = ((80, -167), (116, -167), (152, -167))
TERMINAL_TRIANGLES = (31, 6, 6)
TERMINAL_POSITION = TERMINAL_POSITIONS[0]
TERMINAL_WALKMESH = 0
TERMINAL_TRIANGLE = TERMINAL_TRIANGLES[0]
TERMINAL_OPERATOR_TRIANGLES = (31, 30, 6, 7)
TERMINAL_INTERACTION_HALF_WIDTH = 0x01
TERMINAL_INTERACTION_HALF_DEPTH = 0x0F
TERMINAL_REQUIRES_FACING = True
PLAYER_COLLISION_RADIUS = 0x10
TERMINAL_EFFECTIVE_HALF_REACH = (
    2 * TERMINAL_INTERACTION_HALF_WIDTH + PLAYER_COLLISION_RADIUS,
    2 * TERMINAL_INTERACTION_HALF_DEPTH + PLAYER_COLLISION_RADIUS,
)
TERMINAL_FRONTAGE_X = (70, 164)
TERMINAL_APPROACH_FIXTURE = (70.00340270996094, -142.5971221923828)
TERMINAL_APPROACH_YAW = 0x0400
TERMINAL_REJECTED_AISLE_FIXTURE = (75.00785827636719, -77.75068664550781)
TERMINAL_BED_YAW = 0x0800
TERMINAL_HEADER_FLAGS = 0x01E0
TERMINAL_HEADER_MODEL_INDEX = 0
TERMINAL_HEADER_RECORD = surface.mass_driver._field_actor_record(
    TERMINAL_HEADER_FLAGS,
    TERMINAL_POSITION[0],
    TERMINAL_POSITION[1],
    TERMINAL_HEADER_MODEL_INDEX,
)

# Model 3 is the field's actual side computer bank.  Its source-node 22 record
# rotates the local X[167,220]/Z[11,164] model through 0x0400 to world
# X[11,164]/Z[-220,-167].  Inserting e19 shifts that static node from 22 to 23
# without changing either the record or model bytes.  Model 5 is the unrelated
# screen assembly behind the examination bed.
MEDICAL_TERMINAL_MODEL_INDEX = 3
MEDICAL_TERMINAL_SOURCE_HEADER_NODE = 22
MEDICAL_TERMINAL_HEADER_NODE = MEDICAL_TERMINAL_SOURCE_HEADER_NODE + 1
MEDICAL_TERMINAL_MODEL_IDENTITY = (
    1_436,
    "bc7ed77986a3133bed3e6f3de6d4b7c59ca4f92c4ef45f69130bef34946baa28",
)
MEDICAL_TERMINAL_HEADER_RECORD = bytes.fromhex(
    "10 00 00 00 00 04 00 00 00 00 00 00 00 00 03 00"
)

BED_MODEL_INDEX = foundation.BED_MODEL_INDEX
BED_SOURCE_HEADER_NODE = foundation.BED_HEADER_NODE
BED_HEADER_NODE = BED_SOURCE_HEADER_NODE + 1
BED_MODEL_IDENTITY = foundation.BED_MODEL_IDENTITY
BED_HEADER_RECORD = foundation.BED_HEADER_RECORD

RETURN_CONTROLLER = foundation.RETURN_CONTROLLER
RETURN_CONTROLLER_POSITION = foundation.RETURN_CONTROLLER_POSITION
RETURN_CONTROLLER_TRIANGLE = foundation.RETURN_CONTROLLER_TRIANGLE
RETURN_CONTROLLER_TRIANGLES = foundation.RETURN_CONTROLLER_TRIANGLES
RETURN_HELPER = foundation.RETURN_HELPER
RETURN_HELPER_SCRIPT_INDEX = foundation.RETURN_HELPER_SCRIPT_INDEX
RETURN_HELPER_PC = foundation.RETURN_HELPER_PC
RETURN_HELPER_BODY = foundation.RETURN_HELPER_BODY
RETURN_PLAYER_SCRIPT = foundation.RETURN_PLAYER_SCRIPT
RETURN_FIELD = 621

DOOR_SEAL_RADIUS = foundation.DOOR_SEAL_RADIUS
DOOR_INTERACTION_HALF_WIDTH = foundation.DOOR_INTERACTION_HALF_WIDTH
DOOR_INTERACTION_HALF_DEPTH = foundation.DOOR_INTERACTION_HALF_DEPTH
DOOR_ACTION_HALF_DEPTH = foundation.DOOR_ACTION_HALF_DEPTH
DOOR_CLOSED_SIDE_PROBE = foundation.DOOR_CLOSED_SIDE_PROBE
DOOR_OPEN_SIDE_PROBE = foundation.DOOR_OPEN_SIDE_PROBE
IMMOVABLE_OPCODE = foundation.IMMOVABLE_OPCODE
IMMOVABLE_PRECEDES_STOP = foundation.IMMOVABLE_PRECEDES_STOP

QUARANTINE_KEYCARD_OPERAND = 0x021A
QUARANTINE_KEYCARD_BIT_INDEX = 8
QUARANTINE_KEYCARD_MASK = 0x0100
ITEM_ACQUISITION_SOUND_ID = 0x37
ITEM_ACQUISITION_SOUND = b"\x74\x37\x80"

HEMATOLOGY_DIALOGUE = (
    "PATIENT RECORD: H-591-04\n"
    "Type: long-muzzled demihuman\n"
    "Pulse 74 bpm / BP 102/64\n"
    "Temp 37.1 C / Resp. 16/min<New>"
    "Hemoglobin: BELOW BASELINE\n"
    "Marrow response: IMPROVING\n"
    "Tonic uptake: 93%\n"
    "Prognosis: STABLE.<Close>"
)
NANOMACHINE_DIALOGUE = (
    "PATIENT RECORD: N-592-07\n"
    "Type: cream-furred demihuman\n"
    "Pulse 68 bpm / BP 110/70\n"
    "Temp 36.9 C / Resp. 15/min<New>"
    "Joint inflammation: MODERATE\n"
    "Nanomachine uptake: 96%\n"
    "Pain response: IMPROVING\n"
    "Prognosis: STABLE.<Close>"
)
TREATMENT_PREPARATION_DIALOGUE = (
    "PATIENT RECORD: T-594-03\n"
    "Type: fin-armed demihuman\n"
    "Pulse 76 bpm / BP 108/68\n"
    "Temp 37.0 C / Resp. 18/min<New>"
    "Hydration: NOMINAL\n"
    "Metabolic response: 91%\n"
    "Injection uptake: STABLE\n"
    "Prognosis: IMPROVING.<Close>"
)

# The public waiting area remains hopeful at this point in the story.  These
# private-room patients likewise believe the staff are helping them; nothing
# in their dialogue anticipates the later Soylent revelation.  The physician
# wording is deliberately similar in purpose but distinct in every room.
DOCTOR_DIALOGUES_BY_SCENE = {
    591: (
        'Doctor\n"How did you get in here?\n'
        'This bay is private.\n'
        'Go back to the waiting area."<Close>'
    ),
    592: (
        'Doctor\n"You lack clearance here.\n'
        'This procedure is private.\n'
        'Please wait at reception."<Close>'
    ),
    593: (
        'Doctor\n"This is a restricted room.\n'
        'My patient needs privacy.\n'
        'Return to the waiting area."<Close>'
    ),
    594: (
        'Doctor\n"You should not be in here.\n'
        'Treatment is underway.\n'
        'Wait outside for your name."<Close>'
    ),
}
PATIENT_DIALOGUES_BY_SCENE = {
    591: (
        'Patient\n"The tonic should help me\n'
        'get my strength back.\n'
        'I may go home soon."<Close>'
    ),
    592: (
        'Patient\n"This should ease the pain\n'
        'in my joints.\n'
        'I am staying hopeful."<Close>'
    ),
    593: (
        'Patient\n"My results look promising.\n'
        'After this, I can go\n'
        'back to my family."<Close>'
    ),
    594: (
        'Patient\n"The injections are helping.\n'
        'Tomorrow, I may be strong\n'
        'enough to leave."<Close>'
    ),
}
KEYCARD_INSERTED_DIALOGUE = (
    "QUARANTINE KEYCARD\n"
    "A keycard is seated in the\n"
    "computer's access slot.<Close>"
)
KEYCARD_CHOICE_DIALOGUE = (
    "<Opcode:01:FF>Take the Quarantine keycard?\n"
    "     Accept it\n"
    "     Leave it<Close>"
)
KEYCARD_ACQUIRED_DIALOGUE = (
    "QUARANTINE KEYCARD ACQUIRED\n"
    "Access authorization:\n"
    "QUARANTINE DIAGNOSTICS.<Close>"
)
POST_KEYCARD_DIAGNOSTICS_DIALOGUE = (
    "PATIENT RECORD: A-593-12\n"
    "Type: shelled demihuman\n"
    "Pulse 58 bpm / BP 124/76\n"
    "Temp 36.5 C / Resp. 11/min<New>"
    "Shell density: NOMINAL\n"
    "Mineral balance: 98%\n"
    "Treatment response: STRONG\n"
    "Clearance: APPROVED.<Close>"
)
PATIENT_RECORD_DIALOGUES_BY_SCENE = {
    591: HEMATOLOGY_DIALOGUE,
    592: NANOMACHINE_DIALOGUE,
    593: POST_KEYCARD_DIAGNOSTICS_DIALOGUE,
    594: TREATMENT_PREPARATION_DIALOGUE,
}


@dataclass(frozen=True)
class ExamRoomSpec:
    """One logical target and its room-specific terminal contract."""

    scene: int
    target_bundle_id: int
    target_graphics_id: int
    return_parameter: int
    endpoint_id: str
    terminal_dialogues: tuple[str, ...]
    doctor_dialogue: str
    patient_dialogue: str
    awards_quarantine_keycard: bool
    role: str


EXAM_ROOM_SPECS = (
    ExamRoomSpec(
        591,
        1788,
        1789,
        7,
        "intake_exam_a.examination",
        (PATIENT_RECORD_DIALOGUES_BY_SCENE[591],),
        DOCTOR_DIALOGUES_BY_SCENE[591],
        PATIENT_DIALOGUES_BY_SCENE[591],
        False,
        "bright Solaris hematology examination room",
    ),
    ExamRoomSpec(
        592,
        1790,
        1791,
        8,
        "intake_exam_b.examination",
        (PATIENT_RECORD_DIALOGUES_BY_SCENE[592],),
        DOCTOR_DIALOGUES_BY_SCENE[592],
        PATIENT_DIALOGUES_BY_SCENE[592],
        False,
        "bright Solaris nanomachine examination room",
    ),
    ExamRoomSpec(
        593,
        1792,
        1793,
        9,
        "intake_exam_c.examination",
        (
            KEYCARD_INSERTED_DIALOGUE,
            KEYCARD_ACQUIRED_DIALOGUE,
            PATIENT_RECORD_DIALOGUES_BY_SCENE[593],
            KEYCARD_CHOICE_DIALOGUE,
        ),
        DOCTOR_DIALOGUES_BY_SCENE[593],
        PATIENT_DIALOGUES_BY_SCENE[593],
        True,
        "bright Solaris authorization examination room",
    ),
    ExamRoomSpec(
        594,
        1794,
        1795,
        5,
        "intake_treatment_preparation.treatment",
        (PATIENT_RECORD_DIALOGUES_BY_SCENE[594],),
        DOCTOR_DIALOGUES_BY_SCENE[594],
        PATIENT_DIALOGUES_BY_SCENE[594],
        False,
        "bright Solaris treatment-preparation room",
    ),
)
EXAM_ROOM_BY_SCENE = {spec.scene: spec for spec in EXAM_ROOM_SPECS}


@dataclass(frozen=True)
class PatientAssetSpec:
    """One exact native Soylent demihuman bank used in a treatment room."""

    target_scene: int
    source_scene: int
    source_bundle_id: int
    source_bank: int
    source_mapping: tuple[int, int, int, int]
    actor_identity: tuple[int, str]
    actor_section_identities: tuple[tuple[int, str], ...]
    sprite_identity: tuple[int, str]
    sprite_header: tuple[int, int, int, int]
    treatment_animation: int | None
    appearance: str


@dataclass(frozen=True)
class LoadedPatientAsset:
    """Verified actor/sprite bytes paired with their frozen provenance."""

    spec: PatientAssetSpec
    actor: bytes
    sprite: bytes


# Retail Disc 2 fields 620 and 621 are Soylent patient areas.  The four banks
# below were rendered during the V228 asset audit and are visibly different
# demihumans, rather than recolors of one silhouette.  The first two retain
# their native animation 1, a crouched treatment pose; the latter pair remain
# in their ordinary standing idle.  Every sprite is one 64-word-wide sheet
# with embedded CLUT data, so it can be relocated as a self-contained bank.
PATIENT_SOURCE_BUNDLE_IDENTITIES = {
    620: (
        1846,
        145_132,
        "6d35b720af7f116064af42692e5f4975dfe6b3231d641318df79240d78caabbc",
    ),
    621: (
        1848,
        128_452,
        "11f6727de949c6441aee587efcf87706a63c2c33f1616e9d214fb710afd534b9",
    ),
}
PATIENT_ASSET_SPECS = {
    591: PatientAssetSpec(
        591,
        620,
        1846,
        2,
        (960, 0, 0, 0),
        (
            1_508,
            "1db68ed864f5ce45cce60eec5ad2a3949b35e2d9bf22a8ee505e5ce6dbc10f5f",
        ),
        (
            (64, "cbe575eadea1ed52b380e53b96bdacfb15a09c99ef4f55326ec03452bc8c74c2"),
            (1_324, "2797d078dab8171da95f1422eedadff8a8cdce4de4a93134660b316e82aad1be"),
            (100, "2b67b3d0a464d1d5b4d5a1c6e41e8b892035bcfcfeff7455162ef4446378b57d"),
        ),
        (
            9_356,
            "05e616539b2840334499400f8591c9f8486737d4599b32cb25d62b29274abc0b",
        ),
        (1, 8, 64, 73),
        1,
        "crouched pale long-muzzled demihuman",
    ),
    592: PatientAssetSpec(
        592,
        620,
        1846,
        3,
        (960, 75, 0, 0),
        (
            1_512,
            "1e899c43471e35f37d8a0eb261dfd47c16d40b732fc70854d557fad68fa3d67b",
        ),
        (
            (68, "66eed3b747a96373285e342162bc7bf48f76dbf250fc8da60ce2c7f8b24f7cb4"),
            (1_292, "be8724c23e7de4bbaee778e95f85020f84d712b79a9f6dbb7a6b69c1cab91f40"),
            (132, "536a6f60f481a96d3c2fa38675ac4122c3ce0f30e8f0fb5d5b893c1b7cd53e33"),
        ),
        (
            8_716,
            "0d31c98646a26593c5b87e133f541e3dd17b62a7fd15a23e3014bd0a7468f08d",
        ),
        (1, 8, 64, 68),
        1,
        "tall cream-and-pink-furred demihuman",
    ),
    593: PatientAssetSpec(
        593,
        621,
        1848,
        1,
        (896, 0, 0, 0),
        (
            2_740,
            "c7f8db985ed06d11e8935ee114929e597542723d7fbc76a4dce8d56185063377",
        ),
        (
            (72, "923538ae5e3165b7e32256b858ed6205315f4d0ce985d2ded916037ead06da38"),
            (2_612, "799655ae9fb81cb7964b75fd8207228568952da6ac1599f62095f1ea5fd5616f"),
            (36, "583ce7af4af4abea84b2b87eae89224a13beeb2db1070d4178be531b521847e2"),
        ),
        (
            16_652,
            "d6e24302172e3977fcb4eb1c3bb13b4c2f730adf1393bb3a7e6d2c14459a83e6",
        ),
        (1, 8, 64, 130),
        None,
        "round-bodied dark-shelled demihuman",
    ),
    594: PatientAssetSpec(
        594,
        621,
        1848,
        3,
        (320, 256, 0, 0),
        (
            2_928,
            "0f082753c9c9c055496c998a0948ada510133815ed342ac60c3db627718a98f0",
        ),
        (
            (88, "058763c229d799beb9dc22294c71bdcbb5f686f041f432ded4052947f538b694"),
            (2_720, "fbe86f7568898a9776fe76adc85d06f1ceb6e52b11c910f1c39430ffd36a8a77"),
            (100, "f02340f78c1a493aaf1504f1c2dd20e86bdc12d495aebdd5ebe301c7c22364e5"),
        ),
        (
            18_828,
            "9d947412330464b966894b11b547c104ba4aa357730c51bde48617da62907c95",
        ),
        (1, 8, 64, 147),
        None,
        "teal-crested fin-armed demihuman",
    ),
}

PATIENT_ENTITY = 13
DOCTOR_ENTITY = foundation.DOCTOR_ENTITY
PATIENT_TARGET_BANK = 0
DOCTOR_BANK = 3
PATIENT_POSITION = (76, -16)
DOCTOR_POSITION = (76, 24)
PATIENT_TRIANGLE = 8
DOCTOR_TRIANGLE = 13
PATIENT_DIRECTION = 0
DOCTOR_DIRECTION = 4
ACTOR_INTERACTION_HALF_WIDTH = 0x10
ACTOR_INTERACTION_HALF_DEPTH = 0x10
ACTOR_BOUNDING_VOLUME = b"\x18\x10\x10\x00\x00"
ACTOR_STATIONARY_COLLISION_FLAGS = b"\x20\x0C\x80"
ACTOR_GHOST_COLLISION_FLAGS = b"\x20\x01\x80"
PATIENT_TARGET_MAPPING = (832, 0, 0, 0)
PATIENT_TARGET_ACTOR_COMPONENT_IDENTITY = foundation.SOURCE_COMPONENT_IDENTITIES[3]
PATIENT_TARGET_SPRITE_COMPONENT_IDENTITY = foundation.SOURCE_COMPONENT_IDENTITIES[4]
DOCTOR_ACTOR_IDENTITY = (
    2_396,
    "30636fcb252091e3c65c5fdc584f46fae31c66522d794570dc02b79e3a1c1559",
)
DOCTOR_SPRITE_IDENTITY = (
    26_764,
    "7c321cbd684a6205a779d10f01f5b832a10aeadb9edf60fb494e11c67544215a",
)

EXAM_ROOM_IDENTITIES = {
    spec.scene: surface.SourceIdentity(
        spec.scene,
        spec.target_bundle_id,
        spec.target_graphics_id,
        *SOURCE_BUNDLE_IDENTITY,
        *SOURCE_GRAPHICS_IDENTITY,
        *foundation.SOURCE_SCRIPT_IDENTITY,
        *foundation.SOURCE_HEADER_IDENTITY,
    )
    for spec in EXAM_ROOM_SPECS
}

# Field 352 owns 53 retail blocks (IDs 0..52); the authored terminal blocks are
# appended without modifying that dormant inventory.
SOURCE_DIALOGUE_COUNT = 53
EMPTY_ROOM_TERMINAL_DIALOGUE = (
    "PATIENT RECORD\n"
    "No patient is loaded\n"
    "for this room.<Close>"
)
EMPTY_ROOM_TERMINAL_DIALOGUE_ID = SOURCE_DIALOGUE_COUNT
TERMINAL_DIALOGUE_IDS_BY_SCENE = {
    591: (53,),
    592: (53,),
    593: (53, 54, 55, 56),
    594: (53,),
}
PATIENT_RECORD_DIALOGUE_IDS_BY_SCENE = {
    scene: dialogue_ids[2] if scene == 593 else dialogue_ids[0]
    for scene, dialogue_ids in TERMINAL_DIALOGUE_IDS_BY_SCENE.items()
}
DOCTOR_DIALOGUE_IDS_BY_SCENE = {
    scene: SOURCE_DIALOGUE_COUNT + len(spec.terminal_dialogues)
    for scene, spec in EXAM_ROOM_BY_SCENE.items()
}
PATIENT_DIALOGUE_IDS_BY_SCENE = {
    scene: DOCTOR_DIALOGUE_IDS_BY_SCENE[scene] + 1
    for scene in SCENES
}
FINAL_DIALOGUE_COUNTS_BY_SCENE = {
    scene: PATIENT_DIALOGUE_IDS_BY_SCENE[scene] + 1
    for scene in SCENES
}

# Starting from the frozen empty-clinic foundation (bytecode size 0x06B5), the
# variant return action is appended first so every room presents the same door
# route PC to the later collision-clearance layer.
RETURN_ACTION_PC = 0x06B5
TERMINAL_INIT_PC = 0x06C3
TERMINAL_ACTION_PC = 0x06E0
EMPTY_ROOM_TERMINAL_INIT_PC = 0x06B5
EMPTY_ROOM_TERMINAL_ACTION_PC = 0x06D2
TERMINAL_AUX_INIT_PCS = (0x044E, 0x046B)
EMPTY_ROOM_TERMINAL_ENTITIES = (4, 5, 6)
EMPTY_ROOM_TERMINAL_INIT_PCS = (
    *TERMINAL_AUX_INIT_PCS,
    EMPTY_ROOM_TERMINAL_INIT_PC,
)
TERMINAL_AUX_CAVITY_END_PC = 0x04A5
TERMINAL_AUX_CAVITY_SOURCE_IDENTITY = (
    87,
    "85581a31b32134e75912714f1e71cbe0957721e289f114f954a98ed7c4ca8824",
)
TERMINAL_ACTION_LENGTHS_BY_SCENE = {591: 39, 592: 39, 593: 101, 594: 39}
TERMINAL_ACTION_SHA256_BY_SCENE = {
    591: "ffafd3a2127c0e5c894007224545e9325a4b65f0a06ce5be8fe2f84a28b9a85c",
    592: "ffafd3a2127c0e5c894007224545e9325a4b65f0a06ce5be8fe2f84a28b9a85c",
    593: "178e0251af24d952cb69071f49c15842f0f7d0963b0e8558db2c8760f1c944de",
    594: "ffafd3a2127c0e5c894007224545e9325a4b65f0a06ce5be8fe2f84a28b9a85c",
}
EMPTY_ROOM_TERMINAL_ACTION_IDENTITY = (
    39,
    "4af5b82701e6732faf51b5f6f661a93d52787c79b8b113aeb4e7bb2cf165616b",
)
EMPTY_ROOM_TERMINAL_SCRIPT_IDENTITY = (
    3_133,
    "fe55b3dd734676017273713647c0fe8f5c45efbb899dcbb16d54f2ff9e190fde",
)
EMPTY_ROOM_TERMINAL_DIALOGUE_IDENTITY = (
    5_232,
    "2f15ffdeda92ec407a983737cd0acf550856725718b4fb6a05df046e47f2d8fd",
)
EMPTY_ROOM_TERMINAL_HEADER_IDENTITY = (
    928,
    "f50f5ceb1f7069443fe2a8e26145ae60c604ad0785ef8569c9dfd84272ef1a31",
)
EMPTY_ROOM_TERMINAL_BUNDLE_IDENTITY = (
    83_468,
    "1b4e40d5077fbc07cd621340f2074f77dcd42d986370447996b14c71173d5695",
)

FINAL_SCRIPT_IDENTITIES = {
    591: (
        3_307,
        "d77d3f6ca53d6e080e59915f28ad88989335072af5016057c7e64917617ac4c9",
    ),
    592: (
        3_307,
        "725cae9270e6b26a5d9a2094860d235118dc0391890cbb9f94bbf369a8184f4f",
    ),
    593: (
        3_367,
        "c1a41523fed6559190f5a4f79db6460a04b86432fb8d77d67997e8030074ad67",
    ),
    594: (
        3_305,
        "797b41a6d9f83da6d5aeff03f04709061f6a4ed13ab6e45cf914a50bf694ed4c",
    ),
}
FINAL_DIALOGUE_IDENTITIES = {
    591: (
        5_547,
        "f17545e5f7dce86a4fd857341428ec6dfcc454a77641f92d6a6693fadfcf00ef",
    ),
    592: (
        5_551,
        "c774f221679530eca7b78cdcd0c0686cab9d281fc1048419c992c45de8cf1eb9",
    ),
    593: (
        5_766,
        "92d7f6d9ab86a53e8cabd300bc7bb84d8bbb04142f9aa9c4f91a9bd5578b828e",
    ),
    594: (
        5_550,
        "699a16a2e6764a798109fbe89e530a7e07876454357c048e65437a927f0d6829",
    ),
}
FINAL_HEADER_IDENTITIES = {
    591: (
        944,
        "d34da2b5c92e2ff9aa475f29dd1bbc746a36807943335bc8daf1163b0babc266",
    ),
    592: (
        944,
        "d723ef75cf4b97cc71fa4de0af59f71b76d2db0d2d245a7dd4d323dc3a5caf73",
    ),
    593: (
        944,
        "2661db51760ccf2d2f4cee720b0471551c7bd70d40b0c3f62d5add0f6cb81292",
    ),
    594: (
        944,
        "34bc5e44e539500f91e1ee6a4e464e42875941330df97fea51b96fe714806f9c",
    ),
}
FINAL_BUNDLE_IDENTITIES = {
    591: (
        63_560,
        "ece9e9eee5c5a3923ef5da59e9c881bde80ced2273a071ba8fd3c5b34a9c0185",
    ),
    592: (
        64_104,
        "bf223119db14d7fec7a7c343c8ac410ad2bd6690de41c2cee3f8408c1eb46b14",
    ),
    593: (
        69_596,
        "8131044ac16631ed032428341c14b5b8271878f0b04eac1bbc79b90cd7d6006b",
    ),
    594: (
        72_044,
        "ed9ac03d03d0575846943cd933be5b7b8e0cfb51ecc5f3959ceabf11f8c95934",
    ),
}
FINAL_ACTOR_COMPONENT_IDENTITIES = {
    591: (10_548, "f699333147359a01c99170273e32e93c556e473d0ebd45be607f69346d0eabe6"),
    592: (10_552, "ff6edbf9a50f11aafb10cd0c8a0411ddf23063945120b63f0f10bb902438650d"),
    593: (11_780, "da7c4b0be3e22c756a122a56502b9322d61dfc9afd9c005c1a35b2df678c51d7"),
    594: (11_968, "f97589669d0ddfcd6aeb1239903c0bbdda006e796c698f3eb48dc03ac1f4f8fb"),
}
FINAL_SPRITE_COMPONENT_IDENTITIES = {
    591: (64_708, "1829b542c0aedda40f945423befa5051e28df03d5466a9075b0c28d0abe11ec5"),
    592: (64_068, "5d973f44a8bdfc08a4ffc7e546f43810920a3a23c6e45e60418be24268de1c3c"),
    593: (72_004, "2c8bcfb42b4f4c8dc097e40e0e7d21231787a0ebdcf916c9337cd2a55ff47185"),
    594: (74_180, "4b069f27b29b0f2d233efb2ce12aa8dba7d167f353b6b2668ef1b3c8b881ffce"),
}
FINAL_ENCOUNTER_IDENTITY = foundation.FINAL_ENCOUNTER_IDENTITY


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _identity(data: bytes) -> tuple[int, str]:
    return len(data), _sha256(data)


def _u16(value: int) -> bytes:
    if not 0 <= value <= 0xFFFF:
        raise surface.SurfaceSoylentBuildError(
            f"Exam-room u16 value is outside range: {value}"
        )
    return struct.pack("<H", value)


def _s16(value: int) -> bytes:
    if not -0x8000 <= value <= 0x7FFF:
        raise surface.SurfaceSoylentBuildError(
            f"Exam-room s16 value is outside range: {value}"
        )
    return struct.pack("<h", value)


def _set_bit(operand: int, bit_index: int) -> bytes:
    return b"\x3A" + _u16(operand) + _u16(bit_index) + b"\x40"


def load_patient_assets(
    source_disc: Path | str,
) -> dict[int, LoadedPatientAsset]:
    """Load four exact native Soylent demihuman actor/sprite pairs."""

    image = Mode2Image(source_disc)
    entries = image.read_index()
    directories = image.read_directories()
    if FIELD_DIRECTORY >= len(directories):
        raise surface.SurfaceSoylentBuildError(
            "Disc 2 field directory is absent while loading treatment patients"
        )
    first = directories[FIELD_DIRECTORY].first_file
    parsed_by_scene: dict[int, object] = {}
    for source_scene, (
        expected_canonical_id,
        expected_size,
        expected_sha256,
    ) in PATIENT_SOURCE_BUNDLE_IDENTITIES.items():
        local = FIRST_FIELD_LOCAL_FILE + 2 * source_scene
        fat_index = directory_file_fat_index(first, local)
        if (
            fat_index + 5 != expected_canonical_id
            or not 0 <= fat_index < len(entries)
        ):
            raise surface.SurfaceSoylentBuildError(
                f"Soylent patient field {source_scene} resolved to the wrong "
                "canonical resource"
            )
        bundle = image.extract_entry(entries[fat_index])
        if _identity(bundle) != (expected_size, expected_sha256):
            raise surface.SurfaceSoylentBuildError(
                f"Soylent patient field {source_scene} donor changed"
            )
        parsed_by_scene[source_scene] = parse_field(bundle)

    result: dict[int, LoadedPatientAsset] = {}
    for target_scene, spec in PATIENT_ASSET_SPECS.items():
        parsed = parsed_by_scene[spec.source_scene]
        actors = surface.mass_driver._indexed_bundle_entries(
            parsed.parts[surface.mass_driver.ACTOR_INDEX].data
        )
        sprites = surface.mass_driver._indexed_bundle_entries(
            parsed.parts[surface.mass_driver.SPRITE_INDEX].data
        )
        if not 0 <= spec.source_bank < min(len(actors), len(sprites)):
            raise surface.SurfaceSoylentBuildError(
                f"Field {spec.source_scene} demihuman bank {spec.source_bank} moved"
            )
        actor = actors[spec.source_bank]
        sprite = sprites[spec.source_bank]
        actor_sections = surface.mass_driver._indexed_bundle_entries(actor)
        mapping = struct.unpack_from(
            "<4H", parsed.header, spec.source_bank * 8
        )
        if (
            mapping != spec.source_mapping
            or _identity(actor) != spec.actor_identity
            or tuple(_identity(section) for section in actor_sections)
            != spec.actor_section_identities
            or _identity(sprite) != spec.sprite_identity
            or len(sprite) < 12
            or struct.unpack_from("<IIHH", sprite) != spec.sprite_header
            or spec.sprite_header[0] != 1
            or spec.sprite_header[2] != 64
        ):
            raise surface.SurfaceSoylentBuildError(
                f"Field {spec.source_scene} demihuman bank "
                f"{spec.source_bank} changed"
            )
        result[target_scene] = LoadedPatientAsset(spec, actor, sprite)

    if (
        set(result) != set(SCENES)
        or len({asset.spec.actor_identity[1] for asset in result.values()})
        != len(SCENES)
        or len({asset.spec.sprite_identity[1] for asset in result.values()})
        != len(SCENES)
    ):
        raise surface.SurfaceSoylentBuildError(
            "Treatment-room demihuman inventory is not four distinct banks"
        )
    return result


def _install_patient_asset(
    header: bytes,
    components: Sequence[bytes],
    asset: LoadedPatientAsset,
) -> tuple[bytes, bytes]:
    """Replace only retired field-352 bank 0 with one patient pair."""

    actor_index = surface.mass_driver.ACTOR_INDEX
    sprite_index = surface.mass_driver.SPRITE_INDEX
    if (
        _identity(components[actor_index])
        != PATIENT_TARGET_ACTOR_COMPONENT_IDENTITY
        or _identity(components[sprite_index])
        != PATIENT_TARGET_SPRITE_COMPONENT_IDENTITY
        or struct.unpack_from("<4H", header, PATIENT_TARGET_BANK * 8)
        != PATIENT_TARGET_MAPPING
    ):
        raise surface.SurfaceSoylentBuildError(
            "Field-352 treatment-patient bank destination changed"
        )
    actors = list(
        surface.mass_driver._indexed_bundle_entries(components[actor_index])
    )
    sprites = list(
        surface.mass_driver._indexed_bundle_entries(components[sprite_index])
    )
    if len(actors) != 4 or len(sprites) != 4:
        raise surface.SurfaceSoylentBuildError(
            "Field-352 treatment-room actor inventory changed"
        )
    if (
        _identity(actors[DOCTOR_BANK]) != DOCTOR_ACTOR_IDENTITY
        or _identity(sprites[DOCTOR_BANK]) != DOCTOR_SPRITE_IDENTITY
    ):
        raise surface.SurfaceSoylentBuildError(
            "Field-352 physician bank changed before patient installation"
        )
    actors[PATIENT_TARGET_BANK] = asset.actor
    sprites[PATIENT_TARGET_BANK] = asset.sprite
    actor_component = surface.mass_driver._rebuild_indexed_bundle(
        components[actor_index], actors
    )
    sprite_component = surface.mass_driver._rebuild_indexed_bundle(
        components[sprite_index], sprites
    )
    reparsed_actors = surface.mass_driver._indexed_bundle_entries(actor_component)
    reparsed_sprites = surface.mass_driver._indexed_bundle_entries(sprite_component)
    if (
        reparsed_actors[PATIENT_TARGET_BANK] != asset.actor
        or reparsed_sprites[PATIENT_TARGET_BANK] != asset.sprite
        or _identity(reparsed_actors[DOCTOR_BANK]) != DOCTOR_ACTOR_IDENTITY
        or _identity(reparsed_sprites[DOCTOR_BANK]) != DOCTOR_SPRITE_IDENTITY
    ):
        raise surface.SurfaceSoylentBuildError(
            f"Field {asset.spec.target_scene} patient bank did not install exactly"
        )
    return actor_component, sprite_component


def _stationary_actor_init(
    *,
    entity: int,
    graphic: int,
    position: tuple[int, int],
    direction: int,
    animation: int | None = None,
    establish_mutual_facing: bool = False,
) -> bytes:
    """Create one visible, solid bedside actor without ambient wandering."""

    body = (
        b"\x0B"
        + bytes((graphic, 0x80))
        + b"\x19"
        + _s16(position[0])
        + _s16(position[1])
        + b"\xC0\x1A\x00\x69"
        + bytes((direction, 0x80))
        + b"\xF8\x00\x00\x20\xF8\x07\x04\x00"
        + ACTOR_BOUNDING_VOLUME
        + ACTOR_STATIONARY_COLLISION_FLAGS
    )
    if animation is not None:
        if not 0 <= animation <= 0xFF:
            raise surface.SurfaceSoylentBuildError(
                f"Treatment-patient animation is invalid: {animation}"
            )
        body += b"\x2C" + bytes((animation,))
    if establish_mutual_facing:
        body += (
            b"\xFE\x17"
            + bytes((DOCTOR_ENTITY, PATIENT_ENTITY))
            + b"\xFE\x17"
            + bytes((PATIENT_ENTITY, DOCTOR_ENTITY))
        )
    return body + b"\x00"


def _stationary_actor_action(
    *,
    entity: int,
    counterpart: int,
    dialogue_id: int,
) -> bytes:
    """Face Fei for one native talk window, then resume the treatment pose."""

    return (
        b"\x6F\xFF\xD2"
        + _u16(dialogue_id)
        + b"\x00\x9C\xFE\x17"
        + bytes((entity, counterpart))
        + b"\x00"
    )


def _terminal_init_body(position: tuple[int, int]) -> bytes:
    """Create one facing-gated, non-colliding side-bank X carrier."""

    return (
        b"\x0B\x00\x80"
        + b"\x19"
        + _s16(position[0])
        + _s16(position[1])
        + b"\xC0\x1A\x00"
        + b"\xF8\x00\x00\x20"
        + (
            b"\xF8\x03\x04\x00"
            if TERMINAL_REQUIRES_FACING
            else b"\xF8\x07\x04\x00"
        )
        + b"\x18"
        + bytes(
            (
                TERMINAL_INTERACTION_HALF_WIDTH,
                TERMINAL_INTERACTION_HALF_DEPTH,
                0x64,
                min(
                    TERMINAL_INTERACTION_HALF_WIDTH,
                    TERMINAL_INTERACTION_HALF_DEPTH,
                ),
            )
        )
        + b"\x20\x01\x80\x23\x00"
    )


TERMINAL_INIT_BODIES = tuple(
    _terminal_init_body(position) for position in TERMINAL_POSITIONS
)
TERMINAL_INIT_BODY = TERMINAL_INIT_BODIES[0]
TERMINAL_AUX_CAVITY = (
    b"".join(TERMINAL_INIT_BODIES[1:])
    + b"\x00"
    * (
        TERMINAL_AUX_CAVITY_END_PC
        - TERMINAL_AUX_INIT_PCS[0]
        - sum(len(body) for body in TERMINAL_INIT_BODIES[1:])
    )
)
EMPTY_ROOM_TERMINAL_AUX_CAVITY = (
    b"".join(TERMINAL_INIT_BODIES[:2])
    + b"\x00"
    * (
        TERMINAL_AUX_CAVITY_END_PC
        - TERMINAL_AUX_INIT_PCS[0]
        - sum(len(body) for body in TERMINAL_INIT_BODIES[:2])
    )
)
EMPTY_ROOM_TERMINAL_AUX_CAVITY_IDENTITY = (
    87,
    "dd87cc07ee6313fe77431e34af52c9158d41a59498f9abf056013feac490a400",
)


def _install_terminal_aux_initializers(editor: ScriptEditor) -> ScriptEditor:
    """Use one checked dormant cavity for the two extra frontage carriers."""

    cavity_start = TERMINAL_AUX_INIT_PCS[0]
    cavity = editor.bytecode[cavity_start:TERMINAL_AUX_CAVITY_END_PC]
    if _identity(cavity) != TERMINAL_AUX_CAVITY_SOURCE_IDENTITY:
        raise surface.SurfaceSoylentBuildError(
            "Field-352 dormant terminal-carrier cavity changed"
        )
    payload = TERMINAL_AUX_CAVITY
    if (
        tuple(
            cavity_start + index * len(TERMINAL_INIT_BODY)
            for index in range(len(TERMINAL_AUX_ENTITIES))
        )
        != TERMINAL_AUX_INIT_PCS
        or len(payload) != len(cavity)
    ):
        raise surface.SurfaceSoylentBuildError(
            "Examination-room terminal-carrier cavity no longer fits"
        )
    data = bytearray(editor.to_bytes())
    start = editor.bytecode_offset + cavity_start
    data[start : start + len(cavity)] = payload
    patched = ScriptEditor(data)
    for entity, pc in zip(
        TERMINAL_AUX_ENTITIES,
        TERMINAL_AUX_INIT_PCS,
        strict=True,
    ):
        patched.set_script_pointer(entity, 0, pc)
    return patched


def _install_empty_room_terminal_aux_initializers(
    editor: ScriptEditor,
) -> ScriptEditor:
    """Put field 567's first two carriers in the checked dormant cavity."""

    cavity_start = TERMINAL_AUX_INIT_PCS[0]
    cavity = editor.bytecode[cavity_start:TERMINAL_AUX_CAVITY_END_PC]
    if _identity(cavity) != TERMINAL_AUX_CAVITY_SOURCE_IDENTITY:
        raise surface.SurfaceSoylentBuildError(
            "Field-352 dormant empty-terminal cavity changed"
        )
    if (
        len(EMPTY_ROOM_TERMINAL_AUX_CAVITY) != len(cavity)
        or _identity(EMPTY_ROOM_TERMINAL_AUX_CAVITY)
        != EMPTY_ROOM_TERMINAL_AUX_CAVITY_IDENTITY
    ):
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-terminal carrier cavity no longer fits"
        )
    data = bytearray(editor.to_bytes())
    start = editor.bytecode_offset + cavity_start
    data[start : start + len(cavity)] = EMPTY_ROOM_TERMINAL_AUX_CAVITY
    patched = ScriptEditor(data)
    for entity, pc in zip(
        EMPTY_ROOM_TERMINAL_ENTITIES[:2],
        TERMINAL_AUX_INIT_PCS,
        strict=True,
    ):
        patched.set_script_pointer(entity, 0, pc)
    return patched


def _repeatable_terminal_action(dialogue_id: int, routine_pc: int) -> bytes:
    opening_release_pc = routine_pc + 3
    prefix = (
        b"\x33\xFE\x54"
        + surface.mass_driver._wait_for_pad_release(
            surface.mass_driver.PAD_MASK_CROSS,
            opening_release_pc,
        )
        + b"\x26\x01\x80"
        + b"\xF5"
        + _u16(dialogue_id)
        + b"\x01\x9C"
    )
    # WAIT_DIALOG returns while the Cross press that closed the window may
    # still be physically held.  Drain that edge before restoring field
    # control so one deliberate interaction produces exactly one readout.
    closing_release_pc = routine_pc + len(prefix)
    return (
        prefix
        + surface.mass_driver._wait_for_pad_release(
            surface.mass_driver.PAD_MASK_CROSS,
            closing_release_pc,
        )
        + surface.mass_driver._wait()
        + b"\xFE\x53\x00"
    )


def _install_empty_room_terminal_scripts(
    script: bytes,
    dialogue_id: int,
) -> bytes:
    """Add the side-bank readout without reviving any field-352 NPC."""

    foundation_editor = ScriptEditor(script)
    if (
        foundation_editor.entity_count != SOURCE_ENTITY_COUNT
        or foundation_editor.bytecode_size != EMPTY_ROOM_TERMINAL_INIT_PC
        or foundation_editor.get_script_pointer(RETURN_CONTROLLER, 2)
        != foundation.RETURN_CONTROLLER_ACTION_PC
    ):
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-clinic script changed before terminal installation"
        )

    editor = _install_empty_room_terminal_aux_initializers(
        ScriptEditor(script)
    )

    terminal_init_pc = editor.append_and_repoint(
        EMPTY_ROOM_TERMINAL_ENTITIES[2],
        0,
        TERMINAL_INIT_BODIES[2],
    )
    terminal_action_pc = editor.bytecode_size
    action = _repeatable_terminal_action(dialogue_id, terminal_action_pc)
    installed_action_pc = editor.append_and_repoint(
        EMPTY_ROOM_TERMINAL_ENTITIES[2],
        2,
        action,
    )
    for entity in EMPTY_ROOM_TERMINAL_ENTITIES[:2]:
        editor.set_script_pointer(entity, 2, installed_action_pc)

    if (terminal_init_pc, terminal_action_pc, installed_action_pc) != (
        EMPTY_ROOM_TERMINAL_INIT_PC,
        EMPTY_ROOM_TERMINAL_ACTION_PC,
        EMPTY_ROOM_TERMINAL_ACTION_PC,
    ):
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-room terminal routine layout changed"
        )
    if _identity(action) != EMPTY_ROOM_TERMINAL_ACTION_IDENTITY:
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-room terminal action changed"
        )

    active_slots = foundation.FINAL_ACTIVE_SLOTS | {
        *((entity, slot) for entity in EMPTY_ROOM_TERMINAL_ENTITIES for slot in (0, 2)),
    }
    for entity in range(editor.entity_count):
        for script_index in range(32):
            pointer = editor.get_script_pointer(entity, script_index)
            if (entity, script_index) not in active_slots and pointer != SHARED_STOP_PC:
                raise surface.SurfaceSoylentBuildError(
                    f"Field 567 e{entity}:s{script_index} escaped empty-room "
                    "retirement"
                )
    if (
        editor.get_script_pointer(RETURN_CONTROLLER, 2)
        != foundation.RETURN_CONTROLLER_ACTION_PC
        or editor.bytecode[
            foundation.RETURN_CONTROLLER_ACTION_PC :
            foundation.RETURN_CONTROLLER_ACTION_PC + len(foundation.RETURN_ACTION)
        ]
        != foundation.RETURN_ACTION
    ):
        raise surface.SurfaceSoylentBuildError(
            "Field 567 terminal changed the native return action"
        )
    return editor.to_bytes()


def _keycard_terminal_action(
    *,
    inserted_dialogue_id: int,
    acquired_dialogue_id: int,
    diagnostics_dialogue_id: int,
    choice_dialogue_id: int,
    routine_pc: int,
) -> bytes:
    """Offer, conditionally remove, and persist the Quarantine keycard."""

    routine = surface.mass_driver._RoutineBuilder(routine_pc)
    routine.emit(b"\x33\xFE\x54")
    initial_release_pc = routine.pc
    routine.emit(
        surface.mass_driver._wait_for_pad_release(
            surface.mass_driver.PAD_MASK_CROSS,
            initial_release_pc,
        )
    )
    routine.jump_if_bit_clear(
        QUARANTINE_KEYCARD_OPERAND,
        QUARANTINE_KEYCARD_MASK,
        "take_keycard",
    )

    routine.emit(b"\x26\x01\x80")
    routine.emit(b"\xF5" + _u16(diagnostics_dialogue_id) + b"\x01\x9C")
    routine.jump("finish")

    routine.label("take_keycard")
    routine.emit(b"\x26\x01\x80")
    # Keep the descriptive call and WAIT_DIALOG at their V214 addresses.  The
    # user's captured Slot 1 is paused on that exact WAIT_DIALOG, so the new
    # choice can follow it without skipping or replaying progression.
    routine.emit(b"\xF5" + _u16(inserted_dialogue_id) + b"\x01\x9C")
    description_release_pc = routine.pc
    routine.emit(
        surface.mass_driver._wait_for_pad_release(
            surface.mass_driver.PAD_MASK_CROSS,
            description_release_pc,
        )
    )
    routine.emit(surface.mass_driver._wait())
    # The title occupies absolute line zero, so WAIT_DIALOG records Accept as
    # line one and Leave as line two in field variable 0x0014.  Declining
    # restores control without a sound, receipt, or progression write, leaving
    # the physical card available on the next interaction.
    routine.emit(surface.mass_driver._choice_dialog(choice_dialogue_id))
    routine.emit(b"\xA9\x12\x9C")
    routine.jump_if_not_equal(0x0014, 1, "finish")
    # Drain the choice-confirmation edge before the acquisition receipt.
    accepted_release_pc = routine.pc
    routine.emit(
        surface.mass_driver._wait_for_pad_release(
            surface.mass_driver.PAD_MASK_CROSS,
            accepted_release_pc,
        )
    )
    routine.emit(surface.mass_driver._wait())
    routine.emit(ITEM_ACQUISITION_SOUND)
    routine.emit(b"\xF5" + _u16(acquired_dialogue_id) + b"\x01\x9C")
    # Commit only after the acquisition receipt closes.  A state interrupted
    # earlier may safely replay the receipt but cannot unlock progression
    # without visibly completing the pickup.
    routine.emit(
        _set_bit(
            QUARANTINE_KEYCARD_OPERAND,
            QUARANTINE_KEYCARD_BIT_INDEX,
        )
    )

    routine.label("finish")
    routine.emit(b"\xFE\x53\x00")
    return routine.finish()


PATIENT_INIT_BODIES_BY_SCENE = {
    scene: _stationary_actor_init(
        entity=PATIENT_ENTITY,
        graphic=PATIENT_TARGET_BANK,
        position=PATIENT_POSITION,
        direction=PATIENT_DIRECTION,
        animation=PATIENT_ASSET_SPECS[scene].treatment_animation,
    )
    for scene in SCENES
}
DOCTOR_INIT_BODY = _stationary_actor_init(
    entity=DOCTOR_ENTITY,
    graphic=DOCTOR_BANK,
    position=DOCTOR_POSITION,
    direction=DOCTOR_DIRECTION,
    establish_mutual_facing=True,
)
PATIENT_ACTION_BODIES_BY_SCENE = {
    scene: _stationary_actor_action(
        entity=PATIENT_ENTITY,
        counterpart=DOCTOR_ENTITY,
        dialogue_id=PATIENT_DIALOGUE_IDS_BY_SCENE[scene],
    )
    for scene in SCENES
}
DOCTOR_ACTION_BODIES_BY_SCENE = {
    scene: _stationary_actor_action(
        entity=DOCTOR_ENTITY,
        counterpart=PATIENT_ENTITY,
        dialogue_id=DOCTOR_DIALOGUE_IDS_BY_SCENE[scene],
    )
    for scene in SCENES
}


def _npc_routine_layout(scene: int) -> dict[str, int]:
    """Return the exact append-only treatment-actor PC layout."""

    pc = TERMINAL_ACTION_PC + TERMINAL_ACTION_LENGTHS_BY_SCENE[scene]
    result = {"patient_init": pc}
    pc += len(PATIENT_INIT_BODIES_BY_SCENE[scene])
    result["doctor_init"] = pc
    pc += len(DOCTOR_INIT_BODY)
    result["patient_action"] = pc
    pc += len(PATIENT_ACTION_BODIES_BY_SCENE[scene])
    result["doctor_action"] = pc
    pc += len(DOCTOR_ACTION_BODIES_BY_SCENE[scene])
    result["end"] = pc
    return result


NPC_ROUTINE_PCS_BY_SCENE = {
    scene: _npc_routine_layout(scene)
    for scene in SCENES
}


def _append_dialogue(
    dialogue: bytes,
    texts: Sequence[str],
    *,
    width: int = 58,
    height: int = 4,
) -> tuple[bytes, tuple[int, ...]]:
    parsed = parse_dialogue(dialogue)
    specs = [
        DialogueBlockSpec(block.block_id, block.width, block.height, block.text)
        for block in parsed.blocks
    ]
    ids: list[int] = []
    for text in texts:
        ids.append(len(specs))
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
                "Field-352 retail dialogue changed while adding an exam terminal"
            )
    return rebuilt, tuple(ids)


def _return_action(return_parameter: int) -> bytes:
    return (
        b"\xFE\x54\x74\x77\x80"
        + b"\x09"
        + bytes((RETURN_HELPER, 0xC4))
        + surface._change_field(RETURN_FIELD, return_parameter)
        + b"\x00"
    )


def _insert_terminal_header_record(header: bytes) -> bytes:
    if len(header) < 0x190:
        raise surface.SurfaceSoylentBuildError(
            "Field-352 exam-room header is truncated"
        )
    actor_count = struct.unpack_from("<H", header, 0x18C)[0]
    if (
        actor_count != SOURCE_HEADER_ACTOR_COUNT
        or len(header) != 0x190 + actor_count * 16
        or SOURCE_ENTITY_COUNT > actor_count
    ):
        raise surface.SurfaceSoylentBuildError(
            "Field-352 exam-room actor table boundary changed"
        )
    records = [
        header[0x190 + index * 16 : 0x190 + (index + 1) * 16]
        for index in range(actor_count)
    ]
    records.insert(TERMINAL_ENTITY, TERMINAL_HEADER_RECORD)
    result = bytearray(header[:0x190] + b"".join(records))
    struct.pack_into("<H", result, 0x18C, len(records))
    return bytes(result)


def _validate_treatment_pair_geometry(walkmesh: bytes) -> None:
    """Prove both solid actors occupy separate bedside floor and leave an aisle."""

    triangles = surface._walkmesh_layer(walkmesh, 0)
    hits = {
        label: tuple(
            index
            for index, triangle in enumerate(triangles)
            if surface._point_inside_triangle(position, triangle)
        )
        for label, position in (
            ("patient", PATIENT_POSITION),
            ("doctor", DOCTOR_POSITION),
        )
    }
    if hits != {
        "patient": (PATIENT_TRIANGLE,),
        "doctor": (DOCTOR_TRIANGLE,),
    }:
        raise surface.SurfaceSoylentBuildError(
            f"Treatment pair left audited bedside triangles: {hits}"
        )
    if (
        abs(DOCTOR_POSITION[1] - PATIENT_POSITION[1])
        < 2 * ACTOR_INTERACTION_HALF_DEPTH
        or abs(PATIENT_POSITION[1] - TERMINAL_POSITION[1])
        < ACTOR_INTERACTION_HALF_DEPTH + TERMINAL_INTERACTION_HALF_DEPTH
        or PATIENT_POSITION[0] + ACTOR_INTERACTION_HALF_WIDTH >= 108
        or DOCTOR_POSITION[0] + ACTOR_INTERACTION_HALF_WIDTH >= 108
    ):
        raise surface.SurfaceSoylentBuildError(
            "Treatment pair overlaps itself, the terminal, or the right-hand aisle"
        )


def _terminal_in_reach(
    point: tuple[float, float],
    position: tuple[int, int],
) -> bool:
    return (
        abs(point[0] - position[0]) <= TERMINAL_EFFECTIVE_HALF_REACH[0]
        and abs(point[1] - position[1]) <= TERMINAL_EFFECTIVE_HALF_REACH[1]
    )


def _terminal_target_yaw(
    point: tuple[float, float],
    position: tuple[int, int],
) -> int:
    engine_x, engine_z = (math.floor(axis) for axis in point)
    return (
        -surface.mass_driver._noah_ratan2(
            position[1] - engine_z,
            position[0] - engine_x,
        )
    ) & 0x0FFF


def _terminal_facing_accepts(
    point: tuple[float, float],
    position: tuple[int, int],
    yaw: int,
) -> bool:
    delta = (yaw - _terminal_target_yaw(point, position)) & 0x0FFF
    return delta < 700 or delta > 3396


def _validate_terminal_frontage_geometry(walkmesh: bytes) -> None:
    """Prove all real side-bank frontage works and the saved aisle does not."""

    triangles = surface._walkmesh_layer(walkmesh, TERMINAL_WALKMESH)
    operator_triangles = tuple(
        triangles[index] for index in TERMINAL_OPERATOR_TRIANGLES
    )
    # The carrier anchors deliberately sit on the static model's front plane,
    # just outside the walkmesh.  Fei occupies the adjacent operator floor.
    anchor_hits = tuple(
        tuple(
            index
            for index, triangle in enumerate(triangles)
            if surface._point_inside_triangle(position, triangle)
        )
        for position in TERMINAL_POSITIONS
    )
    if anchor_hits != ((), (), ()):
        raise surface.SurfaceSoylentBuildError(
            f"Side-bank terminal anchors entered the walkmesh: {anchor_hits}"
        )

    front_z = TERMINAL_POSITIONS[0][1]
    eligible = tuple(
        (x, z)
        for x in range(TERMINAL_FRONTAGE_X[0], TERMINAL_FRONTAGE_X[1] + 1)
        for z in range(
            front_z - TERMINAL_EFFECTIVE_HALF_REACH[1],
            front_z + TERMINAL_EFFECTIVE_HALF_REACH[1] + 1,
        )
        if any(
            surface._point_inside_triangle((x, z), triangle)
            for triangle in operator_triangles
        )
    )
    terminal_facing_coverage = tuple(
        point
        for point in eligible
        if any(
            _terminal_in_reach(point, position)
            and _terminal_facing_accepts(
                point,
                position,
                TERMINAL_APPROACH_YAW,
            )
            for position in TERMINAL_POSITIONS
        )
    )
    bed_facing_acceptance = tuple(
        (point, position)
        for point in eligible
        for position in TERMINAL_POSITIONS
        if _terminal_in_reach(point, position)
        and _terminal_facing_accepts(point, position, TERMINAL_BED_YAW)
    )
    if (
        len(eligible) != 1_201
        or terminal_facing_coverage != eligible
        or bed_facing_acceptance
        or not any(
            _terminal_in_reach(TERMINAL_APPROACH_FIXTURE, position)
            and _terminal_facing_accepts(
                TERMINAL_APPROACH_FIXTURE,
                position,
                TERMINAL_APPROACH_YAW,
            )
            for position in TERMINAL_POSITIONS
        )
        or any(
            _terminal_in_reach(TERMINAL_REJECTED_AISLE_FIXTURE, position)
            for position in TERMINAL_POSITIONS
        )
    ):
        raise surface.SurfaceSoylentBuildError(
            "Examination-room terminal frontage coverage changed"
        )


def _validate_private_dialogue(
    scene: int,
    dialogue: bytes,
) -> None:
    """Keep the private warnings distinct and the patients pre-revelation."""

    parsed = parse_dialogue(dialogue)
    if len(parsed.blocks) != FINAL_DIALOGUE_COUNTS_BY_SCENE[scene]:
        raise surface.SurfaceSoylentBuildError(
            f"Field {scene} treatment dialogue count changed"
        )
    doctor = parsed.blocks[DOCTOR_DIALOGUE_IDS_BY_SCENE[scene]]
    patient = parsed.blocks[PATIENT_DIALOGUE_IDS_BY_SCENE[scene]]
    if (
        doctor.text != DOCTOR_DIALOGUES_BY_SCENE[scene]
        or patient.text != PATIENT_DIALOGUES_BY_SCENE[scene]
        or len(set(DOCTOR_DIALOGUES_BY_SCENE.values())) != len(SCENES)
        or len(set(PATIENT_DIALOGUES_BY_SCENE.values())) != len(SCENES)
        or any(
            word in patient.text.casefold()
            for word in (
                "soylent",
                "sufal",
                "mass",
                "processing",
                "food",
                "kill",
                "death",
            )
        )
    ):
        raise surface.SurfaceSoylentBuildError(
            f"Field {scene} private-treatment dialogue contract changed"
        )
    terminal_blocks = tuple(
        parsed.blocks[dialogue_id]
        for dialogue_id in TERMINAL_DIALOGUE_IDS_BY_SCENE[scene]
    )
    if tuple(block.text for block in terminal_blocks) != EXAM_ROOM_BY_SCENE[
        scene
    ].terminal_dialogues:
        raise surface.SurfaceSoylentBuildError(
            f"Field {scene} patient-record terminal dialogue changed"
        )
    for block in (*terminal_blocks, doctor, patient):
        surface.mass_driver._validate_authored_manual_wrap(
            {
                "manual_wrap": True,
                "width": block.width,
                "height": block.height,
                "text": block.text,
            },
            block.block_id,
        )


def _install_exam_room_scripts(
    script: bytes,
    spec: ExamRoomSpec,
    dialogue_ids: tuple[int, ...],
) -> bytes:
    foundation_editor = ScriptEditor(script)
    if (
        foundation_editor.entity_count != SOURCE_ENTITY_COUNT
        or foundation_editor.bytecode_size != RETURN_ACTION_PC
        or foundation_editor.get_script_pointer(RETURN_CONTROLLER, 2)
        != foundation.RETURN_CONTROLLER_ACTION_PC
    ):
        raise surface.SurfaceSoylentBuildError(
            "Empty-clinic script foundation changed before exam-room installation"
        )

    editor = ScriptEditor(
        surface.mass_driver._extend_atel_entity_table(script, ENTITY_COUNT)
    )
    for script_index in range(32):
        editor.set_script_pointer(TERMINAL_ENTITY, script_index, SHARED_STOP_PC)
    editor = _install_terminal_aux_initializers(editor)

    return_action_pc = editor.append_and_repoint(
        RETURN_CONTROLLER,
        2,
        _return_action(spec.return_parameter),
    )
    terminal_init_pc = editor.append_and_repoint(
        TERMINAL_ENTITY,
        0,
        TERMINAL_INIT_BODY,
    )
    terminal_action_pc = editor.bytecode_size
    terminal_count = len(spec.terminal_dialogues)
    terminal_dialogue_ids = dialogue_ids[:terminal_count]
    npc_dialogue_ids = dialogue_ids[terminal_count:]
    if (
        terminal_dialogue_ids != TERMINAL_DIALOGUE_IDS_BY_SCENE[spec.scene]
        or npc_dialogue_ids
        != (
            DOCTOR_DIALOGUE_IDS_BY_SCENE[spec.scene],
            PATIENT_DIALOGUE_IDS_BY_SCENE[spec.scene],
        )
    ):
        raise surface.SurfaceSoylentBuildError(
            f"Field {spec.scene} treatment-room dialogue layout changed"
        )
    if spec.awards_quarantine_keycard:
        if len(terminal_dialogue_ids) != 4:
            raise surface.SurfaceSoylentBuildError(
                f"Field {spec.scene} keycard terminal dialogue contract changed"
            )
        action = _keycard_terminal_action(
            inserted_dialogue_id=terminal_dialogue_ids[0],
            acquired_dialogue_id=terminal_dialogue_ids[1],
            diagnostics_dialogue_id=terminal_dialogue_ids[2],
            choice_dialogue_id=terminal_dialogue_ids[3],
            routine_pc=terminal_action_pc,
        )
    else:
        if len(terminal_dialogue_ids) != 1:
            raise surface.SurfaceSoylentBuildError(
                f"Field {spec.scene} clinical terminal dialogue contract changed"
            )
        action = _repeatable_terminal_action(
            terminal_dialogue_ids[0], terminal_action_pc
        )
    installed_action_pc = editor.append_and_repoint(
        TERMINAL_ENTITY,
        2,
        action,
    )
    for entity in TERMINAL_AUX_ENTITIES:
        editor.set_script_pointer(entity, 2, installed_action_pc)
    if (return_action_pc, terminal_init_pc, installed_action_pc) != (
        RETURN_ACTION_PC,
        TERMINAL_INIT_PC,
        TERMINAL_ACTION_PC,
    ):
        raise surface.SurfaceSoylentBuildError(
            f"Field {spec.scene} exam-room routine layout changed"
        )
    if (
        len(action) != TERMINAL_ACTION_LENGTHS_BY_SCENE[spec.scene]
        or _sha256(action) != TERMINAL_ACTION_SHA256_BY_SCENE[spec.scene]
    ):
        raise surface.SurfaceSoylentBuildError(
            f"Field {spec.scene} exam-terminal action changed"
        )

    patient_init_pc = editor.append_and_repoint(
        PATIENT_ENTITY,
        0,
        PATIENT_INIT_BODIES_BY_SCENE[spec.scene],
    )
    doctor_init_pc = editor.append_and_repoint(
        DOCTOR_ENTITY,
        0,
        DOCTOR_INIT_BODY,
    )
    patient_action_pc = editor.append_and_repoint(
        PATIENT_ENTITY,
        2,
        PATIENT_ACTION_BODIES_BY_SCENE[spec.scene],
    )
    doctor_action_pc = editor.append_and_repoint(
        DOCTOR_ENTITY,
        2,
        DOCTOR_ACTION_BODIES_BY_SCENE[spec.scene],
    )
    layout = NPC_ROUTINE_PCS_BY_SCENE[spec.scene]
    if (
        patient_init_pc,
        doctor_init_pc,
        patient_action_pc,
        doctor_action_pc,
        editor.bytecode_size,
    ) != (
        layout["patient_init"],
        layout["doctor_init"],
        layout["patient_action"],
        layout["doctor_action"],
        layout["end"],
    ):
        raise surface.SurfaceSoylentBuildError(
            f"Field {spec.scene} treatment-actor routine layout changed"
        )

    active_slots = foundation.FINAL_ACTIVE_SLOTS | {
        *((entity, slot) for entity in TERMINAL_ENTITIES for slot in (0, 2)),
        (PATIENT_ENTITY, 0),
        (PATIENT_ENTITY, 2),
        (DOCTOR_ENTITY, 0),
        (DOCTOR_ENTITY, 2),
    }
    for entity in range(editor.entity_count):
        for script_index in range(32):
            pointer = editor.get_script_pointer(entity, script_index)
            if (entity, script_index) not in active_slots and pointer != SHARED_STOP_PC:
                raise surface.SurfaceSoylentBuildError(
                    f"Field {spec.scene} e{entity}:s{script_index} escaped retirement"
                )
    return editor.to_bytes()


def load_exam_room_source(donor_disc: Path | str) -> tuple[bytes, bytes]:
    """Extract and verify the shared Disc 1 field-352 clinic pair."""

    return foundation.load_empty_clinic567_source(donor_disc)


def verify_exam_room_targets_are_dummy(source_disc: Path | str) -> None:
    """Refuse to replace any of the eight Disc 2 slots unless all are dummies."""

    expected = {
        canonical_id: (len(surface.DONOR_DUMMY), surface.DONOR_DUMMY_SHA256)
        for canonical_id in TARGET_IDS
    }
    resources = surface._load_canonical_resources(source_disc, expected)
    if set(resources) != set(TARGET_IDS) or any(
        resources[canonical_id] != surface.DONOR_DUMMY
        for canonical_id in TARGET_IDS
    ):
        raise surface.SurfaceSoylentBuildError(
            "Disc 2 fields 591-594 clinical-room targets are not checked "
            "CDMAKE dummies"
        )


def prepare_empty_room_terminal(
    prepared_foundation: surface.PreparedDonorField,
) -> surface.PreparedDonorField:
    """Activate field 567's workstation with a read-only empty record."""

    if (
        prepared_foundation.identity != foundation.EMPTY_CLINIC567_IDENTITY
        or _identity(prepared_foundation.bundle)
        != foundation.FINAL_BUNDLE_IDENTITY
        or _identity(prepared_foundation.header)
        != foundation.FINAL_HEADER_IDENTITY
        or _identity(prepared_foundation.components[surface.SCRIPT_INDEX])
        != foundation.FINAL_SCRIPT_IDENTITY
        or _identity(prepared_foundation.components[7])
        != foundation.FINAL_DIALOGUE_IDENTITY
    ):
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-clinic foundation changed before terminal activation"
        )

    components = list(prepared_foundation.components)
    _validate_terminal_frontage_geometry(components[1])
    dialogue, dialogue_ids = _append_dialogue(
        components[7],
        (EMPTY_ROOM_TERMINAL_DIALOGUE,),
    )
    if dialogue_ids != (EMPTY_ROOM_TERMINAL_DIALOGUE_ID,):
        raise surface.SurfaceSoylentBuildError(
            f"Field 567 empty-room dialogue ID changed: {dialogue_ids}"
        )
    empty_record = parse_dialogue(dialogue).blocks[
        EMPTY_ROOM_TERMINAL_DIALOGUE_ID
    ]
    if empty_record.text != EMPTY_ROOM_TERMINAL_DIALOGUE:
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-room terminal dialogue changed"
        )
    surface.mass_driver._validate_authored_manual_wrap(
        {
            "manual_wrap": True,
            "width": empty_record.width,
            "height": empty_record.height,
            "text": empty_record.text,
        },
        empty_record.block_id,
    )

    script = _install_empty_room_terminal_scripts(
        components[surface.SCRIPT_INDEX],
        EMPTY_ROOM_TERMINAL_DIALOGUE_ID,
    )
    header = prepared_foundation.header
    components[surface.SCRIPT_INDEX] = script
    components[7] = dialogue
    bundle = build_field_preserving(
        prepared_foundation.bundle,
        components,
        (surface.SCRIPT_INDEX, 7),
        compact_changed=True,
        replacement_header=header,
    )
    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-room terminal failed decoded-stream round trip"
        )
    if (
        _identity(script) != EMPTY_ROOM_TERMINAL_SCRIPT_IDENTITY
        or _identity(dialogue) != EMPTY_ROOM_TERMINAL_DIALOGUE_IDENTITY
        or _identity(reparsed.header) != EMPTY_ROOM_TERMINAL_HEADER_IDENTITY
        or _identity(bundle) != EMPTY_ROOM_TERMINAL_BUNDLE_IDENTITY
    ):
        raise surface.SurfaceSoylentBuildError(
            "Field 567 empty-room terminal output changed"
        )

    actor_count = struct.unpack_from("<H", reparsed.header, 0x18C)[0]
    models = surface.mass_driver._indexed_bundle_entries(
        components[surface.mass_driver.MODEL_INDEX]
    )
    if (
        actor_count != SOURCE_HEADER_ACTOR_COUNT
        or reparsed.header[
            0x190
            + BED_SOURCE_HEADER_NODE * 16 : 0x190
            + (BED_SOURCE_HEADER_NODE + 1) * 16
        ]
        != BED_HEADER_RECORD
        or reparsed.header[
            0x190
            + MEDICAL_TERMINAL_SOURCE_HEADER_NODE * 16 : 0x190
            + (MEDICAL_TERMINAL_SOURCE_HEADER_NODE + 1) * 16
        ]
        != MEDICAL_TERMINAL_HEADER_RECORD
        or _identity(models[BED_MODEL_INDEX]) != BED_MODEL_IDENTITY
        or _identity(models[MEDICAL_TERMINAL_MODEL_INDEX])
        != MEDICAL_TERMINAL_MODEL_IDENTITY
    ):
        raise surface.SurfaceSoylentBuildError(
            "Field 567 terminal activation changed its clinic props"
        )
    for index, before in enumerate(prepared_foundation.components):
        if index not in (surface.SCRIPT_INDEX, 7) and components[index] != before:
            raise surface.SurfaceSoylentBuildError(
                f"Field 567 terminal unexpectedly changed component {index}"
            )

    return surface.PreparedDonorField(
        prepared_foundation.identity,
        (
            "empty Ethos medical room; examination bed and environment "
            "preserved; three facing-gated ghost side-computer X carriers "
            "report that no patient is loaded; no NPC or progression event; "
            "one animated reciprocal return to field 621/p4; random encounters "
            "disabled"
        ),
        prepared_foundation.source_bundle,
        prepared_foundation.graphics,
        reparsed.header,
        tuple(components),
        bundle,
        prepared_foundation.entry_triangles,
    )


def prepare_exam_room(
    scene: int,
    source_bundle: bytes,
    graphics: bytes,
    patient_asset: LoadedPatientAsset,
) -> surface.PreparedDonorField:
    """Build one deterministic field-352 examination-room clone."""

    try:
        spec = EXAM_ROOM_BY_SCENE[scene]
    except KeyError as exc:
        raise surface.SurfaceSoylentBuildError(
            f"Unsupported examination-room scene: {scene}"
        ) from exc
    if patient_asset.spec != PATIENT_ASSET_SPECS[scene]:
        raise surface.SurfaceSoylentBuildError(
            f"Field {scene} received the wrong demihuman patient asset"
        )

    # Reuse the audited empty-room conversion in full: it verifies every source
    # component, patches the runtime party, retires retail story execution,
    # preserves the native leaf, and suppresses random encounters.
    prepared_foundation = foundation.prepare_empty_clinic567(
        source_bundle,
        graphics,
    )
    components = list(prepared_foundation.components)
    _validate_treatment_pair_geometry(components[1])
    _validate_terminal_frontage_geometry(components[1])

    dialogue, dialogue_ids = _append_dialogue(
        components[7],
        (
            *spec.terminal_dialogues,
            spec.doctor_dialogue,
            spec.patient_dialogue,
        ),
    )
    if (
        len(parse_dialogue(components[7]).blocks) != SOURCE_DIALOGUE_COUNT
        or dialogue_ids[: len(spec.terminal_dialogues)]
        != TERMINAL_DIALOGUE_IDS_BY_SCENE[scene]
        or dialogue_ids[-2:]
        != (
            DOCTOR_DIALOGUE_IDS_BY_SCENE[scene],
            PATIENT_DIALOGUE_IDS_BY_SCENE[scene],
        )
    ):
        raise surface.SurfaceSoylentBuildError(
            f"Field {scene} terminal dialogue IDs changed: {dialogue_ids}"
        )
    _validate_private_dialogue(scene, dialogue)
    script = _install_exam_room_scripts(
        components[surface.SCRIPT_INDEX],
        spec,
        dialogue_ids,
    )
    (
        components[surface.mass_driver.ACTOR_INDEX],
        components[surface.mass_driver.SPRITE_INDEX],
    ) = _install_patient_asset(
        prepared_foundation.header,
        components,
        patient_asset,
    )
    header = _insert_terminal_header_record(prepared_foundation.header)
    components[surface.SCRIPT_INDEX] = script
    components[7] = dialogue
    if (
        _identity(script) != FINAL_SCRIPT_IDENTITIES[scene]
        or _identity(dialogue) != FINAL_DIALOGUE_IDENTITIES[scene]
        or _identity(components[surface.mass_driver.ACTOR_INDEX])
        != FINAL_ACTOR_COMPONENT_IDENTITIES[scene]
        or _identity(components[surface.mass_driver.SPRITE_INDEX])
        != FINAL_SPRITE_COMPONENT_IDENTITIES[scene]
        or _identity(components[6]) != FINAL_ENCOUNTER_IDENTITY
    ):
        raise surface.SurfaceSoylentBuildError(
            f"Field {scene} exam-room component identity changed"
        )

    bundle = build_field_preserving(
        prepared_foundation.bundle,
        components,
        (
            surface.mass_driver.ACTOR_INDEX,
            surface.mass_driver.SPRITE_INDEX,
            surface.SCRIPT_INDEX,
            7,
        ),
        compact_changed=True,
        replacement_header=header,
    )
    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise surface.SurfaceSoylentBuildError(
            f"Field {scene} exam-room output failed decoded-stream round trip"
        )
    if (
        _identity(bundle) != FINAL_BUNDLE_IDENTITIES[scene]
        or _identity(reparsed.header) != FINAL_HEADER_IDENTITIES[scene]
    ):
        raise surface.SurfaceSoylentBuildError(
            f"Field {scene} packed exam-room identity changed"
        )
    actor_count = struct.unpack_from("<H", reparsed.header, 0x18C)[0]
    if (
        actor_count != HEADER_ACTOR_COUNT
        or reparsed.header[
            0x190 + TERMINAL_ENTITY * 16 : 0x190 + (TERMINAL_ENTITY + 1) * 16
        ]
        != TERMINAL_HEADER_RECORD
        or reparsed.header[
            0x190 + BED_HEADER_NODE * 16 : 0x190 + (BED_HEADER_NODE + 1) * 16
        ]
        != BED_HEADER_RECORD
        or reparsed.header[
            0x190
            + MEDICAL_TERMINAL_HEADER_NODE * 16 : 0x190
            + (MEDICAL_TERMINAL_HEADER_NODE + 1) * 16
        ]
        != MEDICAL_TERMINAL_HEADER_RECORD
    ):
        raise surface.SurfaceSoylentBuildError(
            f"Field {scene} terminal insertion changed its clinic props"
        )
    model_entries = surface.mass_driver._indexed_bundle_entries(
        components[surface.mass_driver.MODEL_INDEX]
    )
    if (
        _identity(model_entries[BED_MODEL_INDEX]) != BED_MODEL_IDENTITY
        or _identity(model_entries[MEDICAL_TERMINAL_MODEL_INDEX])
        != MEDICAL_TERMINAL_MODEL_IDENTITY
    ):
        raise surface.SurfaceSoylentBuildError(
            f"Field {scene} examination bed/workstation model changed"
        )
    installed_actors = surface.mass_driver._indexed_bundle_entries(
        components[surface.mass_driver.ACTOR_INDEX]
    )
    installed_sprites = surface.mass_driver._indexed_bundle_entries(
        components[surface.mass_driver.SPRITE_INDEX]
    )
    if (
        installed_actors[PATIENT_TARGET_BANK] != patient_asset.actor
        or installed_sprites[PATIENT_TARGET_BANK] != patient_asset.sprite
        or _identity(installed_actors[DOCTOR_BANK]) != DOCTOR_ACTOR_IDENTITY
        or _identity(installed_sprites[DOCTOR_BANK]) != DOCTOR_SPRITE_IDENTITY
    ):
        raise surface.SurfaceSoylentBuildError(
            f"Field {scene} treatment actors changed after packing"
        )

    return surface.PreparedDonorField(
        EXAM_ROOM_IDENTITIES[scene],
        (
            f"{spec.role}; independent field-352 clinic shell with bed and "
            f"native animated return to field {RETURN_FIELD}/p{spec.return_parameter}; "
            f"solid talkable physician treating a {patient_asset.spec.appearance}; "
            "three facing-gated ghost side-computer X carriers; retail events "
            "unreachable; random "
            "encounters disabled"
            + (
                "; explicitly accepted, one-time Quarantine keycard in the "
                "authorization slot"
                if spec.awards_quarantine_keycard
                else "; repeatable Solaris clinical status terminal"
            )
        ),
        source_bundle,
        graphics,
        reparsed.header,
        tuple(components),
        bundle,
        ((ENTRY_PARAMETER, ENTRY_TRIANGLE),),
    )


def prepare_exam_rooms(
    source_bundle: bytes,
    graphics: bytes,
    patient_assets: Mapping[int, LoadedPatientAsset],
) -> tuple[surface.PreparedDonorField, ...]:
    """Build all four independent clinical rooms from one verified pair."""

    if set(patient_assets) != set(SCENES):
        raise surface.SurfaceSoylentBuildError(
            "Treatment-room patient asset map has the wrong scene set"
        )
    return tuple(
        prepare_exam_room(
            scene,
            source_bundle,
            graphics,
            patient_assets[scene],
        )
        for scene in SCENES
    )


def prepare_exam_rooms_from_discs(
    source_disc: Path | str,
    donor_disc: Path | str,
) -> tuple[surface.PreparedDonorField, ...]:
    """Verify all Disc 2 targets, load field 352 once, and build all rooms."""

    verify_exam_room_targets_are_dummy(source_disc)
    return prepare_exam_rooms(
        *load_exam_room_source(donor_disc),
        load_patient_assets(source_disc),
    )


RETURN_ACTIONS_BY_SCENE = {
    scene: _return_action(parameter)
    for scene, parameter in RETURN_PARAMETERS_BY_SCENE.items()
}
RETURN_ROUTES_BY_SCENE = {
    scene: (
        RETURN_CONTROLLER,
        RETURN_ACTION_PC,
        RETURN_HELPER,
        RETURN_PLAYER_SCRIPT,
        RETURN_FIELD,
        RETURN_PARAMETERS_BY_SCENE[scene],
    )
    for scene in SCENES
}
DOOR_ENDPOINT_IDS_BY_SCENE = {
    spec.scene: spec.endpoint_id for spec in EXAM_ROOM_SPECS
}


__all__ = [
    "BED_HEADER_NODE",
    "BED_HEADER_RECORD",
    "BED_MODEL_IDENTITY",
    "BED_MODEL_INDEX",
    "BED_SOURCE_HEADER_NODE",
    "ACTOR_BOUNDING_VOLUME",
    "ACTOR_GHOST_COLLISION_FLAGS",
    "ACTOR_INTERACTION_HALF_DEPTH",
    "ACTOR_INTERACTION_HALF_WIDTH",
    "ACTOR_STATIONARY_COLLISION_FLAGS",
    "DOCTOR_ACTION_BODIES_BY_SCENE",
    "DOCTOR_ACTOR_IDENTITY",
    "DOCTOR_BANK",
    "DOCTOR_DIALOGUE_IDS_BY_SCENE",
    "DOCTOR_DIALOGUES_BY_SCENE",
    "DOCTOR_ENTITY",
    "DOCTOR_INIT_BODY",
    "DOCTOR_POSITION",
    "DOCTOR_SPRITE_IDENTITY",
    "DOCTOR_TRIANGLE",
    "DOOR_ACTION_HALF_DEPTH",
    "DOOR_CLOSED_SIDE_PROBE",
    "DOOR_ENDPOINT_IDS_BY_SCENE",
    "DOOR_INTERACTION_HALF_DEPTH",
    "DOOR_INTERACTION_HALF_WIDTH",
    "DOOR_OPEN_SIDE_PROBE",
    "DOOR_SEAL_RADIUS",
    "ENTITY_COUNT",
    "ENTRY_ACTOR_DIRECTION",
    "ENTRY_CAMERA_DIRECTION",
    "ENTRY_PARAMETER",
    "ENTRY_PLAYABLE",
    "ENTRY_POSITION",
    "ENTRY_TRIANGLE",
    "ENTRY_WALKMESH",
    "EMPTY_ROOM_TERMINAL_ACTION_PC",
    "EMPTY_ROOM_TERMINAL_ACTION_IDENTITY",
    "EMPTY_ROOM_TERMINAL_AUX_CAVITY",
    "EMPTY_ROOM_TERMINAL_AUX_CAVITY_IDENTITY",
    "EMPTY_ROOM_TERMINAL_BUNDLE_IDENTITY",
    "EMPTY_ROOM_TERMINAL_DIALOGUE",
    "EMPTY_ROOM_TERMINAL_DIALOGUE_ID",
    "EMPTY_ROOM_TERMINAL_DIALOGUE_IDENTITY",
    "EMPTY_ROOM_TERMINAL_ENTITIES",
    "EMPTY_ROOM_TERMINAL_HEADER_IDENTITY",
    "EMPTY_ROOM_TERMINAL_INIT_PC",
    "EMPTY_ROOM_TERMINAL_INIT_PCS",
    "EMPTY_ROOM_TERMINAL_SCRIPT_IDENTITY",
    "EXAM_ROOM_BY_SCENE",
    "EXAM_ROOM_IDENTITIES",
    "EXAM_ROOM_SPECS",
    "ExamRoomSpec",
    "FINAL_BUNDLE_IDENTITIES",
    "FINAL_ACTOR_COMPONENT_IDENTITIES",
    "FINAL_DIALOGUE_COUNTS_BY_SCENE",
    "FINAL_DIALOGUE_IDENTITIES",
    "FINAL_ENCOUNTER_IDENTITY",
    "FINAL_HEADER_IDENTITIES",
    "FINAL_SCRIPT_IDENTITIES",
    "FINAL_SPRITE_COMPONENT_IDENTITIES",
    "HEADER_ACTOR_COUNT",
    "HEMATOLOGY_DIALOGUE",
    "IMMOVABLE_OPCODE",
    "IMMOVABLE_PRECEDES_STOP",
    "ITEM_ACQUISITION_SOUND",
    "ITEM_ACQUISITION_SOUND_ID",
    "KEYCARD_ACQUIRED_DIALOGUE",
    "POST_KEYCARD_DIAGNOSTICS_DIALOGUE",
    "KEYCARD_INSERTED_DIALOGUE",
    "MEDICAL_TERMINAL_HEADER_NODE",
    "MEDICAL_TERMINAL_HEADER_RECORD",
    "MEDICAL_TERMINAL_MODEL_IDENTITY",
    "MEDICAL_TERMINAL_MODEL_INDEX",
    "MEDICAL_TERMINAL_SOURCE_HEADER_NODE",
    "NANOMACHINE_DIALOGUE",
    "NPC_ROUTINE_PCS_BY_SCENE",
    "LoadedPatientAsset",
    "PATIENT_ACTION_BODIES_BY_SCENE",
    "PATIENT_ASSET_SPECS",
    "PATIENT_DIALOGUE_IDS_BY_SCENE",
    "PATIENT_DIALOGUES_BY_SCENE",
    "PATIENT_RECORD_DIALOGUE_IDS_BY_SCENE",
    "PATIENT_RECORD_DIALOGUES_BY_SCENE",
    "PATIENT_ENTITY",
    "PATIENT_INIT_BODIES_BY_SCENE",
    "PATIENT_POSITION",
    "PATIENT_SOURCE_BUNDLE_IDENTITIES",
    "PATIENT_TARGET_BANK",
    "PATIENT_TARGET_MAPPING",
    "PATIENT_TRIANGLE",
    "PatientAssetSpec",
    "PLAYER_COLLISION_RADIUS",
    "QUARANTINE_KEYCARD_BIT_INDEX",
    "QUARANTINE_KEYCARD_MASK",
    "QUARANTINE_KEYCARD_OPERAND",
    "RETURN_ACTION_PC",
    "RETURN_ACTIONS_BY_SCENE",
    "RETURN_CONTROLLER",
    "RETURN_CONTROLLER_POSITION",
    "RETURN_CONTROLLER_TRIANGLE",
    "RETURN_CONTROLLER_TRIANGLES",
    "RETURN_FIELD",
    "RETURN_HELPER",
    "RETURN_HELPER_BODY",
    "RETURN_HELPER_PC",
    "RETURN_HELPER_SCRIPT_INDEX",
    "RETURN_PARAMETERS_BY_SCENE",
    "RETURN_PLAYER_SCRIPT",
    "RETURN_ROUTES_BY_SCENE",
    "SCENES",
    "SHARED_STOP_PC",
    "SOURCE_BUNDLE_ID",
    "SOURCE_BUNDLE_IDENTITY",
    "SOURCE_COMPONENT_IDENTITIES",
    "SOURCE_DIALOGUE_COUNT",
    "SOURCE_ENTITY_COUNT",
    "SOURCE_GRAPHICS_ID",
    "SOURCE_GRAPHICS_IDENTITY",
    "SOURCE_HEADER_ACTOR_COUNT",
    "SOURCE_IDS",
    "SOURCE_SCENE",
    "TARGET_IDS",
    "TARGET_IDS_BY_SCENE",
    "TERMINAL_ACTION_PC",
    "TERMINAL_ACTION_LENGTHS_BY_SCENE",
    "TERMINAL_ACTION_SHA256_BY_SCENE",
    "TERMINAL_APPROACH_FIXTURE",
    "TERMINAL_APPROACH_YAW",
    "TERMINAL_AUX_CAVITY",
    "TERMINAL_AUX_CAVITY_END_PC",
    "TERMINAL_AUX_CAVITY_SOURCE_IDENTITY",
    "TERMINAL_AUX_ENTITIES",
    "TERMINAL_AUX_INIT_PCS",
    "TERMINAL_BED_YAW",
    "TERMINAL_DIALOGUE_IDS_BY_SCENE",
    "TERMINAL_EFFECTIVE_HALF_REACH",
    "TERMINAL_ENTITY",
    "TERMINAL_ENTITIES",
    "TERMINAL_FRONTAGE_X",
    "TERMINAL_HEADER_FLAGS",
    "TERMINAL_HEADER_MODEL_INDEX",
    "TERMINAL_HEADER_RECORD",
    "TERMINAL_INIT_BODY",
    "TERMINAL_INIT_BODIES",
    "TERMINAL_INIT_PC",
    "TERMINAL_INTERACTION_HALF_DEPTH",
    "TERMINAL_INTERACTION_HALF_WIDTH",
    "TERMINAL_OPERATOR_TRIANGLES",
    "TERMINAL_POSITION",
    "TERMINAL_POSITIONS",
    "TERMINAL_REJECTED_AISLE_FIXTURE",
    "TERMINAL_REQUIRES_FACING",
    "TERMINAL_TRIANGLE",
    "TERMINAL_TRIANGLES",
    "TERMINAL_WALKMESH",
    "TREATMENT_PREPARATION_DIALOGUE",
    "load_exam_room_source",
    "load_patient_assets",
    "prepare_exam_room",
    "prepare_exam_rooms",
    "prepare_exam_rooms_from_discs",
    "prepare_empty_room_terminal",
    "verify_exam_room_targets_are_dummy",
]
