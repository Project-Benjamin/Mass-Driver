from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

import hashlib
from pathlib import Path
import struct
import unittest

from tools.migrate_duckstation_disc_state import (
    DUCKSTATION_DATA_OFFSET_OFFSET,
    _Zstd,
)
from tools.migrate_rico_arc_stove_slot1 import (
    DEFAULT_BUNDLE,
    DEFAULT_ZSTD,
    EXPECTED_SCRIPT_DIFF,
    REPAIRED_SCRIPT_SHA256,
    SOURCE_STATE_SHA256,
    RicoStoveStateMigrationError,
    migrate_state,
)
from work.read_duckstation_runtime import _psx_ram_offset


ROOT = REPOSITORY_ROOT
SOURCE_STATE = ROOT / "emulator_data" / "SLUS-00664_1.sav"
EXPECTED_REPAIRED_STATE_SHA256 = (
    "02f940c3a6ac8e0848dc7b2effcd9fff11d863d8ee0c2af2366e373b38c87ff8"
)
EXPECTED_REPAIRED_PAYLOAD_SHA256 = (
    "1fe0840a9aeaf0e53993e77c22ee452c54fb6e167e75c5a615599265828cb05d"
)


class RicoStoveSlotOneMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not SOURCE_STATE.is_file():
            raise unittest.SkipTest("Audited Rico Slot 1 is unavailable")
        if not DEFAULT_BUNDLE.is_file() or not DEFAULT_ZSTD.is_file():
            raise unittest.SkipTest("Rebuilt Chapter 1 bundle or zstd is unavailable")
        cls.source = SOURCE_STATE.read_bytes()
        if hashlib.sha256(cls.source).hexdigest() != SOURCE_STATE_SHA256:
            raise unittest.SkipTest("Live Slot 1 is no longer the audited stove state")
        cls.zstd = _Zstd(DEFAULT_ZSTD)
        cls.result, cls.report = migrate_state(
            cls.source,
            repaired_field_bundle=DEFAULT_BUNDLE.read_bytes(),
            zstd=cls.zstd,
        )

    def test_migration_has_the_exact_checked_identity(self) -> None:
        self.assertEqual(
            hashlib.sha256(self.result).hexdigest(),
            EXPECTED_REPAIRED_STATE_SHA256,
        )
        self.assertEqual(
            self.report["payload_sha256"],
            EXPECTED_REPAIRED_PAYLOAD_SHA256,
        )
        self.assertEqual(
            self.report["resident_script_sha256"],
            REPAIRED_SCRIPT_SHA256,
        )

    def test_only_the_gate_literal_changes_in_decompressed_state(self) -> None:
        source_frame = struct.unpack_from(
            "<I", self.source, DUCKSTATION_DATA_OFFSET_OFFSET
        )[0]
        result_frame = struct.unpack_from(
            "<I", self.result, DUCKSTATION_DATA_OFFSET_OFFSET
        )[0]
        self.assertEqual(source_frame, result_frame)
        source_payload = self.zstd.decompress(self.source[source_frame:])
        result_payload = self.zstd.decompress(self.result[result_frame:])
        differences = [
            (offset, old, new)
            for offset, (old, new) in enumerate(zip(source_payload, result_payload))
            if old != new
        ]
        self.assertEqual(
            differences,
            [
                (
                    self.report["changed_payload_offset"],
                    EXPECTED_SCRIPT_DIFF[1],
                    EXPECTED_SCRIPT_DIFF[2],
                )
            ],
        )
        self.assertEqual(_psx_ram_offset(source_payload), _psx_ram_offset(result_payload))

    def test_migration_rejects_any_source_drift(self) -> None:
        altered = bytearray(self.source)
        altered[0x20] ^= 1
        with self.assertRaisesRegex(
            RicoStoveStateMigrationError,
            "Source Slot 1 identity changed",
        ):
            migrate_state(
                bytes(altered),
                repaired_field_bundle=DEFAULT_BUNDLE.read_bytes(),
                zstd=self.zstd,
            )


if __name__ == "__main__":
    unittest.main()
