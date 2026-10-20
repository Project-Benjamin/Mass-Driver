#!/usr/bin/env python3
"""Build the standalone USA Disc-1 flying/global Weltall-2 mod.

The native publisher/title boot is preserved.  New Game enters an inert field
gateway, which performs the retail WORLD_MAP transition into the first
post-Lahan world-map configuration.  Canonical file 37 retains the native
Yggdrasil flight task but presents and controls Weltall-2 in its place.
Every regular-Weltall presentation and gameplay path on Disc 1 is also
replaced by, or checked as a compatibility alias to, native Weltall-2 data.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import sys
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import xenoiso_build
from tools.xgdisc import Mode2Image
from tools.xgfield import build_field_preserving, parse_field
from tools.xgmode2 import (
    PATCH_CONTEXT_BEFORE,
    PATCH_CONTEXT_OFFSET,
    RAW_SECTOR_SIZE,
    SLUS_TEXT_SIZE,
    USER_DATA_OFFSET,
    regenerate_mode2_form1,
)
from tools.xgscript import AtelScript
from tools import xgweltall2_global as global_w2
from tools.xgweltall2_flight import patch_disc1_worldmap_overlay


FORMAT = "xenogears-flying-weltall2-disc1-v6"
DISC1_SIZE = 718_738_272
DISC1_SHA256 = (
    "39c547a9afc6da15d847ef81a2c6cea1a6516bdfa562cf13b0999b04e8598bda"
)
DISC1_SLUS_HEADER_LBA = 108_606
DISC1_SLUS_TARGET_LBA = 108_626
DISC1_RETAIL_TARGET_SECTOR_SHA256 = (
    "871d1875313743ad06b4661659955fdbf567029e7303f6ace4eab2a7006ffdb0"
)

DEFAULT_DISC = ROOT / "Xenogears (Disc 1).bin"
DEFAULT_XENOISO = (
    Path.home()
    / "Downloads"
    / "Xenogears_Perfect_Works_Edition_0.10.2"
    / "Tools"
    / "xenoiso.exe"
)
DEFAULT_FEI_PROFILE_STATE = ROOT / "work" / "standalone_bootstrap" / "2595.bin"
DEFAULT_STAGE = ROOT / "work" / "weltall2_flight_v6_stage"
DEFAULT_OUTPUT = ROOT / "output" / "Xenogears_US_CD1_Flying_Weltall2_v6.bin"

WORLD_MAP_OVERLAY_ID = 37
TITLE_FIELD_ID = 490
TITLE_FIELD_CANONICAL_ID = 1586
GATEWAY_FIELD_ID = 724
GATEWAY_FIELD_CANONICAL_ID = 606 + 2 * GATEWAY_FIELD_ID
INITIAL_GAMESTATE_ID = 2595
POST_LAHAN_WORLD_MAP_ID = 3975

SOURCE_IDENTITIES = {
    WORLD_MAP_OVERLAY_ID: (
        92_180,
        "0f7e7a283fc5ef25d4a82960e16b119d09e1ba5594cc02069cf3dd2113f48803",
    ),
    TITLE_FIELD_CANONICAL_ID: (
        4_336,
        "8086ef838b330ef7d8385a44d45352ba9017eeaab0db34ef6f9b23d39c085ba8",
    ),
    GATEWAY_FIELD_CANONICAL_ID: (
        26_180,
        "a22e96a7987ebb10d7340b6ffbdfec8327742be7d3dbe621dbff881a1cf47de8",
    ),
    INITIAL_GAMESTATE_ID: (
        9_048,
        "d892fa678f66ab12e0d2cb5ccb6cd432ecbc055b41360d8a4c4404fd38f1e20b",
    ),
    POST_LAHAN_WORLD_MAP_ID: (
        42_932,
        "cfc703579f5f6c10e68880d41eac3802ae4c54e7dd797ed5cad9e1029df79857",
    ),
    **global_w2.SOURCE_IDENTITIES,
}

SCRIPT_INDEX = 5

TITLE_SCRIPT_SOURCE_SIZE = 560
TITLE_SCRIPT_SOURCE_SHA256 = (
    "76525b0f68a8875a1a3d8955f9fcb9905801f977c11ce51ec0902144c523e8a6"
)
TITLE_RESULT_BRANCH_PC = 0x00B0
TITLE_RESULT_BRANCH = bytes.fromhex("02 46 00 00 00 40 E7 00")
TITLE_FALLTHROUGH_PC = 0x00B8
TITLE_FALLTHROUGH_SOURCE = bytes.fromhex("02 02 04 00 00 40 CF 00")
TITLE_FALLTHROUGH_PATCHED = bytes.fromhex("01 6C 01 00 00 00 00 00")
TITLE_GATEWAY_ROUTINE = bytes.fromhex("98 D4 82 00 80 5B")
TITLE_SCRIPT_PATCHED_SIZE = 566
TITLE_SCRIPT_PATCHED_SHA256 = (
    "78cb6c96d7b076faf8b1c400220fe5279c47bede6555939336b56aa607efaa6a"
)
TITLE_FIELD_PATCHED_SIZE = 4_348
TITLE_FIELD_PATCHED_SHA256 = (
    "c80ca1a6cecc86d0e406615afa0453c68ca7523373a4f07323b87737143a64f0"
)

GATEWAY_SCRIPT_SOURCE_SIZE = 5_412
GATEWAY_SCRIPT_SOURCE_SHA256 = (
    "8f5457f4befe275832cbd338c6bcfae69e9b3b33c1a2edc3b9ff9ea333917fda"
)
GATEWAY_ENTITY_COUNT = 19
GATEWAY_BYTECODE_OFFSET = 0x544
GATEWAY_STOP_PC = 0x0FE0
GATEWAY_DIRECTOR_PC = 0x0FE1
GATEWAY_UPDATE_PC = 0x0FE7
GATEWAY_DIRECTOR = bytes.fromhex("FE 54 B4 01 80 00")
GATEWAY_UPDATE = bytes.fromhex(
    "FE 54 B4 01 80 26 20 80 56 00 04 01 00 FF FF 01 00 F0 5B"
)
GATEWAY_SCRIPT_PATCHED_SIZE = 5_438
GATEWAY_SCRIPT_PATCHED_SHA256 = (
    "7359ff094fdb25dcbb30363091b5000957e626a6b0f7428e08ed1dc841a3883a"
)
GATEWAY_FIELD_PATCHED_SIZE = 26_024
GATEWAY_FIELD_PATCHED_SHA256 = (
    "668f688f4551cb5e8732c925ab4dd85c590301c0f26e4a8052bebda53816cfc7"
)

GAMESTATE_SIZE = 0x2358
FEI_PROFILE_GAMESTATE_SHA256 = (
    "c90f343a1cceccf9e9a8d3cb68079856ac8e63efad0d99a1f5655a4d45fa4375"
)
FEI_PROFILE_RECORD_SHA256 = (
    "a61ce9698ed2172a6430943903299d3dbee14dc3e920ab8449b9d71580db465b"
)
NAME_REGION_SIZE = 31 * 20
FIXED_NAME_CELL_SIZE = 20
WELTALL_NAME_CELL = 11
WELTALL2_NAME_CELL = 12
RETAIL_NAME_REGION_SHA256 = (
    "34598355d2ae9c72c084f728aaf9ae0099d47ae94e7911246470d16d22b65734"
)

FEI_RECORD = 0x26C
FEI_LEVEL_OFFSETS = (FEI_RECORD + 0x62, FEI_RECORD + 0x63)
FEI_CURRENT_HP = FEI_RECORD + 0x4C
FEI_MAX_HP = FEI_RECORD + 0x4E
FEI_CURRENT_MP = FEI_RECORD + 0x50
FEI_MAX_MP = FEI_RECORD + 0x52
FEI_GEAR_ID = FEI_RECORD + 0xA0
FEI_ABILITY_RECORD = 0x16C0

WELTALL2_GEAR_ID = 1
GEAR_RECORD_SIZE = 0xA4
WELTALL_RECORD = 0x978
WELTALL2_RECORD = 0x978 + WELTALL2_GEAR_ID * GEAR_RECORD_SIZE
BEST_FRAME_ID = 0x11       # XENO-30400
BEST_ENGINE_ID = 0x36      # OMEGA100
BEST_ARMOR_ID = 0x37       # Z Gold100
BEST_ACCESSORY_IDS = bytes((0x64, 0x64, 0x64))  # three stackable GNRS50 units

# This complete Weltall-2 record was captured after running the retail
# equipment-menu recalculation for the four selections above.  Using the
# complete record matters: battle code consumes cached HP, fuel, output,
# defense, weight, and accessory effects rather than deriving them from IDs.
BEST_WELTALL2_RECORD = bytes.fromhex(
    "00 00 11 36 00 00 00 00 37 64 64 64 00 00 00 00 "
    "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
    "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
    "00 00 00 00 00 00 00 00 E8 03 E8 03 64 0A 0A 0A "
    "00 00 00 00 D0 02 00 00 00 00 00 00 00 00 00 00 "
    "00 00 00 00 00 00 0F 00 00 00 00 00 00 00 00 00 "
    "C0 76 00 00 C0 76 00 00 AC 0D 00 00 00 00 00 00 "
    "E8 03 00 00 0A 05 00 00 00 00 00 00 00 00 00 00 "
    "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
    "00 00 00 00 00 00 00 00 0A 00 00 00 00 00 0A 00 "
    "00 00 00 00"
)
BEST_WELTALL2_RECORD_SHA256 = (
    "bf3df25a3c56edf8399d2d84ebe408ad9f48912f258848258c192d2c7d1d4d1f"
)

POST_LAHAN_SCENARIO = 0x18
POST_LAHAN_POSITION_INDEX = 1
POST_LAHAN_X = 29_947
POST_LAHAN_Z = 11_075

INITIAL_GAMESTATE_PATCHED_SHA256 = (
    "e4255c517f86a8d809cc31334e506cf0a55dca953881988212c13d945497ec6a"
)

REPLACEMENT_IDS = frozenset(
    (
        WORLD_MAP_OVERLAY_ID,
        TITLE_FIELD_CANONICAL_ID,
        GATEWAY_FIELD_CANONICAL_ID,
        INITIAL_GAMESTATE_ID,
        *global_w2.GLOBAL_REPLACEMENT_IDS,
    )
)


class Weltall2BuildError(RuntimeError):
    """Raised when a source identity or standalone build contract changes."""


@dataclass(frozen=True)
class Replacement:
    canonical_id: int
    filename: str
    role: str
    data: bytes

    @property
    def sha256(self) -> str:
        return _sha256(self.data)


@dataclass(frozen=True)
class PreparedMod:
    replacements: tuple[Replacement, ...]
    source_sentinel: bytes


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _checked_identity(data: bytes, canonical_id: int) -> None:
    expected_size, expected_hash = SOURCE_IDENTITIES[canonical_id]
    actual_hash = _sha256(data)
    if len(data) != expected_size or actual_hash != expected_hash:
        raise Weltall2BuildError(
            f"Canonical {canonical_id} source mismatch: {len(data)} bytes, "
            f"SHA-256 {actual_hash}; expected {expected_size}, {expected_hash}"
        )


def validate_source_disc(path: Path | str) -> tuple[Path, str]:
    disc = Path(path).resolve()
    if not disc.is_file():
        raise Weltall2BuildError(f"Disc-1 source does not exist: {disc}")
    size = disc.stat().st_size
    digest = _sha256_file(disc)
    if size != DISC1_SIZE or digest != DISC1_SHA256:
        raise Weltall2BuildError(
            f"Disc-1 source mismatch: {size} bytes, SHA-256 {digest}; "
            f"expected {DISC1_SIZE}, {DISC1_SHA256}"
        )
    Mode2Image(disc).read_index()
    return disc, digest


def _canonical(image: Mode2Image, canonical_id: int) -> bytes:
    entries = image.read_index()
    if not 0 <= canonical_id < len(entries):
        raise Weltall2BuildError(
            f"Canonical {canonical_id} lies outside the Disc-1 FAT"
        )
    entry = entries[canonical_id]
    if entry.kind != "file":
        raise Weltall2BuildError(
            f"Canonical {canonical_id} is {entry.kind}, not a file"
        )
    return image.extract_entry(entry)


def patch_title_field(source: bytes) -> bytes:
    _checked_identity(source, TITLE_FIELD_CANONICAL_ID)
    parsed = parse_field(source)
    components = [part.data for part in parsed.parts]
    script = components[SCRIPT_INDEX]
    if (
        len(script) != TITLE_SCRIPT_SOURCE_SIZE
        or _sha256(script) != TITLE_SCRIPT_SOURCE_SHA256
    ):
        raise Weltall2BuildError("Title field script identity changed")

    editor = AtelScript(script)
    if editor.entity_count != 1 or editor.bytecode_offset != 0xC4:
        raise Weltall2BuildError("Title field ATEL layout changed")
    appended_pc = editor.append_raw_routine(TITLE_GATEWAY_ROUTINE)
    if appended_pc != 0x016C:
        raise Weltall2BuildError(
            f"Title gateway routine moved to PC 0x{appended_pc:04X}"
        )

    patched_script = bytearray(editor.to_bytes())
    bytecode = editor.bytecode_offset
    result = bytecode + TITLE_RESULT_BRANCH_PC
    fallthrough = bytecode + TITLE_FALLTHROUGH_PC
    if patched_script[result : result + 8] != TITLE_RESULT_BRANCH:
        raise Weltall2BuildError("Title New Game result branch changed")
    if patched_script[fallthrough : fallthrough + 8] != TITLE_FALLTHROUGH_SOURCE:
        raise Weltall2BuildError("Title New Game fallthrough changed")
    patched_script[fallthrough : fallthrough + 8] = TITLE_FALLTHROUGH_PATCHED
    components[SCRIPT_INDEX] = bytes(patched_script)
    if (
        len(components[SCRIPT_INDEX]) != TITLE_SCRIPT_PATCHED_SIZE
        or _sha256(components[SCRIPT_INDEX]) != TITLE_SCRIPT_PATCHED_SHA256
    ):
        raise Weltall2BuildError("Patched title script identity changed")

    result_bundle = build_field_preserving(
        source,
        components,
        (SCRIPT_INDEX,),
        compact_changed=True,
    )
    if (
        len(result_bundle) != TITLE_FIELD_PATCHED_SIZE
        or _sha256(result_bundle) != TITLE_FIELD_PATCHED_SHA256
    ):
        raise Weltall2BuildError("Patched title field identity changed")
    return result_bundle


def build_gateway_field(source: bytes) -> bytes:
    """Replace unused field 724's scripts with a black world-map handoff."""

    _checked_identity(source, GATEWAY_FIELD_CANONICAL_ID)
    parsed = parse_field(source)
    components = [part.data for part in parsed.parts]
    script = components[SCRIPT_INDEX]
    if (
        len(script) != GATEWAY_SCRIPT_SOURCE_SIZE
        or _sha256(script) != GATEWAY_SCRIPT_SOURCE_SHA256
    ):
        raise Weltall2BuildError("Gateway donor script identity changed")

    editor = AtelScript(script)
    if (
        editor.entity_count != GATEWAY_ENTITY_COUNT
        or editor.bytecode_offset != GATEWAY_BYTECODE_OFFSET
        or editor.bytecode_size != GATEWAY_STOP_PC
    ):
        raise Weltall2BuildError("Gateway donor ATEL layout changed")

    stop_pc = editor.append_raw_routine(b"\x5B")
    if stop_pc != GATEWAY_STOP_PC:
        raise Weltall2BuildError("Gateway inert routine moved")
    for entity in range(editor.entity_count):
        for script_index in range(32):
            editor.set_script_pointer(entity, script_index, stop_pc)

    director_pc = editor.append_raw_routine(GATEWAY_DIRECTOR)
    update_pc = editor.append_raw_routine(GATEWAY_UPDATE)
    if (director_pc, update_pc) != (GATEWAY_DIRECTOR_PC, GATEWAY_UPDATE_PC):
        raise Weltall2BuildError("Gateway bootstrap routines moved")
    editor.set_script_pointer(0, 0, director_pc)
    editor.set_script_pointer(0, 1, update_pc)
    components[SCRIPT_INDEX] = editor.to_bytes()
    if (
        len(components[SCRIPT_INDEX]) != GATEWAY_SCRIPT_PATCHED_SIZE
        or _sha256(components[SCRIPT_INDEX]) != GATEWAY_SCRIPT_PATCHED_SHA256
    ):
        raise Weltall2BuildError("Patched gateway script identity changed")

    result_bundle = build_field_preserving(
        source,
        components,
        (SCRIPT_INDEX,),
        compact_changed=True,
    )
    if (
        len(result_bundle) != GATEWAY_FIELD_PATCHED_SIZE
        or _sha256(result_bundle) != GATEWAY_FIELD_PATCHED_SHA256
    ):
        raise Weltall2BuildError("Patched gateway field identity changed")
    return result_bundle


