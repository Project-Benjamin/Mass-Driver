#!/usr/bin/env python3
"""Checked MODE2/Form1 sector repair and standalone Xenogears boot patch."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import sys
from typing import Sequence


RAW_SECTOR_SIZE = 2352
USER_DATA_OFFSET = 24
SLUS_HEADER_LBA = 172918
SLUS_TARGET_LBA = 172938
SLUS_TEXT_SIZE = 0x49800
PATCH_CONTEXT_OFFSET = 0x128
PATCH_CONTEXT_BEFORE = bytes.fromhex(
    "00 00 00 00 5B 66 00 0C 06 00 04 34 B3 66 00 0C"
)
PATCH_CONTEXT_AFTER = bytes.fromhex(
    "00 00 00 00 5B 66 00 0C 01 00 04 34 B3 66 00 0C"
)
RETAIL_TARGET_SECTOR_SHA256 = (
    "7463eab81506e4f9a2b84691634776de3c2ebe4c3794237af8825a44fb921852"
)
PATCHED_TARGET_SECTOR_SHA256 = (
    "79a0d23b2320ba4a3487623e7199b2e393758ce9d33b006c9c284d0d99d188bc"
)


class Mode2PatchError(RuntimeError):
    """Raised before any write when the audited disc layout does not match."""


@dataclass(frozen=True)
class BootPatchResult:
    image: Path
    lba: int
    before_sha256: str
    after_sha256: str
    already_patched: bool


@dataclass(frozen=True)
class BootVerificationResult:
    image: Path
    lba: int
    sha256: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tables() -> tuple[list[int], list[int], list[int]]:
    forward = [0] * 256
    backward = [0] * 256
    edc = [0] * 256
    for index in range(256):
        doubled = (index << 1) ^ (0x11D if index & 0x80 else 0)
        forward[index] = doubled & 0xFF
        backward[(index ^ doubled) & 0xFF] = index
        value = index
        for _ in range(8):
            value = (value >> 1) ^ (0xD8018001 if value & 1 else 0)
        edc[index] = value & 0xFFFFFFFF
    return forward, backward, edc


ECC_FORWARD, ECC_BACKWARD, EDC_TABLE = _tables()


def _edc(data: bytes) -> bytes:
    value = 0
    for byte in data:
        value = (value >> 8) ^ EDC_TABLE[(value ^ byte) & 0xFF]
    return value.to_bytes(4, "little")


def _ecc(
    source: bytes,
    major_count: int,
    minor_count: int,
    major_multiplier: int,
    minor_increment: int,
) -> bytes:
    size = major_count * minor_count
    result = bytearray(major_count * 2)
    for major in range(major_count):
        source_index = (major >> 1) * major_multiplier + (major & 1)
        value_a = 0
        value_b = 0
        for _ in range(minor_count):
            value = source[source_index]
            source_index += minor_increment
            if source_index >= size:
                source_index -= size
            value_a ^= value
            value_b ^= value
            value_a = ECC_FORWARD[value_a]
        value_a = ECC_BACKWARD[ECC_FORWARD[value_a] ^ value_b]
        result[major] = value_a
        result[major + major_count] = value_a ^ value_b
    return bytes(result)


def regenerate_mode2_form1(raw_sector: bytes) -> bytes:
    if len(raw_sector) != RAW_SECTOR_SIZE:
        raise Mode2PatchError(
            f"Raw sector is {len(raw_sector)} bytes, expected {RAW_SECTOR_SIZE}"
        )
    if raw_sector[:12] != b"\x00" + b"\xFF" * 10 + b"\x00":
        raise Mode2PatchError("Sector sync pattern does not match a raw CD-ROM sector")
    if (
        raw_sector[15] != 2
        or raw_sector[16:20] != raw_sector[20:24]
        or raw_sector[18] & 0x20
    ):
        raise Mode2PatchError("Target sector is not MODE2/Form1")

    result = bytearray(raw_sector)
    result[0x818:0x81C] = _edc(result[0x10:0x818])
    address = bytes(result[12:16])
    result[12:16] = b"\x00" * 4
    result[0x81C:0x8C8] = _ecc(result[0x0C:0x81C], 86, 24, 2, 86)
    result[0x8C8:0x930] = _ecc(result[0x0C:0x8C8], 52, 43, 86, 88)
    result[12:16] = address
    return bytes(result)


def patch_standalone_boot(image_path: Path | str) -> BootPatchResult:
    image = Path(image_path).resolve()
    if not image.is_file():
        raise Mode2PatchError(f"Output image does not exist: {image}")
    minimum_size = (SLUS_TARGET_LBA + 1) * RAW_SECTOR_SIZE
    if image.stat().st_size < minimum_size:
        raise Mode2PatchError(f"Output image is too small for LBA {SLUS_TARGET_LBA}")

    header_offset = SLUS_HEADER_LBA * RAW_SECTOR_SIZE
    target_offset = SLUS_TARGET_LBA * RAW_SECTOR_SIZE
    with image.open("rb") as handle:
        handle.seek(header_offset)
        header_sector = handle.read(RAW_SECTOR_SIZE)
        handle.seek(target_offset)
        target_sector = handle.read(RAW_SECTOR_SIZE)

    header = header_sector[USER_DATA_OFFSET : USER_DATA_OFFSET + 2048]
    if header[:8] != b"PS-X EXE":
        raise Mode2PatchError("Audited SLUS header LBA does not contain PS-X EXE")
    text_size = int.from_bytes(header[0x1C:0x20], "little")
    if text_size != SLUS_TEXT_SIZE:
        raise Mode2PatchError(
            f"SLUS text size is 0x{text_size:X}, expected 0x{SLUS_TEXT_SIZE:X}"
        )
    if regenerate_mode2_form1(target_sector) != target_sector:
        raise Mode2PatchError("Target SLUS sector has invalid retail EDC/ECC")

    before_hash = _sha256(target_sector)
    context_start = USER_DATA_OFFSET + PATCH_CONTEXT_OFFSET
    context = target_sector[context_start : context_start + len(PATCH_CONTEXT_BEFORE)]
    if context == PATCH_CONTEXT_AFTER and before_hash == PATCHED_TARGET_SECTOR_SHA256:
        return BootPatchResult(
            image, SLUS_TARGET_LBA, before_hash, before_hash, True
        )
    if before_hash != RETAIL_TARGET_SECTOR_SHA256:
        raise Mode2PatchError(
            f"Target SLUS sector hash mismatch: {before_hash}"
        )
    if context != PATCH_CONTEXT_BEFORE:
        raise Mode2PatchError(
            f"SLUS boot context mismatch: {context.hex(' ')}"
        )

    patched = bytearray(target_sector)
    patched[context_start : context_start + len(context)] = PATCH_CONTEXT_AFTER
    repaired = regenerate_mode2_form1(bytes(patched))
    after_hash = _sha256(repaired)
    if after_hash != PATCHED_TARGET_SECTOR_SHA256:
        raise Mode2PatchError(
            f"Regenerated standalone boot sector hash mismatch: {after_hash}"
        )

    with image.open("r+b") as handle:
        handle.seek(target_offset)
        handle.write(repaired)
        handle.flush()
        handle.seek(target_offset)
        verified = handle.read(RAW_SECTOR_SIZE)
    if verified != repaired:
        raise Mode2PatchError("Standalone boot sector did not verify after writing")
    return BootPatchResult(
        image, SLUS_TARGET_LBA, before_hash, after_hash, False
    )


def verify_retail_title_boot(
    image_path: Path | str,
) -> BootVerificationResult:
    """Verify, without writing, that the native publisher/title boot is intact."""

    image = Path(image_path).resolve()
    if not image.is_file():
        raise Mode2PatchError(f"Output image does not exist: {image}")
    minimum_size = (SLUS_TARGET_LBA + 1) * RAW_SECTOR_SIZE
    if image.stat().st_size < minimum_size:
        raise Mode2PatchError(f"Output image is too small for LBA {SLUS_TARGET_LBA}")

    header_offset = SLUS_HEADER_LBA * RAW_SECTOR_SIZE
    target_offset = SLUS_TARGET_LBA * RAW_SECTOR_SIZE
    with image.open("rb") as handle:
        handle.seek(header_offset)
        header_sector = handle.read(RAW_SECTOR_SIZE)
        handle.seek(target_offset)
        target_sector = handle.read(RAW_SECTOR_SIZE)

    header = header_sector[USER_DATA_OFFSET : USER_DATA_OFFSET + 2048]
    if header[:8] != b"PS-X EXE":
        raise Mode2PatchError("Audited SLUS header LBA does not contain PS-X EXE")
    text_size = int.from_bytes(header[0x1C:0x20], "little")
    if text_size != SLUS_TEXT_SIZE:
        raise Mode2PatchError(
            f"SLUS text size is 0x{text_size:X}, expected 0x{SLUS_TEXT_SIZE:X}"
        )
    if regenerate_mode2_form1(target_sector) != target_sector:
        raise Mode2PatchError("Target SLUS sector has invalid retail EDC/ECC")

    sector_hash = _sha256(target_sector)
    if sector_hash != RETAIL_TARGET_SECTOR_SHA256:
        raise Mode2PatchError(
            "Native publisher/title boot sector hash mismatch: "
            f"{sector_hash}"
        )
    context_start = USER_DATA_OFFSET + PATCH_CONTEXT_OFFSET
    context = target_sector[
        context_start : context_start + len(PATCH_CONTEXT_BEFORE)
    ]
    if context != PATCH_CONTEXT_BEFORE:
        raise Mode2PatchError(
            f"Native publisher/title boot context mismatch: {context.hex(' ')}"
        )
    return BootVerificationResult(image, SLUS_TARGET_LBA, sector_hash)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="required acknowledgement that the checked output image is modified",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.in_place:
        parser.error("pass --in-place to patch the checked output image")
    try:
        result = patch_standalone_boot(args.image)
        action = "Already patched" if result.already_patched else "Patched"
        print(
            f"{action} {result.image} LBA {result.lba}: "
            f"{result.before_sha256} -> {result.after_sha256}"
        )
        return 0
    except (Mode2PatchError, OSError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
