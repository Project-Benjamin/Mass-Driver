"""The Champ: a persistent, connected Chapter 2 field campaign.

The legacy one-room builder remains available for historical regression tests.
Release preparation replaces that room's actions with this world graph and
installs its additional retail-art fields on each supported disc.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Callable, Mapping

from modules.rico import build as core
from modules.rico.chapter_two_music import room_music


STATE = core.CHAPTER_TWO_PERSISTENT_STATE_VARIABLE
LOCAL = core.PLAYABLE_STATE_VARIABLE
BITS = {
    "room_intro": 0, "hammer": 1, "baptism": 2, "defense": 3,
    "murders": 4, "key": 5, "evidence": 6, "bell": 7,
    "redrum": 8, "bandage": 9, "finals": 10, "title": 11,
    "crash": 12, "flight": 13, "delivery": 14, "investigation": 15,
}


@dataclass(frozen=True)
class Step:
    scenes: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    absent: tuple[str, ...] = ()
    sets: tuple[str, ...] = ()
    target: str | None = None
    battle: int | None = None
    choreography: str | None = None
    complete: bool = False
    entry: int = 0


@dataclass(frozen=True)
class Action:
    name: str
    landmark: str
    steps: tuple[Step, ...]


class ActorRoutines(list):
    def __init__(self, walkmesh: bytes):
        super().__init__()
        self.walkmesh = walkmesh


def step(*scenes: str, requires=(), absent=(), sets=(), target=None,
         battle=None, choreography=None, complete=False, entry=0) -> Step:
    return Step(tuple(scenes), tuple(requires), tuple(absent), tuple(sets),
                target, battle, choreography, complete, entry)


def actions_for(room: str) -> tuple[Action, ...]:
    """First matching branch wins; every successful action is replay-safe."""
    table = {
        "main": (
            Action("Hammer", "hammer", (
                step("hammer_report", absent=("hammer",), sets=("hammer",)),
                step("bandage", requires=("redrum",), absent=("bandage",),
                     sets=("bandage",), choreography="bandage"),
                step("room_hammer_after_title", requires=("finals",)),
                step("room_hammer_after_redrum", requires=("redrum",)),
                step("room_hammer_before_baptism", absent=("baptism",)),
                step("dblock_hammer_before"),
            )),
            Action("Arena schedule", "schedule", (
                step("room_schedule_after", requires=("finals",)),
                step("room_schedule_before"),
            )),
            Action("Suzarn", "suzarn", (
                step("room_suzarn_after_baptism", requires=("baptism",), absent=("murders",)),
                step("room_suzarn_before", absent=("murders",)),
            )),
            Action("Stairs to Latina's Bar", "exit", (
                step("room_exit_before", absent=("hammer",)),
                step(target="bar", entry=1),
            )),
        ),
        "bedroom": (
            Action("Bed", "bed", (
                step("room_bed_after", requires=("title",)),
                step("room_bed_injured", requires=("redrum",)),
                step("room_bed_before"),
            )),
        ),
        "intake": (),
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
            Action("Worker", "worker", (
                step("dblock_worker_after_redrum", requires=("redrum",)),
                step("dblock_worker_missing", requires=("defense",)),
                step("dblock_worker_before"),
            )),
            Action("Battler", "battler", (
                step("dblock_battler_after_redrum", requires=("redrum",)),
                step("dblock_battler_missing", requires=("defense",)),
                step("dblock_battler_before"),
            )),
            Action("Prisoner", "prisoner", (
                step("title_prisoner", requires=("finals",)),
                step("dblock_prisoner_before", "pardon_question"),
            )),
            Action("Fei and Citan", "fei", (
                step("investigation_request", requires=("murders",),
                     absent=("investigation",), sets=("investigation",), target="commons"),
                step("title_fei", requires=("finals",)),
                step("sewer_after_redrum", requires=("redrum",)),
                step("fei_after_investigation", requires=("investigation",)),
                step("fei_before_investigation", requires=("baptism",)),
            )),
            Action("Clerk", "official", (
                step("title_clerk", requires=("finals",), absent=("title",),
                     sets=("title",)),
                step("clerk_after_title", requires=("title",)),
                step("clerk_waiting", requires=("defense",)),
                step("clerk_schedule_before"),
            )),
            Action("Yard", "yard_exit", (
                step(target="baptism", absent=("baptism",)),
                step(target="prep"),
            )),
            Action("D Block west street door", "room_exit", (step(target="street", entry=2),)),
            Action("D Block east street door", "east_exit", (step(target="street", entry=1),)),
            Action("Sewer entrance", "sewer_exit", (
                step(target="sewer_entry", requires=("investigation",), absent=("redrum",)),
                step("sewer_after_redrum", requires=("redrum",)),
                step("murders_report", requires=("defense",), absent=("murders",),
                     sets=("murders",)),
                step("room_schedule_before"),
            )),
            Action("Citan", "citan", (
                step("citan_after_title", requires=("baptism", "finals")),
                step("citan_after_redrum", requires=("baptism", "redrum")),
                step("citan_after_investigation", requires=("baptism", "investigation")),
                step("citan_before_investigation", requires=("baptism",)),
            )),
        ),
        "baptism": (Action("Return to D Block", "exit", (step(target="commons"),)),),
        "prep": (
            Action("Stier", "stier", (
                step("prep_stier", "defense_before", absent=("defense",),
                     battle=6, sets=("defense",)),
                step("finals_before", requires=("bandage",), absent=("finals",), target="arena"),
                step("league_return", requires=("title",), absent=("crash",), target="arena"),
                step("prep_hammer_after_title", requires=("finals",)),
                step("prep_hammer_injured", requires=("redrum",), absent=("bandage",)),
                step("prep_hammer_waiting", requires=("defense",)),
            )),
            Action("D Block", "exit", (step(target="commons"),)),
        ),
        "sewer_entry": (
            Action("Slime", "slime", (step("sewer_slime", sets=("evidence",)),)),
            Action("Message", "message", (step("sewer_message"),)),
            Action("Waterways", "forward", (step(target="sewer_hub"),)),
            Action("D Block", "exit", (step(target="commons"),)),
        ),
        "sewer_hub": (
            Action("Gramps", "gramps", (step("sewer_gramps"),)),
            Action("Bell", "bell", (step("sewer_bell", sets=("bell",)),)),
            Action("Treatment gate", "forward", (
                step(target="sewer_drain", requires=("key", "evidence", "bell")),
                step("treatment_gate_locked"),
            )),
            Action("Maintenance passage", "key_exit", (step(target="sewer_key"),)),
            Action("Entrance passage", "exit", (step(target="sewer_entry"),)),
        ),
        "sewer_key": (
            Action("Burnt odor", "burnt", (step("sewer_burnt"),)),
            Action("Jammed rat remover", "key", (step("sewer_key", sets=("key",)),)),
            Action("Waterways", "exit", (step(target="sewer_hub"),)),
        ),
        "sewer_drain": (
            Action("Treatment drain", "drain", (
                step("sewer_drain", "redrum_before", requires=("key", "evidence", "bell"),
                     absent=("redrum",), battle=15, sets=("redrum",), target="main"),
                step("sewer_drain"),
            )),
            Action("Waterways", "exit", (step(target="sewer_hub"),)),
        ),
        "arena": (),
        "central": (
            Action("Central District passage", "exit", (
                step(requires=("crash",),
                     sets=("flight",), choreography="flight", complete=True),
            )),
        ),
    }
    return table[room]


def load_dialogue() -> dict[str, tuple[str, ...]]:
    doc = json.loads((core.CONTENT_ROOT / "chapter_02_expansion.json").read_text(encoding="utf-8"))
    if doc.get("format") != "xenogears-rico-chapter-two-expansion-v1":
        raise core.RicoArcBuildError("Unknown Chapter 2 expansion document")
    result = {key: tuple(blocks) for key, blocks in doc["scenes"].items()}
    for key, blocks in result.items():
        if not blocks or any(not text.endswith("<Close>") for text in blocks):
            raise core.RicoArcBuildError(f"Incomplete Chapter 2 scene: {key}")
    return result


def commit(*names: str) -> bytes:
    return b"".join(core.atel.set_var_bit(STATE, BITS[name]) for name in names) + core._restore_chapter_two_state()


def party_for(room: str) -> tuple[int, ...]:
    if room == "intake":
        return (0,)
    if room in ("arena", "baptism"):
        return (5, 0)
    if room == "commons":
        return (5, 0, 2)
    return (5, 0, 2) if room.startswith("sewer_") else (5,)


def travel(room: str, fields: Mapping[str, int], entry: int = 0) -> bytes:
    # State is authoritative in persistent storage, including after a battle.
    from modules.rico.chapter_two_scenes import unmount_before_travel
    return (core._chapter_two_transition_out() + core._restore_chapter_two_state()
            + unmount_before_travel() + core._party_setup(party_for(room))
            + core._change_field(fields[room], entry) + b"\x5B")


def emit_travel(routine, room, fields, entry=0) -> None:
    routine.emit(core._wait_for_pad_release(core.PAD_MASK_CROSS, routine.pc))
    routine.emit(travel(room, fields, entry))


def emit_conditions(routine, branch: Step, skip: str) -> None:
    for name in branch.requires:
        routine.jump_if_bit_clear(STATE, 1 << BITS[name], skip)
    for index, name in enumerate(branch.absent):
        clear = f"{skip}_clear_{index}"
        routine.jump_if_bit_clear(STATE, 1 << BITS[name], clear)
        routine.jump(skip)
        routine.label(clear)


def validate_graph() -> dict:
    """Explore real branch conditions, including revisits and optional clues."""
    rooms = ("main", "bedroom", "intake", "bar", "street", "commons", "baptism", "prep",
             "sewer_entry", "sewer_hub", "sewer_key", "sewer_drain", "arena", "central")
    scenes = load_dialogue()
    used = set()
    for room in rooms:
        for action in actions_for(room):
            for branch in action.steps:
                used.update(branch.scenes)
                if branch.target is not None and branch.target not in rooms:
                    raise core.RicoArcBuildError(f"Unknown destination {branch.target}")
                for name in (*branch.requires, *branch.absent, *branch.sets):
                    if name not in BITS:
                        raise core.RicoArcBuildError(f"Unknown Chapter 2 flag {name}")
    missing = used - scenes.keys()
    if missing:
        raise core.RicoArcBuildError(f"Missing Chapter 2 dialogue: {sorted(missing)}")
    return {"rooms": len(rooms), "authored_scenes": len(scenes),
            "authored_blocks": sum(map(len, scenes.values())), "flags": dict(BITS)}


def _scene(routine, name: str, dialogue: Callable[[str], bytes], actors: Mapping[str, int], editor) -> None:
    from modules.rico import chapter_two_scenes as scenes
    from modules.rico import chapter_two_opening as opening
    builders = {"baptism": scenes.build_baptism, "finals": scenes.build_finals,
                "crash": scenes.build_crash, "bandage": scenes.build_bandage,
                "flight": scenes.build_flight, "arrival_delivery": scenes.build_arrival_delivery,
                "room_introduction": opening.build_room_introduction}
    kwargs = {"base_pc": routine.pc, "dialogue": dialogue}
    if name == "arrival_delivery":
        kwargs.update(fei_entity=actors["fei"], doctor_entity=actors["doctor"], guard_entity=actors["guard"])
    else:
        kwargs["rico_entity"] = actors["rico"]
    if name == "room_introduction":
        kwargs.update(suzarn_entity=actors["suzarn"], hammer_entity=actors["hammer"])
    elif name == "bandage":
        kwargs["hammer_entity"] = actors["hammer"]
    elif name not in ("flight", "arrival_delivery"):
        kwargs["fei_entity"] = actors["fei"]
    if name == "crash":
        kwargs["first_script"] = 16
    built = builders[name](**kwargs)
    if hasattr(editor, "walkmesh"):
        scenes.validate_geometry(built, editor.walkmesh)
    editor.extend(built.actor_routines)
    routine.emit(built.body)


def _battle(routine, configuration: int, room: str, dialogue) -> None:
    if configuration == 6:
        before, after = core._gear_battle_stage(solo_rico=True, chapter_party=(5,))
    elif configuration == 15:
        before = core._party_setup((5, 0, 2)) + b"".join(
            b"\xFE\x42" + core._immediate(slot) for slot in range(3))
        after = b""
    else:
        raise core.RicoArcBuildError(f"Unreviewed Chapter 2 battle {configuration}")
    routine.emit(before + core._wait(15) + core._play_music(0x14)
                 + core.mass_driver._fixed_battle(configuration) + b"\xFE\x7F" + after)
    routine.emit(core._play_music(room_music(room)))
    if configuration == 6:
        routine.emit(dialogue("defense_after") + dialogue("fei_explosion_report"))
    else:
        routine.emit(dialogue("redrum_after") + dialogue("injury_exit"))


def _completion(routine, dialogue, return_hub: int, next_ids: tuple[int, ...], choice_id: int) -> None:
    routine.emit(core._choice_dialog(choice_id, flags=1) + b"\xA9\x12\x9C")
    routine.jump_if_not_equal(core.MENU_SELECTION_VARIABLE, 1, "finish_hub")
    routine.emit(core._prelaunch_exposition(next_ids, routine_pc=routine.pc, flags=1))
    routine.emit(core._chapter_launch_body(3, core._chapter_fields_for_hub(return_hub)[3]))
    routine.label("finish_hub")
    routine.jump_if_not_equal(core.MENU_SELECTION_VARIABLE, 2, "finish_stay")
    routine.emit(core._hub_launch_body(return_hub))
    routine.label("finish_stay")


def _action_body(action: Action, *, base_pc: int, room: str, fields, dialogue,
                 actors, editor, return_hub, next_ids, choice_id) -> bytes:
    routine = core.mass_driver._RoutineBuilder(base_pc)
    routine.emit(core._playable_action_prefix(routine.pc))
    for index, branch in enumerate(action.steps):
        skip = f"branch_{index}_skip"
        emit_conditions(routine, branch, skip)
        # Choreographed scenes own their dialogue order and meaningful pauses.
        if branch.choreography in ("bandage",):
            _scene(routine, branch.choreography, dialogue, actors, editor)
        else:
            for key in branch.scenes:
                if key == "treatment_gate_locked":
                    for clue_index, flag in enumerate(("key", "evidence", "bell")):
                        routine.jump_if_bit_clear(STATE, 1 << BITS[flag], f"gate_hint_{clue_index}")
                    routine.jump("gate_hint_done")
                    for clue_index in range(3):
                        routine.label(f"gate_hint_{clue_index}")
                        routine.emit(dialogue(key, clue_index, clue_index + 1))
                        routine.jump("gate_hint_done")
                    routine.label("gate_hint_done")
                else:
                    routine.emit(dialogue(key))
            if branch.choreography:
                _scene(routine, branch.choreography, dialogue, actors, editor)
        if branch.battle is not None:
            _battle(routine, branch.battle, room, dialogue)
        if branch.sets:
            routine.emit(commit(*branch.sets))
        if branch.complete:
            _completion(routine, dialogue, return_hub, next_ids, choice_id)
        if branch.target:
            emit_travel(routine, branch.target, fields, branch.entry)
        routine.jump("action_done")
        routine.label(skip)
    routine.label("action_done")
    routine.emit(core._playable_action_finish(routine.pc))
    return routine.finish()


def _automatic_body(room: str, *, base_pc: int, fields, dialogue, actors, editor) -> bytes:
    routine = core.mass_driver._RoutineBuilder(base_pc)
    # The reception is a locked cutaway from its first frame. Never expose a
    # movable Fei during the initial load delay.
    if room == "intake":
        routine.emit(b"\x33\xFE\x54")
    elif room != "main":
        routine.emit(core._wait(30))
    if room == "main":
        routine.jump_if_bit_clear(STATE, 1 << BITS["room_intro"], "room_intro")
        routine.emit(b"\x5B")
        routine.label("room_intro")
        routine.emit(core._playable_action_prefix(routine.pc))
        routine.emit(core._wait(30))
        # Native saves from the former room-first opening stay in Rico's
        # room. Do not send an already loaded player back into the cutaway.
        # Choreography owns the camera and all three actors. Complete the
        # exchange before releasing control; Suzarn remains available to talk.
        _scene(routine, "room_introduction", dialogue, actors, editor)
        routine.emit(commit("delivery", "room_intro", "hammer"))
    elif room == "intake":
        routine.jump_if_bit_clear(STATE, 1 << BITS["delivery"], "receive_fei")
        emit_travel(routine, "main", fields)
        routine.label("receive_fei")
        routine.emit(core._playable_action_prefix(routine.pc))
        _scene(routine, "arrival_delivery", dialogue, actors, editor)
        routine.emit(commit("delivery"))
        emit_travel(routine, "main", fields)
    elif room == "baptism":
        routine.jump_if_bit_clear(STATE, 1 << BITS["baptism"], "perform")
        routine.emit(b"\x5B")
        routine.label("perform")
        routine.emit(core._playable_action_prefix(routine.pc))
        _scene(routine, "baptism", dialogue, actors, editor)
        routine.emit(commit("baptism"))
    elif room == "arena":
        routine.emit(core._playable_action_prefix(routine.pc))
        routine.jump_if_bit_clear(STATE, 1 << BITS["finals"], "finals")
        routine.jump_if_bit_clear(STATE, 1 << BITS["title"], "return_block")
        _scene(routine, "crash", dialogue, actors, editor)
        routine.emit(commit("crash"))
        emit_travel(routine, "central", fields)
        routine.label("finals")
        _scene(routine, "finals", dialogue, actors, editor)
        routine.emit(commit("finals"))
        routine.label("return_block")
        emit_travel(routine, "commons", fields)
    elif room == "sewer_entry":
        routine.emit(core._playable_action_prefix(routine.pc) + dialogue("sewer_entry"))
    elif room == "central":
        routine.emit(core._playable_action_prefix(routine.pc) + dialogue("central_approach"))
    else:
        return b"\x5B"
    # Finish deliberately uses 5B instead of STOP: this update runs once.
    routine.emit(core._playable_action_finish(routine.pc)[:-1] + b"\x5B")
    return routine.finish()


def _main_stair_exit_body(base_pc: int, fields) -> bytes:
    """Restore field218's real walk-through trigger, with anthology routing."""
    routine = core.mass_driver._RoutineBuilder(base_pc)
    for flag in ("room_intro", "hammer"):
        routine.jump_if_bit_clear(STATE, 1 << BITS[flag], "idle")
    departing = travel("bar", fields, 1)
    # Native CB00 tests trigger0 (including its Y plane). Outside it, STOP
    # yields until the next UPDATE. On contact, travel immediately locks and
    # fades; no hidden Cross hotspot or unbounded movement owns the exit.
    routine.emit(b"\xCB\x00" + core._u16(routine.pc + 4 + len(departing)) + departing)
    routine.label("idle")
    routine.emit(b"\x00")
    return routine.finish()


