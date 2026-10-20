"""Compile speaker-aware Rico windows without moving existing ATEL addresses.

Each proven F5 call site is replaced with a same-sized CALL/WAIT pair. An
appended native subroutine selects the speaker's portrait, displays each
independent page and returns to the original continuation. Source dialogue
IDs and all unrelated payloads remain stable. No pattern-only byte patching.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import struct
from typing import Callable, Mapping

from shared.tools import xgatel
from shared.tools.xgdialog import decode_text, encode_text
from shared.tools.xgfield import build_field_preserving, parse_field
from shared.tools.xgscript import AtelScript
from modules.rico.dialogue_presentation import plan_dialogue, SPEAKER_LABELS

ROOT = Path(__file__).resolve().parents[2]
METADATA = ROOT / "work/noah-decomp/NoahLib/field/fieldDebugger/atelOpcodes.cpp"
NO_PORTRAIT = 0xFC
_LABEL = re.compile(r"(?:^|<New>)(" + "|".join(re.escape(v) for v in SPEAKER_LABELS) + r")\n")


class PortraitCompileError(ValueError):
    pass


@dataclass(frozen=True)
class FieldPresentation:
    bundle: bytes
    windows: int
    calls: int
    speakers: tuple[str, ...]
    maximum_original_call_depth: int


def opcode_metadata():
    """Supplement Noah's declarations with already audited native routines.

    FE1B's two signed words are the native door rotation step (the pinned
    CHAPTER_*_DOOR_*_SUBROUTINE bodies). FE14 is the preserved field237 model
    setup's two immediate words. FE84's four words and VM advance are defined
    by Noah OPX_84. These declarations describe lengths, not inferred names.
    Base OP1B advances seven bytes in Noah OP_1B and appears in the exact
    native field196 resident INITs, including their walkmesh-layer operand.
    """
    base, extended = xgatel.load_noah_metadata(METADATA)
    for opcode, size in ((0x1B, 6), (0x14, 6), (0x84, 10), (0x7F, 2)):
        extended[opcode] = xgatel.OpcodeInfo(opcode, f"AUDITED_FE_{opcode:02X}",
                                           size - 1, (), False, True)
    base[0x0D] = xgatel.OpcodeInfo(0x0D, "RETURN", 1, (), True)
    base[0x1B] = xgatel.OpcodeInfo(0x1B, "AUDITED_1B", 7, (), False)
    base[0x5B] = xgatel.OpcodeInfo(0x5B, "RETIRE_UPDATE", 1, (), True)
    return base, extended


def _decode(script: bytes):
    parsed = xgatel.AtelScript(script)
    base, extended = opcode_metadata()
    instructions, errors = xgatel.reachable_instructions(parsed, base, extended)
    if errors:
        raise PortraitCompileError("Unproven ATEL flow: " + "; ".join(dict.fromkeys(errors)))
    return parsed, instructions


def _call_depths(script, instructions, targets: set[int]) -> dict[int, int]:
    """Explore native calls/returns with a concrete bounded return stack.

    Branch outcomes are both followed. Actor-script entry points have their
    own empty call stack. Reject recursive/overdeep paths before adding CALL.
    """
    pending = [(pc, ()) for _, _, pc in script.entry_points()]
    seen = set()
    depths = {}
    while pending:
        pc, stack = pending.pop()
        key = (pc, stack)
        if key in seen:
            continue
        seen.add(key)
        if len(seen) > 300000:
            raise PortraitCompileError("Call-flow audit exceeded its finite budget")
        instruction = instructions.get(pc)
        if instruction is None:
            raise PortraitCompileError(f"Call flow reached undecoded PC {pc:#x}")
        if pc in targets:
            depths[pc] = max(depths.get(pc, 0), len(stack))
            if len(stack) >= 4:
                raise PortraitCompileError(f"Portrait call at {pc:#x} would overflow the native stack")
        opcode, raw = instruction.opcode, instruction.raw
        next_pc = pc + instruction.size
        if opcode == 0x05:
            if len(stack) >= 4:
                raise PortraitCompileError(f"Existing CALL at {pc:#x} exceeds native stack")
            pending.append((struct.unpack_from("<H", raw, 1)[0], (*stack, next_pc)))
            continue
        if opcode == 0x0A:
            # Native CALL_IF_IN_TRIGGER has a one-byte trigger selector and
            # a u16 destination. Both trigger outcomes are possible. At depth
            # four it deliberately falls through instead of pushing a fifth
            # return address (Noah OP_CALL_IF_IN_TRIGGER).
            pending.append((next_pc, stack))
            if len(stack) < 4:
                pending.append((struct.unpack_from("<H", raw, 2)[0], (*stack, next_pc)))
            continue
        if opcode == 0x0D:
            if stack:
                pending.append((stack[-1], stack[:-1]))
            continue
        if opcode in (0x00, 0x5B):
            continue
        if opcode == 0x01:
            pending.append((struct.unpack_from("<H", raw, 1)[0], stack))
            continue
        if opcode == 0x02:
            pending.append((struct.unpack_from("<H", raw, 6)[0], stack))
        elif instruction.info:
            start = 2 if instruction.extended_opcode is not None else 1
            for argument in instruction.info.arguments:
                if argument.method == "addArgumentJumpLocation":
                    target = struct.unpack_from("<H", raw, start + argument.offset - 1)[0]
                    pending.append((target, stack))
        if instruction.info and instruction.info.breaks_flow:
            continue
        if next_pc < len(script.bytecode):
            pending.append((next_pc, stack))
    if set(depths) != targets:
        raise PortraitCompileError("Some dialogue call sites have unproven call-stack depth")
    return depths


def _dialogue_records(source: bytes) -> list[tuple[int, int, bytes]]:
    """Read tables while preserving harmless trailing retail bytes verbatim."""
    if len(source) < 8:
        raise PortraitCompileError("Dialogue is truncated")
    count = struct.unpack_from("<I", source)[0] + 1
    header = 4 + 4 * count
    if header > len(source):
        raise PortraitCompileError("Dialogue table exceeds component")
    offsets = list(struct.unpack_from(f"<{count}H", source, 4))
    if offsets[0] != header or offsets != sorted(set(offsets)) or offsets[-1] >= len(source):
        raise PortraitCompileError("Invalid dialogue offset table")
    ends = offsets[1:] + [len(source)]
    dimensions = 4 + 2 * count
    return [(source[dimensions + 2*i], source[dimensions + 2*i+1], source[start:end])
            for i, (start, end) in enumerate(zip(offsets, ends))]


def _encode_records(records):
    cursor = 4 + 4 * len(records)
    offsets = []
    for _, _, payload in records:
        offsets.append(cursor)
        cursor += len(payload)
    if cursor > 0xFFFF:
        raise PortraitCompileError(f"Presented dialogue exceeds 64 KiB: {cursor}")
    return (struct.pack("<I", len(records)-1)
            + struct.pack(f"<{len(offsets)}H", *offsets)
            + bytes(value for width, height, _ in records for value in (width, height))
            + b"".join(payload for _, _, payload in records))


def _release(pc: int) -> bytes:
    # Cross held-word loop, yielding a frame; used between independent windows.
    return b"\x31\x20\x00" + struct.pack("<H", pc+11) + b"\x26\x01\x80\x01" + struct.pack("<H", pc)


def present_field(source: bytes, portrait_ids: Mapping[str, int], *,
                  colorize: Callable[[str], str] = lambda value: value) -> FieldPresentation:
    field = parse_field(source)
    components = [part.data for part in field.parts]
    script, instructions = _decode(components[5])
    records = _dialogue_records(components[7])
    calls = {}
    plans = {}
    for pc, instruction in instructions.items():
        if instruction.opcode != 0xF5:
            continue
        block = struct.unpack_from("<H", instruction.raw, 1)[0]
        if block >= len(records):
            raise PortraitCompileError(f"F5 at {pc:#x} references absent dialogue {block}")
        text = decode_text(records[block][2])
        if not _LABEL.search(text):
            continue
        following = instructions.get(pc + instruction.size)
        if following is None or following.opcode != 0x9C:
            raise PortraitCompileError(
                f"Speaking F5 at {pc:#x} is not immediately awaited; "
                "a blocking portrait helper would change its scene timing"
            )
        if block not in plans:
            # Do not normalize old trailing bytes: only a standard authored
            # block is eligible for presentation.
            if text.count("<Close>") != 1 or not text.endswith("<Close>"):
                raise PortraitCompileError(f"Speaking block {block} has irregular terminal controls")
            plans[block] = plan_dialogue(text)
        calls[pc] = (block, instruction.raw[3])
    if not calls:
        return FieldPresentation(source, 0, 0, (), 0)
    for instruction in instructions.values():
        if instruction.opcode in (0xD2, 0xD4, 0xFC):
            # These native forms still address the original dialogue table.
            # Replacing a shared record with its first portrait segment would
            # silently truncate their conversation or alter menu semantics.
            offset = 1 if instruction.opcode == 0xD2 else 2
            block = struct.unpack_from("<H", instruction.raw, offset)[0]
            if block in plans:
                raise PortraitCompileError(
                    f"Speaking block {block} is shared with non-F5 dialogue "
                    f"opcode {instruction.opcode:#x} at {instruction.pc:#x}"
                )
    depths = _call_depths(script, instructions, set(calls))
    speakers = set()
    compiled = {}
    for block, segments in sorted(plans.items()):
        pages = []
        for index, segment in enumerate(segments):
            if segment.speaker:
                if segment.speaker not in portrait_ids:
                    raise PortraitCompileError(f"No portrait allocated for {segment.speaker}")
                portrait = portrait_ids[segment.speaker]
                if not 0 <= portrait < 90:
                    raise PortraitCompileError(f"Portrait ID is outside native table: {portrait}")
                speakers.add(segment.speaker)
                text = colorize(segment.text)
            else:
                portrait, text = NO_PORTRAIT, segment.text
            record = (segment.width, segment.height, encode_text(text))
            if index == 0:
                records[block] = record
                target = block
            else:
                target = len(records)
                records.append(record)
            pages.append((target, portrait))
        compiled[block] = pages
    editor = AtelScript(components[5])
    helpers = {}
    patches = {}
    for pc, (block, flags) in sorted(calls.items()):
        key = (block, flags)
        if key not in helpers:
            start = editor.bytecode_size
            body = bytearray()
            for index, (target, portrait) in enumerate(compiled[block]):
                if index:
                    body += _release(start + len(body)) + b"\x26\x01\x80"
                # Clear inherited actor overrides before applying table
                # dimensions. F4 01 yields and resets size/position/flags;
                # FE0D then selects the new portrait and F5 reapplies the
                # original instruction's flags, including hidden ownership.
                body += b"\xF4\x01"
                body += b"\xFE\x0D" + struct.pack("<H", 0x8000 | portrait)
                # Bit0 explicitly supports invisible directors; bit1 would
                # suppress the selected portrait and its text column.
                page_flags = (flags | 1) & ~2 if portrait != NO_PORTRAIT else flags | 1
                body += b"\xF5" + struct.pack("<H", target) + bytes((page_flags, 0x9C))
            body += b"\xFE\x0D\xFC\x80\x0D"
            actual = editor.append_raw_routine(bytes(body))
            if actual != start:
                raise PortraitCompileError("Appended presentation helper moved")
            helpers[key] = start
        patches[pc] = b"\x05" + struct.pack("<H", helpers[key]) + b"\x9C"
    data = bytearray(editor.to_bytes())
    for pc, replacement in patches.items():
        absolute = editor.bytecode_offset + pc
        if bytes(data[absolute:absolute+4]) != instructions[pc].raw:
            raise PortraitCompileError("Dialogue callsite bytes changed before patch")
        data[absolute:absolute+4] = replacement
    components[5] = bytes(data)
    components[7] = _encode_records(records)
    result = build_field_preserving(source, components, (5, 7), compact_changed=True)
    parsed = parse_field(result)
    if (parsed.header[:0x10C] != field.header[:0x10C]
            or parsed.header[0x154:] != field.header[0x154:]) or any(parsed.parts[i].data != field.parts[i].data
                                          for i in (0, 1, 2, 3, 4, 6, 8)):
        raise PortraitCompileError("Presentation changed a non-dialogue scene resource")
    _decode(components[5])
    return FieldPresentation(result, sum(len(p) for p in compiled.values()), len(calls),
                             tuple(sorted(speakers)), max(depths.values(), default=0))
