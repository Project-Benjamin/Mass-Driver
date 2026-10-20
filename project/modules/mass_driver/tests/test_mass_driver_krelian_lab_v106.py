from __future__ import annotations

from shared.paths import PROJECT_ROOT as REPOSITORY_ROOT

import hashlib
import json
import math
import struct
import unittest
from pathlib import Path
from types import SimpleNamespace

import tools.build_mass_driver_dungeon as dungeon
from tools.xgatel import AtelScript as ParsedAtelScript
from tools.xgatel import scan_raw_transitions
from tools.xgdialog import parse_dialogue
from tools.xgfield import parse_field
from tools.xgscript import AtelScript


PROJECT = REPOSITORY_ROOT
SOURCE_BUNDLE_SHA256 = (
    "a16f54a1eca717603d36e2886a6aa24142d4af81c1e849deb8fe83bdb5fc4135"
)
SOURCE_GRAPHICS_SHA256 = (
    "c253c815b126a9527851057d9279b9646fed0ea982fde359d389020178f9d9d6"
)
SOURCE_HEADER_SHA256 = (
    "e49f9573e08e6b8d475bf9185dd79e843fad1ba75ef1f9c5e5fa60440846ed9d"
)
SOURCE_COMPONENT_SHA256S = (
    "df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119",
    "a262f53fc609909d4ffb34fa3c898c7938ddca49e8170bb9d7e10bf89946a0ee",
    "223a7d84cc89b29feb74f3393ef257908a964854c38cd6fbccda173b8f80915d",
    "d886f360c112ac59247f3439c6dc2a800840cd153bbeed2e296b1f2db39da004",
    "0762607a4654cf1c8c373d21be79a48656cd203001891ee988a65568311464e0",
    "383569c16e8b062011037191331b4cabb578526a257933bc025fbcd3fa6fcd5d",
    "a7dacd9fc86d36309e2d4d1a805321404457d5430cf4107bca2c62081b68a6f8",
    "37a4b87f4393f9ce6ffc87b8a63cc0d300dcfb907096d46938d810e407406eb1",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
)
CURRENT_BUNDLE_SHA256 = (
    "5a292fd2df08bff7af3bcb3c243748bb9f92a18ad2e469a4931d64b1b4364c97"
)
CURRENT_SCRIPT_SHA256 = (
    "7e089ce88febe68ffa51709476a9e2eb4f0ab9cbb36baf9e21b6227b569dd51a"
)
CURRENT_DIALOGUE_SHA256 = (
    "0ffe294fd9f9904c85679e476ec9af4aee264798df31671a8fbe7cf7990130e2"
)
DUMMY_SHA256 = (
    "aafefb97ceb8e4667c719b99c4250b286e03087315b61848d196300140a95a2c"
)
DUMMY_BYTES = b"It's CDMAKE Dummy !\r\n\r\n "


def _clone(target_field: int):
    return next(
        spec for spec in dungeon.CLONES if spec.target_field == target_field
    )


def _source_and_transformed(target_field: int) -> tuple[AtelScript, AtelScript]:
    if target_field == 507:
        source = (
            PROJECT
            / "work"
            / "reference_fields"
            / "cd1_krelian_computer_room_573"
            / "05_scripts.bin"
        ).read_bytes()
        transformed = (
            PROJECT
            / "work"
            / "mass_driver_v147_stage"
            / "clones"
            / "field_507"
            / "05_scripts.bin"
        ).read_bytes()
        return AtelScript(source), AtelScript(transformed)
    spec = _clone(target_field)
    source = (
        PROJECT / "work" / spec.bundle_directory / "05_scripts.bin"
    ).read_bytes()
    transformed, _notes = dungeon._transform_clone_script(spec, source)
    return AtelScript(source), AtelScript(transformed)


def _prepared_507():
    """Load the frozen V147 field-507 replacement as historical evidence."""

    stage = PROJECT / "work" / "mass_driver_v147_stage"
    clone = stage / "clones" / "field_507"
    bundle = (stage / "replacements" / "1620_field_507.bin").read_bytes()
    graphics = (
        stage / "replacements" / "1621_field_507_graphics.bin"
    ).read_bytes()
    components = tuple(
        (clone / f"{index:02d}_{name}.bin").read_bytes()
        for index, name in enumerate(
            (
                "images",
                "walkmesh",
                "models",
                "actors",
                "sprites",
                "scripts",
                "encounters",
                "dialogue",
                "triggers",
            )
        )
    )
    prepared = SimpleNamespace(
        bundle=bundle,
        graphics=graphics,
        header=(clone / "header.bin").read_bytes(),
        components=components,
    )
    return None, prepared, parse_field(bundle)


