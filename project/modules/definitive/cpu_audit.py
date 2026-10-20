"""Execute bounded native mechanics blocks, without launching a PSX emulator.

Unicorn models CPU instructions, not the game's scenes, saves, GPU or timing.
These checks exercise existing delay-slot-safe blocks only; they cannot certify
arbitrary R3000A load-delay behavior or a full campaign.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

from modules.definitive.build import RetailDisc, digest, RETAIL_SHA256
from shared.tools.xgfield import decompress_lzss

BATTLE_BASE = 0x8006FAF0
SHOP_BASE = 0x801C5000
MASK = 0x1FFFFFFF


class CpuAuditError(ValueError):
    pass


class Machine:
    def __init__(self, data, base):
        from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE
        from unicorn import mips_const
        self.regs = mips_const
        self.cpu = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_LITTLE_ENDIAN)
        self.cpu.mem_map(0, 0x200000)
        self.end = None
        self.reached = False
        self.cpu.hook_add(UC_HOOK_CODE, self._boundary)
        self.write(base, data)

    def _boundary(self, cpu, address, size, user_data):
        if address == self.end:
            self.reached = True
            cpu.emu_stop()

    def write(self, address, data):
        self.cpu.mem_write(address & MASK, bytes(data))

    def read(self, address, count):
        return bytes(self.cpu.mem_read(address & MASK, count))

    def reg(self, name, value=None):
        register = getattr(self.regs, "UC_MIPS_REG_" + name.upper())
        if value is not None:
            self.cpu.reg_write(register, value)
        return self.cpu.reg_read(register)

    def run(self, start, end, *, max_instructions=1000):
        self.end, self.reached = end, False
        self.cpu.emu_start(start, 0, timeout=100_000, count=max_instructions)
        if not self.reached:
            raise CpuAuditError(f"Native block did not reach its boundary: {self.reg('pc'):08x}")


def charger_cases(decoded):
    machine = Machine(decoded, BATTLE_BASE)
    machine.reg("s0", 0x80100000)
    machine.reg("s2", 0x80101000)
    machine.reg("a1", 0x80102000)
    rows = []
    for charger in (0, 5, 10, 20, 50):
        for level in range(6):
            for damage_table_head in (0, 1, 10, 32767, 65535):
                machine.write(0x80100057, bytes([charger]))
                machine.write(0x80101000, bytes([level]))
                machine.write(0x80102000, struct.pack("<H", damage_table_head))
                machine.run(0x8009A370, 0x8009A3FC)
                expected = charger * 10 if charger else 30
                if level in (1, 2, 3):
                    expected += level * 20
                elif level == 4:
                    expected *= 10
                actual = struct.unpack("<H", machine.read(0x80102026, 2))[0]
                rows.append({"charger_stat": charger, "attack_level": level,
                             "damage_table_head": damage_table_head,
                             "expected": expected, "actual": actual, "passed": actual == expected})
    return rows


def defense_cases(decoded):
    machine = Machine(decoded, BATTLE_BASE)
    machine.reg("a0", 0x80100000)
    machine.write(0x800C3E50, b"\0")
    machine.write(0x800C34B0, struct.pack("<I", 0x80110000))
    rows = []
    for status, temporary in ((0, 0), (0x100, 0), (0, 0x100), (0x4000, 0),
                              (0, 0x4000), (0x4000, 0x100), (0xFFFF, 0)):
        for defense in (0, 1, 2, 127, 255, 1024, 65535):
            for bypass in (False, True):
                machine.write(0x80100084, struct.pack("<HH", status, temporary))
                machine.write(0x8011015A, bytes([0x80 if bypass else 0]))
                machine.reg("a2", defense)
                machine.run(0x800976C8, 0x80097774)
                expected = defense * 3 // 2 if (status | temporary) & 0x4000 else defense
                if bypass:
                    expected = 0
                actual = machine.reg("a2")
                rows.append({"status": status, "temporary_status": temporary,
                             "defense": defense, "bypass": bypass,
                             "expected": expected, "actual": actual, "passed": actual == expected})
    return rows


def gear_shop_cases(data):
    machine = Machine(data, SHOP_BASE)
    machine.reg("s0", 0x80100000)
    machine.reg("t0", 0x80101000)
    rows = []
    for amplifier in (0, 1, 2, 8, 16, 64, 128, 255):
        original = bytearray(range(256))
        original[0x54] = amplifier
        machine.write(0x80100000, original)
        machine.write(0x80101000, b"\xff\xff")
        machine.run(SHOP_BASE + 0x113D8, SHOP_BASE + 0x1144C)
        expected = original.copy()
        expected[0x50:0x54] = bytes(4)
        expected[0x55:0x58] = bytes(3)
        expected[0x7E:0x80] = bytes(2)
        expected[0x82:0x84] = bytes(2)
        expected[0x86:0x88] = struct.pack("<H", struct.unpack_from("<H", original, 0x86)[0] & 0xF000)
        actual = machine.read(0x80100000, 256)
        rows.append({"amplifier": amplifier, "actual_amplifier": actual[0x54],
                     "passed": actual == expected and machine.read(0x80101000, 2) == b"\x7f\xdb",
                     "changed_gear_offsets": [i for i, (a, b) in enumerate(zip(original, actual)) if a != b]})
    return rows


def audit_routines(retail_battle, built_battle, retail_shop, built_shop):
    report = {}
    for name, check, original, built in (
        ("charger", charger_cases, retail_battle, built_battle),
        ("defense_up", defense_cases, retail_battle, built_battle),
        ("gear_shop_ether_amp", gear_shop_cases, retail_shop, built_shop),
    ):
        before, after = check(original), check(built)
        report[name] = {"cases_per_variant": len(after),
                        "retail_failures": sum(not row["passed"] for row in before),
                        "built_failures": sum(not row["passed"] for row in after),
                        "retail_cases": before, "built_cases": after}
    report["passed"] = all(report[name]["built_failures"] == 0 for name in
                           ("charger", "defense_up", "gear_shop_ether_amp"))
    return report


def audit_release(folder: Path):
    import unicorn
    folder = folder.resolve()
    receipt = json.loads((folder / "project-build.json").read_text(encoding="utf-8"))
    if receipt.get("status") != "built" or receipt.get("plan", {}).get("profile") != "definitive":
        raise CpuAuditError("A completed Definitive release receipt is required")
    output_records = {row["path"]: row for row in receipt["outputs"]}
    report = {"format": "xenogears-native-cpu-audit-v1", "release": receipt["plan"]["release"],
              "engine": f"Unicorn {unicorn.__version__} MIPS32 little-endian",
              "scope": "Bounded native instruction blocks; not PSX gameplay or a full bug certification",
              "limits": ["Fuel reservoir caps and final damage outside these blocks were not executed",
                         "Scene progression, menu entry, save/load, R3000A timing and campaign were not tested"],
              "discs": {}, "gameplay_status": "untested"}
    for disc in (1, 2):
        original_path = Path(receipt["sources"][f"retail_disc{disc}"]["path"])
        name = f"Xenogears_Definitive_CD{disc}.bin"
        built_path = folder / name
        original_digest, built_digest = digest(original_path), digest(built_path)
        if original_digest != RETAIL_SHA256[disc] or built_digest != output_records[name]["sha256"]:
            raise CpuAuditError(f"Disc {disc} identity does not match its audited receipt")
        original, built = RetailDisc(original_path, disc), RetailDisc(built_path, disc)
        def decoded(reader):
            packed = reader.read(38)
            return decompress_lzss(packed, int.from_bytes(packed[:4], "little")).data
        findings = audit_routines(decoded(original), decoded(built), original.read(2602), built.read(2602))
        report["discs"][str(disc)] = {"source_sha256": original_digest, "built_sha256": built_digest, **findings}
    report["passed"] = all(value["passed"] for value in report["discs"].values())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit_release(args.build_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"release": report["release"], "passed": report["passed"],
                      "gameplay_status": report["gameplay_status"], "output": str(args.output)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
