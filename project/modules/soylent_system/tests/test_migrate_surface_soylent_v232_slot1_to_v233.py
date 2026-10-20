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
import tools.migrate_surface_soylent_v232_slot1_to_v233 as migration
from tools.xgdeathblows import GAMESTATE_SIZE
from tools.xgdialog import parse_dialogue
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


class SurfaceSoylentV232Slot1ToV233Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_path = migration.SOURCE_FIXTURE
        cls.candidate_path = (
            PROJECT_ROOT
            / "work"
            / "save_candidates"
            / "SLUS-00669_1_v233_from_3f09a8ce_field567_empty_terminal_native_init.sav"
        )
        cls.report_path = cls.candidate_path.with_suffix(".json")
        cls.old_disc = PROJECT_ROOT / "output" / migration.OLD_CUE_NAME.replace(".cue", ".bin")
        cls.new_disc = PROJECT_ROOT / "output" / migration.NEW_CUE_NAME.replace(".cue", ".bin")
        cls.old_stage = PROJECT_ROOT / "work" / "surface_soylent_campaign_v232_stage"
        cls.new_stage = PROJECT_ROOT / "work" / "surface_soylent_campaign_v233_stage"
        cls.old_clone = cls.old_stage / "clones" / "field_567_disc1_donor"
        cls.new_clone = cls.new_stage / "clones" / "field_567_disc1_donor"
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

        cls.result, cls.report = migration.migrate_v232_slot1_to_v233(
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
        cls.source_payload, cls.source_frame, cls.source_prefix = migration._unpack_state(
            cls.source_state, cls.zstd
        )
        cls.result_payload, cls.result_frame, cls.result_prefix = migration._unpack_state(
            cls.result, cls.zstd
        )
        cls.ram_offset = _psx_ram_offset(cls.source_payload)
        cls.source_ram = cls.source_payload[
            cls.ram_offset : cls.ram_offset + RAM_SIZE
        ]
        cls.result_ram = cls.result_payload[
            cls.ram_offset : cls.ram_offset + RAM_SIZE
        ]
        cls.actor_array = migration._guest_ram_offset(
            migration.EXPECTED_ACTOR_ARRAY_GUEST_POINTER, "field actor array"
        )

    @classmethod
    def _actor_data(cls, ram: bytes, entity: int) -> int:
        record = cls.actor_array + entity * FIELD_ACTOR_STRIDE
        return migration._guest_ram_offset(
            struct.unpack_from("<I", ram, record + FIELD_ACTOR_DATA_POINTER)[0],
            f"e{entity} ActorData",
        )

    def test_candidate_report_and_round_trip_have_frozen_identities(self) -> None:
        self.assertEqual(
            (len(self.source_state), _sha256(self.source_state)),
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
        self.assertEqual(self.candidate_path.read_bytes(), self.result)
        self.assertEqual(self.report_path.read_bytes(), report_blob)
        self.assertEqual(json.loads(report_blob), self.report)
        self.assertTrue(self.report["allocator_safe"])
        self.assertTrue(self.report["round_trip_verified"])
        self.assertTrue(self.report["safe_to_mount_after_duckstation_is_fully_closed"])
        self.assertFalse(self.report["live_slot1_modified"])

    def test_prefix_and_payload_change_only_the_frozen_whitelist(self) -> None:
        old_name = migration.OLD_CUE_NAME.encode("ascii")
        new_name = migration.NEW_CUE_NAME.encode("ascii")
        self.assertEqual((self.source_state.count(old_name), self.source_state.count(new_name)), (1, 0))
        self.assertEqual((self.result.count(old_name), self.result.count(new_name)), (0, 1))
        prefix_diffs = migration._diff_triplets(self.source_prefix, self.result_prefix)
        self.assertEqual(len(prefix_diffs), migration.EXPECTED_PREFIX_BYTES_CHANGED)
        self.assertEqual(migration._triplet_digest(prefix_diffs), migration.PREFIX_DIFF_SHA256)

        old_table = media_migration._archive_table(self.old_disc)
        new_table = media_migration._archive_table(self.new_disc)
        table_start = migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        source_table = self.source_payload[table_start : table_start + migration.ARCHIVE_TABLE_SIZE]
        result_table = self.result_payload[table_start : table_start + migration.ARCHIVE_TABLE_SIZE]
        self.assertEqual(
            source_table,
            old_table[:-1] + bytes((migration.EXPECTED_VOLATILE_TABLE_VALUE,)),
        )
        self.assertEqual(
            result_table,
            new_table[:-1] + bytes((migration.EXPECTED_VOLATILE_TABLE_VALUE,)),
        )

        resident_script = migration._build_resident_script(self.old_script, self.new_script)
        resident_dialogue = migration._build_resident_dialogue(
            self.old_dialogue, self.new_dialogue, resident_script
        )
        table_offsets = {
            table_start + offset
            for offset in migration._diff_offsets(source_table, result_table)
        }
        script_offsets = {
            migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + offset
            for offset in migration._diff_offsets(self.old_script, resident_script)
        }
        dialogue_offsets = {
            migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET + offset
            for offset in migration._diff_offsets(self.old_dialogue, resident_dialogue)
        }
        runtime_offsets = {
            offset
            for offset, _old, _new in migration._runtime_diff_triplets(self.ram_offset)
        }
        groups = (table_offsets, script_offsets, dialogue_offsets, runtime_offsets)
        for index, group in enumerate(groups):
            for other in groups[index + 1 :]:
                self.assertTrue(group.isdisjoint(other))
        expected = set().union(*groups)
        actual_diffs = migration._diff_triplets(self.source_payload, self.result_payload)
        self.assertEqual({offset for offset, _old, _new in actual_diffs}, expected)
        self.assertEqual(len(actual_diffs), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        self.assertEqual(migration._triplet_digest(actual_diffs), migration.PAYLOAD_DIFF_SHA256)
        self.assertEqual(
            tuple(map(len, groups)),
            (
                migration.EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED,
                migration.EXPECTED_SCRIPT_BYTES_CHANGED,
                migration.EXPECTED_DIALOGUE_BYTES_CHANGED,
                migration.EXPECTED_RUNTIME_BYTES_CHANGED,
            ),
        )

    def test_fixed_size_resident_components_are_allocator_safe(self) -> None:
        script_start = migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET
        resident_script = self.result_payload[
            script_start : script_start + migration.RESIDENT_SCRIPT_SIZE
        ]
        self.assertEqual(len(resident_script), len(self.old_script))
        self.assertNotEqual(resident_script, self.new_script)
        editor = AtelScript(resident_script)
        self.assertEqual(editor.bytecode_size, migration.OLD_SCRIPT_BYTECODE_SIZE)
        self.assertEqual(
            tuple(editor.get_script_pointer(entity, 0) for entity in migration.TERMINAL_ENTITIES),
            migration.COMPAT_TERMINAL_INIT_PCS,
        )
        self.assertEqual(
            tuple(editor.get_script_pointer(entity, 2) for entity in migration.TERMINAL_ENTITIES),
            (migration.COMPAT_ACTION_PC,) * 3,
        )
        action = editor.bytecode[
            migration.COMPAT_ACTION_PC :
            migration.COMPAT_ACTION_PC + len(migration.COMPAT_ACTION)
        ]
        self.assertEqual(action, migration.COMPAT_ACTION)
        self.assertEqual(action.count(bytes.fromhex("F5 2D 00")), 1)
        self.assertEqual(action.count(bytes.fromhex("31 20 00")), 2)
        self.assertNotIn(b"\xFE\x69", action)

        old_editor = AtelScript(self.old_script)
        new_editor = AtelScript(self.new_script)
        expected_cavity = b"".join(
            new_editor.bytecode[pc : pc + migration.TERMINAL_INIT_BODY_SIZE]
            for pc in migration.NORMAL_TERMINAL_INIT_PCS
        )
        self.assertEqual(
            len(expected_cavity),
            migration.RETIRED_CAVITY_END_PC - migration.RETIRED_CAVITY_START_PC,
        )
        self.assertEqual(_sha256(expected_cavity), migration.COMPAT_INIT_CAVITY_SHA256)
        self.assertEqual(
            editor.bytecode[
                migration.RETIRED_CAVITY_START_PC : migration.RETIRED_CAVITY_END_PC
            ],
            expected_cavity,
        )

        # The two overwritten V232 spans are unreachable from every active
        # script root.  The apparent retail ID45 reference belongs to e16:s4,
        # while all 32 live e16 pointers resolve to the shared STOP.
        self.assertEqual(
            old_editor.bytecode[
                migration.RETIRED_ID45_REFERENCE_PC :
                migration.RETIRED_ID45_REFERENCE_PC
                + len(migration.RETIRED_ID45_REFERENCE)
            ],
            migration.RETIRED_ID45_REFERENCE,
        )
        self.assertEqual(old_editor.bytecode.count(migration.RETIRED_ID45_REFERENCE), 1)
        self.assertEqual(
            tuple(old_editor.get_script_pointer(16, slot) for slot in range(32)),
            (migration.SHARED_STOP_PC,) * 32,
        )
        self.assertFalse(
            migration._pointer_hits(
                old_editor,
                migration.RETIRED_CAVITY_START_PC,
                migration.RETIRED_CAVITY_END_PC,
            )
        )
        self.assertFalse(
            migration._pointer_hits(
                old_editor,
                migration.COMPAT_ACTION_PC,
                migration.RETIRED_ACTION_END_PC,
            )
        )
        old_reachable, old_edges = migration._reachable_active_instructions(old_editor)
        old_occupied = migration._instruction_byte_offsets(old_reachable)
        self.assertEqual(len(old_reachable), migration.SOURCE_REACHABLE_INSTRUCTION_COUNT)
        self.assertEqual(
            migration._reachable_instruction_digest(old_reachable),
            migration.SOURCE_REACHABLE_INSTRUCTION_SHA256,
        )
        self.assertEqual(len(old_edges), migration.SOURCE_REACHABLE_EDGE_COUNT)
        self.assertEqual(
            migration._reachable_edge_digest(old_edges),
            migration.SOURCE_REACHABLE_EDGE_SHA256,
        )
        self.assertTrue(
            old_occupied.isdisjoint(
                range(
                    migration.RETIRED_CAVITY_START_PC,
                    migration.RETIRED_CAVITY_END_PC,
                )
            )
        )
        self.assertTrue(
            old_occupied.isdisjoint(
                range(migration.COMPAT_ACTION_PC, migration.RETIRED_ACTION_END_PC)
            )
        )

        target_reachable, target_edges = migration._reachable_active_instructions(editor)
        target_occupied = migration._instruction_byte_offsets(target_reachable)
        self.assertEqual(len(target_reachable), migration.TARGET_REACHABLE_INSTRUCTION_COUNT)
        self.assertEqual(
            migration._reachable_instruction_digest(target_reachable),
            migration.TARGET_REACHABLE_INSTRUCTION_SHA256,
        )
        self.assertEqual(len(target_edges), migration.TARGET_REACHABLE_EDGE_COUNT)
        self.assertEqual(
            migration._reachable_edge_digest(target_edges),
            migration.TARGET_REACHABLE_EDGE_SHA256,
        )
        self.assertTrue(
            set(
                range(
                    migration.RETIRED_CAVITY_START_PC,
                    migration.RETIRED_CAVITY_END_PC,
                )
            ).issubset(target_occupied)
        )
        self.assertTrue(
            set(
                range(migration.COMPAT_ACTION_PC, migration.RETIRED_ACTION_END_PC)
            ).issubset(target_occupied)
        )
        self.assertNotIn(migration.RETIRED_ID45_REFERENCE, editor.bytecode)
        self.assertEqual(
            editor.bytecode.count(bytes((0xF5, migration.RELOCATION_DIALOGUE_ID, 0))),
            1,
        )

        dialogue_start = migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        resident_dialogue = self.result_payload[
            dialogue_start : dialogue_start + migration.RESIDENT_DIALOGUE_SIZE
        ]
        parsed = parse_dialogue(resident_dialogue)
        relocated = parsed.blocks[migration.RELOCATION_DIALOGUE_ID]
        target = parse_dialogue(self.new_dialogue).blocks[
            migration.NORMAL_TERMINAL_DIALOGUE_ID
        ]
        self.assertEqual(len(parsed.blocks), migration.OLD_DIALOGUE_COUNT)
        self.assertEqual((relocated.width, relocated.height), migration.TARGET_DIALOGUE_GRID)
        self.assertEqual(relocated.payload[: migration.TARGET_DIALOGUE_SIZE], target.payload)
        self.assertEqual(
            relocated.payload[migration.TARGET_DIALOGUE_SIZE :],
            b"\x00" * (migration.RELOCATION_CAPACITY - migration.TARGET_DIALOGUE_SIZE),
        )

        header_start = migration.EXPECTED_HEADER_PAYLOAD_OFFSET
        self.assertEqual(
            self.result_payload[header_start : header_start + migration.HEADER_SIZE],
            self.old_header,
        )
        self.assertNotEqual(self.old_header, self.new_header)
        self.assertTrue(self.report["resident_header_and_heap_layout_preserved"])
        self.assertTrue(self.report["cold_reload_uses_normal_v233"])

    def test_terminal_native_init_is_queued_and_everything_else_is_preserved(self) -> None:
        for entity, init_pc, sprite_pointer in zip(
            migration.TERMINAL_ENTITIES,
            migration.COMPAT_TERMINAL_INIT_PCS,
            migration.EXPECTED_TERMINAL_SPRITE_POINTERS,
            strict=True,
        ):
            record = self.actor_array + entity * FIELD_ACTOR_STRIDE
            source_actor_data = self._actor_data(self.source_ram, entity)
            result_actor_data = self._actor_data(self.result_ram, entity)
            with self.subTest(entity=entity):
                self.assertEqual(source_actor_data, result_actor_data)
                self.assertEqual(
                    struct.unpack_from("<I", self.source_ram, record + 4)[0],
                    sprite_pointer,
                )

                expected_record = bytearray(
                    self.source_ram[record : record + FIELD_ACTOR_STRIDE]
                )
                self.assertEqual(struct.unpack_from("<H", expected_record, 0x58)[0], 0x01E0)
                struct.pack_into("<H", expected_record, 0x58, 0x0260)
                self.assertEqual(
                    self.result_ram[record : record + FIELD_ACTOR_STRIDE],
                    expected_record,
                )

                expected_actor_data = bytearray(
                    self.source_ram[
                        source_actor_data : source_actor_data + migration.ACTOR_DATA_SIZE
                    ]
                )
                self.assertEqual(struct.unpack_from("<I", expected_actor_data, 0)[0], 0x00B0)
                self.assertEqual(struct.unpack_from("<I", expected_actor_data, 4)[0], 0x04000800)
                struct.pack_into("<I", expected_actor_data, 4, 0x00000800)
                expected_slot = struct.pack("<HBBI", init_pc, 0, 0, 0x001CFFFF)
                expected_actor_data[
                    migration.ACTOR_SCRIPT_SLOT_OFFSET :
                    migration.ACTOR_SCRIPT_SLOT_OFFSET + len(expected_slot)
                ] = expected_slot
                self.assertEqual(
                    self.result_ram[
                        result_actor_data : result_actor_data + migration.ACTOR_DATA_SIZE
                    ],
                    expected_actor_data,
                )
                self.assertEqual(
                    struct.unpack_from(
                        "<H",
                        self.result_ram,
                        result_actor_data + migration.ACTOR_CURRENT_PC_OFFSET,
                    )[0],
                    migration.SHARED_STOP_PC,
                )

                # No stale-sprite workaround is fabricated offline.  The
                # exact native initializer owns the reset, allocation,
                # callback, position, surface, and animation side effects.
                sprite = migration._guest_ram_offset(sprite_pointer, f"e{entity} sprite")
                self.assertEqual(
                    self.result_ram[sprite : sprite + 0x24C],
                    self.source_ram[sprite : sprite + 0x24C],
                )

        source_pcs = migration._runtime_pc_snapshot(self.source_ram, self.actor_array)
        result_pcs = migration._runtime_pc_snapshot(self.result_ram, self.actor_array)
        self.assertEqual(
            migration._runtime_pc_digest(source_pcs),
            migration.SOURCE_RUNTIME_PC_SHA256,
        )
        self.assertEqual(
            migration._runtime_pc_digest(result_pcs),
            migration.TARGET_RUNTIME_PC_SHA256,
        )
        self.assertFalse(
            migration._runtime_pc_hits(
                source_pcs,
                migration.RETIRED_CAVITY_START_PC,
                migration.RETIRED_CAVITY_END_PC,
            )
        )
        self.assertFalse(
            migration._runtime_pc_hits(
                source_pcs,
                migration.COMPAT_ACTION_PC,
                migration.RETIRED_ACTION_END_PC,
            )
        )
        self.assertEqual(
            migration._runtime_pc_hits(
                result_pcs,
                migration.RETIRED_CAVITY_START_PC,
                migration.RETIRED_CAVITY_END_PC,
            ),
            tuple(
                (entity, 0, pc)
                for entity, pc in zip(
                    migration.TERMINAL_ENTITIES,
                    migration.COMPAT_TERMINAL_INIT_PCS,
                    strict=True,
                )
            ),
        )
        self.assertFalse(
            migration._runtime_pc_hits(
                result_pcs,
                migration.COMPAT_ACTION_PC,
                migration.RETIRED_ACTION_END_PC,
            )
        )

        self.assertEqual(
            struct.unpack_from("<3i", self.result_ram, self._actor_data(self.result_ram, 1) + 0x20),
            migration.EXPECTED_FEI_POSITION,
        )
        self.assertEqual(
            struct.unpack_from("<H", self.result_ram, self._actor_data(self.result_ram, 1) + migration.ACTOR_FACING_OFFSET)[0] & 0xFFF,
            migration.EXPECTED_FEI_YAW,
        )
        self.assertEqual(
            self.result_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
            self.source_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
        )
        self.assertEqual(
            self.result_ram[FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + migration.FIELD_VARIABLE_BANK_SIZE],
            self.source_ram[FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + migration.FIELD_VARIABLE_BANK_SIZE],
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
            actor_data = self._actor_data(self.source_ram, entity)
            with self.subTest(unrelated_entity=entity):
                self.assertEqual(
                    self.result_ram[record : record + FIELD_ACTOR_STRIDE],
                    self.source_ram[record : record + FIELD_ACTOR_STRIDE],
                )
                self.assertEqual(
                    self.result_ram[actor_data : actor_data + migration.ACTOR_DATA_SIZE],
                    self.source_ram[actor_data : actor_data + migration.ACTOR_DATA_SIZE],
                )
        self.assertTrue(self.report["fei_party_gamestate_field_variables_camera_preserved"])
        self.assertTrue(self.report["dialog_windows_preserved_and_closed"])
        self.assertTrue(self.report["terminal_initializers_queued"])
        self.assertTrue(
            self.report[
                "native_sprite_allocator_and_initializer_side_effects_deferred_to_engine"
            ]
        )
        self.assertEqual(self.report["offline_sprite_actor_bytes_changed"], 0)
        self.assertTrue(self.report["native_allocator_pointer_reuse_statically_proven"])
        self.assertTrue(self.report["native_allocator_no_net_growth_statically_proven"])
        self.assertTrue(
            self.report["native_sprite_callback_list_effect_statically_proven"]
        )
        self.assertTrue(self.report["native_walkmesh_fallback_xz_retention_requires_smoke"])
        self.assertEqual(self.report["native_walkmesh_fallback_triangle"], 0)
        self.assertEqual(
            self.report["native_walkmesh_fallback_material_flag"], "0x00400000"
        )
        self.assertTrue(self.report["runtime_acceptance_pending_manual_smoke_test"])

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
            migration.migrate_v232_slot1_to_v233(bytes(damaged_state), **common)

        damaged_script = bytearray(self.new_script)
        damaged_script[-1] ^= 1
        with self.assertRaises(migration.SurfaceSlotMigrationError):
            migration.migrate_v232_slot1_to_v233(
                self.source_state,
                **{**common, "new_script": bytes(damaged_script)},
            )

        live_before = migration.LIVE_SLOT1.read_bytes()
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            status = migration.main(
                [
                    str(self.source_path),
                    "--output", str(migration.LIVE_SLOT1),
                    "--report", str(self.report_path),
                ]
            )
        self.assertEqual(status, 1)
        self.assertIn("may not be the live Slot 1", stderr.getvalue())
        self.assertEqual(migration.LIVE_SLOT1.read_bytes(), live_before)


if __name__ == "__main__":
    unittest.main()
