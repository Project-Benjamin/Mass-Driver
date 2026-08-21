#!/usr/bin/env python3
"""Inspect, unpack, and rebuild Xenogears field bundles.

The nine compressed streams use the game's LZSS codec.  The module provides
both a conservative literal-only encoder and a compact greedy/lazy encoder.
"""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct
import sys
from typing import Iterable, Sequence


SIZE_TABLE_OFFSET = 0x10C
STREAM_TABLE_OFFSET = 0x130
FIELD_HEADER_MINIMUM = 0x154
STREAM_COUNT = 9
RING_SIZE = 4096
MAX_MATCH_LENGTH = 18

STREAM_NAMES = (
    "images",
    "walkmesh",
    "models",
    "actors",
    "sprites",
    "scripts",
    "encounters",
    "dialogue",
    "triggers",
)


class FieldFormatError(RuntimeError):
    """Raised when a field bundle or compressed stream is malformed."""


@dataclass(frozen=True)
class DecodedStream:
    data: bytes
    stream_declared_size: int
    decoded_size: int
    consumed_size: int


@dataclass(frozen=True)
class FieldPart:
    index: int
    name: str
    declared_size: int
    offset: int
    compressed_size: int
    stream_declared_size: int
    decoded_size: int
    consumed_size: int
    data: bytes


@dataclass(frozen=True)
class ParsedField:
    source: bytes
    header: bytes
    parts: tuple[FieldPart, ...]


