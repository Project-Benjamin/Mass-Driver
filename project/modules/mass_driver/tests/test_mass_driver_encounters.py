from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import unittest

from modules.mass_driver import encounters
from shared.tools.atel_primitives import immediate
from shared.tools.xgdisc import Mode2Image
from shared.tools.xgencounter import EncounterTable, FORMATION_SIZE
from shared.tools.xgscript import AtelScript


ROOT = Path(__file__).resolve().parents[3]
NATIVE_TABLE = ROOT / "work/audit_zeboim_cd1/field_372/06_encounters.bin"
CLEAN_DISC = ROOT / "Xenogears (Disc 2).bin"


def synthetic_table() -> bytes:
    """Valid table with weighted Gear placeholders and a fixed-boss sentinel."""
    result = bytearray(528)
    for index in range(16):
        result[index * 32:index * 32 + 32] = bytes.fromhex(
            "10 80 0B 00 00 00 00 00 80 FF FF FF FF FF FF FF "
            "00 FF FF FF FF FF FF FF 00 FF FF FF FF FF FF FF"
        )
        result[512 + index] = 9
    for index, formation in enumerate(encounters.CURATED_FORMATIONS):
        result[index * 32:index * 32 + 32] = formation
    return EncounterTable(result).to_bytes()


def synthetic_script(pc: int, initializer: bytes) -> bytes:
    result = bytearray(0x84 + 0x40 + pc + 8)
    struct.pack_into("<I", result, 0x80, 1)
    result[0xC4:] = b"\x14" * (pc + 8)
    result[0xC4 + pc:0xC4 + pc + 5] = initializer
    result[-1] = 0
    return AtelScript(result).to_bytes()


