from __future__ import annotations

import struct
import unittest

from tools.xgscript import AtelScript, ScriptFormatError


def _script(bytecode: bytes = b"\x00", entity_count: int = 1) -> bytes:
    data = bytearray(0x84 + entity_count * 0x40)
    struct.pack_into("<I", data, 0x80, entity_count)
    data.extend(bytecode)
    return bytes(data)


class ScriptEditorTests(unittest.TestCase):
    def test_parses_and_gets_all_entity_script_pointers(self) -> None:
        data = bytearray(_script(b"\x00\x11\x22", entity_count=2))
        struct.pack_into("<H", data, 0x84 + 0x40 + 31 * 2, 2)

        script = AtelScript(data)

        self.assertEqual(script.entity_count, 2)
        self.assertEqual(script.bytecode_offset, 0x104)
        self.assertEqual(script.bytecode, b"\x00\x11\x22")
        self.assertEqual(script.get_script_pointer(1, 31), 2)

    def test_sets_pointer_without_changing_other_data(self) -> None:
        source = _script(b"\x00\x11\x22")
        script = AtelScript(source)

        script.set_script_pointer(0, 7, 2)
        result = script.to_bytes()

        self.assertEqual(script.get_script_pointer(0, 7), 2)
        self.assertEqual(result[0x84 + 7 * 2 : 0x84 + 7 * 2 + 2], b"\x02\x00")
        self.assertEqual(result[: 0x84 + 7 * 2], source[: 0x84 + 7 * 2])
        self.assertEqual(result[script.bytecode_offset :], b"\x00\x11\x22")

    def test_appends_raw_routine_and_repoints_slot(self) -> None:
        script = AtelScript(_script(b"\x00\xAA"))

        offset = script.append_and_repoint(0, 5, b"\x98\xD1\x82\x00\x80\x00")

        self.assertEqual(offset, 2)
        self.assertEqual(script.get_script_pointer(0, 5), 2)
        self.assertEqual(script.bytecode, b"\x00\xAA\x98\xD1\x82\x00\x80\x00")
        self.assertEqual(bytes(script), script.to_bytes())

    def test_rejects_malformed_header_table_and_pointer(self) -> None:
        with self.assertRaisesRegex(ScriptFormatError, "fixed header"):
            AtelScript(bytes(0x83))

        truncated_table = bytearray(0x84)
        struct.pack_into("<I", truncated_table, 0x80, 1)
        with self.assertRaisesRegex(ScriptFormatError, "Entity table ends"):
            AtelScript(truncated_table)

        past_end = bytearray(_script(b"\x00"))
        struct.pack_into("<H", past_end, 0x84 + 2, 1)
        with self.assertRaisesRegex(ScriptFormatError, "outside 1-byte bytecode"):
            AtelScript(past_end)

    def test_rejects_invalid_indices_offsets_and_empty_routine(self) -> None:
        script = AtelScript(_script(b"\x00\x11"))

        with self.assertRaisesRegex(ScriptFormatError, "Entity index"):
            script.get_script_pointer(1, 0)
        with self.assertRaisesRegex(ScriptFormatError, "Script index"):
            script.set_script_pointer(0, 32, 0)
        with self.assertRaisesRegex(ScriptFormatError, "16-bit offset"):
            script.set_script_pointer(0, 1, 0x10000)
        with self.assertRaisesRegex(ScriptFormatError, "outside 2-byte"):
            script.set_script_pointer(0, 1, 2)
        with self.assertRaisesRegex(ScriptFormatError, "at least one byte"):
            script.append_raw_routine(b"")

    def test_allows_last_u16_offset_but_rejects_overflow(self) -> None:
        script = AtelScript(_script(bytes(0xFFFF)))

        self.assertEqual(script.append_raw_routine(b"\x00"), 0xFFFF)
        self.assertEqual(script.bytecode_size, 0x10000)
        with self.assertRaisesRegex(ScriptFormatError, "16-bit offset limit"):
            script.append_raw_routine(b"\x00")


if __name__ == "__main__":
    unittest.main()
