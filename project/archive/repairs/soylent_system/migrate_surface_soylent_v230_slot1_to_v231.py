#!/usr/bin/env python3
"""Migrate the exact V230 field-592 patient-terminal Slot 1 to V231.

The pinned source is paused at field 592's Solaris terminal with dialogue ID
53 open on its final ``Close``.  V231 expands that terminal record from 110 to
203 encoded bytes, while the resident dialogue allocation has only 26 spare
bytes before the walkmesh.  Growing or shifting that allocation would corrupt
the already-loaded field.

The allocator-safe migration instead places V231's exact ID53 payload inside
retired retail dialogue ID45's 307-byte cavity, pads the remainder with Close
bytes, changes the resident terminal's sole dialogue operand from 53 to 45,
and retargets the active window's two source pointers to the relocated record.
Field 352's retail story routines were retired when this examination-room
foundation was built; the source script is pinned and proves ID45 has no live
entry point.  A cold field reload still obtains the ordinary V231 script and
dialogue from media, where the terminal continues to use authored ID53.

The archive table is rebuilt for V231 while preserving DuckStation's known
volatile final byte.  Component sizes, heap neighbours, Fei, party/GameState,
field variables, camera, actors, and every dialogue-window byte other than the
two guarded pointers remain unchanged.  The helper is fail-closed, emits only
a separate candidate, and never writes DuckStation's live Slot 1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
from typing import Protocol, Sequence


if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import tools.migrate_duckstation_disc_state as media_migration  # noqa: E402
import tools.migrate_surface_soylent_v229_slot1_to_v230 as previous  # noqa: E402
from tools.xgdeathblows import GAMESTATE_SIZE  # noqa: E402
from tools.xgdialog import parse_dialogue  # noqa: E402
from tools.xgdisc import DiscFormatError, Mode2Image  # noqa: E402
from tools.xgfield import FieldFormatError, ParsedField, parse_field  # noqa: E402
from tools.xgscript import AtelScript  # noqa: E402
from work.read_duckstation_runtime import (  # noqa: E402
    CAMERA_VECTORS,
    FIELD_ACTORS,
    FIELD_ACTOR_DATA_POINTER,
    FIELD_ACTOR_STRIDE,
    FIELD_CUR_SCRIPT_FILE,
    FIELD_NUM_ACTORS,
    FIELD_SCRIPT_MEMORY,
    FIELD_SCRIPT_VM_CUR_ACTOR,
    FIELD_SCRIPT_VM_CUR_SCRIPT_DATA,
    GAME_STATE,
    RAM_SIZE,
    _psx_ram_offset,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIVE_SLOT1 = (PROJECT_ROOT / "emulator_data" / "SLUS-00669_1.sav").resolve()
SOURCE_FIXTURE = (
    PROJECT_ROOT
    / "work"
    / "save_candidates"
    / "SLUS-00669_1_v230_patient_terminal_1eb8b434.sav"
).resolve()

SOURCE_STATE_SIZE = 1_845_278
SOURCE_STATE_SHA256 = "1eb8b43472bece86bb46a0e50120d3ea31baa5c19b11418eb2818ce00245e2f3"
SOURCE_PREFIX_SIZE = 37_263
SOURCE_PREFIX_SHA256 = "6d8db8ba202fdc9ea4e252e624ffbda7b98742dd9196ee4ebe13d4758a28da50"
SOURCE_COMPRESSED_SIZE = 1_808_015
SOURCE_COMPRESSED_SHA256 = "c8ff62d023b166d1e456ad4369914b7f31baa4925191401c105a29ae683bfa08"
SOURCE_PAYLOAD_SIZE = 3_819_109
SOURCE_PAYLOAD_SHA256 = "c7a3c3945d70eb7c70a730729c942d07fca3c91b8bea4f7428f82c2da236a348"
SOURCE_RAM_SHA256 = "73011bd8fb14ce32004221243dc5c6b51bf568c154b1225bb4ddd91e563ce271"

OUTPUT_STATE_SIZE = 1_670_155
OUTPUT_STATE_SHA256 = "b8fd8b566aed92e68133739ea2eb1911a7f6742c923e467e63cde2c6986a214f"
OUTPUT_PREFIX_SHA256 = "d6dec1d6a29e6e48c26963e9fafd4d9fc3866b49bdf167bcc612159ded6aa1fe"
OUTPUT_COMPRESSED_SIZE = 1_632_892
OUTPUT_COMPRESSED_SHA256 = "74a42b884ed1c37754bd5795639280f5b75ae067b399d41cc39e0f97437302df"
OUTPUT_PAYLOAD_SHA256 = "3fcb89198149dc128817755c8baed0144504154b0a3705e9c0e294f4f72ebd0c"
OUTPUT_RAM_SHA256 = "cd3fe349aebc937bd0dc251a251867fe9525051564c9cd5b510a942428642b00"

OLD_DISC_SIZE = 698_814_480
NEW_DISC_SIZE = 698_816_832
OLD_DISC_SHA256 = "140921144d691e81ed1d7f7340bef3c45a1753d18f5be9c81db5f8b0c7e1c79e"
NEW_DISC_SHA256 = "1f01094862fdb859787295f8babec12ad8d8a3122649b30a8ac01d84f84be3d2"
OLD_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v230.cue"
NEW_CUE_NAME = "Xenogears_PW_CD2_mass_driver_surface_soylent_v231.cue"
OLD_CUE_SIZE = NEW_CUE_SIZE = 112
OLD_CUE_SHA256 = "c3dc7220ce01a0f55457d8e2652f7c54a235adfa5baafdd10a18503a2bcfbf3a"
NEW_CUE_SHA256 = "3f7037d31b91d0e05360ed94d48d5a93c93839c9ac8ffa4bd0516533871e4f9b"

OLD_MANIFEST_SIZE = 129_959
OLD_MANIFEST_SHA256 = "9a8be0713439ad4c140ac0a8ab43f950555305e897fc087ff4aea204c16d9d07"
NEW_MANIFEST_SIZE = 131_663
NEW_MANIFEST_SHA256 = "3158359afe3ff059e3882de85a8e4aa3ebbc057bfc788affe120693934b17717"
CHANGED_RESOURCE_IDS = (1788, 1790, 1792, 1794)
CHANGED_RESOURCE_IDENTITIES = {
    1788: (
        (63_572, "c828843c6e56ca487ede86c46dec856b3df7fe6c1acefe4eb2101753e49dd858"),
        (63_680, "52ca81a59f421127a1352cace807aecc40177b1d36f7bbf367fb434e36b33b58"),
    ),
    1790: (
        (64_132, "3867af0fa734544016496619ce1fea4732754412e4b413a0730d30b36cda3e63"),
        (64_224, "e0c6785f2c1a3799ac96e66b4b8a713d3fe4ae1165506ed3adff15e89a609a5d"),
    ),
    1792: (
        (69_624, "82e05fe9ec3d662fd031a7749bd0a8728b54be281f3a47526a375ebd2455280a"),
        (69_716, "abbc49722ab4817f49012c37136b2ea3cafc52f98b1c33ccac09804202bf65ca"),
    ),
    1794: (
        (72_072, "d8c41033d516f9b1c0a6c965ef24302953bb5d524f523bb0e360e95202095bb7"),
        (72_156, "e6deba398bb2394a695af0f04dcc7401eb4f70b3aa7d4427165dfd419122ea31"),
    ),
}

FIELD592_CANONICAL_ID = 1790
OLD_FIELD_BUNDLE_SIZE, OLD_FIELD_BUNDLE_SHA256 = CHANGED_RESOURCE_IDENTITIES[
    FIELD592_CANONICAL_ID
][0]
NEW_FIELD_BUNDLE_SIZE, NEW_FIELD_BUNDLE_SHA256 = CHANGED_RESOURCE_IDENTITIES[
    FIELD592_CANONICAL_ID
][1]
OLD_HEADER_SIZE = NEW_HEADER_SIZE = 960
OLD_HEADER_SHA256 = "e4dd9f12bc976041a50a6529f9a6460f16cba4926441639b7017ac9fe7469ad6"
NEW_HEADER_SHA256 = "a3cd166f5a386231dfee62a5743a311853ee308fdea8a837dbc8e1692dd097f7"

ARCHIVE_TABLE_SIZE = 0x8000
OLD_ARCHIVE_TABLE_SHA256 = "1210942fd110cc83cd5090488f61605d51a521992909c8c4fa1298c912eaa1ec"
NEW_ARCHIVE_TABLE_SHA256 = "4238e60078de7c6442228ccfdc35b5d410d4eff6f496ddfba71a316c6d2ea1bf"
ARCHIVE_TABLE_DIFF_COUNT = 2_201
ARCHIVE_TABLE_DIFF_FIRST = 0x30C4
ARCHIVE_TABLE_DIFF_LAST = 0x7157
ARCHIVE_TABLE_DIFF_SHA256 = "a05335961d63f428819a9e19d8585da3f7eeb63db7f9d07c4b6518838af07fc0"
EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET = 0x11A66
EXPECTED_VOLATILE_TABLE_VALUE = 0xE0
SOURCE_RESIDENT_TABLE_SHA256 = "ad54b3917aaa84e84eabb8751a56df8a3311b708fc2da1fd690b4011068206c4"
OUTPUT_RESIDENT_TABLE_SHA256 = "bc09aa66f53ab89dab9f747132b324677dab93ff9c6c633a369b51733176f555"

OLD_SCRIPT_SIZE = NEW_SCRIPT_SIZE = RESIDENT_SCRIPT_SIZE = 3_455
OLD_SCRIPT_SHA256 = NEW_SCRIPT_SHA256 = (
    "e8f796b59e74805618fe6e69fb4a15afb975a0d2b10c1c0f1fafba2ce9ec5fc5"
)
OUTPUT_RESIDENT_SCRIPT_SHA256 = "fb23ca1e59a3f37f57e67a3a9b5a5db6758d3fb1ae1d9c6b6ef04e1b47164ee0"
EXPECTED_SCRIPT_PAYLOAD_OFFSET = 0x10CD56
SCRIPT_BYTECODE_OFFSET = 0x05C4
SCRIPT_BYTECODE_SIZE = 0x07BB
SCRIPT_ENTITY_COUNT = 21
SCRIPT_POINTER_TABLE_SHA256 = "0f59816acac9b06f466f941a044b7fefeb36a6367ea33ece63f05be716df632f"
SHARED_STOP_PC = 0x068C
TERMINAL_ENTITY = 19
TERMINAL_ACTION_PC = 0x06E0
TERMINAL_DIALOGUE_PC = 0x06F1
TERMINAL_WAIT_DIALOG_PC = 0x06F5
TERMINAL_DIALOGUE_INSTRUCTION = bytes.fromhex("F5 35 00 01 9C")
RELOCATED_TERMINAL_DIALOGUE_INSTRUCTION = bytes.fromhex("F5 2D 00 01 9C")
SCRIPT_DIALOGUE_OPERAND_OFFSET = SCRIPT_BYTECODE_OFFSET + TERMINAL_DIALOGUE_PC + 1
RETIRED_ID45_REFERENCE_PC = 0x05C2
RETIRED_ID45_REFERENCE = bytes.fromhex("D2 2D 00 00 9C")
RETIRED_RANGE = (0x019A, 0x066A)

OLD_DIALOGUE_SIZE = RESIDENT_DIALOGUE_SIZE = 5_458
NEW_DIALOGUE_SIZE = 5_551
OLD_DIALOGUE_SHA256 = "8011b0a809b9e55c963a3937612eca3e32961b65ea4562c41e915d2dbce8a96b"
NEW_DIALOGUE_SHA256 = "c774f221679530eca7b78cdcd0c0686cab9d281fc1048419c992c45de8cf1eb9"
OUTPUT_RESIDENT_DIALOGUE_SHA256 = "c2168bcf49feb8a2d529bad65d0173890ac006dc1e99f15641192690cfb964ca"
EXPECTED_DIALOGUE_PAYLOAD_OFFSET = 0x10DB06
DIALOGUE_COUNT = 56
SOURCE_TERMINAL_DIALOGUE_ID = 53
RELOCATION_DIALOGUE_ID = 45
RELOCATION_OFFSET = 0x0FDB
RELOCATION_CAPACITY = 307
RELOCATION_SOURCE_GRID = (54, 4)
RELOCATION_SOURCE_SHA256 = "8bcc838c08acff04b23700fd2108098b29f48fba3d1bfee25f539175a4b2dc56"
TARGET_TERMINAL_PAYLOAD_SIZE = 203
TARGET_TERMINAL_PAYLOAD_SHA256 = "4a56e0be4fe2622a3bb41d7ac8d52c7cadd2e7f80620dade25b90bc0c1eb028f"
TARGET_TERMINAL_GRID = (58, 4)
TARGET_TERMINAL_TEXT = (
    "PATIENT RECORD: N-592-07\n"
    "Type: cream-furred demihuman\n"
    "Pulse 68 bpm / BP 110/70\n"
    "Temp 36.9 C / Resp. 15/min<New>"
    "Joint inflammation: MODERATE\n"
    "Nanomachine uptake: 96%\n"
    "Pain response: IMPROVING\n"
    "Prognosis: STABLE.<Close>"
)
DIALOGUE_DIMENSIONS_OFFSET = 4 + 2 * DIALOGUE_COUNT
RELOCATION_WIDTH_OFFSET = DIALOGUE_DIMENSIONS_OFFSET + 2 * RELOCATION_DIALOGUE_ID
EXPECTED_WALKMESH_PAYLOAD_OFFSET = 0x10F072
WALKMESH_SIZE = 1_948
WALKMESH_SHA256 = "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d8cca4238393571df"
SCRIPT_GAP_SIZE = 49
SCRIPT_GAP_SHA256 = "090dbf8fdbbdc3609575a53e95833103a791a5c5705fe8b992a152c0feccd959"
DIALOGUE_GAP_SIZE = 26
DIALOGUE_GAP_SHA256 = "37ca65c785e04e29add5dc60ae24c4fc8203eb1c6d504097f05731c7c21eba21"

EXPECTED_RAM_PAYLOAD_OFFSET = 0x1A62
EXPECTED_FIELD = 592
GAME_SCENE_MAP = 0x04F34C
EXPECTED_GAME_SCENE_MAP = 0x0250
EXPECTED_ACTOR_COUNT = 35
EXPECTED_ACTOR_ARRAY_GUEST_POINTER = 0x80110714
EXPECTED_ACTOR_ARRAY_SHA256 = "0b55d4c748359e7eb4fb92b69f89d31fca76a2c8f0f8ecebc8c2c5af31aec6aa"
EXPECTED_SCRIPT_GUEST_POINTER = 0x8010B2F4
EXPECTED_VM_SCRIPT_GUEST_POINTER = 0x8010B8B8
EXPECTED_VM_ACTOR_GUEST_POINTER = 0x80113694
FIELD_CUR_DIALOGUE_FILE = 0x0ADBF0
FIELD_SMALL_COMPONENT = 0x0ADBF4
EXPECTED_DIALOGUE_GUEST_POINTER = 0x8010C0A4
EXPECTED_SMALL_COMPONENT_POINTER = 0x8010C08C

ACTOR_DATA_SIZE = 0x138
ACTOR_SCRIPT_SLOT_OFFSET = 0x8C
ACTOR_CURRENT_PC_OFFSET = 0xCC
EXPECTED_TERMINAL_ACTOR_DATA = 0x1134DC
EXPECTED_SCHEDULER_ACTOR_DATA = 0x113694
EXPECTED_TERMINAL_SLOT0 = bytes.fromhex("F5 06 00 02 FF FF 0C 00")
EXPECTED_TERMINAL_CURRENT = bytes.fromhex("F5 06 00 00")
EXPECTED_SCHEDULER_SLOT0 = bytes.fromhex("67 07 00 FF FF FF 3C 00")
EXPECTED_SCHEDULER_CURRENT = bytes.fromhex("67 07 00 00")

DIALOG_WINDOWS = 0x0C2698
DIALOG_WINDOW_STRIDE = 0x498
DIALOG_WINDOWS_SIZE = 4 * DIALOG_WINDOW_STRIDE
DIALOG_WINDOW_STATUS_OFFSET = 0x40E
WINDOW0_START_POINTER_OFFSET = DIALOG_WINDOWS + 0xA8
WINDOW0_CURRENT_POINTER_OFFSET = DIALOG_WINDOWS + 0x34
SOURCE_WINDOW0_START_POINTER = 0x8010D4E9
SOURCE_WINDOW0_CURRENT_POINTER = 0x8010D556
OUTPUT_WINDOW0_START_POINTER = EXPECTED_DIALOGUE_GUEST_POINTER + RELOCATION_OFFSET
OUTPUT_WINDOW0_CURRENT_POINTER = (
    OUTPUT_WINDOW0_START_POINTER + TARGET_TERMINAL_PAYLOAD_SIZE - 1
)
SOURCE_DIALOG_WINDOWS_SHA256 = "cca69dcacb91bbeb69073fcfeee7548723554b039115f69d5493b9af01fc0ca8"
OUTPUT_DIALOG_WINDOWS_SHA256 = "c0252a0a43080ba703b5947858e7d6eb21e2f198b762e5af54f47628f1deefc5"

FIELD_VARIABLE_BANK_SIZE = 0x400
FIELD_VARIABLE_BACKUP_OFFSET = 0x1930
EXPECTED_FIELD_VARIABLE_BANK_SHA256 = "5941238f27d52f504626034e7d5455fdc763da008ff5c8a410c2edd9441a0f93"
EXPECTED_GAMESTATE_SHA256 = "524988d27537bb8a2546a7d2aa5a9b93a8b15d7d2df2743497ab261ed2e5156c"
EXPECTED_CAMERA_SHA256 = "402479a89b0c35b1a8bc2552837eb4ea03e17fe5dadb6e0ac2a2a482796f6979"

EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED = ARCHIVE_TABLE_DIFF_COUNT
EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED = 1
EXPECTED_RESIDENT_DIALOGUE_BYTES_CHANGED = 299
EXPECTED_DIALOG_WINDOW_BYTES_CHANGED = 4
EXPECTED_PAYLOAD_BYTES_CHANGED = 2_505
EXPECTED_PREFIX_BYTES_CHANGED = 4


class _ZstdLike(Protocol):
    def frame_size(self, frame: bytes) -> int: ...
    def decompress(self, frame: bytes) -> bytes: ...
    def compress(self, payload: bytes) -> bytes: ...


SurfaceSlotMigrationError = previous.SurfaceSlotMigrationError


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _diff_offsets(before: bytes, after: bytes) -> tuple[int, ...]:
    return previous._diff_offsets(before, after)


def _diff_triplets(before: bytes, after: bytes) -> tuple[tuple[int, int, int], ...]:
    return previous._diff_triplets(before, after)


def _triplet_digest(diffs: Sequence[tuple[int, int, int]]) -> str:
    payload = b"".join(
        struct.pack("<IBB", offset, old, new) for offset, old, new in diffs
    )
    return _sha256(payload)


def _unpack_state(state: bytes, zstd: _ZstdLike) -> tuple[bytes, int, bytes]:
    return previous._unpack_state(state, zstd)


def _pack_state(prefix: bytes, payload: bytes, zstd: _ZstdLike) -> bytes:
    return previous._pack_state(prefix, payload, zstd)


def _ram_from_payload(payload: bytes) -> tuple[int, bytes]:
    try:
        offset = _psx_ram_offset(payload)
    except SystemExit as exc:
        raise SurfaceSlotMigrationError(str(exc)) from exc
    if offset != EXPECTED_RAM_PAYLOAD_OFFSET:
        raise SurfaceSlotMigrationError("Serialized RAM payload offset drifted")
    ram = payload[offset : offset + RAM_SIZE]
    if len(ram) != RAM_SIZE:
        raise SurfaceSlotMigrationError("Serialized PSX RAM is incomplete")
    return offset, ram


def _camera_snapshot(ram: bytes) -> bytes:
    return b"".join(ram[address : address + 16] for address in CAMERA_VECTORS.values())


def _validate_file(path: Path, size: int, sha256: str, label: str) -> None:
    if not path.is_file() or path.stat().st_size != size or _file_sha256(path) != sha256:
        raise SurfaceSlotMigrationError(f"{label} identity drifted")


def _expected_prefix(source_prefix: bytes, *, compressed_size: int) -> bytes:
    old_name = OLD_CUE_NAME.encode("ascii")
    new_name = NEW_CUE_NAME.encode("ascii")
    if (
        len(old_name) != len(new_name)
        or source_prefix.count(old_name) != 1
        or source_prefix.count(new_name)
    ):
        raise SurfaceSlotMigrationError("Pinned V230 media path changed")
    expected = bytearray(source_prefix.replace(old_name, new_name))
    struct.pack_into(
        "<I",
        expected,
        media_migration.DUCKSTATION_DATA_COMPRESSED_SIZE_OFFSET,
        compressed_size,
    )
    return bytes(expected)


def _manifest_inventory(
    blob: bytes,
    *,
    size: int,
    sha256: str,
    label: str,
) -> dict[int, tuple[int, str]]:
    if (len(blob), _sha256(blob)) != (size, sha256):
        raise SurfaceSlotMigrationError(f"{label} identity drifted")
    try:
        return {
            int(item["canonical_id"]): (int(item["size"]), str(item["sha256"]))
            for item in json.loads(blob)["replacement_inventory"]
        }
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise SurfaceSlotMigrationError(f"{label} structure drifted") from exc


def _disc_resource(
    image: Mode2Image,
    canonical_id: int,
    size: int,
    sha256: str,
    label: str,
) -> bytes:
    entries = image.read_index()
    index = canonical_id - 5
    if index >= len(entries) or entries[index].canonical_disc2_index != canonical_id:
        raise SurfaceSlotMigrationError(f"{label} FAT mapping drifted")
    data = image.extract_entry(entries[index])
    if (len(data), _sha256(data)) != (size, sha256):
        raise SurfaceSlotMigrationError(f"{label} identity drifted")
    return data


def _disc_field592(
    disc: Path,
    *,
    size: int,
    sha256: str,
    label: str,
) -> ParsedField:
    try:
        bundle = _disc_resource(
            Mode2Image(disc), FIELD592_CANONICAL_ID, size, sha256, label
        )
        parsed = parse_field(bundle)
    except (DiscFormatError, FieldFormatError) as exc:
        raise SurfaceSlotMigrationError(f"Cannot decode {label}: {exc}") from exc
    if len(parsed.parts) != 9:
        raise SurfaceSlotMigrationError(f"{label} component layout drifted")
    return parsed


def _script_pointer_digest(editor: AtelScript) -> str:
    return _sha256(
        b"".join(
            struct.pack("<H", editor.get_script_pointer(entity, slot))
            for entity in range(editor.entity_count)
            for slot in range(32)
        )
    )


def _validate_id45_retirement(editor: AtelScript) -> None:
    bytecode = editor.bytecode
    pointers = tuple(
        editor.get_script_pointer(entity, slot)
        for entity in range(editor.entity_count)
        for slot in range(32)
    )
    retired_start, retired_end = RETIRED_RANGE
    direct_retired_entries = tuple(
        pointer for pointer in pointers if retired_start <= pointer < retired_end
    )
    if (
        _script_pointer_digest(editor) != SCRIPT_POINTER_TABLE_SHA256
        or direct_retired_entries
        or bytecode.find(RETIRED_ID45_REFERENCE) != RETIRED_ID45_REFERENCE_PC
        or bytecode.count(RETIRED_ID45_REFERENCE) != 1
        or bytecode.count(bytes.fromhex("F5 2D 00")) != 0
        or bytecode.find(TERMINAL_DIALOGUE_INSTRUCTION) != TERMINAL_DIALOGUE_PC
        or bytecode.count(TERMINAL_DIALOGUE_INSTRUCTION) != 1
        or editor.get_script_pointer(TERMINAL_ENTITY, 2) != TERMINAL_ACTION_PC
    ):
        raise SurfaceSlotMigrationError("Retired ID45 cavity reachability drifted")


def _build_resident_script(old_script: bytes, new_script: bytes) -> bytes:
    if old_script != new_script:
        raise SurfaceSlotMigrationError("V231 unexpectedly changes field-592 ATEL")
    for blob, sha256, label in (
        (old_script, OLD_SCRIPT_SHA256, "V230 field-592 script"),
        (new_script, NEW_SCRIPT_SHA256, "V231 field-592 script"),
    ):
        if (len(blob), _sha256(blob)) != (OLD_SCRIPT_SIZE, sha256):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    editor = AtelScript(old_script)
    if (
        editor.entity_count != SCRIPT_ENTITY_COUNT
        or (editor.bytecode_offset, editor.bytecode_size)
        != (SCRIPT_BYTECODE_OFFSET, SCRIPT_BYTECODE_SIZE)
    ):
        raise SurfaceSlotMigrationError("Field-592 ATEL topology drifted")
    _validate_id45_retirement(editor)
    if old_script[
        SCRIPT_BYTECODE_OFFSET + TERMINAL_DIALOGUE_PC :
        SCRIPT_BYTECODE_OFFSET + TERMINAL_DIALOGUE_PC + len(TERMINAL_DIALOGUE_INSTRUCTION)
    ] != TERMINAL_DIALOGUE_INSTRUCTION:
        raise SurfaceSlotMigrationError("Terminal ID53 operand moved")

    resident = bytearray(old_script)
    if resident[SCRIPT_DIALOGUE_OPERAND_OFFSET] != SOURCE_TERMINAL_DIALOGUE_ID:
        raise SurfaceSlotMigrationError("Resident terminal dialogue operand drifted")
    resident[SCRIPT_DIALOGUE_OPERAND_OFFSET] = RELOCATION_DIALOGUE_ID
    result = bytes(resident)
    migrated = AtelScript(result)
    if (
        (len(result), _sha256(result))
        != (RESIDENT_SCRIPT_SIZE, OUTPUT_RESIDENT_SCRIPT_SHA256)
        or _diff_offsets(old_script, result) != (SCRIPT_DIALOGUE_OPERAND_OFFSET,)
        or _script_pointer_digest(migrated) != SCRIPT_POINTER_TABLE_SHA256
        or migrated.bytecode[
            TERMINAL_DIALOGUE_PC :
            TERMINAL_DIALOGUE_PC + len(RELOCATED_TERMINAL_DIALOGUE_INSTRUCTION)
        ] != RELOCATED_TERMINAL_DIALOGUE_INSTRUCTION
        or migrated.bytecode.count(RELOCATED_TERMINAL_DIALOGUE_INSTRUCTION) != 1
        or migrated.bytecode.find(RETIRED_ID45_REFERENCE) != RETIRED_ID45_REFERENCE_PC
    ):
        raise SurfaceSlotMigrationError("Allocator-safe resident script drifted")
    return result


def _build_resident_dialogue(old_dialogue: bytes, new_dialogue: bytes) -> bytes:
    for blob, size, sha256, label in (
        (old_dialogue, OLD_DIALOGUE_SIZE, OLD_DIALOGUE_SHA256, "V230 field-592 dialogue"),
        (new_dialogue, NEW_DIALOGUE_SIZE, NEW_DIALOGUE_SHA256, "V231 field-592 dialogue"),
    ):
        if (len(blob), _sha256(blob)) != (size, sha256):
            raise SurfaceSlotMigrationError(f"{label} identity drifted")
    old, new = parse_dialogue(old_dialogue), parse_dialogue(new_dialogue)
    if len(old.blocks) != DIALOGUE_COUNT or len(new.blocks) != DIALOGUE_COUNT:
        raise SurfaceSlotMigrationError("Field-592 dialogue count drifted")
    for dialogue_id, (before, after) in enumerate(zip(old.blocks, new.blocks, strict=True)):
        if dialogue_id == SOURCE_TERMINAL_DIALOGUE_ID:
            continue
        if (before.width, before.height, before.payload) != (
            after.width,
            after.height,
            after.payload,
        ):
            raise SurfaceSlotMigrationError(
                f"V231 changes unrelated field-592 dialogue ID{dialogue_id}"
            )
    target = new.blocks[SOURCE_TERMINAL_DIALOGUE_ID]
    cavity = old.blocks[RELOCATION_DIALOGUE_ID]
    if (
        (target.width, target.height) != TARGET_TERMINAL_GRID
        or target.text != TARGET_TERMINAL_TEXT
        or (len(target.payload), _sha256(target.payload))
        != (TARGET_TERMINAL_PAYLOAD_SIZE, TARGET_TERMINAL_PAYLOAD_SHA256)
        or (cavity.offset, len(cavity.payload), cavity.width, cavity.height)
        != (RELOCATION_OFFSET, RELOCATION_CAPACITY, *RELOCATION_SOURCE_GRID)
        or _sha256(cavity.payload) != RELOCATION_SOURCE_SHA256
        or len(target.payload) > len(cavity.payload)
    ):
        raise SurfaceSlotMigrationError("ID45 relocation cavity/target drifted")

    resident = bytearray(old_dialogue)
    if resident[RELOCATION_WIDTH_OFFSET : RELOCATION_WIDTH_OFFSET + 2] != bytes(
        RELOCATION_SOURCE_GRID
    ):
        raise SurfaceSlotMigrationError("ID45 dialogue dimensions moved")
    resident[RELOCATION_WIDTH_OFFSET : RELOCATION_WIDTH_OFFSET + 2] = bytes(
        TARGET_TERMINAL_GRID
    )
    resident[RELOCATION_OFFSET : RELOCATION_OFFSET + RELOCATION_CAPACITY] = (
        target.payload
        + b"\x00" * (RELOCATION_CAPACITY - len(target.payload))
    )
    result = bytes(resident)
    migrated = parse_dialogue(result)
    relocated = migrated.blocks[RELOCATION_DIALOGUE_ID]
    expected_text = TARGET_TERMINAL_TEXT + "<Close>" * (
        RELOCATION_CAPACITY - TARGET_TERMINAL_PAYLOAD_SIZE
    )
    if (
        (len(result), _sha256(result))
        != (RESIDENT_DIALOGUE_SIZE, OUTPUT_RESIDENT_DIALOGUE_SHA256)
        or (relocated.offset, len(relocated.payload), relocated.width, relocated.height)
        != (RELOCATION_OFFSET, RELOCATION_CAPACITY, *TARGET_TERMINAL_GRID)
        or relocated.text != expected_text
        or migrated.blocks[SOURCE_TERMINAL_DIALOGUE_ID] != old.blocks[
            SOURCE_TERMINAL_DIALOGUE_ID
        ]
        or len(_diff_offsets(old_dialogue, result))
        != EXPECTED_RESIDENT_DIALOGUE_BYTES_CHANGED
    ):
        raise SurfaceSlotMigrationError("Allocator-safe resident dialogue drifted")
    return result


def _validate_media(
    old_disc: Path,
    new_disc: Path,
    old_manifest: bytes,
    new_manifest: bytes,
    old_script: bytes,
    new_script: bytes,
    old_dialogue: bytes,
    new_dialogue: bytes,
) -> tuple[bytes, bytes, bytes, bytes]:
    for path, size, sha256, label in (
        (old_disc, OLD_DISC_SIZE, OLD_DISC_SHA256, "V230 disc"),
        (new_disc, NEW_DISC_SIZE, NEW_DISC_SHA256, "V231 disc"),
        (old_disc.with_name(OLD_CUE_NAME), OLD_CUE_SIZE, OLD_CUE_SHA256, "V230 CUE"),
        (new_disc.with_name(NEW_CUE_NAME), NEW_CUE_SIZE, NEW_CUE_SHA256, "V231 CUE"),
    ):
        _validate_file(path, size, sha256, label)

    old_inventory = _manifest_inventory(
        old_manifest,
        size=OLD_MANIFEST_SIZE,
        sha256=OLD_MANIFEST_SHA256,
        label="V230 stage manifest",
    )
    new_inventory = _manifest_inventory(
        new_manifest,
        size=NEW_MANIFEST_SIZE,
        sha256=NEW_MANIFEST_SHA256,
        label="V231 stage manifest",
    )
    changed = tuple(
        resource_id
        for resource_id in sorted(set(old_inventory) | set(new_inventory))
        if old_inventory.get(resource_id) != new_inventory.get(resource_id)
    )
    if (
        set(old_inventory) != set(new_inventory)
        or changed != CHANGED_RESOURCE_IDS
        or any(
            (old_inventory[resource_id], new_inventory[resource_id])
            != CHANGED_RESOURCE_IDENTITIES[resource_id]
            for resource_id in CHANGED_RESOURCE_IDS
        )
    ):
        raise SurfaceSlotMigrationError("V230/V231 replacement inventory drifted")

    old_field = _disc_field592(
        old_disc,
        size=OLD_FIELD_BUNDLE_SIZE,
        sha256=OLD_FIELD_BUNDLE_SHA256,
        label="V230 field-592 bundle",
    )
    new_field = _disc_field592(
        new_disc,
        size=NEW_FIELD_BUNDLE_SIZE,
        sha256=NEW_FIELD_BUNDLE_SHA256,
        label="V231 field-592 bundle",
    )
    if (
        (len(old_field.header), _sha256(old_field.header))
        != (OLD_HEADER_SIZE, OLD_HEADER_SHA256)
        or (len(new_field.header), _sha256(new_field.header))
        != (NEW_HEADER_SIZE, NEW_HEADER_SHA256)
        or old_field.parts[5].data != old_script
        or new_field.parts[5].data != new_script
        or old_field.parts[7].data != old_dialogue
        or new_field.parts[7].data != new_dialogue
        or any(
            old_field.parts[index].data != new_field.parts[index].data
            for index in range(9)
            if index != 7
        )
    ):
        raise SurfaceSlotMigrationError("V230/V231 field-592 media delta drifted")

    resident_script = _build_resident_script(old_script, new_script)
    resident_dialogue = _build_resident_dialogue(old_dialogue, new_dialogue)
    old_table = media_migration._archive_table(old_disc)
    new_table = media_migration._archive_table(new_disc)
    table_diffs = _diff_triplets(old_table, new_table)
    if (
        _sha256(old_table) != OLD_ARCHIVE_TABLE_SHA256
        or _sha256(new_table) != NEW_ARCHIVE_TABLE_SHA256
        or len(table_diffs) != ARCHIVE_TABLE_DIFF_COUNT
        or table_diffs[0][0] != ARCHIVE_TABLE_DIFF_FIRST
        or table_diffs[-1][0] != ARCHIVE_TABLE_DIFF_LAST
        or _triplet_digest(table_diffs) != ARCHIVE_TABLE_DIFF_SHA256
    ):
        raise SurfaceSlotMigrationError("V230/V231 archive-table delta drifted")
    return old_table, new_table, resident_script, resident_dialogue


def _actor_snapshot(ram: bytes) -> tuple[bytes, tuple[tuple[int, bytes], ...]]:
    guest = struct.unpack_from("<I", ram, FIELD_ACTORS)[0]
    base = guest & 0x1FFFFFFF
    actor_array = bytes(
        ram[base : base + EXPECTED_ACTOR_COUNT * FIELD_ACTOR_STRIDE]
    )
    actors: list[tuple[int, bytes]] = []
    for entity in range(SCRIPT_ENTITY_COUNT):
        record = base + entity * FIELD_ACTOR_STRIDE
        data_offset = (
            struct.unpack_from("<I", ram, record + FIELD_ACTOR_DATA_POINTER)[0]
            & 0x1FFFFFFF
        )
        actors.append((data_offset, bytes(ram[data_offset : data_offset + ACTOR_DATA_SIZE])))
    return actor_array, tuple(actors)


def _validate_source(payload: bytes, old_table: bytes, old_script: bytes, old_dialogue: bytes) -> dict[str, object]:
    if (len(payload), _sha256(payload)) != (
        SOURCE_PAYLOAD_SIZE,
        SOURCE_PAYLOAD_SHA256,
    ):
        raise SurfaceSlotMigrationError("V230 decompressed payload identity drifted")
    ram_offset, ram = _ram_from_payload(payload)
    if _sha256(ram) != SOURCE_RAM_SHA256:
        raise SurfaceSlotMigrationError("V230 serialized RAM identity drifted")

    table_offset, volatile = media_migration._find_resident_archive_table(
        payload, old_table
    )
    resident_table = payload[table_offset : table_offset + ARCHIVE_TABLE_SIZE]
    script = payload[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET :
        EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE
    ]
    dialogue = payload[
        EXPECTED_DIALOGUE_PAYLOAD_OFFSET :
        EXPECTED_DIALOGUE_PAYLOAD_OFFSET + RESIDENT_DIALOGUE_SIZE
    ]
    walkmesh = payload[
        EXPECTED_WALKMESH_PAYLOAD_OFFSET :
        EXPECTED_WALKMESH_PAYLOAD_OFFSET + WALKMESH_SIZE
    ]
    if (
        table_offset != EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET
        or volatile != 1
        or resident_table != old_table[:-1] + bytes((EXPECTED_VOLATILE_TABLE_VALUE,))
        or _sha256(resident_table) != SOURCE_RESIDENT_TABLE_SHA256
        or script != old_script
        or payload.count(old_script) != 1
        or payload.find(old_script) != EXPECTED_SCRIPT_PAYLOAD_OFFSET
        or dialogue != old_dialogue
        or payload.count(old_dialogue) != 1
        or payload.find(old_dialogue) != EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        or (len(walkmesh), _sha256(walkmesh)) != (WALKMESH_SIZE, WALKMESH_SHA256)
        or _sha256(
            payload[
                EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE :
                EXPECTED_DIALOGUE_PAYLOAD_OFFSET
            ]
        ) != SCRIPT_GAP_SHA256
        or _sha256(
            payload[
                EXPECTED_DIALOGUE_PAYLOAD_OFFSET + RESIDENT_DIALOGUE_SIZE :
                EXPECTED_WALKMESH_PAYLOAD_OFFSET
            ]
        ) != DIALOGUE_GAP_SHA256
    ):
        raise SurfaceSlotMigrationError("Resident field-592 component/table/gap identity drifted")

    actor_array_guest = struct.unpack_from("<I", ram, FIELD_ACTORS)[0]
    if (
        struct.unpack_from("<I", ram, GAME_SCENE_MAP)[0] != EXPECTED_GAME_SCENE_MAP
        or struct.unpack_from("<I", ram, FIELD_NUM_ACTORS)[0] != EXPECTED_ACTOR_COUNT
        or actor_array_guest != EXPECTED_ACTOR_ARRAY_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_CUR_SCRIPT_FILE)[0]
        != EXPECTED_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_SCRIPT_DATA)[0]
        != EXPECTED_VM_SCRIPT_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SCRIPT_VM_CUR_ACTOR)[0]
        != EXPECTED_VM_ACTOR_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_CUR_DIALOGUE_FILE)[0]
        != EXPECTED_DIALOGUE_GUEST_POINTER
        or struct.unpack_from("<I", ram, FIELD_SMALL_COMPONENT)[0]
        != EXPECTED_SMALL_COMPONENT_POINTER
    ):
        raise SurfaceSlotMigrationError("Live field-592 pointer topology drifted")

    terminal = EXPECTED_TERMINAL_ACTOR_DATA
    scheduler = EXPECTED_SCHEDULER_ACTOR_DATA
    if (
        ram[terminal + ACTOR_SCRIPT_SLOT_OFFSET : terminal + ACTOR_SCRIPT_SLOT_OFFSET + 8]
        != EXPECTED_TERMINAL_SLOT0
        or ram[terminal + ACTOR_CURRENT_PC_OFFSET : terminal + ACTOR_CURRENT_PC_OFFSET + 4]
        != EXPECTED_TERMINAL_CURRENT
        or ram[scheduler + ACTOR_SCRIPT_SLOT_OFFSET : scheduler + ACTOR_SCRIPT_SLOT_OFFSET + 8]
        != EXPECTED_SCHEDULER_SLOT0
        or ram[scheduler + ACTOR_CURRENT_PC_OFFSET : scheduler + ACTOR_CURRENT_PC_OFFSET + 4]
        != EXPECTED_SCHEDULER_CURRENT
    ):
        raise SurfaceSlotMigrationError("Active terminal/scheduler runtime drifted")

    windows = bytes(ram[DIALOG_WINDOWS : DIALOG_WINDOWS + DIALOG_WINDOWS_SIZE])
    if (
        _sha256(windows) != SOURCE_DIALOG_WINDOWS_SHA256
        or struct.unpack_from("<h", ram, DIALOG_WINDOWS + DIALOG_WINDOW_STATUS_OFFSET)[0] != 0
        or any(
            struct.unpack_from(
                "<h",
                ram,
                DIALOG_WINDOWS
                + index * DIALOG_WINDOW_STRIDE
                + DIALOG_WINDOW_STATUS_OFFSET,
            )[0]
            != -1
            for index in range(1, 4)
        )
        or struct.unpack_from("<I", ram, WINDOW0_START_POINTER_OFFSET)[0]
        != SOURCE_WINDOW0_START_POINTER
        or struct.unpack_from("<I", ram, WINDOW0_CURRENT_POINTER_OFFSET)[0]
        != SOURCE_WINDOW0_CURRENT_POINTER
    ):
        raise SurfaceSlotMigrationError("Active ID53 dialogue-window state drifted")

    gamestate = bytes(ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE])
    field_bank = bytes(
        ram[FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE]
    )
    backup_bank = bytes(
        ram[
            GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET :
            GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET + FIELD_VARIABLE_BANK_SIZE
        ]
    )
    camera = _camera_snapshot(ram)
    actor_array, actors = _actor_snapshot(ram)
    if (
        _sha256(gamestate) != EXPECTED_GAMESTATE_SHA256
        or _sha256(field_bank) != EXPECTED_FIELD_VARIABLE_BANK_SHA256
        or backup_bank != field_bank
        or _sha256(camera) != EXPECTED_CAMERA_SHA256
        or _sha256(actor_array) != EXPECTED_ACTOR_ARRAY_SHA256
        or actors[TERMINAL_ENTITY][0] != EXPECTED_TERMINAL_ACTOR_DATA
        or actors[20][0] != EXPECTED_SCHEDULER_ACTOR_DATA
    ):
        raise SurfaceSlotMigrationError("Gameplay/runtime preservation source drifted")
    return {
        "ram_offset": ram_offset,
        "ram": ram,
        "table": resident_table,
        "script": script,
        "dialogue": dialogue,
        "walkmesh": walkmesh,
        "windows": windows,
        "gamestate": gamestate,
        "field_bank": field_bank,
        "backup_bank": backup_bank,
        "camera": camera,
        "actor_array": actor_array,
        "actors": actors,
    }


def _rebuild_resident_table(source_table: bytes, new_table: bytes) -> bytes:
    if (
        len(source_table) != ARCHIVE_TABLE_SIZE
        or len(new_table) != ARCHIVE_TABLE_SIZE
        or source_table[-1] != EXPECTED_VOLATILE_TABLE_VALUE
        or new_table[-1] != 0
    ):
        raise SurfaceSlotMigrationError("Resident archive-table source drifted")
    result = new_table[:-1] + bytes((EXPECTED_VOLATILE_TABLE_VALUE,))
    if (
        _sha256(result) != OUTPUT_RESIDENT_TABLE_SHA256
        or _diff_triplets(result, new_table)
        != ((ARCHIVE_TABLE_SIZE - 1, EXPECTED_VOLATILE_TABLE_VALUE, 0),)
    ):
        raise SurfaceSlotMigrationError("V231 resident archive-table reconstruction drifted")
    return result


def migrate_v230_slot1_to_v231(
    state: bytes,
    *,
    old_disc: Path,
    new_disc: Path,
    old_manifest: bytes,
    new_manifest: bytes,
    old_script: bytes,
    new_script: bytes,
    old_dialogue: bytes,
    new_dialogue: bytes,
    zstd: _ZstdLike,
) -> tuple[bytes, dict[str, object]]:
    """Return the exact separately writable V231 state candidate and report."""

    source_sha256 = _sha256(state)
    if (len(state), source_sha256) != (SOURCE_STATE_SIZE, SOURCE_STATE_SHA256):
        raise SurfaceSlotMigrationError(
            f"Source Slot 1 identity is {len(state)} / {source_sha256}, expected "
            f"{SOURCE_STATE_SIZE} / {SOURCE_STATE_SHA256}"
        )
    old_name = OLD_CUE_NAME.encode("ascii")
    new_name = NEW_CUE_NAME.encode("ascii")
    if (
        len(old_name) != len(new_name)
        or state.count(old_name) != 1
        or state.count(new_name)
    ):
        raise SurfaceSlotMigrationError("Source CUE identity drifted")

    old_table, new_table, resident_script, resident_dialogue = _validate_media(
        old_disc,
        new_disc,
        old_manifest,
        new_manifest,
        old_script,
        new_script,
        old_dialogue,
        new_dialogue,
    )
    source_payload, frame_start, source_prefix = _unpack_state(state, zstd)
    if (
        frame_start != SOURCE_PREFIX_SIZE
        or len(state) - frame_start != SOURCE_COMPRESSED_SIZE
        or _sha256(state[frame_start:]) != SOURCE_COMPRESSED_SHA256
        or _sha256(source_prefix) != SOURCE_PREFIX_SHA256
    ):
        raise SurfaceSlotMigrationError("Source frame/prefix identity drifted")
    snapshots = _validate_source(source_payload, old_table, old_script, old_dialogue)

    rebuilt_table = _rebuild_resident_table(snapshots["table"], new_table)
    final = bytearray(source_payload)
    final[
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
        EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
    ] = rebuilt_table
    final[
        EXPECTED_SCRIPT_PAYLOAD_OFFSET :
        EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE
    ] = resident_script
    final[
        EXPECTED_DIALOGUE_PAYLOAD_OFFSET :
        EXPECTED_DIALOGUE_PAYLOAD_OFFSET + RESIDENT_DIALOGUE_SIZE
    ] = resident_dialogue
    ram_offset = snapshots["ram_offset"]
    struct.pack_into(
        "<I",
        final,
        ram_offset + WINDOW0_START_POINTER_OFFSET,
        OUTPUT_WINDOW0_START_POINTER,
    )
    struct.pack_into(
        "<I",
        final,
        ram_offset + WINDOW0_CURRENT_POINTER_OFFSET,
        OUTPUT_WINDOW0_CURRENT_POINTER,
    )
    final_payload = bytes(final)

    table_diffs = _diff_offsets(snapshots["table"], rebuilt_table)
    script_diffs = _diff_offsets(snapshots["script"], resident_script)
    dialogue_diffs = _diff_offsets(snapshots["dialogue"], resident_dialogue)
    source_windows = snapshots["windows"]
    output_windows = final_payload[
        ram_offset + DIALOG_WINDOWS :
        ram_offset + DIALOG_WINDOWS + DIALOG_WINDOWS_SIZE
    ]
    window_diffs = _diff_offsets(source_windows, output_windows)
    expected_offsets = {
        *(
            EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + offset
            for offset in table_diffs
        ),
        *(EXPECTED_SCRIPT_PAYLOAD_OFFSET + offset for offset in script_diffs),
        *(EXPECTED_DIALOGUE_PAYLOAD_OFFSET + offset for offset in dialogue_diffs),
        *(ram_offset + DIALOG_WINDOWS + offset for offset in window_diffs),
    }
    actual_offsets = _diff_offsets(source_payload, final_payload)
    if (
        len(table_diffs) != EXPECTED_ARCHIVE_TABLE_BYTES_CHANGED
        or len(script_diffs) != EXPECTED_RESIDENT_SCRIPT_BYTES_CHANGED
        or len(dialogue_diffs) != EXPECTED_RESIDENT_DIALOGUE_BYTES_CHANGED
        or len(window_diffs) != EXPECTED_DIALOG_WINDOW_BYTES_CHANGED
        or actual_offsets != tuple(sorted(expected_offsets))
        or len(actual_offsets) != EXPECTED_PAYLOAD_BYTES_CHANGED
        or _sha256(final_payload) != OUTPUT_PAYLOAD_SHA256
    ):
        raise SurfaceSlotMigrationError(
            "Migration escaped the archive/ATEL/cavity/window whitelist"
        )

    if (
        final_payload[
            EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET :
            EXPECTED_ARCHIVE_TABLE_PAYLOAD_OFFSET + ARCHIVE_TABLE_SIZE
        ] != rebuilt_table
        or final_payload[
            EXPECTED_SCRIPT_PAYLOAD_OFFSET :
            EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE
        ] != resident_script
        or final_payload[
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET :
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET + RESIDENT_DIALOGUE_SIZE
        ] != resident_dialogue
        or final_payload[
            EXPECTED_WALKMESH_PAYLOAD_OFFSET :
            EXPECTED_WALKMESH_PAYLOAD_OFFSET + WALKMESH_SIZE
        ] != snapshots["walkmesh"]
        or final_payload[
            EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE :
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        ] != source_payload[
            EXPECTED_SCRIPT_PAYLOAD_OFFSET + RESIDENT_SCRIPT_SIZE :
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET
        ]
        or final_payload[
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET + RESIDENT_DIALOGUE_SIZE :
            EXPECTED_WALKMESH_PAYLOAD_OFFSET
        ] != source_payload[
            EXPECTED_DIALOGUE_PAYLOAD_OFFSET + RESIDENT_DIALOGUE_SIZE :
            EXPECTED_WALKMESH_PAYLOAD_OFFSET
        ]
    ):
        raise SurfaceSlotMigrationError("Resident component boundaries changed")

    result_ram_offset, result_ram = _ram_from_payload(final_payload)
    if result_ram_offset != ram_offset or _sha256(result_ram) != OUTPUT_RAM_SHA256:
        raise SurfaceSlotMigrationError("Final serialized RAM identity drifted")
    source_ram = snapshots["ram"]
    if (
        result_ram[GAME_STATE : GAME_STATE + GAMESTATE_SIZE] != snapshots["gamestate"]
        or result_ram[
            FIELD_SCRIPT_MEMORY : FIELD_SCRIPT_MEMORY + FIELD_VARIABLE_BANK_SIZE
        ] != snapshots["field_bank"]
        or result_ram[
            GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET :
            GAME_STATE + FIELD_VARIABLE_BACKUP_OFFSET + FIELD_VARIABLE_BANK_SIZE
        ] != snapshots["backup_bank"]
        or _camera_snapshot(result_ram) != snapshots["camera"]
    ):
        raise SurfaceSlotMigrationError("GameState/party/field/camera changed")
    actor_array, actors = _actor_snapshot(result_ram)
    if actor_array != snapshots["actor_array"] or actors != snapshots["actors"]:
        raise SurfaceSlotMigrationError("Field actor/runtime state changed")

    if (
        _sha256(output_windows) != OUTPUT_DIALOG_WINDOWS_SHA256
        or struct.unpack_from("<I", result_ram, WINDOW0_START_POINTER_OFFSET)[0]
        != OUTPUT_WINDOW0_START_POINTER
        or struct.unpack_from("<I", result_ram, WINDOW0_CURRENT_POINTER_OFFSET)[0]
        != OUTPUT_WINDOW0_CURRENT_POINTER
        or struct.unpack_from(
            "<h", result_ram, DIALOG_WINDOWS + DIALOG_WINDOW_STATUS_OFFSET
        )[0] != 0
    ):
        raise SurfaceSlotMigrationError("Relocated active dialogue pointers drifted")
    dialogue_base = EXPECTED_DIALOGUE_GUEST_POINTER & 0x1FFFFFFF
    relocated_start = (OUTPUT_WINDOW0_START_POINTER & 0x1FFFFFFF) - dialogue_base
    relocated_current = (
        (OUTPUT_WINDOW0_CURRENT_POINTER & 0x1FFFFFFF) - dialogue_base
    )
    new_target = parse_dialogue(new_dialogue).blocks[SOURCE_TERMINAL_DIALOGUE_ID]
    if (
        relocated_start != RELOCATION_OFFSET
        or relocated_current
        != RELOCATION_OFFSET + TARGET_TERMINAL_PAYLOAD_SIZE - 1
        or resident_dialogue[
            relocated_start : relocated_start + TARGET_TERMINAL_PAYLOAD_SIZE
        ] != new_target.payload
        or resident_dialogue[relocated_current] != 0
        or result_ram[
            EXPECTED_TERMINAL_ACTOR_DATA :
            EXPECTED_TERMINAL_ACTOR_DATA + ACTOR_DATA_SIZE
        ] != source_ram[
            EXPECTED_TERMINAL_ACTOR_DATA :
            EXPECTED_TERMINAL_ACTOR_DATA + ACTOR_DATA_SIZE
        ]
    ):
        raise SurfaceSlotMigrationError("Relocated terminal record runtime contract drifted")

    provisional_prefix = _expected_prefix(
        source_prefix,
        compressed_size=OUTPUT_COMPRESSED_SIZE,
    )
    if (
        len(_diff_offsets(source_prefix, provisional_prefix))
        != EXPECTED_PREFIX_BYTES_CHANGED
        or _sha256(provisional_prefix) != OUTPUT_PREFIX_SHA256
    ):
        raise SurfaceSlotMigrationError("V231 media-prefix reconstruction drifted")
    result = _pack_state(provisional_prefix, final_payload, zstd)
    verified_payload, verified_frame, verified_prefix = _unpack_state(result, zstd)
    if (
        verified_payload != final_payload
        or verified_frame != SOURCE_PREFIX_SIZE
        or verified_prefix != provisional_prefix
        or len(result) - verified_frame != OUTPUT_COMPRESSED_SIZE
        or _sha256(result[verified_frame:]) != OUTPUT_COMPRESSED_SHA256
        or result.count(old_name) != 0
        or result.count(new_name) != 1
        or (len(result), _sha256(result))
        != (OUTPUT_STATE_SIZE, OUTPUT_STATE_SHA256)
    ):
        raise SurfaceSlotMigrationError("Final V231 state identity or round trip drifted")

    report: dict[str, object] = {
        "source_sha256": SOURCE_STATE_SHA256,
        "output_sha256": OUTPUT_STATE_SHA256,
        "source_size": len(state),
        "output_size": len(result),
        "field": EXPECTED_FIELD,
        "payload_size": len(final_payload),
        "payload_sha256": OUTPUT_PAYLOAD_SHA256,
        "ram_sha256": OUTPUT_RAM_SHA256,
        "compressed_payload_size": OUTPUT_COMPRESSED_SIZE,
        "compressed_payload_sha256": OUTPUT_COMPRESSED_SHA256,
        "payload_bytes_changed": len(actual_offsets),
        "archive_table_bytes_changed": len(table_diffs),
        "resident_script_bytes_changed": len(script_diffs),
        "resident_dialogue_bytes_changed": len(dialogue_diffs),
        "dialogue_window_bytes_changed": len(window_diffs),
        "resident_archive_table_sha256": OUTPUT_RESIDENT_TABLE_SHA256,
        "resident_script_sha256": OUTPUT_RESIDENT_SCRIPT_SHA256,
        "resident_dialogue_sha256": OUTPUT_RESIDENT_DIALOGUE_SHA256,
        "relocated_dialogue_id": RELOCATION_DIALOGUE_ID,
        "relocated_dialogue_offset": f"0x{RELOCATION_OFFSET:X}",
        "relocated_dialogue_capacity": RELOCATION_CAPACITY,
        "authored_record_bytes": TARGET_TERMINAL_PAYLOAD_SIZE,
        "active_window_start_before": f"0x{SOURCE_WINDOW0_START_POINTER:08X}",
        "active_window_start_after": f"0x{OUTPUT_WINDOW0_START_POINTER:08X}",
        "active_window_current_before": f"0x{SOURCE_WINDOW0_CURRENT_POINTER:08X}",
        "active_window_current_after": f"0x{OUTPUT_WINDOW0_CURRENT_POINTER:08X}",
        "retired_id45_cavity_proven": True,
        "resident_terminal_remapped_to_id45": True,
        "cold_reload_uses_v231_id53": True,
        "resident_component_sizes_preserved": True,
        "heap_neighbors_preserved": True,
        "fei_party_gamestate_field_camera_preserved": True,
        "actor_runtime_preserved": True,
        "dialogue_window_state_preserved_except_source_pointers": True,
        "resident_archive_volatile_tail_preserved": True,
        "allocator_safe": True,
        "round_trip_verified": True,
        "changed_resource_ids": list(CHANGED_RESOURCE_IDS),
        "old_cue_name": OLD_CUE_NAME,
        "new_cue_name": NEW_CUE_NAME,
        "v230_manifest_sha256": OLD_MANIFEST_SHA256,
        "v231_manifest_sha256": NEW_MANIFEST_SHA256,
        "v230_disc_sha256": OLD_DISC_SHA256,
        "v231_disc_sha256": NEW_DISC_SHA256,
    }
    return result, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=SOURCE_FIXTURE)
    parser.add_argument(
        "--old-disc",
        type=Path,
        default=PROJECT_ROOT / "output" / OLD_CUE_NAME.replace(".cue", ".bin"),
    )
    parser.add_argument(
        "--new-disc",
        type=Path,
        default=PROJECT_ROOT / "output" / NEW_CUE_NAME.replace(".cue", ".bin"),
    )
    parser.add_argument(
        "--old-manifest",
        type=Path,
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v230_stage" / "manifest.json",
    )
    parser.add_argument(
        "--new-manifest",
        type=Path,
        default=PROJECT_ROOT / "work" / "surface_soylent_campaign_v231_stage" / "manifest.json",
    )
    parser.add_argument(
        "--old-script",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "surface_soylent_campaign_v230_stage"
            / "clones"
            / "field_592_disc1_donor"
            / "05_scripts.bin"
        ),
    )
    parser.add_argument(
        "--new-script",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "surface_soylent_campaign_v231_stage"
            / "clones"
            / "field_592_disc1_donor"
            / "05_scripts.bin"
        ),
    )
    parser.add_argument(
        "--old-dialogue",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "surface_soylent_campaign_v230_stage"
            / "clones"
            / "field_592_disc1_donor"
            / "07_dialogue.bin"
        ),
    )
    parser.add_argument(
        "--new-dialogue",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "surface_soylent_campaign_v231_stage"
            / "clones"
            / "field_592_disc1_donor"
            / "07_dialogue.bin"
        ),
    )
    parser.add_argument(
        "--zstd",
        type=Path,
        default=PROJECT_ROOT / "work" / "duckstation" / "zstd.dll",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "save_candidates"
            / "SLUS-00669_1_v231_from_1eb8b434_field592_patient_record.sav"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=(
            PROJECT_ROOT
            / "work"
            / "save_candidates"
            / "SLUS-00669_1_v231_from_1eb8b434_field592_patient_record.json"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        source_path = args.source.resolve()
        output = args.output.resolve()
        report_path = args.report.resolve()
        if output == LIVE_SLOT1 or report_path == LIVE_SLOT1:
            raise SurfaceSlotMigrationError("Output/report may not be the live Slot 1")
        if output == source_path or report_path == source_path:
            raise SurfaceSlotMigrationError("Output/report may not replace the source state")
        if output == report_path:
            raise SurfaceSlotMigrationError("Output and report paths must be distinct")
        result, report = migrate_v230_slot1_to_v231(
            source_path.read_bytes(),
            old_disc=args.old_disc,
            new_disc=args.new_disc,
            old_manifest=args.old_manifest.read_bytes(),
            new_manifest=args.new_manifest.read_bytes(),
            old_script=args.old_script.read_bytes(),
            new_script=args.new_script.read_bytes(),
            old_dialogue=args.old_dialogue.read_bytes(),
            new_dialogue=args.new_dialogue.read_bytes(),
            zstd=media_migration._Zstd(args.zstd),
        )
        if output.exists() and output.read_bytes() != result:
            raise SurfaceSlotMigrationError("Refusing to overwrite a different V231 candidate")
        if report_path.exists():
            try:
                existing_report = json.loads(report_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                raise SurfaceSlotMigrationError("Refusing to overwrite an unreadable report") from exc
            if existing_report != report:
                raise SurfaceSlotMigrationError("Refusing to overwrite a different V231 report")
        output.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if (
            output.read_bytes() != result
            or json.loads(report_path.read_text(encoding="utf-8")) != report
        ):
            raise SurfaceSlotMigrationError("Written V231 candidate/report failed verification")
    except (
        OSError,
        ValueError,
        SurfaceSlotMigrationError,
        media_migration.StateMigrationError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote V231 candidate: {output}")
    print(f"Wrote migration report: {report_path}")
    print(f"SHA-256: {report['output_sha256']}")
    print("The live Slot 1 was not modified. Install only after DuckStation is fully closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
