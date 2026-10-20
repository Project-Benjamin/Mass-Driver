from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

import tools.migrate_duckstation_disc_state as migration


OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_standalone_v55.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_standalone_v56.cue"
OLD_TABLE = b"\xA5" * 0x8000
NEW_TABLE = b"\x5A" * 0x8000
SOURCE_FRAME = migration.ZSTD_MAGIC + b"source-frame"
RECOMPRESSED_FRAME = migration.ZSTD_MAGIC + b"recompressed-frame-is-longer"


class _FakeZstd:
    def __init__(
        self,
        payload: bytes,
        *,
        frame_size: int | None = None,
        recompressed: bytes = RECOMPRESSED_FRAME,
    ) -> None:
        self.payload = payload
        self.declared_frame_size = (
            len(SOURCE_FRAME) if frame_size is None else frame_size
        )
        self.recompressed = recompressed
        self.compressed_payload: bytes | None = None

    def frame_size(self, frame: bytes) -> int:
        self.frame = frame
        return self.declared_frame_size

    def decompress(self, frame: bytes) -> bytes:
        self.decompressed_frame = frame
        return self.payload

    def compress(self, payload: bytes) -> bytes:
        self.compressed_payload = payload
        return self.recompressed


def _source_payload() -> bytes:
    return b"payload-before|" + OLD_TABLE + b"|payload-after"


def _source_state(
    *,
    frame_start: int = 0x140,
    declared_frame_size: int = len(SOURCE_FRAME),
    declared_payload_size: int | None = None,
    frame: bytes = SOURCE_FRAME,
    tail: bytes = b"",
) -> bytes:
    payload_size = (
        len(_source_payload())
        if declared_payload_size is None
        else declared_payload_size
    )
    prefix = bytearray(b"\x6D" * frame_start)
    prefix[:4] = migration.DUCKSTATION_STATE_MAGIC
    cue_offset = 0x30
    prefix[cue_offset : cue_offset + len(OLD_CUE_NAME)] = OLD_CUE_NAME.encode(
        "ascii"
    )
    struct.pack_into(
        "<IIII",
        prefix,
        0xC8,
        2,
        declared_frame_size,
        payload_size,
        frame_start,
    )
    # A zstd-looking sequence at the minimum header boundary ensures the
    # migration honors offset_to_data at 0xD4 instead of searching for magic.
    prefix[0xD8:0xDC] = migration.ZSTD_MAGIC
    return bytes(prefix) + frame + tail


def _archive_table(path: Path) -> bytes:
    if path.name == "old.bin":
        return OLD_TABLE
    if path.name == "new.bin":
        return NEW_TABLE
    raise AssertionError(f"unexpected disc path: {path}")


