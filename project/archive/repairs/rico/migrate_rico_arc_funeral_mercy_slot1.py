#!/usr/bin/env python3
"""Migrate audited Rico Slot 1 to the shortened Chapter 1 funeral ending.

The current state is inside the Chapter 1 house and carries a self-consistent
resident 129-block dialogue/script pair.  The edited funeral blocks are dead
in that house script, while the actual funeral is loaded later as an
independent field.  Repacking the resident pair would shift live custom IDs
and active pointers, so this successor deliberately preserves it byte-for-byte.

Only four Disc-1 FAT size bytes change: two for the newly packed funeral field
and two for the cold-load house resource.  Exact source, media, resource,
script-topology, changed-byte, and candidate identities are pinned.  The tool
always writes a separate candidate and refuses the live slot or input aliases.
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
    / "rico_funeral_mercy_stage"
    / "Xenogears_Rico_Arc_Disc_1.bin"
)

SOURCE_STATE_SIZE: Final = 1_366_027
SOURCE_STATE_SHA256: Final = (
    "04557fa170e3d30667ce922dbe83f8261196dcb5f9d60003bb06614a273fe340"
)
SOURCE_FRAME_OFFSET: Final = 0x6DD0
SOURCE_COMPRESSED_SIZE: Final = 1_337_915
SOURCE_PAYLOAD_SIZE: Final = 3_817_429
SOURCE_PAYLOAD_SHA256: Final = (
    "2cf5e0514da75dd302dca90edb806e9e5f01618c4877c1c79f24a9e3089f815f"
)
SOURCE_RAM_OFFSET: Final = 0x1A62
SOURCE_MEDIA_PATH: Final = (
    rb"C:\Users\Chad\Xenogears_Reimagined\output\rico_arc\Xenogears_Rico_Arc.m3u"
)
GAME_SCENE_MAP: Final = 0x04F34C

TARGET_DISC_SIZE: Final = 719_175_744
TARGET_DISC_SHA256: Final = (
    "52158e62be6fcfc0c8e90db7ef431b835690e18cd6b94a28e791357d2fc92117"
)
SCRIPT_COMPONENT_INDEX: Final = 5
DIALOGUE_COMPONENT_INDEX: Final = 7

HOUSE_FIELD_CANONICAL_ID: Final = 2048
HOUSE_FIELD_SECTOR: Final = 230_237
HOUSE_FIELD_SIZE: Final = 37_620
HOUSE_FIELD_SHA256: Final = (
    "f6dbfc165d4a04341a08ebb13e0b8d94cf65019463c9e064c5d809117730868e"
)
HOUSE_SCRIPT_SIZE: Final = 5_426
HOUSE_SCRIPT_SHA256: Final = (
    "f8c5fa31b2e5654a505df37c7405c8ce8b486860ef781033dbdef39a44d8145a"
)
HOUSE_DIALOGUE_SIZE: Final = 11_494
HOUSE_DIALOGUE_SHA256: Final = (
    "95fc624d90b31ec6467aceaf863e35f0c6495df1cfea7be21466c8ac3c18b7e2"
)
HOUSE_DIALOGUE_BLOCK_COUNT: Final = 128
HOUSE_FUNERAL_DIALOGUE_IDS: Final = (68, 69, 70, 71)

FUNERAL_FIELD_CANONICAL_ID: Final = 1362
FUNERAL_FIELD_SECTOR: Final = 179_821
FUNERAL_FIELD_SIZE: Final = 134_300
FUNERAL_FIELD_SHA256: Final = (
    "51eb526fc6f3f101a7b4a5d660ebecabe3791c2692d87da4985583fe32791239"
)
FUNERAL_SCRIPT_SIZE: Final = 16_456
FUNERAL_SCRIPT_SHA256: Final = (
    "3b1b8be2c9bb0b6710918de5410283261ef39057c77d80875849085d6726466d"
)
FUNERAL_DIALOGUE_SIZE: Final = 867
FUNERAL_DIALOGUE_SHA256: Final = (
    "f7dd44ab98ca17fadafb54676e8bcac875b27a6ec3b0941ae45f5da0ec8dcd0c"
)
FUNERAL_DIALOGUE_BLOCK_COUNT: Final = 6
EXPECTED_BLESSING: Final = (
    "The priest lowers his head\nand gives Rico a final,\nsilent blessing.<Close>"
)
EXPECTED_MERCY: Final = "<Rico>\nMercy...<Close>"
EXPECTED_CHAPTER_END: Final = "END OF CHAPTER 1<Close>"
RETIRED_FUNERAL_PHRASES: Final = (
    "holding his promise to anne close",
    "you taught me that mercy breaks the cycle of hate",
    "follow dad's path",
    "not make them suffer because i suffered",
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
RESIDENT_DIALOGUE_BLOCK_COUNT: Final = 129
RESIDENT_DEAD_FUNERAL_IDS: Final = (68, 69, 70, 71, 72)
FATHER_BRIDGE_DIALOGUE_ID: Final = 57
FATHER_FIRST_DIALOGUE_ID: Final = 127
OBSOLETE_FATHER_DIALOGUE_ID: Final = 128

ARCHIVE_TABLE_SIZE: Final = 0x8000
ARCHIVE_TABLE_PAYLOAD_OFFSET: Final = 0x11A66
SOURCE_ARCHIVE_TABLE_SHA256: Final = (
    "994e04db7df514ebf8230345fee269a1a910dd038a945223e8b3320d80eca3e9"
)
SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "e1a5436c56991c019c9ca70ad3274919d92aea8843558043690f0ac79a7e43be"
)
SOURCE_VOLATILE_ARCHIVE_BYTE: Final = 0xC4
TARGET_ARCHIVE_TABLE_SHA256: Final = (
    "4d63340269893ccd8ab4ffcc789faffb85f859346043855a6881b3630cc9d7bd"
)
TARGET_RESIDENT_ARCHIVE_TABLE_SHA256: Final = (
    "cc9d1f6e832e74c6c1efe4998b18fe17f98884fb945edeaa9505bfa1964d080c"
)
ARCHIVE_TABLE_DIFFS: Final = (
    (0x2541, 0x4C, 0x9C),  # FAT 1362 low: 134,476 -> 134,300
    (0x2542, 0x0D, 0x0C),  # FAT 1362 high
    (0x3803, 0x68, 0xF4),  # FAT 2048 low: 37,736 -> 37,620
    (0x3804, 0x93, 0x92),  # FAT 2048 high
)

EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT: Final = 4
EXPECTED_OUTPUT_PAYLOAD_SHA256: Final = (
    "2e1e4f1eeeeb0ad407bad8cf91ec5bb0b8a170eed16a625e5bc47f247d4b071c"
)
EXPECTED_OUTPUT_SIZE: Final = 1_366_026
EXPECTED_OUTPUT_SHA256: Final = (
    "a35acf06ace2c5c38fadfb1c30bf257eec09a53d63583f6b0d31fc826a87e211"
)


class RicoFuneralMercyMigrationError(RuntimeError):
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
        raise RicoFuneralMercyMigrationError(
            f"Final staged Disc 1 is missing canonical {canonical_id}"
        )
    entry = entries[canonical_id]
    if (
        getattr(entry, "kind", None) != "file"
        or getattr(entry, "sector", None) != sector
        or getattr(entry, "size", None) != size
    ):
        raise RicoFuneralMercyMigrationError(
            f"Final staged canonical {canonical_id} allocation changed"
        )
    raw = image.extract_entry(entry)
    if len(raw) != size or _sha256(raw) != field_sha256:
        raise RicoFuneralMercyMigrationError(
            f"Final staged canonical {canonical_id} identity changed"
        )
    parsed = parse_field(raw)
    if len(parsed.parts) != 9:
        raise RicoFuneralMercyMigrationError(
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
        raise RicoFuneralMercyMigrationError(
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
    funeral_script, funeral_dialogue = _target_field(
        image,
        entries,
        canonical_id=FUNERAL_FIELD_CANONICAL_ID,
        sector=FUNERAL_FIELD_SECTOR,
        size=FUNERAL_FIELD_SIZE,
        field_sha256=FUNERAL_FIELD_SHA256,
    )
    if (
        (len(house_script), _sha256(house_script))
        != (HOUSE_SCRIPT_SIZE, HOUSE_SCRIPT_SHA256)
        or (len(house_dialogue), _sha256(house_dialogue))
        != (HOUSE_DIALOGUE_SIZE, HOUSE_DIALOGUE_SHA256)
        or (len(funeral_script), _sha256(funeral_script))
        != (FUNERAL_SCRIPT_SIZE, FUNERAL_SCRIPT_SHA256)
        or (len(funeral_dialogue), _sha256(funeral_dialogue))
        != (FUNERAL_DIALOGUE_SIZE, FUNERAL_DIALOGUE_SHA256)
    ):
        raise RicoFuneralMercyMigrationError(
            "Final staged Chapter 1 component identity changed"
        )

    house_blocks = _raw_dialogue_blocks(house_dialogue)
    funeral_blocks = _raw_dialogue_blocks(funeral_dialogue)
    if (
        len(house_blocks) != HOUSE_DIALOGUE_BLOCK_COUNT
        or len(funeral_blocks) != FUNERAL_DIALOGUE_BLOCK_COUNT
        or decode_text(house_blocks[70].payload) != EXPECTED_BLESSING
        or decode_text(house_blocks[71].payload) != EXPECTED_MERCY
        or decode_text(funeral_blocks[2].payload) != EXPECTED_BLESSING
        or decode_text(funeral_blocks[3].payload) != EXPECTED_MERCY
        or decode_text(funeral_blocks[4].payload) != EXPECTED_CHAPTER_END
    ):
        raise RicoFuneralMercyMigrationError(
            "Final staged funeral closing sequence changed"
        )
    target_text = "\n".join(
        decode_text(block.payload) for block in funeral_blocks
    ).casefold()
    if any(phrase in target_text for phrase in RETIRED_FUNERAL_PHRASES):
        raise RicoFuneralMercyMigrationError(
            "Final staged funeral retained removed closing text"
        )
    for block_id in HOUSE_FUNERAL_DIALOGUE_IDS:
        if (
            house_script.count(_dialogue_command(block_id)) != 0
            or house_script.count(_choice_command(block_id)) != 0
        ):
            raise RicoFuneralMercyMigrationError(
                "House unexpectedly calls its dead funeral-dialogue copies"
            )
    # The funeral story itself presents setup/eulogy/blessing/Mercy/END once.
    for block_id in range(5):
        if funeral_script.count(_dialogue_command(block_id)) != 1:
            raise RicoFuneralMercyMigrationError(
                "Final staged funeral story call topology changed"
            )

    table = _archive_table(new_disc)
    if (
        len(table) != ARCHIVE_TABLE_SIZE
        or _sha256(table) != TARGET_ARCHIVE_TABLE_SHA256
    ):
        raise RicoFuneralMercyMigrationError(
            "Final staged Disc-1 archive table identity changed"
        )
    return table


def migrate_state(
    state: bytes,
    *,
    zstd: _Zstd,
    new_disc: Path,
) -> tuple[bytes, dict[str, object]]:
    """Return the exact four-byte FAT-only candidate and audit report."""

    state_hash = _sha256(state)
    if (len(state), state_hash) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise RicoFuneralMercyMigrationError(
            "Source Slot 1 identity changed: "
            f"{len(state)} bytes / {state_hash}; expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    if (
        len(state) < DUCKSTATION_STATE_HEADER_SIZE
        or state[:4] != DUCKSTATION_STATE_MAGIC
        or state.count(SOURCE_MEDIA_PATH) != 1
    ):
        raise RicoFuneralMercyMigrationError(
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
        raise RicoFuneralMercyMigrationError(
            "Source payload is not Zstandard-compressed"
        )
    if (
        compressed_size != SOURCE_COMPRESSED_SIZE
        or payload_size != SOURCE_PAYLOAD_SIZE
        or frame_offset != SOURCE_FRAME_OFFSET
        or frame_offset + compressed_size != len(state)
    ):
        raise RicoFuneralMercyMigrationError(
            "Source DuckStation frame layout changed"
        )
    frame = state[frame_offset:]
    if not frame.startswith(ZSTD_MAGIC) or zstd.frame_size(frame) != compressed_size:
        raise RicoFuneralMercyMigrationError(
            "Source compressed frame identity is invalid"
        )
    source_payload = zstd.decompress(frame)
    if (
        len(source_payload) != SOURCE_PAYLOAD_SIZE
        or _sha256(source_payload) != SOURCE_PAYLOAD_SHA256
    ):
        raise RicoFuneralMercyMigrationError(
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
    resident_blocks = _raw_dialogue_blocks(dialogue)
    if (
        _sha256(script) != RESIDENT_SCRIPT_SHA256
        or _sha256(dialogue) != RESIDENT_DIALOGUE_SHA256
        or len(resident_blocks) != RESIDENT_DIALOGUE_BLOCK_COUNT
        or script.count(_dialogue_command(FATHER_BRIDGE_DIALOGUE_ID)) != 1
        or script.count(_choice_command(FATHER_BRIDGE_DIALOGUE_ID)) != 0
        or script.count(_dialogue_command(FATHER_FIRST_DIALOGUE_ID)) != 1
        or script.count(_dialogue_command(OBSOLETE_FATHER_DIALOGUE_ID)) != 0
        or script.count(_choice_command(OBSOLETE_FATHER_DIALOGUE_ID)) != 0
    ):
        raise RicoFuneralMercyMigrationError(
            "Resident house/father bridge identity changed"
        )
    for block_id in RESIDENT_DEAD_FUNERAL_IDS:
        if (
            script.count(_dialogue_command(block_id)) != 0
            or script.count(_choice_command(block_id)) != 0
        ):
            raise RicoFuneralMercyMigrationError(
                "Resident house unexpectedly calls dead funeral dialogue"
            )

    ram_offset = _psx_ram_offset(source_payload)
    if ram_offset != SOURCE_RAM_OFFSET or ram_offset + RAM_SIZE > len(source_payload):
        raise RicoFuneralMercyMigrationError("Source PSX RAM layout changed")
    ram = source_payload[ram_offset : ram_offset + RAM_SIZE]
    active = resident_blocks[ACTIVE_DIALOGUE_ID]
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
        raise RicoFuneralMercyMigrationError(
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
        raise RicoFuneralMercyMigrationError(
            "Source/final resident Disc-1 FAT contract changed"
        )

    payload = bytearray(source_payload)
    for relative, old, new in ARCHIVE_TABLE_DIFFS:
        absolute = table_start + relative
        if payload[absolute] != old:
            raise RicoFuneralMercyMigrationError(
                f"Resident FAT byte changed at payload 0x{absolute:X}"
            )
        payload[absolute] = new
    final_payload = bytes(payload)
    expected_changes = tuple(
        (table_start + relative, old, new)
        for relative, old, new in ARCHIVE_TABLE_DIFFS
    )
    if _differences(source_payload, final_payload) != expected_changes:
        raise RicoFuneralMercyMigrationError(
            "Migration changed bytes outside the four-byte FAT whitelist"
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
        raise RicoFuneralMercyMigrationError(
            "Migration changed resident scene data or installed the wrong FAT"
        )
    final_payload_hash = _sha256(final_payload)
    if final_payload_hash != EXPECTED_OUTPUT_PAYLOAD_SHA256:
        raise RicoFuneralMercyMigrationError(
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
        raise RicoFuneralMercyMigrationError(
            "Candidate failed its Zstandard round trip"
        )
    result_hash = _sha256(result)
    if (
        len(result) != EXPECTED_OUTPUT_SIZE
        or result_hash != EXPECTED_OUTPUT_SHA256
    ):
        raise RicoFuneralMercyMigrationError(
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
        "resident_house_pair_preserved": True,
        "funeral_dialogue_loaded_from_media": True,
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
    except RicoFuneralMercyMigrationError as exc:
        raise SystemExit(str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)
    if output.read_bytes() != result:
        raise SystemExit("Written candidate changed on disk")
    print(f"Wrote FAT-only funeral-mercy candidate: {output}")
    for key, value in report.items():
        print(f"{key}: {value}")
    print("The source and DuckStation's live Slot 1 were not modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
