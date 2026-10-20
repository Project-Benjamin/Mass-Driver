#!/usr/bin/env python3
"""Migrate the audited Rico Slot 1 to the cleaned Chapter 1 night text.

The saved game is still inside the Chapter 1 house, while the edited deathbed
dialogue is played by the separate aftermath field loaded later.  The house's
resident copies of authored blocks 36 and 40 are dead data: neither is called
by the normal nor the save-state bridge script.  Repacking resident dialogue
would therefore add risk without affecting play.

This migration changes only the two Disc-1 FAT size bytes needed to load the
rebuilt house and aftermath resources.  It pins the exact source state, staged
disc, resource identities, script topology, and final candidate.  It always
writes a separate candidate and refuses DuckStation's live Slot 1.
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
from tools.xgdialog import decode_text  # noqa: E402
from tools.xgdisc import Mode2Image  # noqa: E402
from tools.xgfield import parse_field  # noqa: E402
from work.read_duckstation_runtime import (  # noqa: E402
    FIELD_ACTORS,
    FIELD_CUR_SCRIPT_FILE,
    FIELD_NUM_ACTORS,
    RAM_SIZE,
    _psx_ram_offset,
)


ROOT: Final = Path(__file__).resolve().parents[3]
LIVE_SLOT_ONE: Final = ROOT / "emulator_data" / "SLUS-00664_1.sav"
DEFAULT_ZSTD: Final = ROOT / "work" / "duckstation" / "zstd.dll"
DEFAULT_NEW_DISC: Final = (
    ROOT
    / "work"
    / "rico_night_cleanup_stage"
    / "Xenogears_Rico_Arc_Disc_1.bin"
)

SOURCE_STATE_SIZE: Final = 1_366_027
SOURCE_STATE_SHA256: Final = (
    "6493b88c6d69b060e624eea9847c1f567d3c530244605572a61c9d6b4267c117"
)
SOURCE_FRAME_OFFSET: Final = 0x6DD0
SOURCE_COMPRESSED_SIZE: Final = 1_337_915
SOURCE_PAYLOAD_SIZE: Final = 3_817_429
SOURCE_PAYLOAD_SHA256: Final = (
    "4e7bf019585d78adc8e40b4e5dba5f4bbc53fb719faffc1b4c36e5a9b7cb1721"
)
SOURCE_RAM_OFFSET: Final = 0x1A62
SOURCE_MEDIA_PATH: Final = (
    rb"C:\Users\Chad\Xenogears_Reimagined\output\rico_arc\Xenogears_Rico_Arc.m3u"
)
GAME_SCENE_MAP: Final = 0x04F34C

TARGET_DISC_SIZE: Final = 719_175_744
TARGET_DISC_SHA256: Final = (
    "bd2d08097df93be2c707d528e877b91d4f165b782197dbdb6be11c79e5a19a3e"
)
SCRIPT_COMPONENT_INDEX: Final = 5
DIALOGUE_COMPONENT_INDEX: Final = 7

HOUSE_FIELD_CANONICAL_ID: Final = 2048
HOUSE_FIELD_SECTOR: Final = 230_237
HOUSE_FIELD_SIZE: Final = 37_736
HOUSE_FIELD_SHA256: Final = (
    "d4f8f957bbfc809c00ea58eecc59965ec1691157cf7751504ded6375b9574a43"
)
HOUSE_SCRIPT_SIZE: Final = 5_426
HOUSE_SCRIPT_SHA256: Final = (
    "85e334efff6a70674d84615fde31be4fd5be8f60bd1eebdb46e7ebc2b9d20386"
)
HOUSE_DIALOGUE_SIZE: Final = 11_744
HOUSE_DIALOGUE_SHA256: Final = (
    "2d9d89bb4d3d65993cbfe0fcdc669f9fe01a765aff1710501d4b2fa3fda4de40"
)
HOUSE_DIALOGUE_BLOCK_COUNT: Final = 129
HOUSE_NIGHT_DIALOGUE_IDS: Final = (63, 67)

AFTERMATH_FIELD_CANONICAL_ID: Final = 1358
AFTERMATH_FIELD_SECTOR: Final = 179_507
AFTERMATH_FIELD_SIZE: Final = 30_508
AFTERMATH_FIELD_SHA256: Final = (
    "1bff977a2b236346e1a2b8d4a964e4b4f90b824fba8636756f90a5aeae7a3b77"
)
AFTERMATH_SCRIPT_SIZE: Final = 1_880
AFTERMATH_SCRIPT_SHA256: Final = (
    "33cc45d865b554b970ff8a39351eb80eed7ed01095e489e2e6fb72f49b43d4a1"
)
AFTERMATH_DIALOGUE_SIZE: Final = 931
AFTERMATH_DIALOGUE_SHA256: Final = (
    "022dfc2da236cd7514ea7864619252642f3ebbde8ab9ca0c6f5d2b0f127b6db0"
)
AFTERMATH_DIALOGUE_BLOCK_COUNT: Final = 10
AFTERMATH_NIGHT_DIALOGUE_IDS: Final = (5, 9)

EXPECTED_NIGHT_LINE: Final = (
    "Anne\nMy stubborn boy. You have\ndone everything I asked.<Close>"
)
EXPECTED_DAYLIGHT_LINE: Final = (
    "Daylight enters through the\nwindow.<New>Across the room, the watered\n"
    "stonebell turns its pale blue\nbells toward the light.<Close>"
)

RESIDENT_SCRIPT_PAYLOAD_OFFSET: Final = 0x10C822
RESIDENT_SCRIPT_SIZE: Final = 5_426
RESIDENT_SCRIPT_SHA256: Final = (
    "c61094be0baf53aa838f7c29871d963d0a1bc40c08888de099b12f81913dcc29"
)
RESIDENT_DIALOGUE_PAYLOAD_OFFSET: Final = 0x10DD9E
RESIDENT_DIALOGUE_SIZE: Final = 11_794
RESIDENT_DIALOGUE_SHA256: Final = (
    "059db2e7b0eac4474ce8af3f72afc97adcb4edf6a1f0906f3c1feed90142ec25"
)
RESIDENT_SCRIPT_GUEST_POINTER: Final = 0x8010ADC0
FATHER_BRIDGE_DIALOGUE_ID: Final = 57
OBSOLETE_FATHER_DIALOGUE_ID: Final = 128

ARCHIVE_TABLE_SIZE: Final = 0x8000
ARCHIVE_TABLE_PAYLOAD_OFFSET: Final = 0x11A66
SOURCE_ARCHIVE_TABLE_SHA256: Final = (
    "c6ef521cf9a471e45e725e9070537cb25102342662d25c1727df6a863bf908ea"
)
SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "28723dfa0f6422cf0308af5b919513609a9796d95a568f5c9690d7339621dd72"
)
SOURCE_VOLATILE_ARCHIVE_BYTE: Final = 0xC4
TARGET_ARCHIVE_TABLE_SHA256: Final = (
    "994e04db7df514ebf8230345fee269a1a910dd038a945223e8b3320d80eca3e9"
)
TARGET_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "e1a5436c56991c019c9ca70ad3274919d92aea8843558043690f0ac79a7e43be"
)
ARCHIVE_TABLE_DIFFS: Final = (
    (0x2525, 0x9C, 0x2C),  # FAT 1358: 30,620 -> 30,508
    (0x3803, 0x9C, 0x68),  # FAT 2048: 37,788 -> 37,736
)

EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT: Final = 2
EXPECTED_OUTPUT_PAYLOAD_SHA256: Final = (
    "2cf5e0514da75dd302dca90edb806e9e5f01618c4877c1c79f24a9e3089f815f"
)
EXPECTED_OUTPUT_SIZE: Final = 1_366_027
EXPECTED_OUTPUT_SHA256: Final = (
    "04557fa170e3d30667ce922dbe83f8261196dcb5f9d60003bb06614a273fe340"
)


class RicoNightDialogueMigrationError(RuntimeError):
    """Raised before output whenever the pinned migration contract drifts."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _aliases_existing_file(first: Path, second: Path) -> bool:
    """Return whether two resolved paths name the same existing file."""

    if first == second:
        return True
    try:
        return first.samefile(second)
    except (FileNotFoundError, OSError):
        return False


