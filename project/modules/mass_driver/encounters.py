"""Native on-foot encounter policy for the Mass Driver interior.

The reusable field art brings unrelated and sometimes placeholder encounter
tables with it. Only six launch-works passages run random battles. Their three
formations are exact native Zeboim records, using Shellbelle and Hammerhead;
every other random weight is zero, including the fixed Guardian's slot 15.

No enemy stats, AI, models, rewards, persistent state, or fixed-battle records
are changed here. Runtime acceptance must still measure frequency and balance
with the release party. The native F7 timer counts movement-input ticks, not
wall-clock seconds; its second operand is the number of random timer entries.
"""

from __future__ import annotations

import hashlib
import struct
from types import MappingProxyType
from typing import Any

from shared.tools.atel_primitives import AtelEncodingError, immediate
from shared.tools.xgdialog import PLAIN_DECODE
from shared.tools.xgencounter import EncounterTable, FORMATION_COUNT, FORMATION_SIZE
from shared.tools.xgscript import AtelScript


class MassDriverEncounterError(AtelEncodingError):
    """Raised when a Mass Driver encounter or provenance contract drifts."""


MASS_DRIVER_FIELD_IDS = frozenset((
    360, 361, 362, 363, 364, 366, 367, 368, 369, 370, 371, 372,
    375, 376, 377, 378, 379, 382, 383, 384, 385, 386, 387,
    720, 721, 722, 723, 724, 725, 726, 727, 728, 729,
))

# Bytecode-relative PCs in the checked donors, BEFORE later room transforms.
# In particular, field 726's extra entries/controllers move its eventual code.
CORRIDOR_INITIALIZER_PCS = MappingProxyType({
    727: 0x0025,  # Three-door operations junction.
    372: 0x002C,  # Four-door service hub.
    723: 0x0017,  # Sealed stair connector on the archive branch.
    375: 0x0017,  # Main post-auxiliary stair connector.
    387: 0x001E,  # Vertical service connector.
    726: 0x001B,  # Launch-support hall, outside the individual archives.
})
COMBAT_FIELD_IDS = frozenset(CORRIDOR_INITIALIZER_PCS)
SAFE_FIELD_IDS = MASS_DRIVER_FIELD_IDS - COMBAT_FIELD_IDS
FIXED_BOSS_SLOT = 15
ENCOUNTER_MOVEMENT_TICKS = 900
ENCOUNTER_TIMER_COUNT = 1
NATIVE_DISABLED_INITIALIZER = b"\xF7" + immediate(900) + immediate(0)
DISABLED_INITIALIZER = b"\x14" * 5
ACTIVE_INITIALIZER = (
    b"\xF7" + immediate(ENCOUNTER_MOVEMENT_TICKS)
    + immediate(ENCOUNTER_TIMER_COUNT)
)

ENEMY_RESOURCE_SET = 0x06
ENEMY_STATS_CANONICAL_ID = 2630
ENEMY_MODELS_CANONICAL_ID = 2631
ENEMY_STATS_SIZE = 5775
ENEMY_MODELS_SIZE = 144432
ENEMY_STATS_SHA256 = "dd0567993af22f222652c756b77df29c785bd883e655e5c06f4a7689b0bcdf15"
ENEMY_MODELS_SHA256 = "b70b7437dffac87e591ed3a452fc20758d0fd02999d47b32130111b10c97a589"
ENEMY_NAMES = ("Shellbelle", "Hammerhead")
ENEMY_HP = (680, 180)

# Exact records 0-2 of native Zeboim field 372/373. The native arena, flags,
# layout variants, slots and positions are kept together, rather than mixing
# enemy selectors into a different donor arena. None has the no-Escape bit.
CURATED_FORMATIONS = (
    bytes.fromhex(
        "06 40 17 00 00 00 00 00 00 00 FF FF FF FF FF FF "
        "00 00 00 00 FF FF FF FF 00 00 00 00 FF FF FF FF"
    ),
    bytes.fromhex(
        "06 40 17 00 02 02 02 00 01 01 01 01 FF FF FF FF "
        "00 00 00 00 00 00 00 00 02 02 02 02 FF FF FF FF"
    ),
    bytes.fromhex(
        "06 40 17 00 01 01 01 00 00 01 01 01 FF FF FF FF "
        "00 00 00 00 FF FF FF FF 00 01 01 01 FF FF FF FF"
    ),
)
CURATED_WEIGHTS = (2, 2, 2)


