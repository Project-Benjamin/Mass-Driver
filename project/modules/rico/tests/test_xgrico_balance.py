from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

import hashlib
from pathlib import Path
import struct
import unittest

from tools import xgbattle_weight as battle_weight
from tools import xgrico_balance as balance
from tools.build_rico_arc import DiscReader
from tools.migrate_duckstation_disc_state import (
    DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    _Zstd,
)
from work.read_duckstation_runtime import RAM_SIZE, _psx_ram_offset


ROOT = REPOSITORY_ROOT
NORMALIZED_STATE = ROOT / "work" / "standalone_bootstrap" / "2595.bin"
TITLE_OVERLAY = ROOT / "work" / "rico_arc_audit" / "disc1" / "2599.bin"
CLEAN_DISC_1 = ROOT / "Xenogears (Disc 1).bin"
CRASH_STATE = ROOT / "emulator_data" / "SLUS-00664_1.bak"
ZSTD_DLL = ROOT / "work" / "duckstation" / "zstd.dll"
CRASH_STATE_SHA256 = (
    "aade12257284352741fbc7e6f3cfd25c2434b846ab0fd1898cca65e22249dc7f"
)
CRASH_PAYLOAD_SHA256 = (
    "c62f6386a369495c26b7cdfbc7b3738d6c5f65a16debd92cdab5f19c191b4692"
)
# Exact 0x256D0..0x2571F windows from the pre-crash overlay and the user's
# crashing Slot 1 backup.  Their first differing byte pins the allocator's
# observed lower boundary without requiring the mutable savestate in CI.
PRECRASH_WEIGHT_WINDOW = bytes.fromhex(
    "56008390000000000b00682c0a000011000000001f80083c14a7082521400301"
    "00000891000000002b180201"
    "020060100000000021100001780082a00800e0030000000013191416125e1e10"
    "0d141e00"
)
CRASH_RUNTIME_WEIGHT_WINDOW = bytes.fromhex(
    "56008390000000000b00682c0a000011000000001f80083c14a7082521400301"
    "00000891000000002b180201"
    "0b0000000b000000000000002e0000000000000002000000e3191416125e1e10"
    "0d141e00"
)


class WeightProfileTests(unittest.TestCase):
    def test_profiles_cover_every_player_form_and_requested_bounds(self) -> None:
        self.assertEqual(
            tuple(profile.character_id for profile in balance.WEIGHT_PROFILES),
            tuple(range(11)),
        )
        profiles = {profile.name: profile for profile in balance.WEIGHT_PROFILES}
        self.assertEqual(
            (
                profiles["Fei"].minimum_hundredths_lb,
                profiles["Fei"].default_hundredths_lb,
                profiles["Fei"].maximum_hundredths_lb,
            ),
            (14_520, 16_720, 18_700),
        )
        self.assertEqual(
            (
                profiles["Elly"].minimum_hundredths_lb,
                profiles["Elly"].default_hundredths_lb,
                profiles["Elly"].maximum_hundredths_lb,
            ),
            (9_460, 11_660, 14_960),
        )
        self.assertEqual(
            (
                profiles["Rico"].minimum_hundredths_lb,
                profiles["Rico"].default_hundredths_lb,
                profiles["Rico"].maximum_hundredths_lb,
            ),
            (21_120, 35_200, 41_800),
        )

    def test_every_range_produces_the_intended_damage_and_turn_tradeoff(self) -> None:
        for profile in balance.WEIGHT_PROFILES:
            with self.subTest(character=profile.name):
                weights = (
                    profile.minimum_hundredths_lb,
                    profile.default_hundredths_lb,
                    profile.maximum_hundredths_lb,
                )
                attacks = [
                    battle_weight.scale_physical_attack(100, value)
                    for value in weights
                ]
                atb_ticks = [
                    battle_weight.adjust_atb_ticks(80, value)
                    for value in weights
                ]
                self.assertEqual(attacks, sorted(attacks))
                self.assertEqual(atb_ticks, sorted(atb_ticks))
                self.assertLess(attacks[0], attacks[-1])
                self.assertLess(atb_ticks[0], atb_ticks[-1])

    def test_mutable_clamp_reaches_but_never_crosses_each_maximum(self) -> None:
        for profile in balance.WEIGHT_PROFILES:
            with self.subTest(character=profile.name):
                self.assertEqual(
                    balance.clamp_mutable_weight(
                        profile.character_id,
                        profile.mutable_cap,
                    ),
                    profile.mutable_cap,
                )
                self.assertEqual(
                    balance.clamp_mutable_weight(profile.character_id, 0xFF),
                    profile.mutable_cap,
                )
                total = profile.minimum_native + balance.clamp_mutable_weight(
                    profile.character_id,
                    0xFF,
                )
                self.assertEqual(total, profile.maximum_native)


