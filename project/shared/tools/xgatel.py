#!/usr/bin/env python3
"""Inspect and make size-preserving edits to Xenogears ATEL field scripts."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import struct
import sys
from typing import Iterable, Sequence


ENTITY_COUNT_OFFSET = 0x80
ENTRY_TABLE_OFFSET = 0x84
SCRIPTS_PER_ENTITY = 32
ENTRY_BYTES_PER_ENTITY = 0x40


class AtelFormatError(RuntimeError):
    """Raised when an ATEL script blob or requested patch is invalid."""


@dataclass(frozen=True)
class OpcodeArgument:
    method: str
    offset: int
    size: int
    name: str | None


@dataclass(frozen=True)
class OpcodeInfo:
    opcode: int
    name: str
    size: int
    arguments: tuple[OpcodeArgument, ...]
    breaks_flow: bool
    extended: bool = False


@dataclass(frozen=True)
class Instruction:
    pc: int
    opcode: int
    size: int
    name: str
    raw: bytes
    info: OpcodeInfo | None
    extended_opcode: int | None = None


@dataclass(frozen=True)
class Transition:
    pc: int
    field: int
    parameter: int


ARGUMENT_SIZES = {
    "addArgumentJumpLocation": 2,
    "addArgumentFunctionEntryPoint": 2,
    "addArgumentU16": 2,
    "addArgumentS16OrVar": 2,
    "addArgumentS16": 2,
    "addArgumentU16OrVar": 2,
    "addSignControlByte": 1,
    "addArgumentDialogId": 2,
    "addArgumentByte": 1,
    "addArgumentCharacter": 1,
    "addArgumentVarIndex": 2,
    "addArgumentPC": 1,
    "addArgumentTriggerIndex": 1,
}


def _u16(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(data):
        raise AtelFormatError(f"u16 read outside script at 0x{offset:X}")
    return struct.unpack_from("<H", data, offset)[0]


def _u32(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise AtelFormatError(f"u32 read outside script at 0x{offset:X}")
    return struct.unpack_from("<I", data, offset)[0]


class AtelScript:
    def __init__(self, data: bytes):
        if len(data) < ENTRY_TABLE_OFFSET:
            raise AtelFormatError("ATEL blob is shorter than its fixed header")
        self.data = data
        self.entity_count = _u32(data, ENTITY_COUNT_OFFSET)
        self.bytecode_offset = (
            ENTRY_TABLE_OFFSET + self.entity_count * ENTRY_BYTES_PER_ENTITY
        )
        if self.bytecode_offset > len(data):
            raise AtelFormatError(
                f"Entity table ends at 0x{self.bytecode_offset:X}, past file end"
            )
        self.bytecode = data[self.bytecode_offset :]

    def entry_points(self) -> list[tuple[int, int, int]]:
        entries = []
        for entity in range(self.entity_count):
            for script in range(SCRIPTS_PER_ENTITY):
                offset = _u16(
                    self.data,
                    ENTRY_TABLE_OFFSET
                    + entity * ENTRY_BYTES_PER_ENTITY
                    + script * 2,
                )
                if offset != 0 or script == 0:
                    if offset >= len(self.bytecode):
                        raise AtelFormatError(
                            f"Entity {entity} script {script} points past bytecode: "
                            f"0x{offset:04X}"
                        )
                    entries.append((entity, script, offset))
        return entries


def _parse_opcode_blocks(source: str, table_name: str, extended: bool) -> dict[int, OpcodeInfo]:
    marker = re.compile(
        rf"{re.escape(table_name)}\[0x([0-9A-Fa-f]+)\](.*?)(?:\.end\(\);)",
        re.DOTALL,
    )
    result: dict[int, OpcodeInfo] = {}
    for match in marker.finditer(source):
        opcode = int(match.group(1), 16)
        body = match.group(2)
        name_match = re.search(r'\.setName\("([^"]+)"\)', body)
        name = name_match.group(1) if name_match else (
            f"OPX_{opcode:02X}" if extended else f"OP_{opcode:02X}"
        )
        offset = 1
        arguments = []
        for argument in re.finditer(
            r"\.(addArgumentJumpLocation|addArgumentFunctionEntryPoint|"
            r"addArgumentU16|addArgumentS16OrVar|addArgumentS16|"
            r"addArgumentU16OrVar|addSignControlByte|addArgumentDialogId|"
            r"addArgumentByte|addArgumentCharacter|addArgumentVarIndex|"
            r"addArgumentPC|addArgumentTriggerIndex)\(([^)]*)\)",
            body,
        ):
            method = argument.group(1)
            argument_text = argument.group(2)
            argument_name = re.search(r'"([^"]+)"', argument_text)
            size = ARGUMENT_SIZES[method]
            arguments.append(
                OpcodeArgument(
                    method=method,
                    offset=offset,
                    size=size,
                    name=argument_name.group(1) if argument_name else None,
                )
            )
            offset += size
        result[opcode] = OpcodeInfo(
            opcode=opcode,
            name=name,
            size=offset,
            arguments=tuple(arguments),
            breaks_flow=".setOpcodeBreakExecutionFlow()" in body,
            extended=extended,
        )
    return result


def load_noah_metadata(path: Path | str) -> tuple[dict[int, OpcodeInfo], dict[int, OpcodeInfo]]:
    source = Path(path).read_text(encoding="utf-8")
    return (
        _parse_opcode_blocks(source, "m_opcode", False),
        _parse_opcode_blocks(source, "m_extendedOpcode", True),
    )


def _dynamic_size(bytecode: bytes, pc: int, opcode: int) -> tuple[int, str] | None:
    if opcode == 0x02:
        return 8, "JUMP_IF"
    if opcode == 0x10:
        if pc + 2 > len(bytecode):
            raise AtelFormatError("Truncated dynamic opcode 0x10")
        mode = bytecode[pc + 1]
        if mode == 0:
            return 9, "OP_10_MODE0"
        if mode == 1:
            return 2, "OP_10_MODE1"
    if opcode == 0x57:
        if pc + 2 > len(bytecode):
            raise AtelFormatError("Truncated dynamic opcode 0x57")
        mode = bytecode[pc + 1] & 3
        if mode in (0, 1):
            return 11, "OP_57_MOVE"
        if mode == 3:
            return 2, "OP_57_MODE3"
    return None


def _dynamic_extended_size(
    bytecode: bytes, pc: int, extended_opcode: int
) -> tuple[int, str] | None:
    if pc + 3 > len(bytecode):
        raise AtelFormatError(f"Truncated dynamic extended opcode at 0x{pc:04X}")
    mode = bytecode[pc + 2]
    if extended_opcode == 0x27:
        return (5, "SCREEN_DISTORTION_FADE_OUT") if mode == 0 else (
            3,
            "SCREEN_DISTORTION_FADE_OUT",
        )
    if extended_opcode == 0x5C:
        if mode in (0, 1):
            return 3, "LOAD_NEW_MECHA"
        if mode == 2:
            return 5, "LOAD_NEW_MECHA"
    if extended_opcode == 0x77:
        if mode in (0, 2):
            return 3, "LOAD_TIM_TO_VRAM"
        if mode == 1:
            return 12, "LOAD_TIM_TO_VRAM"
    return None


def decode_instruction(
    script: AtelScript,
    pc: int,
    base: dict[int, OpcodeInfo],
    extended: dict[int, OpcodeInfo],
) -> Instruction:
    bytecode = script.bytecode
    if pc < 0 or pc >= len(bytecode):
        raise AtelFormatError(f"PC is outside bytecode: 0x{pc:04X}")
    opcode = bytecode[pc]
    info: OpcodeInfo | None = None
    extended_opcode: int | None = None

    if opcode == 0xFE:
        if pc + 2 > len(bytecode):
            raise AtelFormatError(f"Truncated extended opcode at 0x{pc:04X}")
        extended_opcode = bytecode[pc + 1]
        dynamic_extended = _dynamic_extended_size(bytecode, pc, extended_opcode)
        info = extended.get(extended_opcode)
        if dynamic_extended is not None:
            size, name = dynamic_extended
            info = None
        elif info is None:
            raise AtelFormatError(
                f"Unknown extended opcode FE {extended_opcode:02X} at 0x{pc:04X}"
            )
        else:
            size = 1 + info.size
            name = info.name
    else:
        dynamic = _dynamic_size(bytecode, pc, opcode)
        if dynamic is not None:
            size, name = dynamic
        else:
            info = base.get(opcode)
            if info is None:
                raise AtelFormatError(f"Unknown opcode {opcode:02X} at 0x{pc:04X}")
            size = info.size
            name = info.name

    if pc + size > len(bytecode):
        raise AtelFormatError(f"Instruction at 0x{pc:04X} runs past bytecode")
    return Instruction(
        pc=pc,
        opcode=opcode,
        size=size,
        name=name,
        raw=bytecode[pc : pc + size],
        info=info,
        extended_opcode=extended_opcode,
    )


def scan_raw_transitions(script: AtelScript) -> list[Transition]:
    transitions = []
    data = script.bytecode
    for pc in range(0, len(data) - 4):
        if data[pc] != 0x98:
            continue
        field_raw = _u16(data, pc + 1)
        parameter_raw = _u16(data, pc + 3)
        if field_raw & 0x8000 and parameter_raw & 0x8000:
            transitions.append(
                Transition(pc, field_raw & 0x7FFF, parameter_raw & 0x7FFF)
            )
    return transitions


def reachable_instructions(
    script: AtelScript,
    base: dict[int, OpcodeInfo],
    extended: dict[int, OpcodeInfo],
) -> tuple[dict[int, Instruction], list[str]]:
    pending = [offset for _, _, offset in script.entry_points()]
    decoded: dict[int, Instruction] = {}
    errors: list[str] = []

    while pending:
        pc = pending.pop()
        while pc not in decoded and 0 <= pc < len(script.bytecode):
            try:
                instruction = decode_instruction(script, pc, base, extended)
            except AtelFormatError as exc:
                errors.append(str(exc))
                break
            decoded[pc] = instruction

            if instruction.opcode == 0x01:
                pending.append(_u16(instruction.raw, 1))
                break
            if instruction.opcode == 0x02:
                pending.append(_u16(instruction.raw, 6))
            elif instruction.opcode == 0x05:
                pending.append(_u16(instruction.raw, 1))
            elif instruction.info is not None:
                argument_base = 2 if instruction.extended_opcode is not None else 1
                for argument in instruction.info.arguments:
                    if argument.method in (
                        "addArgumentJumpLocation",
                        "addArgumentFunctionEntryPoint",
                    ):
                        position = argument_base + argument.offset - 1
                        pending.append(_u16(instruction.raw, position))

            if instruction.opcode == 0x00 or (
                instruction.info is not None and instruction.info.breaks_flow
            ):
                break
            pc += instruction.size
    return decoded, errors


def _format_instruction(instruction: Instruction) -> str:
    raw = " ".join(f"{byte:02X}" for byte in instruction.raw)
    suffix = ""
    if instruction.opcode == 0x98 and instruction.size == 5:
        field = _u16(instruction.raw, 1)
        parameter = _u16(instruction.raw, 3)
        if field & 0x8000 and parameter & 0x8000:
            suffix = f"  ; field={field & 0x7FFF}, param={parameter & 0x7FFF}"
    return f"{instruction.pc:04X}: {raw:<42} {instruction.name}{suffix}"


def command_inspect(args: argparse.Namespace) -> int:
    script = AtelScript(Path(args.script).read_bytes())
    entries = script.entry_points()
    print(f"Script: {Path(args.script).resolve()}")
    print(f"Entities: {script.entity_count}")
    print(f"Bytecode base: 0x{script.bytecode_offset:X}")
    print(f"Bytecode size: {len(script.bytecode)}")
    print(f"Non-empty entry points: {len(entries)}")
    for entity, index, pc in entries:
        print(f"  entity {entity:02d} script {index:02d} -> 0x{pc:04X}")
    return 0


def command_transitions(args: argparse.Namespace) -> int:
    script = AtelScript(Path(args.script).read_bytes())
    base, extended = load_noah_metadata(args.metadata)
    reachable, errors = reachable_instructions(script, base, extended)
    raw = scan_raw_transitions(script)
    print(f"Script: {Path(args.script).resolve()}")
    print(" PC     field  param  reachable")
    for transition in raw:
        print(
            f"0x{transition.pc:04X}  {transition.field:5d}  "
            f"{transition.parameter:5d}  "
            f"{'yes' if transition.pc in reachable else 'unproven'}"
        )
    if errors:
        unique_errors = list(dict.fromkeys(errors))
        print(f"Decoder warnings: {len(unique_errors)} unique")
        for error in unique_errors[: args.max_warnings]:
            print(f"  {error}")
    return 0


def command_disassemble(args: argparse.Namespace) -> int:
    script = AtelScript(Path(args.script).read_bytes())
    base, extended = load_noah_metadata(args.metadata)
    pc = args.start
    for _ in range(args.count):
        instruction = decode_instruction(script, pc, base, extended)
        print(_format_instruction(instruction))
        pc += instruction.size
        if instruction.opcode == 0x00:
            break
    return 0


def _immediate(value: int) -> int:
    if value < 0 or value > 0x7FFF:
        raise AtelFormatError(f"Immediate value is outside 0..32767: {value}")
    return value | 0x8000


def patch_transition(
    data: bytes,
    pc: int,
    expected_field: int,
    expected_parameter: int,
    new_field: int,
    new_parameter: int,
) -> bytes:
    script = AtelScript(data)
    absolute = script.bytecode_offset + pc
    if pc < 0 or absolute + 5 > len(data):
        raise AtelFormatError(f"Transition PC is outside bytecode: 0x{pc:04X}")
    if data[absolute] != 0x98:
        raise AtelFormatError(
            f"Expected CHANGE_FIELD opcode 0x98 at PC 0x{pc:04X}, "
            f"found 0x{data[absolute]:02X}"
        )
    old_field = _u16(data, absolute + 1)
    old_parameter = _u16(data, absolute + 3)
    if old_field != _immediate(expected_field) or old_parameter != _immediate(
        expected_parameter
    ):
        raise AtelFormatError(
            f"Transition at 0x{pc:04X} is "
            f"{old_field & 0x7FFF}/{old_parameter & 0x7FFF}, expected "
            f"{expected_field}/{expected_parameter}"
        )
    result = bytearray(data)
    struct.pack_into("<H", result, absolute + 1, _immediate(new_field))
    struct.pack_into("<H", result, absolute + 3, _immediate(new_parameter))
    return bytes(result)


def command_patch_transition(args: argparse.Namespace) -> int:
    source = Path(args.script).resolve()
    destination = Path(args.output).resolve()
    if source == destination:
        raise AtelFormatError("Output must not overwrite the source script")
    if destination.exists() and not args.force:
        raise AtelFormatError(f"Refusing to overwrite {destination}; pass --force")
    patched = patch_transition(
        source.read_bytes(),
        args.pc,
        args.expect_field,
        args.expect_param,
        args.field,
        args.param,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(patched)
    print(
        f"Patched PC 0x{args.pc:04X}: {args.expect_field}/{args.expect_param} -> "
        f"{args.field}/{args.param}"
    )
    print(f"Wrote {destination}")
    return 0


def _integer(value: str) -> int:
    try:
        return int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not an integer: {value}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("script", type=Path)
    inspect_parser.set_defaults(handler=command_inspect)

    transitions_parser = subparsers.add_parser("transitions")
    transitions_parser.add_argument("script", type=Path)
    transitions_parser.add_argument("--metadata", type=Path, required=True)
    transitions_parser.add_argument("--max-warnings", type=int, default=10)
    transitions_parser.set_defaults(handler=command_transitions)

    disassemble_parser = subparsers.add_parser("disassemble")
    disassemble_parser.add_argument("script", type=Path)
    disassemble_parser.add_argument("--metadata", type=Path, required=True)
    disassemble_parser.add_argument("--start", type=_integer, required=True)
    disassemble_parser.add_argument("--count", type=int, default=40)
    disassemble_parser.set_defaults(handler=command_disassemble)

    patch_parser = subparsers.add_parser("patch-transition")
    patch_parser.add_argument("script", type=Path)
    patch_parser.add_argument("output", type=Path)
    patch_parser.add_argument("--pc", type=_integer, required=True)
    patch_parser.add_argument("--expect-field", type=_integer, required=True)
    patch_parser.add_argument("--expect-param", type=_integer, required=True)
    patch_parser.add_argument("--field", type=_integer, required=True)
    patch_parser.add_argument("--param", type=_integer, required=True)
    patch_parser.add_argument("--force", action="store_true")
    patch_parser.set_defaults(handler=command_patch_transition)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (AtelFormatError, OSError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
