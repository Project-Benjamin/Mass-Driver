#!/usr/bin/env python3
"""Migrate the audited Rico Slot 1 to Anne's concise firewood reply.

The captured state has Chapter 1's house field resident in its allocator-safe
father-dialogue bridge form.  The rebuilt field packs its dialogue blocks at
new offsets, so replacing the complete resident dialogue would invalidate the
live pointers and overwrite heap ownership.  This successor migration changes
only authored block 28's resident counterpart (dialogue ID 55), padding the
shorter text inside its existing 98-byte span and adopting its rebuilt window
dimensions.  It also applies the single exact Disc-1 FAT size byte required by
the rebuilt house resource.

The father-dialogue bridge, every dialogue offset, the active window, field
progress, and all allocator bytes remain untouched.  Only the exact audited
state and exact staged Disc 1 are accepted.  The tool always writes a separate
candidate and refuses DuckStation's live Slot 1.
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
    EXPECTED_CONTINUATION_DIALOGUE as FATHER_CONTINUATION_DIALOGUE,
    EXPECTED_FIRST_DIALOGUE as FATHER_FIRST_DIALOGUE,
    _choice_command,
    _dialogue_command,
    _dialogue_dimensions_offset,
    _differences,
    _raw_dialogue_blocks,
)
from tools.xgdialog import decode_text, encode_text  # noqa: E402
from tools.xgdisc import Mode2Image  # noqa: E402
from tools.xgfield import parse_field  # noqa: E402
from tools.xgscript import AtelScript  # noqa: E402
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
    ROOT
    / "work"
    / "rico_firewood_reply_stage"
    / "Xenogears_Rico_Arc_Disc_1.bin"
)

SOURCE_STATE_SIZE: Final = 1_366_030
SOURCE_STATE_SHA256: Final = (
    "a8987ae352c2a0971d7d5dcbaaac4ac1c8d80f5a6858fb700e027b4435846cc4"
)
SOURCE_FRAME_OFFSET: Final = 0x6DD0
SOURCE_COMPRESSED_SIZE: Final = 1_337_918
SOURCE_PAYLOAD_SIZE: Final = 3_817_429
SOURCE_PAYLOAD_SHA256: Final = (
    "a83141d45e96e578daa982df953ae9445d0f8157dbfc726194262bc763d5caa5"
)
SOURCE_RAM_OFFSET: Final = 0x1A62
SOURCE_RAM_SHA256: Final = (
    "8ba1a88e965f9c303d54c0a6b005b7b791e9929884c0471062726635d52d6589"
)
SOURCE_MEDIA_PATH: Final = (
    rb"C:\Users\Chad\Xenogears_Reimagined\output\rico_arc\Xenogears_Rico_Arc.m3u"
)

HOUSE_FIELD_CANONICAL_ID: Final = 2048
HOUSE_FIELD_SECTOR: Final = 230_237
TARGET_HOUSE_FIELD_SIZE: Final = 37_788
TARGET_HOUSE_FIELD_SHA256: Final = (
    "f7e9926a02d325ae0f8e59e98eecc72885a44b60917d6a76a01d3d1654f20aae"
)

SCRIPT_COMPONENT_INDEX: Final = 5
DIALOGUE_COMPONENT_INDEX: Final = 7
RESIDENT_SCRIPT_PAYLOAD_OFFSET: Final = 0x10C822
RESIDENT_SCRIPT_SIZE: Final = 5_426
TARGET_SCRIPT_SHA256: Final = (
    "85e334efff6a70674d84615fde31be4fd5be8f60bd1eebdb46e7ebc2b9d20386"
)
RESIDENT_SCRIPT_SHA256: Final = (
    "c61094be0baf53aa838f7c29871d963d0a1bc40c08888de099b12f81913dcc29"
)
SCRIPT_BYTECODE_OFFSET: Final = 0x0704
DOORWAY_SECOND_DIALOGUE_PC: Final = 0x0D44
TARGET_DOORWAY_SECOND_DIALOGUE: Final = bytes.fromhex("F5 80 00 00 9C")
RESIDENT_DOORWAY_SECOND_DIALOGUE: Final = bytes.fromhex("F5 39 00 00 9C")
RESIDENT_SCRIPT_GUEST_POINTER: Final = 0x8010ADC0
SCRIPT_DIALOGUE_GAP_SIZE: Final = 74
SCRIPT_DIALOGUE_GAP_SHA256: Final = (
    "cb98285922eb7787dd16492152a83067ba80c92456be560eaa25c3d7d0936c1e"
)

RESIDENT_DIALOGUE_PAYLOAD_OFFSET: Final = 0x10DD9E
RESIDENT_DIALOGUE_SIZE: Final = 11_794
RESIDENT_DIALOGUE_SHA256: Final = (
    "f37d7b21f0e82c99fbcfee57782751af79a73f30cdc29ed5d1aa9a9c696f28e6"
)
EXPECTED_RESIDENT_DIALOGUE_SHA256: Final = (
    "059db2e7b0eac4474ce8af3f72afc97adcb4edf6a1f0906f3c1feed90142ec25"
)
TARGET_DIALOGUE_SIZE: Final = 11_887
TARGET_DIALOGUE_SHA256: Final = (
    "cb6e914a0cb2e26e8c1355a19ad9e12001d6339b3bc7a44a03d8e836b4e9a2ac"
)
DIALOGUE_BLOCK_COUNT: Final = 129
RESIDENT_DIALOGUE_GUEST_POINTER: Final = 0x8010C33C
FIELD_CUR_DIALOGUE_FILE: Final = 0x0ADBF0

FIREWOOD_REPLY_DIALOGUE_ID: Final = 55
FIREWOOD_REPLY_OFFSET: Final = 0x120A
FIREWOOD_REPLY_CAPACITY: Final = 98
SOURCE_FIREWOOD_REPLY_DIMENSIONS: Final = (58, 3)
TARGET_FIREWOOD_REPLY_SIZE: Final = 62
TARGET_FIREWOOD_REPLY_DIMENSIONS: Final = (58, 2)
SOURCE_FIREWOOD_REPLY: Final = (
    "Anne\nThe pile is just outside,\nbeside the house.<New>"
    "Take only what you can carry.\nThe rest can wait.<Close>"
)
TARGET_FIREWOOD_REPLY: Final = (
    "Anne\nI will.<New>Take only what you can carry.\n"
    "The rest can wait.<Close>"
)

# These spans are the previously installed father-dialogue bridge.  They must
# remain byte-exact while the unrelated firewood reply changes.
BRIDGE_DIALOGUE_ID: Final = 57
BRIDGE_DIALOGUE_OFFSET: Final = 0x12CF
BRIDGE_DIALOGUE_CAPACITY: Final = 263
BRIDGE_DIALOGUE_DIMENSIONS: Final = (54, 3)
FIRST_FATHER_DIALOGUE_ID: Final = 127
FIRST_FATHER_DIALOGUE_OFFSET: Final = 0x2D67
FIRST_FATHER_DIALOGUE_CAPACITY: Final = 47
FIRST_FATHER_DIALOGUE_DIMENSIONS: Final = (56, 3)
OBSOLETE_FATHER_DIALOGUE_ID: Final = 128

# The rebuilt media packs the normal father exchange after the shorter block
# 55.  Its offsets intentionally differ from the fixed resident bridge.
TARGET_FIRST_FATHER_OFFSET: Final = 0x2D43
TARGET_FIRST_FATHER_SIZE: Final = 40
TARGET_FATHER_CONTINUATION_OFFSET: Final = 0x2D6B
TARGET_FATHER_CONTINUATION_SIZE: Final = 260
TARGET_FATHER_CONTINUATION_DIMENSIONS: Final = (54, 3)

RESIDENT_DIALOGUE_ALLOCATED_SIZE: Final = 11_803
RESIDENT_DIALOGUE_ALLOCATION_SHA256: Final = (
    "4c893d8440d3ea6bec332e483424505d44e865d9765e9c5f69f155832a12dc8f"
)
RESIDENT_DIALOGUE_UNUSED_TAIL: Final = bytes(9)
RESIDENT_DIALOGUE_ALIGNMENT: Final = bytes(7)
NEXT_ALLOCATOR_HEADER: Final = bytes.fromhex(
    "60 1D 00 02 2D E4 4B 12 6B 51 90 FC 10 80 5E C4 01 81"
)

TARGET_DISC_SIZE: Final = 719_175_744
TARGET_DISC_SHA256: Final = (
    "6737d501262b2d056f362281973506c2262236824c488f9bbd8f1ca9f0b634a0"
)
ARCHIVE_TABLE_SIZE: Final = 0x8000
ARCHIVE_TABLE_PAYLOAD_OFFSET: Final = 0x11A66
SOURCE_ARCHIVE_TABLE_SHA256: Final = (
    "6a41348947362660556b561c0f8792cdbcb38639840f7711e7d30eabad29666c"
)
SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "96d391672da4e9bc97323c67a2261c9b75f227ea459b90a467163992ba87cf5c"
)
SOURCE_VOLATILE_ARCHIVE_BYTE: Final = 0xC4
TARGET_ARCHIVE_TABLE_SHA256: Final = (
    "c6ef521cf9a471e45e725e9070537cb25102342662d25c1727df6a863bf908ea"
)
TARGET_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "28723dfa0f6422cf0308af5b919513609a9796d95a568f5c9690d7339621dd72"
)
ARCHIVE_TABLE_DIFFS: Final = (
    (0x3803, 0xA4, 0x9C),  # FAT 2048 size: 37,796 -> 37,788
)

GAME_SCENE_MAP: Final = 0x04F34C
EXPECTED_GAME_SCENE_MAP: Final = 0x02D1
EXPECTED_ACTOR_COUNT: Final = 47
EXPECTED_ACTOR_ARRAY_GUEST_POINTER: Final = 0x80110D00
DIALOG_WINDOWS: Final = 0x0C2698
DIALOG_WINDOW_STRIDE: Final = 0x498
DIALOG_WINDOW_COUNT: Final = 4
DIALOG_WINDOW_STATUS_OFFSET: Final = 0x40E
WINDOW0_START_POINTER_OFFSET: Final = DIALOG_WINDOWS + 0xA8
WINDOW0_CURRENT_POINTER_OFFSET: Final = DIALOG_WINDOWS + 0x34
EXPECTED_WINDOW_STATUSES: Final = (0, -1, -1, -1)
EXPECTED_WINDOW0_START_POINTER: Final = 0x8010CE05
EXPECTED_WINDOW0_CURRENT_POINTER: Final = 0x8010CE49
ACTIVE_DIALOGUE_ID: Final = 39
ACTIVE_DIALOGUE_OFFSET: Final = 0x0AC9
EXPECTED_DIALOG_WINDOWS_SHA256: Final = (
    "141c0c5c78469c7246a4c4c4a10ea58b554e185d2f92a9abf7cba6b7dbc3830a"
)
EXPECTED_GAMESTATE_SHA256: Final = (
    "cd1ea76ddb1a3f6f4915ea616f10e84a43525a1f72fc4f4915f2275650a917ca"
)
EXPECTED_FIELD_VARIABLE_BANK_SHA256: Final = (
    "3c8dc09f17d846b30e5876a0475e422ce10ec7722d746f16a2a95a8d26c53125"
)
GAMESTATE_SIZE: Final = 0x2358
FIELD_VARIABLE_BANK_SIZE: Final = 0x800

EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT: Final = 93
EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT: Final = 94
EXPECTED_OUTPUT_PAYLOAD_SHA256: Final = (
    "4e7bf019585d78adc8e40b4e5dba5f4bbc53fb719faffc1b4c36e5a9b7cb1721"
)
EXPECTED_OUTPUT_SIZE: Final = 1_366_027
EXPECTED_OUTPUT_SHA256: Final = (
    "6493b88c6d69b060e624eea9847c1f567d3c530244605572a61c9d6b4267c117"
)


class RicoFirewoodReplyMigrationError(RuntimeError):
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
        raise RicoFirewoodReplyMigrationError(
            "Final staged Rico Disc 1 identity changed"
        )

    image = Mode2Image(new_disc)
    entries = image.read_index()
    if HOUSE_FIELD_CANONICAL_ID >= len(entries):
        raise RicoFirewoodReplyMigrationError(
            "Final staged Disc 1 is missing canonical 2048"
        )
    entry = entries[HOUSE_FIELD_CANONICAL_ID]
    if (
        entry.kind != "file"
        or entry.sector != HOUSE_FIELD_SECTOR
        or entry.size != TARGET_HOUSE_FIELD_SIZE
    ):
        raise RicoFirewoodReplyMigrationError(
            "Final staged Chapter 1 house allocation changed"
        )
    field = image.extract_entry(entry)
    if (
        len(field) != TARGET_HOUSE_FIELD_SIZE
        or _sha256(field) != TARGET_HOUSE_FIELD_SHA256
    ):
        raise RicoFirewoodReplyMigrationError(
            "Final staged Chapter 1 house identity changed"
        )
    parsed = parse_field(field)
    if len(parsed.parts) != 9:
        raise RicoFirewoodReplyMigrationError(
            "Final staged Chapter 1 component count changed"
        )
    script = parsed.parts[SCRIPT_COMPONENT_INDEX].data
    dialogue = parsed.parts[DIALOGUE_COMPONENT_INDEX].data
    if (
        len(script) != RESIDENT_SCRIPT_SIZE
        or _sha256(script) != TARGET_SCRIPT_SHA256
    ):
        raise RicoFirewoodReplyMigrationError(
            "Final staged Chapter 1 script identity changed"
        )
    if (
        len(dialogue) != TARGET_DIALOGUE_SIZE
        or _sha256(dialogue) != TARGET_DIALOGUE_SHA256
    ):
        raise RicoFirewoodReplyMigrationError(
            "Final staged Chapter 1 dialogue identity changed"
        )

    editor = AtelScript(script)
    command_start = SCRIPT_BYTECODE_OFFSET + DOORWAY_SECOND_DIALOGUE_PC
    if (
        editor.entity_count != 26
        or editor.bytecode_offset != SCRIPT_BYTECODE_OFFSET
        or editor.get_script_pointer(25, 2) != 0x0CDE
        or script[
            command_start : command_start + len(TARGET_DOORWAY_SECOND_DIALOGUE)
        ]
        != TARGET_DOORWAY_SECOND_DIALOGUE
        or script.count(_dialogue_command(BRIDGE_DIALOGUE_ID)) != 0
        or script.count(_choice_command(BRIDGE_DIALOGUE_ID)) != 0
        or script.count(_dialogue_command(OBSOLETE_FATHER_DIALOGUE_ID)) != 1
    ):
        raise RicoFirewoodReplyMigrationError(
            "Final staged father-dialogue topology changed"
        )

    blocks = _raw_dialogue_blocks(dialogue)
    if len(blocks) != DIALOGUE_BLOCK_COUNT:
        raise RicoFirewoodReplyMigrationError(
            "Final staged dialogue block count changed"
        )
    reply = blocks[FIREWOOD_REPLY_DIALOGUE_ID]
    first = blocks[FIRST_FATHER_DIALOGUE_ID]
    continuation = blocks[OBSOLETE_FATHER_DIALOGUE_ID]
    if (
        (
            reply.offset,
            len(reply.payload),
            reply.width,
            reply.height,
        )
        != (
            FIREWOOD_REPLY_OFFSET,
            TARGET_FIREWOOD_REPLY_SIZE,
            *TARGET_FIREWOOD_REPLY_DIMENSIONS,
        )
        or reply.payload != encode_text(TARGET_FIREWOOD_REPLY)
        or decode_text(reply.payload) != TARGET_FIREWOOD_REPLY
        or (
            first.offset,
            len(first.payload),
            first.width,
            first.height,
        )
        != (
            TARGET_FIRST_FATHER_OFFSET,
            TARGET_FIRST_FATHER_SIZE,
            *FIRST_FATHER_DIALOGUE_DIMENSIONS,
        )
        or decode_text(first.payload) != FATHER_FIRST_DIALOGUE
        or (
            continuation.offset,
            len(continuation.payload),
            continuation.width,
            continuation.height,
        )
        != (
            TARGET_FATHER_CONTINUATION_OFFSET,
            TARGET_FATHER_CONTINUATION_SIZE,
            *TARGET_FATHER_CONTINUATION_DIMENSIONS,
        )
        or decode_text(continuation.payload) != FATHER_CONTINUATION_DIALOGUE
    ):
        raise RicoFirewoodReplyMigrationError(
            "Final staged firewood/father dialogue contract changed"
        )

    table = _archive_table(new_disc)
    if (
        len(table) != ARCHIVE_TABLE_SIZE
        or _sha256(table) != TARGET_ARCHIVE_TABLE_SHA256
    ):
        raise RicoFirewoodReplyMigrationError(
            "Final staged Disc-1 archive table identity changed"
        )
    return script, dialogue, table


def _validate_resident_father_bridge(script: bytes, dialogue: bytes) -> None:
    if (
        len(script) != RESIDENT_SCRIPT_SIZE
        or _sha256(script) != RESIDENT_SCRIPT_SHA256
    ):
        raise RicoFirewoodReplyMigrationError(
            "Resident Chapter 1 script identity changed"
        )
    command_start = SCRIPT_BYTECODE_OFFSET + DOORWAY_SECOND_DIALOGUE_PC
    if (
        script[
            command_start : command_start + len(RESIDENT_DOORWAY_SECOND_DIALOGUE)
        ]
        != RESIDENT_DOORWAY_SECOND_DIALOGUE
        or script.count(_dialogue_command(BRIDGE_DIALOGUE_ID)) != 1
        or script.count(_choice_command(BRIDGE_DIALOGUE_ID)) != 0
        or script.count(_dialogue_command(OBSOLETE_FATHER_DIALOGUE_ID)) != 0
    ):
        raise RicoFirewoodReplyMigrationError(
            "Resident father-dialogue bridge script changed"
        )
    if (
        len(dialogue) != RESIDENT_DIALOGUE_SIZE
        or _sha256(dialogue) != RESIDENT_DIALOGUE_SHA256
    ):
        raise RicoFirewoodReplyMigrationError(
            "Resident Chapter 1 dialogue identity changed"
        )
    blocks = _raw_dialogue_blocks(dialogue)
    if len(blocks) != DIALOGUE_BLOCK_COUNT:
        raise RicoFirewoodReplyMigrationError(
            "Resident dialogue block count changed"
        )
    reply = blocks[FIREWOOD_REPLY_DIALOGUE_ID]
    bridge = blocks[BRIDGE_DIALOGUE_ID]
    first = blocks[FIRST_FATHER_DIALOGUE_ID]
    if (
        (
            reply.offset,
            len(reply.payload),
            reply.width,
            reply.height,
        )
        != (
            FIREWOOD_REPLY_OFFSET,
            FIREWOOD_REPLY_CAPACITY,
            *SOURCE_FIREWOOD_REPLY_DIMENSIONS,
        )
        or reply.payload != encode_text(SOURCE_FIREWOOD_REPLY)
        or (
            bridge.offset,
            len(bridge.payload),
            bridge.width,
            bridge.height,
        )
        != (
            BRIDGE_DIALOGUE_OFFSET,
            BRIDGE_DIALOGUE_CAPACITY,
            *BRIDGE_DIALOGUE_DIMENSIONS,
        )
        or bridge.payload
        != encode_text(FATHER_CONTINUATION_DIALOGUE)
        + bytes(BRIDGE_DIALOGUE_CAPACITY - len(encode_text(FATHER_CONTINUATION_DIALOGUE)))
        or (
            first.offset,
            len(first.payload),
            first.width,
            first.height,
        )
        != (
            FIRST_FATHER_DIALOGUE_OFFSET,
            FIRST_FATHER_DIALOGUE_CAPACITY,
            *FIRST_FATHER_DIALOGUE_DIMENSIONS,
        )
        or first.payload
        != encode_text(FATHER_FIRST_DIALOGUE)
        + bytes(FIRST_FATHER_DIALOGUE_CAPACITY - len(encode_text(FATHER_FIRST_DIALOGUE)))
    ):
        raise RicoFirewoodReplyMigrationError(
            "Resident firewood reply or father bridge spans changed"
        )


def _build_resident_dialogue(source: bytes, target: bytes) -> bytes:
    source_blocks = _raw_dialogue_blocks(source)
    target_blocks = _raw_dialogue_blocks(target)
    source_reply = source_blocks[FIREWOOD_REPLY_DIALOGUE_ID]
    target_reply = target_blocks[FIREWOOD_REPLY_DIALOGUE_ID]
    if (
        source_reply.offset != FIREWOOD_REPLY_OFFSET
        or len(source_reply.payload) != FIREWOOD_REPLY_CAPACITY
        or len(target_reply.payload) > FIREWOOD_REPLY_CAPACITY
    ):
        raise RicoFirewoodReplyMigrationError(
            "Firewood reply no longer fits its fixed resident span"
        )

    resident = bytearray(source)
    dimensions = _dialogue_dimensions_offset(
        DIALOGUE_BLOCK_COUNT,
        FIREWOOD_REPLY_DIALOGUE_ID,
    )
    resident[dimensions : dimensions + 2] = bytes(
        TARGET_FIREWOOD_REPLY_DIMENSIONS
    )
    resident[
        FIREWOOD_REPLY_OFFSET : FIREWOOD_REPLY_OFFSET + FIREWOOD_REPLY_CAPACITY
    ] = target_reply.payload + bytes(
        FIREWOOD_REPLY_CAPACITY - len(target_reply.payload)
    )
    result = bytes(resident)
    result_blocks = _raw_dialogue_blocks(result)
    result_reply = result_blocks[FIREWOOD_REPLY_DIALOGUE_ID]
    if (
        len(result) != RESIDENT_DIALOGUE_SIZE
        or tuple(block.offset for block in result_blocks)
        != tuple(block.offset for block in source_blocks)
        or (
            result_reply.offset,
            len(result_reply.payload),
            result_reply.width,
            result_reply.height,
        )
        != (
            FIREWOOD_REPLY_OFFSET,
            FIREWOOD_REPLY_CAPACITY,
            *TARGET_FIREWOOD_REPLY_DIMENSIONS,
        )
        or result_reply.payload
        != target_reply.payload
        + bytes(FIREWOOD_REPLY_CAPACITY - len(target_reply.payload))
        or decode_text(result_reply.payload)
        != TARGET_FIREWOOD_REPLY
        + "<Close>" * (FIREWOOD_REPLY_CAPACITY - len(target_reply.payload))
        or result_blocks[BRIDGE_DIALOGUE_ID]
        != source_blocks[BRIDGE_DIALOGUE_ID]
        or result_blocks[FIRST_FATHER_DIALOGUE_ID]
        != source_blocks[FIRST_FATHER_DIALOGUE_ID]
        or result_blocks[OBSOLETE_FATHER_DIALOGUE_ID]
        != source_blocks[OBSOLETE_FATHER_DIALOGUE_ID]
    ):
        raise RicoFirewoodReplyMigrationError(
            "Fixed-span firewood reply rewrite is not exact"
        )
    differences = _differences(source, result)
    allowed_offsets = {
        dimensions,
        dimensions + 1,
        *range(
            FIREWOOD_REPLY_OFFSET,
            FIREWOOD_REPLY_OFFSET + FIREWOOD_REPLY_CAPACITY,
        ),
    }
    if (
        len(differences) != EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT
        or {offset for offset, _old, _new in differences} - allowed_offsets
        or _sha256(result) != EXPECTED_RESIDENT_DIALOGUE_SHA256
    ):
        raise RicoFirewoodReplyMigrationError(
            "Resident firewood reply changed-byte contract drifted"
        )
    return result


def migrate_state(
    state: bytes,
    *,
    zstd: _Zstd,
    new_disc: Path,
) -> tuple[bytes, dict[str, object]]:
    """Return the fixed-span firewood-reply candidate and audit report."""

    state_hash = _sha256(state)
    if (len(state), state_hash) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise RicoFirewoodReplyMigrationError(
            "Source Slot 1 identity changed: "
            f"{len(state)} bytes / {state_hash}; expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    if (
        len(state) < DUCKSTATION_STATE_HEADER_SIZE
        or state[:4] != DUCKSTATION_STATE_MAGIC
        or state.count(SOURCE_MEDIA_PATH) != 1
    ):
        raise RicoFirewoodReplyMigrationError(
            "Source is not the supported stable-path DuckStation state"
        )
    target_script, target_dialogue, target_table = _validated_target_resources(
        new_disc.resolve()
    )

    compression_type, compressed_size, payload_size, frame_offset = (
        struct.unpack_from(
            "<IIII",
            state,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
        )
    )
    if compression_type != DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise RicoFirewoodReplyMigrationError(
            "Source payload is not Zstandard-compressed"
        )
    if (
        compressed_size != SOURCE_COMPRESSED_SIZE
        or payload_size != SOURCE_PAYLOAD_SIZE
        or frame_offset != SOURCE_FRAME_OFFSET
        or frame_offset + compressed_size != len(state)
    ):
        raise RicoFirewoodReplyMigrationError(
            "Source DuckStation frame layout changed"
        )
    frame = state[frame_offset:]
    if not frame.startswith(ZSTD_MAGIC) or zstd.frame_size(frame) != compressed_size:
        raise RicoFirewoodReplyMigrationError(
            "Source compressed frame identity is invalid"
        )
    source_payload = zstd.decompress(frame)
    if (
        len(source_payload) != SOURCE_PAYLOAD_SIZE
        or _sha256(source_payload) != SOURCE_PAYLOAD_SHA256
    ):
        raise RicoFirewoodReplyMigrationError(
            "Source decompressed payload identity changed"
        )
    ram_offset = _psx_ram_offset(source_payload)
    if ram_offset != SOURCE_RAM_OFFSET or ram_offset + RAM_SIZE > len(source_payload):
        raise RicoFirewoodReplyMigrationError("Source PSX RAM layout changed")
    source_ram = source_payload[ram_offset : ram_offset + RAM_SIZE]
    if _sha256(source_ram) != SOURCE_RAM_SHA256:
        raise RicoFirewoodReplyMigrationError("Source PSX RAM identity changed")

    script_start = RESIDENT_SCRIPT_PAYLOAD_OFFSET
    script_end = script_start + RESIDENT_SCRIPT_SIZE
    dialogue_start = RESIDENT_DIALOGUE_PAYLOAD_OFFSET
    dialogue_end = dialogue_start + RESIDENT_DIALOGUE_SIZE
    allocated_end = dialogue_start + RESIDENT_DIALOGUE_ALLOCATED_SIZE
    alignment_end = allocated_end + len(RESIDENT_DIALOGUE_ALIGNMENT)
    header_end = alignment_end + len(NEXT_ALLOCATOR_HEADER)
    source_script = source_payload[script_start:script_end]
    source_dialogue = source_payload[dialogue_start:dialogue_end]
    _validate_resident_father_bridge(source_script, source_dialogue)
    if source_script == target_script:
        raise RicoFirewoodReplyMigrationError(
            "Resident father bridge was unexpectedly replaced by the media script"
        )
    if (
        _sha256(source_payload[script_end:dialogue_start])
        != SCRIPT_DIALOGUE_GAP_SHA256
        or source_payload[dialogue_end:allocated_end]
        != RESIDENT_DIALOGUE_UNUSED_TAIL
        or source_payload[allocated_end:alignment_end]
        != RESIDENT_DIALOGUE_ALIGNMENT
        or source_payload[alignment_end:header_end] != NEXT_ALLOCATOR_HEADER
        or _sha256(source_payload[dialogue_start:allocated_end])
        != RESIDENT_DIALOGUE_ALLOCATION_SHA256
    ):
        raise RicoFirewoodReplyMigrationError(
            "Resident script/dialogue allocator boundary changed"
        )

    blocks = _raw_dialogue_blocks(source_dialogue)
    active = blocks[ACTIVE_DIALOGUE_ID]
    statuses = tuple(
        struct.unpack_from(
            "<h",
            source_ram,
            DIALOG_WINDOWS
            + index * DIALOG_WINDOW_STRIDE
            + DIALOG_WINDOW_STATUS_OFFSET,
        )[0]
        for index in range(DIALOG_WINDOW_COUNT)
    )
    if (
        struct.unpack_from("<I", source_ram, GAME_SCENE_MAP)[0]
        != EXPECTED_GAME_SCENE_MAP
        or struct.unpack_from("<I", source_ram, FIELD_NUM_ACTORS)[0]
        != EXPECTED_ACTOR_COUNT
        or struct.unpack_from("<I", source_ram, FIELD_ACTORS)[0]
        != EXPECTED_ACTOR_ARRAY_GUEST_POINTER
        or struct.unpack_from("<I", source_ram, FIELD_CUR_SCRIPT_FILE)[0]
        != RESIDENT_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", source_ram, FIELD_CUR_DIALOGUE_FILE)[0]
        != RESIDENT_DIALOGUE_GUEST_POINTER
        or statuses != EXPECTED_WINDOW_STATUSES
        or struct.unpack_from("<I", source_ram, WINDOW0_START_POINTER_OFFSET)[0]
        != EXPECTED_WINDOW0_START_POINTER
        or struct.unpack_from("<I", source_ram, WINDOW0_CURRENT_POINTER_OFFSET)[0]
        != EXPECTED_WINDOW0_CURRENT_POINTER
        or active.offset != ACTIVE_DIALOGUE_OFFSET
        or not (
            RESIDENT_DIALOGUE_GUEST_POINTER + active.offset
            <= EXPECTED_WINDOW0_START_POINTER
            <= EXPECTED_WINDOW0_CURRENT_POINTER
            < RESIDENT_DIALOGUE_GUEST_POINTER
            + active.offset
            + len(active.payload)
        )
        or _sha256(
            source_ram[
                DIALOG_WINDOWS :
                DIALOG_WINDOWS + DIALOG_WINDOW_STRIDE * DIALOG_WINDOW_COUNT
            ]
        )
        != EXPECTED_DIALOG_WINDOWS_SHA256
        or _sha256(source_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE])
        != EXPECTED_GAMESTATE_SHA256
        or _sha256(
            source_ram[
                FIELD_SCRIPT_MEMORY :
                FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE
            ]
        )
        != EXPECTED_FIELD_VARIABLE_BANK_SHA256
    ):
        raise RicoFirewoodReplyMigrationError(
            "Live field/progress/window topology changed"
        )

    table_start = ARCHIVE_TABLE_PAYLOAD_OFFSET
    table_end = table_start + ARCHIVE_TABLE_SIZE
    source_table = source_payload[table_start:table_end]
    normalized_source_table = source_table[:-1] + target_table[-1:]
    if (
        len(source_table) != ARCHIVE_TABLE_SIZE
        or _sha256(source_table) != SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256
        or source_table[-1] != SOURCE_VOLATILE_ARCHIVE_BYTE
        or _sha256(normalized_source_table) != SOURCE_ARCHIVE_TABLE_SHA256
        or _differences(normalized_source_table, target_table)
        != ARCHIVE_TABLE_DIFFS
    ):
        raise RicoFirewoodReplyMigrationError(
            "Source/final resident Disc-1 FAT contract changed"
        )

    resident_dialogue = _build_resident_dialogue(
        source_dialogue,
        target_dialogue,
    )
    payload = bytearray(source_payload)
    payload[dialogue_start:dialogue_end] = resident_dialogue
    for relative, old, new in ARCHIVE_TABLE_DIFFS:
        absolute = table_start + relative
        if payload[absolute] != old:
            raise RicoFirewoodReplyMigrationError(
                f"Resident FAT byte changed at payload 0x{absolute:X}"
            )
        payload[absolute] = new
    final_payload = bytes(payload)

    dialogue_diffs = _differences(source_dialogue, resident_dialogue)
    expected_changes = tuple(
        sorted(
            (
                *((dialogue_start + offset, old, new) for offset, old, new in dialogue_diffs),
                *((table_start + offset, old, new) for offset, old, new in ARCHIVE_TABLE_DIFFS),
            )
        )
    )
    actual_changes = _differences(source_payload, final_payload)
    if actual_changes != expected_changes:
        raise RicoFirewoodReplyMigrationError(
            "Migration changed bytes outside the exact dialogue/FAT whitelist"
        )
    if (
        len(dialogue_diffs) != EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT
        or len(actual_changes) != EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT
    ):
        raise RicoFirewoodReplyMigrationError(
            "Migration payload changed-byte count drifted"
        )

    final_table = final_payload[table_start:table_end]
    if (
        _sha256(final_table) != TARGET_RESIDENT_ARCHIVE_TABLE_SHA256
        or final_table[:-1] != target_table[:-1]
        or final_table[-1] != SOURCE_VOLATILE_ARCHIVE_BYTE
        or final_payload[script_start:script_end] != source_script
        or final_payload[script_end:dialogue_start]
        != source_payload[script_end:dialogue_start]
        or final_payload[dialogue_end:header_end]
        != source_payload[dialogue_end:header_end]
    ):
        raise RicoFirewoodReplyMigrationError(
            "Migration changed the script/allocator or did not install the exact FAT"
        )
    final_ram = final_payload[ram_offset : ram_offset + RAM_SIZE]
    preserved_ram_spans = (
        (GAME_STATE, GAMESTATE_SIZE, "GameState"),
        (FIELD_SCRIPT_MEMORY, FIELD_VARIABLE_BANK_SIZE, "field variables"),
        (
            DIALOG_WINDOWS,
            DIALOG_WINDOW_STRIDE * DIALOG_WINDOW_COUNT,
            "dialogue windows",
        ),
    )
    for start, size, label in preserved_ram_spans:
        if final_ram[start : start + size] != source_ram[start : start + size]:
            raise RicoFirewoodReplyMigrationError(f"{label} was not preserved")

    final_payload_hash = _sha256(final_payload)
    if final_payload_hash != EXPECTED_OUTPUT_PAYLOAD_SHA256:
        raise RicoFirewoodReplyMigrationError(
            "Fixed-span output payload identity changed: " + final_payload_hash
        )
    compressed = zstd.compress(final_payload)
    prefix = bytearray(state[:frame_offset])
    struct.pack_into(
        "<I",
        prefix,
        DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        len(compressed),
    )
    result = bytes(prefix) + compressed
    if zstd.decompress(result[frame_offset:]) != final_payload:
        raise RicoFirewoodReplyMigrationError(
            "Candidate failed its Zstandard round trip"
        )
    result_hash = _sha256(result)
    if (
        len(result) != EXPECTED_OUTPUT_SIZE
        or result_hash != EXPECTED_OUTPUT_SHA256
    ):
        raise RicoFirewoodReplyMigrationError(
            "Fixed-span candidate identity changed: "
            f"{len(result)} / {result_hash}"
        )

    return result, {
        "source_state_sha256": state_hash,
        "output_state_sha256": result_hash,
        "source_state_size": len(state),
        "output_state_size": len(result),
        "source_payload_sha256": SOURCE_PAYLOAD_SHA256,
        "output_payload_sha256": final_payload_hash,
        "payload_changed_byte_count": len(actual_changes),
        "resident_script_changed_byte_count": 0,
        "resident_dialogue_changed_byte_count": len(dialogue_diffs),
        "resident_fat_changed_byte_count": len(ARCHIVE_TABLE_DIFFS),
        "resident_dialogue_size": len(resident_dialogue),
        "normal_media_dialogue_size": len(target_dialogue),
        "firewood_reply_dialogue_id": FIREWOOD_REPLY_DIALOGUE_ID,
        "active_dialogue_id": ACTIVE_DIALOGUE_ID,
        "active_dialogue_window_preserved": True,
        "dialogue_offsets_preserved": True,
        "father_dialogue_bridge_preserved": True,
        "script_allocation_relocated": False,
        "dialogue_allocation_relocated": False,
        "allocator_header_preserved": True,
        "gamestate_field_variables_windows_preserved": True,
        "resident_fat_migrated": True,
        "cold_reload_uses_normal_packed_dialogue": True,
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
    if source == output or output == LIVE_SLOT_ONE.resolve():
        raise SystemExit(
            "Output must be separate and may not be DuckStation's live Slot 1"
        )
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
            source.read_bytes(),
            zstd=_Zstd(zstd_path),
            new_disc=new_disc,
        )
    except RicoFirewoodReplyMigrationError as exc:
        raise SystemExit(str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)
    if output.read_bytes() != result:
        raise SystemExit("Written candidate changed on disk")
    print(f"Wrote fixed-span firewood-reply candidate: {output}")
    for key, value in report.items():
        print(f"{key}: {value}")
    print("The source and DuckStation's live Slot 1 were not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
