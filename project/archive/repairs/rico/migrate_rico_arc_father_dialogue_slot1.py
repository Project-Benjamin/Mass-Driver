#!/usr/bin/env python3
"""Migrate the audited Rico Slot 1 to the revised father-door dialogue.

The captured state has Chapter 1's house field resident behind an open text
window.  The normal rebuilt field has a 129-byte-larger dialogue component,
so copying it over the resident allocation would overwrite the next live heap
header.  This migration instead builds a field-resident bridge without moving
any component, dialogue offset, pointer, or allocator byte:

* the new first Rico line is padded into its existing dialogue-127 span;
* the new combined Anne/Rico continuation is padded into dialogue 57, a
  263-byte block with no F5/D2 reference anywhere in the house script; and
* the still-dormant doorway routine changes its second dialogue operand from
  128 to 57.

Dialogue 57's prose belongs to the separate firewood scene and is duplicated
in that field's own resource, so it is unreachable in the resident house.
The exact rebuilt Disc-1 FAT is also adopted (apart from its known volatile
tail byte).  Once the player leaves or otherwise reloads the house, the normal
two-block version is loaded from rebuilt media.

Only the exact audited state and exact staged Disc 1 are accepted.  The tool
always writes a separate candidate and refuses DuckStation's live Slot 1.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct
import sys
from typing import Final, NamedTuple, Sequence


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
from tools.xgdialog import decode_text  # noqa: E402
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
    ROOT / "work" / "rico_dad_stage" / "Xenogears_Rico_Arc_Disc_1.bin"
)

SOURCE_STATE_SIZE: Final = 1_366_013
SOURCE_STATE_SHA256: Final = (
    "ddf81b82182f0ce664ffe3d190d2fcc61ff75a065ab8fcd02de21eceed6e40d8"
)
SOURCE_FRAME_OFFSET: Final = 0x6DD0
SOURCE_COMPRESSED_SIZE: Final = 1_337_901
SOURCE_PAYLOAD_SIZE: Final = 3_817_429
SOURCE_PAYLOAD_SHA256: Final = (
    "3f9ce043263d6cddee81867cfcacf4cbe3b958f297bb1d8c9b772d2bd2992b2b"
)
SOURCE_RAM_OFFSET: Final = 0x1A62
SOURCE_RAM_SHA256: Final = (
    "fd0cf808e2e9047b2aa1c6dfe8e0ecc04bab4089078344cb12e661f34d46fce5"
)
SOURCE_MEDIA_PATH: Final = (
    rb"C:\Users\Chad\Xenogears_Reimagined\output\rico_arc\Xenogears_Rico_Arc.m3u"
)

HOUSE_FIELD_CANONICAL_ID: Final = 2048
HOUSE_FIELD_SCENE: Final = 721
HOUSE_FIELD_SECTOR: Final = 230_237
TARGET_HOUSE_FIELD_SIZE: Final = 37_796
TARGET_HOUSE_FIELD_SHA256: Final = (
    "9c82db3d88e4e70ab9924b324e74aa3fcff703a007ee16f6d62aa91846ccfbd4"
)

SCRIPT_COMPONENT_INDEX: Final = 5
DIALOGUE_COMPONENT_INDEX: Final = 7
RESIDENT_SCRIPT_PAYLOAD_OFFSET: Final = 0x10C822
RESIDENT_SCRIPT_SIZE: Final = 5_426
RESIDENT_SCRIPT_SHA256: Final = (
    "85e334efff6a70674d84615fde31be4fd5be8f60bd1eebdb46e7ebc2b9d20386"
)
SCRIPT_BYTECODE_OFFSET: Final = 0x0704
DOORWAY_SECOND_DIALOGUE_PC: Final = 0x0D44
SOURCE_DOORWAY_SECOND_DIALOGUE: Final = bytes.fromhex("F5 80 00 00 9C")
RESIDENT_DOORWAY_SECOND_DIALOGUE: Final = bytes.fromhex("F5 39 00 00 9C")
RESIDENT_SCRIPT_GUEST_POINTER: Final = 0x8010ADC0
SCRIPT_DIALOGUE_GAP_SIZE: Final = 74
SCRIPT_DIALOGUE_GAP_SHA256: Final = (
    "cb98285922eb7787dd16492152a83067ba80c92456be560eaa25c3d7d0936c1e"
)

RESIDENT_DIALOGUE_PAYLOAD_OFFSET: Final = 0x10DD9E
SOURCE_DIALOGUE_SIZE: Final = 11_794
SOURCE_DIALOGUE_SHA256: Final = (
    "e96b1a4bc2d525150511cce3dd9d01206814da050c7a400400b32f2e5451f0ed"
)
TARGET_DIALOGUE_SIZE: Final = 11_923
TARGET_DIALOGUE_SHA256: Final = (
    "1c036e7cb88d75c850f860ec1101d635543d6a8b6e75318f844056843f03833d"
)
DIALOGUE_BLOCK_COUNT: Final = 129
RESIDENT_DIALOGUE_GUEST_POINTER: Final = 0x8010C33C
FIELD_CUR_DIALOGUE_FILE: Final = 0x0ADBF0

# All three resident spans stay at their original offsets and capacities.
BRIDGE_DIALOGUE_ID: Final = 57
BRIDGE_DIALOGUE_OFFSET: Final = 0x12CF
BRIDGE_DIALOGUE_CAPACITY: Final = 263
FIRST_DIALOGUE_ID: Final = 127
FIRST_DIALOGUE_OFFSET: Final = 0x2D67
FIRST_DIALOGUE_CAPACITY: Final = 47
OBSOLETE_DIALOGUE_ID: Final = 128
OBSOLETE_DIALOGUE_OFFSET: Final = 0x2D96
OBSOLETE_DIALOGUE_CAPACITY: Final = 124
TARGET_FIRST_DIALOGUE_OFFSET: Final = 0x2D67
TARGET_FIRST_DIALOGUE_SIZE: Final = 40
TARGET_CONTINUATION_DIALOGUE_OFFSET: Final = 0x2D8F
TARGET_CONTINUATION_DIALOGUE_SIZE: Final = 260
TARGET_FIRST_DIMENSIONS: Final = (56, 3)
TARGET_CONTINUATION_DIMENSIONS: Final = (54, 3)

EXPECTED_FIRST_DIALOGUE: Final = (
    "<Rico>\nMom... how come I don't have\na dad?<Close>"
)
EXPECTED_CONTINUATION_DIALOGUE: Final = (
    "Anne\nRico, you do have a father.<New>"
    "<Rico>\nThen where is he?<New>"
    "Anne\nHe's... away.<New>"
    "Fighting in the war.<New>"
    "<Rico>\nIs he ever coming back?<New>"
    "Anne\nW-Well... that is...<New>"
    "I don't know.<New>"
    "Anne\nBut your father is a great\nman, Rico.<New>"
    "And someday...<New>"
    "I know you'll follow in his\nfootsteps.<Close>"
)
SOURCE_BRIDGE_DIALOGUE_PREFIX: Final = (
    "Outside their house, pale\ndaylight lies over the\nsettlement"
)
SOURCE_OBSOLETE_DIALOGUE_PREFIX: Final = (
    "Anne\nWhen the war is over, I hope.<New>"
)

# The old logical dialogue used 11,794 of its 11,803-byte allocation.  Seven
# alignment bytes and the next 18-byte allocator header follow that allocation.
RESIDENT_DIALOGUE_ALLOCATED_SIZE: Final = 11_803
RESIDENT_DIALOGUE_ALLOCATION_SHA256: Final = (
    "7e1d2c5084c3a4f850fc9f2790293867149926c4faca398cb370e2e83a322692"
)
RESIDENT_DIALOGUE_UNUSED_TAIL: Final = bytes(9)
RESIDENT_DIALOGUE_ALIGNMENT: Final = bytes(7)
NEXT_ALLOCATOR_HEADER: Final = bytes.fromhex(
    "60 1D 00 02 2D E4 4B 12 6B 51 90 FC 10 80 5E C4 01 81"
)

TARGET_DISC_SIZE: Final = 719_175_744
TARGET_DISC_SHA256: Final = (
    "1bf9eebcdfa2298653e4d27c686c14b1defca3e8fcb19c1c540713ba08e0a180"
)
ARCHIVE_TABLE_SIZE: Final = 0x8000
ARCHIVE_TABLE_PAYLOAD_OFFSET: Final = 0x11A66
SOURCE_ARCHIVE_TABLE_SHA256: Final = (
    "db423876ee5f975cdf053d10101abfc97030d459914931b38dad40da43821edc"
)
SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "7cd56307bfbcbd45f316810c253356b68f491a051a67a707bdfdec7a77373eda"
)
SOURCE_VOLATILE_ARCHIVE_BYTE: Final = 0xC4
TARGET_ARCHIVE_TABLE_SHA256: Final = (
    "6a41348947362660556b561c0f8792cdbcb38639840f7711e7d30eabad29666c"
)
TARGET_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "96d391672da4e9bc97323c67a2261c9b75f227ea459b90a467163992ba87cf5c"
)
ARCHIVE_TABLE_DIFFS: Final = (
    (0x3803, 0x4C, 0xA4),  # FAT 2048 size: 37,708 -> 37,796
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

# Keeping the complete bridge, payload, and state identities pinned makes a
# future compressor/library or contract drift fail closed.
EXPECTED_RESIDENT_SCRIPT_SHA256: Final = (
    "c61094be0baf53aa838f7c29871d963d0a1bc40c08888de099b12f81913dcc29"
)
EXPECTED_RESIDENT_DIALOGUE_SHA256: Final = (
    "f37d7b21f0e82c99fbcfee57782751af79a73f30cdc29ed5d1aa9a9c696f28e6"
)
EXPECTED_SCRIPT_CHANGED_BYTE_COUNT: Final = 1
EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT: Final = 289
EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT: Final = 291
EXPECTED_OUTPUT_PAYLOAD_SHA256: Final = (
    "a83141d45e96e578daa982df953ae9445d0f8157dbfc726194262bc763d5caa5"
)
EXPECTED_OUTPUT_SIZE: Final = 1_366_030
EXPECTED_OUTPUT_SHA256: Final = (
    "a8987ae352c2a0971d7d5dcbaaac4ac1c8d80f5a6858fb700e027b4435846cc4"
)


class RicoFatherDialogueMigrationError(RuntimeError):
    """Raised before output whenever the pinned migration contract drifts."""


class _DialogueBlock(NamedTuple):
    block_id: int
    offset: int
    payload: bytes
    width: int
    height: int


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _differences(
    before: bytes,
    after: bytes,
) -> tuple[tuple[int, int, int], ...]:
    if len(before) != len(after):
        raise RicoFatherDialogueMigrationError(
            f"Compared payload sizes differ: {len(before)} != {len(after)}"
        )
    return tuple(
        (offset, old, new)
        for offset, (old, new) in enumerate(zip(before, after, strict=True))
        if old != new
    )


def _raw_dialogue_blocks(data: bytes) -> tuple[_DialogueBlock, ...]:
    """Parse spans without rejecting the donor's intentional block-26 tail."""

    if len(data) < 8:
        raise RicoFatherDialogueMigrationError("Dialogue component is truncated")
    count = struct.unpack_from("<I", data, 0)[0] + 1
    header_size = 4 + 4 * count
    if header_size > len(data):
        raise RicoFatherDialogueMigrationError("Dialogue header exceeds component")
    offsets = tuple(
        struct.unpack_from("<H", data, 4 + index * 2)[0]
        for index in range(count)
    )
    if (
        offsets[0] != header_size
        or tuple(sorted(offsets)) != offsets
        or len(set(offsets)) != len(offsets)
        or offsets[-1] >= len(data)
    ):
        raise RicoFatherDialogueMigrationError("Dialogue offset table drifted")
    dimensions = 4 + count * 2
    return tuple(
        _DialogueBlock(
            block_id=index,
            offset=start,
            payload=data[
                start : offsets[index + 1] if index + 1 < count else len(data)
            ],
            width=data[dimensions + index * 2],
            height=data[dimensions + index * 2 + 1],
        )
        for index, start in enumerate(offsets)
    )


