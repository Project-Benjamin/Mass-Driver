from __future__ import annotations

from contextlib import ExitStack
import hashlib
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

import tools.migrate_duckstation_disc_state as media_migration
import tools.migrate_surface_soylent_v204_slot1_to_v205 as slot_migration
from work.read_duckstation_runtime import (
    FIELD_ACTORS,
    FIELD_ACTOR_DATA_POINTER,
    FIELD_ACTOR_STRIDE,
    FIELD_CUR_SCRIPT_FILE,
    FIELD_NUM_ACTORS,
    FIELD_SCRIPT_VM_CUR_SCRIPT_DATA,
    GAME_STATE,
    RAM_SIZE,
)


SOURCE_FRAME = media_migration.ZSTD_MAGIC + b"synthetic-v204-slot1"
OLD_DISC = Path("old.bin")
NEW_DISC = Path("new.bin")


class _FakeZstd:
    def __init__(self, source_payload: bytes) -> None:
        self.frames = {SOURCE_FRAME: source_payload}
        self.compressed_payloads: list[bytes] = []

    def frame_size(self, frame: bytes) -> int:
        if frame not in self.frames:
            raise AssertionError(f"Unknown fake zstd frame: {frame!r}")
        return len(frame)

    def decompress(self, frame: bytes) -> bytes:
        try:
            return self.frames[frame]
        except KeyError as exc:
            raise AssertionError(f"Unknown fake zstd frame: {frame!r}") from exc

    def compress(self, payload: bytes) -> bytes:
        self.compressed_payloads.append(payload)
        sequence = len(self.compressed_payloads)
        frame = media_migration.ZSTD_MAGIC + f"synthetic-{sequence}".encode()
        self.frames[frame] = payload
        return frame


def _scripts() -> tuple[bytes, bytes]:
    old = bytearray(slot_migration.SCRIPT_SIZE)
    struct.pack_into("<I", old, 0x80, slot_migration.SCRIPT_ENTITY_COUNT)
    pointer_offset = (
        slot_migration.SCRIPT_ENTRY_TABLE_OFFSET
        + slot_migration.FREIGHT_ENTITY * slot_migration.SCRIPT_ENTRY_SIZE
        + slot_migration.FREIGHT_ACTION_SLOT * 2
    )
    struct.pack_into("<H", old, pointer_offset, slot_migration.FREIGHT_GATE_PC)
    change_offset = (
        slot_migration.SCRIPT_BYTECODE_OFFSET
        + slot_migration.FREIGHT_CHANGE_PC
    )
    old[
        change_offset : change_offset + len(slot_migration.OLD_FREIGHT_CHANGE)
    ] = slot_migration.OLD_FREIGHT_CHANGE
    new = bytearray(old)
    new[
        change_offset : change_offset + len(slot_migration.NEW_FREIGHT_CHANGE)
    ] = slot_migration.NEW_FREIGHT_CHANGE
    return bytes(old), bytes(new)


def _tables() -> tuple[bytes, bytes]:
    old = bytearray(
        (offset * 73 + 19) & 0xFF
        for offset in range(slot_migration.ARCHIVE_TABLE_SIZE)
    )
    new = bytearray(old)
    offset, old_byte, new_byte = slot_migration.ARCHIVE_TABLE_DIFFS[0]
    old[offset] = old_byte
    new[offset] = new_byte
    return bytes(old), bytes(new)


