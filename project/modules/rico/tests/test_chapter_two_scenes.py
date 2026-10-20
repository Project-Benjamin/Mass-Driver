"""Inspect emitted ATEL choreography; native geometry needs local retail discs.

The compact instruction grammar below comes from Noah's opcode metadata, not
the scene builders. Keeping it here makes bytecode tests independent of a local
Noah checkout. These tests validate structure and floor coverage, not rendering.
"""
from dataclasses import replace
import json
from pathlib import Path
import struct
import unittest

from shared.paths import PROJECT_ROOT
from shared.tools.xgatel import (AtelScript, OpcodeArgument, OpcodeInfo,
                                 decode_instruction, reachable_instructions)
from shared.tools.xgfield import parse_field
from modules.rico import chapter_two_scenes as scenes
from modules.rico.build import DiscReader


# Native atelOpcodes.cpp instruction lengths, including the opcode byte(s).
BASE_SIZES = {
    0x00: 1, 0x01: 3, 0x09: 3, 0x16: 3, 0x19: 6, 0x1A: 2,
    0x20: 3, 0x24: 2, 0x25: 2, 0x26: 3, 0x2C: 2, 0x31: 5,
    0x33: 1, 0x4B: 8, 0x5F: 2, 0x60: 1, 0x63: 8, 0x64: 1,
    0x99: 1, 0x9A: 3, 0x9B: 5, 0x9C: 1, 0xA3: 8, 0xAC: 4,
    0xD2: 4, 0xEF: 3, 0xF1: 11, 0xF2: 9, 0xF4: 2, 0xF6: 2,
}
EXTENDED_SIZES = {
    0x0D: 4, 0x17: 4, 0x1E: 3, 0x41: 4, 0x42: 4, 0x4A: 4,
    0x4B: 2, 0x4D: 3, 0x53: 2, 0x54: 2, 0xA1: 6,
}
BASE = {
    opcode: OpcodeInfo(opcode, f"OP_{opcode:02X}", size,
                       (OpcodeArgument("addArgumentJumpLocation", 3, 2, "target"),)
                       if opcode == 0x31 else (), opcode in (0, 1))
    for opcode, size in BASE_SIZES.items()
}
EXTENDED = {
    opcode: OpcodeInfo(opcode, f"OPX_{opcode:02X}", size - 1, (), False, True)
    for opcode, size in EXTENDED_SIZES.items()
}
CASES = (
    ("arrival_delivery", scenes.build_arrival_delivery,
     {"fei_entity": 33, "doctor_entity": 8, "guard_entity": 10}),
    ("baptism", scenes.build_baptism, {"rico_entity": 19, "fei_entity": 1}),
    ("bandage", scenes.build_bandage, {"rico_entity": 1, "hammer_entity": 19}),
    ("finals", scenes.build_finals, {"rico_entity": 1, "fei_entity": 2}),
    ("crash", scenes.build_crash,
     {"rico_entity": 1, "fei_entity": 2, "witness_entity": 3}),
    ("flight", scenes.build_flight, {"rico_entity": 1}),
)


def emit_dialogue(key, start=0, stop=None):
    return bytes.fromhex("D2 00 00 00 9C")


def decode_linear(raw):
    script = AtelScript(bytes(0x84) + raw)
    pc = 0
    while pc < len(raw):
        instruction = decode_instruction(script, pc, BASE, EXTENDED)
        yield instruction
        pc += instruction.size


def install_scene(scene, base_pc):
    count = max(actor.entity for actor in scene.actor_routines) + 1
    header = bytearray(0x84 + count * 64)
    struct.pack_into("<I", header, 0x80, count)
    struct.pack_into("<H", header, 0x84, base_pc)
    body = bytearray(bytes(base_pc) + scene.body + b"\x00")
    for actor in scene.actor_routines:
        struct.pack_into("<H", header, 0x84 + actor.entity * 64 + actor.script_index * 2,
                         len(body))
        body.extend(actor.body)
    return AtelScript(bytes(header + body))


