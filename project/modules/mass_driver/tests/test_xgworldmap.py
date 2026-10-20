from __future__ import annotations

import struct
import unittest

from tools.xgdialog import encode_text
from tools.xgfield import compress_lzss_literals
from tools.xgworldmap import (
    WorldmapData,
    WorldmapFormatError,
    _retail_safe_lzss_edit,
    decompress_worldmap,
    patch_mass_driver_entry,
    patch_worldmap_standalone_controls,
    patch_worldmap_x_interaction,
)
from tools.xgfield import compress_lzss


def _dialogue() -> bytes:
    # Duplicate offsets are legal in retail world-map label tables.
    labels = [
        encode_text(" <Close>"),
        encode_text("Torah's House<Close>"),
        encode_text("Mass Driver<Close>"),
    ]
    count = 22
    header = 4 + count * 4
    payloads = [labels[0]] * count
    payloads[20] = labels[1]
    payloads[21] = labels[2]
    offsets: list[int] = []
    body = bytearray()
    by_value: dict[bytes, int] = {}
    for payload in payloads:
        if payload not in by_value:
            by_value[payload] = header + len(body)
            body.extend(payload)
        offsets.append(by_value[payload])
    result = bytearray(struct.pack("<I", count - 1))
    result.extend(b"".join(struct.pack("<H", value) for value in offsets))
    result.extend(bytes((26, 1)) * count)
    result.extend(body)
    return bytes(result)


def _fixture() -> bytes:
    data = bytearray(0x800)
    root = 0x70
    initial = 0x78
    directory = 0x90
    group0 = 0xA0
    group1 = 0xC0
    # The retail patch relocates the initial-position table into the dead
    # remainder of group 1 after its first duplicate exit.  Leave the same
    # 0x20-byte span available here before group 2 begins.
    group2 = 0xF0
    group3 = 0x100
    dialogue = 0x120
    model_config = 0x300
    text = _dialogue()
    struct.pack_into("<I", data, 0x04, root)
    struct.pack_into("<I", data, 0x10, model_config)
    struct.pack_into("<I", data, 0x1C, dialogue)
    struct.pack_into("<I", data, 0x20, dialogue + len(text))
    struct.pack_into("<II", data, root, initial - root, directory - root)
    struct.pack_into("<hhhh", data, initial, 30352, 4095, 10852, 0)
    struct.pack_into("<hhhh", data, initial + 8, 28162, 20, 23793, 0)
    struct.pack_into("<hhhh", data, initial + 0x10, 0, -1, 0, 0)
    for index, value in enumerate((group0, group1, group2, group3)):
        struct.pack_into("<I", data, directory + 4 * index, value - root)
    struct.pack_into(
        "<hhhhhhhh", data, group0, 27990, 23381, 340, 376, 614, 0, 20, 0
    )
    struct.pack_into("<hhhhhhhh", data, group0 + 0x10, 0, 0, 0, 0, -1, 0, 0, 0)
    struct.pack_into(
        "<hhhhhhhh", data, group1, 27990, 23381, 340, 376, 614, 0, 20, 0
    )
    for value in (group1 + 0x10, group2, group3):
        struct.pack_into("<hhhhhhhh", data, value, 0, 0, 0, 0, -1, 0, 0, 0)
    data[dialogue : dialogue + len(text)] = text
    struct.pack_into("<H", data, model_config, 63)
    struct.pack_into(
        "<HHhhhHHH",
        data,
        model_config + 2 + 51 * 0x10,
        41,
        0,
        28175,
        -166,
        -23606,
        0,
        0,
        0,
    )
    for record in (
        (59, 48, 0, 29991, -344, -16384, 0, 0, 0),
        (60, 49, 0, 28751, -224, -16549, 0, 0, 0),
        (61, 50, 0, 28580, -225, -17425, 0, 0, 0),
        (62, 51, 0, 29283, -222, -17286, 0, 0, 0),
    ):
        index, *values = record
        struct.pack_into(
            "<HHhhhHHH",
            data,
            model_config + 2 + index * 0x10,
            *values,
        )
    return compress_lzss_literals(bytes(data))


def _fixture_with_mass_driver_encounter() -> bytes:
    decoded = bytearray(decompress_worldmap(_fixture()))
    decoded.extend(bytes(0x31000 - len(decoded)))
    decoded[0x30F58 : 0x30F78] = bytes.fromhex(
        "47 00 2C 00 00 00 00 00 "
        "80 FF FF FF FF FF FF FF "
        "00 FF FF FF FF FF FF FF "
        "00 FF FF FF FF FF FF FF"
    )
    return compress_lzss_literals(bytes(decoded))


