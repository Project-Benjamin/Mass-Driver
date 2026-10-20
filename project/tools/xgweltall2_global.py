#!/usr/bin/env python3
"""Checked Disc-1 replacement of every playable Weltall path with Weltall-2.

Xenogears does not use one universal Gear model.  Field movement, world-map
movement, battles, the Gear-parts shop, and the equipment preview all select
independent resources.  Story scripts can also assign Fei's Gear ID back to
zero.  This module audits and patches every one of those Disc-1 paths while
leaving the native Weltall-2 slot (Gear ID 1) intact.

The ordinary Weltall slots are retained only as compatibility aliases.  Their
payloads, combat tables, and menu selectors are replaced by the native
Weltall-2 equivalents, so a missed or save-carried Gear-0 reference cannot
bring the old model back.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
from typing import Mapping

from tools import xgweltall2_field3d as field3d
from tools.xgfield import build_field_preserving, decompress_lzss, parse_field
from tools.xgscript import AtelScript


SCRIPT_INDEX = 5
DIALOGUE_INDEX = 7

SYSTEM_NAMES_ID = 29
BATTLING_WELTALL_ID = 52
BATTLING_WELTALL2_ID = 62
FIELD_WELTALL_ID = 443
FIELD_WELTALL2_ID = 444
SYSTEM_DATA_ID = 2594
GEAR_SHOP_MENU_ID = 2602
LIVE_BATTLE_STATS_ID = 2614
RANKAR_INTRO_BATTLE_BUNDLE_ID = 2641
BATTLE_WELTALL_MODEL_ID = 2926
BATTLE_WELTALL_ANIMATION_ID = 2927
BATTLE_WELTALL2_MODEL_ID = 2928
BATTLE_WELTALL2_ANIMATION_ID = 2929
EQUIPMENT_WELTALL_PREVIEW_ID = 2988
EQUIPMENT_WELTALL2_PREVIEW_ID = 2989
WORLDMAP_WELTALL_ID = 3939
WORLDMAP_WELTALL2_ID = 3940
WORLDMAP_WELTALL_ALIAS_ID = 3949

WELTALL_ASSIGNMENT = bytes.fromhex("FE A1 00 80 00 80")
WELTALL2_ASSIGNMENT = bytes.fromhex("FE A1 00 80 01 80")


@dataclass(frozen=True)
class ScriptBytePatch:
    pc: int
    before: bytes
    after: bytes
    role: str


def _battling_player_patch(pc: int) -> ScriptBytePatch:
    return ScriptBytePatch(
        pc + 6,
        bytes.fromhex("00 80"),
        bytes.fromhex("0A 80"),
        "SETUP_BATTLING player selector: Weltall 0 -> native Weltall-2 10",
    )


# Nortune's real-time Battling engine has its own roster namespace.  Runtime
# directory tracing proves selector 0 loads canonical 52 (Weltall), while
# selector 10 loads canonical 62 (Weltall-2).  These are every Disc-1 fixed
# player-Weltall call, plus the mirror-match opponent and the two assignments
# which feed the optional variable-selector call in field 222.
FIELD_BATTLING_PATCHES = {
    1048: tuple(
        _battling_player_patch(pc)
        for pc in (
            0x0C88,
            0x0CB8,
            0x0CF7,
            0x1719,
            0x1762,
            0x177E,
            0x17A0,
            0x17BC,
            0x17DE,
            0x17FF,
            0x181B,
        )
    ),
    1050: (
        _battling_player_patch(0x1C2A),
        _battling_player_patch(0x1CC2),
        _battling_player_patch(0x1D43),
        ScriptBytePatch(
            0x1D43 + 8,
            bytes.fromhex("00 80"),
            bytes.fromhex("0A 80"),
            "SETUP_BATTLING mirror opponent: Weltall 0 -> Weltall-2 10",
        ),
        ScriptBytePatch(
            0x248B + 3,
            b"\x00",
            b"\x0A",
            "optional roster's first Gear-0 assignment -> Weltall-2 10",
        ),
        ScriptBytePatch(
            0x24A5 + 3,
            b"\x00",
            b"\x0A",
            "optional roster's second Gear-0 assignment -> Weltall-2 10",
        ),
        ScriptBytePatch(
            0x245E,
            bytes.fromhex("A9 24"),
            bytes.fromhex("A9 23"),
            "optional roster menu count: three choices -> two choices",
        ),
    ),
    1052: tuple(
        _battling_player_patch(pc) for pc in (0x0200, 0x025E, 0x02A7)
    ),
    2062: (
        _battling_player_patch(0x0B2C),
        ScriptBytePatch(
            0x0B2C + 8,
            bytes.fromhex("00 80"),
            bytes.fromhex("0A 80"),
            "debug mirror opponent: Weltall 0 -> Weltall-2 10",
        ),
        _battling_player_patch(0x2468),
    ),
}

# Every Disc-1 field script containing the exact immediate form
# ASSIGN_GEAR(character=Fei, gear=Weltall).  Field 728 is the retail debug
# room; it is included because this mod's contract is the entire disc, not
# only the ordinary story route.
FIELD_ASSIGNMENT_COUNTS = {
    610: 1,   # field 2, Lahan intro battle
    654: 1,   # field 24, Blackmoon Forest Rankar opening
    714: 1,   # field 54, Citan returns Weltall
    728: 1,   # field 61
    734: 1,   # field 64
    1006: 1,  # field 200, Nortune doctor
    1052: 1,  # field 223, Battling Arena issue
    1056: 1,  # field 225, Rico rescue completion
    1106: 1,  # field 250, Kislev Gear dock
    1452: 4,  # field 423, Shevat map variants
    2062: 11, # field 728, retail debug selectors
}

FIELD_SCRIPT_IDS = frozenset(FIELD_ASSIGNMENT_COUNTS) | frozenset(
    FIELD_BATTLING_PATCHES
)

FIELD_NUMBERS = {
    canonical_id: (canonical_id - 606) // 2
    for canonical_id in FIELD_SCRIPT_IDS
}

# Exact USA retail Disc-1 identities.  Donors are checked as strictly as
# targets so an accidental cross-revision transplant fails before staging.
SOURCE_IDENTITIES = {
    **field3d.RETAIL_RESOURCE_IDENTITIES,
    SYSTEM_NAMES_ID: (
        13_768,
        "4b6ca5e621c92d4603ccc4368b05d9d6815f61e098972737ed8af22778a47bc3",
    ),
    BATTLING_WELTALL_ID: (
        65_356,
        "3280edb4d292a62d8bfb66d4503bc960af41a011c7181e41b5937f9c6ce1c9f0",
    ),
    BATTLING_WELTALL2_ID: (
        71_204,
        "f13db03b32949b1e91426e2d87d2690dcb02e7facc5f8f095a00cea55b7734db",
    ),
    FIELD_WELTALL_ID: (
        51_732,
        "f3d792b9adeb63af0d72324da2bd496fe05e34ae58dd3c11fb9582b37de25241",
    ),
    FIELD_WELTALL2_ID: (
        56_032,
        "e1195d6152bbab1d031799184c2453b9963faa7ff27f1b4599dde7b626a67605",
    ),
    SYSTEM_DATA_ID: (
        40_336,
        "c3bd13cfc3579339a072377dbca30319535aa9ef2aa5f93d464c5ae12c13f4fa",
    ),
    GEAR_SHOP_MENU_ID: (
        82_080,
        "5a08a22f2c5cc1d131b33a944d3167a2ac460c5f9f17f2dcf94dd8860158a25c",
    ),
    LIVE_BATTLE_STATS_ID: (
        56_260,
        "52805ab340a772ad978266fb56cd747baae3549cee9260194e91605653cad369",
    ),
    RANKAR_INTRO_BATTLE_BUNDLE_ID: (
        197_724,
        "b3b2b7df4c8b16f2fc8d0a6fd8c66fd919b564614b92ecacb96129e305768f05",
    ),
    BATTLE_WELTALL_MODEL_ID: (
        49_840,
        "2584a9f52d50a6be4518a582474ce3a9523d99fb9eaa71e420f56dfb8b1086a1",
    ),
    BATTLE_WELTALL_ANIMATION_ID: (
        20_716,
        "c02986c12dd9616a001f522ee02bbdb6c615e60f81676047b6d9580cc8cda1b1",
    ),
    BATTLE_WELTALL2_MODEL_ID: (
        52_280,
        "b3576c385efba096fa45895b2141888f68c4e2c7c0258485849d9ab61d5e0afe",
    ),
    BATTLE_WELTALL2_ANIMATION_ID: (
        26_968,
        "1c18f04fde4dc25a002a312d8840865416e83981068647bccc5ca63505edc6cb",
    ),
    EQUIPMENT_WELTALL_PREVIEW_ID: (
        71_640,
        "bc6c241427ce32b2407a323ddceb7fe97479dbdadbe434f5eb73a5db2f9d290f",
    ),
    EQUIPMENT_WELTALL2_PREVIEW_ID: (
        84_012,
        "dbf3c3815bddc5668e587d00a8f7f2262fa741fcc74637c76f45939087b79be9",
    ),
    WORLDMAP_WELTALL_ID: (
        10_960,
        "d2d36a82bc67a3e79ac3d966e0b2d4a09049c3bb047fba384df0f9fa901cc79d",
    ),
    WORLDMAP_WELTALL2_ID: (
        15_520,
        "365febd425cee6229a9b4c63589a97d0d584011ae2499dbe539102944784495e",
    ),
    WORLDMAP_WELTALL_ALIAS_ID: (
        10_960,
        "d2d36a82bc67a3e79ac3d966e0b2d4a09049c3bb047fba384df0f9fa901cc79d",
    ),
    610: (
        123_808,
        "d81670fa78aeed510852153349cd8d4e4b5a6bc6469110e41fb6274aa4e4261f",
    ),
    654: (
        96_216,
        "bb1cd440a14310648ee11137730e608fc80608a7994cb1af203121d6cdabb19c",
    ),
    714: (
        58_680,
        "20092339518a54049892e835b422da750ade5a256cede6e671d475e1afa75607",
    ),
    728: (
        49_836,
        "212de9d91b25f75a7f4db98e277c9a70fe43806d21618928d259a20472b94f8f",
    ),
    734: (
        165_376,
        "6cebb2db4c54c6d9c7978ccb62004bae90ff734ae015d330af0e16f4a59b1d50",
    ),
    1006: (
        47_372,
        "1efde46aab7ecc0e3807b5d928e8eb7725aba24be84583586e7f3caae78bc5de",
    ),
    1048: (
        76_428,
        "41ad0497f17db2851c0a812ad7e41e9a485e950e21edfd3bf9257fce32ca47ea",
    ),
    1050: (
        155_100,
        "dcf7a11820c2b83c713b79237dae4396f73638b44d62301d3cd8ba6f0ae151f0",
    ),
    1052: (
        67_128,
        "b9925d5672baed18ed1dfa6cc64931defe90d3aca8152ee3905f3298439b62aa",
    ),
    1056: (
        76_704,
        "2cbca37795aec0230d6b843a17cbe2ef02bec030ab7b6aae4f647ee879614f27",
    ),
    1106: (
        161_380,
        "37330253bcd6a61eb1a3f071fa3bfcc57d71c082d59ca6694471cb43cbd4d461",
    ),
    1452: (
        47_652,
        "6b2b95053924c16b20de9b5acd52becc4e13c9ed015d4c9defe2d97f00d5a83a",
    ),
    2062: (
        81_636,
        "2b7decfea1f6c5a09f74ef76ca41ba2da40d7384fe33a48e7e1ac9509f1e3a1a",
    ),
}

FIELD_RESULT_IDENTITIES = {
    610: (123_764, "b093d416292cc977c01e9f9cd28873c31f4748e7f12c0fc3d66b103dec6834fa"),
    654: (96_196, "ff891942a64443067a0327e50c3c5f67465c6f13664ccb3942091e31209a77fe"),
    714: (58_664, "f4588d3609e70a2609235ca6fb9a42a9462c75e12dad83cdca0fa202b0a7afa4"),
    728: (49_828, "b74815aaa2a783bdd79a21461b4f16402be0d9bb456325631f60f0d5180fade5"),
    734: (165_296, "2561681de4932cdb0b12685cedb1425b8534b6f5f3f78ec91535105a7a827ce5"),
    1006: (47_348, "a2e6bb5291afd7f91213c587f9502b03f3c503eb99e55b10b286b519f442d4a9"),
    1048: (76_392, "c9ace3909abcc7358ea759eb63c2d8f907969d6d52638fe29bfd7253c73ebc88"),
    1050: (154_780, "020194152b54087c32d35ebffb814cfac9afbea7f3a53f9cac4ccd71b6ed18ad"),
    1052: (67_096, "90fc86fd4bfdd7c04dc3a723a9bffbfde60425ea0545836029187d77e93a5c94"),
    1056: (76_680, "a7425e0815c660d2c5fc0f052b2747023a5c4e00f67170082cf280d0b2b00ce4"),
    1106: (161_304, "1dde924c853f59f9dd52301eedbb521989ec9e392a47ff6e9181bc5c6e69acb6"),
    1452: (47_608, "1fda206af631dedd2d56c4909af4b7aa8ee2533281aea61f47b2954b6d3e0efb"),
    2062: (81_280, "a2cd0e1ee73cb01dd1f0ff96d3095b8ed2646b9ce7a27d235c71b6cdf44e4193"),
}

SYSTEM_DATA_RESULT = (
    40_332,
    "5a0219352d029ab91f065b30428cb6bf76679e676e8bfb5c7671a35546518751",
)
LIVE_BATTLE_STATS_RESULT = (
    56_256,
    "ee8ff4023fda4d926d3cdad82e384316f5c70ca82c38407a04454ec7dd4fbd34",
)
GEAR_SHOP_MENU_RESULT = (
    82_080,
    "5172016a358d308055e676865b35a85c7b449d9d4e2808067fc98573434ebd3d",
)

# Field 24 encounter 15 uses battle setup 11/event 4.  Its dropped Weltall is
# not the ordinary player-Gear slot: it is model-7 mecha entry 2 inside
# canonical 2641, with a scene-specific controller and an exact embedded copy
# of canonical 2159 geometry.  Entry 0 is Rankar Dragon and entry 1 is Citan's
# carrier; both must remain untouched.
RANKAR_BUNDLE_ENTITY_COUNT = 6
RANKAR_BUNDLE_BUFFER_SIZE = 0x8148
RANKAR_BUNDLE_POINTERS = (
    (0x0050, 0x8148),
    (0x446C, 0x1860C),
    (0x5F40, 0x22074),
    (0x79C8, 0x2EBD0),
    (0x0000, 0x0000),
    (0x0000, 0x0000),
)
RANKAR_WELTALL_CONTROLLER_RANGE = (0x5F40, 0x79C8)
RANKAR_WELTALL_CONTROLLER_SHA256 = (
    "77dccd2fda89da1f9f9095487ed02b9d7ed0323d50f1191a6b91778e3c2f32f3"
)
RANKAR_WELTALL_GEOMETRY_RANGE = (0x22074, 0x2EBD0)
RANKAR_WELTALL_GEOMETRY_SHA256 = (
    "b00a8cc8c0f72487f6d1f78307a6c4c3e56bc3f7a211d83b0c265e65f48ac9e5"
)
RANKAR_BUNDLE_RESULT_SIZE = 201_624
RANKAR_BUNDLE_RESULT_SHA256 = (
    "a4b24c434edc96f4ea616669d2455342424f170e53bcdf2698245854a7060298"
)
RANKAR_BUNDLE_RESULT_BUFFER_SIZE = 0x8FA8
RANKAR_BUNDLE_RESULT_POINTERS = (
    (0x0050, 0x8FA8),
    (0x446C, 0x1946C),
    (0x5F40, 0x22ED4),
    (0x8828, 0x2FB0C),
    (0x0000, 0x0000),
    (0x0000, 0x0000),
)

SYSTEM_NAMES_DECODED_SIZE = 29_048
SYSTEM_NAMES_DECODED_SHA256 = (
    "ac9e9eccf6899af438168303d063b1e25b044385768e1e712ef059f3226e63d7"
)
SYSTEM_NAMES_WELTALL_ENTRY = 28
SYSTEM_NAMES_WELTALL2_ENTRY = 29
SYSTEM_NAMES_COMMAND_ENTRY_SHA256 = (
    "639340e6ec8ab5234abd6f648ab17f3886336428315ddead5b765f3f6675aa5c"
)

SYSTEM_DATA_WELTALL_ENTRY = 22
SYSTEM_DATA_WELTALL2_ENTRY = 23
LIVE_BATTLE_WELTALL_ENTRY = 16
LIVE_BATTLE_WELTALL2_ENTRY = 17
WELTALL_STATS_ENTRY_SHA256 = (
    "9da817280a505b15b3cd0db0cf37d81b9e1dd4344fcca9ddc336a74b94bb56d8"
)
WELTALL2_STATS_ENTRY_SHA256 = (
    "bc9de1d339b615447a3da8db189f28a9de32d17b4d0591a97ee57fac025ad6ae"
)

GEAR_SHOP_MODEL_TABLE = 0x11D7C
GEAR_SHOP_POSE_TABLE = 0x11DA0
GEAR_SHOP_WELTALL_MODEL = 0x06BA
GEAR_SHOP_WELTALL2_MODEL = 0x070E
GEAR_SHOP_WELTALL_POSE = 0x0D
GEAR_SHOP_WELTALL2_POSE = 0x04

BATTLING_DIALOGUE_CANONICAL_ID = 1050
BATTLING_DIALOGUE_SOURCE_SIZE = 47_671
BATTLING_DIALOGUE_SOURCE_SHA256 = (
    "d79e26e2ba4daed706a41de5ae8a585e1761760706e854154c9a53b364d0b3c1"
)
BATTLING_ROSTER_DIALOGUE_ID = 0x011D
BATTLING_ROSTER_SOURCE_DIMENSIONS = bytes.fromhex("38 05")
BATTLING_ROSTER_RESULT_DIMENSIONS = bytes.fromhex("38 04")
BATTLING_ROSTER_REMOVED_SUFFIX = bytes.fromhex(
    "01 10 10 10 10 0F 05 0B 00"
)
BATTLING_DIALOGUE_RESULT_SIZE = 47_663
BATTLING_DIALOGUE_RESULT_SHA256 = (
    "51cd7696b98eac3799cd1bb4288de59f9697cb5e231c29783458f24bb30a3e19"
)


@dataclass(frozen=True)
class GlobalReplacement:
    canonical_id: int
    filename: str
    role: str
    data: bytes


class Weltall2GlobalPatchError(RuntimeError):
    """Raised when a global Weltall/Weltall-2 contract changes."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_identity(canonical_id: int, data: bytes) -> None:
    try:
        expected_size, expected_hash = SOURCE_IDENTITIES[canonical_id]
    except KeyError as exc:
        raise Weltall2GlobalPatchError(
            f"No source identity for canonical {canonical_id}"
        ) from exc
    actual_hash = _sha256(data)
    if len(data) != expected_size or actual_hash != expected_hash:
        raise Weltall2GlobalPatchError(
            f"Canonical {canonical_id} source mismatch: {len(data)} bytes, "
            f"SHA-256 {actual_hash}; expected {expected_size}, {expected_hash}"
        )