class MassDriverEncountersTests(unittest.TestCase):
    def test_selected_passages_and_quiet_rooms_are_explicit(self) -> None:
        self.assertEqual(len(encounters.MASS_DRIVER_FIELD_IDS), 33)
        self.assertEqual(encounters.COMBAT_FIELD_IDS, {727, 372, 723, 375, 387, 726})
        self.assertTrue({721, 725, 361, 722, 376, 384, 728, 377, 378, 379, 382, 383}.issubset(encounters.SAFE_FIELD_IDS))
        self.assertEqual(encounters.SAFE_FIELD_IDS | encounters.COMBAT_FIELD_IDS, encounters.MASS_DRIVER_FIELD_IDS)

    def test_all_33_tables_have_only_intended_random_rows(self) -> None:
        original = synthetic_table()
        for field_id in encounters.MASS_DRIVER_FIELD_IDS:
            with self.subTest(field=field_id):
                result = encounters.curate_encounter_table(original, field_id)
                table = EncounterTable(result)
                enabled = [i for i, weight in enumerate(table.weights) if weight]
                self.assertEqual(enabled, [0, 1, 2] if field_id in encounters.COMBAT_FIELD_IDS else [])
                self.assertEqual(result[:512], original[:512])
                self.assertEqual(table.formation(15), EncounterTable(original).formation(15))
                self.assertEqual(table.get_weight(15), 0)
                self.assertEqual(encounters.curate_encounter_table(result, field_id), result)
                encounters.verify_encounter_table(result, field_id, original)

    def test_native_rows_keep_on_foot_scale_resources_layouts_and_escape(self) -> None:
        table = EncounterTable(encounters.curate_encounter_table(synthetic_table(), 727))
        expected_enemies = [(0, 0), (1, 1, 1, 1), (0, 1, 1, 1)]
        for index, expected in enumerate(expected_enemies):
            formation = table.formation(index)
            self.assertEqual(struct.unpack_from("<HH", formation), (0x4006, 0x17))
            self.assertFalse(formation[1] & 0x80)
            enemies = [table.get_enemy(index, i) for i in range(8)]
            self.assertEqual(tuple(e.enemy_id for e in enemies if e.enemy_id != 0x7F), expected)
            self.assertTrue(all(not e.is_gear for e in enemies if e.enemy_id != 0x7F))

    def test_real_zeboim_donor_matches_all_three_rows(self) -> None:
        if not NATIVE_TABLE.is_file():
            self.skipTest("Native field-372 extracted donor not installed")
        native = EncounterTable(NATIVE_TABLE.read_bytes())
        self.assertEqual(tuple(native.formation(i) for i in range(3)), encounters.CURATED_FORMATIONS)

    def test_unsafe_random_guardian_or_mixed_scale_is_rejected(self) -> None:
        valid = encounters.curate_encounter_table(synthetic_table(), 727)
        unsafe_weight = bytearray(valid)
        unsafe_weight[512 + 8] = 1
        unsafe_gear = bytearray(valid)
        unsafe_gear[8] |= 0x80
        unsafe_resource = bytearray(valid)
        unsafe_resource[0] = 0x10
        for unsafe in (unsafe_weight, unsafe_gear, unsafe_resource):
            with self.subTest(unsafe=unsafe[:10].hex()), self.assertRaises(encounters.MassDriverEncounterError):
                encounters.verify_encounter_table(unsafe, 727)

    def test_quiet_room_rejects_even_one_weighted_formation(self) -> None:
        valid = bytearray(encounters.curate_encounter_table(synthetic_table(), 384))
        valid[512 + 8] = 1
        with self.assertRaises(encounters.MassDriverEncounterError):
            encounters.verify_encounter_table(valid, 384)

    def test_preservation_verifier_detects_unrelated_fixed_row_change(self) -> None:
        original = synthetic_table()
        result = bytearray(encounters.curate_encounter_table(original, 727))
        result[15 * FORMATION_SIZE + 2] ^= 1
        with self.assertRaises(encounters.MassDriverEncounterError):
            encounters.verify_encounter_table(result, 727, original)

    def test_wrong_donor_is_rejected_before_enabling_random_battles(self) -> None:
        source = bytearray(synthetic_table())
        source[0] = 0x10
        with self.assertRaises(encounters.MassDriverEncounterError):
            encounters.curate_encounter_table(source, 727)

    def test_initializer_encodes_movement_timer_and_nonzero_timer_count(self) -> None:
        self.assertEqual(encounters.ACTIVE_INITIALIZER, b"\xF7" + immediate(900) + immediate(1))
        for field_id, pc in encounters.CORRIDOR_INITIALIZER_PCS.items():
            with self.subTest(field=field_id):
                original = synthetic_script(pc, encounters.NATIVE_DISABLED_INITIALIZER)
                result = encounters.configure_encounter_initializer(original, field_id, pc)
                editor = AtelScript(original)
                start = editor.bytecode_offset + pc
                self.assertEqual(len(result), len(original))
                self.assertEqual(result[:start], original[:start])
                self.assertEqual(result[start + 5:], original[start + 5:])
                self.assertEqual(result[start:start + 5], encounters.ACTIVE_INITIALIZER)
                self.assertEqual(struct.unpack_from("<HH", result, start + 1), (0x8384, 0x8001))
                self.assertEqual(encounters.configure_encounter_initializer(result, field_id, pc), result)

    def test_quiet_initializer_disables_random_battles_same_size(self) -> None:
        pc = 0x11
        original = synthetic_script(pc, encounters.NATIVE_DISABLED_INITIALIZER)
        result = encounters.configure_encounter_initializer(original, 361, pc)
        self.assertEqual(AtelScript(result).bytecode[pc:pc + 5], b"\x14" * 5)
        self.assertEqual(len(result), len(original))

    def test_initializer_refuses_wrong_pc_bytes_or_unknown_field(self) -> None:
        pc = encounters.CORRIDOR_INITIALIZER_PCS[727]
        source = synthetic_script(pc, encounters.NATIVE_DISABLED_INITIALIZER)
        with self.assertRaises(encounters.MassDriverEncounterError):
            encounters.configure_encounter_initializer(source, 727, pc + 1)
        with self.assertRaises(encounters.MassDriverEncounterError):
            encounters.configure_encounter_initializer(synthetic_script(pc, b"\x00" * 5), 727, pc)
        with self.assertRaises(encounters.MassDriverEncounterError):
            encounters.curate_encounter_table(synthetic_table(), 999)

    def test_native_resource_pair_exists_on_clean_disc_and_rejects_drift(self) -> None:
        if not CLEAN_DISC.is_file():
            self.skipTest("Clean US Disc 2 not installed")
        image = Mode2Image(CLEAN_DISC)
        entries = image.read_index()
        stats = image.extract_entry(entries[encounters.ENEMY_STATS_CANONICAL_ID - 5])
        models = image.extract_entry(entries[encounters.ENEMY_MODELS_CANONICAL_ID - 5])
        proof = encounters.validate_enemy_resource_pair(stats, models)
        self.assertEqual(proof["enemy_names"], ["Shellbelle", "Hammerhead"])
        self.assertEqual(proof["enemy_hp"], [680, 180])
        self.assertFalse(proof["enemy_resources_modified"])
        self.assertEqual(hashlib.sha256(stats).hexdigest(), encounters.ENEMY_STATS_SHA256)
        changed = bytearray(models)
        changed[-1] ^= 1
        with self.assertRaises(encounters.MassDriverEncounterError):
            encounters.validate_enemy_resource_pair(stats, changed)
        with self.assertRaises(encounters.MassDriverEncounterError):
            encounters.validate_enemy_resource_pair(stats[:-1], models)


if __name__ == "__main__":
    unittest.main()
