from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT
from shared.tools.xgdialog import parse_dialogue

import hashlib
import struct
import unittest
from functools import lru_cache
from pathlib import Path

from tools.build_mass_driver_dungeon import (
    ACTOR_INDEX,
    ANNEX_TREASURE_A_OPENED_BIT,
    ANNEX_TREASURE_B_OPENED_BIT,
    ANNEX_TREASURE_VARIABLE,
    ARRIVAL_CONTINUITY_CONTRACTS,
    CLONES,
    MODEL_INDEX,
    OMEGASOL_ITEM_ID,
    SCRIPT_INDEX,
    SPRITE_INDEX,
    STATIC_DOOR_SLIDE_POINTERS,
    VISIBLE_DOOR_CONTRACTS,
    FieldEntryAddition,
    _change_field,
    _indexed_bundle_entries,
    _jump_if_bit_clear,
    _install_static_door_assets,
    _load_components,
    _pointed_script_body,
    _prepare_clone,
    _read_field_entry,
    _set_var_bit,
    _solid_station_controller_init,
    _static_door_controller_init,
    _transform_clone_script,
)
from tools.xgcloning_warheads import (
    _graphics_rows,
    _reconstruct_graphics_vram,
)
from tools.xginner_access_station import (
    INNER_ACCESS_STATION_RELOCATED_MODEL_SHA256,
    INNER_ACCESS_STATION_TARGET_CLUT,
    INNER_ACCESS_STATION_TARGET_MODEL_INDEX,
)
from tools.xgservice_junction_station import (
    SERVICE_JUNCTION_GRAPHICS_RECTANGLES,
    SERVICE_JUNCTION_NATIVE_ROW485_USED_INDICES,
    SERVICE_JUNCTION_NATIVE_ROW488_RECT,
    SERVICE_JUNCTION_STATION_APPROACH_POSITION,
    SERVICE_JUNCTION_STATION_APPROACH_TRIANGLE,
    SERVICE_JUNCTION_STATION_ATLAS_SHA256,
    SERVICE_JUNCTION_STATION_COLLIDER_ENTITY,
    SERVICE_JUNCTION_STATION_COLLIDER_POSITION,
    SERVICE_JUNCTION_STATION_COLLIDER_TRIANGLE,
    SERVICE_JUNCTION_STATION_COLLISION_OPERAND,
    SERVICE_JUNCTION_STATION_OUTPUT_GRAPHICS_SHA256,
    SERVICE_JUNCTION_STATION_PALETTE_SHA256,
    SERVICE_JUNCTION_STATION_PLACEMENT,
    SERVICE_JUNCTION_STATION_READER_ENTITY,
    SERVICE_JUNCTION_STATION_READER_HALF_WIDTH,
    SERVICE_JUNCTION_STATION_READER_POSITION,
    SERVICE_JUNCTION_STATION_READER_TRIANGLE,
    SERVICE_JUNCTION_STATION_REMAPPED_ATLAS_SHA256,
    SERVICE_JUNCTION_STATION_SCREEN_NORMAL,
    SERVICE_JUNCTION_STATION_TARGET_CLUT,
    SERVICE_JUNCTION_STATION_TARGET_PALETTE_RECT,
    SERVICE_JUNCTION_STATION_TARGET_MODEL_INDEX,
    SERVICE_JUNCTION_STATION_TARGET_NODE_INDEX,
    SERVICE_JUNCTION_STATION_TARGET_TPAGES,
    SERVICE_JUNCTION_STATION_TEXTURE_RECT,
    SERVICE_JUNCTION_STATION_USED_INDEX_COUNT,
    SERVICE_JUNCTION_STATION_WORLD_BOUNDS,
    SERVICE_JUNCTION_STATION_Y_ROTATION,
)
from tools.xgsubway_station import _build_legacy_station_atlas
from tools.xgscript import AtelScript


PROJECT = REPOSITORY_ROOT
WORK = PROJECT / "work"


# origin field, controller, model helpers, annex, return parameter, return entry
DIRECT_ANNEX_CASES = (
    (
        726,
        19,
        (26,),
        366,
        3,
        FieldEntryAddition(20, -176, 0, 6, 6),
    ),
    (
        726,
        21,
        (28,),
        368,
        5,
        FieldEntryAddition(-529, -560, 0, 0, 0),
    ),
    (
        726,
        22,
        (29,),
        369,
        6,
        FieldEntryAddition(-345, -545, 0, 6, 6),
    ),
    (
        726,
        23,
        (30,),
        370,
        7,
        FieldEntryAddition(-529, 510, 0, 0, 0),
    ),
    (
        726,
        25,
        (32,),
        724,
        9,
        FieldEntryAddition(20, 441, 0, 6, 6),
    ),
)
ANNEX_RETURN_CASES = tuple(
    (origin, annex, return_parameter)
    for (
        origin,
        _controller,
        _helpers,
        annex,
        return_parameter,
        _return_entry,
    ) in DIRECT_ANNEX_CASES
) + ((723, 371, 0),)


def _spec(target_field: int):
    return next(spec for spec in CLONES if spec.target_field == target_field)


@lru_cache(maxsize=None)
def _script_pair(target_field: int) -> tuple[AtelScript, AtelScript]:
    spec = _spec(target_field)
    source = (WORK / spec.bundle_directory / "05_scripts.bin").read_bytes()
    transformed, _notes = _transform_clone_script(spec, source)
    return AtelScript(source), AtelScript(transformed)


@lru_cache(maxsize=None)
def _prepared_clone(target_field: int):
    return _prepare_clone(
        _spec(target_field),
        WORK,
        PROJECT / "modules" / "mass_driver" / "content",
    )


