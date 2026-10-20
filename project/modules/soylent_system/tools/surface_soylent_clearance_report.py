"""Explain the ward's four production clearances without granting any of them.

Apply after ``surface_soylent_checkpoint.prepare_checkpoint`` and before music.
The fifth menu row enters a read-only report; the sixth gives one next goal.
Existing choices keep their native checkpoint paths and four-credential gate.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib

from modules.soylent_system import base
from modules.soylent_system.tools import surface_soylent_checkpoint as checkpoint
from shared.tools.atel_primitives import u16
from shared.tools.xgdialog import parse_dialogue, replace_dialogue, REPLACEMENTS_JSON_FORMAT
from shared.tools.xgfield import build_field_preserving, parse_field
from shared.tools.xgscript import AtelScript


SCENE = checkpoint.SCENE
REPORT_CHOICE = 5
OBJECTIVE_CHOICE = 6
MENU_HEIGHT = 7
MENU_TEXT = checkpoint.MENU_TEXT.replace(
    "    Leave<Close>", "    Leave\n    Clearance report\n    Next objective<Close>",
)
ACTION_PC = 0x0D6D
MENU_RANGE_PC = 0x0D83
REPORT_BRANCH_TARGET_PC = 0x0DB8
CHECKPOINT_FINISH_PC = 0x0DC1
REPORT_PC = 0x0DD2
INPUT_SCRIPT_IDENTITY = (
    5270, "d3698ede8bd9897f2bca6565f2a967e4e7830b104a78d3e959f6f9f363e105bc",
)
INPUT_DIALOGUE_IDENTITY = (
    308, "4a9671a437167417d47c0e5db650b0e56d3aab11da1e2d78c4f29751d4fcc555",
)
INPUT_HEADER_IDENTITY = (
    944, "c11b08000087ff5382730ce590e30e200ec806cadda0cc4c388729e7e001c9ae",
)
INPUT_BUNDLE_IDENTITY = (
    85176, "ea6e563f9680feb5dbc33b9f284dbccb7f0d8d722e4eaf29109d1d8862d93099",
)
STATE_OPERAND = 0x03FA
SECURED_MASK = 0x8000
READY_DIALOGUE_ID = 9
SECURED_DIALOGUE_ID = 10
READY_TEXT = (
    "PRODUCTION CLEARANCE READY\n"
    "All four requirements met.\n"
    "Select Enter production to\n"
    "reach Molecular Sorting.<Close>"
)
SECURED_TEXT = (
    "LOCAL NODE SECURED\n"
    "New transfers have stopped.\n"
    "The emergency return is open.\n"
    "Recovery and saving remain.<Close>"
)


@dataclass(frozen=True)
class Clearance:
    key: str
    operand: int
    mask: int
    dialogue_id: int
    source_fields: tuple[int, ...]
    text: str


# These are exactly the existing gate's four tests. The report order follows
# the player's route; hearing the resonance clue alone never satisfies it.
CLEARANCES = (
    Clearance(
        "security_keycard", 0x021A, 0x0001, 5, (549, 621, 550),
        "SECURITY KEYCARD MISSING\n"
        "Return through Service\n"
        "Manifold to Intake Reception.\n"
        "Visit the physician's clinic.<New>"
        "Register at the Archive and\n"
        "wait for your alias to be\n"
        "called. Follow the physician.<New>"
        "After refusing bloodwork\n"
        "twice, defeat the responding\n"
        "team to recover its keycard.<Close>",
    ),
    Clearance(
        "quarantine_complete", STATE_OPERAND, 0x0100, 6, (620,),
        "QUARANTINE DIAGNOSIS MISSING\n"
        "Return to Quarantine through\n"
        "Intake Reception. Switch ON\n"
        "Genome, Limiter, Nanomachines<New>"
        "Keep the Caste relay OFF.\n"
        "Use the east continuation\n"
        "door to confirm diagnosis.<Close>",
    ),
    Clearance(
        "tone_authorized", 0x021E, 0x0200, 7, (565, 589),
        "ORGANIC RESONANCE MISSING\n"
        "Return to Service Manifold.\n"
        "Hear the five-tone clue in\n"
        "Organic Resonance Annex.<New>"
        "Then use the five-direction\n"
        "lock in Service Manifold.\n"
        "Hearing the clue alone does\n"
        "not grant authorization.<Close>",
    ),
    Clearance(
        "interface_cutoff_armed", STATE_OPERAND, 0x0800, 8, (565, 588),
        "INTERFACE CUTOFF MISSING\n"
        "Return to Service Manifold.\n"
        "Enter the Clinical Interface\n"
        "Scanner Annex.<New>"
        "Use its diagnostic scanner\n"
        "to arm the living-subject\n"
        "interface cutoff.<Close>",
    ),
)

# Ordered read-only goals. Each goal is shown only while its actual native
# completion flag is absent. The first four exactly match the production gate.
OBJECTIVES = (
    (0x021A, 0x0001, "NEXT: SECURITY KEYCARD\nVisit the physician's clinic\nfrom Intake Reception.\nVisit Archive to register.<Close>"),
    (STATE_OPERAND, 0x0100, "NEXT: QUARANTINE DIAGNOSIS\nConfigure the four readings\nin Quarantine. Submit them\nat its east door.<Close>"),
    (0x021E, 0x0200, "NEXT: RESONANCE LOCK\nHear the pattern in the\nOrganic Resonance Annex, then\nuse the service input panel.<Close>"),
    (STATE_OPERAND, 0x0800, "NEXT: INTERFACE CUTOFF\nVisit the Clinical Interface\nScanner Annex from Service\nManifold. Use its scanner.<Close>"),
    (STATE_OPERAND, 0x1000, "NEXT: MOLECULAR SORTING\nSelect Enter production.\nSet all three feed routes.\nCommit at the forward exit.<Close>"),
    (STATE_OPERAND, 0x2000, "NEXT: M-PROJECT CORE\nContinue past Sorting.\nSet all three core controls.\nCommit at the forward exit.<Close>"),
    (STATE_OPERAND, 0x4000, "NEXT: MELD CONTAINMENT\nContinue past the Core.\nInspect the containment\ndisplay before proceeding.<Close>"),
)
OBJECTIVE_FIRST_ID = 11
BOSS_OBJECTIVE_ID = OBJECTIVE_FIRST_ID + len(OBJECTIVES)
BOSS_OBJECTIVE_TEXT = (
    "NEXT: GENERATION CHAMBER\nSave beside the entrance.\nConfront the Sufal Mass, then\nfinish the shutdown epilogue.<Close>"
)


class ClearanceReportError(base.SurfaceSoylentBuildError):
    """Raised when the audited checkpoint or its production gate changes."""


def _identity(data: bytes) -> tuple[int, str]:
    return len(data), hashlib.sha256(data).hexdigest()


def clearance_report_action(routine_pc: int) -> bytes:
    """Report missing credentials using only reads of existing state words."""
    routine = base.mass_driver._RoutineBuilder(routine_pc)

    def show(dialogue_id: int) -> None:
        routine.emit(b"\xF5" + u16(dialogue_id) + b"\x01\x9C")
        routine.emit(base.mass_driver._wait_for_pad_release(
            base.mass_driver.PAD_MASK_CROSS, routine.pc,
        ))
        routine.emit(base.mass_driver._wait())

    # The existing Save comparison routes every non-Save value here. Keep
    # Leave, Cancel and invalid values on the exact old finish path.
    routine.jump_if_not_equal(0x0014, OBJECTIVE_CHOICE, "report")
    routine.jump_if_bit_clear(STATE_OPERAND, SECURED_MASK, "next_goal")
    show(SECURED_DIALOGUE_ID)
    routine.jump("finish")
    routine.label("next_goal")
    for index, (operand, mask, _) in enumerate(OBJECTIVES):
        routine.jump_if_bit_clear(operand, mask, f"goal_{index}")
    show(BOSS_OBJECTIVE_ID)
    routine.jump("finish")
    for index in range(len(OBJECTIVES)):
        routine.label(f"goal_{index}")
        show(OBJECTIVE_FIRST_ID + index)
        routine.jump("finish")
    routine.label("report")
    routine.jump_if_not_equal(0x0014, REPORT_CHOICE, "finish")
    routine.jump_if_bit_clear(STATE_OPERAND, SECURED_MASK, "clearance")
    show(SECURED_DIALOGUE_ID)
    routine.jump("finish")
    routine.label("clearance")
    for requirement in CLEARANCES:
        routine.jump_if_bit_clear(requirement.operand, requirement.mask, "missing")
    show(READY_DIALOGUE_ID)
    routine.jump("finish")
    routine.label("missing")
    for requirement in CLEARANCES:
        routine.jump_if_bit_clear(requirement.operand, requirement.mask,
                                  f"show_{requirement.key}")
        routine.jump(f"after_{requirement.key}")
        routine.label(f"show_{requirement.key}")
        show(requirement.dialogue_id)
        routine.label(f"after_{requirement.key}")
    routine.label("finish")
    routine.emit(b"\x01" + u16(CHECKPOINT_FINISH_PC))
    return routine.finish()


def prepare_clearance_report(prepared: base.PreparedDonorField) -> base.PreparedDonorField:
    """Add report/objective choices without replacing the checkpoint's gate."""
    if (prepared.identity.scene, prepared.identity.bundle_id,
            prepared.identity.graphics_id) != (SCENE, 1786, 1787):
        raise ClearanceReportError("Clearance report requires logical ward field 590")
    for label, data, expected in (
        ("script", prepared.components[base.SCRIPT_INDEX], INPUT_SCRIPT_IDENTITY),
        ("dialogue", prepared.components[7], INPUT_DIALOGUE_IDENTITY),
        ("header", prepared.header, INPUT_HEADER_IDENTITY),
        ("bundle", prepared.bundle, INPUT_BUNDLE_IDENTITY),
    ):
        if _identity(data) != expected:
            raise ClearanceReportError(f"Field-590 clearance input {label} changed")

    editor = AtelScript(prepared.components[base.SCRIPT_INDEX])
    if (editor.entity_count != checkpoint.INPUT_ENTITY_COUNT
            or editor.bytecode_size != REPORT_PC
            or editor.get_script_pointer(checkpoint.CONTROLLER_ENTITY,
                                         checkpoint.ACTION_SCRIPT) != ACTION_PC
            or editor.bytecode[ACTION_PC:] != checkpoint.checkpoint_action(ACTION_PC)
            or editor.bytecode[checkpoint.PRODUCTION_GATE_PC:ACTION_PC]
            != checkpoint.PRODUCTION_GATE_BYTES):
        raise ClearanceReportError("Field-590 checkpoint or four-clearance gate changed")
    script = base._patch_bytecode(editor.to_bytes(), MENU_RANGE_PC, b"\x14", b"\x16")
    script = base._patch_bytecode(script, REPORT_BRANCH_TARGET_PC,
                                 u16(CHECKPOINT_FINISH_PC), u16(REPORT_PC))
    editor = AtelScript(script)
    if editor.append_raw_routine(clearance_report_action(REPORT_PC)) != REPORT_PC:
        raise ClearanceReportError("Field-590 clearance append point moved")

    original_dialogue = prepared.components[7]
    blocks = parse_dialogue(original_dialogue).blocks
    if (len(blocks) != CLEARANCES[0].dialogue_id
            or blocks[checkpoint.MENU_DIALOGUE_ID].text != checkpoint.MENU_TEXT):
        raise ClearanceReportError("Field-590 checkpoint dialogue allocation changed")
    for block_id, text, height in (
        (checkpoint.MENU_DIALOGUE_ID, MENU_TEXT, MENU_HEIGHT),
        *((requirement.dialogue_id, requirement.text, 4) for requirement in CLEARANCES),
        (READY_DIALOGUE_ID, READY_TEXT, 4),
        (SECURED_DIALOGUE_ID, SECURED_TEXT, 4),
        *((OBJECTIVE_FIRST_ID + index, text, 4) for index, (_, _, text) in enumerate(OBJECTIVES)),
        (BOSS_OBJECTIVE_ID, BOSS_OBJECTIVE_TEXT, 4),
    ):
        base.mass_driver._validate_authored_manual_wrap(
            {"manual_wrap": True, "width": checkpoint.MENU_WIDTH, "height": height,
             "text": text.replace("<Opcode:01:FF>", "")}, block_id,
        )
    dialogue = replace_dialogue(original_dialogue, {
        "format": REPLACEMENTS_JSON_FORMAT,
        "source_size": len(original_dialogue),
        "source_sha256": _identity(original_dialogue)[1],
        "block_count": len(blocks),
        "replacements": [{"id": checkpoint.MENU_DIALOGUE_ID, "text": MENU_TEXT,
                          "height": MENU_HEIGHT}],
    })
    dialogue = base._append_dialogue_blocks(
        dialogue, tuple(requirement.text for requirement in CLEARANCES)
        + (READY_TEXT, SECURED_TEXT) + tuple(text for _, _, text in OBJECTIVES)
        + (BOSS_OBJECTIVE_TEXT,), width=checkpoint.MENU_WIDTH, height=4,
    )
    components = list(prepared.components)
    components[base.SCRIPT_INDEX] = editor.to_bytes()
    components[7] = dialogue
    bundle = build_field_preserving(
        prepared.bundle, components, (base.SCRIPT_INDEX, 7), compact_changed=True,
    )
    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise ClearanceReportError("Field-590 clearance report failed stream round trip")
    return replace(
        prepared, components=tuple(components), header=reparsed.header, bundle=bundle,
        role=prepared.role + "; read-only production clearance report with route guidance",
    )


