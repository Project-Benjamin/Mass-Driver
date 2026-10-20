#!/usr/bin/env python3
"""Migrate the exact V233 field-567 Slot 1 state to V234 safely.

V233 accidentally made both physical Circle and Cross satisfy the field
overlay's confirm/interaction tests.  Several authored ATEL actions also used
the reversed face-button constant, so Circle could dash and activate a nearby
action at the same time.  V234 restores the intended split: Cross (raw mask
0x0040) confirms/interacts, while Circle (raw mask 0x0020) remains dash/cancel.

An old save state serializes both the loaded field overlay and field-567's
allocator-safe resident script, so merely mounting the corrected disc is not
enough.  This helper validates and preserves the byte-identical V233/V234
resident archive table, then changes exactly five overlay immediates plus two
resident-script immediates.

The helper is deliberately fail-closed.  It accepts only the pinned V233
state/media and final V234 media, verifies an exact decompressed-byte
whitelist, writes only a separate candidate and JSON report, and refuses to
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
import tools.migrate_surface_soylent_v232_slot1_to_v233 as previous  # noqa: E402
from tools.xgdisc import Mode2Image  # noqa: E402
from work.read_duckstation_runtime import (  # noqa: E402
    FIELD_ACTORS,
    FIELD_CUR_SCRIPT_FILE,
    FIELD_NUM_ACTORS,
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
    / "save_candidates"
    / "SLUS-00669_1_v233_from_3f09a8ce_field567_empty_terminal_native_init.sav"
).resolve()

SOURCE_STATE_SIZE = 1_457_268
SOURCE_STATE_SHA256 = "b9b41cbc756300f6567a7c1cdc6b304e44bc57e025f1a4a51ff74aae84742acf"
SOURCE_PREFIX_SIZE = 52_816
SOURCE_PREFIX_SHA256 = "f5ab567793263a22faf42376d5349e5b18c320247532306f73e285c4f57dc315"
SOURCE_COMPRESSED_SIZE = 1_404_452
SOURCE_COMPRESSED_SHA256 = "b79a9c75dfc4163341d035afa4d4a88c5896494f0c95b8e5f17f4977bf4de0e6"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "805b6f3e2a57aba686f2ce21e1192f9746127843cb06dd5b6903f5ad042016a0"
EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
SOURCE_RAM_SHA256 = "976b6da70c96c9833e1ba6d548c3a3824977cdd9db26d91caae34dfec1f6dd51"

# These identities were frozen only after the final V234 disc and manifest
# completed their deterministic rebuild.
OUTPUT_STATE_SIZE: int | None = 1_457_268
OUTPUT_STATE_SHA256: str | None = "ccabae7cc2594e58bcf727fd3295aac65b11fd7853c3de5389cce1ec5756f263"
OUTPUT_PREFIX_SHA256: str | None = "10f9c7f08c8c705f5720cd328bc2b47b2912d838361497d4adfc678c043a7d13"
OUTPUT_COMPRESSED_SIZE: int | None = 1_404_452
OUTPUT_COMPRESSED_SHA256: str | None = "d6435aef68dc426441db285d550a406dd849759a988c944a3537ba0abcc44aba"
OUTPUT_PAYLOAD_SHA256: str | None = "3e4e4e2ed307556eb346ab709ed979b240761dc0eb1bbd81e8ee6af51ac30771"
OUTPUT_RAM_SHA256: str | None = "2c9a1676c974dfbfe544827e3cdac4450fb51b5f7d7279e61294cc8a82eea76e"
OUTPUT_REPORT_SIZE: int | None = 2_490
OUTPUT_REPORT_SHA256: str | None = "39787ab708904fe6fa76973f1d721791ffcab07a2852aaf8daabf803abde2515"

OLD_DISC_SIZE = 698_816_832
OLD_DISC_SHA256 = "f50fa064e8d466bde46e0946a4c1ea7dc556a6a94d85f4632de201934318a72b"
NEW_DISC_SIZE: int | None = 698_816_832
NEW_DISC_SHA256: str | None = "86ad52f30bfa1790adc451f68cf38977108c090cac715799de4ef970b9159b72"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v233.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v234.cue"
OLD_CUE_SIZE = 112
OLD_CUE_SHA256 = "106149772cdd6b12a460be98858e59d268fb1e01008d12b81f3eda80dd04ca28"
NEW_CUE_SIZE: int | None = 112
NEW_CUE_SHA256: str | None = "49d9b03f240fa747c7bc10faba7de0730037c62685f55d93b8d4d4f0ea4e088c"

OLD_MANIFEST_SIZE = 136_361
OLD_MANIFEST_SHA256 = "b79d7a866ba29ad9a5f488bf6e004310f5a5a2c32ed73aaf676eee3154ac4d1a"
NEW_MANIFEST_SIZE: int | None = 136_361
NEW_MANIFEST_SHA256: str | None = "4df5b690883612d40c2fa9efa45ae0ae888082972be500c163439e3dad93e12d"
CHANGED_RESOURCE_IDS: tuple[int, ...] | None = (
    1704, 1706, 1736, 1740, 1782, 1786, 1788, 1790, 1792,
    1794, 1846, 1848, 1850, 1852, 1854, 1856, 1858,
)

FIELD_OVERLAY_CANONICAL_ID = 36
WORLDMAP_OVERLAY_CANONICAL_ID = 37
OLD_FIELD_OVERLAY_SIZE = NEW_FIELD_OVERLAY_SIZE = 293_476
OLD_FIELD_OVERLAY_SHA256 = "5f39eac91cf360bf459ad7c7f484213a915e057a3c9bc2ad74c91c452964a0c4"
NEW_FIELD_OVERLAY_SHA256 = "56ed679c9bff2cfe6292e29add3bf04dcaba8f36aba65aa27347105d6e8469f1"
OLD_WORLDMAP_OVERLAY_SIZE = NEW_WORLDMAP_OVERLAY_SIZE = 93_360
OLD_WORLDMAP_OVERLAY_SHA256 = "94ccdb23e021939fab22b8f71586ced257413f2ed9ba2723e74f5e34ee606110"
NEW_WORLDMAP_OVERLAY_SHA256 = "575a4303eccd2ec2c6a12e7c778c18d5d9e631cc3c760ebf8a5cfde53680eb9e"

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = "aabe75ccb44040ab908fe90b649c1af84f28df4cd01f3098e3db4ff611fd318d"
NEW_ARCHIVE_TABLE_SHA256: str | None = "aabe75ccb44040ab908fe90b649c1af84f28df4cd01f3098e3db4ff611fd318d"
ARCHIVE_TABLE_DIFFS: tuple[tuple[int, int, int], ...] | None = ()
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
SOURCE_RESIDENT_TABLE_SHA256 = "0e44380e3f69290b581d40209a0161e2a50defb7ab5d37323fdde4c0c00e97a2"
OUTPUT_RESIDENT_TABLE_SHA256: str | None = "0e44380e3f69290b581d40209a0161e2a50defb7ab5d37323fdde4c0c00e97a2"
EXPECTED_VOLATILE_TABLE_VALUE = 0xE0

# The decoded field overlay is loaded at 0x8006FAF0.  Its final 0x0FCE bytes
# are writable data/BSS and legitimately differ from the media image, so the
# complete runtime span and its immutable 0x3E000-byte code prefix are pinned
# separately before changing the five exact MIPS immediates.
FIELD_OVERLAY_RAM_OFFSET = 0x06FAF0
FIELD_OVERLAY_RUNTIME_SIZE = 260_862
FIELD_OVERLAY_CODE_SIZE = 0x3E000
SOURCE_FIELD_OVERLAY_RUNTIME_SHA256 = "c741170c094515384b3dee86196b0de3d01072f1fcb458594727da58042fa232"
SOURCE_FIELD_OVERLAY_CODE_SHA256 = "40a0288df04e09738633419c48dc885b6fdd0db49315bda973f0f9fd93090883"
OUTPUT_FIELD_OVERLAY_RUNTIME_SHA256 = "42f87fe8e38744d15b75415d5c352f8c2e12d2eadd8d3e9d87a9c8671ee613bc"
OUTPUT_FIELD_OVERLAY_CODE_SHA256 = "8a16b745de4199af131191e8f7ce71c4746c53b94019a03e6af0bcc0c6e1d065"
FIELD_OVERLAY_MASK_OFFSETS = (0x106F8, 0x108AC, 0x13FC8, 0x14184, 0x14458)
OLD_OVERLAY_MASK_INSTRUCTION = bytes.fromhex("60 00 42 30")
NEW_OVERLAY_MASK_INSTRUCTION = bytes.fromhex("40 00 42 30")

# V233's allocator-safe compatibility script is smaller than the normal media
# script and must stay in place until a field reload.  Only its two opcode-31
# mask operands change.
RESIDENT_SCRIPT_RAM_OFFSET = 0x10B2F4
RESIDENT_SCRIPT_SIZE = 3_213
SOURCE_RESIDENT_SCRIPT_SHA256 = "65077c3176cf791bf9b5c4adb7fc3b11fa37b741d3b34a1613c4f42eacef8b82"
OUTPUT_RESIDENT_SCRIPT_SHA256 = "4cffe36da49f20d559a6d4a1552a2895bf7e5ee5853c751062ffd428d5053409"
RESIDENT_ACTION_RAM_OFFSET = 0x10BE35
OLD_RESIDENT_ACTION = bytes.fromhex(
    "33 FE 54 31 20 00 CB 05 26 01 80 01 C0 05 26 01 80 "
    "F5 2D 00 01 9C 31 20 00 DE 05 26 01 80 01 D3 05 "
    "26 01 80 FE 53 00"
)
NEW_RESIDENT_ACTION = bytes.fromhex(
    "33 FE 54 31 40 00 CB 05 26 01 80 01 C0 05 26 01 80 "
    "F5 2D 00 01 9C 31 40 00 DE 05 26 01 80 01 D3 05 "
    "26 01 80 FE 53 00"
)
OLD_RESIDENT_ACTION_SHA256 = "7d3c593800d9042fcc83489b0efb1cf5e9d5b047117c1ae9b8ca4140add45d9e"
NEW_RESIDENT_ACTION_SHA256 = "c65c452f4b0b2be7fc306fa3c178d07d0e27b68d46ceea9808f0614c236dac51"
RESIDENT_ACTION_MASK_OFFSETS = (4, 23)

EXPECTED_FIELD = 567
EXPECTED_ACTOR_COUNT = 34
EXPECTED_ACTOR_ARRAY_GUEST_POINTER = 0x80112BD8
EXPECTED_VM_SCRIPT_GUEST_POINTER = 0x8010B878
EXPECTED_VM_ACTOR_GUEST_POINTER = 0x80115944
EXPECTED_CONTROL_BYTES_CHANGED = 7
CONTROL_DIFF_SHA256 = "638b747117cb8d105d90c38f09e13d8226aff7bb3492758b2d8d40087e939689"
EXPECTED_PAYLOAD_BYTES_CHANGED: int | None = 7
PAYLOAD_DIFF_SHA256: str | None = "638b747117cb8d105d90c38f09e13d8226aff7bb3492758b2d8d40087e939689"
EXPECTED_PREFIX_BYTES_CHANGED: int | None = 1

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


def _unpack_state(state: bytes, zstd: _ZstdLike) -> tuple[bytes, int, bytes]:
    return previous._unpack_state(state, zstd)


def _pack_state(prefix: bytes, payload: bytes, zstd: _ZstdLike) -> bytes:
    return previous._pack_state(prefix, payload, zstd)


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


def _validate_file(path: Path, size: int, sha256: str, label: str) -> None:
    if not path.is_file() or path.stat().st_size != size or _file_sha256(path) != sha256:
        raise SurfaceSlotMigrationError(f"{label} identity drifted")


def _manifest_inventory(blob: bytes, *, size: int, sha256: str, label: str) -> dict[int, tuple[int, str]]:
    if (len(blob), _sha256(blob)) != (size, sha256):
        raise SurfaceSlotMigrationError(f"{label} identity drifted")
    try:
        document = json.loads(blob)
        if document.get("format") != "xenogears-surface-soylent-campaign-v1":
            raise ValueError("unexpected format")
        return {
            int(item["canonical_id"]): (int(item["size"]), str(item["sha256"]))
            for item in document["replacement_inventory"]
        }
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise SurfaceSlotMigrationError(f"{label} structure drifted") from exc


def _disc_resource(image: Mode2Image, canonical_id: int, size: int, sha256: str, label: str) -> bytes:
    entries = image.read_index()
    index = canonical_id - 5
    if index < 0 or index >= len(entries) or entries[index].canonical_disc2_index != canonical_id:
        raise SurfaceSlotMigrationError(f"{label} FAT entry is missing")
    data = image.extract_entry(entries[index])
    if (len(data), _sha256(data)) != (size, sha256):
        raise SurfaceSlotMigrationError(f"{label} identity drifted")
    return data


def _require_target_pins() -> None:
    pins = {
        "output state size": OUTPUT_STATE_SIZE,
        "output state hash": OUTPUT_STATE_SHA256,
        "output prefix hash": OUTPUT_PREFIX_SHA256,
        "output compressed size": OUTPUT_COMPRESSED_SIZE,
        "output compressed hash": OUTPUT_COMPRESSED_SHA256,
        "output payload hash": OUTPUT_PAYLOAD_SHA256,
        "output RAM hash": OUTPUT_RAM_SHA256,
        "output report size": OUTPUT_REPORT_SIZE,
        "output report hash": OUTPUT_REPORT_SHA256,
        "V234 disc size": NEW_DISC_SIZE,
        "V234 disc hash": NEW_DISC_SHA256,
        "V234 CUE size": NEW_CUE_SIZE,
        "V234 CUE hash": NEW_CUE_SHA256,
        "V234 manifest size": NEW_MANIFEST_SIZE,
        "V234 manifest hash": NEW_MANIFEST_SHA256,
        "changed resource IDs": CHANGED_RESOURCE_IDS,
        "V234 archive-table hash": NEW_ARCHIVE_TABLE_SHA256,
        "V234 resident-table hash": OUTPUT_RESIDENT_TABLE_SHA256,
        "payload byte count": EXPECTED_PAYLOAD_BYTES_CHANGED,
        "payload diff hash": PAYLOAD_DIFF_SHA256,
        "prefix byte count": EXPECTED_PREFIX_BYTES_CHANGED,
    }
    missing = [label for label, value in pins.items() if value is None]
    if missing:
        raise SurfaceSlotMigrationError(
            "Final V234 identities are not pinned: " + ", ".join(missing)
        )


def _validate_media(
    old_disc: Path,
    new_disc: Path,
    old_manifest: bytes,
    new_manifest: bytes,
) -> tuple[bytes, bytes]:
    _require_target_pins()
    assert NEW_DISC_SIZE is not None and NEW_DISC_SHA256 is not None
    assert NEW_CUE_SIZE is not None and NEW_CUE_SHA256 is not None
    assert NEW_MANIFEST_SIZE is not None and NEW_MANIFEST_SHA256 is not None
    assert CHANGED_RESOURCE_IDS is not None
    assert NEW_ARCHIVE_TABLE_SHA256 is not None
    for path, size, sha256, label in (
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V233 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V234 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V233 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V234 CUE"),
    ):
        _validate_file(path, size, sha256, label)
    old_inventory = _manifest_inventory(
        old_manifest, size=OLD_MANIFEST_SIZE, sha256=OLD_MANIFEST_SHA256, label="V233 manifest"
    )
    new_inventory = _manifest_inventory(
        new_manifest, size=NEW_MANIFEST_SIZE, sha256=NEW_MANIFEST_SHA256, label="V234 manifest"
    )
    changed = tuple(
        resource_id
        for resource_id in sorted(set(old_inventory) | set(new_inventory))
        if old_inventory.get(resource_id) != new_inventory.get(resource_id)
    )
    if changed != CHANGED_RESOURCE_IDS:
        raise SurfaceSlotMigrationError("V233/V234 manifest delta drifted")

    old_image, new_image = Mode2Image(old_disc), Mode2Image(new_disc)
    _disc_resource(
        old_image, FIELD_OVERLAY_CANONICAL_ID, OLD_FIELD_OVERLAY_SIZE,
        OLD_FIELD_OVERLAY_SHA256, "V233 field overlay",
    )
    _disc_resource(
        new_image, FIELD_OVERLAY_CANONICAL_ID, NEW_FIELD_OVERLAY_SIZE,
        NEW_FIELD_OVERLAY_SHA256, "V234 field overlay",
    )
    _disc_resource(
        old_image, WORLDMAP_OVERLAY_CANONICAL_ID, OLD_WORLDMAP_OVERLAY_SIZE,
        OLD_WORLDMAP_OVERLAY_SHA256, "V233 world-map overlay",
    )
    _disc_resource(
        new_image, WORLDMAP_OVERLAY_CANONICAL_ID, NEW_WORLDMAP_OVERLAY_SIZE,
        NEW_WORLDMAP_OVERLAY_SHA256, "V234 world-map overlay",
    )
    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    if (
        (len(old_table), len(new_table)) != (ARCHIVE_TABLE_SIZE, ARCHIVE_TABLE_SIZE)
        or _sha256(old_table) != OLD_ARCHIVE_TABLE_SHA256
        or _sha256(new_table) != NEW_ARCHIVE_TABLE_SHA256
        or _diff_triplets(old_table, new_table) != ARCHIVE_TABLE_DIFFS
    ):
        raise SurfaceSlotMigrationError("V233/V234 archive-table delta drifted")
    return old_table, new_table


def _validate_source_payload(payload: bytes, old_table: bytes) -> tuple[int, bytes]:
    if (len(payload), _sha256(payload)) != (SOURCE_PAYLOAD_SIZE, SOURCE_PAYLOAD_SHA256):
        raise SurfaceSlotMigrationError("Pinned V233 payload identity drifted")
    ram_offset, ram = _ram_from_payload(payload)
    if _sha256(ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("Pinned V233 RAM identity drifted")
    if (
        struct.unpack_from("<I", ram, previous.GAME_SCENE_MAP)[0] != EXPECTED_FIELD
        or struct.unpack_from("<I", ram, FIELD_NUM_ACTORS)[0] != EXPECTED_ACTOR_COUNT
        or struct.unpack_from("<I", ram, FIELD_ACTORS)[0] != EXPECTED_ACTOR_ARRAY_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0]
        != (RESIDENT_SCRIPT_RAM_OFFSET | 0x80000000)
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA)[0] != EXPECTED_VM_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_ACTOR)[0] != EXPECTED_VM_ACTOR_GUEST_POINTER
    ):
        raise SurfaceSlotMigrationError("Pinned field-567 runtime pointers drifted")

    table_offset, volatile = media_migration._find_resident_archive_table(payload, old_table)
    resident_table = payload[table_offset : table_offset + ARCHIVE_TABLE_SIZE]
    if (
        table_offset != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or volatile != 1
        or resident_table[-1] != EXPECTED_VOLATILE_TABLE_VALUE
        or _sha256(resident_table) != SOURCE_RESIDENT_TABLE_SHA256
        or resident_table[:-1] != old_table[:-1]
    ):
        raise SurfaceSlotMigrationError("Resident V233 archive table drifted")

    overlay = ram[
        FIELD_OVERLAY_RAM_OFFSET : FIELD_OVERLAY_RAM_OFFSET + FIELD_OVERLAY_RUNTIME_SIZE
    ]
    if (
        _sha256(overlay) != SOURCE_FIELD_OVERLAY_RUNTIME_SHA256
        or _sha256(overlay[:FIELD_OVERLAY_CODE_SIZE]) != SOURCE_FIELD_OVERLAY_CODE_SHA256
    ):
        raise SurfaceSlotMigrationError("Resident V233 field overlay drifted")
    for offset in FIELD_OVERLAY_MASK_OFFSETS:
        if overlay[offset : offset + 4] != OLD_OVERLAY_MASK_INSTRUCTION:
            raise SurfaceSlotMigrationError(
                f"Resident field-overlay mask drifted at 0x{offset:05X}"
            )

    script = ram[
        RESIDENT_SCRIPT_RAM_OFFSET : RESIDENT_SCRIPT_RAM_OFFSET + RESIDENT_SCRIPT_SIZE
    ]
    action_relative = RESIDENT_ACTION_RAM_OFFSET - RESIDENT_SCRIPT_RAM_OFFSET
    if (
        _sha256(script) != SOURCE_RESIDENT_SCRIPT_SHA256
        or script[action_relative : action_relative + len(OLD_RESIDENT_ACTION)]
        != OLD_RESIDENT_ACTION
        or _sha256(OLD_RESIDENT_ACTION) != OLD_RESIDENT_ACTION_SHA256
    ):
        raise SurfaceSlotMigrationError("Resident V233 field-567 script drifted")
    runtime_pcs = previous._runtime_pc_snapshot(
        ram, EXPECTED_ACTOR_ARRAY_GUEST_POINTER & 0x1FFFFFFF
    )
    if (
        previous._runtime_pc_digest(runtime_pcs) != previous.TARGET_RUNTIME_PC_SHA256
        or previous._runtime_pc_hits(
            runtime_pcs,
            previous.COMPAT_ACTION_PC,
            previous.RETIRED_ACTION_END_PC,
        )
    ):
        raise SurfaceSlotMigrationError("A field script PC enters the resident action span")
    return ram_offset, ram


def _patch_resident_controls(payload: bytes, old_table: bytes, new_table: bytes) -> tuple[bytes, dict[str, object]]:
    """Return the exact decompressed V234 payload and its patch audit."""

    ram_offset, source_ram = _validate_source_payload(payload, old_table)
    final = bytearray(payload)

    resident_table = bytearray(new_table)
    resident_table[-1] = EXPECTED_VOLATILE_TABLE_VALUE
    if OUTPUT_RESIDENT_TABLE_SHA256 is not None and _sha256(resident_table) != OUTPUT_RESIDENT_TABLE_SHA256:
        raise SurfaceSlotMigrationError("V234 resident archive-table reconstruction drifted")
    final[
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
    ] = resident_table

    overlay_payload = ram_offset + FIELD_OVERLAY_RAM_OFFSET
    for offset in FIELD_OVERLAY_MASK_OFFSETS:
        absolute = overlay_payload + offset
        if final[absolute : absolute + 4] != OLD_OVERLAY_MASK_INSTRUCTION:
            raise SurfaceSlotMigrationError(
                f"Resident overlay patch source drifted at 0x{offset:05X}"
            )
        final[absolute : absolute + 4] = NEW_OVERLAY_MASK_INSTRUCTION

    action_payload = ram_offset + RESIDENT_ACTION_RAM_OFFSET
    if final[action_payload : action_payload + len(OLD_RESIDENT_ACTION)] != OLD_RESIDENT_ACTION:
        raise SurfaceSlotMigrationError("Resident action patch source drifted")
    final[action_payload : action_payload + len(NEW_RESIDENT_ACTION)] = NEW_RESIDENT_ACTION
    final_payload = bytes(final)

    _result_ram_offset, result_ram = _ram_from_payload(final_payload)
    target_overlay = result_ram[
        FIELD_OVERLAY_RAM_OFFSET : FIELD_OVERLAY_RAM_OFFSET + FIELD_OVERLAY_RUNTIME_SIZE
    ]
    target_script = result_ram[
        RESIDENT_SCRIPT_RAM_OFFSET : RESIDENT_SCRIPT_RAM_OFFSET + RESIDENT_SCRIPT_SIZE
    ]
    target_action = result_ram[
        RESIDENT_ACTION_RAM_OFFSET : RESIDENT_ACTION_RAM_OFFSET + len(NEW_RESIDENT_ACTION)
    ]
    if (
        _sha256(target_overlay) != OUTPUT_FIELD_OVERLAY_RUNTIME_SHA256
        or _sha256(target_overlay[:FIELD_OVERLAY_CODE_SIZE]) != OUTPUT_FIELD_OVERLAY_CODE_SHA256
        or _sha256(target_script) != OUTPUT_RESIDENT_SCRIPT_SHA256
        or target_action != NEW_RESIDENT_ACTION
        or _sha256(target_action) != NEW_RESIDENT_ACTION_SHA256
    ):
        raise SurfaceSlotMigrationError("Cross-only resident reconstruction drifted")

    table_diffs = _diff_triplets(
        payload[
            EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
            EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
        ],
        resident_table,
    )
    control_offsets = {
        *(overlay_payload + offset for offset in FIELD_OVERLAY_MASK_OFFSETS),
        *(action_payload + offset for offset in RESIDENT_ACTION_MASK_OFFSETS),
    }
    control_diffs = tuple(
        diff for diff in _diff_triplets(payload, final_payload) if diff[0] in control_offsets
    )
    actual_diffs = _diff_triplets(payload, final_payload)
    expected_offsets = {
        *(EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + offset for offset, _old, _new in table_diffs),
        *control_offsets,
    }
    if (
        len(control_diffs) != EXPECTED_CONTROL_BYTES_CHANGED
        or _triplet_digest(control_diffs) != CONTROL_DIFF_SHA256
        or {offset for offset, _old, _new in actual_diffs} != expected_offsets
        or (
            EXPECTED_PAYLOAD_BYTES_CHANGED is not None
            and len(actual_diffs) != EXPECTED_PAYLOAD_BYTES_CHANGED
        )
        or (PAYLOAD_DIFF_SHA256 is not None and _triplet_digest(actual_diffs) != PAYLOAD_DIFF_SHA256)
        or (OUTPUT_PAYLOAD_SHA256 is not None and _sha256(final_payload) != OUTPUT_PAYLOAD_SHA256)
        or (OUTPUT_RAM_SHA256 is not None and _sha256(result_ram) != OUTPUT_RAM_SHA256)
    ):
        raise SurfaceSlotMigrationError("Migration escaped the exact payload whitelist")

    # Every byte outside the archive table and the seven mask operands remains
    # byte-identical, including Fei, party/GameState, field variables, camera,
    # actors, dialogue windows, and the writable portion of the overlay.
    return final_payload, {
        "archive_table_bytes_changed": len(table_diffs),
        "control_bytes_changed": len(control_diffs),
        "payload_bytes_changed": len(actual_diffs),
        "payload_diff_triplet_sha256": _triplet_digest(actual_diffs),
        "resident_archive_table_sha256": _sha256(resident_table),
        "resident_field_overlay_sha256": _sha256(target_overlay),
        "resident_script_sha256": _sha256(target_script),
    }


def _expected_prefix(source_prefix: bytes, *, compressed_size: int) -> bytes:
    old_name, new_name = OLD_CUE_NAME.encode("ascii"), NEW_CUE_NAME.encode("ascii")
    if (
        len(old_name) != len(new_name)
        or source_prefix.count(old_name) != 1
        or source_prefix.count(new_name)
    ):
        raise SurfaceSlotMigrationError("Pinned V233 media path changed")
    expected = bytearray(source_prefix.replace(old_name, new_name))
    struct.pack_into(
        "<I", expected, media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET, compressed_size
    )
    return bytes(expected)


def migrate_v233_slot1_to_v234(
    state: bytes,
    *,
    old_disc: Path,
    new_disc: Path,
    old_manifest: bytes,
    new_manifest: bytes,
    zstd: _ZstdLike,
) -> tuple[bytes, dict[str, object]]:
    """Return the separately writable, fully validated V234 candidate."""

    _require_target_pins()
    source_sha256 = _sha256(state)
    if (len(state), source_sha256) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise SurfaceSlotMigrationError(
            f"Source Slot 1 is {len(state)} / {source_sha256}, expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    old_name, new_name = OLD_CUE_NAME.encode("ascii"), NEW_CUE_NAME.encode("ascii")
    if state.count(old_name) != 1 or state.count(new_name):
        raise SurfaceSlotMigrationError("Source CUE identity drifted")

    old_table, new_table = _validate_media(
        old_disc, new_disc, old_manifest, new_manifest
    )
    source_payload, frame_start, source_prefix = _unpack_state(state, zstd)
    if (
        frame_start != SOURCE_PREFIX_SIZE
        or _sha256(source_prefix) != SOURCE_PREFIX_SHA256
        or len(state) - frame_start != SOURCE_COMPRESSED_SIZE
        or _sha256(state[frame_start:]) != SOURCE_COMPRESSED_SHA256
    ):
        raise SurfaceSlotMigrationError("Pinned V233 DuckStation frame drifted")
    final_payload, audit = _patch_resident_controls(source_payload, old_table, new_table)

    result = _pack_state(source_prefix.replace(old_name, new_name), final_payload, zstd)
    verified_payload, verified_frame, verified_prefix = _unpack_state(result, zstd)
    expected_prefix = _expected_prefix(
        source_prefix, compressed_size=len(result) - frame_start
    )
    prefix_diffs = _diff_triplets(source_prefix, expected_prefix)
    assert OUTPUT_STATE_SIZE is not None and OUTPUT_STATE_SHA256 is not None
    assert OUTPUT_PREFIX_SHA256 is not None
    assert OUTPUT_COMPRESSED_SIZE is not None and OUTPUT_COMPRESSED_SHA256 is not None
    assert OUTPUT_PAYLOAD_SHA256 is not None and OUTPUT_RAM_SHA256 is not None
    assert EXPECTED_PREFIX_BYTES_CHANGED is not None
    if (
        verified_payload != final_payload
        or verified_frame != SOURCE_PREFIX_SIZE
        or verified_prefix != expected_prefix
        or len(prefix_diffs) != EXPECTED_PREFIX_BYTES_CHANGED
        or len(result) != OUTPUT_STATE_SIZE
        or _sha256(result) != OUTPUT_STATE_SHA256
        or _sha256(verified_prefix) != OUTPUT_PREFIX_SHA256
        or len(result) - verified_frame != OUTPUT_COMPRESSED_SIZE
        or _sha256(result[verified_frame:]) != OUTPUT_COMPRESSED_SHA256
        or _sha256(verified_payload) != OUTPUT_PAYLOAD_SHA256
        or _sha256(_ram_from_payload(verified_payload)[1]) != OUTPUT_RAM_SHA256
        or result.count(old_name)
        or result.count(new_name) != 1
    ):
        raise SurfaceSlotMigrationError("Deterministic V234 state round trip drifted")

    report: dict[str, object] = {
        "source_size": len(state),
        "source_sha256": SOURCE_STATE_SHA256,
        "output_size": len(result),
        "output_sha256": OUTPUT_STATE_SHA256,
        "prefix_size": verified_frame,
        "prefix_sha256": OUTPUT_PREFIX_SHA256,
        "prefix_bytes_changed": len(prefix_diffs),
        "compressed_payload_size": len(result) - verified_frame,
        "compressed_payload_sha256": OUTPUT_COMPRESSED_SHA256,
        "payload_size": len(final_payload),
        "payload_sha256": OUTPUT_PAYLOAD_SHA256,
        "ram_sha256": OUTPUT_RAM_SHA256,
        **audit,
        "field": EXPECTED_FIELD,
        "field_overlay_mask_count": len(FIELD_OVERLAY_MASK_OFFSETS),
        "resident_script_mask_count": len(RESIDENT_ACTION_MASK_OFFSETS),
        "physical_cross_mask": "0x0040",
        "physical_circle_mask": "0x0020",
        "cross_only_confirm_and_interact": True,
        "circle_reserved_for_dash_and_cancel": True,
        "fei_party_gamestate_field_runtime_preserved": True,
        "resident_overlay_writable_data_preserved": True,
        "resident_archive_volatile_tail_preserved": True,
        "cold_reload_uses_normal_v234": True,
        "round_trip_verified": True,
        "changed_resource_ids": list(CHANGED_RESOURCE_IDS or ()),
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "v233_manifest_sha256": OLD_MANIFEST_SHA256,
        "v234_manifest_sha256": NEW_MANIFEST_SHA256,
        "v233_disc_sha256": OLD_DISC_SHA256,
        "v234_disc_sha256": NEW_DISC_SHA256,
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
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v233_stage" / "manifest.json",
    )
    parser.add_argument(
        "--new-manifest", type=Path,
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v234_stage" / "manifest.json",
    )
    parser.add_argument(
        "--zstd", type=Path,
        default=PROJECT_ROOT / "work" / "duckstation" / "zstd.dll",
    )
    parser.add_argument(
        "--output", type=Path,
        default=(PROJECT_ROOT / "work" / "save_candidates"
                 / "SLUS-00669_1_v234_from_b9b41cbc_cross_only_controls.sav"),
    )
    parser.add_argument(
        "--report", type=Path,
        default=(PROJECT_ROOT / "work" / "save_candidates"
                 / "SLUS-00669_1_v234_from_b9b41cbc_cross_only_controls.json"),
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
        result, report = migrate_v233_slot1_to_v234(
            source_path.read_bytes(),
            old_disc=args.old_disc,
            new_disc=args.new_disc,
            old_manifest=args.old_manifest.read_bytes(),
            new_manifest=args.new_manifest.read_bytes(),
            zstd=media_migration._Zstd(args.zstd),
        )
        report_blob = _report_blob(report)
        assert OUTPUT_REPORT_SIZE is not None and OUTPUT_REPORT_SHA256 is not None
        if (len(report_blob), _sha256(report_blob)) != (
            OUTPUT_REPORT_SIZE, OUTPUT_REPORT_SHA256
        ):
            raise SurfaceSlotMigrationError("V234 report identity drifted")
        if output.exists() and output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Refusing to overwrite a different V234 candidate")
        if report_path.exists() and report_path.read_bytes() != report_blob:
            raise SurfaceSlotMigrationError("Refusing to overwrite a different V234 report")
        output.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        report_path.write_bytes(report_blob)
        if output.read_bytes() != result or report_path.read_bytes() != report_blob:
            raise SurfaceSlotMigrationError("Written V234 candidate/report failed verification")
    except (
        OSError,
        ValueError,
        SurfaceSlotMigrationError,
        media_migration.StateMigrationError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote V234 candidate: {output}")
    print(f"Wrote migration report: {report_path}")
    print(f"SHA-256: {report['output_sha256']}")
    print("The live Slot 1 was not modified. Install only after DuckStation is fully closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
