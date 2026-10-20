#!/usr/bin/env python3
"""Migrate the audited Rico Slot 1 to the Chapter 1 audio revision.

The saved scene has already passed the stove interaction, so replacing the
disc alone cannot select the corrected music in the resident field.  This
migration redirects entity 0's dormant update PC through four bytes of retired
field-229 code: play native music 0x08 once, then resume the same silent update.
The active Rico/Anne dialogue and its actor are left untouched.

The rebuilt disc contains the burner click/fire helper for future Chapter 1
playthroughs.  The migration also adopts the exact two cached Disc-1 FAT bytes
needed by that build.  It never resizes resident data, writes only a separate
candidate, and refuses DuckStation's live Slot 1.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct
import sys
from typing import Final, Sequence


if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from tools import build_rico_arc as rico  # noqa: E402
from tools.migrate_duckstation_disc_state import (  # noqa: E402
    DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
    DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    DUCKSTATION_STATE_HEADER_SIZE,
    DUCKSTATION_STATE_MAGIC,
    DUCKSTATION_ZSTD_COMPRESSION_TYPE,
    ZSTD_MAGIC,
    _Zstd,
    _archive_table,
)
from tools.migrate_rico_arc_father_dialogue_slot1 import (  # noqa: E402
    _differences,
    _raw_dialogue_blocks,
)
from tools.migrate_rico_arc_firewood_reply_slot1 import (  # noqa: E402
    ACTIVE_DIALOGUE_ID,
    ACTIVE_DIALOGUE_OFFSET,
    DIALOG_WINDOWS,
    DIALOG_WINDOW_COUNT,
    DIALOG_WINDOW_STATUS_OFFSET,
    DIALOG_WINDOW_STRIDE,
    EXPECTED_ACTOR_ARRAY_GUEST_POINTER,
    EXPECTED_ACTOR_COUNT,
    EXPECTED_GAME_SCENE_MAP,
    EXPECTED_WINDOW0_CURRENT_POINTER,
    EXPECTED_WINDOW0_START_POINTER,
    EXPECTED_WINDOW_STATUSES,
    FIELD_CUR_DIALOGUE_FILE,
    RESIDENT_DIALOGUE_GUEST_POINTER,
    WINDOW0_CURRENT_POINTER_OFFSET,
    WINDOW0_START_POINTER_OFFSET,
)
from tools.migrate_rico_arc_night_dialogue_slot1 import (  # noqa: E402
    _aliases_existing_file,
)
from tools.xgdialog import decode_text  # noqa: E402
from tools.xgdisc import Mode2Image  # noqa: E402
from tools.xgfield import parse_field  # noqa: E402
from tools.xgscript import AtelScript  # noqa: E402
from work.read_duckstation_runtime import (  # noqa: E402
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


ROOT: Final = Path(__file__).resolve().parents[3]
LIVE_SLOT_ONE: Final = ROOT / "emulator_data" / "SLUS-00664_1.sav"
DEFAULT_ZSTD: Final = ROOT / "work" / "duckstation" / "zstd.dll"
DEFAULT_NEW_DISC: Final = (
    ROOT / "work" / "raudio" / "Xenogears_Rico_Arc_Disc_1.bin"
)

SOURCE_STATE_SIZE: Final = 1_365_946
SOURCE_STATE_SHA256: Final = (
    "4e8c3b35f30dc65be3cc53d6a214d083901360bde666b9d4124a16e7204dbff8"
)
SOURCE_FRAME_OFFSET: Final = 0x6DD0
SOURCE_COMPRESSED_SIZE: Final = 1_337_834
SOURCE_PAYLOAD_SIZE: Final = 3_817_429
SOURCE_PAYLOAD_SHA256: Final = (
    "5efe6b1cc63038b6baa2f1c5037ff1781d491511d74d20b75beb66fdff2afa64"
)
SOURCE_RAM_OFFSET: Final = 0x1A62
SOURCE_RAM_SHA256: Final = (
    "e7d405133614c32b569f957a8fba8cda688a2705febc6b2259ddc2433e601912"
)
SOURCE_MEDIA_PATH: Final = (
    rb"C:\Users\Chad\Xenogears_Reimagined\output\rico_arc\Xenogears_Rico_Arc.m3u"
)

TARGET_DISC_SIZE: Final = 719_175_744
TARGET_DISC_SHA256: Final = (
    "eec00dbbf18d485807e5373b92cd2fbb0c7f0af4e62160a8208ec06e3aefed45"
)
HOUSE_FIELD_CANONICAL_ID: Final = 2048
HOUSE_FIELD_SECTOR: Final = 230_237
TARGET_HOUSE_FIELD_SIZE: Final = 37_632
TARGET_HOUSE_FIELD_SHA256: Final = (
    "b70f5d01686ee484ba835d960a019b3663af412127edcea8cfa1ba3a3598b65d"
)
SCRIPT_COMPONENT_INDEX: Final = 5
DIALOGUE_COMPONENT_INDEX: Final = 7
TARGET_SCRIPT_SIZE: Final = 5_426
TARGET_SCRIPT_SHA256: Final = (
    "067ce9f7bd966f7af4568963ffc75ab14784665e29888b8f6c85b5d1d5cc6063"
)
TARGET_DIALOGUE_SIZE: Final = 11_497
TARGET_DIALOGUE_SHA256: Final = (
    "fa88a677cb01fb087bc5f5a3a6fb1dd808604f5df4c91e395e2eefcd119a8dbb"
)

RESIDENT_SCRIPT_PAYLOAD_OFFSET: Final = 0x10C822
RESIDENT_SCRIPT_SIZE: Final = 5_426
SOURCE_RESIDENT_SCRIPT_SHA256: Final = (
    "d73d6bcc785660f9622a561188ea672cfc8a3cf22e6eeaf69071c8b66a1df074"
)
TARGET_RESIDENT_SCRIPT_SHA256: Final = (
    "2b527fa52e328e8a440f2f847eed0ee483e3413e8c4fe8846d0ed36b29e9b7f5"
)
RESIDENT_SCRIPT_GUEST_POINTER: Final = 0x8010ADC0
RESIDENT_SCRIPT_BYTECODE_OFFSET: Final = 0x0704
MUSIC_BRIDGE_PC: Final = 0x035B
MUSIC_BRIDGE_COMPONENT_OFFSET: Final = (
    RESIDENT_SCRIPT_BYTECODE_OFFSET + MUSIC_BRIDGE_PC
)
SOURCE_MUSIC_BRIDGE: Final = bytes.fromhex("02 06 04 0E")
TARGET_MUSIC_BRIDGE: Final = bytes.fromhex("75 08 80 5B")
SILENT_UPDATE_PC: Final = 0x037E
CHAPTER_ONE_DOOR_OPEN_END_PC: Final = 0x035B

RESIDENT_DIALOGUE_PAYLOAD_OFFSET: Final = 0x10DD9E
RESIDENT_DIALOGUE_SIZE: Final = 11_794
SOURCE_RESIDENT_DIALOGUE_SHA256: Final = (
    "d0f0326d0ae060d5685bfa0419307c76649c2690a3d2a372fb53f39b2b0bbcbb"
)
RESIDENT_DIALOGUE_ALLOCATED_SIZE: Final = 11_803
SOURCE_DIALOGUE_ALLOCATION_SHA256: Final = (
    "31fb3d367cb90a926b3a93afc9943794410e8b773facf83e7980eeff069c7439"
)
RESIDENT_DIALOGUE_UNUSED_TAIL: Final = bytes(9)
RESIDENT_DIALOGUE_ALIGNMENT: Final = bytes(7)
NEXT_ALLOCATOR_HEADER: Final = bytes.fromhex(
    "60 1D 00 02 2D E4 4B 12 6B 51 90 FC 10 80 5E C4 01 81"
)
SCRIPT_DIALOGUE_GAP_SHA256: Final = (
    "cb98285922eb7787dd16492152a83067ba80c92456be560eaa25c3d7d0936c1e"
)

ENTITY_ZERO_ACTOR_DATA: Final = 0x111DEC
ENTITY_ZERO_SAVED_PC_RAM_OFFSET: Final = ENTITY_ZERO_ACTOR_DATA + 0x8C
ENTITY_ZERO_CURRENT_PC_RAM_OFFSET: Final = ENTITY_ZERO_ACTOR_DATA + 0xCC
ENTITY_ZERO_SAVED_PC_PAYLOAD_OFFSET: Final = (
    SOURCE_RAM_OFFSET + ENTITY_ZERO_SAVED_PC_RAM_OFFSET
)
ENTITY_ZERO_CURRENT_PC_PAYLOAD_OFFSET: Final = (
    SOURCE_RAM_OFFSET + ENTITY_ZERO_CURRENT_PC_RAM_OFFSET
)
SOURCE_ENTITY_ZERO_PC: Final = struct.pack("<H", SILENT_UPDATE_PC)
TARGET_ENTITY_ZERO_PC: Final = struct.pack("<H", MUSIC_BRIDGE_PC)
EXPECTED_GLOBAL_VM_ACTOR: Final = 0x80114968
EXPECTED_GLOBAL_VM_SCRIPT: Final = 0x8010B4C4
ACTIVE_ENTITY: Final = 22
ACTIVE_ENTITY_DATA: Final = 0x114440
ACTIVE_ENTITY_DATA_SIZE: Final = 0x1B8
ACTIVE_ENTITY_PC: Final = 0x08C9
EXPECTED_FIELD_STATE: Final = 0x3CCE
EXPECTED_ACTIVE_TEXT: Final = (
    "<Rico>\nThere is blood again. The\nmedicine isn't helping.<New>"
    "Tell me what to do, Mom. I\ncan find another doctor.<Close>"
)

ARCHIVE_TABLE_SIZE: Final = 0x8000
ARCHIVE_TABLE_PAYLOAD_OFFSET: Final = 0x11A66
SOURCE_NORMALIZED_ARCHIVE_TABLE_SHA256: Final = (
    "cd04c8934901721ff1e7c9352b678dfd4b311a528e449d262126e1710f5d41db"
)
SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "1636b11610b1ab28b4edd50558da135250c1d130bc8d261d9c6ce1018a3b43db"
)
SOURCE_VOLATILE_ARCHIVE_BYTE: Final = 0xC4
TARGET_ARCHIVE_TABLE_SHA256: Final = (
    "ce9f08126d63171be5c6b4d30cfac6e536d19d853063386b816b3bbb4cac3478"
)
TARGET_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "c2589b36980daa8fa13b47f3288ed8717c4fbc3fdbd718515fca2bd1e662c7ea"
)
ARCHIVE_TABLE_DIFFS: Final = (
    (0x2525, 0x2C, 0x24),
    (0x3803, 0x04, 0x00),
)

GAME_SCENE_MAP: Final = 0x04F34C
GAMESTATE_SIZE: Final = 0x2358
PREVIOUS_MUSIC_GAMESTATE_OFFSET: Final = 0x2322
SOURCE_PREVIOUS_MUSIC: Final = 0x2F
FIELD_VARIABLE_BANK_SIZE: Final = 0x800
EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT: Final = 8
EXPECTED_OUTPUT_PAYLOAD_SHA256: Final = (
    "9db734a2c937b82618eb05546190e65337171a57d525b86aececaf1831ad2269"
)
EXPECTED_OUTPUT_RAM_SHA256: Final = (
    "7f257c90a464825110d19c2c51dde4a02071c8893634239b650abe022f4b861a"
)
EXPECTED_COMPRESSED_SHA256: Final = (
    "7928a664b711fdf958a94df951639bac46dc828a42b3fc00daeb535f825e4f1c"
)
EXPECTED_OUTPUT_SIZE: Final = 1_365_946
EXPECTED_OUTPUT_SHA256: Final = (
    "3f2681f6f14427952fd58e6055186da5635c3f51b0439653abd3a5f0f61501ce"
)


class RicoFarawayFireMigrationError(RuntimeError):
    """Raised before output whenever the pinned migration contract drifts."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _validated_target_resources(new_disc: Path) -> tuple[bytes, bytes, bytes]:
    if (
        not new_disc.is_file()
        or new_disc.stat().st_size != TARGET_DISC_SIZE
        or _file_sha256(new_disc) != TARGET_DISC_SHA256
    ):
        raise RicoFarawayFireMigrationError("Final staged Rico Disc 1 identity changed")
    image = Mode2Image(new_disc)
    entries = image.read_index()
    if HOUSE_FIELD_CANONICAL_ID >= len(entries):
        raise RicoFarawayFireMigrationError("Final staged Disc 1 lost Chapter 1")
    entry = entries[HOUSE_FIELD_CANONICAL_ID]
    if (
        entry.kind != "file"
        or entry.sector != HOUSE_FIELD_SECTOR
        or entry.size != TARGET_HOUSE_FIELD_SIZE
    ):
        raise RicoFarawayFireMigrationError("Final Chapter 1 allocation changed")
    raw = image.extract_entry(entry)
    if _sha256(raw) != TARGET_HOUSE_FIELD_SHA256:
        raise RicoFarawayFireMigrationError("Final Chapter 1 field identity changed")
    parsed = parse_field(raw)
    if len(parsed.parts) != 9:
        raise RicoFarawayFireMigrationError("Final Chapter 1 component count changed")
    script = parsed.parts[SCRIPT_COMPONENT_INDEX].data
    dialogue = parsed.parts[DIALOGUE_COMPONENT_INDEX].data
    if (
        (len(script), _sha256(script)) != (TARGET_SCRIPT_SIZE, TARGET_SCRIPT_SHA256)
        or (len(dialogue), _sha256(dialogue))
        != (TARGET_DIALOGUE_SIZE, TARGET_DIALOGUE_SHA256)
    ):
        raise RicoFarawayFireMigrationError("Final Chapter 1 components changed")
    editor = AtelScript(script)
    director_pc = editor.get_script_pointer(0, 0)
    fire = rico._chapter_one_stove_audio_helper()
    if (
        editor.bytecode[director_pc : director_pc + 7]
        != rico._sanitized_director(rico.CHAPTER_ONE_MUSIC_ID)
        or editor.bytecode[
            rico.CHAPTER_ONE_STOVE_AUDIO_HELPER_PC :
            rico.CHAPTER_ONE_STOVE_AUDIO_HELPER_PC + len(fire)
        ]
        != fire
        or script.count(rico.CHAPTER_ONE_STOVE_AUDIO_HELPER_CALL) != 1
        or rico._play_sound_effect(0x46) in fire
    ):
        raise RicoFarawayFireMigrationError("Final Chapter 1 audio topology changed")
    table = _archive_table(new_disc)
    if len(table) != ARCHIVE_TABLE_SIZE or _sha256(table) != TARGET_ARCHIVE_TABLE_SHA256:
        raise RicoFarawayFireMigrationError("Final Disc-1 archive table changed")
    return script, dialogue, table