def _apply_best_weltall2_equipment(state: bytearray) -> None:
    if (
        len(BEST_WELTALL2_RECORD) != GEAR_RECORD_SIZE
        or _sha256(BEST_WELTALL2_RECORD) != BEST_WELTALL2_RECORD_SHA256
    ):
        raise Weltall2BuildError("Checked maximum-output Weltall-2 record changed")
    # Gear 1 is the native Weltall-2 identity.  Gear 0 remains only as a
    # compatibility fallback for imported saves and any unaudited engine-side
    # selector, so give both slots the exact same maximum-output record.
    for gear in (WELTALL_RECORD, WELTALL2_RECORD):
        state[gear : gear + GEAR_RECORD_SIZE] = BEST_WELTALL2_RECORD


def build_initial_gamestate(retail: bytes, fei_profile_state: bytes) -> bytes:
    _checked_identity(retail, INITIAL_GAMESTATE_ID)
    if (
        len(fei_profile_state) != GAMESTATE_SIZE
        or _sha256(fei_profile_state) != FEI_PROFILE_GAMESTATE_SHA256
    ):
        raise Weltall2BuildError("Checked high-level Fei profile identity changed")
    fei_profile = fei_profile_state[
        FEI_RECORD:FEI_RECORD + GEAR_RECORD_SIZE
    ]
    if _sha256(fei_profile) != FEI_PROFILE_RECORD_SHA256:
        raise Weltall2BuildError("Checked high-level Fei record changed")

    state = bytearray(retail)
    # Import only Fei's audited high-level A4 record.  Every other character,
    # story flag, inventory byte, party selector, and control field remains
    # retail Disc 1, preventing the former whole-GameState donor leakage.
    state[FEI_RECORD:FEI_RECORD + GEAR_RECORD_SIZE] = fei_profile
    if _sha256(bytes(state[:NAME_REGION_SIZE])) != RETAIL_NAME_REGION_SHA256:
        raise Weltall2BuildError("Retail fixed-cell name region changed")

    # The fixed-name table is used by more than the ordinary equipment UI.
    # Turn Gear 0's name into an exact alias of native Weltall-2 as a fallback.
    weltall_name = WELTALL_NAME_CELL * FIXED_NAME_CELL_SIZE
    weltall2_name = WELTALL2_NAME_CELL * FIXED_NAME_CELL_SIZE
    state[weltall_name : weltall_name + FIXED_NAME_CELL_SIZE] = state[
        weltall2_name : weltall2_name + FIXED_NAME_CELL_SIZE
    ]

    # Fei only, maximum displayed/logic level, fully healed, in Weltall-2.
    struct.pack_into("<H", state, 0x1D30, 1)
    # Keep retail's all-eligible frame mask.  Battle selection intersects it
    # with membership, so this is still Fei-only here, while later story
    # scripts may safely add/reorder temporary companions without creating a
    # sparse battle-character list that reuses a stale visual slot.
    if struct.unpack_from("<H", state, 0x1D32)[0] != 0xFFFF:
        raise Weltall2BuildError("Retail party-frame mask changed")
    state[0x1D34:0x1D37] = bytes((0, 0xFF, 0xFF))
    state[0x22B1:0x22B4] = bytes((1, 0, 0))
    for offset in FEI_LEVEL_OFFSETS:
        state[offset] = 99
    state[FEI_GEAR_ID] = WELTALL2_GEAR_ID
    state[FEI_CURRENT_HP : FEI_CURRENT_HP + 2] = state[FEI_MAX_HP : FEI_MAX_HP + 2]
    state[FEI_CURRENT_MP : FEI_CURRENT_MP + 2] = state[FEI_MAX_MP : FEI_MAX_MP + 2]
    struct.pack_into("<H", state, FEI_ABILITY_RECORD + 0x00, 0xFFF8)
    struct.pack_into("<H", state, FEI_ABILITY_RECORD + 0x04, 0x1FF8)
    _apply_best_weltall2_equipment(state)

    # First playable post-Lahan world configuration and its position-one
    # coordinates.  m1834 low mode 3 keeps the native Ygg flight task alive;
    # bit 0x4000 deliberately remains clear so the player begins as a Gear.
    struct.pack_into("<6h", state, 0x1820, POST_LAHAN_X, POST_LAHAN_Z, 0, 0, 0, 0)
    struct.pack_into("<4h", state, 0x182C, POST_LAHAN_X, 0, POST_LAHAN_Z, 0)
    struct.pack_into("<H", state, 0x1834, 0x0003)
    struct.pack_into("<H", state, 0x1836, 0)
    struct.pack_into("<H", state, 0x1930, POST_LAHAN_SCENARIO)
    story_word = struct.unpack_from("<H", state, 0x1BF6)[0] & ~0x0004
    struct.pack_into("<H", state, 0x1BF6, story_word)

    # Cold boot still enters the retail title field.  The field gateway later
    # invokes WORLD_MAP(position=1, mode=1) through the normal resumable path.
    struct.pack_into("<H", state, 0x2318, 0)
    struct.pack_into("<H", state, 0x231A, TITLE_FIELD_ID)
    struct.pack_into("<h", state, 0x231C, 0)
    struct.pack_into("<h", state, 0x231E, POST_LAHAN_POSITION_INDEX)
    struct.pack_into("<H", state, 0x2320, 0)

    result = bytes(state)
    if INITIAL_GAMESTATE_PATCHED_SHA256:
        actual_hash = _sha256(result)
        if actual_hash != INITIAL_GAMESTATE_PATCHED_SHA256:
            raise Weltall2BuildError(
                f"Patched initial GameState identity changed: {actual_hash}"
            )
    return result


