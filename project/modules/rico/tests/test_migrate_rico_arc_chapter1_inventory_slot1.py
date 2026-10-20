from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

import hashlib
from pathlib import Path
import struct
import unittest

from tools import xgrico_balance as balance
from tools.migrate_duckstation_disc_state import (
    DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
    DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    _Zstd,
    _archive_table,
)
from tools.migrate_rico_arc_chapter1_inventory_slot1 import (
    ACCESSORY_ID_OFFSET,
    ACCESSORY_QUANTITY_OFFSET,
    ARCHIVE_TABLE_DIFFS,
    ARCHIVE_TABLE_PAYLOAD_OFFSET,
    ARCHIVE_TABLE_SIZE,
    DEFAULT_ZSTD,
    EXPECTED_REPAIRED_PAYLOAD_SHA256,
    EXPECTED_REPAIRED_STATE_SHA256,
    EXPECTED_REPAIRED_STATE_SIZE,
    HISTORICAL_HELPER_RAM_SPAN,
    RESIDENT_GEAR_HOOK_RAM_OFFSET,
    SOURCE_ACCESSORY_STACKS,
    SOURCE_ARCHIVE_TABLE_SHA256,
    SOURCE_FRAME_OFFSET,
    SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256,
    SOURCE_RESIDENT_GEAR_HOOK,
    SOURCE_STATE_SHA256,
    SOURCE_VOLATILE_ARCHIVE_BYTE,
    SOURCE_WEAPON_STACKS,
    TARGET_ARCHIVE_TABLE_SHA256,
    TARGET_HELPER_RAM_SPAN,
    TARGET_RESIDENT_ARCHIVE_TABLE_SHA256,
    TARGET_RESIDENT_GEAR_HOOK,
    WEAPON_ID_OFFSET,
    WEAPON_QUANTITY_OFFSET,
    RicoChapterOneStateMigrationError,
    _inventory_patches,
    migrate_state,
)
from work.read_duckstation_runtime import GAME_STATE, _psx_ram_offset


ROOT = REPOSITORY_ROOT
SOURCE_STATE = (
    ROOT / "work" / "rico_arc_menu_crash_slot1_20260902_220235.sav"
)
TARGET_DISC = (
    ROOT
    / "work"
    / "rico_arc_menu_fix_stage"
    / "Xenogears_Rico_Arc_Disc_1.bin"
)


class RicoChapterOneInventorySlotOneMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not all(path.is_file() for path in (SOURCE_STATE, TARGET_DISC, DEFAULT_ZSTD)):
            raise unittest.SkipTest("Audited Rico Slot 1, disc, or zstd is unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        if hashlib.sha256(cls.source).hexdigest() != SOURCE_STATE_SHA256:
            raise unittest.SkipTest("Archived Slot 1 is no longer the audited source")
        cls.zstd = _Zstd(DEFAULT_ZSTD)
        cls.result, cls.report = migrate_state(
            cls.source,
            zstd=cls.zstd,
            new_disc=TARGET_DISC,
        )

        source_frame = struct.unpack_from(
            "<I",
            cls.source,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET + 12,
        )[0]
        result_frame = struct.unpack_from(
            "<I",
            cls.result,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET + 12,
        )[0]
        cls.source_payload = cls.zstd.decompress(cls.source[source_frame:])
        cls.result_payload = cls.zstd.decompress(cls.result[result_frame:])
        cls.ram_offset = _psx_ram_offset(cls.source_payload)

    def test_candidate_has_the_exact_checked_identity(self) -> None:
        self.assertEqual(len(self.result), EXPECTED_REPAIRED_STATE_SIZE)
        self.assertEqual(
            hashlib.sha256(self.result).hexdigest(),
            EXPECTED_REPAIRED_STATE_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(self.result_payload).hexdigest(),
            EXPECTED_REPAIRED_PAYLOAD_SHA256,
        )
        self.assertEqual(self.report["changed_payload_byte_count"], 39)
        self.assertEqual(self.report["inventory_changed_byte_count"], 18)
        self.assertEqual(self.report["gear_hook_changed_byte_count"], 19)
        self.assertEqual(
            self.report["resident_archive_table_changed_byte_count"],
            2,
        )

    def test_only_inventory_slots_and_stable_hook_context_change(self) -> None:
        expected = list(_inventory_patches(ram_offset=self.ram_offset))
        hook_payload_offset = self.ram_offset + RESIDENT_GEAR_HOOK_RAM_OFFSET
        expected.extend(
            (hook_payload_offset + index, old, new)
            for index, (old, new) in enumerate(
                zip(
                    SOURCE_RESIDENT_GEAR_HOOK,
                    TARGET_RESIDENT_GEAR_HOOK,
                    strict=True,
                )
            )
            if old != new
        )
        expected.extend(
            (ARCHIVE_TABLE_PAYLOAD_OFFSET + offset, old, new)
            for offset, old, new in ARCHIVE_TABLE_DIFFS
        )
        actual = [
            (offset, old, new)
            for offset, (old, new) in enumerate(
                zip(self.source_payload, self.result_payload, strict=True)
            )
            if old != new
        ]
        self.assertEqual(actual, sorted(expected))

        source_prefix = bytearray(self.source[:SOURCE_FRAME_OFFSET])
        result_prefix = bytearray(self.result[:SOURCE_FRAME_OFFSET])
        source_prefix[
            DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET:
            DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET + 4
        ] = result_prefix[
            DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET:
            DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET + 4
        ]
        self.assertEqual(source_prefix, result_prefix)

    def test_retail_removal_result_is_exact_for_all_nine_stacks(self) -> None:
        game_state = self.ram_offset + GAME_STATE
        families = (
            (WEAPON_QUANTITY_OFFSET, WEAPON_ID_OFFSET, SOURCE_WEAPON_STACKS),
            (
                ACCESSORY_QUANTITY_OFFSET,
                ACCESSORY_ID_OFFSET,
                SOURCE_ACCESSORY_STACKS,
            ),
        )
        for quantity_base, id_base, stacks in families:
            for slot, item_id, quantity in stacks:
                with self.subTest(slot=slot, item_id=hex(item_id)):
                    self.assertEqual(
                        self.source_payload[game_state + quantity_base + slot],
                        quantity,
                    )
                    self.assertEqual(
                        self.source_payload[game_state + id_base + slot],
                        item_id,
                    )
                    self.assertEqual(
                        self.result_payload[game_state + quantity_base + slot],
                        0,
                    )
                    self.assertEqual(
                        self.result_payload[game_state + id_base + slot],
                        0xFF,
                    )

        child = (
            game_state
            + balance.PARTY_RECORD_BASE
            + balance.YOUNG_RICO_ID * balance.PARTY_RECORD_SIZE
        )
        self.assertEqual(
            self.result_payload[
                child + balance.FIRST_ACCESSORY_OFFSET:
                child + balance.FIRST_ACCESSORY_OFFSET + 3
            ],
            bytes((0x90, 0x91, 0x92)),
        )
        self.assertEqual(self.result_payload[child + 0x6A], 0)
        self.assertEqual(self.result_payload[child + 0xA0], 0xFF)

    def test_hook_targets_rebuilt_code_without_touching_allocator_data(self) -> None:
        hook = self.ram_offset + RESIDENT_GEAR_HOOK_RAM_OFFSET
        self.assertEqual(
            self.source_payload[hook:hook + len(SOURCE_RESIDENT_GEAR_HOOK)],
            SOURCE_RESIDENT_GEAR_HOOK,
        )
        self.assertEqual(
            self.result_payload[hook:hook + len(TARGET_RESIDENT_GEAR_HOOK)],
            TARGET_RESIDENT_GEAR_HOOK,
        )
        for start, end in (TARGET_HELPER_RAM_SPAN, HISTORICAL_HELPER_RAM_SPAN):
            with self.subTest(start=hex(start)):
                source = self.source_payload[
                    self.ram_offset + start:self.ram_offset + end
                ]
                result = self.result_payload[
                    self.ram_offset + start:self.ram_offset + end
                ]
                self.assertNotEqual(source, bytes(len(source)))
                self.assertEqual(result, source)

        self.assertFalse(self.report["resident_helper_patched"])
        self.assertTrue(self.report["menu_reload_from_rebuilt_media_required"])
        self.assertTrue(self.report["resident_fat_migrated"])
        self.assertFalse(
            self.report["media_path_rewrite_required_if_output_path_is_unchanged"]
        )

    def test_resident_fat_is_final_except_for_the_preserved_volatile_byte(self) -> None:
        source_table = self.source_payload[
            ARCHIVE_TABLE_PAYLOAD_OFFSET:
            ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
        ]
        result_table = self.result_payload[
            ARCHIVE_TABLE_PAYLOAD_OFFSET:
            ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
        ]
        self.assertEqual(
            hashlib.sha256(source_table).hexdigest(),
            SOURCE_RESIDENT_ARCHIVE_TABLE_SHA256,
        )
        self.assertEqual(source_table[-1], SOURCE_VOLATILE_ARCHIVE_BYTE)
        normalized_source = source_table[:-1] + b"\x00"
        self.assertEqual(
            hashlib.sha256(normalized_source).hexdigest(),
            SOURCE_ARCHIVE_TABLE_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(result_table).hexdigest(),
            TARGET_RESIDENT_ARCHIVE_TABLE_SHA256,
        )
        media_table = _archive_table(TARGET_DISC)
        self.assertEqual(
            hashlib.sha256(media_table).hexdigest(),
            TARGET_ARCHIVE_TABLE_SHA256,
        )
        self.assertEqual(result_table[:-1], media_table[:-1])
        self.assertEqual(result_table[-1], SOURCE_VOLATILE_ARCHIVE_BYTE)
        self.assertEqual(
            [
                (offset, old, new)
                for offset, (old, new) in enumerate(
                    zip(source_table, result_table, strict=True)
                )
                if old != new
            ],
            list(ARCHIVE_TABLE_DIFFS),
        )
        self.assertEqual(self.report["canonical_2597_sector"], 239_671)
        self.assertEqual(self.report["canonical_2597_size"], 153_864)

    def test_source_drift_is_rejected_before_decompression(self) -> None:
        altered = bytearray(self.source)
        altered[0x20] ^= 1
        with self.assertRaisesRegex(
            RicoChapterOneStateMigrationError,
            "Source Slot 1 identity changed",
        ):
            migrate_state(bytes(altered), zstd=self.zstd, new_disc=TARGET_DISC)

    def test_nonfinal_disc_is_rejected_before_payload_migration(self) -> None:
        wrong_disc = TARGET_DISC.with_name("Xenogears_Rico_Arc_Disc_2.bin")
        if not wrong_disc.is_file():
            self.skipTest("Rico Disc 2 is unavailable")
        with self.assertRaisesRegex(
            RicoChapterOneStateMigrationError,
            "Final Rico Disc 1 identity changed",
        ):
            migrate_state(self.source, zstd=self.zstd, new_disc=wrong_disc)


if __name__ == "__main__":
    unittest.main()
