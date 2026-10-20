import copy
import json
from pathlib import Path
import tempfile
import unittest

from modules.definitive import translation as tr
from shared.tools import xgdialog, xgfield


def source():
    return {"storyId": "story01", "sha256": "a" * 64}


def fan():
    document = {"schemaVersion": 1, "storyId": "story01", "sourceSha256": "a" * 64,
        "translationMethod": tr.FAN_METHOD, "units": [{"id": "story01-b001-u001", "text": 'Fei\n“Welcome!”▽'}],
        "provenance": {"edition": "fan"}}
    document["provenance"]["unitsSha256"] = tr.sha256(tr._json_bytes(document["units"]))
    return document


def alignment():
    return {"schemaVersion": 1, "id": "01", "sources": {"japanese": [source()]},
        "units": {"japanese": [{"id": "story01-b001-u001", "text": "Japanese source"}],
                  "official": [{"id": "en-01-u001", "text": 'Fei\n"Hello!"'}]},
        "rows": [{"id": "row-1", "japanese": ["story01-b001-u001"], "official": ["en-01-u001"], "status": "anchored"}]}


def field_bytes():
    dialogue = xgdialog.encode_dialogue([
        xgdialog.DialogueBlockSpec(0, 24, 2, 'Fei\n"Hello!"<Delay:20><Close>'),
        xgdialog.DialogueBlockSpec(1, 24, 2, 'Untouched<Close>')])
    header = bytes(xgfield.FIELD_HEADER_MINIMUM)
    parts = [bytes([index]) * 10 for index in range(9)]
    parts[7] = dialogue
    return xgfield.build_field(header, parts)


def reviewed_mapping(data, document):
    component = xgfield.parse_field(data).parts[7].data
    block = xgdialog.parse_dialogue(component).blocks[0]
    return {"format": tr.MAPPING_FORMAT, "review_status": "static-reviewed", "review_evidence": "Fixture exact-source mapping and fitted layout",
        "source_field_sha256": tr.sha256(data), "source_dialogue_sha256": tr.sha256(component),
        "blocks": [{"block_id": 0, "source_payload_sha256": tr.sha256(block.payload),
            "fan_unit_ids": [document["units"][0]["id"]], "fan_units_sha256": tr.sha256(tr._json_bytes(document["units"])),
            "text": 'Fei\n"Welcome!"<Delay:20><Close>', "width": 24, "height": 2}]}


class TranslationSourceTests(unittest.TestCase):
    def test_fan_integrity_and_edition_are_checked(self):
        document = fan()
        self.assertIs(tr.validate_fan(document, source()), document)
        for field, value in [("translationMethod", "Context-aware independent retranslation; semantically reviewed"),
                             ("sourceSha256", "b" * 64)]:
            changed = copy.deepcopy(document)
            changed[field] = value
            with self.assertRaises(tr.TranslationError):
                tr.validate_fan(changed, source())

    def test_tampered_fan_text_and_duplicate_ids_fail(self):
        for change in (lambda doc: doc["units"][0].update(text="Changed"),
                       lambda doc: doc["units"].append(copy.deepcopy(doc["units"][0]))):
            document = fan()
            change(document)
            with self.assertRaises(tr.TranslationError):
                tr.validate_fan(document, source())

    def test_alignment_foreign_and_duplicate_ids_fail(self):
        tr.validate_alignment(alignment(), "01")
        bad = alignment()
        bad["rows"][0]["official"] = ["foreign"]
        with self.assertRaises(tr.TranslationError):
            tr.validate_alignment(bad, "01")
        bad = alignment()
        bad["units"]["japanese"].append(bad["units"]["japanese"][0])
        with self.assertRaises(tr.TranslationError):
            tr.validate_alignment(bad, "01")

    def test_audit_reports_missing_fan_without_fallback(self):
        complete = tr.corpus_audit([alignment()], {"story01": fan()})
        self.assertEqual(complete["selected_fan_passage_count"], 1)
        self.assertEqual(complete["verified_rom_replacements"], 0)
        missing = tr.corpus_audit([alignment()], {})
        self.assertEqual(missing["missing_selected_fan_passages"], ["story01-b001-u001"])
        self.assertEqual(tr.candidate_index([alignment()], {}), {})

    def test_candidate_matching_keeps_ambiguity_and_review_status(self):
        other = alignment()
        other["id"] = "02"
        indexed = tr.candidate_index([alignment(), other], {"story01": fan()})
        key = tr.normalized_dialogue('<Fei>\n"Hello!"<Close>', game_tokens=True)
        self.assertEqual(len(indexed[key]), 2)
        self.assertTrue(all(row["verified"] is False for row in indexed[key]))
        self.assertNotEqual(key, tr.normalized_dialogue('Fei\n"hello!"'))

    def test_catalogue_discovery_reads_code_without_executing(self):
        responses = {tr.SOURCE_ORIGIN + "/": b'<script type="module" src="/assets/index-abc.js"></script>',
            tr.SOURCE_ORIGIN + "/assets/index-abc.js": b'const files=["assets/ArchivePage-def.js"]',
            tr.SOURCE_ORIGIN + "/assets/ArchivePage-def.js": b'var chapters=[Z(-1,`Opening Movie`,`a`),Z(0,`Prologue`,`b`),Z(1,`Lahan`,`c`)];'}
        chapters, metadata = tr.discover_chapters(responses.__getitem__)
        self.assertEqual(chapters, ["opening", "00", "01"])
        self.assertEqual(metadata["catalogue_sha256"], tr.sha256(responses[metadata["catalogue_url"]]))

    def test_local_asset_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "aligned").mkdir()
            raw = tr._json_bytes(alignment())
            (root / "aligned/01.json").write_bytes(raw)
            tr._write_json(root / "manifest.json", {"format": tr.CORPUS_FORMAT, "chapters": ["01"],
                "assets": {"aligned/01.json": {"sha256": tr.sha256(raw)}}})
            alignments, fans = tr.load_corpus(root)
            self.assertEqual(len(alignments), 1)
            self.assertEqual(fans, {})
            (root / "aligned/01.json").write_bytes(raw + b" ")
            with self.assertRaisesRegex(tr.TranslationError, "checksum mismatch"):
                tr.load_corpus(root)

    def test_fetch_import_and_offline_load_use_only_fan_edition(self):
        chapter = alignment()
        chapter["id"] = "opening"
        urls = {tr.SOURCE_ORIGIN + "/": b'<script src="/assets/index-test.js"></script>',
            tr.SOURCE_ORIGIN + "/assets/index-test.js": b'"assets/ArchivePage-test.js"',
            tr.SOURCE_ORIGIN + "/assets/ArchivePage-test.js": b'var chapters=[Z(-1,`Opening Movie`,`a`)];',
            tr.SOURCE_ORIGIN + "/assets/scripts/xenogears/aligned/opening.json": tr._json_bytes(chapter),
            tr.SOURCE_ORIGIN + "/assets/scripts/xenogears/fan-retranslation/story01.json": tr._json_bytes(fan())}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            audit = tr.fetch_corpus(root, download=urls.__getitem__)
            self.assertEqual(audit["fan_passage_count"], 1)
            alignments, fans = tr.load_corpus(root)
            self.assertEqual(alignments[0]["id"], "opening")
            self.assertEqual(fans["story01"]["translationMethod"], tr.FAN_METHOD)
            urls[tr.SOURCE_ORIGIN + "/assets/scripts/xenogears/fan-retranslation/story01.json"] = b"<!doctype html>"
            missing = tr.fetch_corpus(root, download=urls.__getitem__)
            self.assertEqual(missing["missing_fan_stories"], ["story01"])
            self.assertEqual(tr.load_corpus(root)[1], {})

    def test_content_key_preserves_words_across_page_controls(self):
        self.assertEqual(tr.translation_content_key('Fei\n“One.”▽\n“Two.”'),
                         tr.translation_content_key('Fei\n"One.<New>Two."<Close>', game_tokens=True))


