from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import tools.build_mass_driver_dungeon as dungeon
import tools.prepare_mass_driver_bootstrap as bootstrap
import tools.xgmode2 as xgmode2


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _form1_sector(user_data: bytes) -> bytes:
    if len(user_data) != 2048:
        raise ValueError("MODE2/Form1 user data must be exactly 2048 bytes")
    sector = bytearray(xgmode2.RAW_SECTOR_SIZE)
    sector[:12] = b"\x00" + b"\xFF" * 10 + b"\x00"
    sector[12:16] = bytes((1, 2, 3, 2))
    sector[16:20] = bytes((4, 5, 0, 0))
    sector[20:24] = sector[16:20]
    sector[xgmode2.USER_DATA_OFFSET : xgmode2.USER_DATA_OFFSET + 2048] = user_data
    return xgmode2.regenerate_mode2_form1(bytes(sector))


def _boot_patch_fixture() -> tuple[bytes, bytes, bytes]:
    header_data = bytearray(2048)
    header_data[:8] = b"PS-X EXE"
    struct.pack_into("<I", header_data, 0x1C, xgmode2.SLUS_TEXT_SIZE)
    header_sector = _form1_sector(bytes(header_data))

    target_data = bytearray((index * 37 + 11) & 0xFF for index in range(2048))
    start = xgmode2.PATCH_CONTEXT_OFFSET
    target_data[start : start + len(xgmode2.PATCH_CONTEXT_BEFORE)] = (
        xgmode2.PATCH_CONTEXT_BEFORE
    )
    retail_sector = _form1_sector(bytes(target_data))

    patched_data = bytearray(target_data)
    patched_data[start : start + len(xgmode2.PATCH_CONTEXT_AFTER)] = (
        xgmode2.PATCH_CONTEXT_AFTER
    )
    patched_sector = _form1_sector(bytes(patched_data))
    return header_sector, retail_sector, patched_sector


def _source_gamestate() -> bytes:
    state = bytearray(
        (index * 29 + 7) & 0xFF for index in range(bootstrap.STATE_SIZE)
    )
    # This retail global is deliberately preserved by normalize_state() and is
    # independently checked by the dungeon builder.
    state[0x1930:0x1932] = b"\xFC\x00"
    state[
        dungeon.INITIAL_GAMESTATE_EL_REGULUS_NAME_OFFSET :
        dungeon.INITIAL_GAMESTATE_EL_REGULUS_NAME_OFFSET
        + len(dungeon.INITIAL_GAMESTATE_SOURCE_GEAR_NAME_BYTES)
    ] = dungeon.INITIAL_GAMESTATE_SOURCE_GEAR_NAME_BYTES
    state[dungeon.INITIAL_GAMESTATE_ELLY_GEAR_OFFSET] = 2
    for offset in dungeon.INITIAL_GAMESTATE_ELLY_LEVEL_OFFSETS:
        state[offset] = dungeon.INITIAL_GAMESTATE_ELLY_SOURCE_LEVEL
    struct.pack_into(
        "<H",
        state,
        dungeon.INITIAL_GAMESTATE_ELLY_ON_FOOT_DEATHBLOW_FLAGS_OFFSET,
        dungeon.INITIAL_GAMESTATE_ELLY_SOURCE_ON_FOOT_DEATHBLOW_FLAGS,
    )
    struct.pack_into(
        "<H",
        state,
        dungeon.INITIAL_GAMESTATE_ELLY_GEAR_DEATHBLOW_FLAGS_OFFSET,
        dungeon.INITIAL_GAMESTATE_ELLY_SOURCE_GEAR_DEATHBLOW_FLAGS,
    )
    struct.pack_into(
        "<H",
        state,
        dungeon.INITIAL_GAMESTATE_ELLY_GEAR_OPTIONS_OFFSET,
        dungeon.INITIAL_GAMESTATE_ELLY_GEAR_OPTIONS,
    )
    accessory_start = dungeon.INITIAL_GAMESTATE_EL_REGULUS_ACCESSORY_OFFSET
    state[
        accessory_start :
        accessory_start
        + len(dungeon.INITIAL_GAMESTATE_EL_REGULUS_SOURCE_ACCESSORIES)
    ] = dungeon.INITIAL_GAMESTATE_EL_REGULUS_SOURCE_ACCESSORIES
    return bytes(state)


