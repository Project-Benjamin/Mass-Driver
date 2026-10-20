"""Retain explicit historical scene/geometry regressions using real donors.

The preparation fixture selects interludes=False; these scenes are not the
default release. The direct launch test checks today's Rico-led entry, while
test_chapter_two_interludes covers the current narrated interlude policy.
"""
from pathlib import Path
import json
import struct
import unittest
from unittest.mock import patch

from modules.rico import build as core, chapter_two as world
from modules.rico import chapter_two_resources as resources, chapter_two_scenes as scenes
from modules.rico.tests.test_chapter_two_scenes import BASE as SCENE_BASE, EXTENDED as SCENE_EXTENDED
from shared.tools.xgatel import AtelScript as ParsedScript, OpcodeInfo, decode_instruction


# Native instruction widths supplement the independently checked choreography
# grammar. Operands are decoded below so embedded bytes cannot masquerade as
# locks, fades, transitions, or actor-update opcodes in these assertions.
BASE = dict(SCENE_BASE)
EXTENDED = dict(SCENE_EXTENDED)
for opcode, size in {0x0B: 3, 0x18: 5, 0x23: 1, 0x2A: 1, 0x35: 6, 0x3A: 6, 0x5B: 1, 0x75: 3,
                     0x98: 5, 0xA7: 1, 0xB4: 3, 0xBC: 1, 0xCB: 4, 0xF5: 4, 0xF8: 4}.items():
    BASE[opcode] = OpcodeInfo(opcode, f"OP_{opcode:02X}", size, (), opcode == 0x5B)
for opcode, size in {0x08: 8, 0x18: 3, 0x19: 3, 0x1A: 2, 0x3A: 4, 0x3B: 4, 0x5F: 9}.items():
    EXTENDED[opcode] = OpcodeInfo(opcode, f"OPX_{opcode:02X}", size - 1, (), False, True)


def word(raw, offset=1):
    return struct.unpack_from("<H", raw, offset)[0]


def trace(script, pc=0, flags=0, *, owner_hidden=False, initial_variables=None, trigger_inside=False):
    """Follow actual emitted control flow with released input and finite waits.

Variable operations and WAIT_DIALOG's hidden-owner abort are executed.
Rendering, actor calls and completed loads remain observable events, not
simulated gameplay. The abort models the native non-priority-7 action path
when a window is still open; a closed window can advance normally.
"""
    variables = {world.STATE: flags, world.LOCAL: flags}
    variables.update(initial_variables or {})
    dialogue_flags = 0
    executed = []
    for _ in range(3000):
        instruction = decode_instruction(script, pc, BASE, EXTENDED)
        executed.append(instruction)
        raw = instruction.raw
        pc += instruction.size
        if instruction.opcode in (0, 0x5B):
            return executed, variables
        if instruction.opcode in (0xD2, 0xF5):
            dialogue_flags = raw[3]
        elif instruction.opcode == 0x9C and owner_hidden and not dialogue_flags & 1:
            # Native WAIT_DIALOG calls OP_STOP for a hidden talking owner
            # unless the active window's control flags include bit 0.
            return executed, variables
        if instruction.opcode == 1:
            pc = word(raw)
        elif instruction.opcode == 2:
            left, right, mode = variables.get(word(raw), 0), word(raw, 3), raw[5]
            if mode == 0x46:
                jump = not left & right
            elif mode == 0x40:
                jump = left != right
            elif mode == 0x41:
                jump = left == right
            else:
                raise AssertionError(f"Unreviewed branch comparison {mode:#x}")
            if jump:
                pc = word(raw, 6)
        elif instruction.opcode == 0x31:
            pc = word(raw, 3)  # Released Cross takes the native loop exit.
        elif instruction.opcode == 0xCB and not trigger_inside:
            pc = word(raw, 2)
        elif instruction.opcode == 0x35:
            variables[word(raw)] = word(raw, 3) if raw[5] & 0x40 else variables.get(word(raw, 3), 0)
        elif instruction.opcode == 0x3A:
            if raw[5] != 0x40:
                raise AssertionError("Unreviewed variable-driven bit write")
            variables[word(raw)] = variables.get(word(raw), 0) | (1 << word(raw, 3))
    raise AssertionError("Opening control flow did not terminate")