def _dialogue_dimensions_offset(block_count: int, block_id: int) -> int:
    return 4 + block_count * 2 + block_id * 2


def _dialogue_command(block_id: int) -> bytes:
    # Match the opcode and operand regardless of the following flags byte.
    return b"\xF5" + struct.pack("<H", block_id)


def _choice_command(block_id: int) -> bytes:
    return b"\xD2" + struct.pack("<H", block_id)


def _validated_target_resources(new_disc: Path) -> tuple[bytes, bytes, bytes]:
    if (
        not new_disc.is_file()
        or new_disc.stat().st_size != TARGET_DISC_SIZE
        or _file_sha256(new_disc) != TARGET_DISC_SHA256
    ):
        raise RicoFatherDialogueMigrationError(
            "Final staged Rico Disc 1 identity changed"
        )

    image = Mode2Image(new_disc)
    entries = image.read_index()
    if HOUSE_FIELD_CANONICAL_ID >= len(entries):
        raise RicoFatherDialogueMigrationError(
            "Final staged Disc 1 is missing canonical 2048"
        )
    entry = entries[HOUSE_FIELD_CANONICAL_ID]
    if (
        entry.kind != "file"
        or entry.sector != HOUSE_FIELD_SECTOR
        or entry.size != TARGET_HOUSE_FIELD_SIZE
    ):
        raise RicoFatherDialogueMigrationError(
            "Final staged Chapter 1 house allocation changed"
        )
    field = image.extract_entry(entry)
    if (
        len(field) != TARGET_HOUSE_FIELD_SIZE
        or _sha256(field) != TARGET_HOUSE_FIELD_SHA256
    ):
        raise RicoFatherDialogueMigrationError(
            "Final staged Chapter 1 house identity changed"
        )
    parsed = parse_field(field)
    if len(parsed.parts) != 9:
        raise RicoFatherDialogueMigrationError(
            "Final staged Chapter 1 component count changed"
        )
    script = parsed.parts[SCRIPT_COMPONENT_INDEX].data
    dialogue = parsed.parts[DIALOGUE_COMPONENT_INDEX].data
    if (
        len(script) != RESIDENT_SCRIPT_SIZE
        or _sha256(script) != RESIDENT_SCRIPT_SHA256
    ):
        raise RicoFatherDialogueMigrationError(
            "Two-block rebuild unexpectedly changed the house script"
        )
    if (
        len(dialogue) != TARGET_DIALOGUE_SIZE
        or _sha256(dialogue) != TARGET_DIALOGUE_SHA256
    ):
        raise RicoFatherDialogueMigrationError(
            "Final staged father dialogue identity changed"
        )
    editor = AtelScript(script)
    if (
        editor.entity_count != 26
        or editor.bytecode_offset != SCRIPT_BYTECODE_OFFSET
        or editor.get_script_pointer(25, 2) != 0x0CDE
        or editor.bytecode[
            DOORWAY_SECOND_DIALOGUE_PC :
            DOORWAY_SECOND_DIALOGUE_PC + len(SOURCE_DOORWAY_SECOND_DIALOGUE)
        ]
        != SOURCE_DOORWAY_SECOND_DIALOGUE
        or script.count(_dialogue_command(BRIDGE_DIALOGUE_ID)) != 0
        or script.count(_choice_command(BRIDGE_DIALOGUE_ID)) != 0
        or script.count(_dialogue_command(OBSOLETE_DIALOGUE_ID)) != 1
    ):
        raise RicoFatherDialogueMigrationError(
            "Final staged doorway-script topology changed"
        )

    blocks = _raw_dialogue_blocks(dialogue)
    if len(blocks) != DIALOGUE_BLOCK_COUNT:
        raise RicoFatherDialogueMigrationError(
            "Final staged dialogue block count changed"
        )
    first = blocks[FIRST_DIALOGUE_ID]
    continuation = blocks[OBSOLETE_DIALOGUE_ID]
    if (
        (first.offset, len(first.payload), first.width, first.height)
        != (
            TARGET_FIRST_DIALOGUE_OFFSET,
            TARGET_FIRST_DIALOGUE_SIZE,
            *TARGET_FIRST_DIMENSIONS,
        )
        or decode_text(first.payload) != EXPECTED_FIRST_DIALOGUE
        or (
            continuation.offset,
            len(continuation.payload),
            continuation.width,
            continuation.height,
        )
        != (
            TARGET_CONTINUATION_DIALOGUE_OFFSET,
            TARGET_CONTINUATION_DIALOGUE_SIZE,
            *TARGET_CONTINUATION_DIMENSIONS,
        )
        or decode_text(continuation.payload) != EXPECTED_CONTINUATION_DIALOGUE
    ):
        raise RicoFatherDialogueMigrationError(
            "Final staged father dialogue text/layout changed"
        )

    table = _archive_table(new_disc)
    if (
        len(table) != ARCHIVE_TABLE_SIZE
        or _sha256(table) != TARGET_ARCHIVE_TABLE_SHA256
    ):
        raise RicoFatherDialogueMigrationError(
            "Final staged Disc-1 archive table identity changed"
        )
    return script, dialogue, table


