"""Check native music evidence and explicitly historical prepared scripts.

The legacy fixture retains battle-return audio regression coverage. Current
interludes never dispatch those battles and have separate release-path tests.
"""

import hashlib
import json
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from modules.rico import build as core, chapter_two as world
from modules.rico import chapter_two_music as music, chapter_two_resources as resources
from modules.rico.tests import test_chapter_two_integration as integration
from shared.tools.xgatel import AtelScript, OpcodeInfo


def played_tracks(instructions):
    return [struct.unpack_from("<H", ins.raw, 1)[0] & 0x7FFF
            for ins in instructions if ins.opcode == 0x75]


class ChapterTwoMusicPolicyTests(unittest.TestCase):
    def test_champion_config_uses_the_native_room_track(self):
        chapter = json.loads((core.CONTENT_ROOT / "chapter_02_the_champ.json").read_text())
        self.assertEqual(chapter["music"], 47)

    def test_room_overrides_preserve_the_sewer_and_other_chapter_cues(self):
        for room in ("main", "bedroom"):
            self.assertEqual(music.room_music(room, 34), 47)
        for room in ("commons", "intake"):
            self.assertEqual(music.room_music(room, 34), 71)
        for room in ("sewer_entry", "sewer_hub", "sewer_key", "sewer_drain"):
            self.assertEqual(music.room_music(room, 34), 13)
        self.assertEqual(music.room_music("prep", 35), 35)


class ChapterTwoPreparedMusicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = core.ROOT / "project.local.json"
        if not config.is_file():
            raise unittest.SkipTest("Configured retail donor required")
        path = Path(json.loads(config.read_text())["sources"]["retail_disc1"]["path"])
        if not path.is_file():
            raise unittest.SkipTest("Configured retail donor unavailable")
        cls.reader = core.DiscReader(path, 1)
        expand = world.expand_replacements
        with patch.object(world, "expand_replacements", side_effect=lambda *args, **kwargs:
                          expand(*args, **{**kwargs, "interludes": False})):
            cls.prepared = core.prepare_replacements(cls.reader, core.load_chapters())

    def script(self, disc, field):
        data = next(item.data for item in self.prepared[disc]
                    if item.canonical_id == core._field_bundle_id(field))
        return core.AtelScript(core.parse_field(data).parts[5].data)

    def traced(self, disc, field, entity, slot, flags=0):
        script = self.script(disc, field)
        # Native FE84 has four words; FE7F is the two-byte battle return.
        # These are observed events here, not a simulated battle execution.
        metadata = {
            0x84: OpcodeInfo(0x84, "FIXED_BATTLE", 9, (), False, True),
            0x7F: OpcodeInfo(0x7F, "BATTLE_RETURN", 1, (), False, True),
            0x0E: OpcodeInfo(0x0E, "FADE_MUSIC", 5, (), False, True),
        }
        with patch.dict(integration.EXTENDED, metadata):
            return integration.trace(AtelScript(script.to_bytes()),
                                     script.get_script_pointer(entity, slot), flags)[0]

    def test_native_director_bytes_identify_champ_and_nortune_tracks(self):
        cases = (
            (1042, "61c0a85ede3b528d77252808ebc66238ee5d938244f21e36cb934f4470a54895", 47),
            (1066, "87707b40154d04bea8733038ac0130331697d3155ed13f3a431bf1ce0c079318", 71),
        )
        for canonical, expected_sha, track in cases:
            with self.subTest(canonical=canonical):
                data = self.reader.canonical(canonical)
                self.assertEqual(hashlib.sha256(data).hexdigest(), expected_sha)
                script = core.AtelScript(core.parse_field(data).parts[5].data)
                pc = script.get_script_pointer(0, 0)
                self.assertEqual(script.bytecode[pc:pc + 4], b"\xBC\x75" + struct.pack("<H", track | 0x8000))

    def test_prepared_room_init_reaches_correct_music_on_first_entry_and_revisit(self):
        for disc in (1, 2):
            fields = ((core.CHAPTER_FIELDS[disc][2], 47),
                      (core.CHAPTER_TWO_BEDROOM_FIELD, 47),
                      (resources.WORLD_FIELDS["commons"], 71),
                      (resources.WORLD_FIELDS["intake"], 71))
            for field, track in fields:
                for flags in (0, 0xFFFF):
                    with self.subTest(disc=disc, field=field, flags=flags):
                        instructions = self.traced(disc, field, 0, 0, flags)
                        self.assertEqual(played_tracks(instructions), [track])
                        music_index = next(i for i, ins in enumerate(instructions) if ins.opcode == 0x75)
                        later = instructions[music_index + 1:]
                        self.assertNotIn(0x0E, [ins.extended_opcode for ins in later])
                        self.assertLess(music_index, next((i for i, ins in enumerate(instructions)
                                                          if ins.opcode in (0x26, 0xD2, 0xF5)), len(instructions)))

    def test_delivery_and_room_introduction_do_not_stop_or_fade_the_selected_track(self):
        for disc in (1, 2):
            for field in (resources.WORLD_FIELDS["intake"], core.CHAPTER_FIELDS[disc][2]):
                for flags in (0, 0xFFFF):
                    with self.subTest(disc=disc, field=field, flags=flags):
                        instructions = self.traced(disc, field, 0, 1, flags)
                        self.assertEqual(played_tracks(instructions), [])
                        self.assertNotIn(0x0E, [ins.extended_opcode for ins in instructions])

    def test_prepared_stier_battle_restores_the_room_theme_after_return(self):
        for disc in (1, 2):
            instructions = self.traced(disc, resources.WORLD_FIELDS["prep"], 4, 2)
            self.assertEqual(played_tracks(instructions), [20, 47])
            battle_return = next(i for i, ins in enumerate(instructions) if ins.extended_opcode == 0x7F)
            restoration = [i for i, ins in enumerate(instructions) if ins.opcode == 0x75][-1]
            self.assertLess(battle_return, restoration)
            self.assertNotIn(0x0E, [ins.extended_opcode for ins in instructions[restoration:]])


if __name__ == "__main__":
    unittest.main()