def _build_resident_script(source: bytes) -> bytes:
    if (
        len(source) != RESIDENT_SCRIPT_SIZE
        or _sha256(source) != SOURCE_RESIDENT_SCRIPT_SHA256
    ):
        raise RicoFarawayFireMigrationError("Resident script identity changed")
    editor = AtelScript(source)
    if (
        editor.bytecode_offset != RESIDENT_SCRIPT_BYTECODE_OFFSET
        or editor.get_script_pointer(0, 1) != SILENT_UPDATE_PC
        or editor.bytecode[SILENT_UPDATE_PC : SILENT_UPDATE_PC + 1] != b"\x5B"
        or editor.bytecode[MUSIC_BRIDGE_PC : MUSIC_BRIDGE_PC + 4]
        != SOURCE_MUSIC_BRIDGE
        or CHAPTER_ONE_DOOR_OPEN_END_PC
        != rico.CHAPTER_ONE_DOOR_OPEN_PC + len(rico.CHAPTER_ONE_DOOR_OPEN_BODY)
    ):
        raise RicoFarawayFireMigrationError("Resident music cave topology changed")
    for entity in range(editor.entity_count):
        for script_index in range(32):
            pointer = editor.get_script_pointer(entity, script_index)
            if MUSIC_BRIDGE_PC <= pointer < 0x0374:
                raise RicoFarawayFireMigrationError(
                    "A live script pointer enters the resident music cave"
                )
    result = bytearray(source)
    start = MUSIC_BRIDGE_COMPONENT_OFFSET
    result[start : start + 4] = TARGET_MUSIC_BRIDGE
    output = bytes(result)
    if (
        _sha256(output) != TARGET_RESIDENT_SCRIPT_SHA256
        or _differences(source, output)
        != tuple(
            (start + index, old, new)
            for index, (old, new) in enumerate(
                zip(SOURCE_MUSIC_BRIDGE, TARGET_MUSIC_BRIDGE, strict=True)
            )
        )
    ):
        raise RicoFarawayFireMigrationError("Resident music bridge is not exact")
    return output


