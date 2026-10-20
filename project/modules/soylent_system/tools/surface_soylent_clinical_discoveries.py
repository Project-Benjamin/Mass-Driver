"""Optional treatment-room records and human responses to the shutdown.

Uses existing terminal/NPC entities and story flags. Nothing in these rooms
awards clearance or gates the route; field 593 remains entirely untouched.
"""

from __future__ import annotations

import hashlib

from modules.soylent_system import base, build as campaign
from modules.soylent_system.tools import surface_soylent_campaign_exam_rooms as exam
from modules.soylent_system.tools.surface_soylent_story_finish import _drain, _show
from shared.tools import atel_primitives as atel
from shared.tools.xgdialog import parse_dialogue
from shared.tools.xgscript import AtelScript


INPUT_IDENTITIES = {
    591: (3448, "3a9082d9405ef894f1c9decb7a768cc9df2bc0ce8a4c0d286c5a749470c5fb1e"),
    592: (3448, "8f69799ebc146b41a8e0e82c6e19be5eeb4d55eedb0cb87a0ccf7073345514b7"),
    594: (3446, "d8c85f5c2683bef52530c7e601b37cb94104fb54d1718f2215577174fe113a7f"),
}
TERMINAL_ACTION_PCS = {591: 0x07B4, 592: 0x07B4, 594: 0x07B2}
MENU_TEXT = (
    "PATIENT WORKSTATION\n<Opcode:01:FF>    Patient record\n"
    "    Staff memorandum\n    Leave\n    Current status<Close>"
)
MENU_HEIGHT = 5
MEMORANDA = {
    591: (
        "STAFF MEMORANDUM // A\nLiving tissue must remain\n"
        "in STASIS during transfer.\nDo not route it to a drain.<New>"
        "Handwritten below:\nHe still answers to his\n"
        "name. I have requested\nanother delay.<Close>"
    ),
    592: (
        "STAFF MEMORANDUM // B\nNanomachine medium belongs\n"
        "in RECLAMATION. Unstable\nMeld returns to CONTAINMENT.<New>"
        "Handwritten below:\nShe asked whether her family\n"
        "could visit. There is no\nbox for that on this form.<Close>"
    ),
    594: (
        "STAFF MEMORANDUM // C\nEmergency core isolation:\n"
        "FUSION OFF. PATTERN OFF.\nCONTAINMENT must stay ON.<New>"
        "Handwritten below:\nStopping the process must\n"
        "not release what the\ncontainment field holds.<Close>"
    ),
}
HALTED_REPORT = (
    "TRANSFER STATUS // HALTED\nNo new transfer orders.\n"
    "Containment remains active.\nLocal production has stopped.<Close>"
)
ACTIVE_REPORT = (
    "TRANSFER STATUS // ACTIVE\nTransfer queue still active.\n"
    "No shutdown confirmation.\nPatient records retained.<Close>"
)
CARE_HANDOFF = (
    'Physician\n"No more transfer orders.\nHow do we care for the\n'
    'patients who are still here?"<New>'
    'Citan\n"Keep them here for now.\nCheck their breathing and\n'
    'record any changes."<New>'
    'Physician\n"I will check every room.\nWe will stay with them\n'
    'while help is arranged."<Close>'
)
RESPONSES = {
    591: (
        "You came back.\nIs the treatment taking\nlonger than they told us?<Close>",
        "The transfer order is wrong.\nI have kept him here.\nPlease give us more time.<Close>",
        "The floor stopped shaking.\nI can hear myself think.\nWill you tell them I am\nstill here?<Close>",
        CARE_HANDOFF,
    ),
    592: (
        "You look frightened.\nPlease do not decide for me\nthat I cannot bear the truth.<Close>",
        "The medium is not medicine.\nI should have questioned\nthose instructions sooner.<Close>",
        "The machines have stopped,\nbut I still feel like me.\nThat has to count for\nsomething, does it not?<Close>",
        "The line is stopped.\nWe still have patients.\nThat is where our work\nstarts now.<Close>",
    ),
    594: (
        "They said I was next.\nCan I stay here a little\nlonger? Just a little.<Close>",
        "I have not sent this patient\nonward. Keep containment\nrunning if you stop the core.<Close>",
        "I do not have to go through\nthat door now?\nThen I would like to rest.<Close>",
        "The queue has been halted.\nWe can care for the people\nstill in these rooms.<Close>",
    ),
}


def terminal_action(pc, menu_id, record_id, memo_id, halted_id, active_id):
    routine = base.mass_driver._RoutineBuilder(pc)
    routine.emit(b"\x33\xFE\x54")
    _drain(routine)
    routine.emit(base.mass_driver._choice_dialog(menu_id))
    routine.emit(b"\xA9\x14\x9C")
    _drain(routine)
    routine.jump_if_not_equal(0x0014, 1, "memo")
    _show(routine, record_id)
    routine.jump("finish")
    routine.label("memo")
    routine.jump_if_not_equal(0x0014, 2, "status")
    _show(routine, memo_id)
    routine.jump("finish")
    routine.label("status")
    routine.jump_if_not_equal(0x0014, 4, "finish")
    routine.jump_if_bit_clear(campaign.STATE_OPERAND, campaign.SECURED_BIT_MASK, "active_status")
    _show(routine, halted_id)
    routine.jump("finish")
    routine.label("active_status")
    _show(routine, active_id)
    routine.label("finish")
    routine.emit(b"\xFE\x53\x00")
    return routine.finish()


