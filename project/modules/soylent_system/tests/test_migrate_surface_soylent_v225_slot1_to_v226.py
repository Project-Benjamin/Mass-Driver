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
import tools.migrate_surface_soylent_v225_slot1_to_v226 as migration
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
SOURCE_STATE = PROJECT_ROOT / "work" / "save_backups" / "SLUS-00669_1_v225_auto_open_408a5dc9.sav"
CANDIDATE_STATE = PROJECT_ROOT / "work" / "save_candidates" / "SLUS-00669_1_v226_from_408a5dc9_field592_x_only.sav"
CANDIDATE_REPORT = CANDIDATE_STATE.with_suffix(".json")
OLD_DISC = PROJECT_ROOT / "output" / "Xenogears_PW_CD2_mass_driver_surface_soylent_v225.bin"
NEW_DISC = PROJECT_ROOT / "output" / "Xenogears_PW_CD2_mass_driver_surface_soylent_v226.bin"
OLD_FIELD = PROJECT_ROOT / "work" / "surface_soylent_campaign_v225_stage" / "clones" / "field_592_disc1_donor"
NEW_STAGE = PROJECT_ROOT / "work" / "surface_soylent_campaign_v226_stage"
NEW_FIELD = NEW_STAGE / "clones" / "field_592_disc1_donor"
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SurfaceSoylentV225Slot1MigrationTests(unittest.TestCase):
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
            raise unittest.SkipTest("Pinned V225/V226 migration fixtures unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.old_header = (OLD_FIELD / "header.bin").read_bytes()
        cls.new_header = (NEW_FIELD / "header.bin").read_bytes()
        cls.old_script = (OLD_FIELD / "05_scripts.bin").read_bytes()
        cls.new_script = (NEW_FIELD / "05_scripts.bin").read_bytes()
        cls.manifest = (NEW_STAGE / "manifest.json").read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v225_slot1_to_v226(
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
        self.assertEqual((len(self.source), _sha256(self.source)), (migration.SOURCE_STATE_SIZE, migration.SOURCE_STATE_SHA256))
        self.assertEqual((len(self.result), _sha256(self.result)), (migration.OUTPUT_STATE_SIZE, migration.OUTPUT_STATE_SHA256))
        self.assertEqual((len(self.result_payload), _sha256(self.result_payload)), (migration.SOURCE_PAYLOAD_SIZE, migration.OUTPUT_PAYLOAD_SHA256))
        self.assertEqual(_sha256(self.result_ram), migration.OUTPUT_RAM_SHA256)
        self.assertEqual(self.result_frame, self.frame_start)
        self.assertEqual(len(self.result) - self.result_frame, migration.OUTPUT_COMPRESSED_SIZE)
        self.assertEqual(_sha256(self.result[self.result_frame :]), migration.OUTPUT_COMPRESSED_SHA256)
        self.assertEqual(self.result_prefix, migration._expected_prefix(self.source_prefix, compressed_size=migration.OUTPUT_COMPRESSED_SIZE))
        self.assertEqual(_sha256(self.result_prefix), migration.OUTPUT_PREFIX_SHA256)
        self.assertEqual(self.result.count(migration.OLD_CUE_NAME.encode("ascii")), 0)
        self.assertEqual(self.result.count(migration.NEW_CUE_NAME.encode("ascii")), 1)
        self.assertTrue(self.report["round_trip_verified"])
        self.assertTrue(self.report["allocator_safe"])
        self.assertEqual(self.report["payload_bytes_changed"], 70)
        if CANDIDATE_STATE.is_file():
            self.assertEqual(CANDIDATE_STATE.read_bytes(), self.result)
        if CANDIDATE_REPORT.is_file():
            self.assertEqual(json.loads(CANDIDATE_REPORT.read_text(encoding="utf-8")), self.report)

    def test_media_stage_and_x_only_atel_contract_are_exact(self) -> None:
        self.assertEqual((len(self.manifest), _sha256(self.manifest)), (migration.V226_STAGE_MANIFEST_SIZE, migration.V226_STAGE_MANIFEST_SHA256))
        self.assertEqual(migration._diff_triplets(self.old_header, self.new_header), migration.HEADER_DIFFS)
        self.assertEqual(migration._patch_reconstruction(self.old_script, migration._script_patches()), self.new_script)
        self.assertEqual(len(migration._diff_offsets(self.old_script, self.new_script)), 62)
        old_atel, new_atel = AtelScript(self.old_script), AtelScript(self.new_script)
        self.assertEqual(old_atel.get_script_pointer(0, 1), migration.AUTO_POLL_PC)
        self.assertEqual(new_atel.get_script_pointer(0, 1), migration.SHARED_STOP_PC)
        self.assertEqual(old_atel.bytecode[migration.AUTO_POLL_PC : migration.AUTO_POLL_CAVITY_END_PC], migration.AUTO_POLL_CAVITY)
        self.assertEqual(new_atel.bytecode[migration.AUTO_POLL_PC : migration.AUTO_POLL_CAVITY_END_PC], migration.X_ONLY_CAVITY)
        self.assertEqual(new_atel.get_script_pointer(migration.CROSS_CARRIER_ENTITY, 2), migration.NATIVE_X_ACTION_PC)
        self.assertFalse(any(
            migration.AUTO_POLL_PC <= new_atel.get_script_pointer(entity, script) < migration.AUTO_POLL_CAVITY_END_PC
            for entity in range(new_atel.entity_count)
            for script in range(32)
        ))
        old_table = media_migration._archive_table(OLD_DISC)
        new_table = media_migration._archive_table(NEW_DISC)
        self.assertEqual(migration._diff_triplets(old_table, new_table), migration.ARCHIVE_TABLE_DIFFS)
        table = migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        source_table = self.source_payload[table : table + migration.ARCHIVE_TABLE_SIZE]
        result_table = self.result_payload[table : table + migration.ARCHIVE_TABLE_SIZE]
        self.assertEqual(migration._diff_triplets(source_table, old_table), migration.RESIDENT_VS_MEDIA_DIFFS)
        self.assertEqual(migration._diff_triplets(result_table, new_table), migration.RESIDENT_VS_MEDIA_DIFFS)
        self.assertEqual(_sha256(result_table), migration.OUTPUT_RESIDENT_TABLE_SHA256)
        self.assertEqual(result_table[0x7FFF], 0xE0)

    def test_exact_70_byte_payload_whitelist(self) -> None:
        table = migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        script = migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET
        expected = {
            *(table + relative for relative, _old, _new in migration.ARCHIVE_TABLE_DIFFS),
            *(script + relative for relative in migration._diff_offsets(self.old_script, self.new_script)),
        }
        for relative, old, new, _label in migration.RUNTIME_PATCHES:
            absolute = migration.EXPECTED_RAM_PAYLOAD_OFFSET + relative
            self.assertEqual(self.source_payload[absolute : absolute + len(old)], old)
            self.assertEqual(self.result_payload[absolute : absolute + len(new)], new)
            expected.update(
                absolute + index
                for index, (before, after) in enumerate(zip(old, new, strict=True))
                if before != after
            )
        actual = migration._diff_offsets(self.source_payload, self.result_payload)
        self.assertEqual(actual, tuple(sorted(expected)))
        self.assertEqual(len(actual), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        self.assertEqual(self.report["archive_table_bytes_changed"], 4)
        self.assertEqual(self.report["resident_script_bytes_changed"], 62)
        self.assertEqual(self.report["runtime_e0_bytes_changed"], 4)

    def test_only_e0_pc_moves_and_all_required_gameplay_spans_are_preserved(self) -> None:
        actor_base = struct.unpack_from("<I", self.source_ram, FIELD_ACTORS)[0] & 0x1FFFFFFF

        def data_offset(entity: int) -> int:
            return struct.unpack_from(
                "<I",
                self.source_ram,
                actor_base + entity * FIELD_ACTOR_STRIDE + FIELD_ACTOR_DATA_POINTER,
            )[0] & 0x1FFFFFFF

        controller = data_offset(0)
        self.assertEqual(self.source_ram[controller + migration.ACTOR_SCRIPT_SLOT_OFFSET : controller + migration.ACTOR_SCRIPT_SLOT_OFFSET + 4], bytes.fromhex("8A 04 00 FF"))
        self.assertEqual(self.result_ram[controller + migration.ACTOR_SCRIPT_SLOT_OFFSET : controller + migration.ACTOR_SCRIPT_SLOT_OFFSET + 4], bytes.fromhex("8C 06 00 FF"))
        self.assertEqual(self.source_ram[controller + migration.ACTOR_CURRENT_PC_OFFSET : controller + migration.ACTOR_CURRENT_PC_OFFSET + 4], bytes.fromhex("8A 04 00 00"))
        self.assertEqual(self.result_ram[controller + migration.ACTOR_CURRENT_PC_OFFSET : controller + migration.ACTOR_CURRENT_PC_OFFSET + 4], bytes.fromhex("8C 06 00 00"))
        for entity in range(1, migration.SCRIPT_ENTITY_COUNT):
            record = actor_base + entity * FIELD_ACTOR_STRIDE
            data = data_offset(entity)
            self.assertEqual(self.result_ram[record : record + FIELD_ACTOR_STRIDE], self.source_ram[record : record + FIELD_ACTOR_STRIDE])
            self.assertEqual(self.result_ram[data : data + migration.ACTOR_DATA_SIZE], self.source_ram[data : data + migration.ACTOR_DATA_SIZE])
        for entity in (migration.FEI_ENTITY, migration.CROSS_CARRIER_ENTITY, migration.DOOR_LEAF_ENTITY, migration.RECTANGLE_ENTITY):
            self.assertNotEqual(entity, migration.CONTROLLER_ENTITY)
        self.assertTrue(self.report["fei_preserved"])
        self.assertTrue(self.report["e17_carrier_preserved"])
        self.assertTrue(self.report["e18_closed_leaf_preserved"])
        self.assertTrue(self.report["e20_rectangle_preserved"])
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
            self.assertEqual(self.result_payload[offset : offset + size], self.source_payload[offset : offset + size])
        self.assertEqual(
            self.result_payload[migration.EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET : migration.EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET + migration.OLD_HEADER_SIZE],
            self.old_header,
        )

    def test_wrong_source_resource_and_live_output_fail_closed(self) -> None:
        wrong_state = bytearray(self.source)
        wrong_state[0x100] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "Source Slot 1 identity"):
            migration.migrate_v225_slot1_to_v226(
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
        wrong_script = bytearray(self.new_script)
        wrong_script[-1] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "V226 field-592 script identity"):
            migration.migrate_v225_slot1_to_v226(
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
        before = (migration.LIVE_SLOT1.stat().st_size, migration._file_sha256(migration.LIVE_SLOT1))
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = migration.main((str(SOURCE_STATE), "--output", str(migration.LIVE_SLOT1), "--report", str(CANDIDATE_REPORT)))
        self.assertEqual(result, 1)
        self.assertIn("may not be the live Slot 1", stderr.getvalue())
        self.assertEqual((migration.LIVE_SLOT1.stat().st_size, migration._file_sha256(migration.LIVE_SLOT1)), before)

        source_before = SOURCE_STATE.read_bytes()
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = migration.main((str(SOURCE_STATE), "--output", str(CANDIDATE_STATE), "--report", str(SOURCE_STATE)))
        self.assertEqual(result, 1)
        self.assertIn("may not replace the source state", stderr.getvalue())
        self.assertEqual(SOURCE_STATE.read_bytes(), source_before)

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = migration.main((str(SOURCE_STATE), "--output", str(CANDIDATE_STATE), "--report", str(CANDIDATE_STATE)))
        self.assertEqual(result, 1)
        self.assertIn("must be distinct", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
