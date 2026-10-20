"""Finish the playable Meld and Sufal interactions without changing assets.

Runs after the campaign's reviewed dialogue layout and before music. The
native battle, aftermath recovery, door animations and save point are kept.
"""

from __future__ import annotations

import modules.soylent_system.base as base
import modules.soylent_system.build as campaign
from shared.tools.xgdialog import parse_dialogue
from shared.tools.xgscript import AtelScript


MELD_ENTITY = 33
BOSS_ENTITY = 29
MELD_RETURN_TEXT = (
    "The containment field holds.\n"
    "Their voices still reach us.\n"
    "We must stop the line.<Close>"
)
MELD_SECURED_TEXT = (
    "The voices have fallen quiet.\n"
    "No new bodies enter the line.\n"
    "The emergency return is open.<Close>"
)
BOSS_CONFIRM_TEXT = (
    "GENERATION CHAMBER\n"
    "<Opcode:01:FF>    Confront the Sufal Mass\n"
    "    Not yet<Close>"
)
BOSS_CANCEL_TEXT = (
    "The save control is beside\n"
    "the chamber entrance.\n"
    "The Stabilization Ward can\n"
    "restore our HP and EP.<Close>"
)


def _drain(routine: base.mass_driver._RoutineBuilder) -> None:
    routine.emit(base.mass_driver._wait_for_pad_release(
        base.mass_driver.PAD_MASK_CROSS, routine.pc,
    ))
    routine.emit(base.mass_driver._wait())


def _show(routine: base.mass_driver._RoutineBuilder, dialogue_id: int) -> None:
    routine.emit(b"\xF5" + campaign._u16(dialogue_id) + b"\x01\x9C")
    _drain(routine)


def meld_action(routine_pc: int, repeat_id: int, secured_id: int) -> bytes:
    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.emit(b"\x33\xFE\x54")
    _drain(routine)
    routine.jump_if_bit_clear(campaign.STATE_OPERAND, campaign.SECURED_BIT_MASK, "unsecured")
    _show(routine, secured_id)
    routine.jump("finish")
    routine.label("unsecured")
    routine.jump_if_bit_clear(campaign.STATE_OPERAND, campaign.MELD_BIT_MASK, "first")
    _show(routine, repeat_id)
    routine.jump("finish")
    routine.label("first")
    _show(routine, 3)
    # The long first encounter must finish before the onward door opens.
    routine.emit(campaign._set_bit(campaign.STATE_OPERAND, campaign.MELD_BIT_INDEX))
    routine.label("finish")
    routine.emit(b"\xFE\x53\x00")
    return routine.finish()


def boss_confirmation_action(
    routine_pc: int, native_boss_pc: int, menu_id: int, cancel_id: int,
) -> bytes:
    routine = base.mass_driver._RoutineBuilder(routine_pc)
    # Completed and interrupted-victory states retain their exact existing
    # acknowledgement/recovery path without asking to fight the boss again.
    routine.jump_if_bit_clear(campaign.STATE_OPERAND, campaign.SECURED_BIT_MASK, "pending")
    routine.emit(campaign._jump(native_boss_pc))
    routine.label("pending")
    routine.jump_if_bit_clear(campaign.STATE_OPERAND,
                             campaign.FINALE_EPILOGUE_PENDING_BIT_MASK, "prompt")
    routine.emit(campaign._jump(native_boss_pc))
    routine.label("prompt")
    routine.emit(b"\x33\xFE\x54")
    _drain(routine)
    routine.emit(base.mass_driver._choice_dialog(menu_id))
    routine.emit(b"\xA9\x12\x9C")
    _drain(routine)
    routine.jump_if_not_equal(0x0014, 1, "cancel")
    routine.emit(campaign._jump(native_boss_pc))
    routine.label("cancel")
    _show(routine, cancel_id)
    routine.emit(b"\xFE\x53\x00")
    return routine.finish()


def prepare_story_finish(prepared: base.PreparedField) -> base.PreparedField:
    scene = prepared.spec.identity.scene
    if scene not in (625, 622):
        return prepared
    editor = AtelScript(prepared.components[campaign.SCRIPT_INDEX])
    dialogue = prepared.components[7]
    if scene == 625:
        pc = editor.get_script_pointer(MELD_ENTITY, 2)
        expected = campaign._state_console_action(
            operand=campaign.STATE_OPERAND, bit_index=campaign.MELD_BIT_INDEX,
            dialogue_id=3, routine_pc=pc,
        )
        if editor.bytecode[pc:pc + len(expected)] != expected:
            raise campaign.SurfaceCampaignBuildError("Meld witness foundation changed")
        dialogue, ids = campaign._append_dialogue(dialogue, (MELD_RETURN_TEXT, MELD_SECURED_TEXT))
        editor.append_and_repoint(MELD_ENTITY, 2, meld_action(editor.bytecode_size, *ids))
    else:
        pc = editor.get_script_pointer(BOSS_ENTITY, 2)
        expected = campaign._boss_action(pre_dialogue_id=39, post_dialogue_id=40,
                                        already_dialogue_id=41, routine_pc=pc)
        if editor.bytecode[pc:pc + len(expected)] != expected:
            raise campaign.SurfaceCampaignBuildError("Sufal recovery foundation changed")
        dialogue, (menu_id,) = campaign._append_dialogue(dialogue, (BOSS_CONFIRM_TEXT,), height=3)
        dialogue, (cancel_id,) = campaign._append_dialogue(dialogue, (BOSS_CANCEL_TEXT,))
        editor.append_and_repoint(BOSS_ENTITY, 2, boss_confirmation_action(
            editor.bytecode_size, pc, menu_id, cancel_id,
        ))
    return campaign._rebuild_field(prepared, editor=editor, dialogue=dialogue,
        role_suffix="completed story interaction with deliberate commitment and repeat-state aftermath")


def story_metadata(prepared: base.PreparedField) -> dict[str, object]:
    scene = prepared.spec.identity.scene
    if scene not in (625, 622):
        return {}
    entity = MELD_ENTITY if scene == 625 else BOSS_ENTITY
    editor = AtelScript(prepared.components[campaign.SCRIPT_INDEX])
    blocks = parse_dialogue(prepared.components[7]).blocks
    return {
        "field": scene, "entity": entity, "action_pc": editor.get_script_pointer(entity, 2),
        "kind": "first_witness_and_aftermath" if scene == 625 else "boss_confirmation_and_recovery",
        "added_dialogue_ids": [
            next(block.block_id for block in blocks if block.text == text)
            for text in ((MELD_RETURN_TEXT, MELD_SECURED_TEXT) if scene == 625
                         else (BOSS_CONFIRM_TEXT, BOSS_CANCEL_TEXT))
        ],
    }