def npc_action(pc, native_pc, entity, counterpart, revealed_id, secured_id):
    routine = base.mass_driver._RoutineBuilder(pc)
    routine.jump_if_bit_clear(campaign.STATE_OPERAND, campaign.SECURED_BIT_MASK, "revelation")
    routine.jump("secured")
    routine.label("revelation")
    routine.jump_if_bit_clear(campaign.STATE_OPERAND, campaign.MELD_BIT_MASK, "original")
    routine.emit(exam._stationary_actor_action(entity=entity, counterpart=counterpart, dialogue_id=revealed_id))
    routine.label("secured")
    routine.emit(exam._stationary_actor_action(entity=entity, counterpart=counterpart, dialogue_id=secured_id))
    routine.label("original")
    routine.emit(campaign._jump(native_pc))
    return routine.finish()


def expected_terminal_action(scene):
    menu_id = exam.FINAL_DIALOGUE_COUNTS_BY_SCENE[scene]
    return terminal_action(TERMINAL_ACTION_PCS[scene], menu_id,
                           exam.PATIENT_RECORD_DIALOGUE_IDS_BY_SCENE[scene],
                           menu_id + 1, menu_id + 2, menu_id + 7)


def prepare_clinical_discoveries(prepared: base.PreparedDonorField) -> base.PreparedDonorField:
    scene = prepared.identity.scene
    if scene not in INPUT_IDENTITIES:
        return prepared
    script = prepared.components[campaign.SCRIPT_INDEX]
    if (len(script), hashlib.sha256(script).hexdigest()) != INPUT_IDENTITIES[scene]:
        raise campaign.SurfaceCampaignBuildError(f"Field {scene} clinical discovery foundation changed")
    editor = AtelScript(script)
    dialogue, (menu_id,) = campaign._append_dialogue(
        prepared.components[7], (MENU_TEXT,), height=MENU_HEIGHT,
    )
    dialogue, ids = campaign._append_dialogue(
        dialogue, (MEMORANDA[scene], HALTED_REPORT, *RESPONSES[scene], ACTIVE_REPORT),
    )
    memo_id, halted_id, patient_revealed, doctor_revealed, patient_secured, doctor_secured, active_id = ids
    pc = editor.append_and_repoint(exam.TERMINAL_ENTITY, 2, terminal_action(
        editor.bytecode_size, menu_id, exam.PATIENT_RECORD_DIALOGUE_IDS_BY_SCENE[scene],
        memo_id, halted_id, active_id,
    ))
    for entity in exam.TERMINAL_AUX_ENTITIES:
        editor.set_script_pointer(entity, 2, pc)
    for entity, counterpart, revealed, secured in (
        (exam.PATIENT_ENTITY, exam.DOCTOR_ENTITY, patient_revealed, patient_secured),
        (exam.DOCTOR_ENTITY, exam.PATIENT_ENTITY, doctor_revealed, doctor_secured),
    ):
        native_pc = editor.get_script_pointer(entity, 2)
        editor.append_and_repoint(entity, 2, npc_action(editor.bytecode_size, native_pc, entity, counterpart, revealed, secured))
    return campaign._rebuild_donor(
        prepared, editor=editor, dialogue=dialogue,
        role_suffix="retained staff memoranda, separate facility status, and patient/physician responses after revelation and shutdown",
    )


def discovery_metadata(prepared):
    scene = prepared.identity.scene
    blocks = parse_dialogue(prepared.components[7]).blocks
    editor = AtelScript(prepared.components[campaign.SCRIPT_INDEX])
    return {
        "field": scene, "optional": True, "writes_state": False,
        "terminal_entities": list(exam.TERMINAL_ENTITIES),
        "menu_dialogue_id": next(block.block_id for block in blocks if block.text == MENU_TEXT),
        "choices": ["Patient record", "Staff memorandum", "Leave", "Current status"],
        "menu_height": MENU_HEIGHT,
        "memorandum": MEMORANDA[scene],
        "memorandum_available_after_shutdown": True,
        "current_status": {"active": ACTIVE_REPORT, "secured": HALTED_REPORT},
        "care_handoff": CARE_HANDOFF if scene == 591 else None,
        "npc_entities": [exam.PATIENT_ENTITY, exam.DOCTOR_ENTITY],
        "npc_action_pcs": [editor.get_script_pointer(entity, 2) for entity in (exam.PATIENT_ENTITY, exam.DOCTOR_ENTITY)],
        "phases": ["native hopeful treatment", "Meld witnessed", "local production secured"],
        "keycard_room_593": "unchanged and unoccupied",
    }
