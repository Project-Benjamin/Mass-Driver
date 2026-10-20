#!/usr/bin/env python3
"""Migrate the exact V232 field-567 Slot 1 state to V233.

V233 adds a repeatable, read-only side-workstation action to retired field-567
entities 4, 5, and 6.  The normal V233 ATEL and dialogue files are larger than
the allocations serialized in the captured V232 state, so copying them would
overwrite live heap metadata.  This helper instead installs a fixed-size
resident compatibility layout: a proven retired ATEL cavity holds all three
unaltered native V233 initializer bodies, their slot-0 work is queued through
the field scheduler, the action replaces a separately proven-dead retail
routine, and the new text occupies that routine's retired dialogue block.  A
subsequent field reload uses the ordinary V233 files from the exact media.

The helper is deliberately fail-closed.  It accepts only the pinned source,
media, manifests, and field components; verifies an exact decompressed-byte
whitelist; writes only a separate candidate and JSON report; and refuses to
write DuckStation's live Slot 1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
from typing import Protocol, Sequence


if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import tools.migrate_duckstation_disc_state as media_migration  # noqa: E402
import tools.migrate_surface_soylent_v231_slot1_to_v232 as previous  # noqa: E402
from tools.xgdeathblows import GAMESTATE_SIZE  # noqa: E402
from tools.xgdialog import DialogueFormatError, parse_dialogue  # noqa: E402
from tools.xgdisc import DiscFormatError, Mode2Image  # noqa: E402
from tools.xgfield import FieldFormatError, ParsedField, parse_field  # noqa: E402
from tools.xgscript import AtelScript, ScriptFormatError  # noqa: E402
from work.read_duckstation_runtime import (  # noqa: E402
    CAMERA_VECTORS,
    FIELD_ACTORS,
    FIELD_ACTOR_DATA_POINTER,
    FIELD_ACTOR_STRIDE,
    FIELD_CUR_SCRIPT_FILE,
    FIELD_NUM_ACTORS,
    FIELD_SCRIPT_MEMORY,
    FIELD_SCRIPT_VM_CUR_ACTOR,
    FIELD_SCRIPT_VM_CUR_SCRIPT_DATA,
    GAME_STATE,
    RAM_SIZE,
    _psx_ram_offset,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIVE_SLOT1 = (PROJECT_ROOT / "emulator_data" / "SLUS-00669_1.sav").resolve()
SOURCE_FIXTURE = (
    PROJECT_ROOT
    / "work"
    / "save_backups"
    / "SLUS-00669_1_v232_field567_empty_terminal_3f09a8ce.sav"
).resolve()

SOURCE_STATE_SIZE = 1_607_991
SOURCE_STATE_SHA256 = "3f09a8cea70ce09c87b2bc0892ad8e427cc90d7fcf1759b8677413927c20b022"
SOURCE_PREFIX_SIZE = 52_816
SOURCE_PREFIX_SHA256 = "3f13c7b0946ef9957867d15d97c9eb8f1894aaae1db421ecf62febc7799641df"
SOURCE_COMPRESSED_SIZE = 1_555_175
SOURCE_COMPRESSED_SHA256 = "add4f335769ef834f8b68b4c83cd46176c31e4f6b69f4c9fd968e73359c03f3a"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "67141bcd6cd9ffc3669f559c0815ecd4835a26bd29e5485d2d8f70fca2786bdc"
SOURCE_RAM_SHA256 = "908fe35d904cb140b8e65a78b36b12c9d603f2244bdb71c5242bea00a01ddb6d"

OUTPUT_STATE_SIZE = 1_457_268
OUTPUT_STATE_SHA256 = "b9b41cbc756300f6567a7c1cdc6b304e44bc57e025f1a4a51ff74aae84742acf"
OUTPUT_PREFIX_SHA256 = "f5ab567793263a22faf42376d5349e5b18c320247532306f73e285c4f57dc315"
OUTPUT_COMPRESSED_SIZE = 1_404_452
OUTPUT_COMPRESSED_SHA256 = "b79a9c75dfc4163341d035afa4d4a88c5896494f0c95b8e5f17f4977bf4de0e6"
OUTPUT_PAYLOAD_SHA256 = "805b6f3e2a57aba686f2ce21e1192f9746127843cb06dd5b6903f5ad042016a0"
OUTPUT_RAM_SHA256 = "976b6da70c96c9833e1ba6d548c3a3824977cdd9db26d91caae34dfec1f6dd51"
OUTPUT_REPORT_SIZE = 6_393
OUTPUT_REPORT_SHA256 = "c870d9f441933eb0170fb0ce5accf0ca78013acef1cab66095870533da22575a"

OLD_DISC_SIZE = NEW_DISC_SIZE = 698_816_832
OLD_DISC_SHA256 = "8e9020e85760e64555040ea26b73876f0add72a788a3221070e4d57823520394"
NEW_DISC_SHA256 = "f50fa064e8d466bde46e0946a4c1ea7dc556a6a94d85f4632de201934318a72b"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v232.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v233.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = "dacbd8033a8ae9ac9c98c9e3918d3de7deb59a5ddb320dcd7264438ad59d7647"
NEW_CUE_SHA256 = "106149772cdd6b12a460be98858e59d268fb1e01008d12b81f3eda80dd04ca28"

OLD_MANIFEST_SIZE = 135_113
OLD_MANIFEST_SHA256 = "007ef9b6e1863d6ec01b4512303e8b52129da5cf8c454d53704fc48a0f6786ea"
NEW_MANIFEST_SIZE = 136_361
NEW_MANIFEST_SHA256 = "b79d7a866ba29ad9a5f488bf6e004310f5a5a2c32ed73aaf676eee3154ac4d1a"
CHANGED_RESOURCE_IDS = (1740,)
FIELD567_CANONICAL_ID = 1740
OLD_FIELD_BUNDLE_SIZE = 83_512
OLD_FIELD_BUNDLE_SHA256 = "0254d01b7fed03fef798f2980ce64e3de674ab61f6c6dd90b67386066fb492b0"
NEW_FIELD_BUNDLE_SIZE = 83_548
NEW_FIELD_BUNDLE_SHA256 = "6f4be9fa9932c77094b2ff09875ee5a035e145662efd83ba50b1b879d5c36999"

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = "bb4741fed2677df0519c00bb7d105ec7aec027061269e6657bdec60c10717a51"
NEW_ARCHIVE_TABLE_SHA256 = "aabe75ccb44040ab908fe90b649c1af84f28df4cd01f3098e3db4ff611fd318d"
ARCHIVE_TABLE_DIFFS = ((0x2F74, 0x38, 0x5C),)
ARCHIVE_TABLE_DIFF_SHA256 = "170bd9fbdb325cfeaa3fb218007d2e4e41e7b94de23fa2f1a69aa72432e68b22"
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
EXPECTED_VOLATILE_TABLE_PAYLOAD_OFFSET = 0x19A65
EXPECTED_VOLATILE_TABLE_VALUE = 0xE0
SOURCE_RESIDENT_TABLE_SHA256 = "194ecb959cc2af747bc3286f28dc1a54b07c33beb714183eea4938764a1ec2c6"
OUTPUT_RESIDENT_TABLE_SHA256 = "0e44380e3f69290b581d40209a0161e2a50defb7ab5d37323fdde4c0c00e97a2"

OLD_SCRIPT_SIZE = 3_213
NEW_SCRIPT_SIZE = 3_281
OLD_SCRIPT_SHA256 = "efed6a535ff92eab4a58f95c9770714bc142b9f2e2973bc7a794d71c6e7d9858"
NEW_SCRIPT_SHA256 = "24eb53d1aaa10678f2815cf5fe89e80455c592319d6d69712932f4941793790d"
RESIDENT_SCRIPT_SIZE = OLD_SCRIPT_SIZE
RESIDENT_SCRIPT_SHA256 = "65077c3176cf791bf9b5c4adb7fc3b11fa37b741d3b34a1613c4f42eacef8b82"
SCRIPT_ENTITY_COUNT = 20
SCRIPT_BYTECODE_OFFSET = 0x0584
OLD_SCRIPT_BYTECODE_SIZE = 0x0709
NEW_SCRIPT_BYTECODE_SIZE = 0x074D
SHARED_STOP_PC = 0x068C
TERMINAL_ENTITIES = (4, 5, 6)
NORMAL_TERMINAL_INIT_PCS = (0x044E, 0x046B, 0x06B5)
NORMAL_TERMINAL_ACTION_PC = 0x06D2
TERMINAL_INIT_BODY_SIZE = 29
COMPAT_TERMINAL_INIT_PCS = (0x044E, 0x046B, 0x0488)
COMPAT_INIT_CAVITY_SHA256 = (
    "ae8f8d3ec9170dddf16e104f8eb6cb4c0d12f96cebb9debc15b91d4f2602c5dc"
)
COMPAT_ACTION_PC = 0x05BD
COMPAT_ACTION = bytes.fromhex(
    "33 FE 54 31 20 00 CB 05 26 01 80 01 C0 05 26 01 80 "
    "F5 2D 00 01 9C 31 20 00 DE 05 26 01 80 01 D3 05 "
    "26 01 80 FE 53 00"
)
COMPAT_ACTION_SHA256 = "7d3c593800d9042fcc83489b0efb1cf5e9d5b047117c1ae9b8ca4140add45d9e"
RETIRED_CAVITY_START_PC = 0x044E
RETIRED_CAVITY_END_PC = 0x04A5
RETIRED_CAVITY_SHA256 = "85581a31b32134e75912714f1e71cbe0957721e289f114f954a98ed7c4ca8824"
RETIRED_ACTION_END_PC = COMPAT_ACTION_PC + len(COMPAT_ACTION)
RETIRED_ACTION_SOURCE_SHA256 = (
    "42df0cc65fdf41da618964255679bd0abe4d989ee60dd9e39d7e9ffc7571a99e"
)
RETIRED_ID45_OWNER = (16, 4)
RETIRED_ID45_OWNER_PC = 0x05BD
RETIRED_ID45_OWNER_END_PC = 0x05C8
RETIRED_ID45_OWNER_SHA256 = (
    "53211465ca4e9420feedaa3c1b4f1dd254cd4da5c82bab0c1b10cc0bd7586da6"
)
RETIRED_ID45_REFERENCE_PC = 0x05C2
RETIRED_ID45_REFERENCE = bytes.fromhex("D2 2D 00 00")
OLD_SCRIPT_POINTER_TABLE_SHA256 = (
    "f22e9626004aa86e977cc41fb075bee979a66c003a088d3537fcaa5ebba499b7"
)
SOURCE_REACHABLE_INSTRUCTION_COUNT = 52
SOURCE_REACHABLE_INSTRUCTION_SHA256 = (
    "d7b49411945cbeba8454faf137271b0c839f6f9d428e85c0e720cfe2db2cf1aa"
)
SOURCE_REACHABLE_EDGE_COUNT = 4
SOURCE_REACHABLE_EDGE_SHA256 = (
    "4c21cf553519e6b19ffa2d30bd262659e2187d43d08556cf88d47ab1f8bb5542"
)
TARGET_REACHABLE_INSTRUCTION_COUNT = 93
TARGET_REACHABLE_INSTRUCTION_SHA256 = (
    "1d64c855d5a694445c3580464e20b411a55fec095bb6020c86d3dada79b88077"
)
TARGET_REACHABLE_EDGE_COUNT = 8
TARGET_REACHABLE_EDGE_SHA256 = (
    "799a787b2e6e23047ab8946f8293bc3d1b81af567ba425ba72e9698e020ac9ba"
)
TARGET_SCRIPT_POINTER_TABLE_SHA256 = (
    "2289cb3e9534697242f9aaee26e843101da1dc5f0a25be8180ecf0db19a18334"
)
BASE_ACTIVE_SCRIPT_SLOTS = frozenset(
    {
        (0, 0),
        *((entity, slot) for entity in (1, 2, 3) for slot in (0, 1)),
        (17, 0),
        (17, 2),
        (18, 0),
        (18, 4),
        (19, 0),
        (19, 4),
    }
)
ACTIVE_SCRIPT_SLOTS = BASE_ACTIVE_SCRIPT_SLOTS | frozenset(
    (entity, slot)
    for entity in TERMINAL_ENTITIES
    for slot in (0, 2)
)

# Deliberately restricted decoder for the exact vocabulary reachable from the
# frozen field-567 entry points.  Dormant retail bytes are never interpreted as
# instructions merely because they resemble an opcode or dialogue operand.
ACTIVE_OPCODE_SIZES = {
    0x00: 1,  # STOP
    0x01: 3,  # JUMP
    0x02: 8,  # conditional branch
    0x05: 3,  # CALL
    0x07: 3,  # RUN_ENTITY_SCRIPT_ASYNC
    0x08: 3,  # RUN_ENTITY_SCRIPT_UNKMODE
    0x09: 3,  # RUN_ENTITY_SCRIPT_BLOCKING
    0x0B: 3,  # INIT_ENTITY_NPC
    0x0C: 1,  # scheduler-yielding character update
    0x0D: 1,  # RETURN
    0x16: 3,  # INIT_ENTITY_PC
    0x18: 5,  # SET_BOUNDING_VOLUME
    0x19: 6,  # SET_ACTOR_POSITION_2D
    0x1A: 2,  # SET_ENTITY_WALKMESH_LAYER
    0x20: 3,  # SET_CURRENT_ACTOR_FLAGS
    0x23: 1,  # MAKE_INVISIBLE_ACTIVE
    0x26: 3,  # WAIT
    0x2A: 1,  # DISABLE_DIALOG_ACTIVATION
    0x2C: 2,  # PLAY_ANIMATION
    0x31: 5,  # JUMP_IF_PAD_MASK
    0x33: 1,  # RESET_ACCUMULATED_INPUT_MASK
    0x35: 6,  # SET/COPY_VARIABLE
    0x38: 6,  # ADD_VARIABLE
    0x39: 6,  # SUBTRACT_VARIABLE
    0x3A: 6,  # SET_VARBIT_TRUE
    0x3B: 6,  # SET_VARBIT_FALSE
    0x3C: 4,  # INCREMENT_VARIABLE
    0x3D: 4,  # DECREMENT_VARIABLE
    0x3E: 6,  # AND_VARIABLE
    0x42: 5,  # SHIFT_VARIABLE
    0x43: 3,  # RANDOM_VARIABLE
    0x69: 3,  # SET_CURRENT_ACTOR_ROTATION
    0x6F: 2,  # ROTATE_TO_ACTOR
    0x74: 3,  # PLAY_SOUND_EFFECT
    0x75: 3,  # PLAY_MUSIC
    0x8C: 3,  # inventory helper
    0x98: 5,  # CHANGE_FIELD_WHEN_READY2
    0x9C: 1,  # WAIT_DIALOG
    0xA0: 7,  # SET_SCREEN_GEOMETRY
    0xBC: 1,  # INIT_ENTITY_SCRIPT
    0xD2: 4,  # SHOW_DIALOG_WINDOW_MODE0
    0xDE: 6,  # MULTIPLY_VARIABLE
    0xDF: 6,  # DIVIDE_VARIABLE
    0xF5: 4,  # SHOW_DIALOG_WINDOW_MODE3
    0xF6: 2,
    0xF8: 4,  # SET_FLAGS_DYNAMIC
}
ACTIVE_EXTENDED_OPCODE_SIZES = {
    0x0D: 4,
    0x17: 4,
    0x1B: 6,
    0x53: 2,  # RESTORE_FIELD_CONTROL
    0x54: 2,  # SUSPEND_FIELD_CONTROL
    0x7F: 2,
    0xB8: 5,
}
RESIDENT_SCRIPT_DIFF_COUNT = 127
RESIDENT_SCRIPT_DIFF_SHA256 = (
    "a9734f43b7596f50551c432076abfb85c6a2c42f6abafcf5ea7a9852df322a1a"
)

OLD_DIALOGUE_SIZE = 5_177
NEW_DIALOGUE_SIZE = 5_232
OLD_DIALOGUE_SHA256 = "6d9ae403fabe60061966a43a50c5d970317a2f0997bf5554e0dab588866ce518"
NEW_DIALOGUE_SHA256 = "2f15ffdeda92ec407a983737cd0acf550856725718b4fb6a05df046e47f2d8fd"
OLD_DIALOGUE_COUNT = 53
NEW_DIALOGUE_COUNT = 54
NORMAL_TERMINAL_DIALOGUE_ID = 53
RELOCATION_DIALOGUE_ID = 45
RELOCATION_OFFSET = 4_047
RELOCATION_CAPACITY = 307
RELOCATION_SOURCE_GRID = (54, 4)
RELOCATION_SOURCE_SHA256 = "8bcc838c08acff04b23700fd2108098b29f48fba3d1bfee25f539175a4b2dc56"
TARGET_DIALOGUE_GRID = (58, 4)
TARGET_DIALOGUE_SIZE = 51
TARGET_DIALOGUE_SHA256 = "562577377cfbedb6fe12e54a68916dd024a7d03d78bfe61e702edc666d29bb79"
TARGET_DIALOGUE_TEXT = "PATIENT RECORD\nNo patient is loaded\nfor this room.<Close>"
RESIDENT_DIALOGUE_SIZE = OLD_DIALOGUE_SIZE
RESIDENT_DIALOGUE_SHA256 = "32711760eb45436f7f1dcdd9bc83a5918a9928c7c223447168b363f4d0648494"
RESIDENT_DIALOGUE_DIFF_COUNT = 307
RESIDENT_DIALOGUE_DIFF_SHA256 = "df54bcc09e4d7cc14084ab1eaa924b45fd0d6dd16da30dd2f37ce415680941da"

HEADER_SIZE = 944
OLD_HEADER_SHA256 = "05b1d2423392975ca0c4f7b5c0fd98458aea16010da0926630edc1e04c5c7820"
NEW_HEADER_SHA256 = "daa0e99244adbe653367a2257024add96d21d40af973c879e2c18a2bebb925b9"
HEADER_DIFFS = (
    (0x0120, 0x8D, 0xD1),
    (0x0128, 0x39, 0x70),
    (0x0148, 0xC4, 0xD4),
    (0x014C, 0x60, 0x70),
    (0x0150, 0x34, 0x58),
)
HEADER_DIFF_SHA256 = "09cc9465d01da92d786648de17fe71ac36beeabe96d0bc5ade79a3e537d752ee"
WALKMESH_SIZE = 1_948
WALKMESH_SHA256 = "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d8cca4238393571df"

EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
EXPECTED_SCRIPT_PAYLOAD_OFFSET = 0x10CD56
EXPECTED_DIALOGUE_PAYLOAD_OFFSET = 0x10DA16
EXPECTED_WALKMESH_PAYLOAD_OFFSET = 0x10EE6A
EXPECTED_HEADER_PAYLOAD_OFFSET = 0x1D88C6
EXPECTED_SCRIPT_GUEST_POINTER = 0x8010B2F4
EXPECTED_VM_SCRIPT_GUEST_POINTER = 0x8010B878
EXPECTED_VM_ACTOR_GUEST_POINTER = 0x80115944
GAME_SCENE_MAP = 0x04F34C
EXPECTED_FIELD = 567
EXPECTED_ACTOR_COUNT = 34
EXPECTED_ACTOR_ARRAY_GUEST_POINTER = 0x80112BD8
EXPECTED_ACTOR_DATA_POINTERS = (
    0x113818, 0x1139D0, 0x113B88, 0x113D40, 0x113EF8,
    0x1140B0, 0x114268, 0x114420, 0x1145D8, 0x114790,
    0x114948, 0x114B00, 0x114CB8, 0x114E70, 0x115028,
    0x1151E0, 0x115398, 0x115550, 0x11578C, 0x115944,
)
EXPECTED_TERMINAL_SPRITE_POINTERS = (0x80128404, 0x80128650, 0x8012889C)
EXPECTED_TERMINAL_SPRITE_AUX_POINTERS = (0x80128570, 0x801287BC, 0x80128A08)
EXPECTED_TERMINAL_HEAP_SUCCESSORS = (0x80128650, 0x8012889C, 0x80128AE8)
EXPECTED_MODEL0_HEAP_HEADER_TAG = 0x81009158
EXPECTED_MODEL0_AUX_HEAP_HEADER_TAG = 0x8100911D
MODEL0_OBJECT_ALLOCATION_SIZE = 0x164
MODEL0_AUX_ALLOCATION_SIZE = 0x0D8
SPRITE_AUX_POINTER_OFFSETS = (0xE0, 0xE4)
SPRITE_LOCAL_WAIT_OFFSET = 0x9E
EXPECTED_SPRITE_LOCAL_WAIT = 3
FIELD_SCRIPT_ENTITY_ALREADY_INITIALIZED = 0x04F30C
FIELD_DRAW_ENVS_INITIALIZED = 0x059198
SPRITE_CALLBACK_LIST2_DELAY = 0x059428
SPRITE_CALLBACK_LIST2_HEAD = 0x05958C
FIELD_SCRIPT_INIT_VAR0 = 0x0AFC74
EXPECTED_FIELD_DRAW_ENVS_INITIALIZED = 1
EXPECTED_SPRITE_CALLBACK_LIST2_DELAY = 0
EXPECTED_SPRITE_CALLBACK_LIST2_HEAD = 0
EXPECTED_FIELD_SCRIPT_INIT_VAR0 = 1
EXPECTED_FIELD_SCRIPT_INIT_VAR0_AFTER_QUEUE = 4
HEAP_CURRENT_STATE = 0x059318
EXPECTED_HEAP_CURRENT_STATE = bytes.fromhex("20 00 00 00 08 00 00 00")
EXPECTED_HEAP_CURRENT_STATE_SHA256 = (
    "02048ec5e3ba176c29e3b683fe0533b82bdea4acf7cb05b622c52aa233763ae1"
)
HEAP_POINTER = 0x059320
EXPECTED_HEAP_POINTER = 0x800C4278
HEAP_NEEDS_CONSOLIDATION = 0x05932C
HEAP_ERROR_HANDLER_DISABLED = 0x059330
SPRITE_CALLBACK_LIST_GLOBALS = 0x05958C
SPRITE_CALLBACK_LIST_GLOBALS_SIZE = 12
EXPECTED_SPRITE_CALLBACK_LIST_GLOBALS_SHA256 = (
    "15ec7bf0b50732b49f8228e07d24365338f9e3ab994b00af08e5a3bffe55fd8b"
)
EXPECTED_TERMINAL_HEAP_HEADERS_SHA256 = (
    "bfd408041f93e5bc4bf91a9f8e18b95f5c00c927c55e992febdfa827dff7d81e"
)
EXPECTED_FOLLOWING_HEAP_HEADER_OFFSET = 0x128AE0
EXPECTED_FOLLOWING_HEAP_HEADER = bytes.fromhex("54 8C 12 80 58 91 00 81")
NPC_INIT_OPCODE_TABLE_ENTRY = 0x0AE2CC
EXPECTED_NPC_INIT_HANDLER = 0x800A1624
PINNED_NATIVE_MIPS_SPANS = (
    ("execCallbacksList2", 0x01C964, 0x0094, "7d6665c5d06b373e037e41fa5c789d75b7791270487de845a5fa211172a393f2"),
    ("deleteFieldEntitySub4", 0x0230A8, 0x007C, "f60ff3687ef620a2beb9ac618d660b197f13ddb7e1468d35d6143fca9de47cc6"),
    ("spriteAnimationTick", 0x023210, 0x0080, "8b24d91f6ad5afa40f1a281500d9a9843da84aa6b114ae7515ba4d236903e24a"),
    ("initializeSpriteActor", 0x02435C, 0x01C8, "5e36a128e7490ee1197502a2bf35025584c7dd59ba3380d923338247d32ebf5e"),
    ("createSpriteActor", 0x024524, 0x00B4, "6e60d8d472bacf439b5af325e351fd774611beab1eb0a224ea3bebacbdb8a9d1"),
    ("HeapAlloc", 0x031BDC, 0x0394, "769fc2a84de3a5c0fc3829121bd31f8821ce5dad2cfa1f5dcfe6fcbbab14f6f0"),
    ("HeapConsolidate", 0x031FF8, 0x00AC, "83141aee7c5dda8fceba8ea262c2c03e8eaf3bbdfdf8b5ad4ed5d9cacc2473d5"),
    ("HeapFree", 0x0320E8, 0x00A4, "172bdbe744af67620d606319e150a97318f12d59d115f81d13748c22a7bcf7ac"),
    ("resetFieldScriptEntityGraphicEntity", 0x076AC0, 0x06F0, "bff9b1afd351f134f9c667d281007b4bc7cacd39e67e3949ab9930b2d3722d66"),
    ("OP_INIT_ENTITY_NPC", 0x0A1624, 0x010C, "08279c29a1177bbdebd14038fc4081700b98585b7ba70ba8c6fd6a1d9b655c3e"),
)
ACTOR_DATA_SIZE = 0x138
ACTOR_DATA_POSITION_OFFSET = 0x20
ACTOR_FACING_OFFSET = 0x106
ACTOR_SCRIPT_SLOT_OFFSET = 0x8C
ACTOR_SCRIPT_SLOT_STRIDE = 8
ACTOR_SCRIPT_SLOT_COUNT = 8
ACTOR_CURRENT_PC_OFFSET = 0xCC
SOURCE_RUNTIME_PC_SHA256 = (
    "8b39714bf65a7bfab82cd29edfe239dcaa3df2d89427cc2490baa13931b41bd0"
)
TARGET_RUNTIME_PC_SHA256 = (
    "87fc5b1d4812ef069b13084feae139b7ddb7206d8ccab60502e62e6330700ed2"
)
EXPECTED_FEI_POSITION = (4_735_026, 0, -9_255_729)
EXPECTED_FEI_XZ = (72.25076293945312, -141.23121643066406)
EXPECTED_FEI_YAW = 0x0200
TERMINAL_POSITIONS = ((80, -167), (116, -167), (152, -167))
TERMINAL_TRIANGLES = (31, 6, 6)
TERMINAL_EFFECTIVE_HALF_REACH = (18, 46)

FIELD_VARIABLE_BANK_SIZE = 0x400
FIELD_VARIABLE_BACKUP_OFFSET = 0x1930
DIALOG_WINDOWS = 0x0C2698
DIALOG_WINDOW_STRIDE = 0x498
DIALOG_WINDOWS_SIZE = 4 * DIALOG_WINDOW_STRIDE
DIALOG_WINDOW_STATUS_OFFSET = 0x40E

# RAM-relative, fixed-size scheduler patches.  The engine will execute the
# exact native V233 initializer bodies after load; no actor position, surface,
# sprite, allocator, or animation state is fabricated in the save image.
RUNTIME_PATCHES = (
    (0x112DA0, "E0 01", "60 02", "e4 scheduler-active record status"),
    (0x113EFC, "00 08 00 04", "00 08 00 00", "e4 clear retired scheduler flag"),
    (0x113F84, "8C 06 00 FF FF FF 3C 00", "4E 04 00 00 FF FF 1C 00", "e4 queued native initializer"),
    (0x112DFC, "E0 01", "60 02", "e5 scheduler-active record status"),
    (0x1140B4, "00 08 00 04", "00 08 00 00", "e5 clear retired scheduler flag"),
    (0x11413C, "8C 06 00 FF FF FF 3C 00", "6B 04 00 00 FF FF 1C 00", "e5 queued native initializer"),
    (0x112E58, "E0 01", "60 02", "e6 scheduler-active record status"),
    (0x11426C, "00 08 00 04", "00 08 00 00", "e6 clear retired scheduler flag"),
    (0x1142F4, "8C 06 00 FF FF FF 3C 00", "88 04 00 00 FF FF 1C 00", "e6 queued native initializer"),
)
RUNTIME_PATCHES = tuple(
    (offset, bytes.fromhex(old), bytes.fromhex(new), label)
    for offset, old, new, label in RUNTIME_PATCHES
)
EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED = 1
EXPECTED_SCRIPT_BYTES_CHANGED = 127
EXPECTED_DIALOGUE_BYTES_CHANGED = 307
EXPECTED_RUNTIME_BYTES_CHANGED = 21
EXPECTED_PAYLOAD_BYTES_CHANGED = 456
RUNTIME_DIFF_SHA256 = "a71c3320ff6b86e9878004a1cb885057b181f0bfa119a268d7004c9a44c023f2"
PAYLOAD_DIFF_SHA256 = "e3d450721d6fea821459867123810a4c43676364cda74338aa921d86e02c2d16"
EXPECTED_PREFIX_BYTES_CHANGED = 4
PREFIX_DIFF_SHA256 = "bd51da70f45993966fc921b56e8ca4e61c875f63b47f66ae3796937f3a63b6cf"

OUTPUT_ACTOR_ARRAY_SHA256 = "f7aa6b1b3a783c550234b62f4e7c8c025c3095840081ecd2b50e7f6a9d19c091"
OUTPUT_ALL_SCRIPT_ACTOR_DATA_SHA256 = "3e7d48a81bbb9bd6aafd8f1a80391d623f29ae215f3dc6b860bacc10b5191b88"
OUTPUT_TERMINAL_RUNTIME_SHA256 = {
    4: ("f1c3f2751f1ceee089132211397f9d572b72a99a9691826a78e86664e7df6937", "2b2d5f3052b31a02785e227d96509d9ff755abcf14ca332fe421517ae9cfbef4"),
    5: ("dc9b00bfd11cedb0d5929f80367b431436fa083c97d27cf19d6a72e0bdf9d231", "fdadc5520304feb6b9130f48ecac85c8df05d80801fcff6ccd01253a53a87e29"),
    6: ("b46e881a8bd5beb60f55a0c43d2432e82ebdb9bb41708fe49d2ba57fb1f4062a", "dbe97eede8ea57848109424380943250ed61329ccadbfadbd7624d41bf488eb1"),
}

ZSTD_SIZE = 657_408
ZSTD_SHA256 = "51172dce5d1ffef10d90789d97b94b5ffbcaf1404bcd34c1f80e9c3072361c5e"


class _ZstdLike(Protocol):
    def frame_size(self, frame: bytes) -> int: ...
    def decompress(self, frame: bytes) -> bytes: ...
    def compress(self, payload: bytes) -> bytes: ...


SurfaceSlotMigrationError = previous.SurfaceSlotMigrationError


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _diff_triplets(before: bytes, after: bytes) -> tuple[tuple[int, int, int], ...]:
    return previous._diff_triplets(before, after)


def _diff_offsets(before: bytes, after: bytes) -> tuple[int, ...]:
    return previous._diff_offsets(before, after)


def _triplet_digest(diffs: Sequence[tuple[int, int, int]]) -> str:
    return _sha256(
        b"".join(struct.pack("<IBB", offset, old, new) for offset, old, new in diffs)
    )


def _script_pointer_digest(editor: AtelScript) -> str:
    return _sha256(
        b"".join(
            struct.pack("<H", editor.get_script_pointer(entity, slot))
            for entity in range(editor.entity_count)
            for slot in range(32)
        )
    )


def _reachable_active_instructions(
    editor: AtelScript,
) -> tuple[dict[int, bytes], tuple[tuple[int, int], ...]]:
    """Decode every instruction reachable from the frozen active slot set."""

    pending = [
        editor.get_script_pointer(entity, slot)
        for entity, slot in ACTIVE_SCRIPT_SLOTS
    ]
    decoded: dict[int, bytes] = {}
    edges: list[tuple[int, int]] = []
    while pending:
        pc = pending.pop()
        while pc not in decoded:
            if not 0 <= pc < len(editor.bytecode):
                raise SurfaceSlotMigrationError(
                    f"Reachable ATEL PC is out of range: 0x{pc:04X}"
                )
            opcode = editor.bytecode[pc]
            if opcode == 0xFE:
                if pc + 1 >= len(editor.bytecode):
                    raise SurfaceSlotMigrationError("Truncated reachable extended opcode")
                extension = editor.bytecode[pc + 1]
                size = ACTIVE_EXTENDED_OPCODE_SIZES.get(extension)
                if size is None:
                    raise SurfaceSlotMigrationError(
                        f"Unexpected reachable extension FE{extension:02X} at 0x{pc:04X}"
                    )
            else:
                size = ACTIVE_OPCODE_SIZES.get(opcode)
                if size is None:
                    raise SurfaceSlotMigrationError(
                        f"Unexpected reachable opcode {opcode:02X} at 0x{pc:04X}"
                    )
            instruction = editor.bytecode[pc : pc + size]
            if len(instruction) != size:
                raise SurfaceSlotMigrationError(
                    f"Truncated reachable instruction at 0x{pc:04X}"
                )
            decoded[pc] = instruction

            if opcode in (0x07, 0x08, 0x09):
                entity, selector = instruction[1:3]
                if entity >= editor.entity_count:
                    raise SurfaceSlotMigrationError(
                        f"Reachable entity call leaves ATEL table at 0x{pc:04X}"
                    )
                target = editor.get_script_pointer(entity, selector & 0x1F)
                edges.append((pc, target))
                pending.append(target)
            if opcode in (0x01, 0x05):
                target = struct.unpack_from("<H", instruction, 1)[0]
                edges.append((pc, target))
                pending.append(target)
                if opcode == 0x01:
                    break
            if opcode == 0x02:
                target = struct.unpack_from("<H", instruction, 6)[0]
                edges.append((pc, target))
                pending.append(target)
            elif opcode == 0x31:
                target = struct.unpack_from("<H", instruction, 3)[0]
                edges.append((pc, target))
                pending.append(target)
            if opcode in (0x00, 0x0C, 0x0D, 0x98):
                break
            pc += size
    return decoded, tuple(sorted(edges))


def _reachable_instruction_digest(instructions: dict[int, bytes]) -> str:
    return _sha256(
        b"".join(
            struct.pack("<HH", pc, len(instruction)) + instruction
            for pc, instruction in sorted(instructions.items())
        )
    )


def _reachable_edge_digest(edges: Sequence[tuple[int, int]]) -> str:
    return _sha256(b"".join(struct.pack("<HH", source, target) for source, target in edges))


def _instruction_byte_offsets(instructions: dict[int, bytes]) -> frozenset[int]:
    return frozenset(
        offset
        for pc, instruction in instructions.items()
        for offset in range(pc, pc + len(instruction))
    )


def _pointer_hits(
    editor: AtelScript, start: int, end: int
) -> tuple[tuple[int, int, int], ...]:
    return tuple(
        (entity, slot, pointer)
        for entity in range(editor.entity_count)
        for slot in range(32)
        if start <= (pointer := editor.get_script_pointer(entity, slot)) < end
    )


def _unpack_state(state: bytes, zstd: _ZstdLike) -> tuple[bytes, int, bytes]:
    return previous._unpack_state(state, zstd)


def _pack_state(prefix: bytes, payload: bytes, zstd: _ZstdLike) -> bytes:
    return previous._pack_state(prefix, payload, zstd)


def _guest_ram_offset(pointer: int, label: str) -> int:
    offset = pointer & 0x1FFFFFFF
    if offset >= RAM_SIZE:
        raise SurfaceSlotMigrationError(f"{label} pointer is outside PSX RAM")
    return offset


def _ram_from_payload(payload: bytes) -> tuple[int, bytes]:
    try:
        offset = _psx_ram_offset(payload)
    except SystemExit as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc
    if offset != EXPECTED_RAM_PAYLOAD_OFFSET:
        raise SurfaceSlotMigrationError("Serialized RAM payload offset drifted")
    ram = payload[offset : offset + RAM_SIZE]
    if len(ram) != RAM_SIZE:
        raise SurfaceSlotMigrationError("Serialized PSX RAM is incomplete")
    return offset, ram


def _camera_snapshot(ram: bytes) -> bytes:
    return b"".join(ram[address : address + 16] for address in CAMERA_VECTORS.values())


def _validate_file(path: Path, size: int, sha256: str, label: str) -> None:
    if not path.is_file() or path.stat().st_size != size or _file_sha256(path) != sha256:
        raise SurfaceSlotMigrationError(f"{label} identity drifted")


def _manifest_inventory(
    blob: bytes, *, size: int, sha256: str, label: str
) -> dict[int, tuple[int, str]]:
    if (len(blob), _sha256(blob)) != (size, sha256):
        raise SurfaceSlotMigrationError(f"{label} identity drifted")
    try:
        return {
            int(item["canonical_id"]): (int(item["size"]), str(item["sha256"]))
            for item in json.loads(blob)["replacement_inventory"]
        }
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise SurfaceSlotMigrationError(f"{label} structure drifted") from exc


def _disc_resource(
    image: Mode2Image,
    canonical_id: int,
    size: int,
    sha256: str,
    label: str,
) -> bytes:
    entries = image.read_index()
    index = canonical_id - 5
    if index >= len(entries) or entries[index].canonical_disc2_index != canonical_id:
        raise SurfaceSlotMigrationError(f"{label} FAT mapping drifted")
    data = image.extract_entry(entries[index])
    if (len(data), _sha256(data)) != (size, sha256):
        raise SurfaceSlotMigrationError(f"{label} identity drifted")
    return data


def _disc_field567(disc: Path, *, size: int, sha256: str, label: str) -> ParsedField:
    try:
        result = parse_field(
            _disc_resource(Mode2Image(disc), FIELD567_CANONICAL_ID, size, sha256, label)
        )
    except (DiscFormatError, FieldFormatError) as exc:
        raise SurfaceSlotMigrationError(f"Cannot decode {label}: {exc}") from exc
    if len(result.parts) != 9:
        raise SurfaceSlotMigrationError(f"{label} component layout drifted")
    return result


def _build_resident_script(old_script: bytes, new_script: bytes) -> bytes:
    for blob, size, sha256, label in (
        (old_script, OLD_SCRIPT_SIZE, OLD_SCRIPT_SHA256, "V232 field-567 ATEL"),
        (new_script, NEW_SCRIPT_SIZE, NEW_SCRIPT_SHA256, "V233 field-567 ATEL"),
    ):
        if (len(blob), _sha256(blob)) != (size, sha256):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    old, new = AtelScript(old_script), AtelScript(new_script)
    normal_init_bodies = tuple(
        new.bytecode[pc : pc + TERMINAL_INIT_BODY_SIZE]
        for pc in NORMAL_TERMINAL_INIT_PCS
    )
    compat_init_cavity = b"".join(normal_init_bodies)
    old_reachable, old_edges = _reachable_active_instructions(old)
    old_occupied = _instruction_byte_offsets(old_reachable)
    dead_ranges = (
        range(RETIRED_CAVITY_START_PC, RETIRED_CAVITY_END_PC),
        range(COMPAT_ACTION_PC, RETIRED_ACTION_END_PC),
    )
    if (
        old.entity_count != SCRIPT_ENTITY_COUNT
        or new.entity_count != SCRIPT_ENTITY_COUNT
        or (old.bytecode_offset, old.bytecode_size)
        != (SCRIPT_BYTECODE_OFFSET, OLD_SCRIPT_BYTECODE_SIZE)
        or (new.bytecode_offset, new.bytecode_size)
        != (SCRIPT_BYTECODE_OFFSET, NEW_SCRIPT_BYTECODE_SIZE)
        or _script_pointer_digest(old) != OLD_SCRIPT_POINTER_TABLE_SHA256
        or tuple(old.get_script_pointer(entity, 0) for entity in TERMINAL_ENTITIES)
        != (SHARED_STOP_PC,) * 3
        or tuple(old.get_script_pointer(entity, 2) for entity in TERMINAL_ENTITIES)
        != (SHARED_STOP_PC,) * 3
        or tuple(new.get_script_pointer(entity, 0) for entity in TERMINAL_ENTITIES)
        != NORMAL_TERMINAL_INIT_PCS
        or tuple(new.get_script_pointer(entity, 2) for entity in TERMINAL_ENTITIES)
        != (NORMAL_TERMINAL_ACTION_PC,) * 3
        or any(len(body) != TERMINAL_INIT_BODY_SIZE for body in normal_init_bodies)
        or len(compat_init_cavity) != RETIRED_CAVITY_END_PC - RETIRED_CAVITY_START_PC
        or _sha256(compat_init_cavity) != COMPAT_INIT_CAVITY_SHA256
        or _sha256(old.bytecode[RETIRED_CAVITY_START_PC:RETIRED_CAVITY_END_PC])
        != RETIRED_CAVITY_SHA256
        or _sha256(old.bytecode[COMPAT_ACTION_PC:RETIRED_ACTION_END_PC])
        != RETIRED_ACTION_SOURCE_SHA256
        or _sha256(
            old.bytecode[RETIRED_ID45_OWNER_PC:RETIRED_ID45_OWNER_END_PC]
        )
        != RETIRED_ID45_OWNER_SHA256
        or old.get_script_pointer(*RETIRED_ID45_OWNER) != SHARED_STOP_PC
        or any(old.get_script_pointer(RETIRED_ID45_OWNER[0], slot) != SHARED_STOP_PC
               for slot in range(32))
        or old.bytecode.find(RETIRED_ID45_REFERENCE) != RETIRED_ID45_REFERENCE_PC
        or old.bytecode.count(RETIRED_ID45_REFERENCE) != 1
        or _pointer_hits(old, RETIRED_CAVITY_START_PC, RETIRED_CAVITY_END_PC)
        or _pointer_hits(old, COMPAT_ACTION_PC, RETIRED_ACTION_END_PC)
        or len(old_reachable) != SOURCE_REACHABLE_INSTRUCTION_COUNT
        or _reachable_instruction_digest(old_reachable)
        != SOURCE_REACHABLE_INSTRUCTION_SHA256
        or len(old_edges) != SOURCE_REACHABLE_EDGE_COUNT
        or _reachable_edge_digest(old_edges) != SOURCE_REACHABLE_EDGE_SHA256
        or any(set(span) & old_occupied for span in dead_ranges)
        or any(
            start <= target < end
            for _source, target in old_edges
            for start, end in (
                (RETIRED_CAVITY_START_PC, RETIRED_CAVITY_END_PC),
                (COMPAT_ACTION_PC, RETIRED_ACTION_END_PC),
            )
        )
        or (len(COMPAT_ACTION), _sha256(COMPAT_ACTION))
        != (39, COMPAT_ACTION_SHA256)
    ):
        raise SurfaceSlotMigrationError(
            "Field-567 retired-cavity/ID45 reachability proof drifted"
        )

    data = bytearray(old_script)
    cavity_offset = old.bytecode_offset + RETIRED_CAVITY_START_PC
    data[cavity_offset : cavity_offset + len(compat_init_cavity)] = compat_init_cavity
    action_offset = old.bytecode_offset + COMPAT_ACTION_PC
    data[action_offset : action_offset + len(COMPAT_ACTION)] = COMPAT_ACTION
    resident = AtelScript(data)
    for entity, init_pc in zip(
        TERMINAL_ENTITIES, COMPAT_TERMINAL_INIT_PCS, strict=True
    ):
        resident.set_script_pointer(entity, 0, init_pc)
        resident.set_script_pointer(entity, 2, COMPAT_ACTION_PC)
    result = resident.to_bytes()
    diffs = _diff_triplets(old_script, result)
    for entity in range(SCRIPT_ENTITY_COUNT):
        for slot in range(32):
            if entity in TERMINAL_ENTITIES and slot in (0, 2):
                continue
            if resident.get_script_pointer(entity, slot) != old.get_script_pointer(
                entity, slot
            ):
                raise SurfaceSlotMigrationError(
                    "Compatibility ATEL changed an unrelated pointer"
                )

    target_reachable, target_edges = _reachable_active_instructions(resident)
    target_occupied = _instruction_byte_offsets(target_reachable)
    expected_cavity_pointers = tuple(
        (entity, 0, pc)
        for entity, pc in zip(
            TERMINAL_ENTITIES, COMPAT_TERMINAL_INIT_PCS, strict=True
        )
    )
    expected_action_pointers = tuple(
        (entity, 2, COMPAT_ACTION_PC) for entity in TERMINAL_ENTITIES
    )
    if (
        (len(result), _sha256(result))
        != (RESIDENT_SCRIPT_SIZE, RESIDENT_SCRIPT_SHA256)
        or len(diffs) != RESIDENT_SCRIPT_DIFF_COUNT
        or _triplet_digest(diffs) != RESIDENT_SCRIPT_DIFF_SHA256
        or _script_pointer_digest(resident) != TARGET_SCRIPT_POINTER_TABLE_SHA256
        or tuple(resident.get_script_pointer(entity, 0) for entity in TERMINAL_ENTITIES)
        != COMPAT_TERMINAL_INIT_PCS
        or tuple(resident.get_script_pointer(entity, 2) for entity in TERMINAL_ENTITIES)
        != (COMPAT_ACTION_PC,) * 3
        or resident.bytecode[RETIRED_CAVITY_START_PC:RETIRED_CAVITY_END_PC]
        != compat_init_cavity
        or resident.bytecode[COMPAT_ACTION_PC:RETIRED_ACTION_END_PC]
        != COMPAT_ACTION
        or resident.bytecode.count(COMPAT_ACTION) != 1
        or resident.bytecode.count(RETIRED_ID45_REFERENCE) != 0
        or resident.bytecode.count(bytes((0xF5, RELOCATION_DIALOGUE_ID, 0))) != 1
        or _pointer_hits(
            resident, RETIRED_CAVITY_START_PC, RETIRED_CAVITY_END_PC
        )
        != expected_cavity_pointers
        or _pointer_hits(resident, COMPAT_ACTION_PC, RETIRED_ACTION_END_PC)
        != expected_action_pointers
        or len(target_reachable) != TARGET_REACHABLE_INSTRUCTION_COUNT
        or _reachable_instruction_digest(target_reachable)
        != TARGET_REACHABLE_INSTRUCTION_SHA256
        or len(target_edges) != TARGET_REACHABLE_EDGE_COUNT
        or _reachable_edge_digest(target_edges) != TARGET_REACHABLE_EDGE_SHA256
        or not set(range(RETIRED_CAVITY_START_PC, RETIRED_CAVITY_END_PC))
        <= target_occupied
        or not set(range(COMPAT_ACTION_PC, RETIRED_ACTION_END_PC))
        <= target_occupied
    ):
        raise SurfaceSlotMigrationError("Allocator-safe resident ATEL drifted")
    return result


def _build_resident_dialogue(
    old_dialogue: bytes, new_dialogue: bytes, resident_script: bytes
) -> bytes:
    for blob, size, sha256, label in (
        (old_dialogue, OLD_DIALOGUE_SIZE, OLD_DIALOGUE_SHA256, "V232 dialogue"),
        (new_dialogue, NEW_DIALOGUE_SIZE, NEW_DIALOGUE_SHA256, "V233 dialogue"),
    ):
        if (len(blob), _sha256(blob)) != (size, sha256):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    old, new = parse_dialogue(old_dialogue), parse_dialogue(new_dialogue)
    if len(old.blocks) != OLD_DIALOGUE_COUNT or len(new.blocks) != NEW_DIALOGUE_COUNT:
        raise SurfaceSlotMigrationError("Field-567 dialogue count drifted")
    for before, after in zip(old.blocks, new.blocks[:OLD_DIALOGUE_COUNT], strict=True):
        if (before.width, before.height, before.payload) != (
            after.width, after.height, after.payload
        ):
            raise SurfaceSlotMigrationError("V233 changes a pre-existing dialogue block")
    cavity = old.blocks[RELOCATION_DIALOGUE_ID]
    target = new.blocks[NORMAL_TERMINAL_DIALOGUE_ID]
    resident_editor = AtelScript(resident_script)
    if (
        (cavity.offset, len(cavity.payload), cavity.width, cavity.height)
        != (RELOCATION_OFFSET, RELOCATION_CAPACITY, *RELOCATION_SOURCE_GRID)
        or _sha256(cavity.payload) != RELOCATION_SOURCE_SHA256
        or (len(target.payload), target.width, target.height, target.text)
        != (TARGET_DIALOGUE_SIZE, *TARGET_DIALOGUE_GRID, TARGET_DIALOGUE_TEXT)
        or _sha256(target.payload) != TARGET_DIALOGUE_SHA256
        or len(target.payload) > len(cavity.payload)
        or resident_editor.bytecode.count(RETIRED_ID45_REFERENCE) != 0
        or resident_editor.bytecode.count(
            bytes((0xF5, RELOCATION_DIALOGUE_ID, 0))
        )
        != 1
        or resident_editor.bytecode[
            COMPAT_ACTION_PC:RETIRED_ACTION_END_PC
        ]
        != COMPAT_ACTION
    ):
        raise SurfaceSlotMigrationError("Retired ID45 dialogue cavity drifted")

    dimensions_offset = 4 + 2 * OLD_DIALOGUE_COUNT + 2 * RELOCATION_DIALOGUE_ID
    result = bytearray(old_dialogue)
    result[dimensions_offset : dimensions_offset + 2] = bytes(TARGET_DIALOGUE_GRID)
    result[RELOCATION_OFFSET : RELOCATION_OFFSET + RELOCATION_CAPACITY] = (
        target.payload + b"\x00" * (RELOCATION_CAPACITY - len(target.payload))
    )
    result = bytes(result)
    migrated = parse_dialogue(result)
    relocated = migrated.blocks[RELOCATION_DIALOGUE_ID]
    diffs = _diff_triplets(old_dialogue, result)
    if (
        (len(result), _sha256(result))
        != (RESIDENT_DIALOGUE_SIZE, RESIDENT_DIALOGUE_SHA256)
        or len(diffs) != RESIDENT_DIALOGUE_DIFF_COUNT
        or _triplet_digest(diffs) != RESIDENT_DIALOGUE_DIFF_SHA256
        or (relocated.offset, len(relocated.payload), relocated.width, relocated.height)
        != (RELOCATION_OFFSET, RELOCATION_CAPACITY, *TARGET_DIALOGUE_GRID)
        or relocated.payload[:TARGET_DIALOGUE_SIZE] != target.payload
        or relocated.payload[TARGET_DIALOGUE_SIZE:] != b"\x00" * (
            RELOCATION_CAPACITY - TARGET_DIALOGUE_SIZE
        )
    ):
        raise SurfaceSlotMigrationError("Allocator-safe resident dialogue drifted")
    return result


def _validate_media(
    old_disc: Path,
    new_disc: Path,
    old_manifest: bytes,
    new_manifest: bytes,
    old_script: bytes,
    new_script: bytes,
    old_header: bytes,
    new_header: bytes,
    old_dialogue: bytes,
    new_dialogue: bytes,
) -> tuple[bytes, bytes, bytes, bytes]:
    for path, size, sha256, label in (
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V232 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V233 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V232 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V233 CUE"),
    ):
        _validate_file(path, size, sha256, label)
    old_inventory = _manifest_inventory(
        old_manifest, size=OLD_MANIFEST_SIZE, sha256=OLD_MANIFEST_SHA256, label="V232 manifest"
    )
    new_inventory = _manifest_inventory(
        new_manifest, size=NEW_MANIFEST_SIZE, sha256=NEW_MANIFEST_SHA256, label="V233 manifest"
    )
    changed = tuple(
        resource_id
        for resource_id in sorted(set(old_inventory) | set(new_inventory))
        if old_inventory.get(resource_id) != new_inventory.get(resource_id)
    )
    if (
        changed != CHANGED_RESOURCE_IDS
        or old_inventory.get(FIELD567_CANONICAL_ID)
        != (OLD_FIELD_BUNDLE_SIZE, OLD_FIELD_BUNDLE_SHA256)
        or new_inventory.get(FIELD567_CANONICAL_ID)
        != (NEW_FIELD_BUNDLE_SIZE, NEW_FIELD_BUNDLE_SHA256)
    ):
        raise SurfaceSlotMigrationError("V232/V233 manifest delta drifted")

    if (
        (len(old_header), _sha256(old_header)) != (HEADER_SIZE, OLD_HEADER_SHA256)
        or (len(new_header), _sha256(new_header)) != (HEADER_SIZE, NEW_HEADER_SHA256)
        or _diff_triplets(old_header, new_header) != HEADER_DIFFS
        or _triplet_digest(HEADER_DIFFS) != HEADER_DIFF_SHA256
    ):
        raise SurfaceSlotMigrationError("V232/V233 field-567 header delta drifted")
    resident_script = _build_resident_script(old_script, new_script)
    resident_dialogue = _build_resident_dialogue(
        old_dialogue, new_dialogue, resident_script
    )

    old_field = _disc_field567(
        old_disc, size=OLD_FIELD_BUNDLE_SIZE, sha256=OLD_FIELD_BUNDLE_SHA256, label="V232 field-567 bundle"
    )
    new_field = _disc_field567(
        new_disc, size=NEW_FIELD_BUNDLE_SIZE, sha256=NEW_FIELD_BUNDLE_SHA256, label="V233 field-567 bundle"
    )
    if (
        old_field.header != old_header
        or new_field.header != new_header
        or old_field.parts[5].data != old_script
        or new_field.parts[5].data != new_script
        or old_field.parts[7].data != old_dialogue
        or new_field.parts[7].data != new_dialogue
        or any(
            old_field.parts[index].data != new_field.parts[index].data
            for index in range(9) if index not in (5, 7)
        )
        or (len(old_field.parts[1].data), _sha256(old_field.parts[1].data))
        != (WALKMESH_SIZE, WALKMESH_SHA256)
    ):
        raise SurfaceSlotMigrationError("V232/V233 field-567 media contract drifted")

    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    if (
        (len(old_table), len(new_table)) != (ARCHIVE_TABLE_SIZE, ARCHIVE_TABLE_SIZE)
        or _sha256(old_table) != OLD_ARCHIVE_TABLE_SHA256
        or _sha256(new_table) != NEW_ARCHIVE_TABLE_SHA256
        or _diff_triplets(old_table, new_table) != ARCHIVE_TABLE_DIFFS
        or _triplet_digest(ARCHIVE_TABLE_DIFFS) != ARCHIVE_TABLE_DIFF_SHA256
    ):
        raise SurfaceSlotMigrationError("V232/V233 archive-table delta drifted")
    return old_table, new_table, resident_script, resident_dialogue


def _entity_records(ram: bytes, actor_array: int, entities: Sequence[int]) -> bytes:
    return b"".join(
        ram[actor_array + entity * FIELD_ACTOR_STRIDE : actor_array + (entity + 1) * FIELD_ACTOR_STRIDE]
        for entity in entities
    )


def _entity_actor_data(ram: bytes, actor_array: int, entities: Sequence[int]) -> bytes:
    result = bytearray()
    for entity in entities:
        record = actor_array + entity * FIELD_ACTOR_STRIDE
        actor_data = _guest_ram_offset(
            struct.unpack_from("<I", ram, record + FIELD_ACTOR_DATA_POINTER)[0],
            f"e{entity} ActorData",
        )
        result.extend(ram[actor_data : actor_data + ACTOR_DATA_SIZE])
    return bytes(result)


def _runtime_pc_snapshot(
    ram: bytes, actor_array: int
) -> tuple[tuple[int, int, tuple[int, ...]], ...]:
    rows: list[tuple[int, int, tuple[int, ...]]] = []
    for entity in range(SCRIPT_ENTITY_COUNT):
        record = actor_array + entity * FIELD_ACTOR_STRIDE
        actor_data = _guest_ram_offset(
            struct.unpack_from("<I", ram, record + FIELD_ACTOR_DATA_POINTER)[0],
            f"e{entity} ActorData",
        )
        current_pc = struct.unpack_from(
            "<H", ram, actor_data + ACTOR_CURRENT_PC_OFFSET
        )[0]
        slot_pcs = tuple(
            struct.unpack_from(
                "<H",
                ram,
                actor_data + ACTOR_SCRIPT_SLOT_OFFSET
                + slot * ACTOR_SCRIPT_SLOT_STRIDE,
            )[0]
            for slot in range(ACTOR_SCRIPT_SLOT_COUNT)
        )
        rows.append((entity, current_pc, slot_pcs))
    return tuple(rows)


def _runtime_pc_digest(
    rows: Sequence[tuple[int, int, tuple[int, ...]]]
) -> str:
    return _sha256(
        b"".join(
            struct.pack("<BH8H", entity, current_pc, *slot_pcs)
            for entity, current_pc, slot_pcs in rows
        )
    )


def _runtime_pc_hits(
    rows: Sequence[tuple[int, int, tuple[int, ...]]], start: int, end: int
) -> tuple[tuple[int, int, int], ...]:
    hits: list[tuple[int, int, int]] = []
    for entity, current_pc, slot_pcs in rows:
        if start <= current_pc < end:
            hits.append((entity, -1, current_pc))
        hits.extend(
            (entity, slot, pc)
            for slot, pc in enumerate(slot_pcs)
            if start <= pc < end
        )
    return tuple(hits)


def _validate_source_runtime(
    payload: bytes,
    *,
    old_table: bytes,
    old_script: bytes,
    new_script: bytes,
    old_header: bytes,
    new_header: bytes,
    old_dialogue: bytes,
    new_dialogue: bytes,
) -> dict[str, object]:
    if (len(payload), _sha256(payload)) != (SOURCE_PAYLOAD_SIZE, SOURCE_PAYLOAD_SHA256):
        raise SurfaceSlotMigrationError("V232 decompressed payload identity drifted")
    ram_offset, ram = _ram_from_payload(payload)
    if _sha256(ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("V232 serialized RAM identity drifted")
    for component, offset, label in (
        (old_script, EXPECTED_SCRIPT_PAYLOAD_OFFSET, "resident V232 ATEL"),
        (old_dialogue, EXPECTED_DIALOGUE_PAYLOAD_OFFSET, "resident V232 dialogue"),
        (old_header, EXPECTED_HEADER_PAYLOAD_OFFSET, "cached V232 header"),
    ):
        if payload.count(component) != 1 or payload.find(component) != offset:
            raise SurfaceSlotMigrationError(f"{label} identity/offset drifted")
    if payload.count(new_script) or payload.count(new_dialogue) or payload.count(new_header):
        raise SurfaceSlotMigrationError("Source already contains a complete V233 resident component")
    walkmesh = payload[
        EXPECTED_WALKMESH_PAYLOAD_OFFSET : EXPECTED_WALKMESH_PAYLOAD_OFFSET + WALKMESH_SIZE
    ]
    if _sha256(walkmesh) != WALKMESH_SHA256:
        raise SurfaceSlotMigrationError("Resident field-567 walkmesh drifted")

    if (
        struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0] != EXPECTED_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA)[0]
        != EXPECTED_VM_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_ACTOR)[0]
        != EXPECTED_VM_ACTOR_GUEST_POINTER
        or struct.unpack_from("<I", ram, GAME_SCENE_MAP)[0] != EXPECTED_FIELD
        or struct.unpack_from("<I", ram, FIELD_NUM_ACTORS)[0] != EXPECTED_ACTOR_COUNT
        or struct.unpack_from("<I", ram, FIELD_ACTORS)[0] != EXPECTED_ACTOR_ARRAY_GUEST_POINTER
    ):
        raise SurfaceSlotMigrationError("Resident field-567 runtime topology drifted")
    actor_array = _guest_ram_offset(EXPECTED_ACTOR_ARRAY_GUEST_POINTER, "field actor array")
    actual_pointers = tuple(
        _guest_ram_offset(
            struct.unpack_from(
                "<I", ram, actor_array + entity * FIELD_ACTOR_STRIDE + FIELD_ACTOR_DATA_POINTER
            )[0],
            f"e{entity} ActorData",
        )
        for entity in range(SCRIPT_ENTITY_COUNT)
    )
    if actual_pointers != EXPECTED_ACTOR_DATA_POINTERS:
        raise SurfaceSlotMigrationError("Field-567 ActorData allocation drifted")
    terminal_sprite_pointers = tuple(
        struct.unpack_from(
            "<I", ram, actor_array + entity * FIELD_ACTOR_STRIDE + 4
        )[0]
        for entity in TERMINAL_ENTITIES
    )
    terminal_sprite_offsets = tuple(
        _guest_ram_offset(pointer, f"e{entity} sprite")
        for entity, pointer in zip(
            TERMINAL_ENTITIES, terminal_sprite_pointers, strict=True
        )
    )
    terminal_aux_offsets = tuple(
        _guest_ram_offset(pointer, f"e{entity} sprite auxiliary block")
        for entity, pointer in zip(
            TERMINAL_ENTITIES,
            EXPECTED_TERMINAL_SPRITE_AUX_POINTERS,
            strict=True,
        )
    )
    terminal_heap_headers = b"".join(
        ram[sprite - 8 : sprite] + ram[aux - 8 : aux]
        for sprite, aux in zip(
            terminal_sprite_offsets, terminal_aux_offsets, strict=True
        )
    )
    if (
        terminal_sprite_pointers != EXPECTED_TERMINAL_SPRITE_POINTERS
        or any(
            aux_pointer
            != sprite_pointer + 8 + MODEL0_OBJECT_ALLOCATION_SIZE
            for sprite_pointer, aux_pointer in zip(
                EXPECTED_TERMINAL_SPRITE_POINTERS,
                EXPECTED_TERMINAL_SPRITE_AUX_POINTERS,
                strict=True,
            )
        )
        or any(
            successor != aux_pointer + 8 + MODEL0_AUX_ALLOCATION_SIZE
            for aux_pointer, successor in zip(
                EXPECTED_TERMINAL_SPRITE_AUX_POINTERS,
                EXPECTED_TERMINAL_HEAP_SUCCESSORS,
                strict=True,
            )
        )
        or any(
            ram[sprite - 8 : sprite]
            != struct.pack(
                "<II", aux_pointer, EXPECTED_MODEL0_HEAP_HEADER_TAG
            )
            or ram[aux - 8 : aux]
            != struct.pack(
                "<II", successor, EXPECTED_MODEL0_AUX_HEAP_HEADER_TAG
            )
            or any(
                struct.unpack_from("<I", ram, sprite + offset)[0]
                != aux_pointer
                for offset in SPRITE_AUX_POINTER_OFFSETS
            )
            or struct.unpack_from(
                "<h", ram, sprite + SPRITE_LOCAL_WAIT_OFFSET
            )[0]
            != EXPECTED_SPRITE_LOCAL_WAIT
            for sprite, aux, aux_pointer, successor in zip(
                terminal_sprite_offsets,
                terminal_aux_offsets,
                EXPECTED_TERMINAL_SPRITE_AUX_POINTERS,
                EXPECTED_TERMINAL_HEAP_SUCCESSORS,
                strict=True,
            )
        )
        or _sha256(terminal_heap_headers)
        != EXPECTED_TERMINAL_HEAP_HEADERS_SHA256
        or ram[
            EXPECTED_FOLLOWING_HEAP_HEADER_OFFSET :
            EXPECTED_FOLLOWING_HEAP_HEADER_OFFSET + 8
        ]
        != EXPECTED_FOLLOWING_HEAP_HEADER
        or ram[HEAP_CURRENT_STATE : HEAP_CURRENT_STATE + 8]
        != EXPECTED_HEAP_CURRENT_STATE
        or _sha256(ram[HEAP_CURRENT_STATE : HEAP_CURRENT_STATE + 8])
        != EXPECTED_HEAP_CURRENT_STATE_SHA256
        or struct.unpack_from("<I", ram, HEAP_POINTER)[0] != EXPECTED_HEAP_POINTER
        or struct.unpack_from("<I", ram, HEAP_NEEDS_CONSOLIDATION)[0] != 0
        or struct.unpack_from("<I", ram, HEAP_ERROR_HANDLER_DISABLED)[0] != 0
        or struct.unpack_from("<I", ram, FIELD_DRAW_ENVS_INITIALIZED)[0]
        != EXPECTED_FIELD_DRAW_ENVS_INITIALIZED
        or struct.unpack_from("<I", ram, SPRITE_CALLBACK_LIST2_DELAY)[0]
        != EXPECTED_SPRITE_CALLBACK_LIST2_DELAY
        or struct.unpack_from("<I", ram, SPRITE_CALLBACK_LIST2_HEAD)[0]
        != EXPECTED_SPRITE_CALLBACK_LIST2_HEAD
        or _sha256(
            ram[
                SPRITE_CALLBACK_LIST_GLOBALS :
                SPRITE_CALLBACK_LIST_GLOBALS + SPRITE_CALLBACK_LIST_GLOBALS_SIZE
            ]
        )
        != EXPECTED_SPRITE_CALLBACK_LIST_GLOBALS_SHA256
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_INIT_VAR0)[0]
        != EXPECTED_FIELD_SCRIPT_INIT_VAR0
        or struct.unpack_from("<I", ram, NPC_INIT_OPCODE_TABLE_ENTRY)[0]
        != EXPECTED_NPC_INIT_HANDLER
        or any(
            _sha256(ram[start : start + size]) != sha256
            for _label, start, size, sha256 in PINNED_NATIVE_MIPS_SPANS
        )
        or any(
            struct.unpack_from(
                "<H", ram, actor_array + entity * FIELD_ACTOR_STRIDE + 0x5A
            )[0]
            != 1
            for entity in TERMINAL_ENTITIES
        )
        or struct.unpack_from(
            "<I", ram, FIELD_SCRIPT_ENTITY_ALREADY_INITIALIZED
        )[0]
        != 0
    ):
        raise SurfaceSlotMigrationError(
            "Native terminal sprite/heap/callback preconditions drifted"
        )
    runtime_pcs = _runtime_pc_snapshot(ram, actor_array)
    if (
        _runtime_pc_digest(runtime_pcs) != SOURCE_RUNTIME_PC_SHA256
        or _runtime_pc_hits(
            runtime_pcs, RETIRED_CAVITY_START_PC, RETIRED_CAVITY_END_PC
        )
        or _runtime_pc_hits(runtime_pcs, COMPAT_ACTION_PC, RETIRED_ACTION_END_PC)
    ):
        raise SurfaceSlotMigrationError(
            "A current/slot PC enters a resident ATEL replacement span"
        )
    fei = actual_pointers[1]
    if (
        struct.unpack_from("<3i", ram, fei + ACTOR_DATA_POSITION_OFFSET) != EXPECTED_FEI_POSITION
        or (struct.unpack_from("<H", ram, fei + ACTOR_FACING_OFFSET)[0] & 0xFFF)
        != EXPECTED_FEI_YAW
    ):
        raise SurfaceSlotMigrationError("Pinned Fei stance drifted")

    table_offset, volatile = media_migration._find_resident_archive_table(payload, old_table)
    resident_table = payload[table_offset : table_offset + ARCHIVE_TABLE_SIZE]
    if (
        table_offset != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or volatile != 1
        or payload[EXPECTED_VOLATILE_TABLE_PAYLOAD_OFFSET] != EXPECTED_VOLATILE_TABLE_VALUE
        or _sha256(resident_table) != SOURCE_RESIDENT_TABLE_SHA256
        or resident_table != old_table[:-1] + bytes((EXPECTED_VOLATILE_TABLE_VALUE,))
    ):
        raise SurfaceSlotMigrationError("Resident V232 archive table drifted")
    dialog_windows = ram[DIALOG_WINDOWS : DIALOG_WINDOWS + DIALOG_WINDOWS_SIZE]
    if any(
        struct.unpack_from(
            "<h", dialog_windows, index * DIALOG_WINDOW_STRIDE + DIALOG_WINDOW_STATUS_OFFSET
        )[0] != -1
        for index in range(4)
    ):
        raise SurfaceSlotMigrationError("A dialogue window is active; relocation is unsafe")
    return {
        "ram_offset": ram_offset,
        "ram": ram,
        "actor_array": actor_array,
        "runtime_pcs": runtime_pcs,
        "gamestate": ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
        "field_bank": ram[FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE],
        "backup_bank": ram[
            GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET :
            GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET + FIELD_VARIABLE_BANK_SIZE
        ],
        "camera": _camera_snapshot(ram),
        "party_records": _entity_records(ram, actor_array, (1, 2, 3)),
        "party_data": _entity_actor_data(ram, actor_array, (1, 2, 3)),
        "unrelated_records": _entity_records(
            ram, actor_array, tuple(e for e in range(SCRIPT_ENTITY_COUNT) if e not in TERMINAL_ENTITIES)
        ),
        "unrelated_data": _entity_actor_data(
            ram, actor_array, tuple(e for e in range(SCRIPT_ENTITY_COUNT) if e not in TERMINAL_ENTITIES)
        ),
        "dialog_windows": dialog_windows,
        "walkmesh": walkmesh,
    }


def _expected_prefix(source_prefix: bytes, *, compressed_size: int) -> bytes:
    old_name, new_name = OLD_CUE_NAME.encode("ascii"), NEW_CUE_NAME.encode("ascii")
    if (
        len(old_name) != len(new_name)
        or source_prefix.count(old_name) != 1
        or source_prefix.count(new_name)
    ):
        raise SurfaceSlotMigrationError("Pinned V232 media path changed")
    expected = bytearray(source_prefix.replace(old_name, new_name))
    struct.pack_into(
        "<I", expected, media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET, compressed_size
    )
    return bytes(expected)


def _runtime_diff_triplets(ram_offset: int) -> tuple[tuple[int, int, int], ...]:
    return tuple(
        (ram_offset + offset + relative, before, after)
        for offset, old, new, _label in RUNTIME_PATCHES
        for relative, (before, after) in enumerate(zip(old, new, strict=True))
        if before != after
    )


def migrate_v232_slot1_to_v233(
    state: bytes,
    *,
    old_disc: Path,
    new_disc: Path,
    old_manifest: bytes,
    new_manifest: bytes,
    old_script: bytes,
    new_script: bytes,
    old_header: bytes,
    new_header: bytes,
    old_dialogue: bytes,
    new_dialogue: bytes,
    zstd: _ZstdLike,
) -> tuple[bytes, dict[str, object]]:
    """Return the separately writable, fully validated V233 candidate."""

    source_sha256 = _sha256(state)
    if (len(state), source_sha256) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise SurfaceSlotMigrationError(
            f"Source Slot 1 is {len(state)} / {source_sha256}, expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    old_name, new_name = OLD_CUE_NAME.encode("ascii"), NEW_CUE_NAME.encode("ascii")
    if state.count(old_name) != 1 or state.count(new_name) != 0:
        raise SurfaceSlotMigrationError("Source CUE identity drifted")

    old_table, new_table, resident_script, resident_dialogue = _validate_media(
        old_disc, new_disc, old_manifest, new_manifest, old_script, new_script,
        old_header, new_header, old_dialogue, new_dialogue
    )
    source_payload, frame_start, source_prefix = _unpack_state(state, zstd)
    if (
        frame_start != SOURCE_PREFIX_SIZE
        or _sha256(source_prefix) != SOURCE_PREFIX_SHA256
        or len(state) - frame_start != SOURCE_COMPRESSED_SIZE
        or _sha256(state[frame_start:]) != SOURCE_COMPRESSED_SHA256
    ):
        raise SurfaceSlotMigrationError("Pinned V232 DuckStation frame drifted")
    snapshots = _validate_source_runtime(
        source_payload,
        old_table=old_table,
        old_script=old_script,
        new_script=new_script,
        old_header=old_header,
        new_header=new_header,
        old_dialogue=old_dialogue,
        new_dialogue=new_dialogue,
    )
    ram_offset = int(snapshots["ram_offset"])

    final = bytearray(source_payload)
    rebuilt_table = bytearray(new_table)
    rebuilt_table[-1] = source_payload[EXPECTED_VOLATILE_TABLE_PAYLOAD_OFFSET]
    rebuilt_table = bytes(rebuilt_table)
    if _sha256(rebuilt_table) != OUTPUT_RESIDENT_TABLE_SHA256:
        raise SurfaceSlotMigrationError("V233 resident archive reconstruction drifted")
    final[
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
    ] = rebuilt_table
    final[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET : EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE
    ] = resident_script
    final[
        EXPECTED_DIALOGUE_PAYLOAD_OFFSET :
        EXPECTED_DIALOGUE_PAYLOAD_OFFSET + RESIDENT_DIALOGUE_SIZE
    ] = resident_dialogue
    for offset, old, new, label in RUNTIME_PATCHES:
        payload_offset = ram_offset + offset
        if final[payload_offset : payload_offset + len(old)] != old:
            raise SurfaceSlotMigrationError(f"Runtime patch source drifted: {label}")
        final[payload_offset : payload_offset + len(new)] = new
    final_payload = bytes(final)

    table_diffs = _diff_triplets(
        source_payload[
            EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
            EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
        ],
        rebuilt_table,
    )
    script_diffs = _diff_triplets(old_script, resident_script)
    dialogue_diffs = _diff_triplets(old_dialogue, resident_dialogue)
    runtime_diffs = _runtime_diff_triplets(ram_offset)
    expected_offsets = {
        *(EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + offset for offset, _old, _new in table_diffs),
        *(EXPECTED_SCRIPT_PAYLOAD_OFFSET + offset for offset, _old, _new in script_diffs),
        *(EXPECTED_DIALOGUE_PAYLOAD_OFFSET + offset for offset, _old, _new in dialogue_diffs),
        *(offset for offset, _old, _new in runtime_diffs),
    }
    actual_diffs = _diff_triplets(source_payload, final_payload)
    if (
        len(table_diffs) != EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED
        or len(script_diffs) != EXPECTED_SCRIPT_BYTES_CHANGED
        or len(dialogue_diffs) != EXPECTED_DIALOGUE_BYTES_CHANGED
        or len(runtime_diffs) != EXPECTED_RUNTIME_BYTES_CHANGED
        or _triplet_digest(runtime_diffs) != RUNTIME_DIFF_SHA256
        or len(actual_diffs) != EXPECTED_PAYLOAD_BYTES_CHANGED
        or {offset for offset, _old, _new in actual_diffs} != expected_offsets
        or _triplet_digest(actual_diffs) != PAYLOAD_DIFF_SHA256
        or _sha256(final_payload) != OUTPUT_PAYLOAD_SHA256
    ):
        raise SurfaceSlotMigrationError("Migration escaped the exact payload whitelist")

    _result_ram_offset, result_ram = _ram_from_payload(final_payload)
    actor_array = int(snapshots["actor_array"])
    result_runtime_pcs = _runtime_pc_snapshot(result_ram, actor_array)
    expected_queued_pcs = tuple(
        (entity, 0, pc)
        for entity, pc in zip(
            TERMINAL_ENTITIES, COMPAT_TERMINAL_INIT_PCS, strict=True
        )
    )
    if (
        _runtime_pc_digest(result_runtime_pcs) != TARGET_RUNTIME_PC_SHA256
        or _runtime_pc_hits(
            result_runtime_pcs, RETIRED_CAVITY_START_PC, RETIRED_CAVITY_END_PC
        )
        != expected_queued_pcs
        or _runtime_pc_hits(
            result_runtime_pcs, COMPAT_ACTION_PC, RETIRED_ACTION_END_PC
        )
    ):
        raise SurfaceSlotMigrationError(
            "Final current/slot PC scheduler contract drifted"
        )
    unrelated_entities = tuple(
        entity for entity in range(SCRIPT_ENTITY_COUNT) if entity not in TERMINAL_ENTITIES
    )
    if (
        _sha256(result_ram) != OUTPUT_RAM_SHA256
        or result_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE] != snapshots["gamestate"]
        or result_ram[FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE]
        != snapshots["field_bank"]
        or result_ram[
            GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET :
            GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET + FIELD_VARIABLE_BANK_SIZE
        ] != snapshots["backup_bank"]
        or _camera_snapshot(result_ram) != snapshots["camera"]
        or _entity_records(result_ram, actor_array, (1, 2, 3)) != snapshots["party_records"]
        or _entity_actor_data(result_ram, actor_array, (1, 2, 3)) != snapshots["party_data"]
        or _entity_records(result_ram, actor_array, unrelated_entities)
        != snapshots["unrelated_records"]
        or _entity_actor_data(result_ram, actor_array, unrelated_entities)
        != snapshots["unrelated_data"]
        or result_ram[DIALOG_WINDOWS : DIALOG_WINDOWS + DIALOG_WINDOWS_SIZE]
        != snapshots["dialog_windows"]
        or final_payload[
            EXPECTED_HEADER_PAYLOAD_OFFSET : EXPECTED_HEADER_PAYLOAD_OFFSET + HEADER_SIZE
        ] != old_header
        or final_payload[
            EXPECTED_WALKMESH_PAYLOAD_OFFSET : EXPECTED_WALKMESH_PAYLOAD_OFFSET + WALKMESH_SIZE
        ] != snapshots["walkmesh"]
    ):
        raise SurfaceSlotMigrationError("Fei/party/GameState/camera/unrelated runtime changed")

    actor_array_blob = result_ram[
        actor_array : actor_array + EXPECTED_ACTOR_COUNT * FIELD_ACTOR_STRIDE
    ]
    all_actor_data = _entity_actor_data(
        result_ram, actor_array, tuple(range(SCRIPT_ENTITY_COUNT))
    )
    if (
        _sha256(actor_array_blob) != OUTPUT_ACTOR_ARRAY_SHA256
        or _sha256(all_actor_data) != OUTPUT_ALL_SCRIPT_ACTOR_DATA_SHA256
    ):
        raise SurfaceSlotMigrationError("Final field-567 actor runtime identity drifted")
    for entity, (record_sha256, data_sha256) in OUTPUT_TERMINAL_RUNTIME_SHA256.items():
        record = actor_array + entity * FIELD_ACTOR_STRIDE
        actor_data = EXPECTED_ACTOR_DATA_POINTERS[entity]
        if (
            _sha256(result_ram[record : record + FIELD_ACTOR_STRIDE]) != record_sha256
            or _sha256(result_ram[actor_data : actor_data + ACTOR_DATA_SIZE]) != data_sha256
        ):
            raise SurfaceSlotMigrationError(f"Final e{entity} terminal runtime drifted")

    cue_prefix = source_prefix.replace(old_name, new_name)
    result = _pack_state(cue_prefix, final_payload, zstd)
    verified_payload, verified_frame, verified_prefix = _unpack_state(result, zstd)
    expected_prefix = _expected_prefix(source_prefix, compressed_size=len(result) - frame_start)
    prefix_diffs = _diff_triplets(source_prefix, expected_prefix)
    if (
        verified_payload != final_payload
        or verified_frame != SOURCE_PREFIX_SIZE
        or verified_prefix != expected_prefix
        or len(prefix_diffs) != EXPECTED_PREFIX_BYTES_CHANGED
        or _triplet_digest(prefix_diffs) != PREFIX_DIFF_SHA256
        or len(result) != OUTPUT_STATE_SIZE
        or _sha256(result) != OUTPUT_STATE_SHA256
        or len(result) - verified_frame != OUTPUT_COMPRESSED_SIZE
        or _sha256(result[verified_frame:]) != OUTPUT_COMPRESSED_SHA256
        or _sha256(verified_prefix) != OUTPUT_PREFIX_SHA256
    ):
        raise SurfaceSlotMigrationError("Deterministic V233 state round trip drifted")

    report: dict[str, object] = {
        "source_size": len(state),
        "source_sha256": SOURCE_STATE_SHA256,
        "output_size": len(result),
        "output_sha256": OUTPUT_STATE_SHA256,
        "prefix_size": verified_frame,
        "prefix_sha256": OUTPUT_PREFIX_SHA256,
        "compressed_payload_size": len(result) - verified_frame,
        "compressed_payload_sha256": OUTPUT_COMPRESSED_SHA256,
        "payload_size": len(final_payload),
        "payload_sha256": OUTPUT_PAYLOAD_SHA256,
        "ram_sha256": OUTPUT_RAM_SHA256,
        "payload_bytes_changed": len(actual_diffs),
        "payload_diff_triplet_sha256": PAYLOAD_DIFF_SHA256,
        "prefix_bytes_changed": len(prefix_diffs),
        "archive_table_bytes_changed": len(table_diffs),
        "resident_archive_table_sha256": OUTPUT_RESIDENT_TABLE_SHA256,
        "resident_archive_volatile_tail_preserved": True,
        "resident_script_bytes_changed": len(script_diffs),
        "resident_script_size": RESIDENT_SCRIPT_SIZE,
        "resident_script_sha256": RESIDENT_SCRIPT_SHA256,
        "normal_v233_script_size": NEW_SCRIPT_SIZE,
        "resident_dialogue_bytes_changed": len(dialogue_diffs),
        "resident_dialogue_size": RESIDENT_DIALOGUE_SIZE,
        "resident_dialogue_sha256": RESIDENT_DIALOGUE_SHA256,
        "normal_v233_dialogue_size": NEW_DIALOGUE_SIZE,
        "relocated_dialogue_id": RELOCATION_DIALOGUE_ID,
        "normal_v233_dialogue_id": NORMAL_TERMINAL_DIALOGUE_ID,
        "relocated_dialogue_offset": f"0x{RELOCATION_OFFSET:X}",
        "relocated_dialogue_capacity": RELOCATION_CAPACITY,
        "terminal_runtime_bytes_changed": len(runtime_diffs),
        "terminal_runtime_diff_triplet_sha256": RUNTIME_DIFF_SHA256,
        "terminal_entities": list(TERMINAL_ENTITIES),
        "terminal_positions_after_queued_native_init": [
            list(position) for position in TERMINAL_POSITIONS
        ],
        "terminal_bounds_half_width_depth": [1, 15],
        "terminal_requires_facing": True,
        "terminal_initializers_queued": True,
        "terminal_initializer_pcs": [
            f"0x{pc:04X}" for pc in COMPAT_TERMINAL_INIT_PCS
        ],
        "terminal_initializer_cavity_span": (
            f"0x{RETIRED_CAVITY_START_PC:04X}..0x{RETIRED_CAVITY_END_PC - 1:04X}"
        ),
        "terminal_initializer_cavity_sha256": COMPAT_INIT_CAVITY_SHA256,
        "native_sprite_allocator_and_initializer_side_effects_deferred_to_engine": True,
        "offline_sprite_actor_bytes_changed": 0,
        "source_terminal_sprite_pointers_valid": True,
        "source_terminal_sprites_use_same_model0_reset_shape": True,
        "source_terminal_heap_headers_sha256": (
            EXPECTED_TERMINAL_HEAP_HEADERS_SHA256
        ),
        "source_terminal_heap_blocks_unpinned_and_contiguous": True,
        "source_heap_current_user": 8,
        "source_heap_current_content_type": "0x20",
        "source_heap_consolidation_pending": False,
        "source_sprite_callback_lists_empty": True,
        "source_sprite_callback_list2_delay_zero": True,
        "field_script_entity_already_initialized_zero": True,
        "field_draw_envs_initialized": True,
        "field_script_init_var0_before_queue": EXPECTED_FIELD_SCRIPT_INIT_VAR0,
        "field_script_init_var0_expected_after_queue": (
            EXPECTED_FIELD_SCRIPT_INIT_VAR0_AFTER_QUEUE
        ),
        "native_init_side_effect_opcodes_complete_first_scheduler_pass": True,
        "native_init_stop_completes_next_scheduler_pass": True,
        "native_init_actor_order": list(TERMINAL_ENTITIES),
        "native_init_material_opcode_count": 8,
        "native_allocator_original_mips_spans_pinned": True,
        "native_allocator_object_and_aux_sizes": [
            MODEL0_OBJECT_ALLOCATION_SIZE,
            MODEL0_AUX_ALLOCATION_SIZE,
        ],
        "native_allocator_pointer_reuse_statically_proven": True,
        "native_allocator_no_net_growth_statically_proven": True,
        "native_sprite_callback_list_effect_statically_proven": True,
        "native_walkmesh_fallback_triangle": 0,
        "native_walkmesh_fallback_material_flag": "0x00400000",
        "native_walkmesh_fallback_normal": [0, 0, 0],
        "native_walkmesh_fallback_elevation_and_max_y": [0, 0],
        "native_walkmesh_fallback_xz_retention_requires_smoke": True,
        "terminal_action_pc": f"0x{COMPAT_ACTION_PC:04X}",
        "terminal_action_sha256": COMPAT_ACTION_SHA256,
        "terminal_action_replaces_retired_span": (
            f"0x{COMPAT_ACTION_PC:04X}..0x{RETIRED_ACTION_END_PC - 1:04X}"
        ),
        "terminal_message": TARGET_DIALOGUE_TEXT,
        "terminal_read_only_and_repeatable": True,
        "retired_id45_owner": "e16:s4",
        "retired_id45_reference_pc": f"0x{RETIRED_ID45_REFERENCE_PC:04X}",
        "retired_id45_reference_overwritten": True,
        "retired_id45_owner_all_slots_stopped_in_v232": True,
        "source_reachable_instruction_count": SOURCE_REACHABLE_INSTRUCTION_COUNT,
        "source_reachable_instruction_sha256": SOURCE_REACHABLE_INSTRUCTION_SHA256,
        "target_reachable_instruction_count": TARGET_REACHABLE_INSTRUCTION_COUNT,
        "target_reachable_instruction_sha256": TARGET_REACHABLE_INSTRUCTION_SHA256,
        "source_runtime_current_and_slot_pcs_scanned": (
            SCRIPT_ENTITY_COUNT * (1 + ACTOR_SCRIPT_SLOT_COUNT)
        ),
        "source_runtime_pcs_in_replaced_spans": 0,
        "target_runtime_pcs_in_initializer_cavity": len(expected_queued_pcs),
        "target_runtime_pcs_in_action_span_before_interaction": 0,
        "saved_stance": [EXPECTED_FEI_XZ[0], EXPECTED_FEI_XZ[1], EXPECTED_FEI_YAW],
        "saved_stance_is_within_terminal_reach": True,
        "fei_party_gamestate_field_variables_camera_preserved": True,
        "dialog_windows_preserved_and_closed": True,
        "resident_header_sha256": OLD_HEADER_SHA256,
        "resident_header_and_heap_layout_preserved": True,
        "resident_walkmesh_sha256": WALKMESH_SHA256,
        "allocator_safe": True,
        "resident_heap_allocations_resized_offline": False,
        "resident_compatibility_layout": True,
        "cold_reload_uses_normal_v233": True,
        "runtime_acceptance_pending_manual_smoke_test": True,
        "round_trip_verified": True,
        "changed_resource_ids": list(CHANGED_RESOURCE_IDS),
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "v232_manifest_sha256": OLD_MANIFEST_SHA256,
        "v233_manifest_sha256": NEW_MANIFEST_SHA256,
        "v232_disc_sha256": OLD_DISC_SHA256,
        "v233_disc_sha256": NEW_DISC_SHA256,
        "field": EXPECTED_FIELD,
        "safe_to_mount_after_duckstation_is_fully_closed": True,
        "live_slot1_modified": False,
    }
    return result, report


def _report_blob(report: dict[str, object]) -> bytes:
    return (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=SOURCE_FIXTURE)
    parser.add_argument(
        "--old-disc", type=Path,
        default=PROJECT_ROOT / "output" / OLD_CUE_NAME.replace(".cue", ".bin"),
    )
    parser.add_argument(
        "--new-disc", type=Path,
        default=PROJECT_ROOT / "output" / NEW_CUE_NAME.replace(".cue", ".bin"),
    )
    parser.add_argument(
        "--old-manifest", type=Path,
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v232_stage" / "manifest.json",
    )
    parser.add_argument(
        "--new-manifest", type=Path,
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v233_stage" / "manifest.json",
    )
    for version in (232, 233):
        stage = (
            PROJECT_ROOT / "work" / f"surface_soylent_campaign_v{version}_stage"
            / "clones" / "field_567_disc1_donor"
        )
        prefix = "old" if version == 232 else "new"
        parser.add_argument(f"--{prefix}-script", type=Path, default=stage / "05_scripts.bin")
        parser.add_argument(f"--{prefix}-header", type=Path, default=stage / "header.bin")
        parser.add_argument(f"--{prefix}-dialogue", type=Path, default=stage / "07_dialogue.bin")
    parser.add_argument(
        "--zstd", type=Path,
        default=PROJECT_ROOT / "work" / "duckstation" / "zstd.dll",
    )
    parser.add_argument(
        "--output", type=Path,
        default=(PROJECT_ROOT / "work" / "save_candidates"
                 / "SLUS-00669_1_v233_from_3f09a8ce_field567_empty_terminal_native_init.sav"),
    )
    parser.add_argument(
        "--report", type=Path,
        default=(PROJECT_ROOT / "work" / "save_candidates"
                 / "SLUS-00669_1_v233_from_3f09a8ce_field567_empty_terminal_native_init.json"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        source_path = args.source.resolve()
        output = args.output.resolve()
        report_path = args.report.resolve()
        if output == LIVE_SLOT1 or report_path == LIVE_SLOT1:
            raise SurfaceSlotMigrationError("Output/report may not be the live Slot 1")
        if output == source_path or report_path == source_path:
            raise SurfaceSlotMigrationError("Output/report may not replace the source state")
        if output == report_path:
            raise SurfaceSlotMigrationError("Output and report paths must be distinct")
        _validate_file(args.zstd, ZSTD_SIZE, ZSTD_SHA256, "zstd codec")
        result, report = migrate_v232_slot1_to_v233(
            source_path.read_bytes(),
            old_disc=args.old_disc,
            new_disc=args.new_disc,
            old_manifest=args.old_manifest.read_bytes(),
            new_manifest=args.new_manifest.read_bytes(),
            old_script=args.old_script.read_bytes(),
            new_script=args.new_script.read_bytes(),
            old_header=args.old_header.read_bytes(),
            new_header=args.new_header.read_bytes(),
            old_dialogue=args.old_dialogue.read_bytes(),
            new_dialogue=args.new_dialogue.read_bytes(),
            zstd=media_migration._Zstd(args.zstd),
        )
        report_blob = _report_blob(report)
        if (
            OUTPUT_REPORT_SIZE is not None and len(report_blob) != OUTPUT_REPORT_SIZE
        ) or (
            OUTPUT_REPORT_SHA256 is not None and _sha256(report_blob) != OUTPUT_REPORT_SHA256
        ):
            raise SurfaceSlotMigrationError("V233 report identity drifted")
        if output.exists() and output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Refusing to overwrite a different V233 candidate")
        if report_path.exists() and report_path.read_bytes() != report_blob:
            raise SurfaceSlotMigrationError("Refusing to overwrite a different V233 report")
        output.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        report_path.write_bytes(report_blob)
        if output.read_bytes() != result or report_path.read_bytes() != report_blob:
            raise SurfaceSlotMigrationError("Written V233 candidate/report failed verification")
    except (
        OSError,
        ValueError,
        DialogueFormatError,
        ScriptFormatError,
        SurfaceSlotMigrationError,
        media_migration.StateMigrationError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote V233 candidate: {output}")
    print(f"Wrote migration report: {report_path}")
    print(f"SHA-256: {report['output_sha256']}")
    print("The live Slot 1 was not modified. Install only after DuckStation is fully closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