def _source_payload(old_script: bytes, old_table: bytes) -> bytes:
    payload = bytearray(slot_migration.EXPECTED_PAYLOAD_SIZE)
    ram_payload_offset = slot_migration.EXPECTED_RAM_PAYLOAD_OFFSET

    marker = ram_payload_offset - (4 + len(b"Bus") + 4 + 5 * 3 * 4)
    payload[marker : marker + 7] = struct.pack("<I", 3) + b"Bus"
    struct.pack_into("<I", payload, marker + 7, RAM_SIZE)

    def ram_pack(fmt: str, ram_offset: int, *values: int) -> None:
        struct.pack_into(fmt, payload, ram_payload_offset + ram_offset, *values)

    ram_pack(
        "<I",
        FIELD_CUR_SCRIPT_FILE,
        slot_migration.EXPECTED_SCRIPT_GUEST_POINTER,
    )
    ram_pack(
        "<I",
        FIELD_SCRIPT_VM_CUR_SCRIPT_DATA,
        slot_migration.EXPECTED_VM_SCRIPT_GUEST_POINTER,
    )
    ram_pack("<H", GAME_STATE + slot_migration.GAMESTATE_FIELD_OFFSET, 621)
    ram_pack("<I", FIELD_NUM_ACTORS, slot_migration.EXPECTED_ACTOR_COUNT)
    ram_pack(
        "<I",
        FIELD_ACTORS,
        slot_migration.EXPECTED_ACTOR_ARRAY_GUEST_POINTER,
    )
    actor_array = (
        slot_migration.EXPECTED_ACTOR_ARRAY_GUEST_POINTER & 0x1FFFFFFF
    )
    for entity, actor_data, current_pc in (
        (
            slot_migration.PLAYER_ENTITY,
            slot_migration.EXPECTED_PLAYER_ACTOR_DATA,
            slot_migration.EXPECTED_PLAYER_IDLE_PC,
        ),
        (
            slot_migration.FREIGHT_ENTITY,
            slot_migration.FREIGHT_ACTOR_DATA,
            slot_migration.EXPECTED_FREIGHT_IDLE_PC,
        ),
    ):
        actor = actor_array + entity * FIELD_ACTOR_STRIDE
        ram_pack(
            "<I",
            actor + FIELD_ACTOR_DATA_POINTER,
            0x80000000 | actor_data,
        )
        ram_pack(
            "<HB",
            actor_data + slot_migration.ACTOR_CURRENT_PC_OFFSET,
            current_pc,
            0,
        )

    payload[
        slot_migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
        slot_migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + len(old_table)
    ] = old_table
    payload[
        slot_migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET :
        slot_migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + len(old_script)
    ] = old_script
    return bytes(payload)


def _source_state(payload: bytes) -> bytes:
    prefix = bytearray(b"\x6D" * slot_migration.EXPECTED_FRAME_START)
    prefix[:4] = media_migration.DUCKSTATION_STATE_MAGIC
    cue = slot_migration.OLD_CUE_NAME.encode("ascii")
    prefix[0x102 : 0x102 + len(cue)] = cue
    struct.pack_into(
        "<IIII",
        prefix,
        media_migration.DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
        media_migration.DUCKSTATION_ZSTD_COMPRESSION_TYPE,
        len(SOURCE_FRAME),
        len(payload),
        slot_migration.EXPECTED_FRAME_START,
    )
    return bytes(prefix) + SOURCE_FRAME


def _archive_table_for(
    path: Path,
    old_table: bytes,
    new_table: bytes,
) -> bytes:
    if path.name == OLD_DISC.name:
        return old_table
    if path.name == NEW_DISC.name:
        return new_table
    raise AssertionError(f"Unexpected fake disc path: {path}")


def _preview_media_sha256(
    source: bytes,
    payload: bytes,
    old_table: bytes,
    new_table: bytes,
) -> str:
    zstd = _FakeZstd(payload)
    with patch.object(
        media_migration,
        "_archive_table",
        side_effect=lambda path: _archive_table_for(
            path, old_table, new_table
        ),
    ):
        result, _report = media_migration.migrate_state(
            source,
            old_disc=OLD_DISC,
            new_disc=NEW_DISC,
            old_cue_name=slot_migration.OLD_CUE_NAME,
            new_cue_name=slot_migration.NEW_CUE_NAME,
            zstd=zstd,
        )
    return hashlib.sha256(result).hexdigest()


def _pinned_contract(
    source: bytes,
    payload: bytes,
    old_script: bytes,
    new_script: bytes,
    old_table: bytes,
    new_table: bytes,
) -> ExitStack:
    expected_media_hash = _preview_media_sha256(
        source, payload, old_table, new_table
    )
    stack = ExitStack()
    stack.enter_context(
        patch.object(
            slot_migration,
            "SOURCE_STATE_SHA256",
            hashlib.sha256(source).hexdigest(),
        )
    )
    stack.enter_context(
        patch.object(
            slot_migration,
            "EXPECTED_MEDIA_STATE_SHA256",
            expected_media_hash,
        )
    )
    stack.enter_context(
        patch.object(
            slot_migration,
            "OLD_SCRIPT_SHA256",
            hashlib.sha256(old_script).hexdigest(),
        )
    )
    stack.enter_context(
        patch.object(
            slot_migration,
            "NEW_SCRIPT_SHA256",
            hashlib.sha256(new_script).hexdigest(),
        )
    )
    stack.enter_context(
        patch.object(
            slot_migration,
            "OLD_ARCHIVE_TABLE_SHA256",
            hashlib.sha256(old_table).hexdigest(),
        )
    )
    stack.enter_context(
        patch.object(
            slot_migration,
            "NEW_ARCHIVE_TABLE_SHA256",
            hashlib.sha256(new_table).hexdigest(),
        )
    )
    stack.enter_context(
        patch.object(
            slot_migration,
            "_file_sha256",
            side_effect=lambda path: (
                slot_migration.OLD_DISC_SHA256
                if path.name == OLD_DISC.name
                else slot_migration.NEW_DISC_SHA256
            ),
        )
    )
    stack.enter_context(
        patch.object(
            media_migration,
            "_archive_table",
            side_effect=lambda path: _archive_table_for(
                path, old_table, new_table
            ),
        )
    )
    return stack


class SurfaceSoylentSlotMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old_script, self.new_script = _scripts()
        self.old_table, self.new_table = _tables()
        self.payload = _source_payload(self.old_script, self.old_table)
        self.source = _source_state(self.payload)

    def test_combined_migration_changes_only_fat_and_script_bytes(self) -> None:
        zstd = _FakeZstd(self.payload)
        with _pinned_contract(
            self.source,
            self.payload,
            self.old_script,
            self.new_script,
            self.old_table,
            self.new_table,
        ):
            result, report = slot_migration.migrate_v204_slot1_to_v205(
                self.source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_script=self.old_script,
                new_script=self.new_script,
                zstd=zstd,
            )

        final_payload, frame_start, _prefix = slot_migration._unpack_state(
            result, zstd
        )
        expected_offsets = (
            slot_migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + 0x2F58,
            slot_migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + 0x1891,
            slot_migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + 0x1893,
        )
        self.assertEqual(
            slot_migration._diff_offsets(self.payload, final_payload),
            tuple(sorted(expected_offsets)),
        )
        self.assertEqual(report["payload_bytes_changed"], 3)
        self.assertTrue(report["gamestate_preserved"])
        self.assertTrue(report["runtime_contract_preserved"])
        self.assertTrue(report["round_trip_verified"])
        self.assertEqual(frame_start, slot_migration.EXPECTED_FRAME_START)
        self.assertEqual(
            final_payload[
                slot_migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
                slot_migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
                + len(self.new_table)
            ],
            self.new_table,
        )
        self.assertEqual(
            final_payload[
                slot_migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET :
                slot_migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET
                + len(self.new_script)
            ],
            self.new_script,
        )
        game_state_start = (
            slot_migration.EXPECTED_RAM_PAYLOAD_OFFSET + GAME_STATE
        )
        game_state_end = game_state_start + slot_migration.GAMESTATE_SIZE
        self.assertEqual(
            final_payload[game_state_start:game_state_end],
            self.payload[game_state_start:game_state_end],
        )
        self.assertEqual(
            result.count(slot_migration.OLD_CUE_NAME.encode("ascii")), 0
        )
        self.assertEqual(
            result.count(slot_migration.NEW_CUE_NAME.encode("ascii")), 1
        )

    def test_rejects_any_source_state_hash_drift(self) -> None:
        with self.assertRaisesRegex(
            slot_migration.SurfaceSlotMigrationError,
            "Source Slot 1 SHA-256",
        ):
            slot_migration.migrate_v204_slot1_to_v205(
                self.source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_script=self.old_script,
                new_script=self.new_script,
                zstd=_FakeZstd(self.payload),
            )

    def test_rejects_script_delta_beyond_the_two_audited_bytes(self) -> None:
        drifted = bytearray(self.new_script)
        drifted[0x200] ^= 0x01
        with (
            patch.object(
                slot_migration,
                "SOURCE_STATE_SHA256",
                hashlib.sha256(self.source).hexdigest(),
            ),
            patch.object(
                slot_migration,
                "OLD_SCRIPT_SHA256",
                hashlib.sha256(self.old_script).hexdigest(),
            ),
            patch.object(
                slot_migration,
                "NEW_SCRIPT_SHA256",
                hashlib.sha256(bytes(drifted)).hexdigest(),
            ),
            self.assertRaisesRegex(
                slot_migration.SurfaceSlotMigrationError,
                "exact audited V205 freight retarget",
            ),
        ):
            slot_migration.migrate_v204_slot1_to_v205(
                self.source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_script=self.old_script,
                new_script=bytes(drifted),
                zstd=_FakeZstd(self.payload),
            )

    def test_rejects_cue_identity_drift_even_with_a_pinned_source(self) -> None:
        drifted_source = self.source.replace(
            slot_migration.OLD_CUE_NAME.encode("ascii"),
            b"X" * len(slot_migration.OLD_CUE_NAME),
        )
        with (
            patch.object(
                slot_migration,
                "SOURCE_STATE_SHA256",
                hashlib.sha256(drifted_source).hexdigest(),
            ),
            self.assertRaisesRegex(
                slot_migration.SurfaceSlotMigrationError,
                "one exact V204 CUE name",
            ),
        ):
            slot_migration.migrate_v204_slot1_to_v205(
                drifted_source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_script=self.old_script,
                new_script=self.new_script,
                zstd=_FakeZstd(self.payload),
            )

    def test_rejects_archive_table_delta_beyond_the_audited_byte(self) -> None:
        drifted_new_table = bytearray(self.new_table)
        drifted_new_table[0x100] ^= 0x01
        with (
            patch.object(
                slot_migration,
                "OLD_ARCHIVE_TABLE_SHA256",
                hashlib.sha256(self.old_table).hexdigest(),
            ),
            patch.object(
                slot_migration,
                "NEW_ARCHIVE_TABLE_SHA256",
                hashlib.sha256(bytes(drifted_new_table)).hexdigest(),
            ),
            patch.object(
                slot_migration,
                "_file_sha256",
                side_effect=(
                    slot_migration.OLD_DISC_SHA256,
                    slot_migration.NEW_DISC_SHA256,
                ),
            ),
            patch.object(
                media_migration,
                "_archive_table",
                side_effect=(self.old_table, bytes(drifted_new_table)),
            ),
            self.assertRaisesRegex(
                slot_migration.SurfaceSlotMigrationError,
                "exact audited release delta",
            ),
        ):
            slot_migration._validate_disc_contract(OLD_DISC, NEW_DISC)

    def test_rejects_runtime_pointer_drift_even_with_a_pinned_source(self) -> None:
        drifted_payload = bytearray(self.payload)
        pointer = (
            slot_migration.EXPECTED_RAM_PAYLOAD_OFFSET + FIELD_CUR_SCRIPT_FILE
        )
        struct.pack_into("<I", drifted_payload, pointer, 0x80110000)
        drifted_source = _source_state(bytes(drifted_payload))
        with (
            patch.object(
                slot_migration,
                "SOURCE_STATE_SHA256",
                hashlib.sha256(drifted_source).hexdigest(),
            ),
            patch.object(
                slot_migration,
                "OLD_SCRIPT_SHA256",
                hashlib.sha256(self.old_script).hexdigest(),
            ),
            patch.object(
                slot_migration,
                "NEW_SCRIPT_SHA256",
                hashlib.sha256(self.new_script).hexdigest(),
            ),
            patch.object(
                slot_migration,
                "OLD_ARCHIVE_TABLE_SHA256",
                hashlib.sha256(self.old_table).hexdigest(),
            ),
            patch.object(
                slot_migration,
                "NEW_ARCHIVE_TABLE_SHA256",
                hashlib.sha256(self.new_table).hexdigest(),
            ),
            patch.object(
                slot_migration,
                "_file_sha256",
                side_effect=(
                    slot_migration.OLD_DISC_SHA256,
                    slot_migration.NEW_DISC_SHA256,
                ),
            ),
            patch.object(
                media_migration,
                "_archive_table",
                side_effect=lambda path: _archive_table_for(
                    path, self.old_table, self.new_table
                ),
            ),
            self.assertRaisesRegex(
                slot_migration.SurfaceSlotMigrationError,
                "runtime pointers",
            ),
        ):
            slot_migration.migrate_v204_slot1_to_v205(
                drifted_source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_script=self.old_script,
                new_script=self.new_script,
                zstd=_FakeZstd(bytes(drifted_payload)),
            )

    def test_cli_refuses_the_live_slot_as_output(self) -> None:
        argv = (
            "input.sav",
            str(slot_migration.LIVE_SLOT1),
            "--old-disc",
            "old.bin",
            "--new-disc",
            "new.bin",
            "--old-script",
            "old-script.bin",
            "--new-script",
            "new-script.bin",
            "--zstd",
            "zstd.dll",
        )
        with (
            patch.object(Path, "is_file", return_value=True),
            self.assertRaises(SystemExit),
        ):
            slot_migration.main(argv)


if __name__ == "__main__":
    unittest.main()
