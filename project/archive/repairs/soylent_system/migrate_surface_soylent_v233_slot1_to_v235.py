#!/usr/bin/env python3
"""Migrate the exact pre-test V233 field-567 Slot 1 directly to V235.

The V234 control correction was reversed for the user's controller: its
resident field overlay made physical Circle the interaction button and left
physical Cross inactive.  The safest recovery does not chain through that
state.  It starts from the pinned, untouched V233 backup, keeps field 567's
already-correct authored action masks (0x0020), and changes only the five
resident overlay masks from the V233 dual-button value 0x0060 to the verified
physical-Cross value 0x0020.

This helper is deliberately fail-closed.  It accepts only the pinned V233
state/media and final V235 media, verifies an exact decompressed-byte
whitelist, writes only a separate candidate and JSON report, and refuses to
write DuckStation's live Slot 1.  Final V235 media/report pins are intentionally
left unset until the deterministic V235 build is available; until then the CLI
cannot write a candidate.
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
import tools.migrate_surface_soylent_v233_slot1_to_v234 as v234_migration  # noqa: E402
from tools.xgdisc import Mode2Image  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIVE_SLOT1 = (PROJECT_ROOT / "emulator_data" / "SLUS-00669_1.sav").resolve()
SOURCE_FIXTURE = v234_migration.SOURCE_FIXTURE

# Exact untouched V233 pre-test backup.
SOURCE_STATE_SIZE = v234_migration.SOURCE_STATE_SIZE
SOURCE_STATE_SHA256 = v234_migration.SOURCE_STATE_SHA256
SOURCE_PREFIX_SIZE = v234_migration.SOURCE_PREFIX_SIZE
SOURCE_PREFIX_SHA256 = v234_migration.SOURCE_PREFIX_SHA256
SOURCE_COMPRESSED_SIZE = v234_migration.SOURCE_COMPRESSED_SIZE
SOURCE_COMPRESSED_SHA256 = v234_migration.SOURCE_COMPRESSED_SHA256
SOURCE_PAYLOAD_SIZE = v234_migration.SOURCE_PAYLOAD_SIZE
SOURCE_PAYLOAD_SHA256 = v234_migration.SOURCE_PAYLOAD_SHA256
SOURCE_RAM_SHA256 = v234_migration.SOURCE_RAM_SHA256

# The final V235 media changes the resident archive table by two bytes because
# the corrected world-map overlay packs smaller.  These identities freeze the
# exact result of that table migration plus the five resident control bytes.
OUTPUT_STATE_SIZE: int | None = 1_457_266
OUTPUT_STATE_SHA256: str | None = "71248a8ca5fa5961967470e20c263e9301d7ac9d4a1b696588ce2f720255a47a"
OUTPUT_PREFIX_SHA256: str | None = "fa3060535f9770437498b164a0a0cbffef1fa5b26d30c15d57e2f693c94e9068"
OUTPUT_COMPRESSED_SIZE: int | None = 1_404_450
OUTPUT_COMPRESSED_SHA256: str | None = "e7d2155f914b3cd39b662d3eb10ead6e24af41a06c20b581a70924ac7a632d0a"
OUTPUT_PAYLOAD_SHA256: str | None = "c6bdf845a4bb39063ff3b9ded7d9a4159fef4213d3a56863dc7550bab114e6dd"
OUTPUT_RAM_SHA256: str | None = "a9769fb37c961bddeac6ed7dd4ec45b9776b4331dc3db687bb557db2165affe3"
OUTPUT_REPORT_SIZE: int | None = 2_365
OUTPUT_REPORT_SHA256: str | None = "348e68c037703fb2c6646b2e9d24a9ef7c927856f8424d9dbee69569d30a8740"

OLD_DISC_SIZE = v234_migration.OLD_DISC_SIZE
OLD_DISC_SHA256 = v234_migration.OLD_DISC_SHA256
NEW_DISC_SIZE: int | None = 698_816_832
NEW_DISC_SHA256: str | None = "a799fccff716373db5ce37f7a8c728179ab206b9f8da6753fc3ac00ddc732e73"
OLD_CUE_NAME = v234_migration.OLD_CUE_NAME
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v235.cue"
OLD_CUE_SIZE = v234_migration.OLD_CUE_SIZE
OLD_CUE_SHA256 = v234_migration.OLD_CUE_SHA256
NEW_CUE_SIZE: int | None = 112
NEW_CUE_SHA256: str | None = "887cf1d477a450dfe241c14ae59b1cba56f09099475569d2c5cc59f769a0ce5b"

OLD_MANIFEST_SIZE = v234_migration.OLD_MANIFEST_SIZE
OLD_MANIFEST_SHA256 = v234_migration.OLD_MANIFEST_SHA256
NEW_MANIFEST_SIZE: int | None = 136_361
NEW_MANIFEST_SHA256: str | None = "902134a13d4ecd321d459f4d1be555ae55ad1c386d5ca3fee7f10b94425697c8"
CHANGED_RESOURCE_IDS: tuple[int, ...] | None = ()

FIELD_OVERLAY_CANONICAL_ID = v234_migration.FIELD_OVERLAY_CANONICAL_ID
WORLDMAP_OVERLAY_CANONICAL_ID = v234_migration.WORLDMAP_OVERLAY_CANONICAL_ID
OLD_FIELD_OVERLAY_SIZE = v234_migration.OLD_FIELD_OVERLAY_SIZE
OLD_FIELD_OVERLAY_SHA256 = v234_migration.OLD_FIELD_OVERLAY_SHA256
NEW_FIELD_OVERLAY_SIZE: int | None = 293_476
NEW_FIELD_OVERLAY_SHA256: str | None = "efb2261d9ba698f1cac134d0e4a04a0a68ecbb02a19ee1ca5f365817d0d9c500"
OLD_WORLDMAP_OVERLAY_SIZE = v234_migration.OLD_WORLDMAP_OVERLAY_SIZE
OLD_WORLDMAP_OVERLAY_SHA256 = v234_migration.OLD_WORLDMAP_OVERLAY_SHA256
NEW_WORLDMAP_OVERLAY_SIZE: int | None = 92_451
NEW_WORLDMAP_OVERLAY_SHA256: str | None = "d20de1731324e5024745e54ed592aeb5664d5ac0f5f5197d52e5432f0d7e11b8"

ARCHIVE_TABLE_SIZE = v234_migration.ARCHIVE_TABLE_SIZE
OLD_ARCHIVE_TABLE_SHA256 = v234_migration.OLD_ARCHIVE_TABLE_SHA256
NEW_ARCHIVE_TABLE_SHA256: str | None = "648bf421a766f34642f7d60c1eac8bf0192af36a5985404affc372323437d94d"
ARCHIVE_TABLE_DIFFS: tuple[tuple[int, int, int], ...] | None = (
    (227, 0xB0, 0x23),
    (228, 0x6C, 0x69),
)
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = v234_migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
SOURCE_RESIDENT_TABLE_SHA256 = v234_migration.SOURCE_RESIDENT_TABLE_SHA256
OUTPUT_RESIDENT_TABLE_SHA256: str | None = "aa713f7ed2564a84c79d5683784a80faf7a6d7aade235c0d70e45fec3f93813a"
EXPECTED_VOLATILE_TABLE_VALUE = v234_migration.EXPECTED_VOLATILE_TABLE_VALUE

FIELD_OVERLAY_RAM_OFFSET = v234_migration.FIELD_OVERLAY_RAM_OFFSET
FIELD_OVERLAY_RUNTIME_SIZE = v234_migration.FIELD_OVERLAY_RUNTIME_SIZE
FIELD_OVERLAY_CODE_SIZE = v234_migration.FIELD_OVERLAY_CODE_SIZE
SOURCE_FIELD_OVERLAY_RUNTIME_SHA256 = v234_migration.SOURCE_FIELD_OVERLAY_RUNTIME_SHA256
SOURCE_FIELD_OVERLAY_CODE_SHA256 = v234_migration.SOURCE_FIELD_OVERLAY_CODE_SHA256
OUTPUT_FIELD_OVERLAY_RUNTIME_SHA256 = "39d3c686f3975ac276dc38e891f8ab2728c761836178bda238b8285a3533e95b"
OUTPUT_FIELD_OVERLAY_CODE_SHA256 = "da21cfc3759fe7e25d58ebf1e430f443c5f5e2a2eaa63eee6514a1ecbb492f72"
FIELD_OVERLAY_MASK_OFFSETS = v234_migration.FIELD_OVERLAY_MASK_OFFSETS
OLD_OVERLAY_MASK_INSTRUCTION = bytes.fromhex("60 00 42 30")
NEW_OVERLAY_MASK_INSTRUCTION = bytes.fromhex("20 00 42 30")

# Field 567 already uses the correct physical-Cross mask in the V233 backup.
# It is validated byte-for-byte and deliberately not patched.
RESIDENT_SCRIPT_RAM_OFFSET = v234_migration.RESIDENT_SCRIPT_RAM_OFFSET
RESIDENT_SCRIPT_SIZE = v234_migration.RESIDENT_SCRIPT_SIZE
SOURCE_RESIDENT_SCRIPT_SHA256 = v234_migration.SOURCE_RESIDENT_SCRIPT_SHA256
OUTPUT_RESIDENT_SCRIPT_SHA256 = SOURCE_RESIDENT_SCRIPT_SHA256
RESIDENT_ACTION_RAM_OFFSET = v234_migration.RESIDENT_ACTION_RAM_OFFSET
UNCHANGED_RESIDENT_ACTION = v234_migration.OLD_RESIDENT_ACTION
UNCHANGED_RESIDENT_ACTION_SHA256 = v234_migration.OLD_RESIDENT_ACTION_SHA256
RESIDENT_ACTION_MASK_OFFSETS = v234_migration.RESIDENT_ACTION_MASK_OFFSETS

EXPECTED_FIELD = v234_migration.EXPECTED_FIELD
EXPECTED_CONTROL_BYTES_CHANGED = len(FIELD_OVERLAY_MASK_OFFSETS)
CONTROL_DIFF_SHA256 = "5482d2fe40383d1912a9a515a3e78092c4673942ea51411e80bddbd976c503bc"
EXPECTED_PAYLOAD_BYTES_CHANGED: int | None = 7
PAYLOAD_DIFF_SHA256: str | None = "ee1c844a1296f2e5657dd08fecd590a70b7fc1bcffe28d4914721e83c963bffd"
EXPECTED_PREFIX_BYTES_CHANGED: int | None = 2

ZSTD_SIZE = v234_migration.ZSTD_SIZE
ZSTD_SHA256 = v234_migration.ZSTD_SHA256


class _ZstdLike(Protocol):
    def frame_size(self, frame: bytes) -> int: ...
    def decompress(self, frame: bytes) -> bytes: ...
    def compress(self, payload: bytes) -> bytes: ...


SurfaceSlotMigrationError = v234_migration.SurfaceSlotMigrationError
_sha256 = v234_migration._sha256
_file_sha256 = v234_migration._file_sha256
_diff_triplets = v234_migration._diff_triplets
_diff_offsets = v234_migration._diff_offsets
_triplet_digest = v234_migration._triplet_digest
_unpack_state = v234_migration._unpack_state
_pack_state = v234_migration._pack_state
_ram_from_payload = v234_migration._ram_from_payload
_validate_file = v234_migration._validate_file
_manifest_inventory = v234_migration._manifest_inventory
_disc_resource = v234_migration._disc_resource


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
        "V235 disc size": NEW_DISC_SIZE,
        "V235 disc hash": NEW_DISC_SHA256,
        "V235 CUE size": NEW_CUE_SIZE,
        "V235 CUE hash": NEW_CUE_SHA256,
        "V235 manifest size": NEW_MANIFEST_SIZE,
        "V235 manifest hash": NEW_MANIFEST_SHA256,
        "changed resource IDs": CHANGED_RESOURCE_IDS,
        "V235 field-overlay size": NEW_FIELD_OVERLAY_SIZE,
        "V235 field-overlay hash": NEW_FIELD_OVERLAY_SHA256,
        "V235 world-map size": NEW_WORLDMAP_OVERLAY_SIZE,
        "V235 world-map hash": NEW_WORLDMAP_OVERLAY_SHA256,
        "V235 archive-table hash": NEW_ARCHIVE_TABLE_SHA256,
        "V235 resident-table hash": OUTPUT_RESIDENT_TABLE_SHA256,
        "archive-table diffs": ARCHIVE_TABLE_DIFFS,
        "payload byte count": EXPECTED_PAYLOAD_BYTES_CHANGED,
        "payload diff hash": PAYLOAD_DIFF_SHA256,
        "prefix byte count": EXPECTED_PREFIX_BYTES_CHANGED,
    }
    missing = [label for label, value in pins.items() if value is None]
    if missing:
        raise SurfaceSlotMigrationError(
            "Final V235 identities are not pinned: " + ", ".join(missing)
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
    assert NEW_FIELD_OVERLAY_SIZE is not None and NEW_FIELD_OVERLAY_SHA256 is not None
    assert NEW_WORLDMAP_OVERLAY_SIZE is not None and NEW_WORLDMAP_OVERLAY_SHA256 is not None
    assert NEW_ARCHIVE_TABLE_SHA256 is not None and ARCHIVE_TABLE_DIFFS is not None
    for path, size, sha256, label in (
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V233 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V235 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V233 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V235 CUE"),
    ):
        _validate_file(path, size, sha256, label)

    old_inventory = _manifest_inventory(
        old_manifest, size=OLD_MANIFEST_SIZE, sha256=OLD_MANIFEST_SHA256,
        label="V233 manifest",
    )
    new_inventory = _manifest_inventory(
        new_manifest, size=NEW_MANIFEST_SIZE, sha256=NEW_MANIFEST_SHA256,
        label="V235 manifest",
    )
    changed = tuple(
        resource_id
        for resource_id in sorted(set(old_inventory) | set(new_inventory))
        if old_inventory.get(resource_id) != new_inventory.get(resource_id)
    )
    if changed != CHANGED_RESOURCE_IDS:
        raise SurfaceSlotMigrationError("V233/V235 manifest delta drifted")

    old_image, new_image = Mode2Image(old_disc), Mode2Image(new_disc)
    _disc_resource(
        old_image, FIELD_OVERLAY_CANONICAL_ID, OLD_FIELD_OVERLAY_SIZE,
        OLD_FIELD_OVERLAY_SHA256, "V233 field overlay",
    )
    _disc_resource(
        new_image, FIELD_OVERLAY_CANONICAL_ID, NEW_FIELD_OVERLAY_SIZE,
        NEW_FIELD_OVERLAY_SHA256, "V235 field overlay",
    )
    _disc_resource(
        old_image, WORLDMAP_OVERLAY_CANONICAL_ID, OLD_WORLDMAP_OVERLAY_SIZE,
        OLD_WORLDMAP_OVERLAY_SHA256, "V233 world-map overlay",
    )
    _disc_resource(
        new_image, WORLDMAP_OVERLAY_CANONICAL_ID, NEW_WORLDMAP_OVERLAY_SIZE,
        NEW_WORLDMAP_OVERLAY_SHA256, "V235 world-map overlay",
    )
    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    if (
        (len(old_table), len(new_table)) != (ARCHIVE_TABLE_SIZE, ARCHIVE_TABLE_SIZE)
        or _sha256(old_table) != OLD_ARCHIVE_TABLE_SHA256
        or _sha256(new_table) != NEW_ARCHIVE_TABLE_SHA256
        or _diff_triplets(old_table, new_table) != ARCHIVE_TABLE_DIFFS
    ):
        raise SurfaceSlotMigrationError("V233/V235 archive-table delta drifted")
    return old_table, new_table


def _validate_source_payload(payload: bytes, old_table: bytes) -> tuple[int, bytes]:
    """Reuse the exhaustive, pinned V233 field-567 runtime validation."""

    return v234_migration._validate_source_payload(payload, old_table)


def _patch_resident_controls(
    payload: bytes,
    old_table: bytes,
    new_table: bytes,
) -> tuple[bytes, dict[str, object]]:
    """Return the exact V235 payload while changing five overlay bytes only."""

    ram_offset, source_ram = _validate_source_payload(payload, old_table)
    final = bytearray(payload)

    resident_table = bytearray(new_table)
    resident_table[-1] = EXPECTED_VOLATILE_TABLE_VALUE
    if (
        OUTPUT_RESIDENT_TABLE_SHA256 is not None
        and _sha256(resident_table) != OUTPUT_RESIDENT_TABLE_SHA256
    ):
        raise SurfaceSlotMigrationError("V235 resident archive-table reconstruction drifted")
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
    final_payload = bytes(final)

    _result_ram_offset, result_ram = _ram_from_payload(final_payload)
    target_overlay = result_ram[
        FIELD_OVERLAY_RAM_OFFSET : FIELD_OVERLAY_RAM_OFFSET + FIELD_OVERLAY_RUNTIME_SIZE
    ]
    target_script = result_ram[
        RESIDENT_SCRIPT_RAM_OFFSET : RESIDENT_SCRIPT_RAM_OFFSET + RESIDENT_SCRIPT_SIZE
    ]
    target_action = result_ram[
        RESIDENT_ACTION_RAM_OFFSET :
        RESIDENT_ACTION_RAM_OFFSET + len(UNCHANGED_RESIDENT_ACTION)
    ]
    if (
        _sha256(target_overlay) != OUTPUT_FIELD_OVERLAY_RUNTIME_SHA256
        or _sha256(target_overlay[:FIELD_OVERLAY_CODE_SIZE])
        != OUTPUT_FIELD_OVERLAY_CODE_SHA256
        or _sha256(target_script) != OUTPUT_RESIDENT_SCRIPT_SHA256
        or target_action != UNCHANGED_RESIDENT_ACTION
        or _sha256(target_action) != UNCHANGED_RESIDENT_ACTION_SHA256
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
    }
    actual_diffs = _diff_triplets(payload, final_payload)
    control_diffs = tuple(diff for diff in actual_diffs if diff[0] in control_offsets)
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
        or (
            PAYLOAD_DIFF_SHA256 is not None
            and _triplet_digest(actual_diffs) != PAYLOAD_DIFF_SHA256
        )
        or (
            OUTPUT_PAYLOAD_SHA256 is not None
            and _sha256(final_payload) != OUTPUT_PAYLOAD_SHA256
        )
        or (OUTPUT_RAM_SHA256 is not None and _sha256(result_ram) != OUTPUT_RAM_SHA256)
    ):
        raise SurfaceSlotMigrationError("Migration escaped the exact payload whitelist")

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
        "<I",
        expected,
        media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        compressed_size,
    )
    return bytes(expected)


def migrate_v233_slot1_to_v235(
    state: bytes,
    *,
    old_disc: Path,
    new_disc: Path,
    old_manifest: bytes,
    new_manifest: bytes,
    zstd: _ZstdLike,
) -> tuple[bytes, dict[str, object]]:
    """Return the separately writable, fully validated V235 candidate."""

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

    old_table, new_table = _validate_media(old_disc, new_disc, old_manifest, new_manifest)
    source_payload, frame_start, source_prefix = _unpack_state(state, zstd)
    if (
        frame_start != SOURCE_PREFIX_SIZE
        or _sha256(source_prefix) != SOURCE_PREFIX_SHA256
        or len(state) - frame_start != SOURCE_COMPRESSED_SIZE
        or _sha256(state[frame_start:]) != SOURCE_COMPRESSED_SHA256
    ):
        raise SurfaceSlotMigrationError("Pinned V233 DuckStation frame drifted")
    final_payload, audit = _patch_resident_controls(payload=source_payload, old_table=old_table, new_table=new_table)

    result = _pack_state(source_prefix.replace(old_name, new_name), final_payload, zstd)
    verified_payload, verified_frame, verified_prefix = _unpack_state(result, zstd)
    expected_prefix = _expected_prefix(source_prefix, compressed_size=len(result) - frame_start)
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
        raise SurfaceSlotMigrationError("Deterministic V235 state round trip drifted")

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
        "resident_script_mask_count": 0,
        "physical_cross_mask": "0x0020",
        "physical_circle_mask": "0x0040",
        "cross_only_confirm_and_interact": True,
        "circle_reserved_for_dash_and_cancel": True,
        "resident_field_567_action_preserved": True,
        "fei_party_gamestate_field_runtime_preserved": True,
        "resident_overlay_writable_data_preserved": True,
        "resident_archive_volatile_tail_preserved": True,
        "cold_reload_uses_normal_v235": True,
        "round_trip_verified": True,
        "changed_resource_ids": list(CHANGED_RESOURCE_IDS or ()),
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "v233_manifest_sha256": OLD_MANIFEST_SHA256,
        "v235_manifest_sha256": NEW_MANIFEST_SHA256,
        "v233_disc_sha256": OLD_DISC_SHA256,
        "v235_disc_sha256": NEW_DISC_SHA256,
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
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v235_stage" / "manifest.json",
    )
    parser.add_argument(
        "--zstd", type=Path,
        default=PROJECT_ROOT / "work" / "duckstation" / "zstd.dll",
    )
    parser.add_argument(
        "--output", type=Path,
        default=(PROJECT_ROOT / "work" / "save_candidates"
                 / "SLUS-00669_1_v235_from_b9b41cbc_cross_only_controls.sav"),
    )
    parser.add_argument(
        "--report", type=Path,
        default=(PROJECT_ROOT / "work" / "save_candidates"
                 / "SLUS-00669_1_v235_from_b9b41cbc_cross_only_controls.json"),
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
        _require_target_pins()
        _validate_file(args.zstd, ZSTD_SIZE, ZSTD_SHA256, "zstd codec")
        result, report = migrate_v233_slot1_to_v235(
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
            raise SurfaceSlotMigrationError("V235 report identity drifted")
        if output.exists() and output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Refusing to overwrite a different V235 candidate")
        if report_path.exists() and report_path.read_bytes() != report_blob:
            raise SurfaceSlotMigrationError("Refusing to overwrite a different V235 report")
        output.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        report_path.write_bytes(report_blob)
        if output.read_bytes() != result or report_path.read_bytes() != report_blob:
            raise SurfaceSlotMigrationError("Written V235 candidate/report failed verification")
    except (
        OSError,
        ValueError,
        SurfaceSlotMigrationError,
        media_migration.StateMigrationError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote V235 candidate: {output}")
    print(f"Wrote migration report: {report_path}")
    print(f"SHA-256: {report['output_sha256']}")
    print("The live Slot 1 was not modified. Install only after DuckStation is fully closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
