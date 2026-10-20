"""Keep the diverted Sorting line visibly stationary on subsequent visits.

Apply after production controls, before music. Native field 624 actors 5--76
are the biological material carried along the conveyor paths: their actor
records reference visible model parts 8--11, eighteen of each. Only their
update entry points change. Before commitment the exact native movement loops
run; after commitment the updates keep their native initial placement and
stop before starting any movement. Four updates have explicit native position
setup; those prefixes still run before stopping, avoiding placeholder overlap.
commit occurs immediately before leaving the field, so the effect appears on
reentry. Models, initial positions, controls, doors, sound and music are exact.

Core 626 is deliberately unchanged: its paired carrier/rotation actors have
no checked mapping that distinguishes production from active containment.
"""

from __future__ import annotations

import hashlib

from modules.soylent_system import base, build as campaign
from shared.tools.xgscript import AtelScript


SCENE = 624
ENTITIES = tuple(range(5, 77))
COMPLETION_MASK = 1 << 12
NATIVE_REGION = (0x00B4, 0x12F0)
NATIVE_REGION_SHA256 = "41191d16a83a9a17af7879ae9ca7d33c521d93e03a082fce779b82960373a67b"
ACTOR_RECORDS_SHA256 = "cfff03f6dd9c4f8740df162116076f054583427d30045f83c023d7a5bacde892"
MODELS_SHA256 = "2851fe5ba5707c668e60e30f12616cc50f1d23a73e19a5fa04a619b497f9fed6"
# Every checked initializer is BC 2A 21 00 82 00; its update begins six bytes
# later. Fixed native PCs keep this pass independent of appended menu changes.
NATIVE_INIT_PCS = (
    405, 430, 455, 491, 516, 541, 597, 622, 647, 672, 708, 733,
    758, 783, 808, 844, 869, 894, 919, 955, 980, 1005, 1324, 1435,
    1537, 1639, 1741, 1832, 1923, 2014, 2105, 2196, 2287, 2367,
    2436, 2505, 2574, 2643, 2701, 2759, 2817, 2864, 2911, 2947,
    2983, 3008, 3119, 3221, 3323, 3414, 3492, 3561, 3619, 3666,
    3702, 3738, 3763, 3788, 3890, 3992, 4094, 4185, 4276, 4367,
    4447, 4516, 4585, 4643, 4701, 4748, 4784, 4820,
)
# FE 1C sets immediate X, Z, Y before any movement. The remaining 68 actors
# already have their proper nonzero starting locations in their header records.
NATIVE_POSITION_SETUPS = {
    0x0223: bytes.fromhex("FE 1C 00 00 75 F9 00 00 E0"),  # entity 10
    0x0532: bytes.fromhex("FE 1C B7 06 13 FD 00 00 E0"),  # entity 27
    0x0BC6: bytes.fromhex("FE 1C 07 06 62 FC 00 00 E0"),  # entity 50
    0x0D5C: bytes.fromhex("FE 1C CC FE 9E 03 00 00 E0"),  # entity 54
}


def shutdown_update(routine_pc: int, native_update_pc: int) -> bytes:
    """Read the existing commit bit; never write puzzle or progression state."""
    routine = base.mass_driver._RoutineBuilder(routine_pc)
    routine.jump_if_bit_clear(campaign.STATE_OPERAND, COMPLETION_MASK, "moving")
    routine.emit(NATIVE_POSITION_SETUPS.get(native_update_pc, b""))
    routine.emit(b"\x00")
    routine.label("moving")
    routine.emit(campaign._jump(native_update_pc))
    return routine.finish()


def prepare_shutdown_visuals(prepared: base.PreparedField) -> base.PreparedField:
    if prepared.spec.identity.scene != SCENE:
        return prepared
    editor = AtelScript(prepared.components[campaign.SCRIPT_INDEX])
    start, end = NATIVE_REGION
    if hashlib.sha256(editor.bytecode[start:end]).hexdigest() != NATIVE_REGION_SHA256:
        raise campaign.SurfaceCampaignBuildError("Sorting native conveyor routines changed")
    actors = prepared.header[0x190 + ENTITIES[0] * 16:0x190 + (ENTITIES[-1] + 1) * 16]
    if (hashlib.sha256(actors).hexdigest() != ACTOR_RECORDS_SHA256
            or hashlib.sha256(prepared.components[2]).hexdigest() != MODELS_SHA256):
        raise campaign.SurfaceCampaignBuildError("Sorting conveyor actor/model mapping changed")
    for entity, native_init_pc in zip(ENTITIES, NATIVE_INIT_PCS, strict=True):
        native_update_pc = native_init_pc + 6
        if (editor.get_script_pointer(entity, 0) != native_init_pc
                or editor.get_script_pointer(entity, 1) != native_update_pc
                or editor.bytecode[native_init_pc:native_update_pc] != bytes.fromhex("BC 2A 21 00 82 00")):
            raise campaign.SurfaceCampaignBuildError("Sorting conveyor entry points changed")
        editor.append_and_repoint(entity, 1, shutdown_update(editor.bytecode_size, native_update_pc))
    return campaign._rebuild_field(
        prepared, editor=editor,
        role_suffix="diverted biological conveyor motion remains stopped on reentry",
    )


def shutdown_visuals_metadata(prepared: base.PreparedField) -> dict[str, object]:
    editor = AtelScript(prepared.components[campaign.SCRIPT_INDEX])
    return {
        "field": SCENE,
        "entities": list(ENTITIES),
        "native_models": [8, 9, 10, 11],
        "update_pcs": [editor.get_script_pointer(entity, 1) for entity in ENTITIES],
        "completion_operand": campaign.STATE_OPERAND,
        "completion_mask": COMPLETION_MASK,
        "uncommitted": "Exact native biological conveyor movement",
        "committed": "Biological material remains stationary at its native initial positions on reentry",
        "native_position_setup_entities": [10, 27, 50, 54],
        "timing": "The persistent bit commits immediately before the forward field transition",
        "writes_puzzle_or_progression_state": False,
        "initializers_controls_doors_models_music": "Unchanged",
        "core_containment": "Field 626 visuals unchanged; no unverified production/containment mapping",
    }
