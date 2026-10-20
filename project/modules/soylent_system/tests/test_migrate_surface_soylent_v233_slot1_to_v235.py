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
import tools.migrate_surface_soylent_v233_slot1_to_v235 as migration
from tools.xgdeathblows import GAMESTATE_SIZE
from work.read_duckstation_runtime import GAME_STATE, RAM_SIZE


PROJECT_ROOT = REPOSITORY_ROOT
SOURCE_STATE = migration.SOURCE_FIXTURE
OLD_DISC = PROJECT_ROOT / "output" / migration.OLD_CUE_NAME.replace(".cue", ".bin")
NEW_DISC = PROJECT_ROOT / "output" / migration.NEW_CUE_NAME.replace(".cue", ".bin")
OLD_MANIFEST = PROJECT_ROOT / "work" / "surface_soylent_campaign_v233_stage" / "manifest.json"
NEW_MANIFEST = PROJECT_ROOT / "work" / "surface_soylent_campaign_v235_stage" / "manifest.json"
CANDIDATE_STATE = (
    PROJECT_ROOT / "work" / "save_candidates"
    / "SLUS-00669_1_v235_from_b9b41cbc_cross_only_controls.sav"
)
CANDIDATE_REPORT = CANDIDATE_STATE.with_suffix(".json")
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SurfaceSoylentV233Slot1ToV235Tests(unittest.TestCase):
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
            raise unittest.SkipTest("Pinned V233/V235 migration fixtures unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.old_manifest = OLD_MANIFEST.read_bytes()
        cls.new_manifest = NEW_MANIFEST.read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.old_table = media_migration._archive_table(OLD_DISC)
        cls.new_table = media_migration._archive_table(NEW_DISC)
        cls.result, cls.report = migration.migrate_v233_slot1_to_v235(
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
        self.assertEqual(_sha256(self.result_prefix), migration.OUTPUT_PREFIX_SHA256)
        self.assertEqual(
            (len(self.result) - self.result_frame, _sha256(self.result[self.result_frame :])),
            (migration.OUTPUT_COMPRESSED_SIZE, migration.OUTPUT_COMPRESSED_SHA256),
        )
        self.assertEqual(_sha256(self.result_payload), migration.OUTPUT_PAYLOAD_SHA256)
        self.assertEqual(_sha256(self.result_ram), migration.OUTPUT_RAM_SHA256)
        self.assertEqual(self.result.count(migration.OLD_CUE_NAME.encode("ascii")), 0)
        self.assertEqual(self.result.count(migration.NEW_CUE_NAME.encode("ascii")), 1)
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
        self.assertFalse(self.report["live_slot1_modified"])

    def test_exactly_five_overlay_mask_bytes_change_from_60_to_20(self) -> None:
        overlay_payload = self.ram_offset + migration.FIELD_OVERLAY_RAM_OFFSET
        control_expected = tuple(
            (overlay_payload + offset, 0x60, 0x20) for offset in migration.FIELD_OVERLAY_MASK_OFFSETS
        )
        table_expected = tuple(
            (migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + offset, old, new)
            for offset, old, new in migration.ARCHIVE_TABLE_DIFFS or ()
        )
        expected = tuple(sorted((*table_expected, *control_expected)))
        actual = migration._diff_triplets(self.source_payload, self.result_payload)
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        self.assertEqual(migration._triplet_digest(actual), migration.PAYLOAD_DIFF_SHA256)
        self.assertEqual(
            migration._triplet_digest(control_expected), migration.CONTROL_DIFF_SHA256
        )
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
        self.assertEqual(self.report["archive_table_bytes_changed"], 2)
        self.assertEqual(self.report["control_bytes_changed"], 5)
        self.assertEqual(self.report["payload_bytes_changed"], 7)

    def test_field_567_action_and_every_unrelated_ram_byte_are_preserved(self) -> None:
        expected_ram_offsets = {
            *(migration.FIELD_OVERLAY_RAM_OFFSET + offset for offset in migration.FIELD_OVERLAY_MASK_OFFSETS),
            *(
                migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET - self.ram_offset + offset
                for offset, _old, _new in migration.ARCHIVE_TABLE_DIFFS or ()
            ),
        }
        self.assertEqual(
            set(migration._diff_offsets(self.source_ram, self.result_ram)),
            expected_ram_offsets,
        )
        self.assertEqual(
            self.source_ram[
                migration.RESIDENT_ACTION_RAM_OFFSET :
                migration.RESIDENT_ACTION_RAM_OFFSET + len(migration.UNCHANGED_RESIDENT_ACTION)
            ],
            migration.UNCHANGED_RESIDENT_ACTION,
        )
        self.assertEqual(
            self.result_ram[
                migration.RESIDENT_ACTION_RAM_OFFSET :
                migration.RESIDENT_ACTION_RAM_OFFSET + len(migration.UNCHANGED_RESIDENT_ACTION)
            ],
            migration.UNCHANGED_RESIDENT_ACTION,
        )
        for offset in migration.RESIDENT_ACTION_MASK_OFFSETS:
            self.assertEqual(migration.UNCHANGED_RESIDENT_ACTION[offset], 0x20)
        script_start = migration.RESIDENT_SCRIPT_RAM_OFFSET
        script_end = script_start + migration.RESIDENT_SCRIPT_SIZE
        self.assertEqual(
            self.source_ram[script_start:script_end],
            self.result_ram[script_start:script_end],
        )
        self.assertEqual(
            self.source_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
            self.result_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
        )
        self.assertEqual(len(self.source_ram), RAM_SIZE)

    def test_source_validation_and_whitelist_fail_closed(self) -> None:
        damaged = bytearray(self.source_payload)
        damaged[self.ram_offset + migration.FIELD_OVERLAY_RAM_OFFSET + 0x20] ^= 1
        with self.assertRaisesRegex(
            migration.SurfaceSlotMigrationError,
            "Pinned V233 payload identity",
        ):
            migration._patch_resident_controls(bytes(damaged), self.old_table, self.new_table)

        changed_table = bytearray(self.old_table)
        changed_table[0] ^= 1
        with self.assertRaisesRegex(
            media_migration.StateMigrationError,
            "resident archive table",
        ):
            migration._patch_resident_controls(
                self.source_payload, bytes(changed_table), self.new_table
            )

    def test_media_pins_and_cli_candidate_are_fail_closed(self) -> None:
        self.assertEqual(
            migration._diff_triplets(self.old_table, self.new_table),
            migration.ARCHIVE_TABLE_DIFFS,
        )
        with patch.object(migration, "NEW_DISC_SHA256", None):
            with self.assertRaisesRegex(
                migration.SurfaceSlotMigrationError,
                "Final V235 identities are not pinned: V235 disc hash",
            ):
                migration.migrate_v233_slot1_to_v235(
                    self.source,
                    old_disc=OLD_DISC,
                    new_disc=NEW_DISC,
                    old_manifest=self.old_manifest,
                    new_manifest=self.new_manifest,
                    zstd=self.zstd,
                )
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "candidate.sav"
            report = Path(temp_dir) / "candidate.json"
            code = migration.main(
                (str(SOURCE_STATE), "--output", str(output), "--report", str(report))
            )
            self.assertEqual(code, 0)
            self.assertEqual(output.read_bytes(), self.result)
            self.assertEqual(report.read_bytes(), migration._report_blob(self.report))

    def test_cli_refuses_live_and_source_outputs_before_media_access(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = migration.main((str(SOURCE_STATE), "--output", str(migration.LIVE_SLOT1)))
        self.assertEqual(code, 1)
        self.assertIn("may not be the live Slot 1", stderr.getvalue())

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = migration.main((str(SOURCE_STATE), "--report", str(SOURCE_STATE)))
        self.assertEqual(code, 1)
        self.assertIn("may not replace the source state", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