class InitialStateBalanceTests(unittest.TestCase):
    def test_young_rico_equipment_and_hover_text_contract_is_exact(self) -> None:
        expected_names = {
            0x90: "Toy Gear",
            0x91: "Old Blanket",
            0x92: "Wooden Medal",
        }
        expected_descriptions = {
            0x90: "Rico's favorite toy",
            0x91: "Mended many times by Anne",
            0x92: "A make-believe arena prize",
        }
        self.assertEqual(balance.YOUNG_RICO_ACCESSORIES, (0x90, 0x91, 0x92))
        self.assertEqual(balance.YOUNG_RICO_EQUIPMENT_NAMES, expected_names)
        self.assertEqual(
            balance.YOUNG_RICO_EQUIPMENT_DESCRIPTIONS,
            expected_descriptions,
        )
        for item_id in balance.YOUNG_RICO_ACCESSORIES:
            with self.subTest(item_id=hex(item_id)):
                name = expected_names[item_id]
                description = expected_descriptions[item_id]
                self.assertLessEqual(len(name), 13)
                self.assertLessEqual(len(description), 30)
                self.assertTrue(
                    all(character in balance.PLAIN_ENCODE for character in name)
                )
                self.assertTrue(
                    all(character in balance.PLAIN_ENCODE for character in description)
                )
                self.assertLessEqual(len(description) * 2, 0xFF)

    def test_initial_state_installs_weights_rico_stats_and_abilities(self) -> None:
        state = balance.apply_initial_character_balance(NORMALIZED_STATE.read_bytes())
        for profile in balance.WEIGHT_PROFILES:
            with self.subTest(character=profile.name):
                record = (
                    balance.PARTY_RECORD_BASE
                    + profile.character_id * balance.PARTY_RECORD_SIZE
                )
                self.assertEqual(
                    state[
                        record + balance.WEIGHT_FIXED_OFFSET:
                        record + balance.WEIGHT_TENTHS_OFFSET + 1
                    ],
                    bytes((profile.minimum_native, profile.initial_mutable, 0)),
                )

        rico = balance.PARTY_RECORD_BASE + balance.RICO_ID * balance.PARTY_RECORD_SIZE
        self.assertEqual(state[rico + balance.ATTACK_OFFSET], 90)
        self.assertEqual(state[rico + balance.DEFENSE_OFFSET], 80)
        self.assertEqual(
            tuple(
                state[
                    rico + balance.FIRST_ACCESSORY_OFFSET :
                    rico + balance.FIRST_ACCESSORY_OFFSET + 3
                ]
            ),
            balance.RICO_ACCESSORIES,
        )
        self.assertNotIn(balance.MEMENTO_ITEM_ID, balance.RICO_ACCESSORIES)
        self.assertEqual(
            struct.unpack_from("<HHH", state, balance.RICO_ABILITY_RECORD),
            (0xFFC0, 0xF000, 0x1FF8),
        )

    def test_anthology_child_profile_is_isolated_from_adult_rico(self) -> None:
        adult = balance.apply_initial_character_balance(NORMALIZED_STATE.read_bytes())
        state = balance.apply_young_rico_anthology_profile(adult)
        child = (
            balance.PARTY_RECORD_BASE
            + balance.YOUNG_RICO_ID * balance.PARTY_RECORD_SIZE
        )
        rico = balance.PARTY_RECORD_BASE + balance.RICO_ID * balance.PARTY_RECORD_SIZE
        self.assertEqual(
            state[
                balance.YOUNG_RICO_NAME_OFFSET:
                balance.YOUNG_RICO_NAME_OFFSET + len(balance.YOUNG_RICO_NAME_CELL)
            ],
            balance.YOUNG_RICO_NAME_CELL,
        )
        self.assertEqual(state[child + balance.CHARACTER_ID_OFFSET], 10)
        self.assertEqual(
            struct.unpack_from("<HHHH", state, child + 0x4C),
            (50, 50, 10, 10),
        )
        self.assertEqual(
            state[child + balance.ATTACK_OFFSET:child + balance.ATTACK_OFFSET + 8],
            balance.YOUNG_RICO_STATS,
        )
        self.assertEqual(state[child + 0x62:child + 0x64], b"\x01\x01")
        self.assertEqual(state[child + 0x6A], 0)
        self.assertEqual(
            tuple(
                state[
                    child + balance.FIRST_ACCESSORY_OFFSET:
                    child + balance.FIRST_ACCESSORY_OFFSET + 3
                ]
            ),
            (0x90, 0x91, 0x92),
        )
        self.assertEqual(
            tuple(
                state[
                    child + balance.WEIGHT_FIXED_OFFSET:
                    child + balance.WEIGHT_TENTHS_OFFSET + 1
                ]
            ),
            balance.YOUNG_RICO_WEIGHT,
        )
        self.assertEqual(state[child + 0xA0], balance.YOUNG_RICO_NO_GEAR)
        self.assertEqual(state[0x1800:0x1820], bytes(0x20))
        self.assertEqual(
            state[
                rico + balance.FIRST_ACCESSORY_OFFSET:
                rico + balance.FIRST_ACCESSORY_OFFSET + 3
            ],
            bytes(balance.RICO_ACCESSORIES),
        )


class WeightMutationOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.retail = TITLE_OVERLAY.read_bytes()
        cls.patched = balance.patch_weight_mutation_overlay(cls.retail)

    def test_helper_has_load_delays_exact_caps_and_safe_branches(self) -> None:
        words = balance.WEIGHT_CLAMP_HELPER_WORDS
        self.assertEqual(
            words,
            (
                0x90830056,
                0x3C08801F,
                0x2508A6F0,
                0x01034021,
                0x91080000,
                0,
                0x03E00008,
                0,
            ),
        )
        self.assertEqual(
            balance.WEIGHT_GAIN_CAP_PATCHED_WORDS,
            (
                0x0102182B,
                0x10600011,
                0xA0820078,
                0x01001021,
                0x08078D44,
                0xA0820078,
                0,
            ),
        )
        helper_start = balance.WEIGHT_CLAMP_CAVE_OFFSET
        table_start = helper_start + len(words) * 4
        self.assertEqual(
            self.patched[table_start:table_start + 11],
            balance.MUTABLE_WEIGHT_CAPS,
        )
        self.assertEqual(balance.WEIGHT_CLAMP_CAVE_END, 0x256FC)
        self.assertLessEqual(
            helper_start + len(balance.WEIGHT_CLAMP_HELPER),
            balance.WEIGHT_CLAMP_CAVE_END,
        )

    def test_helpers_stop_before_pinned_slot_one_allocator_boundary(self) -> None:
        first_runtime_write = next(
            index
            for index, (before, after) in enumerate(
                zip(
                    PRECRASH_WEIGHT_WINDOW,
                    CRASH_RUNTIME_WEIGHT_WINDOW,
                    strict=True,
                )
            )
            if before != after
        )
        boundary = balance.WEIGHT_CLAMP_CAVE_OFFSET + first_runtime_write
        self.assertEqual(first_runtime_write, 0x2C)
        self.assertEqual(boundary, 0x256FC)
        self.assertEqual(balance.WEIGHT_CLAMP_CAVE_END, boundary)
        self.assertEqual(self.patched[boundary:], self.retail[boundary:])
        self.assertLess(balance.GEAR_MENU_GRAY_HELPER_END, boundary)

    def test_pinned_crash_window_matches_the_archived_slot_one(self) -> None:
        if not CRASH_STATE.is_file() or not ZSTD_DLL.is_file():
            raise unittest.SkipTest("Archived crashing Slot 1 is unavailable")
        state = CRASH_STATE.read_bytes()
        if hashlib.sha256(state).hexdigest() != CRASH_STATE_SHA256:
            raise unittest.SkipTest("Slot 1 backup is no longer the archived crash")
        compression_type, compressed_size, _payload_size, frame_offset = (
            struct.unpack_from(
                "<4I", state, DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET
            )
        )
        self.assertEqual(compression_type, 2)
        payload = _Zstd(ZSTD_DLL).decompress(
            state[frame_offset:frame_offset + compressed_size]
        )
        self.assertEqual(
            hashlib.sha256(payload).hexdigest(), CRASH_PAYLOAD_SHA256
        )
        ram_offset = _psx_ram_offset(payload)
        self.assertEqual(ram_offset, 0x1A62)
        ram = payload[ram_offset:ram_offset + RAM_SIZE]
        overlay = ram[0x1C5000:0x1C5000 + balance.TITLE_OVERLAY_SIZE]
        self.assertEqual(
            overlay[0x256D0:0x25720], CRASH_RUNTIME_WEIGHT_WINDOW
        )
        self.assertEqual(overlay[0x254B8:0x254DC], bytes(0x24))
        # The serialized CPU is stopped in the BIOS exception handler after
        # executing allocator-corrupted overlay code.
        self.assertEqual(struct.unpack_from("<I", payload, 0xC6)[0], 0xBFC0D8E0)
        self.assertEqual(struct.unpack_from("<I", payload, 0xDA)[0], 0x00001013)
        self.assertEqual(struct.unpack_from("<I", payload, 0xE6)[0], 0x801EA910)
        self.assertEqual(struct.unpack_from("<I", payload, 0xF2)[0], 0x00000414)

    def test_gear_row_helper_is_guarded_and_tail_calls_retail_draw(self) -> None:
        self.assertEqual(
            balance.GEAR_MENU_GRAY_HELPER_WORDS,
            (
                0x9083033B,
                0x8C820350,
                0x14600004,
                0x3C032C40,
                0x34634040,
                0xAC4300A4,
                0xAC4300CC,
                0x08071EFD,
                0,
            ),
        )
        self.assertEqual(
            struct.unpack("<5I", balance.GEAR_MENU_DRAW_HOOK_PATCHED),
            (
                0x3C108006,
                0x8E1025A0,
                0x0C07A92E,
                0x02002021,
                0x02002021,
            ),
        )
        self.assertEqual(
            self.patched[
                balance.GEAR_MENU_DRAW_HOOK_OFFSET:
                balance.GEAR_MENU_DRAW_HOOK_END
            ],
            balance.GEAR_MENU_DRAW_HOOK_PATCHED,
        )
        helper_end = (
            balance.GEAR_MENU_GRAY_HELPER_OFFSET
            + len(balance.GEAR_MENU_GRAY_HELPER)
        )
        self.assertEqual(
            self.patched[balance.GEAR_MENU_GRAY_HELPER_OFFSET:helper_end],
            balance.GEAR_MENU_GRAY_HELPER,
        )
        self.assertEqual(balance.GEAR_MENU_GRAY_HELPER_OFFSET, 0x254B8)
        self.assertLessEqual(helper_end, balance.GEAR_MENU_GRAY_HELPER_END)
        # Native input blocking remains the authority for whether Gear opens.
        self.assertEqual(
            self.retail[
                balance.GEAR_MENU_SELECTION_GUARD_OFFSET:
                balance.GEAR_MENU_SELECTION_GUARD_END
            ],
            balance.GEAR_MENU_SELECTION_GUARD,
        )
        self.assertEqual(
            self.patched[
                balance.GEAR_MENU_SELECTION_GUARD_OFFSET:
                balance.GEAR_MENU_SELECTION_GUARD_END
            ],
            balance.GEAR_MENU_SELECTION_GUARD,
        )

    def test_patch_changes_only_audited_hooks_and_zero_cave(self) -> None:
        changed = {
            index
            for index, (before, after) in enumerate(
                zip(self.retail, self.patched, strict=True)
            )
            if before != after
        }
        allowed = set(
            range(balance.WEIGHT_GAIN_HOOK_OFFSET, balance.WEIGHT_GAIN_HOOK_END)
        ) | set(
            range(balance.WEIGHT_GAIN_CAP_OFFSET, balance.WEIGHT_GAIN_CAP_END)
        ) | set(
            range(
                balance.WEIGHT_CLAMP_CAVE_OFFSET,
                balance.WEIGHT_CLAMP_CAVE_OFFSET
                + len(balance.WEIGHT_CLAMP_HELPER),
            )
        ) | set(
            range(
                balance.GEAR_MENU_DRAW_HOOK_OFFSET,
                balance.GEAR_MENU_DRAW_HOOK_END,
            )
        ) | set(
            range(
                balance.GEAR_MENU_GRAY_HELPER_OFFSET,
                balance.GEAR_MENU_GRAY_HELPER_OFFSET
                + len(balance.GEAR_MENU_GRAY_HELPER),
            )
        )
        self.assertTrue(changed <= allowed)
        # The original global cap is replaced in place; the loss-to-zero path
        # remains retail-exact.
        self.assertEqual(
            self.patched[
                balance.WEIGHT_GAIN_CAP_OFFSET:balance.WEIGHT_GAIN_CAP_END
            ],
            balance.WEIGHT_GAIN_CAP_PATCHED,
        )
        self.assertEqual(
            self.patched[0x1E4E0:0x1E510],
            self.retail[0x1E4E0:0x1E510],
        )
        self.assertEqual(
            hashlib.sha256(self.patched).hexdigest(),
            balance.TITLE_OVERLAY_BALANCED_SHA256,
        )

    def test_disc2_gate_composes_without_touching_weight_logic(self) -> None:
        gated = bytearray(self.retail)
        gated[0x13B8:0x13BC] = bytes.fromhex("01 00 04 34")
        self.assertEqual(
            hashlib.sha256(gated).hexdigest(),
            balance.TITLE_OVERLAY_DISC2_GATE_SHA256,
        )
        combined = balance.patch_weight_mutation_overlay(bytes(gated))
        self.assertEqual(
            hashlib.sha256(combined).hexdigest(),
            balance.TITLE_OVERLAY_DISC2_BALANCED_SHA256,
        )


