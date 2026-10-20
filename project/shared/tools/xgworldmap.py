#!/usr/bin/env python3
"""Inspect and patch Xenogears' compressed world-map location data.

The world-map data file is one LZSS stream.  Its decompressed root contains
relative tables for initial positions, location rectangles, destination field
IDs, and location-name dialogue.  This module deliberately edits only a
uniquely audited entry and validates the result after recompression.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
import sys
from typing import Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.tools.xgdialog import decode_text
from shared.tools.xgfield import compress_lzss, decompress_lzss


class WorldmapFormatError(RuntimeError):
    """Raised when world-map data does not match the audited layout."""


@dataclass(frozen=True)
class InitialPosition:
    offset: int
    x: int
    index: int
    z: int
    reserved: int


@dataclass(frozen=True)
class WorldmapExit:
    group: int
    offset: int
    x: int
    z: int
    width: int
    height: int
    destination_field: int
    destination_parameter: int
    label_id: int
    exit_type: int


@dataclass(frozen=True)
class WorldmapModel:
    record: int
    offset: int
    block_id: int
    flags: int
    x: int
    y: int
    raw_z: int
    rotation_x: int
    rotation_y: int
    rotation_z: int


@dataclass(frozen=True)
class PatchedWorldmap:
    packed: bytes
    decoded: bytes
    spawn: InitialPosition
    new_exit: WorldmapExit
    taura_exit: WorldmapExit
    taura_model: WorldmapModel
    mass_driver_models: tuple[WorldmapModel, ...]
    label: str


@dataclass(frozen=True)
class PatchedWorldmapControls:
    packed: bytes
    decoded: bytes
    instruction_offset: int
    old_mask: int
    new_mask: int
    encounter_instruction_offset: int | None
    old_encounter_slots: int | None
    new_encounter_slots: int | None
    formation_instruction_offset: int | None
    forced_formation_slot: int | None


@dataclass(frozen=True)
class _LzssGroup:
    packed_start: int
    packed_end: int
    decoded_start: int
    decoded_end: int


def _u16(data: bytes | bytearray, offset: int, *, signed: bool = False) -> int:
    if offset < 0 or offset + 2 > len(data):
        raise WorldmapFormatError(f"u16 read outside world map at 0x{offset:X}")
    return int.from_bytes(data[offset : offset + 2], "little", signed=signed)


def _u32(data: bytes | bytearray, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise WorldmapFormatError(f"u32 read outside world map at 0x{offset:X}")
    return int.from_bytes(data[offset : offset + 4], "little")


def decompress_worldmap(packed: bytes) -> bytes:
    """Decode a world-map file, tolerating retail's partial final group."""

    if len(packed) < 5:
        raise WorldmapFormatError("Compressed world map is too short")
    required = _u32(packed, 0)
    if required < 0x80:
        raise WorldmapFormatError(
            f"Implausible decompressed world-map size: {required}"
        )
    # Several retail files end in a partial command group.  The original game
    # reads harmless allocation padding.  Supplying zero padding makes that
    # behavior deterministic without changing any meaningful decoded byte.
    try:
        return decompress_lzss(packed + bytes(32), required).data
    except Exception as exc:  # normalized for callers of this format module
        raise WorldmapFormatError(f"Cannot decompress world map: {exc}") from exc