def _archive_entries(data: bytes) -> tuple[tuple[int, ...], tuple[bytes, ...]]:
    if len(data) < 8:
        raise Weltall2GlobalPatchError("Indexed archive is shorter than its header")
    count = struct.unpack_from("<I", data, 0)[0]
    table_end = 4 + 4 * count
    if count == 0 or table_end > len(data):
        raise Weltall2GlobalPatchError("Indexed archive header is invalid")
    offsets = struct.unpack_from(f"<{count}I", data, 4)
    if (
        offsets[0] < table_end
        or any(offset % 4 for offset in offsets)
        or any(left >= right for left, right in zip(offsets, offsets[1:]))
        or offsets[-1] >= len(data)
    ):
        raise Weltall2GlobalPatchError("Indexed archive offsets are invalid")
    entries = tuple(
        data[start : offsets[index + 1] if index + 1 < count else len(data)]
        for index, start in enumerate(offsets)
    )
    return offsets, entries


def _alias_archive_entry(
    source: bytes,
    *,
    canonical_id: int,
    target_entry: int,
    donor_entry: int,
    expected_result: tuple[int, str],
) -> bytes:
    _validate_identity(canonical_id, source)
    offsets, original = _archive_entries(source)
    if not 0 <= target_entry < len(original) or not 0 <= donor_entry < len(original):
        raise Weltall2GlobalPatchError("Gear archive alias index is out of range")
    if _sha256(original[target_entry]) != WELTALL_STATS_ENTRY_SHA256:
        raise Weltall2GlobalPatchError("Weltall combat table identity changed")
    if _sha256(original[donor_entry]) != WELTALL2_STATS_ENTRY_SHA256:
        raise Weltall2GlobalPatchError("Weltall-2 combat table identity changed")

    entries = list(original)
    entries[target_entry] = original[donor_entry]
    rebuilt = bytearray(source[: offsets[0]])
    rebuilt_offsets: list[int] = []
    for entry in entries:
        rebuilt_offsets.append(len(rebuilt))
        rebuilt.extend(entry)
        rebuilt.extend(bytes((-len(rebuilt)) % 4))
    struct.pack_into(f"<{len(entries)}I", rebuilt, 4, *rebuilt_offsets)
    result = bytes(rebuilt)

    _, checked_entries = _archive_entries(result)
    for index, (before, after) in enumerate(
        zip(original, checked_entries, strict=True)
    ):
        expected = original[donor_entry] if index == target_entry else before
        if after != expected:
            raise Weltall2GlobalPatchError(
                f"Combat archive alias changed unrelated entry {index}"
            )
    expected_size, expected_hash = expected_result
    if len(result) != expected_size or _sha256(result) != expected_hash:
        raise Weltall2GlobalPatchError(
            f"Canonical {canonical_id} aliased result identity changed"
        )
    return result


