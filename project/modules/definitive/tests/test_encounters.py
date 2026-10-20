from __future__ import annotations

import hashlib
import json
import struct
import unittest

from modules.definitive import encounters
from modules.definitive.tests.test_mechanics import _retail_sources
from shared.tools.xgdisc import Mode2Image
from shared.tools.xgfield import decompress_lzss


class EncounterSelectionTests(unittest.TestCase):
    def test_normal_mode_does_not_read_resources(self):
        def forbidden(_):
            self.fail("normal encounters read an overlay")
        self.assertEqual(encounters.build_encounter_replacements(forbidden)[0], {})

    def test_unsupported_modes_fail_before_read(self):
        def forbidden(_):
            self.fail("invalid mode read an overlay")
        for mode in ("half", "off", "all"):
            with self.assertRaises(encounters.EncounterPatchError):
                encounters.build_encounter_replacements(forbidden, mode)


@unittest.skipUnless(_retail_sources(), "local user retail discs are not configured")
class RetailEncounterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = []
        for disc, path in _retail_sources():
            image = Mode2Image(path)
            index = image.read_index()
            for patch in encounters.NO_ENCOUNTER_PATCHES:
                source = image.extract_entry(index[patch.canonical_id if disc == 1 else patch.canonical_id - 5])
                decoded = decompress_lzss(source + bytes(16), patch.decoded_size).data
                packed, receipt = encounters.patch_no_encounter_resource(source, patch.canonical_id)
                padded = decompress_lzss(packed, int.from_bytes(packed[:4], "little")).data
                cls.results.append((disc, patch, source, decoded, packed, padded, receipt))

    def test_every_byte_outside_the_two_patch_words_is_unchanged(self):
        for disc, patch, source, decoded, packed, padded, receipt in self.results:
            with self.subTest(disc=disc, canonical=patch.canonical_id):
                changed = padded[:len(decoded)]
                self.assertEqual(changed[:patch.offset], decoded[:patch.offset])
                self.assertEqual(changed[patch.offset:patch.offset + 4], patch.after)
                self.assertEqual(changed[patch.offset + 4:], decoded[patch.offset + 4:])
                self.assertEqual(padded[len(decoded):], bytes(len(padded) - len(decoded)))
                self.assertLessEqual(len(padded) - len(decoded), 7)
                self.assertEqual(hashlib.sha256(changed).hexdigest(), patch.patched_decoded_sha256)

    def test_field_always_branches_to_existing_epilogue_and_keeps_forced_battles(self):
        for disc, patch, _, decoded, _, padded, _ in self.results:
            if patch.canonical_id != 36:
                continue
            with self.subTest(disc=disc):
                word = struct.unpack_from("<I", padded, 0x99CC)[0]
                self.assertEqual(word >> 26, 4)  # BEQ
                self.assertEqual((word >> 21) & 31, 0)  # zero
                self.assertEqual((word >> 16) & 31, 0)  # zero
                self.assertEqual(0x99CC + 4 + 4 * (word & 0xFFFF), 0x9A40)
                self.assertEqual(padded[0x99D0:0x99D4], bytes(4))  # unchanged NOP delay slot
                self.assertEqual(padded[0x9A40:0x9A5C], decoded[0x9A40:0x9A5C])
                # Separate forced encounter VM handler begins at VA8009F5F4.
                self.assertEqual(padded[0x2FB04:0x30000], decoded[0x2FB04:0x30000])

    def test_worldmap_readiness_stores_all_write_zero_after_patch(self):
        for disc, patch, _, decoded, _, padded, _ in self.results:
            if patch.canonical_id != 37:
                continue
            with self.subTest(disc=disc):
                stores = []
                for offset in range(0, len(decoded) - 3, 4):
                    word = struct.unpack_from("<I", padded, offset)[0]
                    # All absolute SW sites for readiness address8009D80C.
                    if word >> 26 == 0x2B and (word & 0xFFFF) == 0xD80C:
                        stores.append((offset, (word >> 16) & 31))
                self.assertEqual(stores, [(0x1D78, 0), (0x5790, 0), (0x58F8, 0), (0x5940, 0)])
                # All movement/menu/battle dispatch callers retain their bytes.
                self.assertEqual(padded[0x1A24:0x1E00], decoded[0x1A24:0x1E00])

    def test_modified_or_patched_sources_are_rejected(self):
        for _, patch, source, _, packed, _, _ in self.results[:2]:
            damaged = bytearray(source)
            damaged[100] ^= 1
            for data in (bytes(damaged), source[:-1], packed):
                with self.assertRaises(encounters.EncounterPatchError):
                    encounters.patch_no_encounter_resource(data, patch.canonical_id)

    def test_candidate_receipts_do_not_claim_runtime_success(self):
        for _, _, _, _, _, _, receipt in self.results:
            self.assertEqual(receipt["runtime_validation"], "not tested in emulator")
            json.dumps(receipt)

    def test_builder_reads_only_field_and_worldmap_overlays(self):
        disc, path = _retail_sources()[0]
        image = Mode2Image(path)
        index = image.read_index()
        reads = []
        def reader(canonical):
            reads.append(canonical)
            return image.extract_entry(index[canonical if disc == 1 else canonical - 5])
        replacements, receipt = encounters.build_encounter_replacements(reader, "none")
        self.assertEqual(reads, [36, 37])
        self.assertEqual(set(replacements), {36, 37})
        self.assertEqual(receipt["mode"], "none")
        json.dumps(receipt)


if __name__ == "__main__":
    unittest.main()
