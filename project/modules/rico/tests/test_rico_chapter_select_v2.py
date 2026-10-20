from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

from dataclasses import replace
import hashlib
import math
from pathlib import Path
import struct
import unittest

import tools.build_rico_arc as rico
from tools.xgdialog import decode_text
from tools.xgfield import parse_field
from tools.xgscript import AtelScript


PROJECT_ROOT = REPOSITORY_ROOT
AUDIT_ROOT = PROJECT_ROOT / "work" / "rico_arc_audit" / "disc1"
MASS_DRIVER_RETAIL_ROOT = (
    PROJECT_ROOT / "work" / "reference_fields" / "cd1_zeboim"
)


def _audit_resource(canonical_id: int) -> bytes:
    path = AUDIT_ROOT / f"{canonical_id}.bin"
    if not path.is_file():
        raise AssertionError(f"Missing checked retail audit resource: {path}")
    return path.read_bytes()


def _save_point_donor_resource() -> bytes:
    candidates = (
        AUDIT_ROOT / f"{rico._field_bundle_id(rico.HUB_SAVE_DONOR_FIELD)}.bin",
        MASS_DRIVER_RETAIL_ROOT
        / f"{rico._field_bundle_id(rico.HUB_SAVE_DONOR_FIELD)}.bin",
    )
    for path in candidates:
        if path.is_file():
            return path.read_bytes()
    raise AssertionError(
        "Missing checked retail memory-cube donor: "
        + " or ".join(str(path) for path in candidates)
    )


def _pointed_body(editor: AtelScript, entity: int, script_index: int) -> bytes:
    pointer = editor.get_script_pointer(entity, script_index)
    return rico.mass_driver._pointed_script_body(editor, pointer)


def _lenient_dialogue_texts(data: bytes) -> tuple[str, ...]:
    """Decode retail dialogue without rejecting harmless post-Close padding."""

    block_count = struct.unpack_from("<I", data, 0)[0] + 1
    offsets = tuple(
        struct.unpack_from("<H", data, 4 + index * 2)[0]
        for index in range(block_count)
    )
    return tuple(
        decode_text(
            data[
                offset : (
                    offsets[index + 1]
                    if index + 1 < block_count
                    else len(data)
                )
            ]
        )
        for index, offset in enumerate(offsets)
    )


def _replace_stage(
    contract: rico.PlayableChapter,
    interaction_index: int,
    stage_index: int,
    stage: rico.PlayableStage,
) -> rico.PlayableChapter:
    interactions = list(contract.interactions)
    stages = list(interactions[interaction_index].stages)
    stages[stage_index] = stage
    interactions[interaction_index] = replace(
        interactions[interaction_index],
        stages=tuple(stages),
    )
    return replace(contract, interactions=tuple(interactions))


def _normalize_local_routes(data: bytes) -> bytes:
    """Erase only local hub/chapter field operands for parity comparisons."""

    result = data
    local_fields = set(rico.HUB_FIELDS.values())
    for fields in rico.CHAPTER_FIELDS.values():
        local_fields.update(fields.values())
    local_fields.update(
        (
            rico.CHAPTER_TWO_BEDROOM_FIELD,
            rico.UNIFIED_DISC2_CHAPTER_TWO_BEDROOM_FIELD,
        )
    )
    replacement = bytes.fromhex("98 FE FF 00 80")
    for field in sorted(local_fields):
        result = result.replace(rico._change_field(field, 0), replacement)
    native_door_replacement = bytes.fromhex("FD FC FB FA F9")
    for field in (
        rico.CHAPTER_TWO_BEDROOM_FIELD,
        rico.UNIFIED_DISC2_CHAPTER_TWO_BEDROOM_FIELD,
    ):
        result = result.replace(
            rico._immediate(field) + rico._immediate(0) + b"\x5B",
            native_door_replacement,
        )
    return result


