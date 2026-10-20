from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

from pathlib import Path
import struct
import unittest

from tools import build_rico_arc as rico
from tools.migrate_duckstation_disc_state import (
    DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    _Zstd,
)
from tools.migrate_rico_arc_faraway_fire_slot1 import (
    ACTIVE_ENTITY_DATA,
    ACTIVE_ENTITY_DATA_SIZE,
    ARCHIVE_TABLE_DIFFS,
    ARCHIVE_TABLE_PAYLOAD_OFFSET,
    DEFAULT_NEW_DISC,
    DEFAULT_ZSTD,
    ENTITY_ZERO_CURRENT_PC_PAYLOAD_OFFSET,
    ENTITY_ZERO_SAVED_PC_PAYLOAD_OFFSET,
    EXPECTED_OUTPUT_PAYLOAD_SHA256,
    EXPECTED_OUTPUT_RAM_SHA256,
    EXPECTED_OUTPUT_SHA256,
    EXPECTED_OUTPUT_SIZE,
    EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT,
    GAMESTATE_SIZE,
    LIVE_SLOT_ONE,
    MUSIC_BRIDGE_COMPONENT_OFFSET,
    MUSIC_BRIDGE_PC,
    RESIDENT_DIALOGUE_PAYLOAD_OFFSET,
    RESIDENT_DIALOGUE_SIZE,
    RESIDENT_SCRIPT_PAYLOAD_OFFSET,
    RESIDENT_SCRIPT_SIZE,
    RicoFarawayFireMigrationError,
    SOURCE_ENTITY_ZERO_PC,
    SOURCE_MUSIC_BRIDGE,
    SOURCE_PAYLOAD_SHA256,
    SOURCE_RAM_OFFSET,
    SOURCE_STATE_SHA256,
    TARGET_ENTITY_ZERO_PC,
    TARGET_MUSIC_BRIDGE,
    TARGET_RESIDENT_SCRIPT_SHA256,
    _differences,
    _sha256,
    _validated_target_resources,
    main,
    migrate_state,
)
from tools.xgscript import AtelScript
from work.read_duckstation_runtime import (
    FIELD_SCRIPT_MEMORY,
    GAME_STATE,
    RAM_SIZE,
)


ROOT = REPOSITORY_ROOT
SOURCE_STATE = ROOT / "work" / "rico_arc_before_faraway_fire_audio_slot1.sav"


class RicoFarawayFireSlotOneMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (SOURCE_STATE, DEFAULT_NEW_DISC, DEFAULT_ZSTD)
        if any(not path.is_file() for path in required):
            raise unittest.SkipTest("Audited Rico audio migration inputs are unavailable")
        cls.source_state = SOURCE_STATE.read_bytes()
        if _sha256(cls.source_state) != SOURCE_STATE_SHA256:
            raise unittest.SkipTest("Archived source Slot 1 is no longer exact")
        cls.zstd = _Zstd(DEFAULT_ZSTD)
        cls.result, cls.report = migrate_state(
            cls.source_state,
            zstd=cls.zstd,
            new_disc=DEFAULT_NEW_DISC,
        )
        source_frame = struct.unpack_from(
            "<I",
            cls.source_state,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET + 12,
        )[0]
        result_frame = struct.unpack_from(
            "<I",
            cls.result,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET + 12,
        )[0]
        cls.source_payload = cls.zstd.decompress(cls.source_state[source_frame:])
        cls.result_payload = cls.zstd.decompress(cls.result[result_frame:])
        cls.source_ram = cls.source_payload[
            SOURCE_RAM_OFFSET : SOURCE_RAM_OFFSET + RAM_SIZE
        ]
        cls.result_ram = cls.result_payload[
            SOURCE_RAM_OFFSET : SOURCE_RAM_OFFSET + RAM_SIZE
        ]
        cls.target_script, cls.target_dialogue, cls.target_table = (
            _validated_target_resources(DEFAULT_NEW_DISC)
        )
        cls.source_script = cls.source_payload[
            RESIDENT_SCRIPT_PAYLOAD_OFFSET :
            RESIDENT_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE
        ]
        cls.result_script = cls.result_payload[
            RESIDENT_SCRIPT_PAYLOAD_OFFSET :
            RESIDENT_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE
        ]

    def test_exact_candidate_identity_and_report(self) -> None:
        self.assertEqual(len(self.result), EXPECTED_OUTPUT_SIZE)
        self.assertEqual(_sha256(self.result), EXPECTED_OUTPUT_SHA256)
        self.assertEqual(_sha256(self.source_payload), SOURCE_PAYLOAD_SHA256)
        self.assertEqual(_sha256(self.result_payload), EXPECTED_OUTPUT_PAYLOAD_SHA256)
        self.assertEqual(_sha256(self.result_ram), EXPECTED_OUTPUT_RAM_SHA256)
        self.assertEqual(
            self.report["payload_changed_byte_count"],
            EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT,
        )
        self.assertEqual(self.report["resident_script_changed_byte_count"], 4)
        self.assertEqual(self.report["resident_fat_changed_byte_count"], 2)
        self.assertEqual(self.report["entity_zero_resume_pc_changes"], 2)
        self.assertTrue(self.report["active_dialogue_window_preserved"])
        self.assertTrue(self.report["active_dialogue_actor_preserved"])
        self.assertTrue(self.report["field_progress_preserved"])
        self.assertTrue(self.report["allocator_header_preserved"])

    def test_exact_eight_byte_payload_whitelist(self) -> None:
        script_diffs = _differences(self.source_script, self.result_script)
        self.assertEqual(
            script_diffs,
            tuple(
                (MUSIC_BRIDGE_COMPONENT_OFFSET + index, old, new)
                for index, (old, new) in enumerate(
                    zip(SOURCE_MUSIC_BRIDGE, TARGET_MUSIC_BRIDGE, strict=True)
                )
            ),
        )
        expected = tuple(
            sorted(
                (
                    *(
                        (RESIDENT_SCRIPT_PAYLOAD_OFFSET + offset, old, new)
                        for offset, old, new in script_diffs
                    ),
                    (
                        ENTITY_ZERO_SAVED_PC_PAYLOAD_OFFSET,
                        SOURCE_ENTITY_ZERO_PC[0],
                        TARGET_ENTITY_ZERO_PC[0],
                    ),
                    (
                        ENTITY_ZERO_CURRENT_PC_PAYLOAD_OFFSET,
                        SOURCE_ENTITY_ZERO_PC[0],
                        TARGET_ENTITY_ZERO_PC[0],
                    ),
                    *(
                        (ARCHIVE_TABLE_PAYLOAD_OFFSET + offset, old, new)
                        for offset, old, new in ARCHIVE_TABLE_DIFFS
                    ),
                )
            )
        )
        self.assertEqual(len(expected), EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT)
        self.assertEqual(_differences(self.source_payload, self.result_payload), expected)

    def test_resume_bridge_and_active_scene_are_preserved(self) -> None:
        self.assertEqual(
            self.result_script[
                MUSIC_BRIDGE_COMPONENT_OFFSET : MUSIC_BRIDGE_COMPONENT_OFFSET + 4
            ],
            TARGET_MUSIC_BRIDGE,
        )
        self.assertEqual(_sha256(self.result_script), TARGET_RESIDENT_SCRIPT_SHA256)
        self.assertEqual(
            self.result_payload[
                ENTITY_ZERO_SAVED_PC_PAYLOAD_OFFSET :
                ENTITY_ZERO_SAVED_PC_PAYLOAD_OFFSET + 2
            ],
            TARGET_ENTITY_ZERO_PC,
        )
        self.assertEqual(
            self.result_payload[
                ENTITY_ZERO_CURRENT_PC_PAYLOAD_OFFSET :
                ENTITY_ZERO_CURRENT_PC_PAYLOAD_OFFSET + 2
            ],
            TARGET_ENTITY_ZERO_PC,
        )
        dialogue_slice = slice(
            RESIDENT_DIALOGUE_PAYLOAD_OFFSET,
            RESIDENT_DIALOGUE_PAYLOAD_OFFSET + RESIDENT_DIALOGUE_SIZE,
        )
        self.assertEqual(
            self.result_payload[dialogue_slice],
            self.source_payload[dialogue_slice],
        )
        active_slice = slice(
            ACTIVE_ENTITY_DATA,
            ACTIVE_ENTITY_DATA + ACTIVE_ENTITY_DATA_SIZE,
        )
        self.assertEqual(self.result_ram[active_slice], self.source_ram[active_slice])
        self.assertEqual(
            self.result_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
            self.source_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE],
        )
        self.assertEqual(
            self.result_ram[
                FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + 0x800
            ],
            self.source_ram[
                FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + 0x800
            ],
        )

    def test_staged_disc_has_faraway_promise_and_finite_fire_helper(self) -> None:
        editor = AtelScript(self.target_script)
        director_pc = editor.get_script_pointer(0, 0)
        self.assertEqual(
            editor.bytecode[
                director_pc : director_pc + len(
                    rico._sanitized_director(rico.CHAPTER_ONE_MUSIC_ID)
                )
            ],
            rico._sanitized_director(rico.CHAPTER_ONE_MUSIC_ID),
        )
        helper = rico._chapter_one_stove_audio_helper()
        self.assertEqual(
            editor.bytecode[
                MUSIC_BRIDGE_PC + 4 : MUSIC_BRIDGE_PC + 4 + len(helper)
            ],
            helper,
        )
        self.assertEqual(
            helper,
            rico._wait(24)
            + rico._play_sound_effect(0x111)
            + rico._wait(60)
            + rico._play_sound_effect(0)
            + b"\x0D",
        )
        self.assertEqual(self.target_script.count(rico.CHAPTER_ONE_STOVE_AUDIO_HELPER_CALL), 1)
        self.assertNotIn(rico._play_sound_effect(0x46), helper)

    def test_source_identity_and_mutations_are_guarded(self) -> None:
        changed = bytearray(self.source_state)
        changed[-1] ^= 1
        with self.assertRaisesRegex(
            RicoFarawayFireMigrationError,
            "Source Slot 1 identity changed",
        ):
            migrate_state(bytes(changed), zstd=self.zstd, new_disc=DEFAULT_NEW_DISC)
        with self.assertRaisesRegex(
            RicoFarawayFireMigrationError,
            "Disc 1 identity changed",
        ):
            migrate_state(self.source_state, zstd=self.zstd, new_disc=LIVE_SLOT_ONE)

    def test_cli_refuses_live_slot_output(self) -> None:
        with self.assertRaisesRegex(SystemExit, "live Slot 1"):
            main(
                (
                    str(SOURCE_STATE),
                    str(LIVE_SLOT_ONE),
                    "--new-disc",
                    str(DEFAULT_NEW_DISC),
                    "--zstd",
                    str(DEFAULT_ZSTD),
                )
            )


if __name__ == "__main__":
    unittest.main()