def _expected_normalized_state(source: bytes) -> bytes:
    state = bytearray(source)
    struct.pack_into("<H", state, 0x1834, 0)
    struct.pack_into("<H", state, 0x1836, 0)
    struct.pack_into("<H", state, 0x1934, 0)
    struct.pack_into("<H", state, 0x1D2A, 0)
    struct.pack_into("<H", state, 0x1D2C, 0)
    struct.pack_into("<H", state, 0x1D2E, 0)
    state[0x1D34:0x1D37] = bytes((1, 6, 0xFF))
    state[0x22B1:0x22B4] = b"\x00\x00\x00"
    struct.pack_into("<H", state, 0x2318, 0)
    struct.pack_into("<H", state, 0x231A, 720)
    struct.pack_into("<H", state, 0x231C, 0x400)
    struct.pack_into("<H", state, 0x231E, 21)
    struct.pack_into("<H", state, 0x2320, 0)
    return bytes(state)


class StandaloneBootPatchTests(unittest.TestCase):
    def test_native_title_boot_verifier_is_read_only(self) -> None:
        header, retail, _ = _boot_patch_fixture()
        original = bytes(xgmode2.RAW_SECTOR_SIZE) + header + retail

        with tempfile.TemporaryDirectory() as temporary:
            image = Path(temporary) / "disc.bin"
            image.write_bytes(original)
            with patch.multiple(
                xgmode2,
                SLUS_HEADER_LBA=1,
                SLUS_TARGET_LBA=2,
                RETAIL_TARGET_SECTOR_SHA256=_sha256(retail),
            ):
                result = xgmode2.verify_retail_title_boot(image)

            self.assertEqual(result.image, image.resolve())
            self.assertEqual(result.lba, 2)
            self.assertEqual(result.sha256, _sha256(retail))
            self.assertEqual(image.read_bytes(), original)

    def test_native_title_boot_verifier_rejects_direct_field_patch(self) -> None:
        header, retail, patched = _boot_patch_fixture()
        original = bytes(xgmode2.RAW_SECTOR_SIZE) + header + patched

        with tempfile.TemporaryDirectory() as temporary:
            image = Path(temporary) / "disc.bin"
            image.write_bytes(original)
            with patch.multiple(
                xgmode2,
                SLUS_HEADER_LBA=1,
                SLUS_TARGET_LBA=2,
                RETAIL_TARGET_SECTOR_SHA256=_sha256(retail),
            ):
                with self.assertRaisesRegex(
                    xgmode2.Mode2PatchError, "publisher/title boot sector"
                ):
                    xgmode2.verify_retail_title_boot(image)

            self.assertEqual(image.read_bytes(), original)

    def test_patch_repairs_sector_and_is_idempotent(self) -> None:
        header, retail, expected_patched = _boot_patch_fixture()
        prefix = bytes(xgmode2.RAW_SECTOR_SIZE) + header

        with tempfile.TemporaryDirectory() as temporary:
            image = Path(temporary) / "disc.bin"
            image.write_bytes(prefix + retail)
            with patch.multiple(
                xgmode2,
                SLUS_HEADER_LBA=1,
                SLUS_TARGET_LBA=2,
                RETAIL_TARGET_SECTOR_SHA256=_sha256(retail),
                PATCHED_TARGET_SECTOR_SHA256=_sha256(expected_patched),
            ):
                result = xgmode2.patch_standalone_boot(image)
                second = xgmode2.patch_standalone_boot(image)

            self.assertEqual(result.image, image.resolve())
            self.assertEqual(result.lba, 2)
            self.assertEqual(result.before_sha256, _sha256(retail))
            self.assertEqual(result.after_sha256, _sha256(expected_patched))
            self.assertFalse(result.already_patched)
            self.assertEqual(image.read_bytes(), prefix + expected_patched)

            self.assertTrue(second.already_patched)
            self.assertEqual(second.before_sha256, _sha256(expected_patched))
            self.assertEqual(second.after_sha256, _sha256(expected_patched))
            self.assertEqual(
                xgmode2.regenerate_mode2_form1(expected_patched), expected_patched
            )

    def test_hash_mismatch_fails_before_mutating_image(self) -> None:
        header, retail, expected_patched = _boot_patch_fixture()
        original = bytes(xgmode2.RAW_SECTOR_SIZE) + header + retail

        with tempfile.TemporaryDirectory() as temporary:
            image = Path(temporary) / "disc.bin"
            image.write_bytes(original)
            with patch.multiple(
                xgmode2,
                SLUS_HEADER_LBA=1,
                SLUS_TARGET_LBA=2,
                RETAIL_TARGET_SECTOR_SHA256="0" * 64,
                PATCHED_TARGET_SECTOR_SHA256=_sha256(expected_patched),
            ):
                with self.assertRaisesRegex(xgmode2.Mode2PatchError, "hash mismatch"):
                    xgmode2.patch_standalone_boot(image)

            self.assertEqual(image.read_bytes(), original)


