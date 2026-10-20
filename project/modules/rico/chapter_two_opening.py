"""The Champion's rooms: one visible Rico, Suzarn, and Hammer introduction.

The room assembler owns actor registration, the first-load black hold,
progress flags, and the final input unlock. Install the returned actor scripts
and body as one scene. Keep Hammer's old autonomous stair UPDATE retired;
this scene is his only movement owner during the introduction.
"""
from __future__ import annotations

from dataclasses import replace

from modules.rico import chapter_two_scenes as scenes


# Field218 layer0: all three conversation points are on the broad Y=0 room
# floor. The former Hammer hotspot(60,-49) is sloping stair triangle133.
MAIN_RICO = (38, -282, 68)
MAIN_SUZARN = (-10, -265, 67)
MAIN_HAMMER = (90, -245, 73)
CONVERSATION_SUZARN = (-6, -240, 67)
CONVERSATION_HAMMER = (55, -209, 68)
HAMMER_ENTRANCE = (92, -29, 19)
HAMMER_APPROACH = ((69, -52, 14), (-27, -151, 89), (-37, -159, 88))
HAMMER_ROOM_ROUTE = ((-27, -230, 65), CONVERSATION_HAMMER)
# OP20 bit0 maps to the native actor-collision bypass flag0x80; bits2/3
# retain the stationary NPC contract. Dialogue activation is independent.
# An immovable NPC must not become a barrier across this narrow room.
NPC_PASSABLE_FLAGS = b"\x20\x0D\x80"

# Native e19:s0 PC079E begins(92,-29); e19:s4 PC07C9 ends(-37,-159).
# The stair tread/top landing follow the same connected native stair path.
# Camera orientation comes from e8:s6 PC0517/0520, target(-69,76,-28),
# eye(793,-396,-344), translated to the upper room and brought closer.
ESTABLISHING_TARGET = (20, -160, -32)
ESTABLISHING_EYE = (796, -585, -316)
CONVERSATION_TARGET = (25, -245, -35)
CONVERSATION_EYE = (585, -552, -240)
MAX_WALK_STEPS = 120
# The later bandage scene in this same room owns slots24..28.
FIRST_SCRIPT = 16


def npc_init(bank: int, position: tuple[int, int], direction: int = 4) -> bytes:
    """Load one already supplied NPC bank at a persistent room-floor point."""
    if not 0 <= direction < 8:
        raise ValueError("Room NPC direction must be 0..7")
    return (b"\x0B" + scenes._word(bank) + b"\x19" + scenes._position(position)
            + b"\x1A\x00" + NPC_PASSABLE_FLAGS + b"\x5F" + bytes((direction,)) + b"\x00")


def hammer_init(position: tuple[int, int] = MAIN_HAMMER[:2]) -> bytes:
    """Initialize authentic local bank4; normal revisits keep Hammer upstairs."""
    return npc_init(4, position)


