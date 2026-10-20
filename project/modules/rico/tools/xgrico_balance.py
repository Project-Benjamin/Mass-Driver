#!/usr/bin/env python3
"""Rico anthology character, item, and persistent weight balancing.

The retail game stores each character's weight as a fixed byte, a mutable
byte, and one decimal digit.  Weight-loss items already stop the mutable byte
at zero.  This module treats the fixed byte as a body-appropriate minimum and
patches the retail weight-gain routine so the mutable byte also has a
character-specific ceiling.

It also turns the Memento accessory into an Attack/Defense/Agility item,
prepares Rico's anthology stats and complete ability masks, and repacks the
clean USA battle overlay after installing the restored battle-weight hooks.
Every binary mutation is guarded by the audited retail identity and context.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import struct
from typing import Final, Sequence

from shared.tools.xgbattle_weight import (
    BATTLE_OVERLAY_CLEAN_DECODED_PATCHED_SHA256,
    BATTLE_OVERLAY_CLEAN_DECODED_RETAIL_SHA256,
    patch_decoded_battle_overlay,
)
from shared.tools.xgdialog import PLAIN_ENCODE
from shared.tools.xgfield import compress_lzss


class RicoBalanceError(ValueError):
    """An input no longer matches the audited USA retail resource."""


@dataclass(frozen=True)
class WeightProfile:
    """One character's native 2.20-lb weight interval."""

    character_id: int
    name: str
    minimum_native: int
    default_native: int
    maximum_native: int

    @property
    def minimum_hundredths_lb(self) -> int:
        return self.minimum_native * 220

    @property
    def default_hundredths_lb(self) -> int:
        return self.default_native * 220

    @property
    def maximum_hundredths_lb(self) -> int:
        return self.maximum_native * 220

    @property
    def initial_mutable(self) -> int:
        return self.default_native - self.minimum_native

    @property
    def mutable_cap(self) -> int:
        return self.maximum_native - self.minimum_native


# Values are exact native increments: each whole unit is 2.20 lb.  Citan's
# sword form and Emeralda's adult form retain the same mass intervals as their
# paired records.  Emeralda is a nanomachine colony, so her transformation is
# a change of shape rather than ordinary biological weight gain.
WEIGHT_PROFILES: Final = (
    WeightProfile(0, "Fei", 66, 76, 85),          # 145.2 / 167.2 / 187.0
    WeightProfile(1, "Elly", 43, 53, 68),         #  94.6 / 116.6 / 149.6
    WeightProfile(2, "Citan", 65, 72, 85),        # 143.0 / 158.4 / 187.0
    WeightProfile(3, "Bart", 66, 74, 88),         # 145.2 / 162.8 / 193.6
    WeightProfile(4, "Billy", 48, 54, 66),        # 105.6 / 118.8 / 145.2
    WeightProfile(5, "Rico", 96, 160, 190),       # 211.2 / 352.0 / 418.0
    WeightProfile(6, "Emeralda", 80, 96, 110),    # 176.0 / 211.2 / 242.0
    WeightProfile(7, "Chu-Chu", 16, 22, 32),      #  35.2 /  48.4 /  70.4
    WeightProfile(8, "Maria", 23, 28, 36),        #  50.6 /  61.6 /  79.2
    WeightProfile(9, "Sword Citan", 65, 72, 85),
    WeightProfile(10, "Adult Emeralda", 80, 96, 110),
)

if tuple(profile.character_id for profile in WEIGHT_PROFILES) != tuple(range(11)):
    raise RuntimeError("weight profiles must cover character IDs 0 through 10")
for _profile in WEIGHT_PROFILES:
    if not (
        0 <= _profile.minimum_native
        <= _profile.default_native
        <= _profile.maximum_native
        <= 0xFF
        and _profile.initial_mutable <= 0xFF
        and _profile.mutable_cap <= 0xFF
    ):
        raise RuntimeError(f"invalid weight profile: {_profile}")

MUTABLE_WEIGHT_CAPS: Final = bytes(
    profile.mutable_cap for profile in WEIGHT_PROFILES
)


def clamp_mutable_weight(character_id: int, mutable_weight: int) -> int:
    """Return the value enforced by the injected weight-gain helper."""

    if not 0 <= character_id < len(WEIGHT_PROFILES):
        raise ValueError(f"character ID is outside 0..10: {character_id}")
    if not 0 <= mutable_weight <= 0xFF:
        raise ValueError(f"mutable weight is not an unsigned byte: {mutable_weight}")
    return min(mutable_weight, MUTABLE_WEIGHT_CAPS[character_id])


# Initial GameState layout and anthology-facing Rico balance.
GAMESTATE_SIZE: Final = 0x2358
PARTY_RECORD_BASE: Final = 0x26C
PARTY_RECORD_SIZE: Final = 0xA4
CHARACTER_ID_OFFSET: Final = 0x56
ATTACK_OFFSET: Final = 0x58
DEFENSE_OFFSET: Final = 0x59
WEIGHT_FIXED_OFFSET: Final = 0x77
WEIGHT_MUTABLE_OFFSET: Final = 0x78
WEIGHT_TENTHS_OFFSET: Final = 0x79
FIRST_ACCESSORY_OFFSET: Final = 0x74

RICO_ID: Final = 5
RICO_BASE_ATTACK: Final = 90
RICO_BASE_DEFENSE: Final = 80
MEMENTO_ITEM_ID: Final = 0x8F
# The Memento remains in Kaiser Sigmund's custody during this anthology.
# Keep its system-data definition intact, but never equip it on Rico.
RICO_ACCESSORIES: Final = (0, 0, 0)

