from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

import io
from contextlib import redirect_stderr
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock

import tools.migrate_duckstation_disc_state as media_migration
import tools.migrate_surface_soylent_v219_slot1_to_v220 as migration
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
    / "SLUS-00669_1_v219_latest_camera_glitch_3081ee5d.sav"
)
CANDIDATE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v220_from_3081ee5d_camera_occluder_fix.sav"
)
OLD_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v219.bin"
)
NEW_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v220.bin"
)
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


class SurfaceSoylentV219ToV220StateTests(unittest.TestCase):
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
            raise unittest.SkipTest("Pinned V219/V220 migration fixtures are unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v219_slot1_to_v220(
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
        output_ram_offset, cls.output_ram = migration._ram_from_payload(
            cls.output_payload
        )
        if output_ram_offset != cls.ram_offset:
            raise AssertionError("Serialized RAM moved during migration")

    def test_candidate_identity_media_path_and_round_trip_are_exact(self) -> None:
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

    def test_archive_table_and_geometry_are_the_only_payload_edits(self) -> None:
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

        geometry = migration._geometry_changed_payload_offsets(
            self.source_ram, self.ram_offset
        )
        expected = {
            *(
                table_offset + relative
                for relative, _old, _new in migration.ARCHIVE_TABLE_DIFFS
            ),
            *geometry,
        }
        actual = set(migration._diff_offsets(self.source_payload, self.output_payload))
        self.assertEqual(actual, expected)
        self.assertEqual(len(geometry), migration.EXPECTED_GEOMETRY_BYTES_CHANGED)
        self.assertEqual(len(actual), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        self.assertEqual(
            (migration._sha256(self.output_payload), migration._sha256(self.output_ram)),
            (migration.OUTPUT_PAYLOAD_SHA256, migration.OUTPUT_RAM_SHA256),
        )
        self.assertEqual(self.report["archive_table_bytes_changed"], 2)
        self.assertEqual(self.report["geometry_bytes_changed"], 546)
        self.assertEqual(self.report["payload_bytes_changed"], 548)

    def test_model2_only_loses_flat_black_group_indices(self) -> None:
        before = self.source_ram[
            migration.RUNTIME_MODEL2_OFFSET :
            migration.RUNTIME_MODEL2_OFFSET + migration.RUNTIME_MODEL2_SIZE
        ]
        after = self.output_ram[
            migration.RUNTIME_MODEL2_OFFSET :
            migration.RUNTIME_MODEL2_OFFSET + migration.RUNTIME_MODEL2_SIZE
        ]
        self.assertEqual(
            (migration._sha256(before), migration._sha256(after)),
            (
                migration.SOURCE_RUNTIME_MODEL2_SHA256,
                migration.OUTPUT_RUNTIME_MODEL2_SHA256,
            ),
        )
        expected_model_offsets = {
            relative
            for start, end in migration.MODEL2_ZERO_RANGES
            for relative in range(start, end)
            if before[relative]
        }
        self.assertEqual(
            set(migration._diff_offsets(before, after)), expected_model_offsets
        )
        self.assertEqual(
            len(expected_model_offsets), migration.EXPECTED_MODEL2_BYTES_CHANGED
        )

        model_guest = 0x8010B370
        vertex_offset, normal_offset, mesh_pointer, display_pointer = struct.unpack_from(
            "<4I", after, 0x18
        )
        self.assertEqual(
            (
                vertex_offset - model_guest,
                normal_offset - model_guest,
                mesh_pointer - model_guest,
                display_pointer - model_guest,
            ),
            (0x48, 0x48, 0x6F0, 0xD80),
        )
        self.assertEqual(struct.unpack_from("<HHH", after, 0x12), (213, 210, 4))
        self.assertEqual(
            migration._model_layout(
                after,
                guest_base=migration.RUNTIME_MODEL2_OFFSET,
                expected_size=migration.RUNTIME_MODEL2_SIZE,
                expected_counts=(213, 210, 4),
                expected_offsets=(0x48, 0x48, 0x6F0, 0xD80),
            ),
            migration.MODEL2_EXPECTED_LAYOUT,
        )

        for start, end in migration.MODEL2_ZERO_RANGES:
            self.assertNotEqual(before[start:end], bytes(end - start))
            self.assertEqual(after[start:end], bytes(end - start))
        # The mesh headers, textured group records, and complete display list
        # remain byte-identical.  In particular, the black F3/F4 packets stay
        # allocated even though their index records now have zero area.
        for start, end in ((0x6F0, 0x6F4), (0x714, 0x74C), (0xB7C, 0xD80), (0xD80, len(after))):
            self.assertEqual(after[start:end], before[start:end])
        self.assertEqual(after[0xD80:0xD90], bytes.fromhex("00 00 00 20") * 4)
        self.assertEqual(after[0xDC8:0xFE0], bytes.fromhex("00 00 00 28") * 134)
        self.assertEqual(self.report["model2_bytes_changed"], 546)

    def test_model20_was_already_inert_and_is_preserved_exactly(self) -> None:
        before = self.source_ram[
            migration.RUNTIME_MODEL20_OFFSET :
            migration.RUNTIME_MODEL20_OFFSET + migration.RUNTIME_MODEL20_SIZE
        ]
        after = self.output_ram[
            migration.RUNTIME_MODEL20_OFFSET :
            migration.RUNTIME_MODEL20_OFFSET + migration.RUNTIME_MODEL20_SIZE
        ]
        self.assertEqual(before, after)
        self.assertEqual(
            migration._sha256(after), migration.OUTPUT_RUNTIME_MODEL20_SHA256
        )
        self.assertEqual(struct.unpack_from("<HHH", after, 0x12), (16, 18, 1))
        self.assertEqual(
            migration._model_layout(
                after,
                guest_base=migration.RUNTIME_MODEL20_OFFSET,
                expected_size=migration.RUNTIME_MODEL20_SIZE,
                expected_counts=(16, 18, 1),
                expected_offsets=(0x48, 0x48, 0xC8, 0x14C),
            ),
            migration.MODEL20_EXPECTED_LAYOUT,
        )
        for start, end in migration.MODEL20_ZERO_RANGES:
            self.assertEqual(after[start:end], bytes(end - start))
        self.assertEqual(after[0x14C:], bytes.fromhex("00 00 00 20") * 16)
        self.assertEqual(self.report["model20_bytes_changed"], 0)
        self.assertTrue(self.report["model20_already_inert_and_preserved"])

    def test_actor_header_game_camera_script_and_collision_are_byte_identical(self) -> None:
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
        self.assertTrue(
            self.report["actor_header_game_camera_script_collision_preserved"]
        )

    def test_wrong_source_resource_and_live_target_fail_closed(self) -> None:
        damaged = bytearray(self.source)
        damaged[-1] ^= 1
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError, "Source Slot 1 identity changed"
        ):
            migration.migrate_v219_slot1_to_v220(
                bytes(damaged),
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                zstd=self.zstd,
            )
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError, "V219 disc identity changed"
        ):
            migration.migrate_v219_slot1_to_v220(
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
                    result = migration.main((str(SOURCE_STATE), "--output", str(fake_live)))
            self.assertEqual(result, 1)
            self.assertIn("never writes live Slot 1", stderr.getvalue())
            self.assertFalse(fake_live.exists())


if __name__ == "__main__":
    unittest.main()
