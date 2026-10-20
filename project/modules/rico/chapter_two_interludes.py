"""Rico's private Nortune intervals, separated by deliberate narration skips.

This policy supplies the current Chapter2 route. It does not call the legacy
campaign's scenes, battle graph, Gear setup or original-story progression.
Only the already reserved anthology STATE and its LOCAL mirror record time.
"""
from __future__ import annotations

from dataclasses import replace
import json

from modules.rico import build as core
from modules.rico import chapter_two_opening as opening
from modules.rico import chapter_two_scenes as staging


STATE = core.CHAPTER_TWO_PERSISTENT_STATE_VARIABLE
LOCAL = core.PLAYABLE_STATE_VARIABLE
ACTIVE_ROOMS = ("main", "bedroom", "bar", "street", "commons")
STAGE_BITS = tuple(range(6))
SEEN_BITS = tuple(range(8, 14))
STAGE_KEYS = (
    "gap_01_familiar", "gap_02_after_yard", "gap_03_absence",
    "gap_04_small_task", "gap_05_without_title", "gap_06_before_league",
)
CHOICE_TEXT = (
    "<Opcode:01:FF>Move to the next interval?\n"
    "     Continue\n     Stay here<Close>"
)
choice_text = CHOICE_TEXT
CONTENT_PATH = core.CONTENT_ROOT / "chapter_02_interludes.json"


def load_dialogue() -> dict[str, tuple[str, ...]]:
    document = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    if document.get("format") != "xenogears-rico-chapter-two-interludes-v1":
        raise core.RicoArcBuildError("Unknown Rico interlude document")
    result = {key: tuple(blocks) for key, blocks in document["scenes"].items()}
    required = set(STAGE_KEYS) | {"gap_intro", "gap_outro", "gap_repeat_03_hammer"}
    required.update(f"gap_skip_{stage:02d}" for stage in range(1, 7))
    required.update(f"gap_optional_{name}" for name in
                    ("hammer", "suzarn", "schedule", "bed", "worker",
                     "battler", "prisoner", "clerk"))
    if not required <= result.keys():
        raise core.RicoArcBuildError(f"Missing Rico interlude dialogue: {sorted(required - result.keys())}")
    for key, blocks in result.items():
        if not blocks or any(not isinstance(text, str) or not text.endswith("<Close>") for text in blocks):
            raise core.RicoArcBuildError(f"Incomplete Rico interlude dialogue: {key}")
    return result


def state_for(stage: int, *, seen: bool = True) -> int:
    """One-based interval to the cumulative private-state contract."""
    if not 1 <= stage <= 6:
        raise ValueError("Rico interlude stage must be 1..6")
    return ((1 << stage) - 1) | (((1 << (stage if seen else stage - 1)) - 1) << 8)


def stage_for(state: int) -> int:
    """Fresh zero represents interval1 until its director initializes it."""
    return max(1, (state & 0x3F).bit_length())


def npc_visible_until(name: str) -> int | None:
    """The availability bit whose arrival retires this private-room actor."""
    return {"suzarn": STAGE_BITS[2], "hammer": STAGE_BITS[3]}.get(name)


def gated_init(base_pc: int, name: str, body: bytes) -> bytes:
    cutoff = npc_visible_until(name)
    if cutoff is None:
        return body
    routine = core.mass_driver._RoutineBuilder(base_pc)
    routine.jump_if_bit_clear(STATE, 1 << cutoff, "visible")
    routine.emit(core.INERT_HIDDEN_INIT)
    routine.label("visible")
    routine.emit(body)
    return routine.finish()


def party_for(room: str) -> tuple[int, ...]:
    if room not in ACTIVE_ROOMS:
        raise core.RicoArcBuildError(f"Original event room is outside Rico's interludes: {room}")
    return (5,)


def actions_for(room: str):
    from modules.rico.chapter_two import Action, step
    table = {
        "main": (
            Action("Hammer", "hammer", (step("gap_optional_hammer"),)),
            Action("Noticeboard", "schedule", (step("gap_optional_schedule", complete=True),)),
            Action("Suzarn", "suzarn", (step("gap_optional_suzarn"),)),
            Action("Stairs to Latina's Bar", "exit", (step(target="bar", entry=1),)),
        ),
        "bedroom": (Action("Bed", "bed", (step("gap_optional_bed", complete=True),)),),
        "bar": (
            Action("Champion's rooms", "room_exit", (step(target="main", entry=1),)),
            Action("D Block street", "street_exit", (step(target="street", entry=5),)),
        ),
        "street": (
            Action("Latina's Bar", "bar_exit", (step(target="bar"),)),
            Action("D Block east dormitory door", "east_dorm", (step(target="commons"),)),
            Action("D Block west dormitory door", "west_dorm", (step(target="commons", entry=1),)),
        ),
        "commons": (
            Action("Worker", "worker", (step("gap_optional_worker"),)),
            Action("Battler", "battler", (step("gap_optional_battler"),)),
            Action("Prisoner", "prisoner", (step("gap_optional_prisoner"),)),
            Action("Clerk", "official", (step("gap_optional_clerk"),)),
            Action("D Block west street door", "room_exit", (step(target="street", entry=2),)),
            Action("D Block east street door", "east_exit", (step(target="street", entry=1),)),
        ),
    }
    return table[room]