class ReviewedTranslationTests(unittest.TestCase):
    def setUp(self):
        self.source = field_bytes()
        self.fan = fan()
        self.mapping = reviewed_mapping(self.source, self.fan)

    def compile(self):
        return tr.compile_verified_field(self.source, self.mapping, {"story01": self.fan})

    def test_compiler_preserves_unselected_payloads_and_other_components(self):
        result, report = self.compile()
        before, after = xgfield.parse_field(self.source), xgfield.parse_field(result)
        self.assertEqual([part.data for part in before.parts if part.index != 7], [part.data for part in after.parts if part.index != 7])
        old_blocks = xgdialog.parse_dialogue(before.parts[7].data).blocks
        new_blocks = xgdialog.parse_dialogue(after.parts[7].data).blocks
        self.assertEqual(new_blocks[0].text, 'Fei\n"Welcome!"<Delay:20><Close>')
        self.assertEqual(old_blocks[1].payload, new_blocks[1].payload)
        self.assertEqual(report["runtime_status"], "not_playtested")

    def test_modified_source_is_rejected(self):
        self.mapping["source_field_sha256"] = "0" * 64
        with self.assertRaises(tr.TranslationError):
            self.compile()

    def test_dropped_delay_is_rejected(self):
        self.mapping["blocks"][0]["text"] = 'Fei\n"Welcome!"<Close>'
        with self.assertRaisesRegex(tr.TranslationError, "control/name"):
            self.compile()

    def test_unreviewed_wording_is_rejected(self):
        self.mapping["blocks"][0]["text"] = 'Fei\n"Different!"<Delay:20><Close>'
        with self.assertRaisesRegex(tr.TranslationError, "Fan wording"):
            self.compile()

    def test_changed_fan_source_is_rejected(self):
        self.fan["units"][0]["text"] = "Another revision"
        with self.assertRaisesRegex(tr.TranslationError, "wording changed"):
            self.compile()

    def test_bad_window_dimensions_or_line_width_are_rejected(self):
        for width, height in [(10, 2), (24, 1), (65, 2), (24, 5)]:
            with self.subTest(width=width, height=height):
                self.mapping["blocks"][0].update(width=width, height=height)
                with self.assertRaises(tr.TranslationError):
                    self.compile()

    def test_duplicate_mapping_and_missing_review_are_rejected(self):
        self.mapping["blocks"].append(copy.deepcopy(self.mapping["blocks"][0]))
        with self.assertRaisesRegex(tr.TranslationError, "duplicated"):
            self.compile()
        self.mapping["blocks"].pop()
        self.mapping["review_status"] = "candidate"
        with self.assertRaisesRegex(tr.TranslationError, "static review"):
            self.compile()


if __name__ == "__main__":
    unittest.main()
