#!/usr/bin/env python3
"""Migrate the audited Rico Slot 1 to the revised stonebell conversation.

The rebuilt house dialogue is smaller and has a different packed layout, so
it cannot replace the resident component without invalidating live pointers.
This migration installs an allocator-safe bridge instead:

* rebuilt dialogue 51 is padded into resident dialogue 51's fixed span;
* rebuilt dialogue 52 is padded into dead resident dialogue 69's fixed span;
* the sole resident F5 call to dialogue 52 is redirected to dialogue 69; and
* the exact two-byte Disc-1 FAT size update is adopted.

Every dialogue offset, the active window, the father bridge, unrelated script
and dialogue bytes, and allocator neighbors remain fixed.  Only the exact
audited state and staged Disc 1 are accepted.  The tool always writes a
separate candidate and refuses DuckStation's live Slot 1.
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
    _choice_command,
    _dialogue_command,
    _dialogue_dimensions_offset,
    _differences,
    _raw_dialogue_blocks,
)
from tools.migrate_rico_arc_night_dialogue_slot1 import (  # noqa: E402
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
    _aliases_existing_file,
)
from tools.xgdialog import decode_text, encode_text  # noqa: E402
from tools.xgdisc import Mode2Image  # noqa: E402
from tools.xgfield import parse_field  # noqa: E402
from work.read_duckstation_runtime import (  # noqa: E402
    FIELD_ACTORS,
    FIELD_CUR_SCRIPT_FILE,
    FIELD_NUM_ACTORS,
    FIELD_SCRIPT_MEMORY,
    GAME_STATE,
    RAM_SIZE,
    _psx_ram_offset,
)


ROOT: Final = Path(__file__).resolve().parents[3]
LIVE_SLOT_ONE: Final = ROOT / "emulator_data" / "SLUS-00664_1.sav"
DEFAULT_ZSTD: Final = ROOT / "work" / "duckstation" / "zstd.dll"
DEFAULT_NEW_DISC: Final = (
    ROOT / "work" / "rico_flower_stage" / "Xenogears_Rico_Arc_Disc_1.bin"
)

SOURCE_STATE_SIZE: Final = 1_366_026
SOURCE_STATE_SHA256: Final = (
    "a35acf06ace2c5c38fadfb1c30bf257eec09a53d63583f6b0d31fc826a87e211"
)
SOURCE_FRAME_OFFSET: Final = 0x6DD0
SOURCE_COMPRESSED_SIZE: Final = 1_337_914
SOURCE_PAYLOAD_SIZE: Final = 3_817_429
SOURCE_PAYLOAD_SHA256: Final = (
    "2e1e4f1eeeeb0ad407bad8cf91ec5bb0b8a170eed16a625e5bc47f247d4b071c"
)
SOURCE_RAM_OFFSET: Final = 0x1A62
SOURCE_RAM_SHA256: Final = (
    "c8abd49f1d017ed6a2b3103fc701b54731490b393d5a9fde788bb57cffaf68a2"
)
SOURCE_MEDIA_PATH: Final = (
    rb"C:\Users\Chad\Xenogears_Reimagined\output\rico_arc\Xenogears_Rico_Arc.m3u"
)

TARGET_DISC_SIZE: Final = 719_175_744
TARGET_DISC_SHA256: Final = (
    "23e183d94baf6c691a565cc72608df66057287ae7db7bcb0a5dfed0697614b38"
)
HOUSE_FIELD_CANONICAL_ID: Final = 2048
HOUSE_FIELD_SECTOR: Final = 230_237
TARGET_HOUSE_FIELD_SIZE: Final = 37_636
TARGET_HOUSE_FIELD_SHA256: Final = (
    "334dcdfd03610f7a5d7a3381d2e738aeee7795591a024c1433e72f8e8f7b3e18"
)
SCRIPT_COMPONENT_INDEX: Final = 5
DIALOGUE_COMPONENT_INDEX: Final = 7
TARGET_SCRIPT_SIZE: Final = 5_426
TARGET_SCRIPT_SHA256: Final = (
    "f8c5fa31b2e5654a505df37c7405c8ce8b486860ef781033dbdef39a44d8145a"
)
TARGET_DIALOGUE_SIZE: Final = 11_497
TARGET_DIALOGUE_SHA256: Final = (
    "fa88a677cb01fb087bc5f5a3a6fb1dd808604f5df4c91e395e2eefcd119a8dbb"
)
TARGET_DIALOGUE_BLOCK_COUNT: Final = 128

TARGET_QUESTION_DIALOGUE_ID: Final = 51
TARGET_QUESTION_OFFSET: Final = 0x0F36
TARGET_QUESTION_SIZE: Final = 176
TARGET_QUESTION_DIMENSIONS: Final = (54, 3)
TARGET_QUESTION_TEXT: Final = (
    "Anne\nDo you remember where you\nfound that stonebell, Rico?<New>"
    "<Rico>\nIn the streets near the\nmarket.<New>"
    "I felt bad because it was\nstepped on.<New>"
    "Remember you said we could\ntry to save it?<Close>"
)
TARGET_LESSON_DIALOGUE_ID: Final = 52
TARGET_LESSON_OFFSET: Final = 0x0FE6
TARGET_LESSON_SIZE: Final = 368
TARGET_LESSON_DIMENSIONS: Final = (58, 3)
TARGET_LESSON_TEXT: Final = (
    "Anne\nYes, I remember.<New>That stonebell is the most\n"
    "precious gift I've ever\nreceived.<New>Look how healthy it is now\n"
    "because you've been taking\ncare of it.<New>Stonebells take root between\n"
    "bare stones, where almost\nnothing else can grow.<New>"
    "Still, their pale blue bells\nalways turn toward the light.<New>"
    "You have a good soul, Rico.<New>Never let this world forget\n"
    "that.<New><Rico>\nI won't, Mom...<Close>"
)

RESIDENT_SCRIPT_PAYLOAD_OFFSET: Final = 0x10C822
RESIDENT_SCRIPT_SIZE: Final = 5_426
SOURCE_RESIDENT_SCRIPT_SHA256: Final = (
    "c61094be0baf53aa838f7c29871d963d0a1bc40c08888de099b12f81913dcc29"
)
EXPECTED_RESIDENT_SCRIPT_SHA256: Final = (
    "d73d6bcc785660f9622a561188ea672cfc8a3cf22e6eeaf69071c8b66a1df074"
)
FLOWER_LESSON_COMMAND_OFFSET: Final = 0x0DBD
FLOWER_LESSON_OPERAND_OFFSET: Final = 0x0DBE
SOURCE_FLOWER_LESSON_COMMAND: Final = bytes.fromhex("F5 34 00 00 9C")
TARGET_FLOWER_LESSON_COMMAND: Final = bytes.fromhex("F5 45 00 00 9C")
FATHER_BRIDGE_DIALOGUE_ID: Final = 57
OBSOLETE_FATHER_DIALOGUE_ID: Final = 128
RESIDENT_SCRIPT_GUEST_POINTER: Final = 0x8010ADC0
SCRIPT_DIALOGUE_GAP_SIZE: Final = 74
SCRIPT_DIALOGUE_GAP_SHA256: Final = (
    "cb98285922eb7787dd16492152a83067ba80c92456be560eaa25c3d7d0936c1e"
)

RESIDENT_DIALOGUE_PAYLOAD_OFFSET: Final = 0x10DD9E
RESIDENT_DIALOGUE_SIZE: Final = 11_794
SOURCE_RESIDENT_DIALOGUE_SHA256: Final = (
    "059db2e7b0eac4474ce8af3f72afc97adcb4edf6a1f0906f3c1feed90142ec25"
)
EXPECTED_RESIDENT_DIALOGUE_SHA256: Final = (
    "d0f0326d0ae060d5685bfa0419307c76649c2690a3d2a372fb53f39b2b0bbcbb"
)
RESIDENT_DIALOGUE_BLOCK_COUNT: Final = 129

RESIDENT_QUESTION_DIALOGUE_ID: Final = 51
RESIDENT_QUESTION_OFFSET: Final = 0x0F3A
RESIDENT_QUESTION_CAPACITY: Final = 184
RESIDENT_QUESTION_SOURCE_DIMENSIONS: Final = (54, 6)
RESIDENT_LESSON_DIALOGUE_ID: Final = 69
RESIDENT_LESSON_OFFSET: Final = 0x18C0
RESIDENT_LESSON_CAPACITY: Final = 430
RESIDENT_LESSON_SOURCE_DIMENSIONS: Final = (58, 4)

RESIDENT_DIALOGUE_ALLOCATED_SIZE: Final = 11_803
SOURCE_DIALOGUE_ALLOCATION_SHA256: Final = (
    "bace55cea96e6ea226b3547c342269a4566df6d29ff97687f49e063d1a343d6b"
)
EXPECTED_DIALOGUE_ALLOCATION_SHA256: Final = (
    "31fb3d367cb90a926b3a93afc9943794410e8b773facf83e7980eeff069c7439"
)
RESIDENT_DIALOGUE_UNUSED_TAIL: Final = bytes(9)
RESIDENT_DIALOGUE_ALIGNMENT: Final = bytes(7)
NEXT_ALLOCATOR_HEADER: Final = bytes.fromhex(
    "60 1D 00 02 2D E4 4B 12 6B 51 90 FC 10 80 5E C4 01 81"
)

ARCHIVE_TABLE_SIZE: Final = 0x8000
ARCHIVE_TABLE_PAYLOAD_OFFSET: Final = 0x11A66
SOURCE_ARCHIVE_TABLE_SHA256: Final = (
    "4d63340269893ccd8ab4ffcc789faffb85f859346043855a6881b3630cc9d7bd"
)
SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "cc9d1f6e832e74c6c1efe4998b18fe17f98884fb945edeaa9505bfa1964d080c"
)
SOURCE_VOLATILE_ARCHIVE_BYTE: Final = 0xC4
TARGET_ARCHIVE_TABLE_SHA256: Final = (
    "cd04c8934901721ff1e7c9352b678dfd4b311a528e449d262126e1710f5d41db"
)
TARGET_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "1636b11610b1ab28b4edd50558da135250c1d130bc8d261d9c6ce1018a3b43db"
)
ARCHIVE_TABLE_DIFFS: Final = (
    (0x3803, 0xF4, 0x04),
    (0x3804, 0x92, 0x93),
)

GAME_SCENE_MAP: Final = 0x04F34C
GAMESTATE_SIZE: Final = 0x2358
FIELD_VARIABLE_BANK_SIZE: Final = 0x800

EXPECTED_SCRIPT_CHANGED_BYTE_COUNT: Final = 1
EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT: Final = 524
EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT: Final = 527
EXPECTED_OUTPUT_PAYLOAD_SHA256: Final = (
    "5efe6b1cc63038b6baa2f1c5037ff1781d491511d74d20b75beb66fdff2afa64"
)
EXPECTED_OUTPUT_SIZE: Final = 1_365_946
EXPECTED_OUTPUT_SHA256: Final = (
    "4e8c3b35f30dc65be3cc53d6a214d083901360bde666b9d4124a16e7204dbff8"
)


class RicoFlowerDialogueMigrationError(RuntimeError):
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
        raise RicoFlowerDialogueMigrationError(
            "Final staged Rico Disc 1 identity changed"
        )
    image = Mode2Image(new_disc)
    entries = image.read_index()
    if HOUSE_FIELD_CANONICAL_ID >= len(entries):
        raise RicoFlowerDialogueMigrationError(
            "Final staged Disc 1 is missing canonical 2048"
        )
    entry = entries[HOUSE_FIELD_CANONICAL_ID]
    if (
        entry.kind != "file"
        or entry.sector != HOUSE_FIELD_SECTOR
        or entry.size != TARGET_HOUSE_FIELD_SIZE
    ):
        raise RicoFlowerDialogueMigrationError(
            "Final staged Chapter 1 house allocation changed"
        )
    raw = image.extract_entry(entry)
    if len(raw) != TARGET_HOUSE_FIELD_SIZE or _sha256(raw) != TARGET_HOUSE_FIELD_SHA256:
        raise RicoFlowerDialogueMigrationError(
            "Final staged Chapter 1 house identity changed"
        )
    parsed = parse_field(raw)
    if len(parsed.parts) != 9:
        raise RicoFlowerDialogueMigrationError(
            "Final staged Chapter 1 component count changed"
        )
    script = parsed.parts[SCRIPT_COMPONENT_INDEX].data
    dialogue = parsed.parts[DIALOGUE_COMPONENT_INDEX].data
    if (
        (len(script), _sha256(script)) != (TARGET_SCRIPT_SIZE, TARGET_SCRIPT_SHA256)
        or (len(dialogue), _sha256(dialogue))
        != (TARGET_DIALOGUE_SIZE, TARGET_DIALOGUE_SHA256)
    ):
        raise RicoFlowerDialogueMigrationError(
            "Final staged Chapter 1 component identity changed"
        )
    blocks = _raw_dialogue_blocks(dialogue)
    question = blocks[TARGET_QUESTION_DIALOGUE_ID]
    lesson = blocks[TARGET_LESSON_DIALOGUE_ID]
    if (
        len(blocks) != TARGET_DIALOGUE_BLOCK_COUNT
        or (question.offset, len(question.payload), question.width, question.height)
        != (
            TARGET_QUESTION_OFFSET,
            TARGET_QUESTION_SIZE,
            *TARGET_QUESTION_DIMENSIONS,
        )
        or question.payload != encode_text(TARGET_QUESTION_TEXT)
        or decode_text(question.payload) != TARGET_QUESTION_TEXT
        or (lesson.offset, len(lesson.payload), lesson.width, lesson.height)
        != (
            TARGET_LESSON_OFFSET,
            TARGET_LESSON_SIZE,
            *TARGET_LESSON_DIMENSIONS,
        )
        or lesson.payload != encode_text(TARGET_LESSON_TEXT)
        or decode_text(lesson.payload) != TARGET_LESSON_TEXT
        or script.count(_dialogue_command(TARGET_QUESTION_DIALOGUE_ID)) != 1
        or script.count(_dialogue_command(TARGET_LESSON_DIALOGUE_ID)) != 1
    ):
        raise RicoFlowerDialogueMigrationError(
            "Final staged stonebell dialogue text/topology changed"
        )
    table = _archive_table(new_disc)
    if len(table) != ARCHIVE_TABLE_SIZE or _sha256(table) != TARGET_ARCHIVE_TABLE_SHA256:
        raise RicoFlowerDialogueMigrationError(
            "Final staged Disc-1 archive table identity changed"
        )
    return script, dialogue, table


def _build_resident_script(source: bytes) -> bytes:
    if len(source) != RESIDENT_SCRIPT_SIZE or _sha256(source) != SOURCE_RESIDENT_SCRIPT_SHA256:
        raise RicoFlowerDialogueMigrationError("Resident script identity changed")
    start = FLOWER_LESSON_COMMAND_OFFSET
    end = start + len(SOURCE_FLOWER_LESSON_COMMAND)
    if (
        source[start:end] != SOURCE_FLOWER_LESSON_COMMAND
        or source.count(_dialogue_command(RESIDENT_QUESTION_DIALOGUE_ID)) != 1
        or source.count(_dialogue_command(TARGET_LESSON_DIALOGUE_ID)) != 1
        or source.count(_dialogue_command(RESIDENT_LESSON_DIALOGUE_ID)) != 0
        or source.count(_choice_command(RESIDENT_LESSON_DIALOGUE_ID)) != 0
        or source.count(_dialogue_command(FATHER_BRIDGE_DIALOGUE_ID)) != 1
        or source.count(_dialogue_command(OBSOLETE_FATHER_DIALOGUE_ID)) != 0
    ):
        raise RicoFlowerDialogueMigrationError("Resident script topology changed")
    result = bytearray(source)
    result[start:end] = TARGET_FLOWER_LESSON_COMMAND
    output = bytes(result)
    if (
        len(_differences(source, output)) != EXPECTED_SCRIPT_CHANGED_BYTE_COUNT
        or output[FLOWER_LESSON_OPERAND_OFFSET] != RESIDENT_LESSON_DIALOGUE_ID
        or output.count(_dialogue_command(TARGET_LESSON_DIALOGUE_ID)) != 0
        or output.count(_dialogue_command(RESIDENT_LESSON_DIALOGUE_ID)) != 1
        or _sha256(output) != EXPECTED_RESIDENT_SCRIPT_SHA256
    ):
        raise RicoFlowerDialogueMigrationError("Resident script bridge is not exact")
    return output


def _build_resident_dialogue(source: bytes, target: bytes) -> bytes:
    if len(source) != RESIDENT_DIALOGUE_SIZE or _sha256(source) != SOURCE_RESIDENT_DIALOGUE_SHA256:
        raise RicoFlowerDialogueMigrationError("Resident dialogue identity changed")
    source_blocks = _raw_dialogue_blocks(source)
    target_blocks = _raw_dialogue_blocks(target)
    specifications = (
        (
            TARGET_QUESTION_DIALOGUE_ID,
            RESIDENT_QUESTION_DIALOGUE_ID,
            RESIDENT_QUESTION_OFFSET,
            RESIDENT_QUESTION_CAPACITY,
            TARGET_QUESTION_DIMENSIONS,
            TARGET_QUESTION_TEXT,
        ),
        (
            TARGET_LESSON_DIALOGUE_ID,
            RESIDENT_LESSON_DIALOGUE_ID,
            RESIDENT_LESSON_OFFSET,
            RESIDENT_LESSON_CAPACITY,
            TARGET_LESSON_DIMENSIONS,
            TARGET_LESSON_TEXT,
        ),
    )
    if len(source_blocks) != RESIDENT_DIALOGUE_BLOCK_COUNT:
        raise RicoFlowerDialogueMigrationError("Resident dialogue block count changed")
    resident = bytearray(source)
    for target_id, resident_id, offset, capacity, dimensions, _text in specifications:
        source_block = source_blocks[resident_id]
        target_block = target_blocks[target_id]
        if source_block.offset != offset or len(source_block.payload) != capacity or len(target_block.payload) > capacity:
            raise RicoFlowerDialogueMigrationError(
                f"Dialogue {target_id} no longer fits resident span {resident_id}"
            )
        dimensions_offset = _dialogue_dimensions_offset(
            RESIDENT_DIALOGUE_BLOCK_COUNT,
            resident_id,
        )
        resident[dimensions_offset : dimensions_offset + 2] = bytes(dimensions)
        resident[offset : offset + capacity] = target_block.payload + bytes(
            capacity - len(target_block.payload)
        )
    output = bytes(resident)
    output_blocks = _raw_dialogue_blocks(output)
    if tuple(block.offset for block in output_blocks) != tuple(
        block.offset for block in source_blocks
    ):
        raise RicoFlowerDialogueMigrationError("Resident dialogue offsets moved")
    for target_id, resident_id, offset, capacity, dimensions, text in specifications:
        target_block = target_blocks[target_id]
        output_block = output_blocks[resident_id]
        if (
            (output_block.offset, len(output_block.payload), output_block.width, output_block.height)
            != (offset, capacity, *dimensions)
            or output_block.payload
            != target_block.payload + bytes(capacity - len(target_block.payload))
            or decode_text(output_block.payload)
            != text + "<Close>" * (capacity - len(target_block.payload))
        ):
            raise RicoFlowerDialogueMigrationError(
                f"Resident dialogue bridge {resident_id} is not exact"
            )
    for block_id in range(RESIDENT_DIALOGUE_BLOCK_COUNT):
        if block_id not in {RESIDENT_QUESTION_DIALOGUE_ID, RESIDENT_LESSON_DIALOGUE_ID}:
            if output_blocks[block_id] != source_blocks[block_id]:
                raise RicoFlowerDialogueMigrationError(
                    f"Unrelated resident dialogue {block_id} changed"
                )
    if (
        len(_differences(source, output)) != EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT
        or _sha256(output) != EXPECTED_RESIDENT_DIALOGUE_SHA256
    ):
        raise RicoFlowerDialogueMigrationError(
            "Resident dialogue changed-byte contract drifted"
        )
    return output


def migrate_state(
    state: bytes,
    *,
    zstd: _Zstd,
    new_disc: Path,
) -> tuple[bytes, dict[str, object]]:
    state_hash = _sha256(state)
    if (len(state), state_hash) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise RicoFlowerDialogueMigrationError(
            "Source Slot 1 identity changed: "
            f"{len(state)} bytes / {state_hash}; expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    if (
        len(state) < DUCKSTATION_STATE_HEADER_SIZE
        or state[:4] != DUCKSTATION_STATE_MAGIC
        or state.count(SOURCE_MEDIA_PATH) != 1
    ):
        raise RicoFlowerDialogueMigrationError(
            "Source is not the supported stable-path DuckStation state"
        )
    _target_script, target_dialogue, target_table = _validated_target_resources(
        new_disc.resolve()
    )
    compression_type, compressed_size, payload_size, frame_offset = struct.unpack_from(
        "<IIII", state, DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET
    )
    if compression_type != DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise RicoFlowerDialogueMigrationError("Source is not Zstandard-compressed")
    if (
        compressed_size != SOURCE_COMPRESSED_SIZE
        or payload_size != SOURCE_PAYLOAD_SIZE
        or frame_offset != SOURCE_FRAME_OFFSET
        or frame_offset + compressed_size != len(state)
    ):
        raise RicoFlowerDialogueMigrationError("Source frame layout changed")
    frame = state[frame_offset:]
    if not frame.startswith(ZSTD_MAGIC) or zstd.frame_size(frame) != compressed_size:
        raise RicoFlowerDialogueMigrationError("Source compressed frame is invalid")
    source_payload = zstd.decompress(frame)
    if len(source_payload) != SOURCE_PAYLOAD_SIZE or _sha256(source_payload) != SOURCE_PAYLOAD_SHA256:
        raise RicoFlowerDialogueMigrationError("Source payload identity changed")
    ram_offset = _psx_ram_offset(source_payload)
    if ram_offset != SOURCE_RAM_OFFSET or ram_offset + RAM_SIZE > len(source_payload):
        raise RicoFlowerDialogueMigrationError("Source PSX RAM layout changed")
    source_ram = source_payload[ram_offset : ram_offset + RAM_SIZE]
    if _sha256(source_ram) != SOURCE_RAM_SHA256:
        raise RicoFlowerDialogueMigrationError("Source PSX RAM identity changed")

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
        _sha256(source_payload[script_end:dialogue_start]) != SCRIPT_DIALOGUE_GAP_SHA256
        or _sha256(source_payload[dialogue_start:allocated_end])
        != SOURCE_DIALOGUE_ALLOCATION_SHA256
        or source_payload[dialogue_end:allocated_end] != RESIDENT_DIALOGUE_UNUSED_TAIL
        or source_payload[allocated_end:aligned_end] != RESIDENT_DIALOGUE_ALIGNMENT
        or source_payload[aligned_end:header_end] != NEXT_ALLOCATOR_HEADER
    ):
        raise RicoFlowerDialogueMigrationError("Resident allocator boundary changed")

    blocks = _raw_dialogue_blocks(source_dialogue)
    active = blocks[ACTIVE_DIALOGUE_ID]
    statuses = tuple(
        struct.unpack_from(
            "<h",
            source_ram,
            DIALOG_WINDOWS + i * DIALOG_WINDOW_STRIDE + DIALOG_WINDOW_STATUS_OFFSET,
        )[0]
        for i in range(DIALOG_WINDOW_COUNT)
    )
    if (
        struct.unpack_from("<I", source_ram, GAME_SCENE_MAP)[0] != EXPECTED_GAME_SCENE_MAP
        or struct.unpack_from("<I", source_ram, FIELD_NUM_ACTORS)[0] != EXPECTED_ACTOR_COUNT
        or struct.unpack_from("<I", source_ram, FIELD_ACTORS)[0] != EXPECTED_ACTOR_ARRAY_GUEST_POINTER
        or struct.unpack_from("<I", source_ram, FIELD_CUR_SCRIPT_FILE)[0] != RESIDENT_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", source_ram, FIELD_CUR_DIALOGUE_FILE)[0] != RESIDENT_DIALOGUE_GUEST_POINTER
        or statuses != EXPECTED_WINDOW_STATUSES
        or struct.unpack_from("<I", source_ram, WINDOW0_START_POINTER_OFFSET)[0] != EXPECTED_WINDOW0_START_POINTER
        or struct.unpack_from("<I", source_ram, WINDOW0_CURRENT_POINTER_OFFSET)[0] != EXPECTED_WINDOW0_CURRENT_POINTER
        or active.offset != ACTIVE_DIALOGUE_OFFSET
    ):
        raise RicoFlowerDialogueMigrationError("Live field/window topology changed")

    table_start = ARCHIVE_TABLE_PAYLOAD_OFFSET
    table_end = table_start + ARCHIVE_TABLE_SIZE
    source_table = source_payload[table_start:table_end]
    normalized_source_table = source_table[:-1] + target_table[-1:]
    if (
        _sha256(source_table) != SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256
        or source_table[-1] != SOURCE_VOLATILE_ARCHIVE_BYTE
        or _sha256(normalized_source_table) != SOURCE_ARCHIVE_TABLE_SHA256
        or _differences(normalized_source_table, target_table) != ARCHIVE_TABLE_DIFFS
    ):
        raise RicoFlowerDialogueMigrationError("Resident Disc-1 FAT contract changed")

    resident_script = _build_resident_script(source_script)
    resident_dialogue = _build_resident_dialogue(source_dialogue, target_dialogue)
    payload = bytearray(source_payload)
    payload[script_start:script_end] = resident_script
    payload[dialogue_start:dialogue_end] = resident_dialogue
    for relative, old, new in ARCHIVE_TABLE_DIFFS:
        absolute = table_start + relative
        if payload[absolute] != old:
            raise RicoFlowerDialogueMigrationError("Resident FAT byte changed")
        payload[absolute] = new
    final_payload = bytes(payload)
    script_diffs = _differences(source_script, resident_script)
    dialogue_diffs = _differences(source_dialogue, resident_dialogue)
    expected_changes = tuple(
        sorted(
            (
                *((script_start + o, a, b) for o, a, b in script_diffs),
                *((dialogue_start + o, a, b) for o, a, b in dialogue_diffs),
                *((table_start + o, a, b) for o, a, b in ARCHIVE_TABLE_DIFFS),
            )
        )
    )
    if (
        _differences(source_payload, final_payload) != expected_changes
        or len(expected_changes) != EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT
        or _sha256(final_payload[dialogue_start:allocated_end])
        != EXPECTED_DIALOGUE_ALLOCATION_SHA256
        or final_payload[dialogue_end:header_end]
        != source_payload[dialogue_end:header_end]
        or final_payload[script_end:dialogue_start]
        != source_payload[script_end:dialogue_start]
    ):
        raise RicoFlowerDialogueMigrationError("Migration whitelist/allocator check failed")
    final_table = final_payload[table_start:table_end]
    if (
        _sha256(final_table) != TARGET_RESIDENT_ARCHIVE_TABLE_SHA256
        or final_table[:-1] != target_table[:-1]
        or final_table[-1] != SOURCE_VOLATILE_ARCHIVE_BYTE
    ):
        raise RicoFlowerDialogueMigrationError("Final resident FAT is not exact")
    for start, size in (
        (GAME_STATE, GAMESTATE_SIZE),
        (FIELD_SCRIPT_MEMORY, FIELD_VARIABLE_BANK_SIZE),
        (DIALOG_WINDOWS, DIALOG_WINDOW_STRIDE * DIALOG_WINDOW_COUNT),
    ):
        final_ram = final_payload[ram_offset : ram_offset + RAM_SIZE]
        if final_ram[start : start + size] != source_ram[start : start + size]:
            raise RicoFlowerDialogueMigrationError("Progress/window span changed")

    final_payload_hash = _sha256(final_payload)
    if final_payload_hash != EXPECTED_OUTPUT_PAYLOAD_SHA256:
        raise RicoFlowerDialogueMigrationError(
            "Output payload identity changed: " + final_payload_hash
        )
    compressed = zstd.compress(final_payload)
    prefix = bytearray(state[:frame_offset])
    struct.pack_into("<I", prefix, DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET, len(compressed))
    result = bytes(prefix) + compressed
    result_hash = _sha256(result)
    if (
        zstd.decompress(result[frame_offset:]) != final_payload
        or len(result) != EXPECTED_OUTPUT_SIZE
        or result_hash != EXPECTED_OUTPUT_SHA256
    ):
        raise RicoFlowerDialogueMigrationError(
            f"Candidate identity changed: {len(result)} / {result_hash}"
        )
    return result, {
        "source_state_sha256": state_hash,
        "output_state_sha256": result_hash,
        "payload_changed_byte_count": len(expected_changes),
        "resident_script_changed_byte_count": len(script_diffs),
        "resident_dialogue_changed_byte_count": len(dialogue_diffs),
        "resident_fat_changed_byte_count": len(ARCHIVE_TABLE_DIFFS),
        "dialogue_offsets_preserved": True,
        "active_dialogue_window_preserved": True,
        "father_dialogue_bridge_preserved": True,
        "allocator_header_preserved": True,
        "dialogue_51_capacity": RESIDENT_QUESTION_CAPACITY,
        "dialogue_69_capacity": RESIDENT_LESSON_CAPACITY,
        "lesson_call_redirect": "52->69",
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
    except RicoFlowerDialogueMigrationError as exc:
        raise SystemExit(str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)
    if output.read_bytes() != result:
        raise SystemExit("Written candidate changed on disk")
    print(f"Wrote allocator-safe flower-dialogue candidate: {output}")
    for key, value in report.items():
        print(f"{key}: {value}")
    print("The source and DuckStation's live Slot 1 were not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
