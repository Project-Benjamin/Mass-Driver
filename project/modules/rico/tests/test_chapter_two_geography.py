"""Retail doors, entry heights and callback isolation for the D Block route."""
from pathlib import Path
import json
import struct
import unittest
from unittest.mock import patch

from modules.rico import build as core, chapter_two as world
from modules.rico import chapter_two_resources as resources
from modules.rico import chapter_two_geography as geography
from modules.rico import chapter_two_opening as opening
from modules.rico.tests import test_chapter_two_integration as integration
from shared.tools.xgatel import AtelScript as ParsedScript, OpcodeInfo


DOORS = {
    "bar": {2: ("street", 5, 0)},
    "street": {31: ("bar", 0, 1), 29: ("commons", 0, 1),
               34: ("commons", 1, 1)},
    "commons": {4: ("street", 2, 0), 5: ("street", 1, 0)},
}
EXTRA_BASE = {code: OpcodeInfo(code, f"OP_{code:02X}", size, (), False)
              for code, size in {0x15: 1, 0x1B: 7, 0x1F: 2,
                                  0x3B: 6, 0x47: 6, 0x6F: 2, 0xC4: 2}.items()}
EXTRA_EXTENDED = {0x15: OpcodeInfo(0x15, "INIT_NPC_WITH_PALETTE", 5, (), False, True)}


def traced(editor, entity, slot, flags=0, **kwargs):
    with patch.dict(integration.BASE, EXTRA_BASE), patch.dict(integration.EXTENDED, EXTRA_EXTENDED):
        return integration.trace(ParsedScript(editor.to_bytes()),
                                 editor.get_script_pointer(entity, slot), flags, **kwargs)


class ChapterTwoGeographyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = core.ROOT / "project.local.json"
        if not config.is_file():
            raise unittest.SkipTest("Configure retail Disc1 for native geography checks")
        source = Path(json.loads(config.read_text())["sources"]["retail_disc1"]["path"])
        if not source.is_file():
            raise unittest.SkipTest("Configured retail Disc1 is unavailable")
        cls.reader = core.DiscReader(source, 1)
        cls.fields = {**resources.WORLD_FIELDS, "main": core.CHAPTER_FIELDS[1][2],
                      "bedroom": core.CHAPTER_TWO_BEDROOM_FIELD}
        chapters = {chapter.chapter_id: chapter for chapter in core.load_chapters()}
        cls.native, cls.built, cls.editors = {}, {}, {}
        for room in ("bar", "street", "commons"):
            spec = resources.ROOM_SPECS[room]
            source = cls.reader.canonical(core._field_bundle_id(spec["donor"]))
            cls.native[room] = core.parse_field(source)
            result = world.build_room(room, source, fields=cls.fields, chapter=chapters[2],
                next_chapter=chapters[3], return_hub=core.HUB_FIELDS[1], spec=spec)
            cls.built[room] = core.parse_field(result)
            cls.editors[room] = core.AtelScript(cls.built[room].parts[5].data)
        # Match release preparation's two-stage inherited main-room build.
        source = cls.reader.canonical(core._field_bundle_id(218))
        inherited = core._build_scene_bundle(source, chapters[2], core.HUB_FIELDS[1], chapters[3])
        main_spec = {"entry": (-125, 134, 38), "landmarks": {
            "hammer": opening.MAIN_HAMMER, "schedule": (115, -187, 62),
            "exit": opening.HAMMER_ENTRANCE, "suzarn": opening.MAIN_SUZARN},
            "npcs": {"suzarn": {"entity": 4, "bank": 0}}}
        result = world.build_room("main", inherited, fields=cls.fields, chapter=chapters[2],
            next_chapter=chapters[3], return_hub=core.HUB_FIELDS[1], spec=main_spec, inherited=True)
        cls.built["main"] = core.parse_field(result)
        cls.editors["main"] = core.AtelScript(cls.built["main"].parts[5].data)

    def test_native_route_survives_final_dialogue_presentation(self):
        from modules.rico.dialogue_portraits import present_field
        from modules.rico.release_presentation import speaker_portraits
        for room in ("bar", "street", "commons", "main"):
            source = self.built[room].source
            result = present_field(source, speaker_portraits(),
                                   colorize=lambda text: "<Opcode:0B:FE>" + text)
            after = core.parse_field(result.bundle)
            for index in (1, 2, 3, 4, 6, 8):
                self.assertEqual(after.parts[index].data, self.built[room].parts[index].data)
            if room in ("bar", "street"):
                if room == "street":
                    self.assertEqual(result.calls, 0, "All street residents speak anonymously")
                else:
                    self.assertGreater(result.calls, 0, "Latina retains her named portrait")
                presented = core.AtelScript(after.parts[5].data)
                for entity, target, entry, direction in geography.DOOR_ROUTES[room]:
                    body = geography.native_door_body(target, entry, direction, self.fields)
                    pc = presented.get_script_pointer(entity, 2)
                    self.assertEqual(presented.bytecode[pc:pc + len(body)], body,
                                     "Portrait presentation changed the physical door routine")

    def test_route_uses_the_bar_and_street_between_champion_and_dorm(self):
        self.assertEqual(resources.ROOM_SPECS["bar"]["donor"], 217)
        self.assertEqual(resources.ROOM_SPECS["street"]["donor"], 196)
        self.assertEqual(resources.ROOM_SPECS["commons"]["donor"], 211)
        expected = {"main": {"bar"}, "bar": {"main", "street"},
                    "street": {"bar", "commons"}}
        for room, destinations in expected.items():
            actual = {step.target for action in world.actions_for(room)
                      for step in action.steps if step.target}
            self.assertEqual(actual, destinations, room)

    def test_native_door_actors_walk_to_the_correct_reciprocal_entry(self):
        flags = 0xFFFF
        for room, doors in DOORS.items():
            for entity, (target, entry, direction) in doors.items():
                with self.subTest(room=room, entity=entity):
                    commands, variables = traced(self.editors[room], entity, 2, flags)
                    exits = [ins for ins in commands if ins.opcode == 0x47]
                    self.assertEqual(len(exits), 1)
                    self.assertEqual(exits[0].raw, bytes((0x47, direction))
                        + struct.pack("<HH", self.fields[target] | 0x8000, entry | 0x8000))
                    self.assertEqual(commands[-1].opcode, 0x5B)
                    self.assertNotIn(0x98, [ins.opcode for ins in commands])
                    self.assertEqual(variables[world.LOCAL], flags)
                    self.assertIn(b"\xC4" + bytes((direction,)), [ins.raw for ins in commands])
                    self.assertIn(b"\x1F\x11", [ins.raw for ins in commands])
                    self.assertFalse(any(ins.extended_opcode in (0x18, 0x19, 0x1A) for ins in commands),
                                     "Live party teardown/reload resets the walker before OP47")
                    self.assertNotIn(0x31, [ins.opcode for ins in commands],
                                     "Physical door actions must not acquire a second Cross-release gate")

    def test_native_entry_tables_floor_and_trigger_data_survive_compilation(self):
        entries = {"bar": (0, 1), "street": (1, 2, 5), "commons": (0, 1)}
        for room, indices in entries.items():
            before, after = self.native[room], self.built[room]
            for part in (1, 2, 3, 4, 8):
                self.assertEqual(after.parts[part].data, before.parts[part].data,
                                 f"{room} native component{part} changed")
            triangles, neighbours = resources._layer_zero_geometry(after.parts[1].data)
            entry_triangles = []
            for index in indices:
                entry = core.mass_driver._read_field_entry(after.parts[5].data, index)
                self.assertEqual(entry, core.mass_driver._read_field_entry(before.parts[5].data, index))
                hits = [n for n, triangle in enumerate(triangles)
                        if resources._inside((entry.x, entry.z), triangle)]
                self.assertTrue(hits, (room, index, entry))
                entry_triangles.append(hits[0])
            reachable, pending = {entry_triangles[0]}, [entry_triangles[0]]
            while pending:
                for neighbour in neighbours[pending.pop()]:
                    if neighbour not in reachable:
                        reachable.add(neighbour)
                        pending.append(neighbour)
            self.assertTrue(set(entry_triangles) <= reachable,
                            f"{room} reciprocal entries have disconnected floors")
        # These real landings/slopes must not be flattened to the bar's Y=0.
        expected_heights = {("bar", 1): {-31}, ("street", 1): {-27},
                            ("street", 5): {234, 260, 285}}
        for (room, index), heights in expected_heights.items():
            entry = core.mass_driver._read_field_entry(self.built[room].parts[5].data, index)
            triangles, _ = resources._layer_zero_geometry(self.built[room].parts[1].data)
            triangle = next(t for t in triangles if resources._inside((entry.x, entry.z), t))
            self.assertEqual({vertex[1] for vertex in triangle}, heights)

    def test_rico_uses_each_native_entry_without_a_position_override(self):
        for room, editor in self.editors.items():
            characters = core._registered_character_entities(editor)
            self.assertIn(5, characters)
            commands, _ = traced(editor, characters[5], 0)
            self.assertEqual([ins.raw for ins in commands if ins.opcode == 0x16], [b"\x16\x05\x80"])
            self.assertFalse(any(ins.opcode in (0x19, 0x1A, 0x1B) for ins in commands), room)
            update, _ = traced(editor, characters[5], 1)
            self.assertEqual([ins.raw for ins in update], [b"\xA7", b"\x00"])
        for room in ("bar", "street"):
            director, _ = traced(self.editors[room], 0, 0)
            self.assertEqual([ins.raw[2] for ins in director if ins.extended_opcode == 0x18], [5])
            tracks = [integration.word(ins.raw) & 0x7FFF for ins in director if ins.opcode == 0x75]
            self.assertEqual(tracks, [71])

    def test_bar_and_street_retire_every_native_story_entrypoint(self):
        for room in ("bar", "street"):
            old = core.AtelScript(self.native[room].parts[5].data)
            current = self.editors[room]
            for entity in range(current.entity_count):
                for slot in range(32):
                    self.assertGreaterEqual(current.get_script_pointer(entity, slot), len(old.bytecode),
                                            (room, entity, slot))
            # Former Fei controller is hidden and cannot receive player input.
            commands, _ = traced(current, 1, 0)
            self.assertNotIn(0x16, [ins.opcode for ins in commands])
            self.assertTrue(any(ins.opcode in (0x23, 0x29) for ins in commands))

    def test_ambient_sprites_keep_native_banks_palettes_layers_and_seated_poses(self):
        for room, residents in (("bar", geography.BAR_RESIDENT_INITS),
                                ("street", geography.STREET_RESIDENT_INITS)):
            old = core.AtelScript(self.native[room].parts[5].data)
            current = self.editors[room]
            for entity, native_hex in residents.items():
                with self.subTest(room=room, entity=entity):
                    expected = bytes.fromhex(native_hex)
                    pc = old.get_script_pointer(entity, 0)
                    self.assertEqual(old.bytecode[pc:pc + len(expected)], expected)
                    commands, _ = traced(current, entity, 0)
                    self.assertEqual(b"".join(ins.raw for ins in commands), expected)
                    action, _ = traced(current, entity, 2)
                    self.assertTrue(any(ins.opcode == 0xF5 for ins in action))
                    self.assertTrue(any(ins.extended_opcode == 0x53 for ins in action))
                    if room == "bar":
                        update, _ = traced(current, entity, 1)
                        native_pose = b"\x2C\x02" + (b"\x6F\x07" if entity in (11, 12) else b"")
                        self.assertEqual(b"".join(ins.raw for ins in update), native_pose + b"\x00")

    def test_physical_doors_have_no_competing_hidden_action_carriers(self):
        for room in ("bar", "street", "commons"):
            editor = self.editors[room]
            old_count = core.AtelScript(self.native[room].parts[5].data).entity_count
            for offset, action in enumerate(world.actions_for(room)):
                if action.landmark not in resources.ROOM_SPECS[room].get("native_actions", {}):
                    continue
                entity = old_count + 3 + offset
                commands, _ = traced(editor, entity, 0)
                self.assertFalse(any(ins.opcode == 0x18 for ins in commands),
                                 f"{room}/{action.landmark} retains a competing collision hotspot")
                commands, _ = traced(editor, entity, 2)
                self.assertEqual([ins.raw for ins in commands], [b"\x00"])

    def test_champion_stairs_require_completed_opening_and_reciprocal_points_are_clear(self):
        ready = sum(1 << world.BITS[name] for name in ("room_intro", "hammer", "delivery"))
        for room, donor, target in (("main", 218, "bar"), ("bar", 217, "main")):
            source = self.built[room]
            editor = self.editors[room]
            for flags, inside in ((ready, False), (ready, True)):
                commands, _ = traced(editor, 3, 1, flags, trigger_inside=inside)
                exits = [ins for ins in commands if ins.opcode == 0x98]
                self.assertEqual([ins.raw for ins in exits],
                    [b"\x98" + struct.pack("<HH", self.fields[target] | 0x8000, 0x8001)] if inside else [])
            if room == "main":
                for flags in (0, 1 << world.BITS["room_intro"]):
                    commands, _ = traced(editor, 3, 1, flags, trigger_inside=True)
                    self.assertFalse(any(ins.opcode in (0x47, 0x98) for ins in commands))
            entry = core.mass_driver._read_field_entry(source.parts[5].data, 1)
            polygon = [struct.unpack_from("<hhh", source.parts[8].data, offset)
                       for offset in range(0, 24, 6)]
            inside = (resources._inside((entry.x, entry.z), polygon[:3])
                      or resources._inside((entry.x, entry.z), (polygon[0], polygon[2], polygon[3])))
            self.assertFalse(inside, f"{room} return point immediately retriggers its stairs")
            triangles, _ = resources._layer_zero_geometry(source.parts[1].data)
            floor = next(t for t in triangles if resources._inside((entry.x, entry.z), t))
            expected_y = 62 if room == "main" else -31
            self.assertEqual({vertex[1] for vertex in floor}, {expected_y})
            trigger_y = 62 if room == "main" else -107
            self.assertEqual({vertex[1] for vertex in polygon}, {trigger_y})
            # Native CB00 also requires planeY < feetY < planeY + height.
            # Exercise real landing height and a conservative one-unit floor
            # rounding offset, plus vertical overlap itself. Neither return
            # depends on a retired native arrival walk to escape the trigger.
            for feet_y in (expected_y, expected_y + 1, trigger_y + 1):
                for height in (64, 96, 128):
                    triggered = trigger_y < feet_y < trigger_y + height and inside
                    self.assertFalse(triggered, (room, entry, feet_y, height))
            self.assertTrue(trigger_y < expected_y + 1 < trigger_y + 96,
                            "Fixture must exercise an overlapping native Y interval")
            # Feed the computed native containment to the actual compiled
            # UPDATE, rather than assuming that arrival is outside it.
            commands, _ = traced(editor, 3, 1, ready,
                                 trigger_inside=trigger_y < expected_y + 1 < trigger_y + 96 and inside)
            self.assertFalse(any(ins.opcode in (0x47, 0x98) for ins in commands))


if __name__ == "__main__":
    unittest.main()
