#!/usr/bin/env python3
"""Repair the warm V143 Guardian authorization state without moving gameplay.

The V143 disc contains an aligned system-name archive, but the authorization
state was migrated after V142 had already decoded canonical 29 into RAM.  This
tool replaces only that decoded RAM block.  The replacement stays the exact
same allocation size by dropping one audited, unused final padding zero from
V143 outer entry 52; allocator headers and every byte of gameplay state remain
at their original addresses.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import struct
import sys
from typing import Sequence

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
else:
    project_root = Path(__file__).resolve().parents[3]

from tools.migrate_duckstation_disc_state import (
    DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
    DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET,
    DUCKSTATION_STATE_HEADER_SIZE,
    DUCKSTATION_STATE_MAGIC,
    DUCKSTATION_ZSTD_COMPRESSION_TYPE,
    StateMigrationError,
    _Zstd,
)
from work.read_duckstation_runtime import RAM_SIZE, _psx_ram_offset


SOURCE_STATE_SHA256 = (
    "fe8052037cec5b2f1349763be0df965c87d968b5513170947bf70f1132b352ff"
)
V142_RESOURCE_SHA256 = (
    "851076cf9d59288f581800786fa92454e13046187dc2ae05cb1409afe9de5303"
)
V143_RESOURCE_SHA256 = (
    "b2feb89ac7031b5007aa137e2711ca0ab2f5b48efbe0d55ee040f98f81192816"
)
V142_DECODED_SHA256 = (
    "9f60f94ed430b0be5d8cd48e818e7a3ac4df6dca2a1d00b7f6096e47e546dbe4"
)
V143_DECODED_SHA256 = (
    "f13e56005378583b43ea7ae27fd028a0f7651b48e6c186a91c2a07d147898c60"
)

V143_CUE_NAME = b"Xenogears_PW_CD2_mass_driver_standalone_v143.cue"
RESOURCE_GUEST_BASE = 0x801F34BC
RESOURCE_RAM_BASE = RESOURCE_GUEST_BASE & 0x1FFFFF
OUTER_ENTRY_COUNT = 53
V142_DECODED_SIZE = 0x7168
V143_DECODED_SIZE = 0x7169
V142_ENTRY_OFFSETS = {
    22: 0x17C0,
    23: 0x2165,
    37: 0x50DF,
    38: 0x51A7,
    52: 0x6E07,
}
V143_ENTRY_OFFSETS = {
    22: 0x17C0,
    23: 0x2166,
    37: 0x50E0,
    38: 0x51A8,
    52: 0x6E08,
}
NEXT_HEAP_HEADER = bytes.fromhex("00 C0 1F 80 A5 CB C0 C2")


class GuardianStateRepairError(RuntimeError):
    """Raised before writing if any byte-level repair guard drifts."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _decode_lzss_complete_groups(stream: bytes) -> bytes:
    """Decode the complete eight-command groups used by canonical 29."""

    if len(stream) < 4:
        raise GuardianStateRepairError("canonical 29 is shorter than its header")
    declared_size = struct.unpack_from("<I", stream, 0)[0]
    position = 4
    output = bytearray()
    padded_stream = stream + bytes(16)
    while len(output) < declared_size:
        if position >= len(padded_stream):
            raise GuardianStateRepairError("canonical 29 ends before a command group")
        control = padded_stream[position]
        position += 1
        for bit in range(8):
            if control & (1 << bit):
                if position + 2 > len(padded_stream):
                    raise GuardianStateRepairError(
                        "canonical 29 ends inside a backreference"
                    )
                low = padded_stream[position]
                high = padded_stream[position + 1]
                position += 2
                distance = low | ((high & 0x0F) << 8)
                length = (high >> 4) + 3
                if not 1 <= distance <= len(output):
                    raise GuardianStateRepairError(
                        "canonical 29 has an invalid backreference"
                    )
                for _ in range(length):
                    output.append(output[-distance])
            else:
                if position >= len(padded_stream):
                    raise GuardianStateRepairError(
                        "canonical 29 ends inside a literal"
                    )
                output.append(padded_stream[position])
                position += 1
        if len(output) > declared_size:
            raise GuardianStateRepairError(
                "canonical 29 command group overruns its declared allocation"
            )
    return bytes(output)


