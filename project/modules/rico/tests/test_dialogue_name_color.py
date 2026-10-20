"""Differential R3000A execution of the opt-in kernel text patch."""
from pathlib import Path
import json
import struct
import tempfile
import unittest

from modules.rico import build as core
from modules.rico import dialogue_name_color as color
from shared.tools.xgdisc import Mode2Image, RAW_SECTOR_SIZE, USER_DATA_OFFSET, USER_DATA_SIZE


class Machine:
    """Small instruction interpreter with real branch and load delay slots.

Only the audited helper/dispatcher instruction set is supported. Reading a
pending load result in its delay slot fails rather than hiding a PSX hazard.
"""
    def __init__(self, executable):
        self.code = executable[0x800:]
        self.reg = [0] + [0x10100000 + i * 0x101 for i in range(1, 32)]
        self.mem = {}
        self.writes = {}
        self.pc = 0
        self.branch = None
        self.load = None

    def read(self, address, size, signed=False):
        data = bytes(self.mem.get(address + i,
                     self.code[address + i - color.LOAD_ADDRESS]
                     if color.LOAD_ADDRESS <= address + i < color.LOAD_ADDRESS + len(self.code)
                     else 0) for i in range(size))
        return int.from_bytes(data, "little", signed=signed) & 0xFFFFFFFF

    def put(self, address, value, size=4, *, initial=False):
        for i in range(size):
            self.mem[address + i] = (value >> (i * 8)) & 255
            if not initial:
                self.writes[address + i] = self.mem[address + i]

    def run(self, start, stops):
        self.pc = start
        for _ in range(300):
            if self.pc in stops and self.branch is None:
                return self
            pc, old_branch, old_load = self.pc, self.branch, self.load
            self.branch = self.load = None
            word = self.read(pc, 4)
            op, rs, rt, rd = word >> 26, word >> 21 & 31, word >> 16 & 31, word >> 11 & 31
            imm = word & 0xFFFF
            simm = imm - 0x10000 if imm & 0x8000 else imm
            changes = {}

            def register(index):
                if old_load is not None and old_load[0] == index and index != 0:
                    raise AssertionError(f"R3000A load hazard at {pc:#x}, r{index}")
                return self.reg[index]

            if word == 0:
                pass
            elif op == 0:
                funct = word & 63
                if funct == 0x21:
                    changes[rd] = register(rs) + register(rt)
                elif funct == 2:
                    changes[rd] = register(rt) >> (word >> 6 & 31)
                elif funct == 8:
                    self.branch = register(rs)
                else:
                    raise AssertionError(f"Unsupported special instruction {word:08x}")
            elif op in (2, 3):
                self.branch = ((pc + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)
                if op == 3:
                    changes[31] = pc + 8
            elif op in (4, 5):
                equal = register(rs) == register(rt)
                self.branch = pc + 4 + simm * 4 if equal == (op == 4) else pc + 8
            elif op in (9, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E):
                value = register(rs)
                if op == 9:
                    changes[rt] = value + simm
                elif op == 0x0A:
                    changes[rt] = int((value if value < 0x80000000 else value - 0x100000000) < simm)
                elif op == 0x0B:
                    changes[rt] = int(value < (simm & 0xFFFFFFFF))
                elif op == 0x0C:
                    changes[rt] = value & imm
                elif op == 0x0D:
                    changes[rt] = value | imm
                else:
                    changes[rt] = value ^ imm
            elif op == 0x0F:
                changes[rt] = imm << 16
            elif op in (0x21, 0x23, 0x24):
                size = {0x21: 2, 0x23: 4, 0x24: 1}[op]
                self.load = (rt, self.read((register(rs) + simm) & 0xFFFFFFFF, size, op == 0x21))
            elif op in (0x28, 0x29, 0x2B):
                self.put((register(rs) + simm) & 0xFFFFFFFF, register(rt),
                         {0x28: 1, 0x29: 2, 0x2B: 4}[op])
            else:
                raise AssertionError(f"Unsupported instruction {word:08x} at {pc:#x}")
            if old_load is not None and old_load[0] not in changes:
                self.reg[old_load[0]] = old_load[1]
            for register_id, value in changes.items():
                self.reg[register_id] = value & 0xFFFFFFFF
            self.reg[0] = 0
            self.pc = old_branch if old_branch is not None else pc + 4
        raise AssertionError("Helper did not reach a native continuation")


class DialogueNameColorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = core.ROOT / "project.local.json"
        if not path.is_file():
            raise unittest.SkipTest("Configured USA executable donors required")
        config = json.loads(path.read_text())
        cls.sources = {}
        for name, disc in (("retail_disc1", 1), ("retail_disc2", 2),
                           ("pw_disc1", 1), ("pw_disc2", 2)):
            source = Path(config["sources"][name]["path"])
            if source.is_file():
                cls.sources[name] = core.DiscReader(source, disc).canonical(22)
        cls.source = cls.sources["retail_disc1"]
        cls.patched = color.patch_executable(cls.source)

    def machine(self, patched=True):
        machine = Machine(self.patched if patched else self.source)
        machine.reg[16] = 0x80100000
        machine.reg[19] = 9
        machine.put(0x8010001C, 0x80110000, initial=True)
        return machine

    def executable_image(self, disc):
        """Small image with real donor EXE/FAT and deliberately relocated boot."""
        donor = self.sources[f"retail_disc{disc}"]
        expected = color.patch_executable(donor)
        actual = bytearray(expected)
        fat_size = color.FAT_ENTRY_COUNTS[disc] * 7
        fat = bytearray(donor[color.EMBEDDED_FAT_OFFSET:color.EMBEDDED_FAT_OFFSET + fat_size])
        physical_id = 22 if disc == 1 else 17
        fat[physical_id * 7:physical_id * 7 + 3] = (50).to_bytes(3, "little")
        actual[color.EMBEDDED_FAT_OFFSET:color.EMBEDDED_FAT_OFFSET + fat_size] = fat
        data = bytearray(210 * RAW_SECTOR_SIZE)

        def put(sector, content):
            for offset in range(0, len(content), USER_DATA_SIZE):
                start = (sector + offset // USER_DATA_SIZE) * RAW_SECTOR_SIZE + USER_DATA_OFFSET
                data[start:start + min(USER_DATA_SIZE, len(content) - offset)] = content[offset:offset + USER_DATA_SIZE]

        def record(name, sector, size, flags=0):
            result = bytearray(33 + len(name) + (len(name) % 2 == 0))
            result[0] = len(result)
            struct.pack_into("<I", result, 2, sector)
            struct.pack_into(">I", result, 6, sector)
            struct.pack_into("<I", result, 10, size)
            struct.pack_into(">I", result, 14, size)
            result[25] = flags
            result[32] = len(name)
            result[33:33 + len(name)] = name
            return result

        config = b"BOOT = cdrom:\\" + color.BOOT_FILENAMES[disc] + b"\r\n"
        root = record(b"\0", 20, USER_DATA_SIZE, 2)
        boot = record(color.BOOT_FILENAMES[disc], 50, color.EXE_SIZE)
        system = record(b"SYSTEM.CNF;1", 40, len(config))
        pvd = bytearray(USER_DATA_SIZE)
        pvd[:7] = b"\x01CD001\x01"
        pvd[156:156 + len(root)] = root
        put(16, pvd)
        put(20, root + boot + system)
        put(24, fat)
        put(40, config)
        put(50, actual)
        temporary = tempfile.TemporaryDirectory(prefix="rico_color_exe_")
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "fixture.bin"
        path.write_bytes(data)
        return path, expected

    @staticmethod
    def mutate_user_byte(path, sector, offset, value=None):
        position = (sector + offset // USER_DATA_SIZE) * RAW_SECTOR_SIZE + USER_DATA_OFFSET + offset % USER_DATA_SIZE
        with path.open("r+b") as stream:
            stream.seek(position)
            old = stream.read(1)[0]
            stream.seek(position)
            stream.write(bytes((old ^ 1 if value is None else value,)))

    def test_rebuilt_image_verifies_both_boot_mappings_and_only_normalizes_fat_entries(self):
        for disc in (1, 2):
            with self.subTest(disc=disc):
                path, expected = self.executable_image(disc)
                result = color.verify_executable_image(path, disc, expected)
                self.assertEqual(result["sector"], 50)
                self.assertEqual(result["physical_id"], 22 if disc == 1 else 17)
                self.assertEqual(result["embedded_fat_entries"], color.FAT_ENTRY_COUNTS[disc])
                image = Mode2Image(path)
                actual = image.extract_entry(image.read_index()[result["physical_id"]])
                self.assertNotEqual(actual, expected)  # relocated FAT must be accepted

    def test_rebuilt_image_rejects_stale_fat_missing_code_and_changed_padding(self):
        for offset, message in (
            (color.EMBEDDED_FAT_OFFSET + 22 * 7, "embedded FAT"),
            (color.file_offset(color.COLOR_ADDRESS), "staged patch"),
            (color.EMBEDDED_FAT_OFFSET + color.FAT_ENTRY_COUNTS[1] * 7, "staged patch"),
            (0x800, "staged patch"),
        ):
            with self.subTest(offset=offset):
                path, expected = self.executable_image(1)
                self.mutate_user_byte(path, 50, offset)
                with self.assertRaisesRegex(color.DialogueNameColorError, message):
                    color.verify_executable_image(path, 1, expected)

    def test_rebuilt_image_rejects_wrong_iso_extent_and_boot_configuration(self):
        path, expected = self.executable_image(1)
        # Root record is 34 bytes; change both endian extent copies coherently.
        self.mutate_user_byte(path, 20, 34 + 2, 51)
        self.mutate_user_byte(path, 20, 34 + 9, 51)
        with self.assertRaisesRegex(color.DialogueNameColorError, "boot extent"):
            color.verify_executable_image(path, 1, expected)
        path, expected = self.executable_image(2)
        self.mutate_user_byte(path, 40, len(b"BOOT = cdrom:\\"), ord("X"))
        with self.assertRaisesRegex(color.DialogueNameColorError, "SYSTEM.CNF"):
            color.verify_executable_image(path, 2, expected)

    def test_dispatch_compaction_preserves_all_five_tables_and_invalid_types(self):
        for kind in range(256):
            for index in (0, 255):
                machines = []
                for patched in (False, True):
                    machine = self.machine(patched)
                    machine.put(0x80100080, kind * 256 + index, 2, initial=True)
                    machine.put(0x80059360, 0x80120000, initial=True)
                    for offset in (0x58, 0x5C, 0x44, 0xCC, 0xC8):
                        machine.put(0x80120000 + offset, 0x80130000 + offset * 256, initial=True)
                    before = list(machine.reg)
                    machine.run(color.SUBSTITUTION_ADDRESS, {0x80034474, 0x800345A8})
                    for register in set(range(32)) - {2, 3, 4, 5, 19}:
                        self.assertEqual(machine.reg[register], before[register])
                    machines.append(machine)
                old, new = machines
                with self.subTest(kind=kind, index=index):
                    self.assertEqual(new.pc, old.pc)
                    self.assertEqual(new.writes, old.writes)
                    self.assertEqual(new.reg[19], old.reg[19])
                    if kind < 5:
                        self.assertEqual(new.reg[4:6], old.reg[4:6])

    def test_marker_consumes_extra_byte_only_for_the_opt_in_sentinel(self):
        for marker in range(256):
            machine = self.machine()
            machine.put(0x80110000, int.from_bytes(bytes((15, 11, marker, 0x20)), "little"), initial=True)
            before = list(machine.reg)
            machine.run(color.MARKER_ADDRESS, {0x800345A4})
            with self.subTest(marker=marker):
                self.assertEqual(machine.read(0x8010001C, 4), 0x80110000 + (3 if marker == 254 else 2))
                self.assertEqual(machine.read(0x8010006D, 1), marker)
                for register in set(range(32)) - {2, 3, 4}:
                    self.assertEqual(machine.reg[register], before[register])

    def test_both_sprite_halves_and_parities_color_only_the_first_marked_row(self):
        for marker in (0, 1, 253, 254, 255):
            for row in (0, 1, 6):
                for physical_row in (0, 3):
                    for parity in (0, 1):
                        for hook in color.ROW_HOOK_ADDRESSES:
                            machine = self.machine()
                            machine.reg[17] = physical_row * 0x60
                            machine.reg[18] = parity * 0x28
                            machine.reg[20] = row
                            machine.put(0x80100028, 0x80140000, initial=True)
                            machine.put(0x8010006D, marker, 1, initial=True)
                            machine.put(0x8010006E, 255, 1, initial=True)
                            before = list(machine.reg)
                            machine.run(hook, {hook + 8})
                            selected = marker == 254 and row == 0
                            self.assertEqual(machine.reg[2], 0 if selected else 255)
                            expected = {}
                            if selected:
                                pointer = 0x80140000 + physical_row * 0x60 + parity * 0x28
                                for offset in (4, 0x18):
                                    expected.update({pointer + offset + i: channel for i, channel in enumerate(color.NAME_RGB)})
                            self.assertEqual(machine.writes, expected)
                            for register in set(range(32)) - {2, 3, 31}:
                                self.assertEqual(machine.reg[register], before[register])

    def test_next_queued_block_clears_marker_and_preserves_native_delay_resets(self):
        machine = self.machine()
        machine.reg[2] = 7  # native character speed survives this hook
        machine.put(0x8010006D, 254, 1, initial=True)
        machine.put(0x80100086, 0x12345678, initial=True)
        before = list(machine.reg)
        machine.run(color.RESET_HOOK_ADDRESS, {0x80034938})
        self.assertEqual(machine.read(0x8010006D, 1), 0)
        self.assertEqual(machine.read(0x80100086, 4), 0)
        self.assertEqual(machine.reg, before)

    def test_pins_accept_active_disc_variants_and_preserve_every_other_byte(self):
        spans = ((color.SUBSTITUTION_ADDRESS, 216), (color.RESET_ADDRESS, 28),
                 (color.DISPATCH_ADDRESS + 44, 4), (color.RESET_HOOK_ADDRESS, 8),
                 *((address, 8) for address in color.ROW_HOOK_ADDRESSES))
        allowed = {color.file_offset(address) + i for address, size in spans for i in range(size)}
        for name, source in self.sources.items():
            with self.subTest(source=name):
                patched = color.patch_executable(source)
                self.assertEqual(len(patched), len(source))
                self.assertTrue({i for i, (a, b) in enumerate(zip(source, patched)) if a != b} <= allowed)
                self.assertEqual(patched[:0x8804], source[:0x8804], "Embedded archive tables changed")
                self.assertEqual(patched[0x49ABC:], source[0x49ABC:], "Live trailing globals changed")
        for offset in (0x24880, 0x25088, color.file_offset(color.DISPATCH_ADDRESS), 0x18):
            modified = bytearray(self.source)
            modified[offset] ^= 1
            with self.assertRaises(color.DialogueNameColorError):
                color.patch_executable(bytes(modified))


if __name__ == "__main__":
    unittest.main()