def _target_field(
    image: Mode2Image,
    entries: Sequence[object],
    *,
    canonical_id: int,
    sector: int,
    size: int,
    field_sha256: str,
) -> tuple[bytes, bytes]:
    if canonical_id >= len(entries):
        raise RicoNightDialogueMigrationError(
            f"Final staged Disc 1 is missing canonical {canonical_id}"
        )
    entry = entries[canonical_id]
    if (
        getattr(entry, "kind", None) != "file"
        or getattr(entry, "sector", None) != sector
        or getattr(entry, "size", None) != size
    ):
        raise RicoNightDialogueMigrationError(
            f"Final staged canonical {canonical_id} allocation changed"
        )
    raw = image.extract_entry(entry)
    if len(raw) != size or _sha256(raw) != field_sha256:
        raise RicoNightDialogueMigrationError(
            f"Final staged canonical {canonical_id} identity changed"
        )
    parsed = parse_field(raw)
    if len(parsed.parts) != 9:
        raise RicoNightDialogueMigrationError(
            f"Final staged canonical {canonical_id} component count changed"
        )
    return (
        parsed.parts[SCRIPT_COMPONENT_INDEX].data,
        parsed.parts[DIALOGUE_COMPONENT_INDEX].data,
    )


def _validated_target_resources(new_disc: Path) -> bytes:
    if (
        not new_disc.is_file()
        or new_disc.stat().st_size != TARGET_DISC_SIZE
        or _file_sha256(new_disc) != TARGET_DISC_SHA256
    ):
        raise RicoNightDialogueMigrationError(
            "Final staged Rico Disc 1 identity changed"
        )

    image = Mode2Image(new_disc)
    entries = image.read_index()
    house_script, house_dialogue = _target_field(
        image,
        entries,
        canonical_id=HOUSE_FIELD_CANONICAL_ID,
        sector=HOUSE_FIELD_SECTOR,
        size=HOUSE_FIELD_SIZE,
        field_sha256=HOUSE_FIELD_SHA256,
    )
    aftermath_script, aftermath_dialogue = _target_field(
        image,
        entries,
        canonical_id=AFTERMATH_FIELD_CANONICAL_ID,
        sector=AFTERMATH_FIELD_SECTOR,
        size=AFTERMATH_FIELD_SIZE,
        field_sha256=AFTERMATH_FIELD_SHA256,
    )
    if (
        (len(house_script), _sha256(house_script))
        != (HOUSE_SCRIPT_SIZE, HOUSE_SCRIPT_SHA256)
        or (len(house_dialogue), _sha256(house_dialogue))
        != (HOUSE_DIALOGUE_SIZE, HOUSE_DIALOGUE_SHA256)
        or (len(aftermath_script), _sha256(aftermath_script))
        != (AFTERMATH_SCRIPT_SIZE, AFTERMATH_SCRIPT_SHA256)
        or (len(aftermath_dialogue), _sha256(aftermath_dialogue))
        != (AFTERMATH_DIALOGUE_SIZE, AFTERMATH_DIALOGUE_SHA256)
    ):
        raise RicoNightDialogueMigrationError(
            "Final staged Chapter 1 component identity changed"
        )

    house_blocks = _raw_dialogue_blocks(house_dialogue)
    aftermath_blocks = _raw_dialogue_blocks(aftermath_dialogue)
    if (
        len(house_blocks) != HOUSE_DIALOGUE_BLOCK_COUNT
        or len(aftermath_blocks) != AFTERMATH_DIALOGUE_BLOCK_COUNT
        or decode_text(house_blocks[63].payload) != EXPECTED_NIGHT_LINE
        or decode_text(house_blocks[67].payload) != EXPECTED_DAYLIGHT_LINE
        or decode_text(aftermath_blocks[5].payload) != EXPECTED_NIGHT_LINE
        or decode_text(aftermath_blocks[9].payload) != EXPECTED_DAYLIGHT_LINE
    ):
        raise RicoNightDialogueMigrationError(
            "Final staged cleaned dialogue changed"
        )
    for block_id in HOUSE_NIGHT_DIALOGUE_IDS:
        if (
            house_script.count(_dialogue_command(block_id)) != 0
            or house_script.count(_choice_command(block_id)) != 0
        ):
            raise RicoNightDialogueMigrationError(
                "House unexpectedly calls its dead night-dialogue copies"
            )
    for block_id in AFTERMATH_NIGHT_DIALOGUE_IDS:
        if (
            aftermath_script.count(_dialogue_command(block_id)) != 1
            or aftermath_script.count(_choice_command(block_id)) != 1
        ):
            raise RicoNightDialogueMigrationError(
                "Aftermath night-dialogue call topology changed"
            )

    table = _archive_table(new_disc)
    if (
        len(table) != ARCHIVE_TABLE_SIZE
        or _sha256(table) != TARGET_ARCHIVE_TABLE_SHA256
    ):
        raise RicoNightDialogueMigrationError(
            "Final staged Disc-1 archive table identity changed"
        )
    return table