def _actor_record(header: bytes, entity: int) -> tuple[int, ...]:
    return struct.unpack_from("<HhhhhhhH", header, 0x190 + entity * 16)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class StaticDoorAssetTests(unittest.TestCase):
    def test_field_363_preserves_retail_model_2_as_inert_wall_scenery(
        self,
    ) -> None:
        spec = _spec(363)
        header, components = _load_components(WORK / spec.bundle_directory)
        prepared = _prepared_clone(363)
        patched_header = prepared.header
        assert patched_header is not None
        patched_models = prepared.components[MODEL_INDEX]

        self.assertEqual(spec.static_door_exits, ())
        self.assertEqual(len(header), 800)
        self.assertEqual(struct.unpack_from("<H", header, 0x18C)[0], 25)
        self.assertEqual(len(patched_header), 832)
        self.assertEqual(struct.unpack_from("<H", patched_header, 0x18C)[0], 27)
        self.assertEqual(
            _sha256(patched_header),
            "c5dd92f8b149eee4e8287b622d0cd70c730c82eb796115dc0642464d2df6a182",
        )

        # The donor's static node-17/model-2 panel remains exactly once as
        # inert node 18. Reader e17 is inserted before it, but neither its
        # flags nor model change and it has no corresponding ATEL entity.
        self.assertEqual(
            _actor_record(header, 17),
            (0x0010, 0, 0, 0, 0, 0, 0, 2),
        )
        self.assertEqual(
            _actor_record(patched_header, 17),
            (0x01E0, 0, 0, 0, 0, 0, -150, 0),
        )
        self.assertEqual(
            _actor_record(patched_header, 18),
            _actor_record(header, 17),
        )
        self.assertEqual(
            patched_header[0x190 : 0x190 + 17 * 16],
            header[0x190 : 0x190 + 17 * 16],
        )
        self.assertEqual(
            patched_header[0x190 + 18 * 16 : 0x190 + 26 * 16],
            header[0x190 + 17 * 16 : 0x190 + 25 * 16],
        )

        original = _indexed_bundle_entries(components[MODEL_INDEX])
        patched = _indexed_bundle_entries(patched_models)
        self.assertEqual(len(original), 10)
        self.assertEqual(len(patched), 11)
        self.assertEqual(patched[:10], original)
        self.assertEqual(
            _sha256(patched[2]),
            "66b29de5eaa2ecdbffdf9a7188e29f323270dd0dc444b861cd3645818bfcd784",
        )

    def test_field_726_header_and_models_cover_all_seven_orphan_panels(
        self,
    ) -> None:
        spec = _spec(726)
        header, components = _load_components(WORK / spec.bundle_directory)
        patched_header, patched_models = _install_static_door_assets(
            header,
            components[MODEL_INDEX],
            726,
            spec.static_door_exits,
        )

        self.assertEqual(len(header), 752)
        self.assertEqual(struct.unpack_from("<H", header, 0x18C)[0], 22)
        self.assertEqual(len(patched_header), 976)
        self.assertEqual(struct.unpack_from("<H", patched_header, 0x18C)[0], 36)
        self.assertEqual(
            _sha256(patched_header),
            "fe84877061b8e70a7544a444e0f9d3054208e65ec8803b5acd68d7d97f1124ae",
        )

        expected_controllers = {
            door.controller_entity: (
                0x01E0,
                0,
                0,
                0,
                door.controller_x,
                0,
                door.controller_z,
                0,
            )
            for door in spec.static_door_exits
        }
        expected_helpers = {
            helper.entity: (
                0x0290,
                0,
                helper.y_rotation,
                0,
                helper.x,
                0,
                helper.z,
                helper.model_index,
            )
            for door in spec.static_door_exits
            for helper in door.helpers
        }
        self.assertEqual(set(expected_controllers), set(range(19, 26)))
        self.assertEqual(set(expected_helpers), set(range(26, 33)))
        for entity, expected in (*expected_controllers.items(), *expected_helpers.items()):
            self.assertEqual(_actor_record(patched_header, entity), expected)

        # Horizontal panels use the two retail-facing donors: model 7 with a
        # quarter-turn where needed, or model 8 for the opposite native face.
        self.assertEqual(
            tuple(
                (
                    helper.entity,
                    helper.model_index,
                    helper.y_rotation,
                    helper.animation_pointer,
                )
                for door in spec.static_door_exits
                for helper in door.helpers
            ),
            (
                (26, 7, -0x0400, 0x019D),
                (27, 6, 0, 0x017C),
                (28, 7, 0, 0x019D),
                (29, 8, 0, 0x01BE),
                (30, 7, 0, 0x019D),
                (31, 7, 0, 0x019D),
                (32, 7, -0x0400, 0x019D),
            ),
        )

        # The three original static actors survive after the inserted
        # controller/helper records, so unrelated scenery is not lost.
        self.assertEqual(
            patched_header[0x190 : 0x190 + 19 * 16],
            header[0x190 : 0x190 + 19 * 16],
        )
        self.assertEqual(
            patched_header[0x190 + 33 * 16 :],
            header[0x190 + 19 * 16 :],
        )

        original = _indexed_bundle_entries(components[MODEL_INDEX])
        patched = _indexed_bundle_entries(patched_models)
        self.assertEqual(len(original), 6)
        self.assertEqual(len(patched), 9)
        self.assertEqual(patched[:3], original[:3])
        self.assertEqual(patched[4:6], original[4:6])
        self.assertEqual(
            tuple(_sha256(model) for model in patched[6:]),
            (
                "e3f33694c200a978a22f53ad6ff9861c55108d666f7cf9005f022cbb38d8fc03",
                "f5406d2a45be891fc262499a864a77fe2c33ae5211af38ae11235fdbbb236da2",
                "d96d685266b27606890122ba11eb372545342abfbe7c53839557137ea8b1e350",
            ),
        )
        self.assertEqual(
            _sha256(patched_models),
            "aa1c67b892f689fd98f5817b511c8262f5430a8edae31bf3f556a535e78e1b97",
        )

    def test_field_726_baked_panel_tail_is_removed_from_mesh_and_display_list(
        self,
    ) -> None:
        spec = _spec(726)
        header, components = _load_components(WORK / spec.bundle_directory)
        _patched_header, patched_models = _install_static_door_assets(
            header,
            components[MODEL_INDEX],
            726,
            spec.static_door_exits,
        )
        original = _indexed_bundle_entries(components[MODEL_INDEX])[3]
        patched = _indexed_bundle_entries(patched_models)[3]

        expected_indices = bytes.fromhex(
            "93 00 92 00 94 00 91 00 53 00 52 00 4E 00 4D 00 "
            "71 00 72 00 6F 00 6E 00 76 00 75 00 77 00 74 00 "
            "83 00 82 00 84 00 81 00 6A 00 6B 00 67 00 66 00 "
            "8B 00 8A 00 8C 00 89 00 4D 00 4C 00 4E 00 4B 00"
        )
        self.assertEqual(original[0x1200:0x1240], expected_indices)
        self.assertEqual(
            (
                struct.unpack_from("<H", original, 0x14)[0],
                struct.unpack_from("<H", patched, 0x14)[0],
                struct.unpack_from("<H", original, 0x0A7E)[0],
                struct.unpack_from("<H", patched, 0x0A7E)[0],
                struct.unpack_from("<I", original, 0x24)[0],
                struct.unpack_from("<I", patched, 0x24)[0],
                struct.unpack_from("<I", original, 0x44)[0],
                struct.unpack_from("<I", patched, 0x44)[0],
            ),
            (268, 260, 248, 240, 0x1240, 0x1200, 0x2940, 0x2800),
        )
        self.assertEqual(len(original) - len(patched), 0xA0)
        self.assertEqual(patched[0x0A80:0x1200], original[0x0A80:0x1200])
        self.assertEqual(patched[0x1200:], original[0x1240:-0x60])
        self.assertNotEqual(patched[0x1200:0x1240], expected_indices)
        self.assertEqual(
            0x0A80 + struct.unpack_from("<H", patched, 0x0A7E)[0] * 8,
            struct.unpack_from("<I", patched, 0x24)[0],
        )
        self.assertEqual(len(patched) - 0x1200, 20 * 11 + 240 * 12)
        self.assertEqual(
            _sha256(patched),
            "9e6686ad10243acfb6274dd5b9a9a22399adaeb87f145c71ea67ffba8c33e745",
        )

    def test_field_394_defense_archive_has_real_west_bulkhead_assets(
        self,
    ) -> None:
        spec = _spec(376)
        header, components = _load_components(WORK / spec.bundle_directory)
        patched_header, patched_models = _install_static_door_assets(
            header,
            components[MODEL_INDEX],
            376,
            spec.static_door_exits,
        )

        self.assertEqual((spec.source_field, spec.target_field), (394, 376))
        self.assertEqual((len(header), len(patched_header)), (848, 912))
        self.assertEqual(
            (
                struct.unpack_from("<H", header, 0x18C)[0],
                struct.unpack_from("<H", patched_header, 0x18C)[0],
            ),
            (28, 32),
        )
        self.assertEqual(
            _sha256(patched_header),
            "d9375c6faff8145f7d7836789a374e13b646ed4bd085c4124bd904c51b6103c4",
        )
        self.assertEqual(
            _actor_record(patched_header, 14),
            (0x01E0, 0, 0, 0, -530, 0, 0, 0),
        )
        self.assertEqual(
            _actor_record(patched_header, 15),
            (0x0290, 0, 0, 0, 0, 0, 0, 14),
        )
        self.assertEqual(
            _actor_record(patched_header, 16),
            (0x0290, 0, 0, 0, 0, 0, 0, 15),
        )
        self.assertEqual(
            patched_header[0x190 : 0x190 + 14 * 16],
            header[0x190 : 0x190 + 14 * 16],
        )
        self.assertEqual(
            patched_header[0x190 + 17 * 16 : 0x190 + 31 * 16],
            header[0x190 + 14 * 16 :],
        )
        self.assertEqual(
            _actor_record(patched_header, 31),
            (0x0010, 0, 0, 0, 0, 0, 0, 16),
        )

        original = _indexed_bundle_entries(components[MODEL_INDEX])
        patched = _indexed_bundle_entries(patched_models)
        self.assertEqual((len(original), len(patched)), (14, 20))
        self.assertEqual(patched[:8], original[:8])
        self.assertEqual(patched[9:13], original[9:13])
        self.assertEqual(
            _sha256(patched[8]),
            "0d4f5eeac9f21d96e3a1c93cdb8ac0cf4b6d5e09ed7a1de4d690063c2e72138a",
        )
        self.assertEqual(
            (
                struct.unpack_from("<H", patched[8], 0x14)[0],
                struct.unpack_from("<H", patched[8], 0x806)[0],
                struct.unpack_from("<I", patched[8], 0x24)[0],
                struct.unpack_from("<I", patched[8], 0x44)[0],
            ),
            (153, 151, 0x0CC0, 0x17D8),
        )
        self.assertNotIn(
            bytes.fromhex("2A 00 38 00 C8 00 C7 00"),
            patched[8],
        )
        self.assertEqual(
            _sha256(patched[14]),
            "e6dee685c9856adc626d9785749fc37155362c76253d36e60b8850f7dc3beebc",
        )
        self.assertEqual(len(patched[14]), 136)
        self.assertEqual(
            struct.unpack_from("<HHH", patched[14], 0x12),
            (4, 1, 1),
        )
        self.assertEqual(
            patched[14][-20:],
            bytes.fromhex(
                "87 00 00 C4 00 78 00 C8 "
                "00 00 00 2D 60 73 70 73 60 42 70 42"
            ),
        )
        self.assertEqual(
            _sha256(patched[15]),
            "7a869fff26c681a2164f2cdc197fa8396f5f7cf3b366b387dd2eee55d85a51d6",
        )
        self.assertEqual(len(patched[15]), 136)
        self.assertEqual(
            struct.unpack_from("<HHH", patched[15], 0x12),
            (4, 1, 1),
        )
        self.assertEqual(
            patched[15][-20:],
            bytes.fromhex(
                "87 00 00 C4 00 78 00 C8 "
                "00 00 00 2D 70 73 80 73 70 42 80 42"
            ),
        )
        self.assertEqual(
            _sha256(patched[16]),
            "3352ec9ab42d8a0741db97a8c2763887ef96f45ab280fcf273d3d17ff93f97b0",
        )
        self.assertEqual(len(patched[16]), 396)
        self.assertEqual(
            struct.unpack_from("<HHH", patched[16], 0x12),
            (16, 16, 1),
        )
        self.assertEqual(
            _sha256(patched[13]),
            "9cebfc7ad288d4f9332c67be1ca1283d78b329f559483143dc4d936413347520",
        )
        self.assertEqual(
            (
                len(patched[13]),
                struct.unpack_from("<H", patched[13], 0x14)[0],
                struct.unpack_from("<H", patched[13], 0x3EE)[0],
                struct.unpack_from("<I", patched[13], 0x24)[0],
                struct.unpack_from("<I", patched[13], 0x44)[0],
            ),
            (2652, 89, 73, 0x0638, 0x0D68),
        )
        self.assertEqual(
            tuple(_sha256(patched[index]) for index in (17, 18, 19)),
            (
                "f68dbae6a908826a625f1c4537a9317e575e4950b544fae235ebff2e4e9e6677",
                "9fb6ae79e2f864b2f79f10f06ddabd0d7526d788dd8278e2f094a77731f0fc45",
                "00faa0d0d3bf6b6e6fd4e393b7cec160ef05b75779431032ecb99dfd753c78ee",
            ),
        )
        self.assertEqual(
            tuple(len(patched[index]) for index in (17, 18, 19)),
            (136, 136, 396),
        )
        self.assertEqual(
            _sha256(patched_models),
            "1720f5af5e753aa89bcbb9d6032e9127576e6ceb314ec99ec58219e9047bcd24",
        )


