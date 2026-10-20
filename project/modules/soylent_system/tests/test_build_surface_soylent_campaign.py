from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT
from modules.soylent_system.tests.disc_fixtures import source_disc_path
from modules.soylent_system.tools import surface_soylent_final_guidance as final_guidance

from collections import deque
from dataclasses import replace
import hashlib
import json
import math
import re
import struct
import tempfile
import unittest
from pathlib import Path

import tools.build_surface_soylent_campaign as campaign
import tools.build_surface_soylent_dungeon as base
import tools.surface_soylent_campaign_blueprint as blueprint
import tools.surface_soylent_campaign_donor567 as reserved_donor567
import tools.surface_soylent_campaign_donor588 as donor588
import tools.surface_soylent_campaign_empty_clinic567 as empty_clinic567
import tools.surface_soylent_campaign_exam_rooms as exam_rooms
import tools.surface_soylent_campaign_stabilization590 as stabilization590
import tools.surface_soylent_campaign_title as campaign_title
import tools.xgdeathblows as deathblows
from tools.xgdialog import DialogueBlockSpec, encode_dialogue, parse_dialogue
from tools.xgdisc import (
    FIELD_DIRECTORY,
    FIRST_FIELD_LOCAL_FILE,
    Mode2Image,
    directory_file_fat_index,
)
from tools.xgfield import parse_field
from tools.xgencounter import EncounterTable
from tools.xgscript import AtelScript as ScriptEditor


PROJECT_ROOT = REPOSITORY_ROOT
SOURCE_DISC = source_disc_path("mass_driver_base")
DONOR_DISC = source_disc_path("pw_disc1")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _actor_records(header: bytes) -> tuple[bytes, ...]:
    count = struct.unpack_from("<H", header, 0x18C)[0]
    if len(header) != 0x190 + count * 16:
        raise AssertionError("header actor table does not end at its boundary")
    return tuple(
        header[0x190 + index * 16 : 0x190 + (index + 1) * 16]
        for index in range(count)
    )


def _indexed_entries(data: bytes) -> tuple[bytes, ...]:
    count = struct.unpack_from("<I", data)[0]
    offsets = struct.unpack_from(f"<{count}I", data, 4)
    ends = offsets[1:] + (len(data),)
    return tuple(data[start:end] for start, end in zip(offsets, ends, strict=True))


def _single_block_model_aabb(
    model: bytes,
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if len(model) < 0x48 or struct.unpack_from("<I", model)[0] != 1:
        raise AssertionError("door leaf is not the audited single-block model")
    block = 0x10
    vertex_count = struct.unpack_from("<H", model, block + 2)[0]
    vertex_offset = struct.unpack_from("<I", model, block + 8)[0]
    vertices = tuple(
        struct.unpack_from("<hhh", model, vertex_offset + index * 8)
        for index in range(vertex_count)
    )
    return tuple(
        (min(vertex[axis] for vertex in vertices), max(vertex[axis] for vertex in vertices))
        for axis in range(3)
    )


class IntakeExamDoorGeometryUnitTests(unittest.TestCase):
    """Exercise the Intake geometry surgery without preparing all 18 rooms."""

    @classmethod
    def setUpClass(cls) -> None:
        if not SOURCE_DISC.is_file():
            raise unittest.SkipTest("checked Surface campaign source disc is unavailable")
        image = Mode2Image(SOURCE_DISC)
        entries = image.read_index()
        first = image.read_directories()[FIELD_DIRECTORY].first_file
        local_file = FIRST_FIELD_LOCAL_FILE + 2 * 621
        fat_index = directory_file_fat_index(first, local_file)
        bundle = image.extract_entry(entries[fat_index])
        cls.native_models = parse_field(bundle).parts[2].data

    def test_wall_carve_and_camera_cleanup_are_deterministic(self) -> None:
        native_entries = _indexed_entries(self.native_models)
        rebuilt = campaign._install_intake_exam_room_geometry(
            self.native_models
        )
        entries = _indexed_entries(rebuilt)
        self.assertEqual(
            (len(rebuilt), _sha256(rebuilt)),
            (
                39_292,
                "b06e38c58fcd5e1ce5033e1135f0ae7c7d745b9ef37575f44b0cba4c936c52aa",
            ),
        )
        self.assertEqual(len(entries), 21)
        self.assertTrue(
            all(
                entries[index] == native
                for index, native in enumerate(native_entries)
                if index
                not in (
                    campaign.INTAKE_EXAM_ROOM_WALL_MODEL_INDEX,
                    campaign.INTAKE_EXAM_ROOM_OCCLUDER_MODEL_INDEX,
                )
            )
        )

        wall = entries[campaign.INTAKE_EXAM_ROOM_WALL_MODEL_INDEX]
        self.assertEqual(
            (len(wall), _sha256(wall)),
            (
                campaign.INTAKE_EXAM_ROOM_WALL_MODEL_SIZE,
                campaign.INTAKE_EXAM_ROOM_WALL_MODEL_SHA256,
            ),
        )
        self.assertEqual(
            struct.unpack_from("<HHH", wall, 0x12),
            (660, 575, 3),
        )
        self.assertEqual(
            tuple(
                struct.unpack_from("<I", wall, offset)[0]
                for offset in (0x18, 0x1C, 0x20, 0x24, 0x44)
            ),
            (0x48, 0x48, 0x14E8, 0x26EC, 0x54A8),
        )

        native_occluder = native_entries[
            campaign.INTAKE_EXAM_ROOM_OCCLUDER_MODEL_INDEX
        ]
        occluder = entries[campaign.INTAKE_EXAM_ROOM_OCCLUDER_MODEL_INDEX]
        self.assertEqual(
            (len(native_occluder), _sha256(native_occluder)),
            (
                campaign.INTAKE_EXAM_ROOM_OCCLUDER_MODEL_SIZE,
                campaign.INTAKE_EXAM_ROOM_NATIVE_OCCLUDER_MODEL_SHA256,
            ),
        )
        self.assertEqual(
            (len(occluder), _sha256(occluder)),
            (
                campaign.INTAKE_EXAM_ROOM_OCCLUDER_MODEL_SIZE,
                campaign.INTAKE_EXAM_ROOM_OCCLUDER_MODEL_SHA256,
            ),
        )
        self.assertEqual(
            struct.unpack_from("<HHH", occluder, 0x12),
            (213, 208, 4),
        )
        self.assertEqual(
            tuple(
                struct.unpack_from("<I", occluder, offset)[0]
                for offset in (0x18, 0x1C, 0x20, 0x24, 0x44)
            ),
            (0x48, 0x48, 0x6F0, 0xD80, 0x17A0),
        )

        expected_occluder = bytearray(native_occluder)
        occluder_cursor = 0x6F0
        native_occluder_inventory: list[
            tuple[int, int, tuple[tuple[int, int, int, int], ...]]
        ] = []
        for group_index in range(4):
            primitive_type, unknown, primitive_count = struct.unpack_from(
                "<BBH", native_occluder, occluder_cursor
            )
            self.assertEqual(
                struct.unpack_from("<BBH", occluder, occluder_cursor),
                (primitive_type, unknown, primitive_count),
            )
            occluder_cursor += 4
            native_indices = tuple(
                struct.unpack_from(
                    "<HHHH",
                    native_occluder,
                    occluder_cursor + primitive_index * 8,
                )
                for primitive_index in range(primitive_count)
            )
            final_indices = tuple(
                struct.unpack_from(
                    "<HHHH",
                    occluder,
                    occluder_cursor + primitive_index * 8,
                )
                for primitive_index in range(primitive_count)
            )
            native_occluder_inventory.append(
                (primitive_type, unknown, native_indices)
            )
            if group_index in (0, 2):
                self.assertTrue(any(any(indices) for indices in native_indices))
                self.assertEqual(
                    final_indices,
                    ((0, 0, 0, 0),) * primitive_count,
                )
                expected_occluder[
                    occluder_cursor : occluder_cursor + primitive_count * 8
                ] = bytes(primitive_count * 8)
            else:
                self.assertEqual(final_indices, native_indices)
            occluder_cursor += primitive_count * 8
        self.assertEqual(
            tuple(
                (kind, unknown, len(indices))
                for kind, unknown, indices in native_occluder_inventory
            ),
            (
                (0x04, 0x77, 4),
                (0x05, 0x77, 6),
                (0x0C, 0x77, 134),
                (0x0D, 0x77, 64),
            ),
        )
        self.assertEqual(occluder_cursor, 0xD80)
        self.assertEqual(occluder, bytes(expected_occluder))
        self.assertEqual(occluder[0xD80:], native_occluder[0xD80:])

        threshold = entries[campaign.INTAKE_EXAM_ROOM_THRESHOLD_MODEL_INDEX]
        self.assertEqual(
            (len(threshold), _sha256(threshold)),
            (
                campaign.INTAKE_EXAM_ROOM_THRESHOLD_MODEL_SIZE,
                campaign.INTAKE_EXAM_ROOM_THRESHOLD_MODEL_SHA256,
            ),
        )
        self.assertEqual(
            _single_block_model_aabb(threshold),
            ((0, 89), (0, 0), (0, 44)),
        )
        self.assertEqual(
            struct.unpack_from("<HHH", threshold, 0x12),
            (15, 15, 2),
        )
        self.assertEqual(
            tuple(
                struct.unpack_from("<I", threshold, offset)[0]
                for offset in (0x18, 0x1C, 0x20, 0x24, 0x44)
            ),
            (0x48, 0x48, 0xC0, 0x140, 0x140),
        )
        vertex_offset = struct.unpack_from("<I", threshold, 0x18)[0]
        mesh_offset = struct.unpack_from("<I", threshold, 0x20)[0]
        display_offset = struct.unpack_from("<I", threshold, 0x24)[0]
        self.assertEqual(vertex_offset + 15 * 8, mesh_offset)
        self.assertEqual(
            struct.unpack_from("<BBH", threshold, mesh_offset),
            (0x0D, 0x77, 1),
        )
        self.assertEqual(
            tuple(
                struct.unpack_from(
                    "<HHHH", threshold, mesh_offset + 4 + index * 8
                )
                for index in range(1)
            ),
            ((0, 1, 4, 5),),
        )
        triangle_group = mesh_offset + 4 + 8
        self.assertEqual(
            struct.unpack_from("<BBH", threshold, triangle_group),
            (0x04, 0x77, 14),
        )
        self.assertEqual(
            tuple(
                struct.unpack_from(
                    "<HHHH", threshold, triangle_group + 4 + index * 8
                )
                for index in range(14)
            ),
            ((0, 0, 0, 0),) * 14,
        )
        self.assertEqual(triangle_group + 4 + 14 * 8, display_offset)
        self.assertEqual(
            threshold[display_offset : display_offset + 20],
            bytes.fromhex(
                "A8 00 00 C4 00 79 00 C8 "
                "00 00 00 2D 97 89 97 8D B6 89 B6 8D"
            ),
        )
        self.assertEqual(
            threshold[display_offset + 20 :],
            bytes.fromhex("00 00 00 20") * 14,
        )


def _sampled_cut_is_reachable(
    triangles: tuple[tuple[tuple[int, int, int], ...], ...],
    triangle_ids: tuple[int, ...],
    center: tuple[int, int],
    radius: int,
    start: tuple[int, int],
    goal: tuple[int, int],
    rectangular_half_extents: tuple[int, int] | None = None,
) -> bool:
    """Conservatively sample one local walkmesh chord around one seal."""

    selected = tuple(triangles[index] for index in triangle_ids)
    step = 2
    xs = [vertex[0] for triangle in selected for vertex in triangle]
    zs = [vertex[2] for triangle in selected for vertex in triangle]
    points = {
        (x, z)
        for x in range(min(xs) // step * step, max(xs) + 1, step)
        for z in range(min(zs) // step * step, max(zs) + 1, step)
        if (
            (
                (x - center[0]) ** 2 + (z - center[1]) ** 2
                >= radius ** 2
            )
            if rectangular_half_extents is None
            else (
                abs(x - center[0]) > rectangular_half_extents[0]
                or abs(z - center[1]) > rectangular_half_extents[1]
            )
        )
        and any(
            base._point_inside_triangle((x, z), triangle)
            for triangle in selected
        )
    }
    nearest = lambda point: min(  # noqa: E731 - local geometry helper
        points,
        key=lambda sample: (
            (sample[0] - point[0]) ** 2 + (sample[1] - point[1]) ** 2
        ),
    )
    sampled_start = nearest(start)
    sampled_goal = nearest(goal)
    reachable = {sampled_start}
    pending = deque((sampled_start,))
    while pending:
        x, z = pending.popleft()
        for dx in (-step, 0, step):
            for dz in (-step, 0, step):
                candidate = (x + dx, z + dz)
                if candidate in points and candidate not in reachable:
                    reachable.add(candidate)
                    pending.append(candidate)
    return sampled_goal in reachable


_SURFACE_ACTION_OPCODE_SIZES = {
    0x00: 1,  # STOP
    0x01: 3,  # JUMP
    0x02: 8,  # JUMP_IF
    0x07: 3,  # RUN_ENTITY_SCRIPT_ASYNC
    0x09: 3,  # RUN_ENTITY_SCRIPT_BLOCKING
    0x26: 3,  # WAIT
    0x31: 5,  # JUMP_IF_PAD_MASK
    0x33: 1,  # RESET_ACCUMULATED_INPUT_MASK
    0x35: 6,  # SET_VAR_FROM_S16
    0x39: 6,  # SUBTRACT_VARIABLE
    0x3A: 6,  # SET_VARBIT_TRUE
    0x3B: 6,  # SET_VARBIT_FALSE
    0x3E: 6,  # SET_VAR_AND
    0xDE: 6,  # MULTIPLY_VARIABLE
    0xDF: 6,  # DIVIDE_VARIABLE
    0x5B: 1,  # RESET_FIELD_SCRIPT_ACTOR_FOREVER
    0x67: 4,  # SET_ENTITY_FACING_TO_ENTITY_RELATIVE
    0x74: 3,  # PLAY_SOUND_EFFECT
    0x98: 5,  # CHANGE_FIELD_WHEN_READY2
    0x9C: 1,  # WAIT_DIALOG
    0xF5: 4,  # SHOW_DIALOG_WINDOW_MODE3
    0xFE: 2,  # extended opcode used here by FE53/FE54
}


def _reachable_surface_action_instructions(
    editor: ScriptEditor,
    start_pc: int,
) -> dict[int, bytes]:
    """Decode the small, frozen opcode vocabulary of Surface door actions."""

    pending = [start_pc]
    decoded: dict[int, bytes] = {}
    while pending:
        pc = pending.pop()
        while pc not in decoded:
            opcode = editor.bytecode[pc]
            if opcode not in _SURFACE_ACTION_OPCODE_SIZES:
                raise AssertionError(
                    f"unexpected Surface action opcode {opcode:02X} at 0x{pc:04X}"
                )
            size = _SURFACE_ACTION_OPCODE_SIZES[opcode]
            instruction = editor.bytecode[pc : pc + size]
            if len(instruction) != size:
                raise AssertionError(f"truncated Surface action at 0x{pc:04X}")
            decoded[pc] = instruction

            if opcode == 0x01:
                pending.append(struct.unpack_from("<H", instruction, 1)[0])
                break
            if opcode == 0x02:
                pending.append(struct.unpack_from("<H", instruction, 6)[0])
            elif opcode == 0x31:
                pending.append(struct.unpack_from("<H", instruction, 3)[0])
            if opcode in (0x00, 0x5B):
                break
            pc += size
    return decoded


def _simulate_archive_checkin_action(
    editor: ScriptEditor,
    *,
    initial_state: int,
    initial_appointment: int = 0,
    menu_choices: dict[int, int],
    character_weights: dict[int, int],
) -> dict[str, object]:
    """Execute the check-in action's small VM vocabulary independently.

    Cross is modeled as released, so OP31 takes its release target.  The
    retired retail binary-code menu is never a valid custom-action target.
    """

    pc = editor.get_script_pointer(campaign.ARCHIVE_TERMINAL_ENTITY, 2)
    variables = {
        campaign.STATE_OPERAND: initial_state,
        campaign.APPOINTMENT_OPERAND: initial_appointment,
    }
    dialogue_ids: list[int] = []
    current_dialogue_id: int | None = None
    control_suspends = 0
    control_restores = 0
    screen_opens: list[int] = []
    screen_closes: list[int] = []

    for _step in range(192):
        opcode = editor.bytecode[pc]
        if opcode == 0x00:  # STOP
            break
        if opcode == 0x01:  # JUMP
            target = struct.unpack_from("<H", editor.bytecode, pc + 1)[0]
            if target == campaign.ARCHIVE_TERMINAL_NATIVE_MENU_PC:
                raise AssertionError("check-in action reached retired binary menu")
            pc = target
            continue
        if opcode == 0x02:  # JUMP_IF
            operand, value = struct.unpack_from("<HH", editor.bytecode, pc + 1)
            operator = editor.bytecode[pc + 5]
            target = struct.unpack_from("<H", editor.bytecode, pc + 6)[0]
            if operator == 0x46:  # bit mask is clear
                take_branch = variables.get(operand, 0) & value == 0
            elif operator == 0x40:  # value is not equal
                take_branch = variables.get(operand, 0) != value
            elif operator == 0x41:  # value is equal
                take_branch = variables.get(operand, 0) == value
            else:
                raise AssertionError(
                    f"unexpected check-in comparison {operator:02X} at 0x{pc:04X}"
                )
            pc = target if take_branch else pc + 8
            continue
        if opcode == 0x07:  # native panel script, asynchronous
            entity, selector = editor.bytecode[pc + 1 : pc + 3]
            if entity in campaign.ARCHIVE_TERMINAL_SCREEN_ENTITIES:
                script = selector & 0x1F
                if script == campaign.ARCHIVE_TERMINAL_SCREEN_OPEN_SCRIPT:
                    screen_opens.append(entity)
                elif script == campaign.ARCHIVE_TERMINAL_SCREEN_CLOSE_SCRIPT:
                    screen_closes.append(entity)
                else:
                    raise AssertionError(
                        f"unexpected panel script {script} at 0x{pc:04X}"
                    )
            pc += 3
            continue
        if opcode == 0x09:  # retained player-use animation, blocking
            pc += 3
            continue
        if opcode == 0x26:  # WAIT
            pc += 3
            continue
        if opcode == 0x31:  # JUMP_IF_PAD_MASK; model Cross as released
            pc = struct.unpack_from("<H", editor.bytecode, pc + 3)[0]
            continue
        if opcode == 0x33:  # RESET_ACCUMULATED_INPUT_MASK
            pc += 1
            continue
        if opcode == 0x35:  # SET/COPY_VARIABLE
            destination, operand = struct.unpack_from(
                "<HH", editor.bytecode, pc + 1
            )
            flags = editor.bytecode[pc + 5]
            if flags == 0x40:
                value = operand
            elif flags == 0x00:
                value = variables.get(operand, 0)
            else:
                raise AssertionError(f"unexpected OP35 mode at 0x{pc:04X}")
            variables[destination] = value & 0xFFFF
            pc += 6
            continue
        if opcode in (0x38, 0x39, 0x3E, 0xDE, 0xDF):
            destination, operand = struct.unpack_from(
                "<HH", editor.bytecode, pc + 1
            )
            flags = editor.bytecode[pc + 5]
            if flags == 0x00:
                value = variables.get(operand, 0)
            elif flags == 0x40:
                value = operand
            else:
                raise AssertionError(
                    f"unexpected arithmetic mode at 0x{pc:04X}"
                )
            if opcode == 0x38:
                result = variables.get(destination, 0) + value
            elif opcode == 0x39:
                result = variables.get(destination, 0) - value
            elif opcode == 0x3E:
                result = variables.get(destination, 0) & value
            elif opcode == 0xDE:
                result = variables.get(destination, 0) * value
            else:
                if value == 0:
                    raise AssertionError(f"division by zero at 0x{pc:04X}")
                result = variables.get(destination, 0) // value
            variables[destination] = result & 0xFFFF
            pc += 6
            continue
        if opcode == 0x3A:  # SET_VARBIT_TRUE
            operand, bit_index = struct.unpack_from("<HH", editor.bytecode, pc + 1)
            if editor.bytecode[pc + 5] != 0x40:
                raise AssertionError(f"unexpected OP3A mode at 0x{pc:04X}")
            variables[operand] = variables.get(operand, 0) | (1 << bit_index)
            pc += 6
            continue
        if opcode == 0x67:  # retained world-relative player turn
            pc += 4
            continue
        if opcode == 0x74:  # retained terminal sound
            pc += 3
            continue
        if opcode == 0x9C:  # WAIT_DIALOG
            pc += 1
            continue
        if opcode == 0xA9:  # activate choices in the current D2 window
            if current_dialogue_id not in menu_choices:
                raise AssertionError(
                    f"no modeled selection for dialogue {current_dialogue_id}"
                )
            variables[0x0014] = menu_choices[current_dialogue_id]
            pc += 2
            continue
        if opcode == 0xD2:  # actor-owned dialogue
            current_dialogue_id = struct.unpack_from("<H", editor.bytecode, pc + 1)[0]
            if editor.bytecode[pc + 3] != 0:
                raise AssertionError(f"unexpected D2 mode at 0x{pc:04X}")
            dialogue_ids.append(current_dialogue_id)
            pc += 4
            continue
        if opcode == 0xFE:
            extension = editor.bytecode[pc + 1]
            if extension == 0x53:  # restore field control
                control_restores += 1
                pc += 2
                continue
            if extension == 0x54:  # suspend field control
                control_suspends += 1
                pc += 2
                continue
            if extension == 0x69:  # live character-weight read
                variable = struct.unpack_from("<H", editor.bytecode, pc + 2)[0]
                character_id, mode = editor.bytecode[pc + 4 : pc + 6]
                if mode != 0x80 or character_id not in character_weights:
                    raise AssertionError(f"invalid EX69 at 0x{pc:04X}")
                variables[variable] = character_weights[character_id]
                pc += 6
                continue
            raise AssertionError(
                f"unexpected check-in extension FE{extension:02X} at 0x{pc:04X}"
            )
        raise AssertionError(
            f"unexpected check-in opcode {opcode:02X} at 0x{pc:04X}"
        )
    else:
        raise AssertionError("check-in action did not terminate within 192 instructions")

    return {
        "state": variables[campaign.STATE_OPERAND],
        "appointment": variables[campaign.APPOINTMENT_OPERAND],
        "variables": variables,
        "dialogue_ids": tuple(dialogue_ids),
        "control_suspends": control_suspends,
        "control_restores": control_restores,
        "screen_opens": tuple(screen_opens),
        "screen_closes": tuple(screen_closes),
    }


def _run_appointment_vm(
    bytecode: bytes,
    *,
    start_pc: int,
    variables: dict[int, int],
    menu_choices: dict[int, int] | None = None,
    stop_pcs: tuple[int, ...] = (),
    stop_on_zero_wait: bool = False,
    max_steps: int = 512,
) -> dict[str, object]:
    """Execute the appointment routines' audited VM subset.

    This is intentionally independent of the production builders.  Cross is
    modeled as released, arithmetic wraps to one word, and WAIT 0 may be used
    as the observable scheduler-yield boundary for the timer poll.
    """

    values = {address: value & 0xFFFF for address, value in variables.items()}
    choices = {} if menu_choices is None else menu_choices
    pc = start_pc
    current_dialogue: int | None = None
    dialogue_ids: list[int] = []
    sound_ids: list[int] = []
    battle_ids: list[int] = []
    battle_syncs = 0
    hp_restores = 0
    mp_restores = 0
    save_menus = 0
    save_returns = 0
    save_modes: list[int] = []
    blocking_calls: list[tuple[int, int]] = []
    bit_writes: list[tuple[int, int, int]] = []
    bit_clears: list[tuple[int, int, int]] = []
    control_suspends = 0
    control_restores = 0
    field_change: tuple[int, int] | None = None

    def operand_value(raw: int, flags: int) -> int:
        if flags == 0x00:
            return values.get(raw, 0)
        if flags == 0x40:
            return raw
        raise AssertionError(f"unexpected appointment operand mode {flags:02X}")

    for _step in range(max_steps):
        if pc in stop_pcs:
            reason = "target"
            break
        opcode = bytecode[pc]
        if opcode == 0x00:
            reason = "stop"
            break
        if opcode == 0x01:
            pc = struct.unpack_from("<H", bytecode, pc + 1)[0]
            continue
        if opcode == 0x02:
            variable, raw = struct.unpack_from("<HH", bytecode, pc + 1)
            control = bytecode[pc + 5]
            target = struct.unpack_from("<H", bytecode, pc + 6)[0]
            left = values.get(variable, 0)
            if control == 0x40:
                branch = left != raw
            elif control == 0x41:
                branch = left == raw
            elif control == 0x44:
                branch = left < raw
            elif control == 0x46:
                branch = left & raw == 0
            else:
                raise AssertionError(
                    f"unexpected appointment comparison {control:02X} "
                    f"at 0x{pc:04X}"
                )
            pc = target if branch else pc + 8
            continue
        if opcode == 0x07:  # RUN_ENTITY_SCRIPT_ASYNC
            entity, selector = bytecode[pc + 1 : pc + 3]
            if (
                entity in campaign.CLINIC_SECURITY_ENTITIES
                and selector & 0x1F == campaign.CLINIC_SECURITY_ENTRY_SCRIPT
            ):
                bit = campaign.CLINIC_SECURITY_ENTITIES.index(entity)
                values[campaign.CLINIC_SECURITY_DONE_VARIABLE] = (
                    values.get(campaign.CLINIC_SECURITY_DONE_VARIABLE, 0)
                    | (1 << bit)
                )
            pc += 3
            continue
        if opcode == 0x09:  # RUN_ENTITY_SCRIPT_BLOCKING
            blocking_calls.append(tuple(bytecode[pc + 1 : pc + 3]))
            pc += 3
            continue
        if opcode == 0x19:  # SET_ACTOR_POSITION_2D
            pc += 6
            continue
        if opcode == 0x1A:  # actor walkmesh placement after a waypoint
            pc += 2
            continue
        if opcode == 0x20:  # SET_CURRENT_ACTOR_FLAGS
            pc += 3
            continue
        if opcode in (0x23,):  # MAKE_INVISIBLE_ACTIVE
            pc += 1
            continue
        if opcode == 0x24:  # MAKE_VISIBLE_ACTIVE
            pc += 2
            continue
        if opcode == 0x2A:  # DISABLE_DIALOG_ACTIVATION
            pc += 1
            continue
        if opcode == 0x26:
            frames = struct.unpack_from("<H", bytecode, pc + 1)[0] & 0x7FFF
            pc += 3
            if frames == 0 and stop_on_zero_wait:
                reason = "yield"
                break
            continue
        if opcode == 0x31:  # model Cross as already released
            pc = struct.unpack_from("<H", bytecode, pc + 3)[0]
            continue
        if opcode == 0x33:
            pc += 1
            continue
        if opcode == 0x35:
            destination, raw = struct.unpack_from("<HH", bytecode, pc + 1)
            values[destination] = operand_value(raw, bytecode[pc + 5]) & 0xFFFF
            pc += 6
            continue
        if opcode in (0x38, 0x39, 0x3E, 0xDE):
            destination, raw = struct.unpack_from("<HH", bytecode, pc + 1)
            operand = operand_value(raw, bytecode[pc + 5])
            original = values.get(destination, 0)
            if opcode == 0x38:
                result = original + operand
            elif opcode == 0x39:
                result = original - operand
            elif opcode == 0x3E:
                result = original & operand
            else:
                result = original * operand
            values[destination] = result & 0xFFFF
            pc += 6
            continue
        if opcode == 0x3A:
            destination, bit_index = struct.unpack_from("<HH", bytecode, pc + 1)
            if bytecode[pc + 5] != 0x40:
                raise AssertionError(f"unexpected OP3A mode at 0x{pc:04X}")
            values[destination] = values.get(destination, 0) | (1 << bit_index)
            bit_writes.append((pc, destination, bit_index))
            pc += 6
            continue
        if opcode == 0x3B:
            destination, bit_index = struct.unpack_from("<HH", bytecode, pc + 1)
            if bytecode[pc + 5] != 0x40:
                raise AssertionError(f"unexpected OP3B mode at 0x{pc:04X}")
            values[destination] = values.get(destination, 0) & ~(1 << bit_index)
            bit_clears.append((pc, destination, bit_index))
            pc += 6
            continue
        if opcode == 0x42:
            destination, raw = struct.unpack_from("<HH", bytecode, pc + 1)
            values[destination] = values.get(destination, 0) >> (raw & 0x7FFF)
            pc += 5
            continue
        if opcode == 0x4B:  # bounded actor waypoint, movement is not simulated
            pc += 8
            continue
        if opcode == 0x5F:  # SET_ACTOR_DIRECTION
            pc += 2
            continue
        if opcode == 0x6F:  # face interacting actor; movement not simulated
            pc += 2
            continue
        if opcode == 0x79:  # RESTORE_PARTY_HP
            hp_restores += 1
            pc += 1
            continue
        if opcode == 0x7A:  # RESTORE_PARTY_MP
            mp_restores += 1
            pc += 1
            continue
        if opcode == 0x74:  # PLAY_SOUND
            sound_ids.append(
                struct.unpack_from("<H", bytecode, pc + 1)[0] & 0x7FFF
            )
            pc += 3
            continue
        if opcode == 0x71:  # START_BATTLE
            battle_ids.append(
                struct.unpack_from("<H", bytecode, pc + 1)[0] & 0x7FFF
            )
            pc += 3
            continue
        if opcode == 0x75:  # PLAY_MUSIC
            pc += 3
            continue
        if opcode == 0x98:  # CHANGE_FIELD_WHEN_READY2
            raw_field, raw_parameter = struct.unpack_from("<HH", bytecode, pc + 1)
            field_change = (raw_field & 0x7FFF, raw_parameter & 0x7FFF)
            reason = "field_change"
            break
        if opcode == 0x9C:
            pc += 1
            continue
        if opcode == 0xA9:
            if current_dialogue not in choices:
                raise AssertionError(
                    f"no modeled appointment selection for {current_dialogue}"
                )
            values[0x0014] = choices[current_dialogue]
            pc += 2
            continue
        if opcode == 0xD2:
            current_dialogue = struct.unpack_from("<H", bytecode, pc + 1)[0]
            dialogue_ids.append(current_dialogue)
            pc += 4
            continue
        if opcode == 0xF4:  # RESET_DIALOG_WINDOW_STATE
            if bytecode[pc + 1] != 0x01:
                raise AssertionError(f"unexpected OPF4 mode at 0x{pc:04X}")
            pc += 2
            continue
        if opcode == 0xF5:
            current_dialogue = struct.unpack_from("<H", bytecode, pc + 1)[0]
            dialogue_ids.append(current_dialogue)
            pc += 4
            continue
        if opcode == 0xF8:  # audited actor-local doorway traversal override
            if bytecode[pc + 1:pc + 4] not in (b"\x02\x38\x00", b"\x06\x38\x00"):
                raise AssertionError(f"unsupported actor flag instruction at 0x{pc:04X}")
            pc += 4
            continue
        if opcode == 0xFE:
            extension = bytecode[pc + 1]
            if extension == 0x53:
                control_restores += 1
                pc += 2
                continue
            if extension == 0x54:
                control_suspends += 1
                pc += 2
                continue
            if extension == 0x0D:
                pc += 4
                continue
            if extension == 0x17:  # face another entity; movement not simulated
                pc += 4
                continue
            if extension == 0x08:  # diagnostic relay scale; no campaign state
                pc += 8
                continue
            if extension == 0x7F:  # postbattle field synchronization
                battle_syncs += 1
                pc += 2
                continue
            if extension == 0x84:  # fixed formation; model its successful return
                configuration, ignored, next_field, next_parameter = struct.unpack_from("<4H", bytecode, pc + 2)
                if (ignored, next_field, next_parameter) != (0x8000, 0xFFFF, 0x8000):
                    raise AssertionError(f"unsupported fixed battle return at 0x{pc:04X}")
                battle_ids.append(configuration & 0x7FFF)
                pc += 10
                continue
            if extension == 0x99:  # native save-menu mode
                save_modes.append(bytecode[pc + 2])
                pc += 3
                continue
            if extension == 0x55:  # native save menu handoff
                save_menus += 1
                pc += 2
                continue
            if extension == 0x87:  # native save-menu return
                save_returns += 1
                pc += 2
                continue
            raise AssertionError(
                f"unexpected appointment extension FE{extension:02X} "
                f"at 0x{pc:04X}"
            )
        raise AssertionError(
            f"unexpected appointment opcode {opcode:02X} at 0x{pc:04X}"
        )
    else:
        raise AssertionError(
            f"appointment routine exceeded {max_steps} instructions"
        )

    return {
        "reason": reason,
        "pc": pc,
        "variables": values,
        "dialogue_ids": tuple(dialogue_ids),
        "sound_ids": tuple(sound_ids),
        "battle_ids": tuple(battle_ids),
        "battle_syncs": battle_syncs,
        "hp_restores": hp_restores,
        "mp_restores": mp_restores,
        "save_menus": save_menus,
        "save_returns": save_returns,
        "save_modes": tuple(save_modes),
        "blocking_calls": tuple(blocking_calls),
        "bit_writes": tuple(bit_writes),
        "bit_clears": tuple(bit_clears),
        "control_suspends": control_suspends,
        "control_restores": control_restores,
        "field_change": field_change,
    }


def _clock_variables(total_seconds: int) -> dict[int, int]:
    """Encode native hours plus packed minute/second system variables."""

    hours, remainder = divmod(total_seconds, 3_600)
    minutes, seconds = divmod(remainder, 60)
    return {0x000E: hours, 0x000C: (minutes << 8) | seconds}


_MUSIC_INITIALIZER_OPCODE_SIZES = {
    0x00: 1,  # STOP
    0x01: 3,  # JUMP
    0x02: 8,  # JUMP_IF
    0x18: 5,  # SET_BOUNDING_VOLUME
    0x19: 6,  # SET_ACTOR_POSITION_2D
    0x20: 3,  # SET_CURRENT_ACTOR_FLAGS
    0x23: 1,  # MAKE_INVISIBLE_ACTIVE
    0x2A: 1,  # DISABLE_DIALOG_ACTIVATION
    0x35: 6,  # SET_VAR_FROM_S16
    0x75: 3,  # PLAY_MUSIC
    0x80: 5,  # retail field-effect setup
    0xA0: 7,  # SET_SCREEN_GEOMETRY
    0xBC: 1,  # INIT_ENTITY_SCRIPT
    0xE7: 7,  # SET_BACKGROUND_CLEAR_COLOR
    0xF7: 5,  # SET_ENCOUNTER_DATA
    0xF8: 4,  # SET_FLAGS_DYNAMIC
}


def _reachable_music_initializer_instructions(
    editor: ScriptEditor,
) -> dict[int, bytes]:
    """Decode only the frozen entity-zero initializer vocabulary.

    This deliberately starts at the current e0:s0 pointer.  Dormant retail
    cutscene bodies elsewhere in a few fields still contain raw byte 0x75 and
    must not be mistaken for active room music.
    """

    pending = [editor.get_script_pointer(0, 0)]
    decoded: dict[int, bytes] = {}
    while pending:
        pc = pending.pop()
        while pc not in decoded:
            opcode = editor.bytecode[pc]
            if opcode == 0xFE:
                if editor.bytecode[pc : pc + 2] != b"\xFE\xB8":
                    raise AssertionError(
                        f"unexpected initializer extension at 0x{pc:04X}"
                    )
                size = 5
            else:
                if opcode not in _MUSIC_INITIALIZER_OPCODE_SIZES:
                    raise AssertionError(
                        f"unexpected music initializer opcode {opcode:02X} "
                        f"at 0x{pc:04X}"
                    )
                size = _MUSIC_INITIALIZER_OPCODE_SIZES[opcode]
            instruction = editor.bytecode[pc : pc + size]
            if len(instruction) != size:
                raise AssertionError(
                    f"truncated music initializer at 0x{pc:04X}"
                )
            decoded[pc] = instruction

            if opcode == 0x01:
                pending.append(struct.unpack_from("<H", instruction, 1)[0])
                break
            if opcode == 0x02:
                pending.append(struct.unpack_from("<H", instruction, 6)[0])
            if opcode == 0x00:
                break
            pc += size
    return decoded


class SurfaceSoylentCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not SOURCE_DISC.is_file() or not DONOR_DISC.is_file():
            raise unittest.SkipTest("checked Surface campaign source discs are unavailable")
        cls.base_fields, cls.base_donors = base.prepare_complete_route(
            SOURCE_DISC, DONOR_DISC
        )
        cls.base_567 = empty_clinic567.prepare_empty_clinic567_from_discs(
            SOURCE_DISC,
            DONOR_DISC,
        )
        cls.base_588 = donor588.prepare_donor588_from_discs(SOURCE_DISC, DONOR_DISC)
        cls.base_590 = stabilization590.prepare_stabilization590_from_discs(
            SOURCE_DISC,
            DONOR_DISC,
        )
        cls.base_exam_rooms = exam_rooms.prepare_exam_rooms_from_discs(
            SOURCE_DISC,
            DONOR_DISC,
        )
        cls.base_exam_room_by_scene = {
            item.identity.scene: item for item in cls.base_exam_rooms
        }
        cls.clinic_pre_door = campaign._prepare_clinic_office(DONOR_DISC)
        cls.fields, cls.donors, cls.title = campaign.prepare_campaign(
            SOURCE_DISC, DONOR_DISC
        )
        cls.field_by_scene = {item.spec.identity.scene: item for item in cls.fields}
        cls.donor_by_scene = {item.identity.scene: item for item in cls.donors}
        cls.base_field_by_scene = {
            item.spec.identity.scene: item for item in cls.base_fields
        }
        cls.base_donor_by_scene = {
            item.identity.scene: item for item in cls.base_donors
        }
        cls.base_donor_by_scene[567] = cls.base_567
        cls.base_donor_by_scene[590] = cls.base_590

    def test_u16_encoder_fails_closed(self) -> None:
        self.assertEqual(campaign._u16(0), b"\x00\x00")
        self.assertEqual(campaign._u16(0xFFFF), b"\xFF\xFF")
        for value in (-1, 0x10000):
            with self.subTest(value=value):
                with self.assertRaises(campaign.SurfaceCampaignBuildError):
                    campaign._u16(value)

    def test_exact_eighteen_room_campaign_and_frozen_outputs(self) -> None:
        self.assertEqual(
            set(self.field_by_scene) | set(self.donor_by_scene),
            {room.field for room in blueprint.ROOMS},
        )
        self.assertEqual(len(blueprint.ROOMS), 18)
        self.assertEqual(len(blueprint.DOOR_PAIRS), 20)
        self.assertEqual(len(blueprint.ENDPOINTS), 40)
        self.assertEqual(
            {room.field for room in blueprint.ROOMS} & set(exam_rooms.SCENES),
            set(exam_rooms.SCENES),
        )
        prepared = self.field_by_scene | self.donor_by_scene
        self.assertEqual(set(prepared), set(campaign.CAMPAIGN_FINAL_IDENTITIES))
        for scene, item in prepared.items():
            with self.subTest(scene=scene):
                self.assertEqual(
                    (
                        len(item.components[base.SCRIPT_INDEX]),
                        _sha256(item.components[base.SCRIPT_INDEX]),
                        len(item.components[7]),
                        _sha256(item.components[7]),
                        len(item.bundle),
                        _sha256(item.bundle),
                    ),
                    campaign.CAMPAIGN_FINAL_IDENTITIES[scene],
                )

    def test_authentic_krelian_lab_music_sources_and_assets_are_frozen(self) -> None:
        self.assertEqual(
            campaign.KRELIAN_LAB_WAVE_LOCAL_FILE,
            campaign.KRELIAN_LAB_MUSIC_ID * 2 + 0x13,
        )
        self.assertEqual(
            campaign.KRELIAN_LAB_SEQUENCE_LOCAL_FILE,
            campaign.KRELIAN_LAB_MUSIC_ID * 2 + 0x14,
        )
        disc2_assets = campaign._load_campaign_music_assets(SOURCE_DISC)
        disc1_assets = campaign._load_campaign_music_assets(DONOR_DISC)
        self.assertEqual(disc1_assets, disc2_assets)
        self.assertEqual(
            set(disc2_assets),
            set(campaign.KRELIAN_LAB_MUSIC_ASSET_IDENTITIES),
        )
        for local_file, data in disc2_assets.items():
            with self.subTest(asset=f"0x{local_file:02X}"):
                self.assertEqual(
                    (len(data), _sha256(data)),
                    campaign.KRELIAN_LAB_MUSIC_ASSET_IDENTITIES[local_file],
                )

        image = Mode2Image(DONOR_DISC)
        entries = image.read_index()
        first = image.read_directories()[FIELD_DIRECTORY].first_file
        self.assertGreaterEqual(first, 0)
        for scene, evidence in campaign.KRELIAN_LAB_MUSIC_SOURCE_EVIDENCE.items():
            (
                canonical_bundle_id,
                expected_bundle_size,
                expected_bundle_sha,
                expected_script_size,
                expected_script_sha,
                initializer_pc,
                music_pc,
            ) = evidence
            local_file = FIRST_FIELD_LOCAL_FILE + 2 * scene
            fat_index = directory_file_fat_index(first, local_file)
            with self.subTest(scene=scene):
                self.assertEqual(fat_index + 5, canonical_bundle_id)
                bundle = image.extract_entry(entries[fat_index])
                self.assertEqual(
                    (len(bundle), _sha256(bundle)),
                    (expected_bundle_size, expected_bundle_sha),
                )
                script = parse_field(bundle).parts[base.SCRIPT_INDEX].data
                self.assertEqual(
                    (len(script), _sha256(script)),
                    (expected_script_size, expected_script_sha),
                )
                editor = ScriptEditor(script)
                self.assertEqual(editor.get_script_pointer(0, 0), initializer_pc)
                self.assertEqual(
                    editor.bytecode[
                        music_pc : music_pc + len(campaign.KRELIAN_LAB_MUSIC_OPCODE)
                    ],
                    campaign.KRELIAN_LAB_MUSIC_OPCODE,
                )

    def test_perfect_works_deathblow_level_requirements_are_removed(self) -> None:
        decoded = campaign._validate_no_deathblow_level_requirements(SOURCE_DISC)
        self.assertEqual(
            (len(decoded), _sha256(decoded)),
            (
                campaign.DEATHBLOW_LEVEL_FILE0_SIZE,
                campaign.DEATHBLOW_LEVEL_FILE0_SHA256,
            ),
        )
        profiles = tuple(
            profile
            for profile in deathblows.DEATHBLOW_PROFILES
            if profile.full_mask
        )
        for profile, offset in zip(
            profiles,
            campaign.DEATHBLOW_LEVEL_TABLE_OFFSETS,
            strict=True,
        ):
            with self.subTest(character=profile.character):
                count = len(profile.command_names)
                self.assertEqual(
                    decoded[offset : offset + count], bytes((1,)) * count
                )
                self.assertIn(decoded[offset + count], (0x00, 0xFF))

    def test_nortune_selector_is_frozen_and_excluded(self) -> None:
        self.assertNotEqual(
            campaign.NORTUNE_STEALTH_MUSIC_ID,
            campaign.KRELIAN_LAB_MUSIC_ID,
        )
        self.assertNotEqual(
            campaign.NORTUNE_STEALTH_MUSIC_OPCODE,
            campaign.KRELIAN_LAB_MUSIC_OPCODE,
        )

        image = Mode2Image(DONOR_DISC)
        entries = image.read_index()
        first = image.read_directories()[FIELD_DIRECTORY].first_file
        self.assertGreaterEqual(first, 0)
        for scene, evidence in (
            campaign.NORTUNE_STEALTH_MUSIC_SOURCE_EVIDENCE.items()
        ):
            (
                canonical_bundle_id,
                expected_bundle_size,
                expected_bundle_sha,
                expected_script_size,
                expected_script_sha,
                initializer_pc,
                music_pc,
            ) = evidence
            local_file = FIRST_FIELD_LOCAL_FILE + 2 * scene
            fat_index = directory_file_fat_index(first, local_file)
            with self.subTest(scene=scene):
                self.assertEqual(fat_index + 5, canonical_bundle_id)
                bundle = image.extract_entry(entries[fat_index])
                self.assertEqual(
                    (len(bundle), _sha256(bundle)),
                    (expected_bundle_size, expected_bundle_sha),
                )
                script = parse_field(bundle).parts[base.SCRIPT_INDEX].data
                self.assertEqual(
                    (len(script), _sha256(script)),
                    (expected_script_size, expected_script_sha),
                )
                editor = ScriptEditor(script)
                self.assertEqual(editor.get_script_pointer(0, 0), initializer_pc)
                self.assertEqual(
                    editor.bytecode[
                        music_pc :
                        music_pc + len(campaign.NORTUNE_STEALTH_MUSIC_OPCODE)
                    ],
                    campaign.NORTUNE_STEALTH_MUSIC_OPCODE,
                )

    def test_all_fourteen_rooms_select_one_reachable_krelian_lab_cue(self) -> None:
        prepared = self.field_by_scene | self.donor_by_scene
        self.assertEqual(
            set(prepared),
            set(campaign.CAMPAIGN_PRE_MUSIC_SCRIPT_IDENTITIES),
        )
        for scene, item in prepared.items():
            editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
            instructions = _reachable_music_initializer_instructions(editor)
            music = {
                pc: instruction
                for pc, instruction in instructions.items()
                if instruction[0] == 0x75
            }
            with self.subTest(scene=scene):
                self.assertEqual(
                    music,
                    {
                        (
                            {
                                565: campaign.FIELD565_MUSIC_PC,
                                stabilization590.SCENE: reserved_donor567.MUSIC_PC,
                            }[scene]
                            if scene in (565, stabilization590.SCENE)
                            else campaign.CAMPAIGN_MUSIC_WRAPPER_PCS[scene]
                            + 1
                        ): campaign.KRELIAN_LAB_MUSIC_OPCODE
                    },
                )
                self.assertIn(b"\x00", instructions.values())

                if scene in (565, stabilization590.SCENE):
                    self.assertEqual(
                        editor.get_script_pointer(0, 0),
                        campaign.CAMPAIGN_MUSIC_SOURCE_ENTRY_PCS[scene],
                    )
                    self.assertEqual(
                        (
                            len(item.components[base.SCRIPT_INDEX]),
                            _sha256(item.components[base.SCRIPT_INDEX]),
                        ),
                        campaign.CAMPAIGN_PRE_MUSIC_SCRIPT_IDENTITIES[scene],
                    )
                    continue

                wrapper_pc = campaign.CAMPAIGN_MUSIC_WRAPPER_PCS[scene]
                source_pc = campaign.CAMPAIGN_MUSIC_SOURCE_ENTRY_PCS[scene]
                wrapper = (
                    b"\xBC"
                    + campaign.KRELIAN_LAB_MUSIC_OPCODE
                    + b"\x01"
                    + struct.pack("<H", source_pc + 1)
                )
                self.assertEqual(editor.get_script_pointer(0, 0), wrapper_pc)
                self.assertEqual(
                    editor.bytecode[wrapper_pc : wrapper_pc + len(wrapper)],
                    wrapper,
                )

    def test_campaign_music_transform_fails_closed(self) -> None:
        prepared = self.field_by_scene | self.donor_by_scene
        for scene in (621, 567):
            with self.subTest(wrapper_scene=scene):
                final_script = prepared[scene].components[base.SCRIPT_INDEX]
                final_editor = ScriptEditor(final_script)
                wrapper_pc = campaign.CAMPAIGN_MUSIC_WRAPPER_PCS[scene]
                source_pc = campaign.CAMPAIGN_MUSIC_SOURCE_ENTRY_PCS[scene]
                self.assertEqual(final_editor.bytecode_size, wrapper_pc + 7)

                pre_music = bytearray(final_script)
                struct.pack_into("<H", pre_music, 0x84, source_pc)
                del pre_music[final_editor.bytecode_offset + wrapper_pc :]
                pre_music_script = bytes(pre_music)
                self.assertEqual(
                    (len(pre_music_script), _sha256(pre_music_script)),
                    campaign.CAMPAIGN_PRE_MUSIC_SCRIPT_IDENTITIES[scene],
                )
                self.assertEqual(
                    campaign._install_campaign_music(
                        pre_music_script,
                        scene,
                    ).to_bytes(),
                    final_script,
                )

                changed = bytearray(pre_music_script)
                changed[final_editor.bytecode_offset + source_pc] ^= 0x01
                with self.assertRaisesRegex(
                    campaign.SurfaceCampaignBuildError,
                    "pre-music ATEL identity changed",
                ):
                    campaign._install_campaign_music(bytes(changed), scene)

        for scene in (565, stabilization590.SCENE):
            native_script = self.donor_by_scene[scene].components[base.SCRIPT_INDEX]
            with self.subTest(native_music_scene=scene):
                self.assertEqual(
                    campaign._install_campaign_music(
                        native_script,
                        scene,
                    ).to_bytes(),
                    native_script,
                )

    def test_all_forty_planned_blueprint_foundations_resolve_to_an_entry(self) -> None:
        # The blueprint deliberately retains the authored future reciprocal
        # graph.  V212's runtime field-620/e24 override is tested separately
        # as a dialogue-only current-content boundary.
        entries = {
            (item.spec.identity.scene, edit.parameter)
            for item in self.fields
            for edit in item.spec.entry_edits
        }
        entries.update(
            (item.identity.scene, parameter)
            for item in self.donors
            for parameter, _triangle in item.entry_triangles
        )
        self.assertEqual(len(blueprint.ENDPOINTS), 40)
        for endpoint in blueprint.ENDPOINTS:
            with self.subTest(endpoint=endpoint.id):
                self.assertIn(
                    (endpoint.destination_field, endpoint.destination_entry_parameter),
                    entries,
                )
                self.assertEqual(endpoint.interaction, "x")
        blueprint.validate_blueprint()
        snapshots = blueprint.simulate_progression()
        self.assertEqual(snapshots[-1].reachable_rooms, frozenset(entries_field for entries_field, _ in entries))

    def test_campaign_consoles_are_on_audited_walkmesh_and_scheduler_active(self) -> None:
        contracts = {
            624: (campaign.SORTER_CONSOLES, (77, 78, 79)),
            626: (campaign.CORE_CONSOLES, (59, 60, 61)),
            625: ((campaign.MELD_CONSOLE,), (33,)),
            622: (
                (campaign.GENERATION_SAVE_CONSOLE, campaign.GENERATION_BOSS_CONSOLE),
                (28, 29),
            ),
        }
        for scene, (consoles, entities) in contracts.items():
            item = self.field_by_scene[scene]
            editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
            triangles = base._walkmesh_layer(item.components[1], 0)
            for console, entity in zip(consoles, entities, strict=True):
                with self.subTest(scene=scene, entity=entity):
                    self.assertTrue(
                        base._point_inside_triangle(
                            (console.x, console.z), triangles[console.triangle]
                        )
                    )
                    init_pc = editor.get_script_pointer(entity, 0)
                    expected = campaign._console_init(console)
                    self.assertEqual(editor.bytecode[init_pc : init_pc + len(expected)], expected)
                    self.assertTrue(expected.startswith(bytes.fromhex("0B 00 80")))
                    self.assertIn(bytes.fromhex("F8 00 00 20"), expected)
                    self.assertIn(bytes.fromhex("20 01 80 23 00"), expected)

        item = self.donor_by_scene[588]
        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
        console = campaign.INTERFACE_CONSOLE
        triangles = base._walkmesh_layer(item.components[1], 0)
        self.assertTrue(
            base._point_inside_triangle(
                (console.x, console.z), triangles[console.triangle]
            )
        )
        init_pc = editor.get_script_pointer(donor588.CONSOLE_ENTITY, 0)
        expected = campaign._console_init(console)
        self.assertEqual(editor.bytecode[init_pc : init_pc + len(expected)], expected)

    def test_inserted_controller_records_preserve_every_static_model(self) -> None:
        contracts = {
            623: (self.base_field_by_scene[623], self.field_by_scene[623], ()),
            621: (self.base_field_by_scene[621], self.field_by_scene[621], ()),
            620: (self.base_field_by_scene[620], self.field_by_scene[620], ()),
            624: (self.base_field_by_scene[624], self.field_by_scene[624], campaign.SORTER_CONSOLES),
            626: (self.base_field_by_scene[626], self.field_by_scene[626], campaign.CORE_CONSOLES),
            625: (self.base_field_by_scene[625], self.field_by_scene[625], (campaign.MELD_CONSOLE,)),
            622: (
                self.base_field_by_scene[622],
                self.field_by_scene[622],
                (campaign.GENERATION_SAVE_CONSOLE, campaign.GENERATION_BOSS_CONSOLE),
            ),
            549: (self.base_donor_by_scene[549], self.donor_by_scene[549], ()),
            550: (self.clinic_pre_door, self.donor_by_scene[550], ()),
            565: (self.base_donor_by_scene[565], self.donor_by_scene[565], ()),
            567: (self.base_567, self.donor_by_scene[567], ()),
            591: (
                self.base_exam_room_by_scene[591],
                self.donor_by_scene[591],
                (),
            ),
            592: (
                self.base_exam_room_by_scene[592],
                self.donor_by_scene[592],
                (),
            ),
            593: (
                self.base_exam_room_by_scene[593],
                self.donor_by_scene[593],
                (),
            ),
            594: (
                self.base_exam_room_by_scene[594],
                self.donor_by_scene[594],
                (),
            ),
            589: (self.base_donor_by_scene[589], self.donor_by_scene[589], ()),
            # Field 588 reuses native scanner carrier e4 beside the baked
            # six-node diagnostic fixture.
            # Only the physical return-door seal extends the entity/header
            # tables; the credential console itself must not add a model-less
            # actor record.
            588: (self.base_588, self.donor_by_scene[588], ()),
        }
        for scene, (before, after, consoles) in contracts.items():
            with self.subTest(scene=scene):
                old_count = ScriptEditor(before.components[base.SCRIPT_INDEX]).entity_count
                doors = (
                    base.NATIVE_DOOR_CONTROLLERS.get(scene)
                    or campaign.DONOR_DOOR_COLLISION_CONTRACTS.get(scene, ())
                )
                doctor = (
                    (
                        campaign.Console(
                            campaign.INTAKE_DOCTOR_STAGING_POSITION[0],
                            campaign.INTAKE_DOCTOR_STAGING_POSITION[1],
                            86,
                            0,
                            "",
                        ),
                    )
                    if scene == 621
                    else ()
                )
                security = (
                    tuple(
                        campaign.Console(
                            campaign.CLINIC_SECURITY_STAGING_POSITION[0],
                            campaign.CLINIC_SECURITY_STAGING_POSITION[1],
                            34,
                            0,
                            "",
                        )
                        for _entity in campaign.CLINIC_SECURITY_ENTITIES
                    )
                    if scene == 550
                    else ()
                )
                inserted = (*consoles, *doctor, *doors, *security)
                exam_door_records = (
                    (
                        *(
                            base.mass_driver._field_actor_record(
                                0x01E0, door.x, door.z, 0
                            )
                            for door in campaign.INTAKE_EXAM_ROOM_DOORS
                        ),
                        *(
                            struct.pack(
                                "<Hhhh hhh H",
                                campaign.INTAKE_EXAM_ROOM_MODEL_FLAGS,
                                0,
                                yaw,
                                0,
                                origin_x,
                                origin_y,
                                origin_z,
                                model_index,
                            )
                            for (
                                model_index,
                                yaw,
                                origin_x,
                                origin_y,
                                origin_z,
                                _delta_x,
                                _delta_z,
                            ) in campaign.INTAKE_EXAM_ROOM_MODEL_PLACEMENTS
                        ),
                    )
                    if scene == 621
                    else ()
                )
                exam_threshold_records = (
                    tuple(
                        struct.pack(
                            "<Hhhh hhh H",
                            campaign.INTAKE_EXAM_ROOM_THRESHOLD_MODEL_FLAGS,
                            0,
                            yaw,
                            0,
                            origin_x,
                            origin_y,
                            origin_z,
                            campaign.INTAKE_EXAM_ROOM_THRESHOLD_MODEL_INDEX,
                        )
                        for yaw, origin_x, origin_y, origin_z in (
                            campaign.INTAKE_EXAM_ROOM_THRESHOLD_PLACEMENTS
                        )
                    )
                    if scene == 621
                    else ()
                )
                before_records = _actor_records(before.header)
                after_records = _actor_records(after.header)
                duplicated_leaves = ()
                if scene == 623:
                    north_header = campaign._insert_transfer_north_door_leaf_records(
                        before.header,
                        old_entity_count=old_count,
                    )
                    duplicated_leaves = _actor_records(north_header)[
                        old_count : old_count
                        + len(campaign.TRANSFER_NORTH_DOOR_HELPER_ENTITIES)
                    ]
                self.assertEqual(before_records[:old_count], after_records[:old_count])
                preserved_start = (
                    old_count
                    + len(duplicated_leaves)
                    + len(inserted)
                    + len(exam_door_records)
                )
                preserved_end = len(after_records) - len(exam_threshold_records)
                self.assertEqual(
                    before_records[old_count:],
                    after_records[preserved_start:preserved_end],
                )
                expected = (
                    duplicated_leaves
                    + tuple(
                        base.mass_driver._field_actor_record(
                            0x01E0,
                            *(
                                campaign._donor_seal_position(inserted_item)
                                if isinstance(
                                    inserted_item,
                                    campaign.DonorDoorCollisionContract,
                                )
                                else (inserted_item.x, inserted_item.z)
                            ),
                            0,
                        )
                        for inserted_item in inserted
                    )
                    + exam_door_records
                )
                self.assertEqual(
                    after_records[old_count : old_count + len(expected)],
                    expected,
                )
                if exam_threshold_records:
                    self.assertEqual(
                        after_records[-len(exam_threshold_records) :],
                        exam_threshold_records,
                    )

    def test_all_native_surface_doors_split_action_from_collision(self) -> None:
        self.assertEqual(
            set(campaign.SURFACE_DOOR_COLLISION_CONTRACTS),
            set(base.NATIVE_DOOR_CONTROLLERS),
        )
        for scene, doors in base.NATIVE_DOOR_CONTROLLERS.items():
            item = self.field_by_scene[scene]
            editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
            contracts = campaign.SURFACE_DOOR_COLLISION_CONTRACTS[scene]
            self.assertEqual(len(doors), len(contracts))
            first_seal = (
                campaign.INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES[0] - len(doors)
                if scene == 621
                else editor.entity_count - len(doors)
            )
            triangles = base._walkmesh_layer(item.components[1], 0)
            for offset, (door, contract) in enumerate(
                zip(doors, contracts, strict=True)
            ):
                seal_entity = first_seal + offset
                with self.subTest(scene=scene, controller=contract.controller_entity):
                    self.assertTrue(
                        base._point_inside_triangle(
                            (door.x, door.z), triangles[door.triangle]
                        )
                    )
                    controller_init = campaign._ghost_door_controller_init(door)
                    controller_pc = editor.get_script_pointer(
                        contract.controller_entity, 0
                    )
                    if contract.controller_entity == 0:
                        self.assertEqual(
                            controller_pc,
                            campaign.CAMPAIGN_MUSIC_WRAPPER_PCS[scene],
                        )
                        controller_pc = campaign.CAMPAIGN_MUSIC_SOURCE_ENTRY_PCS[
                            scene
                        ]
                    self.assertEqual(
                        editor.bytecode[
                            controller_pc : controller_pc + len(controller_init)
                        ],
                        controller_init,
                    )
                    self.assertIn(bytes.fromhex("20 01 80 23 00"), controller_init)
                    self.assertNotIn(bytes.fromhex("F8 00 10 00"), controller_init)

                    seal_init = campaign._door_seal_init(
                        door, contract.normal_axis
                    )
                    seal_pc = editor.get_script_pointer(seal_entity, 0)
                    self.assertEqual(
                        editor.bytecode[seal_pc : seal_pc + len(seal_init)],
                        seal_init,
                    )
                    self.assertIn(bytes.fromhex("F8 00 10 00 2A 23 00"), seal_init)
                    half_width, half_depth = campaign._door_seal_bounds(
                        door, contract.normal_axis
                    )
                    if contract.normal_axis == "x":
                        self.assertEqual(
                            half_width,
                            campaign.DOOR_SEAL_NORMAL_HALF_EXTENT,
                        )
                        self.assertEqual(half_depth, door.interaction_half_depth)
                    else:
                        self.assertEqual(half_width, door.interaction_half_width)
                        self.assertEqual(
                            half_depth,
                            campaign.DOOR_SEAL_NORMAL_HALF_EXTENT,
                        )
                    for script_index in (1, 2, 3):
                        stop_pc = editor.get_script_pointer(
                            seal_entity, script_index
                        )
                        self.assertEqual(editor.bytecode[stop_pc], 0)

        # Exact v173 report point: the old broad e26 collider caught the next
        # northward step, while the door's X shell already included the party.
        # The campaign seal reaches only sixteen world units on x, so this point
        # can move along the vestibule without permitting a panel crossing.
        live_x, live_z = 1671.2933, 343.9499
        door = base.NATIVE_DOOR_CONTROLLERS[621][6]
        self.assertGreater(
            abs(live_x - door.x),
            2 * campaign.DOOR_SEAL_NORMAL_HALF_EXTENT,
        )
        self.assertLessEqual(
            abs(live_x - door.x),
            2 * door.interaction_half_width + 16,
        )
        self.assertLessEqual(
            abs(live_z - door.z),
            2 * door.interaction_half_depth + 16,
        )

    def test_intake_adds_three_keycard_gated_animated_examination_rooms(self) -> None:
        item = self.field_by_scene[621]
        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
        self.assertEqual(
            (
                editor.entity_count,
                struct.unpack_from("<H", item.header, 0x18C)[0],
            ),
            (49, 63),
        )

        self.assertEqual(
            tuple(
                base.mass_driver._read_field_entry(
                    editor.to_bytes(), parameter
                )
                for parameter in campaign.INTAKE_EXAM_ROOM_ENTRY_PARAMETERS
            ),
            campaign.INTAKE_EXAM_ROOM_ENTRY_ADDITIONS,
        )
        self.assertEqual(
            {
                edit.parameter: (
                    edit.playable.x,
                    edit.playable.z,
                    edit.playable.walkmesh,
                    edit.playable.camera_direction,
                    edit.playable.actor_direction,
                    edit.triangle,
                )
                for edit in item.spec.entry_edits
                if edit.parameter in campaign.INTAKE_EXAM_ROOM_ENTRY_PARAMETERS
            },
            {
                7: (1598, 1194, 0, 6, 5, 76),
                8: (1720, 840, 0, 6, 6, 81),
                9: (1720, 396, 0, 6, 6, 84),
            },
        )
        self.assertEqual(
            tuple(
                (edge.destination_field, edge.destination_parameter)
                for edge in item.spec.edges
                if edge.destination_field in (591, 592, 593)
            ),
            campaign.INTAKE_EXAM_ROOM_DESTINATIONS,
        )

        records = _actor_records(item.header)
        triangles = base._walkmesh_layer(item.components[1], 0)
        models = _indexed_entries(item.components[2])

        # Door A reuses one of Intake's one-sided panel models.  Its first
        # textured quad winds toward local -Z; the PSX-rendered front is the
        # opposite normal.  The 0x0A00 yaw therefore turns that visible face
        # toward the user's saved Fei stance while the translated origin
        # places the panel directly on the rendered diagonal-wall aperture.
        door_a_placement = campaign.INTAKE_EXAM_ROOM_MODEL_PLACEMENTS[0]
        self.assertEqual(
            door_a_placement,
            (3, 0x0A00, 3088, 0, 1463, -2, 2),
        )
        door_a_model = models[door_a_placement[0]]
        vertex_offset = struct.unpack_from("<I", door_a_model, 0x18)[0]
        mesh_offset = struct.unpack_from("<I", door_a_model, 0x20)[0]
        mesh_type, _unknown, quad_count = struct.unpack_from(
            "<BBH", door_a_model, mesh_offset
        )
        self.assertEqual((mesh_type, quad_count), (0x0D, 4))
        vertices = tuple(
            struct.unpack_from("<hhh", door_a_model, vertex_offset + index * 8)
            for index in range(struct.unpack_from("<H", door_a_model, 0x12)[0])
        )
        first_quad = struct.unpack_from("<HHHH", door_a_model, mesh_offset + 4)
        a, b, c = (vertices[first_quad[index]] for index in range(3))
        local_winding_normal_z = (b[0] - a[0]) * (c[1] - a[1]) - (
            b[1] - a[1]
        ) * (c[0] - a[0])
        self.assertEqual(local_winding_normal_z, -3872)

        x_bounds, _y_bounds, z_bounds = _single_block_model_aabb(door_a_model)
        self.assertEqual((x_bounds, z_bounds), ((822, 910), (1131, 1131)))
        local_centroid_x = sum(x_bounds) / 2
        local_centroid_z = sum(z_bounds) / 2
        yaw_radians = door_a_placement[1] * 2 * math.pi / 0x1000
        cosine = math.cos(yaw_radians)
        sine = math.sin(yaw_radians)
        world_centroid_x = (
            door_a_placement[2]
            + cosine * local_centroid_x
            + sine * local_centroid_z
        )
        world_centroid_z = (
            door_a_placement[4]
            - sine * local_centroid_x
            + cosine * local_centroid_z
        )
        self.assertAlmostEqual(world_centroid_x, 1675.91, delta=0.02)
        self.assertAlmostEqual(world_centroid_z, 1275.62, delta=0.02)
        self.assertAlmostEqual(
            world_centroid_x + world_centroid_z,
            2952,
            delta=0.50,
        )

        # The rendered/front normal is opposite the stored winding normal.
        local_front_z = -local_winding_normal_z
        world_front = (sine * local_front_z, cosine * local_front_z)
        saved_fei = (1656.65, 1252.67)
        panel_to_fei = (
            saved_fei[0] - world_centroid_x,
            saved_fei[1] - world_centroid_z,
        )
        self.assertGreater(
            world_front[0] * panel_to_fei[0]
            + world_front[1] * panel_to_fei[1],
            0,
        )

        # The two straight-wall leaves use the native architectural bays.
        # Their panels sit directly on the newly cut x=1821 wall, reproducing
        # the native leaf/wall co-planarity.  Their centers are 444 world units
        # apart, eliminating both visible protrusion and crowding.
        for placement, expected_z_bounds in zip(
            campaign.INTAKE_EXAM_ROOM_MODEL_PLACEMENTS[1:],
            ((793, 882), (352, 441)),
            strict=True,
        ):
            model = models[placement[0]]
            x_bounds, _y_bounds, z_bounds = _single_block_model_aabb(model)
            self.assertEqual(x_bounds, (88, 88))
            self.assertEqual(placement[2] + x_bounds[0], 1821)
            self.assertEqual(
                (placement[4] + z_bounds[0], placement[4] + z_bounds[1]),
                expected_z_bounds,
            )
        self.assertEqual(
            campaign.INTAKE_EXAM_ROOM_DOORS[1].z
            - campaign.INTAKE_EXAM_ROOM_DOORS[2].z,
            444,
        )

        # The three overlay doors now occupy real holes in model 1.  Only the
        # six audited wall quads change: three lower panels disappear and the
        # three panels above them retain their native texture as short caps.
        # Model 2 receives the separate allocation-neutral camera cleanup;
        # every other native model remains byte-for-byte exact.
        native_models = _indexed_entries(
            self.base_field_by_scene[621].components[2]
        )
        self.assertEqual(len(native_models), 20)
        self.assertEqual(
            tuple(
                model
                for index, model in enumerate(models[:-1])
                if index
                not in (
                    campaign.INTAKE_EXAM_ROOM_WALL_MODEL_INDEX,
                    campaign.INTAKE_EXAM_ROOM_OCCLUDER_MODEL_INDEX,
                )
            ),
            tuple(
                model
                for index, model in enumerate(native_models)
                if index
                not in (
                    campaign.INTAKE_EXAM_ROOM_WALL_MODEL_INDEX,
                    campaign.INTAKE_EXAM_ROOM_OCCLUDER_MODEL_INDEX,
                )
            ),
        )
        self.assertEqual(
            len(models) - 1,
            campaign.INTAKE_EXAM_ROOM_THRESHOLD_MODEL_INDEX,
        )
        native_wall = native_models[campaign.INTAKE_EXAM_ROOM_WALL_MODEL_INDEX]
        carved_wall = models[campaign.INTAKE_EXAM_ROOM_WALL_MODEL_INDEX]
        self.assertEqual(
            carved_wall,
            campaign._carve_intake_exam_room_wall_model(native_wall),
        )
        self.assertEqual(
            (len(carved_wall), _sha256(carved_wall)),
            (
                campaign.INTAKE_EXAM_ROOM_WALL_MODEL_SIZE,
                campaign.INTAKE_EXAM_ROOM_WALL_MODEL_SHA256,
            ),
        )

        native_occluder = native_models[
            campaign.INTAKE_EXAM_ROOM_OCCLUDER_MODEL_INDEX
        ]
        occluder = models[campaign.INTAKE_EXAM_ROOM_OCCLUDER_MODEL_INDEX]
        self.assertEqual(
            occluder,
            campaign._remove_intake_black_camera_occluders(native_occluder),
        )
        self.assertEqual(
            (len(occluder), _sha256(occluder)),
            (
                campaign.INTAKE_EXAM_ROOM_OCCLUDER_MODEL_SIZE,
                campaign.INTAKE_EXAM_ROOM_OCCLUDER_MODEL_SHA256,
            ),
        )
        self.assertEqual(
            occluder[:0x6F4],
            native_occluder[:0x6F4],
        )
        self.assertEqual(occluder[0x6F4:0x714], bytes(0x20))
        self.assertEqual(
            occluder[0x714:0x74C],
            native_occluder[0x714:0x74C],
        )
        self.assertEqual(occluder[0x74C:0xB7C], bytes(0x430))
        self.assertEqual(
            occluder[0xB7C:],
            native_occluder[0xB7C:],
        )

        def textured_wall_quads(
            model: bytes,
        ) -> tuple[
            tuple[tuple[tuple[int, int, int], ...], bytes],
            ...,
        ]:
            count = struct.unpack_from("<H", model, 0x12)[0]
            vertices_offset = struct.unpack_from("<I", model, 0x18)[0]
            wall_vertices = tuple(
                struct.unpack_from(
                    "<hhh", model, vertices_offset + index * 8
                )
                for index in range(count)
            )
            mesh_cursor = struct.unpack_from("<I", model, 0x20)[0]
            mesh_count = struct.unpack_from("<H", model, 0x16)[0]
            ft4_indices: tuple[tuple[int, int, int, int], ...] = ()
            for _mesh_index in range(mesh_count):
                kind, _unknown, primitive_count = struct.unpack_from(
                    "<BBH", model, mesh_cursor
                )
                mesh_cursor += 4
                indices = tuple(
                    struct.unpack_from(
                        "<HHHH", model, mesh_cursor + index * 8
                    )
                    for index in range(primitive_count)
                )
                mesh_cursor += primitive_count * 8
                if kind == 0x0D:
                    self.assertFalse(ft4_indices)
                    ft4_indices = indices

            display_cursor = struct.unpack_from("<I", model, 0x24)[0]
            command_sizes = {
                0x25: 8,
                0x28: 4,
                0x2D: 12,
                0xC4: 4,
                0xC8: 4,
            }
            ft4_packets: list[bytes] = []
            while display_cursor < len(model):
                command = model[display_cursor + 3]
                size = command_sizes[command]
                packet = model[display_cursor : display_cursor + size]
                if command == 0x2D:
                    ft4_packets.append(packet)
                display_cursor += size
            self.assertEqual(len(ft4_packets), len(ft4_indices))
            return tuple(
                (
                    tuple(wall_vertices[index] for index in indices),
                    packet,
                )
                for indices, packet in zip(
                    ft4_indices, ft4_packets, strict=True
                )
            )

        native_quads = textured_wall_quads(native_wall)
        carved_quads = textured_wall_quads(carved_wall)
        self.assertEqual((len(native_quads), len(carved_quads)), (434, 431))
        expected_quads = list(native_quads)
        for ordinal, first, third, packet in (
            (
                45,
                (1821, -116, 441),
                (1821, -116, 352),
                bytes.fromhex("00 00 00 2D CA 66 D6 66 CA 85 D6 85"),
            ),
            (
                54,
                (1821, -116, 882),
                (1821, -116, 793),
                bytes.fromhex("00 00 00 2D CA 66 D6 66 CA 85 D6 85"),
            ),
            (
                62,
                (1645, -116, 1307),
                (1707, -116, 1245),
                bytes.fromhex("00 00 00 2D 01 1A 01 0F 20 1A 20 0F"),
            ),
        ):
            corners = list(expected_quads[ordinal][0])
            corners[0] = first
            corners[2] = third
            expected_quads[ordinal] = (tuple(corners), packet)
        for ordinal in (63, 55, 44):
            del expected_quads[ordinal]
        self.assertEqual(carved_quads, tuple(expected_quads))

        # No retained textured polygon overlaps the open -116..0 span.  The
        # strict interval test permits only shared aperture-edge vertices.
        for corners, _packet in carved_quads:
            ys = tuple(corner[1] for corner in corners)
            if max(ys) <= -116 or min(ys) >= 0:
                continue
            xs = tuple(corner[0] for corner in corners)
            zs = tuple(corner[2] for corner in corners)
            for low, high in ((352, 441), (793, 882)):
                overlaps = min(max(zs), high) > max(min(zs), low)
                self.assertFalse(set(xs) == {1821} and overlaps)
            diagonal = set(x + z for x, _y, z in corners) == {2952}
            diagonal_overlap = min(max(xs), 1707) > max(min(xs), 1645)
            self.assertFalse(diagonal and diagonal_overlap)

        # Retail model 19 is native header node e38 (shifted to e59 after the
        # campaign's inserted actors).  Its ordinals 1/2 form e23/model 3's
        # 88-wide diagonal apron, ordinal 4 forms e24/model 4's single 89-wide
        # apron, and ordinals 0/5 are the exact companions of models 6/7.
        # Pin every source used by the three added panels before proving that
        # model 20 normalizes and places the same textured detail.
        retail_threshold = native_models[19]
        retail_vertex_offset = struct.unpack_from(
            "<I", retail_threshold, 0x18
        )[0]
        retail_mesh_offset = struct.unpack_from(
            "<I", retail_threshold, 0x20
        )[0]
        retail_display_offset = struct.unpack_from(
            "<I", retail_threshold, 0x24
        )[0]
        self.assertEqual(
            struct.unpack_from("<HHH", retail_threshold, 0x12),
            (34, 10, 1),
        )
        self.assertEqual(
            struct.unpack_from("<BBH", retail_threshold, retail_mesh_offset),
            (0x0D, 0x77, 10),
        )
        def retail_indices(ordinal: int) -> tuple[int, int, int, int]:
            return struct.unpack_from(
                "<HHHH",
                retail_threshold,
                retail_mesh_offset + 4 + ordinal * 8,
            )

        def retail_coordinates(
            indices: tuple[int, int, int, int],
        ) -> tuple[tuple[int, int, int], ...]:
            return tuple(
                struct.unpack_from(
                    "<hhh",
                    retail_threshold,
                    retail_vertex_offset + vertex * 8,
                )
                for vertex in indices
            )

        def retail_packet(ordinal: int) -> bytes:
            start = retail_display_offset + 8 + ordinal * 12
            return retail_threshold[start : start + 12]

        retail_diagonal_indices = tuple(retail_indices(ordinal) for ordinal in (1, 2))
        self.assertEqual(
            retail_diagonal_indices,
            ((12, 13, 9, 10), (9, 10, 8, 11)),
        )
        self.assertEqual(
            tuple(retail_coordinates(indices) for indices in retail_diagonal_indices),
            (
                (
                    (822, 0, 1087),
                    (822, 0, 1131),
                    (866, 0, 1087),
                    (866, 0, 1131),
                ),
                (
                    (866, 0, 1087),
                    (866, 0, 1131),
                    (910, 0, 1087),
                    (910, 0, 1131),
                ),
            ),
        )
        self.assertEqual(
            retail_threshold[retail_display_offset : retail_display_offset + 8],
            bytes.fromhex("A8 00 00 C4 00 79 00 C8"),
        )
        self.assertEqual(
            tuple(retail_packet(ordinal) for ordinal in (1, 2)),
            (
                bytes.fromhex("00 00 00 2D 97 95 97 89 A6 95 A6 89"),
                bytes.fromhex("00 00 00 2D A6 95 A6 89 B6 95 B6 89"),
            ),
        )

        retail_e24_indices = retail_indices(4)
        self.assertEqual(retail_e24_indices, (1, 2, 0, 3))
        self.assertEqual(
            retail_coordinates(retail_e24_indices),
            (
                (1601, 0, 882),
                (1645, 0, 882),
                (1601, 0, 793),
                (1645, 0, 793),
            ),
        )
        retail_full_apron_packet = bytes.fromhex(
            "00 00 00 2D B6 95 B6 89 97 95 97 89"
        )
        self.assertEqual(retail_packet(4), retail_full_apron_packet)

        retail_bc_indices = tuple(retail_indices(ordinal) for ordinal in (0, 5))
        self.assertEqual(
            retail_bc_indices,
            ((21, 22, 20, 23), (25, 26, 24, 27)),
        )
        retail_bc_coordinates = tuple(
            retail_coordinates(indices) for indices in retail_bc_indices
        )
        self.assertEqual(
            retail_bc_coordinates,
            (
                (
                    (132, 0, 793),
                    (88, 0, 793),
                    (132, 0, 882),
                    (88, 0, 882),
                ),
                (
                    (132, 0, 352),
                    (88, 0, 352),
                    (132, 0, 441),
                    (88, 0, 441),
                ),
            ),
        )
        retail_bc_packets = tuple(retail_packet(ordinal) for ordinal in (0, 5))
        self.assertEqual(
            retail_bc_packets,
            (retail_full_apron_packet, retail_full_apron_packet),
        )

        # Model 20 retains its 396-byte size and exact 0x140 GPU arena.  One
        # whole-width top-facing FT4 reproduces the retail floor tongue; all
        # fourteen retained F3 slots are zero-area, with no trailing pad.
        threshold = models[campaign.INTAKE_EXAM_ROOM_THRESHOLD_MODEL_INDEX]
        self.assertEqual(
            (len(threshold), _sha256(threshold)),
            (
                campaign.INTAKE_EXAM_ROOM_THRESHOLD_MODEL_SIZE,
                campaign.INTAKE_EXAM_ROOM_THRESHOLD_MODEL_SHA256,
            ),
        )
        self.assertEqual(
            _single_block_model_aabb(threshold),
            ((0, 89), (0, 0), (0, 44)),
        )
        self.assertEqual(
            struct.unpack_from("<HHH", threshold, 0x12),
            (15, 15, 2),
        )
        self.assertEqual(
            tuple(
                struct.unpack_from("<I", threshold, offset)[0]
                for offset in (0x18, 0x1C, 0x20, 0x24, 0x44)
            ),
            (0x48, 0x48, 0xC0, 0x140, 0x140),
        )
        threshold_vertex_offset = struct.unpack_from("<I", threshold, 0x18)[0]
        threshold_mesh_offset = struct.unpack_from("<I", threshold, 0x20)[0]
        threshold_display_offset = struct.unpack_from("<I", threshold, 0x24)[0]
        threshold_vertices = tuple(
            struct.unpack_from(
                "<hhh", threshold, threshold_vertex_offset + index * 8
            )
            for index in range(15)
        )
        self.assertEqual(
            threshold_vertices,
            (
                (0, 0, 0),
                (0, 0, 44),
                (44, 0, 0),
                (44, 0, 44),
                (89, 0, 0),
                (89, 0, 44),
                *((0, 0, 0),) * 9,
            ),
        )
        self.assertEqual(
            threshold_vertex_offset + 15 * 8,
            threshold_mesh_offset,
        )
        self.assertEqual(
            struct.unpack_from("<BBH", threshold, threshold_mesh_offset),
            (0x0D, 0x77, 1),
        )
        threshold_quads = tuple(
            struct.unpack_from(
                "<HHHH", threshold, threshold_mesh_offset + 4 + index * 8
            )
            for index in range(1)
        )
        self.assertEqual(
            threshold_quads,
            ((0, 1, 4, 5),),
        )
        triangle_group_offset = threshold_mesh_offset + 4 + 8
        self.assertEqual(
            struct.unpack_from("<BBH", threshold, triangle_group_offset),
            (0x04, 0x77, 14),
        )
        inert_triangles = tuple(
            struct.unpack_from(
                "<HHHH",
                threshold,
                triangle_group_offset + 4 + triangle_index * 8,
            )
            for triangle_index in range(14)
        )
        self.assertEqual(inert_triangles, ((0, 0, 0, 0),) * 14)
        self.assertEqual(
            triangle_group_offset + 4 + 14 * 8,
            threshold_display_offset,
        )
        self.assertEqual(
            threshold[
                threshold_display_offset : threshold_display_offset + 20
            ],
            bytes.fromhex(
                "A8 00 00 C4 00 79 00 C8 "
                "00 00 00 2D 97 89 97 8D B6 89 B6 8D"
            ),
        )
        threshold_packets = (
            threshold[
                threshold_display_offset + 8 : threshold_display_offset + 20
            ],
        )
        threshold_uv_by_local_vertex: dict[
            tuple[int, int, int], tuple[int, int]
        ] = {}
        for indices, packet in zip(
            threshold_quads, threshold_packets, strict=True
        ):
            uvs = tuple(
                (packet[offset], packet[offset + 1])
                for offset in range(4, 12, 2)
            )
            for vertex_index, uv in zip(indices, uvs, strict=True):
                vertex = threshold_vertices[vertex_index]
                if vertex in threshold_uv_by_local_vertex:
                    self.assertEqual(threshold_uv_by_local_vertex[vertex], uv)
                threshold_uv_by_local_vertex[vertex] = uv
        self.assertEqual(
            threshold_uv_by_local_vertex,
            {
                (0, 0, 0): (0x97, 0x89),
                (0, 0, 44): (0x97, 0x8D),
                (89, 0, 0): (0xB6, 0x89),
                (89, 0, 44): (0xB6, 0x8D),
            },
        )
        self.assertEqual(
            threshold[threshold_display_offset + 20 :],
            bytes.fromhex("00 00 00 20") * 14,
        )

        # The index order preserves retail's top-facing winding.  Local +Z is
        # rotated onto the far side of every aperture; the accessible hall is
        # local -Z and stays empty.
        for indices, expected_cross_y in zip(
            threshold_quads,
            (89 * 44,),
            strict=True,
        ):
            first, second, third, _fourth = (
                threshold_vertices[index] for index in indices
            )
            first_to_second = tuple(
                second[axis] - first[axis] for axis in range(3)
            )
            first_to_third = tuple(
                third[axis] - first[axis] for axis in range(3)
            )
            cross_y = (
                first_to_second[2] * first_to_third[0]
                - first_to_second[0] * first_to_third[2]
            )
            self.assertEqual(cross_y, expected_cross_y)
        self.assertTrue(all(vertex[1] == 0 for vertex in threshold_vertices))
        self.assertTrue(all(vertex[2] >= 0 for vertex in threshold_vertices))

        def world_xz(
            local_x: float,
            local_z: float,
            placement: tuple[int, int, int, int],
        ) -> tuple[float, float]:
            yaw, origin_x, _origin_y, origin_z = placement
            radians = yaw * 2.0 * math.pi / 0x1000
            cosine = math.cos(radians)
            sine = math.sin(radians)
            return (
                origin_x + cosine * local_x + sine * local_z,
                origin_z - sine * local_x + cosine * local_z,
            )

        self.assertEqual(
            campaign.INTAKE_EXAM_ROOM_THRESHOLD_PLACEMENTS,
            (
                (0x0200, 1645, 0, 1307),
                (0x0400, 1821, 0, 882),
                (0x0400, 1821, 0, 441),
            ),
        )

        # B/C use a quarter-turn and the exact model-6/model-7 translation.
        # Their four outer model-20 corners equal retail model-19 ordinals 0/5
        # after translating X by 1733.  The only texture deviation is V224's
        # deliberate far-depth clamp from the source's black row 0x95 to cyan
        # shadow row 0x8D.
        outer_local_vertices = (
            (0, 0, 0),
            (0, 0, 44),
            (89, 0, 0),
            (89, 0, 44),
        )
        for placement, source_coordinates, source_packet in zip(
            campaign.INTAKE_EXAM_ROOM_THRESHOLD_PLACEMENTS[1:],
            retail_bc_coordinates,
            retail_bc_packets,
            strict=True,
        ):
            source_uvs = tuple(
                (source_packet[offset], source_packet[offset + 1])
                for offset in range(4, 12, 2)
            )
            expected_world_uvs = {
                (x + 1733, z): (uv[0], 0x8D if uv[1] == 0x95 else uv[1])
                for (x, _y, z), uv in zip(
                    source_coordinates, source_uvs, strict=True
                )
            }
            transformed_world_uvs: dict[tuple[int, int], tuple[int, int]] = {}
            for local_vertex in outer_local_vertices:
                world_x, world_z = world_xz(
                    local_vertex[0], local_vertex[2], placement
                )
                rounded_world = (round(world_x), round(world_z))
                self.assertTrue(
                    math.isclose(world_x, rounded_world[0], abs_tol=1e-9)
                )
                self.assertTrue(
                    math.isclose(world_z, rounded_world[1], abs_tol=1e-9)
                )
                transformed_world_uvs[rounded_world] = (
                    threshold_uv_by_local_vertex[local_vertex]
                )
            self.assertEqual(transformed_world_uvs, expected_world_uvs)

        # Pin the three final model-1 hall-floor quads that meet the aperture
        # edges.  The reversed model-20 footprints occupy the opposite closed
        # half-spaces, so the two surfaces share only their leaf-plane edge and
        # can never overlap in area or z-fight in the accessible hall.
        model1_hall_floor_corners = (
            (
                (1707, 0, 1245),
                (1645, 0, 1183),
                (1645, 0, 1307),
                (1583, 0, 1245),
            ),
            (
                (1733, 0, 882),
                (1821, 0, 882),
                (1733, 0, 793),
                (1821, 0, 793),
            ),
            (
                (1733, 0, 441),
                (1821, 0, 441),
                (1733, 0, 352),
                (1821, 0, 352),
            ),
        )
        final_wall_corners = tuple(corners for corners, _packet in carved_quads)
        for corners in model1_hall_floor_corners:
            self.assertIn(corners, final_wall_corners)

        for door_index, (door, placement) in enumerate(
            zip(
                campaign.INTAKE_EXAM_ROOM_DOORS,
                campaign.INTAKE_EXAM_ROOM_THRESHOLD_PLACEMENTS,
                strict=True,
            )
        ):
            yaw, origin_x, _origin_y, origin_z = placement
            radians = yaw * 2.0 * math.pi / 0x1000
            cosine = math.cos(radians)
            sine = math.sin(radians)
            leaf_edge_centroid = world_xz(44.5, 0, placement)
            far_edge_centroid = world_xz(44.5, 44, placement)
            far_delta = (
                far_edge_centroid[0] - leaf_edge_centroid[0],
                far_edge_centroid[1] - leaf_edge_centroid[1],
            )
            footprint = tuple(
                world_xz(local_x, local_z, placement)
                for local_x, local_z in (
                    (0, 0),
                    (89, 0),
                    (0, 44),
                    (89, 44),
                )
            )
            local_controller = (
                cosine * (door.x - origin_x)
                - sine * (door.z - origin_z),
                sine * (door.x - origin_x)
                + cosine * (door.z - origin_z),
            )
            with self.subTest(threshold_world_placement=door_index):
                self.assertAlmostEqual(math.hypot(*far_delta), 44.0)
                self.assertGreaterEqual(local_controller[0], 0)
                self.assertLessEqual(local_controller[0], 89)
                self.assertLess(local_controller[1], 0)
                if door_index == 0:
                    hall_plane = max(
                        x + z
                        for x, _y, z in model1_hall_floor_corners[door_index]
                    )
                    self.assertEqual(hall_plane, 2952)
                    native_aperture_start = (1645, 1307)
                    native_aperture_end = (1707, 1245)
                    self.assertEqual(footprint[0], native_aperture_start)
                    self.assertTrue(
                        all(
                            math.isclose(x + z, hall_plane, abs_tol=0.01)
                            for x, z in footprint[:2]
                        )
                    )
                    self.assertTrue(
                        all(x + z > hall_plane for x, z in footprint[2:])
                    )
                    far_side_plane = hall_plane + 44 * math.sqrt(2)
                    self.assertAlmostEqual(far_side_plane, 3014.225397, places=6)
                    self.assertTrue(
                        all(
                            math.isclose(
                                x + z, far_side_plane, abs_tol=0.01
                            )
                            for x, z in footprint[2:]
                        )
                    )
                    self.assertGreater(far_delta[0], 0)
                    self.assertGreater(far_delta[1], 0)
                    self.assertGreater(
                        sum(far_edge_centroid), sum(leaf_edge_centroid)
                    )
                    # The shared e24-derived apron is 89 units wide, while
                    # e23/model 3's diagonal opening is 62*sqrt(2), about
                    # 87.68 units wide.  Centering is impossible with the
                    # frozen integer static-node placement, so V224 anchors
                    # the northwest endpoint exactly and accepts a harmless
                    # 1.32-unit overhang at the southeast endpoint.
                    native_aperture_width = math.dist(
                        native_aperture_start, native_aperture_end
                    )
                    lateral_overhang = math.dist(
                        footprint[1], native_aperture_end
                    )
                    self.assertAlmostEqual(
                        lateral_overhang,
                        89 - native_aperture_width,
                        places=6,
                    )
                    self.assertGreater(lateral_overhang, 1.31)
                    self.assertLess(lateral_overhang, 1.33)
                else:
                    hall_plane = max(
                        x
                        for x, _y, _z in model1_hall_floor_corners[door_index]
                    )
                    self.assertEqual(hall_plane, 1821)
                    self.assertTrue(
                        all(
                            math.isclose(x, hall_plane, abs_tol=0.01)
                            for x, _z in footprint[:2]
                        )
                    )
                    self.assertTrue(
                        all(x > hall_plane for x, _z in footprint[2:])
                    )
                    self.assertAlmostEqual(far_delta[0], 44.0)
                    self.assertAlmostEqual(far_delta[1], 0.0)
                    self.assertEqual(
                        (
                            min(x for x, _z in footprint),
                            max(x for x, _z in footprint),
                            min(z for _x, z in footprint),
                            max(z for _x, z in footprint),
                        ),
                        (
                            1821,
                            1865,
                            (793, 352)[door_index - 1],
                            (882, 441)[door_index - 1],
                        ),
                    )

        self.assertEqual(
            campaign.INTAKE_EXAM_ROOM_THRESHOLD_HEADER_ENTITIES,
            (60, 61, 62),
        )
        self.assertTrue(
            all(
                entity >= editor.entity_count
                for entity in campaign.INTAKE_EXAM_ROOM_THRESHOLD_HEADER_ENTITIES
            )
        )
        for entity, placement in zip(
            campaign.INTAKE_EXAM_ROOM_THRESHOLD_HEADER_ENTITIES,
            campaign.INTAKE_EXAM_ROOM_THRESHOLD_PLACEMENTS,
            strict=True,
        ):
            yaw, origin_x, origin_y, origin_z = placement
            self.assertEqual(
                records[entity],
                struct.pack(
                    "<Hhhh hhh H",
                    campaign.INTAKE_EXAM_ROOM_THRESHOLD_MODEL_FLAGS,
                    0,
                    yaw,
                    0,
                    origin_x,
                    origin_y,
                    origin_z,
                    campaign.INTAKE_EXAM_ROOM_THRESHOLD_MODEL_INDEX,
                ),
            )

        for (
            door,
            animation,
            controller_entity,
            helper_entity,
            placement,
        ) in zip(
            campaign.INTAKE_EXAM_ROOM_DOORS,
            campaign.INTAKE_EXAM_ROOM_ANIMATIONS,
            campaign.INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES,
            campaign.INTAKE_EXAM_ROOM_HELPER_ENTITIES,
            campaign.INTAKE_EXAM_ROOM_MODEL_PLACEMENTS,
            strict=True,
        ):
            with self.subTest(destination=door.destination_field):
                self.assertTrue(
                    base._point_inside_triangle(
                        (door.x, door.z), triangles[door.triangle]
                    )
                )
                self.assertEqual(
                    records[controller_entity],
                    base.mass_driver._field_actor_record(
                        0x01E0, door.x, door.z, 0
                    ),
                )
                (
                    model_index,
                    yaw,
                    origin_x,
                    origin_y,
                    origin_z,
                    delta_x,
                    delta_z,
                ) = placement
                self.assertEqual(
                    struct.unpack("<Hhhh hhh H", records[helper_entity]),
                    (
                        campaign.INTAKE_EXAM_ROOM_MODEL_FLAGS,
                        0,
                        yaw,
                        0,
                        origin_x,
                        origin_y,
                        origin_z,
                        model_index,
                    ),
                )

                controller_init = campaign._ghost_door_controller_init(door)
                controller_init_pc = editor.get_script_pointer(
                    controller_entity, 0
                )
                self.assertEqual(
                    editor.bytecode[
                        controller_init_pc : controller_init_pc
                        + len(controller_init)
                    ],
                    controller_init,
                )
                self.assertIn(bytes.fromhex("20 01 80 23 00"), controller_init)
                helper_init_pc = editor.get_script_pointer(helper_entity, 0)
                self.assertEqual(
                    editor.bytecode[helper_init_pc : helper_init_pc + 3],
                    b"\xBC\x2A\x00",
                )
                expected_slide = (
                    campaign._intake_exam_room_two_axis_slide_body(
                        start_x=origin_x,
                        start_z=origin_z,
                        delta_x=delta_x,
                        delta_z=delta_z,
                        iterations=campaign.INTAKE_EXAM_ROOM_SLIDE_FRAMES,
                    )
                    if delta_x and delta_z
                    else base.mass_driver._world_position_static_slide_body(
                        start_x=origin_x,
                        start_z=origin_z,
                        delta_x=delta_x,
                        delta_z=delta_z,
                        iterations=campaign.INTAKE_EXAM_ROOM_SLIDE_FRAMES,
                    )
                )
                slide_pc = editor.get_script_pointer(helper_entity, 4)
                self.assertEqual(
                    editor.bytecode[slide_pc : slide_pc + len(expected_slide)],
                    expected_slide,
                )

                gate_pc = editor.get_script_pointer(controller_entity, 2)
                locked = _run_appointment_vm(
                    editor.bytecode,
                    start_pc=gate_pc,
                    variables={campaign.SECURITY_KEYCARD_OPERAND: 0},
                )
                self.assertEqual(locked["reason"], "stop")
                self.assertEqual(
                    locked["dialogue_ids"],
                    (campaign.INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE_ID,),
                )
                self.assertEqual(locked["sound_ids"], ())
                self.assertEqual(locked["blocking_calls"], ())
                self.assertIsNone(locked["field_change"])

                unlocked = _run_appointment_vm(
                    editor.bytecode,
                    start_pc=gate_pc,
                    variables={
                        campaign.SECURITY_KEYCARD_OPERAND: (
                            campaign.SECURITY_KEYCARD_MASK
                        )
                    },
                )
                self.assertEqual(unlocked["reason"], "field_change")
                self.assertEqual(
                    unlocked["field_change"],
                    (door.destination_field, door.destination_parameter),
                )
                self.assertEqual(
                    unlocked["sound_ids"],
                    (campaign.INTAKE_EXAM_ROOM_SOUND_ID,),
                )
                self.assertEqual(
                    unlocked["blocking_calls"],
                    ((helper_entity, 0x24),),
                )
                self.assertEqual(unlocked["dialogue_ids"], ())

    def test_transfer_north_threshold_uses_the_existing_paired_blue_door(self) -> None:
        before = self.base_field_by_scene[623]
        after = self.field_by_scene[623]
        editor = ScriptEditor(after.components[base.SCRIPT_INDEX])
        self.assertEqual(
            (
                editor.entity_count,
                editor.bytecode_offset,
                editor.bytecode_size,
                struct.unpack_from("<H", after.header, 0x18C)[0],
            ),
            (45, 0x0BC4, 0x0EF7, 59),
        )

        before_records = _actor_records(before.header)
        after_records = _actor_records(after.header)
        for source_entity, leaf, expected_pcs in zip(
            campaign.TRANSFER_NORTH_DOOR_SOURCE_HELPER_ENTITIES,
            campaign.TRANSFER_NORTH_DOOR_ANIMATION.leaves,
            campaign.TRANSFER_NORTH_DOOR_HELPER_PCS,
            strict=True,
        ):
            with self.subTest(helper=leaf.helper_entity):
                self.assertEqual(
                    before_records[source_entity],
                    after_records[source_entity],
                )
                source = struct.unpack(
                    "<Hhhh hhh H", before_records[source_entity]
                )
                duplicate = struct.unpack(
                    "<Hhhh hhh H", after_records[leaf.helper_entity]
                )
                self.assertEqual(source, (0x0290, 0, 0, 0, 0, 0, 0, leaf.model_index))
                self.assertEqual(
                    duplicate,
                    (
                        0x0290,
                        0,
                        campaign.TRANSFER_NORTH_DOOR_ROTATION_Y,
                        0,
                        0,
                        0,
                        campaign.TRANSFER_NORTH_DOOR_ORIGIN_Z,
                        leaf.model_index,
                    ),
                )
                self.assertEqual(
                    (
                        editor.get_script_pointer(leaf.helper_entity, 0),
                        editor.get_script_pointer(leaf.helper_entity, 4),
                    ),
                    expected_pcs,
                )
                init_pc, slide_pc = expected_pcs
                self.assertEqual(editor.bytecode[init_pc : init_pc + 3], b"\xBC\x2A\x00")
                slide = base.mass_driver._world_position_static_slide_body(
                    start_x=0,
                    start_z=campaign.TRANSFER_NORTH_DOOR_ORIGIN_Z,
                    delta_x=leaf.delta_x,
                    delta_z=leaf.delta_z,
                    iterations=campaign.TRANSFER_NORTH_DOOR_FRAMES,
                )
                self.assertEqual(
                    editor.bytecode[slide_pc : slide_pc + len(slide)],
                    slide,
                )

        models = _indexed_entries(after.components[2])
        local_aabbs = tuple(
            _single_block_model_aabb(models[index])
            for index in campaign.TRANSFER_NORTH_DOOR_MODEL_INDICES
        )
        self.assertEqual(
            local_aabbs,
            (
                ((0, 88), (-132, 0), (-882, -882)),
                ((-88, 0), (-132, 0), (-882, -882)),
            ),
        )
        # A yaw half-turn maps (x,z) to (-x,-z), making the one-sided source
        # leaves face the party at the opposite wall while retaining z=1259.
        self.assertEqual(
            tuple(
                (
                    (-x_bounds[1], -x_bounds[0]),
                    y_bounds,
                    (
                        campaign.TRANSFER_NORTH_DOOR_ORIGIN_Z - z_bounds[1],
                        campaign.TRANSFER_NORTH_DOOR_ORIGIN_Z - z_bounds[0],
                    ),
                )
                for x_bounds, y_bounds, z_bounds in local_aabbs
            ),
            (
                ((-88, 0), (-132, 0), (1259, 1259)),
                ((0, 88), (-132, 0), (1259, 1259)),
            ),
        )
        for model_index in campaign.TRANSFER_NORTH_DOOR_MODEL_INDICES:
            model = models[model_index]
            vertex_offset = struct.unpack_from("<I", model, 0x18)[0]
            mesh_offset = struct.unpack_from("<I", model, 0x20)[0]
            mesh_type, _unknown, quad_count = struct.unpack_from(
                "<BBH", model, mesh_offset
            )
            self.assertEqual((mesh_type, quad_count), (0x0D, 2))
            vertices = tuple(
                struct.unpack_from("<hhh", model, vertex_offset + index * 8)
                for index in range(struct.unpack_from("<H", model, 0x12)[0])
            )
            first_quad = struct.unpack_from("<HHHH", model, mesh_offset + 4)
            a, b, c = (vertices[first_quad[index]] for index in range(3))
            local_normal_z = (b[0] - a[0]) * (c[1] - a[1]) - (
                b[1] - a[1]
            ) * (c[0] - a[0])
            self.assertLess(local_normal_z, 0)
            # The 0x0800 yaw is the required opposite-wall facing correction.
            self.assertGreater(-local_normal_z, 0)

        for frame in range(campaign.TRANSFER_NORTH_DOOR_FRAMES + 1):
            left = (-88 - 2 * frame, -2 * frame)
            right = (2 * frame, 88 + 2 * frame)
            self.assertLessEqual(left[1], right[0])
        self.assertEqual(left, (-152, -64))
        self.assertEqual(right, (64, 152))
        triangles = base._walkmesh_layer(after.components[1], 0)
        self.assertTrue(
            any(
                base._point_inside_triangle(
                    (0, campaign.TRANSFER_NORTH_DOOR_ORIGIN_Z), triangle
                )
                for triangle in triangles
            )
        )
        self.assertEqual(
            _sha256(after.header),
            "0439db0872d9ac68d327a29ba499283320677f6cfa4961346f8720f750edf764",
        )

        north_door = base.NATIVE_DOOR_CONTROLLERS[623][0]
        action_pc = editor.get_script_pointer(
            campaign.TRANSFER_NORTH_DOOR_CONTROLLER_ENTITY, 2
        )
        self.assertEqual(action_pc, campaign.TRANSFER_NORTH_DOOR_ACTION_PC)
        action = base._animated_door_transition_action(
            north_door,
            campaign.TRANSFER_NORTH_DOOR_ANIMATION,
            action_pc,
        )
        self.assertEqual(editor.bytecode[action_pc : action_pc + len(action)], action)
        self.assertEqual(
            action.count(
                bytes((0x74, campaign.TRANSFER_NORTH_DOOR_SOUND_ID, 0x80))
            ),
            1,
        )
        self.assertIn(bytes.fromhex("07 29 24 09 2A 24"), action)
        self.assertTrue(action.endswith(base._change_field(621, 6) + b"\x5B"))

        controller_pc = editor.get_script_pointer(
            campaign.TRANSFER_NORTH_DOOR_CONTROLLER_ENTITY, 0
        )
        controller_init = campaign._ghost_door_controller_init(north_door)
        self.assertEqual(
            editor.bytecode[controller_pc : controller_pc + len(controller_init)],
            controller_init,
        )
        contract = campaign.SURFACE_DOOR_COLLISION_CONTRACTS[623][0]
        seal_pc = editor.get_script_pointer(campaign.TRANSFER_NORTH_DOOR_SEAL_ENTITY, 0)
        seal_init = campaign._door_seal_init(north_door, contract.normal_axis)
        self.assertEqual(
            editor.bytecode[seal_pc : seal_pc + len(seal_init)],
            seal_init,
        )

    def test_all_surface_door_actions_have_no_party_walk_calls(self) -> None:
        # Frozen after the v174 campaign transforms.  OP07 is valid here only
        # for simultaneously launched door-leaf helpers; none of the 19
        # permanent Surface seals may be crossed by scripted party movement.
        audit = {
            (623, 37): (0x0E5A, ((0x0E6B, 41, 0x24),)),
            (623, 38): (0x0BD4, ((0x0BED, 39, 0x24),)),
            (621, 20): (0x0CB0, ((0x0CC1, 27, 0x24),)),
            (621, 21): (0x0CCD, ((0x0CDE, 29, 0x24),)),
            # V197 turns the marked door into the completed-Quarantine
            # shortcut; its successful branch still rejoins the native body.
            (621, 22): (campaign.INTAKE_QUARANTINE_LOCK_ACTION_PC, ()),
            # V184 interposes the phase-aware office gate, which reaches the
            # retained 0x0CEA native transition only after the doctor enters.
            (621, 23): (None, ()),
            # Both Intake-to-Service routes share the clinic keycard while
            # retaining their distinct native open-and-enter actions.
            (621, 24): (campaign.INTAKE_PATIENT_KEYCARD_GATE_ACTION_PC, ()),
            (621, 25): (0x0D1E, ()),
            # V197 keeps the freight keycard gate; its credential-set branch jumps
            # to the retained 0x0D38 native helper/transition action.
            (621, 26): (campaign.INTAKE_FREIGHT_KEYCARD_GATE_ACTION_PC, ()),
            (620, 23): (0x0A71, ()),
            # V237 validates and commits the diagnostic solve before reaching
            # the preserved native east-door animation and Service transition.
            (620, 24): (campaign.QUARANTINE_CURRENT_END_DOOR_ACTION_PC, ()),
            (624, 0): (0x133F, ()),
            (624, 1): (0x1927, ()),
            (626, 0): (0x0E4B, ()),
            (626, 1): (0x1373, ()),
            (625, 0): (0x0AD6, ()),
            (625, 6): (0x0B3D, ()),
            (622, 0): (0x1015, ()),
            (622, 26): (0x10FC, ()),
        }
        expected_endpoints = {
            (scene, contract.controller_entity)
            for scene, contracts in campaign.SURFACE_DOOR_COLLISION_CONTRACTS.items()
            for contract in contracts
        }
        self.assertEqual(set(audit), expected_endpoints)
        self.assertEqual(len(audit), 19)
        party_by_scene = {
            spec.identity.scene: {party.entity for party in spec.party}
            for spec in (*base.PLAYABLE_SCENES, *base.NATIVE_WING_SCENES)
        }

        for (scene, entity), (expected_pc, expected_async) in audit.items():
            editor = ScriptEditor(
                self.field_by_scene[scene].components[base.SCRIPT_INDEX]
            )
            with self.subTest(scene=scene, entity=entity):
                if expected_pc is None:
                    expected_pc = editor.get_script_pointer(entity, 2)
                self.assertEqual(
                    editor.get_script_pointer(entity, 2),
                    expected_pc,
                )
                decoded = _reachable_surface_action_instructions(
                    editor,
                    expected_pc,
                )
                async_calls = tuple(
                    (pc, raw[1], raw[2])
                    for pc, raw in sorted(decoded.items())
                    if raw[0] == 0x07
                )
                self.assertEqual(async_calls, expected_async)
                for _pc, target_entity, _script in async_calls:
                    self.assertNotIn(target_entity, party_by_scene[scene])

    def test_all_donor_doors_split_action_from_physical_collision(self) -> None:
        self.assertEqual(
            set(campaign.DONOR_DOOR_COLLISION_CONTRACTS),
            set(self.donor_by_scene),
        )
        blueprint_ids = {endpoint.id for endpoint in blueprint.ENDPOINTS}
        external = {
            contract.endpoint_id
            for contracts in campaign.DONOR_DOOR_COLLISION_CONTRACTS.values()
            for contract in contracts
            if contract.arrival_parameter is not None
        }
        self.assertEqual(len(external), 18)
        self.assertTrue(
            {
                "intake_exam_a.examination",
                "intake_exam_b.examination",
                "intake_exam_c.examination",
                "intake_treatment_preparation.treatment",
            }
            <= external
        )
        self.assertTrue(external <= blueprint_ids)

        seal_by_scene_and_controller: dict[tuple[int, int], int] = {}
        for scene, contracts in campaign.DONOR_DOOR_COLLISION_CONTRACTS.items():
            item = self.donor_by_scene[scene]
            editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
            first_seal = (
                campaign.CLINIC_EXIT_SEAL_ENTITY
                if scene == 550
                else editor.entity_count - len(contracts)
            )
            triangles = base._walkmesh_layer(item.components[1], 0)
            for offset, contract in enumerate(contracts):
                seal_entity = first_seal + offset
                seal_by_scene_and_controller[
                    (scene, contract.controller_entity)
                ] = seal_entity
                with self.subTest(scene=scene, controller=contract.controller_entity):
                    self.assertTrue(
                        base._point_inside_triangle(
                            (contract.x, contract.z),
                            triangles[contract.triangle],
                        )
                    )
                    carrier = campaign._ghost_donor_door_controller_init(contract)
                    carrier_pc = editor.get_script_pointer(
                        contract.controller_entity, 0
                    )
                    self.assertEqual(
                        editor.bytecode[carrier_pc : carrier_pc + len(carrier)],
                        carrier,
                    )
                    self.assertIn(bytes.fromhex("F8 00 00 20"), carrier)
                    self.assertIn(bytes.fromhex("F8 07 04 00"), carrier)
                    self.assertNotIn(bytes.fromhex("F8 03 04 00"), carrier)
                    self.assertNotIn(bytes.fromhex("F8 00 10 00"), carrier)
                    self.assertTrue(carrier.endswith(bytes.fromhex("20 01 80 00")))

                    seal = campaign._donor_seal_init(contract)
                    seal_pc = editor.get_script_pointer(seal_entity, 0)
                    self.assertEqual(
                        editor.bytecode[seal_pc : seal_pc + len(seal)],
                        seal,
                    )
                    seal_position = campaign._donor_seal_position(contract)
                    header_record = _actor_records(item.header)[seal_entity]
                    self.assertEqual(
                        struct.unpack_from("<hh", header_record, 8),
                        (seal_position[0], 0),
                    )
                    self.assertEqual(
                        struct.unpack_from("<h", header_record, 12)[0],
                        seal_position[1],
                    )
                    rectangular = contract.rectangular_seal_half_extents
                    if rectangular is None:
                        self.assertIn(bytes.fromhex("F8 04 00 20"), seal)
                        self.assertNotIn(bytes.fromhex("F8 00 00 20"), seal)
                        self.assertIn(
                            bytes((0x18, 0, 0, 0x64, contract.seal_radius)),
                            seal,
                        )
                    else:
                        self.assertIn(bytes.fromhex("F8 00 00 20"), seal)
                        self.assertNotIn(bytes.fromhex("F8 04 00 20"), seal)
                        self.assertIn(
                            bytes(
                                (
                                    0x18,
                                    rectangular[0],
                                    rectangular[1],
                                    0x64,
                                    min(rectangular),
                                )
                            ),
                            seal,
                        )
                    self.assertIn(
                        bytes.fromhex("F8 00 10 00 2A 23 00"),
                        seal,
                    )
                    release_pc = editor.get_script_pointer(seal_entity, 4)
                    self.assertEqual(
                        editor.bytecode[
                            release_pc : release_pc
                            + len(campaign.DONOR_SEAL_RELEASE_ACTION)
                        ],
                        campaign.DONOR_SEAL_RELEASE_ACTION,
                    )
                    for script_index in tuple(range(1, 4)) + tuple(range(5, 32)):
                        stop_pc = editor.get_script_pointer(
                            seal_entity, script_index
                        )
                        self.assertEqual(editor.bytecode[stop_pc], 0)

                    action_half_width, action_half_depth = (
                        campaign._donor_door_action_bounds(contract)
                    )
                    if rectangular is None:
                        effective_radius = (
                            2 * contract.seal_radius
                            + campaign.PLAYER_COLLISION_RADIUS
                        )
                        for probe in (
                            contract.closed_side_probe,
                            contract.open_side_probe,
                        ):
                            self.assertGreater(
                                math.hypot(
                                    probe[0] - seal_position[0],
                                    probe[1] - seal_position[1],
                                ),
                                effective_radius,
                            )

                        # At first round contact along the audited approach,
                        # Cross is already inside the no-facing X shell.
                        dx = contract.closed_side_probe[0] - seal_position[0]
                        dz = contract.closed_side_probe[1] - seal_position[1]
                        approach_distance = math.hypot(dx, dz)
                        contact_dx = (
                            abs(dx) * effective_radius / approach_distance
                        )
                        contact_dz = (
                            abs(dz) * effective_radius / approach_distance
                        )
                        self.assertLessEqual(
                            contact_dx,
                            2 * action_half_width
                            + campaign.PLAYER_COLLISION_RADIUS,
                        )
                        self.assertLessEqual(
                            contact_dz,
                            2 * action_half_depth
                            + campaign.PLAYER_COLLISION_RADIUS,
                        )
                        sampled_radius = effective_radius
                        sampled_rectangle = None
                    else:
                        physical_half_extents = (
                            2 * rectangular[0],
                            2 * rectangular[1],
                        )
                        for probe in (
                            contract.closed_side_probe,
                            contract.open_side_probe,
                        ):
                            self.assertTrue(
                                abs(probe[0] - seal_position[0])
                                > physical_half_extents[0]
                                or abs(probe[1] - seal_position[1])
                                > physical_half_extents[1]
                            )
                        inner_contact_z = (
                            seal_position[1] - physical_half_extents[1]
                        )
                        self.assertLessEqual(
                            abs(seal_position[0] - contract.x),
                            2 * action_half_width
                            + campaign.PLAYER_COLLISION_RADIUS,
                        )
                        self.assertLessEqual(
                            abs(inner_contact_z - contract.z),
                            2 * action_half_depth
                            + campaign.PLAYER_COLLISION_RADIUS,
                        )
                        sampled_radius = 0
                        sampled_rectangle = physical_half_extents

                    self.assertFalse(
                        _sampled_cut_is_reachable(
                            triangles,
                            contract.cut_triangles,
                            seal_position,
                            sampled_radius,
                            contract.closed_side_probe,
                            contract.open_side_probe,
                            sampled_rectangle,
                        )
                    )

        for scene, action in campaign.DONOR_NATIVE_FIELD_CHANGE_ACTIONS.items():
            entity, _old_pc, helper, player, destination, parameter = action
            editor = ScriptEditor(
                self.donor_by_scene[scene].components[base.SCRIPT_INDEX]
            )
            seal_entity = seal_by_scene_and_controller[(scene, entity)]
            action_pc = editor.get_script_pointer(entity, 2)
            output_destination, output_parameter = (
                campaign._final_route_destination(
                    scene,
                    entity,
                    (destination, parameter),
                )
            )
            if scene == 550:
                native_action = campaign._clinic_native_field_change_action(
                    destination_field=output_destination,
                    destination_parameter=output_parameter,
                    seal_entity=seal_entity,
                )
                already_open_action = (
                    campaign._clinic_post_escape_field_change_action(
                        seal_entity=seal_entity,
                    )
                )
                self.assertEqual(editor.bytecode.count(native_action), 1)
                self.assertEqual(editor.bytecode.count(already_open_action), 1)
                native_action_pc = editor.bytecode.index(native_action)
                already_open_action_pc = editor.bytecode.index(
                    already_open_action
                )
                expected = campaign._clinic_exit_gate_action(
                    native_action_pc=native_action_pc,
                    already_open_action_pc=already_open_action_pc,
                    insistence_dialogue_id=(
                        campaign.CLINIC_EXIT_INSISTENCE_DIALOGUE_ID
                    ),
                    escape_in_progress_dialogue_id=(
                        campaign.CLINIC_ESCAPE_IN_PROGRESS_DIALOGUE_ID
                    ),
                    routine_pc=action_pc,
                )
            elif scene in (567, *exam_rooms.SCENES):
                expected = campaign._clinic_native_field_change_action(
                    destination_field=output_destination,
                    destination_parameter=output_parameter,
                    seal_entity=seal_entity,
                )
            else:
                expected = campaign._donor_native_field_change_action(
                    helper_entity=helper,
                    player_script=player,
                    destination_field=output_destination,
                    destination_parameter=output_parameter,
                    seal_entity=seal_entity,
                    routine_pc=action_pc,
                    arm_appointment=(scene == 549),
                )
            with self.subTest(scene=scene, action_entity=entity):
                self.assertEqual(
                    editor.bytecode[action_pc : action_pc + len(expected)],
                    expected,
                )
                if scene == 550:
                    continue
                helper_call = (
                    bytes(
                        (
                            0x09,
                            helper,
                            0xC4 if scene in (567, *exam_rooms.SCENES) else 0x24,
                        )
                    )
                )
                self.assertLess(
                    expected.index(helper_call),
                    expected.index(bytes((0x09, seal_entity, 0x24))),
                )
                if scene in (567, *exam_rooms.SCENES):
                    self.assertLess(
                        expected.index(bytes((0x09, seal_entity, 0x24))),
                        expected.index(
                            base._change_field(
                                output_destination,
                                output_parameter,
                            )
                        ),
                    )
                    continue
                self.assertLess(
                    expected.index(bytes((0x09, seal_entity, 0x24))),
                    expected.index(bytes((0x07, 0x01, 0x20 | player))),
                )

        item565 = self.donor_by_scene[565]
        editor = ScriptEditor(item565.components[base.SCRIPT_INDEX])
        for entity, _old_pc, helper, player, destination, parameter in (
            campaign.FIELD565_FRESH_FIELD_CHANGE_ACTIONS
        ):
            action_pc = editor.get_script_pointer(entity, 2)
            seal_entity = seal_by_scene_and_controller[(565, entity)]
            if entity == campaign.FIELD565_FUTURE_LAB_HANDOFF_ENTITY:
                expected = campaign._repeatable_dialogue_action(
                    campaign.SERVICE_FUTURE_LAB_HANDOFF_DIALOGUE_ID,
                    action_pc,
                )
                with self.subTest(scene=565, action_entity=entity):
                    self.assertEqual(
                        editor.bytecode[action_pc : action_pc + len(expected)],
                        expected,
                    )
                    self.assertNotIn(bytes((0x09, helper, 0x24)), expected)
                    self.assertNotIn(
                        bytes((0x09, seal_entity, 0x24)),
                        expected,
                    )
                    self.assertNotIn(
                        base._change_field(destination, parameter),
                        expected,
                    )
                    denied = _run_appointment_vm(
                        editor.bytecode,
                        start_pc=action_pc,
                        variables={},
                    )
                    self.assertEqual(denied["reason"], "stop")
                    self.assertEqual(
                        denied["dialogue_ids"],
                        (campaign.SERVICE_FUTURE_LAB_HANDOFF_DIALOGUE_ID,),
                    )
                    self.assertEqual(denied["sound_ids"], ())
                    self.assertEqual(denied["blocking_calls"], ())
                    self.assertIsNone(denied["field_change"])
                continue
            output_destination, output_parameter = (
                campaign._final_route_destination(
                    565,
                    entity,
                    (destination, parameter),
                )
            )
            expected = campaign._donor_fresh_cross_field_change_action(
                helper_entity=helper,
                player_script=player,
                destination_field=output_destination,
                destination_parameter=output_parameter,
                routine_pc=action_pc,
                seal_entity=seal_entity,
            )
            with self.subTest(scene=565, action_entity=entity):
                self.assertEqual(
                    editor.bytecode[action_pc : action_pc + len(expected)],
                    expected,
                )

        e8_seal = seal_by_scene_and_controller[(565, 8)]
        e8_pc = editor.get_script_pointer(8, 2)
        e8_expected = campaign._donor_native_field_change_action(
            helper_entity=13,
            player_script=8,
            destination_field=589,
            destination_parameter=0,
            seal_entity=e8_seal,
        )
        self.assertEqual(
            editor.bytecode[e8_pc : e8_pc + len(e8_expected)],
            e8_expected,
        )

        # e5 retains both campaign gates; only their successful fallthrough
        # redirects to a new action that releases this one seal.
        production_outer = campaign._gate_existing_action(
            requirements=(
                (
                    campaign.SECURITY_KEYCARD_OPERAND,
                    campaign.SECURITY_KEYCARD_MASK,
                ),
                (campaign.TONE_OPERAND, campaign.TONE_MASK),
                (campaign.STATE_OPERAND, campaign.QUARANTINE_MASK),
                (campaign.STATE_OPERAND, campaign.INTERFACE_BIT_MASK),
            ),
            old_action_pc=0x064C,
            denial_dialogue_id=12,
            routine_pc=0x07D3,
        )
        self.assertEqual(
            editor.bytecode[0x07D3 : 0x07D3 + len(production_outer)],
            production_outer,
        )
        inner_gate = base._field565_quarantine_exit_action(0x064C)
        self.assertEqual(editor.bytecode[0x064C:0x0654], inner_gate[:8])
        self.assertEqual(
            editor.bytecode[0x0671:0x068A],
            base._field565_repeatable_dialogue_action(11, 0x0671),
        )
        production_pc = editor.get_script_pointer(5, 2)
        production_seal = seal_by_scene_and_controller[(565, 5)]
        production_expected = campaign._donor_fresh_cross_field_change_action(
            helper_entity=16,
            player_script=5,
            destination_field=stabilization590.SCENE,
            destination_parameter=0,
            routine_pc=production_pc,
            seal_entity=production_seal,
        )
        self.assertEqual(
            editor.bytecode[
                production_pc : production_pc + len(production_expected)
            ],
            production_expected,
        )

        quarantine_gate = campaign._gate_existing_action(
            requirements=(
                (
                    campaign.QUARANTINE_KEYCARD_OPERAND,
                    campaign.QUARANTINE_KEYCARD_MASK,
                ),
            ),
            old_action_pc=0x035D,
            denial_dialogue_id=13,
            routine_pc=0x07AF,
        )
        self.assertEqual(editor.bytecode[0x07AF:0x07B7], quarantine_gate[:8])
        self.assertEqual(editor.bytecode[0x07BA:0x07D3], quarantine_gate[11:])
        quarantine_pc = struct.unpack_from("<H", editor.bytecode, 0x07B8)[0]
        quarantine_seal = seal_by_scene_and_controller[(565, 10)]
        quarantine_expected = campaign._donor_fresh_cross_field_change_action(
            helper_entity=15,
            player_script=10,
            destination_field=620,
            destination_parameter=1,
            routine_pc=quarantine_pc,
            seal_entity=quarantine_seal,
        )
        self.assertEqual(
            editor.bytecode[
                quarantine_pc : quarantine_pc + len(quarantine_expected)
            ],
            quarantine_expected,
        )

        e11_seal = seal_by_scene_and_controller[(565, 11)]
        e11_pc = editor.get_script_pointer(11, 2)
        e11_expected = campaign._field565_internal_gate_action_with_seal(
            e11_seal
        )
        self.assertEqual(
            editor.bytecode[e11_pc : e11_pc + len(e11_expected)],
            e11_expected,
        )
        e12_seal = seal_by_scene_and_controller[(565, 12)]
        e12_pc = editor.get_script_pointer(12, 2)
        self.assertEqual(e12_pc, base.FIELD565_TONE_GATE_ACTION_PC)

        # The saved door is once again the complete native directional-input
        # puzzle.  Its action body remains byte-identical to the checked V201
        # foundation, including the accepted Up/Down/Up/Left/Right values and
        # the persistent tone-authorization write on the success path.
        foundation = ScriptEditor(
            self.base_donor_by_scene[565].components[base.SCRIPT_INDEX]
        )
        self.assertEqual(
            editor.bytecode[e12_pc:0x053D],
            foundation.bytecode[e12_pc:0x053D],
        )
        accepted_input = bytes.fromhex(
            "02 0C 04 01 00 40 68 04 "
            "02 0E 04 02 00 40 68 04 "
            "02 10 04 01 00 40 68 04 "
            "02 12 04 04 00 40 68 04 "
            "02 14 04 03 00 40 68 04"
        )
        native_action = editor.bytecode[e12_pc:0x053D]
        self.assertIn(accepted_input, native_action)
        self.assertEqual(
            native_action.count(
                campaign._set_bit(
                    campaign.TONE_OPERAND,
                    campaign.TONE_BIT_INDEX,
                )
            ),
            1,
        )
        self.assertIn(bytes.fromhex("09 15 24 80 99 00 00 80"), native_action)

        # Only the two authentic success exits are extended.  Each detour
        # releases the new round seal, ghosts the native carrier, and rejoins
        # its original success continuation.  All failed-input branches stay
        # inside the byte-identical native action above and cannot reach these
        # out-of-line routines.
        for trampoline_pc, return_pc in ((0x069E, 0x053C), (0x06A4, 0x051D)):
            with self.subTest(tone_trampoline=trampoline_pc):
                patched = editor.bytecode[trampoline_pc : trampoline_pc + 6]
                self.assertEqual(patched[0], 0x01)
                expanded_pc = struct.unpack_from("<H", patched, 1)[0]
                self.assertEqual(patched[3:], b"\x00\x00\x00")
                expected = campaign._field565_gate_clearance_trampoline(
                    e12_seal,
                    return_pc,
                )
                self.assertEqual(
                    editor.bytecode[expanded_pc : expanded_pc + len(expected)],
                    expected,
                )
                self.assertEqual(
                    expected,
                    b"\x09" + bytes((e12_seal, 0x24))
                    + bytes.fromhex("20 01 80 01")
                    + struct.pack("<H", return_pc),
                )

    def test_field565_outer_spokes_have_wide_targets_and_safe_arrivals(
        self,
    ) -> None:
        item = self.donor_by_scene[565]
        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
        triangles = base._walkmesh_layer(item.components[1], 0)
        contracts = campaign.DONOR_DOOR_COLLISION_CONTRACTS[565]
        contract_by_parameter = {
            contract.arrival_parameter: contract
            for contract in contracts
            if contract.arrival_parameter is not None
        }
        expected_arrivals = {
            0: ((33, -33), 75),
            1: ((4813, -3671), 8),
            2: ((4190, -3044), 12),
            3: ((3570, -2430), 17),
            4: ((1152, -4468), 57),
            5: ((2970, -4520), 64),
            6: ((3270, -5718), 68),
        }
        active_arrivals = {
            parameter: values
            for parameter, values in expected_arrivals.items()
            if parameter != 3
        }
        self.assertEqual(set(contract_by_parameter), set(active_arrivals))
        self.assertEqual(
            {contract.controller_entity for contract in contract_by_parameter.values()},
            {4, 5, 6, 8, 9, 10},
        )
        dormant_handoff = next(
            contract
            for contract in contracts
            if contract.controller_entity
            == campaign.FIELD565_FUTURE_LAB_HANDOFF_ENTITY
        )
        self.assertEqual(
            (
                dormant_handoff.endpoint_id,
                dormant_handoff.arrival_parameter,
                dormant_handoff.closed_side_probe,
                dormant_handoff.open_side_probe,
            ),
            (
                "field565.future_lab_handoff_sealed",
                None,
                expected_arrivals[3][0],
                (3700, -2300),
            ),
        )
        self.assertNotIn(
            dormant_handoff.endpoint_id,
            {endpoint.id for endpoint in blueprint.ENDPOINTS},
        )

        first_seal = editor.entity_count - len(contracts)
        for parameter, (position, triangle) in expected_arrivals.items():
            contract = (
                dormant_handoff
                if parameter == 3
                else contract_by_parameter[parameter]
            )
            entry_pc = 1 + 7 * parameter
            x, z, walkmesh, _camera, _actor = struct.unpack_from(
                "<hhBBB",
                editor.bytecode,
                entry_pc,
            )
            with self.subTest(parameter=parameter, controller=contract.controller_entity):
                self.assertEqual((x, z, walkmesh), (*position, 0))
                self.assertEqual(contract.closed_side_probe, position)
                self.assertEqual(
                    tuple(
                        index
                        for index, candidate in enumerate(triangles)
                        if base._point_inside_triangle(position, candidate)
                    ),
                    (triangle,),
                )
                self.assertIn((parameter, triangle), item.entry_triangles)

                # Keep the checked donor's narrow 0x0A source bounds as
                # provenance, but emit a substantially more forgiving 0x18
                # no-facing action shell.  Collision remains on the separate
                # round seal rather than growing with the X target.
                self.assertEqual(
                    (
                        contract.interaction_half_width,
                        contract.interaction_half_depth,
                        campaign._donor_door_action_bounds(contract),
                    ),
                    (0x0A, 0x0A, (0x18, 0x18)),
                )
                carrier = campaign._ghost_donor_door_controller_init(contract)
                self.assertIn(bytes.fromhex("18 18 18 1E 00"), carrier)
                seal_entity = first_seal + contracts.index(contract)
                seal = campaign._donor_circle_seal_init(contract)
                seal_pc = editor.get_script_pointer(seal_entity, 0)
                self.assertEqual(
                    editor.bytecode[seal_pc : seal_pc + len(seal)],
                    seal,
                )
                self.assertIn(bytes.fromhex("18 00 00 64 0E"), seal)

                # A field transition made while Cross is still held must not
                # immediately select either the reciprocal leaf or another
                # manifold carrier.  OP18 doubles each action operand and the
                # player contributes a further 16 units on both axes.
                candidates = []
                for candidate in contracts:
                    half_width, half_depth = (
                        campaign._donor_door_action_bounds(candidate)
                    )
                    if (
                        abs(x - candidate.x)
                        <= 2 * half_width + campaign.PLAYER_COLLISION_RADIUS
                        and abs(z - candidate.z)
                        <= 2 * half_depth + campaign.PLAYER_COLLISION_RADIUS
                    ):
                        candidates.append(candidate.controller_entity)
                self.assertEqual(candidates, [])

    def test_recovered_field590_routes_collisions_and_production_gate(
        self,
    ) -> None:
        item = self.donor_by_scene[stabilization590.SCENE]
        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
        triangles = base._walkmesh_layer(item.components[1], 0)
        contracts = campaign.DONOR_DOOR_COLLISION_CONTRACTS[
            stabilization590.SCENE
        ]
        self.assertEqual(
            tuple(contract.controller_entity for contract in contracts),
            (
                reserved_donor567.LOBBY_CONTROLLER,
                reserved_donor567.SERVICE_CONTROLLER,
                reserved_donor567.RESTRICTED_CONTROLLER,
            ),
        )
        self.assertEqual(
            tuple(contract.arrival_parameter for contract in contracts),
            stabilization590.ENTRY_PARAMETERS,
        )
        self.assertEqual(
            {contract.endpoint_id for contract in contracts},
            {
                endpoint.id
                for endpoint in blueprint.ENDPOINTS
                if endpoint.field == stabilization590.SCENE
            },
        )

        first_seal = editor.entity_count - len(contracts)
        for offset, contract in enumerate(contracts):
            parameter = contract.arrival_parameter
            self.assertIsNotNone(parameter)
            assert parameter is not None
            entry_pc = 1 + 7 * parameter
            x, z, walkmesh, camera, actor = struct.unpack_from(
                "<hhBBB",
                editor.bytecode,
                entry_pc,
            )
            with self.subTest(parameter=parameter, controller=contract.controller_entity):
                self.assertEqual(
                    (x, z),
                    stabilization590.ENTRY_POSITIONS[parameter],
                )
                self.assertEqual(
                    (walkmesh, camera, actor),
                    (
                        stabilization590.ENTRY_WALKMESH,
                        *stabilization590.ENTRY_DIRECTIONS[parameter],
                    ),
                )
                self.assertEqual(contract.closed_side_probe, (x, z))
                self.assertEqual(
                    tuple(
                        index
                        for index, triangle in enumerate(triangles)
                        if base._point_inside_triangle((x, z), triangle)
                    ),
                    (stabilization590.ENTRY_TRIANGLES[parameter],),
                )
                self.assertIn(
                    (
                        parameter,
                        stabilization590.ENTRY_TRIANGLES[parameter],
                    ),
                    item.entry_triangles,
                )
                self.assertEqual(
                    (
                        contract.interaction_half_width,
                        contract.interaction_half_depth,
                        campaign._donor_door_action_bounds(contract),
                    ),
                    (
                        *reserved_donor567.CONTROLLER_INTERACTION_HALF_EXTENTS,
                        (
                            stabilization590.ACTION_HALF_EXTENT,
                            stabilization590.ACTION_HALF_EXTENT,
                        ),
                    ),
                )
                carrier = campaign._ghost_donor_door_controller_init(contract)
                self.assertIn(bytes.fromhex("18 24 24 1E 00"), carrier)
                seal_entity = first_seal + offset
                seal = campaign._donor_circle_seal_init(contract)
                seal_pc = editor.get_script_pointer(seal_entity, 0)
                self.assertEqual(
                    editor.bytecode[seal_pc : seal_pc + len(seal)],
                    seal,
                )

                # Every arrival lies outside every widened target, not merely
                # its reciprocal one.  This proves a held Cross cannot bounce
                # the party through either neighboring ward door.
                candidates = []
                for candidate in contracts:
                    half_width, half_depth = (
                        campaign._donor_door_action_bounds(candidate)
                    )
                    if (
                        abs(x - candidate.x)
                        <= 2 * half_width + campaign.PLAYER_COLLISION_RADIUS
                        and abs(z - candidate.z)
                        <= 2 * half_depth + campaign.PLAYER_COLLISION_RADIUS
                    ):
                        candidates.append(candidate.controller_entity)
                self.assertEqual(candidates, [])

        route_specs = {
            reserved_donor567.LOBBY_CONTROLLER: (
                reserved_donor567.LOBBY_ASYNC_HELPER,
                reserved_donor567.LOBBY_BLOCKING_HELPER,
                reserved_donor567.LOBBY_PLAYER_SCRIPT,
                stabilization590.MANIFOLD_BULKHEAD_DESTINATION,
            ),
            reserved_donor567.SERVICE_CONTROLLER: (
                reserved_donor567.SERVICE_ASYNC_HELPER,
                reserved_donor567.SERVICE_BLOCKING_HELPER,
                reserved_donor567.SERVICE_PLAYER_SCRIPT,
                stabilization590.MANIFOLD_STAFF_DESTINATION,
            ),
        }
        for controller, (
            async_helper,
            blocking_helper,
            player_script,
            destination,
        ) in route_specs.items():
            offset = next(
                index
                for index, contract in enumerate(contracts)
                if contract.controller_entity == controller
            )
            seal_entity = first_seal + offset
            action_pc = editor.get_script_pointer(controller, 2)
            action = campaign._field567_fresh_cross_field_change_action(
                async_helper_entity=async_helper,
                blocking_helper_entity=blocking_helper,
                player_script=player_script,
                destination_field=destination[0],
                destination_parameter=destination[1],
                routine_pc=action_pc,
                seal_entity=seal_entity,
            )
            with self.subTest(return_controller=controller):
                self.assertEqual(
                    editor.bytecode[action_pc : action_pc + len(action)],
                    action,
                )
                result = _run_appointment_vm(
                    editor.bytecode,
                    start_pc=action_pc,
                    variables={},
                )
                self.assertEqual(result["field_change"], destination)
                self.assertEqual(
                    result["blocking_calls"],
                    ((blocking_helper, 0x24), (seal_entity, 0x24)),
                )

        production_controller = reserved_donor567.RESTRICTED_CONTROLLER
        production_offset = next(
            index
            for index, contract in enumerate(contracts)
            if contract.controller_entity == production_controller
        )
        production_seal = first_seal + production_offset
        production_pc = editor.get_script_pointer(production_controller, 2)
        denied = _run_appointment_vm(
            editor.bytecode,
            start_pc=production_pc,
            menu_choices={3: 1},
            variables={
                campaign.SECURITY_KEYCARD_OPERAND: 0,
                campaign.TONE_OPERAND: campaign.TONE_MASK,
                campaign.STATE_OPERAND: (
                    campaign.QUARANTINE_MASK | campaign.INTERFACE_BIT_MASK
                ),
            },
        )
        self.assertEqual(
            denied["dialogue_ids"],
            (3, stabilization590.PRODUCTION_DENIAL_DIALOGUE_ID),
        )
        self.assertIsNone(denied["field_change"])
        self.assertEqual(denied["blocking_calls"], ())

        admitted = _run_appointment_vm(
            editor.bytecode,
            start_pc=production_pc,
            menu_choices={3: 1},
            variables={
                campaign.SECURITY_KEYCARD_OPERAND: (
                    campaign.SECURITY_KEYCARD_MASK
                ),
                campaign.TONE_OPERAND: campaign.TONE_MASK,
                campaign.STATE_OPERAND: (
                    campaign.QUARANTINE_MASK | campaign.INTERFACE_BIT_MASK
                ),
            },
        )
        self.assertEqual(
            admitted["field_change"],
            stabilization590.SORTING_DESTINATION,
        )
        self.assertEqual(
            admitted["blocking_calls"],
            (
                (reserved_donor567.RESTRICTED_BLOCKING_HELPER, 0x24),
                (production_seal, 0x24),
            ),
        )
        blocks = parse_dialogue(item.components[7]).blocks
        self.assertEqual(
            blocks[stabilization590.PRODUCTION_DENIAL_DIALOGUE_ID].text,
            stabilization590.PRODUCTION_DENIAL_DIALOGUE,
        )

    def test_field567_is_an_empty_examination_annex_and_field565_e6_is_expansion_route(
        self,
    ) -> None:
        clinic = self.donor_by_scene[567]
        editor = ScriptEditor(clinic.components[base.SCRIPT_INDEX])
        contracts = campaign.DONOR_DOOR_COLLISION_CONTRACTS[567]
        self.assertEqual(len(contracts), 1)
        contract = contracts[0]
        self.assertEqual(
            (
                contract.endpoint_id,
                contract.controller_entity,
                contract.arrival_parameter,
                contract.closed_side_probe,
                contract.open_side_probe,
            ),
            (
                empty_clinic567.DOOR_ENDPOINT_ID,
                empty_clinic567.RETURN_CONTROLLER,
                empty_clinic567.ENTRY_PARAMETER,
                empty_clinic567.DOOR_CLOSED_SIDE_PROBE,
                empty_clinic567.DOOR_OPEN_SIDE_PROBE,
            ),
        )
        seal_entity = editor.entity_count - 1
        self.assertEqual(seal_entity, empty_clinic567.SOURCE_ENTITY_COUNT)
        self.assertEqual(
            campaign.DONOR_NATIVE_FIELD_CHANGE_ACTIONS[567],
            empty_clinic567.RETURN_ROUTE,
        )

        action_pc = editor.get_script_pointer(
            empty_clinic567.RETURN_CONTROLLER,
            2,
        )
        action = campaign._clinic_native_field_change_action(
            destination_field=621,
            destination_parameter=4,
            seal_entity=seal_entity,
        )
        self.assertEqual(
            editor.bytecode[action_pc : action_pc + len(action)],
            action,
        )
        helper_call = bytes(
            (0x09, empty_clinic567.RETURN_HELPER, 0xC4)
        )
        release = bytes((0x09, seal_entity, 0x24))
        transition = base._change_field(621, 4)
        self.assertLess(action.index(helper_call), action.index(release))
        self.assertLess(action.index(release), action.index(transition))
        self.assertTrue(action.endswith(transition + b"\x00"))
        self.assertNotIn(b"\xD2", action)
        self.assertNotIn(b"\xF5", action)
        self.assertNotIn(b"\xFE\x84", action)

        helper_pc = editor.get_script_pointer(
            empty_clinic567.RETURN_HELPER,
            empty_clinic567.RETURN_HELPER_SCRIPT_INDEX,
        )
        self.assertEqual(helper_pc, empty_clinic567.RETURN_HELPER_PC)
        self.assertEqual(
            editor.bytecode[
                helper_pc : helper_pc + len(empty_clinic567.RETURN_HELPER_BODY)
            ],
            empty_clinic567.RETURN_HELPER_BODY,
        )

        # Campaign clearance and music extend the empty clinic with only the
        # read-only workstation, door seal, and music wrapper.  Its field-352
        # bed, walkmesh, models, encounter formations, and graphics remain
        # intact.
        self.assertEqual(clinic.graphics, self.base_567.graphics)
        for component_index in (0, 1, 2, 3, 4, 6, 8):
            with self.subTest(preserved_component=component_index):
                self.assertEqual(
                    clinic.components[component_index],
                    self.base_567.components[component_index],
                )
        models = base.mass_driver._indexed_bundle_entries(
            clinic.components[base.mass_driver.MODEL_INDEX]
        )
        self.assertEqual(
            (
                len(models[empty_clinic567.BED_MODEL_INDEX]),
                _sha256(models[empty_clinic567.BED_MODEL_INDEX]),
            ),
            empty_clinic567.BED_MODEL_IDENTITY,
        )
        installed_bed_node = empty_clinic567.BED_HEADER_NODE + len(contracts)
        bed_offset = 0x190 + installed_bed_node * 16
        self.assertEqual(
            clinic.header[bed_offset : bed_offset + 16],
            empty_clinic567.BED_HEADER_RECORD,
        )
        source_bed_offset = 0x190 + empty_clinic567.BED_HEADER_NODE * 16
        self.assertEqual(
            clinic.header[bed_offset : bed_offset + 16],
            self.base_567.header[source_bed_offset : source_bed_offset + 16],
        )
        self.assertEqual((editor.entity_count, len(_actor_records(clinic.header))), (20, 34))
        self.assertEqual(EncounterTable(clinic.components[6]).weights, (0,) * 16)
        terminalized = exam_rooms.prepare_empty_room_terminal(self.base_567)
        self.assertEqual(clinic.components[7], terminalized.components[7])
        self.assertEqual(
            parse_dialogue(clinic.components[7]).blocks[
                exam_rooms.EMPTY_ROOM_TERMINAL_DIALOGUE_ID
            ].text,
            exam_rooms.EMPTY_ROOM_TERMINAL_DIALOGUE,
        )

        # Every retired doctor/NPC/story slot remains stopped.  Only e4/e5/e6
        # gain read-only workstation slots; e0:s1 stays inert and the physical
        # seal remains the sole new actor.
        terminal_slots = {
            (entity, script_index)
            for entity in exam_rooms.EMPTY_ROOM_TERMINAL_ENTITIES
            for script_index in (0, 2)
        }
        for entity in range(empty_clinic567.SOURCE_ENTITY_COUNT):
            for script_index in range(32):
                if (entity, script_index) in (
                    empty_clinic567.FINAL_ACTIVE_SLOTS | terminal_slots
                ):
                    continue
                with self.subTest(retired_entity=entity, slot=script_index):
                    self.assertEqual(
                        editor.get_script_pointer(entity, script_index),
                        empty_clinic567.SHARED_STOP_PC,
                    )
        for entity in empty_clinic567.RETIRED_NPC_ENTITIES:
            for script_index in range(32):
                self.assertEqual(
                    editor.get_script_pointer(entity, script_index),
                    empty_clinic567.SHARED_STOP_PC,
                )
        self.assertIn(
            empty_clinic567.DOCTOR_ENTITY,
            empty_clinic567.RETIRED_NPC_ENTITIES,
        )
        self.assertEqual(
            editor.get_script_pointer(empty_clinic567.GLOBAL_ENTITY, 1),
            empty_clinic567.SHARED_STOP_PC,
        )
        self.assertEqual(
            tuple(
                editor.get_script_pointer(entity, 0)
                for entity in exam_rooms.EMPTY_ROOM_TERMINAL_ENTITIES
            ),
            exam_rooms.EMPTY_ROOM_TERMINAL_INIT_PCS,
        )
        self.assertEqual(
            {
                editor.get_script_pointer(entity, 2)
                for entity in exam_rooms.EMPTY_ROOM_TERMINAL_ENTITIES
            },
            {exam_rooms.EMPTY_ROOM_TERMINAL_ACTION_PC},
        )

        # The former field-565 dead staff threshold is now the second route
        # into the recovered stabilization ward.  It retains the authentic
        # e17 leaf helper and Fei movement script, releases only its own seal,
        # and uses a fresh-Cross wrapper before changing field.
        editor565 = ScriptEditor(
            self.donor_by_scene[565].components[base.SCRIPT_INDEX]
        )
        contracts565 = campaign.DONOR_DOOR_COLLISION_CONTRACTS[565]
        staff_offset, staff_contract = next(
            (offset, item)
            for offset, item in enumerate(contracts565)
            if item.controller_entity == 6
        )
        self.assertEqual(staff_contract.arrival_parameter, 2)
        self.assertEqual(staff_contract.closed_side_probe, (4190, -3044))
        staff_endpoint = next(
            endpoint
            for endpoint in blueprint.ENDPOINTS
            if (
                endpoint.field,
                endpoint.local_entry_parameter,
                endpoint.destination_field,
                endpoint.destination_entry_parameter,
            )
            == (565, 2, stabilization590.SCENE, 1)
        )
        self.assertEqual(staff_contract.endpoint_id, staff_endpoint.id)
        staff_seal = editor565.entity_count - len(contracts565) + staff_offset
        staff_pc = editor565.get_script_pointer(6, 2)
        self.assertNotEqual(staff_pc, 0x0612)
        staff_route = next(
            route
            for route in campaign.FIELD565_FRESH_FIELD_CHANGE_ACTIONS
            if route[0] == 6
        )
        self.assertEqual(
            staff_route,
            # Freeze the authentic donor foundation independently of the
            # campaign destination.  The checked source action still names
            # its former 621/p4 route; _final_route_destination owns the ward
            # retarget without weakening that byte-level source check.
            (6, 0x0612, 17, 6, 621, 4),
        )
        staff_action = campaign._donor_fresh_cross_field_change_action(
            helper_entity=17,
            player_script=6,
            destination_field=stabilization590.SCENE,
            destination_parameter=1,
            routine_pc=staff_pc,
            seal_entity=staff_seal,
        )
        self.assertEqual(
            editor565.bytecode[staff_pc : staff_pc + len(staff_action)],
            staff_action,
        )
        helper_call = bytes((0x09, 17, 0x24))
        release_call = bytes((0x09, staff_seal, 0x24))
        player_walk = bytes((0x07, 0x01, 0x26))
        transition = base._change_field(stabilization590.SCENE, 1)
        self.assertTrue(staff_action.startswith(bytes.fromhex("33 FE 54")))
        self.assertLess(staff_action.index(helper_call), staff_action.index(release_call))
        self.assertLess(staff_action.index(release_call), staff_action.index(player_walk))
        self.assertLess(staff_action.index(player_walk), staff_action.index(transition))
        self.assertTrue(staff_action.endswith(transition + b"\x5B"))
        self.assertEqual(
            campaign._final_route_destination(
                565,
                6,
                (621, 4),
            ),
            (stabilization590.SCENE, 1),
        )
        staff_release_pc = editor565.get_script_pointer(staff_seal, 4)
        self.assertEqual(
            editor565.bytecode[
                staff_release_pc :
                staff_release_pc + len(campaign.DONOR_SEAL_RELEASE_ACTION)
            ],
            campaign.DONOR_SEAL_RELEASE_ACTION,
        )
        self.assertEqual(
            editor565.bytecode.count(bytes((0x09, staff_seal, 0x24))),
            1,
        )

        intake_retarget = next(
            retarget
            for retarget in campaign.ROOM_SWAP_RETARGETS
            if (retarget.field, retarget.controller_entity) == (621, 25)
        )
        self.assertEqual(intake_retarget.destination, (567, 0))
        editor621 = ScriptEditor(
            self.field_by_scene[621].components[base.SCRIPT_INDEX]
        )
        self.assertEqual(
            editor621.get_script_pointer(25, 2),
            intake_retarget.action_pc,
        )
        self.assertEqual(
            editor621.bytecode[
                intake_retarget.change_pc : intake_retarget.change_pc + 5
            ],
            base._change_field(567, 0),
        )

    def test_live_room_swap_foundations_and_current_room_routes(self) -> None:
        expected = {
            (621, 21): ((620, 0), (549, 0), 0x0CCD, 0x0CE4),
            (621, 22): ((549, 0), (620, 0), 0x0D52, 0x0D66),
            (621, 25): ((565, 2), (567, 0), 0x0D1E, 0x0D32),
            (621, 26): ((565, 3), (594, 0), 0x0D38, 0x0D4C),
            (620, 23): ((621, 0), (621, 2), 0x0A71, 0x0A85),
            (624, 0): ((565, 1), (590, 2), 0x133F, 0x1341),
            (565, 5): ((624, 0), (590, 0), None, None),
            (565, 6): ((621, 4), (590, 1), None, None),
            (588, 17): ((621, 5), (565, 5), None, None),
            (549, 6): ((621, 2), (621, 0), None, None),
        }
        self.assertEqual(
            {
                (item.field, item.controller_entity): (
                    item.source_destination,
                    item.destination,
                    item.action_pc,
                    item.change_pc,
                )
                for item in campaign.ROOM_SWAP_RETARGETS
            },
            expected,
        )

        # Slot 1 (SHA-256 492d9aeb...) freezes the user's Step-3 stance.  Its
        # exact fixed-point position lies inside only e22's action rectangle.
        live_x = 4_473_931 / 65_536
        live_z = 54_433_643 / 65_536
        candidates = []
        for offset, door in enumerate(base.NATIVE_DOOR_CONTROLLERS[621]):
            if (
                abs(live_x - door.x)
                <= 2 * door.interaction_half_width
                + campaign.PLAYER_COLLISION_RADIUS
                and abs(live_z - door.z)
                <= 2 * door.interaction_half_depth
                + campaign.PLAYER_COLLISION_RADIUS
            ):
                candidates.append(20 + offset)
        self.assertEqual(candidates, [22])
        self.assertEqual(
            (
                base.NATIVE_DOOR_CONTROLLERS[621][2].x,
                base.NATIVE_DOOR_CONTROLLERS[621][2].z,
                base.NATIVE_DOOR_CONTROLLERS[621][2].triangle,
            ),
            (88, 840, 18),
        )

        helpers = {
            (621, 21): 30,
            (621, 22): 2,
            (621, 25): 33,
            (621, 26): 34,
            (620, 23): 25,
        }
        prepared = self.field_by_scene | self.donor_by_scene
        for retarget in campaign.ROOM_SWAP_RETARGETS:
            editor = ScriptEditor(
                prepared[retarget.field].components[base.SCRIPT_INDEX]
            )
            with self.subTest(
                field=retarget.field,
                entity=retarget.controller_entity,
            ):
                key = (retarget.field, retarget.controller_entity)
                if key == (549, 6):
                    # Donor collision separation appends an active wrapper
                    # that releases its physical seal before changing field.
                    # It consequently has no stable in-place action/change PC.
                    self.assertIsNone(retarget.action_pc)
                    self.assertIsNone(retarget.change_pc)
                    wrapper_pc = editor.get_script_pointer(6, 2)
                    seal_entity = editor.entity_count - 1
                    wrapper = campaign._donor_native_field_change_action(
                        helper_entity=7,
                        player_script=4,
                        destination_field=621,
                        destination_parameter=0,
                        seal_entity=seal_entity,
                        routine_pc=wrapper_pc,
                        arm_appointment=True,
                    )
                    self.assertEqual(
                        editor.bytecode[wrapper_pc : wrapper_pc + len(wrapper)],
                        wrapper,
                    )
                elif key in ((565, 5), (565, 6)):
                    # These donor leaves use newly appended fresh-X wrappers.
                    # Their checked source bodies remain frozen, so there is no
                    # stable in-place change operand to patch.
                    self.assertIsNone(retarget.action_pc)
                    self.assertIsNone(retarget.change_pc)
                    helper, player, destination = {
                        (565, 5): (16, 5, (590, 0)),
                        (565, 6): (17, 6, (590, 1)),
                    }[key]
                    wrapper_pc = editor.get_script_pointer(
                        retarget.controller_entity,
                        2,
                    )
                    contracts = campaign.DONOR_DOOR_COLLISION_CONTRACTS[565]
                    offset = next(
                        index
                        for index, contract in enumerate(contracts)
                        if contract.controller_entity
                        == retarget.controller_entity
                    )
                    seal_entity = editor.entity_count - len(contracts) + offset
                    wrapper = campaign._donor_fresh_cross_field_change_action(
                        helper_entity=helper,
                        player_script=player,
                        destination_field=destination[0],
                        destination_parameter=destination[1],
                        routine_pc=wrapper_pc,
                        seal_entity=seal_entity,
                    )
                    self.assertEqual(
                        editor.bytecode[wrapper_pc : wrapper_pc + len(wrapper)],
                        wrapper,
                    )
                elif key == (588, donor588.RETURN_CONTROLLER):
                    # The scanner annex's retained native door body stays
                    # frozen at 621/p5, while its active collision wrapper is
                    # the reciprocal Service-Manifold route to 565/p5.
                    self.assertIsNone(retarget.action_pc)
                    self.assertIsNone(retarget.change_pc)
                    wrapper_pc = editor.get_script_pointer(
                        donor588.RETURN_CONTROLLER,
                        2,
                    )
                    contracts = campaign.DONOR_DOOR_COLLISION_CONTRACTS[588]
                    self.assertEqual(len(contracts), 1)
                    seal_entity = editor.entity_count - 1
                    wrapper = campaign._donor_native_field_change_action(
                        helper_entity=donor588.RETURN_HELPER,
                        player_script=donor588.RETURN_PLAYER_SCRIPT_INDEX,
                        destination_field=565,
                        destination_parameter=5,
                        seal_entity=seal_entity,
                        routine_pc=wrapper_pc,
                    )
                    self.assertEqual(
                        editor.bytecode[wrapper_pc : wrapper_pc + len(wrapper)],
                        wrapper,
                    )
                elif key == (621, 22):
                    # The checked 620/p0 route remains byte-identical at its
                    # original PC while script 2 conditionally rejoins it only
                    # when the dedicated Quarantine keycard is present.
                    self.assertEqual(
                        editor.get_script_pointer(
                            campaign.INTAKE_QUARANTINE_DOOR_ENTITY,
                            2,
                        ),
                        campaign.INTAKE_QUARANTINE_LOCK_ACTION_PC,
                    )
                    self.assertEqual(
                        editor.bytecode[
                            campaign.INTAKE_QUARANTINE_DOOR_ACTION_PC :
                            campaign.INTAKE_QUARANTINE_DOOR_ACTION_PC
                            + len(campaign.INTAKE_QUARANTINE_UNLOCKED_ACTION)
                        ],
                        campaign.INTAKE_QUARANTINE_UNLOCKED_ACTION,
                    )
                elif key == (621, 26):
                    self.assertEqual(
                        editor.get_script_pointer(
                            campaign.INTAKE_FREIGHT_DOOR_ENTITY,
                            2,
                        ),
                        campaign.INTAKE_FREIGHT_KEYCARD_GATE_ACTION_PC,
                    )
                    self.assertEqual(
                        editor.bytecode[
                            campaign.INTAKE_FREIGHT_DOOR_ACTION_PC :
                            campaign.INTAKE_FREIGHT_DOOR_ACTION_PC
                            + len(campaign.INTAKE_FREIGHT_UNLOCKED_ACTION)
                        ],
                        campaign.INTAKE_FREIGHT_UNLOCKED_ACTION,
                    )
                else:
                    self.assertEqual(
                        editor.get_script_pointer(retarget.controller_entity, 2),
                        retarget.action_pc,
                    )
                if retarget.change_pc is not None:
                    self.assertEqual(
                        editor.bytecode[
                            retarget.change_pc : retarget.change_pc + 5
                        ],
                        base._change_field(*retarget.destination),
                    )
                if key in helpers:
                    self.assertIn(
                        bytes(
                            (
                                0x09,
                                helpers[(retarget.field, retarget.controller_entity)],
                                0x24,
                            )
                        ),
                        editor.bytecode[
                            retarget.action_pc : retarget.change_pc
                        ],
                    )

        # The patient-side native action remains dormant and byte-identical;
        # V197 points e24 at a keycard gate which rejoins it on success.  The
        # freight action retains its native animation but owns the audited
        # V227 two-byte destination retarget into Treatment Preparation.
        native_routes = {
            (621, 24): (
                campaign.INTAKE_PATIENT_KEYCARD_GATE_ACTION_PC,
                0x0D04,
                0x0D18,
                (565, 0),
            ),
            (621, 26): (
                campaign.INTAKE_FREIGHT_KEYCARD_GATE_ACTION_PC,
                campaign.INTAKE_FREIGHT_DOOR_ACTION_PC,
                campaign.INTAKE_FREIGHT_DOOR_CHANGE_PC,
                (594, 0),
            ),
            (565, 4): (0x0A09, 0x0A09, 0x0A23, (621, 1)),
        }
        for (field, entity), (
            selected_pc,
            native_action_pc,
            change_pc,
            destination,
        ) in (
            native_routes.items()
        ):
            editor = ScriptEditor(
                prepared[field].components[base.SCRIPT_INDEX]
            )
            with self.subTest(field=field, entity=entity, native=True):
                self.assertEqual(editor.get_script_pointer(entity, 2), selected_pc)
                self.assertEqual(
                    editor.bytecode[change_pc : change_pc + 5],
                    base._change_field(*destination),
                )
                if (field, entity) == (621, 24):
                    self.assertEqual(
                        editor.bytecode[
                            native_action_pc : native_action_pc
                            + len(campaign.INTAKE_PATIENT_UNLOCKED_ACTION)
                        ],
                        campaign.INTAKE_PATIENT_UNLOCKED_ACTION,
                    )

        intake_edges = {
            edge.sample: (edge.destination_field, edge.destination_parameter)
            for edge in self.field_by_scene[621].spec.edges
        }
        self.assertEqual(intake_edges[(870, 1830)], (549, 0))
        self.assertEqual(intake_edges[(0, 840)], (620, 0))
        self.assertEqual(intake_edges[(866, 1131)], (565, 0))
        self.assertEqual(intake_edges[(1645, 396)], (594, 0))
        quarantine_edges = {
            edge.sample: (edge.destination_field, edge.destination_parameter)
            for edge in self.field_by_scene[620].spec.edges
        }
        self.assertEqual(quarantine_edges[(-352, 0)], (621, 2))

    def test_slot1_marked_quarantine_door_requires_quarantine_keycard(self) -> None:
        item = self.field_by_scene[621]
        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])

        # The fresh marker is e3 at raw fixed (4586400, 55050240), yaw 0,
        # directly facing the +X carrier e22 at (88,840) on triangle 18.
        live_x = 4_586_400 / 65_536
        live_z = 55_050_240 / 65_536
        door = base.NATIVE_DOOR_CONTROLLERS[621][2]
        self.assertEqual(
            (door.x, door.z, door.triangle, live_z),
            (88, 840, 18, 840),
        )
        self.assertLess(door.x - live_x, 19)
        self.assertGreater(door.x - live_x, 18)

        action_pc = editor.get_script_pointer(
            campaign.INTAKE_QUARANTINE_DOOR_ENTITY,
            2,
        )
        self.assertEqual(action_pc, campaign.INTAKE_QUARANTINE_LOCK_ACTION_PC)
        action = campaign._intake_quarantine_locked_action(
            dialogue_id=campaign.INTAKE_QUARANTINE_LOCK_DIALOGUE_ID,
            unlocked_action_pc=campaign.INTAKE_QUARANTINE_DOOR_ACTION_PC,
            routine_pc=action_pc,
        )
        self.assertEqual(
            editor.bytecode[action_pc : action_pc + len(action)],
            action,
        )

        publish = base.mass_driver._set_variable_s16(
            campaign.INTAKE_DIALOG_BUSY_VARIABLE,
            1,
        )
        clear = base.mass_driver._set_variable_s16(
            campaign.INTAKE_DIALOG_BUSY_VARIABLE,
            0,
        )
        hidden_notice = (
            b"\xF5"
            + struct.pack("<H", campaign.INTAKE_QUARANTINE_LOCK_DIALOGUE_ID)
            + b"\x01\x9C"
        )
        denial_pc = struct.unpack_from("<H", action, 6)[0]
        self.assertEqual(
            action[:8],
            campaign._bit_test(
                campaign.QUARANTINE_KEYCARD_OPERAND,
                campaign.QUARANTINE_KEYCARD_MASK,
                denial_pc,
            ),
        )
        self.assertEqual(
            action[8:11],
            campaign._jump(campaign.INTAKE_QUARANTINE_DOOR_ACTION_PC),
        )
        self.assertTrue(action[11:].startswith(publish + b"\x33\xFE\x54"))
        self.assertIn(hidden_notice, action)
        self.assertLess(action.index(publish), action.index(hidden_notice))
        self.assertLess(action.index(hidden_notice), action.index(clear))
        self.assertEqual(action.count(b"\x31\x20\x00"), 2)
        self.assertTrue(action.endswith(clear + b"\xFE\x53\x00"))

        # The Security keycard does not open this entrance.  The locked branch
        # has no sound, leaf call, or transition; the dedicated Quarantine
        # keycard jumps to the retained native opening body with all three.
        locked = _run_appointment_vm(
            editor.bytecode,
            start_pc=action_pc,
            variables={
                campaign.QUARANTINE_KEYCARD_OPERAND: (
                    campaign.SECURITY_KEYCARD_MASK
                ),
            },
        )
        self.assertEqual(
            locked["dialogue_ids"],
            (campaign.INTAKE_QUARANTINE_LOCK_DIALOGUE_ID,),
        )
        self.assertEqual(locked["sound_ids"], ())
        self.assertEqual(locked["blocking_calls"], ())
        self.assertIsNone(locked["field_change"])

        unlocked = _run_appointment_vm(
            editor.bytecode,
            start_pc=action_pc,
            variables={
                campaign.QUARANTINE_KEYCARD_OPERAND: (
                    campaign.QUARANTINE_KEYCARD_MASK
                ),
            },
        )
        self.assertEqual(unlocked["dialogue_ids"], ())
        self.assertEqual(unlocked["sound_ids"], (0x77,))
        self.assertEqual(unlocked["blocking_calls"], ((2, 0x24),))
        self.assertEqual(
            unlocked["field_change"],
            campaign.INTAKE_QUARANTINE_DESTINATION,
        )

        # Preserve the authentic open-and-enter path byte-for-byte instead of
        # reconstructing the leaf animation inside the conditional gate.
        self.assertEqual(
            editor.bytecode[
                campaign.INTAKE_QUARANTINE_DOOR_ACTION_PC :
                campaign.INTAKE_QUARANTINE_DOOR_ACTION_PC
                + len(campaign.INTAKE_QUARANTINE_UNLOCKED_ACTION)
            ],
            campaign.INTAKE_QUARANTINE_UNLOCKED_ACTION,
        )
        blocks = parse_dialogue(item.components[7]).blocks
        lock_block = blocks[campaign.INTAKE_QUARANTINE_LOCK_DIALOGUE_ID]
        self.assertEqual(
            (lock_block.width, lock_block.height, lock_block.text),
            (58, 5, campaign.INTAKE_QUARANTINE_LOCK_DIALOGUE),
        )

    def test_intake_patient_freight_and_exam_routes_use_security_keycard_gates(
        self,
    ) -> None:
        item = self.field_by_scene[621]
        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])

        # The current V195 Slot-1 capture is Fei/e3 at this exact fixed-point
        # stance, looking west at the lower-east freight carrier.  It is e26,
        # not the earlier e22 Quarantine marker at (88,840).
        live_x = 109_118_480 / 65_536
        live_z = 25_952_256 / 65_536
        live_triangle = 85
        live_facing = 0x0800
        self.assertEqual((live_x, live_z), (1665.015869140625, 396))
        self.assertEqual((live_triangle, live_facing), (85, 0x0800))

        candidates = []
        for offset, candidate in enumerate(base.NATIVE_DOOR_CONTROLLERS[621]):
            if (
                abs(live_x - candidate.x)
                <= 2 * candidate.interaction_half_width
                + campaign.PLAYER_COLLISION_RADIUS
                and abs(live_z - candidate.z)
                <= 2 * candidate.interaction_half_depth
                + campaign.PLAYER_COLLISION_RADIUS
            ):
                candidates.append(20 + offset)
        self.assertEqual(candidates, [campaign.INTAKE_FREIGHT_DOOR_ENTITY])

        door = base.NATIVE_DOOR_CONTROLLERS[621][6]
        # Freeze the retail carrier's physical source geometry separately
        # from V227's checked room retarget.  The e26 threshold and keycard
        # gate stay put, while its CHANGE_FIELD now enters field 594/p0.
        self.assertEqual(
            (
                door.x,
                door.z,
                door.triangle,
                door.destination_field,
                door.destination_parameter,
            ),
            (1645, 396, live_triangle, 565, 3),
        )
        self.assertEqual(campaign.INTAKE_FREIGHT_DESTINATION, (594, 0))
        freight_retarget = next(
            retarget
            for retarget in campaign.ROOM_SWAP_RETARGETS
            if (
                retarget.field,
                retarget.controller_entity,
            )
            == (621, campaign.INTAKE_FREIGHT_DOOR_ENTITY)
        )
        self.assertEqual(freight_retarget.source_destination, (565, 3))
        self.assertEqual(
            freight_retarget.destination,
            campaign.INTAKE_FREIGHT_DESTINATION,
        )
        self.assertGreater(live_x, door.x)
        self.assertEqual(live_z, door.z)

        self.assertEqual(
            (
                campaign.SECURITY_KEYCARD_OPERAND,
                campaign.SECURITY_KEYCARD_BIT_INDEX,
                campaign.SECURITY_KEYCARD_MASK,
                campaign.INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE_ID,
                campaign.INTAKE_FREIGHT_AUTHORIZATION_LOCK_DIALOGUE_ID,
            ),
            (0x021A, 0, 0x0001, 22, 23),
        )
        action_pc = editor.get_script_pointer(
            campaign.INTAKE_FREIGHT_DOOR_ENTITY,
            2,
        )
        self.assertEqual(action_pc, campaign.INTAKE_FREIGHT_KEYCARD_GATE_ACTION_PC)
        gate = campaign._intake_freight_keycard_gate_action(
            dialogue_id=campaign.INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE_ID,
            unlocked_action_pc=campaign.INTAKE_FREIGHT_DOOR_ACTION_PC,
            routine_pc=action_pc,
        )
        self.assertEqual(editor.bytecode[action_pc : action_pc + len(gate)], gate)
        self.assertEqual(
            gate[:8],
            campaign._bit_test(
                campaign.SECURITY_KEYCARD_OPERAND,
                campaign.SECURITY_KEYCARD_MASK,
                struct.unpack_from("<H", gate, 6)[0],
            ),
        )
        self.assertEqual(
            gate[8:11],
            campaign._jump(campaign.INTAKE_FREIGHT_DOOR_ACTION_PC),
        )

        # The authentic animated route stays dormant and byte-identical at its
        # native PC.  Credential success jumps here instead of rebuilding it.
        self.assertEqual(
            editor.bytecode[
                campaign.INTAKE_FREIGHT_DOOR_ACTION_PC :
                campaign.INTAKE_FREIGHT_DOOR_ACTION_PC
                + len(campaign.INTAKE_FREIGHT_UNLOCKED_ACTION)
            ],
            campaign.INTAKE_FREIGHT_UNLOCKED_ACTION,
        )
        self.assertEqual(
            editor.bytecode[
                campaign.INTAKE_FREIGHT_DOOR_CHANGE_PC :
                campaign.INTAKE_FREIGHT_DOOR_CHANGE_PC + 5
            ],
            base._change_field(*campaign.INTAKE_FREIGHT_DESTINATION),
        )

        for tone_value in (0, campaign.TONE_MASK):
            with self.subTest(
                freight_security=False,
                freight_tone=bool(tone_value),
            ):
                locked = _run_appointment_vm(
                    editor.bytecode,
                    start_pc=action_pc,
                    variables={
                        campaign.SECURITY_KEYCARD_OPERAND: 0,
                        campaign.TONE_OPERAND: tone_value,
                    },
                )
                self.assertEqual(locked["reason"], "stop")
                self.assertEqual(
                    locked["dialogue_ids"],
                    (campaign.INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE_ID,),
                )
                self.assertEqual(locked["sound_ids"], ())
                self.assertEqual(locked["blocking_calls"], ())
                self.assertIsNone(locked["field_change"])
                self.assertEqual(
                    (
                        locked["control_suspends"],
                        locked["control_restores"],
                    ),
                    (1, 1),
                )

        for tone_value in (0, campaign.TONE_MASK):
            with self.subTest(
                freight_security=True,
                freight_tone=bool(tone_value),
            ):
                unlocked = _run_appointment_vm(
                    editor.bytecode,
                    start_pc=action_pc,
                    variables={
                        campaign.SECURITY_KEYCARD_OPERAND: (
                            campaign.SECURITY_KEYCARD_MASK
                        ),
                        campaign.TONE_OPERAND: tone_value,
                    },
                )
                self.assertEqual(unlocked["reason"], "field_change")
                self.assertEqual(
                    unlocked["field_change"],
                    campaign.INTAKE_FREIGHT_DESTINATION,
                )
                self.assertEqual(unlocked["dialogue_ids"], ())
                self.assertEqual(unlocked["sound_ids"], (0x77,))
                self.assertEqual(unlocked["blocking_calls"], ((0x22, 0x24),))

        blocks = parse_dialogue(item.components[7]).blocks
        lock_block = blocks[campaign.INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE_ID]
        self.assertEqual(
            (lock_block.width, lock_block.height, lock_block.text),
            (58, 5, campaign.INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE),
        )
        self.assertEqual(campaign._campaign_dialogue_layout_issues(lock_block), ())
        authorization_block = blocks[
            campaign.INTAKE_FREIGHT_AUTHORIZATION_LOCK_DIALOGUE_ID
        ]
        self.assertEqual(
            (
                authorization_block.width,
                authorization_block.height,
                authorization_block.text,
            ),
            (58, 5, campaign.INTAKE_FREIGHT_AUTHORIZATION_LOCK_DIALOGUE),
        )
        self.assertEqual(
            campaign._campaign_dialogue_layout_issues(authorization_block),
            (),
        )

        # The north patient route uses the same denial flow but rejoins its own
        # untouched e24 helper, destination parameter, and field change.
        patient_pc = editor.get_script_pointer(
            campaign.INTAKE_PATIENT_DOOR_ENTITY,
            2,
        )
        self.assertEqual(patient_pc, campaign.INTAKE_PATIENT_KEYCARD_GATE_ACTION_PC)
        patient_gate = campaign._intake_freight_keycard_gate_action(
            dialogue_id=campaign.INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE_ID,
            unlocked_action_pc=campaign.INTAKE_PATIENT_DOOR_ACTION_PC,
            routine_pc=patient_pc,
        )
        self.assertEqual(
            editor.bytecode[patient_pc : patient_pc + len(patient_gate)],
            patient_gate,
        )
        self.assertEqual(
            patient_gate[8:11],
            campaign._jump(campaign.INTAKE_PATIENT_DOOR_ACTION_PC),
        )
        self.assertEqual(
            editor.bytecode[
                campaign.INTAKE_PATIENT_DOOR_ACTION_PC :
                campaign.INTAKE_PATIENT_DOOR_ACTION_PC
                + len(campaign.INTAKE_PATIENT_UNLOCKED_ACTION)
            ],
            campaign.INTAKE_PATIENT_UNLOCKED_ACTION,
        )
        self.assertEqual(
            editor.bytecode[
                campaign.INTAKE_PATIENT_DOOR_CHANGE_PC :
                campaign.INTAKE_PATIENT_DOOR_CHANGE_PC + 5
            ],
            base._change_field(*campaign.INTAKE_PATIENT_DESTINATION),
        )

        patient_locked = _run_appointment_vm(
            editor.bytecode,
            start_pc=patient_pc,
            variables={campaign.SECURITY_KEYCARD_OPERAND: 0},
        )
        self.assertEqual(
            patient_locked["dialogue_ids"],
            (campaign.INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE_ID,),
        )
        self.assertEqual(patient_locked["sound_ids"], ())
        self.assertEqual(patient_locked["blocking_calls"], ())
        self.assertIsNone(patient_locked["field_change"])

        patient_unlocked = _run_appointment_vm(
            editor.bytecode,
            start_pc=patient_pc,
            variables={
                campaign.SECURITY_KEYCARD_OPERAND: campaign.SECURITY_KEYCARD_MASK,
                # The patient-service route deliberately remains independent of
                # the later field-565 tone authorization.
                campaign.TONE_OPERAND: 0,
            },
        )
        self.assertEqual(
            patient_unlocked["field_change"],
            campaign.INTAKE_PATIENT_DESTINATION,
        )
        self.assertEqual(patient_unlocked["dialogue_ids"], ())
        self.assertEqual(patient_unlocked["sound_ids"], (0x77,))
        self.assertEqual(patient_unlocked["blocking_calls"], ((0x20, 0x24),))

        # e22 is a different progression contract: completed Quarantine, not
        # the clinic credential, unlocks its preserved shortcut action.
        self.assertEqual(
            editor.get_script_pointer(campaign.INTAKE_QUARANTINE_DOOR_ENTITY, 2),
            campaign.INTAKE_QUARANTINE_LOCK_ACTION_PC,
        )

    def test_archive_return_door_reaches_before_seal_at_exact_live_stances(
        self,
    ) -> None:
        contract = campaign.DONOR_DOOR_COLLISION_CONTRACTS[549][0]
        seal_x, seal_z = campaign._donor_seal_position(contract)
        v179_x = -13_924_297 / 65_536
        v179_z = 13_206_107 / 65_536
        v179_dx = abs(v179_x - contract.x)
        v179_dz = abs(v179_z - contract.z)
        v228_x = -12_702_524 / 65_536
        v228_z = 16_007_409 / 65_536
        v228_action_dx = abs(v228_x - contract.x)
        v228_action_dz = abs(v228_z - contract.z)
        v228_seal_dx = abs(v228_x - seal_x)
        v228_seal_dz = abs(v228_z - seal_z)
        v229_x = -13_485_612 / 65_536
        v229_z = 15_269_605 / 65_536
        action_half_width, action_half_depth = (
            campaign._donor_door_action_bounds(contract)
        )

        # V179 was depth-limited, so its checked 0x0C extension remains.  V228
        # approaches laterally: it begins outside the X shell, but the thinner
        # seal leaves room to advance until every first-contact point lies
        # inside that unchanged deliberate-X shell.
        self.assertLessEqual(
            v179_dx,
            2 * action_half_width + campaign.PLAYER_COLLISION_RADIUS,
        )
        self.assertGreater(
            v179_dz,
            2 * contract.interaction_half_depth
            + campaign.PLAYER_COLLISION_RADIUS,
        )
        self.assertLessEqual(
            v179_dz,
            2 * action_half_depth + campaign.PLAYER_COLLISION_RADIUS,
        )
        effective_action_width = (
            2 * action_half_width
            + campaign.PLAYER_COLLISION_RADIUS
        )
        effective_action_depth = (
            2 * action_half_depth + campaign.PLAYER_COLLISION_RADIUS
        )
        effective_seal_radius = (
            2 * contract.seal_radius + campaign.PLAYER_COLLISION_RADIUS
        )
        self.assertGreater(v228_action_dx, effective_action_width)
        self.assertGreater(
            math.hypot(v228_seal_dx, v228_seal_dz),
            effective_seal_radius,
        )
        first_contact_seal_dx = math.sqrt(
            effective_seal_radius**2 - v228_seal_dz**2
        )
        first_contact_x = seal_x + first_contact_seal_dx
        first_contact_action_dx = abs(first_contact_x - contract.x)
        self.assertLess(first_contact_seal_dx, v228_seal_dx)
        self.assertLessEqual(first_contact_action_dx, effective_action_width)
        self.assertLessEqual(v228_action_dz, effective_action_depth)
        # V230 moves only the physical actor deeper into the aperture.  Its
        # complete circle still fits in e6's rectangular X shell.
        self.assertEqual((contract.x, contract.z), (-240, 240))
        self.assertEqual((seal_x, seal_z), (-244, 248))
        self.assertLessEqual(
            abs(seal_x - contract.x) + effective_seal_radius,
            effective_action_width,
        )
        self.assertLessEqual(
            abs(seal_z - contract.z) + effective_seal_radius,
            effective_action_depth,
        )
        self.assertEqual((action_half_width, action_half_depth), (0x0A, 0x0C))

        # The exact round-trip Slot-1 facing is yaw 0x600: world (-X,-Z).
        # Its infinite forward ray must clear the shifted circle rather than
        # snagging against the side of a door Fei is walking past.
        direction = (-1 / math.sqrt(2), -1 / math.sqrt(2))
        relative = (v229_x - seal_x, v229_z - seal_z)
        dot = relative[0] * direction[0] + relative[1] * direction[1]
        forward_t = -dot
        closest_distance = math.sqrt(
            relative[0] ** 2 + relative[1] ** 2 - dot**2
        )
        self.assertGreater(forward_t, 0)
        self.assertAlmostEqual(
            closest_distance - effective_seal_radius,
            5.639441995778888,
        )
        self.assertGreater(closest_distance, effective_seal_radius)

        source = campaign._expected_donor_door_controller_init(contract)
        carrier = campaign._ghost_donor_door_controller_init(contract)
        seal = campaign._donor_circle_seal_init(contract)
        self.assertIn(bytes.fromhex("18 0A 0A 1E 00"), source)
        self.assertIn(bytes.fromhex("18 0A 0C 1E 00"), carrier)
        self.assertIn(bytes.fromhex("19 0C FF F8 00"), seal)
        self.assertIn(bytes.fromhex("18 00 00 64 08"), seal)
        self.assertEqual(contract.seal_radius, campaign.ARCHIVE_RETURN_SEAL_RADIUS)
        self.assertEqual(effective_seal_radius, 32)

        prepared = self.donor_by_scene[549]
        editor = ScriptEditor(prepared.components[base.SCRIPT_INDEX])
        self.assertEqual(editor.entity_count, 17)
        carrier_pc = editor.get_script_pointer(contract.controller_entity, 0)
        seal_pc = editor.get_script_pointer(16, 0)
        self.assertEqual(
            editor.bytecode[carrier_pc : carrier_pc + len(carrier)],
            carrier,
        )
        self.assertEqual(
            editor.bytecode[seal_pc : seal_pc + len(seal)],
            seal,
        )
        self.assertEqual(
            (len(prepared.header), _sha256(prepared.header)),
            (
                752,
                "27432b47d36a1d08438aa843146bfeccbae0efbd0370167ccbf00871a9914a21",
            ),
        )
        records = _actor_records(prepared.header)
        self.assertEqual(len(records), 22)
        self.assertEqual(
            (
                struct.unpack_from("<h", records[16], 8)[0],
                struct.unpack_from("<h", records[16], 12)[0],
            ),
            (seal_x, seal_z),
        )

        triangles = base._walkmesh_layer(
            self.donor_by_scene[549].components[1],
            0,
        )
        self.assertTrue(
            base._point_inside_triangle(
                (v229_x, v229_z),
                triangles[10],
            )
        )
        self.assertEqual(contract.cut_triangles, (6, 10, 11, 12, 13))
        self.assertTrue(
            _sampled_cut_is_reachable(
                triangles,
                contract.cut_triangles,
                (seal_x, seal_z),
                0,
                contract.closed_side_probe,
                contract.open_side_probe,
            )
        )
        self.assertFalse(
            _sampled_cut_is_reachable(
                triangles,
                contract.cut_triangles,
                (seal_x, seal_z),
                effective_seal_radius,
                contract.closed_side_probe,
                contract.open_side_probe,
            )
        )

        # The effective disk crosses both diagonal aperture seams by a wide
        # analytic margin, so the sampled proof cannot hide a sub-grid leak.
        def segment_distance(
            point: tuple[int, int],
            start: tuple[int, int],
            end: tuple[int, int],
        ) -> float:
            dx = end[0] - start[0]
            dz = end[1] - start[1]
            parameter = (
                (point[0] - start[0]) * dx
                + (point[1] - start[1]) * dz
            ) / (dx * dx + dz * dz)
            self.assertGreater(parameter, 0)
            self.assertLess(parameter, 1)
            closest = (
                start[0] + parameter * dx,
                start[1] + parameter * dz,
            )
            return math.hypot(
                point[0] - closest[0],
                point[1] - closest[1],
            )

        seam_margins = tuple(
            effective_seal_radius
            - segment_distance((seal_x, seal_z), start, end)
            for start, end in (
                ((-240, 209), (-286, 273)),
                ((-207, 241), (-271, 288)),
            )
        )
        self.assertAlmostEqual(seam_margins[0], 12.48625560742041)
        self.assertAlmostEqual(seam_margins[1], 15.741379398790173)

    def test_field352_return_requires_x_and_reaches_saved_stances(self) -> None:
        saved_stances = {
            "field593_v216": (
                2_624_381 / 65_536,
                14_973_253 / 65_536,
            ),
            "field550_v224": (
                2_841_247 / 65_536,
                14_988_804 / 65_536,
            ),
            "field592_v225": (0.0, 14_745_200 / 65_536),
        }
        self.assertAlmostEqual(
            saved_stances["field593_v216"][0],
            40.04487609863281,
        )
        self.assertAlmostEqual(
            saved_stances["field593_v216"][1],
            228.4737091064453,
        )
        self.assertAlmostEqual(
            saved_stances["field550_v224"][0],
            43.35398864746094,
        )
        self.assertAlmostEqual(
            saved_stances["field550_v224"][1],
            228.71099853515625,
        )
        self.assertAlmostEqual(
            saved_stances["field592_v225"][1],
            224.993896484375,
        )
        self.assertGreater(saved_stances["field550_v224"][0], 23)
        self.assertEqual(
            (
                len(campaign.EXAM_RETURN_RETIRED_CAVITY_SOURCE),
                _sha256(campaign.EXAM_RETURN_RETIRED_CAVITY_SOURCE),
            ),
            (
                87,
                "85581a31b32134e75912714f1e71cbe0957721e289f114f954a98ed7c4ca8824",
            ),
        )

        self.assertEqual(
            campaign.FIELD352_X_ONLY_SCENES,
            (550, 567, *exam_rooms.SCENES),
        )
        self.assertEqual(
            campaign.FIELD352_SIDE_TERMINAL_SCENES,
            (567, *exam_rooms.SCENES),
        )
        for scene in campaign.FIELD352_X_ONLY_SCENES:
            contract = campaign.DONOR_DOOR_COLLISION_CONTRACTS[scene][0]
            source_item = (
                self.clinic_pre_door
                if scene == 550
                else (
                    exam_rooms.prepare_empty_room_terminal(self.base_567)
                    if scene == 567
                    else self.base_exam_room_by_scene[scene]
                )
            )
            source = ScriptEditor(
                source_item.components[base.SCRIPT_INDEX]
            )
            editor = ScriptEditor(
                self.donor_by_scene[scene].components[base.SCRIPT_INDEX]
            )
            with self.subTest(scene=scene):
                self.assertEqual(
                    contract.rectangular_seal_position,
                    campaign.EXAM_RETURN_RECTANGULAR_SEAL_POSITION,
                )
                self.assertEqual(
                    contract.rectangular_seal_half_extents,
                    campaign.EXAM_RETURN_RECTANGULAR_SEAL_HALF_EXTENTS,
                )
                physical_half_width = (
                    2 * contract.rectangular_seal_half_extents[0]
                )
                physical_half_depth = (
                    2 * contract.rectangular_seal_half_extents[1]
                )
                self.assertEqual(
                    (physical_half_width, physical_half_depth),
                    (48, 16),
                )
                self.assertEqual(
                    contract.rectangular_seal_position[1] - physical_half_depth,
                    250,
                )
                self.assertEqual(
                    contract.rectangular_seal_position[1] + physical_half_depth,
                    282,
                )
                self.assertLess(
                    234,
                    contract.rectangular_seal_position[1] - physical_half_depth,
                )
                self.assertEqual(contract.closed_side_probe, (0, 200))
                self.assertEqual(contract.open_side_probe, (0, 300))

                action_half_width, action_half_depth = (
                    campaign._donor_door_action_bounds(contract)
                )
                effective_cross_half_extents = (
                    2 * action_half_width + campaign.PLAYER_COLLISION_RADIUS,
                    2 * action_half_depth + campaign.PLAYER_COLLISION_RADIUS,
                )
                self.assertEqual(effective_cross_half_extents, (64, 48))
                for stance_name, (saved_x, saved_z) in saved_stances.items():
                    with self.subTest(scene=scene, stance=stance_name):
                        self.assertLessEqual(
                            abs(saved_x - contract.x),
                            effective_cross_half_extents[0],
                        )
                        self.assertLessEqual(
                            abs(saved_z - contract.z),
                            effective_cross_half_extents[1],
                        )

                triangles = base._walkmesh_layer(
                    self.donor_by_scene[scene].components[1],
                    0,
                )
                self.assertEqual(
                    {triangles[15][0], triangles[15][2]},
                    {(160, 0, 234), (23, 0, 234)},
                )

                for version, inspected in (("source", source), ("final", editor)):
                    with self.subTest(scene=scene, version=version):
                        expected_cavity = (
                            exam_rooms.EMPTY_ROOM_TERMINAL_AUX_CAVITY
                            if scene == 567
                            else (
                                exam_rooms.TERMINAL_AUX_CAVITY
                                if scene in exam_rooms.SCENES
                                else campaign.EXAM_RETURN_RETIRED_CAVITY_SOURCE
                            )
                        )
                        self.assertEqual(
                            inspected.bytecode[
                                campaign.EXAM_RETURN_RETIRED_CAVITY_PC :
                                campaign.EXAM_RETURN_RETIRED_CAVITY_END_PC
                            ],
                            expected_cavity,
                        )
                        self.assertEqual(
                            inspected.get_script_pointer(0, 1),
                            empty_clinic567.SHARED_STOP_PC,
                        )
                        cavity_entries = tuple(
                            (entity, script_index)
                            for entity in range(inspected.entity_count)
                            for script_index in range(32)
                            if campaign.EXAM_RETURN_RETIRED_CAVITY_PC
                            <= inspected.get_script_pointer(entity, script_index)
                            < campaign.EXAM_RETURN_RETIRED_CAVITY_END_PC
                        )
                        self.assertEqual(
                            cavity_entries,
                            (
                                tuple(
                                    (entity, 0)
                                    for entity in exam_rooms.TERMINAL_AUX_ENTITIES
                                )
                                if scene in campaign.FIELD352_SIDE_TERMINAL_SCENES
                                else ()
                            ),
                        )
                        if scene == 567:
                            third = exam_rooms.EMPTY_ROOM_TERMINAL_ENTITIES[2]
                            self.assertEqual(
                                inspected.get_script_pointer(third, 0),
                                exam_rooms.EMPTY_ROOM_TERMINAL_INIT_PC,
                            )
                            self.assertEqual(
                                inspected.get_script_pointer(third, 2),
                                exam_rooms.EMPTY_ROOM_TERMINAL_ACTION_PC,
                            )
                            self.assertEqual(
                                inspected.bytecode[
                                    exam_rooms.EMPTY_ROOM_TERMINAL_INIT_PC :
                                    exam_rooms.EMPTY_ROOM_TERMINAL_ACTION_PC
                                ],
                                exam_rooms.TERMINAL_INIT_BODIES[2],
                            )

                self.assertIs(
                    campaign._validate_exam_return_x_only(
                        editor,
                        contract,
                        scene,
                    ),
                    editor,
                )

                seal_entity = (
                    campaign.CLINIC_EXIT_SEAL_ENTITY
                    if scene == 550
                    else editor.entity_count - 1
                )
                action_pc = editor.get_script_pointer(
                    contract.controller_entity,
                    2,
                )
                destination = campaign.DONOR_NATIVE_FIELD_CHANGE_ACTIONS[scene]
                expected_action = campaign._clinic_native_field_change_action(
                    destination_field=destination[4],
                    destination_parameter=destination[5],
                    seal_entity=seal_entity,
                )
                if scene == 550:
                    # The office's bloodwork gate owns e17:s2, but retains one
                    # exact post-victory native action that releases e19.
                    self.assertEqual(editor.bytecode.count(expected_action), 1)
                    self.assertNotEqual(
                        editor.bytecode[
                            action_pc : action_pc + len(expected_action)
                        ],
                        expected_action,
                    )
                else:
                    self.assertEqual(
                        editor.bytecode[
                            action_pc : action_pc + len(expected_action)
                        ],
                        expected_action,
                    )

    def test_decoded_stream_and_graphics_preservation_matrix(self) -> None:
        changed_by_scene = {
            623: {5, 7},
            621: {2, 3, 4, 5, 7},
            620: {5, 7},
            624: {5, 7},
            626: {5, 7},
            625: {5, 7},
            622: {5, 7},
            549: {5, 7},
            550: {5},
            565: {5, 7},
            567: {5, 7},
            591: {5, 7},
            592: {5, 7},
            593: {5},
            594: {5, 7},
            589: {5, 7},
            588: {5, 7},
            590: {5, 7},
        }
        before = self.base_field_by_scene | self.base_donor_by_scene | {
            550: self.clinic_pre_door,
            588: self.base_588,
            **self.base_exam_room_by_scene,
        }
        after = self.field_by_scene | self.donor_by_scene
        for scene, item in after.items():
            with self.subTest(scene=scene):
                self.assertEqual(item.graphics, before[scene].graphics)
                for index, (old, new) in enumerate(
                    zip(before[scene].components, item.components, strict=True)
                ):
                    if index in changed_by_scene[scene]:
                        self.assertNotEqual(old, new)
                    else:
                        self.assertEqual(old, new)

    def test_lobby_uses_exact_office_physician_asset_without_clobbering_civilians(self) -> None:
        before = self.base_field_by_scene[621]
        after = self.field_by_scene[621]
        office = self.clinic_pre_door
        actor_index = base.mass_driver.ACTOR_INDEX
        sprite_index = base.mass_driver.SPRITE_INDEX

        before_actors = _indexed_entries(before.components[actor_index])
        before_sprites = _indexed_entries(before.components[sprite_index])
        after_actors = _indexed_entries(after.components[actor_index])
        after_sprites = _indexed_entries(after.components[sprite_index])
        office_actors = _indexed_entries(office.components[actor_index])
        office_sprites = _indexed_entries(office.components[sprite_index])

        self.assertEqual((len(after_actors), len(after_sprites)), (8, 8))
        self.assertEqual(
            after_actors[campaign.INTAKE_DOCTOR_TARGET_BANK],
            office_actors[campaign.INTAKE_DOCTOR_SOURCE_BANK],
        )
        self.assertEqual(
            after_sprites[campaign.INTAKE_DOCTOR_TARGET_BANK],
            office_sprites[campaign.INTAKE_DOCTOR_SOURCE_BANK],
        )
        self.assertEqual(
            (
                _sha256(after_actors[campaign.INTAKE_DOCTOR_TARGET_BANK]),
                _sha256(after_sprites[campaign.INTAKE_DOCTOR_TARGET_BANK]),
            ),
            (
                campaign.INTAKE_SOURCE_PHYSICIAN_ACTOR_SHA256,
                campaign.INTAKE_SOURCE_PHYSICIAN_SPRITE_SHA256,
            ),
        )
        for bank in range(8):
            if bank == campaign.INTAKE_DOCTOR_TARGET_BANK:
                continue
            with self.subTest(preserved_lobby_bank=bank):
                self.assertEqual(after_actors[bank], before_actors[bank])
                self.assertEqual(after_sprites[bank], before_sprites[bank])

        # Bank 7 is the desk receptionist's palette-selected asset.  It must
        # remain byte-identical while the displaced bank-6 civilian moves to
        # an existing bank instead of inheriting the physician's appearance.
        self.assertEqual(after_actors[7], before_actors[7])
        self.assertEqual(after_sprites[7], before_sprites[7])
        editor = ScriptEditor(after.components[base.SCRIPT_INDEX])
        self.assertEqual(
            editor.bytecode[
                campaign.INTAKE_REASSIGNED_CIVILIAN_INIT_PC :
                campaign.INTAKE_REASSIGNED_CIVILIAN_INIT_PC + 3
            ],
            campaign.INTAKE_REASSIGNED_CIVILIAN_NEW_INIT,
        )
        self.assertEqual(
            campaign.INTAKE_REASSIGNED_CIVILIAN_NEW_INIT,
            b"\x0B" + base._immediate(campaign.INTAKE_REASSIGNED_CIVILIAN_GRAPHIC),
        )
        receptionist_pc = editor.get_script_pointer(
            campaign.INTAKE_RECEPTIONIST_ENTITY, 0
        )
        self.assertEqual(
            editor.bytecode[receptionist_pc : receptionist_pc + 3],
            bytes.fromhex("FE 15 07"),
        )
        self.assertEqual(
            struct.unpack_from(
                "<4H",
                after.header,
                campaign.INTAKE_DOCTOR_TARGET_BANK * 8,
            ),
            campaign.INTAKE_DOCTOR_TARGET_MAPPING,
        )

    def test_saved_stance_receptionist_and_room_behind_fei_are_exact(self) -> None:
        before_item = self.base_field_by_scene[621]
        final_item = self.field_by_scene[621]
        before = ScriptEditor(before_item.components[base.SCRIPT_INDEX])
        final = ScriptEditor(final_item.components[base.SCRIPT_INDEX])

        self.assertEqual(
            before.get_script_pointer(campaign.INTAKE_RECEPTIONIST_ENTITY, 2),
            campaign.INTAKE_RECEPTIONIST_RETAIL_ACTION_PC,
        )
        self.assertEqual(
            before.bytecode[campaign.INTAKE_RECEPTIONIST_RETAIL_ACTION_PC],
            0x00,
        )
        self.assertEqual(
            final.get_script_pointer(campaign.INTAKE_RECEPTIONIST_ENTITY, 2),
            campaign.INTAKE_RECEPTIONIST_ACTION_PC,
        )

        self.assertEqual(
            before.get_script_pointer(campaign.INTAKE_RECEPTIONIST_ENTITY, 0),
            campaign.INTAKE_RECEPTIONIST_RETAIL_INIT_PC,
        )
        self.assertEqual(
            before.bytecode[
                campaign.INTAKE_RECEPTIONIST_RETAIL_INIT_PC :
                campaign.INTAKE_RECEPTIONIST_RETAIL_INIT_PC
                + len(campaign.INTAKE_RECEPTIONIST_RETAIL_INIT)
            ],
            campaign.INTAKE_RECEPTIONIST_RETAIL_INIT,
        )
        self.assertEqual(
            final.get_script_pointer(campaign.INTAKE_RECEPTIONIST_ENTITY, 0),
            campaign.INTAKE_RECEPTIONIST_WIDE_INIT_PC,
        )
        expected_init = bytes.fromhex(
            "FE 15 07 80 01 80 19 66 03 16 05 C0 5F 00 "
            "F8 00 00 20 F8 07 04 00 18 20 40 00 00 20 01 80 00"
        )
        self.assertEqual(campaign._intake_receptionist_init(), expected_init)
        self.assertEqual(
            final.bytecode[
                campaign.INTAKE_RECEPTIONIST_WIDE_INIT_PC :
                campaign.INTAKE_RECEPTIONIST_WIDE_INIT_PC + len(expected_init)
            ],
            expected_init,
        )
        self.assertTrue(
            expected_init.startswith(campaign.INTAKE_RECEPTIONIST_RETAIL_INIT[:-1])
        )
        self.assertEqual(struct.unpack_from("<hh", expected_init, 7), (870, 1302))
        self.assertIn(bytes.fromhex("F8 00 00 20"), expected_init)
        self.assertIn(bytes.fromhex("F8 07 04 00"), expected_init)
        self.assertIn(bytes.fromhex("18 20 40 00 00"), expected_init)
        self.assertTrue(expected_init.endswith(bytes.fromhex("20 01 80 00")))
        self.assertNotIn(b"\x23", expected_init)  # sprite remains visible

        saved_fei_x, saved_fei_z = (870.0675354, 1433.6101837)
        receptionist_x, receptionist_z = (870, 1302)
        dx = abs(saved_fei_x - receptionist_x)
        dz = abs(saved_fei_z - receptionist_z)
        effective_width = (
            2 * campaign.INTAKE_RECEPTIONIST_INTERACTION_HALF_WIDTH
            + campaign.PLAYER_COLLISION_RADIUS
        )
        effective_depth = (
            2 * campaign.INTAKE_RECEPTIONIST_INTERACTION_HALF_DEPTH
            + campaign.PLAYER_COLLISION_RADIUS
        )
        self.assertAlmostEqual(dx, 0.0675354, places=7)
        self.assertAlmostEqual(dz, 131.6101837, places=7)
        self.assertEqual((effective_width, effective_depth), (80, 144))
        self.assertLessEqual(dx, effective_width)
        self.assertLessEqual(dz, effective_depth)
        self.assertGreater(math.hypot(dx, dz), 64)

        expected_action = bytes.fromhex(
            "35 CC 07 01 00 40 "
            "33 FE 54 31 20 00 80 0D 26 01 80 01 75 0D 26 01 80 "
            "02 FA 03 80 00 46 93 0D "
            "D2 0C 00 00 9C 01 98 0D "
            "D2 0B 00 00 9C "
            "31 20 00 A3 0D 26 01 80 01 98 0D 26 01 80 "
            "35 CC 07 00 00 40 FE 53 00"
        )
        self.assertEqual(
            expected_action,
            campaign._intake_receptionist_action(
                precheck_dialogue_id=11,
                postcheck_dialogue_id=12,
                routine_pc=campaign.INTAKE_RECEPTIONIST_ACTION_PC,
            ),
        )
        self.assertEqual(
            final.bytecode[
                campaign.INTAKE_RECEPTIONIST_ACTION_PC :
                campaign.INTAKE_RECEPTIONIST_ACTION_PC + len(expected_action)
            ],
            expected_action,
        )

        # e6 is the nearby survivor, whose existing action must not be
        # mistaken for the receptionist identified by the user's save.
        self.assertEqual(before.get_script_pointer(6, 0), 0x0158)
        survivor_init = bytes.fromhex(
            "0B 00 80 19 69 02 BF 05 C0 00 59 00 00"
        )
        self.assertEqual(before.bytecode[0x0158:0x0165], survivor_init)
        self.assertEqual(final.bytecode[0x0158:0x0165], survivor_init)
        bounded_survivor_pc = final.get_script_pointer(6, 0)
        bounded_survivor_init = campaign._intake_wandering_survivor_init(
            graphic=0,
            position=(617, 1450),
            zone=campaign.INTAKE_SURVIVOR_MOVEMENT_ZONES[6],
        )
        self.assertNotEqual(bounded_survivor_pc, 0x0158)
        self.assertEqual(
            final.bytecode[
                bounded_survivor_pc :
                bounded_survivor_pc + len(bounded_survivor_init)
            ],
            bounded_survivor_init,
        )
        self.assertEqual(before.get_script_pointer(6, 2), 0x0359)
        survivor_action = bytes.fromhex("D2 02 00 00 9C 00")
        self.assertEqual(before.bytecode[0x0359:0x035F], survivor_action)
        self.assertEqual(final.bytecode[0x0359:0x035F], survivor_action)
        survivor_wrapper = campaign._intake_native_dialogue_mutex_action(2)
        survivor_wrapper_pc = final.get_script_pointer(6, 2)
        self.assertNotEqual(survivor_wrapper_pc, 0x0359)
        self.assertEqual(
            final.bytecode[
                survivor_wrapper_pc : survivor_wrapper_pc + len(survivor_wrapper)
            ],
            survivor_wrapper,
        )

        # e21 is the physical north door behind Fei at the saved receptionist
        # stance.  Only its checked destination changes from quarantine to the
        # archive room containing the terminal.
        self.assertEqual(
            before.get_script_pointer(campaign.INTAKE_ARCHIVE_DOOR_ENTITY, 2),
            campaign.INTAKE_ARCHIVE_DOOR_ACTION_PC,
        )
        self.assertEqual(
            final.get_script_pointer(campaign.INTAKE_ARCHIVE_DOOR_ENTITY, 2),
            campaign.INTAKE_ARCHIVE_DOOR_ACTION_PC,
        )
        self.assertEqual(before.bytecode[0x0CE4:0x0CE9], base._change_field(620, 0))
        self.assertEqual(final.bytecode[0x0CE4:0x0CE9], base._change_field(549, 0))

        before_blocks = parse_dialogue(before_item.components[7]).blocks
        final_blocks = parse_dialogue(final_item.components[7]).blocks
        self.assertEqual(len(before_blocks), 11)
        self.assertEqual(len(final_blocks), 24)
        self.assertEqual(
            campaign.RECEPTIONIST_POSTCHECK_DIALOGUE,
            "Receptionist\n"
            '"I see you have signed in.\n'
            "Please wait here until your\n"
            'name is called."<Close>',
        )
        for block_id, expected_text in (
            (11, campaign.RECEPTIONIST_PRECHECK_DIALOGUE),
            (12, campaign.RECEPTIONIST_POSTCHECK_DIALOGUE),
        ):
            with self.subTest(dialogue_id=block_id):
                block = final_blocks[block_id]
                self.assertEqual((block.width, block.height), (58, 5))
                self.assertEqual(block.text, expected_text)
                self.assertEqual(campaign._campaign_dialogue_layout_issues(block), ())

        # A clear bit branches to ID 11; a set bit falls through to ID 12.
        self.assertEqual(
            expected_action[23:31],
            campaign._bit_test(campaign.STATE_OPERAND, campaign.CHECKIN_BIT_MASK, 0x0D93),
        )
        self.assertEqual(expected_action[31:36], bytes.fromhex("D2 0C 00 00 9C"))
        self.assertEqual(expected_action[39:44], bytes.fromhex("D2 0B 00 00 9C"))

        precheck = _run_appointment_vm(
            final.bytecode,
            start_pc=campaign.INTAKE_RECEPTIONIST_ACTION_PC,
            variables={campaign.STATE_OPERAND: 0},
        )
        waiting = _run_appointment_vm(
            final.bytecode,
            start_pc=campaign.INTAKE_RECEPTIONIST_ACTION_PC,
            variables={
                campaign.STATE_OPERAND: (
                    campaign.CHECKIN_BIT_MASK | campaign.APPOINTMENT_PHASE_ARMED
                )
            },
        )
        self.assertEqual(precheck["dialogue_ids"], (11,))
        self.assertEqual(waiting["dialogue_ids"], (12,))
        self.assertEqual(waiting["control_suspends"], 1)
        self.assertEqual(waiting["control_restores"], 1)

    def test_intake_wandering_survivors_stay_inside_archive_door(self) -> None:
        before_item = self.base_field_by_scene[621]
        final_item = self.field_by_scene[621]
        before = ScriptEditor(before_item.components[base.SCRIPT_INDEX])
        final = ScriptEditor(final_item.components[base.SCRIPT_INDEX])

        expected_specs = {
            6: (0x0158, 0, (617, 1471), (617, 1450)),
            7: (0x0165, 1, (1134, 1616), (1122, 1600)),
            8: (0x0172, 2, (1022, 1634), (1020, 1650)),
            9: (0x017F, 3, (726, 1799), (650, 1635)),
            10: (0x018C, 4, (882, 1732), (1020, 1550)),
            11: (0x0199, 5, (1127, 1414), (1090, 1450)),
            12: (0x01A6, 3, (843, 1486), (760, 1460)),
            14: (0x01C4, 1, (746, 1661), (760, 1580)),
            15: (0x01D1, 2, (574, 1637), (595, 1545)),
        }
        expected_zones = {
            6: ((570, 1470), (650, 1470), (650, 1415), (570, 1415)),
            7: ((1100, 1635), (1145, 1635), (1145, 1560), (1100, 1560)),
            8: ((985, 1670), (1050, 1670), (1050, 1630), (985, 1630)),
            9: ((615, 1650), (680, 1650), (680, 1620), (615, 1620)),
            10: ((985, 1580), (1050, 1580), (1050, 1525), (985, 1525)),
            11: ((1060, 1475), (1120, 1475), (1120, 1425), (1060, 1425)),
            12: ((720, 1490), (800, 1490), (800, 1420), (720, 1420)),
            14: ((730, 1610), (790, 1610), (790, 1550), (730, 1550)),
            15: ((565, 1570), (625, 1570), (625, 1520), (565, 1520)),
        }
        self.assertEqual(campaign.INTAKE_WANDERING_SURVIVOR_SPECS, expected_specs)
        self.assertEqual(campaign.INTAKE_SURVIVOR_MOVEMENT_ZONES, expected_zones)
        self.assertEqual(campaign.INTAKE_SURVIVOR_COLLISION_RADIUS, 16)
        self.assertEqual(campaign.INTAKE_SURVIVOR_WALKMESH_HALO, 24)
        self.assertEqual(campaign.INTAKE_SURVIVOR_MIN_ZONE_SEPARATION, 50)
        self.assertEqual(campaign.INTAKE_SURVIVOR_CENTER_AISLE, (824, 946))
        self.assertEqual(campaign.INTAKE_SURVIVOR_MIN_DOCTOR_CLEARANCE, 80)
        self.assertEqual(campaign.INTAKE_ARCHIVE_DOOR_POSITION, (867, 1832))
        self.assertEqual(campaign.INTAKE_SURVIVOR_DOOR_CLEARANCE, 162)
        campaign._validate_intake_survivor_movement_zone(before_item)

        def inside_clockwise_zone(
            point: tuple[int, int],
            zone: tuple[tuple[int, int], ...],
        ) -> bool:
            return all(
                (end[0] - start[0]) * (point[1] - start[1])
                - (end[1] - start[1]) * (point[0] - start[0])
                <= 0
                for start, end in zip(
                    zone,
                    zone[1:] + zone[:1],
                    strict=True,
                )
            )

        triangles = base._walkmesh_layer(before_item.components[1], 0)

        def on_layer_zero(point: tuple[int, int]) -> bool:
            return any(
                base._point_inside_triangle(point, triangle)
                for triangle in triangles
            )

        # The former shared V188 rectangle crossed both side walls.  Its two
        # north corners are not on any layer-0 triangle, so it cannot safely
        # bound even a point actor, much less an actor with collision radius.
        legacy_zone = (
            (500, 1680),
            (1250, 1680),
            (1250, 1350),
            (500, 1350),
        )
        self.assertFalse(on_layer_zero(legacy_zone[0]))
        self.assertFalse(on_layer_zero(legacy_zone[1]))

        # Exact polygon coverage proves the complete 24-unit halo around each
        # rectangle lies in the full layer-0 walkmesh, including its transition
        # triangles.  The halo deliberately exceeds the 16-unit actor radius.
        self.assertGreaterEqual(
            campaign.INTAKE_SURVIVOR_WALKMESH_HALO,
            campaign.INTAKE_SURVIVOR_COLLISION_RADIUS,
        )
        zone_bounds: dict[int, tuple[int, int, int, int]] = {}
        for entity, zone in expected_zones.items():
            with self.subTest(entity=entity, contract="zone geometry"):
                bounds = campaign._intake_survivor_zone_bounds(zone)
                zone_bounds[entity] = bounds
                min_x, max_x, min_z, max_z = bounds
                self.assertEqual(
                    zone,
                    (
                        (min_x, max_z),
                        (max_x, max_z),
                        (max_x, min_z),
                        (min_x, min_z),
                    ),
                )
                position = expected_specs[entity][3]
                self.assertTrue(inside_clockwise_zone(position, zone))
                self.assertTrue(all(inside_clockwise_zone(point, zone) for point in zone))
                for excluded_point in (
                    (min_x - 1, position[1]),
                    (max_x + 1, position[1]),
                    (position[0], min_z - 1),
                    (position[0], max_z + 1),
                ):
                    self.assertFalse(inside_clockwise_zone(excluded_point, zone))

                halo = campaign.INTAKE_SURVIVOR_WALKMESH_HALO
                halo_bounds = (
                    min_x - halo,
                    max_x + halo,
                    min_z - halo,
                    max_z + halo,
                )
                covered_area2 = campaign._intake_walkmesh_rectangle_coverage_area2(
                    triangles,
                    halo_bounds,
                )
                expected_area2 = (
                    2
                    * (halo_bounds[1] - halo_bounds[0])
                    * (halo_bounds[3] - halo_bounds[2])
                )
                self.assertEqual(covered_area2, expected_area2)
                self.assertTrue(
                    all(
                        on_layer_zero(point)
                        for point in (
                            (halo_bounds[0], halo_bounds[2]),
                            (halo_bounds[0], halo_bounds[3]),
                            (halo_bounds[1], halo_bounds[2]),
                            (halo_bounds[1], halo_bounds[3]),
                        )
                    )
                )

                aisle_min_x, aisle_max_x = campaign.INTAKE_SURVIVOR_CENTER_AISLE
                self.assertTrue(max_x < aisle_min_x or min_x > aisle_max_x)

        # Private zones never overlap or approach within one combined actor
        # diameter.  Several deliberate 50-unit gaps pin the exact minimum.
        separation_squared: dict[tuple[int, int], int] = {}
        ordered_zones = sorted(expected_zones.items())
        for index, (first_entity, first_zone) in enumerate(ordered_zones):
            for second_entity, second_zone in ordered_zones[index + 1 :]:
                pair = (first_entity, second_entity)
                distance2 = campaign._intake_survivor_zone_separation_squared(
                    first_zone,
                    second_zone,
                )
                separation_squared[pair] = distance2
                self.assertGreaterEqual(
                    distance2,
                    campaign.INTAKE_SURVIVOR_MIN_ZONE_SEPARATION**2,
                    pair,
                )
                self.assertGreater(
                    distance2,
                    (2 * campaign.INTAKE_SURVIVOR_COLLISION_RADIUS) ** 2,
                    pair,
                )
        self.assertEqual(min(separation_squared.values()), 50**2)
        self.assertEqual(
            {
                pair
                for pair, distance2 in separation_squared.items()
                if distance2 == 50**2
            },
            {(6, 15), (7, 8), (7, 10), (8, 10), (9, 15)},
        )

        # The distributed lanes leave the center aisle and the physician's
        # complete east-side route unobstructed.  The closest route X remains
        # beyond every zone's 24-unit walkmesh halo.
        doctor_route = (
            campaign.INTAKE_DOCTOR_STAGING_POSITION,
            *campaign.INTAKE_DOCTOR_OUTBOUND_WAYPOINTS,
        )
        route_min_x = min(point[0] for point in doctor_route)
        zones_max_x = max(bounds[1] for bounds in zone_bounds.values())
        self.assertEqual(route_min_x - zones_max_x, 55)
        self.assertGreater(
            route_min_x - zones_max_x,
            campaign.INTAKE_SURVIVOR_WALKMESH_HALO,
        )
        doctor_x, doctor_z = campaign.INTAKE_DOCTOR_WAITING_POSITION
        for entity, (min_x, max_x, min_z, max_z) in zone_bounds.items():
            with self.subTest(entity=entity, contract="doctor clearance"):
                delta_x = max(0, min_x - doctor_x, doctor_x - max_x)
                delta_z = max(0, min_z - doctor_z, doctor_z - max_z)
                self.assertGreaterEqual(
                    delta_x * delta_x + delta_z * delta_z,
                    campaign.INTAKE_SURVIVOR_MIN_DOCTOR_CLEARANCE**2,
                )

        starts: set[tuple[int, int]] = set()
        for entity, (init_pc, graphic, retail_position, position) in (
            expected_specs.items()
        ):
            with self.subTest(entity=entity):
                retail_graphic = 6 if entity == 12 else graphic
                retail_init = (
                    b"\x0B"
                    + base._immediate(retail_graphic)
                    + b"\x19"
                    + struct.pack("<hh", *retail_position)
                    + b"\xC0\x00"
                )
                dormant_final_init = (
                    b"\x0B"
                    + base._immediate(graphic)
                    + b"\x19"
                    + struct.pack("<hh", *retail_position)
                    + b"\xC0\x00"
                )
                update_pc = init_pc + len(retail_init)
                self.assertEqual(before.get_script_pointer(entity, 0), init_pc)
                self.assertEqual(
                    before.bytecode[init_pc : init_pc + len(retail_init)],
                    retail_init,
                )
                self.assertEqual(
                    final.bytecode[
                        init_pc : init_pc + len(dormant_final_init)
                    ],
                    dormant_final_init,
                )

                # Random walking remains active in slot 1; only the actor's
                # initializer gains the native four-corner movement limiter.
                self.assertEqual(before.get_script_pointer(entity, 1), update_pc)
                self.assertEqual(final.get_script_pointer(entity, 1), update_pc)
                self.assertEqual(before.bytecode[update_pc : update_pc + 2], b"\x59\x00")
                self.assertEqual(final.bytecode[update_pc : update_pc + 2], b"\x59\x00")
                self.assertEqual(
                    before.get_script_pointer(entity, 3),
                    update_pc + 2,
                )
                self.assertEqual(
                    final.get_script_pointer(entity, 3),
                    update_pc + 2,
                )
                self.assertEqual(final.bytecode[update_pc + 2], 0)

                bounded_pc = final.get_script_pointer(entity, 0)
                zone = expected_zones[entity]
                expected_zone_body = (
                    b"\x17"
                    + b"".join(
                        struct.pack("<h", coordinate)
                        for point in zone
                        for coordinate in point
                    )
                    + b"\xFF"
                )
                self.assertEqual(
                    campaign._intake_survivor_movement_zone_body(zone),
                    expected_zone_body,
                )
                self.assertEqual(len(expected_zone_body), 18)
                expected_bounded_init = (
                    b"\x0B"
                    + base._immediate(graphic)
                    + b"\x19"
                    + struct.pack("<hh", *position)
                    + b"\xC0"
                    + expected_zone_body
                    + b"\x00"
                )
                bounded_init = final.bytecode[
                    bounded_pc : bounded_pc + len(expected_bounded_init)
                ]
                self.assertNotEqual(bounded_pc, init_pc)
                self.assertEqual(bounded_init, expected_bounded_init)
                self.assertEqual(
                    campaign._intake_wandering_survivor_init(
                        graphic=graphic,
                        position=position,
                        zone=zone,
                    ),
                    expected_bounded_init,
                )
                self.assertEqual(len(bounded_init), 28)
                self.assertEqual(bounded_init[9:27], expected_zone_body)
                self.assertEqual(bounded_init[-2:], b"\xFF\x00")
                self.assertNotIn(b"\xFE\x54", bounded_init)
                self.assertNotIn(b"\xFE\x53", bounded_init)
                self.assertNotIn(position, starts)
                starts.add(position)

                # Slot 2 keeps its native dialogue ID through the mutex wrapper;
                # movement repointing must never disturb an interaction action.
                old_action_pc, dialogue_id = campaign.INTAKE_NATIVE_DIALOGUE_ACTIONS[
                    entity
                ]
                native_action = campaign._actor_dialogue(dialogue_id) + b"\x00"
                self.assertEqual(before.get_script_pointer(entity, 2), old_action_pc)
                self.assertEqual(
                    before.bytecode[
                        old_action_pc : old_action_pc + len(native_action)
                    ],
                    native_action,
                )
                wrapper = campaign._intake_native_dialogue_mutex_action(dialogue_id)
                wrapper_pc = final.get_script_pointer(entity, 2)
                self.assertEqual(
                    final.bytecode[wrapper_pc : wrapper_pc + len(wrapper)],
                    wrapper,
                )

        self.assertEqual(
            {
                entity: (retail, bounded)
                for entity, (_pc, _graphic, retail, bounded) in expected_specs.items()
                if retail != bounded
            },
            {
                entity: (spec[2], spec[3])
                for entity, spec in expected_specs.items()
            },
        )
        self.assertEqual(
            campaign.INTAKE_ARCHIVE_DOOR_POSITION[1]
            - max(point[1] for zone in expected_zones.values() for point in zone),
            campaign.INTAKE_SURVIVOR_DOOR_CLEARANCE,
        )
        blocks = parse_dialogue(final_item.components[7]).blocks
        self.assertEqual(campaign.INTAKE_BOY_ENTITY, 11)
        self.assertEqual(
            campaign.INTAKE_NATIVE_DIALOGUE_ACTIONS[campaign.INTAKE_BOY_ENTITY][1],
            campaign.INTAKE_BOY_DIALOGUE_ID,
        )
        self.assertEqual(campaign.INTAKE_BOY_DIALOGUE, "I like turtles!<Close>")
        self.assertEqual(
            blocks[campaign.INTAKE_BOY_DIALOGUE_ID].text,
            "I like turtles!<Close>",
        )

    def test_intake_all_twelve_lobby_dialogue_owners_publish_the_mutex(self) -> None:
        before_item = self.base_field_by_scene[621]
        final_item = self.field_by_scene[621]
        before = ScriptEditor(before_item.components[base.SCRIPT_INDEX])
        final = ScriptEditor(final_item.components[base.SCRIPT_INDEX])
        blocks = parse_dialogue(final_item.components[7]).blocks
        publish = base.mass_driver._set_variable_s16(
            campaign.INTAKE_DIALOG_BUSY_VARIABLE, 1
        )
        clear = base.mass_driver._set_variable_s16(
            campaign.INTAKE_DIALOG_BUSY_VARIABLE, 0
        )
        owners: list[tuple[str, bytes, tuple[bytes, ...]]] = []

        self.assertEqual(
            campaign.INTAKE_NATIVE_DIALOGUE_ACTIONS,
            {
                6: (0x0359, 2),
                7: (0x035F, 3),
                8: (0x0365, 4),
                9: (0x036B, 5),
                10: (0x0371, 6),
                11: (0x0377, 7),
                12: (0x037D, 8),
                14: (0x0383, 9),
                15: (0x0389, 10),
            },
        )
        for entity, (retail_pc, dialogue_id) in (
            campaign.INTAKE_NATIVE_DIALOGUE_ACTIONS.items()
        ):
            retail_body = campaign._actor_dialogue(dialogue_id) + b"\x00"
            wrapper = campaign._intake_native_dialogue_mutex_action(dialogue_id)
            wrapper_pc = final.get_script_pointer(entity, 2)
            with self.subTest(native_dialogue_owner=entity):
                self.assertEqual(before.get_script_pointer(entity, 2), retail_pc)
                self.assertEqual(
                    before.bytecode[retail_pc : retail_pc + len(retail_body)],
                    retail_body,
                )
                # Repointing keeps the retail bodies dormant and byte-exact.
                self.assertEqual(
                    final.bytecode[retail_pc : retail_pc + len(retail_body)],
                    retail_body,
                )
                self.assertNotEqual(wrapper_pc, retail_pc)
                self.assertEqual(
                    final.bytecode[wrapper_pc : wrapper_pc + len(wrapper)],
                    wrapper,
                )
                self.assertEqual(
                    wrapper,
                    publish + campaign._actor_dialogue(dialogue_id) + clear + b"\x00",
                )
                self.assertEqual(
                    blocks[dialogue_id].text,
                    campaign.CAMPAIGN_DIALOGUE_LAYOUT_REPLACEMENTS[621][dialogue_id],
                )
            owners.append(
                (
                    f"entity {entity}",
                    wrapper,
                    (campaign._actor_dialogue(dialogue_id),),
                )
            )

        receptionist_pc = final.get_script_pointer(
            campaign.INTAKE_RECEPTIONIST_ENTITY, 2
        )
        receptionist = campaign._intake_receptionist_action(
            precheck_dialogue_id=11,
            postcheck_dialogue_id=12,
            routine_pc=receptionist_pc,
        )
        self.assertEqual(
            final.bytecode[
                receptionist_pc : receptionist_pc + len(receptionist)
            ],
            receptionist,
        )
        owners.append(
            (
                "receptionist",
                receptionist,
                (
                    campaign._actor_dialogue(11),
                    campaign._actor_dialogue(12),
                ),
            )
        )

        gate_pc = final.get_script_pointer(campaign.INTAKE_CLINIC_DOOR_ENTITY, 2)
        gate = campaign._clinic_door_gate_action(
            old_action_pc=campaign.INTAKE_CLINIC_DOOR_ACTION_PC,
            denial_dialogue_id=20,
            routine_pc=gate_pc,
        )
        self.assertEqual(final.bytecode[gate_pc : gate_pc + len(gate)], gate)
        hidden_owner_dialogue = (
            b"\xF5" + struct.pack("<H", 20) + b"\x01\x9C"
        )
        self.assertIn(hidden_owner_dialogue, gate)
        self.assertNotIn(campaign._actor_dialogue(20), gate)
        owners.append(("clinic door denial", gate, (hidden_owner_dialogue,)))

        lock_pc = final.get_script_pointer(
            campaign.INTAKE_QUARANTINE_DOOR_ENTITY,
            2,
        )
        lock = campaign._intake_quarantine_locked_action(
            dialogue_id=campaign.INTAKE_QUARANTINE_LOCK_DIALOGUE_ID,
            unlocked_action_pc=campaign.INTAKE_QUARANTINE_DOOR_ACTION_PC,
            routine_pc=lock_pc,
        )
        lock_dialogue = (
            b"\xF5"
            + struct.pack("<H", campaign.INTAKE_QUARANTINE_LOCK_DIALOGUE_ID)
            + b"\x01\x9C"
        )
        self.assertEqual(final.bytecode[lock_pc : lock_pc + len(lock)], lock)
        owners.append(("quarantine completion gate", lock, (lock_dialogue,)))

        self.assertEqual(len(owners), 12)
        for label, body, dialogue_bodies in owners:
            with self.subTest(mutex_owner=label):
                self.assertEqual(body.count(publish), 1)
                self.assertEqual(body.count(clear), 1)
                publish_at = body.index(publish)
                clear_at = body.index(clear)
                self.assertLess(publish_at, clear_at)
                for dialogue in dialogue_bodies:
                    dialogue_at = body.index(dialogue)
                    self.assertLess(publish_at, dialogue_at)
                    self.assertLess(dialogue_at, clear_at)

    def test_intake_doctor_yields_for_lobby_dialogue_without_locking_fei(self) -> None:
        item = self.field_by_scene[621]
        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
        update_pc = editor.get_script_pointer(campaign.INTAKE_DOCTOR_ENTITY, 1)
        update = campaign._intake_doctor_update(
            legacy_menu_dialogue_id=13,
            call_dialogue_ids=(14, 15, 16),
            routine_pc=update_pc,
        )
        poll_prefix = (
            b"\x02"
            + struct.pack("<HH", campaign.INTAKE_DIALOG_BUSY_VARIABLE, 0)
            + b"\x41"
        )
        self.assertEqual(update.count(poll_prefix), 1)
        poll_at = update.index(poll_prefix)
        choose_alias_pc = struct.unpack_from("<H", update, poll_at + 6)[0]
        choose_alias_at = choose_alias_pc - update_pc
        wait_loop = (
            poll_prefix
            + struct.pack("<H", choose_alias_pc)
            + base.mass_driver._yield_tick()
            + campaign._jump(update_pc + poll_at)
        )
        self.assertEqual(
            update[poll_at : poll_at + len(wait_loop)], wait_loop
        )
        self.assertEqual(poll_at + len(wait_loop), choose_alias_at)
        self.assertNotIn(b"\xFE\x54", wait_loop)
        self.assertEqual(
            update[choose_alias_at : choose_alias_at + 3], b"\x33\xFE\x54"
        )
        first_automatic_reset = update.index(
            base.mass_driver._actor_dialog_reset_body(), choose_alias_at
        )
        self.assertLess(choose_alias_at, first_automatic_reset)

        close_call = bytes(
            (
                0x09,
                campaign.INTAKE_DOCTOR_DOOR_HELPER_ENTITY,
                0x20 | campaign.INTAKE_DOCTOR_DOOR_CLOSE_SCRIPT,
            )
        )
        outbound = campaign._actor_waypoint_body(
            campaign.INTAKE_DOCTOR_OUTBOUND_WAYPOINTS,
            final_direction=6,
        )
        self.assertLess(update.index(outbound), update.index(close_call))
        self.assertLess(update.index(close_call), poll_at)

        alias = campaign.APPOINTMENT_ALIAS_CODES[0]
        state = campaign.CHECKIN_BIT_MASK | campaign.APPOINTMENT_PHASE_ARMED
        busy = _run_appointment_vm(
            editor.bytecode,
            start_pc=update_pc + poll_at,
            stop_on_zero_wait=True,
            variables={
                campaign.STATE_OPERAND: state,
                campaign.APPOINTMENT_OPERAND: alias,
                campaign.APPOINTMENT_DOCTOR_BUSY_VARIABLE: 1,
                campaign.INTAKE_DIALOG_BUSY_VARIABLE: 1,
            },
        )
        self.assertEqual(busy["reason"], "yield")
        self.assertEqual(busy["dialogue_ids"], ())
        self.assertEqual(busy["control_suspends"], 0)
        self.assertEqual(busy["control_restores"], 0)
        self.assertEqual(
            busy["variables"][campaign.INTAKE_DIALOG_BUSY_VARIABLE], 1
        )

        idle = _run_appointment_vm(
            editor.bytecode,
            start_pc=update_pc + poll_at,
            variables={
                campaign.STATE_OPERAND: state,
                campaign.APPOINTMENT_OPERAND: alias,
                campaign.APPOINTMENT_DOCTOR_BUSY_VARIABLE: 1,
                campaign.INTAKE_DIALOG_BUSY_VARIABLE: 0,
            },
        )
        self.assertEqual(idle["reason"], "stop")
        self.assertEqual(idle["dialogue_ids"], (14,))
        self.assertEqual(idle["control_suspends"], 2)
        self.assertEqual(idle["control_restores"], 1)
        self.assertEqual(
            idle["variables"][campaign.STATE_OPERAND]
            & campaign.APPOINTMENT_PHASE_MASK,
            campaign.APPOINTMENT_PHASE_CALLED,
        )
        self.assertEqual(
            idle["variables"][campaign.APPOINTMENT_DOCTOR_BUSY_VARIABLE], 0
        )

        init_pc = editor.get_script_pointer(campaign.INTAKE_DOCTOR_ENTITY, 0)
        init = campaign._intake_doctor_init(routine_pc=init_pc)
        self.assertTrue(
            init.startswith(
                base.mass_driver._set_variable_s16(
                    campaign.APPOINTMENT_DOCTOR_BUSY_VARIABLE, 0
                )
                + base.mass_driver._set_variable_s16(
                    campaign.INTAKE_DIALOG_BUSY_VARIABLE, 0
                )
                + base.mass_driver._set_variable_s16(
                    campaign.INTAKE_DOCTOR_DOOR_OPEN_VARIABLE, 0
                )
            )
        )

    def test_intake_doctor_entity_dialogue_and_commit_ordering(self) -> None:
        item = self.field_by_scene[621]
        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
        self.assertEqual(
            campaign.CLINIC_EXIT_INSISTENCE_DIALOGUE,
            "The door is locked.<New>Doctor\n"
            '"We need to continue the\n'
            'procedure before you leave."<Close>',
        )
        blocks = parse_dialogue(item.components[7]).blocks
        expected_dialogue = {
            13: campaign.LEGACY_ALIAS_CONFIRM_DIALOGUE,
            14: campaign.DOCTOR_CALL_DIALOGUES[0],
            15: campaign.DOCTOR_CALL_DIALOGUES[1],
            16: campaign.DOCTOR_CALL_DIALOGUES[2],
            17: campaign.DOCTOR_INSTRUCTION_DIALOGUES[0],
            18: campaign.DOCTOR_INSTRUCTION_DIALOGUES[1],
            19: campaign.DOCTOR_INSTRUCTION_DIALOGUES[2],
            20: campaign.CLINIC_DOOR_DENIAL_DIALOGUE,
            21: campaign.INTAKE_QUARANTINE_LOCK_DIALOGUE,
            22: campaign.INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE,
            23: campaign.INTAKE_FREIGHT_AUTHORIZATION_LOCK_DIALOGUE,
        }
        self.assertEqual(len(blocks), 24)
        for block_id, text_value in expected_dialogue.items():
            with self.subTest(dialogue_id=block_id):
                self.assertEqual(
                    (blocks[block_id].width, blocks[block_id].height, blocks[block_id].text),
                    (58, 5, text_value),
                )
                measurable_text = text_value.replace("<Opcode:01:FF>", "")
                measurable = parse_dialogue(
                    encode_dialogue(
                        (DialogueBlockSpec(0, 58, 5, measurable_text),)
                    )
                ).blocks[0]
                self.assertEqual(
                    campaign._campaign_dialogue_layout_issues(measurable),
                    (),
                )
        for alias, text_value in zip(
            campaign.CHECKIN_ALIASES,
            campaign.DOCTOR_INSTRUCTION_DIALOGUES,
            strict=True,
        ):
            with self.subTest(follow_instruction=alias):
                self.assertIn("Follow me into\nthe examination room.", text_value)
                self.assertNotIn("go first", text_value.casefold())

        self.assertEqual(campaign.INTAKE_DOCTOR_ENTITY, 35)
        self.assertEqual(editor.entity_count, 49)
        doctor_record = _actor_records(item.header)[campaign.INTAKE_DOCTOR_ENTITY]
        self.assertEqual(
            doctor_record,
            base.mass_driver._field_actor_record(
                0x01E0,
                campaign.INTAKE_DOCTOR_STAGING_POSITION[0],
                campaign.INTAKE_DOCTOR_STAGING_POSITION[1],
                0,
            ),
        )

        init_pc = editor.get_script_pointer(campaign.INTAKE_DOCTOR_ENTITY, 0)
        action_pc = editor.get_script_pointer(campaign.INTAKE_DOCTOR_ENTITY, 2)
        update_pc = editor.get_script_pointer(campaign.INTAKE_DOCTOR_ENTITY, 1)
        init = campaign._intake_doctor_init(routine_pc=init_pc)
        action = campaign._intake_doctor_action(
            instruction_dialogue_ids=(17, 18, 19),
            routine_pc=action_pc,
        )
        update = campaign._intake_doctor_update(
            legacy_menu_dialogue_id=13,
            call_dialogue_ids=(14, 15, 16),
            routine_pc=update_pc,
        )
        self.assertEqual(editor.bytecode[init_pc : init_pc + len(init)], init)
        self.assertEqual(editor.bytecode[action_pc : action_pc + len(action)], action)
        self.assertEqual(editor.bytecode[update_pc : update_pc + len(update)], update)

        ghost = campaign.DOCTOR_TRANSIT_COLLISION_FLAGS
        solid = campaign.DOCTOR_STATIONARY_COLLISION_FLAGS
        self.assertEqual(ghost, bytes.fromhex("20 01 80"))
        self.assertEqual(solid, bytes.fromhex("20 0C 80"))
        self.assertEqual(
            campaign.DOCTOR_RECTANGULAR_BOUNDING_VOLUME,
            bytes.fromhex("18 10 10 00 00"),
        )
        self.assertEqual(init.count(campaign.DOCTOR_RECTANGULAR_BOUNDING_VOLUME), 1)

        # The hidden staging state remains non-colliding. A called-phase field
        # reload places the physician at reception and immediately restores the
        # ordinary NPC 0x20/0x10 collision class instead of leaving bit 0x80.
        waiting_pose = (
            b"\x19"
            + campaign._s16(campaign.INTAKE_DOCTOR_WAITING_POSITION[0])
            + campaign._s16(campaign.INTAKE_DOCTOR_WAITING_POSITION[1])
            + b"\xC0\x1A\x00\x69\x06\x80"
        )
        staging_pose = (
            b"\x19"
            + campaign._s16(campaign.INTAKE_DOCTOR_STAGING_POSITION[0])
            + campaign._s16(campaign.INTAKE_DOCTOR_STAGING_POSITION[1])
            + b"\xC0\x1A\x00\x69\x06\x80\x23"
        )
        self.assertEqual(init.count(ghost), 1)
        self.assertEqual(init.count(solid), 1)
        self.assertIn(waiting_pose + solid, init)
        self.assertIn(staging_pose, init)
        self.assertLess(init.index(solid), init.index(staging_pose))

        close_pc = editor.get_script_pointer(
            campaign.INTAKE_DOCTOR_DOOR_HELPER_ENTITY,
            campaign.INTAKE_DOCTOR_DOOR_CLOSE_SCRIPT,
        )
        close = base.mass_driver._world_position_static_slide_body(
            start_x=0,
            start_z=campaign.INTAKE_DOCTOR_DOOR_OPEN_OFFSET_Z,
            delta_x=0,
            delta_z=-2,
            iterations=campaign.INTAKE_DOCTOR_DOOR_SLIDE_FRAMES,
        )
        self.assertEqual(editor.bytecode[close_pc : close_pc + len(close)], close)

        outbound = campaign._actor_waypoint_body(
            campaign.INTAKE_DOCTOR_OUTBOUND_WAYPOINTS,
            final_direction=6,
        )
        open_call = bytes(
            (0x09, campaign.INTAKE_DOCTOR_DOOR_HELPER_ENTITY, 0x24)
        )
        show_doctor = bytes((0x24, campaign.INTAKE_DOCTOR_ENTITY))
        close_call = bytes(
            (
                0x09,
                campaign.INTAKE_DOCTOR_DOOR_HELPER_ENTITY,
                0x20 | campaign.INTAKE_DOCTOR_DOOR_CLOSE_SCRIPT,
            )
        )
        self.assertLess(update.index(open_call), update.index(show_doctor))
        self.assertLess(update.index(show_doctor), update.index(outbound))
        self.assertLess(update.index(outbound), update.index(close_call))
        transit_at = update.index(ghost)
        stationary_at = update.index(solid)
        self.assertLess(transit_at, update.index(open_call))
        self.assertLess(update.index(outbound), stationary_at)
        self.assertLess(update.index(close_call), stationary_at)
        self.assertEqual(update.count(ghost), 1)
        self.assertEqual(update.count(solid), 1)
        open_flag = base.mass_driver._set_variable_s16(
            campaign.INTAKE_DOCTOR_DOOR_OPEN_VARIABLE, 1
        )
        closed_flag = base.mass_driver._set_variable_s16(
            campaign.INTAKE_DOCTOR_DOOR_OPEN_VARIABLE, 0
        )
        self.assertLess(update.index(open_call), update.index(open_flag))
        self.assertLess(update.index(open_flag), update.index(show_doctor))
        self.assertLess(update.index(close_call), update.index(closed_flag))
        self.assertLess(update.index(closed_flag), stationary_at)

        busy_set = base.mass_driver._set_variable_s16(
            campaign.APPOINTMENT_DOCTOR_BUSY_VARIABLE, 1
        )
        emerge_at = update.index(busy_set)
        outbound_end = update.index(outbound) + len(outbound)
        self.assertLess(emerge_at, update.index(open_call))
        self.assertNotIn(b"\xFE\x54", update[emerge_at:outbound_end])

        called_commit = campaign._appointment_phase_body(
            campaign.APPOINTMENT_PHASE_CALLED
        )
        self.assertEqual(update.count(called_commit), 1)
        commit_at = update.index(called_commit)
        reset_and_drain = (
            base.mass_driver._actor_dialog_reset_body() + b"\x33\xFE\x54"
        )
        for dialogue_id in (14, 15, 16):
            with self.subTest(call_dialogue=dialogue_id):
                dialogue_at = update.index(
                    b"\xF5" + struct.pack("<H", dialogue_id) + b"\x00"
                )
                automatic_at = update.rfind(reset_and_drain, 0, dialogue_at + 1)
                self.assertGreaterEqual(automatic_at, 0)
                automatic = base.mass_driver._automatic_dialogue_body(
                    (dialogue_id,),
                    routine_pc=update_pc + automatic_at,
                    reset_actor_dialog_state=True,
                )
                self.assertEqual(
                    update[automatic_at : automatic_at + len(automatic)],
                    automatic,
                )
                self.assertIn(bytes.fromhex("31 20 00"), automatic)
                self.assertIn(bytes.fromhex("26 01 80 F5"), automatic)
                self.assertIn(b"\x9C", automatic)
                self.assertTrue(automatic.endswith(bytes.fromhex("FE 53")))
                self.assertLessEqual(automatic_at + len(automatic), commit_at)

        interaction_at = action.index(b"\x33\xFE\x54")
        interaction_drain = (
            b"\x33\xFE\x54"
            + base.mass_driver._wait_for_pad_release(
                base.mass_driver.PAD_MASK_CROSS,
                action_pc + interaction_at + 3,
            )
            + base.mass_driver._wait()
        )
        self.assertGreater(interaction_at, 0)
        self.assertEqual(
            action[interaction_at : interaction_at + len(interaction_drain)],
            interaction_drain,
        )
        returned = campaign._actor_waypoint_body(
            campaign.INTAKE_DOCTOR_RETURN_WAYPOINTS,
            final_direction=6,
        )
        entered_commit = campaign._appointment_phase_body(
            campaign.APPOINTMENT_PHASE_ENTERED
        )
        restore_at = action.index(b"\xFE\x53")
        return_open_at = action.index(open_call)
        returned_at = action.index(returned)
        action_transit_at = action.index(ghost)
        self.assertLess(action_transit_at, restore_at)
        self.assertEqual(action.count(ghost), 1)
        self.assertNotIn(solid, action)
        self.assertEqual(restore_at + 2, return_open_at)
        self.assertLess(return_open_at, returned_at)
        self.assertLess(return_open_at, action.index(open_flag))
        self.assertLess(action.index(open_flag), returned_at)
        self.assertNotIn(b"\xFE\x54", action[restore_at:])
        self.assertLess(returned_at, action.index(b"\x23", returned_at))
        self.assertNotIn(close_call, action)
        self.assertNotIn(closed_flag, action)
        self.assertLess(action.index(b"\x23", returned_at), action.index(entered_commit))
        self.assertTrue(action.endswith(b"\x00"))
        for player_script in range(32):
            self.assertNotIn(
                bytes((0x07, 0x01, 0x20 | player_script)), action
            )

        receptionist = campaign._intake_receptionist_action(
            precheck_dialogue_id=11,
            postcheck_dialogue_id=12,
            routine_pc=campaign.INTAKE_RECEPTIONIST_ACTION_PC,
        )
        self.assertNotIn(open_flag, receptionist)
        self.assertNotIn(closed_flag, receptionist)

        for label, state, busy in (
            ("wrong phase", campaign.APPOINTMENT_PHASE_ARMED, 0),
            ("doctor walking", campaign.APPOINTMENT_PHASE_CALLED, 1),
        ):
            with self.subTest(noninteractive_state=label):
                result = _run_appointment_vm(
                    editor.bytecode,
                    start_pc=action_pc,
                    variables={
                        campaign.STATE_OPERAND: state,
                        campaign.APPOINTMENT_OPERAND: (
                            campaign.APPOINTMENT_ALIAS_CODES[0]
                        ),
                        campaign.APPOINTMENT_DOCTOR_BUSY_VARIABLE: busy,
                    },
                )
                self.assertEqual(result["reason"], "stop")
                self.assertEqual(result["control_suspends"], 0)
                self.assertEqual(result["control_restores"], 0)

    def test_intake_doctor_waits_on_flat_walkmesh_clear_of_v184_capture(self) -> None:
        item = self.field_by_scene[621]
        self.assertEqual(campaign.INTAKE_DOCTOR_WAITING_POSITION, (1200, 1400))
        self.assertEqual(campaign.INTAKE_DOCTOR_WAITING_TRIANGLE, 36)
        self.assertEqual(
            campaign.INTAKE_DOCTOR_RETURN_WAYPOINTS,
            tuple(reversed(campaign.INTAKE_DOCTOR_OUTBOUND_WAYPOINTS[:-1]))
            + (campaign.INTAKE_DOCTOR_STAGING_POSITION,),
        )
        campaign._validate_intake_doctor_route(item)

        triangles = base._walkmesh_layer(item.components[1], 0)
        waiting_hits = tuple(
            index
            for index, triangle in enumerate(triangles)
            if base._point_inside_triangle(
                campaign.INTAKE_DOCTOR_WAITING_POSITION,
                triangle,
            )
        )
        self.assertEqual(waiting_hits, (36,))
        self.assertTrue(all(vertex[1] == 0 for vertex in triangles[36]))

        # Slot 1 captured Fei/Elly/Citan piled around the V184 endpoint. The
        # replacement leaves at least 96 world units to each captured actor.
        for captured_position in ((1102, 1412), (1065, 1435), (1018, 1428)):
            with self.subTest(captured_position=captured_position):
                dx = campaign.INTAKE_DOCTOR_WAITING_POSITION[0] - captured_position[0]
                dz = campaign.INTAKE_DOCTOR_WAITING_POSITION[1] - captured_position[1]
                self.assertGreaterEqual(dx * dx + dz * dz, 96 * 96)

        receptionist = (870, 1302)
        dx = campaign.INTAKE_DOCTOR_WAITING_POSITION[0] - receptionist[0]
        dz = campaign.INTAKE_DOCTOR_WAITING_POSITION[1] - receptionist[1]
        self.assertLessEqual(dx * dx + dz * dz, 350 * 350)

        # OP18 doubles each nonzero byte. The 0x10 rectangle therefore gives a
        # normal 32-unit axial contact distance, and even after adding each
        # survivor's radius it stays outside every V198 roaming microzone.
        doctor_half_extent = campaign.DOCTOR_RECTANGULAR_BOUNDING_VOLUME[1] * 2
        self.assertEqual(doctor_half_extent, 32)
        doctor_x, doctor_z = campaign.INTAKE_DOCTOR_WAITING_POSITION
        for entity, zone in campaign.INTAKE_SURVIVOR_MOVEMENT_ZONES.items():
            xs = [point[0] for point in zone]
            zs = [point[1] for point in zone]
            radius = campaign.INTAKE_SURVIVOR_COLLISION_RADIUS
            separated = (
                max(xs) + radius <= doctor_x - doctor_half_extent
                or min(xs) - radius >= doctor_x + doctor_half_extent
                or max(zs) + radius <= doctor_z - doctor_half_extent
                or min(zs) - radius >= doctor_z + doctor_half_extent
            )
            with self.subTest(doctor_collision_clearance_entity=entity):
                self.assertTrue(separated)

    def test_v183_slot1_legacy_alias_prompt_is_one_time_and_arms_timer(self) -> None:
        editor = ScriptEditor(self.field_by_scene[621].components[base.SCRIPT_INDEX])
        update_pc = editor.get_script_pointer(campaign.INTAKE_DOCTOR_ENTITY, 1)
        clock = 4_321
        legacy = _run_appointment_vm(
            editor.bytecode,
            start_pc=update_pc,
            stop_on_zero_wait=True,
            menu_choices={13: 2},
            variables={
                campaign.STATE_OPERAND: campaign.CHECKIN_BIT_MASK,
                campaign.APPOINTMENT_OPERAND: 0,
                **_clock_variables(clock),
            },
        )
        self.assertEqual(legacy["reason"], "yield")
        self.assertEqual(legacy["dialogue_ids"], (13,))
        self.assertEqual(legacy["control_suspends"], 1)
        self.assertEqual(legacy["control_restores"], 1)
        values = legacy["variables"]
        self.assertEqual(
            values[campaign.APPOINTMENT_OPERAND],
            campaign.APPOINTMENT_ALIAS_CODES[1]
            | (clock & campaign.APPOINTMENT_TIME_MASK),
        )
        self.assertEqual(
            values[campaign.STATE_OPERAND] & campaign.APPOINTMENT_PHASE_MASK,
            campaign.APPOINTMENT_PHASE_ARMED,
        )

        restored = _run_appointment_vm(
            editor.bytecode,
            start_pc=update_pc,
            stop_on_zero_wait=True,
            variables={
                campaign.STATE_OPERAND: (
                    campaign.CHECKIN_BIT_MASK
                    | campaign.APPOINTMENT_PHASE_ARMED
                ),
                campaign.APPOINTMENT_OPERAND: (
                    campaign.APPOINTMENT_ALIAS_CODES[1] | clock
                ),
                **_clock_variables(clock),
            },
        )
        self.assertEqual(restored["dialogue_ids"], ())
        self.assertEqual(restored["control_suspends"], 0)

        unregistered = _run_appointment_vm(
            editor.bytecode,
            start_pc=update_pc,
            variables={
                campaign.STATE_OPERAND: campaign.APPOINTMENT_PHASE_CALLED,
                campaign.APPOINTMENT_OPERAND: campaign.APPOINTMENT_ALIAS_CODES[0],
                **_clock_variables(clock),
            },
        )
        self.assertEqual(unregistered["reason"], "stop")
        self.assertEqual(
            unregistered["variables"][campaign.STATE_OPERAND]
            & campaign.APPOINTMENT_PHASE_MASK,
            campaign.APPOINTMENT_PHASE_NONE,
        )

    def test_clinic_lobby_gate_allows_only_doctor_entered_phases(self) -> None:
        editor = ScriptEditor(self.field_by_scene[621].components[base.SCRIPT_INDEX])
        gate_pc = editor.get_script_pointer(campaign.INTAKE_CLINIC_DOOR_ENTITY, 2)
        gate = campaign._clinic_door_gate_action(
            old_action_pc=campaign.INTAKE_CLINIC_DOOR_ACTION_PC,
            denial_dialogue_id=20,
            routine_pc=gate_pc,
        )
        self.assertEqual(editor.bytecode[gate_pc : gate_pc + len(gate)], gate)
        closed_door_handoff = campaign._jump(campaign.INTAKE_CLINIC_DOOR_ACTION_PC)
        self.assertEqual(gate.count(closed_door_handoff), 1)
        direct_change = base._change_field(*campaign.INTAKE_CLINIC_DESTINATION)
        self.assertEqual(gate.count(direct_change), 1)
        direct_change_at = gate.index(direct_change)
        follow_at = gate.rfind(b"\x33\xFE\x54", 0, direct_change_at)
        self.assertGreater(follow_at, gate.index(closed_door_handoff))
        follow_body = (
            b"\x33\xFE\x54"
            + base.mass_driver._wait_for_pad_release(
                base.mass_driver.PAD_MASK_CROSS,
                gate_pc + follow_at + 3,
            )
            + base.mass_driver._wait()
            + direct_change
            + b"\x5B"
        )
        self.assertEqual(gate[follow_at : follow_at + len(follow_body)], follow_body)
        self.assertTrue(gate.endswith(follow_body))
        hidden_owner_dialogue = b"\xF5" + struct.pack("<H", 20) + b"\x01\x9C"
        publish = base.mass_driver._set_variable_s16(
            campaign.INTAKE_DIALOG_BUSY_VARIABLE, 1
        )
        clear = base.mass_driver._set_variable_s16(
            campaign.INTAKE_DIALOG_BUSY_VARIABLE, 0
        )
        self.assertIn(hidden_owner_dialogue, gate)
        self.assertNotIn(campaign._actor_dialogue(20), gate)
        self.assertLess(gate.index(publish), gate.index(hidden_owner_dialogue))
        self.assertLess(gate.index(hidden_owner_dialogue), gate.index(clear))

        alias = campaign.APPOINTMENT_ALIAS_CODES[0]
        cases = (
            ("none", campaign.CHECKIN_BIT_MASK | campaign.APPOINTMENT_PHASE_NONE, alias, 0, "stop"),
            ("registered", campaign.CHECKIN_BIT_MASK | campaign.APPOINTMENT_PHASE_REGISTERED, alias, 0, "stop"),
            ("armed", campaign.CHECKIN_BIT_MASK | campaign.APPOINTMENT_PHASE_ARMED, alias, 0, "stop"),
            ("called", campaign.CHECKIN_BIT_MASK | campaign.APPOINTMENT_PHASE_CALLED, alias, 0, "stop"),
            ("entered, live open leaf", campaign.CHECKIN_BIT_MASK | campaign.APPOINTMENT_PHASE_ENTERED, alias, 1, "field_change"),
            ("entered after field reload", campaign.CHECKIN_BIT_MASK | campaign.APPOINTMENT_PHASE_ENTERED, alias, 0, "target"),
            ("briefed", campaign.CHECKIN_BIT_MASK | campaign.APPOINTMENT_PHASE_BRIEFED, alias, 0, "target"),
            ("missing alias", campaign.CHECKIN_BIT_MASK | campaign.APPOINTMENT_PHASE_ENTERED, 0, 1, "stop"),
            ("missing checkin", campaign.APPOINTMENT_PHASE_ENTERED, alias, 1, "stop"),
        )
        for label, state, appointment, door_open, expected_reason in cases:
            with self.subTest(case=label):
                result = _run_appointment_vm(
                    editor.bytecode,
                    start_pc=gate_pc,
                    stop_pcs=(campaign.INTAKE_CLINIC_DOOR_ACTION_PC,),
                    variables={
                        campaign.STATE_OPERAND: state,
                        campaign.APPOINTMENT_OPERAND: appointment,
                        campaign.INTAKE_DOCTOR_DOOR_OPEN_VARIABLE: door_open,
                    },
                )
                self.assertEqual(result["reason"], expected_reason)
                allowed = expected_reason != "stop"
                self.assertEqual(result["dialogue_ids"], () if allowed else (20,))
                self.assertEqual(
                    result["field_change"],
                    campaign.INTAKE_CLINIC_DESTINATION
                    if expected_reason == "field_change"
                    else None,
                )
                self.assertEqual(
                    result["control_suspends"],
                    1 if expected_reason in ("stop", "field_change") else 0,
                )
                self.assertEqual(
                    result["control_restores"],
                    1 if expected_reason == "stop" else 0,
                )

    def test_field550_is_ethos_office_with_safe_briefing_and_return(self) -> None:
        source_bundle, source_graphics = campaign._load_clinic_source(DONOR_DISC)
        source = parse_field(source_bundle)
        source_components = tuple(part.data for part in source.parts)
        source_editor = ScriptEditor(source_components[base.SCRIPT_INDEX])
        source_blocks = parse_dialogue(source_components[7]).blocks
        self.assertEqual(
            (len(source_bundle), _sha256(source_bundle)),
            (campaign.CLINIC_SOURCE_BUNDLE_SIZE, campaign.CLINIC_SOURCE_BUNDLE_SHA256),
        )
        self.assertEqual(
            (len(source_graphics), _sha256(source_graphics)),
            (campaign.CLINIC_SOURCE_GRAPHICS_SIZE, campaign.CLINIC_SOURCE_GRAPHICS_SHA256),
        )
        self.assertEqual(
            (
                source_editor.entity_count,
                source_editor.bytecode_size,
                len(_actor_records(source.header)),
                len(source_blocks),
            ),
            (19, 0x068C, 33, 53),
        )

        item = self.donor_by_scene[550]
        self.assertEqual(
            (item.identity.bundle_id, item.identity.graphics_id),
            (
                base.DONOR_BY_SCENE[550].bundle_id,
                base.DONOR_BY_SCENE[550].graphics_id,
            ),
        )
        self.assertEqual(item.graphics, source_graphics)
        for component_index in (0, 1, 2, 8):
            with self.subTest(preserved_component=component_index):
                self.assertEqual(item.components[component_index], source_components[component_index])
        for component_index in (3, 4, 5, 6, 7):
            with self.subTest(clinic_component=component_index):
                self.assertNotEqual(item.components[component_index], source_components[component_index])
        self.assertEqual(
            _sha256(item.components[base.mass_driver.ACTOR_INDEX]),
            campaign.CLINIC_SECURITY_INSTALLED_ACTOR_COMPONENT_SHA256,
        )
        self.assertEqual(
            _sha256(item.components[base.mass_driver.SPRITE_INDEX]),
            campaign.CLINIC_SECURITY_INSTALLED_SPRITE_COMPONENT_SHA256,
        )

        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
        self.assertEqual(editor.bytecode[1:8], campaign.CLINIC_ENTRY_PLAYABLE)
        self.assertEqual(item.entry_triangles, ((campaign.CLINIC_ENTRY_PARAMETER, campaign.CLINIC_ENTRY_TRIANGLE),))
        self.assertEqual(EncounterTable(item.components[6]).weights, (0,) * 16)

        retained = {
            (0, 0),
            (0, 1),
            *((entity, slot) for entity in campaign.CLINIC_PARTY_ENTITIES for slot in (0, 1)),
            *(
                (entity, slot)
                for entity in campaign.CLINIC_RECORD_TERMINAL_ENTITIES
                for slot in (0, 2)
            ),
            (campaign.CLINIC_DOCTOR_ENTITY, 0),
            (campaign.CLINIC_DOCTOR_ENTITY, 1),
            (campaign.CLINIC_DOCTOR_ENTITY, 2),
            (campaign.CLINIC_EXIT_ENTITY, 0),
            (campaign.CLINIC_EXIT_ENTITY, 2),
            (campaign.CLINIC_EXIT_HELPER_ENTITY, 0),
            (campaign.CLINIC_EXIT_HELPER_ENTITY, 4),
            (campaign.CLINIC_EXIT_HELPER_ENTITY, 5),
        }
        self.assertEqual(editor.bytecode[campaign.CLINIC_SHARED_STOP_PC], 0)
        for entity in range(19):
            for slot in range(32):
                if (entity, slot) not in retained:
                    with self.subTest(retired_entity=entity, retired_slot=slot):
                        self.assertEqual(
                            editor.get_script_pointer(entity, slot),
                            campaign.CLINIC_SHARED_STOP_PC,
                        )

        self.assertEqual(
            editor.bytecode[
                campaign.CLINIC_EXIT_HELPER_PC :
                campaign.CLINIC_EXIT_HELPER_PC + len(campaign.CLINIC_EXIT_HELPER_BODY)
            ],
            campaign.CLINIC_EXIT_HELPER_BODY,
        )

        blocks = parse_dialogue(item.components[7]).blocks
        self.assertEqual(campaign.CLINIC_SECURITY_KEYCARD_DIALOGUE_ID, 60)
        expected_dialogues = {
            **{
                dialogue_id: text
                for dialogue_id, text in zip(
                    campaign.CLINIC_RECORD_ALIAS_DIALOGUE_IDS,
                    campaign.CLINIC_RECORD_DIALOGUES,
                    strict=True,
                )
            },
            campaign.CLINIC_RECORD_MISSING_DIALOGUE_ID: (
                campaign.CLINIC_RECORD_MISSING_DIALOGUE
            ),
            campaign.CLINIC_BRIEFING_DIALOGUE_ID: campaign.CLINIC_BRIEFING_DIALOGUE,
            campaign.CLINIC_EXIT_INSISTENCE_DIALOGUE_ID: campaign.CLINIC_EXIT_INSISTENCE_DIALOGUE,
            campaign.CLINIC_FIRST_REFUSAL_DIALOGUE_ID: campaign.CLINIC_FIRST_REFUSAL_DIALOGUE,
            campaign.CLINIC_SECURITY_CALL_DIALOGUE_ID: campaign.CLINIC_SECURITY_CALL_DIALOGUE,
            campaign.CLINIC_SECURITY_ARRIVAL_DIALOGUE_ID: campaign.CLINIC_SECURITY_ARRIVAL_DIALOGUE,
            campaign.CLINIC_DOCTOR_ESCAPE_DIALOGUE_ID: campaign.CLINIC_DOCTOR_ESCAPE_DIALOGUE,
            campaign.CLINIC_ESCAPE_IN_PROGRESS_DIALOGUE_ID: campaign.CLINIC_ESCAPE_IN_PROGRESS_DIALOGUE,
            campaign.CLINIC_SECURITY_KEYCARD_DIALOGUE_ID: campaign.CLINIC_SECURITY_KEYCARD_DIALOGUE,
        }
        self.assertEqual(len(blocks), 61)
        for dialogue_id, expected_text in expected_dialogues.items():
            with self.subTest(clinic_dialogue=dialogue_id):
                block = blocks[dialogue_id]
                expected_height = (
                    3
                    if dialogue_id == campaign.CLINIC_RECORD_MISSING_DIALOGUE_ID
                    else 5
                )
                self.assertEqual(
                    (block.width, block.height, block.text),
                    (58, expected_height, expected_text),
                )
                measurable = re.sub(
                    r"<Opcode:0A:(?:00|01)>", "255", block.text
                )
                measurable_block = parse_dialogue(
                    encode_dialogue(
                        (
                            DialogueBlockSpec(
                                0,
                                block.width,
                                block.height,
                                measurable,
                            ),
                        )
                    )
                ).blocks[0]
                self.assertEqual(
                    campaign._campaign_dialogue_layout_issues(measurable_block),
                    (),
                )

        terminal_inits = tuple(
            campaign._console_init(console)
            for console in campaign.CLINIC_RECORD_TERMINALS
        )
        terminal_init_pcs = (
            campaign.CLINIC_RECORD_TERMINAL_INIT_PC,
            *campaign.CLINIC_RECORD_TERMINAL_AUX_INIT_PCS,
        )
        terminal_action = campaign._clinic_record_terminal_action(
            alias_dialogue_ids=campaign.CLINIC_RECORD_ALIAS_DIALOGUE_IDS,
            missing_dialogue_id=campaign.CLINIC_RECORD_MISSING_DIALOGUE_ID,
            routine_pc=campaign.CLINIC_RECORD_TERMINAL_ACTION_PC,
        )
        self.assertEqual(
            (
                campaign.CLINIC_RECORD_TERMINAL_ENTITIES,
                tuple(
                    (console.x, console.z)
                    for console in campaign.CLINIC_RECORD_TERMINALS
                ),
                tuple(console.triangle for console in campaign.CLINIC_RECORD_TERMINALS),
                terminal_init_pcs,
            ),
            (
                (4, 5, 6),
                ((80, -167), (116, -167), (152, -167)),
                (31, 6, 6),
                (0x054B, 0x05F1, 0x060E),
            ),
        )
        for entity, console, init_pc, terminal_init in zip(
            campaign.CLINIC_RECORD_TERMINAL_ENTITIES,
            campaign.CLINIC_RECORD_TERMINALS,
            terminal_init_pcs,
            terminal_inits,
            strict=True,
        ):
            with self.subTest(terminal_carrier=entity):
                self.assertEqual(editor.get_script_pointer(entity, 0), init_pc)
                self.assertEqual(
                    editor.get_script_pointer(entity, 2),
                    campaign.CLINIC_RECORD_TERMINAL_ACTION_PC,
                )
                self.assertEqual(
                    editor.bytecode[init_pc : init_pc + len(terminal_init)],
                    terminal_init,
                )
                self.assertIn(b"\xF8\x03\x04\x00", terminal_init)
                self.assertNotIn(b"\xF8\x07\x04\x00", terminal_init)
                self.assertEqual(
                    (
                        console.interaction_half_width,
                        console.interaction_half_depth,
                        console.requires_facing,
                    ),
                    (0x01, 0x0F, True),
                )
        self.assertEqual(
            editor.bytecode[
                campaign.CLINIC_RECORD_TERMINAL_ACTION_PC :
                campaign.CLINIC_RECORD_TERMINAL_ACTION_PC + len(terminal_action)
            ],
            terminal_action,
        )
        self.assertEqual(terminal_action.count(b"\xFE\x69"), 1)
        self.assertNotIn(b"\xFE\x6B", terminal_action)
        terminal_record = _actor_records(item.header)[
            campaign.CLINIC_RECORD_TERMINAL_STATIC_NODE
        ]
        self.assertEqual(
            struct.unpack_from("<H", terminal_record, 14)[0],
            campaign.CLINIC_RECORD_TERMINAL_STATIC_MODEL,
        )
        terminal_model = _indexed_entries(item.components[2])[
            campaign.CLINIC_RECORD_TERMINAL_STATIC_MODEL
        ]
        self.assertEqual(
            _single_block_model_aabb(terminal_model),
            ((167, 220), (-92, 0), (11, 164)),
        )
        terminal_yaw = struct.unpack_from("<h", terminal_record, 4)[0]
        self.assertEqual(terminal_yaw, 0x0400)
        terminal_world_aabb = ((11, 164), (-92, 0), (-220, -167))
        self.assertTrue(
            all(
                terminal_world_aabb[0][0]
                <= console.x
                <= terminal_world_aabb[0][1]
                for console in campaign.CLINIC_RECORD_TERMINALS
            )
        )
        self.assertEqual(
            tuple(console.z for console in campaign.CLINIC_RECORD_TERMINALS),
            (terminal_world_aabb[2][1],) * 3,
        )
        triangles = base._walkmesh_layer(item.components[1], 0)
        for console in campaign.CLINIC_RECORD_TERMINALS:
            self.assertEqual(
                tuple(
                    index
                    for index, triangle in enumerate(triangles)
                    if base._point_inside_triangle(
                        (console.x, console.z), triangle
                    )
                ),
                (),
            )
        saved_terminal_facing_fei = (70.00340270996094, -142.5971221923828)
        saved_bed_facing_fei = (76.045181, -126.168945)
        terminal_reaches = tuple(
            (
                console.interaction_half_width * 2 + 16,
                console.interaction_half_depth * 2 + 16,
            )
            for console in campaign.CLINIC_RECORD_TERMINALS
        )
        self.assertEqual(terminal_reaches, ((18, 46),) * 3)

        def in_terminal_reach(
            fei: tuple[float, float], console: campaign.Console
        ) -> bool:
            reach_x = console.interaction_half_width * 2 + 16
            reach_z = console.interaction_half_depth * 2 + 16
            return (
                abs(fei[0] - console.x) <= reach_x
                and abs(fei[1] - console.z) <= reach_z
            )

        self.assertTrue(
            in_terminal_reach(
                saved_terminal_facing_fei,
                campaign.CLINIC_RECORD_TERMINALS[0],
            )
        )
        self.assertTrue(
            in_terminal_reach(
                saved_bed_facing_fei,
                campaign.CLINIC_RECORD_TERMINALS[0],
            )
        )
        self.assertEqual(
            campaign.CLINIC_RECORD_TERMINAL_OPERATOR_TRIANGLES,
            (31, 30, 6, 7),
        )
        operator_triangles = tuple(
            triangles[index]
            for index in campaign.CLINIC_RECORD_TERMINAL_OPERATOR_TRIANGLES
        )
        self.assertEqual(
            tuple(
                (
                    min(vertex[0] for vertex in triangle),
                    max(vertex[0] for vertex in triangle),
                    min(vertex[2] for vertex in triangle),
                    max(vertex[2] for vertex in triangle),
                )
                for triangle in operator_triangles
            ),
            (
                (70, 91, -146, -107),
                (70, 91, -131, -88),
                (91, 176, -131, -87),
                (91, 176, -131, -87),
            ),
        )
        # F4 0x00040000 uses Noah's integer ratan2 result and accepts an
        # unsigned yaw delta below 700 or above 3396.  Mirror that path exactly
        # (including the fixed-point arithmetic shift for negative positions)
        # so a floating-point approximation cannot hide a one-unit cone error.
        def noah_target_yaw(
            fei: tuple[float, float], console: campaign.Console
        ) -> int:
            engine_x, engine_z = (math.floor(axis) for axis in fei)
            delta_x = console.x - engine_x
            delta_z = console.z - engine_z
            return (-base.mass_driver._noah_ratan2(delta_z, delta_x)) & 0x0FFF

        def native_facing(yaw: int, target_yaw: int) -> tuple[int, bool]:
            delta = (yaw - target_yaw) & 0x0FFF
            return delta, delta < 700 or delta > 3396

        first_terminal = campaign.CLINIC_RECORD_TERMINALS[0]
        terminal_target_yaw = noah_target_yaw(
            saved_terminal_facing_fei, first_terminal
        )
        bed_target_yaw = noah_target_yaw(saved_bed_facing_fei, first_terminal)
        self.assertEqual(
            (
                terminal_target_yaw,
                native_facing(0x0400, terminal_target_yaw),
                bed_target_yaw,
                native_facing(0x0400, bed_target_yaw),
                native_facing(0x0800, bed_target_yaw),
            ),
            (
                0x02FF,
                (257, True),
                0x03BF,
                (65, True),
                (1089, False),
            ),
        )
        self.assertEqual(
            tuple(
                native_facing((bed_target_yaw + offset) & 0x0FFF, bed_target_yaw)
                for offset in (699, -699, 700, -700)
            ),
            ((699, True), (3397, True), (700, False), (3396, False)),
        )

        # Exhaust every integer point on the four room-level walkmesh triangles
        # which reach model 3's accessible x=70..164 frontage.  Three narrow
        # targets cover all of it when Fei faces the bank, but even the closest
        # target remains outside the native cone when Fei faces the bed.
        frontage_x = (70, terminal_world_aabb[0][1])
        terminal_z_reach = terminal_reaches[0][1]
        eligible_walkmesh_points = tuple(
            (x, z)
            for x in range(frontage_x[0], frontage_x[1] + 1)
            for z in range(
                terminal_world_aabb[2][1] - terminal_z_reach,
                terminal_world_aabb[2][1] + terminal_z_reach + 1,
            )
            if any(
                base._point_inside_triangle((x, z), triangle)
                for triangle in operator_triangles
            )
        )
        self.assertEqual(len(eligible_walkmesh_points), 1201)
        self.assertTrue(
            all(
                any(
                    in_terminal_reach(point, console)
                    and native_facing(
                        0x0400, noah_target_yaw(point, console)
                    )[1]
                    for console in campaign.CLINIC_RECORD_TERMINALS
                )
                for point in eligible_walkmesh_points
            )
        )
        bed_heading_results = tuple(
            (
                point,
                (console.x, console.z),
                noah_target_yaw(point, console),
                native_facing(0x0800, noah_target_yaw(point, console)),
            )
            for point in eligible_walkmesh_points
            for console in campaign.CLINIC_RECORD_TERMINALS
            if in_terminal_reach(point, console)
        )
        self.assertEqual(len(bed_heading_results), 1223)
        self.assertFalse(any(result[3][1] for result in bed_heading_results))
        self.assertEqual(
            min(
                bed_heading_results,
                key=lambda result: min(result[3][0], 0x1000 - result[3][0]),
            ),
            ((98, -131), (80, -167), 0x052E, (722, False)),
        )
        terminal_z_max = max(
            console.z + terminal_reaches[index][1]
            for index, console in enumerate(campaign.CLINIC_RECORD_TERMINALS)
        )
        doctor_z_min = (
            campaign.CLINIC_DOCTOR_POSITION[1]
            - campaign.DOCTOR_RECTANGULAR_BOUNDING_VOLUME[2] * 2
            - 16
        )
        self.assertEqual((terminal_z_max, doctor_z_min), (-121, -96))
        self.assertLess(terminal_z_max, doctor_z_min)
        self.assertEqual(
            campaign.CLINIC_RECORD_TERMINAL_ACTION_PC + len(terminal_action),
            campaign.CLINIC_RECORD_TERMINAL_AUX_INIT_PCS[0],
        )
        self.assertEqual(
            campaign.CLINIC_RECORD_TERMINAL_AUX_INIT_PCS[1]
            + len(terminal_inits[2]),
            campaign.CLINIC_RECORD_TERMINAL_PAYLOAD_END_PC,
        )
        self.assertEqual(
            editor.bytecode[
                campaign.CLINIC_RECORD_TERMINAL_PAYLOAD_END_PC :
                campaign.CLINIC_RECORD_TERMINAL_CAVITY_END_PC
            ],
            b"\x00" * (
                campaign.CLINIC_RECORD_TERMINAL_CAVITY_END_PC
                - campaign.CLINIC_RECORD_TERMINAL_PAYLOAD_END_PC
            ),
        )

        doctor_init_pc = editor.get_script_pointer(campaign.CLINIC_DOCTOR_ENTITY, 0)
        doctor_action_pc = editor.get_script_pointer(campaign.CLINIC_DOCTOR_ENTITY, 2)
        doctor_update_pc = editor.get_script_pointer(campaign.CLINIC_DOCTOR_ENTITY, 1)
        doctor_init = campaign._clinic_doctor_init(routine_pc=doctor_init_pc)
        doctor_action = campaign._clinic_doctor_action(
            first_refusal_dialogue_id=campaign.CLINIC_FIRST_REFUSAL_DIALOGUE_ID,
            security_call_dialogue_id=campaign.CLINIC_SECURITY_CALL_DIALOGUE_ID,
            routine_pc=doctor_action_pc,
        )
        doctor_update = campaign._clinic_doctor_update(
            briefing_dialogue_id=campaign.CLINIC_BRIEFING_DIALOGUE_ID,
            security_arrival_dialogue_id=(
                campaign.CLINIC_SECURITY_ARRIVAL_DIALOGUE_ID
            ),
            keycard_dialogue_id=campaign.CLINIC_SECURITY_KEYCARD_DIALOGUE_ID,
            escape_dialogue_id=campaign.CLINIC_DOCTOR_ESCAPE_DIALOGUE_ID,
            routine_pc=doctor_update_pc,
        )
        self.assertEqual(
            editor.bytecode[doctor_init_pc : doctor_init_pc + len(doctor_init)],
            doctor_init,
        )
        self.assertEqual(
            editor.bytecode[
                doctor_action_pc : doctor_action_pc + len(doctor_action)
            ],
            doctor_action,
        )
        self.assertEqual(
            editor.bytecode[doctor_update_pc : doctor_update_pc + len(doctor_update)],
            doctor_update,
        )
        ghost = campaign.DOCTOR_TRANSIT_COLLISION_FLAGS
        solid = campaign.DOCTOR_STATIONARY_COLLISION_FLAGS
        show = b"\x24" + bytes((campaign.CLINIC_DOCTOR_ENTITY,))
        self.assertEqual(doctor_init.count(ghost), 1)
        self.assertEqual(doctor_init.count(solid), 1)
        self.assertEqual(
            doctor_init.count(campaign.DOCTOR_RECTANGULAR_BOUNDING_VOLUME), 1
        )
        self.assertIn(solid + show, doctor_init)
        self.assertLess(doctor_init.index(ghost), doctor_init.index(solid))

    def test_clinic_record_terminal_tracks_alias_and_live_fei_weight(self) -> None:
        editor = ScriptEditor(self.donor_by_scene[550].components[base.SCRIPT_INDEX])
        live_native_weight = 76
        for alias_code, dialogue_id in zip(
            campaign.APPOINTMENT_ALIAS_CODES,
            campaign.CLINIC_RECORD_ALIAS_DIALOGUE_IDS,
            strict=True,
        ):
            with self.subTest(alias_code=f"0x{alias_code:04X}"):
                state = (
                    campaign.CHECKIN_BIT_MASK
                    | campaign.APPOINTMENT_PHASE_OFFICE_ACTIVE
                )
                appointment = alias_code | campaign.APPOINTMENT_STAGE_FINAL_WARNING
                result = _simulate_archive_checkin_action(
                    editor,
                    initial_state=state,
                    initial_appointment=appointment,
                    menu_choices={},
                    character_weights={0: live_native_weight},
                )
                self.assertEqual(result["dialogue_ids"], (dialogue_id,))
                self.assertEqual(result["state"], state)
                self.assertEqual(result["appointment"], appointment)
                self.assertEqual(result["control_suspends"], 1)
                self.assertEqual(result["control_restores"], 1)
                self.assertEqual(result["screen_opens"], ())
                self.assertEqual(result["screen_closes"], ())
                self.assertEqual(
                    result["variables"][campaign.PATIENT_WEIGHT_WHOLE_DIALOG_VARIABLE],
                    167,
                )
                self.assertEqual(
                    result["variables"][campaign.PATIENT_WEIGHT_FRACTION_DIALOG_VARIABLE],
                    2,
                )

        for initial_state, initial_appointment in (
            (0, 0),
            (campaign.CHECKIN_BIT_MASK, 0),
        ):
            with self.subTest(
                missing_state=f"0x{initial_state:04X}",
                missing_alias=f"0x{initial_appointment:04X}",
            ):
                result = _simulate_archive_checkin_action(
                    editor,
                    initial_state=initial_state,
                    initial_appointment=initial_appointment,
                    menu_choices={},
                    character_weights={0: live_native_weight},
                )
                self.assertEqual(
                    result["dialogue_ids"],
                    (campaign.CLINIC_RECORD_MISSING_DIALOGUE_ID,),
                )
                self.assertEqual(result["state"], initial_state)
                self.assertEqual(result["appointment"], initial_appointment)
                self.assertNotIn(
                    campaign.PATIENT_WEIGHT_WHOLE_DIALOG_VARIABLE,
                    result["variables"],
                )

    def test_clinic_office_stages_briefing_refusals_security_and_recovery(self) -> None:
        item = self.donor_by_scene[550]
        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
        update_pc = editor.get_script_pointer(campaign.CLINIC_DOCTOR_ENTITY, 1)
        action_pc = editor.get_script_pointer(campaign.CLINIC_DOCTOR_ENTITY, 2)
        update = campaign._clinic_doctor_update(
            briefing_dialogue_id=campaign.CLINIC_BRIEFING_DIALOGUE_ID,
            security_arrival_dialogue_id=(
                campaign.CLINIC_SECURITY_ARRIVAL_DIALOGUE_ID
            ),
            keycard_dialogue_id=campaign.CLINIC_SECURITY_KEYCARD_DIALOGUE_ID,
            escape_dialogue_id=campaign.CLINIC_DOCTOR_ESCAPE_DIALOGUE_ID,
            routine_pc=update_pc,
        )
        action = campaign._clinic_doctor_action(
            first_refusal_dialogue_id=campaign.CLINIC_FIRST_REFUSAL_DIALOGUE_ID,
            security_call_dialogue_id=campaign.CLINIC_SECURITY_CALL_DIALOGUE_ID,
            routine_pc=action_pc,
        )

        automatic_prefix = (
            base.mass_driver._actor_dialog_reset_body() + b"\x33\xFE\x54"
        )
        briefing_at = update.index(automatic_prefix)
        briefing = base.mass_driver._automatic_dialogue_body(
            (campaign.CLINIC_BRIEFING_DIALOGUE_ID,),
            routine_pc=update_pc + briefing_at,
            reset_actor_dialog_state=True,
        )
        self.assertEqual(
            update[briefing_at : briefing_at + len(briefing)], briefing
        )
        awaiting = campaign._appointment_stage_body(
            campaign.APPOINTMENT_STAGE_AWAIT_REFUSAL
        )
        active = campaign._appointment_phase_body(
            campaign.APPOINTMENT_PHASE_OFFICE_ACTIVE
        )
        awaiting_at = update.index(awaiting, briefing_at + len(briefing))
        active_at = update.index(active, awaiting_at + len(awaiting))
        self.assertLessEqual(briefing_at + len(briefing), awaiting_at)
        self.assertLess(awaiting_at, active_at)

        alias = campaign.APPOINTMENT_ALIAS_CODES[0]
        entered = _run_appointment_vm(
            editor.bytecode,
            start_pc=update_pc,
            variables={
                campaign.STATE_OPERAND: (
                    campaign.CHECKIN_BIT_MASK
                    | campaign.APPOINTMENT_PHASE_ENTERED
                ),
                campaign.APPOINTMENT_OPERAND: alias,
            },
        )
        self.assertEqual(
            entered["dialogue_ids"],
            (campaign.CLINIC_BRIEFING_DIALOGUE_ID,),
        )
        self.assertEqual(
            entered["variables"][campaign.APPOINTMENT_OPERAND],
            alias | campaign.APPOINTMENT_STAGE_AWAIT_REFUSAL,
        )
        self.assertEqual(
            entered["variables"][campaign.STATE_OPERAND]
            & campaign.APPOINTMENT_PHASE_MASK,
            campaign.APPOINTMENT_PHASE_OFFICE_ACTIVE,
        )

        first_refusal = _run_appointment_vm(
            editor.bytecode,
            start_pc=action_pc,
            variables={
                campaign.STATE_OPERAND: (
                    campaign.CHECKIN_BIT_MASK
                    | campaign.APPOINTMENT_PHASE_OFFICE_ACTIVE
                ),
                campaign.APPOINTMENT_OPERAND: (
                    alias | campaign.APPOINTMENT_STAGE_AWAIT_REFUSAL
                ),
            },
        )
        self.assertEqual(
            first_refusal["dialogue_ids"],
            (campaign.CLINIC_FIRST_REFUSAL_DIALOGUE_ID,),
        )
        self.assertEqual(
            first_refusal["variables"][campaign.APPOINTMENT_OPERAND],
            alias | campaign.APPOINTMENT_STAGE_FINAL_WARNING,
        )
        self.assertEqual(
            (
                first_refusal["control_suspends"],
                first_refusal["control_restores"],
            ),
            (1, 1),
        )

        security_call = _run_appointment_vm(
            editor.bytecode,
            start_pc=action_pc,
            variables={
                campaign.STATE_OPERAND: (
                    campaign.CHECKIN_BIT_MASK
                    | campaign.APPOINTMENT_PHASE_OFFICE_ACTIVE
                ),
                campaign.APPOINTMENT_OPERAND: (
                    alias | campaign.APPOINTMENT_STAGE_FINAL_WARNING
                ),
            },
        )
        self.assertEqual(
            security_call["dialogue_ids"],
            (campaign.CLINIC_SECURITY_CALL_DIALOGUE_ID,),
        )
        self.assertEqual(
            security_call["variables"][campaign.APPOINTMENT_OPERAND],
            alias | campaign.APPOINTMENT_STAGE_SECURITY_PENDING,
        )
        self.assertEqual(
            (
                security_call["control_suspends"],
                security_call["control_restores"],
            ),
            # Keep the second-refusal lock active so the automatic entrance
            # begins without a one-frame control/dialogue race.
            (1, 0),
        )

        security_music = base.mass_driver._play_music(0x14)
        fixed_battle = base.mass_driver._fixed_battle(
            campaign.CLINIC_SECURITY_CONFIGURATION
        )
        music_at = update.index(security_music)
        battle_at = update.index(fixed_battle, music_at + len(security_music))
        sync_at = update.index(b"\xFE\x7F", battle_at + len(fixed_battle))
        victory_stage = campaign._appointment_stage_body(
            campaign.APPOINTMENT_STAGE_FLEE_PENDING
        )
        victory_at = sync_at + 2
        self.assertEqual(
            update[victory_at : victory_at + len(victory_stage)],
            victory_stage,
        )
        self.assertEqual(
            (
                campaign.SECURITY_KEYCARD_ACQUIRED_SOUND_ID,
                campaign.SECURITY_KEYCARD_ACQUIRED_SOUND,
            ),
            (0x37, b"\x74\x37\x80"),
        )
        keycard_sound_at = update.index(
            campaign.SECURITY_KEYCARD_ACQUIRED_SOUND,
            victory_at + len(victory_stage),
        )
        keycard_dialogue = campaign._actor_dialogue(
            campaign.CLINIC_SECURITY_KEYCARD_DIALOGUE_ID
        )
        keycard_dialogue_at = update.index(
            keycard_dialogue,
            keycard_sound_at + len(campaign.SECURITY_KEYCARD_ACQUIRED_SOUND),
        )
        keycard_award = campaign._set_bit(
            campaign.SECURITY_KEYCARD_OPERAND,
            campaign.SECURITY_KEYCARD_BIT_INDEX,
        )
        keycard_at = update.index(
            keycard_award,
            keycard_dialogue_at + len(keycard_dialogue),
        )
        resolved = campaign._appointment_phase_body(
            campaign.APPOINTMENT_PHASE_RESOLVED
        )
        resolved_at = update.index(resolved, keycard_at + len(keycard_award))
        restore_at = update.index(b"\xFE\x53", resolved_at + len(resolved))
        self.assertLess(music_at, battle_at)
        self.assertLess(battle_at, sync_at)
        self.assertLess(victory_at, keycard_sound_at)
        self.assertLess(keycard_sound_at, keycard_dialogue_at)
        self.assertLess(keycard_dialogue_at, keycard_at)
        self.assertLess(keycard_at, resolved_at)
        self.assertLess(resolved_at, restore_at)

        pending_battle = _run_appointment_vm(
            editor.bytecode,
            start_pc=update_pc,
            stop_pcs=(update_pc + music_at,),
            variables={
                campaign.STATE_OPERAND: (
                    campaign.CHECKIN_BIT_MASK
                    | campaign.APPOINTMENT_PHASE_OFFICE_ACTIVE
                ),
                campaign.APPOINTMENT_OPERAND: (
                    alias | campaign.APPOINTMENT_STAGE_SECURITY_PENDING
                ),
            },
        )
        self.assertEqual(pending_battle["reason"], "target")
        self.assertEqual(
            pending_battle["dialogue_ids"],
            (campaign.CLINIC_SECURITY_ARRIVAL_DIALOGUE_ID,),
        )
        self.assertEqual(pending_battle["control_suspends"], 1)

        escape_body = campaign._clinic_doctor_escape_body()
        escape_at = update.index(escape_body)
        for label, phase in (
            ("phase promotion", campaign.APPOINTMENT_PHASE_OFFICE_ACTIVE),
            ("resolved reload", campaign.APPOINTMENT_PHASE_RESOLVED),
        ):
            for already_awarded in (False, True):
                with self.subTest(
                    victory_recovery=label,
                    keycard_already_awarded=already_awarded,
                ):
                    recovered = _run_appointment_vm(
                        editor.bytecode,
                        start_pc=update_pc,
                        stop_pcs=(update_pc + escape_at,),
                        variables={
                            campaign.STATE_OPERAND: (
                                campaign.CHECKIN_BIT_MASK | phase
                            ),
                            campaign.APPOINTMENT_OPERAND: (
                                alias | campaign.APPOINTMENT_STAGE_FLEE_PENDING
                            ),
                            campaign.SECURITY_KEYCARD_OPERAND: (
                                campaign.SECURITY_KEYCARD_MASK
                                if already_awarded
                                else 0
                            ),
                        },
                    )
                    self.assertEqual(recovered["reason"], "target")
                    expected_dialogues = (
                        (campaign.CLINIC_DOCTOR_ESCAPE_DIALOGUE_ID,)
                        if already_awarded
                        else (
                            campaign.CLINIC_SECURITY_KEYCARD_DIALOGUE_ID,
                            campaign.CLINIC_DOCTOR_ESCAPE_DIALOGUE_ID,
                        )
                    )
                    self.assertEqual(
                        recovered["dialogue_ids"],
                        expected_dialogues,
                    )
                    self.assertEqual(
                        recovered["sound_ids"],
                        ()
                        if already_awarded
                        else (campaign.SECURITY_KEYCARD_ACQUIRED_SOUND_ID,),
                    )
                    keycard_writes = tuple(
                        (operand, bit_index)
                        for _pc, operand, bit_index in recovered["bit_writes"]
                        if operand == campaign.SECURITY_KEYCARD_OPERAND
                    )
                    self.assertEqual(
                        keycard_writes,
                        ()
                        if already_awarded
                        else (
                            (
                                campaign.SECURITY_KEYCARD_OPERAND,
                                campaign.SECURITY_KEYCARD_BIT_INDEX,
                            ),
                        ),
                    )
                    self.assertEqual(
                        recovered["variables"][campaign.STATE_OPERAND]
                        & campaign.APPOINTMENT_PHASE_MASK,
                        campaign.APPOINTMENT_PHASE_RESOLVED,
                    )
                    self.assertEqual(
                        recovered["variables"].get(
                            campaign.SECURITY_KEYCARD_OPERAND,
                            0,
                        )
                        & campaign.SECURITY_KEYCARD_MASK,
                        campaign.SECURITY_KEYCARD_MASK,
                    )

        complete_reload = _run_appointment_vm(
            editor.bytecode,
            start_pc=update_pc,
            variables={
                campaign.STATE_OPERAND: (
                    campaign.CHECKIN_BIT_MASK
                    | campaign.APPOINTMENT_PHASE_RESOLVED
                ),
                campaign.APPOINTMENT_OPERAND: (
                    alias | campaign.APPOINTMENT_STAGE_COMPLETE
                ),
                campaign.SECURITY_KEYCARD_OPERAND: (
                    campaign.SECURITY_KEYCARD_MASK
                ),
            },
        )
        self.assertEqual(complete_reload["reason"], "stop")
        self.assertEqual(complete_reload["dialogue_ids"], ())
        self.assertEqual(complete_reload["sound_ids"], ())
        self.assertEqual(complete_reload["bit_writes"], ())
        self.assertEqual(complete_reload["control_suspends"], 0)

    def test_clinic_security_formation_is_exact_and_random_weights_are_zero(self) -> None:
        item = self.donor_by_scene[550]
        table = EncounterTable(item.components[6])
        self.assertEqual(table.weights, (0,) * 16)
        self.assertEqual(
            table.formation(campaign.CLINIC_SECURITY_CONFIGURATION),
            campaign.CLINIC_SECURITY_FORMATION,
        )
        self.assertEqual(
            table.get_weight(campaign.CLINIC_SECURITY_CONFIGURATION), 0
        )
        self.assertEqual(
            _sha256(item.components[6]),
            campaign.CLINIC_SECURITY_ENCOUNTER_SHA256,
        )
        self.assertEqual(campaign.CLINIC_SECURITY_CONFIGURATION, 15)
        self.assertEqual(
            campaign.CLINIC_SECURITY_FORMATION,
            bytes.fromhex(
                "21 C0 30 00 00 00 00 00 02 02 01 01 FF FF FF FF "
                "00 00 00 00 FF FF FF FF 00 00 00 00 FF FF FF FF"
            ),
        )
        self.assertEqual(campaign.CLINIC_SECURITY_FORMATION[2], 0x30)
        self.assertEqual(
            campaign.CLINIC_SECURITY_BRIGHT_ARENA_PROOF_FORMATION,
            bytes.fromhex(
                "21 C0 30 00 00 00 00 00 02 02 FF FF FF FF FF FF "
                "00 00 FF FF FF FF FF FF 00 00 FF FF FF FF FF FF"
            ),
        )
        self.assertEqual(
            campaign.CLINIC_SECURITY_BRIGHT_ARENA_PROOF_FORMATION[:3],
            campaign.CLINIC_SECURITY_FORMATION[:3],
        )
        self.assertEqual(
            campaign.CLINIC_SECURITY_NORMALIZED_CD2_RESOURCES[2871],
            (
                "arena_0x30_geometry_and_textures",
                200_064,
                "4fc4ab2b66e8b701d89ddb7e9b2806d74d1320aa30524e2ff38cbe2e451e2d52",
            ),
        )
        self.assertEqual(
            campaign.CLINIC_SECURITY_NORMALIZED_CD2_RESOURCES[2872],
            (
                "arena_0x30_layout",
                1_556,
                "06099720b9683a2e18b0565c62aed99723a0707ba1ab3e0e08a540bd2dcd7ede",
            ),
        )
        self.assertNotIn(2893, campaign.CLINIC_SECURITY_NORMALIZED_CD2_RESOURCES)
        self.assertNotIn(2894, campaign.CLINIC_SECURITY_NORMALIZED_CD2_RESOURCES)
        self.assertEqual(
            campaign.CLINIC_SECURITY_FORMATION[1]
            & ~campaign.CLINIC_SECURITY_SOURCE_FORMATION[1],
            0x80,
        )

        source_bundle, _graphics = campaign._load_clinic_source(DONOR_DISC)
        source_encounters = EncounterTable(parse_field(source_bundle).parts[6].data)
        for configuration in range(15):
            with self.subTest(preserved_retail_formation=configuration):
                self.assertEqual(
                    table.formation(configuration),
                    source_encounters.formation(configuration),
                )
        self.assertEqual(
            source_encounters.formation(15),
            campaign.CLINIC_RETAIL_SLOT15_FORMATION,
        )

    def test_clinic_security_team_visibly_enters_before_matching_battle(self) -> None:
        item = self.donor_by_scene[550]
        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
        self.assertEqual(editor.entity_count, 24)
        self.assertEqual(
            campaign.CLINIC_SECURITY_ROUTES,
            {
                20: (
                    (8, 261),
                    (-1, 237),
                    (0, 200),
                    (-30, 175),
                    (-55, 140),
                    (-85, 105),
                ),
                21: (
                    (8, 261),
                    (-1, 237),
                    (0, 200),
                    (30, 175),
                    (55, 140),
                    (85, 105),
                ),
                22: (
                    (8, 261),
                    (-1, 237),
                    (0, 200),
                    (-18, 180),
                    (-35, 155),
                ),
                23: (
                    (8, 261),
                    (-1, 237),
                    (0, 200),
                    (18, 180),
                    (35, 155),
                ),
            },
        )
        self.assertEqual(
            campaign.CLINIC_SECURITY_TRIANGLE_ROUTES,
            {
                20: (34, 34, 3, 16, 18, 17, 14),
                21: (34, 34, 3, 16, 16, 15, 15),
                22: (34, 34, 3, 16, 18, 18),
                23: (34, 34, 3, 16, 16, 16),
            },
        )
        self.assertEqual(campaign.CLINIC_SECURITY_REVEAL_POSITION, (8, 261))
        self.assertEqual(
            campaign.CLINIC_SECURITY_FIRST_INTERIOR_POSITION, (-1, 237)
        )
        self.assertEqual(campaign.CLINIC_SECURITY_DOOR_PLANE_Z, 250)
        self.assertEqual(campaign.CLINIC_SECURITY_WAYPOINT_MAX_STEPS, 16)
        self.assertEqual(
            campaign.CLINIC_SECURITY_OVERRIDE_CLEAR_POSITION, (0, 200)
        )
        self.assertEqual(campaign.CLINIC_ACTOR_WALK_STEP_UNITS, 8)
        self.assertEqual(campaign.CLINIC_ACTOR_WALK_SAFETY_STEPS, 8)
        self.assertEqual(
            campaign.CLINIC_DOORWAY_WALKMESH_OVERRIDE_FLAGS, 0x0038
        )
        self.assertEqual(
            campaign.CLINIC_DOORWAY_WALKMESH_OVERRIDE_SET,
            bytes.fromhex("F8 02 38 00"),
        )
        self.assertEqual(
            campaign.CLINIC_DOORWAY_WALKMESH_OVERRIDE_CLEAR,
            bytes.fromhex("F8 06 38 00"),
        )
        self.assertEqual(
            campaign.CLINIC_SECURITY_ENTRY_DELAYS,
            {20: 0, 21: 6, 22: 12, 23: 18},
        )
        campaign._validate_clinic_security_routes(item.components[1])
        walkmesh = item.components[1]
        triangles = base._walkmesh_layer(walkmesh, 0)
        self.assertEqual(
            (len(walkmesh), _sha256(walkmesh)),
            (
                1_948,
                "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d8cca4238393571df",
            ),
        )
        self.assertEqual(
            (
                campaign.CLINIC_SOURCE_WALKMESH_SIZE,
                campaign.CLINIC_SOURCE_WALKMESH_SHA256,
                campaign.CLINIC_WALKMESH_LAYER_COUNT,
                campaign.CLINIC_WALKMESH_LAYER0_TRIANGLE_BYTES,
                campaign.CLINIC_WALKMESH_LAYER0_TRIANGLE_OFFSET,
                campaign.CLINIC_WALKMESH_MATERIAL_OFFSET,
            ),
            (
                1_948,
                "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d8cca4238393571df",
                2,
                0x0230,
                0x0028,
                0x039C,
            ),
        )
        self.assertEqual(struct.unpack_from("<I", walkmesh, 0)[0], 2)
        self.assertEqual(struct.unpack_from("<I", walkmesh, 4)[0], 0x0230)
        self.assertEqual(campaign.CLINIC_WALKMESH_EXTERIOR_TRIANGLES, (34, 35))
        self.assertEqual(
            struct.unpack_from("<I", walkmesh, 0x14)[0],
            campaign.CLINIC_WALKMESH_MATERIAL_OFFSET,
        )
        self.assertEqual(
            struct.unpack_from("<I", walkmesh, 0x18)[0],
            campaign.CLINIC_WALKMESH_LAYER0_TRIANGLE_OFFSET,
        )
        for triangle in campaign.CLINIC_WALKMESH_EXTERIOR_TRIANGLES:
            with self.subTest(exterior_material_triangle=triangle):
                self.assertEqual(
                    campaign._clinic_walkmesh_material(walkmesh, triangle),
                    (0, 0x00800000),
                )
        for triangle in (3, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18):
            with self.subTest(interior_material_triangle=triangle):
                self.assertEqual(
                    campaign._clinic_walkmesh_material(walkmesh, triangle),
                    (1, 0),
                )
        expected_required_steps = {
            20: (12, 13, 13, 14, 14),
            21: (12, 13, 13, 14, 14),
            22: (12, 13, 12, 12),
            23: (12, 13, 12, 12),
        }
        for entity, route in campaign.CLINIC_SECURITY_ROUTES.items():
            with self.subTest(security_step_budget=entity):
                required = tuple(
                    campaign._required_clinic_waypoint_steps(start, finish)
                    for start, finish in zip(route, route[1:], strict=False)
                )
                self.assertEqual(required, expected_required_steps[entity])
                self.assertTrue(
                    all(
                        steps <= campaign.CLINIC_SECURITY_WAYPOINT_MAX_STEPS
                        for steps in required
                    )
                )
        self.assertEqual(
            tuple(
                index
                for index, triangle in enumerate(triangles)
                if base._point_inside_triangle(
                    campaign.CLINIC_SECURITY_REVEAL_POSITION, triangle
                )
            ),
            (34,),
        )
        self.assertEqual(
            tuple(
                index
                for index, triangle in enumerate(triangles)
                if base._point_inside_triangle(
                    campaign.CLINIC_SECURITY_FIRST_INTERIOR_POSITION,
                    triangle,
                )
            ),
            (3,),
        )
        self.assertGreater(
            campaign.CLINIC_SECURITY_REVEAL_POSITION[1],
            campaign.CLINIC_SECURITY_DOOR_PLANE_Z,
        )
        self.assertLess(
            campaign.CLINIC_SECURITY_FIRST_INTERIOR_POSITION[1],
            campaign.CLINIC_SECURITY_DOOR_PLANE_Z,
        )
        self.assertEqual(set(triangles[34]) & set(triangles[3]), {
            (23, 0, 234),
            (0, 0, 243),
        })

        source_assets = campaign._load_clinic_security_overworld_assets(DONOR_DISC)
        actors = _indexed_entries(item.components[base.mass_driver.ACTOR_INDEX])
        sprites = _indexed_entries(item.components[base.mass_driver.SPRITE_INDEX])
        self.assertEqual(len(actors), 4)
        self.assertEqual(len(sprites), 4)
        for bank, (source_actor, source_sprite) in source_assets.items():
            with self.subTest(exact_security_bank=bank):
                self.assertEqual(actors[bank], source_actor)
                self.assertEqual(sprites[bank], source_sprite)
        self.assertEqual(
            struct.unpack_from(
                "<4H", item.header, campaign.CLINIC_SECURITY_CUBE_TARGET_BANK * 8
            ),
            campaign.CLINIC_SECURITY_CUBE_MAPPING,
        )
        self.assertEqual(
            struct.unpack_from(
                "<4H", item.header, campaign.CLINIC_SECURITY_GUARD_TARGET_BANK * 8
            ),
            campaign.CLINIC_SECURITY_GUARD_MAPPING,
        )

        actor_records = _actor_records(item.header)
        expected_record = base.mass_driver._field_actor_record(
            0x01E0,
            campaign.CLINIC_SECURITY_STAGING_POSITION[0],
            campaign.CLINIC_SECURITY_STAGING_POSITION[1],
            0,
        )
        for entity in campaign.CLINIC_SECURITY_ENTITIES:
            with self.subTest(security_entity=entity):
                self.assertEqual(actor_records[entity], expected_record)
                init_pc = editor.get_script_pointer(entity, 0)
                init = campaign._clinic_security_actor_init(
                    entity=entity, routine_pc=init_pc
                )
                self.assertEqual(
                    editor.bytecode[init_pc : init_pc + len(init)], init
                )
                self.assertIn(
                    b"\xFE\x17" + bytes((entity, 0xFF))
                    + base.mass_driver._wait(4),
                    init,
                )
                entry_pc = editor.get_script_pointer(
                    entity, campaign.CLINIC_SECURITY_ENTRY_SCRIPT
                )
                entry = campaign._clinic_security_actor_entrance_body(entity=entity)
                self.assertEqual(
                    editor.bytecode[entry_pc : entry_pc + len(entry)], entry
                )
                self.assertIn(bytes.fromhex("20 01 80"), entry)
                delay = campaign.CLINIC_SECURITY_ENTRY_DELAYS[entity]
                delay_body = (
                    b"" if delay == 0 else base.mass_driver._wait(delay)
                )
                hidden_snap = (
                    b"\x19"
                    + campaign._s16(campaign.CLINIC_SECURITY_REVEAL_POSITION[0])
                    + campaign._s16(campaign.CLINIC_SECURITY_REVEAL_POSITION[1])
                    + b"\xC0\x1A\x00"
                )
                show = b"\x24" + bytes((entity,))
                crossing_walk = campaign._actor_waypoint_body(
                    campaign.CLINIC_SECURITY_ROUTES[entity][1:3],
                    final_direction=0,
                    max_steps=campaign.CLINIC_SECURITY_WAYPOINT_MAX_STEPS,
                )
                formation_walk = campaign._actor_waypoint_body(
                    campaign.CLINIC_SECURITY_ROUTES[entity][3:],
                    final_direction=4,
                    max_steps=campaign.CLINIC_SECURITY_WAYPOINT_MAX_STEPS,
                )
                face_fei = (
                    b"\xFE\x17"
                    + bytes((entity, 0xFF))
                    + base.mass_driver._wait(4)
                )
                done = campaign._set_bit(
                    campaign.CLINIC_SECURITY_DONE_VARIABLE,
                    campaign.CLINIC_SECURITY_ENTITIES.index(entity),
                )
                self.assertEqual(
                    entry,
                    delay_body
                    + hidden_snap
                    + bytes.fromhex("20 01 80")
                    + campaign.CLINIC_DOORWAY_WALKMESH_OVERRIDE_SET
                    + show
                    + crossing_walk
                    + campaign.CLINIC_DOORWAY_WALKMESH_OVERRIDE_CLEAR
                    + formation_walk
                    + face_fei
                    + done
                    + b"\x00",
                )
                self.assertNotIn(
                    b"\x4B"
                    + campaign._s16(campaign.CLINIC_SECURITY_REVEAL_POSITION[0])
                    + campaign._s16(campaign.CLINIC_SECURITY_REVEAL_POSITION[1]),
                    entry,
                )
                self.assertNotIn(
                    base._immediate(campaign.INTAKE_DOCTOR_WAYPOINT_MAX_STEPS),
                    crossing_walk + formation_walk,
                )
                self.assertEqual(
                    entry.count(campaign.CLINIC_DOORWAY_WALKMESH_OVERRIDE_SET),
                    1,
                )
                self.assertEqual(
                    entry.count(campaign.CLINIC_DOORWAY_WALKMESH_OVERRIDE_CLEAR),
                    1,
                )
                self.assertLess(
                    entry.index(hidden_snap),
                    entry.index(campaign.CLINIC_DOORWAY_WALKMESH_OVERRIDE_SET),
                )
                self.assertLess(
                    entry.index(campaign.CLINIC_DOORWAY_WALKMESH_OVERRIDE_SET),
                    entry.index(show),
                )
                self.assertLess(entry.index(show), entry.index(crossing_walk))
                self.assertLess(
                    entry.index(crossing_walk),
                    entry.index(campaign.CLINIC_DOORWAY_WALKMESH_OVERRIDE_CLEAR),
                )
                self.assertLess(
                    entry.index(campaign.CLINIC_DOORWAY_WALKMESH_OVERRIDE_CLEAR),
                    entry.index(formation_walk),
                )
                self.assertLess(entry.index(formation_walk), entry.index(face_fei))
                self.assertLess(entry.index(face_fei), entry.index(done))
                hide_pc = editor.get_script_pointer(
                    entity, campaign.CLINIC_SECURITY_HIDE_SCRIPT
                )
                self.assertEqual(
                    editor.bytecode[hide_pc : hide_pc + 2],
                    campaign._clinic_security_actor_hide_body(),
                )

        update_pc = editor.get_script_pointer(campaign.CLINIC_DOCTOR_ENTITY, 1)
        update = campaign._clinic_doctor_update(
            briefing_dialogue_id=campaign.CLINIC_BRIEFING_DIALOGUE_ID,
            security_arrival_dialogue_id=campaign.CLINIC_SECURITY_ARRIVAL_DIALOGUE_ID,
            keycard_dialogue_id=campaign.CLINIC_SECURITY_KEYCARD_DIALOGUE_ID,
            escape_dialogue_id=campaign.CLINIC_DOCTOR_ESCAPE_DIALOGUE_ID,
            routine_pc=update_pc,
        )
        entering = campaign._appointment_stage_body(
            campaign.APPOINTMENT_STAGE_SECURITY_ENTERING
        )
        battle_pending = campaign._appointment_stage_body(
            campaign.APPOINTMENT_STAGE_BATTLE_PENDING
        )
        open_call = bytes(
            (
                0x09,
                campaign.CLINIC_EXIT_HELPER_ENTITY,
                0xC0 | campaign.CLINIC_EXIT_HELPER_OPEN_SCRIPT,
            )
        )
        close_call = bytes(
            (
                0x09,
                campaign.CLINIC_EXIT_HELPER_ENTITY,
                0xC0 | campaign.CLINIC_EXIT_HELPER_CLOSE_SCRIPT,
            )
        )
        entering_at = update.index(entering)
        open_at = update.index(open_call, entering_at + len(entering))
        entry_calls = tuple(
            update.index(
                b"\x07"
                + bytes(
                    (
                        entity,
                        0x20 | campaign.CLINIC_SECURITY_ENTRY_SCRIPT,
                    )
                ),
                open_at + len(open_call),
            )
            for entity in campaign.CLINIC_SECURITY_ENTITIES
        )
        close_at = update.index(close_call, max(entry_calls) + 3)
        battle_pending_at = update.index(
            battle_pending, close_at + len(close_call)
        )
        arrival_at = update.index(
            campaign._actor_dialogue(campaign.CLINIC_SECURITY_ARRIVAL_DIALOGUE_ID),
            battle_pending_at + len(battle_pending),
        )
        battle_at = update.index(
            base.mass_driver._fixed_battle(campaign.CLINIC_SECURITY_CONFIGURATION),
            arrival_at,
        )
        self.assertLess(entering_at, open_at)
        self.assertTrue(all(open_at < call_at < close_at for call_at in entry_calls))
        self.assertLess(close_at, battle_pending_at)
        self.assertLess(battle_pending_at, arrival_at)
        self.assertLess(arrival_at, battle_at)

        sync_at = update.index(b"\xFE\x7F", battle_at)
        victory = campaign._appointment_stage_body(
            campaign.APPOINTMENT_STAGE_FLEE_PENDING
        )
        self.assertEqual(update[sync_at + 2 : sync_at + 2 + len(victory)], victory)
        keycard_at = update.index(
            campaign._set_bit(
                campaign.SECURITY_KEYCARD_OPERAND,
                campaign.SECURITY_KEYCARD_BIT_INDEX,
            ),
            sync_at + 2 + len(victory),
        )
        for entity in campaign.CLINIC_SECURITY_ENTITIES:
            hide_call = b"\x07" + bytes(
                (entity, 0x20 | campaign.CLINIC_SECURITY_HIDE_SCRIPT)
            )
            hide_at = update.index(hide_call, sync_at + 2 + len(victory))
            self.assertLess(hide_at, keycard_at)

        alias = campaign.APPOINTMENT_ALIAS_CODES[0]
        music_at = update.index(base.mass_driver._play_music(0x14), arrival_at)
        for resumable_stage in (
            campaign.APPOINTMENT_STAGE_SECURITY_PENDING,
            campaign.APPOINTMENT_STAGE_SECURITY_ENTERING,
            campaign.APPOINTMENT_STAGE_BATTLE_PENDING,
        ):
            with self.subTest(resumable_stage=resumable_stage):
                resumed = _run_appointment_vm(
                    editor.bytecode,
                    start_pc=update_pc,
                    stop_pcs=(update_pc + music_at,),
                    variables={
                        campaign.STATE_OPERAND: (
                            campaign.CHECKIN_BIT_MASK
                            | campaign.APPOINTMENT_PHASE_OFFICE_ACTIVE
                        ),
                        campaign.APPOINTMENT_OPERAND: alias | resumable_stage,
                    },
                )
                self.assertEqual(resumed["reason"], "target")
                self.assertEqual(
                    resumed["dialogue_ids"],
                    (campaign.CLINIC_SECURITY_ARRIVAL_DIALOGUE_ID,),
                )
                self.assertEqual(
                    resumed["variables"][campaign.APPOINTMENT_OPERAND],
                    alias | campaign.APPOINTMENT_STAGE_BATTLE_PENDING,
                )

    def test_clinic_exit_denies_departure_until_escape_stage_five(self) -> None:
        item = self.donor_by_scene[550]
        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
        seal_entity = campaign.CLINIC_EXIT_SEAL_ENTITY
        native_action = campaign._clinic_native_field_change_action(
            destination_field=campaign.CLINIC_RETURN_FIELD,
            destination_parameter=campaign.CLINIC_RETURN_PARAMETER,
            seal_entity=seal_entity,
        )
        already_open_action = campaign._clinic_post_escape_field_change_action(
            seal_entity=seal_entity
        )
        self.assertEqual(editor.bytecode.count(native_action), 1)
        self.assertEqual(editor.bytecode.count(already_open_action), 1)
        native_pc = editor.bytecode.index(native_action)
        already_open_pc = editor.bytecode.index(already_open_action)
        gate_pc = editor.get_script_pointer(campaign.CLINIC_EXIT_ENTITY, 2)
        gate = campaign._clinic_exit_gate_action(
            native_action_pc=native_pc,
            already_open_action_pc=already_open_pc,
            insistence_dialogue_id=campaign.CLINIC_EXIT_INSISTENCE_DIALOGUE_ID,
            escape_in_progress_dialogue_id=(
                campaign.CLINIC_ESCAPE_IN_PROGRESS_DIALOGUE_ID
            ),
            routine_pc=gate_pc,
        )
        self.assertEqual(editor.bytecode[gate_pc : gate_pc + len(gate)], gate)
        clinic_scratch_word = struct.pack(
            "<H", campaign.CLINIC_EXIT_SCRATCH_VARIABLE
        )
        appointment_scratch_word = struct.pack(
            "<H", campaign.APPOINTMENT_SCRATCH_VARIABLE
        )
        self.assertEqual(gate.count(clinic_scratch_word), 13)
        self.assertNotIn(appointment_scratch_word, gate)

        # Field scripts receive only eight opcodes per scheduler slice.  V211's
        # gate yielded after its phase snapshot, then lower-ID doctor e16 reused
        # 07C6 for stage 2 before e17 resumed.  The resumed gate consequently
        # mistook OFFICE_ACTIVE for an invalid phase and ran the native exit.
        # Reproduce that exact interleave: the dedicated 07D0 snapshot survives
        # the doctor's 07C6 write and still reaches the locked-door dialogue.
        scheduler_yield_pc = gate_pc + 0x38
        captured_state = {
            campaign.STATE_OPERAND: 0x00E0,
            campaign.APPOINTMENT_OPERAND: 0x4002,
        }
        first_slice = _run_appointment_vm(
            editor.bytecode,
            start_pc=gate_pc,
            stop_pcs=(scheduler_yield_pc,),
            variables=captured_state,
        )
        self.assertEqual(first_slice["reason"], "target")
        self.assertEqual(first_slice["pc"], scheduler_yield_pc)
        self.assertEqual(
            first_slice["variables"][campaign.CLINIC_EXIT_SCRATCH_VARIABLE],
            campaign.APPOINTMENT_PHASE_OFFICE_ACTIVE,
        )
        raced_variables = dict(first_slice["variables"])
        raced_variables[campaign.APPOINTMENT_SCRATCH_VARIABLE] = (
            campaign.APPOINTMENT_STAGE_FINAL_WARNING
        )
        resumed_after_doctor = _run_appointment_vm(
            editor.bytecode,
            start_pc=scheduler_yield_pc,
            stop_pcs=(native_pc, already_open_pc),
            variables=raced_variables,
        )
        self.assertEqual(resumed_after_doctor["reason"], "stop")
        self.assertEqual(
            resumed_after_doctor["dialogue_ids"],
            (campaign.CLINIC_EXIT_INSISTENCE_DIALOGUE_ID,),
        )
        self.assertIsNone(resumed_after_doctor["field_change"])

        # The same interleave must not prevent the intentional post-victory
        # path.  RESOLVED/COMPLETE still reaches the native opening action,
        # which releases e19 only after the real clearance has been earned.
        complete_first_slice = _run_appointment_vm(
            editor.bytecode,
            start_pc=gate_pc,
            stop_pcs=(scheduler_yield_pc,),
            variables={
                campaign.STATE_OPERAND: (
                    campaign.CHECKIN_BIT_MASK
                    | campaign.APPOINTMENT_PHASE_RESOLVED
                ),
                campaign.APPOINTMENT_OPERAND: (
                    campaign.APPOINTMENT_ALIAS_CODES[0]
                    | campaign.APPOINTMENT_STAGE_COMPLETE
                ),
            },
        )
        complete_raced_variables = dict(complete_first_slice["variables"])
        complete_raced_variables[campaign.APPOINTMENT_SCRATCH_VARIABLE] = (
            campaign.APPOINTMENT_STAGE_FINAL_WARNING
        )
        complete_after_doctor = _run_appointment_vm(
            editor.bytecode,
            start_pc=scheduler_yield_pc,
            stop_pcs=(native_pc, already_open_pc),
            variables=complete_raced_variables,
        )
        self.assertEqual(complete_after_doctor["reason"], "target")
        self.assertEqual(complete_after_doctor["pc"], native_pc)

        alias = campaign.APPOINTMENT_ALIAS_CODES[0]
        locked_states = (
            (campaign.APPOINTMENT_PHASE_ENTERED, campaign.APPOINTMENT_STAGE_NONE),
            (
                campaign.APPOINTMENT_PHASE_LEGACY_BRIEFED,
                campaign.APPOINTMENT_STAGE_NONE,
            ),
            (
                campaign.APPOINTMENT_PHASE_OFFICE_ACTIVE,
                campaign.APPOINTMENT_STAGE_AWAIT_REFUSAL,
            ),
            (
                campaign.APPOINTMENT_PHASE_OFFICE_ACTIVE,
                campaign.APPOINTMENT_STAGE_FINAL_WARNING,
            ),
            (
                campaign.APPOINTMENT_PHASE_OFFICE_ACTIVE,
                campaign.APPOINTMENT_STAGE_SECURITY_PENDING,
            ),
            (
                campaign.APPOINTMENT_PHASE_OFFICE_ACTIVE,
                campaign.APPOINTMENT_STAGE_SECURITY_ENTERING,
            ),
            (
                campaign.APPOINTMENT_PHASE_OFFICE_ACTIVE,
                campaign.APPOINTMENT_STAGE_BATTLE_PENDING,
            ),
        )
        for phase, stage in locked_states:
            with self.subTest(denied_phase=phase, denied_stage=stage):
                denied = _run_appointment_vm(
                    editor.bytecode,
                    start_pc=gate_pc,
                    stop_pcs=(native_pc, already_open_pc),
                    variables={
                        campaign.STATE_OPERAND: (
                            campaign.CHECKIN_BIT_MASK | phase
                        ),
                        campaign.APPOINTMENT_OPERAND: alias | stage,
                    },
                )
                self.assertEqual(denied["reason"], "stop")
                self.assertEqual(
                    denied["dialogue_ids"],
                    (campaign.CLINIC_EXIT_INSISTENCE_DIALOGUE_ID,),
                )

        escaping = _run_appointment_vm(
            editor.bytecode,
            start_pc=gate_pc,
            stop_pcs=(native_pc, already_open_pc),
            variables={
                campaign.STATE_OPERAND: (
                    campaign.CHECKIN_BIT_MASK
                    | campaign.APPOINTMENT_PHASE_RESOLVED
                ),
                campaign.APPOINTMENT_OPERAND: (
                    alias | campaign.APPOINTMENT_STAGE_FLEE_PENDING
                ),
            },
        )
        self.assertEqual(escaping["reason"], "stop")
        self.assertEqual(
            escaping["dialogue_ids"],
            (campaign.CLINIC_ESCAPE_IN_PROGRESS_DIALOGUE_ID,),
        )

        for door_open, expected_pc in ((0, native_pc), (1, already_open_pc)):
            with self.subTest(complete_door_open=door_open):
                complete = _run_appointment_vm(
                    editor.bytecode,
                    start_pc=gate_pc,
                    stop_pcs=(native_pc, already_open_pc),
                    variables={
                        campaign.STATE_OPERAND: (
                            campaign.CHECKIN_BIT_MASK
                            | campaign.APPOINTMENT_PHASE_RESOLVED
                        ),
                        campaign.APPOINTMENT_OPERAND: (
                            alias | campaign.APPOINTMENT_STAGE_COMPLETE
                        ),
                        campaign.CLINIC_DOOR_OPEN_VARIABLE: door_open,
                    },
                )
                self.assertEqual(complete["reason"], "target")
                self.assertEqual(complete["pc"], expected_pc)
                self.assertEqual(complete["dialogue_ids"], ())

        helper_call = bytes((0x09, campaign.CLINIC_EXIT_HELPER_ENTITY, 0xC4))
        seal_call = bytes((0x09, seal_entity, 0x24))
        change = base._change_field(
            campaign.CLINIC_RETURN_FIELD, campaign.CLINIC_RETURN_PARAMETER
        )
        self.assertLess(native_action.index(bytes.fromhex("74 77 80")), native_action.index(helper_call))
        self.assertLess(native_action.index(helper_call), native_action.index(seal_call))
        self.assertLess(native_action.index(seal_call), native_action.index(change))
        self.assertNotIn(bytes.fromhex("74 77 80"), already_open_action)
        self.assertNotIn(helper_call, already_open_action)
        self.assertLess(already_open_action.index(seal_call), already_open_action.index(change))

    def test_clinic_doctor_escape_route_keeps_player_control(self) -> None:
        item = self.donor_by_scene[550]
        campaign._validate_clinic_doctor_escape_route(item.components[1])
        triangles = base._walkmesh_layer(item.components[1], 0)
        endpoint = campaign.CLINIC_DOCTOR_ESCAPE_WAYPOINTS[-1]
        endpoint_hits = tuple(
            index
            for index, triangle in enumerate(triangles)
            if base._point_inside_triangle(endpoint, triangle)
        )
        self.assertEqual(endpoint_hits, campaign.CLINIC_DOCTOR_ESCAPE_TRIANGLES)

        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
        update_pc = editor.get_script_pointer(campaign.CLINIC_DOCTOR_ENTITY, 1)
        action_pc = editor.get_script_pointer(campaign.CLINIC_DOCTOR_ENTITY, 2)
        update = campaign._clinic_doctor_update(
            briefing_dialogue_id=campaign.CLINIC_BRIEFING_DIALOGUE_ID,
            security_arrival_dialogue_id=(
                campaign.CLINIC_SECURITY_ARRIVAL_DIALOGUE_ID
            ),
            keycard_dialogue_id=campaign.CLINIC_SECURITY_KEYCARD_DIALOGUE_ID,
            escape_dialogue_id=campaign.CLINIC_DOCTOR_ESCAPE_DIALOGUE_ID,
            routine_pc=update_pc,
        )
        escape = campaign._clinic_doctor_escape_body()
        escape_at = update.index(escape)
        self.assertTrue(escape.startswith(campaign.DOCTOR_TRANSIT_COLLISION_FLAGS))
        self.assertEqual(update[escape_at - 2 : escape_at], b"\xFE\x53")
        self.assertNotIn(b"\xFE\x54", escape)
        for player_script in range(32):
            self.assertNotIn(
                bytes((0x07, 0x01, 0x20 | player_script)), escape
            )

        open_call = bytes(
            (
                0x09,
                campaign.CLINIC_EXIT_HELPER_ENTITY,
                0xC0 | campaign.CLINIC_EXIT_HELPER_OPEN_SCRIPT,
            )
        )
        close_call = bytes(
            (
                0x09,
                campaign.CLINIC_EXIT_HELPER_ENTITY,
                0xC0 | campaign.CLINIC_EXIT_HELPER_CLOSE_SCRIPT,
            )
        )
        door_open = base.mass_driver._set_variable_s16(
            campaign.CLINIC_DOOR_OPEN_VARIABLE, 1
        )
        door_closed = base.mass_driver._set_variable_s16(
            campaign.CLINIC_DOOR_OPEN_VARIABLE, 0
        )
        approach = campaign._actor_waypoint_body(
            campaign.CLINIC_DOCTOR_ESCAPE_APPROACH_WAYPOINTS,
            final_direction=0,
        )
        threshold = campaign._actor_waypoint_body(
            campaign.CLINIC_DOCTOR_ESCAPE_THRESHOLD_WAYPOINTS,
            final_direction=0,
            max_steps=campaign.CLINIC_DOCTOR_THRESHOLD_WAYPOINT_MAX_STEPS,
        )
        complete = campaign._appointment_stage_body(
            campaign.APPOINTMENT_STAGE_COMPLETE
        )
        self.assertEqual(
            escape,
            b"\x20\x01\x80"
            + approach
            + bytes.fromhex("74 77 80")
            + open_call
            + door_open
            + campaign.CLINIC_DOORWAY_WALKMESH_OVERRIDE_SET
            + threshold
            + close_call
            + door_closed
            + b"\x23"
            + campaign.CLINIC_DOORWAY_WALKMESH_OVERRIDE_CLEAR
            + complete,
        )
        self.assertEqual(campaign.CLINIC_DOCTOR_THRESHOLD_WAYPOINT_MAX_STEPS, 16)
        doctor_threshold_route = (
            campaign.CLINIC_DOCTOR_ESCAPE_APPROACH_WAYPOINTS[-1],
            *campaign.CLINIC_DOCTOR_ESCAPE_THRESHOLD_WAYPOINTS,
        )
        doctor_required_steps = tuple(
            campaign._required_clinic_waypoint_steps(start, finish)
            for start, finish in zip(
                doctor_threshold_route,
                doctor_threshold_route[1:],
                strict=False,
            )
        )
        self.assertEqual(doctor_required_steps, (13, 12, 13))
        self.assertTrue(
            all(
                steps <= campaign.CLINIC_DOCTOR_THRESHOLD_WAYPOINT_MAX_STEPS
                for steps in doctor_required_steps
            )
        )
        self.assertNotIn(
            base._immediate(campaign.INTAKE_DOCTOR_WAYPOINT_MAX_STEPS),
            threshold,
        )
        override_set_at = escape.index(
            campaign.CLINIC_DOORWAY_WALKMESH_OVERRIDE_SET
        )
        threshold_at = escape.index(threshold, override_set_at)
        close_at = escape.index(close_call, threshold_at)
        hide_at = escape.index(b"\x23", close_at)
        override_clear_at = escape.index(
            campaign.CLINIC_DOORWAY_WALKMESH_OVERRIDE_CLEAR, hide_at
        )
        self.assertLess(escape.index(open_call), override_set_at)
        self.assertLess(override_set_at, threshold_at)
        self.assertLess(threshold_at, close_at)
        self.assertLess(close_at, hide_at)
        self.assertLess(hide_at, override_clear_at)

        close_pc = editor.get_script_pointer(
            campaign.CLINIC_EXIT_HELPER_ENTITY,
            campaign.CLINIC_EXIT_HELPER_CLOSE_SCRIPT,
        )
        close = campaign._clinic_exit_close_helper(routine_pc=close_pc)
        self.assertEqual(editor.bytecode[close_pc : close_pc + len(close)], close)
        self.assertEqual(close.count(bytes.fromhex("FE 1B 01 00 00 00")), 1)

        ignored_during_escape = _run_appointment_vm(
            editor.bytecode,
            start_pc=action_pc,
            variables={
                campaign.STATE_OPERAND: (
                    campaign.CHECKIN_BIT_MASK
                    | campaign.APPOINTMENT_PHASE_RESOLVED
                ),
                campaign.APPOINTMENT_OPERAND: (
                    campaign.APPOINTMENT_ALIAS_CODES[0]
                    | campaign.APPOINTMENT_STAGE_FLEE_PENDING
                ),
            },
        )
        self.assertEqual(ignored_during_escape["reason"], "stop")
        self.assertEqual(ignored_during_escape["control_suspends"], 0)
        self.assertEqual(ignored_during_escape["control_restores"], 0)

    def test_archive_checkin_dialogue_alias_weight_and_layout_contract(self) -> None:
        before_blocks = parse_dialogue(
            self.base_donor_by_scene[549].components[7]
        ).blocks
        final_blocks = parse_dialogue(self.donor_by_scene[549].components[7]).blocks
        self.assertEqual(len(before_blocks), 12)
        self.assertEqual(len(final_blocks), 21)
        for block_id, source in enumerate(before_blocks):
            with self.subTest(retained_dialogue_id=block_id):
                final = final_blocks[block_id]
                self.assertEqual(
                    (final.width, final.height, final.payload),
                    (source.width, source.height, source.payload),
                )

        expected = {
            12: (58, 5, campaign.CHECKIN_ALIAS_MENU_DIALOGUE),
            13: (58, 5, campaign.CHECKIN_ALIAS_RESULT_DIALOGUES[0]),
            14: (58, 5, campaign.CHECKIN_ALIAS_RESULT_DIALOGUES[1]),
            15: (58, 5, campaign.CHECKIN_ALIAS_RESULT_DIALOGUES[2]),
            16: (58, 2, campaign.CHECKIN_CANCELLED_DIALOGUE),
            17: (58, 5, campaign.CHECKIN_REPEAT_MENU_DIALOGUE),
            18: (58, 4, campaign.PATIENT_VITALS_DIALOGUES["Fei"]),
            19: (58, 4, campaign.PATIENT_VITALS_DIALOGUES["Elly"]),
            20: (58, 4, campaign.PATIENT_VITALS_DIALOGUES["Citan"]),
        }
        for block_id, (width, height, text) in expected.items():
            with self.subTest(authored_dialogue_id=block_id):
                block = final_blocks[block_id]
                self.assertEqual((block.width, block.height, block.text), (width, height, text))

                # The normal validator deliberately rejects opaque engine
                # controls.  Substitute a worst-case three-digit live weight
                # and remove only the choice cursor before checking the grid.
                measurable_text = block.text.replace("<Opcode:01:FF>", "")
                measurable_text = measurable_text.replace(
                    "<Opcode:0A:00>", "255"
                ).replace("<Opcode:0A:01>", "9")
                measurable = parse_dialogue(
                    encode_dialogue(
                        (DialogueBlockSpec(0, width, height, measurable_text),)
                    )
                ).blocks[0]
                self.assertEqual(
                    campaign._campaign_dialogue_layout_issues(measurable),
                    (),
                )

        self.assertEqual(
            campaign.CHECKIN_ALIASES,
            ("Aron Voss", "Noel Ardan", "Kiro Dalen"),
        )
        self.assertEqual(len(set(campaign.CHECKIN_ALIASES)), 3)
        self.assertEqual(
            tuple(alias.split()[0] for alias in campaign.CHECKIN_ALIASES),
            ("Aron", "Noel", "Kiro"),
        )
        self.assertTrue(
            all(len(alias.split()) == 2 for alias in campaign.CHECKIN_ALIASES)
        )
        self.assertEqual(
            campaign.APPOINTMENT_ALIAS_CODES,
            (0x4000, 0x8000, 0xC000),
        )
        real_name_parts = {"fei", "fong", "wong", "fei fong wong"}
        for offset, alias in enumerate(campaign.CHECKIN_ALIASES, start=13):
            with self.subTest(alias=alias):
                self.assertNotIn(alias.casefold(), real_name_parts)
                self.assertTrue(real_name_parts.isdisjoint(alias.casefold().split()))
                self.assertIn(f"    {alias}\n", final_blocks[12].text)
                self.assertIn(f"Alias: {alias}\n", final_blocks[offset].text)

        # Height and clinical vitals are biography data.  Weight is not: it
        # must remain an EX69-fed dialogue parameter because food can change it.
        self.assertEqual(
            campaign.PATIENT_RETAIL_INITIAL_WEIGHT_HUNDREDTHS_LB,
            {"Fei": 16_720, "Elly": 9_240, "Citan": 15_840},
        )
        self.assertTrue(
            all(len(profile) == 4 for profile in campaign.PATIENT_PROFILE_MEASUREMENTS.values())
        )
        for patient in ("Fei", "Elly", "Citan"):
            with self.subTest(patient=patient):
                text = campaign.PATIENT_VITALS_DIALOGUES[patient]
                self.assertIn(
                    "Weight <Opcode:0A:00>.<Opcode:0A:01>0 lbs",
                    text,
                )
                self.assertNotRegex(text, r"Weight\s+\d+(?:\.\d+)?\s+lbs")
        checkin_text = "\n".join(final_blocks[index].text for index in range(12, 21))
        self.assertEqual(checkin_text.count(" lbs"), 6)

    def test_archive_terminal_action_bytes_dynamic_reads_and_no_binary_handoff(self) -> None:
        before = ScriptEditor(
            self.base_donor_by_scene[549].components[base.SCRIPT_INDEX]
        )
        final = ScriptEditor(self.donor_by_scene[549].components[base.SCRIPT_INDEX])
        self.assertEqual(
            before.get_script_pointer(campaign.ARCHIVE_TERMINAL_ENTITY, 2),
            campaign.ARCHIVE_TERMINAL_RETAIL_ACTION_PC,
        )
        self.assertEqual(
            final.get_script_pointer(campaign.ARCHIVE_TERMINAL_ENTITY, 2),
            campaign.ARCHIVE_CHECKIN_ACTION_PC,
        )

        expected = campaign._archive_checkin_action(
            alias_menu_dialogue_id=12,
            alias_result_dialogue_ids=(13, 14, 15),
            cancelled_dialogue_id=16,
            repeat_menu_dialogue_id=17,
            patient_dialogue_ids=(18, 19, 20),
            routine_pc=campaign.ARCHIVE_CHECKIN_ACTION_PC,
        )
        self.assertEqual(len(expected), 469)
        self.assertEqual(
            campaign.ARCHIVE_CHECKIN_ACTION_PC + len(expected), 0x0973
        )
        self.assertLessEqual(0x0973, campaign.CAMPAIGN_MUSIC_WRAPPER_PCS[549])
        self.assertEqual(
            final.bytecode_size,
            campaign.CAMPAIGN_MUSIC_WRAPPER_PCS[549] + 7,
        )
        action = final.bytecode[
            campaign.ARCHIVE_CHECKIN_ACTION_PC :
            campaign.ARCHIVE_CHECKIN_ACTION_PC + len(expected)
        ]
        self.assertEqual(action, expected)
        self.assertEqual(
            _sha256(action),
            campaign.ARCHIVE_CHECKIN_ACTION_SHA256,
        )

        native_action = before.bytecode[
            campaign.ARCHIVE_TERMINAL_RETAIL_ACTION_PC :
            campaign.ARCHIVE_TERMINAL_NATIVE_STOP_PC + 1
        ]
        self.assertEqual(
            _sha256(native_action),
            campaign.ARCHIVE_TERMINAL_NATIVE_ACTION_SHA256,
        )
        self.assertEqual(
            before.bytecode[
                campaign.ARCHIVE_TERMINAL_RETAIL_ACTION_PC :
                campaign.ARCHIVE_TERMINAL_NATIVE_MENU_PC
            ],
            campaign.ARCHIVE_TERMINAL_NATIVE_SCREEN_OPEN_BODY,
        )
        self.assertEqual(
            before.bytecode[
                campaign.ARCHIVE_TERMINAL_NATIVE_CLOSE_PC :
                campaign.ARCHIVE_TERMINAL_NATIVE_STOP_PC - 3
            ],
            campaign.ARCHIVE_TERMINAL_NATIVE_SCREEN_CLOSE_LAUNCH_BODY,
        )
        self.assertEqual(
            tuple(
                before.get_script_pointer(
                    entity, campaign.ARCHIVE_TERMINAL_SCREEN_OPEN_SCRIPT
                )
                for entity in campaign.ARCHIVE_TERMINAL_SCREEN_ENTITIES
            ),
            campaign.ARCHIVE_TERMINAL_SCREEN_OPEN_PCS,
        )
        self.assertEqual(
            tuple(
                before.get_script_pointer(
                    entity, campaign.ARCHIVE_TERMINAL_SCREEN_CLOSE_SCRIPT
                )
                for entity in campaign.ARCHIVE_TERMINAL_SCREEN_ENTITIES
            ),
            campaign.ARCHIVE_TERMINAL_SCREEN_CLOSE_PCS,
        )
        self.assertEqual(
            action.count(campaign.ARCHIVE_TERMINAL_NATIVE_SCREEN_OPEN_BODY),
            1,
        )
        self.assertEqual(
            action.count(
                campaign.ARCHIVE_TERMINAL_NATIVE_SCREEN_CLOSE_LAUNCH_BODY
            ),
            1,
        )

        reads = tuple(
            campaign._read_character_weight_lbs(
                campaign.PATIENT_CHARACTER_IDS[patient]
            )
            for patient in ("Fei", "Elly", "Citan")
        )
        open_at = action.index(campaign.ARCHIVE_TERMINAL_NATIVE_SCREEN_OPEN_BODY)
        reads_at = open_at + len(
            campaign.ARCHIVE_TERMINAL_NATIVE_SCREEN_OPEN_BODY
        )
        self.assertEqual(action[reads_at : reads_at + len(reads[0])], reads[0])
        for read in reads:
            self.assertEqual(action.count(read), 1)
        self.assertLess(action.index(reads[0]), action.index(bytes.fromhex("D2 11")))
        self.assertLess(action.index(bytes.fromhex("D2 11")), action.index(reads[1]))
        self.assertLess(action.index(reads[1]), action.index(reads[2]))
        with self.assertRaises(campaign.SurfaceCampaignBuildError):
            campaign._read_character_weight_lbs(3)

        first_use_offset = action.index(bytes.fromhex("D2 0C 00 00"))
        bit_test = campaign._bit_test(
            campaign.STATE_OPERAND,
            campaign.CHECKIN_BIT_MASK,
            campaign.ARCHIVE_CHECKIN_ACTION_PC + first_use_offset,
        )
        set_bit = campaign._set_bit(campaign.STATE_OPERAND, campaign.CHECKIN_BIT_INDEX)
        clear_bit = bytes.fromhex("3B FA 03 07 00 40")
        self.assertEqual(action.count(bit_test), 1)
        self.assertEqual(action.count(set_bit), 3)
        self.assertNotIn(clear_bit, action)
        for alias_index, result_id in enumerate((13, 14, 15)):
            with self.subTest(persisted_alias=campaign.CHECKIN_ALIASES[alias_index]):
                alias_body = campaign._appointment_alias_body(alias_index)
                self.assertEqual(action.count(alias_body), 1)
                self.assertLess(
                    action.index(b"\xD2" + struct.pack("<H", result_id)),
                    action.index(alias_body),
                )
                self.assertLess(action.index(alias_body), action.index(set_bit, action.index(alias_body)))

        self.assertNotIn(
            campaign._jump(campaign.ARCHIVE_TERMINAL_NATIVE_MENU_PC),
            action,
        )
        self.assertNotIn(
            campaign._jump(campaign.ARCHIVE_TERMINAL_RETAIL_ACTION_PC),
            action,
        )
        self.assertNotIn(
            b"\x07"
            + bytes((campaign.ARCHIVE_TERMINAL_ENTITY, 0x22)),
            action,
        )
        self.assertNotIn(
            b"\x09"
            + bytes((campaign.ARCHIVE_TERMINAL_ENTITY, 0x22)),
            action,
        )
        self.assertEqual(
            final.bytecode[0x00D8:0x017A],
            before.bytecode[0x00D8:0x017A],
        )
        self.assertEqual(
            final.bytecode[0x010F:0x0113],
            base.mass_driver._choice_dialog(
                campaign.ARCHIVE_TERMINAL_NATIVE_MENU_DIALOGUE_ID
            ),
        )

    def test_archive_terminal_native_screen_contract_fails_closed(self) -> None:
        prepared = self.base_donor_by_scene[549]
        base_script = prepared.components[base.SCRIPT_INDEX]
        base_editor = ScriptEditor(base_script)

        mutated_scripts: dict[str, bytes] = {}
        for label, pc in (
            ("opening", campaign.ARCHIVE_TERMINAL_RETAIL_ACTION_PC),
            ("menu", campaign.ARCHIVE_TERMINAL_NATIVE_MENU_PC),
            ("closing", campaign.ARCHIVE_TERMINAL_NATIVE_CLOSE_PC),
        ):
            damaged = bytearray(base_script)
            damaged[base_editor.bytecode_offset + pc] ^= 0x01
            mutated_scripts[label] = bytes(damaged)

        pointer_editor = ScriptEditor(base_script)
        pointer_editor.set_script_pointer(
            campaign.ARCHIVE_TERMINAL_SCREEN_ENTITIES[0],
            campaign.ARCHIVE_TERMINAL_SCREEN_OPEN_SCRIPT,
            campaign.ARCHIVE_TERMINAL_SCREEN_OPEN_PCS[0] + 1,
        )
        mutated_scripts["panel pointer"] = pointer_editor.to_bytes()

        for label, script in mutated_scripts.items():
            components = list(prepared.components)
            components[base.SCRIPT_INDEX] = script
            damaged = replace(prepared, components=tuple(components))
            with self.subTest(native_contract=label):
                with self.assertRaisesRegex(
                    campaign.SurfaceCampaignBuildError,
                    "Field 549 retail archive terminal changed",
                ):
                    campaign._prepare_archive_checkin(damaged)

    def test_archive_checkin_all_menu_paths_preserve_state_and_control(self) -> None:
        editor = ScriptEditor(self.donor_by_scene[549].components[base.SCRIPT_INDEX])
        unrelated_state = 0x1000
        checked_state = (
            unrelated_state
            | campaign.CHECKIN_BIT_MASK
            | campaign.APPOINTMENT_PHASE_REGISTERED
        )
        persisted_alias = campaign.APPOINTMENT_ALIAS_CODES[0]
        scenarios = (
            (
                "alias Aron Voss", unrelated_state, 0, {12: 1}, (12, 13),
                checked_state, campaign.APPOINTMENT_ALIAS_CODES[0],
            ),
            (
                "alias Noel Ardan", unrelated_state, 0, {12: 2}, (12, 14),
                checked_state, campaign.APPOINTMENT_ALIAS_CODES[1],
            ),
            (
                "alias Kiro Dalen", unrelated_state, 0, {12: 3}, (12, 15),
                checked_state, campaign.APPOINTMENT_ALIAS_CODES[2],
            ),
            (
                "v183 alias reselection",
                unrelated_state | campaign.CHECKIN_BIT_MASK,
                0,
                {12: 2},
                (12, 14),
                checked_state,
                campaign.APPOINTMENT_ALIAS_CODES[1],
            ),
            (
                "cancel", unrelated_state, 0, {12: 4}, (12, 16),
                unrelated_state, 0,
            ),
            (
                "Fei", checked_state, persisted_alias, {17: 1}, (17, 18),
                checked_state, persisted_alias,
            ),
            (
                "Elly", checked_state, persisted_alias, {17: 2}, (17, 19),
                checked_state, persisted_alias,
            ),
            (
                "Citan", checked_state, persisted_alias, {17: 3}, (17, 20),
                checked_state, persisted_alias,
            ),
            (
                "exit", checked_state, persisted_alias, {17: 4}, (17,),
                checked_state, persisted_alias,
            ),
        )
        live_weights = {0: 83, 1: 47, 2: 75}
        expected_display = {
            "Elly": (103, 4),
            "Citan": (165, 0),
        }
        for (
            label,
            initial_state,
            initial_appointment,
            choices,
            dialogue_ids,
            final_state,
            final_appointment,
        ) in scenarios:
            with self.subTest(path=label):
                result = _simulate_archive_checkin_action(
                    editor,
                    initial_state=initial_state,
                    initial_appointment=initial_appointment,
                    menu_choices=choices,
                    character_weights=live_weights,
                )
                self.assertEqual(result["dialogue_ids"], dialogue_ids)
                self.assertEqual(result["state"], final_state)
                self.assertEqual(result["appointment"], final_appointment)
                self.assertEqual(result["control_suspends"], 1)
                self.assertEqual(result["control_restores"], 1)
                self.assertEqual(
                    result["screen_opens"],
                    campaign.ARCHIVE_TERMINAL_SCREEN_ENTITIES,
                )
                self.assertEqual(
                    result["screen_closes"],
                    campaign.ARCHIVE_TERMINAL_SCREEN_ENTITIES,
                )
                variables = result["variables"]
                self.assertIsInstance(variables, dict)
                whole, fraction = expected_display.get(label, (182, 6))
                self.assertEqual(
                    variables[campaign.PATIENT_WEIGHT_WHOLE_DIALOG_VARIABLE],
                    whole,
                )
                self.assertEqual(
                    variables[campaign.PATIENT_WEIGHT_FRACTION_DIALOG_VARIABLE],
                    fraction,
                )

    def test_archive_exit_arms_one_persistent_alias_timer_once(self) -> None:
        editor = ScriptEditor(self.donor_by_scene[549].components[base.SCRIPT_INDEX])
        action_pc = editor.get_script_pointer(6, 2)
        seal_entity = editor.entity_count - 1
        action = campaign._donor_native_field_change_action(
            helper_entity=7,
            player_script=4,
            destination_field=621,
            destination_parameter=0,
            seal_entity=seal_entity,
            routine_pc=action_pc,
            arm_appointment=True,
        )
        self.assertEqual(editor.bytecode[action_pc : action_pc + len(action)], action)

        open_at = action.index(bytes((0x09, 7, 0x24)))
        release_at = action.index(bytes((0x09, seal_entity, 0x24)))
        player_at = action.index(bytes.fromhex("07 01 24"))
        wait_at = action.index(bytes.fromhex("26 0A 80"))
        arm_at = action.index(campaign._appointment_phase_snapshot_body())
        change_at = action.index(base._change_field(621, 0))
        self.assertLess(open_at, release_at)
        self.assertLess(release_at, player_at)
        self.assertLess(player_at, wait_at)
        self.assertLess(wait_at, arm_at)
        self.assertLess(arm_at, change_at)

        arm_pc = action_pc + arm_at
        change_pc = action_pc + change_at
        arm_body = campaign._appointment_arm_guarded_body(arm_pc)
        self.assertEqual(action[arm_at : arm_at + len(arm_body)], arm_body)

        unrelated = 0x1000
        alias = campaign.APPOINTMENT_ALIAS_CODES[1]
        initial_state = (
            unrelated
            | campaign.CHECKIN_BIT_MASK
            | campaign.APPOINTMENT_PHASE_REGISTERED
        )
        clock = 3_723
        armed = _run_appointment_vm(
            editor.bytecode,
            start_pc=arm_pc,
            stop_pcs=(change_pc,),
            variables={
                campaign.STATE_OPERAND: initial_state,
                campaign.APPOINTMENT_OPERAND: alias,
                **_clock_variables(clock),
            },
        )
        self.assertEqual(armed["reason"], "target")
        armed_values = armed["variables"]
        self.assertEqual(
            armed_values[campaign.APPOINTMENT_OPERAND],
            alias | (clock & campaign.APPOINTMENT_TIME_MASK),
        )
        self.assertEqual(
            armed_values[campaign.STATE_OPERAND],
            unrelated
            | campaign.CHECKIN_BIT_MASK
            | campaign.APPOINTMENT_PHASE_ARMED,
        )

        # Re-entering the wrapper from an already-armed savestate must not
        # reset the minute-long wait to the current clock.
        old_timestamp = alias | 123
        already_armed = _run_appointment_vm(
            editor.bytecode,
            start_pc=arm_pc,
            stop_pcs=(change_pc,),
            variables={
                campaign.STATE_OPERAND: (
                    unrelated
                    | campaign.CHECKIN_BIT_MASK
                    | campaign.APPOINTMENT_PHASE_ARMED
                ),
                campaign.APPOINTMENT_OPERAND: old_timestamp,
                **_clock_variables(9_999),
            },
        )
        self.assertEqual(
            already_armed["variables"][campaign.APPOINTMENT_OPERAND],
            old_timestamp,
        )

    def test_appointment_clock_threshold_and_wrap_math_are_exact(self) -> None:
        current_time = campaign._appointment_current_time_body()
        self.assertEqual(
            current_time,
            bytes.fromhex(
                "35 C4 07 0E 00 00 DE C4 07 10 0E 40 "
                "35 C0 07 0C 00 00 35 C2 07 C0 07 00 "
                "42 C2 07 08 80 3E C0 07 FF 00 40 "
                "DE C2 07 3C 00 40 38 C4 07 C2 07 00 "
                "38 C4 07 C0 07 00 3E C4 07 FF 3F 40"
            ),
        )
        elapsed_body = (
            current_time
            + base.mass_driver._copy_variable(
                campaign.APPOINTMENT_SCRATCH_VARIABLE,
                campaign.APPOINTMENT_OPERAND,
            )
            + base.mass_driver._variable_math(
                0x3E,
                campaign.APPOINTMENT_SCRATCH_VARIABLE,
                campaign.APPOINTMENT_TIME_MASK,
            )
            + base.mass_driver._variable_math(
                0x39,
                campaign.APPOINTMENT_NOW_VARIABLE,
                campaign.APPOINTMENT_SCRATCH_VARIABLE,
                operand_is_variable=True,
            )
            + base.mass_driver._variable_math(
                0x3E,
                campaign.APPOINTMENT_NOW_VARIABLE,
                campaign.APPOINTMENT_TIME_MASK,
            )
        )

        intake = ScriptEditor(self.field_by_scene[621].components[base.SCRIPT_INDEX])
        update_pc = intake.get_script_pointer(campaign.INTAKE_DOCTOR_ENTITY, 1)
        update = campaign._intake_doctor_update(
            legacy_menu_dialogue_id=13,
            call_dialogue_ids=(14, 15, 16),
            routine_pc=update_pc,
        )
        self.assertEqual(update.count(elapsed_body), 1)
        threshold = (
            b"\x02"
            + struct.pack("<HH", campaign.APPOINTMENT_NOW_VARIABLE, 60)
            + b"\x44"
        )
        self.assertEqual(update.count(threshold), 1)
        emerge = (
            base.mass_driver._set_variable_s16(
                campaign.APPOINTMENT_DOCTOR_BUSY_VARIABLE, 1
            )
            + campaign.DOCTOR_TRANSIT_COLLISION_FLAGS
            + bytes(
                (
                    0x09,
                    campaign.INTAKE_DOCTOR_DOOR_HELPER_ENTITY,
                    0x24,
                )
            )
            + base.mass_driver._set_variable_s16(
                campaign.INTAKE_DOCTOR_DOOR_OPEN_VARIABLE, 1
            )
            + bytes((0x24, campaign.INTAKE_DOCTOR_ENTITY))
        )
        emerge_pc = update_pc + update.index(emerge)
        self.assertNotEqual(update[emerge_pc - update_pc :][:2], b"\xFE\x54")

        alias = campaign.APPOINTMENT_ALIAS_CODES[0]
        timer_state = (
            campaign.CHECKIN_BIT_MASK | campaign.APPOINTMENT_PHASE_ARMED
        )
        for start in (100, 0x3FF0):
            for elapsed, expected_reason in ((59, "yield"), (60, "target")):
                now = start + elapsed
                with self.subTest(start=start, elapsed=elapsed):
                    arithmetic = _run_appointment_vm(
                        elapsed_body + b"\x00",
                        start_pc=0,
                        variables={
                            campaign.APPOINTMENT_OPERAND: alias | start,
                            **_clock_variables(now),
                        },
                    )
                    self.assertEqual(
                        arithmetic["variables"][campaign.APPOINTMENT_NOW_VARIABLE],
                        elapsed,
                    )
                    polled = _run_appointment_vm(
                        intake.bytecode,
                        start_pc=update_pc,
                        stop_pcs=(emerge_pc,),
                        stop_on_zero_wait=True,
                        variables={
                            campaign.STATE_OPERAND: timer_state,
                            campaign.APPOINTMENT_OPERAND: alias | start,
                            **_clock_variables(now),
                        },
                    )
                    self.assertEqual(polled["reason"], expected_reason)
                    self.assertEqual(polled["control_suspends"], 0)
                    self.assertEqual(polled["control_restores"], 0)

    def test_quarantine_moves_exactly_eighteen_relay_operands_local(self) -> None:
        expected_pcs = (
            0x0586, 0x05D6, 0x05DE, 0x05F2, 0x0625, 0x0675,
            0x067D, 0x0691, 0x06C4, 0x0714, 0x071C, 0x0730,
            0x0763, 0x07B3, 0x07BB, 0x07CF, 0x082B, 0x08E0,
        )
        self.assertEqual(campaign.QUARANTINE_RELAY_SELECTION_OPERAND_PCS, expected_pcs)
        self.assertEqual(len(set(expected_pcs)), 18)

        retargeted = campaign._retarget_surface_room_actions(
            self.base_field_by_scene[620].components[base.SCRIPT_INDEX],
            620,
        )
        migrated = campaign._isolate_quarantine_relay_selection(retargeted)
        final = ScriptEditor(self.field_by_scene[620].components[base.SCRIPT_INDEX])
        state_word = struct.pack("<H", campaign.STATE_OPERAND)
        local_word = struct.pack("<H", campaign.LOCAL_PUZZLE_OPERAND)
        restored = bytearray(migrated.to_bytes())
        for pc in expected_pcs:
            with self.subTest(pc=f"0x{pc:04X}"):
                self.assertEqual(retargeted.bytecode[pc : pc + 2], state_word)
                self.assertEqual(migrated.bytecode[pc : pc + 2], local_word)
                self.assertEqual(final.bytecode[pc : pc + 2], local_word)
                absolute = migrated.bytecode_offset + pc
                restored[absolute : absolute + 2] = state_word
        self.assertEqual(bytes(restored), retargeted.to_bytes())

        # Persistent relay intro/completion flags deliberately remain in the
        # campaign state word; only the four-bit selection moved local.
        for pc, bit_index in (
            (0x05C7, 9), (0x0666, 9), (0x0705, 9), (0x07A4, 9),
            (0x085D, 8), (0x090D, 8),
        ):
            with self.subTest(retained_state_operand=f"0x{pc:04X}"):
                expected = b"\x3A" + state_word + struct.pack("<H", bit_index) + b"\x40"
                self.assertEqual(retargeted.bytecode[pc : pc + len(expected)], expected)
                self.assertEqual(final.bytecode[pc : pc + len(expected)], expected)

    def test_quarantine_solution_commits_clearance_and_native_continuation(self) -> None:
        item = self.field_by_scene[620]
        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
        action_pc = editor.get_script_pointer(24, 2)
        self.assertEqual(action_pc, campaign.QUARANTINE_CURRENT_END_DOOR_ACTION_PC)
        self.assertEqual(editor.get_script_pointer(23, 2), 0x0A71)
        self.assertEqual(editor.get_script_pointer(24, 0), 0x0C06)
        self.assertEqual(editor.get_script_pointer(28, 0), 0x0C23)
        self.assertEqual(editor.get_script_pointer(26, 4), 0x0A8E)
        self.assertEqual(parse_dialogue(item.components[7]).blocks[24].text,
                         campaign.QUARANTINE_COMPLETION_DIALOGUE)
        # Exhaust every relay configuration. Only three physiological markers
        # with the caste marker excluded may commit and reach the native leaf.
        for selection in range(16):
            with self.subTest(selection=selection):
                initial = {campaign.STATE_OPERAND: 0xA8F5,
                           campaign.LOCAL_PUZZLE_OPERAND: selection << 4}
                result = _run_appointment_vm(editor.bytecode, start_pc=action_pc,
                    variables=initial, stop_pcs=(base.QUARANTINE_EAST_DOOR_SUCCESS_PC,))
                if selection == 7:
                    self.assertEqual(result["reason"], "target")
                    self.assertEqual(result["dialogue_ids"], (24,))
                    self.assertEqual(result["variables"][campaign.STATE_OPERAND], 0xA9F5)
                    self.assertEqual(len(result["bit_writes"]), 1)
                else:
                    self.assertEqual(result["reason"], "stop")
                    self.assertEqual(result["dialogue_ids"], (9,))
                    self.assertEqual(result["variables"], initial)
                    self.assertEqual(result["bit_writes"], ())
        repeat = _run_appointment_vm(editor.bytecode, start_pc=action_pc,
            variables={campaign.STATE_OPERAND: 0x0100, campaign.LOCAL_PUZZLE_OPERAND: 0},
            stop_pcs=(base.QUARANTINE_EAST_DOOR_SUCCESS_PC,))
        self.assertEqual(repeat["reason"], "target")
        self.assertEqual(repeat["dialogue_ids"], ())
        self.assertEqual(repeat["bit_writes"], ())
        # Trace the already-tested native animation too: the active success
        # body retains a real field565/p6 destination, not only a metadata edge.
        native = editor.bytecode[base.QUARANTINE_EAST_DOOR_SUCCESS_PC:0x0C06]
        self.assertIn(base._change_field(565, 6), native)


    def test_checkin_bit_is_a_persistent_cross_room_campaign_flag(self) -> None:
        flag = blueprint.FLAG_BY_KEY["intake_checkin_complete"]
        self.assertEqual(
            (
                flag.operand,
                flag.mask,
                flag.bit_index,
                flag.awarded_in_field,
                flag.reset_on_surface_start,
                flag.active,
            ),
            (
                campaign.STATE_OPERAND,
                campaign.CHECKIN_BIT_MASK,
                campaign.CHECKIN_BIT_INDEX,
                549,
                True,
                True,
            ),
        )
        self.assertEqual(campaign.CHECKIN_BIT_MASK, 1 << campaign.CHECKIN_BIT_INDEX)
        self.assertEqual(campaign_title.CAMPAIGN_STATE_BIT_INDICES.count(7), 1)
        reset_clear = bytes.fromhex("3B FA 03 07 00 40")
        self.assertEqual(campaign_title.CAMPAIGN_RESET_ROUTINE.count(reset_clear), 1)

        receptionist = campaign._intake_receptionist_action(
            precheck_dialogue_id=11,
            postcheck_dialogue_id=12,
            routine_pc=campaign.INTAKE_RECEPTIONIST_ACTION_PC,
        )
        terminal = campaign._archive_checkin_action(
            alias_menu_dialogue_id=12,
            alias_result_dialogue_ids=(13, 14, 15),
            cancelled_dialogue_id=16,
            repeat_menu_dialogue_id=17,
            patient_dialogue_ids=(18, 19, 20),
            routine_pc=campaign.ARCHIVE_CHECKIN_ACTION_PC,
        )
        self.assertNotIn(reset_clear, receptionist)
        self.assertNotIn(reset_clear, terminal)
        self.assertEqual(
            receptionist.count(bytes.fromhex("02 FA 03 80 00 46")),
            1,
        )
        self.assertEqual(
            terminal.count(bytes.fromhex("02 FA 03 80 00 46")),
            1,
        )

    def test_sorter_and_core_receipts_commit_once_before_native_doors(self) -> None:
        from modules.soylent_system.tools.surface_soylent_completion import PUZZLES
        for scene, door_entity, progress_index, progress_mask, success_text in (
            (
                624,
                1,
                campaign.SORTER_BIT_INDEX,
                campaign.SORTER_BIT_MASK,
                campaign.SORTER_SUCCESS_DIALOGUE,
            ),
            (
                626,
                1,
                campaign.CORE_BIT_INDEX,
                campaign.CORE_BIT_MASK,
                campaign.CORE_SUCCESS_DIALOGUE,
            ),
        ):
            item = self.field_by_scene[scene]
            editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
            gate_pc = editor.get_script_pointer(door_entity, 2)
            gate = editor.bytecode[gate_pc:]
            with self.subTest(scene=scene):
                self.assertTrue(
                    gate.startswith(
                        campaign._bit_test(campaign.STATE_OPERAND, progress_mask, gate_pc + 11)
                    )
                )
                self.assertIn(
                    b"\x02\xD0\x07" + struct.pack("<H", PUZZLES[scene].solution) + b"\x40",
                    gate[:64],
                )
                self.assertIn(
                    campaign._set_bit(campaign.STATE_OPERAND, progress_index),
                    gate[:80],
                )
                native_action_pc = struct.unpack_from("<H", gate, 9)[0]
                receipt = (
                    b"\xF5" + struct.pack("<H", 5) + b"\x01\x9C"
                )
                sound_at = gate.index(campaign.PROGRESSION_CONFIRM_SOUND)
                receipt_at = gate.index(receipt)
                commit_at = gate.index(
                    campaign._set_bit(campaign.STATE_OPERAND, progress_index)
                )
                native_at = gate.index(campaign._jump(native_action_pc), 11)
                self.assertLess(sound_at, receipt_at)
                self.assertLess(receipt_at, commit_at)
                self.assertLess(commit_at, native_at)

                denied = _run_appointment_vm(
                    editor.bytecode,
                    start_pc=gate_pc,
                    variables={
                        campaign.STATE_OPERAND: 0,
                        campaign.LOCAL_PUZZLE_OPERAND: 0,
                    },
                    stop_pcs=(native_action_pc,),
                )
                self.assertEqual(denied["reason"], "stop")
                self.assertEqual(denied["dialogue_ids"], (7,))
                self.assertEqual(denied["sound_ids"], ())
                self.assertEqual(denied["bit_writes"], ())

                solved = _run_appointment_vm(
                    editor.bytecode,
                    start_pc=gate_pc,
                    variables={
                        campaign.STATE_OPERAND: 0,
                        campaign.LOCAL_PUZZLE_OPERAND: PUZZLES[scene].solution,
                    },
                    stop_pcs=(native_action_pc,),
                )
                self.assertEqual(solved["reason"], "target")
                self.assertEqual(solved["dialogue_ids"], (5,))
                self.assertEqual(
                    solved["sound_ids"],
                    (campaign.PROGRESSION_CONFIRM_SOUND_ID,),
                )
                self.assertEqual(
                    solved["variables"][campaign.STATE_OPERAND] & progress_mask,
                    progress_mask,
                )

                revisited = _run_appointment_vm(
                    editor.bytecode,
                    start_pc=gate_pc,
                    variables={
                        campaign.STATE_OPERAND: progress_mask,
                        campaign.LOCAL_PUZZLE_OPERAND: 0,
                    },
                    stop_pcs=(native_action_pc,),
                )
                self.assertEqual(revisited["reason"], "target")
                self.assertEqual(revisited["dialogue_ids"], ())
                self.assertEqual(revisited["sound_ids"], ())
                self.assertEqual(revisited["bit_writes"], ())

                success_block = parse_dialogue(item.components[7]).blocks[5]
                self.assertEqual(
                    success_block.text,
                    campaign.CAMPAIGN_DIALOGUE_LAYOUT_REPLACEMENTS[scene][5],
                )
                self.assertEqual(
                    campaign._normalized_authored_dialogue_words(
                        success_block.text
                    ),
                    campaign._normalized_authored_dialogue_words(success_text),
                )
                for console in (
                    campaign.SORTER_CONSOLES if scene == 624 else campaign.CORE_CONSOLES
                ):
                    self.assertIn(
                        campaign._set_bit(campaign.LOCAL_PUZZLE_OPERAND, console.bit_index),
                        editor.bytecode,
                    )

    def test_expanded_meld_and_phased_sufal_finale_are_ordered(self) -> None:
        meld = self.field_by_scene[625]
        meld_editor = ScriptEditor(meld.components[base.SCRIPT_INDEX])
        meld_block = parse_dialogue(meld.components[7]).blocks[3]
        self.assertEqual(
            meld_block.text,
            campaign.CAMPAIGN_DIALOGUE_LAYOUT_REPLACEMENTS[625][3],
        )
        meld_words = campaign._normalized_authored_dialogue_words(meld_block.text)
        for required_text in (
            "people forced together",
            "Their eyes ask for the pain",
        ):
            self.assertIn(required_text, meld_words)
        for speaker in ("Elly\n", "Fei\n", "Citan\n"):
            self.assertIn(speaker, meld_block.text)
        reveal_pc = meld_editor.get_script_pointer(33, 2)
        self.assertIn(
            campaign._set_bit(campaign.STATE_OPERAND, campaign.MELD_BIT_INDEX),
            meld_editor.bytecode[reveal_pc : campaign.CAMPAIGN_MUSIC_WRAPPER_PCS[625]],
        )
        gate_pc = meld_editor.get_script_pointer(6, 2)
        self.assertIn(
            campaign._bit_test(campaign.STATE_OPERAND, campaign.MELD_BIT_MASK, gate_pc + 11),
            meld_editor.bytecode[gate_pc : gate_pc + 32],
        )

        generation = self.field_by_scene[622]
        editor = ScriptEditor(generation.components[base.SCRIPT_INDEX])
        boss_pc = editor.get_script_pointer(29, 2)
        native_boss_pc = struct.unpack_from("<H", editor.bytecode, boss_pc + 9)[0]
        boss = editor.bytecode[native_boss_pc : editor.get_script_pointer(26, 2)]
        battle_at = boss.index(bytes.fromhex("71 09 80 FE 7F"))
        pending_at = boss.index(
            campaign._set_bit(
                campaign.STATE_OPERAND,
                campaign.FINALE_EPILOGUE_PENDING_BIT_INDEX,
            )
        )
        epilogue_sound_at = boss.index(campaign.PROGRESSION_CONFIRM_SOUND)
        secured_at = boss.index(
            campaign._set_bit(campaign.STATE_OPERAND, campaign.SECURED_BIT_INDEX)
        )
        pending_clear = campaign._clear_bit(
            campaign.STATE_OPERAND,
            campaign.FINALE_EPILOGUE_PENDING_BIT_INDEX,
        )
        secured_cleanup_at = boss.index(pending_clear)
        pending_clear_at = boss.index(pending_clear, secured_at)
        already_receipt_at = boss.index(b"\xF5\x29\x00\x01\x9C")
        self.assertLess(secured_cleanup_at, already_receipt_at)
        self.assertLess(battle_at, pending_at)
        self.assertLess(pending_at, epilogue_sound_at)
        self.assertLess(epilogue_sound_at, secured_at)
        self.assertLess(secured_at, pending_clear_at)

        fresh = _run_appointment_vm(
            editor.bytecode,
            start_pc=boss_pc,
            menu_choices={43: 1},
            variables={campaign.STATE_OPERAND: 0},
        )
        self.assertEqual(fresh["dialogue_ids"], (43, 39, 40))
        self.assertEqual(fresh["battle_ids"], (9,))
        self.assertEqual(fresh["battle_syncs"], 1)
        self.assertEqual(
            fresh["sound_ids"],
            (campaign.PROGRESSION_CONFIRM_SOUND_ID,),
        )
        self.assertEqual(
            fresh["variables"][campaign.STATE_OPERAND]
            & (
                campaign.FINALE_EPILOGUE_PENDING_BIT_MASK
                | campaign.SECURED_BIT_MASK
            ),
            campaign.SECURED_BIT_MASK,
        )

        # A torn save after FE7F resumes the epilogue from this same console;
        # it neither reopens the prebattle speech nor starts Sufal again.
        recovered = _run_appointment_vm(
            editor.bytecode,
            start_pc=boss_pc,
            menu_choices={43: 1},
            variables={
                campaign.STATE_OPERAND:
                    campaign.FINALE_EPILOGUE_PENDING_BIT_MASK,
            },
        )
        self.assertEqual(recovered["dialogue_ids"], (40,))
        self.assertEqual(recovered["battle_ids"], ())
        self.assertEqual(recovered["battle_syncs"], 0)
        self.assertEqual(
            recovered["sound_ids"],
            (campaign.PROGRESSION_CONFIRM_SOUND_ID,),
        )
        self.assertEqual(
            recovered["variables"][campaign.STATE_OPERAND]
            & (
                campaign.FINALE_EPILOGUE_PENDING_BIT_MASK
                | campaign.SECURED_BIT_MASK
            ),
            campaign.SECURED_BIT_MASK,
        )

        revisited = _run_appointment_vm(
            editor.bytecode,
            start_pc=boss_pc,
            menu_choices={43: 1},
            variables={campaign.STATE_OPERAND: campaign.SECURED_BIT_MASK},
        )
        self.assertEqual(revisited["dialogue_ids"], (41,))
        self.assertEqual(revisited["battle_ids"], ())
        self.assertEqual(revisited["battle_syncs"], 0)
        self.assertEqual(revisited["sound_ids"], ())
        self.assertEqual(
            tuple(
                (operand, bit_index)
                for _pc, operand, bit_index in revisited["bit_clears"]
            ),
            ((
                campaign.STATE_OPERAND,
                campaign.FINALE_EPILOGUE_PENDING_BIT_INDEX,
            ),),
        )

        torn_secured = _run_appointment_vm(
            editor.bytecode,
            start_pc=boss_pc,
            menu_choices={43: 1},
            variables={
                campaign.STATE_OPERAND: (
                    campaign.SECURED_BIT_MASK
                    | campaign.FINALE_EPILOGUE_PENDING_BIT_MASK
                ),
            },
        )
        self.assertEqual(torn_secured["dialogue_ids"], (41,))
        self.assertEqual(torn_secured["battle_ids"], ())
        self.assertEqual(torn_secured["battle_syncs"], 0)
        self.assertEqual(torn_secured["sound_ids"], ())
        self.assertEqual(
            torn_secured["variables"][campaign.STATE_OPERAND]
            & (
                campaign.SECURED_BIT_MASK
                | campaign.FINALE_EPILOGUE_PENDING_BIT_MASK
            ),
            campaign.SECURED_BIT_MASK,
        )

        finale_blocks = parse_dialogue(generation.components[7]).blocks
        for block_id, required in (
            (39, ("Sufal Mass", "Elly\n", "Fei\n")),
            (40, ("Other Surface systems", "Elly\n", "Fei\n", "Citan\n")),
        ):
            for text_value in required:
                self.assertIn(text_value, finale_blocks[block_id].text)
        shortcut_pc = editor.get_script_pointer(26, 2)
        shortcut = editor.bytecode[shortcut_pc : shortcut_pc + 40]
        self.assertTrue(
            shortcut.startswith(
                campaign._bit_test(
                    campaign.STATE_OPERAND,
                    campaign.SECURED_BIT_MASK,
                    shortcut_pc + 11,
                )
            )
        )

        transfer = self.field_by_scene[623]
        transfer_editor = ScriptEditor(transfer.components[base.SCRIPT_INDEX])
        reverse_pc = transfer_editor.get_script_pointer(38, 2)
        reverse = transfer_editor.bytecode[reverse_pc : reverse_pc + 8]
        self.assertEqual(
            reverse,
            campaign._bit_test(
                campaign.STATE_OPERAND,
                campaign.SECURED_BIT_MASK,
                struct.unpack_from("<H", reverse, 6)[0],
            ),
        )
        self.assertNotIn(
            struct.pack("<H", base.SURFACE_SHORTCUT_DISCOVERED_BIT),
            reverse[3:5],
        )

    def test_generation_save_console_uses_the_retained_menu_sequence(self) -> None:
        editor = ScriptEditor(self.field_by_scene[622].components[base.SCRIPT_INDEX])
        pc = editor.get_script_pointer(28, 2)
        self.assertEqual(
            editor.bytecode[pc : pc + 9],
            bytes.fromhex("33 FE 99 00 FE 55 FE 87 00"),
        )
        self.assertIn(
            bytes.fromhex("FE 99 00 FE 55 FE 87"),
            self.base_field_by_scene[622].components[base.SCRIPT_INDEX],
        )

    def test_service_manifold_preserves_dormant_future_lab_handoff(
        self,
    ) -> None:
        item = self.donor_by_scene[565]
        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
        p5 = editor.bytecode[1 + 7 * 5 : 1 + 7 * 6]
        self.assertEqual(p5, struct.pack("<hhBBB", 2970, -4520, 0, 5, 5))
        self.assertIn((5, 64), item.entry_triangles)

        e9_pc = editor.get_script_pointer(9, 2)
        e9_action = editor.bytecode[e9_pc : e9_pc + 64]
        self.assertIn(base._change_field(588, 0), e9_action)
        self.assertIn(bytes.fromhex("09 0E 24"), e9_action)

        contracts = campaign.DONOR_DOOR_COLLISION_CONTRACTS[565]
        e7_offset, e7_contract = next(
            (offset, contract)
            for offset, contract in enumerate(contracts)
            if contract.controller_entity
            == campaign.FIELD565_FUTURE_LAB_HANDOFF_ENTITY
        )
        self.assertEqual(
            (
                e7_contract.endpoint_id,
                e7_contract.arrival_parameter,
                e7_contract.closed_side_probe,
                e7_contract.open_side_probe,
            ),
            (
                "field565.future_lab_handoff_sealed",
                None,
                (3570, -2430),
                (3700, -2300),
            ),
        )
        e7_seal = editor.entity_count - len(contracts) + e7_offset
        e7_pc = editor.get_script_pointer(7, 2)
        e7_action = campaign._repeatable_dialogue_action(
            campaign.SERVICE_FUTURE_LAB_HANDOFF_DIALOGUE_ID,
            e7_pc,
        )
        self.assertEqual(
            editor.bytecode[e7_pc : e7_pc + len(e7_action)],
            e7_action,
        )
        self.assertNotIn(bytes.fromhex("09 12 24"), e7_action)
        self.assertNotIn(bytes((0x09, e7_seal, 0x24)), e7_action)
        self.assertNotIn(base._change_field(621, 5), e7_action)
        self.assertEqual(
            editor.bytecode.count(bytes((0x09, e7_seal, 0x24))),
            0,
        )
        denied = _run_appointment_vm(
            editor.bytecode,
            start_pc=e7_pc,
            variables={},
        )
        self.assertEqual(denied["dialogue_ids"], (16,))
        self.assertEqual(denied["sound_ids"], ())
        self.assertEqual(denied["blocking_calls"], ())
        self.assertIsNone(denied["field_change"])
        self.assertEqual(
            parse_dialogue(item.components[7]).blocks[
                campaign.SERVICE_FUTURE_LAB_HANDOFF_DIALOGUE_ID
            ].text,
            final_guidance.TEXT[565],
        )

        # The manifold's former production door is now ordinary circulation
        # into the ward.  Its four-clearance gate moved to the ward's actual
        # production-side e6 threshold rather than blocking exploration here.
        production_contracts = contracts
        production_offset, production_contract = next(
            (offset, contract)
            for offset, contract in enumerate(production_contracts)
            if contract.controller_entity == 5
        )
        production_seal = (
            editor.entity_count - len(production_contracts) + production_offset
        )
        production_pc = editor.get_script_pointer(5, 2)
        production_action = campaign._donor_fresh_cross_field_change_action(
            helper_entity=16,
            player_script=5,
            destination_field=stabilization590.SCENE,
            destination_parameter=0,
            routine_pc=production_pc,
            seal_entity=production_seal,
        )
        self.assertEqual(
            editor.bytecode[
                production_pc : production_pc + len(production_action)
            ],
            production_action,
        )
        production_result = _run_appointment_vm(
            editor.bytecode,
            start_pc=production_pc,
            variables={},
        )
        self.assertEqual(production_result["field_change"], (590, 0))
        self.assertEqual(
            production_result["blocking_calls"],
            ((16, 0x24), (production_seal, 0x24)),
        )

        quarantine_pc = editor.get_script_pointer(10, 2)
        self.assertTrue(
            editor.bytecode[quarantine_pc:].startswith(
                campaign._bit_test(
                    campaign.QUARANTINE_KEYCARD_OPERAND,
                    campaign.QUARANTINE_KEYCARD_MASK,
                    quarantine_pc + 11,
                )
            )
        )
        denied_despite_quarantine = _run_appointment_vm(
            editor.bytecode,
            start_pc=quarantine_pc,
            variables={
                campaign.QUARANTINE_KEYCARD_OPERAND: 0,
                campaign.STATE_OPERAND: campaign.QUARANTINE_MASK,
            },
        )
        self.assertEqual(
            denied_despite_quarantine["dialogue_ids"],
            (campaign.SERVICE_QUARANTINE_DENIAL_DIALOGUE_ID,),
        )
        self.assertIsNone(denied_despite_quarantine["field_change"])

        admitted_without_quarantine = _run_appointment_vm(
            editor.bytecode,
            start_pc=quarantine_pc,
            variables={
                campaign.QUARANTINE_KEYCARD_OPERAND: (
                    campaign.QUARANTINE_KEYCARD_MASK
                ),
                campaign.STATE_OPERAND: 0,
            },
        )
        self.assertEqual(
            admitted_without_quarantine["field_change"],
            (620, 1),
        )
        self.assertEqual(admitted_without_quarantine["dialogue_ids"], ())

    def test_field588_bright_scanner_room_is_interface_cutoff_only(self) -> None:
        item = self.donor_by_scene[588]
        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
        foundation_editor = ScriptEditor(
            self.base_588.components[base.SCRIPT_INDEX]
        )
        self.assertEqual(
            (donor588.SOURCE_SCENE, donor588.DONOR588_SOURCE_IDS),
            (550, (1711, 1712)),
        )
        self.assertEqual(
            (item.identity.bundle_id, item.identity.graphics_id),
            donor588.DONOR588_TARGET_IDS,
        )
        entry_pc = 1 + 7 * donor588.ENTRY_PARAMETER
        self.assertEqual(
            editor.bytecode[entry_pc : entry_pc + 7],
            struct.pack(
                "<hhBBB",
                *donor588.ENTRY_POSITION,
                donor588.ENTRY_WALKMESH,
                donor588.ENTRY_CAMERA_DIRECTION,
                donor588.ENTRY_ACTOR_DIRECTION,
            ),
        )
        self.assertEqual(
            item.entry_triangles,
            ((donor588.ENTRY_PARAMETER, donor588.ENTRY_TRIANGLE),),
        )

        # The bright scanner lab keeps its authentic model-backed south door.
        # Its checked native leaf/helper body points directly back to the
        # Intake threshold, while collision separation adds a fresh reciprocal
        # Service-Manifold wrapper around that preserved animation.
        transition_pc = donor588.RETURN_TRANSITION_PC
        self.assertEqual(
            editor.bytecode[transition_pc : transition_pc + 5],
            base._change_field(donor588.RETURN_FIELD, donor588.RETURN_PARAMETER),
        )
        self.assertEqual(
            foundation_editor.get_script_pointer(donor588.RETURN_CONTROLLER, 2),
            donor588.RETURN_CONTROLLER_ACTION_PC,
        )
        self.assertEqual(
            foundation_editor.bytecode[
                donor588.RETURN_CONTROLLER_ACTION_PC :
                donor588.RETURN_CONTROLLER_ACTION_PC + len(donor588.RETURN_ACTION)
            ],
            donor588.RETURN_ACTION,
        )
        return_pc = editor.get_script_pointer(donor588.RETURN_CONTROLLER, 2)
        self.assertNotEqual(return_pc, donor588.RETURN_CONTROLLER_ACTION_PC)
        contracts = campaign.DONOR_DOOR_COLLISION_CONTRACTS[588]
        self.assertEqual(len(contracts), 1)
        seal_entity = editor.entity_count - len(contracts)
        return_action = campaign._donor_native_field_change_action(
            helper_entity=donor588.RETURN_HELPER,
            player_script=donor588.RETURN_PLAYER_SCRIPT_INDEX,
            destination_field=565,
            destination_parameter=5,
            seal_entity=seal_entity,
            routine_pc=return_pc,
        )
        self.assertEqual(
            editor.bytecode[return_pc : return_pc + len(return_action)],
            return_action,
        )

        # V207 reuses native scanner carrier e4 at the center of the six baked
        # scanner nodes.  The console adds no actor-table record: only the door
        # seal inserted at source boundary 29 shifts those static nodes.
        self.assertEqual(donor588.CONSOLE_ENTITY, 4)
        self.assertEqual(
            (
                campaign.INTERFACE_CONSOLE.x,
                campaign.INTERFACE_CONSOLE.z,
                campaign.INTERFACE_CONSOLE.triangle,
                campaign.INTERFACE_CONSOLE.interaction_half_width,
                campaign.INTERFACE_CONSOLE.interaction_half_depth,
            ),
            (190, 190, 34, 0x1E, 0x1E),
        )
        source_records = _actor_records(self.base_588.header)
        final_records = _actor_records(item.header)
        source_entity_count = min(donor588.STATIC_NODE_RANGE)
        source_header_actor_count = max(donor588.STATIC_NODE_RANGE) + 1
        self.assertEqual(
            (foundation_editor.entity_count, len(source_records)),
            (source_entity_count, source_header_actor_count),
        )
        self.assertEqual(
            (editor.entity_count, len(final_records)),
            (
                source_entity_count + len(contracts),
                source_header_actor_count + len(contracts),
            ),
        )
        self.assertEqual(
            donor588.STATIC_NODE_RANGE,
            tuple(range(source_entity_count, source_header_actor_count)),
        )
        self.assertEqual(
            tuple(
                struct.unpack("<8H", source_records[node])
                for node in donor588.VISIBLE_SCANNER_STATIC_NODES
            ),
            donor588.VISIBLE_SCANNER_STATIC_RECORDS,
        )
        self.assertEqual(
            tuple(
                struct.unpack("<8H", source_records[node])[-1]
                for node in donor588.STATIC_NODE_RANGE
            ),
            donor588.STATIC_NODE_MODELS,
        )
        self.assertEqual(
            donor588.VISIBLE_SCANNER_STATIC_NODES,
            (29, 30, 31, 32, 33, 34),
        )
        self.assertEqual(
            donor588.CAMPAIGN_VISIBLE_SCANNER_STATIC_NODES,
            (30, 31, 32, 33, 34, 35),
        )
        for source_node in donor588.STATIC_NODE_RANGE:
            with self.subTest(preserved_static_node=source_node):
                self.assertEqual(
                    final_records[source_node + len(contracts)],
                    source_records[source_node],
                )

        # The source room's e19-e28 story/treasure carriers are terminal STOP
        # records, so both native item awards and every donor cutscene are
        # unreachable.  e5-e16 retain only harmless hide/disable initializers;
        # all their later scanner behaviors are parked as well.
        self.assertEqual(donor588.RETIRED_ENTITIES, tuple(range(19, 29)))
        for entity in donor588.RETIRED_ENTITIES:
            for script_index in range(32):
                with self.subTest(
                    retired_story_entity=entity,
                    script_index=script_index,
                ):
                    self.assertEqual(
                        editor.get_script_pointer(entity, script_index),
                        donor588.SHARED_STOP_PC,
                    )
        for entity in donor588.SCANNER_FIXTURE_ENTITIES:
            for script_index in range(1, 32):
                with self.subTest(
                    parked_scanner_entity=entity,
                    script_index=script_index,
                ):
                    self.assertEqual(
                        editor.get_script_pointer(entity, script_index),
                        donor588.SHARED_STOP_PC,
                    )
        for script_index in range(1, 32):
            self.assertEqual(
                foundation_editor.get_script_pointer(
                    donor588.CONSOLE_ENTITY,
                    script_index,
                ),
                donor588.SHARED_STOP_PC,
            )
            if script_index == 2:
                continue
            with self.subTest(console_retired_script_index=script_index):
                self.assertEqual(
                    editor.get_script_pointer(
                        donor588.CONSOLE_ENTITY,
                        script_index,
                    ),
                    donor588.SHARED_STOP_PC,
                )

        console_init_pc = editor.get_script_pointer(donor588.CONSOLE_ENTITY, 0)
        console_init = campaign._console_init(campaign.INTERFACE_CONSOLE)
        self.assertEqual(
            editor.bytecode[
                console_init_pc : console_init_pc + len(console_init)
            ],
            console_init,
        )
        self.assertIn(bytes.fromhex("F8 07 04 00"), console_init)
        self.assertIn(
            b"\x18"
            + bytes(
                (
                    donor588.CONSOLE_INTERACTION_HALF_WIDTH,
                    donor588.CONSOLE_INTERACTION_HALF_DEPTH,
                    0x64,
                    min(
                        donor588.CONSOLE_INTERACTION_HALF_WIDTH,
                        donor588.CONSOLE_INTERACTION_HALF_DEPTH,
                    ),
                )
            ),
            console_init,
        )

        pc = editor.get_script_pointer(donor588.CONSOLE_ENTITY, 2)
        action = campaign._interface_cutoff_action(
            interface_dialogue_id=campaign.INTERFACE_DIAGNOSTIC_DIALOGUE_ID,
            routine_pc=pc,
        )
        self.assertEqual(editor.bytecode[pc : pc + len(action)], action)
        self.assertIn(
            campaign._set_bit(campaign.STATE_OPERAND, campaign.INTERFACE_BIT_INDEX),
            action,
        )
        self.assertNotIn(
            campaign._set_bit(
                campaign.QUARANTINE_KEYCARD_OPERAND,
                campaign.QUARANTINE_KEYCARD_BIT_INDEX,
            ),
            action,
        )

        # The scanner independently arms the production-interface cutoff.  It
        # never issues the Quarantine keycard now housed in Examination Room C.
        first_use = _run_appointment_vm(
            editor.bytecode,
            start_pc=pc,
            variables={
                campaign.TONE_OPERAND: 0,
                campaign.STATE_OPERAND: 0,
                campaign.QUARANTINE_KEYCARD_OPERAND: 0,
            },
        )
        self.assertEqual(
            first_use["dialogue_ids"],
            (campaign.INTERFACE_DIAGNOSTIC_DIALOGUE_ID,),
        )
        self.assertEqual(
            first_use["sound_ids"],
            (campaign.PROGRESSION_CONFIRM_SOUND_ID,),
        )
        self.assertEqual(
            first_use["variables"][campaign.STATE_OPERAND]
            & campaign.INTERFACE_BIT_MASK,
            campaign.INTERFACE_BIT_MASK,
        )
        self.assertEqual(
            first_use["variables"][campaign.QUARANTINE_KEYCARD_OPERAND]
            & campaign.QUARANTINE_KEYCARD_MASK,
            0,
        )
        self.assertEqual(
            tuple((operand, bit) for _pc, operand, bit in first_use["bit_writes"]),
            ((campaign.STATE_OPERAND, campaign.INTERFACE_BIT_INDEX),),
        )

        repeat = _run_appointment_vm(
            editor.bytecode,
            start_pc=pc,
            variables={
                campaign.TONE_OPERAND: 0,
                campaign.STATE_OPERAND: campaign.INTERFACE_BIT_MASK,
                campaign.QUARANTINE_KEYCARD_OPERAND: 0,
            },
        )
        self.assertEqual(
            repeat["dialogue_ids"],
            (campaign.INTERFACE_DIAGNOSTIC_DIALOGUE_ID,),
        )
        self.assertEqual(repeat["sound_ids"], ())
        self.assertEqual(repeat["bit_writes"], ())
        raw_source_encounters = EncounterTable(
            parse_field(self.base_588.source_bundle).parts[6].data
        )
        foundation_encounters = EncounterTable(self.base_588.components[6])
        final_encounters = EncounterTable(item.components[6])
        self.assertEqual(
            raw_source_encounters.weights,
            donor588.SOURCE_ENCOUNTER_WEIGHTS,
        )
        self.assertEqual(
            foundation_encounters.weights,
            donor588.FINAL_ENCOUNTER_WEIGHTS,
        )
        self.assertEqual(
            final_encounters.weights,
            donor588.FINAL_ENCOUNTER_WEIGHTS,
        )
        self.assertEqual(
            item.components[6][:-16],
            self.base_588.components[6][:-16],
        )

        source_dialogue = parse_dialogue(self.base_588.components[7]).blocks
        final_dialogue = parse_dialogue(item.components[7]).blocks
        self.assertEqual(len(source_dialogue), 10)
        self.assertEqual(
            final_dialogue[campaign.INTERFACE_DIAGNOSTIC_DIALOGUE_ID].text,
            campaign.INTERFACE_CONSOLE.text,
        )
        self.assertEqual(
            final_dialogue[campaign.QUARANTINE_KEYCARD_DIALOGUE_ID].text,
            campaign.QUARANTINE_KEYCARD_DIALOGUE,
        )

    def test_field593_terminal_is_the_sole_quarantine_keycard_writer(self) -> None:
        keycard_write = campaign._set_bit(
            campaign.QUARANTINE_KEYCARD_OPERAND,
            campaign.QUARANTINE_KEYCARD_BIT_INDEX,
        )
        prepared = self.field_by_scene | self.donor_by_scene
        writers = {
            scene: item.components[base.SCRIPT_INDEX].count(keycard_write)
            for scene, item in prepared.items()
            if keycard_write in item.components[base.SCRIPT_INDEX]
        }
        self.assertEqual(writers, {593: 1})

        for scene in exam_rooms.SCENES:
            item = self.donor_by_scene[scene]
            editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
            action_pc = editor.get_script_pointer(exam_rooms.TERMINAL_ENTITY, 2)
            if scene in (591, 592, 594):
                from modules.soylent_system.tools import surface_soylent_clinical_discoveries as discoveries
                expected = discoveries.expected_terminal_action(scene)
                self.assertEqual(action_pc, discoveries.TERMINAL_ACTION_PCS[scene])
                self.assertEqual(editor.bytecode[action_pc:action_pc + len(expected)], expected)
                self.assertNotIn(keycard_write, expected)
                self.assertNotIn(exam_rooms.ITEM_ACQUISITION_SOUND, expected)
                continue
            action_length = exam_rooms.TERMINAL_ACTION_LENGTHS_BY_SCENE[scene]
            action = editor.bytecode[action_pc : action_pc + action_length]
            with self.subTest(scene=scene):
                self.assertEqual(action_pc, exam_rooms.TERMINAL_ACTION_PC)
                self.assertEqual(
                    _sha256(action),
                    exam_rooms.TERMINAL_ACTION_SHA256_BY_SCENE[scene],
                )
                self.assertEqual(
                    keycard_write in action,
                    scene == 593,
                )
                self.assertEqual(
                    exam_rooms.ITEM_ACQUISITION_SOUND in action,
                    scene == 593,
                )

        item = self.donor_by_scene[593]
        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
        action_pc = editor.get_script_pointer(exam_rooms.TERMINAL_ENTITY, 2)
        inserted_id, acquired_id, empty_id, choice_id = (
            exam_rooms.TERMINAL_DIALOGUE_IDS_BY_SCENE[593]
        )
        dialogue = parse_dialogue(item.components[7]).blocks
        self.assertEqual(
            tuple(
                dialogue[dialogue_id].text
                for dialogue_id in (
                    inserted_id,
                    acquired_id,
                    empty_id,
                    choice_id,
                )
            ),
            exam_rooms.EXAM_ROOM_BY_SCENE[593].terminal_dialogues,
        )

        first_use = _run_appointment_vm(
            editor.bytecode,
            start_pc=action_pc,
            variables={campaign.QUARANTINE_KEYCARD_OPERAND: 0},
            menu_choices={choice_id: 1},
        )
        self.assertEqual(
            first_use["dialogue_ids"],
            (inserted_id, choice_id, acquired_id),
        )
        self.assertEqual(
            first_use["sound_ids"],
            (exam_rooms.ITEM_ACQUISITION_SOUND_ID,),
        )
        self.assertEqual(
            first_use["variables"][campaign.QUARANTINE_KEYCARD_OPERAND]
            & campaign.QUARANTINE_KEYCARD_MASK,
            campaign.QUARANTINE_KEYCARD_MASK,
        )
        self.assertEqual(
            tuple((operand, bit) for _pc, operand, bit in first_use["bit_writes"]),
            ((
                campaign.QUARANTINE_KEYCARD_OPERAND,
                campaign.QUARANTINE_KEYCARD_BIT_INDEX,
            ),),
        )

        declined = _run_appointment_vm(
            editor.bytecode,
            start_pc=action_pc,
            variables={campaign.QUARANTINE_KEYCARD_OPERAND: 0},
            menu_choices={choice_id: 2},
        )
        self.assertEqual(declined["dialogue_ids"], (inserted_id, choice_id))
        self.assertEqual(declined["sound_ids"], ())
        self.assertEqual(declined["bit_writes"], ())
        self.assertEqual(
            declined["variables"][campaign.QUARANTINE_KEYCARD_OPERAND]
            & campaign.QUARANTINE_KEYCARD_MASK,
            0,
        )

        repeat = _run_appointment_vm(
            editor.bytecode,
            start_pc=action_pc,
            variables={
                campaign.QUARANTINE_KEYCARD_OPERAND: (
                    campaign.QUARANTINE_KEYCARD_MASK
                )
            },
        )
        self.assertEqual(repeat["dialogue_ids"], (empty_id,))
        self.assertEqual(repeat["sound_ids"], ())
        self.assertEqual(repeat["bit_writes"], ())

    def test_field589_native_five_tones_are_a_clue_not_authorization(self) -> None:
        item = self.donor_by_scene[589]
        editor = ScriptEditor(item.components[base.SCRIPT_INDEX])
        self.assertEqual(
            editor.get_script_pointer(campaign.RESONANCE_CLUE_ENTITY, 2),
            campaign.RESONANCE_CLUE_ACTION_PC,
        )

        native_prefix = editor.bytecode[
            campaign.RESONANCE_CLUE_ACTION_PC :
            campaign.RESONANCE_CLUE_TAIL_PC
        ]
        tone_sequence = tuple(
            bytes((0x74, sound_id, 0x81))
            for sound_id in (0x91, 0x92, 0x91, 0x94, 0x93)
        )
        tone_offsets = []
        cursor = 0
        for sound in tone_sequence:
            offset = native_prefix.index(sound, cursor)
            tone_offsets.append(offset)
            cursor = offset + len(sound)
        self.assertEqual(tone_offsets, sorted(tone_offsets))
        self.assertIn(
            campaign._set_bit(
                campaign.TONE_OPERAND,
                campaign.RESONANCE_CLUE_BIT_INDEX,
            ),
            native_prefix,
        )

        tail_patch = editor.bytecode[
            campaign.RESONANCE_CLUE_TAIL_PC :
            campaign.RESONANCE_CLUE_TAIL_PC + len(campaign.RESONANCE_CLUE_TAIL)
        ]
        self.assertEqual(
            tail_patch,
            campaign._jump(campaign.RESONANCE_CLUE_RECEIPT_ACTION_PC)
            + b"\x00" * (len(campaign.RESONANCE_CLUE_TAIL) - 3),
        )

        action_pc = campaign.RESONANCE_CLUE_RECEIPT_ACTION_PC
        action = editor.bytecode[action_pc:]
        receipt = (
            b"\xF5"
            + struct.pack("<H", campaign.RESONANCE_CLUE_RECEIPT_DIALOGUE_ID)
            + b"\x01\x9C"
        )
        sound_at = action.index(campaign.PROGRESSION_CONFIRM_SOUND)
        receipt_at = action.index(receipt)
        tail_at = action.index(campaign.RESONANCE_CLUE_TAIL)
        self.assertLess(sound_at, receipt_at)
        self.assertLess(receipt_at, tail_at)
        self.assertEqual(action.count(campaign.PROGRESSION_CONFIRM_SOUND), 1)
        self.assertEqual(action.count(receipt), 1)
        self.assertEqual(
            editor.bytecode.count(
                campaign._set_bit(campaign.TONE_OPERAND, campaign.TONE_BIT_INDEX)
            ),
            0,
        )

        receipt_block = parse_dialogue(item.components[7]).blocks[
            campaign.RESONANCE_CLUE_RECEIPT_DIALOGUE_ID
        ]
        self.assertEqual(receipt_block.text, final_guidance.TEXT[589])
        self.assertEqual(
            campaign._normalized_authored_dialogue_words(receipt_block.text),
            campaign._normalized_authored_dialogue_words(
                final_guidance.TEXT[589]
            ),
        )

    def test_intake_waiting_area_is_hopeful_before_soylent_reveal(self) -> None:
        expected_adult_dialogues = {
            2: (
                "They say the treatment can\n"
                "slow the changes. For the\n"
                "first time in weeks, I feel\n"
                "hopeful.<Close>"
            ),
            3: (
                "The staff explained each step\n"
                "and promised to help us.\n"
                "I think we finally came to\n"
                "the right place.<Close>"
            ),
            4: (
                "My appointment is soon.\n"
                "Maybe the doctors can steady\n"
                "my hands and send me home\n"
                "feeling like myself again.<Close>"
            ),
            5: (
                "My brother went in first.\n"
                "He told me not to worry.\n"
                "By tonight, maybe we will\n"
                "both be feeling better.<Close>"
            ),
            6: (
                "They have a test for every\n"
                "symptom. Once my chart is\n"
                "ready, the doctors will know\n"
                "which treatment I need.<Close>"
            ),
            8: (
                "The receptionist has been\n"
                "kind to everyone. Sign in at\n"
                "the terminal, and they will\n"
                "call when it is your turn.<Close>"
            ),
            9: (
                "They say the treatment rooms\n"
                "have the newest equipment.\n"
                "I hope I am cleared for my\n"
                "first session today.<Close>"
            ),
            10: (
                "Everything is so organized.\n"
                "Patients, staff, and supplies\n"
                "all have their own routes.\n"
                "They must help so many here.<Close>"
            ),
        }
        self.assertEqual(
            campaign.INTAKE_WAITING_AREA_HOPEFUL_DIALOGUES,
            expected_adult_dialogues,
        )
        intake_blocks = parse_dialogue(self.field_by_scene[621].components[7]).blocks
        self.assertEqual(
            {
                dialogue_id: intake_blocks[dialogue_id].text
                for dialogue_id in expected_adult_dialogues
            },
            expected_adult_dialogues,
        )
        self.assertEqual(
            intake_blocks[campaign.INTAKE_BOY_DIALOGUE_ID].text,
            "I like turtles!<Close>",
        )

        texts = {
            scene: "\n".join(block.text for block in parse_dialogue(item.components[7]).blocks)
            for scene, item in self.field_by_scene.items()
            if scene in (621, 620, 622)
        }
        combined = "\n".join(texts.values())
        normalized = {
            scene: " ".join(text.replace("<New>", " ").split())
            for scene, text in texts.items()
        }
        self.assertNotIn("Solaris promised relief", combined)
        self.assertNotIn("limiter signal", combined.lower())
        self.assertNotIn("nanomachines are in everyone", combined.lower())
        self.assertNotIn("The Meld was a person", combined)
        for premature_revelation in (
            "holding rooms",
            "processing floor",
            "caste index",
            "walls close around us",
            "service manifold",
        ):
            self.assertNotIn(premature_revelation, normalized[621].lower())
        self.assertIn("first time in weeks, I feel hopeful", normalized[621])
        self.assertIn("promised to help us", normalized[621])
        self.assertIn("I like turtles!", normalized[621])
        self.assertIn("Meld is made from people", normalized[622])
        self.assertIn("other surface systems remain", normalized[622].lower())

    def test_all_authored_dialogue_is_word_safe_and_retail_text_is_untouched(self) -> None:
        prepared = self.field_by_scene | self.donor_by_scene
        foundations = self.base_field_by_scene | self.base_donor_by_scene | {
            567: self.base_567,
            588: self.base_588,
        }
        self.assertEqual(
            sum(len(ids) for ids in campaign.CAMPAIGN_AUTHORED_DIALOGUE_IDS.values()),
            75,
        )
        self.assertEqual(
            sum(
                len(replacements)
                for replacements in campaign.CAMPAIGN_DIALOGUE_LAYOUT_REPLACEMENTS.values()
            ),
            48,
        )
        self.assertEqual(
            set(campaign.CAMPAIGN_AUTHORED_DIALOGUE_IDS),
            set(campaign.CAMPAIGN_DIALOGUE_LAYOUT_REPLACEMENTS),
        )

        for scene, owned_ids in campaign.CAMPAIGN_AUTHORED_DIALOGUE_IDS.items():
            final = parse_dialogue(prepared[scene].components[7]).blocks
            before = parse_dialogue(foundations[scene].components[7]).blocks
            owned = set(owned_ids)
            for block_id in owned_ids:
                with self.subTest(scene=scene, authored_block=block_id):
                    self.assertEqual(
                        campaign._campaign_dialogue_layout_issues(final[block_id]),
                        (),
                    )
            for block_id in range(min(len(before), len(final))):
                if block_id in owned:
                    continue
                with self.subTest(scene=scene, retained_block=block_id):
                    self.assertEqual(
                        (
                            final[block_id].width,
                            final[block_id].height,
                            final[block_id].payload,
                        ),
                        (
                            before[block_id].width,
                            before[block_id].height,
                            before[block_id].payload,
                        ),
                    )

        intake = self.field_by_scene[621]
        blocks = parse_dialogue(intake.components[7]).blocks
        boy = blocks[campaign.INTAKE_BOY_DIALOGUE_ID]
        self.assertEqual((boy.width, boy.height), (58, 4))
        self.assertEqual(boy.text, campaign.INTAKE_BOY_DIALOGUE)
        self.assertEqual(
            boy.payload,
            bytes.fromhex("28 10 48 45 47 41 10 50 51 4E 50 48 41 4F 57 00"),
        )
        editor = ScriptEditor(intake.components[base.SCRIPT_INDEX])
        boy_action = campaign._intake_native_dialogue_mutex_action(
            campaign.INTAKE_BOY_DIALOGUE_ID
        )
        boy_action_pc = editor.get_script_pointer(campaign.INTAKE_BOY_ENTITY, 2)
        self.assertNotEqual(boy_action_pc, 0x0377)
        self.assertEqual(
            editor.bytecode[0x0377 : 0x037D],
            bytes.fromhex("D2 07 00 00 9C 00"),
        )
        self.assertEqual(
            editor.bytecode[boy_action_pc : boy_action_pc + len(boy_action)],
            boy_action,
        )

    def test_authored_dialogue_grid_validator_matches_encoded_font_units(self) -> None:
        def block(text: str, *, width: int = 58, height: int = 4):
            return parse_dialogue(
                encode_dialogue((DialogueBlockSpec(0, width, height, text),))
            ).blocks[0]

        self.assertEqual(
            campaign._campaign_dialogue_layout_issues(block("A" * 29 + "<Close>")),
            (),
        )
        self.assertTrue(
            campaign._campaign_dialogue_layout_issues(block("A" * 30 + "<Close>"))
        )
        self.assertEqual(
            campaign._campaign_dialogue_layout_issues(block("*" * 19 + "<Close>")),
            (),
        )
        self.assertTrue(
            campaign._campaign_dialogue_layout_issues(block("*" * 20 + "<Close>"))
        )
        self.assertEqual(
            campaign._campaign_dialogue_layout_issues(
                block("A" * 29 + "\n" + "B" * 29 + "<New>C<Close>", height=2)
            ),
            (),
        )
        self.assertTrue(
            campaign._campaign_dialogue_layout_issues(
                block("one\ntwo\nthree<Close>", height=2)
            )
        )
        self.assertTrue(
            campaign._campaign_dialogue_layout_issues(block("<Byte:04><Close>"))
        )
        self.assertEqual(
            campaign._normalized_authored_dialogue_words(
                "word-boundary\nlayout<New>stays intact.<Close>"
            ),
            "word-boundary layout stays intact.",
        )
        self.assertNotEqual(
            campaign._normalized_authored_dialogue_words("walk to<Close>"),
            campaign._normalized_authored_dialogue_words("walk t\no<Close>"),
        )

    def test_title_bootstrap_is_campaign_specific_and_installs_canonical_party(self) -> None:
        self.assertEqual(
            tuple(item.canonical_id for item in self.title),
            (1586, 1587, 2593, 2595, 2599),
        )
        resource = next(item for item in self.title if item.canonical_id == 1586)
        self.assertEqual(
            (len(resource.data), _sha256(resource.data)),
            (
                campaign_title.CAMPAIGN_TITLE_BUNDLE_SIZE,
                campaign_title.CAMPAIGN_TITLE_BUNDLE_SHA256,
            ),
        )
        script = parse_field(resource.data).parts[base.SCRIPT_INDEX].data
        editor = ScriptEditor(script)
        reset = editor.bytecode[
            campaign_title.CAMPAIGN_RESET_PC :
            campaign_title.CAMPAIGN_RESET_PC + len(campaign_title.CAMPAIGN_RESET_ROUTINE)
        ]
        self.assertEqual(reset, campaign_title.CAMPAIGN_RESET_ROUTINE)
        self.assertIn(campaign_title.CAMPAIGN_PARTY_BOOTSTRAP, reset)
        for bit in (7, *range(11, 16)):
            self.assertIn(b"\x3B\xFA\x03" + struct.pack("<H", bit) + b"\x40", reset)

        gamestate = next(item for item in self.title if item.canonical_id == 2595)
        self.assertEqual(
            (len(gamestate.data), _sha256(gamestate.data)),
            (
                campaign_title.CAMPAIGN_INITIAL_GAMESTATE_SIZE,
                campaign_title.CAMPAIGN_INITIAL_GAMESTATE_SHA256,
            ),
        )
        for profile in deathblows.DEATHBLOW_PROFILES:
            with self.subTest(character=profile.character):
                self.assertEqual(
                    deathblows.learned_mask(
                        gamestate.data, profile.character_id
                    )
                    & profile.full_mask,
                    profile.full_mask,
                )

    def test_materialized_manifest_is_the_blueprint_not_the_old_slice(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "campaign"
            fields, donors, replacements = campaign.build_campaign(
                SOURCE_DISC,
                DONOR_DISC,
                output,
            )
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["format"], campaign.OUTPUT_FORMAT)
            deathblow_manifest = manifest["player_deathblows"]
            self.assertFalse(deathblow_manifest["levels_changed"])
            self.assertFalse(deathblow_manifest["stats_changed"])
            self.assertEqual(
                deathblow_manifest["gamestate_sha256"],
                campaign_title.CAMPAIGN_INITIAL_GAMESTATE_SHA256,
            )
            self.assertEqual(
                [profile["full_mask"] for profile in deathblow_manifest["profiles"]],
                [
                    f"0x{profile.full_mask:04X}"
                    for profile in deathblows.DEATHBLOW_PROFILES
                ],
            )
            self.assertEqual(len(manifest["rooms"]), 18)
            self.assertEqual(len(manifest["doors"]), 20)
            medical_room = next(
                room for room in manifest["rooms"] if room["field"] == 567
            )
            self.assertEqual(
                (medical_room["slug"], medical_room["name"], medical_room["origin"]),
                (
                    "unassigned_medical_examination_room",
                    "Unassigned Medical Examination Room",
                    "donor_ethos",
                ),
            )
            treatment_room = next(
                room for room in manifest["rooms"] if room["field"] == 594
            )
            self.assertEqual(
                (
                    treatment_room["slug"],
                    treatment_room["name"],
                    treatment_room["origin"],
                ),
                (
                    "treatment_preparation_room",
                    "Treatment Preparation Room",
                    "donor_ethos",
                ),
            )
            doors = {door["id"]: door for door in manifest["doors"]}
            audited_endpoints = {
                endpoint["id"]: (
                    endpoint["field"],
                    endpoint["local_entry_parameter"],
                    endpoint["destination_field"],
                    endpoint["destination_entry_parameter"],
                )
                for door_id in (
                    "intake_quarantine",
                    "intake_archive",
                    "intake_service_patient",
                    "intake_medical_examination",
                    "intake_treatment_preparation",
                    "service_stabilization_production",
                    "service_stabilization_staff",
                    "stabilization_sorting",
                )
                for endpoint in doors[door_id]["endpoints"]
            }
            self.assertEqual(
                audited_endpoints,
                {
                    "intake_quarantine.intake": (621, 2, 620, 0),
                    "intake_quarantine.quarantine": (620, 0, 621, 2),
                    "intake_archive.intake": (621, 0, 549, 0),
                    "intake_archive.archive": (549, 0, 621, 0),
                    "intake_service_patient.intake": (621, 1, 565, 0),
                    "intake_service_patient.service": (565, 0, 621, 1),
                    "intake_medical_examination.intake": (621, 4, 567, 0),
                    "intake_medical_examination.examination": (567, 0, 621, 4),
                    "intake_treatment_preparation.intake": (621, 5, 594, 0),
                    "intake_treatment_preparation.treatment": (594, 0, 621, 5),
                    "service_stabilization_production.service": (565, 1, 590, 0),
                    "service_stabilization_production.stabilization": (590, 0, 565, 1),
                    "service_stabilization_staff.service": (565, 2, 590, 1),
                    "service_stabilization_staff.stabilization": (590, 1, 565, 2),
                    "stabilization_sorting.stabilization": (590, 2, 624, 0),
                    "stabilization_sorting.sorting": (624, 0, 590, 2),
                },
            )
            self.assertEqual(
                [
                    endpoint["id"]
                    for door in manifest["doors"]
                    for endpoint in door["endpoints"]
                    if (
                    endpoint["field"] == 565
                    and endpoint["local_entry_parameter"] == 2
                    )
                ],
                ["service_stabilization_staff.service"],
            )
            music = manifest["music"]
            self.assertEqual(music["track"], campaign.KRELIAN_LAB_MUSIC_TRACK)
            self.assertEqual(music["music_id"], campaign.KRELIAN_LAB_MUSIC_ID)
            self.assertEqual(
                music["opcode"],
                campaign.KRELIAN_LAB_MUSIC_OPCODE.hex(" ").upper(),
            )
            self.assertEqual(music["directory"], campaign.MUSIC_DIRECTORY)
            self.assertEqual(
                (music["wave_local_file"], music["sequence_local_file"]),
                (
                    campaign.KRELIAN_LAB_WAVE_LOCAL_FILE,
                    campaign.KRELIAN_LAB_SEQUENCE_LOCAL_FILE,
                ),
            )
            self.assertEqual(
                music["authentic_source_fields"],
                sorted(campaign.KRELIAN_LAB_MUSIC_SOURCE_EVIDENCE),
            )
            self.assertEqual(
                music["excluded_nortune_music_id"],
                campaign.NORTUNE_STEALTH_MUSIC_ID,
            )
            self.assertEqual(
                music["excluded_nortune_source_fields"],
                sorted(campaign.NORTUNE_STEALTH_MUSIC_SOURCE_EVIDENCE),
            )
            self.assertIn("field 565's native", music["provenance"])
            self.assertIn("Nortune", music["provenance"])
            self.assertEqual(
                music["initialized_rooms"],
                sorted(campaign.CAMPAIGN_PRE_MUSIC_SCRIPT_IDENTITIES),
            )
            self.assertEqual(
                music["selector"],
                "entity 0 script 0 in every campaign room",
            )
            self.assertIn("preserves the loaded sequence", music["transition_policy"])
            self.assertEqual(
                music["assets"],
                [
                    {
                        "local_file": local_file,
                        "size": identity[0],
                        "sha256": identity[1],
                    }
                    for local_file, identity in sorted(
                        campaign.KRELIAN_LAB_MUSIC_ASSET_IDENTITIES.items()
                    )
                ],
            )
            self.assertIsNone(manifest["current_content_boundary"])
            completion = manifest["quarantine_completion"]
            self.assertEqual(completion["required_local_value"], 0x70)
            self.assertEqual(completion["destination"], [565, 6])
            self.assertEqual(completion["award"], "quarantine_complete")
            self.assertEqual(completion["preserved_return"],
                             {"entity": 23, "destination": [621, 2]})
            checkin = manifest["intake_checkin"]
            receptionist = checkin["receptionist"]
            self.assertEqual(
                {
                    "field": receptionist["field"],
                    "entity": receptionist["entity"],
                    "retail_init_pc": receptionist["retail_init_pc"],
                    "wide_init_pc": receptionist["wide_init_pc"],
                    "action_pc": receptionist["action_pc"],
                    "actor_position": receptionist["actor_position"],
                    "retail_circular_effective_reach": receptionist[
                        "retail_circular_effective_reach"
                    ],
                    "interaction_operands": receptionist["interaction_operands"],
                    "interaction_effective_half_extents": receptionist[
                        "interaction_effective_half_extents"
                    ],
                },
                {
                    "field": 621,
                    "entity": campaign.INTAKE_RECEPTIONIST_ENTITY,
                    "retail_init_pc": campaign.INTAKE_RECEPTIONIST_RETAIL_INIT_PC,
                    "wide_init_pc": campaign.INTAKE_RECEPTIONIST_WIDE_INIT_PC,
                    "action_pc": campaign.INTAKE_RECEPTIONIST_ACTION_PC,
                    "actor_position": [870, 1302],
                    "retail_circular_effective_reach": 64,
                    "interaction_operands": [0x20, 0x40],
                    "interaction_effective_half_extents": [80, 144],
                },
            )
            self.assertEqual(
                receptionist["saved_stance"],
                [870.0675354, 1433.6101837],
            )
            self.assertIn("rectangular", receptionist["interaction_policy"])
            self.assertIn("no facing", receptionist["interaction_policy"])
            self.assertIn("sprite", receptionist["interaction_policy"])
            self.assertEqual(
                receptionist["before_registration"],
                campaign.RECEPTIONIST_PRECHECK_DIALOGUE.removesuffix("<Close>"),
            )
            self.assertEqual(
                receptionist["after_registration"],
                campaign.RECEPTIONIST_POSTCHECK_DIALOGUE.removesuffix("<Close>"),
            )
            self.assertEqual(
                checkin["door_behind_saved_stance"],
                {
                    "field": 621,
                    "entity": campaign.INTAKE_ARCHIVE_DOOR_ENTITY,
                    "action_pc": campaign.INTAKE_ARCHIVE_DOOR_ACTION_PC,
                    "destination": [549, 0],
                },
            )
            quarantine_shortcut = checkin["quarantine_keycard_door"]
            self.assertEqual(
                {
                    key: quarantine_shortcut[key]
                    for key in (
                        "field",
                        "entity",
                        "saved_stance",
                        "saved_facing",
                        "triangle",
                        "locked_action_pc",
                        "preserved_unlocked_action_pc",
                        "destination",
                        "dialogue",
                        "unlock_trigger",
                        "credential_operand",
                        "credential_bit_index",
                        "credential_mask",
                    )
                },
                {
                    "field": 621,
                    "entity": campaign.INTAKE_QUARANTINE_DOOR_ENTITY,
                    "saved_stance": [69.98291015625, 840],
                    "saved_facing": 0,
                    "triangle": 18,
                    "locked_action_pc": (
                        campaign.INTAKE_QUARANTINE_LOCK_ACTION_PC
                    ),
                    "preserved_unlocked_action_pc": (
                        campaign.INTAKE_QUARANTINE_DOOR_ACTION_PC
                    ),
                    "destination": list(
                        campaign.INTAKE_QUARANTINE_DESTINATION
                    ),
                    "dialogue": (
                        campaign.INTAKE_QUARANTINE_LOCK_DIALOGUE.removesuffix(
                            "<Close>"
                        )
                    ),
                    "unlock_trigger": (
                        "accept the Quarantine keycard in Examination Room C"
                    ),
                    "credential_operand": campaign.QUARANTINE_KEYCARD_OPERAND,
                    "credential_bit_index": (
                        campaign.QUARANTINE_KEYCARD_BIT_INDEX
                    ),
                    "credential_mask": campaign.QUARANTINE_KEYCARD_MASK,
                },
            )
            self.assertIn("bit-clear", quarantine_shortcut["policy"])
            self.assertIn("native e22", quarantine_shortcut["policy"])
            self.assertEqual(
                checkin["security_keycard_patient_door"],
                {
                    "field": 621,
                    "entity": campaign.INTAKE_PATIENT_DOOR_ENTITY,
                    "gate_action_pc": (
                        campaign.INTAKE_PATIENT_KEYCARD_GATE_ACTION_PC
                    ),
                    "preserved_unlocked_action_pc": (
                        campaign.INTAKE_PATIENT_DOOR_ACTION_PC
                    ),
                    "destination": list(campaign.INTAKE_PATIENT_DESTINATION),
                    "credential_operand": campaign.SECURITY_KEYCARD_OPERAND,
                    "credential_bit_index": campaign.SECURITY_KEYCARD_BIT_INDEX,
                    "credential_mask": campaign.SECURITY_KEYCARD_MASK,
                    "locked_dialogue": (
                        campaign.INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE.removesuffix(
                            "<Close>"
                        )
                    ),
                    "unlock_trigger": "victory over the clinic security team",
                    "policy": (
                        "bit-clear interactions drain Cross and report the "
                        "keycard requirement without sound, leaf animation, or "
                        "transition; bit-set interactions jump to the retained "
                        "native e24 open-and-enter action"
                    ),
                },
            )
            self.assertEqual(
                checkin["security_keycard_freight_door"],
                {
                    "field": 621,
                    "entity": campaign.INTAKE_FREIGHT_DOOR_ENTITY,
                    "role": "Treatment Preparation Room entrance",
                    "saved_stance": [1665.015869140625, 396],
                    "saved_facing": 0x0800,
                    "triangle": 85,
                    "gate_action_pc": (
                        campaign.INTAKE_FREIGHT_KEYCARD_GATE_ACTION_PC
                    ),
                    "preserved_unlocked_action_pc": (
                        campaign.INTAKE_FREIGHT_DOOR_ACTION_PC
                    ),
                    "destination": list(campaign.INTAKE_FREIGHT_DESTINATION),
                    "credential_operand": campaign.SECURITY_KEYCARD_OPERAND,
                    "credential_bit_index": (
                        campaign.SECURITY_KEYCARD_BIT_INDEX
                    ),
                    "credential_mask": campaign.SECURITY_KEYCARD_MASK,
                    "locked_dialogue": (
                        campaign.INTAKE_FREIGHT_KEYCARD_LOCK_DIALOGUE.removesuffix(
                            "<Close>"
                        )
                    ),
                    "unlock_trigger": "victory over the clinic security team",
                    "policy": (
                        "bit-clear interactions drain Cross and report the "
                        "keycard requirement without sound, leaf animation, "
                        "or transition; the credential jumps to the retained "
                        "native e26 open-and-enter action"
                    ),
                },
            )

            examination_rooms = manifest["intake_examination_rooms"]
            self.assertEqual(
                {
                    key: examination_rooms[key]
                    for key in (
                        "source_disc_field",
                        "source_resources",
                        "shared_style",
                        "intake_controller_entities",
                        "intake_helper_entities",
                        "intake_threshold_header_entities",
                        "intake_threshold_model",
                        "intake_camera_occluder_model",
                        "intake_entry_parameters",
                        "entrance_requirement",
                        "quarantine_keycard_source_field",
                        "quarantine_keycard_operand",
                        "quarantine_keycard_bit_index",
                        "quarantine_keycard_mask",
                        "pickup_sound_id",
                    )
                },
                {
                    "source_disc_field": exam_rooms.SOURCE_SCENE,
                    "source_resources": list(exam_rooms.SOURCE_IDS),
                    "shared_style": (
                        "bright Solaris medical examination room with an intact "
                        "bed and illuminated clinical workstation"
                    ),
                    "intake_controller_entities": list(
                        campaign.INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES
                    ),
                    "intake_helper_entities": list(
                        campaign.INTAKE_EXAM_ROOM_HELPER_ENTITIES
                    ),
                    "intake_threshold_header_entities": list(
                        campaign.INTAKE_EXAM_ROOM_THRESHOLD_HEADER_ENTITIES
                    ),
                    "intake_threshold_model": {
                        "model_index": (
                            campaign.INTAKE_EXAM_ROOM_THRESHOLD_MODEL_INDEX
                        ),
                        "size": campaign.INTAKE_EXAM_ROOM_THRESHOLD_MODEL_SIZE,
                        "sha256": (
                            campaign.INTAKE_EXAM_ROOM_THRESHOLD_MODEL_SHA256
                        ),
                        "flags": (
                            f"0x{campaign.INTAKE_EXAM_ROOM_THRESHOLD_MODEL_FLAGS:04X}"
                        ),
                        "placements": [
                            list(placement)
                            for placement in (
                                campaign.INTAKE_EXAM_ROOM_THRESHOLD_PLACEMENTS
                            )
                        ],
                        "rendering": (
                            "allocation-preserving clone of retail model 19's "
                            "single top-facing textured floor-apron FT4: 89 "
                            "units wide, 44 units beyond "
                            "the leaf on the far side, with no geometry on "
                            "the accessible hall side or above the leaf; "
                            "the far-depth V endpoint is capped at cyan-shadow "
                            "row 0x8D before the source texture's near-black "
                            "tail; fourteen retained F3 slots remain degenerate"
                        ),
                    },
                    "intake_camera_occluder_model": {
                        "model_index": (
                            campaign.INTAKE_EXAM_ROOM_OCCLUDER_MODEL_INDEX
                        ),
                        "size": campaign.INTAKE_EXAM_ROOM_OCCLUDER_MODEL_SIZE,
                        "native_sha256": (
                            campaign.INTAKE_EXAM_ROOM_NATIVE_OCCLUDER_MODEL_SHA256
                        ),
                        "final_sha256": (
                            campaign.INTAKE_EXAM_ROOM_OCCLUDER_MODEL_SHA256
                        ),
                        "disabled_mesh_groups": [0, 2],
                        "rendering": (
                            "only the native flat-black F3 corner-cap and F4 "
                            "ceiling-fascia index records are degenerate; "
                            "textured groups, packets, counts, offsets, "
                            "pointers, and model allocation remain unchanged"
                        ),
                    },
                    "intake_entry_parameters": list(
                        campaign.INTAKE_EXAM_ROOM_ENTRY_PARAMETERS
                    ),
                    "entrance_requirement": "security_keycard",
                    "quarantine_keycard_source_field": 593,
                    "quarantine_keycard_operand": (
                        campaign.QUARANTINE_KEYCARD_OPERAND
                    ),
                    "quarantine_keycard_bit_index": (
                        campaign.QUARANTINE_KEYCARD_BIT_INDEX
                    ),
                    "quarantine_keycard_mask": campaign.QUARANTINE_KEYCARD_MASK,
                    "pickup_sound_id": exam_rooms.ITEM_ACQUISITION_SOUND_ID,
                },
            )
            intake_exam_scenes = (591, 592, 593)
            self.assertEqual(
                [room["field"] for room in examination_rooms["rooms"]],
                list(intake_exam_scenes),
            )
            self.assertEqual(
                examination_rooms["policy"],
                (
                    "all four terminals retain their distinct stored diagnostic "
                    "records; field 593 has no patient or doctor and first offers "
                    "the visibly inserted card, committing it once"
                ),
            )
            self.assertIn("fields 591, 592 and 594", examination_rooms["population_policy"])
            self.assertIn("fields 567 and 593", examination_rooms["population_policy"])
            self.assertNotIn("empty access slot", examination_rooms["policy"])
            self.assertEqual(
                [
                    room["awards_quarantine_keycard"]
                    for room in examination_rooms["rooms"]
                ],
                [False, False, True],
            )
            for room, scene, controller, return_parameter in zip(
                examination_rooms["rooms"],
                intake_exam_scenes,
                campaign.INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES,
                (
                    exam_rooms.RETURN_PARAMETERS_BY_SCENE[scene]
                    for scene in intake_exam_scenes
                ),
                strict=True,
            ):
                with self.subTest(manifest_exam_room=scene):
                    self.assertEqual(
                        {
                            key: room[key]
                            for key in (
                                "field",
                                "target_resources",
                                "terminal_entity",
                                "terminal_position",
                                "terminal_model_index",
                                "bed_model_index",
                                "intake_controller_entity",
                                "intake_return_parameter",
                            )
                        },
                        {
                            "field": scene,
                            "target_resources": list(
                                exam_rooms.TARGET_IDS_BY_SCENE[scene]
                            ),
                            "terminal_entity": exam_rooms.TERMINAL_ENTITY,
                            "terminal_position": list(
                                exam_rooms.TERMINAL_POSITION
                            ),
                            "terminal_model_index": (
                                exam_rooms.MEDICAL_TERMINAL_MODEL_INDEX
                            ),
                            "bed_model_index": 2,
                            "intake_controller_entity": controller,
                            "intake_return_parameter": return_parameter,
                        },
                    )
                    self.assertEqual(
                        (
                            room["terminal_entities"],
                            room["terminal_positions"],
                            room["terminal_triangles"],
                            room["terminal_interaction"],
                        ),
                        (
                            list(exam_rooms.TERMINAL_ENTITIES),
                            [
                                list(position)
                                for position in exam_rooms.TERMINAL_POSITIONS
                            ],
                            list(exam_rooms.TERMINAL_TRIANGLES),
                            {
                                "half_extents_script_units": [0x01, 0x0F],
                                "effective_half_reach_world_units": [18, 46],
                                "requires_facing": True,
                            },
                        ),
                    )
                    asset = exam_rooms.PATIENT_ASSET_SPECS[scene]
                    self.assertEqual(
                        room["patient_record"],
                        {
                            "dialogue_id": (
                                exam_rooms.PATIENT_RECORD_DIALOGUE_IDS_BY_SCENE[
                                    scene
                                ]
                            ),
                            "dialogue": (
                                exam_rooms.PATIENT_RECORD_DIALOGUES_BY_SCENE[
                                    scene
                                ].removesuffix("<Close>")
                            ),
                            "repeatable": True,
                        },
                    )
                    self.assertEqual(
                        room["doctor"],
                        {
                            "present": scene != 593,
                            "entity": exam_rooms.DOCTOR_ENTITY,
                            "graphic_bank": exam_rooms.DOCTOR_BANK,
                            "position": list(exam_rooms.DOCTOR_POSITION),
                            "triangle": exam_rooms.DOCTOR_TRIANGLE,
                            "dialogue_id": (
                                exam_rooms.DOCTOR_DIALOGUE_IDS_BY_SCENE[scene]
                            ),
                            "dialogue": (
                                exam_rooms.DOCTOR_DIALOGUES_BY_SCENE[scene]
                                .removesuffix("<Close>")
                            ),
                            "actor_sha256": exam_rooms.DOCTOR_ACTOR_IDENTITY[1],
                            "sprite_sha256": exam_rooms.DOCTOR_SPRITE_IDENTITY[1],
                        },
                    )
                    self.assertEqual(
                        room["patient"],
                        {
                            "present": scene != 593,
                            "entity": exam_rooms.PATIENT_ENTITY,
                            "graphic_bank": exam_rooms.PATIENT_TARGET_BANK,
                            "position": list(exam_rooms.PATIENT_POSITION),
                            "triangle": exam_rooms.PATIENT_TRIANGLE,
                            "dialogue_id": (
                                exam_rooms.PATIENT_DIALOGUE_IDS_BY_SCENE[scene]
                            ),
                            "dialogue": (
                                exam_rooms.PATIENT_DIALOGUES_BY_SCENE[scene]
                                .removesuffix("<Close>")
                            ),
                            "appearance": asset.appearance,
                            "asset_source": {
                                "field": asset.source_scene,
                                "bank": asset.source_bank,
                                "actor_sha256": asset.actor_identity[1],
                                "sprite_sha256": asset.sprite_identity[1],
                            },
                        },
                    )

            treatment = manifest["intake_treatment_preparation"]
            self.assertEqual(
                treatment,
                {
                    "field": 594,
                    "name": "Treatment Preparation Room",
                    "source_disc_field": exam_rooms.SOURCE_SCENE,
                    "source_resources": list(exam_rooms.SOURCE_IDS),
                    "target_resources": list(
                        exam_rooms.TARGET_IDS_BY_SCENE[594]
                    ),
                    "intake_controller_entity": (
                        campaign.INTAKE_FREIGHT_DOOR_ENTITY
                    ),
                    "intake_entry_parameter": 5,
                    "entry_parameter": exam_rooms.ENTRY_PARAMETER,
                    "return_controller_entity": exam_rooms.RETURN_CONTROLLER,
                    "return_leaf_helper_entity": exam_rooms.RETURN_HELPER,
                    "return_destination": [621, 5],
                    "terminal_entity": exam_rooms.TERMINAL_ENTITY,
                    "terminal_entities": list(exam_rooms.TERMINAL_ENTITIES),
                    "terminal_position": list(exam_rooms.TERMINAL_POSITION),
                    "terminal_positions": [
                        list(position)
                        for position in exam_rooms.TERMINAL_POSITIONS
                    ],
                    "terminal_triangles": list(
                        exam_rooms.TERMINAL_TRIANGLES
                    ),
                    "terminal_model_index": (
                        exam_rooms.MEDICAL_TERMINAL_MODEL_INDEX
                    ),
                    "terminal_interaction": {
                        "half_extents_script_units": [0x01, 0x0F],
                        "effective_half_reach_world_units": [18, 46],
                        "requires_facing": True,
                    },
                    "bed_model_index": exam_rooms.BED_MODEL_INDEX,
                    "patient_record": {
                        "dialogue_id": (
                            exam_rooms.PATIENT_RECORD_DIALOGUE_IDS_BY_SCENE[594]
                        ),
                        "dialogue": (
                            exam_rooms.PATIENT_RECORD_DIALOGUES_BY_SCENE[594]
                            .removesuffix("<Close>")
                        ),
                        "repeatable": True,
                    },
                    "doctor": {
                        "entity": exam_rooms.DOCTOR_ENTITY,
                        "graphic_bank": exam_rooms.DOCTOR_BANK,
                        "position": list(exam_rooms.DOCTOR_POSITION),
                        "triangle": exam_rooms.DOCTOR_TRIANGLE,
                        "dialogue_id": (
                            exam_rooms.DOCTOR_DIALOGUE_IDS_BY_SCENE[594]
                        ),
                        "dialogue": (
                            exam_rooms.DOCTOR_DIALOGUES_BY_SCENE[594]
                            .removesuffix("<Close>")
                        ),
                        "actor_sha256": exam_rooms.DOCTOR_ACTOR_IDENTITY[1],
                        "sprite_sha256": exam_rooms.DOCTOR_SPRITE_IDENTITY[1],
                    },
                    "patient": {
                        "entity": exam_rooms.PATIENT_ENTITY,
                        "graphic_bank": exam_rooms.PATIENT_TARGET_BANK,
                        "position": list(exam_rooms.PATIENT_POSITION),
                        "triangle": exam_rooms.PATIENT_TRIANGLE,
                        "dialogue_id": (
                            exam_rooms.PATIENT_DIALOGUE_IDS_BY_SCENE[594]
                        ),
                        "dialogue": (
                            exam_rooms.PATIENT_DIALOGUES_BY_SCENE[594]
                            .removesuffix("<Close>")
                        ),
                        "appearance": (
                            exam_rooms.PATIENT_ASSET_SPECS[594].appearance
                        ),
                        "asset_source": {
                            "field": (
                                exam_rooms.PATIENT_ASSET_SPECS[594].source_scene
                            ),
                            "bank": (
                                exam_rooms.PATIENT_ASSET_SPECS[594].source_bank
                            ),
                            "actor_sha256": (
                                exam_rooms.PATIENT_ASSET_SPECS[594]
                                .actor_identity[1]
                            ),
                            "sprite_sha256": (
                                exam_rooms.PATIENT_ASSET_SPECS[594]
                                .sprite_identity[1]
                            ),
                        },
                    },
                    "entrance_requirement": "security_keycard",
                    "awards_quarantine_keycard": False,
                    "writes_progression": False,
                    "role": exam_rooms.EXAM_ROOM_BY_SCENE[594].role,
                    "terminal_text": (
                        exam_rooms.TREATMENT_PREPARATION_DIALOGUE.removesuffix(
                            "<Close>"
                        )
                    ),
                },
            )
            manifest_patient_records = {
                room["field"]: room["patient_record"]
                for room in examination_rooms["rooms"]
            }
            manifest_patient_records[594] = treatment["patient_record"]
            self.assertEqual(
                manifest_patient_records,
                {
                    scene: {
                        "dialogue_id": (
                            exam_rooms.PATIENT_RECORD_DIALOGUE_IDS_BY_SCENE[
                                scene
                            ]
                        ),
                        "dialogue": (
                            exam_rooms.PATIENT_RECORD_DIALOGUES_BY_SCENE[
                                scene
                            ].removesuffix("<Close>")
                        ),
                        "repeatable": True,
                    }
                    for scene in exam_rooms.SCENES
                },
            )
            self.assertEqual(
                set(exam_rooms.PATIENT_RECORD_DIALOGUE_IDS_BY_SCENE),
                set(exam_rooms.SCENES),
            )
            self.assertEqual(
                set(exam_rooms.PATIENT_RECORD_DIALOGUES_BY_SCENE),
                set(exam_rooms.SCENES),
            )
            self.assertEqual(
                len(
                    {
                        record["dialogue"]
                        for record in manifest_patient_records.values()
                    }
                ),
                len(exam_rooms.SCENES),
            )
            for scene, record in manifest_patient_records.items():
                with self.subTest(manifest_patient_record=scene):
                    self.assertEqual(record["dialogue"].count("<New>"), 1)
                    self.assertIn("PATIENT RECORD:", record["dialogue"])
                    self.assertNotIn("Fei", record["dialogue"])
                    self.assertNotIn("No patient record", record["dialogue"])

            post_keycard = manifest["post_keycard_dungeon"]
            self.assertEqual(
                post_keycard["entry_boundary"],
                {
                    "award_field": 550,
                    "credential_operand": campaign.SECURITY_KEYCARD_OPERAND,
                    "credential_bit_index": campaign.SECURITY_KEYCARD_BIT_INDEX,
                    "credential_mask": campaign.SECURITY_KEYCARD_MASK,
                    "intake_door_entities": [
                        campaign.INTAKE_PATIENT_DOOR_ENTITY,
                        campaign.INTAKE_FREIGHT_DOOR_ENTITY,
                        *campaign.INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES,
                    ],
                    "unlocked_destinations": [
                        list(campaign.INTAKE_PATIENT_DESTINATION),
                        list(campaign.INTAKE_FREIGHT_DESTINATION),
                        *(
                            list(destination)
                            for destination in campaign.INTAKE_EXAM_ROOM_DESTINATIONS
                        ),
                    ],
                    "policy": (
                        "the clinic security victory is the true dungeon "
                        "threshold; the patient-service route, Treatment "
                        "Preparation Room, and all three Intake "
                        "examination rooms require that credential"
                    ),
                },
            )
            service = post_keycard["service_manifold"]
            self.assertEqual(service["field"], 565)
            self.assertEqual(
                service["internal_passage"],
                {
                    "entity": 12,
                    "native_action_pc": base.FIELD565_TONE_GATE_ACTION_PC,
                    "requirement": "five-tone directional puzzle",
                    "input_sequence": ["Up", "Down", "Up", "Left", "Right"],
                    "award_operand": campaign.TONE_OPERAND,
                    "award_bit_index": campaign.TONE_BIT_INDEX,
                    "award_mask": campaign.TONE_MASK,
                    "leaf_helper_entity": 21,
                    "physical_seal_entity": 30,
                    "saved_state_1_door": True,
                },
            )
            self.assertEqual(
                service["future_lab_handoff"],
                {
                    "entity": campaign.FIELD565_FUTURE_LAB_HANDOFF_ENTITY,
                    "arrival_parameter": 3,
                    "destination": None,
                    "dialogue_id": (
                        campaign.SERVICE_FUTURE_LAB_HANDOFF_DIALOGUE_ID
                    ),
                    "dialogue": (
                        final_guidance.TEXT[565].removesuffix(
                            "<Close>"
                        )
                    ),
                    "policy": (
                        "solid and dialogue-only; no sound, leaf helper, "
                        "seal release, state write, or field transition"
                    ),
                },
            )
            self.assertEqual(
                service["quarantine_entry"],
                {
                    "entity": 10,
                    "requirement": "quarantine_keycard",
                    "credential_operand": campaign.QUARANTINE_KEYCARD_OPERAND,
                    "credential_bit_index": (
                        campaign.QUARANTINE_KEYCARD_BIT_INDEX
                    ),
                    "credential_mask": campaign.QUARANTINE_KEYCARD_MASK,
                    "destination": [620, 1],
                },
            )
            quarantine_exit = service["quarantine_exit"]
            self.assertEqual(quarantine_exit["status"], "active_diagnostic_gate")
            self.assertEqual(quarantine_exit["required_local_value"], 0x70)
            self.assertEqual(quarantine_exit["awards"], "quarantine_complete")
            self.assertEqual(quarantine_exit["destination"], [565, 6])
            self.assertTrue(quarantine_exit["animates_leaf"])
            self.assertEqual(
                service["stabilization_routes"],
                [
                    {"entity": 5, "destination": [590, 0]},
                    {
                        "entity": 6,
                        "destination": [590, 1],
                        "saved_state_1_panel": True,
                    },
                ],
            )
            self.assertEqual(
                service["wide_outer_action_targets"],
                {
                    "entities": list(range(4, 11)),
                    "half_extent_script_units": 0x18,
                    "bounce_safe_arrivals": {
                        str(parameter): list(position)
                        for parameter, (position, _triangle) in {
                            0: ((33, -33), 75),
                            1: ((4813, -3671), 8),
                            2: ((4190, -3044), 12),
                            3: ((3570, -2430), 17),
                            4: ((1152, -4468), 57),
                            5: ((2970, -4520), 64),
                            6: ((3270, -5718), 68),
                        }.items()
                    },
                },
            )
            self.assertEqual(
                post_keycard["quarantine_keycard_terminal"],
                {
                    "field": 593,
                    "npc_entities": [],
                    "retired_npc_entities": [
                        exam_rooms.PATIENT_ENTITY, exam_rooms.DOCTOR_ENTITY,
                    ],
                    "independent_room": True,
                    "entry": [593, 0],
                    "intake_origin": [621, 9],
                    "return": [621, 9],
                    "entity": exam_rooms.TERMINAL_ENTITY,
                    "entities": list(exam_rooms.TERMINAL_ENTITIES),
                    "position": list(exam_rooms.TERMINAL_POSITION),
                    "positions": [
                        list(position)
                        for position in exam_rooms.TERMINAL_POSITIONS
                    ],
                    "model_index": exam_rooms.MEDICAL_TERMINAL_MODEL_INDEX,
                    "interaction": {
                        "half_extents_script_units": [0x01, 0x0F],
                        "effective_half_reach_world_units": [18, 46],
                        "requires_facing": True,
                    },
                    "room_style": (
                        "bright Solaris examination room with a bed and an "
                        "illuminated clinical terminal"
                    ),
                    "entrance_requirements": ["security_keycard"],
                    "credential_operand": campaign.QUARANTINE_KEYCARD_OPERAND,
                    "credential_bit_index": (
                        campaign.QUARANTINE_KEYCARD_BIT_INDEX
                    ),
                    "credential_mask": campaign.QUARANTINE_KEYCARD_MASK,
                    "dialogue_ids": list(
                        exam_rooms.TERMINAL_DIALOGUE_IDS_BY_SCENE[593]
                    ),
                    "patient_record_dialogue_id": (
                        exam_rooms.PATIENT_RECORD_DIALOGUE_IDS_BY_SCENE[593]
                    ),
                    "patient_record": (
                        exam_rooms.PATIENT_RECORD_DIALOGUES_BY_SCENE[593]
                        .removesuffix("<Close>")
                    ),
                    "receipt_sound_id": exam_rooms.ITEM_ACQUISITION_SOUND_ID,
                    "policy": (
                        "the card remains visibly seated until the player accepts "
                        "it; Leave grants nothing and keeps the prompt repeatable, "
                        "while Accept plays the receipt sound, commits the persistent "
                        "credential, and makes later interactions display the "
                        "stored shelled demihuman diagnostic record; the room's "
                        "patient and doctor remain retired in every script slot"
                    ),
                },
            )
            self.assertEqual(
                post_keycard["interface_scanner_annex"],
                {
                    "field": 588,
                    "independent_room": True,
                    "entry": [588, 0],
                    "service_origin": [565, 5],
                    "return": [565, 5],
                    "entity": donor588.CONSOLE_ENTITY,
                    "visible_static_nodes": list(
                        donor588.CAMPAIGN_VISIBLE_SCANNER_STATIC_NODES
                    ),
                    "donor_story_and_loot_retired": True,
                    "position": [
                        campaign.INTERFACE_CONSOLE.x,
                        campaign.INTERFACE_CONSOLE.z,
                    ],
                    "room_style": "bright Soylent diagnostic scanner lab",
                    "entrance_requirements": [],
                    "awards": "interface_cutoff_armed",
                    "credential_award": None,
                    "policy": (
                        "the restored Service-Manifold annex arms only the "
                        "interface cutoff; it never issues a keycard"
                    ),
                },
            )
            ward = post_keycard["clinical_stabilization_ward"]
            self.assertEqual(ward["field"], stabilization590.SCENE)
            self.assertEqual(
                ward["production_bulkhead"],
                {
                    "entity": reserved_donor567.RESTRICTED_CONTROLLER,
                    "requirements": [
                        "security_keycard",
                        "tone_authorized",
                        "quarantine_complete",
                        "interface_cutoff_armed",
                    ],
                    "destination": [624, 0],
                },
            )
            self.assertEqual(
                ward["return_routes"],
                [
                    list(stabilization590.MANIFOLD_BULKHEAD_DESTINATION),
                    list(stabilization590.MANIFOLD_STAFF_DESTINATION),
                ],
            )

            resonance = post_keycard["organic_resonance"]
            self.assertEqual(
                {
                    key: resonance[key]
                    for key in (
                        "field",
                        "entity",
                        "native_action_pc",
                        "native_tone_order",
                        "receipt_dialogue_id",
                        "receipt_sound_id",
                        "clue_seen_operand",
                        "clue_seen_bit_index",
                        "clue_seen_mask",
                    )
                },
                {
                    "field": 589,
                    "entity": campaign.RESONANCE_CLUE_ENTITY,
                    "native_action_pc": campaign.RESONANCE_CLUE_ACTION_PC,
                    "native_tone_order": ["Up", "Down", "Up", "Left", "Right"],
                    "receipt_dialogue_id": (
                        campaign.RESONANCE_CLUE_RECEIPT_DIALOGUE_ID
                    ),
                    "receipt_sound_id": campaign.PROGRESSION_CONFIRM_SOUND_ID,
                    "clue_seen_operand": campaign.TONE_OPERAND,
                    "clue_seen_bit_index": campaign.RESONANCE_CLUE_BIT_INDEX,
                    "clue_seen_mask": campaign.RESONANCE_CLUE_BIT_MASK,
                },
            )
            self.assertIn("only field 565", resonance["policy"])
            self.assertEqual(
                post_keycard["ordered_back_half"],
                [
                    {
                        "field": stabilization590.SCENE,
                        "objective": (
                            "present all four authorizations at the recovered "
                            "clinical production bulkhead"
                        ),
                    },
                    {
                        "field": 624,
                        "objective": "divert all three living-material feeds",
                        "receipt_dialogue_id": 5,
                        "receipt_sound_id": campaign.PROGRESSION_CONFIRM_SOUND_ID,
                        "awards": "sorter_complete",
                    },
                    {
                        "field": 626,
                        "objective": (
                            "disable fusion and pattern while retaining containment"
                        ),
                        "receipt_dialogue_id": 5,
                        "receipt_sound_id": campaign.PROGRESSION_CONFIRM_SOUND_ID,
                        "awards": "m_core_safe",
                    },
                    {
                        "field": 625,
                        "objective": (
                            "witness the people within Meld and hear the party response"
                        ),
                        "awards": "meld_witnessed",
                    },
                    {
                        "field": 622,
                        "objective": "defeat the Sufal Mass and secure this node",
                        "awards": "facility_secured",
                    },
                ],
            )
            finale = post_keycard["finale"]
            self.assertEqual(
                {
                    "field": finale["field"],
                    "battle_configuration": finale["battle_configuration"],
                    "progression_sound_id": finale["progression_sound_id"],
                    "pending": finale["pending"],
                    "secured": finale["secured"],
                },
                {
                    "field": 622,
                    "battle_configuration": 9,
                    "progression_sound_id": campaign.PROGRESSION_CONFIRM_SOUND_ID,
                    "pending": {
                        "operand": campaign.STATE_OPERAND,
                        "bit_index": campaign.FINALE_EPILOGUE_PENDING_BIT_INDEX,
                        "mask": campaign.FINALE_EPILOGUE_PENDING_BIT_MASK,
                        "timing": "set immediately after FE7F battle synchronization",
                    },
                    "secured": {
                        "operand": campaign.STATE_OPERAND,
                        "bit_index": campaign.SECURED_BIT_INDEX,
                        "mask": campaign.SECURED_BIT_MASK,
                        "timing": "set only after the epilogue receipt closes",
                    },
                },
            )
            self.assertIn("without replaying Sufal", finale["recovery"])
            self.assertIn("keep the dungeon explorable", finale["completion"])
            self.assertEqual(
                checkin["survivor_movement"],
                {
                    "version": 198,
                    "field": 621,
                    "entities": sorted(campaign.INTAKE_WANDERING_SURVIVOR_SPECS),
                    "random_walk_opcode": "59 00",
                    "bounding_zone_opcode": "17 <four signed X/Z corners> FF",
                    "movement_zones": [
                        {
                            "entity": entity,
                            "start": list(
                                campaign.INTAKE_WANDERING_SURVIVOR_SPECS[entity][3]
                            ),
                            "corners": [list(point) for point in zone],
                            "opcode": (
                                campaign._intake_survivor_movement_zone_body(zone)
                                .hex(" ")
                                .upper()
                            ),
                        }
                        for entity, zone in sorted(
                            campaign.INTAKE_SURVIVOR_MOVEMENT_ZONES.items()
                        )
                    ],
                    "collision_radius": 16,
                    "walkmesh_halo": 24,
                    "minimum_zone_separation": 50,
                    "center_aisle": [824, 946],
                    "minimum_doctor_clearance": 80,
                    "archive_door_position": list(
                        campaign.INTAKE_ARCHIVE_DOOR_POSITION
                    ),
                    "archive_door_clearance": 162,
                    "archive_door_clearance_after_halo": 138,
                    "relocated_starts": [
                        {
                            "entity": entity,
                            "retail_position": list(retail_position),
                            "bounded_position": list(bounded_position),
                        }
                        for entity, (
                            _init_pc,
                            _graphic,
                            retail_position,
                            bounded_position,
                        ) in sorted(campaign.INTAKE_WANDERING_SURVIVOR_SPECS.items())
                        if retail_position != bounded_position
                    ],
                    "policy": (
                        "retain native random walking in nine disjoint clockwise "
                        "microzones whose 24-unit halos remain on the walkmesh; "
                        "keep every pair collision-separated and leave the "
                        "central player/physician aisle open"
                    ),
                },
            )
            self.assertEqual(
                checkin["terminal"],
                {
                    "field": 549,
                    "entity": campaign.ARCHIVE_TERMINAL_ENTITY,
                    "action_pc": campaign.ARCHIVE_CHECKIN_ACTION_PC,
                    "retained_screen_source_action_pc": (
                        campaign.ARCHIVE_TERMINAL_RETAIL_ACTION_PC
                    ),
                    "binary_archive_menu_reachable": False,
                    "native_panel_entities": list(
                        campaign.ARCHIVE_TERMINAL_SCREEN_ENTITIES
                    ),
                    "native_screen_open_script": (
                        campaign.ARCHIVE_TERMINAL_SCREEN_OPEN_SCRIPT
                    ),
                    "native_screen_open_pcs": list(
                        campaign.ARCHIVE_TERMINAL_SCREEN_OPEN_PCS
                    ),
                    "native_screen_close_script": (
                        campaign.ARCHIVE_TERMINAL_SCREEN_CLOSE_SCRIPT
                    ),
                    "native_screen_close_pcs": list(
                        campaign.ARCHIVE_TERMINAL_SCREEN_CLOSE_PCS
                    ),
                    "screen_policy": (
                        "run the retained six-panel opening before every "
                        "check-in interaction and launch the retained native "
                        "close after every custom registration or vitals path; "
                        "the unrelated retail binary-code menu is unreachable"
                    ),
                },
            )
            self.assertEqual(
                checkin["registration"],
                {
                    "aliases": list(campaign.CHECKIN_ALIASES),
                    "real_name_offered": False,
                    "completion_operand": campaign.STATE_OPERAND,
                    "completion_bit_index": campaign.CHECKIN_BIT_INDEX,
                    "completion_mask": campaign.CHECKIN_BIT_MASK,
                    "cancel_sets_completion": False,
                },
            )
            doctor = checkin["appointment"]["doctor"]
            self.assertEqual(
                {
                    "instruction": doctor["instruction"],
                    "follow_destination": doctor["follow_destination"],
                    "follow_door_open_variable": doctor[
                        "follow_door_open_variable"
                    ],
                    "follow_door_policy": doctor["follow_door_policy"],
                },
                {
                    "instruction": "Follow me into the examination room.",
                    "follow_destination": list(
                        campaign.INTAKE_CLINIC_DESTINATION
                    ),
                    "follow_door_open_variable": (
                        campaign.INTAKE_DOCTOR_DOOR_OPEN_VARIABLE
                    ),
                    "follow_door_policy": (
                        "the physician leaves the native lobby leaf at its "
                        "fully open endpoint and the live entered-phase "
                        "action transitions directly without closing or "
                        "replaying the opening animation; a true field "
                        "reload clears the local flag and safely falls "
                        "back to the native opening action"
                    ),
                },
            )
            self.assertEqual(
                doctor["collision"],
                {
                    "version": 199,
                    "bounding_volume_opcode": "18 10 10 00 00",
                    "runtime_half_extents": [32, 32],
                    "retained_collision_radius": 16,
                    "transit_flags_opcode": "20 01 80",
                    "stationary_flags_opcode": "20 0C 80",
                    "policy": (
                        "ghosted while hidden or following a scripted doorway "
                        "route; solid and immovable after reaching reception "
                        "and on a called-phase field reload"
                    ),
                },
            )
            self.assertEqual(
                checkin["appointment"]["office"]["exit_gate_scheduler"],
                {
                    "version": 212,
                    "opcodes_per_entity_slice": 8,
                    "doctor_scratch_operand": (
                        campaign.APPOINTMENT_SCRATCH_VARIABLE
                    ),
                    "exit_scratch_operand": (
                        campaign.CLINIC_EXIT_SCRATCH_VARIABLE
                    ),
                    "policy": (
                        "the exit retains its phase/stage snapshot in a private "
                        "field-local word across scheduler frames; the lower-ID "
                        "doctor update cannot clobber it"
                    ),
                },
            )
            self.assertEqual(
                checkin["appointment"]["office"]["doorway_traversal"],
                {
                    "version": 200,
                    "walkmesh_size": 1_948,
                    "walkmesh_sha256": (
                        "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d8cca4238393571df"
                    ),
                    "exterior_triangles": [34, 35],
                    "exterior_material": 0,
                    "exterior_material_flags": "0x00800000",
                    "actor_local_override": "0x0038",
                    "override_set_opcode": "F8 02 38 00",
                    "override_clear_opcode": "F8 06 38 00",
                    "security_clear_position": [0, 200],
                    "security_waypoint_max_steps": 16,
                    "doctor_threshold_max_steps": 16,
                    "policy": (
                        "the leaf opens completely before actor-local movement "
                        "permission is set; security clears it only on deep "
                        "interior floor, while the doctor crosses outside, "
                        "remains visible for the blocking close, hides, and then "
                        "clears it; Fei's solid seal and the global walkmesh "
                        "never change"
                    ),
                },
            )
            self.assertEqual(
                {
                    "doctor_entity": checkin["appointment"]["office"][
                        "doctor_entity"
                    ],
                    "doctor_collision_policy": checkin["appointment"]["office"][
                        "doctor_collision_policy"
                    ],
                },
                {
                    "doctor_entity": campaign.CLINIC_DOCTOR_ENTITY,
                    "doctor_collision_policy": (
                        "solid and immovable in every visible unresolved office "
                        "phase; ghosted while hidden and before the post-battle "
                        "escape route"
                    ),
                },
            )
            self.assertEqual(
                checkin["appointment"]["office"]["security_keycard"],
                {
                    "operand": campaign.SECURITY_KEYCARD_OPERAND,
                    "bit_index": campaign.SECURITY_KEYCARD_BIT_INDEX,
                    "mask": campaign.SECURITY_KEYCARD_MASK,
                    "dialogue_id": campaign.CLINIC_SECURITY_KEYCARD_DIALOGUE_ID,
                    "dialogue": (
                        campaign.CLINIC_SECURITY_KEYCARD_DIALOGUE.removesuffix(
                            "<Close>"
                        )
                    ),
                    "acquisition_sound_id": (
                        campaign.SECURITY_KEYCARD_ACQUIRED_SOUND_ID
                    ),
                    "timing": (
                        "after FE7F security victory synchronization; "
                        "sound and receipt precede the persistent bit"
                    ),
                    "unlocks": (
                        "field 621 e24 patient-service door, e26 "
                        "Treatment Preparation door, examination-room "
                        "doors e43/e44/e45, and the "
                        "recovered production-clearance chain"
                    ),
                },
            )
            records = checkin["patient_records"]
            self.assertEqual(set(records), {"Fei", "Elly", "Citan"})
            for patient in ("Fei", "Elly", "Citan"):
                with self.subTest(manifest_patient=patient):
                    profile = campaign.PATIENT_PROFILE_MEASUREMENTS[patient]
                    vitals = campaign.PATIENT_AUTHORED_VITALS[patient]
                    self.assertEqual(
                        records[patient],
                        {
                            "display_name": profile[0],
                            "age": profile[1],
                            "sex": profile[2],
                            "height_cm": profile[3],
                            "clean_status_weight_hundredths_lb": (
                                campaign.PATIENT_RETAIL_INITIAL_WEIGHT_HUNDREDTHS_LB[
                                    patient
                                ]
                            ),
                            "weight_character_id": (
                                campaign.PATIENT_CHARACTER_IDS[patient]
                            ),
                            "weight_dialogue_variables": list(
                                campaign.PATIENT_WEIGHT_DIALOG_VARIABLES
                            ),
                            "weight_read_and_convert_opcodes": (
                                campaign._read_character_weight_lbs(
                                    campaign.PATIENT_CHARACTER_IDS[patient],
                                ).hex(" ").upper()
                            ),
                            "pulse_bpm": vitals[0],
                            "blood_pressure": vitals[1],
                            "temperature_c": vitals[2],
                            "respiration_per_min": vitals[3],
                            "observation": vitals[4],
                        },
                    )
            self.assertIn(
                "EX69 reads the selected mutable live Status weight",
                checkin["weight_policy"],
            )
            self.assertIn("x2.20 convention", checkin["weight_policy"])
            self.assertIn("never writes weight with EX6B", checkin["weight_policy"])
            self.assertEqual(
                checkin["repeat_menu"],
                ["Fei", "Elly", "Citan", "Exit"],
            )
            self.assertEqual(
                checkin["terminal"]["retained_screen_source_action_pc"],
                campaign.ARCHIVE_TERMINAL_RETAIL_ACTION_PC,
            )
            dialogue_layout = manifest["dialogue_layout"]
            self.assertEqual(dialogue_layout["authored_blocks_audited"], 75)
            self.assertEqual(dialogue_layout["blocks_repaired"], 48)
            self.assertEqual(
                dialogue_layout["v178_overwidth_lines_repaired"],
                campaign.CAMPAIGN_V178_OVERFLOW_LINE_COUNT,
            )
            self.assertEqual(
                dialogue_layout["retail_dialogue_policy"],
                "byte-identical outside the audited ID set",
            )
            self.assertEqual(
                dialogue_layout["intake_waiting_area"],
                {
                    "field": 621,
                    "premise": (
                        "pre-revelation patients believe screening and treatment "
                        "will help them; no ambient adult knows the Soylent truth"
                    ),
                    "adult_dialogues": [
                        {
                            "entity": entity,
                            "dialogue_id": dialogue_id,
                            "text": campaign.INTAKE_WAITING_AREA_HOPEFUL_DIALOGUES[
                                dialogue_id
                            ].removesuffix("<Close>"),
                        }
                        for entity, (_action_pc, dialogue_id) in sorted(
                            campaign.INTAKE_NATIVE_DIALOGUE_ACTIONS.items()
                        )
                        if entity != campaign.INTAKE_BOY_ENTITY
                    ],
                },
            )
            self.assertEqual(
                dialogue_layout["intake_boy"],
                {
                    "field": 621,
                    "entity": campaign.INTAKE_BOY_ENTITY,
                    "dialogue_id": campaign.INTAKE_BOY_DIALOGUE_ID,
                    "text": "I like turtles!",
                },
            )
            self.assertEqual(len(manifest["door_animations"]), 4)
            north_animation = manifest["door_animations"][0]
            self.assertEqual(
                {
                    "id": north_animation["id"],
                    "field": north_animation["field"],
                    "controller_entity": north_animation["controller_entity"],
                    "physical_seal_entity": north_animation[
                        "physical_seal_entity"
                    ],
                    "destination": north_animation["destination"],
                    "model_indices": north_animation["model_indices"],
                    "source_helper_entities": north_animation[
                        "source_helper_entities"
                    ],
                    "helper_entities": north_animation["helper_entities"],
                    "closed_plane": north_animation["closed_plane"],
                    "header_translation": north_animation[
                        "header_translation"
                    ],
                    "header_rotation": north_animation["header_rotation"],
                    "facing_correction": north_animation["facing_correction"],
                    "closed_world_aabbs": north_animation[
                        "closed_world_aabbs"
                    ],
                    "slide_per_frame": north_animation["slide_per_frame"],
                    "frames": north_animation["frames"],
                    "sound_effect_id": north_animation["sound_effect_id"],
                    "graphics_or_model_bytes_changed": north_animation[
                        "graphics_or_model_bytes_changed"
                    ],
                },
                {
                    "id": "transfer_intake.transfer",
                    "field": 623,
                    "controller_entity": 37,
                    "physical_seal_entity": 43,
                    "destination": [621, 6],
                    "model_indices": [10, 11],
                    "source_helper_entities": [39, 40],
                    "helper_entities": [41, 42],
                    "closed_plane": [0, 1259],
                    "header_translation": [0, 0, 377],
                    "header_rotation": [0, 0x0800, 0],
                    "facing_correction": (
                        "half-turn reverses the source south-threshold winding "
                        "for the north-side approach"
                    ),
                    "closed_world_aabbs": [
                        [[-88, 0], [-132, 0], [1259, 1259]],
                        [[0, 88], [-132, 0], [1259, 1259]],
                    ],
                    "slide_per_frame": [[-2, 0], [2, 0]],
                    "frames": 32,
                    "sound_effect_id": 0x77,
                    "graphics_or_model_bytes_changed": False,
                },
            )
            self.assertIn("same-field paired blue leaves", north_animation["asset"])
            for (
                index,
                animation,
                controller,
                helper,
                threshold_entity,
                threshold_placement,
                placement,
                return_parameter,
            ) in zip(
                ("a", "b", "c"),
                manifest["door_animations"][1:],
                campaign.INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES,
                campaign.INTAKE_EXAM_ROOM_HELPER_ENTITIES,
                campaign.INTAKE_EXAM_ROOM_THRESHOLD_HEADER_ENTITIES,
                campaign.INTAKE_EXAM_ROOM_THRESHOLD_PLACEMENTS,
                campaign.INTAKE_EXAM_ROOM_MODEL_PLACEMENTS,
                campaign.INTAKE_EXAM_ROOM_ENTRY_PARAMETERS,
                strict=True,
            ):
                with self.subTest(manifest_exam_door=index):
                    self.assertEqual(
                        animation,
                        {
                            "id": f"intake_exam_{index}",
                            "field": 621,
                            "controller_entity": controller,
                            "helper_entity": helper,
                            "physical_seal_entity": None,
                            "destination": [
                                campaign.INTAKE_EXAM_ROOM_DESTINATIONS[
                                    ord(index) - ord("a")
                                ][0],
                                0,
                            ],
                            "return_parameter": return_parameter,
                            "asset": (
                                "existing field-621 Solaris single-leaf panel "
                                "model"
                            ),
                            "model_index": placement[0],
                            "header_translation": list(placement[2:5]),
                            "header_rotation": [0, placement[1], 0],
                            "threshold_header_entity": threshold_entity,
                            "threshold_model_index": (
                                campaign.INTAKE_EXAM_ROOM_THRESHOLD_MODEL_INDEX
                            ),
                            "threshold_placement": list(threshold_placement),
                            "slide_per_frame": list(placement[5:7]),
                            "frames": campaign.INTAKE_EXAM_ROOM_SLIDE_FRAMES,
                            "sound_effect_id": campaign.INTAKE_EXAM_ROOM_SOUND_ID,
                            "closed_barrier": (
                                "the retained outer-wall walkmesh boundary; no "
                                "invisible collision-only seal is required"
                            ),
                            "graphics_or_model_bytes_changed": True,
                        },
                    )
            collision = manifest["door_collision"]
            self.assertEqual(collision["blueprint_endpoints_split"], 40)
            self.assertEqual(collision["native_surface_endpoints_split"], 19)
            self.assertEqual(collision["donor_blueprint_endpoints_split"], 18)
            self.assertEqual(collision["field565_internal_gates_split"], 2)
            self.assertEqual(
                collision["field565_sealed_future_handoffs_split"],
                1,
            )
            self.assertEqual(collision["total_split_thresholds"], 43)
            self.assertEqual(
                collision["intake_exam_outer_wall_barriers"],
                {
                    "count": 3,
                    "controller_entities": list(
                        campaign.INTAKE_EXAM_ROOM_CONTROLLER_ENTITIES
                    ),
                    "policy": (
                        "the three new exterior panels sit directly on the "
                        "retained Intake walkmesh boundary; that wall blocks "
                        "Fei until the animated X action changes fields"
                    ),
                },
            )
            self.assertEqual(
                collision["donor_physical_seal"][
                    "external_effective_player_contact_radius"
                ],
                44,
            )
            archive_override = collision["donor_physical_seal"][
                "archive_return_override"
            ]
            self.assertEqual(
                archive_override,
                {
                    "field": 549,
                    "controller_entity": 6,
                    "physical_seal_entity": 16,
                    "shape": "rotation-invariant circle",
                    "center": [-244, 248],
                    "action_center": [-240, 240],
                    "radius_script_units": 0x08,
                    "radius_world_units": 16,
                    "effective_player_contact_radius": 32,
                    "saved_fixed_position": [-12_702_524, 0, 16_007_409],
                    "saved_world_position": [
                        -193.82513427734375,
                        0.0,
                        244.25367736816406,
                    ],
                    "saved_triangle": 10,
                    "round_trip_saved_fixed_position": [
                        -13_485_612,
                        0,
                        15_269_605,
                    ],
                    "round_trip_saved_world_position": [
                        -205.77410888671875,
                        0.0,
                        232.9956817626953,
                    ],
                    "round_trip_saved_triangle": 10,
                    "round_trip_saved_yaw": 0x0600,
                    "southwest_ray_clearance_world_units": 5.639441995778888,
                    "closed_cut_triangles": [6, 10, 11, 12, 13],
                    "diagonal_seam_intersection_margins_world_units": [
                        12.48625560742041,
                        15.741379398790173,
                    ],
                    "x_button": {
                        "required": True,
                        "automatic_proximity_action": False,
                        "carrier_entity": 6,
                        "script": 2,
                        "action_half_extents_script_units": [0x0A, 0x0C],
                        "effective_cross_half_extents_world_units": [36, 40],
                    },
                    "policy": (
                        "the shifted physical circle stays inside the unchanged "
                        "deliberate-X shell, clears the exact southwest corridor "
                        "ray, and intersects both diagonal aperture seams while "
                        "closed; Forward alone cannot open it"
                    ),
                },
            )
            exam_return_override = collision["donor_physical_seal"][
                "exam_room_return_override"
            ]
            self.assertEqual(
                exam_return_override,
                {
                    "scenes": list(campaign.FIELD352_X_ONLY_SCENES),
                    "shape": "axis-aligned z-normal thin rectangle",
                    "center": [0, 266],
                    "half_extents_script_units": [0x18, 0x08],
                    "physical_collision_extra_radius": 0,
                    "physical_collision_half_extents_world_units": [48, 16],
                    "contact_planes_z": {"inner": 250, "outer": 282},
                    "x_button": {
                        "required": True,
                        "automatic_proximity_action": False,
                        "carrier_entity": exam_rooms.RETURN_CONTROLLER,
                        "script": 2,
                        "action_half_extents_script_units": [0x18, 0x10],
                        "start_scripts_extra_radius": 0x10,
                        "effective_cross_half_extents_world_units": [64, 48],
                    },
                    "retired_automatic_cavity": {
                        "owner_entity": 14,
                        "former_script": 5,
                        "span": ["0x044E", "0x04A5"],
                        "byte_identical_scenes": [550],
                        "side_terminal_carrier_scenes": list(
                            campaign.FIELD352_SIDE_TERMINAL_SCENES
                        ),
                        "side_terminal_init_entry_points": [
                            {
                                "entity": entity,
                                "script": 0,
                                "pc": f"0x{pc:04X}",
                            }
                            for entity, pc in zip(
                                exam_rooms.TERMINAL_AUX_ENTITIES,
                                exam_rooms.TERMINAL_AUX_INIT_PCS,
                                strict=True,
                            )
                        ],
                        "empty_room_third_carrier": {
                            "entity": (
                                exam_rooms.EMPTY_ROOM_TERMINAL_ENTITIES[2]
                            ),
                            "script": 0,
                            "pc": (
                                f"0x{exam_rooms.EMPTY_ROOM_TERMINAL_INIT_PC:04X}"
                            ),
                        },
                        "other_active_entry_points": 0,
                        "global_update": {
                            "entity": 0,
                            "script": 1,
                            "pc": "0x068C",
                        },
                    },
                    "retail_walkmesh": {
                        "source_field": empty_clinic567.SOURCE_SCENE,
                        "component_index": 1,
                        "byte_identical": True,
                        "size": 1_948,
                        "sha256": (
                            "abea233198e3a4430536a2e736d39c7a86bc1eb27da44a8d8cca4238393571df"
                        ),
                    },
                },
            )
            for scene in campaign.FIELD352_X_ONLY_SCENES:
                with self.subTest(manifest_exam_walkmesh=scene):
                    self.assertEqual(
                        (
                            len(self.donor_by_scene[scene].components[1]),
                            _sha256(self.donor_by_scene[scene].components[1]),
                        ),
                        (
                            exam_return_override["retail_walkmesh"]["size"],
                            exam_return_override["retail_walkmesh"]["sha256"],
                        ),
                    )
            self.assertEqual(
                collision["donor_physical_seal"][
                    "internal_gate_effective_player_contact_radius"
                ],
                52,
            )
            self.assertIn(
                "success-only",
                collision["donor_physical_seal"]["release"],
            )
            prepared_donors = {
                item["field"]: item for item in manifest["donors_prepared"]
            }
            self.assertEqual(len(prepared_donors), 11)
            self.assertEqual(
                prepared_donors[567]["target_ids"],
                list(empty_clinic567.EMPTY_CLINIC567_TARGET_IDS),
            )
            self.assertEqual(
                prepared_donors[stabilization590.SCENE]["target_ids"],
                list(stabilization590.TARGET_IDS),
            )
            for scene in exam_rooms.SCENES:
                with self.subTest(manifest_prepared_exam_room=scene):
                    self.assertEqual(
                        prepared_donors[scene]["target_ids"],
                        list(exam_rooms.TARGET_IDS_BY_SCENE[scene]),
                    )
            room_metadata = manifest["unassigned_medical_examination_room"]
            self.assertEqual(
                (
                    room_metadata["field"],
                    room_metadata["name"],
                    room_metadata["source_disc_field"],
                    room_metadata["target_resources"],
                    room_metadata["source_resources"],
                ),
                (
                    567,
                    "Unassigned Medical Examination Room",
                    empty_clinic567.SOURCE_SCENE,
                    list(empty_clinic567.EMPTY_CLINIC567_TARGET_IDS),
                    list(empty_clinic567.EMPTY_CLINIC567_SOURCE_IDS),
                ),
            )
            self.assertEqual(
                room_metadata["bed"],
                {
                    "source_model_index": empty_clinic567.BED_MODEL_INDEX,
                    "source_header_node": empty_clinic567.BED_HEADER_NODE,
                    "installed_header_node": (
                        empty_clinic567.BED_HEADER_NODE
                        + len(campaign.DONOR_DOOR_COLLISION_CONTRACTS[567])
                    ),
                    "model_identity": list(empty_clinic567.BED_MODEL_IDENTITY),
                    "preserved": True,
                },
            )
            self.assertEqual(
                room_metadata["route"],
                {
                    "controller_entity": empty_clinic567.RETURN_CONTROLLER,
                    "leaf_helper_entity": empty_clinic567.RETURN_HELPER,
                    "destination": [621, 4],
                },
            )
            self.assertEqual(
                room_metadata["terminal"],
                {
                    "entities": list(
                        exam_rooms.EMPTY_ROOM_TERMINAL_ENTITIES
                    ),
                    "init_pcs": list(
                        exam_rooms.EMPTY_ROOM_TERMINAL_INIT_PCS
                    ),
                    "positions": [
                        list(position)
                        for position in exam_rooms.TERMINAL_POSITIONS
                    ],
                    "triangles": list(exam_rooms.TERMINAL_TRIANGLES),
                    "operator_triangles": list(
                        exam_rooms.TERMINAL_OPERATOR_TRIANGLES
                    ),
                    "action_pc": (
                        exam_rooms.EMPTY_ROOM_TERMINAL_ACTION_PC
                    ),
                    "dialogue_id": (
                        exam_rooms.EMPTY_ROOM_TERMINAL_DIALOGUE_ID
                    ),
                    "dialogue": exam_rooms.EMPTY_ROOM_TERMINAL_DIALOGUE,
                    "interaction": {
                        "half_width": (
                            exam_rooms.TERMINAL_INTERACTION_HALF_WIDTH
                        ),
                        "half_depth": (
                            exam_rooms.TERMINAL_INTERACTION_HALF_DEPTH
                        ),
                        "effective_half_reach": list(
                            exam_rooms.TERMINAL_EFFECTIVE_HALF_REACH
                        ),
                        "frontage_x": list(
                            exam_rooms.TERMINAL_FRONTAGE_X
                        ),
                        "requires_facing": (
                            exam_rooms.TERMINAL_REQUIRES_FACING
                        ),
                    },
                    "population": {"doctor": None, "patient": None},
                    "repeatable": True,
                    "read_only": True,
                    "writes_state": False,
                },
            )
            self.assertIn("exploration-only", room_metadata["behavior"])
            self.assertIn("no-patient", room_metadata["behavior"])
            self.assertIn("all retail NPC", room_metadata["behavior"])
            recovered = manifest["recovered_room_donors"][
                "clinical_stabilization_ward"
            ]
            self.assertEqual(
                recovered,
                {
                    "status": "recovered into the active dungeon",
                    "registry": (
                        "modules/soylent_system/content/reserved_room_donors.json"
                    ),
                    "module": (
                        "tools/surface_soylent_campaign_stabilization590.py"
                    ),
                    "field": stabilization590.SCENE,
                    "source_disc_field": reserved_donor567.SCENE,
                    "source_resources": list(reserved_donor567.DONOR567_SOURCE_IDS),
                    "target_resources": list(stabilization590.TARGET_IDS),
                    "routes": [
                        {
                            "controller_entity": reserved_donor567.LOBBY_CONTROLLER,
                            "destination": list(
                                stabilization590.MANIFOLD_BULKHEAD_DESTINATION
                            ),
                        },
                        {
                            "controller_entity": reserved_donor567.SERVICE_CONTROLLER,
                            "destination": list(
                                stabilization590.MANIFOLD_STAFF_DESTINATION
                            ),
                        },
                        {
                            "controller_entity": (
                                reserved_donor567.RESTRICTED_CONTROLLER
                            ),
                            "destination": list(
                                stabilization590.SORTING_DESTINATION
                            ),
                            "gate": "production_clearance",
                        },
                    ],
                },
            )
            self.assertIn(588, prepared_donors)
            self.assertNotIn("base_materialization", manifest)
            self.assertEqual(
                manifest["materialization"]["replacement_resources"],
                34,
            )
            self.assertEqual(len(manifest["replacement_inventory"]), 34)
            self.assertEqual(
                len({item["canonical_id"] for item in manifest["replacement_inventory"]}),
                34,
            )
            for item in manifest["replacement_inventory"]:
                path = output / item["path"]
                self.assertEqual(path.stat().st_size, item["size"])
                self.assertEqual(_sha256(path.read_bytes()), item["sha256"])
            for item in manifest["rooms_prepared"]:
                self.assertIsInstance(item["canonical_bundle_id"], int)
                self.assertIsInstance(item["canonical_graphics_id"], int)
            for item in manifest["rooms_prepared"] + manifest["donors_prepared"]:
                self.assertGreaterEqual(
                    item["header_actor_count"],
                    item["atel_entity_count"],
                )
            self.assertEqual(len(replacements), 7 + 11 * 2 + 5)
            self.assertEqual(len(fields), 7)
            self.assertEqual(len(donors), 11)


if __name__ == "__main__":
    unittest.main()
