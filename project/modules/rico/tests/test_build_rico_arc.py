from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

from dataclasses import replace
import hashlib
import math
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import tools.build_rico_arc as rico
from tools import xgrico_balance as balance
from modules.rico.recruitment import RICO_RECRUITMENT_PROFILE as recruitment
from tools.xgdeathblows import DEATHBLOW_PROFILES, learned_mask
from tools.xgfield import parse_field
from tools.xgscript import AtelScript


PROJECT_ROOT = REPOSITORY_ROOT
RICO_AUDIT_ROOT = PROJECT_ROOT / "work" / "rico_arc_audit" / "disc1"


class RicoStoryTests(unittest.TestCase):
    def test_all_seven_chapters_compile_in_canonical_order(self) -> None:
        chapters = rico.load_chapters()
        report = rico.validate_story(chapters)

        self.assertEqual([chapter.chapter_id for chapter in chapters], list(range(1, 8)))
        self.assertEqual(chapters[0].title, "Mother's Promise")
        self.assertEqual(chapters[0].music, rico.CHAPTER_ONE_MUSIC_ID)
        self.assertEqual(rico.CHAPTER_ONE_MUSIC_ID, 0x08)
        self.assertEqual([chapter.disc for chapter in chapters], [1, 1, 1, 2, 2, 2, 2])
        self.assertEqual(
            rico.CHAPTER_FIELDS,
            {
                1: {chapter_id: 720 + chapter_id for chapter_id in range(1, 8)},
                2: {chapter_id: 229 + chapter_id for chapter_id in range(1, 8)},
            },
        )
        self.assertEqual(report["chapter_count"], 7)
        self.assertTrue(all(item["dialogue_size"] < 0x10000 for item in report["chapters"]))
        self.assertTrue(all(chapter.selection_exposition for chapter in chapters))
        self.assertTrue(
            all(
                len(item["selection_exposition_sha256"]) == 64
                for item in report["chapters"]
            )
        )

    def test_anne_translation_is_consistent_in_all_authored_story_text(self) -> None:
        chapters = rico.load_chapters()
        authored_text = "\n".join(
            text
            for chapter in chapters
            for text in (
                chapter.selection_exposition,
                *chapter.blocks,
                *rico._playable_custom_texts(
                    rico._playable_chapter_contract(chapter.chapter_id)
                ),
                *(
                    interaction.name
                    for interaction in rico._playable_chapter_contract(
                        chapter.chapter_id
                    ).interactions
                ),
            )
        )

        self.assertRegex(authored_text, r"\bAnne\b")
        self.assertNotRegex(authored_text, r"\bAnna\b")

    def test_private_scene_keeps_the_approved_admission_and_staging(self) -> None:
        chapter = rico.load_chapters()[3]
        text = "\n".join(chapter.blocks)

        self.assertIn("Can we speak in private?", text)
        self.assertIn("They leave. The door\ncloses behind them.", text)
        self.assertIn("I abandoned you, Rico.", text)
        self.assertIn("Say the whole thing.", text)
        self.assertIn("don't ask me to call you Father", text)
        self.assertNotIn("The door stays open", text)
        self.assertNotIn("You were Kaiser everywhere else", text)
        self.assertNotIn("Say their names", text)

    def test_resolve_is_a_chosen_return_not_a_coronation(self) -> None:
        text = "\n".join(rico.load_chapters()[6].blocks)
        plain = " ".join(text.replace("<New>", " ").split())

        self.assertIn("I won't come back as an heir", plain)
        self.assertIn("I won't come back as the Champ", plain)
        self.assertIn("FOR D BLOCK", text)
        self.assertNotIn("SYSTEM\nMESSAGE STORED", text)
        self.assertNotIn("recording channel", text.casefold())
        self.assertIn("I will come back as myself", plain)

    def test_required_story_bridges_are_routed_and_continuity_safe(self) -> None:
        chapters = rico.load_chapters()
        contracts = {
            chapter_id: rico._playable_chapter_contract(chapter_id)
            for chapter_id in range(1, 8)
        }

        self.assertEqual(contracts[1].exit_dialogue, (20,))
        self.assertTrue(chapters[0].blocks[19].startswith("["))
        self.assertFalse(chapters[0].blocks[20].startswith("["))
        self.assertNotIn(19, contracts[1].exit_dialogue)
        self.assertEqual(chapters[0].blocks[20], "END OF CHAPTER 1<Close>")
        chapter_one_ending = "\n".join(chapters[0].blocks[19:21])
        self.assertNotIn("Pale morning light", chapter_one_ending)
        self.assertNotIn("CHAPTER 1 COMPLETE", chapter_one_ending)
        self.assertNotIn("Anne's lesson remains with Rico", chapter_one_ending)
        self.assertNotIn("Adversity will not decide who I become", chapter_one_ending)
        chapter_two_exit_refs = tuple(
            ref for ref in contracts[2].exit_dialogue if isinstance(ref, int)
        )
        self.assertEqual(
            chapter_two_exit_refs,
            (27, 28, 30, 31, 32, 33, 34, 35, 37),
        )
        chapter_two_blocks = chapters[1].blocks
        chapter_two_plain = tuple(
            " ".join(block.replace("<New>", " ").split())
            for block in chapter_two_blocks
        )
        self.assertIn("guards searched Stier", chapter_two_plain[30])
        self.assertIn("Rico was not inside", chapter_two_plain[30])
        self.assertIn("bedroom is next door", chapter_two_plain[31])
        self.assertIn("special Rank S privileges", chapter_two_plain[31])
        self.assertIn("Kaiser Sigmund", chapter_two_plain[32])
        self.assertIn("report to the Central District", chapter_two_plain[32])
        self.assertIn("All right. I'll go", chapter_two_plain[33])
        self.assertIn("Guards at every turn", chapter_two_plain[34])
        self.assertIn("opened the way for Fei", chapter_two_plain[35])
        self.assertIn("air duct above the entrance", chapter_two_plain[35])
        self.assertIn("somewhere to hide", chapter_two_plain[36])
        # Rico's private dialogue must not certify the public malfunction story.
        for index in (28, 34):
            self.assertNotIn("controls", chapter_two_plain[index].casefold())
            self.assertNotIn("malfunction", chapter_two_plain[index].casefold())
        chapter_two_text = "\n".join(chapter_two_blocks).casefold()
        for noncanonical in (
            "sealed palace household index",
            "every guard in d block is hunting you",
            "palace guard pulled away",
            "central district is almost empty",
            "rue just sent for fei",
            "committee supplied stier",
            "who used me",
            "lure",
            "bait",
        ):
            self.assertNotIn(noncanonical, chapter_two_text)
        self.assertIn("Citan's copy", contracts[3].exit_dialogue[0])
        self.assertIn("party returns to Nortune", chapters[3].selection_exposition)
        self.assertIn("buried Fatima vessel", chapters[3].selection_exposition)

        chapter_five = "\n".join(chapters[4].blocks)
        chapter_five_plain = " ".join(chapter_five.split())
        self.assertIn("Anne's offsite copies are secure", chapter_five)
        self.assertIn(
            "records still inside this partition are not",
            chapter_five_plain.lower(),
        )
        self.assertNotIn("We may lose Anne's record", chapter_five)
        self.assertIn("FINAL LIFT TRANSPONDER: VERIFIED", chapter_five)

        chapter_six = contracts[6]
        stages_six = {
            stage.bit: stage
            for interaction in chapter_six.interactions
            for stage in interaction.stages
        }
        self.assertIn(1, stages_six[1].dialogue)
        self.assertIn(8, stages_six[4].after_dialogue)
        self.assertIn(31, chapter_six.exit_dialogue)
        for ref in (1, 8, 31):
            self.assertFalse(chapters[5].blocks[ref].startswith("["))

        chapter_seven = contracts[7]
        routed_seven = set(chapter_seven.exit_dialogue)
        for interaction in chapter_seven.interactions:
            for stage in interaction.stages:
                routed_seven.update(stage.dialogue)
                routed_seven.update(stage.after_dialogue)
        for ref in (8, 11, 21):
            self.assertIn(ref, routed_seven)
            self.assertFalse(chapters[6].blocks[ref].startswith("["))
        self.assertEqual(chapter_seven.exit_dialogue, (23, 24))
        self.assertEqual(
            chapter_seven.exit_dialogue,
            tuple(range(len(chapters[6].blocks) - 2, len(chapters[6].blocks))),
        )
        self.assertIn("stonebell", chapters[6].blocks[23].casefold())
        self.assertIn("between two stones", chapters[6].blocks[23].casefold())
        self.assertIn("journey back to Nortune", chapters[6].blocks[23])
        self.assertEqual(chapters[6].blocks[24], "THE END<Close>")
        chapter_seven_custom = "\n".join(
            rico._playable_custom_texts(contracts[7])
        )
        self.assertIn("I carried my promise to Mom out of Nortune", chapter_seven_custom)
        self.assertNotIn("I carried Mom's lesson", chapter_seven_custom)

        chapter_one = contracts[1]
        stonebell = next(
            interaction
            for interaction in chapter_one.interactions
            if interaction.name == "stonebell vase"
        )
        watering = stonebell.stages[0].dialogue[0]
        self.assertIn("tips the ladle slowly", watering)
        self.assertIn("giving the stonebell a drink", watering)
        stove = next(
            interaction
            for interaction in chapter_one.interactions
            if interaction.name == "cooking counter"
        )
        stove_stage = next(stage for stage in stove.stages if stage.bit == 6)
        self.assertEqual(stove_stage.after_dialogue[1:], (22, 23))
        self.assertNotIn(24, stove_stage.after_dialogue)
        self.assertNotIn(25, stove_stage.after_dialogue)
        self.assertEqual(stonebell.stages[0].after_dialogue, (24, 25))
        tea_stage = next(stage for stage in stove.stages if stage.bit == 10)
        self.assertIn("kettle begins to whistle", tea_stage.dialogue[0])
        self.assertIn("water has boiled", tea_stage.dialogue[0])
        self.assertIn("another scoop", chapters[0].blocks[23])
        self.assertIn("stonebell", chapters[0].blocks[23].casefold())
        self.assertIn("streets near the market", chapters[0].blocks[24])
        self.assertIn("it was stepped on", chapters[0].blocks[24])
        self.assertIn("we could try to save it", chapters[0].blocks[24])
        self.assertIn("Yes, I remember", chapters[0].blocks[25])
        self.assertIn("most precious gift I've ever received", chapters[0].blocks[25])
        self.assertIn("Look how healthy it is now", chapters[0].blocks[25])
        self.assertIn("you've been taking care of it", chapters[0].blocks[25])
        self.assertIn("between bare stones", chapters[0].blocks[25])
        self.assertIn("pale blue bells always turn toward the light", chapters[0].blocks[25])
        self.assertIn("You have a good soul, Rico", chapters[0].blocks[25])
        self.assertIn("Never let this world forget that", chapters[0].blocks[25])
        self.assertIn("<New><Rico>\nI won't, Mom...", chapters[0].blocks[25])
        flower_scene = "\n".join(chapters[0].blocks[24:26])
        for retired_phrase in (
            "rocky cliff past Nortune's outer wall",
            "You said you liked blue",
            "most precious thing in this house",
            "brought it to me with love",
            "gives the world something gentle",
            "Never let a cruel world take that choice",
        ):
            self.assertNotIn(retired_phrase, flower_scene)
        self.assertIn("doctors can do no more", chapters[0].blocks[13])
        self.assertIn("This sickness will take me soon", chapters[0].blocks[13])
        post_chore_lesson = "\n".join(chapters[0].blocks[12:19])
        self.assertIn("cannot fight this sickness for me", post_chore_lesson)
        self.assertIn("what you carry after I am gone", post_chore_lesson)
        self.assertIn("Do not make others suffer because you are suffering", post_chore_lesson)
        self.assertIn("have power over those who looked down on you", post_chore_lesson)
        self.assertIn("protect people, not to take revenge", post_chore_lesson)
        self.assertIn("cruelty that wounded us will end with you", post_chore_lesson)
        self.assertNotIn("Medicine takes time", post_chore_lesson)
        self.assertNotIn("Stop the harm when you can", post_chore_lesson)
        self.assertNotIn("That is resolve", post_chore_lesson)
        self.assertNotIn("choose the door", post_chore_lesson)
        self.assertNotIn("people still waiting outside", post_chore_lesson)
        self.assertEqual(chapters[0].blocks[20], "END OF CHAPTER 1<Close>")
        chapter_one_ending = "\n".join(chapters[0].blocks[19:21]).casefold()
        self.assertNotIn("pale morning light", chapter_one_ending)
        self.assertNotIn("chapter 1 complete", chapter_one_ending)
        self.assertIn("end of chapter 1", chapter_one_ending)
        self.assertNotIn("anne's lesson remains with rico", chapter_one_ending)
        self.assertNotIn("adversity will not decide", chapter_one_ending)
        for removed_teaser in (
            "d block",
            "warden's record",
            "prison collar",
            "battling",
            "the champ",
            "chapter 2",
        ):
            self.assertNotIn(removed_teaser, chapter_one_ending)

        chapter_one_text = "\n".join(chapters[0].blocks).casefold()
        self.assertNotIn("pendant", chapter_one_text)
        self.assertNotIn("memento", chapter_one_text)

        chapter_four_text = (
            "\n".join(chapters[3].blocks)
            + "\n"
            + "\n".join(rico._playable_custom_texts(contracts[4]))
        ).casefold()
        self.assertIn("memento pendant remains on sigmund's desk", chapter_four_text)
        self.assertNotIn("pendant beneath his shirt", chapter_four_text)
        self.assertNotIn("pendant at his chest", chapter_four_text)

        chapter_seven_text = (
            "\n".join(chapters[6].blocks)
            + "\n"
            + "\n".join(rico._playable_custom_texts(chapter_seven))
        ).casefold()
        self.assertNotIn("pendant", chapter_seven_text)
        self.assertNotIn("memento", chapter_seven_text)
        searchable = (
            "\n".join(chapters[6].blocks)
            + "\n"
            + "\n".join(rico._playable_custom_texts(chapter_seven))
        ).casefold()
        for invented in (
            "silent communications room",
            "port relay",
            "bridge relay",
            "engine relay",
            "recording terminal",
            "recording channel",
            "system\nmessage stored",
        ):
            self.assertNotIn(invented, searchable)

    def test_chapter_two_covers_the_canonical_d_block_arc_in_order(self) -> None:
        chapter = rico.load_chapters()[1]
        contract = rico._playable_chapter_contract(2)
        text = "\n".join(chapter.blocks)
        plain = " ".join(text.replace("<New>", " ").split())

        self.assertEqual(len(chapter.blocks), 38)
        self.assertEqual(
            tuple(interaction.name for interaction in contract.interactions),
            ("mantel clock", "Hammer", "Fei", "arena passage"),
        )
        self.assertEqual(
            tuple(
                tuple(stage.bit for stage in interaction.stages)
                for interaction in contract.interactions
            ),
            ((7,), (1, 4), (2, 5), (3, 6)),
        )
        self.assertEqual(contract.required_bits, (1, 2, 3, 4, 5, 6))
        self.assertEqual(contract.optional_bits, (7,))
        self.assertEqual(
            (contract.exit_x, contract.exit_z, contract.exit_triangle),
            (-304, 9, 84),
        )
        self.assertEqual(
            {
                index
                for index, block in enumerate(chapter.blocks)
                if block.lstrip().startswith("[")
            },
            {1, 12, 17, 23, 26, 29, 36},
        )
        routed = {
            ref
            for interaction in contract.interactions
            for stage in interaction.stages
            for refs in (
                stage.dialogue,
                stage.after_dialogue,
            )
            for ref in refs
            if isinstance(ref, int)
        }
        routed.update(
            ref for ref in contract.exit_dialogue if isinstance(ref, int)
        )
        self.assertEqual(
            routed,
            {
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                13,
                14,
                15,
                16,
                18,
                19,
                20,
                21,
                22,
                24,
                25,
                27,
                28,
                30,
                31,
                32,
                33,
                34,
                35,
                37,
            },
        )
        ordered_phrases = (
            "Begin the Baptism",
            "Five Battlers now",
            "Redrum",
            "Your arm is bleeding",
            "Fei Fong Wong wins the Finals",
            "You beat me, Fei. No excuses",
            "strikes the Kaiser's box",
            "guards searched Stier",
            "bedroom is next door",
            "special Rank S privileges",
            "Kaiser Sigmund wishes to meet you",
            "All right. I'll go",
            "Guards at every turn",
            "opened the way for Fei",
            "air duct above the entrance",
        )
        offsets = [plain.index(phrase) for phrase in ordered_phrases]
        self.assertEqual(offsets, sorted(offsets))
        for obsolete in (
            "collar terminal",
            "Committee Control ordered Fei's match",
            "rewrote your match",
            "sealed palace household index",
            "release authority",
            "every guard in D Block is hunting you",
            "palace guard pulled away",
            "Central District is almost empty",
            "Rue just sent for Fei",
            "Committee supplied Stier",
            "who used me",
            "lure",
            "bait",
        ):
            self.assertNotIn(obsolete.casefold(), text.casefold())
        self.assertEqual(chapter.blocks[-1], "CHAPTER 2 COMPLETE<Close>")

    def test_runtime_text_never_reveals_unseen_tasks(self) -> None:
        contracts = tuple(
            rico._playable_chapter_contract(chapter_id)
            for chapter_id in range(1, 8)
        )
        runtime_text = "\n".join(
            text
            for contract in contracts
            for text in rico._playable_custom_texts(contract)
        )
        for removed in (
            "Check the window, then speak with Mom",
            "Hammer said there was a new contract",
            "Hammer said he found something in the new contract",
            "I will read the dispatch after the room is packed",
            "A Kislev dispatch is waiting in the tall locker",
        ):
            self.assertNotIn(removed, runtime_text)
        self.assertNotIn("OBJECTIVE\n", runtime_text)

        family_seal = contracts[2].interactions[0].stages[1]
        state_dialogue = {
            completed: dialogue
            for completed, dialogue in family_seal.locked_dialogue_states
        }
        self.assertEqual(set(state_dialogue), {(), (2,), (3,)})
        self.assertIn("both the portrait index", state_dialogue[()][0])
        self.assertIn("still need Anne's medical ledger", state_dialogue[(2,)][0])
        self.assertIn("still need Anne's portrait index", state_dialogue[(3,)][0])


class RicoDialogueLayoutTests(unittest.TestCase):
    def test_every_story_and_hub_block_is_word_safe_and_page_safe(self) -> None:
        raw_blocks = [
            block
            for chapter in rico.load_chapters()
            for block in chapter.blocks
        ] + [
            chapter.selection_exposition
            for chapter in rico.load_chapters()
        ] + list(rico._hub_dialogue_blocks())

        self.assertTrue(
            any(rico._dialogue_layout_issues(block) for block in raw_blocks)
        )
        for block in raw_blocks:
            laid_out = rico._reflow_dialogue_text(block)
            self.assertFalse(rico._dialogue_layout_issues(laid_out))
            self.assertEqual(
                rico._semantic_dialogue_atoms(laid_out),
                rico._semantic_dialogue_atoms(block),
            )
            self.assertEqual(rico._reflow_dialogue_text(laid_out), laid_out)
            self.assertEqual(laid_out.count("<New>"), block.count("<New>"))

    def test_chapter_one_never_turns_a_page_mid_sentence(self) -> None:
        chapter = rico.load_chapters()[0]
        contract = rico._playable_chapter_contract(1)
        texts = (
            chapter.selection_exposition,
            *chapter.blocks,
            *rico._playable_custom_texts(contract),
        )

        for index, text in enumerate(texts):
            with self.subTest(index=index):
                laid_out = rico._reflow_dialogue_text(
                    text,
                    sentence_safe_pages=True,
                )
                self.assertFalse(rico._dialogue_sentence_page_issues(laid_out))

        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            "sentence crosses a page turn",
        ):
            rico._reflow_dialogue_text(
                "Anne\nA sentence is cut in<New>half.<Close>",
                sentence_safe_pages=True,
            )

    def test_fitted_windows_match_their_widest_and_tallest_page(self) -> None:
        blocks = (
            "<Rico>\nI promise.<Close>",
            "Anne\nMercy is strength.<New>Let it guide you.<Close>",
        )
        parsed = rico.parse_dialogue(
            rico._dialogue_data(
                blocks,
                fit_windows=True,
                sentence_safe_pages=True,
            )
        )

        for block, source in zip(parsed.blocks, blocks, strict=True):
            laid_out = rico._reflow_dialogue_text(
                source,
                sentence_safe_pages=True,
            )
            self.assertEqual(
                (block.width, block.height),
                rico._dialogue_window_dimensions(laid_out),
            )
            page_rows = [
                page.split("\n")
                for page in laid_out.removesuffix("<Close>").split("<New>")
            ]
            widest = max(
                rico._dialogue_units(row)
                for rows in page_rows
                for row in rows
            )
            self.assertGreaterEqual(block.width | 1, widest)
            self.assertEqual(block.height, max(map(len, page_rows)))
            self.assertLessEqual(block.width, rico.DIALOGUE_WINDOW_WIDTH)
            self.assertLessEqual(block.height, rico.DIALOGUE_WINDOW_HEIGHT)
        self.assertTrue(
            all(
                (block.width, block.height)
                != (rico.DIALOGUE_WINDOW_WIDTH, rico.DIALOGUE_WINDOW_HEIGHT)
                for block in parsed.blocks
            )
        )

    def test_speakers_records_and_stage_directions_keep_their_structure(self) -> None:
        capacity = rico.DIALOGUE_WINDOW_WIDTH | 1
        self.assertEqual(
            rico._layout_dialogue_page(
                "ARCHIVIST\nPlease report to central control.", capacity
            )[0][0],
            "ARCHIVIST",
        )
        self.assertEqual(
            rico._layout_dialogue_page(
                "SECURITY CAPTAIN\nRue Cohen, you are under arrest...", capacity
            )[0][0],
            "SECURITY CAPTAIN",
        )
        self.assertEqual(
            rico._layout_dialogue_page(
                "ARCHIVE RECORD 1\nSUBJECT: ANNE BANDERAS\nSTATUS: SEALED",
                capacity,
            )[0][:3],
            ["ARCHIVE RECORD 1", "SUBJECT: ANNE BANDERAS", "STATUS: SEALED"],
        )
        self.assertEqual(
            rico._layout_dialogue_page(
                "<Rico>\nGood. Do the work you already promised.", capacity
            )[0],
            ["<Rico>", "Good. Do the work you already", "promised."],
        )
        self.assertEqual(
            rico._layout_dialogue_page(
                "[Long before D Block called him\n"
                "the Champ, Rico lived with his\n"
                "mother beyond the capital walls.]",
                capacity,
            )[0],
            [
                "[Long before D Block called",
                "him the Champ, Rico lived",
                "with his mother beyond the",
                "capital walls.]",
            ],
        )

    def test_choice_rows_are_never_reflowed(self) -> None:
        for block in rico._hub_dialogue_blocks():
            self.assertTrue(block.startswith(rico.DIALOGUE_CHOICE_START))
            self.assertEqual(rico._reflow_dialogue_text(block), block)
            self.assertEqual(block.count("\n     "), 2)
            rows = block.removesuffix("<Close>").split("\n")
            self.assertEqual(len(rows), 3)
            self.assertTrue(rows[0].endswith("?"))
            self.assertEqual(rows[1:], ["     Enter", "     Not yet"])

    def test_stage_choice_custom_texts_are_allocated_and_layout_safe(self) -> None:
        choice = (
            "<Opcode:01:FF>Enter the arena?\n"
            "     Not yet\n"
            "     Enter<Close>"
        )
        rejected = "<Rico>\nI will check Stier again.<Close>"
        stage = rico._stage(
            1,
            "Stier is ready.<Close>",
            choice=choice,
            accepted=2,
            rejected=(rejected,),
        )
        contract = rico.PlayableChapter(
            chapter_id=2,
            interactions=(rico.PlayableInteraction("test", 0, 0, 0, (stage,)),),
            exit_x=0,
            exit_z=0,
            exit_triangle=0,
            required_bits=(1,),
            exit_dialogue=(),
            exit_locked_steps=(
                (1, "<Rico>\nThe test remains unfinished.<Close>"),
            ),
        )

        custom = rico._playable_custom_texts(contract)
        self.assertEqual(custom.count(choice), 1)
        self.assertEqual(custom.count(rejected), 1)
        self.assertLess(custom.index(choice), custom.index(rejected))
        self.assertEqual(rico._playable_choice_count(choice), 2)
        for text in (choice, rejected):
            laid_out = rico._reflow_dialogue_text(text)
            self.assertFalse(rico._dialogue_layout_issues(laid_out))

    def test_compiled_dialogue_contains_the_laid_out_text(self) -> None:
        blocks = rico.load_chapters()[5].blocks
        parsed = rico.parse_dialogue(rico._dialogue_data(blocks))
        self.assertEqual(
            tuple(block.text for block in parsed.blocks),
            tuple(rico._reflow_dialogue_text(text) for text in blocks),
        )
        self.assertEqual(
            parsed.blocks[30].text,
            "<Rico>\nGood. Do the work you already\npromised.<Close>",
        )


class RicoRuntimeTests(unittest.TestCase):
    def test_stage_choice_rejection_cannot_commit_or_start_accepted_work(self) -> None:
        choice = (
            "<Opcode:01:FF>Enter the arena?\n"
            "     Not yet\n"
            "     Enter<Close>"
        )
        rejected = "<Rico>\nNot until I am ready.<Close>"
        stage = rico._stage(
            1,
            "Stier is ready.<Close>",
            choice=choice,
            accepted=2,
            rejected=(rejected,),
            battle=6,
            gear=True,
            solo_rico=True,
        )
        interaction = rico.PlayableInteraction(
            "arena",
            0,
            0,
            0,
            (stage,),
            repeat_dialogue=("ARENA CONTROL\nMATCH COMPLETE<Close>",),
        )
        contract = rico.PlayableChapter(
            chapter_id=2,
            interactions=(interaction,),
            exit_x=0,
            exit_z=0,
            exit_triangle=0,
            required_bits=(1,),
            exit_dialogue=(),
            exit_locked_steps=(
                (1, "<Rico>\nThe test remains unfinished.<Close>"),
            ),
        )
        custom_texts = rico._playable_custom_texts(contract)
        custom_ids = {text: 100 + index for index, text in enumerate(custom_texts)}
        base = 0x4000
        action = rico._build_playable_interaction_action(
            interaction,
            base_pc=base,
            authored_base=0,
            authored_count=1,
            custom_ids=custom_ids,
            field_music=0x22,
            chapter_party=(rico.RICO_ID,),
            contract=contract,
            return_hub=rico.HUB_FIELDS[1],
            next_chapter_exposition_ids=(),
        )

        prompt = (
            rico._choice_dialog(custom_ids[choice])
            + bytes((0xA9, 0x12, 0x9C))
        )
        prompt_at = action.index(prompt)
        branch_at = prompt_at + len(prompt)
        self.assertEqual(
            action[branch_at : branch_at + 6],
            b"\x02"
            + struct.pack("<H", rico.MENU_SELECTION_VARIABLE)
            + struct.pack("<H", 2)
            + b"\x40",
        )
        rejected_pc = struct.unpack_from("<H", action, branch_at + 6)[0]
        rejected_at = rejected_pc - base
        self.assertGreater(rejected_at, branch_at + 8)

        accepted_path = action[branch_at + 8 : rejected_at]
        fixed_battle = rico.mass_driver._fixed_battle(6)
        progress = rico.mass_driver._set_var_bit(
            rico.PLAYABLE_STATE_VARIABLE,
            stage.bit,
        )
        self.assertIn(fixed_battle, accepted_path)
        self.assertIn(progress, accepted_path)

        rejection_prefix = rico._wait() + rico._dialogue_sequence(
            (custom_ids[rejected],)
        )
        rejection_finish = rico._playable_action_finish(
            rejected_pc + len(rejection_prefix)
        )
        rejection_path = action[
            rejected_at : rejected_at + len(rejection_prefix) + len(rejection_finish)
        ]
        self.assertEqual(rejection_path, rejection_prefix + rejection_finish)
        self.assertNotIn(fixed_battle, rejection_path)
        self.assertNotIn(progress, rejection_path)
        self.assertTrue(rejection_path.endswith(b"\xFE\x53\x00"))

    def test_hub_routes_every_chapter_without_live_disc_checks(self) -> None:
        base = 0x1000
        expected_parties = {
            1: (rico.YOUNG_RICO_ID,),
            2: (5, 0),
            3: (5, 0, 2),
            4: (5, 0, 3),
            5: (5, 0, 3),
            6: (5, 0, 3),
            7: (5, 0),
        }
        self.assertEqual(rico.CHAPTER_PARTIES, expected_parties)
        clear_chapter_state = rico.mass_driver._set_variable_s16(
            rico.PLAYABLE_STATE_VARIABLE,
            0,
        )
        for disc in (1, 2):
            with self.subTest(disc=disc):
                for marker in rico.HUB_MARKERS:
                    chapter_id = marker.chapter_id
                    field = rico.CHAPTER_FIELDS[disc][chapter_id]
                    # Chapter 2 opens its narrated interludes directly in
                    # Rico's room; the historical Fei reception is bypassed.
                    entry_field = field
                    entry_party = (5,) if chapter_id == 2 else expected_parties[chapter_id]
                    routine = rico._build_hub_marker_action(
                        base,
                        marker,
                        field,
                        rico._hub_selection_exposition_ids(
                            rico.load_chapters()
                        )[chapter_id],
                    )
                    self.assertNotIn(b"\xFE\xCD", routine)
                    transition = (
                        clear_chapter_state
                        + (
                            rico.mass_driver._set_variable_s16(
                                rico.CHAPTER_TWO_PERSISTENT_STATE_VARIABLE,
                                0,
                            )
                            + rico.mass_driver._set_variable_s16(
                                rico.CHAPTER_TWO_HAMMER_STATE_VARIABLE,
                                0,
                            )
                            if chapter_id == 2
                            else b""
                        )
                        + rico._change_field(entry_field, 0)
                    )
                    self.assertEqual(routine.count(transition), 1)
                    self.assertEqual(routine.count(rico._change_field(entry_field, 0)), 1)
                    if chapter_id == 2:
                        self.assertNotIn(rico._change_field(68, 0), routine)
                    active_party_setup = bytearray()
                    for character in range(11):
                        active_party_setup.extend(
                            b"\xFE\x19" + bytes((character,))
                        )
                    for character in entry_party:
                        active_party_setup.extend(
                            b"\xFE\x18"
                            + bytes((character,))
                            + b"\xFE\x1A"
                        )
                    frame_mask_setup = bytearray()
                    for character in range(11):
                        frame_mask_setup.extend(
                            b"\xFE\x3B" + rico._immediate(character)
                        )
                    for character in entry_party:
                        frame_mask_setup.extend(
                            b"\xFE\x3A" + rico._immediate(character)
                        )
                    self.assertNotIn(b"\xFE\x3A", active_party_setup)
                    self.assertNotIn(b"\xFE\x3B", active_party_setup)
                    self.assertNotIn(b"\xFE\x18", frame_mask_setup)
                    self.assertNotIn(b"\xFE\x19", frame_mask_setup)
                    self.assertNotIn(b"\xFE\x1A", frame_mask_setup)
                    chapter_inventory_setup = (
                        rico._chapter_one_inventory_restriction()
                        if chapter_id == 1
                        else b""
                    )
                    self.assertEqual(
                        routine.count(
                            bytes(active_party_setup)
                            + bytes(frame_mask_setup)
                            + chapter_inventory_setup
                            + transition
                        ),
                        1,
                    )
                    self.assertEqual(
                        routine.count(rico._choice_dialog(chapter_id - 1)),
                        1,
                    )
                    self.assertEqual(routine.count(b"\xA9\x12\x9C"), 1)
                    self.assertNotIn(b"\x09\xFF", routine)
        hub_text = "\n".join(rico._hub_dialogue_blocks())
        self.assertEqual(len(rico._hub_dialogue_blocks()), 7)
        self.assertIn("MOTHER'S PROMISE", hub_text)
        self.assertNotIn("MOM'S LESSON", hub_text)
        self.assertIn("RESOLVE", hub_text)
        self.assertNotIn("Change Disc", hub_text)
        self.assertNotIn("Earlier Chapters", hub_text)
        self.assertNotIn("About this project", hub_text)

    def test_chapter_one_temporarily_keeps_only_child_items_and_equipment(
        self,
    ) -> None:
        self.assertEqual(
            rico.CHAPTER_ONE_RETAINED_ITEM_STACKS,
            ((0x39, 10), (0x3F, 12)),
        )
        self.assertEqual(
            sum(
                quantity
                for _item_id, quantity in rico.CHAPTER_ONE_HIDDEN_ITEM_STACKS
            ),
            36,
        )
        self.assertEqual(
            rico.CHAPTER_ONE_HIDDEN_WEAPON_STACKS,
            (
                (0x32, 1),
                (0x10, 1),
                (0x39, 1),
                (0x33, 1),
                (0x01, 1),
                (0x3A, 1),
                (0x1F, 1),
            ),
        )
        self.assertEqual(
            rico.CHAPTER_ONE_HIDDEN_ACCESSORY_STACKS,
            ((0x6A, 1), (0x62, 3)),
        )
        self.assertEqual(
            rico.CHAPTER_ONE_HIDDEN_INVENTORY_OBJECT_STACKS,
            (
                *rico.CHAPTER_ONE_HIDDEN_ITEM_STACKS,
                (0x0132, 1),
                (0x0110, 1),
                (0x0139, 1),
                (0x0133, 1),
                (0x0101, 1),
                (0x013A, 1),
                (0x011F, 1),
                (0x026A, 1),
                (0x0262, 3),
            ),
        )
        self.assertEqual(
            sum(
                quantity
                for _object_id, quantity in (
                    rico.CHAPTER_ONE_HIDDEN_INVENTORY_OBJECT_STACKS
                )
            ),
            47,
        )

        expected_restriction = b"".join(
            b"\x8D" + rico._immediate(object_id)
            for object_id, quantity in (
                rico.CHAPTER_ONE_HIDDEN_INVENTORY_OBJECT_STACKS
            )
            for _copy in range(quantity)
        )
        expected_restore = b"".join(
            b"\x8C" + rico._immediate(object_id)
            for object_id, quantity in (
                rico.CHAPTER_ONE_HIDDEN_INVENTORY_OBJECT_STACKS
            )
            for _copy in range(quantity)
        )
        restriction = rico._chapter_one_inventory_restriction()
        restore = rico._chapter_one_inventory_restore()
        self.assertEqual(restriction, expected_restriction)
        self.assertEqual(restore, expected_restore)
        self.assertEqual(len(restriction), 47 * 3)
        self.assertEqual(len(restore), 47 * 3)
        for item_id, _quantity in rico.CHAPTER_ONE_RETAINED_ITEM_STACKS:
            self.assertNotIn(b"\x8D" + rico._immediate(item_id), restriction)
            self.assertNotIn(b"\x8C" + rico._immediate(item_id), restore)
        for object_id, quantity in (
            rico.CHAPTER_ONE_HIDDEN_INVENTORY_OBJECT_STACKS
        ):
            self.assertEqual(
                restriction.count(b"\x8D" + rico._immediate(object_id)),
                quantity,
            )
            self.assertEqual(
                restore.count(b"\x8C" + rico._immediate(object_id)),
                quantity,
            )

        chapter_one_launch = rico._chapter_launch_body(
            1,
            rico.CHAPTER_FIELDS[1][1],
        )
        chapter_one_state_clear = rico.mass_driver._set_variable_s16(
            rico.PLAYABLE_STATE_VARIABLE,
            0,
        )
        self.assertEqual(chapter_one_launch.count(restriction), 1)
        self.assertLess(
            chapter_one_launch.index(restriction),
            chapter_one_launch.index(chapter_one_state_clear),
        )
        for chapter_id in range(2, 8):
            self.assertNotIn(
                restriction,
                rico._chapter_launch_body(
                    chapter_id,
                    rico.CHAPTER_FIELDS[1][chapter_id],
                ),
            )
        self.assertNotIn(restriction, rico._hub_launch_body(rico.HUB_FIELDS[1]))
        self.assertNotIn(restore, rico._hub_launch_body(rico.HUB_FIELDS[1]))

        next_launch = rico._chapter_launch_body(
            2,
            rico.CHAPTER_FIELDS[1][2],
        )
        hub_launch = rico._hub_launch_body(rico.HUB_FIELDS[1])
        live_completion = rico._build_chapter_one_live_funeral_completion(
            base_pc=0x2000,
            choice_id=10,
            next_field=rico.CHAPTER_FIELDS[1][2],
            return_hub=rico.HUB_FIELDS[1],
        )
        transition = rico._playable_chapter_contract(1).exit_transition
        self.assertIsNotNone(transition)
        # The retired still-image fallback no longer installs its presentation
        # constants in active builds. Supply inert selectors here so its two
        # departure branches remain covered alongside the live funeral.
        with patch.multiple(
            rico,
            create=True,
            CHAPTER_ONE_STILL_SCREEN_ENTITY=0,
            CHAPTER_ONE_STILL_FIELD_FILE_IDS=frozenset((1, 2, 3)),
            CHAPTER_ONE_ANNA_SICKBED_FIELD_FILE_ID=1,
            CHAPTER_ONE_RICO_MOURNING_FIELD_FILE_ID=2,
            CHAPTER_ONE_FUNERAL_FIELD_FILE_ID=3,
            CHAPTER_ONE_STILL_FADE_FRAMES=1,
        ):
            fallback_completion = rico._build_chapter_one_funeral_story(
                base_pc=0x2000,
                transition=transition,
                sickness_ids=(0,),
                loss_ids=(1,),
                funeral_ids=(2,),
                epilogue_ids=(3,),
                choice_id=4,
                return_hub=rico.HUB_FIELDS[1],
            )
        for completion in (live_completion, fallback_completion):
            self.assertEqual(completion.count(restore), 2)
            self.assertEqual(completion.count(next_launch), 1)
            self.assertEqual(completion.count(hub_launch), 1)
            self.assertLess(completion.index(restore), completion.index(next_launch))
            self.assertIn(restore + hub_launch, completion)

    def test_chapter_one_ancillary_mapping_rewrites_every_story_route(self) -> None:
        fields = rico._chapter_one_ancillary_fields(
            {"firewood": 64, "aftermath": 65, "funeral": 66}
        )
        self.assertEqual(
            fields,
            rico.UNIFIED_DISC2_CHAPTER_ONE_ANCILLARY_FIELDS,
        )
        self.assertEqual(
            rico.DEFAULT_CHAPTER_ONE_ANCILLARY_FIELDS,
            rico.ChapterOneAncillaryFields(
                firewood=rico.CHAPTER_ONE_FIREWOOD_FIELD,
                aftermath=rico.CHAPTER_ONE_AFTERMATH_FIELD,
                funeral=rico.CHAPTER_ONE_FUNERAL_FIELD,
            ),
        )

        door = rico._chapter_one_door_transition_body(fields.firewood)
        self.assertTrue(door.endswith(rico._change_field(64, 0) + b"\x5B"))
        self.assertNotIn(
            rico._change_field(rico.CHAPTER_ONE_FIREWOOD_FIELD, 0),
            door,
        )

        firewood = rico._build_chapter_one_firewood_story(
            base_pc=0x4000,
            aftermath_field=fields.aftermath,
        )
        self.assertTrue(firewood.endswith(rico._change_field(65, 0) + b"\x5B"))
        self.assertNotIn(
            rico._change_field(rico.CHAPTER_ONE_AFTERMATH_FIELD, 0),
            firewood,
        )

        aftermath = rico._build_chapter_one_aftermath_story(
            base_pc=0x5000,
            sickness_ids=range(6),
            loss_ids=range(6, 10),
            funeral_field=fields.funeral,
        )
        self.assertTrue(aftermath.endswith(rico._change_field(66, 0) + b"\x5B"))
        self.assertNotIn(
            rico._change_field(rico.CHAPTER_ONE_FUNERAL_FIELD, 0),
            aftermath,
        )

        for invalid in (
            {"firewood": 64, "aftermath": 65},
            {"firewood": 64, "aftermath": 64, "funeral": 66},
            {"firewood": -1, "aftermath": 65, "funeral": 66},
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(rico.RicoArcBuildError):
                    rico._chapter_one_ancillary_fields(invalid)

    def test_prepare_replacements_relocates_all_unified_disc2_ancillary_fields(
        self,
    ) -> None:
        chapters = rico.load_chapters()

        class FakeDiscReader:
            def canonical(self, canonical_id: int) -> bytes:
                return f"retail-{canonical_id}".encode("ascii")

        def build_scene(
            donor_bundle: bytes,
            chapter: rico.Chapter,
            return_hub: int,
            next_chapter: rico.Chapter | None,
            *,
            ancillary_fields: rico.ChapterOneAncillaryFields | None = None,
            chapter_two_bedroom_field: int = rico.CHAPTER_TWO_BEDROOM_FIELD,
        ) -> bytes:
            del donor_bundle, return_hub, next_chapter
            fields = rico._chapter_one_ancillary_fields(ancillary_fields)
            return (
                f"scene-{chapter.chapter_id}-firewood-{fields.firewood}-"
                f"bedroom-{chapter_two_bedroom_field}"
            ).encode(
                "ascii",
            )

        def build_firewood(
            donor_bundle: bytes,
            young_rico_source_bundle: bytes,
            chapter: rico.Chapter,
            *,
            aftermath_field: int = rico.CHAPTER_ONE_AFTERMATH_FIELD,
        ) -> bytes:
            del donor_bundle, young_rico_source_bundle, chapter
            return f"firewood-to-{aftermath_field}".encode("ascii")

        def build_aftermath(
            donor_bundle: bytes,
            chapter: rico.Chapter,
            *,
            funeral_field: int = rico.CHAPTER_ONE_FUNERAL_FIELD,
        ) -> bytes:
            del donor_bundle, chapter
            return f"aftermath-to-{funeral_field}".encode("ascii")

        def build_funeral(*args: object, **kwargs: object) -> bytes:
            del args, kwargs
            return b"funeral"

        def build_bedroom(
            donor_bundle: bytes,
            chapter: rico.Chapter,
            main_field: int,
        ) -> bytes:
            del donor_bundle
            self.assertEqual(chapter.chapter_id, 2)
            return f"bedroom-to-{main_field}".encode("ascii")

        identity = lambda data: data
        reader = FakeDiscReader()
        fake_battle_identities = {
            canonical_id: (
                len(reader.canonical(canonical_id)),
                hashlib.sha256(reader.canonical(canonical_id)).hexdigest(),
            )
            for canonical_id in rico.PLAYABLE_BATTLE_RESOURCE_IDS
        }
        donor_graphics = {
            "hub": reader.canonical(
                rico._field_bundle_id(rico.HUB_DONOR_FIELD) + 1
            ),
            "firewood": reader.canonical(
                rico._field_bundle_id(rico.CHAPTER_ONE_FIREWOOD_DONOR_FIELD) + 1
            ),
            "aftermath": reader.canonical(
                rico._field_bundle_id(rico.CHAPTER_ONE_AFTERMATH_DONOR_FIELD) + 1
            ),
            "funeral": reader.canonical(
                rico._field_bundle_id(rico.CHAPTER_ONE_LIVE_FUNERAL_DONOR_FIELD)
                + 1
            ),
            "bedroom": reader.canonical(
                rico._field_bundle_id(rico.CHAPTER_TWO_BEDROOM_DONOR_FIELD) + 1
            ),
        }
        with patch.multiple(
            rico,
            PLAYABLE_BATTLE_RESOURCE_IDENTITIES=fake_battle_identities,
            HUB_DONOR_GRAPHICS_SIZE=len(donor_graphics["hub"]),
            HUB_DONOR_GRAPHICS_SHA256=hashlib.sha256(
                donor_graphics["hub"]
            ).hexdigest(),
            CHAPTER_ONE_FIREWOOD_DONOR_GRAPHICS_SIZE=len(
                donor_graphics["firewood"]
            ),
            CHAPTER_ONE_FIREWOOD_DONOR_GRAPHICS_SHA256=hashlib.sha256(
                donor_graphics["firewood"]
            ).hexdigest(),
            CHAPTER_ONE_AFTERMATH_DONOR_GRAPHICS_SIZE=len(
                donor_graphics["aftermath"]
            ),
            CHAPTER_ONE_AFTERMATH_DONOR_GRAPHICS_SHA256=hashlib.sha256(
                donor_graphics["aftermath"]
            ).hexdigest(),
            CHAPTER_ONE_LIVE_FUNERAL_DONOR_GRAPHICS_SIZE=len(
                donor_graphics["funeral"]
            ),
            CHAPTER_ONE_LIVE_FUNERAL_DONOR_GRAPHICS_SHA256=hashlib.sha256(
                donor_graphics["funeral"]
            ).hexdigest(),
            CHAPTER_TWO_BEDROOM_GRAPHICS_SIZE=len(donor_graphics["bedroom"]),
            CHAPTER_TWO_BEDROOM_GRAPHICS_SHA256=hashlib.sha256(
                donor_graphics["bedroom"]
            ).hexdigest(),
            _build_chapter_one_firewood_bundle=build_firewood,
            _build_chapter_one_aftermath_bundle=build_aftermath,
            _build_chapter_one_live_funeral_bundle=build_funeral,
            _build_chapter_two_bedroom_bundle=build_bedroom,
            _build_scene_bundle=build_scene,
            _build_hub_bundle=lambda *args, **kwargs: b"hub",
            _build_title_bundle=lambda *args, **kwargs: b"title",
            _build_initial_gamestate=identity,
            patch_battle_weight_resource=identity,
            patch_memento_system_data=identity,
            patch_young_rico_equipment_names=identity,
            patch_weight_mutation_overlay=identity,
            build_rico_native_title_menu=lambda data, portrait: (b"atlas", data),
            patch_rico_native_title_graphics=lambda data, atlas: data,
            patch_rico_native_title_overlay=lambda data, expected_disc: data,
            _build_disc2_title_overlay=identity,
        ), patch(
            # This legacy orchestration fixture contains synthetic field bytes.
            # The expanded campaign is checked separately with real donors.
            "modules.rico.chapter_two.expand_replacements",
            side_effect=lambda disc, replacements, chapters, bedrooms: replacements,
        ):
            replacements = rico.prepare_replacements(
                reader,
                chapters,
                disc2_ancillary_fields={
                    "firewood": 64,
                    "aftermath": 65,
                    "funeral": 66,
                },
                disc2_chapter_two_bedroom_field=(
                    rico.UNIFIED_DISC2_CHAPTER_TWO_BEDROOM_FIELD
                ),
            )

        fields_by_disc = {
            1: rico.DEFAULT_CHAPTER_ONE_ANCILLARY_FIELDS,
            2: rico.UNIFIED_DISC2_CHAPTER_ONE_ANCILLARY_FIELDS,
        }
        bedrooms_by_disc = {
            1: rico.CHAPTER_TWO_BEDROOM_FIELD,
            2: rico.UNIFIED_DISC2_CHAPTER_TWO_BEDROOM_FIELD,
        }
        for disc, fields in fields_by_disc.items():
            with self.subTest(disc=disc):
                by_id = {item.canonical_id: item for item in replacements[disc]}
                self.assertEqual(
                    by_id[rico._field_bundle_id(fields.firewood)].data,
                    f"firewood-to-{fields.aftermath}".encode("ascii"),
                )
                self.assertEqual(
                    by_id[rico._field_bundle_id(fields.aftermath)].data,
                    f"aftermath-to-{fields.funeral}".encode("ascii"),
                )
                self.assertEqual(
                    by_id[rico._field_bundle_id(fields.funeral)].data,
                    b"funeral",
                )
                chapter_one = by_id[
                    rico._field_bundle_id(rico.CHAPTER_FIELDS[disc][1])
                ]
                self.assertEqual(
                    chapter_one.data,
                    (
                        f"scene-1-firewood-{fields.firewood}-"
                        f"bedroom-{bedrooms_by_disc[disc]}"
                    ).encode("ascii"),
                )
                bedroom = by_id[
                    rico._field_bundle_id(bedrooms_by_disc[disc])
                ]
                self.assertEqual(
                    bedroom.data,
                    f"bedroom-to-{rico.CHAPTER_FIELDS[disc][2]}".encode(
                        "ascii"
                    ),
                )

        disc1_ids = {item.canonical_id for item in replacements[1]}
        disc2_ids = {item.canonical_id for item in replacements[2]}
        relocated_ids = {
            canonical_id
            for field in (
                64,
                65,
                66,
                rico.UNIFIED_DISC2_CHAPTER_TWO_BEDROOM_FIELD,
            )
            for canonical_id in (
                rico._field_bundle_id(field),
                rico._field_bundle_id(field) + 1,
            )
        }
        legacy_ids = {
            canonical_id
            for field in (
                rico.CHAPTER_ONE_FIREWOOD_FIELD,
                rico.CHAPTER_ONE_AFTERMATH_FIELD,
                rico.CHAPTER_ONE_FUNERAL_FIELD,
                rico.CHAPTER_TWO_BEDROOM_FIELD,
            )
            for canonical_id in (
                rico._field_bundle_id(field),
                rico._field_bundle_id(field) + 1,
            )
        }
        self.assertTrue(relocated_ids.isdisjoint(disc1_ids))
        self.assertTrue(relocated_ids.issubset(disc2_ids))
        self.assertTrue(legacy_ids.issubset(disc1_ids))
        self.assertTrue(legacy_ids.isdisjoint(disc2_ids))

    def test_every_chapter_is_installed_on_both_discs_and_returns_locally(self) -> None:
        chapters = rico.load_chapters()

        class FakeDiscReader:
            def canonical(self, canonical_id: int) -> bytes:
                return f"retail-{canonical_id}".encode("ascii")

        scene_calls: list[tuple[int, int, int | None, int]] = []
        hub_calls: list[tuple[dict[int, int], tuple[int, ...]]] = []
        firewood_calls: list[int] = []
        aftermath_calls: list[int] = []
        funeral_calls: list[tuple[int, int, int]] = []
        bedroom_calls: list[tuple[int, int]] = []

        def build_scene(
            donor_bundle: bytes,
            chapter: rico.Chapter,
            return_hub: int,
            next_chapter: rico.Chapter | None,
            *,
            ancillary_fields: rico.ChapterOneAncillaryFields | None = None,
            chapter_two_bedroom_field: int = rico.CHAPTER_TWO_BEDROOM_FIELD,
        ) -> bytes:
            del donor_bundle, ancillary_fields
            scene_calls.append(
                (
                    chapter.chapter_id,
                    return_hub,
                    next_chapter.chapter_id if next_chapter is not None else None,
                    chapter_two_bedroom_field,
                )
            )
            return f"scene-{chapter.chapter_id}-hub-{return_hub}".encode("ascii")

        def build_hub(
            donor_bundle: bytes,
            chapter_fields: dict[int, int],
            hub_chapters: tuple[rico.Chapter, ...],
        ) -> bytes:
            del donor_bundle
            hub_calls.append(
                (
                    dict(chapter_fields),
                    tuple(chapter.chapter_id for chapter in hub_chapters),
                )
            )
            return b"hub"

        def build_aftermath(
            donor_bundle: bytes,
            chapter: rico.Chapter,
        ) -> bytes:
            del donor_bundle
            aftermath_calls.append(chapter.chapter_id)
            return b"live-bedroom-aftermath"

        def build_funeral(
            donor_bundle: bytes,
            young_rico_source_bundle: bytes,
            eton_source_bundle: bytes,
            chapter: rico.Chapter,
            next_chapter: rico.Chapter,
            return_hub: int,
        ) -> bytes:
            del (
                donor_bundle,
                young_rico_source_bundle,
                eton_source_bundle,
            )
            self.assertEqual(chapter.chapter_id, 1)
            funeral_calls.append(
                (chapter.chapter_id, next_chapter.chapter_id, return_hub)
            )
            return f"live-funeral-hub-{return_hub}".encode("ascii")

        def build_firewood(
            donor_bundle: bytes,
            young_rico_source_bundle: bytes,
            chapter: rico.Chapter,
        ) -> bytes:
            del donor_bundle, young_rico_source_bundle
            firewood_calls.append(chapter.chapter_id)
            return b"daylight-firewood"

        def build_bedroom(
            donor_bundle: bytes,
            chapter: rico.Chapter,
            main_field: int,
        ) -> bytes:
            del donor_bundle
            bedroom_calls.append((chapter.chapter_id, main_field))
            return f"champion-bedroom-to-{main_field}".encode("ascii")

        identity = lambda data: data
        fake_battle_identities = {
            canonical_id: (
                len(FakeDiscReader().canonical(canonical_id)),
                hashlib.sha256(
                    FakeDiscReader().canonical(canonical_id)
                ).hexdigest(),
            )
            for canonical_id in rico.PLAYABLE_BATTLE_RESOURCE_IDS
        }
        fake_hub_graphics = FakeDiscReader().canonical(
            rico._field_bundle_id(rico.HUB_DONOR_FIELD) + 1
        )
        fake_firewood_graphics = FakeDiscReader().canonical(
            rico._field_bundle_id(rico.CHAPTER_ONE_FIREWOOD_DONOR_FIELD) + 1
        )
        fake_aftermath_graphics = FakeDiscReader().canonical(
            rico._field_bundle_id(rico.CHAPTER_ONE_AFTERMATH_DONOR_FIELD) + 1
        )
        fake_funeral_graphics = FakeDiscReader().canonical(
            rico._field_bundle_id(rico.CHAPTER_ONE_LIVE_FUNERAL_DONOR_FIELD)
            + 1
        )
        fake_bedroom_graphics = FakeDiscReader().canonical(
            rico._field_bundle_id(rico.CHAPTER_TWO_BEDROOM_DONOR_FIELD) + 1
        )
        with patch.multiple(
            rico,
            PLAYABLE_BATTLE_RESOURCE_IDENTITIES=fake_battle_identities,
            HUB_DONOR_GRAPHICS_SIZE=len(fake_hub_graphics),
            HUB_DONOR_GRAPHICS_SHA256=hashlib.sha256(
                fake_hub_graphics
            ).hexdigest(),
            CHAPTER_ONE_FIREWOOD_DONOR_GRAPHICS_SIZE=len(fake_firewood_graphics),
            CHAPTER_ONE_FIREWOOD_DONOR_GRAPHICS_SHA256=hashlib.sha256(
                fake_firewood_graphics
            ).hexdigest(),
            CHAPTER_ONE_AFTERMATH_DONOR_GRAPHICS_SIZE=len(
                fake_aftermath_graphics
            ),
            CHAPTER_ONE_AFTERMATH_DONOR_GRAPHICS_SHA256=hashlib.sha256(
                fake_aftermath_graphics
            ).hexdigest(),
            CHAPTER_ONE_LIVE_FUNERAL_DONOR_GRAPHICS_SIZE=len(
                fake_funeral_graphics
            ),
            CHAPTER_ONE_LIVE_FUNERAL_DONOR_GRAPHICS_SHA256=hashlib.sha256(
                fake_funeral_graphics
            ).hexdigest(),
            CHAPTER_TWO_BEDROOM_GRAPHICS_SIZE=len(fake_bedroom_graphics),
            CHAPTER_TWO_BEDROOM_GRAPHICS_SHA256=hashlib.sha256(
                fake_bedroom_graphics
            ).hexdigest(),
            _build_chapter_one_aftermath_bundle=build_aftermath,
            _build_chapter_one_live_funeral_bundle=build_funeral,
            _build_chapter_one_firewood_bundle=build_firewood,
            _build_chapter_two_bedroom_bundle=build_bedroom,
            _build_initial_gamestate=identity,
            patch_battle_weight_resource=identity,
            patch_memento_system_data=identity,
            patch_young_rico_equipment_names=identity,
            patch_weight_mutation_overlay=identity,
            build_rico_native_title_menu=(
                lambda data, _portrait: (b"atlas", data)
            ),
            patch_rico_native_title_graphics=lambda data, _atlas: data,
            patch_rico_native_title_overlay=(
                lambda data, expected_disc: data
            ),
            _build_disc2_title_overlay=identity,
            _build_title_bundle=(
                lambda _source, hub: f"title-hub-{hub}".encode("ascii")
            ),
            _build_hub_bundle=build_hub,
            _build_scene_bundle=build_scene,
        ), patch(
            # Keep synthetic legacy routing data out of expansion validation;
            # real-donor integration tests cover the expanded campaign.
            "modules.rico.chapter_two.expand_replacements",
            side_effect=lambda disc, replacements, chapters, bedrooms: replacements,
        ):
            replacements = rico.prepare_replacements(FakeDiscReader(), chapters)

        expected_scene_calls = [
            (
                chapter.chapter_id,
                rico.HUB_FIELDS[disc],
                chapter.chapter_id + 1 if chapter.chapter_id < 7 else None,
                rico.CHAPTER_TWO_BEDROOM_FIELD,
            )
            for disc in (1, 2)
            for chapter in chapters
        ]
        self.assertEqual(scene_calls, expected_scene_calls)
        self.assertEqual(
            hub_calls,
            [
                (rico.CHAPTER_FIELDS[1], tuple(range(1, 8))),
                (rico.CHAPTER_FIELDS[2], tuple(range(1, 8))),
            ],
        )
        self.assertEqual(aftermath_calls, [1, 1])
        self.assertEqual(
            funeral_calls,
            [
                (1, 2, rico.HUB_FIELDS[1]),
                (1, 2, rico.HUB_FIELDS[2]),
            ],
        )
        self.assertEqual(firewood_calls, [1, 1])
        self.assertEqual(
            bedroom_calls,
            [
                (2, rico.CHAPTER_FIELDS[1][2]),
                (2, rico.CHAPTER_FIELDS[2][2]),
            ],
        )

        for disc in (1, 2):
            items = replacements[disc]
            replacement_ids = [item.canonical_id for item in items]
            chapter_ids = {
                canonical_id
                for target_field in rico.CHAPTER_FIELDS[disc].values()
                for canonical_id in (
                    rico._field_bundle_id(target_field),
                    rico._field_bundle_id(target_field) + 1,
                )
            }
            hub_ids = {
                rico._field_bundle_id(rico.HUB_FIELDS[disc]),
                rico._field_bundle_id(rico.HUB_FIELDS[disc]) + 1,
            }
            chapter_one_transition_ids = {
                rico._field_bundle_id(rico.CHAPTER_ONE_FIREWOOD_FIELD),
                rico._field_bundle_id(rico.CHAPTER_ONE_FIREWOOD_FIELD) + 1,
                rico._field_bundle_id(rico.CHAPTER_ONE_AFTERMATH_FIELD),
                rico._field_bundle_id(rico.CHAPTER_ONE_AFTERMATH_FIELD) + 1,
                rico._field_bundle_id(rico.CHAPTER_ONE_FUNERAL_FIELD),
                rico._field_bundle_id(rico.CHAPTER_ONE_FUNERAL_FIELD) + 1,
            }
            chapter_two_bedroom_ids = {
                rico._field_bundle_id(rico.CHAPTER_TWO_BEDROOM_FIELD),
                rico._field_bundle_id(rico.CHAPTER_TWO_BEDROOM_FIELD) + 1,
            }

            self.assertEqual(len(replacement_ids), len(set(replacement_ids)))
            self.assertTrue(chapter_ids.issubset(replacement_ids))
            self.assertTrue(hub_ids.isdisjoint(chapter_ids))
            self.assertTrue(hub_ids.issubset(replacement_ids))
            self.assertTrue(chapter_one_transition_ids.issubset(replacement_ids))
            self.assertTrue(chapter_two_bedroom_ids.issubset(replacement_ids))
            self.assertTrue({2468, 2470, 2471}.isdisjoint(replacement_ids))
            firewood = next(
                item
                for item in items
                if item.canonical_id
                == rico._field_bundle_id(rico.CHAPTER_ONE_FIREWOOD_FIELD)
            )
            self.assertEqual(firewood.data, b"daylight-firewood")
            firewood_graphics = next(
                item
                for item in items
                if item.canonical_id
                == rico._field_bundle_id(rico.CHAPTER_ONE_FIREWOOD_FIELD) + 1
            )
            self.assertEqual(
                firewood_graphics.data,
                FakeDiscReader().canonical(
                    rico._field_bundle_id(
                        rico.CHAPTER_ONE_FIREWOOD_DONOR_FIELD
                    )
                    + 1
                ),
            )
            aftermath = next(
                item
                for item in items
                if item.canonical_id
                == rico._field_bundle_id(rico.CHAPTER_ONE_AFTERMATH_FIELD)
            )
            self.assertEqual(aftermath.data, b"live-bedroom-aftermath")
            aftermath_graphics = next(
                item
                for item in items
                if item.canonical_id
                == rico._field_bundle_id(rico.CHAPTER_ONE_AFTERMATH_FIELD) + 1
            )
            self.assertEqual(aftermath_graphics.data, fake_aftermath_graphics)
            funeral = next(
                item
                for item in items
                if item.canonical_id
                == rico._field_bundle_id(rico.CHAPTER_ONE_FUNERAL_FIELD)
            )
            self.assertEqual(
                funeral.data,
                f"live-funeral-hub-{rico.HUB_FIELDS[disc]}".encode("ascii"),
            )
            funeral_graphics = next(
                item
                for item in items
                if item.canonical_id
                == rico._field_bundle_id(rico.CHAPTER_ONE_FUNERAL_FIELD) + 1
            )
            self.assertEqual(funeral_graphics.data, fake_funeral_graphics)
            bedroom = next(
                item
                for item in items
                if item.canonical_id
                == rico._field_bundle_id(rico.CHAPTER_TWO_BEDROOM_FIELD)
            )
            self.assertEqual(
                bedroom.data,
                f"champion-bedroom-to-{rico.CHAPTER_FIELDS[disc][2]}".encode(
                    "ascii"
                ),
            )
            bedroom_graphics = next(
                item
                for item in items
                if item.canonical_id
                == rico._field_bundle_id(rico.CHAPTER_TWO_BEDROOM_FIELD) + 1
            )
            self.assertEqual(bedroom_graphics.data, fake_bedroom_graphics)
            self.assertEqual(replacement_ids.count(rico.SYSTEM_NAMES_CANONICAL_ID), 1)
            title = next(
                item
                for item in items
                if item.canonical_id == rico.TITLE_FIELD_CANONICAL_ID
            )
            self.assertEqual(
                title.data,
                f"title-hub-{rico.HUB_FIELDS[disc]}".encode("ascii"),
            )
            for chapter in chapters:
                field_id = rico._field_bundle_id(
                    rico.CHAPTER_FIELDS[disc][chapter.chapter_id]
                )
                scene = next(item for item in items if item.canonical_id == field_id)
                self.assertEqual(
                    scene.data,
                    f"scene-{chapter.chapter_id}-hub-{rico.HUB_FIELDS[disc]}".encode(
                        "ascii"
                    ),
                )

    def test_dual_disc_targets_map_inside_both_retail_file_tables(self) -> None:
        # USA Disc 1 has 4152 entries. Disc 2 has 4147 and maps the canonical
        # namespace through Xenoiso's fixed five-entry offset.
        self.assertEqual(rico.CHAPTER_TWO_BEDROOM_FIELD, 379)
        self.assertEqual(rico.UNIFIED_DISC2_CHAPTER_TWO_BEDROOM_FIELD, 67)
        bedroom_fields = {
            1: rico.CHAPTER_TWO_BEDROOM_FIELD,
            2: rico.UNIFIED_DISC2_CHAPTER_TWO_BEDROOM_FIELD,
        }
        for disc in (1, 2):
            fields = (
                rico.HUB_FIELDS[disc],
                rico.CHAPTER_ONE_FIREWOOD_FIELD,
                rico.CHAPTER_ONE_AFTERMATH_FIELD,
                rico.CHAPTER_ONE_FUNERAL_FIELD,
                bedroom_fields[disc],
                *rico.CHAPTER_FIELDS[disc].values(),
            )
            canonical_ids = {
                canonical_id
                for field in fields
                for canonical_id in (
                    rico._field_bundle_id(field),
                    rico._field_bundle_id(field) + 1,
                )
            }
            with self.subTest(disc=disc):
                self.assertNotIn(
                    rico.HUB_FIELDS[disc],
                    rico.CHAPTER_FIELDS[disc].values(),
                )
                if disc == 1:
                    self.assertTrue(
                        all(0 <= canonical_id < 4152 for canonical_id in canonical_ids)
                    )
                else:
                    self.assertTrue(
                        all(0 <= canonical_id - 5 < 4147 for canonical_id in canonical_ids)
                    )

    def test_initial_state_installs_rico_party_levels_and_all_deathblows(self) -> None:
        staged = bytearray((index * 17 + 3) & 0xFF for index in range(rico.GAMESTATE_SIZE))
        for character in range(11):
            record = rico.PARTY_RECORD_BASE + character * rico.PARTY_RECORD_SIZE
            staged[record + balance.CHARACTER_ID_OFFSET] = character
            struct.pack_into("<H", staged, record + 0x4E, 1000 + character)
            struct.pack_into("<H", staged, record + 0x52, 100 + character)
        struct.pack_into("<H", staged, 0x1D30, 0)
        struct.pack_into("<H", staged, 0x1D32, 0xFFFF)
        staged_bytes = bytes(staged)

        with tempfile.TemporaryDirectory() as temporary:
            normalized = Path(temporary) / "2595.bin"
            normalized.write_bytes(staged_bytes)
            with (
                patch.object(rico, "NORMALIZED_GAMESTATE", normalized),
                patch.object(
                    rico,
                    "NORMALIZED_GAMESTATE_SHA256",
                    hashlib.sha256(staged_bytes).hexdigest(),
                ),
            ):
                result = rico._build_initial_gamestate(bytes(rico.GAMESTATE_SIZE))

        self.assertEqual(result[0x1D34:0x1D37], bytes((5, 0, 3)))
        self.assertEqual(result[0x22B1:0x22B4], bytes(3))
        self.assertEqual(struct.unpack_from("<H", result, 0x1D1C)[0], 0)
        self.assertEqual(struct.unpack_from("<H", result, 0x1D1E)[0], 0)
        membership = struct.unpack_from("<H", result, 0x1D30)[0]
        self.assertEqual(
            membership,
            sum(1 << character for character in (0, 2, 3, 5, 10)),
        )
        for character in (0, 2, 3, 5, 10):
            self.assertTrue(
                membership & (1 << character),
                f"Initial membership omitted character {character}",
            )
        frame_mask = struct.unpack_from("<H", result, 0x1D32)[0]
        self.assertEqual(
            frame_mask,
            sum(1 << character for character in (0, 3, 5)),
        )
        self.assertTrue(membership & (1 << 2))
        self.assertFalse(frame_mask & (1 << 2))
        self.assertEqual(struct.unpack_from("<H", result, 0x231A)[0], rico.TITLE_FIELD_ID)
        for character in range(11):
            record = rico.PARTY_RECORD_BASE + character * rico.PARTY_RECORD_SIZE
            level = 1 if character == 10 else recruitment.level if character == 5 else 70
            expected_level = bytes((level, level))
            self.assertEqual(result[record + 0x62 : record + 0x64], expected_level)
            self.assertEqual(result[record + 0x4C : record + 0x4E], result[record + 0x4E : record + 0x50])
            self.assertEqual(result[record + 0x50 : record + 0x52], result[record + 0x52 : record + 0x54])
            expected_weight = (
                balance.YOUNG_RICO_WEIGHT
                if character == 10
                else (
                    balance.WEIGHT_PROFILES[character].minimum_native,
                    balance.WEIGHT_PROFILES[character].initial_mutable,
                    0,
                )
            )
            self.assertEqual(
                result[
                    record + balance.WEIGHT_FIXED_OFFSET:
                    record + balance.WEIGHT_TENTHS_OFFSET + 1
                ],
                bytes(expected_weight),
            )
        for profile in DEATHBLOW_PROFILES:
            if profile.full_mask and profile.character_id not in (balance.YOUNG_RICO_ID, balance.RICO_ID):
                self.assertEqual(
                    learned_mask(result, profile.character_id) & profile.full_mask,
                    profile.full_mask,
                )
        rico_record = (
            rico.PARTY_RECORD_BASE + balance.RICO_ID * rico.PARTY_RECORD_SIZE
        )
        self.assertEqual(result[rico_record + balance.ATTACK_OFFSET], recruitment.stats[0])
        self.assertEqual(result[rico_record + balance.DEFENSE_OFFSET], recruitment.stats[1])
        self.assertEqual(
            tuple(
                result[
                    rico_record + balance.FIRST_ACCESSORY_OFFSET :
                    rico_record + balance.FIRST_ACCESSORY_OFFSET + 3
                ]
            ),
            balance.RICO_ACCESSORIES,
        )
        self.assertEqual(
            struct.unpack_from("<HHH", result, balance.RICO_ABILITY_RECORD),
            (recruitment.on_foot_deathblows, recruitment.spirit_commands, recruitment.stier_deathblows),
        )
        child_record = (
            rico.PARTY_RECORD_BASE
            + balance.YOUNG_RICO_ID * rico.PARTY_RECORD_SIZE
        )
        self.assertEqual(
            result[
                balance.YOUNG_RICO_NAME_OFFSET:
                balance.YOUNG_RICO_NAME_OFFSET + len(balance.YOUNG_RICO_NAME_CELL)
            ],
            balance.YOUNG_RICO_NAME_CELL,
        )
        self.assertEqual(
            tuple(
                result[
                    child_record + balance.FIRST_ACCESSORY_OFFSET:
                    child_record + balance.FIRST_ACCESSORY_OFFSET + 3
                ]
            ),
            balance.YOUNG_RICO_ACCESSORIES,
        )
        self.assertEqual(result[child_record + 0xA0], 0xFF)
        self.assertEqual(result[0x1800:0x1820], bytes(0x20))


class RicoPlayableFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.chapters = rico.load_chapters()
        cls.sources: dict[int, bytes] = {}
        cls.outputs: dict[int, bytes] = {}
        missing: list[Path] = []
        for chapter in cls.chapters:
            canonical_id = rico._field_bundle_id(chapter.donor_field)
            path = RICO_AUDIT_ROOT / f"{canonical_id}.bin"
            if not path.is_file():
                missing.append(path)
                continue
            source = path.read_bytes()
            cls.sources[chapter.chapter_id] = source
            cls.outputs[chapter.chapter_id] = rico._build_playable_chapter_bundle(
                source,
                chapter,
                rico.HUB_FIELDS[1],
                (
                    cls.chapters[chapter.chapter_id]
                    if chapter.chapter_id < 7
                    else None
                ),
            )
        if missing:
            raise AssertionError(
                "Rico donor audit is incomplete: "
                + ", ".join(str(path) for path in missing)
            )

    @staticmethod
    def _layout(chapter: rico.Chapter, source: bytes, output: bytes):
        source_field = parse_field(source)
        output_field = parse_field(output)
        source_editor = AtelScript(
            rico._normalize_playable_party_script(
                chapter,
                source_field.parts[rico.SCRIPT_INDEX].data,
            )
        )
        output_editor = AtelScript(output_field.parts[rico.SCRIPT_INDEX].data)
        missing_characters = rico._missing_playable_characters(chapter, source_editor)
        contract = rico._playable_chapter_contract(chapter.chapter_id)
        first_controller = source_editor.entity_count + len(missing_characters)
        exit_entity = first_controller + len(contract.interactions)
        return (
            source_field,
            output_field,
            source_editor,
            output_editor,
            contract,
            first_controller,
            exit_entity,
        )

    def test_authentic_donors_replace_the_screenplay_room_mismatches(self) -> None:
        self.assertEqual(self.chapters[0].donor_field, 229)
        retail_room = parse_field(self.sources[1])
        retail_editor = AtelScript(
            retail_room.parts[rico.SCRIPT_INDEX].data
        )
        retail_director_pc = retail_editor.get_script_pointer(0, 0)
        self.assertEqual(
            retail_editor.bytecode[
                retail_director_pc : retail_director_pc + 6
            ],
            b"\xBC" + rico._play_music(rico.CHAPTER_ONE_MUSIC_ID) + b"\x2A\x00",
        )
        self.assertEqual(self.chapters[1].donor_field, 218)
        self.assertEqual(rico.CHAPTER_TWO_BEDROOM_DONOR_FIELD, 219)
        self.assertEqual(rico._field_bundle_id(219), 1044)
        self.assertEqual(self.chapters[2].donor_field, 236)
        self.assertEqual(self.chapters[3].donor_field, 237)
        self.assertEqual(self.chapters[4].donor_field, 235)
        self.assertEqual(self.chapters[5].donor_field, 232)
        self.assertEqual(self.chapters[6].donor_field, 298)
        self.assertEqual(
            self.chapters[2].blocks[-1],
            "CHAPTER 3 COMPLETE<Close>",
        )

    def test_entry_is_silent_after_prelaunch_exposition(self) -> None:
        for chapter in self.chapters:
            with self.subTest(chapter=chapter.chapter_id):
                (
                    _source_field,
                    _output_field,
                    _source_editor,
                    output_editor,
                    contract,
                    _first_controller,
                    _exit_entity,
                ) = self._layout(
                    chapter,
                    self.sources[chapter.chapter_id],
                    self.outputs[chapter.chapter_id],
                )
                intro_pc = output_editor.get_script_pointer(0, 1)
                stop_pc = output_editor.get_script_pointer(0, 2)
                expected = rico._playable_silent_update()

                self.assertNotEqual(intro_pc, stop_pc)
                self.assertEqual(
                    output_editor.bytecode[intro_pc : intro_pc + len(expected)],
                    expected,
                )
                self.assertEqual(expected, b"\x5B")

                director_pc = output_editor.get_script_pointer(0, 0)
                expected_director = (
                    rico._chapter_two_director(chapter.music)
                    if chapter.chapter_id == 2
                    else rico._sanitized_director(chapter.music)
                )
                self.assertEqual(
                    output_editor.bytecode[
                        director_pc : director_pc + len(expected_director)
                    ],
                    expected_director,
                )

                custom_text = "\n".join(rico._playable_custom_texts(contract))
                self.assertNotIn("OBJECTIVE\n", custom_text)
                self.assertNotIn("Check the window, then speak with Mom", custom_text)
                self.assertEqual(
                    rico._chapter_selection_exposition(chapter),
                    (chapter.blocks[0], chapter.selection_exposition),
                )

    def test_native_dialogue_payload_and_ids_survive_the_append(self) -> None:
        for chapter in self.chapters:
            with self.subTest(chapter=chapter.chapter_id):
                source = parse_field(self.sources[chapter.chapter_id]).parts[
                    rico.DIALOGUE_INDEX
                ].data
                output = parse_field(self.outputs[chapter.chapter_id]).parts[
                    rico.DIALOGUE_INDEX
                ].data
                old_count = struct.unpack_from("<I", source, 0)[0] + 1
                new_count = struct.unpack_from("<I", output, 0)[0] + 1
                old_header = 4 + old_count * 4
                new_header = 4 + new_count * 4
                old_payload = source[old_header:]
                self.assertEqual(
                    output[new_header : new_header + len(old_payload)],
                    old_payload,
                )
                shift = new_header - old_header
                for block_id in range(old_count):
                    before = struct.unpack_from("<H", source, 4 + block_id * 2)[0]
                    after = struct.unpack_from("<H", output, 4 + block_id * 2)[0]
                    self.assertEqual(after, before + shift)

    def test_every_objective_is_a_facing_gated_cross_controller(self) -> None:
        for chapter in self.chapters:
            (
                _source_field,
                _output_field,
                source_editor,
                output_editor,
                contract,
                first_controller,
                exit_entity,
            ) = self._layout(
                chapter,
                self.sources[chapter.chapter_id],
                self.outputs[chapter.chapter_id],
            )
            expected_count = (
                source_editor.entity_count
                + len(rico._missing_playable_characters(chapter, source_editor))
                + len(contract.interactions)
                + 1
            )
            self.assertEqual(output_editor.entity_count, expected_count)
            for index, interaction in enumerate(contract.interactions):
                with self.subTest(chapter=chapter.chapter_id, node=interaction.name):
                    entity = first_controller + index
                    hammer_arrival_gate = (
                        chapter.chapter_id == 2
                        and interaction.name == "Hammer"
                    )
                    init_pc = output_editor.get_script_pointer(entity, 0)
                    expected_init = rico._playable_controller_init(
                        interaction.x,
                        interaction.z,
                        half_width=interaction.interaction_half_width,
                        half_depth=interaction.interaction_half_depth,
                        requires_facing=interaction.requires_facing,
                        initially_disabled=(
                            bool(interaction.activation_required_bits)
                            or hammer_arrival_gate
                        ),
                    )
                    init = output_editor.bytecode[
                        init_pc : init_pc + len(expected_init)
                    ]
                    self.assertEqual(init, expected_init)
                    self.assertTrue(init.startswith(b"\xBC\x19"))
                    self.assertNotIn(b"\x0B\x00\x80", init)
                    self.assertIn(
                        (
                            b"\xF8\x03\x04\x00"
                            if interaction.requires_facing
                            else b"\xF8\x07\x04\x00"
                        ),
                        init,
                    )
                    self.assertIn(b"\x20\x01\x80\x23", init)
                    self.assertTrue(init.endswith(b"\x23\x00"))
                    if interaction.activation_required_bits or hammer_arrival_gate:
                        self.assertIn(
                            b"\x19"
                            + rico._s16(rico.PLAYABLE_CONTROLLER_PARK_POSITION[0])
                            + rico._s16(rico.PLAYABLE_CONTROLLER_PARK_POSITION[1])
                            + b"\xC0",
                            init,
                        )
                        self.assertNotIn(b"\x2A", init)
                        gate_pc = output_editor.get_script_pointer(entity, 1)
                        gate = (
                            rico._chapter_two_hammer_controller_gate(
                                gate_pc,
                                interaction.x,
                                interaction.z,
                            )
                            if hammer_arrival_gate
                            else rico._playable_controller_activation_gate(
                                gate_pc,
                                interaction.activation_required_bits,
                                interaction.x,
                                interaction.z,
                            )
                        )
                        self.assertEqual(
                            output_editor.bytecode[gate_pc : gate_pc + len(gate)],
                            gate,
                        )
                    action_pc = output_editor.get_script_pointer(entity, 2)
                    self.assertGreater(action_pc, init_pc)
                    self.assertEqual(
                        output_editor.get_script_pointer(entity, 3),
                        output_editor.get_script_pointer(0, 2),
                    )
            self.assertEqual(exit_entity, output_editor.entity_count - 1)

    def test_stage_choice_contract_validation_is_one_based_and_layout_safe(self) -> None:
        chapter = self.chapters[1]
        contract = rico._playable_chapter_contract(chapter.chapter_id)
        interaction_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "arena passage"
        )
        interaction = contract.interactions[interaction_index]
        stage_index = next(
            index
            for index, stage in enumerate(interaction.stages)
            if stage.bit == 3
        )
        source_stage = interaction.stages[stage_index]
        components = [
            part.data for part in parse_field(self.outputs[chapter.chapter_id]).parts
        ]
        choice = (
            "<Opcode:01:FF>Enter the arena?\n"
            "     Not yet\n"
            "     Enter<Close>"
        )

        def with_stage(stage: rico.PlayableStage) -> rico.PlayableChapter:
            interactions = list(contract.interactions)
            stages = list(interaction.stages)
            stages[stage_index] = stage
            interactions[interaction_index] = replace(
                interaction,
                stages=tuple(stages),
            )
            return replace(contract, interactions=tuple(interactions))

        valid = with_stage(
            replace(
                source_stage,
                choice_text=choice,
                accepted_selection=2,
                rejection_dialogue=("<Rico>\nNot yet.<Close>",),
            )
        )
        rico._validate_playable_contract(components, chapter, valid)

        with self.assertRaisesRegex(rico.RicoArcBuildError, "valid rows are 1..2"):
            rico._validate_playable_contract(
                components,
                chapter,
                with_stage(
                    replace(
                        source_stage,
                        choice_text=choice,
                        accepted_selection=3,
                    )
                ),
            )
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            "configures a choice result without choice text",
        ):
            rico._validate_playable_contract(
                components,
                chapter,
                with_stage(
                    replace(
                        source_stage,
                        choice_text=None,
                        accepted_selection=1,
                        rejection_dialogue=("<Rico>\nNot yet.<Close>",),
                    )
                ),
            )
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            "Choice row exceeds the native dialogue width",
        ):
            rico._validate_playable_contract(
                components,
                chapter,
                with_stage(
                    replace(
                        source_stage,
                        choice_text=(
                            "<Opcode:01:FF>Enter the arena?\n"
                            "     Not yet\n"
                            "     This choice row is intentionally far too "
                            "wide for the native dialogue window<Close>"
                        ),
                    )
                ),
            )

    def test_battles_are_real_fixed_encounters_and_commit_victory_first(self) -> None:
        expected_counts = {1: 0, 2: 1, 3: 0, 4: 0, 5: 1, 6: 1, 7: 0}
        for chapter in self.chapters:
            (
                _source_field,
                _output_field,
                _source_editor,
                output_editor,
                contract,
                first_controller,
                exit_entity,
            ) = self._layout(
                chapter,
                self.sources[chapter.chapter_id],
                self.outputs[chapter.chapter_id],
            )
            found = 0
            for index, interaction in enumerate(contract.interactions):
                entity = first_controller + index
                action_pc = output_editor.get_script_pointer(entity, 2)
                next_entity = entity + 1
                action_end = output_editor.get_script_pointer(next_entity, 0)
                action = output_editor.bytecode[action_pc:action_end]
                for stage in interaction.stages:
                    if stage.battle_configuration is None:
                        continue
                    found += 1
                    fixed = rico.mass_driver._fixed_battle(
                        stage.battle_configuration
                    )
                    self.assertIn(fixed, action)
                    battle_end = action.index(b"\xFE\x7F", action.index(fixed))
                    progress = rico.mass_driver._set_var_bit(
                        rico.PLAYABLE_STATE_VARIABLE,
                        stage.bit,
                    )
                    self.assertEqual(
                        action[battle_end + 2 : battle_end + 2 + len(progress)],
                        progress,
                    )
                    if stage.gear_battle:
                        self.assertIn(b"\xFE\xA1", action[: action.index(fixed)])
                        self.assertIn(b"\xFE\x41", action[: action.index(fixed)])
                        self.assertIn(b"\xFE\x42", action[action.index(fixed) :])
            self.assertEqual(found, expected_counts[chapter.chapter_id])
            exit_pc = output_editor.get_script_pointer(exit_entity, 2)
            exit_action = output_editor.bytecode[exit_pc:]
            if chapter.chapter_id == 1:
                self.assertIn(
                    rico._change_field(rico.CHAPTER_ONE_FIREWOOD_FIELD, 0),
                    exit_action,
                )
                self.assertNotIn(
                    rico._change_field(rico.HUB_FIELDS[1], 0),
                    exit_action,
                )
                continue
            self.assertIn(
                rico._change_field(rico.HUB_FIELDS[1], 0),
                exit_action,
            )
            self.assertIn(rico._choice_dialog(
                (
                    struct.unpack_from(
                        "<I",
                        parse_field(self.sources[chapter.chapter_id]).parts[
                            rico.DIALOGUE_INDEX
                        ].data,
                        0,
                    )[0]
                    + 1
                    + len(chapter.blocks)
                    + rico._playable_custom_texts(contract).index(
                        rico.PLAYABLE_FINAL_HUB_CHOICE
                        if chapter.chapter_id == 7
                        else rico.PLAYABLE_NEXT_OR_HUB_CHOICE
                    )
                )
            ), exit_action)

    def test_chapters_two_through_seven_have_ordered_playable_objective_dags(self) -> None:
        expected = {
            2: {
                1: set(),
                2: {1},
                3: {2},
                4: {1, 3},
                5: {1, 2, 4},
                6: {3, 5},
                7: set(),
            },
            3: {
                1: set(),
                2: {1},
                3: {1},
                4: {1, 2, 3},
                5: {4},
            },
            4: {
                1: set(),
                2: {1},
                3: {2},
                4: {1, 2, 3},
                5: {1, 2, 3, 4},
                6: {1, 2, 3, 4, 5},
                7: {1, 2, 3, 4, 5, 6},
                8: {1, 2, 3, 4, 5, 6, 7},
                11: {8},
                12: {11},
                13: {11, 12},
            },
            5: {
                1: set(),
                2: {1},
                3: {2},
                4: {3},
                5: {4},
                6: {1, 5},
            },
            6: {
                1: set(),
                2: {1},
                3: {2},
                4: {3},
                5: {4},
                6: {5},
            },
            7: {
                1: set(),
                2: {1},
                3: {2},
                4: {3},
                5: {4},
                6: {5},
                9: {6},
            },
        }
        expected_optional = {2: {7}}

        for chapter_id, expected_requirements in expected.items():
            contract = rico._playable_chapter_contract(chapter_id)
            effective: dict[int, set[int]] = {}
            for interaction in contract.interactions:
                prior: set[int] = set()
                for stage in interaction.stages:
                    effective[stage.bit] = (
                        set(stage.required_bits)
                        | set(interaction.activation_required_bits)
                        | prior
                    )
                    prior.add(stage.bit)
            self.assertEqual(effective, expected_requirements)
            self.assertEqual(
                set(contract.required_bits),
                set(expected_requirements)
                - expected_optional.get(chapter_id, set()),
            )
            self.assertEqual(
                set(contract.optional_bits),
                expected_optional.get(chapter_id, set()),
            )

    def test_every_chapter_completes_only_at_the_physical_exit(self) -> None:
        for chapter in self.chapters:
            with self.subTest(chapter=chapter.chapter_id):
                (
                    source_field,
                    _output_field,
                    _source_editor,
                    output_editor,
                    contract,
                    first_controller,
                    exit_entity,
                ) = self._layout(
                    chapter,
                    self.sources[chapter.chapter_id],
                    self.outputs[chapter.chapter_id],
                )
                self.assertTrue(contract.completion_at_exit)
                self.assertFalse(
                    any(
                        stage.completes_chapter
                        for interaction in contract.interactions
                        for stage in interaction.stages
                    )
                )
                authored_base = (
                    struct.unpack_from(
                        "<I",
                        source_field.parts[rico.DIALOGUE_INDEX].data,
                        0,
                    )[0]
                    + 1
                )
                completion_text = (
                    rico.PLAYABLE_FINAL_HUB_CHOICE
                    if chapter.chapter_id == 7
                    else rico.PLAYABLE_NEXT_OR_HUB_CHOICE
                )
                custom_texts = rico._playable_custom_texts(contract)
                completion_id = (
                    authored_base
                    + len(chapter.blocks)
                    + custom_texts.index(completion_text)
                )
                completion_prompt = rico._choice_dialog(completion_id)

                for index, _interaction in enumerate(contract.interactions):
                    entity = first_controller + index
                    action_pc = output_editor.get_script_pointer(entity, 2)
                    action_end = output_editor.get_script_pointer(entity + 1, 0)
                    self.assertNotIn(
                        completion_prompt,
                        output_editor.bytecode[action_pc:action_end],
                    )

                exit_pc = output_editor.get_script_pointer(exit_entity, 2)
                exit_action = output_editor.bytecode[exit_pc:]
                if contract.exit_transition is not None:
                    self.assertEqual(chapter.chapter_id, 1)
                    self.assertNotIn(completion_prompt, exit_action)
                    self.assertIn(
                        rico._change_field(
                            rico.CHAPTER_ONE_FIREWOOD_FIELD,
                            0,
                        ),
                        exit_action,
                    )
                else:
                    self.assertIn(completion_prompt, exit_action)

    def test_exit_completion_cannot_omit_any_playable_objective_bit(self) -> None:
        chapter = self.chapters[1]
        contract = rico._playable_chapter_contract(chapter.chapter_id)
        self.assertTrue(contract.completion_at_exit)
        incomplete = replace(
            contract,
            required_bits=contract.required_bits[1:],
            exit_locked_steps=contract.exit_locked_steps[1:],
        )
        components = [
            part.data
            for part in parse_field(self.outputs[chapter.chapter_id]).parts
        ]
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            "exit completion can bypass playable objective bits",
        ):
            rico._validate_playable_contract(
                components,
                chapter,
                incomplete,
            )

    def test_solo_gear_battle_changes_only_the_frame_mask_and_restores_it(self) -> None:
        chapter_party = rico.CHAPTER_PARTIES[2]
        self.assertEqual(chapter_party, (5, 0))
        before, after = rico._gear_battle_stage(
            solo_rico=True,
            chapter_party=chapter_party,
        )

        clear_every_frame = b"".join(
            b"\xFE\x3B" + rico._immediate(character)
            for character in range(11)
        )
        rico_only = b"\xFE\x3A" + rico._immediate(5)
        expected_before = (
            clear_every_frame
            + rico_only
            + b"\xFE\xA1"
            + rico._immediate(5)
            + rico._immediate(6)
            + b"\xFE\x41"
            + rico._immediate(0)
        )
        restore_chapter_mask = clear_every_frame + b"".join(
            b"\xFE\x3A" + rico._immediate(character)
            for character in chapter_party
        )
        expected_after = (
            b"\xFE\x42"
            + rico._immediate(0)
            + restore_chapter_mask
        )
        self.assertEqual(before, expected_before)
        self.assertEqual(after, expected_after)

        # Field-party membership must survive the solo formation. These are
        # frame-mask streams only, never FE18/FE19 party mutation streams.
        for opcode in (b"\xFE\x18", b"\xFE\x19", b"\xFE\x1A"):
            self.assertNotIn(opcode, before)
            self.assertNotIn(opcode, after)

        chapter = self.chapters[1]
        (
            _source_field,
            _output_field,
            _source_editor,
            output_editor,
            contract,
            first_controller,
            exit_entity,
        ) = self._layout(
            chapter,
            self.sources[chapter.chapter_id],
            self.outputs[chapter.chapter_id],
        )
        interaction_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "arena passage"
        )
        interaction = contract.interactions[interaction_index]
        stage = next(
            stage
            for stage in interaction.stages
            if stage.battle_configuration is not None
        )
        self.assertTrue(stage.solo_rico)
        action_pc = output_editor.get_script_pointer(
            first_controller + interaction_index,
            2,
        )
        action_end = output_editor.get_script_pointer(
            first_controller + interaction_index + 1,
            0,
        )
        action = output_editor.bytecode[action_pc:action_end]
        fixed_battle = rico.mass_driver._fixed_battle(stage.battle_configuration)
        progress = rico.mass_driver._set_var_bit(
            rico.PLAYABLE_STATE_VARIABLE,
            stage.bit,
        )
        self.assertIn(
            before
            + rico._wait(15)
            + rico._play_music(rico.PLAYABLE_BATTLE_MUSIC)
            + fixed_battle,
            action,
        )
        self.assertIn(
            fixed_battle
            + b"\xFE\x7F"
            + progress
            + after
            + rico._play_music(chapter.music),
            action,
        )

    def test_party_scale_gear_battles_do_not_mutate_party_or_frame_mask(self) -> None:
        before, after = rico._gear_battle_stage(
            solo_rico=False,
            chapter_party=rico.CHAPTER_PARTIES[5],
        )
        for opcode in (
            b"\xFE\x18",
            b"\xFE\x19",
            b"\xFE\x1A",
            b"\xFE\x3A",
            b"\xFE\x3B",
        ):
            self.assertNotIn(opcode, before)
            self.assertNotIn(opcode, after)
        self.assertEqual(before.count(b"\xFE\xA1"), 3)
        self.assertEqual(before.count(b"\xFE\x41"), 3)
        self.assertEqual(after.count(b"\xFE\x42"), 3)

    def test_fixed_encounters_disable_random_battles_and_escape(self) -> None:
        expected_configurations = {
            1: {},
            2: {6: True},
            3: {},
            4: {},
            5: {15: True},
            6: {6: True},
            7: {},
        }
        for chapter in self.chapters:
            with self.subTest(chapter=chapter.chapter_id):
                output_field = parse_field(self.outputs[chapter.chapter_id])
                encounter_data = output_field.parts[6].data
                configurations = rico._battle_configurations(
                    rico._playable_chapter_contract(chapter.chapter_id)
                )

                self.assertEqual(
                    configurations,
                    expected_configurations[chapter.chapter_id],
                )
                if not encounter_data:
                    self.assertEqual(configurations, {})
                    continue
                encounters = rico.EncounterTable(encounter_data)
                self.assertEqual(
                    encounters.weights,
                    (0,) * rico.FORMATION_COUNT,
                )
                for configuration, gear_battle in configurations.items():
                    formation = encounters.formation(configuration)
                    self.assertTrue(
                        formation[1] & 0x80,
                        f"Chapter {chapter.chapter_id} formation "
                        f"{configuration} still permits Escape",
                    )
                    active = tuple(
                        encounters.get_enemy(configuration, slot)
                        for slot in range(8)
                        if encounters.get_enemy(configuration, slot).enemy_id
                        != rico.EMPTY_ENEMY_ID
                    )
                    self.assertTrue(active)
                    self.assertTrue(
                        all(enemy.is_gear == gear_battle for enemy in active)
                    )
                    if chapter.chapter_id == 5:
                        self.assertEqual(configuration, 15)
                        self.assertEqual(len(active), 1)
                        self.assertTrue(active[0].is_gear)

    def test_variable_party_donors_use_selectors_without_duplicate_carriers(self) -> None:
        variable_chapters = {
            chapter.donor_field: chapter
            for chapter in self.chapters
            if chapter.donor_field in rico.VARIABLE_PARTY_DONORS
        }
        self.assertEqual(set(variable_chapters), {232, 235})

        for donor_field, chapter in variable_chapters.items():
            with self.subTest(chapter=chapter.chapter_id, donor=donor_field):
                source_field = parse_field(self.sources[chapter.chapter_id])
                raw_editor = AtelScript(
                    source_field.parts[rico.SCRIPT_INDEX].data
                )
                (
                    source_field,
                    _output_field,
                    normalized_editor,
                    output_editor,
                    contract,
                    first_controller,
                    _exit_entity,
                ) = self._layout(
                    chapter,
                    self.sources[chapter.chapter_id],
                    self.outputs[chapter.chapter_id],
                )
                pcs, source_operands = rico.VARIABLE_PARTY_DONORS[donor_field]

                self.assertEqual(
                    rico._missing_playable_characters(chapter, normalized_editor),
                    (),
                )
                self.assertEqual(first_controller, raw_editor.entity_count)
                self.assertEqual(
                    output_editor.entity_count,
                    raw_editor.entity_count + len(contract.interactions) + 1,
                )
                for pc, source_operand, selector in zip(
                    pcs,
                    source_operands,
                    (0xFD, 0xFE, 0xFF),
                    strict=True,
                ):
                    source_registration = (
                        b"\x16"
                        + struct.pack("<H", source_operand)
                        + b"\xFE\x0D"
                        + struct.pack("<H", source_operand)
                    )
                    selector_registration = (
                        b"\x16"
                        + rico._immediate(selector)
                        + b"\xFE\x0D"
                        + rico._immediate(selector)
                    )
                    self.assertEqual(
                        raw_editor.bytecode[pc : pc + len(source_registration)],
                        source_registration,
                    )
                    self.assertEqual(
                        normalized_editor.bytecode[
                            pc : pc + len(selector_registration)
                        ],
                        selector_registration,
                    )
                    self.assertEqual(
                        output_editor.bytecode[
                            pc : pc + len(selector_registration)
                        ],
                        selector_registration,
                    )

    def test_old_donor_scripts_are_reduced_to_the_explicit_allowlist(self) -> None:
        for chapter in self.chapters:
            with self.subTest(chapter=chapter.chapter_id):
                (
                    source_field,
                    _output_field,
                    source_editor,
                    output_editor,
                    contract,
                    first_controller,
                    _exit_entity,
                ) = self._layout(
                    chapter,
                    self.sources[chapter.chapter_id],
                    self.outputs[chapter.chapter_id],
                )
                stop_pc = output_editor.get_script_pointer(0, 2)
                native_party_entities = rico._playable_native_party_entities(
                    chapter,
                    source_editor,
                )
                party_entities = set(native_party_entities)
                party_entities.update(
                    range(source_editor.entity_count, first_controller)
                )
                registered = rico._registered_character_entities(source_editor)
                missing = rico._missing_playable_characters(chapter, source_editor)
                if chapter.donor_field in rico.VARIABLE_PARTY_DONORS:
                    leader_entity = 1
                    party_selectors = {1: 0xFD, 2: 0xFE, 3: 0xFF}
                else:
                    leader_character = rico.CHAPTER_PARTIES[chapter.chapter_id][0]
                    leader_entity = registered.get(leader_character)
                    if leader_entity is None:
                        leader_entity = (
                            source_editor.entity_count
                            + missing.index(leader_character)
                        )
                    party_selectors = {
                        entity: character
                        for character, entity in registered.items()
                    }
                for character in missing:
                    entity = source_editor.entity_count + missing.index(character)
                    party_selectors[entity] = character
                staged_entities = set()
                for character in rico.STAGED_PARTY_ACTORS.get(
                    chapter.chapter_id,
                    {},
                ):
                    entity = registered.get(character)
                    if entity is None:
                        entity = source_editor.entity_count + missing.index(character)
                    staged_entities.add(entity)
                interaction_actions: dict[int, int] = {}
                actor_action_gates: dict[int, tuple[tuple[int, ...], int]] = {}
                hammer_action_gates: dict[int, int] = {}
                actor_arrival_bits: dict[int, tuple[int, ...]] = {}
                actor_bindings = rico.INTERACTION_ACTOR_BINDINGS.get(
                    chapter.chapter_id,
                    {},
                )
                bound_actor_entities = {
                    entity
                    for entities in actor_bindings.values()
                    for entity in entities
                }
                silent_ambient_entities = (
                    {rico.CHAPTER_TWO_MAIN_DOOR_ENTITY}
                    if chapter.chapter_id == 2
                    else set()
                )
                for index, interaction in enumerate(contract.interactions):
                    action_pc = output_editor.get_script_pointer(
                        first_controller + index,
                        2,
                    )
                    for entity in actor_bindings.get(interaction.name, ()):
                        self.assertNotIn(entity, interaction_actions)
                        if (
                            chapter.chapter_id == 2
                            and interaction.name == "Hammer"
                            and entity == rico.CHAPTER_TWO_HAMMER_ENTITY
                        ):
                            hammer_action_gates[entity] = action_pc
                        elif interaction.hide_bound_actors_until_active:
                            actor_arrival_bits[entity] = (
                                interaction.activation_required_bits
                            )
                            actor_action_gates[entity] = (
                                interaction.activation_required_bits,
                                action_pc,
                            )
                        else:
                            interaction_actions[entity] = action_pc
                hidden_entities = {
                    entity
                    for interaction in contract.interactions
                    for stage in interaction.stages
                    for entity in stage.hide_entities_after
                }
                hazardous_entities = set(
                    rico.HAZARDOUS_DONOR_INIT_ENTITIES.get(
                        chapter.donor_field,
                        (),
                    )
                )
                disabled_ambient_entities = (
                    set(range(1, source_editor.entity_count))
                    - set(native_party_entities)
                    - bound_actor_entities
                    - silent_ambient_entities
                )
                self.assertTrue(disabled_ambient_entities)
                disable_dialogue_pointers = {
                    output_editor.get_script_pointer(entity, 1)
                    for entity in disabled_ambient_entities
                }
                self.assertEqual(len(disable_dialogue_pointers), 1)
                disable_dialogue_pc = next(iter(disable_dialogue_pointers))
                self.assertEqual(
                    output_editor.bytecode[
                        disable_dialogue_pc : disable_dialogue_pc
                        + len(rico.DISABLE_DIALOGUE_UPDATE)
                    ],
                    rico.DISABLE_DIALOGUE_UPDATE,
                )
                regular_update_entities = party_entities - staged_entities
                if chapter.chapter_id == 1:
                    regular_update_entities.discard(leader_entity)
                party_update_pointers = {
                    output_editor.get_script_pointer(entity, 1)
                    for entity in regular_update_entities
                }

                self.assertEqual(
                    output_editor.bytecode[stop_pc : stop_pc + 1],
                    b"\x00",
                )
                self.assertEqual(len(party_update_pointers), 1)
                party_update_pc = next(iter(party_update_pointers))
                self.assertEqual(
                    output_editor.bytecode[party_update_pc : party_update_pc + 2],
                    b"\xA7\x00",
                )
                young_rico_update_pc = None
                if chapter.chapter_id == 1:
                    young_rico_update_pc = output_editor.get_script_pointer(
                        leader_entity,
                        1,
                    )
                    self.assertNotEqual(young_rico_update_pc, party_update_pc)
                    self.assertEqual(
                        output_editor.bytecode[
                            young_rico_update_pc : young_rico_update_pc
                            + len(rico.YOUNG_RICO_PARTY_UPDATE)
                        ],
                        rico.YOUNG_RICO_PARTY_UPDATE,
                    )
                director_pc = output_editor.get_script_pointer(0, 0)
                director = (
                    rico._chapter_two_director(chapter.music)
                    if chapter.chapter_id == 2
                    else rico._sanitized_director(chapter.music)
                )
                if chapter.chapter_id == 2:
                    self.assertEqual(
                        director,
                        b"\xBC\x23\x2A"
                        + rico._restore_chapter_two_state()
                        + rico._play_music(chapter.music)
                        + b"\x00",
                    )
                else:
                    self.assertEqual(
                        director,
                        b"\xBC\x23\x2A"
                        + rico._play_music(chapter.music)
                        + b"\x00",
                    )
                self.assertEqual(
                    output_editor.bytecode[
                        director_pc : director_pc + len(director)
                    ],
                    director,
                )
                silent_pc = output_editor.get_script_pointer(0, 1)
                silent_update = rico._playable_silent_update()
                self.assertNotEqual(silent_pc, stop_pc)
                self.assertEqual(
                    output_editor.bytecode[
                        silent_pc : silent_pc + len(silent_update)
                    ],
                    silent_update,
                )
                private_helpers: dict[tuple[int, int], bytes] = {}
                if chapter.chapter_id == 1:
                    private_helpers[
                        (
                            rico.CHAPTER_ONE_ANNA_ENTITY,
                            rico.CHAPTER_ONE_ANNA_INTERACTION_COUGH_SCRIPT,
                        )
                    ] = rico.CHAPTER_ONE_ANNA_COUGH_ONCE + b"\x00"
                    private_helpers[
                        (
                            rico.CHAPTER_ONE_DOOR_ENTITY,
                            rico.CHAPTER_ONE_DOOR_OPEN_SCRIPT,
                        )
                    ] = rico.CHAPTER_ONE_DOOR_OPEN_BODY
                    private_helpers[
                        (
                            leader_entity,
                            rico.CHAPTER_ONE_DOOR_DEPARTURE_SCRIPT,
                        )
                    ] = rico._chapter_one_door_departure_body()
                if chapter.chapter_id == 2:
                    private_helpers[
                        (rico.CHAPTER_TWO_MAIN_DOOR_ENTITY, 2)
                    ] = rico._chapter_two_main_bedroom_action(
                        rico.CHAPTER_TWO_BEDROOM_FIELD
                    )
                if chapter.chapter_id == 4:
                    for entity in (
                        rico.CHAPTER_FOUR_FEI_ENTITY,
                        rico.CHAPTER_FOUR_BART_ENTITY,
                    ):
                        private_helpers[
                            (entity, rico.CHAPTER_FOUR_PRIVATE_STAGE_SCRIPT)
                        ] = rico._chapter_four_private_stage_body(entity)
                        private_helpers[
                            (entity, rico.CHAPTER_FOUR_PRIVATE_APPROACH_SCRIPT)
                        ] = rico._chapter_four_private_route_body(
                            rico.CHAPTER_FOUR_PRIVATE_APPROACH_ROUTES[entity],
                            hide_offstage=False,
                        )
                        private_helpers[
                            (entity, rico.CHAPTER_FOUR_PRIVATE_CROSS_SCRIPT)
                        ] = rico._chapter_four_private_route_body(
                            rico.CHAPTER_FOUR_PRIVATE_CROSS_ROUTES[entity],
                            hide_offstage=True,
                        )
                    private_helpers[
                        (
                            rico.CHAPTER_FOUR_DOOR_ENTITY,
                            rico.CHAPTER_FOUR_DOOR_OPEN_SCRIPT,
                        )
                    ] = rico.CHAPTER_FOUR_DOOR_OPEN_BODY
                    private_helpers[
                        (
                            rico.CHAPTER_FOUR_DOOR_ENTITY,
                            rico.CHAPTER_FOUR_DOOR_CLOSE_SCRIPT,
                        )
                    ] = rico.CHAPTER_FOUR_DOOR_CLOSE_BODY
                if chapter.chapter_id == 5:
                    private_helpers[
                        (
                            rico.CHAPTER_FIVE_DOOR_ENTITY,
                            rico.CHAPTER_FIVE_DOOR_OPEN_SCRIPT,
                        )
                    ] = rico.CHAPTER_FIVE_DOOR_OPEN_BODY
                    private_helpers[
                        (
                            rico.CHAPTER_FIVE_DOOR_ENTITY,
                            rico.CHAPTER_FIVE_DOOR_CLOSE_SCRIPT,
                        )
                    ] = rico.CHAPTER_FIVE_DOOR_CLOSE_BODY
                if chapter.chapter_id == 6:
                    private_helpers[
                        (
                            rico.CHAPTER_SIX_DOOR_ENTITY,
                            rico.CHAPTER_SIX_DOOR_OPEN_SCRIPT,
                        )
                    ] = rico.CHAPTER_SIX_DOOR_OPEN_BODY
                    private_helpers[
                        (
                            rico.CHAPTER_SIX_DOOR_ENTITY,
                            rico.CHAPTER_SIX_DOOR_CLOSE_SCRIPT,
                        )
                    ] = rico.CHAPTER_SIX_DOOR_CLOSE_BODY
                if chapter.chapter_id == 7:
                    private_helpers[
                        (
                            rico.CHAPTER_SEVEN_DOOR_ENTITY,
                            rico.CHAPTER_SEVEN_DOOR_OPEN_SCRIPT,
                        )
                    ] = rico.CHAPTER_SEVEN_DOOR_OPEN_BODY
                    private_helpers[
                        (
                            rico.CHAPTER_SEVEN_DOOR_ENTITY,
                            rico.CHAPTER_SEVEN_DOOR_CLOSE_SCRIPT,
                        )
                    ] = rico.CHAPTER_SEVEN_DOOR_CLOSE_BODY
                for entity in range(source_editor.entity_count):
                    for script_index in range(2, 32):
                        expected_pointer = stop_pc
                        if script_index == 2 and entity in hammer_action_gates:
                            expected_pointer = output_editor.get_script_pointer(
                                entity,
                                script_index,
                            )
                            expected_body = (
                                rico._chapter_two_hammer_actor_action_gate(
                                    expected_pointer,
                                    hammer_action_gates[entity],
                                )
                            )
                            self.assertEqual(
                                output_editor.bytecode[
                                    expected_pointer : expected_pointer
                                    + len(expected_body)
                                ],
                                expected_body,
                            )
                        elif script_index == 2 and entity in interaction_actions:
                            expected_pointer = interaction_actions[entity]
                        elif script_index == 2 and entity in actor_action_gates:
                            expected_pointer = output_editor.get_script_pointer(
                                entity,
                                script_index,
                            )
                            required_bits, action_pc = actor_action_gates[entity]
                            expected_body = rico._playable_actor_action_gate(
                                expected_pointer,
                                required_bits,
                                action_pc,
                            )
                            self.assertEqual(
                                output_editor.bytecode[
                                    expected_pointer : expected_pointer
                                    + len(expected_body)
                                ],
                                expected_body,
                            )
                        elif (entity, script_index) in private_helpers:
                            expected_pointer = output_editor.get_script_pointer(
                                entity,
                                script_index,
                            )
                            expected_body = private_helpers[(entity, script_index)]
                            self.assertEqual(
                                output_editor.bytecode[
                                    expected_pointer : expected_pointer
                                    + len(expected_body)
                                ],
                                expected_body,
                            )
                        elif script_index == 4 and entity in hidden_entities:
                            expected_pointer = output_editor.get_script_pointer(
                                entity,
                                4,
                            )
                            self.assertEqual(
                                output_editor.bytecode[
                                    expected_pointer : expected_pointer + 5
                                ],
                                b"\x23"
                                + rico.PLAYABLE_ACTOR_GHOST_FLAGS
                                + b"\x00",
                            )
                        self.assertEqual(
                            output_editor.get_script_pointer(entity, script_index),
                            expected_pointer,
                        )
                    if entity == 0:
                        continue
                    if entity in native_party_entities:
                        if chapter.chapter_id == 1 and entity == leader_entity:
                            expected_init = rico._young_rico_party_init(
                                *rico.PLAYABLE_ENTRY_POSITIONS[
                                    chapter.chapter_id
                                ][:2]
                            )
                        else:
                            position = (
                                rico.PLAYABLE_ENTRY_POSITIONS[chapter.chapter_id][:2]
                                if (
                                    entity == leader_entity
                                    and chapter.chapter_id != 2
                                )
                                else None
                            )
                            expected_init = rico._normalized_party_init(
                                party_selectors[entity],
                                position,
                            )
                        init_pc = output_editor.get_script_pointer(entity, 0)
                        self.assertEqual(
                            output_editor.bytecode[
                                init_pc : init_pc + len(expected_init)
                            ],
                            expected_init,
                        )
                    elif (
                        chapter.chapter_id == 1
                        and entity == rico.CHAPTER_ONE_ANNA_ENTITY
                    ):
                        source_init_pc = source_editor.get_script_pointer(entity, 0)
                        self.assertEqual(
                            source_init_pc,
                            rico.CHAPTER_ONE_ANNA_INIT_PC,
                        )
                        self.assertEqual(
                            rico.mass_driver._pointed_script_body(
                                source_editor,
                                source_init_pc,
                            ),
                            rico.CHAPTER_ONE_ANNA_SOURCE_INIT,
                        )
                        init_pc = output_editor.get_script_pointer(entity, 0)
                        self.assertEqual(
                            output_editor.bytecode[
                                init_pc : init_pc
                                + len(rico.CHAPTER_ONE_ANNA_PLAYABLE_INIT)
                            ],
                            rico.CHAPTER_ONE_ANNA_PLAYABLE_INIT,
                        )
                    elif chapter.chapter_id == 1 and entity == 5:
                        init_pc = output_editor.get_script_pointer(entity, 0)
                        self.assertEqual(
                            output_editor.bytecode[
                                init_pc : init_pc + len(rico.INERT_HIDDEN_INIT)
                            ],
                            rico.INERT_HIDDEN_INIT,
                        )
                    elif (
                        chapter.chapter_id == 2
                        and entity == rico.CHAPTER_TWO_HAMMER_ENTITY
                    ):
                        init_pc = output_editor.get_script_pointer(entity, 0)
                        expected_init = rico._chapter_two_hammer_init()
                        self.assertEqual(
                            output_editor.bytecode[
                                init_pc : init_pc + len(expected_init)
                            ],
                            expected_init,
                        )
                    elif entity in hazardous_entities:
                        init_pc = output_editor.get_script_pointer(entity, 0)
                        self.assertEqual(
                            output_editor.bytecode[
                                init_pc : init_pc + len(rico.INERT_HIDDEN_INIT)
                            ],
                            rico.INERT_HIDDEN_INIT,
                        )
                    else:
                        self.assertEqual(
                            output_editor.get_script_pointer(entity, 0),
                            source_editor.get_script_pointer(entity, 0),
                        )
                    if entity in actor_arrival_bits:
                        gate_pc = output_editor.get_script_pointer(entity, 1)
                        expected_gate = rico._playable_actor_arrival_gate(
                            gate_pc,
                            actor_arrival_bits[entity],
                        )
                        self.assertEqual(
                            output_editor.bytecode[
                                gate_pc : gate_pc + len(expected_gate)
                            ],
                            expected_gate,
                        )
                    elif entity in staged_entities:
                        self.assertEqual(
                            output_editor.get_script_pointer(entity, 1),
                            stop_pc,
                        )
                    elif entity in party_entities:
                        expected_update_pc = party_update_pc
                        if chapter.chapter_id == 1 and entity == leader_entity:
                            expected_update_pc = young_rico_update_pc
                        self.assertEqual(
                            output_editor.get_script_pointer(entity, 1),
                            expected_update_pc,
                        )
                    elif (
                        chapter.chapter_id == 1
                        and entity == rico.CHAPTER_ONE_ANNA_ENTITY
                    ):
                        anna_update_pc = output_editor.get_script_pointer(entity, 1)
                        expected_anna_update = (
                            rico._chapter_one_anna_ambient_update(anna_update_pc)
                        )
                        self.assertEqual(
                            output_editor.bytecode[
                                anna_update_pc:
                                anna_update_pc + len(expected_anna_update)
                            ],
                            expected_anna_update,
                        )
                    elif entity in silent_ambient_entities:
                        self.assertEqual(
                            output_editor.get_script_pointer(entity, 1),
                            silent_pc,
                        )
                    elif (
                        chapter.chapter_id == 2
                        and entity == rico.CHAPTER_TWO_HAMMER_ENTITY
                    ):
                        route_pc = output_editor.get_script_pointer(entity, 1)
                        expected_route = rico._chapter_two_hammer_stair_route(
                            route_pc
                        )
                        self.assertEqual(
                            output_editor.bytecode[
                                route_pc : route_pc + len(expected_route)
                            ],
                            expected_route,
                        )
                    elif entity in bound_actor_entities:
                        self.assertEqual(
                            output_editor.get_script_pointer(entity, 1),
                            stop_pc,
                        )
                    else:
                        self.assertEqual(
                            output_editor.get_script_pointer(entity, 1),
                            disable_dialogue_pc,
                        )
                for entity in range(source_editor.entity_count, first_controller):
                    position = (
                        rico.PLAYABLE_ENTRY_POSITIONS[chapter.chapter_id][:2]
                        if entity == leader_entity and chapter.chapter_id != 2
                        else None
                    )
                    expected_init = (
                        rico._young_rico_party_init(*position)
                        if chapter.chapter_id == 1 and entity == leader_entity
                        else rico._normalized_party_init(
                            party_selectors[entity],
                            position,
                        )
                    )
                    init_pc = output_editor.get_script_pointer(entity, 0)
                    self.assertEqual(
                        output_editor.bytecode[
                            init_pc : init_pc + len(expected_init)
                        ],
                        expected_init,
                    )
                    expected_update = (
                        stop_pc
                        if entity in staged_entities
                        else (
                            young_rico_update_pc
                            if chapter.chapter_id == 1 and entity == leader_entity
                            else party_update_pc
                        )
                    )
                    self.assertEqual(
                        output_editor.get_script_pointer(entity, 1),
                        expected_update,
                    )

    def test_chapter_four_private_scene_uses_the_real_door_and_finite_walks(
        self,
    ) -> None:
        chapter = self.chapters[3]
        (
            source_field,
            output_field,
            source_editor,
            output_editor,
            contract,
            first_controller,
            exit_entity,
        ) = self._layout(
            chapter,
            self.sources[chapter.chapter_id],
            self.outputs[chapter.chapter_id],
        )
        source_components = tuple(part.data for part in source_field.parts)
        rico._validate_chapter_four_private_scene_source(
            source_field.header,
            source_components,
        )

        source_walkmesh = source_field.parts[1].data
        sealed_walkmesh = output_field.parts[1].data
        self.assertEqual(
            sealed_walkmesh,
            rico._seal_chapter_four_office_door(source_walkmesh),
        )
        self.assertEqual(
            (len(source_walkmesh), hashlib.sha256(source_walkmesh).hexdigest()),
            (
                rico.CHAPTER_FOUR_WALKMESH_SIZE,
                rico.CHAPTER_FOUR_WALKMESH_SHA256,
            ),
        )
        self.assertEqual(
            hashlib.sha256(sealed_walkmesh).hexdigest(),
            rico.CHAPTER_FOUR_SEALED_WALKMESH_SHA256,
        )
        self.assertEqual(
            {
                index
                for index, (before, after) in enumerate(
                    zip(source_walkmesh, sealed_walkmesh)
                )
                if before != after
            },
            {0x21A, 0x21B, 0x228, 0x229},
        )

        door_record = 0x190 + rico.CHAPTER_FOUR_DOOR_ENTITY * 16
        for field in (source_field, output_field):
            self.assertEqual(
                field.header[door_record : door_record + 16],
                rico.CHAPTER_FOUR_DOOR_HEADER_RECORD,
            )
            models = rico.mass_driver._indexed_bundle_entries(
                field.parts[2].data
            )
            door_model = models[rico.CHAPTER_FOUR_DOOR_MODEL_INDEX]
            self.assertEqual(
                len(door_model),
                rico.CHAPTER_FOUR_DOOR_MODEL_SIZE,
            )
            self.assertEqual(
                hashlib.sha256(door_model).hexdigest(),
                rico.CHAPTER_FOUR_DOOR_MODEL_SHA256,
            )

        for script, pointer, body in (
            (
                rico.CHAPTER_FOUR_DOOR_OPEN_SCRIPT,
                rico.CHAPTER_FOUR_DOOR_OPEN_PC,
                rico.CHAPTER_FOUR_DOOR_OPEN_BODY,
            ),
            (
                rico.CHAPTER_FOUR_DOOR_CLOSE_SCRIPT,
                rico.CHAPTER_FOUR_DOOR_CLOSE_PC,
                rico.CHAPTER_FOUR_DOOR_CLOSE_BODY,
            ),
        ):
            for editor in (source_editor, output_editor):
                self.assertEqual(
                    editor.get_script_pointer(
                        rico.CHAPTER_FOUR_DOOR_ENTITY,
                        script,
                    ),
                    pointer,
                )
                self.assertEqual(
                    editor.bytecode[pointer : pointer + len(body)],
                    body,
                )
        for pointer, body in (
            (
                rico.CHAPTER_FOUR_DOOR_OPEN_SUBROUTINE_PC,
                rico.CHAPTER_FOUR_DOOR_OPEN_SUBROUTINE,
            ),
            (
                rico.CHAPTER_FOUR_DOOR_CLOSE_SUBROUTINE_PC,
                rico.CHAPTER_FOUR_DOOR_CLOSE_SUBROUTINE,
            ),
        ):
            for editor in (source_editor, output_editor):
                self.assertEqual(
                    editor.bytecode[pointer : pointer + len(body)],
                    body,
                )

        for entity in (
            rico.CHAPTER_FOUR_FEI_ENTITY,
            rico.CHAPTER_FOUR_BART_ENTITY,
        ):
            stage = rico._chapter_four_private_stage_body(entity)
            approach = rico._chapter_four_private_route_body(
                rico.CHAPTER_FOUR_PRIVATE_APPROACH_ROUTES[entity],
                hide_offstage=False,
            )
            crossing = rico._chapter_four_private_route_body(
                rico.CHAPTER_FOUR_PRIVATE_CROSS_ROUTES[entity],
                hide_offstage=True,
            )
            for script, expected in (
                (rico.CHAPTER_FOUR_PRIVATE_STAGE_SCRIPT, stage),
                (rico.CHAPTER_FOUR_PRIVATE_APPROACH_SCRIPT, approach),
                (rico.CHAPTER_FOUR_PRIVATE_CROSS_SCRIPT, crossing),
            ):
                pc = output_editor.get_script_pointer(entity, script)
                self.assertEqual(
                    output_editor.bytecode[pc : pc + len(expected)],
                    expected,
                )
            self.assertTrue(stage.startswith(rico.PLAYABLE_ACTOR_GHOST_FLAGS))
            self.assertNotIn(b"\x4A", approach)
            self.assertNotIn(b"\x4A", crossing)
            self.assertNotIn(b"\x23", approach)
            self.assertTrue(
                crossing.endswith(
                    b"\x23" + rico.PLAYABLE_ACTOR_GHOST_FLAGS + b"\x00"
                )
            )

        sigmund_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "Sigmund"
        )
        sigmund_stage = contract.interactions[sigmund_index].stages[0]
        self.assertTrue(sigmund_stage.private_departure_after)
        self.assertEqual(sigmund_stage.dialogue, (11,))
        self.assertNotIn(12, sigmund_stage.after_dialogue)
        self.assertNotIn(13, sigmund_stage.after_dialogue)
        action_pc = output_editor.get_script_pointer(
            first_controller + sigmund_index,
            2,
        )
        action_end = output_editor.get_script_pointer(
            rico.CHAPTER_FOUR_SIGMUND_ENTITY,
            1,
        )
        action = output_editor.bytecode[action_pc:action_end]
        choreography = rico._chapter_four_private_departure_action()
        authored_base = (
            struct.unpack_from(
                "<I",
                source_field.parts[rico.DIALOGUE_INDEX].data,
                0,
            )[0]
            + 1
        )
        question = rico._dialog(authored_base + 11)
        first_private_line = rico._dialog(authored_base + 14)
        question_at = action.index(question)
        choreography_at = action.index(choreography)
        private_line_at = action.index(first_private_line)
        self.assertLess(question_at, choreography_at)
        self.assertLess(choreography_at, private_line_at)
        self.assertNotIn(rico._dialog(authored_base + 12), action)
        self.assertNotIn(rico._dialog(authored_base + 13), action)
        self.assertNotIn(b"\x2C", choreography)

        blocking_calls = (
            b"\x09\x01\x24",
            b"\x09\x04\x24",
            b"\x09\x01\x25",
            b"\x09\x04\x25",
            b"\x09\x12\x26",
            b"\x09\x01\x26",
            b"\x09\x04\x26",
            b"\x09\x12\x27",
        )
        cursor = 0
        for call in blocking_calls:
            found = choreography.find(call, cursor)
            self.assertGreaterEqual(found, cursor)
            cursor = found + len(call)

        self.assertEqual(
            (contract.exit_x, contract.exit_z, contract.exit_triangle),
            (258, -166, 30),
        )
        exit_pc = output_editor.get_script_pointer(exit_entity, 2)
        exit_action = output_editor.bytecode[exit_pc:]
        native_open_call = b"\x09" + bytes(
            (
                rico.CHAPTER_FOUR_DOOR_ENTITY,
                rico.CHAPTER_FOUR_DOOR_OPEN_SCRIPT | 0x20,
            )
        )
        self.assertIn(native_open_call, exit_action)
        native_close_call = b"\x09" + bytes(
            (
                rico.CHAPTER_FOUR_DOOR_ENTITY,
                rico.CHAPTER_FOUR_DOOR_CLOSE_SCRIPT | 0x20,
            )
        )
        self.assertIn(native_close_call, exit_action)
        self.assertLess(
            exit_action.index(native_open_call),
            exit_action.index(native_close_call),
        )

    def test_chapters_five_and_six_use_solid_animated_exit_doors(self) -> None:
        specs = {
            5: {
                "entity": rico.CHAPTER_FIVE_DOOR_ENTITY,
                "model": rico.CHAPTER_FIVE_DOOR_MODEL_INDEX,
                "model_size": rico.CHAPTER_FIVE_DOOR_MODEL_SIZE,
                "model_sha": rico.CHAPTER_FIVE_DOOR_MODEL_SHA256,
                "header": rico.CHAPTER_FIVE_DOOR_HEADER_RECORD,
                "init_pc": rico.CHAPTER_FIVE_DOOR_INIT_PC,
                "init_body": rico.CHAPTER_FIVE_DOOR_INIT_BODY,
                "open_script": rico.CHAPTER_FIVE_DOOR_OPEN_SCRIPT,
                "open_pc": rico.CHAPTER_FIVE_DOOR_OPEN_PC,
                "open_body": rico.CHAPTER_FIVE_DOOR_OPEN_BODY,
                "close_script": rico.CHAPTER_FIVE_DOOR_CLOSE_SCRIPT,
                "close_body": rico.CHAPTER_FIVE_DOOR_CLOSE_BODY,
                "open_sub_pc": rico.CHAPTER_FIVE_DOOR_OPEN_SUBROUTINE_PC,
                "open_sub": rico.CHAPTER_FIVE_DOOR_OPEN_SUBROUTINE,
                "close_sub_pc": rico.CHAPTER_FIVE_DOOR_CLOSE_SUBROUTINE_PC,
                "close_sub": rico.CHAPTER_FIVE_DOOR_CLOSE_SUBROUTINE,
                "solid_init": bytes.fromhex(
                    "0B 00 80 19 06 00 73 03 C0 1A 00 F8 00 00 20 "
                    "F8 03 04 00 18 04 04 64 04 F8 00 10 00 23 00"
                ),
            },
            6: {
                "entity": rico.CHAPTER_SIX_DOOR_ENTITY,
                "model": rico.CHAPTER_SIX_DOOR_MODEL_INDEX,
                "model_size": rico.CHAPTER_SIX_DOOR_MODEL_SIZE,
                "model_sha": rico.CHAPTER_SIX_DOOR_MODEL_SHA256,
                "header": rico.CHAPTER_SIX_DOOR_HEADER_RECORD,
                "init_pc": rico.CHAPTER_SIX_DOOR_INIT_PC,
                "init_body": rico.CHAPTER_SIX_DOOR_INIT_BODY,
                "open_script": rico.CHAPTER_SIX_DOOR_OPEN_SCRIPT,
                "open_pc": rico.CHAPTER_SIX_DOOR_OPEN_PC,
                "open_body": rico.CHAPTER_SIX_DOOR_OPEN_BODY,
                "close_script": rico.CHAPTER_SIX_DOOR_CLOSE_SCRIPT,
                "close_body": rico.CHAPTER_SIX_DOOR_CLOSE_BODY,
                "open_sub_pc": rico.CHAPTER_SIX_DOOR_OPEN_SUBROUTINE_PC,
                "open_sub": rico.CHAPTER_SIX_DOOR_OPEN_SUBROUTINE,
                "close_sub_pc": rico.CHAPTER_SIX_DOOR_CLOSE_SUBROUTINE_PC,
                "close_sub": rico.CHAPTER_SIX_DOOR_CLOSE_SUBROUTINE,
                "solid_init": bytes.fromhex(
                    "0B 00 80 19 95 02 06 00 C0 1A 00 F8 00 00 20 "
                    "F8 03 04 00 18 04 04 64 04 F8 00 10 00 23 00"
                ),
            },
        }
        for chapter_id, spec in specs.items():
            with self.subTest(chapter=chapter_id):
                chapter = self.chapters[chapter_id - 1]
                (
                    source_field,
                    output_field,
                    source_editor,
                    output_editor,
                    contract,
                    _first_controller,
                    exit_entity,
                ) = self._layout(
                    chapter,
                    self.sources[chapter_id],
                    self.outputs[chapter_id],
                )
                source_components = tuple(
                    part.data for part in source_field.parts
                )
                rico._validate_chapter_five_six_exit_door_source(
                    chapter_id,
                    source_field.header,
                    source_components,
                )
                self.assertEqual(source_field.parts[1].data, output_field.parts[1].data)

                door_record = 0x190 + spec["entity"] * 16
                for field in (source_field, output_field):
                    self.assertEqual(
                        field.header[door_record : door_record + 16],
                        spec["header"],
                    )
                    models = rico.mass_driver._indexed_bundle_entries(
                        field.parts[2].data
                    )
                    door_model = models[spec["model"]]
                    self.assertEqual(len(door_model), spec["model_size"])
                    self.assertEqual(
                        hashlib.sha256(door_model).hexdigest(),
                        spec["model_sha"],
                    )

                for editor in (source_editor, output_editor):
                    self.assertEqual(
                        editor.get_script_pointer(spec["entity"], 0),
                        spec["init_pc"],
                    )
                    self.assertEqual(
                        editor.bytecode[
                            spec["init_pc"] :
                            spec["init_pc"] + len(spec["init_body"])
                        ],
                        spec["init_body"],
                    )
                    self.assertEqual(
                        editor.get_script_pointer(
                            spec["entity"], spec["open_script"]
                        ),
                        spec["open_pc"],
                    )
                    self.assertEqual(
                        editor.bytecode[
                            spec["open_pc"] :
                            spec["open_pc"] + len(spec["open_body"])
                        ],
                        spec["open_body"],
                    )
                    for pointer, body in (
                        (spec["open_sub_pc"], spec["open_sub"]),
                        (spec["close_sub_pc"], spec["close_sub"]),
                    ):
                        self.assertEqual(
                            editor.bytecode[pointer : pointer + len(body)],
                            body,
                        )

                close_pc = output_editor.get_script_pointer(
                    spec["entity"], spec["close_script"]
                )
                self.assertEqual(
                    output_editor.bytecode[
                        close_pc : close_pc + len(spec["close_body"])
                    ],
                    spec["close_body"],
                )
                exit_init_pc = output_editor.get_script_pointer(exit_entity, 0)
                exit_action_pc = output_editor.get_script_pointer(exit_entity, 2)
                self.assertEqual(
                    output_editor.bytecode[exit_init_pc:exit_action_pc],
                    spec["solid_init"],
                )
                self.assertEqual(
                    rico._playable_exit_controller_init(contract),
                    spec["solid_init"],
                )
                exit_action = output_editor.bytecode[exit_action_pc:]
                open_call = b"\x09" + bytes(
                    (spec["entity"], spec["open_script"] | 0x20)
                )
                close_call = b"\x09" + bytes(
                    (spec["entity"], spec["close_script"] | 0x20)
                )
                self.assertEqual(exit_action.count(open_call), 1)
                self.assertEqual(exit_action.count(close_call), 1)
                self.assertLess(
                    exit_action.index(open_call),
                    exit_action.index(close_call),
                )

    def test_remapped_objectives_are_exact_visible_donor_props(self) -> None:
        self.assertEqual(
            tuple(pin[0] for pin in rico.PLAYABLE_VISIBLE_PROP_SOURCE_PINS[2]),
            ("mantel clock", "Champion bedroom door"),
        )
        self.assertEqual(
            tuple(
                (pin[1], pin[2])
                for pin in rico.PLAYABLE_VISIBLE_PROP_SOURCE_PINS[2]
            ),
            ((41, 13), (2, 24)),
        )
        expected_positions = {
            1: {
                "settlement window": rico.CHAPTER_ONE_SETTLEMENT_WINDOW_POSITION,
                "gate window": rico.CHAPTER_ONE_GATE_WINDOW_POSITION,
                "cold window": rico.CHAPTER_ONE_WINDOW_POSITION,
                "room heater": rico.CHAPTER_ONE_HEATER_POSITION,
                "stonebell vase": rico.CHAPTER_ONE_FLOWER_VASE_POSITION,
                "water buckets": rico.CHAPTER_ONE_WATER_BUCKET_POSITION,
                "Anne's bedside": rico.CHAPTER_ONE_ANNA_INTERACTION_POSITION,
            },
            2: {
                "mantel clock": (115, -187, 62),
                "arena passage": (-213, -73, 82),
            },
            3: {
                "Anne's portrait": (-169, -254, 11),
                "medical cabinet": (-170, 96, 34),
            },
            4: {
                "office archive cabinet": (121, -110, 20),
                "north vessel archive conduit": (-154, 146, 49),
                "south vessel archive conduit": (-157, -137, 56),
                "Anne's file on the desk": (281, 92, 10),
                "wall communication display": (388, 0, 24),
            },
            6: {
                "Fatima command station": (111, 31, 165),
                "core regulator": (31, 111, 167),
                "Nortune evacuation station": (-111, 31, 169),
                "Stier launch control": (-31, -111, 171),
                "collar shutdown console": (300, 200, 6),
                "Kislev communications receiver": (-300, -200, 1),
            },
            7: {
                "Hammer's empty bunk": (-50, 85, 30),
                "Rico's bunk": (100, 55, 28),
                "hanging work clothes": (-120, -100, 27),
                "Kislev dispatch in the locker": (-10, 165, 38),
                "Rico's reply": (65, -96, 27),
                "Rico's folded letter on the chair": (120, -100, 26),
            },
        }
        for chapter_id, expected in expected_positions.items():
            chapter = self.chapters[chapter_id - 1]
            source_field = parse_field(self.sources[chapter_id])
            source_components = tuple(part.data for part in source_field.parts)
            rico._validate_playable_visible_prop_sources(
                chapter_id,
                source_field.header,
                source_components,
            )
            contract = rico._playable_chapter_contract(chapter_id)
            actual = {
                interaction.name: (
                    interaction.x,
                    interaction.z,
                    interaction.triangle,
                )
                for interaction in contract.interactions
                if interaction.name in expected
            }
            self.assertEqual(actual, expected)
            # The full contract validator independently proves every stance is
            # on its named triangle, entry-connected, and action-box disjoint.
            output_components = [
                part.data for part in parse_field(self.outputs[chapter_id]).parts
            ]
            rico._validate_playable_contract(
                output_components,
                chapter,
                contract,
            )

    def test_chapter_two_native_bedroom_door_is_optional_and_state_safe(self) -> None:
        chapter = self.chapters[1]
        source_field = parse_field(self.sources[2])
        output_field = parse_field(self.outputs[2])
        source_components = tuple(part.data for part in source_field.parts)
        rico._validate_chapter_two_room_source(
            source_field.header,
            source_components,
        )
        source_editor = AtelScript(source_components[rico.SCRIPT_INDEX])
        output_editor = AtelScript(
            output_field.parts[rico.SCRIPT_INDEX].data
        )

        self.assertEqual(
            rico.mass_driver._read_field_entry(
                source_components[rico.SCRIPT_INDEX],
                0,
            ),
            rico.CHAPTER_TWO_MAIN_ENTRY,
        )
        self.assertEqual(
            rico.mass_driver._read_field_entry(
                output_field.parts[rico.SCRIPT_INDEX].data,
                0,
            ),
            rico.CHAPTER_TWO_MAIN_PLAYABLE_ENTRY,
        )
        for field in (source_field, output_field):
            self.assertEqual(
                rico.mass_driver._read_field_entry(
                    field.parts[rico.SCRIPT_INDEX].data,
                    2,
                ),
                rico.CHAPTER_TWO_MAIN_RETURN_ENTRY,
            )
            record = 0x190 + rico.CHAPTER_TWO_MAIN_DOOR_ENTITY * 16
            self.assertEqual(
                field.header[record : record + 16],
                rico.CHAPTER_TWO_MAIN_DOOR_HEADER_RECORD,
            )
            models = rico.mass_driver._indexed_bundle_entries(
                field.parts[2].data
            )
            model = models[rico.CHAPTER_TWO_MAIN_DOOR_MODEL_INDEX]
            self.assertEqual(len(model), 172)
            self.assertEqual(
                hashlib.sha256(model).hexdigest(),
                "688a7e41612bb3c2ec19bb371f2a1e1b43073b2558697d5548bc1eb3fa62f1b9",
            )

        self.assertEqual(
            source_editor.get_script_pointer(
                rico.CHAPTER_TWO_MAIN_DOOR_ENTITY,
                0,
            ),
            rico.CHAPTER_TWO_MAIN_DOOR_INIT_PC,
        )
        door_action = rico.mass_driver._pointed_script_body(
            output_editor,
            output_editor.get_script_pointer(
                rico.CHAPTER_TWO_MAIN_DOOR_ENTITY,
                2,
            ),
        )
        self.assertEqual(
            door_action,
            rico._chapter_two_main_bedroom_action(
                rico.CHAPTER_TWO_BEDROOM_FIELD
            ),
        )
        self.assertTrue(
            door_action.startswith(rico._copy_chapter_two_state_to_persistent())
        )
        self.assertIn(
            rico._immediate(rico.CHAPTER_TWO_BEDROOM_FIELD)
            + rico._immediate(0)
            + b"\x5B",
            door_action,
        )
        self.assertNotIn(
            rico.mass_driver._set_var_bit(rico.PLAYABLE_STATE_VARIABLE, 7),
            door_action,
        )
        self.assertNotIn(
            rico.mass_driver._set_variable_s16(
                rico.CHAPTER_TWO_HAMMER_STATE_VARIABLE,
                0,
            ),
            door_action,
        )
        self.assertEqual(
            tuple(
                stage.bit
                for interaction in rico._playable_chapter_contract(2).interactions
                for stage in interaction.stages
            ),
            (7, 1, 4, 2, 5, 3, 6),
        )

    def test_chapter_two_builds_the_real_field_219_bedroom_loop(self) -> None:
        retail = PROJECT_ROOT / "Xenogears (Disc 1).bin"
        self.assertTrue(retail.is_file())
        reader = rico.DiscReader(retail, 1)
        source = reader.canonical(
            rico._field_bundle_id(rico.CHAPTER_TWO_BEDROOM_DONOR_FIELD)
        )
        graphics = reader.canonical(
            rico._field_bundle_id(rico.CHAPTER_TWO_BEDROOM_DONOR_FIELD) + 1
        )
        self.assertEqual(
            (len(source), hashlib.sha256(source).hexdigest()),
            (
                rico.CHAPTER_TWO_BEDROOM_BUNDLE_SIZE,
                rico.CHAPTER_TWO_BEDROOM_BUNDLE_SHA256,
            ),
        )
        self.assertEqual(
            (len(graphics), hashlib.sha256(graphics).hexdigest()),
            (
                rico.CHAPTER_TWO_BEDROOM_GRAPHICS_SIZE,
                rico.CHAPTER_TWO_BEDROOM_GRAPHICS_SHA256,
            ),
        )
        source_field = parse_field(source)
        chapter = self.chapters[1]

        for disc in (1, 2):
            main_field = rico.CHAPTER_FIELDS[disc][2]
            with self.subTest(disc=disc, main_field=main_field):
                output = rico._build_chapter_two_bedroom_bundle(
                    source,
                    chapter,
                    main_field,
                )
                field = parse_field(output)
                editor = AtelScript(field.parts[rico.SCRIPT_INDEX].data)
                self.assertEqual(len(field.header), len(source_field.header))
                self.assertEqual(
                    field.header[0x18C:],
                    source_field.header[0x18C:],
                )
                self.assertEqual(
                    rico.mass_driver._read_field_entry(
                        field.parts[rico.SCRIPT_INDEX].data,
                        0,
                    ),
                    rico.CHAPTER_TWO_BEDROOM_ENTRY,
                )
                self.assertEqual(
                    rico.mass_driver._pointed_script_body(
                        editor,
                        editor.get_script_pointer(0, 0),
                    ),
                    rico._chapter_two_director(chapter.music),
                )
                return_action = rico.mass_driver._pointed_script_body(
                    editor,
                    editor.get_script_pointer(
                        rico.CHAPTER_TWO_BEDROOM_DOOR_ENTITY,
                        2,
                    ),
                )
                self.assertEqual(
                    return_action,
                    rico._chapter_two_bedroom_return_action(main_field),
                )
                self.assertNotIn(
                    rico.mass_driver._set_variable_s16(
                        rico.CHAPTER_TWO_HAMMER_STATE_VARIABLE,
                        0,
                    ),
                    return_action,
                )
                door_record = (
                    0x190 + rico.CHAPTER_TWO_BEDROOM_DOOR_ENTITY * 16
                )
                self.assertEqual(
                    field.header[door_record : door_record + 16],
                    rico.CHAPTER_TWO_BEDROOM_DOOR_HEADER_RECORD,
                )
                models = rico.mass_driver._indexed_bundle_entries(
                    field.parts[2].data
                )
                door_model = models[rico.CHAPTER_TWO_BEDROOM_DOOR_MODEL_INDEX]
                self.assertEqual(
                    (len(door_model), hashlib.sha256(door_model).hexdigest()),
                    (
                        rico.CHAPTER_TWO_BEDROOM_DOOR_MODEL_SIZE,
                        rico.CHAPTER_TWO_BEDROOM_DOOR_MODEL_SHA256,
                    ),
                )
                dialogue = rico.parse_dialogue(
                    field.parts[rico.DIALOGUE_INDEX].data
                )
                self.assertEqual(
                    tuple(block.text for block in dialogue.blocks),
                    (rico._reflow_dialogue_text(rico.CHAPTER_TWO_BED_REFLECTION),),
                )
                bed_action_pc = editor.get_script_pointer(
                    rico.CHAPTER_TWO_BED_CONTROLLER_ENTITY,
                    2,
                )
                self.assertEqual(
                    rico.mass_driver._pointed_script_body(
                        editor,
                        bed_action_pc,
                    ),
                    rico._build_chapter_two_bed_reflection_action(
                        bed_action_pc
                    ),
                )
                encounters = field.parts[rico.mass_driver.ENCOUNTER_INDEX].data
                self.assertEqual(
                    encounters[
                        rico.WEIGHTS_OFFSET :
                        rico.WEIGHTS_OFFSET + rico.FORMATION_COUNT
                    ],
                    bytes(rico.FORMATION_COUNT),
                )
                for entity in range(4, editor.entity_count):
                    init_pc = editor.get_script_pointer(entity, 0)
                    self.assertEqual(
                        editor.bytecode[
                            init_pc : init_pc + len(rico.INERT_HIDDEN_INIT)
                        ],
                        rico.INERT_HIDDEN_INIT,
                    )

    def test_chapter_seven_uses_the_real_sealed_bedroom_door(self) -> None:
        chapter = self.chapters[6]
        (
            source_field,
            output_field,
            source_editor,
            output_editor,
            contract,
            _first_controller,
            exit_entity,
        ) = self._layout(
            chapter,
            self.sources[chapter.chapter_id],
            self.outputs[chapter.chapter_id],
        )
        source_components = tuple(part.data for part in source_field.parts)
        rico._validate_chapter_seven_room_source(
            source_field.header,
            source_components,
        )

        source_walkmesh = source_field.parts[1].data
        sealed_walkmesh = output_field.parts[1].data
        self.assertEqual(
            sealed_walkmesh,
            rico._seal_chapter_seven_bedroom_door(source_walkmesh),
        )
        self.assertEqual(
            hashlib.sha256(sealed_walkmesh).hexdigest(),
            rico.CHAPTER_SEVEN_SEALED_WALKMESH_SHA256,
        )
        self.assertEqual(
            {
                index
                for index, (before, after) in enumerate(
                    zip(source_walkmesh, sealed_walkmesh)
                )
                if before != after
            },
            {0x16A, 0x16B, 0x17C, 0x17D},
        )

        door_record = 0x190 + rico.CHAPTER_SEVEN_DOOR_ENTITY * 16
        for field in (source_field, output_field):
            self.assertEqual(
                field.header[door_record : door_record + 16],
                rico.CHAPTER_SEVEN_DOOR_HEADER_RECORD,
            )
            models = rico.mass_driver._indexed_bundle_entries(
                field.parts[2].data
            )
            door_model = models[rico.CHAPTER_SEVEN_DOOR_MODEL_INDEX]
            self.assertEqual(len(door_model), rico.CHAPTER_SEVEN_DOOR_MODEL_SIZE)
            self.assertEqual(
                hashlib.sha256(door_model).hexdigest(),
                rico.CHAPTER_SEVEN_DOOR_MODEL_SHA256,
            )
        for script, pointer, body in (
            (
                rico.CHAPTER_SEVEN_DOOR_OPEN_SCRIPT,
                rico.CHAPTER_SEVEN_DOOR_OPEN_PC,
                rico.CHAPTER_SEVEN_DOOR_OPEN_BODY,
            ),
            (
                rico.CHAPTER_SEVEN_DOOR_CLOSE_SCRIPT,
                rico.CHAPTER_SEVEN_DOOR_CLOSE_PC,
                rico.CHAPTER_SEVEN_DOOR_CLOSE_BODY,
            ),
        ):
            for editor in (source_editor, output_editor):
                self.assertEqual(
                    editor.get_script_pointer(
                        rico.CHAPTER_SEVEN_DOOR_ENTITY,
                        script,
                    ),
                    pointer,
                )
                self.assertEqual(
                    editor.bytecode[pointer : pointer + len(body)],
                    body,
                )
        for pointer, body in (
            (
                rico.CHAPTER_SEVEN_DOOR_OPEN_SUBROUTINE_PC,
                rico.CHAPTER_SEVEN_DOOR_OPEN_SUBROUTINE,
            ),
            (
                rico.CHAPTER_SEVEN_DOOR_CLOSE_SUBROUTINE_PC,
                rico.CHAPTER_SEVEN_DOOR_CLOSE_SUBROUTINE,
            ),
        ):
            self.assertEqual(
                output_editor.bytecode[pointer : pointer + len(body)],
                body,
            )

        self.assertEqual(
            (contract.exit_x, contract.exit_z, contract.exit_triangle),
            rico.CHAPTER_SEVEN_EXIT_POSITION,
        )
        exit_pc = output_editor.get_script_pointer(exit_entity, 2)
        exit_action = output_editor.bytecode[exit_pc:]
        open_call = b"\x09" + bytes(
            (
                rico.CHAPTER_SEVEN_DOOR_ENTITY,
                rico.CHAPTER_SEVEN_DOOR_OPEN_SCRIPT | 0x20,
            )
        )
        close_call = b"\x09" + bytes(
            (
                rico.CHAPTER_SEVEN_DOOR_ENTITY,
                rico.CHAPTER_SEVEN_DOOR_CLOSE_SCRIPT | 0x20,
            )
        )
        self.assertEqual(exit_action.count(open_call), 1)
        self.assertEqual(exit_action.count(close_call), 1)
        self.assertLess(exit_action.index(open_call), exit_action.index(close_call))
        retired_pc = output_editor.get_script_pointer(16, 0)
        self.assertEqual(
            output_editor.bytecode[
                retired_pc : retired_pc + len(rico.INERT_HIDDEN_INIT)
            ],
            rico.INERT_HIDDEN_INIT,
        )

    def test_each_chapter_places_rico_at_its_explicit_entry_coordinates(self) -> None:
        expected_positions = {
            1: (115, -121, 86),
            2: (-125, 134, 38),
            3: (0, 0, 25),
            4: (91, 74, 15),
            5: (3, 51, 195),
            6: (0, 0, 164),
            7: (-11, 121, 32),
        }
        self.assertEqual(rico.PLAYABLE_ENTRY_POSITIONS, expected_positions)

        for chapter in self.chapters:
            with self.subTest(chapter=chapter.chapter_id):
                (
                    _source_field,
                    output_field,
                    source_editor,
                    _output_editor,
                    _contract,
                    _first_controller,
                    _exit_entity,
                ) = self._layout(
                    chapter,
                    self.sources[chapter.chapter_id],
                    self.outputs[chapter.chapter_id],
                )
                if chapter.donor_field in rico.VARIABLE_PARTY_DONORS:
                    leader_entity = 1
                else:
                    registered = rico._registered_character_entities(source_editor)
                    missing = rico._missing_playable_characters(
                        chapter,
                        source_editor,
                    )
                    leader_character = rico.CHAPTER_PARTIES[chapter.chapter_id][0]
                    leader_entity = registered.get(leader_character)
                    if leader_entity is None:
                        leader_entity = (
                            source_editor.entity_count
                            + missing.index(leader_character)
                        )

                record = 0x190 + leader_entity * 16
                x = struct.unpack_from("<h", output_field.header, record + 8)[0]
                z = struct.unpack_from("<h", output_field.header, record + 12)[0]
                self.assertEqual(
                    (x, z),
                    expected_positions[chapter.chapter_id][:2],
                )

    def test_chapter_one_has_a_silent_and_coherent_household_sequence(self) -> None:
        contract = rico._playable_chapter_contract(1)
        interactions = {
            interaction.name: interaction for interaction in contract.interactions
        }

        self.assertEqual(
            self.chapters[0].blocks[0],
            "CHAPTER 1\nMOTHER'S PROMISE<Close>",
        )
        self.assertNotIn(
            "Nortune, many years ago",
            self.chapters[0].blocks[0],
        )
        self.assertIn(
            "young Rico lives with his mother, Anne",
            self.chapters[0].selection_exposition,
        )
        self.assertIn(
            "one cold day becomes a turning point in Rico's life",
            self.chapters[0].selection_exposition,
        )
        self.assertIn(
            "Though Anne passes away when Rico is only ten years old",
            self.chapters[0].selection_exposition,
        )
        self.assertIn(
            "the words she leaves behind remain with him",
            self.chapters[0].selection_exposition,
        )
        self.assertIn(
            "shaping the man he will one day become...",
            self.chapters[0].selection_exposition,
        )
        self.assertNotIn(
            "Fei and Elly",
            self.chapters[0].selection_exposition,
        )
        self.assertNotIn(
            "merciful ruler",
            self.chapters[0].selection_exposition,
        )
        self.assertNotIn(
            "final lesson in mercy",
            self.chapters[0].selection_exposition,
        )
        self.assertNotIn(
            "cold night",
            self.chapters[0].selection_exposition.casefold(),
        )
        self.assertEqual(
            rico._chapter_selection_exposition(self.chapters[0]),
            (
                self.chapters[0].blocks[0],
                self.chapters[0].selection_exposition,
            ),
        )
        self.assertNotIn(
            self.chapters[0].blocks[1],
            rico._chapter_selection_exposition(self.chapters[0]),
        )
        custom_text = "\n".join(rico._playable_custom_texts(contract))
        self.assertNotIn("OBJECTIVE\n", custom_text)
        self.assertNotIn("Check the window, then speak with Mom", custom_text)
        self.assertEqual(
            sum(
                text.casefold().count("chipped cup")
                for text in (
                    *self.chapters[0].blocks,
                    *rico._playable_custom_texts(contract),
                )
            ),
            1,
        )
        self.assertEqual(
            set(interactions),
            {
                "settlement window",
                "gate window",
                "cold window",
                "room heater",
                "stonebell vase",
                "water buckets",
                "Anne's bedside",
                "reading desk",
                "cooking counter",
            },
        )
        self.assertNotIn("Anne's pendant", interactions)
        self.assertEqual(contract.optional_bits, (8, 9))
        settlement_window = interactions["settlement window"]
        gate_window = interactions["gate window"]
        for room_window, position, half_width, half_depth, anchor in (
            (
                settlement_window,
                rico.CHAPTER_ONE_SETTLEMENT_WINDOW_POSITION,
                rico.CHAPTER_ONE_SETTLEMENT_WINDOW_INTERACTION_HALF_WIDTH,
                rico.CHAPTER_ONE_SETTLEMENT_WINDOW_INTERACTION_HALF_DEPTH,
                rico.CHAPTER_ONE_SETTLEMENT_WINDOW_WALKMESH_ANCHOR,
            ),
            (
                gate_window,
                rico.CHAPTER_ONE_GATE_WINDOW_POSITION,
                rico.CHAPTER_ONE_GATE_WINDOW_INTERACTION_HALF_WIDTH,
                rico.CHAPTER_ONE_GATE_WINDOW_INTERACTION_HALF_DEPTH,
                rico.CHAPTER_ONE_GATE_WINDOW_WALKMESH_ANCHOR,
            ),
        ):
            with self.subTest(window=room_window.name):
                self.assertEqual(
                    (
                        room_window.x,
                        room_window.z,
                        room_window.triangle,
                        room_window.interaction_half_width,
                        room_window.interaction_half_depth,
                        room_window.requires_facing,
                    ),
                    (*position, half_width, half_depth, True),
                )
                self.assertEqual(room_window.walkmesh_anchor, anchor)
                self.assertFalse(room_window.stages)
                self.assertEqual(
                    (
                        room_window.interaction_half_width * 2 + 0x10,
                        room_window.interaction_half_depth * 2 + 0x10,
                    ),
                    (24, 24),
                )

        self.assertEqual(settlement_window.repeat_dialogue, (2,))
        settlement_view = self.chapters[0].blocks[2]
        self.assertIn("Rain streaks the glass", settlement_view)
        self.assertIn("low roofs", settlement_view)
        self.assertIn("Nortune's outer wall", settlement_view)
        self.assertEqual(gate_window.repeat_dialogue, (3,))
        gate_view = self.chapters[0].blocks[3]
        self.assertIn("Nortune's gate", gate_view)
        self.assertIn("poor settlement", gate_view)
        self.assertIn("Imperial Capital's wall", gate_view)

        window = interactions["cold window"]
        self.assertEqual(
            (
                window.x,
                window.z,
                window.triangle,
                window.interaction_half_width,
                window.interaction_half_depth,
                window.requires_facing,
            ),
            (
                *rico.CHAPTER_ONE_WINDOW_POSITION,
                rico.CHAPTER_ONE_WINDOW_INTERACTION_HALF_WIDTH,
                rico.CHAPTER_ONE_WINDOW_INTERACTION_HALF_DEPTH,
                True,
            ),
        )
        self.assertEqual(
            window.walkmesh_anchor,
            rico.CHAPTER_ONE_WINDOW_SLOT_ONE_EDGE_ENGINE_POSITION,
        )
        window_effective_x = window.interaction_half_width * 2 + 0x10
        window_effective_z = window.interaction_half_depth * 2 + 0x10
        # RAC27 had a 56-by-56 effective box.  This replacement is smaller in
        # both dimensions and shifted through the wall, so it spans the frame
        # without recreating a large room-side hotspot.
        self.assertEqual((window_effective_x, window_effective_z), (24, 20))
        self.assertLess(window_effective_x, 0x06 * 2 + 0x10)
        self.assertLess(window_effective_z, 0x06 * 2 + 0x10)

        # RAC21's earlier stance, RAC27 Slot 1's exact right-side stance, and
        # the 2026-08-30 Slot 1 stance on the other reachable part of the frame
        # are all directly before the intended pane and inside the tight box.
        window_x, window_z = rico.CHAPTER_ONE_WINDOW_LIVE_REPRO_POSITION
        self.assertLessEqual(abs(window_x - window.x), window_effective_x)
        self.assertLessEqual(abs(window_z - window.z), window_effective_z)
        saved_x, saved_z = rico.CHAPTER_ONE_WINDOW_SLOT_ONE_EDGE_REPRO_POSITION
        engine_position = (math.floor(saved_x), math.floor(saved_z))
        self.assertEqual(
            engine_position,
            rico.CHAPTER_ONE_WINDOW_SLOT_ONE_EDGE_ENGINE_POSITION,
        )
        self.assertLessEqual(abs(saved_x - window.x), window_effective_x)
        self.assertLessEqual(abs(saved_z - window.z), window_effective_z)
        left_x, left_z = rico.CHAPTER_ONE_WINDOW_SLOT_ONE_LEFT_EDGE_REPRO_POSITION
        left_engine_position = (math.floor(left_x), math.floor(left_z))
        self.assertEqual(
            left_engine_position,
            rico.CHAPTER_ONE_WINDOW_SLOT_ONE_LEFT_EDGE_ENGINE_POSITION,
        )
        self.assertLessEqual(abs(left_x - window.x), window_effective_x)
        self.assertLessEqual(abs(left_z - window.z), window_effective_z)
        lower_x, lower_z = rico.CHAPTER_ONE_WINDOW_SLOT_ONE_LOWER_EDGE_REPRO_POSITION
        lower_engine_position = (math.floor(lower_x), math.floor(lower_z))
        self.assertEqual(
            lower_engine_position,
            rico.CHAPTER_ONE_WINDOW_SLOT_ONE_LOWER_EDGE_ENGINE_POSITION,
        )
        self.assertLessEqual(abs(lower_x - window.x), window_effective_x)
        self.assertLessEqual(abs(lower_z - window.z), window_effective_z)
        for far_x, far_z in rico.CHAPTER_ONE_WINDOW_TOO_FAR_REPRO_POSITIONS:
            self.assertTrue(
                abs(far_x - window.x) > window_effective_x
                or abs(far_z - window.z) > window_effective_z
            )
        self.assertTrue(window.requires_facing)

        def facing_result(
            point: tuple[int, int],
            target: tuple[int, int],
            yaw: int,
        ) -> tuple[int, int, bool]:
            ratan = rico.mass_driver._noah_ratan2(
                target[1] - point[1],
                target[0] - point[0],
            ) & 0x0FFF
            desired = (-ratan) & 0x0FFF
            gap = (yaw - desired) & 0x0FFF
            return desired, gap, gap < 700 or gap > 3396

        saved_yaw = rico.CHAPTER_ONE_WINDOW_SLOT_ONE_EDGE_YAW
        legacy_facing = facing_result(
            engine_position,
            (194, -193),
            saved_yaw,
        )
        corrected_facing = facing_result(
            engine_position,
            (window.x, window.z),
            saved_yaw,
        )
        self.assertEqual(legacy_facing, (0x0ED2, 0x032E, False))
        self.assertEqual(corrected_facing, (0x01E4, 0x001C, True))
        left_edge_facing = facing_result(
            left_engine_position,
            (window.x, window.z),
            saved_yaw,
        )
        self.assertEqual(left_edge_facing, (0x0191, 0x006F, True))
        lower_edge_facing = facing_result(
            lower_engine_position,
            (window.x, window.z),
            saved_yaw,
        )
        self.assertEqual(lower_edge_facing, (0x0156, 0x00AA, True))

        source_field = parse_field(self.sources[1])
        walkmesh = rico._walkmesh_layer(source_field.parts[1].data, 0)
        self.assertTrue(
            rico._point_inside_triangle(
                engine_position,
                walkmesh[window.triangle],
            )
        )
        # The invisible pivot is deliberately behind the wall and aims toward
        # the pane.  The separate reachable anchor is what triangle 25 owns.
        self.assertFalse(
            any(
                rico._point_inside_triangle((window.x, window.z), triangle)
                for triangle in walkmesh
            )
        )
        pane_x, pane_z = rico.CHAPTER_ONE_WINDOW_PANE_WORLD_CENTER
        self.assertGreater(window.x - window.z, engine_position[0] - engine_position[1])
        self.assertLess(window.x - window.z, pane_x - pane_z)

        contact_min_t, contact_max_t = (
            rico.CHAPTER_ONE_WINDOW_CONTACT_TANGENT_RANGE
        )
        contact_triangles = tuple(
            walkmesh[index]
            for index in rico.CHAPTER_ONE_WINDOW_CONTACT_TRIANGLES
        )
        contact_min_x = min(vertex[0] for tri in contact_triangles for vertex in tri)
        contact_max_x = max(vertex[0] for tri in contact_triangles for vertex in tri)
        contact_min_z = min(vertex[2] for tri in contact_triangles for vertex in tri)
        contact_max_z = max(vertex[2] for tri in contact_triangles for vertex in tri)
        frame_contact_points = {
            (x, z)
            for x in range(contact_min_x, contact_max_x + 1)
            for z in range(contact_min_z, contact_max_z + 1)
            if x - z >= rico.CHAPTER_ONE_WINDOW_CONTACT_NORMAL_MIN
            and contact_min_t <= x + z <= contact_max_t
            and abs(x - window.x) <= window_effective_x
            and abs(z - window.z) <= window_effective_z
            and facing_result((x, z), (window.x, window.z), saved_yaw)[2]
            and any(
                rico._point_inside_triangle((x, z), triangle)
                for triangle in contact_triangles
            )
        }
        self.assertEqual(len(frame_contact_points), 280)
        self.assertIn(engine_position, frame_contact_points)
        self.assertIn(left_engine_position, frame_contact_points)
        self.assertIn(lower_engine_position, frame_contact_points)
        self.assertIn(
            (math.floor(window_x), math.floor(window_z)),
            frame_contact_points,
        )
        self.assertEqual(
            max(x - z for x, z in frame_contact_points),
            393,
        )
        frame_facing_errors = []
        for point in frame_contact_points:
            with self.subTest(window_frame_point=point):
                self.assertLessEqual(abs(point[0] - window.x), window_effective_x)
                self.assertLessEqual(abs(point[1] - window.z), window_effective_z)
                _desired, gap, accepted = facing_result(
                    point,
                    (window.x, window.z),
                    saved_yaw,
                )
                self.assertTrue(accepted)
                frame_facing_errors.append(min(gap, 0x1000 - gap))
        self.assertEqual(max(frame_facing_errors), 584)

        # The native rectangle and cone necessarily over-select around a
        # diagonal prop.  Script 2 samples Rico's coordinates and rejects all
        # 131 of those reachable off-frame cells before showing dialogue.
        coarse_accepted_points = {
            (x, z)
            for x in range(
                window.x - window_effective_x,
                window.x + window_effective_x + 1,
            )
            for z in range(
                window.z - window_effective_z,
                window.z + window_effective_z + 1,
            )
            if any(
                rico._point_inside_triangle((x, z), triangle)
                for triangle in walkmesh
            )
            and facing_result((x, z), (window.x, window.z), saved_yaw)[2]
        }
        self.assertEqual(len(coarse_accepted_points), 411)
        off_frame_points = coarse_accepted_points - frame_contact_points
        self.assertEqual(len(off_frame_points), 131)
        self.assertIn((174, -188), off_frame_points)
        scripted_contact_points = {
            (x, z)
            for x, z in coarse_accepted_points
            if x - z >= rico.CHAPTER_ONE_WINDOW_CONTACT_NORMAL_MIN
            and contact_min_t <= x + z <= contact_max_t
        }
        self.assertEqual(scripted_contact_points, frame_contact_points)

        # The first complete integer layer roomward of the audited contact band
        # remains inside the native box and facing cone, but the diagonal gate
        # rejects it.  This pins the cutoff without restoring the old hotspot.
        just_off_frame = (179, -195)
        self.assertTrue(
            any(
                rico._point_inside_triangle(just_off_frame, triangle)
                for triangle in walkmesh
            )
        )
        self.assertEqual(
            just_off_frame[0] - just_off_frame[1],
            rico.CHAPTER_ONE_WINDOW_CONTACT_NORMAL_MIN - 1,
        )
        self.assertLessEqual(abs(just_off_frame[0] - window.x), window_effective_x)
        self.assertLessEqual(abs(just_off_frame[1] - window.z), window_effective_z)
        self.assertTrue(
            facing_result(just_off_frame, (window.x, window.z), saved_yaw)[2]
        )
        self.assertNotIn(just_off_frame, frame_contact_points)
        self.assertEqual(
            rico._playable_controller_init(
                window.x,
                window.z,
                half_width=window.interaction_half_width,
                half_depth=window.interaction_half_depth,
                requires_facing=window.requires_facing,
            ),
            bytes.fromhex(
                "BC 19 C6 00 30 FF C0 F8 00 00 20 F8 03 04 00 18 "
                "04 02 64 00 20 01 80 23 00"
            ),
        )
        self.assertFalse(window.stages)
        window_narration = window.repeat_dialogue[0]
        self.assertIn("Rico looks through the glass", window_narration)
        self.assertIn("weathered houses", window_narration)
        self.assertIn("poor settlement", window_narration)
        self.assertIn("Kislev's outskirts", window_narration)
        self.assertIn("Imperial Capital", window_narration)
        self.assertIn("cold haze", window_narration)
        self.assertNotIn("slat", window_narration.casefold())
        self.assertNotIn("wood", window_narration.casefold())
        self.assertNotIn("crate", window_narration.casefold())

        desk = interactions["reading desk"]
        self.assertEqual(
            (
                desk.x,
                desk.z,
                desk.triangle,
                desk.interaction_half_width,
                desk.interaction_half_depth,
                desk.requires_facing,
            ),
            (
                *rico.CHAPTER_ONE_READING_DESK_POSITION,
                rico.CHAPTER_ONE_READING_DESK_INTERACTION_HALF_WIDTH,
                rico.CHAPTER_ONE_READING_DESK_INTERACTION_HALF_DEPTH,
                True,
            ),
        )
        self.assertEqual(
            desk.walkmesh_anchor,
            rico.CHAPTER_ONE_READING_DESK_SLOT_ONE_ENGINE_POSITION,
        )
        self.assertEqual(tuple(stage.bit for stage in desk.stages), (8,))
        self.assertEqual(desk.stages[0].required_bits, ())
        self.assertEqual(desk.activation_required_bits, ())
        self.assertEqual(len(desk.stages[0].dialogue), 1)
        first_book_narration = desk.stages[0].dialogue[0]
        self.assertIn("Rico inspects The Emerald Traveler", first_book_narration)
        self.assertIn("his mother has been reading with him", first_book_narration)
        self.assertIn("a heroine", first_book_narration)
        self.assertIn("key to saving the world", first_book_narration)
        self.assertNotIn("Anne\n", first_book_narration)
        self.assertNotIn("<Rico>", first_book_narration)
        repeat_book_narration = desk.repeat_dialogue[0]
        self.assertIn("The Emerald Traveler", repeat_book_narration)
        self.assertIn("Rico and his mother stopped reading", repeat_book_narration)
        self.assertIn("heroine's journey", repeat_book_narration)
        self.assertIn("key to saving the world", repeat_book_narration)
        self.assertNotIn("<Rico>", repeat_book_narration)

        saved_x, saved_z = rico.CHAPTER_ONE_READING_DESK_SLOT_ONE_REPRO_POSITION
        desk_engine_position = (math.floor(saved_x), math.floor(saved_z))
        self.assertEqual(
            desk_engine_position,
            rico.CHAPTER_ONE_READING_DESK_SLOT_ONE_ENGINE_POSITION,
        )
        desk_effective_x = desk.interaction_half_width * 2 + 0x10
        desk_effective_z = desk.interaction_half_depth * 2 + 0x10
        self.assertEqual((desk_effective_x, desk_effective_z), (28, 28))
        self.assertLessEqual(abs(desk_engine_position[0] - desk.x), desk_effective_x)
        self.assertLessEqual(abs(desk_engine_position[1] - desk.z), desk_effective_z)
        self.assertEqual(
            desk_effective_x - abs(desk_engine_position[0] - desk.x),
            3,
        )
        self.assertEqual(
            desk_effective_z - abs(desk_engine_position[1] - desk.z),
            3,
        )
        self.assertTrue(
            rico._point_inside_triangle(
                desk_engine_position,
                walkmesh[desk.triangle],
            )
        )
        self.assertFalse(
            any(
                rico._point_inside_triangle((desk.x, desk.z), triangle)
                for triangle in walkmesh
            )
        )
        desk_ratan = rico.mass_driver._noah_ratan2(
            desk.z - desk_engine_position[1],
            desk.x - desk_engine_position[0],
        ) & 0x0FFF
        desk_desired_yaw = (-desk_ratan) & 0x0FFF
        desk_facing_gap = (
            rico.CHAPTER_ONE_READING_DESK_SLOT_ONE_YAW - desk_desired_yaw
        ) & 0x0FFF
        self.assertEqual((desk_desired_yaw, desk_facing_gap), (0x0200, 0))
        self.assertEqual(
            rico._playable_controller_init(
                desk.x,
                desk.z,
                half_width=desk.interaction_half_width,
                half_depth=desk.interaction_half_depth,
                requires_facing=desk.requires_facing,
            ),
            bytes.fromhex(
                "BC 19 E2 00 AB FF C0 F8 00 00 20 F8 03 04 00 18 "
                "06 06 64 00 20 01 80 23 00"
            ),
        )

        current_x, current_z = (
            rico.CHAPTER_ONE_READING_DESK_CURRENT_SLOT_ONE_REPRO_POSITION
        )
        current_engine_position = (math.floor(current_x), math.floor(current_z))
        self.assertEqual(
            current_engine_position,
            rico.CHAPTER_ONE_READING_DESK_CURRENT_SLOT_ONE_ENGINE_POSITION,
        )
        self.assertLessEqual(
            abs(current_engine_position[0] - desk.x),
            desk_effective_x,
        )
        self.assertLessEqual(
            abs(current_engine_position[1] - desk.z),
            desk_effective_z,
        )
        self.assertEqual(
            desk_effective_z - abs(current_engine_position[1] - desk.z),
            0,
        )
        self.assertTrue(
            rico._point_inside_triangle(
                current_engine_position,
                walkmesh[
                    rico.CHAPTER_ONE_READING_DESK_CURRENT_SLOT_ONE_TRIANGLE
                ],
            )
        )
        current_ratan = rico.mass_driver._noah_ratan2(
            desk.z - current_engine_position[1],
            desk.x - current_engine_position[0],
        ) & 0x0FFF
        current_desired_yaw = (-current_ratan) & 0x0FFF
        current_facing_gap = (
            rico.CHAPTER_ONE_READING_DESK_CURRENT_SLOT_ONE_YAW
            - current_desired_yaw
        ) & 0x0FFF
        self.assertEqual(
            (current_desired_yaw, current_facing_gap),
            (0x0218, 0x0FE8),
        )
        self.assertLessEqual(
            min(current_facing_gap, 0x1000 - current_facing_gap),
            0x64,
        )

        counter = interactions["cooking counter"]
        self.assertEqual(
            (
                counter.x,
                counter.z,
                counter.triangle,
                counter.interaction_half_width,
                counter.interaction_half_depth,
                counter.requires_facing,
                counter.walkmesh_anchor,
            ),
            (
                *rico.CHAPTER_ONE_COOKING_COUNTER_POSITION,
                rico.CHAPTER_ONE_COOKING_COUNTER_INTERACTION_HALF_WIDTH,
                rico.CHAPTER_ONE_COOKING_COUNTER_INTERACTION_HALF_DEPTH,
                False,
                None,
            ),
        )
        self.assertEqual(tuple(stage.bit for stage in counter.stages), (6, 10, 9))
        stove_stage, tea_service_stage, counter_lore_stage = counter.stages
        self.assertEqual(stove_stage.required_bits, (3,))
        self.assertEqual(
            tea_service_stage.required_bits,
            (7, rico.CHAPTER_ONE_KETTLE_BOILED_BIT),
        )
        self.assertEqual(counter_lore_stage.required_bits, ())
        self.assertEqual(counter.activation_required_bits, ())
        self.assertEqual(len(tea_service_stage.dialogue), 1)
        tea_service = tea_service_stage.dialogue[0]
        self.assertIn("kettle begins to whistle", tea_service)
        self.assertIn("water has boiled", tea_service)
        self.assertIn("pinch of dried medicinal herbs", tea_service)
        self.assertIn("jar on the counter", tea_service)
        self.assertIn("places it into the cup", tea_service)
        self.assertNotIn("chipped", tea_service)
        self.assertIn("pours in the steaming water", tea_service)
        self.assertIn("sets the kettle back on the cooktop", tea_service)
        self.assertIn("herbal tea is ready for Anne", tea_service)
        self.assertNotIn("lifts the kettle", tea_service)
        self.assertFalse(tea_service_stage.locked_dialogue)
        tea_locked = {
            completed: dialogue[0]
            for completed, dialogue in tea_service_stage.locked_dialogue_states
        }
        self.assertEqual(
            set(tea_locked),
            {(), (7,), (rico.CHAPTER_ONE_KETTLE_BOILED_BIT,)},
        )
        self.assertIn(
            "water is heating",
            tea_locked[(7,)],
        )
        self.assertIn("has not boiled yet", tea_locked[(7,)])
        self.assertIn(
            "still has the flower to water",
            tea_locked[()],
        )
        self.assertIn(
            "kettle has boiled",
            tea_locked[(rico.CHAPTER_ONE_KETTLE_BOILED_BIT,)].casefold(),
        )
        self.assertEqual(len(counter_lore_stage.dialogue), 5)
        counter_lore, rico_fuller, anna_noticing, rico_smaller, anna_argument = (
            counter_lore_stage.dialogue
        )
        self.assertIn("dented pot and two chipped bowls", counter_lore)
        self.assertIn("Anne taught Rico", counter_lore)
        self.assertIn("handful of grain feed them both", counter_lore)
        self.assertIn("fuller bowl", rico_fuller)
        self.assertIn("put some back", anna_noticing)
        self.assertIn("smaller bowl", rico_smaller)
        self.assertIn("miss this argument", anna_argument)
        self.assertIn("Neither bowl stays fuller for long", counter.repeat_dialogue[0])
        counter_task_language = " ".join(
            (*counter_lore_stage.dialogue, *counter.repeat_dialogue)
        ).casefold()
        for imperative in ("need", "should", "bring", "asked me"):
            self.assertNotIn(imperative, counter_task_language)

        saved_x, saved_z = (
            rico.CHAPTER_ONE_COOKING_COUNTER_SLOT_ONE_REPRO_POSITION
        )
        counter_engine_position = (math.floor(saved_x), math.floor(saved_z))
        self.assertEqual(
            counter_engine_position,
            rico.CHAPTER_ONE_COOKING_COUNTER_SLOT_ONE_ENGINE_POSITION,
        )
        self.assertEqual(rico.CHAPTER_ONE_COOKING_COUNTER_SLOT_ONE_YAW, 0x0A00)
        stove_x, stove_z = (
            rico.CHAPTER_ONE_COOKING_STOVE_SLOT_ONE_REPRO_POSITION
        )
        stove_engine_position = (math.floor(stove_x), math.floor(stove_z))
        self.assertEqual(
            stove_engine_position,
            rico.CHAPTER_ONE_COOKING_STOVE_SLOT_ONE_ENGINE_POSITION,
        )
        self.assertEqual(
            rico.CHAPTER_ONE_COOKING_STOVE_SLOT_ONE_YAW,
            0x0A00,
        )
        counter_effective_x = counter.interaction_half_width * 2 + 0x10
        counter_effective_z = counter.interaction_half_depth * 2 + 0x10
        self.assertEqual((counter_effective_x, counter_effective_z), (36, 36))
        self.assertLessEqual(
            abs(counter_engine_position[0] - counter.x),
            counter_effective_x,
        )
        self.assertLessEqual(
            abs(counter_engine_position[1] - counter.z),
            counter_effective_z,
        )
        self.assertTrue(
            rico._point_inside_triangle(
                counter_engine_position,
                walkmesh[counter.triangle],
            )
        )
        self.assertTrue(
            rico._point_inside_triangle(
                (counter.x, counter.z),
                walkmesh[counter.triangle],
            )
        )
        self.assertEqual(
            rico._playable_controller_init(
                counter.x,
                counter.z,
                half_width=counter.interaction_half_width,
                half_depth=counter.interaction_half_depth,
                requires_facing=counter.requires_facing,
            ),
            bytes.fromhex(
                "BC 19 84 FF CD 00 C0 F8 00 00 20 F8 07 04 00 18 "
                "0A 0A 64 00 20 01 80 23 00"
            ),
        )

        normal_min, normal_max = (
            rico.CHAPTER_ONE_COOKING_COUNTER_CONTACT_NORMAL_RANGE
        )
        tangent_min, tangent_max = (
            rico.CHAPTER_ONE_COOKING_COUNTER_CONTACT_TANGENT_RANGE
        )

        def on_counter_contact(point: tuple[int, int]) -> bool:
            point_x, point_z = point
            return (
                normal_min <= point_z - point_x <= normal_max
                and tangent_min <= point_x + point_z <= tangent_max
            )

        first_edge, last_edge = rico.CHAPTER_ONE_COOKING_COUNTER_FRONTAGE_EDGE
        counter_frontage = tuple(
            zip(
                range(first_edge[0], last_edge[0] + 1),
                range(first_edge[1], last_edge[1] + 1),
            )
        )
        self.assertEqual(len(counter_frontage), 68)
        self.assertEqual((counter_frontage[0], counter_frontage[-1]), (first_edge, last_edge))
        for point in counter_frontage:
            with self.subTest(counter_frontage_point=point):
                self.assertTrue(
                    rico._point_inside_triangle(point, walkmesh[counter.triangle])
                )
                self.assertLessEqual(abs(point[0] - counter.x), counter_effective_x)
                self.assertLessEqual(abs(point[1] - counter.z), counter_effective_z)
                self.assertTrue(on_counter_contact(point))

        coarse_counter_points = {
            (x, z)
            for x in range(
                counter.x - counter_effective_x,
                counter.x + counter_effective_x + 1,
            )
            for z in range(
                counter.z - counter_effective_z,
                counter.z + counter_effective_z + 1,
            )
            if any(
                rico._point_inside_triangle((x, z), triangle)
                for triangle in walkmesh
            )
        }
        counter_contact_points = {
            point for point in coarse_counter_points if on_counter_contact(point)
        }
        self.assertEqual(len(coarse_counter_points), 2_958)
        self.assertEqual(len(counter_contact_points), 1_178)
        self.assertTrue(set(counter_frontage) <= counter_contact_points)
        self.assertIn(counter_engine_position, counter_contact_points)
        self.assertIn(stove_engine_position, counter_contact_points)
        self.assertEqual(
            stove_engine_position[1] - stove_engine_position[0],
            normal_min + 1,
        )
        self.assertEqual(
            stove_engine_position[0] + stove_engine_position[1],
            87,
        )
        # The exact move requested by the player remains active as Rico moves
        # left along Z=232 until the counter collision edge at X=-101.
        self.assertTrue(
            {(-96, 232), (-97, 232), (-98, 232), (-99, 232), (-100, 232), (-101, 232)}
            <= counter_contact_points
        )
        self.assertIn((-96, 219), coarse_counter_points)
        self.assertNotIn((-96, 219), counter_contact_points)

        bucket_effective_x = (
            rico.CHAPTER_ONE_WATER_BUCKET_INTERACTION_HALF_WIDTH * 2 + 0x10
        )
        bucket_effective_z = (
            rico.CHAPTER_ONE_WATER_BUCKET_INTERACTION_HALF_DEPTH * 2 + 0x10
        )
        self.assertEqual((bucket_effective_x, bucket_effective_z), (34, 24))
        counter_box_min_z = counter.z - counter_effective_z
        bucket_box_max_z = (
            rico.CHAPTER_ONE_WATER_BUCKET_POSITION[1] + bucket_effective_z
        )
        self.assertEqual(counter_box_min_z - bucket_box_max_z, 5)

        anna = interactions["Anne's bedside"]
        self.assertEqual(
            (
                anna.x,
                anna.z,
                anna.triangle,
                anna.interaction_half_width,
                anna.interaction_half_depth,
                anna.requires_facing,
            ),
            (
                *rico.CHAPTER_ONE_ANNA_INTERACTION_POSITION,
                rico.CHAPTER_ONE_ANNA_INTERACTION_HALF_WIDTH,
                rico.CHAPTER_ONE_ANNA_INTERACTION_HALF_DEPTH,
                False,
            ),
        )
        anna_effective_x = anna.interaction_half_width * 2 + 0x10
        anna_effective_z = anna.interaction_half_depth * 2 + 0x10
        bed_repros = (
            rico.CHAPTER_ONE_SLOT_ONE_BED_REPRO_POSITION,
            rico.CHAPTER_ONE_MISLABELLED_BED_REPRO_POSITION,
            (154, -169),
        )
        bed_min_x, bed_max_x, bed_min_z, bed_max_z = (
            rico.CHAPTER_ONE_BED_WORLD_FOOTPRINT
        )
        for bed_x, bed_z in bed_repros:
            with self.subTest(bed_repro=(bed_x, bed_z)):
                self.assertLessEqual(bed_min_x, bed_x)
                self.assertLessEqual(bed_x, bed_max_x)
                self.assertLessEqual(bed_min_z, bed_z)
                self.assertLessEqual(bed_z, bed_max_z)
        # The closest bed-edge capture still lies inside the tight position
        # box, so the facing cone remains necessary there.  More distant bed
        # stances are rejected by position alone.
        close_bed_x, close_bed_z = rico.CHAPTER_ONE_MISLABELLED_BED_REPRO_POSITION
        self.assertLessEqual(abs(close_bed_x - window.x), window_effective_x)
        self.assertLessEqual(abs(close_bed_z - window.z), window_effective_z)
        for far_bed_x, far_bed_z in (
            rico.CHAPTER_ONE_SLOT_ONE_BED_REPRO_POSITION,
            (154, -169),
        ):
            self.assertTrue(
                abs(far_bed_x - window.x) > window_effective_x
                or abs(far_bed_z - window.z) > window_effective_z
            )
        self.assertTrue(
            abs(window.x - anna.x) > window_effective_x + anna_effective_x
            or abs(window.z - anna.z) > window_effective_z + anna_effective_z
        )
        self.assertGreater(window.x, 0)
        self.assertLess(window.z, 0)
        self.assertGreater(pane_x, 0)
        self.assertLess(pane_z, 0)
        self.assertGreater(anna.x, 0)
        self.assertLess(anna.z, 0)
        # Anne and her forgiving controller now share a flat-floor point just
        # beyond the bed's foot.  The historical captures remain useful bed
        # landmarks, but the relocated controller need not cover them.
        self.assertEqual(
            rico.CHAPTER_ONE_ANNA_VISUAL_POSITION,
            rico.CHAPTER_ONE_ANNA_INTERACTION_POSITION,
        )
        self.assertLessEqual(bed_min_x, anna.x)
        self.assertLessEqual(anna.x, bed_max_x)
        self.assertGreater(anna.z, bed_max_z)
        self.assertLessEqual(anna.z - bed_max_z, anna_effective_z)
        self.assertEqual(tuple(stage.bit for stage in anna.stages), (2, 4))
        self.assertTrue(contract.completion_at_exit)
        self.assertFalse(any(stage.completes_chapter for stage in anna.stages))
        self.assertEqual(anna.repeat_dialogue, (29,))
        self.assertIn(
            "dry slats are stacked just outside, beside the house",
            self.chapters[0].blocks[29],
        )
        self.assertIn("Take only what you can carry", self.chapters[0].blocks[29])
        self.assertNotIn("window", self.chapters[0].blocks[29].casefold())
        conversation_stage, return_stage = anna.stages
        self.assertEqual(conversation_stage.required_bits, ())
        self.assertFalse(conversation_stage.locked_dialogue)
        self.assertEqual(conversation_stage.dialogue, (4, 5, 6, 7, 8, 9, 10))
        anna_opening = self.chapters[0].blocks[4]
        self.assertTrue(anna_opening.startswith("Anne\n"))
        self.assertIn("come closer, my sweet boy", anna_opening)
        self.assertIn("Don't hide your hands from me", anna_opening)
        rico_report = self.chapters[0].blocks[5]
        self.assertTrue(rico_report.startswith("<Rico>\n"))
        self.assertIn("city gate called me a beast", rico_report)
        self.assertIn("They threw stones", rico_report)
        self.assertIn("don't belong in Kislev", rico_report)
        anna_lesson = self.chapters[0].blocks[6]
        self.assertTrue(anna_lesson.startswith("Anne\n"))
        self.assertIn("People often fear what they do not understand", anna_lesson)
        self.assertIn("fear hardens into hate", anna_lesson)
        self.assertEqual(
            self.chapters[0].blocks[7],
            "<Rico>\nIt hurts, Mom.<Close>",
        )
        anna_mercy_lesson = self.chapters[0].blocks[8]
        self.assertIn("violence does not excuse violence in return", anna_mercy_lesson)
        self.assertIn("Mercy is choosing to end that cycle", anna_mercy_lesson)
        self.assertIn("keep your heart gentle", anna_mercy_lesson)
        self.assertIn("Never let their cruelty decide", anna_mercy_lesson)
        self.assertEqual(
            self.chapters[0].blocks[9],
            "<Rico>\nI'll try, Mom.<Close>",
        )
        anna_task_request = self.chapters[0].blocks[10]
        self.assertTrue(anna_task_request.startswith("Anne\n"))
        self.assertIn("help me with a few tasks today", anna_task_request)
        self.assertEqual(conversation_stage.after_dialogue, (21,))
        first_task = self.chapters[0].blocks[21]
        self.assertTrue(first_task.startswith("Anne\n"))
        self.assertIn("fetch some water from the bucket", first_task)
        self.assertIn("make me some tea", first_task)
        for procedural_instruction in (
            "fill the kettle",
            "Turn on the cooking stove",
            "let the water boil",
            "pinch of the medicinal herbs",
            "Pour in the hot water",
        ):
            self.assertNotIn(procedural_instruction, first_task)

        stove_reply = self.chapters[0].blocks[22]
        self.assertTrue(stove_reply.startswith("<Rico>\n"))
        self.assertIn("The stove is on, Mom", stove_reply)
        self.assertIn("It'll boil soon", stove_reply)
        self.assertIn("<New>Anne\nThank you, Rico", stove_reply)
        second_task = self.chapters[0].blocks[23]
        self.assertTrue(second_task.startswith("Anne\n"))
        self.assertIn("Second... take another scoop", second_task)
        self.assertIn("same bucket", second_task)
        self.assertIn("stonebell in the vase on the table", second_task)
        self.assertIn("open the woodstove valve", second_task)
        self.assertIn("more heat can spread through the house", second_task)
        stonebell_memory = self.chapters[0].blocks[24]
        self.assertEqual(
            stonebell_memory,
            "Anne\nDo you remember where you found that stonebell, Rico?"
            "<New><Rico>\nIn the streets near the market."
            "<New>I felt bad because it was stepped on."
            "<New>Remember you said we could try to save it?<Close>",
        )
        self.assertIn("where you found that stonebell", stonebell_memory)
        self.assertIn("<New><Rico>\n", stonebell_memory)
        self.assertIn("streets near the market", stonebell_memory)
        self.assertIn("it was stepped on", stonebell_memory)
        self.assertIn("we could try to save it", stonebell_memory)
        stonebell_lesson = self.chapters[0].blocks[25]
        self.assertEqual(
            stonebell_lesson,
            "Anne\nYes, I remember."
            "<New>That stonebell is the most precious gift I've ever received."
            "<New>Look how healthy it is now because you've been taking care of it."
            "<New>Stonebells take root between bare stones, where almost nothing "
            "else can grow."
            "<New>Still, their pale blue bells always turn toward the light."
            "<New>You have a good soul, Rico."
            "<New>Never let this world forget that."
            "<New><Rico>\nI won't, Mom...<Close>",
        )
        self.assertIn("Yes, I remember", stonebell_lesson)
        self.assertIn("most precious gift I've ever received", stonebell_lesson)
        self.assertIn("Look how healthy it is now", stonebell_lesson)
        self.assertIn("you've been taking care of it", stonebell_lesson)
        self.assertIn("Stonebells take root between bare stones", stonebell_lesson)
        self.assertIn("pale blue bells always turn toward the light", stonebell_lesson)
        self.assertIn("You have a good soul, Rico", stonebell_lesson)
        self.assertIn("Never let this world forget that", stonebell_lesson)
        self.assertIn("<New><Rico>\nI won't, Mom...", stonebell_lesson)
        self.assertEqual(
            tuple(
                rico._dialogue_window_dimensions(
                    rico._reflow_dialogue_text(
                        text,
                        sentence_safe_pages=True,
                    )
                )
                for text in (stonebell_memory, stonebell_lesson)
            ),
            ((54, 3), (58, 3)),
        )

        expected_return_requirements = (
            3,
            rico.CHAPTER_ONE_STOVE_ON_BIT,
            1,
            7,
            rico.CHAPTER_ONE_HEATER_VALVE_BIT,
            rico.CHAPTER_ONE_KETTLE_BOILED_BIT,
            10,
        )
        self.assertEqual(return_stage.required_bits, expected_return_requirements)
        self.assertFalse(return_stage.locked_dialogue)
        self.assertFalse(return_stage.locked_dialogue_states)
        self.assertEqual(
            tuple(bit for bit, _dialogue in return_stage.locked_dialogue_steps),
            expected_return_requirements,
        )
        return_reminders = {
            bit: dialogue[0]
            for bit, dialogue in return_stage.locked_dialogue_steps
        }
        self.assertTrue(
            all(text.startswith("Anne\n") for text in return_reminders.values())
        )
        self.assertIn("bucket and ladle", return_reminders[3])
        self.assertIn("stove is still cold", return_reminders[6])
        self.assertIn("another scoop", return_reminders[1])
        self.assertIn("soil is still dry", return_reminders[7])
        self.assertIn("woodstove valve is still nearly closed", return_reminders[11])
        self.assertIn("more heat can spread", return_reminders[11])
        self.assertIn("more time to boil", return_reminders[12])
        self.assertIn("water should be ready", return_reminders[10])
        self.assertIn("finish the tea", return_reminders[10])
        self.assertIn("bring it to me", return_reminders[10])
        self.assertNotIn("medicinal herbs", return_reminders[10])
        self.assertNotIn("Pour in the hot water", return_reminders[10])
        self.assertNotIn("chipped", return_reminders[10])
        self.assertTrue(
            all("Finish what I asked" not in text for text in return_reminders.values())
        )

        success_text = " ".join(
            ref for ref in return_stage.dialogue if isinstance(ref, str)
        )
        self.assertTrue(return_stage.dialogue[0].startswith("<Rico>\n"))
        self.assertIn("I brought your cup, Mom", success_text)
        self.assertIn("Thank you, Rico", success_text)
        self.assertNotIn("There you are", success_text)
        self.assertIn("brings Anne the cup", success_text)
        self.assertNotIn("chipped", success_text)
        self.assertIn("steadies it", success_text)
        self.assertIn("takes a small drink", success_text)
        self.assertNotIn("sets down the kettle", success_text)
        self.assertNotIn("pours the hot tea", success_text)
        self.assertIn("presses the cloth to her mouth", success_text)
        self.assertIn("lowers the cloth", success_text)
        self.assertIn("sees blood", success_text)
        post_chore_lesson = "\n".join(self.chapters[0].blocks[12:19])
        self.assertIn("doctors can do no more", post_chore_lesson)
        self.assertIn("This sickness will take me soon", post_chore_lesson)
        self.assertIn("cannot fight this sickness for me", post_chore_lesson)
        self.assertIn("what you carry after I am gone", post_chore_lesson)
        self.assertIn("Do not make others suffer because you are suffering", post_chore_lesson)
        self.assertIn("have power over those who looked down on you", post_chore_lesson)
        self.assertIn("protect people, not to take revenge", post_chore_lesson)
        self.assertIn("cruelty that wounded us will end with you", post_chore_lesson)
        self.assertNotIn("Medicine takes time", post_chore_lesson)
        self.assertNotIn("Pain can make the heart angry", post_chore_lesson)
        self.assertNotIn("Stop the harm when you can", post_chore_lesson)
        self.assertNotIn("That is resolve", post_chore_lesson)
        self.assertNotIn("choose the door", post_chore_lesson)
        self.assertNotIn("people still waiting outside", post_chore_lesson)
        self.assertEqual(return_stage.dialogue[-3:], (26, 27, 28))
        self.assertFalse(return_stage.hide_entities_after)
        self.assertFalse(return_stage.time_cut_after)
        self.assertIn(
            "fire in the woodstove won't last through tonight",
            self.chapters[0].blocks[26],
        )
        self.assertIn("stacked outside beside the house", self.chapters[0].blocks[26])
        self.assertNotIn("window", self.chapters[0].blocks[26].casefold())
        self.assertTrue(self.chapters[0].blocks[26].startswith("Anne\n"))
        self.assertTrue(self.chapters[0].blocks[27].startswith("<Rico>\n"))
        self.assertIn("I'll be just outside", self.chapters[0].blocks[27])
        self.assertIn("Call if you need me", self.chapters[0].blocks[27])
        self.assertTrue(self.chapters[0].blocks[28].startswith("Anne\n"))
        self.assertIn("Anne\nI will.<New>", self.chapters[0].blocks[28])
        self.assertIn("Take only what you can carry", self.chapters[0].blocks[28])
        self.assertNotIn("outside", self.chapters[0].blocks[28].casefold())
        self.assertNotIn("pile", self.chapters[0].blocks[28].casefold())
        self.assertNotIn("rain", self.chapters[0].blocks[28].casefold())
        self.assertNotIn("see the pile", self.chapters[0].blocks[28].casefold())
        self.assertNotIn("window", self.chapters[0].blocks[28].casefold())
        self.assertIn("The rest can wait", self.chapters[0].blocks[28])

        locked_custom_texts = tuple(
            ref
            for _bit, dialogue in return_stage.locked_dialogue_steps
            for ref in dialogue
            if isinstance(ref, str)
        )
        custom_texts = rico._playable_custom_texts(contract)
        self.assertEqual(len(locked_custom_texts), 7)
        self.assertEqual(
            tuple(text for text in custom_texts if text in locked_custom_texts),
            locked_custom_texts,
        )
        for text in locked_custom_texts:
            self.assertEqual(custom_texts.count(text), 1)
            self.assertFalse(
                rico._dialogue_layout_issues(rico._reflow_dialogue_text(text))
            )
        transition = contract.exit_transition
        self.assertIsNotNone(transition)
        assert transition is not None
        self.assertEqual(transition.bit, 5)
        self.assertEqual(transition.required_bits, (2, 3, 6, 1, 7, 11, 10, 4))
        self.assertEqual(transition.firewood_dialogue, (30,))
        self.assertEqual(transition.sickness_dialogue, (31, 32, 33, 34, 35, 36))
        self.assertEqual(transition.loss_dialogue, (37, 38, 39, 40))
        self.assertEqual(transition.funeral_dialogue, (41, 42, 43, 44))
        self.assertIn("pale daylight", self.chapters[0].blocks[30])
        self.assertIn("the broken packing crate", self.chapters[0].blocks[30])
        self.assertIn("driest slats", self.chapters[0].blocks[30])
        self.assertIn("small armful for the stove", self.chapters[0].blocks[30])
        self.assertIn("Beside the house", self.chapters[0].blocks[30])
        self.assertIn("This should keep Mom warm tonight", self.chapters[0].blocks[30])
        self.assertNotIn("rain", self.chapters[0].blocks[30].casefold())
        self.assertNotIn("window", self.chapters[0].blocks[30].casefold())
        self.assertNotIn("within sight", self.chapters[0].blocks[30].casefold())
        self.assertIn("As night falls", self.chapters[0].blocks[31])
        self.assertIn("feeds the woodstove", self.chapters[0].blocks[31])
        self.assertIn("Anne's shivering has not stopped", self.chapters[0].blocks[31])
        self.assertIn("This sickness has been with me", self.chapters[0].blocks[33])
        self.assertEqual(
            self.chapters[0].blocks[36],
            "Anne\nMy stubborn boy. You have done everything I asked.<Close>",
        )
        self.assertNotIn("father's footsteps", self.chapters[0].blocks[36])
        self.assertNotIn("rule Kislev", self.chapters[0].blocks[36])
        self.assertNotIn("Kaiser", self.chapters[0].blocks[36])
        self.assertIn("breathing grows quiet", self.chapters[0].blocks[37])
        self.assertIn("When morning comes", self.chapters[0].blocks[38])
        self.assertIn("local Ethos priest", self.chapters[0].blocks[38])
        self.assertIn("silent vigil", self.chapters[0].blocks[38])
        self.assertIn("empty bed", self.chapters[0].blocks[38])
        self.assertIn("<Rico>\nMom...", self.chapters[0].blocks[39])
        self.assertIn("I did everything you asked", self.chapters[0].blocks[39])
        self.assertIn("flower has water", self.chapters[0].blocks[39])
        self.assertIn("room is warm", self.chapters[0].blocks[39])
        self.assertTrue(
            self.chapters[0].blocks[40].startswith(
                "Daylight enters through the window.<New>"
            )
        )
        self.assertNotIn("gray window", self.chapters[0].blocks[40].casefold())
        self.assertIn("watered stonebell", self.chapters[0].blocks[40])
        self.assertIn("pale blue bells", self.chapters[0].blocks[40])
        self.assertNotIn("pale blue petals", self.chapters[0].blocks[40])
        self.assertNotIn("night", self.chapters[0].blocks[40].casefold())
        self.assertNotIn("moon", self.chapters[0].blocks[40].casefold())
        self.assertIn(
            "burial ground beyond Nortune's outer wall",
            self.chapters[0].blocks[41],
        )
        self.assertIn("weathered markers", self.chapters[0].blocks[41])
        self.assertIn("plain wooden post", self.chapters[0].blocks[41])
        self.assertIn("Only Rico and the Ethos priest", self.chapters[0].blocks[41])
        self.assertTrue(self.chapters[0].blocks[42].startswith("ETHOS PRIEST\n"))
        self.assertIn("never had much", self.chapters[0].blocks[42])
        self.assertIn("shared whatever she could", self.chapters[0].blocks[42])
        self.assertIn("neighbor fell ill one winter", self.chapters[0].blocks[42])
        self.assertIn("brought her firewood", self.chapters[0].blocks[42])
        self.assertIn("stayed until the fever broke", self.chapters[0].blocks[42])
        self.assertIn("own long sickness", self.chapters[0].blocks[42])
        self.assertIn("endured with quiet courage", self.chapters[0].blocks[42])
        self.assertIn("young son, Rico", self.chapters[0].blocks[42])
        husband_sentence = (
            "She leaves behind her young son, Rico, and her husband, "
            "who is still fighting far from home in the war."
        )
        self.assertIn(husband_sentence, self.chapters[0].blocks[42])
        self.assertNotIn("Sigmund", self.chapters[0].blocks[42])
        self.assertIn("who is still fighting far from home", self.chapters[0].blocks[42])
        self.assertIn("in the war", self.chapters[0].blocks[42])
        self.assertIn("soul has returned to God", self.chapters[0].blocks[42])
        self.assertIn("May she rest in His peace", self.chapters[0].blocks[42])
        priest_pages = self.chapters[0].blocks[42].removesuffix("<Close>").split(
            "<New>"
        )
        self.assertEqual(len(priest_pages), 6)
        self.assertTrue(all(page.rstrip().endswith(".") for page in priest_pages))
        laid_out_priest_pages = rico._reflow_dialogue_text(
            self.chapters[0].blocks[42],
            sentence_safe_pages=True,
        ).removesuffix("<Close>").split("<New>")
        husband_pages = [
            page
            for page in laid_out_priest_pages
            if "her husband, who is still fighting" in " ".join(page.split())
        ]
        self.assertEqual(len(husband_pages), 1)
        self.assertEqual(" ".join(husband_pages[0].split()), husband_sentence)
        self.assertNotIn("taught her son", self.chapters[0].blocks[42])
        self.assertNotIn("strength should protect", self.chapters[0].blocks[42])
        self.assertEqual(
            (
                self.chapters[0].blocks[43],
                self.chapters[0].blocks[44],
                self.chapters[0].blocks[20],
            ),
            (
                "The priest lowers his head and gives Rico a final, silent "
                "blessing.<Close>",
                "<Rico>\nMercy...<Close>",
                "END OF CHAPTER 1<Close>",
            ),
        )
        funeral_and_close = "\n".join(
            self.chapters[0].blocks[index]
            for index in (*range(41, 45), *contract.exit_dialogue)
        ).casefold()
        self.assertNotIn("holding his promise to anne close", funeral_and_close)
        self.assertNotIn("you taught me that mercy", funeral_and_close)
        self.assertNotIn("follow dad's path", funeral_and_close)
        self.assertNotIn("because i suffered", funeral_and_close)
        self.assertTrue(funeral_and_close.endswith("end of chapter 1<close>"))
        self.assertNotIn("pendant", funeral_and_close)
        self.assertNotIn("memento", funeral_and_close)
        self.assertNotIn("d block", funeral_and_close)
        self.assertNotIn("chapter 2", funeral_and_close)
        complete_chapter_text = "\n".join(self.chapters[0].blocks).casefold()
        for retired_line in (
            "holding his promise to anne close",
            "you taught me that mercy breaks the cycle of hate",
            "follow dad's path",
            "not make them suffer because i suffered",
        ):
            self.assertNotIn(retired_line, complete_chapter_text)
        self.assertFalse(any(stage.bit == 5 for stage in anna.stages))

        vase = interactions["stonebell vase"]
        self.assertEqual(
            (vase.x, vase.z, vase.triangle),
            rico.CHAPTER_ONE_FLOWER_VASE_POSITION,
        )
        self.assertEqual(
            (vase.interaction_half_width, vase.interaction_half_depth),
            (
                rico.CHAPTER_ONE_FLOWER_VASE_INTERACTION_HALF_WIDTH,
                rico.CHAPTER_ONE_FLOWER_VASE_INTERACTION_HALF_DEPTH,
            ),
        )
        self.assertFalse(vase.requires_facing)
        self.assertEqual(
            rico._playable_controller_init(
                vase.x,
                vase.z,
                half_width=vase.interaction_half_width,
                half_depth=vase.interaction_half_depth,
                requires_facing=vase.requires_facing,
            ),
            bytes.fromhex(
                "BC 19 15 FF 5A 00 C0 F8 00 00 20 F8 07 04 00 18 "
                "02 02 64 00 20 01 80 23 00"
            ),
        )
        self.assertEqual(tuple(stage.bit for stage in vase.stages), (7,))
        self.assertEqual(vase.stages[0].required_bits, (1,))
        self.assertEqual(len(vase.stages[0].dialogue), 1)
        watering = vase.stages[0].dialogue[0]
        self.assertIn("tips the ladle slowly", watering)
        self.assertIn("giving the stonebell a drink", watering)
        self.assertIn("pale blue bells lift", watering)
        self.assertEqual(vase.stages[0].after_dialogue, (24, 25))
        self.assertNotIn(
            "whistle",
            " ".join(str(ref) for ref in vase.stages[0].after_dialogue).casefold(),
        )
        flower_observation = vase.stages[0].locked_dialogue[0]
        self.assertTrue(flower_observation.startswith("A small blue flower rises"))
        self.assertIn("pale blue bells hang over dry soil", flower_observation)
        self.assertIn("rusty orange clay vase", flower_observation)
        self.assertNotIn("purple", flower_observation)
        self.assertNotIn("scoop", flower_observation.casefold())
        self.assertNotIn("Anne\n", flower_observation)
        self.assertNotIn("<Rico>\n", flower_observation)
        self.assertNotIn("stonebell", flower_observation.casefold())
        self.assertFalse(vase.repeat_dialogue[0].startswith("<Rico>\n"))
        self.assertIn("stonebell", vase.repeat_dialogue[0].casefold())
        self.assertIn("pale blue bells lift above the damp soil", vase.repeat_dialogue[0])
        self.assertTrue(self.chapters[0].blocks[22].startswith("<Rico>\n"))
        self.assertTrue(self.chapters[0].blocks[23].startswith("Anne\n"))
        self.assertIn("another scoop of water", self.chapters[0].blocks[23])
        self.assertTrue(self.chapters[0].blocks[24].startswith("Anne\n"))
        self.assertIn("streets near the market", self.chapters[0].blocks[24])
        self.assertIn("stepped on", self.chapters[0].blocks[24])
        self.assertTrue(self.chapters[0].blocks[25].startswith("Anne\n"))
        self.assertIn("between bare stones", self.chapters[0].blocks[25])
        self.assertIn("always turn toward the light", self.chapters[0].blocks[25])
        self.assertIn("I won't, Mom...", self.chapters[0].blocks[25])

        buckets = interactions["water buckets"]
        self.assertEqual(
            (buckets.x, buckets.z, buckets.triangle),
            rico.CHAPTER_ONE_WATER_BUCKET_POSITION,
        )
        self.assertEqual(
            rico.CHAPTER_ONE_WATER_BUCKET_POSITION,
            (-190, 140, 64),
        )
        self.assertEqual(
            (buckets.interaction_half_width, buckets.interaction_half_depth),
            (
                rico.CHAPTER_ONE_WATER_BUCKET_INTERACTION_HALF_WIDTH,
                rico.CHAPTER_ONE_WATER_BUCKET_INTERACTION_HALF_DEPTH,
            ),
        )
        self.assertEqual(
            (
                rico.CHAPTER_ONE_WATER_BUCKET_INTERACTION_HALF_WIDTH,
                rico.CHAPTER_ONE_WATER_BUCKET_INTERACTION_HALF_DEPTH,
            ),
            (0x09, 0x04),
        )
        self.assertFalse(buckets.requires_facing)
        self.assertEqual(
            rico._playable_controller_init(
                buckets.x,
                buckets.z,
                half_width=buckets.interaction_half_width,
                half_depth=buckets.interaction_half_depth,
                requires_facing=buckets.requires_facing,
            ),
            bytes.fromhex(
                "BC 19 42 FF 8C 00 C0 F8 00 00 20 F8 07 04 00 18 "
                "09 04 64 00 20 01 80 23 00"
            ),
        )
        self.assertEqual(tuple(stage.bit for stage in buckets.stages), (3, 1))
        carry_water, second_scoop = buckets.stages
        self.assertEqual(carry_water.required_bits, (2,))
        self.assertIn("dips the ladle", carry_water.dialogue[0])
        self.assertIn("gathers a ladleful of clear water", carry_water.dialogue[0])
        self.assertNotIn("toward the kettle", carry_water.dialogue[0])
        self.assertNotIn("fills the kettle", carry_water.dialogue[0])
        self.assertNotIn("flower", carry_water.dialogue[0])
        water_observation = carry_water.locked_dialogue[0]
        self.assertTrue(
            water_observation.startswith(
                "Two dented water buckets stand underneath the window."
            )
        )
        self.assertIn("Both hold clear water", water_observation)
        self.assertIn("ladle rests across the nearer rim", water_observation)
        self.assertNotIn("stand in the corner", water_observation)
        self.assertNotIn("Mom", water_observation)
        self.assertNotIn("asked", water_observation)
        self.assertNotIn("<Rico>\n", water_observation)
        self.assertEqual(second_scoop.required_bits, (6,))
        self.assertIn("same bucket again", second_scoop.dialogue[0])
        self.assertIn("careful scoop for the stonebell", second_scoop.dialogue[0])
        self.assertIn("turn on the stove", second_scoop.locked_dialogue[0])
        self.assertNotIn("set it on the stove", second_scoop.locked_dialogue[0])
        self.assertIn("water for the flower", second_scoop.locked_dialogue[0])
        self.assertIn("ladle rests across the bucket", buckets.repeat_dialogue[0])
        self.assertIn("water Anne asked for", buckets.repeat_dialogue[0])

        heater = interactions["room heater"]
        self.assertEqual(
            (heater.x, heater.z, heater.triangle),
            rico.CHAPTER_ONE_HEATER_POSITION,
        )
        self.assertEqual(
            (heater.interaction_half_width, heater.interaction_half_depth),
            (
                rico.CHAPTER_ONE_HEATER_INTERACTION_HALF_WIDTH,
                rico.CHAPTER_ONE_HEATER_INTERACTION_HALF_DEPTH,
            ),
        )
        self.assertTrue(heater.requires_facing)
        self.assertEqual(
            heater.walkmesh_anchor,
            rico.CHAPTER_ONE_HEATER_SLOT_ONE_ENGINE_POSITION,
        )
        self.assertEqual(
            rico._playable_controller_init(
                heater.x,
                heater.z,
                half_width=heater.interaction_half_width,
                half_depth=heater.interaction_half_depth,
                requires_facing=heater.requires_facing,
            ),
            bytes.fromhex(
                "BC 19 F5 FF EE FF C0 F8 00 00 20 F8 03 04 00 18 "
                "07 04 64 00 20 01 80 23 00"
            ),
        )
        self.assertEqual(tuple(stage.bit for stage in heater.stages), (11,))
        valve_stage = heater.stages[0]
        self.assertEqual(valve_stage.required_bits, (2,))
        self.assertEqual(len(valve_stage.locked_dialogue), 1)
        self.assertIn("low fire", valve_stage.locked_dialogue[0])
        self.assertIn("valve is nearly closed", valve_stage.locked_dialogue[0])
        self.assertNotIn("Rico opens", valve_stage.locked_dialogue[0])
        self.assertEqual(valve_stage.accepted_selection, 1)
        self.assertIn("Open the valve", valve_stage.choice_text)
        self.assertIn("Open Valve", valve_stage.choice_text)
        self.assertIn("Leave It Closed", valve_stage.choice_text)
        self.assertIn("leaves the valve closed", valve_stage.rejection_dialogue[0])
        self.assertIn("more heat spreads through the house", valve_stage.after_dialogue[0])
        self.assertIn("open valve", heater.repeat_dialogue[0])
        self.assertIn("woodstove", heater.repeat_dialogue[0])

        self.assertEqual(tuple(stage.bit for stage in counter.stages), (6, 10, 9))
        stove_stage, tea_service_stage, _counter_lore_stage = counter.stages
        self.assertEqual(stove_stage.required_bits, (3,))
        self.assertIn("fills the kettle with water", stove_stage.dialogue[0])
        self.assertNotIn("set it on the stove", stove_stage.dialogue[0])
        self.assertIn("Turn on the stove", stove_stage.choice_text)
        self.assertIn("Turn It On", stove_stage.choice_text)
        self.assertIn("Leave It Off", stove_stage.choice_text)
        self.assertNotIn("Set It Down", stove_stage.choice_text)
        self.assertEqual(stove_stage.accepted_selection, 1)
        self.assertIn("leaves the stove off", stove_stage.rejection_dialogue[0])
        self.assertIn("turns on the cooking stove", stove_stage.after_dialogue[0])
        self.assertIn("Heat begins to build", stove_stage.after_dialogue[0])
        self.assertNotIn("sets the filled kettle", stove_stage.after_dialogue[0])
        self.assertEqual(stove_stage.after_dialogue[1:], (22, 23))
        self.assertNotIn(24, stove_stage.after_dialogue)
        self.assertNotIn(25, stove_stage.after_dialogue)
        stove_observation = stove_stage.locked_dialogue[0]
        self.assertIn("worn-down iron cooking stove", stove_observation)
        self.assertIn("beside the counter", stove_observation)
        self.assertIn("empty kettle rests on its cold cooktop", stove_observation)
        self.assertIn("small chipped cup", stove_observation)
        self.assertIn("jar of dried medicinal herbs", stove_observation)
        self.assertNotIn("rests nearby", stove_observation)
        self.assertNotIn("heat rises", stove_observation)
        self.assertNotIn("water bucket", stove_observation)
        self.assertNotIn("needs to fill", stove_observation)
        self.assertNotIn("Mom", stove_observation)
        self.assertNotIn("asked", stove_observation)
        self.assertNotIn("<Rico>\n", stove_observation)
        self.assertEqual(
            tea_service_stage.required_bits,
            (7, rico.CHAPTER_ONE_KETTLE_BOILED_BIT),
        )
        self.assertIn("kettle begins to whistle", tea_service_stage.dialogue[0])
        self.assertIn("water has boiled", tea_service_stage.dialogue[0])
        self.assertIn(
            "pinch of dried medicinal herbs",
            tea_service_stage.dialogue[0],
        )
        self.assertIn("jar on the counter", tea_service_stage.dialogue[0])
        self.assertIn(
            "places it into the cup",
            tea_service_stage.dialogue[0],
        )
        self.assertNotIn("chipped", tea_service_stage.dialogue[0])
        self.assertIn("pours in the steaming water", tea_service_stage.dialogue[0])
        self.assertIn(
            "sets the kettle back on the cooktop",
            tea_service_stage.dialogue[0],
        )
        self.assertIn(
            "herbal tea is ready for Anne",
            tea_service_stage.dialogue[0],
        )
        self.assertNotIn("lifts the kettle", tea_service_stage.dialogue[0])
        tea_locked = {
            completed: dialogue[0]
            for completed, dialogue in tea_service_stage.locked_dialogue_states
        }
        self.assertIn("water is heating", tea_locked[(7,)])
        self.assertIn("has not boiled yet", tea_locked[(7,)])
        self.assertNotIn("kettle", counter.repeat_dialogue[0])
        self.assertIn("two chipped bowls", counter.repeat_dialogue[0].casefold())

        saved_x, saved_z = rico.CHAPTER_ONE_HEATER_SLOT_ONE_REPRO_POSITION
        heater_engine_position = (math.floor(saved_x), math.floor(saved_z))
        self.assertEqual(
            heater_engine_position,
            rico.CHAPTER_ONE_HEATER_SLOT_ONE_ENGINE_POSITION,
        )
        heater_effective_x = heater.interaction_half_width * 2 + 0x10
        heater_effective_z = heater.interaction_half_depth * 2 + 0x10
        self.assertEqual((heater_effective_x, heater_effective_z), (30, 24))
        self.assertLessEqual(
            abs(heater_engine_position[0] - heater.x),
            heater_effective_x,
        )
        self.assertLessEqual(
            abs(heater_engine_position[1] - heater.z),
            heater_effective_z,
        )
        heater_ratan = rico.mass_driver._noah_ratan2(
            heater.z - heater_engine_position[1],
            heater.x - heater_engine_position[0],
        ) & 0x0FFF
        heater_desired_yaw = (-heater_ratan) & 0x0FFF
        heater_facing_gap = (
            rico.CHAPTER_ONE_HEATER_SLOT_ONE_YAW - heater_desired_yaw
        ) & 0x0FFF
        self.assertEqual((heater_desired_yaw, heater_facing_gap), (0x0A74, 0x018C))
        self.assertLess(heater_facing_gap, 700)

        source_field = parse_field(self.sources[1])
        walkmesh = rico._walkmesh_layer(source_field.parts[1].data, 0)
        for interaction, (stance_x, stance_z, stance_triangle) in (
            (vase, rico.CHAPTER_ONE_FLOWER_VASE_POSITION),
            (buckets, (-196, 135, 64)),
            (
                buckets,
                (
                    *rico.CHAPTER_ONE_WATER_BUCKET_SLOT_ONE_ENGINE_POSITION,
                    64,
                ),
            ),
            (heater, rico.CHAPTER_ONE_HEATER_INTERACTION_STANCE),
        ):
            with self.subTest(prop=interaction.name):
                self.assertTrue(
                    rico._point_inside_triangle(
                        (stance_x, stance_z),
                        walkmesh[stance_triangle],
                    )
                )
                effective_x = interaction.interaction_half_width * 2 + 0x10
                effective_z = interaction.interaction_half_depth * 2 + 0x10
                self.assertLessEqual(abs(stance_x - interaction.x), effective_x)
                self.assertLessEqual(abs(stance_z - interaction.z), effective_z)

        vase_effective_x = vase.interaction_half_width * 2 + 0x10
        vase_effective_z = vase.interaction_half_depth * 2 + 0x10
        bucket_effective_x = buckets.interaction_half_width * 2 + 0x10
        bucket_effective_z = buckets.interaction_half_depth * 2 + 0x10
        self.assertEqual((bucket_effective_x, bucket_effective_z), (34, 24))
        saved_x, saved_z = rico.CHAPTER_ONE_WATER_BUCKET_SLOT_ONE_REPRO_POSITION
        bucket_engine_position = (math.floor(saved_x), math.floor(saved_z))
        self.assertEqual(
            bucket_engine_position,
            rico.CHAPTER_ONE_WATER_BUCKET_SLOT_ONE_ENGINE_POSITION,
        )
        self.assertLessEqual(
            abs(bucket_engine_position[0] - buckets.x),
            bucket_effective_x,
        )
        self.assertLessEqual(
            abs(bucket_engine_position[1] - buckets.z),
            bucket_effective_z,
        )
        self.assertTrue(
            rico._point_inside_triangle(bucket_engine_position, walkmesh[64])
        )
        saved_x, saved_z = rico.CHAPTER_ONE_FLOWER_VASE_SLOT_ONE_REPRO_POSITION
        self.assertLessEqual(abs(saved_x - vase.x), vase_effective_x)
        self.assertLessEqual(abs(saved_z - vase.z), vase_effective_z)
        self.assertTrue(
            abs(saved_x - buckets.x) > bucket_effective_x
            or abs(saved_z - buckets.z) > bucket_effective_z
        )
        self.assertTrue(
            abs(vase.x - buckets.x) > vase_effective_x + bucket_effective_x
            or abs(vase.z - buckets.z) > vase_effective_z + bucket_effective_z
        )
        self.assertEqual(
            abs(vase.z - buckets.z)
            - (vase_effective_z + bucket_effective_z),
            6,
        )

        task_text = " ".join(
            (
                *(
                    ref
                    for interaction in contract.interactions
                    for ref in interaction.repeat_dialogue
                    if isinstance(ref, str)
                ),
                *(
                    ref
                    for interaction in contract.interactions
                    for stage in interaction.stages
                    for ref in (
                        *stage.dialogue,
                        *stage.after_dialogue,
                        *stage.locked_dialogue,
                    )
                    if isinstance(ref, str)
                ),
                *(
                    ref
                    for interaction in contract.interactions
                    for stage in interaction.stages
                    for _missing_bit, step_dialogue in (
                        stage.locked_dialogue_steps
                    )
                    for ref in step_dialogue
                    if isinstance(ref, str)
                ),
                *(
                    ref
                    for interaction in contract.interactions
                    for stage in interaction.stages
                    for _completed_bits, state_dialogue in (
                        stage.locked_dialogue_states
                    )
                    for ref in state_dialogue
                    if isinstance(ref, str)
                ),
                *(text for _bit, text in contract.exit_locked_steps),
            )
        ).lower()
        self.assertNotIn("washstand", task_text)
        self.assertNotIn("bread table", task_text)
        self.assertEqual(contract.required_bits, (1, 2, 3, 4, 5, 6, 7, 10, 11))
        self.assertEqual(contract.optional_bits, (8, 9))
        self.assertNotIn(8, contract.required_bits)
        self.assertNotIn(9, contract.required_bits)
        self.assertIn(11, contract.required_bits)
        self.assertIn(10, contract.required_bits)
        self.assertNotIn(8, transition.required_bits)
        self.assertNotIn(9, transition.required_bits)
        self.assertIn(11, transition.required_bits)
        self.assertIn(10, transition.required_bits)
        self.assertNotIn(8, {bit for bit, _text in contract.exit_locked_steps})
        self.assertNotIn(9, {bit for bit, _text in contract.exit_locked_steps})
        self.assertIn(11, {bit for bit, _text in contract.exit_locked_steps})
        self.assertIn(10, {bit for bit, _text in contract.exit_locked_steps})
        self.assertEqual(
            {
                stage.bit
                for interaction in contract.interactions
                for stage in interaction.stages
            }
            | {transition.bit},
            set(contract.required_bits) | set(contract.optional_bits),
        )
        self.assertEqual(contract.exit_dialogue, (20,))
        self.assertTrue(self.chapters[0].blocks[19].lstrip().startswith("["))
        self.assertFalse(self.chapters[0].blocks[20].lstrip().startswith("["))
        self.assertEqual(self.chapters[0].blocks[20], "END OF CHAPTER 1<Close>")
        self.assertEqual(
            (contract.exit_x, contract.exit_z, contract.exit_triangle),
            rico.CHAPTER_ONE_EXIT_POSITION,
        )
        self.assertTrue(
            abs(window_x - contract.exit_x) > 0x18
            or abs(window_z - contract.exit_z) > 0x18
        )
        routed_authored = {
            ref
            for interaction in contract.interactions
            for stage in interaction.stages
            for ref in (
                *stage.dialogue,
                *stage.after_dialogue,
                *stage.locked_dialogue,
                *(
                    step_ref
                    for _missing_bit, step_dialogue in (
                        stage.locked_dialogue_steps
                    )
                    for step_ref in step_dialogue
                ),
                *(
                    state_ref
                    for _completed_bits, state_dialogue in (
                        stage.locked_dialogue_states
                    )
                    for state_ref in state_dialogue
                ),
            )
            if isinstance(ref, int)
        }
        routed_authored.update(
            ref
            for interaction in contract.interactions
            for ref in interaction.repeat_dialogue
            if isinstance(ref, int)
        )
        routed_authored.update(
            ref
            for refs in (
                transition.doorway_dialogue,
                transition.firewood_dialogue,
                transition.sickness_dialogue,
                transition.loss_dialogue,
                transition.funeral_dialogue,
            )
            for ref in refs
            if isinstance(ref, int)
        )
        self.assertNotIn(11, routed_authored)
        self.assertTrue(
            set(range(21, 45)) <= routed_authored
        )
        self.assertIn(30, routed_authored)

    def test_chapter_one_uses_visual_coughs_without_text_stage_directions(
        self,
    ) -> None:
        chapter = self.chapters[0]
        contract = rico._playable_chapter_contract(1)
        visible_text = " ".join(
            (
                *chapter.blocks,
                *rico._playable_custom_texts(contract),
            )
        ).casefold()
        self.assertNotIn("cough", visible_text)
        self.assertNotIn("mama", visible_text)
        prepared_cup = next(
            stage
            for interaction in contract.interactions
            if interaction.name == "Anne's bedside"
            for stage in interaction.stages
            if stage.bit == 4
        )
        self.assertIn(
            "presses the cloth to her mouth",
            " ".join(
                ref for ref in prepared_cup.dialogue if isinstance(ref, str)
            ),
        )

    def test_chapter_one_anna_compiles_the_sequential_task_gate(self) -> None:
        chapter = self.chapters[0]
        (
            source_field,
            _output_field,
            source_editor,
            output_editor,
            contract,
            first_controller,
            _exit_entity,
        ) = self._layout(
            chapter,
            self.sources[chapter.chapter_id],
            self.outputs[chapter.chapter_id],
        )
        anna_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "Anne's bedside"
        )
        anna = contract.interactions[anna_index]
        return_stage = next(stage for stage in anna.stages if stage.bit == 4)
        authored_base = (
            struct.unpack_from(
                "<I",
                source_field.parts[rico.DIALOGUE_INDEX].data,
                0,
            )[0]
            + 1
        )
        custom_texts = rico._playable_custom_texts(contract)
        custom_ids = {
            text: authored_base + len(chapter.blocks) + index
            for index, text in enumerate(custom_texts)
        }
        controller = first_controller + anna_index
        action_pc = output_editor.get_script_pointer(controller, 2)
        action_end = output_editor.get_script_pointer(controller + 1, 0)
        action = output_editor.bytecode[action_pc:action_end]

        branch_at = len(rico._playable_action_prefix(action_pc))
        stage_targets: dict[int, int] = {}
        for stage in anna.stages:
            expected_branch = (
                b"\x02"
                + struct.pack("<H", rico.PLAYABLE_STATE_VARIABLE)
                + struct.pack("<H", 1 << stage.bit)
                + b"\x46"
            )
            self.assertEqual(
                action[branch_at : branch_at + len(expected_branch)],
                expected_branch,
            )
            stage_targets[stage.bit] = (
                struct.unpack_from("<H", action, branch_at + 6)[0] - action_pc
            )
            branch_at += 8

        def route_requirements(state: int) -> int:
            at = stage_targets[return_stage.bit]
            visited: set[int] = set()
            while action[at] in (0x01, 0x02):
                self.assertNotIn(at, visited)
                visited.add(at)
                if action[at] == 0x01:
                    at = struct.unpack_from("<H", action, at + 1)[0] - action_pc
                    continue
                self.assertEqual(
                    action[at + 1 : at + 3],
                    struct.pack("<H", rico.PLAYABLE_STATE_VARIABLE),
                )
                mask = struct.unpack_from("<H", action, at + 3)[0]
                self.assertIn(
                    mask,
                    tuple(1 << bit for bit in return_stage.required_bits),
                )
                self.assertEqual(action[at + 5], 0x46)
                if state & mask:
                    at += 8
                else:
                    at = struct.unpack_from("<H", action, at + 6)[0] - action_pc
            return at

        expected_requirements = (
            3,
            rico.CHAPTER_ONE_STOVE_ON_BIT,
            1,
            7,
            rico.CHAPTER_ONE_HEATER_VALVE_BIT,
            rico.CHAPTER_ONE_KETTLE_BOILED_BIT,
            10,
        )
        self.assertEqual(return_stage.required_bits, expected_requirements)
        self.assertEqual(
            tuple(bit for bit, _dialogue in return_stage.locked_dialogue_steps),
            expected_requirements,
        )
        reminder_refs = dict(return_stage.locked_dialogue_steps)
        locked_routes: set[int] = set()
        complete_state = 0
        bit_four_commit = rico.mass_driver._set_var_bit(
            rico.PLAYABLE_STATE_VARIABLE,
            return_stage.bit,
        )
        for missing_bit in expected_requirements:
            locked_at = route_requirements(complete_state)
            expected_ids = rico._resolve_playable_dialogue(
                reminder_refs[missing_bit],
                authored_base=authored_base,
                authored_count=len(chapter.blocks),
                custom_ids=custom_ids,
            )
            expected_scene = (
                rico.CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL
                + rico._dialogue_sequence(expected_ids)
            )
            expected_body = expected_scene + rico._playable_action_finish(
                action_pc + locked_at + len(expected_scene)
            )
            with self.subTest(next_missing_bit=missing_bit):
                self.assertTrue(action.startswith(expected_body, locked_at))
                self.assertNotIn(bit_four_commit, expected_body)
            locked_routes.add(locked_at)
            complete_state |= 1 << missing_bit

        self.assertEqual(len(locked_routes), len(expected_requirements))
        early_boil_at = route_requirements(
            1 << rico.CHAPTER_ONE_KETTLE_BOILED_BIT
        )
        self.assertEqual(early_boil_at, route_requirements(0))

        success_at = route_requirements(complete_state)
        self.assertNotIn(success_at, locked_routes)
        success_ids = rico._resolve_playable_dialogue(
            return_stage.dialogue,
            authored_base=authored_base,
            authored_count=len(chapter.blocks),
            custom_ids=custom_ids,
        )
        success_scene = (
            rico.CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL
            + rico._dialogue_sequence(success_ids)
        )
        self.assertTrue(action.startswith(success_scene, success_at))
        self.assertIn("I brought your cup, Mom", return_stage.dialogue[0])
        self.assertIn("Thank you, Rico", return_stage.dialogue[0])
        self.assertNotIn("There you are", return_stage.dialogue[0])
        self.assertIn("brings Anne the cup", return_stage.dialogue[1])
        self.assertNotIn("chipped", return_stage.dialogue[1])
        self.assertIn("steadies it", return_stage.dialogue[1])
        self.assertNotIn("sets down the kettle", return_stage.dialogue[1])
        self.assertNotIn("pours the hot tea", return_stage.dialogue[1])
        self.assertIn("small drink", return_stage.dialogue[1])
        self.assertEqual(
            action[success_at:].count(
                rico.mass_driver._set_var_bit(
                    rico.PLAYABLE_STATE_VARIABLE,
                    return_stage.bit,
                )
            ),
            1,
        )
        self.assertNotIn(
            rico.mass_driver._set_var_bit(
                rico.PLAYABLE_STATE_VARIABLE,
                5,
            ),
            action,
        )

    def test_chapter_one_window_compiles_exact_diagonal_contact_gate(self) -> None:
        chapter = self.chapters[0]
        (
            _source_field,
            _output_field,
            source_editor,
            output_editor,
            contract,
            first_controller,
            _exit_entity,
        ) = self._layout(
            chapter,
            self.sources[chapter.chapter_id],
            self.outputs[chapter.chapter_id],
        )
        window_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "cold window"
        )
        controller = first_controller + window_index
        action_pc = output_editor.get_script_pointer(controller, 2)
        action_end = output_editor.get_script_pointer(controller + 1, 0)
        action = output_editor.bytecode[action_pc:action_end]
        prefix = rico._playable_action_prefix(action_pc)
        self.assertTrue(action.startswith(prefix))

        x_variable = rico.CHAPTER_ONE_WINDOW_POSITION_X_VARIABLE
        z_variable = rico.CHAPTER_ONE_WINDOW_POSITION_Z_VARIABLE
        scratch = rico.CHAPTER_ONE_WINDOW_POSITION_SCRATCH_VARIABLE
        self.assertEqual((x_variable, z_variable, scratch), (0x07F8, 0x07FA, 0x07FC))
        self.assertEqual(len({x_variable, z_variable, scratch}), 3)
        self.assertTrue(all(variable % 2 == 0 for variable in (x_variable, z_variable, scratch)))
        self.assertNotIn(
            rico.PLAYABLE_STATE_VARIABLE,
            (x_variable, z_variable, scratch),
        )
        for variable in (x_variable, z_variable, scratch):
            self.assertNotIn(rico._u16(variable), source_editor.bytecode)

        cursor = len(prefix)
        position_and_normal = (
            b"\x2D\xFF"
            + rico._u16(x_variable)
            + rico._u16(z_variable)
            + rico._u16(scratch)
            + rico.mass_driver._copy_variable(scratch, x_variable)
            + rico.mass_driver._variable_math(
                0x39,
                scratch,
                z_variable,
                operand_is_variable=True,
            )
        )
        self.assertEqual(
            action[cursor : cursor + len(position_and_normal)],
            position_and_normal,
        )
        cursor += len(position_and_normal)

        branch_targets: list[int] = []

        def assert_branch(variable: int, value: int, control: int) -> None:
            nonlocal cursor
            expected = (
                b"\x02"
                + rico._u16(variable)
                + struct.pack("<h", value)
                + bytes((control,))
            )
            self.assertEqual(action[cursor : cursor + 6], expected)
            branch_targets.append(struct.unpack_from("<H", action, cursor + 6)[0])
            cursor += 8

        assert_branch(
            scratch,
            rico.CHAPTER_ONE_WINDOW_CONTACT_NORMAL_MIN,
            0x44,
        )
        tangent_math = (
            rico.mass_driver._copy_variable(scratch, x_variable)
            + rico.mass_driver._variable_math(
                0x38,
                scratch,
                z_variable,
                operand_is_variable=True,
            )
        )
        self.assertEqual(
            action[cursor : cursor + len(tangent_math)],
            tangent_math,
        )
        cursor += len(tangent_math)
        minimum_tangent, maximum_tangent = (
            rico.CHAPTER_ONE_WINDOW_CONTACT_TANGENT_RANGE
        )
        assert_branch(scratch, minimum_tangent, 0x44)
        assert_branch(scratch, maximum_tangent + 1, 0x43)

        self.assertEqual(len(set(branch_targets)), 1)
        outside_pc = branch_targets[0]
        outside_at = outside_pc - action_pc
        self.assertGreater(outside_at, cursor)
        outside_finish = rico._playable_action_finish(outside_pc)
        self.assertEqual(action[outside_at:], outside_finish)
        self.assertNotIn(b"\x3A" + rico._u16(rico.PLAYABLE_STATE_VARIABLE), outside_finish)
        self.assertTrue(outside_finish.endswith(b"\xFE\x53\x00"))

    def test_chapter_one_counter_compiles_exact_diagonal_contact_gate(self) -> None:
        chapter = self.chapters[0]
        (
            _source_field,
            _output_field,
            source_editor,
            output_editor,
            contract,
            first_controller,
            _exit_entity,
        ) = self._layout(
            chapter,
            self.sources[chapter.chapter_id],
            self.outputs[chapter.chapter_id],
        )
        counter_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "cooking counter"
        )
        controller = first_controller + counter_index
        action_pc = output_editor.get_script_pointer(controller, 2)
        action_end = output_editor.get_script_pointer(controller + 1, 0)
        action = output_editor.bytecode[action_pc:action_end]
        prefix = rico._playable_action_prefix(action_pc)
        self.assertTrue(action.startswith(prefix))

        x_variable = rico.CHAPTER_ONE_COOKING_COUNTER_POSITION_X_VARIABLE
        z_variable = rico.CHAPTER_ONE_COOKING_COUNTER_POSITION_Z_VARIABLE
        scratch = rico.CHAPTER_ONE_COOKING_COUNTER_POSITION_SCRATCH_VARIABLE
        self.assertEqual((x_variable, z_variable, scratch), (0x07F8, 0x07FA, 0x07FC))
        self.assertEqual(len({x_variable, z_variable, scratch}), 3)
        self.assertNotIn(
            rico.PLAYABLE_STATE_VARIABLE,
            (x_variable, z_variable, scratch),
        )
        for variable in (x_variable, z_variable, scratch):
            self.assertNotIn(rico._u16(variable), source_editor.bytecode)

        cursor = len(prefix)
        position_and_normal = (
            b"\x2D\xFF"
            + rico._u16(x_variable)
            + rico._u16(z_variable)
            + rico._u16(scratch)
            + rico.mass_driver._copy_variable(scratch, z_variable)
            + rico.mass_driver._variable_math(
                0x39,
                scratch,
                x_variable,
                operand_is_variable=True,
            )
        )
        self.assertEqual(
            action[cursor : cursor + len(position_and_normal)],
            position_and_normal,
        )
        cursor += len(position_and_normal)
        branch_targets: list[int] = []

        def assert_branch(value: int, control: int) -> None:
            nonlocal cursor
            expected = (
                b"\x02"
                + rico._u16(scratch)
                + struct.pack("<h", value)
                + bytes((control,))
            )
            self.assertEqual(action[cursor : cursor + 6], expected)
            branch_targets.append(struct.unpack_from("<H", action, cursor + 6)[0])
            cursor += 8

        minimum_normal, maximum_normal = (
            rico.CHAPTER_ONE_COOKING_COUNTER_CONTACT_NORMAL_RANGE
        )
        assert_branch(minimum_normal, 0x44)
        assert_branch(maximum_normal + 1, 0x43)
        tangent_math = (
            rico.mass_driver._copy_variable(scratch, x_variable)
            + rico.mass_driver._variable_math(
                0x38,
                scratch,
                z_variable,
                operand_is_variable=True,
            )
        )
        self.assertEqual(
            action[cursor : cursor + len(tangent_math)],
            tangent_math,
        )
        cursor += len(tangent_math)
        minimum_tangent, maximum_tangent = (
            rico.CHAPTER_ONE_COOKING_COUNTER_CONTACT_TANGENT_RANGE
        )
        assert_branch(minimum_tangent, 0x44)
        assert_branch(maximum_tangent + 1, 0x43)

        self.assertEqual(len(set(branch_targets)), 1)
        outside_pc = branch_targets[0]
        outside_at = outside_pc - action_pc
        self.assertGreater(outside_at, cursor)
        outside_finish = rico._playable_action_finish(outside_pc)
        self.assertEqual(action[outside_at:], outside_finish)
        self.assertNotIn(
            rico.mass_driver._set_var_bit(rico.PLAYABLE_STATE_VARIABLE, 9),
            outside_finish,
        )
        self.assertTrue(outside_finish.endswith(b"\xFE\x53\x00"))

    def test_chapter_one_kettle_boils_in_a_nonblocking_background_timer(
        self,
    ) -> None:
        chapter = self.chapters[0]
        (
            source_field,
            _output_field,
            _source_editor,
            output_editor,
            contract,
            first_controller,
            _exit_entity,
        ) = self._layout(
            chapter,
            self.sources[chapter.chapter_id],
            self.outputs[chapter.chapter_id],
        )
        counter_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "cooking counter"
        )
        counter = contract.interactions[counter_index]
        counter_entity = first_controller + counter_index

        self.assertEqual(rico.CHAPTER_ONE_KETTLE_BOIL_FRAMES, 15 * 60)
        timer_pc = output_editor.get_script_pointer(counter_entity, 1)
        timer = rico._chapter_one_kettle_timer_update(timer_pc)
        self.assertEqual(
            output_editor.bytecode[timer_pc : timer_pc + len(timer)],
            timer,
        )
        stove_test = (
            b"\x02"
            + rico._u16(rico.PLAYABLE_STATE_VARIABLE)
            + rico._u16(1 << rico.CHAPTER_ONE_STOVE_ON_BIT)
            + b"\x46"
        )
        boil_wait = rico._wait(rico.CHAPTER_ONE_KETTLE_BOIL_FRAMES)
        boiled_commit = rico.mass_driver._set_var_bit(
            rico.PLAYABLE_STATE_VARIABLE,
            rico.CHAPTER_ONE_KETTLE_BOILED_BIT,
        )
        self.assertEqual(timer.count(stove_test), 1)
        self.assertEqual(timer.count(boil_wait), 1)
        self.assertEqual(timer.count(boiled_commit), 1)
        self.assertLess(timer.index(stove_test), timer.index(boil_wait))
        self.assertLess(timer.index(boil_wait), timer.index(boiled_commit))

        action_pc = output_editor.get_script_pointer(counter_entity, 2)
        action_end = output_editor.get_script_pointer(counter_entity + 1, 0)
        action = output_editor.bytecode[action_pc:action_end]
        self.assertNotIn(boil_wait, action)
        self.assertNotIn(boiled_commit, action)

        stove_stage = counter.stages[0]
        self.assertEqual(rico.CHAPTER_ONE_STOVE_IGNITION_SOUND_ID, 0xF9)
        self.assertEqual(rico.CHAPTER_ONE_STOVE_FIRE_SOUND_ID, 0x111)
        self.assertEqual(
            stove_stage.accepted_sound_id,
            rico.CHAPTER_ONE_STOVE_IGNITION_SOUND_ID,
        )
        authored_base = (
            struct.unpack_from(
                "<I",
                source_field.parts[rico.DIALOGUE_INDEX].data,
                0,
            )[0]
            + 1
        )
        custom_texts = rico._playable_custom_texts(contract)
        custom_ids = {
            text: authored_base + len(chapter.blocks) + index
            for index, text in enumerate(custom_texts)
        }
        fill_dialogue = rico._dialogue_sequence(
            rico._resolve_playable_dialogue(
                stove_stage.dialogue,
                authored_base=authored_base,
                authored_count=len(chapter.blocks),
                custom_ids=custom_ids,
            )
        )
        filled_commit = rico.mass_driver._set_var_bit(
            rico.PLAYABLE_STATE_VARIABLE,
            rico.CHAPTER_ONE_KETTLE_FILLED_BIT,
        )
        assert stove_stage.choice_text is not None
        choice = (
            rico._wait()
            + rico._choice_dialog(custom_ids[stove_stage.choice_text])
            + b"\xA9\x12\x9C"
        )
        filled_test = (
            b"\x02"
            + rico._u16(rico.PLAYABLE_STATE_VARIABLE)
            + rico._u16(1 << rico.CHAPTER_ONE_KETTLE_FILLED_BIT)
            + b"\x46"
        )
        filled_test_at = action.index(filled_test)
        fill_at = struct.unpack_from("<H", action, filled_test_at + 6)[0] - action_pc
        self.assertEqual(action[filled_test_at + 8], 0x01)
        choice_at = (
            struct.unpack_from("<H", action, filled_test_at + 9)[0] - action_pc
        )
        self.assertTrue(action.startswith(choice, choice_at))
        self.assertTrue(
            action.startswith(fill_dialogue + filled_commit + choice, fill_at)
        )
        self.assertEqual(action.count(fill_dialogue), 1)
        self.assertEqual(action.count(filled_commit), 1)

        choice_branch_at = choice_at + len(choice)
        choice_branch_prefix = (
            b"\x02"
            + rico._u16(rico.MENU_SELECTION_VARIABLE)
            + rico._u16(stove_stage.accepted_selection)
            + b"\x40"
        )
        self.assertEqual(
            action[
                choice_branch_at : choice_branch_at + len(choice_branch_prefix)
            ],
            choice_branch_prefix,
        )
        rejected_at = (
            struct.unpack_from(
                "<H",
                action,
                choice_branch_at + len(choice_branch_prefix),
            )[0]
            - action_pc
        )
        success_at = choice_branch_at + len(choice_branch_prefix) + 2
        ignition_sound = rico._play_sound_effect(
            rico.CHAPTER_ONE_STOVE_IGNITION_SOUND_ID
        )
        audio_helper = rico._chapter_one_stove_audio_helper()
        self.assertEqual(
            output_editor.bytecode[
                rico.CHAPTER_ONE_STOVE_AUDIO_HELPER_PC :
                rico.CHAPTER_ONE_STOVE_AUDIO_HELPER_PC + len(audio_helper)
            ],
            audio_helper,
        )
        for entity in range(output_editor.entity_count):
            for script_index in range(32):
                pointer = output_editor.get_script_pointer(entity, script_index)
                self.assertFalse(
                    rico.CHAPTER_ONE_STOVE_AUDIO_HELPER_PC
                    <= pointer
                    < rico.CHAPTER_ONE_STOVE_AUDIO_HELPER_PC + len(audio_helper),
                    f"entity {entity} script {script_index} enters the fire cave",
                )
        self.assertEqual(
            audio_helper,
            rico._wait(rico.CHAPTER_ONE_STOVE_CLICK_HOLD_FRAMES)
            + rico._play_sound_effect(rico.CHAPTER_ONE_STOVE_FIRE_SOUND_ID)
            + rico._wait(rico.CHAPTER_ONE_STOVE_FIRE_HOLD_FRAMES)
            + rico._play_sound_effect(rico.CHAPTER_ONE_FIELD_SOUND_STOP_ID)
            + b"\x0D",
        )
        self.assertTrue(action.startswith(ignition_sound, success_at))
        self.assertTrue(
            action.startswith(
                ignition_sound + rico.CHAPTER_ONE_STOVE_AUDIO_HELPER_CALL,
                success_at,
            )
        )
        self.assertEqual(action.count(ignition_sound), 1)
        self.assertEqual(action.count(rico.CHAPTER_ONE_STOVE_AUDIO_HELPER_CALL), 1)
        self.assertNotIn(ignition_sound, action[:success_at])
        self.assertNotIn(ignition_sound, action[rejected_at:])

        stove_commit = rico.mass_driver._set_var_bit(
            rico.PLAYABLE_STATE_VARIABLE,
            rico.CHAPTER_ONE_STOVE_ON_BIT,
        )
        after_dialogue = rico._dialogue_sequence(
            rico._resolve_playable_dialogue(
                stove_stage.after_dialogue,
                authored_base=authored_base,
                authored_count=len(chapter.blocks),
                custom_ids=custom_ids,
            )
        )
        self.assertEqual(action.count(stove_commit), 1)
        ignition_at = action.index(ignition_sound)
        after_dialogue_at = action.index(after_dialogue)
        stove_commit_at = action.index(stove_commit)
        self.assertLess(ignition_at, after_dialogue_at)
        self.assertLess(after_dialogue_at, stove_commit_at)
        self.assertLess(stove_commit_at, rejected_at)

        flower = next(
            interaction
            for interaction in contract.interactions
            if interaction.name == "stonebell vase"
        )
        self.assertEqual(flower.stages[0].after_dialogue, (24, 25))

    def test_chapter_one_door_gives_progress_specific_reminders(self) -> None:
        chapter = self.chapters[0]
        (
            source_field,
            _output_field,
            source_editor,
            output_editor,
            contract,
            _first_controller,
            exit_entity,
        ) = self._layout(
            chapter,
            self.sources[chapter.chapter_id],
            self.outputs[chapter.chapter_id],
        )
        self.assertEqual(
            tuple(bit for bit, _text in contract.exit_locked_steps),
            (2, 3, 6, 1, 7, 11, 10, 4),
        )
        transition = contract.exit_transition
        self.assertIsNotNone(transition)
        assert transition is not None
        custom_texts = rico._playable_custom_texts(contract)
        self.assertNotIn("Rico is not finished here yet.<Close>", custom_texts)
        self.assertNotIn(
            "There is still something else to do first.<Close>",
            custom_texts,
        )
        authored_base = (
            struct.unpack_from(
                "<I",
                source_field.parts[rico.DIALOGUE_INDEX].data,
                0,
            )[0]
            + 1
        )
        custom_ids = {
            text: authored_base + len(chapter.blocks) + index
            for index, text in enumerate(custom_texts)
        }
        missing = rico._missing_playable_characters(chapter, source_editor)
        leader_entity = source_editor.entity_count + missing.index(
            rico.YOUNG_RICO_ID
        )
        doorway_dialogue_ids = tuple(
            custom_ids[text] for text in transition.doorway_dialogue
        )
        exit_pc = output_editor.get_script_pointer(exit_entity, 2)
        exit_action = output_editor.bytecode[exit_pc:]
        prefix = rico._playable_action_prefix(exit_pc)
        self.assertTrue(exit_action.startswith(prefix))
        branch_at = len(prefix)
        compiled_branches: list[tuple[int, int]] = []
        for bit, text in contract.exit_locked_steps:
            expected_branch = (
                b"\x02"
                + struct.pack("<H", rico.PLAYABLE_STATE_VARIABLE)
                + struct.pack("<H", 1 << bit)
                + b"\x46"
            )
            self.assertEqual(
                exit_action[branch_at : branch_at + len(expected_branch)],
                expected_branch,
            )
            target_pc = struct.unpack_from("<H", exit_action, branch_at + 6)[0]
            target_at = target_pc - exit_pc
            self.assertGreater(target_at, branch_at)
            dialogue = rico._dialogue_sequence((custom_ids[text],))
            locked_body = dialogue + rico._playable_action_finish(
                target_pc + len(dialogue)
            )
            self.assertTrue(
                exit_action.startswith(locked_body, target_at)
            )
            compiled_branches.append((1 << bit, target_at))
            branch_at += 8

        doorway_exchange = rico._chapter_one_doorway_exchange_body(
            leader_entity,
            doorway_dialogue_ids,
        )
        transition_prefix = (
            doorway_exchange + rico._chapter_one_door_transition_body()
        )
        turn_to_anna = rico._chapter_one_door_turn_to_anna_body(leader_entity)
        dialogue_beats = tuple(
            rico._dialogue_sequence((dialogue_id,))
            for dialogue_id in doorway_dialogue_ids
        )
        door_open = b"\x09" + bytes(
            (
                rico.CHAPTER_ONE_DOOR_ENTITY,
                rico.CHAPTER_ONE_DOOR_OPEN_SCRIPT | 0x20,
            )
        )
        doorway_beats = (
            turn_to_anna,
            dialogue_beats[0],
            rico.CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL,
            *dialogue_beats[1:],
        )
        doorway_cursor = 0
        for beat in doorway_beats:
            beat_at = doorway_exchange.index(beat, doorway_cursor)
            self.assertGreaterEqual(beat_at, doorway_cursor)
            doorway_cursor = beat_at + len(beat)
        self.assertEqual(
            turn_to_anna,
            b"\xFE\x17"
            + bytes((leader_entity, rico.CHAPTER_ONE_ANNA_ENTITY))
            + rico._wait(rico.CHAPTER_ONE_DOOR_TURN_TO_ANNA_FRAMES),
        )
        self.assertEqual(doorway_exchange.count(turn_to_anna), 1)
        for dialogue_beat in dialogue_beats:
            self.assertEqual(doorway_exchange.count(dialogue_beat), 1)
        self.assertEqual(
            doorway_exchange.count(rico.CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL),
            1,
        )
        self.assertEqual(transition_prefix.count(door_open), 1)
        self.assertLess(
            transition_prefix.index(dialogue_beats[-1]),
            transition_prefix.index(door_open),
        )
        self.assertEqual(
            transition.doorway_dialogue,
            (
                "<Rico>\nMom... how come I don't have a dad?<Close>",
                "Anne\nRico, you do have a father.<New><Rico>\nThen where "
                "is he?<New>Anne\nHe's... away.<New>Fighting in the war."
                "<New><Rico>\nIs he ever coming back?<New>Anne\nW-Well... "
                "that is...<New>I don't know.<New>Anne\nBut your father "
                "is a great man, Rico.<New>And someday...<New>I know "
                "you'll follow in his footsteps.<Close>",
            ),
        )
        self.assertEqual(
            transition.doorway_dialogue[1].split("<New>"),
            [
                "Anne\nRico, you do have a father.",
                "<Rico>\nThen where is he?",
                "Anne\nHe's... away.",
                "Fighting in the war.",
                "<Rico>\nIs he ever coming back?",
                "Anne\nW-Well... that is...",
                "I don't know.",
                "Anne\nBut your father is a great man, Rico.",
                "And someday...",
                "I know you'll follow in his footsteps.<Close>",
            ],
        )
        doorway_text = "\n".join(transition.doorway_dialogue)
        self.assertNotIn("when is Dad coming back from the war", doorway_text)
        self.assertNotIn("find his way back to us", doorway_text)
        routed_cases = (
            ((), contract.exit_locked_steps[0][1]),
            ((2,), contract.exit_locked_steps[1][1]),
            ((2, 3), contract.exit_locked_steps[2][1]),
            ((2, 6), contract.exit_locked_steps[1][1]),
            ((2, 3, 6), contract.exit_locked_steps[3][1]),
            ((2, 3, 6, 1), contract.exit_locked_steps[4][1]),
            ((2, 3, 6, 1, 7), contract.exit_locked_steps[5][1]),
            ((2, 3, 6, 1, 7, 11), contract.exit_locked_steps[6][1]),
            ((2, 3, 6, 1, 7, 11, 10), contract.exit_locked_steps[7][1]),
            ((2, 3, 6, 1, 7, 11, 10, 4), None),
            ((2, 3, 6, 1, 7, 11, 10, 4, 5), None),
        )
        for set_bits, expected_text in routed_cases:
            with self.subTest(set_bits=set_bits):
                state = sum(1 << bit for bit in set_bits)
                target_at = next(
                    (
                        target
                        for mask, target in compiled_branches
                        if state & mask == 0
                    ),
                    None,
                )
                if expected_text is None:
                    self.assertIsNone(target_at)
                    self.assertTrue(
                        exit_action.startswith(transition_prefix, branch_at)
                    )
                else:
                    self.assertIsNotNone(target_at)
                    self.assertTrue(
                        exit_action.startswith(
                            rico._dialog(custom_ids[expected_text]),
                            target_at,
                        )
                    )
        expected_counts: dict[str, int] = {}
        for _bit, text in contract.exit_locked_steps:
            expected_counts[text] = expected_counts.get(text, 0) + 1
        for text, count in expected_counts.items():
            self.assertIn(text, custom_ids)
            self.assertEqual(
                exit_action.count(rico._dialog(custom_ids[text])),
                count,
        )
        self.assertEqual(
            contract.exit_locked_steps[0][1],
            "<Rico>\nI can't leave Mom right now.<Close>",
        )
        self.assertIn("fill the kettle", contract.exit_locked_steps[1][1])
        self.assertIn("bucket and ladle", contract.exit_locked_steps[1][1])
        self.assertIn("turn on the stove", contract.exit_locked_steps[2][1])
        self.assertIn("stonebell", contract.exit_locked_steps[3][1])
        self.assertIn("another scoop", contract.exit_locked_steps[3][1])
        self.assertIn("water in the ladle", contract.exit_locked_steps[4][1])
        self.assertIn("soil is still dry", contract.exit_locked_steps[4][1])
        self.assertIn("woodstove valve", contract.exit_locked_steps[5][1])
        self.assertIn("room stays warm for Mom", contract.exit_locked_steps[5][1])
        self.assertNotIn("kettle is whistling", contract.exit_locked_steps[6][1])
        self.assertNotIn("chipped", contract.exit_locked_steps[6][1])
        self.assertIn("finish Mom's tea at the stove", contract.exit_locked_steps[6][1])
        self.assertIn("pinch of medicinal herbs", contract.exit_locked_steps[6][1])
        self.assertIn("pour in the hot water", contract.exit_locked_steps[6][1])
        self.assertIn("bring it to Mom", contract.exit_locked_steps[6][1])
        self.assertIn("Mom's cup of hot tea", contract.exit_locked_steps[7][1])
        self.assertIn("take it to her", contract.exit_locked_steps[7][1])
        self.assertNotIn("pendant", " ".join(
            text for _bit, text in contract.exit_locked_steps
        ).casefold())
        self.assertNotIn(
            rico._choice_dialog(custom_ids[rico.PLAYABLE_NEXT_OR_HUB_CHOICE]),
            exit_action,
        )
        self.assertNotIn(
            rico.mass_driver._set_var_bit(
                rico.PLAYABLE_STATE_VARIABLE,
                transition.bit,
            ),
            exit_action,
        )

    def test_ordered_locked_dialogue_validation_fails_closed(self) -> None:
        chapter = self.chapters[0]
        contract = rico._playable_chapter_contract(1)
        components = [
            part.data for part in parse_field(self.outputs[chapter.chapter_id]).parts
        ]
        interaction_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "Anne's bedside"
        )
        stage_index = next(
            index
            for index, stage in enumerate(
                contract.interactions[interaction_index].stages
            )
            if stage.bit == 4
        )
        return_stage = contract.interactions[interaction_index].stages[stage_index]
        steps = return_stage.locked_dialogue_steps

        def with_return_stage(stage: rico.PlayableStage) -> rico.PlayableChapter:
            interactions = list(contract.interactions)
            stages = list(interactions[interaction_index].stages)
            stages[stage_index] = stage
            interactions[interaction_index] = replace(
                interactions[interaction_index],
                stages=tuple(stages),
            )
            return replace(contract, interactions=tuple(interactions))

        malformed = (
            replace(return_stage, locked_dialogue_steps=steps[:-1]),
            replace(return_stage, locked_dialogue_steps=tuple(reversed(steps))),
            replace(
                return_stage,
                locked_dialogue_steps=((steps[0][0], ()), *steps[1:]),
            ),
        )
        for index, stage in enumerate(malformed):
            with self.subTest(malformed_ordered_dialogue=index):
                with self.assertRaisesRegex(
                    rico.RicoArcBuildError,
                    "has invalid ordered locked dialogue",
                ):
                    rico._validate_playable_contract(
                        components,
                        chapter,
                        with_return_stage(stage),
                    )

        mixed = replace(
            return_stage,
            locked_dialogue=("Anne\nThis fallback must not coexist.<Close>",),
        )
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            "mixes ordered and other locked dialogue",
        ):
            rico._validate_playable_contract(
                components,
                chapter,
                with_return_stage(mixed),
            )

        bracketed = replace(
            return_stage,
            locked_dialogue_steps=((steps[0][0], (1,)), *steps[1:]),
        )
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            r"routes screenplay prose blocks: \[1\]",
        ):
            rico._validate_playable_contract(
                components,
                chapter,
                with_return_stage(bracketed),
            )

    def test_locked_state_dialogue_matrix_validation_fails_closed(self) -> None:
        chapter = self.chapters[2]
        contract = rico._playable_chapter_contract(3)
        components = [
            part.data for part in parse_field(self.outputs[chapter.chapter_id]).parts
        ]
        interaction_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "family seal"
        )
        stage_index = next(
            index
            for index, stage in enumerate(
                contract.interactions[interaction_index].stages
            )
            if stage.bit == 4
        )
        return_stage = contract.interactions[interaction_index].stages[stage_index]
        states = return_stage.locked_dialogue_states

        def with_return_stage(stage: rico.PlayableStage) -> rico.PlayableChapter:
            interactions = list(contract.interactions)
            stages = list(interactions[interaction_index].stages)
            stages[stage_index] = stage
            interactions[interaction_index] = replace(
                interactions[interaction_index],
                stages=tuple(stages),
            )
            return replace(contract, interactions=tuple(interactions))

        malformed = (
            (
                "fallback_and_states",
                replace(
                    return_stage,
                    locked_dialogue=("Anne\nThis fallback must not coexist.<Close>",),
                ),
                "mixes fallback and state-specific locked dialogue",
            ),
            (
                "missing_state",
                replace(return_stage, locked_dialogue_states=states[:-1]),
                "does not cover every incomplete state",
            ),
            (
                "duplicate_state",
                replace(
                    return_stage,
                    locked_dialogue_states=(*states[:-1], states[0]),
                ),
                "does not cover every incomplete state",
            ),
            (
                "complete_state_is_not_locked",
                replace(
                    return_stage,
                    locked_dialogue_states=(
                        ((2, 3), states[0][1]),
                        *states[1:],
                    ),
                ),
                "has an invalid locked state",
            ),
            (
                "empty_state_dialogue",
                replace(
                    return_stage,
                    locked_dialogue_states=(
                        (states[0][0], ()),
                        *states[1:],
                    ),
                ),
                "has an invalid locked state",
            ),
        )
        for name, stage, error in malformed:
            with self.subTest(malformed_matrix=name):
                with self.assertRaisesRegex(rico.RicoArcBuildError, error):
                    rico._validate_playable_contract(
                        components,
                        chapter,
                        with_return_stage(stage),
                    )

        bracketed_state = replace(
            return_stage,
            locked_dialogue_states=(
                (states[0][0], (1,)),
                *states[1:],
            ),
        )
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            r"routes screenplay prose blocks: \[1\]",
        ):
            rico._validate_playable_contract(
                components,
                chapter,
                with_return_stage(bracketed_state),
            )

    def test_chapter_one_rejects_action_points_on_walkmesh_boundaries(self) -> None:
        chapter = self.chapters[0]
        contract = rico._playable_chapter_contract(1)
        anna_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "Anne's bedside"
        )
        interactions = list(contract.interactions)
        interactions[anna_index] = replace(
            interactions[anna_index],
            x=27,
            z=-173,
            triangle=75,
        )
        interactions = [
            interaction
            for interaction in interactions
            if interaction.name != "gate window"
        ]
        boundary_contract = replace(contract, interactions=tuple(interactions))
        components = [
            part.data for part in parse_field(self.outputs[1]).parts
        ]
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            "not strictly inside walkmesh triangle 75",
        ):
            rico._validate_playable_contract(
                components,
                chapter,
                boundary_contract,
            )

    def test_recessed_props_require_their_reachable_walkmesh_anchors(self) -> None:
        chapter = self.chapters[0]
        contract = rico._playable_chapter_contract(1)
        window_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "cold window"
        )
        components = [
            part.data for part in parse_field(self.outputs[1]).parts
        ]

        interactions = list(contract.interactions)
        interactions[window_index] = replace(
            interactions[window_index],
            walkmesh_anchor=None,
        )
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            r"cold window \(198,-208\) left walkmesh triangle 25",
        ):
            rico._validate_playable_contract(
                components,
                chapter,
                replace(contract, interactions=tuple(interactions)),
            )

        interactions[window_index] = replace(
            interactions[window_index],
            walkmesh_anchor=(173, -197),
        )
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            "walkmesh anchor left its effective interaction box",
        ):
            rico._validate_playable_contract(
                components,
                chapter,
                replace(contract, interactions=tuple(interactions)),
            )

        heater_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "room heater"
        )
        interactions = list(contract.interactions)
        interactions[heater_index] = replace(
            interactions[heater_index],
            walkmesh_anchor=None,
        )
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            r"room heater \(-11,-18\) left walkmesh triangle 45",
        ):
            rico._validate_playable_contract(
                components,
                chapter,
                replace(contract, interactions=tuple(interactions)),
            )

        desk_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "reading desk"
        )
        interactions = list(contract.interactions)
        interactions[desk_index] = replace(
            interactions[desk_index],
            walkmesh_anchor=None,
        )
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            r"reading desk \(226,-85\) left walkmesh triangle 51",
        ):
            rico._validate_playable_contract(
                components,
                chapter,
                replace(contract, interactions=tuple(interactions)),
            )

        interactions = list(contract.interactions)
        interactions[desk_index] = replace(
            interactions[desk_index],
            walkmesh_anchor=(202, -60),
        )
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            "Only Chapter 1's exact audited recessed carriers",
        ):
            rico._validate_playable_contract(
                components,
                chapter,
                replace(contract, interactions=tuple(interactions)),
            )

        anna_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "Anne's bedside"
        )
        interactions = list(contract.interactions)
        interactions[anna_index] = replace(
            interactions[anna_index],
            x=27,
            z=-173,
            triangle=75,
            walkmesh_anchor=(35, -140),
        )
        interactions = [
            interaction
            for interaction in interactions
            if interaction.name != "gate window"
        ]
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            "Only Chapter 1's exact audited recessed carriers",
        ):
            rico._validate_playable_contract(
                components,
                chapter,
                replace(contract, interactions=tuple(interactions)),
            )

    def test_chapter_one_exit_reminder_bits_fail_closed_on_contract_drift(self) -> None:
        chapter = self.chapters[0]
        contract = rico._playable_chapter_contract(chapter.chapter_id)
        components = [
            part.data
            for part in parse_field(self.outputs[chapter.chapter_id]).parts
        ]
        steps = contract.exit_locked_steps

        duplicate_steps = (*steps[:-1], (steps[-2][0], steps[-1][1]))
        duplicate = replace(contract, exit_locked_steps=duplicate_steps)
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            "exit reminder bits must be unique",
        ):
            rico._validate_playable_contract(components, chapter, duplicate)

        mismatched_steps = (*steps[:-1], (8, steps[-1][1]))
        mismatched = replace(contract, exit_locked_steps=mismatched_steps)
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            "exit reminder bits must match its player-completed requirements",
        ):
            rico._validate_playable_contract(components, chapter, mismatched)

        transition = contract.exit_transition
        self.assertIsNotNone(transition)
        assert transition is not None
        for doorway_dialogue in (
            (),
            transition.doorway_dialogue[:-1],
            (*transition.doorway_dialogue, "Anne\nExtra.<Close>"),
        ):
            with self.subTest(doorway_blocks=len(doorway_dialogue)):
                malformed = replace(
                    contract,
                    exit_transition=replace(
                        transition,
                        doorway_dialogue=doorway_dialogue,
                    ),
                )
                with self.assertRaisesRegex(
                    rico.RicoArcBuildError,
                    "has an invalid exit transition",
                ):
                    rico._validate_playable_contract(
                        components,
                        chapter,
                        malformed,
                    )

    def test_chapter_one_exit_initializer_is_exact_threshold_controller(self) -> None:
        chapter = self.chapters[0]
        (
            _source_field,
            _output_field,
            _source_editor,
            output_editor,
            contract,
            _first_controller,
            exit_entity,
        ) = self._layout(
            chapter,
            self.sources[chapter.chapter_id],
            self.outputs[chapter.chapter_id],
        )
        self.assertEqual(
            (contract.exit_x, contract.exit_z, contract.exit_triangle),
            (70, 76, 59),
        )
        self.assertEqual(
            (
                contract.exit_interaction_half_width,
                contract.exit_interaction_half_depth,
                contract.exit_requires_facing,
            ),
            (6, 6, False),
        )
        exit_init_pc = output_editor.get_script_pointer(exit_entity, 0)
        exit_action_pc = output_editor.get_script_pointer(exit_entity, 2)
        self.assertEqual(
            output_editor.bytecode[exit_init_pc:exit_action_pc],
            rico._playable_exit_controller_init(contract),
        )

    def test_chapter_entries_are_clear_of_effective_interaction_boxes(self) -> None:
        for chapter in self.chapters:
            entry_x, entry_z, _triangle = rico.PLAYABLE_ENTRY_POSITIONS[
                chapter.chapter_id
            ]
            contract = rico._playable_chapter_contract(chapter.chapter_id)
            for interaction in contract.interactions:
                with self.subTest(
                    chapter=chapter.chapter_id,
                    interaction=interaction.name,
                ):
                    effective_x = interaction.interaction_half_width * 2 + 0x10
                    effective_z = interaction.interaction_half_depth * 2 + 0x10
                    self.assertTrue(
                        abs(entry_x - interaction.x) > effective_x
                        or abs(entry_z - interaction.z) > effective_z
                    )

    def test_interaction_actors_share_the_controller_action_at_visible_positions(self) -> None:
        expected_bindings = {
            1: {"Anne's bedside": (4,)},
            2: {"Hammer": (rico.CHAPTER_TWO_HAMMER_ENTITY,), "Fei": (1,)},
            3: {"Sigmund": (25,)},
            4: {"Sigmund": (14,)},
            7: {"Fei": (1,)},
        }
        self.assertEqual(rico.INTERACTION_ACTOR_BINDINGS, expected_bindings)
        visual_positions = {
            (1, "Anne's bedside", 4): (
                "2d",
                rico.CHAPTER_ONE_ANNA_VISUAL_POSITION[:2],
            ),
            (2, "Hammer", rico.CHAPTER_TWO_HAMMER_ENTITY): (
                "2d",
                rico.CHAPTER_TWO_HAMMER_STAGE_POSITION[:2],
            ),
            (2, "Fei", 1): ("header", (-70, 181)),
            (3, "Sigmund", 25): ("2d", (0, 223)),
            (4, "Sigmund", 14): ("3d", (-190, 0, -10)),
            (7, "Fei", 1): ("header", (47, 116)),
        }

        for chapter in self.chapters:
            if chapter.chapter_id not in expected_bindings:
                continue
            (
                _source_field,
                output_field,
                _source_editor,
                output_editor,
                contract,
                first_controller,
                _exit_entity,
            ) = self._layout(
                chapter,
                self.sources[chapter.chapter_id],
                self.outputs[chapter.chapter_id],
            )
            for interaction_name, entities in expected_bindings[
                chapter.chapter_id
            ].items():
                interaction_index = next(
                    index
                    for index, interaction in enumerate(contract.interactions)
                    if interaction.name == interaction_name
                )
                action_pc = output_editor.get_script_pointer(
                    first_controller + interaction_index,
                    2,
                )
                interaction = contract.interactions[interaction_index]
                stop_pc = output_editor.get_script_pointer(0, 2)
                for entity in entities:
                    with self.subTest(
                        chapter=chapter.chapter_id,
                        interaction=interaction_name,
                        entity=entity,
                    ):
                        actor_action_pc = output_editor.get_script_pointer(
                            entity,
                            2,
                        )
                        if (
                            chapter.chapter_id == 2
                            and interaction_name == "Hammer"
                            and entity == rico.CHAPTER_TWO_HAMMER_ENTITY
                        ):
                            actor_gate = (
                                rico._chapter_two_hammer_actor_action_gate(
                                    actor_action_pc,
                                    action_pc,
                                )
                            )
                            self.assertEqual(
                                output_editor.bytecode[
                                    actor_action_pc : actor_action_pc
                                    + len(actor_gate)
                                ],
                                actor_gate,
                            )
                        elif interaction.hide_bound_actors_until_active:
                            actor_gate = rico._playable_actor_action_gate(
                                actor_action_pc,
                                interaction.activation_required_bits,
                                action_pc,
                            )
                            self.assertEqual(
                                output_editor.bytecode[
                                    actor_action_pc : actor_action_pc
                                    + len(actor_gate)
                                ],
                                actor_gate,
                            )
                        else:
                            self.assertEqual(actor_action_pc, action_pc)
                        kind, position = visual_positions[
                            (chapter.chapter_id, interaction_name, entity)
                        ]
                        if kind == "header":
                            record = 0x190 + entity * 16
                            actual = (
                                struct.unpack_from(
                                    "<h", output_field.header, record + 8
                                )[0],
                                struct.unpack_from(
                                    "<h", output_field.header, record + 12
                                )[0],
                            )
                            self.assertEqual(actual, position)
                            continue
                        init_pc = output_editor.get_script_pointer(entity, 0)
                        if kind in ("2d", "2d_after_flags"):
                            x, z = position
                            expected_position = (
                                b"\x19"
                                + struct.pack("<h", x)
                                + struct.pack("<h", z)
                                + b"\xC0"
                            )
                        else:
                            x, y, z = position
                            expected_position = (
                                b"\xFE\x1C"
                                + struct.pack("<hhh", x, y, z)
                            )
                        position_offset = 6 if kind == "2d_after_flags" else 3
                        self.assertEqual(
                            output_editor.bytecode[
                                init_pc
                                + position_offset : init_pc
                                + position_offset
                                + len(expected_position)
                            ],
                            expected_position,
                        )

    def test_chapter_two_uses_authentic_hammer_and_a_finite_stair_route(self) -> None:
        source_field = parse_field(self.sources[2])
        output_field = parse_field(self.outputs[2])
        source_components = tuple(part.data for part in source_field.parts)
        output_components = tuple(part.data for part in output_field.parts)
        output_editor = AtelScript(output_components[rico.SCRIPT_INDEX])

        hammer = rico.CHAPTER_TWO_HAMMER_ENTITY
        self.assertEqual(hammer, 19)
        self.assertEqual(rico.CHAPTER_TWO_HAMMER_ACTOR_BANK, 4)
        self.assertEqual(rico.CHAPTER_TWO_HAMMER_STATE_VARIABLE, 0x03EE)
        self.assertEqual(rico.CHAPTER_TWO_HAMMER_ARRIVED_BIT, 0)
        self.assertEqual(
            struct.unpack_from(
                "<4H",
                output_field.header,
                rico.CHAPTER_TWO_HAMMER_ACTOR_BANK * 8,
            ),
            rico.CHAPTER_TWO_HAMMER_VRAM_MAPPING,
        )
        hammer_record = 0x190 + hammer * 16
        self.assertEqual(
            (
                struct.unpack_from("<h", output_field.header, hammer_record + 8)[0],
                struct.unpack_from("<h", output_field.header, hammer_record + 12)[0],
            ),
            rico.CHAPTER_TWO_HAMMER_STAGE_POSITION[:2],
        )

        expected_init = rico._chapter_two_hammer_init()
        init_pc = output_editor.get_script_pointer(hammer, 0)
        self.assertEqual(
            output_editor.bytecode[init_pc : init_pc + len(expected_init)],
            expected_init,
        )
        route_pc = output_editor.get_script_pointer(hammer, 1)
        expected_route = rico._chapter_two_hammer_stair_route(route_pc)
        self.assertEqual(
            output_editor.bytecode[route_pc : route_pc + len(expected_route)],
            expected_route,
        )
        self.assertEqual(expected_route.count(b"\x4B"), 2)
        self.assertEqual(expected_route.count(b"\x19"), 3)
        arrived_commit = rico.mass_driver._set_var_bit(
            rico.CHAPTER_TWO_HAMMER_STATE_VARIABLE,
            rico.CHAPTER_TWO_HAMMER_ARRIVED_BIT,
        )
        self.assertEqual(expected_route.count(arrived_commit), 1)
        self.assertLess(expected_route.index(b"\x4B"), expected_route.index(arrived_commit))
        for x, z, _triangle in rico.CHAPTER_TWO_HAMMER_ROUTE:
            position = rico._s16(x) + rico._s16(z)
            self.assertIn(
                b"\x4B"
                + position
                + b"\xC0"
                + rico._immediate(rico.CHAPTER_TWO_HAMMER_ROUTE_MAX_STEPS)
                + b"\x19"
                + position
                + b"\xC0",
                expected_route,
            )
        end_x, end_z, _end_triangle = rico.CHAPTER_TWO_HAMMER_ROUTE[-1]
        reload_snap = (
            b"\x19"
            + rico._s16(end_x)
            + rico._s16(end_z)
            + b"\xC0"
            + rico.PLAYABLE_ACTOR_SOLID_FLAGS
            + b"\x5F\x04\x5B"
        )
        self.assertEqual(expected_route.count(reload_snap), 1)
        self.assertLess(expected_route.index(reload_snap), expected_route.index(b"\x4B"))
        self.assertTrue(
            expected_route.endswith(
                rico.PLAYABLE_ACTOR_SOLID_FLAGS + b"\x5F\x04\x5B"
            )
        )

        contract = rico._playable_chapter_contract(2)
        source_editor = AtelScript(
            rico._normalize_playable_party_script(
                self.chapters[1],
                source_components[rico.SCRIPT_INDEX],
            )
        )
        first_controller = source_editor.entity_count + len(
            rico._missing_playable_characters(
                self.chapters[1],
                source_editor,
            )
        )
        hammer_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "Hammer"
        )
        hammer_interaction = contract.interactions[hammer_index]
        controller = first_controller + hammer_index
        controller_init = rico.mass_driver._pointed_script_body(
            output_editor,
            output_editor.get_script_pointer(controller, 0),
        )
        self.assertEqual(
            controller_init,
            rico._playable_controller_init(
                hammer_interaction.x,
                hammer_interaction.z,
                half_width=hammer_interaction.interaction_half_width,
                half_depth=hammer_interaction.interaction_half_depth,
                requires_facing=hammer_interaction.requires_facing,
                initially_disabled=True,
            ),
        )
        self.assertIn(
            b"\x19"
            + rico._s16(rico.PLAYABLE_CONTROLLER_PARK_POSITION[0])
            + rico._s16(rico.PLAYABLE_CONTROLLER_PARK_POSITION[1])
            + b"\xC0",
            controller_init,
        )
        controller_gate_pc = output_editor.get_script_pointer(controller, 1)
        self.assertEqual(
            rico.mass_driver._pointed_script_body(
                output_editor,
                controller_gate_pc,
            ),
            rico._chapter_two_hammer_controller_gate(
                controller_gate_pc,
                hammer_interaction.x,
                hammer_interaction.z,
            ),
        )
        hammer_action_pc = output_editor.get_script_pointer(hammer, 2)
        controller_action_pc = output_editor.get_script_pointer(controller, 2)
        self.assertEqual(
            rico.mass_driver._pointed_script_body(
                output_editor,
                hammer_action_pc,
            ),
            rico._chapter_two_hammer_actor_action_gate(
                hammer_action_pc,
                controller_action_pc,
            ),
        )

        suzarn_init_pc = output_editor.get_script_pointer(4, 0)
        self.assertEqual(
            output_editor.bytecode[
                suzarn_init_pc : suzarn_init_pc + len(rico.INERT_HIDDEN_INIT)
            ],
            rico.INERT_HIDDEN_INIT,
        )
        source_actor_banks = rico.mass_driver._indexed_bundle_entries(
            source_components[rico.mass_driver.ACTOR_INDEX]
        )
        output_actor_banks = rico.mass_driver._indexed_bundle_entries(
            output_components[rico.mass_driver.ACTOR_INDEX]
        )
        source_sprite_banks = rico.mass_driver._indexed_bundle_entries(
            source_components[rico.mass_driver.SPRITE_INDEX]
        )
        output_sprite_banks = rico.mass_driver._indexed_bundle_entries(
            output_components[rico.mass_driver.SPRITE_INDEX]
        )
        bank = rico.CHAPTER_TWO_HAMMER_ACTOR_BANK
        self.assertEqual(output_actor_banks[bank], source_actor_banks[bank])
        self.assertEqual(output_sprite_banks[bank], source_sprite_banks[bank])
        self.assertEqual(
            (len(output_actor_banks[bank]), hashlib.sha256(output_actor_banks[bank]).hexdigest()),
            (
                rico.CHAPTER_TWO_HAMMER_ACTOR_BANK_SIZE,
                rico.CHAPTER_TWO_HAMMER_ACTOR_BANK_SHA256,
            ),
        )
        self.assertEqual(
            (len(output_sprite_banks[bank]), hashlib.sha256(output_sprite_banks[bank]).hexdigest()),
            (
                rico.CHAPTER_TWO_HAMMER_SPRITE_BANK_SIZE,
                rico.CHAPTER_TWO_HAMMER_SPRITE_BANK_SHA256,
            ),
        )

    def test_audited_donor_managers_have_inert_initializers(self) -> None:
        expected_hazards = {
            218: (4, 5, 6, 7, 20, 21, 22, 23, 24, 25, 27),
            236: (13, 15, 16, 18, 19, 26, 28),
            237: (13, 16, 19, 20, 22, 23, 24, 26, 32),
            235: (4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17),
            232: (4, 6, 7, 8, 9, 10, 11, 12, 15, 16),
            298: (12, 13, 14, 16),
        }
        self.assertEqual(rico.HAZARDOUS_DONOR_INIT_ENTITIES, expected_hazards)
        self.assertEqual(rico.INERT_HIDDEN_INIT, b"\xBC\x23\x2A\x00")
        chapters_by_donor = {
            chapter.donor_field: chapter for chapter in self.chapters
        }
        for donor_field, entities in expected_hazards.items():
            chapter = chapters_by_donor[donor_field]
            output_editor = AtelScript(
                parse_field(self.outputs[chapter.chapter_id]).parts[
                    rico.SCRIPT_INDEX
                ].data
            )
            for entity in entities:
                with self.subTest(donor=donor_field, entity=entity):
                    init_pc = output_editor.get_script_pointer(entity, 0)
                    self.assertEqual(
                        output_editor.bytecode[
                            init_pc : init_pc + len(rico.INERT_HIDDEN_INIT)
                        ],
                        rico.INERT_HIDDEN_INIT,
                    )

    def test_chapter_one_uses_one_young_rico_and_retires_the_cutscene_double(self) -> None:
        chapter = self.chapters[0]
        (
            _source_field,
            _output_field,
            source_editor,
            output_editor,
            _contract,
            _first_controller,
            _exit_entity,
        ) = self._layout(
            chapter,
            self.sources[chapter.chapter_id],
            self.outputs[chapter.chapter_id],
        )
        missing = rico._missing_playable_characters(chapter, source_editor)
        leader_entity = source_editor.entity_count + missing.index(rico.YOUNG_RICO_ID)
        entry_x, entry_z, _triangle = rico.PLAYABLE_ENTRY_POSITIONS[1]
        expected_init = rico._young_rico_party_init(entry_x, entry_z)
        leader_init_pc = output_editor.get_script_pointer(leader_entity, 0)
        self.assertEqual(
            output_editor.bytecode[
                leader_init_pc : leader_init_pc + len(expected_init)
            ],
            expected_init,
        )
        self.assertTrue(
            expected_init.startswith(
                b"\x16"
                + rico._immediate(rico.YOUNG_RICO_ID)
                + b"\x0B"
                + rico._immediate(1)
                + b"\xFE\x0D"
                + rico._immediate(rico.RICO_ID)
            )
        )

        cutscene_entity = 5
        cutscene_init_pc = output_editor.get_script_pointer(cutscene_entity, 0)
        self.assertEqual(
            output_editor.bytecode[
                cutscene_init_pc : cutscene_init_pc + len(rico.INERT_HIDDEN_INIT)
            ],
            rico.INERT_HIDDEN_INIT,
        )
        stop_pc = output_editor.get_script_pointer(0, 2)
        disable_pc = output_editor.get_script_pointer(cutscene_entity, 1)
        self.assertEqual(
            output_editor.bytecode[
                disable_pc : disable_pc + len(rico.DISABLE_DIALOGUE_UPDATE)
            ],
            rico.DISABLE_DIALOGUE_UPDATE,
        )
        for script_index in range(2, 32):
            self.assertEqual(
                output_editor.get_script_pointer(cutscene_entity, script_index),
                stop_pc,
            )

    def test_chapter_one_seals_the_cutscene_door_at_its_inner_threshold(self) -> None:
        chapter = self.chapters[0]
        source_field = parse_field(self.sources[chapter.chapter_id])
        output_field = parse_field(self.outputs[chapter.chapter_id])
        source = source_field.parts[1].data
        output = output_field.parts[1].data

        self.assertEqual(
            (len(source), hashlib.sha256(source).hexdigest()),
            (
                rico.CHAPTER_ONE_WALKMESH_SIZE,
                rico.CHAPTER_ONE_WALKMESH_SHA256,
            ),
        )
        self.assertEqual(output, rico._seal_chapter_one_house_door(source))
        self.assertEqual(
            hashlib.sha256(output).hexdigest(),
            rico.CHAPTER_ONE_SEALED_WALKMESH_SHA256,
        )
        self.assertEqual(
            {
                index
                for index, (before, after) in enumerate(zip(source, output))
                if before != after
            },
            {0x36A, 0x36B, 0x482, 0x483},
        )

        # Geometry and materials remain byte-for-byte semantic matches; only
        # the reciprocal t59/t79 neighbor words become boundary markers.
        self.assertEqual(
            rico._walkmesh_layer(source, 0),
            rico._walkmesh_layer(output, 0),
        )
        triangle_offset = rico.CHAPTER_ONE_WALKMESH_TRIANGLE_OFFSET
        for triangle, slot, neighbor in rico.CHAPTER_ONE_DOOR_NEIGHBOR_LINKS:
            record = triangle_offset + triangle * 14
            self.assertEqual(
                struct.unpack_from("<h", source, record + 6 + slot * 2)[0],
                neighbor,
            )
            self.assertEqual(
                struct.unpack_from("<h", output, record + 6 + slot * 2)[0],
                -1,
            )
            self.assertEqual(
                struct.unpack_from("<H", output, record + 12)[0],
                1,
            )

        def reachable_triangles(walkmesh: bytes) -> set[int]:
            reachable = {rico.PLAYABLE_ENTRY_POSITIONS[1][2]}
            pending = list(reachable)
            while pending:
                current = pending.pop()
                record = triangle_offset + current * 14
                for neighbor in struct.unpack_from("<3h", walkmesh, record + 6):
                    if neighbor >= 0 and neighbor not in reachable:
                        reachable.add(neighbor)
                        pending.append(neighbor)
            return reachable

        reachable = reachable_triangles(output)
        self.assertEqual(
            set(range(87)) - reachable,
            rico.CHAPTER_ONE_DOOR_EXTERIOR_TRIANGLES,
        )
        contract = rico._playable_chapter_contract(1)
        self.assertTrue(
            {
                rico.PLAYABLE_ENTRY_POSITIONS[1][2],
                contract.exit_triangle,
                *(interaction.triangle for interaction in contract.interactions),
            }
            <= reachable
        )
        triangles = rico._walkmesh_layer(output, 0)
        self.assertTrue(
            rico._point_inside_triangle(
                rico.CHAPTER_ONE_DOOR_REPRO_POSITION,
                triangles[78],
            )
        )
        self.assertNotIn(78, reachable)

        # The authentic visual leaf and its initializer are untouched.
        door_entity = 6
        door_record = 0x190 + door_entity * 16
        self.assertEqual(
            output_field.header[door_record : door_record + 16],
            source_field.header[door_record : door_record + 16],
        )
        self.assertEqual(output_field.parts[2].data, source_field.parts[2].data)
        source_editor = AtelScript(source_field.parts[rico.SCRIPT_INDEX].data)
        output_editor = AtelScript(output_field.parts[rico.SCRIPT_INDEX].data)
        self.assertEqual(
            output_editor.bytecode[
                output_editor.get_script_pointer(door_entity, 0) :
                output_editor.get_script_pointer(door_entity, 0) + 3
            ],
            source_editor.bytecode[
                source_editor.get_script_pointer(door_entity, 0) :
                source_editor.get_script_pointer(door_entity, 0) + 3
            ],
        )
        self.assertEqual(
            output_editor.bytecode[
                output_editor.get_script_pointer(door_entity, 0) :
                output_editor.get_script_pointer(door_entity, 0) + 3
            ],
            b"\xBC\x2A\x00",
        )

    def test_chapter_one_door_departure_is_finite_and_interior_only(self) -> None:
        chapter = self.chapters[0]
        (
            _source_field,
            _output_field,
            source_editor,
            output_editor,
            _contract,
            _first_controller,
            _exit_entity,
        ) = self._layout(
            chapter,
            self.sources[chapter.chapter_id],
            self.outputs[chapter.chapter_id],
        )
        missing = rico._missing_playable_characters(chapter, source_editor)
        leader_entity = source_editor.entity_count + missing.index(
            rico.YOUNG_RICO_ID
        )
        departure = rico._chapter_one_door_departure_body()

        self.assertEqual(rico.CHAPTER_ONE_DOOR_DEPARTURE_MAX_STEPS, 16)
        self.assertEqual(
            rico.CHAPTER_ONE_DOOR_REPOSITION,
            rico.CHAPTER_ONE_EXIT_POSITION,
        )
        self.assertEqual(
            departure,
            bytes.fromhex("4B 46 00 4C 00 C0 10 80 00"),
        )
        self.assertEqual(departure.count(b"\x4B"), 1)
        for forbidden_opcode in (b"\x19", b"\x1A", b"\xF8"):
            self.assertNotIn(forbidden_opcode, departure)

        departure_pc = output_editor.get_script_pointer(
            leader_entity,
            rico.CHAPTER_ONE_DOOR_DEPARTURE_SCRIPT,
        )
        self.assertEqual(
            output_editor.bytecode[
                departure_pc : departure_pc + len(departure)
            ],
            departure,
        )

    def test_chapter_one_aliases_missing_run_animation_to_true_walk(self) -> None:
        source = parse_field(self.sources[1]).parts[rico.mass_driver.ACTOR_INDEX].data
        output = parse_field(self.outputs[1]).parts[rico.mass_driver.ACTOR_INDEX].data
        aliased = rico._alias_young_rico_run_to_walk(source)
        start = rico.YOUNG_RICO_ANIMATION_HEADER_OFFSET
        end = start + len(rico.YOUNG_RICO_NPC_ANIMATION_HEADER)

        self.assertEqual(
            hashlib.sha256(source).hexdigest(),
            rico.YOUNG_RICO_ACTOR_COMPONENT_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(aliased).hexdigest(),
            rico.YOUNG_RICO_PLAYER_ACTOR_COMPONENT_SHA256,
        )
        self.assertEqual(source[start:end], rico.YOUNG_RICO_NPC_ANIMATION_HEADER)
        self.assertEqual(aliased[start:end], rico.YOUNG_RICO_PLAYER_ANIMATION_HEADER)
        self.assertEqual(
            {
                index
                for index, (before, after) in enumerate(zip(source, aliased))
                if before != after
            },
            {start, start + 6},
        )
        self.assertEqual(output, aliased)
        self.assertEqual(len(output), 4_184)
        self.assertEqual(
            hashlib.sha256(output).hexdigest(),
            rico.YOUNG_RICO_PLAYER_ACTOR_COMPONENT_SHA256,
        )
        bank_offsets = struct.unpack_from("<2I", output, 4)
        self.assertEqual(bank_offsets, (0x0C, 0xAA0))
        self.assertTrue(all(offset % 4 == 0 for offset in bank_offsets))
        source_banks = rico.mass_driver._indexed_bundle_entries(source)
        banks = rico.mass_driver._indexed_bundle_entries(output)
        self.assertEqual(banks[0], source_banks[0])
        self.assertEqual(
            hashlib.sha256(banks[0]).hexdigest(),
            rico.CHAPTER_ONE_ANNA_ACTOR_BANK_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(
                banks[rico.YOUNG_RICO_ACTOR_BANK_INDEX]
            ).hexdigest(),
            rico.YOUNG_RICO_PLAYER_ACTOR_BANK_SHA256,
        )
        # Field-script button words are physical PSX masks.  Cross confirms
        # interactions; Circle is the run/cancel input being neutralized.
        self.assertEqual(rico.PAD_MASK_CROSS, 0x0020)
        self.assertEqual(rico.PAD_MASK_CIRCLE, 0x0040)

    def test_chapter_one_stages_native_standing_anna_at_the_bed_foot(self) -> None:
        chapter = self.chapters[0]
        (
            source_field,
            output_field,
            source_editor,
            output_editor,
            contract,
            first_controller,
            _exit_entity,
        ) = self._layout(
            chapter,
            self.sources[1],
            self.outputs[1],
        )
        source_components = [part.data for part in source_field.parts]
        output_components = [part.data for part in output_field.parts]
        rico._validate_chapter_one_anna_source(
            source_field.header,
            source_components,
        )

        record = 0x190 + rico.CHAPTER_ONE_ANNA_ENTITY * 16
        self.assertEqual(
            source_field.header[record : record + 16],
            rico.CHAPTER_ONE_ANNA_HEADER_RECORD,
        )
        self.assertEqual(
            output_field.header[record : record + 16],
            rico.CHAPTER_ONE_ANNA_HEADER_RECORD,
        )
        source_actor_banks = rico.mass_driver._indexed_bundle_entries(
            source_components[rico.mass_driver.ACTOR_INDEX]
        )
        output_actor_banks = rico.mass_driver._indexed_bundle_entries(
            output_components[rico.mass_driver.ACTOR_INDEX]
        )
        output_actor_bank_offsets = struct.unpack_from(
            "<2I",
            output_components[rico.mass_driver.ACTOR_INDEX],
            4,
        )
        self.assertEqual(output_actor_bank_offsets, (0x0C, 0xAA0))
        self.assertTrue(
            all(offset % 4 == 0 for offset in output_actor_bank_offsets)
        )
        source_sprite_banks = rico.mass_driver._indexed_bundle_entries(
            source_components[rico.mass_driver.SPRITE_INDEX]
        )
        output_sprite_banks = rico.mass_driver._indexed_bundle_entries(
            output_components[rico.mass_driver.SPRITE_INDEX]
        )
        self.assertEqual(
            output_components[rico.mass_driver.ACTOR_INDEX],
            rico._alias_young_rico_run_to_walk(
                source_components[rico.mass_driver.ACTOR_INDEX]
            ),
        )
        self.assertEqual(source_actor_banks[0], output_actor_banks[0])
        self.assertNotEqual(source_actor_banks[1], output_actor_banks[1])
        self.assertEqual(
            source_components[rico.mass_driver.SPRITE_INDEX],
            output_components[rico.mass_driver.SPRITE_INDEX],
        )
        self.assertEqual(source_sprite_banks[0], output_sprite_banks[0])
        self.assertEqual(
            len(output_actor_banks[0]),
            rico.CHAPTER_ONE_ANNA_ACTOR_BANK_SIZE,
        )
        self.assertEqual(
            hashlib.sha256(output_actor_banks[0]).hexdigest(),
            rico.CHAPTER_ONE_ANNA_ACTOR_BANK_SHA256,
        )
        self.assertEqual(
            len(output_sprite_banks[0]),
            rico.CHAPTER_ONE_ANNA_SPRITE_BANK_SIZE,
        )
        self.assertEqual(
            hashlib.sha256(output_sprite_banks[0]).hexdigest(),
            rico.CHAPTER_ONE_ANNA_SPRITE_BANK_SHA256,
        )

        source_update_pc = source_editor.get_script_pointer(
            rico.CHAPTER_ONE_ANNA_ENTITY,
            1,
        )
        self.assertEqual(source_update_pc, rico.CHAPTER_ONE_ANNA_UPDATE_PC)
        self.assertEqual(
            rico.mass_driver._pointed_script_body(
                source_editor,
                source_update_pc,
            ),
            rico.CHAPTER_ONE_ANNA_SOURCE_UPDATE,
        )
        native_cough_scripts = tuple(
            rico.mass_driver._pointed_script_body(
                source_editor,
                source_editor.get_script_pointer(
                    rico.CHAPTER_ONE_ANNA_ENTITY,
                    script_index,
                ),
            )
            for script_index in (9, 12)
        )
        self.assertTrue(
            all(b"\x2C\x02" in body for body in native_cough_scripts)
        )
        self.assertIn(b"\x2C\xFF", native_cough_scripts[1])
        init_pc = output_editor.get_script_pointer(rico.CHAPTER_ONE_ANNA_ENTITY, 0)
        self.assertEqual(
            output_editor.bytecode[
                init_pc : init_pc + len(rico.CHAPTER_ONE_ANNA_PLAYABLE_INIT)
            ],
            rico.CHAPTER_ONE_ANNA_PLAYABLE_INIT,
        )
        self.assertNotIn(
            rico.PLAYABLE_ACTOR_GHOST_FLAGS,
            rico.CHAPTER_ONE_ANNA_PLAYABLE_INIT,
        )
        self.assertEqual(
            rico.CHAPTER_ONE_ANNA_PLAYABLE_INIT,
            bytes.fromhex(
                "0B 00 80 19 23 00 74 FF C0 5F 03 2A 00"
            ),
        )
        self.assertTrue(
            rico.CHAPTER_ONE_ANNA_PLAYABLE_INIT.endswith(b"\x2A\x00")
        )
        self.assertNotIn(b"\x2C", rico.CHAPTER_ONE_ANNA_PLAYABLE_INIT)
        update_pc = output_editor.get_script_pointer(
            rico.CHAPTER_ONE_ANNA_ENTITY,
            1,
        )
        expected_update = rico._chapter_one_anna_ambient_update(update_pc)
        self.assertEqual(rico.CHAPTER_ONE_ANNA_COUGH_INTERVAL_FRAMES, 900)
        self.assertEqual(
            rico.CHAPTER_ONE_ANNA_COUGH_ONCE,
            bytes.fromhex("5D 02 5E"),
        )
        self.assertEqual(
            rico.mass_driver._pointed_script_body(output_editor, update_pc),
            expected_update,
        )
        self.assertEqual(
            expected_update,
            bytes.fromhex("5D 02 5E")
            + rico._wait(rico.CHAPTER_ONE_ANNA_COUGH_INTERVAL_FRAMES)
            + rico._jump(update_pc),
        )
        self.assertTrue(expected_update.startswith(bytes.fromhex("5D 02 5E")))
        self.assertEqual(expected_update.count(bytes.fromhex("5D 02 5E")), 1)
        interaction_cough_pc = output_editor.get_script_pointer(
            rico.CHAPTER_ONE_ANNA_ENTITY,
            rico.CHAPTER_ONE_ANNA_INTERACTION_COUGH_SCRIPT,
        )
        self.assertEqual(
            rico.mass_driver._pointed_script_body(
                output_editor,
                interaction_cough_pc,
            ),
            rico.CHAPTER_ONE_ANNA_COUGH_ONCE + b"\x00",
        )
        self.assertEqual(
            rico.CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL,
            bytes.fromhex("09 04 3F"),
        )
        expected_cough_calls = {
            "Anne's bedside": 10,
            "cooking counter": 2,
            "stonebell vase": 1,
            "reading desk": 1,
        }
        actual_cough_calls = 0
        for index, interaction in enumerate(contract.interactions):
            controller = first_controller + index
            action_pc = output_editor.get_script_pointer(controller, 2)
            action_end = output_editor.get_script_pointer(controller + 1, 0)
            call_count = output_editor.bytecode[action_pc:action_end].count(
                rico.CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL
            )
            self.assertEqual(
                call_count,
                expected_cough_calls.get(interaction.name, 0),
                interaction.name,
            )
            actual_cough_calls += call_count
        self.assertEqual(actual_cough_calls, 14)
        reading_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "reading desk"
        )
        reading_controller = first_controller + reading_index
        reading_action_pc = output_editor.get_script_pointer(
            reading_controller,
            2,
        )
        next_controller_init_pc = output_editor.get_script_pointer(
            reading_controller + 1,
            0,
        )
        reading_action_allocation = output_editor.bytecode[
            reading_action_pc:next_controller_init_pc
        ]
        self.assertEqual(
            rico.CHAPTER_ONE_READING_DESK_ACTION_LAYOUT_PADDING,
            40,
        )
        self.assertEqual(
            reading_action_allocation[
                -rico.CHAPTER_ONE_READING_DESK_ACTION_LAYOUT_PADDING :
            ],
            bytes(rico.CHAPTER_ONE_READING_DESK_ACTION_LAYOUT_PADDING),
        )
        self.assertEqual(
            reading_action_allocation[
                -rico.CHAPTER_ONE_READING_DESK_ACTION_LAYOUT_PADDING - 1
            ],
            0,
        )
        self.assertEqual(
            rico.CHAPTER_ONE_ANNA_VISUAL_POSITION,
            rico.CHAPTER_ONE_ANNA_INTERACTION_POSITION,
        )
        anna_x, anna_z, anna_triangle = rico.CHAPTER_ONE_ANNA_VISUAL_POSITION
        self.assertEqual((anna_x, anna_z, anna_triangle), (35, -140, 75))
        walkmesh = rico._walkmesh_layer(source_components[1], 0)
        self.assertEqual(anna_triangle, 75)
        self.assertTrue(
            rico._point_inside_triangle(
                (anna_x, anna_z),
                walkmesh[anna_triangle],
            )
        )
        self.assertEqual(
            {vertex[1] for vertex in walkmesh[anna_triangle]},
            {0},
        )
        # Slot 1 measured native collision radii of 16 for both Anne and young
        # Rico.  This flat-floor stance stays outside their 32-unit contact
        # distance while remaining inside Anne's independent dialogue box.
        approach_x, approach_z, approach_triangle = (76, -123, 50)
        self.assertTrue(
            rico._point_inside_triangle(
                (approach_x, approach_z),
                walkmesh[approach_triangle],
            )
        )
        self.assertEqual(
            {vertex[1] for vertex in walkmesh[approach_triangle]},
            {0},
        )
        anna_contact_distance = 16 + 16
        self.assertGreater(
            (approach_x - anna_x) ** 2 + (approach_z - anna_z) ** 2,
            anna_contact_distance**2,
        )
        anna_effective_x = rico.CHAPTER_ONE_ANNA_INTERACTION_HALF_WIDTH * 2 + 0x10
        anna_effective_z = rico.CHAPTER_ONE_ANNA_INTERACTION_HALF_DEPTH * 2 + 0x10
        self.assertLessEqual(abs(approach_x - anna_x), anna_effective_x)
        self.assertLessEqual(abs(approach_z - anna_z), anna_effective_z)
        bed_min_x, bed_max_x, _bed_min_z, bed_max_z = (
            rico.CHAPTER_ONE_BED_WORLD_FOOTPRINT
        )
        self.assertLessEqual(bed_min_x, anna_x)
        self.assertLessEqual(anna_x, bed_max_x)
        self.assertGreater(anna_z, bed_max_z)
        anna_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "Anne's bedside"
        )
        bedside_action_pc = output_editor.get_script_pointer(
            first_controller + anna_index,
            2,
        )
        rico._validate_chapter_one_anna_output(
            output_editor,
            bedside_action_pc,
        )
        hide_pc = output_editor.get_script_pointer(
            rico.CHAPTER_ONE_ANNA_ENTITY,
            4,
        )
        self.assertEqual(
            hide_pc,
            output_editor.get_script_pointer(0, 2),
        )

    def test_chapter_one_anna_and_room_prop_pins_fail_closed(self) -> None:
        source_field = parse_field(self.sources[1])
        components = [part.data for part in source_field.parts]

        damaged_header = bytearray(source_field.header)
        record = 0x190 + rico.CHAPTER_ONE_ANNA_ENTITY * 16
        damaged_header[record] ^= 1
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            "Anne source actor changed",
        ):
            rico._validate_chapter_one_anna_source(
                bytes(damaged_header),
                components,
            )

        damaged_actor = bytearray(components[rico.mass_driver.ACTOR_INDEX])
        damaged_actor[12] ^= 1
        damaged_components = list(components)
        damaged_components[rico.mass_driver.ACTOR_INDEX] = bytes(damaged_actor)
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            "Anne visual assets changed",
        ):
            rico._validate_chapter_one_anna_source(
                source_field.header,
                damaged_components,
            )

        damaged_props = bytearray(source_field.header)
        bed_record = 0x190 + 13 * 16
        damaged_props[bed_record] ^= 1
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            "visible Anne's bed node changed",
        ):
            rico._validate_playable_visible_prop_sources(
                1,
                bytes(damaged_props),
                components,
            )

        for description, node in (("stonebell vase", 11), ("stonebell flowers", 18)):
            with self.subTest(prop=description):
                damaged_flower = bytearray(source_field.header)
                flower_record = 0x190 + node * 16
                damaged_flower[flower_record] ^= 1
                with self.assertRaisesRegex(
                    rico.RicoArcBuildError,
                    f"visible {description} node changed",
                ):
                    rico._validate_playable_visible_prop_sources(
                        1,
                        bytes(damaged_flower),
                        components,
                    )

    def test_chapter_three_exit_is_on_the_connected_walkmesh(self) -> None:
        chapter = self.chapters[2]
        (
            source_field,
            _output_field,
            _source_editor,
            output_editor,
            contract,
            _first_controller,
            exit_entity,
        ) = self._layout(
            chapter,
            self.sources[chapter.chapter_id],
            self.outputs[chapter.chapter_id],
        )
        self.assertEqual(
            (contract.exit_x, contract.exit_z, contract.exit_triangle),
            (0, -289, 42),
        )
        expected_init = rico._playable_controller_init(
            contract.exit_x,
            contract.exit_z,
            half_width=0x04,
            half_depth=0x04,
        )
        exit_init_pc = output_editor.get_script_pointer(exit_entity, 0)
        self.assertEqual(
            output_editor.bytecode[
                exit_init_pc : exit_init_pc + len(expected_init)
            ],
            expected_init,
        )

        triangles = rico._walkmesh_layer(source_field.parts[1].data, 0)
        entry_triangle = rico.PLAYABLE_ENTRY_POSITIONS[3][2]
        reachable = {entry_triangle}
        pending = [entry_triangle]
        while pending:
            current = pending.pop()
            current_vertices = set(triangles[current])
            for index, triangle in enumerate(triangles):
                if index in reachable:
                    continue
                if len(current_vertices & set(triangle)) >= 2:
                    reachable.add(index)
                    pending.append(index)
        self.assertIn(contract.exit_triangle, reachable)
        self.assertTrue(
            rico._point_inside_triangle(
                (contract.exit_x, contract.exit_z),
                triangles[contract.exit_triangle],
            )
        )

    def test_anna_remains_visible_until_rico_uses_the_door(self) -> None:
        chapter = self.chapters[0]
        (
            _source_field,
            _output_field,
            _source_editor,
            output_editor,
            contract,
            first_controller,
            exit_entity,
        ) = self._layout(
            chapter,
            self.sources[chapter.chapter_id],
            self.outputs[chapter.chapter_id],
        )
        interaction_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "Anne's bedside"
        )
        interaction = contract.interactions[interaction_index]
        self.assertFalse(
            any(stage.time_cut_after for stage in interaction.stages)
        )
        self.assertFalse(
            any(stage.hide_entities_after for stage in interaction.stages)
        )

        controller = first_controller + interaction_index
        action_pc = output_editor.get_script_pointer(controller, 2)
        action_end = output_editor.get_script_pointer(controller + 1, 0)
        action = output_editor.bytecode[action_pc:action_end]
        self.assertNotIn(
            rico.mass_driver._facility_video_screen_fade_body(0xFF, 20),
            action,
        )
        self.assertNotIn(b"\x09\x04\x24", action)
        self.assertEqual(output_editor.get_script_pointer(4, 2), action_pc)
        hide_pc = output_editor.get_script_pointer(4, 4)
        self.assertEqual(
            hide_pc,
            output_editor.get_script_pointer(0, 2),
        )

        exit_pc = output_editor.get_script_pointer(exit_entity, 2)
        exit_action = output_editor.bytecode[exit_pc:]
        self.assertIn(
            rico.mass_driver._facility_video_screen_fade_body(0xFF, 32),
            exit_action,
        )
        self.assertIn(
            rico._change_field(rico.CHAPTER_ONE_FIREWOOD_FIELD, 0) + b"\x5B",
            exit_action,
        )

    def test_firewood_is_a_finite_automatic_daylight_field(self) -> None:
        retail_disc = PROJECT_ROOT / "Xenogears (Disc 1).bin"
        self.assertTrue(retail_disc.is_file())
        reader = rico.DiscReader(retail_disc, 1)
        donor = reader.canonical(
            rico._field_bundle_id(rico.CHAPTER_ONE_FIREWOOD_DONOR_FIELD)
        )
        graphics = reader.canonical(
            rico._field_bundle_id(rico.CHAPTER_ONE_FIREWOOD_DONOR_FIELD) + 1
        )
        young_rico_source = reader.canonical(
            rico._field_bundle_id(rico.CHAPTER_ONE_FIREWOOD_RICO_SOURCE_FIELD)
        )

        self.assertEqual(rico.CHAPTER_ONE_FIREWOOD_FIELD, 377)
        self.assertEqual(rico.CHAPTER_ONE_FIREWOOD_DONOR_FIELD, 199)
        self.assertEqual(rico.CHAPTER_ONE_FIREWOOD_RICO_SOURCE_FIELD, 229)
        self.assertEqual(rico.CHAPTER_ONE_FIREWOOD_RICO_TIMESCALE, 0x140)
        self.assertEqual(
            (
                rico.CHAPTER_ONE_FIREWOOD_ESTABLISHING_CAMERA_TARGET,
                rico.CHAPTER_ONE_FIREWOOD_ESTABLISHING_CAMERA_EYE,
                rico.CHAPTER_ONE_FIREWOOD_WORK_CAMERA_TARGET,
                rico.CHAPTER_ONE_FIREWOOD_WORK_CAMERA_EYE,
            ),
            (
                (470, 120, -55),
                (926, 696, -457),
                (480, 13, -70),
                (750, -302, -286),
            ),
        )
        self.assertEqual(
            (
                rico.CHAPTER_ONE_FIREWOOD_FIELD_FADE_FRAMES,
                rico.CHAPTER_ONE_FIREWOOD_ESTABLISH_HOLD_FRAMES,
                rico.CHAPTER_ONE_FIREWOOD_CAMERA_MOVE_FRAMES,
                rico.CHAPTER_ONE_FIREWOOD_WORK_SETTLE_FRAMES,
                rico.CHAPTER_ONE_FIREWOOD_GATHER_PAUSE_FRAMES,
                rico.CHAPTER_ONE_FIREWOOD_PICKUP_FADE_FRAMES,
                rico.CHAPTER_ONE_FIREWOOD_PICKUP_BLACK_HOLD_FRAMES,
                rico.CHAPTER_ONE_FIREWOOD_RETURN_SETTLE_FRAMES,
            ),
            (36, 40, 30, 24, 30, 20, 12, 30),
        )
        self.assertEqual(
            rico._field_bundle_id(rico.CHAPTER_ONE_FIREWOOD_FIELD),
            1360,
        )
        self.assertEqual(
            (len(donor), hashlib.sha256(donor).hexdigest()),
            (
                rico.CHAPTER_ONE_FIREWOOD_DONOR_BUNDLE_SIZE,
                rico.CHAPTER_ONE_FIREWOOD_DONOR_BUNDLE_SHA256,
            ),
        )
        self.assertEqual(
            (len(graphics), hashlib.sha256(graphics).hexdigest()),
            (
                rico.CHAPTER_ONE_FIREWOOD_DONOR_GRAPHICS_SIZE,
                rico.CHAPTER_ONE_FIREWOOD_DONOR_GRAPHICS_SHA256,
            ),
        )

        donor_field = parse_field(donor)
        donor_components = tuple(part.data for part in donor_field.parts)
        self.assertEqual(
            (len(donor_field.header), hashlib.sha256(donor_field.header).hexdigest()),
            (
                rico.CHAPTER_ONE_FIREWOOD_DONOR_HEADER_SIZE,
                rico.CHAPTER_ONE_FIREWOOD_DONOR_HEADER_SHA256,
            ),
        )
        for component, expected_size, expected_hash in (
            (
                donor_components[1],
                rico.CHAPTER_ONE_FIREWOOD_DONOR_WALKMESH_SIZE,
                rico.CHAPTER_ONE_FIREWOOD_DONOR_WALKMESH_SHA256,
            ),
            (
                donor_components[rico.mass_driver.MODEL_INDEX],
                rico.CHAPTER_ONE_FIREWOOD_DONOR_MODELS_SIZE,
                rico.CHAPTER_ONE_FIREWOOD_DONOR_MODELS_SHA256,
            ),
            (
                donor_components[rico.mass_driver.ACTOR_INDEX],
                rico.CHAPTER_ONE_FIREWOOD_DONOR_ACTOR_COMPONENT_SIZE,
                rico.CHAPTER_ONE_FIREWOOD_DONOR_ACTOR_COMPONENT_SHA256,
            ),
            (
                donor_components[rico.mass_driver.SPRITE_INDEX],
                rico.CHAPTER_ONE_FIREWOOD_DONOR_SPRITE_COMPONENT_SIZE,
                rico.CHAPTER_ONE_FIREWOOD_DONOR_SPRITE_COMPONENT_SHA256,
            ),
        ):
            self.assertEqual(
                (len(component), hashlib.sha256(component).hexdigest()),
                (expected_size, expected_hash),
            )

        donor_editor = AtelScript(donor_components[rico.SCRIPT_INDEX])
        donor_init_pc = donor_editor.get_script_pointer(0, 0)
        self.assertEqual(
            donor_editor.entity_count,
            rico.CHAPTER_ONE_FIREWOOD_DONOR_ENTITY_COUNT,
        )
        self.assertEqual(
            donor_init_pc,
            rico.CHAPTER_ONE_FIREWOOD_DONOR_DIRECTOR_INIT_PC,
        )
        self.assertEqual(
            donor_editor.bytecode[
                donor_init_pc :
                donor_init_pc
                + len(rico.CHAPTER_ONE_FIREWOOD_DONOR_DIRECTOR_INIT_BODY)
            ],
            rico.CHAPTER_ONE_FIREWOOD_DONOR_DIRECTOR_INIT_BODY,
        )

        crate_record_at = 0x190 + rico.CHAPTER_ONE_FIREWOOD_CRATE_NODE * 16
        self.assertEqual(
            donor_field.header[crate_record_at : crate_record_at + 16],
            rico.CHAPTER_ONE_FIREWOOD_CRATE_HEADER_RECORD,
        )
        door_record_at = 0x190 + rico.CHAPTER_ONE_FIREWOOD_DOOR_NODE * 16
        self.assertEqual(
            donor_field.header[door_record_at : door_record_at + 16],
            rico.CHAPTER_ONE_FIREWOOD_DOOR_HEADER_RECORD,
        )
        donor_models = rico.mass_driver._indexed_bundle_entries(
            donor_components[rico.mass_driver.MODEL_INDEX]
        )
        for role, model_index, expected_size, expected_hash in (
            (
                "discarded wooden packing crate",
                rico.CHAPTER_ONE_FIREWOOD_CRATE_MODEL_INDEX,
                rico.CHAPTER_ONE_FIREWOOD_CRATE_MODEL_SIZE,
                rico.CHAPTER_ONE_FIREWOOD_CRATE_MODEL_SHA256,
            ),
            (
                "Nortune doorway",
                rico.CHAPTER_ONE_FIREWOOD_DOOR_MODEL_INDEX,
                rico.CHAPTER_ONE_FIREWOOD_DOOR_MODEL_SIZE,
                rico.CHAPTER_ONE_FIREWOOD_DOOR_MODEL_SHA256,
            ),
        ):
            with self.subTest(daylight_prop=role):
                model = donor_models[model_index]
                self.assertEqual(
                    (len(model), hashlib.sha256(model).hexdigest()),
                    (expected_size, expected_hash),
                )

        triangles = rico._walkmesh_layer(donor_components[1], 0)
        route_points = (
            ("door", rico.CHAPTER_ONE_FIREWOOD_DOOR_POSITION),
            *(
                (f"route waypoint {index}", point)
                for index, point in enumerate(rico.CHAPTER_ONE_FIREWOOD_MID_ROUTE)
            ),
            ("crate gathering stance", rico.CHAPTER_ONE_FIREWOOD_WORK_POSITION),
        )
        for role, (x, z, triangle) in route_points:
            with self.subTest(firewood_route_point=role):
                self.assertTrue(0 <= triangle < len(triangles))
                self.assertTrue(
                    rico._point_inside_triangle((x, z), triangles[triangle])
                )
        forward_route = (
            rico.CHAPTER_ONE_FIREWOOD_DOOR_POSITION,
            *rico.CHAPTER_ONE_FIREWOOD_MID_ROUTE,
            rico.CHAPTER_ONE_FIREWOOD_WORK_POSITION,
        )
        for start, end in zip(forward_route, forward_route[1:]):
            self.assertTrue(
                rico._chapter_four_segment_on_walkmesh(
                    start[:2], end[:2], triangles
                )
            )
            self.assertTrue(
                rico._chapter_four_segment_on_walkmesh(
                    end[:2], start[:2], triangles
                )
            )

        source_field = parse_field(young_rico_source)
        source_actor_banks = rico.mass_driver._indexed_bundle_entries(
            source_field.parts[rico.mass_driver.ACTOR_INDEX].data
        )
        source_sprite_banks = rico.mass_driver._indexed_bundle_entries(
            source_field.parts[rico.mass_driver.SPRITE_INDEX].data
        )
        bank_index = rico.CHAPTER_ONE_FIREWOOD_BANK_INDEX
        self.assertEqual(
            (
                len(source_actor_banks[bank_index]),
                hashlib.sha256(source_actor_banks[bank_index]).hexdigest(),
            ),
            (1_464, rico.YOUNG_RICO_ACTOR_BANK_SHA256),
        )
        self.assertEqual(
            (
                len(source_sprite_banks[bank_index]),
                hashlib.sha256(source_sprite_banks[bank_index]).hexdigest(),
            ),
            (
                rico.YOUNG_RICO_SPRITE_BANK_SIZE,
                rico.YOUNG_RICO_SPRITE_BANK_SHA256,
            ),
        )

        output = rico._build_chapter_one_firewood_bundle(
            donor,
            young_rico_source,
            self.chapters[0],
        )
        output_field = parse_field(output)
        output_components = tuple(part.data for part in output_field.parts)
        self.assertEqual(len(output_field.header), len(donor_field.header))
        self.assertEqual(output_field.header[0x18C:], donor_field.header[0x18C:])
        for unchanged_index in (
            0,
            1,
            rico.mass_driver.MODEL_INDEX,
            8,
        ):
            self.assertEqual(
                output_components[unchanged_index],
                donor_components[unchanged_index],
            )
        firewood_text = rico._chapter_dialogue_texts(
            self.chapters[0],
            rico._playable_chapter_contract(1).exit_transition.firewood_dialogue,
        )
        output_dialogue = rico.parse_dialogue(
            output_components[rico.DIALOGUE_INDEX]
        )
        self.assertEqual(
            tuple(block.text for block in output_dialogue.blocks),
            tuple(rico._reflow_dialogue_text(text) for text in firewood_text),
        )
        self.assertIn("broken packing crate", firewood_text[0])
        self.assertIn("driest slats", firewood_text[0])

        donor_actor_banks = rico.mass_driver._indexed_bundle_entries(
            donor_components[rico.mass_driver.ACTOR_INDEX]
        )
        donor_sprite_banks = rico.mass_driver._indexed_bundle_entries(
            donor_components[rico.mass_driver.SPRITE_INDEX]
        )
        output_actor_banks = rico.mass_driver._indexed_bundle_entries(
            output_components[rico.mass_driver.ACTOR_INDEX]
        )
        output_sprite_banks = rico.mass_driver._indexed_bundle_entries(
            output_components[rico.mass_driver.SPRITE_INDEX]
        )
        self.assertEqual(output_actor_banks[0], donor_actor_banks[0])
        self.assertEqual(output_sprite_banks[0], donor_sprite_banks[0])
        self.assertEqual(output_actor_banks[bank_index], source_actor_banks[bank_index])
        self.assertEqual(output_sprite_banks[bank_index], source_sprite_banks[bank_index])
        self.assertNotEqual(output_actor_banks[bank_index], donor_actor_banks[bank_index])
        self.assertNotEqual(output_sprite_banks[bank_index], donor_sprite_banks[bank_index])
        self.assertEqual(
            struct.unpack_from("<4H", output_field.header, bank_index * 8),
            rico.CHAPTER_ONE_FIREWOOD_BANK_VRAM_MAPPING,
        )

        expected_encounter = bytearray(
            donor_components[rico.mass_driver.ENCOUNTER_INDEX]
        )
        expected_encounter[
            rico.WEIGHTS_OFFSET : rico.WEIGHTS_OFFSET + rico.FORMATION_COUNT
        ] = bytes(rico.FORMATION_COUNT)
        self.assertEqual(
            output_components[rico.mass_driver.ENCOUNTER_INDEX],
            bytes(expected_encounter),
        )
        self.assertEqual(
            output_components[rico.mass_driver.ENCOUNTER_INDEX][
                rico.WEIGHTS_OFFSET :
                rico.WEIGHTS_OFFSET + rico.FORMATION_COUNT
            ],
            bytes(rico.FORMATION_COUNT),
        )

        editor = AtelScript(output_components[rico.SCRIPT_INDEX])
        self.assertEqual(
            editor.entity_count,
            rico.CHAPTER_ONE_FIREWOOD_DONOR_ENTITY_COUNT,
        )
        stop_pc = editor.get_script_pointer(0, 2)
        self.assertEqual(editor.bytecode[stop_pc : stop_pc + 1], b"\x00")
        live_scripts = {
            (0, 0),
            (0, 1),
            (rico.CHAPTER_ONE_FIREWOOD_RICO_ENTITY, 0),
            (
                rico.CHAPTER_ONE_FIREWOOD_RICO_ENTITY,
                rico.CHAPTER_ONE_FIREWOOD_APPROACH_SCRIPT,
            ),
            (
                rico.CHAPTER_ONE_FIREWOOD_RICO_ENTITY,
                rico.CHAPTER_ONE_FIREWOOD_RETURN_SCRIPT,
            ),
            *((entity, 0) for entity in range(2, editor.entity_count)),
        }
        for entity in range(editor.entity_count):
            for script_index in range(32):
                if (entity, script_index) in live_scripts:
                    continue
                self.assertEqual(
                    editor.get_script_pointer(entity, script_index),
                    stop_pc,
                )
        for entity in range(2, editor.entity_count):
            init_pc = editor.get_script_pointer(entity, 0)
            self.assertEqual(
                editor.bytecode[
                    init_pc : init_pc + len(rico.INERT_HIDDEN_INIT)
                ],
                rico.INERT_HIDDEN_INIT,
            )

        rico_init_pc = editor.get_script_pointer(
            rico.CHAPTER_ONE_FIREWOOD_RICO_ENTITY,
            0,
        )
        rico_init = rico._chapter_one_firewood_rico_init()
        self.assertEqual(
            editor.bytecode[rico_init_pc : rico_init_pc + len(rico_init)],
            rico_init,
        )
        timescale_command = b"\x21" + rico._immediate(0x140)
        self.assertEqual(rico_init.count(timescale_command), 1)
        self.assertTrue(rico_init.endswith(timescale_command + b"\x00"))
        route_specs = (
            (
                rico.CHAPTER_ONE_FIREWOOD_APPROACH_SCRIPT,
                (
                    *rico.CHAPTER_ONE_FIREWOOD_MID_ROUTE,
                    rico.CHAPTER_ONE_FIREWOOD_WORK_POSITION,
                ),
            ),
            (
                rico.CHAPTER_ONE_FIREWOOD_RETURN_SCRIPT,
                (
                    *reversed(rico.CHAPTER_ONE_FIREWOOD_MID_ROUTE),
                    rico.CHAPTER_ONE_FIREWOOD_DOOR_POSITION,
                ),
            ),
        )
        for script_index, route_points in route_specs:
            with self.subTest(firewood_route_script=script_index):
                route_pc = editor.get_script_pointer(
                    rico.CHAPTER_ONE_FIREWOOD_RICO_ENTITY,
                    script_index,
                )
                route = rico._chapter_one_firewood_route_body(route_points)
                self.assertEqual(
                    editor.bytecode[route_pc : route_pc + len(route)],
                    route,
                )
                self.assertEqual(route.count(b"\x4B"), len(route_points))
                for x, z, _triangle in route_points:
                    position = rico._s16(x) + rico._s16(z)
                    self.assertIn(
                        b"\x4B"
                        + position
                        + b"\xC0"
                        + rico._immediate(
                            rico.CHAPTER_ONE_FIREWOOD_WAYPOINT_MAX_STEPS
                        )
                        + b"\x19"
                        + position
                        + b"\xC0",
                        route,
                    )

        director_pc = editor.get_script_pointer(0, 0)
        director = (
            rico.INERT_HIDDEN_INIT[:-1]
            + rico._play_music(self.chapters[0].music)
            + rico.mass_driver._facility_video_screen_fade_body(0xFF, 1)
            + b"\x00"
        )
        self.assertEqual(
            editor.bytecode[director_pc : director_pc + len(director)],
            director,
        )

        story_pc = editor.get_script_pointer(0, 1)
        story = editor.bytecode[story_pc:]
        self.assertEqual(
            story,
            rico._build_chapter_one_firewood_story(base_pc=story_pc),
        )
        narration = rico._dialogue_sequence((0,))
        self.assertEqual(story.count(narration), 1)
        establishing = rico._chapter_one_firewood_camera(
            rico.CHAPTER_ONE_FIREWOOD_ESTABLISHING_CAMERA_TARGET,
            rico.CHAPTER_ONE_FIREWOOD_ESTABLISHING_CAMERA_EYE,
            transition_frames=0,
            enter_camera_mode=True,
        )
        work_camera = rico._chapter_one_firewood_camera(
            rico.CHAPTER_ONE_FIREWOOD_WORK_CAMERA_TARGET,
            rico.CHAPTER_ONE_FIREWOOD_WORK_CAMERA_EYE,
            transition_frames=rico.CHAPTER_ONE_FIREWOOD_CAMERA_MOVE_FRAMES,
            enter_camera_mode=False,
        )
        return_camera = rico._chapter_one_firewood_camera(
            rico.CHAPTER_ONE_FIREWOOD_ESTABLISHING_CAMERA_TARGET,
            rico.CHAPTER_ONE_FIREWOOD_ESTABLISHING_CAMERA_EYE,
            transition_frames=0,
            enter_camera_mode=False,
        )
        approach_call = b"\x09" + bytes(
            (
                rico.CHAPTER_ONE_FIREWOOD_RICO_ENTITY,
                rico.CHAPTER_ONE_FIREWOOD_APPROACH_SCRIPT | 0x20,
            )
        )
        return_call = b"\x09" + bytes(
            (
                rico.CHAPTER_ONE_FIREWOOD_RICO_ENTITY,
                rico.CHAPTER_ONE_FIREWOOD_RETURN_SCRIPT | 0x20,
            )
        )
        field_fade_in = rico.mass_driver._facility_video_screen_fade_body(
            0,
            rico.CHAPTER_ONE_FIREWOOD_FIELD_FADE_FRAMES,
        )
        pickup_fade_out = rico.mass_driver._facility_video_screen_fade_body(
            0xFF,
            rico.CHAPTER_ONE_FIREWOOD_PICKUP_FADE_FRAMES,
        )
        pickup_fade_in = rico.mass_driver._facility_video_screen_fade_body(
            0,
            rico.CHAPTER_ONE_FIREWOOD_PICKUP_FADE_FRAMES,
        )
        final_fade = rico.mass_driver._facility_video_screen_fade_body(
            0xFF,
            rico.CHAPTER_ONE_FIREWOOD_FIELD_FADE_FRAMES,
        )
        ordered_beats = (
            establishing,
            field_fade_in,
            rico._wait(rico.CHAPTER_ONE_FIREWOOD_ESTABLISH_HOLD_FRAMES),
            approach_call,
            work_camera,
            rico._wait(rico.CHAPTER_ONE_FIREWOOD_WORK_SETTLE_FRAMES),
            narration,
            rico._wait(rico.CHAPTER_ONE_FIREWOOD_GATHER_PAUSE_FRAMES),
            pickup_fade_out,
            return_camera,
            rico._wait(rico.CHAPTER_ONE_FIREWOOD_PICKUP_BLACK_HOLD_FRAMES),
            pickup_fade_in,
            return_call,
            rico._wait(rico.CHAPTER_ONE_FIREWOOD_RETURN_SETTLE_FRAMES),
            final_fade,
            rico._change_field(rico.CHAPTER_ONE_AFTERMATH_FIELD, 0) + b"\x5B",
        )
        cursor = 0
        for beat in ordered_beats:
            next_at = story.index(beat, cursor)
            self.assertGreaterEqual(next_at, cursor)
            cursor = next_at + len(beat)
        self.assertEqual(
            story.count(approach_call),
            1,
        )
        self.assertEqual(story.count(return_call), 1)
        self.assertTrue(
            story.endswith(
                rico._change_field(rico.CHAPTER_ONE_AFTERMATH_FIELD, 0) + b"\x5B"
            )
        )
        self.assertTrue(
            rico._chapter_one_door_transition_body().endswith(
                rico._change_field(rico.CHAPTER_ONE_FIREWOOD_FIELD, 0) + b"\x5B"
            )
        )

    def test_live_chapter_one_aftermath_and_funeral_follow_the_firewood_field(
        self,
    ) -> None:
        retail_disc = PROJECT_ROOT / "Xenogears (Disc 1).bin"
        self.assertTrue(retail_disc.is_file())
        reader = rico.DiscReader(retail_disc, 1)
        chapter = self.chapters[0]
        next_chapter = self.chapters[1]
        contract = rico._playable_chapter_contract(1)
        transition = contract.exit_transition
        self.assertIsNotNone(transition)
        assert transition is not None

        self.assertEqual(rico.CHAPTER_ONE_FIREWOOD_DONOR_FIELD, 199)
        self.assertEqual(rico.CHAPTER_ONE_AFTERMATH_FIELD, 376)
        self.assertEqual(rico.CHAPTER_ONE_AFTERMATH_DONOR_FIELD, 229)
        self.assertEqual(rico.CHAPTER_ONE_FUNERAL_FIELD, 378)
        self.assertEqual(rico.CHAPTER_ONE_LIVE_FUNERAL_DONOR_FIELD, 15)
        self.assertEqual(rico.CHAPTER_ONE_ETON_SOURCE_FIELD, 348)
        self.assertEqual(rico.CHAPTER_ONE_GRAVE_MARKER_TARGET_NODE, 63)
        self.assertEqual(rico.CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_NODE, 64)
        self.assertEqual(rico.CHAPTER_ONE_GRAVE_MARKER_TARGET_MODEL_INDEX, 2)
        self.assertEqual(
            rico.CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_MODEL_INDEX,
            3,
        )
        self.assertEqual(
            (
                rico.CHAPTER_ONE_LIVE_FUNERAL_MARKER_POSITION,
                rico.CHAPTER_ONE_LIVE_FUNERAL_BACKGROUND_MARKER_POSITION,
                rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_POSITION,
                rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_START,
                rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_BLESSING_POSITION,
            ),
            (
                (600, -2700, 1885),
                (900, -2750, 1885),
                (500, -2400, 1882),
                (950, -2350, 1885),
                (720, -2520, 1885),
            ),
        )
        self.assertEqual(
            (
                rico.CHAPTER_ONE_LIVE_FUNERAL_CAMERA_TARGET,
                rico.CHAPTER_ONE_LIVE_FUNERAL_CAMERA_EYE,
                rico.CHAPTER_ONE_LIVE_FUNERAL_BLESSING_CAMERA_TARGET,
                rico.CHAPTER_ONE_LIVE_FUNERAL_BLESSING_CAMERA_EYE,
            ),
            (
                (700, -2525, -20),
                (1400, -3400, -650),
                (700, -2600, -20),
                (1120, -3160, -430),
            ),
        )
        self.assertEqual(
            (
                rico.CHAPTER_ONE_LIVE_FUNERAL_CAMERA_MOVE_FRAMES,
                rico.CHAPTER_ONE_LIVE_FUNERAL_RETURN_CAMERA_MOVE_FRAMES,
                rico.CHAPTER_ONE_LIVE_FUNERAL_FADE_FRAMES,
                rico.CHAPTER_ONE_LIVE_FUNERAL_ESTABLISH_HOLD_FRAMES,
                rico.CHAPTER_ONE_LIVE_FUNERAL_BLESSING_SETTLE_FRAMES,
                rico.CHAPTER_ONE_LIVE_FUNERAL_REFLECTION_HOLD_FRAMES,
                rico.CHAPTER_ONE_LIVE_FUNERAL_WIDE_HOLD_FRAMES,
                rico.CHAPTER_ONE_LIVE_FUNERAL_EPILOGUE_SETTLE_FRAMES,
            ),
            (36, 48, 36, 60, 42, 60, 60, 30),
        )

        aftermath_donor = reader.canonical(
            rico._field_bundle_id(rico.CHAPTER_ONE_AFTERMATH_DONOR_FIELD)
        )
        self.assertEqual(
            (len(aftermath_donor), hashlib.sha256(aftermath_donor).hexdigest()),
            (
                rico.CHAPTER_ONE_AFTERMATH_DONOR_BUNDLE_SIZE,
                rico.CHAPTER_ONE_AFTERMATH_DONOR_BUNDLE_SHA256,
            ),
        )
        aftermath = rico._build_chapter_one_aftermath_bundle(
            aftermath_donor,
            chapter,
        )
        aftermath_parsed = parse_field(aftermath)
        aftermath_source = parse_field(aftermath_donor)
        self.assertEqual(
            aftermath_parsed.header[0x18C:],
            aftermath_source.header[0x18C:],
        )
        for unchanged_index in (
            0,
            1,
            rico.mass_driver.MODEL_INDEX,
            rico.mass_driver.ACTOR_INDEX,
            rico.mass_driver.SPRITE_INDEX,
            8,
        ):
            self.assertEqual(
                aftermath_parsed.parts[unchanged_index].data,
                aftermath_source.parts[unchanged_index].data,
            )
        expected_aftermath_text = (
            *rico._chapter_dialogue_texts(chapter, transition.sickness_dialogue),
            *rico._chapter_dialogue_texts(chapter, transition.loss_dialogue),
        )
        self.assertEqual(
            tuple(
                block.text
                for block in rico.parse_dialogue(
                    aftermath_parsed.parts[rico.DIALOGUE_INDEX].data
                ).blocks
            ),
            tuple(
                rico._reflow_dialogue_text(text)
                for text in expected_aftermath_text
            ),
        )
        aftermath_editor = AtelScript(
            aftermath_parsed.parts[rico.SCRIPT_INDEX].data
        )
        self.assertEqual(
            aftermath_editor.entity_count,
            rico.CHAPTER_ONE_AFTERMATH_ENTITY_COUNT,
        )
        self.assertEqual(
            rico.CHAPTER_ONE_AFTERMATH_ANNA_SICKROOM_POSITION,
            (13, -84, 73),
        )
        aftermath_triangles = rico._walkmesh_layer(
            aftermath_parsed.parts[1].data,
            0,
        )
        anna_x, anna_z, anna_triangle = (
            rico.CHAPTER_ONE_AFTERMATH_ANNA_SICKROOM_POSITION
        )
        self.assertTrue(
            rico._point_inside_triangle(
                (anna_x, anna_z),
                aftermath_triangles[anna_triangle],
            )
        )
        self.assertEqual(
            {vertex[1] for vertex in aftermath_triangles[anna_triangle]},
            {0},
        )
        anna_init_pc = aftermath_editor.get_script_pointer(
            rico.CHAPTER_ONE_ANNA_ENTITY,
            0,
        )
        anna_init = rico._chapter_one_aftermath_anna_init()
        self.assertEqual(
            aftermath_editor.bytecode[
                anna_init_pc : anna_init_pc + len(anna_init)
            ],
            anna_init,
        )
        anna_staging = (
            b"\x19"
            + rico._s16(anna_x)
            + rico._s16(anna_z)
            + b"\xC0\x5F\x03"
        )
        self.assertIn(anna_staging, anna_init)
        self.assertTrue(
            rico.CHAPTER_ONE_AFTERMATH_NATIVE_HELPERS[
                (rico.CHAPTER_ONE_ANNA_ENTITY, 5)
            ][1].startswith(anna_staging)
        )
        self.assertNotIn(
            b"\x19" + rico._s16(-124) + rico._s16(203) + b"\xC0",
            anna_init,
        )
        cough_pc = aftermath_editor.get_script_pointer(
            rico.CHAPTER_ONE_ANNA_ENTITY,
            rico.CHAPTER_ONE_AFTERMATH_COUGH_SCRIPT,
        )
        self.assertEqual(
            aftermath_editor.bytecode[
                cough_pc : cough_pc + len(rico.CHAPTER_ONE_ANNA_COUGH_ONCE) + 1
            ],
            rico.CHAPTER_ONE_ANNA_COUGH_ONCE + b"\x00",
        )
        aftermath_story_pc = aftermath_editor.get_script_pointer(0, 1)
        aftermath_story = aftermath_editor.bytecode[aftermath_story_pc:]
        self.assertEqual(
            aftermath_story,
            rico._build_chapter_one_aftermath_story(
                base_pc=aftermath_story_pc,
                sickness_ids=tuple(range(6)),
                loss_ids=tuple(range(6, 10)),
            ),
        )
        daylight_grade = rico._chapter_one_aftermath_daylight_grade_body()
        night_grade = rico._chapter_one_aftermath_night_grade_body()
        daylight_restore = rico._chapter_one_aftermath_daylight_restore_body()
        death_blackout_handoff = (
            rico._chapter_one_aftermath_blackout_handoff_body()
        )
        slot_zero_fade_in = rico._chapter_one_aftermath_scene_fade_body(
            reveal=True,
        )
        slot_zero_fade_out = rico._chapter_one_aftermath_scene_fade_body(
            reveal=False,
        )
        neutral_slot_one_fade = rico.mass_driver._facility_video_screen_fade_body(
            0,
            rico.CHAPTER_ONE_AFTERMATH_FADE_FRAMES,
        )
        self.assertEqual(daylight_restore, neutral_slot_one_fade)
        self.assertEqual(aftermath_story.count(daylight_grade), 1)
        self.assertEqual(aftermath_story.count(night_grade), 1)
        self.assertEqual(aftermath_story.count(daylight_restore), 1)
        self.assertEqual(aftermath_story.count(death_blackout_handoff), 1)
        self.assertEqual(aftermath_story.count(slot_zero_fade_in), 4)
        self.assertEqual(aftermath_story.count(slot_zero_fade_out), 4)

        initial_daylight_at = aftermath_story.index(daylight_grade)
        first_reveal_at = aftermath_story.index(slot_zero_fade_in)
        first_blackout_at = aftermath_story.index(slot_zero_fade_out)
        night_at = aftermath_story.index(night_grade)
        sickroom_reveal_at = aftermath_story.index(
            slot_zero_fade_in,
            first_reveal_at + len(slot_zero_fade_in),
        )
        death_blackout_at = aftermath_story.index(death_blackout_handoff)
        death_narration_at = aftermath_story.index(
            rico._dialogue_sequence((6,))
        )
        daylight_restore_at = aftermath_story.index(daylight_restore)
        morning_vigil_at = aftermath_story.index(
            rico._dialogue_sequence((7, 8))
        )
        stonebell_at = aftermath_story.index(rico._dialogue_sequence((9,)))

        self.assertLess(initial_daylight_at, first_reveal_at)
        self.assertEqual(first_blackout_at + len(slot_zero_fade_out), night_at)
        self.assertLess(night_at, sickroom_reveal_at)
        self.assertNotIn(night_grade, aftermath_story[:first_blackout_at])
        self.assertLess(death_blackout_at, death_narration_at)
        self.assertLess(death_narration_at, daylight_restore_at)
        self.assertLess(daylight_restore_at, morning_vigil_at)
        self.assertLess(morning_vigil_at, stonebell_at)
        self.assertNotIn(daylight_restore, aftermath_story[:death_blackout_at])
        self.assertNotIn(night_grade, aftermath_story[daylight_restore_at:])
        self.assertEqual(
            aftermath_story.count(
                b"\x09"
                + bytes(
                    (
                        rico.CHAPTER_ONE_ANNA_ENTITY,
                        rico.CHAPTER_ONE_AFTERMATH_COUGH_SCRIPT | 0x20,
                    )
                )
            ),
            2,
        )
        self.assertTrue(
            aftermath_story.endswith(
                rico._change_field(rico.CHAPTER_ONE_FUNERAL_FIELD, 0) + b"\x5B"
            )
        )
        self.assertNotIn(b"\xFE\x77\x01", aftermath_story)

        funeral_donor = reader.canonical(
            rico._field_bundle_id(rico.CHAPTER_ONE_LIVE_FUNERAL_DONOR_FIELD)
        )
        funeral_graphics = reader.canonical(
            rico._field_bundle_id(rico.CHAPTER_ONE_LIVE_FUNERAL_DONOR_FIELD) + 1
        )
        young_rico_source = reader.canonical(
            rico._field_bundle_id(rico.CHAPTER_ONE_FIREWOOD_RICO_SOURCE_FIELD)
        )
        eton_source = reader.canonical(
            rico._field_bundle_id(rico.CHAPTER_ONE_ETON_SOURCE_FIELD)
        )
        funeral_source = parse_field(funeral_donor)
        young_source = parse_field(young_rico_source)
        eton_source_field = parse_field(eton_source)
        young_sprite_bank = rico.mass_driver._indexed_bundle_entries(
            young_source.parts[rico.mass_driver.SPRITE_INDEX].data
        )[rico.YOUNG_RICO_ACTOR_BANK_INDEX]
        eton_sprite_bank = rico.mass_driver._indexed_bundle_entries(
            eton_source_field.parts[rico.mass_driver.SPRITE_INDEX].data
        )[rico.CHAPTER_ONE_ETON_SOURCE_BANK_INDEX]
        young_image, = rico.mass_driver._indexed_bundle_entries(young_sprite_bank)
        eton_image, = rico.mass_driver._indexed_bundle_entries(eton_sprite_bank)
        self.assertEqual(struct.unpack_from("<HH", young_image), (64, 75))
        self.assertEqual(struct.unpack_from("<HH", eton_image), (64, 204))
        funeral_vram, funeral_uploads = (
            rico.mass_driver._reconstruct_field_graphics_vram(
                funeral_graphics,
                label="Chapter 1 funeral",
            )
        )
        self.assertIn((832, 0, 64, 75), funeral_uploads)
        priest_x, priest_y, _u, _v = (
            rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_VRAM_MAPPING
        )
        self.assertFalse(
            any(
                upload_x < priest_x + 64
                and priest_x < upload_x + upload_width
                and upload_y < priest_y + 204
                and priest_y < upload_y + upload_height
                for upload_x, upload_y, upload_width, upload_height in funeral_uploads
            )
        )
        rico_x, rico_y, _u, _v = (
            rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_VRAM_MAPPING
        )
        reconstructed_rico = b"".join(
            funeral_vram[
                ((rico_y + row) * 1024 + rico_x) * 2 :
                ((rico_y + row) * 1024 + rico_x + 64) * 2
            ]
            for row in range(75)
        )
        self.assertEqual(reconstructed_rico, young_image[4:])
        funeral_text = rico._chapter_dialogue_texts(
            chapter,
            transition.funeral_dialogue,
        )
        epilogue_text = rico._chapter_dialogue_texts(
            chapter,
            contract.exit_dialogue,
        )
        self.assertEqual(epilogue_text, ("END OF CHAPTER 1<Close>",))
        self.assertNotIn(chapter.blocks[19], epilogue_text)
        expected_funeral_dialogue = (
            *funeral_text,
            *epilogue_text,
            rico.PLAYABLE_NEXT_OR_HUB_CHOICE,
        )
        outputs: dict[int, bytes] = {}
        for disc in (1, 2):
            output = rico._build_chapter_one_live_funeral_bundle(
                funeral_donor,
                young_rico_source,
                eton_source,
                chapter,
                next_chapter,
                rico.HUB_FIELDS[disc],
            )
            outputs[disc] = output
            parsed = parse_field(output)
            self.assertEqual(
                len(parsed.header),
                rico.CHAPTER_ONE_LIVE_FUNERAL_DONOR_HEADER_SIZE,
            )
            self.assertEqual(
                struct.unpack_from(
                    "<4H",
                    parsed.header,
                    rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ACTOR_BANK_INDEX * 8,
                ),
                rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_VRAM_MAPPING,
            )
            self.assertEqual(
                struct.unpack_from(
                    "<4H",
                    parsed.header,
                    rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_ACTOR_BANK_INDEX * 8,
                ),
                rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_VRAM_MAPPING,
            )
            marker_at = 0x190 + rico.CHAPTER_ONE_GRAVE_MARKER_TARGET_NODE * 16
            self.assertEqual(
                parsed.header[marker_at : marker_at + 16],
                rico.CHAPTER_ONE_GRAVE_MARKER_TARGET_NODE_RECORD,
            )
            background_marker_at = (
                0x190 + rico.CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_NODE * 16
            )
            self.assertEqual(
                parsed.header[background_marker_at : background_marker_at + 16],
                rico.CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_NODE_RECORD,
            )
            model_entries = rico.mass_driver._indexed_bundle_entries(
                parsed.parts[rico.mass_driver.MODEL_INDEX].data
            )
            self.assertEqual(
                hashlib.sha256(
                    model_entries[
                        rico.CHAPTER_ONE_GRAVE_MARKER_TARGET_MODEL_INDEX
                    ]
                ).hexdigest(),
                rico.CHAPTER_ONE_GRAVE_MARKER_TARGET_MODEL_SHA256,
            )
            self.assertEqual(
                hashlib.sha256(
                    model_entries[
                        rico.CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_MODEL_INDEX
                    ]
                ).hexdigest(),
                rico.CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_MODEL_SHA256,
            )
            self.assertEqual(
                parsed.parts[rico.mass_driver.MODEL_INDEX].data,
                funeral_source.parts[rico.mass_driver.MODEL_INDEX].data,
            )

            young = parse_field(young_rico_source)
            eton = parse_field(eton_source)
            output_actor_banks = rico.mass_driver._indexed_bundle_entries(
                parsed.parts[rico.mass_driver.ACTOR_INDEX].data
            )
            output_sprite_banks = rico.mass_driver._indexed_bundle_entries(
                parsed.parts[rico.mass_driver.SPRITE_INDEX].data
            )
            young_actor_banks = rico.mass_driver._indexed_bundle_entries(
                young.parts[rico.mass_driver.ACTOR_INDEX].data
            )
            young_sprite_banks = rico.mass_driver._indexed_bundle_entries(
                young.parts[rico.mass_driver.SPRITE_INDEX].data
            )
            eton_actor_banks = rico.mass_driver._indexed_bundle_entries(
                eton.parts[rico.mass_driver.ACTOR_INDEX].data
            )
            eton_sprite_banks = rico.mass_driver._indexed_bundle_entries(
                eton.parts[rico.mass_driver.SPRITE_INDEX].data
            )
            funeral_actor_banks = rico.mass_driver._indexed_bundle_entries(
                funeral_source.parts[rico.mass_driver.ACTOR_INDEX].data
            )
            funeral_sprite_banks = rico.mass_driver._indexed_bundle_entries(
                funeral_source.parts[rico.mass_driver.SPRITE_INDEX].data
            )
            self.assertEqual(
                output_actor_banks[
                    rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_ACTOR_BANK_INDEX
                ],
                young_actor_banks[rico.YOUNG_RICO_ACTOR_BANK_INDEX],
            )
            self.assertEqual(
                output_sprite_banks[
                    rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_SPRITE_BANK_INDEX
                ],
                young_sprite_banks[rico.YOUNG_RICO_ACTOR_BANK_INDEX],
            )
            self.assertEqual(
                output_actor_banks[
                    rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ACTOR_BANK_INDEX
                ],
                eton_actor_banks[rico.CHAPTER_ONE_ETON_SOURCE_BANK_INDEX],
            )
            self.assertEqual(
                output_sprite_banks[
                    rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_SPRITE_BANK_INDEX
                ],
                eton_sprite_banks[rico.CHAPTER_ONE_ETON_SOURCE_BANK_INDEX],
            )
            self.assertEqual(
                output_actor_banks[
                    rico.CHAPTER_ONE_LIVE_FUNERAL_PRESERVED_ACTOR_BANK_INDEX
                ],
                funeral_actor_banks[
                    rico.CHAPTER_ONE_LIVE_FUNERAL_PRESERVED_ACTOR_BANK_INDEX
                ],
            )
            self.assertEqual(
                output_sprite_banks[2],
                funeral_sprite_banks[
                    rico.CHAPTER_ONE_LIVE_FUNERAL_PRESERVED_SPRITE_BANK_INDEX
                ],
            )

            dialogue = rico.parse_dialogue(
                parsed.parts[rico.DIALOGUE_INDEX].data
            )
            self.assertEqual(len(expected_funeral_dialogue), 6)
            self.assertEqual(len(dialogue.blocks), len(expected_funeral_dialogue))
            self.assertEqual(
                tuple(block.text for block in dialogue.blocks),
                tuple(
                    rico._reflow_dialogue_text(text)
                    for text in expected_funeral_dialogue
                ),
            )
            for block in dialogue.blocks:
                self.assertTrue(block.text.endswith("<Close>"))
                self.assertTrue(block.payload)
                self.assertEqual(block.payload[-1], 0)

            editor = AtelScript(parsed.parts[rico.SCRIPT_INDEX].data)
            self.assertEqual(
                editor.entity_count,
                rico.CHAPTER_ONE_LIVE_FUNERAL_ENTITY_COUNT,
            )
            story_pc = editor.get_script_pointer(0, 1)
            story = editor.bytecode[story_pc:]
            self.assertEqual(
                story,
                rico._build_chapter_one_live_funeral_story(
                    base_pc=story_pc,
                    transition=transition,
                    funeral_ids=tuple(range(4)),
                    epilogue_ids=(4,),
                ),
            )
            director_pc = editor.get_script_pointer(0, 0)
            director = (
                rico.INERT_HIDDEN_INIT[:-1]
                + rico._play_music(chapter.music)
                + rico.mass_driver._facility_video_screen_fade_body(0xFF, 1)
                + b"\x00"
            )
            self.assertEqual(
                editor.bytecode[director_pc : director_pc + len(director)],
                director,
            )
            rico_init = rico._chapter_one_live_funeral_actor_init(
                rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_ACTOR_BANK_INDEX,
                rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_POSITION,
                rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_DIRECTION,
            )
            rico_init_pc = editor.get_script_pointer(
                rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_ENTITY,
                0,
            )
            self.assertEqual(
                editor.bytecode[rico_init_pc : rico_init_pc + len(rico_init)],
                rico_init,
            )
            priest_init = rico._chapter_one_live_funeral_actor_init(
                rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ACTOR_BANK_INDEX,
                rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_START,
                rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_START_DIRECTION,
            )
            priest_init_pc = editor.get_script_pointer(
                rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ENTITY,
                0,
            )
            self.assertEqual(
                editor.bytecode[
                    priest_init_pc : priest_init_pc + len(priest_init)
                ],
                priest_init,
            )
            priest_walk = rico._chapter_one_live_funeral_priest_approach()
            priest_walk_pc = editor.get_script_pointer(
                rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ENTITY,
                rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_APPROACH_SCRIPT,
            )
            self.assertEqual(
                editor.bytecode[
                    priest_walk_pc : priest_walk_pc + len(priest_walk)
                ],
                priest_walk,
            )
            priest_approach = b"\x09" + bytes(
                (
                    rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ENTITY,
                    rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_APPROACH_SCRIPT | 0x20,
                )
            )
            progress = rico.mass_driver._set_var_bit(
                rico.PLAYABLE_STATE_VARIABLE,
                transition.bit,
            )
            establishing_camera = rico._chapter_one_live_funeral_camera(
                rico.CHAPTER_ONE_LIVE_FUNERAL_CAMERA_TARGET,
                rico.CHAPTER_ONE_LIVE_FUNERAL_CAMERA_EYE,
                transition_frames=0,
                enter_camera_mode=True,
            )
            blessing_camera = rico._chapter_one_live_funeral_camera(
                rico.CHAPTER_ONE_LIVE_FUNERAL_BLESSING_CAMERA_TARGET,
                rico.CHAPTER_ONE_LIVE_FUNERAL_BLESSING_CAMERA_EYE,
                transition_frames=rico.CHAPTER_ONE_LIVE_FUNERAL_CAMERA_MOVE_FRAMES,
                enter_camera_mode=False,
            )
            return_wide_camera = rico._chapter_one_live_funeral_camera(
                rico.CHAPTER_ONE_LIVE_FUNERAL_CAMERA_TARGET,
                rico.CHAPTER_ONE_LIVE_FUNERAL_CAMERA_EYE,
                transition_frames=(
                    rico.CHAPTER_ONE_LIVE_FUNERAL_RETURN_CAMERA_MOVE_FRAMES
                ),
                enter_camera_mode=False,
            )
            fade_visible = rico.mass_driver._facility_video_screen_fade_body(
                0,
                rico.CHAPTER_ONE_LIVE_FUNERAL_FADE_FRAMES,
            )
            black_grade_prefix = (
                b"\xF1"
                + rico._immediate(2)
                + rico._immediate(0xFF) * 3
            )
            hidden_dialogue_flags = (
                rico.CHAPTER_ONE_LIVE_FUNERAL_HIDDEN_DIALOGUE_FLAGS
            )
            first_funeral_pages = rico._dialogue_sequence(
                (0, 1),
                flags=hidden_dialogue_flags,
            )
            blessing_pages = rico._dialogue_sequence(
                (2, 3),
                flags=hidden_dialogue_flags,
            )
            epilogue_pages = rico._dialogue_sequence(
                (4,),
                flags=hidden_dialogue_flags,
            )
            completion_call = rico._chapter_one_aftermath_call(
                rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_ENTITY,
                rico.CHAPTER_ONE_LIVE_FUNERAL_COMPLETION_SCRIPT,
            )
            ordered_beats = (
                establishing_camera,
                fade_visible,
                rico._wait(rico.CHAPTER_ONE_LIVE_FUNERAL_ESTABLISH_HOLD_FRAMES),
                first_funeral_pages,
                priest_approach,
                blessing_camera,
                rico._wait(rico.CHAPTER_ONE_LIVE_FUNERAL_BLESSING_SETTLE_FRAMES),
                blessing_pages,
                rico._wait(rico.CHAPTER_ONE_LIVE_FUNERAL_REFLECTION_HOLD_FRAMES),
                return_wide_camera,
                rico._wait(rico.CHAPTER_ONE_LIVE_FUNERAL_WIDE_HOLD_FRAMES),
                epilogue_pages,
                progress,
                rico._wait(rico.CHAPTER_ONE_LIVE_FUNERAL_EPILOGUE_SETTLE_FRAMES),
                completion_call,
            )
            cursor = 0
            for beat in ordered_beats:
                beat_at = story.index(beat, cursor)
                self.assertGreaterEqual(beat_at, cursor)
                cursor = beat_at + len(beat)
            self.assertEqual(story.count(priest_approach), 1)
            self.assertEqual(story.count(progress), 1)
            self.assertEqual(story.count(establishing_camera), 1)
            self.assertEqual(story.count(blessing_camera), 1)
            self.assertEqual(story.count(return_wide_camera), 1)
            self.assertEqual(story.count(fade_visible), 1)
            self.assertNotIn(black_grade_prefix, story)
            for dialogue_id in range(5):
                safe_dialogue = (
                    rico._dialog(dialogue_id, flags=hidden_dialogue_flags)
                    + b"\x9C"
                )
                unsafe_dialogue = rico._dialog(dialogue_id, flags=0) + b"\x9C"
                self.assertEqual(
                    story.count(safe_dialogue),
                    1,
                )
                self.assertNotIn(unsafe_dialogue, story)
            self.assertEqual(story.count(completion_call), 1)
            last_epilogue_page = (
                rico._dialog(4, flags=hidden_dialogue_flags) + b"\x9C"
            )
            stale_second_epilogue_page = (
                rico._dialog(5, flags=hidden_dialogue_flags) + b"\x9C"
            )
            self.assertNotIn(stale_second_epilogue_page, story)
            self.assertLess(story.index(last_epilogue_page), story.index(progress))
            self.assertLess(story.index(progress), story.index(completion_call))
            menu_comparison_prefix = (
                b"\x02" + struct.pack("<H", rico.MENU_SELECTION_VARIABLE)
            )
            self.assertNotIn(b"\xD2", story)
            self.assertNotIn(b"\xA9\x12\x9C", story)
            self.assertNotIn(menu_comparison_prefix, story)
            self.assertNotIn(
                rico._change_field(rico.CHAPTER_FIELDS[disc][2], 0),
                story,
            )
            self.assertNotIn(rico._hub_launch_body(rico.HUB_FIELDS[disc]), story)
            self.assertTrue(story.endswith(completion_call))
            self.assertNotIn(b"\xFE\x77\x01", story)

            completion_pc = editor.get_script_pointer(
                rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_ENTITY,
                rico.CHAPTER_ONE_LIVE_FUNERAL_COMPLETION_SCRIPT,
            )
            expected_completion = rico._build_chapter_one_live_funeral_completion(
                base_pc=completion_pc,
                choice_id=5,
                next_field=rico.CHAPTER_FIELDS[disc][2],
                return_hub=rico.HUB_FIELDS[disc],
            )
            completion = editor.bytecode[
                completion_pc : completion_pc + len(expected_completion)
            ]
            self.assertEqual(completion, expected_completion)
            self.assertEqual(completion.count(rico._choice_dialog(5)), 1)
            self.assertEqual(completion.count(b"\xA9\x12\x9C"), 1)
            self.assertEqual(
                completion.count(
                    rico._chapter_launch_body(2, rico.CHAPTER_FIELDS[disc][2])
                ),
                1,
            )
            self.assertEqual(
                completion.count(rico._hub_launch_body(rico.HUB_FIELDS[disc])),
                1,
            )
            chapter_two_framing = tuple(
                rico._reflow_dialogue_text(text)
                for text in rico._chapter_selection_exposition(next_chapter)
            )
            self.assertTrue(
                all(
                    framing not in tuple(block.text for block in dialogue.blocks)
                    for framing in chapter_two_framing
                )
            )
            self.assertIn(menu_comparison_prefix, completion)
        self.assertNotEqual(outputs[1], outputs[2])

    def test_hub_is_a_playable_path_of_sephirot_marker_ring(self) -> None:
        source_path = RICO_AUDIT_ROOT / (
            f"{rico._field_bundle_id(rico.HUB_DONOR_FIELD)}.bin"
        )
        self.assertTrue(source_path.is_file())
        source = source_path.read_bytes()
        self.assertEqual(len(source), rico.HUB_DONOR_BUNDLE_SIZE)
        self.assertEqual(
            hashlib.sha256(source).hexdigest(),
            rico.HUB_DONOR_BUNDLE_SHA256,
        )
        output = rico._build_hub_bundle(
            source,
            rico.CHAPTER_FIELDS[1],
            self.chapters,
        )
        source_field = parse_field(source)
        output_field = parse_field(output)
        source_editor = AtelScript(source_field.parts[rico.SCRIPT_INDEX].data)
        output_editor = AtelScript(output_field.parts[rico.SCRIPT_INDEX].data)

        self.assertEqual(source_editor.entity_count, 11)
        self.assertEqual(output_editor.entity_count, 17)
        self.assertEqual(
            struct.unpack_from("<H", output_field.header, 0x18C)[0],
            18,
        )
        stop_pc = output_editor.get_script_pointer(0, 2)
        self.assertEqual(output_editor.bytecode[stop_pc : stop_pc + 1], b"\x00")
        party_update_pc = output_editor.get_script_pointer(1, 1)
        self.assertEqual(
            output_editor.bytecode[party_update_pc : party_update_pc + 2],
            b"\xA7\x00",
        )
        rico_init = rico._normalized_party_init(
            rico.RICO_ID, rico.HUB_ENTRY_POSITION[:2]
        )
        rico_init_pc = output_editor.get_script_pointer(1, 0)
        self.assertEqual(
            output_editor.bytecode[rico_init_pc : rico_init_pc + len(rico_init)],
            rico_init,
        )
        director_pc = output_editor.get_script_pointer(0, 0)
        director = rico._sanitized_director(rico.HUB_MUSIC)
        self.assertEqual(
            output_editor.bytecode[director_pc : director_pc + len(director)],
            director,
        )
        self.assertEqual(output_editor.get_script_pointer(0, 1), stop_pc)

        # The native animated blue Path is the sole surviving retail behavior.
        for script_index in (0, 1):
            self.assertEqual(
                output_editor.get_script_pointer(
                    rico.HUB_PATH_ENTITY, script_index
                ),
                source_editor.get_script_pointer(
                    rico.HUB_PATH_ENTITY, script_index
                ),
            )
        for entity in (2, 3, 4, 5, 7, 8, 9):
            init_pc = output_editor.get_script_pointer(entity, 0)
            self.assertEqual(
                output_editor.bytecode[
                    init_pc : init_pc + len(rico.INERT_HIDDEN_INIT)
                ],
                rico.INERT_HIDDEN_INIT,
            )

        for marker in rico.HUB_MARKERS:
            entity = rico.HUB_MARKER_FIRST_ENTITY + marker.chapter_id - 1
            init_pc = output_editor.get_script_pointer(entity, 0)
            expected_init = rico._hub_marker_init(marker)
            self.assertEqual(
                output_editor.bytecode[
                    init_pc : init_pc + len(expected_init)
                ],
                expected_init,
            )
            self.assertNotIn(b"\x2A", expected_init)
            self.assertIn(b"\x20\x01\x80", expected_init)
            action_pc = output_editor.get_script_pointer(entity, 2)
            expected_action = rico._build_hub_marker_action(
                action_pc,
                marker,
                rico.CHAPTER_FIELDS[1][marker.chapter_id],
                rico._hub_selection_exposition_ids(self.chapters)[
                    marker.chapter_id
                ],
            )
            self.assertEqual(
                output_editor.bytecode[
                    action_pc : action_pc + len(expected_action)
                ],
                expected_action,
            )
            self.assertEqual(
                output_editor.get_script_pointer(entity, 3),
                stop_pc,
            )

    def test_every_action_finish_drains_cross_before_control_is_restored(self) -> None:
        def finish_offsets(action: bytes, action_pc: int) -> list[int]:
            return [
                offset
                for offset in range(len(action))
                if action.startswith(
                    rico._playable_action_finish(action_pc + offset),
                    offset,
                )
            ]

        for chapter in self.chapters:
            (
                _source_field,
                _output_field,
                _source_editor,
                output_editor,
                contract,
                first_controller,
                exit_entity,
            ) = self._layout(
                chapter,
                self.sources[chapter.chapter_id],
                self.outputs[chapter.chapter_id],
            )
            for index, interaction in enumerate(contract.interactions):
                with self.subTest(chapter=chapter.chapter_id, node=interaction.name):
                    entity = first_controller + index
                    action_pc = output_editor.get_script_pointer(entity, 2)
                    action_end = output_editor.get_script_pointer(entity + 1, 0)
                    action = output_editor.bytecode[action_pc:action_end]
                    offsets = finish_offsets(action, action_pc)
                    custom_locked_count = sum(
                        (
                            len(stage.locked_dialogue_steps)
                            if stage.locked_dialogue_steps
                            else (
                                len(stage.locked_dialogue_states)
                                if stage.locked_dialogue_states
                                else int(bool(stage.locked_dialogue))
                            )
                        )
                        for stage in interaction.stages
                    )
                    choice_rejection_count = sum(
                        stage.choice_text is not None
                        for stage in interaction.stages
                    )
                    actor_gate_count = (
                        len(
                            rico.INTERACTION_ACTOR_BINDINGS.get(
                                chapter.chapter_id,
                                {},
                            ).get(interaction.name, ())
                        )
                        if (
                            interaction.hide_bound_actors_until_active
                            or (
                                chapter.chapter_id == 2
                                and interaction.name == "Hammer"
                            )
                        )
                        else 0
                    )
                    diagonal_contact_rejection_count = int(
                        chapter.chapter_id == 1
                        and interaction.name in ("cold window", "cooking counter")
                    )
                    self.assertEqual(
                        len(offsets),
                        1
                        + len(interaction.stages)
                        + custom_locked_count
                        + choice_rejection_count
                        + actor_gate_count
                        + diagonal_contact_rejection_count,
                    )
                    for offset in offsets:
                        finish = rico._playable_action_finish(action_pc + offset)
                        self.assertIn(
                            b"\x31" + struct.pack("<H", rico.PAD_MASK_CROSS),
                            finish,
                        )
                        self.assertTrue(finish.endswith(b"\xFE\x53\x00"))

            exit_pc = output_editor.get_script_pointer(exit_entity, 2)
            exit_action = output_editor.bytecode[exit_pc:]
            expected_finish_count = len(contract.exit_locked_steps) + int(
                contract.exit_transition is None
            )
            self.assertEqual(
                len(finish_offsets(exit_action, exit_pc)),
                expected_finish_count,
            )

    def test_screenplay_stage_directions_are_not_routed_as_gameplay_dialogue(self) -> None:
        for chapter in self.chapters:
            contract = rico._playable_chapter_contract(chapter.chapter_id)
            forbidden = {
                index
                for index, block in enumerate(chapter.blocks)
                if block.lstrip().startswith("[")
            }
            routed = set(
                ref for ref in contract.exit_dialogue if isinstance(ref, int)
            )
            for interaction in contract.interactions:
                routed.update(
                    ref
                    for ref in interaction.repeat_dialogue
                    if isinstance(ref, int)
                )
                for stage in interaction.stages:
                    routed.update(
                        ref
                        for ref in (
                            *stage.dialogue,
                            *stage.after_dialogue,
                            *stage.locked_dialogue,
                            *stage.rejection_dialogue,
                        )
                            if isinstance(ref, int)
                    )
            if contract.exit_transition is not None:
                transition = contract.exit_transition
                routed.update(
                    ref
                    for refs in (
                        transition.doorway_dialogue,
                        transition.firewood_dialogue,
                        transition.sickness_dialogue,
                        transition.loss_dialogue,
                        transition.funeral_dialogue,
                    )
                    for ref in refs
                    if isinstance(ref, int)
                )
            self.assertTrue(
                forbidden.isdisjoint(routed),
                f"Chapter {chapter.chapter_id} routes bracketed screenplay prose",
            )


if __name__ == "__main__":
    unittest.main()
