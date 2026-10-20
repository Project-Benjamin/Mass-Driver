"""Finish the production-room controls on the checked campaign foundation.

Apply after the retained dialogue-layout pass and before music/final freezes.
No new actors, geometry, persistent flags, or battle resources are allocated.
The three two-bit selections share the existing field-local word 0x07D0.
Until committed at the forward exit they reset on leaving the room; completed
rooms use their existing persistent flag and expose read-only controls.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct

import modules.mass_driver.build as mass_driver
import modules.soylent_system.base as base
import modules.soylent_system.build as campaign
from shared.tools import atel_primitives as atel
from shared.tools.xgdialog import parse_dialogue
from shared.tools.xgscript import AtelScript


LOCAL_OPERAND = 0x07D0
STATE_OPERAND = 0x03FA
MENU_RESULT_OPERAND = 0x0014
REVIEW_INSTRUCTIONS = "Review instructions"


@dataclass(frozen=True)
class Puzzle:
    field: int
    names: tuple[str, str, str]
    choices: tuple[str, ...]
    correct: tuple[int, int, int]
    progress_bit: int
    instruction: str
    denial: str

    @property
    def solution(self) -> int:
        return sum(value << (2 * index) for index, value in enumerate(self.correct))


PUZZLES = {
    624: Puzzle(
        624,
        ("FEED A: LIVING TISSUE", "FEED B: NANOMACHINE MEDIUM", "FEED C: UNSTABLE MELD"),
        ("Stasis assay", "Reclamation drain", "Containment return"),
        (1, 2, 3),
        12,
        "STAGED FEED ROUTING\nKeep living tissue in\nstasis. Reclaim the medium.\nReturn Meld to containment.<New>"
        "Use the forward exit to\ncommit all three routes.\nUncommitted choices reset\nwhen you leave this room.<Close>",
        "ROUTING NOT SAFE\nTissue needs stasis. Medium\nneeds reclamation. Meld\nneeds containment return.<New>"
        "Set each feed, then use\nthe forward exit again.\nNo production change has\nbeen committed.<Close>",
    ),
    626: Puzzle(
        626,
        ("RING A: FUSION", "RING B: PATTERN", "RING C: CONTAINMENT"),
        ("OFF", "ON"),
        (1, 1, 2),
        13,
        "STAGED CORE SETTINGS\nStop fusion and pattern.\nKeep containment active\nto protect those inside.<New>"
        "Use the forward exit to\ncommit all three settings.\nUncommitted choices reset\nwhen you leave this room.<Close>",
        "CORE SETTINGS NOT SAFE\nFusion and pattern must\nbe OFF. Containment must\nremain ON.<New>"
        "Set each ring, then use\nthe forward exit again.\nNo core change has\nbeen committed.<Close>",
    ),
}


def _drain(routine: mass_driver._RoutineBuilder) -> None:
    routine.emit(mass_driver._wait_for_pad_release(mass_driver.PAD_MASK_CROSS, routine.pc))
    routine.emit(mass_driver._wait())


def _show(routine: mass_driver._RoutineBuilder, dialogue_id: int) -> None:
    routine.emit(b"\xF5" + atel.u16(dialogue_id) + b"\x01\x9C")
    _drain(routine)


def choice_action(
    *,
    puzzle: Puzzle,
    index: int,
    routine_pc: int,
    instruction_id: int,
    status_ids: tuple[int, ...],
    menu_id: int,
    result_ids: tuple[int, ...],
    solved_id: int,
) -> bytes:
    """Show current state first, with optional read-only help and explicit Leave."""

    if index not in range(3) or len(status_ids) != len(puzzle.choices) + 1 or len(result_ids) != len(puzzle.choices):
        raise campaign.SurfaceCampaignBuildError("Invalid production puzzle control")
    routine = mass_driver._RoutineBuilder(routine_pc)
    routine.emit(b"\x33\xFE\x54")
    _drain(routine)
    routine.jump_if_bit_clear(STATE_OPERAND, 1 << puzzle.progress_bit, "editable")
    _show(routine, solved_id)
    routine.jump("finish")

    routine.label("editable")
    shift = 2 * index
    routine.jump_if_bit_clear(LOCAL_OPERAND, 2 << shift, "low_half")
    routine.jump_if_bit_clear(LOCAL_OPERAND, 1 << shift, "status_2")
    routine.jump("status_3" if len(puzzle.choices) == 3 else "status_0")
    routine.label("low_half")
    routine.jump_if_bit_clear(LOCAL_OPERAND, 1 << shift, "status_0")
    routine.jump("status_1")
    for value, dialogue_id in enumerate(status_ids):
        routine.label(f"status_{value}")
        _show(routine, dialogue_id)
        routine.jump("menu")
    routine.label("menu")
    routine.emit(mass_driver._choice_dialog(menu_id))
    # Native A9 encodes first and last selectable absolute rows as nibbles.
    # Row zero is the title. Leave keeps its existing row; optional help follows.
    routine.emit(bytes((0xA9, 0x10 | (len(puzzle.choices) + 2), 0x9C)))
    _drain(routine)
    for selection, dialogue_id in enumerate(result_ids, start=1):
        next_label = f"after_{selection}"
        routine.jump_if_not_equal(MENU_RESULT_OPERAND, selection, next_label)
        mask = (~(3 << shift)) & 0xFFFF
        signed_mask = mask if mask < 0x8000 else mask - 0x10000
        routine.emit(atel.variable_math(0x3E, LOCAL_OPERAND, signed_mask))
        routine.emit(atel.variable_math(0x38, LOCAL_OPERAND, selection << shift))
        _show(routine, dialogue_id)
        routine.jump("finish")
        routine.label(next_label)
    routine.jump_if_not_equal(MENU_RESULT_OPERAND, len(puzzle.choices) + 2, "finish")
    _show(routine, instruction_id)
    routine.jump("editable")
    # Leave, controller cancel, and unrecognized result values are state-neutral.
    routine.label("finish")
    _drain(routine)
    routine.emit(b"\xFE\x53\x00")
    return routine.finish()


def _normalized(text: str) -> str:
    return "".join(text.replace("<New>", " ").split())


def _dialogue_id(dialogue: bytes, text: str) -> int:
    matches = [block.block_id for block in parse_dialogue(dialogue).blocks if _normalized(block.text) == _normalized(text)]
    if len(matches) != 1:
        raise campaign.SurfaceCampaignBuildError("Production foundation dialogue is absent or ambiguous")
    return matches[0]


def _console_entities(editor: AtelScript, consoles: tuple[campaign.Console, ...]) -> tuple[int, ...]:
    entities = []
    for console in consoles:
        body = campaign._console_init(console)
        matches = []
        for entity in range(editor.entity_count):
            pc = editor.get_script_pointer(entity, 0)
            if editor.bytecode[pc:pc + len(body)] == body:
                matches.append(entity)
        if len(matches) != 1:
            raise campaign.SurfaceCampaignBuildError("Production console has no unique physical carrier")
        entities.append(matches[0])
    if len(set(entities)) != 3:
        raise campaign.SurfaceCampaignBuildError("Production console carriers overlap")
    return tuple(entities)


def prepare_production_puzzle(prepared: base.PreparedField) -> base.PreparedField:
    """Repoint checked foundation actions while retaining every native exit."""

    scene = prepared.spec.identity.scene
    if scene not in PUZZLES:
        return prepared
    puzzle = PUZZLES[scene]
    consoles = campaign.SORTER_CONSOLES if scene == 624 else campaign.CORE_CONSOLES
    success = campaign.SORTER_SUCCESS_DIALOGUE if scene == 624 else campaign.CORE_SUCCESS_DIALOGUE
    old_denial = (
        "MOLECULAR SORTER INTERLOCK\nDivert all three living-material feeds\nbefore entering the M-Project core.<Close>"
        if scene == 624 else
        "M-PROJECT CORE INTERLOCK\nDischarge fusion, uncouple the pattern,\nand retain containment.<Close>"
    )
    dialogue = prepared.components[7]
    editor = AtelScript(prepared.components[campaign.SCRIPT_INDEX])
    entities = _console_entities(editor, consoles)
    for entity, console in zip(entities, consoles, strict=True):
        pc = editor.get_script_pointer(entity, 2)
        expected = campaign._state_console_action(
            operand=LOCAL_OPERAND, bit_index=console.bit_index,
            dialogue_id=_dialogue_id(dialogue, console.text), routine_pc=pc,
        )
        if editor.bytecode[pc:pc + len(expected)] != expected:
            raise campaign.SurfaceCampaignBuildError(f"Field {scene} production action foundation changed")
    gate_pc = editor.get_script_pointer(1, 2)
    if gate_pc + 11 > editor.bytecode_size or editor.bytecode[gate_pc + 8] != 0x01:
        raise campaign.SurfaceCampaignBuildError("Production forward gate has no checked native target")
    native_exit_pc = struct.unpack_from("<H", editor.bytecode, gate_pc + 9)[0]
    success_id = _dialogue_id(dialogue, success)
    expected_gate = campaign._gate_local_completion(
        progress_bit_index=puzzle.progress_bit, progress_bit_mask=1 << puzzle.progress_bit,
        local_value=7, old_action_pc=native_exit_pc,
        denial_dialogue_id=_dialogue_id(dialogue, old_denial),
        success_dialogue_id=success_id, routine_pc=gate_pc,
    )
    if editor.bytecode[gate_pc:gate_pc + len(expected_gate)] != expected_gate:
        raise campaign.SurfaceCampaignBuildError(f"Field {scene} production completion foundation changed")

    dialogue, (instruction_id, denial_id) = campaign._append_dialogue(dialogue, (puzzle.instruction, puzzle.denial))
    for index, (entity, title) in enumerate(zip(entities, puzzle.names, strict=True)):
        statuses = ("Not configured",) + puzzle.choices
        dialogue, status_ids = campaign._append_dialogue(
            dialogue, tuple(f"{title}\nStaged setting:\n{label}<Close>" for label in statuses),
        )
        dialogue, (menu_id,) = campaign._append_dialogue(
            dialogue, (title + "\n<Opcode:01:FF>" + "\n".join("    " + choice for choice in puzzle.choices + ("Leave", REVIEW_INSTRUCTIONS)) + "<Close>",),
            height=len(puzzle.choices) + 3,
        )
        dialogue, result_ids = campaign._append_dialogue(
            dialogue, tuple(f"{title}\n{label}\nForward exit commits.\nLeaving now resets it.<Close>" for label in puzzle.choices),
        )
        dialogue, (solved_id,) = campaign._append_dialogue(
            dialogue, (f"{title}\nCommitted setting:\n{puzzle.choices[puzzle.correct[index] - 1]}\nSafety interlock active.<Close>",),
        )
        editor.append_and_repoint(entity, 2, choice_action(
            puzzle=puzzle, index=index, routine_pc=editor.bytecode_size,
            instruction_id=instruction_id, status_ids=status_ids, menu_id=menu_id,
            result_ids=result_ids, solved_id=solved_id,
        ))
    editor.append_and_repoint(1, 2, campaign._gate_local_completion(
        progress_bit_index=puzzle.progress_bit, progress_bit_mask=1 << puzzle.progress_bit,
        local_value=puzzle.solution, old_action_pc=native_exit_pc,
        denial_dialogue_id=denial_id, success_dialogue_id=success_id,
        routine_pc=editor.bytecode_size,
    ))
    return campaign._rebuild_field(
        prepared, editor=editor, dialogue=dialogue,
        role_suffix="status-first staged production choices with optional instructions, exact safe configuration, persistent read-only completion",
    )


def puzzle_metadata(prepared: base.PreparedField) -> dict[str, object]:
    """Return final action identities and the player-visible state contract."""

    scene = prepared.spec.identity.scene
    puzzle = PUZZLES[scene]
    editor = AtelScript(prepared.components[campaign.SCRIPT_INDEX])
    consoles = campaign.SORTER_CONSOLES if scene == 624 else campaign.CORE_CONSOLES
    entities = _console_entities(editor, consoles)
    blocks = parse_dialogue(prepared.components[7]).blocks
    controls = []
    for index, (entity, title) in enumerate(zip(entities, puzzle.names, strict=True)):
        menus = [block.block_id for block in blocks if block.text.startswith(title + "\n<Opcode:01:FF>") and block.text.endswith("\n    Leave\n    " + REVIEW_INSTRUCTIONS + "<Close>")]
        if len(menus) != 1:
            raise campaign.SurfaceCampaignBuildError("Completed production menu is absent or ambiguous")
        controls.append({
            "entity": entity,
            "title": title,
            "action_pc": editor.get_script_pointer(entity, 2),
            "menu_dialogue_id": menus[0],
            "choices": list(puzzle.choices) + ["Leave", REVIEW_INSTRUCTIONS],
            "leave_selection": len(puzzle.choices) + 1,
            "instructions_selection": len(puzzle.choices) + 2,
            "correct_selection": puzzle.correct[index],
            "local_mask": 3 << (2 * index),
        })
    return {
        "field": scene,
        "local_operand": LOCAL_OPERAND,
        "local_encoding": "three two-bit settings; zero is unconfigured",
        "solution": puzzle.solution,
        "correct_choices": [puzzle.choices[value - 1] for value in puzzle.correct],
        "progress_operand": STATE_OPERAND,
        "progress_bit": puzzle.progress_bit,
        "console_entities": list(entities),
        "console_action_pcs": [editor.get_script_pointer(entity, 2) for entity in entities],
        "controls": controls,
        "forward_exit_entity": 1,
        "forward_exit_action_pc": editor.get_script_pointer(1, 2),
        "commit": "successful forward exit, after the completion receipt closes",
        "editable_interaction": "current setting, then choices; instructions are optional and return to the current setting and choices",
        "instructions_dialogue_id": _dialogue_id(prepared.components[7], puzzle.instruction),
        "unsolved_reentry": "uncommitted choices reset; explained in optional instructions and every staged-setting confirmation",
        "solved_reentry": "committed settings are read-only; forward exit remains open",
        "leave_choice": "state-neutral",
        "instructions_choice": "state-neutral; returns to current setting and choices",
        "script_sha256": hashlib.sha256(prepared.components[campaign.SCRIPT_INDEX]).hexdigest(),
    }