@unittest.skipUnless(CLEAN_DISC_1.is_file(), "clean Disc 1 fixture is unavailable")
class CleanDiscResourceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.reader = DiscReader(CLEAN_DISC_1, 1)

    def test_all_three_shared_menu_overlays_receive_the_same_patch(self) -> None:
        results = []
        for canonical_id in (2597, 2599, 2603):
            with self.subTest(canonical_id=canonical_id):
                source = self.reader.canonical(canonical_id)
                self.assertEqual(
                    hashlib.sha256(source).hexdigest(),
                    balance.TITLE_OVERLAY_RETAIL_SHA256,
                )
                result = balance.patch_weight_mutation_overlay(source)
                self.assertEqual(
                    hashlib.sha256(result).hexdigest(),
                    balance.TITLE_OVERLAY_BALANCED_SHA256,
                )
                results.append(result)
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])

    def test_battle_resource_repack_has_exact_clean_hash_and_round_trip(self) -> None:
        result = balance.patch_battle_weight_resource(cls_source := self.reader.canonical(38))
        self.assertNotEqual(result, cls_source)
        self.assertEqual(len(result), balance.BATTLE_RESOURCE_PATCHED_SIZE)
        self.assertEqual(
            hashlib.sha256(result).hexdigest(),
            balance.BATTLE_RESOURCE_PATCHED_SHA256,
        )
        decoded, consumed = balance.decode_lzss_complete_groups(result)
        self.assertLessEqual(consumed, len(result))
        self.assertEqual(
            hashlib.sha256(decoded).hexdigest(),
            battle_weight.BATTLE_OVERLAY_CLEAN_DECODED_PATCHED_SHA256,
        )

    def test_memento_replaces_ether_with_attack_defense_and_agility(self) -> None:
        result = balance.patch_memento_system_data(self.reader.canonical(2594))
        self.assertEqual(len(result), balance.SYSTEM_DATA_PATCHED_SIZE)
        self.assertEqual(
            hashlib.sha256(result).hexdigest(),
            balance.SYSTEM_DATA_PATCHED_SHA256,
        )
        entries, offsets = balance._archive_entries(
            result,
            expected_count=balance.SYSTEM_DATA_ARCHIVE_COUNT,
        )
        item_data, _ = balance.decode_lzss_complete_groups(
            entries[balance.MEMENTO_ITEM_ARCHIVE_ENTRY]
        )
        row = balance.MEMENTO_ITEM_RECORD_OFFSET
        self.assertEqual(
            struct.unpack_from("<H", item_data, row + 0x0A)[0],
            0xE006,
        )
        self.assertEqual(struct.unpack_from("<H", item_data, row + 0x0A)[0] & 0x1800, 0)
        for item_id in balance.YOUNG_RICO_ACCESSORIES:
            with self.subTest(item_id=hex(item_id)):
                row = 2 + item_id * balance.MEMENTO_ITEM_RECORD_SIZE
                expected = bytearray.fromhex(
                    "00 00 00 00 22 00 00 00 00 00 00 00 00 00 FF 07"
                )
                expected[5] = item_id
                self.assertEqual(
                    item_data[row:row + balance.MEMENTO_ITEM_RECORD_SIZE],
                    bytes(expected),
                )

        description, _ = balance.decode_lzss_complete_groups(
            result[offsets[balance.MEMENTO_DESCRIPTION_ARCHIVE_ENTRY]:]
        )
        maximum = struct.unpack_from("<I", description, 0)[0]
        pointers = struct.unpack_from(f"<{maximum + 1}H", description, 4)
        start = pointers[balance.MEMENTO_ITEM_ID]
        end = pointers[balance.MEMENTO_ITEM_ID + 1]
        encoded = bytes(
            balance.PLAIN_ENCODE[character]
            for character in balance.MEMENTO_DESCRIPTION
        ) + b"\x00"
        self.assertEqual(description[start:end], encoded)
        for item_id, text in balance.YOUNG_RICO_EQUIPMENT_DESCRIPTIONS.items():
            with self.subTest(item_id=hex(item_id)):
                start = pointers[item_id]
                end = pointers[item_id + 1]
                encoded = bytes(
                    balance.PLAIN_ENCODE[character] for character in text
                ) + b"\x00"
                self.assertEqual(description[start:end], encoded)

    def test_young_rico_equipment_names_are_exact_and_round_trip(self) -> None:
        source = self.reader.canonical(29)
        result = balance.patch_young_rico_equipment_names(source)
        self.assertEqual(
            (len(result), hashlib.sha256(result).hexdigest()),
            (balance.SYSTEM_NAMES_PATCHED_SIZE, balance.SYSTEM_NAMES_PATCHED_SHA256),
        )
        decoded, consumed = balance.decode_lzss_complete_groups(result)
        self.assertLessEqual(consumed, len(result))
        self.assertEqual(
            (len(decoded), hashlib.sha256(decoded).hexdigest()),
            (
                balance.SYSTEM_NAMES_DECODED_PATCHED_SIZE,
                balance.SYSTEM_NAMES_DECODED_PATCHED_SHA256,
            ),
        )
        count = struct.unpack_from("<I", decoded, 0)[0]
        offsets = struct.unpack_from(f"<{count}I", decoded, 4)
        self.assertEqual(count, balance.SYSTEM_NAMES_ARCHIVE_COUNT)
        self.assertTrue(all(offset % 2 == 0 for offset in offsets))
        table_start = offsets[balance.EQUIPMENT_NAMES_ARCHIVE_ENTRY]
        table_end = offsets[balance.EQUIPMENT_NAMES_ARCHIVE_ENTRY + 1]
        table = decoded[table_start:table_end]
        maximum = struct.unpack_from("<I", table, 0)[0]
        pointers = struct.unpack_from(f"<{maximum + 1}H", table, 4)
        dimension_base = 4 + (maximum + 1) * 2
        for item_id, text in balance.YOUNG_RICO_EQUIPMENT_NAMES.items():
            with self.subTest(item_id=hex(item_id)):
                start = pointers[item_id]
                end = pointers[item_id + 1]
                encoded = bytes(
                    balance.PLAIN_ENCODE[character] for character in text
                ) + b"\x00"
                self.assertEqual(table[start:end], encoded)
                self.assertEqual(
                    table[
                        dimension_base + item_id * 2:
                        dimension_base + item_id * 2 + 2
                    ],
                    bytes((len(text) * 2, 1)),
                )


if __name__ == "__main__":
    unittest.main()