class ServiceJunctionTerminalTests(unittest.TestCase):
    def test_authentic_terminal_assets_are_exact_and_preserve_alignment(
        self,
    ) -> None:
        spec = _spec(363)
        station = spec.service_junction_archive_station
        assert station is not None
        prepared = _prepared_clone(363)
        header = prepared.header
        graphics = prepared.graphics
        assert header is not None
        assert graphics is not None

        source_header, source_components = _load_components(
            WORK / spec.bundle_directory
        )
        models = prepared.components[MODEL_INDEX]

        self.assertEqual(
            (len(header), _sha256(header)),
            (
                832,
                "c5dd92f8b149eee4e8287b622d0cd70c730c82eb796115dc0642464d2df6a182",
            ),
        )
        self.assertEqual(
            (len(models), _sha256(models)),
            (
                9_904,
                "b756da8c20274bf8a6c3c136eafe63c73a830566b0c9aaefb56c5bf7db4f9d20",
            ),
        )
        self.assertEqual(struct.unpack_from("<H", header, 0x18C)[0], 27)
        self.assertEqual(len(header), 0x190 + 27 * 16)

        # Reader e17 is inserted exactly where the ATEL table is extended.
        # All eight native static nodes shift together to nodes 18..25, while
        # the authentic field-373 station remains a non-scripted final node 26.
        self.assertEqual(
            _actor_record(header, SERVICE_JUNCTION_STATION_READER_ENTITY),
            (0x01E0, 0, 0, 0, 0, 0, -150, 0),
        )
        self.assertEqual(
            _actor_record(header, SERVICE_JUNCTION_STATION_TARGET_NODE_INDEX),
            (0x0010, 0, 0x0A00, 0, -41, 105, -175, 10),
        )
        self.assertEqual(
            header[0x190 : 0x190 + 17 * 16],
            source_header[0x190 : 0x190 + 17 * 16],
        )
        self.assertEqual(
            header[0x190 + 18 * 16 : 0x190 + 26 * 16],
            source_header[0x190 + 17 * 16 : 0x190 + 25 * 16],
        )
        self.assertEqual(
            _actor_record(header, 18),
            (0x0010, 0, 0, 0, 0, 0, 0, 2),
        )

        before_models = _indexed_bundle_entries(source_components[MODEL_INDEX])
        after_models = _indexed_bundle_entries(models)
        self.assertEqual(len(before_models), 10)
        self.assertEqual(len(after_models), 11)
        # The complete native model inventory, especially door leaves 0/1,
        # remains byte-exact.  Only the appended authentic station is new.
        self.assertEqual(after_models[:10], before_models)

        authentic = after_models[SERVICE_JUNCTION_STATION_TARGET_MODEL_INDEX]
        self.assertEqual(
            (len(authentic), _sha256(authentic)),
            (
                2_524,
                "2466949bd495d1b8c4b150d4cff288e103111c33e63cd90779278482fdcc2041",
            ),
        )
        self.assertEqual(
            struct.unpack_from("<HHH", authentic, 0x12),
            (93, 85, 4),
        )
        self.assertEqual(
            struct.unpack_from("<hhh", authentic, 0x30),
            (-70, -258, -72),
        )
        self.assertEqual(
            struct.unpack_from("<hhh", authentic, 0x38),
            (14, -106, 12),
        )

        # Target 363 reuses target 727's exact retail station model.  The
        # geometry, U coordinates, and TPAGEs remain byte-identical; only the
        # atlas V coordinates move from 128..191 to 0..63 and its CLUT moves
        # from row 482 to free entries shared safely in native row 485.
        inner_models = _indexed_bundle_entries(
            _prepared_clone(727).components[MODEL_INDEX]
        )
        inner_station = inner_models[INNER_ACCESS_STATION_TARGET_MODEL_INDEX]
        self.assertEqual(
            _sha256(inner_station),
            INNER_ACCESS_STATION_RELOCATED_MODEL_SHA256,
        )
        inner_clut_offsets = tuple(
            offset
            for offset in range(0, len(inner_station) - 3, 4)
            if struct.unpack_from("<I", inner_station, offset)[0] >> 24 == 0xC8
        )
        self.assertEqual(len(inner_clut_offsets), 1)
        clut_offset = inner_clut_offsets[0]
        self.assertEqual(
            struct.unpack_from("<H", inner_station, clut_offset)[0],
            INNER_ACCESS_STATION_TARGET_CLUT,
        )
        self.assertEqual(
            struct.unpack_from("<H", authentic, clut_offset)[0],
            SERVICE_JUNCTION_STATION_TARGET_CLUT,
        )
        self.assertEqual(
            tuple(
                struct.unpack_from("<H", authentic, offset)[0]
                for offset in range(0, len(authentic) - 3, 4)
                if struct.unpack_from("<I", authentic, offset)[0] >> 24
                == 0xC4
            ),
            SERVICE_JUNCTION_STATION_TARGET_TPAGES,
        )
        changed_offsets = {
            offset
            for offset, (old, new) in enumerate(
                zip(inner_station, authentic, strict=True)
            )
            if old != new
        }
        self.assertEqual(len(changed_offsets), 337)
        changed_offsets -= {clut_offset, clut_offset + 1}
        self.assertEqual(len(changed_offsets), 335)
        self.assertTrue(
            all(
                inner_station[offset] - authentic[offset] == 128
                for offset in changed_offsets
            )
        )

        self.assertEqual(
            (len(graphics), _sha256(graphics)),
            (
                106_496,
                "0f90479813717a6aa250691ec85f02b2c3fb009aed9adbab003212a80bda2561",
            ),
        )

        script = prepared.components[SCRIPT_INDEX]
        dialogue = prepared.components[7]
        self.assertEqual(
            (len(script), _sha256(script)),
            (
                1_995,
                "1d11ad410628d1d7e1e64a5885144f8529171188cb6e626bafcc2e79af688f30",
            ),
        )
        self.assertEqual(
            (len(dialogue), _sha256(dialogue)),
            (
                483,
                "a0eff0db6e7485927a1b973fc86671c496b574e552b3acb7dcdb699d842c3299",
            ),
        )
        self.assertEqual(
            (len(prepared.bundle), _sha256(prepared.bundle)),
            (
                21_416,
                "bfed6eb354d18369e3053ac2989870c23707bf0527bbc7c87956e3810c0f652f",
            ),
        )
        duty_log = " ".join(
            parse_dialogue(dialogue).blocks[4].text.replace("<New>", " ").split()
        )
        for phrase in (
            "PRESSURE-LOCK STATION",
            "ARCHIVED DUTY LOG",
            "Command line: no response.",
            "Pressure lock: sealed.",
            "Release authorization: pending.",
            "personnel still in the vestibule.",
        ):
            self.assertIn(phrase, duty_log)

    def test_registered_mim_carrier_and_station_palette_remap_are_lossless(
        self,
    ) -> None:
        spec = _spec(363)
        prepared = _prepared_clone(363)
        header = prepared.header
        graphics = prepared.graphics
        assert header is not None
        assert graphics is not None
        source_header, source_components = _load_components(
            WORK / spec.bundle_directory
        )
        source_graphics = (WORK / spec.graphics_file).read_bytes()

        self.assertEqual(struct.unpack_from("<4H", source_header), (832, 0, 0, 1))
        self.assertEqual(header[:8], source_header[:8])
        self.assertEqual(source_components[0], struct.pack("<I", 0))
        self.assertEqual(source_components[SPRITE_INDEX], struct.pack("<I", 0))

        old_vram, old_rectangles = _reconstruct_graphics_vram(
            source_graphics,
            label="Retail field 363",
        )
        new_vram, new_rectangles = _reconstruct_graphics_vram(
            graphics,
            label="Target 363 authentic station",
        )
        expected_rectangles = (
            (0, 480, 256, 9),
            (336, 0, 72, 222),
            (832, 0, 64, 144),
            (408, 0, 27, 239),
            (320, 0, 8, 254),
            (328, 0, 8, 250),
            (440, 0, 10, 148),
            (435, 0, 5, 196),
            (450, 94, 5, 54),
        )
        self.assertEqual(
            SERVICE_JUNCTION_GRAPHICS_RECTANGLES,
            expected_rectangles,
        )
        self.assertEqual(old_rectangles, expected_rectangles)
        self.assertEqual(new_rectangles, expected_rectangles)
        self.assertEqual(len(graphics), len(source_graphics))
        self.assertEqual(
            _sha256(graphics),
            SERVICE_JUNCTION_STATION_OUTPUT_GRAPHICS_SHA256,
        )

        source_atlas, station_palette = _build_legacy_station_atlas(
            (WORK / "audit_zeboim_cd1" / "1353.bin").read_bytes(),
            (
                WORK
                / "reference_fields"
                / "cd1_cloning"
                / "1953.bin"
            ).read_bytes(),
        )
        atlas = _graphics_rows(new_vram, SERVICE_JUNCTION_STATION_TEXTURE_RECT)
        self.assertEqual(
            (len(source_atlas), _sha256(source_atlas)),
            (5_120, SERVICE_JUNCTION_STATION_ATLAS_SHA256),
        )
        self.assertEqual(
            (len(station_palette), _sha256(station_palette)),
            (512, SERVICE_JUNCTION_STATION_PALETTE_SHA256),
        )
        self.assertEqual(
            (len(atlas), _sha256(atlas)),
            (5_120, SERVICE_JUNCTION_STATION_REMAPPED_ATLAS_SHA256),
        )
        self.assertNotEqual(
            atlas,
            _graphics_rows(old_vram, SERVICE_JUNCTION_STATION_TEXTURE_RECT),
        )
        self.assertEqual(
            _graphics_rows(new_vram, (872, 0, 24, 64)),
            _graphics_rows(old_vram, (872, 0, 24, 64)),
        )
        self.assertEqual(
            _graphics_rows(new_vram, (832, 64, 64, 80)),
            _graphics_rows(old_vram, (832, 64, 64, 80)),
        )

        station_sources = tuple(sorted(set(source_atlas)))
        self.assertEqual(
            (len(station_sources), station_sources[0], station_sources[-1]),
            (SERVICE_JUNCTION_STATION_USED_INDEX_COUNT, 2, 255),
        )
        native_row485 = set(SERVICE_JUNCTION_NATIVE_ROW485_USED_INDICES)
        expected_destinations = tuple(
            index for index in range(256) if index not in native_row485
        )[: len(station_sources)]
        index_mapping = dict(
            zip(station_sources, expected_destinations, strict=True)
        )
        self.assertEqual(
            atlas,
            bytes(index_mapping[source] for source in source_atlas),
        )
        self.assertEqual(
            len(set(index_mapping.values())),
            SERVICE_JUNCTION_STATION_USED_INDEX_COUNT,
        )
        self.assertFalse(set(index_mapping.values()) & native_row485)

        old_row485 = _graphics_rows(
            old_vram, SERVICE_JUNCTION_STATION_TARGET_PALETTE_RECT
        )
        new_row485 = _graphics_rows(
            new_vram, SERVICE_JUNCTION_STATION_TARGET_PALETTE_RECT
        )
        for index in native_row485:
            self.assertEqual(
                new_row485[index * 2 : index * 2 + 2],
                old_row485[index * 2 : index * 2 + 2],
            )
        for source, target in index_mapping.items():
            self.assertEqual(
                new_row485[target * 2 : target * 2 + 2],
                station_palette[source * 2 : source * 2 + 2],
            )
        self.assertEqual(
            _graphics_rows(new_vram, SERVICE_JUNCTION_NATIVE_ROW488_RECT),
            _graphics_rows(old_vram, SERVICE_JUNCTION_NATIVE_ROW488_RECT),
        )

        # The native door's 26-by-43 indexed texture footprint remains exact,
        # as does its row-488 palette above.  Together with byte-identical
        # models 0/1, this guards every native door rendering input.
        native_door_texture = bytearray()
        patched_door_texture = bytearray()
        for row in range(43):
            start = (196 + row) * 1024 * 2 + 384 * 2 + 48
            native_door_texture.extend(old_vram[start : start + 26])
            patched_door_texture.extend(new_vram[start : start + 26])
        self.assertEqual(len(native_door_texture), 1_118)
        self.assertEqual(patched_door_texture, native_door_texture)

        # Outside the remapped atlas and row 485, the complete word-addressed
        # VRAM replay is exact; row 488 and the door texture are not masked.
        masked_old = bytearray(old_vram)
        masked_new = bytearray(new_vram)

        def mask_word_rect(x: int, y: int, width: int, height: int) -> None:
            for row in range(height):
                start = ((y + row) * 1024 + x) * 2
                end = start + width * 2
                masked_old[start:end] = bytes(end - start)
                masked_new[start:end] = bytes(end - start)

        mask_word_rect(*SERVICE_JUNCTION_STATION_TEXTURE_RECT)
        mask_word_rect(*SERVICE_JUNCTION_STATION_TARGET_PALETTE_RECT)
        self.assertEqual(masked_new, masked_old)

        # The x832 upload was retail actor bank zero, not anonymous free VRAM.
        # Its only local-bank users remain hidden: e12 initializes bank zero
        # solely as an invisible collider; the party entities use
        # INIT_ENTITY_PC; and the remaining BC entities are header-hidden or
        # stay 3-D models.
        script = AtelScript(prepared.components[SCRIPT_INDEX])
        collider_pc = script.get_script_pointer(
            SERVICE_JUNCTION_STATION_COLLIDER_ENTITY,
            0,
        )
        collider_body = _pointed_script_body(script, collider_pc)
        self.assertEqual(collider_body[0], 0x0B)
        self.assertIn(b"\x23\x2A\x00", collider_body)
        self.assertTrue(
            all(
                _actor_record(header, entity)[0] & 0x20
                for entity in (
                    0,
                    SERVICE_JUNCTION_STATION_COLLIDER_ENTITY,
                    13,
                    14,
                    17,
                )
            )
        )
        self.assertTrue(
            all(
                _actor_record(header, entity)[0] & 0x40 == 0
                for entity in (15, 16)
            )
        )
        self.assertTrue(
            all(
                script.bytecode[script.get_script_pointer(entity, 0)] == 0x16
                for entity in range(1, 12)
            )
        )
        self.assertTrue(
            all(
                script.bytecode[script.get_script_pointer(entity, 0)] == 0xBC
                for entity in (0, 13, 14, 17)
            )
        )

    def test_e12_is_solid_only_and_e17_owns_facing_dialogue_four(self) -> None:
        spec = _spec(363)
        station = spec.service_junction_archive_station
        assert station is not None
        prepared = _prepared_clone(363)
        header = prepared.header
        assert header is not None
        script = AtelScript(prepared.components[SCRIPT_INDEX])

        self.assertEqual(script.entity_count, 18)
        self.assertEqual(struct.unpack_from("<H", header, 0x18C)[0], 27)
        self.assertEqual(
            (
                station.collider_entity,
                station.reader_entity,
                SERVICE_JUNCTION_STATION_COLLIDER_ENTITY,
                SERVICE_JUNCTION_STATION_READER_ENTITY,
            ),
            (12, 17, 12, 17),
        )

        collider_init = script.get_script_pointer(station.collider_entity, 0)
        self.assertEqual(
            _pointed_script_body(script, collider_init),
            _solid_station_controller_init(
                *SERVICE_JUNCTION_STATION_COLLIDER_POSITION,
                requires_facing=False,
                collision_operand=SERVICE_JUNCTION_STATION_COLLISION_OPERAND,
                interaction_enabled=False,
            ),
        )
        self.assertEqual(
            tuple(
                script.get_script_pointer(station.collider_entity, index)
                for index in range(1, 30)
            ),
            (0x01A6, 0x01A5, 0x01A6) + (0,) * 26,
        )
        self.assertEqual(
            script.bytecode[script.get_script_pointer(station.collider_entity, 2)],
            0,
        )
        self.assertEqual(
            tuple(
                script.get_script_pointer(station.collider_entity, index)
                for index in (30, 31)
            ),
            tuple(script.get_script_pointer(2, index) for index in (30, 31)),
        )

        reader_init = script.get_script_pointer(station.reader_entity, 0)
        self.assertEqual(
            _pointed_script_body(script, reader_init),
            _static_door_controller_init(
                *SERVICE_JUNCTION_STATION_READER_POSITION,
                requires_facing=True,
                interaction_half_width=SERVICE_JUNCTION_STATION_READER_HALF_WIDTH,
            ),
        )
        action = _pointed_script_body(
            script,
            script.get_script_pointer(station.reader_entity, 2),
        )
        self.assertIn(b"\xF5\x04\x00\x00", action)
        self.assertTrue(action.endswith(b"\xFE\x53\x00"))
        reader_stop_pointers = {
            script.get_script_pointer(station.reader_entity, index)
            for index in range(32)
            if index not in (0, 2)
        }
        self.assertEqual(len(reader_stop_pointers), 1)
        self.assertEqual(script.bytecode[reader_stop_pointers.pop()], 0)

    def test_terminal_frontage_and_reader_match_the_connected_walkmesh(self) -> None:
        spec = _spec(363)
        station = spec.service_junction_archive_station
        assert station is not None
        prepared = _prepared_clone(363)
        walkmesh = prepared.components[1]

        self.assertEqual(spec.static_door_exits, ())
        self.assertEqual(spec.field_entry_additions, ())
        self.assertIsNone(spec.field_entry_resume_pc)
        self.assertNotIn(365, {item.target_field for item in CLONES})
        self.assertFalse(
            any(
                contract.source_field == 365
                or contract.destination_field == 365
                for contract in ARRIVAL_CONTINUITY_CONTRACTS
            )
        )

        for label, point, triangle, expected_crosses in (
            (
                "collider",
                SERVICE_JUNCTION_STATION_COLLIDER_POSITION,
                SERVICE_JUNCTION_STATION_COLLIDER_TRIANGLE,
                (-1782, -931, -878),
            ),
            (
                "reader",
                SERVICE_JUNCTION_STATION_READER_POSITION,
                SERVICE_JUNCTION_STATION_READER_TRIANGLE,
                (-4620, -2527, -2163),
            ),
            (
                "approach",
                SERVICE_JUNCTION_STATION_APPROACH_POSITION,
                SERVICE_JUNCTION_STATION_APPROACH_TRIANGLE,
                (-497, -4757, -4189),
            ),
        ):
            with self.subTest(point=label):
                triangle_offset = 0x28 + triangle * 14
                vertex_indices = struct.unpack_from(
                    "<3H", walkmesh, triangle_offset
                )
                vertices = tuple(
                    struct.unpack_from("<hhhh", walkmesh, 0x039C + index * 8)
                    for index in vertex_indices
                )
                point_x, point_z = point
                crosses = tuple(
                    (end[0] - start[0]) * (point_z - start[2])
                    - (end[2] - start[2]) * (point_x - start[0])
                    for start, end in zip(
                        vertices,
                        (*vertices[1:], vertices[0]),
                        strict=True,
                    )
                )
                self.assertEqual(crosses, expected_crosses)
                self.assertTrue(all(value < 0 for value in crosses))

        collider_x, collider_z = SERVICE_JUNCTION_STATION_COLLIDER_POSITION
        collider_reach = SERVICE_JUNCTION_STATION_COLLISION_OPERAND * 2 + 16
        self.assertEqual(collider_reach, 56)

        minimum_x, maximum_x, minimum_y, maximum_y, minimum_z, maximum_z = (
            SERVICE_JUNCTION_STATION_WORLD_BOUNDS
        )
        self.assertEqual(
            (
                minimum_x,
                maximum_x,
                minimum_y,
                maximum_y,
                minimum_z,
                maximum_z,
            ),
            (
                -39.58578643762691,
                38.903066274079876,
                -153.0,
                -1.0,
                -227.32590180780451,
                -150.25126265847084,
            ),
        )

        approach_x, approach_z = SERVICE_JUNCTION_STATION_APPROACH_POSITION
        reader_x, reader_z = SERVICE_JUNCTION_STATION_READER_POSITION
        reader_reach = SERVICE_JUNCTION_STATION_READER_HALF_WIDTH * 2 + 16
        self.assertEqual(reader_reach, 24)
        self.assertLessEqual(abs(approach_x - reader_x), reader_reach)
        self.assertLessEqual(abs(approach_z - reader_z), reader_reach)
        self.assertEqual(abs(approach_z - collider_z) - collider_reach, 3)
        self.assertAlmostEqual(reader_z - maximum_z, 0.25126265847084)
        self.assertAlmostEqual(approach_z - maximum_z, 20.25126265847084)
        self.assertGreaterEqual(
            SERVICE_JUNCTION_STATION_COLLISION_OPERAND * 2,
            max(
                abs(minimum_x - collider_x),
                abs(maximum_x - collider_x),
                abs(minimum_z - collider_z),
                abs(maximum_z - collider_z),
            ),
        )
        self.assertEqual((collider_x, collider_z), (0, -189))
        self.assertEqual((reader_x, reader_z), (0, -150))
        self.assertEqual((approach_x, approach_z), (0, -130))
        self.assertEqual(SERVICE_JUNCTION_STATION_SCREEN_NORMAL, (0, 0, 1))
        self.assertEqual(SERVICE_JUNCTION_STATION_PLACEMENT, (-41, 105, -175))
        self.assertEqual(SERVICE_JUNCTION_STATION_Y_ROTATION, 0x0A00)


