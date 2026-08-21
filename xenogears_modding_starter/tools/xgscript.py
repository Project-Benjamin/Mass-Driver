#!/usr/bin/env python3
"""Safely append and repoint routines in Xenogears ATEL field scripts.

ATEL stores a fixed header followed by 32 little-endian, bytecode-relative
script pointers for each entity.  This module deliberately does not assemble
instructions; it only provides the small, lossless operations needed to append
already-encoded routines and point an entity script slot at them.
"""

from __future__ import annotations

import struct


ENTITY_COUNT_OFFSET = 0x80
ENTRY_TABLE_OFFSET = 0x84
SCRIPTS_PER_ENTITY = 32
ENTRY_BYTES_PER_ENTITY = SCRIPTS_PER_ENTITY * 2
MAX_SCRIPT_OFFSET = 0xFFFF
MAX_BYTECODE_SIZE = MAX_SCRIPT_OFFSET + 1


class ScriptFormatError(RuntimeError):
    """Raised when an ATEL blob or requested edit is invalid."""


def _byteslike(value: object, label: str) -> bytes:
    if not isinstance(value, (bytes, bytearray, memoryview)):
        raise ScriptFormatError(f"{label} must be bytes-like")
    return bytes(value)


class AtelScript:
    """Mutable, bounds-checked editor for an ATEL script component."""

    def __init__(self, data: bytes | bytearray | memoryview):
        self._data = bytearray(_byteslike(data, "ATEL data"))
        if len(self._data) < ENTRY_TABLE_OFFSET:
            raise ScriptFormatError("ATEL blob is shorter than its fixed header")

        self.entity_count = struct.unpack_from(
            "<I", self._data, ENTITY_COUNT_OFFSET
        )[0]
        self.bytecode_offset = (
            ENTRY_TABLE_OFFSET + self.entity_count * ENTRY_BYTES_PER_ENTITY
        )
        if self.bytecode_offset > len(self._data):
            raise ScriptFormatError(
                f"Entity table ends at 0x{self.bytecode_offset:X}, past file end"
            )
        if self.bytecode_size > MAX_BYTECODE_SIZE:
            raise ScriptFormatError(
                f"ATEL bytecode is {self.bytecode_size} bytes; script pointers "
                "are limited to 16-bit offsets"
            )

        self._validate_existing_pointers()

    @property
    def bytecode_size(self) -> int:
        return len(self._data) - self.bytecode_offset

    @property
    def bytecode(self) -> bytes:
        return bytes(self._data[self.bytecode_offset :])

    def _pointer_location(self, entity: int, script_index: int) -> int:
        if not isinstance(entity, int) or not 0 <= entity < self.entity_count:
            raise ScriptFormatError(
                f"Entity index must be in 0..{self.entity_count - 1}: {entity}"
            )
        if not isinstance(script_index, int) or not 0 <= script_index < SCRIPTS_PER_ENTITY:
            raise ScriptFormatError(
                f"Script index must be in 0..{SCRIPTS_PER_ENTITY - 1}: "
                f"{script_index}"
            )
        return (
            ENTRY_TABLE_OFFSET
            + entity * ENTRY_BYTES_PER_ENTITY
            + script_index * 2
        )

    def _validate_pointer(self, script_index: int, offset: int) -> None:
        if not isinstance(offset, int) or not 0 <= offset <= MAX_SCRIPT_OFFSET:
            raise ScriptFormatError(
                f"Script pointer must be a 16-bit offset in 0..65535: {offset}"
            )

        # Zero marks an unused slot except for script zero, whose normal entry
        # point is bytecode offset zero.
        if offset == 0 and script_index != 0:
            return
        if offset >= self.bytecode_size:
            raise ScriptFormatError(
                f"Script pointer 0x{offset:04X} is outside "
                f"{self.bytecode_size}-byte bytecode"
            )

    def _validate_existing_pointers(self) -> None:
        for entity in range(self.entity_count):
            for script_index in range(SCRIPTS_PER_ENTITY):
                location = self._pointer_location(entity, script_index)
                offset = struct.unpack_from("<H", self._data, location)[0]
                try:
                    self._validate_pointer(script_index, offset)
                except ScriptFormatError as exc:
                    raise ScriptFormatError(
                        f"Entity {entity} script {script_index}: {exc}"
                    ) from exc

    def get_script_pointer(self, entity: int, script_index: int) -> int:
        """Return one bytecode-relative script pointer."""

        location = self._pointer_location(entity, script_index)
        return struct.unpack_from("<H", self._data, location)[0]

    def set_script_pointer(
        self, entity: int, script_index: int, offset: int
    ) -> None:
        """Set one pointer after checking the slot and bytecode target."""

        location = self._pointer_location(entity, script_index)
        self._validate_pointer(script_index, offset)
        struct.pack_into("<H", self._data, location, offset)

    def append_raw_routine(self, routine: bytes | bytearray | memoryview) -> int:
        """Append encoded ATEL bytes and return their bytecode-relative offset."""

        encoded = _byteslike(routine, "Routine")
        if not encoded:
            raise ScriptFormatError("Routine must contain at least one byte")

        offset = self.bytecode_size
        new_size = offset + len(encoded)
        if offset > MAX_SCRIPT_OFFSET or new_size > MAX_BYTECODE_SIZE:
            raise ScriptFormatError(
                f"Appending {len(encoded)} bytes would grow ATEL bytecode to "
                f"{new_size} bytes, beyond the 16-bit offset limit"
            )
        self._data.extend(encoded)
        return offset

    def append_and_repoint(
        self,
        entity: int,
        script_index: int,
        routine: bytes | bytearray | memoryview,
    ) -> int:
        """Append a routine, repoint a script slot, and return its new offset."""

        # Check the destination before mutating the blob.
        self._pointer_location(entity, script_index)
        offset = self.append_raw_routine(routine)
        self.set_script_pointer(entity, script_index, offset)
        return offset

    def to_bytes(self) -> bytes:
        """Return the edited ATEL component."""

        return bytes(self._data)

    def __bytes__(self) -> bytes:
        return self.to_bytes()
