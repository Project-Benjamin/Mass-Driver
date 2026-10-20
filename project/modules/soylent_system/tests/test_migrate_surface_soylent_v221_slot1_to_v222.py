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
import tools.migrate_surface_soylent_v221_slot1_to_v222 as migration
from tools.xgdeathblows import GAMESTATE_SIZE
from work.read_duckstation_runtime import (
    CAMERA_VECTORS,
    FIELD_ACTOR_DATA_POINTER,
    FIELD_ACTOR_STRIDE,
    GAME_STATE,
)


PROJECT_ROOT = REPOSITORY_ROOT
SOURCE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v221_from_e4aea385_native_threshold_aprons.sav"
)
CANDIDATE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v222_from_27710b20_flush_doors.sav"
)
CANDIDATE_REPORT = CANDIDATE_STATE.with_suffix(".json")
OLD_DISC = PROJECT_ROOT / "output" / migration.OLD_CUE_NAME.replace(".cue", ".bin")
NEW_DISC = PROJECT_ROOT / "output" / migration.NEW_CUE_NAME.replace(".cue", ".bin")
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


class SurfaceSoylentV221ToV222StateTests(unittest.TestCase):
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
            raise unittest.SkipTest("Pinned V221/V222 migration fixtures are unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v221_slot1_to_v222(
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
        cls.old_field = migration._disc_field621(
            OLD_DISC,
            bundle_size=migration.OLD_FIELD621_BUNDLE_SIZE,
            bundle_sha256=migration.OLD_FIELD621_BUNDLE_SHA256,
        )
        cls.new_field = migration._disc_field621(
            NEW_DISC,
            bundle_size=migration.NEW_FIELD621_BUNDLE_SIZE,
            bundle_sha256=migration.NEW_FIELD621_BUNDLE_SHA256,
        )

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
                self.source_prefix, compressed_size=migration.OUTPUT_COMPRESSED_SIZE
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

    def test_finished_media_supplies_exact_header_and_atel_delta(self) -> None:
        self.assertEqual(
            migration._diff_triplets(self.old_field.header, self.new_field.header),
            migration.FIELD_HEADER_DIFF_TRIPLETS,
        )
        self.assertEqual(
            (
                migration._sha256(self.old_field.header),
                migration._sha256(self.new_field.header),
            ),
            (migration.OLD_DISK_HEADER_SHA256, migration.NEW_DISK_HEADER_SHA256),
        )
        old_script = self.old_field.parts[5].data
        new_script = self.new_field.parts[5].data
        self.assertEqual(
            (migration._sha256(old_script), migration._sha256(new_script)),
            (migration.OLD_SCRIPT_SHA256, migration.NEW_SCRIPT_SHA256),
        )
        self.assertEqual(
            len(migration._diff_offsets(old_script, new_script)),
            migration.EXPECTED_SCRIPT_BYTES_CHANGED,
        )
        for entity, relative, size, source_hash, target_hash in migration.SCRIPT_ROUTINES:
            with self.subTest(entity=entity):
                self.assertEqual(
                    (
                        migration._sha256(old_script[relative : relative + size]),
                        migration._sha256(new_script[relative : relative + size]),
                    ),
                    (source_hash, target_hash),
                )
        for index in range(9):
            if index != 5:
                self.assertEqual(
                    self.old_field.parts[index].data, self.new_field.parts[index].data
                )

    def test_all_serialized_door_transform_mirrors_are_updated(self) -> None:
        loaded_header = self.output_ram[
            migration.LOADED_HEADER_OFFSET :
            migration.LOADED_HEADER_OFFSET + migration.FIELD_HEADER_SIZE
        ]
        self.assertEqual(
            migration._sha256(loaded_header), migration.TARGET_LOADED_HEADER_SHA256
        )
        for entity, (_source, target) in migration.HEADER_RECORDS.items():
            start = migration.HEADER_RECORD_OFFSET + entity * migration.HEADER_RECORD_SIZE
            self.assertEqual(
                loaded_header[start : start + migration.HEADER_RECORD_SIZE], target
            )
        self.assertEqual(
            self.output_ram[
                migration.RESIDENT_SCRIPT_OFFSET :
                migration.RESIDENT_SCRIPT_OFFSET + migration.RESIDENT_SCRIPT_SIZE
            ],
            self.new_field.parts[5].data,
        )

        for entity, position in migration.DYNAMIC_PLACEMENTS.items():
            actor = migration.EXPECTED_FIELD_ACTORS + entity * FIELD_ACTOR_STRIDE
            for translation in (0x20, 0x40):
                self.assertEqual(
                    struct.unpack_from("<3i", self.output_ram, actor + translation),
                    position,
                )
            actor_data, sprite = migration.ACTOR_DATA_LAYOUT[entity]
            self.assertEqual(
                struct.unpack_from(
                    "<3i",
                    self.output_ram,
                    actor_data + migration.ACTOR_DATA_POSITION_OFFSET,
                ),
                tuple(value << 16 for value in position),
            )
            self.assertEqual(
                struct.unpack_from(
                    "<3h",
                    self.output_ram,
                    actor_data + migration.ACTOR_DATA_OLD_POSITION_OFFSET,
                ),
                position,
            )
            self.assertEqual(
                struct.unpack_from("<3i", self.output_ram, sprite),
                tuple(value << 16 for value in position),
            )

        for entity, (matrix, position, yaw) in migration.STATIC_PLACEMENTS.items():
            actor = migration.EXPECTED_FIELD_ACTORS + entity * FIELD_ACTOR_STRIDE
            for matrix_offset, translation_offset in ((0x0C, 0x20), (0x2C, 0x40)):
                self.assertEqual(
                    struct.unpack_from("<9h", self.output_ram, actor + matrix_offset),
                    matrix,
                )
                self.assertEqual(
                    struct.unpack_from("<3i", self.output_ram, actor + translation_offset),
                    position,
                )
            self.assertEqual(struct.unpack_from("<h", self.output_ram, actor + 0x52)[0], yaw)

    def test_exact_204_byte_payload_whitelist_and_unchanged_archive_table(self) -> None:
        rebuilt_ram, categories = migration._build_target_ram(
            self.source_ram, old_field=self.old_field, new_field=self.new_field
        )
        self.assertEqual(rebuilt_ram, self.output_ram)
        self.assertEqual(
            {name: len(offsets) for name, offsets in categories.items()},
            {
                "header": 14,
                "script": 129,
                "actors": 49,
                "actor_data": 8,
                "sprites": 4,
            },
        )
        expected_ram = frozenset().union(*categories.values())
        self.assertEqual(len(expected_ram), migration.EXPECTED_RAM_BYTES_CHANGED)
        self.assertEqual(
            frozenset(migration._diff_offsets(self.source_ram, self.output_ram)),
            expected_ram,
        )
        expected_payload = {
            self.ram_offset + relative for relative in expected_ram
        }
        self.assertEqual(
            set(migration._diff_offsets(self.source_payload, self.output_payload)),
            expected_payload,
        )
        self.assertEqual(len(expected_payload), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        self.assertEqual(
            (migration._sha256(self.output_payload), migration._sha256(self.output_ram)),
            (migration.OUTPUT_PAYLOAD_SHA256, migration.OUTPUT_RAM_SHA256),
        )

        old_table = media_migration._archive_table(OLD_DISC)
        new_table = media_migration._archive_table(NEW_DISC)
        self.assertEqual(old_table, new_table)
        self.assertEqual(migration._sha256(old_table), migration.ARCHIVE_TABLE_SHA256)
        table_offset, volatile = media_migration._find_resident_archive_table(
            self.source_payload, old_table
        )
        self.assertEqual(
            (table_offset, volatile),
            (migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET, 1),
        )
        source_resident = self.source_payload[
            table_offset : table_offset + migration.ARCHIVE_TABLE_SIZE
        ]
        output_resident = self.output_payload[
            table_offset : table_offset + migration.ARCHIVE_TABLE_SIZE
        ]
        self.assertEqual(output_resident, source_resident)
        self.assertEqual(
            migration._sha256(output_resident), migration.RESIDENT_ARCHIVE_TABLE_SHA256
        )
        self.assertEqual(output_resident[-1], migration.EXPECTED_VOLATILE_TABLE_VALUE)
        self.assertEqual(self.report["archive_table_bytes_changed"], 0)

    def test_player_camera_collision_models_and_other_actors_are_preserved(self) -> None:
        preserved = (
            (GAME_STATE, GAMESTATE_SIZE),
            (migration.RESIDENT_DIALOGUE_OFFSET, migration.RESIDENT_DIALOGUE_SIZE),
            (migration.RESIDENT_WALKMESH_OFFSET, migration.RESIDENT_WALKMESH_SIZE),
            (migration.RUNTIME_MODEL2_OFFSET, migration.RUNTIME_MODEL2_SIZE),
            (migration.RUNTIME_MODEL20_OFFSET, migration.RUNTIME_MODEL20_SIZE),
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
        self.assertEqual(
            migration._packet_arenas(self.output_ram),
            migration._packet_arenas(self.source_ram),
        )

        changed_actors = set(migration.DYNAMIC_PLACEMENTS) | set(migration.STATIC_PLACEMENTS)
        for entity in range(migration.EXPECTED_FIELD_ACTOR_COUNT):
            if entity in changed_actors:
                continue
            actor = migration.EXPECTED_FIELD_ACTORS + entity * FIELD_ACTOR_STRIDE
            self.assertEqual(
                self.output_ram[actor : actor + FIELD_ACTOR_STRIDE],
                self.source_ram[actor : actor + FIELD_ACTOR_STRIDE],
            )
        for entity in range(migration.EXPECTED_FIELD_ACTOR_COUNT):
            actor = migration.EXPECTED_FIELD_ACTORS + entity * FIELD_ACTOR_STRIDE
            pointer = (
                struct.unpack_from(
                    "<I", self.source_ram, actor + FIELD_ACTOR_DATA_POINTER
                )[0]
                & 0x1FFFFFFF
            )
            if pointer and entity not in migration.DYNAMIC_PLACEMENTS:
                self.assertEqual(
                    self.output_ram[pointer : pointer + migration.ACTOR_DATA_SIZE],
                    self.source_ram[pointer : pointer + migration.ACTOR_DATA_SIZE],
                )
        self.assertTrue(
            self.report["game_camera_dialogue_walkmesh_models_preserved"]
        )
        self.assertTrue(self.report["model20_packet_arenas_preserved"])

    def test_wrong_source_disc_and_live_target_fail_closed(self) -> None:
        damaged = bytearray(self.source)
        damaged[-1] ^= 1
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError, "Source Slot 1 identity changed"
        ):
            migration.migrate_v221_slot1_to_v222(
                bytes(damaged), old_disc=OLD_DISC, new_disc=NEW_DISC, zstd=self.zstd
            )
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError, "V221 disc identity changed"
        ):
            migration.migrate_v221_slot1_to_v222(
                self.source, old_disc=NEW_DISC, new_disc=NEW_DISC, zstd=self.zstd
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