def build_room_introduction(
    base_pc: int, *, rico_entity: int, suzarn_entity: int, hammer_entity: int,
    dialogue: scenes.DialogueEmitter,
) -> scenes.SceneBuild:
    """Stage, introduce, and retain all three cast members in a bounded scene.

    Dialogue uses the established room_first and hammer_report keys. Hammer
    calls from the visible stair entrance; Rico invites him up before he
    climbs. Hammer clears the stairs before the report continues. Code never unlocks input,
    hides/deletes a cast member, or changes progression flags.
    """
    scene = scenes._Scene(base_pc, 218,
                          (rico_entity, suzarn_entity, hammer_entity), FIRST_SCRIPT, dialogue)
    staging = scene.actor(rico_entity, 0, "Rico on clear room floor",
                          scenes._stage(MAIN_RICO[:2], 4))
    staging += scene.actor(suzarn_entity, 0, "Suzarn remains beside Rico",
                           scenes._stage(CONVERSATION_SUZARN[:2], 0))
    staging += scene.actor(hammer_entity, 0, "Hammer at native stair entrance",
                           scenes._stage(HAMMER_ENTRANCE[:2], 6))
    scene.open(staging, ESTABLISHING_TARGET, ESTABLISHING_EYE,
               (rico_entity, suzarn_entity, hammer_entity))
    scene.body.extend(scenes._look(rico_entity, suzarn_entity)
                      + scenes._look(suzarn_entity, rico_entity))
    scene.say("room_first")

    # Call and invitation precede movement. The same wide shot contains the
    # entrance and upper room; the longer report waits for Hammer to arrive.
    scene.body.extend(scenes._look(rico_entity, hammer_entity)
                      + scenes._look(suzarn_entity, hammer_entity))
    scene.body.extend(scenes._look(hammer_entity, rico_entity) + scenes._wait(10))
    scene.say("hammer_report", 0, 2)
    scene.body.extend(scene.actor(hammer_entity, 1, "Hammer climbs visibly to landing",
        scenes._walk(*(point[:2] for point in HAMMER_APPROACH), max_steps=MAX_WALK_STEPS)))
    scene.paths.append(scenes.MotionPath(
        (HAMMER_ENTRANCE[:2], *(point[:2] for point in HAMMER_APPROACH))))
    scene.body.extend(scene.actor(hammer_entity, 2, "Hammer approaches into the room",
        scenes._walk(*(point[:2] for point in HAMMER_ROOM_ROUTE), max_steps=MAX_WALK_STEPS)))
    scene.paths.append(scenes.MotionPath(
        (HAMMER_APPROACH[-1][:2], *(point[:2] for point in HAMMER_ROOM_ROUTE))))
    scene.body.extend(scenes._look(hammer_entity, rico_entity)
                      + scenes._look(rico_entity, hammer_entity)
                      + scenes._look(suzarn_entity, hammer_entity)
                      + scenes._camera(CONVERSATION_TARGET, CONVERSATION_EYE, frames=24))
    scene.say("hammer_report", 2, 10)
    # Native Rico e13:s6 PC06EC uses 0E, then04. Return to the normal idle
    # explicitly so player walking after the conversation is unaffected.
    scene.body.extend(scene.actor(rico_entity, 1, "Rico considers the new prisoner",
        b"\x2C\x0E" + scenes._wait(15) + b"\x2C\x04" + scenes._wait(12)
        + b"\x2C\xFF\x00"))
    scene.body.extend(scenes._look(rico_entity, suzarn_entity)
                      + scenes._look(suzarn_entity, rico_entity))
    scene.say("hammer_report", 10, None)
    scene.body.extend(scenes._look(hammer_entity, rico_entity)
                      + scenes._look(rico_entity, hammer_entity) + scenes._wait(12))
    # Their final spoken decisions have a visible result: both step out of
    # Rico's path before control returns, rather than occupying the stair
    # junction until the player pushes or jumps through them.
    scene.body.extend(scene.actor(suzarn_entity, 1, "Suzarn steps clear of the stair approach",
        scenes._walk(MAIN_SUZARN[:2], max_steps=MAX_WALK_STEPS)))
    scene.body.extend(scene.actor(hammer_entity, 3, "Hammer steps aside after his report",
        scenes._walk(MAIN_HAMMER[:2], max_steps=MAX_WALK_STEPS)))
    scene.paths.extend((scenes.MotionPath((CONVERSATION_SUZARN[:2], MAIN_SUZARN[:2])),
                        scenes.MotionPath((CONVERSATION_HAMMER[:2], MAIN_HAMMER[:2]))))
    scene.body.extend(scenes._look(suzarn_entity, rico_entity)
                      + scenes._look(hammer_entity, rico_entity) + scenes._wait(8))
    built = scene.finish()
    # Generic scene completion restores a controllable actor's ordinary flags.
    # Park both NPCs away from the stair junction, retaining talk activation
    # while allowing Rico past them on first completion and every revisit.
    routines = tuple(replace(routine, body=NPC_PASSABLE_FLAGS + b"\x00")
                     if routine.entity in (suzarn_entity, hammer_entity)
                     and routine.script_index == FIRST_SCRIPT + 4 else routine
                     for routine in built.actor_routines)
    return replace(built, actor_routines=routines)
