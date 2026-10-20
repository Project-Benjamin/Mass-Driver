"""Current private intervals: deliberate skips, native routes and bounded state."""
import json
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from modules.rico import build as core, chapter_two as world
from modules.rico import chapter_two_interludes as policy
from modules.rico import chapter_two_resources as resources
from modules.rico.tests import test_chapter_two_integration as native
from modules.rico.dialogue_portraits import _decode, present_field, opcode_metadata
from modules.rico.release_presentation import speaker_portraits
from shared.tools.xgdialog import parse_dialogue


KEYS = (*policy.STAGE_KEYS, "gap_intro", *(f"gap_skip_{i:02d}" for i in range(1, 7)), "gap_outro", "gap_repeat_03_hammer",
        *(f"gap_optional_{name}" for name in ("hammer", "suzarn", "schedule", "bed", "worker", "battler", "prisoner", "clerk")))
IDS = {key: index for index, key in enumerate(KEYS)}
FIELDS = {**resources.WORLD_FIELDS, "main": core.CHAPTER_FIELDS[1][2],
          "bedroom": core.CHAPTER_TWO_BEDROOM_FIELD}
ACTORS = {"rico": 28, "suzarn": 4, "hammer": 19}


def dialogue(key, start=0, stop=None):
    return b"\xFE\x0D\xFC\x80" + core._dialogue_sequence((IDS[key],), flags=1)


def windows(commands):
    return [native.word(ins.raw) for ins in commands if ins.opcode in (0xD2, 0xF5)]


def execute(body, flags=0, **kwargs):
    base, _ = opcode_metadata()
    with patch.dict(native.BASE, {0xA9: base[0xA9]}):
        return native.trace(native.raw_script(body), flags=flags, **kwargs)


def execute_at(editor, entity, slot, flags=0, **kwargs):
    base, extended = opcode_metadata()
    with patch.dict(native.BASE, base), patch.dict(native.EXTENDED, extended):
        return native.trace(native.ParsedScript(editor.to_bytes()),
                            editor.get_script_pointer(entity, slot), flags, **kwargs)


class DepartureChecks:
    def assert_departure_preserves_live_party(self, commands, target, entry):
        """Check decoded control flow, without simulating native loading or actors."""
        transitions = [(index, ins) for index, ins in enumerate(commands) if ins.opcode == 0x98]
        self.assertEqual(len(transitions), 1)
        transition_index, transition = transitions[0]
        self.assertEqual((native.word(transition.raw) & 0x7FFF,
                          native.word(transition.raw, 3) & 0x7FFF), (target, entry))
        departure = commands[:transition_index]
        self.assertFalse(any(ins.extended_opcode in (0x18, 0x19, 0x1A) for ins in departure),
                         "Departure must not remove, reload, or wait for the live party")
        self.assertFalse(any(ins.opcode == 0x05 for ins in departure),
                         "The path tracer does not execute subroutine calls")
        self.assertTrue(any(ins.extended_opcode == 0x54 for ins in departure))
        self.assertFalse(any(ins.extended_opcode == 0x53 for ins in departure))
        fade_index = max(index for index, ins in enumerate(departure) if ins.opcode == 0xB4)
        fade_frames = native.word(departure[fade_index].raw) & 0x7FFF
        self.assertGreater(fade_frames, 0)
        waited = sum(native.word(ins.raw) & 0x7FFF for ins in departure[fade_index + 1:]
                     if ins.opcode == 0x26)
        self.assertGreaterEqual(waited, fade_frames, "Field load must follow the completed fade wait")
        self.assertEqual(commands[transition_index + 1].opcode, 0x5B)
        self.assertEqual(transition_index + 2, len(commands))