# Character slot 10 is adult Emeralda in retail.  The standalone Rico
# anthology never routes that form, so Chapter 1 safely reserves the slot as a
# young-Rico carrier.  Keeping the child in a different party record is what
# lets the ordinary menu show child-scale equipment without overwriting adult
# Rico's equipment state in Chapters 2 through 7.
YOUNG_RICO_ID: Final = 10
YOUNG_RICO_NAME_OFFSET: Final = YOUNG_RICO_ID * 20
YOUNG_RICO_NAME_CELL: Final = bytes.fromhex(
    "31 00 45 00 3F 00 4B 00 "
    "0F 00 0F 00 0F 00 0F 00 0F 00 0F 00"
)
YOUNG_RICO_LEVEL: Final = 1
YOUNG_RICO_HP: Final = 50
YOUNG_RICO_MP: Final = 10
YOUNG_RICO_STATS: Final = bytes.fromhex("0F 0A 0B 07 08 00 0A 0C")
YOUNG_RICO_ACCESSORIES: Final = (0x90, 0x91, 0x92)
YOUNG_RICO_WEIGHT: Final = (30, 10, 0)  # 66.0 / 88.0 / 132.0 lb range
YOUNG_RICO_NO_GEAR: Final = 0xFF

RICO_ABILITY_RECORD: Final = 0x16C0 + RICO_ID * 0x20
RICO_ON_FOOT_DEATHBLOW_MASK: Final = 0xFFC0
RICO_ETHER_MASK: Final = 0xF000
RICO_STIER_DEATHBLOW_MASK: Final = 0x1FF8


def apply_initial_character_balance(source: bytes) -> bytes:
    """Install bounded defaults, Rico's stats, and full abilities."""

    if len(source) != GAMESTATE_SIZE:
        raise RicoBalanceError(
            f"initial GameState is {len(source)} bytes, expected {GAMESTATE_SIZE}"
        )
    result = bytearray(source)
    for profile in WEIGHT_PROFILES:
        record = PARTY_RECORD_BASE + profile.character_id * PARTY_RECORD_SIZE
        actual_id = result[record + CHARACTER_ID_OFFSET]
        if actual_id != profile.character_id:
            raise RicoBalanceError(
                f"{profile.name} record ID is {actual_id}, "
                f"expected {profile.character_id}"
            )
        result[record + WEIGHT_FIXED_OFFSET] = profile.minimum_native
        result[record + WEIGHT_MUTABLE_OFFSET] = profile.initial_mutable
        result[record + WEIGHT_TENTHS_OFFSET] = 0

    rico = PARTY_RECORD_BASE + RICO_ID * PARTY_RECORD_SIZE
    result[rico + ATTACK_OFFSET] = RICO_BASE_ATTACK
    result[rico + DEFENSE_OFFSET] = RICO_BASE_DEFENSE
    result[
        rico + FIRST_ACCESSORY_OFFSET : rico + FIRST_ACCESSORY_OFFSET + 3
    ] = bytes(RICO_ACCESSORIES)
    struct.pack_into(
        "<HHH",
        result,
        RICO_ABILITY_RECORD,
        RICO_ON_FOOT_DEATHBLOW_MASK,
        RICO_ETHER_MASK,
        RICO_STIER_DEATHBLOW_MASK,
    )
    return bytes(result)


def apply_young_rico_anthology_profile(source: bytes) -> bytes:
    """Turn unused character slot 10 into Chapter 1's menu-safe child Rico.

    This deliberately runs after the anthology's general level/deathblow
    initialization.  The child has no weapon, Gear, adult abilities, or
    Memento; his three zero-stat accessories are sentimental household items.
    Adult Rico remains untouched in slot 5.
    """

    if len(source) != GAMESTATE_SIZE:
        raise RicoBalanceError(
            f"initial GameState is {len(source)} bytes, expected {GAMESTATE_SIZE}"
        )
    result = bytearray(source)
    record = PARTY_RECORD_BASE + YOUNG_RICO_ID * PARTY_RECORD_SIZE
    if result[record + CHARACTER_ID_OFFSET] != YOUNG_RICO_ID:
        raise RicoBalanceError("young-Rico carrier record ID changed")

    result[
        YOUNG_RICO_NAME_OFFSET : YOUNG_RICO_NAME_OFFSET + len(YOUNG_RICO_NAME_CELL)
    ] = YOUNG_RICO_NAME_CELL
    struct.pack_into(
        "<HHHH",
        result,
        record + 0x4C,
        YOUNG_RICO_HP,
        YOUNG_RICO_HP,
        YOUNG_RICO_MP,
        YOUNG_RICO_MP,
    )
    result[record + ATTACK_OFFSET : record + ATTACK_OFFSET + 8] = YOUNG_RICO_STATS
    result[record + 0x62 : record + 0x64] = bytes((YOUNG_RICO_LEVEL,) * 2)
    result[record + 0x6A] = 0  # bare hands
    result[
        record + FIRST_ACCESSORY_OFFSET : record + FIRST_ACCESSORY_OFFSET + 3
    ] = bytes(YOUNG_RICO_ACCESSORIES)
    result[record + WEIGHT_FIXED_OFFSET : record + WEIGHT_TENTHS_OFFSET + 1] = bytes(
        YOUNG_RICO_WEIGHT
    )
    result[record + 0xA0] = YOUNG_RICO_NO_GEAR

    # Slot 10 otherwise exposes adult Emeralda's battle abilities.  Chapter 1
    # has no battle and the child should have no adult Skills menu payload.
    ability_record = 0x16C0 + YOUNG_RICO_ID * 0x20
    result[ability_record : ability_record + 0x20] = bytes(0x20)
    return bytes(result)


# ---------------------------------------------------------------------------
# Retail-complete LZSS command groups


