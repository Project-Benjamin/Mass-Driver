"""Provide a service directory, permanent closure, and resonance directions.

Apply after the reviewed donor dialogue layout and V238 helpers, before music.
Only two existing dialogue blocks change; native audio, scripts, and flags stay
byte-identical to their checked inputs.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib

from modules.soylent_system import base, build as campaign
from shared.tools.xgdialog import parse_dialogue, replace_dialogue, REPLACEMENTS_JSON_FORMAT
from shared.tools.xgfield import build_field_preserving, parse_field


INPUT_IDENTITIES = {
    565: {
        "script": (4931, "6856522f442c67b5d752ca9c099cc367d3501c7f40a3137a1efad721a5f11510"),
        "dialogue": (1230, "4e2ad270c37d5f56c3d62703937da92b6ae209d36aa35efd060b595d91a1159b"),
        "header": (1024, "97b05e0963a89674c3376b8c6f807a3ff271564e042679faa8fa3e0a363ab3a4"),
        "bundle": (82040, "eeb26198ff2d43e6775b49da6fe1a98cb30a7a4ab125b6edcf5c2c124c2775b3"),
    },
    589: {
        "script": (4223, "0bcee861d4b19f1fdbfb2981534b31e99ace293b4e26ffc8fd3ce35947389284"),
        "dialogue": (257, "9779420312d76a566ee09878bbb47381ddd8ab723d9b4c8880415155cb3166e9"),
        "header": (832, "a0f94069cf8417a2fa3a7da190b02e4051bd6715a718ae0c9e8a29fc0368db0d"),
        "bundle": (50896, "da5bdf1530305d658836c910c6d2cf450819bbb202b59c8bc64ee7291811e36c"),
    },
}
DIALOGUE_IDS = {565: 16, 589: 5}
ORIGINAL_TEXT = {
    565: "DEEP SERVICE ACCESS SEALED\nThis transfer route is not\ncurrently authorized.<Close>",
    589: "RESONANCE PATTERN RECORDED\nRepeat the five directions at\nthe service input panel.<Close>",
}
TEXT = {
    565: (
        "DECOMMISSIONED SHAFT\n"
        "This transfer route is\n"
        "permanently sealed. Use the\n"
        "other service passages.<New>"
        "SERVICE DIRECTORY\n"
        "Intake Reception connects\n"
        "the patient rooms, clinic\n"
        "and Classification Archive.<New>"
        "Organic Resonance Annex:\n"
        "hear the five-tone pattern.\n"
        "Use the Service Manifold\n"
        "input panel to enter it.<New>"
        "Clinical Interface\n"
        "Scanner Annex: arm the\n"
        "living-subject cutoff.\n"
        "Quarantine: check readings.<New>"
        "Stabilization Ward:\n"
        "recovery, saving and the\n"
        "production entrance. Its\n"
        "control lists your next task.<Close>"
    ),
    589: (
        "RESONANCE PATTERN RECORDED\n"
        "Up, Down, Up, Left, Right.\n"
        "Repeat this sequence at the\n"
        "Service Manifold input panel.<Close>"
    ),
}
NATIVE_PATTERN = ("Up", "Down", "Up", "Left", "Right")


class FinalGuidanceError(base.SurfaceSoylentBuildError):
    """Raised when either reviewed donor's guidance foundation changes."""


def _identity(data: bytes) -> tuple[int, str]:
    return len(data), hashlib.sha256(data).hexdigest()


def prepare_final_guidance(prepared: base.PreparedDonorField) -> base.PreparedDonorField:
    scene = prepared.identity.scene
    if scene not in INPUT_IDENTITIES:
        return prepared
    expected = base.DONOR_BY_SCENE[scene]
    if (prepared.identity.bundle_id, prepared.identity.graphics_id) != (
        expected.bundle_id, expected.graphics_id,
    ):
        raise FinalGuidanceError(f"Field {scene} final-guidance resource IDs changed")
    for label, data in (
        ("script", prepared.components[base.SCRIPT_INDEX]),
        ("dialogue", prepared.components[7]),
        ("header", prepared.header),
        ("bundle", prepared.bundle),
    ):
        if _identity(data) != INPUT_IDENTITIES[scene][label]:
            raise FinalGuidanceError(f"Field {scene} final-guidance input {label} changed")

    dialogue = prepared.components[7]
    blocks = parse_dialogue(dialogue).blocks
    block_id = DIALOGUE_IDS[scene]
    block = blocks[block_id]
    if (block.width, block.height, block.text) != (58, 4, ORIGINAL_TEXT[scene]):
        raise FinalGuidanceError(f"Field {scene} final-guidance dialogue target changed")
    base.mass_driver._validate_authored_manual_wrap(
        {"manual_wrap": True, "width": block.width, "height": block.height,
         "text": TEXT[scene]}, block_id,
    )
    dialogue = replace_dialogue(dialogue, {
        "format": REPLACEMENTS_JSON_FORMAT,
        "source_size": len(dialogue),
        "source_sha256": _identity(dialogue)[1],
        "block_count": len(blocks),
        "replacements": [{"id": block_id, "text": TEXT[scene]}],
    })
    issues = campaign._campaign_dialogue_layout_issues(parse_dialogue(dialogue).blocks[block_id])
    if issues:
        raise FinalGuidanceError(f"Field {scene} final-guidance dialogue exceeds grid: {issues}")
    components = list(prepared.components)
    components[7] = dialogue
    bundle = build_field_preserving(prepared.bundle, components, (7,), compact_changed=True)
    reparsed = parse_field(bundle)
    if tuple(part.data for part in reparsed.parts) != tuple(components):
        raise FinalGuidanceError(f"Field {scene} final-guidance stream round trip failed")
    return replace(
        prepared, components=tuple(components), header=reparsed.header, bundle=bundle,
        role=prepared.role + "; final service-closure and native resonance guidance",
    )


def final_guidance_metadata() -> dict[str, object]:
    return {
        "script_changes": False,
        "progression_changes": False,
        "service_closure": {
            "field": 565, "entity": 7, "dialogue_id": DIALOGUE_IDS[565],
            "permanently_sealed": True, "text": TEXT[565],
            "service_directory": True,
        },
        "resonance_clue": {
            "field": 589, "entity": 9, "dialogue_id": DIALOGUE_IDS[589],
            "native_pattern": list(NATIVE_PATTERN), "text": TEXT[589],
            "authorization_source": "native field-565 input panel only",
        },
    }
