"""Close the standalone dungeon while retaining native battle/save recovery."""

from __future__ import annotations

import hashlib

from modules.soylent_system import base, build as campaign
from shared.tools.xgdialog import parse_dialogue
from shared.tools.xgscript import AtelScript


SCENE = 622
INPUT_SCRIPT_IDENTITY = (6781, "328a75e900917f19f9a8fb98bc9c9abd52b19789de801302b27ca7c4f1c67049")
INPUT_DIALOGUE_IDENTITY = (5151, "68fee99a3b96a7a0b523f528253745a59ea832b0c864d71e32bb448c01826b34")
EPILOGUE_ID = 40
COMPLETED_ID = 41
EPILOGUE = (
    "The generation cycle stops.\nThis Ignas node is silent.\n"
    "Other Surface systems remain.<New>"
    "Elly\n\"They are quiet now.\nI wish we could have\nreached them sooner.\"<New>"
    "Fei\n\"There are still people\nwaiting upstairs. We are\nnot leaving them behind.\"<New>"
    "Citan\n\"Containment is stable.\nWe can return to the wards\nwithout restarting the line.\"<New>"
    "SOYLENT SYSTEM COMPLETE\nLocal production shut down.\nEmergency return unlocked.<New>"
    "Save at the control beside\nthe chamber entrance.\nThe emergency return leads\nback to the patient wards.<Close>"
)
COMPLETED = (
    "SOYLENT SYSTEM COMPLETE\nThis node remains shut down.\n"
    "Save and emergency return\ncontrols remain available.<New>"
    "The patients in the wards\nstill need care. The line\n"
    "will not restart while you\nreturn to speak with them.<Close>"
)
AFTERMATH = {
    8: "You could not undo what\nhappened to us.\nBut you made it stop.<Close>",
    9: "No more lines to stand in.\nNo more sorting us into\npeople worth saving.<Close>",
    10: "I can hear your footsteps.\nThe machines used to drown\nout everything else.<Close>",
    11: "My body has not changed back.\nI know that.\nI still want tomorrow.<Close>",
    12: "No one else has to give\nthis place their flesh.\nPlease make sure of that.<Close>",
    13: "You came back to look at us.\nThank you for that.<Close>",
    14: "Their measurements can stay\nin their files.\nI am not their weapon.<Close>",
    15: "Some of us need more help\nthan others.\nPlease start with them.<Close>",
    16: "The generation equipment\nhas stopped.\nIt is really stopped.<Close>",
    17: "Nothing is moving in the\nchamber now.\nI hope they can rest.<Close>",
    18: "The barrier is holding.\nFor once, it is keeping\nsomething safe.<Close>",
    19: "The people who ran this\nplace left us here.\nYou did not.<Close>",
    20: "I will remember their eyes.\nSomeone should remember\nwho they were.<Close>",
    21: "The crying has stopped.\nI do not know what to say.<Close>",
    22: "You reached the controls.\nYou listened to us.\nI thought no one would.<Close>",
    23: "That terrible sound is gone.\nI keep waiting for it\nto start again.<Close>",
    24: "When you tell people about\nthis place, tell them\nwe were still here.<Close>",
}


def aftermath_action(pc, native_pc, dialogue_id):
    routine = base.mass_driver._RoutineBuilder(pc)
    routine.jump_if_bit_clear(campaign.STATE_OPERAND, campaign.SECURED_BIT_MASK, "native")
    routine.emit(campaign._repeatable_dialogue_action(dialogue_id, routine.pc))
    routine.label("native")
    routine.emit(campaign._jump(native_pc))
    return routine.finish()


def prepare_finale_closure(prepared: base.PreparedField) -> base.PreparedField:
    if prepared.spec.identity.scene != SCENE:
        return prepared
    for label, index, expected in (("script", 5, INPUT_SCRIPT_IDENTITY), ("dialogue", 7, INPUT_DIALOGUE_IDENTITY)):
        data = prepared.components[index]
        if (len(data), hashlib.sha256(data).hexdigest()) != expected:
            raise campaign.SurfaceCampaignBuildError(f"Finale closure {label} foundation changed")
    editor = AtelScript(prepared.components[5])
    if set(AFTERMATH) != {entity for entity, _ in base.GENERATION_NPC_DIALOGUES}:
        raise campaign.SurfaceCampaignBuildError("Generation survivor inventory changed")
    dialogue = campaign._replace_dialogue_texts(prepared.components[7], {EPILOGUE_ID: EPILOGUE, COMPLETED_ID: COMPLETED})
    dialogue, ids = campaign._append_dialogue(dialogue, tuple(AFTERMATH.values()))
    for entity, dialogue_id in zip(AFTERMATH, ids, strict=True):
        native_pc = editor.get_script_pointer(entity, 2)
        if editor.bytecode[native_pc] != 0xD2:
            raise campaign.SurfaceCampaignBuildError(f"Generation survivor {entity} no longer has a native talk action")
        editor.append_and_repoint(entity, 2, aftermath_action(editor.bytecode_size, native_pc, dialogue_id))
    return campaign._rebuild_field(
        prepared, editor=editor, dialogue=dialogue,
        role_suffix="final dungeon completion receipt and state-aware survivor aftermath",
    )


def closure_metadata(prepared):
    editor = AtelScript(prepared.components[5])
    blocks = parse_dialogue(prepared.components[7]).blocks
    return {
        "field": SCENE, "epilogue_dialogue_id": EPILOGUE_ID, "completed_dialogue_id": COMPLETED_ID,
        "completion": "Native Sufal victory and complete epilogue before persistent secured flag",
        "survivor_entities": list(AFTERMATH),
        "survivor_action_pcs": [editor.get_script_pointer(entity, 2) for entity in AFTERMATH],
        "survivor_dialogue_ids": [next(block.block_id for block in blocks if block.text == text) for text in AFTERMATH.values()],
        "battle_save_recovery_and_return": "Preserved byte-for-byte",
        "scope": "This Ignas node; survivors remain people in need of care; other Surface systems remain",
    }