def migrate_state(
    state: bytes,
    *,
    zstd: _Zstd,
    new_disc: Path,
) -> tuple[bytes, dict[str, object]]:
    state_hash = _sha256(state)
    if (len(state), state_hash) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise RicoFarawayFireMigrationError(
            "Source Slot 1 identity changed: "
            f"{len(state)} bytes / {state_hash}; expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    if (
        len(state) < DUCKSTATION_STATE_HEADER_SIZE
        or state[:4] != DUCKSTATION_STATE_MAGIC
        or state.count(SOURCE_MEDIA_PATH) != 1
    ):
        raise RicoFarawayFireMigrationError(
            "Source is not the supported stable-path DuckStation state"
        )
    _target_script, target_dialogue, target_table = _validated_target_resources(
        new_disc.resolve()
    )
    compression_type, compressed_size, payload_size, frame_offset = struct.unpack_from(
        "<IIII", state, DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET
    )
    if compression_type != DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise RicoFarawayFireMigrationError("Source is not Zstandard-compressed")
    if (
        compressed_size != SOURCE_COMPRESSED_SIZE
        or payload_size != SOURCE_PAYLOAD_SIZE
        or frame_offset != SOURCE_FRAME_OFFSET
        or frame_offset + compressed_size != len(state)
    ):
        raise RicoFarawayFireMigrationError("Source frame layout changed")
    frame = state[frame_offset:]
    if not frame.startswith(ZSTD_MAGIC) or zstd.frame_size(frame) != compressed_size:
        raise RicoFarawayFireMigrationError("Source compressed frame is invalid")
    source_payload = zstd.decompress(frame)
    if (
        len(source_payload) != SOURCE_PAYLOAD_SIZE
        or _sha256(source_payload) != SOURCE_PAYLOAD_SHA256
    ):
        raise RicoFarawayFireMigrationError("Source payload identity changed")
    ram_offset = _psx_ram_offset(source_payload)
    if ram_offset != SOURCE_RAM_OFFSET or ram_offset + RAM_SIZE > len(source_payload):
        raise RicoFarawayFireMigrationError("Source PSX RAM layout changed")
    source_ram = source_payload[ram_offset : ram_offset + RAM_SIZE]
    if _sha256(source_ram) != SOURCE_RAM_SHA256:
        raise RicoFarawayFireMigrationError("Source PSX RAM identity changed")

    script_start = RESIDENT_SCRIPT_PAYLOAD_OFFSET
    script_end = script_start + RESIDENT_SCRIPT_SIZE
    dialogue_start = RESIDENT_DIALOGUE_PAYLOAD_OFFSET
    dialogue_end = dialogue_start + RESIDENT_DIALOGUE_SIZE
    allocated_end = dialogue_start + RESIDENT_DIALOGUE_ALLOCATED_SIZE
    aligned_end = allocated_end + len(RESIDENT_DIALOGUE_ALIGNMENT)
    header_end = aligned_end + len(NEXT_ALLOCATOR_HEADER)
    source_script = source_payload[script_start:script_end]
    source_dialogue = source_payload[dialogue_start:dialogue_end]
    if (
        _sha256(source_dialogue) != SOURCE_RESIDENT_DIALOGUE_SHA256
        or _sha256(source_payload[script_end:dialogue_start])
        != SCRIPT_DIALOGUE_GAP_SHA256
        or _sha256(source_payload[dialogue_start:allocated_end])
        != SOURCE_DIALOGUE_ALLOCATION_SHA256
        or source_payload[dialogue_end:allocated_end] != RESIDENT_DIALOGUE_UNUSED_TAIL
        or source_payload[allocated_end:aligned_end] != RESIDENT_DIALOGUE_ALIGNMENT
        or source_payload[aligned_end:header_end] != NEXT_ALLOCATOR_HEADER
    ):
        raise RicoFarawayFireMigrationError("Resident dialogue allocator changed")
    if _sha256(target_dialogue) != TARGET_DIALOGUE_SHA256:
        raise RicoFarawayFireMigrationError("Target dialogue identity changed")

    blocks = _raw_dialogue_blocks(source_dialogue)
    active = blocks[ACTIVE_DIALOGUE_ID]
    statuses = tuple(
        struct.unpack_from(
            "<h",
            source_ram,
            DIALOG_WINDOWS + index * DIALOG_WINDOW_STRIDE + DIALOG_WINDOW_STATUS_OFFSET,
        )[0]
        for index in range(DIALOG_WINDOW_COUNT)
    )
    actor_array = struct.unpack_from("<I", source_ram, FIELD_ACTORS)[0]
    entity_zero_pointer = struct.unpack_from(
        "<I",
        source_ram,
        (actor_array & 0x1FFFFFFF) + FIELD_ACTOR_DATA_POINTER,
    )[0]
    active_actor_pointer = struct.unpack_from(
        "<I",
        source_ram,
        (actor_array & 0x1FFFFFFF)
        + ACTIVE_ENTITY * FIELD_ACTOR_STRIDE
        + FIELD_ACTOR_DATA_POINTER,
    )[0]
    if (
        struct.unpack_from("<I", source_ram, GAME_SCENE_MAP)[0]
        != EXPECTED_GAME_SCENE_MAP
        or struct.unpack_from("<I", source_ram, FIELD_NUM_ACTORS)[0]
        != EXPECTED_ACTOR_COUNT
        or actor_array != EXPECTED_ACTOR_ARRAY_GUEST_POINTER
        or entity_zero_pointer != (0x80000000 | ENTITY_ZERO_ACTOR_DATA)
        or active_actor_pointer != (0x80000000 | ACTIVE_ENTITY_DATA)
        or struct.unpack_from("<I", source_ram, FIELD_CUR_SCRIPT_FILE)[0]
        != RESIDENT_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", source_ram, FIELD_CUR_DIALOGUE_FILE)[0]
        != RESIDENT_DIALOGUE_GUEST_POINTER
        or struct.unpack_from("<I", source_ram, FIELD_SCRIPT_VM_CUR_ACTOR)[0]
        != EXPECTED_GLOBAL_VM_ACTOR
        or struct.unpack_from("<I", source_ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA)[0]
        != EXPECTED_GLOBAL_VM_SCRIPT
        or statuses != EXPECTED_WINDOW_STATUSES
        or struct.unpack_from("<I", source_ram, WINDOW0_START_POINTER_OFFSET)[0]
        != EXPECTED_WINDOW0_START_POINTER
        or struct.unpack_from("<I", source_ram, WINDOW0_CURRENT_POINTER_OFFSET)[0]
        != EXPECTED_WINDOW0_CURRENT_POINTER
        or active.offset != ACTIVE_DIALOGUE_OFFSET
        or decode_text(active.payload) != EXPECTED_ACTIVE_TEXT
        or struct.unpack_from("<H", source_ram, FIELD_SCRIPT_MEMORY + 0x07D0)[0]
        != EXPECTED_FIELD_STATE
        or source_ram[GAME_STATE + PREVIOUS_MUSIC_GAMESTATE_OFFSET]
        != SOURCE_PREVIOUS_MUSIC
        or source_payload[
            ENTITY_ZERO_SAVED_PC_PAYLOAD_OFFSET :
            ENTITY_ZERO_SAVED_PC_PAYLOAD_OFFSET + 2
        ]
        != SOURCE_ENTITY_ZERO_PC
        or source_payload[
            ENTITY_ZERO_CURRENT_PC_PAYLOAD_OFFSET :
            ENTITY_ZERO_CURRENT_PC_PAYLOAD_OFFSET + 2
        ]
        != SOURCE_ENTITY_ZERO_PC
    ):
        raise RicoFarawayFireMigrationError("Live field/window topology changed")
    actor_array_ram = actor_array & 0x1FFFFFFF
    for entity in range(EXPECTED_ACTOR_COUNT):
        actor_data_pointer = struct.unpack_from(
            "<I",
            source_ram,
            actor_array_ram
            + entity * FIELD_ACTOR_STRIDE
            + FIELD_ACTOR_DATA_POINTER,
        )[0]
        actor_data = actor_data_pointer & 0x1FFFFFFF
        if not 0 <= actor_data <= RAM_SIZE - 0xCE:
            raise RicoFarawayFireMigrationError("Live actor data pointer changed")
        for pc_offset in (0x8C, 0xCC):
            pc = struct.unpack_from("<H", source_ram, actor_data + pc_offset)[0]
            if MUSIC_BRIDGE_PC <= pc < 0x0374:
                raise RicoFarawayFireMigrationError(
                    "A live actor PC already enters the resident music cave"
                )
    active_entity = source_ram[
        ACTIVE_ENTITY_DATA : ACTIVE_ENTITY_DATA + ACTIVE_ENTITY_DATA_SIZE
    ]
    if (
        struct.unpack_from("<H", active_entity, 0x8C)[0] != ACTIVE_ENTITY_PC
        or struct.unpack_from("<H", active_entity, 0xCC)[0] != ACTIVE_ENTITY_PC
    ):
        raise RicoFarawayFireMigrationError("Live actor VM topology changed")

    table_start = ARCHIVE_TABLE_PAYLOAD_OFFSET
    table_end = table_start + ARCHIVE_TABLE_SIZE
    source_table = source_payload[table_start:table_end]
    normalized_source_table = source_table[:-1] + target_table[-1:]
    if (
        _sha256(source_table) != SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256
        or source_table[-1] != SOURCE_VOLATILE_ARCHIVE_BYTE
        or _sha256(normalized_source_table)
        != SOURCE_NORMALIZED_ARCHIVE_TABLE_SHA256
        or _differences(normalized_source_table, target_table) != ARCHIVE_TABLE_DIFFS
    ):
        raise RicoFarawayFireMigrationError("Resident Disc-1 FAT contract changed")

    resident_script = _build_resident_script(source_script)
    payload = bytearray(source_payload)
    payload[script_start:script_end] = resident_script
    for absolute in (
        ENTITY_ZERO_SAVED_PC_PAYLOAD_OFFSET,
        ENTITY_ZERO_CURRENT_PC_PAYLOAD_OFFSET,
    ):
        if payload[absolute : absolute + 2] != SOURCE_ENTITY_ZERO_PC:
            raise RicoFarawayFireMigrationError("Entity 0 resume PC changed")
        payload[absolute : absolute + 2] = TARGET_ENTITY_ZERO_PC
    for relative, old, new in ARCHIVE_TABLE_DIFFS:
        absolute = table_start + relative
        if payload[absolute] != old:
            raise RicoFarawayFireMigrationError("Resident FAT byte changed")
        payload[absolute] = new
    final_payload = bytes(payload)
    expected_changes = tuple(
        sorted(
            (
                *((script_start + o, a, b) for o, a, b in _differences(source_script, resident_script)),
                *(
                    (absolute, SOURCE_ENTITY_ZERO_PC[0], TARGET_ENTITY_ZERO_PC[0])
                    for absolute in (
                        ENTITY_ZERO_SAVED_PC_PAYLOAD_OFFSET,
                        ENTITY_ZERO_CURRENT_PC_PAYLOAD_OFFSET,
                    )
                ),
                *((table_start + o, a, b) for o, a, b in ARCHIVE_TABLE_DIFFS),
            )
        )
    )
    final_ram = final_payload[ram_offset : ram_offset + RAM_SIZE]
    if (
        _differences(source_payload, final_payload) != expected_changes
        or len(expected_changes) != EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT
        or _sha256(final_payload) != EXPECTED_OUTPUT_PAYLOAD_SHA256
        or _sha256(final_ram) != EXPECTED_OUTPUT_RAM_SHA256
        or final_payload[dialogue_start:header_end]
        != source_payload[dialogue_start:header_end]
        or final_payload[script_end:dialogue_start]
        != source_payload[script_end:dialogue_start]
        or final_ram[ACTIVE_ENTITY_DATA : ACTIVE_ENTITY_DATA + ACTIVE_ENTITY_DATA_SIZE]
        != active_entity
        or final_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE]
        != source_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE]
        or final_ram[FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE]
        != source_ram[
            FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE
        ]
        or final_ram[
            DIALOG_WINDOWS : DIALOG_WINDOWS + DIALOG_WINDOW_STRIDE * DIALOG_WINDOW_COUNT
        ]
        != source_ram[
            DIALOG_WINDOWS : DIALOG_WINDOWS + DIALOG_WINDOW_STRIDE * DIALOG_WINDOW_COUNT
        ]
    ):
        raise RicoFarawayFireMigrationError("Migration whitelist/state check failed")
    final_table = final_payload[table_start:table_end]
    if (
        _sha256(final_table) != TARGET_RESIDENT_ARCHIVE_TABLE_SHA256
        or final_table[:-1] != target_table[:-1]
        or final_table[-1] != SOURCE_VOLATILE_ARCHIVE_BYTE
    ):
        raise RicoFarawayFireMigrationError("Final resident FAT is not exact")

    compressed = zstd.compress(final_payload)
    if (
        len(compressed) != SOURCE_COMPRESSED_SIZE
        or _sha256(compressed) != EXPECTED_COMPRESSED_SHA256
    ):
        raise RicoFarawayFireMigrationError("Output compressed frame changed")
    prefix = bytearray(state[:frame_offset])
    struct.pack_into(
        "<I", prefix, DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET, len(compressed)
    )
    result = bytes(prefix) + compressed
    result_hash = _sha256(result)
    if (
        zstd.decompress(result[frame_offset:]) != final_payload
        or len(result) != EXPECTED_OUTPUT_SIZE
        or result_hash != EXPECTED_OUTPUT_SHA256
    ):
        raise RicoFarawayFireMigrationError(
            f"Candidate identity changed: {len(result)} / {result_hash}"
        )
    return result, {
        "source_state_sha256": state_hash,
        "output_state_sha256": result_hash,
        "payload_changed_byte_count": len(expected_changes),
        "resident_script_changed_byte_count": len(_differences(source_script, resident_script)),
        "resident_fat_changed_byte_count": len(ARCHIVE_TABLE_DIFFS),
        "entity_zero_resume_pc_changes": 2,
        "active_dialogue_window_preserved": True,
        "active_dialogue_actor_preserved": True,
        "field_progress_preserved": True,
        "allocator_header_preserved": True,
        "music_bridge_pc": MUSIC_BRIDGE_PC,
        "media_path_rewrite_required": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--zstd", type=Path, default=DEFAULT_ZSTD)
    parser.add_argument("--new-disc", type=Path, default=DEFAULT_NEW_DISC)
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = args.source.resolve()
    output = args.output.resolve()
    zstd_path = args.zstd.resolve()
    new_disc = args.new_disc.resolve()
    if _aliases_existing_file(output, LIVE_SLOT_ONE.resolve()):
        raise SystemExit("Output may not be DuckStation's live Slot 1 or an alias of it")
    for protected, label in (
        (source, "source state"),
        (zstd_path, "zstd library"),
        (new_disc, "staged Disc 1"),
    ):
        if _aliases_existing_file(output, protected):
            raise SystemExit(f"Output must be separate from the {label}")
    for path, label in (
        (source, "source state"),
        (zstd_path, "zstd library"),
        (new_disc, "final staged Rico Disc 1"),
    ):
        if not path.is_file():
            raise SystemExit(f"{label} does not exist: {path}")
    if output.exists() and not args.force:
        raise SystemExit(f"Output already exists (use --force): {output}")
    try:
        result, report = migrate_state(
            source.read_bytes(), zstd=_Zstd(zstd_path), new_disc=new_disc
        )
    except RicoFarawayFireMigrationError as exc:
        raise SystemExit(str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)
    if output.read_bytes() != result:
        raise SystemExit("Written candidate changed on disk")
    print(f"Wrote audio-safe Rico candidate: {output}")
    for key, value in report.items():
        print(f"{key}: {value}")
    print("The source and DuckStation's live Slot 1 were not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
