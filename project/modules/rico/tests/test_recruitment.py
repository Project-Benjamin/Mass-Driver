from __future__ import annotations

from collections import defaultdict
import hashlib
from pathlib import Path
import struct
import unittest

from modules.rico import recruitment as recruitment
from modules.rico.tools import xgrico_balance as balance
from shared.tools.xgdeathblows import grant_all_on_foot_deathblows
from shared.tools.xgdisc import Mode2Image
from shared.tools.xgfield import decompress_lzss


ROOT = Path(__file__).resolve().parents[3]


def _donor() -> bytes:
    # Distinct nonzero bytes reveal writes beyond the declared Rico windows.
    result = bytearray((i * 37 + 11) % 256 for i in range(balance.GAMESTATE_SIZE))
    for character in range(11):
        start = balance.PARTY_RECORD_BASE + character * balance.PARTY_RECORD_SIZE
        result[start + balance.CHARACTER_ID_OFFSET] = character
        result[start + 0x62 : start + 0x64] = bytes((70, 70))
    return bytes(result)


class RicoRecruitmentTests(unittest.TestCase):
    def test_overrides_old_buffs_with_coherent_progression_and_early_commands(self):
        donor = balance.apply_initial_character_balance(grant_all_on_foot_deathblows(_donor()))
        result = recruitment.apply_rico_recruitment_profile(donor)
        r = recruitment.RICO_RECORD
        self.assertEqual(result[r + 0x62 : r + 0x64], bytes((24, 24)))
        self.assertEqual(struct.unpack_from("<4I", result, r + 0x3C), (49265, 49265, 8051, 8051))
        self.assertEqual(struct.unpack_from("<4H", result, r + 0x4C), (209, 209, 23, 23))
        self.assertEqual(result[r + 0x58 : r + 0x60], bytes((39, 35, 7, 10, 12, 0, 13, 12)))
        self.assertEqual(struct.unpack_from("<3H", result, balance.RICO_ABILITY_RECORD), (0xF000, 0xC000, 0x1800))
        self.assertEqual(result[balance.RICO_ABILITY_RECORD + 0x17], 6)
        self.assertEqual(result[r + 0x90 : r + 0xA0], bytes(16))
        self.assertEqual(result[r + 0x55], 3)

    def test_only_adult_rico_progression_changes_and_result_is_idempotent(self):
        donor = balance.apply_initial_character_balance(_donor())
        result = recruitment.apply_rico_recruitment_profile(donor)
        r = recruitment.RICO_RECORD
        allowed = set()
        for start, end in ((r + 0x3C, r + 0x54), (r + 0x55, r + 0x56),
                           (r + 0x58, r + 0x60), (r + 0x62, r + 0x64),
                           (r + 0x90, r + 0xA0),
                           (balance.RICO_ABILITY_RECORD, balance.RICO_ABILITY_RECORD + 0x20)):
            allowed.update(range(start, end))
        changed = {i for i, pair in enumerate(zip(donor, result, strict=True)) if pair[0] != pair[1]}
        self.assertTrue(changed)
        self.assertFalse(changed - allowed)
        self.assertEqual(recruitment.apply_rico_recruitment_profile(result), result)
        self.assertEqual(len(result), len(donor))
        # Equipment, the customized body weight, and Stier's identity remain.
        self.assertEqual(result[r + 0x6A : r + 0x90], donor[r + 0x6A : r + 0x90])
        self.assertEqual(result[r + 0xA0 : r + 0xA4], donor[r + 0xA0 : r + 0xA4])

    def test_bad_sizes_or_wrong_character_are_rejected_without_mutation(self):
        donor = bytearray(_donor())
        for source in (b"", bytes(donor[:-1]), bytes(donor) + b"\0"):
            with self.assertRaises(recruitment.RicoRecruitmentError):
                recruitment.apply_rico_recruitment_profile(source)
        donor[recruitment.RICO_RECORD + balance.CHARACTER_ID_OFFSET] = 4
        original = bytes(donor)
        with self.assertRaises(recruitment.RicoRecruitmentError):
            recruitment.apply_rico_recruitment_profile(donor)
        self.assertEqual(bytes(donor), original)

    def test_profile_stats_are_median_native_growth_outcomes(self):
        # Enumerate every roll outcome, independent of the constant profile.
        # Native growth formulas use integer divisions and uniform 0..99 rolls.
        initial = (110, 14, 28, 23, 6, 7, 10, 9)
        growth = (999, 70, 100, 100, 30, 38, 30, 28)
        medians = []
        for stat, (start, target) in enumerate(zip(initial, growth, strict=True)):
            distribution = {start: 1.0}
            for level in range(11, 25):
                following = defaultdict(float)
                for current, probability in distribution.items():
                    for roll in range(100):
                        if stat == 0:
                            gain = (target + 99 - level - current) * roll // ((100 - level) * 100) + 2
                        else:
                            divisor = (99 if stat == 1 else 100) - level
                            gain = int((target - current) * 100 // divisor - 50 + roll >= 50)
                        following[current + gain] += probability / 100
                distribution = following
            cumulative = 0.0
            for value, probability in sorted(distribution.items()):
                cumulative += probability
                if cumulative >= 0.5:
                    medians.append(value)
                    break
        p = recruitment.RICO_RECRUITMENT_PROFILE
        self.assertEqual(medians, [p.hp, p.mp, p.stats[0], p.stats[1], p.stats[3], p.stats[4], p.stats[6], p.stats[7]])

    @unittest.skipUnless((ROOT / "Xenogears (Disc 1).bin").is_file(), "native disc is not installed")
    def test_recruitment_profile_matches_checked_retail_tables(self):
        image = Mode2Image(ROOT / "Xenogears (Disc 1).bin")
        entries = image.read_index()
        initial = image.extract_entry(entries[2595])
        self.assertEqual(hashlib.sha256(initial).hexdigest(), "d892fa678f66ab12e0d2cb5ccb6cd432ecbc055b41360d8a4c4404fd38f1e20b")
        source = image.extract_entry(entries[2607])
        start = struct.unpack_from("<I", source, 4)[0]
        size = struct.unpack_from("<I", source, start)[0]
        data = decompress_lzss(source[start:], size).data
        self.assertEqual(hashlib.sha256(data).hexdigest(), "67b4996a397b207c75310b2d32f890e1348a1041734439a6a4f161e974350c16")
        self.assertEqual(data[0x608 : 0x61A], bytes.fromhex("E703E70364C864BE1E371C351E46265A4663"))
        p = recruitment.RICO_RECRUITMENT_PROFILE
        xp = struct.unpack_from("<98I", data, 0xBB0)
        self.assertEqual(sum(xp[:p.level - 1]), p.total_experience)
        self.assertEqual(xp[p.level - 1], p.next_level_experience)
        expected_db = sum(1 << (15 - i) for i, level in enumerate(data[0x650:0x65A]) if level <= p.level)
        expected_spirit = sum(1 << (15 - i) for i, level in enumerate(data[0x640:0x644]) if level <= p.level)
        self.assertEqual((expected_db, expected_spirit), (p.on_foot_deathblows, p.spirit_commands))
        self.assertEqual(3 + sum(level <= p.level for level in data[0x61C:0x61F]), p.ap_per_turn)
        self.assertEqual(struct.unpack_from("<H", initial, balance.RICO_ABILITY_RECORD + 4)[0], p.stier_deathblows)


if __name__ == "__main__":
    unittest.main()
