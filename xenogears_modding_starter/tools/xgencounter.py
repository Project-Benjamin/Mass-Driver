#!/usr/bin/env python3
"""Parse and safely edit Xenogears field encounter components.

The decompressed component is exactly 528 bytes: sixteen 32-byte battle
formations followed by sixteen one-byte random-encounter weights.  Within a
formation, bytes 0x08..0x0F select up to eight enemy definitions and bytes
0x18..0x1F select their arena positions.  The low seven bits hold the value;
the enemy selector's high bit marks a Gear battle and other high bits are
preserved as opaque flags.
"""

from __future__ import annotations

from dataclasses import dataclass


FORMATION_COUNT = 16
FORMATION_SIZE = 0x20
FORMATIONS_SIZE = FORMATION_COUNT * FORMATION_SIZE
WEIGHTS_OFFSET = FORMATIONS_SIZE
ENCOUNTER_COMPONENT_SIZE = WEIGHTS_OFFSET + FORMATION_COUNT

ENEMY_COUNT = 8
ENEMY_IDS_OFFSET = 0x08
ENEMY_POSITIONS_OFFSET = 0x18
VALUE_MASK = 0x7F
FLAG_MASK = 0x80

# A battle data file contains eight enemy definitions.  0x7F is the game's
# empty-slot sentinel rather than definition 127.
MAX_ENEMY_ID = 7
EMPTY_ENEMY_ID = 0x7F
MAX_CHARACTER_POSITION = 3
MAX_GEAR_POSITION = 7
EMPTY_POSITION = 0x7F


class EncounterFormatError(RuntimeError):
    """Raised when an encounter component or requested edit is invalid."""


@dataclass(frozen=True)
class EnemyPlacement:
    enemy_id: int
    position: int
    is_gear: bool
    position_flag: bool


def validate_enemy_id(enemy_id: int) -> None:
    """Validate an enemy-definition index or the empty-slot sentinel."""

    if not isinstance(enemy_id, int) or not (
        0 <= enemy_id <= MAX_ENEMY_ID or enemy_id == EMPTY_ENEMY_ID
    ):
        raise EncounterFormatError(
            f"Enemy ID must be 0..{MAX_ENEMY_ID} or 0x7F: {enemy_id}"
        )


def validate_enemy_position(
    position: int, *, is_gear: bool, allow_empty: bool = True
) -> None:
    """Validate an arena slot for a character-scale or Gear-scale enemy."""

    maximum = MAX_GEAR_POSITION if is_gear else MAX_CHARACTER_POSITION
    if not isinstance(position, int) or not (
        0 <= position <= maximum or (allow_empty and position == EMPTY_POSITION)
    ):
        suffix = " or 0x7F" if allow_empty else ""
        scale = "Gear" if is_gear else "character"
        raise EncounterFormatError(
            f"{scale} enemy position must be 0..{maximum}{suffix}: {position}"
        )


