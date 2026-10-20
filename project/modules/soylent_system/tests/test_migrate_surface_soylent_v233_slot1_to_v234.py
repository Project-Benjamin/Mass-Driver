from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

from contextlib import redirect_stderr
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import tools.migrate_duckstation_disc_state as media_migration
import tools.migrate_surface_soylent_v233_slot1_to_v234 as migration
from tools.xgdeathblows import GAMESTATE_SIZE
from tools.xgdisc import Mode2Image
from work.read_duckstation_runtime import GAME_STATE, RAM_SIZE


PROJECT_ROOT = REPOSITORY_ROOT
SOURCE_STATE = migration.SOURCE_FIXTURE
CANDIDATE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v234_from_b9b41cbc_cross_only_controls.sav"
)
CANDIDATE_REPORT = CANDIDATE_STATE.with_suffix(".json")
OLD_DISC = PROJECT_ROOT / "output" / migration.OLD_CUE_NAME.replace(".cue", ".bin")
NEW_DISC = PROJECT_ROOT / "output" / migration.NEW_CUE_NAME.replace(".cue", ".bin")
OLD_MANIFEST = PROJECT_ROOT / "work" / "surface_soylent_campaign_v233_stage" / "manifest.json"
NEW_MANIFEST = PROJECT_ROOT / "work" / "surface_soylent_campaign_v234_stage" / "manifest.json"
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SurfaceSoylentV233Slot1ToV234Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (
            SOURCE_STATE,
            OLD_DISC,
            NEW_DISC,
            OLD_DISC.with_name(migration.OLD_CUE_NAME),
            NEW_DISC.with_name(migration.NEW_CUE_NAME),
            OLD_MANIFEST,
            NEW_MANIFEST,
            ZSTD,
        )
        if not all(path.is_file() for path in required):
            raise unittest.SkipTest("Pinned V233/V234 migration fixtures unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.old_manifest = OLD_MANIFEST.read_bytes()
        cls.new_manifest = NEW_MANIFEST.read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v233_slot1_to_v234(
            cls.source,
            old_disc=OLD_DISC,
            new_disc=NEW_DISC,
            old_manifest=cls.old_manifest,
            new_manifest=cls.new_manifest,
            zstd=cls.zstd,
        )
        cls.source_payload, cls.source_frame, cls.source_prefix = migration._unpack_state(
            cls.source, cls.zstd
        )
        cls.result_payload, cls.result_frame, cls.result_prefix = migration._unpack_state(
            cls.result, cls.zstd
        )
        cls.ram_offset, cls.source_ram = migration._ram_from_payload(cls.source_payload)
        _result_ram_offset, cls.result_ram = migration._ram_from_payload(cls.result_payload)

    def test_candidate_report_and_round_trip_have_frozen_identities(self) -> None:
        self.assertEqual(
            (len(self.source), _sha256(self.source)),
            (migration.SOURCE_STATE_SIZE, migration.SOURCE_STATE_SHA256),
        )
        self.assertEqual(
            (len(self.result), _sha256(self.result)),
            (migration.OUTPUT_STATE_SIZE, migration.OUTPUT_STATE_SHA256),
        )
        self.assertEqual(self.result_frame, migration.SOURCE_PREFIX_SIZE)
        self.assertEqual(
            (len(self.result) - self.result_frame, _sha256(self.result[self.result_frame :])),
            (migration.OUTPUT_COMPRESSED_SIZE, migration.OUTPUT_COMPRESSED_SHA256),
        )
        self.assertEqual(_sha256(self.result_prefix), migration.OUTPUT_PREFIX_SHA256)
        self.assertEqual(_sha256(self.result_payload), migration.OUTPUT_PAYLOAD_SHA256)
        self.assertEqual(_sha256(self.result_ram), migration.OUTPUT_RAM_SHA256)
        report_blob = migration._report_blob(self.report)
        self.assertEqual(
            (len(report_blob), _sha256(report_blob)),
            (migration.OUTPUT_REPORT_SIZE, migration.OUTPUT_REPORT_SHA256),
        )
        if CANDIDATE_STATE.is_file():
            self.assertEqual(CANDIDATE_STATE.read_bytes(), self.result)
        if CANDIDATE_REPORT.is_file():
            self.assertEqual(CANDIDATE_REPORT.read_bytes(), report_blob)
            self.assertEqual(json.loads(report_blob), self.report)
        self.assertTrue(self.report["round_trip_verified"])
        self.assertTrue(self.report["safe_to_mount_after_duckstation_is_fully_closed"])
        self.assertFalse(self.report["live_slot1_modified"])

    def test_exact_seven_resident_control_bytes_change(self) -> None:
        overlay_payload = self.ram_offset + migration.FIELD_OVERLAY_RAM_OFFSET
        action_payload = self.ram_offset + migration.RESIDENT_ACTION_RAM_OFFSET
        expected_triplets = tuple(sorted((
            *(
                (overlay_payload + offset, 0x60, 0x40)
                for offset in migration.FIELD_OVERLAY_MASK_OFFSETS
            ),
            *(
                (action_payload + offset, 0x20, 0x40)
                for offset in migration.RESIDENT_ACTION_MASK_OFFSETS
            ),
        )))
        actual = migration._diff_triplets(self.source_payload, self.result_payload)
        self.assertEqual(actual, expected_triplets)
        self.assertEqual(len(actual), migration.EXPECTED_CONTROL_BYTES_CHANGED)
        self.assertEqual(migration._triplet_digest(actual), migration.CONTROL_DIFF_SHA256)
        for offset in migration.FIELD_OVERLAY_MASK_OFFSETS:
            start = migration.FIELD_OVERLAY_RAM_OFFSET + offset
            self.assertEqual(
                self.source_ram[start : start + 4],
                migration.OLD_OVERLAY_MASK_INSTRUCTION,
            )
            self.assertEqual(
                self.result_ram[start : start + 4],
                migration.NEW_OVERLAY_MASK_INSTRUCTION,
            )
        self.assertEqual(
            self.source_ram[
                migration.RESIDENT_ACTION_RAM_OFFSET :
                migration.RESIDENT_ACTION_RAM_OFFSET + len(migration.OLD_RESIDENT_ACTION)
            ],
            migration.OLD_RESIDENT_ACTION,
        )
        self.assertEqual(
            self.result_ram[
                migration.RESIDENT_ACTION_RAM_OFFSET :
                migration.RESIDENT_ACTION_RAM_OFFSET + len(migration.NEW_RESIDENT_ACTION)
            ],
            migration.NEW_RESIDENT_ACTION,
        )
        self.assertEqual(self.report["archive_table_bytes_changed"], 0)
        self.assertEqual(self.report["control_bytes_changed"], 7)
        self.assertEqual(self.report["payload_bytes_changed"], 7)

    def test_media_and_manifest_delta_are_pinned(self) -> None:
        self.assertEqual(
            (OLD_DISC.stat().st_size, migration._file_sha256(OLD_DISC)),
            (migration.OLD_DISC_SIZE, migration.OLD_DISC_SHA256),
        )
        self.assertEqual(
            (NEW_DISC.stat().st_size, migration._file_sha256(NEW_DISC)),
            (migration.NEW_DISC_SIZE, migration.NEW_DISC_SHA256),
        )
        old_inventory = migration._manifest_inventory(
            self.old_manifest,
            size=migration.OLD_MANIFEST_SIZE,
            sha256=migration.OLD_MANIFEST_SHA256,
            label="V233 manifest",
        )
        new_inventory = migration._manifest_inventory(
            self.new_manifest,
            size=migration.NEW_MANIFEST_SIZE,
            sha256=migration.NEW_MANIFEST_SHA256,
            label="V234 manifest",
        )
        changed = tuple(
            resource_id
            for resource_id in sorted(set(old_inventory) | set(new_inventory))
            if old_inventory.get(resource_id) != new_inventory.get(resource_id)
        )
        self.assertEqual(changed, migration.CHANGED_RESOURCE_IDS)

        old_table = media_migration._archive_table(OLD_DISC)
        new_table = media_migration._archive_table(NEW_DISC)
        self.assertEqual(old_table, new_table)
        self.assertEqual(migration._diff_triplets(old_table, new_table), ())
        table = migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        self.assertEqual(
            self.source_payload[table : table + migration.ARCHIVE_TABLE_SIZE],
            self.result_payload[table : table + migration.ARCHIVE_TABLE_SIZE],
        )
        self.assertEqual(self.result_payload[table + migration.ARCHIVE_TABLE_SIZE - 1], 0xE0)

        for disc, canonical_id, size, sha256 in (
            (OLD_DISC, migration.FIELD_OVERLAY_CANONICAL_ID, migration.OLD_FIELD_OVERLAY_SIZE, migration.OLD_FIELD_OVERLAY_SHA256),
            (NEW_DISC, migration.FIELD_OVERLAY_CANONICAL_ID, migration.NEW_FIELD_OVERLAY_SIZE, migration.NEW_FIELD_OVERLAY_SHA256),
            (OLD_DISC, migration.WORLDMAP_OVERLAY_CANONICAL_ID, migration.OLD_WORLDMAP_OVERLAY_SIZE, migration.OLD_WORLDMAP_OVERLAY_SHA256),
            (NEW_DISC, migration.WORLDMAP_OVERLAY_CANONICAL_ID, migration.NEW_WORLDMAP_OVERLAY_SIZE, migration.NEW_WORLDMAP_OVERLAY_SHA256),
        ):
            image = Mode2Image(disc)
            data = image.extract_entry(image.read_index()[canonical_id - 5])
            self.assertEqual((len(data), _sha256(data)), (size, sha256))

    def test_every_unrelated_runtime_byte_is_preserved(self) -> None:
        expected_ram_offsets = {
            *(migration.FIELD_OVERLAY_RAM_OFFSET + offset for offset in migration.FIELD_OVERLAY_MASK_OFFSETS),
            *(migration.RESIDENT_ACTION_RAM_OFFSET + offset for offset in migration.RESIDENT_ACTION_MASK_OFFSETS),
        }
        self.assertEqual(
            set(migration._diff_offsets(self.source_ram, self.result_ram)),
            expected_ram_offsets,
        )
        self.assertEqual(
            self.source_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
            self.result_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
        )
        writable = migration.FIELD_OVERLAY_RAM_OFFSET + migration.FIELD_OVERLAY_CODE_SIZE
        end = migration.FIELD_OVERLAY_RAM_OFFSET + migration.FIELD_OVERLAY_RUNTIME_SIZE
        self.assertEqual(self.source_ram[writable:end], self.result_ram[writable:end])
        script_start = migration.RESIDENT_SCRIPT_RAM_OFFSET
        script_end = script_start + migration.RESIDENT_SCRIPT_SIZE
        script_diffs = migration._diff_offsets(
            self.source_ram[script_start:script_end],
            self.result_ram[script_start:script_end],
        )
        action_relative = migration.RESIDENT_ACTION_RAM_OFFSET - script_start
        self.assertEqual(
            script_diffs,
            tuple(action_relative + offset for offset in migration.RESIDENT_ACTION_MASK_OFFSETS),
        )
        self.assertEqual(len(self.source_ram), RAM_SIZE)
        self.assertTrue(self.report["fei_party_gamestate_field_runtime_preserved"])
        self.assertTrue(self.report["resident_overlay_writable_data_preserved"])

    def test_wrong_source_media_manifest_and_unpinned_target_fail_closed(self) -> None:
        common = {
            "old_disc": OLD_DISC,
            "new_disc": NEW_DISC,
            "old_manifest": self.old_manifest,
            "new_manifest": self.new_manifest,
            "zstd": self.zstd,
        }
        damaged_state = bytearray(self.source)
        damaged_state[0x100] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "Source Slot 1"):
            migration.migrate_v233_slot1_to_v234(bytes(damaged_state), **common)
        damaged_manifest = bytearray(self.new_manifest)
        damaged_manifest[-2] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "V234 manifest identity"):
            migration.migrate_v233_slot1_to_v234(
                self.source, **{**common, "new_manifest": bytes(damaged_manifest)}
            )
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "V234 disc identity"):
            migration.migrate_v233_slot1_to_v234(
                self.source, **{**common, "new_disc": OLD_DISC}
            )
        with patch.object(migration, "NEW_DISC_SHA256", None):
            with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "not pinned"):
                migration.migrate_v233_slot1_to_v234(self.source, **common)

    def test_cli_refuses_live_or_source_outputs_and_writes_separate_candidate(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = migration.main(
                (str(SOURCE_STATE), "--output", str(migration.LIVE_SLOT1))
            )
        self.assertEqual(code, 1)
        self.assertIn("may not be the live Slot 1", stderr.getvalue())

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = migration.main(
                (str(SOURCE_STATE), "--report", str(SOURCE_STATE))
            )
        self.assertEqual(code, 1)
        self.assertIn("may not replace the source state", stderr.getvalue())

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "candidate.sav"
            report = Path(temp_dir) / "candidate.json"
            code = migration.main(
                (str(SOURCE_STATE), "--output", str(output), "--report", str(report))
            )
            self.assertEqual(code, 0)
            self.assertEqual(output.read_bytes(), self.result)
            self.assertEqual(report.read_bytes(), migration._report_blob(self.report))


if __name__ == "__main__":
    unittest.main()