def decode_lzss_complete_groups(stream: bytes) -> tuple[bytes, int]:
    """Model the retail decoder, which always executes all eight commands."""

    if len(stream) < 4:
        raise RicoBalanceError("LZSS stream is shorter than its size header")
    declared_size = struct.unpack_from("<I", stream, 0)[0]
    position = 4
    output = bytearray()
    while len(output) < declared_size:
        if position >= len(stream):
            raise RicoBalanceError("LZSS stream ends before a command group")
        control = stream[position]
        position += 1
        for bit in range(8):
            if control & (1 << bit):
                if position + 2 > len(stream):
                    raise RicoBalanceError("LZSS backreference is truncated")
                low = stream[position]
                high = stream[position + 1]
                position += 2
                distance = low | ((high & 0x0F) << 8)
                length = (high >> 4) + 3
                if not 1 <= distance <= len(output):
                    raise RicoBalanceError("LZSS backreference distance is invalid")
                for _ in range(length):
                    output.append(output[-distance])
            else:
                if position >= len(stream):
                    raise RicoBalanceError("LZSS literal is truncated")
                output.append(stream[position])
                position += 1
        if len(output) > declared_size:
            raise RicoBalanceError("LZSS group overruns its declared allocation")
    return bytes(output), position


def compress_lzss_exact_complete_groups(data: bytes) -> bytes:
    """Compress exact-size data and finish on an eight-command boundary."""

    if not data:
        return b"\x00\x00\x00\x00"
    packed = compress_lzss(data)
    position = 4
    output_size = 0
    commands: list[tuple[bool, bytes, int]] = []
    while output_size < len(data):
        if position >= len(packed):
            raise RicoBalanceError("compact LZSS stream lost a control group")
        control = packed[position]
        position += 1
        for bit in range(8):
            if output_size >= len(data):
                break
            is_reference = bool(control & (1 << bit))
            payload_size = 2 if is_reference else 1
            if position + payload_size > len(packed):
                raise RicoBalanceError("compact LZSS command is truncated")
            payload = packed[position : position + payload_size]
            position += payload_size
            command_size = (payload[1] >> 4) + 3 if is_reference else 1
            commands.append((is_reference, payload, command_size))
            output_size += command_size
            if output_size > len(data):
                raise RicoBalanceError("compact LZSS command exceeds source data")

    missing = (-len(commands)) % 8
    command_index = 0
    while missing and command_index < len(commands):
        is_reference, payload, command_size = commands[command_index]
        if not is_reference:
            command_index += 1
            continue
        split_count = min(missing, command_size // 3 - 1)
        if split_count <= 0:
            command_index += 1
            continue
        distance_low = payload[0]
        distance_high = payload[1] & 0x0F
        lengths = [3] * split_count + [command_size - 3 * split_count]
        replacements = [
            (
                True,
                bytes((distance_low, distance_high | ((length - 3) << 4))),
                length,
            )
            for length in lengths
        ]
        commands[command_index : command_index + 1] = replacements
        missing -= split_count
        command_index += len(replacements)
    if missing or len(commands) % 8:
        raise RicoBalanceError(
            "compact LZSS stream cannot end without decoded padding"
        )

    exact = bytearray(struct.pack("<I", len(data)))
    for group_start in range(0, len(commands), 8):
        group = commands[group_start : group_start + 8]
        exact.append(
            sum(
                (1 << bit) if is_reference else 0
                for bit, (is_reference, _, _) in enumerate(group)
            )
        )
        for _, payload, _ in group:
            exact.extend(payload)
    exact.extend(bytes((-len(exact)) % 4))
    result = bytes(exact)
    decoded, consumed = decode_lzss_complete_groups(result)
    if decoded != data or consumed > len(result):
        raise RicoBalanceError("exact LZSS stream failed retail round-trip")
    return result


# ---------------------------------------------------------------------------
# Battle overlay 38


BATTLE_RESOURCE_SIZE: Final = 166_564
BATTLE_RESOURCE_RETAIL_SHA256: Final = (
    "b9c3a15bf5f3eb06bcb3824ef62793b9a500fe1dcb3717fe8963e23e9f27628b"
)
BATTLE_RESOURCE_PATCHED_SIZE: Final = 164_632
BATTLE_RESOURCE_PATCHED_SHA256: Final = (
    "edf070ebf570469ed6a22dbbeeac0004ef56730c83302522c0c79635639a5d90"
)


def patch_battle_weight_resource(source: bytes) -> bytes:
    """Install the verified physical-damage and ATB hooks in canonical 38."""

    actual_hash = hashlib.sha256(source).hexdigest()
    if len(source) != BATTLE_RESOURCE_SIZE or actual_hash != BATTLE_RESOURCE_RETAIL_SHA256:
        raise RicoBalanceError(
            f"battle resource mismatch: {len(source)} bytes, {actual_hash}"
        )
    decoded, consumed = decode_lzss_complete_groups(source + bytes(16))
    if consumed > len(source) + 16:
        raise RicoBalanceError("battle resource decoder consumption is invalid")
    if hashlib.sha256(decoded).hexdigest() != BATTLE_OVERLAY_CLEAN_DECODED_RETAIL_SHA256:
        raise RicoBalanceError("battle resource decoded identity changed")
    patched_decoded = patch_decoded_battle_overlay(decoded)
    if hashlib.sha256(patched_decoded).hexdigest() != BATTLE_OVERLAY_CLEAN_DECODED_PATCHED_SHA256:
        raise RicoBalanceError("patched battle-overlay identity changed")
    result = compress_lzss_exact_complete_groups(patched_decoded)
    actual_patched_hash = hashlib.sha256(result).hexdigest()
    if (
        len(result) != BATTLE_RESOURCE_PATCHED_SIZE
        or actual_patched_hash != BATTLE_RESOURCE_PATCHED_SHA256
    ):
        raise RicoBalanceError(
            f"packed battle patch mismatch: {len(result)}, {actual_patched_hash}"
        )
    round_trip, round_trip_consumed = decode_lzss_complete_groups(result)
    if round_trip != patched_decoded or round_trip_consumed > len(result):
        raise RicoBalanceError("packed battle patch failed retail round-trip")
    return result


# ---------------------------------------------------------------------------
# Young-Rico keepsake names in compressed system-name resource 29


SYSTEM_NAMES_SIZE: Final = 13_768
SYSTEM_NAMES_RETAIL_SHA256: Final = (
    "4b6ca5e621c92d4603ccc4368b05d9d6815f61e098972737ed8af22778a47bc3"
)
SYSTEM_NAMES_DECODED_SIZE: Final = 29_048
SYSTEM_NAMES_DECODED_SHA256: Final = (
    "ac9e9eccf6899af438168303d063b1e25b044385768e1e712ef059f3226e63d7"
)
SYSTEM_NAMES_ARCHIVE_COUNT: Final = 53
EQUIPMENT_NAMES_ARCHIVE_ENTRY: Final = 17
EQUIPMENT_NAMES_SOURCE_RANGE: Final = (0x06EC, 0x0F34)
EQUIPMENT_NAMES_SOURCE_SHA256: Final = (
    "53e9ee5185e8718d07b9c4838255c6223382498db3c11ca62663c9020004b889"
)
YOUNG_RICO_EQUIPMENT_NAMES: Final = {
    0x90: "Toy Gear",
    0x91: "Old Blanket",
    0x92: "Wooden Medal",
}
SYSTEM_NAMES_PATCHED_SIZE: Final = 13_736
SYSTEM_NAMES_PATCHED_SHA256: Final = (
    "c7ff806d8b4ff177901ce993faabc3361a6f465c3d0be2d1f7228c7dfc385966"
)
SYSTEM_NAMES_DECODED_PATCHED_SIZE: Final = 29_076
SYSTEM_NAMES_DECODED_PATCHED_SHA256: Final = (
    "49e359e7440be8703a82aa0bc893f4cd9af16d1099b5e2e6c9551dec3e849ecd"
)


# ---------------------------------------------------------------------------
# Memento and child keepsakes in system data 2594


SYSTEM_DATA_SIZE: Final = 40_336
SYSTEM_DATA_RETAIL_SHA256: Final = (
    "c3bd13cfc3579339a072377dbca30319535aa9ef2aa5f93d464c5ae12c13f4fa"
)
SYSTEM_DATA_ARCHIVE_COUNT: Final = 56
MEMENTO_ITEM_ARCHIVE_ENTRY: Final = 2
MEMENTO_DESCRIPTION_ARCHIVE_ENTRY: Final = 40
MEMENTO_ITEM_RECORD_SIZE: Final = 16
MEMENTO_ITEM_RECORD_OFFSET: Final = 2 + MEMENTO_ITEM_ID * MEMENTO_ITEM_RECORD_SIZE
MEMENTO_ITEM_RETAIL_RECORD: Final = bytes.fromhex(
    "64 00 00 00 22 8F 00 00 00 00 06 18 00 00 FF 07"
)
MEMENTO_ITEM_EFFECT_FLAGS: Final = 0xE006  # Attack, Defense, Agility +6
MEMENTO_DESCRIPTION: Final = "Attack / Defense / Agility + 6"
MEMENTO_DESCRIPTION_DIMENSIONS: Final = bytes((len(MEMENTO_DESCRIPTION) * 2, 1))

YOUNG_RICO_EQUIPMENT_DESCRIPTIONS: Final = {
    0x90: "Rico's favorite toy",
    0x91: "Mended many times by Anne",
    0x92: "A make-believe arena prize",
}

SYSTEM_DATA_PATCHED_SIZE: Final = 40_400
SYSTEM_DATA_PATCHED_SHA256: Final = (
    "26365c5f871889df2acada68a1cf61ef5894f6b1c2b37ec7e4feeccefe8ba689"
)


def _archive_entries(source: bytes, *, expected_count: int) -> tuple[list[bytes], tuple[int, ...]]:
    if len(source) < 4:
        raise RicoBalanceError("system-data archive is truncated")
    count = struct.unpack_from("<I", source, 0)[0]
    if count != expected_count:
        raise RicoBalanceError(f"system-data archive count is {count}, expected {expected_count}")
    table_end = 4 + count * 4
    if table_end > len(source):
        raise RicoBalanceError("system-data archive pointer table is truncated")
    offsets = struct.unpack_from(f"<{count}I", source, 4)
    if (
        offsets[0] < table_end
        or any(left >= right for left, right in zip(offsets, offsets[1:]))
        or offsets[-1] >= len(source)
    ):
        raise RicoBalanceError("system-data archive offsets are invalid")
    entries = [
        source[start : offsets[index + 1] if index + 1 < count else len(source)]
        for index, start in enumerate(offsets)
    ]
    return entries, offsets


def _replace_indexed_string(
    source: bytes,
    *,
    entry_id: int,
    expected_text: bytes,
    expected_dimensions: bytes,
    replacement_text: bytes,
    replacement_dimensions: bytes,
) -> bytes:
    if len(source) < 8:
        raise RicoBalanceError("description string table is truncated")
    maximum_index = struct.unpack_from("<I", source, 0)[0]
    count = maximum_index + 1
    if not 0 <= entry_id < count:
        raise RicoBalanceError("indexed string ID is outside its table")
    pointer_end = 4 + count * 2
    dimensions_end = pointer_end + count * 2
    if dimensions_end > len(source):
        raise RicoBalanceError("description pointer/dimension tables are truncated")
    pointers = list(struct.unpack_from(f"<{count}H", source, 4))
    if (
        pointers[0] != dimensions_end
        or any(left >= right for left, right in zip(pointers, pointers[1:]))
        or pointers[-1] >= len(source)
    ):
        raise RicoBalanceError("description string offsets are invalid")
    strings = [
        source[start : pointers[index + 1] if index + 1 < count else len(source)]
        for index, start in enumerate(pointers)
    ]
    dimension_offset = pointer_end + entry_id * 2
    if (
        strings[entry_id] != expected_text
        or source[dimension_offset : dimension_offset + 2] != expected_dimensions
    ):
        raise RicoBalanceError("indexed string source slot changed")
    strings[entry_id] = replacement_text
    result = bytearray(source[:dimensions_end])
    result[dimension_offset : dimension_offset + 2] = replacement_dimensions
    rebuilt_pointers: list[int] = []
    for value in strings:
        if len(result) > 0xFFFF:
            raise RicoBalanceError("description string offset exceeds u16")
        rebuilt_pointers.append(len(result))
        result.extend(value)
    struct.pack_into(f"<{count}H", result, 4, *rebuilt_pointers)
    return bytes(result)


def _rebuild_archive(entries: Sequence[bytes], *, header_size: int) -> bytes:
    result = bytearray(header_size)
    struct.pack_into("<I", result, 0, len(entries))
    offsets: list[int] = []
    for entry in entries:
        offsets.append(len(result))
        result.extend(entry)
        result.extend(bytes((-len(result)) % 4))
    struct.pack_into(f"<{len(entries)}I", result, 4, *offsets)
    return bytes(result)


def patch_young_rico_equipment_names(source: bytes) -> bytes:
    """Name the three unused zero-stat accessories equipped by child Rico."""

    actual_hash = hashlib.sha256(source).hexdigest()
    if len(source) != SYSTEM_NAMES_SIZE or actual_hash != SYSTEM_NAMES_RETAIL_SHA256:
        raise RicoBalanceError(
            f"system names mismatch: {len(source)} bytes, {actual_hash}"
        )
    decoded, consumed = decode_lzss_complete_groups(source + bytes(16))
    if consumed > len(source) + 16 or (
        len(decoded) != SYSTEM_NAMES_DECODED_SIZE
        or hashlib.sha256(decoded).hexdigest() != SYSTEM_NAMES_DECODED_SHA256
    ):
        raise RicoBalanceError("system names decoded identity changed")

    count = struct.unpack_from("<I", decoded, 0)[0]
    if count != SYSTEM_NAMES_ARCHIVE_COUNT:
        raise RicoBalanceError(f"system names archive has {count} entries")
    table_end = 4 + count * 4
    offsets = struct.unpack_from(f"<{count}I", decoded, 4)
    if (
        offsets[0] < table_end
        or any(left >= right for left, right in zip(offsets, offsets[1:]))
        or offsets[-1] >= len(decoded)
    ):
        raise RicoBalanceError("system names archive offsets are invalid")
    entries = [
        decoded[start : offsets[index + 1] if index + 1 < count else len(decoded)]
        for index, start in enumerate(offsets)
    ]
    start, end = EQUIPMENT_NAMES_SOURCE_RANGE
    if (
        offsets[EQUIPMENT_NAMES_ARCHIVE_ENTRY] != start
        or (
            offsets[EQUIPMENT_NAMES_ARCHIVE_ENTRY + 1]
            if EQUIPMENT_NAMES_ARCHIVE_ENTRY + 1 < count
            else len(decoded)
        )
        != end
        or hashlib.sha256(entries[EQUIPMENT_NAMES_ARCHIVE_ENTRY]).hexdigest()
        != EQUIPMENT_NAMES_SOURCE_SHA256
    ):
        raise RicoBalanceError("equipment-name table identity changed")

    names = entries[EQUIPMENT_NAMES_ARCHIVE_ENTRY]
    for item_id, name in YOUNG_RICO_EQUIPMENT_NAMES.items():
        encoded = bytes(PLAIN_ENCODE[character] for character in name) + b"\x00"
        names = _replace_indexed_string(
            names,
            entry_id=item_id,
            expected_text=b"\x01\x00",
            expected_dimensions=b"\x00\x02",
            replacement_text=encoded,
            replacement_dimensions=bytes((len(name) * 2, 1)),
        )
    entries[EQUIPMENT_NAMES_ARCHIVE_ENTRY] = names

    rebuilt = bytearray(decoded[: offsets[0]])
    rebuilt_offsets: list[int] = []
    for entry in entries:
        rebuilt_offsets.append(len(rebuilt))
        rebuilt.extend(entry)
    struct.pack_into(f"<{count}I", rebuilt, 4, *rebuilt_offsets)
    patched_decoded = bytes(rebuilt)
    patched_decoded_hash = hashlib.sha256(patched_decoded).hexdigest()
    if (
        len(patched_decoded) != SYSTEM_NAMES_DECODED_PATCHED_SIZE
        or patched_decoded_hash != SYSTEM_NAMES_DECODED_PATCHED_SHA256
    ):
        raise RicoBalanceError(
            "patched system-name archive mismatch: "
            f"{len(patched_decoded)}, {patched_decoded_hash}"
        )
    result = compress_lzss_exact_complete_groups(patched_decoded)
    result_hash = hashlib.sha256(result).hexdigest()
    if len(result) != SYSTEM_NAMES_PATCHED_SIZE or result_hash != SYSTEM_NAMES_PATCHED_SHA256:
        raise RicoBalanceError(
            f"packed system-name patch mismatch: {len(result)}, {result_hash}"
        )
    round_trip, round_trip_consumed = decode_lzss_complete_groups(result)
    if round_trip != patched_decoded or round_trip_consumed > len(result):
        raise RicoBalanceError("packed system-name patch failed retail round-trip")
    return result


def patch_memento_system_data(source: bytes) -> bytes:
    """Balance Memento and describe young Rico's zero-stat keepsakes."""

    actual_hash = hashlib.sha256(source).hexdigest()
    if len(source) != SYSTEM_DATA_SIZE or actual_hash != SYSTEM_DATA_RETAIL_SHA256:
        raise RicoBalanceError(
            f"system data mismatch: {len(source)} bytes, {actual_hash}"
        )
    entries, offsets = _archive_entries(source, expected_count=SYSTEM_DATA_ARCHIVE_COUNT)

    item_entry = entries[MEMENTO_ITEM_ARCHIVE_ENTRY]
    item_decoded, item_consumed = decode_lzss_complete_groups(item_entry + bytes(16))
    if item_consumed > len(item_entry) + 16 or len(item_decoded) != 3202:
        raise RicoBalanceError("Memento item-data stream failed validation")
    start = MEMENTO_ITEM_RECORD_OFFSET
    end = start + MEMENTO_ITEM_RECORD_SIZE
    if item_decoded[start:end] != MEMENTO_ITEM_RETAIL_RECORD:
        raise RicoBalanceError("Memento item record changed from retail")
    patched_item = bytearray(item_decoded)
    struct.pack_into("<H", patched_item, start + 0x0A, MEMENTO_ITEM_EFFECT_FLAGS)
    entries[MEMENTO_ITEM_ARCHIVE_ENTRY] = compress_lzss_exact_complete_groups(
        bytes(patched_item)
    )

    description_entry = entries[MEMENTO_DESCRIPTION_ARCHIVE_ENTRY]
    description_decoded, description_consumed = decode_lzss_complete_groups(
        source[offsets[MEMENTO_DESCRIPTION_ARCHIVE_ENTRY] :] + bytes(16)
    )
    if description_consumed > len(description_entry) + 16 or len(description_decoded) != 2188:
        raise RicoBalanceError("Memento description stream failed validation")
    encoded_description = bytes(
        PLAIN_ENCODE[character] for character in MEMENTO_DESCRIPTION
    ) + b"\x00"
    patched_description = _replace_indexed_string(
        description_decoded,
        entry_id=MEMENTO_ITEM_ID,
        expected_text=b"\x01\x00",
        expected_dimensions=b"\x00\x02",
        replacement_text=encoded_description,
        replacement_dimensions=MEMENTO_DESCRIPTION_DIMENSIONS,
    )
    for item_id, description in YOUNG_RICO_EQUIPMENT_DESCRIPTIONS.items():
        encoded = bytes(PLAIN_ENCODE[character] for character in description) + b"\x00"
        patched_description = _replace_indexed_string(
            patched_description,
            entry_id=item_id,
            expected_text=b"\x01\x00",
            expected_dimensions=b"\x00\x02",
            replacement_text=encoded,
            replacement_dimensions=bytes((len(description) * 2, 1)),
        )
    entries[MEMENTO_DESCRIPTION_ARCHIVE_ENTRY] = compress_lzss_exact_complete_groups(
        patched_description
    )

    result = _rebuild_archive(entries, header_size=offsets[0])
    patched_hash = hashlib.sha256(result).hexdigest()
    if SYSTEM_DATA_PATCHED_SIZE and (
        len(result) != SYSTEM_DATA_PATCHED_SIZE
        or patched_hash != SYSTEM_DATA_PATCHED_SHA256
    ):
        raise RicoBalanceError(
            f"patched system-data mismatch: {len(result)}, {patched_hash}"
        )
    return result


# ---------------------------------------------------------------------------
# Per-character weight-gain clamp and disabled Gear row in overlays 2597/2599/2603


TITLE_OVERLAY_SIZE: Final = 153_864
TITLE_OVERLAY_RETAIL_SHA256: Final = (
    "82f84a24ac1fd1979754e1cc9c861405fb59ce95dd78db00a76f00c8f1bd177d"
)
TITLE_OVERLAY_DISC2_GATE_SHA256: Final = (
    "546c59dbe8b43a7b3b8799d205ae14a0053137787132a64fa623d0739e078b15"
)
TITLE_OVERLAY_BALANCED_SHA256: Final = (
    "960e852c3830e7c721901aa4373448a8bfc49681fcf3e34b11feed69af56a484"
)
TITLE_OVERLAY_DISC2_BALANCED_SHA256: Final = (
    "a054649dc96943719562462c90474441ff9eeff7cae41b3a9eb9909bf9214701"
)

TITLE_OVERLAY_LOAD_BASE: Final = 0x801C5000
WEIGHT_GAIN_HOOK_OFFSET: Final = 0x1E4BC
WEIGHT_GAIN_HOOK_END: Final = 0x1E4C4
WEIGHT_GAIN_HOOK_RETAIL: Final = bytes.fromhex(
    "21 10 43 00 78 00 82 A0"  # addu v0,v0,v1; sb v0,0x78(a0)
)
# The positive-weight path immediately following the hook used to clamp every
# character to the retail global limit of 200.  Reuse that live instruction
# budget for the per-character comparison instead of putting the whole clamp
# routine in trailing overlay padding.
WEIGHT_GAIN_CAP_OFFSET: Final = 0x1E4C4
WEIGHT_GAIN_CAP_END: Final = 0x1E4E0
WEIGHT_GAIN_CAP_RETAIL: Final = bytes.fromhex(
    "78 00 82 90 00 00 00 00 C9 00 42 2C 0F 00 40 14 "
    "C8 00 02 34 44 8D 07 08 78 00 82 A0"
)
WEIGHT_CLAMP_CAVE_OFFSET: Final = 0x256D0
# Slot 1 proves that the menu allocator begins reusing the nominal zero tail at
# 0x256FC after an Items/Equip round trip.  The 44 bytes below that boundary
# remain byte-exact, so keep only the compact lookup helper and cap table here.
WEIGHT_CLAMP_CAVE_END: Final = 0x256FC
WEIGHT_CLAMP_HELPER_ADDRESS: Final = TITLE_OVERLAY_LOAD_BASE + WEIGHT_CLAMP_CAVE_OFFSET

GEAR_MENU_DRAW_HOOK_OFFSET: Final = 0x05BC
GEAR_MENU_DRAW_HOOK_END: Final = 0x05D0
GEAR_MENU_DRAW_HOOK_RETAIL: Final = bytes.fromhex(
    "FD 1E 07 0C 00 00 00 00 "  # jal 0x801C7BF4; nop
    "06 80 04 3C A0 25 84 8C 00 00 00 00"
)
# The retail input path rejects main-menu row 2 when m33B, the number of
# current party records with a Gear ID other than FF, is zero.
GEAR_MENU_SELECTION_GUARD_OFFSET: Final = 0x0614
GEAR_MENU_SELECTION_GUARD_END: Final = 0x0640
GEAR_MENU_SELECTION_GUARD: Final = bytes.fromhex(
    "36 03 83 90 02 00 02 34 08 00 62 14 01 00 10 34 "
    "3B 03 82 90 00 00 00 00 05 00 40 14 FF 00 02 32 "
    "21 80 00 00 5D 21 07 0C 04 00 04 34"
)
GEAR_MENU_GRAY_HELPER_OFFSET: Final = 0x254B8
GEAR_MENU_GRAY_HELPER_END: Final = 0x254DC
GEAR_MENU_GRAY_HELPER_ADDRESS: Final = (
    TITLE_OVERLAY_LOAD_BASE + GEAR_MENU_GRAY_HELPER_OFFSET
)
GEAR_MENU_DRAW_ADDRESS: Final = 0x801C7BF4
GEAR_MENU_DISABLED_COLOR_WORD: Final = 0x2C404040
# Gear is pair 2 in the foreground array.  Its two display buffers must match;
# the native dark backing glyph remains unchanged.
GEAR_MENU_COLOR_OFFSETS: Final = (0x00A4, 0x00CC)


def _reg(value: str | int) -> int:
    registers = {
        "zero": 0,
        "v0": 2,
        "v1": 3,
        "a0": 4,
        "t0": 8,
        "s0": 16,
        "ra": 31,
    }
    return registers[value] if isinstance(value, str) else value


def _i(opcode: int, rs: str | int, rt: str | int, immediate: int) -> int:
    return (opcode << 26) | (_reg(rs) << 21) | (_reg(rt) << 16) | (immediate & 0xFFFF)


def _r(rs: str | int, rt: str | int, rd: str | int, function: int) -> int:
    return (_reg(rs) << 21) | (_reg(rt) << 16) | (_reg(rd) << 11) | function


def _j(opcode: int, address: int) -> int:
    return (opcode << 26) | ((address >> 2) & 0x03FFFFFF)


def _lbu(rt: str | int, immediate: int, rs: str | int) -> int:
    return _i(0x24, rs, rt, immediate)


def _lw(rt: str | int, immediate: int, rs: str | int) -> int:
    return _i(0x23, rs, rt, immediate)


def _sb(rt: str | int, immediate: int, rs: str | int) -> int:
    return _i(0x28, rs, rt, immediate)


def _sw(rt: str | int, immediate: int, rs: str | int) -> int:
    return _i(0x2B, rs, rt, immediate)


def _sltiu(rt: str | int, rs: str | int, immediate: int) -> int:
    return _i(0x0B, rs, rt, immediate)


def _beq(rs: str | int, rt: str | int, relative_words: int) -> int:
    return _i(0x04, rs, rt, relative_words)


def _bne(rs: str | int, rt: str | int, relative_words: int) -> int:
    return _i(0x05, rs, rt, relative_words)


def _lui(rt: str | int, immediate: int) -> int:
    return _i(0x0F, "zero", rt, immediate)


def _ori(rt: str | int, rs: str | int, immediate: int) -> int:
    return _i(0x0D, rs, rt, immediate)


def _addiu(rt: str | int, rs: str | int, immediate: int) -> int:
    return _i(0x09, rs, rt, immediate)


def _addu(rd: str | int, rs: str | int, rt: str | int) -> int:
    return _r(rs, rt, rd, 0x21)


def _sltu(rd: str | int, rs: str | int, rt: str | int) -> int:
    return _r(rs, rt, rd, 0x2B)


def _jr(rs: str | int) -> int:
    return (_reg(rs) << 21) | 0x08


WEIGHT_CAP_TABLE_ADDRESS: Final = WEIGHT_CLAMP_HELPER_ADDRESS + 8 * 4
_weight_table_high = (WEIGHT_CAP_TABLE_ADDRESS + 0x8000) >> 16
_weight_table_low = WEIGHT_CAP_TABLE_ADDRESS & 0xFFFF
WEIGHT_CLAMP_HELPER_WORDS: Final = (
    _lbu("v1", CHARACTER_ID_OFFSET, "a0"),
    _lui("t0", _weight_table_high),
    _addiu("t0", "t0", _weight_table_low),
    _addu("t0", "t0", "v1"),
    _lbu("t0", 0, "t0"),
    0,
    _jr("ra"),
    0,
)
WEIGHT_CLAMP_HELPER: Final = struct.pack(
    f"<{len(WEIGHT_CLAMP_HELPER_WORDS)}I", *WEIGHT_CLAMP_HELPER_WORDS
) + MUTABLE_WEIGHT_CAPS
WEIGHT_GAIN_HOOK_PATCHED: Final = struct.pack(
    "<2I",
    _j(0x03, WEIGHT_CLAMP_HELPER_ADDRESS),
    _addu("v0", "v0", "v1"),
)
WEIGHT_GAIN_CAP_PATCHED_WORDS: Final = (
    _sltu("v1", "t0", "v0"),
    _beq("v1", "zero", 17),
    _sb("v0", WEIGHT_MUTABLE_OFFSET, "a0"),
    _addu("v0", "t0", "zero"),
    _j(0x02, TITLE_OVERLAY_LOAD_BASE + 0x1E510),
    _sb("v0", WEIGHT_MUTABLE_OFFSET, "a0"),
    0,
)
WEIGHT_GAIN_CAP_PATCHED: Final = struct.pack(
    f"<{len(WEIGHT_GAIN_CAP_PATCHED_WORDS)}I",
    *WEIGHT_GAIN_CAP_PATCHED_WORDS,
)

GEAR_MENU_GRAY_HELPER_WORDS: Final = (
    _lbu("v1", 0x033B, "a0"),
    _lw("v0", 0x0350, "a0"),
    _bne("v1", "zero", 4),
    _lui("v1", GEAR_MENU_DISABLED_COLOR_WORD >> 16),
    _ori("v1", "v1", GEAR_MENU_DISABLED_COLOR_WORD),
    *(_sw("v1", offset, "v0") for offset in GEAR_MENU_COLOR_OFFSETS),
    _j(0x02, GEAR_MENU_DRAW_ADDRESS),
    0,
)
GEAR_MENU_GRAY_HELPER: Final = struct.pack(
    f"<{len(GEAR_MENU_GRAY_HELPER_WORDS)}I", *GEAR_MENU_GRAY_HELPER_WORDS
)
GEAR_MENU_DRAW_HOOK_PATCHED: Final = struct.pack(
    "<5I",
    _lui("s0", 0x8006),
    _lw("s0", 0x25A0, "s0"),
    _j(0x03, GEAR_MENU_GRAY_HELPER_ADDRESS),
    _addu("a0", "s0", "zero"),
    _addu("a0", "s0", "zero"),
)


def patch_weight_mutation_overlay(source: bytes) -> bytes:
    """Install per-character weight caps and gray the unusable Gear row."""

    actual_hash = hashlib.sha256(source).hexdigest()
    accepted = {
        value
        for value in (TITLE_OVERLAY_RETAIL_SHA256, TITLE_OVERLAY_DISC2_GATE_SHA256)
        if value
    }
    if len(source) != TITLE_OVERLAY_SIZE or actual_hash not in accepted:
        raise RicoBalanceError(
            f"title/kernel overlay mismatch: {len(source)} bytes, {actual_hash}"
        )
    if source[WEIGHT_GAIN_HOOK_OFFSET:WEIGHT_GAIN_HOOK_END] != WEIGHT_GAIN_HOOK_RETAIL:
        raise RicoBalanceError("weight-gain hook context changed")
    if source[WEIGHT_GAIN_CAP_OFFSET:WEIGHT_GAIN_CAP_END] != WEIGHT_GAIN_CAP_RETAIL:
        raise RicoBalanceError("weight-gain cap context changed")
    if (
        source[GEAR_MENU_DRAW_HOOK_OFFSET:GEAR_MENU_DRAW_HOOK_END]
        != GEAR_MENU_DRAW_HOOK_RETAIL
    ):
        raise RicoBalanceError("Gear-menu draw hook context changed")
    if (
        source[GEAR_MENU_SELECTION_GUARD_OFFSET:GEAR_MENU_SELECTION_GUARD_END]
        != GEAR_MENU_SELECTION_GUARD
    ):
        raise RicoBalanceError("native Gear-menu selection guard changed")
    weight_cave = source[WEIGHT_CLAMP_CAVE_OFFSET:WEIGHT_CLAMP_CAVE_END]
    if weight_cave != bytes(len(weight_cave)):
        raise RicoBalanceError("stable weight-helper cave is occupied")
    gear_cave = source[GEAR_MENU_GRAY_HELPER_OFFSET:GEAR_MENU_GRAY_HELPER_END]
    if gear_cave != bytes(len(gear_cave)):
        raise RicoBalanceError("stable Gear-gray helper cave is occupied")
    if (
        WEIGHT_CLAMP_CAVE_OFFSET + len(WEIGHT_CLAMP_HELPER)
        > WEIGHT_CLAMP_CAVE_END
        or GEAR_MENU_GRAY_HELPER_OFFSET + len(GEAR_MENU_GRAY_HELPER)
        > GEAR_MENU_GRAY_HELPER_END
    ):
        raise RicoBalanceError("title-overlay helpers exceed their stable caves")

    result = bytearray(source)
    result[WEIGHT_GAIN_HOOK_OFFSET:WEIGHT_GAIN_HOOK_END] = WEIGHT_GAIN_HOOK_PATCHED
    result[WEIGHT_GAIN_CAP_OFFSET:WEIGHT_GAIN_CAP_END] = WEIGHT_GAIN_CAP_PATCHED
    result[
        WEIGHT_CLAMP_CAVE_OFFSET:
        WEIGHT_CLAMP_CAVE_OFFSET + len(WEIGHT_CLAMP_HELPER)
    ] = WEIGHT_CLAMP_HELPER
    result[GEAR_MENU_DRAW_HOOK_OFFSET:GEAR_MENU_DRAW_HOOK_END] = (
        GEAR_MENU_DRAW_HOOK_PATCHED
    )
    result[
        GEAR_MENU_GRAY_HELPER_OFFSET:
        GEAR_MENU_GRAY_HELPER_OFFSET + len(GEAR_MENU_GRAY_HELPER)
    ] = GEAR_MENU_GRAY_HELPER
    patched = bytes(result)
    patched_hash = hashlib.sha256(patched).hexdigest()
    expected = (
        TITLE_OVERLAY_BALANCED_SHA256
        if actual_hash == TITLE_OVERLAY_RETAIL_SHA256
        else TITLE_OVERLAY_DISC2_BALANCED_SHA256
    )
    if expected and patched_hash != expected:
        raise RicoBalanceError(
            f"patched title/kernel overlay hash mismatch: {patched_hash}"
        )
    return patched
