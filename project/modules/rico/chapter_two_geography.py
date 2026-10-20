"""Retail Champion room -> Latina's Bar -> D Block street door contracts.

Field217 dialogue29 names Latina's Bar; dialogue30 names the separate Wildcat
in the civilian district. Its stairs lead to218/1 and its street door to196/5.
Only the physical doors and audited ambient actors are retained here. Retail
Fei story flags, party callbacks, dialogue and camera managers stay retired.
Resident conversations are authored separately for Rico, with no story writes.
"""
from modules.rico import build as core


# (owner, destination role, destination native entry, native door direction).
# 196 e29/e34 reach opposite ends of the same field211 dormitory corridor.
DOOR_ROUTES = {
    "bar": ((2, "street", 5, 0),),
    "street": ((31, "bar", 0, 1), (29, "commons", 0, 1), (34, "commons", 1, 1)),
    "commons": ((4, "street", 2, 0), (5, "street", 1, 0)),
}
BAR_STAIR_TRIGGER = bytes.fromhex("D90095FF9DFE080195FF9DFE080195FFCFFED90095FFCFFE")

# Exact native INITs. Their remaining retail script slots are never copied.
# Latina tends her counter; patrons keep their original seated animation2.
BAR_RESIDENT_INITS = {
    7: "0B018019D1FEC7FFC0F8000020185A0A1900200D8000",
    11: "FE1503800280197EFFC7FEC05F0200",
    12: "FE15048002801986FF21FFC05F0200",
    13: "FE150580018019FEFF0DFFC05F0100",
    14: "0B048019540025FFC05F0700",
    15: "FE1503800180198B01E7FFC05F0000",
    16: "FE1503800280193B019E00C05F0000",
    17: "FE1504800180198C012501C05F01200D8000",
    18: "FE15058002801972003001C05F0200",
    19: "0B04801971007E00C05F0400",
}
# Native OP1B retains the upper walkway layer for these street residents.
STREET_RESIDENT_INITS = {
    36: "FE15018002801B3AFFA80001C05F0300",
    37: "FE15018001801B56FD1A0401C000",
    39: "0B02801916FE61FCC000",
    51: "FE15018002801B3CFCF4FF01C05F0600",
}


def native_door_body(target: str, entry: int, direction: int, fields) -> bytes:
    """Keep OP47's retail door geometry, with anthology state restored.

    Do not pre-fade or use the generic OP98 transition: OP47 owns the native
    walk through this model, then loads the requested reciprocal entry.
    """
    from modules.rico.chapter_two_scenes import unmount_before_travel
    if direction not in (0, 1):
        raise core.RicoArcBuildError("Unreviewed Nortune door direction")
    return (core._restore_chapter_two_state() + unmount_before_travel()
            # The destination director sets its party before actor INITs.
            # Keep the current live Rico through OP47's physical traversal;
            # tearing down/reloading the party here would remove its walker.
            + b"\x15\xC4" + bytes((direction,)) + b"\x1F\x11\x47"
            + bytes((direction,)) + core._immediate(fields[target])
            + core._immediate(entry) + b"\x5B")


def install_routes(room: str, editor, fields, *, travel_body=None) -> None:
    """Install only these checked exits after every donor slot was cleared."""
    for entity, target, entry, direction in DOOR_ROUTES[room]:
        editor.append_and_repoint(entity, 0, b"\x46\x00")
        editor.append_and_repoint(entity, 2, native_door_body(target, entry, direction, fields))
        editor.append_and_repoint(entity, 4, b"\xC4" + bytes((direction,)) + b"\x00")
        editor.append_and_repoint(entity, 5, b"\xC5" + bytes((direction,)) + b"\x00")
    if room == "bar":
        if travel_body is None:
            from modules.rico.chapter_two import travel as travel_body
        editor.append_and_repoint(3, 0, b"\xBC\x2A\x00")
        departing = travel_body("main", fields, 1)
        pc = editor.bytecode_size
        editor.append_and_repoint(3, 1, b"\xCB\x00" + core._u16(pc + 4 + len(departing))
                                 + departing + b"\x00")
    residents = BAR_RESIDENT_INITS if room == "bar" else STREET_RESIDENT_INITS if room == "street" else {}
    for entity, native in residents.items():
        # Disable dialogue activation because their original ACTIONs refer
        # to Fei's campaign. The sprites, palettes and poses stay authentic.
        editor.append_and_repoint(entity, 0, bytes.fromhex(native)[:-1] + b"\x2A\x00")
        if room == "bar":
            pose = b"\x2C\x02" + (b"\x6F\x07" if entity in (11, 12) else b"")
            editor.append_and_repoint(entity, 1, pose + b"\x00")


def resident_action_body(base_pc: int, conversation, dialogue) -> bytes:
    """Talk without turning a seated sprite, moving Rico or changing progress."""
    routine = core.mass_driver._RoutineBuilder(base_pc)
    routine.emit(core._playable_action_prefix(routine.pc))
    for index in range(len(conversation.blocks)):
        # Anonymous records have no speaker label, so the presentation pass
        # can leave their F5 untouched. Clear explicitly before every block,
        # including the anonymous return after Rico has spoken. Named blocks
        # acquire their own portrait in the normal release presentation pass.
        routine.emit(b"\xFE\x0D\xFC\x80")
        routine.emit(dialogue(conversation.key, index, index + 1))
    routine.emit(b"\xFE\x0D\xFC\x80")
    routine.emit(core._playable_action_finish(routine.pc))
    return routine.finish()


def install_resident_interactions(room: str, editor, dialogue, conversations) -> None:
    """Enable only the fourteen retained residents after their donor reset."""
    residents = BAR_RESIDENT_INITS if room == "bar" else STREET_RESIDENT_INITS if room == "street" else {}
    if set(conversations) != set(residents):
        raise core.RicoArcBuildError(f"{room} ambient dialogue does not cover its visible native cast")
    for entity, conversation in conversations.items():
        # Exact native initialization enables native proximity interaction;
        # replacing our route-only 2A trailer does not alter the resident's
        # position, layer, palette, collision flags or seated UPDATE pose.
        editor.append_and_repoint(entity, 0, bytes.fromhex(residents[entity]))
        editor.append_and_repoint(entity, 2, resident_action_body(editor.bytecode_size, conversation, dialogue))
