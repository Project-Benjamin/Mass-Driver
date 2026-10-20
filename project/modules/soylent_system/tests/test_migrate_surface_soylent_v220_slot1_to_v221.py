from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

import io
from contextlib import redirect_stderr
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

import tools.migrate_duckstation_disc_state as media_migration
import tools.migrate_surface_soylent_v220_slot1_to_v221 as migration
from tools.xgdeathblows import GAMESTATE_SIZE
from work.read_duckstation_runtime import (
    CAMERA_VECTORS,
    FIELD_ACTORS,
    FIELD_ACTOR_DATA_POINTER,
    FIELD_ACTOR_STRIDE,
    FIELD_NUM_ACTORS,
    GAME_STATE,
)


PROJECT_ROOT = REPOSITORY_ROOT
SOURCE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_backups"
    / "SLUS-00669_1_v220_original_door_path_reference_e4aea385.sav"
)
CANDIDATE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v221_from_e4aea385_native_threshold_aprons.sav"
)
CANDIDATE_REPORT = CANDIDATE_STATE.with_suffix(".json")
OLD_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v220.bin"
)
NEW_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v221.bin"
)
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


class SurfaceSoylentV220ToV221StateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (
            SOURCE_STATE,
            OLD_DISC,
            NEW_DISC,
            OLD_DISC.with_name(migration.OLD_CUE_NAME),
            NEW_DISC.with_name(migration.NEW_CUE_NAME),
            ZSTD,
        )
        if not all(path.is_file() for path in required):
            raise unittest.SkipTest("Pinned V220/V221 migration fixtures are unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v220_slot1_to_v221(
            cls.source,
            old_disc=OLD_DISC,
            new_disc=NEW_DISC,
            zstd=cls.zstd,
        )
        (
            cls.source_payload,
            cls.source_frame_start,
            cls.source_prefix,
        ) = migration._unpack_state(cls.source, cls.zstd)
        (
            cls.output_payload,
            cls.output_frame_start,
            cls.output_prefix,
        ) = migration._unpack_state(cls.result, cls.zstd)
        cls.ram_offset, cls.source_ram = migration._ram_from_payload(cls.source_payload)
        output_ram_offset, cls.output_ram = migration._ram_from_payload(cls.output_payload)
        if output_ram_offset != cls.ram_offset:
            raise AssertionError("Serialized RAM moved during migration")

    def test_candidate_identity_media_path_report_and_round_trip_are_exact(self) -> None:
        self.assertEqual(
            (len(self.source), migration._sha256(self.source)),
            (migration.SOURCE_STATE_SIZE, migration.SOURCE_STATE_SHA256),
        )
        self.assertEqual(
            (len(self.result), migration._sha256(self.result)),
            (migration.OUTPUT_STATE_SIZE, migration.OUTPUT_STATE_SHA256),
        )
        self.assertEqual(
            (len(self.result) - self.output_frame_start, self.output_frame_start),
            (migration.OUTPUT_COMPRESSED_SIZE, migration.SOURCE_PREFIX_SIZE),
        )
        self.assertEqual(
            self.output_payload,
            self.zstd.decompress(self.result[self.output_frame_start :]),
        )
        self.assertEqual(
            self.output_prefix,
            migration._expected_prefix(
                self.source_prefix,
                compressed_size=migration.OUTPUT_COMPRESSED_SIZE,
            ),
        )
        self.assertEqual(
            migration._sha256(self.output_prefix), migration.OUTPUT_PREFIX_SHA256
        )
        self.assertEqual(
            self.output_prefix.count(migration.NEW_CUE_NAME.encode("ascii")), 1
        )
        self.assertNotIn(migration.OLD_CUE_NAME.encode("ascii"), self.output_prefix)
        self.assertEqual(
            struct.unpack_from(
                "<I",
                self.output_prefix,
                media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
            )[0],
            migration.OUTPUT_COMPRESSED_SIZE,
        )
        self.assertTrue(self.report["round_trip_verified"])
        if CANDIDATE_STATE.is_file():
            self.assertEqual(CANDIDATE_STATE.read_bytes(), self.result)
        if CANDIDATE_REPORT.is_file():
            self.assertEqual(
                json.loads(CANDIDATE_REPORT.read_text(encoding="utf-8")), self.report
            )

    def test_finished_disc_model20_is_the_exact_resident_source_and_target(self) -> None:
        old_disk = migration._disc_model20(
            OLD_DISC,
            bundle_identity=(
                migration.OLD_FIELD621_BUNDLE_SIZE,
                migration.OLD_FIELD621_BUNDLE_SHA256,
            ),
            archive_sha256=migration.OLD_FIELD621_MODEL_ARCHIVE_SHA256,
            model_sha256=migration.OLD_DISK_MODEL20_SHA256,
        )
        new_disk = migration._disc_model20(
            NEW_DISC,
            bundle_identity=(
                migration.NEW_FIELD621_BUNDLE_SIZE,
                migration.NEW_FIELD621_BUNDLE_SHA256,
            ),
            archive_sha256=migration.NEW_FIELD621_MODEL_ARCHIVE_SHA256,
            model_sha256=migration.NEW_DISK_MODEL20_SHA256,
        )
        source_model = self.source_ram[
            migration.RUNTIME_MODEL20_OFFSET :
            migration.RUNTIME_MODEL20_OFFSET + migration.RUNTIME_MODEL20_SIZE
        ]
        output_model = self.output_ram[
            migration.RUNTIME_MODEL20_OFFSET :
            migration.RUNTIME_MODEL20_OFFSET + migration.RUNTIME_MODEL20_SIZE
        ]
        self.assertEqual(migration._runtime_model20(old_disk), source_model)
        self.assertEqual(migration._runtime_model20(new_disk), output_model)
        self.assertEqual(
            (migration._sha256(source_model), migration._sha256(output_model)),
            (
                migration.SOURCE_RUNTIME_MODEL20_SHA256,
                migration.OUTPUT_RUNTIME_MODEL20_SHA256,
            ),
        )
        self.assertEqual(
            migration._model_layout(
                output_model,
                guest_base=migration.RUNTIME_MODEL20_OFFSET,
                expected_counts=migration.NEW_MODEL20_RUNTIME_COUNTS,
                expected_offsets=migration.NEW_MODEL20_OFFSETS,
            ),
            migration.NEW_MODEL20_INVENTORY,
        )
        self.assertEqual(
            struct.unpack_from("<HHH", output_model, 0x12), (15, 16, 2)
        )
        self.assertEqual(
            struct.unpack_from("<4I", output_model, 0x18),
            (0x80110A60, 0x80110A60, 0x80110AD8, 0x80110B50),
        )
        self.assertEqual(
            struct.unpack_from("<I", output_model, 0x44)[0],
            migration.RUNTIME_MODEL20_ARENA_SIZE,
        )
        self.assertEqual(
            output_model[0x138 : 0x138 + len(migration.NEW_MODEL20_DISPLAY_BYTES)],
            migration.NEW_MODEL20_DISPLAY_BYTES,
        )
        self.assertEqual(
            len(migration._diff_offsets(source_model, output_model)),
            migration.EXPECTED_MODEL20_BYTES_CHANGED,
        )

        # Reconcile the loader-count ambiguity explicitly.  The old finished
        # disc's 16 becomes 18 in the untouched source resident block, so the
        # same +2 maps V221's 14 to 16.  Omitting it changes exactly this u16.
        without_overhead = bytearray(output_model)
        struct.pack_into(
            "<H", without_overhead, 0x14, migration.NEW_MODEL20_DISK_COUNTS[1]
        )
        self.assertEqual(
            migration._sha256(bytes(without_overhead)),
            migration.NEW_RUNTIME_MODEL20_WITHOUT_OVERHEAD_SHA256,
        )
        self.assertEqual(
            migration._diff_offsets(bytes(without_overhead), output_model), (0x14,)
        )
        self.assertEqual((without_overhead[0x14], output_model[0x14]), (14, 16))
        self.assertEqual(
            (
                self.report["disk_model20_primitive_count"],
                self.report["runtime_model20_primitive_count"],
                self.report["model20_runtime_primitive_overhead"],
            ),
            (14, 16, 2),
        )

    def test_six_packet_arenas_are_repacked_for_the_new_topology(self) -> None:
        source_offsets = migration._packet_arena_offsets(
            self.source_ram, require_source_hashes=True
        )
        output_offsets = migration._packet_arena_offsets(
            self.output_ram, require_source_hashes=False
        )
        self.assertEqual(source_offsets, output_offsets)
        self.assertEqual(
            source_offsets,
            tuple(
                offset
                for _entity, _instance, pair in migration.MODEL20_INSTANCE_LAYOUT
                for offset in pair
            ),
        )
        target_model = self.output_ram[
            migration.RUNTIME_MODEL20_OFFSET :
            migration.RUNTIME_MODEL20_OFFSET + migration.RUNTIME_MODEL20_SIZE
        ]
        arena = migration._fresh_packet_arena(target_model)
        self.assertEqual(migration._sha256(arena), migration.TARGET_PACKET_ARENA_SHA256)
        changed = 0
        for offset in source_offsets:
            before = self.source_ram[
                offset : offset + migration.RUNTIME_MODEL20_ARENA_SIZE
            ]
            after = self.output_ram[
                offset : offset + migration.RUNTIME_MODEL20_ARENA_SIZE
            ]
            self.assertEqual(after, arena)
            changed += len(migration._diff_offsets(before, after))
        self.assertEqual(changed, migration.EXPECTED_PACKET_ARENA_BYTES_CHANGED)

        # Fresh POLY_FT4s: transient OT links, XY, and pad words are zero;
        # packet sizes/codes and the model's exact UV/CLUT/TPAGE are initialized.
        expected_ft4 = (
            (0x00, (0x97, 0x89, 0x97, 0x95, 0xA6, 0x89, 0xA6, 0x95)),
            (0x28, (0xA6, 0x89, 0xA6, 0x95, 0xB6, 0x89, 0xB6, 0x95)),
        )
        for start, uv in expected_ft4:
            packet = arena[start : start + 0x28]
            self.assertEqual(packet[:3], bytes(3))
            self.assertEqual((packet[3], packet[7]), (9, 0x2D))
            self.assertEqual(packet[4:7], bytes(3))
            self.assertEqual(packet[8:12], bytes(4))
            self.assertEqual(packet[16:20], bytes(4))
            self.assertEqual(packet[24:28], bytes(4))
            self.assertEqual(packet[32:36], bytes(4))
            self.assertEqual(
                (
                    packet[12], packet[13], packet[20], packet[21],
                    packet[28], packet[29], packet[36], packet[37],
                ),
                uv,
            )
            self.assertEqual(struct.unpack_from("<H", packet, 14)[0], 0x7900)
            self.assertEqual(struct.unpack_from("<H", packet, 22)[0], 0x00A8)
            self.assertEqual(packet[30:32] + packet[38:40], bytes(4))

        for index in range(12):
            start = 0x50 + index * 0x14
            packet = arena[start : start + 0x14]
            self.assertEqual(packet, bytes.fromhex("00 00 00 04 00 00 00 20") + bytes(12))
        self.assertEqual(0x50 + 12 * 0x14, migration.RUNTIME_MODEL20_ARENA_SIZE)
        self.assertTrue(self.report["packet_arenas_reinitialized_for_topology"])

    def test_archive_model_and_packet_arenas_are_the_only_payload_edits(self) -> None:
        old_table = media_migration._archive_table(OLD_DISC)
        new_table = media_migration._archive_table(NEW_DISC)
        self.assertEqual(
            migration._diff_triplets(old_table, new_table),
            migration.ARCHIVE_TABLE_DIFFS,
        )
        table_offset, volatile = media_migration._find_resident_archive_table(
            self.source_payload, old_table
        )
        self.assertEqual(table_offset, migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET)
        self.assertEqual(volatile, 1)
        self.assertEqual(
            self.output_payload[table_offset : table_offset + migration.ARCHIVE_TABLE_SIZE - 1],
            new_table[:-1],
        )
        self.assertEqual(
            self.output_payload[table_offset + migration.ARCHIVE_TABLE_SIZE - 1],
            migration.EXPECTED_VOLATILE_TABLE_VALUE,
        )
        self.assertEqual(
            migration._sha256(
                self.output_payload[
                    table_offset : table_offset + migration.ARCHIVE_TABLE_SIZE
                ]
            ),
            migration.OUTPUT_RESIDENT_TABLE_SHA256,
        )

        source_model = self.source_ram[
            migration.RUNTIME_MODEL20_OFFSET :
            migration.RUNTIME_MODEL20_OFFSET + migration.RUNTIME_MODEL20_SIZE
        ]
        output_model = self.output_ram[
            migration.RUNTIME_MODEL20_OFFSET :
            migration.RUNTIME_MODEL20_OFFSET + migration.RUNTIME_MODEL20_SIZE
        ]
        expected = {
            table_offset + migration.ARCHIVE_TABLE_DIFFS[0][0],
            *(
                self.ram_offset + migration.RUNTIME_MODEL20_OFFSET + relative
                for relative in migration._diff_offsets(source_model, output_model)
            ),
        }
        for offset in migration._packet_arena_offsets(
            self.source_ram, require_source_hashes=True
        ):
            before = self.source_ram[
                offset : offset + migration.RUNTIME_MODEL20_ARENA_SIZE
            ]
            after = self.output_ram[
                offset : offset + migration.RUNTIME_MODEL20_ARENA_SIZE
            ]
            expected.update(
                self.ram_offset + offset + relative
                for relative in migration._diff_offsets(before, after)
            )
        actual = set(migration._diff_offsets(self.source_payload, self.output_payload))
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        self.assertEqual(
            (migration._sha256(self.output_payload), migration._sha256(self.output_ram)),
            (migration.OUTPUT_PAYLOAD_SHA256, migration.OUTPUT_RAM_SHA256),
        )
        self.assertEqual(self.report["archive_table_bytes_changed"], 1)
        self.assertEqual(self.report["model20_bytes_changed"], 113)
        self.assertEqual(self.report["packet_arena_bytes_changed"], 911)
        self.assertEqual(self.report["resident_render_bytes_changed"], 1_024)
        self.assertEqual(self.report["payload_bytes_changed"], 1_025)

    def test_actor_player_camera_resources_collision_and_model2_are_identical(self) -> None:
        actor_count = struct.unpack_from("<I", self.source_ram, FIELD_NUM_ACTORS)[0]
        actor_base = struct.unpack_from("<I", self.source_ram, FIELD_ACTORS)[0] & 0x1FFFFFFF
        self.assertEqual(
            (actor_count, actor_base),
            (migration.EXPECTED_FIELD_ACTOR_COUNT, migration.EXPECTED_FIELD_ACTORS),
        )
        actor_size = actor_count * FIELD_ACTOR_STRIDE
        self.assertEqual(
            self.output_ram[actor_base : actor_base + actor_size],
            self.source_ram[actor_base : actor_base + actor_size],
        )
        for entity in range(actor_count):
            record = actor_base + entity * FIELD_ACTOR_STRIDE
            pointer = (
                struct.unpack_from(
                    "<I", self.source_ram, record + FIELD_ACTOR_DATA_POINTER
                )[0]
                & 0x1FFFFFFF
            )
            if pointer:
                self.assertEqual(
                    self.output_ram[pointer : pointer + migration.ACTOR_DATA_SIZE],
                    self.source_ram[pointer : pointer + migration.ACTOR_DATA_SIZE],
                )

        preserved = (
            (GAME_STATE, GAMESTATE_SIZE),
            (migration.LOADED_HEADER_OFFSET, migration.LOADED_HEADER_SIZE),
            (migration.RESIDENT_SCRIPT_OFFSET, migration.RESIDENT_SCRIPT_SIZE),
            (migration.RESIDENT_DIALOGUE_OFFSET, migration.RESIDENT_DIALOGUE_SIZE),
            (migration.RESIDENT_WALKMESH_OFFSET, migration.RESIDENT_WALKMESH_SIZE),
            (migration.RUNTIME_MODEL2_OFFSET, migration.RUNTIME_MODEL2_SIZE),
        )
        for offset, size in preserved:
            self.assertEqual(
                self.output_ram[offset : offset + size],
                self.source_ram[offset : offset + size],
            )
        for address in CAMERA_VECTORS.values():
            self.assertEqual(
                self.output_ram[address : address + 16],
                self.source_ram[address : address + 16],
            )
        for _entity, instance, _buffers in migration.MODEL20_INSTANCE_LAYOUT:
            self.assertEqual(
                self.output_ram[instance : instance + 0x2C],
                self.source_ram[instance : instance + 0x2C],
            )
        self.assertTrue(
            self.report["actor_header_game_camera_script_collision_preserved"]
        )
        self.assertTrue(self.report["model2_preserved"])

    def test_wrong_source_disc_and_live_target_fail_closed(self) -> None:
        damaged = bytearray(self.source)
        damaged[-1] ^= 1
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError, "Source Slot 1 identity changed"
        ):
            migration.migrate_v220_slot1_to_v221(
                bytes(damaged),
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                zstd=self.zstd,
            )
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError, "V220 disc identity changed"
        ):
            migration.migrate_v220_slot1_to_v221(
                self.source,
                old_disc=NEW_DISC,
                new_disc=NEW_DISC,
                zstd=self.zstd,
            )

        with tempfile.TemporaryDirectory() as temporary:
            fake_live = (Path(temporary) / "SLUS-00669_1.sav").resolve()
            stderr = io.StringIO()
            with mock.patch.object(migration, "LIVE_SLOT1", fake_live):
                with redirect_stderr(stderr):
                    result = migration.main(
                        (str(SOURCE_STATE), "--output", str(fake_live))
                    )
            self.assertEqual(result, 1)
            self.assertIn("never writes live Slot 1", stderr.getvalue())
            self.assertFalse(fake_live.exists())

            safe_output = Path(temporary) / "candidate.sav"
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                result = migration.main(
                    (
                        str(SOURCE_STATE),
                        "--output",
                        str(safe_output),
                        "--report",
                        str(SOURCE_STATE),
                    )
                )
            self.assertEqual(result, 1)
            self.assertIn("Report must not overwrite source", stderr.getvalue())
            self.assertFalse(safe_output.exists())
            self.assertEqual(SOURCE_STATE.read_bytes(), self.source)


if __name__ == "__main__":
    unittest.main()
