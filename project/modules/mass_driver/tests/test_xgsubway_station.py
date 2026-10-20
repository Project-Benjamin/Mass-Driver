from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT
from shared.tools.xgdialog import parse_dialogue

import hashlib
from pathlib import Path
import struct
import unittest

from tools.build_mass_driver_dungeon import (
    ACTOR_INDEX,
    CLONES,
    MODEL_INDEX,
    SCRIPT_INDEX,
    SPRITE_INDEX,
    _indexed_bundle_entries,
    _install_repair_bot_assets,
    _install_subway_archive_robot_assets,
    _load_components,
    _prepare_clone,
    _solid_station_controller_init,
    ZEBOIM_STATION_COLLISION_OPERAND,
)
from tools.xgcloning_warheads import (
    ZEBOIM_STATION_TEXTURE_ATLAS as ORIGINAL_STATION_TEXTURE_ATLAS,
    _graphics_rows,
    _reconstruct_graphics_vram,
)
from tools.xgfield import parse_field
from tools.xgscript import AtelScript
from tools.xgsubway_station import (
    SUBWAY_STATION_ATLAS_HEIGHT,
    SUBWAY_STATION_ATLAS_WIDTH,
    SUBWAY_STATION_CARRIER_BANK_SHA256,
    SUBWAY_STATION_CARRIER_IMAGE_INDEX,
    SUBWAY_STATION_CARRIER_IMAGE_SHA256,
    SUBWAY_STATION_CARRIER_VRAM_RECT,
    SUBWAY_STATION_CONTROLLER_POSITION,
    SUBWAY_STATION_DIALOGUE_SCRATCH_VRAM_RECT,
    SUBWAY_STATION_OUTPUT_GRAPHICS_SHA256,
    SUBWAY_STATION_OUTPUT_HEADER_SHA256,
    SUBWAY_STATION_OUTPUT_MODELS_SHA256,
    SUBWAY_STATION_OUTPUT_SPRITES_SHA256,
    SUBWAY_STATION_PATCHED_MODEL14_SHA256,
    SUBWAY_STATION_PLACEMENT,
    SUBWAY_STATION_RELOCATED_MODEL_SHA256,
    SUBWAY_STATION_RELOCATED_ROW489_SHA256,
    SUBWAY_STATION_TARGET_CLUT,
    SUBWAY_STATION_TARGET_MODEL_INDEX,
    SUBWAY_STATION_TARGET_TPAGES,
    SUBWAY_STATION_TEXTURE_ATLAS,
    SUBWAY_STATION_Y_ROTATION,
    SubwayStationError,
    patch_subway_zeboim_station,
)


