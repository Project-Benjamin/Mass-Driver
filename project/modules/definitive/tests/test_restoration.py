"""Check the real repair bundle and option composition on both retail discs."""
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from modules.definitive import build, restoration, deus_fix, mechanics, weight_fix
from modules.definitive.options import Options
from modules.definitive.qol import RECORD_START, RECORD_SIZE, XP_OFFSET, RECORD_END
from modules.definitive.item_spell_audit import archive_members, decode_member, indexed_strings
from shared.project_registry import load_registry
from shared.tools.xgfield import decompress_lzss

ROOT = Path(__file__).resolve().parents[3]


class RestorationCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry = load_registry(ROOT)
        cls.sources = []
        for disc in (1, 2):
            path = Path(registry["sources"][f"retail_disc{disc}"]["path"])
            if not path.is_absolute():
                path = ROOT / path
            if not path.is_file():
                raise unittest.SkipTest("Both local USA retail discs required")
            cls.sources.append(build.RetailDisc(path, disc))

    def test_full_bundle_survives_xp_and_encounter_composition_on_both_discs(self):
        for source in self.sources:
            with self.subTest(disc=source.disc):
                # Field dialogue has separate coverage; keep this focused on
                # the shared battle/menu resources and the actual build order.
                with patch.object(build, "patch_disc_dialogue",
                                  side_effect=lambda _path, _disc, **kw: (kw["replacements"], {})):
                    result, audit = build.prepare_disc(source, Options(double_xp=True, encounters="none"))
                self.assertTrue({36, 37, 38, 39, 2594, 2597, 2599, 2602, 2603, 2746} <= result.keys())
                decoded = decompress_lzss(result[38], mechanics.BATTLE_DECODED_SIZE).data
                for fix in mechanics.BATTLE_FIXES:
                    self.assertEqual(decoded[fix.offset:fix.offset + 4], fix.after)
                for offset, _, after in deus_fix.BLOCKS:
                    self.assertEqual(decoded[offset:offset + len(after)], after)
                enemy = result[2746]
                retail_enemy = source.read(2746)
                self.assertEqual(enemy[0xC25], 1)
                for slot in range(8):
                    offset = RECORD_START + slot * RECORD_SIZE + XP_OFFSET
                    self.assertEqual(struct.unpack_from("<I", enemy, offset)[0],
                                     2 * struct.unpack_from("<I", retail_enemy, offset)[0])
                expected_script = bytearray(retail_enemy[RECORD_END:])
                expected_script[0xC25 - RECORD_END] = 1
                self.assertEqual(enemy[RECORD_END:], expected_script)
                menu = weight_fix.patch_menu(source.read(2599))
                for canonical in (2597, 2599, 2603):
                    self.assertEqual(result[canonical], menu)
                self.assertEqual(decompress_lzss(result[39], len(menu)).data, menu)
                members = archive_members(result[2594], 56)
                for member in (14, 41):
                    strings = indexed_strings(decode_member(members[member]))
                    self.assertEqual(strings[58]["text"], "Restores HP (100) Non-battle")
                    self.assertEqual(strings[59]["text"], "Restores HP (150) Non-battle")
                self.assertEqual(set(audit["bug_fixes"]["repairs"]),
                                 {"mechanics", "deus", "descriptions", "body_weight_gain"})

    def test_unapproved_resource_overlap_cannot_silently_discard_deus_patch(self):
        with patch.object(restoration, "build_mechanics_replacements", return_value=({38: b"base"}, {})), \
                patch.object(restoration, "build_deus_replacements", return_value=({38: b"deus"}, {})), \
                patch.object(restoration, "build_description_replacements", return_value=({38: b"overwrite"}, {})):
            with self.assertRaisesRegex(ValueError, "overlaps"):
                restoration.build_restoration_replacements(lambda _: b"")


if __name__ == "__main__":
    unittest.main()