class EncounterTable:
    """Mutable, strictly validated representation of one encounter component."""

    def __init__(self, data: bytes | bytearray | memoryview):
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise EncounterFormatError("Encounter data must be bytes-like")
        self._data = bytearray(data)
        if len(self._data) != ENCOUNTER_COMPONENT_SIZE:
            raise EncounterFormatError(
                f"Encounter component must be exactly "
                f"{ENCOUNTER_COMPONENT_SIZE} bytes, got {len(self._data)}"
            )
        self.validate()

    @staticmethod
    def _formation_index(index: int) -> int:
        if not isinstance(index, int) or not 0 <= index < FORMATION_COUNT:
            raise EncounterFormatError(
                f"Formation index must be in 0..{FORMATION_COUNT - 1}: {index}"
            )
        return index

    @staticmethod
    def _enemy_index(index: int) -> int:
        if not isinstance(index, int) or not 0 <= index < ENEMY_COUNT:
            raise EncounterFormatError(
                f"Enemy slot must be in 0..{ENEMY_COUNT - 1}: {index}"
            )
        return index

    def _enemy_offsets(self, formation: int, enemy_slot: int) -> tuple[int, int]:
        formation = self._formation_index(formation)
        enemy_slot = self._enemy_index(enemy_slot)
        base = formation * FORMATION_SIZE
        return (
            base + ENEMY_IDS_OFFSET + enemy_slot,
            base + ENEMY_POSITIONS_OFFSET + enemy_slot,
        )

    def formation(self, index: int) -> bytes:
        """Return one raw 32-byte formation."""

        index = self._formation_index(index)
        start = index * FORMATION_SIZE
        return bytes(self._data[start : start + FORMATION_SIZE])

    def copy_formation(
        self, source: int, destination: int, *, copy_weight: bool = False
    ) -> None:
        """Copy a formation, optionally copying its independent weight too."""

        source = self._formation_index(source)
        destination = self._formation_index(destination)
        source_start = source * FORMATION_SIZE
        destination_start = destination * FORMATION_SIZE
        formation = bytes(
            self._data[source_start : source_start + FORMATION_SIZE]
        )
        self._data[
            destination_start : destination_start + FORMATION_SIZE
        ] = formation
        if copy_weight:
            self._data[WEIGHTS_OFFSET + destination] = self._data[
                WEIGHTS_OFFSET + source
            ]

    @property
    def weights(self) -> tuple[int, ...]:
        return tuple(self._data[WEIGHTS_OFFSET:])

    def get_weight(self, formation: int) -> int:
        formation = self._formation_index(formation)
        return self._data[WEIGHTS_OFFSET + formation]

    def set_weight(self, formation: int, weight: int) -> None:
        formation = self._formation_index(formation)
        if not isinstance(weight, int) or not 0 <= weight <= 0xFF:
            raise EncounterFormatError(
                f"Encounter weight must be in 0..255: {weight}"
            )
        self._data[WEIGHTS_OFFSET + formation] = weight

    def get_enemy(self, formation: int, enemy_slot: int) -> EnemyPlacement:
        enemy_offset, position_offset = self._enemy_offsets(
            formation, enemy_slot
        )
        enemy = self._data[enemy_offset]
        position = self._data[position_offset]
        return EnemyPlacement(
            enemy_id=enemy & VALUE_MASK,
            position=position & VALUE_MASK,
            is_gear=bool(enemy & FLAG_MASK),
            position_flag=bool(position & FLAG_MASK),
        )

    def get_enemy_id(self, formation: int, enemy_slot: int) -> int:
        return self.get_enemy(formation, enemy_slot).enemy_id

    def get_enemy_position(self, formation: int, enemy_slot: int) -> int:
        return self.get_enemy(formation, enemy_slot).position

    def set_enemy_id(
        self, formation: int, enemy_slot: int, enemy_id: int
    ) -> None:
        """Set an ID while preserving that selector's Gear flag."""

        validate_enemy_id(enemy_id)
        enemy_offset, _ = self._enemy_offsets(formation, enemy_slot)
        current = self.get_enemy(formation, enemy_slot)
        if enemy_id != EMPTY_ENEMY_ID:
            validate_enemy_position(
                current.position, is_gear=current.is_gear, allow_empty=False
            )
        self._data[enemy_offset] = (
            self._data[enemy_offset] & FLAG_MASK
        ) | enemy_id

    def set_enemy_position(
        self, formation: int, enemy_slot: int, position: int
    ) -> None:
        """Set a position while preserving its opaque high-bit flag."""

        enemy_offset, position_offset = self._enemy_offsets(
            formation, enemy_slot
        )
        enemy = self._data[enemy_offset]
        enemy_id = enemy & VALUE_MASK
        is_gear = bool(enemy & FLAG_MASK)
        validate_enemy_position(
            position,
            is_gear=is_gear,
            allow_empty=enemy_id == EMPTY_ENEMY_ID,
        )
        self._data[position_offset] = (
            self._data[position_offset] & FLAG_MASK
        ) | position

    def set_enemy(
        self,
        formation: int,
        enemy_slot: int,
        enemy_id: int,
        position: int,
        *,
        is_gear: bool,
    ) -> None:
        """Atomically set an enemy ID, position, and scale flag."""

        if not isinstance(is_gear, bool):
            raise EncounterFormatError("is_gear must be a bool")
        validate_enemy_id(enemy_id)
        validate_enemy_position(
            position,
            is_gear=is_gear,
            allow_empty=enemy_id == EMPTY_ENEMY_ID,
        )
        enemy_offset, position_offset = self._enemy_offsets(
            formation, enemy_slot
        )
        self._data[enemy_offset] = enemy_id | (FLAG_MASK if is_gear else 0)
        self._data[position_offset] = (
            self._data[position_offset] & FLAG_MASK
        ) | position

    def validate(self) -> None:
        """Validate all encoded enemy IDs and active arena positions."""

        for formation in range(FORMATION_COUNT):
            for enemy_slot in range(ENEMY_COUNT):
                placement = self.get_enemy(formation, enemy_slot)
                try:
                    validate_enemy_id(placement.enemy_id)
                    validate_enemy_position(
                        placement.position,
                        is_gear=placement.is_gear,
                        allow_empty=placement.enemy_id == EMPTY_ENEMY_ID,
                    )
                except EncounterFormatError as exc:
                    raise EncounterFormatError(
                        f"Formation {formation} enemy slot {enemy_slot}: {exc}"
                    ) from exc

    def to_bytes(self) -> bytes:
        """Return the edited 528-byte component."""

        return bytes(self._data)

    def __bytes__(self) -> bytes:
        return self.to_bytes()
