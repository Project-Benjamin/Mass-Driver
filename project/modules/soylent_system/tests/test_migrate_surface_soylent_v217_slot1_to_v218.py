from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

import struct
import unittest
from pathlib import Path

import tools.migrate_duckstation_disc_state as media_migration
import tools.migrate_surface_soylent_v217_slot1_to_v218 as migration
from work.read_duckstation_runtime import (
    CAMERA_VECTORS,
    FIELD_ACTORS,
    FIELD_ACTOR_STRIDE,
    GAME_STATE,
    RAM_SIZE,
    _psx_ram_offset,
)


PROJECT_ROOT = REPOSITORY_ROOT
SOURCE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_backups"
    / "SLUS-00669_1_v217_door_outline_e8bcc431.sav"
)
OLD_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v217.bin"
)
NEW_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v218.bin"
)
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


class SurfaceSoylentV217ToV218StateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (SOURCE_STATE, OLD_DISC, NEW_DISC, ZSTD)
        if not all(path.is_file() for path in required):
            raise unittest.SkipTest("Pinned V217/V218 state fixtures are unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v217_slot1_to_v218(
            cls.source,
            old_disc=OLD_DISC,
            new_disc=NEW_DISC,
            zstd=cls.zstd,
        )
        cls.source_prefix, cls.source_payload, _ = migration._decode_state(
            cls.source, cls.zstd
        )
        cls.output_prefix, cls.output_payload, _ = migration._decode_state(
            cls.result, cls.zstd
        )

    def test_candidate_identity_and_media_path_are_exact(self) -> None:
        self.assertEqual(
            (len(self.result), migration._sha256(self.result)),
            (migration.OUTPUT_STATE_SIZE, migration.OUTPUT_STATE_SHA256),
        )
        self.assertEqual(
            migration._sha256(self.output_payload),
            migration.OUTPUT_PAYLOAD_SHA256,
        )
        self.assertEqual(
            bytes(self.output_prefix).count(migration.NEW_CUE_NAME.encode("ascii")),
            1,
        )
        self.assertNotIn(
            migration.OLD_CUE_NAME.encode("ascii"), bytes(self.output_prefix)
        )
        self.assertFalse(self.report["media"]["resident_archive_table_changed"])

    def test_only_geometry_changes_in_payload(self) -> None:
        source_ram_offset = _psx_ram_offset(self.source_payload)
        output_ram_offset = _psx_ram_offset(self.output_payload)
        self.assertEqual(source_ram_offset, output_ram_offset)
        changed = {
            index
            for index, (before, after) in enumerate(
                zip(self.source_payload, self.output_payload, strict=True)
            )
            if before != after
        }
        expected = {
            *(
                source_ram_offset + migration.RUNTIME_MODEL_OFFSET + offset
                for offset, _old, _new in migration.GEOMETRY_BYTE_EDITS
            ),
        }
        self.assertEqual(changed, expected)
        self.assertEqual(len(changed), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)

    def test_resident_actor_pointers_are_preserved_and_raw_plate_is_current(self) -> None:
        ram_offset = _psx_ram_offset(self.output_payload)
        ram = self.output_payload[ram_offset : ram_offset + RAM_SIZE]
        actor_offset = struct.unpack_from("<I", ram, FIELD_ACTORS)[0] & 0x1FFFFFFF
        for entity, pointer, source_hash in zip(
            migration.STATIC_BACKER_ENTITIES,
            migration.STATIC_BACKER_MODEL_POINTERS,
            migration.STATIC_BACKER_RECORD_SHA256S,
            strict=True,
        ):
            record = ram[
                actor_offset + entity * FIELD_ACTOR_STRIDE :
                actor_offset + (entity + 1) * FIELD_ACTOR_STRIDE
            ]
            self.assertEqual(struct.unpack_from("<I", record)[0], pointer)
            self.assertEqual(migration._sha256(record), source_hash)
        model = ram[
            migration.RUNTIME_MODEL_OFFSET :
            migration.RUNTIME_MODEL_OFFSET + migration.RUNTIME_MODEL_SIZE
        ]
        self.assertEqual(migration._sha256(model), migration.OUTPUT_RUNTIME_MODEL_SHA256)

    def test_player_gamestate_and_camera_are_byte_identical(self) -> None:
        ram_offset = _psx_ram_offset(self.source_payload)
        before = self.source_payload[ram_offset : ram_offset + RAM_SIZE]
        after = self.output_payload[ram_offset : ram_offset + RAM_SIZE]
        self.assertEqual(
            before[GAME_STATE : GAME_STATE + 0x3000],
            after[GAME_STATE : GAME_STATE + 0x3000],
        )
        for address in CAMERA_VECTORS.values():
            self.assertEqual(before[address : address + 12], after[address : address + 12])

    def test_wrong_source_state_fails_closed(self) -> None:
        damaged = bytearray(self.source)
        damaged[-1] ^= 1
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError, "Source Slot 1 identity changed"
        ):
            migration.migrate_v217_slot1_to_v218(
                bytes(damaged),
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                zstd=self.zstd,
            )


if __name__ == "__main__":
    unittest.main()
