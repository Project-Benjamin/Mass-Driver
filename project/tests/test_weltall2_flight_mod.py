from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from tools import build_weltall2_flight_mod as builder
from tools import xgweltall2_global as global_w2
from tools import xgweltall2_field3d as field3d
from tools import xgweltall2_flight as flight
from tools.xgdisc import Mode2Image
from tools.xgfield import parse_field
from tools.xgscript import AtelScript
from tools.xgworldmap import WorldmapData, decompress_worldmap


ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "work" / "weltall2_flight_inputs"
FEI_PROFILE_STATE = ROOT / "work" / "standalone_bootstrap" / "2595.bin"
RETAIL_DISC = ROOT / "Xenogears (Disc 1).bin"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _input(canonical_id: int) -> bytes:
    path = INPUTS / f"{canonical_id:04d}.bin"
    if path.is_file():
        return path.read_bytes()
    if RETAIL_DISC.is_file():
        return builder._canonical(Mode2Image(RETAIL_DISC), canonical_id)
    raise unittest.SkipTest(f"checked test input and retail disc are missing: {path}")


class FlightOverlayTests(unittest.TestCase):
    def test_checked_overlay_identity_and_diff_isolation(self) -> None:
        source = _input(37)
        result = flight.patch_disc1_worldmap_overlay(source)

        self.assertEqual(len(source), 92_180)
        self.assertEqual(
            _sha256(source),
            "0f7e7a283fc5ef25d4a82960e16b119d09e1ba5594cc02069cf3dd2113f48803",
        )
        self.assertEqual(len(result.packed), 111_572)
        self.assertEqual(
            _sha256(result.packed),
            "58e97284e5adc228cf86ce539922ab6db34a7e9282b96ee2afcb000f8d3721e5",
        )
        self.assertEqual(
            _sha256(result.decoded),
            "cc86b8f58f53bde64527aec049bcb414c680c56490b90b9dee28cb8b919202a8",
        )
        self.assertEqual(decompress_worldmap(result.packed), result.decoded)
        self.assertEqual(
            result.changed_offsets,
            (
                0x14E44,
                0x14EB8,
                0x1CEDC,
                0x1D1E4,
                0x1D214,
                0x1D300,
                0x1D324,
                0x1D39C,
                0x1F064,
                0x1FD48,
                0x21288,
                0x21294,
                0x2177C,
                0x217B8,
                0x21880,
                0x218AC,
                0x218E4,
            ),
        )

        original = decompress_worldmap(source)
        actual_diffs = {
            index
            for index, (before, after) in enumerate(
                zip(original, result.decoded, strict=True)
            )
            if before != after
        }
        declared_diffs = {
            patch_item.offset + relative
            for patch_item in flight._PATCHES
            for relative, (before, after) in enumerate(
                zip(patch_item.before, patch_item.after, strict=True)
            )
            if before != after
        }
        self.assertEqual(actual_diffs, declared_diffs)

    def test_mips_flight_control_contract(self) -> None:
        decoded = flight.patch_disc1_worldmap_overlay(_input(37)).decoded

        def jump_target(offset: int) -> int:
            word = struct.unpack_from("<I", decoded, offset)[0]
            return 0x80000000 | ((word & 0x03FFFFFF) << 2)

        def branch_target(offset: int) -> int:
            word = struct.unpack_from("<I", decoded, offset)[0]
            immediate = word & 0xFFFF
            if immediate & 0x8000:
                immediate -= 0x10000
            return flight._OVERLAY_RUNTIME_BASE + offset + 4 + immediate * 4

        self.assertEqual(decoded[0x14E44:0x14E48], bytes.fromhex("04 00 14 24"))
        self.assertEqual(decoded[0x14EB8:0x14EBC], bytes.fromhex("50 01 12 24"))
        self.assertEqual(decoded[0x1CEDC:0x1CEE0], bytes.fromhex("0A 00 02 24"))
        self.assertEqual(decoded[0x1D1EC:0x1D1F0], bytes.fromhex("24 00 20 A6"))
        self.assertEqual(jump_target(0x1D20C), flight._FLAME_GUARD_RUNTIME)
        self.assertEqual(
            decoded[
                flight._FLAME_UPDATE_OFFSET:
                flight._FLAME_UPDATE_OFFSET + len(flight._FLAME_HELPERS)
            ],
            flight._FLAME_HELPERS,
        )
        self.assertEqual(jump_target(0x1D278), flight._SPAWN_WORLDMAP_PARTICLES)
        self.assertEqual(jump_target(0x1D2F0), flight._CLEAR_WORLDMAP_PARTICLES)

        # The landing wrapper preserves retail channel 0, clears the private
        # wing-light channel, then rejoins retail channel 1 cleanup.
        self.assertEqual(
            decoded[
                flight._FLAME_CLEAR_OFFSET:
                flight._FLAME_CLEAR_OFFSET + len(flight._FLAME_CLEAR_HELPER)
            ],
            flight._FLAME_CLEAR_HELPER,
        )
        self.assertEqual(jump_target(0x1D300), flight._CLEAR_WORLDMAP_PARTICLES)
        self.assertEqual(jump_target(0x1D308), flight._CLEAR_WORLDMAP_PARTICLES)
        self.assertEqual(decoded[0x1D30C:0x1D310], bytes.fromhex("32 00 04 24"))
        self.assertEqual(jump_target(0x1D310), flight._TOUCHDOWN_SECOND_CLEAR)

        # Launch retains the visible Gear, selects Weltall-2 animation 1 once
        # (the native deployed-wing bobbing loop), then initializes its lights.
        self.assertEqual(decoded[0x1D354:0x1D358], bytes.fromhex("C8 03 62 A4"))
        self.assertEqual(decoded[0x1D358:0x1D35C], bytes.fromhex("0C 00 02 24"))
        self.assertEqual(decoded[0x1D35C:0x1D360], bytes.fromhex("20 00 22 A6"))
        self.assertEqual(decoded[0x1D360:0x1D364], bytes.fromhex("4C 00 24 8E"))
        self.assertEqual(jump_target(0x1D364), flight._SPRITE_SET_ANIMATION)
        self.assertEqual(decoded[0x1D368:0x1D36C], bytes.fromhex("01 00 05 24"))
        self.assertEqual(jump_target(0x1D36C), flight._FLAME_INIT_RUNTIME)

        # A normal memory-card save made in midair reconstructs player state 2
        # but not the selected sprite animation or private particle template.
        # The state-2 guard repairs either missing piece and otherwise jumps
        # directly to the ordinary per-frame updater without restarting it.
        self.assertEqual(
            decoded[
                flight._FLAME_GUARD_OFFSET:
                flight._FLAME_GUARD_OFFSET + len(flight._FLAME_GUARD_HELPER)
            ],
            flight._FLAME_GUARD_HELPER,
        )
        self.assertEqual(decoded[0x1D3A4:0x1D3A8], bytes.fromhex("AF 00 82 90"))
        self.assertEqual(branch_target(0x1D3B0), 0x8008CECC)
        self.assertEqual(decoded[0x1D3C4:0x1D3C8], bytes.fromhex("4C 83 02 34"))
        self.assertEqual(branch_target(0x1D3D4), flight._FLAME_UPDATE_RUNTIME)
        self.assertEqual(jump_target(0x1D3DC), flight._SPRITE_SET_ANIMATION)
        self.assertEqual(decoded[0x1D3E0:0x1D3E4], bytes.fromhex("01 00 05 24"))
        self.assertEqual(jump_target(0x1D3E4), flight._FLAME_INIT_RUNTIME)
        self.assertEqual(decoded[0x1F064:0x1F068], bytes(4))
        # The native altitude-store delay slot after the removed collision call
        # must remain byte-identical.
        source = decompress_worldmap(_input(37))
        self.assertEqual(decoded[0x1F068:0x1F06C], source[0x1F068:0x1F06C])
        self.assertEqual(jump_target(0x1FD48), flight._FLAME_CLEAR_RUNTIME)
        self.assertEqual(decoded[0x1FD4C:0x1FD50], bytes.fromhex("21 20 00 00"))
        self.assertEqual(jump_target(0x1FD50), flight._CLEAR_WORLDMAP_PARTICLES)
        self.assertEqual(decoded[0x1FD54:0x1FD58], bytes.fromhex("01 00 04 24"))

        self.assertEqual(decoded[0x21288:0x2128C], bytes.fromhex("80 00 42 30"))
        target = decoded[0x21294:0x212A8]
        self.assertEqual(target, bytes.fromhex(
            "0A 80 02 3C 07 00 03 24 60 BD 43 A0 80 43 02 08 03 00 02 24"
        ))
        # lui v0,0x800A + sb v1,-0x42A0(v0) = 0x8009BD60.
        self.assertEqual(0x800A0000 + struct.unpack("<h", target[8:10])[0], 0x8009BD60)
        jump_word = struct.unpack_from("<I", target, 12)[0]
        self.assertEqual(0x80000000 | ((jump_word & 0x03FFFFFF) << 2), 0x80090E00)
        self.assertEqual(decoded[0x2177C:0x21780], bytes.fromhex("20 00 62 30"))
        self.assertEqual(decoded[0x217B8:0x217BC], bytes.fromhex("20 00 42 30"))
        self.assertEqual(decoded[0x21880:0x21884], bytes.fromhex("00 00 42 30"))
        self.assertEqual(decoded[0x218AC:0x218B0], bytes.fromhex("90 00 42 30"))
        self.assertEqual(decoded[0x218E4:0x218E8], bytes.fromhex("00 00 42 30"))

    def test_native_weltall2_flight_animation_and_particle_contract(self) -> None:
        sprite = _input(3940)
        self.assertEqual(len(sprite), 15_520)
        self.assertEqual(
            _sha256(sprite),
            "365febd425cee6229a9b4c63589a97d0d584011ae2499dbe539102944784495e",
        )
        self.assertEqual(struct.unpack_from("<I", sprite, 0)[0], 3)
        self.assertEqual(
            struct.unpack_from("<4I", sprite, 4),
            (20, 148, 15_484, 15_520),
        )
        animations = sprite[20:148]
        self.assertEqual(struct.unpack_from("<H", animations, 0)[0], 5)
        self.assertEqual(
            struct.unpack_from("<5H", animations, 2),
            (0x0C, 0x1A, 0x28, 0x0C, 0x0C),
        )
        self.assertEqual(
            animations[0x1A:0x28],
            bytes.fromhex("42 00 3E 00 24 00 24 00 24 00 24 00 24 00"),
        )
        # Five headings, each beginning a four-phase deployed-wing bob.
        self.assertEqual(
            struct.unpack_from("<5H", animations, 0x42),
            (16, 20, 24, 28, 32),
        )

        worldmap = decompress_worldmap(_input(3975))
        particle_base = struct.unpack_from("<I", worldmap, 0x18)[0]
        source = particle_base + flight._FLAME_SOURCE_EFFECT * 0x2A0
        private = particle_base + flight._FLAME_EFFECT * 0x2A0
        self.assertEqual(flight._FLAME_SOURCE_EFFECT, 0x08)
        self.assertEqual(
            [struct.unpack_from("<H", worldmap, source + slot * 0x54 + 0x0C)[0]
             for slot in range(8)],
            [32, 32, 32, 32, 0, 0, 0, 0],
        )
        # The native record is a single-particle, neutral-white engine light;
        # the runtime initializer duplicates it so left/right wings match.
        self.assertEqual(struct.unpack_from("<H", worldmap, source + 0x08)[0], 1)
        self.assertEqual(worldmap[source + 0x4C:source + 0x4F], bytes((224, 224, 224)))
        self.assertEqual(worldmap[source + 0x50:source + 0x53], bytes((251, 251, 251)))
        self.assertEqual(
            [struct.unpack_from("<H", worldmap, private + slot * 0x54 + 0x0C)[0]
             for slot in range(8)],
            [0] * 8,
        )

    def test_overlay_rejects_wrong_revision_and_tampering(self) -> None:
        source = _input(37)
        with self.assertRaisesRegex(flight.Weltall2FlightPatchError, "expected"):
            flight.patch_disc1_worldmap_overlay(source[:-1])

        tampered = bytearray(source)
        tampered[100] ^= 1
        with self.assertRaisesRegex(flight.Weltall2FlightPatchError, "hash mismatch"):
            flight.patch_disc1_worldmap_overlay(bytes(tampered))

        patched = flight.patch_disc1_worldmap_overlay(source).packed
        with self.assertRaises(flight.Weltall2FlightPatchError):
            flight.patch_disc1_worldmap_overlay(patched)

        decoded = bytearray(decompress_worldmap(source))
        decoded[0x21288] ^= 1
        with patch.object(
            flight,
            "DISC1_RETAIL_DECODED_SHA256",
            _sha256(bytes(decoded)),
        ):
            with self.assertRaisesRegex(
                flight.Weltall2FlightPatchError, "Checked context changed"
            ):
                flight.apply_decoded_flight_patches(bytes(decoded))