def _check_field(field_id: int) -> None:
    if type(field_id) is not int or field_id not in MASS_DRIVER_FIELD_IDS:
        raise MassDriverEncounterError(
            f"Unknown Mass Driver encounter field: {field_id!r}"
        )


def encounter_policy(field_id: int) -> dict[str, Any]:
    """Return serializable release/audit metadata for one known field."""

    _check_field(field_id)
    active = field_id in COMBAT_FIELD_IDS
    return {
        "field": field_id,
        "random_encounters_enabled": active,
        "movement_tick_window": ENCOUNTER_MOVEMENT_TICKS if active else 0,
        "encounter_timer_count": ENCOUNTER_TIMER_COUNT if active else 0,
        "weighted_slots": list(range(3)) if active else [],
        "weights": list(CURATED_WEIGHTS) if active else [],
        "enemy_resource_set": ENEMY_RESOURCE_SET if active else None,
        "enemy_stats_canonical_id": ENEMY_STATS_CANONICAL_ID if active else None,
        "enemy_models_canonical_id": ENEMY_MODELS_CANONICAL_ID if active else None,
        "enemies": list(ENEMY_NAMES) if active else [],
        "fixed_boss_slot": FIXED_BOSS_SLOT,
        "fixed_boss_random_weight": 0,
    }


def validate_enemy_resource_pair(stats: bytes, models: bytes) -> dict[str, Any]:
    """Prove the native stats/AI and model pair actually used by these rows.

    Both payloads were extracted from the clean US Disc 2 custom FAT. The
    normal-combat 2630 override already installed by this module is identical
    to that clean resource, including native HP, rewards and AI.
    """

    for canonical_id, payload, size, digest in (
        (ENEMY_STATS_CANONICAL_ID, stats, ENEMY_STATS_SIZE, ENEMY_STATS_SHA256),
        (ENEMY_MODELS_CANONICAL_ID, models, ENEMY_MODELS_SIZE, ENEMY_MODELS_SHA256),
    ):
        if not isinstance(payload, (bytes, bytearray, memoryview)):
            raise MassDriverEncounterError(
                f"Enemy resource {canonical_id} must be bytes-like"
            )
        if len(payload) != size or hashlib.sha256(payload).hexdigest() != digest:
            raise MassDriverEncounterError(
                f"Native Zeboim enemy resource {canonical_id} failed size/SHA-256 validation"
            )
    # Check the meaning of the selected definitions alongside their hashes.
    strings = struct.unpack_from("<H", stats, 0x30)[0]
    names = []
    hp = []
    for definition in range(2):
        offset = struct.unpack_from("<H", stats, strings + 6 + definition * 2)[0]
        name = bytes(stats[strings + offset:]).split(b"\x00", 1)[0]
        names.append("".join(PLAIN_DECODE[c] for c in name))
        hp.append(struct.unpack_from("<HH", stats, 0x32 + definition * 0x170 + 0x4C))
    if tuple(names) != ENEMY_NAMES or tuple(hp) != tuple((n, n) for n in ENEMY_HP):
        raise MassDriverEncounterError("Native Zeboim enemy names/HP do not match their definitions")
    return {
        "resource_set": ENEMY_RESOURCE_SET,
        "stats_canonical_id": ENEMY_STATS_CANONICAL_ID,
        "stats_size": ENEMY_STATS_SIZE,
        "stats_sha256": ENEMY_STATS_SHA256,
        "models_canonical_id": ENEMY_MODELS_CANONICAL_ID,
        "models_size": ENEMY_MODELS_SIZE,
        "models_sha256": ENEMY_MODELS_SHA256,
        "enemy_names": names,
        "enemy_hp": list(ENEMY_HP),
        "enemy_resources_modified": False,
    }