class InitialGameStateTests(unittest.TestCase):
    def test_normalization_sets_standalone_boot_contract(self) -> None:
        source = _source_gamestate()
        expected = _expected_normalized_state(source)

        with patch.object(bootstrap, "NORMALIZED_SHA256", _sha256(expected)):
            result = bootstrap.normalize_state(source)

        self.assertEqual(result, expected)
        self.assertEqual(len(result), bootstrap.STATE_SIZE)
        self.assertEqual(source, _source_gamestate())
        self.assertEqual(result[0x1930:0x1932], b"\xFC\x00")
        self.assertEqual(result[0x1934:0x1936], b"\x00\x00")
        self.assertEqual(result[0x1D2A:0x1D2C], b"\x00\x00")
        self.assertEqual(result[0x1D2C:0x1D2E], b"\x00\x00")
        self.assertEqual(result[0x1D2E:0x1D30], b"\x00\x00")
        self.assertEqual(result[0x1D34:0x1D37], b"\x01\x06\xFF")
        self.assertEqual(result[0x22B1:0x22B4], b"\x00\x00\x00")
        self.assertEqual(struct.unpack_from("<H", result, 0x231A)[0], 720)
        self.assertEqual(struct.unpack_from("<H", result, 0x231E)[0], 21)
        # m2320 supplies the field-entry record. WORLD_MAP(21, 1) supplies
        # world-map mode 1 later, so cold boot must begin on source entry 0.
        self.assertEqual(struct.unpack_from("<H", result, 0x2320)[0], 0)

    def test_builder_accepts_the_checked_normalized_state(self) -> None:
        state = _expected_normalized_state(_source_gamestate())
        expected = bytearray(state)
        expected[: dungeon.INITIAL_GAMESTATE_NAME_REGION_SIZE] = (
            dungeon._build_initial_gamestate_retail_name_region()
        )
        expected[
            dungeon.INITIAL_GAMESTATE_ELLY_GEAR_OFFSET
        ] = dungeon.VIERGE_GEAR_ID
        for offset in dungeon.INITIAL_GAMESTATE_ELLY_LEVEL_OFFSETS:
            expected[offset] = dungeon.INITIAL_GAMESTATE_ELLY_RELEASE_LEVEL
        struct.pack_into(
            "<H",
            expected,
            dungeon.INITIAL_GAMESTATE_ELLY_ON_FOOT_DEATHBLOW_FLAGS_OFFSET,
            dungeon.INITIAL_GAMESTATE_ELLY_ALL_ON_FOOT_DEATHBLOW_FLAGS,
        )
        struct.pack_into(
            "<H",
            expected,
            dungeon.INITIAL_GAMESTATE_ELLY_GEAR_DEATHBLOW_FLAGS_OFFSET,
            dungeon.INITIAL_GAMESTATE_ELLY_ALL_GEAR_DEATHBLOW_FLAGS,
        )
        accessory_start = dungeon.INITIAL_GAMESTATE_EL_REGULUS_ACCESSORY_OFFSET
        struct.pack_into("<H", expected, 0x231A, dungeon.TITLE_MENU_FIELD)
        expected = bytes(expected)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "standalone_bootstrap" / "2595.bin"
            source.parent.mkdir()
            source.write_bytes(state)
            with (
                patch.object(
                    dungeon, "INITIAL_GAMESTATE_SOURCE_SHA256", _sha256(state)
                ),
                patch.object(
                    dungeon, "INITIAL_GAMESTATE_SHA256", _sha256(expected)
                ),
            ):
                prepared = dungeon._prepare_initial_gamestate(root)

        self.assertIsNone(prepared.target_field)
        self.assertEqual(prepared.bundle_id, 2595)
        self.assertEqual(prepared.bundle, expected)
        self.assertEqual(
            struct.unpack_from("<H", prepared.bundle, 0x231A)[0],
            dungeon.TITLE_MENU_FIELD,
        )
        self.assertEqual(
            prepared.bundle[
                dungeon.INITIAL_GAMESTATE_EL_REGULUS_NAME_OFFSET :
                dungeon.INITIAL_GAMESTATE_EL_REGULUS_NAME_OFFSET
                + dungeon.INITIAL_GAMESTATE_NAME_RECORD_SIZE
            ],
            dungeon._initial_gamestate_name_record(
                dungeon.INITIAL_GAMESTATE_RETAIL_NAME_GLYPHS[
                    dungeon.INITIAL_GAMESTATE_EL_REGULUS_NAME_SLOT
                ]
            ),
        )
        name_region = prepared.bundle[
            : dungeon.INITIAL_GAMESTATE_NAME_REGION_SIZE
        ]
        self.assertEqual(
            _sha256(name_region),
            dungeon.INITIAL_GAMESTATE_NAME_REGION_RETAIL_SHA256,
        )
        for slot in range(dungeon.INITIAL_GAMESTATE_NAME_RECORD_COUNT):
            record_start = (
                slot * dungeon.INITIAL_GAMESTATE_NAME_RECORD_SIZE
            )
            record = name_region[
                record_start :
                record_start + dungeon.INITIAL_GAMESTATE_NAME_RECORD_SIZE
            ]
            with self.subTest(name_slot=slot):
                self.assertEqual(record[1::2], bytes(10))
        self.assertEqual(
            name_region[1 * 20 : 2 * 20 : 2],
            bytes.fromhex("24 48 48 55 0F 0F 0F 0F 0F 0F"),
        )
        self.assertEqual(
            name_region[2 * 20 : 3 * 20 : 2],
            bytes.fromhex("22 45 50 3D 4A 0F 0F 0F 0F 0F"),
        )
        self.assertEqual(
            name_region[6 * 20 : 7 * 20 : 2],
            bytes.fromhex("24 49 41 4E 3D 48 40 3D 0F 0F"),
        )
        retail_gear_10_record = name_region[21 * 20 : 22 * 20]
        self.assertEqual(
            retail_gear_10_record[::2],
            bytes.fromhex("31 41 43 51 4E 51 4F 0F 0F 0F"),
        )
        self.assertEqual(retail_gear_10_record[1::2], bytes(10))
        self.assertEqual(dungeon.EL_REGULUS_NAME_GLYPHS[2], 0x1A)

        # Resource 2595's fixed-cell alphabet is not the compact runtime /
        # dialogue alphabet.  These three observed retail mappings anchor the
        # loader conversion that turns a stored 0x1A into the runtime hyphen;
        # storing the dialogue hyphen 0x13 instead produces runtime digit 3.
        fixed_name_remap = {0x12: 0x18, 0x13: 0x19, 0x1A: 0x13}

        def compact_fixed_name(record: bytes) -> bytes:
            compacted = bytearray()
            for glyph in record[::2]:
                if glyph == 0x0F:
                    break
                compacted.append(fixed_name_remap.get(glyph, glyph))
            return bytes(compacted)

        self.assertEqual(
            compact_fixed_name(name_region[7 * 20 : 8 * 20]),
            bytes.fromhex("22 44 51 13 22 44 51"),
        )
        self.assertEqual(
            compact_fixed_name(name_region[12 * 20 : 13 * 20]),
            bytes.fromhex("36 41 48 50 3D 48 48 13 18"),
        )
        self.assertEqual(
            prepared.bundle[dungeon.INITIAL_GAMESTATE_ELLY_GEAR_OFFSET],
            dungeon.VIERGE_GEAR_ID,
        )
        self.assertEqual(
            tuple(
                prepared.bundle[offset]
                for offset in dungeon.INITIAL_GAMESTATE_ELLY_LEVEL_OFFSETS
            ),
            (52, 52),
        )
        self.assertEqual(
            struct.unpack_from(
                "<H",
                prepared.bundle,
                dungeon.INITIAL_GAMESTATE_ELLY_ON_FOOT_DEATHBLOW_FLAGS_OFFSET,
            )[0],
            dungeon.INITIAL_GAMESTATE_ELLY_ALL_ON_FOOT_DEATHBLOW_FLAGS,
        )
        self.assertEqual(
            struct.unpack_from(
                "<H",
                prepared.bundle,
                dungeon.INITIAL_GAMESTATE_ELLY_GEAR_DEATHBLOW_FLAGS_OFFSET,
            )[0],
            dungeon.INITIAL_GAMESTATE_ELLY_ALL_GEAR_DEATHBLOW_FLAGS,
        )
        self.assertEqual(
            struct.unpack_from(
                "<H",
                prepared.bundle,
                dungeon.INITIAL_GAMESTATE_ELLY_GEAR_OPTIONS_OFFSET,
            )[0],
            dungeon.INITIAL_GAMESTATE_ELLY_GEAR_OPTIONS,
        )
        self.assertEqual(
            tuple(
                bool(
                    dungeon.INITIAL_GAMESTATE_ELLY_ALL_GEAR_DEATHBLOW_FLAGS
                    & mask
                )
                for mask in dungeon.GEAR_ATTACK_LEVEL_UNLOCK_MASKS
            ),
            (True, True, True),
        )
        def retail_attack_level_max(flags: int) -> int:
            maximum = 0
            for level, mask in enumerate(
                dungeon.GEAR_ATTACK_LEVEL_UNLOCK_MASKS, start=1
            ):
                if flags & mask:
                    maximum = level
            return maximum

        self.assertEqual(
            retail_attack_level_max(
                dungeon.INITIAL_GAMESTATE_ELLY_SOURCE_GEAR_DEATHBLOW_FLAGS
            ),
            1,
        )
        self.assertEqual(
            retail_attack_level_max(
                dungeon.INITIAL_GAMESTATE_ELLY_ALL_GEAR_DEATHBLOW_FLAGS
            ),
            3,
        )
        self.assertTrue(
            dungeon.INITIAL_GAMESTATE_ELLY_ALL_GEAR_DEATHBLOW_FLAGS
            & dungeon.GEAR_INFINITY_DEATHBLOW_UNLOCK_MASK
        )
        self.assertEqual(
            dungeon.INITIAL_GAMESTATE_ELLY_ALL_GEAR_DEATHBLOW_FLAGS,
            dungeon.GEAR_INFINITY_DEATHBLOW_UNLOCK_MASK
            | sum(dungeon.GEAR_ATTACK_LEVEL_UNLOCK_MASKS),
        )
        self.assertEqual(
            prepared.bundle[
                accessory_start :
                accessory_start
                + len(dungeon.INITIAL_GAMESTATE_EL_REGULUS_SOURCE_ACCESSORIES)
            ],
            dungeon.INITIAL_GAMESTATE_EL_REGULUS_SOURCE_ACCESSORIES,
        )
        self.assertEqual(prepared.bundle[0x22B1:0x22B4], b"\x00\x00\x00")
        self.assertEqual(prepared.components, ())
        self.assertIn(
            f"gateway field {dungeon.BOOTSTRAP_FIELD}",
            prepared.notes[0],
        )
        self.assertIn("Vierge", prepared.notes[3])
        self.assertIn("retail equipment", prepared.notes[4])
        self.assertIn("not installed", prepared.notes[6])

    def test_builder_rejects_entry_record_one_even_with_matching_hash(self) -> None:
        state = bytearray(_expected_normalized_state(_source_gamestate()))
        struct.pack_into("<H", state, 0x2320, 1)
        invalid = bytes(state)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "standalone_bootstrap" / "2595.bin"
            source.parent.mkdir()
            source.write_bytes(invalid)
            with patch.object(
                dungeon, "INITIAL_GAMESTATE_SOURCE_SHA256", _sha256(invalid)
            ):
                with self.assertRaisesRegex(
                    dungeon.DungeonBuildError, "0x2320"
                ):
                    dungeon._prepare_initial_gamestate(root)

    def test_builder_rejects_nonzero_paired_lift_state(self) -> None:
        state = bytearray(_expected_normalized_state(_source_gamestate()))
        struct.pack_into("<H", state, 0x1D2C, 1)
        invalid = bytes(state)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "standalone_bootstrap" / "2595.bin"
            source.parent.mkdir()
            source.write_bytes(invalid)
            with patch.object(
                dungeon, "INITIAL_GAMESTATE_SOURCE_SHA256", _sha256(invalid)
            ):
                with self.assertRaisesRegex(
                    dungeon.DungeonBuildError, "0x1D2C"
                ):
                    dungeon._prepare_initial_gamestate(root)


if __name__ == "__main__":
    unittest.main()