def validate_shared_command_names(source: bytes) -> None:
    """Prove Gear IDs 0 and 1 already use the same battle command names."""

    _validate_identity(SYSTEM_NAMES_ID, source)
    declared = struct.unpack_from("<I", source, 0)[0]
    if declared != SYSTEM_NAMES_DECODED_SIZE:
        raise Weltall2GlobalPatchError("System-name decoded size changed")
    decoded = decompress_lzss(source + bytes(32), declared).data
    if _sha256(decoded) != SYSTEM_NAMES_DECODED_SHA256:
        raise Weltall2GlobalPatchError("Decoded system-name identity changed")
    _, entries = _archive_entries(decoded)
    weltall = entries[SYSTEM_NAMES_WELTALL_ENTRY]
    weltall2 = entries[SYSTEM_NAMES_WELTALL2_ENTRY]
    if (
        weltall != weltall2
        or _sha256(weltall) != SYSTEM_NAMES_COMMAND_ENTRY_SHA256
    ):
        raise Weltall2GlobalPatchError(
            "Weltall and Weltall-2 no longer share the audited command names"
        )


def patch_system_data(source: bytes) -> bytes:
    """Alias Gear-0's system/menu combat table to native Weltall-2."""

    return _alias_archive_entry(
        source,
        canonical_id=SYSTEM_DATA_ID,
        target_entry=SYSTEM_DATA_WELTALL_ENTRY,
        donor_entry=SYSTEM_DATA_WELTALL2_ENTRY,
        expected_result=SYSTEM_DATA_RESULT,
    )


