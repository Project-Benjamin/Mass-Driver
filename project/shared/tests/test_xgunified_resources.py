from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import unittest

from tools import build_mass_driver_dungeon as mass_driver
from tools import build_rico_arc as rico
from tools import xgrico_balance as balance
from tools import xgrico_native_title as title
from tools import xgunified_resources as unified
from modules.rico.recruitment import RICO_RECRUITMENT_PROFILE as recruitment
from tools.xgdeathblows import (
    ABILITY_RECORD_BASE,
    ABILITY_RECORD_SIZE,
    DEATHBLOW_PROFILES,
    learned_mask,
)
from tools.xgdialog import PLAIN_ENCODE


ROOT = Path(__file__).resolve().parents[2]
V167_REPLACEMENTS = ROOT / "work" / "mass_driver_v167_stage" / "replacements"
RETAIL_MENU = ROOT / "work" / "title_menu_audit_20260813" / "retail" / "2593.bin"
RICO_DISC_1 = ROOT / "Xenogears (Disc 1).bin"
YOUNG_RICO_TIM = (
    ROOT
    / "modules"
    / "rico"
    / "content"
    / "assets"
    / "young_rico_menu_portrait.tim"
)

V167_NAMES = V167_REPLACEMENTS / "29_video_disk_item_name.bin"
V167_DATA = V167_REPLACEMENTS / "2594_video_disk_description.bin"
V167_MENU = V167_REPLACEMENTS / "2593_menu_shared_mass_driver.bin"
V167_GAMESTATE = V167_REPLACEMENTS / "2595_standalone_gamestate.bin"
V167_BATTLE_ARENA = V167_REPLACEMENTS / "47_normal_combat_balance.bin"
V167_PLAYER_GEAR_STATS = V167_REPLACEMENTS / "2614_normal_combat_balance.bin"
V167_ENEMY_TWO_STATS = V167_REPLACEMENTS / "2622_normal_combat_balance.bin"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _archive_entries(
    data: bytes,
    *,
    expected_count: int,
) -> tuple[bytes, tuple[bytes, ...], tuple[int, ...]]:
    count = struct.unpack_from("<I", data, 0)[0]
    if count != expected_count:
        raise AssertionError(f"archive has {count} entries, expected {expected_count}")
    offsets = struct.unpack_from(f"<{count}I", data, 4)
    entries = tuple(
        data[start : offsets[index + 1] if index + 1 < count else len(data)]
        for index, start in enumerate(offsets)
    )
    return data[: offsets[0]], entries, offsets


def _indexed_string(data: bytes, entry_id: int) -> tuple[bytes, bytes]:
    count = struct.unpack_from("<I", data, 0)[0] + 1
    pointers = struct.unpack_from(f"<{count}H", data, 4)
    pointer_end = 4 + count * 2
    end = pointers[entry_id + 1] if entry_id + 1 < count else len(data)
    dimensions = data[
        pointer_end + entry_id * 2 : pointer_end + entry_id * 2 + 2
    ]
    return data[pointers[entry_id] : end], dimensions


def _encoded_text(value: str) -> bytes:
    return bytes(PLAIN_ENCODE[character] for character in value) + b"\x00"


def _decode_system_archive_entry(
    archive: bytes,
    offsets: tuple[int, ...],
    entry_id: int,
) -> bytes:
    # Retail's complete-group decoder may read harmless bytes after an entry's
    # declared output is complete, so model the canonical archive tail.
    decoded, _consumed = balance.decode_lzss_complete_groups(
        archive[offsets[entry_id] :] + bytes(16)
    )
    return decoded


def _decode_menu_entry(entry: bytes) -> bytes:
    decoded, consumed = title._decode_complete_groups(entry + bytes(16))
    if consumed > len(entry) + 16:
        raise AssertionError("menu decoder consumed beyond its padded entry")
    return decoded


