"""Add a recovery/save menu to the existing stabilization production door.

Apply after campaign donor dialogue layout and before its music pass.  The
original four-clearance production gate remains the only entry route.  No
actors, models, collision targets, progression state, or native doors change.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib

import modules.soylent_system.base as surface
from shared.tools.atel_primitives import u16
from shared.tools.xgdialog import parse_dialogue
from shared.tools.xgfield import build_field_preserving, parse_field
from shared.tools.xgscript import AtelScript as ScriptEditor


SCENE = 590
CONTROLLER_ENTITY = 6
ACTION_SCRIPT = 2
CONTROLLER_INIT_PC = 0x0C91
PRODUCTION_GATE_PC = 0x0D31
INPUT_BYTECODE_SIZE = 0x0D6D
INPUT_ENTITY_COUNT = 25
INPUT_SCRIPT_IDENTITY = (
    5169, "6bf51c67bbe7871cb9fbecde8d47d686eeccbe8e464efae9bd1da8bd75335b2a",
)
INPUT_DIALOGUE_IDENTITY = (
    181, "6d19d08fc0fb9f361b04d6d5e735282f84196c6b7f45450aaae8d1ae15c82325",
)
INPUT_HEADER_IDENTITY = (
    944, "6ca5bfae424e92084131545cb045bd71ac862c429ff55c8975445aa747bce6b0",
)
INPUT_BUNDLE_IDENTITY = (
    85000, "898b0d287277e9f3e6e0a4ecc1f9545cd8b7dbd28be9508af63ae3b9e24cdb30",
)
PRODUCTION_GATE_BYTES = bytes.fromhex(
    "02 1A 02 01 00 46 54 0D 02 1E 02 00 02 46 54 0D "
    "02 FA 03 00 01 46 54 0D 02 FA 03 00 08 46 54 0D "
    "01 0E 0D 33 FE 54 31 20 00 62 0D 26 01 80 01 57 0D "
    "26 01 80 F5 02 00 01 9C FE 53 00"
)
MENU_DIALOGUE_ID = 3
RESTORED_DIALOGUE_ID = 4
MENU_TEXT = (
    "STABILIZATION WARD\n"
    "<Opcode:01:FF>    Enter production\n"
    "    Restore HP and EP\n"
    "    Save progress\n"
    "    Leave<Close>"
)
RESTORED_TEXT = "HP and EP fully restored.<Close>"
MENU_WIDTH = 58
MENU_HEIGHT = 5

# Native one-byte operations restore all eleven character records to their
# maximum HP/EP. Verified against OP_RESTORE_HP / OP_RESTORE_MP and the 79/7A
# entries in Noah's field opcode table; there is no runtime dependency on that
# reference checkout. This deliberately does not repair Gears or alter status.
RESTORE_HP_EP = b"\x79\x7A"
# Same native handoff retained by the field-622 save console. FE87 means that
# the menu closed, not that the user completed a memory-card save.
NATIVE_SAVE_HANDOFF = bytes.fromhex("FE 99 00 FE 55 FE 87")


class CheckpointError(surface.SurfaceSoylentBuildError):
    """Raised when the checkpoint's frozen donor or gate contract changes."""


def _identity(data: bytes) -> tuple[int, str]:
    return len(data), hashlib.sha256(data).hexdigest()


def checkpoint_action(routine_pc: int) -> bytes:
    """Build an explicit-X, cancel-safe four-choice native menu."""
    routine = surface.mass_driver._RoutineBuilder(routine_pc)

    def release_cross() -> None:
        routine.emit(surface.mass_driver._wait_for_pad_release(
            surface.mass_driver.PAD_MASK_CROSS, routine.pc,
        ))
        routine.emit(surface.mass_driver._wait())

    routine.emit(b"\x33\xFE\x54")
    release_cross()
    routine.emit(surface.mass_driver._choice_dialog(MENU_DIALOGUE_ID))
    # The title is line zero; native selections are absolute lines 1--4.
    routine.emit(b"\xA9\x14\x9C")
    release_cross()
    routine.jump_if_not_equal(0x0014, 1, "check_restore")
    routine.emit(b"\xFE\x53\x01" + u16(PRODUCTION_GATE_PC))

    routine.label("check_restore")
    routine.jump_if_not_equal(0x0014, 2, "check_save")
    routine.emit(RESTORE_HP_EP)
    routine.emit(b"\xF5" + u16(RESTORED_DIALOGUE_ID) + b"\x01\x9C")
    routine.jump("finish")

    routine.label("check_save")
    routine.jump_if_not_equal(0x0014, 3, "finish")
    routine.emit(NATIVE_SAVE_HANDOFF)

    routine.label("finish")
    # Also drain a restoration receipt or the native menu's closing press.
    # Leave, Cancel, and unexpected selections never touch the gate or stats.
    release_cross()
    routine.emit(b"\xFE\x53\x00")
    return routine.finish()