def patch_live_battle_stats(source: bytes) -> bytes:
    """Alias Gear-0's live-battle table to native Weltall-2."""

    return _alias_archive_entry(
        source,
        canonical_id=LIVE_BATTLE_STATS_ID,
        target_entry=LIVE_BATTLE_WELTALL_ENTRY,
        donor_entry=LIVE_BATTLE_WELTALL2_ENTRY,
        expected_result=LIVE_BATTLE_STATS_RESULT,
    )


def patch_gear_shop_menu(source: bytes) -> bytes:
    """Make the Gear-0 shop preview select Weltall-2's model and pose."""

    _validate_identity(GEAR_SHOP_MENU_ID, source)
    model0 = GEAR_SHOP_MODEL_TABLE
    model1 = model0 + 2
    if struct.unpack_from("<H", source, model0)[0] != GEAR_SHOP_WELTALL_MODEL:
        raise Weltall2GlobalPatchError("Gear shop Weltall model selector changed")
    if struct.unpack_from("<H", source, model1)[0] != GEAR_SHOP_WELTALL2_MODEL:
        raise Weltall2GlobalPatchError("Gear shop Weltall-2 model selector changed")
    pose0 = GEAR_SHOP_POSE_TABLE
    pose1 = pose0 + 1
    if source[pose0] != GEAR_SHOP_WELTALL_POSE:
        raise Weltall2GlobalPatchError("Gear shop Weltall pose selector changed")
    if source[pose1] != GEAR_SHOP_WELTALL2_POSE:
        raise Weltall2GlobalPatchError("Gear shop Weltall-2 pose selector changed")

    patched = bytearray(source)
    patched[model0 : model0 + 2] = source[model1 : model1 + 2]
    patched[pose0] = source[pose1]
    result = bytes(patched)
    changed = {
        index
        for index, (before, after) in enumerate(zip(source, result, strict=True))
        if before != after
    }
    if changed != {model0, model0 + 1, pose0}:
        raise Weltall2GlobalPatchError("Gear shop patch changed unaudited bytes")
    expected_size, expected_hash = GEAR_SHOP_MENU_RESULT
    if len(result) != expected_size or _sha256(result) != expected_hash:
        raise Weltall2GlobalPatchError("Patched Gear shop identity changed")
    return result