class KrelianFinalLabTests(unittest.TestCase):
    def test_frozen_v147_field_507_cloned_the_exact_field_573_pair(self) -> None:
        self.assertNotIn(507, dungeon.ROUTE)
        self.assertFalse(
            any(spec.target_field == 507 for spec in dungeon.CLONES)
        )
        frozen_manifest = json.loads(
            (
                PROJECT
                / "work"
                / "mass_driver_v147_stage"
                / "manifest.json"
            ).read_text(encoding="utf-8")
        )
        frozen_job = next(
            job
            for job in frozen_manifest["jobs"]
            if job.get("target_field") == 507
        )
        self.assertEqual(
            (
                frozen_job["label"],
                frozen_job["target_field"],
                tuple(
                    replacement["canonical_id"]
                    for replacement in frozen_job["replacements"]
                ),
            ),
            (
                "Compact Krelian computer room and final launch console: retail 573 -> standalone 507",
                507,
                (1620, 1621),
            ),
        )

        donor_root = (
            PROJECT
            / "work"
            / "reference_fields"
            / "cd1_krelian_computer_room_573"
        )
        donor_bundle = (donor_root / "1752.bin").read_bytes()
        donor_graphics = (donor_root / "1753.bin").read_bytes()
        donor_header = (donor_root / "header.bin").read_bytes()
        donor = parse_field(donor_bundle)
        self.assertEqual(
            (
                len(donor_bundle),
                hashlib.sha256(donor_bundle).hexdigest(),
                len(donor_graphics),
                hashlib.sha256(donor_graphics).hexdigest(),
                len(donor_header),
                hashlib.sha256(donor_header).hexdigest(),
            ),
            (
                35_052,
                SOURCE_BUNDLE_SHA256,
                141_312,
                SOURCE_GRAPHICS_SHA256,
                672,
                SOURCE_HEADER_SHA256,
            ),
        )
        self.assertEqual(donor.header, donor_header)
        self.assertEqual(
            tuple(
                (len(part.data), hashlib.sha256(part.data).hexdigest())
                for part in donor.parts
            ),
            tuple(
                zip(
                    (4, 2_328, 34_944, 6_724, 11_684, 1_888, 528, 51, 0),
                    SOURCE_COMPONENT_SHA256S,
                    strict=True,
                )
            ),
        )
        self.assertEqual(
            dungeon.KRELIAN_COMPUTER_ROOM_COMPONENT_SHA256S,
            SOURCE_COMPONENT_SHA256S,
        )

        # Canonicals 1620/1621 are the verified Disc 2 dummy pair being
        # replaced. The physical donor comes wholly from Disc 1 field 573.
        dummy_root = (
            PROJECT
            / "work"
            / "_audit_krelian_ouroboros"
            / "cd2_field507_dummy"
        )
        for canonical_id in (1620, 1621):
            with self.subTest(cd2_dummy_canonical_id=canonical_id):
                data = (dummy_root / f"{canonical_id}.bin").read_bytes()
                self.assertEqual(data, DUMMY_BYTES)
                self.assertEqual(hashlib.sha256(data).hexdigest(), DUMMY_SHA256)

    def test_prepared_field_507_preserves_every_physical_room_component(
        self,
    ) -> None:
        spec, prepared, packed = _prepared_507()
        self.assertEqual(
            (
                len(prepared.bundle),
                hashlib.sha256(prepared.bundle).hexdigest(),
                dungeon.KRELIAN_COMPUTER_ROOM_BUNDLE_SIZE,
                dungeon.KRELIAN_COMPUTER_ROOM_BUNDLE_SHA256,
            ),
            (68_540, CURRENT_BUNDLE_SHA256, 68_540, CURRENT_BUNDLE_SHA256),
        )
        self.assertIsNotNone(prepared.graphics)
        assert prepared.graphics is not None
        self.assertEqual(
            (
                len(prepared.graphics),
                hashlib.sha256(prepared.graphics).hexdigest(),
            ),
            (141_312, SOURCE_GRAPHICS_SHA256),
        )
        self.assertIsNotNone(prepared.header)
        assert prepared.header is not None
        self.assertEqual(
            (len(prepared.header), hashlib.sha256(prepared.header).hexdigest()),
            (672, SOURCE_HEADER_SHA256),
        )

        expected_components = (
            (4, SOURCE_COMPONENT_SHA256S[0]),
            (2_328, SOURCE_COMPONENT_SHA256S[1]),
            (34_944, SOURCE_COMPONENT_SHA256S[2]),
            (6_724, SOURCE_COMPONENT_SHA256S[3]),
            (11_684, SOURCE_COMPONENT_SHA256S[4]),
            (2_405, CURRENT_SCRIPT_SHA256),
            (528, SOURCE_COMPONENT_SHA256S[6]),
            (1_643, CURRENT_DIALOGUE_SHA256),
            (0, SOURCE_COMPONENT_SHA256S[8]),
        )
        self.assertEqual(
            tuple(
                (len(component), hashlib.sha256(component).hexdigest())
                for component in prepared.components
            ),
            expected_components,
        )
        self.assertEqual(
            tuple(part.data for part in packed.parts),
            prepared.components,
        )
        self.assertEqual(
            (len(packed.header), hashlib.sha256(packed.header).hexdigest()),
            (
                672,
                "84f3ac2103a741855ce4f6dbc0c35e5c09935e84f0dd32f5196bdb0c9a1b8ec5",
            ),
        )
        # Packing updates only the field stream size/offset tables. The room
        # header itself, including every model node, is the retail donor.
        self.assertEqual(packed.header[:0x10C], prepared.header[:0x10C])
        self.assertEqual(packed.header[0x154:], prepared.header[0x154:])

        script = AtelScript(prepared.components[dungeon.SCRIPT_INDEX])
        self.assertEqual((script.entity_count, script.bytecode_size), (11, 1_569))
        self.assertEqual(
            (
                len(prepared.components[dungeon.SCRIPT_INDEX]),
                hashlib.sha256(
                    prepared.components[dungeon.SCRIPT_INDEX]
                ).hexdigest(),
            ),
            (2_405, CURRENT_SCRIPT_SHA256),
        )

    def test_compact_shell_center_bank_and_frontages_are_exact(self) -> None:
        _spec, prepared, _packed = _prepared_507()
        assert prepared.header is not None
        header = prepared.header

        def node(index: int) -> tuple[int, ...]:
            return struct.unpack_from(
                "<HhhhhhhH",
                header,
                0x190 + index * 16,
            )

        self.assertEqual(struct.unpack_from("<H", header, 0x18C)[0], 17)
        self.assertEqual(
            tuple(node(index) for index in range(11, 17)),
            (
                (0x0010, 0, 0x0A00, 0, 0, 0, 0, 1),
                (0x0000, 0, 0x0A00, 0, 0, 0, 0, 2),
                (0x0000, 0, 0x0A00, 0, 0, 0, 0, 3),
                (0x0010, 0, 0x0A00, 0, 0, 0, 0, 4),
                (0x8000, 0, 0x0A00, 0, 0, 0, 0, 5),
                (0x8000, 0, 0x0A00, 0, 0, 0, 0, 6),
            ),
        )
        self.assertEqual(
            node(dungeon.KRELIAN_COMPUTER_ROOM_RETURN_HELPER_ENTITY),
            (0x0290, 0, 0x0A00, 0, 0, 0, 0, 0),
        )

        models = dungeon._indexed_bundle_entries(
            prepared.components[dungeon.MODEL_INDEX]
        )
        self.assertEqual(
            tuple(
                (len(model), hashlib.sha256(model).hexdigest())
                for model in models
            ),
            (
                (136, "6b6e475c06c59ad4880d74e25e5d6315d4e1ae73179da31eeaa581f4cbe100d9"),
                (24_400, "ecb1202e0a1bb9dabb4c42e5add0ef69fdcfe81049fa4520327b88f15084e734"),
                (2_044, "98a73af5f97b9a4f4a7466e3f96e600b51aac37f32e27c7baca41b2875b8ea2a"),
                (3_324, "0fd8329e2a63945bf07bb7a2e8119e9934cfd6a742c6e47b1ce8b29931606b98"),
                (608, "8d2f43638e41112c00e18f0ef712d472c39fd160d3e6ff725f92127d6064a47b"),
                (4_264, "e9e99dbaf4ac53d94a4c2b8d6aef8e7d658da41ec04e39d9e37af0866e1d3240"),
                (136, "c54cb7c961bfd5420374d6e02220b14be21ac2c58a6297f9f850d8a3d2a19f8f"),
            ),
        )
        # Model 1 is the integrated opaque room shell and long center bank;
        # model 5 is its matching light/transparent pass. There are no added
        # prop models or transplanted field-507 graphics.
        bank_shell = models[1]
        self.assertEqual(struct.unpack_from("<I", bank_shell, 0)[0], 1)
        vertex_count = struct.unpack_from("<H", bank_shell, 0x12)[0]
        vertex_offset = struct.unpack_from("<I", bank_shell, 0x18)[0]
        vertices = tuple(
            struct.unpack_from("<hhhh", bank_shell, vertex_offset + index * 8)[:3]
            for index in range(vertex_count)
        )
        self.assertEqual(
            (
                vertex_count,
                tuple(min(vertex[axis] for vertex in vertices) for axis in range(3)),
                tuple(max(vertex[axis] for vertex in vertices) for axis in range(3)),
            ),
            (1_024, (-302, -210, -441), (302, 0, 485)),
        )

        walkmesh = prepared.components[1]

        def triangle_audit(
            point: tuple[int, int],
            triangle: int,
        ) -> tuple[tuple[int, ...], tuple[tuple[int, int, int], ...], tuple[int, ...], float]:
            indices = struct.unpack_from("<3H", walkmesh, 0x28 + triangle * 14)
            vertices_3d = tuple(
                struct.unpack_from("<hhhh", walkmesh, 0x364 + index * 8)[:3]
                for index in indices
            )
            x, z = point
            crosses = tuple(
                (end[0] - start[0]) * (z - start[2])
                - (end[2] - start[2]) * (x - start[0])
                for start, end in zip(
                    vertices_3d,
                    (*vertices_3d[1:], vertices_3d[0]),
                    strict=True,
                )
            )
            clearances = tuple(
                abs(cross)
                / math.hypot(end[0] - start[0], end[2] - start[2])
                for cross, start, end in zip(
                    crosses,
                    vertices_3d,
                    (*vertices_3d[1:], vertices_3d[0]),
                    strict=True,
                )
            )
            return indices, vertices_3d, crosses, min(clearances)

        controller = triangle_audit((120, 0), 9)
        self.assertEqual(
            controller[:3],
            (
                (12, 5, 3),
                ((-32, 0, -123), (249, 0, 158), (446, 0, 147)),
                (-8_149, -32_545, -17_754),
            ),
        )
        self.assertAlmostEqual(controller[3], 20.506096654409877)
        for point, triangle in (
            ((295, 295), 5),
            ((335, 335), 0),
            ((365, 365), 0),
            ((280, 180), 8),
            ((200, 80), 9),
            ((180, -60), 10),
        ):
            with self.subTest(point=point, triangle=triangle):
                _indices, _vertices, crosses, clearance = triangle_audit(
                    point,
                    triangle,
                )
                self.assertTrue(
                    all(value > 0 for value in crosses)
                    or all(value < 0 for value in crosses)
                )
                self.assertGreater(clearance, 10.0)

    def test_frozen_v147_party_slots_and_return_door_are_finite(self) -> None:
        self.assertNotIn(507, dungeon.ROUTE)
        self.assertEqual(
            tuple(
                contract
                for contract in dungeon.VISIBLE_DOOR_CONTRACTS
                if 507 in (contract.field, contract.reciprocal_field)
            ),
            (),
        )
        source, transformed = _source_and_transformed(507)
        self.assertEqual(
            tuple(source.get_script_pointer(entity, 0) for entity in (1, 2, 3)),
            (0x007F, 0x00AA, 0x00B5),
        )
        self.assertEqual(
            tuple(transformed.get_script_pointer(entity, 0) for entity in (1, 2, 3)),
            (0x041C, 0x0424, 0x042C),
        )
        self.assertEqual(
            tuple(
                dungeon._pointed_script_body(
                    transformed,
                    transformed.get_script_pointer(entity, 0),
                )
                for entity in (1, 2, 3)
            ),
            (
                bytes.fromhex("16 01 80 FE 0D 01 80 00"),
                bytes.fromhex("16 06 80 FE 0D 06 80 00"),
                bytes.fromhex("16 02 80 FE 0D 02 80 00"),
            ),
        )
        self.assertEqual(
            tuple(transformed.get_script_pointer(entity, 1) for entity in (1, 2, 3)),
            (0x0087, 0x0087, 0x00BF),
        )
        self.assertEqual(transformed.bytecode[0x0087:0x0089], b"\xA7\x00")
        self.assertEqual(transformed.bytecode[0x00BF], 0)

        stop = 0x018F
        self.assertEqual(transformed.bytecode[stop], 0)
        for entity in (6, 8, 9):
            with self.subTest(parked_story_entity=entity):
                self.assertEqual(
                    {transformed.get_script_pointer(entity, index) for index in range(32)},
                    {stop},
                )
        self.assertEqual(
            {
                transformed.get_script_pointer(10, index)
                for index in range(32)
                if index != 4
            },
            {stop},
        )

        self.assertEqual(
            tuple(transformed.get_script_pointer(4, index) for index in range(4)),
            (0x00C0, 0x00D5, 0x00D6, 0x00E4),
        )
        self.assertEqual(
            transformed.bytecode[0x00C0:0x00D5],
            bytes.fromhex(
                "BC 19 4F 01 4F 01 C0 F8 00 00 20 F8 03 04 00 18 "
                "0A 0A 1E 00 00"
            ),
        )
        self.assertEqual(
            transformed.bytecode[0x00D6:0x00E4],
            bytes.fromhex("09 05 24 07 01 24 26 0A 80 98 84 81 00 80"),
        )
        self.assertEqual(
            transformed.bytecode[0x00EA:0x00EE],
            bytes.fromhex("05 84 03 00"),
        )
        self.assertEqual(
            transformed.bytecode[0x008A:0x0093],
            bytes.fromhex("1F 10 4A 6D 01 6D 01 C0 00"),
        )

        source_transitions = scan_raw_transitions(ParsedAtelScript(source.to_bytes()))
        transformed_transitions = scan_raw_transitions(
            ParsedAtelScript(transformed.to_bytes())
        )
        self.assertEqual(
            [(item.pc, item.field, item.parameter) for item in source_transitions],
            [(0x00DF, 557, 1)],
        )
        self.assertEqual(
            [(item.pc, item.field, item.parameter) for item in transformed_transitions],
            [(0x00DF, 388, 0)],
        )
        door_contracts = tuple(
            contract
            for contract in dungeon.VISIBLE_DOOR_CONTRACTS
            if contract.field == 507 or contract.reciprocal_field == 507
        )
        self.assertEqual(
            tuple(
                (
                    contract.field,
                    contract.entity,
                    contract.helper_entities,
                    contract.destination_field,
                    contract.destination_parameter,
                    contract.reciprocal_field,
                    contract.reciprocal_entity,
                )
                for contract in door_contracts
            ),
            (),
        )

    def test_frozen_v147_console_staged_citan_and_one_bounded_panel_beat(
        self,
    ) -> None:
        self.assertFalse(
            any(spec.target_field == 507 for spec in dungeon.CLONES)
        )
        _spec, prepared, _packed = _prepared_507()
        arrival = dungeon.FinalPartyArrival(
            character=2,
            entity=3,
            entry_position=(365, 365, 0, 5),
            position=(180, -60, 0, 7),
            door_helper_entity=5,
            variable=dungeon.INTERLOCK_VARIABLE,
            arrived_bit=dungeon.CITAN_FINAL_ARRIVAL_BIT,
            waypoints=(
                dungeon.FinalPartyWaypoint(280, 180, 320),
                dungeon.FinalPartyWaypoint(200, 80, 256),
                dungeon.FinalPartyWaypoint(180, -60, 256),
            ),
            party_init_repetitions=1,
            door_helper_expected_body=bytes.fromhex("05 84 03 00"),
        )
        completion = dungeon.CompletionInteraction(
            entity=7,
            old_action_pointer=0x018F,
            dialogue_id=3,
            controller_requires_facing=True,
            controller_interaction_half_width=0x04,
            controller_invisible=True,
            variable=dungeon.INTERLOCK_VARIABLE,
            required_mask=dungeon.LAUNCH_AUTHORIZATION_MASK,
            locked_dialogue=2,
            completion_bit=dungeon.LAUNCH_COMPLETED_BIT,
            already_completed_dialogue=4,
            launch_scene=True,
            final_party_arrival=arrival,
            arrival_camera=dungeon.HistoricalCameraShot(
                (240, 140, -48),
                (450, 400, -420),
                18,
                (3,),
            ),
            conversation_camera=dungeon.HistoricalCameraShot(
                (120, 0, -48),
                (430, -310, -380),
                18,
                (3,),
            ),
            prelude_dialogues=(1,),
            mechanism_steps=(dungeon.CompletionMechanismStep(10, 4, 0),),
        )
        self.assertEqual(
            (
                completion.entity,
                completion.old_action_pointer,
                completion.dialogue_id,
                completion.old_init_pointer,
                completion.fixed_script_position,
                completion.controller_requires_facing,
                completion.controller_interaction_half_width,
                completion.controller_invisible,
                completion.variable,
                completion.required_mask,
                completion.locked_dialogue,
                completion.completion_bit,
                completion.already_completed_dialogue,
                completion.launch_scene,
                completion.prelude_dialogues,
                completion.mechanism_steps,
                completion.handoff_field,
            ),
            (
                7,
                0x018F,
                3,
                None,
                None,
                True,
                0x04,
                True,
                dungeon.INTERLOCK_VARIABLE,
                dungeon.LAUNCH_AUTHORIZATION_MASK,
                2,
                dungeon.LAUNCH_COMPLETED_BIT,
                4,
                True,
                (1,),
                (dungeon.CompletionMechanismStep(10, 4, 0),),
                None,
            ),
        )

        arrival = completion.final_party_arrival
        assert arrival is not None
        self.assertEqual(
            (
                arrival.character,
                arrival.entity,
                arrival.entry_position,
                arrival.position,
                arrival.door_helper_entity,
                arrival.variable,
                arrival.arrived_bit,
                arrival.door_helper_script_index,
                arrival.door_sound_id,
                arrival.staging_script_index,
                arrival.walking_script_index,
                arrival.party_init_repetitions,
                arrival.door_helper_expected_body,
                tuple(
                    (waypoint.x, waypoint.z, waypoint.max_steps)
                    for waypoint in arrival.waypoints
                ),
            ),
            (
                2,
                3,
                (365, 365, 0, 5),
                (180, -60, 0, 7),
                5,
                dungeon.INTERLOCK_VARIABLE,
                dungeon.CITAN_FINAL_ARRIVAL_BIT,
                4,
                0x77,
                21,
                22,
                1,
                bytes.fromhex("05 84 03 00"),
                ((280, 180, 320), (200, 80, 256), (180, -60, 256)),
            ),
        )
        assert completion.arrival_camera is not None
        assert completion.conversation_camera is not None
        self.assertEqual(
            (
                completion.arrival_camera.target,
                completion.arrival_camera.eye,
                completion.arrival_camera.transition_frames,
                completion.arrival_camera.dialogues,
                completion.conversation_camera.target,
                completion.conversation_camera.eye,
                completion.conversation_camera.transition_frames,
                completion.conversation_camera.dialogues,
            ),
            (
                (240, 140, -48),
                (450, 400, -420),
                18,
                (3,),
                (120, 0, -48),
                (430, -310, -380),
                18,
                (3,),
            ),
        )

        transformed = AtelScript(prepared.components[dungeon.SCRIPT_INDEX])
        self.assertEqual(
            (
                transformed.get_script_pointer(7, 0),
                transformed.get_script_pointer(7, 2),
                transformed.get_script_pointer(7, 3),
                transformed.get_script_pointer(10, 4),
                transformed.get_script_pointer(3, 21),
                transformed.get_script_pointer(3, 22),
            ),
            (0x0434, 0x0488, 0x018F, 0x044D, 0x045A, 0x0465),
        )
        controller = dungeon._pointed_script_body(transformed, 0x0434)
        self.assertEqual(
            controller,
            dungeon._static_door_controller_init(
                120,
                0,
                requires_facing=True,
                interaction_half_width=0x04,
                invisible=True,
            ),
        )
        self.assertEqual(
            (len(controller), hashlib.sha256(controller).hexdigest()),
            (
                25,
                "ee0585f10f6eca7ede3e78cbb08c9013c0e8ae6492778f49c6ee232faffd2df7",
            ),
        )
        panel_beat = dungeon._pointed_script_body(transformed, 0x044D)
        self.assertEqual(
            panel_beat,
            bytes.fromhex("74 F9 80 26 1E 80 B4 0C 80 26 0C 80 00"),
        )
        self.assertEqual(
            hashlib.sha256(panel_beat).hexdigest(),
            "eee2bca3a027a3db06e5fd547a5b2003da1068977d49b0b7f30bb73da25f7dec",
        )

        stage = dungeon._pointed_script_body(transformed, 0x045A)
        walk = dungeon._pointed_script_body(transformed, 0x0465)
        self.assertEqual(
            stage,
            bytes.fromhex("19 6D 01 6D 01 C0 1A 00 5F 05 00"),
        )
        self.assertEqual(
            walk,
            bytes.fromhex(
                "4B 18 01 B4 00 C0 40 81 "
                "4B C8 00 50 00 C0 00 81 "
                "4B B4 00 C4 FF C0 00 81 "
                "19 B4 00 C4 FF C0 1A 00 5F 07 00"
            ),
        )
        self.assertIsNone(
            dungeon._validate_final_party_arrival_walkmesh(
                prepared.components[1],
                arrival,
            )
        )

        action = dungeon._pointed_script_body(transformed, 0x0488)
        self.assertEqual(
            (len(action), hashlib.sha256(action).hexdigest()),
            (
                340,
                "eb971f559da781ddb57878b8c3d602ffc651cf9310e6ba08e53f95369a4d23db",
            ),
        )
        self.assertEqual(action.count(bytes.fromhex("09 0A 24")), 1)
        self.assertEqual(action.count(dungeon._dialog(1)), 1)
        self.assertEqual(action.count(dungeon._dialog(2)), 1)
        self.assertEqual(action.count(dungeon._dialog(3)), 1)
        self.assertEqual(action.count(dungeon._dialog(4)), 1)
        launch = dungeon._worldmap(
            dungeon.MASS_DRIVER_LAUNCH_SCENE_POSITION,
            dungeon.MASS_DRIVER_LAUNCH_SCENE_MODE,
        )
        self.assertEqual(action.count(launch), 1)
        self.assertEqual(
            action.count(
                dungeon._worldmap(
                    completion.worldmap_position,
                    completion.worldmap_mode,
                )
            ),
            1,
        )
        self.assertLess(action.index(bytes.fromhex("09 0A 24")), action.rindex(launch))
        self.assertIn(
            dungeon._set_var_bit(
                dungeon.INTERLOCK_VARIABLE,
                dungeon.CITAN_FINAL_ARRIVAL_BIT,
            ),
            action,
        )
        self.assertIn(
            dungeon._set_var_bit(
                dungeon.INTERLOCK_VARIABLE,
                dungeon.LAUNCH_COMPLETED_BIT,
            ),
            action,
        )

    def test_active_finale_is_central_only_and_v147_handoff_is_frozen(self) -> None:
        relevant_arrivals = tuple(
            contract
            for contract in dungeon.ARRIVAL_CONTINUITY_CONTRACTS
            if contract.source_field == 507 or contract.destination_field == 507
        )
        self.assertEqual(relevant_arrivals, ())
        self.assertFalse({388, 507} & set(dungeon.ROUTE))

        central = _clone(728).completion_interaction
        self.assertIsNotNone(central)
        assert central is not None
        self.assertEqual(
            (
                central.required_mask,
                central.launch_scene,
                central.handoff_field,
                central.handoff_parameter,
                central.handoff_character,
                central.final_party_arrival,
                central.arrival_camera,
                central.conversation_camera,
            ),
            (
                dungeon.LAUNCH_AUTHORIZATION_MASK,
                True,
                None,
                0,
                None,
                None,
                None,
                None,
            ),
        )
        self.assertIsNotNone(central.historical_scene)
        historical = central.historical_scene
        assert historical is not None
        arrival = historical.final_party_arrival
        assert arrival is not None
        self.assertEqual(
            (
                arrival.position,
                tuple(
                    (waypoint.x, waypoint.z, waypoint.max_steps)
                    for waypoint in arrival.waypoints
                ),
                arrival.preserve_terminal_facing,
                historical.arrival_camera,
                historical.final_camera,
                historical.terminal_operation_camera,
                arrival.terminal_operation_script_index,
                arrival.terminal_operation_body,
            ),
            (
                (136, 131, 0, 0),
                ((170, 89, 32), (160, 110, 32), (136, 131, 20)),
                False,
                dungeon.HistoricalCameraShot(
                    (-13, 106, -32),
                    (-27, -767, -544),
                    24,
                    (35,),
                ),
                dungeon.HistoricalCameraShot(
                    (-13, 106, -32),
                    (-27, -767, -544),
                    24,
                    (35,),
                ),
                dungeon.HistoricalCameraShot(
                    (145, 160, -45),
                    (170, -80, -135),
                    12,
                    (),
                ),
                23,
                bytes.fromhex(
                    "5F 00 2C 0A 74 F9 80 26 19 80 74 F9 80 2C 0A "
                    "74 F9 80 26 23 80 2C 07 26 18 80 2C FF 00"
                ),
            ),
        )

        _source, transformed = _source_and_transformed(728)
        action_pc = transformed.get_script_pointer(13, 2)
        action = dungeon._pointed_script_body(transformed, action_pc)
        self.assertEqual(
            (action_pc, len(action), hashlib.sha256(action).hexdigest()),
            (
                0x03F2,
                1_053,
                "41e90c56f716d18b670e26e28204a0309be3d811dd4a5e0d651a5bc168cebfdf",
            ),
        )
        self.assertEqual(action.count(bytes.fromhex("74 50 80")), 1)
        dialogue_32 = dungeon._dialog(32, dialogue_flags=0x01) + b"\x9C"
        self.assertEqual(action.count(dialogue_32), 1)
        self.assertNotIn(dungeon._dialog(33, dialogue_flags=0x01), action)
        self.assertNotIn(dungeon._dialog(34, dialogue_flags=0x01), action)
        seen_write = dungeon._set_var_bit(
            dungeon.INTERLOCK_VARIABLE,
            dungeon.HISTORICAL_GHOST_SEEN_BIT,
        )
        prepare = dungeon._final_party_arrival_prepare_body(arrival)
        fresh_camera = dungeon._historical_camera_shot_body(
            historical.arrival_camera,
            enter_camera_mode=False,
        )
        recovery_camera = dungeon._historical_camera_shot_body(
            historical.arrival_camera,
            enter_camera_mode=True,
        )
        suffix = dungeon._final_party_arrival_suffix_body(
            arrival,
            conversation_camera=historical.final_camera,
        )
        operation_camera = dungeon._historical_camera_shot_body(
            historical.terminal_operation_camera,
            enter_camera_mode=False,
            allow_silent=True,
        )
        operation_call = bytes.fromhex("09 03 37")
        operation_pointer = transformed.get_script_pointer(
            arrival.entity,
            arrival.terminal_operation_script_index,
        )
        operation_body = dungeon._pointed_script_body(
            transformed,
            operation_pointer,
        )
        self.assertEqual(
            (
                operation_pointer,
                len(operation_body),
                hashlib.sha256(operation_body).hexdigest(),
                operation_body,
            ),
            (
                0x03D5,
                29,
                "e88f1ffb09b42ec8c4d878983cb6cac2e065f686955a5521e7f0fe9f963f1c7e",
                arrival.terminal_operation_body,
            ),
        )
        self.assertEqual(
            action.count(
                dialogue_32
                + seen_write
                + dungeon._wait()
                + prepare
                + fresh_camera
            ),
            1,
        )
        self.assertEqual(action.count(prepare), 2)
        self.assertEqual(action.count(fresh_camera), 1)
        self.assertEqual(action.count(recovery_camera), 1)
        self.assertEqual(action.count(suffix), 1)
        self.assertEqual(action.count(operation_camera + operation_call), 1)
        self.assertNotIn(dungeon._historical_camera_release_body(), action)
        retail_launch = dungeon._worldmap(
            dungeon.MASS_DRIVER_LAUNCH_SCENE_POSITION,
            dungeon.MASS_DRIVER_LAUNCH_SCENE_MODE,
        )
        automatic_finale = action[
            action.index(dialogue_32) : action.index(retail_launch)
            + len(retail_launch)
            + 1
        ]
        self.assertNotIn(b"\xFE\x53", automatic_finale)
        self.assertEqual(suffix.count(bytes.fromhex("FE 17 03 FF")), 1)
        self.assertEqual(suffix.count(bytes.fromhex("FE 17 FF 03")), 1)
        self.assertEqual(action.count(bytes.fromhex("FE 17 03 FF")), 2)
        self.assertEqual(action.count(bytes.fromhex("FE 17 FF 03")), 2)
        dialogue_35 = dungeon._dialog(35, dialogue_flags=0x01) + b"\x9C"
        dialogue_35_offsets = tuple(
            offset
            for offset in range(len(action))
            if action.startswith(dialogue_35, offset)
        )
        self.assertEqual(
            tuple(action_pc + offset for offset in dialogue_35_offsets),
            (0x0454, 0x07B7),
        )
        operation_offset = action.index(operation_camera + operation_call)
        self.assertEqual(action_pc + operation_offset, 0x07BC)
        self.assertEqual(
            operation_offset,
            dialogue_35_offsets[1] + len(dialogue_35),
        )
        recovery_jump = dialogue_35_offsets[0] + len(dialogue_35)
        self.assertEqual(action[recovery_jump], 0x01)
        self.assertEqual(
            struct.unpack_from("<H", action, recovery_jump + 1)[0],
            action_pc + operation_offset,
        )
        for dialogue_offset in dialogue_35_offsets:
            self.assertNotIn(
                b"\xFE\x53",
                action[dialogue_offset : action.index(retail_launch)],
            )
        handoff = dungeon._change_field(388, 1)
        self.assertNotIn(handoff, action)
        for marker in (
            b"\xFE\x18",
            b"\xFE\x1A",
            b"\x09\x03\x35",
            b"\x09\x03\x36",
            b"\x09\x03\x37",
            b"\x09\x0F\x24",
            dungeon._set_var_bit(
                dungeon.INTERLOCK_VARIABLE,
                dungeon.CITAN_FINAL_ARRIVAL_BIT,
            ),
            dungeon._set_var_bit(
                dungeon.INTERLOCK_VARIABLE,
                dungeon.LAUNCH_COMPLETED_BIT,
            ),
            dungeon._set_var_bit(
                dungeon.RETAIL_WORLDMAP_RETURN_VARIABLE,
                dungeon.RETAIL_WORLDMAP_RETURN_BIT,
            ),
            dungeon._worldmap(
                dungeon.MASS_DRIVER_LAUNCH_SCENE_POSITION,
                dungeon.MASS_DRIVER_LAUNCH_SCENE_MODE,
            ),
        ):
            self.assertIn(marker, action)

        # V147's discarded Central-to-lab handoff remains immutable history.
        v147_script = AtelScript(
            (
                PROJECT
                / "work"
                / "mass_driver_v147_stage"
                / "clones"
                / "field_728"
                / "05_scripts.bin"
            ).read_bytes()
        )
        v147_action_pc = v147_script.get_script_pointer(13, 2)
        v147_action = dungeon._pointed_script_body(v147_script, v147_action_pc)
        self.assertEqual(
            (
                v147_action_pc,
                len(v147_action),
                hashlib.sha256(v147_action).hexdigest(),
            ),
            (
                0x0362,
                104,
                "c833f972eca4ce8c4d4cbb06ebc0ca34877bc21e8ec72c3957e32deaeb1ff6b4",
            ),
        )
        self.assertEqual(
            tuple(
                offset
                for offset in range(len(v147_action))
                if v147_action.startswith(handoff, offset)
            ),
            (35, 73),
        )

    def test_frozen_v147_lab_dialogue_is_manual_paginated_and_state_complete(
        self,
    ) -> None:
        self.assertNotIn(
            "field_507_krelian_lab.authored.json",
            {spec.dialogue_file for spec in dungeon.CLONES},
        )
        path = (
            PROJECT
            / "modules" / "mass_driver" / "content"
            / "field_507_krelian_lab.authored.json"
        )
        document = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(
            (document["format"], document["reconstruction"]),
            ("xenogears-field-dialogue-authored-v1", True),
        )
        self.assertEqual([block["id"] for block in document["blocks"]], list(range(6)))
        self.assertTrue(all(block.get("manual_wrap") for block in document["blocks"]))
        self.assertTrue(
            all(
                (block["width"], block["height"]) == (58, 5)
                for block in document["blocks"]
            )
        )
        self.assertEqual(
            [len(block["text"].split("<New>")) for block in document["blocks"]],
            [4, 4, 3, 9, 4, 2],
        )
        for block in document["blocks"]:
            for page in block["text"].split("<New>"):
                self.assertLessEqual(len(page.splitlines()), 5)

        encoded = dungeon._authored_dialogue(document)
        self.assertEqual(
            (len(encoded), hashlib.sha256(encoded).hexdigest()),
            (1_643, CURRENT_DIALOGUE_SHA256),
        )
        parsed = parse_dialogue(encoded)
        self.assertEqual([block.block_id for block in parsed.blocks], list(range(6)))

        blocks = {block["id"]: block["text"] for block in document["blocks"]}
        self.assertIn("Krelian's", blocks[0])
        for term in ("Ouroboros Ring", "Miang", "VISUAL LOG: NOT RECORDED"):
            self.assertIn(term, blocks[1])
        self.assertNotIn("Karellen", blocks[1])
        self.assertNotIn("Myyah", blocks[1])
        self.assertIn("CENTRAL AUTHORITY MISSING", blocks[2])
        self.assertIn("<Elly>", blocks[3])
        self.assertIn("<Citan>", blocks[3])
        self.assertIn("upper atmosphere", blocks[3])
        self.assertIn("CAPSULE ALREADY RELEASED", blocks[4])
        self.assertIn("RED SERVICE TUNNEL", blocks[5])


if __name__ == "__main__":
    unittest.main()