def _build_resident_script(source: bytes) -> bytes:
    if (len(source), _sha256(source)) != (
        RESIDENT_SCRIPT_SIZE,
        RESIDENT_SCRIPT_SHA256,
    ):
        raise RicoFatherDialogueMigrationError(
            "Resident Chapter 1 script identity changed"
        )
    editor = AtelScript(source)
    start = SCRIPT_BYTECODE_OFFSET + DOORWAY_SECOND_DIALOGUE_PC
    end = start + len(SOURCE_DOORWAY_SECOND_DIALOGUE)
    if (
        editor.entity_count != 26
        or editor.bytecode_offset != SCRIPT_BYTECODE_OFFSET
        or editor.get_script_pointer(25, 2) != 0x0CDE
        or source[start:end] != SOURCE_DOORWAY_SECOND_DIALOGUE
        or source.count(_dialogue_command(BRIDGE_DIALOGUE_ID)) != 0
        or source.count(_choice_command(BRIDGE_DIALOGUE_ID)) != 0
        or source.count(_dialogue_command(OBSOLETE_DIALOGUE_ID)) != 1
    ):
        raise RicoFatherDialogueMigrationError(
            "Resident doorway-script provenance changed"
        )
    resident = bytearray(source)
    resident[start:end] = RESIDENT_DOORWAY_SECOND_DIALOGUE
    result = bytes(resident)
    if (
        len(_differences(source, result)) != EXPECTED_SCRIPT_CHANGED_BYTE_COUNT
        or result.count(_dialogue_command(BRIDGE_DIALOGUE_ID)) != 1
        or result.count(_choice_command(BRIDGE_DIALOGUE_ID)) != 0
        or result.count(_dialogue_command(OBSOLETE_DIALOGUE_ID)) != 0
    ):
        raise RicoFatherDialogueMigrationError(
            "Allocator-safe doorway-script rewrite is not exact"
        )
    if _sha256(result) != EXPECTED_RESIDENT_SCRIPT_SHA256:
        raise RicoFatherDialogueMigrationError(
            "Allocator-safe resident script identity changed"
        )
    return result