def _u32(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise FieldFormatError(f"u32 read outside buffer at 0x{offset:X}")
    return struct.unpack_from("<I", data, offset)[0]


def _align(value: int, alignment: int = 4) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decompress_lzss(stream: bytes, required_size: int) -> DecodedStream:
    """Decode one field stream using the original 4 KiB ring-buffer rules."""

    if len(stream) < 4:
        raise FieldFormatError("Compressed stream is shorter than its size header")
    stream_size = _u32(stream, 0)
    if stream_size == 0:
        if required_size != 0:
            raise FieldFormatError(
                f"Empty compressed stream cannot supply {required_size} bytes"
            )
        return DecodedStream(b"", 0, 0, 4)
    if stream_size < required_size:
        raise FieldFormatError(
            f"Compressed stream declares {stream_size} decoded bytes, "
            f"but field header requires {required_size}"
        )
    if stream_size > required_size + 16:
        raise FieldFormatError(
            f"Compressed stream padding is unexpectedly large: "
            f"{stream_size} versus required {required_size}"
        )

    ring = bytearray(RING_SIZE)
    ring_position = RING_SIZE - MAX_MATCH_LENGTH
    output = bytearray()
    position = 4

    # The retail encoder can leave a partially populated final control group.
    # The PS1 decoder has a 16-byte allocation cushion and may read into the
    # following stream while producing irrelevant padding.  The outer field
    # header is the authoritative component size, so stop once it is satisfied.
    while len(output) < required_size:
        if position >= len(stream):
            raise FieldFormatError("Compressed stream ends before a control byte")
        control = stream[position]
        position += 1

        for bit in range(8):
            if control & (1 << bit):
                if position + 2 > len(stream):
                    raise FieldFormatError("Compressed stream ends inside a backreference")
                low = stream[position]
                high = stream[position + 1]
                position += 2
                distance = low | ((high & 0x0F) << 8)
                length = (high >> 4) + 3
                for _ in range(length):
                    value = ring[(ring_position - distance) & (RING_SIZE - 1)]
                    output.append(value)
                    ring[ring_position] = value
                    ring_position = (ring_position + 1) & (RING_SIZE - 1)
            else:
                if position >= len(stream):
                    raise FieldFormatError("Compressed stream ends before a literal")
                value = stream[position]
                position += 1
                output.append(value)
                ring[ring_position] = value
                ring_position = (ring_position + 1) & (RING_SIZE - 1)

            if len(output) >= required_size:
                break

        if len(output) > required_size + 32:
            raise FieldFormatError("Compressed command group overruns the field buffer")

    if len(output) < required_size:
        raise FieldFormatError(
            f"Decoded only {len(output)} of {required_size} required bytes"
        )
    return DecodedStream(
        data=bytes(output[:required_size]),
        stream_declared_size=stream_size,
        decoded_size=len(output),
        consumed_size=position,
    )


def compress_lzss_literals(data: bytes) -> bytes:
    """Encode a stream with literal commands only, padded to a full command group."""

    if not data:
        return b"\x00\x00\x00\x00"
    padded_size = _align(len(data), 8)
    padded = data + bytes(padded_size - len(data))
    output = bytearray(struct.pack("<I", padded_size))
    for offset in range(0, len(padded), 8):
        output.append(0)
        output.extend(padded[offset : offset + 8])
    output.extend(bytes(_align(len(output)) - len(output)))
    return bytes(output)


def compress_lzss(data: bytes) -> bytes:
    """Encode a compact Xenogears LZSS stream with a 4 KiB history window.

    The format stores eight commands behind each control byte.  Set bits are
    12-bit-distance, 4-bit-length backreferences; clear bits are literals.
    A one-command lazy look-ahead avoids the common greedy case where a short
    match hides a substantially longer match at the next byte.
    """

    if not data:
        return b"\x00\x00\x00\x00"

    positions: dict[bytes, deque[int]] = defaultdict(deque)
    output = bytearray(struct.pack("<I", len(data)))
    position = 0

    def add_positions(start: int, end: int) -> None:
        for candidate in range(start, end):
            if candidate + 3 <= len(data):
                positions[data[candidate : candidate + 3]].append(candidate)

    def find_match(at: int) -> tuple[int, int]:
        if at + 3 > len(data):
            return 0, 0
        candidates = positions.get(data[at : at + 3])
        if not candidates:
            return 0, 0
        # The packed value zero is decoder-dependent (some implementations
        # treat it as 4096 bytes back, others as an invalid/self reference),
        # so emit only the unambiguous 1..4095 distance range used by retail.
        cutoff = at - (RING_SIZE - 1)
        while candidates and candidates[0] < cutoff:
            candidates.popleft()

        best_length = 0
        best_distance = 0
        maximum = min(MAX_MATCH_LENGTH, len(data) - at)
        for candidate in reversed(candidates):
            distance = at - candidate
            if not 1 <= distance < RING_SIZE:
                continue
            length = 3
            # Reading through the input beyond ``at`` models the decoder's
            # legal overlapping-copy behavior.  Equality here enforces the
            # same periodic bytes that the ring buffer will produce.
            while length < maximum and data[at + length] == data[candidate + length]:
                length += 1
            if length > best_length:
                best_length = length
                best_distance = distance
                if length == MAX_MATCH_LENGTH:
                    break
        return best_length, best_distance

    while position < len(data):
        control_offset = len(output)
        output.append(0)
        control = 0

        for bit in range(8):
            if position >= len(data):
                break
            match_length, match_distance = find_match(position)

            # Temporarily expose the current byte as history to evaluate a
            # literal followed by the next position's match.
            if match_length >= 3 and position + 1 < len(data):
                add_positions(position, position + 1)
                next_length, _ = find_match(position + 1)
                key = data[position : position + 3]
                temporary = positions[key]
                if not temporary or temporary[-1] != position:
                    raise FieldFormatError("LZSS match dictionary lost its temporary entry")
                temporary.pop()
                if not temporary:
                    del positions[key]
                if next_length > match_length + 1:
                    match_length = 0

            start = position
            if match_length >= 3:
                control |= 1 << bit
                encoded_distance = match_distance & (RING_SIZE - 1)
                output.extend(
                    (
                        encoded_distance & 0xFF,
                        ((encoded_distance >> 8) & 0x0F)
                        | ((match_length - 3) << 4),
                    )
                )
                position += match_length
            else:
                output.append(data[position])
                position += 1
            add_positions(start, position)

        output[control_offset] = control

    output.extend(bytes(_align(len(output)) - len(output)))
    return bytes(output)


def compress_lzss_retail(data: bytes) -> bytes:
    """Encode compact data in complete eight-command retail decoder groups.

    ``compress_lzss`` is useful as a canonical stream encoder, but its final
    control group may contain fewer than eight commands.  Xenogears' PS1 heap
    decoder always executes the complete group before checking the declared
    output size.  Complete the final group with zero literals and include
    those harmless bytes in the stream's allocation size so a field load
    cannot overrun its destination buffer.
    """

    if not data:
        return b"\x00\x00\x00\x00"

    packed = compress_lzss(data)
    position = 4
    output_size = 0
    final_command_count = 0
    final_control = 0
    while output_size < len(data):
        if position >= len(packed):
            raise FieldFormatError("Compact LZSS stream lost its final group")
        final_control = packed[position]
        position += 1
        final_command_count = 0
        for bit in range(8):
            if output_size >= len(data):
                break
            if final_control & (1 << bit):
                if position + 2 > len(packed):
                    raise FieldFormatError(
                        "Compact LZSS stream ends inside a backreference"
                    )
                high = packed[position + 1]
                position += 2
                output_size += (high >> 4) + 3
            else:
                if position >= len(packed):
                    raise FieldFormatError(
                        "Compact LZSS stream ends inside a literal"
                    )
                position += 1
                output_size += 1
            final_command_count += 1
            if output_size > len(data):
                raise FieldFormatError(
                    "Compact LZSS command exceeds its source data"
                )

    missing_commands = 8 - final_command_count
    used_control_mask = (1 << final_command_count) - 1
    if final_control & ~used_control_mask:
        raise FieldFormatError(
            "Compact LZSS final group has commands beyond its declared output"
        )

    completed = bytearray(packed[:position])
    completed.extend(bytes(missing_commands))
    struct.pack_into("<I", completed, 0, len(data) + missing_commands)
    completed.extend(bytes(_align(len(completed)) - len(completed)))

    # The ordinary decoder stops at the field header's authoritative component
    # size.  Decode the declared padding as well to prove that the PS1's
    # complete-group behavior sees only the intended zero suffix.
    expected = data + bytes(missing_commands)
    decoded = decompress_lzss(bytes(completed), len(expected))
    if decoded.data != expected:
        raise FieldFormatError(
            "Retail-safe compact LZSS stream failed its complete-group round trip"
        )
    return bytes(completed)


def parse_field(data: bytes) -> ParsedField:
    if len(data) < FIELD_HEADER_MINIMUM:
        raise FieldFormatError(
            f"Field is only {len(data)} bytes; expected at least 0x{FIELD_HEADER_MINIMUM:X}"
        )

    sizes = [_u32(data, SIZE_TABLE_OFFSET + 4 * index) for index in range(9)]
    offsets = [_u32(data, STREAM_TABLE_OFFSET + 4 * index) for index in range(9)]
    if offsets[0] < FIELD_HEADER_MINIMUM:
        raise FieldFormatError(
            f"First stream begins inside the fixed header: 0x{offsets[0]:X}"
        )
    if any(offset % 4 for offset in offsets):
        raise FieldFormatError("A field stream offset is not four-byte aligned")
    if offsets != sorted(offsets):
        raise FieldFormatError("Field stream offsets are not monotonic")
    if offsets[-1] > len(data):
        raise FieldFormatError("Last field stream begins beyond end of file")

    parts: list[FieldPart] = []
    for index, (name, declared_size, offset) in enumerate(
        zip(STREAM_NAMES, sizes, offsets, strict=True)
    ):
        end = offsets[index + 1] if index + 1 < STREAM_COUNT else len(data)
        if end < offset:
            raise FieldFormatError(f"Negative compressed span for stream {index}")
        compressed = data[offset:end]
        try:
            decoded = decompress_lzss(compressed, declared_size)
        except FieldFormatError as exc:
            raise FieldFormatError(f"Stream {index} ({name}): {exc}") from exc
        parts.append(
            FieldPart(
                index=index,
                name=name,
                declared_size=declared_size,
                offset=offset,
                compressed_size=len(compressed),
                stream_declared_size=decoded.stream_declared_size,
                decoded_size=decoded.decoded_size,
                consumed_size=decoded.consumed_size,
                data=decoded.data,
            )
        )

    return ParsedField(
        source=data,
        header=data[: offsets[0]],
        parts=tuple(parts),
    )


def build_field(
    header: bytes,
    components: Sequence[bytes],
    *,
    compact: bool = False,
) -> bytes:
    """Build a field bundle from its decoded component streams.

    Literal-only packing remains the default for callers that need the most
    conservative byte stream.  Large replacement fields can opt into the
    retail-compatible compact encoder so the packed bundle stays within the
    field loader's practical CD/read-buffer budget.
    """
    if len(components) != STREAM_COUNT:
        raise FieldFormatError(
            f"Expected {STREAM_COUNT} components, got {len(components)}"
        )
    if len(header) < FIELD_HEADER_MINIMUM:
        raise FieldFormatError("Preserved field header is too short")

    mutable_header = bytearray(header)
    encoder = compress_lzss_retail if compact else compress_lzss_literals
    streams = [encoder(component) for component in components]
    cursor = _align(len(mutable_header))
    offsets = []
    for stream in streams:
        offsets.append(cursor)
        cursor += len(stream)

    for index, component in enumerate(components):
        struct.pack_into("<I", mutable_header, SIZE_TABLE_OFFSET + 4 * index, len(component))
        struct.pack_into("<I", mutable_header, STREAM_TABLE_OFFSET + 4 * index, offsets[index])

    output = bytearray(mutable_header)
    output.extend(bytes(_align(len(output)) - len(output)))
    for stream in streams:
        output.extend(stream)
    return bytes(output)


def build_field_preserving(
    template: bytes,
    components: Sequence[bytes],
    changed_indices: Iterable[int],
    *,
    compact_changed: bool = False,
    replacement_header: bytes | None = None,
) -> bytes:
    """Rebuild a field while retaining untouched retail compressed streams.

    This is useful when only a few components change in a large field.  Every
    undeclared component must still decode byte-for-byte to the supplied data;
    its complete packed span is then copied from ``template``.  Changed
    components are encoded independently and all header offsets are rebuilt.
    """

    if len(components) != STREAM_COUNT:
        raise FieldFormatError(
            f"Expected {STREAM_COUNT} components, got {len(components)}"
        )
    changed = set(changed_indices)
    if any(not isinstance(index, int) or not 0 <= index < STREAM_COUNT for index in changed):
        raise FieldFormatError("Changed field-stream index is outside 0..8")

    parsed = parse_field(template)
    encoder = (
        compress_lzss_retail if compact_changed else compress_lzss_literals
    )
    streams: list[bytes] = []
    for index, (component, part) in enumerate(
        zip(components, parsed.parts, strict=True)
    ):
        if index in changed:
            streams.append(encoder(component))
            continue
        if component != part.data:
            raise FieldFormatError(
                f"Unchanged stream {index} ({part.name}) differs from its template"
            )
        streams.append(template[part.offset : part.offset + part.compressed_size])

    if replacement_header is not None and len(replacement_header) != len(
        parsed.header
    ):
        raise FieldFormatError(
            "Replacement field header size differs from its packed template"
        )
    mutable_header = bytearray(
        parsed.header if replacement_header is None else replacement_header
    )
    cursor = _align(len(mutable_header))
    offsets: list[int] = []
    for stream in streams:
        offsets.append(cursor)
        cursor += len(stream)
    for index, component in enumerate(components):
        struct.pack_into(
            "<I", mutable_header, SIZE_TABLE_OFFSET + 4 * index, len(component)
        )
        struct.pack_into(
            "<I", mutable_header, STREAM_TABLE_OFFSET + 4 * index, offsets[index]
        )

    output = bytearray(mutable_header)
    output.extend(bytes(_align(len(output)) - len(output)))
    for stream in streams:
        output.extend(stream)

    reparsed = parse_field(bytes(output))
    if [part.data for part in reparsed.parts] != list(components):
        raise FieldFormatError("Preserving field rebuild changed decoded component data")
    return bytes(output)


def _component_filename(index: int, name: str) -> str:
    return f"{index:02d}_{name}.bin"


def _manifest(parsed: ParsedField, source_path: Path) -> dict[str, object]:
    return {
        "format": "xenogears-field-bundle-v1",
        "source": str(source_path.resolve()),
        "source_size": len(parsed.source),
        "source_sha256": _sha256(parsed.source),
        "header_file": "header.bin",
        "header_size": len(parsed.header),
        "header_sha256": _sha256(parsed.header),
        "components": [
            {
                "index": part.index,
                "name": part.name,
                "file": _component_filename(part.index, part.name),
                "size": len(part.data),
                "sha256": _sha256(part.data),
                "source_offset": part.offset,
                "source_compressed_span": part.compressed_size,
                "source_stream_declared_size": part.stream_declared_size,
                "source_decoded_size": part.decoded_size,
                "source_consumed_size": part.consumed_size,
            }
            for part in parsed.parts
        ],
    }


def command_inspect(args: argparse.Namespace) -> int:
    source_path = Path(args.field)
    parsed = parse_field(source_path.read_bytes())
    manifest = _manifest(parsed, source_path)
    if args.json:
        print(json.dumps(manifest, indent=2))
        return 0

    print(f"Field: {source_path.resolve()}")
    print(f"Size: {len(parsed.source)} bytes; header: {len(parsed.header)} bytes")
    print(" part  name          data size     offset   packed  stream size  decoded")
    for part in parsed.parts:
        print(
            f"{part.index:5d}  {part.name:12s}  {part.declared_size:9d}  "
            f"0x{part.offset:07X}  {part.compressed_size:7d}  "
            f"{part.stream_declared_size:11d}  {part.decoded_size:7d}"
        )
    return 0


def _write_checked(path: Path, data: bytes, force: bool) -> None:
    if path.exists() and not force:
        raise FieldFormatError(f"Refusing to overwrite {path}; pass --force")
    path.write_bytes(data)


def command_unpack(args: argparse.Namespace) -> int:
    source_path = Path(args.field)
    parsed = parse_field(source_path.read_bytes())
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)

    _write_checked(output / "header.bin", parsed.header, args.force)
    for part in parsed.parts:
        _write_checked(
            output / _component_filename(part.index, part.name),
            part.data,
            args.force,
        )
    manifest = json.dumps(_manifest(parsed, source_path), indent=2).encode("utf-8") + b"\n"
    _write_checked(output / "manifest.json", manifest, args.force)
    print(f"Unpacked {source_path.resolve()} -> {output}")
    return 0