class UnifiedRicoInterludeFieldTests(unittest.TestCase):
    def required_pairs(self):
        from shared.tools import build_combined

        # Hub, seven chapters, three childhood annexes, bedroom, commons,
        # Latina's Bar and D Block street. Retired arena/sewer/intake clones
        # are deliberately absent from this current-release fixture.
        fields = {*range(229, 237), 64, 65, 66, 67, 69, 78, 79}
        return {606 + 2 * field + offset:
                build_combined.UnifiedReplacement(606 + 2 * field + offset,
                                                 "test field pair", "rico_arc", b"native")
                for field in fields for offset in (0, 1)}

    def test_current_field_pairs_accept_retired_clones_absent_without_mutation(self):
        from shared.tools import build_combined

        replacements = self.required_pairs()
        before = dict(replacements)
        build_combined._verify_rico_field_pairs(replacements)
        self.assertEqual(replacements, before)
        for field in (68, 70, 71, 72, 73, 74, 75, 76, 77):
            self.assertNotIn(606 + 2 * field, replacements)

    def test_each_active_bundle_and_graphics_partner_remains_required(self):
        from shared.tools import build_combined

        complete = self.required_pairs()
        for resource in complete:
            with self.subTest(canonical_id=resource):
                incomplete = dict(complete)
                del incomplete[resource]
                with self.assertRaisesRegex(build_combined.UnifiedBuildError,
                                            "missing canonical IDs"):
                    build_combined._verify_rico_field_pairs(incomplete)


class UnifiedResourceCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        paths = (
            V167_NAMES,
            V167_DATA,
            V167_MENU,
            V167_GAMESTATE,
            V167_BATTLE_ARENA,
            V167_PLAYER_GEAR_STATS,
            V167_ENEMY_TWO_STATS,
            RETAIL_MENU,
            RICO_DISC_1,
            YOUNG_RICO_TIM,
        )
        missing = [path for path in paths if not path.is_file()]
        if missing:
            raise AssertionError(
                "Checked unified-resource fixtures are incomplete: "
                + ", ".join(str(path) for path in missing)
            )

        cls.mass_names = V167_NAMES.read_bytes()
        cls.mass_data = V167_DATA.read_bytes()
        cls.mass_menu = V167_MENU.read_bytes()
        cls.mass_state = V167_GAMESTATE.read_bytes()
        cls.mass_battle_arena = V167_BATTLE_ARENA.read_bytes()
        cls.mass_player_gear_stats = V167_PLAYER_GEAR_STATS.read_bytes()
        cls.mass_enemy_two_stats = V167_ENEMY_TWO_STATS.read_bytes()
        cls.retail_menu = RETAIL_MENU.read_bytes()
        cls.young_rico_tim = YOUNG_RICO_TIM.read_bytes()
        rico_reader = rico.DiscReader(RICO_DISC_1, 1)
        cls.rico_battle_arena = rico_reader.canonical(47)
        cls.rico_player_gear_stats = rico_reader.canonical(2614)
        cls.rico_enemy_two_stats = rico_reader.canonical(2622)

        cls.names = unified.merge_system_names(cls.mass_names)
        cls.data = unified.merge_system_data(cls.mass_data)
        cls.menu = unified.merge_menu_archive_with_young_rico(
            cls.retail_menu,
            cls.mass_menu,
            cls.young_rico_tim,
        )
        cls.state = unified.merge_initial_gamestate(cls.mass_state)

    def test_inputs_are_the_checked_retail_and_v167_resources(self) -> None:
        expected = (
            (
                self.mass_names,
                mass_driver.FACILITY_VIDEO_ONLY_SYSTEM_NAMES_PATCHED_SIZE,
                mass_driver.FACILITY_VIDEO_ONLY_SYSTEM_NAMES_PATCHED_SHA256,
            ),
            (
                self.mass_data,
                mass_driver.FACILITY_VIDEO_ONLY_SYSTEM_DATA_PATCHED_SIZE,
                mass_driver.FACILITY_VIDEO_ONLY_SYSTEM_DATA_PATCHED_SHA256,
            ),
            (
                self.mass_menu,
                mass_driver.TITLE_MENU_SHARED_PATCHED_SIZE,
                mass_driver.MENU_SHOP_CATALOG_PATCHED_SHA256,
            ),
            (
                self.mass_state,
                mass_driver.INITIAL_GAMESTATE_SIZE,
                # The composition fixture is the frozen V167 state, whose
                # level-70 test party predates release normalization.
                "af23f2082f42ea7874edf0b97fd720ce04419a7bb52f75081d570b5f4b4e9cc7",
            ),
            (
                self.retail_menu,
                title.TITLE_MENU_SOURCE_SIZE,
                title.TITLE_MENU_SOURCE_SHA256,
            ),
            (
                self.young_rico_tim,
                title.MENU_PORTRAIT_TIM_SIZE,
                title.YOUNG_RICO_PORTRAIT_TIM_SHA256,
            ),
        )
        for data, expected_size, expected_hash in expected:
            with self.subTest(expected_hash=expected_hash):
                self.assertEqual(len(data), expected_size)
                self.assertEqual(_sha256(data), expected_hash)

    def test_video_disk_and_keepsake_names_coexist(self) -> None:
        decoded, consumed = balance.decode_lzss_complete_groups(self.names)
        self.assertLessEqual(consumed, len(self.names))
        _header, entries, _offsets = _archive_entries(
            decoded,
            expected_count=balance.SYSTEM_NAMES_ARCHIVE_COUNT,
        )

        video_name, video_dimensions = _indexed_string(
            entries[mass_driver.FACILITY_VIDEO_ITEM_NAME_ARCHIVE_ENTRY],
            mass_driver.FACILITY_VIDEO_ITEM_ID,
        )
        self.assertEqual(video_name, _encoded_text(mass_driver.FACILITY_VIDEO_ITEM_NAME))
        self.assertEqual(
            video_dimensions,
            bytes((len(mass_driver.FACILITY_VIDEO_ITEM_NAME) * 2, 1)),
        )

        keepsakes = entries[balance.EQUIPMENT_NAMES_ARCHIVE_ENTRY]
        for item_id, value in balance.YOUNG_RICO_EQUIPMENT_NAMES.items():
            with self.subTest(item_id=item_id, value=value):
                text, dimensions = _indexed_string(keepsakes, item_id)
                self.assertEqual(text, _encoded_text(value))
                self.assertEqual(dimensions, bytes((len(value) * 2, 1)))

    def test_video_disk_memento_and_keepsake_descriptions_coexist(self) -> None:
        _header, _entries, offsets = _archive_entries(
            self.data,
            expected_count=balance.SYSTEM_DATA_ARCHIVE_COUNT,
        )
        video_descriptions = _decode_system_archive_entry(
            self.data,
            offsets,
            mass_driver.FACILITY_VIDEO_ITEM_DESCRIPTION_ARCHIVE_ENTRY,
        )
        video_text, _video_dimensions = _indexed_string(
            video_descriptions,
            mass_driver.FACILITY_VIDEO_ITEM_ID,
        )
        self.assertEqual(
            video_text,
            _encoded_text(mass_driver.FACILITY_VIDEO_ITEM_DESCRIPTION),
        )

        equipment_descriptions = _decode_system_archive_entry(
            self.data,
            offsets,
            balance.MEMENTO_DESCRIPTION_ARCHIVE_ENTRY,
        )
        expected = {
            balance.MEMENTO_ITEM_ID: (
                balance.MEMENTO_DESCRIPTION,
                balance.MEMENTO_DESCRIPTION_DIMENSIONS,
            ),
            **{
                item_id: (value, bytes((len(value) * 2, 1)))
                for item_id, value in (
                    balance.YOUNG_RICO_EQUIPMENT_DESCRIPTIONS.items()
                )
            },
        }
        for item_id, (value, dimensions) in expected.items():
            with self.subTest(item_id=item_id, value=value):
                text, actual_dimensions = _indexed_string(
                    equipment_descriptions,
                    item_id,
                )
                self.assertEqual(text, _encoded_text(value))
                self.assertEqual(actual_dimensions, dimensions)

    def test_memento_effect_is_the_only_change_to_its_item_record(self) -> None:
        _source_header, _source_entries, source_offsets = _archive_entries(
            self.mass_data,
            expected_count=balance.SYSTEM_DATA_ARCHIVE_COUNT,
        )
        _result_header, _result_entries, result_offsets = _archive_entries(
            self.data,
            expected_count=balance.SYSTEM_DATA_ARCHIVE_COUNT,
        )
        source_items = _decode_system_archive_entry(
            self.mass_data,
            source_offsets,
            balance.MEMENTO_ITEM_ARCHIVE_ENTRY,
        )
        result_items = _decode_system_archive_entry(
            self.data,
            result_offsets,
            balance.MEMENTO_ITEM_ARCHIVE_ENTRY,
        )
        start = balance.MEMENTO_ITEM_RECORD_OFFSET
        end = start + balance.MEMENTO_ITEM_RECORD_SIZE
        self.assertEqual(source_items[start:end], balance.MEMENTO_ITEM_RETAIL_RECORD)

        expected_record = bytearray(balance.MEMENTO_ITEM_RETAIL_RECORD)
        struct.pack_into(
            "<H",
            expected_record,
            0x0A,
            balance.MEMENTO_ITEM_EFFECT_FLAGS,
        )
        expected_items = bytearray(source_items)
        expected_items[start:end] = expected_record
        self.assertEqual(result_items, bytes(expected_items))
        self.assertEqual(
            struct.unpack_from("<H", result_items, start + 0x0A)[0],
            0xE006,
        )

    def test_menu_uses_native_title_mass_shops_and_only_rico_portrait(self) -> None:
        retail_header, retail_entries, _retail_offsets = _archive_entries(
            self.retail_menu,
            expected_count=title.ARCHIVE_ENTRY_COUNT,
        )
        _mass_header, mass_entries, _mass_offsets = _archive_entries(
            self.mass_menu,
            expected_count=title.ARCHIVE_ENTRY_COUNT,
        )
        result_header, result_entries, _result_offsets = _archive_entries(
            self.menu,
            expected_count=title.ARCHIVE_ENTRY_COUNT,
        )

        # The offset table necessarily moves when entries 2 and 4 recompress;
        # the archive count and fixed first-entry boundary remain native.
        self.assertEqual(result_header[:4], retail_header[:4])
        self.assertEqual(len(result_header), len(retail_header))
        for entry_id in (0, 1, 3, 5):
            with self.subTest(entry_id=entry_id, owner="retail"):
                self.assertEqual(result_entries[entry_id], retail_entries[entry_id])
        for entry_id in (
            mass_driver.ITEM_SHOP_ARCHIVE_ENTRY,
            mass_driver.GEAR_SHOP_ARCHIVE_ENTRY,
        ):
            with self.subTest(entry_id=entry_id, owner="mass-driver"):
                self.assertEqual(result_entries[entry_id], mass_entries[entry_id])

        # Entry 2 may be recompressed to recover sector space, but its decoded
        # New Game / Continue / Sound glyph records must remain retail-native.
        self.assertEqual(
            _decode_menu_entry(
                result_entries[mass_driver.TITLE_MENU_FONT_ARCHIVE_ENTRY]
            ),
            _decode_menu_entry(
                retail_entries[mass_driver.TITLE_MENU_FONT_ARCHIVE_ENTRY]
            ),
        )

        portrait_id = title.MENU_PORTRAIT_ENTRY
        before_portraits = _decode_menu_entry(retail_entries[portrait_id])
        after_portraits = _decode_menu_entry(result_entries[portrait_id])
        start = title.YOUNG_RICO_PORTRAIT_OFFSET
        end = start + title.MENU_PORTRAIT_TIM_SIZE
        expected_portraits = bytearray(before_portraits)
        expected_portraits[start:end] = self.young_rico_tim
        self.assertEqual(after_portraits, bytes(expected_portraits))
        self.assertEqual(after_portraits[start:end], self.young_rico_tim)
        self.assertNotEqual(before_portraits[start:end], self.young_rico_tim)
        self.assertEqual(_sha256(after_portraits[start:end]), title.YOUNG_RICO_PORTRAIT_TIM_SHA256)

        self.assertLessEqual(len(self.menu), title.TITLE_MENU_SECTOR_BUDGET)

    def test_all_battle_forms_have_every_deathblow_before_young_rico_override(self) -> None:
        for profile in DEATHBLOW_PROFILES:
            if profile.character_id in (balance.YOUNG_RICO_ID, balance.RICO_ID) or not profile.full_mask:
                continue
            with self.subTest(character=profile.character):
                self.assertEqual(
                    learned_mask(self.state, profile.character_id) & profile.full_mask,
                    profile.full_mask,
                )

        young_ability = (
            ABILITY_RECORD_BASE + balance.YOUNG_RICO_ID * ABILITY_RECORD_SIZE
        )
        self.assertEqual(
            self.state[young_ability : young_ability + ABILITY_RECORD_SIZE],
            bytes(ABILITY_RECORD_SIZE),
        )

    def test_mass_battle_data_preserves_every_rico_gear_attack_record(self) -> None:
        self.assertEqual(
            {
                chapter_id: rico._battle_configurations(
                    rico._playable_chapter_contract(chapter_id)
                )
                for chapter_id in range(1, 8)
                if rico._battle_configurations(
                    rico._playable_chapter_contract(chapter_id)
                )
            },
            {2: {6: True}, 5: {15: True}, 6: {6: True}},
        )
        self.assertEqual(
            rico.NORTUNE_CONFIGURATION_6[0x08:0x10],
            bytes((0x82, 0x82)) + bytes((0xFF,)) * 6,
        )
        # Enemy definition 2's stats are already byte-identical.  Its paired
        # model/animation canonical 2623 remains Rico-owned in the unified map.
        self.assertEqual(self.mass_enemy_two_stats, self.rico_enemy_two_stats)

        _rico_header, rico_entries, _rico_offsets = _archive_entries(
            self.rico_player_gear_stats,
            expected_count=38,
        )
        _mass_header, mass_entries, _mass_offsets = _archive_entries(
            self.mass_player_gear_stats,
            expected_count=38,
        )
        attack_record_region = 41 * mass_driver.EL_REGULUS_ATTACK_RECORD_SIZE
        gear_entries = {
            11: 27,  # Weltall
            15: 31,  # Brigandier
            17: 33,  # Stier
        }
        for gear_id, entry_id in gear_entries.items():
            with self.subTest(gear_id=gear_id, entry_id=entry_id):
                rico_table, _ = balance.decode_lzss_complete_groups(
                    rico_entries[entry_id] + bytes(16)
                )
                mass_table, _ = balance.decode_lzss_complete_groups(
                    mass_entries[entry_id] + bytes(16)
                )
                self.assertGreaterEqual(len(rico_table), attack_record_region)
                self.assertGreaterEqual(len(mass_table), attack_record_region)
                self.assertEqual(
                    mass_table[:attack_record_region],
                    rico_table[:attack_record_region],
                )

        # Canonical 47 is a global battle payload rather than a formation-local
        # record.  Its first logical entry is the 70-row localized battle-text
        # table; the second, non-text entry is byte-identical.  Preserve PWE's
        # translated table instead of replacing the complete global resource.
        rico_arena, _ = balance.decode_lzss_complete_groups(
            self.rico_battle_arena + bytes(16)
        )
        mass_arena, _ = balance.decode_lzss_complete_groups(
            self.mass_battle_arena + bytes(16)
        )
        rico_boundaries = struct.unpack_from("<3I", rico_arena, 4)
        mass_boundaries = struct.unpack_from("<3I", mass_arena, 4)
        self.assertEqual(
            struct.unpack_from("<4I", mass_arena),
            struct.unpack_from("<4I", rico_arena),
        )
        self.assertEqual(mass_boundaries, (0x10, 0x1D40, 0x2360))
        self.assertEqual(mass_boundaries, rico_boundaries)
        text_start, runtime_start, runtime_end = mass_boundaries
        self.assertEqual(struct.unpack_from("<I", mass_arena, text_start)[0], 0x45)
        self.assertNotEqual(
            mass_arena[text_start:runtime_start],
            rico_arena[text_start:runtime_start],
        )
        self.assertEqual(
            mass_arena[runtime_start:runtime_end],
            rico_arena[runtime_start:runtime_end],
        )

    def test_rico_roster_is_added_without_changing_other_module_starts(self) -> None:
        source_membership = struct.unpack_from("<H", self.mass_state, 0x1D30)[0]
        result_membership = struct.unpack_from("<H", self.state, 0x1D30)[0]
        required_ids = (0, 2, 3, balance.RICO_ID, balance.YOUNG_RICO_ID)
        required_mask = sum(1 << character_id for character_id in required_ids)
        self.assertEqual(result_membership, source_membership | required_mask)
        for character_id in required_ids:
            with self.subTest(character_id=character_id):
                self.assertTrue(result_membership & (1 << character_id))

        # Field 63 owns the live-party/frame reset for each module.  Preserve
        # its neutral source state and each adult's module-specific level.
        self.assertEqual(self.state[0x1D32:0x1D37], self.mass_state[0x1D32:0x1D37])
        for character_id in range(balance.YOUNG_RICO_ID):
            record = (
                balance.PARTY_RECORD_BASE
                + character_id * balance.PARTY_RECORD_SIZE
            )
            with self.subTest(character_id=character_id, field="level"):
                self.assertEqual(
                    self.state[record + 0x62 : record + 0x64],
                    bytes((recruitment.level,) * 2) if character_id == balance.RICO_ID
                    else self.mass_state[record + 0x62 : record + 0x64],
                )
        young = (
            balance.PARTY_RECORD_BASE
            + balance.YOUNG_RICO_ID * balance.PARTY_RECORD_SIZE
        )
        self.assertEqual(
            self.state[young + 0x62 : young + 0x64],
            bytes((balance.YOUNG_RICO_LEVEL,) * 2),
        )

    def test_young_rico_profile_keeps_adult_rico_without_memento(self) -> None:
        adult = (
            balance.PARTY_RECORD_BASE
            + balance.RICO_ID * balance.PARTY_RECORD_SIZE
        )
        self.assertEqual(
            self.state[adult + balance.CHARACTER_ID_OFFSET],
            balance.RICO_ID,
        )
        self.assertEqual(
            self.state[adult + balance.ATTACK_OFFSET],
            recruitment.stats[0],
        )
        self.assertEqual(
            self.state[adult + balance.DEFENSE_OFFSET],
            recruitment.stats[1],
        )
        self.assertEqual(
            tuple(
                self.state[
                    adult + balance.FIRST_ACCESSORY_OFFSET :
                    adult + balance.FIRST_ACCESSORY_OFFSET + 3
                ]
            ),
            balance.RICO_ACCESSORIES,
        )
        self.assertNotIn(balance.MEMENTO_ITEM_ID, balance.RICO_ACCESSORIES)
        self.assertEqual(
            struct.unpack_from("<HHH", self.state, balance.RICO_ABILITY_RECORD),
            (
                recruitment.on_foot_deathblows,
                recruitment.spirit_commands,
                recruitment.stier_deathblows,
            ),
        )

        young = (
            balance.PARTY_RECORD_BASE
            + balance.YOUNG_RICO_ID * balance.PARTY_RECORD_SIZE
        )
        self.assertEqual(
            self.state[
                balance.YOUNG_RICO_NAME_OFFSET :
                balance.YOUNG_RICO_NAME_OFFSET + len(balance.YOUNG_RICO_NAME_CELL)
            ],
            balance.YOUNG_RICO_NAME_CELL,
        )
        self.assertEqual(
            self.state[young + balance.CHARACTER_ID_OFFSET],
            balance.YOUNG_RICO_ID,
        )
        self.assertEqual(
            struct.unpack_from("<HHHH", self.state, young + 0x4C),
            (
                balance.YOUNG_RICO_HP,
                balance.YOUNG_RICO_HP,
                balance.YOUNG_RICO_MP,
                balance.YOUNG_RICO_MP,
            ),
        )
        self.assertEqual(
            self.state[young + balance.ATTACK_OFFSET : young + balance.ATTACK_OFFSET + 8],
            balance.YOUNG_RICO_STATS,
        )
        self.assertEqual(
            self.state[young + 0x62 : young + 0x64],
            bytes((balance.YOUNG_RICO_LEVEL,) * 2),
        )
        self.assertEqual(self.state[young + 0x6A], 0)
        self.assertEqual(
            self.state[
                young + balance.FIRST_ACCESSORY_OFFSET :
                young + balance.FIRST_ACCESSORY_OFFSET + 3
            ],
            bytes(balance.YOUNG_RICO_ACCESSORIES),
        )
        self.assertEqual(
            self.state[
                young + balance.WEIGHT_FIXED_OFFSET :
                young + balance.WEIGHT_TENTHS_OFFSET + 1
            ],
            bytes(balance.YOUNG_RICO_WEIGHT),
        )
        self.assertEqual(self.state[young + 0xA0], balance.YOUNG_RICO_NO_GEAR)

    def test_elly_remains_on_vierge(self) -> None:
        offset = mass_driver.INITIAL_GAMESTATE_ELLY_GEAR_OFFSET
        self.assertEqual(self.mass_state[offset], mass_driver.VIERGE_GEAR_ID)
        self.assertEqual(self.state[offset], mass_driver.VIERGE_GEAR_ID)
        self.assertEqual(len(self.state), balance.GAMESTATE_SIZE)


if __name__ == "__main__":
    unittest.main()