class StaticDoorScriptTests(unittest.TestCase):
    def test_helpers_use_exact_audited_finite_sliding_routines(self) -> None:
        retail_fe1b = {
            (726, 0x017C): bytes.fromhex(
                "37 04 04 02 04 04 0E 00 43 97 01 C6 "
                "FE 1B 02 00 00 00 26 00 80 3C 04 04 01 7F 01 00"
            ),
            (726, 0x019D): bytes.fromhex(
                "37 06 04 02 06 04 0E 00 43 B8 01 C6 "
                "FE 1B 02 00 00 00 26 00 80 3C 06 04 01 A0 01 00"
            ),
            (726, 0x01BE): bytes.fromhex(
                "37 08 04 02 08 04 0E 00 43 D9 01 C6 "
                "FE 1B 02 00 00 00 26 00 80 3C 08 04 01 C1 01 00"
            ),
        }
        self.assertEqual(
            {
                field: STATIC_DOOR_SLIDE_POINTERS[field]
                for field in (726, 376)
            },
            {
                726: frozenset((0x017C, 0x019D, 0x01BE)),
                376: frozenset((0x027D, 0x0356)),
            },
        )
        for (target_field, pointer), exact_body in retail_fe1b.items():
            with self.subTest(field=target_field, pointer=pointer):
                source, transformed = _script_pair(target_field)
                self.assertEqual(
                    source.bytecode[pointer : pointer + len(exact_body)],
                    exact_body,
                )
                self.assertEqual(
                    transformed.bytecode[pointer : pointer + len(exact_body)],
                    exact_body,
                )
                self.assertIn(b"\xFE\x1B", exact_body)

        source, transformed = _script_pair(376)
        self.assertEqual(source.bytecode_size, 0x027C)
        for entity, pointer, delta_z in (
            (15, 0x027D, 2),
            (16, 0x0356, -2),
        ):
            with self.subTest(field=376, entity=entity):
                expected_body = (
                    b"".join(
                        b"\x19"
                        + struct.pack("<hh", 0, delta_z * step)
                        + b"\xC0\x26\x00\x80"
                        for step in range(1, 25)
                    )
                    + b"\x00"
                )
                self.assertEqual(len(expected_body), 217)
                self.assertEqual(
                    transformed.get_script_pointer(entity, 4),
                    pointer,
                )
                self.assertEqual(
                    _pointed_script_body(transformed, pointer),
                    expected_body,
                )
                self.assertEqual(expected_body.count(b"\x19"), 24)
                self.assertNotIn(b"\xFE\x1B", expected_body)

    def test_static_controller_and_helper_inventory_matches_extended_atel(
        self,
    ) -> None:
        for target_field, old_count, new_count in (
            (363, 17, 18),
            (726, 19, 33),
            (376, 14, 28),
        ):
            with self.subTest(field=target_field):
                source, transformed = _script_pair(target_field)
                spec = _spec(target_field)
                self.assertEqual(source.entity_count, old_count)
                self.assertEqual(transformed.entity_count, new_count)

                controllers = {
                    door.controller_entity for door in spec.static_door_exits
                }
                helpers = {
                    helper.entity
                    for door in spec.static_door_exits
                    for helper in door.helpers
                }
                extended_entities = controllers | helpers
                if spec.defense_bay_lift_exit is not None:
                    extended_entities |= {
                        spec.defense_bay_lift_exit.controller_entity,
                        *spec.defense_bay_lift_exit.helper_entities,
                    }
                extended_entities |= {
                    terminal.entity
                    for terminal in spec.defense_archive_record_terminals
                }
                if spec.defense_archive_video_event is not None:
                    extended_entities.add(
                        spec.defense_archive_video_event.disk_entity
                    )
                    extended_entities.add(
                        spec.defense_archive_video_event.screen_entity
                    )
                if spec.service_junction_archive_station is not None:
                    extended_entities.add(
                        spec.service_junction_archive_station.reader_entity
                    )
                self.assertEqual(
                    extended_entities,
                    set(range(old_count, new_count)),
                )
                self.assertFalse(controllers & helpers)

                for door in spec.static_door_exits:
                    init = transformed.get_script_pointer(
                        door.controller_entity, 0
                    )
                    self.assertEqual(
                        _pointed_script_body(transformed, init),
                        _static_door_controller_init(
                            door.controller_x,
                            door.controller_z,
                            requires_facing=door.requires_facing,
                            interaction_half_width=door.interaction_half_width,
                        ),
                    )
                    action = transformed.get_script_pointer(
                        door.controller_entity, 2
                    )
                    collision = transformed.get_script_pointer(
                        door.controller_entity, 3
                    )
                    body = _pointed_script_body(transformed, action)
                    self.assertNotEqual(action, collision)
                    self.assertEqual(transformed.bytecode[collision], 0)
                    party_opcode = b"\x09\xFF" if door.opens_from_panel else b"\x07\xFF"
                    party_launch = body.index(party_opcode)
                    self.assertTrue(body[party_launch + 2] & 0x20)
                    if door.opens_from_panel:
                        # The nearby record console has already opened these
                        # leaves with the camera and sound reveal.  The door
                        # frontage now performs only the bounded synchronous
                        # party crossing and must not replay either helper.
                        self.assertEqual(body[party_launch + 3], 0x98)
                        self.assertNotIn(b"\x74\x77\x80", body)
                        for helper in door.helpers:
                            self.assertNotIn(
                                b"\x07" + bytes((helper.entity, 0x24)),
                                body,
                            )
                    else:
                        self.assertEqual(
                            body[party_launch + 3 : party_launch + 8],
                            b"\xFE\x54\x74\x77\x80",
                        )
                    if target_field == 376:
                        self.assertFalse(door.requires_facing)
                        self.assertEqual(door.interaction_half_width, 0x30)
                        controller_body = _pointed_script_body(
                            transformed,
                            init,
                        )
                        self.assertIn(
                            bytes.fromhex("F8 07 04 00"),
                            controller_body,
                        )
                        self.assertIn(
                            bytes.fromhex("18 30 30 64 00"),
                            controller_body,
                        )
                        self.assertEqual(
                            body[:6],
                            bytes.fromhex("02 FA 03 04 00 46"),
                        )
                        self.assertIn(
                            bytes.fromhex("F5 0A 00 00"),
                            body,
                        )
                    else:
                        self.assertEqual(party_launch, 0)
                    self.assertIn(
                        _change_field(door.new_field, door.new_parameter),
                        body,
                    )
                    self.assertTrue(body.endswith(b"\x00"))

                    for helper in door.helpers:
                        helper_call = b"\x07" + bytes((helper.entity, 0x24))
                        if door.opens_from_panel:
                            self.assertNotIn(helper_call, body)
                        else:
                            self.assertIn(helper_call, body)
                        self.assertNotIn(
                            b"\x09" + bytes((helper.entity, 0x24)),
                            body,
                        )
                        helper_update = transformed.get_script_pointer(
                            helper.entity, 1
                        )
                        if (
                            target_field == 376
                            and helper.entity in (16, 17, 18, 19)
                        ):
                            # Missile Command reuses available architectural
                            # hosts as finite automatic script-1 workers;
                            # their collision/action roles stay byte-exact
                            # below.
                            self.assertNotEqual(helper_update, collision)
                            self.assertTrue(
                                _pointed_script_body(
                                    transformed, helper_update
                                ).endswith(b"\x00")
                            )
                        else:
                            self.assertEqual(helper_update, collision)
                        self.assertEqual(
                            transformed.get_script_pointer(helper.entity, 2),
                            collision,
                        )
                        self.assertEqual(
                            transformed.get_script_pointer(helper.entity, 3),
                            collision,
                        )
                        helper_init = transformed.get_script_pointer(
                            helper.entity, 0
                        )
                        helper_init_body = _pointed_script_body(
                            transformed, helper_init
                        )
                        if door.opens_from_panel:
                            self.assertTrue(
                                helper_init_body.startswith(
                                    bytes.fromhex("BC 02 FA 03 04 00 46")
                                )
                            )
                            self.assertTrue(helper_init_body.endswith(b"\xC0\x2A\x00"))
                        else:
                            self.assertEqual(helper_init_body, b"\xBC\x2A\x00")
                        animation = transformed.get_script_pointer(
                            helper.entity, 4
                        )
                        self.assertEqual(
                            animation,
                            (
                                {
                                    15: 0x027D,
                                    16: 0x0356,
                                }[helper.entity]
                                if helper.animation_pointer is None
                                else helper.animation_pointer
                            ),
                        )
                        animation_body = _pointed_script_body(
                            transformed, animation
                        )
                        if helper.animation_pointer is None:
                            self.assertTrue(animation_body.startswith(b"\x19"))
                            self.assertEqual(animation_body.count(b"\x19"), 24)
                            self.assertNotIn(b"\xFE\x1B", animation_body)
                        else:
                            self.assertTrue(animation_body.startswith(b"\x37"))
                            self.assertIn(b"\xFE\x1B", animation_body)

    def test_field_726_gray_panel_controller_dispatches_its_room_action(
        self,
    ) -> None:
        """Offset e20/e22 controllers must not reject X by facing direction."""

        _source, transformed = _script_pair(726)
        spec = _spec(726)
        door = next(
            item
            for item in spec.static_door_exits
            if item.controller_entity == 22
        )
        self.assertEqual(
            (
                door.controller_x,
                door.controller_z,
                door.movement_x,
                door.movement_z,
                door.new_field,
                door.new_parameter,
                door.requires_facing,
            ),
            (-264, -540, -264, -540, 369, 0, False),
        )
        self.assertEqual(len(door.helpers), 1)
        helper = door.helpers[0]
        self.assertEqual(
            (
                helper.entity,
                helper.x,
                helper.z,
                helper.model_index,
                helper.animation_pointer,
            ),
            (29, -302, -485, 8, 0x01BE),
        )
        action = transformed.get_script_pointer(22, 2)
        self.assertEqual(
            transformed.get_script_pointer(helper.entity, 2),
            transformed.get_script_pointer(22, 3),
        )
        body = _pointed_script_body(transformed, action)
        self.assertIn(b"\x07\x1D\x24", body)
        self.assertIn(_change_field(369, 0), body)
        controller_init = transformed.get_script_pointer(22, 0)
        controller_body = _pointed_script_body(
            transformed,
            controller_init,
        )
        self.assertNotIn(b"\xF8\x03\x04\x00", controller_body)
        self.assertIn(b"\xF8\x07\x04\x00", controller_body)
        self.assertEqual(
            {
                other.controller_entity
                for other in spec.static_door_exits
                if not other.requires_facing
            },
            {20, 22},
        )
        for other in spec.static_door_exits:
            if other.controller_entity in (20, 22):
                continue
            self.assertTrue(other.requires_facing)
            other_init = transformed.get_script_pointer(
                other.controller_entity,
                0,
            )
            self.assertIn(
                b"\xF8\x03\x04\x00",
                _pointed_script_body(transformed, other_init),
            )

    def test_field_726_entry_prefix_relocates_every_pointer_and_local_jump(
        self,
    ) -> None:
        source, transformed = _script_pair(726)
        spec = _spec(726)
        overwritten_start = 0x000F
        resume_pc = 0x0047

        arrival_contracts = {
            contract.destination_parameter: contract
            for contract in ARRIVAL_CONTINUITY_CONTRACTS
            if contract.destination_field == 726
        }
        final_additions = tuple(
            FieldEntryAddition(
                entry.x,
                entry.z,
                entry.walkmesh,
                arrival_contracts[parameter].resolved_camera_direction,
                arrival_contracts[parameter].inward_direction,
            )
            for parameter, entry in enumerate(
                spec.field_entry_additions,
                start=2,
            )
        )
        packed_additions = b"".join(
            struct.pack(
                "<hhBBB",
                entry.x,
                entry.z,
                entry.walkmesh,
                entry.camera_direction,
                entry.actor_direction,
            )
            for entry in final_additions
        )
        self.assertEqual(len(packed_additions), resume_pc - overwritten_start)
        self.assertEqual(
            transformed.bytecode[overwritten_start:resume_pc],
            packed_additions,
        )

        affected = (
            (0, 0, 0x000F, 0x002F),
            (0, 1, 0x002F, 0x0030),
            (0, 2, 0x0030, 0x0031),
            (1, 0, 0x0031, 0x0039),
            (1, 1, 0x0039, 0x003B),
            (1, 2, 0x003B, 0x003C),
            (2, 0, 0x003C, 0x0044),
            (2, 1, 0x0044, 0x0046),
            (2, 2, 0x0046, 0x0047),
        )
        relocated_pointers = []
        for entity, script_index, old_pointer, old_end in affected:
            with self.subTest(entity=entity, script=script_index):
                self.assertEqual(
                    source.get_script_pointer(entity, script_index),
                    old_pointer,
                )
                new_pointer = transformed.get_script_pointer(
                    entity, script_index
                )
                relocated_pointers.append(new_pointer)
                self.assertGreaterEqual(new_pointer, resume_pc)

                expected = bytearray(source.bytecode[old_pointer:old_end])
                if (entity, script_index) == (0, 0):
                    # The release's movement timer is enabled before this
                    # prefix is copied into its relocated trampoline.
                    expected[12:17] = bytes.fromhex("F7 84 83 01 80")
                    gameprogress_target = new_pointer + (
                        0x002B - old_pointer
                    )
                    expected[20:22] = struct.pack(
                        "<H",
                        gameprogress_target,
                    )
                    self.assertEqual(
                        transformed.bytecode[
                            gameprogress_target : gameprogress_target + 3
                        ],
                        bytes.fromhex("75 1A 80"),
                    )
                    jump_offset = 25
                    relocated_target = new_pointer + (0x002E - old_pointer)
                    expected[jump_offset : jump_offset + 3] = (
                        b"\x01" + struct.pack("<H", relocated_target)
                    )
                    self.assertEqual(
                        transformed.bytecode[relocated_target],
                        0,
                    )
                self.assertEqual(
                    transformed.bytecode[
                        new_pointer : new_pointer + len(expected)
                    ],
                    expected,
                )

        self.assertEqual(relocated_pointers, sorted(relocated_pointers))
        for entity in range(transformed.entity_count):
            for script_index in range(32):
                pointer = transformed.get_script_pointer(entity, script_index)
                self.assertFalse(
                    overwritten_start <= pointer < resume_pc,
                    f"e{entity}/s{script_index} still points into entry records",
                )