def _commit(bit: int) -> bytes:
    if bit not in (*STAGE_BITS, *SEEN_BITS):
        raise ValueError("Only private interval bits can be committed")
    return core.atel.set_var_bit(STATE, bit) + core._restore_chapter_two_state()


def travel(room: str, fields, entry: int = 0) -> bytes:
    party_for(room)
    # Every interlude destination installs solo Rico in its director INIT.
    # Preserve the live party during departure instead of removing its
    # leader and waiting for an asynchronous reload after the black fade.
    return (core._chapter_two_transition_out() + core._restore_chapter_two_state()
            + core._change_field(fields[room], entry) + b"\x5B")


def director_body(room: str, music: int, base_pc: int) -> bytes:
    party_for(room)
    routine = core.mass_driver._RoutineBuilder(base_pc)
    routine.emit(core._chapter_two_director(music)[:-1])
    if room == "main":
        routine.emit(b"\x33\xFE\x54")
        routine.emit(core.mass_driver._facility_video_screen_fade_body(255, 1)[:-3])
    routine.emit(core._party_setup((5,)) + b"\x00")
    return routine.finish()


def build_private_scene(base_pc: int, stage: int, *, actors, dialogue) -> staging.SceneBuild:
    if not 1 <= stage <= 6:
        raise ValueError("Unknown private interval")
    names = ("rico", "suzarn", "hammer") if stage <= 2 else ("rico", "hammer") if stage == 3 else ("rico",)
    entities = tuple(actors[name] for name in names)
    scene = staging._Scene(base_pc, 218, entities, 16, dialogue)
    positions = {"rico": opening.MAIN_RICO, "suzarn": opening.MAIN_SUZARN,
                 "hammer": opening.MAIN_HAMMER}
    directions = {"rico": 4, "suzarn": 0, "hammer": 6}
    calls = b"".join(scene.actor(actors[name], 0, f"Private room position: {name}",
                                  staging._stage(positions[name][:2], directions[name])) for name in names)
    scene.open(calls, opening.CONVERSATION_TARGET, opening.CONVERSATION_EYE, entities)
    if len(names) > 1:
        scene.body.extend(staging._look(actors["rico"], actors[names[1]]))
        for name in names[1:]:
            scene.body.extend(staging._look(actors[name], actors["rico"]))
    scene.say(STAGE_KEYS[stage - 1])
    scene.body.extend(staging._wait(12))
    built = scene.finish()
    routines = tuple(replace(routine, body=opening.NPC_PASSABLE_FLAGS + b"\x00")
                     if routine.entity != actors["rico"] and routine.script_index == 20
                     else routine for routine in built.actor_routines)
    return replace(built, actor_routines=routines)


def _automatic_body(room: str, *, base_pc: int, fields, dialogue, actors, editor) -> bytes:
    if room != "main":
        party_for(room)
        return b"\x5B"
    routine = core.mass_driver._RoutineBuilder(base_pc)
    routine.emit(core._playable_action_prefix(routine.pc) + core._wait(20))
    routine.jump_if_bit_clear(STATE, 1, "fresh")
    routine.jump("select")
    routine.label("fresh")
    routine.emit(_commit(STAGE_BITS[0]))
    routine.emit(b"\xFE\x0D\xFC\x80" + dialogue("gap_intro"))
    routine.label("select")
    actor_routines = {}
    for stage in range(6, 0, -1):
        routine.jump_if_bit_clear(STATE, 1 << STAGE_BITS[stage - 1], f"not_stage_{stage}")
        routine.jump_if_bit_clear(STATE, 1 << SEEN_BITS[stage - 1], f"play_stage_{stage}")
        routine.jump("ready")
        routine.label(f"play_stage_{stage}")
        built = build_private_scene(routine.pc, stage, actors=actors, dialogue=dialogue)
        if hasattr(editor, "walkmesh"):
            staging.validate_geometry(built, editor.walkmesh)
        for actor in built.actor_routines:
            key = (actor.entity, actor.script_index)
            if key in actor_routines and actor_routines[key].body != actor.body:
                raise core.RicoArcBuildError("Private scene actor routines collide")
            actor_routines[key] = actor
        routine.emit(built.body + _commit(SEEN_BITS[stage - 1]))
        routine.jump("ready")
        routine.label(f"not_stage_{stage}")
    routine.label("ready")
    # Main INIT always holds black. Revisited, already-seen intervals need
    # the same explicit fade/input release as freshly played scenes.
    routine.emit(core.mass_driver._facility_video_screen_fade_body(0, 12))
    routine.emit(core._playable_action_finish(routine.pc)[:-1] + b"\x5B")
    editor.extend(actor_routines.values())
    return routine.finish()