def configure_encounter_initializer(data: bytes, field_id: int, pc: int) -> bytes:
    """Replace the checked donor F7 at its original PC, without moving code.

    Call this in place of the builder's old neutralizer, before any expansion
    of script headers or entry records. Quiet fields retain five native 0x14
    DISABLE_RANDOM_BATTLES instructions. No extra director or state is needed.
    """

    _check_field(field_id)
    if type(pc) is not int or pc < 0:
        raise MassDriverEncounterError(f"Invalid encounter initializer PC: {pc!r}")
    if field_id in COMBAT_FIELD_IDS and pc != CORRIDOR_INITIALIZER_PCS[field_id]:
        raise MassDriverEncounterError(
            f"Field {field_id} encounter initializer PC drifted: 0x{pc:04X}"
        )
    editor = AtelScript(data)
    expected = ACTIVE_INITIALIZER if field_id in COMBAT_FIELD_IDS else DISABLED_INITIALIZER
    current = editor.bytecode[pc:pc + 5]
    if current not in (NATIVE_DISABLED_INITIALIZER, DISABLED_INITIALIZER, expected):
        raise MassDriverEncounterError(
            f"Field {field_id} encounter initializer at 0x{pc:04X} "
            f"does not match the checked donor: {current.hex(' ')}"
        )
    result = bytearray(data)
    absolute = editor.bytecode_offset + pc
    result[absolute:absolute + 5] = expected
    # Validate the unmodified pointer table against the same-size result.
    AtelScript(result)
    if len(result) != len(data):
        raise MassDriverEncounterError("Encounter initializer changed script size")
    return bytes(result)


def curate_encounter_table(data: bytes, field_id: int) -> bytes:
    """Keep three native on-foot rows in passages; suppress every other weight.

    All formation bytes beyond selected slots 0-2 are preserved, including
    Guardian 15. Quiet fields preserve ALL formation bytes. Clear weights even
    on formerly inert donors so a carried or later-restored timer cannot expose
    a placeholder, mixed-scale formation, or random Guardian.
    """

    _check_field(field_id)
    table = EncounterTable(data)
    if field_id in COMBAT_FIELD_IDS:
        for index, expected in enumerate(CURATED_FORMATIONS):
            if table.formation(index) != expected:
                raise MassDriverEncounterError(
                    f"Field {field_id} native Zeboim formation {index} drifted"
                )
    for index in range(FORMATION_COUNT):
        table.set_weight(index, CURATED_WEIGHTS[index] if field_id in COMBAT_FIELD_IDS and index < 3 else 0)
    result = table.to_bytes()
    verify_encounter_table(result, field_id, original_data=data)
    return result


def verify_encounter_table(
    data: bytes, field_id: int, original_data: bytes | None = None,
) -> dict[str, Any]:
    """Reject unsafe weights/rows and optionally prove formation preservation."""

    _check_field(field_id)
    table = EncounterTable(data)
    active = field_id in COMBAT_FIELD_IDS
    expected_weights = CURATED_WEIGHTS + (0,) * 13 if active else (0,) * 16
    if table.weights != expected_weights:
        raise MassDriverEncounterError(f"Field {field_id} random encounter weights drifted")
    if active:
        for index, expected in enumerate(CURATED_FORMATIONS):
            formation = table.formation(index)
            if formation != expected:
                raise MassDriverEncounterError(f"Field {field_id} curated formation {index} drifted")
            if struct.unpack_from("<H", formation)[0] != 0x4000 | ENEMY_RESOURCE_SET:
                raise MassDriverEncounterError("Curated encounter selected a different enemy resource")
            if formation[1] & 0x80:
                raise MassDriverEncounterError("Random encounter must allow ordinary Escape")
            for slot in range(8):
                enemy = table.get_enemy(index, slot)
                if enemy.enemy_id != 0x7F and (enemy.is_gear or enemy.enemy_id not in (0, 1)):
                    raise MassDriverEncounterError("Random encounter is not a selected on-foot Zeboim enemy")
    if original_data is not None:
        original = EncounterTable(original_data)
        for index in range(FORMATION_COUNT):
            if table.formation(index) != original.formation(index):
                raise MassDriverEncounterError(
                    f"Field {field_id} encounter policy changed formation {index} bytes"
                )
    return encounter_policy(field_id)
