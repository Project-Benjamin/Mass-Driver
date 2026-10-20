import struct
import unittest
from pathlib import Path
from modules.definitive.options import Options, PENDING
from modules.definitive.qol import double_enemy_xp, RECORD_END, RECORD_START, RECORD_SIZE, XP_OFFSET


class OptionTests(unittest.TestCase):
    def test_unimplemented_features_cannot_silently_succeed(self):
        for key in PENDING:
            with self.subTest(key=key), self.assertRaises(ValueError):
                Options.from_dict({key: True})
        for value in ("half", "typo"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Options.from_dict({"encounters": value})
        self.assertEqual(Options.from_dict({"encounters": "none"}).encounters, "none")

    def test_strict_boolean_and_unknown_keys(self):
        for value in ({"yellow_names": "false"}, {"double_xp": 1}, {"all_fixes": True}):
            with self.assertRaises(ValueError):
                Options.from_dict(value)
        self.assertFalse(Options.from_dict({"bug_fixes": False}).bug_fixes)


class RewardTests(unittest.TestCase):
    def fixture(self):
        data = bytearray([0xA5] * (RECORD_END + 200))
        struct.pack_into("<H", data, 0, RECORD_END)
        for slot in range(8):
            struct.pack_into("<I", data, RECORD_START + slot * RECORD_SIZE + XP_OFFSET, slot * 70000)
        return bytes(data)

    def test_rewards_use_32_bits_and_preserve_scripts_gold_and_all_other_bytes(self):
        original = self.fixture()
        result, changes = double_enemy_xp(original)
        self.assertEqual(len(changes), 7)
        restored = bytearray(result)
        for slot in range(8):
            offset = RECORD_START + slot * RECORD_SIZE + XP_OFFSET
            self.assertEqual(struct.unpack_from("<I", result, offset)[0], slot * 140000)
            restored[offset:offset+4] = original[offset:offset+4]
        self.assertEqual(restored, original)

    def test_malformed_and_overflow_rejected_before_publish(self):
        for data in (b"", bytes(RECORD_END), self.fixture()[:100]):
            with self.assertRaises(ValueError):
                double_enemy_xp(data)
        data = bytearray(self.fixture())
        struct.pack_into("<I", data, RECORD_START + XP_OFFSET, 0x40000000)
        with self.assertRaisesRegex(ValueError, "overflow"):
            double_enemy_xp(data)

    def test_every_retail_enemy_file_on_both_discs(self):
        from shared.project_registry import load_registry
        from modules.definitive.build import RetailDisc
        from modules.definitive.qol import ENEMY_FILES
        root = Path(__file__).resolve().parents[3]
        registry = load_registry(root)
        for disc in (1, 2):
            path = Path(registry['sources'][f'retail_disc{disc}']['path'])
            if not path.is_file():
                self.skipTest('Configured retail discs unavailable')
            reader = RetailDisc(path, disc)
            for canonical in ENEMY_FILES:
                with self.subTest(disc=disc, canonical=canonical):
                    original = reader.read(canonical)
                    result, changes = double_enemy_xp(original)
                    restored = bytearray(result)
                    for change in changes:
                        offset = change['offset']
                        self.assertEqual(change['after'], 2 * change['before'])
                        restored[offset:offset+4] = original[offset:offset+4]
                    self.assertEqual(restored, original)


if __name__ == '__main__':
    unittest.main()
