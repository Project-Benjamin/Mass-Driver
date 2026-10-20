"""Explore retained historical Chapter 2 emitters with symbolic presentation.

This models successful battle returns and field entry, not emulator timing or
movement. Native choreography has separate tests; its declared dialogue hooks
are included here so graph reachability can be checked against authored content.
The preserved retail bedroom doorway is outside this state-graph model.
The default release uses chapter_two_interludes and never dispatches these
historical battles or reenactments.
"""

from collections import defaultdict, deque
from contextlib import ExitStack
from dataclasses import dataclass
import re
import unittest
from unittest.mock import patch

from modules.rico import chapter_two as chapter
from modules.rico import chapter_two_scenes as choreography


ROOMS = (
    "main", "bedroom", "intake", "bar", "street", "commons", "baptism", "prep",
    "sewer_entry", "sewer_hub", "sewer_key", "sewer_drain", "arena", "central",
)
MARKER = re.compile(rb"\xF0([a-z]+):([a-zA-Z0-9_:]+)\xF1")


def event(kind, value):
    return b"\xF0" + f"{kind}:{value}".encode("ascii") + b"\xF1"


class RecordedRoutine:
    """Record actual emitted branches instead of reconstructing their order."""

    def __init__(self, base_pc):
        self.base_pc = base_pc
        self.operations = []

    @property
    def pc(self):
        return self.base_pc + len(self.operations)

    def emit(self, value):
        self.operations.append(("emit", value))

    def jump(self, label):
        self.operations.append(("jump", label))

    def jump_if_bit_clear(self, variable, mask, label):
        if variable != chapter.STATE:
            raise AssertionError(f"Unexpected graph condition variable {variable:#x}")
        self.operations.append(("clear", mask, label))

    def label(self, label):
        self.operations.append(("label", label))

    def finish(self):
        return tuple(self.operations)


@dataclass(frozen=True)
class State:
    room: str = "intake"
    flags: int = 0
    complete: bool = False

    def has(self, name):
        return bool(self.flags & (1 << chapter.BITS[name]))