class RicoChapterSelectV2Fixtures(unittest.TestCase):
    """Build every checked field once for the focused runtime regressions."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.chapters = rico.load_chapters()
        cls.chapter_sources: dict[int, bytes] = {}
        cls.chapter_outputs: dict[tuple[int, int], bytes] = {}
        for chapter in cls.chapters:
            source = _audit_resource(rico._field_bundle_id(chapter.donor_field))
            cls.chapter_sources[chapter.chapter_id] = source
            for disc in (1, 2):
                cls.chapter_outputs[disc, chapter.chapter_id] = (
                    rico._build_playable_chapter_bundle(
                        source,
                        chapter,
                        rico.HUB_FIELDS[disc],
                        (
                            cls.chapters[chapter.chapter_id]
                            if chapter.chapter_id < 7
                            else None
                        ),
                    )
                )

        cls.hub_source = _audit_resource(
            rico._field_bundle_id(rico.HUB_DONOR_FIELD)
        )
        cls.hub_outputs = {
            disc: rico._build_hub_bundle(
                cls.hub_source,
                rico.CHAPTER_FIELDS[disc],
                cls.chapters,
            )
            for disc in (1, 2)
        }
        cls.title_source = _audit_resource(rico.TITLE_FIELD_CANONICAL_ID)
        cls.title_outputs = {
            disc: rico._build_title_bundle(
                cls.title_source,
                rico.HUB_FIELDS[disc],
            )
            for disc in (1, 2)
        }

    @classmethod
    def _chapter_layout(
        cls,
        disc: int,
        chapter_id: int,
    ) -> tuple[AtelScript, AtelScript, rico.PlayableChapter, int, int]:
        chapter = cls.chapters[chapter_id - 1]
        source_field = parse_field(cls.chapter_sources[chapter_id])
        source_editor = AtelScript(
            rico._normalize_playable_party_script(
                chapter,
                source_field.parts[rico.SCRIPT_INDEX].data,
            )
        )
        output_editor = AtelScript(
            parse_field(cls.chapter_outputs[disc, chapter_id])
            .parts[rico.SCRIPT_INDEX]
            .data
        )
        contract = rico._playable_chapter_contract(chapter_id)
        first_controller = source_editor.entity_count + len(
            rico._missing_playable_characters(chapter, source_editor)
        )
        exit_entity = first_controller + len(contract.interactions)
        return (
            source_editor,
            output_editor,
            contract,
            first_controller,
            exit_entity,
        )


class SephirotHubIdentityTests(RicoChapterSelectV2Fixtures):
    def test_standalone_hubs_remain_byte_exact_without_a_content_target(self) -> None:
        # Reviewed interlude hubs: only script/dialogue components5/7 differ
        # from the reproduced opening-v2 pins. Chapter2 now enters Rico's
        # room directly, after the revised narration in its selection card.
        # Header actors and all other packed components stayed byte-exact.
        expected = {
            1: (
                43_680,
                "b685fd6e4a088906a0367e96a2fc7ef987960c289ddf5bac1d1cd42b2f191336",
            ),
            2: (
                43_680,
                "dad38ac85fbabc3023d9a849f3b669eb89796c2efe1ef64fbb5a08e319deb396",
            ),
        }
        for disc, identity in expected.items():
            with self.subTest(disc=disc):
                self.assertEqual(
                    (
                        len(self.hub_outputs[disc]),
                        hashlib.sha256(self.hub_outputs[disc]).hexdigest(),
                    ),
                    identity,
                )

    def test_exact_field_719_bundle_graphics_and_native_light_assets(self) -> None:
        self.assertEqual(rico.HUB_DONOR_FIELD, 719)
        self.assertEqual(rico._field_bundle_id(719), 2044)
        self.assertEqual(
            (len(self.hub_source), hashlib.sha256(self.hub_source).hexdigest()),
            (rico.HUB_DONOR_BUNDLE_SIZE, rico.HUB_DONOR_BUNDLE_SHA256),
        )

        graphics = _audit_resource(2045)
        self.assertEqual(
            (len(graphics), hashlib.sha256(graphics).hexdigest()),
            (rico.HUB_DONOR_GRAPHICS_SIZE, rico.HUB_DONOR_GRAPHICS_SHA256),
        )

        components = [part.data for part in parse_field(self.hub_source).parts]
        actor_banks = rico.mass_driver._indexed_bundle_entries(
            components[rico.mass_driver.ACTOR_INDEX]
        )
        sprite_banks = rico.mass_driver._indexed_bundle_entries(
            components[rico.mass_driver.SPRITE_INDEX]
        )
        self.assertEqual(len(actor_banks), 2)
        self.assertEqual(len(sprite_banks), 2)
        self.assertEqual(
            hashlib.sha256(actor_banks[rico.HUB_MARKER_ACTOR_BANK]).hexdigest(),
            rico.HUB_MARKER_ACTOR_BANK_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(sprite_banks[rico.HUB_MARKER_ACTOR_BANK]).hexdigest(),
            rico.HUB_MARKER_SPRITE_BANK_SHA256,
        )

        source_field = parse_field(self.hub_source)
        source_editor = AtelScript(components[rico.SCRIPT_INDEX])
        native_record = rico.mass_driver._field_actor_record(0x01E0, 0, 0, 0)
        record_start = 0x190 + 10 * 16
        self.assertEqual(
            source_field.header[record_start : record_start + 16],
            native_record,
        )
        native_init = bytes.fromhex(
            "0B 01 80 2A FE 5E 02 80 FE 03 55 95 00"
        )
        self.assertEqual(source_editor.get_script_pointer(10, 0), 0x0CEA)
        self.assertEqual(
            source_editor.bytecode[0x0CEA : 0x0CEA + len(native_init)],
            native_init,
        )

    def test_seven_markers_are_inserted_as_native_actor_records(self) -> None:
        source = parse_field(self.hub_source)
        output = parse_field(self.hub_outputs[1])
        source_editor = AtelScript(source.parts[rico.SCRIPT_INDEX].data)
        output_editor = AtelScript(output.parts[rico.SCRIPT_INDEX].data)
        source_records = struct.unpack_from("<H", source.header, 0x18C)[0]
        output_records = struct.unpack_from("<H", output.header, 0x18C)[0]

        self.assertEqual(source_editor.entity_count, 11)
        self.assertEqual(source_records, 12)
        self.assertEqual(output_editor.entity_count, 17)
        self.assertEqual(output_records, 18)
        self.assertEqual(len(rico.HUB_MARKERS), 7)
        self.assertEqual(len(output.header), len(source.header) + 6 * 16)
        self.assertEqual(
            tuple(marker.chapter_id for marker in rico.HUB_MARKERS),
            tuple(range(1, 8)),
        )
        self.assertEqual(
            tuple(
                rico.HUB_MARKER_FIRST_ENTITY + marker.chapter_id - 1
                for marker in rico.HUB_MARKERS
            ),
            tuple(range(10, 17)),
        )

        native_record = bytearray(
            rico.mass_driver._field_actor_record(0x01E0, 0, 0, 0)
        )
        for marker in rico.HUB_MARKERS:
            with self.subTest(chapter=marker.chapter_id):
                expected = bytearray(native_record)
                struct.pack_into("<h", expected, 8, marker.x)
                struct.pack_into("<h", expected, 12, marker.z)
                entity = rico.HUB_MARKER_FIRST_ENTITY + marker.chapter_id - 1
                start = 0x190 + entity * 16
                self.assertEqual(
                    output.header[start : start + 16],
                    bytes(expected),
                )
                self.assertEqual(
                    _pointed_body(output_editor, entity, 0),
                    rico._hub_marker_init(marker),
                )

        # Insertion occurs before field 719's one spare actor record.
        source_spare = source.header[0x190 + 11 * 16 : 0x190 + 12 * 16]
        output_spare = output.header[0x190 + 17 * 16 : 0x190 + 18 * 16]
        self.assertEqual(output_spare, source_spare)

    def test_native_path_is_preserved_while_ending_story_entities_are_retired(self) -> None:
        source = parse_field(self.hub_source)
        output = parse_field(self.hub_outputs[1])
        source_components = [part.data for part in source.parts]
        output_components = [part.data for part in output.parts]
        source_editor = AtelScript(source_components[rico.SCRIPT_INDEX])
        output_editor = AtelScript(output_components[rico.SCRIPT_INDEX])

        for index in range(len(source_components)):
            if index not in (rico.SCRIPT_INDEX, rico.DIALOGUE_INDEX):
                self.assertEqual(
                    output_components[index],
                    source_components[index],
                    f"retail Path component {index} changed",
                )
        self.assertEqual(
            output_editor.bytecode[: source_editor.bytecode_size],
            source_editor.bytecode,
        )
        for script_index in (0, 1):
            source_pc = source_editor.get_script_pointer(
                rico.HUB_PATH_ENTITY,
                script_index,
            )
            self.assertEqual(
                output_editor.get_script_pointer(
                    rico.HUB_PATH_ENTITY,
                    script_index,
                ),
                source_pc,
            )

        stop_pc = output_editor.get_script_pointer(0, 2)
        self.assertEqual(output_editor.bytecode[stop_pc : stop_pc + 1], b"\x00")
        for entity in (2, 3, 4, 5, 7, 8, 9):
            self.assertEqual(
                _pointed_body(output_editor, entity, 0),
                rico.INERT_HIDDEN_INIT,
            )
            for script_index in range(1, 32):
                self.assertEqual(
                    output_editor.get_script_pointer(entity, script_index),
                    stop_pc,
                )
        for script_index in range(2, 32):
            self.assertEqual(
                output_editor.get_script_pointer(
                    rico.HUB_PATH_ENTITY,
                    script_index,
                ),
                stop_pc,
            )

        director_pc = output_editor.get_script_pointer(0, 0)
        director = rico._sanitized_director(rico.HUB_MUSIC)
        self.assertEqual(
            output_editor.bytecode[director_pc : director_pc + len(director)],
            director,
        )
        self.assertEqual(output_editor.get_script_pointer(0, 1), stop_pc)
        self.assertEqual(
            output_components[rico.DIALOGUE_INDEX],
            rico._dialogue_data(
                rico._hub_dialogue_layout(self.chapters),
                fit_windows=True,
            ),
        )

    def test_hub_entry_is_walkable_clear_and_rico_only(self) -> None:
        output = parse_field(self.hub_outputs[1])
        editor = AtelScript(output.parts[rico.SCRIPT_INDEX].data)
        x, z, triangle = rico.HUB_ENTRY_POSITION
        triangles = rico._walkmesh_layer(output.parts[1].data, 0)
        self.assertTrue(rico._point_inside_triangle((x, z), triangles[triangle]))

        record = 0x190 + 1 * 16
        self.assertEqual(struct.unpack_from("<h", output.header, record + 8)[0], x)
        self.assertEqual(struct.unpack_from("<h", output.header, record + 12)[0], z)
        self.assertEqual(
            _pointed_body(editor, 1, 0),
            rico._normalized_party_init(rico.RICO_ID, (x, z)),
        )
        self.assertEqual(_pointed_body(editor, 1, 1), b"\xA7\x00")

        hub_setup = rico._hub_launch_body(rico.HUB_FIELDS[1])
        adult_setup = rico._party_setup(rico.HUB_PARTY)
        self.assertTrue(hub_setup.startswith(adult_setup))
        for character in range(11):
            self.assertEqual(
                adult_setup.count(
                    b"\xFE\x19" + bytes((character,))
                ),
                1,
            )
        self.assertEqual(
            adult_setup.count(b"\xFE\x18\x05\xFE\x1A"),
            1,
        )
        self.assertNotIn(b"\xFE\x18\x0A\xFE\x1A", adult_setup)

        effective_x = rico.HUB_MARKER_HALF_WIDTH * 2 + 0x10
        effective_z = rico.HUB_MARKER_HALF_DEPTH * 2 + 0x10
        for marker in rico.HUB_MARKERS:
            with self.subTest(chapter=marker.chapter_id):
                self.assertTrue(
                    rico._point_inside_triangle(
                        (marker.x, marker.z),
                        triangles[marker.triangle],
                    )
                )
                self.assertFalse(
                    abs(x - marker.x) <= effective_x
                    and abs(z - marker.z) <= effective_z
                )


class SephirotHubContentMenuTests(unittest.TestCase):
    """Cover the opt-in memory cube used by the unified content selector."""

    CONTENT_MENU_FIELD = 241

    @classmethod
    def setUpClass(cls) -> None:
        cls.chapters = rico.load_chapters()
        cls.hub_source = _audit_resource(
            rico._field_bundle_id(rico.HUB_DONOR_FIELD)
        )
        cls.save_source = _save_point_donor_resource()
        cls.output = rico._build_hub_bundle(
            cls.hub_source,
            rico.CHAPTER_FIELDS[2],
            cls.chapters,
            content_menu_field=cls.CONTENT_MENU_FIELD,
            save_point_donor_bundle=cls.save_source,
        )

    def test_opt_in_cube_adds_one_entity_record_and_exact_native_assets(self) -> None:
        source = parse_field(self.hub_source)
        output = parse_field(self.output)
        source_components = [part.data for part in source.parts]
        output_components = [part.data for part in output.parts]
        source_editor = AtelScript(source_components[rico.SCRIPT_INDEX])
        output_editor = AtelScript(output_components[rico.SCRIPT_INDEX])

        self.assertEqual(source_editor.entity_count, 11)
        self.assertEqual(output_editor.entity_count, 18)
        self.assertEqual(struct.unpack_from("<H", output.header, 0x18C)[0], 19)
        self.assertEqual(len(output.header), len(source.header) + 7 * 16)
        self.assertEqual(rico.HUB_SAVE_ENTITY, 17)

        actor_banks = rico.mass_driver._indexed_bundle_entries(
            output_components[rico.mass_driver.ACTOR_INDEX]
        )
        sprite_banks = rico.mass_driver._indexed_bundle_entries(
            output_components[rico.mass_driver.SPRITE_INDEX]
        )
        self.assertEqual(len(actor_banks), 3)
        self.assertEqual(len(sprite_banks), 3)
        self.assertEqual(
            (
                len(actor_banks[rico.HUB_SAVE_ACTOR_BANK]),
                hashlib.sha256(
                    actor_banks[rico.HUB_SAVE_ACTOR_BANK]
                ).hexdigest(),
            ),
            (rico.HUB_SAVE_ACTOR_SIZE, rico.HUB_SAVE_ACTOR_SHA256),
        )
        self.assertEqual(
            (
                len(sprite_banks[rico.HUB_SAVE_ACTOR_BANK]),
                hashlib.sha256(
                    sprite_banks[rico.HUB_SAVE_ACTOR_BANK]
                ).hexdigest(),
            ),
            (rico.HUB_SAVE_SPRITE_SIZE, rico.HUB_SAVE_SPRITE_SHA256),
        )
        self.assertEqual(
            tuple(
                struct.unpack_from("<4H", output.header, bank * 8)
                for bank in range(3)
            ),
            ((832, 0, 0, 0), (896, 0, 0, 0), rico.HUB_SAVE_VRAM_MAPPING),
        )
        _vram, uploads = rico.mass_driver._reconstruct_field_graphics_vram(
            _audit_resource(rico._field_bundle_id(rico.HUB_DONOR_FIELD) + 1),
            label="Rico Path of Sephirot hub",
        )
        save_vram_x, save_vram_y = rico.HUB_SAVE_VRAM_MAPPING[:2]
        save_vram_width, save_vram_height = rico.HUB_SAVE_VRAM_SIZE
        self.assertTrue(
            all(
                save_vram_x + save_vram_width <= upload_x
                or upload_x + upload_width <= save_vram_x
                or save_vram_y + save_vram_height <= upload_y
                or upload_y + upload_height <= save_vram_y
                for upload_x, upload_y, upload_width, upload_height in uploads
            )
        )

        x, z, _triangle = rico.HUB_SAVE_POSITION
        record = 0x190 + rico.HUB_SAVE_ENTITY * 16
        self.assertEqual(
            output.header[record : record + 16],
            rico.mass_driver._field_actor_record(0x01E0, x, z, 0),
        )
        # All inserted dynamic records still precede field 719's spare static
        # record; adding the cube cannot overwrite the Path model carrier.
        self.assertEqual(
            output.header[0x190 + 18 * 16 : 0x190 + 19 * 16],
            source.header[0x190 + 11 * 16 : 0x190 + 12 * 16],
        )
        for index in range(len(source_components)):
            if index not in (
                rico.mass_driver.ACTOR_INDEX,
                rico.mass_driver.SPRITE_INDEX,
                rico.SCRIPT_INDEX,
                rico.DIALOGUE_INDEX,
            ):
                self.assertEqual(output_components[index], source_components[index])

    def test_memory_cube_is_walkable_clear_and_owns_the_native_save_protocol(
        self,
    ) -> None:
        output = parse_field(self.output)
        editor = AtelScript(output.parts[rico.SCRIPT_INDEX].data)
        x, z, triangle = rico.HUB_SAVE_POSITION
        triangles = rico._walkmesh_layer(output.parts[1].data, 0)
        self.assertTrue(rico._point_inside_triangle((x, z), triangles[triangle]))
        self.assertGreater(abs(x - rico.HUB_ENTRY_POSITION[0]), 0x80)
        for marker in rico.HUB_MARKERS:
            self.assertFalse(
                abs(x - marker.x) <= 0x80 and abs(z - marker.z) <= 0x80
            )

        self.assertEqual(
            _pointed_body(editor, rico.HUB_SAVE_ENTITY, 0),
            rico._hub_save_point_init(),
        )
        self.assertEqual(
            _pointed_body(editor, rico.HUB_SAVE_ENTITY, 1),
            rico.HUB_SAVE_UPDATE,
        )
        action_pc = editor.get_script_pointer(rico.HUB_SAVE_ENTITY, 2)
        action = _pointed_body(editor, rico.HUB_SAVE_ENTITY, 2)
        dialogue_id = len(rico._hub_dialogue_layout(self.chapters))
        self.assertEqual(
            action,
            rico._build_hub_save_point_action(
                action_pc,
                dialogue_id,
                self.CONTENT_MENU_FIELD,
            ),
        )
        self.assertEqual(
            action.count(rico.HUB_SAVE_NATIVE_ACTION[:-1]),
            1,
        )
        self.assertEqual(action.count(bytes.fromhex("FE 55 FE 87")), 1)
        return_route = (
            rico.mass_driver._set_variable_s16(rico.PLAYABLE_STATE_VARIABLE, 0)
            + rico._change_field(self.CONTENT_MENU_FIELD, 0)
            + b"\x5B"
        )
        self.assertEqual(action.count(return_route), 1)
        self.assertEqual(
            action.count(rico._choice_dialog(dialogue_id) + b"\xA9\x12\x9C"),
            1,
        )

        collision_pc = editor.get_script_pointer(rico.HUB_SAVE_ENTITY, 3)
        self.assertEqual(
            _pointed_body(editor, rico.HUB_SAVE_ENTITY, 3),
            rico._hub_save_point_collision(collision_pc),
        )
        self.assertEqual(
            rico._hub_save_point_collision(0x1000),
            bytes.fromhex(
                "FE 99 00 02 0E 04 00 00 40 11 10 "
                "74 50 80 36 0E 04 00"
            ),
        )

    def test_memory_cube_choice_is_appended_without_shifting_chapter_ids(
        self,
    ) -> None:
        dialogue = parse_field(self.output).parts[rico.DIALOGUE_INDEX].data
        texts = _lenient_dialogue_texts(dialogue)
        ordinary_layout = rico._hub_dialogue_layout(self.chapters)
        self.assertEqual(len(texts), len(ordinary_layout) + 1)
        self.assertEqual(
            texts[:-1],
            tuple(rico._reflow_dialogue_text(text) for text in ordinary_layout),
        )
        self.assertEqual(
            texts[-1],
            rico._reflow_dialogue_text(rico.HUB_SAVE_MENU_CHOICE),
        )
        self.assertEqual(
            rico._hub_selection_exposition_ids(self.chapters)[1],
            (7, 8),
        )

    def test_content_menu_target_and_cube_donor_are_an_atomic_opt_in(self) -> None:
        with self.assertRaisesRegex(rico.RicoArcBuildError, "supplied together"):
            rico._build_hub_bundle(
                self.hub_source,
                rico.CHAPTER_FIELDS[2],
                self.chapters,
                content_menu_field=self.CONTENT_MENU_FIELD,
            )
        with self.assertRaisesRegex(rico.RicoArcBuildError, "supplied together"):
            rico._build_hub_bundle(
                self.hub_source,
                rico.CHAPTER_FIELDS[2],
                self.chapters,
                save_point_donor_bundle=self.save_source,
            )


class SephirotHubRoutingTests(RicoChapterSelectV2Fixtures):
    def test_every_marker_owns_the_complete_prelaunch_exposition(self) -> None:
        expected_blocks = rico._hub_dialogue_layout(self.chapters)
        expected_ids = rico._hub_selection_exposition_ids(self.chapters)
        self.assertEqual(
            tuple(len(expected_ids[chapter_id]) for chapter_id in range(1, 8)),
            (2, 2, 2, 2, 2, 2, 2),
        )
        for disc in (1, 2):
            dialogue = parse_field(self.hub_outputs[disc]).parts[
                rico.DIALOGUE_INDEX
            ].data
            self.assertEqual(
                _lenient_dialogue_texts(dialogue),
                tuple(
                    rico._reflow_dialogue_text(text)
                    for text in expected_blocks
                ),
            )
        for chapter in self.chapters:
            ids = expected_ids[chapter.chapter_id]
            exposition = rico._chapter_selection_exposition(chapter)
            self.assertEqual(
                tuple(expected_blocks[block_id] for block_id in ids),
                exposition,
            )
            self.assertEqual(
                exposition,
                (chapter.blocks[0], chapter.selection_exposition),
            )
            self.assertNotIn(chapter.blocks[1], exposition)
            self.assertTrue(
                all("objective" not in text.casefold() for text in exposition)
            )

    def test_each_destination_is_silent_after_prelaunch_exposition(self) -> None:
        for disc in (1, 2):
            for chapter in self.chapters:
                with self.subTest(disc=disc, chapter=chapter.chapter_id):
                    (
                        _source_editor,
                        output_editor,
                        _contract,
                        _first_controller,
                        _exit_entity,
                    ) = self._chapter_layout(disc, chapter.chapter_id)
                    director_pc = output_editor.get_script_pointer(0, 0)
                    director = (
                        rico._chapter_two_director(chapter.music)
                        if chapter.chapter_id == 2
                        else rico._sanitized_director(chapter.music)
                    )
                    silent_pc = output_editor.get_script_pointer(0, 1)
                    silent_update = rico._playable_silent_update()

                    self.assertEqual(
                        output_editor.bytecode[
                            director_pc : director_pc + len(director)
                        ],
                        director,
                    )
                    self.assertEqual(
                        output_editor.bytecode[
                            silent_pc : silent_pc + len(silent_update)
                        ],
                        silent_update,
                    )
                    self.assertEqual(silent_update, b"\x5B")

    def test_each_marker_is_explicit_cross_and_cancel_safe_on_both_discs(self) -> None:
        cross_poll = b"\x31" + struct.pack("<H", rico.PAD_MASK_CROSS)
        for disc in (1, 2):
            editor = AtelScript(
                parse_field(self.hub_outputs[disc])
                .parts[rico.SCRIPT_INDEX]
                .data
            )
            stop_pc = editor.get_script_pointer(0, 2)
            for marker in rico.HUB_MARKERS:
                with self.subTest(disc=disc, chapter=marker.chapter_id):
                    entity = rico.HUB_MARKER_FIRST_ENTITY + marker.chapter_id - 1
                    action_pc = editor.get_script_pointer(entity, 2)
                    action = _pointed_body(editor, entity, 2)
                    target = rico.CHAPTER_FIELDS[disc][marker.chapter_id]
                    launch = rico._chapter_launch_body(marker.chapter_id, target)

                    self.assertEqual(
                        action,
                        rico._build_hub_marker_action(
                            action_pc,
                            marker,
                            target,
                            rico._hub_selection_exposition_ids(self.chapters)[
                                marker.chapter_id
                            ],
                        ),
                    )
                    self.assertEqual(action.count(cross_poll), 4)
                    self.assertEqual(
                        action.count(rico._choice_dialog(marker.chapter_id - 1)),
                        1,
                    )
                    self.assertIn(
                        rico._choice_dialog(marker.chapter_id - 1)
                        + b"\xA9\x12\x9C",
                        action,
                    )
                    self.assertEqual(action.count(launch), 1)
                    self.assertNotIn(b"\xFE\xCD", action)

                    launch_offset = action.index(launch)
                    comparison = (
                        b"\x02"
                        + struct.pack("<H", rico.MENU_SELECTION_VARIABLE)
                        + struct.pack("<h", 1)
                        + b"\x40"
                    )
                    compare_offset = action.rfind(comparison, 0, launch_offset)
                    self.assertGreaterEqual(compare_offset, 0)
                    cancel_pc = struct.unpack_from(
                        "<H",
                        action,
                        compare_offset + len(comparison),
                    )[0]
                    exposition_offset = compare_offset + 8
                    exposition = rico._prelaunch_exposition(
                        rico._hub_selection_exposition_ids(self.chapters)[
                            marker.chapter_id
                        ],
                        routine_pc=action_pc + exposition_offset,
                    )
                    self.assertTrue(
                        action.startswith(exposition, exposition_offset)
                    )
                    self.assertEqual(
                        launch_offset,
                        exposition_offset + len(exposition),
                    )
                    self.assertEqual(
                        cancel_pc,
                        action_pc + launch_offset + len(launch),
                    )
                    self.assertNotIn(
                        b"\xFE\x53",
                        action[exposition_offset:launch_offset],
                    )
                    self.assertTrue(
                        action[launch_offset + len(launch) :].endswith(
                            b"\xFE\x53\x00"
                        )
                    )

                    # The light is non-colliding and owns no automatic or
                    # collision action; only script 2 can launch a chapter.
                    self.assertTrue(
                        _pointed_body(editor, entity, 0).endswith(
                            b"\x20\x01\x80\x00"
                        )
                    )
                    for script_index in (1, 3):
                        self.assertEqual(
                            editor.get_script_pointer(entity, script_index),
                            stop_pc,
                        )

    def test_disc_one_and_two_hubs_have_exact_local_routes(self) -> None:
        for disc in (1, 2):
            editor = AtelScript(
                parse_field(self.hub_outputs[disc])
                .parts[rico.SCRIPT_INDEX]
                .data
            )
            for marker in rico.HUB_MARKERS:
                entity = rico.HUB_MARKER_FIRST_ENTITY + marker.chapter_id - 1
                action = _pointed_body(editor, entity, 2)
                expected_field = rico.CHAPTER_FIELDS[disc][marker.chapter_id]
                self.assertEqual(
                    action.count(rico._change_field(expected_field, 0)),
                    1,
                )
                if marker.chapter_id == 2:
                    self.assertNotIn(rico._change_field(68, 0), action)
                other_disc = 2 if disc == 1 else 1
                self.assertNotIn(
                    rico._change_field(
                        rico.CHAPTER_FIELDS[other_disc][marker.chapter_id],
                        0,
                    ),
                    action,
                )

        disc1 = parse_field(self.hub_outputs[1])
        disc2 = parse_field(self.hub_outputs[2])
        self.assertEqual(disc1.header[0x18C:], disc2.header[0x18C:])
        for index, (left, right) in enumerate(zip(disc1.parts, disc2.parts, strict=True)):
            if index == rico.SCRIPT_INDEX:
                self.assertEqual(
                    _normalize_local_routes(left.data),
                    _normalize_local_routes(right.data),
                )
            else:
                self.assertEqual(left.data, right.data)


class ChapterCompletionRoutingTests(RicoChapterSelectV2Fixtures):
    def test_completion_choice_pages_keep_requested_wording_and_layout(self) -> None:
        expected = {
            rico.PLAYABLE_NEXT_OR_HUB_CHOICE: (
                "<Opcode:01:FF>Where will Rico go?\n"
                "     Continue to Next Chapter\n"
                "     Return to Chapter Select<Close>"
            ),
            rico.PLAYABLE_FINAL_HUB_CHOICE: (
                "Rico's Arc is complete.<New>"
                "<Opcode:01:FF>Where will Rico go?\n"
                "     Return to Chapter Select\n"
                "     Remain Here<Close>"
            ),
        }
        for source, exact_text in expected.items():
            with self.subTest(choice=exact_text):
                laid_out = rico._reflow_dialogue_text(source)
                self.assertEqual(laid_out, exact_text)
                self.assertEqual(rico._dialogue_layout_issues(laid_out), ())
                choice_page = laid_out.removesuffix("<Close>").split("<New>")[-1]
                rows = choice_page.split("\n")
                self.assertEqual(len(rows), 3)
                self.assertTrue(rows[0].startswith(rico.DIALOGUE_CHOICE_START))
                self.assertTrue(all(row.strip() for row in rows[1:]))

    def test_every_chapter_completion_is_door_only_and_cancel_safe(self) -> None:
        for disc in (1, 2):
            for chapter_id in range(1, 8):
                with self.subTest(disc=disc, chapter=chapter_id):
                    (
                        _source_editor,
                        output_editor,
                        contract,
                        first_controller,
                        exit_entity,
                    ) = self._chapter_layout(disc, chapter_id)
                    exit_pc = output_editor.get_script_pointer(exit_entity, 2)
                    interaction_actions = tuple(
                        _pointed_body(
                            output_editor,
                            first_controller + index,
                            2,
                        )
                        for index, _interaction in enumerate(contract.interactions)
                    )
                    exit_action = _pointed_body(output_editor, exit_entity, 2)
                    source_dialogue_count = (
                        struct.unpack_from(
                            "<I",
                            parse_field(self.chapter_sources[chapter_id])
                            .parts[rico.DIALOGUE_INDEX]
                            .data,
                            0,
                        )[0]
                        + 1
                    )
                    choice_text = (
                        rico.PLAYABLE_FINAL_HUB_CHOICE
                        if chapter_id == 7
                        else rico.PLAYABLE_NEXT_OR_HUB_CHOICE
                    )
                    choice_id = (
                        source_dialogue_count
                        + len(self.chapters[chapter_id - 1].blocks)
                        + rico._playable_custom_texts(contract).index(choice_text)
                    )
                    choice_opcode = rico._choice_dialog(choice_id)
                    hub_launch = rico._hub_launch_body(rico.HUB_FIELDS[disc])

                    self.assertTrue(contract.completion_at_exit)
                    self.assertFalse(
                        any(
                            stage.completes_chapter
                            for interaction in contract.interactions
                            for stage in interaction.stages
                        )
                    )
                    if contract.exit_transition is not None:
                        self.assertEqual(chapter_id, 1)
                        self.assertEqual(exit_action.count(choice_opcode), 0)
                        self.assertEqual(exit_action.count(hub_launch), 0)
                        self.assertEqual(
                            exit_action.count(
                                rico._change_field(
                                    rico.CHAPTER_ONE_FIREWOOD_FIELD,
                                    0,
                                )
                            ),
                            1,
                        )
                        self.assertTrue(
                            all(
                                action.count(choice_opcode) == 0
                                and action.count(hub_launch) == 0
                                and action.count(
                                    rico._change_field(
                                        rico.CHAPTER_ONE_FIREWOOD_FIELD,
                                        0,
                                    )
                                )
                                == 0
                                for action in interaction_actions
                            )
                        )
                        continue
                    self.assertEqual(exit_action.count(choice_opcode), 1)
                    self.assertEqual(exit_action.count(hub_launch), 1)
                    self.assertTrue(
                        all(
                            action.count(choice_opcode) == 0
                            and action.count(hub_launch) == 0
                            for action in interaction_actions
                        )
                    )

                    choice_at = exit_action.index(choice_opcode)
                    if chapter_id in (4, 7):
                        door_entity, open_script = (
                            (
                                rico.CHAPTER_FOUR_DOOR_ENTITY,
                                rico.CHAPTER_FOUR_DOOR_OPEN_SCRIPT,
                            )
                            if chapter_id == 4
                            else (
                                rico.CHAPTER_SEVEN_DOOR_ENTITY,
                                rico.CHAPTER_SEVEN_DOOR_OPEN_SCRIPT,
                            )
                        )
                        native_open = b"\x09" + bytes(
                            (door_entity, open_script | 0x20)
                        )
                        self.assertEqual(exit_action.count(native_open), 1)
                        self.assertLess(exit_action.index(native_open), choice_at)
                    self.assertEqual(
                        exit_action[
                            choice_at : choice_at + len(choice_opcode) + 3
                        ],
                        choice_opcode + b"\xA9\x12\x9C",
                    )
                    branch_at = choice_at + len(choice_opcode) + 3

                    def comparison(at: int) -> tuple[int, int]:
                        self.assertEqual(exit_action[at], 0x02)
                        self.assertEqual(
                            struct.unpack_from("<H", exit_action, at + 1)[0],
                            rico.MENU_SELECTION_VARIABLE,
                        )
                        self.assertEqual(exit_action[at + 5], 0x40)
                        return (
                            struct.unpack_from("<H", exit_action, at + 3)[0],
                            struct.unpack_from("<H", exit_action, at + 6)[0],
                        )

                    first_selection, first_target_pc = comparison(branch_at)
                    self.assertEqual(first_selection, 1)

                    if chapter_id < 7:
                        next_chapter = self.chapters[chapter_id]
                        next_exposition = rico._chapter_selection_exposition(
                            next_chapter
                        )
                        custom_texts = rico._playable_custom_texts(
                            contract,
                            additional_texts=next_exposition,
                        )
                        next_exposition_ids = tuple(
                            source_dialogue_count
                            + len(self.chapters[chapter_id - 1].blocks)
                            + custom_texts.index(text)
                            for text in next_exposition
                        )
                        next_launch = rico._chapter_launch_body(
                            chapter_id + 1,
                            rico.CHAPTER_FIELDS[disc][chapter_id + 1],
                        )
                        self.assertEqual(exit_action.count(next_launch), 1)
                        self.assertTrue(
                            all(
                                action.count(next_launch) == 0
                                for action in interaction_actions
                            )
                        )
                        exposition_at = branch_at + 8
                        exposition = rico._prelaunch_exposition(
                            next_exposition_ids,
                            routine_pc=exit_pc + exposition_at,
                        )
                        self.assertTrue(
                            exit_action.startswith(exposition, exposition_at)
                        )
                        next_at = exposition_at + len(exposition)
                        self.assertTrue(
                            exit_action.startswith(next_launch, next_at)
                        )
                        self.assertNotIn(
                            b"\xFE\x53",
                            exit_action[exposition_at:next_at],
                        )
                        hub_comparison_at = next_at + len(next_launch)
                        self.assertEqual(
                            first_target_pc,
                            exit_pc + hub_comparison_at,
                        )
                        second_selection, stay_target_pc = comparison(
                            hub_comparison_at
                        )
                        self.assertEqual(second_selection, 2)
                        hub_at = hub_comparison_at + 8
                        self.assertTrue(exit_action.startswith(hub_launch, hub_at))
                        stay_at = hub_at + len(hub_launch)
                        self.assertEqual(stay_target_pc, exit_pc + stay_at)
                        routed = {
                            selection: (
                                "next"
                                if selection == first_selection
                                else (
                                    "hub"
                                    if selection == second_selection
                                    else "stay"
                                )
                            )
                            for selection in (0, 1, 2, 3, 0xFFFF)
                        }
                        self.assertEqual(
                            routed,
                            {
                                0: "stay",
                                1: "next",
                                2: "hub",
                                3: "stay",
                                0xFFFF: "stay",
                            },
                        )
                    else:
                        hub_at = branch_at + 8
                        self.assertTrue(exit_action.startswith(hub_launch, hub_at))
                        stay_at = hub_at + len(hub_launch)
                        self.assertEqual(first_target_pc, exit_pc + stay_at)
                        routed = {
                            selection: (
                                "hub" if selection == first_selection else "stay"
                            )
                            for selection in (0, 1, 2, 3, 0xFFFF)
                        }
                        self.assertEqual(
                            routed,
                            {
                                0: "stay",
                                1: "hub",
                                2: "stay",
                                3: "stay",
                                0xFFFF: "stay",
                            },
                        )
                        # Chapter 7 has Return to Chapter Select / Remain Here. A
                        # synthetic chapter-8 numeric field must never appear.
                        would_be_chapter_eight = max(
                            rico.CHAPTER_FIELDS[disc].values()
                        ) + 1
                        for action in interaction_actions:
                            self.assertNotIn(
                                rico._change_field(would_be_chapter_eight, 0),
                                action,
                            )
                        self.assertNotIn(
                            rico._change_field(would_be_chapter_eight, 0),
                            exit_action,
                        )

                    before_finish = b""
                    exit_door = rico.PLAYABLE_NATIVE_EXIT_DOORS.get(chapter_id)
                    if exit_door is not None:
                        door_entity, _open_script, close_script = exit_door
                        before_finish = b"\x09" + bytes(
                            (door_entity, close_script | 0x20)
                        )
                    expected_stay = before_finish + rico._playable_action_finish(
                        exit_pc + stay_at + len(before_finish)
                    )
                    self.assertTrue(exit_action.startswith(expected_stay, stay_at))

    def test_chapter_two_bedroom_loop_shadows_progress_without_completing(self) -> None:
        self.assertEqual(rico.CHAPTER_TWO_PERSISTENT_STATE_VARIABLE, 0x03EC)
        self.assertEqual(rico.CHAPTER_TWO_HAMMER_STATE_VARIABLE, 0x03EE)
        self.assertEqual(rico.CHAPTER_TWO_HAMMER_ARRIVED_BIT, 0)
        local_clear = rico.mass_driver._set_variable_s16(
            rico.PLAYABLE_STATE_VARIABLE,
            0,
        )
        persistent_clear = rico.mass_driver._set_variable_s16(
            rico.CHAPTER_TWO_PERSISTENT_STATE_VARIABLE,
            0,
        )
        hammer_clear = rico.mass_driver._set_variable_s16(
            rico.CHAPTER_TWO_HAMMER_STATE_VARIABLE,
            0,
        )

        for disc in (1, 2):
            with self.subTest(disc=disc):
                chapter_launch = rico._chapter_launch_body(
                    2,
                    rico.CHAPTER_FIELDS[disc][2],
                )
                field_change = rico._change_field(
                    rico.CHAPTER_FIELDS[disc][2],
                    0,
                )
                self.assertNotIn(rico._change_field(68, 0), chapter_launch)
                self.assertEqual(chapter_launch.count(local_clear), 1)
                self.assertEqual(chapter_launch.count(persistent_clear), 1)
                self.assertEqual(chapter_launch.count(hammer_clear), 1)
                self.assertLess(
                    chapter_launch.index(local_clear),
                    chapter_launch.index(persistent_clear),
                )
                self.assertLess(
                    chapter_launch.index(persistent_clear),
                    chapter_launch.index(hammer_clear),
                )
                self.assertLess(
                    chapter_launch.index(hammer_clear),
                    chapter_launch.index(field_change),
                )

                hub_launch = rico._hub_launch_body(rico.HUB_FIELDS[disc])
                self.assertEqual(hub_launch.count(local_clear), 1)
                self.assertEqual(hub_launch.count(persistent_clear), 1)
                self.assertEqual(hub_launch.count(hammer_clear), 1)
                self.assertLess(
                    hub_launch.index(local_clear),
                    hub_launch.index(persistent_clear),
                )
                self.assertLess(
                    hub_launch.index(persistent_clear),
                    hub_launch.index(hammer_clear),
                )

                output_editor = AtelScript(
                    parse_field(self.chapter_outputs[disc, 2])
                    .parts[rico.SCRIPT_INDEX]
                    .data
                )
                director_pc = output_editor.get_script_pointer(0, 0)
                director = rico._chapter_two_director(self.chapters[1].music)
                self.assertEqual(
                    output_editor.bytecode[
                        director_pc : director_pc + len(director)
                    ],
                    director,
                )
                self.assertIn(rico._restore_chapter_two_state(), director)
                self.assertNotIn(hammer_clear, director)

                door_action = _pointed_body(
                    output_editor,
                    rico.CHAPTER_TWO_MAIN_DOOR_ENTITY,
                    2,
                )
                self.assertEqual(
                    door_action,
                    rico._chapter_two_main_bedroom_action(
                        rico.CHAPTER_TWO_BEDROOM_FIELD
                    ),
                )
                self.assertTrue(
                    door_action.startswith(
                        rico._copy_chapter_two_state_to_persistent()
                    )
                )
                for bit in range(1, 8):
                    self.assertNotIn(
                        rico.mass_driver._set_var_bit(
                            rico.PLAYABLE_STATE_VARIABLE,
                            bit,
                        ),
                        door_action,
                    )
                self.assertNotIn(hub_launch, door_action)
                self.assertNotIn(hammer_clear, door_action)
                self.assertNotIn(
                    rico._chapter_launch_body(
                        3,
                        rico.CHAPTER_FIELDS[disc][3],
                    ),
                    door_action,
                )

        chapter_three_launch = rico._chapter_launch_body(
            3,
            rico.CHAPTER_FIELDS[1][3],
        )
        self.assertNotIn(persistent_clear, chapter_three_launch)
        self.assertNotIn(hammer_clear, chapter_three_launch)

    def test_unified_disc2_override_routes_native_e2_to_dummy_field_67(self) -> None:
        self.assertEqual(rico.CHAPTER_TWO_BEDROOM_FIELD, 379)
        self.assertEqual(rico.UNIFIED_DISC2_CHAPTER_TWO_BEDROOM_FIELD, 67)
        chapter = self.chapters[1]
        unified = rico._build_playable_chapter_bundle(
            self.chapter_sources[2],
            chapter,
            rico.HUB_FIELDS[2],
            self.chapters[2],
            chapter_two_bedroom_field=(
                rico.UNIFIED_DISC2_CHAPTER_TWO_BEDROOM_FIELD
            ),
        )
        standalone = self.chapter_outputs[2, 2]
        unified_field = parse_field(unified)
        standalone_field = parse_field(standalone)
        unified_editor = AtelScript(
            unified_field.parts[rico.SCRIPT_INDEX].data
        )
        door_action = _pointed_body(
            unified_editor,
            rico.CHAPTER_TWO_MAIN_DOOR_ENTITY,
            2,
        )
        self.assertEqual(
            door_action,
            rico._chapter_two_main_bedroom_action(
                rico.UNIFIED_DISC2_CHAPTER_TWO_BEDROOM_FIELD
            ),
        )
        self.assertIn(
            rico._immediate(rico.UNIFIED_DISC2_CHAPTER_TWO_BEDROOM_FIELD)
            + rico._immediate(0)
            + b"\x5B",
            door_action,
        )
        self.assertNotIn(
            rico._immediate(rico.CHAPTER_TWO_BEDROOM_FIELD)
            + rico._immediate(0)
            + b"\x5B",
            door_action,
        )
        self.assertEqual(
            unified_field.header[0x18C:],
            standalone_field.header[0x18C:],
        )
        for index, (unified_part, standalone_part) in enumerate(
            zip(unified_field.parts, standalone_field.parts, strict=True)
        ):
            if index == rico.SCRIPT_INDEX:
                self.assertEqual(
                    _normalize_local_routes(unified_part.data),
                    _normalize_local_routes(standalone_part.data),
                )
            else:
                self.assertEqual(unified_part.data, standalone_part.data)

    def test_chapter_one_uses_a_fully_live_three_field_aftermath(self) -> None:
        contract = rico._playable_chapter_contract(1)
        transition = contract.exit_transition
        self.assertIsNotNone(transition)
        assert transition is not None

        self.assertEqual(rico.CHAPTER_ONE_FIREWOOD_FIELD, 377)
        self.assertEqual(rico.CHAPTER_ONE_FIREWOOD_DONOR_FIELD, 199)
        self.assertEqual(rico.CHAPTER_ONE_AFTERMATH_FIELD, 376)
        self.assertEqual(rico.CHAPTER_ONE_AFTERMATH_DONOR_FIELD, 229)
        self.assertEqual(rico.CHAPTER_ONE_FUNERAL_FIELD, 378)
        self.assertEqual(rico.CHAPTER_ONE_LIVE_FUNERAL_DONOR_FIELD, 15)
        self.assertEqual(rico.CHAPTER_ONE_ETON_SOURCE_FIELD, 348)
        self.assertEqual(rico.CHAPTER_ONE_GRAVE_MARKER_TARGET_NODE, 63)
        self.assertEqual(rico.CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_NODE, 64)
        self.assertEqual(rico.CHAPTER_ONE_GRAVE_MARKER_TARGET_MODEL_INDEX, 2)
        self.assertEqual(
            rico.CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_MODEL_INDEX,
            3,
        )
        self.assertEqual(
            rico.CHAPTER_ONE_GRAVE_MARKER_TARGET_NODE_RECORD,
            bytes.fromhex(
                "10 00 00 00 00 00 00 00 B0 03 48 02 34 F0 02 00"
            ),
        )
        self.assertEqual(
            rico.CHAPTER_ONE_GRAVE_MARKER_BACKGROUND_NODE_RECORD,
            bytes.fromhex(
                "10 00 00 00 00 00 00 00 2C 02 1A 00 D2 F8 03 00"
            ),
        )
        self.assertEqual(
            (
                rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_ACTOR_BANK_INDEX,
                rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_SPRITE_BANK_INDEX,
                rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ACTOR_BANK_INDEX,
                rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_SPRITE_BANK_INDEX,
                rico.CHAPTER_ONE_ETON_SOURCE_BANK_INDEX,
            ),
            (1, 1, 0, 0, 0),
        )
        self.assertEqual(
            (
                rico.CHAPTER_ONE_LIVE_FUNERAL_MARKER_POSITION,
                rico.CHAPTER_ONE_LIVE_FUNERAL_BACKGROUND_MARKER_POSITION,
                rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_POSITION,
                rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_START,
                rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_BLESSING_POSITION,
            ),
            (
                (600, -2700, 1885),
                (900, -2750, 1885),
                (500, -2400, 1882),
                (950, -2350, 1885),
                (720, -2520, 1885),
            ),
        )
        self.assertEqual(transition.firewood_dialogue, (30,))
        self.assertEqual(contract.exit_dialogue, (20,))
        self.assertEqual(rico.CHAPTER_ONE_FIREWOOD_RICO_TIMESCALE, 0x140)
        self.assertEqual(
            (
                rico.CHAPTER_ONE_FIREWOOD_ESTABLISHING_CAMERA_EYE,
                rico.CHAPTER_ONE_FIREWOOD_WORK_CAMERA_EYE,
            ),
            ((926, 696, -457), (750, -302, -286)),
        )
        self.assertIn(
            b"\x21" + rico._immediate(0x140),
            rico._chapter_one_firewood_rico_init(),
        )

        firewood_story = rico._build_chapter_one_firewood_story(
            base_pc=0x1000,
            firewood_dialogue_ids=(0,),
        )
        approach = b"\x09" + bytes(
            (
                rico.CHAPTER_ONE_FIREWOOD_RICO_ENTITY,
                rico.CHAPTER_ONE_FIREWOOD_APPROACH_SCRIPT | 0x20,
            )
        )
        return_home = b"\x09" + bytes(
            (
                rico.CHAPTER_ONE_FIREWOOD_RICO_ENTITY,
                rico.CHAPTER_ONE_FIREWOOD_RETURN_SCRIPT | 0x20,
            )
        )
        narration = rico._dialogue_sequence((0,))
        aftermath_route = rico._change_field(rico.CHAPTER_ONE_AFTERMATH_FIELD, 0)
        self.assertEqual(firewood_story.count(approach), 1)
        self.assertEqual(firewood_story.count(return_home), 1)
        self.assertEqual(firewood_story.count(narration), 1)
        self.assertEqual(firewood_story.count(aftermath_route), 1)
        self.assertLess(
            firewood_story.index(approach),
            firewood_story.index(narration),
        )
        self.assertLess(
            firewood_story.index(narration),
            firewood_story.index(return_home),
        )
        self.assertLess(
            firewood_story.index(return_home),
            firewood_story.index(aftermath_route),
        )
        self.assertIn(
            b"\x31" + struct.pack("<H", rico.PAD_MASK_CROSS),
            firewood_story,
        )
        self.assertNotIn(b"\xFE\x77\x01", firewood_story)

        aftermath_story = rico._build_chapter_one_aftermath_story(
            base_pc=0x1000,
            sickness_ids=(0, 1, 2, 3, 4, 5),
            loss_ids=(6, 7, 8, 9),
        )
        funeral_route = rico._change_field(rico.CHAPTER_ONE_FUNERAL_FIELD, 0)
        cough = b"\x09" + bytes(
            (
                rico.CHAPTER_ONE_ANNA_ENTITY,
                rico.CHAPTER_ONE_AFTERMATH_COUGH_SCRIPT | 0x20,
            )
        )
        daylight_grade = rico._chapter_one_aftermath_daylight_grade_body()
        night_grade = rico._chapter_one_aftermath_night_grade_body()
        fade_in = rico._chapter_one_aftermath_scene_fade_body(reveal=True)
        fade_out = rico._chapter_one_aftermath_scene_fade_body(reveal=False)
        death_blackout_handoff = (
            rico._chapter_one_aftermath_blackout_handoff_body()
        )
        daylight_restore = rico._chapter_one_aftermath_daylight_restore_body()
        neutral_slot_one_fade = (
            rico.mass_driver._facility_video_screen_fade_body(
                0,
                rico.CHAPTER_ONE_AFTERMATH_FADE_FRAMES,
            )
        )
        self.assertEqual(
            rico.CHAPTER_ONE_AFTERMATH_NIGHT_GRADE_RGB,
            (100, 40, 30),
        )
        self.assertEqual(rico.CHAPTER_ONE_AFTERMATH_DAYLIGHT_GRADE_RGB, (0, 0, 0))
        self.assertEqual(
            daylight_grade,
            bytes.fromhex("F1 02 80 00 80 00 80 00 80 01 80"),
        )
        self.assertEqual(
            night_grade,
            bytes.fromhex("F1 02 80 64 80 28 80 1E 80 01 80"),
        )
        self.assertNotIn(
            bytes.fromhex("F1 02 80 1E 80 28 80 64 80 01 80"),
            aftermath_story,
        )
        self.assertEqual(aftermath_story.count(night_grade), 1)
        self.assertEqual(aftermath_story.count(daylight_grade), 1)
        self.assertEqual(aftermath_story.count(fade_in), 4)
        self.assertEqual(aftermath_story.count(fade_out), 4)
        self.assertEqual(
            rico.CHAPTER_ONE_AFTERMATH_BLACKOUT_RGB,
            (0xFF, 0xFF, 0xFF),
        )
        self.assertEqual(aftermath_story.count(death_blackout_handoff), 1)
        self.assertEqual(aftermath_story.count(daylight_restore), 1)
        self.assertEqual(
            death_blackout_handoff,
            rico._chapter_one_aftermath_grade_body(
                rico.CHAPTER_ONE_AFTERMATH_BLACKOUT_RGB,
                frames=1,
            )
            + rico._wait()
            + fade_in,
        )
        self.assertEqual(
            daylight_restore,
            rico._chapter_one_aftermath_daylight_grade_body(
                frames=rico.CHAPTER_ONE_AFTERMATH_FADE_FRAMES,
            )
            + rico._wait(rico.CHAPTER_ONE_AFTERMATH_FADE_FRAMES),
        )
        self.assertEqual(daylight_restore, neutral_slot_one_fade)
        self.assertLess(
            aftermath_story.index(daylight_grade),
            aftermath_story.index(fade_in),
        )
        first_fade_in = aftermath_story.index(fade_in)
        first_fade_out = aftermath_story.index(
            fade_out,
            first_fade_in + len(fade_in),
        )
        second_fade_in = aftermath_story.index(
            fade_in,
            first_fade_out + len(fade_out),
        )
        night_grade_at = aftermath_story.index(night_grade)
        self.assertLess(first_fade_out, night_grade_at)
        self.assertLess(night_grade_at, second_fade_in)
        second_fade_out = aftermath_story.index(
            fade_out,
            second_fade_in + len(fade_in),
        )
        return_home = aftermath_story[first_fade_in:first_fade_out]
        sickroom = aftermath_story[second_fade_in:second_fade_out]
        after_anna = aftermath_story[second_fade_out:]
        self.assertEqual(aftermath_story.count(cough), 2)
        self.assertEqual(return_home.count(cough), 1)
        self.assertEqual(sickroom.count(cough), 1)
        self.assertNotIn(cough, after_anna)
        death_narration = rico._dialogue_sequence((6,))
        pad_release = b"\x31" + struct.pack("<H", rico.PAD_MASK_CROSS)
        last_sickness_at = aftermath_story.index(
            rico._dialogue_sequence((5,))
        )
        closing_release_at = aftermath_story.index(
            pad_release,
            last_sickness_at,
        )
        self.assertLess(last_sickness_at, closing_release_at)
        self.assertLess(closing_release_at, second_fade_out)
        handoff_at = after_anna.index(death_blackout_handoff)
        death_narration_at = after_anna.index(death_narration)
        daylight_restore_at = after_anna.index(daylight_restore)
        self.assertLess(handoff_at, death_narration_at)
        self.assertLess(death_narration_at, daylight_restore_at)
        self.assertNotIn(night_grade, after_anna[daylight_restore_at:])
        self.assertNotIn(
            pad_release,
            after_anna[:death_narration_at],
        )
        rico_entry = rico._chapter_one_aftermath_call(
            rico.CHAPTER_ONE_AFTERMATH_RICO_ENTITY,
            rico.CHAPTER_ONE_AFTERMATH_ENTRY_SCRIPT,
        )
        door_close = rico._chapter_one_aftermath_call(
            rico.CHAPTER_ONE_AFTERMATH_DOOR_ENTITY,
            5,
            asynchronous=True,
        )
        self.assertLess(
            return_home.index(rico_entry),
            return_home.index(door_close),
        )
        self.assertLess(
            return_home.index(door_close),
            return_home.index(cough),
        )
        self.assertEqual(aftermath_story.count(funeral_route), 1)
        self.assertLess(
            aftermath_story.index(cough),
            aftermath_story.index(funeral_route),
        )
        self.assertNotIn(b"\xFE\x77\x01", aftermath_story)

        funeral_story = rico._build_chapter_one_live_funeral_story(
            base_pc=0x1000,
            transition=transition,
            funeral_ids=(0, 1, 2, 3),
            epilogue_ids=(4,),
        )
        priest_approach = b"\x09" + bytes(
            (
                rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_ENTITY,
                rico.CHAPTER_ONE_LIVE_FUNERAL_PRIEST_APPROACH_SCRIPT | 0x20,
            )
        )
        progress = rico.mass_driver._set_var_bit(
            rico.PLAYABLE_STATE_VARIABLE,
            transition.bit,
        )
        completion_call = rico._chapter_one_aftermath_call(
            rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_ENTITY,
            rico.CHAPTER_ONE_LIVE_FUNERAL_COMPLETION_SCRIPT,
        )
        establishing_camera = rico._chapter_one_live_funeral_camera(
            rico.CHAPTER_ONE_LIVE_FUNERAL_CAMERA_TARGET,
            rico.CHAPTER_ONE_LIVE_FUNERAL_CAMERA_EYE,
            transition_frames=0,
            enter_camera_mode=True,
        )
        blessing_camera = rico._chapter_one_live_funeral_camera(
            rico.CHAPTER_ONE_LIVE_FUNERAL_BLESSING_CAMERA_TARGET,
            rico.CHAPTER_ONE_LIVE_FUNERAL_BLESSING_CAMERA_EYE,
            transition_frames=rico.CHAPTER_ONE_LIVE_FUNERAL_CAMERA_MOVE_FRAMES,
            enter_camera_mode=False,
        )
        return_wide_camera = rico._chapter_one_live_funeral_camera(
            rico.CHAPTER_ONE_LIVE_FUNERAL_CAMERA_TARGET,
            rico.CHAPTER_ONE_LIVE_FUNERAL_CAMERA_EYE,
            transition_frames=(
                rico.CHAPTER_ONE_LIVE_FUNERAL_RETURN_CAMERA_MOVE_FRAMES
            ),
            enter_camera_mode=False,
        )
        visible_grade_prefix = (
            b"\xF1"
            + rico._immediate(2)
            + rico._immediate(0) * 3
        )
        black_grade_prefix = (
            b"\xF1"
            + rico._immediate(2)
            + rico._immediate(0xFF) * 3
        )
        fade_visible = rico.mass_driver._facility_video_screen_fade_body(
            0,
            rico.CHAPTER_ONE_LIVE_FUNERAL_FADE_FRAMES,
        )
        self.assertEqual(
            (
                rico.CHAPTER_ONE_LIVE_FUNERAL_CAMERA_TARGET,
                rico.CHAPTER_ONE_LIVE_FUNERAL_CAMERA_EYE,
                rico.CHAPTER_ONE_LIVE_FUNERAL_BLESSING_CAMERA_TARGET,
                rico.CHAPTER_ONE_LIVE_FUNERAL_BLESSING_CAMERA_EYE,
            ),
            (
                (700, -2525, -20),
                (1400, -3400, -650),
                (700, -2600, -20),
                (1120, -3160, -430),
            ),
        )
        self.assertEqual(
            (
                rico.CHAPTER_ONE_LIVE_FUNERAL_CAMERA_MOVE_FRAMES,
                rico.CHAPTER_ONE_LIVE_FUNERAL_RETURN_CAMERA_MOVE_FRAMES,
                rico.CHAPTER_ONE_LIVE_FUNERAL_ESTABLISH_HOLD_FRAMES,
                rico.CHAPTER_ONE_LIVE_FUNERAL_BLESSING_SETTLE_FRAMES,
                rico.CHAPTER_ONE_LIVE_FUNERAL_REFLECTION_HOLD_FRAMES,
                rico.CHAPTER_ONE_LIVE_FUNERAL_WIDE_HOLD_FRAMES,
                rico.CHAPTER_ONE_LIVE_FUNERAL_EPILOGUE_SETTLE_FRAMES,
            ),
            (36, 48, 60, 42, 60, 60, 30),
        )
        self.assertEqual(funeral_story.count(priest_approach), 1)
        self.assertEqual(funeral_story.count(progress), 1)
        self.assertEqual(funeral_story.count(completion_call), 1)
        self.assertEqual(funeral_story.count(establishing_camera), 1)
        self.assertEqual(funeral_story.count(blessing_camera), 1)
        self.assertEqual(funeral_story.count(return_wide_camera), 1)
        self.assertEqual(funeral_story.count(fade_visible), 1)
        self.assertIn(visible_grade_prefix, funeral_story)
        self.assertNotIn(black_grade_prefix, funeral_story)
        self.assertEqual(
            rico.CHAPTER_ONE_LIVE_FUNERAL_HIDDEN_DIALOGUE_FLAGS,
            0x01,
        )
        funeral_dialogue_calls = tuple(
            (
                struct.unpack_from("<H", funeral_story, offset + 1)[0],
                funeral_story[offset + 3],
            )
            for offset in range(len(funeral_story) - 4)
            if funeral_story[offset] == 0xF5
            and funeral_story[offset + 4] == 0x9C
            and struct.unpack_from("<H", funeral_story, offset + 1)[0] < 5
        )
        self.assertEqual(
            funeral_dialogue_calls,
            tuple(
                (
                    dialogue_id,
                    rico.CHAPTER_ONE_LIVE_FUNERAL_HIDDEN_DIALOGUE_FLAGS,
                )
                for dialogue_id in range(5)
            ),
        )
        for dialogue_id in range(5):
            self.assertNotIn(
                rico._dialog(dialogue_id, flags=0) + b"\x9C",
                funeral_story,
            )
        self.assertLess(
            funeral_story.index(priest_approach),
            funeral_story.index(progress),
        )
        last_local_dialogue = (
            rico._dialog(
                4,
                flags=rico.CHAPTER_ONE_LIVE_FUNERAL_HIDDEN_DIALOGUE_FLAGS,
            )
            + b"\x9C"
        )
        last_local_dialogue_at = funeral_story.index(last_local_dialogue)
        progress_at = funeral_story.index(progress)
        completion_call_at = funeral_story.index(completion_call)
        closing_dialog_reset_at = funeral_story.index(
            rico._actor_dialog_reset(),
            last_local_dialogue_at + len(last_local_dialogue),
        )
        self.assertEqual(
            last_local_dialogue_at + len(last_local_dialogue),
            closing_dialog_reset_at,
        )
        self.assertLess(closing_dialog_reset_at, progress_at)
        self.assertLess(progress_at, completion_call_at)
        for dialogue_id in range(4, 5):
            dialogue_at = funeral_story.index(
                rico._dialog(
                    dialogue_id,
                    flags=rico.CHAPTER_ONE_LIVE_FUNERAL_HIDDEN_DIALOGUE_FLAGS,
                )
            )
            self.assertGreater(
                funeral_story.rfind(visible_grade_prefix, 0, dialogue_at),
                funeral_story.rfind(black_grade_prefix, 0, dialogue_at),
            )
        menu_comparison_prefix = (
            b"\x02" + struct.pack("<H", rico.MENU_SELECTION_VARIABLE)
        )
        self.assertNotIn(b"\xD2", funeral_story)
        self.assertNotIn(b"\xA9\x12\x9C", funeral_story)
        self.assertNotIn(menu_comparison_prefix, funeral_story)
        self.assertTrue(funeral_story.endswith(completion_call))
        self.assertNotIn(
            rico._hub_launch_body(rico.HUB_FIELDS[1]),
            funeral_story,
        )
        self.assertNotIn(
            rico._chapter_launch_body(2, rico.CHAPTER_FIELDS[1][2]),
            funeral_story,
        )

        completion = rico._build_chapter_one_live_funeral_completion(
            base_pc=0x2000,
            choice_id=5,
            next_field=rico.CHAPTER_FIELDS[1][2],
            return_hub=rico.HUB_FIELDS[1],
        )
        self.assertEqual(
            completion.count(rico._choice_dialog(5) + b"\xA9\x12\x9C"),
            1,
        )
        self.assertEqual(rico.CHAPTER_ONE_LIVE_FUNERAL_RICO_ENTITY, 1)
        self.assertEqual(funeral_story.count(completion_call), 1)
        self.assertNotIn(rico._choice_dialog(5), funeral_story)
        self.assertEqual(
            completion.count(
                rico._chapter_launch_body(2, rico.CHAPTER_FIELDS[1][2])
            ),
            1,
        )
        self.assertEqual(
            completion.count(rico._hub_launch_body(rico.HUB_FIELDS[1])),
            1,
        )
        self.assertIn(menu_comparison_prefix, completion)
        self.assertNotIn(b"\xFE\x77\x01", funeral_story)
        self.assertEqual(
            rico._field_bundle_id(rico.CHAPTER_ONE_AFTERMATH_FIELD),
            1358,
        )
        self.assertEqual(
            rico._field_bundle_id(rico.CHAPTER_ONE_FUNERAL_FIELD),
            1362,
        )

    def test_chapter_seven_ends_on_the_stonebell_payoff_before_the_end(self) -> None:
        chapter = self.chapters[6]
        contract = rico._playable_chapter_contract(7)
        source_dialogue_count = (
            struct.unpack_from(
                "<I",
                parse_field(self.chapter_sources[7]).parts[
                    rico.DIALOGUE_INDEX
                ].data,
                0,
            )[0]
            + 1
        )
        payoff_ids = (source_dialogue_count + 23, source_dialogue_count + 24)
        custom_texts = rico._playable_custom_texts(contract)
        final_menu_id = (
            source_dialogue_count
            + len(chapter.blocks)
            + custom_texts.index(rico.PLAYABLE_FINAL_HUB_CHOICE)
        )
        final_sequence = (
            rico._dialogue_sequence(payoff_ids)
            + rico._wait()
            + rico._choice_dialog(final_menu_id)
            + b"\xA9\x12\x9C"
        )
        native_open = b"\x09" + bytes(
            (
                rico.CHAPTER_SEVEN_DOOR_ENTITY,
                rico.CHAPTER_SEVEN_DOOR_OPEN_SCRIPT | 0x20,
            )
        )

        for disc in (1, 2):
            with self.subTest(disc=disc):
                output_field = parse_field(self.chapter_outputs[disc, 7])
                texts = _lenient_dialogue_texts(
                    output_field.parts[rico.DIALOGUE_INDEX].data
                )
                self.assertEqual(
                    texts[payoff_ids[0]],
                    rico._reflow_dialogue_text(chapter.blocks[23]),
                )
                self.assertEqual(
                    texts[payoff_ids[1]],
                    rico._reflow_dialogue_text(chapter.blocks[24]),
                )
                self.assertIn("stonebell", texts[payoff_ids[0]].casefold())
                self.assertEqual(texts[payoff_ids[1]], "THE END<Close>")

                (
                    source_editor,
                    output_editor,
                    _contract,
                    _first_controller,
                    exit_entity,
                ) = self._chapter_layout(disc, 7)
                exit_action = _pointed_body(output_editor, exit_entity, 2)
                self.assertEqual(exit_action.count(final_sequence), 1)
                self.assertEqual(exit_action.count(native_open), 1)
                self.assertLess(
                    exit_action.index(native_open),
                    exit_action.index(final_sequence),
                )

    def test_chapter_one_unfinished_door_never_reaches_completion(self) -> None:
        chapter = self.chapters[0]
        contract = rico._playable_chapter_contract(1)
        self.assertTrue(contract.completion_at_exit)
        self.assertIn(7, contract.required_bits)
        self.assertIn(10, contract.required_bits)
        self.assertIn(rico.CHAPTER_ONE_HEATER_VALVE_BIT, contract.required_bits)
        source_dialogue_count = (
            struct.unpack_from(
                "<I",
                parse_field(self.chapter_sources[1]).parts[
                    rico.DIALOGUE_INDEX
                ].data,
                0,
            )[0]
            + 1
        )
        custom_texts = rico._playable_custom_texts(contract)
        custom_ids = {
            text: source_dialogue_count + len(chapter.blocks) + index
            for index, text in enumerate(custom_texts)
        }
        expected_states = (
            ((), 2),
            ((2,), 3),
            ((2, 3), 6),
            ((2, 6), 3),
            ((2, 3, 6), 1),
            ((2, 3, 6, 7), 1),
            ((2, 3, 6, 1), 7),
            ((2, 3, 6, 1, 7), 11),
            ((2, 3, 6, 1, 7, 4), 11),
            ((2, 3, 6, 1, 7, 10, 4), 11),
            ((2, 3, 6, 1, 7, 11), 10),
            ((2, 3, 6, 1, 7, 11, 10), 4),
            ((2, 3, 6, 1, 7, 11, 10, 4), None),
            ((2, 3, 6, 1, 7, 11, 10, 4, 5), None),
        )
        reminder_text = dict(contract.exit_locked_steps)
        transition = contract.exit_transition
        self.assertIsNotNone(transition)
        assert transition is not None

        for disc in (1, 2):
            with self.subTest(disc=disc):
                (
                    source_editor,
                    output_editor,
                    _contract,
                    _first_controller,
                    exit_entity,
                ) = self._chapter_layout(disc, 1)
                exit_pc = output_editor.get_script_pointer(exit_entity, 2)
                exit_action = _pointed_body(output_editor, exit_entity, 2)
                missing = rico._missing_playable_characters(
                    chapter,
                    source_editor,
                )
                leader_entity = source_editor.entity_count + missing.index(
                    rico.YOUNG_RICO_ID
                )
                doorway_ids = tuple(
                    custom_ids[text] for text in transition.doorway_dialogue
                )
                successful_departure = (
                    rico._chapter_one_doorway_exchange_body(
                        leader_entity,
                        doorway_ids,
                    )
                    + rico._chapter_one_door_transition_body()
                )
                branch_at = len(rico._playable_action_prefix(exit_pc))
                compiled: list[tuple[int, int]] = []
                for bit, text in contract.exit_locked_steps:
                    self.assertEqual(
                        exit_action[branch_at : branch_at + 6],
                        b"\x02"
                        + struct.pack("<H", rico.PLAYABLE_STATE_VARIABLE)
                        + struct.pack("<H", 1 << bit)
                        + b"\x46",
                    )
                    target_pc = struct.unpack_from(
                        "<H", exit_action, branch_at + 6
                    )[0]
                    target_at = target_pc - exit_pc
                    dialogue = rico._dialogue_sequence((custom_ids[text],))
                    locked_body = dialogue + rico._playable_action_finish(
                        target_pc + len(dialogue)
                    )
                    self.assertTrue(exit_action.startswith(locked_body, target_at))
                    compiled.append((1 << bit, target_at))
                    branch_at += 8

                for set_bits, expected_missing in expected_states:
                    with self.subTest(disc=disc, set_bits=set_bits):
                        state = sum(1 << bit for bit in set_bits)
                        target_at = next(
                            (
                                target
                                for mask, target in compiled
                                if state & mask == 0
                            ),
                            None,
                        )
                        if expected_missing is None:
                            self.assertIsNone(target_at)
                            self.assertTrue(
                                exit_action.startswith(
                                    successful_departure,
                                    branch_at,
                                )
                            )
                        else:
                            self.assertIsNotNone(target_at)
                            self.assertTrue(
                                exit_action.startswith(
                                    rico._dialog(
                                        custom_ids[reminder_text[expected_missing]]
                                    ),
                                    target_at,
                                )
                            )

    def test_chapter_one_anna_requires_the_prepared_cup_in_bytecode(
        self,
    ) -> None:
        chapter = self.chapters[0]
        contract = rico._playable_chapter_contract(1)
        anna_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "Anne's bedside"
        )
        anna = contract.interactions[anna_index]
        return_stage = next(stage for stage in anna.stages if stage.bit == 4)
        expected_requirements = (
            3,
            rico.CHAPTER_ONE_STOVE_ON_BIT,
            1,
            7,
            rico.CHAPTER_ONE_HEATER_VALVE_BIT,
            rico.CHAPTER_ONE_KETTLE_BOILED_BIT,
            10,
        )
        self.assertEqual(return_stage.required_bits, expected_requirements)
        self.assertFalse(return_stage.locked_dialogue)
        self.assertFalse(return_stage.locked_dialogue_states)
        self.assertEqual(
            tuple(bit for bit, _dialogue in return_stage.locked_dialogue_steps),
            expected_requirements,
        )

        source_count = (
            struct.unpack_from(
                "<I",
                parse_field(self.chapter_sources[1]).parts[
                    rico.DIALOGUE_INDEX
                ].data,
                0,
            )[0]
            + 1
        )
        custom_texts = rico._playable_custom_texts(contract)
        custom_ids = {
            text: source_count + len(chapter.blocks) + index
            for index, text in enumerate(custom_texts)
        }

        for disc in (1, 2):
            with self.subTest(disc=disc):
                (
                    _source_editor,
                    output_editor,
                    _contract,
                    first_controller,
                    _exit_entity,
                ) = self._chapter_layout(disc, 1)
                anna_entity = first_controller + anna_index
                action_pc = output_editor.get_script_pointer(anna_entity, 2)
                action = _pointed_body(output_editor, anna_entity, 2)
                branch_at = len(rico._playable_action_prefix(action_pc))

                stage_targets: dict[int, int] = {}
                for stage in anna.stages:
                    self.assertEqual(
                        action[branch_at : branch_at + 6],
                        b"\x02"
                        + struct.pack("<H", rico.PLAYABLE_STATE_VARIABLE)
                        + struct.pack("<H", 1 << stage.bit)
                        + b"\x46",
                    )
                    stage_targets[stage.bit] = (
                        struct.unpack_from("<H", action, branch_at + 6)[0]
                        - action_pc
                    )
                    branch_at += 8

                bit_four_commit = rico.mass_driver._set_var_bit(
                    rico.PLAYABLE_STATE_VARIABLE,
                    4,
                )

                def route_state(offset: int, state: int) -> int:
                    """Follow only the bit-test tree to its first action body."""

                    visited: set[int] = set()
                    while True:
                        self.assertNotIn(offset, visited)
                        self.assertGreaterEqual(offset, 0)
                        self.assertLess(offset, len(action))
                        visited.add(offset)
                        if action[offset] == 0x01:
                            self.assertLessEqual(offset + 3, len(action))
                            offset = (
                                struct.unpack_from("<H", action, offset + 1)[0]
                                - action_pc
                            )
                            continue
                        if (
                            action[offset] == 0x02
                            and offset + 8 <= len(action)
                            and action[offset + 5] == 0x46
                        ):
                            self.assertEqual(
                                struct.unpack_from("<H", action, offset + 1)[0],
                                rico.PLAYABLE_STATE_VARIABLE,
                            )
                            mask = struct.unpack_from("<H", action, offset + 3)[0]
                            target = (
                                struct.unpack_from("<H", action, offset + 6)[0]
                                - action_pc
                            )
                            offset = target if state & mask == 0 else offset + 8
                            continue
                        return offset

                reminder_refs = dict(return_stage.locked_dialogue_steps)
                locked_routes: set[int] = set()
                progress_state = 1 << 2
                for missing_bit in expected_requirements:
                    routed = route_state(stage_targets[4], progress_state)
                    unrelated_state = progress_state | sum(
                        1 << bit
                        for bit in (
                            8,
                            9,
                            rico.CHAPTER_ONE_KETTLE_FILLED_BIT,
                        )
                    )
                    self.assertEqual(
                        route_state(stage_targets[4], unrelated_state),
                        routed,
                    )
                    locked_routes.add(routed)
                    locked_ids = rico._resolve_playable_dialogue(
                        reminder_refs[missing_bit],
                        authored_base=source_count,
                        authored_count=len(chapter.blocks),
                        custom_ids=custom_ids,
                    )
                    locked_scene = (
                        rico.CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL
                        + rico._dialogue_sequence(locked_ids)
                    )
                    finish_at = routed + len(locked_scene)
                    locked_body = locked_scene + rico._playable_action_finish(
                        action_pc + finish_at
                    )
                    with self.subTest(
                        disc=disc,
                        prepared_cup=False,
                        next_missing_bit=missing_bit,
                    ):
                        self.assertTrue(action.startswith(locked_body, routed))
                        self.assertNotIn(bit_four_commit, locked_body)
                    progress_state |= 1 << missing_bit

                self.assertEqual(len(locked_routes), len(expected_requirements))
                early_boil_route = route_state(
                    stage_targets[4],
                    (1 << 2) | (1 << rico.CHAPTER_ONE_KETTLE_BOILED_BIT),
                )
                first_task_route = route_state(stage_targets[4], 1 << 2)
                self.assertEqual(early_boil_route, first_task_route)
                success_route = route_state(stage_targets[4], progress_state)
                success_ids = rico._resolve_playable_dialogue(
                    return_stage.dialogue,
                    authored_base=source_count,
                    authored_count=len(chapter.blocks),
                    custom_ids=custom_ids,
                )
                success_scene = (
                    rico.CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL
                    + rico._dialogue_sequence(success_ids)
                )
                self.assertTrue(action.startswith(success_scene, success_route))
                self.assertNotIn(success_route, locked_routes)
                self.assertEqual(action[success_route:].count(bit_four_commit), 1)
                self.assertNotIn(
                    rico.mass_driver._set_var_bit(
                        rico.PLAYABLE_STATE_VARIABLE,
                        5,
                    ),
                    action,
                )

    def test_chapter_one_heater_is_inspection_only_until_chores_are_assigned(
        self,
    ) -> None:
        chapter = self.chapters[0]
        contract = rico._playable_chapter_contract(1)
        heater_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "room heater"
        )
        heater_stage = contract.interactions[heater_index].stages[0]
        self.assertEqual(heater_stage.bit, rico.CHAPTER_ONE_HEATER_VALVE_BIT)
        self.assertEqual(heater_stage.required_bits, (2,))
        self.assertEqual(len(heater_stage.locked_dialogue), 1)
        self.assertIn("low fire", heater_stage.locked_dialogue[0])
        self.assertIn("valve is nearly closed", heater_stage.locked_dialogue[0])
        self.assertNotIn("opens the valve", heater_stage.locked_dialogue[0])
        self.assertIn(
            rico.CHAPTER_ONE_HEATER_VALVE_BIT,
            contract.required_bits,
        )
        self.assertIsNotNone(contract.exit_transition)
        assert contract.exit_transition is not None
        self.assertIn(
            rico.CHAPTER_ONE_HEATER_VALVE_BIT,
            contract.exit_transition.required_bits,
        )
        self.assertIn(
            rico.CHAPTER_ONE_HEATER_VALVE_BIT,
            dict(contract.exit_locked_steps),
        )

        source_count = (
            struct.unpack_from(
                "<I",
                parse_field(self.chapter_sources[1]).parts[
                    rico.DIALOGUE_INDEX
                ].data,
                0,
            )[0]
            + 1
        )
        custom_texts = rico._playable_custom_texts(contract)
        custom_ids = {
            text: source_count + len(chapter.blocks) + index
            for index, text in enumerate(custom_texts)
        }

        def bit_clear_test(bit: int) -> bytes:
            return (
                b"\x02"
                + struct.pack("<H", rico.PLAYABLE_STATE_VARIABLE)
                + struct.pack("<H", 1 << bit)
                + b"\x46"
            )

        stage_dialogue = rico._dialogue_sequence(
            rico._resolve_playable_dialogue(
                heater_stage.dialogue,
                authored_base=source_count,
                authored_count=len(chapter.blocks),
                custom_ids=custom_ids,
            )
        )
        locked_dialogue = rico._dialogue_sequence(
            rico._resolve_playable_dialogue(
                heater_stage.locked_dialogue,
                authored_base=source_count,
                authored_count=len(chapter.blocks),
                custom_ids=custom_ids,
            )
        )
        assert heater_stage.choice_text is not None
        choice_opcode = (
            rico._choice_dialog(custom_ids[heater_stage.choice_text])
            + b"\xA9\x12\x9C"
        )
        valve_commit = rico.mass_driver._set_var_bit(
            rico.PLAYABLE_STATE_VARIABLE,
            rico.CHAPTER_ONE_HEATER_VALVE_BIT,
        )

        for disc in (1, 2):
            with self.subTest(disc=disc):
                (
                    _source_editor,
                    output_editor,
                    _contract,
                    first_controller,
                    _exit_entity,
                ) = self._chapter_layout(disc, 1)
                heater_entity = first_controller + heater_index
                action_pc = output_editor.get_script_pointer(heater_entity, 2)
                action = _pointed_body(output_editor, heater_entity, 2)
                dispatch_at = len(rico._playable_action_prefix(action_pc))
                self.assertEqual(
                    action[dispatch_at : dispatch_at + 6],
                    bit_clear_test(rico.CHAPTER_ONE_HEATER_VALVE_BIT),
                )
                stage_at = (
                    struct.unpack_from("<H", action, dispatch_at + 6)[0]
                    - action_pc
                )
                self.assertEqual(
                    action[stage_at : stage_at + 6],
                    bit_clear_test(2),
                )
                locked_at = (
                    struct.unpack_from("<H", action, stage_at + 6)[0]
                    - action_pc
                )
                assigned_at = stage_at + 8

                locked_finish_at = locked_at + len(locked_dialogue)
                locked_body = locked_dialogue + rico._playable_action_finish(
                    action_pc + locked_finish_at
                )
                self.assertTrue(action.startswith(locked_body, locked_at))
                self.assertNotIn(choice_opcode, locked_body)
                self.assertNotIn(valve_commit, locked_body)

                self.assertTrue(
                    action.startswith(
                        stage_dialogue + rico._wait() + choice_opcode,
                        assigned_at,
                    )
                )
                self.assertEqual(action.count(choice_opcode), 1)
                self.assertEqual(action.count(valve_commit), 1)
                self.assertLess(assigned_at, action.index(valve_commit))
                self.assertLess(action.index(valve_commit), locked_at)

    def test_chapter_one_stove_needs_a_directional_deliberate_choice(self) -> None:
        chapter = self.chapters[0]
        contract = rico._playable_chapter_contract(1)
        heater = next(
            interaction
            for interaction in contract.interactions
            if interaction.name == "room heater"
        )
        self.assertEqual(tuple(stage.bit for stage in heater.stages), (11,))
        heater_stage = heater.stages[0]
        self.assertIn("Open the valve", heater_stage.choice_text)
        self.assertIn("Open Valve", heater_stage.choice_text)
        self.assertIn("Leave It Closed", heater_stage.choice_text)

        counter_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "cooking counter"
        )
        counter = contract.interactions[counter_index]
        self.assertEqual(
            (counter.x, counter.z, counter.triangle),
            rico.CHAPTER_ONE_COOKING_COUNTER_POSITION,
        )
        self.assertFalse(counter.requires_facing)
        self.assertEqual(
            (counter.interaction_half_width, counter.interaction_half_depth),
            (
                rico.CHAPTER_ONE_COOKING_COUNTER_INTERACTION_HALF_WIDTH,
                rico.CHAPTER_ONE_COOKING_COUNTER_INTERACTION_HALF_DEPTH,
            ),
        )
        self.assertEqual(
            (
                counter.interaction_half_width * 2 + 0x10,
                counter.interaction_half_depth * 2 + 0x10,
            ),
            (36, 36),
        )
        self.assertIsNone(counter.walkmesh_anchor)
        saved_x, saved_z = (
            rico.CHAPTER_ONE_COOKING_STOVE_SLOT_ONE_REPRO_POSITION
        )
        stove_position = (math.floor(saved_x), math.floor(saved_z))
        self.assertEqual(
            stove_position,
            rico.CHAPTER_ONE_COOKING_STOVE_SLOT_ONE_ENGINE_POSITION,
        )
        normal_min, normal_max = (
            rico.CHAPTER_ONE_COOKING_COUNTER_CONTACT_NORMAL_RANGE
        )
        tangent_min, tangent_max = (
            rico.CHAPTER_ONE_COOKING_COUNTER_CONTACT_TANGENT_RANGE
        )
        self.assertLessEqual(normal_min, stove_position[1] - stove_position[0])
        self.assertLessEqual(stove_position[1] - stove_position[0], normal_max)
        self.assertLessEqual(tangent_min, stove_position[0] + stove_position[1])
        self.assertLessEqual(stove_position[0] + stove_position[1], tangent_max)
        self.assertEqual(normal_min, 316)
        self.assertEqual(rico.CHAPTER_ONE_COOKING_STOVE_SLOT_ONE_YAW, 0x0A00)
        self.assertEqual(
            tuple(stage.bit for stage in counter.stages),
            (6, 10, 9),
        )
        stage = counter.stages[0]
        cup_stage = counter.stages[1]
        bowl_stage = counter.stages[2]
        self.assertEqual(stage.required_bits, (3,))
        self.assertEqual(
            cup_stage.required_bits,
            (7, rico.CHAPTER_ONE_KETTLE_BOILED_BIT),
        )
        self.assertEqual(
            {completed for completed, _dialogue in cup_stage.locked_dialogue_states},
            {(), (7,), (rico.CHAPTER_ONE_KETTLE_BOILED_BIT,)},
        )
        self.assertEqual(bowl_stage.required_bits, ())
        self.assertEqual(stage.accepted_selection, 1)
        self.assertEqual(
            stage.accepted_sound_id,
            rico.CHAPTER_ONE_STOVE_IGNITION_SOUND_ID,
        )
        self.assertEqual(rico.CHAPTER_ONE_STOVE_IGNITION_SOUND_ID, 0xF9)
        self.assertEqual(rico.CHAPTER_ONE_STOVE_FIRE_SOUND_ID, 0x111)
        self.assertIsNotNone(stage.choice_text)
        assert stage.choice_text is not None
        self.assertIn("Turn on the stove", stage.choice_text)
        self.assertIn("Turn It On", stage.choice_text)
        self.assertIn("Leave It Off", stage.choice_text)
        self.assertNotIn("Set It Down", stage.choice_text)
        choice_rows = stage.choice_text.removesuffix("<Close>").splitlines()
        self.assertEqual(
            choice_rows[1:],
            ["     Turn It On", "     Leave It Off"],
        )

        source_count = (
            struct.unpack_from(
                "<I",
                parse_field(self.chapter_sources[1]).parts[
                    rico.DIALOGUE_INDEX
                ].data,
                0,
            )[0]
            + 1
        )
        custom_texts = rico._playable_custom_texts(contract)
        custom_ids = {
            text: source_count + len(chapter.blocks) + index
            for index, text in enumerate(custom_texts)
        }
        choice_opcode = (
            rico._choice_dialog(custom_ids[stage.choice_text])
            + b"\xA9\x12\x9C"
        )
        bit_six_commit = rico.mass_driver._set_var_bit(
            rico.PLAYABLE_STATE_VARIABLE,
            6,
        )

        for disc in (1, 2):
            with self.subTest(disc=disc):
                (
                    _source_editor,
                    output_editor,
                    _contract,
                    first_controller,
                    _exit_entity,
                ) = self._chapter_layout(disc, 1)
                counter_entity = first_controller + counter_index
                action_pc = output_editor.get_script_pointer(counter_entity, 2)
                action = _pointed_body(output_editor, counter_entity, 2)
                self.assertEqual(action.count(choice_opcode), 1)
                ignition_click = rico._play_sound_effect(
                    rico.CHAPTER_ONE_STOVE_IGNITION_SOUND_ID
                )
                self.assertEqual(ignition_click, b"\x74\xF9\x80")
                self.assertEqual(action.count(ignition_click), 1)
                self.assertNotIn(rico._play_sound_effect(0x46), action)
                audio_helper = rico._chapter_one_stove_audio_helper()
                self.assertEqual(
                    output_editor.bytecode[
                        rico.CHAPTER_ONE_STOVE_AUDIO_HELPER_PC :
                        rico.CHAPTER_ONE_STOVE_AUDIO_HELPER_PC
                        + len(audio_helper)
                    ],
                    audio_helper,
                )
                timer_pc = output_editor.get_script_pointer(counter_entity, 1)
                timer = rico._chapter_one_kettle_timer_update(timer_pc)
                self.assertEqual(
                    output_editor.bytecode[timer_pc : timer_pc + len(timer)],
                    timer,
                )
                self.assertEqual(rico.CHAPTER_ONE_KETTLE_BOIL_FRAMES, 15 * 60)
                boil_wait = rico._wait(rico.CHAPTER_ONE_KETTLE_BOIL_FRAMES)
                boiled_commit = rico.mass_driver._set_var_bit(
                    rico.PLAYABLE_STATE_VARIABLE,
                    rico.CHAPTER_ONE_KETTLE_BOILED_BIT,
                )
                self.assertIn(boil_wait, timer)
                self.assertIn(boiled_commit, timer)
                self.assertNotIn(boil_wait, action)
                self.assertNotIn(boiled_commit, action)

                def bit_clear_test(bit: int) -> bytes:
                    return (
                        b"\x02"
                        + struct.pack("<H", rico.PLAYABLE_STATE_VARIABLE)
                        + struct.pack("<H", 1 << bit)
                        + b"\x46"
                    )

                dispatch_at = action.index(bit_clear_test(6))
                self.assertEqual(
                    action[dispatch_at + 8 : dispatch_at + 14],
                    bit_clear_test(10),
                )
                self.assertEqual(
                    action[dispatch_at + 16 : dispatch_at + 22],
                    bit_clear_test(9),
                )

                def route_state(offset: int, state: int) -> int:
                    visited: set[int] = set()
                    while action[offset] in (0x01, 0x02):
                        self.assertNotIn(offset, visited)
                        visited.add(offset)
                        if action[offset] == 0x01:
                            offset = (
                                struct.unpack_from("<H", action, offset + 1)[0]
                                - action_pc
                            )
                            continue
                        self.assertEqual(
                            action[offset + 1 : offset + 3],
                            struct.pack("<H", rico.PLAYABLE_STATE_VARIABLE),
                        )
                        self.assertEqual(action[offset + 5], 0x46)
                        mask = struct.unpack_from("<H", action, offset + 3)[0]
                        target = (
                            struct.unpack_from("<H", action, offset + 6)[0]
                            - action_pc
                        )
                        offset = target if state & mask == 0 else offset + 8
                    return offset

                water_carried_state = (1 << 2) | (1 << 3)
                stage_ids = rico._resolve_playable_dialogue(
                    stage.dialogue,
                    authored_base=source_count,
                    authored_count=len(chapter.blocks),
                    custom_ids=custom_ids,
                )
                stage_dialogue = rico._dialogue_sequence(stage_ids)
                filled_commit = rico.mass_driver._set_var_bit(
                    rico.PLAYABLE_STATE_VARIABLE,
                    rico.CHAPTER_ONE_KETTLE_FILLED_BIT,
                )
                bowl_ids = rico._resolve_playable_dialogue(
                    bowl_stage.dialogue,
                    authored_base=source_count,
                    authored_count=len(chapter.blocks),
                    custom_ids=custom_ids,
                )
                bowl_dialogue = (
                    rico.CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL
                    + rico._dialogue_sequence(bowl_ids)
                )
                for state in (
                    water_carried_state,
                    water_carried_state | (1 << 9),
                ):
                    ready_at = route_state(dispatch_at, state)
                    self.assertTrue(action.startswith(stage_dialogue, ready_at))
                    self.assertFalse(action.startswith(bowl_dialogue, ready_at))
                    self.assertTrue(
                        action.startswith(
                            stage_dialogue
                            + filled_commit
                            + rico._wait()
                            + choice_opcode,
                            ready_at,
                        )
                    )
                already_filled_state = water_carried_state | (
                    1 << rico.CHAPTER_ONE_KETTLE_FILLED_BIT
                )
                choice_ready_at = route_state(dispatch_at, already_filled_state)
                self.assertTrue(
                    action.startswith(rico._wait() + choice_opcode, choice_ready_at)
                )
                self.assertFalse(
                    action.startswith(stage_dialogue, choice_ready_at)
                )

                cup_ids = rico._resolve_playable_dialogue(
                    cup_stage.dialogue,
                    authored_base=source_count,
                    authored_count=len(chapter.blocks),
                    custom_ids=custom_ids,
                )
                cup_dialogue = rico._dialogue_sequence(cup_ids)
                cup_locked_dialogues = {
                    completed: rico._dialogue_sequence(
                        rico._resolve_playable_dialogue(
                            refs,
                            authored_base=source_count,
                            authored_count=len(chapter.blocks),
                            custom_ids=custom_ids,
                        )
                    )
                    for completed, refs in cup_stage.locked_dialogue_states
                }
                stove_on_state = already_filled_state | (1 << 6)
                for completed, state in (
                    ((), stove_on_state),
                    ((7,), stove_on_state | (1 << 7)),
                    (
                        (rico.CHAPTER_ONE_KETTLE_BOILED_BIT,),
                        stove_on_state
                        | (1 << rico.CHAPTER_ONE_KETTLE_BOILED_BIT),
                    ),
                ):
                    locked_at = route_state(dispatch_at, state)
                    self.assertTrue(
                        action.startswith(cup_locked_dialogues[completed], locked_at)
                    )
                    self.assertFalse(action.startswith(bowl_dialogue, locked_at))

                cup_ready_state = (
                    stove_on_state
                    | (1 << 7)
                    | (1 << rico.CHAPTER_ONE_KETTLE_BOILED_BIT)
                )
                for state in (
                    cup_ready_state,
                    cup_ready_state | (1 << 9),
                ):
                    cup_at = route_state(dispatch_at, state)
                    self.assertTrue(action.startswith(cup_dialogue, cup_at))
                    self.assertFalse(action.startswith(bowl_dialogue, cup_at))

                bowl_ready_state = cup_ready_state | (1 << 7) | (1 << 10)
                bowl_at = route_state(dispatch_at, bowl_ready_state)
                self.assertTrue(action.startswith(bowl_dialogue, bowl_at))
                bit_ten_commit = rico.mass_driver._set_var_bit(
                    rico.PLAYABLE_STATE_VARIABLE,
                    10,
                )
                self.assertEqual(action.count(bit_ten_commit), 1)

                choice_at = action.index(choice_opcode)
                comparison_at = choice_at + len(choice_opcode)
                self.assertEqual(
                    action[comparison_at : comparison_at + 6],
                    b"\x02"
                    + struct.pack("<H", rico.MENU_SELECTION_VARIABLE)
                    + struct.pack("<H", 1)
                    + b"\x40",
                )
                rejected_at = (
                    struct.unpack_from("<H", action, comparison_at + 6)[0]
                    - action_pc
                )
                success_at = comparison_at + 8
                after_ids = rico._resolve_playable_dialogue(
                    stage.after_dialogue,
                    authored_base=source_count,
                    authored_count=len(chapter.blocks),
                    custom_ids=custom_ids,
                )
                after_prefix = (
                    rico.CHAPTER_ONE_STOVE_AUDIO_HELPER_CALL
                    + rico.CHAPTER_ONE_ANNA_INTERACTION_COUGH_CALL
                    + rico._dialogue_sequence(after_ids)
                )
                self.assertTrue(
                    action.startswith(
                        ignition_click + after_prefix + bit_six_commit,
                        success_at,
                    )
                )

                rejected_ids = rico._resolve_playable_dialogue(
                    stage.rejection_dialogue,
                    authored_base=source_count,
                    authored_count=len(chapter.blocks),
                    custom_ids=custom_ids,
                )
                rejected_prefix = rico._wait() + rico._dialogue_sequence(
                    rejected_ids
                )
                self.assertTrue(action.startswith(rejected_prefix, rejected_at))
                self.assertFalse(action.startswith(ignition_click, rejected_at))
                self.assertNotIn(
                    bit_six_commit,
                    action[rejected_at : rejected_at + len(rejected_prefix)],
                )

    def test_every_unfinished_exit_routes_to_contextual_missing_step(self) -> None:
        generic_texts = {
            "Rico is not finished here yet.<Close>",
            "There is still something else to do first.<Close>",
        }
        for disc in (1, 2):
            for chapter_id in range(1, 8):
                with self.subTest(disc=disc, chapter=chapter_id):
                    chapter = self.chapters[chapter_id - 1]
                    (
                        _source_editor,
                        output_editor,
                        contract,
                        _first_controller,
                        exit_entity,
                    ) = self._chapter_layout(disc, chapter_id)
                    transition_bits = (
                        {contract.exit_transition.bit}
                        if contract.exit_transition is not None
                        else set()
                    )
                    self.assertEqual(
                        {bit for bit, _text in contract.exit_locked_steps},
                        set(contract.required_bits) - transition_bits,
                    )
                    self.assertEqual(
                        len(contract.exit_locked_steps),
                        len(contract.required_bits) - len(transition_bits),
                    )
                    custom_texts = rico._playable_custom_texts(contract)
                    self.assertTrue(generic_texts.isdisjoint(custom_texts))
                    source_count = (
                        struct.unpack_from(
                            "<I",
                            parse_field(self.chapter_sources[chapter_id])
                            .parts[rico.DIALOGUE_INDEX]
                            .data,
                            0,
                        )[0]
                        + 1
                    )
                    custom_ids = {
                        text: source_count + len(chapter.blocks) + index
                        for index, text in enumerate(custom_texts)
                    }
                    exit_pc = output_editor.get_script_pointer(exit_entity, 2)
                    action = _pointed_body(output_editor, exit_entity, 2)
                    branch_at = len(rico._playable_action_prefix(exit_pc))
                    compiled: list[tuple[int, int]] = []
                    for bit, text in contract.exit_locked_steps:
                        self.assertEqual(
                            action[branch_at : branch_at + 6],
                            b"\x02"
                            + struct.pack("<H", rico.PLAYABLE_STATE_VARIABLE)
                            + struct.pack("<H", 1 << bit)
                            + b"\x46",
                        )
                        target_pc = struct.unpack_from(
                            "<H",
                            action,
                            branch_at + 6,
                        )[0]
                        target_at = target_pc - exit_pc
                        dialogue = rico._dialogue_sequence((custom_ids[text],))
                        self.assertTrue(
                            action.startswith(
                                dialogue
                                + rico._playable_action_finish(
                                    target_pc + len(dialogue)
                                ),
                                target_at,
                            )
                        )
                        compiled.append((1 << bit, target_at))
                        branch_at += 8

                    set_bits: set[int] = set()
                    for index, (bit, _text) in enumerate(
                        contract.exit_locked_steps
                    ):
                        state = sum(1 << value for value in set_bits)
                        target = next(
                            target_at
                            for mask, target_at in compiled
                            if state & mask == 0
                        )
                        self.assertEqual(target, compiled[index][1])
                        set_bits.add(bit)
                    complete_state = sum(
                        1 << bit for bit in contract.required_bits
                    )
                    self.assertFalse(
                        any(complete_state & mask == 0 for mask, _ in compiled)
                    )
                    if contract.exit_transition is not None:
                        player_complete_state = sum(
                            1 << bit
                            for bit, _text in contract.exit_locked_steps
                        )
                        self.assertFalse(
                            any(
                                player_complete_state & mask == 0
                                for mask, _ in compiled
                            )
                        )
                        self.assertIn(
                            rico._change_field(
                                rico.CHAPTER_ONE_FIREWOOD_FIELD,
                                0,
                            ),
                            action[branch_at:],
                        )

    def test_title_new_game_route_normalizes_to_rico_alone(self) -> None:
        source = parse_field(self.title_source)
        source_editor = AtelScript(source.parts[rico.SCRIPT_INDEX].data)
        for disc in (1, 2):
            with self.subTest(disc=disc):
                output = parse_field(self.title_outputs[disc])
                output_editor = AtelScript(output.parts[rico.SCRIPT_INDEX].data)
                branch = output_editor.bytecode[
                    rico.TITLE_ROUTE_FALLTHROUGH_PC :
                    rico.TITLE_ROUTE_FALLTHROUGH_PC + 8
                ]
                self.assertEqual(branch[0], 0x01)
                self.assertEqual(branch[3:], bytes(5))
                route_pc = struct.unpack_from("<H", branch, 1)[0]
                route = rico._hub_launch_body(rico.HUB_FIELDS[disc])
                self.assertEqual(
                    output_editor.bytecode[route_pc : route_pc + len(route)],
                    route,
                )
                self.assertEqual(route_pc, source_editor.bytecode_size)
                adult_setup = rico._party_setup(rico.HUB_PARTY)
                self.assertTrue(route.startswith(adult_setup))
                self.assertEqual(
                    adult_setup.count(
                        b"\xFE\x18\x05\xFE\x1A"
                    ),
                    1,
                )
                self.assertEqual(
                    route.count(
                        rico.mass_driver._set_variable_s16(
                            rico.PLAYABLE_STATE_VARIABLE,
                            0,
                        )
                    ),
                    1,
                )
                self.assertTrue(
                    route.endswith(
                        rico._change_field(rico.HUB_FIELDS[disc], 0) + b"\x5B"
                    )
                )

        disc1 = parse_field(self.title_outputs[1])
        disc2 = parse_field(self.title_outputs[2])
        self.assertEqual(disc1.header, disc2.header)
        for index, (left, right) in enumerate(zip(disc1.parts, disc2.parts, strict=True)):
            if index == rico.SCRIPT_INDEX:
                self.assertEqual(
                    _normalize_local_routes(left.data),
                    _normalize_local_routes(right.data),
                )
            else:
                self.assertEqual(left.data, right.data)


class ChapterContractInvariantTests(RicoChapterSelectV2Fixtures):
    def test_compiled_story_dialogue_uses_anne_translation(self) -> None:
        for disc in (1, 2):
            with self.subTest(disc=disc):
                compiled_text = "\n".join(
                    text
                    for chapter in self.chapters
                    for text in _lenient_dialogue_texts(
                        parse_field(
                            self.chapter_outputs[disc, chapter.chapter_id]
                        ).parts[rico.DIALOGUE_INDEX].data
                    )
                )
                self.assertRegex(compiled_text, r"\bAnne\b")
                self.assertNotRegex(compiled_text, r"\bAnna\b")

    def test_every_noncompletion_interaction_has_contextual_repeat_dialogue(self) -> None:
        for chapter in self.chapters:
            contract = rico._playable_chapter_contract(chapter.chapter_id)
            for interaction in contract.interactions:
                if any(stage.completes_chapter for stage in interaction.stages):
                    continue
                with self.subTest(
                    chapter=chapter.chapter_id,
                    interaction=interaction.name,
                ):
                    self.assertTrue(interaction.repeat_dialogue)

    def test_every_prerequisite_has_contextual_guidance_without_generic_text(self) -> None:
        banned = (
            "There is still something else to do first.",
            "Rico is not finished here yet.",
        )
        for chapter in self.chapters:
            contract = rico._playable_chapter_contract(chapter.chapter_id)
            transition_bits = (
                {contract.exit_transition.bit}
                if contract.exit_transition is not None
                else set()
            )
            self.assertEqual(
                tuple(sorted(bit for bit, _text in contract.exit_locked_steps)),
                tuple(sorted(set(contract.required_bits) - transition_bits)),
            )
            for _bit, text in contract.exit_locked_steps:
                self.assertTrue(text.strip())
                self.assertTrue(all(phrase not in text for phrase in banned))
            for interaction in contract.interactions:
                for stage in interaction.stages:
                    locked_dialogues = (
                        (stage.locked_dialogue,)
                        if stage.locked_dialogue
                        else ()
                    ) + tuple(
                        dialogue
                        for _missing_bit, dialogue in (
                            stage.locked_dialogue_steps
                        )
                    ) + tuple(
                        dialogue
                        for _completed_bits, dialogue in (
                            stage.locked_dialogue_states
                        )
                    )
                    if stage.required_bits:
                        self.assertTrue(
                            locked_dialogues,
                            f"Chapter {chapter.chapter_id} {interaction.name} "
                            f"stage {stage.bit} lacks contextual guidance",
                        )
                    for dialogue in locked_dialogues:
                        for ref in dialogue:
                            if isinstance(ref, str):
                                self.assertTrue(
                                    all(phrase not in ref for phrase in banned)
                                )

        for output in self.chapter_outputs.values():
            searchable = "\n".join(
                _lenient_dialogue_texts(
                    parse_field(output).parts[rico.DIALOGUE_INDEX].data
                )
            )
            for phrase in banned:
                self.assertNotIn(phrase, searchable)

    def test_chapter_one_retires_the_shared_nothing_more_fallback(self) -> None:
        chapter = self.chapters[0]
        contract = rico._playable_chapter_contract(1)
        contextual = {
            interaction.name: interaction.repeat_dialogue
            for interaction in contract.interactions
            if not any(stage.completes_chapter for stage in interaction.stages)
        }
        self.assertEqual(
            set(contextual),
            {
                "settlement window",
                "gate window",
                "cold window",
                "room heater",
                "stonebell vase",
                "water buckets",
                "Anne's bedside",
                "reading desk",
                "cooking counter",
            },
        )
        self.assertTrue(
            all(
                len(dialogue) == 1
                and isinstance(dialogue[0], (int, str))
                for dialogue in contextual.values()
            )
        )

        retired = "There is nothing more to do here.<Close>"
        for disc in (1, 2):
            with self.subTest(disc=disc):
                dialogue = (
                    parse_field(self.chapter_outputs[disc, 1])
                    .parts[rico.DIALOGUE_INDEX]
                    .data
                )
                texts = _lenient_dialogue_texts(dialogue)
                self.assertNotIn(retired, texts)
                for name, repeat_dialogue in contextual.items():
                    with self.subTest(disc=disc, interaction=name):
                        repeat_ref = repeat_dialogue[0]
                        repeat_text = (
                            chapter.blocks[repeat_ref]
                            if isinstance(repeat_ref, int)
                            else repeat_ref
                        )
                        expected = rico._reflow_dialogue_text(repeat_text)
                        self.assertEqual(texts.count(expected), 1)

    def test_chapter_one_packed_dialogue_windows_fit_their_pages(self) -> None:
        chapter = self.chapters[0]
        texts = (
            *chapter.blocks,
            *rico._playable_custom_texts(rico._playable_chapter_contract(1)),
        )
        source_dialogue = parse_field(self.chapter_sources[1]).parts[
            rico.DIALOGUE_INDEX
        ].data
        authored_base = struct.unpack_from("<I", source_dialogue, 0)[0] + 1

        for disc in (1, 2):
            with self.subTest(disc=disc):
                dialogue = parse_field(self.chapter_outputs[disc, 1]).parts[
                    rico.DIALOGUE_INDEX
                ].data
                block_count = struct.unpack_from("<I", dialogue, 0)[0] + 1
                self.assertEqual(block_count, authored_base + len(texts))
                dimensions_start = 4 + block_count * 2
                fitted: list[tuple[int, int]] = []
                for index, text in enumerate(texts):
                    laid_out = rico._reflow_dialogue_text(
                        text,
                        sentence_safe_pages=True,
                    )
                    block_id = authored_base + index
                    actual = tuple(
                        dialogue[
                            dimensions_start + block_id * 2 :
                            dimensions_start + block_id * 2 + 2
                        ]
                    )
                    expected = rico._dialogue_window_dimensions(laid_out)
                    self.assertEqual(actual, expected)
                    fitted.append(actual)
                self.assertGreater(len(set(fitted)), 1)
                self.assertLess(
                    fitted.count(
                        (rico.DIALOGUE_WINDOW_WIDTH, rico.DIALOGUE_WINDOW_HEIGHT)
                    ),
                    len(fitted),
                )

    def test_chapter_one_output_uses_the_kettle_stonebell_and_teacup_sequence(self) -> None:
        chapter = self.chapters[0]
        contract = rico._playable_chapter_contract(1)
        custom_texts = rico._playable_custom_texts(contract)
        anna_positive_takeaway = rico._reflow_dialogue_text(chapter.blocks[8])
        obsolete_task_phrases = (
            "washstand",
            "bread table",
            "water and bread",
            "half a loaf",
            "set the bread beside me",
            "bread from the table",
            "bring anne water and bread",
            "buckets are beneath the window",
            "fill my cup",
            "open the heater vent",
            "fire can barely breathe",
            "leave it closed for now",
            "save a little water for the stonebell",
            "first, take the ladle",
            "water bucket in the corner",
            "two dented water buckets stand in the corner",
            "purple clay vase",
            "set it on the stove",
            "set the kettle on the stove",
            "lifts the kettle of hot tea",
            "sets down the kettle",
            "cup and the hot tea",
            "choose the door that matters",
            "people still waiting outside",
            "warden's record",
            "beneath the prison collar",
            "anne's pendant",
            "memento pendant",
            "husband, sigmund",
            "first, fill the kettle with water from the bucket",
            "turn on the cooking stove and let the water boil",
            "then put a pinch of the medicinal herbs in the cup",
            "bring me the tea",
            "one day, you'll follow in your father's footsteps",
            "when you rule kislev",
            "kaiser who breaks the cycle of hate",
            "daylight enters through the gray window",
            "holding his promise to anne close",
            "mom... you taught me that mercy breaks the cycle of hate",
            "when i follow dad's path",
            "i will not make them suffer because i suffered",
            "rocky cliff past nortune's outer wall",
            "rocky cliff",
            "you said you liked blue",
            "so i climbed up and brought it back for you",
            "most precious thing in this house",
            "brought it to me with love",
            "pale blue bells turn toward the light",
            "gives the world something gentle",
            "never let a cruel world take that choice",
            "i won't.<close>",
        )
        current_task_phrases = (
            "fetch some water from the bucket and make me some tea",
            "ladle",
            "fill the kettle",
            "turn on the stove",
            "turn it on",
            "pour in the hot water",
            "two dented water buckets stand underneath the window",
            "rusty orange clay vase",
            "another scoop of water",
            "stonebell in the vase",
            "streets near the market",
            "it was stepped on",
            "we could try to save it",
            "most precious gift i've ever received",
            "look how healthy it is now",
            "you've been taking care of it",
            "stonebells take root between bare stones",
            "pale blue bells always turn toward the light",
            "you have a good soul, rico",
            "never let this world forget that",
            "i won't, mom...",
            "kettle begins to whistle",
            "water has boiled",
            "pinch of dried medicinal herbs",
            "jar on the counter",
            "small chipped cup sits beside the jar of dried medicinal herbs",
            "places it into the cup",
            "pours in the steaming water",
            "sets the kettle back on the cooktop",
            "herbal tea is ready for anne",
            "i brought your cup, mom",
            "brings anne the cup",
            "mom's cup of hot tea",
            "stonebell",
            "open the valve",
            "more heat spreads through the house",
            "the doctors can do no more",
            "this sickness will take me soon",
            "cannot fight this sickness for me",
            "what do you want me to carry",
            "do not make others suffer because you are suffering",
            "protect people, not to take revenge",
            "cruelty that wounded us will end with you",
            "my stubborn boy",
            "done everything i asked",
            "daylight enters through the window",
            "mercy...",
            "end of chapter 1",
            "neighbor fell ill one winter",
            "stayed until the fever broke",
            "own long sickness",
            "endured with quiet courage",
            "young son, rico",
            "husband, who is still fighting far from home",
            "soul has returned to god",
            "may she rest in his peace",
        )

        for disc in (1, 2):
            with self.subTest(disc=disc):
                dialogue = (
                    parse_field(self.chapter_outputs[disc, 1])
                    .parts[rico.DIALOGUE_INDEX]
                    .data
                )
                texts = _lenient_dialogue_texts(dialogue)
                searchable = "\n".join(
                    " ".join(text.replace("<New>", " ").split())
                    for text in texts
                ).casefold()
                for phrase in obsolete_task_phrases:
                    self.assertNotIn(phrase, searchable)
                for phrase in current_task_phrases:
                    self.assertIn(phrase, searchable)
                self.assertEqual(searchable.count("chipped cup"), 1)
                for text in custom_texts:
                    self.assertEqual(
                        texts.count(rico._reflow_dialogue_text(text)),
                        1,
                    )
                for block_id in range(21, 26):
                    self.assertEqual(
                        texts.count(
                            rico._reflow_dialogue_text(chapter.blocks[block_id])
                        ),
                        1,
                    )

                # Removing the obsolete bread chore must not erase Anne's
                # positive statement of Rico's character.
                self.assertEqual(texts.count(anna_positive_takeaway), 1)
                self.assertIn("violence does not excuse violence in return", searchable)
                self.assertIn("mercy is choosing to end that cycle", searchable)
                self.assertIn("keep your heart gentle", searchable)
                self.assertIn(
                    "never let their cruelty decide who you become",
                    searchable,
                )

    def test_chapter_one_completed_actions_call_their_own_repeat_text(self) -> None:
        chapter = self.chapters[0]
        source_dialogue = parse_field(self.chapter_sources[1]).parts[
            rico.DIALOGUE_INDEX
        ].data
        authored_base = struct.unpack_from("<I", source_dialogue, 0)[0] + 1

        for disc in (1, 2):
            with self.subTest(disc=disc):
                (
                    _source_editor,
                    output_editor,
                    contract,
                    first_controller,
                    _exit_entity,
                ) = self._chapter_layout(disc, 1)
                custom_texts = rico._playable_custom_texts(contract)
                custom_ids = {
                    text: authored_base + len(chapter.blocks) + index
                    for index, text in enumerate(custom_texts)
                }
                routed_ids: dict[str, int] = {}
                for index, interaction in enumerate(contract.interactions):
                    if any(
                        stage.completes_chapter for stage in interaction.stages
                    ):
                        continue
                    repeat_ids = rico._resolve_playable_dialogue(
                        interaction.repeat_dialogue,
                        authored_base=authored_base,
                        authored_count=len(chapter.blocks),
                        custom_ids=custom_ids,
                    )
                    self.assertEqual(len(repeat_ids), 1)
                    repeat_id = repeat_ids[0]
                    routed_ids[interaction.name] = repeat_id
                    action = _pointed_body(
                        output_editor,
                        first_controller + index,
                        2,
                    )
                    self.assertEqual(action.count(rico._dialog(repeat_id)), 1)

                self.assertEqual(len(set(routed_ids.values())), len(routed_ids))

    def test_hammer_waits_for_arrival_and_snaps_upstairs_after_reload(self) -> None:
        (
            _source_editor,
            output_editor,
            contract,
            first_controller,
            _exit_entity,
        ) = self._chapter_layout(1, 2)
        interaction_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "Hammer"
        )
        interaction = contract.interactions[interaction_index]
        controller = first_controller + interaction_index
        self.assertEqual(
            _pointed_body(output_editor, controller, 0),
            rico._playable_controller_init(
                interaction.x,
                interaction.z,
                half_width=interaction.interaction_half_width,
                half_depth=interaction.interaction_half_depth,
                requires_facing=interaction.requires_facing,
                initially_disabled=True,
            ),
        )
        controller_gate_pc = output_editor.get_script_pointer(controller, 1)
        self.assertEqual(
            _pointed_body(output_editor, controller, 1),
            rico._chapter_two_hammer_controller_gate(
                controller_gate_pc,
                interaction.x,
                interaction.z,
            ),
        )

        hammer = rico.CHAPTER_TWO_HAMMER_ENTITY
        route_pc = output_editor.get_script_pointer(hammer, 1)
        route = _pointed_body(output_editor, hammer, 1)
        self.assertEqual(route, rico._chapter_two_hammer_stair_route(route_pc))
        climb_at = route.index(b"\x4B")
        self.assertEqual(struct.unpack_from("<H", route, 6)[0], route_pc + climb_at)
        end_x, end_z, _end_triangle = rico.CHAPTER_TWO_HAMMER_ROUTE[-1]
        reload_snap = (
            b"\x19"
            + rico._s16(end_x)
            + rico._s16(end_z)
            + b"\xC0"
            + rico.PLAYABLE_ACTOR_SOLID_FLAGS
            + b"\x5F\x04\x5B"
        )
        self.assertEqual(route[8:climb_at], reload_snap)
        arrived_commit = rico.mass_driver._set_var_bit(
            rico.CHAPTER_TWO_HAMMER_STATE_VARIABLE,
            rico.CHAPTER_TWO_HAMMER_ARRIVED_BIT,
        )
        self.assertEqual(route.count(arrived_commit), 1)
        self.assertGreater(route.index(arrived_commit), route.rindex(b"\x4B"))

        actor_gate_pc = output_editor.get_script_pointer(hammer, 2)
        controller_action_pc = output_editor.get_script_pointer(controller, 2)
        actor_gate = _pointed_body(output_editor, hammer, 2)
        self.assertEqual(
            actor_gate,
            rico._chapter_two_hammer_actor_action_gate(
                actor_gate_pc,
                controller_action_pc,
            ),
        )
        self.assertEqual(actor_gate[8:11], rico._jump(controller_action_pc))
        inactive_pc = struct.unpack_from("<H", actor_gate, 6)[0]
        inactive_offset = inactive_pc - actor_gate_pc
        self.assertTrue(
            actor_gate.startswith(
                rico._playable_action_prefix(inactive_pc),
                inactive_offset,
            )
        )

    def test_arrival_gates_hide_actor_and_disable_action_until_prerequisites(self) -> None:
        expected = {
            2: ("Fei", (1,), 1),
            3: ("Sigmund", (4,), 25),
            4: ("Sigmund", (1, 2, 3), 14),
        }
        for chapter_id, (name, bits, actor_entity) in expected.items():
            (
                _source_editor,
                output_editor,
                contract,
                first_controller,
                _exit_entity,
            ) = self._chapter_layout(1, chapter_id)
            interaction_index = next(
                index
                for index, interaction in enumerate(contract.interactions)
                if interaction.name == name
            )
            interaction = contract.interactions[interaction_index]
            controller = first_controller + interaction_index
            self.assertEqual(interaction.activation_required_bits, bits)
            self.assertTrue(interaction.hide_bound_actors_until_active)
            self.assertEqual(
                _pointed_body(output_editor, controller, 0),
                rico._playable_controller_init(
                    interaction.x,
                    interaction.z,
                    half_width=interaction.interaction_half_width,
                    half_depth=interaction.interaction_half_depth,
                    requires_facing=interaction.requires_facing,
                    initially_disabled=True,
                ),
            )
            controller_gate_pc = output_editor.get_script_pointer(controller, 1)
            self.assertEqual(
                _pointed_body(output_editor, controller, 1),
                rico._playable_controller_activation_gate(
                    controller_gate_pc,
                    bits,
                    interaction.x,
                    interaction.z,
                ),
            )
            controller_init = _pointed_body(output_editor, controller, 0)
            self.assertTrue(controller_init.endswith(b"\x23\x00"))
            self.assertNotIn(b"\x2A", controller_init)
            self.assertIn(
                b"\x19"
                + rico._s16(rico.PLAYABLE_CONTROLLER_PARK_POSITION[0])
                + rico._s16(rico.PLAYABLE_CONTROLLER_PARK_POSITION[1])
                + b"\xC0",
                controller_init,
            )
            self.assertIn(
                b"\x19"
                + rico._s16(interaction.x)
                + rico._s16(interaction.z)
                + b"\xC0",
                _pointed_body(output_editor, controller, 1),
            )

            actor_gate_pc = output_editor.get_script_pointer(actor_entity, 1)
            actor_gate = _pointed_body(output_editor, actor_entity, 1)
            self.assertEqual(
                actor_gate,
                rico._playable_actor_arrival_gate(actor_gate_pc, bits),
            )
            self.assertEqual(actor_gate[0], 0x23)
            self.assertIn(
                b"\x23" + rico.PLAYABLE_ACTOR_GHOST_FLAGS,
                actor_gate,
            )
            self.assertIn(
                rico.PLAYABLE_ACTOR_SOLID_FLAGS + b"\x22",
                actor_gate,
            )
            self.assertIn(b"\x22", actor_gate)
            self.assertEqual(
                _pointed_body(output_editor, actor_entity, 2),
                rico._playable_actor_action_gate(
                    output_editor.get_script_pointer(actor_entity, 2),
                    bits,
                    output_editor.get_script_pointer(controller, 2),
                ),
            )

    def test_fixed_point_terminal_and_prerequisite_closure_cover_every_chapter(self) -> None:
        for chapter in self.chapters:
            contract = rico._playable_chapter_contract(chapter.chapter_id)
            stages = [
                stage
                for interaction in contract.interactions
                for stage in interaction.stages
            ]
            stages_by_bit = {stage.bit: stage for stage in stages}
            self.assertEqual(len(stages_by_bit), len(stages))
            if contract.exit_transition is not None:
                transition = contract.exit_transition
                self.assertNotIn(transition.bit, stages_by_bit)
                stages_by_bit[transition.bit] = transition

            effective_requirements: dict[int, set[int]] = {}
            for interaction in contract.interactions:
                prior_stage_bits: set[int] = set()
                for stage in interaction.stages:
                    effective_requirements[stage.bit] = (
                        set(stage.required_bits)
                        | set(interaction.activation_required_bits)
                        | prior_stage_bits
                    )
                    prior_stage_bits = prior_stage_bits | {stage.bit}
            if contract.exit_transition is not None:
                effective_requirements[contract.exit_transition.bit] = set(
                    contract.exit_transition.required_bits
                )
            for timed in contract.timed_bits:
                self.assertNotIn(timed.bit, stages_by_bit)
                effective_requirements[timed.bit] = {timed.trigger_bit}

            reachable: set[int] = set()
            while True:
                new_bits = {
                    bit
                    for bit, requirements in effective_requirements.items()
                    if requirements <= reachable
                } - reachable
                if not new_bits:
                    break
                reachable.update(new_bits)
            self.assertTrue(set(stages_by_bit) <= reachable)
            for interaction in contract.interactions:
                self.assertTrue(
                    set(interaction.activation_required_bits) <= reachable
                )

            terminals = [
                (interaction, index, stage)
                for interaction in contract.interactions
                for index, stage in enumerate(interaction.stages)
                if stage.completes_chapter
            ]
            self.assertTrue(contract.completion_at_exit)
            self.assertEqual(terminals, [])
            self.assertFalse(
                set(contract.required_bits) & set(contract.optional_bits)
            )
            self.assertEqual(
                set(contract.required_bits) | set(contract.optional_bits),
                set(stages_by_bit),
            )
            closure = set(contract.required_bits)
            pending = list(contract.required_bits)
            while pending:
                bit = pending.pop()
                if bit in closure and not contract.completion_at_exit:
                    continue
                closure.add(bit)
                pending.extend(effective_requirements[bit])
            self.assertTrue(set(contract.required_bits) <= closure)

        chapter_one = rico._playable_chapter_contract(1)
        chapter_one_stages = {
            stage.bit: stage
            for interaction in chapter_one.interactions
            for stage in interaction.stages
        }
        self.assertEqual(chapter_one.optional_bits, (8, 9))
        self.assertEqual(
            chapter_one.timed_bits,
            (
                rico.PlayableTimedBit(
                    bit=rico.CHAPTER_ONE_KETTLE_BOILED_BIT,
                    trigger_bit=rico.CHAPTER_ONE_STOVE_ON_BIT,
                    frames=rico.CHAPTER_ONE_KETTLE_BOIL_FRAMES,
                ),
            ),
        )
        self.assertIn(7, chapter_one_stages)
        self.assertIn(8, chapter_one_stages)
        self.assertIn(9, chapter_one_stages)
        self.assertIn(10, chapter_one_stages)
        self.assertIn(11, chapter_one_stages)
        self.assertNotIn(5, chapter_one_stages)
        self.assertIsNotNone(chapter_one.exit_transition)
        assert chapter_one.exit_transition is not None
        self.assertEqual(chapter_one.exit_transition.bit, 5)
        self.assertEqual(
            set(chapter_one_stages) | {chapter_one.exit_transition.bit},
            set(chapter_one.required_bits) | set(chapter_one.optional_bits),
        )
        self.assertNotIn(8, chapter_one.required_bits)
        self.assertNotIn(9, chapter_one.required_bits)
        self.assertIn(11, chapter_one.required_bits)
        self.assertIn(10, chapter_one.required_bits)
        self.assertNotIn(8, chapter_one.exit_transition.required_bits)
        self.assertNotIn(9, chapter_one.exit_transition.required_bits)
        self.assertIn(11, chapter_one.exit_transition.required_bits)
        self.assertIn(10, chapter_one.exit_transition.required_bits)
        self.assertNotIn(8, {bit for bit, _text in chapter_one.exit_locked_steps})
        self.assertNotIn(9, {bit for bit, _text in chapter_one.exit_locked_steps})
        self.assertIn(11, {bit for bit, _text in chapter_one.exit_locked_steps})
        self.assertIn(10, {bit for bit, _text in chapter_one.exit_locked_steps})
        self.assertEqual(
            chapter_one.required_bits,
            (1, 2, 3, 4, 5, 6, 7, 10, 11),
        )
        self.assertEqual(chapter_one_stages[3].required_bits, (2,))
        self.assertEqual(chapter_one_stages[6].required_bits, (3,))
        self.assertEqual(chapter_one_stages[1].required_bits, (6,))
        self.assertEqual(chapter_one_stages[7].required_bits, (1,))
        self.assertEqual(
            chapter_one_stages[10].required_bits,
            (7, rico.CHAPTER_ONE_KETTLE_BOILED_BIT),
        )
        self.assertEqual(
            chapter_one_stages[4].required_bits,
            (
                3,
                rico.CHAPTER_ONE_STOVE_ON_BIT,
                1,
                7,
                rico.CHAPTER_ONE_HEATER_VALVE_BIT,
                rico.CHAPTER_ONE_KETTLE_BOILED_BIT,
                10,
            ),
        )
        self.assertEqual(
            chapter_one.exit_transition.required_bits,
            (2, 3, 6, 1, 7, 11, 10, 4),
        )
        self.assertEqual(
            tuple(bit for bit, _text in chapter_one.exit_locked_steps),
            (2, 3, 6, 1, 7, 11, 10, 4),
        )
        chapter_two = rico._playable_chapter_contract(2)
        self.assertEqual(chapter_two.required_bits, (1, 2, 3, 4, 5, 6))
        self.assertEqual(chapter_two.optional_bits, (7,))
        self.assertEqual(
            tuple(
                tuple(stage.bit for stage in interaction.stages)
                for interaction in chapter_two.interactions
            ),
            ((7,), (1, 4), (2, 5), (3, 6)),
        )
        self.assertEqual(
            {
                stage.bit: (
                    set(stage.required_bits)
                    | set(interaction.activation_required_bits)
                    | {
                        prior.bit
                        for prior in interaction.stages
                        if interaction.stages.index(prior)
                        < interaction.stages.index(stage)
                    }
                )
                for interaction in chapter_two.interactions
                for stage in interaction.stages
            },
            {
                1: set(),
                2: {1},
                3: {2},
                4: {1, 3},
                5: {1, 2, 4},
                6: {3, 5},
                7: set(),
            },
        )
        chapter_six = rico._playable_chapter_contract(6)
        chapter_six_stages = {
            stage.bit: stage
            for interaction in chapter_six.interactions
            for stage in interaction.stages
        }
        self.assertEqual(chapter_six_stages[2].required_bits, (1,))

    def test_validator_rejects_cycles_terminal_stages_and_bypasses(self) -> None:
        chapter = self.chapters[0]
        components = [
            part.data
            for part in parse_field(self.chapter_outputs[1, 1]).parts
        ]
        contract = rico._playable_chapter_contract(1)
        anna_index = next(
            index
            for index, interaction in enumerate(contract.interactions)
            if interaction.name == "Anne's bedside"
        )

        cyclic = _replace_stage(
            contract,
            anna_index,
            0,
            replace(
                contract.interactions[anna_index].stages[0],
                required_bits=(5,),
                locked_dialogue=("Anne\nCome sit with me first, Rico.<Close>",),
            ),
        )
        with self.assertRaisesRegex(rico.RicoArcBuildError, "unreachable progress"):
            rico._validate_playable_contract(components, chapter, cyclic)

        unexpected_terminal = _replace_stage(
            contract,
            anna_index,
            1,
            replace(
                contract.interactions[anna_index].stages[1],
                completes_chapter=True,
            ),
        )
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            "must complete at the exit; found 1 completion stages",
        ):
            rico._validate_playable_contract(
                components,
                chapter,
                unexpected_terminal,
            )

        self.assertIsNotNone(contract.exit_transition)
        assert contract.exit_transition is not None
        bypassed_bit = 7
        bypass = replace(
            contract,
            required_bits=tuple(
                bit for bit in contract.required_bits if bit != bypassed_bit
            ),
            exit_locked_steps=tuple(
                step
                for step in contract.exit_locked_steps
                if step[0] != bypassed_bit
            ),
            exit_transition=replace(
                contract.exit_transition,
                required_bits=tuple(
                    bit
                    for bit in contract.exit_transition.required_bits
                    if bit != bypassed_bit
                ),
            ),
        )
        with self.assertRaisesRegex(
            rico.RicoArcBuildError,
            "can bypass playable objective bits",
        ):
            rico._validate_playable_contract(components, chapter, bypass)

    def test_no_gameplay_route_displays_bracketed_screenplay_prose(self) -> None:
        for chapter in self.chapters:
            contract = rico._playable_chapter_contract(chapter.chapter_id)
            refs: list[rico.DialogueRef] = list(contract.exit_dialogue)
            for interaction in contract.interactions:
                for stage in interaction.stages:
                    refs.extend(stage.dialogue)
                    refs.extend(stage.after_dialogue)
                    refs.extend(stage.locked_dialogue)
                    for _missing_bit, step_dialogue in (
                        stage.locked_dialogue_steps
                    ):
                        refs.extend(step_dialogue)
                    for _completed_bits, state_dialogue in (
                        stage.locked_dialogue_states
                    ):
                        refs.extend(state_dialogue)
            if contract.exit_transition is not None:
                refs.extend(contract.exit_transition.doorway_dialogue)
                refs.extend(contract.exit_transition.firewood_dialogue)
                refs.extend(contract.exit_transition.sickness_dialogue)
                refs.extend(contract.exit_transition.loss_dialogue)
                refs.extend(contract.exit_transition.funeral_dialogue)
            bracketed = {
                ref
                for ref in refs
                if isinstance(ref, int)
                and chapter.blocks[ref].lstrip().startswith("[")
            }
            self.assertEqual(bracketed, set())

        chapter = self.chapters[3]
        contract = rico._playable_chapter_contract(4)
        bracketed_id = next(
            index
            for index, block in enumerate(chapter.blocks)
            if block.lstrip().startswith("[")
        )
        routed = _replace_stage(
            contract,
            0,
            0,
            replace(
                contract.interactions[0].stages[0],
                dialogue=(bracketed_id,),
            ),
        )
        components = [
            part.data
            for part in parse_field(self.chapter_outputs[1, 4]).parts
        ]
        with self.assertRaisesRegex(rico.RicoArcBuildError, "screenplay prose"):
            rico._validate_playable_contract(components, chapter, routed)

    def test_every_chapter_bundle_is_semantically_identical_on_both_discs(self) -> None:
        for chapter_id in range(1, 8):
            with self.subTest(chapter=chapter_id):
                disc1 = parse_field(self.chapter_outputs[1, chapter_id])
                disc2 = parse_field(self.chapter_outputs[2, chapter_id])
                # Packed component offsets in the prefix can legitimately
                # differ when the two-byte local field operand compresses
                # differently.  The actor count/table is semantic field data.
                self.assertEqual(disc1.header[0x18C:], disc2.header[0x18C:])
                self.assertEqual(len(disc1.parts), len(disc2.parts))
                for index, (left, right) in enumerate(
                    zip(disc1.parts, disc2.parts, strict=True)
                ):
                    if index == rico.SCRIPT_INDEX:
                        if chapter_id == 1:
                            # Both bedroom exits now lead to the shared daylight
                            # firewood field 377; its automatic story continues
                            # into shared aftermath field 376.
                            self.assertEqual(left.data, right.data)
                        else:
                            self.assertNotEqual(left.data, right.data)
                        self.assertEqual(
                            _normalize_local_routes(left.data),
                            _normalize_local_routes(right.data),
                        )
                    else:
                        self.assertEqual(left.data, right.data)


if __name__ == "__main__":
    unittest.main()
