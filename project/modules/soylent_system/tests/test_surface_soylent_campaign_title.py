from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

import hashlib
from pathlib import Path
import struct
import unittest

import tools.build_surface_soylent_dungeon as soylent
import tools.surface_soylent_campaign_title as campaign_title
import tools.xgdeathblows as deathblows
from tools.xgfield import parse_field
from tools.xgscript import AtelScript as ScriptEditor


PROJECT_ROOT = REPOSITORY_ROOT
V173_TITLE = (
    PROJECT_ROOT
    / "work"
    / "surface_soylent_v1_v173_stage"
    / "replacements"
    / "1586_title_screen_complete_surface_route.bin"
)
MASS_DRIVER_GAMESTATE = (
    PROJECT_ROOT
    / "work"
    / "mass_driver_v162_stage"
    / "replacements"
    / "2595_standalone_gamestate.bin"
)


class SurfaceSoylentCampaignTitleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not V173_TITLE.is_file():
            raise AssertionError(f"Missing checked v173 title field: {V173_TITLE}")
        if not MASS_DRIVER_GAMESTATE.is_file():
            raise AssertionError(
                f"Missing checked Mass-Driver GameState: {MASS_DRIVER_GAMESTATE}"
            )
        cls.source = V173_TITLE.read_bytes()
        cls.result = campaign_title.transform_title_bundle(cls.source)
        cls.gamestate_source = MASS_DRIVER_GAMESTATE.read_bytes()
        cls.gamestate_result = campaign_title.transform_initial_gamestate(
            cls.gamestate_source
        )

    def test_campaign_title_output_is_frozen_and_deterministic(self) -> None:
        self.assertEqual(
            (len(self.source), hashlib.sha256(self.source).hexdigest()),
            (
                campaign_title.BASE_TITLE_BUNDLE_SIZE,
                campaign_title.BASE_TITLE_BUNDLE_SHA256,
            ),
        )
        expected = (
            campaign_title.CAMPAIGN_TITLE_BUNDLE_SIZE,
            campaign_title.CAMPAIGN_TITLE_BUNDLE_SHA256,
        )
        self.assertEqual(
            (len(self.result), hashlib.sha256(self.result).hexdigest()),
            expected,
        )
        again = campaign_title.transform_title_bundle(self.source)
        self.assertEqual(again, self.result)

    def test_only_the_atel_stream_changes(self) -> None:
        before = parse_field(self.source)
        after = parse_field(self.result)
        self.assertEqual(len(before.parts), len(after.parts))
        for index, (source_part, final_part) in enumerate(
            zip(before.parts, after.parts, strict=True)
        ):
            with self.subTest(stream=index):
                if index == soylent.SCRIPT_INDEX:
                    self.assertNotEqual(final_part.data, source_part.data)
                else:
                    self.assertEqual(final_part.data, source_part.data)

    def test_surface_tail_clears_appointment_word_and_campaign_bits_then_installs_party(self) -> None:
        script = parse_field(self.result).parts[soylent.SCRIPT_INDEX].data
        editor = ScriptEditor(script)
        self.assertEqual(
            (len(script), hashlib.sha256(script).hexdigest()),
            (
                campaign_title.CAMPAIGN_TITLE_SCRIPT_SIZE,
                campaign_title.CAMPAIGN_TITLE_SCRIPT_SHA256,
            ),
        )

        terminal_pc = (
            soylent.SURFACE_STATE_RESET_PC
            + len(soylent.SURFACE_STATE_RESET_ROUTINE)
            - 5
        )
        self.assertEqual(
            editor.bytecode[terminal_pc : terminal_pc + 5],
            campaign_title.CAMPAIGN_HANDOFF,
        )
        self.assertEqual(
            editor.bytecode[
                campaign_title.CAMPAIGN_RESET_PC :
                campaign_title.CAMPAIGN_RESET_PC
                + len(campaign_title.CAMPAIGN_RESET_ROUTINE)
            ],
            campaign_title.CAMPAIGN_RESET_ROUTINE,
        )

        state_clear_bytes = b"".join(
            b"\x3B"
            + struct.pack("<H", campaign_title.CAMPAIGN_STATE_OPERAND)
            + struct.pack("<H", bit_index)
            + b"\x40"
            for bit_index in campaign_title.CAMPAIGN_STATE_BIT_INDICES
        )
        self.assertEqual(
            campaign_title.APPOINTMENT_STATE_CLEAR,
            b"\x35" + struct.pack("<HH", 0x03EE, 0) + b"\x40",
        )
        clear_bytes = campaign_title.APPOINTMENT_STATE_CLEAR + state_clear_bytes
        self.assertTrue(campaign_title.CAMPAIGN_RESET_ROUTINE.startswith(clear_bytes))
        self.assertEqual(
            campaign_title.CAMPAIGN_RESET_ROUTINE.count(
                campaign_title.APPOINTMENT_STATE_CLEAR
            ),
            1,
        )
        self.assertEqual(
            campaign_title.CAMPAIGN_STATE_BIT_INDICES,
            (7, 11, 12, 13, 14, 15),
        )
        for bit_index in (1, 2, 3, 4):
            self.assertNotIn(
                b"\x3B" + struct.pack("<HH", 0x021A, bit_index) + b"\x40",
                campaign_title.CAMPAIGN_RESET_ROUTINE,
            )
        for bit_index in (0, 8, 9):
            self.assertIn(
                b"\x3B" + struct.pack("<HH", 0x021A, bit_index) + b"\x40",
                soylent.SURFACE_STATE_RESET_ROUTINE,
            )
        party_start = len(clear_bytes)
        self.assertEqual(
            campaign_title.CAMPAIGN_RESET_ROUTINE[
                party_start : party_start
                + len(campaign_title.CAMPAIGN_PARTY_BOOTSTRAP)
            ],
            bytes.fromhex(
                "FE 19 06 FE 19 01 "
                "FE 18 00 FE 1A "
                "FE 18 01 FE 1A "
                "FE 18 02 FE 1A"
            ),
        )
        self.assertTrue(
            campaign_title.CAMPAIGN_RESET_ROUTINE.endswith(
                soylent._change_field(623, 0)
            )
        )

    def test_mass_driver_and_existing_surface_reset_dispatch_are_preserved(self) -> None:
        before = ScriptEditor(
            parse_field(self.source).parts[soylent.SCRIPT_INDEX].data
        )
        after = ScriptEditor(
            parse_field(self.result).parts[soylent.SCRIPT_INDEX].data
        )
        terminal_pc = (
            soylent.SURFACE_STATE_RESET_PC
            + len(soylent.SURFACE_STATE_RESET_ROUTINE)
            - 5
        )
        self.assertEqual(after.bytecode[0x00BE:0x00C0], struct.pack("<H", 0x0176))
        self.assertEqual(
            after.bytecode[0x0171:0x0176],
            soylent._change_field(soylent.MASS_DRIVER_ENTRY_FIELD, 0),
        )
        self.assertEqual(
            after.bytecode[:terminal_pc],
            before.bytecode[:terminal_pc],
        )

    def test_initial_gamestate_grants_every_native_deathblow_only(self) -> None:
        self.assertEqual(
            (len(self.gamestate_source), hashlib.sha256(self.gamestate_source).hexdigest()),
            (
                campaign_title.BASE_INITIAL_GAMESTATE_SIZE,
                campaign_title.BASE_INITIAL_GAMESTATE_SHA256,
            ),
        )
        self.assertEqual(
            (len(self.gamestate_result), hashlib.sha256(self.gamestate_result).hexdigest()),
            (
                campaign_title.CAMPAIGN_INITIAL_GAMESTATE_SIZE,
                campaign_title.CAMPAIGN_INITIAL_GAMESTATE_SHA256,
            ),
        )
        for profile in deathblows.DEATHBLOW_PROFILES:
            with self.subTest(character=profile.character):
                self.assertEqual(
                    deathblows.learned_mask(
                        self.gamestate_result, profile.character_id
                    ),
                    deathblows.learned_mask(
                        self.gamestate_source, profile.character_id
                    )
                    | profile.full_mask,
                )
        self.assertEqual(
            self.gamestate_result[0x026C:0x0978],
            self.gamestate_source[0x026C:0x0978],
        )

    def test_prepared_resource_transform_preserves_other_title_resources(self) -> None:
        title = soylent.PreparedTitleResource(
            1586,
            "v173 title field",
            "1586_title_screen_complete_surface_route.bin",
            soylent.TITLE_BASE_IDENTITIES[1586][1],
            self.source,
        )
        graphics = soylent.PreparedTitleResource(
            1587,
            "title graphics",
            "1587.bin",
            soylent.TITLE_BASE_IDENTITIES[1587][1],
            b"unchanged graphics sentinel",
        )
        gamestate = soylent.PreparedTitleResource(
            2595,
            "initial GameState",
            "2595.bin",
            soylent.TITLE_BASE_IDENTITIES[2595][1],
            self.gamestate_source,
        )
        transformed = campaign_title.transform_title_resources(
            (graphics, title, gamestate)
        )
        self.assertIs(transformed[0], graphics)
        self.assertEqual(transformed[0].data, graphics.data)
        self.assertEqual(transformed[1].canonical_id, 1586)
        self.assertEqual(transformed[1].source_sha256, title.source_sha256)
        self.assertEqual(transformed[1].data, self.result)
        self.assertEqual(
            transformed[1].filename,
            "1586_title_screen_campaign_surface_route.bin",
        )
        self.assertEqual(transformed[2].canonical_id, 2595)
        self.assertEqual(transformed[2].source_sha256, gamestate.source_sha256)
        self.assertEqual(transformed[2].data, self.gamestate_result)
        self.assertEqual(
            transformed[2].filename,
            "2595_surface_all_deathblows_gamestate.bin",
        )

    def test_source_and_prepared_resource_guards_fail_closed(self) -> None:
        tampered = bytearray(self.source)
        tampered[-1] ^= 1
        with self.assertRaisesRegex(
            campaign_title.CampaignTitleError,
            "checked v173 title field",
        ):
            campaign_title.transform_title_bundle(bytes(tampered))

        title = soylent.PreparedTitleResource(
            1586,
            "bad provenance",
            "1586.bin",
            "0" * 64,
            self.source,
        )
        with self.assertRaisesRegex(
            campaign_title.CampaignTitleError,
            "provenance",
        ):
            campaign_title.transform_title_resource(title)

        bad_gamestate = soylent.PreparedTitleResource(
            2595,
            "bad GameState provenance",
            "2595.bin",
            "0" * 64,
            self.gamestate_source,
        )
        with self.assertRaisesRegex(
            campaign_title.CampaignTitleError,
            "provenance",
        ):
            campaign_title.transform_initial_gamestate_resource(bad_gamestate)
        tampered_gamestate = bytearray(self.gamestate_source)
        tampered_gamestate[-1] ^= 1
        with self.assertRaisesRegex(
            campaign_title.CampaignTitleError,
            "checked Mass-Driver initial GameState",
        ):
            campaign_title.transform_initial_gamestate(bytes(tampered_gamestate))
        with self.assertRaisesRegex(
            campaign_title.CampaignTitleError,
            "exactly one",
        ):
            campaign_title.transform_title_resources(())


if __name__ == "__main__":
    unittest.main()
