from __future__ import annotations

import importlib.util
import struct
import unittest

from modules.definitive import deus_fix, mechanics, qol
from modules.definitive.tests.test_mechanics import _retail_sources
from shared.tools.xgdisc import Mode2Image


def _reads(word):
    op, rs, rt = word >> 26, (word >> 21) & 31, (word >> 16) & 31
    if op == 0:
        return {rt} if (word & 63) in (0, 2, 3) else {rs, rt}
    if op in (2, 3, 15):
        return set()
    if op in (4, 5, 40, 41, 43):
        return {rs, rt}
    return {rs}


@unittest.skipUnless(_retail_sources(), "local user retail discs are not configured")
class DeusBinaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discs = []
        for disc, path in _retail_sources():
            image = Mode2Image(path)
            entries = image.read_index()
            ids = set(deus_fix.ENEMY_FILES) | {38, 2602}
            data = {n: image.extract_entry(entries[n - (5 if disc == 2 else 0)]) for n in ids}
            cls.discs.append((disc, data))
        cls.retail = cls.discs[0][1]
        cls.decoded = deus_fix._decode(cls.retail[38])

    def test_both_disc_script_regions_have_only_zero_reserved_bytes(self):
        for disc, data in self.discs:
            with self.subTest(disc=disc):
                report = deus_fix.verify_unused_script_flags(data.__getitem__)
                self.assertEqual(report["file_count"], 76)
                self.assertEqual(report["command_01_records"], 12407)
                self.assertEqual(report["nonzero_reserved_bytes"], 0)

    def test_exact_source_patch_and_composition_preserve_unselected_bytes(self):
        for disc, data in self.discs:
            with self.subTest(disc=disc):
                existing, _ = mechanics.build_mechanics_replacements(data.__getitem__)
                result, report = deus_fix.build_deus_replacements(data.__getitem__, existing)
                before, after = deus_fix._decode(existing[38]), deus_fix._decode(result[38])
                self.assertEqual(report["battle_decoded_changed_bytes"], 158)
                allowed = {o for start, original, _ in deus_fix.BLOCKS for o in range(start, start + len(original))}
                self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(before, after))))
                self.assertEqual(len(before), len(after))
                self.assertEqual(result[2602], existing[2602])
                self.assertEqual([i for i, (a, b) in enumerate(zip(data[2746], result[2746])) if a != b], [0xC25])
                for fix in mechanics.BATTLE_FIXES:
                    self.assertEqual(after[fix.offset:fix.offset + 4], fix.after)
                # XP can compose after this without removing the script flag.
                rewards, _ = qol.patch_rewards(data.__getitem__, result)
                self.assertEqual(rewards[2746][0xC25], 1)
                self.assertEqual(rewards[2746][0xBB2:], result[2746][0xBB2:])

    def test_nonzero_flags_or_unknown_changes_fail_closed(self):
        modified = dict(self.retail)
        enemy = bytearray(modified[2746])
        enemy[0xBFA + 3] = 2  # another command must never suppress its camera
        modified[2746] = bytes(enemy)
        with self.assertRaises(deus_fix.DeusPatchError):
            deus_fix.build_deus_replacements(modified.__getitem__)
        wrong = bytearray(self.decoded)
        wrong[0x200] ^= 1
        with self.assertRaises(deus_fix.DeusPatchError):
            deus_fix.patch_decoded_battle(bytes(wrong))
        already = deus_fix.patch_decoded_battle(self.decoded)
        with self.assertRaises(deus_fix.DeusPatchError):
            deus_fix.patch_decoded_battle(already)
        with self.assertRaises(deus_fix.DeusPatchError):
            deus_fix.build_deus_replacements(self.retail.__getitem__, {2746: qol.double_enemy_xp(self.retail[2746])[0]})

    def test_padding_has_no_retail_direct_reference_and_follows_function_return(self):
        words = struct.unpack(f"<{len(self.decoded) // 4}I", self.decoded)
        self.assertNotIn(deus_fix.SCRATCH_ADDRESS, words)
        self.assertEqual(words[deus_fix.SCRATCH_OFFSET // 4 - 2:deus_fix.SCRATCH_OFFSET // 4 + 1],
                         (0x03E00008, 0, 0))
        # Any direct indexed access to this low address would be visible here;
        # whole-overlay identity excludes hidden edits. Neighbour globals differ.
        accesses = [w for w in words if w >> 26 in (9, 13, 32, 33, 35, 36, 37, 40, 41, 43)
                    and (w & 0xFFFF) == 0x2048]
        self.assertEqual(accesses, [])

    def test_changed_blocks_respect_r3000_load_delay_and_original_targets(self):
        decoded = deus_fix.patch_decoded_battle(self.decoded)
        for start, before, after in deus_fix.BLOCKS:
            for offset in range(start, start + len(after), 4):
                word, next_word = struct.unpack_from("<II", decoded, offset)
                if word >> 26 in (32, 33, 35, 36, 37):
                    self.assertNotIn((word >> 16) & 31, _reads(next_word), f"load delay at {offset:#x}")
        word = struct.unpack_from("<I", decoded, 0x3E110)[0]
        self.assertEqual(word, 0x11C00003)
        self.assertEqual(0x3E110 + 4 + (word & 0xFFFF) * 4, 0x3E120)
        for offset in (0x3D0E4, 0x3E118, 0x3E1A4):
            self.assertEqual(struct.unpack_from("<I", decoded, offset)[0], 0x0802B7AF)
        # Interpreter join redefines s5 in its branch delay slot, before reuse.
        self.assertEqual(decoded[0x3E3CC:0x3E3DC], bytes.fromhex("5001af8f0000000083f4e01521a86002"))


@unittest.skipUnless(importlib.util.find_spec("unicorn") and _retail_sources(), "Unicorn and local retail discs required")
class DeusCpuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from modules.definitive.cpu_audit import Machine
        cls.Machine = Machine
        disc, path = _retail_sources()[0]
        image = Mode2Image(path)
        cls.retail = deus_fix._decode(image.extract_entry(image.read_index()[38 - (5 if disc == 2 else 0)]))
        cls.patched = deus_fix.patch_decoded_battle(cls.retail)

    def camera(self, decoded, flag, coordinates, angle):
        from unicorn import UC_HOOK_CODE
        m = self.Machine(decoded, 0x8006FAF0)
        m.reg("sp", 0x801F0000)
        m.write(0x801F0130, struct.pack("<I", 0x80101000))
        m.write(0x800D3354, struct.pack("<hhhhhhh", coordinates[0], 0, coordinates[1], 0, coordinates[2], 0, coordinates[3]))
        m.write(0x800C3B80, bytes([0x55]) * 48)
        m.write(0x800C3DF8, b"\x55")
        m.write(deus_fix.SCRATCH_ADDRESS, bytes([flag]))
        calls = []
        def trace(cpu, address, size, _):
            if address in (0x800B00F4, 0x800BCAA4, 0x8004B32C):
                calls.append((address, m.reg("a0"), m.reg("a1")))
        m.cpu.hook_add(UC_HOOK_CODE, trace)
        for address in (0x800B00F4, 0x800BCAA4):
            m.write(address, struct.pack("<II", 0x03E00008, 0))
        m.write(0x8004B32C, struct.pack("<II", 0x03E00008, 0x34020000 | angle))
        m.run(0x800ADBF4, 0x800ADEBC)  # decoded0x3E104 through interpreter join
        return m, calls

    def test_unflagged_camera_preserves_calls_arguments_and_camera_state(self):
        for coords in ((0, 0, 0, 0), (-500, 800, 1300, -900), (32767, -32768, -32768, 32767)):
            for angle in (0, 0x456, 0x1FFF, 0xFFFF):
                original, original_calls = self.camera(self.retail, 0, coords, angle)
                patched, patched_calls = self.camera(self.patched, 0, coords, angle)
                self.assertEqual(len(patched_calls), 3)
                self.assertEqual(patched_calls, original_calls)
                for address, size in ((0x800C3B80, 48), (0x800C3DF8, 1)):
                    self.assertEqual(patched.read(address, size), original.read(address, size))
                for reg in ("v0", "s0", "s1", "s3", "s5"):
                    self.assertEqual(patched.reg(reg), original.reg(reg))

    def test_marked_camera_skips_calls_preserves_state_and_consumes_flag(self):
        m, calls = self.camera(self.patched, 1, (-500, 800, 1300, -900), 0x1234)
        self.assertEqual(calls, [])
        self.assertEqual(m.read(0x800C3B80, 48), b"\x55" * 48)
        self.assertEqual(m.read(0x800C3DF8, 1), b"\x55")
        self.assertEqual(m.read(deus_fix.SCRATCH_ADDRESS, 1), b"\0")
        m.run(0x800ADBF4, 0x800ADEBC)
        self.assertEqual(len(calls), 3)  # following unmarked invocation proceeds

    def test_command_capture_preserves_context_and_iteration_count(self):
        for slot in (0, 1, 7):
            for index in (0, 4, 31):
                for flag in (0, 1):
                    results = []
                    for decoded in (self.retail, self.patched):
                        m = self.Machine(decoded, 0x8006FAF0)
                        m.reg("a0", 0x80110000)
                        m.reg("a1", 0x80112000)
                        m.reg("a2", index)
                        m.reg("ra", 0x801E0000)
                        m.write(0x80110000, struct.pack("<I", 0x80111000))
                        m.write(0x80111000, bytes((1, slot, 0x67, flag)))
                        m.run(0x8007A828, 0x801E0000)
                        results.append((m.read(0x80112000, 264), m.reg("v0")))
                        if decoded is self.patched:
                            self.assertEqual(m.read(deus_fix.SCRATCH_ADDRESS, 1), bytes([flag]))
                    self.assertEqual(results[0], results[1])
                    self.assertEqual(results[1][1], index + (slot == 0))

    def test_reset_clears_transient_state_and_interpreter_restores_s5(self):
        for flag in (0, 1, 255):
            m = self.Machine(self.patched, 0x8006FAF0)
            m.reg("sp", 0x801F0000)
            m.reg("s3", 0x80112340)
            m.reg("s5", 0x12345678)
            m.write(deus_fix.SCRATCH_ADDRESS, bytes([flag]))
            m.write(0x801F0150, bytes(4))
            m.write(0x800BF6CC, struct.pack("<II", 0x03E00008, 0))
            m.run(0x800ACBCC, 0x800ADECC)  # decoded3D0DC through3E3DC
            self.assertEqual(m.read(deus_fix.SCRATCH_ADDRESS, 1), b"\0")
            self.assertEqual(m.reg("s5"), m.reg("s3"))


if __name__ == "__main__":
    unittest.main()
