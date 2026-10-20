from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

from contextlib import redirect_stderr
import hashlib
import io
from pathlib import Path
import struct
import unittest

import tools.migrate_duckstation_disc_state as media_migration
import tools.migrate_surface_soylent_v216_slot1_to_v217 as migration
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
    / "SLUS-00669_1_v216_door_clip_1114bf36.sav"
)
CANDIDATE_STATE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v217_from_1114bf36_door_clearance.sav"
)
OLD_DISC = PROJECT_ROOT / "output" / "Xenogears_PW_CD2_mass_driver_surface_soylent_v216.bin"
NEW_DISC = PROJECT_ROOT / "output" / "Xenogears_PW_CD2_mass_driver_surface_soylent_v217.bin"
OLD_FIELD = PROJECT_ROOT / "work" / "surface_soylent_campaign_v216_stage" / "clones" / "field_593_disc1_donor"
NEW_FIELD = PROJECT_ROOT / "work" / "surface_soylent_campaign_v217_stage" / "clones" / "field_593_disc1_donor"
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SurfaceSoylentV216Slot1MigrationTests(unittest.TestCase):
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
            ZSTD,
        )
        if not all(path.is_file() for path in required):
            raise unittest.SkipTest("Pinned V216/V217 migration fixtures unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.old_header = (OLD_FIELD / "header.bin").read_bytes()
        cls.new_header = (NEW_FIELD / "header.bin").read_bytes()
        cls.old_script = (OLD_FIELD / "05_scripts.bin").read_bytes()
        cls.new_script = (NEW_FIELD / "05_scripts.bin").read_bytes()
        cls.old_dialogue = (OLD_FIELD / "07_dialogue.bin").read_bytes()
        cls.new_dialogue = (NEW_FIELD / "07_dialogue.bin").read_bytes()
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v216_slot1_to_v217(
            cls.source,
            old_disc=OLD_DISC,
            new_disc=NEW_DISC,
            old_header=cls.old_header,
            new_header=cls.new_header,
            old_script=cls.old_script,
            new_script=cls.new_script,
            old_dialogue=cls.old_dialogue,
            new_dialogue=cls.new_dialogue,
            zstd=cls.zstd,
        )
        cls.source_payload, cls.frame_start, cls.source_prefix = migration._unpack_state(cls.source, cls.zstd)
        cls.result_payload, cls.result_frame, cls.result_prefix = migration._unpack_state(cls.result, cls.zstd)
        _offset, cls.source_ram = migration._ram_from_payload(cls.source_payload)
        _offset, cls.result_ram = migration._ram_from_payload(cls.result_payload)

    def test_candidate_identity_round_trip_and_formal_file_are_frozen(self) -> None:
        self.assertEqual(
            (len(self.result), _sha256(self.result)),
            (migration.EXPECTED_OUTPUT_SIZE, migration.EXPECTED_OUTPUT_SHA256),
        )
        self.assertEqual(_sha256(self.result_payload), migration.EXPECTED_OUTPUT_PAYLOAD_SHA256)
        self.assertEqual(_sha256(self.result_ram), migration.OUTPUT_RAM_SHA256)
        self.assertEqual(self.frame_start, migration.EXPECTED_FRAME_START)
        self.assertEqual(self.result_frame, self.frame_start)
        self.assertEqual(len(self.result) - self.result_frame, migration.EXPECTED_OUTPUT_COMPRESSED_SIZE)
        self.assertEqual(
            self.result_prefix,
            migration._expected_prefix(
                self.source_prefix,
                compressed_size=len(self.result) - self.frame_start,
            ),
        )
        self.assertEqual(_sha256(self.result_prefix), migration.EXPECTED_OUTPUT_PREFIX_SHA256)
        self.assertEqual(self.result.count(migration.OLD_CUE_NAME.encode()), 0)
        self.assertEqual(self.result.count(migration.NEW_CUE_NAME.encode()), 1)
        self.assertTrue(self.report["round_trip_verified"])
        self.assertTrue(self.report["allocator_safe"])
        if CANDIDATE_STATE.is_file():
            self.assertEqual(CANDIDATE_STATE.read_bytes(), self.result)

    def test_exact_saved_failure_and_v217_clearance_contract(self) -> None:
        actor_base = struct.unpack_from("<I", self.source_ram, FIELD_ACTORS)[0] & 0x1FFFFFFF
        fei = migration.EXPECTED_ACTOR_DATA_POINTERS[migration.FEI_ENTITY]
        cross = migration.EXPECTED_ACTOR_DATA_POINTERS[migration.CROSS_CARRIER_ENTITY]
        leaf = migration.EXPECTED_ACTOR_DATA_POINTERS[migration.DOOR_LEAF_ENTITY]
        seal = migration.EXPECTED_ACTOR_DATA_POINTERS[migration.SEAL_ENTITY]
        self.assertEqual(
            struct.unpack_from("<3i", self.source_ram, fei + migration.ACTOR_DATA_POSITION_OFFSET),
            migration.EXPECTED_FEI_POSITION,
        )
        self.assertEqual(
            struct.unpack_from("<4H", self.source_ram, fei + migration.ACTOR_DATA_SURFACES_OFFSET),
            migration.EXPECTED_FEI_TRIANGLES,
        )
        self.assertEqual(
            struct.unpack_from("<H", self.source_ram, fei + migration.ACTOR_FACING_OFFSET)[0] & 0xFFF,
            migration.EXPECTED_FEI_FACING,
        )
        # E17's unchanged ghost action is selectable at this stance.
        cross_x, _cross_y, cross_z = struct.unpack_from(
            "<3i", self.source_ram, cross + migration.ACTOR_DATA_POSITION_OFFSET
        )
        self.assertEqual((cross_x, cross_z), (0, 250 << 16))
        self.assertEqual(
            struct.unpack_from("<4H", self.source_ram, cross + migration.ACTOR_DATA_BOUNDS_OFFSET),
            (48, 60, 32, 16),
        )
        self.assertTrue(-64 <= migration.EXPECTED_FEI_POSITION[0] // 65536 <= 64)
        self.assertTrue(202 <= migration.EXPECTED_FEI_POSITION[2] // 65536 <= 298)
        # E18 is visibly closed rather than partway through its helper.
        leaf_record = actor_base + migration.DOOR_LEAF_ENTITY * FIELD_ACTOR_STRIDE
        self.assertEqual(
            self.source_ram[leaf + migration.ACTOR_CURRENT_PC_OFFSET : leaf + migration.ACTOR_CURRENT_PC_OFFSET + 4],
            migration.EXPECTED_LEAF_CURRENT,
        )
        self.assertEqual(
            struct.unpack_from(
                "<H", self.source_ram, FIELD_SCRIPT_MEMORY + migration.CLOSED_LEAF_HELPER_OPERAND
            )[0],
            0,
        )
        self.assertEqual(
            self.source_ram[leaf_record + 0x0C : leaf_record + 0x1E],
            migration.CLOSED_LEAF_MATRIX,
        )
        # The source seal is the active z250 circle; the result is a z266
        # rectangle whose physical player-side plane is z250 (MoveCheck uses
        # no extra player radius for rectangles).  The poll fires at integer
        # z230, before the disconnected retail edge at z234.
        self.assertFalse(struct.unpack_from("<I", self.source_ram, seal)[0] & 0x2000)
        self.assertTrue(struct.unpack_from("<I", self.result_ram, seal)[0] & 0x2000)
        self.assertEqual(
            self.result_ram[
                seal + migration.ACTOR_DATA_BOUNDS_OFFSET : seal + migration.ACTOR_DATA_BOUNDS_OFFSET + 8
            ],
            migration.NEW_E20_BOUNDS,
        )
        self.assertEqual(
            struct.unpack_from("<3i", self.result_ram, seal + migration.ACTOR_DATA_POSITION_OFFSET),
            (0, 0, 266 << 16),
        )
        self.assertLess(migration.EXPECTED_FEI_POSITION[2] / 65536, 230)
        self.assertEqual(266 - 2 * 8, 250)
        self.assertLess(230, 234)

    def test_resources_compact_script_and_exact_payload_whitelist(self) -> None:
        self.assertEqual(migration._diff_triplets(self.old_header, self.new_header), migration.HEADER_DIFFS)
        self.assertEqual(self.old_dialogue, self.new_dialogue)
        self.assertEqual(
            migration._patch_reconstruction(self.old_script, migration._normal_script_patches()),
            self.new_script,
        )
        old_table = media_migration._archive_table(OLD_DISC)
        new_table = media_migration._archive_table(NEW_DISC)
        self.assertEqual(migration._diff_triplets(old_table, new_table), migration.ARCHIVE_TABLE_DIFFS)
        table = migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        self.assertEqual(
            self.result_payload[table : table + migration.ARCHIVE_TABLE_SIZE],
            new_table[:-1] + bytes((migration.EXPECTED_VOLATILE_TABLE_VALUE,)),
        )
        self.assertEqual(
            _sha256(self.result_payload[table : table + migration.ARCHIVE_TABLE_SIZE]),
            migration.OUTPUT_RESIDENT_TABLE_SHA256,
        )

        script = migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET
        source_script = self.source_payload[script : script + migration.RESIDENT_SCRIPT_SIZE]
        result_script = self.result_payload[script : script + migration.RESIDENT_SCRIPT_SIZE]
        expected_script = migration._patch_reconstruction(source_script, migration._compact_script_patches())
        self.assertEqual(result_script, expected_script)
        self.assertEqual(_sha256(result_script), migration.OUTPUT_RESIDENT_SCRIPT_SHA256)
        script_diffs = migration._diff_offsets(source_script, result_script)
        expected = {
            *(table + relative for relative, _old, _new in migration.ARCHIVE_TABLE_DIFFS),
            *(script + relative for relative in script_diffs),
        }
        for relative, old, new, _label in migration.RUNTIME_PATCHES:
            self.assertEqual(
                self.source_payload[
                    migration.EXPECTED_RAM_PAYLOAD_OFFSET + relative :
                    migration.EXPECTED_RAM_PAYLOAD_OFFSET + relative + len(old)
                ],
                old,
            )
            self.assertEqual(
                self.result_payload[
                    migration.EXPECTED_RAM_PAYLOAD_OFFSET + relative :
                    migration.EXPECTED_RAM_PAYLOAD_OFFSET + relative + len(new)
                ],
                new,
            )
            expected.update(
                migration.EXPECTED_RAM_PAYLOAD_OFFSET + relative + index
                for index, (before, after) in enumerate(zip(old, new, strict=True))
                if before != after
            )
        actual = migration._diff_offsets(self.source_payload, self.result_payload)
        self.assertEqual(actual, tuple(sorted(expected)))
        self.assertEqual(len(actual), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        self.assertEqual(self.report["payload_bytes_changed"], 60)

    def test_retired_cavity_allocator_native_action_and_scheduler_are_safe(self) -> None:
        script = migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET
        source = AtelScript(self.source_payload[script : script + migration.RESIDENT_SCRIPT_SIZE])
        result = AtelScript(self.result_payload[script : script + migration.RESIDENT_SCRIPT_SIZE])
        self.assertEqual((source.bytecode_offset, source.bytecode_size), (0x5C4, 0x77C))
        self.assertEqual((result.bytecode_offset, result.bytecode_size), (0x5C4, 0x77C))
        self.assertLessEqual(len(result.to_bytes()), migration.SCRIPT_ALLOCATED_CAPACITY)
        self.assertEqual(source.get_script_pointer(0, 1), migration.SHARED_STOP_PC)
        self.assertEqual(result.get_script_pointer(0, 1), migration.FORWARD_POLL_PC)
        self.assertEqual(
            result.bytecode[
                migration.FORWARD_POLL_PC : migration.FORWARD_POLL_PC + len(migration.FORWARD_POLL)
            ],
            migration.FORWARD_POLL,
        )
        self.assertEqual(
            result.bytecode[
                migration.FORWARD_POLL_PC + len(migration.FORWARD_POLL) :
                migration.FORWARD_POLL_CAVITY_END_PC
            ],
            migration.FORWARD_POLL_SOURCE_CAVITY[len(migration.FORWARD_POLL) :],
        )
        cavity_entries = tuple(
            (entity, slot)
            for entity in range(result.entity_count)
            for slot in range(32)
            if migration.FORWARD_POLL_PC
            <= result.get_script_pointer(entity, slot)
            < migration.FORWARD_POLL_CAVITY_END_PC
        )
        self.assertEqual(cavity_entries, ((0, 1),))
        self.assertEqual(
            result.bytecode[migration.COMPACT_NATIVE_ACTION_PC :],
            migration.NATIVE_ACTION,
        )
        controller = migration.EXPECTED_ACTOR_DATA_POINTERS[0]
        # Repointing e0:s1 is sufficient: the finished runtime stays at the
        # shared STOP and the normal scheduler relaunches its update entry.
        self.assertEqual(
            self.result_ram[controller : controller + migration.ACTOR_DATA_SIZE],
            self.source_ram[controller : controller + migration.ACTOR_DATA_SIZE],
        )
        self.assertEqual(
            self.result_ram[
                controller + migration.ACTOR_CURRENT_PC_OFFSET : controller + migration.ACTOR_CURRENT_PC_OFFSET + 4
            ],
            migration.EXPECTED_CONTROLLER_CURRENT,
        )

    def test_only_e20_runtime_changes_and_all_critical_state_is_preserved(self) -> None:
        actor_base = struct.unpack_from("<I", self.source_ram, FIELD_ACTORS)[0] & 0x1FFFFFFF
        for entity in range(migration.SCRIPT_ENTITY_COUNT):
            record = actor_base + entity * FIELD_ACTOR_STRIDE
            actor_data = struct.unpack_from(
                "<I", self.source_ram, record + FIELD_ACTOR_DATA_POINTER
            )[0] & 0x1FFFFFFF
            if entity == migration.SEAL_ENTITY:
                self.assertEqual(
                    _sha256(self.result_ram[record : record + migration.ACTOR_RECORD_SIZE]),
                    migration.OUTPUT_E20_RECORD_SHA256,
                )
                self.assertEqual(
                    _sha256(self.result_ram[actor_data : actor_data + migration.ACTOR_DATA_SIZE]),
                    migration.OUTPUT_E20_ACTOR_DATA_SHA256,
                )
            else:
                self.assertEqual(
                    self.result_ram[record : record + migration.ACTOR_RECORD_SIZE],
                    self.source_ram[record : record + migration.ACTOR_RECORD_SIZE],
                )
                self.assertEqual(
                    self.result_ram[actor_data : actor_data + migration.ACTOR_DATA_SIZE],
                    self.source_ram[actor_data : actor_data + migration.ACTOR_DATA_SIZE],
                )
        preserved = (
            (GAME_STATE, GAMESTATE_SIZE),
            (FIELD_SCRIPT_MEMORY, migration.FIELD_VARIABLE_BANK_SIZE),
            (migration.DIALOG_WINDOWS, migration.DIALOG_WINDOWS_SIZE),
            (migration.LOADED_HEADER_RAM_OFFSET, migration.LOADED_HEADER_SIZE),
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
        self.assertEqual(
            self.result_payload[
                migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET :
                migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET + migration.OUTPUT_RESIDENT_DIALOGUE_SIZE
            ],
            self.source_payload[
                migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET :
                migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET + migration.SOURCE_RESIDENT_DIALOGUE_SIZE
            ],
        )
        self.assertEqual(
            self.result_payload[
                migration.EXPECTED_WALKMESH_PAYLOAD_OFFSET :
                migration.EXPECTED_WALKMESH_PAYLOAD_OFFSET + migration.WALKMESH_SIZE
            ],
            self.source_payload[
                migration.EXPECTED_WALKMESH_PAYLOAD_OFFSET :
                migration.EXPECTED_WALKMESH_PAYLOAD_OFFSET + migration.WALKMESH_SIZE
            ],
        )
        bank = self.result_ram[
            FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + migration.FIELD_VARIABLE_BANK_SIZE
        ]
        self.assertEqual(
            struct.unpack_from("<H", bank, migration.QUARANTINE_CARD_OPERAND)[0],
            migration.EXPECTED_QUARANTINE_WORD,
        )
        self.assertTrue(self.report["gamestate_party_camera_preserved"])
        self.assertTrue(self.report["walkmesh_preserved"])

    def test_wrong_source_resource_and_live_output_fail_closed(self) -> None:
        wrong_state = bytearray(self.source)
        wrong_state[0x100] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "Source Slot 1 identity"):
            migration.migrate_v216_slot1_to_v217(
                bytes(wrong_state),
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_header=self.old_header,
                new_header=self.new_header,
                old_script=self.old_script,
                new_script=self.new_script,
                old_dialogue=self.old_dialogue,
                new_dialogue=self.new_dialogue,
                zstd=self.zstd,
            )
        wrong_script = bytearray(self.new_script)
        wrong_script[-1] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "V217 script identity"):
            migration.migrate_v216_slot1_to_v217(
                self.source,
                old_disc=OLD_DISC,
                new_disc=NEW_DISC,
                old_header=self.old_header,
                new_header=self.new_header,
                old_script=self.old_script,
                new_script=bytes(wrong_script),
                old_dialogue=self.old_dialogue,
                new_dialogue=self.new_dialogue,
                zstd=self.zstd,
            )

        before_size = migration.LIVE_SLOT1.stat().st_size
        before_sha = migration._file_sha256(migration.LIVE_SLOT1)
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = migration.main(
                (
                    str(SOURCE_STATE),
                    str(migration.LIVE_SLOT1),
                    "--old-disc",
                    str(OLD_DISC),
                    "--new-disc",
                    str(NEW_DISC),
                    "--old-header",
                    str(OLD_FIELD / "header.bin"),
                    "--new-header",
                    str(NEW_FIELD / "header.bin"),
                    "--old-script",
                    str(OLD_FIELD / "05_scripts.bin"),
                    "--new-script",
                    str(NEW_FIELD / "05_scripts.bin"),
                    "--old-dialogue",
                    str(OLD_FIELD / "07_dialogue.bin"),
                    "--new-dialogue",
                    str(NEW_FIELD / "07_dialogue.bin"),
                    "--zstd",
                    str(ZSTD),
                )
            )
        self.assertEqual(result, 1)
        self.assertIn("may not be the live Slot 1", stderr.getvalue())
        self.assertEqual(migration.LIVE_SLOT1.stat().st_size, before_size)
        self.assertEqual(migration._file_sha256(migration.LIVE_SLOT1), before_sha)


if __name__ == "__main__":
    unittest.main()