def _load_resource(
    path: Path,
    *,
    packed_sha256: str,
    decoded_sha256: str,
    decoded_size: int,
    expected_offsets: dict[int, int],
) -> bytes:
    packed = path.read_bytes()
    if _sha256(packed) != packed_sha256:
        raise GuardianStateRepairError(f"unexpected canonical-29 hash: {path}")
    decoded = _decode_lzss_complete_groups(packed)
    if (len(decoded), _sha256(decoded)) != (decoded_size, decoded_sha256):
        raise GuardianStateRepairError(f"unexpected decoded canonical 29: {path}")
    count = struct.unpack_from("<I", decoded, 0)[0]
    if count != OUTER_ENTRY_COUNT:
        raise GuardianStateRepairError(f"canonical 29 has {count} outer entries")
    offsets = struct.unpack_from(f"<{count}I", decoded, 4)
    if tuple(offsets) != tuple(sorted(offsets)) or offsets[-1] >= len(decoded):
        raise GuardianStateRepairError("canonical-29 outer offsets are invalid")
    for index, expected in expected_offsets.items():
        if offsets[index] != expected:
            raise GuardianStateRepairError(
                f"canonical-29 entry {index} is 0x{offsets[index]:X}, "
                f"expected 0x{expected:X}"
            )
    return decoded


def _runtime_archive(decoded: bytes) -> bytes:
    """Model the loader's in-place conversion of outer offsets to pointers."""

    result = bytearray(decoded)
    count = struct.unpack_from("<I", result, 0)[0]
    for index in range(count):
        table_position = 4 + index * 4
        offset = struct.unpack_from("<I", result, table_position)[0]
        struct.pack_into("<I", result, table_position, RESOURCE_GUEST_BASE + offset)
    return bytes(result)


def _entry_52_logical_end(decoded: bytes) -> tuple[int, int]:
    count = struct.unpack_from("<I", decoded, 0)[0]
    entry_start = struct.unpack_from(f"<{count}I", decoded, 4)[52]
    entry = decoded[entry_start:]
    string_count = struct.unpack_from("<I", entry, 0)[0] + 1
    offsets = struct.unpack_from(f"<{string_count}H", entry, 4)
    if 4 + string_count * 4 != offsets[0]:
        raise GuardianStateRepairError("entry 52 dimensions/string table drifted")
    ends = []
    for offset in offsets:
        if not 0 <= offset < len(entry):
            raise GuardianStateRepairError("entry 52 has an invalid string offset")
        terminator = entry.find(b"\x00", offset)
        if terminator < 0:
            raise GuardianStateRepairError("entry 52 has an unterminated string")
        ends.append(terminator + 1)
    return entry_start, max(ends)


def _state_payload(state: bytes, zstd: _Zstd) -> tuple[bytes, int]:
    if len(state) < DUCKSTATION_STATE_HEADER_SIZE or state[:4] != DUCKSTATION_STATE_MAGIC:
        raise GuardianStateRepairError("input is not a supported DuckStation state")
    compression, compressed_size, payload_size, frame_start = struct.unpack_from(
        "<IIII", state, DUCKSTATION_DATA_COMPRESSION_TYPE_OFFSET
    )
    if compression != DUCKSTATION_ZSTD_COMPRESSION_TYPE:
        raise GuardianStateRepairError("DuckStation state is not Zstandard-compressed")
    if not DUCKSTATION_STATE_HEADER_SIZE <= frame_start < len(state):
        raise GuardianStateRepairError("DuckStation state data offset is invalid")
    if frame_start + compressed_size != len(state):
        raise GuardianStateRepairError("DuckStation compressed span does not end at EOF")
    payload = zstd.decompress(state[frame_start:])
    if len(payload) != payload_size:
        raise GuardianStateRepairError("DuckStation uncompressed size is inconsistent")
    return payload, frame_start


