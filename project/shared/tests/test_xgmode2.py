from __future__ import annotations

import hashlib
import unittest

from tools.xgmode2 import (
    Mode2PatchError,
    RAW_SECTOR_SIZE,
    regenerate_mode2_form1,
)


def _fixture_sector() -> bytes:
    sector = bytearray(RAW_SECTOR_SIZE)
    sector[:12] = b"\x00" + b"\xFF" * 10 + b"\x00"
    sector[12:16] = bytes((1, 2, 3, 2))
    sector[16:20] = bytes((4, 5, 0, 0))
    sector[20:24] = sector[16:20]
    sector[24 : 24 + 2048] = bytes((index * 37 + 11) & 0xFF for index in range(2048))
    return bytes(sector)


class Mode2Form1Tests(unittest.TestCase):
    def test_edc_and_ecc_match_a_fixed_vector(self) -> None:
        repaired = regenerate_mode2_form1(_fixture_sector())
        self.assertEqual(
            hashlib.sha256(repaired).hexdigest(),
            "52a214b45987f10665b64f74ade965746441718cae43160d1835de178f7976fa",
        )
        self.assertEqual(repaired[0x818:0x81C], bytes.fromhex("ca 39 9c 7e"))
        self.assertEqual(regenerate_mode2_form1(repaired), repaired)

    def test_user_data_change_regenerates_both_parity_layers(self) -> None:
        repaired = bytearray(regenerate_mode2_form1(_fixture_sector()))
        repaired[24 + 0x130] = 3
        changed = regenerate_mode2_form1(bytes(repaired))
        self.assertEqual(
            hashlib.sha256(changed).hexdigest(),
            "2ed7cd81a5466e3377f7f4a5038f1ca5a6b9255b2af179cc1c62d33d6011dada",
        )

    def test_non_form1_sectors_fail_closed(self) -> None:
        sector = bytearray(_fixture_sector())
        sector[18] = 0x20
        sector[22] = 0x20
        with self.assertRaisesRegex(Mode2PatchError, "MODE2/Form1"):
            regenerate_mode2_form1(bytes(sector))


if __name__ == "__main__":
    unittest.main()