class ChapterTwoSceneBytecodeTests(unittest.TestCase):
    def test_arrival_frames_before_reveal_and_leaves_locked_under_black(self):
        from modules.rico import chapter_two_resources as resources

        scene = scenes.build_arrival_delivery(0x1234, fei_entity=33, doctor_entity=8,
                                              guard_entity=10, dialogue=emit_dialogue)
        director = list(decode_linear(scene.body))
        fades = [(i, struct.unpack_from("<H", ins.raw, 3)[0] & 0x7FFF)
                 for i, ins in enumerate(director) if ins.opcode == 0xF1]
        self.assertEqual([value for _, value in fades], [255, 0, 255])
        target = next(i for i, ins in enumerate(director) if ins.opcode == 0x63)
        eye = next(i for i, ins in enumerate(director) if ins.opcode == 0xA3)
        self.assertLess(fades[0][0], target)
        self.assertLess(eye, fades[1][0])
        self.assertEqual(struct.unpack_from("<hhh", director[target].raw, 1), resources.ARRIVAL_CAMERA_TARGET)
        self.assertEqual(struct.unpack_from("<hhh", director[eye].raw, 1), resources.ARRIVAL_CAMERA_EYE)
        calls = [(i, ins.raw[1], ins.raw[2] & 31) for i, ins in enumerate(director) if ins.opcode == 0x09]
        self.assertEqual([(entity, slot) for _, entity, slot in calls],
                         [(33, 24), (8, 24), (10, 24), (33, 28), (8, 28), (10, 28)])
        for index, _, _ in calls[:3]:
            self.assertLess(index, fades[1][0])
        for index, _, _ in calls[3:]:
            self.assertGreater(index, fades[-1][0])
        visible = [(i, ins.raw[1]) for i, ins in enumerate(director) if ins.opcode == 0x24]
        self.assertEqual([entity for _, entity in visible], [33, 8, 10])
        for index, _ in visible:
            self.assertLess(calls[2][0], index)
            self.assertLess(index, fades[1][0])
        dialogue = next(i for i, ins in enumerate(director) if ins.opcode == 0xD2)
        self.assertLess(fades[1][0], dialogue)
        self.assertLess(dialogue, fades[-1][0])
        self.assertNotIn(0x9A, [ins.opcode for ins in director])
        self.assertNotIn(0x53, [ins.extended_opcode for ins in director])
        actor_code = [ins for actor in scene.actor_routines for ins in decode_linear(actor.body)]
        self.assertEqual(sum(ins.extended_opcode == 0x4A for ins in actor_code), 1)
        self.assertEqual(sum(ins.extended_opcode == 0x4D for ins in actor_code), 1)
        poses = [ins.raw for ins in actor_code if ins.extended_opcode in (0x4A, 0x4B, 0x4D)]
        self.assertEqual(poses, [bytes.fromhex("FE 4A 77 80"), b"\xFE\x4B", b"\xFE\x4D\x00"])
        # No idle/reaction after revealing Fei may stand him up again.
        self.assertNotIn(0x2C, [ins.opcode for ins in actor_code])
        self.assertEqual(scene.required_resource_ids, (2455,))
        self.assertEqual(scene.motion_paths, ())

    def test_arrival_requires_three_distinct_concrete_actors(self):
        for fei, doctor, guard in ((33, 33, 10), (33, 8, 33), (33, 8, 8), (33, 8, 0xFD)):
            with self.subTest(cast=(fei, doctor, guard)), self.assertRaises(ValueError):
                scenes.build_arrival_delivery(0, fei_entity=fei, doctor_entity=doctor,
                                              guard_entity=guard, dialogue=emit_dialogue)

    def test_complete_scenes_decode_at_zero_and_relocated_addresses(self):
        for name, builder, kwargs in CASES:
            for base_pc in (0, 0x1234):
                with self.subTest(scene=name, base_pc=base_pc):
                    scene = builder(base_pc, dialogue=emit_dialogue, **kwargs)
                    script = install_scene(scene, base_pc)
                    decoded, errors = reachable_instructions(script, BASE, EXTENDED)
                    self.assertEqual(errors, [])
                    # Every emitted byte must be covered, including actor bodies.
                    covered = {offset for pc, ins in decoded.items()
                               for offset in range(pc, pc + ins.size)}
                    self.assertTrue(set(range(base_pc, len(script.bytecode))) <= covered)
                    slots = {(actor.entity, actor.script_index) for actor in scene.actor_routines}
                    self.assertEqual(len(slots), len(scene.actor_routines))
                    for instruction in decoded.values():
                        raw = instruction.raw
                        if instruction.opcode == 0x09:
                            self.assertIn((raw[1], raw[2] & 31), slots)
                        elif instruction.opcode in (0x01, 0x31):
                            target = struct.unpack_from("<H", raw, 1 if raw[0] == 1 else 3)[0]
                            self.assertIn(target, decoded)
                            self.assertGreaterEqual(target, base_pc)
                        if instruction.opcode == 0x31:
                            self.assertEqual(struct.unpack_from("<H", raw, 1)[0], 0x0020)
                        if instruction.opcode == 0x4B:
                            bound = struct.unpack_from("<H", raw, 6)[0]
                            self.assertTrue(bound & 0x8000)
                            self.assertGreater(bound & 0x7FFF, 0)
                            self.assertLessEqual(bound & 0x7FFF, 120)

    def test_actor_collision_is_restored_and_controls_remain_locked(self):
        for name, builder, kwargs in CASES:
            with self.subTest(scene=name):
                scene = builder(0, dialogue=emit_dialogue, **kwargs)
                routines = {(actor.entity, actor.script_index): actor.body
                            for actor in scene.actor_routines}
                flags, histories = {}, {}
                director = list(decode_linear(scene.body))
                for instruction in director:
                    if instruction.opcode != 0x09:
                        continue
                    entity, slot = instruction.raw[1], instruction.raw[2] & 31
                    for actor_instruction in decode_linear(routines[entity, slot]):
                        if actor_instruction.opcode == 0x20:
                            flags[entity] = struct.unpack_from("<H", actor_instruction.raw, 1)[0] & 0x7FFF
                            histories.setdefault(entity, []).append(flags[entity])
                self.assertTrue(flags)
                expected = {entity: 0 for entity in flags}
                if name == "bandage":
                    expected[kwargs["hammer_entity"]] = 0x0D
                self.assertEqual(flags, expected)
                for entity, history in histories.items():
                    self.assertIn(1, history)
                    self.assertEqual(history[-1], expected[entity])
                self.assertIn(0x54, [ins.extended_opcode for ins in director])
                self.assertNotIn(0x53, [ins.extended_opcode for ins in director])
                self.assertNotEqual(director[-1].opcode, 0)  # caller owns termination

    def test_bandage_retains_room_positions_camera_and_dialogue_timing(self):
        from modules.rico import chapter_two_opening as opening

        slices = []
        def dialogue(key, start=0, stop=None):
            slices.append((key, start, stop))
            return emit_dialogue(key, start, stop)

        scene = scenes.build_bandage(0, 1, 19, dialogue)
        routines = {(a.entity, a.script_index): a.body for a in scene.actor_routines}
        positions, waits = {}, []
        director = list(decode_linear(scene.body))
        for ins in director:
            if ins.opcode == 0x09:
                entity = ins.raw[1]
                for actor_ins in decode_linear(routines[entity, ins.raw[2] & 31]):
                    if actor_ins.opcode == 0x19:
                        positions[entity] = struct.unpack_from("<hh", actor_ins.raw, 1)
            elif ins.opcode == 0x26:
                waits.append(struct.unpack_from("<H", ins.raw, 1)[0] & 0x7FFF)
        self.assertEqual(positions, {1: opening.MAIN_RICO[:2], 19: opening.MAIN_HAMMER[:2]})
        self.assertEqual(slices, [("bandage", 0, 3), ("bandage", 3, 5), ("bandage", 5, None)])
        self.assertIn(24, waits)
        self.assertIn(30, waits)
        self.assertEqual(next(struct.unpack_from("<hhh", i.raw, 1) for i in director if i.opcode == 0x63),
                         opening.CONVERSATION_TARGET)
        self.assertEqual(next(struct.unpack_from("<hhh", i.raw, 1) for i in director if i.opcode == 0xA3),
                         opening.CONVERSATION_EYE)
        self.assertEqual(routines[19, 28], bytes.fromhex("20 0D 80 00"))

    def test_final_and_crash_actor_installations_coexist(self):
        finals = scenes.build_finals(0, 1, 2, emit_dialogue)
        crash = scenes.build_crash(0x1234, 1, emit_dialogue, fei_entity=2, witness_entity=3)
        self.assertFalse({(a.entity, a.script_index) for a in finals.actor_routines}
                         & {(a.entity, a.script_index) for a in crash.actor_routines})

    def test_mount_loads_correct_runtime_gears_before_actor_initialization(self):
        director = list(decode_linear(scenes.arena_director_prefix()))
        assignments = {struct.unpack_from("<H", ins.raw, 2)[0] & 0x7FFF:
                       struct.unpack_from("<H", ins.raw, 4)[0] & 0x7FFF
                       for ins in director if ins.extended_opcode == 0xA1}
        self.assertEqual(assignments, {5: 6, 0: 0})
        self.assertEqual([struct.unpack_from("<H", ins.raw, 2)[0] & 0x7FFF
                          for ins in director if ins.extended_opcode == 0x41], [0, 1])
        self.assertEqual((director[-1].extended_opcode, director[-1].raw[-1]), (0x1E, 0))
        for character in assignments:
            actor = list(decode_linear(scenes.arena_actor_init(character, (0, 0))))
            self.assertEqual(actor[0].opcode, 0x16)
            self.assertEqual(struct.unpack_from("<H", actor[0].raw, 1)[0] & 0x7FFF, character)
        unmount = list(decode_linear(scenes.unmount_before_travel()))
        self.assertEqual([ins.extended_opcode for ins in unmount], [0x42] * 3)
        self.assertEqual([struct.unpack_from("<H", ins.raw, 2)[0] & 0x7FFF
                          for ins in unmount], [0, 1, 2])

    def test_invalid_actor_and_missing_resource_contracts_reject(self):
        with self.assertRaises(ValueError):
            scenes.build_finals(0, 1, 1, emit_dialogue)
        with self.assertRaises(ValueError):
            scenes.arena_actor_init(3, (0, 0))
        with self.assertRaisesRegex(ValueError, "resource443 changed"):
            scenes.prepare_resources(lambda resource: b"")


class ChapterTwoSceneRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry = PROJECT_ROOT / "project.local.json"
        if not registry.is_file():
            raise unittest.SkipTest("Local source-disc registry is absent")
        sources = json.loads(registry.read_text(encoding="utf-8")).get("sources", {})
        path = Path(sources.get("retail_disc1", {}).get("path", "missing-retail-disc1.bin"))
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.is_file():
            raise unittest.SkipTest("Configured original retail Disc 1 is unavailable")
        cls.disc = DiscReader(path, 1)

    def test_complete_movement_paths_are_on_pinned_native_floors(self):
        segments = 0
        for name, builder, kwargs in CASES:
            with self.subTest(scene=name):
                scene = builder(0, dialogue=emit_dialogue, **kwargs)
                field = parse_field(self.disc.canonical(606 + 2 * scene.donor_field))
                report = scenes.validate_geometry(scene, field.parts[1].data)
                if name == "arrival_delivery":
                    self.assertEqual(report, {"paths": 0, "segments": 0})
                else:
                    self.assertGreater(report["segments"], 0)
                segments += report["segments"]
        self.assertEqual(segments, 14)

    def test_arrival_uses_native_bed_elevation_pose_and_bedside_camera(self):
        from modules.rico import chapter_two_resources as resources

        source = self.disc.canonical(606 + 2 * 213)
        field = parse_field(source)
        triangles, _ = resources._layer_zero_geometry(field.parts[1].data)
        resources.validate_room_geometry("intake", source)
        for (x, z, index), height in ((resources.ARRIVAL_PATIENT, -24),
                                      (resources.ARRIVAL_ATTENDANT, 0),
                                      (resources.ARRIVAL_GUARD, 0)):
            self.assertTrue(resources._inside((x, z), triangles[index]))
            self.assertEqual({vertex[1] for vertex in triangles[index]}, {height})
        code = AtelScript(field.parts[5].data).bytecode
        # The original field entry table has a seven-byte record per entry.
        self.assertEqual(code[0], 0xFF)
        for entry, landmark in ((3, resources.ARRIVAL_PATIENT),
                                (5, resources.ARRIVAL_ATTENDANT), (6, resources.ARRIVAL_GUARD)):
            self.assertEqual(struct.unpack_from("<hh", code, 1 + 7 * entry), landmark[:2])
        self.assertEqual(code[0x0FE5:0x0FED], b"\x63" + struct.pack("<hhh", *resources.ARRIVAL_CAMERA_TARGET) + b"\xE0")
        self.assertEqual(code[0x0FEE:0x0FF6], b"\xA3" + struct.pack("<hhh", *resources.ARRIVAL_CAMERA_EYE) + b"\xE0")
        native_pose = code[0x0376:0x037F]
        self.assertEqual(native_pose, bytes.fromhex("FE 4A 77 80 FE 4B FE 4D 00"))
        scene = scenes.build_arrival_delivery(0, fei_entity=33, doctor_entity=8,
                                              guard_entity=10, dialogue=emit_dialogue)
        for actor, landmark in ((33, resources.ARRIVAL_PATIENT),
                                (8, resources.ARRIVAL_ATTENDANT), (10, resources.ARRIVAL_GUARD)):
            routine = next(a for a in scene.actor_routines if (a.entity, a.script_index) == (actor, 24))
            self.assertIn(b"\x19" + struct.pack("<hh", *landmark[:2]) + b"\xC0\x1A\x00", routine.body)
            if actor == 33:
                self.assertIn(native_pose, routine.body)
                # Native entry direction6 and OP5F cardinal2 both yield0x800.
                self.assertEqual(code[7 + 7 * 3], 6)
                self.assertIn(b"\x5F\x02", routine.body)
        mesh = field.parts[1].data
        with self.assertRaisesRegex(ValueError, "exact field213 walkmesh"):
            scenes.validate_geometry(scene, mesh[:-1] + bytes([mesh[-1] ^ 1]))

    def test_bandage_whole_approach_and_withdrawal_stay_on_level_room_floor(self):
        from modules.rico import chapter_two_resources as resources
        from modules.rico import chapter_two_opening as opening

        field = parse_field(self.disc.canonical(606 + 2 * 218))
        triangles, _ = resources._layer_zero_geometry(field.parts[1].data)
        for point in [opening.MAIN_RICO[:2], opening.MAIN_SUZARN[:2],
                      *((55, z) for z in range(-251, -208))]:
            covered = [t for t in triangles if resources._inside(point, t)]
            self.assertTrue(covered, point)
            self.assertEqual({vertex[1] for t in covered for vertex in t}, {0}, point)

    def test_route_departure_and_changed_walkmesh_are_rejected(self):
        scene = scenes.build_finals(0, 1, 2, emit_dialogue)
        mesh = parse_field(self.disc.canonical(606 + 2 * 225)).parts[1].data
        bad_route = replace(scene, motion_paths=(scenes.MotionPath(((0, 0), (30000, 30000))),))
        with self.assertRaisesRegex(ValueError, "leaves the donor floor"):
            scenes.validate_geometry(bad_route, mesh)
        with self.assertRaisesRegex(ValueError, "exact field225 walkmesh"):
            scenes.validate_geometry(scene, mesh[:-1] + bytes([mesh[-1] ^ 1]))

    def test_all_cinematic_resource_pins_reject_same_length_corruption(self):
        resources = scenes.scene_resources(self.disc)
        self.assertEqual(set(resources), {443, 449, 2339, 2369, 2455})
        for resource, payload in resources.items():
            with self.subTest(resource=resource):
                changed = dict(resources)
                changed[resource] = payload[:-1] + bytes([payload[-1] ^ 1])
                with self.assertRaisesRegex(ValueError, f"resource{resource} changed"):
                    scenes.prepare_resources(changed.__getitem__)


if __name__ == "__main__":
    unittest.main()
