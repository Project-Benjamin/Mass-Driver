from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

from pathlib import Path
import os
import struct
import tempfile
import unittest

from tools.migrate_duckstation_disc_state import (
    DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    _Zstd,
)
from tools.migrate_rico_arc_night_dialogue_slot1 import (
    ACTIVE_DIALOGUE_ID,
    ARCHIVE_TABLE_DIFFS,
    ARCHIVE_TABLE_PAYLOAD_OFFSET,
    ARCHIVE_TABLE_SIZE,
    DEFAULT_NEW_DISC,
    DEFAULT_ZSTD,
    EXPECTED_OUTPUT_PAYLOAD_SHA256,
    EXPECTED_OUTPUT_SHA256,
    EXPECTED_OUTPUT_SIZE,
    EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT,
    LIVE_SLOT_ONE,
    RESIDENT_DIALOGUE_PAYLOAD_OFFSET,
    RESIDENT_DIALOGUE_SHA256,
    RESIDENT_DIALOGUE_SIZE,
    RESIDENT_SCRIPT_PAYLOAD_OFFSET,
    RESIDENT_SCRIPT_SHA256,
    RESIDENT_SCRIPT_SIZE,
    RicoNightDialogueMigrationError,
    SOURCE_PAYLOAD_SHA256,
    SOURCE_STATE_SHA256,
    TARGET_RESIDENT_ARCHIVE_TABLE_SHA256,
    _aliases_existing_file,
    _differences,
    _sha256,
    _validated_target_resources,
    main,
    migrate_state,
)


ROOT = REPOSITORY_ROOT
SOURCE_STATE = ROOT / "work" / "rico_arc_before_night_dialogue_cleanup_slot1.sav"


class RicoNightDialogueSlotOneMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = (SOURCE_STATE, DEFAULT_NEW_DISC, DEFAULT_ZSTD)
        if any(not path.is_file() for path in required):
            raise unittest.SkipTest(
                "Audited Rico Slot 1, night-dialogue stage, or zstd is unavailable"
            )
        cls.source_state = SOURCE_STATE.read_bytes()
        if _sha256(cls.source_state) != SOURCE_STATE_SHA256:
            raise unittest.SkipTest(
                "Archived pre-night-dialogue Slot 1 is no longer exact"
            )
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
        cls.source_payload = cls.zstd.decompress(
            cls.source_state[source_frame:]
        )
        cls.result_payload = cls.zstd.decompress(cls.result[result_frame:])
        cls.target_table = _validated_target_resources(DEFAULT_NEW_DISC)

    def test_exact_candidate_identity_and_report(self) -> None:
        self.assertEqual(len(self.result), EXPECTED_OUTPUT_SIZE)
        self.assertEqual(_sha256(self.result), EXPECTED_OUTPUT_SHA256)
        self.assertEqual(
            _sha256(self.result_payload),
            EXPECTED_OUTPUT_PAYLOAD_SHA256,
        )
        self.assertEqual(
            self.report["payload_changed_byte_count"],
            EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT,
        )
        self.assertEqual(self.report["resident_fat_changed_byte_count"], 2)
        self.assertEqual(self.report["resident_script_changed_byte_count"], 0)
        self.assertEqual(self.report["resident_dialogue_changed_byte_count"], 0)
        self.assertEqual(self.report["active_dialogue_id"], ACTIVE_DIALOGUE_ID)
        self.assertTrue(self.report["active_dialogue_window_preserved"])
        self.assertTrue(self.report["father_dialogue_bridge_preserved"])
        self.assertTrue(self.report["resident_dialogue_preserved"])
        self.assertTrue(self.report["aftermath_dialogue_loaded_from_media"])

    def test_only_the_two_pinned_fat_bytes_change(self) -> None:
        expected = tuple(
            (
                ARCHIVE_TABLE_PAYLOAD_OFFSET + relative,
                old,
                new,
            )
            for relative, old, new in ARCHIVE_TABLE_DIFFS
        )
        self.assertEqual(
            _differences(self.source_payload, self.result_payload),
            expected,
        )
        self.assertEqual(len(expected), EXPECTED_PAYLOAD_CHANGED_BYTE_COUNT)

    def test_resident_script_dialogue_and_active_scene_are_byte_exact(self) -> None:
        for start, size, expected_hash, label in (
            (
                RESIDENT_SCRIPT_PAYLOAD_OFFSET,
                RESIDENT_SCRIPT_SIZE,
                RESIDENT_SCRIPT_SHA256,
                "script",
            ),
            (
                RESIDENT_DIALOGUE_PAYLOAD_OFFSET,
                RESIDENT_DIALOGUE_SIZE,
                RESIDENT_DIALOGUE_SHA256,
                "dialogue",
            ),
        ):
            with self.subTest(component=label):
                source = self.source_payload[start : start + size]
                result = self.result_payload[start : start + size]
                self.assertEqual(_sha256(source), expected_hash)
                self.assertEqual(result, source)

    def test_resident_fat_matches_stage_except_volatile_tail(self) -> None:
        start = ARCHIVE_TABLE_PAYLOAD_OFFSET
        end = start + ARCHIVE_TABLE_SIZE
        table = self.result_payload[start:end]
        self.assertEqual(_sha256(table), TARGET_RESIDENT_ARCHIVE_TABLE_SHA256)
        self.assertEqual(table[:-1], self.target_table[:-1])
        self.assertEqual(
            table[-1],
            self.source_payload[end - 1],
        )

    def test_prefix_payload_shape_and_source_identity_are_preserved(self) -> None:
        self.assertEqual(_sha256(self.source_payload), SOURCE_PAYLOAD_SHA256)
        self.assertEqual(len(self.result_payload), len(self.source_payload))
        source_frame = struct.unpack_from(
            "<I",
            self.source_state,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET + 12,
        )[0]
        result_frame = struct.unpack_from(
            "<I",
            self.result,
            DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET + 12,
        )[0]
        source_prefix = bytearray(self.source_state[:source_frame])
        result_prefix = bytearray(self.result[:result_frame])
        compressed_size_offset = DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET + 4
        result_prefix[
            compressed_size_offset : compressed_size_offset + 4
        ] = source_prefix[
            compressed_size_offset : compressed_size_offset + 4
        ]
        self.assertEqual(result_prefix, source_prefix)

    def test_mutated_source_and_wrong_disc_are_rejected(self) -> None:
        changed = bytearray(self.source_state)
        changed[-1] ^= 1
        with self.assertRaisesRegex(
            RicoNightDialogueMigrationError,
            "Source Slot 1 identity changed",
        ):
            migrate_state(
                bytes(changed),
                zstd=self.zstd,
                new_disc=DEFAULT_NEW_DISC,
            )
        with self.assertRaisesRegex(
            RicoNightDialogueMigrationError,
            "Disc 1 identity changed",
        ):
            migrate_state(
                self.source_state,
                zstd=self.zstd,
                new_disc=LIVE_SLOT_ONE,
            )

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

    def test_cli_refuses_inputs_and_hard_link_aliases_as_output(self) -> None:
        with self.assertRaisesRegex(SystemExit, "source state"):
            main(
                (
                    str(SOURCE_STATE),
                    str(SOURCE_STATE),
                    "--new-disc",
                    str(DEFAULT_NEW_DISC),
                    "--zstd",
                    str(DEFAULT_ZSTD),
                )
            )
        with self.assertRaisesRegex(SystemExit, "staged Disc 1"):
            main(
                (
                    str(SOURCE_STATE),
                    str(DEFAULT_NEW_DISC),
                    "--new-disc",
                    str(DEFAULT_NEW_DISC),
                    "--zstd",
                    str(DEFAULT_ZSTD),
                )
            )
        with self.assertRaisesRegex(SystemExit, "zstd library"):
            main(
                (
                    str(SOURCE_STATE),
                    str(DEFAULT_ZSTD),
                    "--new-disc",
                    str(DEFAULT_NEW_DISC),
                    "--zstd",
                    str(DEFAULT_ZSTD),
                )
            )

        with tempfile.TemporaryDirectory() as temporary:
            alias = Path(temporary) / "source-alias.sav"
            try:
                os.link(SOURCE_STATE, alias)
            except OSError as exc:
                self.skipTest(f"Hard links unavailable: {exc}")
            self.assertTrue(_aliases_existing_file(alias, SOURCE_STATE))
            with self.assertRaisesRegex(SystemExit, "source state"):
                main(
                    (
                        str(SOURCE_STATE),
                        str(alias),
                        "--new-disc",
                        str(DEFAULT_NEW_DISC),
                        "--zstd",
                        str(DEFAULT_ZSTD),
                    )
                )


if __name__ == "__main__":
    unittest.main()
