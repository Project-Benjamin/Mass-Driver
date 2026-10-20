"""Every retained resident speaks uniquely, with safe native portrait changes."""
import struct
import unittest
from unittest.mock import patch

from modules.rico import build as core, chapter_two as world
from modules.rico import chapter_two_ambient as ambient, chapter_two_geography as geography
from modules.rico import chapter_two_resources as resources
from modules.rico.dialogue_portraits import _decode, present_field, NO_PORTRAIT
from modules.rico.dialogue_presentation import plan_dialogue
from modules.rico.release_presentation import speaker_portraits
from modules.rico.tests import test_chapter_two_geography as route_tests
from shared.tools.xgdialog import encode_text, decode_text, parse_dialogue


def presented_windows(bundle, entity, prior_portrait=46):
    """Execute the emitted CALL/RETURN path, observing each window's portrait."""
    field = core.parse_field(bundle)
    script = core.AtelScript(field.parts[5].data)
    _, instructions = _decode(field.parts[5].data)
    pc, stack, portrait, windows, unlocked = script.get_script_pointer(entity, 2), [], prior_portrait, [], False
    for _ in range(1000):
        instruction = instructions[pc]
        raw, opcode = instruction.raw, instruction.opcode
        after = pc + instruction.size
        if opcode == 0:
            if stack:
                raise AssertionError("Conversation stopped inside a portrait helper")
            return windows, portrait, unlocked
        if opcode == 0x05:
            stack.append(after)
            pc = struct.unpack_from("<H", raw, 1)[0]
        elif opcode == 0x0D:
            pc = stack.pop()
        elif opcode == 0x31:
            pc = struct.unpack_from("<H", raw, 3)[0]  # Released Cross.
        elif opcode == 0x01:
            pc = struct.unpack_from("<H", raw, 1)[0]
        else:
            if instruction.extended_opcode == 0x0D:
                portrait = struct.unpack_from("<H", raw, 2)[0] & 0x7FFF
            elif instruction.extended_opcode == 0x53:
                unlocked = True
            elif opcode == 0xF5:
                windows.append((struct.unpack_from("<H", raw, 1)[0], portrait))
            pc = after
    raise AssertionError("Resident conversation never returned control")


class ChapterTwoAmbientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        route_tests.ChapterTwoGeographyTests.setUpClass()
        cls.fixture = route_tests.ChapterTwoGeographyTests
        cls.conversations = {room: ambient.load_conversations(room) for room in ("bar", "street")}

    def test_all_fourteen_visible_residents_have_distinct_npc_only_monologues(self):
        first_lines, keys = set(), set()
        for room, expected in (("bar", geography.BAR_RESIDENT_INITS),
                               ("street", geography.STREET_RESIDENT_INITS)):
            self.assertEqual(set(self.conversations[room]), set(expected))
            for conversation in self.conversations[room].values():
                first_lines.add(conversation.blocks[0])
                keys.add(conversation.key)
                self.assertTrue(conversation.blocks)
                self.assertTrue(conversation.native_dialogue_ids)
        self.assertEqual(len(first_lines), 14)
        self.assertEqual(len(keys), 14)

    def test_latina_is_the_only_named_resident_and_anonymous_speech_has_no_label(self):
        named = [(room, entity, row.speaker) for room, rows in self.conversations.items()
                 for entity, row in rows.items() if row.speaker]
        self.assertEqual(named, [("bar", 7, "Latina")])
        for room, rows in self.conversations.items():
            for entity, row in rows.items():
                for text in row.blocks:
                    segments = plan_dialogue(text)
                    self.assertNotIn("<Rico>\n", text, "Rico listens without a spoken reply")
                    self.assertEqual({segment.speaker for segment in segments}, {row.speaker}, (room, entity, text))

    def test_all_authored_blocks_encode_and_layout_preserves_their_words(self):
        for rows in self.conversations.values():
            for row in rows.values():
                for text in row.blocks:
                    self.assertEqual(decode_text(encode_text(text)), text)
                    core._reflow_dialogue_text(text)
                    self.assertTrue(plan_dialogue(text))

    def test_resident_actions_repeat_without_state_writes_travel_or_pose_changes(self):
        for room, rows in self.conversations.items():
            for entity, row in rows.items():
                for flags in (0, 0xFFFF):
                    commands, variables = route_tests.traced(self.fixture.editors[room], entity, 2, flags)
                    self.assertEqual(variables, {world.STATE: flags, world.LOCAL: flags})
                    self.assertEqual(len([ins for ins in commands if ins.opcode == 0xF5]), len(row.blocks))
                    self.assertFalse(any(ins.opcode in (0x19, 0x1B, 0x47, 0x4A, 0x98, 0x3A, 0x3B)
                                         for ins in commands))
                    self.assertTrue(any(ins.extended_opcode == 0x54 for ins in commands))
                    self.assertTrue(any(ins.extended_opcode == 0x53 for ins in commands))
                    self.assertEqual(commands[-1].opcode, 0)
                    for index, ins in enumerate(commands):
                        if ins.opcode == 0xF5:
                            self.assertEqual(commands[index - 1].raw, b"\xFE\x0D\xFC\x80")

    def test_only_script_and_appended_dialogue_change_from_silent_residents(self):
        chapters = {chapter.chapter_id: chapter for chapter in core.load_chapters()}
        for room in ("bar", "street"):
            source = self.fixture.native[room].source
            with patch.object(ambient, "load_conversations", return_value={}), \
                    patch.object(geography, "install_resident_interactions"):
                before = core.parse_field(world.build_room(room, source, fields=self.fixture.fields,
                    chapter=chapters[2], next_chapter=chapters[3], return_hub=core.HUB_FIELDS[1],
                    spec=resources.ROOM_SPECS[room]))
            after = self.fixture.built[room]
            self.assertEqual(before.header[0x18C:], after.header[0x18C:])
            for index in (0, 1, 2, 3, 4, 6, 8):
                self.assertEqual(before.parts[index].data, after.parts[index].data)
            old = parse_dialogue(before.parts[7].data).blocks
            new = parse_dialogue(after.parts[7].data).blocks
            self.assertEqual(len(new) - len(old), sum(len(row.blocks) for row in self.conversations[room].values()))
            self.assertEqual([(b.width, b.height, b.payload) for b in old],
                             [(b.width, b.height, b.payload) for b in new[:len(old)]])

    def test_presented_anonymous_then_latina_use_only_npc_portraits_on_every_page(self):
        portraits = speaker_portraits()
        self.assertIn("Latina", portraits)
        result = present_field(self.fixture.built["bar"].source, portraits,
                               colorize=lambda text: "<Opcode:0B:FE>" + text)
        records = parse_dialogue(core.parse_field(result.bundle).parts[7].data).blocks
        windows, final, unlocked = presented_windows(result.bundle, 14, prior_portrait=5)
        self.assertEqual([portrait for _, portrait in windows], [NO_PORTRAIT])
        self.assertEqual(final, NO_PORTRAIT)
        self.assertTrue(unlocked)
        named, final, unlocked = presented_windows(result.bundle, 7, prior_portrait=final)
        # Her single three-line monologue reflows into two native pages
        # after reserving the portrait width and yellow speaker-name row.
        self.assertEqual([portrait for _, portrait in named],
                         [portraits["Latina"], portraits["Latina"]])
        self.assertEqual(final, NO_PORTRAIT)
        self.assertTrue(unlocked)
        for block, portrait in windows + named:
            text = records[block].text
            if portrait == NO_PORTRAIT:
                self.assertFalse(text.startswith("<Opcode:0B:FE>"))
            else:
                self.assertTrue(text.startswith("<Opcode:0B:FE>"))

    def test_every_presented_resident_uses_only_its_own_label_and_portrait(self):
        portraits = speaker_portraits()
        for room, rows in self.conversations.items():
            result = present_field(self.fixture.built[room].source, portraits)
            records = parse_dialogue(core.parse_field(result.bundle).parts[7].data).blocks
            for entity, row in rows.items():
                windows, final, unlocked = presented_windows(result.bundle, entity)
                self.assertTrue(unlocked)
                self.assertEqual(final, NO_PORTRAIT)
                for block, portrait in windows:
                    text = records[block].text
                    self.assertNotIn("<Rico>\n", text, "Rico must remain a silent listener")
                    expected = portraits[row.speaker] if row.speaker else NO_PORTRAIT
                    self.assertEqual(portrait, expected, (room, entity, text))


if __name__ == "__main__":
    unittest.main()