def prepare_mod(disc: Path | str, fei_profile_state: Path | str) -> PreparedMod:
    image = Mode2Image(Path(disc).resolve())
    source = {
        canonical_id: _canonical(image, canonical_id)
        for canonical_id in SOURCE_IDENTITIES
    }
    for canonical_id, data in source.items():
        _checked_identity(data, canonical_id)

    flight = patch_disc1_worldmap_overlay(source[WORLD_MAP_OVERLAY_ID]).packed
    standalone = (
        Replacement(
            WORLD_MAP_OVERLAY_ID,
            "0037_worldmap_flying_weltall2.bin",
            "native flight controls, deployed-wing animation, and compact wing lights",
            flight,
        ),
        Replacement(
            TITLE_FIELD_CANONICAL_ID,
            "1586_title_new_game_route.bin",
            "native New Game route to the standalone gateway",
            patch_title_field(source[TITLE_FIELD_CANONICAL_ID]),
        ),
        Replacement(
            GATEWAY_FIELD_CANONICAL_ID,
            "2054_field_724_worldmap_gateway.bin",
            "black resumable WORLD_MAP(1,1) gateway",
            build_gateway_field(source[GATEWAY_FIELD_CANONICAL_ID]),
        ),
        Replacement(
            INITIAL_GAMESTATE_ID,
            "2595_flying_weltall2_gamestate.bin",
            "post-Lahan Fei/Weltall-2 initial state",
            build_initial_gamestate(
                source[INITIAL_GAMESTATE_ID],
                Path(fei_profile_state).resolve().read_bytes(),
            ),
        ),
    )
    try:
        global_replacements = global_w2.build_global_replacements(source)
    except global_w2.Weltall2GlobalPatchError as exc:
        raise Weltall2BuildError(str(exc)) from exc
    replacements = tuple(
        sorted(
            (
                *standalone,
                *(
                    Replacement(
                        item.canonical_id,
                        item.filename,
                        item.role,
                        item.data,
                    )
                    for item in global_replacements
                ),
            ),
            key=lambda item: item.canonical_id,
        )
    )
    ids = frozenset(item.canonical_id for item in replacements)
    if ids != REPLACEMENT_IDS or len(replacements) != len(ids):
        raise Weltall2BuildError(
            f"Replacement set changed: {sorted(ids)}; expected {sorted(REPLACEMENT_IDS)}"
        )
    return PreparedMod(replacements, source[POST_LAHAN_WORLD_MAP_ID])