def _continue(routine, fields, dialogue, return_hub: int, choice_id: int) -> None:
    routine.emit(b"\xFE\x0D\xFC\x80" + core._choice_dialog(choice_id, flags=1) + b"\xA9\x12\x9C")
    routine.jump_if_not_equal(core.MENU_SELECTION_VARIABLE, 1, "continue_done")
    routine.emit(core._wait_for_pad_release(core.PAD_MASK_CROSS, routine.pc))
    for stage in range(6, 0, -1):
        routine.jump_if_bit_clear(STATE, 1 << STAGE_BITS[stage - 1], f"skip_stage_{stage}")
        # A current scene must finish before time can advance, including
        # early object activation or an interrupted field-load state.
        routine.jump_if_bit_clear(STATE, 1 << SEEN_BITS[stage - 1], "continue_done")
        routine.emit(core._chapter_two_transition_out() + b"\xFE\x0D\xFC\x80")
        routine.emit(dialogue(f"gap_skip_{stage:02d}"))
        if stage < 6:
            routine.emit(_commit(STAGE_BITS[stage]))
            routine.emit(travel("main", fields))
        else:
            routine.emit(dialogue("gap_outro"))
            routine.emit(core._hub_launch_body(return_hub))
        routine.label(f"skip_stage_{stage}")
    routine.label("continue_done")


def _action_body(action, *, base_pc: int, room: str, fields, dialogue, actors,
                 editor, return_hub, next_ids, choice_id) -> bytes:
    party_for(room)
    routine = core.mass_driver._RoutineBuilder(base_pc)
    routine.emit(core._playable_action_prefix(routine.pc))
    # Policy branches are unconditional; no original event or battle branch
    # is permitted to leak in through the generic assembler's Action type.
    if len(action.steps) != 1:
        raise core.RicoArcBuildError("Interlude actions require one explicit branch")
    branch = action.steps[0]
    if branch.battle is not None or branch.choreography or branch.sets or branch.requires or branch.absent:
        raise core.RicoArcBuildError("Original campaign progression reached an interlude action")
    for key in branch.scenes:
        if key == "gap_optional_hammer":
            routine.jump_if_bit_clear(STATE, 1 << STAGE_BITS[2], "hammer_ordinary")
            routine.emit(b"\xFE\x0D\xFC\x80" + dialogue("gap_repeat_03_hammer"))
            routine.jump("hammer_spoken")
            routine.label("hammer_ordinary")
            routine.emit(b"\xFE\x0D\xFC\x80" + dialogue(key))
            routine.label("hammer_spoken")
        else:
            routine.emit(b"\xFE\x0D\xFC\x80" + dialogue(key))
    if branch.complete:
        _continue(routine, fields, dialogue, return_hub, choice_id)
    if branch.target:
        routine.emit(core._wait_for_pad_release(core.PAD_MASK_CROSS, routine.pc))
        routine.emit(travel(branch.target, fields, branch.entry))
    routine.emit(b"\xFE\x0D\xFC\x80")
    routine.emit(core._playable_action_finish(routine.pc))
    return routine.finish()


def _main_stair_exit_body(base_pc: int, fields) -> bytes:
    routine = core.mass_driver._RoutineBuilder(base_pc)
    routine.jump_if_bit_clear(STATE, 1 << SEEN_BITS[0], "idle")
    departing = travel("bar", fields, 1)
    routine.emit(b"\xCB\x00" + core._u16(routine.pc + 4 + len(departing)) + departing)
    routine.label("idle")
    routine.emit(b"\x00")
    return routine.finish()


def validate_graph() -> dict:
    scenes = load_dialogue()
    for room in ACTIVE_ROOMS:
        for action in actions_for(room):
            for branch in action.steps:
                if branch.target and branch.target not in ACTIVE_ROOMS:
                    raise core.RicoArcBuildError("Interlude route leaves its private exploration rooms")
                if any(key not in scenes for key in branch.scenes):
                    raise core.RicoArcBuildError("Missing optional private dialogue")
                if branch.battle is not None or branch.choreography or branch.sets:
                    raise core.RicoArcBuildError("Interlude graph contains original gameplay")
    return {"rooms": len(ACTIVE_ROOMS), "stages": 6, "authored_scenes": len(scenes),
            "authored_blocks": sum(map(len, scenes.values())), "state_variable": STATE,
            "stage_bits": STAGE_BITS, "seen_bits": SEEN_BITS}
