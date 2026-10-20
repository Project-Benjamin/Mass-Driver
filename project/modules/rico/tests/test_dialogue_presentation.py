from __future__ import annotations

import json
from pathlib import Path
import unittest

from modules.rico import dialogue_presentation as presentation


class DialoguePresentationTests(unittest.TestCase):
    def test_mixed_speakers_get_separate_native_windows(self) -> None:
        result = presentation.plan_dialogue(
            "Anne\nCome here, Rico.<New><Rico>\nI am here, Mom.<Close>"
        )
        self.assertEqual([item.speaker for item in result], ["Anne", "Rico"])
        self.assertEqual(result[1].text, "<Rico>\nI am here, Mom.<Close>")
        self.assertTrue(all(item.height == 4 for item in result))
        self.assertTrue(all("<New>" not in item.text for item in result))

    def test_unlabeled_pronoun_pages_retain_the_speaker(self) -> None:
        result = presentation.plan_dialogue(
            "ETHOS PRIEST\nHer suffering is over.<New>"
            "She leaves behind her son.<Close>"
        )
        self.assertTrue(all(item.speaker == "Ethos Priest" for item in result))
        self.assertTrue(all(item.text.startswith("ETHOS PRIEST\n") for item in result))

    def test_narrator_can_introduce_a_speaker_later_in_one_block(self) -> None:
        result = presentation.plan_dialogue(
            "Outside, Rico gathers wood.<New><Rico>\nThese will burn.<Close>"
        )
        self.assertEqual([item.speaker for item in result], [None, "Rico"])
        self.assertEqual(result[0].text, "Outside, Rico gathers wood.<Close>")

    def test_system_and_bracketed_pages_reset_speaker(self) -> None:
        result = presentation.plan_dialogue(
            "<Rico>\nOpen the gate.<New>SYSTEM\nGATE OPEN.<New>"
            "The lights go dark.<New><Fei>\nIt worked.<New>"
            "[Rico leaves.]<New>Silence returns.<Close>"
        )
        self.assertEqual(
            [item.speaker for item in result], ["Rico", None, None, "Fei", None, None]
        )

    def test_choice_preserves_control_indentation_order_and_rows(self) -> None:
        choice = "<Opcode:01:FF>Continue?\n     Enter\n     Not yet<Close>"
        result = presentation.plan_dialogue("<Rico>\nWhere now?<New>" + choice)
        self.assertIsNone(result[-1].speaker)
        self.assertEqual(result[-1].text, choice)
        self.assertEqual(result[-1].height, 3)

    def test_unknown_uppercase_heading_is_not_a_cast_member(self) -> None:
        result = presentation.plan_dialogue("POWER RELAY\nSTATUS: NOMINAL<Close>")
        self.assertIsNone(result[0].speaker)
        self.assertEqual(result[0].text, "POWER RELAY\nSTATUS: NOMINAL<Close>")

    def test_each_portrait_page_repeats_name_and_fits_native_bounds(self) -> None:
        body = (
            "The people outside the wall need food and medicine. "
            "We can carry both through the gate before it closes tonight."
        )
        result = presentation.plan_dialogue("<Rico>\n" + body + "<Close>")
        self.assertGreater(len(result), 1)
        words = []
        for item in result:
            rows = item.text.removesuffix("<Close>").split("\n")
            self.assertEqual(rows[0], "<Rico>")
            self.assertLessEqual(len(rows), 4)
            self.assertEqual((item.width, item.height), (41, 4))
            self.assertEqual(item.width + 17, presentation.WINDOW_WIDTH)
            self.assertTrue(all(presentation.glyph_units(row) <= 41 for row in rows))
            words.extend(" ".join(rows[1:]).split())
        self.assertEqual(words, body.split())

    def test_sentence_boundary_is_preferred_when_a_sentence_fits(self) -> None:
        result = presentation.plan_dialogue(
            "<Rico>\nWe can leave now. The people outside need food and medicine.<Close>"
        )
        self.assertTrue(result[0].text.endswith("We can leave now.<Close>"))

    def test_wait_and_delay_controls_are_preserved_without_width(self) -> None:
        result = presentation.plan_dialogue(
            "Anne\nRico...<Wait><Delay:16> come here.<Close>"
        )
        self.assertIn("<Wait><Delay:16>", result[0].text)
        self.assertEqual(presentation.glyph_units("<Rico><Wait>"), 8)

    def test_overlong_word_and_unknown_controls_fail_without_guessing(self) -> None:
        with self.assertRaises(presentation.DialoguePresentationError):
            presentation.plan_dialogue("<Rico>\n" + "a" * 21 + "<Close>")
        with self.assertRaises(presentation.DialoguePresentationError):
            presentation.plan_dialogue("<Rico>\n<Opcode:99:FF>Test.<Close>")

    def test_all_authored_chapter_and_expansion_blocks_conserve_words(self) -> None:
        content = Path(__file__).resolve().parents[1] / "content"
        for path in sorted(content.glob("chapter_*.json")):
            document = json.loads(path.read_text(encoding="utf-8"))
            blocks = document.get("blocks", []) or [
                text for scene in document.get("scenes", {}).values() for text in scene
            ]
            for index, text in enumerate(blocks):
                with self.subTest(file=path.name, block=index):
                    # The planner independently checks story/control conservation.
                    segments = presentation.plan_dialogue(text)
                    self.assertTrue(segments)
                    for segment in segments:
                        rows = segment.text.removesuffix("<Close>").split("\n")
                        capacity = 41 if segment.speaker else 59
                        self.assertLessEqual(len(rows), 4 if segment.speaker else 7)
                        self.assertTrue(all(
                            presentation.glyph_units(row) <= capacity for row in rows
                        ))


if __name__ == "__main__":
    unittest.main()