class WorldmapTests(unittest.TestCase):
    def test_checked_mass_driver_patch(self) -> None:
        source = _fixture()
        retail = WorldmapData(decompress_worldmap(source))
        exit_tuple = lambda value: (
            value.x,
            value.z,
            value.width,
            value.height,
            value.destination_field,
            value.destination_parameter,
            value.label_id,
            value.exit_type,
        )
        retail_groups = tuple(
            tuple(map(exit_tuple, retail.exits(group))) for group in range(4)
        )
        retail_taura_exit = retail.exits(0)[0]
        retail_taura_model = retail.model(51)
        retail_mass_driver = tuple(retail.model(record) for record in range(59, 63))

        result = patch_mass_driver_entry(source)
        parsed = WorldmapData(decompress_worldmap(result.packed))
        self.assertEqual(result.spawn.index, 21)
        self.assertEqual((result.spawn.x, result.spawn.z), (30192, 16396))
        self.assertEqual(result.label, "Mass Driver<Close>")
        self.assertEqual(len(parsed.exits(0)), 2)
        self.assertEqual(len(parsed.exits(1)), 2)
        self.assertEqual(parsed.exits(0)[0].destination_field, 614)
        self.assertEqual(parsed.exits(0)[0].label_id, 20)
        self.assertEqual(parsed.exits(0)[1].destination_field, 720)
        self.assertEqual(parsed.exits(0)[1].destination_parameter, 0)
        self.assertEqual(parsed.exits(0)[1].label_id, 21)
        self.assertEqual(parsed.exits(0)[1].exit_type, 0)
        self.assertEqual(
            tuple(map(exit_tuple, parsed.exits(0))),
            retail_groups[0] + ((29880, 16287, 288, 214, 720, 0, 21, 0),),
        )
        self.assertEqual(
            tuple(map(exit_tuple, parsed.exits(1))),
            tuple(map(exit_tuple, parsed.exits(0))),
        )
        self.assertEqual(tuple(map(exit_tuple, parsed.exits(2))), retail_groups[2])
        self.assertEqual(tuple(map(exit_tuple, parsed.exits(3))), retail_groups[3])
        self.assertEqual(
            (
                parsed.exits(0)[1].x,
                parsed.exits(0)[1].z,
                parsed.exits(0)[1].width,
                parsed.exits(0)[1].height,
            ),
            (29880, 16287, 288, 214),
        )
        self.assertEqual(
            result.spawn.x - (result.new_exit.x + result.new_exit.width),
            24,
        )
        self.assertLessEqual(result.spawn.z, result.new_exit.z + result.new_exit.height)
        self.assertGreaterEqual(result.spawn.z, result.new_exit.z)
        self.assertEqual(
            [(value.x, value.index, value.z) for value in parsed.initial_positions()],
            [
                (30352, 4095, 10852),
                (28162, 20, 23793),
                (30192, 21, 16396),
            ],
        )
        self.assertEqual(result.taura_exit, parsed.exits(0)[0])
        self.assertEqual(result.taura_exit.destination_field, 614)
        self.assertEqual(result.taura_exit.label_id, 20)
        self.assertEqual(result.taura_model, retail_taura_model)
        self.assertEqual(parsed.model(51), retail_taura_model)
        self.assertEqual(result.mass_driver_models, retail_mass_driver)
        self.assertEqual(
            tuple(parsed.model(record) for record in range(59, 63)),
            retail_mass_driver,
        )
        self.assertEqual(
            result.decoded[
                retail_taura_exit.offset : retail_taura_exit.offset + 0x10
            ],
            retail.data[
                retail_taura_exit.offset : retail_taura_exit.offset + 0x10
            ],
        )
        self.assertEqual(
            result.decoded[retail_taura_model.offset : retail_taura_model.offset + 0x10],
            retail.data[retail_taura_model.offset : retail_taura_model.offset + 0x10],
        )

    def test_patch_rejects_an_unexpected_destination(self) -> None:
        decoded = bytearray(decompress_worldmap(_fixture()))
        parsed = WorldmapData(decoded)
        struct.pack_into("<h", decoded, parsed.exits(0)[0].offset + 8, 999)
        with self.assertRaisesRegex(WorldmapFormatError, "not duplicates"):
            patch_mass_driver_entry(compress_lzss_literals(bytes(decoded)))

    def test_patch_rejects_a_spawn_inside_or_far_from_the_entry_apron(self) -> None:
        source = _fixture()
        with self.assertRaisesRegex(WorldmapFormatError, "not just east"):
            patch_mass_driver_entry(source, spawn_x=30168)
        with self.assertRaisesRegex(WorldmapFormatError, "not just east"):
            patch_mass_driver_entry(source, spawn_x=30300)

    def test_mass_driver_encounter_selector_edit_is_checked_and_optional(self) -> None:
        source = _fixture_with_mass_driver_encounter()
        enemy_offset = 0x30F60

        default = patch_mass_driver_entry(source)
        dragon = patch_mass_driver_entry(
            source,
            encounter_enemy_offset=enemy_offset,
        )

        self.assertEqual(default.decoded[enemy_offset], 0x80)
        self.assertEqual(dragon.decoded[enemy_offset], 0x81)
        self.assertEqual(
            [
                offset
                for offset, (before, after) in enumerate(
                    zip(default.decoded, dragon.decoded, strict=True)
                )
                if before != after
            ],
            [enemy_offset],
        )
        self.assertEqual(decompress_worldmap(dragon.packed), dragon.decoded)

        with self.assertRaisesRegex(
            WorldmapFormatError,
            "audited decoded offset 0x30F60",
        ):
            patch_mass_driver_entry(
                source,
                encounter_enemy_offset=enemy_offset + 1,
            )

        with self.assertRaisesRegex(
            WorldmapFormatError,
            "encounter enemy selector is not 0x7F",
        ):
            patch_mass_driver_entry(
                source,
                encounter_enemy_offset=enemy_offset,
                old_encounter_enemy=0x7F,
            )

        changed_context = bytearray(decompress_worldmap(source))
        changed_context[enemy_offset - 8] = 0x46
        with self.assertRaisesRegex(
            WorldmapFormatError,
            "encounter formation context changed",
        ):
            patch_mass_driver_entry(
                compress_lzss_literals(bytes(changed_context)),
                encounter_enemy_offset=enemy_offset,
            )

    def test_retail_safe_edit_realigns_overlapping_compact_islands(self) -> None:
        original = (b"ABCDEFGH" * 96) + (b"01234567" * 64)
        packed = compress_lzss(original)
        edited = bytearray(original)
        for offset, value in ((7, 0x78), (12, 0x79), (20, 0x7A), (516, 0x7B)):
            edited[offset] = value
        result = _retail_safe_lzss_edit(packed, original, bytes(edited))
        self.assertEqual(decompress_worldmap(result), bytes(edited))

    def test_x_interaction_patch_changes_only_the_checked_instruction(self) -> None:
        offset = 0x40
        decoded = bytearray(0x100)
        decoded[offset : offset + 4] = struct.pack("<I", 0x30420020)
        packed = compress_lzss_literals(bytes(decoded))
        result = patch_worldmap_x_interaction(
            packed,
            instruction_offset=offset,
        )
        expected = bytearray(decoded)
        expected[offset : offset + 4] = struct.pack("<I", 0x30420020)
        self.assertEqual(result.decoded, bytes(expected))
        self.assertEqual(decompress_worldmap(result.packed), bytes(expected))

    def test_standalone_controls_enable_x_and_one_encounter_slot(self) -> None:
        interaction_offset = 0x40
        encounter_offset = 0x80
        formation_offset = 0xC0
        decoded = bytearray(0x140)
        decoded[interaction_offset : interaction_offset + 4] = struct.pack(
            "<I", 0x30420020
        )
        decoded[encounter_offset : encounter_offset + 4] = struct.pack(
            "<I", 0x24020000
        )
        decoded[formation_offset : formation_offset + 4] = bytes.fromhex(
            "08 95 29 A0"
        )
        packed = compress_lzss_literals(bytes(decoded))
        result = patch_worldmap_standalone_controls(
            packed,
            instruction_offset=interaction_offset,
            encounter_instruction_offset=encounter_offset,
            formation_instruction_offset=formation_offset,
        )
        expected = bytearray(decoded)
        expected[interaction_offset : interaction_offset + 4] = struct.pack(
            "<I", 0x30420020
        )
        expected[encounter_offset : encounter_offset + 4] = struct.pack(
            "<I", 0x24020001
        )
        expected[formation_offset : formation_offset + 4] = bytes.fromhex(
            "08 95 20 A0"
        )
        self.assertEqual(result.decoded, bytes(expected))
        self.assertEqual(result.new_encounter_slots, 1)
        self.assertEqual(decompress_worldmap(result.packed), bytes(expected))

        with self.assertRaisesRegex(WorldmapFormatError, "between 0 and 16"):
            patch_worldmap_standalone_controls(
                packed,
                instruction_offset=interaction_offset,
                encounter_instruction_offset=encounter_offset,
                formation_instruction_offset=formation_offset,
                new_encounter_slots=17,
            )


if __name__ == "__main__":
    unittest.main()