def _battle_bundle_pointers(source: bytes) -> tuple[tuple[int, int], ...]:
    """Return the controller/visual-data pointers from a battle sprite bundle."""

    count = source[0] if source else 0
    header_end = 8 + count * 0x0C
    if count == 0 or header_end > len(source):
        raise Weltall2GlobalPatchError("Battle sprite bundle header is invalid")
    return tuple(
        struct.unpack_from("<II", source, 8 + index * 0x0C)
        for index in range(count)
    )


def patch_rankar_intro_battle_bundle(
    source: bytes,
    *,
    weltall2_controller: bytes,
    weltall2_geometry: bytes,
    transform_weltall_geometry: bytes,
) -> bytes:
    """Replace only the dropped Weltall embedded in the Rankar intro."""

    _validate_identity(RANKAR_INTRO_BATTLE_BUNDLE_ID, source)
    _validate_identity(
        field3d.FIELD_TRANSFORM_WELTALL_GEOMETRY_ID,
        transform_weltall_geometry,
    )
    field3d.validate_retail_resource(
        field3d.FIELD_WELTALL2_CONTROLLER_ID,
        weltall2_controller,
    )
    field3d.validate_retail_resource(
        field3d.FIELD_WELTALL2_GEOMETRY_ID,
        weltall2_geometry,
    )
    if source[0] != RANKAR_BUNDLE_ENTITY_COUNT:
        raise Weltall2GlobalPatchError("Rankar bundle entity count changed")
    if struct.unpack_from("<I", source, 4)[0] != RANKAR_BUNDLE_BUFFER_SIZE:
        raise Weltall2GlobalPatchError("Rankar bundle buffer boundary changed")
    if _battle_bundle_pointers(source) != RANKAR_BUNDLE_POINTERS:
        raise Weltall2GlobalPatchError("Rankar bundle resource pointers changed")

    controller_start, controller_end = RANKAR_WELTALL_CONTROLLER_RANGE
    geometry_start, geometry_end = RANKAR_WELTALL_GEOMETRY_RANGE
    old_controller = source[controller_start:controller_end]
    old_geometry = source[geometry_start:geometry_end]
    if _sha256(old_controller) != RANKAR_WELTALL_CONTROLLER_SHA256:
        raise Weltall2GlobalPatchError(
            "Rankar intro embedded Weltall controller changed"
        )
    if _sha256(old_geometry) != RANKAR_WELTALL_GEOMETRY_SHA256:
        raise Weltall2GlobalPatchError(
            "Rankar intro embedded Weltall geometry changed"
        )

    # The visual is byte-for-byte canonical model 7 (2159).  Pin that exact
    # relationship so Rankar or the carrier can never be mistaken for it.
    if old_geometry != transform_weltall_geometry:
        raise Weltall2GlobalPatchError(
            "Rankar intro entry 2 is no longer the model-7 Weltall variant"
        )

    try:
        new_controller = field3d.build_rankar_transform_compat_controller(
            weltall2_controller
        )
    except field3d.Weltall2Field3DError as exc:
        raise Weltall2GlobalPatchError(str(exc)) from exc
    controller_delta = len(new_controller) - len(old_controller)
    geometry_delta = len(weltall2_geometry) - len(old_geometry)
    result = bytearray(
        source[:controller_start]
        + new_controller
        + source[controller_end:geometry_start]
        + weltall2_geometry
        + source[geometry_end:]
    )

    def relocate(value: int) -> int:
        if value >= geometry_end:
            return value + controller_delta + geometry_delta
        if value >= controller_end:
            return value + controller_delta
        return value

    struct.pack_into("<I", result, 4, relocate(RANKAR_BUNDLE_BUFFER_SIZE))
    for index, (control, visual) in enumerate(RANKAR_BUNDLE_POINTERS):
        offset = 8 + index * 0x0C
        if control > 7:
            struct.pack_into("<I", result, offset, relocate(control))
        if visual > 7:
            struct.pack_into("<I", result, offset + 4, relocate(visual))
    patched = bytes(result)

    if (
        struct.unpack_from("<I", patched, 4)[0]
        != RANKAR_BUNDLE_RESULT_BUFFER_SIZE
        or _battle_bundle_pointers(patched) != RANKAR_BUNDLE_RESULT_POINTERS
    ):
        raise Weltall2GlobalPatchError(
            "Rankar bundle pointers did not relocate to the audited layout"
        )
    new_geometry_start = RANKAR_BUNDLE_RESULT_POINTERS[2][1]
    if (
        patched[controller_start:controller_start + len(new_controller)]
        != new_controller
        or patched[
            new_geometry_start:new_geometry_start + len(weltall2_geometry)
        ]
        != weltall2_geometry
    ):
        raise Weltall2GlobalPatchError(
            "Rankar bundle did not install complete Weltall-2 resources"
        )
    if (
        patched[controller_start + len(new_controller):new_geometry_start]
        != source[controller_end:geometry_start]
        or patched[new_geometry_start + len(weltall2_geometry):]
        != source[geometry_end:]
    ):
        raise Weltall2GlobalPatchError(
            "Rankar bundle changed a neighboring mecha or sprite payload"
        )
    if (
        len(patched) != RANKAR_BUNDLE_RESULT_SIZE
        or _sha256(patched) != RANKAR_BUNDLE_RESULT_SHA256
    ):
        raise Weltall2GlobalPatchError("Patched Rankar bundle identity changed")
    return patched


