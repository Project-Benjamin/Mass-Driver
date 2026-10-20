from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import unittest

import tools.grant_all_deathblows_duckstation_state as state_grant
from tools.migrate_duckstation_disc_state import (
    DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    DUCKSTATION_STATE_HEADER_SIZE,
    DUCKSTATION_ZSTD_COMPRESSION_TYPE,
    ZSTD_MAGIC,
)
from tools.xgdeathblows import DEATHBLOW_PROFILES, learned_mask


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_GAMESTATE = (
    PROJECT_ROOT
    / "work"
    / "mass_driver_v162_stage"
    / "replacements"
    / "2595_standalone_gamestate.bin"
)
SOURCE_FRAME = ZSTD_MAGIC + b"source-state-frame"
OUTPUT_FRAME = ZSTD_MAGIC + b"recompressed-deathblow-state-frame"


class _FakeZstd:
    def __init__(self, source_payload: bytes):
        self.source_payload = source_payload
        self.output_payload: bytes | None = None

    def frame_size(self, frame: bytes) -> int:
        return len(frame)

    def decompress(self, frame: bytes) -> bytes:
        if frame == SOURCE_FRAME:
            return self.source_payload
        if frame == OUTPUT_FRAME and self.output_payload is not None:
            return self.output_payload
        raise AssertionError(f"Unexpected fake Zstandard frame: {frame!r}")

    def compress(self, payload: bytes) -> bytes:
        self.output_payload = payload
        return OUTPUT_FRAME


def _source_state() -> tuple[bytes, bytes]:
    gamestate = bytearray(SOURCE_GAMESTATE.read_bytes())
    struct.pack_into(
        "<H", gamestate, state_grant.GAMESTATE_FIELD_OFFSET, 621
    )
    payload = bytearray(state_grant.GAMESTATE_PAYLOAD_OFFSET + len(gamestate) + 0x40)
    payload[
        state_grant.GAMESTATE_PAYLOAD_OFFSET :
        state_grant.GAMESTATE_PAYLOAD_OFFSET + len(gamestate)
    ] = gamestate
    prefix = bytearray(DUCKSTATION_STATE_HEADER_SIZE)
    prefix[:4] = b"DUCC"
    struct.pack_into(
        "<IIII",
        prefix,
        DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
        DUCKSTATION_ZSTD_COMPRESSION_TYPE,
        len(SOURCE_FRAME),
        len(payload),
        DUCKSTATION_STATE_HEADER_SIZE,
    )
    return bytes(prefix) + SOURCE_FRAME, bytes(payload)


class DuckStationDeathblowGrantTests(unittest.TestCase):
    def test_state_migration_changes_only_sixteen_gamestate_bytes(self) -> None:
        source, payload = _source_state()
        zstd = _FakeZstd(payload)
        result, report = state_grant.grant_deathblows_to_state(
            source,
            zstd=zstd,
            expected_source_sha256=hashlib.sha256(source).hexdigest(),
            expected_field=621,
        )

        self.assertEqual(report["gamestate_field"], 621)
        self.assertEqual(report["changed_gamestate_bytes"], 16)
        self.assertEqual(report["changed_payload_bytes"], 16)
        self.assertFalse(report["levels_changed"])
        self.assertFalse(report["stats_changed"])
        self.assertEqual(result[DUCKSTATION_STATE_HEADER_SIZE:], OUTPUT_FRAME)
        self.assertEqual(zstd.output_payload[:state_grant.GAMESTATE_PAYLOAD_OFFSET], payload[:state_grant.GAMESTATE_PAYLOAD_OFFSET])

        end = state_grant.GAMESTATE_PAYLOAD_OFFSET + state_grant.GAMESTATE_SIZE
        self.assertEqual(zstd.output_payload[end:], payload[end:])
        source_gamestate = payload[state_grant.GAMESTATE_PAYLOAD_OFFSET:end]
        final_gamestate = zstd.output_payload[state_grant.GAMESTATE_PAYLOAD_OFFSET:end]
        self.assertEqual(final_gamestate[0x026C:0x0978], source_gamestate[0x026C:0x0978])
        for profile in DEATHBLOW_PROFILES:
            with self.subTest(character=profile.character):
                self.assertEqual(
                    learned_mask(final_gamestate, profile.character_id),
                    learned_mask(source_gamestate, profile.character_id)
                    | profile.full_mask,
                )

        expected_prefix = bytearray(source[:DUCKSTATION_STATE_HEADER_SIZE])
        struct.pack_into("<I", expected_prefix, 0xCC, len(OUTPUT_FRAME))
        self.assertEqual(result[:DUCKSTATION_STATE_HEADER_SIZE], bytes(expected_prefix))

    def test_idempotent_migration_keeps_payload_identical(self) -> None:
        source, payload = _source_state()
        first_zstd = _FakeZstd(payload)
        _first_state, _report = state_grant.grant_deathblows_to_state(
            source,
            zstd=first_zstd,
            expected_source_sha256=hashlib.sha256(source).hexdigest(),
            expected_field=621,
        )
        upgraded_payload = first_zstd.output_payload
        self.assertIsNotNone(upgraded_payload)

        second_source_prefix = bytearray(source[:DUCKSTATION_STATE_HEADER_SIZE])
        struct.pack_into("<I", second_source_prefix, 0xCC, len(SOURCE_FRAME))
        second_source = bytes(second_source_prefix) + SOURCE_FRAME
        second_zstd = _FakeZstd(upgraded_payload)
        _second_state, report = state_grant.grant_deathblows_to_state(
            second_source,
            zstd=second_zstd,
            expected_source_sha256=hashlib.sha256(second_source).hexdigest(),
            expected_field=621,
        )
        self.assertEqual(report["changed_payload_bytes"], 0)
        self.assertEqual(second_zstd.output_payload, upgraded_payload)

    def test_guards_reject_wrong_hash_field_and_envelope(self) -> None:
        source, payload = _source_state()
        with self.assertRaisesRegex(state_grant.StateDeathblowError, "SHA-256"):
            state_grant.grant_deathblows_to_state(
                source,
                zstd=_FakeZstd(payload),
                expected_source_sha256="0" * 64,
                expected_field=621,
            )
        with self.assertRaisesRegex(state_grant.StateDeathblowError, "expected field"):
            state_grant.grant_deathblows_to_state(
                source,
                zstd=_FakeZstd(payload),
                expected_source_sha256=hashlib.sha256(source).hexdigest(),
                expected_field=550,
            )
        with self.assertRaisesRegex(
            state_grant.StateDeathblowError, "supported DuckStation"
        ):
            state_grant.grant_deathblows_to_state(
                b"bad state",
                zstd=_FakeZstd(payload),
                expected_source_sha256=hashlib.sha256(b"bad state").hexdigest(),
                expected_field=621,
            )

        with self.assertRaisesRegex(
            state_grant.StateDeathblowError, "exact source SHA-256"
        ):
            state_grant.grant_deathblows_to_state(
                source,
                zstd=_FakeZstd(payload),
            )


if __name__ == "__main__":
    unittest.main()
