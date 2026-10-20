from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import unittest

from modules.definitive import mechanics
from shared.tools.xgdisc import Mode2Image
from shared.tools.xgfield import decompress_lzss


ROOT = Path(__file__).resolve().parents[3]


def _retail_sources() -> list[tuple[int, Path]]:
    config_path = ROOT / "project.local.json"
    if not config_path.is_file():
        return []
    config = json.loads(config_path.read_text(encoding="utf-8"))
    result = []
    for disc in (1, 2):
        value = config.get("sources", {}).get(f"retail_disc{disc}", {}).get("path")
        if value:
            path = Path(value)
            if not path.is_absolute():
                path = ROOT / path
            if path.is_file():
                result.append((disc, path))
    return result


class MechanicsSelectionTests(unittest.TestCase):
    def test_disabled_mechanics_never_reads_game_data(self):
        def forbidden(_):
            self.fail("disabled option tried to read a game resource")
        replacements, receipt = mechanics.build_mechanics_replacements(forbidden, ())
        self.assertEqual(replacements, {})
        self.assertEqual(receipt["fixes"], [])

    def test_unknown_and_duplicate_fixes_rejected_before_read(self):
        def forbidden(_):
            self.fail("invalid option tried to read a game resource")
        for fixes in (("all_bugs",), ("gear_charge_multiplier",) * 2):
            with self.subTest(fixes=fixes), self.assertRaises(mechanics.MechanicsPatchError):
                mechanics.build_mechanics_replacements(forbidden, fixes)

    def test_invalid_resource_is_rejected(self):
        with self.assertRaises(mechanics.MechanicsPatchError):
            mechanics.patch_battle_resource(b"not a retail overlay")


@unittest.skipUnless(_retail_sources(), "local user retail discs are not configured")
class RetailMechanicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = []
        for disc, path in _retail_sources():
            image = Mode2Image(path)
            index = image.read_index()
            canonical = 38 if disc == 1 else 33
            cls.sources.append((disc, image.extract_entry(index[canonical])))
        cls.source = cls.sources[0][1]
        cls.decoded = decompress_lzss(cls.source, mechanics.BATTLE_DECODED_SIZE).data

    def test_both_discs_use_the_audited_retail_overlay(self):
        for disc, source in self.sources:
            with self.subTest(disc=disc):
                self.assertEqual(len(source), mechanics.BATTLE_PACKED_SIZE)
                self.assertEqual(hashlib.sha256(source).hexdigest(), mechanics.BATTLE_PACKED_SHA256)

    def test_changes_are_confined_to_selected_retail_instructions(self):
        for ids in ((), ("gear_charge_multiplier",), ("defense_up_status",), mechanics.BATTLE_FIX_IDS):
            with self.subTest(ids=ids):
                patched = mechanics.patch_decoded_battle_overlay(self.decoded, ids)
                expected = bytearray(self.decoded)
                for fix in mechanics.BATTLE_FIXES:
                    if fix.id in ids:
                        expected[fix.offset:fix.offset + 4] = fix.after
                self.assertEqual(patched, bytes(expected))
                self.assertEqual(len(patched), len(self.decoded))

    def test_charger_instruction_removes_dependency_on_damage_table(self):
        # Execute the changed instruction's actual opcode/register/immediate
        # semantics across different damage-table values and retail Charger stats.
        patched = mechanics.patch_decoded_battle_overlay(self.decoded, ("gear_charge_multiplier",))
        word = struct.unpack_from("<I", patched, 0x2A894)[0]
        self.assertEqual(word >> 26, 0x0D)  # ORI
        self.assertEqual((word >> 21) & 31, 0)  # zero
        self.assertEqual((word >> 16) & 31, 3)  # v1
        for first_damage in (0, 1, 10, 255, 65535):
            for charger_stat, fuel in ((5, 50), (10, 100), (20, 200), (50, 500)):
                with self.subTest(first_damage=first_damage, charger_stat=charger_stat):
                    multiplier = 0 | (word & 0xFFFF)
                    self.assertEqual(charger_stat * multiplier, fuel)
        # The no-Charger branch and attack-level/Infinity bonuses stay identical.
        self.assertEqual(patched[0x2A880:0x2A894], self.decoded[0x2A880:0x2A894])
        self.assertEqual(patched[0x2A898:0x2A90C], self.decoded[0x2A898:0x2A90C])

    def test_def_up_uses_its_status_bit_and_preserves_other_bits(self):
        patched = mechanics.patch_decoded_battle_overlay(self.decoded, ("defense_up_status",))
        word = struct.unpack_from("<I", patched, 0x27C28)[0]
        self.assertEqual(word >> 26, 0x0C)  # ANDI
        mask = word & 0xFFFF
        for status in (0, 0x100, 0x4000, 0x4100, 0xFFFF):
            self.assertEqual(bool(status & mask), bool(status & 0x4000))
        self.assertEqual(patched[0x27C2C:0x27C84], self.decoded[0x27C2C:0x27C84])

    def test_packed_replacements_roundtrip_and_report_runtime_honestly(self):
        for disc, source in self.sources:
            with self.subTest(disc=disc):
                packed, receipt = mechanics.patch_battle_resource(source)
                declared = int.from_bytes(packed[:4], "little")
                decoded = decompress_lzss(packed, declared).data
                expected = mechanics.patch_decoded_battle_overlay(self.decoded)
                self.assertEqual(decoded[:len(expected)], expected)
                self.assertEqual(decoded[len(expected):], bytes(declared - len(expected)))
                self.assertEqual(receipt["runtime_validation"], "not tested in emulator")
                self.assertEqual(len(receipt["fixes"]), 2)
                json.dumps(receipt)

    def test_repatch_and_unrelated_modified_inputs_are_rejected(self):
        patched = mechanics.patch_decoded_battle_overlay(self.decoded)
        changed = bytearray(self.decoded)
        changed[0x100] ^= 1
        for data in (patched, bytes(changed), self.decoded[:-1]):
            with self.assertRaises(mechanics.MechanicsPatchError):
                mechanics.patch_decoded_battle_overlay(data)

    def test_gear_shop_fix_preserves_entire_resource_except_clearing_store(self):
        for disc, path in _retail_sources():
            image = Mode2Image(path)
            index = image.read_index()
            source = image.extract_entry(index[2602 if disc == 1 else 2597])
            with self.subTest(disc=disc):
                patched, receipt = mechanics.patch_gear_shop_resource(source)
                self.assertEqual(patched[:0x11428], source[:0x11428])
                self.assertEqual(patched[0x11428:0x1142C], bytes(4))
                self.assertEqual(patched[0x1142C:], source[0x1142C:])
                self.assertEqual(receipt["patched_sha256"], mechanics.GEAR_SHOP_PATCHED_SHA256)
                with self.assertRaises(mechanics.MechanicsPatchError):
                    mechanics.patch_gear_shop_resource(patched)

    def test_builder_reads_canonical_resources_and_returns_three_fixes(self):
        disc, path = _retail_sources()[0]
        image = Mode2Image(path)
        index = image.read_index()
        reads = []
        def reader(canonical):
            reads.append(canonical)
            return image.extract_entry(index[canonical if disc == 1 else canonical - 5])
        replacements, receipt = mechanics.build_mechanics_replacements(reader)
        self.assertEqual(reads, [38, 2602])
        self.assertEqual(set(replacements), {38, 2602})
        self.assertEqual({fix["id"] for fix in receipt["fixes"]}, set(mechanics.SUPPORTED_FIX_IDS))
        self.assertEqual(len(receipt["resources"]), 2)
        json.dumps(receipt)


if __name__ == "__main__":
    unittest.main()
