"""Retire the doctor and patient from the Quarantine keycard room only.

Run after the existing exam-room, door-clearance and dialogue passes, before
music. Keep the checked foundation's entity ordering, assets and bytecode;
retire the two humanoids by pointing every slot at its existing shared STOP.
This uses the same non-instantiation policy as the empty-clinic foundation.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib

import modules.soylent_system.base as base
from shared.tools.xgfield import build_field_preserving, parse_field
from shared.tools.xgscript import AtelScript


SCENE = 593
RETIRED_NPC_ENTITIES = (13, 16)
SHARED_STOP_PC = 0x068C
INPUT_ENTITY_COUNT = 21
INPUT_BYTECODE_SIZE = 0x07F0
INPUT_SCRIPT_IDENTITY = (
    3508, "0187d5c54fe447e814f6540812385975c24acab4737d9a9923c00eace1c04366",
)
INPUT_HEADER_IDENTITY = (
    960, "7c31d2c3824cbde729d39be98092c6dd8e567aefe7e75337330a390a09c07d87",
)
INPUT_BUNDLE_IDENTITY = (
    69664, "c91e5f85035d13165eb59d0c31d7cec6628199c4fafe710b145f2a3b50129f61",
)
NPC_ACTIVE_POINTERS = {
    (13, 0): 0x0745,
    (13, 2): 0x078B,
    (16, 0): 0x0764,
    (16, 2): 0x0797,
}


class KeycardRoomError(base.SurfaceSoylentBuildError):
    """Raised when field 593 no longer matches the checked foundation."""


def _identity(data: bytes) -> tuple[int, str]:
    return len(data), hashlib.sha256(data).hexdigest()


def prepare_keycard_room(prepared: base.PreparedDonorField) -> base.PreparedDonorField:
    """Remove both NPCs without changing the keycard, party or door behavior."""

    if prepared.identity.scene != SCENE:
        return prepared
    script = prepared.components[base.SCRIPT_INDEX]
    for label, data, expected in (
        ("script", script, INPUT_SCRIPT_IDENTITY),
        ("header", prepared.header, INPUT_HEADER_IDENTITY),
        ("bundle", prepared.bundle, INPUT_BUNDLE_IDENTITY),
    ):
        if _identity(data) != expected:
            raise KeycardRoomError(f"Field-593 NPC retirement input {label} changed")

    editor = AtelScript(script)
    if (editor.entity_count != INPUT_ENTITY_COUNT
            or editor.bytecode_size != INPUT_BYTECODE_SIZE
            or editor.bytecode[SHARED_STOP_PC] != 0):
        raise KeycardRoomError("Field-593 NPC retirement layout or shared STOP changed")
    for entity in RETIRED_NPC_ENTITIES:
        for slot in range(32):
            expected = NPC_ACTIVE_POINTERS.get((entity, slot), SHARED_STOP_PC)
            if editor.get_script_pointer(entity, slot) != expected:
                raise KeycardRoomError(f"Field-593 e{entity}:s{slot} NPC pointer changed")
            editor.set_script_pointer(entity, slot, SHARED_STOP_PC)

    components = list(prepared.components)
    components[base.SCRIPT_INDEX] = editor.to_bytes()
    bundle = build_field_preserving(
        prepared.bundle, components, (base.SCRIPT_INDEX,), compact_changed=True,
    )
    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise KeycardRoomError("Field-593 NPC retirement failed decoded-stream round trip")
    return replace(
        prepared,
        role=(
            "NPC-empty Quarantine keycard examination room; preserved party, "
            "bed, three facing-gated side-computer X carriers and stored medical "
            "record; explicitly accepted one-time Quarantine keycard; native "
            "animated return to field 621/p9; retail events unreachable; "
            "random encounters disabled"
        ),
        components=tuple(components),
        header=reparsed.header,
        bundle=bundle,
    )