def _retail_safe_lzss_edit(
    packed: bytes, original: bytes, edited: bytes
) -> bytes:
    """Keep retail LZSS commands except for small literal-only edit islands.

    The compact project encoder round-trips through the inspection decoder,
    but the PS1 world-map loader is stricter about streams produced by its
    original encoder.  Recompressing all of file 4052 therefore crashes the
    retail loader.  This routine preserves the retail stream and replaces only
    complete command-group ranges around changed decoded bytes.  Each island
    emits full groups of eight literals, after which the untouched retail
    backreferences remain valid because the decoded history is identical.

    A changed literal can feed a later retail backreference.  The iterative
    pass detects those secondary differences and literalizes their groups too.
    """

    if len(original) != len(edited):
        raise WorldmapFormatError("Retail-safe LZSS edits must preserve decoded size")
    if decompress_worldmap(packed) != original:
        raise WorldmapFormatError("Retail-safe LZSS source does not match decoded data")
    if original == edited:
        return packed

    groups: list[_LzssGroup] = []
    packed_offset = 4
    decoded_offset = 0
    while decoded_offset < len(original):
        packed_start = packed_offset
        decoded_start = decoded_offset
        if packed_offset >= len(packed):
            raise WorldmapFormatError("Retail LZSS stream ends before a control group")
        control = packed[packed_offset]
        packed_offset += 1
        for bit in range(8):
            if decoded_offset >= len(original):
                break
            if control & (1 << bit):
                if packed_offset + 2 > len(packed):
                    raise WorldmapFormatError(
                        "Retail LZSS stream ends inside a backreference"
                    )
                high = packed[packed_offset + 1]
                packed_offset += 2
                decoded_offset += (high >> 4) + 3
            else:
                if packed_offset >= len(packed):
                    raise WorldmapFormatError(
                        "Retail LZSS stream ends before a literal"
                    )
                packed_offset += 1
                decoded_offset += 1
        groups.append(
            _LzssGroup(
                packed_start,
                packed_offset,
                decoded_start,
                min(decoded_offset, len(original)),
            )
        )

    def group_range(decoded_byte: int) -> tuple[int, int]:
        try:
            start = next(
                index
                for index, group in enumerate(groups)
                if group.decoded_start <= decoded_byte < group.decoded_end
            )
        except StopIteration as exc:
            raise WorldmapFormatError(
                f"Changed world-map byte 0x{decoded_byte:X} has no LZSS group"
            ) from exc
        end = start + 1
        while (
            groups[end - 1].decoded_end - groups[start].decoded_start
        ) % 8:
            if end >= len(groups):
                raise WorldmapFormatError(
                    "Cannot align a retail-safe LZSS literal island"
                )
            end += 1
        return start, end

    ranges = [
        group_range(index)
        for index, (before, after) in enumerate(zip(original, edited, strict=True))
        if before != after
    ]

    def merged_aligned_ranges(
        source_ranges: Sequence[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        """Merge islands and realign their union to eight decoded bytes.

        Two individually aligned decoded spans can overlap while using
        different alignment origins.  Their merged union is then not
        necessarily divisible by eight.  Re-extending and re-merging to a
        fixed point keeps every emitted literal island command-group aligned.
        """

        current = list(source_ranges)
        for _ in range(len(groups) + 1):
            merged: list[tuple[int, int]] = []
            for start, end in sorted(current):
                if merged and start <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                else:
                    merged.append((start, end))

            aligned: list[tuple[int, int]] = []
            for start, end in merged:
                while (groups[end - 1].decoded_end - groups[start].decoded_start) % 8:
                    if end >= len(groups):
                        raise WorldmapFormatError(
                            "Cannot align a merged retail-safe LZSS island"
                        )
                    end += 1
                aligned.append((start, end))
            if aligned == merged:
                return aligned
            current = aligned
        raise WorldmapFormatError("Retail-safe LZSS island alignment did not converge")

    for _ in range(len(groups) + 1):
        merged = merged_aligned_ranges(ranges)

        result = bytearray(packed)
        for start, end in reversed(merged):
            first = groups[start]
            last = groups[end - 1]
            chunk = edited[first.decoded_start : last.decoded_end]
            if len(chunk) % 8:
                raise WorldmapFormatError("Literal island is not command-group aligned")
            encoded = bytearray()
            for offset in range(0, len(chunk), 8):
                encoded.append(0)
                encoded.extend(chunk[offset : offset + 8])
            result[first.packed_start : last.packed_end] = encoded

        candidate = bytes(result)
        decoded = decompress_worldmap(candidate)
        mismatches = [
            index
            for index, (expected, actual) in enumerate(
                zip(edited, decoded, strict=True)
            )
            if expected != actual
        ]
        if not mismatches:
            return candidate
        ranges.extend(group_range(index) for index in mismatches)

    raise WorldmapFormatError("Retail-safe LZSS edit did not converge")


class WorldmapData:
    """Strict parser for the initial-position, exit, and label tables."""

    def __init__(self, decoded: bytes | bytearray | memoryview):
        self.data = bytes(decoded)
        if len(self.data) < 0x30:
            raise WorldmapFormatError("Decoded world map is shorter than its root")

        self.data_root = _u32(self.data, 0x04)
        if self.data_root < 0x30 or self.data_root + 8 > len(self.data):
            raise WorldmapFormatError(
                f"World-map data root is invalid: 0x{self.data_root:X}"
            )
        self.initial_positions_offset = self.data_root + _u32(
            self.data, self.data_root
        )
        self.exit_directory_offset = self.data_root + _u32(
            self.data, self.data_root + 4
        )
        self.dialogue_offset = _u32(self.data, 0x1C)
        self.dialogue_end = _u32(self.data, 0x20)

        for label, offset in (
            ("initial-position table", self.initial_positions_offset),
            ("exit directory", self.exit_directory_offset),
            ("dialogue table", self.dialogue_offset),
            ("dialogue end", self.dialogue_end),
        ):
            if offset < 0 or offset > len(self.data):
                raise WorldmapFormatError(f"{label} is outside the world map")
        if self.dialogue_end <= self.dialogue_offset:
            raise WorldmapFormatError("World-map dialogue span is empty or reversed")

        first_group_relative = _u32(self.data, self.exit_directory_offset)
        directory_relative = self.exit_directory_offset - self.data_root
        delta = first_group_relative - directory_relative
        if delta <= 0 or delta % 4:
            raise WorldmapFormatError("World-map exit group directory is malformed")
        self.exit_group_count = delta // 4
        if self.exit_group_count != 4:
            raise WorldmapFormatError(
                f"Expected four world-map exit groups, got {self.exit_group_count}"
            )

    def initial_positions(self) -> tuple[InitialPosition, ...]:
        values: list[InitialPosition] = []
        offset = self.initial_positions_offset
        for _ in range(256):
            value = InitialPosition(
                offset=offset,
                x=_u16(self.data, offset, signed=True),
                index=_u16(self.data, offset + 2, signed=True),
                z=_u16(self.data, offset + 4, signed=True),
                reserved=_u16(self.data, offset + 6, signed=True),
            )
            if value.index == -1:
                return tuple(values)
            values.append(value)
            offset += 8
        raise WorldmapFormatError("Initial-position table has no terminator")

    def exits(self, group: int) -> tuple[WorldmapExit, ...]:
        if not 0 <= group < self.exit_group_count:
            raise WorldmapFormatError(f"Exit group is outside 0..3: {group}")
        relative = _u32(self.data, self.exit_directory_offset + group * 4)
        offset = self.data_root + relative
        values: list[WorldmapExit] = []
        for _ in range(256):
            value = WorldmapExit(
                group=group,
                offset=offset,
                x=_u16(self.data, offset, signed=True),
                z=_u16(self.data, offset + 2, signed=True),
                width=_u16(self.data, offset + 4, signed=True),
                height=_u16(self.data, offset + 6, signed=True),
                destination_field=_u16(self.data, offset + 8, signed=True),
                destination_parameter=_u16(self.data, offset + 10, signed=True),
                label_id=_u16(self.data, offset + 12, signed=True),
                exit_type=_u16(self.data, offset + 14, signed=True),
            )
            if value.destination_field == -1:
                return tuple(values)
            values.append(value)
            offset += 0x10
        raise WorldmapFormatError(f"Exit group {group} has no terminator")

    def label(self, block_id: int) -> str:
        component = self.data[self.dialogue_offset : self.dialogue_end]
        if len(component) < 8:
            raise WorldmapFormatError("World-map dialogue table is too short")
        block_count = _u32(component, 0) + 1
        if not 0 <= block_id < block_count:
            raise WorldmapFormatError(
                f"Dialogue block {block_id} is outside 0..{block_count - 1}"
            )
        offsets = [_u16(component, 4 + index * 2) for index in range(block_count)]
        start = offsets[block_id]
        # Retail world maps legally alias two label IDs to one payload.  Find
        # the next strictly greater offset instead of rejecting duplicates.
        end = next((value for value in offsets[block_id + 1 :] if value > start), len(component))
        if start >= end or end > len(component):
            raise WorldmapFormatError(f"Dialogue block {block_id} has an invalid span")
        try:
            return decode_text(component[start:end])
        except Exception as exc:
            raise WorldmapFormatError(
                f"Cannot decode world-map label {block_id}: {exc}"
            ) from exc

    def model(self, record: int) -> WorldmapModel:
        config = _u32(self.data, 0x10)
        if config <= 0 or config + 2 > len(self.data):
            raise WorldmapFormatError("World-map model configuration is invalid")
        count = _u16(self.data, config)
        if not 0 <= record < count:
            raise WorldmapFormatError(
                f"World-map model record {record} is outside 0..{count - 1}"
            )
        offset = config + 2 + record * 0x10
        if offset + 0x10 > len(self.data):
            raise WorldmapFormatError("World-map model record is truncated")
        values = struct.unpack_from("<HHhhhHHH", self.data, offset)
        return WorldmapModel(record, offset, *values)


def patch_mass_driver_entry(
    packed: bytes,
    *,
    spawn_index: int = 21,
    spawn_x: int = 30192,
    spawn_z: int = 16396,
    entry_x: int = 29880,
    entry_z: int = 16287,
    entry_width: int = 288,
    entry_height: int = 214,
    new_destination: int = 720,
    new_label: int = 21,
    encounter_enemy_offset: int | None = None,
    old_encounter_enemy: int = 0x80,
    new_encounter_enemy: int = 0x81,
) -> PatchedWorldmap:
    """Create a usable entrance for the retail Mass Driver complex.

    Retail 4052 already contains the English ``Mass Driver`` label and the
    complete four-model Mass Driver complex, but its final playable exit table
    omits an active trigger and spawn.  Later retail bundles preserve position
    index 21, the ``Mass Driver`` label, and a disabled rectangle around
    endpoint block 48.  That rectangle ends in the non-traversable half of a
    mixed terrain cell, so this patch extends its east edge into the
    traversable half to form an explicit exterior interaction apron.  The
    apron links directly to the standalone field, and position 21 is placed
    just outside it on the same walkable strip.

    The decoded file has no spare bytes between its tables.  Groups 0 and 1
    are byte-for-byte duplicate on-foot/Gear exit lists, so both are pointed at
    one shared list.  The released group-0 terminator becomes the Mass Driver
    record, the first now-unused group-1 record becomes its terminator, and the
    remaining unused group-1 storage holds a relocated copy of every retail
    initial position plus position 21.  No table grows and no retail location
    is removed.  When requested, the separately audited Mass Driver formation
    selector at decoded offset 0x30F60 is changed under an exact 32-byte
    context check.
    """

    decoded = decompress_worldmap(packed)
    parsed = WorldmapData(decoded)

    signed_values = (spawn_x, spawn_z, entry_x, entry_z, entry_width, entry_height)
    if any(not -0x8000 <= value <= 0x7FFF for value in signed_values):
        raise WorldmapFormatError("Mass Driver coordinates must fit signed 16 bits")
    if entry_width <= 0 or entry_height <= 0:
        raise WorldmapFormatError("Mass Driver entry dimensions must be positive")

    def exit_payload(value: WorldmapExit) -> tuple[int, ...]:
        return (
            value.x,
            value.z,
            value.width,
            value.height,
            value.destination_field,
            value.destination_parameter,
            value.label_id,
            value.exit_type,
        )

    positions = parsed.initial_positions()
    if any(value.index == spawn_index for value in positions):
        raise WorldmapFormatError(
            f"World-map initial position {spawn_index} unexpectedly already exists"
        )
    reserved = [value for value in positions if value.index == 0x0FFF]
    if len(reserved) != 1 or reserved[0] != InitialPosition(
        reserved[0].offset if reserved else 0,
        30352,
        0x0FFF,
        10852,
        0,
    ):
        raise WorldmapFormatError("Audited reserved world-map position changed")

    group0 = parsed.exits(0)
    group1 = parsed.exits(1)
    group2 = parsed.exits(2)
    group3 = parsed.exits(3)
    if tuple(map(exit_payload, group0)) != tuple(map(exit_payload, group1)):
        raise WorldmapFormatError("Retail on-foot and Gear exit tables are not duplicates")
    if any(
        value.label_id == new_label
        for group in (group0, group1, group2, group3)
        for value in group
    ):
        raise WorldmapFormatError("Mass Driver exit unexpectedly already exists")

    taura_candidates = [
        value
        for value in group0
        if exit_payload(value)
        == (27990, 23381, 340, 376, 614, 0, 20, 0)
    ]
    if len(taura_candidates) != 1:
        raise WorldmapFormatError(
            f"Expected one untouched Taura exit, found {len(taura_candidates)}"
        )
    taura_exit = taura_candidates[0]

    label = parsed.label(new_label)
    if label != "Mass Driver<Close>":
        raise WorldmapFormatError(
            f"World-map label {new_label} is {label!r}, expected 'Mass Driver<Close>'"
        )

    taura_model = parsed.model(51)
    expected_taura = WorldmapModel(
        51,
        taura_model.offset,
        41,
        0,
        28175,
        -166,
        -23606,
        0,
        0,
        0,
    )
    if taura_model != expected_taura:
        raise WorldmapFormatError(
            f"Audited Taura landmark changed: {taura_model}"
        )

    expected_mass_driver = (
        (59, 48, 0, 29991, -344, -16384, 0, 0, 0),
        (60, 49, 0, 28751, -224, -16549, 0, 0, 0),
        (61, 50, 0, 28580, -225, -17425, 0, 0, 0),
        (62, 51, 0, 29283, -222, -17286, 0, 0, 0),
    )
    mass_driver_models = tuple(parsed.model(record) for record in range(59, 63))
    for actual, expected in zip(mass_driver_models, expected_mass_driver, strict=True):
        if (
            actual.record,
            actual.block_id,
            actual.flags,
            actual.x,
            actual.y,
            actual.raw_z,
            actual.rotation_x,
            actual.rotation_y,
            actual.rotation_z,
        ) != expected:
            raise WorldmapFormatError(
                f"Audited Mass Driver model record {actual.record} changed: {actual}"
            )

    group_starts = [
        parsed.data_root
        + _u32(decoded, parsed.exit_directory_offset + group * 4)
        for group in range(parsed.exit_group_count)
    ]
    group0_terminator = group0[-1].offset + 0x10 if group0 else group_starts[0]
    group1_terminator = group1[-1].offset + 0x10 if group1 else group_starts[1]
    exact_terminator = struct.pack("<hhhhhhhh", 0, 0, 0, 0, -1, 0, 0, 0)
    if decoded[group0_terminator : group0_terminator + 0x10] != exact_terminator:
        raise WorldmapFormatError("Retail on-foot exit terminator changed")
    if decoded[group1_terminator : group1_terminator + 0x10] != exact_terminator:
        raise WorldmapFormatError("Retail Gear exit terminator changed")
    if group1 and group1[0].offset != group0_terminator + 0x10:
        raise WorldmapFormatError("Retail duplicate exit tables are not contiguous")

    relocated_positions = group_starts[1] + 0x10
    relocated_end = relocated_positions + (len(positions) + 2) * 8
    if relocated_end > group_starts[2]:
        raise WorldmapFormatError("Unused duplicate exit storage cannot hold positions")

    mutable = bytearray(decoded)
    if encounter_enemy_offset is not None:
        if encounter_enemy_offset != 0x30F60:
            raise WorldmapFormatError(
                "Mass Driver encounter enemy selector must use the audited "
                "decoded offset 0x30F60"
            )
        if not 0 <= old_encounter_enemy <= 0xFF:
            raise WorldmapFormatError(
                "Old world-map encounter enemy selector must fit one byte"
            )
        if not 0 <= new_encounter_enemy <= 0xFF:
            raise WorldmapFormatError(
                "New world-map encounter enemy selector must fit one byte"
            )
        if not 0 <= encounter_enemy_offset < len(decoded):
            raise WorldmapFormatError(
                "World-map encounter enemy selector is outside the bundle"
            )
        expected_formation = bytes.fromhex(
            "47 00 2C 00 00 00 00 00 "
            "80 FF FF FF FF FF FF FF "
            "00 FF FF FF FF FF FF FF "
            "00 FF FF FF FF FF FF FF"
        )
        formation_start = encounter_enemy_offset - 8
        if decoded[
            formation_start : formation_start + len(expected_formation)
        ] != expected_formation:
            raise WorldmapFormatError(
                "Mass Driver encounter formation context changed"
            )
        if decoded[encounter_enemy_offset] != old_encounter_enemy:
            raise WorldmapFormatError(
                "World-map encounter enemy selector is not "
                f"0x{old_encounter_enemy:02X}"
            )
        mutable[encounter_enemy_offset] = new_encounter_enemy
    mass_driver_record = struct.pack(
        "<hhhhhhhh",
        entry_x,
        entry_z,
        entry_width,
        entry_height,
        new_destination,
        0,
        new_label,
        0,
    )
    mutable[group0_terminator : group0_terminator + 0x10] = mass_driver_record
    mutable[group_starts[1] : group_starts[1] + 0x10] = exact_terminator
    group0_relative = group_starts[0] - parsed.data_root
    struct.pack_into("<I", mutable, parsed.exit_directory_offset + 4, group0_relative)

    original_positions = decoded[
        parsed.initial_positions_offset : parsed.initial_positions_offset
        + len(positions) * 8
    ]
    new_position = struct.pack("<hhhh", spawn_x, spawn_index, spawn_z, 0)
    position_terminator = struct.pack("<hhhh", 0, -1, 0, 0)
    relocated = original_positions + new_position + position_terminator
    mutable[relocated_positions : relocated_positions + len(relocated)] = relocated
    struct.pack_into(
        "<I", mutable, parsed.data_root, relocated_positions - parsed.data_root
    )

    edited = bytes(mutable)
    checked = WorldmapData(edited)
    checked_group0 = checked.exits(0)
    checked_group1 = checked.exits(1)
    expected_new_payload = (
        entry_x,
        entry_z,
        entry_width,
        entry_height,
        new_destination,
        0,
        new_label,
        0,
    )
    if tuple(map(exit_payload, checked_group0[:-1])) != tuple(map(exit_payload, group0)):
        raise WorldmapFormatError("A retail on-foot exit changed during insertion")
    if exit_payload(checked_group0[-1]) != expected_new_payload:
        raise WorldmapFormatError("Mass Driver exit did not survive the checked edit")
    if tuple(map(exit_payload, checked_group1)) != tuple(map(exit_payload, checked_group0)):
        raise WorldmapFormatError("On-foot and Gear modes do not share the new exits")
    if tuple(map(exit_payload, checked.exits(2))) != tuple(map(exit_payload, group2)):
        raise WorldmapFormatError("Yggdrasil exits changed during insertion")
    if tuple(map(exit_payload, checked.exits(3))) != tuple(map(exit_payload, group3)):
        raise WorldmapFormatError("Reserved exits changed during insertion")

    checked_positions = checked.initial_positions()
    if tuple(
        (value.x, value.index, value.z, value.reserved)
        for value in checked_positions[:-1]
    ) != tuple(
        (value.x, value.index, value.z, value.reserved) for value in positions
    ):
        raise WorldmapFormatError("A retail initial position changed during relocation")
    spawn = checked_positions[-1]
    if (spawn.x, spawn.index, spawn.z, spawn.reserved) != (
        spawn_x,
        spawn_index,
        spawn_z,
        0,
    ):
        raise WorldmapFormatError("Mass Driver spawn did not survive the checked edit")
    new_exit = checked_group0[-1]
    east_edge = new_exit.x + new_exit.width
    east_gap = spawn.x - east_edge
    if not (
        new_exit.z <= spawn.z <= new_exit.z + new_exit.height
        and 0 < east_gap <= 128
    ):
        raise WorldmapFormatError(
            "Mass Driver spawn is not just east of its exterior entry apron"
        )

    if checked.model(51) != taura_model:
        raise WorldmapFormatError("Taura's house model changed during insertion")
    if tuple(checked.model(record) for record in range(59, 63)) != mass_driver_models:
        raise WorldmapFormatError("Mass Driver models changed during insertion")
    checked_taura = [
        value
        for value in checked_group0
        if exit_payload(value) == exit_payload(taura_exit)
    ]
    if len(checked_taura) != 1:
        raise WorldmapFormatError("Taura's house exit changed during insertion")

    repacked = _retail_safe_lzss_edit(packed, decoded, edited)
    roundtrip = decompress_worldmap(repacked)
    if roundtrip != edited:
        raise WorldmapFormatError("Repacked world-map data failed its round trip")
    return PatchedWorldmap(
        packed=repacked,
        decoded=edited,
        spawn=spawn,
        new_exit=new_exit,
        taura_exit=checked_taura[0],
        taura_model=taura_model,
        mass_driver_models=mass_driver_models,
        label=label,
    )


def _patch_worldmap_controls(
    packed: bytes,
    *,
    instruction_offset: int = 0x210A4,
    old_mask: int = 0x20,
    new_mask: int = 0x20,
    encounter_instruction_offset: int | None = None,
    old_encounter_slots: int = 0,
    new_encounter_slots: int = 1,
    formation_instruction_offset: int | None = None,
) -> PatchedWorldmapControls:
    decoded = decompress_worldmap(packed)
    if not 0 <= old_mask <= 0xFFFF or not 0 <= new_mask <= 0xFFFF:
        raise WorldmapFormatError("World-map interaction masks must fit 16 bits")
    old_instruction = struct.pack("<I", 0x30420000 | old_mask)
    new_instruction = struct.pack("<I", 0x30420000 | new_mask)
    context_start = instruction_offset - 0x10
    context_end = instruction_offset + 0x10
    if context_start < 0 or context_end > len(decoded):
        raise WorldmapFormatError("World-map interaction instruction is outside overlay")
    expected_context = bytes.fromhex(
        "40 00 02 AE 0A 80 02 3C 10 BD 42 94 00 00 00 00 "
        "20 00 42 30 0D 00 40 10 FF FF 02 24 0A 80 02 3C"
    )
    if instruction_offset == 0x210A4 and decoded[context_start:context_end] != expected_context:
        raise WorldmapFormatError("On-foot world-map interaction context changed")
    if decoded[instruction_offset : instruction_offset + 4] != old_instruction:
        raise WorldmapFormatError(
            f"World-map interaction instruction is not andi v0,v0,0x{old_mask:02X}"
        )

    edited = bytearray(decoded)
    edited[instruction_offset : instruction_offset + 4] = new_instruction
    if encounter_instruction_offset is not None:
        if not 0 <= old_encounter_slots <= 16:
            raise WorldmapFormatError(
                "Old world-map encounter slot count must be between 0 and 16"
            )
        if not 0 <= new_encounter_slots <= 16:
            raise WorldmapFormatError(
                "New world-map encounter slot count must be between 0 and 16"
            )
        old_encounter_instruction = struct.pack(
            "<I", 0x24020000 | old_encounter_slots
        )
        new_encounter_instruction = struct.pack(
            "<I", 0x24020000 | new_encounter_slots
        )
        encounter_context_start = encounter_instruction_offset - 0x10
        encounter_context_end = encounter_instruction_offset + 0x10
        if (
            encounter_context_start < 0
            or encounter_context_end > len(decoded)
        ):
            raise WorldmapFormatError(
                "World-map encounter initialization is outside overlay"
            )
        expected_encounter_context = bytes.fromhex(
            "00 03 02 24 80 01 02 24 0A 80 01 3C 40 BE 22 AC "
            "00 00 02 24 0A 80 01 3C C4 BC 22 AC 0A 80 01 3C"
        )
        if (
            encounter_instruction_offset == 0x5780
            and decoded[encounter_context_start:encounter_context_end]
            != expected_encounter_context
        ):
            raise WorldmapFormatError(
                "World-map encounter initialization context changed"
            )
        if (
            decoded[
                encounter_instruction_offset : encounter_instruction_offset + 4
            ]
            != old_encounter_instruction
        ):
            raise WorldmapFormatError(
                "World-map encounter slot initializer is not "
                f"addiu v0,zero,{old_encounter_slots}"
            )
        edited[
            encounter_instruction_offset : encounter_instruction_offset + 4
        ] = new_encounter_instruction

    if formation_instruction_offset is not None:
        formation_context_start = formation_instruction_offset - 0x10
        formation_context_end = formation_instruction_offset + 0x10
        if formation_context_start < 0 or formation_context_end > len(decoded):
            raise WorldmapFormatError(
                "World-map encounter formation selection is outside overlay"
            )
        expected_formation_context = bytes.fromhex(
            "10 00 C6 24 F6 FF C8 14 10 00 E7 24 06 80 01 3C "
            "08 95 29 A0 01 00 02 24 2C 00 BF 8F 28 00 B2 8F"
        )
        if (
            formation_instruction_offset == 0x6584
            and decoded[formation_context_start:formation_context_end]
            != expected_formation_context
        ):
            raise WorldmapFormatError(
                "World-map encounter formation selection context changed"
            )
        old_formation_instruction = bytes.fromhex("08 95 29 A0")
        new_formation_instruction = bytes.fromhex("08 95 20 A0")
        if (
            decoded[
                formation_instruction_offset : formation_instruction_offset + 4
            ]
            != old_formation_instruction
        ):
            raise WorldmapFormatError(
                "World-map encounter formation store is not sb t1,0x9508(at)"
            )
        edited[
            formation_instruction_offset : formation_instruction_offset + 4
        ] = new_formation_instruction

    edited_bytes = bytes(edited)
    if edited_bytes.count(new_instruction) < 1:
        raise WorldmapFormatError("X interaction instruction did not survive edit")
    # The compact encoder's tail for some tiny executable-overlay edits is
    # valid to the inspection decoder but stalls the retail overlay loader.
    # Preserve the audited retail command stream and literalize only the
    # affected command-group island.  Canonical 37 ends in a partial group, so
    # supply the same zero allocation padding used by the retail reader while
    # editing and omit it again from the replacement file.
    allocation_padding = bytes(32)
    repacked_with_padding = _retail_safe_lzss_edit(
        packed + allocation_padding,
        decoded,
        edited_bytes,
    )
    repacked = repacked_with_padding[: -len(allocation_padding)]
    if decompress_worldmap(repacked) != edited_bytes:
        raise WorldmapFormatError("World-map control overlay failed its LZSS round trip")
    return PatchedWorldmapControls(
        repacked,
        edited_bytes,
        instruction_offset,
        old_mask,
        new_mask,
        encounter_instruction_offset,
        old_encounter_slots if encounter_instruction_offset is not None else None,
        new_encounter_slots if encounter_instruction_offset is not None else None,
        formation_instruction_offset,
        0 if formation_instruction_offset is not None else None,
    )


def patch_worldmap_x_interaction(
    packed: bytes,
    *,
    instruction_offset: int = 0x210A4,
    old_mask: int = 0x20,
    new_mask: int = 0x20,
) -> PatchedWorldmapControls:
    """Use physical Cross alone for world-map landmark interaction."""

    return _patch_worldmap_controls(
        packed,
        instruction_offset=instruction_offset,
        old_mask=old_mask,
        new_mask=new_mask,
    )


def patch_worldmap_standalone_controls(
    packed: bytes,
    *,
    instruction_offset: int = 0x210A4,
    old_mask: int = 0x20,
    new_mask: int = 0x20,
    encounter_instruction_offset: int = 0x5780,
    old_encounter_slots: int = 0,
    new_encounter_slots: int = 1,
    formation_instruction_offset: int = 0x6584,
) -> PatchedWorldmapControls:
    """Use Cross-only interaction and a deterministic Gear-safe encounter slot."""

    return _patch_worldmap_controls(
        packed,
        instruction_offset=instruction_offset,
        old_mask=old_mask,
        new_mask=new_mask,
        encounter_instruction_offset=encounter_instruction_offset,
        old_encounter_slots=old_encounter_slots,
        new_encounter_slots=new_encounter_slots,
        formation_instruction_offset=formation_instruction_offset,
    )


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    if args.output.exists() and not args.force:
        parser.error(f"Refusing to overwrite {args.output}; pass --force")
    try:
        result = patch_mass_driver_entry(args.source.read_bytes())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(result.packed)
    except (OSError, WorldmapFormatError) as exc:
        parser.error(str(exc))
    print(
        f"Patched spawn {result.spawn.index} at ({result.spawn.x}, {result.spawn.z}); "
        f"entry -> field {result.new_exit.destination_field} ({result.label}); "
        f"kept Taura block {result.taura_model.block_id} and Mass Driver blocks "
        f"{','.join(str(model.block_id) for model in result.mass_driver_models)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