def _build_resident_dialogue(source: bytes, target: bytes) -> bytes:
    if (len(source), _sha256(source)) != (
        SOURCE_DIALOGUE_SIZE,
        SOURCE_DIALOGUE_SHA256,
    ):
        raise RicoFatherDialogueMigrationError(
            "Resident Chapter 1 dialogue identity changed"
        )
    source_blocks = _raw_dialogue_blocks(source)
    target_blocks = _raw_dialogue_blocks(target)
    if len(source_blocks) != DIALOGUE_BLOCK_COUNT:
        raise RicoFatherDialogueMigrationError(
            "Resident dialogue block count changed"
        )
    source_bridge = source_blocks[BRIDGE_DIALOGUE_ID]
    source_first = source_blocks[FIRST_DIALOGUE_ID]
    source_obsolete = source_blocks[OBSOLETE_DIALOGUE_ID]
    target_first = target_blocks[FIRST_DIALOGUE_ID]
    target_continuation = target_blocks[OBSOLETE_DIALOGUE_ID]
    if (
        (
            source_bridge.offset,
            len(source_bridge.payload),
        )
        != (BRIDGE_DIALOGUE_OFFSET, BRIDGE_DIALOGUE_CAPACITY)
        or not decode_text(source_bridge.payload).startswith(
            SOURCE_BRIDGE_DIALOGUE_PREFIX
        )
        or (source_first.offset, len(source_first.payload))
        != (FIRST_DIALOGUE_OFFSET, FIRST_DIALOGUE_CAPACITY)
        or (source_obsolete.offset, len(source_obsolete.payload))
        != (OBSOLETE_DIALOGUE_OFFSET, OBSOLETE_DIALOGUE_CAPACITY)
        or not decode_text(source_obsolete.payload).startswith(
            SOURCE_OBSOLETE_DIALOGUE_PREFIX
        )
        or len(target_first.payload) > FIRST_DIALOGUE_CAPACITY
        or len(target_continuation.payload) > BRIDGE_DIALOGUE_CAPACITY
    ):
        raise RicoFatherDialogueMigrationError(
            "Resident dialogue bridge spans/provenance changed"
        )

    resident = bytearray(source)
    dimensions = _dialogue_dimensions_offset(
        DIALOGUE_BLOCK_COUNT,
        BRIDGE_DIALOGUE_ID,
    )
    resident[dimensions : dimensions + 2] = bytes(
        TARGET_CONTINUATION_DIMENSIONS
    )
    resident[
        BRIDGE_DIALOGUE_OFFSET :
        BRIDGE_DIALOGUE_OFFSET + BRIDGE_DIALOGUE_CAPACITY
    ] = target_continuation.payload + bytes(
        BRIDGE_DIALOGUE_CAPACITY - len(target_continuation.payload)
    )
    resident[
        FIRST_DIALOGUE_OFFSET :
        FIRST_DIALOGUE_OFFSET + FIRST_DIALOGUE_CAPACITY
    ] = target_first.payload + bytes(
        FIRST_DIALOGUE_CAPACITY - len(target_first.payload)
    )
    result = bytes(resident)
    result_blocks = _raw_dialogue_blocks(result)
    bridge = result_blocks[BRIDGE_DIALOGUE_ID]
    first = result_blocks[FIRST_DIALOGUE_ID]
    if (
        len(result) != SOURCE_DIALOGUE_SIZE
        or tuple(block.offset for block in result_blocks)
        != tuple(block.offset for block in source_blocks)
        or (bridge.width, bridge.height) != TARGET_CONTINUATION_DIMENSIONS
        or bridge.payload
        != target_continuation.payload
        + bytes(BRIDGE_DIALOGUE_CAPACITY - len(target_continuation.payload))
        or decode_text(bridge.payload)
        != EXPECTED_CONTINUATION_DIALOGUE
        + "<Close>" * (BRIDGE_DIALOGUE_CAPACITY - len(target_continuation.payload))
        or first.payload
        != target_first.payload
        + bytes(FIRST_DIALOGUE_CAPACITY - len(target_first.payload))
        or decode_text(first.payload)
        != EXPECTED_FIRST_DIALOGUE
        + "<Close>" * (FIRST_DIALOGUE_CAPACITY - len(target_first.payload))
        or result_blocks[OBSOLETE_DIALOGUE_ID] != source_obsolete
    ):
        raise RicoFatherDialogueMigrationError(
            "Allocator-safe resident dialogue bridge is not exact"
        )
    if (
        len(_differences(source, result))
        != EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT
    ):
        raise RicoFatherDialogueMigrationError(
            "Resident dialogue changed-byte count drifted"
        )
    if _sha256(result) != EXPECTED_RESIDENT_DIALOGUE_SHA256:
        raise RicoFatherDialogueMigrationError(
            "Allocator-safe resident dialogue identity changed"
        )
    return result


