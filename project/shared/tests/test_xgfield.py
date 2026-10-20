from __future__ import annotations

import struct
import unittest

from tools.xgfield import (
    FIELD_HEADER_MINIMUM,
    FieldFormatError,
    STREAM_COUNT,
    STREAM_TABLE_OFFSET,
    build_field,
    build_field_preserving,
    compress_lzss,
    compress_lzss_literals,
    compress_lzss_retail,
    decompress_lzss,
    parse_field,
)


class LzssTests(unittest.TestCase):
    def test_literal_codec_roundtrips_varied_lengths(self) -> None:
        for size in (0, 1, 7, 8, 9, 25, 528):
            with self.subTest(size=size):
                source = bytes((index * 29 + 7) & 0xFF for index in range(size))
                compressed = compress_lzss_literals(source)
                decoded = decompress_lzss(compressed, size)
                self.assertEqual(decoded.data, source)

    def test_compact_codec_roundtrips_and_uses_backreferences(self) -> None:
        source = (b"Zeboim mass-driver rail 0320\x00" * 300) + bytes(range(256))
        compressed = compress_lzss(source)
        decoded = decompress_lzss(compressed, len(source))
        self.assertEqual(decoded.data, source)
        self.assertLess(len(compressed), len(compress_lzss_literals(source)) // 4)
        self.assertEqual(compress_lzss(source), compressed)

    def test_retail_compact_codec_completes_the_final_command_group(self) -> None:
        source = bytes(range(99))
        compressed = compress_lzss_retail(source)
        declared_size = struct.unpack_from("<I", compressed)[0]

        self.assertEqual(declared_size, 104)
        self.assertEqual(
            decompress_lzss(compressed, declared_size).data,
            source + bytes(5),
        )
        self.assertEqual(len(compressed) % 4, 0)


class FieldBundleTests(unittest.TestCase):
    def test_build_and_parse_preserves_header_and_components(self) -> None:
        header = bytearray(0x180)
        header[0x20:0x28] = b"HEADER!!"
        components = [
            bytes((byte + index) & 0xFF for byte in range(index * 5))
            for index in range(STREAM_COUNT)
        ]

        rebuilt = build_field(header, components)
        parsed = parse_field(rebuilt)

        self.assertEqual(parsed.header[0x20:0x28], b"HEADER!!")
        self.assertEqual([part.data for part in parsed.parts], components)
        self.assertGreaterEqual(
            struct.unpack_from("<I", rebuilt, STREAM_TABLE_OFFSET)[0],
            FIELD_HEADER_MINIMUM,
        )

    def test_compact_field_build_preserves_components_and_reduces_size(self) -> None:
        header = bytearray(0x180)
        components = [
            (f"field-stream-{index}:".encode("ascii") * 300)
            for index in range(STREAM_COUNT)
        ]

        literal = build_field(header, components)
        compact = build_field(header, components, compact=True)

        self.assertEqual(
            [part.data for part in parse_field(compact).parts],
            components,
        )
        self.assertLess(len(compact), len(literal) // 4)

    def test_preserving_build_reuses_unchanged_packed_streams(self) -> None:
        header = bytearray(0x180)
        original = [
            (f"retail-stream-{index}:".encode("ascii") * (index + 8))
            for index in range(STREAM_COUNT)
        ]
        template = build_field(header, original, compact=True)
        changed = list(original)
        changed[2] = b"replacement-model-data" * 40
        replacement_header = bytearray(parse_field(template).header)
        replacement_header[0x20:0x28] = b"PATCHED!"

        rebuilt = build_field_preserving(
            template,
            changed,
            (2,),
            compact_changed=True,
            replacement_header=replacement_header,
        )
        before = parse_field(template)
        after = parse_field(rebuilt)

        self.assertEqual([part.data for part in after.parts], changed)
        self.assertEqual(after.header[0x20:0x28], b"PATCHED!")
        for index in set(range(STREAM_COUNT)) - {2}:
            old_part = before.parts[index]
            new_part = after.parts[index]
            self.assertEqual(
                template[
                    old_part.offset : old_part.offset + old_part.compressed_size
                ],
                rebuilt[
                    new_part.offset : new_part.offset + new_part.compressed_size
                ],
            )

        with self.assertRaisesRegex(FieldFormatError, "differs from its template"):
            build_field_preserving(template, changed, ())

    def test_preserving_build_accepts_an_audited_grown_header(self) -> None:
        header = bytearray(0x180)
        original = [
            (f"header-growth-stream-{index}:".encode("ascii") * (index + 4))
            for index in range(STREAM_COUNT)
        ]
        template = build_field(header, original, compact=True)
        before = parse_field(template)
        replacement_header = before.header + bytes.fromhex(
            "E0 01 00 00 00 00 00 00 20 00 00 00 9C FF 00 00"
        )

        rebuilt = build_field_preserving(
            template,
            original,
            (),
            replacement_header=replacement_header,
        )
        after = parse_field(rebuilt)
        self.assertEqual(len(after.header), len(before.header) + 16)
        self.assertEqual(after.header[-16:], replacement_header[-16:])
        self.assertEqual([part.data for part in after.parts], original)
        for old_part, new_part in zip(before.parts, after.parts, strict=True):
            self.assertEqual(
                template[
                    old_part.offset : old_part.offset + old_part.compressed_size
                ],
                rebuilt[
                    new_part.offset : new_part.offset + new_part.compressed_size
                ],
            )


if __name__ == "__main__":
    unittest.main()