class InterludePolicyTests(DepartureChecks, unittest.TestCase):
    def automatic(self, state):
        actors = []
        body = policy._automatic_body("main", base_pc=0, fields=FIELDS,
                                     dialogue=dialogue, actors=ACTORS, editor=actors)
        return execute(body, state), actors

    def continue_action(self, stage, selection, *, seen=True, room="main"):
        action = next(a for a in policy.actions_for(room) if a.steps[0].complete)
        body = policy._action_body(action, base_pc=0, room=room, fields=FIELDS,
            dialogue=dialogue, actors=ACTORS, editor=[], return_hub=core.HUB_FIELDS[1],
            next_ids=(999,), choice_id=99)
        return execute(body, policy.state_for(stage, seen=seen),
                       initial_variables={core.MENU_SELECTION_VARIABLE: selection})

    def test_every_period_plays_once_and_revisit_always_releases_black_and_input(self):
        for stage in range(1, 7):
            before = 0 if stage == 1 else policy.state_for(stage, seen=False)
            (first, state), routines = self.automatic(before)
            expected = ([IDS["gap_intro"]] if stage == 1 else []) + [IDS[policy.STAGE_KEYS[stage - 1]]]
            self.assertEqual(windows(first), expected)
            self.assertEqual(state[policy.STATE], policy.state_for(stage))
            self.assertEqual(state[policy.LOCAL], state[policy.STATE])
            (again, after), _ = self.automatic(state[policy.STATE])
            self.assertFalse(windows(again))
            self.assertEqual(after, state)
            for commands in (first, again):
                self.assertTrue(any(ins.extended_opcode == 0x53 for ins in commands))
                fades = [struct.unpack_from("<5H", ins.raw, 1) for ins in commands if ins.opcode == 0xF1]
                self.assertTrue(any(tuple(value & 0x7FFF for value in fade[1:4]) == (0, 0, 0) for fade in fades))
                self.assertEqual(commands[-1].opcode, 0x5B)
            pairs = [(routine.entity, routine.script_index) for routine in routines]
            self.assertEqual(len(pairs), len(set(pairs)), "Scenes overwrite incompatible actor scripts")

    def test_continue_narrates_before_advancing_and_next_visit_plays_only_next_period(self):
        for stage in range(1, 6):
            commands, state = self.continue_action(stage, 1)
            self.assertEqual(windows(commands), [IDS["gap_optional_schedule"], 99, IDS[f"gap_skip_{stage:02d}"]])
            self.assertEqual(state[policy.STATE], policy.state_for(stage + 1, seen=False))
            narration = next(i for i, ins in enumerate(commands) if ins.opcode == 0xF5 and native.word(ins.raw) == IDS[f"gap_skip_{stage:02d}"])
            write = next(i for i, ins in enumerate(commands) if ins.opcode == 0x3A)
            self.assertLess(narration, write)
            self.assertEqual([native.word(ins.raw) & 0x7FFF for ins in commands if ins.opcode == 0x98], [FIELDS["main"]])
            (next_scene, _), _ = self.automatic(state[policy.STATE])
            self.assertEqual(windows(next_scene), [IDS[policy.STAGE_KEYS[stage]]])

    def test_stay_and_unseen_period_do_not_advance_time_or_travel(self):
        for stage in range(1, 7):
            for seen, selection in ((True, 2), (False, 1)):
                commands, state = self.continue_action(stage, selection, seen=seen)
                self.assertEqual(state[policy.STATE], policy.state_for(stage, seen=seen))
                self.assertFalse(any(ins.opcode in (0x3A, 0x98) for ins in commands))
                self.assertTrue(any(ins.extended_opcode == 0x53 for ins in commands))
                self.assertEqual(commands[-1].opcode, 0)

    def test_last_continue_returns_only_to_hub_after_campaign_handoff_narration(self):
        commands, state = self.continue_action(6, 1, room="bedroom")
        self.assertEqual(windows(commands), [IDS["gap_optional_bed"], 99, IDS["gap_skip_06"], IDS["gap_outro"]])
        destinations = [native.word(ins.raw) & 0x7FFF for ins in commands if ins.opcode == 0x98]
        self.assertEqual(destinations, [core.HUB_FIELDS[1]])
        self.assertNotIn(core.CHAPTER_FIELDS[1][3], destinations)
        self.assertEqual(state[policy.STATE], 0)

    def test_optional_talks_do_not_mutate_time_inventory_or_canon_flags(self):
        for room in policy.ACTIVE_ROOMS:
            for action in policy.actions_for(room):
                if action.steps[0].target or action.steps[0].complete:
                    continue
                body = policy._action_body(action, base_pc=0, room=room, fields=FIELDS,
                    dialogue=dialogue, actors=ACTORS, editor=[], return_hub=core.HUB_FIELDS[1],
                    next_ids=(), choice_id=99)
                commands, after = execute(body, policy.state_for(3))
                self.assertEqual(after, {policy.STATE: policy.state_for(3), policy.LOCAL: policy.state_for(3)})
                self.assertFalse(any(ins.opcode in (0x35, 0x3A, 0x3B, 0x98) for ins in commands))
                self.assertFalse(any(ins.extended_opcode in (0x84, 0xA1, 0x41, 0x1E) for ins in commands))

    def test_private_cast_disappears_at_boundaries_and_scene_four_onward_is_solo(self):
        for name, final_visible in (("suzarn", 2), ("hammer", 3)):
            body = policy.gated_init(0, name, b"\x0B\x00\x80\x00")
            for stage in range(1, 7):
                commands, _ = execute(body, policy.state_for(stage))
                self.assertEqual(any(ins.opcode == 0x0B for ins in commands), stage <= final_visible)
        for stage in range(4, 7):
            built = policy.build_private_scene(0, stage, actors=ACTORS, dialogue=dialogue)
            self.assertEqual({routine.entity for routine in built.actor_routines}, {ACTORS["rico"]})
            commands, _ = execute(built.body + b"\x00")
            self.assertEqual([ins.raw[1] for ins in commands if ins.opcode == 0x24], [ACTORS["rico"]])

    def test_hammer_repeat_acknowledges_private_grief_in_third_interval(self):
        action = next(action for action in policy.actions_for("main") if action.landmark == "hammer")
        body = policy._action_body(action, base_pc=0, room="main", fields=FIELDS,
            dialogue=dialogue, actors=ACTORS, editor=[], return_hub=core.HUB_FIELDS[1],
            next_ids=(), choice_id=99)
        for stage in (1, 2, 3):
            commands, state = execute(body, policy.state_for(stage))
            key = "gap_repeat_03_hammer" if stage == 3 else "gap_optional_hammer"
            self.assertEqual(windows(commands), [IDS[key]])
            self.assertEqual(state[policy.STATE], policy.state_for(stage))

    def test_stairs_require_only_seen_opening_and_preserve_reciprocal_native_entry(self):
        body = policy._main_stair_exit_body(0, FIELDS)
        for flags, inside, exits in ((0, True, []), (policy.state_for(1), False, []),
                                     (policy.state_for(1), True, [(FIELDS["bar"], 1)]),
                                     (policy.state_for(6), True, [(FIELDS["bar"], 1)])):
            commands, state = execute(body, flags, trigger_inside=inside)
            self.assertEqual([(native.word(ins.raw) & 0x7FFF, native.word(ins.raw, 3) & 0x7FFF)
                              for ins in commands if ins.opcode == 0x98], exits)
            self.assertEqual(state[policy.STATE], flags)


    def test_all_interlude_travel_bodies_and_actions_keep_the_current_party_until_load(self):
        for disc in (1, 2):
            fields = {**FIELDS, "main": core.CHAPTER_FIELDS[disc][2]}
            for stage in range(1, 7):
                flags = policy.state_for(stage)
                for room in policy.ACTIVE_ROOMS:
                    with self.subTest(disc=disc, stage=stage, direct_destination=room):
                        commands, state = execute(policy.travel(room, fields), flags)
                        self.assert_departure_preserves_live_party(commands, fields[room], 0)
                        self.assertEqual(state, {policy.STATE: flags, policy.LOCAL: flags})
                    for action in policy.actions_for(room):
                        branch = action.steps[0]
                        if not branch.target:
                            continue
                        with self.subTest(disc=disc, stage=stage, room=room, action=action.landmark):
                            body = policy._action_body(action, base_pc=0, room=room, fields=fields,
                                dialogue=dialogue, actors=ACTORS, editor=[], return_hub=core.HUB_FIELDS[disc],
                                next_ids=(), choice_id=99)
                            commands, state = execute(body, flags)
                            self.assert_departure_preserves_live_party(commands, fields[branch.target], branch.entry)
                            self.assertEqual(state, {policy.STATE: flags, policy.LOCAL: flags})