def _assert_no_external_downstream_pointers(ram: bytes, block_size: int) -> None:
    """No aligned cached pointer may require relocation with entries 23-52."""

    downstream_start = RESOURCE_GUEST_BASE + V142_ENTRY_OFFSETS[23]
    downstream_end = RESOURCE_GUEST_BASE + block_size
    block_end = RESOURCE_RAM_BASE + block_size
    for offset in range(0, len(ram) - 3, 4):
        if RESOURCE_RAM_BASE <= offset < block_end:
            continue
        value = struct.unpack_from("<I", ram, offset)[0]
        if downstream_start <= value < downstream_end:
            raise GuardianStateRepairError(
                f"cached downstream canonical-29 pointer 0x{value:08X} "
                f"exists at RAM 0x{offset:X}"
            )


def repair_state(
    state: bytes,
    *,
    v142_resource: Path,
    v143_resource: Path,
    zstd: _Zstd,
) -> tuple[bytes, dict[str, object]]:
    if _sha256(state) != SOURCE_STATE_SHA256:
        raise GuardianStateRepairError("source authorization state hash drifted")
    if state.count(V143_CUE_NAME) != 1:
        raise GuardianStateRepairError("source state does not name the V143 CUE once")

    old_decoded = _load_resource(
        v142_resource,
        packed_sha256=V142_RESOURCE_SHA256,
        decoded_sha256=V142_DECODED_SHA256,
        decoded_size=V142_DECODED_SIZE,
        expected_offsets=V142_ENTRY_OFFSETS,
    )
    new_decoded = _load_resource(
        v143_resource,
        packed_sha256=V143_RESOURCE_SHA256,
        decoded_sha256=V143_DECODED_SHA256,
        decoded_size=V143_DECODED_SIZE,
        expected_offsets=V143_ENTRY_OFFSETS,
    )
    entry_start, logical_end = _entry_52_logical_end(new_decoded)
    full_entry_size = len(new_decoded) - entry_start
    if (
        new_decoded[-1] != 0
        or full_entry_size - logical_end != 10
        or full_entry_size - 1 - logical_end != 9
    ):
        raise GuardianStateRepairError(
            "V143 final-byte removal is not confined to audited entry-52 padding"
        )

    old_runtime = _runtime_archive(old_decoded)
    full_new_runtime = _runtime_archive(new_decoded)
    repaired_runtime = full_new_runtime[:-1]
    if len(old_runtime) != len(repaired_runtime) or len(old_runtime) != V142_DECODED_SIZE:
        raise GuardianStateRepairError("same-allocation repair size contract drifted")

    payload, frame_start = _state_payload(state, zstd)
    ram_offset = _psx_ram_offset(payload)
    ram = payload[ram_offset : ram_offset + RAM_SIZE]
    block_end = RESOURCE_RAM_BASE + len(old_runtime)
    if ram[RESOURCE_RAM_BASE:block_end] != old_runtime:
        raise GuardianStateRepairError(
            "source state does not contain the exact relocated V142 canonical 29"
        )
    if ram[block_end : block_end + len(NEXT_HEAP_HEADER)] != NEXT_HEAP_HEADER:
        raise GuardianStateRepairError("canonical-29 following heap header drifted")
    _assert_no_external_downstream_pointers(ram, len(old_runtime))

    patched_payload = bytearray(payload)
    payload_block = ram_offset + RESOURCE_RAM_BASE
    patched_payload[payload_block : payload_block + len(repaired_runtime)] = (
        repaired_runtime
    )
    if (
        patched_payload[:payload_block] != payload[:payload_block]
        or patched_payload[payload_block + len(repaired_runtime) :]
        != payload[payload_block + len(repaired_runtime) :]
    ):
        raise GuardianStateRepairError("payload changed outside canonical 29")

    repaired_ram = patched_payload[ram_offset : ram_offset + RAM_SIZE]
    if repaired_ram[RESOURCE_RAM_BASE:block_end] != repaired_runtime:
        raise GuardianStateRepairError("repaired runtime archive did not verify")
    if repaired_ram[block_end : block_end + len(NEXT_HEAP_HEADER)] != NEXT_HEAP_HEADER:
        raise GuardianStateRepairError("repair overwrote the following heap header")
    for index in range(23, OUTER_ENTRY_COUNT):
        pointer = struct.unpack_from(
            "<I", repaired_ram, RESOURCE_RAM_BASE + 4 + index * 4
        )[0]
        if pointer & 1:
            raise GuardianStateRepairError(
                f"repaired outer entry {index} remains odd at 0x{pointer:08X}"
            )

    compressed = zstd.compress(bytes(patched_payload))
    prefix = bytearray(state[:frame_start])
    struct.pack_into(
        "<I", prefix, DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET, len(compressed)
    )
    result = bytes(prefix) + compressed
    verified_payload, verified_frame_start = _state_payload(result, zstd)
    if verified_frame_start != frame_start or verified_payload != patched_payload:
        raise GuardianStateRepairError("repaired state did not round-trip exactly")
    if result.count(V143_CUE_NAME) != 1:
        raise GuardianStateRepairError("repaired state changed the mounted CUE name")

    changed = sum(a != b for a, b in zip(old_runtime, repaired_runtime))
    return result, {
        "source_sha256": _sha256(state),
        "output_sha256": _sha256(result),
        "source_size": len(state),
        "output_size": len(result),
        "payload_size": len(payload),
        "ram_payload_offset": ram_offset,
        "resource_ram_span": (
            f"0x{RESOURCE_RAM_BASE:X}-0x{block_end:X}"
        ),
        "resource_allocation_size": len(repaired_runtime),
        "resource_bytes_changed": changed,
        "entry_52_full_padding": full_entry_size - logical_end,
        "entry_52_repaired_padding": full_entry_size - 1 - logical_end,
        "entry_37_pointer": f"0x{RESOURCE_GUEST_BASE + V143_ENTRY_OFFSETS[37]:08X}",
        "entry_38_pointer": f"0x{RESOURCE_GUEST_BASE + V143_ENTRY_OFFSETS[38]:08X}",
        "next_heap_header_preserved": True,
        "payload_bytes_changed_outside_resource": 0,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--v142-resource",
        type=Path,
        default=(
            project_root
            / "work"
            / "mass_driver_v142_stage"
            / "replacements"
            / "29_el_regulus_level1_deathblow_names.bin"
        ),
    )
    parser.add_argument(
        "--v143-resource",
        type=Path,
        default=(
            project_root
            / "work"
            / "mass_driver_v143_stage"
            / "replacements"
            / "29_el_regulus_level1_deathblow_names.bin"
        ),
    )
    parser.add_argument(
        "--zstd",
        type=Path,
        default=project_root / "work" / "duckstation" / "zstd.dll",
    )
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        source = args.state.resolve()
        output = args.output.resolve()
        if source == output:
            raise GuardianStateRepairError("output must not overwrite the source state")
        if output.exists() and not args.force:
            raise GuardianStateRepairError(
                f"refusing to overwrite {output}; pass --force"
            )
        result, report = repair_state(
            source.read_bytes(),
            v142_resource=args.v142_resource.resolve(),
            v143_resource=args.v143_resource.resolve(),
            zstd=_Zstd(args.zstd.resolve()),
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        print(f"Wrote {output} ({len(result)} bytes)")
        for key, value in report.items():
            print(f"{key}: {value}")
        return 0
    except (OSError, StateMigrationError, GuardianStateRepairError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
