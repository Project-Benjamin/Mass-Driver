from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

from contextlib import redirect_stderr
import hashlib
import io
from pathlib import Path
import struct
import unittest

import tools.migrate_duckstation_disc_state as media_migration
import tools.migrate_surface_soylent_v214_slot1_to_v215 as migration
from tools.xgdialog import parse_dialogue
from tools.xgscript import AtelScript
from work.read_duckstation_runtime import (
    CAMERA_VECTORS,
    FIELD_ACTORS,
    FIELD_ACTOR_DATA_POINTER,
    FIELD_ACTOR_STRIDE,
    GAME_STATE,
)
from tools.xgdeathblows import GAMESTATE_SIZE


PROJECT_ROOT = REPOSITORY_ROOT
SOURCE_STATE = PROJECT_ROOT / "work" / "save_backups" / "SLUS-00669_1_v214_field621_door_dcd01f7a.sav"
OLD_DISC = PROJECT_ROOT / "output" / "Xenogears_PW_CD2_mass_driver_surface_soylent_v214.bin"
NEW_DISC = PROJECT_ROOT / "output" / "Xenogears_PW_CD2_mass_driver_surface_soylent_v215.bin"
OLD_FIELD = PROJECT_ROOT / "work" / "surface_soylent_campaign_v214_stage" / "clones" / "field_593_disc1_donor"
NEW_FIELD = PROJECT_ROOT / "work" / "surface_soylent_campaign_v215_stage" / "clones" / "field_593_disc1_donor"
ZSTD = PROJECT_ROOT / "work" / "duckstation" / "zstd.dll"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SurfaceSoylentV214Slot1MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (
            SOURCE_STATE,
            OLD_DISC,
            NEW_DISC,
            OLD_DISC.with_suffix(".cue"),
            NEW_DISC.with_suffix(".cue"),
            OLD_FIELD / "05_scripts.bin",
            NEW_FIELD / "05_scripts.bin",
            OLD_FIELD / "07_dialogue.bin",
            NEW_FIELD / "07_dialogue.bin",
            ZSTD,
        )
        if not all(path.is_file() for path in required):
            raise unittest.SkipTest("Pinned V214/V215 migration fixtures unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        cls.old_script = (OLD_FIELD / "05_scripts.bin").read_bytes()
        cls.new_script = (NEW_FIELD / "05_scripts.bin").read_bytes()
        cls.old_dialogue = (OLD_FIELD / "07_dialogue.bin").read_bytes()
        cls.new_dialogue = (NEW_FIELD / "07_dialogue.bin").read_bytes()
        cls.resident_script = migration._build_resident_script(cls.old_script)
        cls.resident_dialogue = migration._build_resident_dialogue(cls.old_dialogue, cls.new_dialogue)
        cls.zstd = media_migration._Zstd(ZSTD)
        cls.result, cls.report = migration.migrate_v214_slot1_to_v215(
            cls.source,
            old_disc=OLD_DISC,
            new_disc=NEW_DISC,
            old_script=cls.old_script,
            new_script=cls.new_script,
            old_dialogue=cls.old_dialogue,
            new_dialogue=cls.new_dialogue,
            zstd=cls.zstd,
        )
        cls.source_payload, cls.frame_start, cls.source_prefix = migration._unpack_state(cls.source, cls.zstd)
        cls.result_payload, cls.result_frame_start, cls.result_prefix = migration._unpack_state(cls.result, cls.zstd)

    def test_candidate_identity_and_round_trip_are_frozen(self) -> None:
        self.assertEqual((len(self.result), _sha256(self.result)), (migration.EXPECTED_OUTPUT_SIZE, migration.EXPECTED_OUTPUT_SHA256))
        self.assertEqual(_sha256(self.result_payload), migration.EXPECTED_OUTPUT_PAYLOAD_SHA256)
        self.assertEqual(self.frame_start, migration.EXPECTED_FRAME_START)
        self.assertEqual(self.result_frame_start, self.frame_start)
        self.assertEqual(
            self.result_prefix,
            migration._expected_prefix(self.source_prefix, compressed_size=len(self.result) - self.frame_start),
        )
        self.assertEqual(self.result.count(migration.OLD_CUE_NAME.encode()), 0)
        self.assertEqual(self.result.count(migration.NEW_CUE_NAME.encode()), 1)
        self.assertTrue(self.report["round_trip_verified"])
        self.assertTrue(self.report["allocator_safe"])

    def test_full_v215_growth_cannot_overwrite_the_live_allocator(self) -> None:
        self.assertEqual(len(self.old_script), migration.OLD_SCRIPT_SIZE)
        self.assertEqual(len(self.new_script), migration.NEW_SCRIPT_SIZE)
        self.assertGreater(len(self.new_script), migration.SCRIPT_ALLOCATED_CAPACITY)
        self.assertEqual(len(self.resident_script), len(self.old_script))
        self.assertLessEqual(len(self.resident_script), migration.SCRIPT_ALLOCATED_CAPACITY)
        script = migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET
        dialogue = migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        # The apparent gap includes a live 8-byte header and 16-byte trigger-zone
        # allocation.  The complete span must remain byte-identical.
        self.assertEqual(
            self.source_payload[script + len(self.old_script) : dialogue],
            self.result_payload[script + len(self.resident_script) : dialogue],
        )
        self.assertEqual(
            _sha256(self.result_payload[script + len(self.resident_script) : dialogue]),
            migration.SCRIPT_GAP_SHA256,
        )
        ram_offset = migration.EXPECTED_RAM_PAYLOAD_OFFSET
        self.assertEqual(
            self.result_payload[ram_offset + 0x10C044 : ram_offset + 0x10C064],
            self.source_payload[ram_offset + 0x10C044 : ram_offset + 0x10C064],
        )
        self.assertEqual(
            struct.unpack_from("<I", self.result_payload, ram_offset + migration.FIELD_SMALL_COMPONENT)[0],
            migration.EXPECTED_SMALL_COMPONENT_POINTER,
        )

    def test_compact_script_uses_only_retired_e14_and_preserves_all_live_pcs(self) -> None:
        old = AtelScript(self.old_script)
        resident = AtelScript(self.resident_script)
        new = AtelScript(self.new_script)
        self.assertEqual((len(self.resident_script), _sha256(self.resident_script)), (migration.RESIDENT_SCRIPT_SIZE, migration.RESIDENT_SCRIPT_SHA256))
        self.assertEqual(old.entity_count, resident.entity_count)
        self.assertEqual(old.bytecode_size, resident.bytecode_size)
        self.assertEqual(
            [old.get_script_pointer(entity, slot) for entity in range(old.entity_count) for slot in range(32)],
            [resident.get_script_pointer(entity, slot) for entity in range(resident.entity_count) for slot in range(32)],
        )
        self.assertEqual(
            [resident.get_script_pointer(migration.RETIRED_ENTITY, slot) for slot in range(32)],
            [migration.RETIRED_ENTITY_STOP_PC] * 32,
        )
        self.assertEqual(
            resident.bytecode[migration.ACTION_JUMP_PC : migration.ACTION_JUMP_PC + 3],
            migration.ACTION_JUMP_NEW,
        )
        self.assertEqual(
            resident.bytecode[migration.RETIRED_CAVITY_PC : migration.RETIRED_CAVITY_PC + len(migration.RETIRED_CAVITY_BODY)],
            migration.RETIRED_CAVITY_BODY,
        )
        self.assertEqual(resident.bytecode[migration.TERMINAL_ACTIVE_PC], 0x9C)
        self.assertEqual(new.bytecode[migration.TERMINAL_ACTIVE_PC], 0x9C)
        self.assertEqual(resident.get_script_pointer(migration.SCHEDULER_ENTITY, 1), migration.SHARED_STOP_PC)
        self.assertEqual(self.report["scheduler_e20_pc_preserved"], "0x0728")
        self.assertEqual(len(migration._diff_offsets(self.old_script, self.resident_script)), migration.EXPECTED_SCRIPT_BYTES_CHANGED)

    def test_compact_cavity_has_exact_leave_and_accept_semantics(self) -> None:
        bytecode = AtelScript(self.resident_script).bytecode
        start = migration.RETIRED_CAVITY_PC
        body = bytecode[start : start + len(migration.RETIRED_CAVITY_BODY)]
        # Open choice ID52, configure lines 1..2, then WAIT_DIALOG.
        self.assertEqual(body[0:7], bytes.fromhex("D2 34 00 00 A9 12 9C"))
        # Any line except Accept (absolute line 1) branches directly to the
        # terminal finish, before the release loop, sound, receipt, or write.
        self.assertEqual(body[7:15], bytes.fromhex("02 14 00 01 00 40 25 07"))
        self.assertEqual(struct.unpack_from("<H", body, 13)[0], migration.TERMINAL_FINISH_PC)
        # Accept drains the Cross edge, yields once, plays item SFX 0x37,
        # displays receipt ID54, sets operand021A bit8, and exits at 0x0725.
        self.assertEqual(body[15:26], bytes.fromhex("31 20 00 FD 03 26 01 80 01 F2 03"))
        self.assertEqual(body[26:29], bytes.fromhex("26 01 80"))
        self.assertEqual(body[29:32], bytes.fromhex("74 37 80"))
        self.assertEqual(body[32:37], bytes.fromhex("F5 36 00 01 9C"))
        self.assertEqual(body[37:43], bytes.fromhex("3A 1A 02 08 00 40"))
        self.assertEqual(body[43:46], bytes.fromhex("01 25 07"))

    def test_dialogue_choice_reuses_id52_without_moving_active_id53(self) -> None:
        old = parse_dialogue(self.old_dialogue)
        resident = parse_dialogue(self.resident_dialogue)
        new = parse_dialogue(self.new_dialogue)
        self.assertEqual((len(resident.blocks), len(resident.source)), (56, migration.OLD_DIALOGUE_SIZE))
        self.assertEqual((len(self.resident_dialogue), _sha256(self.resident_dialogue)), (migration.RESIDENT_DIALOGUE_SIZE, migration.RESIDENT_DIALOGUE_SHA256))
        self.assertEqual((resident.blocks[52].offset, resident.blocks[52].width, resident.blocks[52].height), (old.blocks[52].offset, 58, 4))
        self.assertTrue(resident.blocks[52].text.startswith(new.blocks[56].text))
        self.assertEqual(resident.blocks[53].offset, old.blocks[53].offset)
        self.assertTrue(resident.blocks[53].text.startswith(new.blocks[53].text))
        self.assertEqual(resident.blocks[54], old.blocks[54])
        self.assertEqual(resident.blocks[55].offset, old.blocks[55].offset)
        self.assertTrue(resident.blocks[55].text.startswith(new.blocks[55].text))
        self.assertEqual(self.resident_dialogue[0x14B1], 0)
        self.assertEqual(len(migration._diff_offsets(self.old_dialogue, self.resident_dialogue)), migration.EXPECTED_DIALOGUE_BYTES_CHANGED)

    def test_resident_terminal_dialogues_use_the_retail_58_by_4_grid(self) -> None:
        resident = parse_dialogue(self.resident_dialogue)
        for dialogue_id in (52, 53, 54, 55):
            block = resident.blocks[dialogue_id]
            self.assertEqual((block.width, block.height), (58, 4), f"dialogue {dialogue_id}")
            visible_text = block.text.split("<Close>", 1)[0]
            self.assertLessEqual(len(visible_text.split("\n")), 4, f"dialogue {dialogue_id}")
        self.assertEqual(
            resident.blocks[52].text.split("<Close>", 1)[0].split("\n"),
            [
                "<Opcode:01:FF>Take the Quarantine keycard?",
                "     Accept it",
                "     Leave it",
            ],
        )

    def test_only_two_table_49_script_and_270_dialogue_bytes_change(self) -> None:
        actual = migration._diff_offsets(self.source_payload, self.result_payload)
        expected = {
            *(migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + relative for relative, _old, _new in migration.ARCHIVE_TABLE_DIFFS),
            *(migration.EXPECTED_SCRIPT_PAYLOAD_OFFSET + offset for offset in migration._diff_offsets(self.old_script, self.resident_script)),
            *(migration.EXPECTED_DIALOGUE_PAYLOAD_OFFSET + offset for offset in migration._diff_offsets(self.old_dialogue, self.resident_dialogue)),
        }
        self.assertEqual(actual, tuple(sorted(expected)))
        self.assertEqual(len(actual), migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        self.assertEqual(self.report["payload_bytes_changed"], migration.EXPECTED_PAYLOAD_BYTES_CHANGED)
        self.assertEqual(self.report["archive_table_bytes_changed"], 2)
        self.assertEqual(self.report["resident_script_bytes_changed"], 49)
        self.assertEqual(self.report["resident_dialogue_bytes_changed"], 270)
        table = migration.EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        expected_table = media_migration._archive_table(NEW_DISC)[:-1] + bytes((migration.EXPECTED_VOLATILE_TABLE_VALUE,))
        self.assertEqual(self.result_payload[table : table + migration.ARCHIVE_TABLE_SIZE], expected_table)

    def test_active_window_e19_e20_gamestate_party_and_camera_are_identical(self) -> None:
        _, source_ram = migration._ram_from_payload(self.source_payload)
        _, result_ram = migration._ram_from_payload(self.result_payload)
        self.assertEqual(
            source_ram[migration.DIALOG_WINDOWS : migration.DIALOG_WINDOWS + migration.DIALOG_WINDOWS_SIZE],
            result_ram[migration.DIALOG_WINDOWS : migration.DIALOG_WINDOWS + migration.DIALOG_WINDOWS_SIZE],
        )
        self.assertEqual(
            struct.unpack_from("<I", result_ram, migration.ACTIVE_WINDOW_START_POINTER_OFFSET)[0],
            migration.EXPECTED_ACTIVE_WINDOW_START_POINTER,
        )
        self.assertEqual(
            struct.unpack_from("<I", result_ram, migration.ACTIVE_WINDOW_CURRENT_POINTER_OFFSET)[0],
            migration.EXPECTED_ACTIVE_WINDOW_CURRENT_POINTER,
        )
        for actor_data in (migration.EXPECTED_TERMINAL_ACTOR_DATA, migration.EXPECTED_SCHEDULER_ACTOR_DATA):
            self.assertEqual(source_ram[actor_data : actor_data + 0x138], result_ram[actor_data : actor_data + 0x138])
        self.assertEqual(
            result_ram[migration.EXPECTED_SCHEDULER_ACTOR_DATA + migration.ACTOR_SCRIPT_SLOT_OFFSET : migration.EXPECTED_SCHEDULER_ACTOR_DATA + migration.ACTOR_SCRIPT_SLOT_OFFSET + 8],
            migration.EXPECTED_SCHEDULER_SLOT0,
        )
        self.assertEqual(source_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE], result_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE])
        for address in CAMERA_VECTORS.values():
            self.assertEqual(source_ram[address : address + 16], result_ram[address : address + 16])
        actor_base = struct.unpack_from("<I", source_ram, FIELD_ACTORS)[0] & 0x1FFFFFFF
        for entity in range(3):
            record = actor_base + entity * FIELD_ACTOR_STRIDE
            actor_data = struct.unpack_from("<I", source_ram, record + FIELD_ACTOR_DATA_POINTER)[0] & 0x1FFFFFFF
            self.assertEqual(source_ram[record : record + FIELD_ACTOR_STRIDE], result_ram[record : record + FIELD_ACTOR_STRIDE])
            self.assertEqual(source_ram[actor_data : actor_data + 0x138], result_ram[actor_data : actor_data + 0x138])
        self.assertTrue(self.report["active_window_pointers_preserved"])
        self.assertTrue(self.report["gamestate_party_camera_preserved"])

    def test_wrong_source_or_resource_fails_closed(self) -> None:
        wrong_state = bytearray(self.source)
        wrong_state[0x100] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "Source Slot 1 identity"):
            migration.migrate_v214_slot1_to_v215(
                bytes(wrong_state), old_disc=OLD_DISC, new_disc=NEW_DISC,
                old_script=self.old_script, new_script=self.new_script,
                old_dialogue=self.old_dialogue, new_dialogue=self.new_dialogue,
                zstd=self.zstd,
            )
        wrong_script = bytearray(self.new_script)
        wrong_script[-1] ^= 1
        with self.assertRaisesRegex(migration.SurfaceSlotMigrationError, "V215 script identity"):
            migration.migrate_v214_slot1_to_v215(
                self.source, old_disc=OLD_DISC, new_disc=NEW_DISC,
                old_script=self.old_script, new_script=bytes(wrong_script),
                old_dialogue=self.old_dialogue, new_dialogue=self.new_dialogue,
                zstd=self.zstd,
            )

    def test_cli_refuses_to_overwrite_live_slot1(self) -> None:
        before = migration.LIVE_SLOT1.read_bytes()
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = migration.main(
                (
                    str(SOURCE_STATE), str(migration.LIVE_SLOT1),
                    "--old-disc", str(OLD_DISC), "--new-disc", str(NEW_DISC),
                    "--old-script", str(OLD_FIELD / "05_scripts.bin"),
                    "--new-script", str(NEW_FIELD / "05_scripts.bin"),
                    "--old-dialogue", str(OLD_FIELD / "07_dialogue.bin"),
                    "--new-dialogue", str(NEW_FIELD / "07_dialogue.bin"),
                    "--zstd", str(ZSTD),
                )
            )
        self.assertEqual(result, 1)
        self.assertIn("may not be the live Slot 1", stderr.getvalue())
        self.assertEqual(migration.LIVE_SLOT1.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
