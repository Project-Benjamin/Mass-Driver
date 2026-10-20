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
import tools.migrate_surface_soylent_v224_slot1_to_v225 as migration
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
SOURCE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_backups"
    / "SLUS-00669_1_v224_field550_door_clip_6df7129d.sav"
)
CANDIDATE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v225_from_6df7129d_field550_clearance.sav"
)
CANDIDATE_REPORT = CANDIDATE_STATE.with_suffix(".json")
OLD_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v224.bin"
)
NEW_DISC = (
    PROJECT_ROOT
    / "output"
    / "Xenogears_PW_CD2_mass_driver_surface_soylent_v225.bin"
)
OLD_FIELD = (
    PROJECT_ROOT
    / "work"
    / "surface_soylent_campaign_v224_stage"
    / "clones"
    / "field_550_disc1_donor"
)
NEW_FIELD = (
    PROJECT_ROOT
    / "work"
    / "surface_soylent_campaign_v225_stage"
    / "clones"
    / "field_550_disc1_donor"
)
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SurfaceSoylentV224Slot1MigrationTests(unittest.TestCase):
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
            OLD_FIELD / "07_dialogue.bin",
            NEW_FIELD / "07_dialogue.bin",
            OLD_FIELD / "01_walkmesh.bin",
            NEW_FIELD / "01_walkmesh.bin",
            ZSTD,
        )
        if not all(path.is_file() for path in required):
            raise unittest.SkipTest("Pinned V224/V225 migration fixtures unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.old_header = (OLD_FIELD / "header.bin").read_bytes()
        cls.new_header = (NEW_FIELD / "header.bin").read_bytes()
        cls.old_script = (OLD_FIELD / "05_scripts.bin").read_bytes()
        cls.new_script = (NEW_FIELD / "05_scripts.bin").read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v224_slot1_to_v225(
            cls.source,
            old_disc=OLD_DISC,
            new_disc=NEW_DISC,
            old_header=cls.old_header,
            new_header=cls.new_header,
            old_script=cls.old_script,
            new_script=cls.new_script,
            zstd=cls.zstd,
        )
        (
            cls.source_payload,
            cls.frame_start,
            cls.source_prefix,
        ) = migration._unpack_state(cls.source, cls.zstd)
        (
            cls.result_payload,
            cls.result_frame,
            cls.result_prefix,
        ) = migration._unpack_state(cls.result, cls.zstd)
        _offset, cls.source_ram = migration._ram_from_payload(cls.source_payload)
        _offset, cls.result_ram = migration._ram_from_payload(cls.result_payload)

    def test_candidate_identity_round_trip_and_report_are_frozen(self) -> None:
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
        self.assertEqual(self.result_frame, migration.SOURCE_PREFIX_SIZE)
        self.assertEqual(
            len(self.result) - self.result_frame,
            migration.OUTPUT_COMPRESSED_SIZE,
        )
        self.assertEqual(
            _sha256(self.result[self.result_frame :]),
            migration.OUTPUT_COMPRESSED_SHA256,
        )
        self.assertEqual(
            self.result_prefix,
            migration._expected_prefix(
                self.source_prefix,
                compressed_size=migration.OUTPUT_COMPRESSED_SIZE,
            ),
        )
        self.assertEqual(_sha256(self.result_prefix), migration.OUTPUT_PREFIX_SHA256)
        self.assertEqual(self.result.count(migration.OLD_CUE_NAME.encode("ascii")), 0)
        self.assertEqual(self.result.count(migration.NEW_CUE_NAME.encode("ascii")), 1)
        self.assertTrue(self.report["round_trip_verified"])
        self.assertTrue(self.report["allocator_safe"])
        if CANDIDATE_STATE.is_file():
            self.assertEqual(CANDIDATE_STATE.read_bytes(), self.result)
        if CANDIDATE_REPORT.is_file():
            self.assertEqual(
                json.loads(CANDIDATE_REPORT.read_text(encoding="utf-8")),
                self.report,
            )

    def test_disc_resources_equal_size_atel_and_loaded_header_are_exact(self) -> None:
        self.assertEqual(
            migration._diff_triplets(self.old_header, self.new_header),
            migration.HEADER_DIFFS,
        )
        self.assertEqual(
            migration._patch_reconstruction(
                self.old_script,
                migration._script_patches(),
            ),
            self.new_script,
        )
        self.assertEqual(
            len(migration._diff_offsets(self.old_script, self.new_script)),
            migration.EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED,
        )
        old_editor = AtelScript(self.old_script)
        new_editor = AtelScript(self.new_script)
        self.assertEqual(
            (old_editor.bytecode_offset, old_editor.bytecode_size),
            (migration.NORMAL_BYTECODE_OFFSET, migration.NORMAL_BYTECODE_SIZE),
        )
        self.assertEqual(
            (new_editor.bytecode_offset, new_editor.bytecode_size),
            (migration.NORMAL_BYTECODE_OFFSET, migration.NORMAL_BYTECODE_SIZE),
        )
        self.assertEqual(old_editor.get_script_pointer(0, 1), migration.SHARED_STOP_PC)
        self.assertEqual(new_editor.get_script_pointer(0, 1), migration.FORWARD_POLL_PC)
        self.assertEqual(
            new_editor.bytecode[
                migration.FORWARD_POLL_PC :
                migration.FORWARD_POLL_PC + len(migration.FORWARD_POLL)
            ],
            migration.FORWARD_POLL,
        )
        self.assertEqual(
            new_editor.bytecode[
                migration.FORWARD_POLL_PC + len(migration.FORWARD_POLL) :
                migration.FORWARD_POLL_CAVITY_END_PC
            ],
            migration.FORWARD_POLL_SOURCE_CAVITY[len(migration.FORWARD_POLL) :],
        )
        self.assertEqual(
            new_editor.bytecode[
                migration.NATIVE_EXIT_GATE_PC :
            ],
            old_editor.bytecode[migration.NATIVE_EXIT_GATE_PC :],
        )

        old_table = media_migration._archive_table(OLD_DISC)
        new_table = media_migration._archive_table(NEW_DISC)
        self.assertEqual(
            migration._diff_triplets(old_table, new_table),
            migration.ARCHIVE_TABLE_DIFFS,
        )
        table = migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        output_table = self.result_payload[table : table + migration.ARCHIVE_TABLE_SIZE]
        self.assertEqual(_sha256(output_table), migration.OUTPUT_RESIDENT_TABLE_SHA256)
        # The V224->V225 release delta and nonvolatile field-621 FAT entry are
        # synchronized; only the true volatile tail remains different.
        self.assertEqual(
            migration._diff_triplets(output_table, new_table),
            migration.RESIDENT_VS_NEW_MEDIA_DIFFS,
        )
        self.assertEqual(output_table[0x3268], 0xE0)
        self.assertEqual(output_table[0x7FFF], 0xE0)
        self.assertTrue(
            self.report["resident_archive_nonvolatile_field621_entry_normalized"]
        )
        self.assertTrue(self.report["resident_archive_volatile_tail_preserved"])

        header = migration.EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET
        source_header = self.source_payload[
            header : header + migration.OLD_HEADER_SIZE
        ]
        result_header = self.result_payload[
            header : header + migration.NEW_HEADER_SIZE
        ]
        self.assertEqual(source_header, self.old_header)
        self.assertEqual(_sha256(result_header), migration.OUTPUT_LOADED_HEADER_SHA256)
        self.assertEqual(
            migration._diff_triplets(source_header, result_header),
            migration.HEADER_DIFFS[-2:],
        )
        self.assertEqual(
            migration._diff_triplets(result_header, self.new_header),
            migration.HEADER_DIFFS[:3],
        )

    def test_exact_saved_stance_poll_and_e19_clearance_contract(self) -> None:
        actor_base = struct.unpack_from("<I", self.source_ram, FIELD_ACTORS)[0] & 0x1FFFFFFF

        def data_offset(entity: int) -> int:
            return struct.unpack_from(
                "<I",
                self.source_ram,
                actor_base
                + entity * FIELD_ACTOR_STRIDE
                + FIELD_ACTOR_DATA_POINTER,
            )[0] & 0x1FFFFFFF

        fei = data_offset(migration.FEI_ENTITY)
        carrier = data_offset(migration.CROSS_CARRIER_ENTITY)
        seal = data_offset(migration.SEAL_ENTITY)
        self.assertEqual(
            struct.unpack_from(
                "<3i",
                self.source_ram,
                fei + migration.ACTOR_DATA_POSITION_OFFSET,
            ),
            migration.EXPECTED_FEI_POSITION,
        )
        self.assertEqual(migration.EXPECTED_FEI_POSITION[2] // 65_536, 228)
        self.assertEqual(
            struct.unpack_from(
                "<4H",
                self.source_ram,
                fei + migration.ACTOR_DATA_SURFACES_OFFSET,
            ),
            migration.EXPECTED_FEI_TRIANGLES,
        )
        self.assertEqual(
            struct.unpack_from(
                "<3i",
                self.source_ram,
                carrier + migration.ACTOR_DATA_POSITION_OFFSET,
            ),
            (0, 0, 250 << 16),
        )
        self.assertEqual(
            struct.unpack_from(
                "<4H",
                self.source_ram,
                carrier + migration.ACTOR_DATA_BOUNDS_OFFSET,
            ),
            (48, 60, 32, 16),
        )
        self.assertTrue(-64 <= migration.EXPECTED_FEI_POSITION[0] // 65_536 <= 64)

        self.assertFalse(struct.unpack_from("<I", self.source_ram, seal)[0] & 0x2000)
        self.assertTrue(struct.unpack_from("<I", self.result_ram, seal)[0] & 0x2000)
        self.assertEqual(
            self.result_ram[
                seal + migration.ACTOR_DATA_BOUNDS_OFFSET :
                seal + migration.ACTOR_DATA_BOUNDS_OFFSET + 8
            ],
            migration.NEW_E19_BOUNDS,
        )
        self.assertEqual(
            struct.unpack_from(
                "<3i",
                self.result_ram,
                seal + migration.ACTOR_DATA_POSITION_OFFSET,
            ),
            (0, 0, 266 << 16),
        )
        self.assertEqual(266 - 2 * 8, 250)
        self.assertLess(228, 234)
        self.assertLess(234, 250)
        # 0x00E4 is signed 228; the second copy is the debounce threshold.
        self.assertEqual(migration.FORWARD_POLL.count(bytes.fromhex("E4 00")), 2)
        self.assertIn(bytes.fromhex("09 11 22"), migration.FORWARD_POLL)
        self.assertEqual(len(migration.FORWARD_POLL), 63)

    def test_exact_payload_whitelist_and_all_gameplay_state_are_preserved(self) -> None:
        table = migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        script = migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET
        header = migration.EXPECTED_LOADED_HEADER_PAYLOAD_OFFSET
        script_diffs = migration._diff_offsets(self.old_script, self.new_script)
        expected = {
            *(
                table + relative
                for relative, _old, _new in migration.RESIDENT_ARCHIVE_TABLE_PATCHES
            ),
            *(script + relative for relative in script_diffs),
            *(
                header + relative
                for relative, _old, _new in migration.HEADER_DIFFS[-2:]
            ),
        }
        for relative, old, new, _label in migration.RUNTIME_PATCHES:
            absolute = migration.EXPECTED_RAM_PAYLOAD_OFFSET + relative
            self.assertEqual(
                self.source_payload[absolute : absolute + len(old)],
                old,
            )
            self.assertEqual(
                self.result_payload[absolute : absolute + len(new)],
                new,
            )
            expected.update(
                absolute + index
                for index, (before, after) in enumerate(zip(old, new, strict=True))
                if before != after
            )
        actual = migration._diff_offsets(self.source_payload, self.result_payload)
        self.assertEqual(actual, tuple(sorted(expected)))
        self.assertEqual(len(actual), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        self.assertEqual(
            self.report["payload_bytes_changed"],
            migration.EXPECTED_PAYLOAD_BYTES_CHANGED,
        )
        self.assertEqual(self.report["archive_table_bytes_changed"], 6)
        self.assertEqual(self.report["resident_script_bytes_changed"], 68)
        self.assertEqual(self.report["loaded_header_bytes_changed"], 2)
        self.assertEqual(self.report["runtime_e19_bytes_changed"], 11)

        preserved = (
            (GAME_STATE, GAMESTATE_SIZE),
            (FIELD_SCRIPT_MEMORY, migration.FIELD_VARIABLE_BANK_SIZE),
            (migration.DIALOG_WINDOWS, migration.DIALOG_WINDOWS_SIZE),
        )
        for offset, size in preserved:
            self.assertEqual(
                self.result_ram[offset : offset + size],
                self.source_ram[offset : offset + size],
            )
        for address in CAMERA_VECTORS.values():
            self.assertEqual(
                self.result_ram[address : address + 16],
                self.source_ram[address : address + 16],
            )

        actor_base = struct.unpack_from("<I", self.source_ram, FIELD_ACTORS)[0] & 0x1FFFFFFF
        for entity in range(migration.SCRIPT_ENTITY_COUNT):
            record = actor_base + entity * FIELD_ACTOR_STRIDE
            data = struct.unpack_from(
                "<I",
                self.source_ram,
                record + FIELD_ACTOR_DATA_POINTER,
            )[0] & 0x1FFFFFFF
            if entity != migration.SEAL_ENTITY:
                self.assertEqual(
                    self.result_ram[record : record + FIELD_ACTOR_STRIDE],
                    self.source_ram[record : record + FIELD_ACTOR_STRIDE],
                )
                self.assertEqual(
                    self.result_ram[data : data + migration.ACTOR_DATA_SIZE],
                    self.source_ram[data : data + migration.ACTOR_DATA_SIZE],
                )
        for entity in (
            migration.FEI_ENTITY,
            migration.DOCTOR_ENTITY,
            *migration.SECURITY_ENTITIES,
        ):
            self.assertNotEqual(entity, migration.SEAL_ENTITY)
        self.assertTrue(self.report["doctor_security_runtime_preserved"])
        self.assertTrue(self.report["gamestate_party_camera_windows_preserved"])

        dialogue = migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        walkmesh = migration.EXPECTED_WALKMESH_PAYLOAD_OFFSET
        self.assertEqual(
            self.result_payload[dialogue : dialogue + migration.DIALOGUE_SIZE],
            self.source_payload[dialogue : dialogue + migration.DIALOGUE_SIZE],
        )
        self.assertEqual(
            self.result_payload[walkmesh : walkmesh + migration.WALKMESH_SIZE],
            self.source_payload[walkmesh : walkmesh + migration.WALKMESH_SIZE],
        )

    def test_wrong_source_resource_and_live_output_fail_closed(self) -> None:
        wrong_state = bytearray(self.source)
        wrong_state[0x100] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "Source Slot 1 identity"):
            migration.migrate_v224_slot1_to_v225(
                bytes(wrong_state),
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_header=self.old_header,
                new_header=self.new_header,
                old_script=self.old_script,
                new_script=self.new_script,
                zstd=self.zstd,
            )
        wrong_script = bytearray(self.new_script)
        wrong_script[-1] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "V225 field-550 script identity"):
            migration.migrate_v224_slot1_to_v225(
                self.source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_header=self.old_header,
                new_header=self.new_header,
                old_script=self.old_script,
                new_script=bytes(wrong_script),
                zstd=self.zstd,
            )

        before_size = migration.LIVE_SLOT1.stat().st_size
        before_sha = migration._file_sha256(migration.LIVE_SLOT1)
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = migration.main(
                (
                    str(SOURCE_STATE),
                    "--output",
                    str(migration.LIVE_SLOT1),
                    "--report",
                    str(CANDIDATE_REPORT),
                )
            )
        self.assertEqual(result, 1)
        self.assertIn("may not be the live Slot 1", stderr.getvalue())
        self.assertEqual(migration.LIVE_SLOT1.stat().st_size, before_size)
        self.assertEqual(migration._file_sha256(migration.LIVE_SLOT1), before_sha)


if __name__ == "__main__":
    unittest.main()