def checkpoint_metadata() -> dict[str, object]:
    """Describe the interaction and its deliberate separation from clearance."""
    return {
        "field": SCENE,
        "entity": CONTROLLER_ENTITY,
        "script": ACTION_SCRIPT,
        "menu_dialogue_id": MENU_DIALOGUE_ID,
        "restored_dialogue_id": RESTORED_DIALOGUE_ID,
        "menu": MENU_TEXT,
        "choices": ["Enter production", "Restore HP and EP", "Save progress", "Leave"],
        "production_gate_pc": PRODUCTION_GATE_PC,
        "production_gate_unchanged": True,
        "restoration_opcodes": [0x79, 0x7A],
        "restoration_scope": "HP and EP of all eleven native character records",
        "native_save_handoff": NATIVE_SAVE_HANDOFF.hex(" ").upper(),
        "save_cancel_policy": "Return to the ward without changing clearance or healing",
        "writes_progression_state": False,
        "added_actors": 0,
        "geometry_changed": False,
        "requires_fresh_cross": True,
    }


def prepare_checkpoint(prepared: surface.PreparedDonorField) -> surface.PreparedDonorField:
    """Wrap the audited field-590 e6 gate without replacing its native action."""
    if (prepared.identity.scene, prepared.identity.bundle_id,
            prepared.identity.graphics_id) != (SCENE, 1786, 1787):
        raise CheckpointError("Checkpoint requires logical stabilization field 590")
    script = prepared.components[surface.SCRIPT_INDEX]
    for label, data, expected in (
        ("script", script, INPUT_SCRIPT_IDENTITY),
        ("dialogue", prepared.components[7], INPUT_DIALOGUE_IDENTITY),
        ("header", prepared.header, INPUT_HEADER_IDENTITY),
        ("bundle", prepared.bundle, INPUT_BUNDLE_IDENTITY),
    ):
        if _identity(data) != expected:
            raise CheckpointError(f"Field-590 checkpoint input {label} changed")
    editor = ScriptEditor(script)
    if (editor.entity_count != INPUT_ENTITY_COUNT
            or editor.bytecode_size != INPUT_BYTECODE_SIZE
            or editor.get_script_pointer(CONTROLLER_ENTITY, 0) != CONTROLLER_INIT_PC
            or editor.get_script_pointer(CONTROLLER_ENTITY, ACTION_SCRIPT) != PRODUCTION_GATE_PC
            or editor.bytecode[PRODUCTION_GATE_PC:] != PRODUCTION_GATE_BYTES):
        raise CheckpointError("Field-590 production controller or four-clearance gate changed")

    dialogue = prepared.components[7]
    if len(parse_dialogue(dialogue).blocks) != MENU_DIALOGUE_ID:
        raise CheckpointError("Field-590 checkpoint dialogue allocation changed")
    for text, block_id, height in (
        (MENU_TEXT, MENU_DIALOGUE_ID, MENU_HEIGHT),
        (RESTORED_TEXT, RESTORED_DIALOGUE_ID, 2),
    ):
        surface.mass_driver._validate_authored_manual_wrap(
            {"manual_wrap": True, "width": MENU_WIDTH, "height": height,
             "text": text.replace("<Opcode:01:FF>", "")},
            block_id,
        )
        dialogue = surface._append_dialogue_blocks(
            dialogue, (text,), width=MENU_WIDTH, height=height,
        )
    editor.append_and_repoint(
        CONTROLLER_ENTITY, ACTION_SCRIPT, checkpoint_action(editor.bytecode_size),
    )
    components = list(prepared.components)
    components[surface.SCRIPT_INDEX] = editor.to_bytes()
    components[7] = dialogue
    bundle = build_field_preserving(
        prepared.bundle, components, (surface.SCRIPT_INDEX, 7), compact_changed=True,
    )
    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise CheckpointError("Field-590 checkpoint failed decoded-stream round trip")
    return replace(
        prepared,
        role=prepared.role + "; production-door recovery and native-save checkpoint",
        components=tuple(components),
        header=reparsed.header,
        bundle=bundle,
    )