def _pack(source: bytes, components: list[bytes], header: bytes) -> bytes:
    parsed = core.parse_field(source)
    changed = tuple(index for index, part in enumerate(parsed.parts) if part.data != components[index])
    result = core.build_field_preserving(source, components, changed, compact_changed=True,
                                         replacement_header=header)
    checked = core.parse_field(result)
    if tuple(part.data for part in checked.parts) != tuple(components) or checked.header[0x18C:] != header[0x18C:]:
        raise core.RicoArcBuildError("Expanded Chapter 2 field failed packed round-trip")
    return result


def _position_init(bank: int, x: int, z: int, palette: int | None = None) -> bytes:
    load = (b"\x0B" + core._immediate(bank) if palette is None else
            b"\xFE\x15" + core._immediate(bank) + core._immediate(palette))
    return (load + b"\x19" + core._s16(x) + core._s16(z)
            + b"\xC0\x1A\x00" + core.PLAYABLE_ACTOR_SOLID_FLAGS + b"\x00")


def build_room(room: str, source: bytes, *, fields: Mapping[str, int], chapter,
               next_chapter, return_hub: int, spec: dict, inherited=False,
               interludes=False) -> bytes:
    """Compile one isolated donor, installing only authored reachable routines."""
    from modules.rico import chapter_two_resources as resources
    from modules.rico import chapter_two_scenes as scenes
    from modules.rico import chapter_two_opening as opening
    from modules.rico import chapter_two as legacy
    from modules.rico import chapter_two_interludes as gaps
    policy = gaps if interludes else legacy
    parsed = core.parse_field(source)
    components = [part.data for part in parsed.parts]
    editor = core.AtelScript(components[core.SCRIPT_INDEX])
    old_count = editor.entity_count
    original_init = {entity: editor.get_script_pointer(entity, 0) for entity in range(old_count)}
    original_code = editor.bytecode
    original_door = None
    if room in ("main", "bedroom"):
        original_door = editor.get_script_pointer(2, 2)
    registered = core._registered_character_entities(editor) if inherited else {}
    party_entities = {character: entity for character, entity in registered.items() if character in (5, 0, 2)}
    needed = [character for character in (5, 0, 2) if character not in party_entities]
    actions = policy.actions_for(room)
    records = [core.mass_driver._field_actor_record(0x01E0, 0, 0, 0)
               for _ in range(len(needed) + len(actions))]
    header = core._insert_dynamic_actor_records(parsed.header, old_entity_count=old_count,
                                                records_to_insert=records)
    editor = core.AtelScript(core.mass_driver._extend_atel_entity_table(editor.to_bytes(), old_count + len(records)))
    for offset, character in enumerate(needed):
        party_entities[character] = old_count + offset
    stop = editor.append_raw_routine(b"\x00")
    inert = editor.append_raw_routine(core.INERT_HIDDEN_INIT)
    silent = editor.append_raw_routine(b"\x5B")
    for entity in range(editor.entity_count):
        for slot in range(32):
            editor.set_script_pointer(entity, slot, stop)
        editor.set_script_pointer(entity, 0, inert)
        editor.set_script_pointer(entity, 1, silent)
    if inherited:
        # Reuse the old room's audited prop initialization, but retire all its
        # objective controllers and all its legacy story actions.
        native_count = 28 if room == "main" else 4
        for entity in range(min(native_count, old_count)):
            editor.set_script_pointer(entity, 0, original_init[entity])
        if room == "bedroom":
            editor.set_script_pointer(3, 0, inert)
        editor.set_script_pointer(2, 2, original_door)
        if room == "main":
            # Movement is awaited by the opening director, never a competing
            # UPDATE that can strand Hammer on a tread during conversation.
            editor.append_and_repoint(core.CHAPTER_TWO_HAMMER_ENTITY, 0,
                opening.hammer_init())
    else:
        for entity, pc in original_init.items():
            # Retain only the exact audited door-angle initializer here.
            # Ordinary header models use BC and are restored below.
            if original_code[pc:pc + 2] == b"\x46\x00":
                editor.append_and_repoint(entity, 0, b"\x46\x00")
        for entity in spec.get("safe_static_models", ()):
            # OP23 hides header models as well as sprites. Preserve these
            # native transforms and visibility, with every retail event dead.
            editor.append_and_repoint(entity, 0, b"\xBC\x2A\x00")
    if interludes:
        # The inherited anthology room contains dormant registrations for
        # the full playable cast, not only Fei and Citan. None belongs in a
        # private Rico scene; retain only his actual player registration.
        for character, entity in registered.items():
            if character != 5:
                editor.set_script_pointer(entity, 0, inert)
                editor.set_script_pointer(entity, 1, silent)
    entry_x, entry_z, _ = spec["entry"]
    actors = {"rico": party_entities[5], "fei": party_entities[0], "citan": party_entities[2]}
    if room == "main":
        actors["hammer"] = core.CHAPTER_TWO_HAMMER_ENTITY
    for character, entity in party_entities.items():
        visible = character in policy.party_for(room)
        if not visible:
            # Inherited room INITs were restored above. Retire unneeded
            # party actors explicitly even if they occupied a native slot.
            editor.set_script_pointer(entity, 0, inert)
            editor.set_script_pointer(entity, 1, silent)
            continue
        if (inherited or spec.get("native_entries")) and character == 5:
            # The retained field-entry table and native player registration
            # place Rico just inside the real door; do not teleport to (0,0).
            editor.append_and_repoint(entity, 0, core._normalized_party_init(5))
            editor.append_and_repoint(entity, 1, b"\xA7\x00")
            continue
        position = spec.get("cast", {}).get({5: "rico", 0: "fei", 2: "citan"}[character])
        if position is None:
            position = (entry_x, entry_z) if character == 5 else (entry_x, entry_z)
        header = core._place_actor_record(header, entity, *position[:2])
        init_body = (scenes.arena_actor_init(character, position[:2]) if room == "arena" else
                     core._normalized_party_init(character, position=position[:2]))
        if not interludes and room == "commons" and character in (0, 2):
            init = core.mass_driver._RoutineBuilder(editor.bytecode_size)
            init.jump_if_bit_clear(STATE, 1 << BITS["baptism"], "hide")
            init.emit(init_body)
            init.label("hide")
            init.emit(core.INERT_HIDDEN_INIT)
            init_body = init.finish()
        editor.append_and_repoint(entity, 0, init_body)
        if room != "intake" and character in policy.party_for(room) and not (room == "commons" and character != 5):
            editor.append_and_repoint(entity, 1, b"\xA7\x00")
    for landmark, npc in spec.get("npcs", {}).items():
        entity, bank = npc["entity"], npc["bank"]
        x, z, _ = spec["landmarks"][landmark]
        if entity in party_entities.values() or not 0 < entity < old_count:
            raise core.RicoArcBuildError(f"{room} NPC {landmark} collides with a party actor")
        header = core._place_actor_record(header, entity, x, z)
        npc_body = _position_init(bank, x, z, npc.get("palette"))
        if room == "sewer_hub" and landmark == "gramps":
            # Retail field240 e42's RGB tint and nonuniform scale identify
            # the same green, squat Gramps shown in his dialogue portrait.
            # Keep the authored location and interaction flags after loading.
            if not npc_body.startswith(b"\x0B\x00\x80"):
                raise core.RicoArcBuildError("Gramps no longer loads native actor bank0")
            npc_body = (npc_body[:3] + bytes.fromhex("FE5F031E8064801E80FE08889300880090")
                        + npc_body[3:])
        if room == "main" and landmark == "suzarn":
            # Suzarn stays through the opening. The later disappearance is
            # story-driven: retail D Block identifies Suzarn as victim five.
            init = core.mass_driver._RoutineBuilder(editor.bytecode_size)
            init.jump_if_bit_clear(STATE, 1 << (gaps.npc_visible_until("suzarn") if interludes else BITS["murders"]), "alive")
            init.emit(core.INERT_HIDDEN_INIT)
            init.label("alive")
            init.emit(opening.npc_init(bank, (x, z)))
            npc_body = init.finish()
        elif interludes and room == "commons" and landmark == "battler":
            # The optional resident is anonymous throughout these intervals.
            # Bank1 is Leonardo; retaining it after his death would be wrong.
            npc_body = _position_init(0, x, z)
        elif room == "commons" and landmark == "battler":
            init = core.mass_driver._RoutineBuilder(editor.bytecode_size)
            init.jump_if_bit_clear(STATE, 1 << BITS["defense"], "leonardo")
            init.emit(_position_init(0, x, z))
            init.label("leonardo")
            init.emit(npc_body)
            npc_body = init.finish()
        editor.append_and_repoint(entity, 0, npc_body)
        actors[landmark] = entity
    if interludes and room == "main":
        init = core.mass_driver._RoutineBuilder(editor.bytecode_size)
        init.jump_if_bit_clear(STATE, 1 << gaps.npc_visible_until("hammer"), "present")
        init.emit(core.INERT_HIDDEN_INIT)
        init.label("present")
        init.emit(opening.hammer_init())
        editor.append_and_repoint(actors["hammer"], 0, init.finish())
    music = room_music(room, chapter.music)
    director = core.mass_driver._RoutineBuilder(editor.bytecode_size)
    director.emit(core._chapter_two_director(music)[:-1])
    if room == "intake":
        director.emit(b"\x33\xFE\x54")
        # Slot one holds the shot black independently of the engine's slot
        # zero field fade, until the cutaway has positioned its cast/camera.
        # Init scripts do not wait for rendered frames.
        director.emit(core.mass_driver._facility_video_screen_fade_body(0xFF, 1)[:-3])
    elif room == "main" and interludes:
        director.emit(b"\x33\xFE\x54")
        director.emit(core.mass_driver._facility_video_screen_fade_body(0xFF, 1)[:-3])
    elif room == "main":
        director.jump_if_bit_clear(STATE, 1 << BITS["room_intro"], "lock_intro")
        director.jump("intro_ready")
        director.label("lock_intro")
        director.emit(b"\x33\xFE\x54")
        director.emit(core.mass_driver._facility_video_screen_fade_body(0xFF, 1)[:-3])
        director.label("intro_ready")
    if room == "commons" and not interludes:
        # Citan is already beside Fei for the existing post-Baptism lines.
        # The investigation flag still gates their entry into the sewers.
        director.jump_if_bit_clear(STATE, 1 << BITS["baptism"], "without_citan")
        director.emit(core._party_setup((5, 0, 2)))
        director.jump("party_ready")
        director.label("without_citan")
        director.emit(core._party_setup((5, 0)))
        director.label("party_ready")
    else:
        director.emit(core._party_setup(policy.party_for(room)))
    if room == "arena":
        director.emit(scenes.arena_director_prefix())
    director.emit(b"\x00")
    director_body = (gaps.director_body(room, music, editor.bytecode_size)
                     if interludes else director.finish())
    editor.append_and_repoint(0, 0, director_body)

    texts = policy.load_dialogue()
    flattened: list[str] = []
    scene_ids: dict[str, tuple[int, ...]] = {}
    for key, blocks in texts.items():
        scene_ids[key] = tuple(range(len(flattened), len(flattened) + len(blocks)))
        flattened.extend(blocks)
    next_blocks = () if interludes else core._chapter_selection_exposition(next_chapter)
    next_ids = tuple(range(len(flattened), len(flattened) + len(next_blocks)))
    flattened.extend(next_blocks)
    choice_id = len(flattened)
    flattened.append(gaps.choice_text if interludes else core.PLAYABLE_NEXT_OR_HUB_CHOICE)
    from modules.rico.chapter_two_ambient import load_conversations
    ambient = load_conversations(room)
    for conversation in ambient.values():
        if conversation.key in scene_ids:
            raise core.RicoArcBuildError("Ambient conversation collides with a Chapter2 scene")
        scene_ids[conversation.key] = tuple(range(len(flattened), len(flattened) + len(conversation.blocks)))
        flattened.extend(conversation.blocks)
    # Expansion blocks are sentence-checked independently. Successor heading
    # and native choice rows intentionally are not prose sentences.
    components[core.DIALOGUE_INDEX] = core._dialogue_data(flattened)
    def dialogue(key: str, start: int = 0, stop: int | None = None) -> bytes:
        # Native WAIT_DIALOG aborts ordinary dialogue owned by a hidden
        # carrier. Both the automatic director and object/NPC hotspots own
        # these routines; bit 0 preserves the full exchange, state commit,
        # and final control unlock for either activation path.
        ids = scene_ids[key][start:stop]
        if interludes:
            # Narration and anonymous replies must not inherit the previous
            # named speaker's face. The presentation pass sets named faces.
            return b"".join(b"\xFE\x0D\xFC\x80" + core._dialogue_sequence((index,), flags=1)
                            for index in ids)
        return core._dialogue_sequence(ids, flags=1)

    # All inherited return-door bytecode contains no dialogue operands and
    # synchronizes LOCAL from STATE before it can copy LOCAL back out.
    for offset, action in enumerate(actions):
        entity = old_count + len(needed) + offset
        if action.landmark in spec.get("native_actions", {}):
            # Native doors own collision/open/walk behavior. Keep this
            # reserved carrier inert rather than creating a second trigger.
            continue
        x, z, triangle = spec["landmarks"][action.landmark]
        mesh = core._walkmesh_layer(components[1], 0)
        if not 0 <= triangle < len(mesh) or not core._point_inside_triangle((x, z), mesh[triangle]):
            raise core.RicoArcBuildError(f"{room}/{action.landmark} is outside its audited walkmesh")
        header = core._place_actor_record(header, entity, x, z)
        half_extent = 12 if room == "commons" and action.landmark in ("worker", "battler") else 18
        controller_init = core._playable_controller_init(
            x, z, half_width=half_extent, half_depth=half_extent, requires_facing=False,
            initially_disabled=(room == "commons" and action.landmark in ("fei", "citan")))
        if room == "main" and (action.landmark == "suzarn" or (interludes and action.landmark == "hammer")):
            init = core.mass_driver._RoutineBuilder(editor.bytecode_size)
            init.jump_if_bit_clear(STATE, 1 << (gaps.npc_visible_until(action.landmark) if interludes else BITS["murders"]), "alive")
            init.emit(core.INERT_HIDDEN_INIT)
            init.label("alive")
            init.emit(controller_init)
            controller_init = init.finish()
        editor.append_and_repoint(entity, 0, controller_init)
        if room == "commons" and action.landmark in ("fei", "citan"):
            editor.append_and_repoint(entity, 1, core._playable_controller_activation_gate(
                editor.bytecode_size, (BITS["baptism"],), x, z))
        pending = ActorRoutines(components[1])
        action_pc = editor.bytecode_size
        body = policy._action_body(action, base_pc=action_pc, room=room, fields=fields,
                            dialogue=dialogue, actors=actors, editor=pending,
                            return_hub=return_hub, next_ids=next_ids, choice_id=choice_id)
        installed = editor.append_and_repoint(entity, 2, body)
        if installed != action_pc:
            raise core.RicoArcBuildError("Chapter 2 action PC changed during assembly")
        for actor in pending:
            editor.append_and_repoint(actor.entity, actor.script_index, actor.body)
        if action.landmark in actors and action.landmark != "rico":
            bound = actors[action.landmark]
            editor.set_script_pointer(bound, 2, installed)
    pending = ActorRoutines(components[1])
    auto_pc = editor.bytecode_size
    auto_body = policy._automatic_body(room, base_pc=auto_pc, fields=fields, dialogue=dialogue,
                                actors=actors, editor=pending)
    editor.append_and_repoint(0, 1, auto_body)
    for actor in pending:
        editor.append_and_repoint(actor.entity, actor.script_index, actor.body)
    if room == "main":
        expected_trigger = bytes.fromhex("4A003E00CCFF6D003E00CCFF6D003E00F8FF4A003E00F8FF")
        if components[8] != expected_trigger:
            raise core.RicoArcBuildError("Champion room's native stair trigger changed")
        editor.append_and_repoint(3, 0, b"\xBC\x2A\x00")
        editor.append_and_repoint(3, 1, policy._main_stair_exit_body(editor.bytecode_size, fields))
    if room in ("bar", "street", "commons"):
        from modules.rico.chapter_two_geography import (
            install_routes, install_resident_interactions, BAR_STAIR_TRIGGER,
        )
        if room == "bar" and components[8][:24] != BAR_STAIR_TRIGGER:
            raise core.RicoArcBuildError("Latina's Bar native stair trigger changed")
        install_routes(room, editor, fields, travel_body=policy.travel)
        install_resident_interactions(room, editor, dialogue, ambient)
    encounter_source = components[core.mass_driver.ENCOUNTER_INDEX]
    if len(encounter_source) not in (0, core.ENCOUNTER_COMPONENT_SIZE):
        raise core.RicoArcBuildError(f"{room} has an unexpected encounter component length")
    encounters = bytearray(encounter_source or bytes(core.ENCOUNTER_COMPONENT_SIZE))
    encounters[core.WEIGHTS_OFFSET:core.WEIGHTS_OFFSET + core.FORMATION_COUNT] = bytes(core.FORMATION_COUNT)
    if room == "prep":
        encounters[6 * core.FORMATION_SIZE + 1] |= 0x80
    if room == "sewer_drain":
        encounters[15 * core.FORMATION_SIZE:16 * core.FORMATION_SIZE] = resources.REDRUM_FORMATION
    components[core.mass_driver.ENCOUNTER_INDEX] = bytes(encounters)
    components[core.SCRIPT_INDEX] = editor.to_bytes()
    return _pack(source, components, header)


