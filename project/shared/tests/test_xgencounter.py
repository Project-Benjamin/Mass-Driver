from __future__ import annotations

import unittest

from tools.xgencounter import (
    EMPTY_ENEMY_ID,
    EMPTY_POSITION,
    ENCOUNTER_COMPONENT_SIZE,
    EncounterFormatError,
    EncounterTable,
)


def _empty_table() -> bytes:
    return bytes([0xFF]) * 0x200 + bytes(range(16))


class EncounterTableTests(unittest.TestCase):
    def test_parses_formations_and_weights(self) -> None:
        table = EncounterTable(_empty_table())

        self.assertEqual(len(table.formation(0)), 0x20)
        self.assertEqual(table.get_enemy_id(0, 0), EMPTY_ENEMY_ID)
        self.assertEqual(table.get_enemy_position(0, 0), EMPTY_POSITION)
        self.assertEqual(table.weights, tuple(range(16)))
        self.assertEqual(len(table.to_bytes()), ENCOUNTER_COMPONENT_SIZE)

    def test_sets_enemy_and_preserves_unrelated_high_bits(self) -> None:
        table = EncounterTable(_empty_table())
        table.set_enemy(2, 3, 3, 5, is_gear=True)

        table.set_enemy_id(2, 3, 4)
        table.set_enemy_position(2, 3, 6)
        placement = table.get_enemy(2, 3)
        raw = table.formation(2)

        self.assertEqual((placement.enemy_id, placement.position), (4, 6))
        self.assertTrue(placement.is_gear)
        self.assertTrue(placement.position_flag)
        self.assertEqual(raw[0x08 + 3], 0x84)
        self.assertEqual(raw[0x18 + 3], 0x86)

    def test_copies_exact_formation_and_weight_only_when_requested(self) -> None:
        table = EncounterTable(_empty_table())
        table.set_enemy(1, 0, 6, 3, is_gear=False)
        table.set_weight(1, 200)
        original_destination_weight = table.get_weight(4)

        table.copy_formation(1, 4)

        self.assertEqual(table.formation(4), table.formation(1))
        self.assertEqual(table.get_weight(4), original_destination_weight)

        table.copy_formation(1, 5, copy_weight=True)
        self.assertEqual(table.formation(5), table.formation(1))
        self.assertEqual(table.get_weight(5), 200)

    def test_validates_enemy_ids_and_scale_specific_positions(self) -> None:
        table = EncounterTable(_empty_table())

        with self.assertRaisesRegex(EncounterFormatError, "Enemy ID"):
            table.set_enemy(0, 0, 8, 0, is_gear=False)
        with self.assertRaisesRegex(EncounterFormatError, r"character.*0\.\.3"):
            table.set_enemy(0, 0, 1, 4, is_gear=False)
        with self.assertRaisesRegex(EncounterFormatError, r"Gear.*0\.\.7"):
            table.set_enemy(0, 0, 1, 8, is_gear=True)

        table.set_enemy(0, 0, 1, 4, is_gear=True)
        self.assertEqual(table.get_enemy_position(0, 0), 4)

    def test_rejects_bad_component_and_encoded_formation(self) -> None:
        with self.assertRaisesRegex(EncounterFormatError, "exactly 528 bytes"):
            EncounterTable(bytes(527))

        bad_id = bytearray(_empty_table())
        bad_id[0x08] = 8
        bad_id[0x18] = 0
        with self.assertRaisesRegex(EncounterFormatError, "Formation 0.*Enemy ID"):
            EncounterTable(bad_id)

        bad_position = bytearray(_empty_table())
        bad_position[0x08] = 1
        bad_position[0x18] = 4
        with self.assertRaisesRegex(
            EncounterFormatError, r"Formation 0.*character.*0\.\.3"
        ):
            EncounterTable(bad_position)

    def test_rejects_bad_indices_and_weight(self) -> None:
        table = EncounterTable(_empty_table())

        with self.assertRaisesRegex(EncounterFormatError, "Formation index"):
            table.formation(16)
        with self.assertRaisesRegex(EncounterFormatError, "Enemy slot"):
            table.get_enemy(0, 8)
        with self.assertRaisesRegex(EncounterFormatError, r"0\.\.255"):
            table.set_weight(0, 256)


if __name__ == "__main__":
    unittest.main()