def migrate_state(
    state: bytes,
    *,
    zstd: _Zstd,
    new_disc: Path,
) -> tuple[bytes, dict[str, object]]:
    """Return the exact FAT-only candidate and its audit report."""

    state_hash = _sha256(state)
    if (len(state), state_hash) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise RicoNightDialogueMigrationError(
            "Source Slot 1 identity changed: "
            f"{len(state)} bytes / {state_hash}; expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    if (
        len(state) < DUCKSTATION_STATE_HEADER_SIZE
        or state[:4] != DUCKSTATION_STATE_MAGIC
        or state.count(SOURCE_MEDIA_PATH) != 1
    ):
        raise RicoNightDialogueMigrationError(
            "Source is not the supported stable-path DuckStation state"
        )
    target_table = _validated_target_resources(new_disc.resolve())

    compression_type, compressed_size, payload_size, frame_offset = (
        struct.unpack_from(
            "<IIII",
            state,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
        )
    )
    if compression_type != DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise RicoNightDialogueMigrationError(
            "Source payload is not Zstandard-compressed"
        )
    if (
        compressed_size != SOURCE_COMPRESSED_SIZE
        or payload_size != SOURCE_PAYLOAD_SIZE
        or frame_offset != SOURCE_FRAME_OFFSET
        or frame_offset + compressed_size != len(state)
    ):
        raise RicoNightDialogueMigrationError(
            "Source DuckStation frame layout changed"
        )
    frame = state[frame_offset:]
    if not frame.startswith(ZSTD_MAGIC) or zstd.frame_size(frame) != compressed_size:
        raise RicoNightDialogueMigrationError(
            "Source compressed frame identity is invalid"
        )
    source_payload = zstd.decompress(frame)
    if (
        len(source_payload) != SOURCE_PAYLOAD_SIZE
        or _sha256(source_payload) != SOURCE_PAYLOAD_SHA256
    ):
        raise RicoNightDialogueMigrationError(
            "Source decompressed payload identity changed"
        )

    script = source_payload[
        RESIDENT_SCRIPT_PAYLOAD_OFFSET :
        RESIDENT_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE
    ]
    dialogue = source_payload[
        RESIDENT_DIALOGUE_PAYLOAD_OFFSET :
        RESIDENT_DIALOGUE_PAYLOAD_OFFSET + RESIDENT_DIALOGUE_SIZE
    ]
    if (
        _sha256(script) != RESIDENT_SCRIPT_SHA256
        or _sha256(dialogue) != RESIDENT_DIALOGUE_SHA256
        or script.count(_dialogue_command(FATHER_BRIDGE_DIALOGUE_ID)) != 1
        or script.count(_choice_command(FATHER_BRIDGE_DIALOGUE_ID)) != 0
        or script.count(_dialogue_command(OBSOLETE_FATHER_DIALOGUE_ID)) != 0
        or script.count(_choice_command(OBSOLETE_FATHER_DIALOGUE_ID)) != 0
    ):
        raise RicoNightDialogueMigrationError(
            "Resident father bridge identity or topology changed"
        )
    for block_id in HOUSE_NIGHT_DIALOGUE_IDS:
        if (
            script.count(_dialogue_command(block_id)) != 0
            or script.count(_choice_command(block_id)) != 0
        ):
            raise RicoNightDialogueMigrationError(
                "Resident house script unexpectedly calls dead night dialogue"
            )

    ram_offset = _psx_ram_offset(source_payload)
    if ram_offset != SOURCE_RAM_OFFSET or ram_offset + RAM_SIZE > len(source_payload):
        raise RicoNightDialogueMigrationError("Source PSX RAM layout changed")
    ram = source_payload[ram_offset : ram_offset + RAM_SIZE]
    blocks = _raw_dialogue_blocks(dialogue)
    active = blocks[ACTIVE_DIALOGUE_ID]
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
    ):
        raise RicoNightDialogueMigrationError(
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
        raise RicoNightDialogueMigrationError(
            "Source/final resident Disc-1 FAT contract changed"
        )

    payload = bytearray(source_payload)
    for relative, old, new in ARCHIVE_TABLE_DIFFS:
        absolute = table_start + relative
        if payload[absolute] != old:
            raise RicoNightDialogueMigrationError(
                f"Resident FAT byte changed at payload 0x{absolute:X}"
            )
        payload[absolute] = new
    final_payload = bytes(payload)
    expected_changes = tuple(
        (table_start + relative, old, new)
        for relative, old, new in ARCHIVE_TABLE_DIFFS
    )
    if _differences(source_payload, final_payload) != expected_changes:
        raise RicoNightDialogueMigrationError(
            "Migration changed bytes outside the two-byte FAT whitelist"
        )
    final_table = final_payload[table_start:table_end]
    if (
        _sha256(final_table) != TARGET_RESIDENT_ARCHIVE_TABLE_SHA256
        or final_table[:-1] != target_table[:-1]
        or final_table[-1] != SOURCE_VOLATILE_ARCHIVE_BYTE
        or final_payload[
            RESIDENT_SCRIPT_PAYLOAD_OFFSET :
            RESIDENT_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE
        ]
        != script
        or final_payload[
            RESIDENT_DIALOGUE_PAYLOAD_OFFSET :
            RESIDENT_DIALOGUE_PAYLOAD_OFFSET + RESIDENT_DIALOGUE_SIZE
        ]
        != dialogue
    ):
        raise RicoNightDialogueMigrationError(
            "Migration changed resident scene data or installed the wrong FAT"
        )
    final_payload_hash = _sha256(final_payload)
    if final_payload_hash != EXPECTED_OUTPUT_PAYLOAD_SHA256:
        raise RicoNightDialogueMigrationError(
            "FAT-only output payload identity changed: " + final_payload_hash
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
        raise RicoNightDialogueMigrationError(
            "Candidate failed its Zstandard round trip"
        )
    result_hash = _sha256(result)
    if (
        len(result) != EXPECTED_OUTPUT_SIZE
        or result_hash != EXPECTED_OUTPUT_SHA256
    ):
        raise RicoNightDialogueMigrationError(
            "FAT-only candidate identity changed: "
            f"{len(result)} / {result_hash}"
        )

    return result, {
        "source_state_sha256": state_hash,
        "output_state_sha256": result_hash,
        "source_state_size": len(state),
        "output_state_size": len(result),
        "source_payload_sha256": SOURCE_PAYLOAD_SHA256,
        "output_payload_sha256": final_payload_hash,
        "payload_changed_byte_count": len(expected_changes),
        "resident_fat_changed_byte_count": len(ARCHIVE_TABLE_DIFFS),
        "resident_script_changed_byte_count": 0,
        "resident_dialogue_changed_byte_count": 0,
        "active_dialogue_id": ACTIVE_DIALOGUE_ID,
        "active_dialogue_window_preserved": True,
        "father_dialogue_bridge_preserved": True,
        "resident_dialogue_preserved": True,
        "aftermath_dialogue_loaded_from_media": True,
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
    live_slot = LIVE_SLOT_ONE.resolve()
    if _aliases_existing_file(output, live_slot):
        raise SystemExit(
            "Output may not be DuckStation's live Slot 1 or an alias of it"
        )
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
            source.read_bytes(),
            zstd=_Zstd(zstd_path),
            new_disc=new_disc,
        )
    except RicoNightDialogueMigrationError as exc:
        raise SystemExit(str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)
    if output.read_bytes() != result:
        raise SystemExit("Written candidate changed on disk")
    print(f"Wrote FAT-only night-dialogue candidate: {output}")
    for key, value in report.items():
        print(f"{key}: {value}")
    print("The source and DuckStation's live Slot 1 were not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