def patch_battling_roster_dialogue(source: bytes) -> bytes:
    """Remove the duplicate regular-Weltall choice from field 222's menu.

    This component contains one unrelated retail block with data after its
    first Close control, so a semantic whole-component re-encoder would be
    lossy.  Perform a checked surgical rebuild instead: remove only the final
    line from block 0x11D, lower its height, and shift later u16 offsets.
    """

    if (
        len(source) != BATTLING_DIALOGUE_SOURCE_SIZE
        or _sha256(source) != BATTLING_DIALOGUE_SOURCE_SHA256
    ):
        raise Weltall2GlobalPatchError("Field 222 dialogue identity changed")
    block_count = struct.unpack_from("<I", source, 0)[0] + 1
    if block_count <= BATTLING_ROSTER_DIALOGUE_ID:
        raise Weltall2GlobalPatchError("Field 222 roster dialogue is missing")
    offsets = list(struct.unpack_from(f"<{block_count}H", source, 4))
    header_size = 4 + 4 * block_count
    if (
        offsets[0] != header_size
        or offsets != sorted(offsets)
        or len(set(offsets)) != len(offsets)
    ):
        raise Weltall2GlobalPatchError("Field 222 dialogue offsets are invalid")

    block_id = BATTLING_ROSTER_DIALOGUE_ID
    start = offsets[block_id]
    end = offsets[block_id + 1]
    payload = source[start:end]
    if not payload.endswith(BATTLING_ROSTER_REMOVED_SUFFIX):
        raise Weltall2GlobalPatchError("Field 222 roster dialogue text changed")
    dimensions = 4 + 2 * block_count
    dimension_offset = dimensions + 2 * block_id
    if source[dimension_offset : dimension_offset + 2] != (
        BATTLING_ROSTER_SOURCE_DIMENSIONS
    ):
        raise Weltall2GlobalPatchError("Field 222 roster dialogue dimensions changed")

    # Preserve the final Close byte while removing newline + indentation +
    # the dynamic <Weltall> token immediately before it.
    remove_start = end - len(BATTLING_ROSTER_REMOVED_SUFFIX)
    remove_end = end - 1
    removed_size = remove_end - remove_start
    rebuilt = bytearray(source[:remove_start] + source[remove_end:])
    for index in range(block_id + 1, block_count):
        offsets[index] -= removed_size
    struct.pack_into(f"<{block_count}H", rebuilt, 4, *offsets)
    rebuilt[dimension_offset : dimension_offset + 2] = (
        BATTLING_ROSTER_RESULT_DIMENSIONS
    )
    result = bytes(rebuilt)

    # Every byte outside the offset-table suffix, one dimension byte, and the
    # removed line must remain in its original order.
    expected_size = BATTLING_DIALOGUE_RESULT_SIZE
    expected_hash = BATTLING_DIALOGUE_RESULT_SHA256
    if len(result) != expected_size or _sha256(result) != expected_hash:
        raise Weltall2GlobalPatchError("Patched field 222 dialogue identity changed")
    new_end = offsets[block_id + 1]
    new_payload = result[offsets[block_id] : new_end]
    if (
        bytes.fromhex("0F 05 0B") in new_payload
        or not new_payload.endswith(bytes.fromhex("0F 05 0C 00"))
    ):
        raise Weltall2GlobalPatchError("Regular Weltall remains in roster dialogue")
    return result


