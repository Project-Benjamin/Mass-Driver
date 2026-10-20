#!/usr/bin/env python3
"""Migrate the audited Rico Slot 1 to the Emerald Traveler revision.

The saved field-721 house keeps both its ATEL script and dialogue component
resident.  A rebuilt disc therefore cannot update either interaction by
itself.  This guarded migration installs the exact padded replacement script,
installs the shorter dialogue inside the existing allocation, adopts the two
changed Disc-1 FAT bytes, and clears only the completed reading-desk bit so the
new first-use narration is immediately testable.

The source state and DuckStation's live Slot 1 are never output targets.  The
tool accepts only the exact audited state, exact staged media, and exact
prepared canonical-2048 bundle, then writes a separate candidate.
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
    _archive_table,
    _Zstd,
)
from tools.migrate_rico_arc_father_dialogue_slot1 import (  # noqa: E402
    _raw_dialogue_blocks,
)
from tools.migrate_rico_arc_firewood_reply_slot1 import (  # noqa: E402
    DIALOG_WINDOWS,
    DIALOG_WINDOW_COUNT,
    DIALOG_WINDOW_STATUS_OFFSET,
    DIALOG_WINDOW_STRIDE,
    FIELD_CUR_DIALOGUE_FILE,
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
    FIELD_CUR_SCRIPT_FILE,
    FIELD_NUM_ACTORS,
    FIELD_SCRIPT_MEMORY,
    GAME_STATE,
    RAM_SIZE,
    _psx_ram_offset,
)


ROOT: Final = Path(__file__).resolve().parents[3]
LIVE_SLOT_ONE: Final = ROOT / "emulator_data" / "SLUS-00664_1.sav"
DEFAULT_SOURCE: Final = (
    ROOT
    / "work"
    / "save_backups"
    / "SLUS-00664_1_pre_emerald_traveler_a61f51ea.sav"
)
DEFAULT_OUTPUT: Final = (
    ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00664_1.emerald_traveler_candidate.sav"
)
DEFAULT_ZSTD: Final = ROOT / "work" / "duckstation" / "zstd.dll"
DEFAULT_NEW_DISC: Final = ROOT / "work" / "r35" / "Xenogears_Rico_Arc_Disc_1.bin"
DEFAULT_TARGET_BUNDLE: Final = (
    ROOT / "work" / "r35" / "prepared" / "disc1" / "2048.bin"
)

SOURCE_STATE_SIZE: Final = 1_679_128
SOURCE_STATE_SHA256: Final = (
    "a61f51ea534e2e63a5e11d65259c137c574bf15c2278f854a3622311fd497eb5"
)
SOURCE_FRAME_OFFSET: Final = 0xB8AC
SOURCE_COMPRESSED_SIZE: Final = 1_631_852
SOURCE_PAYLOAD_SIZE: Final = 3_817_149
SOURCE_PAYLOAD_SHA256: Final = (
    "86a04d362b9a243bf2d80325e721da85376957ee1d033d38faffb696ebb2d1b5"
)
SOURCE_RAM_OFFSET: Final = 0x1A62
SOURCE_RAM_SHA256: Final = (
    "ab6c626e92f798fbf3adc39f07a9c1a6e1ac178813adbb9e793305168c67f5d1"
)
SOURCE_MEDIA_PATH: Final = (
    rb"C:\Users\Chad\Xenogears_Reimagined\output\rico_arc\Xenogears_Rico_Arc.m3u"
)

HOUSE_FIELD_CANONICAL_ID: Final = 2048
HOUSE_FIELD_SECTOR: Final = 230_237
TARGET_HOUSE_FIELD_SIZE: Final = 37_460
TARGET_HOUSE_FIELD_SHA256: Final = (
    "95261d09cd038e42fa6183815179b208b286f6dc65ece3c7499d2862683477ed"
)
SCRIPT_COMPONENT_INDEX: Final = 5
DIALOGUE_COMPONENT_INDEX: Final = 7

TARGET_DISC_SIZE: Final = 719_175_744
TARGET_DISC_SHA256: Final = (
    "39e48aacfbc98422d30cb3c1c08cb2383b2de062a15a52eae27a9103099d1fd8"
)

RESIDENT_SCRIPT_PAYLOAD_OFFSET: Final = 0x10C822
RESIDENT_SCRIPT_GUEST_POINTER: Final = 0x8010ADC0
RESIDENT_SCRIPT_SIZE: Final = 5_426
SOURCE_RESIDENT_SCRIPT_SHA256: Final = (
    "067ce9f7bd966f7af4568963ffc75ab14784665e29888b8f6c85b5d1d5cc6063"
)
TARGET_RESIDENT_SCRIPT_SHA256: Final = (
    "b2b16c722a2857966fbdb7d364901c33b617c48805901d79842e7e1ade2d5470"
)
SCRIPT_BYTECODE_OFFSET: Final = 0x0704
READING_CONTROLLER_ENTITY: Final = 23
READING_ACTION_SCRIPT: Final = 2
READING_ACTION_PC: Final = 0x0A09
NEXT_CONTROLLER_ENTITY: Final = 24
NEXT_CONTROLLER_INIT_PC: Final = 0x0A8B
NEXT_CONTROLLER_UPDATE_PC: Final = 0x0AA4
READING_ACTION_SIZE: Final = NEXT_CONTROLLER_INIT_PC - READING_ACTION_PC
READING_ACTION_TRAILING_STOP_BYTES: Final = 41
SCRIPT_DIALOGUE_GAP_SIZE: Final = 74
SCRIPT_DIALOGUE_GAP_SHA256: Final = (
    "54ebe0f6a06561673fa8ba331445ad2a0e5e11758916e04f1f5a336be59679c8"
)

RESIDENT_DIALOGUE_PAYLOAD_OFFSET: Final = 0x10DD9E
RESIDENT_DIALOGUE_GUEST_POINTER: Final = 0x8010C33C
SOURCE_RESIDENT_DIALOGUE_SIZE: Final = 11_497
SOURCE_RESIDENT_DIALOGUE_SHA256: Final = (
    "fa88a677cb01fb087bc5f5a3a6fb1dd808604f5df4c91e395e2eefcd119a8dbb"
)
SOURCE_DIALOGUE_BLOCK_COUNT: Final = 128
TARGET_DIALOGUE_SIZE: Final = 11_249
TARGET_DIALOGUE_SHA256: Final = (
    "1be4f54f7385fca744106be79a2159f10c5c2da3075d584c38c048230f060567"
)
TARGET_DIALOGUE_BLOCK_COUNT: Final = 123
OBSOLETE_DIALOGUE_TAIL_SIZE: Final = (
    SOURCE_RESIDENT_DIALOGUE_SIZE - TARGET_DIALOGUE_SIZE
)
TARGET_RESIDENT_DIALOGUE_SPAN_SHA256: Final = (
    "06bcba4d69244863aa8004ac6e5089c367f9c59cc59da83ab7cd0cdd097aa8f2"
)
DIALOGUE_ALIGNMENT: Final = bytes.fromhex("00 51 48 48 42 55 74 40 42")
NEXT_ALLOCATOR_HEADER: Final = bytes.fromhex(
    "4E 4B 49 9D 00 53 4C 01 4B 22 60 FB 10 80 5E C4 01 81"
)

SOURCE_WINDOW_DIALOGUE_ID: Final = 81
SOURCE_READING_REPEAT_DIALOGUE_ID: Final = 104
SOURCE_READING_FIRST_DIALOGUE_IDS: Final = (105, 106, 107, 108, 109, 110)
TARGET_READING_REPEAT_DIALOGUE_ID: Final = 104
TARGET_READING_FIRST_DIALOGUE_ID: Final = 105
EXPECTED_TARGET_WINDOW_TEXT: Final = (
    "Rico looks through the glass\nat the weathered houses of\n"
    "the poor settlement on\nKislev's outskirts. Beyond\n"
    "them, the Imperial Capital\nfades into the cold haze.<Close>"
)
EXPECTED_TARGET_READING_REPEAT_TEXT: Final = (
    "The Emerald Traveler lies\nopen where Rico and his\n"
    "mother stopped reading.<New>Its heroine's journey will be\n"
    "key to saving the world.<Close>"
)
EXPECTED_TARGET_READING_FIRST_TEXT: Final = (
    "Rico inspects The Emerald\nTraveler, a book his mother\n"
    "has been reading with him.<New>It tells of a heroine whose\n"
    "journey will be key to saving\nthe world.<Close>"
)

ARCHIVE_TABLE_SIZE: Final = 0x8000
ARCHIVE_TABLE_PAYLOAD_OFFSET: Final = 0x11A66
SOURCE_NORMALIZED_ARCHIVE_TABLE_SHA256: Final = (
    "ce9f08126d63171be5c6b4d30cfac6e536d19d853063386b816b3bbb4cac3478"
)
SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "c2589b36980daa8fa13b47f3288ed8717c4fbc3fdbd718515fca2bd1e662c7ea"
)
SOURCE_VOLATILE_ARCHIVE_BYTE: Final = 0xC4
TARGET_ARCHIVE_TABLE_SHA256: Final = (
    "63a8459311dcfe8a339c60610137558f400268c627a8be876a4c1b46aa7c6c82"
)
TARGET_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "0e7ebfbfccaee7eee679ac22cf8c7447b3cce80da917fd424cc24bad49a62764"
)
ARCHIVE_TABLE_DIFFS: Final = (
    (0x3803, 0x00, 0x54),
    (0x3804, 0x93, 0x92),
)

GAME_SCENE_MAP: Final = 0x04F34C
EXPECTED_GAME_SCENE_MAP: Final = 0x02D1
EXPECTED_ACTOR_COUNT: Final = 47
EXPECTED_ACTOR_ARRAY_GUEST_POINTER: Final = 0x80110BD0
EXPECTED_WINDOW_STATUSES: Final = (-1, -1, -1, -1)
EXPECTED_WINDOW0_START_POINTER: Final = 0x8010E9F2
EXPECTED_WINDOW0_CURRENT_POINTER: Final = 0x8010EA20
EXPECTED_GAMESTATE_SHA256: Final = (
    "7edc0f58b93812efa0a9cd8843268de771992ed835852b458d43c34a579548e4"
)
GAMESTATE_SIZE: Final = 0x2358
FIELD_VARIABLE_BANK_SIZE: Final = 0x800
SOURCE_FIELD_VARIABLE_BANK_SHA256: Final = (
    "4aa3008b3cc716fb7426ac0d4bdd7787fc5957fd43f7c8b8e88cf802a26fd737"
)
EXPECTED_DIALOG_WINDOWS_SHA256: Final = (
    "8258f8ef949df740b04e7c8bd0d7af1f83669a97b1224b9394f8f1aa37fe771a"
)
READING_COMPLETE_BIT: Final = 8
SOURCE_PLAYABLE_STATE: Final = 1 << READING_COMPLETE_BIT
TARGET_PLAYABLE_STATE: Final = 0
PLAYABLE_STATE_RAM_OFFSET: Final = FIELD_SCRIPT_MEMORY + rico.PLAYABLE_STATE_VARIABLE
PLAYABLE_STATE_PAYLOAD_OFFSET: Final = SOURCE_RAM_OFFSET + PLAYABLE_STATE_RAM_OFFSET

EXPECTED_SCRIPT_CHANGED_BYTE_COUNT: Final = 75
EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT: Final = 10_715
EXPECTED_FAT_CHANGED_BYTE_COUNT: Final = 2
EXPECTED_PROGRESS_CHANGED_BYTE_COUNT: Final = 1
EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT: Final = 10_793
EXPECTED_OUTPUT_PAYLOAD_SHA256: Final = (
    "140cf5f7bcb604904bcd39400af10b99b212e706edf9ce0c7033abd41f5890ee"
)
EXPECTED_OUTPUT_RAM_SHA256: Final = (
    "4b8c539211adbec87a8288387f2cbd50b3632548e740ad4e6daec633b06b37fd"
)
EXPECTED_COMPRESSED_SIZE: Final = 1_373_053
EXPECTED_COMPRESSED_SHA256: Final = (
    "c6f856cc681d863624eff28bc413ae4e1f4dea932d0eca8a3fc569d1569d60b7"
)
EXPECTED_OUTPUT_SIZE: Final = 1_420_329
EXPECTED_OUTPUT_SHA256: Final = (
    "9e1d4e73a72797765a01410533bff5b76d9f95931265135bc4e2a85ab634893b"
)


class RicoEmeraldTravelerMigrationError(RuntimeError):
    """Raised before output whenever the pinned migration contract drifts."""


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
        raise RicoEmeraldTravelerMigrationError(
            f"Compared payload sizes differ: {len(before)} != {len(after)}"
        )
    return tuple(
        (offset, old, new)
        for offset, (old, new) in enumerate(zip(before, after, strict=True))
        if old != new
    )


def _dialogue_command(block_id: int) -> bytes:
    return b"\xF5" + struct.pack("<H", block_id)


def _validated_target_resources(
    new_disc: Path,
    target_bundle: Path = DEFAULT_TARGET_BUNDLE,
) -> tuple[bytes, bytes, bytes]:
    """Return the exact padded script, shorter dialogue, and target FAT."""

    if (
        not new_disc.is_file()
        or new_disc.stat().st_size != TARGET_DISC_SIZE
        or _file_sha256(new_disc) != TARGET_DISC_SHA256
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Final staged Rico Disc 1 identity changed"
        )
    if (
        not target_bundle.is_file()
        or target_bundle.stat().st_size != TARGET_HOUSE_FIELD_SIZE
        or _file_sha256(target_bundle) != TARGET_HOUSE_FIELD_SHA256
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Prepared canonical-2048 bundle identity changed"
        )

    image = Mode2Image(new_disc)
    entries = image.read_index()
    if HOUSE_FIELD_CANONICAL_ID >= len(entries):
        raise RicoEmeraldTravelerMigrationError(
            "Final staged Disc 1 lost canonical 2048"
        )
    entry = entries[HOUSE_FIELD_CANONICAL_ID]
    if (
        entry.kind != "file"
        or entry.sector != HOUSE_FIELD_SECTOR
        or entry.size != TARGET_HOUSE_FIELD_SIZE
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Final staged canonical-2048 FAT allocation changed"
        )
    raw = image.extract_entry(entry)
    prepared = target_bundle.read_bytes()
    if raw != prepared or _sha256(raw) != TARGET_HOUSE_FIELD_SHA256:
        raise RicoEmeraldTravelerMigrationError(
            "Final staged and prepared canonical-2048 bundles differ"
        )
    parsed = parse_field(raw)
    if len(parsed.parts) != 9:
        raise RicoEmeraldTravelerMigrationError(
            "Final staged canonical-2048 component count changed"
        )
    script = parsed.parts[SCRIPT_COMPONENT_INDEX].data
    dialogue = parsed.parts[DIALOGUE_COMPONENT_INDEX].data
    if (
        len(script) != RESIDENT_SCRIPT_SIZE
        or _sha256(script) != TARGET_RESIDENT_SCRIPT_SHA256
        or len(dialogue) != TARGET_DIALOGUE_SIZE
        or _sha256(dialogue) != TARGET_DIALOGUE_SHA256
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Final staged Chapter 1 components changed"
        )

    editor = AtelScript(script)
    reading_pc = editor.get_script_pointer(
        READING_CONTROLLER_ENTITY,
        READING_ACTION_SCRIPT,
    )
    next_pc = editor.get_script_pointer(NEXT_CONTROLLER_ENTITY, 0)
    reading_action = editor.bytecode[reading_pc:next_pc]
    if (
        editor.bytecode_offset != SCRIPT_BYTECODE_OFFSET
        or reading_pc != READING_ACTION_PC
        or next_pc != NEXT_CONTROLLER_INIT_PC
        or editor.get_script_pointer(NEXT_CONTROLLER_ENTITY, 1)
        != NEXT_CONTROLLER_UPDATE_PC
        or len(reading_action) != READING_ACTION_SIZE
        or reading_action[-READING_ACTION_TRAILING_STOP_BYTES:]
        != bytes(READING_ACTION_TRAILING_STOP_BYTES)
        or reading_action.count(_dialogue_command(TARGET_READING_REPEAT_DIALOGUE_ID))
        != 1
        or reading_action.count(_dialogue_command(TARGET_READING_FIRST_DIALOGUE_ID))
        != 1
        or any(
            _dialogue_command(block_id) in reading_action
            for block_id in SOURCE_READING_FIRST_DIALOGUE_IDS[1:]
        )
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Final staged padded reading-action topology changed"
        )

    blocks = _raw_dialogue_blocks(dialogue)
    if (
        len(blocks) != TARGET_DIALOGUE_BLOCK_COUNT
        or decode_text(blocks[SOURCE_WINDOW_DIALOGUE_ID].payload)
        != EXPECTED_TARGET_WINDOW_TEXT
        or decode_text(blocks[TARGET_READING_REPEAT_DIALOGUE_ID].payload)
        != EXPECTED_TARGET_READING_REPEAT_TEXT
        or decode_text(blocks[TARGET_READING_FIRST_DIALOGUE_ID].payload)
        != EXPECTED_TARGET_READING_FIRST_TEXT
        or "slat" in decode_text(blocks[SOURCE_WINDOW_DIALOGUE_ID].payload).casefold()
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Final staged window or Emerald Traveler dialogue changed"
        )

    table = _archive_table(new_disc)
    if (
        len(table) != ARCHIVE_TABLE_SIZE
        or _sha256(table) != TARGET_ARCHIVE_TABLE_SHA256
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Final staged Disc-1 archive table changed"
        )
    return script, dialogue, table


def migrate_state(
    state: bytes,
    *,
    zstd: _Zstd,
    new_disc: Path,
    target_bundle: Path = DEFAULT_TARGET_BUNDLE,
) -> tuple[bytes, dict[str, object]]:
    """Return the exact separate candidate and a byte-audit report."""

    state_hash = _sha256(state)
    if (len(state), state_hash) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise RicoEmeraldTravelerMigrationError(
            "Source Slot 1 identity changed: "
            f"{len(state)} bytes / {state_hash}; expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    if (
        len(state) < DUCKSTATION_STATE_HEADER_SIZE
        or state[:4] != DUCKSTATION_STATE_MAGIC
        or state.count(SOURCE_MEDIA_PATH) != 1
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Source is not the supported stable-path DuckStation state"
        )

    target_script, target_dialogue, target_table = _validated_target_resources(
        new_disc.resolve(),
        target_bundle.resolve(),
    )
    compression_type, compressed_size, payload_size, frame_offset = (
        struct.unpack_from(
            "<IIII",
            state,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
        )
    )
    if compression_type != DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise RicoEmeraldTravelerMigrationError(
            "Source state is not Zstandard-compressed"
        )
    if (
        compressed_size != SOURCE_COMPRESSED_SIZE
        or payload_size != SOURCE_PAYLOAD_SIZE
        or frame_offset != SOURCE_FRAME_OFFSET
        or frame_offset + compressed_size != len(state)
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Source DuckStation frame layout changed"
        )
    frame = state[frame_offset:]
    if not frame.startswith(ZSTD_MAGIC) or zstd.frame_size(frame) != compressed_size:
        raise RicoEmeraldTravelerMigrationError(
            "Source compressed frame identity is invalid"
        )

    source_payload = zstd.decompress(frame)
    if (
        len(source_payload) != SOURCE_PAYLOAD_SIZE
        or _sha256(source_payload) != SOURCE_PAYLOAD_SHA256
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Source decompressed payload identity changed"
        )
    ram_offset = _psx_ram_offset(source_payload)
    if ram_offset != SOURCE_RAM_OFFSET or ram_offset + RAM_SIZE > len(source_payload):
        raise RicoEmeraldTravelerMigrationError(
            "Source PSX RAM layout changed"
        )
    source_ram = source_payload[ram_offset : ram_offset + RAM_SIZE]
    if _sha256(source_ram) != SOURCE_RAM_SHA256:
        raise RicoEmeraldTravelerMigrationError("Source PSX RAM identity changed")

    script_start = RESIDENT_SCRIPT_PAYLOAD_OFFSET
    script_end = script_start + RESIDENT_SCRIPT_SIZE
    dialogue_start = RESIDENT_DIALOGUE_PAYLOAD_OFFSET
    source_dialogue_end = dialogue_start + SOURCE_RESIDENT_DIALOGUE_SIZE
    target_dialogue_end = dialogue_start + TARGET_DIALOGUE_SIZE
    alignment_end = source_dialogue_end + len(DIALOGUE_ALIGNMENT)
    allocator_header_end = alignment_end + len(NEXT_ALLOCATOR_HEADER)
    source_script = source_payload[script_start:script_end]
    source_dialogue = source_payload[dialogue_start:source_dialogue_end]
    if (
        _sha256(source_script) != SOURCE_RESIDENT_SCRIPT_SHA256
        or len(source_dialogue) != SOURCE_RESIDENT_DIALOGUE_SIZE
        or _sha256(source_dialogue) != SOURCE_RESIDENT_DIALOGUE_SHA256
        or len(_raw_dialogue_blocks(source_dialogue)) != SOURCE_DIALOGUE_BLOCK_COUNT
        or len(source_payload[script_end:dialogue_start])
        != SCRIPT_DIALOGUE_GAP_SIZE
        or _sha256(source_payload[script_end:dialogue_start])
        != SCRIPT_DIALOGUE_GAP_SHA256
        or source_payload[source_dialogue_end:alignment_end]
        != DIALOGUE_ALIGNMENT
        or source_payload[alignment_end:allocator_header_end]
        != NEXT_ALLOCATOR_HEADER
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Resident Chapter 1 component allocation changed"
        )

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
    playable_state = struct.unpack_from(
        "<H",
        source_ram,
        PLAYABLE_STATE_RAM_OFFSET,
    )[0]
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
        or playable_state != SOURCE_PLAYABLE_STATE
        or _sha256(source_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE])
        != EXPECTED_GAMESTATE_SHA256
        or _sha256(
            source_ram[
                FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE
            ]
        )
        != SOURCE_FIELD_VARIABLE_BANK_SHA256
        or _sha256(
            source_ram[
                DIALOG_WINDOWS : DIALOG_WINDOWS
                + DIALOG_WINDOW_STRIDE * DIALOG_WINDOW_COUNT
            ]
        )
        != EXPECTED_DIALOG_WINDOWS_SHA256
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Live field, closed-window, or first-use topology changed"
        )

    table_start = ARCHIVE_TABLE_PAYLOAD_OFFSET
    table_end = table_start + ARCHIVE_TABLE_SIZE
    source_table = source_payload[table_start:table_end]
    normalized_source_table = source_table[:-1] + target_table[-1:]
    if (
        len(source_table) != ARCHIVE_TABLE_SIZE
        or _sha256(source_table) != SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256
        or source_table[-1] != SOURCE_VOLATILE_ARCHIVE_BYTE
        or _sha256(normalized_source_table)
        != SOURCE_NORMALIZED_ARCHIVE_TABLE_SHA256
        or _differences(normalized_source_table, target_table)
        != ARCHIVE_TABLE_DIFFS
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Resident Disc-1 archive-table contract changed"
        )

    payload = bytearray(source_payload)
    payload[script_start:script_end] = target_script
    payload[dialogue_start:target_dialogue_end] = target_dialogue
    payload[target_dialogue_end:source_dialogue_end] = bytes(
        OBSOLETE_DIALOGUE_TAIL_SIZE
    )
    for relative_offset, old, new in ARCHIVE_TABLE_DIFFS:
        absolute_offset = table_start + relative_offset
        if payload[absolute_offset] != old:
            raise RicoEmeraldTravelerMigrationError(
                f"Resident FAT byte changed at payload 0x{absolute_offset:X}"
            )
        payload[absolute_offset] = new
    if struct.unpack_from("<H", payload, PLAYABLE_STATE_PAYLOAD_OFFSET)[0] != (
        SOURCE_PLAYABLE_STATE
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Reading-desk progress changed before migration"
        )
    struct.pack_into(
        "<H",
        payload,
        PLAYABLE_STATE_PAYLOAD_OFFSET,
        SOURCE_PLAYABLE_STATE & ~(1 << READING_COMPLETE_BIT),
    )

    final_payload = bytes(payload)
    final_ram = final_payload[ram_offset : ram_offset + RAM_SIZE]
    final_dialogue_span = final_payload[dialogue_start:source_dialogue_end]
    if (
        final_payload[script_start:script_end] != target_script
        or final_payload[dialogue_start:target_dialogue_end] != target_dialogue
        or final_payload[target_dialogue_end:source_dialogue_end]
        != bytes(OBSOLETE_DIALOGUE_TAIL_SIZE)
        or _sha256(final_dialogue_span)
        != TARGET_RESIDENT_DIALOGUE_SPAN_SHA256
        or final_payload[source_dialogue_end:alignment_end]
        != DIALOGUE_ALIGNMENT
        or final_payload[alignment_end:allocator_header_end]
        != NEXT_ALLOCATOR_HEADER
        or final_payload[script_end:dialogue_start]
        != source_payload[script_end:dialogue_start]
        or struct.unpack_from("<H", final_ram, PLAYABLE_STATE_RAM_OFFSET)[0]
        != TARGET_PLAYABLE_STATE
        or final_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE]
        != source_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE]
        or final_ram[
            DIALOG_WINDOWS : DIALOG_WINDOWS
            + DIALOG_WINDOW_STRIDE * DIALOG_WINDOW_COUNT
        ]
        != source_ram[
            DIALOG_WINDOWS : DIALOG_WINDOWS
            + DIALOG_WINDOW_STRIDE * DIALOG_WINDOW_COUNT
        ]
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Migrated component, allocator, or gameplay state is not exact"
        )

    final_table = final_payload[table_start:table_end]
    if (
        _sha256(final_table) != TARGET_RESIDENT_ARCHIVE_TABLE_SHA256
        or final_table[:-1] != target_table[:-1]
        or final_table[-1] != SOURCE_VOLATILE_ARCHIVE_BYTE
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Migrated resident Disc-1 archive table is not exact"
        )

    script_differences = _differences(source_script, target_script)
    target_dialogue_span = target_dialogue + bytes(OBSOLETE_DIALOGUE_TAIL_SIZE)
    dialogue_differences = _differences(source_dialogue, target_dialogue_span)
    progress_differences = _differences(
        source_payload[
            PLAYABLE_STATE_PAYLOAD_OFFSET : PLAYABLE_STATE_PAYLOAD_OFFSET + 2
        ],
        final_payload[
            PLAYABLE_STATE_PAYLOAD_OFFSET : PLAYABLE_STATE_PAYLOAD_OFFSET + 2
        ],
    )
    expected_changes = tuple(
        sorted(
            (
                *(
                    (script_start + offset, old, new)
                    for offset, old, new in script_differences
                ),
                *(
                    (dialogue_start + offset, old, new)
                    for offset, old, new in dialogue_differences
                ),
                *(
                    (table_start + offset, old, new)
                    for offset, old, new in ARCHIVE_TABLE_DIFFS
                ),
                *(
                    (PLAYABLE_STATE_PAYLOAD_OFFSET + offset, old, new)
                    for offset, old, new in progress_differences
                ),
            )
        )
    )
    actual_changes = _differences(source_payload, final_payload)
    if (
        len(script_differences) != EXPECTED_SCRIPT_CHANGED_BYTE_COUNT
        or len(dialogue_differences) != EXPECTED_DIALOGUE_CHANGED_BYTE_COUNT
        or len(progress_differences) != EXPECTED_PROGRESS_CHANGED_BYTE_COUNT
        or actual_changes != expected_changes
        or len(actual_changes) != EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT
        or _sha256(final_payload) != EXPECTED_OUTPUT_PAYLOAD_SHA256
        or _sha256(final_ram) != EXPECTED_OUTPUT_RAM_SHA256
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Migration byte whitelist or final payload identity changed"
        )

    compressed = zstd.compress(final_payload)
    if (
        len(compressed) != EXPECTED_COMPRESSED_SIZE
        or _sha256(compressed) != EXPECTED_COMPRESSED_SHA256
    ):
        raise RicoEmeraldTravelerMigrationError(
            "Migrated compressed frame identity changed"
        )
    prefix = bytearray(state[:frame_offset])
    struct.pack_into(
        "<I",
        prefix,
        DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        len(compressed),
    )
    result = bytes(prefix) + compressed
    result_hash = _sha256(result)
    if (
        zstd.decompress(result[frame_offset:]) != final_payload
        or len(result) != EXPECTED_OUTPUT_SIZE
        or result_hash != EXPECTED_OUTPUT_SHA256
    ):
        raise RicoEmeraldTravelerMigrationError(
            f"Candidate identity changed: {len(result)} / {result_hash}"
        )

    return result, {
        "source_state_sha256": state_hash,
        "output_state_sha256": result_hash,
        "source_payload_sha256": SOURCE_PAYLOAD_SHA256,
        "output_payload_sha256": EXPECTED_OUTPUT_PAYLOAD_SHA256,
        "payload_changed_byte_count": len(actual_changes),
        "resident_script_changed_byte_count": len(script_differences),
        "resident_dialogue_changed_byte_count": len(dialogue_differences),
        "dialogue_zeroed_tail_size": OBSOLETE_DIALOGUE_TAIL_SIZE,
        "resident_fat_changed_byte_count": len(ARCHIVE_TABLE_DIFFS),
        "progress_changed_byte_count": len(progress_differences),
        "reading_complete_bit_cleared": True,
        "first_use_narration_ready": True,
        "closed_dialogue_windows_preserved": True,
        "actor_vm_state_preserved": True,
        "game_state_preserved": True,
        "dialogue_allocation_relocated": False,
        "allocator_alignment_preserved": True,
        "allocator_header_preserved": True,
        "resident_fat_migrated": True,
        "media_path_rewrite_required": False,
        "target_field_canonical_id": HOUSE_FIELD_CANONICAL_ID,
        "target_field_size": TARGET_HOUSE_FIELD_SIZE,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--zstd", type=Path, default=DEFAULT_ZSTD)
    parser.add_argument("--new-disc", type=Path, default=DEFAULT_NEW_DISC)
    parser.add_argument(
        "--target-bundle",
        type=Path,
        default=DEFAULT_TARGET_BUNDLE,
    )
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = args.source.resolve()
    output = args.output.resolve()
    zstd_path = args.zstd.resolve()
    new_disc = args.new_disc.resolve()
    target_bundle = args.target_bundle.resolve()
    live_slot = LIVE_SLOT_ONE.resolve()
    if _aliases_existing_file(output, live_slot):
        raise SystemExit(
            "Output may not be DuckStation's live Slot 1 or an alias of it"
        )
    for protected, label in (
        (source, "source state"),
        (zstd_path, "zstd library"),
        (new_disc, "staged Disc 1"),
        (target_bundle, "prepared canonical-2048 bundle"),
    ):
        if _aliases_existing_file(output, protected):
            raise SystemExit(f"Output must be separate from the {label}")
    for path, label in (
        (source, "source state"),
        (zstd_path, "zstd library"),
        (new_disc, "final staged Rico Disc 1"),
        (target_bundle, "prepared canonical-2048 bundle"),
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
            target_bundle=target_bundle,
        )
    except RicoEmeraldTravelerMigrationError as exc:
        raise SystemExit(str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)
    if output.read_bytes() != result:
        raise SystemExit("Written candidate changed on disk")
    print(f"Wrote Emerald Traveler Slot 1 candidate: {output}")
    for key, value in report.items():
        print(f"{key}: {value}")
    print("The source and DuckStation's live Slot 1 were not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