class BootstrapResourceTests(unittest.TestCase):
    def test_title_new_game_route_is_exact_and_isolated(self) -> None:
        source = _input(1586)
        result = builder.patch_title_field(source)
        self.assertEqual(len(result), 4_348)
        self.assertEqual(
            _sha256(result),
            "c80ca1a6cecc86d0e406615afa0453c68ca7523373a4f07323b87737143a64f0",
        )

        old = parse_field(source)
        new = parse_field(result)
        for index, (before, after) in enumerate(zip(old.parts, new.parts, strict=True)):
            with self.subTest(component=index):
                if index == 5:
                    self.assertNotEqual(before.data, after.data)
                else:
                    self.assertEqual(before.data, after.data)
        atel = AtelScript(new.parts[5].data)
        self.assertEqual(atel.bytecode[0xB8:0xC0], builder.TITLE_FALLTHROUGH_PATCHED)
        self.assertEqual(atel.bytecode[0x16C:0x172], builder.TITLE_GATEWAY_ROUTINE)

    def test_gateway_is_inert_except_for_resumable_worldmap_handoff(self) -> None:
        source = _input(2054)
        result = builder.build_gateway_field(source)
        self.assertEqual(len(result), 26_024)
        self.assertEqual(
            _sha256(result),
            "668f688f4551cb5e8732c925ab4dd85c590301c0f26e4a8052bebda53816cfc7",
        )
        old = parse_field(source)
        new = parse_field(result)
        for index, (before, after) in enumerate(zip(old.parts, new.parts, strict=True)):
            with self.subTest(component=index):
                if index == 5:
                    self.assertNotEqual(before.data, after.data)
                else:
                    self.assertEqual(before.data, after.data)

        atel = AtelScript(new.parts[5].data)
        self.assertEqual(atel.entity_count, 19)
        self.assertEqual(atel.bytecode[0xFE0], 0x5B)
        self.assertEqual(
            atel.bytecode[builder.GATEWAY_DIRECTOR_PC:builder.GATEWAY_UPDATE_PC],
            builder.GATEWAY_DIRECTOR,
        )
        self.assertEqual(
            atel.bytecode[builder.GATEWAY_UPDATE_PC:],
            builder.GATEWAY_UPDATE,
        )
        for entity in range(atel.entity_count):
            for script_index in range(32):
                expected = 0xFE0
                if entity == 0 and script_index == 0:
                    expected = builder.GATEWAY_DIRECTOR_PC
                elif entity == 0 and script_index == 1:
                    expected = builder.GATEWAY_UPDATE_PC
                with self.subTest(entity=entity, script=script_index):
                    self.assertEqual(
                        atel.get_script_pointer(entity, script_index), expected
                    )

    def test_initial_state_is_exact_flying_weltall_contract(self) -> None:
        if not FEI_PROFILE_STATE.is_file():
            self.skipTest(f"checked Fei profile is missing: {FEI_PROFILE_STATE}")
        retail = _input(2595)
        result = builder.build_initial_gamestate(retail, FEI_PROFILE_STATE.read_bytes())

        self.assertEqual(len(result), 0x2358)
        self.assertEqual(
            _sha256(result),
            "e4255c517f86a8d809cc31334e506cf0a55dca953881988212c13d945497ec6a",
        )
        weltall_name = builder.WELTALL_NAME_CELL * builder.FIXED_NAME_CELL_SIZE
        weltall2_name = builder.WELTALL2_NAME_CELL * builder.FIXED_NAME_CELL_SIZE
        self.assertEqual(
            result[weltall_name:weltall_name + builder.FIXED_NAME_CELL_SIZE],
            retail[weltall2_name:weltall2_name + builder.FIXED_NAME_CELL_SIZE],
        )
        self.assertEqual(
            result[:weltall_name] + result[weltall_name + 20:620],
            retail[:weltall_name] + retail[weltall_name + 20:620],
        )
        self.assertEqual(struct.unpack_from("<H", result, 0x1930)[0], 0x18)
        self.assertEqual(struct.unpack_from("<H", result, 0x1BF6)[0] & 4, 0)
        self.assertEqual(struct.unpack_from("<H", result, 0x1D30)[0], 1)
        self.assertEqual(struct.unpack_from("<H", result, 0x1D32)[0], 0xFFFF)
        self.assertEqual(result[0x1D34:0x1D37], bytes((0, 0xFF, 0xFF)))
        self.assertEqual(result[0x22B1:0x22B4], bytes((1, 0, 0)))
        self.assertEqual(result[builder.FEI_LEVEL_OFFSETS[0]], 99)
        self.assertEqual(result[builder.FEI_LEVEL_OFFSETS[1]], 99)
        self.assertEqual(result[builder.FEI_GEAR_ID], 1)
        self.assertEqual(struct.unpack_from("<H", result, builder.FEI_MAX_HP)[0], 404)
        self.assertEqual(struct.unpack_from("<H", result, builder.FEI_MAX_MP)[0], 57)
        self.assertEqual(
            result[builder.FEI_CURRENT_HP:builder.FEI_CURRENT_HP + 2],
            result[builder.FEI_MAX_HP:builder.FEI_MAX_HP + 2],
        )
        self.assertEqual(
            result[builder.FEI_CURRENT_MP:builder.FEI_CURRENT_MP + 2],
            result[builder.FEI_MAX_MP:builder.FEI_MAX_MP + 2],
        )
        self.assertEqual(struct.unpack_from("<H", result, 0x16C0)[0], 0xFFF8)
        self.assertEqual(struct.unpack_from("<H", result, 0x16C4)[0], 0x1FF8)

        record = result[
            builder.WELTALL2_RECORD:
            builder.WELTALL2_RECORD + builder.GEAR_RECORD_SIZE
        ]
        self.assertEqual(record, builder.BEST_WELTALL2_RECORD)
        self.assertEqual(record[2:4], bytes((0x11, 0x36)))
        self.assertEqual(record[8:12], bytes((0x37, 0x64, 0x64, 0x64)))
        self.assertEqual(struct.unpack_from("<H", record, 0x38)[0], 1_000)
        self.assertEqual(struct.unpack_from("<H", record, 0x3A)[0], 1_000)
        self.assertEqual(record[0x3C], 100)
        self.assertEqual(record[0x56], 15)
        self.assertEqual(struct.unpack_from("<I", record, 0x60)[0], 30_400)
        self.assertEqual(struct.unpack_from("<I", record, 0x64)[0], 30_400)
        fallback_record = result[
            builder.WELTALL_RECORD:
            builder.WELTALL_RECORD + builder.GEAR_RECORD_SIZE
        ]
        self.assertEqual(fallback_record, builder.BEST_WELTALL2_RECORD)

        self.assertEqual(
            struct.unpack_from("<6h", result, 0x1820),
            (29_947, 11_075, 0, 0, 0, 0),
        )
        self.assertEqual(
            struct.unpack_from("<4h", result, 0x182C),
            (29_947, 0, 11_075, 0),
        )
        self.assertEqual(struct.unpack_from("<H", result, 0x1834)[0], 3)
        self.assertEqual(struct.unpack_from("<H", result, 0x1836)[0], 0)
        self.assertEqual(struct.unpack_from("<H", result, 0x231A)[0], 490)
        self.assertEqual(struct.unpack_from("<h", result, 0x231C)[0], 0)
        self.assertEqual(struct.unpack_from("<h", result, 0x231E)[0], 1)
        self.assertEqual(struct.unpack_from("<H", result, 0x2320)[0], 0)

        # No Elly/Emeralda Mass Driver state survives: all non-Fei character
        # records and ability records are byte-identical to retail Disc 1.
        other_characters = builder.FEI_RECORD + builder.GEAR_RECORD_SIZE
        self.assertEqual(result[other_characters:0x978], retail[other_characters:0x978])
        self.assertEqual(
            result[builder.FEI_ABILITY_RECORD + 0x20:0x1820],
            retail[builder.FEI_ABILITY_RECORD + 0x20:0x1820],
        )

        allowed_ranges = (
            (weltall_name, weltall_name + builder.FIXED_NAME_CELL_SIZE),
            (builder.FEI_RECORD, builder.FEI_RECORD + builder.GEAR_RECORD_SIZE),
            (builder.WELTALL_RECORD, builder.WELTALL2_RECORD + builder.GEAR_RECORD_SIZE),
            (builder.FEI_ABILITY_RECORD, builder.FEI_ABILITY_RECORD + 0x20),
            (0x1820, 0x1838),
            (0x1930, 0x1932),
            (0x1BF6, 0x1BF8),
            (0x1D30, 0x1D37),
            (0x22B1, 0x22B4),
            (0x2318, 0x2322),
        )
        actual_diffs = {
            offset
            for offset, (before, after) in enumerate(zip(retail, result, strict=True))
            if before != after
        }
        allowed_diffs = {
            offset
            for start, end in allowed_ranges
            for offset in range(start, end)
        }
        self.assertTrue(actual_diffs <= allowed_diffs)

    def test_retail_frame_mask_survives_story_party_reordering(self) -> None:
        def retail_battle_selection(
            party: tuple[int, int, int],
            membership: int,
            frame_mask: int,
            stale: tuple[int, int, int],
        ) -> tuple[int, int, int]:
            battle = list(stale)
            used = 0
            eligible = membership & frame_mask
            for slot, character in enumerate(party):
                if character != 0xFF and eligible & (1 << character):
                    battle[slot] = character
                    used += 1
            for slot in range(used, 3):
                battle[slot] = 0x7F
            return tuple(battle)

        reordered = (1, 0, 0xFF)  # temporary Elly/Fei story ordering
        self.assertEqual(
            retail_battle_selection(reordered, 0x0003, 0xFFFF, (1, 0x7F, 0x7F)),
            (1, 0, 0x7F),
        )
        self.assertNotIn(
            0,
            retail_battle_selection(reordered, 0x0003, 0x0001, (1, 0x7F, 0x7F)),
        )

    def test_post_lahan_position_is_from_the_untouched_retail_map(self) -> None:
        packed = _input(3975)
        self.assertEqual(
            _sha256(packed),
            "cfc703579f5f6c10e68880d41eac3802ae4c54e7dd797ed5cad9e1029df79857",
        )
        positions = WorldmapData(decompress_worldmap(packed)).initial_positions()
        matches = [position for position in positions if position.index == 1]
        self.assertEqual(len(matches), 1)
        self.assertEqual((matches[0].x, matches[0].z), (29_947, 11_075))

    def test_replacement_set_is_separate_and_complete(self) -> None:
        self.assertEqual(
            builder.REPLACEMENT_IDS,
            frozenset((37, 1586, 2054, 2595))
            | global_w2.GLOBAL_REPLACEMENT_IDS,
        )
        self.assertTrue(builder.REPLACEMENT_IDS.isdisjoint((1587, 2593, 2599)))
        self.assertEqual(builder.GATEWAY_FIELD_CANONICAL_ID, 606 + 2 * 724)
        self.assertEqual(builder.FORMAT, "xenogears-flying-weltall2-disc1-v6")

    def test_source_validation_rejects_before_disc_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "wrong.bin"
            source.write_bytes(b"not a disc")
            with patch.object(builder, "Mode2Image") as reader:
                with self.assertRaisesRegex(builder.Weltall2BuildError, "source mismatch"):
                    builder.validate_source_disc(source)
            reader.assert_not_called()


class GlobalWeltallReplacementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.resources = {
            canonical_id: _input(canonical_id)
            for canonical_id in global_w2.SOURCE_IDENTITIES
        }
        cls.replacements = {
            item.canonical_id: item
            for item in global_w2.build_global_replacements(cls.resources)
        }

    def test_inventory_and_exact_model_aliases(self) -> None:
        self.assertEqual(
            frozenset(self.replacements),
            global_w2.GLOBAL_REPLACEMENT_IDS,
        )
        for target, donor, _role in global_w2.MODEL_ALIASES:
            with self.subTest(target=target, donor=donor):
                self.assertEqual(self.replacements[target].data, self.resources[donor])

        # 2150/2151 are Rankar, not Weltall.  Model 7 and both byte-identical
        # regular-Weltall world-map slots are the actual replacement targets.
        self.assertTrue({2150, 2151}.isdisjoint(self.replacements))
        self.assertTrue({2158, 2159, 3939, 3949}.issubset(self.replacements))
        self.assertEqual(self.resources[3939], self.resources[3949])

    def test_field_scene_controller_is_weltall2_native_and_index_safe(self) -> None:
        controller = self.replacements[field3d.FIELD_WELTALL_CONTROLLER_ID].data
        self.assertEqual(len(controller), field3d.COMPAT_CONTROLLER_SIZE)
        self.assertEqual(_sha256(controller), field3d.COMPAT_CONTROLLER_SHA256)
        self.assertEqual(
            controller,
            field3d.build_compat_controller(
                self.resources[field3d.FIELD_WELTALL2_CONTROLLER_ID]
            ),
        )
        roots, entries, tail = field3d._controller_entries(controller)
        source_roots, source_entries, source_tail = field3d._controller_entries(
            self.resources[field3d.FIELD_WELTALL2_CONTROLLER_ID]
        )
        self.assertEqual(roots, field3d.COMPAT_CONTROLLER_ROOTS)
        self.assertEqual(source_roots, field3d.WELTALL2_SOURCE_ROOTS)
        self.assertEqual(len(entries), 24)
        self.assertEqual(entries[0], source_entries[0])
        self.assertEqual(tail, source_tail)
        for target, donor in enumerate(field3d.REGULAR_TO_WELTALL2_ANIMATION):
            self.assertEqual(entries[target + 1], source_entries[donor + 1])

    def test_field_scene_geometry_is_exact_native_weltall2(self) -> None:
        self.assertEqual(
            self.replacements[field3d.FIELD_WELTALL_GEOMETRY_ID].data,
            self.resources[field3d.FIELD_WELTALL2_GEOMETRY_ID],
        )

    def test_scripted_model7_controller_and_geometry_are_weltall2_native(self) -> None:
        controller = self.replacements[
            field3d.FIELD_TRANSFORM_WELTALL_CONTROLLER_ID
        ].data
        self.assertEqual(
            controller,
            field3d.build_compat_controller(
                self.resources[field3d.FIELD_WELTALL2_CONTROLLER_ID]
            ),
        )
        self.assertEqual(len(controller), field3d.COMPAT_CONTROLLER_SIZE)
        self.assertEqual(
            _sha256(controller),
            field3d.COMPAT_CONTROLLER_SHA256,
        )
        roots, entries, tail = field3d._controller_entries(controller)
        _, source_entries, source_tail = field3d._controller_entries(
            self.resources[field3d.FIELD_WELTALL2_CONTROLLER_ID]
        )
        self.assertEqual(roots, field3d.COMPAT_CONTROLLER_ROOTS)
        self.assertEqual(len(entries), 24)
        self.assertEqual(entries[0], source_entries[0])
        self.assertEqual(tail, source_tail)
        for target, donor in enumerate(field3d.REGULAR_TO_WELTALL2_ANIMATION):
            self.assertEqual(entries[target + 1], source_entries[donor + 1])
        self.assertEqual(
            self.replacements[field3d.FIELD_TRANSFORM_WELTALL_GEOMETRY_ID].data,
            self.resources[field3d.FIELD_WELTALL2_GEOMETRY_ID],
        )

    def test_rankar_intro_embedded_weltall_is_rebuilt_without_neighbor_drift(self) -> None:
        source = self.resources[global_w2.RANKAR_INTRO_BATTLE_BUNDLE_ID]
        result = self.replacements[
            global_w2.RANKAR_INTRO_BATTLE_BUNDLE_ID
        ].data
        self.assertEqual(len(result), global_w2.RANKAR_BUNDLE_RESULT_SIZE)
        self.assertEqual(_sha256(result), global_w2.RANKAR_BUNDLE_RESULT_SHA256)
        self.assertEqual(
            struct.unpack_from("<I", result, 4)[0],
            global_w2.RANKAR_BUNDLE_RESULT_BUFFER_SIZE,
        )
        self.assertEqual(
            global_w2._battle_bundle_pointers(result),
            global_w2.RANKAR_BUNDLE_RESULT_POINTERS,
        )

        event_controller = field3d.build_rankar_transform_compat_controller(
            self.resources[field3d.FIELD_WELTALL2_CONTROLLER_ID]
        )
        controller_start = global_w2.RANKAR_BUNDLE_RESULT_POINTERS[2][0]
        self.assertEqual(
            result[controller_start:controller_start + len(event_controller)],
            event_controller,
        )
        roots, entries, _tail = field3d._controller_entries(event_controller)
        self.assertEqual(roots, field3d.RANKAR_TRANSFORM_COMPAT_CONTROLLER_ROOTS)
        self.assertEqual(len(entries), 33)
        geometry_start = global_w2.RANKAR_BUNDLE_RESULT_POINTERS[2][1]
        geometry = self.resources[field3d.FIELD_WELTALL2_GEOMETRY_ID]
        self.assertEqual(
            result[geometry_start:geometry_start + len(geometry)],
            geometry,
        )
        self.assertEqual(
            source[
                global_w2.RANKAR_BUNDLE_POINTERS[2][1]:
                global_w2.RANKAR_BUNDLE_POINTERS[3][1]
            ],
            self.resources[field3d.FIELD_TRANSFORM_WELTALL_GEOMETRY_ID],
        )

        # Entry 0 is Rankar and entry 1 is Citan's carrier.  Their complete
        # controller/model spans, plus the trailing sprite, remain identical.
        old_pointers = global_w2.RANKAR_BUNDLE_POINTERS
        new_pointers = global_w2.RANKAR_BUNDLE_RESULT_POINTERS
        self.assertEqual(
            result[new_pointers[0][0]:new_pointers[1][0]],
            source[old_pointers[0][0]:old_pointers[1][0]],
        )
        self.assertEqual(
            result[new_pointers[1][0]:new_pointers[2][0]],
            source[old_pointers[1][0]:old_pointers[2][0]],
        )
        self.assertEqual(
            result[new_pointers[0][1]:new_pointers[1][1]],
            source[old_pointers[0][1]:old_pointers[1][1]],
        )
        self.assertEqual(
            result[new_pointers[1][1]:new_pointers[2][1]],
            source[old_pointers[1][1]:old_pointers[2][1]],
        )
        self.assertEqual(
            result[new_pointers[3][1]:],
            source[old_pointers[3][1]:],
        )

    def test_persistent_story_assignments_are_all_gear_one(self) -> None:
        for canonical_id, expected_count in global_w2.FIELD_ASSIGNMENT_COUNTS.items():
            with self.subTest(canonical_id=canonical_id):
                source = parse_field(self.resources[canonical_id])
                result = parse_field(self.replacements[canonical_id].data)
                old_bytecode = AtelScript(source.parts[5].data).bytecode
                new_bytecode = AtelScript(result.parts[5].data).bytecode
                self.assertEqual(
                    old_bytecode.count(global_w2.WELTALL_ASSIGNMENT), expected_count
                )
                self.assertEqual(new_bytecode.count(global_w2.WELTALL_ASSIGNMENT), 0)
                self.assertEqual(
                    new_bytecode.count(global_w2.WELTALL2_ASSIGNMENT),
                    old_bytecode.count(global_w2.WELTALL2_ASSIGNMENT) + expected_count,
                )
                for index, (before, after) in enumerate(
                    zip(source.parts, result.parts, strict=True)
                ):
                    if index == 5:
                        continue
                    if canonical_id == 1050 and index == 7:
                        self.assertNotEqual(before.data, after.data)
                    else:
                        self.assertEqual(before.data, after.data)

    def test_battling_weltall_selectors_use_native_roster_ten(self) -> None:
        for canonical_id, patches in global_w2.FIELD_BATTLING_PATCHES.items():
            with self.subTest(canonical_id=canonical_id):
                source = parse_field(self.resources[canonical_id])
                result = parse_field(self.replacements[canonical_id].data)
                old_atel = AtelScript(source.parts[5].data)
                new_atel = AtelScript(result.parts[5].data)
                for script_patch in patches:
                    start = script_patch.pc
                    end = start + len(script_patch.before)
                    self.assertEqual(
                        old_atel.bytecode[start:end], script_patch.before
                    )
                    self.assertEqual(
                        new_atel.bytecode[start:end], script_patch.after
                    )
                for index, (before, after) in enumerate(
                    zip(source.parts, result.parts, strict=True)
                ):
                    if index == 5:
                        continue
                    if canonical_id == 1050 and index == 7:
                        self.assertNotEqual(before.data, after.data)
                    else:
                        self.assertEqual(before.data, after.data)

        # The optional selector's two "Weltall" branches now store roster 10;
        # its native Weltall-2 and Xenogears branches remain untouched.
        field222 = AtelScript(
            parse_field(self.replacements[1050].data).parts[5].data
        ).bytecode
        self.assertEqual(field222[0x248B:0x2491], bytes.fromhex("35 02 04 0A 00 40"))
        self.assertEqual(field222[0x24A5:0x24AB], bytes.fromhex("35 02 04 0A 00 40"))
        self.assertEqual(field222[0x245E:0x2460], bytes.fromhex("A9 23"))

        source_dialogue = parse_field(self.resources[1050]).parts[7].data
        result_dialogue = parse_field(self.replacements[1050].data).parts[7].data
        self.assertEqual(
            result_dialogue,
            global_w2.patch_battling_roster_dialogue(source_dialogue),
        )
        block_count = struct.unpack_from("<I", result_dialogue, 0)[0] + 1
        offsets = struct.unpack_from(f"<{block_count}H", result_dialogue, 4)
        block_id = global_w2.BATTLING_ROSTER_DIALOGUE_ID
        payload = result_dialogue[offsets[block_id]:offsets[block_id + 1]]
        self.assertNotIn(bytes.fromhex("0F 05 0B"), payload)
        self.assertTrue(payload.endswith(bytes.fromhex("0F 05 0C 00")))
        dimensions = 4 + 2 * block_count + 2 * block_id
        self.assertEqual(
            result_dialogue[dimensions:dimensions + 2],
            global_w2.BATTLING_ROSTER_RESULT_DIMENSIONS,
        )

    def test_combat_tables_alias_only_the_weltall_entries(self) -> None:
        cases = (
            (
                global_w2.SYSTEM_DATA_ID,
                global_w2.SYSTEM_DATA_WELTALL_ENTRY,
                global_w2.SYSTEM_DATA_WELTALL2_ENTRY,
            ),
            (
                global_w2.LIVE_BATTLE_STATS_ID,
                global_w2.LIVE_BATTLE_WELTALL_ENTRY,
                global_w2.LIVE_BATTLE_WELTALL2_ENTRY,
            ),
        )
        for canonical_id, target, donor in cases:
            with self.subTest(canonical_id=canonical_id):
                _, before = global_w2._archive_entries(self.resources[canonical_id])
                _, after = global_w2._archive_entries(
                    self.replacements[canonical_id].data
                )
                self.assertEqual(after[target], before[donor])
                for index in range(len(before)):
                    if index != target:
                        self.assertEqual(after[index], before[index])

    def test_gear_shop_slot_zero_uses_native_weltall2_selector_and_pose(self) -> None:
        result = self.replacements[global_w2.GEAR_SHOP_MENU_ID].data
        model0 = struct.unpack_from("<H", result, global_w2.GEAR_SHOP_MODEL_TABLE)[0]
        model1 = struct.unpack_from("<H", result, global_w2.GEAR_SHOP_MODEL_TABLE + 2)[0]
        self.assertEqual(model0, model1)
        self.assertEqual(model0, global_w2.GEAR_SHOP_WELTALL2_MODEL)
        self.assertEqual(
            result[global_w2.GEAR_SHOP_POSE_TABLE],
            result[global_w2.GEAR_SHOP_POSE_TABLE + 1],
        )


if __name__ == "__main__":
    unittest.main()
