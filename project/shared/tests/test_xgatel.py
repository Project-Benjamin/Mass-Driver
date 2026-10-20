from __future__ import annotations

import struct
import unittest

from tools.xgatel import AtelScript, patch_transition


def _script_with_transition(field: int, parameter: int) -> bytes:
    data = bytearray(0x84 + 0x40)
    struct.pack_into("<I", data, 0x80, 1)
    data.extend(
        bytes((0x98,))
        + struct.pack("<H", field | 0x8000)
        + struct.pack("<H", parameter | 0x8000)
        + bytes((0x00,))
    )
    return bytes(data)


class AtelTests(unittest.TestCase):
    def test_reads_entity_table(self) -> None:
        script = AtelScript(_script_with_transition(618, 0))

        self.assertEqual(script.entity_count, 1)
        self.assertEqual(script.bytecode_offset, 0xC4)
        self.assertEqual(script.entry_points(), [(0, 0, 0)])

    def test_patches_transition_without_changing_size(self) -> None:
        source = _script_with_transition(618, 0)

        patched = patch_transition(source, 0, 618, 0, 721, 0)

        self.assertEqual(len(patched), len(source))
        self.assertEqual(patched[-6:], bytes((0x98, 0xD1, 0x82, 0, 0x80, 0)))

    def test_rejects_wrong_expected_target(self) -> None:
        with self.assertRaisesRegex(Exception, "expected 617/0"):
            patch_transition(_script_with_transition(618, 0), 0, 617, 0, 721, 0)


if __name__ == "__main__":
    unittest.main()