def _stage_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == data:
        return
    path.write_bytes(data)


def stage_mod(prepared: PreparedMod, stage: Path | str) -> tuple[Path, ...]:
    root = Path(stage).resolve()
    replacements_root = root / "replacements"
    paths: list[Path] = []
    for item in prepared.replacements:
        target = replacements_root / item.filename
        _stage_file(target, item.data)
        paths.append(target)
    manifest = {
        "format": FORMAT,
        "disc": 1,
        "source_disc": {"size": DISC1_SIZE, "sha256": DISC1_SHA256},
        "entry": {
            "title_field": TITLE_FIELD_ID,
            "gateway_field": GATEWAY_FIELD_ID,
            "world_map_position": POST_LAHAN_POSITION_INDEX,
            "world_map_mode": 1,
            "scenario": POST_LAHAN_SCENARIO,
        },
        "party": {
            "members": ["Fei"],
            "level": 99,
            "base_state": "USA retail Disc 1 with only an audited Fei A4 profile imported",
            "gear": "Weltall-2",
            "gear_id": WELTALL2_GEAR_ID,
            "equipment": {
                "frame": "XENO-30400",
                "engine": "OMEGA100",
                "armor": "Z Gold100",
                "accessories": ["GNRS50", "GNRS50", "GNRS50"],
                "policy": "maximum engine output",
            },
        },
        "controls": {
            "take_off": "Jump (physical Square)",
            "forward": "X / Cross while flying",
            "land": "Triangle, or Jump again, at a native-valid landing point",
        },
        "flight_visuals": {
            "animation": "native Weltall-2 deployed-wing bobbing flight loop",
            "wing_lights": "two compact native white engine lights pinned to the wings",
            "lifetime": "takeoff through native touchdown",
        },
        "disc1_global_weltall_replacement": {
            "policy": "regular Weltall is retained only as a Weltall-2 compatibility alias",
            "native_gear_id": WELTALL2_GEAR_ID,
            "covered_paths": [
                "persistent story assignments",
                "field mounted sprite",
                "field-scene 3D model and compatible animation table",
                "scripted model-7 Weltall and compatible animation table",
                "Blackmoon Rankar intro's embedded dropped Weltall",
                "both regular-Weltall world-map sprite slots",
                "battle geometry, animations, and live combat tables",
                "Nortune Battling Arena roster, selectors, and fallback bundle",
                "equipment preview and Gear-parts shop",
                "fixed names and imported-save Gear-0 fallback",
            ],
            "replacement_count": len(global_w2.GLOBAL_REPLACEMENT_IDS),
        },
        "replacements": [
            {
                "canonical_id": item.canonical_id,
                "filename": item.filename,
                "role": item.role,
                "size": len(item.data),
                "sha256": item.sha256,
            }
            for item in prepared.replacements
        ],
        "untouched_post_lahan_map": {
            "canonical_id": POST_LAHAN_WORLD_MAP_ID,
            "size": len(prepared.source_sentinel),
            "sha256": _sha256(prepared.source_sentinel),
        },
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return tuple(paths)


def _link_or_copy(source: Path, target: Path) -> None:
    target.unlink(missing_ok=True)
    try:
        os.link(source, target)
    except OSError:
        shutil.copyfile(source, target)


def _verify_built_disc(
    output: Path,
    prepared: PreparedMod,
    source_hash: str,
    source_disc: Path,
) -> None:
    verify_disc1_retail_title_boot(output)
    image = Mode2Image(output)
    for item in prepared.replacements:
        actual = _canonical(image, item.canonical_id)
        if actual != item.data:
            raise Weltall2BuildError(
                f"Built-disc readback differs for canonical {item.canonical_id}"
            )
    sentinel = _canonical(image, POST_LAHAN_WORLD_MAP_ID)
    if sentinel != prepared.source_sentinel:
        raise Weltall2BuildError("Untouched post-Lahan world-map resource changed")
    if _sha256_file(source_disc) != source_hash:
        raise Weltall2BuildError("Source Disc 1 changed during the build")


def verify_disc1_retail_title_boot(image_path: Path | str) -> None:
    """Verify Disc 1's native boot decision at its checked retail SLUS LBA.

    Xenoiso legitimately rewrites thousands of embedded CD-sector references
    in the executable when replacement sizes move later resources.  The boot
    decision itself lives in one unaffected checked sector; validating that
    complete raw sector plus its context proves this mod did not use the
    direct-field executable patch.
    """

    image = Path(image_path).resolve()
    minimum = (DISC1_SLUS_TARGET_LBA + 1) * RAW_SECTOR_SIZE
    if not image.is_file() or image.stat().st_size < minimum:
        raise Weltall2BuildError(
            f"Built image is missing or too small for the Disc-1 SLUS: {image}"
        )
    with image.open("rb") as handle:
        handle.seek(DISC1_SLUS_HEADER_LBA * RAW_SECTOR_SIZE)
        header_sector = handle.read(RAW_SECTOR_SIZE)
        handle.seek(DISC1_SLUS_TARGET_LBA * RAW_SECTOR_SIZE)
        target_sector = handle.read(RAW_SECTOR_SIZE)

    header = header_sector[USER_DATA_OFFSET : USER_DATA_OFFSET + 2_048]
    if header[:8] != b"PS-X EXE":
        raise Weltall2BuildError("Disc-1 SLUS header does not contain PS-X EXE")
    text_size = struct.unpack_from("<I", header, 0x1C)[0]
    if text_size != SLUS_TEXT_SIZE:
        raise Weltall2BuildError(
            f"Disc-1 SLUS text size is 0x{text_size:X}, expected 0x{SLUS_TEXT_SIZE:X}"
        )
    if regenerate_mode2_form1(header_sector) != header_sector:
        raise Weltall2BuildError("Disc-1 SLUS header sector has invalid EDC/ECC")
    if regenerate_mode2_form1(target_sector) != target_sector:
        raise Weltall2BuildError("Disc-1 SLUS target sector has invalid EDC/ECC")
    target_hash = _sha256(target_sector)
    if target_hash != DISC1_RETAIL_TARGET_SECTOR_SHA256:
        raise Weltall2BuildError(
            "Native publisher/title boot sector changed: "
            f"{target_hash}; expected {DISC1_RETAIL_TARGET_SECTOR_SHA256}"
        )
    start = USER_DATA_OFFSET + PATCH_CONTEXT_OFFSET
    if target_sector[start : start + len(PATCH_CONTEXT_BEFORE)] != PATCH_CONTEXT_BEFORE:
        raise Weltall2BuildError("Native publisher/title boot context changed")


def build_disc(
    *,
    source_disc: Path,
    xenoiso: Path,
    fei_profile_state: Path,
    stage: Path,
    output: Path,
    force: bool,
    prepare_only: bool,
) -> Path | None:
    source_disc, source_hash = validate_source_disc(source_disc)
    if not fei_profile_state.resolve().is_file():
        raise Weltall2BuildError(
            f"Checked high-level Fei profile is missing: {fei_profile_state.resolve()}"
        )
    prepared = prepare_mod(source_disc, fei_profile_state)
    replacement_paths = stage_mod(prepared, stage)
    print(f"Prepared {len(replacement_paths)} checked replacements in {stage.resolve()}")
    if prepare_only:
        return None

    output = output.resolve()
    cue = output.with_suffix(".cue")
    if (output.exists() or cue.exists()) and not force:
        raise Weltall2BuildError(
            f"Refusing to overwrite {output} or {cue}; pass --force"
        )
    executable = xenoiso.resolve()
    if not executable.is_file():
        raise Weltall2BuildError(f"Xenoiso executable is missing: {executable}")

    stage = stage.resolve()
    stage.mkdir(parents=True, exist_ok=True)
    staged_source = stage / "disc1_source.bin"
    staged_executable = stage / "xenoiso.exe"
    staged_output = stage / "built.bin"
    staged_cue = staged_output.with_suffix(".cue")
    _link_or_copy(source_disc, staged_source)
    _link_or_copy(executable, staged_executable)
    try:
        args = argparse.Namespace(
            xenoiso=staged_executable,
            source=staged_source,
            output=staged_output,
            replacement=[
                (item.canonical_id, path)
                for item, path in zip(
                    prepared.replacements, replacement_paths, strict=True
                )
            ],
            disc=1,
            force=True,
        )
        xenoiso_build.command_build(args)
        _verify_built_disc(
            staged_output,
            prepared,
            source_hash,
            source_disc,
        )

        output.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staged_output, output)
        cue.write_text(
            f'FILE "{output.name}" BINARY\n'
            "  TRACK 01 MODE2/2352\n"
            "    INDEX 01 00:00:00\n",
            encoding="ascii",
            newline="\n",
        )
        _verify_built_disc(output, prepared, source_hash, source_disc)
        print(f"Verified {output} ({output.stat().st_size} bytes)")
        print(f"Wrote {cue}")
        return output
    finally:
        staged_source.unlink(missing_ok=True)
        staged_executable.unlink(missing_ok=True)
        staged_cue.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-disc", type=Path, default=DEFAULT_DISC)
    parser.add_argument("--xenoiso", type=Path, default=DEFAULT_XENOISO)
    parser.add_argument(
        "--fei-profile-state", type=Path, default=DEFAULT_FEI_PROFILE_STATE
    )
    parser.add_argument("--stage", type=Path, default=DEFAULT_STAGE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        build_disc(
            source_disc=args.source_disc,
            xenoiso=args.xenoiso,
            fei_profile_state=args.fei_profile_state,
            stage=args.stage,
            output=args.output,
            force=args.force,
            prepare_only=args.prepare_only,
        )
    except (
        OSError,
        Weltall2BuildError,
        global_w2.Weltall2GlobalPatchError,
        xenoiso_build.BuildError,
    ) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())


__all__ = [
    "BEST_ACCESSORY_IDS",
    "BEST_ARMOR_ID",
    "BEST_ENGINE_ID",
    "BEST_FRAME_ID",
    "GATEWAY_FIELD_CANONICAL_ID",
    "INITIAL_GAMESTATE_ID",
    "POST_LAHAN_POSITION_INDEX",
    "REPLACEMENT_IDS",
    "WELTALL_RECORD",
    "WELTALL2_RECORD",
    "Weltall2BuildError",
    "build_gateway_field",
    "build_initial_gamestate",
    "patch_title_field",
    "prepare_mod",
    "stage_mod",
    "validate_source_disc",
    "verify_disc1_retail_title_boot",
]