def raw_script(body):
    return ParsedScript(bytes(0x84) + body)


def dialogue_ids(name):
    first = 0
    for key, blocks in world.load_dialogue().items():
        if key == name:
            return set(range(first, first + len(blocks)))
        first += len(blocks)
    raise AssertionError(f"Missing authored scene {name}")


class ChapterTwoIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = core.ROOT / "project.local.json"
        if not config.is_file():
            raise unittest.SkipTest("Configure the retail donor for complete preparation tests")
        source = Path(json.loads(config.read_text())["sources"]["retail_disc1"]["path"])
        if not source.is_file():
            raise unittest.SkipTest("Configured retail donor is unavailable")
        cls.reader = core.DiscReader(source, 1)
        expand = world.expand_replacements
        with patch.object(world, "expand_replacements", side_effect=lambda *args, **kwargs:
                          expand(*args, **{**kwargs, "interludes": False})):
            cls.prepared = core.prepare_replacements(cls.reader, core.load_chapters())

    def field(self, disc, field):
        data = next(item.data for item in self.prepared[disc] if item.canonical_id == 606 + 2 * field)
        parsed = core.parse_field(data)
        return parsed, core.AtelScript(parsed.parts[5].data)

    def routine(self, disc, field, entity, slot, flags=0, **kwargs):
        _, script = self.field(disc, field)
        return trace(ParsedScript(script.to_bytes()), script.get_script_pointer(entity, slot), flags, **kwargs)

    def assert_black_before_party_changes(self, instructions):
        locked = False
        black = False
        pending_black_frames = None
        party_changes = 0
        for instruction in instructions:
            if instruction.extended_opcode == 0x54:
                locked = True
            elif instruction.extended_opcode == 0x53:
                locked = False
            elif instruction.opcode == 0xB4:
                pending_black_frames = word(instruction.raw) & 0x7FFF
                black = pending_black_frames == 0
            elif instruction.opcode == 0xF1:
                mode, red, green, blue, duration = struct.unpack_from("<5H", instruction.raw, 1)
                if (mode & 0x7FFF) == 2 and all((value & 0x7FFF) == 255 for value in (red, green, blue)):
                    pending_black_frames = duration & 0x7FFF
                    black = pending_black_frames == 0
            elif instruction.opcode == 0x26 and pending_black_frames is not None:
                pending_black_frames -= word(instruction.raw) & 0x7FFF
                black = pending_black_frames <= 0
            if instruction.extended_opcode in (0x18, 0x19, 0x1A):
                party_changes += 1
                self.assertTrue(locked, f"Party changed without a control lock at {instruction.pc:#x}")
                self.assertTrue(black, f"Party changed before the black fade completed at {instruction.pc:#x}")
            if instruction.opcode == 0x98:
                self.assertTrue(locked, "Field transition unexpectedly unlocks the departing scene")
                self.assertTrue(black, "Field transition starts before the black fade completes")
        self.assertGreater(party_changes, 0, "Tested transition does not actually reload a party")

    def test_current_chapter_two_launch_enters_rico_room_without_intake_on_both_discs(self):
        for disc in (1, 2):
            with self.subTest(disc=disc):
                instructions, _ = trace(raw_script(core._chapter_launch_body(2, core.CHAPTER_FIELDS[disc][2])))
                self.assert_black_before_party_changes(instructions)
                targets = [word(ins.raw) & 0x7FFF for ins in instructions if ins.opcode == 0x98]
                self.assertEqual(targets, [core.CHAPTER_FIELDS[disc][2]])
                self.assertNotIn(resources.WORLD_FIELDS["intake"], targets)
                self.assertEqual([ins.raw[2] for ins in instructions if ins.extended_opcode == 0x18], [5])

    def test_every_campaign_travel_blacks_and_locks_before_party_reload(self):
        for disc in (1, 2):
            fields = {**resources.WORLD_FIELDS, "main": core.CHAPTER_FIELDS[disc][2],
                      "bedroom": core.CHAPTER_TWO_BEDROOM_FIELD}
            for room in fields:
                with self.subTest(disc=disc, room=room):
                    instructions, _ = trace(raw_script(world.travel(room, fields)))
                    self.assert_black_before_party_changes(instructions)
                    self.assertEqual([word(ins.raw) & 0x7FFF for ins in instructions if ins.opcode == 0x98], [fields[room]])

    def test_real_stair_trigger_exits_without_cross_only_after_intro_and_report(self):
        ready = sum(1 << world.BITS[flag] for flag in ("room_intro", "hammer", "delivery"))
        for disc in (1, 2):
            field = core.CHAPTER_FIELDS[disc][2]
            parsed, _ = self.field(disc, field)
            native = core.parse_field(self.reader.canonical(606 + 2 * 218))
            self.assertEqual(parsed.parts[8].data, native.parts[8].data)
            for flags, inside in ((0, True), (1 << world.BITS['room_intro'], True),
                                  (ready, False), (ready, True)):
                with self.subTest(disc=disc, flags=flags, inside=inside):
                    commands, variables = self.routine(disc, field, 3, 1, flags, trigger_inside=inside)
                    destinations = [word(ins.raw) & 0x7FFF for ins in commands if ins.opcode == 0x98]
                    self.assertEqual(destinations, [resources.WORLD_FIELDS['bar']]
                                     if flags == ready and inside else [])
                    if destinations:
                        self.assert_black_before_party_changes(commands)
                        self.assertNotIn(0x31, [ins.opcode for ins in commands],
                                         'Walk-through exit must not wait for Cross')
                        self.assertEqual(variables[world.STATE], ready)

    def test_main_npc_init_and_hotspots_use_passable_parking_clear_of_stairs(self):
        from modules.rico import chapter_two_opening as opening
        for disc in (1, 2):
            field = core.CHAPTER_FIELDS[disc][2]
            for entity, position in ((4, opening.MAIN_SUZARN), (19, opening.MAIN_HAMMER)):
                commands, _ = self.routine(disc, field, entity, 0)
                self.assertEqual([struct.unpack_from('<hh', ins.raw, 1) for ins in commands if ins.opcode == 0x19],
                                 [position[:2]])
                self.assertIn(b'\x20\x0D\x80', [ins.raw for ins in commands])
            _, script = self.field(disc, field)
            for offset, action in enumerate(world.actions_for('main')):
                if action.landmark not in ('hammer', 'suzarn', 'exit'):
                    continue
                entity = script.entity_count - len(world.actions_for('main')) + offset
                commands, _ = self.routine(disc, field, entity, 0)
                positions = [struct.unpack_from('<hh', ins.raw, 1) for ins in commands if ins.opcode == 0x19]
                expected = {'hammer': opening.MAIN_HAMMER, 'suzarn': opening.MAIN_SUZARN,
                            'exit': opening.HAMMER_ENTRANCE}[action.landmark]
                self.assertEqual(positions, [expected[:2]])

    def test_return_from_bar_and_bedroom_cannot_spawn_inside_stair_exit(self):
        flags = sum(1 << world.BITS[flag] for flag in ('delivery', 'room_intro', 'hammer'))
        for disc in (1, 2):
            room = resources.WORLD_FIELDS['bar']
            commands, _ = self.routine(disc, room, 3, 1, flags, trigger_inside=True)
            self.assertEqual([(word(ins.raw) & 0x7FFF, word(ins.raw, 3) & 0x7FFF)
                              for ins in commands if ins.opcode == 0x98], [(core.CHAPTER_FIELDS[disc][2], 1)])
            field, _ = self.field(disc, core.CHAPTER_FIELDS[disc][2])
            trigger = struct.unpack('<12h', field.parts[8].data)
            xs, zs = trigger[0::3], trigger[2::3]
            for index, expected in ((0, core.CHAPTER_TWO_MAIN_PLAYABLE_ENTRY),
                                    (2, core.CHAPTER_TWO_MAIN_RETURN_ENTRY)):
                entry = core.mass_driver._read_field_entry(field.parts[5].data, index)
                self.assertEqual(entry, expected)
                self.assertFalse(min(xs) <= entry.x <= max(xs) and min(zs) <= entry.z <= max(zs))
            arrival = core.mass_driver._read_field_entry(field.parts[5].data, 1)
            self.assertEqual((arrival.x, arrival.z), (73, -54))
            self.assertFalse(min(xs) <= arrival.x <= max(xs) and min(zs) <= arrival.z <= max(zs))
            entered, _ = self.routine(disc, core.CHAPTER_FIELDS[disc][2], 0, 1, flags)
            self.assertFalse(any(ins.opcode in (0x98, 0xF5) for ins in entered))
            outside, _ = self.routine(disc, core.CHAPTER_FIELDS[disc][2], 3, 1, flags, trigger_inside=False)
            self.assertFalse(any(ins.opcode == 0x98 for ins in outside))

    def test_gramps_preserves_native_tint_scale_and_authored_location(self):
        for disc in (1, 2):
            commands, _ = self.routine(disc, resources.WORLD_FIELDS['sewer_hub'], 42, 0)
            raw = [ins.raw for ins in commands]
            self.assertEqual(raw[:3], [b'\x0B\x00\x80', bytes.fromhex('FE5F031E8064801E80'),
                                      bytes.fromhex('FE08889300880090')])
            self.assertIn(b'\x20\x0C\x80', raw)
            self.assertEqual([struct.unpack_from('<hh', ins.raw, 1) for ins in commands if ins.opcode == 0x19],
                             [(-40, 180)])

    def test_commons_uses_receptionist_actor_and_paired_graphics(self):
        from modules.rico import chapter_two_clerk as clerk
        import hashlib
        source_actors = core.mass_driver._indexed_bundle_entries(
            core.parse_field(self.reader.canonical(1028)).parts[3].data)
        expected_graphics = clerk.install_commons_clerk_graphics(
            self.reader.canonical(1029), self.reader.canonical(1049))
        for disc in (1, 2):
            parsed, _ = self.field(disc, resources.WORLD_FIELDS['commons'])
            actors = core.mass_driver._indexed_bundle_entries(parsed.parts[3].data)
            self.assertEqual((len(actors[2]), hashlib.sha256(actors[2]).hexdigest()),
                             clerk.RECEPTIONIST_ACTOR_IDENTITY)
            self.assertEqual([actor for i, actor in enumerate(actors) if i != 2],
                             [actor for i, actor in enumerate(source_actors) if i != 2])
            graphics = next(item.data for item in self.prepared[disc] if item.canonical_id == 745)
            self.assertEqual(graphics, expected_graphics)
            init, _ = self.routine(disc, resources.WORLD_FIELDS['commons'], clerk.CLERK_ENTITY, 0)
            self.assertEqual([ins.raw for ins in init if ins.opcode == 0x0B], [b'\x0B\x02\x80'])

    def test_prepared_intake_locks_before_waits_and_fei_has_no_player_update(self):
        for disc in (1, 2):
            field = resources.WORLD_FIELDS["intake"]
            _, script = self.field(disc, field)
            for slot in (0, 1):
                with self.subTest(disc=disc, director_slot=slot):
                    instructions, _ = self.routine(disc, field, 0, slot)
                    lock = next(index for index, ins in enumerate(instructions) if ins.extended_opcode == 0x54)
                    waits = [index for index, ins in enumerate(instructions)
                             if ins.opcode == 0x26 or ins.extended_opcode == 0x1A]
                    self.assertTrue(waits)
                    self.assertLess(lock, min(waits))
            actors = core._registered_character_entities(script)
            self.assertIn(0, actors, "The prepared intake must register Fei")
            instructions, _ = self.routine(disc, field, actors[0], 1)
            self.assertNotIn(0xA7, [ins.opcode for ins in instructions])
            self.assertNotIn(0x4B, [ins.opcode for ins in instructions])

    def test_prepared_intake_delivery_is_once_only_and_never_unlocks_before_main(self):
        delivery = 1 << world.BITS["delivery"]
        for disc in (1, 2):
            for initial_flags in (0, delivery):
                with self.subTest(disc=disc, completed=bool(initial_flags)):
                    instructions, variables = self.routine(disc, resources.WORLD_FIELDS["intake"], 0, 1, initial_flags)
                    self.assertNotIn(0x53, [ins.extended_opcode for ins in instructions])
                    self.assertEqual([word(ins.raw) & 0x7FFF for ins in instructions if ins.opcode == 0x98], [core.CHAPTER_FIELDS[disc][2]])
                    shown = {word(ins.raw) for ins in instructions if ins.opcode in (0xD2, 0xF5)}
                    if initial_flags:
                        self.assertEqual(shown, set(), "Completed intake replayed dialogue")
                    else:
                        self.assertTrue(dialogue_ids("arrival_delivery") <= shown)
                        self.assertIn(0x09, [ins.opcode for ins in instructions], "Arrival has no performed actor choreography")
                        commit = next(index for index, ins in enumerate(instructions)
                                      if ins.opcode == 0x3A and word(ins.raw) == world.STATE
                                      and word(ins.raw, 3) == world.BITS["delivery"])
                        transition = next(index for index, ins in enumerate(instructions) if ins.opcode == 0x98)
                        self.assertLess(commit, transition)
                    self.assertTrue(variables[world.STATE] & delivery)

    def test_prepared_main_introduction_preserves_old_saves_without_bouncing_to_intake(self):
        delivered = 1 << world.BITS["delivery"]
        introduced = 1 << world.BITS["room_intro"]
        for disc in (1, 2):
            for flags in (0, delivered, introduced, delivered | introduced):
                with self.subTest(disc=disc, flags=flags):
                    instructions, variables = self.routine(disc, core.CHAPTER_FIELDS[disc][2], 0, 1, flags)
                    self.assertEqual([ins for ins in instructions if ins.opcode == 0x98], [])
                    shown = {word(ins.raw) for ins in instructions if ins.opcode in (0xD2, 0xF5)}
                    self.assertFalse(shown & dialogue_ids("arrival_delivery"))
                    if not flags & introduced:
                        self.assertTrue(dialogue_ids("room_first") <= shown)
                        self.assertEqual(variables[world.STATE] & (delivered | introduced), delivered | introduced)
                    else:
                        self.assertEqual(shown, set(), "Completed sitting-room intro replayed")

    def test_suzarn_remains_visible_after_the_complete_three_actor_introduction(self):
        delivered = 1 << world.BITS["delivery"]
        introduced = 1 << world.BITS["room_intro"]
        for disc in (1, 2):
            with self.subTest(disc=disc):
                field = core.CHAPTER_FIELDS[disc][2]
                init, _ = self.routine(disc, field, 4, 0, delivered)
                self.assertEqual([(ins.opcode, word(ins.raw) & 0x7FFF)
                                  for ins in init if ins.opcode == 0x0B], [(0x0B, 0)],
                                 "Suzarn must initialize retail field 218's native bank 0")
                self.assertNotIn(0x23, [ins.opcode for ins in init])
                instructions, variables = self.routine(
                    disc, field, 0, 1, delivered, owner_hidden=True)
                shows = [index for index, ins in enumerate(instructions)
                         if ins.opcode == 0x24 and ins.raw[1] == 4]
                hides = [index for index, ins in enumerate(instructions)
                         if ins.opcode == 0x25 and ins.raw[1] == 4]
                spoken = [(index, ins) for index, ins in enumerate(instructions)
                          if ins.opcode == 0xF5 and word(ins.raw) in dialogue_ids("room_first")]
                self.assertEqual(len(shows), 1)
                self.assertEqual(hides, [])
                self.assertEqual({word(ins.raw) for _, ins in spoken}, dialogue_ids("room_first"))
                for index, ins in spoken:
                    self.assertLess(shows[0], index)
                    self.assertTrue(ins.raw[3] & 1)
                    self.assertEqual(instructions[index + 1].opcode, 0x9C)
                self.assertEqual(variables[world.STATE] & (delivered | introduced), delivered | introduced)
                self.assertTrue(variables[world.STATE] & (1 << world.BITS["hammer"]))
                shown = {word(ins.raw) for ins in instructions if ins.opcode == 0xF5}
                self.assertTrue(dialogue_ids("hammer_report") <= shown)
                self.assertIn(0x53, [ins.extended_opcode for ins in instructions])
                revisited, _ = self.routine(disc, field, 4, 0, delivered | introduced)
                self.assertIn(0x0B, [ins.opcode for ins in revisited],
                              "Suzarn remains available for conversations on return visits")
                self.assertNotIn(0x23, [ins.opcode for ins in revisited])

    def test_hammer_report_commits_and_unlocks_from_visible_actor_and_hidden_hotspot(self):
        initial = (1 << world.BITS["delivery"]) | (1 << world.BITS["room_intro"])
        arrived = {core.CHAPTER_TWO_HAMMER_STATE_VARIABLE:
                   1 << core.CHAPTER_TWO_HAMMER_ARRIVED_BIT}
        heard = 1 << world.BITS["hammer"]
        for disc in (1, 2):
            field = core.CHAPTER_FIELDS[disc][2]
            _, script = self.field(disc, field)
            hotspot = script.entity_count - len(world.actions_for("main"))
            for entity, hidden in ((hotspot, True), (core.CHAPTER_TWO_HAMMER_ENTITY, False)):
                with self.subTest(disc=disc, entity=entity, owner_hidden=hidden):
                    instructions, variables = self.routine(
                        disc, field, entity, 2, initial,
                        owner_hidden=hidden, initial_variables=arrived)
                    shown = {word(ins.raw) for ins in instructions if ins.opcode == 0xF5}
                    self.assertEqual(shown, dialogue_ids("hammer_report"))
                    self.assertTrue(variables[world.STATE] & heard)
                    self.assertEqual(variables[world.LOCAL], variables[world.STATE])
                    self.assertIn(0x53, [ins.extended_opcode for ins in instructions])
                    stairs, _ = self.routine(
                        disc, field, script.entity_count - 1, 2,
                        variables[world.STATE], owner_hidden=True)
                    self.assertEqual([word(ins.raw) & 0x7FFF for ins in stairs if ins.opcode == 0x98],
                                     [resources.WORLD_FIELDS["bar"]])
                    if hidden:
                        # Prove this assertion models the reported failure:
                        # restoring the old flag closes/stops at the first
                        # WAIT_DIALOG, before the milestone or FE53 unlock.
                        old = bytearray(script.bytecode)
                        for ins in instructions:
                            if ins.opcode == 0xF5:
                                old[ins.pc + 3] = 0
                        stopped, old_variables = trace(
                            raw_script(bytes(old)), script.get_script_pointer(entity, 2), initial,
                            owner_hidden=True, initial_variables=arrived)
                        self.assertFalse(old_variables[world.STATE] & heard)
                        self.assertNotIn(0x53, [ins.extended_opcode for ins in stopped])
                        self.assertEqual(stopped[-1].opcode, 0x9C)

    def test_every_opening_actor_call_resolves_to_its_own_bounded_routine(self):
        from modules.rico import chapter_two_opening as opening
        for disc in (1, 2):
            for field in (resources.WORLD_FIELDS["intake"], core.CHAPTER_FIELDS[disc][2]):
                _, script = self.field(disc, field)
                instructions, _ = self.routine(disc, field, 0, 1, owner_hidden=True)
                calls = [ins for ins in instructions if ins.opcode == 0x09]
                self.assertTrue(calls)
                for call in calls:
                    entity, slot = call.raw[1], call.raw[2] & 0x1F
                    self.assertLess(entity, script.entity_count)
                    called, _ = self.routine(disc, field, entity, slot)
                    self.assertEqual(called[-1].opcode, 0)
                    self.assertNotIn(0xA7, [ins.opcode for ins in called])
                    self.assertNotIn(0x53, [ins.extended_opcode for ins in called])
                    if field == core.CHAPTER_FIELDS[disc][2]:
                        self.assertIn(slot, range(opening.FIRST_SCRIPT, opening.FIRST_SCRIPT + 5))
                if field == core.CHAPTER_FIELDS[disc][2]:
                    idle, _ = self.routine(disc, field, core.CHAPTER_TWO_HAMMER_ENTITY, 1)
                    self.assertEqual([ins.opcode for ins in idle], [0x5B])

    def test_suzarn_followup_reflects_progress_without_awarding_flags(self):
        base = sum(1 << world.BITS[key] for key in ("delivery", "room_intro", "hammer"))
        cases = [((), "room_suzarn_before"), (("baptism",), "room_suzarn_after_baptism"),
                 (("baptism", "murders", "redrum"), None),
                 (("baptism", "murders", "redrum", "finals"), None)]
        for disc in (1, 2):
            for flags, name in cases:
                state = base | sum(1 << world.BITS[key] for key in flags)
                instructions, variables = self.routine(disc, core.CHAPTER_FIELDS[disc][2], 4, 2, state)
                shown = {word(ins.raw) for ins in instructions if ins.opcode == 0xF5}
                self.assertEqual(shown, dialogue_ids(name) if name else set())
                self.assertEqual(variables[world.STATE], state)
                self.assertIn(0x53, [ins.extended_opcode for ins in instructions])
                init, _ = self.routine(disc, core.CHAPTER_FIELDS[disc][2], 4, 0, state)
                self.assertEqual(0x0B in [ins.opcode for ins in init], name is not None)

    def test_real_preparation_installs_twelve_rooms_and_eight_pinned_dependencies(self):
        pins = {**resources.REDRUM_RESOURCE_IDENTITIES, **scenes.CINEMATIC_RESOURCE_IDENTITIES}
        for disc in (1, 2):
            ids = [item.canonical_id for item in self.prepared[disc]]
            self.assertEqual(len(ids), len(set(ids)))
            for field in (*resources.WORLD_FIELDS.values(), core.CHAPTER_FIELDS[disc][2], core.CHAPTER_TWO_BEDROOM_FIELD):
                self.assertIn(606 + 2 * field, ids)
                self.assertIn(607 + 2 * field, ids)
            for resource, pin in pins.items():
                data = next(item.data for item in self.prepared[disc] if item.canonical_id == resource)
                self.assertEqual((len(data), core._sha256_bytes(data)), pin)
            _, exit_script = self.field(disc, resources.WORLD_FIELDS["central"])
            self.assertIn(core._chapter_launch_body(3, core.CHAPTER_FIELDS[disc][3]), exit_script.bytecode)
            self.assertIn(core._hub_launch_body(core.HUB_FIELDS[disc]), exit_script.bytecode)

    def test_actual_boss_and_title_defense_have_no_random_encounters(self):
        for disc in (1, 2):
            for role in resources.WORLD_FIELDS:
                parsed, _ = self.field(disc, resources.WORLD_FIELDS[role])
                self.assertEqual(parsed.parts[6].data[512:], bytes(16))
            parsed, script = self.field(disc, resources.WORLD_FIELDS["sewer_drain"])
            self.assertEqual(parsed.parts[6].data[15 * 32:16 * 32], resources.REDRUM_FORMATION)
            self.assertIn(core.mass_driver._fixed_battle(15) + b"\xFE\x7F", script.bytecode)
            parsed, script = self.field(disc, resources.WORLD_FIELDS["prep"])
            self.assertTrue(parsed.parts[6].data[6 * 32 + 1] & 0x80)
            self.assertIn(core.mass_driver._fixed_battle(6) + b"\xFE\x7F", script.bytecode)
            banks = core.mass_driver._indexed_bundle_entries(parsed.parts[3].data)
            self.assertEqual(core._sha256_bytes(banks[0]), core.CHAPTER_TWO_HAMMER_ACTOR_BANK_SHA256)

    def test_native_doors_and_audited_static_geometry_remain_reachable(self):
        for disc in (1, 2):
            _, main = self.field(disc, core.CHAPTER_FIELDS[disc][2])
            pc = main.get_script_pointer(2, 2)
            expected = core._chapter_two_main_bedroom_action(core.CHAPTER_TWO_BEDROOM_FIELD)
            self.assertEqual(main.bytecode[pc:pc + len(expected)], expected)
            _, bed = self.field(disc, core.CHAPTER_TWO_BEDROOM_FIELD)
            pc = bed.get_script_pointer(2, 2)
            expected = core._chapter_two_bedroom_return_action(core.CHAPTER_FIELDS[disc][2])
            self.assertEqual(bed.bytecode[pc:pc + len(expected)], expected)
            for role, spec in resources.ROOM_SPECS.items():
                parsed, script = self.field(disc, resources.WORLD_FIELDS[role])
                for entity in spec["safe_static_models"]:
                    pc = script.get_script_pointer(entity, 0)
                    self.assertEqual(script.bytecode[pc:pc + 3], b"\xBC\x2A\x00")
                self.assertLess(script.bytecode_size, 0x10000)
                self.assertEqual(parsed.parts[1].data,
                    core.parse_field(self.reader.canonical(606 + 2 * spec["donor"])).parts[1].data)


if __name__ == "__main__":
    unittest.main()
