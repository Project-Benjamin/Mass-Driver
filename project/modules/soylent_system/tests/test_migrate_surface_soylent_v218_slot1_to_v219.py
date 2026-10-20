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
import tools.migrate_surface_soylent_v218_slot1_to_v219 as migration
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
    / "SLUS-00669_1_v218_black_wall_f2c08418.sav"
)
CANDIDATE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v219_from_f2c08418_black_wall_fix.sav"
)
OLD_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v218.bin"
)
NEW_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v219.bin"
)
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


class SurfaceSoylentV218ToV219StateTests(unittest.TestCase):
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
            raise unittest.SkipTest("Pinned V218/V219 migration fixtures are unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v218_slot1_to_v219(
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
        _output_ram_offset, cls.output_ram = migration._ram_from_payload(
            cls.output_payload
        )

    def test_candidate_identity_media_path_and_round_trip_are_exact(self) -> None:
        self.assertEqual(
            (len(self.result), migration._sha256(self.result)),
            (migration.OUTPUT_STATE_SIZE, migration.OUTPUT_STATE_SHA256),
        )
        self.assertEqual(
            (len(self.result) - self.output_frame_start, self.output_frame_start),
            (migration.OUTPUT_COMPRESSED_SIZE, migration.SOURCE_PREFIX_SIZE),
        )
        self.assertEqual(self.output_payload, self.zstd.decompress(self.result[self.output_frame_start :]))
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
        self.assertTrue(self.report["round_trip_verified"])
        if CANDIDATE_STATE.is_file():
            self.assertEqual(CANDIDATE_STATE.read_bytes(), self.result)

    def test_archive_table_and_geometry_have_the_only_payload_edits(self) -> None:
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

        expected = {
            *(
                table_offset + relative
                for relative, _old, _new in migration.ARCHIVE_TABLE_DIFFS
            ),
            *(
                self.ram_offset + migration.RUNTIME_MODEL_OFFSET + relative
                for relative, _old, _new in migration.GEOMETRY_BYTE_EDITS
            ),
        }
        actual = set(migration._diff_offsets(self.source_payload, self.output_payload))
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        self.assertEqual(
            self.report["payload_bytes_changed"], migration.EXPECTED_PAYLOAD_BYTES_CHANGED
        )
        self.assertEqual(self.report["archive_table_bytes_changed"], 1)
        self.assertEqual(self.report["geometry_bytes_changed"], 16)

    def test_resident_model_is_one_sided_without_relocation(self) -> None:
        before = self.source_ram[
            migration.RUNTIME_MODEL_OFFSET :
            migration.RUNTIME_MODEL_OFFSET + migration.RUNTIME_MODEL_SIZE
        ]
        after = self.output_ram[
            migration.RUNTIME_MODEL_OFFSET :
            migration.RUNTIME_MODEL_OFFSET + migration.RUNTIME_MODEL_SIZE
        ]
        self.assertEqual(
            migration._sha256(before), migration.SOURCE_RUNTIME_MODEL_SHA256
        )
        self.assertEqual(
            migration._sha256(after), migration.OUTPUT_RUNTIME_MODEL_SHA256
        )
        expected_model_offsets = {
            relative for relative, _old, _new in migration.GEOMETRY_BYTE_EDITS
        }
        self.assertEqual(set(migration._diff_offsets(before, after)), expected_model_offsets)

        model_guest = 0x80110A18
        mesh_offset = (struct.unpack_from("<I", after, 0x20)[0] - model_guest)
        display_offset = (struct.unpack_from("<I", after, 0x24)[0] - model_guest)
        self.assertEqual((mesh_offset, display_offset), (0xC8, 0x14C))
        self.assertEqual(struct.unpack_from("<BBH", after, mesh_offset), (0x04, 0x77, 16))
        triangles = tuple(
            struct.unpack_from("<HHHH", after, mesh_offset + 4 + index * 8)
            for index in range(16)
        )
        for rectangle in range(4):
            base = rectangle * 4
            self.assertEqual(
                triangles[rectangle * 4 : rectangle * 4 + 4],
                (
                    (base, base + 1, base + 2, 0),
                    (base + 1, base + 3, base + 2, 0),
                    (base, base + 1, base + 2, 0),
                    (base + 1, base + 3, base + 2, 0),
                ),
            )
        self.assertEqual(after[display_offset:], bytes.fromhex("00 00 00 20") * 16)

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
            migration.migrate_v218_slot1_to_v219(
                bytes(damaged),
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                zstd=self.zstd,
            )
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError, "V218 disc identity changed"
        ):
            migration.migrate_v218_slot1_to_v219(
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