def command_pack(args: argparse.Namespace) -> int:
    source = Path(args.directory).resolve()
    header = (source / "header.bin").read_bytes()
    components = [
        (source / _component_filename(index, name)).read_bytes()
        for index, name in enumerate(STREAM_NAMES)
    ]
    rebuilt = build_field(header, components)
    # Parse immediately so no malformed bundle can be emitted silently.
    reparsed = parse_field(rebuilt)
    for expected, actual in zip(components, reparsed.parts, strict=True):
        if expected != actual.data:
            raise FieldFormatError(f"Internal rebuild mismatch in {actual.name}")

    destination = Path(args.output).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    _write_checked(destination, rebuilt, args.force)
    print(
        f"Packed {source} -> {destination} ({len(rebuilt)} bytes, "
        "literal-only LZSS)"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="show field stream metadata")
    inspect_parser.add_argument("field", type=Path)
    inspect_parser.add_argument("--json", action="store_true")
    inspect_parser.set_defaults(handler=command_inspect)

    unpack_parser = subparsers.add_parser("unpack", help="decompress all nine streams")
    unpack_parser.add_argument("field", type=Path)
    unpack_parser.add_argument("output", type=Path)
    unpack_parser.add_argument("--force", action="store_true")
    unpack_parser.set_defaults(handler=command_unpack)

    pack_parser = subparsers.add_parser("pack", help="rebuild from an unpacked directory")
    pack_parser.add_argument("directory", type=Path)
    pack_parser.add_argument("output", type=Path)
    pack_parser.add_argument("--force", action="store_true")
    pack_parser.set_defaults(handler=command_pack)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (FieldFormatError, OSError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