def expand_replacements(disc1, replacements, chapters, bedroom_fields, *, interludes=True) -> dict:
    from modules.rico import chapter_two_resources as resources
    from modules.rico import chapter_two_scenes as scenes
    from modules.rico import chapter_two_opening as opening
    from modules.rico.chapter_two_guard import (
        install_intake_guard, install_intake_guard_graphics, GUARD_DONOR_FIELD,
    )
    from modules.rico.chapter_two_clerk import (
        install_commons_clerk, install_commons_clerk_graphics, RECEPTIONIST_DONOR_FIELD,
    )
    from modules.rico import chapter_two_interludes as gaps
    (gaps.validate_graph if interludes else validate_graph)()
    resources.validate_allocations(disc1)
    main_spec = {"entry": (-125, 134, 38), "landmarks": {
        "hammer": opening.MAIN_HAMMER, "schedule": (115, -187, 62), "exit": opening.HAMMER_ENTRANCE,
        "suzarn": opening.MAIN_SUZARN}, "npcs": {"suzarn": {"entity": 4, "bank": 0}}}
    bed_spec = {"entry": (0, 0, 0), "landmarks": {"bed": core.CHAPTER_TWO_BED_POSITION}}
    for disc in (1, 2):
        fields = {**resources.WORLD_FIELDS, "main": core.CHAPTER_FIELDS[disc][2],
                  "bedroom": bedroom_fields[disc]}
        if len(set(fields.values())) != len(fields):
            raise core.RicoArcBuildError(f"Disc {disc} Chapter 2 field allocation overlaps")
        existing = {item.canonical_id: item for item in replacements[disc]}
        overlap = {core._field_bundle_id(field) + offset for field in resources.WORLD_FIELDS.values()
                   for offset in (0, 1)} & existing.keys()
        if overlap:
            raise core.RicoArcBuildError(f"Chapter 2 world overwrites another field: {sorted(overlap)}")
        for room, spec in {"main": main_spec, "bedroom": bed_spec, **resources.ROOM_SPECS}.items():
            if interludes and room not in gaps.ACTIVE_ROOMS:
                continue
            canonical = core._field_bundle_id(fields[room])
            inherited = room in ("main", "bedroom")
            source = existing[canonical].data if inherited else disc1.canonical(core._field_bundle_id(spec["donor"]))
            if room == "prep":
                source = resources.install_prep_hammer(source, disc1.canonical(core._field_bundle_id(218)))
            elif room == "intake":
                source = install_intake_guard(source, disc1.canonical(core._field_bundle_id(GUARD_DONOR_FIELD)))
            elif room == "commons":
                source = install_commons_clerk(source, disc1.canonical(core._field_bundle_id(RECEPTIONIST_DONOR_FIELD)))
            data = build_room(room, source, fields=fields, chapter=chapters[2], next_chapter=chapters[3],
                              return_hub=core.HUB_FIELDS[disc], spec=spec, inherited=inherited,
                              interludes=interludes)
            existing[canonical] = core.Replacement(canonical, f"Chapter 2 The Champ: {room}", data)
            if not inherited:
                graphics = disc1.canonical(core._field_bundle_id(spec["donor"]) + 1)
                if room == "intake":
                    graphics = install_intake_guard_graphics(
                        graphics, disc1.canonical(core._field_bundle_id(GUARD_DONOR_FIELD)))
                elif room == "commons":
                    graphics = install_commons_clerk_graphics(
                        graphics, disc1.canonical(core._field_bundle_id(RECEPTIONIST_DONOR_FIELD) + 1))
                existing[canonical + 1] = core.Replacement(canonical + 1, f"Chapter 2 {room} native graphics",
                    graphics)
        dependencies = {} if interludes else resources.battle_resources(disc1)
        if not interludes:
            dependencies.update(scenes.scene_resources(disc1))
        for canonical, data in dependencies.items():
            if canonical in existing and existing[canonical].data != data:
                raise core.RicoArcBuildError(f"Chapter 2 dependency collision at {canonical}")
            existing[canonical] = core.Replacement(canonical, "Chapter 2 checked battle/cinematic dependency", data)
        replacements[disc] = list(existing.values())
    return replacements
