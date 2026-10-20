"""Safety checks for whole-disc dialogue inventory and opt-in name markers."""
from pathlib import Path
from types import SimpleNamespace
import struct
import unittest
from unittest.mock import patch

from modules.definitive import dialogue as d
from modules.rico import dialogue_name_color as legacy_color
from shared.tools import xgdialog_name_color as color
from shared.tools.xgdialog import (
    DialogueBlockSpec, DialogueFormatError, encode_dialogue, encode_text_unchecked,
)
from shared.tools.xgfield import build_field, parse_field


def component(*texts, width=58):
    """Construct retail bytes, including tails the authored codec rejects."""
    count = len(texts)
    result = bytearray(struct.pack("<I", count - 1) + bytes(count * 4))
    for index, text in enumerate(texts):
        struct.pack_into("<H", result, 4 + 2 * index, len(result))
        result[4 + count * 2 + index * 2:6 + count * 2 + index * 2] = bytes((width, 4))
        result.extend(encode_text_unchecked(text))
    return bytes(result)


def field(dialogue):
    parts = [b"unchanged" + bytes((index,)) for index in range(9)]
    parts[7] = dialogue
    return build_field(bytes(0x154), parts)


class DialogueTests(unittest.TestCase):
    def test_retail_tails_are_lossless_and_disabled_is_exact_identity(self):
        source = component("<Fei>\nHello.<Close><Delay:20><Close>", "World!<Close>")
        blocks = d.retail_blocks(source)
        self.assertTrue(blocks[0].text.endswith("<Close><Delay:20><Close>"))
        result, audit = d.mark_dialogue(source, enabled=False)
        self.assertEqual(result, source)
        self.assertEqual(audit["marked_block_ids"], [])

    def test_only_marker_and_offsets_change_and_repeat_is_idempotent(self):
        source = component("<Fei>\nHello.<Close><Delay:20><Close>", "World!<Close>",
                           "<Delay:5>  Miang\nYes.<Close>")
        result, audit = d.mark_dialogue(source)
        self.assertEqual(audit["marked_block_ids"], [0, 2])
        self.assertEqual(len(result), len(source) + 6)
        self.assertEqual(result[10:16], source[10:16], "Native width/height bytes changed")
        for index, (before, after) in enumerate(zip(d.retail_blocks(source), d.retail_blocks(result))):
            self.assertEqual(after.payload, (color.MARKER_BYTES if index in (0, 2) else b"") + before.payload)
        second, audit = d.mark_dialogue(result)
        self.assertEqual(second, result)
        self.assertEqual(audit["status_counts"]["already_marked"], 2)

    def test_ordinary_names_prose_choices_and_pages_are_never_colored(self):
        texts = (
            "<Fei> said hello.\nA fine day.<Close>",
            "UNKNOWN\nA voice.<Close>",
            "ARCHIVE RECORD\nText.<Close>",
            "<Fei>\n    <Opcode:01:FF>Yes\n    No<Close>",
            "<Fei>\nHello.<New>The next page.<Close>",
            "<Fei><Close>",
            "<Fei>\n<Opcode:0B:20>Hello.<Close>",
        )
        source = component(*texts)
        result, audit = d.mark_dialogue(source)
        self.assertEqual(result, source)
        self.assertEqual(audit["status_counts"], {"unidentified": 4, "choice": 1,
                         "multipage_review": 1, "existing_control_review": 1})

    def test_wrapped_label_is_reported_without_changing_dimensions(self):
        source = component("<Emeralda>\nHello.<Close>", width=8)
        result, audit = d.mark_dialogue(source)
        self.assertEqual(result, source)
        self.assertEqual(audit["status_counts"], {"name_width_review": 1})

    def test_unsupported_offset_control_and_missing_close_fail_closed(self):
        good = component("<Fei>\nHello.<Close>")
        bad_offset = bytearray(good)
        bad_offset[4] = 7
        for bad in (b"", bytes(bad_offset), good[:-1] + b"\x0f"):
            with self.subTest(bad=bad[:12]):
                with self.assertRaises(DialogueFormatError):
                    d.mark_dialogue(bad)
        result, audit = d.mark_dialogue(good[:-1])
        self.assertEqual(result, good[:-1])
        self.assertEqual(audit["status_counts"], {"terminal_control_review": 1})

    def test_duplicate_offsets_keep_shared_payload_and_grow_only_once(self):
        source = bytearray(component("Fei\nHello.<Close>", "Fei\nHello.<Close>"))
        first = struct.unpack_from("<H", source, 4)[0]
        second = struct.unpack_from("<H", source, 6)[0]
        del source[second:]
        struct.pack_into("<H", source, 6, first)
        result, audit = d.mark_dialogue(bytes(source))
        self.assertEqual(len(result), len(source) + 3)
        self.assertEqual(audit["marked_block_ids"], [0, 1])
        blocks = d.retail_blocks(result)
        self.assertEqual(blocks[0].offset, blocks[1].offset)
        self.assertEqual(d.mark_dialogue(result)[0], result)

    def test_alias_with_ineligible_dimensions_is_left_untouched(self):
        source = bytearray(component("Fei\nHello.<Close>", "Fei\nHello.<Close>"))
        first, second = struct.unpack_from("<HH", source, 4)
        del source[second:]
        struct.pack_into("<H", source, 6, first)
        source[10] = 2
        result, audit = d.mark_dialogue(bytes(source))
        self.assertEqual(result, source)
        self.assertEqual(audit["status_counts"], {"alias_review": 1, "name_width_review": 1})

    def test_u16_growth_limit_is_enforced(self):
        source = component("Fei\n" + "A" * 65522 + "<Close>")
        self.assertEqual(len(source), 65535)
        with self.assertRaisesRegex(DialogueFormatError, "u16"):
            d.mark_dialogue(source)

    def test_raw_reader_matches_shared_authored_reader_for_supported_text(self):
        texts = ["<Fei>\nHello.<Close>", "<Byte:90>Look.<Close>"]
        raw = component(*texts)
        canonical = encode_dialogue([DialogueBlockSpec(index, 58, 4, text)
                                     for index, text in enumerate(texts)])
        self.assertEqual(raw, canonical)

    def test_rico_compatibility_import_uses_exact_shared_functions_and_constants(self):
        for name in ("patch_executable", "verify_executable_image", "_row_color_helper",
                     "MARKER_BYTES", "INJECTED_DISPATCH"):
            self.assertIs(getattr(legacy_color, name), getattr(color, name))

    def test_disc_pass_composes_translation_and_preserves_other_streams(self):
        donor = field(component("Fei\nOriginal.<Close>"))
        translation = field(component("Fei\nTranslated.<Close>"))
        entry = SimpleNamespace(index=601, kind="file")
        image = SimpleNamespace(path=Path("retail.bin"), extract_entry=lambda ignored: donor)
        with patch.object(d, "Mode2Image", return_value=image), \
                patch.object(d, "field_entries", return_value=[(0, entry)]):
            replacements, audit = d.patch_disc_dialogue("retail.bin", 2,
                yellow_names=True, replacements={606: translation, 22: b"executable"}, include_text=True)
        self.assertEqual(replacements[22], b"executable")
        before = parse_field(translation)
        after = parse_field(replacements[606])
        for index in range(9):
            if index == 7:
                self.assertIn("Translated", d.retail_blocks(after.parts[7].data)[0].text)
                continue
            self.assertEqual(after.parts[index].data, before.parts[index].data)
            old, new = before.parts[index], after.parts[index]
            self.assertEqual(translation[old.offset:old.offset + old.compressed_size],
                             replacements[606][new.offset:new.offset + new.compressed_size])
        self.assertEqual(audit["field_status_counts"], {"changed": 1})
        self.assertEqual(audit["fields"][0]["physical_id"], 601)

    def test_disc_audit_reports_failed_fields_and_keeps_supplied_bytes(self):
        entry = SimpleNamespace(index=606, kind="file")
        image = SimpleNamespace(path=Path("retail.bin"), extract_entry=lambda ignored: b"bad")
        with patch.object(d, "Mode2Image", return_value=image), \
                patch.object(d, "field_entries", return_value=[(0, entry)]):
            replacements, audit = d.patch_disc_dialogue("retail.bin", 1, replacements={606: b"bad"})
        self.assertEqual(replacements, {606: b"bad"})
        self.assertEqual(audit["field_status_counts"], {"review_required": 1})

    def test_directory_boundary_does_not_scan_next_directory(self):
        entries = [SimpleNamespace(index=index, kind="empty") for index in range(2594)]
        directories = [SimpleNamespace(first_file=-1) for _ in range(17)]
        directories[4].first_file = 424
        directories[16].first_file = 2594
        image = SimpleNamespace(read_index=lambda: entries, read_directories=lambda: directories)
        found = d.field_entries(image)
        self.assertEqual(found[0][1].index, 606)
        self.assertEqual(found[-1][1].index, 2590)
        self.assertEqual(len(found), 993)
        entries[2142].kind = "metadata"
        self.assertEqual(len(d.field_entries(image)), 768)
        entries[2592].kind = "file"
        with self.assertRaisesRegex(DiscFormatError, "unpaired"):
            d.field_entries(image)


from shared.tools.xgdisc import DiscFormatError


if __name__ == "__main__":
    unittest.main()