def clearance_report_metadata() -> dict[str, object]:
    return {
        "field": SCENE,
        "entity": checkpoint.CONTROLLER_ENTITY,
        "script": checkpoint.ACTION_SCRIPT,
        "action_pc": ACTION_PC,
        "report_pc": REPORT_PC,
        "menu_dialogue_id": checkpoint.MENU_DIALOGUE_ID,
        "menu_height": MENU_HEIGHT,
        "choices": ["Enter production", "Restore HP and EP", "Save progress",
                    "Leave", "Clearance report", "Next objective"],
        "report_choice": REPORT_CHOICE,
        "objective_choice": OBJECTIVE_CHOICE,
        "objectives": [{"operand": operand, "mask": mask, "dialogue_id": OBJECTIVE_FIRST_ID + index}
                       for index, (operand, mask, _) in enumerate(OBJECTIVES)],
        "boss_objective_dialogue_id": BOSS_OBJECTIVE_ID,
        "requirements": [{"flag": requirement.key, "operand": requirement.operand,
                          "mask": requirement.mask, "dialogue_id": requirement.dialogue_id,
                          "source_fields": list(requirement.source_fields)}
                         for requirement in CLEARANCES],
        "ready_dialogue_id": READY_DIALOGUE_ID,
        "secured_dialogue_id": SECURED_DIALOGUE_ID,
        "production_gate_pc": checkpoint.PRODUCTION_GATE_PC,
        "production_gate_unchanged": True,
        "writes_progression_state": False,
        "added_actors": 0,
        "geometry_changed": False,
    }
