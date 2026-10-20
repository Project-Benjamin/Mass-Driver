"""Native bytecode and donor-floor checks for the three-person room opening."""
import json
from pathlib import Path
import struct
import unittest

from modules.rico import chapter_two_opening as opening
from modules.rico import chapter_two_scenes as scenes
from modules.rico.build import DiscReader
from modules.rico.tests.test_chapter_two_scenes import decode_linear
from shared.paths import PROJECT_ROOT
from shared.tools.xgfield import parse_field
from modules.soylent_system.base import _point_inside_triangle, _walkmesh_layer


def make_scene(base=0x2400):
    calls = []
    def dialogue(key, start=0, stop=None):
        calls.append((key, start, stop))
        return b"\xD2" + struct.pack("<H", len(calls)) + b"\x01\x9C"
    return opening.build_room_introduction(base, rico_entity=13, suzarn_entity=4,
        hammer_entity=19, dialogue=dialogue), calls


class RoomOpeningTests(unittest.TestCase):
    def test_hammer_waits_for_invitation_before_climbing_then_reports_from_room(self):
        scene, calls = make_scene()
        self.assertEqual(calls, [("room_first", 0, None), ("hammer_report", 0, 2),
                                ("hammer_report", 2, 10), ("hammer_report", 10, None)])
        code = list(decode_linear(scene.body))
        events = [(ins.opcode, ins.raw[1:]) for ins in code if ins.opcode in (0x09, 0xD2)]
        self.assertLess(events.index((0xD2, b"\x02\x00\x01")), events.index((0x09, b"\x13\x31")))
        self.assertLess(events.index((0x09, b"\x13\x32")), events.index((0xD2, b"\x03\x00\x01")))
        final_line = events.index((0xD2, b"\x04\x00\x01"))
        for call in ((0x09, b"\x04\x31"), (0x09, b"\x13\x33")):
            self.assertLess(final_line, events.index(call))
            self.assertLess(events.index(call), events.index((0x09, b"\x0D\x34")))
        self.assertEqual(scene.donor_field, 218)
        self.assertEqual(scene.required_resource_ids, ())

    def test_cast_stays_visible_controls_locked_and_all_scripts_decode(self):
        for base in (0, 0x2400):
            scene, _ = make_scene(base)
            main = list(decode_linear(scene.body))
            actor = [ins for routine in scene.actor_routines for ins in decode_linear(routine.body)]
            self.assertEqual({ins.raw[1] for ins in main if ins.opcode == 0x24}, {4, 13, 19})
            self.assertFalse(any(ins.opcode in (0x25, 0x27, 0x29) for ins in main + actor))
            self.assertFalse(any(ins.extended_opcode == 0x53 for ins in main + actor))
            self.assertEqual(len({(r.entity, r.script_index) for r in scene.actor_routines}),
                             len(scene.actor_routines))
            self.assertTrue(all(r.body.endswith(b"\x00") for r in scene.actor_routines))
            walks = [ins for ins in actor if ins.opcode == 0x4B]
            self.assertEqual(len(walks), 7)
            self.assertTrue(all((struct.unpack_from("<H", ins.raw, 6)[0] & 0x7FFF) == 120
                                for ins in walks))

    def test_revisit_hammer_init_uses_final_floor_and_authentic_bank(self):
        body = opening.hammer_init()
        self.assertEqual(body[:3], b"\x0B\x04\x80")
        self.assertEqual(body[3:9], b"\x19" + struct.pack("<hh", *opening.MAIN_HAMMER[:2]) + b"\xC0")
        self.assertNotIn(b"\x23", body)
        with self.assertRaisesRegex(ValueError, "distinct"):
            opening.build_room_introduction(0, rico_entity=4, suzarn_entity=4,
                hammer_entity=19, dialogue=lambda *_: b"\x00")

    def test_opening_does_not_overwrite_bandage_and_both_leave_npcs_passable(self):
        opening_scene, _ = make_scene()
        bandage = scenes.build_bandage(0x5000, 13, 19, lambda *_: b"\xD2\x00\x00\x01\x9C")
        occupied = {(actor.entity, actor.script_index) for actor in opening_scene.actor_routines}
        self.assertFalse(occupied & {(actor.entity, actor.script_index) for actor in bandage.actor_routines})
        restored = {actor.entity: actor.body for actor in opening_scene.actor_routines
                    if actor.script_index == opening.FIRST_SCRIPT + 4}
        self.assertEqual(restored, {13: b"\x20\x00\x80\x00", 4: b"\x20\x0D\x80\x00",
                                   19: b"\x20\x0D\x80\x00"})
        hammer_restore = next(actor.body for actor in bandage.actor_routines
                              if (actor.entity, actor.script_index) == (19, 28))
        self.assertEqual(hammer_restore, b"\x20\x0D\x80\x00")
        for body in (opening.hammer_init(), opening.npc_init(0, opening.MAIN_SUZARN[:2])):
            self.assertIn(b"\x20\x0D\x80", body)


class RoomOpeningNativeGeometryTests(unittest.TestCase):
    def test_conversation_is_on_clear_floor_and_entire_climb_is_continuous(self):
        config = PROJECT_ROOT / "project.local.json"
        if not config.is_file():
            self.skipTest("Local retail source configuration is unavailable")
        source = Path(json.loads(config.read_text())["sources"]["retail_disc1"]["path"])
        if not source.is_file():
            self.skipTest("Local retail Disc1 is unavailable")
        field = parse_field(DiscReader(source, 1).canonical(606 + 2 * 218))
        scene, _ = make_scene()
        self.assertEqual(scenes.validate_geometry(scene, field.parts[1].data), {"paths": 4, "segments": 7})
        triangles = _walkmesh_layer(field.parts[1].data, 0)
        for x, z, index in (opening.MAIN_RICO, opening.MAIN_SUZARN, opening.MAIN_HAMMER):
            self.assertTrue(_point_inside_triangle((x, z), triangles[index]))
            self.assertEqual({vertex[1] for vertex in triangles[index]}, {0})
        # Native doorway and upper landing anchor the route, avoiding an
        # assumed staircase direction or the former intermediate tread.
        script = field.parts[5].data
        from shared.tools.xgatel import AtelScript
        code = AtelScript(script).bytecode
        self.assertEqual(code[0x079E:0x07A4], b"\x19" + struct.pack("<hh", *opening.HAMMER_ENTRANCE[:2]) + b"\xC0")
        self.assertEqual(code[0x07C9:0x07CF], b"\x4A" + struct.pack("<hh", *opening.HAMMER_APPROACH[-1][:2]) + b"\xC0")


if __name__ == "__main__":
    unittest.main()
