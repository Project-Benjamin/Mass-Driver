from __future__ import annotations

import hashlib
from pathlib import Path
import unittest

from tools import xgbattle_weight as weight


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RETAIL_DECODED_OVERLAY = (
    PROJECT_ROOT / "work" / "_audit_gear_damage_battle_overlay" / "0038.dec"
)


def _record(fixed_part: int, mutable_part: int, tenths: int = 0) -> bytes:
    result = bytearray(weight.CHARACTER_RECORD_SIZE)
    result[weight.WEIGHT_FIXED_OFFSET] = fixed_part
    result[weight.WEIGHT_MUTABLE_OFFSET] = mutable_part
    result[weight.WEIGHT_TENTHS_OFFSET] = tenths
    return bytes(result)


class CharacterWeightFormulaTests(unittest.TestCase):
    # Initial-game records, in character-ID order.  Sword Citan and adult
    # Emeralda repeat their original character's body weight.
    INITIAL_WEIGHTS = (
        ("Fei", 26, 50, 16_720),
        ("Elly", 22, 20, 9_240),
        ("Citan", 22, 50, 15_840),
        ("Bart", 24, 50, 16_280),
        ("Billy", 24, 30, 11_880),
        ("Rico", 43, 80, 27_060),
        ("Emeralda", 21, 75, 21_120),
        ("Chu-Chu", 12, 10, 4_840),
        ("Maria", 18, 10, 6_160),
        ("Sword Citan", 22, 50, 15_840),
        ("Adult Emeralda", 21, 75, 21_120),
    )

    def test_retail_character_weight_conversion_to_pounds(self) -> None:
        for name, fixed, mutable, expected in self.INITIAL_WEIGHTS:
            with self.subTest(character=name):
                self.assertEqual(
                    weight.weight_hundredths_lb(_record(fixed, mutable)),
                    expected,
                )
        self.assertEqual(
            weight.weight_hundredths_lb(_record(26, 50, 7)),
            16_874,
        )
        self.assertEqual(
            weight.weight_hundredths_lb(_record(43, 200, 9)),
            53_658,
        )

    def test_invalid_character_weight_encoding_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "too short"):
            weight.weight_hundredths_lb(bytes(weight.WEIGHT_TENTHS_OFFSET))
        with self.assertRaisesRegex(ValueError, "tenths digit"):
            weight.weight_hundredths_lb(_record(26, 50, 10))

    def test_physical_attack_is_neutral_at_feis_initial_weight(self) -> None:
        self.assertEqual(weight.scale_physical_attack(0, 16_720), 0)
        self.assertEqual(weight.scale_physical_attack(1, 16_720), 1)
        self.assertEqual(weight.scale_physical_attack(100, 16_720), 100)
        self.assertEqual(weight.scale_physical_attack(37, 16_720), 37)
        self.assertEqual(weight.scale_physical_attack(255, 16_720), 255)
        # The direct hook keeps its widened register result; it never stores
        # this value back through the character record's u8 Attack byte.
        self.assertEqual(weight.scale_physical_attack(255, 53_658), 469)

    def test_starting_weight_physical_factors_are_monotonic(self) -> None:
        expected_at_attack_100 = {
            "Fei": 100,
            "Elly": 83,
            "Citan": 98,
            "Bart": 99,
            "Billy": 89,
            "Rico": 123,
            "Emeralda": 110,
            "Chu-Chu": 73,
            "Maria": 76,
            "Sword Citan": 98,
            "Adult Emeralda": 110,
        }
        ordered: list[tuple[int, int]] = []
        for name, _fixed, _mutable, weight_hundredths in self.INITIAL_WEIGHTS:
            actual = weight.scale_physical_attack(100, weight_hundredths)
            self.assertEqual(actual, expected_at_attack_100[name])
            ordered.append((weight_hundredths, actual))
        ordered.sort()
        self.assertEqual(
            [attack for _weight, attack in ordered],
            sorted(attack for _weight, attack in ordered),
        )

    def test_retail_four_point_four_lb_changes_affect_both_sides(self) -> None:
        self.assertEqual(weight.scale_physical_attack(100, 16_280), 99)
        self.assertEqual(weight.scale_physical_attack(100, 17_160), 101)
        self.assertEqual(weight.adjust_atb_ticks(80, 16_280), 79)
        self.assertEqual(weight.adjust_atb_ticks(80, 17_160), 81)

    def test_starting_weight_atb_deltas_are_monotonic(self) -> None:
        expected_at_base_80 = {
            "Fei": 80,
            "Elly": 63,
            "Citan": 78,
            "Bart": 79,
            "Billy": 69,
            "Rico": 103,
            "Emeralda": 90,
            "Chu-Chu": 53,
            "Maria": 56,
            "Sword Citan": 78,
            "Adult Emeralda": 90,
        }
        ordered: list[tuple[int, int]] = []
        for name, _fixed, _mutable, weight_hundredths in self.INITIAL_WEIGHTS:
            actual = weight.adjust_atb_ticks(80, weight_hundredths)
            self.assertEqual(actual, expected_at_base_80[name])
            ordered.append((weight_hundredths, actual))
        ordered.sort()
        self.assertEqual(
            [ticks for _weight, ticks in ordered],
            sorted(ticks for _weight, ticks in ordered),
        )

    def test_atb_signed_division_and_pre_jitter_floor_match_mips(self) -> None:
        # The helper quantizes to 2.20 lb steps and DIV truncates toward zero.
        self.assertEqual(weight.adjust_atb_ticks(80, 16_478), 79)
        self.assertEqual(weight.adjust_atb_ticks(80, 16_522), 80)
        self.assertEqual(weight.adjust_atb_ticks(80, 17_138), 80)
        self.assertEqual(weight.adjust_atb_ticks(80, 17_160), 81)
        # Retail subsequently subtracts rand()%8-4.  A pre-jitter floor of 4
        # guarantees the final byte never wraps below zero.
        for base_ticks in (1, 2, 3):
            with self.subTest(base_ticks=base_ticks):
                self.assertEqual(
                    weight.adjust_atb_ticks(base_ticks, 16_720),
                    4,
                )
        self.assertEqual(weight.adjust_atb_ticks(1, 0), 4)
        self.assertEqual(weight.adjust_atb_ticks(156, 53_658), 239)

    def test_curves_are_monotonic_over_the_retail_weight_domain(self) -> None:
        attacks = [
            weight.scale_physical_attack(100, 22 * native_value)
            for native_value in range(0, 2440)
        ]
        ticks = [
            weight.adjust_atb_ticks(80, 22 * native_value)
            for native_value in range(0, 2440)
        ]
        self.assertEqual(attacks, sorted(attacks))
        self.assertEqual(ticks, sorted(ticks))

    def test_formula_rejects_impossible_arguments(self) -> None:
        for attack in (-1, 256):
            with self.subTest(attack=attack), self.assertRaises(ValueError):
                weight.scale_physical_attack(attack, 16_720)
        with self.assertRaises(ValueError):
            weight.scale_physical_attack(100, -1)
        with self.assertRaises(ValueError):
            weight.adjust_atb_ticks(-1, 16_720)
        with self.assertRaises(ValueError):
            weight.adjust_atb_ticks(80, -1)


class BattleWeightOverlayPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.retail = RETAIL_DECODED_OVERLAY.read_bytes()
        cls.patched = weight.patch_decoded_battle_overlay(cls.retail)

    def test_helper_layout_fits_the_audited_unreferenced_cave(self) -> None:
        self.assertEqual(len(weight.DAMAGE_HELPER), 88)
        self.assertEqual(len(weight.ATB_HELPER), 88)
        self.assertEqual(len(weight.INJECTED_CODE), 176)
        self.assertLessEqual(len(weight.INJECTED_CODE), weight.CODE_CAVE_SIZE)
        self.assertEqual(
            hashlib.sha256(weight.INJECTED_CODE).hexdigest(),
            "70925d5afa86f0bcc2fc4fbad8b22592205630379e1f1426b7364950b40ade7b",
        )
        self.assertEqual(weight.ATB_HELPER_ADDRESS, 0x8009B400)

    def test_helpers_schedule_every_r3000a_load_delay(self) -> None:
        # LW battleEntities; independent fixed-weight LBU; then consume LW.
        self.assertEqual(
            weight.DAMAGE_HELPER_WORDS[1:4],
            (0x8D0834B0, 0x90490077, 0x00484023),
        )
        # Mutable-weight LBU; independent tenths LBU; then consume mutable.
        self.assertEqual(
            weight.DAMAGE_HELPER_WORDS[6:9],
            (0x90480078, 0x904A0079, 0x01094021),
        )
        # The multiply result is followed by two safe instructions before
        # DIVU can modify HI/LO, as required for R3000 exception recovery.
        self.assertEqual(
            weight.DAMAGE_HELPER_WORDS[14:20],
            (0x00E80019, 0x00003812, 0x340807D0, 0, 0x00E8001B, 0x00003812),
        )
        # The ATB helper likewise fills both its base-pointer and flag delays.
        self.assertEqual(
            weight.ATB_HELPER_WORDS[1:4],
            (0x8D0834B0, 0x90C90077, 0x00C84023),
        )
        self.assertEqual(
            weight.ATB_HELPER_WORDS[6:11],
            (0x90C8015A, 0x90C20078, 0x31080080, 0x1500000A, 0x01224021),
        )
        # Signed SLTI catches 1..3, and a plain J tail-calls retail RNG while
        # preserving the hook's RA for RNG to return through.
        self.assertEqual(weight.ATB_HELPER_WORDS[16:22], (
            0x2A080004,
            0x11000002,
            0,
            0x34100004,
            0x0800FE8E,
            0,
        ))

    def test_hooks_keep_their_native_load_and_subtract_delay_slots(self) -> None:
        self.assertEqual(
            weight.DAMAGE_HOOK_PATCHED,
            bytes.fromhex("EA 6C 02 0C 58 00 47 90"),
        )
        self.assertEqual(
            weight.ATB_HOOK_PATCHED,
            bytes.fromhex("00 6D 02 0C 23 80 50 00"),
        )
        self.assertEqual(
            self.patched[
                weight.DAMAGE_HOOK_OFFSET : weight.DAMAGE_HOOK_OFFSET + 8
            ],
            weight.DAMAGE_HOOK_PATCHED,
        )
        self.assertEqual(
            self.patched[weight.ATB_HOOK_OFFSET : weight.ATB_HOOK_OFFSET + 8],
            weight.ATB_HOOK_PATCHED,
        )

    def test_patch_changes_only_two_calls_and_the_code_cave(self) -> None:
        changed = {
            index
            for index, (before, after) in enumerate(
                zip(self.retail, self.patched, strict=True)
            )
            if before != after
        }
        allowed = (
            set(range(weight.DAMAGE_HOOK_OFFSET, weight.DAMAGE_HOOK_OFFSET + 4))
            | set(range(weight.ATB_HOOK_OFFSET, weight.ATB_HOOK_OFFSET + 4))
            | set(
                range(
                    weight.CODE_CAVE_OFFSET,
                    weight.CODE_CAVE_OFFSET + len(weight.INJECTED_CODE),
                )
            )
        )
        # Zero bytes inside encoded instructions naturally equal the empty
        # cave's prior bytes; every actual change must still stay in scope.
        self.assertTrue(changed <= allowed)
        self.assertTrue(
            set(range(weight.DAMAGE_HOOK_OFFSET, weight.DAMAGE_HOOK_OFFSET + 4))
            & changed
        )
        self.assertTrue(
            set(range(weight.ATB_HOOK_OFFSET, weight.ATB_HOOK_OFFSET + 4))
            & changed
        )
        self.assertEqual(
            self.patched[
                weight.CODE_CAVE_OFFSET :
                weight.CODE_CAVE_OFFSET + len(weight.INJECTED_CODE)
            ],
            weight.INJECTED_CODE,
        )
        self.assertEqual(
            self.patched[
                weight.CODE_CAVE_OFFSET + len(weight.INJECTED_CODE) :
                weight.CODE_CAVE_OFFSET + weight.CODE_CAVE_SIZE
            ],
            bytes(weight.CODE_CAVE_SIZE - len(weight.INJECTED_CODE)),
        )

    def test_patch_has_the_frozen_decoded_hash(self) -> None:
        self.assertEqual(len(self.patched), weight.BATTLE_OVERLAY_DECODED_SIZE)
        self.assertEqual(
            hashlib.sha256(self.patched).hexdigest(),
            weight.BATTLE_OVERLAY_DECODED_PATCHED_SHA256,
        )

    def test_patch_rejects_wrong_or_already_patched_sources(self) -> None:
        corrupted = bytearray(self.retail)
        corrupted[0x100] ^= 1
        with self.assertRaises(weight.BattleWeightPatchError):
            weight.patch_decoded_battle_overlay(bytes(corrupted))
        with self.assertRaises(weight.BattleWeightPatchError):
            weight.patch_decoded_battle_overlay(self.patched)


if __name__ == "__main__":
    unittest.main()
