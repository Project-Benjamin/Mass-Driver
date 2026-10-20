"""Restore accepted Quarantine ring sizes when its local selections reset.

Apply after the V238 relay feedback pass and before music. Each replacement
initializer keeps the exact native actor-creation/setup prefix. Uncommitted
rooms resume their original selection branch; completed rooms render the
accepted biological solution without writing any puzzle or progression state.
"""

from __future__ import annotations

import hashlib

from modules.soylent_system import base, build as campaign
from modules.soylent_system.tools import surface_soylent_quarantine_feedback as feedback
from shared.tools.xgscript import AtelScript


SCENE = 620
INPUT_SCRIPT_IDENTITY = (
    5894, "3f2fcd150aed98ba4c6744a270b42b349461a3dff6a40744012ffc5cbad70eea",
)
# BC, 2D, FB, 35, F8, F8, 18, 64 and 20 comprise the native setup.
# None branches. The following 02 tests the field-local selection word.
NATIVE_SETUP_SIZE = 31


def committed_initializer(routine_pc: int, native_setup: bytes,
                          native_selection_pc: int, included: bool) -> bytes:
    if len(native_setup) != NATIVE_SETUP_SIZE or native_setup[0] != 0xBC:
        raise campaign.SurfaceCampaignBuildError("Quarantine ring setup changed")
    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.emit(native_setup)
    routine.jump_if_bit_clear(campaign.STATE_OPERAND, base.QUARANTINE_COMPLETE_BIT,
                             "uncommitted")
    routine.emit(feedback.SCALE_INCLUDED if included else feedback.SCALE_EXCLUDED)
    routine.emit(b"\x00")
    routine.label("uncommitted")
    # Keep the native branch at its existing address, including its absolute
    # STOP target. Relocating that conditional without its target is unsafe.
    routine.emit(campaign._jump(native_selection_pc))
    return routine.finish()


def prepare_committed_visuals(prepared: base.PreparedField) -> base.PreparedField:
    if prepared.spec.identity.scene != SCENE:
        return prepared
    script = prepared.components[campaign.SCRIPT_INDEX]
    if (len(script), hashlib.sha256(script).hexdigest()) != INPUT_SCRIPT_IDENTITY:
        raise campaign.SurfaceCampaignBuildError("Quarantine committed-visual foundation changed")
    editor = AtelScript(script)
    for entity, _, native_pc, _, native_init, _ in base.QUARANTINE_RING_ROUTINES:
        expected = bytearray(native_init)
        expected[NATIVE_SETUP_SIZE + 1:NATIVE_SETUP_SIZE + 3] = campaign._u16(
            campaign.LOCAL_PUZZLE_OPERAND,
        )
        if (editor.get_script_pointer(entity, 0) != native_pc
                or editor.bytecode[native_pc:native_pc + len(expected)] != expected):
            raise campaign.SurfaceCampaignBuildError("Quarantine native ring initializer changed")
        editor.append_and_repoint(entity, 0, committed_initializer(
            editor.bytecode_size, bytes(expected[:NATIVE_SETUP_SIZE]),
            native_pc + NATIVE_SETUP_SIZE, included=entity != 20,
        ))
    return campaign._rebuild_field(
        prepared, editor=editor,
        role_suffix="accepted Quarantine ring visuals persist through field-local reset",
    )


def committed_visuals_metadata(prepared: base.PreparedField) -> dict[str, object]:
    editor = AtelScript(prepared.components[campaign.SCRIPT_INDEX])
    return {
        "field": SCENE,
        "entities": [entity for entity, *_ in base.QUARANTINE_RING_ROUTINES],
        "initializer_pcs": [editor.get_script_pointer(entity, 0)
                            for entity, *_ in base.QUARANTINE_RING_ROUTINES],
        "completion_operand": campaign.STATE_OPERAND,
        "completion_mask": base.QUARANTINE_COMPLETE_BIT,
        "accepted_included_entities": [17, 18, 19],
        "accepted_excluded_entities": [20],
        "writes_puzzle_or_progression_state": False,
        "uncommitted_visuals": "Original native field-local selection branch",
        "native_actions_and_doors": "Unchanged",
    }
