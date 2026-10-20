from __future__ import annotations

import hashlib
import math
import struct
import unittest
from unittest import mock

import tools.build_surface_soylent_dungeon as surface
import tools.surface_soylent_campaign_empty_clinic567 as foundation
import tools.surface_soylent_campaign_exam_rooms as exam_rooms
from modules.soylent_system.tests.disc_fixtures import source_disc_path
from tools.xgdialog import parse_dialogue
from tools.xgencounter import EncounterTable
from tools.xgfield import parse_field
from tools.xgscript import AtelScript as ScriptEditor


DISC1 = source_disc_path("pw_disc1")
DISC2 = source_disc_path("pw_disc2")


def _identity(data: bytes) -> tuple[int, str]:
    return len(data), hashlib.sha256(data).hexdigest()


def _single_block_model_aabb(
    model: bytes,
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if len(model) < 0x48 or struct.unpack_from("<I", model)[0] != 1:
        raise AssertionError("terminal is not the audited single-block model")
    block = 0x10
    vertex_count = struct.unpack_from("<H", model, block + 2)[0]
    vertex_offset = struct.unpack_from("<I", model, block + 8)[0]
    vertices = tuple(
        struct.unpack_from("<hhh", model, vertex_offset + index * 8)
        for index in range(vertex_count)
    )
    return tuple(
        (
            min(vertex[axis] for vertex in vertices),
            max(vertex[axis] for vertex in vertices),
        )
        for axis in range(3)
    )


_REPEATABLE_TERMINAL_ACTION = bytes.fromhex(
    "33 FE 54 31 20 00 EE 06 26 01 80 01 E3 06 26 01 80 "
    "F5 35 00 01 9C 31 20 00 01 07 26 01 80 01 F6 06 "
    "26 01 80 FE 53 00"
)

# Independent decoder for the deliberately small vocabulary reachable from
# the examination rooms' active entry points.  In particular, this avoids
# treating dormant field-352 story bytecode (or an operand byte) as live code.
_ACTIVE_OPCODE_SIZES = {
    0x00: 1,  # STOP
    0x01: 3,  # JUMP
    0x02: 8,  # JUMP_IF
    0x07: 3,  # RUN_ENTITY_SCRIPT_ASYNC
    0x09: 3,  # RUN_ENTITY_SCRIPT_BLOCKING
    0x0B: 3,
    0x0C: 1,  # RETURN
    0x16: 3,
    0x18: 5,  # SET_BOUNDING_VOLUME
    0x19: 6,  # SET_ACTOR_POSITION_2D
    0x1A: 2,
    0x20: 3,  # SET_CURRENT_ACTOR_FLAGS
    0x23: 1,  # MAKE_INVISIBLE_ACTIVE
    0x26: 3,  # WAIT
    0x2A: 1,  # DISABLE_DIALOG_ACTIVATION
    0x2C: 2,  # PLAY_ANIMATION
    0x31: 5,  # JUMP_IF_PAD_MASK
    0x33: 1,  # RESET_ACCUMULATED_INPUT_MASK
    0x35: 6,  # SET/COPY_VARIABLE
    0x38: 6,  # ADD_VARIABLE
    0x39: 6,  # SUBTRACT_VARIABLE
    0x3A: 6,  # SET_VARBIT_TRUE
    0x3B: 6,  # SET_VARBIT_FALSE
    0x3C: 4,  # INCREMENT_VARIABLE
    0x3D: 4,  # DECREMENT_VARIABLE
    0x3E: 6,  # AND_VARIABLE
    0x42: 5,  # SHIFT_VARIABLE
    0x69: 3,  # SET_ACTOR_DIRECTION
    0x6F: 2,  # FACE_PLAYER
    0x74: 3,  # PLAY_SOUND
    0x8C: 3,  # ADD_ITEM_TO_INVENTORY
    0x98: 5,  # CHANGE_FIELD
    0x9C: 1,  # WAIT_DIALOG
    0xA0: 7,
    0xBC: 1,
    0xD2: 4,  # SHOW_ACTOR_DIALOG
    0xDE: 6,  # MULTIPLY_VARIABLE
    0xDF: 6,  # DIVIDE_VARIABLE
    0xF5: 4,  # SHOW_DIALOG
    0xF8: 4,
}
_ACTIVE_EXTENDED_OPCODE_SIZES = {
    0x0D: 4,
    0x17: 4,  # FACE_ACTOR_TO_ACTOR
    0x1B: 6,
    0x53: 2,  # RESTORE_FIELD_CONTROL
    0x54: 2,  # SUSPEND_FIELD_CONTROL
}
_VARIABLE_WRITE_OPCODES = frozenset(
    {0x35, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E, 0x42, 0xDE, 0xDF}
)


def _reachable_active_instructions(editor: ScriptEditor) -> dict[int, bytes]:
    active_slots = (
        foundation.FINAL_ACTIVE_SLOTS
        | {
            (entity, script_index)
            for entity in exam_rooms.TERMINAL_ENTITIES
            for script_index in (0, 2)
        }
        | {
            (exam_rooms.PATIENT_ENTITY, 0),
            (exam_rooms.PATIENT_ENTITY, 2),
            (exam_rooms.DOCTOR_ENTITY, 0),
            (exam_rooms.DOCTOR_ENTITY, 2),
        }
    )
    pending = [
        editor.get_script_pointer(entity, script_index)
        for entity, script_index in active_slots
    ]
    decoded: dict[int, bytes] = {}
    while pending:
        pc = pending.pop()
        while pc not in decoded:
            if not 0 <= pc < len(editor.bytecode):
                raise AssertionError(f"active PC is out of range: 0x{pc:04X}")
            opcode = editor.bytecode[pc]
            if opcode == 0xFE:
                extension = editor.bytecode[pc + 1]
                if extension not in _ACTIVE_EXTENDED_OPCODE_SIZES:
                    raise AssertionError(
                        f"unexpected active extension FE{extension:02X} "
                        f"at 0x{pc:04X}"
                    )
                size = _ACTIVE_EXTENDED_OPCODE_SIZES[extension]
            else:
                if opcode not in _ACTIVE_OPCODE_SIZES:
                    raise AssertionError(
                        f"unexpected active opcode {opcode:02X} at 0x{pc:04X}"
                    )
                size = _ACTIVE_OPCODE_SIZES[opcode]
            instruction = editor.bytecode[pc : pc + size]
            if len(instruction) != size:
                raise AssertionError(f"truncated active opcode at 0x{pc:04X}")
            decoded[pc] = instruction

            if opcode in (0x07, 0x09):
                entity, selector = instruction[1:3]
                pending.append(
                    editor.get_script_pointer(entity, selector & 0x1F)
                )
            if opcode == 0x01:
                pending.append(struct.unpack_from("<H", instruction, 1)[0])
                break
            if opcode == 0x02:
                pending.append(struct.unpack_from("<H", instruction, 6)[0])
            elif opcode == 0x31:
                pending.append(struct.unpack_from("<H", instruction, 3)[0])
            if opcode in (0x00, 0x0C, 0x98):
                break
            pc += size
    return decoded


class ExamRoomMetadataTests(unittest.TestCase):
    def test_four_independent_targets_and_returns_are_explicit(self) -> None:
        self.assertEqual(exam_rooms.SCENES, (591, 592, 593, 594))
        self.assertEqual(
            exam_rooms.TARGET_IDS_BY_SCENE,
            {
                591: (1788, 1789),
                592: (1790, 1791),
                593: (1792, 1793),
                594: (1794, 1795),
            },
        )
        self.assertEqual(
            exam_rooms.RETURN_PARAMETERS_BY_SCENE,
            {591: 7, 592: 8, 593: 9, 594: 5},
        )
        self.assertEqual(
            exam_rooms.DOOR_ENDPOINT_IDS_BY_SCENE,
            {
                591: "intake_exam_a.examination",
                592: "intake_exam_b.examination",
                593: "intake_exam_c.examination",
                594: "intake_treatment_preparation.treatment",
            },
        )
        for scene in exam_rooms.SCENES:
            with self.subTest(scene=scene):
                identity = exam_rooms.EXAM_ROOM_IDENTITIES[scene]
                self.assertEqual(identity.scene, scene)
                self.assertEqual(
                    (identity.bundle_id, identity.graphics_id),
                    exam_rooms.TARGET_IDS_BY_SCENE[scene],
                )
                self.assertEqual(
                    (identity.bundle_size, identity.bundle_sha256),
                    exam_rooms.SOURCE_BUNDLE_IDENTITY,
                )
                self.assertEqual(
                    (identity.graphics_size, identity.graphics_sha256),
                    exam_rooms.SOURCE_GRAPHICS_IDENTITY,
                )

    def test_all_rooms_share_the_verified_field352_clinic_source(self) -> None:
        self.assertEqual(exam_rooms.SOURCE_SCENE, 352)
        self.assertEqual(exam_rooms.SOURCE_IDS, (1315, 1316))
        self.assertEqual(
            exam_rooms.SOURCE_BUNDLE_IDENTITY,
            foundation.SOURCE_BUNDLE_IDENTITY,
        )
        self.assertEqual(
            exam_rooms.SOURCE_GRAPHICS_IDENTITY,
            foundation.SOURCE_GRAPHICS_IDENTITY,
        )
        self.assertEqual(exam_rooms.ENTRY_PARAMETER, 0)
        self.assertEqual(exam_rooms.ENTRY_POSITION, (0, 200))
        self.assertEqual(exam_rooms.ENTRY_TRIANGLE, 16)

    def test_terminal_and_keycard_contracts_are_frozen(self) -> None:
        self.assertEqual(exam_rooms.TERMINAL_ENTITY, 19)
        self.assertEqual(exam_rooms.TERMINAL_AUX_ENTITIES, (4, 5))
        self.assertEqual(exam_rooms.TERMINAL_ENTITIES, (19, 4, 5))
        self.assertEqual(
            exam_rooms.TERMINAL_POSITIONS,
            ((80, -167), (116, -167), (152, -167)),
        )
        self.assertEqual(exam_rooms.TERMINAL_TRIANGLES, (31, 6, 6))
        self.assertEqual(
            exam_rooms.TERMINAL_OPERATOR_TRIANGLES,
            (31, 30, 6, 7),
        )
        self.assertEqual(
            (
                exam_rooms.TERMINAL_INTERACTION_HALF_WIDTH,
                exam_rooms.TERMINAL_INTERACTION_HALF_DEPTH,
            ),
            (0x01, 0x0F),
        )
        self.assertTrue(exam_rooms.TERMINAL_REQUIRES_FACING)
        self.assertEqual(exam_rooms.TERMINAL_EFFECTIVE_HALF_REACH, (18, 46))
        self.assertEqual(exam_rooms.TERMINAL_FRONTAGE_X, (70, 164))
        self.assertEqual(
            (
                exam_rooms.TERMINAL_INIT_PC,
                exam_rooms.TERMINAL_ACTION_PC,
                exam_rooms.TERMINAL_AUX_INIT_PCS,
                exam_rooms.TERMINAL_AUX_CAVITY_END_PC,
            ),
            (0x06C3, 0x06E0, (0x044E, 0x046B), 0x04A5),
        )
        self.assertEqual(
            exam_rooms.TERMINAL_AUX_CAVITY_SOURCE_IDENTITY,
            (
                87,
                "85581a31b32134e75912714f1e71cbe0957721e289f114f954a98ed7c4ca8824",
            ),
        )
        self.assertEqual(
            (
                exam_rooms.MEDICAL_TERMINAL_MODEL_INDEX,
                exam_rooms.MEDICAL_TERMINAL_SOURCE_HEADER_NODE,
                exam_rooms.MEDICAL_TERMINAL_HEADER_NODE,
            ),
            (3, 22, 23),
        )
        self.assertEqual(exam_rooms.QUARANTINE_KEYCARD_OPERAND, 0x021A)
        self.assertEqual(exam_rooms.QUARANTINE_KEYCARD_BIT_INDEX, 8)
        self.assertEqual(exam_rooms.QUARANTINE_KEYCARD_MASK, 0x0100)
        self.assertEqual(exam_rooms.ITEM_ACQUISITION_SOUND_ID, 0x37)
        self.assertEqual(exam_rooms.ITEM_ACQUISITION_SOUND, b"\x74\x37\x80")
        self.assertEqual(
            exam_rooms.TERMINAL_ACTION_LENGTHS_BY_SCENE,
            {591: 39, 592: 39, 593: 101, 594: 39},
        )
        self.assertEqual(
            exam_rooms.TERMINAL_ACTION_SHA256_BY_SCENE,
            {
                591: "ffafd3a2127c0e5c894007224545e9325a4b65f0a06ce5be8fe2f84a28b9a85c",
                592: "ffafd3a2127c0e5c894007224545e9325a4b65f0a06ce5be8fe2f84a28b9a85c",
                593: "178e0251af24d952cb69071f49c15842f0f7d0963b0e8558db2c8760f1c944de",
                594: "ffafd3a2127c0e5c894007224545e9325a4b65f0a06ce5be8fe2f84a28b9a85c",
            },
        )
        self.assertFalse(exam_rooms.EXAM_ROOM_BY_SCENE[591].awards_quarantine_keycard)
        self.assertFalse(exam_rooms.EXAM_ROOM_BY_SCENE[592].awards_quarantine_keycard)
        self.assertTrue(exam_rooms.EXAM_ROOM_BY_SCENE[593].awards_quarantine_keycard)
        self.assertFalse(exam_rooms.EXAM_ROOM_BY_SCENE[594].awards_quarantine_keycard)

    def test_native_door_contract_matches_the_clinic_geometry(self) -> None:
        self.assertEqual(exam_rooms.RETURN_CONTROLLER, 17)
        self.assertEqual(exam_rooms.RETURN_HELPER, 18)
        self.assertEqual(exam_rooms.RETURN_ACTION_PC, 0x06B5)
        self.assertEqual(exam_rooms.RETURN_CONTROLLER_POSITION, (0, 250))
        self.assertEqual(exam_rooms.RETURN_CONTROLLER_TRIANGLE, 34)
        self.assertEqual(exam_rooms.RETURN_CONTROLLER_TRIANGLES, (16, 34, 35))
        self.assertEqual(exam_rooms.DOOR_CLOSED_SIDE_PROBE, (0, 200))
        self.assertEqual(exam_rooms.DOOR_OPEN_SIDE_PROBE, (0, 300))
        self.assertEqual(exam_rooms.DOOR_SEAL_RADIUS, 0x0E)
        for scene, parameter in exam_rooms.RETURN_PARAMETERS_BY_SCENE.items():
            with self.subTest(scene=scene):
                self.assertEqual(
                    exam_rooms.RETURN_ROUTES_BY_SCENE[scene],
                    (17, 0x06B5, 18, 4, 621, parameter),
                )
                self.assertIn(
                    surface._change_field(621, parameter),
                    exam_rooms.RETURN_ACTIONS_BY_SCENE[scene],
                )

    def test_dummy_guard_checks_all_eight_exact_targets(self) -> None:
        exact = {
            canonical_id: surface.DONOR_DUMMY
            for canonical_id in exam_rooms.TARGET_IDS
        }
        with mock.patch.object(
            exam_rooms.surface,
            "_load_canonical_resources",
            return_value=exact,
        ) as loader:
            exam_rooms.verify_exam_room_targets_are_dummy("disc2.bin")
        self.assertEqual(set(loader.call_args.args[1]), set(exam_rooms.TARGET_IDS))

        wrong = dict(exact)
        wrong[exam_rooms.TARGET_IDS[-1]] = b"not the checked dummy"
        with mock.patch.object(
            exam_rooms.surface,
            "_load_canonical_resources",
            return_value=wrong,
        ):
            with self.assertRaisesRegex(
                surface.SurfaceSoylentBuildError,
                "not checked CDMAKE dummies",
            ):
                exam_rooms.verify_exam_room_targets_are_dummy("disc2.bin")

    def test_unknown_scene_is_rejected_before_any_rebuild(self) -> None:
        with self.assertRaisesRegex(
            surface.SurfaceSoylentBuildError,
            "Unsupported examination-room scene",
        ):
            exam_rooms.prepare_exam_room(590, b"", b"", None)


@unittest.skipUnless(DISC1.is_file(), "Perfect Works Disc 1 is unavailable")
class EmptyRoomTerminalBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_bundle, cls.graphics = exam_rooms.load_exam_room_source(DISC1)
        cls.foundation = foundation.prepare_empty_clinic567(
            cls.source_bundle,
            cls.graphics,
        )
        cls.prepared = exam_rooms.prepare_empty_room_terminal(cls.foundation)

    def test_empty_room_terminal_output_is_deterministic_and_frozen(self) -> None:
        again = exam_rooms.prepare_empty_room_terminal(self.foundation)
        self.assertEqual(self.prepared, again)
        self.assertEqual(
            _identity(self.prepared.components[surface.SCRIPT_INDEX]),
            exam_rooms.EMPTY_ROOM_TERMINAL_SCRIPT_IDENTITY,
        )
        self.assertEqual(
            _identity(self.prepared.components[7]),
            exam_rooms.EMPTY_ROOM_TERMINAL_DIALOGUE_IDENTITY,
        )
        self.assertEqual(
            _identity(self.prepared.header),
            exam_rooms.EMPTY_ROOM_TERMINAL_HEADER_IDENTITY,
        )
        self.assertEqual(
            _identity(self.prepared.bundle),
            exam_rooms.EMPTY_ROOM_TERMINAL_BUNDLE_IDENTITY,
        )

    def test_terminal_reports_no_patient_without_adding_an_npc(self) -> None:
        parsed = parse_dialogue(self.prepared.components[7])
        self.assertEqual(
            len(parsed.blocks),
            exam_rooms.SOURCE_DIALOGUE_COUNT + 1,
        )
        self.assertEqual(
            parsed.blocks[exam_rooms.EMPTY_ROOM_TERMINAL_DIALOGUE_ID].text,
            exam_rooms.EMPTY_ROOM_TERMINAL_DIALOGUE,
        )
        self.assertIn("No patient is loaded", exam_rooms.EMPTY_ROOM_TERMINAL_DIALOGUE)

        editor = ScriptEditor(self.prepared.components[surface.SCRIPT_INDEX])
        self.assertEqual(editor.entity_count, exam_rooms.SOURCE_ENTITY_COUNT)
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
        for entity in foundation.RETIRED_NPC_ENTITIES:
            for script_index in range(32):
                self.assertEqual(
                    editor.get_script_pointer(entity, script_index),
                    foundation.SHARED_STOP_PC,
                )

    def test_empty_terminal_is_read_only_and_preserves_the_native_exit(self) -> None:
        editor = ScriptEditor(self.prepared.components[surface.SCRIPT_INDEX])
        action = editor.bytecode[
            exam_rooms.EMPTY_ROOM_TERMINAL_ACTION_PC :
            exam_rooms.EMPTY_ROOM_TERMINAL_ACTION_PC
            + exam_rooms.EMPTY_ROOM_TERMINAL_ACTION_IDENTITY[0]
        ]
        self.assertEqual(
            _identity(action),
            exam_rooms.EMPTY_ROOM_TERMINAL_ACTION_IDENTITY,
        )
        self.assertIn(
            b"\xF5"
            + struct.pack("<H", exam_rooms.EMPTY_ROOM_TERMINAL_DIALOGUE_ID)
            + b"\x01\x9C",
            action,
        )
        self.assertNotIn(exam_rooms.ITEM_ACQUISITION_SOUND, action)
        self.assertNotIn(b"\x3A", action)
        self.assertNotIn(b"\x98", action)
        self.assertEqual(
            editor.get_script_pointer(foundation.RETURN_CONTROLLER, 2),
            foundation.RETURN_CONTROLLER_ACTION_PC,
        )
        self.assertEqual(
            editor.bytecode[
                foundation.RETURN_CONTROLLER_ACTION_PC :
                foundation.RETURN_CONTROLLER_ACTION_PC
                + len(foundation.RETURN_ACTION)
            ],
            foundation.RETURN_ACTION,
        )

    def test_only_script_and_dialogue_components_change(self) -> None:
        for index, before in enumerate(self.foundation.components):
            with self.subTest(component=index):
                if index in (surface.SCRIPT_INDEX, 7):
                    self.assertNotEqual(self.prepared.components[index], before)
                else:
                    self.assertEqual(self.prepared.components[index], before)
        source_actor_count = struct.unpack_from(
            "<H", self.foundation.header, 0x18C
        )[0]
        actor_count = struct.unpack_from("<H", self.prepared.header, 0x18C)[0]
        self.assertEqual(actor_count, source_actor_count)
        self.assertEqual(
            self.prepared.header[0x190:],
            self.foundation.header[0x190:],
        )

    def test_users_saved_field567_workstation_stance_is_covered(self) -> None:
        saved_position = (72.25076294, -141.23121643)
        saved_yaw = 0x0200
        self.assertTrue(
            any(
                exam_rooms._terminal_in_reach(saved_position, position)
                and exam_rooms._terminal_facing_accepts(
                    saved_position,
                    position,
                    saved_yaw,
                )
                for position in exam_rooms.TERMINAL_POSITIONS
            )
        )

    def test_empty_room_uses_the_exact_narrow_facing_bank_carriers(self) -> None:
        editor = ScriptEditor(self.prepared.components[surface.SCRIPT_INDEX])
        self.assertEqual(
            _identity(exam_rooms.EMPTY_ROOM_TERMINAL_AUX_CAVITY),
            exam_rooms.EMPTY_ROOM_TERMINAL_AUX_CAVITY_IDENTITY,
        )
        self.assertNotEqual(
            exam_rooms.EMPTY_ROOM_TERMINAL_AUX_CAVITY,
            exam_rooms.TERMINAL_AUX_CAVITY,
        )
        for entity, pc, body in zip(
            exam_rooms.EMPTY_ROOM_TERMINAL_ENTITIES,
            exam_rooms.EMPTY_ROOM_TERMINAL_INIT_PCS,
            exam_rooms.TERMINAL_INIT_BODIES,
            strict=True,
        ):
            with self.subTest(entity=entity):
                self.assertEqual(editor.bytecode[pc : pc + len(body)], body)
                self.assertEqual(body.count(b"\xF8\x03\x04\x00"), 1)
                self.assertNotIn(b"\xF8\x07\x04\x00", body)
                self.assertIn(b"\x18\x01\x0F\x64\x01", body)
                self.assertIn(b"\x20\x01\x80\x23\x00", body)

        active_slots = foundation.FINAL_ACTIVE_SLOTS | {
            (entity, script_index)
            for entity in exam_rooms.EMPTY_ROOM_TERMINAL_ENTITIES
            for script_index in (0, 2)
        }
        for entity in range(editor.entity_count):
            for script_index in range(32):
                pointer = editor.get_script_pointer(entity, script_index)
                if (entity, script_index) in active_slots:
                    self.assertNotEqual(pointer, foundation.SHARED_STOP_PC)
                else:
                    self.assertEqual(pointer, foundation.SHARED_STOP_PC)
        exam_rooms._validate_terminal_frontage_geometry(
            self.prepared.components[1]
        )
        self.assertFalse(
            any(
                exam_rooms._terminal_in_reach(
                    exam_rooms.TERMINAL_REJECTED_AISLE_FIXTURE,
                    position,
                )
                for position in exam_rooms.TERMINAL_POSITIONS
            )
        )


@unittest.skipUnless(DISC1.is_file(), "Perfect Works Disc 1 is unavailable")
class ExamRoomBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_bundle, cls.graphics = exam_rooms.load_exam_room_source(DISC1)
        cls.patient_assets = exam_rooms.load_patient_assets(DISC2)
        cls.source = parse_field(cls.source_bundle)
        cls.prepared_tuple = exam_rooms.prepare_exam_rooms(
            cls.source_bundle,
            cls.graphics,
            cls.patient_assets,
        )
        cls.prepared = {
            item.identity.scene: item for item in cls.prepared_tuple
        }

    def test_all_four_outputs_are_deterministic_and_frozen(self) -> None:
        again = exam_rooms.prepare_exam_rooms(
            self.source_bundle,
            self.graphics,
            self.patient_assets,
        )
        self.assertEqual(self.prepared_tuple, again)
        self.assertEqual(tuple(self.prepared), exam_rooms.SCENES)
        for scene, prepared in self.prepared.items():
            with self.subTest(scene=scene):
                self.assertEqual(
                    _identity(prepared.components[surface.SCRIPT_INDEX]),
                    exam_rooms.FINAL_SCRIPT_IDENTITIES[scene],
                )
                self.assertEqual(
                    _identity(prepared.components[6]),
                    exam_rooms.FINAL_ENCOUNTER_IDENTITY,
                )
                self.assertEqual(
                    _identity(prepared.components[7]),
                    exam_rooms.FINAL_DIALOGUE_IDENTITIES[scene],
                )
                self.assertEqual(
                    _identity(prepared.header),
                    exam_rooms.FINAL_HEADER_IDENTITIES[scene],
                )
                self.assertEqual(
                    _identity(prepared.bundle),
                    exam_rooms.FINAL_BUNDLE_IDENTITIES[scene],
                )
                self.assertEqual(prepared.graphics, self.graphics)
                self.assertEqual(prepared.entry_triangles, ((0, 16),))

    def test_only_patient_banks_script_encounters_dialogue_and_header_change(self) -> None:
        for scene, prepared in self.prepared.items():
            with self.subTest(scene=scene):
                reparsed = parse_field(prepared.bundle)
                self.assertEqual(
                    tuple(part.data for part in reparsed.parts),
                    prepared.components,
                )
                for index, source_part in enumerate(self.source.parts):
                    if index in (
                        surface.mass_driver.ACTOR_INDEX,
                        surface.mass_driver.SPRITE_INDEX,
                        surface.SCRIPT_INDEX,
                        6,
                        7,
                    ):
                        self.assertNotEqual(
                            prepared.components[index],
                            source_part.data,
                        )
                    else:
                        self.assertEqual(
                            prepared.components[index],
                            source_part.data,
                        )

    def test_terminal_header_insertion_preserves_every_existing_actor_record(self) -> None:
        source_records = [
            self.source.header[0x190 + index * 16 : 0x190 + (index + 1) * 16]
            for index in range(exam_rooms.SOURCE_HEADER_ACTOR_COUNT)
        ]
        for scene, prepared in self.prepared.items():
            with self.subTest(scene=scene):
                actor_count = struct.unpack_from("<H", prepared.header, 0x18C)[0]
                self.assertEqual(actor_count, exam_rooms.HEADER_ACTOR_COUNT)
                records = [
                    prepared.header[
                        0x190 + index * 16 : 0x190 + (index + 1) * 16
                    ]
                    for index in range(actor_count)
                ]
                self.assertEqual(
                    records[exam_rooms.TERMINAL_ENTITY],
                    exam_rooms.TERMINAL_HEADER_RECORD,
                )
                self.assertEqual(
                    records[: exam_rooms.TERMINAL_ENTITY],
                    source_records[: exam_rooms.TERMINAL_ENTITY],
                )
                self.assertEqual(
                    records[exam_rooms.TERMINAL_ENTITY + 1 :],
                    source_records[exam_rooms.TERMINAL_ENTITY :],
                )
                # E18 is the authentic animated leaf and remains before the
                # insertion boundary, byte-for-byte and at the same entity ID.
                self.assertEqual(records[18], source_records[18])

    def test_bed_and_side_computer_bank_models_are_unchanged(self) -> None:
        source_models = surface.mass_driver._indexed_bundle_entries(
            self.source.parts[surface.mass_driver.MODEL_INDEX].data
        )
        self.assertEqual(
            (
                exam_rooms.MEDICAL_TERMINAL_MODEL_INDEX,
                exam_rooms.MEDICAL_TERMINAL_SOURCE_HEADER_NODE,
                exam_rooms.MEDICAL_TERMINAL_HEADER_NODE,
            ),
            (3, 22, 23),
        )
        self.assertEqual(
            _single_block_model_aabb(
                source_models[exam_rooms.MEDICAL_TERMINAL_MODEL_INDEX]
            ),
            ((167, 220), (-92, 0), (11, 164)),
        )
        source_terminal_offset = (
            0x190 + exam_rooms.MEDICAL_TERMINAL_SOURCE_HEADER_NODE * 16
        )
        self.assertEqual(
            self.source.header[
                source_terminal_offset : source_terminal_offset + 16
            ],
            exam_rooms.MEDICAL_TERMINAL_HEADER_RECORD,
        )
        self.assertEqual(
            struct.unpack_from(
                "<Hhhh hhh H",
                exam_rooms.MEDICAL_TERMINAL_HEADER_RECORD,
            ),
            (0x0010, 0, 0x0400, 0, 0, 0, 0, 3),
        )
        for scene, prepared in self.prepared.items():
            with self.subTest(scene=scene):
                models = surface.mass_driver._indexed_bundle_entries(
                    prepared.components[surface.mass_driver.MODEL_INDEX]
                )
                self.assertEqual(models, source_models)
                self.assertEqual(
                    _identity(models[exam_rooms.BED_MODEL_INDEX]),
                    exam_rooms.BED_MODEL_IDENTITY,
                )
                self.assertEqual(
                    _identity(models[exam_rooms.MEDICAL_TERMINAL_MODEL_INDEX]),
                    exam_rooms.MEDICAL_TERMINAL_MODEL_IDENTITY,
                )
                bed_offset = 0x190 + exam_rooms.BED_HEADER_NODE * 16
                terminal_offset = (
                    0x190 + exam_rooms.MEDICAL_TERMINAL_HEADER_NODE * 16
                )
                self.assertEqual(
                    prepared.header[bed_offset : bed_offset + 16],
                    exam_rooms.BED_HEADER_RECORD,
                )
                self.assertEqual(
                    prepared.header[terminal_offset : terminal_offset + 16],
                    exam_rooms.MEDICAL_TERMINAL_HEADER_RECORD,
                )

    def test_four_distinct_native_soylent_patient_banks_install_exactly(self) -> None:
        source_actors = surface.mass_driver._indexed_bundle_entries(
            self.source.parts[surface.mass_driver.ACTOR_INDEX].data
        )
        source_sprites = surface.mass_driver._indexed_bundle_entries(
            self.source.parts[surface.mass_driver.SPRITE_INDEX].data
        )
        installed_actor_hashes: set[str] = set()
        installed_sprite_hashes: set[str] = set()
        for scene, prepared in self.prepared.items():
            asset = self.patient_assets[scene]
            actors = surface.mass_driver._indexed_bundle_entries(
                prepared.components[surface.mass_driver.ACTOR_INDEX]
            )
            sprites = surface.mass_driver._indexed_bundle_entries(
                prepared.components[surface.mass_driver.SPRITE_INDEX]
            )
            with self.subTest(scene=scene):
                self.assertEqual(
                    _identity(prepared.components[surface.mass_driver.ACTOR_INDEX]),
                    exam_rooms.FINAL_ACTOR_COMPONENT_IDENTITIES[scene],
                )
                self.assertEqual(
                    _identity(prepared.components[surface.mass_driver.SPRITE_INDEX]),
                    exam_rooms.FINAL_SPRITE_COMPONENT_IDENTITIES[scene],
                )
                self.assertEqual(
                    actors[exam_rooms.PATIENT_TARGET_BANK],
                    asset.actor,
                )
                self.assertEqual(
                    sprites[exam_rooms.PATIENT_TARGET_BANK],
                    asset.sprite,
                )
                for bank in range(1, 4):
                    self.assertEqual(actors[bank], source_actors[bank])
                    self.assertEqual(sprites[bank], source_sprites[bank])
                self.assertEqual(
                    _identity(actors[exam_rooms.DOCTOR_BANK]),
                    exam_rooms.DOCTOR_ACTOR_IDENTITY,
                )
                self.assertEqual(
                    _identity(sprites[exam_rooms.DOCTOR_BANK]),
                    exam_rooms.DOCTOR_SPRITE_IDENTITY,
                )
                installed_actor_hashes.add(_identity(asset.actor)[1])
                installed_sprite_hashes.add(_identity(asset.sprite)[1])
        self.assertEqual(len(installed_actor_hashes), 4)
        self.assertEqual(len(installed_sprite_hashes), 4)

    def test_bedside_patient_and_doctor_are_solid_talkable_and_mutually_facing(self) -> None:
        for scene, prepared in self.prepared.items():
            editor = ScriptEditor(prepared.components[surface.SCRIPT_INDEX])
            layout = exam_rooms.NPC_ROUTINE_PCS_BY_SCENE[scene]
            expected = (
                (
                    exam_rooms.PATIENT_ENTITY,
                    0,
                    "patient_init",
                    exam_rooms.PATIENT_INIT_BODIES_BY_SCENE[scene],
                ),
                (
                    exam_rooms.DOCTOR_ENTITY,
                    0,
                    "doctor_init",
                    exam_rooms.DOCTOR_INIT_BODY,
                ),
                (
                    exam_rooms.PATIENT_ENTITY,
                    2,
                    "patient_action",
                    exam_rooms.PATIENT_ACTION_BODIES_BY_SCENE[scene],
                ),
                (
                    exam_rooms.DOCTOR_ENTITY,
                    2,
                    "doctor_action",
                    exam_rooms.DOCTOR_ACTION_BODIES_BY_SCENE[scene],
                ),
            )
            with self.subTest(scene=scene):
                for entity, slot, label, body in expected:
                    pc = layout[label]
                    self.assertEqual(editor.get_script_pointer(entity, slot), pc)
                    self.assertEqual(editor.bytecode[pc : pc + len(body)], body)
                for body in (
                    exam_rooms.PATIENT_INIT_BODIES_BY_SCENE[scene],
                    exam_rooms.DOCTOR_INIT_BODY,
                ):
                    self.assertIn(exam_rooms.ACTOR_BOUNDING_VOLUME, body)
                    self.assertIn(
                        exam_rooms.ACTOR_STATIONARY_COLLISION_FLAGS,
                        body,
                    )
                    self.assertNotIn(exam_rooms.ACTOR_GHOST_COLLISION_FLAGS, body)
                    self.assertNotIn(b"\x23", body)
                    self.assertNotIn(b"\x2A", body)
                if scene in (591, 592):
                    self.assertIn(
                        b"\x2C\x01",
                        exam_rooms.PATIENT_INIT_BODIES_BY_SCENE[scene],
                    )
                else:
                    self.assertNotIn(
                        b"\x2C\x01",
                        exam_rooms.PATIENT_INIT_BODIES_BY_SCENE[scene],
                    )
                mutual = (
                    b"\xFE\x17"
                    + bytes((exam_rooms.DOCTOR_ENTITY, exam_rooms.PATIENT_ENTITY))
                    + b"\xFE\x17"
                    + bytes((exam_rooms.PATIENT_ENTITY, exam_rooms.DOCTOR_ENTITY))
                )
                self.assertIn(mutual, exam_rooms.DOCTOR_INIT_BODY)
                self.assertTrue(
                    exam_rooms.PATIENT_ACTION_BODIES_BY_SCENE[scene].startswith(
                        b"\x6F\xFF\xD2"
                    )
                )
                self.assertTrue(
                    exam_rooms.DOCTOR_ACTION_BODIES_BY_SCENE[scene].startswith(
                        b"\x6F\xFF\xD2"
                    )
                )

    def test_treatment_pair_has_safe_walkmesh_and_interaction_separation(self) -> None:
        triangles = surface._walkmesh_layer(self.source.parts[1].data, 0)
        patient_hits = tuple(
            index
            for index, triangle in enumerate(triangles)
            if surface._point_inside_triangle(exam_rooms.PATIENT_POSITION, triangle)
        )
        doctor_hits = tuple(
            index
            for index, triangle in enumerate(triangles)
            if surface._point_inside_triangle(exam_rooms.DOCTOR_POSITION, triangle)
        )
        self.assertEqual(patient_hits, (exam_rooms.PATIENT_TRIANGLE,))
        self.assertEqual(doctor_hits, (exam_rooms.DOCTOR_TRIANGLE,))
        self.assertGreaterEqual(
            abs(exam_rooms.DOCTOR_POSITION[1] - exam_rooms.PATIENT_POSITION[1]),
            2 * exam_rooms.ACTOR_INTERACTION_HALF_DEPTH,
        )
        self.assertGreaterEqual(
            abs(exam_rooms.PATIENT_POSITION[1] - exam_rooms.TERMINAL_POSITION[1]),
            exam_rooms.ACTOR_INTERACTION_HALF_DEPTH
            + exam_rooms.TERMINAL_INTERACTION_HALF_DEPTH,
        )
        # X >= 108 is the room's right-hand player aisle.
        self.assertLess(
            exam_rooms.PATIENT_POSITION[0]
            + exam_rooms.ACTOR_INTERACTION_HALF_WIDTH,
            108,
        )
        self.assertLess(
            exam_rooms.DOCTOR_POSITION[0]
            + exam_rooms.ACTOR_INTERACTION_HALF_WIDTH,
            108,
        )

    def test_private_room_dialogue_is_unique_positive_and_font_grid_safe(self) -> None:
        doctor_texts: set[str] = set()
        patient_texts: set[str] = set()
        banned_revelation_words = (
            "soylent",
            "sufal",
            "mass",
            "processing",
            "food",
            "kill",
            "death",
        )
        for scene, prepared in self.prepared.items():
            dialogue = parse_dialogue(prepared.components[7])
            doctor = dialogue.blocks[
                exam_rooms.DOCTOR_DIALOGUE_IDS_BY_SCENE[scene]
            ]
            patient = dialogue.blocks[
                exam_rooms.PATIENT_DIALOGUE_IDS_BY_SCENE[scene]
            ]
            with self.subTest(scene=scene):
                self.assertEqual(
                    len(dialogue.blocks),
                    exam_rooms.FINAL_DIALOGUE_COUNTS_BY_SCENE[scene],
                )
                self.assertEqual(
                    doctor.text,
                    exam_rooms.DOCTOR_DIALOGUES_BY_SCENE[scene],
                )
                self.assertEqual(
                    patient.text,
                    exam_rooms.PATIENT_DIALOGUES_BY_SCENE[scene],
                )
                self.assertTrue(
                    "private" in doctor.text.casefold()
                    or "restricted" in doctor.text.casefold()
                    or "not be in here" in doctor.text.casefold()
                )
                self.assertTrue(
                    "waiting" in doctor.text.casefold()
                    or "reception" in doctor.text.casefold()
                    or "outside" in doctor.text.casefold()
                )
                self.assertFalse(
                    any(
                        word in patient.text.casefold()
                        for word in banned_revelation_words
                    )
                )
                for block in (doctor, patient):
                    surface.mass_driver._validate_authored_manual_wrap(
                        {
                            "manual_wrap": True,
                            "width": block.width,
                            "height": block.height,
                            "text": block.text,
                        },
                        block.block_id,
                    )
                doctor_texts.add(doctor.text)
                patient_texts.add(patient.text)
        self.assertEqual(len(doctor_texts), 4)
        self.assertEqual(len(patient_texts), 4)

    def test_entry_is_on_walkmesh_and_terminal_anchors_are_on_the_model_plane(self) -> None:
        triangles = surface._walkmesh_layer(self.source.parts[1].data, 0)
        entry_hits = tuple(
            index
            for index, triangle in enumerate(triangles)
            if surface._point_inside_triangle(exam_rooms.ENTRY_POSITION, triangle)
        )
        self.assertEqual(entry_hits, (exam_rooms.ENTRY_TRIANGLE,))
        # The invisible targets sit on model 3's room-facing Z=-167 plane;
        # Fei remains on the adjacent operator triangles in front of the bank.
        self.assertEqual(
            tuple(
                tuple(
                    index
                    for index, triangle in enumerate(triangles)
                    if surface._point_inside_triangle(position, triangle)
                )
                for position in exam_rooms.TERMINAL_POSITIONS
            ),
            ((), (), ()),
        )

    def test_all_side_bank_frontage_is_covered_and_saved_aisle_is_silent(self) -> None:
        triangles = surface._walkmesh_layer(self.source.parts[1].data, 0)
        operator_triangles = tuple(
            triangles[index]
            for index in exam_rooms.TERMINAL_OPERATOR_TRIANGLES
        )
        reach = (
            2 * exam_rooms.TERMINAL_INTERACTION_HALF_WIDTH + 0x10,
            2 * exam_rooms.TERMINAL_INTERACTION_HALF_DEPTH + 0x10,
        )
        self.assertEqual(reach, (18, 46))

        def in_reach(
            point: tuple[float, float],
            position: tuple[int, int],
        ) -> bool:
            return (
                abs(point[0] - position[0]) <= reach[0]
                and abs(point[1] - position[1]) <= reach[1]
            )

        def target_yaw(
            point: tuple[float, float],
            position: tuple[int, int],
        ) -> int:
            engine_x, engine_z = (math.floor(axis) for axis in point)
            return (
                -surface.mass_driver._noah_ratan2(
                    position[1] - engine_z,
                    position[0] - engine_x,
                )
            ) & 0x0FFF

        def facing_accepts(
            point: tuple[float, float],
            position: tuple[int, int],
            yaw: int,
        ) -> bool:
            delta = (yaw - target_yaw(point, position)) & 0x0FFF
            return delta < 700 or delta > 3396

        front_z = exam_rooms.TERMINAL_POSITIONS[0][1]
        eligible = tuple(
            (x, z)
            for x in range(
                exam_rooms.TERMINAL_FRONTAGE_X[0],
                exam_rooms.TERMINAL_FRONTAGE_X[1] + 1,
            )
            for z in range(front_z - reach[1], front_z + reach[1] + 1)
            if any(
                surface._point_inside_triangle((x, z), triangle)
                for triangle in operator_triangles
            )
        )
        self.assertEqual(len(eligible), 1_201)
        self.assertEqual(
            tuple(
                point
                for point in eligible
                if any(
                    in_reach(point, position)
                    and facing_accepts(
                        point,
                        position,
                        exam_rooms.TERMINAL_APPROACH_YAW,
                    )
                    for position in exam_rooms.TERMINAL_POSITIONS
                )
            ),
            eligible,
        )
        self.assertFalse(
            any(
                in_reach(point, position)
                and facing_accepts(
                    point,
                    position,
                    exam_rooms.TERMINAL_BED_YAW,
                )
                for point in eligible
                for position in exam_rooms.TERMINAL_POSITIONS
            )
        )
        self.assertTrue(
            any(
                in_reach(exam_rooms.TERMINAL_APPROACH_FIXTURE, position)
                and facing_accepts(
                    exam_rooms.TERMINAL_APPROACH_FIXTURE,
                    position,
                    exam_rooms.TERMINAL_APPROACH_YAW,
                )
                for position in exam_rooms.TERMINAL_POSITIONS
            )
        )

        self.assertEqual(
            exam_rooms.TERMINAL_REJECTED_AISLE_FIXTURE,
            (75.00785827636719, -77.75068664550781),
        )
        self.assertEqual(
            tuple(
                index
                for index, triangle in enumerate(triangles)
                if surface._point_inside_triangle(
                    exam_rooms.TERMINAL_REJECTED_AISLE_FIXTURE,
                    triangle,
                )
            ),
            (8,),
        )
        self.assertFalse(
            any(
                in_reach(exam_rooms.TERMINAL_REJECTED_AISLE_FIXTURE, position)
                for position in exam_rooms.TERMINAL_POSITIONS
            )
        )

    def test_retail_events_remain_retired_and_only_clinical_slots_are_active(self) -> None:
        active_slots = (
            foundation.FINAL_ACTIVE_SLOTS
            | {
                (entity, script_index)
                for entity in exam_rooms.TERMINAL_ENTITIES
                for script_index in (0, 2)
            }
            | {
                (exam_rooms.PATIENT_ENTITY, 0),
                (exam_rooms.PATIENT_ENTITY, 2),
                (exam_rooms.DOCTOR_ENTITY, 0),
                (exam_rooms.DOCTOR_ENTITY, 2),
            }
        )
        for scene, prepared in self.prepared.items():
            editor = ScriptEditor(prepared.components[surface.SCRIPT_INDEX])
            with self.subTest(scene=scene):
                self.assertEqual(editor.entity_count, exam_rooms.ENTITY_COUNT)
                self.assertEqual(editor.bytecode[exam_rooms.SHARED_STOP_PC], 0)
                for entity in range(editor.entity_count):
                    for script_index in range(32):
                        pointer = editor.get_script_pointer(entity, script_index)
                        if (entity, script_index) in active_slots:
                            self.assertNotEqual(pointer, exam_rooms.SHARED_STOP_PC)
                        else:
                            self.assertEqual(pointer, exam_rooms.SHARED_STOP_PC)

    def test_native_leaf_is_preserved_and_each_exit_returns_to_its_own_parameter(self) -> None:
        source_editor = ScriptEditor(
            self.source.parts[surface.SCRIPT_INDEX].data
        )
        for scene, prepared in self.prepared.items():
            editor = ScriptEditor(prepared.components[surface.SCRIPT_INDEX])
            parameter = exam_rooms.RETURN_PARAMETERS_BY_SCENE[scene]
            with self.subTest(scene=scene):
                self.assertEqual(
                    editor.get_script_pointer(exam_rooms.RETURN_CONTROLLER, 2),
                    exam_rooms.RETURN_ACTION_PC,
                )
                self.assertEqual(
                    editor.bytecode[
                        exam_rooms.RETURN_ACTION_PC : exam_rooms.TERMINAL_INIT_PC
                    ],
                    exam_rooms.RETURN_ACTIONS_BY_SCENE[scene],
                )
                self.assertIn(
                    surface._change_field(621, parameter),
                    exam_rooms.RETURN_ACTIONS_BY_SCENE[scene],
                )
                self.assertEqual(
                    editor.get_script_pointer(
                        exam_rooms.RETURN_HELPER,
                        exam_rooms.RETURN_HELPER_SCRIPT_INDEX,
                    ),
                    source_editor.get_script_pointer(
                        exam_rooms.RETURN_HELPER,
                        exam_rooms.RETURN_HELPER_SCRIPT_INDEX,
                    ),
                )
                self.assertEqual(
                    editor.bytecode[
                        exam_rooms.RETURN_HELPER_PC : exam_rooms.RETURN_HELPER_PC
                        + len(exam_rooms.RETURN_HELPER_BODY)
                    ],
                    exam_rooms.RETURN_HELPER_BODY,
                )

    def test_each_side_bank_has_three_facing_gated_ghost_x_carriers(self) -> None:
        source_editor = ScriptEditor(
            self.source.parts[surface.SCRIPT_INDEX].data
        )
        source_cavity = source_editor.bytecode[
            exam_rooms.TERMINAL_AUX_INIT_PCS[0] :
            exam_rooms.TERMINAL_AUX_CAVITY_END_PC
        ]
        self.assertEqual(
            _identity(source_cavity),
            exam_rooms.TERMINAL_AUX_CAVITY_SOURCE_IDENTITY,
        )
        self.assertEqual(len(exam_rooms.TERMINAL_INIT_BODY), 29)
        self.assertEqual(len(exam_rooms.TERMINAL_AUX_CAVITY), 87)

        carrier_pcs = (
            exam_rooms.TERMINAL_INIT_PC,
            *exam_rooms.TERMINAL_AUX_INIT_PCS,
        )
        for scene, prepared in self.prepared.items():
            editor = ScriptEditor(prepared.components[surface.SCRIPT_INDEX])
            with self.subTest(scene=scene):
                self.assertEqual(
                    editor.bytecode[
                        exam_rooms.TERMINAL_AUX_INIT_PCS[0] :
                        exam_rooms.TERMINAL_AUX_CAVITY_END_PC
                    ],
                    exam_rooms.TERMINAL_AUX_CAVITY,
                )
                self.assertEqual(
                    tuple(
                        editor.get_script_pointer(entity, 0)
                        for entity in exam_rooms.TERMINAL_ENTITIES
                    ),
                    carrier_pcs,
                )
                self.assertEqual(
                    tuple(
                        editor.get_script_pointer(entity, 2)
                        for entity in exam_rooms.TERMINAL_ENTITIES
                    ),
                    (exam_rooms.TERMINAL_ACTION_PC,) * 3,
                )
                for entity, pc, position, body in zip(
                    exam_rooms.TERMINAL_ENTITIES,
                    carrier_pcs,
                    exam_rooms.TERMINAL_POSITIONS,
                    exam_rooms.TERMINAL_INIT_BODIES,
                    strict=True,
                ):
                    with self.subTest(scene=scene, entity=entity):
                        self.assertEqual(
                            editor.bytecode[pc : pc + len(body)],
                            body,
                        )
                        self.assertEqual(
                            body[3:9],
                            b"\x19"
                            + struct.pack("<hh", *position)
                            + b"\xC0",
                        )
                        # F8/0x03 retains the native narrow facing cone;
                        # F8/0x07 would accept Cross from any heading.
                        self.assertEqual(body.count(b"\xF8\x03\x04\x00"), 1)
                        self.assertNotIn(b"\xF8\x07\x04\x00", body)
                        # OP18 0x01/0x0F gives 18-by-46 effective half-reach.
                        self.assertIn(b"\x18\x01\x0F\x64\x01", body)
                        # OP20/0x80 keeps every invisible target non-colliding.
                        self.assertIn(b"\x20\x01\x80", body)

    def test_room_specific_terminal_dialogue_is_appended_repeatably(self) -> None:
        for scene in (591, 592, 594):
            prepared = self.prepared[scene]
            editor = ScriptEditor(prepared.components[surface.SCRIPT_INDEX])
            dialogue = parse_dialogue(prepared.components[7])
            expected_text = exam_rooms.EXAM_ROOM_BY_SCENE[scene].terminal_dialogues[0]
            action = editor.bytecode[
                exam_rooms.TERMINAL_ACTION_PC :
                exam_rooms.TERMINAL_ACTION_PC
                + exam_rooms.TERMINAL_ACTION_LENGTHS_BY_SCENE[scene]
            ]
            with self.subTest(scene=scene):
                self.assertEqual(
                    len(dialogue.blocks),
                    exam_rooms.FINAL_DIALOGUE_COUNTS_BY_SCENE[scene],
                )
                self.assertEqual(dialogue.blocks[53].text, expected_text)
                self.assertEqual(
                    _identity(action),
                    (
                        exam_rooms.TERMINAL_ACTION_LENGTHS_BY_SCENE[scene],
                        exam_rooms.TERMINAL_ACTION_SHA256_BY_SCENE[scene],
                    ),
                )
                self.assertEqual(action, _REPEATABLE_TERMINAL_ACTION)
                reachable = _reachable_active_instructions(editor)
                release_polls = tuple(
                    pc
                    for pc, instruction in sorted(reachable.items())
                    if instruction.startswith(b"\x31\x20\x00")
                )
                self.assertEqual(release_polls, (0x06E3, 0x06F6))
                self.assertIn(b"\xF5\x35\x00\x01\x9C", action)
                self.assertNotIn(exam_rooms.ITEM_ACQUISITION_SOUND, action)
                self.assertNotIn(
                    b"\x3A\x1A\x02\x08\x00\x40",
                    action,
                )

    def test_every_occupied_room_terminal_loads_its_current_patient_record(self) -> None:
        expected_records = {
            591: (53, "H-591-04", "long-muzzled", "Hemoglobin", "Tonic uptake"),
            592: (53, "N-592-07", "cream-furred", "Joint inflammation", "Nanomachine uptake"),
            593: (55, "A-593-12", "shelled", "Shell density", "Mineral balance"),
            594: (53, "T-594-03", "fin-armed", "Hydration", "Injection uptake"),
        }
        records: set[str] = set()
        patient_ids: set[str] = set()
        banned_placeholder_or_fei_text = (
            "no patient",
            "empty",
            "standby",
            "awaiting the next patient",
            "fei",
            "neural activity",
            "biological compatibility",
            "pulse 64 / bp 118/72",
        )

        for scene, expected in expected_records.items():
            dialogue_id, patient_id, patient_type, finding, response = expected
            dialogue = parse_dialogue(self.prepared[scene].components[7])
            record = dialogue.blocks[dialogue_id]
            pages = record.text.split("<New>")
            with self.subTest(scene=scene, dialogue_id=dialogue_id):
                self.assertEqual(
                    record.text,
                    exam_rooms.EXAM_ROOM_BY_SCENE[scene].terminal_dialogues[
                        2 if scene == 593 else 0
                    ],
                )
                self.assertEqual(len(pages), 2)
                self.assertEqual(pages[0].count("\n"), 3)
                self.assertEqual(
                    pages[1].removesuffix("<Close>").count("\n"),
                    3,
                )
                self.assertTrue(record.text.endswith("<Close>"))
                self.assertIn("PATIENT RECORD", pages[0])
                self.assertIn(patient_id, pages[0])
                self.assertIn(patient_type, pages[0])
                self.assertIn("Pulse ", pages[0])
                self.assertIn(" / BP ", pages[0])
                self.assertIn("Temp ", pages[0])
                self.assertIn(" / Resp. ", pages[0])
                self.assertIn(finding, pages[1])
                self.assertIn(response, pages[1])
                self.assertFalse(
                    any(
                        banned in record.text.casefold()
                        for banned in banned_placeholder_or_fei_text
                    )
                )
                surface.mass_driver._validate_authored_manual_wrap(
                    {
                        "manual_wrap": True,
                        "width": record.width,
                        "height": record.height,
                        "text": record.text,
                    },
                    record.block_id,
                )
                records.add(record.text)
                patient_ids.add(patient_id)

        self.assertEqual(len(records), 4)
        self.assertEqual(len(patient_ids), 4)

    def test_room594_is_benign_treatment_preparation(self) -> None:
        prepared = self.prepared[594]
        editor = ScriptEditor(prepared.components[surface.SCRIPT_INDEX])
        action = editor.bytecode[
            exam_rooms.TERMINAL_ACTION_PC :
            exam_rooms.TERMINAL_ACTION_PC
            + exam_rooms.TERMINAL_ACTION_LENGTHS_BY_SCENE[594]
        ]
        dialogue = parse_dialogue(prepared.components[7])
        spec = exam_rooms.EXAM_ROOM_BY_SCENE[594]
        self.assertEqual(spec.return_parameter, 5)
        self.assertEqual(spec.endpoint_id, "intake_treatment_preparation.treatment")
        self.assertFalse(spec.awards_quarantine_keycard)
        self.assertEqual(
            len(dialogue.blocks),
            exam_rooms.FINAL_DIALOGUE_COUNTS_BY_SCENE[594],
        )
        self.assertEqual(dialogue.blocks[53].text, exam_rooms.TREATMENT_PREPARATION_DIALOGUE)
        self.assertIn("PATIENT RECORD: T-594-03", dialogue.blocks[53].text)
        self.assertIn("Type: fin-armed demihuman", dialogue.blocks[53].text)
        self.assertIn("Hydration: NOMINAL", dialogue.blocks[53].text)
        self.assertIn("Injection uptake: STABLE", dialogue.blocks[53].text)
        self.assertNotIn("Sufal", dialogue.blocks[53].text)
        self.assertNotIn("Soylent", dialogue.blocks[53].text)
        self.assertIn(b"\xF5\x35\x00\x01\x9C", action)
        self.assertNotIn(exam_rooms.ITEM_ACQUISITION_SOUND, action)
        self.assertNotIn(b"\x3A\x1A\x02\x08\x00\x40", action)
        reachable = _reachable_active_instructions(editor)
        inventory_awards = tuple(
            pc
            for pc, instruction in sorted(reachable.items())
            if instruction[0] == 0x8C
        )
        variable_writes = tuple(
            (pc, instruction[0], struct.unpack_from("<H", instruction, 1)[0])
            for pc, instruction in sorted(reachable.items())
            if instruction[0] in _VARIABLE_WRITE_OPCODES
        )
        self.assertEqual(inventory_awards, ())
        # The native animated door helper only resets/increments its field-local
        # scratch word.  Any write below 0x0400 would be a system/persistent
        # mutation and is forbidden in this benign treatment room.
        self.assertEqual(
            variable_writes,
            ((0x066E, 0x35, 0x040E), (0x0685, 0x3C, 0x040E)),
        )
        self.assertFalse(
            tuple(write for write in variable_writes if write[2] < 0x0400)
        )
        surface.mass_driver._validate_authored_manual_wrap(
            {
                "manual_wrap": True,
                "width": dialogue.blocks[53].width,
                "height": dialogue.blocks[53].height,
                "text": dialogue.blocks[53].text,
            },
            dialogue.blocks[53].block_id,
        )

    def test_room593_awards_the_keycard_then_displays_current_patient_record(self) -> None:
        prepared = self.prepared[593]
        editor = ScriptEditor(prepared.components[surface.SCRIPT_INDEX])
        action = editor.bytecode[
            exam_rooms.TERMINAL_ACTION_PC :
            exam_rooms.TERMINAL_ACTION_PC
            + exam_rooms.TERMINAL_ACTION_LENGTHS_BY_SCENE[593]
        ]
        dialogue = parse_dialogue(prepared.components[7])
        self.assertEqual(
            len(dialogue.blocks),
            exam_rooms.FINAL_DIALOGUE_COUNTS_BY_SCENE[593],
        )
        self.assertEqual(
            tuple(block.text for block in dialogue.blocks[53:57]),
            exam_rooms.EXAM_ROOM_BY_SCENE[593].terminal_dialogues,
        )
        diagnostics = dialogue.blocks[55]
        self.assertEqual(
            diagnostics.text,
            exam_rooms.POST_KEYCARD_DIAGNOSTICS_DIALOGUE,
        )
        self.assertIn("PATIENT RECORD: A-593-12", diagnostics.text)
        self.assertIn("Type: shelled demihuman", diagnostics.text)
        self.assertIn("Pulse 58 bpm / BP 124/76", diagnostics.text)
        self.assertIn("Temp 36.5 C / Resp. 11/min", diagnostics.text)
        self.assertIn("Shell density: NOMINAL", diagnostics.text)
        self.assertIn("Treatment response: STRONG", diagnostics.text)
        self.assertEqual(diagnostics.text.count("<New>"), 1)
        self.assertNotIn("keycard", diagnostics.text.casefold())
        self.assertNotIn("empty", diagnostics.text.casefold())
        self.assertNotIn("fei", diagnostics.text.casefold())
        # The retail renderer wraps in encoded font units, not Python
        # characters.  Validate every authored keycard line against the exact
        # width/height grid so the one-unit V214 clipping cannot return.
        for block in dialogue.blocks[53:57]:
            with self.subTest(dialogue_id=block.block_id):
                surface.mass_driver._validate_authored_manual_wrap(
                    {
                        "manual_wrap": True,
                        "width": block.width,
                        "height": block.height,
                        "text": block.text,
                    },
                    block.block_id,
                )
        self.assertEqual(
            _identity(action),
            (
                exam_rooms.TERMINAL_ACTION_LENGTHS_BY_SCENE[593],
                exam_rooms.TERMINAL_ACTION_SHA256_BY_SCENE[593],
            ),
        )

        bit_test = b"\x02\x1A\x02\x00\x01\x46"
        set_bit = b"\x3A\x1A\x02\x08\x00\x40"
        inserted_dialogue = b"\xF5\x35\x00\x01\x9C"
        acquired_dialogue = b"\xF5\x36\x00\x01\x9C"
        diagnostics_dialogue = b"\xF5\x37\x00\x01\x9C"
        choice_dialogue = b"\xD2\x38\x00\x00\xA9\x12\x9C"
        self.assertEqual(action.count(bit_test), 1)
        self.assertEqual(action.count(exam_rooms.ITEM_ACQUISITION_SOUND), 1)
        self.assertEqual(action.count(set_bit), 1)
        self.assertEqual(action.count(inserted_dialogue), 1)
        self.assertEqual(action.count(acquired_dialogue), 1)
        self.assertEqual(action.count(diagnostics_dialogue), 1)
        self.assertEqual(action.count(choice_dialogue), 1)
        self.assertLess(action.index(inserted_dialogue), action.index(choice_dialogue))
        self.assertLess(action.index(choice_dialogue), action.index(exam_rooms.ITEM_ACQUISITION_SOUND))
        self.assertLess(action.index(exam_rooms.ITEM_ACQUISITION_SOUND), action.index(acquired_dialogue))
        self.assertLess(action.index(acquired_dialogue), action.index(set_bit))

    def test_random_encounters_stay_disabled_without_touching_formations(self) -> None:
        source_encounters = self.source.parts[6].data
        for scene, prepared in self.prepared.items():
            encounters = prepared.components[6]
            with self.subTest(scene=scene):
                self.assertEqual(encounters[:-16], source_encounters[:-16])
                self.assertEqual(EncounterTable(encounters).weights, (0,) * 16)

    def test_source_drift_is_rejected_by_the_shared_foundation(self) -> None:
        bad_bundle = bytearray(self.source_bundle)
        bad_bundle[-1] ^= 1
        with self.assertRaisesRegex(
            surface.SurfaceSoylentBuildError,
            "bundle changed",
        ):
            exam_rooms.prepare_exam_room(
                591,
                bytes(bad_bundle),
                self.graphics,
                self.patient_assets[591],
            )

        bad_graphics = bytearray(self.graphics)
        bad_graphics[-1] ^= 1
        with self.assertRaisesRegex(
            surface.SurfaceSoylentBuildError,
            "graphics changed",
        ):
            exam_rooms.prepare_exam_room(
                591,
                self.source_bundle,
                bytes(bad_graphics),
                self.patient_assets[591],
            )

    def test_disc_loader_extracts_the_frozen_field352_pair(self) -> None:
        self.assertEqual(
            exam_rooms.load_exam_room_source(DISC1),
            (self.source_bundle, self.graphics),
        )

    @unittest.skipUnless(DISC2.is_file(), "Perfect Works Disc 2 is unavailable")
    def test_real_disc_two_targets_are_checked_dummies(self) -> None:
        exam_rooms.verify_exam_room_targets_are_dummy(DISC2)


if __name__ == "__main__":
    unittest.main()
