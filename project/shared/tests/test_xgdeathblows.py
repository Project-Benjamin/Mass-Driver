from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import unittest

from tools import xgdeathblows as deathblows


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_GAMESTATE = (
    PROJECT_ROOT
    / "work"
    / "mass_driver_v162_stage"
    / "replacements"
    / "2595_standalone_gamestate.bin"
)
SOURCE_SHA256 = "c8d444b056e86679f6ac1ef1d60a42bf7f9bd41425c619c19dd35154e065513e"
PATCHED_SHA256 = "5880e33ef21edfd370ffa87b199d595c8f6df92d94b7c3bb96abe7a9aa056bcc"


class XenogearsDeathblowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not SOURCE_GAMESTATE.is_file():
            raise AssertionError(f"Missing checked GameState: {SOURCE_GAMESTATE}")
        cls.source = SOURCE_GAMESTATE.read_bytes()
        cls.patched = deathblows.grant_all_on_foot_deathblows(cls.source)

    def test_native_profiles_have_exact_roster_order_counts_and_masks(self) -> None:
        profiles = deathblows.DEATHBLOW_PROFILES
        self.assertEqual(tuple(profile.character_id for profile in profiles), tuple(range(11)))
        self.assertEqual(
            tuple(profile.character for profile in profiles),
            (
                "Fei",
                "Elly",
                "Citan",
                "Bart",
                "Billy",
                "Rico",
                "Emeralda (child)",
                "Chu-Chu",
                "Maria",
                "Citan (sword)",
                "Emeralda (adult)",
            ),
        )
        self.assertEqual(
            tuple(len(profile.command_names) for profile in profiles),
            (13, 11, 11, 11, 10, 10, 10, 0, 0, 11, 10),
        )
        self.assertEqual(
            tuple(profile.full_mask for profile in profiles),
            deathblows.EXPECTED_FULL_MASKS,
        )
        self.assertEqual(
            tuple(profile.word_offset for profile in profiles),
            tuple(0x16C0 + character_id * 0x20 for character_id in range(11)),
        )

    def test_checked_surface_gamestate_unlock_is_exact_and_deterministic(self) -> None:
        self.assertEqual(len(self.source), deathblows.GAMESTATE_SIZE)
        self.assertEqual(hashlib.sha256(self.source).hexdigest(), SOURCE_SHA256)
        self.assertEqual(len(self.patched), deathblows.GAMESTATE_SIZE)
        self.assertEqual(hashlib.sha256(self.patched).hexdigest(), PATCHED_SHA256)
        self.assertEqual(
            deathblows.grant_all_on_foot_deathblows(self.source), self.patched
        )
        self.assertEqual(
            deathblows.grant_all_on_foot_deathblows(self.patched), self.patched
        )

    def test_every_native_mask_is_complete_without_inventing_maria_or_chuchu_moves(self) -> None:
        for profile in deathblows.DEATHBLOW_PROFILES:
            with self.subTest(character=profile.character):
                expected = (
                    deathblows.learned_mask(self.source, profile.character_id)
                    | profile.full_mask
                )
                self.assertEqual(
                    deathblows.learned_mask(self.patched, profile.character_id),
                    expected,
                )
        self.assertEqual(deathblows.learned_mask(self.patched, 7), 0)
        self.assertEqual(deathblows.learned_mask(self.patched, 8), 0)

    def test_only_the_eight_incomplete_on_foot_halfwords_change(self) -> None:
        expected_changed_offsets = {
            offset + byte
            for offset in (0x16C0, 0x16E0, 0x1700, 0x1720, 0x1740, 0x1760, 0x1780, 0x17E0)
            for byte in (0, 1)
        }
        actual_changed_offsets = {
            offset
            for offset, (before, after) in enumerate(
                zip(self.source, self.patched, strict=True)
            )
            if before != after
        }
        self.assertEqual(actual_changed_offsets, expected_changed_offsets)

        # Levels and every later ability halfword, including Gear commands,
        # remain byte-identical.
        self.assertEqual(self.patched[0x026C:0x0978], self.source[0x026C:0x0978])
        for profile in deathblows.DEATHBLOW_PROFILES:
            start = profile.word_offset
            self.assertEqual(self.patched[start + 2 : start + 0x20], self.source[start + 2 : start + 0x20])

    def test_unrelated_bits_are_preserved_and_invalid_inputs_fail_closed(self) -> None:
        state = bytearray(self.source)
        struct.pack_into("<H", state, 0x16C0, 0x0003)
        result = deathblows.grant_all_on_foot_deathblows(bytes(state))
        self.assertEqual(struct.unpack_from("<H", result, 0x16C0)[0], 0xFFFB)

        with self.assertRaisesRegex(ValueError, "GameState"):
            deathblows.grant_all_on_foot_deathblows(self.source[:-1])
        with self.assertRaisesRegex(ValueError, "Character ID"):
            deathblows.learned_mask(self.source, 11)


if __name__ == "__main__":
    unittest.main()