class PreparedInterludeTests(DepartureChecks, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config = core.ROOT / "project.local.json"
        if not config.is_file():
            raise unittest.SkipTest("Retail Disc1 configuration is required")
        source = Path(json.loads(config.read_text())["sources"]["retail_disc1"]["path"])
        if not source.is_file():
            raise unittest.SkipTest("Configured retail Disc1 is unavailable")
        cls.reader = core.DiscReader(source, 1)
        cls.prepared = core.prepare_replacements(cls.reader, core.load_chapters())

    def field(self, disc, room):
        field = ({"main": core.CHAPTER_FIELDS[disc][2], "bedroom": core.CHAPTER_TWO_BEDROOM_FIELD}
                 | resources.WORLD_FIELDS)[room]
        payload = next(item.data for item in self.prepared[disc] if item.canonical_id == core._field_bundle_id(field))
        return core.parse_field(payload)

    def test_actual_default_preparation_uses_only_private_rooms_and_solo_rico(self):
        for disc in (1, 2):
            resources_by_id = {item.canonical_id for item in self.prepared[disc]}
            for room, field in resources.WORLD_FIELDS.items():
                self.assertEqual(core._field_bundle_id(field) in resources_by_id, room in policy.ACTIVE_ROOMS, room)
            for room in policy.ACTIVE_ROOMS:
                field = self.field(disc, room)
                editor = core.AtelScript(field.parts[5].data)
                _, commands = _decode(field.parts[5].data)
                self.assertEqual(set(core._registered_character_entities(editor)), {5})
                for ins in commands.values():
                    self.assertNotIn(ins.extended_opcode, (0x84, 0xA1, 0x41, 0x1E), (disc, room, ins))
                    if ins.extended_opcode == 0x18:
                        self.assertEqual(ins.raw[2], 5, (disc, room, ins))
                    if ins.opcode in (0x98, 0x47):
                        target = native.word(ins.raw, 2 if ins.opcode == 0x47 else 1) & 0x7FFF
                        allowed = {core.HUB_FIELDS[disc], core.CHAPTER_FIELDS[disc][2],
                                   core.CHAPTER_TWO_BEDROOM_FIELD,
                                   *(resources.WORLD_FIELDS[key] for key in ("bar", "street", "commons"))}
                        self.assertIn(target, allowed, (disc, room, ins))
                    if ins.opcode in (0x35, 0x3A, 0x3B):
                        self.assertIn(native.word(ins.raw),
                            (policy.STATE, policy.LOCAL, core.CHAPTER_TWO_HAMMER_STATE_VARIABLE),
                            (disc, room, ins))
                    if ins.opcode == 0x3A:
                        self.assertEqual(native.word(ins.raw), policy.STATE)
                        self.assertIn(native.word(ins.raw, 3), (*policy.STAGE_BITS, *policy.SEEN_BITS))

    def test_actual_default_dialogue_contains_no_legacy_reenactment_and_presents_cleanly(self):
        expected = policy.load_dialogue()
        for disc in (1, 2):
            for room in policy.ACTIVE_ROOMS:
                field = self.field(disc, room)
                result = present_field(field.source, speaker_portraits())
                after = core.parse_field(result.bundle)
                self.assertEqual(set(core._registered_character_entities(core.AtelScript(after.parts[5].data))), {5})
                for part in (1, 2, 3, 4, 6, 8):
                    self.assertEqual(after.parts[part].data, field.parts[part].data)
                texts = [block.text for block in parse_dialogue(field.parts[7].data).blocks]
                expected_count = sum(map(len, expected.values()))
                self.assertGreaterEqual(len(texts), expected_count)
                self.assertNotIn("Rank A", " ".join(texts))
                self.assertNotIn("Continue to Next Chapter", " ".join(texts))
                _, commands = _decode(field.parts[5].data)
                bytecode = core.AtelScript(field.parts[5].data).bytecode
                for ins in commands.values():
                    if ins.opcode == 0xF5:
                        self.assertEqual(bytecode[ins.pc - 4:ins.pc], b"\xFE\x0D\xFC\x80")

    def test_actual_main_cast_and_interaction_carriers_follow_new_period_bits(self):
        actions = policy.actions_for("main")
        for disc in (1, 2):
            editor = core.AtelScript(self.field(disc, "main").parts[5].data)
            for name, actor, final_visible in (("suzarn", 4, 2), ("hammer", 19, 3)):
                offset = next(index for index, action in enumerate(actions) if action.landmark == name)
                carrier = editor.entity_count - len(actions) + offset
                self.assertEqual(editor.get_script_pointer(actor, 2), editor.get_script_pointer(carrier, 2))
                for stage in range(1, 7):
                    flags = policy.state_for(stage)
                    actor_commands, _ = execute_at(editor, actor, 0, flags)
                    carrier_commands, _ = execute_at(editor, carrier, 0, flags)
                    self.assertEqual(any(ins.opcode == 0x0B for ins in actor_commands), stage <= final_visible)
                    self.assertEqual(any(ins.opcode == 0x18 for ins in carrier_commands), stage <= final_visible)
                    if stage <= final_visible:
                        self.assertIn(b"\x20\x0D\x80", [ins.raw for ins in actor_commands])
            rico = core._registered_character_entities(editor)[5]
            for stage in range(1, 7):
                initial = 0 if stage == 1 else policy.state_for(stage, seen=False)
                commands, after = execute_at(editor, 0, 1, initial)
                called = {ins.raw[1] for ins in commands if ins.opcode == 0x09}
                expected = {rico, 4, 19} if stage <= 2 else {rico, 19} if stage == 3 else {rico}
                self.assertEqual(called, expected, (disc, stage))
                self.assertEqual(after[policy.STATE], policy.state_for(stage))
                again, unchanged = execute_at(editor, 0, 1, after[policy.STATE])
                self.assertFalse(windows(again))
                self.assertEqual(unchanged[policy.STATE], after[policy.STATE])
                self.assertTrue(any(ins.extended_opcode == 0x53 for ins in again))

    def test_both_presented_stairs_preserve_party_and_state_until_destination_init(self):
        for disc in (1, 2):
            fields = {**FIELDS, "main": core.CHAPTER_FIELDS[disc][2]}
            for presented in (False, True):
                editors = {}
                for room in ("main", "bar"):
                    field = self.field(disc, room)
                    if presented:
                        field = core.parse_field(present_field(field.source, speaker_portraits()).bundle)
                    editors[room] = core.AtelScript(field.parts[5].data)
                for stage in range(1, 7):
                    flags = policy.state_for(stage)
                    for source, destination in (("main", "bar"), ("bar", "main")):
                        with self.subTest(disc=disc, presented=presented, stage=stage, source=source):
                            commands, after = execute_at(editors[source], 3, 1, flags, trigger_inside=True)
                            self.assert_departure_preserves_live_party(commands, fields[destination], 1)
                            self.assertEqual(after, {policy.STATE: flags, policy.LOCAL: flags})
                            outside, unchanged = execute_at(editors[source], 3, 1, flags, trigger_inside=False)
                            self.assertFalse(any(ins.opcode == 0x98 for ins in outside))
                            self.assertEqual(unchanged, after)

                            # Party preparation remains in destination INIT, before
                            # the registered Rico actor enters its normal A7 update.
                            target = editors[destination]
                            initialized, loaded = execute_at(target, 0, 0, flags)
                            self.assertEqual([ins.raw[2] for ins in initialized
                                              if ins.extended_opcode == 0x18], [5])
                            self.assertEqual(sum(ins.extended_opcode == 0x1A for ins in initialized), 1)
                            self.assertEqual([native.word(ins.raw) & 0x7FFF for ins in initialized
                                              if ins.opcode == 0x75], [47 if destination == "main" else 71])
                            self.assertEqual(loaded, after)
                            registered = core._registered_character_entities(target)
                            self.assertEqual(set(registered), {5})
                            actor_init, _ = execute_at(target, registered[5], 0, flags)
                            self.assertEqual([native.word(ins.raw) & 0x7FFF for ins in actor_init
                                              if ins.opcode == 0x16], [5])
                            actor_update, _ = execute_at(target, registered[5], 1, flags)
                            self.assertIn(0xA7, [ins.opcode for ins in actor_update])
                            if destination == "main":
                                revisit, ready = execute_at(target, 0, 1, flags)
                                self.assertFalse(windows(revisit))
                                self.assertFalse(any(ins.opcode == 0x05 for ins in revisit))
                                unblack = next(index for index, ins in enumerate(revisit)
                                    if ins.opcode == 0xF1 and all(
                                        (value & 0x7FFF) == 0 for value in struct.unpack_from("<5H", ins.raw, 1)[1:4]))
                                unlock = next(index for index, ins in enumerate(revisit) if ins.extended_opcode == 0x53)
                                self.assertLess(unblack, unlock)
                                self.assertTrue(any(ins.opcode == 0x26 for ins in revisit[unblack + 1:unlock]))
                                self.assertEqual(revisit[-1].opcode, 0x5B)
                                self.assertEqual(ready, after)

    def test_prepared_noticeboard_and_bed_skips_do_not_reload_the_departing_party(self):
        for disc in (1, 2):
            for room in ("main", "bedroom"):
                field = self.field(disc, room)
                # Trace the compiled narration before portrait subroutines are
                # inserted: the shared tracer deliberately does not execute CALL.
                # The dialogue-free stair paths above also run after presentation.
                editor = core.AtelScript(field.parts[5].data)
                actions = policy.actions_for(room)
                offset = next(index for index, action in enumerate(actions) if action.steps[0].complete)
                carrier = editor.entity_count - len(actions) + offset
                for stage in range(1, 6):
                    with self.subTest(disc=disc, room=room, stage=stage):
                        commands, state = execute_at(editor, carrier, 2, policy.state_for(stage),
                            initial_variables={core.MENU_SELECTION_VARIABLE: 1})
                        self.assert_departure_preserves_live_party(commands, core.CHAPTER_FIELDS[disc][2], 0)
                        self.assertEqual(state[policy.STATE], policy.state_for(stage + 1, seen=False))
                        self.assertEqual(state[policy.LOCAL], state[policy.STATE])
                        self.assertTrue(windows(commands), "The deliberate skip must retain its narration")


if __name__ == "__main__":
    unittest.main()