def migrate_state(
    state: bytes,
    *,
    zstd: _Zstd,
    new_disc: Path,
) -> tuple[bytes, dict[str, object]]:
    """Return the allocator-safe father-dialogue candidate and audit report."""

    state_hash = _sha256(state)
    if (len(state), state_hash) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise RicoFatherDialogueMigrationError(
            "Source Slot 1 identity changed: "
            f"{len(state)} bytes / {state_hash}; expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    if (
        len(state) < DUCKSTATION_STATE_HEADER_SIZE
        or state[:4] != DUCKSTATION_STATE_MAGIC
        or state.count(SOURCE_MEDIA_PATH) != 1
    ):
        raise RicoFatherDialogueMigrationError(
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
        raise RicoFatherDialogueMigrationError(
            "Source payload is not Zstandard-compressed"
        )
    if (
        compressed_size != SOURCE_COMPRESSED_SIZE
        or payload_size != SOURCE_PAYLOAD_SIZE
        or frame_offset != SOURCE_FRAME_OFFSET
        or frame_offset + compressed_size != len(state)
    ):
        raise RicoFatherDialogueMigrationError(
            "Source DuckStation frame layout changed"
        )
    frame = state[frame_offset:]
    if not frame.startswith(ZSTD_MAGIC) or zstd.frame_size(frame) != compressed_size:
        raise RicoFatherDialogueMigrationError(
            "Source compressed frame identity is invalid"
        )
    source_payload = zstd.decompress(frame)
    if (
        len(source_payload) != SOURCE_PAYLOAD_SIZE
        or _sha256(source_payload) != SOURCE_PAYLOAD_SHA256
    ):
        raise RicoFatherDialogueMigrationError(
            "Source decompressed payload identity changed"
        )
    ram_offset = _psx_ram_offset(source_payload)
    if ram_offset != SOURCE_RAM_OFFSET or ram_offset + RAM_SIZE > len(source_payload):
        raise RicoFatherDialogueMigrationError("Source PSX RAM layout changed")
    source_ram = source_payload[ram_offset : ram_offset + RAM_SIZE]
    if _sha256(source_ram) != SOURCE_RAM_SHA256:
        raise RicoFatherDialogueMigrationError("Source PSX RAM identity changed")

    script_start = RESIDENT_SCRIPT_PAYLOAD_OFFSET
    script_end = script_start + RESIDENT_SCRIPT_SIZE
    dialogue_start = RESIDENT_DIALOGUE_PAYLOAD_OFFSET
    dialogue_end = dialogue_start + SOURCE_DIALOGUE_SIZE
    allocated_end = dialogue_start + RESIDENT_DIALOGUE_ALLOCATED_SIZE
    alignment_end = allocated_end + len(RESIDENT_DIALOGUE_ALIGNMENT)
    header_end = alignment_end + len(NEXT_ALLOCATOR_HEADER)
    source_script = source_payload[script_start:script_end]
    source_dialogue = source_payload[dialogue_start:dialogue_end]
    if source_script != target_script:
        raise RicoFatherDialogueMigrationError(
            "Resident/final two-block house scripts are not identical"
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
        raise RicoFatherDialogueMigrationError(
            "Resident script/dialogue allocator boundary changed"
        )

    ram = source_ram
    source_blocks = _raw_dialogue_blocks(source_dialogue)
    active = source_blocks[ACTIVE_DIALOGUE_ID]
    statuses = tuple(
        struct.unpack_from(
            "<h",
            ram,
            DIALOG_WINDOWS
            + index * DIALOG_WINDOW_STRIDE
            + DIALOG_WINDOW_STATUS_OFFSET,
        )[0]
        for index in range(DIALOG_WINDOW_COUNT)
    )
    if (
        struct.unpack_from("<I", ram, GAME_SCENE_MAP)[0]
        != EXPECTED_GAME_SCENE_MAP
        or struct.unpack_from("<I", ram, FIELD_NUM_ACTORS)[0]
        != EXPECTED_ACTOR_COUNT
        or struct.unpack_from("<I", ram, FIELD_ACTORS)[0]
        != EXPECTED_ACTOR_ARRAY_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0]
        != RESIDENT_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_CUR_DIALOGUE_FILE)[0]
        != RESIDENT_DIALOGUE_GUEST_POINTER
        or statuses != EXPECTED_WINDOW_STATUSES
        or struct.unpack_from("<I", ram, WINDOW0_START_POINTER_OFFSET)[0]
        != EXPECTED_WINDOW0_START_POINTER
        or struct.unpack_from("<I", ram, WINDOW0_CURRENT_POINTER_OFFSET)[0]
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
            ram[
                DIALOG_WINDOWS :
                DIALOG_WINDOWS + DIALOG_WINDOW_STRIDE * DIALOG_WINDOW_COUNT
            ]
        )
        != EXPECTED_DIALOG_WINDOWS_SHA256
        or _sha256(ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE])
        != EXPECTED_GAMESTATE_SHA256
        or _sha256(
            ram[
                FIELD_SCRIPT_MEMORY :
                FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE
            ]
        )
        != EXPECTED_FIELD_VARIABLE_BANK_SHA256
    ):
        raise RicoFatherDialogueMigrationError(
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
        raise RicoFatherDialogueMigrationError(
            "Source/final resident Disc-1 FAT contract changed"
        )

    resident_script = _build_resident_script(source_script)
    resident_dialogue = _build_resident_dialogue(
        source_dialogue,
        target_dialogue,
    )
    payload = bytearray(source_payload)
    payload[script_start:script_end] = resident_script
    payload[dialogue_start:dialogue_end] = resident_dialogue
    for relative, old, new in ARCHIVE_TABLE_DIFFS:
        absolute = table_start + relative
        if payload[absolute] != old:
            raise RicoFatherDialogueMigrationError(
                f"Resident FAT byte changed at payload 0x{absolute:X}"
            )
        payload[absolute] = new
    final_payload = bytes(payload)

    script_diffs = _differences(source_script, resident_script)
    dialogue_diffs = _differences(source_dialogue, resident_dialogue)
    expected_changes = tuple(
        sorted(
            (
                *((script_start + offset, old, new) for offset, old, new in script_diffs),
                *((dialogue_start + offset, old, new) for offset, old, new in dialogue_diffs),
                *((table_start + offset, old, new) for offset, old, new in ARCHIVE_TABLE_DIFFS),
            )
        )
    )
    actual_changes = _differences(source_payload, final_payload)
    if actual_changes != expected_changes:
        raise RicoFatherDialogueMigrationError(
            "Migration changed bytes outside the exact script/dialogue/FAT whitelist"
        )
    if len(dialogue_diffs) != EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT:
        raise RicoFatherDialogueMigrationError(
            "Resident dialogue changed-byte count changed"
        )
    if len(actual_changes) != EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT:
        raise RicoFatherDialogueMigrationError(
            "Migration payload changed-byte count changed"
        )

    final_table = final_payload[table_start:table_end]
    if (
        _sha256(final_table) != TARGET_RESIDENT_ARCHIVE_TABLE_SHA256
        or final_table[:-1] != target_table[:-1]
        or final_table[-1] != SOURCE_VOLATILE_ARCHIVE_BYTE
        or final_payload[script_end:dialogue_start]
        != source_payload[script_end:dialogue_start]
        or final_payload[dialogue_end:header_end]
        != source_payload[dialogue_end:header_end]
    ):
        raise RicoFatherDialogueMigrationError(
            "Migration changed an allocator neighbor or did not install the exact FAT"
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
        if final_ram[start : start + size] != ram[start : start + size]:
            raise RicoFatherDialogueMigrationError(f"{label} was not preserved")

    final_payload_hash = _sha256(final_payload)
    if final_payload_hash != EXPECTED_OUTPUT_PAYLOAD_SHA256:
        raise RicoFatherDialogueMigrationError(
            "Allocator-safe output payload identity changed: " + final_payload_hash
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
        raise RicoFatherDialogueMigrationError(
            "Candidate failed its Zstandard round trip"
        )
    result_hash = _sha256(result)
    if (
        len(result) != EXPECTED_OUTPUT_SIZE
        or result_hash != EXPECTED_OUTPUT_SHA256
    ):
        raise RicoFatherDialogueMigrationError(
            "Allocator-safe candidate identity changed: "
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
        "resident_script_changed_byte_count": len(script_diffs),
        "resident_dialogue_changed_byte_count": len(dialogue_diffs),
        "resident_fat_changed_byte_count": len(ARCHIVE_TABLE_DIFFS),
        "resident_dialogue_size": len(resident_dialogue),
        "normal_media_dialogue_size": len(target_dialogue),
        "dialogue_growth_avoided": len(target_dialogue) - len(resident_dialogue),
        "bridge_dialogue_id": BRIDGE_DIALOGUE_ID,
        "active_dialogue_id": ACTIVE_DIALOGUE_ID,
        "active_dialogue_window_preserved": True,
        "dialogue_offsets_preserved": True,
        "script_allocation_relocated": False,
        "dialogue_allocation_relocated": False,
        "allocator_header_preserved": True,
        "gamestate_field_variables_windows_preserved": True,
        "resident_fat_migrated": True,
        "cold_reload_uses_normal_two_block_dialogue": True,
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
    except RicoFatherDialogueMigrationError as exc:
        raise SystemExit(str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)
    if output.read_bytes() != result:
        raise SystemExit("Written candidate changed on disk")
    print(f"Wrote allocator-safe father-dialogue candidate: {output}")
    for key, value in report.items():
        print(f"{key}: {value}")
    print("The source and DuckStation's live Slot 1 were not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
