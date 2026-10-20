"""Checked ATEL operands and variable writes shared by chapter builders.

Legacy DungeonBuildError keeps its name and identity for existing callers;
AtelEncodingError is the chapter-independent public alias for new code.
"""

from __future__ import annotations

import struct

class DungeonBuildError(RuntimeError):
    """Raised when an input or checked patch does not match the audited build."""


def u16(value: int) -> bytes:
    if not isinstance(value, int) or not 0 <= value <= 0xFFFF:
        raise DungeonBuildError(f"u16 value outside 0..65535: {value}")
    return struct.pack("<H", value)


def s16(value: int) -> bytes:
    if not isinstance(value, int) or not -0x8000 <= value <= 0x7FFF:
        raise DungeonBuildError(f"s16 value outside -32768..32767: {value}")
    return struct.pack("<h", value)


def immediate(value: int) -> bytes:
    if not isinstance(value, int) or not 0 <= value <= 0x7FFF:
        raise DungeonBuildError(f"ATEL immediate outside 0..32767: {value}")
    return u16(value | 0x8000)


def set_var_bit(variable: int, bit_index: int) -> bytes:
    """Set one bit in a persistent ATEL variable without disturbing the rest."""

    if not 0 <= bit_index <= 15:
        raise DungeonBuildError(f"ATEL bit index outside 0..15: {bit_index}")
    return b"\x3A" + u16(variable) + u16(bit_index) + b"\x40"


def clear_var_bit(variable: int, bit_index: int) -> bytes:
    """Clear one bit in an ATEL variable without disturbing the rest."""

    if not 0 <= bit_index <= 15:
        raise DungeonBuildError(f"ATEL bit index outside 0..15: {bit_index}")
    return b"\x3B" + u16(variable) + u16(bit_index) + b"\x40"


def set_variable_s16(variable: int, value: int) -> bytes:
    """Set one ATEL variable from a checked signed literal."""

    if not isinstance(variable, int) or not 0 <= variable <= 0xFFFF:
        raise DungeonBuildError(f"ATEL variable outside 0..65535: {variable}")
    if variable & 1:
        raise DungeonBuildError(f"ATEL variable address is not aligned: {variable}")
    return b"\x35" + u16(variable) + s16(value) + b"\x40"


def copy_variable(destination: int, source: int) -> bytes:
    """Copy one ATEL field word into another."""

    for label, variable in (("destination", destination), ("source", source)):
        if not isinstance(variable, int) or not 0 <= variable <= 0x07FE:
            raise DungeonBuildError(
                f"ATEL copy {label} variable is outside 0000..07FE: {variable}"
            )
        if variable & 1:
            raise DungeonBuildError(
                f"ATEL copy {label} variable is not aligned: {variable}"
            )
    return b"\x35" + u16(destination) + u16(source) + b"\x00"


def variable_math(
    opcode: int,
    destination: int,
    operand: int,
    *,
    operand_is_variable: bool = False,
) -> bytes:
    """Encode one checked six-byte ATEL arithmetic assignment."""

    if opcode not in (0x38, 0x39, 0x3E, 0xDE, 0xDF):
        raise DungeonBuildError(f"Unsupported ATEL arithmetic opcode: {opcode:#x}")
    if not 0 <= destination <= 0x07FE or destination & 1:
        raise DungeonBuildError(
            f"ATEL arithmetic destination is invalid: {destination}"
        )
    if operand_is_variable:
        if not 0 <= operand <= 0x07FE or operand & 1:
            raise DungeonBuildError(
                f"ATEL arithmetic source variable is invalid: {operand}"
            )
        encoded_operand = u16(operand)
        flags = 0
    else:
        encoded_operand = s16(operand)
        flags = 0x40
    return bytes((opcode,)) + u16(destination) + encoded_operand + bytes((flags,))


AtelEncodingError = DungeonBuildError