class DuckStationStateMigrationTests(unittest.TestCase):
    def test_recompression_uses_header_offset_and_rewrites_size_at_0xcc(
        self,
    ) -> None:
        payload = _source_payload()
        source = _source_state()
        zstd = _FakeZstd(payload)

        with patch.object(migration, "_archive_table", side_effect=_archive_table):
            result, report = migration.migrate_state(
                source,
                old_disc=Path("old.bin"),
                new_disc=Path("new.bin"),
                old_cue_name=OLD_CUE_NAME,
                new_cue_name=NEW_CUE_NAME,
                zstd=zstd,
            )

        self.assertEqual(source, _source_state())
        self.assertEqual(
            (
                migration.DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
                migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
                migration.DUCKSTATION_DATA_UNCOMPRESSED_SIZE_OFFSET,
                migration.DUCKSTATION_DATA_OFFSET_OFFSET,
            ),
            (0xC8, 0xCC, 0xD0, 0xD4),
        )
        self.assertEqual(
            struct.unpack_from("<IIII", result, 0xC8),
            (
                2,
                len(RECOMPRESSED_FRAME),
                len(payload),
                0x140,
            ),
        )
        self.assertEqual(len(result), 0x140 + len(RECOMPRESSED_FRAME))
        self.assertEqual(result[0x140:], RECOMPRESSED_FRAME)
        self.assertEqual(zstd.frame, SOURCE_FRAME)
        self.assertEqual(zstd.decompressed_frame, SOURCE_FRAME)
        self.assertEqual(
            zstd.compressed_payload,
            b"payload-before|" + NEW_TABLE + b"|payload-after",
        )
        self.assertNotIn(OLD_CUE_NAME.encode("ascii"), result[:0x140])
        self.assertIn(NEW_CUE_NAME.encode("ascii"), result[:0x140])
        self.assertEqual(report["payload_frame_offset"], 0x140)
        self.assertEqual(
            report["source_payload_compressed_size"],
            len(SOURCE_FRAME),
        )
        self.assertEqual(
            report["output_payload_compressed_size"],
            len(RECOMPRESSED_FRAME),
        )

    def test_rejects_stale_compressed_size_from_header(self) -> None:
        payload = _source_payload()
        stale_size = len(SOURCE_FRAME)
        source = _source_state()
        zstd = _FakeZstd(payload, frame_size=stale_size - 1)

        with (
            patch.object(migration, "_archive_table", side_effect=_archive_table),
            self.assertRaisesRegex(
                migration.StateMigrationError,
                "header compressed size does not match",
            ),
        ):
            migration.migrate_state(
                source,
                old_disc=Path("old.bin"),
                new_disc=Path("new.bin"),
                old_cue_name=OLD_CUE_NAME,
                new_cue_name=NEW_CUE_NAME,
                zstd=zstd,
            )

    def test_rejects_stale_uncompressed_size_from_header(self) -> None:
        payload = _source_payload()
        source = _source_state(declared_payload_size=len(payload) + 1)
        zstd = _FakeZstd(payload)

        with (
            patch.object(migration, "_archive_table", side_effect=_archive_table),
            self.assertRaisesRegex(
                migration.StateMigrationError,
                "header uncompressed size does not match",
            ),
        ):
            migration.migrate_state(
                source,
                old_disc=Path("old.bin"),
                new_disc=Path("new.bin"),
                old_cue_name=OLD_CUE_NAME,
                new_cue_name=NEW_CUE_NAME,
                zstd=zstd,
            )

    def test_rejects_header_span_that_does_not_end_at_eof(self) -> None:
        payload = _source_payload()
        zstd = _FakeZstd(payload)
        cases = (
            (
                "past EOF",
                _source_state(declared_frame_size=len(SOURCE_FRAME) + 1),
                "compressed data past EOF",
            ),
            (
                "trailing data",
                _source_state(tail=b"\x00"),
                "unsupported trailing data",
            ),
        )

        for label, source, message in cases:
            with (
                self.subTest(label=label),
                patch.object(
                    migration,
                    "_archive_table",
                    side_effect=_archive_table,
                ),
                self.assertRaisesRegex(
                    migration.StateMigrationError,
                    message,
                ),
            ):
                migration.migrate_state(
                    source,
                    old_disc=Path("old.bin"),
                    new_disc=Path("new.bin"),
                    old_cue_name=OLD_CUE_NAME,
                    new_cue_name=NEW_CUE_NAME,
                    zstd=zstd,
                )

    def test_tolerates_only_the_volatile_final_archive_table_byte(self) -> None:
        payload = bytearray(_source_payload())
        table_offset = payload.index(OLD_TABLE)
        payload[table_offset + len(OLD_TABLE) - 1] ^= 0xFF
        source = _source_state(declared_payload_size=len(payload))
        zstd = _FakeZstd(bytes(payload))

        with patch.object(migration, "_archive_table", side_effect=_archive_table):
            _result, report = migration.migrate_state(
                source,
                old_disc=Path("old.bin"),
                new_disc=Path("new.bin"),
                old_cue_name=OLD_CUE_NAME,
                new_cue_name=NEW_CUE_NAME,
                zstd=zstd,
            )

        self.assertEqual(report["volatile_source_table_bytes"], 1)
        self.assertEqual(
            zstd.compressed_payload,
            b"payload-before|" + NEW_TABLE + b"|payload-after",
        )

    def test_rejects_archive_table_drift_before_the_final_byte(self) -> None:
        payload = bytearray(_source_payload())
        table_offset = payload.index(OLD_TABLE)
        payload[table_offset + len(OLD_TABLE) - 2] ^= 0xFF
        source = _source_state(declared_payload_size=len(payload))

        with (
            patch.object(migration, "_archive_table", side_effect=_archive_table),
            self.assertRaisesRegex(
                migration.StateMigrationError,
                "does not contain exactly one",
            ),
        ):
            migration.migrate_state(
                source,
                old_disc=Path("old.bin"),
                new_disc=Path("new.bin"),
                old_cue_name=OLD_CUE_NAME,
                new_cue_name=NEW_CUE_NAME,
                zstd=_FakeZstd(bytes(payload)),
            )


class PackagedContinuationTests(unittest.TestCase):
    def test_v60_state_header_and_hash_match_the_checked_release(self) -> None:
        project = Path(__file__).resolve().parents[2]
        state = (project / "output" / "MASS_DRIVER_V60_CONTINUE.sav").read_bytes()

        self.assertEqual(state[:4], b"DUCC")
        self.assertEqual(
            hashlib.sha256(state).hexdigest(),
            "fa9880cdab354ddf2b4d17ce3dce951c78a09dace1d6ece70135824bf005e200",
        )
        compression_type, compressed_size, uncompressed_size, offset = (
            struct.unpack_from("<IIII", state, 0xC8)
        )
        self.assertEqual(compression_type, 2)
        self.assertEqual(offset, 98422)
        self.assertEqual(uncompressed_size, 3817114)
        self.assertEqual(compressed_size, 1876885)
        self.assertEqual(offset + compressed_size, len(state))
        self.assertEqual(state[offset : offset + 4], migration.ZSTD_MAGIC)

    def test_v60_launcher_uses_foreground_stateful_startup(self) -> None:
        project = Path(__file__).resolve().parents[2]
        launcher = (
            project / "output" / "CONTINUE_MASS_DRIVER_V60.cmd"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'set "DISC=%~dp0Xenogears_PW_CD2_mass_driver_standalone_v60.cue"',
            launcher,
        )
        self.assertIn(
            'set "STATE=%~dp0MASS_DRIVER_V60_CONTINUE.sav"',
            launcher,
        )
        self.assertIn(
            '"%DUCKSTATION%" -nofullscreen '
            '-statefile "%STATE%" -- "%DISC%"',
            launcher,
        )
        self.assertNotIn('start "" "%DUCKSTATION%"', launcher)
        self.assertNotIn("-batch", launcher.lower())
        self.assertIn("DuckStation exited with code", launcher)


if __name__ == "__main__":
    unittest.main()