def patch_field_scripts(source: bytes, canonical_id: int) -> bytes:
    """Patch checked persistent and Battling Weltall selectors in one field."""

    if canonical_id not in FIELD_SCRIPT_IDS:
        raise Weltall2GlobalPatchError(
            f"Canonical {canonical_id} is not an audited Weltall script field"
        )
    _validate_identity(canonical_id, source)
    parsed = parse_field(source)
    components = [part.data for part in parsed.parts]
    script = bytearray(components[SCRIPT_INDEX])
    atel = AtelScript(script)
    bytecode = atel.bytecode
    expected_count = FIELD_ASSIGNMENT_COUNTS.get(canonical_id, 0)
    if bytecode.count(WELTALL_ASSIGNMENT) != expected_count:
        raise Weltall2GlobalPatchError(
            f"Canonical {canonical_id} has an unexpected Weltall assignment count"
        )

    original_script = bytes(script)
    cursor = 0
    changed_offsets: set[int] = set()
    for _ in range(expected_count):
        relative = bytecode.find(WELTALL_ASSIGNMENT, cursor)
        if relative < 0:
            raise Weltall2GlobalPatchError("Weltall assignment scan lost a match")
        absolute = atel.bytecode_offset + relative
        script[absolute : absolute + len(WELTALL_ASSIGNMENT)] = WELTALL2_ASSIGNMENT
        changed_offsets.add(absolute + 4)
        cursor = relative + len(WELTALL_ASSIGNMENT)

    for patch in FIELD_BATTLING_PATCHES.get(canonical_id, ()):
        absolute = atel.bytecode_offset + patch.pc
        end = absolute + len(patch.before)
        if bytes(script[absolute:end]) != patch.before:
            raise Weltall2GlobalPatchError(
                f"Canonical {canonical_id} Battling context changed at "
                f"PC 0x{patch.pc:04X}: {patch.role}"
            )
        if len(patch.before) != len(patch.after):
            raise Weltall2GlobalPatchError("Battling patch changes script length")
        script[absolute:end] = patch.after
        changed_offsets.update(
            absolute + relative
            for relative, (before, after) in enumerate(
                zip(patch.before, patch.after, strict=True)
            )
            if before != after
        )

    actual_changed = {
        index
        for index, (before, after) in enumerate(
            zip(original_script, script, strict=True)
        )
        if before != after
    }
    if actual_changed != changed_offsets:
        raise Weltall2GlobalPatchError(
            f"Canonical {canonical_id} changed bytes outside Gear operands"
        )
    checked = AtelScript(script).bytecode
    if checked.count(WELTALL_ASSIGNMENT) != 0:
        raise Weltall2GlobalPatchError(
            f"Canonical {canonical_id} still assigns regular Weltall"
        )
    components[SCRIPT_INDEX] = bytes(script)
    changed_components = {SCRIPT_INDEX}
    if canonical_id == BATTLING_DIALOGUE_CANONICAL_ID:
        components[DIALOGUE_INDEX] = patch_battling_roster_dialogue(
            components[DIALOGUE_INDEX]
        )
        changed_components.add(DIALOGUE_INDEX)
    result = build_field_preserving(
        source,
        components,
        tuple(sorted(changed_components)),
        compact_changed=True,
    )

    reparsed = parse_field(result)
    for index, (before, after) in enumerate(
        zip(parsed.parts, reparsed.parts, strict=True)
    ):
        expected = components[index] if index in changed_components else before.data
        if after.data != expected:
            raise Weltall2GlobalPatchError(
                f"Canonical {canonical_id} changed field component {index}"
            )
    expected_size, expected_hash = FIELD_RESULT_IDENTITIES[canonical_id]
    if len(result) != expected_size or _sha256(result) != expected_hash:
        raise Weltall2GlobalPatchError(
            f"Canonical {canonical_id} patched field identity changed"
        )
    return result


def patch_field_assignments(source: bytes, canonical_id: int) -> bytes:
    """Compatibility wrapper for callers patching an assignment field."""

    if canonical_id not in FIELD_ASSIGNMENT_COUNTS:
        raise Weltall2GlobalPatchError(
            f"Canonical {canonical_id} is not an audited assignment field"
        )
    return patch_field_scripts(source, canonical_id)


MODEL_ALIASES = (
    (
        BATTLING_WELTALL_ID,
        BATTLING_WELTALL2_ID,
        "Battling roster-0 bundle aliased to native roster-10 Weltall-2 fallback",
    ),
    (
        FIELD_WELTALL_ID,
        FIELD_WELTALL2_ID,
        "regular Weltall global field sprite aliased to Weltall-2",
    ),
    (
        field3d.FIELD_WELTALL_GEOMETRY_ID,
        field3d.FIELD_WELTALL2_GEOMETRY_ID,
        "regular Weltall 3D field/cutscene geometry aliased to Weltall-2",
    ),
    (
        field3d.FIELD_TRANSFORM_WELTALL_GEOMETRY_ID,
        field3d.FIELD_WELTALL2_GEOMETRY_ID,
        "scripted model-7 Weltall geometry aliased to Weltall-2",
    ),
    (
        BATTLE_WELTALL_MODEL_ID,
        BATTLE_WELTALL2_MODEL_ID,
        "regular Weltall battle geometry aliased to Weltall-2",
    ),
    (
        BATTLE_WELTALL_ANIMATION_ID,
        BATTLE_WELTALL2_ANIMATION_ID,
        "regular Weltall battle animations aliased to Weltall-2",
    ),
    (
        EQUIPMENT_WELTALL_PREVIEW_ID,
        EQUIPMENT_WELTALL2_PREVIEW_ID,
        "regular Weltall equipment preview aliased to Weltall-2",
    ),
    (
        WORLDMAP_WELTALL_ID,
        WORLDMAP_WELTALL2_ID,
        "regular Weltall world-map sprite aliased to Weltall-2",
    ),
    (
        WORLDMAP_WELTALL_ALIAS_ID,
        WORLDMAP_WELTALL2_ID,
        "dormant Gear-10 Weltall world-map alias replaced by Weltall-2",
    ),
)