class ArchiveAnnexContractTests(unittest.TestCase):
    def test_five_launch_hall_annex_doors_have_exact_reciprocal_contracts_and_entries(
        self,
    ) -> None:
        # Runtime collision audit: the controller extends 60 map units from
        # its center and the leader contributes another 16. A reciprocal
        # return therefore needs at least one axis strictly beyond 76 units.
        minimum_controller_clearance = 60 + 16
        contracts = {
            (contract.field, contract.entity): contract
            for contract in VISIBLE_DOOR_CONTRACTS
        }
        arrivals = {
            (
                contract.source_field,
                contract.destination_field,
                contract.destination_parameter,
            ): contract
            for contract in ARRIVAL_CONTINUITY_CONTRACTS
        }

        self.assertEqual(len(DIRECT_ANNEX_CASES), 5)
        for (
            origin,
            controller,
            helpers,
            annex,
            return_parameter,
            return_entry,
        ) in DIRECT_ANNEX_CASES:
            with self.subTest(origin=origin, annex=annex):
                annex_controller = 22
                annex_helpers = (23,)
                arrival_entry = FieldEntryAddition(76, 141, 0)
                arrival_direction = 5
                patched_arrival_entry = FieldEntryAddition(
                    76, 141, 0, 5, 5
                )
                outward = contracts[(origin, controller)]
                inward = contracts[(annex, annex_controller)]
                self.assertEqual(outward.helper_entities, helpers)
                self.assertEqual(
                    (
                        outward.destination_field,
                        outward.destination_parameter,
                        outward.reciprocal_field,
                        outward.reciprocal_entity,
                    ),
                    (annex, 0, annex, annex_controller),
                )
                self.assertEqual(inward.helper_entities, annex_helpers)
                self.assertEqual(
                    (
                        inward.destination_field,
                        inward.destination_parameter,
                        inward.reciprocal_field,
                        inward.reciprocal_entity,
                    ),
                    (origin, return_parameter, origin, controller),
                )

                into_annex = arrivals[(origin, annex, 0)]
                back_to_origin = arrivals[
                    (annex, origin, return_parameter)
                ]
                self.assertEqual(
                    into_annex.expected_entry,
                    arrival_entry,
                )
                self.assertEqual(
                    into_annex.inward_direction,
                    arrival_direction,
                )
                self.assertEqual(
                    into_annex.resolved_camera_direction,
                    patched_arrival_entry.camera_direction,
                )
                self.assertEqual(
                    FieldEntryAddition(
                        back_to_origin.expected_entry.x,
                        back_to_origin.expected_entry.z,
                        back_to_origin.expected_entry.walkmesh,
                        back_to_origin.resolved_camera_direction,
                        back_to_origin.inward_direction,
                    ),
                    return_entry,
                )

                _annex_source, annex_script = _script_pair(annex)
                _origin_source, origin_script = _script_pair(origin)
                origin_spec = _spec(origin)
                origin_door = next(
                    door
                    for door in origin_spec.static_door_exits
                    if door.controller_entity == controller
                )
                self.assertGreater(
                    max(
                        abs(return_entry.x - origin_door.controller_x),
                        abs(return_entry.z - origin_door.controller_z),
                    ),
                    minimum_controller_clearance,
                    "return entry overlaps controller + leader collision",
                )
                self.assertEqual(
                    _read_field_entry(annex_script.to_bytes(), 0),
                    patched_arrival_entry,
                )
                self.assertEqual(
                    _read_field_entry(
                        origin_script.to_bytes(), return_parameter
                    ),
                    return_entry,
                )

    def test_source_378_annexes_use_both_archive_terminals_and_native_door(
        self,
    ) -> None:
        source_378_cases = ANNEX_RETURN_CASES
        self.assertEqual(len(source_378_cases), 6)
        for origin, annex, return_parameter in source_378_cases:
            with self.subTest(annex=annex):
                source, transformed = _script_pair(annex)
                self.assertEqual(source.entity_count, 24)
                self.assertEqual(transformed.entity_count, 24)

                # Released field 378's entity-15 nanoreactor update is no
                # longer live in a standalone archive room.
                self.assertEqual(source.get_script_pointer(15, 1), 0x035A)
                self.assertEqual(
                    transformed.get_script_pointer(15, 1),
                    0x03B5,
                )
                self.assertEqual(transformed.bytecode[0x03B5], 0)

                # Entity 13 controls the desk station and entity 14 controls
                # the distinct hanging terminal. Both props carry repeatable
                # mail in each lore-only annex. Target 368 is the deliberate
                # exception: its desk station remains the rail switch while
                # the hanging terminal carries that room's mail.
                self.assertEqual(source.get_script_pointer(13, 2), 0x02E6)
                self.assertEqual(
                    tuple(
                        source.get_script_pointer(14, index)
                        for index in range(4)
                    ),
                    (0x030F, 0x0312, 0x0313, 0x0314),
                )
                if annex == 368:
                    main_init = transformed.get_script_pointer(13, 0)
                    self.assertEqual(
                        _pointed_script_body(transformed, main_init),
                        _static_door_controller_init(
                            45,
                            -42,
                            requires_facing=False,
                            interaction_half_width=0x1E,
                        ),
                    )
                    main_console = transformed.get_script_pointer(13, 2)
                    main_body = _pointed_script_body(
                        transformed,
                        main_console,
                    )
                    self.assertIn(b"\x3A\xFE\x03\x01\x00\x40", main_body)
                    self.assertIn(b"\x74\x50\x80", main_body)
                    self.assertIn(b"\xF5\x00\x00\x00", main_body)
                    archive_terminals = (
                        (14, -124, -25, 0x08, b"\xF5\x01\x00\x00"),
                    )
                else:
                    self.assertEqual(
                        tuple(
                            transformed.get_script_pointer(13, index)
                            for index in (1, 3)
                        ),
                        (0x02E5, 0x030E),
                    )
                    archive_terminals = (
                        (13, 45, -42, 0x1E, b"\xF5\x01\x00\x00"),
                        (14, -124, -25, 0x08, b"\xF5\x00\x00\x00"),
                    )

                for entity, x, z, interaction_half_width, dialogue in archive_terminals:
                    with self.subTest(annex=annex, terminal=entity):
                        init = transformed.get_script_pointer(entity, 0)
                        self.assertEqual(
                            _pointed_script_body(transformed, init),
                            _static_door_controller_init(
                                x,
                                z,
                                requires_facing=False,
                                interaction_half_width=interaction_half_width,
                            ),
                        )
                        action = transformed.get_script_pointer(entity, 2)
                        body = _pointed_script_body(transformed, action)
                        self.assertIn(dialogue, body)
                        self.assertTrue(
                            body.endswith(b"\x9C\xFE\x53\x00")
                        )
                        update = transformed.get_script_pointer(entity, 1)
                        collision = transformed.get_script_pointer(entity, 3)
                        self.assertEqual(transformed.bytecode[update], 0)
                        self.assertEqual(transformed.bytecode[collision], 0)

                # The one architectural door remains native, audible,
                # animated, X-only, and returns to its matching origin entry.
                door = transformed.get_script_pointer(22, 2)
                collision = transformed.get_script_pointer(22, 3)
                door_body = _pointed_script_body(transformed, door)
                self.assertEqual(transformed.bytecode[collision], 0)
                self.assertIn(b"\x74\x77\x80", door_body)
                self.assertIn(b"\x07\x17\x24", door_body)
                self.assertNotIn(b"\x09\x17\x24", door_body)
                self.assertIn(
                    _change_field(origin, return_parameter),
                    door_body,
                )
                helper = transformed.get_script_pointer(23, 4)
                self.assertEqual(transformed.bytecode[helper], 0x37)
                self.assertEqual(
                    transformed.bytecode[
                        0x0400 :
                        0x0400
                        + len(_change_field(origin, return_parameter))
                    ],
                    _change_field(origin, return_parameter),
                )

    def test_archive_branch_uses_source_377s_three_native_reciprocal_doors(
        self,
    ) -> None:
        spec = _spec(367)
        source, transformed = _script_pair(367)

        self.assertEqual((spec.source_field, spec.target_field), (377, 367))
        self.assertEqual(
            (spec.target_bundle_id, spec.target_graphics_id),
            (1340, 1341),
        )
        self.assertEqual((source.entity_count, transformed.entity_count), (18, 18))
        self.assertEqual(
            _read_field_entry(transformed.to_bytes(), 0),
            FieldEntryAddition(0, 134, 0, 4, 4),
        )
        self.assertEqual(
            _read_field_entry(transformed.to_bytes(), 1),
            FieldEntryAddition(-239, 47, 0, 1, 1),
        )
        self.assertEqual(
            _read_field_entry(transformed.to_bytes(), 2),
            FieldEntryAddition(0, -125, 0, 0, 0),
        )

        for entity, helper, destination, parameter in (
            (12, 15, 726, 4),
            (13, 16, 385, 0),
            (14, 17, 386, 0),
        ):
            door = transformed.get_script_pointer(entity, 2)
            collision = transformed.get_script_pointer(entity, 3)
            door_body = _pointed_script_body(transformed, door)
            self.assertEqual(transformed.bytecode[collision], 0)
            self.assertIn(b"\x74\x77\x80", door_body)
            self.assertIn(bytes((0x07, helper, 0x24)), door_body)
            self.assertIn(_change_field(destination, parameter), door_body)
            helper_pointer = transformed.get_script_pointer(helper, 4)
            self.assertEqual(transformed.bytecode[helper_pointer], 0x37)

        header, components = _load_components(WORK / spec.bundle_directory)
        self.assertEqual(
            _sha256(header),
            "f46e59eb359cca3d27da02b1c1919a2c4c1e846ed3562b38ebcbb803b8757f09",
        )
        self.assertEqual(
            _sha256(components[MODEL_INDEX]),
            "c4435de49086ccfd68df20488c7e69204c2bbde27305d26af798c0512cb1d2b4",
        )
        self.assertEqual(
            _sha256(components[ACTOR_INDEX]),
            "f84a626b32efd650069e635576ba51a420e4dfd2061f8323278737ef1761df5f",
        )
        self.assertEqual(
            _sha256(components[SPRITE_INDEX]),
            "96902a4a530809dee1c9fb6eb01ec046205ff6a04ff81e445acac3ab3a4052e2",
        )

    def test_two_source_374_storage_leaves_have_mail_chests_and_only_return(
        self,
    ) -> None:
        for field, return_parameter, opened_bit in (
            (385, 1, ANNEX_TREASURE_A_OPENED_BIT),
            (386, 2, ANNEX_TREASURE_B_OPENED_BIT),
        ):
            with self.subTest(field=field):
                spec = _spec(field)
                source, transformed = _script_pair(field)
                self.assertEqual(spec.source_field, 374)
                self.assertEqual((source.entity_count, transformed.entity_count), (16, 16))
                self.assertEqual(
                    _read_field_entry(transformed.to_bytes(), 0),
                    FieldEntryAddition(-36, 0, 0, 2, 2),
                )
                door = _pointed_script_body(
                    transformed,
                    transformed.get_script_pointer(12, 2),
                )
                self.assertIn(b"\x74\x77\x80", door)
                self.assertIn(b"\x07\x0D\x24", door)
                self.assertIn(_change_field(367, return_parameter), door)
                terminal_init = transformed.get_script_pointer(14, 0)
                self.assertEqual(
                    _pointed_script_body(transformed, terminal_init),
                    _static_door_controller_init(
                        40,
                        150,
                        requires_facing=False,
                        interaction_half_width=0x20,
                    ),
                )
                terminal = _pointed_script_body(
                    transformed,
                    transformed.get_script_pointer(14, 2),
                )
                self.assertIn(b"\xF5\x02\x00\x00", terminal)
                self.assertNotIn(b"\x3A\xFA\x03", terminal)
                self.assertEqual(
                    tuple(
                        transformed.get_script_pointer(15, script_index)
                        for script_index in range(4)
                    ),
                    (0x019D, 0x01E6, 0x01E7, 0x0241),
                )
                self.assertEqual(
                    transformed.bytecode[0x0059:0x005F],
                    b"\x35\x1E\x04" + struct.pack("<h", OMEGASOL_ITEM_ID) + b"\x40",
                )
                self.assertEqual(
                    transformed.bytecode[0x005F:0x0067],
                    _jump_if_bit_clear(
                        ANNEX_TREASURE_VARIABLE,
                        1 << opened_bit,
                        0x006A,
                    ),
                )
                self.assertEqual(
                    transformed.bytecode[0x006D:0x0073],
                    _set_var_bit(ANNEX_TREASURE_VARIABLE, opened_bit),
                )


if __name__ == "__main__":
    unittest.main()
