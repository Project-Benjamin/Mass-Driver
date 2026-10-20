from __future__ import annotations

import hashlib
from pathlib import Path
import struct
import unittest

from tools.migrate_duckstation_disc_state import (
    DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
    _Zstd,
)
import tools.repair_guardian_v143_state as repair
from work.read_duckstation_runtime import RAM_SIZE, _psx_ram_offset


PROJECT = Path(__file__).resolve().parents[3]
SOURCE_STATE = (
    PROJECT
    / "work"
    / "runtime_capture"
    / "guardian_v143_authorization_console.sav"
)
REPAIRED_STATE = (
    PROJECT
    / "work"
    / "runtime_capture"
    / "guardian_v143_authorization_console_resource29_repaired.sav"
)
V142_RESOURCE = (
    PROJECT
    / "work"
    / "mass_driver_v142_stage"
    / "replacements"
    / "29_el_regulus_level1_deathblow_names.bin"
)
V143_RESOURCE = (
    PROJECT
    / "work"
    / "mass_driver_v143_stage"
    / "replacements"
    / "29_el_regulus_level1_deathblow_names.bin"
)
ZSTD_LIBRARY = PROJECT / "work" / "duckstation" / "zstd.dll"
EXPECTED_OUTPUT_SHA256 = (
    "86860bd7ae97f83797a61929cddcba446cd6157459fb80eabb85e609db646a4e"
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _outer_offsets(decoded: bytes) -> tuple[int, ...]:
    count = struct.unpack_from("<I", decoded, 0)[0]
    return struct.unpack_from(f"<{count}I", decoded, 4)


def _outer_entry(decoded: bytes, index: int) -> bytes:
    offsets = _outer_offsets(decoded)
    end = offsets[index + 1] if index + 1 < len(offsets) else len(decoded)
    return decoded[offsets[index] : end]


class GuardianV143StateRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.zstd = _Zstd(ZSTD_LIBRARY)
        cls.source_state = SOURCE_STATE.read_bytes()
        cls.expected_state = REPAIRED_STATE.read_bytes()
        cls.result_state, cls.report = repair.repair_state(
            cls.source_state,
            v142_resource=V142_RESOURCE,
            v143_resource=V143_RESOURCE,
            zstd=cls.zstd,
        )
        cls.source_payload, cls.source_frame_start = repair._state_payload(
            cls.source_state,
            cls.zstd,
        )
        cls.result_payload, cls.result_frame_start = repair._state_payload(
            cls.result_state,
            cls.zstd,
        )
        cls.ram_offset = _psx_ram_offset(cls.source_payload)
        cls.resource_payload_start = cls.ram_offset + repair.RESOURCE_RAM_BASE
        cls.resource_payload_end = (
            cls.resource_payload_start + repair.V142_DECODED_SIZE
        )
        cls.source_ram = cls.source_payload[
            cls.ram_offset : cls.ram_offset + RAM_SIZE
        ]
        cls.result_ram = cls.result_payload[
            cls.ram_offset : cls.ram_offset + RAM_SIZE
        ]
        cls.v142_decoded = repair._load_resource(
            V142_RESOURCE,
            packed_sha256=repair.V142_RESOURCE_SHA256,
            decoded_sha256=repair.V142_DECODED_SHA256,
            decoded_size=repair.V142_DECODED_SIZE,
            expected_offsets=repair.V142_ENTRY_OFFSETS,
        )
        cls.v143_decoded = repair._load_resource(
            V143_RESOURCE,
            packed_sha256=repair.V143_RESOURCE_SHA256,
            decoded_sha256=repair.V143_DECODED_SHA256,
            decoded_size=repair.V143_DECODED_SIZE,
            expected_offsets=repair.V143_ENTRY_OFFSETS,
        )
        cls.v142_runtime = repair._runtime_archive(cls.v142_decoded)
        cls.v143_runtime = repair._runtime_archive(cls.v143_decoded)
        cls.repaired_runtime = cls.v143_runtime[:-1]

    def test_source_hash_guard_and_exact_repaired_state_hash(self) -> None:
        self.assertEqual(_sha256(self.source_state), repair.SOURCE_STATE_SHA256)
        drifted = self.source_state[:-1] + bytes([self.source_state[-1] ^ 1])
        with self.assertRaisesRegex(
            repair.GuardianStateRepairError,
            "source authorization state hash drifted",
        ):
            repair.repair_state(
                drifted,
                v142_resource=V142_RESOURCE,
                v143_resource=V143_RESOURCE,
                zstd=self.zstd,
            )

        self.assertEqual(self.result_state, self.expected_state)
        self.assertEqual(_sha256(self.result_state), EXPECTED_OUTPUT_SHA256)
        self.assertEqual(self.report["output_sha256"], EXPECTED_OUTPUT_SHA256)
        self.assertEqual(
            (len(self.source_state), len(self.result_state)),
            (1_745_291, 1_745_310),
        )

    def test_payload_delta_is_exactly_the_resource_29_allocation(self) -> None:
        start = self.resource_payload_start
        end = self.resource_payload_end
        self.assertEqual(len(self.source_payload), len(self.result_payload))
        self.assertEqual(self.source_payload[:start], self.result_payload[:start])
        self.assertEqual(self.source_payload[end:], self.result_payload[end:])
        self.assertEqual(self.source_payload[start:end], self.v142_runtime)
        self.assertEqual(self.result_payload[start:end], self.repaired_runtime)

        changed_offsets = tuple(
            offset
            for offset, (before, after) in enumerate(
                zip(self.source_payload, self.result_payload, strict=True)
            )
            if before != after
        )
        self.assertEqual(len(changed_offsets), 16_751)
        self.assertTrue(changed_offsets)
        self.assertGreaterEqual(changed_offsets[0], start)
        self.assertLess(changed_offsets[-1], end)
        self.assertEqual(self.report["resource_bytes_changed"], 16_751)
        self.assertEqual(self.report["payload_bytes_changed_outside_resource"], 0)

    def test_entry_37_38_and_every_command_pointer_lhu_site_are_even(self) -> None:
        pointers = tuple(
            struct.unpack_from(
                "<I",
                self.result_ram,
                repair.RESOURCE_RAM_BASE + 4 + 4 * index,
            )[0]
            for index in range(repair.OUTER_ENTRY_COUNT)
        )
        expected_pointers = tuple(
            repair.RESOURCE_GUEST_BASE + offset
            for offset in _outer_offsets(self.v143_decoded)
        )
        self.assertEqual(pointers, expected_pointers)
        self.assertTrue(all(pointer % 2 == 0 for pointer in pointers))
        self.assertEqual(
            (pointers[37], pointers[38]),
            (0x801F859C, 0x801F8664),
        )

        for entry_index in (37, 38):
            with self.subTest(entry=entry_index):
                entry_offset = pointers[entry_index] - repair.RESOURCE_GUEST_BASE
                max_index = struct.unpack_from(
                    "<I",
                    self.repaired_runtime,
                    entry_offset,
                )[0]
                self.assertEqual(max_index, 14)
                lhu_sites = tuple(
                    pointers[entry_index] + 4 + 2 * index
                    for index in range(max_index + 1)
                )
                self.assertEqual(len(lhu_sites), 15)
                self.assertTrue(all(address % 2 == 0 for address in lhu_sites))

    def test_final_padding_trade_keeps_allocation_and_following_header(self) -> None:
        self.assertEqual(
            (len(self.v142_runtime), len(self.v143_runtime)),
            (repair.V142_DECODED_SIZE, repair.V143_DECODED_SIZE),
        )
        self.assertEqual(len(self.repaired_runtime), len(self.v142_runtime))
        self.assertEqual(self.repaired_runtime, self.v143_runtime[:-1])
        self.assertEqual(self.v143_runtime[-1], 0)

        self.assertEqual(
            _outer_entry(self.v143_decoded, 22),
            _outer_entry(self.v142_decoded, 22) + b"\x00",
        )
        for index in range(23, repair.OUTER_ENTRY_COUNT):
            with self.subTest(unchanged_outer_entry=index):
                self.assertEqual(
                    _outer_entry(self.v143_decoded, index),
                    _outer_entry(self.v142_decoded, index),
                )

        entry_start, logical_end = repair._entry_52_logical_end(
            self.v143_decoded
        )
        full_entry_size = len(self.v143_decoded) - entry_start
        self.assertEqual(full_entry_size - logical_end, 10)
        self.assertEqual(
            self.repaired_runtime[entry_start + logical_end :],
            self.v143_runtime[entry_start + logical_end : -1],
        )
        self.assertEqual(
            self.v143_runtime[entry_start + logical_end :],
            b"\x77" + bytes(9),
        )

        block_end = repair.RESOURCE_RAM_BASE + repair.V142_DECODED_SIZE
        self.assertEqual(
            self.source_ram[block_end : block_end + len(repair.NEXT_HEAP_HEADER)],
            repair.NEXT_HEAP_HEADER,
        )
        self.assertEqual(
            self.result_ram[block_end : block_end + len(repair.NEXT_HEAP_HEADER)],
            repair.NEXT_HEAP_HEADER,
        )

    def test_gameplay_and_runtime_state_are_byte_identical_outside_resource_29(
        self,
    ) -> None:
        ram_start = repair.RESOURCE_RAM_BASE
        ram_end = ram_start + repair.V142_DECODED_SIZE
        self.assertEqual(self.source_ram[:ram_start], self.result_ram[:ram_start])
        self.assertEqual(self.source_ram[ram_end:], self.result_ram[ram_end:])
        self.assertEqual(self.source_frame_start, self.result_frame_start)

        source_header = bytearray(self.source_state[: self.source_frame_start])
        result_header = bytearray(self.result_state[: self.result_frame_start])
        source_header[
            DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET :
            DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET + 4
        ] = bytes(4)
        result_header[
            DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET :
            DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET + 4
        ] = bytes(4)
        self.assertEqual(source_header, result_header)
        self.assertEqual(
            self.source_state.count(repair.V143_CUE_NAME),
            self.result_state.count(repair.V143_CUE_NAME),
        )
        self.assertEqual(self.result_state.count(repair.V143_CUE_NAME), 1)


if __name__ == "__main__":
    unittest.main()