GLOBAL_REPLACEMENT_IDS = frozenset(
    (
        *(target for target, _donor, _role in MODEL_ALIASES),
        field3d.FIELD_WELTALL_CONTROLLER_ID,
        field3d.FIELD_TRANSFORM_WELTALL_CONTROLLER_ID,
        SYSTEM_DATA_ID,
        GEAR_SHOP_MENU_ID,
        LIVE_BATTLE_STATS_ID,
        RANKAR_INTRO_BATTLE_BUNDLE_ID,
        *FIELD_SCRIPT_IDS,
    )
)


def build_global_replacements(
    resources: Mapping[int, bytes],
) -> tuple[GlobalReplacement, ...]:
    """Return the complete checked global Weltall-to-Weltall-2 payload set."""

    missing = sorted(set(SOURCE_IDENTITIES) - set(resources))
    if missing:
        raise Weltall2GlobalPatchError(
            f"Global Weltall-2 inputs are missing canonical IDs {missing}"
        )
    for canonical_id, data in resources.items():
        if canonical_id in SOURCE_IDENTITIES:
            _validate_identity(canonical_id, data)
    validate_shared_command_names(resources[SYSTEM_NAMES_ID])

    replacements: list[GlobalReplacement] = []
    try:
        compatibility_controller = field3d.build_compat_controller(
            resources[field3d.FIELD_WELTALL2_CONTROLLER_ID]
        )
    except field3d.Weltall2Field3DError as exc:
        raise Weltall2GlobalPatchError(str(exc)) from exc
    replacements.extend(
        (
            GlobalReplacement(
                field3d.FIELD_WELTALL_CONTROLLER_ID,
                "2144_weltall_slot_uses_weltall2_compat_controller.bin",
                "Weltall-2-native 23-index controller for 3D field/cutscene scenes",
                compatibility_controller,
            ),
            GlobalReplacement(
                field3d.FIELD_TRANSFORM_WELTALL_CONTROLLER_ID,
                "2158_scripted_weltall_uses_weltall2_compat_controller.bin",
                "Weltall-2-native controller for model-7 cinematic scenes",
                compatibility_controller,
            ),
        )
    )
    for target, donor, role in MODEL_ALIASES:
        replacements.append(
            GlobalReplacement(
                target,
                f"{target:04d}_weltall_slot_uses_weltall2.bin",
                role,
                resources[donor],
            )
        )
    replacements.extend(
        (
            GlobalReplacement(
                SYSTEM_DATA_ID,
                "2594_weltall_combat_table_uses_weltall2.bin",
                "Gear-0 system/menu combat data aliased to native Gear 1",
                patch_system_data(resources[SYSTEM_DATA_ID]),
            ),
            GlobalReplacement(
                GEAR_SHOP_MENU_ID,
                "2602_weltall_shop_preview_uses_weltall2.bin",
                "Gear-parts shop model and pose aliases for Gear 0",
                patch_gear_shop_menu(resources[GEAR_SHOP_MENU_ID]),
            ),
            GlobalReplacement(
                LIVE_BATTLE_STATS_ID,
                "2614_weltall_live_battle_uses_weltall2.bin",
                "Gear-0 live-battle data aliased to native Gear 1",
                patch_live_battle_stats(resources[LIVE_BATTLE_STATS_ID]),
            ),
            GlobalReplacement(
                RANKAR_INTRO_BATTLE_BUNDLE_ID,
                "2641_rankar_intro_dropped_weltall_uses_weltall2.bin",
                "Blackmoon Rankar intro's embedded model-7 Weltall rebuilt as Weltall-2",
                patch_rankar_intro_battle_bundle(
                    resources[RANKAR_INTRO_BATTLE_BUNDLE_ID],
                    weltall2_controller=resources[
                        field3d.FIELD_WELTALL2_CONTROLLER_ID
                    ],
                    weltall2_geometry=resources[
                        field3d.FIELD_WELTALL2_GEOMETRY_ID
                    ],
                    transform_weltall_geometry=resources[
                        field3d.FIELD_TRANSFORM_WELTALL_GEOMETRY_ID
                    ],
                ),
            ),
        )
    )
    for canonical_id in sorted(FIELD_SCRIPT_IDS):
        field = FIELD_NUMBERS[canonical_id]
        assignment_count = FIELD_ASSIGNMENT_COUNTS.get(canonical_id, 0)
        battling_count = len(FIELD_BATTLING_PATCHES.get(canonical_id, ()))
        replacements.append(
            GlobalReplacement(
                canonical_id,
                f"{canonical_id:04d}_field_{field:03d}_weltall2_selectors.bin",
                f"field {field}: {assignment_count} persistent and "
                f"{battling_count} Battling Weltall selectors changed",
                patch_field_scripts(resources[canonical_id], canonical_id),
            )
        )

    ids = frozenset(item.canonical_id for item in replacements)
    if ids != GLOBAL_REPLACEMENT_IDS or len(ids) != len(replacements):
        raise Weltall2GlobalPatchError(
            f"Global replacement inventory changed: {sorted(ids)}"
        )
    return tuple(sorted(replacements, key=lambda item: item.canonical_id))


__all__ = [
    "FIELD_ASSIGNMENT_COUNTS",
    "FIELD_BATTLING_PATCHES",
    "FIELD_SCRIPT_IDS",
    "GLOBAL_REPLACEMENT_IDS",
    "GlobalReplacement",
    "MODEL_ALIASES",
    "RANKAR_INTRO_BATTLE_BUNDLE_ID",
    "SOURCE_IDENTITIES",
    "WELTALL_ASSIGNMENT",
    "WELTALL2_ASSIGNMENT",
    "Weltall2GlobalPatchError",
    "build_global_replacements",
    "patch_field_assignments",
    "patch_field_scripts",
    "patch_battling_roster_dialogue",
    "patch_gear_shop_menu",
    "patch_live_battle_stats",
    "patch_rankar_intro_battle_bundle",
    "patch_system_data",
    "validate_shared_command_names",
]
