"""Make Quarantine's diagnostic choices explicit without changing its solution."""

from __future__ import annotations

import hashlib

from modules.soylent_system import base, build as campaign
from shared.tools import atel_primitives as atel
from shared.tools.xgdialog import parse_dialogue
from shared.tools.xgscript import AtelScript


SCENE = 620
INPUT_SCRIPT_IDENTITY = (5218, "4ef602ddb8edd4694b6a7e669d0483c65e5e19ae6b7d2bfe481b65daefe33a5e")
RELAYS = (
    (17, 4, "POD A // GENOME", "Human baseline retained."),
    (18, 5, "POD B // LIMITER", "Limiter collapse detected."),
    (19, 6, "POD C // NANOMACHINES", "Contamination detected."),
    (20, 7, "POD D // CASTE INDEX", "Administrative data only."),
)
INSTRUCTIONS = (
    "DIAGNOSTIC SELECTION\nChoose readings that describe\n"
    "the patient's biology.\nCaste is a social category.<New>"
    "Use a pod to include or\nexclude its reading. Submit\n"
    "at the east door. Leaving\nresets unsubmitted readings.<Close>"
)
SCALE_INCLUDED = bytes.fromhex("FE 08 00 94 00 94 00 94")
SCALE_EXCLUDED = bytes.fromhex("FE 08 00 90 00 90 00 90")


def _drain(routine):
    routine.emit(base.mass_driver._wait_for_pad_release(base.mass_driver.PAD_MASK_CROSS, routine.pc))
    routine.emit(base.mass_driver._wait())


def _show(routine, block_id):
    routine.emit(b"\xF5" + atel.u16(block_id) + b"\x01\x9C")
    _drain(routine)


def relay_action(routine_pc, bit, hint_id, included_id, excluded_id, committed_id):
    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.emit(b"\x33\xFE\x54")
    _drain(routine)
    routine.jump_if_bit_clear(campaign.STATE_OPERAND, 0x0100, "editable")
    _show(routine, committed_id)
    routine.jump("finish")
    routine.label("editable")
    # Reuse the native one-time instruction flag; allocate no new state.
    routine.jump_if_bit_clear(campaign.STATE_OPERAND, 0x0200, "instructions")
    routine.jump("toggle")
    routine.label("instructions")
    _show(routine, hint_id)
    routine.emit(campaign._set_bit(campaign.STATE_OPERAND, 9))
    routine.label("toggle")
    routine.jump_if_bit_clear(campaign.LOCAL_PUZZLE_OPERAND, 1 << bit, "include")
    routine.emit(campaign._clear_bit(campaign.LOCAL_PUZZLE_OPERAND, bit))
    routine.emit(bytes.fromhex("74 5F 80") + SCALE_EXCLUDED)
    _show(routine, excluded_id)
    routine.jump("finish")
    routine.label("include")
    routine.emit(campaign._set_bit(campaign.LOCAL_PUZZLE_OPERAND, bit))
    routine.emit(bytes.fromhex("74 50 80") + SCALE_INCLUDED)
    _show(routine, included_id)
    routine.label("finish")
    routine.emit(b"\xFE\x53\x00")
    return routine.finish()


def prepare_quarantine_feedback(prepared: base.PreparedField) -> base.PreparedField:
    if prepared.spec.identity.scene != SCENE:
        return prepared
    script = prepared.components[campaign.SCRIPT_INDEX]
    if (len(script), hashlib.sha256(script).hexdigest()) != INPUT_SCRIPT_IDENTITY:
        raise campaign.SurfaceCampaignBuildError("Quarantine feedback foundation changed")
    editor = AtelScript(script)
    dialogue, (hint_id,) = campaign._append_dialogue(prepared.components[7], (INSTRUCTIONS,))
    for entity, bit, title, reading in RELAYS:
        texts = (
            f"{title}\n{reading}\nReading: INCLUDED\nUse the east door to submit.<Close>",
            f"{title}\n{reading}\nReading: EXCLUDED\nUse the east door to submit.<Close>",
            f"{title}\nAccepted reading: {'EXCLUDED' if bit == 7 else 'INCLUDED'}\nDiagnostic check complete.\nThe service route is open.<Close>",
        )
        dialogue, ids = campaign._append_dialogue(dialogue, texts)
        editor.append_and_repoint(entity, 2, relay_action(editor.bytecode_size, bit, hint_id, *ids))
    return campaign._rebuild_field(
        prepared, editor=editor, dialogue=dialogue,
        role_suffix="explicit included/excluded biological readings and read-only accepted result",
    )


def feedback_metadata(prepared):
    editor = AtelScript(prepared.components[campaign.SCRIPT_INDEX])
    blocks = parse_dialogue(prepared.components[7]).blocks
    return {
        "field": SCENE, "entities": [entry[0] for entry in RELAYS],
        "action_pcs": [editor.get_script_pointer(entry[0], 2) for entry in RELAYS],
        "instruction_dialogue_id": next(block.block_id for block in blocks if block.text == INSTRUCTIONS),
        "solution": "Include Genome, Limiter and Nanomachines; exclude Caste Index",
        "selection": "Each deliberate interaction toggles the reading and reports its resulting state",
        "submitted_result": "Persistent and read-only; native east and west door actions unchanged",
        "unsubmitted_readings": "Reset on leaving, explained in the first-use instructions",
    }
