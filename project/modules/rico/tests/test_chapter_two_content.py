"""Historical Chapter 2 dialogue and knowledge boundaries, without disc builds.

These retained scene records do not define the default narrated interludes.
The current release's allowed text and progression have their own tests.
"""

import json
from pathlib import Path
import re
import unittest

from modules.rico import build as rico
from shared.tools.xgdialog import decode_text, encode_text


CONTENT = Path(__file__).resolve().parents[1] / "content"
SCENE_KEYS = frozenset("""
arrival_delivery room_first room_bed_before room_schedule_before room_exit_before
hammer_report baptism_before baptism_exchange baptism_after dblock_worker_before
dblock_battler_before dblock_prisoner_before dblock_hammer_before pardon_question
prep_stier defense_before defense_after fei_explosion_report dblock_worker_missing
dblock_battler_missing murders_report investigation_request sewer_entry sewer_burnt
sewer_slime sewer_message sewer_gramps sewer_key sewer_bell sewer_drain redrum_before
redrum_after injury_exit room_bed_injured bandage finals_before finals_exchange
finals_after title_clerk title_prisoner title_fei room_bed_after room_schedule_after
league_return crash_before crash_public central_approach central_flight chapter_end
treatment_gate_locked fei_before_investigation fei_after_investigation sewer_after_redrum
room_suzarn_before room_suzarn_after_baptism room_hammer_before_baptism room_hammer_after_redrum room_hammer_after_title
dblock_worker_after_redrum dblock_battler_after_redrum
prep_hammer_waiting prep_hammer_injured prep_hammer_after_title
clerk_schedule_before clerk_waiting clerk_after_title
citan_before_investigation citan_after_investigation citan_after_redrum citan_after_title
""".split())
PLAIN_SPEAKERS = frozenset((
    "Hammer", "Suzarn", "Guard", "Infirmary Attendant", "Worker", "Leonardo",
    "Prisoner", "Battler", "Arena Official", "Gramps", "Clerk", "Rue",
))


def plain(text):
    return " ".join(re.sub(r"<[^>]+>", " ", text).split())


class ChapterTwoContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expansion = json.loads((CONTENT / "chapter_02_expansion.json").read_text(encoding="utf-8"))
        cls.legacy = json.loads((CONTENT / "chapter_02_the_champ.json").read_text(encoding="utf-8"))
        cls.scenes = cls.expansion["scenes"]

    def scene_text(self, *keys):
        return " ".join(plain(block) for key in keys for block in self.scenes[key])

    def test_all_scene_hooks_and_legacy_ids_are_present(self):
        self.assertEqual(self.expansion["format"], "xenogears-rico-chapter-two-expansion-v1")
        self.assertEqual(self.expansion["chapter_id"], 2)
        self.assertEqual(set(self.scenes), SCENE_KEYS)
        self.assertEqual(len(SCENE_KEYS), 70)
        self.assertEqual(len(self.legacy["blocks"]), 38)
        self.assertEqual(self.legacy["id"], 2)
        self.assertEqual(self.legacy["target_field"], 722)
        self.assertEqual(self.legacy["donor_field"], 218)
        for key, blocks in self.scenes.items():
            with self.subTest(scene=key):
                self.assertIsInstance(blocks, list)
                self.assertTrue(blocks)
                self.assertTrue(all(isinstance(block, str) and block for block in blocks))
        self.assertEqual(set(self.expansion["inventory_labels"]),
                         {"sewer_passkey", "small_bell", "spare_bandage"})
        self.assertTrue(set(self.expansion["descriptions"]).issubset(SCENE_KEYS))

    def test_every_block_encodes_and_fits_without_mid_sentence_page_turns(self):
        entries = [(f"{key}/{index}", block)
                   for key, blocks in self.scenes.items() for index, block in enumerate(blocks)]
        entries += [(f"legacy/{index}", block) for index, block in enumerate(self.legacy["blocks"])]
        entries.append(("selection", self.legacy["selection_exposition"]))
        for key, block in entries:
            with self.subTest(block=key):
                self.assertEqual(decode_text(encode_text(block)), block)
                self.assertEqual(rico._dialogue_layout_issues(block), ())
                self.assertEqual(rico._dialogue_sentence_page_issues(block), ())
                for page in block[:-len("<Close>")].split("<New>"):
                    rows = page.splitlines()
                    speaker = rows[0] in PLAIN_SPEAKERS or bool(re.fullmatch(r"<(Rico|Fei|Citan)>", rows[0]))
                    # Named portrait windows reserve one of four rows for
                    # the speaker; narrator/selection cards use up to seven.
                    self.assertLessEqual(len(rows) - int(speaker), 3 if speaker else 7)

    def test_arrival_baptism_and_explosion_establish_the_investigation(self):
        self.assertIn("breathing", self.scene_text("arrival_delivery"))
        self.assertIn("prisoner's awake", self.scene_text("hammer_report"))
        self.assertIn("Fei Fong Wong", self.scene_text("hammer_report"))
        self.assertIn("I don't want to fight you", self.scene_text("baptism_exchange"))
        self.assertIn("Fei lies on the ground", self.scene_text("baptism_after"))
        self.assertIn("Rank A", self.scene_text("baptism_after"))
        self.assertIn("Weltall blew", self.scene_text("fei_explosion_report"))
        self.assertIn("Suzarn", self.scene_text("murders_report"))
        self.assertIn("makes five", self.scene_text("murders_report"))
        investigation = self.scene_text("investigation_request")
        self.assertIn("My men set it up", investigation)
        self.assertIn("I'm sorry", investigation)
        self.assertIn("I do not know", investigation.replace("I don't", "I do not"))
        self.assertTrue(any(block.startswith("<Citan>\n") for block in self.scenes["investigation_request"]))

    def test_opening_preserves_recovery_interval_and_one_meeting_destination(self):
        self.assertIn("Four days later", plain(self.scenes["room_first"][0]))
        self.assertFalse(any(block.startswith("<Fei>\n")
                             for block in self.scenes["arrival_delivery"]))
        report = self.scene_text("hammer_report")
        self.assertIn("Bring him to the yard", report)
        self.assertNotIn("bring him here", report.casefold())
        self.assertIn("Come up", self.scenes["hammer_report"][1])

    def test_hammer_repeat_reports_follow_known_work_without_inventing_a_request(self):
        self.assertIn("yard", self.scene_text("room_hammer_before_baptism"))
        self.assertIn("Stier", self.scene_text("dblock_hammer_before"))
        self.assertNotIn("coupling", self.scene_text("room_hammer_before_baptism", "dblock_hammer_before"))

    def test_sewer_clues_keep_citan_and_provisional_humanity_observation(self):
        for key in ("sewer_entry", "sewer_burnt", "sewer_message", "redrum_before", "redrum_after"):
            with self.subTest(scene=key):
                self.assertTrue(any(block.startswith("<Citan>\n") for block in self.scenes[key]))
        self.assertIn("sewer passkey", self.scene_text("sewer_key"))
        self.assertIn("small bell", self.scene_text("sewer_bell"))
        self.assertIn("burnt", self.scene_text("sewer_burnt"))
        aftermath = self.scene_text("redrum_after")
        self.assertIn("something human", aftermath)
        self.assertIn("may have survived", aftermath)
        self.assertIn("Survived?", aftermath)
        # This scene must remain compatible with the much later Id revelation.
        resolution = aftermath + " " + " ".join(plain(block) for block in self.legacy["blocks"][17:20])
        self.assertNotRegex(resolution.casefold(), r"redrum.{0,60}(killed|murdered|the killer)")
        self.assertNotRegex(resolution.casefold(), r"the killer.{0,40}redrum")
        self.assertNotIn("that thing killed the battlers", resolution.casefold())

    def test_injury_fei_victory_and_changed_room_status_remain_distinct(self):
        self.assertIn("arm is bleeding", self.scene_text("injury_exit"))
        self.assertIn("Hammer finishes the knot", self.scene_text("bandage"))
        self.assertIn("winner is Fei Fong Wong", self.scene_text("finals_exchange"))
        self.assertIn("You beat me", self.scene_text("finals_after"))
        self.assertIn("new Champion", self.scene_text("title_clerk", "room_bed_after"))
        self.assertIn("don't owe me anything", self.scene_text("title_fei"))
        self.assertIn("group bouts", self.scene_text("league_return"))

    def test_crash_public_account_is_not_a_private_malfunction_explanation(self):
        public = self.scenes["crash_public"]
        self.assertIn("Kaiser's box", self.scene_text("crash_public"))
        self.assertTrue(any(block.startswith("Arena Official\n") and
                            "They say it went out of control" in plain(block) for block in public))
        private = self.scene_text("crash_before", "central_flight", "chapter_end")
        private += " " + " ".join(plain(self.legacy["blocks"][index]) for index in (27, 28, 34, 35))
        self.assertNotRegex(private.casefold(), r"malfunction|controls|stopped answering|not responding")
        self.assertIn("air duct", private)
        self.assertIn("somewhere to hide", private)

    def test_pardon_and_later_revelations_are_not_explained_early(self):
        pardon = self.scene_text("pardon_question")
        self.assertIn("pardon", pardon)
        self.assertIn("Keep wondering", pardon)
        self.assertNotIn("because", pardon.casefold())
        # Only visible text belongs here; descriptions deliberately document
        # later revelations so implementers know what must stay off screen.
        visible = self.scene_text(*self.scenes)
        visible += " " + " ".join(plain(block) for block in self.legacy["blocks"])
        self.assertNotRegex(visible, r"(?i)\b(Id|Solaris|Wels|Anne|Anna|mother|father|parentage|DNA)\b")
        selection = plain(self.legacy["selection_exposition"])
        self.assertNotRegex(selection, r"(?i)\b(murder|murders|Redrum|Finals|assassination|trap)\b")
        self.assertEqual(self.legacy["blocks"][-1], "CHAPTER 2 COMPLETE<Close>")


if __name__ == "__main__":
    unittest.main()
