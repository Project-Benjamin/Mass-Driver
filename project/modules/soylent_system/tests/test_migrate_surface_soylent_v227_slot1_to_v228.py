from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

from contextlib import redirect_stderr
import hashlib
import io
import json
from pathlib import Path
import struct
import unittest

import tools.migrate_duckstation_disc_state as media_migration
import tools.migrate_surface_soylent_v227_slot1_to_v228 as migration
from tools.xgdeathblows import GAMESTATE_SIZE
from work.read_duckstation_runtime import (
    CAMERA_VECTORS,
    FIELD_ACTORS,
    FIELD_ACTOR_DATA_POINTER,
    FIELD_ACTOR_STRIDE,
    FIELD_SCRIPT_MEMORY,
    GAME_STATE,
)


PROJECT_ROOT = REPOSITORY_ROOT
SOURCE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v227_from_9436ef84_treatment_preparation.sav"
)
CANDIDATE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v228_from_23221b34_clinic_aid.sav"
)
CANDIDATE_REPORT = CANDIDATE_STATE.with_suffix(".json")
OLD_DISC = PROJECT_ROOT / "output" / "Xenogears_PW_CD2_mass_driver_surface_soylent_v227.bin"
NEW_DISC = PROJECT_ROOT / "output" / "Xenogears_PW_CD2_mass_driver_surface_soylent_v228.bin"
OLD_STAGE = PROJECT_ROOT / "work" / "surface_soylent_campaign_v227_stage"
NEW_STAGE = PROJECT_ROOT / "work" / "surface_soylent_campaign_v228_stage"
OLD_FIELD = OLD_STAGE / "clones" / "field_621"
NEW_FIELD = NEW_STAGE / "clones" / "field_621"
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SurfaceSoylentV227Slot1MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (
            SOURCE_STATE,
            OLD_DISC,
            NEW_DISC,
            OLD_DISC.with_suffix(".cue"),
            NEW_DISC.with_suffix(".cue"),
            OLD_STAGE / "manifest.json",
            NEW_STAGE / "manifest.json",
            OLD_FIELD / "header.bin",
            NEW_FIELD / "header.bin",
            OLD_FIELD / "05_scripts.bin",
            NEW_FIELD / "05_scripts.bin",
            ZSTD,
        )
        if not all(path.is_file() for path in required):
            raise unittest.SkipTest("Pinned V227/V228 migration fixtures unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.old_manifest = (OLD_STAGE / "manifest.json").read_bytes()
        cls.new_manifest = (NEW_STAGE / "manifest.json").read_bytes()
        cls.old_header = (OLD_FIELD / "header.bin").read_bytes()
        cls.new_header = (NEW_FIELD / "header.bin").read_bytes()
        cls.old_script = (OLD_FIELD / "05_scripts.bin").read_bytes()
        cls.new_script = (NEW_FIELD / "05_scripts.bin").read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v227_slot1_to_v228(
            cls.source,
            old_disc=OLD_DISC,
            new_disc=NEW_DISC,
            old_manifest=cls.old_manifest,
            new_manifest=cls.new_manifest,
            old_header=cls.old_header,
            new_header=cls.new_header,
            old_script=cls.old_script,
            new_script=cls.new_script,
            zstd=cls.zstd,
        )
        cls.source_payload, cls.source_frame, cls.source_prefix = migration._unpack_state(cls.source, cls.zstd)
        cls.result_payload, cls.result_frame, cls.result_prefix = migration._unpack_state(cls.result, cls.zstd)
        _offset, cls.source_ram = migration._ram_from_payload(cls.source_payload)
        _offset, cls.result_ram = migration._ram_from_payload(cls.result_payload)

    def test_candidate_round_trip_report_and_exact_identities_are_frozen(self) -> None:
        self.assertEqual(
            (len(self.source), _sha256(self.source)),
            (migration.SOURCE_STATE_SIZE, migration.SOURCE_STATE_SHA256),
        )
        self.assertEqual(
            (len(self.result), _sha256(self.result)),
            (migration.OUTPUT_STATE_SIZE, migration.OUTPUT_STATE_SHA256),
        )
        self.assertEqual(
            (len(self.result_payload), _sha256(self.result_payload)),
            (migration.SOURCE_PAYLOAD_SIZE, migration.OUTPUT_PAYLOAD_SHA256),
        )
        self.assertEqual(_sha256(self.result_ram), migration.OUTPUT_RAM_SHA256)
        self.assertEqual(self.source_frame, self.result_frame)
        self.assertEqual(len(self.result) - self.result_frame, migration.OUTPUT_COMPRESSED_SIZE)
        self.assertEqual(_sha256(self.result[self.result_frame :]), migration.OUTPUT_COMPRESSED_SHA256)
        self.assertEqual(
            self.result_prefix,
            migration._expected_prefix(self.source_prefix, compressed_size=migration.OUTPUT_COMPRESSED_SIZE),
        )
        self.assertEqual(_sha256(self.result_prefix), migration.OUTPUT_PREFIX_SHA256)
        self.assertEqual(
            len(migration._diff_offsets(self.source_prefix, self.result_prefix)),
            migration.EXPECTED_PREFIX_BYTES_CHANGED,
        )
        self.assertEqual(self.result.count(migration.OLD_CUE_NAME.encode("ascii")), 0)
        self.assertEqual(self.result.count(migration.NEW_CUE_NAME.encode("ascii")), 1)
        self.assertEqual(self.report["archive_table_bytes_changed"], 2_464)
        self.assertEqual(self.report["compressed_payload_size"], migration.OUTPUT_COMPRESSED_SIZE)
        self.assertEqual(self.report["compressed_payload_sha256"], migration.OUTPUT_COMPRESSED_SHA256)
        self.assertEqual(self.report["ram_sha256"], migration.OUTPUT_RAM_SHA256)
        self.assertEqual(self.report["resident_script_bytes_changed"], 0)
        self.assertEqual(self.report["resident_header_bytes_changed"], 0)
        self.assertEqual(self.report["runtime_actor_pc_bytes_changed"], 0)
        self.assertTrue(self.report["round_trip_verified"])
        if CANDIDATE_STATE.is_file():
            self.assertEqual(CANDIDATE_STATE.read_bytes(), self.result)
        if CANDIDATE_REPORT.is_file():
            self.assertEqual(json.loads(CANDIDATE_REPORT.read_text(encoding="utf-8")), self.report)

    def test_media_manifests_changed_resources_and_field621_are_exact(self) -> None:
        self.assertEqual(
            (len(self.old_manifest), _sha256(self.old_manifest)),
            (migration.V227_STAGE_MANIFEST_SIZE, migration.V227_STAGE_MANIFEST_SHA256),
        )
        self.assertEqual(
            (len(self.new_manifest), _sha256(self.new_manifest)),
            (migration.V228_STAGE_MANIFEST_SIZE, migration.V228_STAGE_MANIFEST_SHA256),
        )
        old_inventory = migration._manifest_inventory(
            self.old_manifest,
            size=migration.V227_STAGE_MANIFEST_SIZE,
            sha256=migration.V227_STAGE_MANIFEST_SHA256,
            label="V227 stage manifest",
        )
        new_inventory = migration._manifest_inventory(
            self.new_manifest,
            size=migration.V228_STAGE_MANIFEST_SIZE,
            sha256=migration.V228_STAGE_MANIFEST_SHA256,
            label="V228 stage manifest",
        )
        for canonical_id in migration.PINNED_RESOURCE_IDS:
            self.assertEqual(old_inventory[canonical_id], migration.OLD_MANIFEST_RESOURCES[canonical_id])
            self.assertEqual(new_inventory[canonical_id], migration.NEW_MANIFEST_RESOURCES[canonical_id])
        changed = tuple(
            sorted(
                canonical_id
                for canonical_id in old_inventory.keys() | new_inventory.keys()
                if old_inventory.get(canonical_id) != new_inventory.get(canonical_id)
            )
        )
        self.assertEqual(changed, migration.CHANGED_RESOURCE_IDS)
        self.assertEqual(self.old_header, self.new_header)
        self.assertEqual(self.old_script, self.new_script)
        self.assertEqual(
            (len(self.old_header), _sha256(self.old_header)),
            (migration.MEDIA_HEADER_SIZE, migration.MEDIA_HEADER_SHA256),
        )
        self.assertEqual(
            (len(self.old_script), _sha256(self.old_script)),
            (migration.MEDIA_SCRIPT_SIZE, migration.MEDIA_SCRIPT_SHA256),
        )

    def test_exact_archive_table_only_payload_whitelist_and_volatile_tail(self) -> None:
        old_table = media_migration._archive_table(OLD_DISC)
        new_table = media_migration._archive_table(NEW_DISC)
        table_diffs = migration._diff_triplets(old_table, new_table)
        self.assertEqual(len(table_diffs), migration.ARCHIVE_TABLE_DIFF_COUNT)
        self.assertEqual(
            (table_diffs[0][0], table_diffs[-1][0]),
            (migration.ARCHIVE_TABLE_DIFF_FIRST, migration.ARCHIVE_TABLE_DIFF_LAST),
        )
        self.assertEqual(migration._triplet_digest(table_diffs), migration.ARCHIVE_TABLE_DIFF_SHA256)
        expected = tuple(
            migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + relative
            for relative, _old, _new in table_diffs
        )
        actual = migration._diff_offsets(self.source_payload, self.result_payload)
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        table_offset = migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        source_table = self.source_payload[table_offset : table_offset + migration.ARCHIVE_TABLE_SIZE]
        result_table = self.result_payload[table_offset : table_offset + migration.ARCHIVE_TABLE_SIZE]
        self.assertEqual(migration._diff_triplets(source_table, old_table), migration.RESIDENT_VS_MEDIA_DIFFS)
        self.assertEqual(migration._diff_triplets(result_table, new_table), migration.RESIDENT_VS_MEDIA_DIFFS)
        self.assertEqual(result_table[0x7FFF], 0xE0)
        self.assertEqual(_sha256(result_table), migration.OUTPUT_RESIDENT_TABLE_SHA256)

    def test_hybrid_header_route_and_all_runtime_state_are_preserved(self) -> None:
        for offset, size, expected_sha in (
            (
                migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET,
                migration.RESIDENT_SCRIPT_SIZE,
                migration.RESIDENT_SCRIPT_SHA256,
            ),
            (
                migration.EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET,
                migration.RESIDENT_HEADER_SIZE,
                migration.RESIDENT_HEADER_SHA256,
            ),
            (migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET, migration.DIALOGUE_SIZE, migration.DIALOGUE_SHA256),
            (migration.EXPECTED_WALKMESH_PAYLOAD_OFFSET, migration.WALKMESH_SIZE, migration.WALKMESH_SHA256),
        ):
            source = self.source_payload[offset : offset + size]
            result = self.result_payload[offset : offset + size]
            self.assertEqual(result, source)
            self.assertEqual(_sha256(result), expected_sha)
        resident_header = self.result_payload[
            migration.EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET :
            migration.EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET + migration.RESIDENT_HEADER_SIZE
        ]
        self.assertNotEqual(resident_header, self.new_header)
        route = migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + migration.previous.SCRIPT_PATCH_OFFSET
        self.assertEqual(self.result_payload[route : route + 5], migration.CURRENT_CHANGE_FIELD)

        actor_base = struct.unpack_from("<I", self.source_ram, FIELD_ACTORS)[0] & 0x1FFFFFFF
        self.assertEqual(
            self.result_ram[actor_base : actor_base + migration.ACTOR_ARRAY_SIZE],
            self.source_ram[actor_base : actor_base + migration.ACTOR_ARRAY_SIZE],
        )
        for entity in range(migration.SCRIPT_ENTITY_COUNT):
            record = actor_base + entity * FIELD_ACTOR_STRIDE
            data = struct.unpack_from(
                "<I", self.source_ram, record + FIELD_ACTOR_DATA_POINTER
            )[0] & 0x1FFFFFFF
            self.assertEqual(
                self.result_ram[record : record + FIELD_ACTOR_STRIDE],
                self.source_ram[record : record + FIELD_ACTOR_STRIDE],
            )
            self.assertEqual(
                self.result_ram[data : data + migration.ACTOR_DATA_SIZE],
                self.source_ram[data : data + migration.ACTOR_DATA_SIZE],
            )
        for offset, size in (
            (GAME_STATE, GAMESTATE_SIZE),
            (FIELD_SCRIPT_MEMORY, migration.previous.FIELD_VARIABLE_BANK_SIZE),
            (migration.previous.DIALOG_WINDOWS, migration.previous.DIALOG_WINDOWS_SIZE),
        ):
            self.assertEqual(self.result_ram[offset : offset + size], self.source_ram[offset : offset + size])
        for address in CAMERA_VECTORS.values():
            self.assertEqual(self.result_ram[address : address + 16], self.source_ram[address : address + 16])

    def test_wrong_source_artifacts_and_live_output_paths_fail_closed(self) -> None:
        wrong_source = bytearray(self.source)
        wrong_source[0x100] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "Source Slot 1 identity"):
            migration.migrate_v227_slot1_to_v228(
                bytes(wrong_source),
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_manifest=self.old_manifest,
                new_manifest=self.new_manifest,
                old_header=self.old_header,
                new_header=self.new_header,
                old_script=self.old_script,
                new_script=self.new_script,
                zstd=self.zstd,
            )
        wrong_manifest = bytearray(self.new_manifest)
        wrong_manifest[-2] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "V228 stage manifest identity"):
            migration.migrate_v227_slot1_to_v228(
                self.source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_manifest=self.old_manifest,
                new_manifest=bytes(wrong_manifest),
                old_header=self.old_header,
                new_header=self.new_header,
                old_script=self.old_script,
                new_script=self.new_script,
                zstd=self.zstd,
            )
        wrong_script = bytearray(self.new_script)
        wrong_script[-1] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "V228 field-621 script clone identity"):
            migration.migrate_v227_slot1_to_v228(
                self.source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_manifest=self.old_manifest,
                new_manifest=self.new_manifest,
                old_header=self.old_header,
                new_header=self.new_header,
                old_script=self.old_script,
                new_script=bytes(wrong_script),
                zstd=self.zstd,
            )

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = migration.main(
                (str(SOURCE_STATE), "--output", str(migration.LIVE_SLOT1), "--report", str(CANDIDATE_REPORT))
            )
        self.assertEqual(exit_code, 1)
        self.assertIn("may not be the live Slot 1", stderr.getvalue())
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = migration.main(
                (str(SOURCE_STATE), "--output", str(CANDIDATE_STATE), "--report", str(migration.LIVE_SLOT1))
            )
        self.assertEqual(exit_code, 1)
        self.assertIn("may not be the live Slot 1", stderr.getvalue())
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = migration.main(
                (str(SOURCE_STATE), "--output", str(SOURCE_STATE), "--report", str(CANDIDATE_REPORT))
            )
        self.assertEqual(exit_code, 1)
        self.assertIn("may not replace the source state", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
