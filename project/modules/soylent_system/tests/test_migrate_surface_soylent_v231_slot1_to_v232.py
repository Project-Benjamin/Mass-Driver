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
import tools.migrate_surface_soylent_v231_slot1_to_v232 as migration
from tools.xgdeathblows import GAMESTATE_SIZE
from tools.xgscript import AtelScript
from work.read_duckstation_runtime import (
    CAMERA_VECTORS,
    FIELD_ACTOR_DATA_POINTER,
    FIELD_ACTOR_STRIDE,
    FIELD_SCRIPT_MEMORY,
    GAME_STATE,
    RAM_SIZE,
    _psx_ram_offset,
)


PROJECT_ROOT = REPOSITORY_ROOT


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SurfaceSoylentV231Slot1ToV232Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_path = migration.SOURCE_FIXTURE
        cls.candidate_path = (
            PROJECT_ROOT
            / "work"
            / "save_candidates"
            / "SLUS-00669_1_v232_from_6adde32f_field593_terminal_proximity.sav"
        )
        cls.report_path = cls.candidate_path.with_suffix(".json")
        cls.old_disc = (
            PROJECT_ROOT
            / "output"
            / migration.OLD_CUE_NAME.replace(".cue", ".bin")
        )
        cls.new_disc = (
            PROJECT_ROOT
            / "output"
            / migration.NEW_CUE_NAME.replace(".cue", ".bin")
        )
        cls.old_stage = PROJECT_ROOT / "work" / "surface_soylent_campaign_v231_stage"
        cls.new_stage = PROJECT_ROOT / "work" / "surface_soylent_campaign_v232_stage"
        cls.old_clone = cls.old_stage / "clones" / "field_593_disc1_donor"
        cls.new_clone = cls.new_stage / "clones" / "field_593_disc1_donor"
        cls.zstd_path = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"
        cls.zstd = media_migration._Zstd(cls.zstd_path)

        cls.source_state = cls.source_path.read_bytes()
        cls.old_manifest = (cls.old_stage / "manifest.json").read_bytes()
        cls.new_manifest = (cls.new_stage / "manifest.json").read_bytes()
        cls.old_script = (cls.old_clone / "05_scripts.bin").read_bytes()
        cls.new_script = (cls.new_clone / "05_scripts.bin").read_bytes()
        cls.old_header = (cls.old_clone / "header.bin").read_bytes()
        cls.new_header = (cls.new_clone / "header.bin").read_bytes()
        cls.old_dialogue = (cls.old_clone / "07_dialogue.bin").read_bytes()
        cls.new_dialogue = (cls.new_clone / "07_dialogue.bin").read_bytes()

        cls.result, cls.report = migration.migrate_v231_slot1_to_v232(
            cls.source_state,
            old_disc=cls.old_disc,
            new_disc=cls.new_disc,
            old_manifest=cls.old_manifest,
            new_manifest=cls.new_manifest,
            old_script=cls.old_script,
            new_script=cls.new_script,
            old_header=cls.old_header,
            new_header=cls.new_header,
            old_dialogue=cls.old_dialogue,
            new_dialogue=cls.new_dialogue,
            zstd=cls.zstd,
        )
        (
            cls.source_payload,
            cls.source_frame,
            cls.source_prefix,
        ) = migration._unpack_state(cls.source_state, cls.zstd)
        (
            cls.result_payload,
            cls.result_frame,
            cls.result_prefix,
        ) = migration._unpack_state(cls.result, cls.zstd)
        cls.ram_offset = _psx_ram_offset(cls.source_payload)
        cls.source_ram = cls.source_payload[
            cls.ram_offset : cls.ram_offset + RAM_SIZE
        ]
        cls.result_ram = cls.result_payload[
            cls.ram_offset : cls.ram_offset + RAM_SIZE
        ]
        cls.actor_array = migration._guest_ram_offset(
            migration.EXPECTED_ACTOR_ARRAY_GUEST_POINTER,
            "field actor array",
        )

    @classmethod
    def _actor_data(cls, ram: bytes, entity: int) -> int:
        record = cls.actor_array + entity * FIELD_ACTOR_STRIDE
        return migration._guest_ram_offset(
            struct.unpack_from("<I", ram, record + FIELD_ACTOR_DATA_POINTER)[0],
            f"e{entity} ActorData",
        )

    def test_candidate_report_and_round_trip_have_frozen_identities(self) -> None:
        self.assertEqual(len(self.source_state), migration.SOURCE_STATE_SIZE)
        self.assertEqual(_sha256(self.source_state), migration.SOURCE_STATE_SHA256)
        self.assertEqual(len(self.result), migration.OUTPUT_STATE_SIZE)
        self.assertEqual(_sha256(self.result), migration.OUTPUT_STATE_SHA256)
        self.assertEqual(self.result_frame, migration.SOURCE_PREFIX_SIZE)
        self.assertEqual(
            len(self.result) - self.result_frame,
            migration.OUTPUT_COMPRESSED_SIZE,
        )
        self.assertEqual(
            _sha256(self.result[self.result_frame :]),
            migration.OUTPUT_COMPRESSED_SHA256,
        )
        self.assertEqual(_sha256(self.result_prefix), migration.OUTPUT_PREFIX_SHA256)
        self.assertEqual(_sha256(self.result_payload), migration.OUTPUT_PAYLOAD_SHA256)
        self.assertEqual(_sha256(self.result_ram), migration.OUTPUT_RAM_SHA256)

        report_blob = migration._report_blob(self.report)
        self.assertEqual(len(report_blob), migration.OUTPUT_REPORT_SIZE)
        self.assertEqual(_sha256(report_blob), migration.OUTPUT_REPORT_SHA256)
        self.assertEqual(self.candidate_path.read_bytes(), self.result)
        self.assertEqual(self.report_path.read_bytes(), report_blob)
        self.assertEqual(json.loads(report_blob), self.report)
        self.assertTrue(self.report["round_trip_verified"])
        self.assertTrue(self.report["safe_to_mount_after_duckstation_is_fully_closed"])
        self.assertFalse(self.report["live_slot1_modified"])

    def test_prefix_switches_only_to_v232_and_payload_uses_exact_whitelist(self) -> None:
        old_name = migration.OLD_CUE_NAME.encode("ascii")
        new_name = migration.NEW_CUE_NAME.encode("ascii")
        self.assertEqual(self.source_state.count(old_name), 1)
        self.assertEqual(self.source_state.count(new_name), 0)
        self.assertEqual(self.result.count(old_name), 0)
        self.assertEqual(self.result.count(new_name), 1)
        self.assertEqual(
            len(migration._diff_offsets(self.source_prefix, self.result_prefix)),
            migration.EXPECTED_PREFIX_BYTES_CHANGED,
        )

        old_table = media_migration._archive_table(self.old_disc)
        new_table = media_migration._archive_table(self.new_disc)
        source_resident_table = self.source_payload[
            migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
            migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
            + migration.ARCHIVE_TABLE_SIZE
        ]
        result_resident_table = self.result_payload[
            migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
            migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
            + migration.ARCHIVE_TABLE_SIZE
        ]
        self.assertEqual(
            source_resident_table,
            old_table[:-1] + bytes((migration.EXPECTED_VOLATILE_TABLE_VALUE,)),
        )
        self.assertEqual(
            result_resident_table,
            new_table[:-1] + bytes((migration.EXPECTED_VOLATILE_TABLE_VALUE,)),
        )
        self.assertEqual(
            migration._diff_triplets(source_resident_table, result_resident_table),
            migration.ARCHIVE_TABLE_DIFFS,
        )

        resident_header = bytearray(self.old_header)
        resident_header[0x2CC] = 0x59
        resident_header = bytes(resident_header)
        table_offsets = {
            migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + offset
            for offset, _old, _new in migration.ARCHIVE_TABLE_DIFFS
        }
        script_offsets = {
            migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + offset
            for offset in migration._diff_offsets(self.old_script, self.new_script)
        }
        header_offsets = {
            migration.EXPECTED_HEADER_PAYLOAD_OFFSET + offset
            for offset in migration._diff_offsets(self.old_header, resident_header)
        }
        runtime_offsets: set[int] = set()
        for offset, old, new, _label in migration.RUNTIME_PATCHES:
            runtime_offsets.update(
                self.ram_offset + offset + relative
                for relative, (before, after) in enumerate(zip(old, new, strict=True))
                if before != after
            )
        groups = (table_offsets, script_offsets, header_offsets, runtime_offsets)
        for index, group in enumerate(groups):
            for other in groups[index + 1 :]:
                self.assertTrue(group.isdisjoint(other))
        expected = set().union(*groups)
        actual = set(migration._diff_offsets(self.source_payload, self.result_payload))
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        self.assertEqual(len(table_offsets), 4)
        self.assertEqual(len(script_offsets), 84)
        self.assertEqual(len(header_offsets), 1)
        self.assertEqual(len(runtime_offsets), 23)

    def test_resident_header_is_allocator_safe_and_media_header_is_normal_v232(self) -> None:
        start = migration.EXPECTED_HEADER_PAYLOAD_OFFSET
        resident = self.result_payload[start : start + migration.HEADER_SIZE]
        self.assertEqual(_sha256(resident), migration.RESIDENT_HEADER_SHA256)
        self.assertEqual(
            migration._diff_triplets(self.old_header, resident),
            migration.RESIDENT_HEADER_DIFFS,
        )
        for offset, old, new in migration.HEADER_DIFFS[:-1]:
            with self.subTest(packed_stream_offset=hex(offset)):
                self.assertEqual(resident[offset], old)
                self.assertEqual(self.new_header[offset], new)
        offset, _old, new = migration.HEADER_DIFFS[-1]
        self.assertEqual(resident[offset], new)
        self.assertEqual(resident[offset], self.new_header[offset])
        self.assertEqual(_sha256(self.new_header), migration.NEW_HEADER_SHA256)
        self.assertTrue(self.report["resident_v231_packed_stream_offsets_preserved"])
        self.assertTrue(self.report["cold_reload_uses_normal_v232"])

    def test_resident_atel_has_three_facing_gated_shared_action_carriers(self) -> None:
        start = migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET
        resident = self.result_payload[start : start + migration.SCRIPT_SIZE]
        self.assertEqual(resident, self.new_script)
        editor = AtelScript(resident)
        self.assertEqual(
            tuple(
                editor.get_script_pointer(entity, 0)
                for entity in migration.TERMINAL_ENTITIES
            ),
            migration.TERMINAL_INIT_PCS,
        )
        self.assertEqual(
            tuple(
                editor.get_script_pointer(entity, 2)
                for entity in migration.TERMINAL_ENTITIES
            ),
            (migration.TERMINAL_ACTION_PC,) * 3,
        )
        self.assertEqual(
            tuple(
                editor.bytecode[pc : pc + len(body)]
                for pc, body in zip(
                    migration.TERMINAL_INIT_PCS,
                    migration.TERMINAL_INIT_BODIES,
                    strict=True,
                )
            ),
            migration.TERMINAL_INIT_BODIES,
        )
        for body, position in zip(
            migration.TERMINAL_INIT_BODIES,
            migration.TERMINAL_POSITIONS,
            strict=True,
        ):
            with self.subTest(position=position):
                self.assertEqual(struct.unpack_from("<hh", body, 4), position)
                self.assertEqual(body[15:19], bytes.fromhex("F8 03 04 00"))
                self.assertEqual(body[20:24], bytes.fromhex("01 0F 64 01"))
        action = editor.bytecode[
            migration.TERMINAL_ACTION_PC :
            migration.TERMINAL_ACTION_PC + migration.TERMINAL_ACTION_SIZE
        ]
        self.assertEqual(_sha256(action), migration.TERMINAL_ACTION_SHA256)

    def test_loaded_e19_is_moved_and_auxiliary_initializers_are_queued(self) -> None:
        primary_record = self.actor_array + 19 * FIELD_ACTOR_STRIDE
        primary_data = self._actor_data(self.result_ram, 19)
        self.assertEqual(
            self.result_ram[primary_record + 0x28 : primary_record + 0x2C],
            bytes.fromhex("59 FF FF FF"),
        )
        self.assertEqual(
            self.result_ram[primary_record + 0x48 : primary_record + 0x4C],
            bytes.fromhex("59 FF FF FF"),
        )
        self.assertEqual(
            self.result_ram[
                primary_data + migration.ACTOR_DATA_FLAGS_OFFSET :
                primary_data + migration.ACTOR_DATA_FLAGS_OFFSET + 4
            ],
            bytes.fromhex("00 00 04 00"),
        )
        self.assertEqual(
            self.result_ram[
                primary_data + migration.ACTOR_DATA_SURFACES_OFFSET :
                primary_data + migration.ACTOR_DATA_SURFACES_OFFSET + 8
            ],
            bytes.fromhex("1F 00 00 00 00 00 00 00"),
        )
        self.assertEqual(
            self.result_ram[
                primary_data + migration.ACTOR_DATA_BOUNDS_OFFSET :
                primary_data + migration.ACTOR_DATA_BOUNDS_OFFSET + 8
            ],
            bytes.fromhex("02 00 C8 00 1E 00 02 00"),
        )
        self.assertEqual(
            self.result_ram[
                primary_data + migration.ACTOR_DATA_POSITION_OFFSET :
                primary_data + migration.ACTOR_DATA_POSITION_OFFSET + 12
            ],
            bytes.fromhex("00 00 50 00 00 00 00 00 00 00 59 FF"),
        )
        self.assertEqual(
            self.result_ram[
                primary_data + migration.ACTOR_CURRENT_PC_OFFSET :
                primary_data + migration.ACTOR_CURRENT_PC_OFFSET + 4
            ],
            bytes.fromhex("8C 06 00 00"),
        )

        for entity, slot0, init_pc in zip(
            (4, 5),
            migration.NEW_AUX_SLOT0,
            migration.TERMINAL_INIT_PCS[1:],
            strict=True,
        ):
            record = self.actor_array + entity * FIELD_ACTOR_STRIDE
            actor_data = self._actor_data(self.result_ram, entity)
            with self.subTest(entity=entity):
                self.assertEqual(
                    self.result_ram[
                        record + migration.ACTOR_RECORD_STATUS_OFFSET :
                        record + migration.ACTOR_RECORD_STATUS_OFFSET + 2
                    ],
                    migration.NEW_AUX_RECORD_STATUS,
                )
                self.assertEqual(
                    self.result_ram[
                        actor_data + migration.ACTOR_DATA_FLAGS_OFFSET :
                        actor_data + migration.ACTOR_DATA_FLAGS_OFFSET + 4
                    ],
                    migration.NEW_AUX_FLAGS,
                )
                self.assertEqual(
                    self.result_ram[
                        actor_data + migration.ACTOR_SCRIPT_SLOT_OFFSET :
                        actor_data + migration.ACTOR_SCRIPT_SLOT_OFFSET + 8
                    ],
                    slot0,
                )
                self.assertEqual(struct.unpack_from("<H", slot0)[0], init_pc)
                self.assertEqual(
                    self.result_ram[
                        actor_data + migration.ACTOR_CURRENT_PC_OFFSET :
                        actor_data + migration.ACTOR_CURRENT_PC_OFFSET + 4
                    ],
                    bytes.fromhex("8C 06 00 00"),
                )

        for x, z in migration.TERMINAL_POSITIONS:
            self.assertFalse(
                abs(migration.SAVED_FEI_XZ[0] - x)
                <= migration.TERMINAL_EFFECTIVE_HALF_REACH[0]
                and abs(migration.SAVED_FEI_XZ[1] - z)
                <= migration.TERMINAL_EFFECTIVE_HALF_REACH[1]
            )
        self.assertTrue(self.report["old_aisle_carrier_disabled"])
        self.assertTrue(self.report["saved_stance_is_outside_all_terminal_reach"])

    def test_gameplay_party_patient_doctor_and_keycard_state_are_preserved(self) -> None:
        self.assertEqual(
            self.result_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
            self.source_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
        )
        self.assertEqual(
            self.result_ram[
                FIELD_SCRIPT_MEMORY :
                FIELD_SCRIPT_MEMORY + migration.FIELD_VARIABLE_BANK_SIZE
            ],
            self.source_ram[
                FIELD_SCRIPT_MEMORY :
                FIELD_SCRIPT_MEMORY + migration.FIELD_VARIABLE_BANK_SIZE
            ],
        )
        backup = GAME_STATE + migration.FIELD_VARIABLE_BACKUP_OFFSET
        self.assertEqual(
            self.result_ram[backup : backup + migration.FIELD_VARIABLE_BANK_SIZE],
            self.source_ram[backup : backup + migration.FIELD_VARIABLE_BANK_SIZE],
        )
        for address in CAMERA_VECTORS.values():
            self.assertEqual(
                self.result_ram[address : address + 16],
                self.source_ram[address : address + 16],
            )

        for entity in range(migration.SCRIPT_ENTITY_COUNT):
            if entity in migration.TERMINAL_ENTITIES:
                continue
            record = self.actor_array + entity * FIELD_ACTOR_STRIDE
            source_actor_data = self._actor_data(self.source_ram, entity)
            result_actor_data = self._actor_data(self.result_ram, entity)
            with self.subTest(unrelated_entity=entity):
                self.assertEqual(result_actor_data, source_actor_data)
                self.assertEqual(
                    self.result_ram[record : record + FIELD_ACTOR_STRIDE],
                    self.source_ram[record : record + FIELD_ACTOR_STRIDE],
                )
                self.assertEqual(
                    self.result_ram[
                        result_actor_data :
                        result_actor_data + migration.ACTOR_DATA_SIZE
                    ],
                    self.source_ram[
                        source_actor_data :
                        source_actor_data + migration.ACTOR_DATA_SIZE
                    ],
                )
        self.assertTrue(
            self.report["fei_party_gamestate_field_variables_camera_preserved"]
        )
        self.assertTrue(self.report["patient_doctor_state_preserved"])
        self.assertTrue(self.report["security_and_quarantine_keycard_state_preserved"])

        dialogue = slice(
            migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET,
            migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET + migration.DIALOGUE_SIZE,
        )
        walkmesh = slice(
            migration.EXPECTED_WALKMESH_PAYLOAD_OFFSET,
            migration.EXPECTED_WALKMESH_PAYLOAD_OFFSET + migration.WALKMESH_SIZE,
        )
        self.assertEqual(self.result_payload[dialogue], self.source_payload[dialogue])
        self.assertEqual(self.result_payload[walkmesh], self.source_payload[walkmesh])

    def test_corruption_and_live_output_paths_fail_closed(self) -> None:
        common = {
            "old_disc": self.old_disc,
            "new_disc": self.new_disc,
            "old_manifest": self.old_manifest,
            "new_manifest": self.new_manifest,
            "old_script": self.old_script,
            "new_script": self.new_script,
            "old_header": self.old_header,
            "new_header": self.new_header,
            "old_dialogue": self.old_dialogue,
            "new_dialogue": self.new_dialogue,
            "zstd": self.zstd,
        }
        damaged_state = bytearray(self.source_state)
        damaged_state[-1] ^= 1
        with self.assertRaises(migration.SurfaceSlotMigrationError):
            migration.migrate_v231_slot1_to_v232(bytes(damaged_state), **common)

        damaged_script = bytearray(self.new_script)
        damaged_script[-1] ^= 1
        with self.assertRaises(migration.SurfaceSlotMigrationError):
            migration.migrate_v231_slot1_to_v232(
                self.source_state,
                **{**common, "new_script": bytes(damaged_script)},
            )

        damaged_header = bytearray(self.new_header)
        damaged_header[0x2CC] ^= 1
        with self.assertRaises(migration.SurfaceSlotMigrationError):
            migration.migrate_v231_slot1_to_v232(
                self.source_state,
                **{**common, "new_header": bytes(damaged_header)},
            )

        live_before = migration.LIVE_SLOT1.read_bytes()
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            status = migration.main(
                [
                    str(self.source_path),
                    "--output",
                    str(migration.LIVE_SLOT1),
                    "--report",
                    str(self.report_path),
                ]
            )
        self.assertEqual(status, 1)
        self.assertIn("may not be the live Slot 1", stderr.getvalue())
        self.assertEqual(migration.LIVE_SLOT1.read_bytes(), live_before)


if __name__ == "__main__":
    unittest.main()
