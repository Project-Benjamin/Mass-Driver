from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT
from modules.soylent_system.tests.disc_fixtures import source_disc_path

import hashlib
import json
import struct
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import tools.build_surface_soylent_dungeon as soylent
from tools.xgdialog import parse_dialogue
from tools.xgfield import SIZE_TABLE_OFFSET, STREAM_COUNT, STREAM_TABLE_OFFSET, parse_field
from tools.xgscript import AtelScript as ScriptEditor


PROJECT_ROOT = REPOSITORY_ROOT
SOURCE_ROOT = PROJECT_ROOT / "work" / "reference_fields" / "surface_soylent_cd2"


class SurfaceSoylentDungeonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources: dict[int, tuple[bytes, bytes]] = {}
        missing: list[Path] = []
        for identity in soylent.SOURCE_FIELDS:
            bundle_path = SOURCE_ROOT / f"{identity.bundle_id}.bin"
            graphics_path = SOURCE_ROOT / f"{identity.graphics_id}.bin"
            missing.extend(path for path in (bundle_path, graphics_path) if not path.is_file())
            if bundle_path.is_file() and graphics_path.is_file():
                cls.sources[identity.scene] = (
                    bundle_path.read_bytes(),
                    graphics_path.read_bytes(),
                )
        if missing:
            raise AssertionError(
                "Surface Soylent canonical extraction is incomplete: "
                + ", ".join(str(path) for path in missing)
            )
        cls.prepared = tuple(
            soylent.prepare_playable_field(
                spec,
                *cls.sources[spec.identity.scene],
            )
            for spec in soylent.PLAYABLE_SCENES
        )
        cls.quarantine = soylent.prepare_quarantine_puzzle(
            next(item for item in cls.prepared if item.spec.identity.scene == 620)
        )

    def test_all_native_surface_fields_match_frozen_disc_two_sources(self) -> None:
        self.assertEqual(
            [identity.scene for identity in soylent.SOURCE_FIELDS],
            [620, 621, 622, 623, 624, 625, 626],
        )
        for identity in soylent.SOURCE_FIELDS:
            with self.subTest(scene=identity.scene):
                bundle, graphics = self.sources[identity.scene]
                parsed = parse_field(bundle)
                script = parsed.parts[soylent.SCRIPT_INDEX].data
                self.assertEqual(len(bundle), identity.bundle_size)
                self.assertEqual(hashlib.sha256(bundle).hexdigest(), identity.bundle_sha256)
                self.assertEqual(len(graphics), identity.graphics_size)
                self.assertEqual(hashlib.sha256(graphics).hexdigest(), identity.graphics_sha256)
                self.assertEqual(len(parsed.header), identity.header_size)
                self.assertEqual(
                    hashlib.sha256(parsed.header).hexdigest(), identity.header_sha256
                )
                self.assertEqual(len(script), identity.script_size)
                self.assertEqual(hashlib.sha256(script).hexdigest(), identity.script_sha256)

    def test_vertical_slice_outputs_are_deterministic_and_script_only(self) -> None:
        self.assertEqual(
            [item.spec.identity.scene for item in self.prepared],
            [623, 621, 620, 622],
        )
        for item in self.prepared:
            spec = item.spec
            with self.subTest(scene=spec.identity.scene):
                source = parse_field(item.source_bundle)
                patched = parse_field(item.bundle)
                self.assertEqual(len(item.bundle), spec.patched_bundle_size)
                self.assertEqual(
                    hashlib.sha256(item.bundle).hexdigest(),
                    spec.patched_bundle_sha256,
                )
                # The container directory is repacked because the ATEL stream grows;
                # decoded payload streams other than ATEL remain byte-identical.
                self.assertNotEqual(source.header, patched.header)
                self.assertEqual(item.graphics, self.sources[spec.identity.scene][1])
                self.assertEqual(len(source.parts), len(patched.parts))
                for index, (before, after) in enumerate(
                    zip(source.parts, patched.parts, strict=True)
                ):
                    if index == soylent.SCRIPT_INDEX:
                        self.assertNotEqual(before.data, after.data)
                    else:
                        self.assertEqual(before.data, after.data)

    def test_party_control_entries_and_edge_polls_are_exact(self) -> None:
        destinations = {
            (item.spec.identity.scene, edit.parameter): edit.playable
            for item in self.prepared
            for edit in item.spec.entry_edits
        }
        for item in self.prepared:
            spec = item.spec
            script = item.components[soylent.SCRIPT_INDEX]
            editor = ScriptEditor(script)
            with self.subTest(scene=spec.identity.scene):
                for edit in spec.entry_edits:
                    start = 1 + 7 * edit.parameter
                    self.assertEqual(
                        editor.bytecode[start : start + 7],
                        edit.playable.pack(),
                    )
                for index, party in enumerate(spec.party):
                    selector = soylent.PARTY_SELECTORS[index]
                    expected_init = (
                        b"\x16"
                        + soylent._immediate(selector)
                        + b"\xFE\x0D"
                        + soylent._immediate(selector)
                    )
                    self.assertEqual(editor.get_script_pointer(party.entity, 0), party.init_pc)
                    self.assertEqual(
                        editor.bytecode[party.init_pc : party.init_pc + 7],
                        expected_init,
                    )
                    self.assertEqual(
                        editor.get_script_pointer(party.entity, 1),
                        spec.playable_update_pc,
                    )
                self.assertEqual(
                    editor.bytecode[spec.playable_update_pc : spec.playable_update_pc + 2],
                    b"\xA7\x00",
                )
                self.assertEqual(
                    editor.get_script_pointer(spec.director_entity, 1),
                    spec.poll_pc,
                )
                expected_poll = soylent._edge_poll(
                    spec.poll_pc,
                    spec.party[0].entity,
                    spec.edges,
                )
                self.assertEqual(
                    editor.bytecode[spec.poll_pc : spec.poll_pc + len(expected_poll)],
                    expected_poll,
                )
                soylent.validate_walkmesh_contract(spec, item.components[1])
                for edge in spec.edges:
                    self.assertIn(
                        (edge.destination_field, edge.destination_parameter),
                        destinations,
                    )
                if spec.force_party_direction is not None:
                    for party in spec.party:
                        self.assertEqual(
                            editor.bytecode[party.init_pc + 7 : party.init_pc + 9],
                            b"\x5F" + bytes((spec.force_party_direction,)),
                        )

    def test_materialized_stage_records_route_and_preservation_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "stage"
            replacements = soylent.materialize(
                self.prepared,
                output,
                "Xenogears_PW_CD2.bin",
            )
            self.assertEqual([canonical for canonical, _ in replacements], [1852, 1848, 1846, 1850])
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["format"], soylent.OUTPUT_FORMAT)
            self.assertEqual(manifest["playable_route"], [623, 621, 620, 622])
            self.assertEqual(manifest["future_native_wings"], [624, 626, 625])
            self.assertEqual(manifest["preservation"]["changed_streams"], ["scripts"])
            self.assertEqual(manifest["preservation"]["graphics"], "byte-identical")
            self.assertEqual(
                manifest["preservation"]["container_header"],
                "deterministically repacked for the longer script stream",
            )
            for item, (_, replacement) in zip(self.prepared, replacements, strict=True):
                self.assertEqual(replacement.read_bytes(), item.bundle)
                clone = output / "clones" / f"field_{item.spec.identity.scene}"
                self.assertEqual((clone / "header.bin").read_bytes(), item.header)
                self.assertEqual((clone / "graphics.bin").read_bytes(), item.graphics)

    def test_quarantine_uses_four_authentic_rings_as_a_persistent_relay_puzzle(self) -> None:
        item = self.quarantine
        script = item.components[soylent.SCRIPT_INDEX]
        editor = ScriptEditor(script)
        self.assertEqual((len(script), hashlib.sha256(script).hexdigest()), (
            soylent.QUARANTINE_SCRIPT_SIZE,
            soylent.QUARANTINE_SCRIPT_SHA256,
        ))
        self.assertEqual(
            (len(item.components[7]), hashlib.sha256(item.components[7]).hexdigest()),
            (soylent.QUARANTINE_DIALOGUE_SIZE, soylent.QUARANTINE_DIALOGUE_SHA256),
        )
        self.assertEqual(
            (len(item.bundle), hashlib.sha256(item.bundle).hexdigest()),
            (soylent.QUARANTINE_BUNDLE_SIZE, soylent.QUARANTINE_BUNDLE_SHA256),
        )
        self.assertEqual(editor.get_script_pointer(1, 1), soylent.QUARANTINE_GATE_PC)
        self.assertEqual(
            editor.bytecode[
                soylent.QUARANTINE_GATE_PC :
                soylent.QUARANTINE_GATE_PC + len(soylent.QUARANTINE_GATE_ROUTINE)
            ],
            soylent.QUARANTINE_GATE_ROUTINE,
        )
        for entity, source_pointers, init_pc, action_pc, init_body, action_body in (
            soylent.QUARANTINE_RING_ROUTINES
        ):
            self.assertEqual(editor.get_script_pointer(entity, 0), init_pc)
            self.assertEqual(editor.get_script_pointer(entity, 1), source_pointers[1])
            self.assertEqual(editor.get_script_pointer(entity, 2), action_pc)
            self.assertEqual(editor.bytecode[init_pc : init_pc + len(init_body)], init_body)
            self.assertEqual(
                editor.bytecode[action_pc : action_pc + len(action_body)],
                action_body,
            )
        self.assertEqual(soylent.QUARANTINE_SELECTION_MASK, 0x00F0)
        self.assertEqual(soylent.QUARANTINE_VALID_SELECTION, 0x0070)
        self.assertEqual(
            [(edge.destination_field, edge.destination_parameter) for edge in item.spec.edges],
            [(621, 0), (565, 6)],
        )
        source_parts = parse_field(
            next(base.bundle for base in self.prepared if base.spec.identity.scene == 620)
        ).parts
        final_parts = parse_field(item.bundle).parts
        for index, (before, after) in enumerate(zip(source_parts, final_parts, strict=True)):
            if index in (soylent.SCRIPT_INDEX, 7):
                self.assertNotEqual(before.data, after.data)
            else:
                self.assertEqual(before.data, after.data)

    def test_quarantine_ring_interactions_are_on_walkable_floor(self) -> None:
        triangles = soylent._walkmesh_layer(self.quarantine.components[1], 0)
        for point, triangle in (
            ((264, 132), 252),
            ((-88, 132), 269),
            ((88, -132), 278),
            ((-264, -132), 227),
        ):
            self.assertTrue(soylent._point_inside_triangle(point, triangles[triangle]))


class SurfaceSoylentTitleIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        stage = PROJECT_ROOT / "work" / "mass_driver_v162_stage" / "replacements"
        paths = {
            1586: stage / "1586_title_screen_mass_driver_route.bin",
            1587: stage / "1587_title_screen_destination_labels.bin",
            2593: stage / "2593_menu_shared_mass_driver.bin",
            2595: stage / "2595_standalone_gamestate.bin",
            2599: stage / "2599_title_menu_mass_driver_only.bin",
        }
        missing = [path for path in paths.values() if not path.is_file()]
        if missing:
            raise AssertionError(
                "Mass-Driver release base is incomplete: "
                + ", ".join(str(path) for path in missing)
            )
        cls.base = {canonical_id: path.read_bytes() for canonical_id, path in paths.items()}
        cls.atlas, shared = soylent._surface_title_labels(cls.base[2593])
        cls.final = {
            1586: soylent._patch_surface_title_field(cls.base[1586]),
            1587: soylent._patch_surface_title_graphics(cls.base[1587], cls.atlas),
            2593: shared,
            2599: soylent._patch_surface_title_overlay(cls.base[2599]),
        }

    def test_title_resources_match_frozen_two_choice_release(self) -> None:
        for canonical_id, data in self.final.items():
            with self.subTest(canonical_id=canonical_id):
                expected_size, expected_sha256 = soylent.TITLE_FINAL_IDENTITIES[
                    canonical_id
                ]
                self.assertEqual(len(data), expected_size)
                self.assertEqual(hashlib.sha256(data).hexdigest(), expected_sha256)
        self.assertEqual(
            hashlib.sha256(self.base[2595]).hexdigest(),
            soylent.TITLE_BASE_IDENTITIES[2595][1],
        )

    def test_title_field_dispatches_surface_and_mass_driver_separately(self) -> None:
        script = parse_field(self.final[1586]).parts[soylent.SCRIPT_INDEX].data
        editor = ScriptEditor(script)
        self.assertEqual(len(script), soylent.TITLE_FIELD_SCRIPT_SIZE)
        self.assertEqual(
            hashlib.sha256(script).hexdigest(),
            soylent.TITLE_FIELD_SCRIPT_SHA256,
        )
        self.assertEqual(
            editor.bytecode[0x00B8 : 0x00C0],
            bytes.fromhex("02 02 04 00 00 40 6C 01"),
        )
        self.assertEqual(editor.bytecode[0x00C0 : 0x00C3], bytes.fromhex("01 71 01"))
        self.assertEqual(
            editor.bytecode[0x016C : 0x0171],
            soylent._change_field(soylent.SURFACE_ENTRY_FIELD, 0),
        )
        self.assertEqual(
            editor.bytecode[0x0171 : 0x0176],
            soylent._change_field(soylent.MASS_DRIVER_ENTRY_FIELD, 0),
        )

    def test_overlay_has_two_movable_rows_one_disabled_boundary_and_native_sounds(self) -> None:
        overlay = self.final[2599]
        self.assertEqual(overlay[0x001C : 0x0024], bytes.fromhex("50 54 1C 80 2C 5A 1C 80"))
        self.assertEqual(overlay[0x01FC : 0x0200], bytes.fromhex("B0 31 1E 80"))
        self.assertEqual(overlay[0x0960 : 0x0964], bytes.fromhex("8E FE 62 10"))
        self.assertEqual(overlay[0x0970 : 0x0974], bytes.fromhex("83 FE 71 10"))
        self.assertEqual(overlay[0x1AFC : 0x1B00], bytes.fromhex("02 00 02 34"))
        self.assertEqual(
            overlay[
                soylent.mass_driver.TITLE_MENU_CONFIRM_SOUND_DISPATCH_OFFSET :
                soylent.mass_driver.TITLE_MENU_CONFIRM_SOUND_DISPATCH_OFFSET + 8
            ],
            soylent.mass_driver.TITLE_MENU_CONFIRM_SOUND_DISPATCH,
        )
        self.assertEqual(
            overlay[0x0A2C : 0x0A40],
            bytes.fromhex(
                "0C 80 01 3C 01 00 02 34 6A 3E 22 A4 "
                "12 15 07 08 00 00 00 00"
            ),
        )
        # Surface joins the native case-9 path after its redundant initial-
        # state reload, then clears both loop flags and runs normal cleanup.
        self.assertEqual(
            overlay[0x0440 : 0x0450],
            bytes.fromhex(
                "5C 6E 00 0C 00 00 00 00 21 80 00 00 21 88 00 00"
            ),
        )
        self.assertEqual(overlay[0x0A40 : 0x0A44], bytes(4))

    def test_surface_label_uses_active_palette_and_mahanon_stays_disabled(self) -> None:
        atlas_offset = soylent.mass_driver.TITLE_MENU_GRAPHICS_LABEL_PIXELS_OFFSET
        atlas = self.final[1587][atlas_offset : atlas_offset + 1152]
        self.assertEqual(hashlib.sha256(atlas).hexdigest(), soylent.SURFACE_TITLE_ATLAS_SHA256)
        _header, entries = soylent._split_menu_archive(self.final[2593])
        font, consumed = soylent.mass_driver._decode_lzss_complete_groups(
            entries[soylent.mass_driver.TITLE_MENU_FONT_ARCHIVE_ENTRY]
        )
        self.assertLessEqual(consumed, len(entries[soylent.mass_driver.TITLE_MENU_FONT_ARCHIVE_ENTRY]))
        self.assertEqual(hashlib.sha256(font).hexdigest(), soylent.SURFACE_TITLE_FONT_SHA256)
        _count, _offsets, records = soylent.mass_driver._title_menu_font_records(font)
        cluts = []
        for glyph in soylent.mass_driver.TITLE_MENU_LABEL_GLYPHS:
            values = struct.unpack_from("<14h", records[glyph], 4)
            cluts.append(values[9:11])
        self.assertEqual(
            cluts,
            [
                soylent.mass_driver.TITLE_MENU_STANDARD_CLUT,
                soylent.mass_driver.TITLE_MENU_STANDARD_CLUT,
                soylent.mass_driver.TITLE_MENU_DISABLED_CLUT,
            ],
        )

    def test_checked_v163_disc_produces_the_same_title_resources(self) -> None:
        source_disc = PROJECT_ROOT / "output" / "Xenogears_PW_CD2_mass_driver_standalone_v163.bin"
        self.assertTrue(source_disc.is_file(), f"Missing checked base disc: {source_disc}")
        prepared = soylent.prepare_title_integration(source_disc)
        self.assertEqual(
            {item.canonical_id: item.data for item in prepared},
            self.final,
        )


class SurfaceSoylentCompleteDungeonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_disc = source_disc_path("mass_driver_base")
        cls.donor_disc = source_disc_path("pw_disc1")
        if not cls.source_disc.is_file() or not cls.donor_disc.is_file():
            raise AssertionError(
                f"Complete Surface sources are missing: {cls.source_disc}, {cls.donor_disc}"
            )
        cls.prepared, cls.donors = soylent.prepare_complete_route(
            cls.source_disc,
            cls.donor_disc,
        )

    def test_complete_route_has_all_native_and_donor_rooms(self) -> None:
        self.assertEqual(
            [item.spec.identity.scene for item in self.prepared],
            [623, 621, 620, 624, 626, 625, 622],
        )
        self.assertEqual(
            [item.identity.scene for item in self.donors],
            [549, 550, 565, 589],
        )
        for item in self.prepared:
            with self.subTest(native_scene=item.spec.identity.scene):
                expected = soylent.COMPLETE_INTERACTION_FINAL_IDENTITIES[
                    item.spec.identity.scene
                ]
                self.assertEqual(
                    (
                        len(item.components[soylent.SCRIPT_INDEX]),
                        hashlib.sha256(
                            item.components[soylent.SCRIPT_INDEX]
                        ).hexdigest(),
                        len(item.bundle),
                        hashlib.sha256(item.bundle).hexdigest(),
                    ),
                    expected,
                )
                self.assertEqual(
                    (
                        item.spec.patched_script_size,
                        item.spec.patched_script_sha256,
                        item.spec.patched_bundle_size,
                        item.spec.patched_bundle_sha256,
                    ),
                    expected,
                )
                dialogue_identity = soylent.NATIVE_NPC_DIALOGUE_IDENTITIES.get(
                    item.spec.identity.scene
                )
                if dialogue_identity is not None:
                    self.assertEqual(
                        (
                            len(item.components[7]),
                            hashlib.sha256(item.components[7]).hexdigest(),
                        ),
                        dialogue_identity,
                    )
        for item in self.donors:
            with self.subTest(donor_scene=item.identity.scene):
                if item.identity.scene == 565:
                    expected = soylent.INTERACTIVE_DONOR_FINAL_IDENTITIES[565]
                    self.assertEqual(
                        (
                            len(item.components[soylent.SCRIPT_INDEX]),
                            hashlib.sha256(
                                item.components[soylent.SCRIPT_INDEX]
                            ).hexdigest(),
                            len(item.components[7]),
                            hashlib.sha256(item.components[7]).hexdigest(),
                            len(item.bundle),
                            hashlib.sha256(item.bundle).hexdigest(),
                        ),
                        expected,
                    )
                else:
                    script_size, script_sha, bundle_size, bundle_sha = (
                        soylent.INTERACTIVE_DONOR_FINAL_IDENTITIES[
                            item.identity.scene
                        ]
                    )
                    self.assertEqual(
                        (
                            len(item.components[soylent.SCRIPT_INDEX]),
                            hashlib.sha256(
                                item.components[soylent.SCRIPT_INDEX]
                            ).hexdigest(),
                            len(item.bundle),
                            hashlib.sha256(item.bundle).hexdigest(),
                        ),
                        (script_size, script_sha, bundle_size, bundle_sha),
                    )

    def test_complete_route_destinations_all_have_audited_entries(self) -> None:
        destinations = {
            (item.spec.identity.scene, edit.parameter)
            for item in self.prepared
            for edit in item.spec.entry_edits
        }
        destinations.update(
            (item.identity.scene, parameter)
            for item in self.donors
            for parameter, _triangle in item.entry_triangles
        )
        for item in self.prepared:
            for edge in item.spec.edges:
                self.assertIn(
                    (edge.destination_field, edge.destination_parameter),
                    destinations,
                    f"missing destination for field {item.spec.identity.scene}",
                )
        expected_edges = {
            623: [(621, 6), (622, 1)],
            621: [
                (623, 1),
                (620, 0),
                (549, 0),
                (550, 0),
                (565, 0),
                (565, 2),
                (565, 3),
            ],
            620: [(621, 0), (565, 6)],
            624: [(565, 1), (626, 0)],
            626: [(624, 1), (625, 0)],
            625: [(626, 1), (622, 0)],
            622: [(625, 1), (623, 0)],
        }
        self.assertEqual(
            {
                item.spec.identity.scene: [
                    (edge.destination_field, edge.destination_parameter)
                    for edge in item.spec.edges
                ]
                for item in self.prepared
            },
            expected_edges,
        )

        native_links = {
            (scene, door.destination_field, door.destination_parameter)
            for scene, doors in soylent.NATIVE_DOOR_CONTROLLERS.items()
            for door in doors
        }
        donor_links = {
            (549, 621, 2),
            (550, 621, 3),
            (565, 621, 1),
            (565, 621, 4),
            (565, 621, 5),
            (565, 620, 1),
            (565, 589, 0),
            (565, 624, 0),
            (589, 565, 4),
        }
        links = native_links | donor_links
        reciprocal_pairs = (
            ((623, 621, 6), (621, 623, 1)),
            ((621, 620, 0), (620, 621, 0)),
            ((621, 549, 0), (549, 621, 2)),
            ((621, 550, 0), (550, 621, 3)),
            ((621, 565, 0), (565, 621, 1)),
            ((621, 565, 2), (565, 621, 4)),
            ((621, 565, 3), (565, 621, 5)),
            ((620, 565, 6), (565, 620, 1)),
            ((565, 624, 0), (624, 565, 1)),
            ((624, 626, 0), (626, 624, 1)),
            ((626, 625, 0), (625, 626, 1)),
            ((625, 622, 0), (622, 625, 1)),
            ((565, 589, 0), (589, 565, 4)),
            ((623, 622, 1), (622, 623, 0)),
        )
        self.assertEqual(links, {link for pair in reciprocal_pairs for link in pair})

    def test_all_native_routes_use_spatial_script_two_doors(self) -> None:
        original_poll_pcs = {
            623: 0x0912,
            621: 0x0202,
            620: 0x07E2,
            624: 0x12F2,
            626: 0x0DFE,
            625: 0x0A82,
            622: 0x0DEE,
        }
        for item in self.prepared:
            scene = item.spec.identity.scene
            editor = ScriptEditor(item.components[soylent.SCRIPT_INDEX])
            doors = soylent.NATIVE_DOOR_CONTROLLERS[scene]
            added_doors = tuple(
                door for door in doors if door.carrier_entity is None
            )
            source_editor = ScriptEditor(
                parse_field(item.source_bundle).parts[soylent.SCRIPT_INDEX].data
            )
            first_added_entity = source_editor.entity_count
            animations = soylent.NATIVE_DOOR_ANIMATIONS.get(scene, ())
            all_animations = animations + (
                (soylent.QUARANTINE_EAST_DOOR_ANIMATION,)
                if scene == 620
                else ()
            )
            animated_leaves = tuple(
                leaf
                for animation in all_animations
                for leaf in animation.leaves
            )
            self.assertEqual(
                editor.entity_count,
                source_editor.entity_count
                + len(added_doors)
                + len(animated_leaves),
            )

            stop_pc = editor.get_script_pointer(item.spec.director_entity, 1)
            self.assertEqual(stop_pc, item.spec.poll_pc)
            self.assertEqual(editor.bytecode[stop_pc], 0)
            self.assertNotEqual(stop_pc, original_poll_pcs[scene])
            self.assertNotIn(
                original_poll_pcs[scene],
                {
                    editor.get_script_pointer(entity, script_index)
                    for entity in range(editor.entity_count)
                    for script_index in range(32)
                },
                f"field {scene} still has a live automatic edge poll",
            )
            if scene in soylent.NATIVE_ROUTE_STOP_PCS:
                self.assertEqual(stop_pc, soylent.NATIVE_ROUTE_STOP_PCS[scene])

            triangles = soylent._walkmesh_layer(item.components[1], 0)
            next_added_entity = first_added_entity
            carrier_entities: list[int] = []
            for door in doors:
                entity = door.carrier_entity
                if entity is None:
                    entity = next_added_entity
                    next_added_entity += 1
                    for script_index in range(32):
                        if script_index not in (0, 2):
                            self.assertEqual(
                                editor.get_script_pointer(entity, script_index),
                                stop_pc,
                            )
                else:
                    collision_pc = editor.get_script_pointer(entity, 3)
                    self.assertEqual(editor.bytecode[collision_pc], 0)
                carrier_entities.append(entity)

                init_pc = editor.get_script_pointer(entity, 0)
                expected_init = soylent._door_controller_init(door)
                self.assertEqual(
                    editor.bytecode[init_pc : init_pc + len(expected_init)],
                    expected_init,
                )
                if door.carrier_entity is None:
                    # Added blank entities must enter an active scheduler class.
                    # INIT_ENTITY_SCRIPT (BC) accepts X selection but leaves the
                    # queued script frozen forever on an otherwise blank actor.
                    self.assertTrue(expected_init.startswith(b"\x0B\x00\x80"))
                    self.assertNotEqual(expected_init[0], 0xBC)
                    self.assertIn(bytes.fromhex("F8 00 10 00"), expected_init)
                    self.assertIn(
                        b"\x18"
                        + bytes(
                            (
                                door.interaction_half_width,
                                door.interaction_half_depth,
                                0x64,
                                min(
                                    door.interaction_half_width,
                                    door.interaction_half_depth,
                                ),
                            )
                        ),
                        expected_init,
                    )
                else:
                    self.assertTrue(expected_init.startswith(door.init_prefix))
                    self.assertIn(bytes.fromhex("F8 00 10 00"), expected_init)
                    self.assertNotIn(bytes.fromhex("20 01 80"), expected_init)
                self.assertIn(bytes.fromhex("F8 00 00 20"), expected_init)
                self.assertIn(bytes.fromhex("F8 07 04 00"), expected_init)
                self.assertNotIn(b"\x2A", expected_init)

                action_pc = editor.get_script_pointer(entity, 2)
                animation = next(
                    (
                        candidate
                        for candidate in animations
                        if (
                            candidate.destination_field,
                            candidate.destination_parameter,
                        )
                        == (
                            door.destination_field,
                            door.destination_parameter,
                        )
                    ),
                    None,
                )
                existing_helper = next(
                    (
                        candidate
                        for candidate in soylent.NATIVE_EXISTING_DOOR_HELPERS.get(
                            scene, ()
                        )
                        if candidate[:2]
                        == (door.destination_field, door.destination_parameter)
                    ),
                    None,
                )
                if animation is not None:
                    expected_action = soylent._animated_door_transition_action(
                        door,
                        animation,
                        action_pc,
                    )
                elif existing_helper is not None:
                    expected_action = soylent._existing_helper_door_transition_action(
                        door,
                        existing_helper[2],
                        action_pc,
                    )
                elif door.action_kind == "quarantine_gate":
                    expected_action = soylent.QUARANTINE_DOOR_GATE_FINAL_ROUTINE
                else:
                    expected_action = soylent._door_transition_action(door)
                self.assertEqual(
                    editor.bytecode[action_pc : action_pc + len(expected_action)],
                    expected_action,
                )
                if animation is not None or existing_helper is not None:
                    if door.action_kind == "discovery_gate":
                        self.assertTrue(
                            expected_action.startswith(
                                b"\x02"
                                + soylent._u16(
                                    soylent.SURFACE_SHORTCUT_STATE_OPERAND
                                )
                                + soylent._u16(
                                    soylent.SURFACE_SHORTCUT_DISCOVERED_BIT
                                )
                                + b"\x46"
                            )
                        )
                        self.assertEqual(
                            expected_action[8:11],
                            b"\x33\xFE\x54",
                        )
                    else:
                        self.assertTrue(
                            expected_action.startswith(b"\x33\xFE\x54")
                        )
                    self.assertEqual(expected_action.count(b"\x74\x77\x80"), 1)
                    if animation is not None:
                        for leaf in animation.leaves[:-1]:
                            self.assertIn(
                                b"\x07" + bytes((leaf.helper_entity, 0x24)),
                                expected_action,
                            )
                        blocking_helper = animation.leaves[-1].helper_entity
                    else:
                        blocking_helper = existing_helper[2]
                    self.assertIn(
                        b"\x09" + bytes((blocking_helper, 0x24)),
                        expected_action,
                    )
                    transition = (
                        soylent._change_field(
                            door.destination_field,
                            door.destination_parameter,
                        )
                        + b"\x5B"
                    )
                    if door.action_kind == "discovery_gate":
                        self.assertIn(transition, expected_action)
                    else:
                        self.assertTrue(expected_action.endswith(transition))
                self.assertTrue(
                    soylent._point_inside_triangle(
                        (door.x, door.z), triangles[door.triangle]
                    ),
                    f"field {scene} carrier left triangle {door.triangle}",
                )
            self.assertEqual(len(carrier_entities), len(set(carrier_entities)))
            self.assertEqual(
                tuple(leaf.helper_entity for leaf in animated_leaves),
                tuple(range(next_added_entity, editor.entity_count)),
            )
            for animation in all_animations:
                for leaf in animation.leaves:
                    init_pc = editor.get_script_pointer(leaf.helper_entity, 0)
                    slide_pc = editor.get_script_pointer(leaf.helper_entity, 4)
                    self.assertEqual(editor.bytecode[init_pc : init_pc + 3], b"\xBC\x2A\x00")
                    self.assertEqual(
                        editor.bytecode[
                            slide_pc : slide_pc + animation.frames * 9 + 1
                        ],
                        soylent.mass_driver._world_position_static_slide_body(
                            start_x=0,
                            start_z=0,
                            delta_x=leaf.delta_x,
                            delta_z=leaf.delta_z,
                            iterations=animation.frames,
                        ),
                    )
                    for script_index in range(32):
                        if script_index not in (0, 4):
                            pointer = editor.get_script_pointer(
                                leaf.helper_entity, script_index
                            )
                            self.assertEqual(editor.bytecode[pointer], 0)

    def test_added_door_headers_preserve_every_static_model_record(self) -> None:
        by_scene = {item.spec.identity.scene: item for item in self.prepared}
        for scene in (623, 621, 620, 622):
            with self.subTest(scene=scene):
                item = by_scene[scene]
                source_header = parse_field(item.source_bundle).header
                final_header = item.header
                source_editor = ScriptEditor(
                    parse_field(item.source_bundle).parts[soylent.SCRIPT_INDEX].data
                )
                final_editor = ScriptEditor(item.components[soylent.SCRIPT_INDEX])
                old_count = source_editor.entity_count
                added_doors = tuple(
                    door
                    for door in soylent.NATIVE_DOOR_CONTROLLERS[scene]
                    if door.carrier_entity is None
                )
                source_actor_count = struct.unpack_from("<H", source_header, 0x18C)[0]
                final_actor_count = struct.unpack_from("<H", final_header, 0x18C)[0]

                animations = soylent.NATIVE_DOOR_ANIMATIONS.get(scene, ()) + (
                    (soylent.QUARANTINE_EAST_DOOR_ANIMATION,)
                    if scene == 620
                    else ()
                )
                animated_leaves = tuple(
                    leaf
                    for animation in animations
                    for leaf in animation.leaves
                )
                self.assertEqual(
                    final_editor.entity_count,
                    old_count + len(added_doors) + len(animated_leaves),
                )
                self.assertEqual(final_actor_count, source_actor_count + len(added_doors))
                self.assertGreaterEqual(final_actor_count, final_editor.entity_count)
                self.assertEqual(final_header, parse_field(item.bundle).header)
                self.assertEqual(
                    (len(final_header), hashlib.sha256(final_header).hexdigest()),
                    soylent.PACKED_INTERACTION_HEADER_IDENTITIES[scene],
                )
                # Normalize the rebuilt stream size/offset tables and the one
                # intentional totalObjects change; all other fixed metadata
                # must stay retail-exact.
                normalized = bytearray(final_header[:0x190])
                for table_offset in (SIZE_TABLE_OFFSET, STREAM_TABLE_OFFSET):
                    normalized[
                        table_offset : table_offset + STREAM_COUNT * 4
                    ] = source_header[
                        table_offset : table_offset + STREAM_COUNT * 4
                    ]
                normalized[0x18C:0x18E] = source_header[0x18C:0x18E]
                self.assertEqual(bytes(normalized), source_header[:0x190])

                source_records = [
                    source_header[0x190 + index * 16 : 0x190 + (index + 1) * 16]
                    for index in range(source_actor_count)
                ]
                final_records = [
                    final_header[0x190 + index * 16 : 0x190 + (index + 1) * 16]
                    for index in range(final_actor_count)
                ]
                inserted = [
                    soylent.mass_driver._field_actor_record(
                        0x01E0, door.x, door.z, 0
                    )
                    for door in added_doors
                ]
                expected_records = (
                    source_records[:old_count]
                    + inserted
                    + source_records[old_count:]
                )
                if animated_leaves:
                    promoted: list[bytes] = []
                    source_indices = {
                        leaf.source_header_entity for leaf in animated_leaves
                    }
                    for leaf in animated_leaves:
                        record = bytearray(expected_records[leaf.source_header_entity])
                        self.assertEqual(struct.unpack_from("<H", record)[0], leaf.source_flags)
                        self.assertEqual(struct.unpack_from("<H", record, 14)[0], leaf.model_index)
                        struct.pack_into("<H", record, 0, 0x0290)
                        promoted.append(bytes(record))
                    expected_records = [
                        record
                        for index, record in enumerate(expected_records)
                        if index not in source_indices
                    ]
                    first_helper = old_count + len(added_doors)
                    expected_records[first_helper:first_helper] = promoted
                self.assertEqual(final_records, expected_records)

    def test_quarantine_two_panel_threshold_and_shared_success_are_exact(self) -> None:
        item = next(
            item for item in self.prepared if item.spec.identity.scene == 620
        )
        west, east = soylent.NATIVE_DOOR_CONTROLLERS[620]
        self.assertEqual(
            (
                west.x,
                west.z,
                west.interaction_half_width,
                west.interaction_half_depth,
                west.destination_field,
                west.destination_parameter,
                west.triangle,
            ),
            (-352, 0, 0x10, 0x18, 621, 0, 100),
        )
        self.assertEqual(
            (
                east.x,
                east.z,
                east.interaction_half_width,
                east.interaction_half_depth,
                east.destination_field,
                east.destination_parameter,
                east.triangle,
                east.action_kind,
            ),
            (352, 0, 0x10, 0x18, 565, 6, 182, "quarantine_gate"),
        )
        self.assertEqual(
            tuple(
                (edge.sample, edge.triangle)
                for edge in item.spec.edges
            ),
            (((-352, 0), 100), ((352, 0), 182)),
        )
        entries = {edit.parameter: edit for edit in item.spec.entry_edits}
        self.assertEqual(
            (entries[0].playable.x, entries[0].playable.z, entries[0].triangle),
            (-300, 0, 104),
        )
        self.assertEqual(
            (entries[1].playable.x, entries[1].playable.z, entries[1].triangle),
            (300, 0, 183),
        )
        self.assertGreaterEqual(entries[0].playable.x - west.x, 0x10 * 2 + 16)
        self.assertGreaterEqual(east.x - entries[1].playable.x, 0x10 * 2 + 16)

        editor = ScriptEditor(item.components[soylent.SCRIPT_INDEX])
        self.assertEqual(editor.entity_count, 27)
        west_leaf = soylent.NATIVE_DOOR_ANIMATIONS[620][0].leaves[0]
        east_leaf = soylent.QUARANTINE_EAST_DOOR_ANIMATION.leaves[0]
        self.assertEqual(
            (
                west_leaf.source_header_entity,
                west_leaf.helper_entity,
                west_leaf.source_flags,
                west_leaf.model_index,
                west_leaf.delta_x,
                west_leaf.delta_z,
            ),
            (25, 25, 0x0290, 0, 0, 2),
        )
        self.assertEqual(
            (
                east_leaf.source_header_entity,
                east_leaf.helper_entity,
                east_leaf.source_flags,
                east_leaf.model_index,
                east_leaf.delta_x,
                east_leaf.delta_z,
            ),
            (26, 26, 0x0290, 0, 0, -2),
        )
        east_record = item.header[0x190 + 26 * 16 : 0x190 + 27 * 16]
        self.assertEqual(struct.unpack_from("<H", east_record)[0], 0x0290)
        self.assertEqual(struct.unpack_from("<H", east_record, 14)[0], 0)

        self.assertEqual(
            editor.get_script_pointer(east_leaf.helper_entity, 0),
            soylent.QUARANTINE_EAST_DOOR_INIT_PC,
        )
        self.assertEqual(
            editor.bytecode[
                soylent.QUARANTINE_EAST_DOOR_INIT_PC :
                soylent.QUARANTINE_EAST_DOOR_INIT_PC + 3
            ],
            b"\xBC\x2A\x00",
        )
        self.assertEqual(
            editor.get_script_pointer(east_leaf.helper_entity, 4),
            soylent.QUARANTINE_EAST_DOOR_SLIDE_PC,
        )
        expected_slide = soylent.mass_driver._world_position_static_slide_body(
            start_x=0,
            start_z=0,
            delta_x=0,
            delta_z=-2,
            iterations=32,
        )
        self.assertEqual(
            editor.bytecode[
                soylent.QUARANTINE_EAST_DOOR_SLIDE_PC :
                soylent.QUARANTINE_EAST_DOOR_SLIDE_PC + len(expected_slide)
            ],
            expected_slide,
        )
        for script_index in range(32):
            if script_index not in (0, 4):
                self.assertEqual(
                    editor.get_script_pointer(east_leaf.helper_entity, script_index),
                    0x094C,
                )

        gate_pc = editor.get_script_pointer(24, 2)
        self.assertEqual(gate_pc, soylent.QUARANTINE_DOOR_GATE_PC)
        self.assertEqual(
            editor.bytecode[
                gate_pc : gate_pc + len(soylent.QUARANTINE_DOOR_GATE_FINAL_ROUTINE)
            ],
            soylent.QUARANTINE_DOOR_GATE_FINAL_ROUTINE,
        )
        for pc in soylent.QUARANTINE_EAST_DOOR_SUCCESS_SITES:
            self.assertEqual(
                editor.bytecode[
                    pc : pc + len(soylent.QUARANTINE_EAST_DOOR_SUCCESS_REDIRECT)
                ],
                soylent.QUARANTINE_EAST_DOOR_SUCCESS_REDIRECT,
            )
        success = soylent._animated_door_transition_action(
            east,
            soylent.QUARANTINE_EAST_DOOR_ANIMATION,
            soylent.QUARANTINE_EAST_DOOR_SUCCESS_PC,
        )
        self.assertEqual(
            editor.bytecode[
                soylent.QUARANTINE_EAST_DOOR_SUCCESS_PC :
                soylent.QUARANTINE_EAST_DOOR_SUCCESS_PC + len(success)
            ],
            success,
        )
        self.assertEqual(success.count(bytes.fromhex("74 77 80")), 1)
        self.assertIn(bytes.fromhex("09 1A 24"), success)
        self.assertTrue(success.endswith(soylent._change_field(565, 6) + b"\x5B"))

    def test_east_diagnostic_door_uses_its_visible_panel_and_safe_return(self) -> None:
        item = next(
            item for item in self.prepared if item.spec.identity.scene == 621
        )
        door = next(
            door
            for door in soylent.NATIVE_DOOR_CONTROLLERS[621]
            if (door.destination_field, door.destination_parameter) == (550, 0)
        )
        self.assertEqual(
            (
                door.x,
                door.z,
                door.interaction_half_width,
                door.interaction_half_depth,
                door.triangle,
            ),
            (1645, 840, 0x10, 0x18, 86),
        )
        return_entry = next(
            edit for edit in item.spec.entry_edits if edit.parameter == 3
        )
        self.assertEqual(
            (
                return_entry.playable.x,
                return_entry.playable.z,
                return_entry.playable.actor_direction,
                return_entry.triangle,
            ),
            (1730, 840, 2, 81),
        )
        self.assertGreaterEqual(return_entry.playable.x - door.x, 0x10 * 2 + 16)

        animation = next(
            animation
            for animation in soylent.NATIVE_DOOR_ANIMATIONS[621]
            if (
                animation.destination_field,
                animation.destination_parameter,
            )
            == (550, 0)
        )
        self.assertEqual(animation.frames, 32)
        self.assertEqual(len(animation.leaves), 1)
        leaf = animation.leaves[0]
        self.assertEqual(
            (
                leaf.source_header_entity,
                leaf.helper_entity,
                leaf.source_flags,
                leaf.model_index,
                leaf.delta_x,
                leaf.delta_z,
            ),
            (31, 31, 0x0010, 4, 0, 2),
        )

        donor = next(item for item in self.donors if item.identity.scene == 550)
        donor_editor = ScriptEditor(donor.components[soylent.SCRIPT_INDEX])
        reciprocal_pc = donor_editor.get_script_pointer(17, 2)
        reciprocal = donor_editor.bytecode[reciprocal_pc : reciprocal_pc + 18]
        self.assertIn(bytes.fromhex("09 12 24"), reciprocal)
        self.assertIn(soylent._change_field(621, 3), reciprocal)
        return_leaf_pc = donor_editor.get_script_pointer(18, 4)
        self.assertEqual(
            donor_editor.bytecode[return_leaf_pc : return_leaf_pc + 4],
            bytes.fromhex("05 C2 00 00"),
        )
        self.assertEqual(
            donor_editor.bytecode[0x00C2:0x00C5],
            bytes.fromhex("74 77 80"),
        )

    def test_intake_all_seven_visible_panels_are_animated_reciprocal_doors(self) -> None:
        item = next(
            item for item in self.prepared if item.spec.identity.scene == 621
        )
        editor = ScriptEditor(item.components[soylent.SCRIPT_INDEX])
        doors = soylent.NATIVE_DOOR_CONTROLLERS[621]
        self.assertEqual(
            tuple(
                (
                    door.x,
                    door.z,
                    door.interaction_half_width,
                    door.interaction_half_depth,
                    door.destination_field,
                    door.destination_parameter,
                    door.triangle,
                )
                for door in doors
            ),
            (
                (176, 0, 0x0E, 0x2C, 623, 1, 6),
                (867, 1832, 0x2C, 0x10, 620, 0, 65),
                (88, 840, 0x10, 0x18, 549, 0, 18),
                (1645, 840, 0x10, 0x18, 550, 0, 86),
                (866, 1131, 0x16, 0x0E, 565, 0, 45),
                (88, 396, 0x10, 0x18, 565, 2, 14),
                (1645, 396, 0x10, 0x18, 565, 3, 85),
            ),
        )
        entries = {edit.parameter: edit for edit in item.spec.entry_edits}
        self.assertEqual(set(entries), set(range(7)))
        self.assertEqual(
            tuple(
                (
                    entries[parameter].playable.x,
                    entries[parameter].playable.z,
                    entries[parameter].playable.walkmesh,
                    entries[parameter].playable.camera_direction,
                    entries[parameter].playable.actor_direction,
                    entries[parameter].triangle,
                )
                for parameter in range(7)
            ),
            (
                (870, 1781, 0, 4, 4, 63),
                (870, 1190, 0, 4, 0, 88),
                (0, 840, 0, 2, 6, 17),
                (1730, 840, 0, 6, 2, 81),
                (0, 396, 0, 2, 6, 15),
                (1730, 396, 0, 6, 2, 84),
                (112, 0, 0, 2, 6, 2),
            ),
        )

        # Each reciprocal arrival is on the connected circulation side and
        # beyond the controller's doubled ATEL bound plus the 16-unit player
        # radius, so a held return press cannot retrigger a reclosed panel.
        return_parameters = (6, 0, 2, 3, 1, 4, 5)
        normal_axes = ("x", "z", "x", "x", "z", "x", "x")
        for door, parameter, axis in zip(
            doors,
            return_parameters,
            normal_axes,
            strict=True,
        ):
            entry = entries[parameter].playable
            if axis == "x":
                separation = abs(entry.x - door.x)
                bound = door.interaction_half_width
            else:
                separation = abs(entry.z - door.z)
                bound = door.interaction_half_depth
            self.assertGreater(separation, bound * 2 + 16)

        animations = soylent.NATIVE_DOOR_ANIMATIONS[621]
        inventory = {
            (animation.destination_field, animation.destination_parameter): tuple(
                (
                    leaf.source_header_entity,
                    leaf.helper_entity,
                    leaf.source_flags,
                    leaf.model_index,
                    leaf.delta_x,
                    leaf.delta_z,
                )
                for leaf in animation.leaves
            )
            for animation in animations
        }
        self.assertEqual(
            inventory,
            {
                (623, 1): (
                    (36, 27, 0x0010, 10, 0, 2),
                    (37, 28, 0x0010, 11, 0, -2),
                ),
                (620, 0): (
                    (34, 29, 0x0010, 8, -2, 0),
                    (35, 30, 0x0010, 9, 2, 0),
                ),
                (550, 0): ((31, 31, 0x0010, 4, 0, 2),),
                (565, 0): ((30, 32, 0x0010, 3, 2, 0),),
                (565, 2): ((33, 33, 0x0010, 7, 0, -2),),
                (565, 3): ((32, 34, 0x0010, 5, 0, -2),),
            },
        )
        self.assertTrue(all(animation.frames == 32 for animation in animations))
        self.assertEqual(
            soylent.NATIVE_EXISTING_DOOR_HELPERS[621],
            ((549, 0, 2, 0x00F7, 0x0122),),
        )
        self.assertEqual(
            editor.bytecode[0x00F7:0x0122],
            soylent.NATIVE_EXISTING_DOOR_HELPER_BODY,
        )
        animated_destinations = set(inventory)
        existing_destinations = {
            helper[:2] for helper in soylent.NATIVE_EXISTING_DOOR_HELPERS[621]
        }
        self.assertEqual(
            animated_destinations | existing_destinations,
            {
                (door.destination_field, door.destination_parameter)
                for door in doors
            },
        )
        native_helper_action_pc = editor.get_script_pointer(22, 2)
        self.assertEqual(native_helper_action_pc, 0x0D52)
        expected_native_action = soylent._existing_helper_door_transition_action(
            doors[2],
            2,
            native_helper_action_pc,
        )
        self.assertEqual(
            editor.bytecode[
                native_helper_action_pc :
                native_helper_action_pc + len(expected_native_action)
            ],
            expected_native_action,
        )

    def test_generation_west_panel_uses_its_native_finite_helper(self) -> None:
        item = next(
            item for item in self.prepared if item.spec.identity.scene == 622
        )
        door = soylent.NATIVE_DOOR_CONTROLLERS[622][0]
        self.assertEqual(
            (
                door.x,
                door.z,
                door.interaction_half_width,
                door.interaction_half_depth,
                door.destination_field,
                door.destination_parameter,
                door.triangle,
                door.carrier_entity,
            ),
            (-794, -132, 0x10, 0x18, 625, 1, 16, 0),
        )
        self.assertEqual(
            (
                item.spec.edges[0].sample,
                item.spec.edges[0].triangle,
            ),
            ((-794, -132), 16),
        )
        entry = item.spec.entry_edits[0]
        self.assertEqual(
            (entry.playable.x, entry.playable.z, entry.triangle),
            (-700, -136, 15),
        )
        self.assertGreater(entry.playable.x - door.x, 0x10 * 2 + 16)

        editor = ScriptEditor(item.components[soylent.SCRIPT_INDEX])
        init_pc = editor.get_script_pointer(0, 0)
        init = soylent._door_controller_init(door)
        self.assertEqual(editor.bytecode[init_pc : init_pc + len(init)], init)
        self.assertIn(bytes.fromhex("F8 00 10 00"), init)
        self.assertNotIn(bytes.fromhex("20 01 80"), init)

        self.assertEqual(
            soylent.NATIVE_EXISTING_DOOR_HELPERS[622],
            ((625, 1, 7, 0x07A7, 0x07CA),),
        )
        self.assertEqual(editor.get_script_pointer(7, 4), 0x07A7)
        self.assertEqual(
            editor.bytecode[0x07A7:0x07CA],
            soylent.GENERATION_NATIVE_DOOR_HELPER_BODY,
        )
        self.assertEqual(soylent.GENERATION_NATIVE_DOOR_HELPER_BODY[-1], 0)
        record = item.header[0x190 + 7 * 16 : 0x190 + 8 * 16]
        flags, _rx, yaw, _rz, x, y, z, model = struct.unpack(
            "<Hhhh hhh H", record
        )
        self.assertEqual((flags, yaw, x, y, z, model), (0x0290, 0x0C00, 132, 0, -132, 2))

        action_pc = editor.get_script_pointer(0, 2)
        action = soylent._existing_helper_door_transition_action(
            door,
            7,
            action_pc,
        )
        self.assertEqual(editor.bytecode[action_pc : action_pc + len(action)], action)
        self.assertEqual(action.count(bytes.fromhex("74 77 80")), 1)
        self.assertIn(bytes.fromhex("09 07 24"), action)
        self.assertTrue(action.endswith(soylent._change_field(625, 1) + b"\x5B"))

    def test_generation_discovers_the_gated_surface_service_shortcut(self) -> None:
        by_scene = {item.spec.identity.scene: item for item in self.prepared}
        approach = by_scene[623]
        generation = by_scene[622]
        approach_editor = ScriptEditor(
            approach.components[soylent.SCRIPT_INDEX]
        )
        generation_editor = ScriptEditor(
            generation.components[soylent.SCRIPT_INDEX]
        )

        self.assertEqual(soylent.SURFACE_SHORTCUT_STATE_OPERAND, 0x03FA)
        self.assertEqual(soylent.SURFACE_SHORTCUT_DISCOVERED_BIT, 0x0400)
        self.assertEqual(soylent.SURFACE_SHORTCUT_DISCOVERED_BIT_INDEX, 10)
        state_write = (
            b"\x3A"
            + soylent._u16(soylent.SURFACE_SHORTCUT_STATE_OPERAND)
            + soylent._u16(soylent.SURFACE_SHORTCUT_DISCOVERED_BIT_INDEX)
            + b"\x40"
        )
        state_gate = (
            b"\x02"
            + soylent._u16(soylent.SURFACE_SHORTCUT_STATE_OPERAND)
            + soylent._u16(soylent.SURFACE_SHORTCUT_DISCOVERED_BIT)
            + b"\x46"
        )
        self.assertEqual(state_write, bytes.fromhex("3A FA 03 0A 00 40"))
        self.assertEqual(state_gate, bytes.fromhex("02 FA 03 00 04 46"))

        approach_door = soylent.NATIVE_DOOR_CONTROLLERS[623][1]
        generation_door = soylent.NATIVE_DOOR_CONTROLLERS[622][1]
        self.assertEqual(
            (
                approach_door.x,
                approach_door.z,
                approach_door.interaction_half_width,
                approach_door.interaction_half_depth,
                approach_door.destination_field,
                approach_door.destination_parameter,
                approach_door.triangle,
                approach_door.action_kind,
            ),
            (0, -881, 0x21, 0x10, 622, 1, 17, "discovery_gate"),
        )
        self.assertEqual(
            (
                generation_door.x,
                generation_door.z,
                generation_door.interaction_half_width,
                generation_door.interaction_half_depth,
                generation_door.destination_field,
                generation_door.destination_parameter,
                generation_door.triangle,
                generation_door.action_kind,
            ),
            (0, -926, 0x1F, 0x10, 623, 0, 64, "discovery_unlock"),
        )

        approach_source = ScriptEditor(
            parse_field(approach.source_bundle).parts[soylent.SCRIPT_INDEX].data
        )
        generation_source = ScriptEditor(
            parse_field(generation.source_bundle).parts[soylent.SCRIPT_INDEX].data
        )
        self.assertEqual(approach_source.entity_count, 37)
        self.assertEqual(generation_source.entity_count, 26)
        self.assertEqual(approach.spec.poll_pc, 0x093E)
        self.assertEqual(generation.spec.poll_pc, 0x0E1A)
        self.assertEqual(
            approach_editor.get_script_pointer(approach.spec.director_entity, 1),
            0x093E,
        )
        self.assertEqual(
            generation_editor.get_script_pointer(generation.spec.director_entity, 1),
            0x0E1A,
        )
        self.assertEqual(approach_editor.bytecode[0x093E], 0)
        self.assertEqual(generation_editor.bytecode[0x0E1A], 0)
        approach_carrier = 38
        generation_carrier = 26

        approach_animation = soylent.NATIVE_DOOR_ANIMATIONS[623][0]
        generation_animation = soylent.NATIVE_DOOR_ANIMATIONS[622][0]
        self.assertEqual(
            tuple(
                (
                    leaf.source_header_entity,
                    leaf.helper_entity,
                    leaf.source_flags,
                    leaf.model_index,
                    leaf.delta_x,
                    leaf.delta_z,
                )
                for leaf in approach_animation.leaves
            ),
            (
                (49, 39, 0x0010, 10, 2, 0),
                (50, 40, 0x0010, 11, -2, 0),
            ),
        )
        self.assertEqual(
            tuple(
                (
                    leaf.source_header_entity,
                    leaf.helper_entity,
                    leaf.source_flags,
                    leaf.model_index,
                    leaf.delta_x,
                    leaf.delta_z,
                )
                for leaf in generation_animation.leaves
            ),
            ((36, 27, 0x0010, 2, 2, 0),),
        )
        for item, leaves in (
            (approach, approach_animation.leaves),
            (generation, generation_animation.leaves),
        ):
            for leaf in leaves:
                record = item.header[
                    0x190 + leaf.helper_entity * 16 :
                    0x190 + (leaf.helper_entity + 1) * 16
                ]
                self.assertEqual(struct.unpack_from("<H", record)[0], 0x0290)
                self.assertEqual(struct.unpack_from("<H", record, 14)[0], leaf.model_index)

        gate_pc = approach_editor.get_script_pointer(approach_carrier, 2)
        gate_action = soylent._animated_door_transition_action(
            approach_door,
            approach_animation,
            gate_pc,
        )
        self.assertEqual(
            approach_editor.bytecode[gate_pc : gate_pc + len(gate_action)],
            gate_action,
        )
        self.assertTrue(gate_action.startswith(state_gate))
        success_pc = gate_pc + 8
        success = soylent._animated_door_transition_action(
            replace(approach_door, action_kind="transition"),
            approach_animation,
            success_pc,
        )
        denial_pc = struct.unpack_from("<H", gate_action, 6)[0]
        self.assertEqual(denial_pc, success_pc + len(success))
        self.assertEqual(gate_action[8 : 8 + len(success)], success)
        denial = soylent._surface_shortcut_denial_action(
            soylent.SURFACE_SHORTCUT_DENIAL_DIALOGUE_ID,
            denial_pc,
        )
        self.assertTrue(gate_action.endswith(denial))
        self.assertNotIn(state_write, gate_action)
        self.assertTrue(success.endswith(soylent._change_field(622, 1) + b"\x5B"))

        unlock_pc = generation_editor.get_script_pointer(generation_carrier, 2)
        unlock = soylent._animated_door_transition_action(
            generation_door,
            generation_animation,
            unlock_pc,
        )
        self.assertEqual(
            generation_editor.bytecode[unlock_pc : unlock_pc + len(unlock)],
            unlock,
        )
        self.assertEqual(unlock.count(state_write), 1)
        self.assertLess(unlock.index(state_write), unlock.index(bytes.fromhex("74 77 80")))
        self.assertLess(unlock.index(state_write), unlock.index(bytes.fromhex("09 1B 24")))
        self.assertTrue(unlock.endswith(soylent._change_field(623, 0) + b"\x5B"))

        return_entry = next(
            edit for edit in generation.spec.entry_edits if edit.parameter == 1
        )
        self.assertEqual(
            (
                return_entry.playable.x,
                return_entry.playable.z,
                return_entry.playable.camera_direction,
                return_entry.playable.actor_direction,
                return_entry.triangle,
            ),
            (0, -800, 0, 0, 65),
        )
        self.assertGreater(
            return_entry.playable.z - generation_door.z,
            generation_door.interaction_half_depth * 2 + 16,
        )
        approach_entry = next(
            edit for edit in approach.spec.entry_edits if edit.parameter == 0
        )
        self.assertEqual(
            (approach_entry.playable.x, approach_entry.playable.z, approach_entry.triangle),
            (0, -665, 16),
        )
        self.assertGreater(
            approach_entry.playable.z - approach_door.z,
            approach_door.interaction_half_depth * 2 + 16,
        )

        dialogues = parse_dialogue(approach.components[7]).blocks
        self.assertEqual(len(dialogues), 2)
        self.assertEqual(
            dialogues[soylent.SURFACE_SHORTCUT_DENIAL_DIALOGUE_ID].text,
            soylent.SURFACE_SHORTCUT_DENIAL_DIALOGUE,
        )
        self.assertEqual(
            (len(approach.components[7]), hashlib.sha256(approach.components[7]).hexdigest()),
            soylent.SURFACE_SHORTCUT_DIALOGUE_IDENTITIES[623],
        )

    def test_every_visible_native_npc_has_one_valid_unique_dialogue(self) -> None:
        expected_entities = {
            621: set(range(6, 13)) | {14, 15},
            620: set(range(5, 17)),
            622: set(range(8, 25)),
        }
        first_dialogue_ids = {621: 2, 620: 12, 622: 22}
        by_scene = {item.spec.identity.scene: item for item in self.prepared}
        for scene, expected in expected_entities.items():
            item = by_scene[scene]
            editor = ScriptEditor(item.components[soylent.SCRIPT_INDEX])
            dialogues = parse_dialogue(item.components[7]).blocks
            npc_dialogues = soylent.NATIVE_NPC_DIALOGUES[scene]
            self.assertEqual({entity for entity, _text in npc_dialogues}, expected)

            dialogue_ids: list[int] = []
            for index, (entity, text) in enumerate(npc_dialogues):
                dialogue_id = first_dialogue_ids[scene] + index
                action_pc = editor.get_script_pointer(entity, 2)
                self.assertLess(action_pc + 6, editor.bytecode_size + 1)
                self.assertEqual(
                    editor.bytecode[action_pc : action_pc + 6],
                    soylent._actor_dialogue_action(dialogue_id),
                )
                self.assertLess(dialogue_id, len(dialogues))
                self.assertEqual(dialogues[dialogue_id].text, text)
                self.assertEqual(
                    dialogues[dialogue_id].width,
                    soylent._native_npc_dialogue_width(scene),
                )
                self.assertEqual(dialogues[dialogue_id].height, 4)
                dialogue_ids.append(dialogue_id)

            self.assertEqual(len(dialogue_ids), len(set(dialogue_ids)))
            self.assertEqual(
                dialogue_ids,
                list(
                    range(
                        first_dialogue_ids[scene],
                        first_dialogue_ids[scene] + len(expected),
                    )
                ),
            )

            if scene == 622:
                source_editor = ScriptEditor(
                    parse_field(item.source_bundle).parts[soylent.SCRIPT_INDEX].data
                )
                self.assertEqual(
                    len(soylent.GENERATION_NPC_ENABLE_PCS),
                    len(npc_dialogues),
                )
                for (entity, _text), enable_pc in zip(
                    npc_dialogues,
                    soylent.GENERATION_NPC_ENABLE_PCS,
                    strict=True,
                ):
                    self.assertEqual(source_editor.bytecode[enable_pc], 0x2A)
                    self.assertEqual(editor.bytecode[enable_pc], 0x33)
                    self.assertLessEqual(
                        editor.get_script_pointer(entity, 0), enable_pc
                    )
                    self.assertLess(enable_pc, editor.get_script_pointer(entity, 1))

    def test_native_rooms_change_only_script_and_authored_dialogue(self) -> None:
        dialogue_scenes = (
            set(soylent.NATIVE_NPC_DIALOGUES)
            | set(soylent.SURFACE_SHORTCUT_DIALOGUE_IDENTITIES)
        )
        for item in self.prepared:
            scene = item.spec.identity.scene
            source = parse_field(item.source_bundle)
            final = parse_field(item.bundle)
            expected_changed = {soylent.SCRIPT_INDEX}
            if scene in dialogue_scenes:
                expected_changed.add(7)
            actual_changed = {
                index
                for index, (before, after) in enumerate(
                    zip(source.parts, final.parts, strict=True)
                )
                if before.data != after.data
            }
            self.assertEqual(actual_changed, expected_changed)
            self.assertEqual(len(item.graphics), item.spec.identity.graphics_size)
            self.assertEqual(
                hashlib.sha256(item.graphics).hexdigest(),
                item.spec.identity.graphics_sha256,
            )
            soylent.validate_walkmesh_contract(item.spec, item.components[1])

    def test_donor_rooms_preserve_native_scanner_and_five_tone_controllers(self) -> None:
        by_scene = {item.identity.scene: item for item in self.donors}
        scanner = ScriptEditor(by_scene[550].components[soylent.SCRIPT_INDEX])
        self.assertEqual(scanner.get_script_pointer(4, 2), 0x0237)

        lock = ScriptEditor(by_scene[565].components[soylent.SCRIPT_INDEX])
        self.assertEqual(lock.get_script_pointer(12, 2), 0x03AC)
        self.assertEqual(
            by_scene[565].entry_triangles,
            ((0, 75), (1, 8), (2, 12), (3, 17), (4, 57), (6, 68)),
        )
        self.assertEqual(
            tuple(
                struct.unpack_from("<hhBBB", lock.bytecode, 1 + parameter * 7)
                for parameter in range(7)
            ),
            (
                (-24, 24, 0, 7, 3),
                (4864, -3626, 0, 5, 5),
                (4240, -3000, 0, 1, 5),
                (3615, -2385, 0, 1, 5),
                (1097, -4523, 0, 1, 1),
                (3020, -4477, 0, 0xFF, 0xFF),
                (3330, -5773, 0, 7, 7),
            ),
        )
        active_doors = {
            8: (0x030B, 0x0316, 589, 0),
            10: (0x035D, 0x0368, 620, 1),
        }
        for entity, (action_pc, transition_pc, field, parameter) in (
            active_doors.items()
        ):
            self.assertEqual(lock.get_script_pointer(entity, 2), action_pc)
            init_pc = lock.get_script_pointer(entity, 0)
            init = lock.bytecode[init_pc : init_pc + 21]
            self.assertIn(bytes.fromhex("F8 00 00 20"), init)
            self.assertIn(bytes.fromhex("F8 03 04 00"), init)
            self.assertEqual(
                lock.bytecode[transition_pc : transition_pc + 5],
                soylent._change_field(field, parameter),
            )

        self.assertEqual(
            soylent.FIELD565_RECIPROCAL_DOORS,
            ((4, 19, 4, 1), (6, 17, 6, 4), (7, 18, 7, 5)),
        )
        reciprocal_pcs = {4: 0x05F5, 6: 0x0612, 7: 0x062F}
        for entity, helper, player_script, parameter in (
            soylent.FIELD565_RECIPROCAL_DOORS
        ):
            action_pc = lock.get_script_pointer(entity, 2)
            self.assertEqual(action_pc, reciprocal_pcs[entity])
            expected = soylent._field565_reciprocal_action(
                helper,
                player_script,
                parameter,
                action_pc,
            )
            self.assertEqual(
                lock.bytecode[action_pc : action_pc + len(expected)],
                expected,
            )
            helper_pc = lock.get_script_pointer(helper, 4)
            self.assertEqual(
                lock.bytecode[helper_pc : helper_pc + 4],
                bytes.fromhex("05 EC 00 00"),
            )
        self.assertEqual(lock.bytecode[0x00EC:0x00EF], bytes.fromhex("74 77 80"))
        live_pointers = {
            lock.get_script_pointer(entity, script_index)
            for entity in range(lock.entity_count)
            for script_index in range(32)
        }
        self.assertTrue(
            {0x0267, 0x02B9, 0x02E2, 0x0334}.isdisjoint(live_pointers)
        )

        self.assertEqual(
            lock.bytecode[
                soylent.SEALED_ROUTE_RESPONSE_PC :
                soylent.SEALED_ROUTE_RESPONSE_PC
                + len(soylent.SEALED_ROUTE_RESPONSE)
            ],
            soylent.SEALED_ROUTE_RESPONSE,
        )
        self.assertEqual(soylent.SEALED_ROUTE_ENTITIES, (9,))
        self.assertEqual(
            {
                lock.get_script_pointer(entity, 2)
                for entity in soylent.SEALED_ROUTE_ENTITIES
            },
            {soylent.SEALED_ROUTE_RESPONSE_PC},
        )
        for entity, native_start, native_stop in (
            soylent.FIELD565_IMMOVABLE_CONTROLLER_INITS
        ):
            init_pc = lock.get_script_pointer(entity, 0)
            expected_init = (
                lock.bytecode[native_start:native_stop]
                + bytes.fromhex("F8 00 10 00 00")
            )
            init = lock.bytecode[init_pc : init_pc + len(expected_init)]
            self.assertEqual(init, expected_init)
            self.assertIn(bytes.fromhex("F8 00 00 20"), init)
            self.assertIn(bytes.fromhex("F8 00 10 00"), init)
            self.assertNotEqual(init[0], 0x2A)
        self.assertEqual(
            tuple(
                entity
                for entity, _native_start, _native_stop in (
                    soylent.FIELD565_IMMOVABLE_CONTROLLER_INITS
                )
            ),
            tuple(range(4, 13)),
        )

        # The first internal gate keeps its complete native blocking animation,
        # then ghosts only its now-immovable controller before restoring input.
        internal_gate_pc = lock.get_script_pointer(11, 2)
        self.assertEqual(
            internal_gate_pc,
            soylent.FIELD565_INTERNAL_GATE_ACTION_PC,
        )
        internal_gate = soylent._field565_internal_gate_action()
        self.assertEqual(
            lock.bytecode[
                internal_gate_pc : internal_gate_pc + len(internal_gate)
            ],
            internal_gate,
        )
        self.assertEqual(
            internal_gate[:13],
            bytes.fromhex(
                "FE 54 36 00 04 09 14 24 80 98 00 00 80"
            ),
        )
        self.assertEqual(internal_gate[13:16], bytes.fromhex("20 01 80"))
        self.assertTrue(internal_gate.endswith(bytes.fromhex("2A FE 53 00")))

        # The five-tone controller stays on its native action.  Only its two
        # success exits detour through a ghost opcode and immediately rejoin;
        # failed tone sequences remain byte-for-byte retail.
        self.assertEqual(
            lock.get_script_pointer(12, 2),
            soylent.FIELD565_TONE_GATE_ACTION_PC,
        )
        for helper_pc in (0x03B6, 0x0447):
            self.assertEqual(
                lock.bytecode[helper_pc : helper_pc + 8],
                bytes.fromhex("09 15 24 80 99 00 00 80"),
            )
        tone_exits = (
            (
                soylent.FIELD565_TONE_GATE_REOPEN_EXIT_PC,
                soylent.FIELD565_TONE_GATE_REOPEN_GHOST_PC,
                0x053C,
            ),
            (
                soylent.FIELD565_TONE_GATE_SUCCESS_EXIT_PC,
                soylent.FIELD565_TONE_GATE_SUCCESS_GHOST_PC,
                0x051D,
            ),
        )
        for exit_pc, ghost_pc, return_pc in tone_exits:
            self.assertEqual(
                lock.bytecode[exit_pc : exit_pc + 3],
                b"\x01" + soylent._u16(ghost_pc),
            )
            trampoline = soylent._field565_gate_ghost_trampoline(return_pc)
            self.assertEqual(
                lock.bytecode[ghost_pc : ghost_pc + len(trampoline)],
                trampoline,
            )
            self.assertEqual(trampoline[:3], bytes.fromhex("20 01 80"))
            self.assertEqual(trampoline[3:], b"\x01" + soylent._u16(return_pc))

        sources = soylent.load_donor_fields(self.donor_disc)
        native_lock = ScriptEditor(
            parse_field(sources[565][0]).parts[soylent.SCRIPT_INDEX].data
        )
        patched_target_bytes = {0x03C2, 0x03C3, 0x0466, 0x0467}
        for pc in range(soylent.FIELD565_TONE_GATE_ACTION_PC, 0x053D):
            if pc not in patched_target_bytes:
                self.assertEqual(
                    lock.bytecode[pc],
                    native_lock.bytecode[pc],
                    f"native five-tone byte changed at PC 0x{pc:04X}",
                )

        gate_pc = lock.get_script_pointer(
            soylent.FIELD565_QUARANTINE_EXIT_ENTITY,
            2,
        )
        self.assertEqual(gate_pc, soylent.FIELD565_QUARANTINE_EXIT_GATE_PC)
        gate = soylent._field565_quarantine_exit_action(gate_pc)
        self.assertEqual(lock.bytecode[gate_pc : gate_pc + len(gate)], gate)
        self.assertEqual(
            gate[:8],
            b"\x02"
            + soylent._u16(soylent.QUARANTINE_STATE_OPERAND)
            + soylent._u16(soylent.QUARANTINE_COMPLETE_BIT)
            + b"\x46"
            + soylent._u16(soylent.FIELD565_QUARANTINE_DENIAL_PC),
        )
        denial = soylent._field565_repeatable_dialogue_action(
            11,
            soylent.FIELD565_QUARANTINE_DENIAL_PC,
        )
        self.assertEqual(
            lock.bytecode[
                soylent.FIELD565_QUARANTINE_DENIAL_PC :
                soylent.FIELD565_QUARANTINE_DENIAL_PC + len(denial)
            ],
            denial,
        )
        self.assertIn(bytes.fromhex("09 10 24 07 01 25"), gate)
        self.assertTrue(gate.endswith(soylent._change_field(624, 0) + b"\x5B"))

        sealed_dialogues = parse_dialogue(by_scene[565].components[7]).blocks
        self.assertEqual(len(sealed_dialogues), 12)
        self.assertEqual(
            sealed_dialogues[10].text,
            "AUXILIARY ROUTE SEALED\n"
            "No authorization signal is present.<Close>",
        )
        self.assertEqual(
            sealed_dialogues[11].text,
            "QUARANTINE CONSENSUS REQUIRED\n"
            "Outbound sorting is still locked.<Close>",
        )
        self.assertEqual(
            by_scene[565].header,
            parse_field(by_scene[565].bundle).header,
        )
        self.assertEqual(
            (
                len(by_scene[565].header),
                hashlib.sha256(by_scene[565].header).hexdigest(),
            ),
            soylent.INTERACTIVE_DONOR_HEADER_IDENTITIES[565],
        )

        clue = ScriptEditor(by_scene[589].components[soylent.SCRIPT_INDEX])
        self.assertEqual(clue.bytecode[0x00EC : 0x00F1], soylent._change_field(565, 4))
        for scene, item in by_scene.items():
            source = parse_field(sources[scene][0])
            final = parse_field(item.bundle)
            self.assertEqual(item.graphics, sources[scene][1])
            expected_changed = {soylent.SCRIPT_INDEX}
            if scene == 565:
                expected_changed.add(7)
            actual_changed = {
                index
                for index, (before, after) in enumerate(
                    zip(source.parts, final.parts, strict=True)
                )
                if before.data != after.data
            }
            self.assertEqual(actual_changed, expected_changed)

    def test_annex_return_doors_are_immovable_and_keep_native_motion(self) -> None:
        contracts = {
            # scene: controller, native init start/STOP, appended init PC,
            # action PC, leaf helper/script-four PC/body, transition, target,
            # audited return-entry triangles
            549: (
                6, 0x019E, 0x01B3, 0x0784, 0x01B4,
                7, 0x01CC, bytes.fromhex("05 EE 06 00"),
                0x01BF, 621, 2, ((0, 6),),
            ),
            550: (
                17, 0x0628, 0x063D, 0x0A18, 0x063E,
                18, 0x0656, bytes.fromhex("05 C2 00 00"),
                0x0649, 621, 3, ((0, 14),),
            ),
            589: (
                4, 0x00CB, 0x00E0, 0x09FC, 0x00E1,
                5, 0x00F9, bytes.fromhex("05 67 09 00"),
                0x00EC, 565, 4, ((0, 57),),
            ),
        }
        self.assertEqual(
            soylent.DONOR_ROUTE_IMMOVABLE_CONTROLLER_INITS,
            {
                scene: ((values[0], values[1], values[2]),)
                for scene, values in contracts.items()
            },
        )
        self.assertEqual(set(soylent.DONOR_ROUTE_NATIVE_MOTION), set(contracts))

        sources = soylent.load_donor_fields(self.donor_disc)
        final_by_scene = {item.identity.scene: item for item in self.donors}
        for scene, values in contracts.items():
            (
                controller,
                native_start,
                native_stop,
                appended_pc,
                action_pc,
                helper,
                helper_pc,
                helper_body,
                transition_pc,
                destination_field,
                destination_parameter,
                entry_triangles,
            ) = values
            with self.subTest(scene=scene):
                baseline = soylent.prepare_donor_field(
                    soylent.DONOR_BY_SCENE[scene],
                    *sources[scene],
                )
                native = ScriptEditor(
                    baseline.components[soylent.SCRIPT_INDEX]
                )
                final_item = final_by_scene[scene]
                final = ScriptEditor(
                    final_item.components[soylent.SCRIPT_INDEX]
                )

                self.assertEqual(final.bytecode[: native.bytecode_size], native.bytecode)
                expected_init = (
                    native.bytecode[native_start:native_stop]
                    + bytes.fromhex("F8 00 10 00 00")
                )
                self.assertEqual(final.get_script_pointer(controller, 0), appended_pc)
                self.assertEqual(
                    final.bytecode[appended_pc : appended_pc + len(expected_init)],
                    expected_init,
                )
                self.assertEqual(
                    final.bytecode_size,
                    native.bytecode_size + len(expected_init),
                )
                self.assertNotIn(
                    bytes.fromhex("F8 00 10 00"),
                    native.bytecode[native_start:native_stop],
                )

                for entity in range(native.entity_count):
                    for script_index in range(32):
                        expected_pointer = native.get_script_pointer(
                            entity, script_index
                        )
                        if entity == controller and script_index == 0:
                            expected_pointer = appended_pc
                        self.assertEqual(
                            final.get_script_pointer(entity, script_index),
                            expected_pointer,
                        )

                expected_action = (
                    bytes.fromhex("FE 54")
                    + bytes((0x09, helper, 0x24))
                    + bytes.fromhex("07 01 24 26 0A 80")
                    + soylent._change_field(
                        destination_field, destination_parameter
                    )
                    + b"\x5B"
                )
                self.assertEqual(final.get_script_pointer(controller, 2), action_pc)
                self.assertEqual(
                    final.bytecode[action_pc : action_pc + len(expected_action)],
                    expected_action,
                )
                self.assertEqual(final.get_script_pointer(helper, 4), helper_pc)
                self.assertEqual(
                    final.bytecode[helper_pc : helper_pc + len(helper_body)],
                    helper_body,
                )
                self.assertEqual(
                    final.bytecode[transition_pc : transition_pc + 5],
                    soylent._change_field(
                        destination_field, destination_parameter
                    ),
                )
                self.assertEqual(final_item.entry_triangles, entry_triangles)
                self.assertEqual(final_item.header, parse_field(final_item.bundle).header)
                self.assertEqual(
                    (
                        len(final_item.header),
                        hashlib.sha256(final_item.header).hexdigest(),
                    ),
                    soylent.INTERACTIVE_DONOR_HEADER_IDENTITIES[scene],
                )
                for index, (before, after) in enumerate(
                    zip(baseline.components, final_item.components, strict=True)
                ):
                    if index != soylent.SCRIPT_INDEX:
                        self.assertEqual(after, before)

    def test_complete_title_bootstrap_resets_only_surface_puzzle_bits(self) -> None:
        resources = {
            item.canonical_id: item.data
            for item in soylent.prepare_title_integration(
                self.source_disc,
                complete_dungeon=True,
            )
        }
        title = resources[1586]
        self.assertEqual(
            (len(title), hashlib.sha256(title).hexdigest()),
            (
                soylent.COMPLETE_TITLE_FIELD_BUNDLE_SIZE,
                soylent.COMPLETE_TITLE_FIELD_BUNDLE_SHA256,
            ),
        )
        script = parse_field(title).parts[soylent.SCRIPT_INDEX].data
        editor = ScriptEditor(script)
        self.assertEqual(
            (len(script), hashlib.sha256(script).hexdigest()),
            (
                soylent.COMPLETE_TITLE_FIELD_SCRIPT_SIZE,
                soylent.COMPLETE_TITLE_FIELD_SCRIPT_SHA256,
            ),
        )
        self.assertEqual(editor.bytecode[0x00BE : 0x00C0], bytes.fromhex("76 01"))
        self.assertEqual(
            editor.bytecode[
                soylent.SURFACE_STATE_RESET_PC :
                soylent.SURFACE_STATE_RESET_PC + len(soylent.SURFACE_STATE_RESET_ROUTINE)
            ],
            soylent.SURFACE_STATE_RESET_ROUTINE,
        )
        shortcut_clear = (
            b"\x3B"
            + soylent._u16(soylent.SURFACE_SHORTCUT_STATE_OPERAND)
            + soylent._u16(soylent.SURFACE_SHORTCUT_DISCOVERED_BIT_INDEX)
            + b"\x40"
        )
        self.assertEqual(shortcut_clear, bytes.fromhex("3B FA 03 0A 00 40"))
        self.assertEqual(soylent.SURFACE_STATE_RESET_ROUTINE.count(shortcut_clear), 1)
        self.assertNotIn(bytes.fromhex("3B FA 03 0B 00 40"), soylent.SURFACE_STATE_RESET_ROUTINE)
        self.assertEqual(
            editor.bytecode[
                soylent.SURFACE_STATE_RESET_PC
                + len(soylent.SURFACE_STATE_RESET_ROUTINE)
                - 5 :
                soylent.SURFACE_STATE_RESET_PC
                + len(soylent.SURFACE_STATE_RESET_ROUTINE)
            ],
            soylent._change_field(
                soylent.SURFACE_ENTRY_FIELD,
                soylent.SURFACE_ENTRY_PARAMETER,
            ),
        )
        self.assertEqual(
            editor.bytecode[0x0171 : 0x0176],
            soylent._change_field(soylent.MASS_DRIVER_ENTRY_FIELD, 0),
        )

    def test_complete_stage_materializes_unique_bundle_graphics_and_title_ids(self) -> None:
        title = soylent.prepare_title_integration(
            self.source_disc,
            complete_dungeon=True,
        )
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "complete"
            replacements = soylent.materialize(
                self.prepared,
                output,
                self.source_disc,
                donor_fields=self.donors,
                donor_disc=self.donor_disc,
                title_resources=title,
                complete_dungeon=True,
            )
            canonical_ids = [canonical_id for canonical_id, _path in replacements]
            self.assertEqual(len(canonical_ids), len(set(canonical_ids)))
            self.assertEqual(len(canonical_ids), 19)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                manifest["playable_route"],
                [623, 621, 620, 565, 624, 626, 625, 622],
            )
            self.assertEqual(manifest["optional_wings"], [549, 550, 589])
            self.assertEqual(
                manifest["discovered_shortcuts"],
                [
                    {
                        "name": "Generation emergency service latch",
                        "discovery_side": [622, 623, 0],
                        "gated_reverse_side": [623, 622, 1],
                        "persistent_operand": soylent.SURFACE_SHORTCUT_STATE_OPERAND,
                        "persistent_bit_mask": soylent.SURFACE_SHORTCUT_DISCOVERED_BIT,
                        "persistent_bit_index": soylent.SURFACE_SHORTCUT_DISCOVERED_BIT_INDEX,
                        "cold_surface_entry_denied": True,
                        "input": "Cross",
                        "authentic_panel_animation": True,
                    }
                ],
            )
            self.assertEqual(manifest["future_native_wings"], [])
            self.assertEqual(len(manifest["donor_jobs"]), 4)
            self.assertEqual(len(manifest["puzzles"]), 3)
            self.assertEqual(
                manifest["preservation"]["changed_streams"],
                ["scripts", "dialogue"],
            )
            self.assertNotIn(
                "scripts", manifest["preservation"]["unchanged_streams"]
            )
            self.assertNotIn(
                "dialogue", manifest["preservation"]["unchanged_streams"]
            )

            jobs = {job["scene"]: job for job in manifest["jobs"]}
            self.assertEqual(set(jobs), set(soylent.NATIVE_DOOR_CONTROLLERS))
            for scene, job in jobs.items():
                self.assertEqual(
                    job["changed_streams"],
                    [soylent.SCRIPT_INDEX, 7]
                    if (
                        scene in soylent.NATIVE_NPC_DIALOGUES
                        or scene in soylent.SURFACE_SHORTCUT_DIALOGUE_IDENTITIES
                    )
                    else [soylent.SCRIPT_INDEX],
                )
                self.assertEqual(
                    job["header_actor_records_added"],
                    len(
                        tuple(
                            door
                            for door in soylent.NATIVE_DOOR_CONTROLLERS[scene]
                            if door.carrier_entity is None
                        )
                    ),
                )
                self.assertEqual(
                    [
                        (
                            tuple(interaction["position"]),
                            interaction["interaction_half_width"],
                            interaction["interaction_half_depth"],
                            tuple(interaction["destination"]),
                            interaction["triangle"],
                            interaction["input"],
                        )
                        for interaction in job["door_interactions"]
                    ],
                    [
                        (
                            (door.x, door.z),
                            door.interaction_half_width,
                            door.interaction_half_depth,
                            (
                                door.destination_field,
                                door.destination_parameter,
                            ),
                            door.triangle,
                            "Cross",
                        )
                        for door in soylent.NATIVE_DOOR_CONTROLLERS[scene]
                    ],
                )

            donor_jobs = {
                job["scene"]: job for job in manifest["donor_jobs"]
            }
            donors_by_scene = {item.identity.scene: item for item in self.donors}
            self.assertEqual(set(donor_jobs), {549, 550, 565, 589})
            for scene, job in donor_jobs.items():
                self.assertEqual(
                    job["changed_streams"],
                    [soylent.SCRIPT_INDEX, 7]
                    if scene == 565
                    else [soylent.SCRIPT_INDEX],
                )
                donor = donors_by_scene[scene]
                self.assertEqual(
                    (
                        output
                        / "clones"
                        / f"field_{scene}_disc1_donor"
                        / "header.bin"
                    ).read_bytes(),
                    donor.header,
                )
                self.assertEqual(donor.header, parse_field(donor.bundle).header)
            self.assertEqual(
                donor_jobs[565]["entry_triangles"],
                [[0, 75], [1, 8], [2, 12], [3, 17], [4, 57], [6, 68]],
            )


if __name__ == "__main__":
    unittest.main()
