#!/usr/bin/env python3
"""Inspect and rebuild Xenogears field dialogue components.

Field dialogue is component 07 of a field bundle after decompression.  ATEL
scripts address its blocks by zero-based ID, while this component owns the
variable-length byte offsets.  Rebuilding the offset table therefore permits
text changes without modifying the field script.

The JSON representation is deliberately strict and deterministic.  Literal
newlines encode the game's line-break byte.  Other non-printing values use
explicit tokens such as ``<Close>``, ``<New>``, ``<Wait>``, ``<Delay:8>``,
``<Elly>``, and the lossless fallback ``<Byte:90>``.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
from typing import Any, Mapping, Sequence


DIALOGUE_JSON_FORMAT = "xenogears-field-dialogue-v1"
REPLACEMENTS_JSON_FORMAT = "xenogears-field-dialogue-replacements-v1"
MAX_DIALOGUE_SIZE = 0xFFFF


class DialogueFormatError(RuntimeError):
    """Raised when a dialogue component or requested rebuild is invalid."""


@dataclass(frozen=True)
class DialogueBlock:
    block_id: int
    width: int
    height: int
    offset: int
    payload: bytes
    text: str


@dataclass(frozen=True)
class ParsedDialogue:
    source: bytes
    blocks: tuple[DialogueBlock, ...]


@dataclass(frozen=True)
class DialogueBlockSpec:
    block_id: int
    width: int
    height: int
    text: str


PLAIN_ENCODE: dict[str, int] = {
    " ": 0x10,
    "+": 0x11,
    ",": 0x12,
    "-": 0x13,
    ".": 0x14,
    "/": 0x15,
    "[": 0x3A,
    "]": 0x3B,
    "=": 0x3C,
    "!": 0x57,
    '"': 0x58,
    "#": 0x59,
    "%": 0x5A,
    "&": 0x5B,
    "'": 0x5C,
    "(": 0x5D,
    ")": 0x5E,
    ":": 0x5F,
    "?": 0x60,
    "*": 0x6D,
}
PLAIN_ENCODE.update({str(value): 0x16 + value for value in range(10)})
PLAIN_ENCODE.update(
    {chr(ord("A") + value): 0x20 + value for value in range(26)}
)
PLAIN_ENCODE.update(
    {chr(ord("a") + value): 0x3D + value for value in range(26)}
)
PLAIN_DECODE = {value: key for key, value in PLAIN_ENCODE.items()}


CHARACTER_NAMES: dict[int, str] = {
    0: "Fei",
    1: "Elly",
    2: "Citan",
    3: "Bart",
    4: "Billy",
    5: "Rico",
    6: "Emeralda",
    7: "Chu-Chu",
    8: "Maria",
    9: "Citan2",
    10: "Emeralda2",
    11: "Weltall",
    12: "Weltall-2",
    13: "Vierge",
    14: "Heimdal",
    15: "Brigandier",
    16: "Renmazuo",
    17: "Stier",
    18: "BigChu-chu",
    19: "Seibzehn",
    20: "Crescens",
    21: "El-Regulus",
    22: "Fenrir",
    23: "Andvari",
    24: "Renmazuo2",
    25: "Stier-2",
    26: "Xenogears",
    27: "BARTHOS",
    28: "Yggdra",
    128: "Perso1",
    129: "Perso2",
    130: "Perso3",
}
CHARACTER_IDS = {name: value for value, name in CHARACTER_NAMES.items()}


BYTE_TOKEN = re.compile(r"Byte:([0-9A-Fa-f]{2})", re.ASCII)
DELAY_TOKEN = re.compile(r"Delay:(\d{1,3})", re.ASCII)
NAME_TOKEN = re.compile(r"Name:(\d{1,3})", re.ASCII)
OPCODE_TOKEN = re.compile(
    r"Opcode:([0-9A-Fa-f]{2}):([0-9A-Fa-f]{2})", re.ASCII
)
EXTRA1_TOKEN = re.compile(r"Extra1:([0-9A-Fa-f]{2})", re.ASCII)
EXTRA2_TOKEN = re.compile(r"Extra2:([0-9A-Fa-f]{2})", re.ASCII)


def _u16(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 2 > len(data):
        raise DialogueFormatError(f"u16 read outside dialogue at 0x{offset:X}")
    return struct.unpack_from("<H", data, offset)[0]


def _u32(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise DialogueFormatError(f"u32 read outside dialogue at 0x{offset:X}")
    return struct.unpack_from("<I", data, offset)[0]


def _byte_value(value: str, token: str) -> int:
    result = int(value, 16)
    if result < 0 or result > 0xFF:
        raise DialogueFormatError(f"{token} value is outside 00..FF")
    return result


def _decimal_byte(value: str, token: str) -> int:
    result = int(value, 10)
    if result < 0 or result > 0xFF:
        raise DialogueFormatError(f"{token} value is outside 0..255: {result}")
    return result


def decode_text(payload: bytes) -> str:
    """Convert one encoded block to deterministic, lossless token text."""

    output: list[str] = []
    position = 0
    while position < len(payload):
        value = payload[position]
        position += 1
        if value == 0x00:
            output.append("<Close>")
        elif value == 0x01:
            output.append("\n")
        elif value == 0x02:
            output.append("<New>")
        elif value == 0x03:
            output.append("<Wait>")
        elif value == 0x0F:
            if position + 2 > len(payload):
                raise DialogueFormatError("Truncated 0F control in dialogue block")
            operation = payload[position]
            argument = payload[position + 1]
            position += 2
            if operation == 0:
                output.append(f"<Delay:{argument}>")
            elif operation == 5:
                name = CHARACTER_NAMES.get(argument)
                output.append(f"<{name}>" if name else f"<Name:{argument}>")
            else:
                output.append(f"<Opcode:{operation:02X}:{argument:02X}>")
        elif value == 0xFE:
            if position >= len(payload):
                raise DialogueFormatError("Truncated FE control in dialogue block")
            output.append(f"<Extra1:{payload[position]:02X}>")
            position += 1
        elif value == 0xFF:
            if position >= len(payload):
                raise DialogueFormatError("Truncated FF control in dialogue block")
            output.append(f"<Extra2:{payload[position]:02X}>")
            position += 1
        elif value in PLAIN_DECODE:
            output.append(PLAIN_DECODE[value])
        else:
            output.append(f"<Byte:{value:02X}>")
    return "".join(output)


def _encode_token(token: str) -> bytes:
    if token == "Close":
        return b"\x00"
    if token == "New":
        return b"\x02"
    if token == "Wait":
        return b"\x03"
    if token in CHARACTER_IDS:
        return bytes((0x0F, 0x05, CHARACTER_IDS[token]))

    match = DELAY_TOKEN.fullmatch(token)
    if match:
        return bytes((0x0F, 0x00, _decimal_byte(match.group(1), "Delay")))
    match = NAME_TOKEN.fullmatch(token)
    if match:
        return bytes((0x0F, 0x05, _decimal_byte(match.group(1), "Name")))
    match = OPCODE_TOKEN.fullmatch(token)
    if match:
        return bytes(
            (
                0x0F,
                _byte_value(match.group(1), "Opcode"),
                _byte_value(match.group(2), "Opcode"),
            )
        )
    match = EXTRA1_TOKEN.fullmatch(token)
    if match:
        return bytes((0xFE, _byte_value(match.group(1), "Extra1")))
    match = EXTRA2_TOKEN.fullmatch(token)
    if match:
        return bytes((0xFF, _byte_value(match.group(1), "Extra2")))
    match = BYTE_TOKEN.fullmatch(token)
    if match:
        return bytes((_byte_value(match.group(1), "Byte"),))
    raise DialogueFormatError(f"Unsupported control token <{token}>")


def encode_text(text: str) -> bytes:
    """Encode deterministic token text and require a safe terminal Close."""

    if not isinstance(text, str):
        raise DialogueFormatError("Dialogue text must be a string")
    output = bytearray()
    position = 0
    while position < len(text):
        character = text[position]
        if character == "<":
            end = text.find(">", position + 1)
            if end == -1:
                raise DialogueFormatError(
                    f"Unterminated control token at text offset {position}"
                )
            output.extend(_encode_token(text[position + 1 : end]))
            position = end + 1
            continue
        if character == "\n":
            output.append(0x01)
        elif character in PLAIN_ENCODE:
            output.append(PLAIN_ENCODE[character])
        else:
            rendered = repr(character)
            raise DialogueFormatError(
                f"Unsupported character {rendered} at text offset {position}"
            )
        position += 1

    decoded = decode_text(bytes(output))
    if not decoded.endswith("<Close>"):
        raise DialogueFormatError("Every dialogue block must end with <Close>")
    first_close = decoded.find("<Close>")
    trailing = decoded[first_close:]
    while trailing.startswith("<Close>"):
        trailing = trailing[len("<Close>") :]
    if trailing:
        raise DialogueFormatError(
            "Only additional <Close> controls may follow the first <Close>"
        )

    # Generic byte tokens can express any value.  Verify that their result is
    # still a structurally decodable stream before accepting it.
    if encode_text_unchecked(decoded) != bytes(output):
        raise DialogueFormatError("Dialogue controls do not round-trip losslessly")
    return bytes(output)


def encode_text_unchecked(text: str) -> bytes:
    """Encode text without recursively applying terminal-structure checks."""

    output = bytearray()
    position = 0
    while position < len(text):
        character = text[position]
        if character == "<":
            end = text.find(">", position + 1)
            if end == -1:
                raise DialogueFormatError(
                    f"Unterminated control token at text offset {position}"
                )
            output.extend(_encode_token(text[position + 1 : end]))
            position = end + 1
            continue
        if character == "\n":
            output.append(0x01)
        elif character in PLAIN_ENCODE:
            output.append(PLAIN_ENCODE[character])
        else:
            raise DialogueFormatError(
                f"Unsupported character {character!r} at text offset {position}"
            )
        position += 1
    return bytes(output)


def _validate_terminal_close(payload: bytes, block_id: int) -> None:
    decoded = decode_text(payload)
    if not decoded.endswith("<Close>"):
        raise DialogueFormatError(f"Block {block_id} does not end with Close")
    first_close = decoded.find("<Close>")
    trailing = decoded[first_close:]
    while trailing.startswith("<Close>"):
        trailing = trailing[len("<Close>") :]
    if trailing:
        raise DialogueFormatError(
            f"Block {block_id} contains reachable data after its first Close"
        )


def parse_dialogue(data: bytes) -> ParsedDialogue:
    if len(data) < 8:
        raise DialogueFormatError("Dialogue component is too short")
    block_count = _u32(data, 0) + 1
    header_size = 4 + 4 * block_count
    if header_size > len(data):
        raise DialogueFormatError(
            f"Dialogue header for {block_count} blocks exceeds file size"
        )

    offsets = [_u16(data, 4 + 2 * index) for index in range(block_count)]
    if offsets[0] != header_size:
        raise DialogueFormatError(
            f"First block starts at 0x{offsets[0]:X}, expected 0x{header_size:X}"
        )
    if offsets != sorted(offsets) or len(set(offsets)) != len(offsets):
        raise DialogueFormatError("Dialogue block offsets are not strictly increasing")
    if offsets[-1] >= len(data):
        raise DialogueFormatError("Last dialogue block starts at or beyond file end")

    blocks: list[DialogueBlock] = []
    dimensions_offset = 4 + 2 * block_count
    for block_id, offset in enumerate(offsets):
        end = offsets[block_id + 1] if block_id + 1 < block_count else len(data)
        if end > len(data):
            raise DialogueFormatError(f"Block {block_id} ends beyond file size")
        payload = data[offset:end]
        _validate_terminal_close(payload, block_id)
        width = data[dimensions_offset + block_id * 2]
        height = data[dimensions_offset + block_id * 2 + 1]
        blocks.append(
            DialogueBlock(
                block_id=block_id,
                width=width,
                height=height,
                offset=offset,
                payload=payload,
                text=decode_text(payload),
            )
        )
    return ParsedDialogue(source=data, blocks=tuple(blocks))


def _integer_byte(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DialogueFormatError(f"{context} must be an integer")
    if value < 0 or value > 0xFF:
        raise DialogueFormatError(f"{context} is outside 0..255: {value}")
    return value


def _block_id(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DialogueFormatError(f"{context} must be a non-negative integer")
    return value


def encode_dialogue(blocks: Sequence[DialogueBlockSpec]) -> bytes:
    """Build an entire dialogue component from ordered, zero-based blocks."""

    if not blocks:
        raise DialogueFormatError("At least one dialogue block is required")
    expected_ids = list(range(len(blocks)))
    actual_ids = [
        _block_id(block.block_id, f"Block {index} ID")
        for index, block in enumerate(blocks)
    ]
    if actual_ids != expected_ids:
        raise DialogueFormatError(
            f"Dialogue block IDs must be exactly {expected_ids}; got {actual_ids}"
        )

    payloads: list[bytes] = []
    for block in blocks:
        _integer_byte(block.width, f"Block {block.block_id} width")
        _integer_byte(block.height, f"Block {block.block_id} height")
        payloads.append(encode_text(block.text))

    cursor = 4 + 4 * len(blocks)
    offsets: list[int] = []
    for block_id, payload in enumerate(payloads):
        if cursor > MAX_DIALOGUE_SIZE:
            raise DialogueFormatError(
                f"Block {block_id} offset exceeds the u16 limit: 0x{cursor:X}"
            )
        offsets.append(cursor)
        cursor += len(payload)
    if cursor > MAX_DIALOGUE_SIZE:
        raise DialogueFormatError(
            f"Dialogue section exceeds the u16 safety limit: {cursor} bytes"
        )

    output = bytearray(struct.pack("<I", len(blocks) - 1))
    for offset in offsets:
        output.extend(struct.pack("<H", offset))
    for block in blocks:
        output.extend(bytes((block.width, block.height)))
    for payload in payloads:
        output.extend(payload)

    result = bytes(output)
    reparsed = parse_dialogue(result)
    if [block.text for block in reparsed.blocks] != [block.text for block in blocks]:
        raise DialogueFormatError("Internal dialogue rebuild mismatch")
    return result


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dialogue_document(data: bytes) -> dict[str, Any]:
    parsed = parse_dialogue(data)
    return {
        "format": DIALOGUE_JSON_FORMAT,
        "source_size": len(data),
        "source_sha256": _sha256(data),
        "block_count": len(parsed.blocks),
        "blocks": [
            {
                "id": block.block_id,
                "width": block.width,
                "height": block.height,
                "text": block.text,
            }
            for block in parsed.blocks
        ],
    }


def replacements_document(data: bytes) -> dict[str, Any]:
    parsed = parse_dialogue(data)
    return {
        "format": REPLACEMENTS_JSON_FORMAT,
        "source_size": len(data),
        "source_sha256": _sha256(data),
        "block_count": len(parsed.blocks),
        "replacements": [
            {
                "id": block.block_id,
                "width": block.width,
                "height": block.height,
                "text": block.text,
            }
            for block in parsed.blocks
        ],
    }


def _mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise DialogueFormatError(f"{context} must be a JSON object")
    return value


def _array(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise DialogueFormatError(f"{context} must be a JSON array")
    return value


def _string(value: Any, context: str) -> str:
    if not isinstance(value, str):
        raise DialogueFormatError(f"{context} must be a string")
    return value


def _check_keys(
    value: Mapping[str, Any],
    allowed: set[str],
    required: set[str],
    context: str,
) -> None:
    missing = sorted(required - value.keys())
    unknown = sorted(value.keys() - allowed)
    if missing:
        raise DialogueFormatError(f"{context} is missing keys: {', '.join(missing)}")
    if unknown:
        raise DialogueFormatError(f"{context} has unknown keys: {', '.join(unknown)}")


def _verify_source(document: Mapping[str, Any], data: bytes, block_count: int) -> None:
    source_size = document.get("source_size")
    if isinstance(source_size, bool) or not isinstance(source_size, int):
        raise DialogueFormatError("source_size must be an integer")
    if source_size != len(data):
        raise DialogueFormatError(
            f"Template size is {len(data)}, but JSON expects {source_size}"
        )
    source_sha256 = _string(document.get("source_sha256"), "source_sha256").lower()
    if source_sha256 != _sha256(data):
        raise DialogueFormatError("Template SHA-256 does not match the JSON document")
    expected_count = document.get("block_count")
    if isinstance(expected_count, bool) or not isinstance(expected_count, int):
        raise DialogueFormatError("block_count must be an integer")
    if expected_count != block_count:
        raise DialogueFormatError(
            f"Template has {block_count} blocks, but JSON expects {expected_count}"
        )


def build_dialogue(data: bytes, document_value: Any) -> bytes:
    """Rebuild from a complete dump while preserving template IDs/count."""

    parsed = parse_dialogue(data)
    document = _mapping(document_value, "document")
    allowed = {
        "format",
        "source_size",
        "source_sha256",
        "block_count",
        "blocks",
    }
    _check_keys(document, allowed, allowed, "document")
    if document["format"] != DIALOGUE_JSON_FORMAT:
        raise DialogueFormatError(f"Unsupported dialogue JSON format: {document['format']}")
    _verify_source(document, data, len(parsed.blocks))
    values = _array(document["blocks"], "blocks")
    if len(values) != len(parsed.blocks):
        raise DialogueFormatError(
            f"Expected {len(parsed.blocks)} block entries, got {len(values)}"
        )

    specs: list[DialogueBlockSpec] = []
    for index, value in enumerate(values):
        block = _mapping(value, f"blocks[{index}]")
        block_keys = {"id", "width", "height", "text"}
        _check_keys(block, block_keys, block_keys, f"blocks[{index}]")
        specs.append(
            DialogueBlockSpec(
                block_id=_block_id(block["id"], f"blocks[{index}].id"),
                width=_integer_byte(block["width"], f"blocks[{index}].width"),
                height=_integer_byte(block["height"], f"blocks[{index}].height"),
                text=_string(block["text"], f"blocks[{index}].text"),
            )
        )
    return encode_dialogue(specs)


def replace_dialogue(data: bytes, document_value: Any) -> bytes:
    """Apply a partial or complete ID-keyed replacement document."""

    parsed = parse_dialogue(data)
    document = _mapping(document_value, "document")
    allowed = {
        "format",
        "source_size",
        "source_sha256",
        "block_count",
        "replacements",
    }
    _check_keys(document, allowed, allowed, "document")
    if document["format"] != REPLACEMENTS_JSON_FORMAT:
        raise DialogueFormatError(
            f"Unsupported replacement JSON format: {document['format']}"
        )
    _verify_source(document, data, len(parsed.blocks))
    values = _array(document["replacements"], "replacements")
    if not values:
        raise DialogueFormatError("Replacement document contains no replacements")

    specs = [
        DialogueBlockSpec(
            block_id=block.block_id,
            width=block.width,
            height=block.height,
            text=block.text,
        )
        for block in parsed.blocks
    ]
    seen: set[int] = set()
    for index, value in enumerate(values):
        replacement = _mapping(value, f"replacements[{index}]")
        allowed_block = {"id", "width", "height", "text"}
        required_block = {"id", "text"}
        _check_keys(
            replacement,
            allowed_block,
            required_block,
            f"replacements[{index}]",
        )
        block_id = _block_id(replacement["id"], f"replacements[{index}].id")
        if block_id >= len(specs):
            raise DialogueFormatError(
                f"Replacement block ID {block_id} is outside 0..{len(specs) - 1}"
            )
        if block_id in seen:
            raise DialogueFormatError(f"Duplicate replacement for block ID {block_id}")
        seen.add(block_id)
        original = specs[block_id]
        specs[block_id] = DialogueBlockSpec(
            block_id=block_id,
            width=(
                _integer_byte(
                    replacement["width"], f"replacements[{index}].width"
                )
                if "width" in replacement
                else original.width
            ),
            height=(
                _integer_byte(
                    replacement["height"], f"replacements[{index}].height"
                )
                if "height" in replacement
                else original.height
            ),
            text=_string(replacement["text"], f"replacements[{index}].text"),
        )
    return encode_dialogue(specs)


def rebuild_dialogue(data: bytes, document_value: Any) -> bytes:
    """Rebuild from either supported JSON format."""

    document = _mapping(document_value, "document")
    format_name = document.get("format")
    if format_name == DIALOGUE_JSON_FORMAT:
        return build_dialogue(data, document)
    if format_name == REPLACEMENTS_JSON_FORMAT:
        return replace_dialogue(data, document)
    raise DialogueFormatError(f"Unsupported dialogue JSON format: {format_name}")


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DialogueFormatError(f"Cannot parse JSON {path}: {exc}") from exc


def _write_checked(path: Path, data: bytes, force: bool) -> None:
    if path.exists() and not force:
        raise DialogueFormatError(f"Refusing to overwrite {path}; pass --force")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def command_inspect(args: argparse.Namespace) -> int:
    source = Path(args.dialogue)
    data = source.read_bytes()
    parsed = parse_dialogue(data)
    if args.json:
        sys.stdout.buffer.write(_json_bytes(dialogue_document(data)))
        return 0

    print(f"Dialogue: {source.resolve()}")
    print(f"Size: {len(data)} bytes; blocks: {len(parsed.blocks)}")
    print(" id  offset  bytes  width  height  text")
    for block in parsed.blocks:
        print(
            f"{block.block_id:3d}  0x{block.offset:04X}  {len(block.payload):5d}  "
            f"{block.width:5d}  {block.height:6d}  "
            f"{json.dumps(block.text, ensure_ascii=True)}"
        )
    return 0


def command_dump(args: argparse.Namespace) -> int:
    source = Path(args.dialogue).resolve()
    destination = Path(args.output).resolve()
    data = source.read_bytes()
    document = replacements_document(data) if args.replacements else dialogue_document(data)
    _write_checked(destination, _json_bytes(document), args.force)
    kind = "replacement template" if args.replacements else "complete dialogue"
    print(f"Dumped {kind}: {source} -> {destination}")
    return 0


def _rebuild(args: argparse.Namespace, replacement: bool | None) -> int:
    source = Path(args.dialogue).resolve()
    destination = Path(args.output).resolve()
    if source == destination:
        raise DialogueFormatError("Output must not overwrite the source dialogue")
    source_data = source.read_bytes()
    spec_path = Path(args.spec) if replacement is None else Path(args.json)
    document = _load_json(spec_path)
    if replacement is None:
        rebuilt = rebuild_dialogue(source_data, document)
    elif replacement:
        rebuilt = replace_dialogue(source_data, document)
    else:
        rebuilt = build_dialogue(source_data, document)
    _write_checked(destination, rebuilt, args.force)
    print(
        f"Rebuilt {len(parse_dialogue(rebuilt).blocks)} dialogue blocks: "
        f"{len(source_data)} -> {len(rebuilt)} bytes"
    )
    print(f"Wrote {destination}")
    return 0


def command_build(args: argparse.Namespace) -> int:
    return _rebuild(args, replacement=False)


def command_replace(args: argparse.Namespace) -> int:
    return _rebuild(args, replacement=True)


def command_rebuild(args: argparse.Namespace) -> int:
    return _rebuild(args, replacement=None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="show dialogue blocks")
    inspect_parser.add_argument("dialogue", type=Path)
    inspect_parser.add_argument("--json", action="store_true")
    inspect_parser.set_defaults(handler=command_inspect)

    dump_parser = subparsers.add_parser("dump", help="write deterministic JSON")
    dump_parser.add_argument("dialogue", type=Path)
    dump_parser.add_argument("output", type=Path)
    dump_parser.add_argument(
        "--replacements",
        action="store_true",
        help="emit an ID-keyed replacement template instead of a complete dump",
    )
    dump_parser.add_argument("--force", action="store_true")
    dump_parser.set_defaults(handler=command_dump)

    build_parser = subparsers.add_parser(
        "build", help="rebuild from a complete JSON dump"
    )
    build_parser.add_argument("dialogue", type=Path)
    build_parser.add_argument("json", type=Path)
    build_parser.add_argument("output", type=Path)
    build_parser.add_argument("--force", action="store_true")
    build_parser.set_defaults(handler=command_build)

    replace_parser = subparsers.add_parser(
        "replace", help="apply an ID-keyed replacement JSON document"
    )
    replace_parser.add_argument("dialogue", type=Path)
    replace_parser.add_argument("json", type=Path)
    replace_parser.add_argument("output", type=Path)
    replace_parser.add_argument("--force", action="store_true")
    replace_parser.set_defaults(handler=command_replace)

    rebuild_parser = subparsers.add_parser(
        "rebuild",
        help="rebuild from either JSON format (builder-friendly interface)",
    )
    rebuild_parser.add_argument("dialogue", type=Path, help="template component")
    rebuild_parser.add_argument("output", type=Path)
    rebuild_parser.add_argument("--spec", type=Path, required=True)
    rebuild_parser.add_argument("--force", action="store_true")
    rebuild_parser.set_defaults(handler=command_rebuild)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (DialogueFormatError, OSError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    sys.exit(main())