class Graph:
    def __init__(self):
        self.automatic = {}
        self.actions = {}
        fields = {room: index + 100 for index, room in enumerate(ROOMS)}

        def scene(routine, name, dialogue, actors, editor):
            routine.emit(event("choreography", name))
            for key in choreography.CHOREOGRAPHY_SCENES.get(name, ()):
                routine.emit(dialogue(key))

        def commit(*names):
            return b"".join(event("set", name) for name in names)

        def completion(routine, *args, **kwargs):
            routine.emit(event("complete", "yes"))

        with ExitStack() as patches:
            for owner, name, value in (
                (chapter.core.mass_driver, "_RoutineBuilder", RecordedRoutine),
                (chapter.core, "_wait", lambda *args: b""),
                (chapter.core, "_playable_action_prefix", lambda *args: b""),
                (chapter.core, "_playable_action_finish", lambda *args: b"\x00"),
                (chapter.core, "_party_setup", lambda *args: b""),
                (chapter.core, "_gear_battle_stage", lambda **kwargs: (b"", b"")),
                (chapter.core, "_play_music", lambda *args: b""),
                (chapter.core.mass_driver, "_fixed_battle", lambda number: event("battle", str(number))),
                (chapter, "commit", commit),
                (chapter, "travel", lambda room, fields, entry=0: event("travel", room) + b"\x5B"),
                (chapter, "_scene", scene),
                (chapter, "_completion", completion),
            ):
                patches.enter_context(patch.object(owner, name, value))
            def dialogue(key, start=0, stop=None):
                suffix = f":{start}" if start or stop is not None else ""
                return event("scene", key + suffix)
            for room in ROOMS:
                self.automatic[room] = chapter._automatic_body(
                    room, base_pc=0, fields=fields, dialogue=dialogue, actors={"fei": 1}, editor=[])
                for action in chapter.actions_for(room):
                    self.actions[room, action.landmark] = chapter._action_body(
                        action, base_pc=0, room=room, fields=fields, dialogue=dialogue,
                        actors={}, editor=[], return_hub=720, next_ids=(), choice_id=0)

    def run(self, program, state):
        # Rooms without automatic work return the native stop instruction.
        if isinstance(program, bytes):
            if program != b"\x5B":
                raise AssertionError(f"Unexpected automatic body {program!r}")
            return state, (), False
        labels = {op[1]: index for index, op in enumerate(program) if op[0] == "label"}
        pc = 0
        room, flags, complete = state.room, state.flags, state.complete
        trace = []
        travelled = False
        for _ in range(500):
            if pc >= len(program):
                break
            op = program[pc]
            pc += 1
            if op[0] == "jump":
                pc = labels[op[1]]
            elif op[0] == "clear" and not flags & op[1]:
                pc = labels[op[2]]
            elif op[0] == "emit":
                for raw_kind, raw_value in MARKER.findall(op[1]):
                    kind, value = raw_kind.decode(), raw_value.decode()
                    trace.append(f"{kind}:{value}")
                    if kind == "set":
                        flags |= 1 << chapter.BITS[value]
                    elif kind == "travel":
                        room, travelled = value, True
                    elif kind == "complete":
                        complete = True
                if op[1].endswith(b"\x5B"):
                    break
        else:
            raise AssertionError("Emitted graph routine did not terminate")
        return State(room, flags, complete), tuple(trace), travelled

    def enter(self, state):
        trace = []
        for _ in range(12):
            state, emitted, travelled = self.run(self.automatic[state.room], state)
            trace.extend(emitted)
            if not travelled:
                return state, tuple(trace)
        raise AssertionError("Automatic field transitions did not settle")

    def act(self, state, landmark):
        state, trace, travelled = self.run(self.actions[state.room, landmark], state)
        if travelled:
            state, entry = self.enter(state)
            trace += entry
        return state, trace

    def explore(self):
        initial, first = self.enter(State())
        paths = {initial: first}
        edges = defaultdict(set)
        queue = deque([initial])
        while queue:
            state = queue.popleft()
            if state.complete:
                continue
            for action in chapter.actions_for(state.room):
                successor, trace = self.act(state, action.landmark)
                edges[state].add(successor)
                if successor not in paths:
                    paths[successor] = paths[state] + trace
                    queue.append(successor)
            if len(paths) > 10000:
                raise AssertionError("Unexpectedly unbounded Chapter 2 state graph")
        return paths, edges


class ChapterTwoProgressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = Graph()

    def test_delivery_precedes_room_intro_and_hammer_report(self):
        state, trace = self.graph.enter(State())
        self.assertEqual(state.room, "main")
        self.assertTrue(state.has("delivery"))
        self.assertTrue(state.has("room_intro"))
        self.assertTrue(state.has("hammer"))
        self.assertLess(trace.index("scene:arrival_delivery"), trace.index("scene:room_first"))
        self.assertLess(trace.index("scene:room_first"), trace.index("scene:hammer_report"))
        self.assertEqual(tuple(item for item in trace if item.startswith("travel:")), ("travel:main",))
        departed, response = self.graph.act(state, "exit")
        self.assertEqual(departed.room, "bar")
        self.assertIn("travel:bar", response)
        street, _ = self.graph.act(departed, "street_exit")
        self.assertEqual(street.room, "street")
        dorm, _ = self.graph.act(street, "east_dorm")
        self.assertEqual(dorm.room, "commons")
        repeated, response = self.graph.act(state, "hammer")
        self.assertEqual(repeated, state)
        self.assertNotIn("scene:hammer_report", response)

    def test_hammer_repeat_uses_yard_then_stier_without_a_phantom_worker_request(self):
        ready = sum(1 << chapter.BITS[flag] for flag in ("delivery", "room_intro", "hammer"))
        _, before = self.graph.act(State("main", ready), "hammer")
        self.assertIn("scene:room_hammer_before_baptism", before)
        self.assertNotIn("scene:dblock_hammer_before", before)
        _, after = self.graph.act(State("main", ready | (1 << chapter.BITS['baptism'])), "hammer")
        self.assertIn("scene:dblock_hammer_before", after)
        self.assertNotIn("scene:room_hammer_before_baptism", after)

    def test_legacy_room_save_can_finish_hammers_report_and_leave(self):
        state = State("main", sum(1 << chapter.BITS[name] for name in ("delivery", "room_intro")))
        blocked, response = self.graph.act(state, "exit")
        self.assertEqual(blocked, state)
        self.assertIn("scene:room_exit_before", response)
        heard, response = self.graph.act(state, "hammer")
        self.assertTrue(heard.has("hammer"))
        self.assertIn("scene:hammer_report", response)
        departed, _ = self.graph.act(heard, "exit")
        self.assertEqual(departed.room, "bar")

    def test_complete_route_keeps_all_required_milestones_in_order(self):
        paths, _ = self.graph.explore()
        completed_paths = [trace for state, trace in paths.items() if state.complete]
        self.assertTrue(completed_paths, "No complete route exists")
        trace = min(completed_paths, key=len)
        expected = (
            "scene:arrival_delivery", "scene:hammer_report", "choreography:baptism",
            "battle:6", "scene:defense_after", "scene:fei_explosion_report",
            "scene:murders_report", "scene:investigation_request", "scene:sewer_entry",
            "battle:15",
            "scene:redrum_after", "scene:injury_exit", "choreography:bandage",
            "scene:finals_before", "choreography:finals", "scene:title_clerk",
            "scene:league_return", "choreography:crash", "scene:central_approach",
            "scene:central_flight", "scene:chapter_end", "complete:yes",
        )
        offsets = [trace.index(event) for event in expected]
        self.assertEqual(offsets, sorted(offsets))
        for clue in ("scene:sewer_slime", "scene:sewer_key", "scene:sewer_bell"):
            self.assertLess(trace.index("scene:investigation_request"), trace.index(clue))
            self.assertLess(trace.index(clue), trace.index("battle:15"))
        self.assertEqual(trace.count("battle:6"), 1)
        self.assertEqual(trace.count("battle:15"), 1)

    def test_every_reachable_state_can_still_complete(self):
        paths, edges = self.graph.explore()
        finishable = {state for state in paths if state.complete}
        self.assertTrue(finishable, "No completion state is reachable")
        reverse = defaultdict(set)
        for source, targets in edges.items():
            for target in targets:
                reverse[target].add(source)
        queue = deque(finishable)
        while queue:
            for predecessor in reverse[queue.popleft()] - finishable:
                finishable.add(predecessor)
                queue.append(predecessor)
        stranded = set(paths) - finishable
        self.assertFalse(stranded, f"Stranded states: {sorted(stranded, key=repr)[:8]}")

    def test_reachable_flags_never_bypass_future_event_prerequisites(self):
        prerequisites = {
            "room_intro": ("delivery",), "hammer": ("delivery", "room_intro"),
            "baptism": ("hammer",), "defense": ("baptism",),
            "murders": ("defense",), "investigation": ("murders",),
            "key": ("investigation",), "evidence": ("investigation",), "bell": ("investigation",),
            "redrum": ("key", "evidence", "bell"), "bandage": ("redrum",),
            "finals": ("bandage",), "title": ("finals",),
            "crash": ("title",), "flight": ("crash",),
        }
        paths, _ = self.graph.explore()
        for state, trace in paths.items():
            for event_name, required in prerequisites.items():
                if state.has(event_name):
                    for earlier in required:
                        self.assertTrue(state.has(earlier), f"{event_name} without {earlier}: {trace}")
            if state.complete:
                self.assertTrue(state.has("flight"))

    def test_repeating_current_npc_interactions_cannot_advance_objectives(self):
        paths, _ = self.graph.explore()
        npc_landmarks = {"worker", "battler", "prisoner", "fei", "official", "hammer", "gramps", "suzarn"}
        for state in paths:
            if state.complete:
                continue
            for action in chapter.actions_for(state.room):
                if action.landmark not in npc_landmarks:
                    continue
                first, _ = self.graph.act(state, action.landmark)
                repeated, _ = self.graph.act(first, action.landmark)
                self.assertEqual(repeated, first, (state, action.name))

    def test_treatment_gate_requires_all_three_clues_in_any_collection_order(self):
        base = sum(1 << chapter.BITS[name] for name in
                   ("delivery", "room_intro", "hammer", "baptism", "defense", "murders", "investigation"))
        clues = ("key", "evidence", "bell")
        for combination in range(8):
            flags = base | sum(1 << chapter.BITS[name] for index, name in enumerate(clues)
                               if combination & (1 << index))
            state, trace = self.graph.act(State("sewer_hub", flags), "forward")
            self.assertEqual(state.room, "sewer_drain" if combination == 7 else "sewer_hub")
            if combination != 7:
                first_missing = next(index for index in range(3) if not combination & (1 << index))
                hints = tuple(item for item in trace if item.startswith("scene:treatment_gate_locked"))
                self.assertEqual(hints, (f"scene:treatment_gate_locked:{first_missing}",))

    def test_post_redrum_repeat_dialogue_does_not_restart_the_investigation(self):
        paths, _ = self.graph.explore()
        examined = 0
        for state in paths:
            if state.room != "commons" or not state.has("redrum") or state.has("finals"):
                continue
            examined += 1
            for landmark in ("fei", "sewer_exit"):
                repeated, trace = self.graph.act(state, landmark)
                self.assertEqual(repeated, state)
                self.assertNotIn("scene:fei_after_investigation", trace)
                self.assertNotIn("scene:investigation_request", trace)
                self.assertNotIn("scene:injury_exit", trace)
        self.assertGreater(examined, 0)

    def test_repeated_automatic_entry_does_not_reaward_progress(self):
        initial, _ = self.graph.enter(State())
        repeated, trace = self.graph.enter(initial)
        self.assertEqual(repeated, initial)
        self.assertNotIn("scene:arrival_delivery", trace)
        self.assertNotIn("scene:room_first", trace)
        baptized = State("baptism", initial.flags | sum(1 << chapter.BITS[name] for name in ("hammer", "baptism")))
        repeated, trace = self.graph.enter(baptized)
        self.assertEqual(repeated, baptized)
        self.assertNotIn("choreography:baptism", trace)

    def test_completed_delivery_and_old_room_saves_do_not_replay_cutaway(self):
        initial, _ = self.graph.enter(State())
        repeated, trace = self.graph.enter(State("intake", initial.flags))
        self.assertEqual(repeated, initial)
        self.assertNotIn("scene:arrival_delivery", trace)
        for flags in (0, 1 << chapter.BITS["room_intro"], initial.flags):
            restored, trace = self.graph.enter(State("main", flags))
            self.assertEqual(restored.room, "main")
            self.assertFalse(any(item.startswith("travel:") for item in trace))
            self.assertNotIn("scene:arrival_delivery", trace)

    def test_every_authored_scene_has_a_reachable_graph_or_bedroom_response(self):
        paths, _ = self.graph.explore()
        seen = set()
        # This dialogue only serves a pre-repair room save whose introduction
        # completed before Hammer's previously separate report.
        legacy = State("main", sum(1 << chapter.BITS[name] for name in ("delivery", "room_intro")))
        _, legacy_trace = self.graph.act(legacy, "exit")
        seen.update(item.split(":", 2)[1] for item in legacy_trace if item.startswith("scene:"))
        for state, path in paths.items():
            traces = [path]
            if not state.complete:
                for action in chapter.actions_for(state.room):
                    _, trace = self.graph.act(state, action.landmark)
                    traces.append(trace)
            # The main/bedroom door is preserved native routing, tested by the
            # room-build suite. Here verify its response for each reachable flag set.
            _, bedroom_trace = self.graph.act(State("bedroom", state.flags), "bed")
            traces.append(bedroom_trace)
            for trace in traces:
                seen.update(item.split(":", 2)[1] for item in trace if item.startswith("scene:"))
        self.assertEqual(seen, set(chapter.load_dialogue()))


if __name__ == "__main__":
    unittest.main()
