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
import tools.migrate_surface_soylent_v226_slot1_to_v227 as migration
from tools.xgdeathblows import GAMESTATE_SIZE
from tools.xgscript import AtelScript
from work.read_duckstation_runtime import (
    CAMERA_VECTORS,
    FIELD_ACTORS,
    FIELD_ACTOR_DATA_POINTER,
    FIELD_ACTOR_STRIDE,
    FIELD_SCRIPT_MEMORY,
    GAME_STATE,
)


PROJECT_ROOT = REPOSITORY_ROOT
SOURCE_STATE = PROJECT_ROOT / "work" / "save_backups" / "SLUS-00669_1_v226_intake_door_room_change_9436ef84.sav"
CANDIDATE_STATE = PROJECT_ROOT / "work" / "save_candidates" / "SLUS-00669_1_v227_from_9436ef84_treatment_preparation.sav"
CANDIDATE_REPORT = CANDIDATE_STATE.with_suffix(".json")
OLD_DISC = PROJECT_ROOT / "output" / "Xenogears_PW_CD2_mass_driver_surface_soylent_v226.bin"
NEW_DISC = PROJECT_ROOT / "output" / "Xenogears_PW_CD2_mass_driver_surface_soylent_v227.bin"
OLD_FIELD = PROJECT_ROOT / "work" / "surface_soylent_campaign_v226_stage" / "clones" / "field_621"
NEW_STAGE = PROJECT_ROOT / "work" / "surface_soylent_campaign_v227_stage"
NEW_FIELD = NEW_STAGE / "clones" / "field_621"
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SurfaceSoylentV226Slot1MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (
            SOURCE_STATE,
            OLD_DISC,
            NEW_DISC,
            OLD_DISC.with_suffix(".cue"),
            NEW_DISC.with_suffix(".cue"),
            OLD_FIELD / "header.bin",
            NEW_FIELD / "header.bin",
            OLD_FIELD / "05_scripts.bin",
            NEW_FIELD / "05_scripts.bin",
            NEW_STAGE / "manifest.json",
            ZSTD,
        )
        if not all(path.is_file() for path in required):
            raise unittest.SkipTest("Pinned V226/V227 migration fixtures unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.old_header = (OLD_FIELD / "header.bin").read_bytes()
        cls.new_header = (NEW_FIELD / "header.bin").read_bytes()
        cls.old_script = (OLD_FIELD / "05_scripts.bin").read_bytes()
        cls.new_script = (NEW_FIELD / "05_scripts.bin").read_bytes()
        cls.manifest = (NEW_STAGE / "manifest.json").read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v226_slot1_to_v227(
            cls.source,
            old_disc=OLD_DISC,
            new_disc=NEW_DISC,
            stage_manifest=cls.manifest,
            old_header=cls.old_header,
            new_header=cls.new_header,
            old_script=cls.old_script,
            new_script=cls.new_script,
            zstd=cls.zstd,
        )
        cls.source_payload, cls.frame_start, cls.source_prefix = migration._unpack_state(cls.source, cls.zstd)
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
        self.assertEqual(self.result_frame, self.frame_start)
        self.assertEqual(len(self.result) - self.result_frame, migration.OUTPUT_COMPRESSED_SIZE)
        self.assertEqual(_sha256(self.result[self.result_frame :]), migration.OUTPUT_COMPRESSED_SHA256)
        self.assertEqual(
            self.result_prefix,
            migration._expected_prefix(self.source_prefix, compressed_size=migration.OUTPUT_COMPRESSED_SIZE),
        )
        self.assertEqual(_sha256(self.result_prefix), migration.OUTPUT_PREFIX_SHA256)
        self.assertEqual(len(migration._diff_offsets(self.source_prefix, self.result_prefix)), 4)
        self.assertEqual(self.result.count(migration.OLD_CUE_NAME.encode("ascii")), 0)
        self.assertEqual(self.result.count(migration.NEW_CUE_NAME.encode("ascii")), 1)
        self.assertEqual(self.report["new_destination"], {"field": 594, "parameter": 0})
        self.assertEqual(self.report["endpoint"], "intake_treatment_preparation.treatment")
        self.assertTrue(self.report["round_trip_verified"])
        self.assertTrue(self.report["allocator_safe"])
        if CANDIDATE_STATE.is_file():
            self.assertEqual(CANDIDATE_STATE.read_bytes(), self.result)
        if CANDIDATE_REPORT.is_file():
            self.assertEqual(json.loads(CANDIDATE_REPORT.read_text(encoding="utf-8")), self.report)

    def test_media_manifest_and_field621_route_contract_are_exact(self) -> None:
        self.assertEqual(
            (len(self.manifest), _sha256(self.manifest)),
            (migration.V227_STAGE_MANIFEST_SIZE, migration.V227_STAGE_MANIFEST_SHA256),
        )
        inventory = {item["canonical_id"]: item for item in json.loads(self.manifest)["replacement_inventory"]}
        for canonical_id, identity in migration.MANIFEST_RESOURCES.items():
            self.assertEqual((inventory[canonical_id]["size"], inventory[canonical_id]["sha256"]), identity)
        header_diffs = migration._diff_triplets(self.old_header, self.new_header)
        script_diffs = migration._diff_triplets(self.old_script, self.new_script)
        self.assertEqual(header_diffs, migration.HEADER_DIFFS)
        self.assertEqual(migration._triplet_digest(header_diffs), migration.HEADER_DIFF_SHA256)
        self.assertEqual(script_diffs, migration.SCRIPT_DIFFS)
        self.assertEqual(migration._triplet_digest(script_diffs), migration.SCRIPT_DIFF_SHA256)
        self.assertEqual(
            migration._patch_reconstruction(
                self.old_script,
                migration.SCRIPT_PATCH_OFFSET,
                migration.OLD_CHANGE_FIELD,
                migration.NEW_CHANGE_FIELD,
            ),
            self.new_script,
        )
        old_atel, new_atel = AtelScript(self.old_script), AtelScript(self.new_script)
        self.assertEqual(old_atel.get_script_pointer(migration.DOOR_ENTITY, 2), migration.DOOR_SCRIPT2_PC)
        self.assertEqual(new_atel.get_script_pointer(migration.DOOR_ENTITY, 2), migration.DOOR_SCRIPT2_PC)
        self.assertEqual(
            old_atel.bytecode[migration.DOOR_CHANGE_FIELD_PC : migration.DOOR_CHANGE_FIELD_PC + 5],
            bytes.fromhex("98 35 82 03 80"),
        )
        self.assertEqual(
            new_atel.bytecode[migration.DOOR_CHANGE_FIELD_PC : migration.DOOR_CHANGE_FIELD_PC + 5],
            bytes.fromhex("98 52 82 00 80"),
        )
        old_table = media_migration._archive_table(OLD_DISC)
        new_table = media_migration._archive_table(NEW_DISC)
        table_diffs = migration._diff_triplets(old_table, new_table)
        self.assertEqual(len(table_diffs), 3_031)
        self.assertEqual((table_diffs[0][0], table_diffs[-1][0]), (0x2F58, 0x7157))
        self.assertEqual(migration._triplet_digest(table_diffs), migration.ARCHIVE_TABLE_DIFF_SHA256)

    def test_exact_3033_byte_payload_whitelist_and_volatile_tail(self) -> None:
        old_table = media_migration._archive_table(OLD_DISC)
        new_table = media_migration._archive_table(NEW_DISC)
        table_diffs = migration._diff_triplets(old_table, new_table)
        expected = {
            *(migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + relative for relative, _old, _new in table_diffs),
            *(
                migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + relative
                for relative in migration._diff_offsets(self.old_script, self.new_script)
            ),
        }
        actual = migration._diff_offsets(self.source_payload, self.result_payload)
        self.assertEqual(actual, tuple(sorted(expected)))
        self.assertEqual(len(actual), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        self.assertEqual(self.report["archive_table_bytes_changed"], 3_031)
        self.assertEqual(self.report["resident_script_bytes_changed"], 2)
        self.assertEqual(self.report["runtime_actor_pc_bytes_changed"], 0)
        script = migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + migration.SCRIPT_PATCH_OFFSET
        self.assertEqual(self.source_payload[script : script + 5], migration.OLD_CHANGE_FIELD)
        self.assertEqual(self.result_payload[script : script + 5], migration.NEW_CHANGE_FIELD)
        self.assertEqual(script, 0x11402E)
        table = migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        source_table = self.source_payload[table : table + migration.ARCHIVE_TABLE_SIZE]
        result_table = self.result_payload[table : table + migration.ARCHIVE_TABLE_SIZE]
        self.assertEqual(migration._diff_triplets(source_table, old_table), migration.RESIDENT_VS_MEDIA_DIFFS)
        self.assertEqual(migration._diff_triplets(result_table, new_table), migration.RESIDENT_VS_MEDIA_DIFFS)
        self.assertEqual(result_table[0x7FFF], 0xE0)
        self.assertEqual(_sha256(result_table), migration.OUTPUT_RESIDENT_TABLE_SHA256)

    def test_no_actor_pc_patch_and_all_gameplay_spans_are_preserved(self) -> None:
        actor_base = struct.unpack_from("<I", self.source_ram, FIELD_ACTORS)[0] & 0x1FFFFFFF

        def data_offset(entity: int) -> int:
            return struct.unpack_from(
                "<I",
                self.source_ram,
                actor_base + entity * FIELD_ACTOR_STRIDE + FIELD_ACTOR_DATA_POINTER,
            )[0] & 0x1FFFFFFF

        self.assertEqual(
            self.result_ram[actor_base : actor_base + migration.ACTOR_ARRAY_SIZE],
            self.source_ram[actor_base : actor_base + migration.ACTOR_ARRAY_SIZE],
        )
        old_atel = AtelScript(self.old_script)
        for entity in range(migration.SCRIPT_ENTITY_COUNT):
            data = data_offset(entity)
            self.assertEqual(
                self.result_ram[data : data + migration.ACTOR_DATA_SIZE],
                self.source_ram[data : data + migration.ACTOR_DATA_SIZE],
            )
            current_pc = struct.unpack_from("<H", self.source_ram, data + migration.ACTOR_CURRENT_PC_OFFSET)[0]
            self.assertFalse(
                migration.DOOR_CHANGE_FIELD_PC <= current_pc < migration.DOOR_CHANGE_FIELD_PC + 5
            )
        for entity, expected_pc in (
            (migration.FEI_ENTITY, migration.EXPECTED_FEI_PC),
            (migration.DOOR_ENTITY, migration.EXPECTED_DOOR_PC),
            (migration.DOOR_HELPER_ENTITY, migration.EXPECTED_HELPER_PC),
        ):
            data = data_offset(entity)
            self.assertEqual(struct.unpack_from("<H", self.source_ram, data + migration.ACTOR_SCRIPT_SLOT_OFFSET)[0], expected_pc)
            self.assertEqual(struct.unpack_from("<H", self.source_ram, data + migration.ACTOR_CURRENT_PC_OFFSET)[0], expected_pc)
            self.assertEqual(old_atel.bytecode[expected_pc], 0x00)
        for offset, size in (
            (GAME_STATE, GAMESTATE_SIZE),
            (FIELD_SCRIPT_MEMORY, migration.FIELD_VARIABLE_BANK_SIZE),
            (migration.DIALOG_WINDOWS, migration.DIALOG_WINDOWS_SIZE),
        ):
            self.assertEqual(self.result_ram[offset : offset + size], self.source_ram[offset : offset + size])
        for address in CAMERA_VECTORS.values():
            self.assertEqual(self.result_ram[address : address + 16], self.source_ram[address : address + 16])
        for offset, size in (
            (migration.EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET, migration.OLD_HEADER_SIZE),
            (migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET, migration.DIALOGUE_SIZE),
            (migration.EXPECTED_WALKMESH_PAYLOAD_OFFSET, migration.WALKMESH_SIZE),
        ):
            self.assertEqual(
                self.result_payload[offset : offset + size],
                self.source_payload[offset : offset + size],
            )
        header = migration.EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET
        self.assertEqual(self.result_payload[header : header + migration.OLD_HEADER_SIZE], self.old_header)
        self.assertNotEqual(self.result_payload[header : header + migration.OLD_HEADER_SIZE], self.new_header)
        self.assertTrue(self.report["fei_e26_e34_idle_and_preserved"])
        self.assertTrue(self.report["all_actor_runtime_preserved"])

    def test_wrong_source_resources_and_live_paths_fail_closed(self) -> None:
        wrong_state = bytearray(self.source)
        wrong_state[0x100] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "Source Slot 1 identity"):
            migration.migrate_v226_slot1_to_v227(
                bytes(wrong_state),
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                stage_manifest=self.manifest,
                old_header=self.old_header,
                new_header=self.new_header,
                old_script=self.old_script,
                new_script=self.new_script,
                zstd=self.zstd,
            )
        wrong_manifest = bytearray(self.manifest)
        wrong_manifest[-2] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "V227 stage manifest identity"):
            migration.migrate_v226_slot1_to_v227(
                self.source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                stage_manifest=bytes(wrong_manifest),
                old_header=self.old_header,
                new_header=self.new_header,
                old_script=self.old_script,
                new_script=self.new_script,
                zstd=self.zstd,
            )
        wrong_script = bytearray(self.new_script)
        wrong_script[-1] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "V227 field-621 script identity"):
            migration.migrate_v226_slot1_to_v227(
                self.source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                stage_manifest=self.manifest,
                old_header=self.old_header,
                new_header=self.new_header,
                old_script=self.old_script,
                new_script=bytes(wrong_script),
                zstd=self.zstd,
            )
        live_before = migration.LIVE_SLOT1.read_bytes() if migration.LIVE_SLOT1.is_file() else None
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = migration.main(
                (str(SOURCE_STATE), "--output", str(migration.LIVE_SLOT1), "--report", str(CANDIDATE_REPORT))
            )
        self.assertEqual(exit_code, 1)
        self.assertIn("may not be the live Slot 1", stderr.getvalue())
        if live_before is not None:
            self.assertEqual(migration.LIVE_SLOT1.read_bytes(), live_before)
        source_before = SOURCE_STATE.read_bytes()
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = migration.main(
                (str(SOURCE_STATE), "--output", str(CANDIDATE_STATE), "--report", str(SOURCE_STATE))
            )
        self.assertEqual(exit_code, 1)
        self.assertIn("may not replace the source state", stderr.getvalue())
        self.assertEqual(SOURCE_STATE.read_bytes(), source_before)
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = migration.main(
                (str(SOURCE_STATE), "--output", str(CANDIDATE_STATE), "--report", str(CANDIDATE_STATE))
            )
        self.assertEqual(exit_code, 1)
        self.assertIn("must be distinct", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
