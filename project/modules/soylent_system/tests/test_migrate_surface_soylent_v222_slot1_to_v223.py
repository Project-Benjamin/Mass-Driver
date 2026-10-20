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
import tools.migrate_surface_soylent_v222_slot1_to_v223 as migration
from tools.xgdeathblows import GAMESTATE_SIZE
from work.read_duckstation_runtime import (
    CAMERA_VECTORS,
    FIELD_ACTORS,
    FIELD_ACTOR_STRIDE,
    FIELD_NUM_ACTORS,
    GAME_STATE,
)


PROJECT_ROOT = REPOSITORY_ROOT
SOURCE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_backups"
    / "SLUS-00669_1_v222_bottom_left_clip_a714c8e8.sav"
)
CANDIDATE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v223_from_a714c8e8_threshold_uv.sav"
)
CANDIDATE_REPORT = CANDIDATE_STATE.with_suffix(".json")
OLD_DISC = PROJECT_ROOT / "output" / migration.OLD_CUE_NAME.replace(".cue", ".bin")
NEW_DISC = PROJECT_ROOT / "output" / migration.NEW_CUE_NAME.replace(".cue", ".bin")
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


class SurfaceSoylentV222ToV223StateTests(unittest.TestCase):
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
            raise unittest.SkipTest("Pinned V222/V223 migration fixtures are unavailable")

        cls.source = SOURCE_STATE.read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v222_slot1_to_v223(
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

        cls.old_field, cls.old_models, cls.old_disk_model = migration._disc_field621(
            OLD_DISC,
            bundle_size=migration.OLD_FIELD621_BUNDLE_SIZE,
            bundle_sha256=migration.OLD_FIELD621_BUNDLE_SHA256,
            header_sha256=migration.OLD_DISK_HEADER_SHA256,
            model_archive_sha256=migration.OLD_FIELD621_MODEL_ARCHIVE_SHA256,
            model20_sha256=migration.OLD_DISK_MODEL20_SHA256,
        )
        cls.new_field, cls.new_models, cls.new_disk_model = migration._disc_field621(
            NEW_DISC,
            bundle_size=migration.NEW_FIELD621_BUNDLE_SIZE,
            bundle_sha256=migration.NEW_FIELD621_BUNDLE_SHA256,
            header_sha256=migration.NEW_DISK_HEADER_SHA256,
            model_archive_sha256=migration.NEW_FIELD621_MODEL_ARCHIVE_SHA256,
            model20_sha256=migration.NEW_DISK_MODEL20_SHA256,
        )
        cls.old_runtime_model = migration._runtime_model20(cls.old_disk_model)
        cls.target_runtime_model = migration._runtime_model20(cls.new_disk_model)

    def test_candidate_identity_prefix_report_and_round_trip_are_exact(self) -> None:
        self.assertEqual(
            (len(self.source), migration._sha256(self.source)),
            (migration.SOURCE_STATE_SIZE, migration.SOURCE_STATE_SHA256),
        )
        self.assertEqual(
            (len(self.result), migration._sha256(self.result)),
            (migration.OUTPUT_STATE_SIZE, migration.OUTPUT_STATE_SHA256),
        )
        self.assertEqual(
            (
                self.source_frame_start,
                len(self.source) - self.source_frame_start,
                migration._sha256(self.source[self.source_frame_start :]),
            ),
            (
                migration.SOURCE_PREFIX_SIZE,
                migration.SOURCE_COMPRESSED_SIZE,
                migration.SOURCE_COMPRESSED_SHA256,
            ),
        )
        self.assertEqual(
            (
                self.output_frame_start,
                len(self.result) - self.output_frame_start,
                migration._sha256(self.result[self.output_frame_start :]),
            ),
            (
                migration.SOURCE_PREFIX_SIZE,
                migration.OUTPUT_COMPRESSED_SIZE,
                migration.OUTPUT_COMPRESSED_SHA256,
            ),
        )
        self.assertEqual(
            self.output_payload,
            self.zstd.decompress(self.result[self.output_frame_start :]),
        )
        expected_prefix = migration._expected_prefix(
            self.source_prefix, compressed_size=migration.OUTPUT_COMPRESSED_SIZE
        )
        self.assertEqual(self.output_prefix, expected_prefix)
        self.assertEqual(
            migration._sha256(self.output_prefix), migration.OUTPUT_PREFIX_SHA256
        )
        self.assertEqual(
            len(migration._diff_offsets(self.source_prefix, self.output_prefix)),
            migration.EXPECTED_PREFIX_BYTES_CHANGED,
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

    def test_finished_media_is_the_pinned_uv_only_field_change(self) -> None:
        old_table = media_migration._archive_table(OLD_DISC)
        new_table = media_migration._archive_table(NEW_DISC)
        self.assertEqual(
            (migration._sha256(old_table), migration._sha256(new_table)),
            (
                migration.OLD_ARCHIVE_TABLE_SHA256,
                migration.NEW_ARCHIVE_TABLE_SHA256,
            ),
        )
        self.assertEqual(
            migration._diff_triplets(old_table, new_table),
            migration.MEDIA_ARCHIVE_TABLE_DIFFS,
        )
        self.assertEqual(
            migration._diff_triplets(self.old_field.header, self.new_field.header),
            migration.FIELD_HEADER_DIFF_TRIPLETS,
        )
        self.assertEqual(
            migration._diff_triplets(self.old_models, self.new_models),
            migration.MODEL_ARCHIVE_DIFF_TRIPLETS,
        )
        self.assertEqual(
            migration._diff_triplets(self.old_disk_model, self.new_disk_model),
            migration.MODEL20_UV_DIFF_TRIPLETS,
        )
        for index in range(9):
            if index == migration.FIELD621_MODEL_COMPONENT_INDEX:
                continue
            self.assertEqual(
                self.old_field.parts[index].data,
                self.new_field.parts[index].data,
                f"field component {index}",
            )
        self.assertEqual(
            migration._sha256(self.new_field.parts[5].data),
            migration.DISK_SCRIPT_SHA256,
        )
        self.assertEqual(
            migration._model_layout(
                self.old_disk_model,
                guest_base=0,
                expected_counts=migration.MODEL20_DISK_COUNTS,
            ),
            migration.MODEL20_INVENTORY,
        )
        self.assertEqual(
            migration._model_layout(
                self.new_disk_model,
                guest_base=0,
                expected_counts=migration.MODEL20_DISK_COUNTS,
            ),
            migration.MODEL20_INVENTORY,
        )
        self.assertEqual(
            migration._diff_triplets(
                self.old_runtime_model, self.target_runtime_model
            ),
            migration.MODEL20_UV_DIFF_TRIPLETS,
        )

    def test_exact_28_byte_payload_and_ram_whitelist(self) -> None:
        rebuilt_ram, categories = migration._build_target_ram(
            self.source_ram,
            old_runtime_model=self.old_runtime_model,
            target_runtime_model=self.target_runtime_model,
        )
        self.assertEqual(rebuilt_ram, self.output_ram)
        self.assertEqual(
            {name: len(offsets) for name, offsets in categories.items()},
            {"model20_uv": 4, "packet_arena_uv": 24},
        )
        expected_ram = frozenset().union(*categories.values())
        self.assertEqual(len(expected_ram), migration.EXPECTED_RAM_BYTES_CHANGED)
        self.assertEqual(
            frozenset(migration._diff_offsets(self.source_ram, self.output_ram)),
            expected_ram,
        )
        expected_payload = frozenset(
            self.ram_offset + relative for relative in expected_ram
        )
        self.assertEqual(
            frozenset(
                migration._diff_offsets(self.source_payload, self.output_payload)
            ),
            expected_payload,
        )
        self.assertEqual(
            (migration._sha256(self.output_payload), migration._sha256(self.output_ram)),
            (migration.OUTPUT_PAYLOAD_SHA256, migration.OUTPUT_RAM_SHA256),
        )
        self.assertEqual(self.report["payload_bytes_changed"], 28)
        self.assertEqual(self.report["ram_bytes_changed"], 28)
        self.assertEqual(self.report["model20_uv_bytes_changed"], 4)
        self.assertEqual(self.report["packet_arena_uv_bytes_changed"], 24)

    def test_resident_model_and_all_six_packet_buffers_receive_only_uv_patch(self) -> None:
        source_model = self.source_ram[
            migration.RUNTIME_MODEL20_OFFSET :
            migration.RUNTIME_MODEL20_OFFSET + migration.RUNTIME_MODEL20_SIZE
        ]
        output_model = self.output_ram[
            migration.RUNTIME_MODEL20_OFFSET :
            migration.RUNTIME_MODEL20_OFFSET + migration.RUNTIME_MODEL20_SIZE
        ]
        self.assertEqual(source_model, self.old_runtime_model)
        self.assertEqual(output_model, self.target_runtime_model)
        self.assertEqual(
            migration._diff_triplets(source_model, output_model),
            migration.MODEL20_UV_DIFF_TRIPLETS,
        )
        self.assertEqual(
            migration._sha256(output_model), migration.TARGET_RUNTIME_MODEL20_SHA256
        )

        source_offsets = migration._packet_arena_offsets(
            self.source_ram, expected_hashes=migration.SOURCE_PACKET_ARENA_SHA256
        )
        output_offsets = migration._packet_arena_offsets(
            self.output_ram, expected_hashes=migration.TARGET_PACKET_ARENA_SHA256
        )
        self.assertEqual(source_offsets, output_offsets)
        self.assertEqual(len(source_offsets), migration.EXPECTED_PACKET_ARENA_COUNT)
        for arena_offset in source_offsets:
            with self.subTest(arena=hex(arena_offset)):
                source_arena = self.source_ram[
                    arena_offset : arena_offset + migration.RUNTIME_MODEL20_ARENA_SIZE
                ]
                output_arena = self.output_ram[
                    arena_offset : arena_offset + migration.RUNTIME_MODEL20_ARENA_SIZE
                ]
                self.assertEqual(
                    migration._diff_triplets(source_arena, output_arena),
                    migration.PACKET_ARENA_UV_DIFF_TRIPLETS,
                )
        self.assertEqual(
            migration._sha256(migration._packet_arenas(self.source_ram)),
            migration.SOURCE_PACKET_ARENAS_SHA256,
        )
        self.assertEqual(
            migration._sha256(migration._packet_arenas(self.output_ram)),
            migration.TARGET_PACKET_ARENAS_SHA256,
        )
        self.assertEqual(self.report["packet_arena_count"], 6)
        self.assertEqual(self.report["packet_arena_uv_bytes_changed_each"], 4)
        self.assertTrue(self.report["model20_topology_and_allocation_preserved"])
        self.assertTrue(self.report["packet_arena_allocations_preserved"])

    def test_header_scripts_actors_collision_player_camera_and_archive_are_preserved(self) -> None:
        preserved = (
            (GAME_STATE, GAMESTATE_SIZE),
            (migration.LOADED_HEADER_OFFSET, migration.FIELD_HEADER_SIZE),
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
        self.assertEqual(
            migration._sha256(
                self.output_ram[
                    migration.LOADED_HEADER_OFFSET :
                    migration.LOADED_HEADER_OFFSET + migration.FIELD_HEADER_SIZE
                ]
            ),
            migration.LOADED_HEADER_SHA256,
        )
        for address in CAMERA_VECTORS.values():
            self.assertEqual(
                self.output_ram[address : address + 16],
                self.source_ram[address : address + 16],
            )

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
        self.assertEqual(
            migration._actor_data_snapshot(self.output_ram, actor_base, actor_count),
            migration._actor_data_snapshot(self.source_ram, actor_base, actor_count),
        )

        old_table = media_migration._archive_table(OLD_DISC)
        table_offset, volatile = media_migration._find_resident_archive_table(
            self.source_payload, old_table
        )
        self.assertEqual(
            (table_offset, volatile),
            (
                migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET,
                migration.EXPECTED_ARCHIVE_TABLE_VOLATILE_BYTES,
            ),
        )
        source_table = self.source_payload[
            table_offset : table_offset + migration.ARCHIVE_TABLE_SIZE
        ]
        output_table = self.output_payload[
            table_offset : table_offset + migration.ARCHIVE_TABLE_SIZE
        ]
        self.assertEqual(output_table, source_table)
        self.assertEqual(
            migration._sha256(output_table), migration.RESIDENT_ARCHIVE_TABLE_SHA256
        )
        self.assertEqual(output_table[-1], migration.EXPECTED_VOLATILE_TABLE_VALUE)
        self.assertEqual(self.report["resident_archive_table_bytes_changed"], 0)
        self.assertTrue(self.report["resident_archive_table_preserved"])
        self.assertTrue(self.report["field_header_scripts_actors_collision_preserved"])
        self.assertTrue(self.report["player_and_camera_preserved"])

    def test_migration_is_deterministic(self) -> None:
        second_result, second_report = migration.migrate_v222_slot1_to_v223(
            self.source,
            old_disc=OLD_DISC,
            new_disc=NEW_DISC,
            zstd=self.zstd,
        )
        self.assertEqual(second_result, self.result)
        self.assertEqual(second_report, self.report)

    def test_wrong_source_disc_runtime_and_live_target_fail_closed(self) -> None:
        damaged_state = bytearray(self.source)
        damaged_state[-1] ^= 1
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError, "Source Slot 1 identity changed"
        ):
            migration.migrate_v222_slot1_to_v223(
                bytes(damaged_state), old_disc=OLD_DISC, new_disc=NEW_DISC, zstd=self.zstd
            )
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError, "V222 disc identity changed"
        ):
            migration.migrate_v222_slot1_to_v223(
                self.source, old_disc=NEW_DISC, new_disc=NEW_DISC, zstd=self.zstd
            )

        damaged_ram = bytearray(self.source_ram)
        first_arena = migration.MODEL20_INSTANCE_LAYOUT[0][2][0]
        damaged_ram[first_arena + migration.PACKET_ARENA_UV_DIFF_TRIPLETS[0][0]] ^= 1
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError,
            "packet-arena identities changed",
        ):
            migration._build_target_ram(
                bytes(damaged_ram),
                old_runtime_model=self.old_runtime_model,
                target_runtime_model=self.target_runtime_model,
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