def _sha256(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


class SubwayZeboimStationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project = REPOSITORY_ROOT
        cls.input_root = cls.project / "work"
        cls.dialogue_root = cls.project / "modules" / "mass_driver" / "content"
        cls.spec = next(spec for spec in CLONES if spec.target_field == 721)
        assert cls.spec.repair_bot_shop is not None
        assert cls.spec.subway_archive_robot is not None

        header, components = _load_components(
            cls.input_root / cls.spec.bundle_directory
        )
        header, components = _install_repair_bot_assets(
            header,
            components,
            cls.input_root,
            cls.spec.repair_bot_shop,
        )
        header, components = _install_subway_archive_robot_assets(
            header,
            components,
            cls.input_root,
            cls.spec.subway_archive_robot,
        )
        donor_header, donor_components = _load_components(
            cls.input_root / "audit_zeboim_cd1" / "field_373"
        )
        cls.original = (
            header,
            components[MODEL_INDEX],
            components[SPRITE_INDEX],
            (cls.input_root / cls.spec.graphics_file).read_bytes(),
        )
        cls.output = patch_subway_zeboim_station(
            *cls.original,
            donor_header,
            donor_components[MODEL_INDEX],
            (cls.input_root / "audit_zeboim_cd1" / "1353.bin").read_bytes(),
        )

    def test_exact_station_model_node_carrier_and_palette_repack(self) -> None:
        header, models, sprites, graphics = self.output
        self.assertEqual(
            (
                len(header),
                _sha256(header),
                len(models),
                _sha256(models),
                len(sprites),
                _sha256(sprites),
                len(graphics),
                _sha256(graphics),
            ),
            (
                896,
                SUBWAY_STATION_OUTPUT_HEADER_SHA256,
                51_964,
                SUBWAY_STATION_OUTPUT_MODELS_SHA256,
                102_196,
                SUBWAY_STATION_OUTPUT_SPRITES_SHA256,
                319_488,
                SUBWAY_STATION_OUTPUT_GRAPHICS_SHA256,
            ),
        )
        self.assertEqual(struct.unpack_from("<H", header, 0x18C)[0], 31)
        self.assertEqual(
            struct.unpack_from("<HhhhhhhH", header, 0x370),
            (
                0x0010,
                0,
                SUBWAY_STATION_Y_ROTATION,
                0,
                *SUBWAY_STATION_PLACEMENT,
                SUBWAY_STATION_TARGET_MODEL_INDEX,
            ),
        )

        model_entries = _indexed_bundle_entries(models)
        self.assertEqual(len(model_entries), 16)
        self.assertEqual(_sha256(model_entries[14]), SUBWAY_STATION_PATCHED_MODEL14_SHA256)
        self.assertEqual(
            _sha256(model_entries[SUBWAY_STATION_TARGET_MODEL_INDEX]),
            SUBWAY_STATION_RELOCATED_MODEL_SHA256,
        )
        station = model_entries[SUBWAY_STATION_TARGET_MODEL_INDEX]
        self.assertIn(struct.pack("<H", SUBWAY_STATION_TARGET_TPAGES[0]), station)
        self.assertIn(struct.pack("<H", SUBWAY_STATION_TARGET_TPAGES[1]), station)
        self.assertIn(struct.pack("<H", SUBWAY_STATION_TARGET_CLUT), station)

        old_graphics = self.original[3]
        self.assertEqual(len(graphics), len(old_graphics))
        changed = {
            index
            for index, (old, new) in enumerate(zip(old_graphics, graphics, strict=True))
            if old != new
        }
        self.assertTrue(changed)
        self.assertTrue(changed <= set(range(0x1600, 0x1A00)))
        old_vram, old_rectangles = _reconstruct_graphics_vram(
            old_graphics, label="Original field 721"
        )
        new_vram, new_rectangles = _reconstruct_graphics_vram(
            graphics, label="Station field 721"
        )
        self.assertEqual(old_rectangles, new_rectangles)
        self.assertEqual(len(new_rectangles), 37)
        self.assertEqual(
            _sha256(_graphics_rows(new_vram, (0, 488, 256, 1))),
            "7754aac52c72639ecd632cbac7a46c73b0a2873ca1091dcb67325ba2508c1065",
        )
        self.assertEqual(
            _sha256(_graphics_rows(new_vram, (0, 489, 256, 1))),
            SUBWAY_STATION_RELOCATED_ROW489_SHA256,
        )
        # Every VRAM byte outside the two edited CLUT rows is unchanged.
        masked = bytearray(new_vram)
        for row in (488, 489):
            start = row * 1024 * 2
            masked[start : start + 512] = old_vram[start : start + 512]
        self.assertEqual(masked, old_vram)

        old_banks = _indexed_bundle_entries(self.original[2])
        new_banks = _indexed_bundle_entries(sprites)
        self.assertEqual(new_banks[0], old_banks[0])
        self.assertEqual(
            _sha256(new_banks[1]),
            SUBWAY_STATION_CARRIER_BANK_SHA256,
        )
        old_images = _indexed_bundle_entries(old_banks[1])
        new_images = _indexed_bundle_entries(new_banks[1])
        self.assertEqual(new_images[0], old_images[0])
        self.assertNotEqual(new_images[1], old_images[1])
        self.assertEqual(
            SUBWAY_STATION_CARRIER_IMAGE_INDEX,
            1,
        )
        self.assertEqual(struct.unpack_from("<HH", new_images[1]), (64, 49))
        self.assertEqual(
            _sha256(new_images[1]),
            SUBWAY_STATION_CARRIER_IMAGE_SHA256,
        )

        # Live post-shop VRAM proves x768 is the dialogue/menu glyph page and
        # x832 rows 0..48 survive unchanged. The passive station must sample
        # only the latter; rows 49+ are deliberately excluded as well.
        carrier_x, carrier_y, carrier_width, carrier_height = (
            SUBWAY_STATION_CARRIER_VRAM_RECT
        )
        scratch_x, scratch_y, scratch_width, scratch_height = (
            SUBWAY_STATION_DIALOGUE_SCRATCH_VRAM_RECT
        )
        self.assertFalse(
            carrier_x < scratch_x + scratch_width
            and scratch_x < carrier_x + carrier_width
            and carrier_y < scratch_y + scratch_height
            and scratch_y < carrier_y + carrier_height
        )
        self.assertEqual(
            (SUBWAY_STATION_ATLAS_WIDTH, SUBWAY_STATION_ATLAS_HEIGHT),
            (128, 49),
        )
        for _source, (target_u, target_v) in SUBWAY_STATION_TEXTURE_ATLAS:
            source_width, source_height = _source[2:]
            self.assertLessEqual(target_u + source_width, 128)
            self.assertLessEqual(target_v + source_height, 49)

        # The menu-safe repack splits some islands at audited polygon seams,
        # but it must preserve exactly the original set of sampled texels.
        def sampled_texels(atlas: tuple[tuple[tuple[int, int, int, int], tuple[int, int]], ...]) -> set[tuple[int, int]]:
            return {
                (source_u + x, source_v + y)
                for (source_u, source_v, width, height), _target in atlas
                for y in range(height)
                for x in range(width)
            }

        self.assertEqual(
            sampled_texels(SUBWAY_STATION_TEXTURE_ATLAS),
            sampled_texels(ORIGINAL_STATION_TEXTURE_ATLAS),
        )

    def test_prepared_field_renders_no_archive_robot_and_keeps_repeatable_timetable(self) -> None:
        prepared = _prepare_clone(self.spec, self.input_root, self.dialogue_root)
        parsed = parse_field(prepared.bundle)
        self.assertEqual(
            (len(prepared.bundle), _sha256(prepared.bundle)),
            (
                195_392,
                "214a214d303b87bd80c5d5c7c5de99892e7e23d27bc8eccc46aeb284f1fa176b",
            ),
        )
        self.assertEqual(len(_indexed_bundle_entries(parsed.parts[MODEL_INDEX].data)), 16)
        self.assertEqual(
            _sha256(parsed.parts[ACTOR_INDEX].data),
            "0f6489e7d9e31932a9cf5854f2aa3da16422999e72e901ae064c8d9deece8c50",
        )
        editor = AtelScript(parsed.parts[SCRIPT_INDEX].data)
        controller_x, controller_z = SUBWAY_STATION_CONTROLLER_POSITION
        expected_init = _solid_station_controller_init(
            controller_x,
            controller_z,
            requires_facing=False,
            collision_operand=ZEBOIM_STATION_COLLISION_OPERAND,
        )
        init = editor.get_script_pointer(14, 0)
        self.assertEqual(editor.bytecode[init : init + len(expected_init)], expected_init)
        self.assertEqual(editor.bytecode[init], 0x0B)  # INIT_ENTITY_NPC
        self.assertIn(bytes.fromhex("F8 00 10 00"), expected_init)
        self.assertIn(b"\x23", expected_init)
        self.assertNotIn(b"\x2A", expected_init)
        action = editor.get_script_pointer(14, 2)
        action_body = editor.bytecode[action : action + 32]
        self.assertTrue(action_body.startswith(bytes.fromhex("33 FE 54")))
        self.assertIn(bytes.fromhex("F5 00 00 00 9C FE 53 00"), action_body)
        timetable = parse_dialogue(parsed.parts[7].data).blocks[0].text
        for phrase in (
            "PERSONNEL TRAIN",
            "SERVICE SUSPENDED",
            "No departures scheduled.",
            "SAVED SHIFT TIMETABLE\nArrival / Departure\n"
            "06:00 / 06:15\n14:00 / 14:15\n22:00 / 22:15",
            "PASSENGER NOTICE",
            "All passenger runs cancelled.",
        ):
            self.assertIn(phrase, timetable)
        self.assertNotIn("Mira", timetable)
        self.assertNotIn("SURVEY CARRIER", timetable)

    def test_rejects_target_drift(self) -> None:
        header, models, sprites, graphics = self.original
        corrupt = bytearray(sprites)
        corrupt[-1] ^= 1
        donor_header, donor_components = _load_components(
            self.input_root / "audit_zeboim_cd1" / "field_373"
        )
        with self.assertRaises(SubwayStationError):
            patch_subway_zeboim_station(
                header,
                models,
                bytes(corrupt),
                graphics,
                donor_header,
                donor_components[MODEL_INDEX],
                (self.input_root / "audit_zeboim_cd1" / "1353.bin").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
