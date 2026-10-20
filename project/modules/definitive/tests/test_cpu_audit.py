from importlib.util import find_spec
from pathlib import Path
import unittest

from modules.definitive.build import RetailDisc
from modules.definitive.cpu_audit import Machine, CpuAuditError, audit_routines, charger_cases
from modules.definitive.mechanics import patch_decoded_battle_overlay, patch_gear_shop_resource
from shared.project_registry import load_registry
from shared.tools.xgfield import decompress_lzss

ROOT = Path(__file__).resolve().parents[3]


@unittest.skipUnless(find_spec("unicorn"), "optional native CPU audit requires requirements-audit.txt")
class NativeMechanicsExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry = load_registry(ROOT)
        path = Path(registry["sources"]["retail_disc1"]["path"])
        if not path.is_absolute():
            path = ROOT / path
        if not path.is_file():
            raise unittest.SkipTest("local USA retail disc is unavailable")
        source = RetailDisc(path, 1)
        packed = source.read(38)
        cls.battle = decompress_lzss(packed, int.from_bytes(packed[:4], "little")).data
        cls.shop = source.read(2602)

    def test_native_blocks_reproduce_retail_defects_and_pass_with_corrections(self):
        result = audit_routines(self.battle, patch_decoded_battle_overlay(self.battle),
                                self.shop, patch_gear_shop_resource(self.shop)[0])
        self.assertTrue(result["passed"])
        for routine in ("charger", "defense_up", "gear_shop_ether_amp"):
            self.assertGreater(result[routine]["retail_failures"], 0)
            self.assertEqual(result[routine]["built_failures"], 0)

    def test_wrong_multiplier_is_detected_by_native_execution(self):
        changed = bytearray(patch_decoded_battle_overlay(self.battle))
        changed[0x2A894] = 11
        self.assertTrue(any(not row["passed"] for row in charger_cases(changed)))

    def test_instruction_limit_cannot_be_mistaken_for_reaching_boundary(self):
        machine = Machine(bytes(256), 0x80010000)
        with self.assertRaises(CpuAuditError):
            machine.run(0x80010000, 0x80010040, max_instructions=2)


if __name__ == "__main__":
    unittest.main()
